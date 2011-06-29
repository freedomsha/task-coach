'''
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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
'''

from taskcoachlib.changes import ChangeMonitor
from taskcoachlib.domain.note import NoteOwner
from taskcoachlib.domain.attachment import AttachmentOwner
from taskcoachlib.domain.base import CompositeObject
from taskcoachlib.domain.task import Task


class ChangeSynchronizer(object):
    def __init__(self, monitor, allChanges):
        self._monitor = monitor
        self._allChanges = allChanges

    @staticmethod
    def allObjects(theList):
        result = list()
        for obj in theList:
            result.append(obj)
            if isinstance(obj, CompositeObject):
                result.extend(ChangeSynchronizer.allObjects(obj.children()))
            if isinstance(obj, NoteOwner):
                result.extend(ChangeSynchronizer.allObjects(obj.notes()))
            if isinstance(obj, AttachmentOwner):
                result.extend(ChangeSynchronizer.allObjects(obj.attachments()))
            if isinstance(obj, Task):
                result.extend(obj.efforts())
        return result

    def sync(self, lists):
        self.diskChanges = ChangeMonitor()
        self.conflictChanges = ChangeMonitor()

        self.memMap = dict()
        self.memOwnerMap = dict()
        self.diskMap = dict()
        self.diskOwnerMap = dict()

        for devGUID, changes in self._allChanges.items():
            if devGUID == self._monitor.guid():
                self.diskChanges = changes
            else:
                changes.merge(self._monitor)
        self._allChanges[self._monitor.guid()] = self._monitor

        for memList, diskList in lists:
            self.mergeObjects(memList, diskList)

        # Cleanup monitor
        self._monitor.empty()
        for memList, diskList in lists:
            for obj in self.allObjects(memList.rootItems()):
                self._monitor.resetChanges(obj)

        # Merge conflict changes
        for devGUID, changes in self._allChanges.items():
            if devGUID != self._monitor.guid():
                changes.merge(self.conflictChanges)

    def mergeObjects(self, memList, diskList):
        # Map id to object
        def addIds(objects, idMap, ownerMap, owner=None):
            for obj in objects:
                idMap[obj.id()] = obj
                if owner is not None:
                    ownerMap[obj.id()] = owner
                if isinstance(obj, CompositeObject):
                    addIds(obj.children(), idMap, ownerMap)
                if isinstance(obj, NoteOwner):
                    addIds(obj.notes(), idMap, ownerMap, obj)
                if isinstance(obj, AttachmentOwner):
                    addIds(obj.attachments(), idMap, ownerMap, obj)
                if isinstance(obj, Task):
                    addIds(obj.efforts(), idMap, ownerMap)
        addIds(memList, self.memMap, self.memOwnerMap)
        addIds(diskList, self.diskMap, self.diskOwnerMap)

        self.mergeCompositeObjects(memList, diskList)
        self.mergeOwnedObjectsFromDisk(diskList)
        self.reparentObjects(memList, diskList)
        self.deletedObjects(memList)
        self.deletedOwnedObjects(memList)
        self.applyChanges(memList)

    def mergeCompositeObjects(self, memList, diskList):
        # First pass: new composite objects on disk. Don't handle
        # other (notes belonging to object, attachments, efforts) yet
        # because they may belong to a category. This assumes that
        # categories are the first domain class handled.

        for diskObject in diskList.allItemsSorted():
            memChanges = self._monitor.getChanges(diskObject)
            deleted = memChanges is not None and '__del__' in memChanges

            if diskObject.id() not in self.memMap and not deleted:
                if isinstance(diskObject, CompositeObject):
                    # New children will be handled later. This assumes
                    # that the parent() is not changed when removing a
                    # child.
                    for child in diskObject.children():
                        diskObject.removeChild(child)
                    parent = diskObject.parent()
                    if parent is not None and parent.id() in self.memMap:
                        parent = self.memMap[parent.id()]
                        parent.addChild(diskObject)
                        diskObject.setParent(parent)
                    elif parent is not None:
                        # Parent deleted from memory; the task will be
                        # top-level.
                        diskObject.setParent(None)
                        self.conflictChanges.addChange(diskObject, '__parent__')
                memList.append(diskObject)
                self.memMap[diskObject.id()] = diskObject

    def mergeOwnedObjectsFromDisk(self, diskList):
        # Second pass: 'owned' objects (notes and attachments
        # currently) new on disk, and efforts.

        for obj in diskList.allItemsSorted():
            if isinstance(obj, NoteOwner):
                self._handleNewOwnedObjectsOnDisk(obj.notes())
            if isinstance(obj, AttachmentOwner):
                self._handleNewOwnedObjectsOnDisk(obj.attachments())
            if isinstance(obj, Task):
                self._handleNewEffortsOnDisk(obj.efforts())

    def _handleNewOwnedObjectsOnDisk(self, diskObjects):
        for diskObject in diskObjects:
            className = diskObject.__class__.__name__
            if className.endswith('Attachment'):
                className = 'Attachment'

            if isinstance(diskObject, CompositeObject):
                children = diskObject.children()[:]

            memChanges = self._monitor.getChanges(diskObject)
            deleted = memChanges is not None and '__del__' in memChanges

            if diskObject.id() not in self.memMap and not deleted:
                addObject = True

                if isinstance(diskObject, CompositeObject):
                    for child in diskObject.children():
                        diskObject.removeChild(child)
                    parent = diskObject.parent()
                    if parent is not None and parent.id() in self.memMap:
                        parent = self.memMap[parent.id()]
                        parent.addChild(diskObject)
                        diskObject.setParent(parent)
                    elif parent is not None:
                        # Parent deleted from memory; the object
                        # becomes top-level but its owner stays
                        # the same.
                        diskObject.setParent(None)
                        while parent.parent() is not None:
                            parent = parent.parent()
                        diskOwner = self.diskOwnerMap[parent.id()]
                        if diskOwner.id() in self.memMap:
                            memOwner = self.memMap[diskOwner.id()]
                            getattr(memOwner, 'add%s' % className)(diskObject)
                            self.conflictChanges.addChange(diskObject, '__owner__')
                            self.memOwnerMap[diskObject.id()] = memOwner
                    else:
                        diskOwner = self.diskOwnerMap[diskObject.id()]
                        if diskOwner.id() in self.memMap:
                            memOwner = self.memMap[diskOwner.id()]
                            getattr(memOwner, 'add%s' % className)(diskObject)
                            self.memOwnerMap[diskObject.id()] = memOwner
                        else:
                            # Owner deleted. Just forget it.
                            self.conflictChanges.addChange(diskObject, '__del__')
                            addObject = False
                else:
                    diskOwner = self.diskOwnerMap[diskObject.id()]
                    if diskOwner.id() in self.memMap:
                        memOwner = self.memMap[diskOwner.id()]
                        getattr(memOwner, 'add%s' % className)(diskObject)
                        self.memOwnerMap[diskObject.id()] = memOwner
                    else:
                        # Forget it again...
                        self.conflictChanges.addChange(diskObject, '__del__')
                        addObject = False

                if addObject:
                    self.memMap[diskObject.id()] = diskObject

            if diskObject.id() in self.memMap:
                if isinstance(diskObject, CompositeObject):
                    self._handleNewOwnedObjectsOnDisk(children)
                if isinstance(diskObject, NoteOwner):
                    self._handleNewOwnedObjectsOnDisk(diskObject.notes())
                if isinstance(diskObject, AttachmentOwner):
                    self._handleNewOwnedObjectsOnDisk(diskObject.attachments())

    def _handleNewEffortsOnDisk(self, diskEfforts):
        for diskEffort in diskEfforts:
            memChanges = self._monitor.getChanges(diskEffort)
            deleted = memChanges is not None and '__del__' in memChanges
            if diskEffort.id() not in self.memMap and not deleted:
                diskTask = diskEffort.parent()
                if diskTask.id() in self.memMap:
                    memTask = self.memMap[diskTask.id()]
                    diskEffort.setTask(memTask)
                    self.memMap[diskEffort.id()] = diskEffort
                else:
                    # Task deleted; forget it.
                    self.conflictChanges.addChange(diskEffort, '__del__')

    def reparentObjects(self, memList, diskList):
        # Third pass: objects reparented on disk.

        for diskObject in self.allObjects(diskList):
            diskChanges = self.diskChanges.getChanges(diskObject)
            if diskChanges is not None and '__parent__' in diskChanges:
                memChanges = self._monitor.getChanges(diskObject)
                memObject = self.memMap[diskObject.id()]
                memList.remove(memObject)

                # Note: no conflict resolution for this one,
                # it would be a bit tricky... Instead, the
                # disk version wins.

                def sameParents(a, b):
                    if a is None and b is None:
                        return True
                    elif a is None or b is None:
                        return False
                    return a.id() == b.id()

                parentConflict = False
                if memChanges is not None and '__parent__' in memChanges:
                    if not sameParents(memObject.parent(), diskObject.parent()):
                        parentConflict = True

                if memObject.parent() is not None:
                    memObject.parent().removeChild(memObject)

                if parentConflict:
                    diskParent = diskObject.parent()

                    if diskParent is None:
                        memObject.setParent(None)
                    else:
                        if diskParent.id() in self.memMap:
                            memParent = self.memMap[diskParent.id()]
                            memParent.addChild(memObject)
                            memObject.setParent(memParent)
                        else:
                            # New parent deleted from memory...
                            memObject.setParent(None)
                            self.conflictChanges.addChange(memObject, '__parent__')
                else:
                    diskParent = diskObject.parent()
                    if diskParent is None:
                        memObject.setParent(None)
                    else:
                        if diskParent.id() in self.memMap:
                            memParent = self.memMap[diskParent.id()]
                            memParent.addChild(memObject)
                            memObject.setParent(memParent)
                        else:
                            memObject.setParent(None)
                            self.conflictChanges.addChange(memObject, '__parent__')

                memList.append(memObject)

    def deletedObjects(self, memList):
        # Fourth pass: objects deleted from disk

        for memObject in memList.allItemsSorted():
            diskChanges = self.diskChanges.getChanges(memObject)

            if diskChanges is not None and '__del__' in diskChanges:
                # If there are local changes we just ignore them if
                # the object has been deleted on disk.
                memList.remove(memObject)
                del self.memMap[memObject.id()]
                if memObject.id() in self.memOwnerMap:
                    del self.memOwnerMap[memObject.id()]

    def deletedOwnedObjects(self, memList):
        for obj in memList.allItemsSorted():
            if isinstance(obj, NoteOwner):
                self._handleOwnedObjectsRemovedFromDisk(obj.notes())
            if isinstance(obj, AttachmentOwner):
                self._handleOwnedObjectsRemovedFromDisk(obj.attachments())
            if isinstance(obj, Task):
                self._handleEffortsRemovedFromDisk(obj.efforts())

    def _handleOwnedObjectsRemovedFromDisk(self, memObjects):
        for memObject in memObjects:
            className = memObject.__class__.__name__
            if className.endswith('Attachment'):
                className = 'Attachment'

            if isinstance(memObject, CompositeObject):
                self._handleOwnedObjectsRemovedFromDisk(memObject.children())
            if isinstance(memObject, NoteOwner):
                self._handleOwnedObjectsRemovedFromDisk(memObject.notes())
            if isinstance(memObject, AttachmentOwner):
                self._handleOwnedObjectsRemovedFromDisk(memObject.attachments())

            diskChanges = self.diskChanges.getChanges(memObject)
            if diskChanges is not None and '__del__' in diskChanges:
                # Same remark as above
                if isinstance(memObject, CompositeObject):
                    if memObject.parent() is None:
                        getattr(self.memOwnerMap[memObject.id()], 'remove%s' % className)(memObject)
                    else:
                        self.memMap[memObject.parent().id()].removeChild(memObject)
                else:
                    getattr(self.memOwnerMap[memObject.id()], 'remove%s' % className)(memObject)
                del self.memMap[memObject.id()]

    def _handleEffortsRemovedFromDisk(self, memEfforts):
        for memEffort in memEfforts:
            diskChanges = self.diskChanges.getChanges(memEffort)

            if diskChanges is not None and '__del__' in diskChanges:
                # Same remark as above
                self.memMap[memEffort.parent().id()].removeEffort(memEffort)
                del self.memMap[memEffort.id()]

    def applyChanges(self, memList):
        # Final: apply disk changes

        for memObject in self.allObjects(memList.rootItems()):
            diskChanges = self.diskChanges.getChanges(memObject)
            if diskChanges:
                memChanges = self._monitor.getChanges(memObject)
                diskObject = self.diskMap[memObject.id()]

                conflicts = []

                for changeName in diskChanges:
                    if changeName == '__parent__':
                        pass # Already handled
                    elif changeName == '__categories__':
                        diskCategories = set([self.memMap[category.id()] for category in diskObject.categories()])
                        if memChanges is not None and \
                           '__categories__' in memChanges and \
                           diskCategories != memObject.categories():
                            conflicts.append('__categories__')
                            self.conflictChanges.addChange(memObject, '__categories__')
                        else:
                            for cat in memObject.categories():
                                cat.removeCategorizable(memObject)
                                memObject.removeCategory(cat)
                            for cat in diskCategories:
                                cat.addCategorizable(memObject)
                                memObject.addCategory(cat)
                    elif changeName == 'appearance':
                        attrNames = ['foregroundColor', 'backgroundColor', 'font', 'icon', 'selectedIcon']
                        if memChanges is not None and \
                           'appearance' in memChanges:
                            for attrName in attrNames:
                                if getattr(memObject, attrName)() != getattr(diskObject, attrName)():
                                    conflicts.append(attrName)
                            self.conflictChanges.addChange(memObject, 'appearance')
                        else:
                            for attrName in attrNames:
                                getattr(memObject, 'set' + attrName[0].upper() + attrName[1:])(getattr(diskObject, attrName)())
                    elif changeName == 'expandedContexts':
                        # Note: no conflict resolution for this one.
                        memObject.expand(diskObject.isExpanded())
                    else:
                        if changeName in ['start', 'stop']:
                            getterName = 'get' + changeName[0].upper() + changeName[1:]
                        else:
                            getterName = changeName
                        if memChanges is not None and \
                               changeName in memChanges and \
                               getattr(memObject, getterName)() != getattr(diskObject, getterName)():
                            conflicts.append(changeName)
                            self.conflictChanges.addChange(memObject, changeName)
                        else:
                            getattr(memObject, 'set' + changeName[0].upper() + changeName[1:])(getattr(diskObject, getterName)())

                    if conflicts:
                        print conflicts # XXXTODO
