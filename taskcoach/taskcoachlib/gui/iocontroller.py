# -*- coding: utf-8 -*-

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

from taskcoachlib import meta, persistence, patterns, operating_system
from taskcoachlib.i18n import _
from taskcoachlib.thirdparty import lockfile
from taskcoachlib.widgets import GetPassword
from taskcoachlib.workarounds import ExceptionAsUnicode
from taskcoachlib.gui.dialog import BackupManagerDialog
import wx
import os
import gc
import sys
import codecs
import traceback

try:
    from taskcoachlib.syncml import sync
except ImportError:  # pragma: no cover
    # Unsupported platform.
    pass


class IOController(object):
    """IOController is responsible for opening, closing, loading,
    saving, and exporting files. It also presents the necessary dialogs
    to let the user specify what file to load/save/etc."""

    def __init__(self, taskFile, messageCallback, settings, splash=None):
        super(IOController, self).__init__()
        self.__taskFile = taskFile
        self.__messageCallback = messageCallback
        self.__settings = settings
        self.__splash = splash
        defaultPath = os.path.expanduser("~")
        self.__tskFileSaveDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "tsk",
            "wildcard": _("%s files (*.tsk)|*.tsk|All files (*.*)|*")
            % meta.name,
        }
        self.__tskFileOpenDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "tsk",
            "wildcard": _(
                "%s files (*.tsk)|*.tsk|Backup files (*.tsk.bak)|*.tsk.bak|"
                "All files (*.*)|*"
            )
            % meta.name,
        }
        self.__icsFileDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "ics",
            "wildcard": _("iCalendar files (*.ics)|*.ics|All files (*.*)|*"),
        }
        self.__htmlFileDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "html",
            "wildcard": _("HTML files (*.html)|*.html|All files (*.*)|*"),
        }
        self.__csvFileDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "csv",
            "wildcard": _(
                "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|"
                "All files (*.*)|*"
            ),
        }
        self.__todotxtFileDialogOpts = {
            "default_path": defaultPath,
            "default_extension": "txt",
            "wildcard": _("Todo.txt files (*.txt)|*.txt|All files (*.*)|*"),
        }
        self.__errorMessageOptions = dict(
            caption=_("%s file error") % meta.name, style=wx.ICON_ERROR
        )

    def syncMLConfig(self):
        """Returns the task file sync configuration.

        Returns:
            dict: The task file sync configuration.
        """
        return self.__taskFile.syncMLConfig()

    def setSyncMLConfig(self, config):
        """Sets the task file synchronization configuration.

        Args:
            config (dict): The new synchronization configuration.

        Returns :
            None
        """
        self.__taskFile.setSyncMLConfig(config)

    def needSave(self):
        """Returns True if the task file has been modified since the last backup, False otherwise.

        Returns :
            bool
        """
        return self.__taskFile.needSave()

    def changedOnDisk(self):
        """Returns True if the task file has been modified on disk since the last opening, False otherwise.

        Returns :
            bool
        """
        return self.__taskFile.changedOnDisk()

    def hasDeletedItems(self):
        """Returns True if there are deleted tasks or notes in the task file, False otherwise.

        Returns :
            bool
        """
        return bool(
            [task for task in self.__taskFile.tasks() if task.isDeleted()]
            + [note for note in self.__taskFile.notes() if note.isDeleted()]
        )

    def purgeDeletedItems(self):
        """Permanently deletes deleted tasks and notes from the task file.

        Returns :
            None
        """
        self.__taskFile.tasks().removeItems(
            [task for task in self.__taskFile.tasks() if task.isDeleted()]
        )
        self.__taskFile.notes().removeItems(
            [note for note in self.__taskFile.notes() if note.isDeleted()]
        )

    def openAfterStart(self, commandLineArgs):
        """Open either the file specified on the command line, or the file
        the user was working on previously, or none at all.

        Args :
            commandLineArgs (list): List of command line arguments.

        Returns :
            None
        """
        if commandLineArgs:
            if isinstance(commandLineArgs, str):
                filename = commandLineArgs[0]
            else:
                filename = commandLineArgs[0].decode(
                    sys.getfilesystemencoding()
                )
        else:
            filename = self.__settings.get("file", "lastfile")
        if filename:
            # Use CallAfter so that the main window is opened first and any
            # error messages are shown on top of it
            wx.CallAfter(self.open, filename)

    def open(
        self,
        filename=None,
        showerror=wx.MessageBox,
        fileExists=os.path.exists,
        breakLock=False,
        lock=True,
    ):
        """The method Opens a task file.

        Allows you to open a task file.

        If the file has been modified since the last save,
        the user is prompted to save changes.

        If the file exists, it is loaded and locked if necessary.

        If the file does not exist, an error is displayed.

        Args:
            filename (str): The name of the file to open. If None, the user is prompted to choose a file.
            showerror (callable): The function to use to display error messages.
            fileExists (callable): The function to use to check if the file exists.
            breakLock (bool): If True, allows you to force the opening of the file even if it is locked.
            lock (bool): If True, locks the file after opening.

        Returns :
            None
        """
        if self.__taskFile.needSave():
            if not self.__saveUnsavedChanges():
                return
        if not filename:
            filename = self.__askUserForFile(
                _("Open"), self.__tskFileOpenDialogOpts
            )
        if not filename:
            return
        self.__updateDefaultPath(filename)
        if fileExists(filename):
            self.__closeUnconditionally()
            self.__addRecentFile(filename)
            try:
                try:
                    self.__taskFile.load(
                        filename, lock=lock, breakLock=breakLock
                    )
                except:
                    # Need to destroy splash screen first because it may
                    # interfere with dialogs we show later on Mac OS X
                    if self.__splash:
                        self.__splash.Destroy()
                    raise
            except lockfile.LockTimeout:
                if breakLock:
                    if self.__askOpenUnlocked(filename):
                        self.open(filename, showerror, lock=False)
                elif self.__askBreakLock(filename):
                    self.open(filename, showerror, breakLock=True)
                else:
                    return
            except lockfile.LockFailed:
                if self.__askOpenUnlocked(filename):
                    self.open(filename, showerror, lock=False)
                else:
                    return
            except persistence.xml.reader.XMLReaderTooNewException:
                self.__showTooNewErrorMessage(filename, showerror)
                return
            except Exception:
                self.__showGenericErrorMessage(
                    filename, showerror, showBackups=True
                )
                return
            self.__messageCallback(
                _("Loaded %(nrtasks)d tasks from " "%(filename)s")
                % dict(
                    nrtasks=len(self.__taskFile.tasks()),
                    filename=self.__taskFile.filename(),
                )
            )
        else:
            errorMessage = (
                _("Cannot open %s because it doesn't exist") % filename
            )
            # Use CallAfter on Mac OS X because otherwise the app will hang:
            if operating_system.isMac():
                wx.CallAfter(
                    showerror, errorMessage, **self.__errorMessageOptions
                )
            else:
                showerror(errorMessage, **self.__errorMessageOptions)
            self.__removeRecentFile(filename)

    def merge(self, filename=None, showerror=wx.MessageBox):
        """Method allows you to merge a task file with the current file.

        Args:
            filename (str): The name of the file to merge. If None, the user is prompted to choose a file.
            showerror (callable): The function to use to display error messages.

        Returns :
            None
        """
        if not filename:
            filename = self.__askUserForFile(
                _("Merge"), self.__tskFileOpenDialogOpts
            )
        if filename:
            try:
                self.__taskFile.merge(filename)
            except lockfile.LockTimeout:
                showerror(
                    _("Cannot open %(filename)s\nbecause it is locked.")
                    % dict(filename=filename),
                    **self.__errorMessageOptions
                )
                return
            except persistence.xml.reader.XMLReaderTooNewException:
                self.__showTooNewErrorMessage(filename, showerror)
                return
            except Exception:
                self.__showGenericErrorMessage(filename, showerror)
                return
            self.__messageCallback(
                _("Merged %(filename)s") % dict(filename=filename)
            )
            self.__addRecentFile(filename)

    def save(self, showerror=wx.MessageBox):
        """The method saves the current task file.

        If the file has not yet been saved,
        the user is prompted to choose a file name.
        If the file has been modified since the last backup,
        it displays a dialog box to ask
        the user to confirm the backup.

        Args:
            showerror (callable): The function.
        """
        if self.__taskFile.filename():
            if self._saveSave(self.__taskFile, showerror):
                return True
            else:
                return self.saveas(showerror=showerror)
        elif not self.__taskFile.isEmpty():
            return self.saveas(showerror=showerror)  # Ask for filename
        else:
            return False

    def mergeDiskChanges(self):
        """The mergeDiskChanges method allows you to merge the
        modifications made to the task file on the disk with the current file.

                If the file has been modified since the last backup,
                it displays a dialog box to ask the user to confirm the backup.
        """
        self.__taskFile.mergeDiskChanges()

    def saveas(
        self, filename=None, showerror=wx.MessageBox, fileExists=os.path.exists
    ):
        """The method saves the current task file under a new name.

        Save the task file currently open in the application under a new file name.

        If no file name is specified, it displays a dialog box to
        ask the user to select a file name.

        If the file already exists, it displays a dialog box to ask the user
        to confirm overwriting the existing file."""
        if not filename:
            filename = self.__askUserForFile(
                _("Save as"),
                self.__tskFileSaveDialogOpts,
                flag=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                fileExists=fileExists,
            )
            if not filename:
                return False  # User didn't enter a filename, cancel save
        if self._saveSave(self.__taskFile, showerror, filename):
            return True
        else:
            return self.saveas(showerror=showerror)  # Try again

    def saveselection(
        self,
        tasks,
        filename=None,
        showerror=wx.MessageBox,
        TaskFileClass=persistence.TaskFile,
        fileExists=os.path.exists,
    ):
        if not filename:
            filename = self.__askUserForFile(
                _("Save selection"),
                self.__tskFileSaveDialogOpts,
                flag=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                fileExists=fileExists,
            )
            if not filename:
                return False  # User didn't enter a filename, cancel save
        selectionFile = self._createSelectionFile(tasks, TaskFileClass)
        if self._saveSave(selectionFile, showerror, filename):
            return True
        else:
            return self.saveselection(
                tasks, showerror=showerror, TaskFileClass=TaskFileClass
            )  # Try again

    def _createSelectionFile(self, tasks, TaskFileClass):
        """Creates a new task file from a selection of tasks.

        This method is an internal method of the IOController class.
        It allows you to create a new task file (TaskFile)
        from a selection of tasks.

        The method takes as parameter a list of selected tasks
        and a class TaskFileClass which allows you to create
        an instance of the TaskFile class.

        The method creates a new empty task file,
        then adds the selected tasks to it.
        It also adds the categories used by the selected tasks,
        as well as the parent categories of these categories.

        Args:
            tasks (list): The list of selected tasks.
            TaskFileClass (class): The class to use to create the new task file.

        Returns:
            TaskFile: The new task file created from the task selection.
        """
        selectionFile = TaskFileClass()
        # Add the selected tasks:
        selectionFile.tasks().extend(tasks)
        # Include categories used by the selected tasks:
        allCategories = set()
        for task in tasks:
            allCategories.update(task.categories())
        # Also include parents of used categories, recursively:
        for category in allCategories.copy():
            allCategories.update(category.ancestors())
        selectionFile.categories().extend(allCategories)
        return selectionFile

    def _saveSave(self, taskFile, showerror, filename=None):
        """Save the file and show an error message if saving fails."""
        try:
            if filename:
                taskFile.saveas(filename)
            else:
                filename = taskFile.filename()
                taskFile.save()
            self.__showSaveMessage(taskFile)
            self.__addRecentFile(filename)
            return True
        except lockfile.LockTimeout:
            errorMessage = _(
                "Cannot save %s\nIt is locked by another instance " "of %s.\n"
            ) % (filename, meta.name)
            showerror(errorMessage, **self.__errorMessageOptions)
            return False
        except (OSError, IOError, lockfile.LockFailed) as reason:
            errorMessage = _("Cannot save %s\n%s") % (
                filename,
                ExceptionAsUnicode(reason),
            )
            showerror(errorMessage, **self.__errorMessageOptions)
            return False

    def saveastemplate(self, task):
        """This method allows you to save a task as a template in the templates directory."""
        templates = persistence.TemplateList(
            self.__settings.pathToTemplatesDir()
        )
        templates.addTemplate(task)
        templates.save()

    def importTemplate(self, showerror=wx.MessageBox):
        """This function allows you to import a task template from a file.

        - The first line defines the function "importTemplate"
        with a parameter "showerror" which is a dialog function error.

        - The second line asks the user to select a file to import
        using the "__askUserForFile" function which is defined elsewhere in the code.

        - If the user selects a file, the third line
        creates an instance of the "TemplateList" class which is defined elsewhere in the code
        and which represents a list of task templates.

        - The fourth line tries to copy the selected task template
        to the task template directory using the "copyTemplate"
        method of the "TemplateList" class.

        - If an exception is thrown during copying, the fifth line
        creates an error message with the file name and the reason for the exception,
        then displays the error dialog box using the "showerror" function passed as a parameter.
        """
        filename = self.__askUserForFile(
            _("Import template"),
            fileDialogOpts={
                "default_extension": "tsktmpl",
                "wildcard": _("%s template files (*.tsktmpl)|" "*.tsktmpl")
                % meta.name,
            },
        )
        if filename:
            templates = persistence.TemplateList(
                self.__settings.pathToTemplatesDir()
            )
            try:
                templates.copyTemplate(filename)
            except Exception as reason:  # pylint: disable=W0703
                errorMessage = _("Cannot import template %s\n%s") % (
                    filename,
                    ExceptionAsUnicode(reason),
                )
                showerror(errorMessage, **self.__errorMessageOptions)

    def close(self, force=False):
        """This function allows you to close the task currently being edited.

        - The first line defines the "close" function with an optional parameter "force"
        which is a boolean indicating whether the closure must be forced
        without asking the user to save the current changes.

        - The second line checks if the task file currently being edited
        needs to be saved by calling the method "needSave" of the "taskFile" object
        which is defined elsewhere in the code.

        - If the file needs to be saved and the close must be forced,
        the third line saves the file without asking the user
        using the "_saveSave" method of the "taskFile"
        object and a lambda function which does nothing (it empties the arguments).

        - If the file needs to be saved but closing is not forced,
        the fifth line calls the "__saveUnsavedChanges" method which
        asks the user if they want to save the changes in course.
        If the user chooses not to save, the function returns "False"
        and the task is not closed.

        - If the file does not need be saved or
        if the user chose to save the changes,
        the seventh line calls the "__closeUnconditionally" method
        which closes the task unconditionally.

        - Finally, the last line returns " True" to indicate that
        the task was closed successfully.
        """
        if self.__taskFile.needSave():
            if force:
                # No user interaction, since we're forced to close right now.
                if self.__taskFile.filename():
                    self._saveSave(
                        self.__taskFile, lambda *args, **kwargs: None
                    )
                else:
                    pass  # No filename, we cannot ask, give up...
            else:
                if not self.__saveUnsavedChanges():
                    return False
        self.__closeUnconditionally()
        return True

    def export(
        self,
        title,
        fileDialogOpts,
        writerClass,
        viewer,
        selectionOnly,
        openfile=codecs.open,
        showerror=wx.MessageBox,
        filename=None,
        fileExists=os.path.exists,
        **kwargs
    ):
        """This function opens the file filename for writing and returns
        whether everything went well.

        Several optional parameters:
        Args:
            "title": which is the title of the dialog box backup,
            "fileDialogOpts": which are the options of the backup dialog box,
            "writerClass": which is the class that writes the exported data to the file,
            "viewer": which is the object which provides the data to export,
            "selectionOnly": which is a boolean indicating whether only
             the selected data must be exported,
            "openfile": which is the function used to open the file for writing,
            "showerror": which is the error dialog box function,
            "filename": which is the file name to use for export,
            "fileExists": which is the function used to check if the file already exists, and
            "**kwargs": which allows additional arguments to be passed to the write method.

        The second line uses the file name provided as a parameter
        or asks the user to select a file using the "__askUserForFile"
        method which is defined elsewhere in the code.

        If the user selects a file, the third line opens the file for writing
        using the "__openFileForWriting" method which is defined elsewhere in the code.
        If opening the file fails, the function returns "False".

        If the file is opened successfully, the fourth line uses the "writerClass"
        class to write the exported data to the file by calling the "write"
        method with the parameters "viewer", "self.__settings", "selectionOnly" and "**kwargs".
        The "write" method is defined in the "writerClass" class.

        The fifth line closes the file and displays a confirmation message
        using the "__messageCallback" method " which is defined elsewhere in the code.

        Finally, the last line

        Returns:
            bool: returns "True" if the export was successful and "False" otherwise.
        """
        filename = filename or self.__askUserForFile(
            title,
            fileDialogOpts,
            flag=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            fileExists=fileExists,
        )
        if filename:
            fd = self.__openFileForWriting(filename, openfile, showerror)
            if fd is None:
                return False
            count = writerClass(fd, filename).write(
                viewer, self.__settings, selectionOnly, **kwargs
            )
            fd.close()
            self.__messageCallback(
                _("Exported %(count)d items to " "%(filename)s")
                % dict(count=count, filename=filename)
            )
            return True
        else:
            return False

    def exportAsHTML(
        self,
        viewer,
        selectionOnly=False,
        separateCSS=False,
        columns=None,
        openfile=codecs.open,
        showerror=wx.MessageBox,
        filename=None,
        fileExists=os.path.exists,
    ):
        """Exports the data of the currently edited task in HTML format.

        The data is provided by the "viewer" object.

        If "selectionOnly" is True, only the selected data are exported.

        If "separateCSS" is True, the CSS is written to a separate file.

        "columns" is a list of column names to export.

        If "filename" is provided, the file is saved under that name.
        Otherwise, the user is prompted to select a file name.

        If the file already exists, the user is prompted to confirm overwriting.
        """
        return self.export(
            _("Export as HTML"),
            self.__htmlFileDialogOpts,
            persistence.HTMLWriter,
            viewer,
            selectionOnly,
            openfile,
            showerror,
            filename,
            fileExists,
            separateCSS=separateCSS,
            columns=columns,
        )

    def exportAsCSV(
        self,
        viewer,
        selectionOnly=False,
        separateDateAndTimeColumns=False,
        columns=None,
        fileExists=os.path.exists,
    ):
        """Exports the data of the currently edited task in CSV format.

        The data is provided by the "viewer" object.

        If "selectionOnly" is True, only the selected data are exported.

        If "separateDateAndTimeColumns" is True, dates and times are exported in separate columns.

        "columns" is a list of column names to export.

        If "fileExists" is provided, it is used to check if the file already exists.

        If "filename" is provided, the file is saved under that name.

        Otherwise, the The user is prompted to select a file name.

        If the file already exists, the user is prompted to confirm overwriting.
        """
        return self.export(
            _("Export as CSV"),
            self.__csvFileDialogOpts,
            persistence.CSVWriter,
            viewer,
            selectionOnly,
            separateDateAndTimeColumns=separateDateAndTimeColumns,
            columns=columns,
            fileExists=fileExists,
        )

    def exportAsICalendar(
        self, viewer, selectionOnly=False, fileExists=os.path.exists
    ):
        """Exports the data of the currently edited task in iCalendar format.

                The data is provided by the "viewer" object.

                If "selectionOnly" is True, only the selected data are exported.

                If "fileExists" is provided, it is used to check if the file already exists.

                If "filename" is provided, the file is saved under that name.
        )
                Otherwise, the user is prompted to select a file name.

                If the file already exists, the user is prompted to confirm overwriting.
        """
        return self.export(
            _("Export as iCalendar"),
            self.__icsFileDialogOpts,
            persistence.iCalendarWriter,
            viewer,
            selectionOnly,
            fileExists=fileExists,
        )

    def exportAsTodoTxt(
        self, viewer, selectionOnly=False, fileExists=os.path.exists
    ):
        """Exports the data of the currently edited task in Todo.txt format.

        The data is provided by the "viewer" object.

        If "selectionOnly" is True, only the selected data is exported.

        If "fileExists" is provided, it is used to check if the file already exists.

        If "filename" is provided, the file is saved under that name.

        Otherwise, the user is prompted to select a file name.

        If the file already exists, the user is prompted to confirm overwriting.
        """
        return self.export(
            _("Export as Todo.txt"),
            self.__todotxtFileDialogOpts,
            persistence.TodoTxtWriter,
            viewer,
            selectionOnly,
            fileExists=fileExists,
        )

    def importCSV(self, **kwargs):
        """Imports data in CSV format into the task being edited.

        Data is read from a CSV file using the "CSVReader" class of the "persistence" object.

        Tasks and categories are stored in the "self.__taskFile" object.

        Additional parameters can be passed to the "read" method of the "CSVReader" class.
        """
        persistence.CSVReader(
            self.__taskFile.tasks(), self.__taskFile.categories()
        ).read(**kwargs)

    def importTodoTxt(self, filename):
        """Imports data in Todo.txt format into the task being edited.

        Data is read from a Todo.txt
        file using the object's "TodoTxtReader" class "persistence".

        Tasks and categories are stored in the "self.__taskFile" object.

        The file name must be provided as a parameter.
        """
        persistence.TodoTxtReader(
            self.__taskFile.tasks(), self.__taskFile.categories()
        ).read(filename)

    def synchronize(self):
        """Synchronizes data from the currently editing task with a SyncML server.

         The user is prompted for a password for authentication.

        If authentication fails, the user can choose to reset the password.

        The synchronization information is stored
        in the "synchronizer" object of the "Synchronizer" class of the "sync" object.

        The synchronization results are displayed
        in the synchronization report dialog box "self.__syncReport".

        If the synchronization is successful, a confirmation message is displayed.

        If the synchronization fails, an "AuthenticationFailure" exception is thrown and
        the user can choose to retry or cancel.
        """
        doReset = False
        while True:
            password = GetPassword("Task Coach", "SyncML", reset=doReset)
            if not password:
                break

            synchronizer = sync.Synchronizer(
                self.__syncReport, self.__taskFile, password
            )
            try:
                synchronizer.synchronize()
            except sync.AuthenticationFailure:
                doReset = True
            else:
                self.__messageCallback(_("Finished synchronization"))
                break
            finally:
                synchronizer.Destroy()

    def filename(self):
        """Returns the file name of the task currently being edited.

        The file name is stored in the "self.__taskFile" object.
        """
        return self.__taskFile.filename()

    def __syncReport(self, msg):
        """Displays an error message in a synchronization report dialog box.

         The message is provided as parameter "msg".

        The dialog box is created with the title "Synchronization status "
        and style "wx.OK | wx.ICON_ERROR".
        """
        wx.MessageBox(
            msg, _("Synchronization status"), style=wx.OK | wx.ICON_ERROR
        )

    def __openFileForWriting(
        self, filename, openfile, showerror, mode="w", encoding="utf-8"
    ):
        """Opens a file for writing with filename "filename" using the "openfile" function.

        Open mode is "mode" and encoding is "encoding".

        ) If opening the file fails, an error message is created with
        the file name and the reason for the exception, then displayed in an error dialog box
        using the function " showerror".

        The error dialog box options are stored in the "self.__errorMessageOptions" object.

        If the file opening is successful, the open file is returned .

        If opening the file fails, the function returns "None".
        """
        try:
            return openfile(filename, mode, encoding)
        except IOError as reason:
            errorMessage = _("Cannot open %s\n%s") % (
                filename,
                ExceptionAsUnicode(reason),
            )
            showerror(errorMessage, **self.__errorMessageOptions)
            return None

    def __addRecentFile(self, fileName):
        """Adds the file name "fileName" to the list of recent files.

        The list of recent files is stored in the settings of the "self.__settings" object.

        If the file is already in the list, it is moved to the top of the list.

        The list is then truncated so as not to exceed
        the maximum number of recent files defined in the "maxrecentfiles" parameters.

        Recent files are stored in the "file" section of the settings
        of the "self.__settings" object under the "recentfiles" key.
        """
        recentFiles = self.__settings.getlist("file", "recentfiles")
        if fileName in recentFiles:
            recentFiles.remove(fileName)
        recentFiles.insert(0, fileName)
        maximumNumberOfRecentFiles = self.__settings.getint(
            "file", "maxrecentfiles"
        )
        recentFiles = recentFiles[:maximumNumberOfRecentFiles]
        self.__settings.setlist("file", "recentfiles", recentFiles)

    def __removeRecentFile(self, fileName):
        """Removes the file name "fileName" from the recent file list.

         The recent file list is stored in the settings of the "self.__settings" object.

        If the file is in the list, it is removed from the list.

        Recent files are stored in the "file" section of the settings
        of the "self.__settings" object under the "recentfiles" key.
        """
        recentFiles = self.__settings.getlist("file", "recentfiles")
        if fileName in recentFiles:
            recentFiles.remove(fileName)
            self.__settings.setlist("file", "recentfiles", recentFiles)

    def __askUserForFile(
        self, title, fileDialogOpts, flag=wx.FD_OPEN, fileExists=os.path.exists
    ):
        """Opens a file selection dialog box to ask the user to select a file.

        The title of the dialog box is "title".

        The box options dialog box are provided in the "fileDialogOpts" dictionary.

        The "flag" flag indicates whether the dialog box should be used to open or save a file.

        The "fileExists" function is used to check if the file already exists.

        If the file selected for saving does not have the default extension,
        the extension is added automatically.

        If the file already exists, the user is prompted to confirm the overwrite
        by calling the "__askUserForOverwriteConfirmation" method.

        If the user confirms the overwrite, the file name is returned.

        Otherwise, the function returns "None".
        """
        filename = wx.FileSelector(
            title, flags=flag, **fileDialogOpts
        )  # pylint: disable=W0142
        if filename and (flag & wx.FD_SAVE):
            # On Ubuntu, the default extension is not added automatically to
            # a filename typed by the user. Add the extension if necessary.
            extension = os.path.extsep + fileDialogOpts["default_extension"]
            if not filename.endswith(extension):
                filename += extension
                if fileExists(filename):
                    return self.__askUserForOverwriteConfirmation(
                        filename, title, fileDialogOpts
                    )
        return filename

    def __askUserForOverwriteConfirmation(
        self, filename, title, fileDialogOpts
    ):
        """Displays a confirmation dialog box to ask the user
        if they want to overwrite the existing file "filename".

        The title of the dialog box is "title".

        The dialog box options are provided in the dictionary "fileDialogOpts".

        If the user confirms overwriting, the function returns the file name "filename".

        If the user does not want to overwrite the file,
        the function calls the "__askUserForFile" method to
        ask the user to select another file name.

        If the user cancels , the function returns "None".

        If the file to be overwritten is used for automatic import or export,
        the corresponding files are deleted if they exist.
        """
        result = wx.MessageBox(
            _("A file named %s already exists.\n" "Do you want to replace it?")
            % filename,
            title,
            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.NO_DEFAULT,
        )
        if result == wx.YES:
            extensions = {"Todo.txt": ".txt"}
            for auto in set(
                self.__settings.getlist("file", "autoimport")
                + self.__settings.getlist("file", "autoexport")
            ):
                autoName = os.path.splitext(filename)[0] + extensions[auto]
                if os.path.exists(autoName):
                    os.remove(autoName)
                if os.path.exists(autoName + "-meta"):
                    os.remove(autoName + "-meta")
            return filename
        elif result == wx.NO:
            return self.__askUserForFile(
                title, fileDialogOpts, flag=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
        else:
            return None

    def __saveUnsavedChanges(self):
        """Asks the user if they want to save the current changes
        before closing the currently editing task.

        If unsaved changes are detected,
        a dialog box confirmation is displayed with
        the message "You have unsaved changes. Save before closing?".

        If the user chooses to save the changes,
        the function calls the "save" method.

        If the save fails, the function returns "False".

        If the user cancels, the function returns "False".

        If the user chooses to close without save or if the save succeeds, the function returns "True".
        """
        result = wx.MessageBox(
            _("You have unsaved changes.\n" "Save before closing?"),
            _("%s: save changes?") % meta.name,
            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.YES_DEFAULT,
        )
        if result == wx.YES:
            if not self.save():
                return False
        elif result == wx.CANCEL:
            return False
        return True

    def __askBreakLock(self, filename):
        """Asks the user if they want to break the lock on the file "filename".

        If the file is locked, a confirmation dialog box is displayed.

        If the user chooses to break the lock, the function returns "True".

        Otherwise, the function returns "False".
        """
        result = wx.MessageBox(
            _(
                """Cannot open %s because it is locked.

This means either that another instance of TaskCoach
is running and has this file opened, or that a previous
instance of Task Coach crashed. If no other instance is
running, you can safely break the lock.

Break the lock?"""
            )
            % filename,
            _("%s: file locked") % meta.name,
            style=wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
        )
        return result == wx.YES

    def __askOpenUnlocked(self, filename):
        """Asks the user if they want to open the file "filename" without locking.

        If locking is not supported for the file location,
        a confirmation dialog box is displayed.

        If the user chooses to open the file without locking, the function returns "True".

        Otherwise, the function returns "False".
        """
        result = wx.MessageBox(
            _(
                "Cannot acquire a lock because locking is not "
                "supported\non the location of %s.\n"
                "Open %s unlocked?"
            )
            % (filename, filename),
            _("%s: file locked") % meta.name,
            style=wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
        )
        return result == wx.YES

    def __closeUnconditionally(self):
        """Closes the currently edited task unconditionally.

        A confirmation message is displayed with the file name of the currently edited task.

        The "self.__taskFile" object " is closed.

        The command history is cleared.

        The memory is cleaned with the "gc.collect()" function.
        """
        self.__messageCallback(_("Closed %s") % self.__taskFile.filename())
        self.__taskFile.close()
        patterns.CommandHistory().clear()
        gc.collect()

    def __showSaveMessage(self, savedFile):
        """Displays a confirmation message to indicate that the job being edited has been saved successfully.

        The message contains the number of jobs being saved and the file name of the job being edited.

        The message is displayed by calling the "__messageCallback" method.
        """
        self.__messageCallback(
            _("Saved %(nrtasks)d tasks to %(filename)s")
            % {
                "nrtasks": len(savedFile.tasks()),
                "filename": savedFile.filename(),
            }
        )

    def __showTooNewErrorMessage(self, filename, showerror):
        """Displays an error message to indicate that the file "filename" was created
        by a newer version of the application.

        The error message is displayed using the "showerror" function passed as a parameter.

        The options for the error dialog box are stored in the "self.__errorMessageOptions" object.

        The application name is obtained from the 'meta' object.
        """
        showerror(
            _(
                "Cannot open %(filename)s\n"
                "because it was created by a newer version of %(name)s.\n"
                "Please upgrade %(name)s."
            )
            % dict(filename=filename, name=meta.name),
            **self.__errorMessageOptions
        )

    def __showGenericErrorMessage(
        self, filename, showerror, showBackups=False
    ):
        """Displays a generic error message for reading a given file.

        :param filename: The name of the file that caused the error
        :type filename: str
        :param showerror : the function to use to display the error
        : type showerror: function
        : param showBackups: indicates whether the backup manager must be opened to allow the restoration of an earlier version of the file
        : type showBackups: bool
        """
        sys.stderr.write("".join(traceback.format_exception(*sys.exc_info())))
        limitedException = "".join(
            traceback.format_exception(*sys.exc_info(), limit=10)
        )
        message = _("Error while reading %s:\n") % filename + limitedException
        man = persistence.BackupManifest(self.__settings)
        if showBackups and man.hasBackups(filename):
            message += "\n" + _(
                "The backup manager will now open to allow you to restore\nan older version of this file."
            )
        showerror(message, **self.__errorMessageOptions)

        if showBackups and man.hasBackups(filename):
            dlg = BackupManagerDialog(None, self.__settings, filename)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    wx.CallAfter(self.open, dlg.restoredFilename())
            finally:
                dlg.Destroy()

    def __updateDefaultPath(self, filename):
        """Updates default paths.

        For each option in ..., sets the default path option for the .tsk file to open.
        """
        for options in [
            self.__tskFileOpenDialogOpts,
            self.__tskFileSaveDialogOpts,
            self.__csvFileDialogOpts,
            self.__icsFileDialogOpts,
            self.__htmlFileDialogOpts,
        ]:
            options["default_path"] = os.path.dirname(filename)
