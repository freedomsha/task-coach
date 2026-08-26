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

# from builtins import object
import codecs
import gc
import logging
import os
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from taskcoachlib import meta, persistence, patterns, operating_system
from taskcoachlib.i18n import _

# from taskcoachlib.thirdparty import lockfile  # TODO : obsolète ?
import lockfile
from taskcoachlib.widgetstk.passwordtk import GetPassword
from taskcoachlib.workarounds import ExceptionAsUnicode
from taskcoachlib.guitk.dialog.backupmanagertk import (
    BackupManagerDialog,
)  # Remplacé par une simulation tkinter

try:
    from taskcoachlib.syncml import sync
except ImportError:  # pragma: no cover
    # Unsupported platform.
    pass

log = logging.getLogger(__name__)


# Simulation de BackupManagerDialog avec tkinter
# Convertir gui.dialog.backupmanager.BackupManagerDialog pour tkinter
# puis supprimer cette simulation.
# class BackupManagerDialog(simpledialog.Dialog):
#     def __init__(self, parent, settings, filename):
#         self.settings = settings
#         self.filename = filename
#         self.restored_filename = None
#         super().__init__(parent, "Backup Manager")
#
#     def body(self, master):
#         tk.Label(master, text="Simulated Backup Manager Dialog").pack()
#         return master
#
#     def apply(self):
#         # Cette méthode est appelée si l'utilisateur clique sur OK
#         # Ici, nous simulons la restauration d'un fichier.
#         self.restored_filename = f"{self.filename}.restored"


