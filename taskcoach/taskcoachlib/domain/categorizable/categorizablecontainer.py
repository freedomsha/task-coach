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

import logging
from taskcoachlib.domain import base
from taskcoachlib import patterns

log = logging.getLogger(__name__)


class CategorizableContainer(base.Collection):
    """Une classe conteneur de catégorisables qui étend Collection de domain.base
    (une classe de collection qui étend CompositeSet de taskcoachlib.paterns).

    Collection qui est un ensemble d'objets de domaine
    fournit la méthode getObjectId pour récupérer un objet par son ID.

    Elle hérite aussi de CompositeCollection et de ObservableSet
    pour gérer les composites et leurs relations parent/enfant
    et avertir les observateurs quand un élément est ajouté ou supprimé.

    Cette classe représente un conteneur catégorisable
    (collection/ensemble d'objets de domaine catégorisable)
    et fournit deux méthodes pour ajouter ou retirer des éléments de la liste
    des catégorisables.

    Methods :
        - extend : Ajoute une liste d'éléments à la liste des catégorisables
        - removeItems : Retirer les éléments de la liste des catégorisables.
    """

    @patterns.eventSource
    def extend(self, items, event=None):
        log.info(
            f"CategorizableContainer.extend: pour {self}, items : {items}."
        )
        super().extend(items, event=event)
        log.debug(
            f"CategorizableContainer.extend : ajoute {items} à {super()} avec event={event}."
        )
        for item in self._compositesAndAllChildren(items):
            for category in item.categories():
                log.debug(
                    f"CategorizableContainer.extend : ajoute le catégorisable {item} à {category} avec event={event}."
                )
                category.addCategorizable(item, event=event)
        log.info(
            f"CategorizableContainer.extend: après traitement de {self}, items : {items} !"
        )

    @patterns.eventSource
    def removeItems(self, items, event=None):
        super().removeItems(items, event=event)
        for item in self._compositesAndAllChildren(items):
            for category in item.categories():
                category.removeCategorizable(item, event=event)
