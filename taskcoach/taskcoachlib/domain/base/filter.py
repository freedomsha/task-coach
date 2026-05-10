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
import re

# import sre_constants # inutile avec re sous python 3
from taskcoachlib import patterns
from taskcoachlib.domain.base import object as domainobject

log = logging.getLogger(__name__)


class Filter(patterns.SetDecorator):
    """
    Classe de base abstraite pour les filtres qui décorent un ensemble d'articles.

    Cette classe fournit une implémentation de base pour le filtrage des éléments
    dans un ensemble et la maintenance d'un sous-ensemble d'éléments qui passent
    les critères de filtre. Il utilise le modèle SetDecorator pour décorer un
    ensemble d'objets observables.

    Ivar Args :
        __treeMode : Un booléen indiquant si le filtre doit fonctionner en mode arborescence.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance de filtre.

        Args :
            args : Arguments de position transmis au constructeur de superclasse.
            *kwargs : Arguments de mots clés transmis au constructeur de superclasse.
                       Les arguments de mots clés suivants sont pris en charge :
            Keyword Args :
                treeMode : Un booléen indiquant si le filtre doit fonctionner en mode arborescence.
        """
        self.__treeMode = kwargs.pop("treeMode", False)
        # Track items added as ancestors to maintain tree hierarchy, not because
        # they matched filter criteria. Used by outer filters for orphan cleanup.
        self.__filterForced = set()
        super().__init__(*args, **kwargs)
        self.reset()

    def thaw(self):
        """
        Dégèle le filtre, réactivant le filtrage après un gel.
        """
        log.debug(f"Filter.thaw : degèle le filtre {self.__class__.__name__}.")
        super().thaw()  # Boucle entre ici et patterns.observer.CollectionDecorator.thaw
        if not self.isFrozen():
            self.reset()
        log.debug(f"Filter.thaw : filtre {self.__class__.__name__} dégelé !")

    def setTreeMode(self, treeMode):
        """
        Définit le mode arborescence pour le filtre.

        Args :
            treeMode : Un booléen indiquant si le filtre doit fonctionner en mode arborescence.
        """
        self.__treeMode = treeMode
        try:
            self.observable().setTreeMode(treeMode)
        except AttributeError:
            pass
        self.reset()

    def treeMode(self):
        """
        Renvoie le mode arborescence actuel du filtre.

        Return :
            Un booléen indiquant si le filtre fonctionne en mode arborescence.
        """
        log.debug(
            f"Filter.treeMode : renvoie le mode d'arborescence actuel de {self.__class__.__name__}: {self.__treeMode}."
        )
        return self.__treeMode

    @patterns.eventSource
    def reset(self, event=None):
        """
        Réinitialise le filtre, réappliquez les critères du filtre à l'ensemble observable.

        Args :
            event : Un objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        log.debug(
            f"Filter.reset : réinitialisation du filtre pour self={self.__class__.__name__}, event={event}."
        )
        if self.isFrozen():
            log.debug(
                f"Filter.reset : self={self.__class__.__name__} est Gelé !."
            )
            return

        filteredItems = set(self.filterItems(self.observable()))
        log.debug(f"Filter.reset : l'attribut filteredItems={filteredItems}")
        if self.treeMode():
            log.debug(
                f"Filter.reset : remet à jour filteredItems car self.treeMode est {self.treeMode()}"
            )
            for item in filteredItems.copy():
                log.debug(f"Filter.reset : pour item={item}")
                filteredItems.update(set(item.ancestors()))  # Erreur !
                log.debug(f"filteredItems devient {filteredItems}.")
        log.debug(f"Filter.reset : filteredItems est devenu {filteredItems}.")
        self.removeItemsFromSelf(
            [item for item in self if item not in filteredItems], event=event
        )
        self.extendSelf(
            [item for item in filteredItems if item not in self], event=event
        )
        log.debug(f"Filter.reset : self est devenu {self}.")
        log.debug("Filter.reset : filtre réinitialisé !")

    def getFilterForced(self):
        """Return items that were added as ancestors, not directly matched.

        These items are in the filter only to maintain tree hierarchy, not
        because they passed the filter criteria.
        """
        return self.__filterForced.copy()

    def getAccumulatedFilterForced(self):
        """Return filter_forced items accumulated from the entire filter chain.

        Walks up the filter chain (via observable()) to collect all items that
        were added as ancestors by any filter in the chain. This is used by
        the outermost filter (typically ViewFilter) to identify items that may
        need cleanup if they've become orphans.

        Example: CategoryFilter adds a parent as ancestor of a categorized child.
        ViewFilter later hides the child (completed). ViewFilter uses this method
        to find that the parent was filter_forced, and removes it since it has
        no visible children.
        """
        accumulated = self.__filterForced.copy()
        try:
            inner = self.observable()
            if hasattr(inner, "getAccumulatedFilterForced"):
                accumulated |= inner.getAccumulatedFilterForced()
        except AttributeError:
            pass
        return accumulated

    def filterItems(self, items):
        """Ce filtre renvoie les éléments qui passent le filtre.

        Filtre les articles donnés, ne renvoyant que ceux qui passent les critères de filtre.

        Args :
            items : Un itérable d'articles à filtrer.
        Return :
            Une liste d'éléments qui transmettent les critères de filtre.
        Raises :
            NotImplementedError : Si la méthode n'est pas implémentée dans une sous-classe.
        """
        raise NotImplementedError  # pragma: no cover

    def rootItems(self) -> list:
        """
        Renvoie les éléments racinaires dans l'ensemble filtré.

        Return : Une liste d'éléments qui n'ont pas de parent.
        """
        rootItems_to_return = [item for item in self if item.parent() is None]
        log.debug(f"Filter.rootItems : renvoie {rootItems_to_return}")
        # return [item for item in self if item.parent() is None]
        return rootItems_to_return

    def onAddItem(self, event):
        """
        Gère l'ajout d'un élément à l'ensemble observable.

        Args :
            event : Un objet d'événement contenant des informations sur l'élément ajouté.
        """
        self.reset()

    def onRemoveItem(self, event):
        """
        Gère le retrait d'un élément de l'ensemble observable.

        Args :
            event : Un objet d'événement contenant des informations sur l'élément supprimé.
        """
        self.reset()
        # self.reset(event)


class SelectedItemsFilter(Filter):
    """
    Un filtre qui ne comprend que des éléments sélectionnés ou qui sont des ancêtres d'articles sélectionnés.

    Ivar :
        __selectedItems : Un ensemble d'éléments sélectionnés.
        __includeSubItems : Un booléen indiquant s'il faut inclure des sous-éléments d'articles sélectionnés.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance SelectedItemsFilter.

        Args :
            args : Arguments de position transmis au constructeur de superclasse.
            *kwargs : Arguments de mots clés transmis au constructeur de superclasse.
                       Les arguments de mots clés suivants sont pris en charge :
            Keyword Args :
                selectedItems : Un itérable d'articles à sélectionner initialement.
                includeSubItems : Un booléen indiquant s'il faut inclure des sous-éléments d'articles sélectionnés.
        """
        self.__selectedItems = set(kwargs.pop("selectedItems", []))
        self.__includeSubItems = kwargs.pop("includeSubItems", True)
        super().__init__(*args, **kwargs)

    @patterns.eventSource
    def removeItemsFromSelf(self, items, event=None):
        """
        Supprime les éléments donnés de l'ensemble filtré et met à jour les éléments sélectionnés.

        Args :
            items : Un itérable d'articles à supprimer.
            *event : Un objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        super().removeItemsFromSelf(items, event)
        self.__selectedItems.difference_update(set(items))
        if not self.__selectedItems:
            self.extendSelf(self.observable(), event)

    def filterItems(self, items):
        """
        Filtre les éléments donnés, ne renvoyant que ceux qui sont sélectionnés ou sont des ancêtres des articles sélectionnés.

        Args :
            items : Un itérable d'articles à filtrer.
        Return :
            Une liste d'éléments sélectionnés ou qui sont des ancêtres d'articles sélectionnés.
        """
        if self.__selectedItems:
            result = [
                item
                for item in items
                if self.itemOrAncestorInSelectedItems(item)
            ]
            if self.__includeSubItems:
                for item in result[:]:
                    result.extend(item.children(recursive=True))
            return result
        else:
            return [item for item in items if item not in self]

    def itemOrAncestorInSelectedItems(self, item):
        """
        Checks if the given item or any of its ancestors are in the selected items.

        Args :
            item : L'article à vérifier.
        Return :
            bool : Vrai si l'article ou l'un de ses ancêtres est dans les éléments sélectionnés, faux autrement.
        """
        if item in self.__selectedItems:
            return True
        elif item.parent():
            return self.itemOrAncestorInSelectedItems(item.parent())
        else:
            return False


