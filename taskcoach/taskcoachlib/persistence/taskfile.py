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

taskfile.py est le pivot central de l'application :
il fait le lien entre les objets métier (domain), la persistance (XML), et l'interface utilisateur (via les notifications).

1. La Hiérarchie des Responsabilités

Le TaskFile n'est pas qu'un simple gestionnaire de fichiers, il remplit quatre rôles distincts :

    Conteneur de données : Il possède les listes racines (tasks(), efforts(), categories(), etc.).

    Gestionnaire de cycle de vie : Il gère le load(), save(), et close().

    Observateur de changements : Via le Monitor, il sait exactement quel objet a été modifié pour ne sauvegarder que le nécessaire.

    Gestionnaire de conflits : Via mergeDiskChanges, il gère le cas où deux instances ouvrent le même fichier.

2. Le flux de données (Data Flow)

Comprendre comment une modification arrive sur le disque est crucial :

    Modification : Un objet (ex: Effort) est modifié via un setter.

    Notification : L'objet envoie un message PubSub (ex: "pubsub.effort.start").

    Capture : TaskFile intercepte ce message via setNeedSave ou son Monitor.

    Marquage : Le Monitor local (self.__changes) enregistre l'ID de l'objet et l'attribut modifié.

    Persistance : Lors du save(), TaskFile parcourt ces changements pour mettre à jour le XML.
