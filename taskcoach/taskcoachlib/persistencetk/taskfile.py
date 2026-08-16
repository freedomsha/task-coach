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

Ce fichier gère le modèle de données central :
les tâches, efforts, catégories, notes, etc.
Il est également responsable de la gestion des événements, de la persistence,
de la synchronisation, et de la sécurité des écritures.

Donc c'est un fichier critique à bien logger :
tout plantage ici impacte la sauvegarde, le chargement, les notifs, etc.

Remarques :
- Ce fichier est une version ciblée pour Tkinter : onFileChanged utilise
  self.__parent.after_idle(...). L'objet parent doit donc être la racine Tk
  (ou un widget) passé à TaskFile lors de l'initialisation.
- L'en
# Le fichier taskfile.py que vous avez fourni gère le modèle de données et la persistance de l'application, et ne contient pas directement d'éléments d'interface utilisateur de wxPython. La conversion de wxPython à tkinter affectera principalement les fichiers qui gèrent l'interface graphique (GUI) elle-même.
#
# Cependant, il y a une ligne dans votre fichier qui utilise wx:
#
#     wx.CallAfter(pub.sendMessage, "taskfile.changed", taskFile=self)
#
# Cette ligne doit être remplacée par un équivalent tkinter pour fonctionner correctement. L'objectif de wx.CallAfter est de planifier une fonction à exécuter dans le thread principal de l'interface utilisateur. Avec tkinter, vous pouvez utiliser la méthode after d'un widget (comme la fenêtre racine) pour accomplir la même chose.
#
# Voici le fichier taskfile.py converti, avec la modification nécessaire pour tkinter et une explication des changements. Les autres parties du code, qui traitent du modèle de données, de la gestion des fichiers et de la logique métier, n'ont pas besoin d'être modifiées.