class IOController(object):
    """IOController is responsible for opening, closing, loading,
    saving, and exporting files. It also presents the necessary dialogs
    to let the user specify what file to load/save/etc.

    IOController est responsable de l’ouverture, de la fermeture, du chargement
    de l’enregistrement et de l’exportation des fichiers.
    Il présente également les boîtes de dialogue nécessaires
    pour permettre à l'utilisateur de spécifier quel fichier charger/enregistrer/etc.
    """

    def __init__(
        self, parent_window, taskFile, messageCallback, settings, splash=None
    ):
        # log.info("Initialisation de IOController.")
        super().__init__()
        # Le fichier de tâches
        self.__taskFile = taskFile
        # Boîte de dialogue pour les messages.
        self.__messageCallback = messageCallback
        self.__settings = settings
        self.__parent_window = parent_window  # La fenêtre principale tkinter
        # self.__splash = splash  # Nous n'avons plus besoin de l'écran de démarrage `splash` de wxPython.
        self.__splash = None
        defaultPath = os.path.expanduser("~")
        self.filename_changed_callbacks = []
        self.dirty_changed_callbacks = []

        self.__tskFileSaveDialogOpts = {
            "defaultextension": ".tsk",
            "filetypes": [
                (_("%s files") % meta.name, "*.tsk"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__tskFileOpenDialogOpts = {
            "defaultextension": ".tsk",
            "filetypes": [
                (_("%s files") % meta.name, "*.tsk"),
                (_("Backup files"), "*.tsk.bak"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__icsFileDialogOpts = {
            "defaultextension": ".ics",
            "filetypes": [
                (_("iCalendar files"), "*.ics"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__htmlFileDialogOpts = {
            "defaultextension": ".html",
            "filetypes": [
                (_("HTML files"), "*.html"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__csvFileDialogOpts = {
            "defaultextension": ".csv",
            "filetypes": [
                (_("CSV files"), "*.csv"),
                (_("Text files"), "*.txt"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__todotxtFileDialogOpts = {
            "defaultextension": ".txt",
            "filetypes": [
                (_("Todo.txt files"), "*.txt"),
                (_("All files"), "*.*"),
            ],
            "initialdir": defaultPath,
        }
        self.__errorMessageOptions = dict(
            caption=_("%s file error") % meta.name  # , style=ICON_ERROR
        )

    def syncMLConfig(self):
        """
        Renvoie la configuration de synchronisation du fichier de tâches.

        Returns :
            (dict) : La configuration de synchronisation du fichier de tâches.
        """
        return self.__taskFile.syncMLConfig()

    def setSyncMLConfig(self, config):
        """
        Définit la configuration de synchronisation du fichier de tâches.

        Args :
            config (dict) : La nouvelle configuration de synchronisation.

        Returns :
            None
        """
        self.__taskFile.setSyncMLConfig(config)

    def needSave(self):
        """
        Renvoie si le fichier de tâches a besoin d'être sauvegardé.

        Returns :
            (bool) : True si le fichier de tâches a été modifié depuis la dernière sauvegarde, False sinon.
        """
        return self.__taskFile.needSave()

    def changedOnDisk(self):
        """
        Renvoie si le fichier de tâches a été modifié sur le disque depuis la dernière ouverture.

        Returns :
            (bool) : True si le fichier de tâches a été modifié sur le disque depuis la dernière ouverture, False sinon.
        """
        return self.__taskFile.changedOnDisk()

    def hasDeletedItems(self):
        """
        Renvoie s'il y a des tâches ou des notes supprimées dans le fichier de tâches.

        Returns :
            (bool) : True si des tâches ou des notes sont supprimées du fichier de tâches, sinon False.
        """
        return bool(
            [task for task in self.__taskFile.tasks() if task.isDeleted()]
            + [note for note in self.__taskFile.notes() if note.isDeleted()]
        )

    def purgeDeletedItems(self):
        """
        Supprime définitivement les tâches et les notes supprimées du fichier de tâches.

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
        """
        Ouvre le fichier spécifié en ligne de commande ou le dernier fichier
        ouvert par l'utilisateur, ou aucun fichier du tout.

        Args :
            commandLineArgs (list) : Liste d'arguments de ligne de commande.

        Returns :
            None
        """
        # commandLineArgs[0] est le premier argument de la ligne de commande,
        # qui est une chaîne de caractères encodée en bytes.
        # La méthode decode() est appelée sur cette chaîne de caractères
        # pour la convertir en une chaîne de caractères Unicode.
        # La méthode decode() prend en paramètre l'encodage
        # utilisé pour encoder la chaîne de caractères en bytes.
        # sys.getfilesystemencoding() retourne l'encodage utilisé
        # par le système de fichiers. Cela permet de s'assurer que
        # la chaîne de caractères est correctement décodée,
        # même si l'encodage par défaut de l'application
        # n'est pas le même que celui du système de fichiers.
        # En résumé, cette commande permet de
        # convertir le premier argument de la ligne de commande
        # en une chaîne de caractères Unicode,
        # en utilisant l'encodage du système de fichiers.
        filename = None
        log.info(
            "IOController.openAfterStart : Ouvre le fichier spécifié en ligne de commande"
            " ou le dernier fichier ouvert par l'utilisateur, ou aucun fichier du tout."
        )
        if commandLineArgs:
            # Si un argument de ligne de commande est présent, on considère
            # que c'est le nom du fichier à ouvrir.
            try:
                filename = commandLineArgs[0]
                if isinstance(filename, bytes):
                    filename = filename.decode(sys.getfilesystemencoding())
                log.info(
                    f"IOController.openAfterStart : Enregistre {filename} comme nom de fichier."
                )
            except Exception as e:
                messagebox.showerror(
                    "File Open Error", f"Cannot open file due to: {e}"
                )
                return
        else:
            # Sinon, on récupère le nom du dernier fichier ouvert par
            # l'utilisateur à partir des paramètres de configuration.
            filename = self.__settings.get("file", "lastfile")
            log.info(
                f"IOController.openAfterStart : Récupère le dernier fichier ouvert {filename} comme nom de fichier."
            )
        if filename:
            # Use `after` to ensure the main window is ready
            # On utilise CallAfter pour s'assurer que la fenêtre principale
            # est ouverte avant d'ouvrir le fichier.
            log.info(
                f"IOController.openAfterStart : Appelle after avec la méthode self.open et filename={filename}"
            )
            self.__parent_window.after(
                10, self.open, filename
            )  # TODO : est-ce sur self.__parent_window ?
            log.info(
                f"IOController.openAfterStart : Appelle after réussi. Fichier {filename} ouvert. Terminé !"
            )

    def open(
        self,
        filename=None,
        showerror=messagebox.showerror,
        fileExists=os.path.exists,
        breakLock=False,
        lock=True,
    ):
        """
        La méthode Ouvre un fichier de tâches.

        Permet d'ouvrir un fichier de tâches.

        Si le fichier a été modifié depuis la dernière sauvegarde,
        l'utilisateur est invité à sauvegarder les modifications.

        Si le fichier existe, il est chargé et verrouillé si nécessaire.

        Si le fichier n'existe pas, une erreur est affichée.

        Args :
            filename (str | None) : Le nom du fichier à ouvrir. Si None, l'utilisateur est invité à choisir un fichier.
            showerror (callable) : La fonction à utiliser pour afficher les messages d'erreur.
            fileExists (callable) : La fonction à utiliser pour vérifier si le fichier existe.
            breakLock (bool) : Si True, permet de forcer l'ouverture du fichier même s'il est verrouillé.
            lock (bool) : Si True, verrouille le fichier après l'ouverture.

        Returns :
            None
        """
        log.info(
            f"IOController.open : Ouverture du fichier {filename}, fileExists={fileExists}, breakLock={breakLock}, lock={lock}"
        )
        if self.__taskFile.needSave():
            log.info(
                f"IOController.open : Le fichier de tâche {self.__taskFile} a besoin d'être sauvegardé."
            )
            if not self.__saveUnsavedChanges():
                return
        if not filename or filename == "/":
            filename = self.__askUserForFile(
                _("Open"), self.__tskFileOpenDialogOpts, flag="open"
            )
            log.info(
                f"IOController.open : L'utilisateur a choisi d'ouvrir {filename}."
            )
        if not filename:
            log.warning("IOController.open : Aucun fichier à ouvrir !")
            return
        self.__updateDefaultPath(filename)
        # TODO : code à vérifier la complexité
        # Si le fichier existe d'après fileExists
        if fileExists(filename):
            # Fermer la tâche en cours d'édition sans condition.
            self.__closeUnconditionally()
            # Ajoute le nom de fichier "fileName" à la liste des fichiers récents.
            self.__addRecentFile(filename)

            try:
                # Si l'écran de démarrage est configuré et actif
                if self.__splash:
                    # Le fermer.
                    self.__splash.destroy()  # Remplacer par la méthode de destruction de la fenêtre tkinter
                # Chargez le fichier de tâche à partir du disque.
                self.__taskFile.load(filename, lock=lock, breakLock=breakLock)
            # Cas d'erreurs obsolètes !
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
            showerror(_("%s file error") % meta.name, errorMessage)
            # Supprime le nom de fichier "fileName" de la liste des fichiers récents.
            self.__removeRecentFile(filename)

    def merge(self, filename=None, showerror=messagebox.showerror):
        """
        Méthode permet de fusionner un fichier de tâches avec le fichier courant.

        Args :
            filename (str) : Le nom du fichier à fusionner. Si None, l'utilisateur est invité à choisir un fichier.
            showerror (callable) : La fonction à utiliser pour afficher les messages d'erreur.

        Returns :
            None
        """
        if not filename:
            filename = self.__askUserForFile(
                _("Merge"), self.__tskFileOpenDialogOpts, flag="open"
            )
        if filename:
            try:
                self.__taskFile.merge(filename)
            except lockfile.LockTimeout:
                showerror(
                    _("%s file error") % meta.name,
                    _("Cannot open %(filename)s\nbecause it is locked.")
                    % dict(filename=filename),
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

    def save(self, showerror=messagebox.showerror):
        """
        La méthode permet de sauvegarder le fichier de tâches courant.

        Si le fichier n'a pas encore été enregistré,
        l'utilisateur est invité à choisir un nom de fichier.
        Si le fichier a été modifié depuis la dernière sauvegarde,
        elle affiche une boîte de dialogue pour demander à
        l'utilisateur de confirmer la sauvegarde.

        Args :
            showerror (callable) : La fonction.
        """
        log.info(
            "IOController.save tente de sauvegarder le fichier de tâches courant."
        )
        # Si le nom de fichier existe :
        if self.__taskFile.filename():
            # Renvoie True si l'enregistrement du fichier est ok :
            if self._saveSave(self.__taskFile, showerror):
                log.info(
                    f"IOController.save a sauvegardé le fichier de tâches courant {self.__taskFile} sous son nom {self.__taskFile.filename()}."
                )
                return True
            else:
                log.warning(
                    f"IOController.save sauvegarde le fichier de tâches courant {self.__taskFile} sous un nouveau nom."
                )
                # Sinon enregistre le fichier sous un nouveau nom.
                return self.saveas(showerror=showerror)
        # Si le fichier n'existe pas, vérifier si le fichier de tâche est vide.
        elif not self.__taskFile.isEmpty():
            # S'il ne l'est pas, lancer l'enregistrement du fichier courant sous un nouveau nom.
            log.warning(
                f"IOController.save : Le fichier n'existe pas, sauvegarder {self.__taskFile} sous un nouveau nom."
            )
            return self.saveas(showerror=showerror)
        else:
            # Sinon Retourne False Si le fichier courant self.__taskFile est vide.
            log.warning(
                f"IOController.save : Le fichier {self.__taskFile} est vide."
            )
            return False

    def mergeDiskChanges(self):
        """
        La méthode mergeDiskChanges permet de fusionner les modifications apportées au fichier de tâches
        sur le disque avec le fichier courant.

        Si le fichier a été modifié depuis la dernière sauvegarde,
        elle affiche une boîte de dialogue pour demander à l'utilisateur de confirmer la sauvegarde.
        """
        self.__taskFile.mergeDiskChanges()

    def saveas(
        self,
        filename=None,
        showerror=messagebox.showerror,
        fileExists=os.path.exists,
    ):
        """
        La méthode permet de sauvegarder le fichier de tâches courant sous un nouveau nom.

        Sauvegarder le fichier de tâches actuellement ouvert dans l'application sous un nouveau nom de fichier.

        Si aucun nom de fichier n'est spécifié, elle affiche une boîte de dialogue pour
        demander à l'utilisateur de sélectionner un nom de fichier.

        Si le fichier existe déjà, elle affiche une boîte de dialogue pour demander à l'utilisateur
        de confirmer l'écrasement du fichier existant.
        """
        # Si filename n'existe pas :
        if not filename:
            # Ouvrir une boîte de dialogue de sélection de fichier pour
            # demander à l'utilisateur de sélectionner un fichier :
            filename = self.__askUserForFile(
                _("Save as"),
                self.__tskFileSaveDialogOpts,
                flag="save",
                fileExists=fileExists,
            )
            if not filename:
                return False  # User didn't enter a filename, cancel save
        if self._saveSave(self.__taskFile, showerror, filename):
            return True
        else:
            return self.saveas(showerror=showerror)

    def saveselection(
        self,
        tasks,
        filename=None,
        showerror=messagebox.showerror,
        TaskFileClass=persistence.TaskFile,
        fileExists=os.path.exists,
    ):
        """La méthode permet de sauvegarder une sélection de tâches dans un nouveau fichier."""
        if not filename:
            filename = self.__askUserForFile(
                _("Save selection"),
                self.__tskFileSaveDialogOpts,
                flag="save",
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
            )

    def _createSelectionFile(self, tasks, TaskFileClass):
        """
        Crée un nouveau fichier de tâches à partir d'une sélection de tâches.

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
        # Ajoute les tâches sélectionnées :
        selectionFile.tasks().extend(tasks)
        # Inclut les catégories utilisées par les tâches sélectionnées :
        allCategories = set()
        for task in tasks:
            allCategories.update(task.categories())
        # Inclut également les parents des catégories utilisées, récursivement :
        for category in allCategories.copy():
            allCategories.update(category.ancestors())
        selectionFile.categories().extend(allCategories)
        return selectionFile

    def _saveSave(self, taskFile, showerror, filename=None):
        """Enregistrez le fichier et affichez un message d'erreur si l'enregistrement échoue."""
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
            showerror(_("%s file error") % meta.name, errorMessage)
            return False
        except (OSError, IOError, lockfile.LockFailed) as reason:
            errorMessage = _("Cannot save %s\n%s") % (
                filename,
                ExceptionAsUnicode(reason),
            )
            showerror(_("%s file error") % meta.name, errorMessage)
            return False

    def saveastemplate(self, task):
        """Cette méthode permet de sauvegarder une tâche sous forme de modèle dans le répertoire des modèles."""
        templates = persistence.TemplateList(
            self.__settings.pathToTemplatesDir()
        )
        templates.addTemplate(task)
        templates.save()

    def importTemplate(self, showerror=messagebox.showerror):
        """
        Cette fonction permet d'importer un modèle de tâche à partir d'un fichier.

        Voici une explication ligne par ligne :
            - La première ligne définit la fonction "importTemplate"
            avec un paramètre "showerror" qui est une fonction de boîte de dialogue d'erreur.

            - La deuxième ligne demande à l'utilisateur de sélectionner un fichier à importer
            en utilisant la fonction "__askUserForFile" qui est définie ailleurs dans le code.

            - Si l'utilisateur sélectionne un fichier, la troisième ligne
            crée une instance de la classe "TemplateList" qui est définie ailleurs dans le code
            et qui représente une liste de modèles de tâches.

            - La quatrième ligne essaie de copier le modèle de tâche sélectionné
            dans le répertoire des modèles de tâches en utilisant la méthode "copyTemplate"
            de la classe "TemplateList".

            - Si une exception est levée pendant la copie, la cinquième ligne
            crée un message d'erreur avec le nom du fichier et la raison de l'exception,
            puis affiche la boîte de dialogue d'erreur en utilisant la fonction "showerror" passée en paramètre.
        """
        filename = self.__askUserForFile(
            _("Import template"),
            fileDialogOpts={
                "defaultextension": ".tsktmpl",
                "filetypes": [
                    (_("%s template files") % meta.name, "*.tsktmpl")
                ],
            },
            flag="open",
        )
        if filename:
            templates = persistence.TemplateList(
                self.__settings.pathToTemplatesDir()
            )
            try:
                templates.copyTemplate(filename)
            except Exception as reason:
                errorMessage = _("Cannot import template %s\n%s") % (
                    filename,
                    ExceptionAsUnicode(reason),
                )
                showerror(_("%s file error") % meta.name, errorMessage)

    def close(self, force: bool = False):
        """Cette fonction permet de fermer la tâche en cours d'édition.

        Voici une explication ligne par ligne :
            - La première ligne définit la fonction "Close" avec un paramètre optionnel "force"
              qui est un booléen indiquant si la fermeture doit être forcée
              sans demander à l'utilisateur de sauvegarder les modifications en cours.

            - La deuxième ligne vérifie si le fichier de tâche en cours d'édition
              a besoin d'être sauvegardé en appelant la méthode "needSave" de l'objet "taskFile"
              qui est défini ailleurs dans le code.

            - Si le fichier a besoin d'être sauvegardé et que la fermeture doit être forcée,
              la troisième ligne sauvegarde le fichier sans demander à l'utilisateur
              en utilisant la méthode "_saveSave" de l'objet "taskFile"
              et une fonction lambda qui ne fait rien (elle vide les arguments).

            - Si le fichier a besoin d'être sauvegardé mais que la fermeture n'est pas forcée,
              la cinquième ligne appelle la méthode "__saveUnsavedChanges" qui
              demande à l'utilisateur s'il veut sauvegarder les modifications en cours.
              Si l'utilisateur choisit de ne pas sauvegarder, la fonction retourne "False"
              et la tâche n'est pas fermée.

            - Si le fichier n'a pas besoin d'être sauvegardé ou
              si l'utilisateur a choisi de sauvegarder les modifications,
              la septième ligne appelle la méthode "__closeUnconditionally" qui ferme la tâche sans condition.

            - Enfin, la dernière ligne retourne "True" pour indiquer que
              la tâche a été fermée avec succès.
        """
        if self.__taskFile.needSave():
            if force:
                # No user interaction, since we're forced to Close right Now.
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
        showerror=messagebox.showerror,
        filename=None,
        fileExists=os.path.exists,
        **kwargs,
    ):
        """Cette fonction ouvre le fichier filename pour écriture et renvoie si tout s'est bien passé.

        Plusieurs paramètres optionnels :
        Args :
            "title" : qui est le titre de la boîte de dialogue de sauvegarde,
            "fileDialogOpts" : qui sont les options de la boîte de dialogue de sauvegarde,
            "writerClass" : qui est la classe qui écrit les données exportées dans le fichier,
            "viewer" : qui est l'objet qui fournit les données à exporter,
            "selectionOnly" : qui est un booléen indiquant si seules les données sélectionnées doivent être exportées,
            "openfile" : (optionnel) qui est la fonction utilisée pour ouvrir le fichier en écriture,
            "showerror" : (optionnel) qui est la fonction de boîte de dialogue d'erreur,
            "filename" : qui est le nom de fichier à utiliser pour l'export,
            "fileExists" : (optionnel) qui est la fonction utilisée pour vérifier si le fichier existe déjà, et
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

        Enfin, la dernière ligne retourne "False" si le nom de fichier
        n'existe toujours pas après la boîte de dialogue.

        Returns :
            (bool) : retourne "True" si l'export a réussi et "False" sinon.
        """
        log.info(
            "IOController.export ouvre le fichier filename pour écriture et renvoie si tout s'est bien passé."
        )
        # filename est filename s'il existe sinon ouvre une boîte de dialogue.
        filename = filename or self.__askUserForFile(
            title, fileDialogOpts, flag="save", fileExists=fileExists
        )
        # Si filename existe :
        if filename:
            # revoir la méthode avec with ! :
            # l'ouvre avec open pour écrire dedans ! Attention mode w !
            fd = self.__openFileForWriting(filename, openfile, showerror)
            if fd is None:
                return False
            # Sinon, utiliser writerClass().write() pour écrire les données exportées dans le fichier :
            count = writerClass(fd, filename).write(
                viewer, self.__settings, selectionOnly, **kwargs
            )
            # Fermer le fichier :
            fd.close()
            # Afficher un message de confirmation :
            self.__messageCallback(
                _("Exported %(count)d items to " "%(filename)s")
                % dict(count=count, filename=filename)
            )
            return True
        else:
            log.warning("IOController.export n'a pas enregistré de fichier.")
            return False

    def exportAsHTML(
        self,
        viewer,
        selectionOnly=False,
        separateCSS=False,
        columns=None,
        openfile=codecs.open,
        showerror=messagebox.showerror,
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
        r"""Importe des données au format Todo.txt dans la tâche en cours d'édition.

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
            # TODO : tkinter n'a pas de GetPassword, il faudrait le coder
            # la version wxPython est dans widgets.password.GetPassword()
            # la version tkinter est dans widgetstk.password.GetPassword()
            password = simpledialog.askstring(
                "Task Coach", "SyncML Password", show="*"
            )
            if not password:
                break
            synchronizer = sync.Synchronizer(
                self.__syncReport, self.__taskFile, password
            )
            try:
                synchronizer.synchronize()
            except sync.AuthenticationFailure:
                doReset = True
                messagebox.showerror(
                    "Synchronization status",
                    "Authentication failed. Would you like to reset?",
                )
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

    def isDirty(self):
        return False

    def stop(self):
        logging.info("IOController : Arrêt.")

    def clear(self, save):
        """

        Args:
            save:

        Returns:

        """
        logging.info(f"MockIOController: Effacement (sauvegarde: {save}).")

    def __syncReport(self, msg):
        r"""Affiche un message d'erreur dans une boîte de dialogue de rapport de synchronisation.

         Le message est fourni en paramètre "msg".

        La boîte de dialogue est créée avec le titre "Synchronization status"
        et le style "wx.OK | wx.ICON_ERROR".
        """
        messagebox.showerror(_("Synchronization status"), msg)

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
            log.info(
                f"IOController.__openFileForWriting : Ouvre {filename} avec {openfile} en mode={mode} et encoding={encoding}."
            )
            return openfile(filename, mode, encoding)
        except IOError as reason:
            errorMessage = _("Cannot open %s\n%s") % (
                filename,
                ExceptionAsUnicode(reason),
            )
            messagebox.showerror(_("%s file error") % meta.name, errorMessage)
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
        self, title, fileDialogOpts, flag, fileExists=os.path.exists
    ):
        """
        Ouvre une boîte de dialogue de sélection de fichier pour demander à l'utilisateur de sélectionner un fichier.

        Args :
            title : Le titre de la boîte de dialogue est "title".
            fileDialogOpts : Les options de la boîte de dialogue sont fournies dans le dictionnaire "fileDialogOpts".
            flag : Le drapeau "flag" indique si la boîte de dialogue doit être utilisée pour ouvrir ou enregistrer un fichier.
            fileExists : La fonction "fileExists" est utilisée pour vérifier si le fichier existe déjà.

        Si le fichier sélectionné pour l'enregistrement n'a pas l'extension par défaut,
        l'extension est ajoutée automatiquement.

        Si le fichier existe déjà, l'utilisateur est invité à confirmer l'écrasement
        en appelant la méthode "__askUserForOverwriteConfirmation".

        Returns :
            Si l'utilisateur confirme l'écrasement, le nom de fichier est retourné.
            Sinon, la fonction retourne "None".
        """
        filename = None
        options = {
            "title": title,
            # "initialdir": fileDialogOpts["initialdir"],
            "filetypes": fileDialogOpts["filetypes"],
        }
        if flag == "open":
            filename = filedialog.askopenfilename(**options)
        elif flag == "save":
            filename = filedialog.asksaveasfilename(**options)
            if filename:
                extension = fileDialogOpts["defaultextension"]
                if not filename.endswith(extension):
                    filename += extension
        return filename

    def __askUserForOverwriteConfirmation(
        self, filename, title, fileDialogOpts
    ):
        """
        Affiche une boîte de dialogue de confirmation pour demander à l'utilisateur
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
        result = messagebox.askyesnocancel(
            title,
            _("A file named %s already exists.\nDo you want to replace it?")
            % filename,
        )
        if result is True:  # YES
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
        elif result is False:  # NO
            return self.__askUserForFile(title, fileDialogOpts, flag="save")
        else:  # CANCEL or None
            return None

    def __saveUnsavedChanges(self):
        """
        Demande à l'utilisateur s'il veut sauvegarder les modifications
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
        result = messagebox.askyesnocancel(
            _("%s: save changes?") % meta.name,
            _("You have unsaved changes.\nSave before closing?"),
        )
        # if result is True:  # YES
        if result:  # YES
            if not self.save():
                return False
        elif result is None:  # CANCEL
            return False
        return True

    def __askBreakLock(self, filename):
        """
        Demande à l'utilisateur s'il veut casser le verrouillage du fichier "filename".

        Si le fichier est verrouillé, une boîte de dialogue de confirmation est affichée.

        Si l'utilisateur choisit de casser le verrouillage, la fonction retourne "True".

        Sinon, la fonction retourne "False".
        """
        log.info(
            f"IOController.__askBreakLock demande à l'utilisateur s'il veut casser le verrouillage du fichier {filename}."
        )
        result = messagebox.askyesno(
            _("%s: file locked") % meta.name,
            _("""Cannot open %s because it is locked.

                                 This means either that another instance of TaskCoach
                                 is running and has this file opened, or that a previous
                                 instance of Task Coach crashed. If no other instance is
                                 running, you can safely break the lock.

                                 Break the lock?""") % filename,
        )
        return result

    def __askOpenUnlocked(self, filename):
        """
        Demander à l'utilisateur s'il veut ouvrir le fichier "filename" sans verrouillage.

        Si le verrouillage n'est pas pris en charge pour l'emplacement du fichier,
        une boîte de dialogue de confirmation est affichée.

        Si l'utilisateur choisit d'ouvrir le fichier sans verrouillage, la fonction retourne "True".

        Sinon, la fonction retourne "False".
        """
        log.warning("IOController.__askOpenUnlocked appelé !")
        result = messagebox.askyesno(
            _("%s: file locked") % meta.name,
            _(
                "Cannot acquire a lock because locking is not "
                "supported\non the location of %s.\n"
                "Open %s unlocked?"
            )
            % (filename, filename),
        )
        return result

    def __closeUnconditionally(self):
        """
        Fermer la tâche en cours d'édition sans condition.

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
        """
        Affiche un message de confirmation pour indiquer que la tâche en cours d'édition a été sauvegardée avec succès.

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
        """
        Afficher un message d'erreur pour indiquer que le fichier "filename" a été créé
        par une version plus récente de l'application.

        Le message d'erreur est affiché en utilisant la fonction "showerror" passée en paramètre.

        Les options de la boîte de dialogue d'erreur sont stockées dans l'objet "self.__errorMessageOptions".

        Le nom de l'application est obtenu à partir de l'objet "meta".
        """
        showerror(
            _("%s file error") % meta.name,
            _(
                "Cannot open %(filename)s\n"
                "because it was created by a newer version of %(name)s.\n"
                "Please upgrade %(name)s."
            )
            % dict(filename=filename, name=meta.name),
        )

    def __showGenericErrorMessage(
        self, filename, showerror, showBackups=False
    ):
        """
        Affiche un message d'erreur générique pour la lecture d'un fichier donné.

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
                "The backup manager will Now open to allow you to restore\nan older version of this file."
            )
        showerror(_("%s file error") % meta.name, message)

        if showBackups and man.hasBackups(filename):
            # Utilisation de la classe tkinter
            dlg = BackupManagerDialog(
                self.__parent_window, self.__settings, filename
            )
            if dlg.restoredFilename():
                self.__parent_window.after(10, self.open, dlg.restoredFilename)

    def __updateDefaultPath(self, filename):
        """
        Met à jour les chemins par défaut.

        Pour chaque option dans ...,
        définit l'option du chemin par défaut pour le fichier .tsk à ouvrir.
        """
        new_path = os.path.dirname(filename)
        for options in [
            self.__tskFileOpenDialogOpts,
            self.__tskFileSaveDialogOpts,
            self.__csvFileDialogOpts,
            self.__icsFileDialogOpts,
            self.__htmlFileDialogOpts,
        ]:
            options["initialdir"] = new_path
            options["default_path"] = new_path