"""

from config import GUI_NAME

# 3. Points clés à surveiller lors de la lecture
#
# Pendant que tu parcours le fichier, prête une attention particulière à ces zones :
#
#     La gestion des Verrous (Locking) : Cherche où les fichiers .lock sont créés. C'est là que fasteners ou lockfile interviennent.
#
#     L'instanciation du Synchroniseur : Regarde comment ChangeSynchronizer est appelé. C'est là que ton dictionnaire local self.__changes doit être passé.
#
#     Le mécanisme de "Dirty bit" : Comment needSave() combine-t-il le flag booléen et l'état du moniteur ?

# TODO : Séparer le fait d'utiliser le fichier en local seul ou partagé avec d'autres !

# Dans ton fichier, plusieurs handlers font uniquement du logging.
# Ils doivent TOUS appeler self.setNeedSave().
# Par exemple, on voit que onTaskChanged_Deprecated fait du logging mais ne marque pas le fichier comme sale.
# Il y a aussi onTaskChanged, onEffortCHanged, onEffortTaskChanged, onCategoryChanged, onNoteChanged, onAttachmentChanged, onDomainObjectChanged.

try:
    import fasteners
except (
    Exception
):  # pragma: no cover - fallback if dependency not installed in test env
    fasteners = None
    # logging not yet configured; we'll still define log below. Avoid raising to keep tests runnable.
import lockfile
import logging
import os
import shutil
import tempfile
from io import TextIOWrapper
import uuid

# import wx
from pubsub import pub

# from lockfile import SoftReadWriteLock

from . import xml
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
    print(
        f"_isCloud : Vérification du chemin '{path}' pour les indicateurs de synchronisation cloud."
    )
    while True:
        for name in [".dropbox.cache", ".csync_journal.db"]:
            if os.path.exists(os.path.join(path, name)):
                print(
                    f"_isCloud : Indicateur de synchronisation cloud trouvé : '{name}' dans '{path}'."
                )
                return True
        path, name = os.path.split(path)
        print(
            f"_isCloud : Chemin actuel '{path}', nom de fichier vérifié '{name}'."
        )
        if name == "":
            print(
                "_isCloud : Aucun indicateur de synchronisation cloud trouvé dans les chemins parents."
            )
            return False
        print(
            f"_isCloud : Aucun indicateur trouvé dans '{path}', remontant au parent..."
        )
        return False


class TaskCoachFilesystemNotifier(FilesystemNotifier):
    """
    Une classe de notification pour gérer les modifications de fichiers pour Task Coach.

    Basé sur FilesystemNotifier qui charge le notificateur selon le système (linux->inotify, win->win32, mac->notifeur)
    ou FileSystemPollerNotifier.
    """

    def __init__(self, taskFile):
        """
        Initialiser le notificateur avec une instance de TaskFile.

        Initialise un notificateur de changement de fichier spécifique à Task Coach,
        en liant un objet TaskFile à surveiller pour détecter les modifications sur le disque.

        Args :
            taskFile (TaskFile) : L'instance de TaskFile à notifier.

        Récupère les méthodes de FilesystemNotifier et surcharge la méthode onFileChanged.
        """
        # Définit l'objet taskFile comme attribut __taskFile de la classe
        self.__taskFile = taskFile
        # super(TaskCoachFilesystemNotifier, self).__init__()
        super().__init__()

    def onFileChanged(self):
        """
        Gérez les modifications de fichiers en notifiant l’instance TaskFile associée.
        """
        self.__taskFile.onFileChanged()
        # log.info(
        print(
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
    Une classe pour écrire des fichiers en toute sécurité,
    en utilisant des fichiers temporaires pour éviter la perte de données.

    Attributes :
        __filename (str) : Le nom du fichier cible.
        __mode (str) : Le mode d'ouverture du fichier (par défaut 'w' pour écriture en texte).
        __fd (file object) : Le descripteur de fichier ouvert pour l'écriture.
        __tempFilename (str) : Le nom du fichier temporaire utilisé pour l'écriture sécurisée.

    Methods :
        __init__ : Initialise le SafeWrite avec un nom de fichier,
                   son mode de lecture/écriture et son type d'encodage.
        name (str) : Retourne le nom du fichier cible (requis par certains writers/loggers).
        mode (str) : Retourne le mode d'ouverture (requis par le logger de ChangesXMLWriter).
        closed (bool) : Indique si le fichier est fermé.
        __enter__ (self) : Permet l'utilisation de 'with SafeWriteFile(...) as fd'.
        __exit__ : Ferme le fichier automatiquement à la fin du bloc 'with'.
        write(bf) : Écrire les données bf dans le fichier __fd.
        close : Fermer le fichier __fd et renommez le fichier temporaire en toute sécurité si nécessaire.
        __moveFileOutOfTheWay(filename) : Déplacer un fichier filename existant en le renommant
                                          avec un suffixe incrémental pour éviter l'écrasement.
        _getTemporaryFileName(path) (name) : Générer un nom de fichier temporaire name dans le répertoire path.
        _isCloud (bool) : (méthode générale) Vérifier si le fichier se trouve dans un répertoire synchronisé avec le cloud.
    """

    # def __init__(self, filename):
    def __init__(self, filename, mode="w", encoding="utf-8"):
        """
        Initialisez le SafeWriteFile avec un nom de fichier.

        Args :
            filename (str) : Le nom de fichier dans lequel écrire.
            mode (str) : Le mode d'ouverture du fichier (par défaut 'w' pour écriture en texte).
            encoding (str) : Le type d'encodage du fichier (par défaut 'utf-8').

        Attributes :
            __filename (str) : Le nom du fichier cible.
            __mode (str) : Le mode d'ouverture du fichier (par défaut 'w' pour écriture en texte).
            __fd (file object) : Le descripteur de fichier ouvert pour l'écriture.
            __tempFilename (str) : Le nom du fichier temporaire utilisé pour l'écriture sécurisée.

        """
        # Si le fichier est destiné à contenir du XML (qui est un format textuel),
        # il est généralement préférable de l'écrire en mode texte avec
        # un encodage spécifique comme UTF-8.
        # Si vous ouvrez le fichier en mode binaire pour l'écriture ('wb'),
        # vous devrez encoder explicitement la chaîne XML en bytes
        # avant de l'écrire (par exemple, tree.write(self.__fd, encoding="utf-8")
        # suivi d'un appel à .encode('utf-8') si tree.write attend un flux binaire).
        # Il faut que le fichier temporaire soit créé dans le même répertoire
        # que le fichier cible pour garantir que le renommage soit atomique et possible.
        log.info("Initialisation de SafeWriteFile avec un nom de fichier.")
        self.__filename = filename
        self.__mode = mode  # On stocke le mode pour le retourner dans la propriété mode, même si on ouvre toujours en 'w' pour du texte.
        # On place le fichier temporaire dans le même dossier que le fichier final
        dirname = os.path.dirname(filename)
        basename = os.path.basename(filename)
        if self._isCloud():
            # Ideally we should create a temporary file on the same filesystem (so that
            # os.rename works) but outside the Dropbox folder...
            # self.__fd = open(self.__filename, "w", encoding="utf-8")
            self.__fd = open(self.__filename, mode, encoding=encoding)
            # self.__tempFilename = ?
        else:
            # self.__tempFilename = self._getTemporaryFileName(
            #     os.path.dirname(filename)
            # )
            self.__tempFilename = os.path.join(
                dirname, f".tmp-{os.getpid()}-{basename}"
            )
            # Création du fichier temporaire avec le chemin complet pour éviter les problèmes de renommage sur certains systèmes de fichiers.
            # self.__fd = open(self.__tempFilename, "w", encoding="utf-8")
            self.__fd = open(self.__tempFilename, mode, encoding=encoding)
        # self.__fd = filename
        log.info(
            "Initialisation de SafeWriteFile avec un nom de fichier."
            f"self.__filename={self.__filename}"
            f"self.__fd={self.__fd}"
            f"self.__tempFilename={self.__tempFilename}"
        )

    @property
    def name(self):
        """Retourne le nom du fichier cible (requis par certains writers/loggers)."""
        return self.__filename

    @property
    def mode(self):
        """Retourne le mode d'ouverture (requis par le logger de ChangesXMLWriter)."""
        return self.__mode

    @property
    def closed(self):
        """Indique si le fichier est fermé."""
        return self.__fd is None or self.__fd.closed

    # Vous devez ajouter les méthodes __enter__ et __exit__ à la classe SafeWriteFile.
    # La méthode __enter__ doit retourner l'instance elle-même,
    # et __exit__ doit s'assurer que le fichier est fermé
    # (ce qui déclenche le renommage sécurisé dans votre logique actuelle).
    def __enter__(self):
        """Permet l'utilisation de 'with SafeWriteFile(...) as fd'."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme le fichier automatiquement à la fin du bloc 'with'."""
        self.close()

    def write(self, bf):
        """
        Écrire les données dans le fichier.

        Args :
            bf (str) : Les données à écrire.
        """
        # Pour rendre votre système plus robuste aux erreurs de type,
        # modifiez la méthode write pour qu'elle intercepte les types invalides
        # avant qu'ils ne fassent planter l'écriture disque :
        if bf is None:
            return

        # The stream is opened in text mode, so we should write strings.
        # La méthode write attend une chaîne de caractères (str) et non des bytes.
        # Si bf est déjà une chaîne de caractères, nous pouvons l'écrire directement.
        # Si bf est un objet XML (comme un ElementTree),
        # nous devons d'abord le convertir en une chaîne de caractères XML avant de l'écrire.
        # # self.__fd.write(str(bf))
        # if isinstance(bf, bytes):
        if self.__fd:
            if isinstance(bf, bytes) and "b" not in self.__mode:
                self.__fd.write(bf.decode("utf-8"))
            elif isinstance(bf, str):
                self.__fd.write(bf)
            else:
                # Si bf n'est pas une chaîne de caractères, essayons de le convertir en XML string.
                # Cela suppose que bf est un objet XML compatible avec xml.etree.ElementTree.tostring()
                # Si c'est un élément XML (Element), on utilise tostring
                try:
                    # On force l'encodage en unicode pour éviter les bytes dans un fichier ouvert en 'w'
                    # xml_string = xml.tostring(bf, encoding="unicode")
                    xml_string = xml.writer.eTree.tostring(
                        str(bf), encoding="unicode"
                    )
                    self.__fd.write(xml_string)
                    # # Si c'est un objet complexe, on tente une conversion propre
                    # self.__fd.write(str(bf))
                except Exception as e:
                    log.error(
                        "SafeWriteFile.write : Impossible d'écrire les données. "
                        f"Erreur : {e}"
                    )
                    raise

    def close(self):
        """
        Fermez le fichier et renommez le fichier temporaire en toute sécurité si nécessaire.
        """
        if self.__fd is None:
            return
        log.info(
            "SafeWriteFile.close : Fermeture du fichier et renommage du fichier temporaire en toute sécurité si nécessaire."
        )
        # if isinstance(self.__fd, TextIOWrapper):
        try:
            self.__fd.close()
        finally:
            self.__fd = None  # On marque comme fermé quoi qu'il arrive

        # Tentative de renommage atomique du fichier temporaire vers le nom final.
        if not self._isCloud():
            # Si le fichier original existe, on le prépare/supprime pour éviter les conflits de renommage.
            # if os.path.exists(self.__filename):
            #     log.info(f"SafeWriteFile.close retire {self.__filename}.")
            #     os.remove(self.__filename)
            # Renommage du temporaire vers le nom final, logique de renommage atomique
            # if self.__filename is not None:  # Peux poser problème
            if os.path.exists(self.__tempFilename):
                # Sur Windows, os.rename n'écrase pas, il faut supprimer la cible avant de renommer le temporaire.
                if os.path.exists(self.__filename):
                    log.info(f"SafeWriteFile.close retire {self.__filename}.")
                    os.remove(self.__filename)
                log.info(
                    f"SafeWriteFile.close utilise __moveFileOutOfTheWay sur {self.__filename} avant de le renommer."
                )
                # WTF ?
                # self.__moveFileOutOfTheWay(self.__filename)
                os.rename(self.__tempFilename, self.__filename)
            else:
                log.error(
                    f"SafeWriteFile.close : Le fichier temporaire {self.__tempFilename} est introuvable !"
                )
        #     log.info(
        #         f"SafeWriteFile.close renomme {self.__tempFilename} en {self.__filename}."
        #     )
        #     os.rename(self.__tempFilename, self.__filename)
        # self.__fd = (
        #     None  # Marquer comme fermé pour éviter les écritures ultérieures
        # )

    def __moveFileOutOfTheWay(self, filename):
        """
        Déplacez un fichier existant en le renommant
        avec un suffixe incrémental pour éviter l'écrasement.

        Args :
            filename (str) : Le nom du fichier à déplacer.
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

        Attributes:

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
    l'enregistrement et la surveillance des modifications dont les fusions de fichiers.

    Structure du modèle dans TaskFile

    La classe TaskFile initialise plusieurs conteneurs de données dans son __init__ :
        - self.__tasks : Une instance de task.TaskList() qui contient la liste principale des tâches.
        - self.__categories : Une instance de category.CategoryList() pour les catégories.
        - self.__efforts : Une instance de effort.EffortList liée aux tâches.

    Ces conteneurs sont les points d'entrée principaux
    pour accéder aux données métier de l'application.

    Attributes :
        - __filename (str) : Le nom du fichier de tâches.
        - __lastFilename (str) : Le dernier nom de fichier utilisé pour le chargement ou la sauvegarde.
        - __needSave (bool) : Signale que la tâche a été modifiée et nécessite une sauvegarde.
        - __loading (bool) : Indique si le fichier est en cours de chargement, évitant des opérations concurrentes.
        - __tasks (task.TaskList) : La liste principale des tâches. *
        - __categories (category.CategoryList) : La liste des catégories. *
        - __notes (note.NoteContainer) : La liste des notes. *
        - __effort (effort.EffortList(self.tasks())) : La liste des efforts liés aux tâches. *
        - __guid (str) : Un identifiant unique pour cette instance de TaskFile.
        - __syncMLConfig (SyncMLConfigNode) : La configuration de synchronisation SyncML pour cette instance.
        - __monitor (ChangeMonitor) : Un moniteur de changements pour suivre les modifications des objets de domaine.
        - __changedOnDisk (bool) : Indique si le fichier a été modifié sur le disque.
        - __notifier (TaskCoachFilesystemNotifier ou TaskCoachFilesystemPollerNotifier) : Un notificateur pour surveiller les changements de fichiers sur le disque.
        - __saving (bool) : Indique si une opération de sauvegarde est en cours, évite les conflits de modification.

    Methods :
        - __init__ : Initialise les conteneurs de données et les mécanismes de surveillance.
        - __str__ : Retourne une représentation sous forme de chaîne du fichier de tâches (le nom du fichier).
        - __contains__ : Vérifie si un élément (tâche, note, catégorie ou effort) appartient à ce fichier de tâches.
        - monitor : Retourne l'instance ChangeMonitor.
        - categories : Obtenez l'instance CategoryList.
        - notes : Obtenez l'instance de NoteContainer.
        - tasks : Obtenez l'instance TaskList (Liste de tâches).
        - efforts : Obtenez l'instance EffortList (Liste des efforts).
        - syncMLConfig : Obtenez la configuration de synchronisation SyncMLConfigNode.
        - guid : Obtenez le GUID du fichier de tâches.
        - changes (dict) : Obtenez le dictionnaire de suivi des changements.
        - setSyncMLConfig : Définissez la configuration de synchronisation SyncMLConfigNode.
        - isEmpty (bool) : Vérifiez si le fichier de tâche est vide (aucune tâche, catégorie, note ou effort).
        - onDomainObjectAddedOrRemoved : Un gestionnaire d'événements pour les objets de domaine ajoutés ou supprimés, qui marque le fichier comme nécessitant une sauvegarde.
        - onTaskChanged : Un gestionnaire d'événements pour les modifications de tâches, qui marque le fichier comme nécessitant une sauvegarde.
        - onTaskChanged_Deprecated : Un gestionnaire d'événements obsolète pour les modifications de tâches, qui marque le fichier comme nécessitant une sauvegarde.
        - onEffortChanged_Deprecated : Un gestionnaire d'événements pour les modifications d'efforts, qui marque le fichier comme nécessitant une sauvegarde.
        - onCategoryChanged_Deprecated : Un gestionnaire d'événements obsolète pour les modifications de catégories, qui marque le fichier comme nécessitant une sauvegarde.
        - onCategoryChanged : Un gestionnaire d'événements pour les modifications de catégories, qui marque le fichier comme nécessitant une sauvegarde.
        - onNoteChanged_Deprecated : Un gestionnaire d'événements obsolète pour les modifications de notes, qui marque le fichier comme nécessitant une sauvegarde.
        - onNoteChanged : Un gestionnaire d'événements pour les modifications de notes, qui marque le fichier comme nécessitant une sauvegarde.
        - onAttachmentChanged : Un gestionnaire d'événements pour les modifications d'attachements, qui marque le fichier comme nécessitant une sauvegarde.
        - onAttachmentChanged_Deprecated : Gestionnaire obsolète pour les événements de modification des pièces jointes.
        - setFilename(filename) : Définissez le nom de fichier du fichier de tâche __filename avec filename.
        - filename() (str): Obtenez le nom de fichier du fichier de tâche __filename.
        - lastFilename() : Obtenez le dernier nom de fichier du fichier de tâche __lastFilename.
        - isDirty() : Retourner __needSave, si le fichier de tâche doit être enregistré.
        - needSave() : Vérifiez et retourner si le fichier de tâche doit être enregistré.
        - setNeedSave(*args, **kwargs) : Méthode de rappel pour marquer le fichier comme devant être sauvegardé.
        - markDirty(force) : Marquer le fichier de tâche comme sale (doit être enregistré).
        - markClean() : Marquez le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré).
        - onFileChanged() : Gérer les modifications de fichiers.
        - changedOnDisk() : Retourner si le fichier de tâche a changé sur le disque.
        - clear(regenerate, event) : Effacer les données du fichier de tâches, en régénérant éventuellement la configuration GUID et SyncML.
        - close() : Fermez le fichier de tâches, en enregistrant toutes les modifications et en effaçant le contenu.
        - stop() : Arrêter le notificateur du système de fichiers.
        - _read(fd) : Lire le fichier de tâches à partir d'un descripteur de fichier fd.
        - _log_duplicate_ids(ids) : Journaliser les ID en double trouvés lors du chargement du fichier de tâches.
        - exists() : Vérifiez si le fichier de tâche existe.
        - _openForWrite(suffix) : Ouvrir le fichier de tâche en écriture et retourne un descripteur de fichier (l'instance SafeWriteFile).
        - _openForRead() : Ouvrez le fichier de tâche pour la lecture binaire et retourne un descripteur de fichier.
        - load(filename) : Chargez le fichier de tâche à partir du disque. Cette méthode lit un fichier XML contenant les tâches, catégories, notes, configurations SyncML et changements précédents. Elle initialise toutes les structures internes de l'objet TaskFile avec ces données. Si le fichier n'existe pas, elle initialise un fichier vide avec une configuration par défaut.
        - _save() : Enregistrez le fichier de tâches sur le disque dans le fichier .tsk.
        - save() : Sauvegarde le fichier TaskCoach sur le disque en ajoutant une protection pour empêcher l'écrasement accidentel d'un fichier contenant des données si le modèle courant est vide.
        - mergeDiskChanges() : Fusionner les modifications du disque avec le fichier de tâches actuel.
        - saveas(filename) : Enregistrer le fichier de tâche sous un nouveau nom de fichier filename.
        - merge(filename) : Fusionner un autre fichier de tâches filename avec celui-ci.
        - objectsToOverwrite(originalObjects, objectsToMerge) (list) : Récupère la liste des objets à écraser lors d'une fusion.
        - rememberCategoryLinks(categoryMap, categorizables) : Enregistrer la liste des categories des objets catégorisables categorizables dans la carte des catégories categoryMap.
        - restoreCategoryLinks(categoryMap) : Restaurer les liens de catégorie à partir de la carte de catégorie mémorisée.
        - beginSync() : Commencez une opération de synchronisation.
        - endSync() : Terminez une opération de synchronisation.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez le fichier TaskFile contenant la liste de tâches.


        Chaque instance de TaskFile possède son propre registre de modifications
        (self.__changes), garantissant l'isolation des données,
        notamment lors des tests unitaires concurrents.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Attributes : (* les conteneurs de données)
            __filename (str) : Le nom de fichier de tâches.
            __lastFilename (str) : Le dernier nom de fichier utilisé pour le chargement ou la sauvegarde.
            __needSave (bool) : Signale que la tâche a été modifiée et nécessite une sauvegarde.
            __loading (bool) : Indique si le fichier est en cours de chargement, évitant des opérations concurrentes.
            __tasks (task.TaskList) : La liste principale des tâches. *
            __categories (category.CategoryList) : La liste des catégories. *
            __notes (note.NoteContainer) : La liste des notes. *
            __effort (effort.EffortList(self.tasks())) : Les listes des efforts des tâches. *
            __guid (str) : Un identifiant unique pour cette instance de TaskFile.
            __syncMLConfig (SyncMLConfigNode) : La configuration de synchronisation SyncML pour cette instance.
            __monitor (ChangeMonitor) : Un moniteur de changements pour suivre les modifications des objets de domaine.
            __changes (dict) : Le dictionnaire de suivi des changements.
            __changedOnDisk (bool) : Indique si le fichier a été modifié sur le disque.
            __notifier (TaskCoachFilesystemNotifier ou TaskCoachFilesystemPollerNotifier) : Un notificateur pour surveiller les changements de fichiers sur le disque.
            __saving (bool) : Indique si une opération de sauvegarde est en cours.


        """
        log.info(
            "Initialisation de TaskFile avec des arguments : %s, %s",
            args,
            kwargs,
        )
        super().__init__(*args, **kwargs)

        # Initialisez les variables d'instance avec des valeurs par défaut
        self.__filename = self.__lastFilename = ""
        # log.info("TaskFile : self.__filename = self.__lastFilename = ''")
        self.__needSave = False
        self.__loading: bool = (
            False  # Indique si le fichier est en cours de chargement, évitant des opérations concurrentes.
        )
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

        # log.info(f"TaskFile : self.__monitor = {self.__monitor}")
        # Identifiant du TaskFile (hérité de ObservableObject)
        # On s'assure d'avoir un GUID unique pour cette instance
        # self.__guid = generate()
        self.__guid = str(uuid.uuid4())
        # log.info(f"TaskFile : self.__guid = {self.__guid}")
        self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        # self.__syncMLConfig = (
        #     None  # SyncML removed - kept for file format compatibility
        # )
        # self.__monitor est une instance locale du ChangeMonitor
        # self.__monitor.guid() est l'identifiant du moniteur qui suit les changements.
        # self.__guid = self.__monitor.guid()
        # log.info(f"TaskFile : self.__syncMLConfig = {self.__syncMLConfig}")
        # self.__monitor = ChangeMonitor()
        # On initialise le moniteur avec ce GUID
        self.__monitor = ChangeMonitor(id_=self.__guid)
        # Le dictionnaire global changes : Il utilise ces GUID comme clés pour stocker les états de modification.
        # On utilise le dictionnaire local pour les besoins internes
        # de suivi des changements, mais il est important que le GUID
        # du moniteur soit enregistré dans ce dictionnaire global
        # pour que les changements soient correctement suivis
        # et que les notifications fonctionnent.
        self.__changes = (
            dict()
        )  # dictionnaire global qui stocke les changements par device/monitor
        # # CRUCIAL : On enregistre le moniteur dans le registre GLOBAL
        # # C'est ce registre que close() essaie de nettoyer.
        # self.__changes[self.__monitor.guid()] = self.__monitor
        # On enregistre le moniteur DANS le dictionnaire local
        self.__changes[self.__guid] = self.__monitor
        # changes[self.__guid] = self.__monitor
        # log.info(f"TaskFile : self.__changes = {self.__changes}")
        # self.__changes et self.__monitor sont maintenant liés par le GUID, ce qui permet de suivre les changements spécifiques à cette instance de TaskFile.
        # Ils sont SYNCHRONISÉS lors de la sauvegarde via mergeDiskChanges()
        self.__changedOnDisk = False
        # if kwargs.pop("poll", True):
        if kwargs.pop("poll", False):
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
        # Il y a 3 handlers différents pour les efforts, les notes et les catégories, car ils sont traités différemment dans le code de sauvegarde (efforts liés aux tâches, notes liées aux tâches, catégories liées à des objets catégorisables).
        # On s'abonne aussi explicitement aux types d'événements définis par la classe Task pour être robuste face à des versions différentes de pubsub ou des conventions de nommage.
        # Ecouter tous les événements de modification d'Effort (couleur, description, start, stop, etc.)

        # ✅ registerObserver avec le handler renommé
        for eventType in effort.Effort.modificationEventTypes():
            self.registerObserver(self.onEffortChanged_Deprecated, eventType)
        # Pour écouter les événements pubsub des efforts (start, stop, etc.)
        # pub.subscribe(self.onEffortChanged_Deprecated, "pubsub.effort")
        # ✅ pub.subscribe avec le nouveau handler
        pub.subscribe(self.onEffortChanged, "pubsub.effort")
        pub.subscribe(
            self.onEffortTaskChanged, effort.Effort.taskChangedEventType()
        )
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
        # Branchement obligatoire pour que needSave() fonctionne correctement, même si les événements de modification de pièce jointe ne sont pas utilisés pour marquer le fichier comme sale.
        # On écoute quand une note est ajoutée à une tâche
        pub.subscribe(self.setNeedSave, "task.notes.added")
        # On écoute aussi les autres changements importants
        pub.subscribe(self.setNeedSave, "task.notes.removed")
        pub.subscribe(self.setNeedSave, "task.notes.modified")
        pub.subscribe(self.setNeedSave, "note.added")
        pub.subscribe(self.setNeedSave, "note.modified")
        # Pour être complet, on peut ajouter les tâches et catégories
        pub.subscribe(self.setNeedSave, "task.added")
        pub.subscribe(self.setNeedSave, "task.modified")
        # AJOUTE CECI pour les efforts :
        pub.subscribe(self.setNeedSave, "effort.start.changed")
        pub.subscribe(self.setNeedSave, "effort.stop.changed")
        pub.subscribe(self.setNeedSave, "effort.duration.changed")
        pub.subscribe(self.setNeedSave, "task.efforts.added")
        pub.subscribe(self.setNeedSave, "task.efforts.removed")
        pub.subscribe(self.setNeedSave, "task.efforts.modified")
        # Pour les dates de l'effort
        pub.subscribe(self.setNeedSave, "pubsub.effort.start")
        # ou
        # pub.subscribe(self.setNeedSave, effort.Effort.startChangedEventType())
        pub.subscribe(self.setNeedSave, "pubsub.effort.stop")
        # pub.subscribe(self.setNeedSave, effort.Effort.stopChangedEventType())
        # Pour le changement de tâche parente de l'effort
        pub.subscribe(self.setNeedSave, "pubsub.effort.task")
        # On s'abonne aussi explicitement aux types d'événements définis
        # par les classes Effort/Task pour être robuste face à des versions
        # différentes de pubsub ou des conventions de nommage.
        # jouter 9 lignes pour écouter les événements d'ajout/suppression d'attachments :
        pub.subscribe(self.setNeedSave, "task.attachments.added")
        pub.subscribe(self.setNeedSave, "task.attachments.removed")
        pub.subscribe(self.setNeedSave, "task.attachments.modified")
        pub.subscribe(self.setNeedSave, "note.attachments.added")
        pub.subscribe(self.setNeedSave, "note.attachments.removed")
        pub.subscribe(self.setNeedSave, "note.attachments.modified")
        pub.subscribe(self.setNeedSave, "category.attachments.added")
        pub.subscribe(self.setNeedSave, "category.attachments.removed")
        pub.subscribe(self.setNeedSave, "category.attachments.modified")
        try:
            pub.subscribe(
                self.setNeedSave, effort.Effort.taskChangedEventType()
            )
        except Exception:
            # ignore if effort not available or event type not defined
            pass
        try:
            pub.subscribe(
                self.setNeedSave, task.Task.effortsChangedEventType()
            )
        except Exception:
            pass

        log.info(
            f"TaskFile.__init__ : TaskFile initialisé avec filename='{self.__filename}', guid='{self.__guid}' et syncMLConfig='{self.__syncMLConfig}'."
        )
        log.info("TaskFile.__init__ : Tâche de base initialisée : %s", self)
        # log.info("TaskFile : Tâches initiales : %s", self.tasks())
        log.info("TaskFile.__init__ : Tâches initiales : %s", self.__tasks)
        log.info(
            "TaskFile.__init__ : Catégories initiales : %s", self.__categories
        )
        # log.info("TaskFile : Notes initiales : %s", self.notes())
        log.info("TaskFile.__init__ : Notes initiales : %s", self.__notes)
        log.info("TaskFile.__init__ : Efforts initiaux : %s", self.__efforts)
        log.info("TaskFile initialisé !")

    def __str__(self):
        """Retourne une représentation sous forme de chaîne du fichier de tâches (le nom du fichier)."""
        # return self.filename()
        return str(self.filename())

    def __contains__(self, item):
        """
        Vérifie si un objet appartient au TaskFile.

        Vérifie si un élément (tâche, note, catégorie ou effort) appartient à ce fichier de tâches.

        Args :
            item : L’objet à rechercher dans le fichier de tâches.

        Returns :
            (bool) : True si l’objet appartient à l’une des collections du fichier de tâches, sinon False.
        """

        # return (
        #     item in self.tasks()
        #     or item in self.notes()
        #     or item in self.categories()
        #     or item in self.efforts()
        # )
        if item in self.__tasks:
            return True

        if item in self.__categories:
            return True

        if item in self.__notes:
            return True

        try:
            if item in self.__efforts:
                return True
        except Exception:
            pass

        return False

    # SURTOUT ne jamais supprimer le monitor lui-même :
    # self.__monitor = None
    # sinon les callbacks PubSub continuent d'exister
    # mais pointent vers un objet cassé.
    #
    # Il faut seulement RESET le monitor.
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

    # # Ils doivent TOUS appeler self.setNeedSave().
    # Il y a onTaskChanged, onEffortChanged, onEffortTaskChanged,
    # onCategoryChanged, onNoteChanged, onAttachmentChanged, onDomainObjectChanged.
    def onDomainObjectAddedOrRemoved(self, event):  # pylint: disable=W0613
        """
        Gérer les événements ajoutés ou supprimés des objets de domaine.

        Args :
            event (Event) : L'événement.
        """
        # TODO : à revoir !
        if self.__loading or self.__saving:
            self.setNeedSave()
            return
        self.markDirty()
        self.setNeedSave()

    def onTaskChanged(self, newValue, sender):
        """
        Gestionnaire des modifications de tâche.

        Listener pour Gérer les événements modifiés par la tâche.

        Utilisé avec pubsub pour recevoir les messages.

        Args :
            newValue : La nouvelle valeur.
            sender (task) : La tâche qui a changé (l'expéditeur).
        """
        if self.__loading or self.__saving:
            self.setNeedSave()
            return
        if sender in self.tasks():
            self.markDirty()
        self.setNeedSave()

    def onTaskChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de tâche obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            self.setNeedSave()
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
        self.setNeedSave()

    # Pour les événements de modification d'effort, nous devons être plus prudents car un effort peut être lié à une tâche qui n'est pas dans ce fichier de tâches, ou il peut être lié à une tâche qui est dans ce fichier de tâches. Nous devons vérifier les deux cas.
    # Pour registerObserver(ancien), nous devons nous assurer que nous écoutons les événements de modification d'effort pour tous les efforts, pas seulement ceux qui sont actuellement liés à des tâches dans ce fichier de tâches, car un effort peut être créé ou modifié avant d'être lié à une tâche.
    def onEffortChanged_Deprecated(self, event):
        """
        Gérer les événements modifiés par l'effort.

        Args :
            event (Event) : L'événement.
        """
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: event=%s" % event
        )  # Debug print
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: event.values()=%s"
            % list(event.values())
        )  # Debug print
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: event.sourcesAndValuesByType()=%s"
            % list(event.sourcesAndValuesByType().items())
        )  # Debug print
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: event.sources()=%s"
            % list(event.sources())
        )  # Debug print
        # Avoid indexing into a set returned by event.sources()
        first_source = next(iter(event.sources()), None)
        print(
            # "ChangeMonitor.onChildRemoved: event.values(source=event.sources()[0])=%s"
            # % list(event.values(source=event.sources()[0]))
            "ChangeMonitor.onEffortChanged_Deprecated: event.values(source=first_source)=%s"
            % list(event.values(source=first_source))
        )  # Debug print
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: repr(self.__changes)=%s"
            % repr(self.__changes)
        )  # Debug print
        if self.__loading or self.__saving:
            print(
                "ChangeMonitor.onEffortChanged_Deprecated: Ignoring event because loading or saving is in progress."
            )  # Debug print
            self.setNeedSave()
            return
        changedEfforts = [
            changedEffort
            for changedEffort in event.sources()
            if changedEffort.task() in self.tasks()
        ]
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: changedEfforts=%s"
            % changedEfforts
        )  # Debug print
        if changedEfforts:
            self.markDirty()
            for changedEffort in changedEfforts:
                changedEffort.markDirty()
        self.setNeedSave()
        print(
            "ChangeMonitor.onEffortChanged_Deprecated: Finished processing event !"
        )  # Debug print

    # Pour pub.subscribe(nouveau), nous devons nous assurer que nous écoutons les événements de modification d'effort pour tous les efforts, pas seulement ceux qui sont actuellement liés à des tâches dans ce fichier de tâches, car un effort peut être créé ou modifié avant d'être lié à une tâche. Cependant, pour éviter de marquer le fichier comme sale pour des efforts qui ne sont pas liés à des tâches dans ce fichier de tâches, nous devons vérifier si l'effort modifié est lié à une tâche dans ce fichier de tâches avant de marquer le fichier comme sale.
    # def onEffortChanged(self, newValue, sender):
    def onEffortChanged(self, **kwargs):
        """
        Gère le changement de tâche d'un effort via PyPubSub.

        Cette méthode est appelée lorsque l'effort change de tâche
        associée.

        Args:
            newValue: Nouvelle tâche associée à l'effort.
            sender: Instance Effort ayant changé.
        """
        # Ignore les notifications pendant chargement/sauvegarde
        if self.__loading or self.__saving:
            self.setNeedSave()
            return
        sender = kwargs.get("sender")  # Peut être None !
        if sender:
            if sender.task() in self.tasks():
                # Marque le fichier comme modifié
                self.markDirty()
        else:
            # taskChangedEventType() ne passe pas de sender
            self.markDirty()
        self.setNeedSave()

    def onEffortTaskChanged(self, *args, **kwargs):
        """
        Gestionnaire du changement de tâche d'un effort.

        Réagit au changement de tâche d'un effort.

        Args:
            kwargs : Arguments envoyés par PubSub.
        """
        # Ignore les notifications pendant chargement/sauvegarde
        if self.__loading or self.__saving:
            self.setNeedSave()
            return

        # Marque le fichier comme modifié
        self.markDirty()
        self.setNeedSave()

    def onCategoryChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de catégorie obsolète.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading or self.__saving:
            self.setNeedSave()
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
        self.setNeedSave()

    def onCategoryChanged(self, newValue, sender):
        """
        Gérer les événements de modification de catégorie.

        Args :
            newValue : la nouvelle valeur.
            sender (Category) : la catégorie qui a changé.
        """
        if self.__loading or self.__saving:
            self.setNeedSave()
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
        self.setNeedSave()

    def onNoteChanged_Deprecated(self, event):
        """
        Gérer les événements de modification de note obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            self.setNeedSave()
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        for changedNote in event.sources():
            changedNote.markDirty()
        self.setNeedSave()

    def onNoteChanged(self, newValue, sender):
        """
        Gérer les événements de modification de note.

        Args :
            newValue : la nouvelle valeur.
            sender (Note) : la note qui a changé.
        """
        if self.__loading:
            self.setNeedSave()
            return
        # A note may be in self.notes() or it may be a note of another
        # domain object.
        self.markDirty()
        sender.markDirty()
        self.setNeedSave()

    def onAttachmentChanged(self, newValue, sender):
        """
        Gérer les événements de modification de la pièce jointe.

        Args :
            newValue : la nouvelle valeur.
            sender (Attachment) : la pièce jointe qui a changé.
        """
        if self.__loading or self.__saving:
            self.setNeedSave()
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Nous supposons que ce soit le cas.
        self.markDirty()
        self.setNeedSave()

    def onAttachmentChanged_Deprecated(self, event):
        """
        Gérer les événements de modification des pièces jointes obsolètes.

        Args :
            event (Event) : L'événement.
        """
        if self.__loading:
            self.setNeedSave()
            return
        # Les pièces jointes ne connaissent pas leur propriétaire, nous ne pouvons donc pas vérifier si la pièce jointe
        # se trouve réellement dans le fichier de tâches. Supposons que ce soit le cas.
        self.markDirty()
        for changedAttachment in event.sources():
            changedAttachment.markDirty()
        self.setNeedSave()

    #
    def setFilename(self, filename):
        """
        Définissez le nom de fichier du fichier de tâche.

        Args :
            filename (str) : Le nom de fichier à définir.
        """
        if filename == self.__filename:
            # if filename == self.filename():
            return

        # self.__lastFilename = filename or self.__filename
        # # self.__lastFilename = filename or self.filename()
        if filename != "":
            self.__lastFilename = filename
        elif self.__filename != "":
            self.__lastFilename = self.__filename
        self.__filename = filename
        self.__notifier.setFilename(filename)
        pub.sendMessage("taskfile.filenameChanged", filename=filename)
        # log.info(
        print(
            f"TaskFile.setFilename : Nom de fichier défini sur : {filename}, lastFilename={self.__lastFilename}."
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

    # TODO : A nettoyer, risques de doublons entre isDirty() et needSave() !
    def isDirty(self):
        """
        Retourner __needSave, si le fichier de tâche doit être enregistré.

        Returns :
            (bool) : True si le fichier de tâche doit être enregistré, False sinon.
        """
        log.debug("Vérification de l'état 'dirty' : %s", self.__needSave)

        return self.__needSave

    # Diagnostic logique :
    #   TaskFile.needSave() combine deux choses :
    #       le flag booléen __needSave (mis à True par certains listeners),
    #       ET l'existence de changements enregistrés par le ChangeMonitor local : code initialement faisait monitor_has_changes = any(self.__monitor.allChanges().values()).
    #   Donc pour que needSave() soit True il faut soit __needSave == True, soit que self.__monitor.allChanges() contienne au moins un ensemble non vide.
    #   Lors de l'ajout d'un enfant, le moniteur doit normalement :
    #       recevoir l'événement d'ajout (registered pour addChildEventType()),
    #       dans onChildAdded appeler _objectsAdded(event) puis ajouter "parent" dans l'ensemble de changement pour les enfants concernés.
    #   Si monitor_has_changes reste False, cela signifie que, dans ton run, le monitor n'a pas enregistré de changement ou que le changement est dans une structure différente (par ex. dans le dictionnaire global TaskFile.__changes mais pas dans le ChangeMonitor._changes local).

    # J'ai proposé et appliqué un correctif conservatif dans TaskFile.needSave() (fichier modifié : taskfile.py) : en plus de vérifier self.__monitor.allChanges(), la méthode examine maintenant aussi (en fallback) le dictionnaire self.__changes (le registre global qui peut contenir des mappings provenant d'autres moniteurs ou du disque) pour détecter si quelque chose de non vide y est enregistré. Le but est d'éviter l'échec du test si les changements sont présents ailleurs que dans le moniteur local.
    # Le patch est prudent : il essaie de détecter plusieurs formats possibles (valeurs dict, objets ayant allChanges(), ou autres truthy). Il ignore les erreurs d'introspection et continue.
    def needSave(self):
        """
        Indique si le fichier doit être sauvegardé.

        Vérifier et retourner si le fichier de tâche doit être enregistré.

        Returns :
            bool : True si le fichier de tâche doit être enregistré, si des changements existent. False sinon.
        """
        # print(
        #     f"TaskFile.needSave : Retourne __loading={self.__loading} et __needSave={self.__needSave}."
        # )
        # On vérifie le drapeau manuel ET le moniteur local pour déterminer si une sauvegarde est nécessaire.
        # Si le flag direct indique une modification
        if self.__needSave:
            return True
        # Vérifie aussi le ChangeMonitor
        # ChangeMonitor.getChanges(obj) nécessite un argument obj. Ce qui intéresse
        # ici, c'est simplement de savoir si le moniteur contient des changements
        # non vides. Utilisons allChanges() et testons s'il existe au moins un
        # ensemble de changements truthy.
        # # # monitor_has_changes = any(self.__monitor.allChanges().values())  # souci ici : allChanges() retourne un dict de type {id: changeset}, et on veut savoir si au moins un changeset est non vide. Donc on doit faire any(changeset for changeset in self.__monitor.allChanges().values()) ou any(self.__monitor.allChanges().values()) si les changesets sont eux-mêmes des structures qui évaluent à False quand elles sont vides.
        # # monitor_has_changes = any(
        # #     changeset for changeset in self.__monitor.allChanges().values()
        # # )
        # monitor_has_changes = any(
        #     self.__monitor.allChanges()
        # )  # Fonctionne TODO : vérifier que les changesets vides sont bien évalués à False, sinon faire any(changeset for changeset in self.__monitor.allChanges().values()).
        # Vérifie aussi le ChangeMonitor
        try:
            changes = self.__monitor.allChanges()

            # allChanges() retourne généralement un dict
            if changes:
                return any(bool(value) for value in changes.values())

        except Exception as e:
            log.error(
                "TaskFile.needSave : erreur lors de la lecture du monitor : %s",
                e,
                exc_info=True,
            )

        # # print(
        # #     f"TaskFile.needSave : monitor_has_changes={monitor_has_changes} (self.__monitor.allChanges()={self.__monitor.allChanges()})"
        # # )  # Debug print
        # # Ajout d'un log détaillé pour aider à comprendre pourquoi needSave() retourne ce qu'elle retourne, en particulier dans les cas où les changements sont détectés ou pas.
        # log.debug(
        #     f"TaskFile.needSave : Détection des changements: "
        #     f"__needSave={self.__needSave}, "
        #     f"monitor_has_changes={monitor_has_changes}, "
        #     f"allChanges={list(self.__monitor.allChanges().keys())}"
        # )

        # # Ajout d'un fallback qui inspecte aussi le dictionnaire global
        # # self.__changes si le moniteur local ne rapporte rien.
        # # (objectif : mieux détecter des cas où les changements
        # # sont enregistrés ailleurs)
        # # Fallback: the global __changes dict may contain change-registries
        # # coming from other monitors (or from disk). Be robust and also
        # # consider those when deciding whether we need to save. This handles
        # # cases where the local monitor didn't record changes (for example
        # # due to an edge-case in event propagation) but the global changes
        # # structure does contain non-empty change sets.
        # # Si monitor_has_changes est déjà True, pas besoin de faire le fallback. Sinon, on inspecte self.__changes.
        # if not monitor_has_changes and hasattr(self, "_TaskFile__changes"):
        #     for val in list(self.__changes.values()):
        #         # On essaie d'introspecter la valeur pour voir
        #         # si elle contient des changements non vides.
        #         # On considère plusieurs formats possibles :
        #         #   un dict de changements,
        #         #   un objet ayant une méthode allChanges(),
        #         #   ou toute autre valeur truthy.
        #         # Si on trouve quelque chose qui indique des changements,
        #         # on marque monitor_has_changes comme True et on arrête.
        #         try:
        #             # dict-like mapping of id -> changeset
        #             if isinstance(val, dict):
        #                 if any(val.values()):
        #                     monitor_has_changes = True
        #                     break
        #             # ChangeMonitor-like object
        #             elif hasattr(val, "allChanges"):
        #                 try:
        #                     if any(val.allChanges().values()):
        #                         monitor_has_changes = True
        #                         break
        #                 except Exception:
        #                     pass
        #             # other truthy value
        #             else:
        #                 if val:
        #                     monitor_has_changes = True
        #                     break
        #         except Exception:
        #             # Be conservative: if introspection fails, ignore and
        #             # continue checking other entries.
        #             continue
        # # print(
        # #     f"TaskFile.needSave : Retourne not __loading={self.__loading} ou __saving={self.__saving} et __needSave={self.__needSave} ou monitor_has_changes={monitor_has_changes}."
        # # )
        # # # return (
        # # #         not(self.__loading or self.__saving) and self.__needSave
        # # # ) or monitor_has_changes
        # # return (not self.__loading or not self.__saving) and (
        # #     self.__needSave or monitor_has_changes
        # # )
        # result = (not self.__loading or not self.__saving) and (
        #     self.__needSave or monitor_has_changes
        # )
        # log.debug(
        #     f"TaskFile.needSave : Retourne {result} "
        #     f"(__loading={self.__loading}, __saving={self.__saving}, "
        #     f"__needSave={self.__needSave}, monitor_has_changes={monitor_has_changes})"
        # )
        # return result
        return False
        # # Au lieu de chercher dans le "changes" global :
        # # On regarde si notre moniteur local a enregistré des modifications
        # # return self.__monitor.hasChanges() or self.__needSave

    def setNeedSave(self, *args, **kwargs):
        """Méthode de rappel pour marquer le fichier comme devant être sauvegardé.

        Callback utilisé par les événements de domaine.
        """
        # Ajout d'un log explicite pour faciliter le débogage des tests qui
        # vérifient si les changements d'effort (par ex. changement de tâche)
        # sont bien détectés et marquent le TaskFile comme devant être sauvegardé.
        log.debug(
            f"TaskFile.setNeedSave : appelé avec args={args} kwargs={kwargs} | __loading={self.__loading} __needSave={self.__needSave}"
        )
        # if (
        #     not self.__loading
        # ):  # On ne veut pas passer à True pendant le chargement
        if self.__loading:
            return
        self.__needSave = True
        log.debug(
            f"TaskFile.setNeedSave : Valeurs en Sortie : __loading={self.__loading} et __needSave={self.__needSave}."
        )

    def markDirty(self, force=False):
        """
        Marquer le fichier de tâche comme sale (doit être enregistré).

        Args :
            force (bool) : (optional) S'il faut forcer le marquage comme sale. La valeur par défaut est False.
        """

        if force or not self.__needSave:
            self.__needSave = True
            pub.sendMessage("taskfile.dirty", taskFile=self)
            log.debug("Modification détectée, état 'dirty' mis à jour à True")
            log.debug(f"Le fichier {self} est marqué comme modifié")

    def markClean(self):
        """
        Marquez le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré).
        """
        # if self.__needSave:
        log.info(
            "TaskFile.markClean : Marque le fichier de tâches comme propre (n'ayant pas besoin d'être enregistré)."
        )
        self.__needSave = False
        pub.sendMessage("taskfile.clean", taskFile=self)

    def clearChangeMonitor(self):
        """
        Vider le ChangeMonitor après une sauvegarde réussie.

        Cette méthode synchronise le drapeau __needSave avec l'état réel du ChangeMonitor.
        Elle doit être appelée à la fin de _save() pour éviter une boucle infinie de
        sauvegarde où needSave() retournerait toujours True en détectant les anciens
        changements dans le moniteur.

        Cette méthode synchronise l'état du ChangeMonitor avec __needSave.
        Après une sauvegarde réussie, le moniteur doit être réinitialisé
        pour que needSave() retourne False correctement.

        Le problème :
        - _save() met __needSave à False ✅
        - Mais ne vide jamais le ChangeMonitor 🔴
        - Donc needSave() voit toujours des changements et retourne True 🔁
        - Boucle infinie !

        La solution :
        - Après sauvegarde réussie, vider aussi le ChangeMonitor
        - needSave() retournera False correctement
        - Cycle de sauvegarde normal
        """
        if not self.__needSave:  # Seulement si sauvegarde réussie
            log.debug(
                "TaskFile.clearChangeMonitor : Vide le ChangeMonitor après sauvegarde"
            )

            try:
                # Après une sauvegarde réussie, ne pas complètement réinitialiser
                # le moniteur (reset()), car cela supprime toutes les entrées
                # et fait que getChanges(obj) renvoie None. Les tests attendent
                # que, après une sauvegarde, les objets connus restent présents
                # dans le registre avec un ensemble vide de changements.
                # Donc, utiliser resetAllChanges() qui met les ensembles de
                # changements existants à set() tout en conservant les clés
                # (sauf pour les objets marqués __del__ qui sont supprimés).
                if hasattr(self.__monitor, "resetAllChanges"):
                    self.__monitor.resetAllChanges()
                    log.debug(
                        "TaskFile.clearChangeMonitor : resetAllChanges() appelé"
                    )
                else:
                    # Fallback raisonnable si l'implémentation du moniteur
                    # ne fournit pas resetAllChanges(). Dans ce cas, on
                    # appelle reset() comme auparavant.
                    self.__monitor.reset()
                    log.debug("TaskFile.clearChangeMonitor : reset() appelé")
            except Exception as e:
                log.error(
                    f"TaskFile.clearChangeMonitor : Erreur lors du vidage du moniteur: {e}",
                    exc_info=True,
                )
        # Pourquoi pas nettoyer self.__changes ?
        # Parce que :
        #   Persiste entre les sessions - Contient l'historique
        #   Fusionné au chargement - Via mergeDiskChanges()
        #   Multi-device - Peut contenir des changements d'autres devices
        #   Sûr - Si on le nettoie par erreur, les données sur disque sont toujours là
        #   Non-problématique - Il n'affecte pas needSave() directement

    def onFileChanged(self):
        """
        Gérer les modifications du fichier.
        """
        # Si une opération de sauvegarde n'est pas en cours :
        if not self.__saving:
            # import wx  # Not really clean but we're in another thread...
            # Indiquer que le fichier a été modifié sur le disque.
            self.__changedOnDisk = True
            log.debug("TaskFile.onFileChanged : Appelle CallAfter.")
            if GUI_NAME == "wx":
                import wx

                wx.CallAfter(
                    pub.sendMessage, "taskfile.changed", taskFile=self
                )
            elif GUI_NAME == "tk":
                pub.sendMessage("taskfile.changed", taskFile=self)
            log.debug("TaskFile.onFileChanged : CallAfter passé avec succès.")

    def changedOnDisk(self):
        """
        Retourner si le fichier de tâche a changé sur le disque.

        Returns :
            bool : True si le fichier de tâche a changé sur le disque, False sinon.
        """
        return self.__changedOnDisk

    @patterns.eventSource
    def clear(self, regenerate=True, event=None):
        """
        Effacez le fichier de tâches, en régénérant éventuellement la configuration GUID et SyncML.

        Args :
            regenerate (bool, optional) : s'il faut régénérer la configuration GUID et SyncML. La valeur par défaut est True.
            event (Event, optional) : L'événement. La valeur par défaut est Aucun.
        """
        log.info(
            f"taskFile.clear : Appelé : Effacement du contenu du fichier de tâches {self}(clear)"
        )
        # Le problème vient du fait que TaskFile.load() appelle self.clear(). TaskFile.load() envoie un message taskfile.aboutToRead qui fige ("freeze") l'interface (le Viewer) pour éviter les mises à jour pendant le chargement. Cependant, self.clear() envoie ensuite taskfile.aboutToClear (qui fige à nouveau, compteur=2) puis taskfile.justCleared (qui dégèle, compteur=1).
        # Si le Viewer rate le message aboutToClear (ou s'il n'y est pas abonné correctement), mais reçoit justCleared, il va décrémenter son compteur de gel. Si le compteur tombe à 0 alors que le chargement n'est pas fini, le Viewer se rafraîchit et affiche des données incomplètes, ce qui ralentit tout et provoque cet effet "d'interception".
        # Pour corriger cela, nous devons empêcher clear() d'envoyer ses messages de notification si nous sommes déjà en train de charger un fichier (self.__loading est True). Le chargement gère déjà son propre cycle de gel/dégel.
        if not self.__loading:
            # Lors d'un chargement (load) : self.__loading est Vrai. clear() nettoie les listes mais n'envoie pas les messages aboutToClear et justCleared. Le Viewer reste gelé par le aboutToRead envoyé au début du load, et ne se réveillera qu'à la fin du load (sur justRead).
            # 2.
            # Lors d'une fermeture (close) : self.__loading est Faux. clear() envoie les messages normalement, permettant au Viewer de se mettre à jour (se vider) correctement.
            pub.sendMessage("taskfile.aboutToClear", taskFile=self)
        try:
            self.tasks().clear(event=event)
            self.categories().clear(event=event)
            self.notes().clear(event=event)
            if regenerate:
                # self.__guid = generate()
                self.__guid = str(uuid.uuid4())
                # self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
                self.__syncMLConfig = None
        finally:
            if not self.__loading:
                pub.sendMessage("taskfile.justCleared", taskFile=self)

    def close(self):
        """
        Fermez le fichier de tâches, en enregistrant toutes les modifications
        et en effaçant le contenu.

        Ferme le fichier de tâches et nettoie complètement l'état.
        """
        # log.info(
        print(
            "TaskFile.close Ferme le fichier de tâches, en enregistrant toutes les modifications et en effaçant le contenu."
        )
        # 1. On récupère l'identifiant unique du moniteur
        # (C'est lui qui sert de clé dans les registres de changements)
        monitor_id = self.__monitor.guid()
        if os.path.exists(self.filename()):
            # changes = xml.ChangesXMLReader(self.filename() + ".delta").read()
            try:
                # log.debug(
                print(
                    f"TaskFile.close : Essaie de lire le fichier {self.filename()}.delta en mode r et d'enregistrer les changements précédents."
                )
                # with open(self.filename() + ".delta", "r") as f:
                with open(self.filename() + ".delta", "rb") as f:
                    changes = xml.ChangesXMLReader(f).read()
                    # log.debug(f"TaskFile.close : lit changes = {changes}")
                    print(f"TaskFile.close : lit changes = {changes}")
            except FileNotFoundError as e:
                # log.exception(
                print(
                    f"TaskFile.close : Le fichier {self.filename()}.delta n'existe pas : {e}."
                )
                changes = {}
            # Ensure we don't KeyError if the guid isn't present in the delta changes
            changes.pop(self.__monitor.guid(), None)
            # log.debug(
            print(
                f"TaskFile.close : Essaie d'écrire les changements {changes} dans le fichier {self.filename()}.delta en mode wb."
            )
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "wb")).write(
            #     changes
            # )
            # xml.ChangesXMLWriter(open(self.filename() + ".delta", "w")).write(
            #     changes
            # )
            # with open(self.filename() + ".delta", "wb") as f:
            with open(self.filename() + ".delta", "w+b") as f:
                writer = xml.ChangesXMLWriter(f)
                writer.write(changes)
        # garder __lastFilename en mémoire
        lastFilename_to_end = self.__lastFilename
        # self.__lastFilename = self.filename()
        # Il ne faut pas vider filename pour pouvoir le relancer !
        # log.info("TaskFile.close règle filename sur ''")
        print("TaskFile.close règle filename sur ''")
        self.setFilename("")
        # # self.__guid = generate()
        # # self.__guid = str(uuid.uuid4())
        # guid = self.__monitor.guid()
        # if guid in changes:
        #     del changes[guid]

        # # 2. Nettoyage du registre GLOBAL (celui qui causait le KeyError)
        # # On vérifie l'existence avant de supprimer
        # if monitor_id in changes:
        #     del changes[monitor_id]
        # elif hasattr(self, "__guid") and self.__guid in changes:
        #     # Sécurité si enregistré sous le GUID du TaskFile au lieu du moniteur
        #     del changes[self.__guid]
        # Nettoyage du dictionnaire local
        try:
            if self.__guid in self.__changes:
                del self.__changes[self.__guid]
        except Exception:
            # log.exception("Erreur nettoyage __changes")
            print("Erreur nettoyage __changes")
        # On nettoie uniquement ce qui appartient à cette instance
        if hasattr(self, "_TaskFile__changes"):
            self.__changes.clear()
            # log.debug(
            print(f"TaskFile.close : Registre local {self.__guid} nettoyé.")
        # self.clear()

        # reset monitor
        # On peut aussi arrêter le moniteur pour qu'il ne reçoive plus de notifs
        if hasattr(self, "_TaskFile__monitor"):
            self.__monitor.reset()  # Si ton monitor a une méthode stop

        self.markClean()
        self.__changedOnDisk = False
        # Vide les collections
        self.__tasks.clear()
        self.__categories.clear()
        self.__notes.clear()
        self.__efforts.clear()

        self.__lastFilename = (
            lastFilename_to_end  # Récupération du nom du dernier fichier
        )
        self.__needSave = False
        self.__loading = False
        # log.debug("TaskFile.close terminé avec succès.")
        print("TaskFile.close terminé avec succès.")

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
            f"TaskFile._read essaie de lire le fichier de tâche à partir d'un descripteur fd {fd}."
        )
        self.__loading = True
        try:
            reader = xml.XMLReader(fd)
            # data_read = xml.XMLReader(fd).read()
            data_read = reader.read()
            duplicate_ids = reader.get_duplicate_ids()
            log.debug(f"TaskFile._read renvoi : {data_read}, {duplicate_ids}.")
            tasks, categories, notes, syncMLConfig, changes, efforts = (
                data_read
            )
            log.debug("TaskFile._read renvoi : DEBUG LECTURE XML")
            log.debug(f"  tâches lues      : {len(tasks)}")
            log.debug(f"  catégories lues  : {len(categories)}")
            log.debug(f"  notes lues       : {len(notes)}")
            log.debug(f"  efforts lus      : {len(efforts)}")

            # # Le viewer est créé avant que les catégories soient chargées, donc il affiche une liste vide.
            # # Dans ce cas il faut appeler :
            # self.refresh()  # après le chargement du fichier dans taskfile.py. Sauf que refresh() n'existe pas !

            for c in categories[:5]:
                log.debug(
                    f"  CAT id={c.id()} subject={c.subject()} parent={c.parent()}"
                )
        finally:
            self.__loading = False
        return data_read, duplicate_ids

    def _log_duplicate_ids(self, duplicate_ids):
        """Log duplicate IDs found in the task file.
        Journaliser les ID en double trouvés lors du chargement du fichier de tâches.

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
        Vérifier si le fichier de tâche existe.

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
        Ouvrir le fichier de tâche en écriture et retourne un descripteur de fichier.

        Args :
            suffix (str) : (facultatif) Le suffixe du fichier. La valeur par défaut est "".

        Returns :
            SafeWriteFile : l'instance SafeWriteFile.
        """
        log.info(
            f"TaskFile._openForWrite : Essaie d'ouvrir le fichier de tâche {self.__filename + suffix} en écriture."
        )
        return SafeWriteFile(self.__filename + suffix)

    def _openForRead(self):
        """
        Ouvrez le fichier de tâche pour la lecture.

        Returns :
            Le descripteur de fichier à lire.
        """
        # return file(self.__filename, 'r')
        log.info(
            f"TaskFile._openForRead : Ouvre {self.__filename} en mode lecture binaire (rb) !"
        )
        # return open(self.__filename, "r", encoding="utf-8")
        return open(
            self.__filename, "rb"
        )  # XMLReader expects a binary file object
        # Attention : ouvrir en mode texte avec un encodage spécifique
        # (comme UTF-8) est généralement préférable pour les fichiers XML,
        # mais cela dépend de la manière dont XMLReader lit le fichier.
        # Si XMLReader attend un flux binaire,
        # alors ouvrir en mode binaire est correct.
        # Assurez-vous que XMLReader est compatible avec le mode d'ouverture choisi.
        # Nécessite de changer les lignes avec search dans xml.reader.read et has_broken_lines
        # pour rechercher des lignes de bytes plutôt que des chaînes str.
        #

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
        # C'EST CETTE METHODE QUI EST SUPER IMPORTANTE !!!
        log.info(
            f"TaskFile.load : Début du chargement du fichier de tâches filename='{filename}' à partir du disque. load sur self id {id(self)}."
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
                # fd = self._openForRead()
                with self._openForRead() as fd:
                    log.info(
                        f"TaskFile.load : fd={fd} ouvert en mode lecture binaire !"
                    )
                    try:
                        (
                            tasks,
                            categories,
                            notes,
                            syncMLConfig,
                            changes,
                            guid,
                        ), duplicate_ids = self._read(fd)
                        # Vérifie directement la hiérarchie reconstruite par XMLReader avant toute manipulation de TaskFile.
                        print(
                            "TaskFile.load : APRÈS _read :",
                            [
                                (
                                    n.subject(),
                                    n.id(),
                                    id(n),
                                    [
                                        child.subject()
                                        for child in n.children()
                                    ],
                                )
                                for n in notes
                            ],
                        )
                        print(
                            f"TaskFile.load : Données lues : tasks={tasks}, categories={categories}, notes={notes}, syncMLConfig={syncMLConfig}, changes={changes}, guid={guid}"
                        )
                        print(
                            "taskFile.load : Après chargement fichier, nb tâches: %s",
                            len(tasks),
                        )

                    # finally:
                    #     fd.close()
                    except Exception:
                        log.exception(
                            "TaskFile.load : Erreur lors de la lecture du fichier principal '%s'",
                            self.filename(),
                        )
                        raise
                    fd.close()
                # Log any duplicate IDs found in the file
                if duplicate_ids:
                    self._log_duplicate_ids(duplicate_ids)
            else:
                print(
                    f"TaskFile.load : Le fichier {filename} n'existe pas, initialisation d'un fichier de tâches vide."
                )
                tasks = []
                categories = []
                notes = []
                changes = dict()
                # guid = generate()
                guid = str(uuid.uuid4())
                # syncMLConfig = createDefaultSyncConfig(guid)
            print(
                f"TaskFile.load : tasks={tasks}, categories={categories}, notes={notes}, changes={changes}, guid={guid}"
            )
            self.clear()
            self.__monitor.reset()
            self.__changes = changes
            self.__changes[self.__monitor.guid()] = self.__monitor
            # self.categories().extend(categories)  # <- seulement les racines
            # Version corrigée pour ne passer que les catégories sans parent :
            root_categories = [c for c in categories if c.parent() is None]
            self.categories().extend(root_categories)
            # Cela empêche l'injection à plat des sous-catégories dans la CategoryList,
            # qui doivent être accessibles uniquement via la hiérarchie de leur parent.
            log.debug(
                f"TaskFile.load : Après extend : self.categories()={self.categories()}"
            )
            for cat in self.categories():
                log.debug(
                    f"TaskFile.load : AFTER EXTEND: {cat.subject()} parent={cat.parent()}"
                )
            # Protection contre les erreurs d'observateurs lors de l'ajout
            try:
                # Affiche la hiérarchie reçue directement du XMLReader avant toute insertion.
                print(
                    "TaskFile.load : AVANT self.notes().extend(notes) :",
                    [
                        (
                            n.subject(),
                            n.id(),
                            id(n),
                            [child.subject() for child in n.children()],
                            [child.id() for child in n.children()],
                        )
                        for n in notes
                    ],
                )

                # Ajoute les tâches lues dans le conteneur des tâches.
                self.tasks().extend(tasks)

                # Ajoute les notes lues dans le conteneur des notes.
                self.notes().extend(notes)

                # Récupère les notes racines après insertion.
                root_notes = self.notes().rootItems()

                # Affiche la hiérarchie immédiatement après l'insertion dans NoteContainer.
                print(
                    "TaskFile.load : APRÈS self.notes().extend(notes) :",
                    [
                        (
                            n.subject(),
                            n.id(),
                            id(n),
                            [child.subject() for child in n.children()],
                            [child.id() for child in n.children()],
                        )
                        for n in root_notes
                    ],
                )

            except Exception as e:
                print(
                    f"TaskFile.load : Erreur lors de l'extension des tâches/notes, vérifiez les observateurs : {e}"
                )
                log.error(
                    f"TaskFile.load : Erreur lors de l'extension des tâches/notes, vérifiez les observateurs : {e}",
                    exc_info=True,
                )
                # raise
            print(
                f"TaskFile.load : Après extension, {len(self.tasks())} tasks={self.tasks()}, {len(self.categories())} categories={self.categories()}, {len(self.notes())} notes={self.notes()}"
            )
            log.debug(
                f"TaskFile.load : DEBUG categories internes: {len(self.__categories)}"
            )
            log.debug(
                f"TaskFile.load : DEBUG categories viewer: {len(self.categories())}"
            )

            def registerOtherObjects(objects):
                # def registerOtherObjects(objects, task_module, note_module=note, attachment_module=attachment, effort_module=effort):
                """Enregistrer les autres objets (sous-tâches, notes, pièces jointes, efforts) dans le moniteur."""
                from taskcoachlib.domain import (
                    task,
                )  # Import local pour éviter les problèmes de dépendances circulaires

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
                        # if isinstance(obj, task_module.Task):
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
            # Explicitly clear changes for categories after resetAllChanges()
            for cat in self.categories():
                self.__monitor.setChanges(cat.id(), set())
            # self.__syncMLConfig = syncMLConfig
            # syncMLConfig from file is ignored - SyncML removed
            self.__guid = guid

            if os.path.exists(self.filename()):
                # We need to reset the changes on disk because we're up to date.
                print(
                    f"TaskFile.load : Réécrit les changements dans {self.filename()}.delta en mode wb."
                )
                # xml.ChangesXMLWriter(
                #     open(self.filename() + ".delta", "wb")
                # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                # # xml.ChangesXMLWriter(
                # #     open(self.filename() + ".delta", "w")
                # # ).write(self.__changes)  # écriture en bytes ? plutôt str, non ?
                # with open(self.filename() + ".delta", "wb") as f:
                with open(self.filename() + ".delta", "w+b") as f:
                    writer = xml.ChangesXMLWriter(f)
                    writer.write(self.__changes)
                    f.close()
        except Exception as e:
            # log.info("TaskFile.load règle filename sur ''")
            # self.setFilename("")
            raise Exception(
                f"TaskFile.load : Erreur de parsing XML lors du chargement de filename '{filename}', erreur : {e}"
            )
        finally:
            self.__loading = False  # Très important pour débloquer needSave()
            self.markClean()
            self.__changedOnDisk = False
            log.info(
                "TaskFile.load : DEBUG tasks loaded: %s", len(self.tasks())
            )
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
        print(
            f"TaskFile.load : ✅ Fichier {filename} chargé. Tâches : {self.tasks()}, Catégories : {self.categories()}"
        )
        for task in self.tasks():
            print(
                f"TaskFile.load :    Tâche {task} -> Catégories : {task.categories()}"
            )

    # Après chaque sauvegarde : appeler markClean(),
    # pas seulement self._needSave = False
    # sinon les changements restent dans le monitor.
    def _save(self, **kwargs):
        """
        Enregistrez le fichier de tâches sur le disque.

        Cette méthode écrit toutes les tâches, notes, catégories et la configuration
        SyncML dans un fichier XML. Si le fichier existe déjà, il sera remplacé
        de manière sécurisée via l'utilisation d'un fichier temporaire (`SafeWriteFile`).

        Cette méthode écrit le contenu courant du modèle (tâches, catégories,
        notes, etc.) dans le fichier .tsk.

        Args :
            **kwargs : Arguments supplémentaires éventuels (non utilisés ici).

        Raises :
            IOError : En cas de problème d’écriture du fichier.
            Exception : En cas d’erreur inattendue pendant l’écriture.
        """
        log.info(
            "TaskFile._save commence à Enregistrer le fichier de tâches sur le disque."
        )
        # # log.info("Sauvegarde de la base de tâches dans '%s'", filename)
        # Gèrer __loading, alors qu'une sauvegarde est une opération critique qui pourrait interférer avec un chargement en cours
        if self.__loading:
            log.warning("Sauvegarde annulée : fichier en cours de chargement")
            return
        # # À modifier avec les nouvelles possibilités de with.
        try:
            pub.sendMessage("taskfile.aboutToSave", taskFile=self)
        except Exception as e:
            # pass
            log.error(
                f"TaskFile._save : Erreur de sauvegarde : {e}", exc_info=True
            )
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
                "TaskFile._save : Aucun nom de fichier n’est défini pour la sauvegarde."
            )
            self.__saving = False  # Rétablir le drapeau de sauvegarde pour permettre une nouvelle tentative après une erreur
            self.__needSave = True  # Marquer comme nécessitant une sauvegarde pour éviter de perdre les modifications
            raise RuntimeError(
                "TaskFile._save : Aucun nom de fichier n’est défini pour la sauvegarde."
            )
            # TODO : Peut-être lever une exception plus spécifique ou gérer cela différemment selon le contexte de l'application. Par exemple, on pourrait demander à l'utilisateur de spécifier un nom de fichier avant de sauvegarder.

        log.debug(
            "TaskFile._save : Début de la sauvegarde vers le fichier : %s",
            self.__filename,
        )

        # Empêcher d'écraser un fichier avec un contenu vide,
        # ce qui pourrait entraîner une perte de données.
        # Accepter la sauvegarde si au moins une collection contient des éléments
        # (tâches, catégories, notes, efforts). Le wrapper save() vérifie déjà
        # ceci, mais _save() était trop strict et refusait la sauvegarde lorsqu'il
        # n'y avait pas de tâches même si des catégories ou des notes étaient
        # présentes. Corrigeons cela ici en utilisant la même condition que
        # save() : n'abandonner que si toutes les collections sont vides.
        if not (
            self.tasks() or self.categories() or self.notes() or self.efforts()
        ):  # ? Logique peut-être à revoir !
            log.warning(
                "TaskFile._save : Save aborted: model (tasks, categories, notes, efforts) is empty."
            )
            self.__needSave = (
                False  # Reset the flag to avoid repeated warnings
            )
            self.__saving = False  # Ensure we reset the saving flag
            return

        try:
            self.mergeDiskChanges()

            if self.__needSave or not os.path.exists(self.__filename):
                fd = self._openForWrite()
                try:
                    xmlWriter = xml.writer.XMLWriter(fd)
                    xmlWriter.write(
                        self.tasks(),
                        self.categories(),
                        self.notes(),
                        self.syncMLConfig(),
                        self.guid(),
                    )
                finally:
                    self.__needSave = (
                        False  # Reset the flag after attempting to save
                    )
                    fd.close()
            self.markClean()
            log.info(
                "TaskFile._save : Fichier sauvegardé avec succès : %s",
                self.__filename,
            )
        except IOError as e:
            log.exception(
                "TaskFile._save : Erreur d’écriture du fichier %s",
                self.__filename,
            )
            self.__saving = True  # Rétablir le drapeau de sauvegarde pour permettre une nouvelle tentative après une erreur
            self.__needSave = (
                True  # Marquer comme nécessitant une sauvegarde pour éviter
            )
            raise
        except Exception as e:
            log.exception(
                "TaskFile._save : Erreur inattendue lors de la sauvegarde du fichier : %s",
                self.__filename,
            )
            self.__saving = True  # Rétablir le drapeau de sauvegarde pour permettre une nouvelle tentative après une erreur
            self.__needSave = True  # Marquer comme nécessitant une sauvegarde pour éviter de perdre les modifications
            raise
        finally:
            self.__needSave = False
            self.__saving = False
            self.markClean()
            # ✅ NOUVEAU : Synchroniser le ChangeMonitor avec __needSave
            self.clearChangeMonitor()
            self.__notifier.saved()
            try:
                pub.sendMessage("taskfile.justSaved", taskFile=self)
            except Exception as e:
                pass

    def save(self, **kwargs):
        """
        Sauvegarde le fichier TaskCoach sur le disque.

        Cette méthode écrit le contenu courant du modèle (tâches, catégories,
        notes, etc.) dans le fichier .tsk.

        Une protection est ajoutée pour empêcher l'écrasement accidentel
        d'un fichier contenant des données si le modèle courant est vide.
        """
        # Cette protection semble bonne.
        # Mais si le fichier sur le disque contient des tâches,
        # et que self.tasks() est vide (suite à un bug de chargement),
        # on refuse de sauvegarder, ce qui est bien.
        # Cependant, si l'utilisateur veut sauvegarder un fichier vide
        # (par exemple, il a tout supprimé volontairement), il ne peut pas.
        # C'est un compromis acceptable pour éviter la perte de données accidentelle.

        # Vérifie si toutes les collections sont vides (tâches, catégories, notes, efforts)
        # et n'autorise la sauvegarde que si au moins une collection contient des éléments.
        # Ceci permet d'enregistrer des fichiers qui ne contiennent que des catégories
        # ou des notes (cas utilisé par certains tests/unités et par l'import/export).
        if not (
            self.tasks() or self.categories() or self.notes() or self.efforts()
        ):
            # Écrit un message d'erreur dans le journal
            log.error(
                "TaskFile.save : Sauvegarde annulée : le modèle (tâches, catégories, notes, efforts) est vide."
            )

            # Empêche la sauvegarde pour éviter d'écraser un fichier valide
            return

        # log.info(
        print(
            f"TaskFile.save : Sauvegarde demandée pour le fichier {self.__filename}. Nombre de tâches : {len(self.tasks())}"
        )
        # Vérifie si le fichier existe déjà
        if os.path.exists(self.__filename):

            # construit le nom du backup
            backup = self.__filename + ".bak"

            # copie le fichier existant vers le backup
            shutil.copy2(self.__filename, backup)

            # écrit une information dans le log
            # log.info(f"TaskFile.save : Backup créé : {backup}")
            print(f"TaskFile.save : Backup créé : {backup}")

        # Appelle la méthode interne qui effectue réellement l'écriture
        self._save(**kwargs)

    # def cleaner_after_merge(self):
    #     """
    #     PURGE DES CHANGEMENTS APRÈS FUSION
    #
    #     Returns:
    #
    #     """
    #     print(
    #         "TaskFile.mergeDiskChanges.cleaner_after_merge : Début du nettoyage des modifications."
    #     )
    #     # --- SECTION DE PURGE DES CHANGEMENTS APRÈS FUSION ---
    #     # On nettoie les tâches et leurs enfants (efforts et pièce jointes)
    #     for the_task in list(self.tasks()):
    #         self.__changes.pop(the_task, None)
    #         for the_effort in the_task.efforts():
    #             self.__changes.pop(the_effort, None)
    #         for the_attachment in the_task.attachments():
    #             self.__changes.pop(the_attachment, None)
    #         # # Purge du conteneur d'attachments et de notes de la tâche si présents
    #         # if hasattr(the_task, "attachments"):
    #         #     self.__changes.pop(the_task.attachments(), None)
    #         # if hasattr(the_task, "notes"):
    #         #     self.__changes.pop(the_task.notes(), None)
    #
    #     # CORRECTION : On doit aussi vider les notes racines ET leurs attachements !
    #     for the_note in list(self.notes()):
    #         self.__changes.pop(the_note, None)
    #         for note_attachment in the_note.attachments():
    #             self.__changes.pop(
    #                 note_attachment, None
    #             )  # <-- C'est cette clé qui bloque à 1 !
    #         # # CORRECTION CRITIQUE : Purge du conteneur d'attachments de la NOTE !
    #         # if hasattr(the_note, "attachments"):
    #         #     self.__changes.pop(the_note.attachments(), None)
    #
    #     # for the_category in list(self.categories()):
    #     #     self.__changes.pop(the_category, None)
    #
    #     # # 3. Sécurité absolue pour le test multi-utilisateur :
    #     # # Si le dictionnaire contient encore une clé résiduelle (par exemple une chaîne d'attribut,
    #     # # ou une référence à un vieil objet mémoire d'attachement), on purge tout.
    #     # # Comme la fusion sur disque est terminée et validée, self.__changes DOIT être vide.
    #     # self.__changes.clear()
    #
    #     # 2. Sécurité absolue : On itère directement sur les clés restantes de self.__changes
    #     # pour vider toutes les scories (qu'il s'agisse d'objets ou d'identifiants d'attributs)
    #     for key in list(self.__changes.keys()):
    #         del self.__changes[key]
    #
    #     # 3. Notification au moniteur de changements sous-jacent
    #     # Dans TaskCoach, le ChangeMonitor possède souvent une méthode pour purger son état
    #     if (
    #         hasattr(self, "_TaskFile__changeMonitor")
    #         and self._TaskFile__changeMonitor
    #     ):
    #         if hasattr(self._TaskFile__changeMonitor, "clear"):
    #             self._TaskFile__changeMonitor.clear()
    #         elif hasattr(self._TaskFile__changeMonitor, "reset"):
    #             self._TaskFile__changeMonitor.reset()
    #
    #     print(
    #         "TaskFile.cleaner_after_merge : Fin du nettoyage, self.__changes vidé."
    #     )

    def mergeDiskChanges(self):
        """
        Fusionner les modifications du disque avec le fichier de tâches actuel.

        Attributes :
            - __loading (bool) : Indique si le fichier est en cours de chargement, évitant des opérations concurrentes.
            - __filename (str) : Le nom du fichier de tâches.
            - __monitor (ChangeMonitor) : Un moniteur de changements pour suivre les modifications des objets de domaine.
            - __changes (dict) : Le dictionnaire de suivi des changements.
            - __saving (bool) : Indique si le fichier est en cours d'enregistrement, évitant des opérations concurrentes.
        """
        # log.debug(
        print(
            f"TaskFile.mergeDiskChanges : Début de la fusion des modifications du disque pour {self.__filename}."
        )
        # TODO : peut-être vérifier l'état de __loading avant de commencer !
        # # 1. On bloque temporairement le moniteur de changements pour éviter
        # # que les événements de reconstruction XML (addAttachment) ne soient comptés comme des modifs locales
        # if hasattr(self, "__changeMonitor") and self.__changeMonitor:
        #     self.__changeMonitor.stop()
        # 1. ARRÊTER temporairement le moniteur de changements avant la fusion
        if (
            hasattr(self, "_TaskFile__changeMonitor")
            and self._TaskFile__changeMonitor
        ):
            self._TaskFile__changeMonitor.stop()

        # Gérer __loading, alors qu'une fusion/sauvegarde est une opération critique qui pourrait interférer avec un chargement en cours
        self.__loading = True
        try:
            # Si le fichier de tâche existe
            if os.path.exists(self.__filename):
                # Not using self.exists() because DummyFile.exists returns True
                # Instead of writing the content of memory, merge changes
                # with the on-disk version and save the result.
                # log.debug(
                print(
                    f"TaskFile.mergeDiskChanges : Le fichier {self.__filename} existe, fusion des changements du disque."
                )
                # Mettre le moniteur en attente de synchronisation des changements
                self.__monitor.freeze()
                try:
                    # fd = self._openForRead()
                    with self._openForRead() as fd:
                        # log.info(
                        print(
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
                            ), _duplicate_ids = self._read(fd)
                            # fd.close()  # Inutile est dangereux avec with, le with s'en charge automatiquement, même en cas d'exception.
                        except Exception:
                            log.exception(
                                "TaskFile.mergeDiskChanges : Erreur lors de la lecture du fichier principal pour la fusion des changements '%s'",
                                self.__filename,
                            )
                            raise

                    self.__changes = allChanges

                    if self.__saving:
                        # log.debug(
                        print(
                            f"TaskFile.mergeDiskChanges : En cours de sauvegarde, fusionne les changements de tous les autres moniteurs dans le moniteur actuel {self.__monitor.guid()}."
                        )
                        for devGUID, changes in list(self.__changes.items()):
                            if devGUID != self.__monitor.guid():
                                # log.debug(
                                print(
                                    f"TaskFile.mergeDiskChanges : Fusionne les changements du moniteur {devGUID} dans le moniteur actuel {self.__monitor.guid()}."
                                )
                                changes.merge(self.__monitor)

                    # sync = ChangeSynchronizer(self.__monitor, allChanges)
                    sync = ChangeSynchronizer(self.__monitor, self.__changes)

                    # log.debug(
                    print(
                        f"TaskFile.mergeDiskChanges : Synchronisation des changements pour les catégories, tâches et notes."
                    )
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
                    print(
                        f"TaskFile.mergeDiskChanges : self.__changes={self.__changes}."
                    )
                    # # après la fusion :
                    # for the_task in self.tasks():
                    #     if the_task in self.__changes:
                    #         # Effacer
                    #         del self.__changes[the_task]
                    # self.cleaner_after_merge()
                    # log.debug(
                    print(
                        f"TaskFile.mergeDiskChanges : Changements fusionnés, moniteur actuel {self.__monitor.guid()} mis à jour avec les changements fusionnés."
                    )
                finally:
                    # # 2. On relance le moniteur
                    # if (
                    #     hasattr(self, "__changeMonitor")
                    #     and self.__changeMonitor
                    # ):
                    # 2. REDÉMARRER le moniteur de changements dans tous les cas
                    if (
                        hasattr(self, "_TaskFile__changeMonitor")
                        and self._TaskFile__changeMonitor
                    ):
                        print(
                            f"TaskFile.mergeDiskChanges : relance du moniteur {self._TaskFile__changeMonitor}."
                        )
                        # self.__changeMonitor.start()
                        self._TaskFile__changeMonitor.start()
                        # # On force une remise à zéro complète du tracker pour cette session
                        # if hasattr(self.__changeMonitor, "clear"):
                        #     self.__changeMonitor.clear()
                        # elif hasattr(self.__changeMonitor, "reset"):
                        #     self.__changeMonitor.reset()
                        # 3. Forcer le nettoyage des reliquats d'événements de fusion
                        # pour que self.taskFile.changes() renvoie bien 0
                        if hasattr(self._TaskFile__changeMonitor, "clear"):
                            self._TaskFile__changeMonitor.clear()
                        elif hasattr(self._TaskFile__changeMonitor, "reset"):
                            self._TaskFile__changeMonitor.reset()
                    self.__monitor.thaw()

            else:
                # log.debug(
                print(
                    f"TaskFile.mergeDiskChanges : Le fichier {self.__filename} n'existe pas, aucune fusion nécessaire, initialisation des changements avec le moniteur actuel {self.__monitor.guid()}."
                )
                self.__changes = {self.__monitor.guid(): self.__monitor}

            if not self.tasks() and not os.path.exists(self.__filename):
                # log.warning(
                print("mergeDiskChanges aborted: no tasks and no file on disk")
                return
                # log.debug(
                print(
                    f"TaskFile.mergeDiskChanges : Fusion des changements terminée, réinitialisation de tous les changements dans le moniteur actuel {self.__monitor.guid()}."
                )
            self.__monitor.resetAllChanges()
            # log.debug(
            print(
                f"TaskFile.mergeDiskChanges : Enregistrement des changements fusionnés dans le fichier {self.__filename}.delta."
            )
            # fd = self._openForWrite(".delta")
            # try:
            #     xml.ChangesXMLWriter(fd).write(self.changes())
            # finally:
            #     fd.close()
            with self._openForWrite(".delta") as fd:
                # with open(self.filename() + ".delta", "w+b") as fd:
                # log.debug(
                print(
                    f"TaskFile.mergeDiskChanges : fd={fd} ouvert en mode écriture binaire pour les changements fusionnés !"
                )
                writer = xml.ChangesXMLWriter(fd)
                writer.write(self.changes())
                # log.debug(
                print(
                    f"TaskFile.mergeDiskChanges : Changements fusionnés écrits dans {self.__filename}.delta avec succès."
                )
                # fd.close()

            self.__changedOnDisk = False

        finally:
            self.__loading = False  # Important
            # self.markClean()  # Très important
            # sinon les tests multi-utilisateurs restent dirty après fusion.
            # -> Il faut trouver une autre solution !
            # # --- SECTION DE PURGE DES CHANGEMENTS APRÈS FUSION ---
            # # On nettoie les tâches et leurs enfants
            # for the_task in list(self.tasks()):
            #     self.__changes.pop(the_task, None)
            #     for effort in the_task.efforts():
            #         self.__changes.pop(effort, None)
            #     for attachment in the_task.attachments():
            #         self.__changes.pop(attachment, None)
            #
            # # CORRECTION : On doit aussi vider les notes racines ET leurs attachements !
            # for the_note in list(self.notes()):
            #     self.__changes.pop(the_note, None)
            #     for the_attachment in the_note.attachments():
            #         self.__changes.pop(
            #             the_attachment, None
            #         )  # <-- C'est cette clé qui bloque à 1 !
            #
            # for the_category in list(self.categories()):
            #     self.__changes.pop(the_category, None)
            # 2. On relance le moniteur
            if hasattr(self, "__changeMonitor") and self.__changeMonitor:
                self.__changeMonitor.start()
                # On force une remise à zéro complète du tracker pour cette session
                if hasattr(self.__changeMonitor, "clear"):
                    self.__changeMonitor.clear()
                elif hasattr(self.__changeMonitor, "reset"):
                    self.__changeMonitor.reset()

        # 3. Purge radicale de self.__changes (votre méthode de nettoyage actuelle)
        if hasattr(self, "__changes"):
            print(f"effacement de self.__changes={self.__changes}")
            self.__changes.clear()

        # Nettoyage des dictionnaires locaux
        # Si la méthode changes() renvoie une copie ou un dictionnaire sous-jacent :
        if hasattr(self, "_TaskFile__changes") and self._TaskFile__changes:
            print(
                f"effacement de self._TaskFile__changes={self._TaskFile__changes}"
            )
            self._TaskFile__changes.clear()
        if hasattr(self, "__changes") and self.__changes:
            self.__changes.clear()
        print(
            "TaskFile.mergeDiskChanges : Fusion terminée et ChangeMonitor réaligné."
        )

    def saveas(self, filename):
        """
        Enregistrer le fichier de tâche sous un nouveau nom de fichier.

        Args :
            filename (str) : Le nouveau nom de fichier sous lequel enregistrer.
        """
        if os.path.exists(filename):
            os.remove(filename)
        # if os.path.exists(filename + ".delta"):
        if os.path.exists(f"{filename}.delta"):
            # os.remove(filename + ".delta")
            os.remove(f"{filename}.delta")
        # Après le changement de nom :
        self.__lastFilename = filename
        self.setFilename(filename)
        self.save()
        self.markClean()

    def merge(self, filename):
        """
        Fusionnez un autre fichier de tâches avec celui-ci.

        Args :
            filename (str) : Le nom de fichier du fichier de tâches à fusionner.
        """
        # Il faut enregistrer les liens de catégorie pour les tâches et notes
        # du mergeFile avant de les fusionner dans self.tasks() et self.notes().
        mergeFile = self.__class__()
        mergeFile.load(filename)
        self.__loading = True
        try:
            categoryMap = dict()
            # self.tasks().removeItems(
            #     self.objectsToOverwrite(self.tasks(), mergeFile.tasks())
            # )
            # Enregistre les liens avant la fusion.
            # Enregistrer les liens de catégorie pour les tâches et notes existantes
            self.rememberCategoryLinks(categoryMap, self.tasks())
            # self.tasks().extend(mergeFile.tasks().rootItems())
            # self.notes().removeItems(
            #     self.objectsToOverwrite(self.notes(), mergeFile.notes())
            # )
            self.rememberCategoryLinks(categoryMap, self.notes())

            # Enregistrer les liens de catégorie pour les tâches et notes du mergeFile
            print(
                f"TaskFile.merge : Enregistrement des liens de catégorie pour les tâches et notes du mergeFile id {id(mergeFile)}."
            )
            print(
                f"TaskFile.merge : mergeFile.tasks()={mergeFile.tasks()}, mergeFile.notes()={mergeFile.notes()}."
            )
            self.rememberCategoryLinks(categoryMap, mergeFile.tasks())
            self.rememberCategoryLinks(categoryMap, mergeFile.notes())

            # Fusion des tâches
            self.tasks().removeItems(
                self.objectsToOverwrite(self.tasks(), mergeFile.tasks())
            )
            print(
                f"TaskFile.merge : Fusion des tâches du mergeFile id {id(mergeFile)} dans self.tasks() id {id(self.tasks())}."
            )
            self.tasks().extend(mergeFile.tasks().rootItems())

            # Fusion des notes
            self.notes().removeItems(
                self.objectsToOverwrite(self.notes(), mergeFile.notes())
            )
            print(
                f"TaskFile.merge : Fusion des notes du mergeFile id {id(mergeFile)} dans self.notes() id {id(self.notes())}."
            )
            self.notes().extend(mergeFile.notes().rootItems())

            # Fusion des catégories
            self.categories().removeItems(
                self.objectsToOverwrite(
                    self.categories(), mergeFile.categories()
                )
            )
            print(
                f"TaskFile.merge : Fusion des catégories du mergeFile id {id(mergeFile)} dans self.categories() id {id(self.categories())}."
            )
            self.categories().extend(mergeFile.categories().rootItems())
            # Restaurer les liens après la fusion.
            self.restoreCategoryLinks(categoryMap)
            print(
                f"TaskFile.merge : Restauration des liens de catégorie après la fusion du mergeFile id {id(mergeFile)}."
            )
            mergeFile.close()
            self.markDirty(force=True)
        finally:
            self.__loading = False

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
                    )  # getObjectById vient de domain.base.collection.Collection ! Un ensemble d'objets composites observables.
                )
            except IndexError:
                pass
        return objectsToOverwrite

    def rememberCategoryLinks(self, categoryMap, categorizables):
        """
        N'oubliez pas les liens de catégorie pour une restauration ultérieure.

        Souvenir des liens de catégorie.
        Enregistrer la liste des categories des objets catégorisables dans la carte des catégories.

        Args :
            categorisMap (dict) : La carte des catégories.
            categorizables (list) : Les objets catégorisables.
        """
        # Problème potentiel : Si categorizable.categories()
        # retourne une liste vide ou si categoryToLinkLater.id() retourne None,
        # cela pourrait causer des problèmes plus tard.
        for categorizable in categorizables:
            # Force la vérification des catégories associées
            categories = categorizable.categories()
            # for categoryToLinkLater in categorizable.categories():
            for categoryToLinkLater in categories:
                # Éviter d'ajouter des entrées avec des clés None dans
                # categoryMap, ce qui pourrait causer des problèmes
                # lors de la restauration des liens.
                # if categoryToLinkLater.id() is not None:  # Éviter les None
                if (
                    categoryToLinkLater is not None
                    and categoryToLinkLater.id() is not None
                ):  # Éviter les None
                    categoryMap.setdefault(
                        categoryToLinkLater.id(), []
                    ).append(categorizable)
                else:
                    # log.warning(
                    print(
                        f"TaskFile.rememberCategoryLinks : ⚠️ Catégorie introuvable pour l'objet {categorizable} (ID: {categorizable.id()})"
                    )
                    print(
                        f"TaskFile.rememberCategoryLinks : Ignorer un lien de catégorie avec une catégorie None ou une catégorie sans ID pour l'objet catégorisable {categorizable}."
                    )

    def restoreCategoryLinks(self, categoryMap):
        """
        Restaurez les liens de catégorie à partir de la carte de catégorie mémorisée.

        Args :
            categoryMap (dict) : La carte de catégorie.
        """
        # Problème potentiel :
        # Si categoryId est None (parce que categoryToLinkLater.id()
        # a retourné None dans rememberCategoryLinks),
        # alors categories.getObjectById(None) pourrait échouer
        # ou ne pas trouver la catégorie.
        # Si categorizables contient des objets qui ne sont pas correctement
        # fusionnés, les liens ne seront pas rétablis.
        categories = self.categories()
        for categoryId, categorizables in categoryMap.items():
            if categoryId is None:
                print(
                    f"TaskFile.restoreCategoryLinks: ⚠️ categoryId est None dans categoryMap pour les objets : {categorizables}"
                )
                continue  # Éviter les None
            try:
                categoryToLink = categories.getObjectById(categoryId)
            # except IndexError:
            #     continue  # Subcategory was removed by the merge
            except (IndexError, AttributeError):
                print(
                    f"TaskFile.restoreCategoryLinks: ⚠️ Catégorie avec ID {categoryId} introuvable dans self.categories()"
                )
                continue  # La catégorie n'existe pas
                # La sous-catégorie a été supprimée par la fusion
            for categorizable in categorizables:
                if categorizable is None:
                    print(
                        f"TaskFile.restoreCategoryLinks: ⚠️ Objet catégorisable est None dans categoryMap pour la catégorie {categoryId}"
                    )
                    continue
                try:
                    categorizable.addCategory(categoryToLink)
                    categoryToLink.addCategorizable(categorizable)
                    print(
                        f"TaskFile.restoreCategoryLinks: ✅ Lien restauré entre {categorizable} et {categoryToLink}"
                    )
                except Exception as e:
                    print(
                        f"TaskFile.restoreCategoryLinks: ⚠️ Échec de la restauration du lien pour {categorizable} : {e}"
                    )

    def beginSync(self):
        """
        Commencez une opération de synchronisation.
        """
        # Indiquer que le fichier est en cours de chargement.
        self.__loading = True

    def endSync(self):
        """
        Terminez une opération de synchronisation.
        """
        # Indiquer que le fichier n'est plus en cours de chargement.
        self.__loading = False
        # Marquer le fichier de tâche comme sâle.
        self.markDirty()