class SearchFilter(Filter):
    """
    Un filtre qui ne comprend que des éléments qui correspondent à une chaîne de recherche.

    Ce filtre vous permet de rechercher des éléments basés sur une chaîne
    de recherche donnée, avec des options de sensibilité à la casse,
    y compris des sous-éléments, la recherche dans la description
    et l'utilisation d'expressions régulières.

    Ivar Args :
        __includeSubItems : Un booléen indiquant s'il faut inclure des sous-éléments d'articles correspondants.
        __searchDescription : Un booléen indiquant s'il faut rechercher dans la description de l'article.
        __regularExpression : Un booléen indiquant si la chaîne de recherche est une expression régulière.
        __searchPredicate : Un texte appelant un texte et renvoie True si l'élément correspond aux critères de recherche.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance SearchFilter.

        Args :
            args : Arguments de position transmis au constructeur de superclasse.
            *kwargs : Arguments de mots clés transmis au constructeur de superclasse.
                       Les arguments de mots clés suivants sont pris en charge :
            Keyword Args :
                searchString : La chaîne à rechercher.
                matchCase : Un booléen indiquant si la recherche doit être sensible à la cas.
                includeSubItems : Un booléen indiquant s'il faut inclure des sous-éléments d'articles correspondants.
                searchDescription : Un booléen indiquant s'il faut rechercher dans la description de l'article.
                regularExpression : Un booléen indiquant si la chaîne de recherche est une expression régulière.
        """
        searchString = kwargs.pop("searchString", "")
        matchCase = kwargs.pop("matchCase", False)
        includeSubItems = kwargs.pop("includeSubItems", False)
        # self.__includeSubItems = includeSubItems = kwargs.pop("includeSubItems", False)
        searchDescription = kwargs.pop("searchDescription", False)
        # self.__searchDescription = searchDescription = kwargs.pop("searchDescription", False)
        regularExpression = kwargs.pop("regularExpression", False)
        # self.__regularExpression = regularExpression = kwargs.pop("regularExpression", False)

        self.setSearchFilter(
            searchString,
            matchCase=matchCase,
            includeSubItems=includeSubItems,
            searchDescription=searchDescription,
            regularExpression=regularExpression,
            doReset=False,
        )

        super().__init__(*args, **kwargs)

    def setSearchFilter(
        self,
        searchString,
        matchCase=False,
        includeSubItems=False,
        searchDescription=False,
        regularExpression=False,
        doReset=True,
    ):
        """
        Définit les paramètres de filtre de recherche.

        Args :
            searchString : La chaîne de caractères à rechercher.
            matchCase : Un booléen indiquant si la recherche doit être sensible à la cas.
            includeSubItems : Un booléen indiquant s'il faut inclure des sous-éléments d'articles correspondants.
            searchDescription : Un booléen indiquant s'il faut rechercher dans la description de l'article.
            regularExpression : Un booléen indiquant si la chaîne de recherche est une expression régulière.
            doReset : Un booléen indiquant s'il faut réinitialiser le filtre après avoir réglé les paramètres.
        """
        # pylint: disable=W0201
        self.__includeSubItems = includeSubItems
        self.__searchDescription = searchDescription
        self.__regularExpression = regularExpression
        self.__searchPredicate = self.__compileSearchPredicate(
            searchString, matchCase, regularExpression
        )
        if doReset:
            self.reset()

    @staticmethod
    def __compileSearchPredicate(searchString, matchCase, regularExpression):
        """
        Compile un prédicat de recherche en fonction des paramètres donnés.

        Args :
            searchString : La chaîne à rechercher.
            matchCase : Un booléen indiquant si la recherche doit être sensible à la cas.
            regularExpression : Un booléen indiquant si la chaîne de recherche est une expression régulière.
        Return :
            Un texte appelant un texte et renvoie True si l'élément correspond aux critères de recherche.
        """
        if not searchString:
            return ""
        flag = 0 if matchCase else re.IGNORECASE | re.UNICODE
        if regularExpression:
            try:
                rx = re.compile(searchString, flag)
            # except sre_constants.error:
            except re.error:
                if matchCase:
                    return lambda x: x.find(searchString) != -1
                else:
                    return lambda x: x.lower().find(searchString.lower()) != -1
            else:
                return rx.search
        elif matchCase:
            return lambda x: x.find(searchString) != -1
        else:
            return lambda x: x.lower().find(searchString.lower()) != -1

    def filterItems(self, items):
        """
        Filtre les éléments donnés, ne renvoyant que ceux qui correspondent aux critères de recherche.

        Args :
            items : Un itérable d'articles à filtrer.
        Return :
            Une liste d'éléments qui correspondent aux critères de recherche.
        """
        return (
            [
                item
                for item in items
                if self.__searchPredicate(self.__itemText(item))
            ]
            if self.__searchPredicate
            else items
        )

    def __itemText(self, item):
        """
        Renvoie le texte pour rechercher l'élément donné.

        Le texte comprend le sujet de l'élément et, éventuellement, la description
        et le texte des éléments parent et enfant, selon les paramètres du filtre.

        Args :
            item : L'article pour obtenir le texte.
        Return :
            Le texte pour rechercher l'élément donné.
        """
        text = self.__itemOwnText(item)
        if self.__includeSubItems:
            parent = item.parent()
            while parent:
                text += self.__itemOwnText(parent)
                parent = parent.parent()
        if self.treeMode():
            text += " ".join(
                [
                    self.__itemOwnText(child)
                    for child in item.children(recursive=True)
                    if child in self.observable()
                ]
            )
        return text

    def __itemOwnText(self, item):
        """
        Renvoie le texte de l'élément donné, à l'exclusion du texte de ses ancêtres et des descendants.

        Args :
            item : L'article pour obtenir le texte.
        Return :
            Le texte de l'élément donné, à l'exclusion du texte de ses ancêtres et des descendants.
        """
        text = item.subject()
        if self.__searchDescription:
            # text += item.description()
            text += item.getDescription()
        return text


