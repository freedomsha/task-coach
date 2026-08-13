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
from . import observer

# import weakref  # Devient inutile, parent est devenu une référence forte

log = logging.getLogger(__name__)


class Composite(object):
    """
    Une classe représentant un objet Composite dans le modèle composite.

    Un objet Composite peut avoir un parent et des enfants, formant ainsi une hiérarchie d'objets composites.

    Attributs :
        __parent (weakref) : Référence faible au composite parent.
        __children (list) : Liste des composites enfants.

    Méthodes :
        __init__(children=None, parent=None) : Initialisez le composite avec une liste facultative d'enfants et de parents.
        __getstate__() : Obtenez l'état de l'objet composite.
        __setstate__(state) : Définir l'état à partir de state.
        __getcopystate__() : Obtenez l'état pour la copie.
        parent() : Obtenez le composite parent.
        ancestors() : Récupère la liste des ancêtres du composite.
        family() : Obtenez la famille du composite (ses ancêtres, lui-même et ses enfants).
        setParent(parent) : Définir le composite parent.
        children(recursive=False) : Récupère les enfants du composite.
        siblings(recursive=False) : Obtenez les frères et sœurs du composite.
        copy() : Créer une copie du composite.
        newChild() : Créez un nouveau composite enfant.
        addChild(child) : Ajouter un composite enfant à la liste d'enfants et définir le parent de cet enfant.
        removeChild(child) : Supprimer un composite enfant.
    """

    def __init__(self, children=None, parent=None):
        """
        Initialisez le composite avec une liste facultative d'enfants et de parents.

        Args :
            children (list | None) : (facultatif) Liste des composites enfants.
            parent (Composite | None) : (facultatif) Référence faible au Composite parent.
        """
        # log.debug(
        print(
            f"Composite : Initialisation de l'objet composite self = {id(self)} avec parent = {parent} et children = {children}."
        )
        print(
            "Composite : Initialisation de l'objet composite avec la méthode super."
        )
        super().__init__()
        log.debug("Composite : méthode super terminée.")
        print(
            f"Composite : L'objet composite self = {id(self)} a parent = {parent} et children = {children}."
        )
        # self.__parent = parent if parent is None else weakref.ref(parent)
        # # Ne réinitialiser __parent que si pas déjà défini par un setParent précédent
        if (
            not hasattr(self, "_Composite__parent")
            or self._Composite__parent  # Utiliser plutôt la méthode super() !?
            is None
        ):
            # self.__parent = parent if parent is None else weakref.ref(parent)
            self.__parent = parent
        self.__children = children or []
        # log.debug(
        print(
            f"Composite : self.__parent = {self.__parent} et self.__children = {self.__children}."
        )

        for child in self.__children:
            # log.debug(
            print(
                # f"Composite : Ajout de l'enfant {child.id()} à {self.id()}"
                f"Composite : Ajout de l'enfant {child} à self.id={id(self)}"
            )
            child.setParent(self)
            # self.addChild( # !!! Crée une boucle infinie si addChild() est redéfini dans une sous-classe
            #     child
            # )  # ✅ Utilise addChild pour ajouter chaque enfant
        # log.debug(
        print(
            "Après Composite.__init__ : de id=%s avec %s enfants."
            % (id(self), len(self.children())),
        )  # Ne jamais appeler self dans un print() pendant l’initialisation.
        # log.debug(
        print(
            "Après Composite.__init__ : parent=%s et children=%s."
            % (self.parent(), self.children())
        )
        log.debug("Composite : Initialisé !")

    def __getstate__(self):
        """
        Obtenez l'état de l'objet composite.

        Renvoie :
            (dict) : L'état du composite.
        """
        # return dict(children=self.__children[:], parent=self.parent())
        state = dict(children=self.__children[:], parent=self.parent())
        print(f"Composite.__getstate__ : retourne state : {state}!")
        return state

    def __setstate__(self, state):
        """
        Définir l'état à partir de state.

        self.__parent est une référence faible à state["parent"].
        self.__children est state["children"]

        Args :
            state (dict) : L'état du composite.
        """
        print(f"Composite.__setstate__ : state : {state}.")
        # self.__parent = (
        #     None if state["parent"] is None else weakref.ref(state["parent"])
        # )
        self.__parent = state[
            "parent"
        ]  # Référence forte (suppression des weakrefs)
        print(f"Composite.__setstate__ : self.__parent = {self.__parent}")
        self.__children = state["children"]
        # log.debug(
        print(f"Composite.__setstate__ : self.__children = {self.__children}")

    def __getcopystate__(self):
        """
        Obtenez l'état pour la copie.

        Renvoie :
            dict : L'état du composite pour la copie.
        """
        print("Composite.__getcopystate__ : enfants =", self.children())
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        # log.debug(
        print(
            f"Composite.__getcopystate__ : state après super et avant update {state}."
        )
        state.update(
            dict(
                children=[child.copy() for child in self.__children],
                parent=self.parent(),
            )
        )
        # log.debug(f"Composite.__getcopystate__ : retourne state {state}.")
        print(f"Composite.__getcopystate__ : retourne state {state}.")
        return state

    def parent(self):
        """
        Obtenez le parent du composite.

        Retourne le parent du nœud composite.

        Compatibilité :
        - remplace l'ancien usage weakref()
        - garantit une API stable pour tout le projet

        Renvoie :
            (Composite) : Le composite parent.
        """
        # return None if self.__parent is None else self.__parent()
        return self.__parent  # Référence forte (suppression des weakrefs)

    def hasParent(self):
        """
        Vérifiez si le composite a un parent.

        Returns :
            (bool) : True si le composite a un parent, False sinon.
        """
        return self.__parent is not None

    def ancestors(self):
        """
        Récupère la liste des ancêtres du composite.

        Renvoie :
            (list) : La liste des ancêtres.
        """
        parent = self.parent()
        return parent.ancestors() + [parent] if parent else []

    def family(self):
        """
        Obtenez la famille du composite
        (liste de ses ancêtres, lui-même et ses enfants).

        Returns :
            (list) : La famille du composite.
        """
        return self.ancestors() + [self] + self.children(recursive=True)

    def setParent(self, parent):
        """
        Définit le parent du composite.

        Migration propre :
        - stockage en référence forte
        - compatibilité API via getter

        Args :
            parent (Composite) : Le composite parent en référence faible.
        """
        # self.__parent = None if parent is None else weakref.ref(parent)
        self.__parent = (
            parent  # Référence forte volontaire (suppression des weakrefs)
        )
        # self.__parent.set(
        #     parent, event=event
        # )  # Non, ne fonctinne pas comme Object

    def children(self, recursive=False) -> list | None:
        """
        Récupère les enfants du composite.

        Args :
            recursive (bool) : (facultatif) Si True, récupère tous les descendants de manière récursive.

        Returns :
            (list) : La liste des enfants.
        """
        # Attention : cela doit satisfaire les mêmes conditions de sortie que allItemSorted().
        if recursive:
            result = self.__children[:]
            for child in self.__children:
                # log.debug(f"Composite.children : Ajout de l'enfant {child.id()} à {self.id()}")
                result.extend(child.children(recursive=True))
            return result
        else:
            return self.__children

    def siblings(self, recursive=False):
        """
        Obtenez les frères et sœurs du composite.

        Args :
            recursive (bool) : (facultatif) Si True, obtenez tous les descendants des frères et sœurs de manière récursive.

        Returns :
            (list) : La liste de frères et sœurs.
        """
        parent = self.parent()
        if parent:
            result = [child for child in parent.children() if child != self]
            if recursive:
                for child in result[:]:
                    result.extend(child.children(recursive=True))
            return result
        else:
            return []

    def copy(self, *args, **kwargs):
        """
        Créer une copie du composite.

        Returns :
            (Composite) : Le composite copié.
        """
        kwargs["parent"] = self.parent()
        kwargs["children"] = [
            child.copy() for child in self.children(recursive=True)
        ]
        return self.__class__(*args, **kwargs)

    def newChild(self, *args, **kwargs):
        """
        Créez un nouveau composite enfant.

        Returns :
            (Composite) : Le nouveau composite enfant.
        """
        # L'objet devient parent :
        kwargs["parent"] = self
        return self.__class__(*args, **kwargs)

    def addChild(self, child):
        """
        Ajouter un composite enfant à la liste d'enfants
        et définir le parent de cet enfant.

        Args :
            child (Composite) : Le composite enfant à ajouter.

        Attributes :
            __children : La liste des enfants.
        """
        self.__children.append(child)
        child.setParent(self)

    def removeChild(self, child):
        """
        Supprimer un composite enfant.

        Args :
            child (Composite) : Le composite enfant à supprimer.
        """
        self.__children.remove(child)
        # We don't reset the parent of the child, because that makes restoring
        # the parent-child relationship easier.