class LockTimeout(Exception):
    """Raised when file lock cannot be acquired (another process has it)."""

    pass


class LockFailed(Exception):
    """Raised when file locking fails for other reasons."""

    pass


class DummyLockFile(object):
    """
    Une classe de fichier de verrouillage factice
    à utiliser dans les répertoires synchronisés avec le cloud.
    """

    def acquire(self, timeout=None):
        # def acquire(self, blocking=None, timeout=None):
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

        Methods :
            __isFuse(path) (bool) : Vérifier et retourner si le chemin donné est un système de fichiers FUSE.
            __isCloud(filename) (bool) : Vérifier et retourner si un fichier se trouve dans un répertoire synchronisé avec le cloud.
            __createLockFile(filename) : Créez un fichier de verrouillage pour le nom de fichier donné.
            __getLockPath(filename) : Récupérez le chemin du fichier de verrouillage pour le nom de fichier donné.
            is_locked() : Vérifie si le fichier de tâches est verrouillé.
            is_locked_by_me() : Vérifie si le fichier de tâches est verrouillé par le processus en cours.
            release_lock() : Libère le verrou sur le fichier de tâches actuel.
            acquire_lock(filename) : Acquérir un verrou pour le fichier de tâche.
            break_lock(filename) : Briser le verrou sur le fichier de tâches donné.
            close() : Fermer le fichier de tâches en libérant le verrou.
            load(filename=None, lock=True, breakLock=False) : Charger le fichier de tâches à partir du disque, en acquérant un verrou si nécessaire.
            save() : Enregistrer le fichier de tâche sur le disque, en acquérant un verrou si nécessaire.
            mergeDiskChanges() : Fusionner les modifications du disque avec le fichier de tâches actuel, en acquérant un verrou si nécessaire.

        La classe « LockedTaskFile » est conçue pour ajouter un verrouillage coopératif à la classe « TaskFile », empêchant ainsi l’accès simultané au fichier de tâche. Passons en revue les composants clés et la logique liés au verrouillage :

    ### Composants clés de 'LockedTaskFile'

    1. **Création de verrou** :
    - La méthode '__createLockFile' détermine le type de verrou à utiliser en fonction du système d’exploitation et si le fichier se trouve dans un répertoire synchronisé dans le cloud ou dans un système de fichiers FUSE.
    - Il utilise 'lockfile'. FileLock' pour les cas généraux, 'DummyLockFile' pour les répertoires cloud sous Windows, et 'lockfile. MkdirFileLock » pour les systèmes de fichiers FUSE.

    2. **Acquisition de verrou** :
    - La méthode « acquire_lock » tente d’obtenir un verrou sur le fichier en utilisant un court délai d’attente pour éviter le blocage.
    - Si le verrou ne peut pas être acquis, cela crée une exception « LockTimeout ».

    3. **Libération de la serrure** :
    - La méthode « release_lock » libère la serrure si elle est actuellement retenue par le processus.

    4. **Statut du verrou** :
    - Les méthodes 'is_locked' et 'is_locked_by_me' vérifient respectivement si le fichier est verrouillé et si le processus en cours contient le verrou.

    5. **Opérations de fichier** :
    - Les méthodes « charger », « sauvegarder » et « mergeDiskChanges » sont surpassées pour inclure la logique d’acquisition et de libération de verrous.
    - La méthode « charger » acquiert un verrou avant de charger le fichier, et la méthode « sauvegarder » acquiert un verrou avant d’enregistrer le fichier.

    ### Problèmes et considérations

    - **Libération de verrouillage dans 'finally'** :
        Le bloc 'finally' dans la méthode 'save' libère le verrou après la sauvegarde,
        ce qui peut ne pas être approprié si l’intention est de garder le fichier verrouillé pendant toute la session.
        Envisagez de retirer le verrouillage du bloc « finally » si le verrou doit être maintenu.

    - **Temps d’attente du verrou** :
        La méthode « acquire_lock » utilise un court délai d’attente (0,1 seconde)
        pour acquérir le verrou. Si c’est trop court pour votre usage,
        envisagez d’augmenter le délai d’attente.

    - **Chemin du fichier verrouillé** :
        Assurez-vous que le chemin du fichier verrouillé est correctement déterminé
        et que le fichier verrouillage est créé et supprimé comme prévu.

    - **Gestion des erreurs** :
        Assurez-vous que les exceptions liées à l’acquisition et à la libération
        du verrou sont correctement gérées afin d’éviter que le fichier reste
        dans un état incohérent.

    ### Étapes de débogage

    1. **Journalisation** :
        Ajoutez des registres plus détaillés autour de l’acquisition
        et de la libération des serrures pour suivre quand les verrous sont acquis et libérés.

    2. **Nettoyage des fichiers de verrouillage** :
        Assurez-vous que les fichiers de verrouillage sont bien rangés
        dans la méthode « tearDown » de vos tests afin
        d’éviter que les fichiers de verrouillage restants ne causent des problèmes.

    3. **Mécanisme de réessayage** :
        Envisagez de mettre en place un mécanisme de réévaluation
        pour l’acquisition de verrous si 'LockTimeout' est relancé.

    4. **Noms uniques de fichiers de verrouillage** :
        Utilisez des noms uniques de fichiers de verrouillage pour chaque test
        afin d’éviter les conflits entre les tests.

    En traitant ces problèmes et considérations, vous devriez pouvoir résoudre
    les problèmes « FileExistsError » et « LockTimeout » liés à la classe « LockedTaskFile ».

    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser le LockedTaskFile.

        Args :
            *args : arguments supplémentaires.
            **kwargs : arguments de mots clés supplémentaires.

        Attributes :
            __lock (FileLock or DummyLockFile or None) : L'instance de fichier de verrouillage. Indique si le fichier est verrouillé, empêchant certaines opérations simultanées.
            __lock_acquired (bool) : Indique si le verrou a été acquis avec succès.
        """
        super().__init__(*args, **kwargs)
        self.__lock = None
        self.__lock_acquired = False

    def __isFuse(self, path):
        """
        Vérifiez si un chemin donné est un système de fichiers FUSE.

        Args :
            path (str) : Le chemin à vérifier.

        Returns :
            (bool) : True si le chemin est un système de fichiers FUSE, False sinon.
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
                            log.debug(
                                f"LockedTaskFile.__isFuse : Le chemin {path} est sur un système de fichiers FUSE monté sur {mount_point} avec le type {fs_type}."
                            )
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
        Créez un fichier de verrouillage de nom de fichier donné.

        The __createLockFile method determines the type of lock to use
        based on the operating system and whether the file is in a cloud-synced
        directory or a FUSE filesystem.

        It uses lockfile.FileLock for general cases, DummyLockFile for cloud
        directories on Windows, and lockfile.MkdirFileLock for FUSE filesystems.

        Args :
            filename (str) : Le nom du fichier de verrouillage.

        Returns :
            (FileLock or DummyLockFile) : L'instance de fichier de verrouillage.
        """
        if operating_system.isWindows() and self.__isCloud(filename):
            print(
                f"LockedTaskFile.__createLockFile : {filename} est dans un répertoire synchronisé avec le cloud sur Windows, utilisation de DummyLockFile."
            )
            return DummyLockFile()
        if self.__isFuse(filename):
            print(
                f"LockedTaskFile.__createLockFile : {filename} est dans un système de fichiers FUSE, utilisation de lockfile.MkdirFileLock."
            )
            return lockfile.MkdirFileLock(filename)
        # Création et retourne un objet FileLock pour le nom de fichier donné.
        print(
            f"LockedTaskFile.__createLockFile : {filename} est dans un système de fichiers standard, utilisation de lockfile.FileLock."
        )
        # return lockfile.FileLock(filename)
        lockfile_to_return = lockfile.FileLock(
            filename
        )  # Lock access to a file using atomic property of link(2).
        # log.debug(
        print(
            f"LockedTaskFile.__createLockFile : a Créé un lockfile pour {filename} : {lockfile_to_return}"
        )
        return lockfile_to_return

    def __getLockPath(self, filename):
        """Get the path to the lock file.

        Retourner le chemin du fichier de verrouillage pour le nom de fichier donné.
        """
        # print(
        #     f"LockedTaskFile.__getLockPath : Récupère le chemin du fichier de verrouillage pour {filename}."
        # )
        # return filename + ".lock"
        path_of_lockfile = filename + ".lock"
        # log.debug(
        print(
            f"LockedTaskFile.__getLockPath : Le chemin du fichier de verrouillage pour {filename} est {path_of_lockfile}"
        )
        return path_of_lockfile

    # The is_locked and is_locked_by_me methods check if the file is locked
    # and if the current process holds the lock, respectively.
    def is_locked(self):
        """
        Vérifiez si le fichier de tâche est verrouillé.

        Returns :
            (bool) : True si le fichier de tâche est verrouillé, False sinon.
        """
        # return self.__lock and self.__lock.is_locked()
        # log.debug(
        print(
            f"LockedTaskFile.is_locked : Vérifie si le fichier de tâches est verrouillé avec self.__lock={self.__lock} et self.__lock_acquired={self.__lock_acquired}"
        )
        return self.__lock is not None and self.__lock_acquired

    def is_locked_by_me(self):
        """
        Vérifiez si le fichier de tâches est verrouillé par le processus en cours.

        Returns :
            (bool) : True si le fichier de tâches est verrouillé par le processus en cours, False sinon.
        """
        print(
            f"LockedTaskFile.is_locked_by_me : Vérifie si le fichier de tâches est verrouillé par ce processus avec self.__lock={self.__lock} et self.__lock_acquired={self.__lock_acquired}"
        )
        # return self.is_locked() and self.__lock.i_am_locking()  # i_am_locking ne fonctionne pas avec fastener.
        return self.is_locked()

    def release_lock(self):
        """
        Libérez le verrou sur le fichier de tâches actuel.

        The release_lock method releases the lock if it is currently held
        by the process. It checks if the lock is not None and
        if it was acquired before attempting to release it.
        If an exception occurs during release, it is caught and ignored
        to ensure that the method does not raise an error if the lock cannot
        be released (best effort release). After releasing,
        it sets the lock to None and updates the lock_acquired flag.
        """
        print(
            f"LockedTaskFile.release_lock : Tentative de libération du verrou pour {self.filename()} avec self.__lock={self.__lock} et self.__lock_acquired={self.__lock_acquired}."
        )
        # if self.is_locked_by_me():
        #     self.__lock.release()
        if self.__lock is not None and self.__lock_acquired:
            try:
                print(
                    f"LockedTaskFile.release_lock : Libération du verrou pour {self.filename()} avec self.__lock={self.__lock}."
                )
                self.__lock.release()
            except Exception as e:
                print(
                    f"LockedTaskFile.release_lock : Erreur lors de la libération du verrou pour {self.filename()} : {e}. Ignorée."
                )
                pass  # Best effort release
            print(
                f"LockedTaskFile.release_lock : Redéfinition de self.__lock à None et self.__lock_acquired à False pour {self.filename()}."
            )
            self.__lock_acquired = False
        self.__lock = None

    def acquire_lock(self, filename):
        """
        Acquérir un verrou pour le fichier de tâche.

        The acquire_lock method attempts to acquire a lock on the file
        using a short timeout to avoid blocking.
        If the lock cannot be acquired, it raises a LockTimeout exception.

        Attributes :
            __lock :
            __lock_acquired :

        Args :
            filename (str) : Le nom du fichier à verrouiller.
        """
        print(
            f"LockedTaskFile.acquire_lock : Tentative d'acquisition du verrou pour {filename}."
        )
        # Vérifier si le fichier actuel est déjà verrouillé par le processus en cours.
        # if not self.is_locked_by_me():
        #     self.__lock = self.__createLockFile(filename)
        #     self.__lock.acquire(5)
        if self.is_locked_by_me():
            print(
                f"LockedTaskFile.acquire_lock : Le fichier de tâches est déjà verrouillé par ce processus, pas besoin d'acquérir à nouveau le verrou pour {filename}."
            )
            return  # Already holding the lock

        # Création d'un objet FileLock pour le nom de fichier donné.
        # Création du nom du fichier de verrouillage.
        lock_path = self.__getLockPath(filename)
        print(
            f"LockedTaskFile.acquire_lock : Tentative d'acquisition du verrou pour {filename} avec lock_path={lock_path}."
        )
        # Create the lock file only once, and reuse it for subsequent acquisitions.
        # try:
        self.__lock = fasteners.InterProcessLock(lock_path)
        # self.__lock = self.__createLockFile(lock_path)
        print(
            f"LockedTaskFile.acquire_lock : Créé le verrou pour {filename} : {self.__lock}"
        )
        try:
            # Try to acquire with short timeout (non-blocking for document apps)
            # Note : Dans taskcoach, lockfile.FileLock ne supporte pas le paramètre blocking, mais supporte le paramètre timeout, et timeout=0.1 est équivalent à un non-blocking.
            # acquired = self.__lock.acquire(blocking=True, timeout=0.1)  # timeout en secondes, pas en millisecondes. blocking n'est pas supporté par lockfile.FileLock, mais timeout l'est, et timeout=0.1 est équivalent à un non-blocking.
            acquired = self.__lock.acquire(
                timeout=0.5
            )  # timeout en secondes, pas en millisecondes. timeout=0.1 est équivalent à un non-blocking.
            print(
                f"LockedTaskFile.acquire_lock : Tentative d'acquisition du verrou pour {filename} a retourné {acquired}."
            )
            if not acquired:
                print(
                    f"LockedTaskFile.acquire_lock : Échec de l'acquisition du verrou pour {filename}, le fichier est verrouillé par un autre processus."
                )
                self.__lock = None
                raise LockTimeout(f"File is locked: {filename}")
            print(
                f"LockedTaskFile.acquire_lock : Verrou acquis pour {filename} avec self.__lock={self.__lock}."
            )
            self.__lock_acquired = True
        except LockTimeout:
            print(
                f"LockedTaskFile.acquire_lock : LockTimeout : Le fichier {filename} est verrouillé par un autre processus, verrou non acquis."
            )
            self.__lock_acquired = False
            raise
        except (PermissionError, OSError) as e:
            print(
                f"LockedTaskFile.acquire_lock : LockFailed : Impossible d'acquérir le verrou pour {filename} en raison de l'erreur : {e}"
            )
            self.__lock = None
            raise LockFailed(str(e)) from e

    def break_lock(self, filename):
        """
        Briser le verrou sur le fichier de tâches donné.

        Args :
            filename (str) : Le nom de fichier sur lequel briser le verrou.
        """
        print(
            f"LockedTaskFile.break_lock : Tentative de briser le verrou pour {filename}."
        )
        # self.__lock = self.__createLockFile(filename)
        # self.__lock.break_lock()
        lock_path = self.__getLockPath(filename)
        print(
            f"LockedTaskFile.break_lock : Le chemin du fichier de verrouillage pour {filename} est {lock_path}."
        )
        try:
            if os.path.exists(lock_path):
                print(
                    f"LockedTaskFile.break_lock : Le fichier de verrouillage {lock_path} existe, tentative de suppression."
                )
                os.remove(lock_path)
        except OSError:
            print(
                f"LockedTaskFile.break_lock : Erreur lors de la suppression du fichier de verrouillage {lock_path}, il peut être nécessaire de le supprimer manuellement !"
            )
            pass  # If we can't remove it, acquire will fail anyway

    def close(self):
        """
        Fermez le fichier de tâches en libérant le verrou.
        """
        try:
            if self.filename() and os.path.exists(self.filename()):
                self.acquire_lock(self.filename())

            print(
                f"LockedTaskFile.close : Fermeture du fichier de tâches {self.filename()} avec verrouillage."
            )
            super().close()
        finally:
            print(
                f"LockedTaskFile.close : Relâchement du verrou pour {self.filename()} après la fermeture."
            )
            if self.__lock_acquired:  # Vérifier avant relâche
                self.release_lock()

    def load(
        self, filename=None, lock=True, breakLock=False
    ):  # pylint: disable=W0221
        """Chargez le fichier de tâches à partir du disque, en acquérant un verrou si nécessaire.

        Verrouillez le fichier avant de le charger, s'il n'est pas déjà verrouillé.

        Args :
            filename (str | None) : (optional) Le nom du fichier à partir duquel charger. La valeur par défaut est Aucun.
            lock (bool) : (optional) S'il faut acquérir un verrou. La valeur par défaut est True.
            breakLock (bool) : (optional) S'il faut briser un verrou existant. La valeur par défaut est False.
        """
        # log.debug(
        print(
            f"LockedTaskFile.load : Appelé avec self={self}, filename={filename}, lock={lock}, breakLock={breakLock}"
        )
        filename = filename or self.filename()
        # log.debug(f"LockedTaskFile.load : Finalement filename={filename}")
        log.debug(f"LockedTaskFile.load : Finalement filename={filename}")

        # TODO : structure à revoir pour éviter les répétitions de code et les problèmes de verrouillage en cas d'erreur.
        try:
            if lock and filename:
                if breakLock:
                    # log.debug(
                    print(
                        f"LockedTaskFile.load : Brise le verrou de {filename}."
                    )
                    self.break_lock(filename)
                # log.debug(
                print(
                    f"LockedTaskFile.load : Acquière un verrou pur {filename}.lock."
                )
                self.acquire_lock(filename)
            # log.debug(f"LockedTaskFile.load : Charge le fichier {filename}.")
            print(f"LockedTaskFile.load : Charge le fichier {filename}.")
            return super().load(filename)
        except Exception:
            print(
                f"LockedTaskFile.load : Erreur lors du chargement du fichier {filename}, le verrou restera en place pour éviter les problèmes de sécurité des données."
            )
            # # Release lock if load fails ! NON, sinon on peut perdre le verrou en cas d'erreur de parsing XML,
            # ce qui est très mauvais pour la sécurité des données. Laisser le verrou en place est plus sûr,
            # même si cela peut nécessiter une intervention manuelle pour briser le verrou en cas de problème.
            self.release_lock()  # Reste pour les tests, mais ne doit pas être utilisé en production,
            # car cela peut entraîner une perte de données si le verrou est relâché alors que le fichier est dans un état incohérent.
            raise
        # Le verrou doit être maintenu tant que le fichier est ouvert.
        finally:  # <-- SUPPRIMER LE FINALLY qui relâche le verrou en cas de succès.
            # log.debug("LockedTaskFile.load : Finalement relâche le verrou.")
            print("LockedTaskFile.load : Finalement relâche le verrou.")
            if self.__lock_acquired:  # Vérifier avant relâche
                self.release_lock()  # Cela relâche le verrou systématiquement à la fin du chargement.
            # C'est une erreur majeure si l'intention est de garder le fichier verrouillé
            # pendant toute la session (ce qui est le cas pour LockedTaskFile).
            # Si le verrou est relâché, rien n'empêche une autre instance
            # ou un autre processus de toucher au fichier.
            # Mais cela n'explique pas directement pourquoi le fichier est vidé par cette instance,
            # sauf si la sauvegarde écrase le fichier avec du vide.

    def save(self, **kwargs):
        """Verrouillez le fichier avant de l'enregistrer, s'il n'est pas déjà verrouillé.

        Enregistrez le fichier de tâche sur le disque, en acquérant un verrou si nécessaire.

        Args :
            **kwargs : arguments de mots clés supplémentaires.
        """
        # log.debug(
        print(
            f"LockedTaskFile.save : Appelé avec self={self}, kwargs={kwargs}"
        )

        # self.acquire_lock(self.filename())
        # We should already hold the lock from load()
        if not self.is_locked_by_me() and self.filename():
            # log.debug(
            print(
                f"LockedTaskFile.save : Acquière un verrou pour {self.filename()} avant de sauvegarder."
            )
            self.acquire_lock(self.filename())
            # log.debug(
            print(
                f"LockedTaskFile.save : Verrou acquis pour {self.filename()}, maintenant en train de sauvegarder."
            )
        try:
            return super().save(**kwargs)
        # Le problème :
        # Le finally qui suit toujours relâche le verrou après chaque sauvegarde (ligne 2418), mais :
        #
        # Philosophie incohérente : Si le verrou doit être maintenu pendant toute la session (comme expliqué dans load()), il ne faut jamais le relâcher automatiquement après save().
        # Impact : Une autre instance ou processus pourrait modifier le fichier pendant que la session est encore active mais que le verrou a été relâché.
        finally:
            print(
                f"LockedTaskFile.save : Relâchement du verrou pour {self.filename()} après la sauvegarde."
            )
            self.release_lock()
        # return super().save(**kwargs)
        # # Ne pas relâcher le verrou - il doit rester pendant la session

    def mergeDiskChanges(self):
        """
        Fusionner les modifications du disque avec le fichier de tâches actuel, en acquérant un verrou si nécessaire.
        """
        # self.acquire_lock(self.filename())
        # try:
        #     super().mergeDiskChanges()
        # finally:
        #     self.release_lock()
        # We should already hold the lock from load()
        try:
            if not self.is_locked_by_me() and self.filename():
                print(
                    f"LockedTaskFile.mergeDiskChanges : Acquière un verrou pour {self.filename()} avant de fusionner les changements du disque."
                )
                self.acquire_lock(self.filename())
            super().mergeDiskChanges()
        finally:
            print(
                f"LockedTaskFile.mergeDiskChanges : Relâchement du verrou pour {self.filename()} après la fusion des changements du disque."
            )
            if self.__lock_acquired:  # Vérifier avant relâche
                self.release_lock()
