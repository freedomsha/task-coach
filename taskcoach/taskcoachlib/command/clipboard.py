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


Description :
    Ce fichier-module définit une classe singleton nommée Clipboard qui gère le presse-papier de l'application Task Coach.

Fonctionnalité principale :
    Fournit des méthodes pour copier et coller des éléments (probablement des tâches, des notes, etc.) dans l'application.
    Suit le modèle singleton pour garantir qu'il n'existe qu'une seule instance du presse-papier dans l'application.

Méthodes principales :
    put(items, source) : Copie un ensemble d'éléments (items) dans le presse-papier, en stockant également la source (source) de ces éléments.
    get() : Récupère le contenu actuel du presse-papier, y compris les éléments (items) et la source (source).
    peek() : Renvoie uniquement le contenu actuel du presse-papier (éléments items).
    clear() : Vide le presse-papier en supprimant les éléments et la source stockés.
    __nonzero__() (méthode magique) : Vérifie si le presse-papier contient des éléments (renvoie True si le presse-papier n'est pas vide).

Remarques :
    La méthode __nonzero__() est une ancienne méthode pour vérifier la vérité d'un objet. Dans les versions modernes de Python, il est recommandé d'utiliser la méthode __bool__() à la place.
    Le code ne montre pas explicitement comment les éléments sont copiés ou collés à partir de l'interface utilisateur.

En résumé, ce fichier fournit une implémentation de base pour le presse-papier dans Task Coach, permettant de copier et coller des éléments tout en gardant la trace de leur source.
"""

from taskcoachlib import patterns


class Clipboard(metaclass=patterns.Singleton):
    """Classe qui gère le presse-papier de l'application Task Coach."""

    def __init__(self):
        self._contents = []
        self._source = None
        self.clear()  # Fait la même chose que les deux lignes précédentes

    def put(self, items, source):
        """Copie un ensemble d'éléments (items) dans le presse-papier, en stockant également la source (source) de ces éléments."""
        # pylint: disable=W0201
        self._contents = items
        self._source = source

    def get(self):
        """Récupère le contenu actuel du presse-papier, y compris les éléments (items) et la source (source)."""
        currentContents = self._contents
        currentSource = self._source
        return currentContents, currentSource

    def peek(self):
        """Renvoie uniquement le contenu actuel du presse-papier (éléments items)."""
        return self._contents

    def clear(self):
        """Vide le presse-papier en supprimant les éléments et la source stockés."""
        self._contents = []
        self._source = None

    def __nonzero__(self):
        """Méthode magique qui vérifie si le presse-papier contient des éléments
        (renvoie True si le presse-papier n'est pas vide).

        Remarques :
            La méthode __nonzero__() est une
            ancienne méthode pour vérifier la vérité d'un objet.
            Dans les versions modernes de Python,
            il est recommandé d'utiliser la méthode __bool__() à la place.
        """
        return len(self._contents)

    def __bool__(self):
        return len(self._contents) > 0
