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
import time
import threading
from taskcoachlib.filesystem import base


class FilesystemPollerNotifier(base.NotifierBase, threading.Thread):
    """
    Notifier class that polls the filesystem for changes.

    This class extends the base `NotifierBase` class and uses threading to periodically check
    if the associated file has been modified. If a modification is detected, the `onFileChanged`
    method is called.

    Attributes:
        lock (threading.RLock): A reentrant lock for thread safety.
        cancelled (bool): Flag indicating whether the notifier has been cancelled.
        evt (threading.Event): An event used for synchronization.
    """

    def __init__(self):
        super(FilesystemPollerNotifier, self).__init__()

        self.lock = threading.RLock()
        self.cancelled = False
        self.evt = threading.Event()

        # self.setDaemon(True) is obsolete
        self.daemon = True
        self.start()

    def setFilename(self, filename):
        """
        Set the filename associated with the notifier.

        Args:
            filename (str): The filename to set.
        """
        self.lock.acquire()
        try:
            super(FilesystemPollerNotifier, self).setFilename(filename)
        finally:
            self.lock.release()

    def run(self):
        """
        Run the notifier thread.

        This method periodically checks if the associated file has been modified.
        If a modification is detected, the `onFileChanged` method is called.
        """
        try:
            while not self.cancelled:
                self.lock.acquire()
                try:
                    if self._filename and os.path.exists(self._filename):
                        stamp = os.stat(self._filename).st_mtime
                        if stamp > self.stamp:
                            self.stamp = stamp
                            self.onFileChanged()
                finally:
                    self.lock.release()

                self.evt.wait(10)
        except TypeError:
            pass

    def stop(self):
        """
        Stop the notifier.

        This method cancels the notifier thread.
        """
        self.cancelled = True
        self.evt.set()
        self.join()

    def saved(self):
        """
        Update the modification timestamp based on the file.

        This method should be called after the file has been saved.

        Note:
            If the filename is not set or the file does not exist, the timestamp is set to None.
        """
        with self.lock:
            super(FilesystemPollerNotifier, self).saved()

    def onFileChanged(self):
        """
        Handle the file change event.

        This method should be overridden by subclasses to perform specific actions
        when the associated file is modified.
        """
        raise NotImplementedError
