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

from taskcoachlib import patterns
from taskcoachlib.domain.attribute import icon
from taskcoachlib.domain.date import DateTime, Now
from pubsub import pub
from . import attribute
import functools
import sys
import uuid
import re


class SynchronizedObject(object):
    """
    A base class for synchronized objects.

    This class provides methods for marking objects as new, dirty, deleted, or none,
    and synchronizes these states with events.
    """

    STATUS_NONE = 0
    STATUS_NEW = 1
    STATUS_CHANGED = 2
    STATUS_DELETED = 3

    def __init__(self, *args, **kwargs):
        """
        Initialize the SynchronizedObject instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.__status = kwargs.pop("status", self.STATUS_NEW)
        super().__init__(*args, **kwargs)

    @classmethod
    def markDeletedEventType(class_):
        """
        Get the event type for marking an object as deleted.

        Returns:
            str: The event type for marking an object as deleted.
        """
        return "object.markdeleted"

    @classmethod
    def markNotDeletedEventType(class_):
        """
        Get the event type for marking an object as not deleted.

        Returns:
            str: The event type for marking an object as not deleted.
        """
        return "object.marknotdeleted"

    def __getstate__(self):
        """
        Get the state of the object for serialization.

        Returns:
            dict: The state of the object.
        """
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()

        state["status"] = self.__status
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Set the state of the object from deserialization.

        Args:
            state (dict): The state to set.
            event: The event associated with setting the state.
        """
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        if state["status"] != self.__status:
            if state["status"] == self.STATUS_CHANGED:
                self.markDirty(event=event)
            elif state["status"] == self.STATUS_DELETED:
                self.markDeleted(event=event)
            elif state["status"] == self.STATUS_NEW:
                self.markNew(event=event)
            elif state["status"] == self.STATUS_NONE:
                self.cleanDirty(event=event)

    def getStatus(self):
        """
        Get the current status of the object.

        Returns:
            int: The current status.
        """
        return self.__status

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Mark the object as dirty (changed).

        Args:
            force (bool, optional): Force marking the object as dirty. Defaults to False.
            event: The event associated with marking the object as dirty.
        """
        if not self.setStatusDirty(force):
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusDirty(self, force=False):
        """
        Set the status of the object as dirty (changed).

        Args:
            force (bool, optional): Force setting the status as dirty. Defaults to False.

        Returns:
            bool: True if the status was changed from deleted, False otherwise.
        """
        oldStatus = self.__status
        if self.__status == self.STATUS_NONE or force:
            self.__status = self.STATUS_CHANGED
            return oldStatus == self.STATUS_DELETED
        else:
            return False

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Mark the object as new.

        Args:
            event: The event associated with marking the object as new.
        """
        if not self.setStatusNew():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNew(self):
        """
        Set the status of the object as new.

        Returns:
            bool: True if the status was changed from deleted, False otherwise.
        """
        oldStatus = self.__status
        self.__status = self.STATUS_NEW
        return oldStatus == self.STATUS_DELETED

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Mark the object as deleted.

        Args:
            event: The event associated with marking the object as deleted.
        """
        self.setStatusDeleted()
        event.addSource(self, self.__status, type=self.markDeletedEventType())

    def setStatusDeleted(self):
        """
        Set the status of the object as deleted.
        """
        self.__status = self.STATUS_DELETED

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Mark the object as not dirty (none).

        Args:
            event: The event associated with marking the object as not dirty.
        """
        if not self.setStatusNone():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNone(self):
        """
        Set the status of the object as none.

        Returns:
            bool: True if the status was changed from deleted, False otherwise.
        """
        oldStatus = self.__status
        self.__status = self.STATUS_NONE
        return oldStatus == self.STATUS_DELETED

    def isNew(self):
        """
        Check if the object is new.

        Returns:
            bool: True if the object is new, False otherwise.
        """
        return self.__status == self.STATUS_NEW

    def isModified(self):
        """
        Check if the object is modified (dirty).

        Returns:
            bool: True if the object is modified, False otherwise.
        """
        return self.__status == self.STATUS_CHANGED

    def isDeleted(self):
        """
        Check if the object is deleted.

        Returns:
            bool: True if the object is deleted, False otherwise.
        """
        return self.__status == self.STATUS_DELETED


