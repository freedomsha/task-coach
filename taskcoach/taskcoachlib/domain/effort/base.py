"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
# try:
from pubsub import pub

# except ImportError:
#    try:
#        from taskcoachlib.thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
import weakref
from taskcoachlib.domain.base.attribute import Attribute


class BaseEffort(object):
    """
    An effort is a time interval during which work is done on a task.

    It has a start and a stop time.
    It may be a detail effort or a total effort.
    A detail effort is an effort that represents a single time interval
    during which work is done on a task.
    A total effort is an effort that represents the total time spent on a task,
    including all detail efforts and the time spent on its subtasks.

    An effort is associated with a task,
    but it is not a child of the task in the task hierarchy.
    This is because efforts are not composite objects,
    and they do not have children.
    Instead, efforts are associated with tasks through a weak reference,
    which allows them to be garbage collected when the task is deleted.

    Methods :
        task() : Returns the task associated with this effort.
        parent() : Returns the parent of this effort, which is the task associated with this effort.
        getStart() : Returns the start time of this effort.
        getStop() : Returns the stop time of this effort.
        subject() : Returns the subject of the task associated with this effort.
        categories() : Returns the categories of the task associated with this effort.
        foregroundColor() : Returns the foreground color of the task associated with this effort.
        backgroundColor() : Returns the background color of the task associated with this effort.
        font() : Returns the font of the task associated with this effort.
        duration() : Returns the duration of this effort.
        revenue() : Returns the revenue of this effort.
        isTotal() : Returns True if this effort is a total effort, False if it is a detail effort.

        _onStartChanged() : Called when the start time of this effort changes.
        _onStopChanged() : Called when the stop time of this effort changes.
        trackingChangedEventType() : Returns the event type for tracking changes of this effort.
        sendDurationChangedMessage() : Sends a message that the duration of this effort has changed.
        durationChangedEventType() : Returns the event type for duration changes of this effort.
        sendRevenueChangedMessage() : Sends a message that the revenue of this effort has changed.
        revenueChangedEventType() : Returns the event type for revenue changes of this effort.
    """

    def __init__(self, task, start, stop, *args, **kwargs):
        self._task = None if task is None else weakref.ref(task)
        # self._start = start
        self._start = Attribute(start, self, self._onStartChanged)
        # self._stop = stop
        self._stop = Attribute(stop, self, self._onStopChanged)
        super().__init__(*args, **kwargs)

    def task(self):
        """Returns the task associated with this effort."""
        return (
            None if self._task is None else self._task()
        )  # TODO: avec ou sans parenthèses ? attention confusion!

    def parent(self):
        """Returns the parent of this effort, which is the task associated with this effort."""
        # Efforts don't have real parents since they are not composite.
        # However, we pretend the parent of an effort is its task for the
        # benefit of the search filter.
        return self.task()

    def getStart(self):
        """Returns the start time of this effort."""
        # return self._start
        return self._start.get()

    def getStop(self):
        """Returns the stop time of this effort."""
        # return self._stop
        return self._stop.get()

    def subject(self, *args, **kwargs):
        """Returns the subject of the task associated with this effort."""
        return self.task().subject(*args, **kwargs)

    def categories(self, *args, **kwargs):
        """Returns the categories of the task associated with this effort."""
        return self.task().categories(*args, **kwargs)

    def foregroundColor(self, recursive=False):
        """Returns the foreground color of the task associated with this effort."""
        return self.task().foregroundColor(recursive)

    def backgroundColor(self, recursive=False):
        """Returns the background color of the task associated with this effort."""
        return self.task().backgroundColor(recursive)

    def font(self, recursive=False):
        """Returns the font of the task associated with this effort."""
        return self.task().font(recursive)

    def duration(self, recursive=False):
        """Returns the duration of this effort."""
        raise NotImplementedError  # pragma: no cover

    def revenue(self, recursive=False):
        """Returns the revenue of this effort."""
        raise NotImplementedError  # pragma: no cover

    def isTotal(self):
        """Returns True if this effort is a total effort, False if it is a detail effort."""
        return False  # Are we a detail effort or a total effort? For sorting.

    def _onStartChanged(self, event):
        """Called when the start time of this effort changes."""
        pass

    def _onStopChanged(self, event):
        """Called when the stop time of this effort changes."""
        pass

    @classmethod
    def trackingChangedEventType(class_):
        """Returns the event type for tracking changes of this effort."""
        return "pubsub.effort.track"

    def sendDurationChangedMessage(self):
        """Sends a message that the duration of this effort has changed."""
        pub.sendMessage(
            self.durationChangedEventType(),
            newValue=self.duration(),
            # newValue=self.timeSpent(),
            sender=self,
        )  # !!! TODO: should we send the new duration or the new time spent? Or both? Or something else?, Risque de ne pas fonctionner si duration() n'est pas implémenté dans les sous-classes, à vérifier.

    @classmethod
    def durationChangedEventType(class_):
        """Returns the event type for duration changes of this effort."""
        return "pubsub.effort.duration"

    def sendRevenueChangedMessage(self):
        """Sends a message that the revenue of this effort has changed."""
        pub.sendMessage(
            self.revenueChangedEventType(),
            newValue=self.revenue(),
            sender=self,
        )

    @classmethod
    def revenueChangedEventType(class_):
        """Returns the event type for revenue changes of this effort."""
        return "pubsub.effort.revenue"
