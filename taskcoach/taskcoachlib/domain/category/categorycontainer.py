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
from taskcoachlib.domain import base
from taskcoachlib import patterns


# Choix de correction (options) :
# Option A* — Modifier CategoryList.init (recommandée) : accepter *args/**kwargs (ou categories=None) et transmettre ces arguments à super().init(...) puis définir self.id. Raison : cohérence avec TaskList/NoteContainer et appel existant category.CategoryList(categories). Minimal, peu intrusif.
# Option B — Modifier l'appel dans mergeDiskChanges : remplacer category.CategoryList(categories) par temp = category.CategoryList(); temp.extend(categories). Moins cohérent si d'autres sites appellent CategoryList(iterable).
# Option C — Créer constructeur explicite def init(self, categories=None, ...): super().init(categories) — variante d'A (plus explicite).
class CategoryList(base.Collection):
    """
    Classe de collection de catégories.

    Hérite de Collection qui représente un ensemble d'objets composites observables.
    Hérite donc de la méthode getObjectById pour récupérer un objet par son ID.
    Hérite de CompositeCollection et de ObservableSet pour gérer les composites
    et leurs relations parent/enfant et avertir les observateurs
    quand un élément est ajouté ou supprimé.

    Attributes :
        id : Identifiant de la collection de catégories.

    Methods :
        extend : Ajoutez plusieurs composites à la collection avec notification d'événement.
        removeItems : Supprimez plusieurs éléments composites de la collection avec notification d'événement.
        findCategoryByName : Cherche et retourne la catégorie avec ce nom.
        filteredCategories : Retourne une liste de categories qui sont filtrée (avec le filre Category.isFiltered() returns True).
        resetAllFilteredCategories : Remet à zéro toutes les catégories filtrées vers non-filtrées.
    """

    def __init__(self, *args, **kwargs):
        """Crée une Collection de catégories.

        Accept arbitrary positional/keyword arguments and pass them to the
        base Collection constructor so callers can construct a CategoryList
        from an iterable (e.g. CategoryList(categories)).

        Accèpte arbitrairement des arguments de position/avec mot clé
        et les passe au constructeur de base de la Collection
        ainsi les appellants peuvent contruire une CategoryList
        depuis un itérable (par exemple, CategoryList(categories)).

        Attributes :
            id : Identifiant de la collection de catégories.
        """
        super().__init__(*args, **kwargs)
        self.id = str(uuid.uuid4())

    @patterns.eventSource
    def extend(self, categories, event=None):
        super().extend(categories, event=event)
        for category in self._compositesAndAllChildren(categories):
            for categorizable in category.categorizables():
                categorizable.addCategory(category, event=event, modify=False)

    @patterns.eventSource
    def removeItems(self, categories, event=None):
        super().removeItems(categories, event=event)
        for category in self._compositesAndAllChildren(categories):
            for categorizable in category.categorizables():
                categorizable.removeCategory(category, event=event)

    def findCategoryByName(self, name):
        """Find a category by name."""
        for category in self:
            recursive = " -> " in name
            if category.subject(recursive=recursive) == name:
                return category
        return None

    def filteredCategories(self):
        """Return a list of categories that are filtered (i.e. for which isFiltered() returns True)."""
        return [category for category in self if category.isFiltered()]

    @patterns.eventSource
    def resetAllFilteredCategories(self, event=None):
        """Reset all filtered categories to unfiltered."""
        for category in self:
            category.setFiltered(False, event=event)