class Object(SynchronizedObject):
    """
    A base class for objects with common attributes and functionality.

    This class extends SynchronizedObject to provide additional attributes
    and methods for managing an object's state and behavior.
    """

    rx_attributes = re.compile(r"\[(\w+):(.+)\]")

    if sys.version_info.major == 2:
        _long_zero = int(0)
    else:
        _long_zero = 0

    def __init__(self, *args, **kwargs):
        """
        Initialize the Object instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        Attribute = attribute.Attribute
        self.__creationDateTime = kwargs.pop("creationDateTime", None) or Now()
        self.__modificationDateTime = kwargs.pop(
            "modificationDateTime", DateTime.min
        )
        self.__subject = Attribute(
            kwargs.pop("subject", ""), self, self.subjectChangedEvent
        )
        self.__description = Attribute(
            kwargs.pop("description", ""), self, self.descriptionChangedEvent
        )
        self.__fgColor = Attribute(
            kwargs.pop("fgColor", None), self, self.appearanceChangedEvent
        )
        self.__bgColor = Attribute(
            kwargs.pop("bgColor", None), self, self.appearanceChangedEvent
        )
        self.__font = Attribute(
            kwargs.pop("font", None), self, self.appearanceChangedEvent
        )
        self.__icon = Attribute(
            kwargs.pop("icon", ""), self, self.appearanceChangedEvent
        )
        self.__selectedIcon = Attribute(
            kwargs.pop("selectedIcon", ""), self, self.appearanceChangedEvent
        )
        self.__ordering = Attribute(
            kwargs.pop("ordering", Object._long_zero),
            self,
            self.orderingChangedEvent,
        )
        self.__id = kwargs.pop("id", None) or str(uuid.uuid1())
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """
        Return a string representation of the Object instance.

        Returns:
            str: The string representation.
        """
        return self.subject()

    def __getstate__(self):
        """
        Get the state of the object for serialization.

        Returns:
            dict: The state of the object.
        """
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()
        state.update(
            dict(
                id=self.__id,
                creationDateTime=self.__creationDateTime,
                modificationDateTime=self.__modificationDateTime,
                subject=self.__subject.get(),
                description=self.__description.get(),
                fgColor=self.__fgColor.get(),
                bgColor=self.__bgColor.get(),
                font=self.__font.get(),
                icon=self.__icon.get(),
                ordering=self.__ordering.get(),
                selectedIcon=self.__selectedIcon.get(),
            )
        )
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Set the state of the object from deserialization.

        Args:
            state (dict): The state to set.
            event: The event associated with setting the state.
        """
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        self.__id = state["id"]
        self.setSubject(state["subject"], event=event)
        self.setDescription(state["description"], event=event)
        self.setForegroundColor(state["fgColor"], event=event)
        self.setBackgroundColor(state["bgColor"], event=event)
        self.setFont(state["font"], event=event)
        self.setIcon(state["icon"], event=event)
        self.setSelectedIcon(state["selectedIcon"], event=event)
        self.setOrdering(state["ordering"], event=event)
        self.__creationDateTime = state["creationDateTime"]
        # Set modification date/time last to overwrite changes made by the
        # setters above
        self.__modificationDateTime = state["modificationDateTime"]

    def __getcopystate__(self):
        """
        Return a dictionary that can be passed to __init__ when creating
        a copy of the object.

        E.g. copy = obj.__class__(**original.__getcopystate__())

        Returns:
            dict: The state dictionary for creating a copy.
        """
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        # Note that we don't put the id and the creation date/time in the state
        # dict, because a copy should get a new id and a new creation date/time
        state.update(
            dict(
                subject=self.__subject.get(),
                description=self.__description.get(),
                fgColor=self.__fgColor.get(),
                bgColor=self.__bgColor.get(),
                font=self.__font.get(),
                icon=self.__icon.get(),
                selectedIcon=self.__selectedIcon.get(),
                ordering=self.__ordering.get(),
            )
        )
        return state

    def copy(self):
        """
        Create a copy of the object.

        Returns:
            Object: A new instance of the object with the same state.
        """
        return self.__class__(**self.__getcopystate__())

    @classmethod
    def monitoredAttributes(class_):
        """
        Get the list of monitored attributes.

        Returns:
            list: The list of monitored attributes.
        """
        return ["ordering", "subject", "description", "appearance"]

    # Id:

    def id(self):
        """
        Get the ID of the object.

        Returns:
            str: The ID of the object.
        """
        return self.__id

    # Custom attributes
    def customAttributes(self, sectionName):
        """
        Get the custom attributes for a given section name.

        Args:
            sectionName (str): The section name.

        Returns:
            set: The set of custom attributes.
        """
        attributes = set()
        for line in self.description().split("\n"):
            match = self.rx_attributes.match(line.strip())
            if match and match.group(1) == sectionName:
                attributes.add(match.group(2))
        return attributes

    # Editing date/time:

    def creationDateTime(self):
        """
        Get the creation date and time of the object.

        Returns:
            DateTime: The creation date and time.
        """
        return self.__creationDateTime

    def modificationDateTime(self):
        """
        Get the modification date and time of the object.

        Returns:
            DateTime: The modification date and time.
        """
        return self.__modificationDateTime

    def setModificationDateTime(self, dateTime):
        """
        Set the modification date and time of the object.

        Args:
            dateTime (DateTime): The modification date and time.
        """
        self.__modificationDateTime = dateTime

    @staticmethod
    def modificationDateTimeSortFunction(**kwargs):
        """
        Get a sort function for sorting by modification date and time.

        Returns:
            function: The sort function.
        """
        return lambda item: item.modificationDateTime()

    @staticmethod
    def creationDateTimeSortFunction(**kwargs):
        """
        Get a sort function for sorting by creation date and time.

        Returns:
            function: The sort function.
        """
        return lambda item: item.creationDateTime()

    # Subject:

    def subject(self):
        """
        Get the subject of the object.

        Returns:
            str: The subject of the object.
        """
        return self.__subject.get()

    def setSubject(self, subject, event=None):
        """
        Set the subject of the object.

        Args:
            subject (str): The subject to set.
            event: The event associated with setting the subject.
        """
        self.__subject.set(subject, event=event)

    def subjectChangedEvent(self, event):
        """
        Handle the subject changed event.

        Args:
            event: The event.
        """
        event.addSource(
            self, self.subject(), type=self.subjectChangedEventType()
        )

    @classmethod
    def subjectChangedEventType(class_):
        """
        Get the event type for subject changed events.

        Returns:
            str: The event type for subject changed events.
        """
        return "%s.subject" % class_

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Function to pass to list.sort when sorting by subject.

        Get a sort function for sorting by subject.

        Returns:
            function: The sort function.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject()
        else:
            return lambda item: item.subject().lower()

    @classmethod
    def subjectSortEventTypes(class_):
        """
        Get the event types that influence the subject sort order.

        Returns:
            tuple: The event types.
        """
        return (class_.subjectChangedEventType(),)

    # Ordering:

    def ordering(self):
        """
        Get the ordering of the object.

        Returns:
            int: The ordering.
        """
        return self.__ordering.get()

    def setOrdering(self, ordering, event=None):
        """
        Set the ordering of the object.

        Args:
            ordering (int): The ordering to set.
            event: The event associated with setting the ordering.
        """
        self.__ordering.set(ordering, event=event)

    def orderingChangedEvent(self, event):
        """
        Handle the ordering changed event.

        Args:
            event: The event.
        """
        event.addSource(
            self, self.ordering(), type=self.orderingChangedEventType()
        )

    @classmethod
    def orderingChangedEventType(class_):
        """
        Get the event type for ordering changed events.

        Returns:
            str: The event type for ordering changed events.
        """
        return "%s.ordering" % class_

    @staticmethod
    def orderingSortFunction(**kwargs):
        """
        Get a sort function for sorting by ordering.

        Returns:
            function: The sort function.
        """
        return lambda item: item.ordering()

    @classmethod
    def orderingSortEventTypes(class_):
        """
        Get the event types that influence the ordering sort order.

        Returns:
            tuple: The event types.
        """
        return (class_.orderingChangedEventType(),)

    # Description:

    def description(self):
        """
        Get the description of the object.

        Returns:
            str: The description of the object.
        """
        return self.__description.get()

    def setDescription(self, description, event=None):
        """
        Set the description of the object.

        Args:
            description (str): The description to set.
            event: The event associated with setting the description.
        """
        self.__description.set(description, event=event)

    def descriptionChangedEvent(self, event):
        """
        Handle the description changed event.

        Args:
            event: The event.
        """
        event.addSource(
            self, self.description(), type=self.descriptionChangedEventType()
        )

    @classmethod
    def descriptionChangedEventType(class_):
        """
        Get the event type for description changed events.

        Returns:
            str: The event type for description changed events.
        """
        return "%s.description" % class_

    @staticmethod
    def descriptionSortFunction(**kwargs):
        """
        Get a sort function for sorting by description.

        Function to pass to list.sort when sorting by description.

        Returns:
            function: The sort function.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.description()
        else:
            return lambda item: item.description().lower()

    @classmethod
    def descriptionSortEventTypes(class_):
        """
        Get the event types that influence the description sort order.

        Returns:
            tuple: The event types.
        """
        return (class_.descriptionChangedEventType(),)

    # Color:

    def setForegroundColor(self, color, event=None):
        """
        Set the foreground color of the object.

        Args:
            color: The color to set.
            event: The event associated with setting the color.
        """
        self.__fgColor.set(color, event=event)

    def foregroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Get the foreground color of the object.

        Args:
            recursive (bool, optional): Whether to get the color recursively. Defaults to False.

        Returns:
            The foreground color.
        """
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__fgColor.get()

    def setBackgroundColor(self, color, event=None):
        """
        Set the background color of the object.

        Args:
            color: The color to set.
            event: The event associated with setting the color.
        """
        self.__bgColor.set(color, event=event)

    def backgroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Get the background color of the object.

        Args:
            recursive (bool, optional): Whether to get the color recursively. Defaults to False.

        Returns:
            The background color.
        """
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__bgColor.get()

    # Font:

    def font(self, recursive=False):  # pylint: disable=W0613
        """
        Get the font of the object.

        Args:
            recursive (bool, optional): Whether to get the font recursively. Defaults to False.

        Returns:
            The font.
        """
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__font.get()

    def setFont(self, font, event=None):
        """
        Set the font of the object.

        Args:
            font: The font to set.
            event: The event associated with setting the font.
        """
        self.__font.set(font, event=event)

    # Icons:

    def icon(self):
        """
        Get the icon of the object.

        Returns:
            The icon.
        """
        return self.__icon.get()

    def setIcon(self, icon, event=None):
        """
        Set the icon of the object.

        Args:
            icon: The icon to set.
            event: The event associated with setting the icon.
        """
        self.__icon.set(icon, event=event)

    def selectedIcon(self):
        """
        Get the selected icon of the object.

        Returns:
            The selected icon.
        """
        return self.__selectedIcon.get()

    def setSelectedIcon(self, selectedIcon, event=None):
        """
        Set the selected icon of the object.

        Args:
            selectedIcon: The selected icon to set.
            event: The event associated with setting the selected icon.
        """
        self.__selectedIcon.set(selectedIcon, event=event)

    # Event types:

    @classmethod
    def appearanceChangedEventType(class_):
        """
        Get the event type for appearance changed events.

        Returns:
            str: The event type for appearance changed events.
        """
        return "%s.appearance" % class_

    def appearanceChangedEvent(self, event):
        """
        Handle the appearance changed event.

        Args:
            event: The event.
        """
        event.addSource(self, type=self.appearanceChangedEventType())

    @classmethod
    def modificationEventTypes(class_):
        """
        Get the event types for modification events.

        Returns:
            list: The list of event types.
        """
        try:
            eventTypes = super(Object, class_).modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [
            class_.subjectChangedEventType(),
            class_.descriptionChangedEventType(),
            class_.appearanceChangedEventType(),
            class_.orderingChangedEventType(),
        ]


class CompositeObject(Object, patterns.ObservableComposite):
    """
    A composite object that can contain other objects as children.

    This class extends Object and ObservableComposite to provide additional
    methods for managing child objects and their state.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the CompositeObject instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.__expandedContexts = set(kwargs.pop("expandedContexts", []))
        super().__init__(*args, **kwargs)

    def __getcopystate__(self):
        """
        Return a dictionary that can be passed to __init__ when creating
        a copy of the composite object.

        Returns:
            dict: The state dictionary for creating a copy.
        """
        state = super().__getcopystate__()
        state.update(dict(expandedContexts=self.expandedContexts()))
        return state

    @classmethod
    def monitoredAttributes(cls):
        """
        Get the list of monitored attributes.

        Returns:
            list: The list of monitored attributes.
        """
        return Object.monitoredAttributes() + ["expandedContexts"]

    # Subject:

    def subject(self, recursive=False):  # pylint: disable=W0221
        """
        Get the subject of the composite object.

        Args:
            recursive (bool, optional): Whether to get the subject recursively. Defaults to False.

        Returns:
            str: The subject of the composite object.
        """
        subject = super().subject()
        if recursive and self.parent():
            subject = "%s -> %s" % (
                self.parent().subject(recursive=True),
                subject,
            )
        return subject

    def subjectChangedEvent(self, event):
        """
        Handle the subject changed event.

        Args:
            event: The event.
        """
        super().subjectChangedEvent(event)
        for child in self.children():
            child.subjectChangedEvent(event)

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Get a sort function for sorting by subject.

        Function to pass to list.sort when sorting by subject.

        Returns:
            function: The sort function.
        """
        recursive = kwargs.get("treeMode", False)
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject(recursive=recursive)
        else:
            return lambda item: item.subject(recursive=recursive).lower()

    # Description:

    def description(self, recursive=False):  # pylint: disable=W0221,W0613
        """
        Get the description of the composite object.

        Args:
            recursive (bool, optional): Whether to get the description recursively. Defaults to False.

        Returns:
            str: The description of the composite object.
        """
        # Allow for the recursive flag, but ignore it
        return super().description()

    # Expansion state:

    # Note: expansion state is stored by context. A context is a simple string
    # identifier (without comma's) to distinguish between different contexts,
    # i.e. viewers. A composite object may be expanded in one context and
    # collapsed in another.

    def isExpanded(self, context="None"):
        """
        Check if the composite object is expanded in the specified context.

        Returns a boolean indicating whether the composite object is
        expanded in the specified context.

        Args:
            context (str, optional): The context. Defaults to "None".

        Returns:
            bool: True if the composite object is expanded, False otherwise.
        """
        return context in self.__expandedContexts

    def expandedContexts(self):
        """
        Get the list of contexts where the composite object is expanded.

        Returns:
            list: The list of contexts.
        """
        return list(self.__expandedContexts)

    def expand(self, expand=True, context="None", notify=True):
        """
        Expand or collapse the composite object in the specified context.

        Args:
            expand (bool, optional): Whether to expand or collapse. Defaults to True.
            context (str, optional): The context. Defaults to "None".
            notify (bool, optional): Whether to send a notification. Defaults to True.
        """
        if expand == self.isExpanded(context):
            return
        if expand:
            self.__expandedContexts.add(context)
        else:
            self.__expandedContexts.discard(context)
        if notify:
            pub.sendMessage(
                self.expansionChangedEventType(), newValue=expand, sender=self
            )

    @classmethod
    def expansionChangedEventType(cls):
        """
        Get the event type for expansion state changes.

        The event type used for notifying changes in the expansion state
        of a composite object.

        Returns:
            str: The event type for expansion state changes.
        """
        return "pubsub.%s.expandedContexts" % cls.__name__.lower()

    def expansionChangedEvent(self, event):
        """
        Handle the expansion changed event.

        Args:
            event: The event.
        """
        event.addSource(self, type=self.expansionChangedEventType())

    # The ChangeMonitor expects this...
    @classmethod
    def expandedContextsChangedEventType(class_):
        """
        Get the event type for expanded contexts changes.

        Returns:
            str: The event type for expanded contexts changes.
        """
        return class_.expansionChangedEventType()

    # Appearance:

    def appearanceChangedEvent(self, event):
        """
        Handle the appearance changed event.

        Args:
            event: The event.
        """
        super().appearanceChangedEvent(event)
        # Assume that most of the times our children change appearance too
        for child in self.children():
            child.appearanceChangedEvent(event)

    def foregroundColor(self, recursive=False):
        """
        Get the foreground color of the composite object.

        Args:
            recursive (bool, optional): Whether to get the color recursively. Defaults to False.

        Returns:
            The foreground color.
        """
        myFgColor = super().foregroundColor()
        if not myFgColor and recursive and self.parent():
            return self.parent().foregroundColor(recursive=True)
        else:
            return myFgColor

    def backgroundColor(self, recursive=False):
        """
        Get the background color of the composite object.

        Args:
            recursive (bool, optional): Whether to get the color recursively. Defaults to False.

        Returns:
            The background color.
        """
        myBgColor = super().backgroundColor()
        if not myBgColor and recursive and self.parent():
            return self.parent().backgroundColor(recursive=True)
        else:
            return myBgColor

    def font(self, recursive=False):
        """
        Get the font of the composite object.

        Args:
            recursive (bool, optional): Whether to get the font recursively. Defaults to False.

        Returns:
            The font.
        """
        myFont = super().font()
        if not myFont and recursive and self.parent():
            return self.parent().font(recursive=True)
        else:
            return myFont

    def icon(self, recursive=False):
        """
        Get the icon of the composite object.

        Args:
            recursive (bool, optional): Whether to get the icon recursively. Defaults to False.

        Returns:
            The icon.
        """
        myIcon = super().icon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().icon(recursive=True)
        return self.pluralOrSingularIcon(myIcon, native=super().icon() == "")

    def selectedIcon(self, recursive=False):
        """
        Get the selected icon of the composite object.

        Args:
            recursive (bool, optional): Whether to get the selected icon recursively. Defaults to False.

        Returns:
            The selected icon.
        """
        myIcon = super().selectedIcon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().selectedIcon(recursive=True)
        return self.pluralOrSingularIcon(
            myIcon, native=super().selectedIcon() == ""
        )

    def pluralOrSingularIcon(self, myIcon, native=True):
        """
        Get the plural or singular icon based on whether the object has children.

        Args:
            myIcon: The base icon.
            native (bool, optional): Whether the icon is from the user settings. Defaults to True.

        Returns:
            The plural or singular icon.
        """
        hasChildren = any(
            child for child in self.children() if not child.isDeleted()
        )
        mapping = (
            icon.itemImagePlural if hasChildren else icon.itemImageSingular
        )
        # If the icon comes from the user settings, only pluralize it; this is probably
        # the Way of the Least Astonishment
        if native or hasChildren:
            return mapping.get(myIcon, myIcon)
        return myIcon

    # Event types:

    @classmethod
    def modificationEventTypes(class_):
        """
        Get the event types for modification events.

        Returns:
            list: The list of event types.
        """
        return super(CompositeObject, class_).modificationEventTypes() + [
            class_.expansionChangedEventType()
        ]

    # Override SynchronizedObject methods to also mark child objects

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Mark the composite object and its children as deleted.

        Args:
            event: The event associated with marking the object as deleted.
        """
        super().markDeleted(event=event)
        for child in self.children():
            child.markDeleted(event=event)

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Mark the composite object and its children as new.

        Args:
            event: The event associated with marking the object as new.
        """
        super().markNew(event=event)
        for child in self.children():
            child.markNew(event=event)

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Mark the composite object and its children as dirty (changed).

        Args:
            force (bool, optional): Force marking the object as dirty. Defaults to False.
            event: The event associated with marking the object as dirty.
        """
        super().markDirty(force, event=event)
        for child in self.children():
            child.markDirty(force, event=event)

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Mark the composite object and its children as not dirty (none).

        Args:
            event: The event associated with marking the object as not dirty.
        """
        super().cleanDirty(event=event)
        for child in self.children():
            child.cleanDirty(event=event)
