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

Cross-platform file system monitoring using the watchdog library.

The watchdog library (https://pypi.org/project/watchdog/) provides:
- Cross-platform support: Linux (inotify), macOS (FSEvents), Windows (ReadDirectoryChangesW)
- Pure Python, actively maintained
- Clean API without reactor integration

This module monitors task files for external modifications (e.g., Dropbox sync,
another instance) and triggers reload prompts.
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from taskcoachlib.powermgt import GUI_NAME

# if GUI_NAME == "wx":
#     import wx
# elif GUI_NAME == "tk":
#     import tkinter as tk

from taskcoachlib.filesystem import base
import os


class TaskFileEventHandler(FileSystemEventHandler):
    """
    Event handler for file system changes.

    Monitors changes to the task file and notifies the parent FilesystemNotifier
    when modifications are detected.
    """

    def __init__(self, notifier):
        super().__init__()
        self._notifier = notifier

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Get the filename being watched
        watched_filename = self._notifier._filename
        if watched_filename is None:
            return

        # Check if this event is for our watched file
        event_filename = os.path.basename(event.src_path)
        watched_basename = os.path.basename(watched_filename)

        if event_filename == watched_basename:
            if self._notifier._check(watched_filename) and watched_filename:
                self._notifier.stamp = os.stat(watched_filename).st_mtime
                # if GUI_NAME == "wx":
                #     # Use wx.CallAfter to ensure callback runs in main thread
                #     wx.CallAfter(self._notifier.onFileChanged)
                # elif GUI_NAME == "tk":
                #     # # For Tkinter, we assume the notifier or a global app handle
                #     # # can dispatch to the main thread.
                #     # from taskcoachlib.config.arguments import get_main_window
                #     # main_window = get_main_window()
                #     # if main_window:
                #     #     main_window.after_idle(self._notifier.onFileChanged)
                #     # For Tkinter, we assume the notifier or a global app handle
                #     # can dispatch to the main thread.
                #     from taskcoachlib.config.arguments import get_main_window
                #     main_window = get_main_window()
                #     if main_window:
                #         main_window.after_idle(self._notifier.onFileChanged)
                #     else:
                #         # Fallback if window not yet initialized
                #         self._notifier.onFileChanged()
                self._notifier.dispatch_to_main_thread(
                    self._notifier.onFileChanged
                )

    def on_created(self, event):
        """Handle file creation events (might be recreated after save)."""
        self.on_modified(event)


class FilesystemNotifier(base.NotifierBase):
    """
    File system notifier using watchdog library.

    Monitors a task file for external changes and triggers callbacks
    when modifications are detected. This allows the application to
    prompt users to reload when files are modified externally.
    """

    def __init__(self, main_window=None):
        super().__init__()
        self._observer = None
        self._event_handler = TaskFileEventHandler(self)
        self._main_window = main_window  # Store the main window reference

    def dispatch_to_main_thread(self, func):
        """Dispatch a function call to the main GUI thread."""
        if GUI_NAME == "wx":
            import wx

            wx.CallAfter(func)
        elif GUI_NAME == "tk":
            if self._main_window:
                self._main_window.after_idle(func)
            else:
                func()  # Fallback if main window is not available
        else:
            func()  # Fallback for unknown GUIs

    def setFilename(self, filename):
        """Set the filename to monitor."""
        # Stop watching old path
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=1.0)
            self._observer = None

        # Update parent class state
        super().setFilename(filename)

        # Start watching new path
        if self._path is not None and os.path.exists(self._path):
            self._observer = Observer()
            self._observer.schedule(
                self._event_handler, self._path, recursive=False
            )
            self._observer.start()

    def stop(self):
        """Stop file system monitoring."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=1.0)
            self._observer = None

    def onFileChanged(self):
        """
        Callback when the watched file changes.

        This method should be overridden by subclasses to handle
        file change notifications.
        """
        raise NotImplementedError
