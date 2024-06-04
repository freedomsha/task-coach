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

from taskcoachlib import operating_system


class AbstractNotifier(object):
    """
    Abstract base class for interfacing with notification systems
    (Growl, Snarl...).
    """

    notifiers = {}
    _enabled = True

    def getName(self):
        raise NotImplementedError

    def isAvailable(self):
        raise NotImplementedError

    def notify(self, title, summary, bitmap, **kwargs):
        raise NotImplementedError

    @classmethod
    def register(cls, notifier):
        if notifier.isAvailable():
            cls.notifiers[notifier.getName()] = notifier

    @classmethod
    def get(cls, name):
        return cls.notifiers.get(name, None)

    @classmethod
    def getSimple(cls):
        """
        Returns a notifier suitable for simple notifications. This
        defaults to Growl/Snarl depending on their availability.
        """

        if cls._enabled:
            if operating_system.isMac():
                return cls.get("Growl") or cls.get("Task Coach")
            elif operating_system.isWindows():
                return cls.get("Snarl") or cls.get("Task Coach")
            else:
                return cls.get("Task Coach")
        else:

            class DummyNotifier(AbstractNotifier):
                def getName(self):
                    return "Dummy"

                def isAvailable(self):
                    return True

                def notify(self, title, summary, bitmap, **kwargs):
                    pass

            return DummyNotifier()

    @classmethod
    def disableNotifications(cls):
        cls._enabled = False

    @classmethod
    def names(cls):
        names = list(cls.notifiers.keys())
        names.sort()
        return names
