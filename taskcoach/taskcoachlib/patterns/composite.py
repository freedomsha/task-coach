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

from . import observer
import weakref


class Composite(object):
    """
    A class representing a composite object in the composite pattern.

    Attributes:
        __parent (weakref): Weak reference to the parent composite.
        __children (list): List of child composites.
    """

    def __init__(self, children=None, parent=None):
        """
        Initialize the composite with an optional list of children and parent.

        Args:
            children (list, optional): List of child composites.
            parent (Composite, optional): Parent composite.
        """
        super().__init__()
        self.__parent = parent if parent is None else weakref.ref(parent)
        self.__children = children or []
        for child in self.__children:
            child.setParent(self)

    def __getstate__(self):
        """
        Get the state for pickling.

        Returns:
            dict: The state of the composite.
        """
        return dict(children=self.__children[:], parent=self.parent())

    def __setstate__(self, state):
        """
        Set the state from unpickling.

        Args:
            state (dict): The state of the composite.
        """
        self.__parent = (
            None if state["parent"] is None else weakref.ref(state["parent"])
        )
        self.__children = state["children"]

    def __getcopystate__(self):
        """
        Get the state for copying.

        Returns:
            dict: The state of the composite for copying.
        """
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        state.update(
            dict(
                children=[child.copy() for child in self.__children],
                parent=self.parent(),
            )
        )
        return state

    def parent(self):
        """
        Get the parent composite.

        Returns:
            Composite: The parent composite.
        """
        return None if self.__parent is None else self.__parent()

    def ancestors(self):
        """
        Get the list of ancestors of the composite.

        Returns:
            list: The list of ancestors.
        """
        parent = self.parent()
        return parent.ancestors() + [parent] if parent else []

    def family(self):
        """
        Get the family of the composite (ancestors, self, and children).

        Returns:
            list: The family of the composite.
        """
        return self.ancestors() + [self] + self.children(recursive=True)

    def setParent(self, parent):
        """
        Set the parent composite.

        Args:
            parent (Composite): The parent composite.
        """
        self.__parent = None if parent is None else weakref.ref(parent)

    def children(self, recursive=False):
        """
        Get the children of the composite.

        Args:
            recursive (bool, optional): If True, get all descendants recursively.

        Returns:
            list: The list of children.
        """
        # Warning: this must satisfy the same condition as
        # allItemsSorted() below.

        if recursive:
            result = self.__children[:]
            for child in self.__children:
                result.extend(child.children(recursive=True))
            return result
        else:
            return self.__children

    def siblings(self, recursive=False):
        """
        Get the siblings of the composite.

        Args:
            recursive (bool, optional): If True, get all descendants of siblings recursively.

        Returns:
            list: The list of siblings.
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
        Create a copy of the composite.

        Returns:
            Composite: The copied composite.
        """
        kwargs["parent"] = self.parent()
        kwargs["children"] = [child.copy() for child in self.children()]
        return self.__class__(*args, **kwargs)

    def newChild(self, *args, **kwargs):
        """
        Create a new child composite.

        Returns:
            Composite: The new child composite.
        """
        kwargs["parent"] = self
        return self.__class__(*args, **kwargs)

    def addChild(self, child):
        """
        Add a child composite.

        Args:
            child (Composite): The child composite to add.
        """
        self.__children.append(child)
        child.setParent(self)

    def removeChild(self, child):
        """
        Remove a child composite.

        Args:
            child (Composite): The child composite to remove.
        """
        self.__children.remove(child)
        # We don't reset the parent of the child, because that makes restoring
        # the parent-child relationship easier.