# J'ai remplacé l'import wx par tkinter. Dans la méthode onFileChanged, j'ai commenté la ligne wx.CallAfter et ajouté une explication sur la manière de la remplacer par tkinter.Tk.after. La méthode after de tkinter est l'équivalent direct de wx.CallAfter, car elle permet de planifier l'exécution d'une fonction dans la boucle d'événements principale de tkinter de manière sécurisée pour le threading.
#
# Pour que cette partie fonctionne, vous devrez vous assurer que la fenêtre principale (le "root" de Tkinter) est accessible depuis cet objet, soit en la passant lors de l'initialisation, soit en utilisant une variable globale. Pour le moment, j'ai laissé un commentaire pour vous guider. J'ai aussi légèrement modifié la méthode write dans la classe SafeWriteFile pour m'assurer que le contenu est encodé correctement si le fichier est ouvert en mode binaire ('wb').
"""

import fasteners
import lockfile
import logging
import os
import tempfile
import uuid
from io import TextIOWrapper

# import wx  # Remplacé par tkinter pour la conversion
from pubsub import pub

# Ajout de l'import tkinter
import tkinter as tk

from taskcoachlib.domain.task.task import GUI_NAME
from taskcoachlib.persistence import xml

# xml = mock
from taskcoachlib import patterns, operating_system
from taskcoachlib.domain import base, task, category, note, effort, attachment
from taskcoachlib.syncml.config import createDefaultSyncConfig
from taskcoachlib.thirdparty.guid import generate

# from taskcoachlib.thirdparty import lockfile
from taskcoachlib.changes import ChangeMonitor, ChangeSynchronizer
from taskcoachlib.filesystem import (
    FilesystemNotifier,
    FilesystemPollerNotifier,
)

log = logging.getLogger(__name__)


def _isCloud(path):
    """
    Vérifiez si un chemin donné se trouve dans un répertoire synchronisé avec le cloud.

    Args :
        path (str) : Le chemin du fichier à vérifier.

    Returns :
        (bool) : Vrai si le chemin se trouve dans un répertoire synchronisé avec le cloud, sinon False.
    """
    path = os.path.abspath(path)
    while True:
        for name in [".dropbox.cache", ".csync_journal.db"]:
            if os.path.exists(os.path.join(path, name)):
                return True
        path, name = os.path.split(path)
        if name == "":
            return False


class TaskCoachFilesystemNotifier(FilesystemNotifier):
    """
    Une classe de notification pour gérer les modifications de fichiers pour Task Coach.

    Basé sur FilesystemNotifier qui charge le notificateur selon le système (linux->inotify, win->win32, mac->notifeur) ou FileSystemPollerNotifier.
    """

    def __init__(self, taskFile):
        """
        Initialiser le notificateur avec une instance de TaskFile.

        Initialise un notificateur de changement de fichier spécifique à Task Coach,
        en liant un objet TaskFile à surveiller pour détecter les modifications sur le disque.

        Args :
            taskFile (TaskFile) : l'instance de TaskFile à notifier.
        """
        self.__taskFile = taskFile
        root = tk.Tk()
        # super(TaskCoachFilesystemNotifier, self).__init__()
        super().__init__(main_window=root)

    def onFileChanged(self):
        """
        Gérez les modifications de fichiers en notifiant l’instance TaskFile associée.
        """
        self.__taskFile.onFileChanged()
        log.info(
            "TaskCoachFileSystemNotifier.onFileChanged : Modification détectée sur le fichier '%s'",
            self.__taskFile,
        )


class TaskCoachFilesystemPollerNotifier(FilesystemPollerNotifier):
    """
    Une classe de notification d'interrogation pour gérer les modifications de fichiers pour Task Coach.
    """

    def __init__(self, taskFile):
        """
        Initialiser le notificateur d'interrogation avec une instance de TaskFile.

        Initialise un notificateur de changement de fichier spécifique à Task Coach,
        en liant un objet TaskFile à surveiller pour détecter les modifications sur disque.

        Args :
            taskFile (TaskFile) : L'instance de TaskFile à notifier.
        """
        self.__taskFile = taskFile
        # super(TaskCoachFilesystemPollerNotifier, self).__init__()
        super().__init__()

    def onFileChanged(self):
        """
        Gérez les modifications de fichiers en notifiant l’instance TaskFile associée.
        """
        self.__taskFile.onFileChanged()
        log.info(
            "TaskCoachFileSystemPollerNotifier.onFileChanged : Modification détectée sur le fichier '%s'",
            self.__taskFile,
        )


class SafeWriteFile(object):
    # class SafeWriteFile(metaclass=open):  # Pourquoi pas ?
    """
    Safe write helper that writes to a temporary file (on the same directory)
    and atomically replaces the target file with os.replace. Works in text
    mode with UTF-8 encoding. Provides context manager support.
    If the path is detected as a cloud-synced folder, we fall back to writing
    directly to the target file (best-effort; cloud folders cannot guarantee
    atomic renames).

    Une classe pour écrire des fichiers en toute sécurité,
    en utilisant des fichiers temporaires pour éviter la perte de données.
    """
    # il faut s'assurer que la classe SafeWriteFile ouvre les fichiers en mode texte avec l'encodage UTF-8.

    def __init__(self, filename):
        """
        Initialisez le SafeWriteFile avec un nom de fichier.

        Args :
            filename (str) : Le nom de fichier dans lequel écrire.
        """
        # Si le fichier est destiné à contenir du XML (qui est un format textuel),
        # il est généralement préférable de l'écrire en mode texte avec
        # un encodage spécifique comme UTF-8.
        # Si vous ouvrez le fichier en mode binaire pour l'écriture ('wb'),
        # vous devrez encoder explicitement la chaîne XML en bytes
        # avant de l'écrire (par exemple, tree.write(self.__fd, encoding="utf-8")
        # suivi d'un appel à .encode('utf-8') si tree.write attend un flux binaire).
        # log.info("Initialisation de SafeWriteFile avec un nom de fichier.")
        self.__filename = filename
        self.__tempFilename = None
        self.__fd = None
        self.__cloud = self._isCloud()
        log.info(
            "SafeWriteFile: initialisation pour filename=%s (cloud=%s)",
            filename,
            self.__cloud,
        )
        if self._isCloud():
            # Ideally we should create a temporary file on the same filesystem (so that
            # os.rename works) but outside the Dropbox folder...
            self.__fd = open(self.__filename, "wb")  # texte ou binaire ?
            # self.__fd = open(self.__filename, "w")
            # self.__fd = open(self.__filename, "w", encoding="utf-8")
            # self.__tempFilename = ?
        else:
            self.__tempFilename = self._getTemporaryFileName(
                os.path.dirname(filename)
            )
            # # Create a named temporary file in same directory; keep the name and open it.
            # dirn = os.path.dirname(filename) or "."
            # # NamedTemporaryFile with delete=False returns a file that we can close and reopen.
            # with tempfile.NamedTemporaryFile(dir=dirn, delete=False, mode="w", encoding="utf-8") as tf:
            #     self.__tempFilename = tf.name
            # # Open the temp file for writing (text mode UTF-8)
            self.__fd = open(self.__tempFilename, "wb")  # texte ou binaire ?
            # # self.__fd = open(self.__tempFilename, "wb+")  # texte ou binaire ?
            # self.__fd = open(self.__tempFilename, "w", encoding="utf-8")
            # # self.__fd = open(file=self.__tempFilename, mode="wb", encoding="utf-8")
        # self.__fd = filename
        # log.info("Initialisation de SafeWriteFile avec un nom de fichier."
        #          f"self.__filename={self.__filename}"
        #          f"self.__fd={self.__fd}"
        #          f"self.__tempFilename={self.__tempFilename}")
        log.info(
            "SafeWriteFile.init terminé : temp=%s fd=%r",
            self.__tempFilename,
            self.__fd,
        )

    # L'erreur AttributeError: 'SafeWriteFile' object has no attribute 'name' indique que l'objet SafeWriteFile n'a pas d'attribut name. Cela se produit dans writer.py à la ligne 802 lors de la tentative d'accès à self.__fd.name pour enregistrer le fichier.
    # L'attribut name est généralement disponible pour les objets fichiers standard, mais il semble que SafeWriteFile ne l'implémente pas. Pour corriger cela, on peut ajouter une propriété name à la classe SafeWriteFile dans taskfile.py qui retourne le nom du fichier.
    # Cette modification ajoute une propriété name à la classe SafeWriteFile qui retourne la valeur de self.__filename. Cela permettra à la méthode ChangesXMLWriter.write d'accéder au nom du fichier sans erreur.
    @property
    def name(self):
        """Retourne le nom du fichier."""
        return self.__filename

    # Cette modification ajoute une propriété mode à la classe SafeWriteFile qui retourne la valeur de self.__fd.mode si l'attribut existe.
    # Cela permettra à la méthode ChangesXMLWriter.write d'accéder au mode du fichier sans erreur.
    @property
    def mode(self):
        """Retourne le mode du fichier."""
        if hasattr(self.__fd, "mode"):
            return self.__fd.mode
        return None

    def write(self, bf):
        """
        Écrivez les données dans le fichier.

        Args :
            bf (str) : Les données à écrire.
        """
        log.info(f"SafeWriteFile.write essaie d'écrire {bf} dans {self.__fd}.")
        # # if isinstance(bf, str):
        # #     # Le mode d'ouverture 'wb' est binaire, donc nous devons encoder la chaîne
        # #     # self.__fd.write(bf)  # comment transformer bf(bytes) en string ? Non, ici, init est en bytes !!!
        # #     self.__fd.write(bf.encode('utf-8'))
        # # else:
        # #     # self.__fd.write(str(bf))
        # #     self.__fd.write(str(bf).encode('utf-8'))
        # if not isinstance(bf, str):
        #     bf = str(bf)
        self.__fd.write(bf)

    def flush_and_sync(self):
        # Nouvelle méthode pour forcer l'écriture sur le disque
        """
        Force l'écriture des données en mémoire tampon sur le disque.

        Returns :

        """
        try:
            self.__fd.flush()
            os.fsync(self.__fd.fileno())
        except Exception:
            # If fsync not applicable (e.g., Windows text mode sometimes), ignore but keep flush
            try:
                self.__fd.flush()
            except Exception:
                pass

    def close(self):
        """
        Fermez le fichier et renommez le fichier temporaire en toute sécurité si nécessaire.
        """
        log.info(
            "SafeWriteFile.close essaie de Fermer le fichier et renommer le fichier temporaire en toute sécurité si nécessaire."
        )
        # # if isinstance(self.__fd, TextIOWrapper):
        self.__fd.close()
        # if not self.__fd:
        #     return
        # try:
        #     self.flush_and_sync()
        # finally:
        #     try:
        #         self.__fd.close()
        #     except Exception:
        #         pass
        # if not self._isCloud():
        if not self.__cloud and self.__tempFilename:
            # Use os.replace for atomic replacement where supported
            # if os.path.exists(self.__filename):
            try:
                log.info(f"SafeWriteFile.close retire {self.__filename}.")
                # os.remove(self.__filename)
                os.replace(self.__tempFilename, self.__filename)
            # if self.__filename is not None:
            #     if os.path.exists(self.__filename):
            #         log.info(f"SafeWriteFile.close utilise __moveFileOutOfTheWay sur {self.__filename} avant de le renommer.")
            #         # WTF ?
            #         self.__moveFileOutOfTheWay(self.__filename)
            #     log.info(f"SafeWriteFile.close renomme {self.__tempFilename} en {self.__filename}.")
            #     os.rename(self.__tempFilename, self.__filename)
            except Exception as e:
                # Try fallback rename if replace fails
                log.exception(
                    "SafeWriteFile.close: os.replace failed, trying os.rename: %s",
                    e,
                )
                try:
                    os.rename(self.__tempFilename, self.__filename)
                except Exception:
                    log.exception(
                        "SafeWriteFile.close: os.rename fallback failed; removing temp file."
                    )
                    try:
                        if os.path.exists(self.__tempFilename):
                            os.remove(self.__tempFilename)
                    except Exception:
                        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # On exception, ensure temp file removed to avoid littering
            try:
                if self.__fd:
                    try:
                        self.__fd.close()
                    except Exception:
                        pass
                if self.__tempFilename and os.path.exists(self.__tempFilename):
                    os.remove(self.__tempFilename)
            except Exception:
                log.exception(
                    "SafeWriteFile.__exit__: erreur lors du nettoyage après exception"
                )
            return False  # propagate exception
        else:
            try:
                self.close()
            except Exception:
                log.exception(
                    "SafeWriteFile.__exit__: erreur lors de la fermeture"
                )
                raise
            return False

    # méthodes obsolètes, à supprimer plus tard :
    def __moveFileOutOfTheWay(self, filename):
        """
        Déplacez un fichier existant en le renommant
        avec un suffixe incrémental pour éviter l'écrasement.

        Args :
            filename str : Le nom du fichier à déplacer.
        """
        log.debug(
            "SafeWriteFile.__moveFileOutOfTheWay : Déplacement de '%s' pour éviter l'écrasement",
            filename,
        )

        index = 1
        while True:
            name, ext = os.path.splitext(filename)
            # newName = "%s (%d)%s" % (name, index, ext)
            newName = f"{name} ({index:d}){ext}"
            if not os.path.exists(newName):
                os.rename(filename, newName)
                break
            index += 1

    def _getTemporaryFileName(self, path):
        """Générer un nom de fichier temporaire.

        Toutes les fonctions/classes de la bibliothèque standard qui peuvent générer
        un fichier temporaire, visible sur le système de fichiers, sans le supprimer
        à la fermeture sont obsolètes (il existe tempfile.NamedTemporaryFile
        mais son argument 'delete' est nouveau dans Python 2.6). Ce n'est pas
        sécurisé, ni thread-safe, mais cela fonctionne.

        Args :
            path (str) : Le chemin du répertoire dans lequel créer le fichier temporaire.

        Returns :
            name (str) : Le nom du fichier temporaire généré.
        """
        idx = 0
        while True:
            # name = os.path.join(path, "tmp-%d" % idx)
            name = os.path.join(path, f"tmp-{idx:d}")
            if not os.path.exists(name):
                return name
            idx += 1
        # Use `tempfile.NamedTemporaryFile`: This is the recommended way to create temporary files
        # in Python and provides better security and thread safety.
        # TODO: A utiliser une fois le reste réglé :
        # with tempfile.NamedTemporaryFile(dir=path, delete=False) as tf:
        #     return tf.name

    def _isCloud(self):
        """
        Vérifiez si le fichier se trouve dans un répertoire synchronisé avec le cloud.

        Returns :
            (bool) : True si le fichier se trouve dans un répertoire synchronisé avec le cloud, False sinon.
        """
        return _isCloud(os.path.dirname(self.__filename))


class TaskFile(patterns.Observer):
    """
    Une classe pour gérer le fichier de tâches, y compris le chargement,
    l'enregistrement et la surveillance des modifications.
    """

    def __init__(self, parent, poll=True, *args, **kwargs):
        """
        Initialisez le fichier TaskFile  contenant la liste de tâches.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        log.info("Initialisation de TaskFile")

        # self.settings = settings
        self.__parent = parent
        self.__poll = poll
        self.__filename = self.__lastFilename = ""
        # log.info("TaskFile : self.__filename = self.__lastFilename = ''")
        self.__needSave = self.__loading = False
        # log.info("TaskFile : self.__needSave = self.__loading = False")
        self.__tasks = task.TaskList()  # La liste de tâches.
        # log.info(f"TaskFile : self.__tasks = {self.__tasks}")
        self.__categories = category.CategoryList()  # La liste des catégories.
        # log.info(f"TaskFile : self.__categories = {self.__categories}")
        self.__notes = note.NoteContainer()  # La liste des notes.
        # log.info(f"TaskFile : self.__notes = {self.__notes}")
        self.__efforts = effort.EffortList(
            self.tasks()
        )  # Les listes des efforts des tâches.
        # log.info(f"TaskFile : self.__efforts = {self.__efforts}")
        # self.__guid = generate()  # utilisation de thirdparty.guid
        # remplacé par uuid :
        self.__guid = str(uuid.uuid4())
        # log.info(f"TaskFile : self.__guid = {self.__guid}")
        self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        # log.info(f"TaskFile : self.__syncMLConfig = {self.__syncMLConfig}")
        self.__monitor = ChangeMonitor()
        # log.info(f"TaskFile : self.__monitor = {self.__monitor}")
        self.__changes = dict()
        self.__changes[self.__monitor.guid()] = self.__monitor
        # log.info(f"TaskFile : self.__changes = {self.__changes}")
        self.__changedOnDisk = False
        if kwargs.pop("poll", True):
            self.__notifier = TaskCoachFilesystemPollerNotifier(self)
        else:
            self.__notifier = TaskCoachFilesystemNotifier(self)
        self.__saving = False
        for collection in [self.__tasks, self.__categories, self.__notes]:
            self.__monitor.monitorCollection(collection)
        for domainClass in [
            task.Task,
            category.Category,
            note.Note,
            effort.Effort,
            attachment.FileAttachment,
            attachment.URIAttachment,
            attachment.MailAttachment,
        ]:
            self.__monitor.monitorClass(domainClass)
        super().__init__(*args, **kwargs)

        # Register observers...
        # Register for tasks, categories, efforts and notes being changed so we
        # can monitor when the task file needs saving (i.e. is 'dirty'):
        for container in self.tasks(), self.categories(), self.notes():
            for eventType in container.modificationEventTypes():
                self.registerObserver(
                    self.onDomainObjectAddedOrRemoved,
                    eventType,
                    eventSource=container,
                )

        for eventType in (
            base.Object.markDeletedEventType(),
            base.Object.markNotDeletedEventType(),
        ):
            self.registerObserver(self.onDomainObjectAddedOrRemoved, eventType)

        for eventType in task.Task.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onTaskChanged_Deprecated, eventType)
        pub.subscribe(self.onTaskChanged, "pubsub.task")
        for eventType in effort.Effort.modificationEventTypes():
            self.registerObserver(self.onEffortChanged, eventType)
        for eventType in note.Note.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(self.onNoteChanged_Deprecated, eventType)
        pub.subscribe(self.onNoteChanged, "pubsub.note")
        for eventType in category.Category.modificationEventTypes():
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onCategoryChanged_Deprecated, eventType
                )
        pub.subscribe(self.onCategoryChanged, "pubsub.category")
        for eventType in (
            attachment.FileAttachment.modificationEventTypes()
            + attachment.URIAttachment.modificationEventTypes()
            + attachment.MailAttachment.modificationEventTypes()
        ):
            if not eventType.startswith("pubsub"):
                self.registerObserver(
                    self.onAttachmentChanged_Deprecated, eventType
                )
        pub.subscribe(self.onAttachmentChanged, "pubsub.attachment")

        # log.info("TaskFile : Tâches initiales : %s", self.tasks())
        # log.info("TaskFile : Notes initiales : %s", self.notes())
        log.info("TaskFile initialisé.")

    def __str__(self):
        """Retourne une représentation sous forme de chaîne du fichier de tâches (le nom du fichier)."""
        return self.filename()
        # return str(self.filename())

    def __contains__(self, item):
        """
        Vérifie si un élément (tâche, note, catégorie ou effort) appartient à ce fichier de tâches.

        Args :
            item : L’objet à rechercher dans le fichier de tâches.

        Returns :
            (bool) : True si l’objet appartient à l’une des collections du fichier de tâches, sinon False.
        """

        return (
            item in self.tasks()
            or item in self.notes()
            or item in self.categories()
            or item in self.efforts()
        )

    def monitor(self):
        """
        Obtenez l'instance ChangeMonitor.

        Returns :
            ChangeMonitor : L'instance ChangeMonitor.
        """
        return self.__monitor

    def categories(self):
        """
        Obtenez l'instance CategoryList.

        Returns :
            CategoryList : l'instance CategoryList.
        """
        return self.__categories

    def notes(self):
        """
        Obtenez l'instance de NoteContainer.

        Returns :
            NoteContainer : l'instance de NoteContainer.
        """
        return self.__notes

    def tasks(self):
        """
        Obtenez l'instance TaskList (Liste de tâches).

        Returns :
            TaskList : L'instance TaskList. La liste de tâches.
        """
        return self.__tasks

    def efforts(self):
        """
        Obtenez l'instance EffortList. (Liste des efforts)

        Returns :
            EffortList : L'instance EffortList. La liste des efforts.
        """
        return self.__efforts

    def syncMLConfig(self):
        """
        Obtenez la configuration SyncML.

        Returns :
            SyncMLConfig : la configuration SyncML.
        """
        return self.__syncMLConfig

    def guid(self):
        """
        Obtenez le GUID du fichier de tâches.

        Returns :
            str : Le GUID du fichier de tâches.
        """
        return self.__guid

    def changes(self):
        """
        Récupère le dictionnaire des modifications.

        Returns :
            (dict) : Le dictionnaire des modifications.
        """
        return self.__changes

    def setSyncMLConfig(self, config):
        """
        Définissez la configuration SyncML et marquez le fichier de tâches comme sale.

        Args :
            config (SyncMLConfig) : La configuration SyncML.
        """
        self.__syncMLConfig = config
        self.markDirty()

    def isEmpty(self):
        """
        Vérifiez si le fichier de tâche est vide.

        Returns :
            bool : True si le fichier de tâche est vide, False sinon.
        """
        return (
            0
            == len(self.categories())
            == len(self.tasks())
            == len(self.notes())
        )

    def onDomainObjectAddedOrRemoved(self, event):  # pylint: disable=W0613
        """
        Gérer les événements ajoutés ou supprimés des objets de domaine.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        self.markDirty()

    def onTaskChanged(self, newValue, sender):
        """
        Listener pour Gérer les événements modifiés par la tâche.

        Utilisé avec pubsub pour recevoir les messages.

        Args :
            newValue : La nouvelle valeur.
            sender (task) : La tâche qui a changé (l'expéditeur).
        """
        if self.__loading or self.__saving:
            return
        if sender in self.tasks():
            self.markDirty()

    def onTaskChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de tâche obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        changedTasks = [
            changedTask
            for changedTask in event.sources()
            if changedTask in self.tasks()
        ]
        if changedTasks:
            self.markDirty()
            for changedTask in changedTasks:
                changedTask.markDirty()

    def onEffortChanged(self, event):
        """
        Gérer les événements modifiés par l'effort.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        changedEfforts = [
            changedEffort
            for changedEffort in event.sources()
            if changedEffort.task() in self.tasks()
        ]
        if changedEfforts:
            self.markDirty()
            for changedEffort in changedEfforts:
                changedEffort.markDirty()

    def onCategoryChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de catégorie obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in event.sources()
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Marquer comme sales tous les éléments catégorisables appartenant à la catégorie modifiée ;
            # ceci est nécessaire car dans le monde SyncML/vcard, les catégories ne sont pas
            # des objets de première classe. Au lieu de cela, chaque tâche/contact/etc a une propriété
            # catégories qui est une liste de noms de catégorie
            # séparés par des virgules. Ainsi, lorsqu'un nom de catégorie change, chaque
            # catégorisable associé change.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onCategoryChanged(self, newValue, sender):
        """
        Gérer les événements de modification de catégorie.

        Args :
            newValue : la nouvelle valeur.
            sender (Category) : la catégorie qui a changé.
        """
        if self.__loading or self.__saving:
            return
        changedCategories = [
            changedCategory
            for changedCategory in [sender]
            if changedCategory in self.categories()
        ]
        if changedCategories:
            self.markDirty()
            # Marquer comme sales tous les éléments catégorisables appartenant à la catégorie modifiée ;
            # ceci est nécessaire car dans le monde SyncML/vcard, les catégories ne sont pas
            # des objets de première classe. Au lieu de cela, chaque tâche/contact/etc a une propriété
            # catégories qui est une liste de noms de catégorie
            # séparés par des virgules. Ainsi, lorsqu'un nom de catégorie change, chaque
            # catégorisable associé change.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()

    def onNoteChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de note obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        for changedNote in event.sources():
            changedNote.markDirty()

    def onNoteChanged(self, newValue, sender):
        """
        Gérer les événements de modification de note.

        Args :
            newValue : la nouvelle valeur.
            sender (Note) : la note qui a changé.
        """
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        sender.markDirty()

    def onAttachmentChanged(self, newValue, sender):
        """
        Gérer les événements de modification de la pièce jointe.

        Args :
            newValue : la nouvelle valeur.
            sender (Attachment) : la pièce jointe qui a changé.
        """
        if self.__loading or self.__saving:
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Nous supposons que ce soit le cas.
        self.markDirty()

    def onAttachmentChanged_Deprecated(self, event):
        """
        Gérer les événements de modification des pièces jointes obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Supposons que ce soit le cas.
        self.markDirty()
        for changedAttachment in event.sources():
            changedAttachment.markDirty()

    def setFilename(self, filename):
        """
        Définissez le nom de fichier du fichier de tâche.

        Args :
            filename (str) : Le nom de fichier à définir.
        """
        if filename == self.__filename:
            return
        self.__lastFilename = filename or self.__filename
        self.__filename = filename
        self.__notifier.setFilename(filename)
        pub.sendMessage("taskfile.filenameChanged", filename=filename)
        log.info(
            "TaskFile.setFilename : Nom de fichier défini sur : %s", filename
        )

    def filename(self):
        """
        Obtenez le nom de fichier du fichier de tâche.

        Returns :
            (str) : Le nom de fichier du fichier de tâche.
        """
        # log.debug("TaskFile.filename : Retourne le nom de fichier courant : %s appelé par %s", self.__filename, self)  # Crée une boucle infini !!! Ne pas utiliser !!!
        return self.__filename

    def lastFilename(self):
        """
        Obtenez le dernier nom de fichier du fichier de tâche.

        Returns :
            (str) : Le dernier nom de fichier du fichier de tâche.
        """
        return self.__lastFilename

    def isDirty(self):
        """
        Vérifiez si le fichier de tâche doit être enregistré.

        Returns :
            (bool) : True si le fichier de tâche doit être enregistré, False sinon.
        """
        log.debug(
            "TaskFile.isDirty : Vérification de l'état 'dirty' : %s",
            self.__needSave,
        )
        return self.__needSave

    def markDirty(self, force=False):
        """
        Marquer le fichier de tâche comme sale (doit être enregistré).

        Args :
            force (bool) : (optional) S'il faut forcer le marquage comme sale. La valeur par défaut est False.
        """
        if force or not self.__needSave:
            self.__needSave = True
            pub.sendMessage("taskfile.dirty", taskFile=self)
            log.debug(
                "TaskFile.markDirty : Modification détectée, état 'dirty' mis à jour à True"
            )
            log.debug(
                f"TaskFile.markDirty : Le fichier {self} est marqué comme à modifier."
            )

    def markClean(self):
        """
        Marquez le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré).
        """
        if self.__needSave:
            log.info(
                "TaskFile.markClean : Marque le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré)."
            )
            self.__needSave = False
            pub.sendMessage("taskfile.clean", taskFile=self)

    def onFileChanged(self):
        """
        Gérer les modifications de fichiers.

        Gère les modifications de fichier détectées par le notificateur.
        Appelé quand l'état de la tâche est changé.

        NOTE: self.__parent doit être un widget Tk possédant after_idle (typiquement root).
        """
        if not self.__saving:
            self.__changedOnDisk = True
            log.debug(
                "TaskFile.onFileChanged : Appelle CallAfter programmé via parent.after_idle."
            )
            if GUI_NAME == "tk":
                # # self.__parent.after_idle(self.__fileChanged)
                # # self.__parent.after_idle(self.notifyFileChange)
                # # self.__parent.after_idle(self.changes)
                # self.__parent.after_idle(lambda: pub.sendMessage("taskfile.changed", taskFile=self))
                try:
                    # schedule the pub send in the Tkinter main thread
                    self.__parent.after_idle(
                        lambda: pub.sendMessage(
                            "taskfile.changed", taskFile=self
                        )
                    )
                except Exception:
                    # If parent is not available or after_idle fails, fall back to direct call (risky for UI thread)
                    log.exception(
                        "TaskFile.onFileChanged : after_idle failed, envoi direct de l'événement"
                    )
                    pub.sendMessage("taskfile.changed", taskFile=self)
            elif GUI_NAME == "wx":
                import wx  # Not really clean but we're in another thread...

                wx.CallAfter(
                    pub.sendMessage, "taskfile.changed", taskFile=self
                )
            # log.debug("TaskFile.onFileChanged : CallAfter passé avec succès.")
            # TODO: Remplacer l'appel wx.CallAfter par l'équivalent tkinter.
            # Il est nécessaire d'avoir une référence à la fenêtre principale Tkinter
            # pour utiliser la méthode after(). Une approche est de passer cette référence
            # au TaskFile ou d'utiliser un objet singleton accessible globalement.
            # Pour l'instant, je vais laisser un commentaire explicatif.

            # Equivalent de wx.CallAfter dans tkinter: root.after(0, ...)
            # Où 'root' est la fenêtre principale de l'application.
            # La ligne ci-dessous est un placeholder et devra être adaptée
            # en fonction de l'architecture de votre application Tkinter.
            # Par exemple:
            # root_widget.after(0, pub.sendMessage, "taskfile.changed", taskFile=self)

            # En l'absence d'une référence à la fenêtre principale, nous devons
            # trouver un autre moyen de déclencher l'événement dans le thread principal.
            # Une solution simple est d'utiliser un événement de thread.
            # Pour le moment, nous allons simplement émettre l'événement directement,
            # mais cela peut causer des problèmes si le listener essaie d'accéder
            # à l'interface utilisateur.

            # La ligne d'origine était :
            # wx.CallAfter(pub.sendMessage, "taskfile.changed", taskFile=self)

            # Pour la conversion, il faut un moyen d'appeler la fonction dans le thread
            # de l'UI. Le plus simple est de supposer que l'objet racine de Tkinter
            # est disponible d'une manière ou d'une autre, et d'utiliser sa méthode `after`.
            # Comme je n'ai pas le code de l'UI, je vais créer une variable
            # `_tkinter_root` qui doit être initialisée dans le code principal de l'UI.

            # En l'absence d'une référence à la fenêtre racine, on peut juste
            # appeler directement l'événement, mais il faut être conscient que
            # cela pourrait entraîner des problèmes de threading si les listeners
            # interagissent avec l'UI. La manière correcte serait de stocker
            # une référence à la fenêtre racine de Tkinter.

            # # Solution proposée: créer une fonction proxy pour sendMessage
            # def _send_message_in_main_thread():
            #     pub.sendMessage("taskfile.changed", taskFile=self)
            #
            # # Si la fenêtre racine Tkinter est disponible globalement, on pourrait faire :
            # # if hasattr(TaskFile, 'root_window'):
            # #     TaskFile.root_window.after(0, _send_message_in_main_thread)
            # # else:
            # _send_message_in_main_thread()

            log.debug(
                "TaskFile.onFileChanged : Appel à pub.sendMessage passé avec succès, événement envoyé/prévu."
            )

    @patterns.eventSource
    def clear(self, regenerate=True, event=None):
        """
        Effacez le fichier de tâches, en régénérant éventuellement la configuration GUID et SyncML.

        Args :
            regenerate (bool, optional) : s'il faut régénérer la configuration GUID et SyncML. La valeur par défaut est True.
            event (Event, optional) : L'événement. La valeur par défaut est Aucun.
        """
        log.info(
            f"taskFile.clear : Effacement du contenu du fichier de tâches {self}(clear)."
        )

        pub.sendMessage("taskfile.aboutToClear", taskFile=self)
        try:
            self.tasks().clear(event=event)
            self.categories().clear(event=event)
            self.notes().clear(event=event)
            if regenerate:
                # self.__guid = generate()
                self.__guid = str(uuid.uuid4())
                self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        finally:
            pub.sendMessage("taskfile.justCleared", taskFile=self)

    def stop(self):
        """
        Arrêter le notificateur du système de fichiers.
        """
        log.info("TaskFile.stop() appelé.")
        self.__notifier.stop()

    def _read(self, fd):
        """
        Lire le fichier de tâches à partir d'un descripteur de fichier.

        Args :
            fd : (file) Le descripteur de fichier à partir duquel lire.

        Returns :
            (tuple) : Les données lues (tâches, catégories, notes, syncMLConfig, modifications, guid).
        """
        # Assurez-vous que la variable fd passée au constructeur de XMLReader
        # est bien un objet fichier valide et ouvert en mode binaire ('rb')
        # pour la lecture. Si ce n'est pas le cas, cela pourrait expliquer
        # pourquoi self.__fd.read() renvoie une chaîne.
        log.debug(
            f"TaskFile._read essaie de lire le fichier de tâche à partir d'un descripteur fd {fd}"
        )
        data_read = xml.XMLReader(fd).read()
        reader = xml.XMLReader(fd)
        result = reader.read()
        duplicate_ids = reader.get_duplicate_ids()

        # Log duplicate IDs if any found
        if duplicate_ids:
            self._log_duplicate_ids(duplicate_ids)

        log.debug(f"TaskFile._read renvoi data_read: {data_read}")
        # log.debug(f"TaskFile._read renvoi : {result}, {duplicate_ids}")
        log.debug(f"TaskFile._read renvoi result: {result}.")
        # return result, duplicate_ids
        return result
        return data_read

    def _log_duplicate_ids(self, duplicate_ids):
        """Log duplicate IDs found in the task file.

        Duplicate IDs can cause issues with sync and data integrity.
        To fix: Either manually edit the .tsk XML file to assign unique IDs,
        or delete and recreate the affected items in Task Coach.
        """
        logger = logging.getLogger(__name__)
        logger.warning("=" * 70)
        logger.warning(
            "WARNING: Duplicate IDs found in task file: %s", self.__filename
        )
        logger.warning(
            "This may cause sync issues or data integrity problems."
        )
        logger.warning("")
        logger.warning("To fix: Either manually edit the .tsk XML file to")
        logger.warning(
            "assign unique IDs, or delete and recreate the affected"
        )
        logger.warning("items in Task Coach.")
        logger.warning("")
        logger.warning("Duplicate IDs and their locations:")
        for obj_id, locations in duplicate_ids.items():
            logger.warning("")
            logger.warning("  ID: %s", obj_id)
            for obj_type, path in locations:
                logger.warning("    - %s", path)
        logger.warning("=" * 70)

    def exists(self):
        """
        Vérifiez si le fichier de tâche existe.

        Returns :
            (bool) : True si le fichier de tâche existe, False sinon.
        """
        log.debug("TaskFile.exists vérifie si le fichier de tâche existe.")
        taskfile_exist = os.path.isfile(self.__filename)
        log.debug(
            f"TaskFile.exists : Le fichier de tâche existe = {taskfile_exist}."
        )
        return taskfile_exist

    def _openForWrite(self, suffix=""):
        """
        Ouvrez le fichier de tâche en écriture.

        Args :
            suffix (str) : (facultatif) le suffixe du fichier. La valeur par défaut est "".

        Returns :
            SafeWriteFile : l'instance SafeWriteFile.
        """
        # log.info(f"TaskFile._openForWrite : Essaie d'ouvrir le fichier de tâche {self.__filename + suffix} en écriture.")
        log.info(
            f"TaskFile._openForWrite : Essaie d'ouvrir le fichier de tâche {self.filename}{suffix} en écriture."
        )
        return SafeWriteFile(self.__filename + suffix)

    def close(self):
        """
        Fermez le fichier de tâches, en enregistrant toutes les modifications
        et en effaçant le contenu.
        """
        log.info(
            "TaskFile.close Ferme le fichier de tâches, en enregistrant toutes les modifications et en effaçant le contenu."
        )
        if os.path.exists(self.filename()):
            # changes = xml.ChangesXMLReader(self.filename() + ".delta").read()
            try:
                log.debug(
                    f"TaskFile.close : Essaie de lire le fichier {self.filename()}.delta en mode r et d'enregistrer les changements précédents."
                )
                # # with open(self.filename() + ".delta", "r") as f:
                # # with open(self.filename() + ".delta", "r", encoding="utf-8") as f:
                # # with self.filename() + ".delta" as f:
                # with f"{self.filename()}.delta" as f:
                with open(f"{self.filename()}.delta", "rb") as f:
                    changes = xml.ChangesXMLReader(f).read()
                    log.debug(f"TaskFile.close : lit changes = {changes}")
            except FileNotFoundError as e:
                log.exception(
                    f"TaskFile.close : Le fichier {self.filename()}.delta n'existe pas : {e}."
                )
                changes = {}
            # remove own monitor's changes
            del changes[self.__monitor.guid()]
            log.debug(
                f"TaskFile.close : Essaie d'écrire les changements {changes} dans le fichier {self.filename()}.delta en mode wb+ avec encodage UTF-8."
            )
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "wb")).write(
            #     changes
            # )
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "w")).write(
            #     changes
            # )
            # with open(self.filename() + ".delta", "wb+") as fd:
            # with open(self.filename() + ".delta", "w+", encoding="utf-8") as fd:
            # with self._openForWrite(".delta") as fd:
            with open(self.filename() + ".delta", "wb") as fd:
                writer = xml.ChangesXMLWriter(fd)
                writer.write(changes)

        log.info("TaskFile.close règle filename sur ''")
        self.setFilename("")
        # self.__guid = generate()
        self.__guid = str(uuid.uuid4())
        # self.clear(False)
        self.clear()
        self.__monitor.reset()
        self.markClean()
        self.__changedOnDisk = False
        log.debug("TaskFile.close terminé avec succès.")

    def _openForRead(self):
        """
        Ouvrez le fichier de tâche pour la lecture.

        Returns :
            Le descripteur de fichier à lire.
        """
        # return file(self.__filename, 'r')
        log.info(
            f"TaskFile._openForRead : Ouvre {self.__filename} en mode lecture texte (r)!"
        )
        # return open(self.__filename, "r")
        return open(self.__filename, "r", encoding="utf-8")

    def load(self, filename=None):
        """
        Chargez le fichier de tâche à partir du disque.

        Cette méthode lit un fichier XML contenant les tâches, catégories, notes,
        configurations SyncML et changements précédents. Elle initialise toutes les
        structures internes de l'objet TaskFile avec ces données.

        Si le fichier n'existe pas, elle initialise un fichier vide avec une
        configuration par défaut.

        Args :
            filename (str | None) : (optional) Le nom du fichier à partir duquel
            charger. La valeur par défaut est None. Le nom du fichier à charger.
            Si None, on utilise le nom déjà défini via `setFilename()`.

        Raises :
            IOError : Si le fichier ne peut pas être ouvert.
            Exception : Si une erreur de parsing XML ou de lecture survient.
        """
        log.info(
            "TaskFile.load : Chargement du fichier de tâches '%s' à partir du disque.",
            filename,
        )

        pub.sendMessage("taskfile.aboutToRead", taskFile=self)
        self.__loading = True
        if filename:
            self.setFilename(filename)
        # filename = filename or self.__filename
        # self.__filename = filename

        log.info(
            "TaskFile.load : Chargement du fichier de tâches depuis : %s",
            filename,
        )

        try:
            if self.exists():
                fd = self._openForRead()
                # with self._openForRead() as fd:
                log.info(
                    f"TaskFile.load : fd={fd} ouvert en mode lecture texte(r) !"
                )
                try:
                    tasks, categories, notes, syncMLConfig, changes, guid = (
                        self._read(fd)
                    )

                except Exception:
                    log.exception(
                        "TaskFile.load : Erreur lors de la lecture du fichier principal '%s'",
                        self.filename(),
                    )
                    raise  # fd.close()  # déjà fait par le with
                finally:
                    fd.close()
            else:
                tasks = []
                categories = []
                notes = []
                changes = dict()
                # guid = generate()
                guid = str(uuid.uuid4())
                syncMLConfig = createDefaultSyncConfig(guid)
            self.clear()
            self.__monitor.reset()
            self.__changes = changes
            self.__changes[self.__monitor.guid()] = self.__monitor
            self.categories().extend(categories)
            self.tasks().extend(tasks)
            self.notes().extend(notes)

            def registerOtherObjects(objects):
                for obj in objects:
                    if isinstance(obj, base.CompositeObject):
                        registerOtherObjects(obj.children())
                    if isinstance(obj, note.NoteOwner):
                        registerOtherObjects(
                            obj.notes()
                        )  # Unresolved attribute reference 'notes' for class 'NoteOwner'
                    if isinstance(obj, attachment.AttachmentOwner):
                        registerOtherObjects(
                            obj.attachments()
                        )  # Unresolved attribute reference 'attachments' for class 'AttachmentOwner'
                    if isinstance(obj, task.Task):
                        registerOtherObjects(obj.efforts())
                    if (
                        isinstance(obj, note.Note)
                        or isinstance(obj, attachment.Attachment)
                        or isinstance(obj, effort.Effort)
                    ):
                        self.__monitor.setChanges(obj.id(), set())

            registerOtherObjects(self.categories().rootItems())
            registerOtherObjects(self.tasks().rootItems())
            registerOtherObjects(self.notes().rootItems())
            self.__monitor.resetAllChanges()
            self.__syncMLConfig = syncMLConfig
            self.__guid = guid

            if os.path.exists(self.filename()):
                # We need to reset the changes on disk because we're up to date.
                # Réécrit les changements sur disque (texte UTF-8)
                log.debug(
                    "TaskFile.load : Réécrit les changements dans {self.filename()}.delta en mode wb."
                )
                # xml.ChangesXMLWriter(
                #     open(self.filename() + ".delta", "wb")
                # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                # # xml.ChangesXMLWriter(
                # #     open(self.filename() + ".delta", "w")
                # # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                with open(self.filename() + ".delta", "wb") as f:
                    # with open(self.filename() + ".delta", "w", encoding="utf-8") as f:
                    writer = xml.ChangesXMLWriter(f)
                    writer.write(self.__changes)
                    # f.close()  # déjà fait par le with
        except Exception as e:
            log.info("TaskFile.load règle filename sur ''")
            self.setFilename("")
            raise Exception(
                f"TaskFile.load : Erreur de parsing XML lors du chargement de '{filename}', erreur : {e}"
            )
        finally:
            self.__loading = False
            self.markClean()
            self.__changedOnDisk = False
            pub.sendMessage("taskfile.justRead", taskFile=self)

        # try:
        #     with open(filename, "r", encoding="utf-8") as file:
        #         log.debug("TaskFile.load : METHODE A REVOIR !!!")
        #         parser = xml.reader.XMLReader(self)
        #         parser.read(file)
        #     # self.__dirty = False
        #     log.info("Fichier chargé avec succès : %s", filename)
        # except FileNotFoundError:
        #     log.warning("Fichier introuvable : %s. Un nouveau fichier sera créé.", filename)
        #     raise
        # except Exception as e:
        #     log.exception("Erreur lors du chargement du fichier de tâches : %s", filename)
        #     raise

    def save(self, **kwargs):
        """
        Enregistrez le fichier de tâches sur le disque.

        Cette méthode écrit toutes les tâches, notes, catégories et la configuration
        SyncML dans un fichier XML. Si le fichier existe déjà, il sera remplacé
        de manière sécurisée via l'utilisation d'un fichier temporaire (`SafeWriteFile`).

        En cas d'échec (problème de disque, erreur d'écriture...), une exception
        est loggée et propagée.

        Args :
            **kwargs : Arguments supplémentaires éventuels (non utilisés ici).

        Raises :
            IOError : En cas de problème d’écriture du fichier.
            Exception : En cas d’erreur inattendue pendant l’écriture.
        """
        log.info(
            "TaskFile.save commence à Enregistrer le fichier de tâches sur le disque."
        )
        # # log.info("Sauvegarde de la base de tâches dans '%s'", filename)
        # # À modifier avec les nouvelles possibilités de with.
        try:
            pub.sendMessage("taskfile.aboutToSave", taskFile=self)
        except Exception:
            pass
        # # When encountering a problem while saving (disk full,
        # # computer on fire), if we were writing directly to the file,
        # # it's lost. So write to a temporary file and rename it if
        # # everything went OK.
        self.__saving = True
        # try:
        #     # Fusionner les modifications du disque avec le fichier de tâches actuel.
        #     self.mergeDiskChanges()
        #
        #     if self.__needSave or not os.path.exists(self.__filename):
        #         fd = self._openForWrite()
        #         try:
        #             xml.XMLWriter(fd).write(
        #                 self.tasks(),
        #                 self.categories(),
        #                 self.notes(),
        #                 self.syncMLConfig(),
        #                 self.guid(),
        #             )
        #         finally:
        #             fd.close()
        #
        #     self.markClean()
        # finally:
        #     self.__saving = False
        #     self.__notifier.saved()
        #     try:
        #         pub.sendMessage("taskfile.justSaved", taskFile=self)
        #     except Exception:
        #         # log.exception("Erreur lors de la sauvegarde de '%s'", filename)
        #         pass

        if not self.__filename:
            log.error(
                "TaskFile.save : Aucun nom de fichier n’est défini pour la sauvegarde."
            )
            raise RuntimeError(
                "TaskFile.save : Aucun nom de fichier n’est défini pour la sauvegarde."
            )

        log.debug(
            "TaskFile.save : Début de la sauvegarde vers le fichier : %s",
            self.__filename,
        )

        try:
            self.mergeDiskChanges()

            if self.__needSave or not os.path.exists(self.__filename):
                # fd = self._openForWrite()
                # try:
                # with self.safeWriter(self.__filename) as file:
                with self._openForWrite() as fd:
                    # xmlWriter = writer.XMLWriter(self)
                    xmlWriter = xml.writer.XMLWriter(fd)
                    xmlWriter.write(
                        self.tasks(),
                        self.categories(),
                        self.notes(),
                        self.syncMLConfig(),
                        self.guid(),
                    )
                    # finally:
                    # fd.close()  # déjà fait par le with
            self.markClean()
            log.info(
                "TaskFile.save : Fichier sauvegardé avec succès : %s",
                self.__filename,
            )
        except IOError as e:
            log.exception(
                "TaskFile.save : Erreur d’écriture du fichier %s",
                self.__filename,
            )
            raise
        except Exception as e:
            log.exception(
                "TaskFile.save : Erreur inattendue lors de la sauvegarde du fichier : %s",
                self.__filename,
            )
            raise
        finally:
            self.__needSave = False
            self.__saving = False
            self.__notifier.saved()
            try:
                pub.sendMessage("taskfile.justSaved", taskFile=self)
            except Exception:
                pass

    def mergeDiskChanges(self):
        """
        Fusionner les modifications du disque avec le fichier de tâches actuel.
        """
        self.__loading = True
        try:
            if os.path.exists(
                self.__filename
            ):  # Not using self.exists() because DummyFile.exists returns True
                # Instead of writing the content of memory, merge changes
                # with the on-disk version and save the result.
                self.__monitor.freeze()
                try:
                    # fd = self._openForRead()
                    with self._openForRead() as fd:
                        log.info(
                            f"TaskFile.mergeDiskChanges : fd={fd} ouvert en mode lecture binaire !"
                        )
                        try:
                            (
                                tasks,
                                categories,
                                notes,
                                syncMLConfig,
                                allChanges,
                                guid,
                                # ) = self._read(fd)
                            ), _duplicate_ids = self._read(fd)
                        except Exception:
                            log.exception(
                                "TaskFile.mergeDiskChanges : Erreur lors de la lecture du fichier principal pour la fusion des changements '%s'",
                                self.__filename,
                            )
                            raise
                        # fd.close()  # déjà fait par le with
                        # Don't log duplicates here - already logged on initial load
                    self.__changes = allChanges

                    if self.__saving:
                        for devGUID, changes in list(self.__changes.items()):
                            if devGUID != self.__monitor.guid():
                                changes.merge(self.__monitor)

                    sync = ChangeSynchronizer(self.__monitor, allChanges)

                    sync.sync(
                        [
                            (
                                self.categories(),
                                category.CategoryList(categories),
                            ),
                            (self.tasks(), task.TaskList(tasks)),
                            (self.notes(), note.NoteContainer(notes)),
                        ]
                    )

                    self.__changes[self.__monitor.guid()] = self.__monitor
                finally:
                    self.__monitor.thaw()
            else:
                self.__changes = {self.__monitor.guid(): self.__monitor}

            self.__monitor.resetAllChanges()
            # fd = self._openForWrite(".delta")
            # try:
            #     xml.ChangesXMLWriter(fd).write(self.changes())
            # finally:
            #     fd.close()
            # write .delta (text UTF-8) using SafeWriteFile for atomicity
            with self._openForWrite(".delta") as fd:
                writer = xml.ChangesXMLWriter(fd)
                writer.write(self.changes())
                # fd.close()  # déjà fait par le with

            self.__changedOnDisk = False
        finally:
            self.__loading = False

    def saveas(self, filename):
        """
        Enregistrez le fichier de tâche sous un nouveau nom de fichier.

        Args :
            filename str : Le nouveau nom de fichier sous lequel enregistrer.
        """
        if os.path.exists(filename):
            os.remove(filename)
        # if os.path.exists(filename + ".delta"):
        if os.path.exists(f"{filename}.delta"):
            # os.remove(filename + ".delta")
            os.remove(f"{filename}.delta")
        self.setFilename(filename)
        self.save()

    def merge(self, filename):
        """
        Fusionnez un autre fichier de tâches avec celui-ci.

        Args :
            filename str : Le nom de fichier du fichier de tâches à fusionner.
        """
        mergeFile = self.__class__()
        mergeFile.load(filename)
        self.__loading = True
        categoryMap = dict()
        self.tasks().removeItems(
            self.objectsToOverwrite(self.tasks(), mergeFile.tasks())
        )
        self.rememberCategoryLinks(categoryMap, self.tasks())
        self.tasks().extend(mergeFile.tasks().rootItems())
        self.notes().removeItems(
            self.objectsToOverwrite(self.notes(), mergeFile.notes())
        )
        self.rememberCategoryLinks(categoryMap, self.notes())
        self.notes().extend(mergeFile.notes().rootItems())
        self.categories().removeItems(
            self.objectsToOverwrite(self.categories(), mergeFile.categories())
        )
        self.categories().extend(mergeFile.categories().rootItems())
        self.restoreCategoryLinks(categoryMap)
        mergeFile.close()
        self.__loading = False
        self.markDirty(force=True)

    def objectsToOverwrite(self, originalObjects, objectsToMerge):
        """
        Récupère les objets à écraser lors d'une fusion.

        Args :
            originalObjects (list) : Les objets d'origine.
            objectsToMerge (list) : Les objets à fusionner.

        Returns :
            list : Les objets à écraser.
        """
        objectsToOverwrite = []
        for domainObject in objectsToMerge:
            try:
                # Unresolved attribute reference 'getObjectById' for class 'list'
                # Vient de domain.base.collection.Collection !
                # get_object_by_Id = base.collection.Collection.getObjectById(domainObject.id())
                # @staticmethod
                # def getObjectById(the_Id):
                #     get_object_by_id = base.collection.Collection.getObjectById(the_Id)
                # from taskcoachlib.domain.base.collection import Collection
                objectsToOverwrite.append(
                    originalObjects.getObjectById(
                        domainObject.id()
                    )  # getObjectById vient de domain.base.collection.Collection ! Une liste d' ensemble d'objets composites observables.
                )
            except IndexError:
                pass
        return objectsToOverwrite

    def rememberCategoryLinks(self, categoryMap, categorizables):
        """
        N'oubliez pas les liens de catégorie pour une restauration ultérieure.

        Args :
            categorisMap (dict) : La carte des catégories.
            categorizables (list) : Les objets catégorisables.
        """
        for categorizable in categorizables:
            for categoryToLinkLater in categorizable.categories():
                categoryMap.setdefault(categoryToLinkLater.id(), []).append(
                    categorizable
                )

    def restoreCategoryLinks(self, categoryMap):
        """
        Restaurez les liens de catégorie à partir de la carte de catégorie mémorisée.

        Args :
            categoryMap (dict) : La carte de catégorie.
        """
        categories = self.categories()
        for categoryId, categorizables in categoryMap.items():
            try:
                categoryToLink = categories.getObjectById(categoryId)
            except IndexError:
                continue  # Subcategory was removed by the merge
            for categorizable in categorizables:
                categorizable.addCategory(categoryToLink)
                categoryToLink.addCategorizable(categorizable)

    def needSave(self):
        """
        Vérifiez si le fichier de tâche doit être enregistré.

        Returns :
            bool : True si le fichier de tâche doit être enregistré, False sinon.
        """
        return not self.__loading and self.__needSave

    def changedOnDisk(self):
        """
        Vérifiez si le fichier de tâche a changé sur le disque.

        Returns :
            bool : True si le fichier de tâche a changé sur le disque, False sinon.
        """
        return self.__changedOnDisk

    def beginSync(self):
        """
        Commencez une opération de synchronisation.
        """
        self.__loading = True

    def endSync(self):
        """
        Terminez une opération de synchronisation.
        """
        self.__loading = False
        self.markDirty()


class LockTimeout(Exception):
    """Raised when file lock cannot be acquired (another process has it)."""

    pass


class LockFailed(Exception):
    """Raised when file locking fails for other reasons."""

    pass


class DummyLockFile(object):
    """
    Une classe de fichier de verrouillage factice à utiliser dans les répertoires synchronisés avec le cloud.
    """

    def acquire(self, timeout=None):
        """Méthode factice pour acquérir un verrou. Ne fait rien."""
        pass

    def release(self):
        """Méthode factice pour relâcher un verrou. Ne fait rien."""
        pass

    def is_locked(self):
        """Retourne toujours True : simule qu’un verrou est en place."""
        return True

    def i_am_locking(self):
        """Retourne toujours True : simule que le processus courant détient le verrou."""
        return True

    def break_lock(self):
        """Méthode factice pour briser un verrou. Ne fait rien."""
        pass


class LockedTaskFile(TaskFile):
    """LockedTaskFile ajoute un verrouillage coopératif à TaskFile.

    Une classe TaskFile avec un verrouillage coopératif pour empêcher les accès simultanés.
    Appelé par Application.init.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser le LockedTaskFile.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.
        """
        super().__init__(*args, **kwargs)
        self.__lock = None
        self.__lock_acquired = False

    def __getLockPath(self, filename):
        """Get the path to the lock file."""
        return filename + ".lock"

    def __isFuse(self, path):
        """
        Vérifiez si un chemin donné est un système de fichiers FUSE.

        Args :
            path (str) : Le chemin à vérifier.

        Returns :
            (bool) : True si le chemin est un système de fichiers FUSE. Système de fichiers FUSE, False sinon.
        """
        if operating_system.isGTK() and os.path.exists("/proc/mounts"):
            # for line in open("/proc/mounts", "r", encoding="utf-8"):
            #     try:
            #         location, mountPoint, fsType, options, a, b = (
            #             line.strip().split()
            #         )
            #     except Exception:
            #         pass
            #     if os.path.abspath(path).startswith(
            #         mountPoint
            #     ) and fsType.startswith("fuse."):
            #         return True
            # essayer de remplacer par :
            try:
                # with garantit que le fichier proc/mounts sera fermé correctement, même en cas d'erreur.
                with open(
                    "/proc/mounts", "r", encoding="utf-8"
                ) as mounts_file:
                    for line in mounts_file:
                        try:
                            location, mount_point, fs_type, options, a, b = (
                                line.strip().split()
                            )
                            # if os.path.abspath(path).startswith(mount_point) and fs_type.startswith("fuse."):
                            #     return True
                        except ValueError:
                            # Ignorer les lignes mal formées dans /proc/mounts
                            continue
                        if os.path.abspath(path).startswith(
                            mount_point
                        ) and fs_type.startswith("fuse."):
                            return True
            except (FileNotFoundError, PermissionError) as e:
                # Gérer les erreurs de lecture du fichier /proc/mounts
                log.error(
                    f"LockedTaskFile.__isFuse: Erreur lors de la lecture de /proc/mounts: {e}"
                )
        return False

    def __isCloud(self, filename):
        """
        Vérifier si un fichier se trouve dans un répertoire synchronisé avec le cloud.

        Args :
            filename (str) : Le nom du fichier à vérifier.

        Returns :
            (bool) : True si le fichier se trouve dans un répertoire synchronisé avec le cloud, sinon False.
        """
        return _isCloud(os.path.dirname(filename))

    def __createLockFile(self, filename):
        """
        Créez un fichier de verrouillage pour le nom de fichier donné.

        Args :
            filename (str) : Le nom de fichier pour lequel créer un fichier de verrouillage.

        Returns :
            (FileLock or DummyLockFile) : L'instance de fichier de verrouillage.
        """
        if operating_system.isWindows() and self.__isCloud(filename):
            return DummyLockFile()
        if self.__isFuse(filename):
            return lockfile.MkdirFileLock(filename)
        return lockfile.FileLock(filename)

    def is_locked(self):
        """
        Vérifiez si le fichier de tâche est verrouillé.

        Returns :
            (bool) : True si le fichier de tâche est verrouillé, False sinon.
        """
        # return self.__lock and self.__lock.is_locked()
        return self.__lock is not None and self.__lock_acquired

    def is_locked_by_me(self):
        """
        Vérifiez si le fichier de tâches est verrouillé par le processus en cours.

        Returns :
            (bool) : True si le fichier de tâches est verrouillé par le processus en cours, False sinon.
        """
        # return self.is_locked() and self.__lock.i_am_locking()
        return self.is_locked()

    def release_lock(self):
        """
        Libérez le verrou sur le fichier de tâches.
        """
        # if self.is_locked_by_me():
        #     self.__lock.release()
        if self.__lock is not None and self.__lock_acquired:
            try:
                self.__lock.release()
            except Exception:
                pass  # Best effort release
            self.__lock_acquired = False
        self.__lock = None

    def acquire_lock(self, filename):
        """
        Acquérir un verrou sur le fichier de tâche.

        Args :
            filename (str) : Le nom du fichier à verrouiller.
        """
        # if not self.is_locked_by_me():
        #     self.__lock = self.__createLockFile(filename)
        #     self.__lock.acquire(5)
        if self.is_locked_by_me():
            return  # Already holding the lock

        lock_path = self.__getLockPath(filename)
        try:
            # self.__lock = self.__createLockFile(filename)
            self.__lock = fasteners.InterProcessLock(lock_path)
            # Try to acquire with short timeout (non-blocking for document apps)
            acquired = self.__lock.acquire(blocking=True, timeout=0.1)
            if not acquired:
                self.__lock = None
                raise LockTimeout(f"File is locked: {filename}")
            self.__lock_acquired = True
        except LockTimeout:
            raise
        except (PermissionError, OSError) as e:
            self.__lock = None
            raise LockFailed(str(e)) from e

    def break_lock(self, filename):
        """
        Briser le verrou sur le fichier de tâches.

        Args :
            filename (str) : Le nom de fichier sur lequel briser le verrou.
        """
        # self.__lock = self.__createLockFile(filename)
        # self.__lock.break_lock()
        lock_path = self.__getLockPath(filename)
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except OSError:
            pass  # If we can't remove it, acquire will fail anyway

    def close(self):
        """
        Fermez le fichier de tâches en libérant le verrou.
        """
        # if self.filename() and os.path.exists(self.filename()):
        #     self.acquire_lock(self.filename())
        try:
            super().close()
        finally:
            self.release_lock()

    def load(
        self, filename=None, lock=True, breakLock=False
    ):  # pylint: disable=W0221
        """Verrouillez le fichier avant de le charger, s'il n'est pas déjà verrouillé.

        Chargez le fichier de tâches à partir du disque, en acquérant un verrou si nécessaire.

        Args :
            filename (str | None) : (optional) Le nom du fichier à partir duquel charger. La valeur par défaut est Aucun.
            lock (bool) : (optional) S'il faut acquérir un verrou. La valeur par défaut est True.
            breakLock (bool) : (optional) S'il faut briser un verrou existant. La valeur par défaut est False.
        """
        log.debug(
            f"LockedTaskFile.load : Appelé avec self={self}, filename={filename}, lock={lock}, breakLock={breakLock}"
        )
        filename = filename or self.filename()
        log.debug(f"LockedTaskFile.load : Finalement filename={filename}")

        try:
            if lock and filename:
                if breakLock:
                    log.debug(
                        f"LockedTaskFile.load : Brise le verrou de {filename}."
                    )
                    self.break_lock(filename)
                log.debug(
                    f"LockedTaskFile.load : Acquière un verrou pur {filename}."
                )
                self.acquire_lock(filename)
            log.debug("LockedTaskFile.load : Charge le fichier {filename}.")
            return super().load(filename)
        finally:
            log.debug("LockedTaskFile.load : Finalement relâche le verrou.")
            # Release lock if load fails
            self.release_lock()

    def save(self, **kwargs):
        """Verrouillez le fichier avant de l'enregistrer, s'il n'est pas déjà verrouillé.

        Enregistrez le fichier de tâche sur le disque, en acquérant un verrou si nécessaire.

        Args :
            **kwargs : arguments de mots clés supplémentaires.
        """
        # self.acquire_lock(self.filename())
        # try:
        #     return super().save(**kwargs)
        # finally:
        #     self.release_lock()
        # We should already hold the lock from load()
        if not self.is_locked_by_me() and self.filename():
            self.acquire_lock(self.filename())
        return super().save(**kwargs)

    def mergeDiskChanges(self):
        """
        Fusionnez les modifications du disque avec le fichier de tâches actuel, en acquérant un verrou si nécessaire.
        """
        # self.acquire_lock(self.filename())
        # try:
        #     super().mergeDiskChanges()
        # finally:
        #     self.release_lock()
        # We should already hold the lock from load()
        if not self.is_locked_by_me() and self.filename():
            self.acquire_lock(self.filename())
        super().mergeDiskChanges()
