'''
Task Coach - Your friendly task manager
Copyright (C) 2008-2009 Jerome Laheurte <fraca7@free.fr>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from taskcoachlib.gui.threads import synchronized, DeferredCallMixin
from taskcoachlib.patterns.network import Acceptor
from taskcoachlib.domain.date import Date, parseDate

from taskcoachlib.domain.category import Category
from taskcoachlib.domain.task import Task

from taskcoachlib.i18n import _

import wx, asynchat, threading, asyncore, struct, StringIO, random, time, sha

# Default port is 8001.
#
# Integers are sent as 32 bits signed, network byte order.
# Strings are sent as their length (as integer), then data (UTF-8 encoded).
#
# 1) The protocol version is negotiated: Task Coach sends its higher
# supported version (currently 2). If the iPhone answers 0, it doesn't
# support it, so decrement and try again. If it answers 1, go to 2.
# See at the end of this comment to know what's new in protocol 2.
#
# 2) SHA1 challenge: Task Coach sends 512 random bytes to the
# device. The device appends the user provided password as UTF-8 data
# and sends back the SHA1 hash of the result. Task Coach checks the
# hash and sends 0 (wrong hash) or 1 (authenticated), and then go to 3.
#
# 3) The iPhone sends its device name.
#
# 4) The iPhone sends the task file GUID it's associated with, or an
# empty string if it has never been synced before. If the GUID doesn't
# match the currently open file, the user is prompted for the kind of
# synchronization he wants (full from Task Coach or full from device).
#
# 5) Task Coach sends the synchronization type to the iPhone. The
# actual synchronization can begin now.
#
# Types are
#   0 two ways
#   1 full from Task Coach
#   2 full from iPhone
#   3 user cancelled
#
# Two-way is actually implemented as: get changes from iPhone, then
# full from Task Coach. This allows us to avoid keeping track of
# changes on the Task Coach side; we're not using the change tracking
# mechanism because it would interfere with SyncML. Cons: no conflict
# resolution, the device always wins. This should not be a problem in
# this use case.
#
# == Full from Task Coach ==
#
# In this scenario, Task Coach first sends the number of categories it
# will send, then the number of tasks. Then it sends the objects
# themselves.
#
# Categories are sent as:
#
#  1) name (string)
#  2) ID (string)
#  3) Parent ID (string)
#
# Tasks are sent as:
#
#  1) title (string)
#  2) ID (string)
#  3) description (string)
#  4) start date
#  5) due date
#  6) completion date
#  7) Number of categories (int)
#  8) Category IDs (strings)
#
# All dates are string, formatted YYYY-MM-DD. An empty string means None.
#
# After all categories and tasks have been sent, Task Coach sends the file
# GUID as a string.
#
# After each object has been sent, Task Coach waits for the device to send
# a status code (integer). Currently it is always 1. This seems necessary for
# the iPhone UI to update; without that the run loop doesn't have a chance to
# run anything not network-related...
#
# == Full from device ==
#
# All conventions are the same as in "Full from Task Coach".
#
# 1) The device sends two integers: number of categories, number of tasks
# 2) For each category, the device sends the category name and waits for its ID.
# 3) For each task, the device sends the full task (same format as above, without
#    the ID), and waits for its ID.
# 4) Task Coach sends the GUID and waits for an integer (currently always 1)
# 5) Task Coach closes the connection
#
# == Two-way ==
#
# All conventions are the same as in "Full from Task Coach".
#
# 1) The device sends four integers: number of new categories, number of new tasks,
#    number of deleted tasks, and number of modified tasks.
# 2) For each new category, the device sends its name, and waits for the ID.
# 3) For each new task, the device sends it (same format as above, but without the
#    ID) and waits for its ID.
# 4) For each deleted task, the device sends its ID.
# 5) For each modified task, the device sends it (same format as above, without the category Id)
# 6) Go into "Full from Task Coach" mode.

# What's new in protocol v2

# In the two-way state, when uploading modified tasks from the device to the desktop,
# it adds the number of categories for the task, then each category ID.

class IPhoneAcceptor(Acceptor):
    def __init__(self, window, settings):
        def factory(fp, addr):
            password = settings.get('iphone', 'password')

            if password:
                return IPhoneHandler(window, settings.get('iphone', 'password'), fp)

            wx.MessageBox(_('''An iPhone or iPod Touch tried to connect to Task Coach,\n'''
                            '''but no password is set. Please set a password in the\n'''
                            '''iPhone section of the configuration and try again.'''),
                          _('Error'), wx.OK)

        Acceptor.__init__(self, factory, '', None)

        thread = threading.Thread(target=asyncore.loop)
        thread.setDaemon(True)
        thread.start()


class IPhoneHandler(asynchat.async_chat):
    def __init__(self, window, password, fp):
        asynchat.async_chat.__init__(self, fp)

        self.window = window
        self.password = password
        self.data = StringIO.StringIO()
        self.state = InitialState(self)

        random.seed(time.time())

    def collect_incoming_data(self, data):
        self.data.write(data)

    def found_terminator(self):
        data = self.data.getvalue()
        self.data = StringIO.StringIO()
        self.state.handleData(self, data)

    def handle_close(self):
        self.state.handleClose(self)
        self.close()

    def handle_error(self):
        asynchat.async_chat.handle_error(self)
        self.close()
        self.state.handleClose(self)

    def pushString(self, string):
        if string is None:
            self.pushInteger(0)
        else:
            string = string.encode('UTF-8')
            self.push(struct.pack('!i', len(string)) + string)

    def pushInteger(self, value):
        self.push(struct.pack('!i', value))

    def pushDate(self, date):
        if date == Date():
            self.pushString('')
        else:
            self.pushString('%04d-%02d-%02d' % (date.year, date.month, date.day))


class BaseState(object):
    def __init__(self, disp, *args, **kwargs):
        self.oldTasks = disp.window.taskFile.tasks().copy()
        self.oldCategories = disp.window.taskFile.categories().copy()

        self.dlg = None

        self.init(disp, *args, **kwargs)

    def isTaskEligible(self, task):
        """Returns True if a task should be considered when syncing with an iPhone/iPod Touch
        device. Right now, a task is eligible if

         * It's a leaf task (no children)
         * Or it has a reminder
         * Or it's overdue
         * Or it belongs to a category named 'iPhone'

         This will probably be more configurable in the future."""

        if task.isDeleted():
            return False

        if len(task.children()) == 0:
            return True

        if task.reminder() is not None:
            return True

        if task.overdue():
            return True

        for category in task.categories():
            if category.subject() == 'iPhone':
                return True

        return False

    def setState(self, state, *args, **kwargs):
        self.__class__ = state
        self.init(*args, **kwargs)

    def handleClose(self, disp):
        if self.dlg is not None:
            self.dlg.Finished()

        # Rollback
        disp.window.restoreTasks(self.oldCategories, self.oldTasks)

    def init(self, disp):
        pass


class InitialState(BaseState):
    def init(self, disp):
        self.currentProtocolVersion = 2
        disp.set_terminator(4)
        disp.pushInteger(self.currentProtocolVersion)

    def handleData(self, disp, data):
        response, = struct.unpack('!i', data)

        if response:
            disp.protocolVersion = self.currentProtocolVersion
            self.setState(PasswordState, disp)
        else:
            if self.currentProtocolVersion == 1:
                disp.close()
                disp.window.notifyIPhoneProtocolFailed()
            else:
                self.currentProtocolVersion -= 1
                disp.set_terminator(4)
                disp.pushInteger(self.currentProtocolVersion)


class PasswordState(BaseState):
    def init(self, disp):
        self.hashData = ''.join([struct.pack('B', random.randint(0, 255)) for i in xrange(512)])
        disp.push(self.hashData)

        self.length = None
        disp.set_terminator(20)

    def handleData(self, disp, data):
        if data == sha.sha(self.hashData + disp.password.encode('UTF-8')).digest():
            disp.pushInteger(1)
            self.setState(DeviceNameState, disp)
        else:
            disp.pushInteger(0)
            self.setState(PasswordState, disp)


class DeviceNameState(BaseState):
    def init(self, disp):
        self.length = None
        disp.set_terminator(4)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            disp.set_terminator(self.length)
        else:
            self.deviceName = data.decode('UTF-8')
            self.setState(GUIDState, disp)


class GUIDState(BaseState):
    def init(self, disp):
        self.length = None
        disp.set_terminator(4)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            if self.length:
                disp.set_terminator(self.length)
            else:
                self.onSyncType(disp, disp.window.getIPhoneSyncType(None))
        else:
            self.onSyncType(disp, disp.window.getIPhoneSyncType(data))

    def onSyncType(self, disp, type_):
        disp.push(struct.pack('!i', type_))

        if type_ != 3:
            self.dlg = disp.window.createIPhoneProgressDialog(self.deviceName)
            self.dlg.Started()

        if type_ == 0:
            self.setState(TwoWayState, disp)
        elif type_ == 1:
            self.setState(FullFromDesktopState, disp)
        elif type_ == 2:
            self.setState(FullFromDeviceState, disp)

        # On cancel, the other end will close the connection


class FullFromDesktopState(BaseState):
    def init(self, disp):
        self.tasks = filter(self.isTaskEligible, disp.window.taskFile.tasks())
        self.categories = list([cat for cat in disp.window.taskFile.categories() if not cat.isDeleted()])

        disp.pushInteger(len(self.categories))
        disp.pushInteger(len(self.tasks))

        self.total = len(self.categories) + len(self.tasks)
        self.count = 0

        self.setState(FullFromDesktopCategoryState, disp)


class FullFromDesktopCategoryState(BaseState):
    def init(self, disp):
        if self.categories:
            disp.pushString(self.categories[0].subject())
            disp.pushString(self.categories[0].id())
            parent = self.categories[0].parent()
            if parent is None:
                disp.pushString(None)
            else:
                disp.pushString(parent.id())
            self.index = 0
            disp.set_terminator(4)
        else:
            self.setState(FullFromDesktopTaskState, disp)

    def handleData(self, disp, data):
        self.count += 1
        self.dlg.SetProgress(self.count, self.total)

        self.index += 1
        if self.index < len(self.categories):
            disp.pushString(self.categories[self.index].subject())
            disp.pushString(self.categories[self.index].id())
            parent = self.categories[self.index].parent()
            if parent is None:
                disp.pushString(None)
            else:
                disp.pushString(parent.id())

            disp.set_terminator(4)
        else:
            self.setState(FullFromDesktopTaskState, disp)

class FullFromDesktopTaskState(BaseState):
    def init(self, disp):
        if self.tasks:
            disp.pushString(self.tasks[0].subject())
            disp.pushString(self.tasks[0].id())
            disp.pushString(self.tasks[0].description())
            disp.pushDate(self.tasks[0].startDate())
            disp.pushDate(self.tasks[0].dueDate())
            disp.pushDate(self.tasks[0].completionDate())
            disp.pushInteger(len(self.tasks[0].categories()))
            for category in self.tasks[0].categories():
                disp.pushString(category.id())
            self.index = 0
            disp.set_terminator(4)
        else:
            disp.pushString(disp.window.taskFile.guid())
            self.setState(EndState, disp)

    def handleData(self, disp, data):
        code, = struct.unpack('!i', data)

        self.count += 1
        self.dlg.SetProgress(self.count, self.total)

        self.index += 1
        if self.index < len(self.tasks):
            disp.pushString(self.tasks[self.index].subject())
            disp.pushString(self.tasks[self.index].id())
            disp.pushString(self.tasks[self.index].description())
            disp.pushDate(self.tasks[self.index].startDate())
            disp.pushDate(self.tasks[self.index].dueDate())
            disp.pushDate(self.tasks[self.index].completionDate())
            disp.pushInteger(len(self.tasks[self.index].categories()))
            for category in self.tasks[self.index].categories():
                disp.pushString(category.id())
            disp.set_terminator(4)
        else:
            disp.pushString(disp.window.taskFile.guid())
            self.setState(EndState, disp)


class FullFromDeviceState(BaseState):
    def init(self, disp):
        disp.window.clearTasks()
        disp.set_terminator(8)

    def handleData(self, disp, data):
        self.categoryCount, self.taskCount = struct.unpack('!ii', data)
        self.total = self.categoryCount + self.taskCount
        self.count = 0
        self.setState(FullFromDeviceCategoryState, disp)


class FullFromDeviceCategoryState(BaseState):
    def init(self, disp):
        self.length = None
        self.categoryMap = {}

        if self.categoryCount:
            disp.set_terminator(4)
        else:
            self.setState(FullFromDeviceTaskState, disp)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            disp.set_terminator(self.length)
        else:
            category = Category(data.decode('UTF-8'))
            disp.window.addIPhoneCategory(category)
            disp.pushString(category.id())
            self.categoryMap[category.id()] = category

            self.categoryCount -= 1
            self.count += 1
            self.dlg.SetProgress(self.count, self.total)

            if self.categoryCount:
                self.length = None
                disp.set_terminator(4)
            else:
                self.setState(FullFromDeviceTaskState, disp)


class FullFromDeviceTaskState(BaseState):
    def init(self, disp):
        if self.taskCount:
            self.length = None
            self.state = 0
            disp.set_terminator(4)
        else:
            disp.pushString(disp.window.taskFile.guid())
            self.setState(EndState, disp)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            if self.length == 0:
                self.handleData(disp, '')
            else:
                disp.set_terminator(self.length)
        else:
            if self.state == 0:
                self.subject = data.decode('UTF-8')
            elif self.state == 1:
                self.description = data.decode('UTF-8')
            elif self.state == 2:
                self.startDate = parseDate(data)
            elif self.state == 3:
                self.dueDate = parseDate(data)
            elif self.state == 4:
                task = Task(subject=self.subject,
                            description=self.description,
                            startDate=self.startDate,
                            dueDate=self.dueDate,
                            completionDate=parseDate(data))

                self.setState(FullFromDeviceTaskCategoryCountState, disp, task)

            if self.state != 4:
                self.length = None
                self.state += 1
                disp.set_terminator(4)

class FullFromDeviceTaskCategoryCountState(BaseState):
    def init(self, disp, task):
        self.task = task
        disp.set_terminator(4)

    def handleData(self, disp, data):
        self.taskCategoryCount, = struct.unpack('!i', data)
        if self.taskCategoryCount:
            self.setState(FullFromDeviceTaskCategoriesState, disp)
        else:
            disp.pushString(self.task.id())
            self.taskCount -= 1
            self.count += 1
            self.dlg.SetProgress(self.count, self.total)

            if self.taskCount:
                self.setState(FullFromDeviceTaskState, disp)
            else:
                disp.pushString(disp.window.taskFile.guid())
                self.setState(EndState, disp)


class FullFromDeviceTaskCategoriesState(BaseState):
    def init(self, disp):
        self.categories = []
        self.length = None
        disp.set_terminator(4)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            disp.set_terminator(self.length)
        else:
            self.categories.append(self.categoryMap[data.decode('UTF-8')])

            self.taskCategoryCount -= 1
            if self.taskCategoryCount:
                self.length = None
                disp.set_terminator(4)
            else:
                disp.window.addIPhoneTask(self.task, self.categories)
                disp.pushString(self.task.id())
                self.taskCount -= 1
                self.count += 1
                self.dlg.SetProgress(self.count, self.total)

                if self.taskCount:
                    self.setState(FullFromDeviceTaskState, disp)
                else:
                    disp.pushString(disp.window.taskFile.guid())
                    self.setState(EndState, disp)


class TwoWayState(BaseState):
    def init(self, disp):
        disp.set_terminator(16)

        self.categoryMap = dict()
        for category in disp.window.taskFile.categories():
            self.categoryMap[category.id()] = category

        self.taskMap = dict()
        for task in disp.window.taskFile.tasks():
            self.taskMap[task.id()] = task

    def handleData(self, disp, data):
        (self.newCategoriesCount, self.newTasksCount,
         self.deletedTasksCount, self.modifiedTasksCount) = struct.unpack('!iiii', data)

        self.setState(TwoWayNewCategoriesState, disp)


class TwoWayNewCategoriesState(BaseState):
    def init(self, disp):
        if self.newCategoriesCount:
            self.length = None
            disp.set_terminator(4)
        else:
            self.setState(TwoWayNewTasksState, disp)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            disp.set_terminator(self.length)
        else:
            category = Category(data.decode('UTF-8'))
            disp.window.addIPhoneCategory(category)
            disp.pushString(category.id())
            self.categoryMap[category.id()] = category

            self.newCategoriesCount -= 1
            if self.newCategoriesCount:
                self.length = None
                disp.set_terminator(4)
            else:
                self.setState(TwoWayNewTasksState, disp)


class TwoWayNewTasksState(BaseState):
    def init(self, disp):
        if self.newTasksCount:
            self.length = None
            self.state = 0
            disp.set_terminator(4)
        else:
            self.setState(TwoWayDeletedTasksState, disp)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            if self.length == 0:
                self.handleData(disp, '')
            else:
                disp.set_terminator(self.length)
        else:
            if self.state == 0:
                self.subject = data.decode('UTF-8')
            elif self.state == 1:
                self.description = data.decode('UTF-8')
            elif self.state == 2:
                self.startDate = parseDate(data)
            elif self.state == 3:
                self.dueDate = parseDate(data)
            elif self.state == 4:
                task = Task(subject=self.subject,
                            description=self.description,
                            startDate=self.startDate,
                            dueDate=self.dueDate,
                            completionDate=parseDate(data))

                self.setState(TwoWayNewTasksCategoryCountState, disp, task)

            if self.state != 4:
                self.state += 1
                self.length = None
                disp.set_terminator(4)


class TwoWayNewTasksCategoryCountState(BaseState):
    def init(self, disp, task):
        self.task = task
        disp.set_terminator(4)

    def handleData(self, disp, data):
        self.taskCategoryCount, = struct.unpack('!i', data)

        if self.taskCategoryCount:
            self.setState(TwoWayNewTasksCategoriesState, disp)
        else:
            disp.window.addIPhoneTask(self.task, [])
            disp.pushString(self.task.id())
            self.newTasksCount -= 1
            if self.newTasksCount:
                self.setState(TwoWayNewTasksState, disp)
            else:
                self.setState(TwoWayDeletedTasksState, disp)


class TwoWayNewTasksCategoriesState(BaseState):
    def init(self, disp):
        self.categories = []
        self.length = None
        disp.set_terminator(4)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            if self.length == 0:
                self.handleData('')
            else:
                disp.set_terminator(self.length)
        else:
            self.categories.append(self.categoryMap[data.decode('UTF-8')])
            self.taskCategoryCount -= 1
            if self.taskCategoryCount:
                self.length = None
                disp.set_terminator(4)
            else:
                disp.window.addIPhoneTask(self.task, self.categories)
                disp.pushString(self.task.id())
                self.newTasksCount -= 1
                if self.newTasksCount:
                    self.setState(TwoWayNewTasksState, disp)
                else:
                    self.setState(TwoWayDeletedTasksState, disp)


class TwoWayDeletedTasksState(BaseState):
    def init(self, disp):
        if self.deletedTasksCount:
            self.length = None
            disp.set_terminator(4)
        else:
            self.setState(TwoWayModifiedTasks, disp)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            disp.set_terminator(self.length)
        else:
            try:
                task = self.taskMap[data.decode('UTF-8')]
            except KeyError:
                # Probably deleted on the desktop side as well
                pass
            else:
                del self.taskMap[data.decode('UTF-8')]
                disp.window.removeIPhoneTask(task)

            self.deletedTasksCount -= 1
            if self.deletedTasksCount:
                self.length = None
                disp.set_terminator(4)
            else:
                self.setState(TwoWayModifiedTasks, disp)


class TwoWayModifiedTasks(BaseState):
    def init(self, disp):
        if self.modifiedTasksCount:
            self.length = None
            self.state = 0
            disp.set_terminator(4)
        else:
            self.setState(FullFromDesktopState, disp)

    def finalize(self, disp):
        try:
            task = self.taskMap[self.id_]
        except KeyError:
            # Probably deleted on desktop
            pass
        else:
            disp.window.modifyIPhoneTask(task,
                                         self.subject,
                                         self.description,
                                         self.startDate,
                                         self.dueDate,
                                         self.completionDate,
                                         self.categories)

    def handleData(self, disp, data):
        if self.length is None:
            self.length, = struct.unpack('!i', data)
            if self.state == 6: # Protocol version 2 only
                if self.length:
                    self.categoryCount = self.length
                    self.length = None
                    self.state = 7
                    disp.set_terminator(4)
                else:
                    self.finalize(disp)
                    self.modifiedTasksCount -= 1
                    if self.modifiedTasksCount == 0:
                        self.setState(FullFromDesktopState, disp)
                    else:
                        self.state = 0
                        self.length = None
                        disp.set_terminator(4)
            else:
                if self.length == 0:
                    self.handleData(disp, '')
                else:
                    disp.set_terminator(self.length)
        else:
            if self.state == 0:
                self.categories = None
                self.subject = data.decode('UTF-8')
            elif self.state == 1:
                self.id_ = data.decode('UTF-8')
            elif self.state == 2:
                self.description = data.decode('UTF-8')
            elif self.state == 3:
                self.startDate = parseDate(data)
            elif self.state == 4:
                self.dueDate = parseDate(data)
            elif self.state == 5:
                self.completionDate = parseDate(data)

                if disp.protocolVersion == 1:
                    self.finalize(disp)
                    self.modifiedTasksCount -= 1
                else:
                    self.categories = []
                    self.state = 6
            elif self.state == 7:
                self.categories.append(self.categoryMap[data.decode('UTF-8')])
                self.categoryCount -= 1
                if self.categoryCount == 0:
                    self.finalize(disp)
                    self.modifiedTasksCount -= 1
                    if self.modifiedTasksCount == 0:
                        self.setState(FullFromDesktopState, disp)
                    else:
                        self.state = 0
                        self.length = None
                        disp.set_terminator(4)
                        return

            if disp.protocolVersion == 1 or (disp.protocolVersion == 2 and self.state < 5):
                if self.state == 5 and self.modifiedTasksCount == 0:
                    self.setState(FullFromDesktopState, disp)
                else:
                    self.state = (self.state + 1) % 6

            self.length = None
            disp.set_terminator(4)


class EndState(BaseState):
    def init(self, disp):
        disp.set_terminator(4)

    def handleData(self, disp, data):
        code, = struct.unpack('!i', data) # We don't care right now
        disp.close_when_done()
        self.dlg.Finished()

    def handleClose(self, disp):
        pass