class ObservableComposite(Composite):
    """
    A class representing an observable composite object in the composite pattern.
    Inherits from Composite and adds observer pattern functionality.
    """

    @observer.eventSource
    def __setstate__(self, state, event=None):  # pylint: disable=W0221
        """
        Set the state from unpickling with event notification.

        Args:
            state (dict): The state of the composite.
            event (Event, optional): The event to notify.
        """
        oldChildren = set(self.children())
        super().__setstate__(state)
        newChildren = set(self.children())
        childrenRemoved = oldChildren - newChildren
        # pylint: disable=W0142
        if childrenRemoved:
            self.removeChildEvent(event, *childrenRemoved)
        childrenAdded = newChildren - oldChildren
        if childrenAdded:
            self.addChildEvent(event, *childrenAdded)

    @observer.eventSource
    def addChild(self, child, event=None):  # pylint: disable=W0221
        """
        Add a child composite with event notification.

        Args:
            child (Composite): The child composite to add.
            event (Event, optional): The event to notify.
        """
        super().addChild(child)
        self.addChildEvent(event, child)

    def addChildEvent(self, event, *children):
        """
        Notify observers of the addition of children.

        Args:
            event (Event): The event to notify.
            children (Composite): The children added.
        """
        event.addSource(self, *children, **dict(type=self.addChildEventType()))

    @classmethod
    def addChildEventType(class_):
        """
        Get the event type for adding children.

        Returns:
            str: The event type.
        """
        return "composite(%s).child.add" % class_

    @observer.eventSource
    def removeChild(self, child, event=None):  # pylint: disable=W0221
        """
        Remove a child composite with event notification.

        Args:
            child (Composite): The child composite to remove.
            event (Event, optional): The event to notify.
        """
        super().removeChild(child)
        self.removeChildEvent(event, child)

    def removeChildEvent(self, event, *children):
        """
        Notify observers of the removal of children.

        Args:
            event (Event): The event to notify.
            children (Composite): The children removed.
        """
        event.addSource(
            self, *children, **dict(type=self.removeChildEventType())
        )

    @classmethod
    def removeChildEventType(class_):
        """
        Get the event type for removing children.

        Returns:
            str: The event type.
        """
        return "composite(%s).child.remove" % class_

    @classmethod
    def modificationEventTypes(class_):
        """
        Get the list of modification event types.

        Returns:
            list: The list of modification event types.
        """
        try:
            eventTypes = super(
                ObservableComposite, class_
            ).modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [
            class_.addChildEventType(),
            class_.removeChildEventType(),
        ]


class CompositeCollection(object):
    """
    A collection of composite objects.

    Methods:
        append(composite): Add a composite to the collection.
        extend(composites): Add multiple composites to the collection.
        remove(composite): Remove a composite from the collection.
        removeItems(composites): Remove multiple composites from the collection.
        rootItems(): Get the root items of the collection.
        allItemsSorted(): Get all items sorted by hierarchy.
    """

    def __init__(self, initList=None, *args, **kwargs):
        """
        Initialize the collection with an optional list of initial composites.

        Args:
            initList (list, optional): Initial list of composites.
        """
        super().__init__(*args, **kwargs)
        self.extend(initList or [])

    def append(self, composite, event=None):
        """
        Add a composite to the collection.

        Args:
            composite (Composite): The composite to add.
            event (Event, optional): The event to notify.
        """
        return self.extend([composite], event=event)

    @observer.eventSource
    def extend(self, composites, event=None):
        """
        Add multiple composites to the collection with event notification.

        Args:
            composites (list): The list of composites to add.
            event (Event, optional): The event to notify.
        """
        if not composites:
            return
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        super().extend(compositesAndAllChildren, event=event)
        self._addCompositesToParent(composites, event)

    def _compositesAndAllChildren(self, composites):
        """
        Get all composites and their children recursively.

        Args:
            composites (list): The list of composites.

        Returns:
            list: The list of composites and their children.
        """
        compositesAndAllChildren = set(composites)
        for composite in composites:
            compositesAndAllChildren |= set(composite.children(recursive=True))
        return list(compositesAndAllChildren)

    def _addCompositesToParent(self, composites, event):
        """
        Add composites to their parent.

        Args:
            composites (list): The list of composites.
            event (Event): The event to notify.
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
        Remove a composite from the collection.

        Args:
            composite (Composite): The composite to remove.
            event (Event, optional): The event to notify.
        """
        return (
            self.removeItems([composite], event=event)
            if composite in self
            else event
        )

    @observer.eventSource
    def removeItems(self, composites, event=None):
        """
        Remove multiple composites from the collection with event notification.

        Args:
            composites (list): The list of composites to remove.
            event (Event, optional): The event to notify.
        """
        if not composites:
            return
        compositesAndAllChildren = self._compositesAndAllChildren(composites)
        super().removeItems(compositesAndAllChildren, event=event)
        self._removeCompositesFromParent(composites, event)

    def _removeCompositesFromParent(self, composites, event):
        """
        Remove composites from their parent.

        Args:
            composites (list): The list of composites.
            event (Event): The event to notify.
        """
        for composite in composites:
            parent = composite.parent()
            if parent:
                parent.removeChild(composite, event=event)

    def rootItems(self):
        """
        Get the root items of the collection.

        Returns:
            list: The list of root items.
        """
        return [
            composite
            for composite in self
            if composite.parent() is None or composite.parent() not in self
        ]

    def allItemsSorted(self):
        """
        Get all items sorted by hierarchy.

        Returns a list of items and their children, so that if B is
        a child, direct or not, of A, then A will come first in the
        list.

        Returns:
            list: The list of all items sorted by hierarchy.
        """
        result = []
        for item in self.rootItems():
            result.append(item)
            result.extend(item.children(recursive=True))
        return result


class CompositeSet(CompositeCollection, observer.ObservableSet):
    """
    A set of composite objects that is observable.
    """

    pass


class CompositeList(CompositeCollection, observer.ObservableList):
    """
    A list of composite objects that is observable.
    """

    pass
