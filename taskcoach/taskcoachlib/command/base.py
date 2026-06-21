# -*- coding: utf-8 -*-

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

# from builtins import zip
# from builtins import object
from taskcoachlib import patterns
from taskcoachlib.domain import date
from taskcoachlib.i18n import _
from taskcoachlib.command.clipboard import Clipboard

log = logging.getLogger(__name__)  # Logger pour ce fichier


class BaseCommand(patterns.Command):
    """Classe de base pour toutes les commandes dans Task Coach.

    Cette classe fournit une structure de base pour les commandes qui peuvent être exécutées,
    annulées et répétées. Elle gère également les dates de modification des objets concernés.

    Attributes :
        list: La liste à laquelle les éléments appartiennent.
        items: Les éléments concernés par la commande.
        __oldModificationDatetimes: Les dates de modification des éléments modifiés.
        __now: La date actuelle.
        *args: Arguments supplémentaires.
        **kwargs: Arguments de mots-clés supplémentaires.
        singular_name: Le nom de la commande au singulier.
        plural_name: Le nom de la commande au pluriel.
    """

    def __init__(
        self, list=None, items=None, *args, **kwargs
    ):  # pylint: disable=W0622
        """Initialise une commande de base.

        Args:
            list: La liste à laquelle les éléments appartiennent.
            items: Les éléments concernés par la commande.
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        super().__init__(*args, **kwargs)
        self.list = list
        self.items = [item for item in items] if items else []
        self.__oldModificationDatetimes = []
        self.__now = date.Now()
        self.save_modification_datetimes()

    def save_modification_datetimes(self):
        """Sauvegarder les dates de modification des éléments modifiés."""
        self.__oldModificationDatetimes = [
            (item, item.modificationDateTime())
            for item in self.modified_items()
            if item
        ]
        self.__now = date.Now()

    def __str__(self):
        """Retourne une représentation sous forme de chaîne de la commande."""
        return self.name()

    singular_name = "Do something with %s"  # Override in subclass
    plural_name = "Do something"  # Override in subclass

    def name(self):
        """Retourne le nom de la commande.

        Returns :
            (str) : Le nom de la commande, soit au singulier, soit au pluriel selon le nombre d'éléments.
        """
        return (
            self.singular_name % self.name_subject(self.items[0])
            if len(self.items) == 1
            else self.plural_name
        )

    def name_subject(self, item):
        """Retourne le sujet d'un élément pour le nom de la commande.

        Args:
            item: L'élément dont on veut le sujet.

        Returns:
            str: Le sujet de l'élément, tronqué si nécessaire.
        """
        subject = item.subject()
        return subject if len(subject) < 60 else subject[:57] + "..."

    def items_are_new(self):
        """Détermine si les éléments sont nouveaux.

        Returns :
            (bool) : True si les éléments sont nouveaux, False sinon.
        """
        return False

    def getItems(self):
        """Retourne les éléments sur lesquels la commande opère.

        Returns :
            (list) : La liste des éléments concernés par la commande.
        """
        return self.items

    def modified_items(self):
        """Retourne les éléments qui sont modifiés par cette commande.

        Returns :
            (list) : La liste des éléments modifiés.
        """
        return self.items

    def canDo(self):
        """Vérifie si la commande peut être exécutée.

        Returns :
            (bool) : True si la commande peut être exécutée, False sinon.
        """
        return bool(self.items)

    def do(self):
        """Exécute la commande si elle peut être exécutée."""
        if self.canDo():
            super().do()
            self.do_command()

    def undo(self):
        """Annule la commande."""
        super().undo()
        self.undo_command()

    def redo(self):
        """Répète la commande."""
        super().redo()
        self.redo_command()

    def __tryInvokeMethodOnSuper(self, method_name, *args, **kwargs):
        """Tente d'appeler une méthode sur la classe parente.

        Args:
            method_name: Le nom de la méthode à appeler.
            *args: Arguments à passer à la méthode.
            **kwargs: Arguments de mots-clés à passer à la méthode.

        Returns:
            Le résultat de l'appel à la méthode, ou None si la méthode n'existe pas.
        """
        try:
            method = getattr(super(), method_name)
        except AttributeError as e:
            log.error(f"AttributeError: {e}", exc_info=True)
            return None  # no 'method' in any super class
        return method(*args, **kwargs)

    def do_command(self):
        """Exécute la commande spécifique."""
        self.__tryInvokeMethodOnSuper("do_command")
        for item in self.modified_items():
            item.setModificationDateTime(self.__now)

    def undo_command(self):
        """Annule la commande spécifique."""
        self.__tryInvokeMethodOnSuper("undo_command")
        for item, old_modification_datetime in self.__oldModificationDatetimes:
            item.setModificationDateTime(old_modification_datetime)

    def redo_command(self):
        """Répète la commande spécifique."""
        self.__tryInvokeMethodOnSuper("redo_command")
        for item in self.modified_items():
            item.setModificationDateTime(self.__now)


class SaveStateMixin(object):
    """Mixin class for commands that need to keep the states of objects.
    Objects should provide __getstate__ and __setstate__ methods.

    Attributes :
        objectsToBeSaved: La liste des objets dont les états doivent être sauvegardés.
        oldStates: La liste des états des objets avant la modification.
        newStates: La liste des états des objets après la modification.
    """

    # pylint: disable=W0201

    def saveStates(self, objects):
        """Sauvegarde les états des objets.

        Args:
            objects: La liste des objets à sauvegarder.
        """
        self.objectsToBeSaved = objects
        self.oldStates = self.__getStates()

    @patterns.eventSource
    def undoStates(self, event=None):
        """Store current states and restore old states.

        Args:
            event: L'événement de notification.
        """
        self.newStates = self.__getStates()
        self.__setStates(self.oldStates, event=event)

    @patterns.eventSource
    def redoStates(self, event=None):
        """Restore previously stored new states.

        Args:
            event: L'événement de notification.
        """
        self.__setStates(self.newStates, event=event)

    def __getStates(self):
        """Récupère les états des objets sauvegardés.

        Returns:
            list: La liste des états des objets.
        """
        return [
            objectToBeSaved.__getstate__()
            for objectToBeSaved in self.objectsToBeSaved
        ]

    @patterns.eventSource
    def __setStates(self, states, event=None):
        """Restaure les états des objets.

        Args:
            states: La liste des états à restaurer.
            event: L'événement de notification.
        """
        for objectToBeSaved, state in zip(self.objectsToBeSaved, states):
            objectToBeSaved.__setstate__(state, event=event)


class CompositeMixin(object):
    """
    Mixin class for commands that deal with composites.

    Récupère les états des objets sauvegardés.

    Attributes :
        items: La liste des éléments concernés par la commande.
        list: La liste à laquelle les éléments appartiennent.
    """

    def getAncestors(self, composites):  # Method may be 'static'
        """Retourne les ancêtres des composites.

        Args:
            composites: La liste des composites.

        Returns:
            list: La liste des ancêtres.
        """
        ancestors = []
        for composite in composites:
            ancestors.extend(composite.ancestors())
        return ancestors

    def getAllChildren(self, composites):  # Method may be 'static'
        """Retourne tous les enfants des composites.

        Args:
            composites: La liste des composites.

        Returns:
            list: La liste de tous les enfants.
        """
        all_children = []
        for composite in composites:
            all_children.extend(composite.children(recursive=True))
        return all_children

    def getAllParents(self, composites):  # Method may be 'static'
        """Retourne tous les parents des composites.

        Args:
            composites: La liste des composites.

        Returns:
            list: La liste de tous les parents.
        """
        return [
            composite.parent()
            for composite in composites
            if composite.parent() is not None
        ]


class NewItemCommand(BaseCommand):
    """Commande pour créer de nouveaux éléments.

    Attributes :
        list: La liste à laquelle les éléments appartiennent.
        items: Les éléments à créer.
        singular_name: Le nom de la commande au singulier.
        plural_name: Le nom de la commande au pluriel.
    """

    def name(self):
        """Retourne le nom de la commande.

        Returns:
            str: Le nom de la commande au singulier.
        """
        # Override to always return the singular name without a subject. The
        # subject would be something like "New task", so not very interesting.
        return (
            self.singular_name
        )  # TODO : vérifier s'il faut aussi utiliser la commande pluriel !

    def items_are_new(self):
        """Détermine si les éléments sont nouveaux.

        Returns:
            bool: True car les éléments sont nouveaux.
        """
        return True

    def modified_items(self):
        """Retourne les éléments modifiés par cette commande.

        Returns:
            list: La liste vide car les nouveaux éléments ne modifient pas d'autres éléments.
        """
        return []

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande de création d'éléments.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        self.list.extend(
            self.items
        )  # Don't use the event to force this change to be notified first
        event.addSource(self, type="newitem", *self.items)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande de création d'éléments.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        self.list.removeItems(self.items, event=event)

    @patterns.eventSource
    def redo_command(self, event=None):
        """Répète la commande de création d'éléments.

        Args:
            event: L'événement de notification.
        """
        super().redo_command()
        self.list.extend(
            self.items
        )  # Don't use the event to force this change to be notified first
        event.addSource(self, type="newitem", *self.items)


class NewSubItemCommand(NewItemCommand):
    """Commande pour créer de nouveaux sous-éléments."""

    def name_subject(self, subitem):
        """Retourne le sujet du parent du sous-élément.

        Args:
            subitem: Le sous-élément.

        Returns:
            (str) : Le sujet du parent du sous-élément.
        """
        # Override to use the subject of the parent of the new subitem instead
        # of the subject of the new subitem itself, which wouldn't be very
        # interesting because it's something like 'New subitem'.
        return subitem.parent().subject()

    def modified_items(self):
        """Retourne les éléments modifiés par cette commande.

        Returns :
            (list) : La liste des parents des sous-éléments créés.
        """
        return [item.parent() for item in self.items]


class CopyCommand(BaseCommand):
    """Commande pour copier des éléments."""

    plural_name = _("Copy")
    singular_name = _('Copy "%s"')

    def do_command(self):
        """Exécuter la commande de copie.

        Sauvegarder les copies des éléments dans le presse-papiers.
        """
        self.__copies = [
            item.copy() for item in self.items
        ]  # pylint: disable=W0201
        # instance attribute __copies defined outside __init__
        Clipboard().put(self.__copies, self.list)

    def undo_command(self):
        """Annule la commande de copie."""
        Clipboard().clear()

    def redo_command(self):
        """Répète la commande de copie."""
        Clipboard().put(self.__copies, self.list)


class DeleteCommand(BaseCommand, SaveStateMixin):
    """Commande pour supprimer des éléments."""

    plural_name = _("Delete")
    singular_name = _('Delete "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande de suppression.

        Args :
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__shadow = kwargs.pop("shadow", False)
        super().__init__(*args, **kwargs)

    def modified_items(self):
        """Retourne les éléments modifiés par cette commande.

        Returns:
            list: La liste des parents des éléments supprimés.
        """
        return [item.parent() for item in self.items if item.parent()]

    def do_command(self):
        """Exécute la commande de suppression."""
        super().do_command()
        if self.__shadow:
            self.saveStates(self.items)

            for item in self.items:
                item.markDeleted()
        else:
            self.list.removeItems(self.items)

    def undo_command(self):
        """Annule la commande de suppression."""
        super().undo_command()
        if self.__shadow:
            self.undoStates()
        else:
            self.list.extend(self.items)

    def redo_command(self):
        """Répète la commande de suppression."""
        super().redo_command()
        if self.__shadow:
            self.redoStates()
        else:
            self.list.removeItems(self.items)


class CutCommandMixin(object):
    """Mixin class for commands that cut items to the clipboard."""

    plural_name = _("Cut")
    singular_name = _('Cut "%s"')

    def __putItemsOnClipboard(self):
        """Met les éléments sur le presse-papiers."""
        cb = Clipboard()
        self.__previousClipboardContents = cb.get()  # pylint: disable=W0201
        cb.put(
            self.itemsToCut(), self.sourceOfItemsToCut()
        )  # Unresolved attribute car mixin !

    def __removeItemsFromClipboard(self):
        """Retire les éléments du presse-papiers."""
        cb = Clipboard()
        cb.put(*self.__previousClipboardContents)

    def do_command(self):
        """Met les éléments sur le presse-papiers et exécute la commande."""
        self.__putItemsOnClipboard()
        super().do_command()

    def undo_command(self):
        """Restaure le contenu précédent du presse-papiers et annule la commande."""
        self.__removeItemsFromClipboard()
        super().undo_command()

    def redo_command(self):
        """Met les éléments de nouveau sur le presse-papiers et répète la commande."""
        self.__putItemsOnClipboard()
        super().redo_command()


class CutCommand(CutCommandMixin, DeleteCommand):
    """Commande pour couper des éléments."""

    def itemsToCut(self):
        """Retourne les éléments à couper.

        Returns:
            list: La liste des éléments à couper.
        """
        return self.items

    def sourceOfItemsToCut(self):
        """Retourne la source des éléments à couper.

        Returns:
            list: La liste source des éléments à couper.
        """
        return self.list


class PasteCommand(BaseCommand, SaveStateMixin):
    """Commande pour coller des éléments."""

    plural_name = _("Paste")
    singular_name = _('Paste "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande de collage.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        super().__init__(*args, **kwargs)
        self.__itemsToPaste, self.__sourceOfItemsToPaste = (
            self.getItemsToPaste()
        )
        self.saveStates(self.getItemsToSave())

    def getItemsToSave(self):
        """Retourne les éléments à sauvegarder pour l'annulation/répétition.

        Returns:
            list: La liste des éléments à sauvegarder.
        """
        return self.__itemsToPaste

    def canDo(self):
        """Vérifie si la commande peut être exécutée.

        Returns:
            bool: True si des éléments peuvent être collés, False sinon.
        """
        return bool(self.__itemsToPaste)

    def do_command(self):
        """Exécute la commande de collage."""
        self.setParentOfPastedItems()
        self.__sourceOfItemsToPaste.extend(self.__itemsToPaste)

    def undo_command(self):
        """Annule la commande de collage."""
        self.__sourceOfItemsToPaste.removeItems(self.__itemsToPaste)
        self.undoStates()

    def redo_command(self):
        """Répète la commande de collage."""
        self.redoStates()
        self.__sourceOfItemsToPaste.extend(self.__itemsToPaste)

    def setParentOfPastedItems(self, newParent=None):
        """Définit le parent pour tous les éléments en cours de collage.

        Détermine si les éléments sont nouveaux.

        Args:
            newParent: L'objet de domaine à définir comme parent.
        """
        for item in self.__itemsToPaste:
            item.setParent(newParent)

    @staticmethod
    def getItemsToPaste():
        """Récupère les éléments depuis le presse-papiers et crée des copies pour le collage.

        Returns:
            tuple: Une liste d'éléments copiés et la collection source.
        """
        items, source = Clipboard().get()
        return [item.copy() for item in items], source


class PasteAsSubItemCommand(PasteCommand, CompositeMixin):
    """Commande pour coller des éléments en tant que sous-éléments."""

    plural_name = _("Paste as subitem")
    singular_name = _('Paste as subitem of "%s"')

    def setParentOfPastedItems(self):  # pylint: disable=W0221
        """Définit le parent pour les éléments collés.

        Args:
            newParent: Le parent à définir.
        """
        newParent = self.items[0]
        super().setParentOfPastedItems(newParent)

    def getItemsToSave(self):
        """Retourne les éléments à sauvegarder pour l'annulation/répétition.

        Returns:
            list: La liste des éléments à sauvegarder.
        """
        return self.getAncestors([self.items[0]]) + super().getItemsToSave()


class DragAndDropCommand(BaseCommand, SaveStateMixin, CompositeMixin):
    """Commande pour le glisser-déposer."""

    plural_name = _("Drag and drop")
    singular_name = _('Drag and drop "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande de glisser-déposer.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        dropTargets = kwargs.pop("drop")
        self._itemToDropOn = dropTargets[0] if dropTargets else None
        super().__init__(*args, **kwargs)
        self.saveStates(self.getItemsToSave())

    def getItemsToSave(self):
        """Retourne les éléments à sauvegarder pour l'annulation/répétition.

        Returns:
            list: La liste des éléments à sauvegarder.
        """
        toSave = self.items[:]
        if self._itemToDropOn is not None:
            toSave.insert(0, self._itemToDropOn)
        return toSave

    def modified_items(self):
        """Retourne les éléments modifiés par cette commande.

        Returns:
            list: La liste des éléments modifiés.
        """
        return (
            [item.parent() for item in self.items if item.parent()]
            + [self._itemToDropOn]
            if self._itemToDropOn
            else []
        )

    def canDo(self):
        """Vérifie si la commande peut être exécutée.

        Returns:
            bool: True si la commande peut être exécutée, False sinon.
        """
        return self._itemToDropOn not in (
            self.items
            + self.getAllChildren(self.items)
            + self.getAllParents(self.items)
        )

    def do_command(self):
        """Exécute la commande de glisser-déposer."""
        super().do_command()
        self.list.removeItems(self.items)
        for item in self.items:
            item.setParent(self._itemToDropOn)
        self.list.extend(self.items)

    def undo_command(self):
        """Annule la commande de glisser-déposer."""
        super().undo_command()
        self.list.removeItems(self.items)
        self.undoStates()
        self.list.extend(self.items)

    def redo_command(self):
        """Répète la commande de glisser-déposer."""
        super().redo_command()
        self.list.removeItems(self.items)
        self.redoStates()
        self.list.extend(self.items)


class OrderingDragAndDropCommand(DragAndDropCommand):
    """Commande pour le glisser-déposer avec réorganisation."""

    def __init__(self, *args, **kwargs):
        """Initialise une commande de glisser-déposer avec réorganisation.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.column = kwargs.pop("column", None)
        self.isTreeMode = kwargs.pop("isTree", True)
        self.part = kwargs.pop("part", 0)
        super().__init__(*args, **kwargs)

    def isOrdering(self):
        """Détermine si l'opération concerne l'ordre.

        Returns:
            bool: True si l'opération concerne l'ordre, False sinon.
        """
        return self.column is not None and self.column.name() == "ordering"

    def getSiblings(self):
        """Retourne les frères et sœurs de l'élément déplacé.

        Returns:
            list: La liste des frères et sœurs.
        """
        siblings = []
        for item in self.list:
            if (
                item.parent() == self._itemToDropOn.parent()
                and item not in self.items
            ):
                siblings.append(item)
        return siblings

    def getOrderingSiblings(self):
        """Retourne les frères et sœurs concernés par l'ordre.

        Returns:
            list: La liste des frères et sœurs concernés par l'ordre.
        """
        if self.isTreeMode:
            return self.getSiblings()
        # Everything, almost
        return [item for item in self.list if item not in self.items]

    def getItemsToSave(self):
        """Retourne les éléments à sauvegarder pour l'annulation/répétition.

        Returns:
            list: La liste des éléments à sauvegarder.
        """
        items = super().getItemsToSave()
        if self.isOrdering():
            items.extend(self.getOrderingSiblings())
        return items

    def canDo(self):
        """Vérifie si la commande peut être exécutée.

        Returns:
            bool: True si la commande peut être exécutée, False sinon.
        """
        if self.isOrdering():
            return True  # Already checked when drag and droppin
        return super().canDo()

    def do_command(self):
        """Exécute la commande de glisser-déposer avec réorganisation."""
        if self.isOrdering():
            siblings = self.getOrderingSiblings()

            orderings = [item.ordering() for item in self.items]
            minOrdering = min(orderings)
            maxOrdering = max(orderings)

            insertIndex = (
                siblings.index(self._itemToDropOn) + (self.part + 1) // 2
            )

            # Simple special cases
            if insertIndex == 0:
                minOrderingOfSiblings = min(
                    [item.ordering() for item in siblings]
                )
                for item in self.items:
                    item.setOrdering(
                        item.ordering()
                        - maxOrdering
                        + minOrderingOfSiblings
                        - 1
                    )
            elif insertIndex == len(siblings):
                maxOrderingOfSiblings = max(
                    [item.ordering() for item in siblings]
                )
                for item in self.items:
                    item.setOrdering(
                        item.ordering()
                        - minOrdering
                        + maxOrderingOfSiblings
                        + 1
                    )
            else:
                maxOrderingOfPreviousSiblings = max(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx < insertIndex
                    ]
                )
                minOrderingOfPreviousSiblings = min(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx < insertIndex
                    ]
                )
                maxOrderingOfNextSiblings = max(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx >= insertIndex
                    ]
                )
                minOrderingOfNextSiblings = min(
                    [
                        item.ordering()
                        for idx, item in enumerate(siblings)
                        if idx >= insertIndex
                    ]
                )
                if insertIndex < len(siblings) // 2:
                    for item in self.items:
                        item.setOrdering(
                            item.ordering()
                            - maxOrdering
                            - 1
                            + minOrderingOfNextSiblings
                        )
                    for item in siblings[:insertIndex]:
                        item.setOrdering(
                            item.ordering()
                            - maxOrderingOfPreviousSiblings
                            - 1
                            + minOrdering
                            - maxOrdering
                            - 1
                            + minOrderingOfNextSiblings
                        )
                else:
                    for item in self.items:
                        item.setOrdering(
                            item.ordering()
                            - minOrdering
                            + 1
                            + maxOrderingOfPreviousSiblings
                        )
                    for item in siblings[insertIndex:]:
                        item.setOrdering(
                            item.ordering()
                            - minOrderingOfNextSiblings
                            + 1
                            + maxOrdering
                            - minOrdering
                            + 1
                            + maxOrderingOfPreviousSiblings
                        )
        else:
            super().do_command()


