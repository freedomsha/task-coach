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

from taskcoachlib import meta, patterns, operating_system
from taskcoachlib.i18n import _
from pubsub import pub
from taskcoachlib.workarounds import ExceptionAsUnicode
import configparser
import os
import sys
import wx
import shutil
from . import defaults


class UnicodeAwareConfigParser(configparser.RawConfigParser):
    """
    A custom ConfigParser that handles Unicode strings.

    This class inherits from RawConfigParser and provides Unicode-aware methods for setting and getting configuration values.
    """

    def set(self, section, setting, value):  # pylint: disable=W0222
        """
        Set a configuration value in the specified section.

        Args:
            section (str): The section name.
            setting (str): The setting name.
            value: The value to set.
        """
        configparser.RawConfigParser.set(self, section, setting, value)

    def get(self, section, setting):  # pylint: disable=W0221
        """
        Get a configuration value from the specified section.

        Args:
            section (str): The section name.
            setting (str): The setting name.

        Returns:
            The configuration value.
        """
        return configparser.RawConfigParser.get(self, section, setting)


class CachingConfigParser(UnicodeAwareConfigParser):
    """
    A custom ConfigParser that caches configuration values for improved performance.

    ConfigParser is rather slow, so cache its values.

    This class inherits from UnicodeAwareConfigParser and adds caching
    functionality to avoid redundant lookups.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the CachingConfigParser.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.__cachedValues = dict()
        UnicodeAwareConfigParser.__init__(self, *args, **kwargs)

    def read(self, *args, **kwargs):
        """
        Read configuration data from files.

        Args:
            *args: File paths to read.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if successful, False otherwise.
        """
        self.__cachedValues = dict()
        return UnicodeAwareConfigParser.read(self, *args, **kwargs)

    def set(self, section, setting, value):
        """
        Set a configuration value and cache it.

        Args:
            section (str): The section name.
            setting (str): The setting name.
            value: The value to set.
        """
        self.__cachedValues[(section, setting)] = value
        UnicodeAwareConfigParser.set(self, section, setting, value)

    def get(self, section, setting):
        """
        Get a configuration value from cache or read it if not cached.

        Args:
            section (str): The section name.
            setting (str): The setting name.

        Returns:
            The configuration value.
        """
        cache, key = self.__cachedValues, (section, setting)
        if key not in cache:
            cache[key] = UnicodeAwareConfigParser.get(
                self, *key
            )  # pylint: disable=W0142
        return cache[key]


class Settings(CachingConfigParser):
    """
    A class to manage application settings, inheriting from CachingConfigParser.

    This class manages the reading, writing, and caching of application settings,
    including handling default values and migrating configuration files.
    """

    def __init__(self, load=True, iniFile=None, *args, **kwargs):
        """
        Initialize the Settings object.

        Args:
            load (bool, optional): Whether to load the settings from file. Defaults to True.
            iniFile (str, optional): The path to the .ini file. Defaults to None.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        # Sigh, ConfigParser.SafeConfigParser is an old-style class, so we
        # have to call the superclass __init__ explicitly:
        CachingConfigParser.__init__(self, *args, **kwargs)

        self.initializeWithDefaults()
        self.__loadAndSave = load
        self.__iniFileSpecifiedOnCommandLine = iniFile
        self.migrateConfigurationFiles()
        if load:
            # First, try to load the settings file from the program directory,
            # if that fails, load the settings file from the settings directory
            try:
                if not self.read(self.filename(forceProgramDir=True)):
                    self.read(self.filename())
                errorMessage = ""
            except configparser.ParsingError as errorMessage:
                # Ignore exceptions and simply use default values.
                # Also record the failure in the settings:
                self.initializeWithDefaults()
            self.setLoadStatus(ExceptionAsUnicode(errorMessage))
        else:
            # Assume that if the settings are not to be loaded, we also
            # should be quiet (i.e. we are probably in test mode):
            self.__beQuiet()
        pub.subscribe(
            self.onSettingsFileLocationChanged,
            "settings.file.saveinifileinprogramdir",
        )

    def onSettingsFileLocationChanged(self, value):
        """
        Handle changes to the settings file location.

        Args:
            value (bool): Whether to save the .ini file in the program directory.
        """
        saveIniFileInProgramDir = value
        if not saveIniFileInProgramDir:
            try:
                os.remove(self.generatedIniFilename(forceProgramDir=True))
            except:
                return  # pylint: disable=W0702

    def initializeWithDefaults(self):
        """
        Initialize settings with default values.
        """
        for section in self.sections():
            self.remove_section(section)
        for section, settings in list(defaults.defaults.items()):
            self.add_section(section)
            for key, value in list(settings.items()):
                # Don't notify observers while we are initializing
                super(Settings, self).set(section, key, value)

    def setLoadStatus(self, message):
        """
        Set the load status of the settings file.

        Args:
            message (str): The error message if loading failed.
        """
        self.set("file", "inifileloaded", "False" if message else "True")
        self.set("file", "inifileloaderror", message)

    def __beQuiet(self):
        """
        Disable noisy settings for quiet mode (e.g., during testing).
        """
        noisySettings = [
            ("window", "splash", "False"),
            ("window", "tips", "False"),
            ("window", "starticonized", "Always"),
        ]
        for section, setting, value in noisySettings:
            self.set(section, setting, value)

    def add_section(
        self, section, copyFromSection=None
    ):  # pylint: disable=W0221
        """
        Add a new section to the settings.

        Args:
            section (str): The section name.
            copyFromSection (str, optional): The section to copy values from. Defaults to None.

        Returns:
            bool: True if the section was added successfully.
        """
        result = super(Settings, self).add_section(section)
        if copyFromSection:
            for name, value in self.items(copyFromSection):
                super(Settings, self).set(section, name, value)
        return result

    def getRawValue(self, section, option):
        """
        Get a raw (unevaluated) value from the settings.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            str: The raw value.
        """
        return super(Settings, self).get(section, option)

    def init(self, section, option, value):
        """
        Initialize a setting with a given value.

        Args:
            section (str): The section name.
            option (str): The option name.
            value: The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        return super(Settings, self).set(section, option, value)

    def get(self, section, option):
        """
        Get a value from the settings, handling defaults and old .ini file formats.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            The value of the setting.
        """
        try:
            result = super(Settings, self).get(section, option)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return self.getDefault(section, option)
        result = self._fixValuesFromOldIniFiles(section, option, result)
        result = self._ensureMinimum(section, option, result)
        return result

    def getDefault(self, section, option):
        """
        Get the default value for a given setting.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            The default value.
        """
        defaultSectionKey = section.strip("0123456789")
        try:
            defaultSection = defaults.defaults[defaultSectionKey]
        except KeyError:
            raise configparser.NoSectionError(defaultSectionKey)
        try:
            return defaultSection[option]
        except KeyError:
            raise configparser.NoOptionError((option, defaultSection))

    def _ensureMinimum(self, section, option, result):
        """
        Ensure that a setting value meets the minimum requirements.

        Args:
            section (str): The section name.
            option (str): The option name.
            result: The value to check.

        Returns:
            The value, ensuring it meets the minimum requirements.
        """
        if section in defaults.minimum and option in defaults.minimum[section]:
            result = max(result, defaults.minimum[section][option])
        return result

    def _fixValuesFromOldIniFiles(self, section, option, result):
        """
        Fix settings from old TaskCoach.ini files that are no longer valid.

        Args:
            section (str): The section name.
            option (str): The option name.
            result: The value to fix.

        Returns:
            The fixed value.
        """
        original = result
        # Starting with release 1.1.0, the date properties of tasks (startDate,
        # dueDate and completionDate) are datetimes:
        taskDateColumns = ("startDate", "dueDate", "completionDate")
        orderingViewers = [
            "taskviewer",
            "categoryviewer",
            "noteviewer",
            "noteviewerintaskeditor",
            "noteviewerincategoryeditor",
            "noteviewerinattachmenteditor",
            "categoryviewerintaskeditor",
            "categoryviewerinnoteeditor",
        ]
        if option == "sortby":
            if result in taskDateColumns:
                result += "Time"
            try:
                eval(result)
            except:
                sortKeys = [result]
                try:
                    ascending = self.getboolean(section, "sortascending")
                except:
                    ascending = True
                result = '["%s%s"]' % (("" if ascending else "-"), result)
        elif option == "columns":
            columns = [
                (col + "Time" if col in taskDateColumns else col)
                for col in eval(result)
            ]
            result = str(columns)
        elif option == "columnwidths":
            widths = dict()
            try:
                columnWidthMap = eval(result)
            except SyntaxError:
                columnWidthMap = dict()
            for column, width in list(columnWidthMap.items()):
                if column in taskDateColumns:
                    column += "Time"
                widths[column] = width
            if section in orderingViewers and "ordering" not in widths:
                widths["ordering"] = 28
            result = str(widths)
        elif (
            section == "feature"
            and option == "notifier"
            and result == "Native"
        ):
            result = "Task Coach"
        elif section == "editor" and option == "preferencespages":
            result = result.replace("colors", "appearance")
        elif section in orderingViewers and option == "columnsalwaysvisible":
            try:
                columns = eval(result)
            except SyntaxError:
                columns = ["ordering"]
            else:
                if "ordering" in columns:
                    columns.remove("ordering")
            result = str(columns)
        if result != original:
            super(Settings, self).set(section, option, result)
        return result

    def set(self, section, option, value, new=False):  # pylint: disable=W0221
        """
        Set a value in the settings.

        Args:
            section (str): The section name.
            option (str): The option name.
            value: The value to set.
            new (bool, optional): Whether this is a new option. Defaults to False.

        Returns:
            bool: True if the value was set successfully.
        """
        if new:
            currentValue = (
                "a new option, so use something as current value"
                " that is unlikely to be equal to the new value"
            )
        else:
            currentValue = self.get(section, option)
        if value != currentValue:
            super(Settings, self).set(section, option, value)
            patterns.Event("%s.%s" % (section, option), self, value).send()
            return True
        else:
            return False

    def setboolean(self, section, option, value):
        """
        Set a boolean value in the settings.

        Args:
            section (str): The section name.
            option (str): The option name.
            value (bool): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        if self.set(section, option, str(value)):
            pub.sendMessage("settings.%s.%s" % (section, option), value=value)

    setvalue = settuple = setlist = setdict = setint = setboolean

    def settext(self, section, option, value):
        """
        Set a text value in the settings.

        Args:
            section (str): The section name.
            option (str): The option name.
            value (str): The value to set.

        Returns:
            bool: True if the value was set successfully.
        """
        if self.set(section, option, value):
            pub.sendMessage("settings.%s.%s" % (section, option), value=value)

    def getlist(self, section, option):
        """
        Get a list value from the settings.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            list: The list value.
        """
        return self.getEvaluatedValue(section, option, eval)

    getvalue = gettuple = getdict = getlist

    def getint(self, section, option):
        """
        Get an integer value from the settings.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            int: The integer value.
        """
        return self.getEvaluatedValue(section, option, int)

    def getboolean(self, section, option):
        """
        Get a boolean value from the settings.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            bool: The boolean value.
        """
        return self.getEvaluatedValue(section, option, self.evalBoolean)

    def gettext(self, section, option):
        """
        Get a text value from the settings.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            str: The text value.
        """
        return self.get(section, option)

    @staticmethod
    def evalBoolean(stringValue):
        """
        Evaluate a string as a boolean value.

        Args:
            stringValue (str): The string value.

        Returns:
            bool: The evaluated boolean value.

        Raises:
            ValueError: If the string is not a valid boolean value.
        """
        if stringValue in ("True", "False"):
            return "True" == stringValue
        else:
            raise ValueError(
                "invalid literal for Boolean value: '%s'" % stringValue
            )

    def getEvaluatedValue(
        self, section, option, evaluate=eval, showerror=wx.MessageBox
    ):
        """
        Get a value from the settings and evaluate it.

        Args:
            section (str): The section name.
            option (str): The option name.
            evaluate (function, optional): The function to evaluate the value. Defaults to eval.
            showerror (function, optional): The function to show errors. Defaults to wx.MessageBox.

        Returns:
            The evaluated value.
        """
        stringValue = self.get(section, option)
        try:
            return evaluate(stringValue)
        except Exception as exceptionMessage:  # pylint: disable=W0703
            message = "\n".join(
                [
                    _("Error while reading the %s-%s setting from %s.ini.")
                    % (section, option, meta.filename),
                    _("The value is: %s") % stringValue,
                    _("The error is: %s") % exceptionMessage,
                    _(
                        "%s will use the default value for the setting and should proceed normally."
                    )
                    % meta.name,
                ]
            )
            showerror(
                message, caption=_("Settings error"), style=wx.ICON_ERROR
            )
            defaultValue = self.getDefault(section, option)
            self.set(
                section, option, defaultValue, new=True
            )  # Ignore current value
            return evaluate(defaultValue)

    def save(
        self, showerror=wx.MessageBox, file=open
    ):  # pylint: disable=W0622
        """
        Save the settings to a file.

        Args:
            showerror (function, optional): The function to show errors. Defaults to wx.MessageBox.
            file (function, optional): The function to open files. Defaults to open.
        """
        self.set("version", "python", sys.version)
        self.set(
            "version",
            "wxpython",
            "%s-%s @ %s"
            % (wx.VERSION_STRING, wx.PlatformInfo[2], wx.PlatformInfo[1]),
        )
        self.set("version", "pythonfrozen", str(hasattr(sys, "frozen")))
        self.set("version", "current", meta.data.version)
        if not self.__loadAndSave:
            return
        try:
            path = self.path()
            if not os.path.exists(path):
                os.mkdir(path)
            tmpFile = open(self.filename() + ".tmp", "w")
            self.write(tmpFile)
            tmpFile.close()
            if os.path.exists(self.filename()):
                os.remove(self.filename())
            os.rename(self.filename() + ".tmp", self.filename())
        except Exception as message:  # pylint: disable=W0703
            showerror(
                _("Error while saving %s.ini:\n%s\n")
                % (meta.filename, message),
                caption=_("Save error"),
                style=wx.ICON_ERROR,
            )

    def filename(self, forceProgramDir=False):
        """
        Get the filename of the .ini file.

        Args:
            forceProgramDir (bool, optional): Whether to force saving in the program directory. Defaults to False.

        Returns:
            str: The filename of the .ini file.
        """
        if self.__iniFileSpecifiedOnCommandLine:
            return self.__iniFileSpecifiedOnCommandLine
        else:
            return self.generatedIniFilename(forceProgramDir)

    def path(
        self, forceProgramDir=False, environ=os.environ
    ):  # pylint: disable=W0102
        """
        Get the path to the configuration directory.

        Args:
            forceProgramDir (bool, optional): Whether to force saving in the program directory. Defaults to False.
            environ (dict, optional): The environment variables. Defaults to os.environ.

        Returns:
            str: The path to the configuration directory.
        """
        if self.__iniFileSpecifiedOnCommandLine:
            return self.pathToIniFileSpecifiedOnCommandLine()
        elif forceProgramDir or self.getboolean(
            "file", "saveinifileinprogramdir"
        ):
            return self.pathToProgramDir()
        else:
            return self.pathToConfigDir(environ)

    @staticmethod
    def pathToDocumentsDir():
        """
        Get the path to the documents directory.

        Returns:
            str: The path to the documents directory.
        """
        if operating_system.isWindows():
            from win32com.shell import shell, shellcon

            try:
                return shell.SHGetSpecialFolderPath(
                    None, shellcon.CSIDL_PERSONAL
                )
            except:
                # Yes, one of the documented ways to get this sometimes fail with "Unspecified error". Not sure
                # this will work either.
                # Update: There are cases when it doesn't work either; see support request #410...
                try:
                    return shell.SHGetFolderPath(
                        None, shellcon.CSIDL_PERSONAL, None, 0
                    )  # SHGFP_TYPE_CURRENT not in shellcon
                except:
                    return os.getcwd()
        elif operating_system.isMac():
            import Carbon.Folder, Carbon.Folders, Carbon.File

            pathRef = Carbon.Folder.FSFindFolder(
                Carbon.Folders.kUserDomain,
                Carbon.Folders.kDocumentsFolderType,
                True,
            )
            return Carbon.File.pathname(pathRef)
        elif operating_system.isGTK():
            try:
                from PyKDE4.kdeui import KGlobalSettings
            except ImportError:
                pass
            else:
                return str(KGlobalSettings.documentPath())
        return os.path.expanduser("~")

    def pathToProgramDir(self):
        """
        Get the path to the program directory.

        Returns:
            str: The path to the program directory.
        """
        path = sys.argv[0]
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return path

    def pathToConfigDir(self, environ):
        """
        Get the path to the configuration directory.

        Args:
            environ (dict): The environment variables.

        Returns:
            str: The path to the configuration directory.
        """
        try:
            if operating_system.isGTK():
                from xdg import BaseDirectory

                path = BaseDirectory.save_config_path(meta.name)
            elif operating_system.isMac():
                import Carbon.Folder, Carbon.Folders, Carbon.File

                pathRef = Carbon.Folder.FSFindFolder(
                    Carbon.Folders.kUserDomain,
                    Carbon.Folders.kPreferencesFolderType,
                    True,
                )
                path = Carbon.File.pathname(pathRef)
                # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
            elif operating_system.isWindows():
                from win32com.shell import shell, shellcon

                path = os.path.join(
                    shell.SHGetSpecialFolderPath(
                        None, shellcon.CSIDL_APPDATA, True
                    ),
                    meta.name,
                )
            else:
                path = self.pathToConfigDir_deprecated(environ=environ)
        except:  # Fallback to old dir
            path = self.pathToConfigDir_deprecated(environ=environ)
        return path

    def _pathToDataDir(self, *args, **kwargs):
        """
        Get the path to the data directory.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The path to the data directory.
        """
        forceGlobal = kwargs.pop("forceGlobal", False)
        if operating_system.isGTK():
            from xdg import BaseDirectory

            path = BaseDirectory.save_data_path(meta.name)
        elif operating_system.isMac():
            import Carbon.Folder, Carbon.Folders, Carbon.File

            pathRef = Carbon.Folder.FSFindFolder(
                Carbon.Folders.kUserDomain,
                Carbon.Folders.kApplicationSupportFolderType,
                True,
            )
            path = Carbon.File.pathname(pathRef)
            # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
            path = os.path.join(path, meta.name)
        elif operating_system.isWindows():
            if self.__iniFileSpecifiedOnCommandLine and not forceGlobal:
                path = self.pathToIniFileSpecifiedOnCommandLine()
            else:
                from win32com.shell import shell, shellcon

                path = os.path.join(
                    shell.SHGetSpecialFolderPath(
                        None, shellcon.CSIDL_APPDATA, True
                    ),
                    meta.name,
                )
        else:  # Errr...
            path = self.path()

        if operating_system.isWindows():
            # Follow shortcuts.
            from win32com.client import Dispatch

            shell = Dispatch("WScript.Shell")
            for component in args:
                path = os.path.join(path, component)
                if os.path.exists(path + ".lnk"):
                    shortcut = shell.CreateShortcut(path + ".lnk")
                    path = shortcut.TargetPath
        else:
            path = os.path.join(path, *args)

        exists = os.path.exists(path)
        if not exists:
            os.makedirs(path)
        return path, exists

    def pathToDataDir(self, *args, **kwargs):
        """
        Get the path to the data directory.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            str: The path to the data directory.
        """
        return self._pathToDataDir(*args, **kwargs)[0]

    def _pathToTemplatesDir(self):
        """
        Get the path to the templates directory.

        Returns:
            str: The path to the templates directory.
        """
        try:
            return self._pathToDataDir("templates")
        except:
            pass  # Fallback on old path
        return self.pathToTemplatesDir_deprecated(), True

    def pathToTemplatesDir(self):
        """
        Get the path to the templates directory.

        Returns:
            str: The path to the templates directory.
        """
        return self._pathToTemplatesDir()[0]

    def pathToBackupsDir(self):
        """
        Get the path to the backups directory.

        Returns:
            str: The path to the backups directory.
        """
        return self._pathToDataDir("backups")[0]

    def pathToConfigDir_deprecated(self, environ):
        """
        Get the deprecated path to the configuration directory.

        Args:
            environ (dict): The environment variables.

        Returns:
            str: The deprecated path to the configuration directory.
        """
        try:
            path = os.path.join(environ["APPDATA"], meta.filename)
        except Exception:
            path = os.path.expanduser("~")  # pylint: disable=W0702
            if path == "~":
                # path not expanded: apparently, there is no home dir
                path = os.getcwd()
            path = os.path.join(path, ".%s" % meta.filename)
        return operating_system.decodeSystemString(path)

    def pathToTemplatesDir_deprecated(self, doCreate=True):
        """
        Get the deprecated path to the templates directory.

        Args:
            doCreate (bool, optional): Whether to create the directory if it doesn't exist. Defaults to True.

        Returns:
            str: The deprecated path to the templates directory.
        """
        path = os.path.join(self.path(), "taskcoach-templates")

        if operating_system.isWindows():
            # Under Windows, check for a shortcut and follow it if it
            # exists.

            if os.path.exists(path + ".lnk"):
                from win32com.client import Dispatch  # pylint: disable=F0401

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(path + ".lnk")
                return shortcut.TargetPath

        if doCreate:
            try:
                os.makedirs(path)
            except OSError:
                pass
        return operating_system.decodeSystemString(path)

    def pathToIniFileSpecifiedOnCommandLine(self):
        """
        Get the path to the .ini file specified on the command line.

        Returns:
            str: The path to the .ini file specified on the command line.
        """
        return os.path.dirname(self.__iniFileSpecifiedOnCommandLine) or "."

    def generatedIniFilename(self, forceProgramDir):
        """
        Generate the filename of the .ini file.

        Args:
            forceProgramDir (bool): Whether to force saving in the program directory.

        Returns:
            str: The generated filename of the .ini file.
        """
        return os.path.join(
            self.path(forceProgramDir), "%s.ini" % meta.filename
        )

    def migrateConfigurationFiles(self):
        """
        Migrate configuration files to new locations if necessary.
        """
        # Templates. Extra care for Windows shortcut.
        oldPath = self.pathToTemplatesDir_deprecated(doCreate=False)
        newPath, exists = self._pathToTemplatesDir()
        if self.__iniFileSpecifiedOnCommandLine:
            globalPath = os.path.join(
                self.pathToDataDir(forceGlobal=True), "templates"
            )
            if os.path.exists(globalPath) and not os.path.exists(oldPath):
                # Upgrade from fresh installation of 1.3.24 Portable
                oldPath = globalPath
                if exists and not os.path.exists(newPath + "-old"):
                    # WTF?
                    os.rename(newPath, newPath + "-old")
                exists = False
        if exists:
            return
        if oldPath != newPath:
            if operating_system.isWindows() and os.path.exists(
                oldPath + ".lnk"
            ):
                shutil.move(oldPath + ".lnk", newPath + ".lnk")
            elif os.path.exists(oldPath):
                # pathToTemplatesDir() has created the directory
                try:
                    os.rmdir(newPath)
                except:
                    pass
                shutil.move(oldPath, newPath)
        # Ini file
        oldPath = os.path.join(
            self.pathToConfigDir_deprecated(environ=os.environ),
            "%s.ini" % meta.filename,
        )
        newPath = os.path.join(
            self.pathToConfigDir(environ=os.environ), "%s.ini" % meta.filename
        )
        if newPath != oldPath and os.path.exists(oldPath):
            shutil.move(oldPath, newPath)
        # Cleanup
        try:
            os.rmdir(self.pathToConfigDir_deprecated(environ=os.environ))
        except:
            pass

    def __hash__(self) -> int:
        """
        Get the hash of the Settings object.

        Returns:
            int: The hash of the Settings object.
        """
        return id(self)
