"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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
import atexit


class NotifierBase(object):
    """
    Base class for notifiers.

    This class provides a basic structure for implementing notifiers in TaskCoach.
    Subclasses should override the `stop` method if needed.

    Attributes:
        _filename (str): The filename associated with the notifier.
        _path (str): The path of the file.
        _name (str): The name of the file.
        stamp (float): The modification timestamp of the file.
    """

    def __init__(self):
        super(NotifierBase, self).__init__()

        self._filename = None
        self._path = None
        self._name = None
        self.stamp = None
        atexit.register(self.__stopWhenExit)

    def __stopWhenExit(self):
        self.stop()

    def stop(self):
        """
        Stop the notifier.

        This method should be overridden by subclasses if needed.
        """
        pass

    def _check(self, filename):
        """
        Check if the file has been modified.

        Args:
            filename (str): The filename to check.

        Returns:
            bool: True if the file has been modified, False otherwise.
        """
        return self.stamp is None or (
            filename
            and os.path.exists(filename)
            and os.stat(filename).st_mtime > self.stamp
        )

    def setFilename(self, filename):
        """
        Set the filename associated with the notifier.

        Args:
            filename (str): The filename to set.
        """
        self._filename = filename
        self.stamp = None
        if filename:
            self._path, self._name = os.path.split(filename)
            if os.path.exists(filename):
                self.stamp = os.stat(filename).st_mtime
        else:
            self._path, self._name = None, None

    def saved(self):
        """
        Update the modification timestamp based on the file.

        This method should be called after the file has been saved.

        Note:
            If the filename is not set or the file does not exist, the timestamp is set to None.
        """
        if self._filename and os.path.exists(self._filename):
            self.stamp = os.stat(self._filename).st_mtime
        else:
            self.stamp = None