class EditSubjectCommand(BaseCommand):
    """Commande pour modifier le sujet d'éléments."""

    plural_name = _("Edit subjects")
    singular_name = _('Edit subject "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande d'édition de sujet.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__newSubject = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__old_subjects = [(item, item.subject()) for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande d'édition de sujet.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        for item in self.items:
            item.setSubject(self.__newSubject, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande d'édition de sujet.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        for item, old_subject in self.__old_subjects:
            item.setSubject(old_subject, event=event)

    def redo_command(self):
        """Répète la commande d'édition de sujet."""
        self.do_command()


class EditDescriptionCommand(BaseCommand):
    """Commande pour modifier la description d'éléments."""

    plural_name = _("Edit descriptions")
    singular_name = _('Edit description "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande d'édition de description.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__new_description = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__old_descriptions = [item.description() for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande d'édition de description.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        for item in self.items:
            item.setDescription(self.__new_description, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande d'édition de description.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        for item, old_description in zip(self.items, self.__old_descriptions):
            item.setDescription(old_description, event=event)

    def redo_command(self):
        """Répète la commande d'édition de description."""
        self.do_command()


class EditIconCommand(BaseCommand):
    """Commande pour modifier l'icône d'éléments."""

    plural_name = _("Change icons")
    singular_name = _('Change icon "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande d'édition d'icône.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__newIcon = icon = kwargs.pop("newValue")
        self.__newSelectedIcon = (
            icon[: -len("_icon")] + "_open_icon"
            if (icon.startswith("folder") and icon.count("_") == 2)
            else icon
        )
        super().__init__(*args, **kwargs)
        self.__oldIcons = [
            (item.icon(), item.selectedIcon()) for item in self.items
        ]

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande d'édition d'icône.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        for item in self.items:
            item.setIcon(self.__newIcon, event=event)
            item.setSelectedIcon(self.__newSelectedIcon, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande d'édition d'icône.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        for item, (oldIcon, oldSelectedIcon) in zip(
            self.items, self.__oldIcons
        ):
            item.setIcon(oldIcon, event=event)
            item.setSelectedIcon(oldSelectedIcon, event=event)

    def redo_command(self):
        """Répète la commande d'édition d'icône."""
        self.do_command()


class EditFontCommand(BaseCommand):
    """Commande pour modifier la police d'éléments."""

    plural_name = _("Change fonts")
    singular_name = _('Change font "%s"')

    def __init__(self, *args, **kwargs):
        """Initialise une commande d'édition de police.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__newFont = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__oldFonts = [item.font() for item in self.items]

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande d'édition de police.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        for item in self.items:
            item.setFont(self.__newFont, event=event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande d'édition de police.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        for item, oldFont in zip(self.items, self.__oldFonts):
            item.setFont(oldFont, event=event)

    def redo_command(self):
        """Répète la commande d'édition de police."""
        self.do_command()


class EditColorCommand(BaseCommand):
    """Commande pour modifier la couleur d'éléments."""

    def __init__(self, *args, **kwargs):
        """Initialise une commande d'édition de couleur.

        Args:
            *args: Arguments supplémentaires.
            **kwargs: Arguments de mots-clés supplémentaires.
        """
        self.__newColor = kwargs.pop("newValue")
        super().__init__(*args, **kwargs)
        self.__oldColors = [self.getItemColor(item) for item in self.items]

    @staticmethod
    def getItemColor(item):
        """Retourne la couleur d'un élément.

        Args:
            item: L'élément dont on veut la couleur.

        Returns:
            La couleur de l'élément.
        """
        raise NotImplementedError

    @staticmethod
    def setItemColor(item, color, event):
        """Définit la couleur d'un élément.

        Args:
            item: L'élément dont on veut définir la couleur.
            color: La couleur à définir.
            event: L'événement de notification.
        """
        raise NotImplementedError

    @patterns.eventSource
    def do_command(self, event=None):
        """Exécute la commande d'édition de couleur.

        Args:
            event: L'événement de notification.
        """
        super().do_command()
        for item in self.items:
            self.setItemColor(item, self.__newColor, event)

    @patterns.eventSource
    def undo_command(self, event=None):
        """Annule la commande d'édition de couleur.

        Args:
            event: L'événement de notification.
        """
        super().undo_command()
        for item, oldColor in zip(self.items, self.__oldColors):
            self.setItemColor(item, oldColor, event)

    def redo_command(self):
        """Répète la commande d'édition de couleur."""
        self.do_command()


class EditForegroundColorCommand(EditColorCommand):
    """Commande pour modifier la couleur de premier plan d'éléments."""

    plural_name = _("Change foreground colors")
    singular_name = _('Change foreground color "%s"')

    @staticmethod
    def getItemColor(item):
        """Retourne la couleur de premier plan d'un élément.

        Args:
            item: L'élément dont on veut la couleur de premier plan.

        Returns:
            La couleur de premier plan de l'élément.
        """
        return item.foregroundColor()

    @staticmethod
    def setItemColor(item, color, event):
        """Définit la couleur de premier plan d'un élément.

        Args:
            item: L'élément dont on veut définir la couleur de premier plan.
            color: La couleur à définir.
            event: L'événement de notification.
        """
        item.setForegroundColor(color, event=event)


class EditBackgroundColorCommand(EditColorCommand):
    """Commande pour modifier la couleur d'arrière-plan d'éléments."""

    plural_name = _("Change background colors")
    singular_name = _('Change background color "%s"')

    @staticmethod
    def getItemColor(item):
        """Retourne la couleur d'arrière-plan d'un élément.

        Args:
            item: L'élément dont on veut la couleur d'arrière-plan.

        Returns:
            La couleur d'arrière-plan de l'élément.
        """
        return item.backgroundColor()

    @staticmethod
    def setItemColor(item, color, event):
        """Définit la couleur d'arrière-plan d'un élément.

        Args:
            item: L'élément dont on veut définir la couleur d'arrière-plan.
            color: La couleur à définir.
            event: L'événement de notification.
        """
        item.setBackgroundColor(color, event=event)