class DeletedFilter(Filter):
    """
    Un filtre qui exclut les articles supprimés.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance supprimée.

        Args :
            args : Arguments de position transmis au constructeur de superclasse.
            *kwargs : Arguments de mots clés transmis au constructeur de superclasse.
        """
        super().__init__(*args, **kwargs)

        for eventType in [
            domainobject.Object.markDeletedEventType(),
            domainobject.Object.markNotDeletedEventType(),
        ]:
            patterns.Publisher().registerObserver(
                self.onObjectMarkedDeletedOrNot, eventType=eventType
            )

    def detach(self):
        """
        Détache le filtre de l'éditeur d'événements.
        """
        patterns.Publisher().removeObserver(self.onObjectMarkedDeletedOrNot)
        super().detach()

    def onObjectMarkedDeletedOrNot(self, event):  # pylint: disable=W0613
        """
        Gère l'événement lorsqu'un objet est marqué comme supprimé ou non supprimé.

        Args :
            event : Un objet d'événement contenant des informations sur l'objet qui a été marqué comme supprimé ou non supprimé.
        """
        self.reset()

    def filterItems(self, items):
        """
        Filtre les éléments donnés, ne renvoyant que ceux qui ne sont pas supprimés.

        Args :
            items : Un itérable d'articles à filtrer.
        Return :
            Une liste d'éléments qui ne sont pas supprimés.
        """

        return [item for item in items if not item.isDeleted()]
