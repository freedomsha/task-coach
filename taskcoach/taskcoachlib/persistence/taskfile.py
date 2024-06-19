"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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
"""

import os
from . import xml
from taskcoachlib import patterns, operating_system
from taskcoachlib.domain import base, task, category, note, effort, attachment
from taskcoachlib.syncml.config import createDefaultSyncConfig
from taskcoachlib.thirdparty.guid import generate
from taskcoachlib.thirdparty import lockfile
from taskcoachlib.changes import ChangeMonitor, ChangeSynchronizer
from taskcoachlib.filesystem import (
    FilesystemNotifier,
    FilesystemPollerNotifier,
)
from pubsub import pub


def _isCloud(path):
    """
    Check if a given path is in a cloud-synced directory.

    Args:
        path (str): The file path to check.

    Returns:
        bool: True if the path is in a cloud-synced directory, False otherwise.
    """
    path = os.path.abspath(path)
    while True:
        for name in [".dropbox.cache", ".csync_journal.db"]:
            if os.path.exists(os.path.join(path, name)):
                return True
        path, name = os.path.split(path)
        if name == "":
            return False


class TaskCoachFilesystemNotifier(FilesystemNotifier):
    """
    A notifier class to handle file changes for Task Coach.
    """

    def __init__(self, taskFile):
        """
        Initialize the notifier with a TaskFile instance.

        Args:
            taskFile (TaskFile): The TaskFile instance to notify.
        """
        self.__taskFile = taskFile
        super(TaskCoachFilesystemNotifier, self).__init__()

    def onFileChanged(self):
        """
        Handle file changes by notifying the associated TaskFile instance.
        """
        self.__taskFile.onFileChanged()


class TaskCoachFilesystemPollerNotifier(FilesystemPollerNotifier):
    """
    A poller notifier class to handle file changes for Task Coach.
    """

    def __init__(self, taskFile):
        """
        Initialize the poller notifier with a TaskFile instance.

        Args:
            taskFile (TaskFile): The TaskFile instance to notify.
        """
        self.__taskFile = taskFile
        super(TaskCoachFilesystemPollerNotifier, self).__init__()

    def onFileChanged(self):
        """
        Handle file changes by notifying the associated TaskFile instance.
        """
        self.__taskFile.onFileChanged()


class SafeWriteFile(object):
    """
    A class to safely write files, using temporary files to avoid data loss.
    """

    def __init__(self, filename):
        """
        Initialize the SafeWriteFile with a filename.

        Args:
            filename (str): The filename to write to.
        """
        self.__filename = filename
        if self._isCloud():
            # Ideally we should create a temporary file on the same filesystem (so that
            # os.rename works) but outside the Dropbox folder...
            self.__fd = open(self.__filename, "wb")
        else:
            self.__tempFilename = self._getTemporaryFileName(
                os.path.dirname(filename)
            )
            self.__fd = open(self.__tempFilename, "wb")

    def write(self, bf):
        """
        Write data to the file.

        Args:
            bf (bytes): The data to write.
        """
        self.__fd.write(bf)

    def close(self):
        """
        Close the file and safely rename the temporary file if needed.
        """
        self.__fd.close()
        if not self._isCloud():
            if os.path.exists(self.__filename):
                os.remove(self.__filename)
            if self.__filename is not None:
                if os.path.exists(self.__filename):
                    # WTF ?
                    self.__moveFileOutOfTheWay(self.__filename)
                os.rename(self.__tempFilename, self.__filename)

    def __moveFileOutOfTheWay(self, filename):
        """
        Move an existing file out of the way by renaming it.

        Args:
            filename (str): The filename to move.
        """
        index = 1
        while True:
            name, ext = os.path.splitext(filename)
            newName = "%s (%d)%s" % (name, index, ext)
            if not os.path.exists(newName):
                os.rename(filename, newName)
                break
            index += 1

    def _getTemporaryFileName(self, path):
        """Generate a temporary filename.

        All functions/classes in the standard library that can generate
        a temporary file, visible on the file system, without deleting it
        when closed are deprecated (there is tempfile.NamedTemporaryFile
        but its 'delete' argument is new in Python 2.6). This is not
        secure, not thread-safe, but it works.

        Args:
            path (str): The directory path to create the temporary file in.

        Returns:
            str: The generated temporary filename.
        """
        idx = 0
        while True:
            name = os.path.join(path, "tmp-%d" % idx)
            if not os.path.exists(name):
                return name
            idx += 1

    def _isCloud(self):
        """
        Check if the file is in a cloud-synced directory.

        Returns:
            bool: True if the file is in a cloud-synced directory, False otherwise.
        """
        return _isCloud(os.path.dirname(self.__filename))


class TaskFile(patterns.Observer):
    """
    A class to manage the task file, including loading, saving, and monitoring changes.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the TaskFile.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.__filename = self.__lastFilename = ""
        self.__needSave = self.__loading = False
        self.__tasks = task.TaskList()
        self.__categories = category.CategoryList()
        self.__notes = note.NoteContainer()
        self.__efforts = effort.EffortList(self.tasks())
        self.__guid = generate()
        self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        self.__monitor = ChangeMonitor()
        self.__changes = dict()
        self.__changes[self.__monitor.guid()] = self.__monitor
        self.__changedOnDisk = False
        if kwargs.pop("poll", True):
            self.__notifier = TaskCoachFilesystemPollerNotifier(self)
        else:
            self.__notifier = TaskCoachFilesystemNotifier(self)
        self.__saving = False
        for collection in [self.__tasks, self.__categories, self.__notes]:
            self.__monitor.monitorCollection(collection)
        for domainClass in [
            task.Task,
            category.Category,
            note.Note,
            effort.Effort,
            attachment.FileAttachment,
            attachment.URIAttachment,
            attachment.MailAttachment,
        ]:
            self.__monitor.monitorClass(domainClass)
        super(TaskFile, self).__init__(*args, **kwargs)
        # Register for tasks, categories, efforts and notes being changed so we
        # can monitor when the task file needs saving (i.e. is 'dirty'):
        for container in self.tasks(), self.categories(), self.notes():
            for eventType in container.modificationEventTypes():
                self.registerObserver(
                    self.onDomainObjectAddedOrRemoved,
                    eventType,
                    eventSource=container,
                )

        for eventType in (
            base.Object.markDeletedEventType(),
            base.Object.markNotDeletedEventType(),
        ):
            self.registerObserver(self.onDomainObjectAddedOrRemoved, eventType)

        for eventType in task.Task.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onTaskChanged_Deprecated, eventType)
        pub.subscribe(self.onTaskChanged, "pubsub.task")
        for eventType in effort.Effort.modificationEventTypes():
            self.registerObserver(self.onEffortChanged, eventType)
        for eventType in note.Note.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onNoteChanged_Deprecated, eventType)
        pub.subscribe(self.onNoteChanged, "pubsub.note")
        for eventType in category.Category.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onCategoryChanged_Deprecated, eventType
                )
        pub.subscribe(self.onCategoryChanged, "pubsub.category")
        for eventType in (
            attachment.FileAttachment.modificationEventTypes()
            + attachment.URIAttachment.modificationEventTypes()
            + attachment.MailAttachment.modificationEventTypes()
        ):
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onAttachmentChanged_Deprecated, eventType
                )
        pub.subscribe(self.onAttachmentChanged, "pubsub.attachment")

    def __str__(self):
        return self.filename()

    def __contains__(self, item):
        return (
            item in self.tasks()
            or item in self.notes()
            or item in self.categories()
            or item in self.efforts()
        )

    def monitor(self):
        """
        Get the ChangeMonitor instance.

        Returns:
            ChangeMonitor: The ChangeMonitor instance.
        """
        return self.__monitor

    def categories(self):
        """
        Get the CategoryList instance.

        Returns:
            CategoryList: The CategoryList instance.
        """
        return self.__categories

    def notes(self):
        """
        Get the NoteContainer instance.

        Returns:
            NoteContainer: The NoteContainer instance.
        """
        return self.__notes

    def tasks(self):
        """
        Get the TaskList instance.

        Returns:
            TaskList: The TaskList instance.
        """
        return self.__tasks

    def efforts(self):
        """
        Get the EffortList instance.

        Returns:
            EffortList: The EffortList instance.
        """
        return self.__efforts

    def syncMLConfig(self):
        """
        Get the SyncML configuration.

        Returns:
            SyncMLConfig: The SyncML configuration.
        """
        return self.__syncMLConfig

    def guid(self):
        """
        Get the GUID of the task file.

        Returns:
            str: The GUID of the task file.
        """
        return self.__guid

    def changes(self):
        """
        Get the changes dictionary.

        Returns:
            dict: The changes dictionary.
        """
        return self.__changes

    def setSyncMLConfig(self, config):
        """
        Set the SyncML configuration and mark the task file as dirty.

        Args:
            config (SyncMLConfig): The SyncML configuration.
        """
        self.__syncMLConfig = config
        self.markDirty()

    def isEmpty(self):
        """
        Check if the task file is empty.

        Returns:
            bool: True if the task file is empty, False otherwise.
        """
        return (
            0
            == len(self.categories())
            == len(self.tasks())
            == len(self.notes())
        )

    def onDomainObjectAddedOrRemoved(self, event):  # pylint: disable=W0613
        """
        Handle domain object added or removed events.

        Args:
            event (Event): The event.
        """
        if self.__loading or self.__saving:
            return
        self.markDirty()

    def onTaskChanged(self, newValue, sender):
        """
        Handle task changed events.

        Args:
            newValue: The new value.
            sender (Task): The task that changed.
        """
        if self.__loading or self.__saving:
            return
        if sender in self.tasks():
            self.markDirty()

    def onTaskChanged_Deprecated(self, event):
        """
        Handle deprecated task changed events.

        Args:
            event (Event): The event.
        """
        if self.__loading:
            return
        changedTasks = [
            changedTask
            for changedTask in event.sources()
            if changedTask in self.tasks()
        ]
        if changedTasks:
            self.markDirty()
            for changedTask in changedTasks:
                changedTask.markDirty()

    def onEffortChanged(self, event):
        """
        Handle effort changed events.

        Args:
            event (Event): The event.
        """
        if self.__loading or self.__saving:
            return
        changedEfforts = [
            changedEffort
            for changedEffort in event.sources()
            if changedEffort.task() in self.tasks()
        ]
        if changedEfforts:
            self.markDirty()
            for changedEffort in changedEfforts:
                changedEffort.markDirty()

    def onCategoryChanged_Deprecated(self, event):
        """
        Handle deprecated category changed events.

        Args:
            event (Event): The event.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in event.sources()
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Mark all categorizables belonging to the changed category dirty;
            # this is needed because in SyncML/vcard world, categories are not
            # first-class objects. Instead, each task/contact/etc has a
            # categories property which is a comma-separated list of category
            # names. So, when a category name changes, every associated
            # categorizable changes.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onCategoryChanged(self, newValue, sender):
        """
        Handle category changed events.

        Args:
            newValue: The new value.
            sender (Category): The category that changed.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in [sender]
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Mark all categorizables belonging to the changed category dirty;
            # this is needed because in SyncML/vcard world, categories are not
            # first-class objects. Instead, each task/contact/etc has a
            # categories property which is a comma-separated list of category
            # names. So, when a category name changes, every associated
            # categorizable changes.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onNoteChanged_Deprecated(self, event):
        """
        Handle deprecated note changed events.

        Args:
            event (Event): The event.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        for changedNote in event.sources():
            changedNote.markDirty()

    def onNoteChanged(self, newValue, sender):
        """
        Handle note changed events.

        Args:
            newValue: The new value.
            sender (Note): The note that changed.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        sender.markDirty()

    def onAttachmentChanged(self, newValue, sender):
        """
        Handle attachment changed events.

        Args:
            newValue: The new value.
            sender (Attachment): The attachment that changed.
        """
        if self.__loading or self.__saving:
            return
        # Attachments don't know their owner, so we can't check whether the
        # attachment is actually in the task file. Assume it is.
        self.markDirty()

    def onAttachmentChanged_Deprecated(self, event):
        """
        Handle deprecated attachment changed events.

        Args:
            event (Event): The event.
        """
        if self.__loading:
            return
        # Attachments don't know their owner, so we can't check whether the
        # attachment is actually in the task file. Assume it is.
        self.markDirty()
        for changedAttachment in event.sources():
            changedAttachment.markDirty()

    def setFilename(self, filename):
        """
        Set the filename of the task file.

        Args:
            filename (str): The filename to set.
        """
        if filename == self.__filename:
            return
        self.__lastFilename = filename or self.__filename
        self.__filename = filename
        self.__notifier.setFilename(filename)
        pub.sendMessage("taskfile.filenameChanged", filename=filename)

    def filename(self):
        """
        Get the filename of the task file.

        Returns:
            str: The filename of the task file.
        """
        return self.__filename

    def lastFilename(self):
        """
        Get the last filename of the task file.

        Returns:
            str: The last filename of the task file.
        """
        return self.__lastFilename

    def isDirty(self):
        """
        Check if the task file needs to be saved.

        Returns:
            bool: True if the task file needs to be saved, False otherwise.
        """
        return self.__needSave

    def markDirty(self, force=False):
        """
        Mark the task file as dirty (needing to be saved).

        Args:
            force (bool, optional): Whether to force marking as dirty. Defaults to False.
        """
        if force or not self.__needSave:
            self.__needSave = True
            pub.sendMessage("taskfile.dirty", taskFile=self)

    def markClean(self):
        """
        Mark the task file as clean (not needing to be saved).
        """
        if self.__needSave:
            self.__needSave = False
            pub.sendMessage("taskfile.clean", taskFile=self)

    def onFileChanged(self):
        """
        Handle file changes.
        """
        if not self.__saving:
            import wx  # Not really clean but we're in another thread...

            self.__changedOnDisk = True
            wx.CallAfter(pub.sendMessage, "taskfile.changed", taskFile=self)

    @patterns.eventSource
    def clear(self, regenerate=True, event=None):
        """
        Clear the task file, optionally regenerating the GUID and SyncML config.

        Args:
            regenerate (bool, optional): Whether to regenerate the GUID and SyncML config. Defaults to True.
            event (Event, optional): The event. Defaults to None.
        """
        pub.sendMessage("taskfile.aboutToClear", taskFile=self)
        try:
            self.tasks().clear(event=event)
            self.categories().clear(event=event)
            self.notes().clear(event=event)
            if regenerate:
                self.__guid = generate()
                self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        finally:
            pub.sendMessage("taskfile.justCleared", taskFile=self)

    def close(self):
        """
        Close the task file, saving any changes and clearing the contents.
        """
        if os.path.exists(self.filename()):
            changes = xml.ChangesXMLReader(self.filename() + ".delta").read()
            del changes[self.__monitor.guid()]
            xml.ChangesXMLWriter(open(self.filename() + ".delta", "wb")).write(
                changes
            )

        self.setFilename("")
        self.__guid = generate()
        self.clear()
        self.__monitor.reset()
        self.markClean()
        self.__changedOnDisk = False

    def stop(self):
        """
        Stop the filesystem notifier.
        """
        self.__notifier.stop()

    def _read(self, fd):
        """
        Read the task file from a file descriptor.

        Args:
            fd (file): The file descriptor to read from.

        Returns:
            tuple: The read data (tasks, categories, notes, syncMLConfig, changes, guid).
        """
        return xml.XMLReader(fd).read()

    def exists(self):
        """
        Check if the task file exists.

        Returns:
            bool: True if the task file exists, False otherwise.
        """
        return os.path.isfile(self.__filename)

    def _openForWrite(self, suffix=""):
        """
        Open the task file for writing.

        Args:
            suffix (str, optional): The file suffix. Defaults to "".

        Returns:
            SafeWriteFile: The SafeWriteFile instance.
        """
        return SafeWriteFile(self.__filename + suffix)

    def _openForRead(self):
        """
        Open the task file for reading.

        Returns:
            file: The file descriptor for reading.
        """
        return open(self.__filename, "r")

    def load(self, filename=None):
        """
        Load the task file from disk.

        Args:
            filename (str, optional): The filename to load from. Defaults to None.
        """
        pub.sendMessage("taskfile.aboutToRead", taskFile=self)
        self.__loading = True
        if filename:
            self.setFilename(filename)
        try:
            if self.exists():
                fd = self._openForRead()
                try:
                    tasks, categories, notes, syncMLConfig, changes, guid = (
                        self._read(fd)
                    )
                finally:
                    fd.close()
            else:
                tasks = []
                categories = []
                notes = []
                changes = dict()
                guid = generate()
                syncMLConfig = createDefaultSyncConfig(guid)
            self.clear()
            self.__monitor.reset()
            self.__changes = changes
            self.__changes[self.__monitor.guid()] = self.__monitor
            self.categories().extend(categories)
            self.tasks().extend(tasks)
            self.notes().extend(notes)

            def registerOtherObjects(objects):
                for obj in objects:
                    if isinstance(obj, base.CompositeObject):
                        registerOtherObjects(obj.children())
                    if isinstance(obj, note.NoteOwner):
                        registerOtherObjects(obj.notes())
                    if isinstance(obj, attachment.AttachmentOwner):
                        registerOtherObjects(obj.attachments())
                    if isinstance(obj, task.Task):
                        registerOtherObjects(obj.efforts())
                    if (
                        isinstance(obj, note.Note)
                        or isinstance(obj, attachment.Attachment)
                        or isinstance(obj, effort.Effort)
                    ):
                        self.__monitor.setChanges(obj.id(), set())

            registerOtherObjects(self.categories().rootItems())
            registerOtherObjects(self.tasks().rootItems())
            registerOtherObjects(self.notes().rootItems())
            self.__monitor.resetAllChanges()
            self.__syncMLConfig = syncMLConfig
            self.__guid = guid

            if os.path.exists(self.filename()):
                # We need to reset the changes on disk because we're up to date.
                xml.ChangesXMLWriter(
                    open(self.filename() + ".delta", "wb")
                ).write(self.__changes)
        except:
            self.setFilename("")
            raise
        finally:
            self.__loading = False
            self.markClean()
            self.__changedOnDisk = False
            pub.sendMessage("taskfile.justRead", taskFile=self)

    def save(self):
        """
        Save the task file to disk.
        """
        try:
            pub.sendMessage("taskfile.aboutToSave", taskFile=self)
        except:
            pass
        # When encountering a problem while saving (disk full,
        # computer on fire), if we were writing directly to the file,
        # it's lost. So write to a temporary file and rename it if
        # everything went OK.
        self.__saving = True
        try:
            self.mergeDiskChanges()

            if self.__needSave or not os.path.exists(self.__filename):
                fd = self._openForWrite()
                try:
                    xml.XMLWriter(fd).write(
                        self.tasks(),
                        self.categories(),
                        self.notes(),
                        self.syncMLConfig(),
                        self.guid(),
                    )
                finally:
                    fd.close()

            self.markClean()
        finally:
            self.__saving = False
            self.__notifier.saved()
            try:
                pub.sendMessage("taskfile.justSaved", taskFile=self)
            except:
                pass

    def mergeDiskChanges(self):
        """
        Merge changes from disk with the current task file.
        """
        self.__loading = True
        try:
            if os.path.exists(
                self.__filename
            ):  # Not using self.exists() because DummyFile.exists returns True
                # Instead of writing the content of memory, merge changes
                # with the on-disk version and save the result.
                self.__monitor.freeze()
                try:
                    fd = self._openForRead()
                    (
                        tasks,
                        categories,
                        notes,
                        syncMLConfig,
                        allChanges,
                        guid,
                    ) = self._read(fd)
                    fd.close()

                    self.__changes = allChanges

                    if self.__saving:
                        for devGUID, changes in list(self.__changes.items()):
                            if devGUID != self.__monitor.guid():
                                changes.merge(self.__monitor)

                    sync = ChangeSynchronizer(self.__monitor, allChanges)

                    sync.sync(
                        [
                            (
                                self.categories(),
                                category.CategoryList(categories),
                            ),
                            (self.tasks(), task.TaskList(tasks)),
                            (self.notes(), note.NoteContainer(notes)),
                        ]
                    )

                    self.__changes[self.__monitor.guid()] = self.__monitor
                finally:
                    self.__monitor.thaw()
            else:
                self.__changes = {self.__monitor.guid(): self.__monitor}

            self.__monitor.resetAllChanges()
            fd = self._openForWrite(".delta")
            try:
                xml.ChangesXMLWriter(fd).write(self.changes())
            finally:
                fd.close()

            self.__changedOnDisk = False
        finally:
            self.__loading = False

    def saveas(self, filename):
        """
        Save the task file under a new filename.

        Args:
            filename (str): The new filename to save as.
        """
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(filename + ".delta"):
            os.remove(filename + ".delta")
        self.setFilename(filename)
        self.save()

    def merge(self, filename):
        """
        Merge another task file into this one.

        Args:
            filename (str): The filename of the task file to merge.
        """
        mergeFile = self.__class__()
        mergeFile.load(filename)
        self.__loading = True
        categoryMap = dict()
        self.tasks().removeItems(
            self.objectsToOverwrite(self.tasks(), mergeFile.tasks())
        )
        self.rememberCategoryLinks(categoryMap, self.tasks())
        self.tasks().extend(mergeFile.tasks().rootItems())
        self.notes().removeItems(
            self.objectsToOverwrite(self.notes(), mergeFile.notes())
        )
        self.rememberCategoryLinks(categoryMap, self.notes())
        self.notes().extend(mergeFile.notes().rootItems())
        self.categories().removeItems(
            self.objectsToOverwrite(self.categories(), mergeFile.categories())
        )
        self.categories().extend(mergeFile.categories().rootItems())
        self.restoreCategoryLinks(categoryMap)
        mergeFile.close()
        self.__loading = False
        self.markDirty(force=True)

    def objectsToOverwrite(self, originalObjects, objectsToMerge):
        """
        Get the objects to overwrite during a merge.

        Args:
            originalObjects (list): The original objects.
            objectsToMerge (list): The objects to merge.

        Returns:
            list: The objects to overwrite.
        """
        objectsToOverwrite = []
        for domainObject in objectsToMerge:
            try:
                objectsToOverwrite.append(
                    originalObjects.getObjectById(domainObject.id())
                )
            except IndexError:
                pass
        return objectsToOverwrite

    def rememberCategoryLinks(self, categoryMap, categorizables):
        """
        Remember the category links for later restoration.

        Args:
            categoryMap (dict): The category map.
            categorizables (list): The categorizable objects.
        """
        for categorizable in categorizables:
            for categoryToLinkLater in categorizable.categories():
                categoryMap.setdefault(categoryToLinkLater.id(), []).append(
                    categorizable
                )

    def restoreCategoryLinks(self, categoryMap):
        """
        Restore the category links from the remembered category map.

        Args:
            categoryMap (dict): The category map.
        """
        categories = self.categories()
        for categoryId, categorizables in categoryMap.items():
            try:
                categoryToLink = categories.getObjectById(categoryId)
            except IndexError:
                continue  # Subcategory was removed by the merge
            for categorizable in categorizables:
                categorizable.addCategory(categoryToLink)
                categoryToLink.addCategorizable(categorizable)

    def needSave(self):
        """
        Check if the task file needs to be saved.

        Returns:
            bool: True if the task file needs to be saved, False otherwise.
        """
        return not self.__loading and self.__needSave

    def changedOnDisk(self):
        """
        Check if the task file has changed on disk.

        Returns:
            bool: True if the task file has changed on disk, False otherwise.
        """
        return self.__changedOnDisk

    def beginSync(self):
        """
        Begin a synchronization operation.
        """
        self.__loading = True

    def endSync(self):
        """
        End a synchronization operation.
        """
        self.__loading = False
        self.markDirty()


