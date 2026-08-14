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

import uuid
from taskcoachlib.domain import categorizable


class NoteContainer(categorizable.CategorizableContainer):
    """Conteneur de notes catégorisables.

    Hérite de CategorizableContainer qui est un conteneur de catégorisables
    qui étend Collection (une classe de collection qui étend CompositeSet).
    Collection qui est un ensemble d'objets de domaine
    fournit la méthode getObjectId pour récupérer un objet par son ID.
    CompositeSet hérite de CompositeCollection et de ObservableSet
    pour gérer les composites et leurs relations parent/enfant
    et avertir les observateurs quand un élément est ajouté ou supprimé.

    Cette classe représente un conteneur de notes catégorisables
    (collection/ensemble d'objets de domaine catégorisable)
    et fournit deux méthodes pour ajouter ou retirer des éléments
    de la liste des catégorisables.
    """

    # pass
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._note = None
        self.id = str(uuid.uuid4())
