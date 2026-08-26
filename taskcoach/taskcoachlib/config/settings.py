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

import ast
import configparser
import logging
import os
import sys

from taskcoachlib.config.arguments import get_gui

gui_name = get_gui()
if gui_name == "wx":
    import wx
elif gui_name == "tk":
    import tkinter as tk
from tkinter import messagebox

import shutil

# from taskcoachlib.thirdparty.pubsub import pub
# https://pypubsub.readthedocs.io/en/v4.0.3/
from pubsub import pub
from typing import Dict, Any
from taskcoachlib import meta, patterns, operating_system
from taskcoachlib.i18n import _

# from taskcoachlib.workarounds import ExceptionAsUnicode  # unused import
from . import defaults

# from ..application import Application
# from taskcoachlib.application.application import Application
# ImportError: cannot import name 'Application' from partially initialized module
# 'taskcoachlib.application' (most likely due to a circular import)
# (/home/sylvain/Téléchargements/src/task-coach-git/taskcoach/taskcoachlib/application/__init__.py)

log = logging.getLogger(__name__)


# class UnicodeAwareConfigParser(configparser.RawConfigParser):
class UnicodeAwareConfigParser(configparser.ConfigParser):
    # class UnicodeAwareConfigParser(configparser.ConfigParser(interpolation=None)):
    """
    Un ConfigParser personnalisé qui gère les chaînes Unicode.

    Cette classe hérite de RawConfigParser et fournit des méthodes
    compatibles Unicode pour définir et obtenir des valeurs de configuration.
    """

    # Note
    #
    # Pensez plutôt à utiliser ConfigParser qui vérifie les types de valeurs à stocker en interne.
    # Si vous ne souhaitez pas d'interpolation, vous pouvez utiliser ConfigParser(interpolation=None).
    def __init__(self, *args, **kwargs):
        if "interpolation" not in kwargs:
            kwargs["interpolation"] = None
        super().__init__(*args, **kwargs)

    def set(self, section, setting, value=None):  # pylint: disable=W0222
        # def set(self, section: str, setting: str, value: str | None = None):  # pylint: disable=W0222
        """
        Définissez une valeur de configuration dans la section spécifiée.

        Args :
            section (str) : le nom de la section.
            setting (str) : le nom du paramètre.
            value : la valeur à définir.
        """
        configparser.RawConfigParser.set(self, section, setting, value)

    def get(
        self, section, setting, *, raw=False, vars=None
    ):  # pylint: disable=W0221
        # def get(self, section: str, setting: str, *, raw: bool = False, vars=None) -> str:  # pylint: disable=W0221
        """
        Obtenez une valeur de configuration à partir de la section spécifiée.

        Obtenez une valeur d'option pour une section donnée.
        Si `vars` est fourni, il doit s'agir d'un dictionnaire.
        L'option est recherchée dans `vars` (si fourni), `section` et dans `DEFAULTSECT` dans cet ordre.
        Si la clé n'est pas trouvée et que `fallback` est fourni, elle est utilisée comme valeur de secours.
        `None` peut être fourni comme valeur `fallback`.

        Si l'interpolation est activée et que l'argument facultatif « raw » est False,
        toutes les interpolations sont développées dans les valeurs de retour.

        Arguments « raw », « vars » et `fallback` sont uniquement des mots-clé.

        Args :
            section (str) : Le nom de la section.
            setting (str) : Le nom du paramètre.
            raw (bool) :
            vars : Dictionnaire

        Returns :
            La valeur de configuration.
        """
        return configparser.RawConfigParser.get(self, section, setting)
        # return configparser.ConfigParser(interpolation=None).get(self, section, setting)