class DummyLockFile(object):
    """
    A dummy lock file class for use in cloud-synced directories.
    """

    def acquire(self, timeout=None):
        pass

    def release(self):
        pass

    def is_locked(self):
        return True

    def i_am_locking(self):
        return True

    def break_lock(self):
        pass


class LockedTaskFile(TaskFile):
    """LockedTaskFile adds cooperative locking to the TaskFile.

    A TaskFile class with cooperative locking to prevent concurrent access.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the LockedTaskFile.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        super(LockedTaskFile, self).__init__(*args, **kwargs)
        self.__lock = None

    def __isFuse(self, path):
        """
        Check if a given path is a FUSE filesystem.

        Args:
            path (str): The path to check.

        Returns:
            bool: True if the path is a FUSE filesystem, False otherwise.
        """
        if operating_system.isGTK() and os.path.exists("/proc/mounts"):
            for line in open("/proc/mounts", "r", encoding="utf-8"):
                try:
                    location, mountPoint, fsType, options, a, b = (
                        line.strip().split()
                    )
                except:
                    pass
                if os.path.abspath(path).startswith(
                    mountPoint
                ) and fsType.startswith("fuse."):
                    return True
        return False

    def __isCloud(self, filename):
        """
        Check if a file is in a cloud-synced directory.

        Args:
            filename (str): The filename to check.

        Returns:
            bool: True if the file is in a cloud-synced directory, False otherwise.
        """
        return _isCloud(os.path.dirname(filename))

    def __createLockFile(self, filename):
        """
        Create a lock file for the given filename.

        Args:
            filename (str): The filename to create a lock file for.

        Returns:
            FileLock or DummyLockFile: The lock file instance.
        """
        if operating_system.isWindows() and self.__isCloud(filename):
            return DummyLockFile()
        if self.__isFuse(filename):
            return lockfile.MkdirFileLock(filename)
        return lockfile.FileLock(filename)

    def is_locked(self):
        """
        Check if the task file is locked.

        Returns:
            bool: True if the task file is locked, False otherwise.
        """
        return self.__lock and self.__lock.is_locked()

    def is_locked_by_me(self):
        """
        Check if the task file is locked by the current process.

        Returns:
            bool: True if the task file is locked by the current process, False otherwise.
        """
        return self.is_locked() and self.__lock.i_am_locking()

    def release_lock(self):
        """
        Release the lock on the task file.
        """
        if self.is_locked_by_me():
            self.__lock.release()

    def acquire_lock(self, filename):
        """
        Acquire a lock on the task file.

        Args:
            filename (str): The filename to lock.
        """
        if not self.is_locked_by_me():
            self.__lock = self.__createLockFile(filename)
            self.__lock.acquire(5)

    def break_lock(self, filename):
        """
        Break the lock on the task file.

        Args:
            filename (str): The filename to break the lock on.
        """
        self.__lock = self.__createLockFile(filename)
        self.__lock.break_lock()

    def close(self):
        """
        Close the task file, releasing the lock.
        """
        if self.filename() and os.path.exists(self.filename()):
            self.acquire_lock(self.filename())
        try:
            super(LockedTaskFile, self).close()
        finally:
            self.release_lock()

    def load(
        self, filename=None, lock=True, breakLock=False
    ):  # pylint: disable=W0221
        """Lock the file before we load, if not already locked.

        Load the task file from disk, acquiring a lock if necessary.

        Args:
            filename (str, optional): The filename to load from. Defaults to None.
            lock (bool, optional): Whether to acquire a lock. Defaults to True.
            breakLock (bool, optional): Whether to break an existing lock. Defaults to False.
        """
        filename = filename or self.filename()
        try:
            if lock and filename:
                if breakLock:
                    self.break_lock(filename)
                self.acquire_lock(filename)
            return super(LockedTaskFile, self).load(filename)
        finally:
            self.release_lock()

    def save(self, **kwargs):
        """Lock the file before we save, if not already locked.

        Save the task file to disk, acquiring a lock if necessary.

        Args:
            **kwargs: Additional keyword arguments.
        """
        self.acquire_lock(self.filename())
        try:
            return super(LockedTaskFile, self).save(**kwargs)
        finally:
            self.release_lock()

    def mergeDiskChanges(self):
        """
        Merge changes from disk with the current task file, acquiring a lock if necessary.
        """
        self.acquire_lock(self.filename())
        try:
            super(LockedTaskFile, self).mergeDiskChanges()
        finally:
            self.release_lock()