class ObservableComposite(Composite):
    """
    Une classe représentant un objet composite observable dans le modèle composite.

    Hérite de Composite et ajoute une fonctionnalité de modèle d'observateur sur la gestion des enfants.

    Méthodes :
        - __setstate__(state, event=None) : Définissez l'état de l'objet composite observable avec la notification d'événement.
        - addChild(child, event=None) : Ajoutez un composite enfant avec notification d'événement et créez un événement d'ajout d'enfant.
        - addChildEvent(event, *children) : Avertir les observateurs de l'ajout d'enfants.
        - addChildEventType(class_) : Obtenez le type d'événement pour l'ajout d'enfants.
        - removeChild(child, event=None) : Supprimer un composite enfant avec notification d'événement et créez un événement de suppression d'enfant.
        - removeChildEvent(event, *children) : Avertir les observateurs du retrait des enfants.
        - removeChildEventType(class_) : Obtenez le type d'événement pour supprimer les enfants.
        - modificationEventTypes(class_) : Obtenez la liste des types d'événements de modification.
    """

    @observer.eventSource
    def __setstate__(self, state, event=None):  # pylint: disable=W0221
        """
        Définissez l'état de l'objet composite observable avec la notification d'événement.

        Args :
            state (dict) : L'état du composite.
            event (Event | None) : (facultatif) L'événement à notifier.
        """
        # log.debug(
        print(
            f"ObservableComposite.__setstate__ : pour state {state} et event {event}"
        )
        # Anciens enfants :
        oldChildren = set(self.children())
        # Récupère l'état en mettant à jour l'état de l'objet composite :
        super().__setstate__(state)
        # Nouveaux enfants :
        newChildren = set(self.children())
        # Enfants supprimés :
        childrenRemoved = oldChildren - newChildren
        # pylint: disable=W0142
        # Création d'événement de suppression d'enfant(s) :
        if childrenRemoved:
            self.removeChildEvent(event, *childrenRemoved)
        # Enfants ajoutés :
        childrenAdded = newChildren - oldChildren
        # Création d'événement d'ajout d'enfants(s) :
        if childrenAdded:
            self.addChildEvent(event, *childrenAdded)
        print(
            f"ObservableComposite.__setstate__ : résultat : pour id={id(self)}, self={self}, state={state} et event={event}, childrenRemoved={childrenRemoved}, childrenAdded={childrenAdded}."
        )
        print("ObservableComposite.__setstate__ : terminé !")

    @observer.eventSource
    def addChild(self, child, event=None):  # pylint: disable=W0221
        """
        Ajoutez un composite enfant avec notification d'événement.

        Args :
            child (Composite) : Le composite enfant à ajouter.
            event (Event | None) : (facultatif) L'événement à notifier.
        """
        super().addChild(child)
        self.addChildEvent(event, child)

    def addChildEvent(self, event, *children):
        """
        Avertir les observateurs de l'ajout d'enfants.

        Args :
            event (Event) : L'événement à notifier.
            children (Composite) : Les enfants ajoutés.
        """
        event.addSource(self, *children, **dict(type=self.addChildEventType()))

    @classmethod
    def addChildEventType(class_):
        """
        Obtenez le type d'événement pour l'ajout d'enfants.

        Returns :
            (str) : Le type d'événement.
        """
        # return "composite(%s).child.add" % class_
        return f"composite({class_}).child.add"

    @observer.eventSource
    def removeChild(self, child, event=None):  # pylint: disable=W0221
        """
        Supprimer un composite enfant avec notification d'événement.

        Args :
            child (Composite) : Le composite enfant à supprimer.
            event (Event, facultatif) : L'événement à notifier.
        """
        super().removeChild(child)
        self.removeChildEvent(event, child)

    def removeChildEvent(self, event, *children):
        """
        Avertir les observateurs du retrait des enfants.

        Args :
            event (Event) : L'événement à notifier.
            children (Composite) : Les enfants supprimés.
        """
        event.addSource(
            self, *children, **dict(type=self.removeChildEventType())
        )

    @classmethod
    def removeChildEventType(class_):
        """
        Obtenez le type d'événement pour supprimer les enfants.

        Returns :
            (str) : Le type d'événement.
        """
        # return "composite(%s).child.remove" % class_
        return f"composite({class_}).child.remove"

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez la liste des types d'événements de modification.

        Returns :
            (list) : La liste des types d'événements de modification.
        """
        try:
            eventTypes = super().modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [
            class_.addChildEventType(),
            class_.removeChildEventType(),
        ]


class CompositeCollection(object):
    """
    Classe représentant une collection d'objets composites.

    Cette collection d'objets composites est une liste ou un ensemble
    qui a des méthodes pour gérer les composites et leurs relations parent-enfant.

    Méthodes :
        - __init__(initList=None, *args, **kwargs) : Initialisez la collection avec une liste facultative de composites initiaux.
        - append (composite) : Ajoutez un composite à la collection.
        - extend (composites) : Ajoutez plusieurs composites à la collection.
        - _compositesAndAllChildren (composites) : Obtenez tous les composites et leurs enfants de manière récursive.
        - _addCompositesToParent (composites, event) : Ajoutez des composites à leur parent.
        - remove (composite) : Supprimez un composite de la collection.
        - removeItems (composites) : Supprimez plusieurs composites de la collection.
        - _removeCompositesFromParent (composites, event) : Supprimer les composites de leur parent.
        - rootItems () : Obtenez les éléments racine de la collection.
        - allItemsSorted () : Obtenez tous les éléments triés par hiérarchie.
    """

    def __init__(self, initList=None, *args, **kwargs):
        # def __init__(self, *args, **kwargs):
        """
        Initialisez la collection avec une liste facultative de composites initiaux.

        Args :
            initList (list) : (facultatif) Liste initiale de composites.
        """
        super().__init__(*args, **kwargs)
        # # self.extend(initList or [])
        if initList:
            self.extend(initList)  # ✅ Ajoute les éléments passés en argument
        else:
            self.extend([])  # ✅ Ajoute une liste vide
        # if args:
        #     self.extend(args[0])

    def append(self, composite, event=None):
        """
        Ajoutez un composite à la collection.

        Args :
            composite (Composite) : Le composite à ajouter.
            event (Event) : (facultatif) L'événement à notifier.
        """
        print(
            f"CompositeCollection.append : ajoute {composite} à la collection {self} avec event = {event}."
        )
        return self.extend([composite], event=event)

    @observer.eventSource
    def extend(self, composites, event=None):
        """
        Ajoutez plusieurs composites à la collection avec notification d'événement.

        Args :
            composites (list) : La liste des composites à ajouter.
            event (Event | None) : (facultatif) L'événement à notifier.
        """
        log.debug(
            f"CompositeCollection.extend : ajoute les composites suivants à la collection {self} avec event = {event} : {composites}."
        )
        if not composites:
            return
        log.debug(
            "CompositeCollection.extend : obtient les composites et tous leurs enfants."
        )
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        log.debug(
            "CompositeCollection.extend : ajoute les composites et tous leurs enfants à la collection."
        )
        super().extend(compositesAndAllChildren, event=event)
        # self.extend(compositesAndAllChildren, event=event)
        log.debug(
            "CompositeCollection.extend : ajoute les composites à leur parent."
        )
        self._addCompositesToParent(composites, event)
        log.debug("CompositeCollection.extend : terminé !")

    def _compositesAndAllChildren(self, composites):
        """
        Obtenez tous les composites et leurs enfants de manière récursive.

        Args :
            composites (list) : La liste des composites.

        Returns :
            list : La liste des composites et de leurs enfants.
        """
        # compositesAndAllChildren = set(composites)
        # for composite in composites:
        #     compositesAndAllChildren |= set(composite.children(recursive=True))
        compositesAndAllChildren = set()
        for composite in composites:
            log.debug(
                f"CompositeCollection._compositesAndAllChildren : traite le composite {composite}."
            )
            compositesAndAllChildren.add(composite)
            log.debug(
                f"CompositeCollection._compositesAndAllChildren : ajoute le composite {composite}."
            )
            compositesAndAllChildren.update(composite.children(recursive=True))
        log.debug(
            f"CompositeCollection._compositesAndAllChildren : pour les composites suivants {composites}, les composites et tous leurs enfants sont : {compositesAndAllChildren}."
        )
        return compositesAndAllChildren

    def _addCompositesToParent(self, composites, event):
        """
        Ajoutez des composites à leur parent.

        Args :
            composites (list) : La liste des composites.
            event (Event) : L'événement à notifier.
        """
        for composite in composites:
            parent = composite.parent()
            if (
                parent
                and parent in self
                and composite not in parent.children()
            ):
                parent.addChild(composite, event=event)

    def remove(self, composite, event=None):
        """
        Supprimer un composite de la collection.

        Args :
            composite (Composite) : Le composite à supprimer.
            event (Event | None) : (facultatif) L'événement à notifier.
        """
        return (
            self.removeItems([composite], event=event)
            if composite in self
            else event
        )

    @observer.eventSource
    def removeItems(self, composites, event=None):
        """
        Supprimez plusieurs éléments composites de la collection avec notification d'événement.

        Args :
            composites (list) : La liste des composites à supprimer.
            event (Event | None) : (facultatif) L'événement à notifier.
        """
        if not composites:
            return
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        super().removeItems(compositesAndAllChildren, event=event)
        self._removeCompositesFromParent(composites, event)

    def _removeCompositesFromParent(self, composites, event):
        """
        Supprimer les composites de leur parent.

        Args :
            composites (list) : La liste des composites.
            event (Event) : L'événement à notifier.
        """
        for composite in composites:
            parent = composite.parent()
            if parent:
                parent.removeChild(composite, event=event)

    def rootItems(self):
        """
        Récupère les éléments racine de la collection.

        Returns :
            (list) : La liste des éléments racine.
        """
        return [
            composite
            for composite in self
            if composite.parent() is None  # si il n'a pas de parent
            or composite.parent()
            not in self  # ou si son parent n'est pas dans cette collection
            # in self or not in self ?,
        ]
        # Conséquence :
        #
        # Une note dont le parent est une tâche (dans taskList) sera considérée comme un root item dans noteContainer, car note.parent() not in noteContainer est True.
        # Résultat : La note est écrite au niveau racine du XML au lieu d'être nestée sous sa tâche.

    def allItemsSorted(self):
        """
        Obtenez tous les éléments triés par hiérarchie.

        Returns :
            (list) : La liste de tous les éléments triés par hiérarchie.
        """
        # Retourne une liste des items et de leurs enfants,
        # ainsi si B est un enfant, direct ou pas, de A,
        # quand A viendra en premier dans la liste.
        result = []
        for item in self.rootItems():
            result.append(item)
            result.extend(item.children(recursive=True))
        return result


class CompositeSet(CompositeCollection, observer.ObservableSet):
    """Un ensemble d'objets composites observables.

    Hérite de CompositeCollection et de ObservableSet
    pour gérer les composites et leurs relations parent/enfant
    et avertir les observateurs quand un élément est ajouté ou supprimé.
    """

    pass


class CompositeList(CompositeCollection, observer.ObservableList):
    """Une liste d'objets composites observables.

    Hérite de CompositeCollection et de ObservableList
    pour gérer les composites et leurs relations parent/enfant
    et avertir les observateurs quand un élément est ajouté ou supprimé de la liste.
    """

    pass