class CachingConfigParser(UnicodeAwareConfigParser):
    """
    Un ConfigParser personnalisé qui met en cache les valeurs de configuration pour des performances améliorées.

    ConfigParser est plutôt lent, donc mettez en cache ses valeurs.

    Cette classe hérite d'UnicodeAwareConfigParser et ajoute une fonctionnalité de mise en cache
    pour éviter les recherches redondantes.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez CachingConfigParser.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        self.__cachedValues = dict()
        # UnicodeAwareConfigParser.__init__(self, *args, **kwargs)
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        """
        Lire les données de configuration à partir des fichiers.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args :
            *args : chemins de fichiers à lire.
            **kwargs : arguments de mot-clé supplémentaires.

        Returns :
            bool : True en cas de succès, False sinon.
        """
        self.__cachedValues = dict()
        # return UnicodeAwareConfigParser.read(self, *args, **kwargs)
        return super().read(*args, **kwargs)
        # Alors read ou readfp ?

    # def set(self, section, setting, value=None):
    def set(self, section, option, value=None):
        """
        Définissez une valeur de configuration et mettez-la en cache.

        Crée un attribut d'instance (dictionnaire) : __cachedValues

        Args :
            section (str) : Le nom de la section.
            setting (str) : Le nom du paramètre.
            value : La valeur à définir.
        """
        # self.__cachedValues[(section, setting)] = value
        # UnicodeAwareConfigParser.set(self, section, setting, value)
        self.__cachedValues[(section, option)] = value
        super().set(section, option, value)

    # def get(self, section, setting, *, raw=False, vars=None):
    def get(self, section, option, **kwargs):
        """
        Obtenez une valeur de configuration à partir du cache ou lisez-la si elle n'est pas mise en cache.

        Obtenez une valeur d'option pour une section donnée.
        Si `vars` est fourni, il doit s'agir d'un dictionnaire.
        L'option est recherchée dans `vars` (si fourni), `section` et dans `DEFAULTSECT` dans cet ordre.
        Si la clé n'est pas trouvée et que `fallback` est fourni, elle est utilisée comme valeur de secours.
        `None` peut être fourni comme valeur `fallback`.

        Si l'interpolation est activée et que l'argument facultatif « raw » est False,
        toutes les interpolations sont développées dans les valeurs de retour.

        Arguments « raw », « vars » et `fallback` sont uniquement des mots-clé.

        Args :
            section (str) : le nom de la section.
            setting (str) : le nom du paramètre.
            raw (bool) :
            vars : Dictionnaire

        Returns :
            La valeur de configuration.
        """
        # cache, key = self.__cachedValues, (section, setting)
        cache, key = self.__cachedValues, (section, option)
        if key not in cache:
            # cache[key] = UnicodeAwareConfigParser.get(self, *key)  # pylint: disable=W0142
            cache[key] = super().get(*key, **kwargs)
        return cache[key]


class Settings(CachingConfigParser):
    """
    Une classe pour gérer les paramètres de l'application, héritant de CachingConfigParser.

    Cette classe gère la lecture, l'écriture et la mise en cache des paramètres de l'application,
    y compris la gestion des valeurs par défaut et la migration des fichiers de configuration.
    """

    def __init__(
        self, load=True, iniFile=None, gui_used="tk", *args, **kwargs
    ):
        """
        Initialisez l'objet Paramètres.

        Args :
            load (bool, optional) : s'il faut charger les paramètres à partir du fichier. La valeur par défaut est True.
            iniFile (str, optional) : le chemin d'accès au fichier .ini. La valeur par défaut est Aucun.
            guiused (str) : Nom du GUI utilisé.
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        # --- LOG 1 : À l'entrée de __init__ de Page ---
        log.debug(f"--- Settings.__init__ entrée ---")
        log.debug(f"  load: {load}")
        log.debug(f"  iniFile (reçu par Settings): {iniFile}")
        log.debug(f"  *args (reçus par Settings): {args}")
        log.debug(f"  **kwargs (reçus par Settings): {kwargs}")
        # log.debug("Settings : Initialisation MRO:", Settings.__mro__)
        # Soupir, ConfigParser.SafeConfigParser est une classe à l'ancienne, donc nous
        # devons appeler explicitement la superclasse __init__ :
        CachingConfigParser.__init__(self, *args, **kwargs)

        self.initializeWithDefaults()
        self.__loadAndSave = load
        self.__iniFileSpecifiedOnCommandLine = iniFile
        self.__ini_lock = (
            None  # Lock for ini file to prevent concurrent access
        )

        self.migrateConfigurationFiles()
        self.gui_used = gui_used
        if self.gui_used == "wx":
            log.info("Settings.__init__ avec wx plutôt que tkinter.")
            import wx  # TODO : Trouver le moyen d'implémenter wx sans wx.App ou créer un autre fichier wxsettings.

            # self.wx = None  # wx quand ce sera corrigé !
            self.wx = wx  # wx quand ce sera corrigé !
            self.MessageboxUsed = self.wx.MessageBox
        elif self.gui_used == "tk":
            log.info("Settings.__init__ avec tkinter plutôt que wx.")
            self.MessageboxUsed = messagebox.showerror
        # Ensure errorMessage is initialized
        errorMessage = None

        # Check if this is first run (no INI file exists yet)
        isFirstRun = load and not self._iniFileExists()

        if load:
            # Tout d'abord, essayez de charger le fichier de paramètres depuis le répertoire du programme,
            # si cela échoue, chargez le fichier de paramètres depuis le répertoire des paramètres
            try:
                if not self.read(self.filename(forceProgramDir=True)):
                    self.read(self.filename())
                errorMessage = ""
            except configparser.ParsingError as e:
                # Ignorez les exceptions et utilisez simplement les valeurs par défaut.
                # Enregistrez également l'échec dans les paramètres :
                self.initializeWithDefaults()
                errorMessage = str(e)
            finally:
                # self.setLoadStatus(ExceptionAsUnicode(errorMessage))
                self.setLoadStatus(
                    errorMessage
                )  # UnboundLocalError: cannot access local variable 'errorMessage' where it is not associated with a value
            # On first run, set up Welcome.tsk in user's Documents folder
            if isFirstRun:
                self._setupFirstRunWelcomeFile()
        else:
            # Supposons que si les paramètres ne doivent pas être chargés, nous
            # devrions également rester silencieux (c'est-à-dire que nous sommes probablement en mode test) :
            self.__beQuiet()
        pub.subscribe(
            self.onSettingsFileLocationChanged,
            "settings.file.saveinifileinprogramdir",
        )  # Envoie un message de notification à onSettingsFileLocationChanged
        log.info("Settings.__init__ terminé avec succès !")

    def acquire_ini_lock(self):
        """Acquire lock on ini file to prevent multiple instances from
        corrupting config. Shows error and exits if another instance has lock.

        Note: This must be called after wxApp is created, as it may display
        a wx.MessageBox on failure."""
        try:
            import fasteners

            lock_path = self.filename() + ".lock"
            self.__ini_lock = fasteners.InterProcessLock(lock_path)
            acquired = self.__ini_lock.acquire(blocking=False)
            if not acquired:
                # Another instance has the lock
                # wx.MessageBox(
                self.MessageboxUsed(
                    _(
                        "Another instance of %s is already running with the same "
                        "configuration file.\n\n"
                        "You can run multiple instances with different configuration "
                        "files using the --ini option:\n"
                        "  taskcoach --ini=/path/to/other.ini\n\n"
                        "The program will now exit."
                    )
                    % meta.name,
                    _("%s: configuration locked") % meta.name,
                    # style=wx.OK | wx.ICON_ERROR,
                )
                sys.exit(1)
        except ImportError:
            # fasteners not available - skip locking
            pass
        except Exception as e:
            # Lock failed for other reasons (permissions, etc.) - continue without lock
            log.error("acquire_ini_lock", stack_info=True)
            pass

    def release_ini_lock(self):
        """Release the ini file lock. Call this on application shutdown."""
        if self.__ini_lock is not None:
            try:
                self.__ini_lock.release()
            except Exception:
                pass  # Ignore errors during cleanup
            self.__ini_lock = None

    def onSettingsFileLocationChanged(self, value):
        """
        Gérer les modifications apportées à l'emplacement du fichier de paramètres.

        Crée un attribut saveIniFileInProgramDir qui prend la valeur de value.

        Args :
            value (bool) : s'il faut enregistrer le fichier .ini dans le répertoire du programme.
        """
        saveIniFileInProgramDir = value
        if not saveIniFileInProgramDir:
            try:
                os.remove(self.generatedIniFilename(forceProgramDir=True))
            except Exception:
                return  # pylint: disable=W0702

    def initializeWithDefaults(self):
        """
        Initialisez les paramètres avec les valeurs par défaut.
        """
        log.info(
            "Settings.initializeWithDefaults : Initialisation des paramètres avec les valeurs par défaut."
        )
        for section in self.sections():
            self.remove_section(section)
        for section, settings in list(defaults.defaults.items()):
            self.add_section(section)
            for key, value in list(settings.items()):
                # Don't Notify observers while we are initializing
                log.info(
                    f"Settings.initializeWithDefaults : Initialisation de la section '{section}', paramètre '{key}' avec la valeur par défaut '{value}'."
                )
                super().set(section, key, value)

    def setLoadStatus(self, message):
        """
        Définissez l'état de chargement du fichier de paramètres.

        Args :
            message (str) : Le message d'erreur en cas d'échec du chargement.
        """
        self.set("file", "inifileloaded", "False" if message else "True")
        self.set("file", "inifileloaderror", message)

    def __beQuiet(self):
        """
        Désactivez les paramètres bruyants pour le mode silencieux (par exemple, pendant les tests).
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
        Ajoutez une nouvelle section aux paramètres.

        Args :
            section (str) : Le nom de la section.
            copyFromSection (str, optional) : La section à partir de laquelle copier les valeurs. La valeur par défaut est Aucun.

        Returns :
            bool : Vrai si la section a été ajoutée avec succès.
        """
        result = super().add_section(section)
        if copyFromSection:
            for name, value in self.items(copyFromSection):
                super().set(section, name, value)
        return result

    def getRawValue(self, section, option):
        # def getRawValue(self, section: str, option: str):
        """
        Obtenez une valeur brute (non évaluée) à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            str : La valeur brute.
        """
        return super().get(section, option)

    def init(self, section, option, value):
        # def init(self, section: str, option: str, value):
        """
        Initialisez un paramètre avec une valeur donnée.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value : La valeur à définir.

        Returns :
            bool : vrai si la valeur a été définie avec succès.
        """
        return super().set(section, option, value)

    # def get(self, section, option, raise_on_missing=False, *, raw=False, vars=None):
    def get(self, section, option, raise_on_missing=False, **kwargs):
        # def get(self, section: str, option: str):
        """
        Obtenez une valeur à partir des paramètres, de la gestion des valeurs par défaut et des anciens formats de fichier .ini.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            raise_on_missing (bool) :
            raw (bool) :
            vars :

        Returns :
            La valeur du paramètre.
        """
        try:
            result = super().get(section, option, **kwargs)
        except configparser.NoSectionError:
            if raise_on_missing:
                raise
            else:
                return self.getDefault(section, option)
        except configparser.NoOptionError:
            if raise_on_missing:
                raise  # Raise for tests
            else:
                return self.getDefault(
                    section, option
                )  # Use default for normal use
        except KeyError:
            if raise_on_missing:
                raise configparser.NoOptionError(option, section)
            else:
                return self.getDefault(section, option)

        result = self._fixValuesFromOldIniFiles(section, option, result)
        result = self._ensureMinimum(section, option, result)
        return result

    def getDefault(self, section, option):
        # def getDefault(self, section: str, option: str) -> Any:
        """
        Obtenez la valeur par défaut pour un paramètre donné.

        Args :
            section (str) : Le nom de la section (les chiffres sont ignorés).
            option (str) : Le nom de l'option.
            default (Any, optional) : Valeur par défaut à retourner si l'option n'est pas trouvée.

        Returns :
            La valeur par défaut.
            Obtenez la valeur par défaut pour un paramètre donné.
            La valeur par défaut ou la valeur trouvée dans le dictionnaire
            ou None si elle n'est pas trouvée.

        Raises :
            configparser.NoSectionError : Si la section n'existe pas.
            configparser.NoOptionError : Si l'option n'existe pas dans la section.
        """
        # Optimisations possibles :
        # Mémoïsation: Si la méthode getDefault est appelée fréquemment avec les mêmes arguments,
        # vous pouvez envisager d'implémenter une cache pour éviter de recalculer les valeurs par défaut.
        # Profilage: Utiliser un profileur pour identifier les goulots d'étranglement
        # et optimiser les parties les plus lentes du code.
        if not section or not option:
            raise ValueError(
                "Settings.getDefault : Section et option doivent être des chaînes non vides."
            )

        defaultSectionKey = section.strip(
            "0123456789"
        )  # Suppression des chiffres non pertinents
        # try:
        #     defaultSection = defaults.defaults[defaultSectionKey]
        # except KeyError:
        #     raise configparser.NoSectionError(defaultSectionKey)
        # try:
        #     return defaultSection[option]
        # except KeyError:
        #     raise configparser.NoOptionError((option, defaultSection))
        # Nouveau code:
        try:
            defaultSection = defaults.defaults[defaultSectionKey]
            return defaultSection.get(option)
        except KeyError as e:
            if e.args[0] == defaultSectionKey:
                # Si la section n'existe pas, lever une exception NoSectionError
                raise configparser.NoSectionError(defaultSectionKey)
            else:
                raise configparser.NoOptionError(option, defaultSectionKey)
        # Autres améliorations possibles :
        #     Validation des entrées : Vérifier que section et option sont des chaînes non vides.
        #     Utilisation d'un logger : Enregistrer les appels à la fonction et les erreurs éventuelles dans un fichier de log.

    def _ensureMinimum(self, section, option, result):
        # def _ensureMinimum(self, section: str, option: str, result):
        """
        Assurez-vous qu'une valeur de paramètre répond aux exigences minimales.

        Args :
            section (str) : le nom de la section.
            option (str) : le nom de l'option.
            result : la valeur à vérifier.

        Returns :
            La valeur result, garantissant qu'elle répond aux exigences minimales.
        """
        if section in defaults.minimum and option in defaults.minimum[section]:
            result = max(result, defaults.minimum[section][option])
        return result

    def _migrateOldSettingNames(self):
        """Migrate old setting names to new names for backward compatibility."""
        # Mapping of (section, old_name) -> new_name
        migrations = [
            ("feature", "sdtcspans", "task_duration_presets"),
            ("feature", "sdtcspans_effort", "effort_duration_presets"),
        ]
        for section, old_name, new_name in migrations:
            try:
                if self.has_option(section, old_name):
                    old_value = super().get(section, old_name)
                    if not self.has_option(section, new_name):
                        self.set(section, new_name, old_value)
                    self.remove_option(section, old_name)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass

    def _fixValuesFromOldIniFiles(self, section, option, result):
        # def _fixValuesFromOldIniFiles(self, section: str, option: str, result):
        """
        Corrigez les paramètres des anciens fichiers TaskCoach.ini qui ne sont plus valides.

        Args :
            section (str) : le nom de la section.
            option (str) : le nom de l'option.
            result : La valeur à corriger.

        Returns :
            La valeur result corrigée.
        """
        original = result
        log.debug(
            f"Settings._fixValuesFromOldIniFiles : Corrige result={result}"
        )
        # À partir de la version 1.1.0, les propriétés de date des tâches (startDate,
        # dueDate et CompletionDate) sont des datetimes :
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
                # eval(result)
                ast.literal_eval(result)
            except Exception:
                sortKeys = [result]
                try:
                    ascending = self.getboolean(section, "sortascending")
                except Exception:
                    ascending = True
                result = '["%s%s"]' % (("" if ascending else "-"), result)
                # result = f'["{("" if ascending else "-")}{result}"]'
        elif option == "columns":
            columns = [
                (col + "Time" if col in taskDateColumns else col)
                # for col in eval(result)
                for col in ast.literal_eval(result)
            ]
            result = str(columns)
        elif option == "columnwidths":
            widths = dict()
            try:
                # columnWidthMap = eval(result)
                columnWidthMap = ast.literal_eval(result)
                # Elle tente d'évaluer la chaîne de caractères comme une expression Python, ce qui échoue avec une erreur.
                # ValueError: malformed node or string on line 1: Call(func=Name(id='dict', ctx=Load()), args=[], keywords=[keyword(arg='subject', value=Constant(value=10, kind=None))])
            # except SyntaxError:
            except (SyntaxError, ValueError) as e:
                log.error(
                    f"Settings._fixValuesFromOldIniFiles : Error occurred while evaluating columnwidths : {e}"
                )
                # columnWidthMap = dict()
                # Si la chaîne ressemble à "dict(subject=10)", on l'analyse manuellement
                if result.startswith("dict(") and result.endswith(")"):
                    # Extraire les arguments entre parenthèses
                    args_str = result[5:-1]
                    # Analyser les arguments pour créer un dictionnaire
                    columnWidthMap = {}
                    for arg in args_str.split(","):
                        if "=" in arg:
                            key, value = arg.split("=", 1)
                            columnWidthMap[key.strip()] = int(value.strip())
                    log.debug(
                        f"Settings._fixValuesFromOldIniFiles : columnWidthMap={columnWidthMap}"
                    )
                #     return columnWidthMap
                # else:
                #     return {}
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
                # columns = eval(result)
                columns = ast.literal_eval(result)
            except SyntaxError:
                columns = ["ordering"]
            else:
                if "ordering" in columns:
                    columns.remove("ordering")
            result = str(columns)
        if result != original:
            super().set(section, option, result)
        return result

    def set(
        self, section, option, value=None, new=False
    ):  # pylint: disable=W0221
        # def set(self, section: str, option: str, value, new: bool = False) -> bool:  # pylint: disable=W0221
        """
        Définissez une valeur dans les paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value : La valeur à définir.
            new (bool, optional) : s'il s'agit d'une nouvelle option. La valeur par défaut est False.

        Returns :
            bool : True si la valeur a été définie avec succès.
        """
        if new:
            currentValue = (
                "a new option, so use something as current value"
                " that is unlikely to be equal to the new value"
            )
        else:
            currentValue = self.get(section, option)
        if value != currentValue:
            super().set(section, option, value)
            # patterns.Event("%s.%s" % (section, option), self, value).send()
            patterns.Event(f"{section}.{option}", self, value).send()
            return True
        else:
            return False

    def setboolean(self, section, option, value):
        # def setboolean(self, section: str, option: str, value: bool) -> bool:
        """
        Définissez une valeur booléenne dans les paramètres.

        Args :, *, raw=False, vars=None
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value (bool) : La valeur à définir.

        Returns :
            bool : Vrai si la valeur a été définie avec succès.
        """
        if self.set(section, option, str(value)):
            # pub.sendMessage("settings.%s.%s" % (section, option), value=value)
            topic = f"settings.{section}.{option}"
            pub.sendMessage(  # Attention à la signature de pub.sendMessage, elle peut varier selon la version de pypubsub utilisée.
                # "settings.%s.%s" % (section, option),
                # # event=f"{section}.{option}",
                # event=topic,
                topic,
                # value=value,
                value=value,
            )
            # pub.sendMessage(f"settings.{section}.{option}", value=value)
            # pubsub.core.topicargspec.SenderMissingReqdMsgDataError: Some required args missing in call to sendMessage('settings.effortviewer.round', event): value

    setvalue = settuple = setlist = setdict = setint = setboolean

    def settext(self, section, option, value):
        # def settext(self, section: str, option: str, value):
        """
        Définissez une valeur de texte dans les paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            value (str) : La valeur à définir.

        Returns :
            bool : Vrai si la valeur a été définie avec succès.
        """
        if self.set(section, option, value):
            # pub.sendMessage("settings.%s.%s" % (section, option), value=value)
            pub.sendMessage(f"settings.{section}.{option}", value=value)

    def getlist(self, section, option):
        """
        Obtenez une valeur de liste à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            list : La valeur de la liste.
        """
        # return self.getEvaluatedValue(section, option, eval)
        return self.getEvaluatedValue(section, option, ast.literal_eval)

    getvalue = gettuple = getdict = getlist

    def getint(self, section, option, *, raw=False, vars=None):
        # def getint(self, section, option) -> int:
        """
        Obtenez une valeur entière à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            int : la valeur entière.
        """
        return self.getEvaluatedValue(section, option, int)

    def getboolean(self, section, option, *, raw=False, vars=None):
        # def getboolean(self, section, option) -> bool:
        """
        Obtenez une valeur booléenne à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            bool : La valeur booléenne.
        """
        # return self.getEvaluatedValue(section, option, self.evalBoolean)
        try:
            return self.getEvaluatedValue(section, option, self.evalBoolean)
        except ValueError:
            # Si la conversion en booléen échoue, renvoyez une valeur par défaut.
            # L'erreur `ValueError: invalid literal for Boolean value: '(22, 22)'`
            # indique que le paramètre "view", "toolbar" n'est pas une valeur booléenne.
            # Nous renvoyons True par défaut pour que l'application puisse continuer.
            log.warning(
                f"Settings.getboolean : La valeur pour [{section}] {option} n'est pas un booléen valide. Utilisation de la valeur par défaut True."
            )
            return True

    def gettext(self, section, option):
        # def gettext(self, section, option) -> str:
        """
        Obtenez une valeur de texte à partir des paramètres.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.

        Returns :
            str : la valeur du texte.
        """
        return self.get(section, option)

    @staticmethod
    def evalBoolean(stringValue):
        # def evalBoolean(stringValue: str) -> bool:
        """
        Évalue une chaîne en tant que valeur booléenne.

        Args :
            stringValue (str) : La valeur de la chaîne.

        Returns :
            bool : La valeur booléenne évaluée.

        Raises :
            ValueError : Relève un message d'erreur si la chaîne n'est pas une valeur booléenne valide.
        """
        if stringValue in ("True", "False"):
            return "True" == stringValue
        else:
            raise ValueError(
                # "invalid literal for Boolean value: '%s'" % stringValue
                f"invalid literal for Boolean value: '{stringValue}'"
            )

    # if Application._options.gui_name == "wx":
    # def getEvaluatedValue(
    #     self, section, option, evaluate=eval, showerror=wx.MessageBox
    # ):
    def getEvaluatedValue(
        # self, section, option, evaluate=eval,
        self,
        section,
        option,
        evaluate=ast.literal_eval,
    ):
        # def getEvaluatedValue(
        #         self, section: str, option: str, evaluate=eval, showerror=wx.MessageBox
        # ):
        """
        Obtenez une valeur à partir des paramètres et évaluez-la.

        Args :
            section (str) : Le nom de la section.
            option (str) : Le nom de l'option.
            evaluate (fonction, optional) : La fonction pour évaluer la valeur. La valeur par défaut est eval.
            showerror (fonction, optional) : la fonction pour afficher les erreurs. La valeur par défaut est wx.MessageBox.

        Returns :
            La valeur évaluée.
        """
        stringValue = self.get(section, option)
        if stringValue:
            try:
                return evaluate(stringValue)
            except Exception as exceptionMessage:  # pylint: disable=W0703
                message = "\n".join(
                    [
                        # _("Error while reading the %s-%s setting from %s.ini.")
                        # % (section, option, meta.filename),
                        _(
                            f"Error while reading the {section}.{option} setting from {meta.filename}.ini."
                        ),
                        # _("The value is: %s") % stringValue,
                        _(f"The value is: {stringValue}"),
                        # _("The error is: %s") % exceptionMessage,
                        _(f"The error is: {exceptionMessage}"),
                        # _(
                        #     "%s will use the default value for the setting and should proceed normally."
                        # )
                        # % meta.name,
                        _(
                            f"{meta.name} will use the default value for the setting and should proceed normally."
                        ),
                    ]
                )
                if self.gui_used == "wx" and self.wx:
                    self.wx.MessageBox(
                        message,
                        caption=_("Settings error"),
                        style=self.wx.ICON_ERROR,
                    )
                elif self.gui_used == "tk":
                    messagebox.showerror(_("Settings error"), message)
                log.error(message)
                defaultValue = self.getDefault(section, option)
                self.set(
                    section, option, defaultValue, new=True
                )  # Ignore current value
            return evaluate(defaultValue)
        else:
            return None

    # def save(
    #     self, showerror=wx.MessageBox, file=open
    # ):  # pylint: disable=W0622
    # def save(self, file=open):  # pylint: disable=W0622
    def save(self, showerror=None, file=open):  # pylint: disable=W0622
        """
        Enregistrez les paramètres dans un fichier.

        Args :
            showerror (fonction, optional) : La fonction pour afficher les erreurs. La valeur par défaut est le fichier wx.MessageBox.
            file (fonction, optional) : La fonction pour ouvrir les fichiers. Par défaut, open.
        """
        self.set("version", "python", sys.version)
        # self.set(
        #     "version",
        #     "wxpython",
        #     "%s-%s @ %s"
        #     % (wx.VERSION_STRING, wx.PlatformInfo[2], wx.PlatformInfo[1]),
        # )
        if self.gui_used == "wx" and self.wx:
            self.set(
                "version",
                "wxpython",
                f"{self.wx.VERSION_STRING}-{self.wx.PlatformInfo[2]} @ {self.wx.PlatformInfo[1]}",
            )
        elif self.gui_used == "tk":
            self.set("version", "tkinter", f"{tk.TkVersion}")
        self.set("version", "pythonfrozen", str(hasattr(sys, "frozen")))
        self.set("version", "current", meta.data.version)
        if not self.__loadAndSave:
            return
        try:
            path = self.path()
            if not os.path.exists(path):
                # os.mkdir(path)
                os.makedirs(path, exist_ok=True)
            # tmpFile = file(self.filename() + ".tmp", "w")
            tmpFile = file(self.filename() + ".tmp", "w", encoding="utf-8")
            self.write(tmpFile)
            tmpFile.close()
            if os.path.exists(self.filename()):
                os.remove(self.filename())
            os.rename(self.filename() + ".tmp", self.filename())
        except Exception as message:  # pylint: disable=W0703
            if self.gui_used == "wx" and self.wx:
                self.wx.MessageBox(
                    # _("Error while saving %s.ini:\n%s\n")
                    # % (meta.filename, message),
                    _(f"Error while saving {meta.filename}.ini:\n{message}\n"),
                    caption=_("Save error"),
                    style=self.wx.ICON_ERROR,
                )
            elif self.gui_used == "tk":
                messagebox.showerror(
                    _("Save error"),
                    _(f"Error while saving {meta.filename}.ini:\n{message}\n"),
                )

    # if Application._options.gui_name == "tk":
    #     def getEvaluatedValue(
    #         self, section, option, evaluate=eval, showerror=messagebox.showerror
    #     ):
    #         """
    #         Obtenez une valeur à partir des paramètres et évaluez-la.
    #
    #         Args :
    #             section (str) : Le nom de la section.
    #             option (str) : Le nom de l'option.
    #             evaluate (fonction, optional) : La fonction pour évaluer la valeur. La valeur par défaut est eval.
    #             showerror (fonction, optional) : la fonction pour afficher les erreurs. La valeur par défaut est wx.MessageBox.
    #
    #         Returns :
    #             La valeur évaluée.
    #         """
    #         stringValue = self.get(section, option)
    #         try:
    #             return evaluate(stringValue)
    #         except Exception as exceptionMessage:
    #             message = "\n".join(
    #                 [
    #                     f"Error while reading the {section}-{option} setting from {meta.filename}.ini.",
    #                     f"The value is: {stringValue}",
    #                     f"The error is: {exceptionMessage}",
    #                     f"{meta.name} will use the default value for the setting and should proceed normally."
    #                 ]
    #             )
    #             showerror(message, "Settings error")
    #             defaultValue = self.getDefault(section, option)
    #             self.set(section, option, defaultValue, new=True)  # Ignore current value
    #             return evaluate(defaultValue)
    #
    #     def save(
    #         self, showerror=messagebox.showerror, file=open
    #     ):  # pylint: disable=W0622
    #         """
    #         Enregistrez les paramètres dans un fichier.
    #
    #         Args :
    #             showerror (fonction, optional) : La fonction pour afficher les erreurs. La valeur par défaut est le fichier wx.MessageBox.
    #             file (fonction, optional) : La fonction pour ouvrir les fichiers. Par défaut, open.
    #         """
    #         self.set("version", "python", sys.version)
    #         self.set("version", "tkinter", f"{tk.TkVersion}")
    #         self.set("version", "pythonfrozen", str(hasattr(sys, "frozen")))
    #         self.set("version", "current", meta.data.version)
    #
    #         if not self.__loadAndSave:
    #             return
    #
    #         try:
    #             path = self.path()
    #             if not os.path.exists(path):
    #                 os.mkdir(path)
    #             tmpFile = file(self.filename() + ".tmp", "w")
    #             self.write(tmpFile)
    #             tmpFile.close()
    #             if os.path.exists(self.filename()):
    #                 os.remove(self.filename())
    #             os.rename(self.filename() + ".tmp", self.filename())
    #         except Exception as message:
    #             showerror(f"Error while saving {meta.filename}.ini:\n{message}\n", "Save error")

    def filename(self, forceProgramDir=False):
        # def filename(self, forceProgramDir: bool = False) -> str:
        """
        Obtenez le nom de fichier du fichier .ini.

        Args :
            forceProgramDir (bool, optional) : s'il faut forcer l'enregistrement dans le répertoire du programme. La valeur par défaut est False.

        Returns :
            str : Le nom du fichier .ini.
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
            log.info(
                f"Settings.path : Retourne le chemin du fichier .ini spécifié sur la ligne de commande. self.pathToIniFileSpecifiedOnCommandLine()={self.pathToIniFileSpecifiedOnCommandLine()}"
            )
            return self.pathToIniFileSpecifiedOnCommandLine()
        elif forceProgramDir or self.getboolean(
            "file", "saveinifileinprogramdir"
        ):
            log.info(
                f"Settings.path : Retourne le chemin du répertoire du programme. self.pathToProgramDir()={self.pathToProgramDir()}"
            )
            return self.pathToProgramDir()
        else:
            log.info(
                f"Settings.path : Retourne le chemin du répertoire de configuration. self.pathToConfigDir(environ)={self.pathToConfigDir(environ)}"
            )
            return self.pathToConfigDir(environ)

    @staticmethod
    def pathToDocumentsDir():
        """
        Obtenez le chemin d'accès au répertoire des documents.

        Returns :
            str : Le chemin d'accès au répertoire des documents.
        """
        # if operating_system.isWindows():
        #     from win32com.shell import shell, shellcon
        #
        #     try:
        #         return shell.SHGetSpecialFolderPath(
        #             None, shellcon.CSIDL_PERSONAL
        #         )
        #     except:
        #         # Yes, one of the documented ways to get this sometimes fail with "Unspecified error". Not sure
        #         # this will work either.
        #         # Update: There are cases when it doesn't work either; see support request #410...
        #         try:
        #             return shell.SHGetFolderPath(
        #                 None, shellcon.CSIDL_PERSONAL, None, 0
        #             )  # SHGFP_TYPE_CURRENT not in shellcon
        #         except:
        #             return os.getcwd()  # Fuck this
        # elif operating_system.isMac():
        #     import Carbon.Folder
        #     import Carbon.Folders
        #     import Carbon.File
        #
        #     pathRef = Carbon.Folder.FSFindFolder(
        #         Carbon.Folders.kUserDomain,
        #         Carbon.Folders.kDocumentsFolderType,
        #         True,
        #     )
        #     return Carbon.File.pathname(pathRef)
        if operating_system.isGTK():
            try:
                from PyKDE4.kdeui import KGlobalSettings
            except ImportError:
                pass
            else:
                return str(KGlobalSettings.documentPath())
            # Check XDG_DOCUMENTS_DIR (standard on Linux)
            xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
            if xdg_docs and os.path.isdir(xdg_docs):
                return xdg_docs
            # Fall back to ~/Documents if it exists
            docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.isdir(docs_dir):
                return docs_dir
        # Assuming Unix-like, fall back to home
        return os.path.expanduser("~")

    def _iniFileExists(self):
        """Check if INI file exists in either program dir or config dir."""
        return os.path.exists(
            self.filename(forceProgramDir=True)
        ) or os.path.exists(self.filename())

    @staticmethod
    def pathToSystemWelcomeFile():
        """Find the system-installed Welcome.tsk file."""
        # Check platform-specific locations
        if operating_system.isWindows():
            # Windows: look in install directory
            candidates = [
                os.path.join(os.path.dirname(sys.executable), "Welcome.tsk"),
                os.path.join(os.path.dirname(sys.argv[0]), "Welcome.tsk"),
            ]
        elif operating_system.isMac():
            # macOS: look in app bundle Resources
            candidates = [
                os.path.join(
                    os.path.dirname(sys.executable),
                    "..",
                    "Resources",
                    "Welcome.tsk",
                ),
                os.path.join(os.path.dirname(sys.argv[0]), "Welcome.tsk"),
            ]
        else:
            # Linux: check standard system locations
            candidates = [
                "/usr/share/taskcoach/Welcome.tsk",
                "/usr/local/share/taskcoach/Welcome.tsk",
                "/usr/share/doc/taskcoach/Welcome.tsk",
                os.path.join(os.path.dirname(sys.argv[0]), "Welcome.tsk"),
            ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _setupFirstRunWelcomeFile(self):
        """On first run, copy Welcome.tsk to user's Documents folder."""
        systemWelcome = self.pathToSystemWelcomeFile()
        if not systemWelcome:
            return  # No system Welcome.tsk found

        # Create TaskCoach folder in user's Documents
        docsDir = self.pathToDocumentsDir()
        taskcoachDocsDir = os.path.join(docsDir, meta.filename)
        userWelcome = os.path.join(taskcoachDocsDir, "Welcome.tsk")

        # Don't overwrite if user already has a Welcome.tsk
        if os.path.exists(userWelcome):
            # But still set it as the file to open on first run
            self.set("file", "lastfile", userWelcome)
            return

        try:
            if not os.path.exists(taskcoachDocsDir):
                os.makedirs(taskcoachDocsDir)
            shutil.copy(systemWelcome, userWelcome)
            # Set this as the last opened file so it opens on startup
            self.set("file", "lastfile", userWelcome)
        except OSError:
            pass  # Silently fail if we can't copy

    def pathToProgramDir(self):
        """
        Obtenez le chemin d'accès au répertoire du programme.

        Returns :
            str : Le chemin d'accès au répertoire du programme.
        """
        log.info(
            "Settings.pathToProgramDir : Détermine le chemin du répertoire du programme."
        )
        # path = sys.argv[0]
        path = os.path.abspath(sys.argv[0])
        log.info(
            f"Settings.pathToProgramDir : Chemin absolu du programme : path={path}"
        )
        if not os.path.isdir(path):
            path = os.path.dirname(path)
            log.info(
                f"Settings.pathToProgramDir : path n'est pas un répertoire, prend le répertoire parent : path={path}"
            )
        # Normaliser le chemin pour éviter les problèmes de chemin absolu local
        path = os.path.normpath(path)
        return path

    def pathToConfigDir(self, environ):
        """
        Obtenez le chemin d'accès au répertoire de configuration.

        Args :
            environ (dict) : Les variables d'environnement.

        Returns :
            str : Le chemin d'accès au répertoire de configuration.
        """
        try:
            if operating_system.isGTK():
                # from taskcoachlib.thirdparty.xdg import BaseDirectory
                from xdg import BaseDirectory

                path = BaseDirectory.save_config_path(meta.name)
            # elif operating_system.isMac():
            #     import Carbon.Folder
            #     import Carbon.Folders
            #     import Carbon.File
            #
            #     pathRef = Carbon.Folder.FSFindFolder(
            #         Carbon.Folders.kUserDomain,
            #         Carbon.Folders.kPreferencesFolderType,
            #         True,
            #     )
            #     path = Carbon.File.pathname(pathRef)
            #     # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
            # elif operating_system.isWindows():
            #     from win32com.shell import shell, shellcon
            #
            #     path = os.path.join(
            #         shell.SHGetSpecialFolderPath(
            #             None, shellcon.CSIDL_APPDATA, True
            #         ),
            #         meta.name,
            #     )
            else:
                path = self.pathToConfigDir_deprecated(environ=environ)
        except Exception:  # Fallback to old dir
            path = self.pathToConfigDir_deprecated(environ=environ)
        return path

    def _pathToDataDir(self, *args, **kwargs):
        """
        Obtenez le chemin d'accès au répertoire de données.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Returns :
            str : le chemin d'accès au répertoire de données.
        """
        forceGlobal = kwargs.pop("forceGlobal", False)
        if operating_system.isGTK():
            # from taskcoachlib.thirdparty.xdg import BaseDirectory
            from xdg import BaseDirectory

            path = BaseDirectory.save_data_path(meta.name)
        # elif operating_system.isMac():
        #     from Carbon import Folder
        #     from Carbon import Folders
        #     from Carbon import File
        #
        #     pathRef = Folder.FSFindFolder(
        #         Folders.kUserDomain,
        #         Folders.kApplicationSupportFolderType,
        #         True,
        #     )
        #     path = File.pathname(pathRef)
        #     # XXXFIXME: should we release pathRef ? Doesn't seem so since I get a SIGSEGV if I try.
        #     path = os.path.join(path, meta.name)
        # elif operating_system.isWindows():
        #     if self.__iniFileSpecifiedOnCommandLine and not forceGlobal:
        #         path = self.pathToIniFileSpecifiedOnCommandLine()
        #     else:
        #         from win32com.shell import shell, shellcon
        #
        #         path = os.path.join(
        #             shell.SHGetSpecialFolderPath(
        #                 None, shellcon.CSIDL_APPDATA, True
        #             ),
        #             meta.name,
        #         )
        else:  # Errr...
            path = self.path()

        # if operating_system.isWindows():
        #     # Follow shortcuts.
        #     from win32com.client import Dispatch
        #
        #     shell = Dispatch("WScript.Shell")
        #     for component in args:
        #         path = os.path.join(path, component)
        #         if os.path.exists(path + ".lnk"):
        #             shortcut = shell.CreateShortcut(path + ".lnk")
        #             path = shortcut.TargetPath
        # else:
        path = os.path.join(path, *args)

        exists = os.path.exists(path)
        if not exists:
            os.makedirs(path)
        return path, exists

    def pathToDataDir(self, *args, **kwargs):
        """
        Obtenez le chemin d'accès au répertoire de données.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Returns :
            str : le chemin d'accès au répertoire de données.
        """
        return self._pathToDataDir(*args, **kwargs)[0]

    def _pathToTemplatesDir(self):
        """
        Obtenez le chemin d'accès au répertoire des modèles.

        Returns :
            str : Le chemin d'accès au répertoire des modèles.
        """
        try:
            return self._pathToDataDir("templates")
        except Exception:
            pass  # Fallback on old path
        return self.pathToTemplatesDir_deprecated(), True

    def pathToTemplatesDir(self):
        """
        Obtenez le chemin d'accès au répertoire des modèles.

        Returns :
            str : Le chemin d'accès au répertoire des modèles.
        """
        return self._pathToTemplatesDir()[0]

    def pathToBackupsDir(self):
        """
        Obtenez le chemin d'accès au répertoire des sauvegardes.

        Returns :
            str : Le chemin d'accès au répertoire des sauvegardes.
        """
        return self._pathToDataDir("backups")[0]

    def pathToConfigDir_deprecated(self, environ):
        """
        Obtenez le chemin obsolète vers le répertoire de configuration.

        Args :
            environ (dict) : Les variables d'environnement.

        Returns :
            str : Le chemin obsolète vers le répertoire de configuration.
        """
        try:
            path = os.path.join(environ["APPDATA"], meta.filename)
        except Exception:
            path = os.path.expanduser("~")  # pylint: disable=W0702
            if path == "~":
                # chemin non développé : apparemment, il n'y a pas de répertoire personnel
                path = os.getcwd()
            # path = os.path.join(path, '.%s' % meta.filename)
            path = os.path.join(path, f".{meta.filename}")
        return operating_system.decodeSystemString(path)

    def pathToTemplatesDir_deprecated(self, doCreate=True):
        # def pathToTemplatesDir_deprecated(self, doCreate: bool = True) -> str:
        """
        Obtenez le chemin obsolète vers le répertoire des modèles.

        Args :
            doCreate (bool, optional) : s'il faut créer le répertoire s'il n'existe pas. La valeur par défaut est True.

        Returns :
            str : le chemin obsolète vers le répertoire des modèles.
        """
        path = os.path.join(self.path(), "taskcoach-templates")

        # if operating_system.isWindows():
        #     # Under Windows, check for a shortcut and follow it if it
        #     # exists.
        #
        #     if os.path.exists(path + ".lnk"):
        #         from win32com.client import Dispatch  # pylint: disable=F0401
        #
        #         shell = Dispatch("WScript.Shell")
        #         shortcut = shell.CreateShortcut(path + ".lnk")
        #         return shortcut.TargetPath

        if doCreate:
            try:
                os.makedirs(path)
            except OSError:
                pass
        return operating_system.decodeSystemString(path)

    def pathToIniFileSpecifiedOnCommandLine(self):
        """
        Obtenez le chemin d'accès au fichier .ini spécifié sur la ligne de commande.

        Returns :
            str : Le chemin d'accès au fichier .ini spécifié sur la ligne de commande.
        """
        return os.path.dirname(self.__iniFileSpecifiedOnCommandLine) or "."

    def generatedIniFilename(self, forceProgramDir):
        """
        Génère le nom de fichier du fichier .ini.

        Args :
            forceProgramDir (bool) : s'il faut forcer l'enregistrement dans le répertoire du programme.

        Returns :
            str : Le nom de fichier généré du fichier .ini.
        """
        # return os.path.join(self.path(forceProgramDir), '%s.ini' % meta.filename)
        return os.path.join(self.path(forceProgramDir), f"{meta.filename}.ini")

    def migrateConfigurationFiles(self):
        # def migrateConfigurationFiles(self) -> None:
        """
        Migrez les fichiers de configuration vers de nouveaux emplacements si nécessaire.
        """
        # Modèles(Templates). Attention particulière au raccourci Windows.
        oldPath = self.pathToTemplatesDir_deprecated(doCreate=False)
        newPath, exists = self._pathToTemplatesDir()
        if self.__iniFileSpecifiedOnCommandLine:
            globalPath = os.path.join(
                self.pathToDataDir(forceGlobal=True), "templates"
            )
            if os.path.exists(globalPath) and not os.path.exists(oldPath):
                # Mise à niveau à partir d'une nouvelle installation de 1.3.24 Portable
                oldPath = globalPath
                if exists and not os.path.exists(newPath + "-old"):
                    # WTF?
                    os.rename(newPath, newPath + "-old")
                exists = False
        if exists:
            return
        if oldPath != newPath:
            # if operating_system.isWindows() and os.path.exists(
            #     oldPath + ".lnk"
            # ):
            #     shutil.move(oldPath + ".lnk", newPath + ".lnk")
            # elif os.path.exists(oldPath):
            if os.path.exists(oldPath):
                # pathToTemplatesDir() has created the directory
                try:
                    os.rmdir(newPath)
                except Exception:
                    pass
                shutil.move(oldPath, newPath)
        # Ini file
        # oldPath = os.path.join(self.pathToConfigDir_deprecated(environ=os.environ), '%s.ini' % meta.filename)
        # newPath = os.path.join(self.pathToConfigDir(environ=os.environ), '%s.ini' % meta.filename)
        oldPath = os.path.join(
            self.pathToConfigDir_deprecated(environ=os.environ),
            f"{meta.filename}.ini",
        )
        newPath = os.path.join(
            self.pathToConfigDir(environ=os.environ),
            f"{meta.filename}.ini",
        )
        if newPath != oldPath and os.path.exists(oldPath):
            shutil.move(oldPath, newPath)
        # Cleanup
        try:
            os.rmdir(self.pathToConfigDir_deprecated(environ=os.environ))
        except Exception:
            pass

    def __hash__(self):
        # def __hash__(self) -> int:
        """
        Obtenez le hachage de l'objet Paramètres(Settings).

        Returns :
            id (int) : L'id de hachage de l'objet Paramètres.
        """
        return id(self)
