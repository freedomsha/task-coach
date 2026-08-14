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
from taskcoachlib import patterns
from taskcoachlib.domain import base
from taskcoachlib.domain.attribute import font, color

log = logging.getLogger(__name__)


class CategorizableCompositeObject(base.CompositeObject):
    """
    Les CatégorizableCompositeObjects sont des objets composites qui peuvent
    être classés en les ajoutant à une ou plusieurs catégories.

    Hérite de CompositeObject pour contenir d'autres objets en tant qu'enfants.
    Cette classe étend Object et ObservableComposite pour fournir des méthodes
    supplémentaires pour gérer les objets enfants et leur état.

    Des exemples d'objets composites catégorisables sont les tâches et les notes.

    Attributes :
        __categories : Un SetAttribute qui stocke les catégories auxquelles cet objet composite catégorisable appartient.

    """

    def __init__(self, *args, **kwargs):
        log.debug("CategorizableCompositeObject : Initialisation.")
        self.__categories = base.SetAttribute(
            kwargs.pop("categories", set()),
            self,
            self.addCategoryEvent,
            self.removeCategoryEvent,
        )
        log.debug(
            f"CategorizableCompositeObject : méthode super avec args={args} et kwargs={kwargs}."
        )
        children = kwargs.pop("children", [])  # ✅ Extrait les enfants des kwargs
        # super().__init__(*args, **kwargs)
        super().__init__(children=children, *args, **kwargs)  # ✅ Passe les enfants à CompositeObject
        log.debug("CategorizableCompositeObject : Initialisé.")

    def __getstate__(self):
        state = super().__getstate__()
        log.debug(
            f"CategorizableCompositeObject.__getstate__ : state avant update : {state}"
        )
        state.update(dict(categories=self.categories()))
        log.debug(
            f"CategorizableCompositeObject.__getstate__ : renvoie {state}."
        )
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        log.debug(
            f"CategorizableCompositeObject.__setstate__ : pour state {state} et event {event}"
        )
        super().__setstate__(state, event=event)
        # Définit les catégories à partir de l'état, en utilisant la méthode setCategories pour gérer les événements et les mises à jour d'apparence.
        self.setCategories(state["categories"], event=event)
        # # Gérer uniquement les attributs spécifiques à CategorizableCompositeObject, comme 'categories'.
        # categories_value = state.pop("categories", set()) # Exemple d'attribut spécifique à CategorizableCompositeObject
        # if isinstance(categories_value, base.SetAttribute):
        #     self.__categories = categories_value
        # else:
        #     self.__categories = base.SetAttribute(
        #         categories_value, self, self.addCategoryEvent, self.removeCategoryEvent
        #     )
        # log.debug(f"CategorizableCompositeObject.__setstate__() - subject après set: {self.__subject.get()}")
        # AttributeError: 'Task' object has no attribute '_CategorizableCompositeObject__subject'
        if hasattr(self, "subject"):
            log.debug(
                f"CategorizableCompositeObject.__setstate__() - subject après set: {self.subject} !"
            )
        else:
            log.debug(
                "CategorizableCompositeObject.__setstate__() - subject non défini !"
            )

    def __getcopystate__(self):
        state = super().__getcopystate__()
        log.debug(
            f"CategorizableCompositeObject.__getcopystate__ : state avant update {state}."
        )
        state.update(dict(categories=self.categories()))
        log.debug(
            f"CategorizableCompositeObject.__getcopystate__ : retourne state {state}."
        )
        return state

    def categories(self, recursive=False, upwards=False):
        """Retourne les catégories auxquelles appartient cet objet catégorisable composite."""
        # print(f"CategorizableCompositeObject.categories : 🔍 DEBUG - Appel de categories() pour {self.id()} | Retour = {self.__categories}")
        result = self.__categories.get()
        # print(f"CategorizableCompositeObject.categories : Retour=result={result}")
        if recursive and upwards and self.parent() is not None:
            result |= self.parent().categories(recursive=True, upwards=True)
        elif recursive and not upwards:
            for child in self.children(recursive=True):
                result |= child.categories()
        return result

    @classmethod
    def categoryAddedEventType(class_):
        """Retourne le type d'événement pour l'ajout d'une catégorie.

        Les événements de ce type sont déclenchés lorsqu'une catégorie
        est ajoutée à un objet catégorisable composite,
        et peuvent être utilisés pour mettre à jour l'apparence
        ou d'autres propriétés de l'objet en fonction de la nouvelle catégorie.
        """
        return "categorizable.category.add"

    # Bug SetAttribute (categorizable.py) :
    # La classe SetAttribute attend souvent un ensemble de valeurs.
    # Si on lui passe un objet unique sans le mettre dans un set ({obj}),
    # cela peut provoquer des erreurs d'itération ou d'ajout.
    # La correction ici est importante pour la stabilité.
    def addCategory(self, *categories, **kwargs):
        """Ajoute une ou plusieurs catégories à cet objet composite catégorisable."""
        # print(f"CategorizableCompositeObject.addCategory : 🛠 DEBUG - Ajout de {categories} à {self} dans {self.__class__.__name__}")
        # return self.__categories.add(set(categories), event=kwargs.pop("event", None))
        # self.__categories.update(categories)  # Ajoute les catégories. Erreur, update() ne fonctionne pas.
        for category in categories:
            # self.__categories.add(category)  # Utilise add() pour un SetAttribute. ⚠️ Erreur, category est un objet et pas un set
            self.__categories.add(
                {category}
            )  # ✅ Convertit en set avant l'ajout
        # print(f"CategorizableCompositeObject.addCategory : ✅ DEBUG - self.__categories après ajout = {self.__categories}")

        return True  # Retourne True pour que Task.addCategory() fonctionne

    def addCategoryEvent(self, event, *categories):
        """
        Gère l'événement d'ajout de catégorie en ajoutant la source de
        l'événement pour cet objet et ses enfants,
        et en déclenchant un changement d'apparence si nécessaire.

        Args :
            event : L'événement d'ajout de catégorie.
            *categories : Les catégories qui ont été ajoutées.
        """
        event.addSource(
            self, *categories, **dict(type=self.categoryAddedEventType())
        )
        for child in self.children(recursive=True):
            event.addSource(
                child, *categories, **dict(type=child.categoryAddedEventType())
            )
        if self.categoriesChangeAppearance(categories):
            self.appearanceChangedEvent(event)

    def categoriesChangeAppearance(self, categories):
        """
        Détermine si l'ajout ou la suppression de catégories change l'apparence de cet objet composite catégorisable.

        Args:
            categories : Les catégories qui ont été ajoutées ou supprimées.

        Returns:
            True si l'apparence change en raison de l'ajout ou de la suppression de catégories, False sinon.
        """
        return (
            self.categoriesChangeFgColor(categories)
            or self.categoriesChangeBgColor(categories)
            or self.categoriesChangeFont(categories)
            or self.categoriesChangeIcon(categories)
        )

    def categoriesChangeFgColor(self, categories):
        """Détermine si l'ajout ou la suppression de catégories change la couleur de premier plan de cet objet composite catégorisable."""
        return not self.foregroundColor() and any(
            category.foregroundColor(recursive=True) for category in categories
        )

    def categoriesChangeBgColor(self, categories):
        """Détermine si l'ajout ou la suppression de catégories change la couleur de fond de cet objet composite catégorisable."""
        return not self.backgroundColor() and any(
            category.backgroundColor(recursive=True) for category in categories
        )

    def categoriesChangeFont(self, categories):
        """Détermine si l'ajout ou la suppression de catégories change la police de cet objet composite catégorisable."""
        return not self.font() and any(
            category.font(recursive=True) for category in categories
        )

    def categoriesChangeIcon(self, categories):
        """Détermine si l'ajout ou la suppression de catégories change l'icône de cet objet composite catégorisable."""
        return not self.icon() and any(
            category.icon(recursive=True) for category in categories
        )

    @classmethod
    def categoryRemovedEventType(class_):
        """Retourne le type d'événement pour la suppression d'une catégorie."""
        return "categorizable.category.remove"

    def removeCategory(self, *categories, **kwargs):
        """Supprime une ou plusieurs catégories de cet objet composite catégorisable."""
        return self.__categories.remove(
            set(categories), event=kwargs.pop("event", None)
        )

    def removeCategoryEvent(self, event, *categories):
        """
        Gère l'événement de suppression de catégorie en ajoutant la source de
        l'événement pour cet objet et ses enfants,
        et en déclenchant un changement d'apparence si nécessaire.
        """
        event.addSource(
            self, *categories, **dict(type=self.categoryRemovedEventType())
        )
        for child in self.children(recursive=True):
            event.addSource(
                child,
                *categories,
                **dict(type=child.categoryRemovedEventType()),
            )
        if self.categoriesChangeAppearance(categories):
            self.appearanceChangedEvent(event)

    def setCategories(self, categories, event=None):
        """Remplace les catégories de cet objet composite catégorisable par un nouvel ensemble de catégories."""
        # print(
        #     f"CategorizableCompositeObject.setCategory : 🛠 DEBUG - Règle de {categories} à {self} dans {self.__class__.__name__}")
        return self.__categories.set(set(categories), event=event)
        # return self.__categories.add(set(categories), event=kwargs.pop("event", None))
        # self.__categories.update(categories)  # Ajoute les catégories. Erreur, update() ne fonctionne pas.
        # for category in categories:
        #     # self.__categories.add(category)  # Utilise add() pour un SetAttribute. ⚠️ Erreur, category est un objet et pas un set
        #     self.__categories.set({category})  # ✅ Convertit en set avant l'ajout
        # print(f"CategorizableCompositeObject.setCategory : ✅ DEBUG - self.__categories après réglage = {self.__categories}")

    @staticmethod
    def categoriesSortFunction(**kwargs):
        """
        Renvoyer une clé de tri pour le tri par les catégories.
        Étant donné qu'une catégorisable peut avoir plusieurs catégories,
        nous triez d'abord les catégories par leurs sujets. Si le trieur
        est en mode arborescence, nous prenons également les catégories
        des enfants Catégorizables, après les catégories de la catégorizable
        elle-même. Si le trieur est en mode liste, nous apportons également
        les catégories du parent (récursivement) en compte, encore une fois
        après les catégories de la catégorisable elle-même.

        Args :
            **kwargs : Arguments optionnels pour configurer la fonction de tri,
                       tels que "treeMode" pour indiquer si le tri
                       est en mode arborescence ou liste.

        Returns :
            Une fonction de clé de tri qui peut être utilisée
            pour trier les objets catégorisables en fonction de leurs catégories.
        """

        def sortKeyFunction(categorizable):
            """
            Fonction de clé de tri pour les objets catégorisables, basée sur les sujets de leurs catégories.

            Args :
                categorizable : L'objet catégorisable pour lequel calculer la clé de tri.

            Returns :
                Une liste de sujets de catégories triés,
                qui peut être utilisée comme clé de tri pour les objets catégorisables.
            """

            def sortedSubjects(items):
                """
                Retourne les sujets des items triés par nom.

                Args :
                    items : Liste d'éléments.

                Returns :
                    Les sujets des items triés par nom.
                """
                return sorted([item.subject(recursive=True) for item in items])

            categories = categorizable.categories()
            # Tri la liste des sujets des catégories par nom.
            sortedCategorySubjects = sortedSubjects(categories)
            isListMode = not kwargs.get("treeMode", False)
            # Retire les catégories triées de la liste des catégories catégorisables.
            childCategories = (
                categorizable.categories(recursive=True, upwards=isListMode)
                - categories
            )
            # Ajoute les catégories enfants triées par nom de sujet à la liste des catégories triées.
            sortedCategorySubjects.extend(sortedSubjects(childCategories))
            # Retourne la liste des catégories triées par sujet.
            return sortedCategorySubjects

        return sortKeyFunction

    @classmethod
    def categoriesSortEventTypes(class_):
        """Les types d'événements qui influencent l'ordre de tri des catégories."""
        # return (class_.categoryAddedEventType(), class_.categoryRemovedEventType())
        return (
            class_.categoryAddedEventType(),
            class_.categoryRemovedEventType(),
        )

    def foregroundColor(self, recursive=False):
        myOwnFgColor = super().foregroundColor()
        if myOwnFgColor or not recursive:
            return myOwnFgColor
        categoryBasedFgColor = self._categoryForegroundColor()
        if categoryBasedFgColor:
            return categoryBasedFgColor
        else:
            return super().foregroundColor(recursive=True)

    def backgroundColor(self, recursive=False):
        myOwnBgColor = super().backgroundColor()
        if myOwnBgColor or not recursive:
            return myOwnBgColor
        categoryBasedBgColor = self._categoryBackgroundColor()
        if categoryBasedBgColor:
            return categoryBasedBgColor
        else:
            return super().backgroundColor(recursive=True)

    def _categoryForegroundColor(self):
        """Si un objet catégorisable appartient à une catégorie qui a
        une couleur de premier plan qui lui est associée,
        l'objet catégorisable est coloré en conséquence. Lorsqu'un objet
        catégorisable appartient à plusieurs catégories, la couleur est mélangée.
        Si un objet composite catégorisable n'a pas de couleur de premier plan,
        il utilise la couleur de premier plan des parents."""
        colors = [
            category.foregroundColor(recursive=True)
            for category in self.categories()
        ]
        if not colors and self.parent():
            return self.parent()._categoryForegroundColor()
        else:
            return color.ColorMixer.mix(colors)

    def _categoryBackgroundColor(self):
        """If a categorizable object belongs to a category that has a
        background color associated with it, the categorizable object is
        colored accordingly. When a categorizable object belongs to
        multiple categories, the color is mixed. If a categorizable
        composite object has no background color of its own, it uses its
        parent's background color."""
        colors = [
            category.backgroundColor(recursive=True)
            for category in self.categories()
        ]
        if not colors and self.parent():
            return self.parent()._categoryBackgroundColor()
        else:
            return color.ColorMixer.mix(colors)

    def font(self, recursive=False):
        myFont = super().font()
        if myFont or not recursive:
            return myFont
        categoryBasedFont = self._categoryFont()
        if categoryBasedFont:
            return categoryBasedFont
        else:
            return super().font(recursive=True)

    def _categoryFont(self):
        """If a categorizable object belongs to a category that has a
        font associated with it, the categorizable object uses that font.
        When a categorizable object belongs to multiple categories, the
        font is mixed. If a categorizable composite object has no font of
        its own, it uses its parent's font."""
        fonts = [
            category.font(recursive=True) for category in self.categories()
        ]
        if not fonts and self.parent():
            return self.parent()._categoryFont()
        else:
            return font.FontMixer.mix(*fonts)  # pylint: disable=W0142

    def icon(self, recursive=False):
        icon = super().icon()
        if not icon and recursive:
            icon = self.categoryIcon() or super().icon(recursive=True)
        return icon

    def categoryIcon(self):
        """If a categorizable object belongs to a category that has an icon
        associated with it, the categorizable object uses that icon. When a
        categorizable object belongs to multiple categories,
        the icon of the first category with an icon is used.
        If a categorizable composite object has no icon of its own,
        it uses its parent's icon.

        En français : Si un objet catégorisable appartient à une catégorie
        qui a une icône associée, l'objet catégorisable utilise cette icône.
        Lorsqu'un objet catégorisable appartient à plusieurs catégories,
        l'icône de la première catégorie avec une icône est utilisée.
        Si un objet composite catégorisable n'a pas d'icône propre,
        il utilise l'icône de son parent.
        """
        icon = ""
        for category in self.categories():
            icon = category.icon(recursive=True)
            if icon:
                return icon
        if self.parent():
            return self.parent().categoryIcon()
        else:
            return ""

    def selectedIcon(self, recursive=False):
        icon = super().selectedIcon()
        if not icon and recursive:
            icon = self.categorySelectedIcon() or super().selectedIcon(
                recursive=True
            )
        return icon

    def categorySelectedIcon(self):
        """
        If a categorizable object belongs to a category that has a selected
        """
        icon = ""
        for category in self.categories():
            icon = category.selectedIcon(recursive=True)
            if icon:
                return icon
        if self.parent():
            return self.parent().categorySelectedIcon()
        else:
            return ""

    @classmethod
    def categorySubjectChangedEventType(class_):
        """
        Renvoyer

        Returns:

        """
        return "categorizable.category.subject"

    def categorySubjectChangedEvent(self, event, subject):
        for categorizable in [self] + self.children(recursive=True):
            event.addSource(
                categorizable,
                subject,
                type=categorizable.categorySubjectChangedEventType(),
            )

    @classmethod
    def modificationEventTypes(class_):
        eventTypes = super().modificationEventTypes()
        if eventTypes is None:
            # eventTypes = []
            eventTypes = list()
        return eventTypes + [
            class_.categoryAddedEventType(),
            class_.categoryRemovedEventType(),
        ]
