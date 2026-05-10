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
import atexit


class NotifierBase(object):
    """
    Classe de base pour les notificateurs.

    Cette classe fournit une structure de base pour l'implémentation des notificateurs dans TaskCoach.
    Les sous-classes doivent remplacer la méthode `stop` si nécessaire.

    Attributs :
        _filename (str) : Le nom de fichier associé au notificateur.
        _path (str) : Le chemin du fichier.
        _name (str) : Le nom du fichier.
        stamp (float) : L'horodatage de modification du fichier.
    """

    def __init__(self):
        # super(NotifierBase, self).__init__()
        super().__init__()

        self._filename = None
        self._path = None
        self._name = None
        self.stamp = None
        # Enregistrer __stopWhenExit comme fonction à exécuter lors d'un arrêt normal du programme.
        atexit.register(self.__stopWhenExit)

    def __stopWhenExit(self):
        """
        Enregistrez __stopWhenExit comme fonction à exécuter lors d'un arrêt normal du programme.
        """
        self.stop()

    def stop(self):
        """
        Arrêtez le notificateur.

        Cette méthode doit être (overridden) remplacée/surchargée par des sous-classes si nécessaire.
        """
        pass

    def _check(self, filename):
        """
        Vérifiez si le fichier a été modifié.

        Args :
            filename (str) : Le nom du fichier à vérifier.

        Returns :
            (bool) : True si le fichier a été modifié, Faux sinon.
        """
        return self.stamp is None or (
            filename
            and os.path.exists(filename)
            and os.stat(filename).st_mtime > self.stamp
        )

    def setFilename(self, filename):
        """
        Définissez le nom de fichier associé au notificateur.

        Args :
            filename (str) : Le nom de fichier à définir.
        """
        self._filename = filename
        self.stamp = None
        if filename:
            self._path, self._name = os.path.split(filename)
            if os.path.exists(filename):
                self.stamp = os.stat(filename).st_mtime
        else:
            self._path, self._name = None, None

    def saved(self):
        """
        Mettez à jour l'horodatage de modification en fonction du fichier.

        Cette méthode doit être appelée une fois le fichier enregistré.

        Note :
            Si le nom de fichier n'est pas défini ou si le fichier n'existe pas, l'horodatage est défini sur Aucun.
        """
        if self._filename and os.path.exists(self._filename):
            self.stamp = os.stat(self._filename).st_mtime
        else:
            self.stamp = None
