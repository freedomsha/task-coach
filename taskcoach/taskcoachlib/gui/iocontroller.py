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
        """Renvoie la configuration de synchronisation du fichier de tâches.

        Returns :
            dict : La configuration de synchronisation du fichier de tâches.
        """
        return self.__taskFile.syncMLConfig()

    def setSyncMLConfig(self, config):
        """Définit la configuration de synchronisation du fichier de tâches.

        Args :
            config (dict) : La nouvelle configuration de synchronisation.

        Returns :
            None
        """
        self.__taskFile.setSyncMLConfig(config)

    def needSave(self):
        """Renvoie True si le fichier de tâches a été modifié depuis la dernière sauvegarde, False sinon.

        Returns :
            bool
        """
        return self.__taskFile.needSave()

    def changedOnDisk(self):
        """Renvoie True si le fichier de tâches a été modifié sur le disque depuis la dernière ouverture, False sinon.

        Returns :
            bool
        """
        return self.__taskFile.changedOnDisk()

    def hasDeletedItems(self):
        """Renvoie True s'il y a des tâches ou des notes supprimées dans le fichier de tâches, False sinon.

        Returns :
            bool
        """
        return bool(
            [task for task in self.__taskFile.tasks() if task.isDeleted()]
            + [note for note in self.__taskFile.notes() if note.isDeleted()]
        )

    def purgeDeletedItems(self):
        """Supprime définitivement les tâches et les notes supprimées du fichier de tâches.

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
            commandLineArgs (list): Liste d'arguments de ligne de commande.

        Returns :
            None"""
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
        """La méthode Ouvre un fichier de tâches.

        Permet d'ouvrir un fichier de tâches.

        Si le fichier a été modifié depuis la dernière sauvegarde,
        l'utilisateur est invité à sauvegarder les modifications.

        Si le fichier existe, il est chargé et verrouillé si nécessaire.

        Si le fichier n'existe pas, une erreur est affichée.

        Args :
            filename (str) : Le nom du fichier à ouvrir. Si None, l'utilisateur est invité à choisir un fichier.
            showerror (callable) : La fonction à utiliser pour afficher les messages d'erreur.
            fileExists (callable) : La fonction à utiliser pour vérifier si le fichier existe.
            breakLock (bool) : Si True, permet de forcer l'ouverture du fichier même s'il est verrouillé.
            lock (bool) : Si True, verrouille le fichier après l'ouverture.

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
        """Méthode permet de fusionner un fichier de tâches avec le fichier courant.

        Args :
            filename (str) : Le nom du fichier à fusionner. Si None, l'utilisateur est invité à choisir un fichier.
            showerror (callable) : La fonction à utiliser pour afficher les messages d'erreur.

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
        """La méthode permet de sauvegarder le fichier de tâches courant.

        Si le fichier n'a pas encore été enregistré,
        l'utilisateur est invité à choisir un nom de fichier.
        Si le fichier a été modifié depuis la dernière sauvegarde,
        elle affiche une boîte de dialogue pour demander à
        l'utilisateur de confirmer la sauvegarde.

        Args :
            showerror (callable) : La fonction.
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
        """La méthode mergeDiskChanges permet de fusionner les
        modifications apportées au fichier de tâches sur le disque avec le fichier courant.

                Si le fichier a été modifié depuis la dernière sauvegarde,
                elle affiche une boîte de dialogue pour demander à l'utilisateur de confirmer la sauvegarde.
        """
        self.__taskFile.mergeDiskChanges()

    def saveas(
        self, filename=None, showerror=wx.MessageBox, fileExists=os.path.exists
    ):
        """La méthode permet de sauvegarder le fichier de tâches courant sous un nouveau nom.

        Sauvegarder le fichier de tâches actuellement ouvert dans l'application sous un nouveau nom de fichier.

        Si aucun nom de fichier n'est spécifié, elle affiche une boîte de dialogue pour
        demander à l'utilisateur de sélectionner un nom de fichier.

        Si le fichier existe déjà, elle affiche une boîte de dialogue pour demander à l'utilisateur
        de confirmer l'écrasement du fichier existant."""
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
        """Crée un nouveau fichier de tâches à partir d'une sélection de tâches.

        Cette méthode est une méthode interne de la classe IOController.
        Elle permet de créer un nouveau fichier de tâches (TaskFile)
        à partir d'une sélection de tâches.

        La méthode prend en paramètre une liste de tâches sélectionnées
        et une classe TaskFileClass qui permet de créer
        une instance de la classe TaskFile.

        La méthode crée un nouveau fichier de tâches vide,
        puis y ajoute les tâches sélectionnées.
        Elle ajoute également les catégories utilisées par les tâches sélectionnées,
        ainsi que les catégories parentes de ces catégories.

        Args :
            tasks (list) : La liste des tâches sélectionnées.
            TaskFileClass (class) : La classe à utiliser pour créer le nouveau fichier de tâches.

        Returns :
            TaskFile : Le nouveau fichier de tâches créé à partir de la sélection de tâches.
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
        """Cette méthode permet de sauvegarder une tâche sous forme de modèle dans le répertoire des modèles."""
        templates = persistence.TemplateList(
            self.__settings.pathToTemplatesDir()
        )
        templates.addTemplate(task)
        templates.save()

    def importTemplate(self, showerror=wx.MessageBox):
        """Cette fonction permet d'importer un modèle de tâche à partir d'un fichier.

        -La première ligne définit la fonction "importTemplate"
        avec un paramètre "showerror" qui est une fonction de boîte de dialogue d'erreur.

        -La deuxième ligne demande à l'utilisateur de sélectionner un fichier à importer
        en utilisant la fonction "__askUserForFile" qui est définie ailleurs dans le code.

        -Si l'utilisateur sélectionne un fichier, la troisième ligne
        crée une instance de la classe "TemplateList" qui est définie ailleurs dans le code
        et qui représente une liste de modèles de tâches.

        -La quatrième ligne essaie de copier le modèle de tâche sélectionné
        dans le répertoire des modèles de tâches en utilisant la méthode "copyTemplate"
        de la classe "TemplateList".

        -Si une exception est levée pendant la copie, la cinquième ligne
        crée un message d'erreur avec le nom du fichier et la raison de l'exception,
        puis affiche la boîte de dialogue d'erreur en utilisant la fonction "showerror" passée en paramètre.
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
        """Cette fonction permet de fermer la tâche en cours d'édition.

        -La première ligne définit la fonction "close" avec un paramètre optionnel "force"
        qui est un booléen indiquant si la fermeture doit être forcée
        sans demander à l'utilisateur de sauvegarder les modifications en cours.

        -La deuxième ligne vérifie si le fichier de tâche en cours d'édition
        a besoin d'être sauvegardé en appelant la méthode "needSave" de l'objet "taskFile"
        qui est défini ailleurs dans le code.

        -Si le fichier a besoin d'être sauvegardé et que la fermeture doit être forcée,
        la troisième ligne sauvegarde le fichier sans demander à l'utilisateur
        en utilisant la méthode "_saveSave" de l'objet "taskFile"
        et une fonction lambda qui ne fait rien (elle vide les arguments).

        -Si le fichier a besoin d'être sauvegardé mais que la fermeture n'est pas forcée,
        la cinquième ligne appelle la méthode "__saveUnsavedChanges" qui
        demande à l'utilisateur s'il veut sauvegarder les modifications en cours.
        Si l'utilisateur choisit de ne pas sauvegarder, la fonction retourne "False"
        et la tâche n'est pas fermée.

        -Si le fichier n'a pas besoin d'être sauvegardé ou
        si l'utilisateur a choisi de sauvegarder les modifications,
        la septième ligne appelle la méthode "__closeUnconditionally" qui ferme la tâche sans condition.

        -Enfin, la dernière ligne retourne "True" pour indiquer que
        la tâche a été fermée avec succès.
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
        """Cette fonction ouvre le fichier filename pour écriture et renvoie si tout s'est bien passé.

        Plusieurs paramètres optionnels :
        Args :
            "title" : qui est le titre de la boîte de dialogue de sauvegarde,
            "fileDialogOpts" : qui sont les options de la boîte de dialogue de sauvegarde,
            "writerClass" : qui est la classe qui écrit les données exportées dans le fichier,
            "viewer" : qui est l'objet qui fournit les données à exporter,
            "selectionOnly" : qui est un booléen indiquant si seules les données sélectionnées doivent être exportées,
            "openfile" : qui est la fonction utilisée pour ouvrir le fichier en écriture,
            "showerror" : qui est la fonction de boîte de dialogue d'erreur,
            "filename" : qui est le nom de fichier à utiliser pour l'export,
            "fileExists" : qui est la fonction utilisée pour vérifier si le fichier existe déjà, et
            "**kwargs" : qui permet de passer des arguments supplémentaires à la méthode d'écriture.

        La deuxième ligne utilise le nom de fichier fourni en paramètre
        ou demande à l'utilisateur de sélectionner un fichier en utilisant la méthode "__askUserForFile"
        qui est définie ailleurs dans le code.

        Si l'utilisateur sélectionne un fichier, la troisième ligne ouvre le fichier en écriture
        en utilisant la méthode "__openFileForWriting" qui est définie ailleurs dans le code.
        Si l'ouverture du fichier échoue, la fonction retourne "False".

        Si le fichier est ouvert avec succès, la quatrième ligne utilise la classe "writerClass"
        pour écrire les données exportées dans le fichier en appelant la méthode "write"
        avec les paramètres "viewer", "self.__settings", "selectionOnly" et "**kwargs".
        La méthode "write" est définie dans la classe "writerClass".

        La cinquième ligne ferme le fichier et affiche un message de confirmation
        en utilisant la méthode "__messageCallback" qui est définie ailleurs dans le code.

        Enfin, la dernière ligne

        Returns :
            bool : retourne "True" si l'export a réussi et "False" sinon.
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
        """Exporte les données de la tâche en cours d'édition au format HTML.

        Les données sont fournies par l'objet "viewer".

        Si "selectionOnly" est True, seules les données sélectionnées sont exportées.

        Si "separateCSS" est True, le CSS est écrit dans un fichier séparé.

        "columns" est une liste de noms de colonnes à exporter.

        Si "filename" est fourni, le fichier est enregistré sous ce nom.
        Sinon, l'utilisateur est invité à sélectionner un nom de fichier.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement.
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
        """Exporte les données de la tâche en cours d'édition au format CSV.

        Les données sont fournies par l'objet "viewer".

        Si "selectionOnly" est True, seules les données sélectionnées sont exportées.

        Si "separateDateAndTimeColumns" est True, les dates et heures sont exportées dans des colonnes séparées.

        "columns" est une liste de noms de colonnes à exporter.

        Si "fileExists" est fourni, il est utilisé pour vérifier si le fichier existe déjà.

        Si "filename" est fourni, le fichier est enregistré sous ce nom.

        Sinon, l'utilisateur est invité à sélectionner un nom de fichier.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement.
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
        """Exporte les données de la tâche en cours d'édition au format iCalendar.

        Les données sont fournies par l'objet "viewer".

        Si "selectionOnly" est True, seules les données sélectionnées sont exportées.

        Si "fileExists" est fourni, il est utilisé pour vérifier si le fichier existe déjà.

        Si "filename" est fourni, le fichier est enregistré sous ce nom.

        Sinon, l'utilisateur est invité à sélectionner un nom de fichier.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement.
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
        """Exporte les données de la tâche en cours d'édition au format Todo.txt.

        Les données sont fournies par l'objet "viewer".

        Si "selectionOnly" est True, seules les données sélectionnées sont exportées.

        Si "fileExists" est fourni, il est utilisé pour vérifier si le fichier existe déjà.

        Si "filename" est fourni, le fichier est enregistré sous ce nom.

        Sinon, l'utilisateur est invité à sélectionner un nom de fichier.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement.
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
        """Importe des données au format CSV dans la tâche en cours d'édition.

        Les données sont lues à partir d'un fichier CSV en utilisant la classe "CSVReader" de l'objet "persistence".

        Les tâches et les catégories sont stockées dans l'objet "self.__taskFile".

        Les paramètres supplémentaires peuvent être passés à la méthode "read" de la classe "CSVReader".
        """
        persistence.CSVReader(
            self.__taskFile.tasks(), self.__taskFile.categories()
        ).read(**kwargs)

    def importTodoTxt(self, filename):
        """Importe des données au format Todo.txt dans la tâche en cours d'édition.

        Les données sont lues à partir d'un fichier Todo.txt
        en utilisant la classe "TodoTxtReader" de l'objet "persistence".

        Les tâches et les catégories sont stockées dans l'objet "self.__taskFile".

        Le nom de fichier doit être fourni en paramètre.
        """
        persistence.TodoTxtReader(
            self.__taskFile.tasks(), self.__taskFile.categories()
        ).read(filename)

    def synchronize(self):
        """Synchronise les données de la tâche en cours d'édition avec un serveur SyncML.

         L'utilisateur est invité à entrer un mot de passe pour l'authentification.

        Si l'authentification échoue, l'utilisateur peut choisir de réinitialiser le mot de passe.

        Les informations de synchronisation sont stockées
        dans l'objet "synchronizer" de la classe "Synchronizer" de l'objet "sync".

        Les résultats de la synchronisation sont affichés
        dans la boîte de dialogue de rapport de synchronisation "self.__syncReport".

        Si la synchronisation réussit, un message de confirmation est affiché.

        Si la synchronisation échoue, une exception "AuthenticationFailure" est levée et
        l'utilisateur peut choisir de réessayer ou d'annuler.
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
        """Retourne le nom de fichier de tâche en cours d'édition.

        Le nom de fichier est stocké dans l'objet "self.__taskFile".
        """
        return self.__taskFile.filename()

    def __syncReport(self, msg):
        """Affiche un message d'erreur dans une boîte de dialogue de rapport de synchronisation.

         Le message est fourni en paramètre "msg".

        La boîte de dialogue est créée avec le titre "Synchronization status"
        et le style "wx.OK | wx.ICON_ERROR".
        """
        wx.MessageBox(
            msg, _("Synchronization status"), style=wx.OK | wx.ICON_ERROR
        )

    def __openFileForWriting(
        self, filename, openfile, showerror, mode="w", encoding="utf-8"
    ):
        """Ouvre un fichier en écriture avec le nom de fichier "filename" en utilisant la fonction "openfile".

        Le mode d'ouverture est "mode" et l'encodage est "encoding".

        Si l'ouverture du fichier échoue, un message d'erreur est créé avec
        le nom de fichier et la raison de l'exception, puis affiché dans une boîte de dialogue d'erreur
        en utilisant la fonction "showerror".

        Les options de la boîte de dialogue d'erreur sont stockées dans l'objet "self.__errorMessageOptions".

        Si l'ouverture du fichier réussit, le fichier ouvert est retourné.

        Si l'ouverture du fichier échoue, la fonction retourne "None".
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
        """Ajoute le nom de fichier "fileName" à la liste des fichiers récents.

        La liste des fichiers récents est stockée dans les paramètres de l'objet "self.__settings".

        Si le fichier est déjà dans la liste, il est déplacé en haut de la liste.

        La liste est ensuite tronquée pour ne pas dépasser
        le nombre maximum de fichiers récents défini dans les paramètres "maxrecentfiles".

        Les fichiers récents sont stockés dans la section "file" des paramètres
        de l'objet "self.__settings" sous la clé "recentfiles".
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
        """Supprime le nom de fichier "fileName" de la liste des fichiers récents.

         La liste des fichiers récents est stockée dans les paramètres de l'objet "self.__settings".

        Si le fichier est dans la liste, il est supprimé de la liste.

        Les fichiers récents sont stockés dans la section "file" des paramètres
        de l'objet "self.__settings" sous la clé "recentfiles".
        """
        recentFiles = self.__settings.getlist("file", "recentfiles")
        if fileName in recentFiles:
            recentFiles.remove(fileName)
            self.__settings.setlist("file", "recentfiles", recentFiles)

    def __askUserForFile(
        self, title, fileDialogOpts, flag=wx.FD_OPEN, fileExists=os.path.exists
    ):
        """Ouvre une boîte de dialogue de sélection de fichier pour demander à l'utilisateur de sélectionner un fichier.

        Le titre de la boîte de dialogue est "title".

        Les options de la boîte de dialogue sont fournies dans le dictionnaire "fileDialogOpts".

        Le drapeau "flag" indique si la boîte de dialogue doit être utilisée pour ouvrir ou enregistrer un fichier.

        La fonction "fileExists" est utilisée pour vérifier si le fichier existe déjà.

        Si le fichier sélectionné pour l'enregistrement n'a pas l'extension par défaut,
        l'extension est ajoutée automatiquement.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement
        en appelant la méthode "__askUserForOverwriteConfirmation".

        Si l'utilisateur confirme l'écrasement, le nom de fichier est retourné.

        Sinon, la fonction retourne "None".
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
        """Affiche une boîte de dialogue de confirmation pour demander à l'utilisateur
        s'il veut écraser le fichier existant "filename".

        Le titre de la boîte de dialogue est "title".

        Les options de la boîte de dialogue sont fournies dans le dictionnaire "fileDialogOpts".

        Si l'utilisateur confirme l'écrasement, la fonction retourne le nom de fichier "filename".

        Si l'utilisateur ne veut pas écraser le fichier,
        la fonction appelle la méthode "__askUserForFile" pour
        demander à l'utilisateur de sélectionner un autre nom de fichier.

        Si l'utilisateur annule, la fonction retourne "None".

        Si le fichier à écraser est utilisé pour l'import ou l'export automatique,
        les fichiers correspondants sont supprimés s'ils existent.
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
        """Demande à l'utilisateur s'il veut sauvegarder les modifications
        en cours avant de fermer la tâche en cours d'édition.

        Si des modifications non sauvegardées sont détectées,
        une boîte de dialogue de confirmation est affichée avec
        le message "You have unsaved changes. Save before closing?".

        Si l'utilisateur choisit de sauvegarder les modifications,
        la fonction appelle la méthode "save".

        Si la sauvegarde échoue, la fonction retourne "False".

        Si l'utilisateur annule, la fonction retourne "False".

        Si l'utilisateur choisit de fermer sans sauvegarder ou si la sauvegarde réussit, la fonction retourne "True".
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
        """Demande à l'utilisateur s'il veut casser le verrouillage du fichier "filename".

        Si le fichier est verrouillé, une boîte de dialogue de confirmation est affichée.

        Si l'utilisateur choisit de casser le verrouillage, la fonction retourne "True".

        Sinon, la fonction retourne "False".
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
        """Demande à l'utilisateur s'il veut ouvrir le fichier "filename" sans verrouillage.

        Si le verrouillage n'est pas pris en charge pour l'emplacement du fichier,
        une boîte de dialogue de confirmation est affichée.

        Si l'utilisateur choisit d'ouvrir le fichier sans verrouillage, la fonction retourne "True".

        Sinon, la fonction retourne "False".
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
        """Ferme la tâche en cours d'édition sans condition.

        Un message de confirmation est affiché avec le nom de fichier de la tâche en cours d'édition.

        L'objet "self.__taskFile" est fermé.

        L'historique des commandes est effacé.

        La mémoire est nettoyée avec la fonction "gc.collect()".
        """
        self.__messageCallback(_("Closed %s") % self.__taskFile.filename())
        self.__taskFile.close()
        patterns.CommandHistory().clear()
        gc.collect()

    def __showSaveMessage(self, savedFile):
        """Affiche un message de confirmation pour indiquer que la tâche en cours d'édition a été sauvegardée avec succès.

        Le message contient le nombre de tâches sauvegardées et le nom de fichier de la tâche en cours d'édition.

        Le message est affiché en appelant la méthode "__messageCallback".
        """
        self.__messageCallback(
            _("Saved %(nrtasks)d tasks to %(filename)s")
            % {
                "nrtasks": len(savedFile.tasks()),
                "filename": savedFile.filename(),
            }
        )

    def __showTooNewErrorMessage(self, filename, showerror):
        """Affiche un message d'erreur pour indiquer que le fichier "filename" a été créé
        par une version plus récente de l'application.

        Le message d'erreur est affiché en utilisant la fonction "showerror" passée en paramètre.

        Les options de la boîte de dialogue d'erreur sont stockées dans l'objet "self.__errorMessageOptions".

        Le nom de l'application est obtenu à partir de l'objet "meta".
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
        """Affiche un message d'erreur générique pour la lecture d'un fichier donné.

        :param filename: Le nom du fichier qui a causé l'erreur
        :type filename: str
        :param showerror: la fonction à utiliser pour afficher l'erreur
        :type showerror: function
        :param showBackups: indique si le gestionnaire de sauvegardes doit être ouvert pour permettre la restauration d'une version antérieure du fichier
        :type showBackups: bool
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
        """Met à jour les chemins par défaut.

        Pour chaque option dans ..., définit l'option du chemin par défaut pour le fichier .tsk à ouvrir.
        """
        for options in [
            self.__tskFileOpenDialogOpts,
            self.__tskFileSaveDialogOpts,
            self.__csvFileDialogOpts,
            self.__icsFileDialogOpts,
            self.__htmlFileDialogOpts,
        ]:
            options["default_path"] = os.path.dirname(filename)
