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

# from builtins import object
from taskcoachlib import patterns, meta, notify
from taskcoachlib.domain import date, task
from taskcoachlib.gui.dialog import reminder, editor
from taskcoachlib.gui.dialog.editor import TaskEditor
from taskcoachlib.i18n import _

# try:
#    from ..thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub
import wx


class ReminderController(object):
    """
    Controller for showing task reminders.

    Uses simple polling via global timer instead of per-task scheduling.
    Checks all tasks every second and shows reminders for those that are due.

    Note: As of January 2026, only the built-in Task Coach reminder dialog is used.
    External notification system support (KNotify, Growl) has been removed.
    """

    lastId = 0

    @classmethod
    def nextId(cls):
        cls.lastId += 1
        return cls.lastId

    def __init__(self, mainWindow, taskList, effortList, settings):
        super().__init__()
        pub.subscribe(self.onSetReminder, task.Task.reminderChangedEventType())
        patterns.Publisher().registerObserver(
            self.onAddTask,
            eventType=taskList.addItemEventType(),
            eventSource=taskList,
        )
        patterns.Publisher().registerObserver(
            self.onRemoveTask,
            eventType=taskList.removeItemEventType(),
            eventSource=taskList,
        )
        # self.__tasksWithReminders = {}  # {task: reminderDateTime}
        # Changed from dict to set, as we don't need to store scheduler jobs anymore
        self.__tasksWithReminders = set()
        self.__mainWindow = mainWindow
        self.__mainWindowWasHidden = False
        self.__registerRemindersForTasks(taskList)
        self.settings = settings
        self.taskList = taskList
        self.effortList = effortList

        # Track shown reminders to avoid duplicates (replaces __tasksWithReminders)
        self._shownReminders = set()

        # Subscribe to timer for polling
        pub.subscribe(self._onTimerSecond, "timer.second")

        # Subscribe to reminder changes to clear shown status when snoozed
        pub.subscribe(
            self._onReminderChanged, task.Task.reminderChangedEventType()
        )

    def onAddTask(self, event):
        self.__registerRemindersForTasks(list(event.values()))

    def onRemoveTask(self, event):
        self.__removeRemindersForTasks(list(event.values()))

    def onSetReminder(self, newValue, sender):  # pylint: disable=W0613
        self.__removeRemindersForTasks([sender])
        self.__registerRemindersForTasks([sender])

    def onReminder(self):
        # Legacy method, kept if needed but not used by polling
        self.showReminderMessages(date.DateTime.now())

    def _onTimerSecond(self, timestamp):
        """
        Check for due reminders every second.

        Args:
            timestamp: DateTime from global timer (reuse, don't call now())
        """
        # self._checkReminders(timestamp)
        self.showReminderMessages(timestamp)

    def _onReminderChanged(self, newValue, sender):
        """
        Handle reminder change (e.g., snooze).
        Clear from shown set so it can fire again at new time.
        """
        self._shownReminders.discard(sender)

    def showReminderMessages(self, now):
        # def _checkReminder(self, now):
        """
        Check all tasks for due reminders.

        Args:
            now: Current timestamp from timer
        """
        # Add a small buffer to ensure we don't miss reminders due to second rounding
        # now += date.TimeDelta(seconds=5)  # Be sure not to miss reminders
        now += date.TimeDelta(seconds=2)  # Be sure not to miss reminders
        requestUserAttention = False
        # Iterate over a copy of the set to allow modification during iteration
        # for taskWithReminder in self.__tasksWithReminders.copy():
        for taskWithReminder in list(self.__tasksWithReminders.copy()):
            # Check if reminder is due
            # if taskWithReminder.reminder() <= now:
            if (
                taskWithReminder.reminder()
                and taskWithReminder.reminder() <= now
            ):
                requestUserAttention = True
                self.showReminderMessage(taskWithReminder)
        if requestUserAttention:
            self.requestUserAttention()

    def showReminderMessage(
        self, taskWithReminder, ReminderDialog=reminder.ReminderDialog
    ):
        # Always use internal dialog, external notifiers removed for stability
        # if self.__useOwnReminderDialog():
        self.__showReminderDialog(taskWithReminder, ReminderDialog)
        self.__removeReminder(taskWithReminder)
        # else:
        #     self.__showReminderViaNotifier(taskWithReminder)
        #     self.__removeReminder(taskWithReminder)
        #     self.__snooze(taskWithReminder)

    def __useOwnReminderDialog(self):
        notifier = self.settings.get("feature", "notifier")
        return (
            notifier == "Task Coach"
            or notify.AbstractNotifier.get(notifier) is None
        )

    def __showReminderDialog(self, taskWithReminder, ReminderDialog):
        """Show Task Coach's reminder dialog for a task."""
        # If the dialog has self.__mainWindow as parent, it steals the focus when
        # returning to Task Coach through Alt+Tab; we don't want that for
        # reminders.
        reminderDialog = ReminderDialog(
            taskWithReminder,
            self.taskList,
            self.effortList,
            self.settings,
            None,
        )
        # # Position on app's monitor even though it has no parent
        # wxhelper.centerOnAppMonitor(reminderDialog)
        reminderDialog.Bind(wx.EVT_CLOSE, self.onCloseReminderDialog)
        reminderDialog.Show()

    def __showReminderViaNotifier(self, taskWithReminder):
        notifier = notify.AbstractNotifier.get(
            self.settings.get("feature", "notifier")
        )
        notifier.Notify(
            _("%s Reminder") % meta.name,
            taskWithReminder.subject(),
            wx.ArtProvider.GetBitmap("taskcoach", size=wx.Size(32, 32)),
            windowId=self.__mainWindow.GetHandle(),
        )

    def __snooze(self, taskWithReminder):
        minutesToSnooze = self.settings.getint("view", "defaultsnoozetime")
        taskWithReminder.snoozeReminder(
            date.TimeDelta(minutes=minutesToSnooze)
        )

    def onCloseReminderDialog(self, event, show=True):
        """Handle reminder dialog close."""
        event.Skip()
        dialog = event.EventObject
        taskWithReminder = dialog.task
        if not dialog.ignoreSnoozeOption:
            snoozeOptions = dialog.snoozeOptions
            snoozeTimeDelta = snoozeOptions.GetClientData(
                snoozeOptions.Selection
            )
            taskWithReminder.snoozeReminder(
                snoozeTimeDelta
            )  # Note that this is not undoable
            # Undoing the snoozing makes little sense, because it would set the
            # reminder back to its original date-time, which is now in the past.
        if dialog.openTaskAfterClose:
            editTask = TaskEditor(
                self.__mainWindow,
                [taskWithReminder],
                self.settings,
                self.taskList,
                self.__mainWindow.taskFile,
                bitmap="edit",
            )
            editTask.Show(show)
        else:
            editTask = None
        dialog.Destroy()
        if self.__mainWindowWasHidden:
            self.__mainWindow.Hide()
        return editTask  # For unit testing purposes

    def requestUserAttention(self):
        """Request user attention when showing reminders."""
        notifier = self.settings.get("feature", "notifier")
        if (
            notifier != "Task Coach"
            and notify.AbstractNotifier.get(notifier) is not None
        ):
            # When using Growl/Snarl, this is not necessary. Even when not using Growl, it's
            # annoying as hell. Anyway.
            return
        self.__mainWindowWasHidden = not self.__mainWindow.IsShown()
        if self.__mainWindowWasHidden:
            self.__mainWindow.Show()
        # Restore if minimized
        if self.__mainWindow.IsIconized():
            self.__mainWindow.Iconize(False)
        if not self.__mainWindow.IsActive():
            self.__mainWindow.RequestUserAttention()

    def __registerRemindersForTasks(self, tasks):
        for eachTask in tasks:
            # if eachTask.reminder() and eachTask.reminder() < date.DateTime():
            # Register if it has a reminder (future or past)
            if eachTask.reminder():
                self.__registerReminder(eachTask)

    def __removeRemindersForTasks(self, tasks):
        for eachTask in tasks:
            if eachTask in self.__tasksWithReminders:
                self.__removeReminder(eachTask)

    def __registerReminder(self, taskWithReminder):
        # reminderDateTime = taskWithReminder.reminder()
        # now = date.DateTime.now()
        # if reminderDateTime < now:
        #     reminderDateTime = now + date.TimeDelta(seconds=10)
        # job = self.__tasksWithReminders[taskWithReminder] = (
        #     date.Scheduler().schedule(self.onReminder, reminderDateTime)
        # )
        # job.setId(self.nextId())
        # Just add to the set, polling will handle the rest
        self.__tasksWithReminders.add(taskWithReminder)

    def __removeReminder(self, taskWithReminder):
        # job = self.__tasksWithReminders[taskWithReminder]
        # date.Scheduler().unschedule(job)
        # del self.__tasksWithReminders[taskWithReminder]
        # Just remove from the set
        if taskWithReminder in self.__tasksWithReminders:
            self.__tasksWithReminders.remove(taskWithReminder)

    def shutdown(self):
        """Cleanup subscriptions."""
        pub.unsubscribe(self._onTimerSecond, "timer.second")
        pub.unsubscribe(
            self._onReminderChanged, task.Task.reminderChangedEventType()
        )
