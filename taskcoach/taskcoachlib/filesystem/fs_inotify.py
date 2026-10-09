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

# inotify wrapper from this recipe: http://code.activestate.com/recipes/576375-low-level-inotify-wrapper/
# Slightly modified to handle timeout and use select(); cleanup error handling

import logging
from twisted.internet.inotify import INotify
from twisted.python.filepath import FilePath

# from . import base
from taskcoachlib.filesystem import base
import os

log = logging.getLogger(__name__)


class FilesystemNotifier(base.NotifierBase):
    """
    Une classe de notification qui utilise inotify pour surveiller les modifications du système de fichiers.

    Cette classe est un wrapper autour de la classe INotify du framework Twisted.
    Elle surveille un fichier spécifique et déclenche un événement lorsque le fichier est modifié.
    """

    def __init__(self):
        """
        Initialisez le FilesystemNotifier.
        """
        log.debug(
            "FilesystemNotifier.__init__ : initialisation du notificateur utilisant inotify"
        )
        # super(FilesystemNotifier, self).__init__()
        super().__init__()
        # Création de l'objet INotify, conteneur de données interne self.notifier :
        self.notifier = INotify()
        # Commencer à attendre l'accessibilité de la lecture :
        self.notifier.startReading()
        log.debug("FilesystemNotifier initialisé !")

    def setFilename(self, filename):
        """
        Définissez le nom du fichier à surveiller.

        Args :
            filename (str) : Le nom du fichier à surveiller.
        """
        if self._path is not None:
            self.notifier.ignore(FilePath(self._path))
        # super(FilesystemNotifier, self).setFilename(filename)
        super().setFilename(filename)
        if self._path is not None:
            self.notifier.watch(
                FilePath(self._path), callbacks=[self.__notify]
            )

    def stop(self):
        """
        Arrête le notificateur de lire les événements du système de fichiers.
        """
        if self.notifier is not None:
            self.notifier.stopReading()
            self.notifier = None

    def __notify(self, handle, filepath, mask):
        """
        Fonction de rappel pour les événements inotify.

        Args :
            handle : Le handle inotify.
            filepath (FilePath) : Le chemin du fichier qui a déclenché l'événement.
            mask (int) : Le masque d'événement.
        """
        myName = self._filename
        if myName is not None:
            if filepath.basename() == os.path.split(myName)[-1]:
                if self._check(myName) and myName:
                    self.stamp = os.stat(myName).st_mtime
                    self.onFileChanged()

    def onFileChanged(self):
        """
        Gestionnaire d'événements pour les événements de modification de fichier.

        Cette méthode doit être implémentée par des sous-classes.
        """
        raise NotImplementedError
