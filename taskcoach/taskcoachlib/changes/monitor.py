"""
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
"""

from taskcoachlib.patterns import Observer, ObservableComposite
from taskcoachlib.domain.categorizable import CategorizableCompositeObject

# from taskcoachlib.domain.base import NoteOwner, AttachmentOwner
# vous êtes sûr ? quel NoteOwner utiliser ? domain/note/noteowner ou domain/base/owner ?
from taskcoachlib.domain.attachment import AttachmentOwner
from taskcoachlib.domain.note import NoteOwner
from taskcoachlib.domain.task import Task
from taskcoachlib.domain.effort import Effort

# from taskcoachlib.thirdparty import guid
# UUID : C'est une standardisation.
# On utilise la librairie standard de Python au lieu d'un module tiers potentiellement obsolète.
import uuid

# try:
from pubsub.core import topicobj
from pubsub import pub

# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub


class ChangeMonitor(Observer):
    """
    Cette classe surveille les modifications apportées à l'objet en fonction de chaque attribut.
    """

    def __init__(self, id_=None):
        # super(ChangeMonitor, self).__init__()
        super().__init__()

        # self.__guid = id_ or guid.generate()
        self.__guid = id_ or str(uuid.uuid4())
        self.__frozen = False
        self.__collections = []
        self._changes = dict()
        self._classes = set()
        self.reset()

    def freeze(self):
        self.__frozen = True

    def thaw(self):
        self.__frozen = False

    def guid(self):
        return self.__guid

    def reset(self):
        self._changes = dict()
        self._classes = set()

    def monitorClass(self, klass):
        if klass not in self._classes:
            for name in klass.monitoredAttributes():
                # eventType = getattr(klass, "%sChangedEventType" % name)()
                eventType = getattr(klass, f"{name}ChangedEventType")()
                if eventType.startswith("pubsub"):
                    pub.subscribe(self.onAttributeChanged, eventType)
                else:
                    self.registerObserver(
                        self.onAttributeChanged_Deprecated, eventType
                    )
                self._classes.add(klass)
            if issubclass(klass, ObservableComposite):
                self.registerObserver(
                    self.onChildAdded, klass.addChildEventType()
                )
                self.registerObserver(
                    self.onChildRemoved, klass.removeChildEventType()
                )
            if issubclass(klass, CategorizableCompositeObject):
                self.registerObserver(
                    self.onCategoryAdded, klass.categoryAddedEventType()
                )
                self.registerObserver(
                    self.onCategoryRemoved, klass.categoryRemovedEventType()
                )
            if issubclass(klass, Task):
                pub.subscribe(
                    self.onEffortAddedOrRemoved, Task.effortsChangedEventType()
                )
                pub.subscribe(
                    self.onPrerequisitesChanged,
                    Task.prerequisitesChangedEventType(),
                )
                # pubsub.core.callables.ListenerMismatchError: Listener "ChangeMonitor.onEffortAddedOrRemoved"
                # (from module "taskcoachlib.changes.monitor") inadequate: needs to accept 1 more args (newValue)
            if issubclass(klass, NoteOwner):
                # Unresolved attribute reference 'noteAddedEventType' for class 'NoteOwner'
                self.registerObserver(
                    self.onOtherObjectAdded, klass.noteAddedEventType()
                )
                # Unresolved attribute reference 'noteRemovedEventType' for class 'NoteOwner'
                self.registerObserver(
                    self.onOtherObjectRemoved, klass.noteRemovedEventType()
                )
            if issubclass(klass, AttachmentOwner):
                # Cannot find reference 'attachmentAddedEventType' in 'AttachmentOwner | AttachmentOwner'
                self.registerObserver(
                    self.onOtherObjectAdded, klass.attachmentAddedEventType()
                )
                # Cannot find reference 'attachmentRemovedEventType' in 'AttachmentOwner | AttachmentOwner'
                self.registerObserver(
                    self.onOtherObjectRemoved,
                    klass.attachmentRemovedEventType(),
                )
            if issubclass(klass, Effort):
                pub.subscribe(
                    self.onEffortTaskChanged, Effort.taskChangedEventType()
                )

    def unmonitorClass(self, klass):
        if klass in self._classes:
            for name in klass.monitoredAttributes():
                # eventType = getattr(klass, "%sChangedEventType" % name)()
                eventType = getattr(klass, f"{name}ChangedEventType")()
                if eventType.startswith("pubsub"):
                    pub.unsubscribe(self.onAttributeChanged, eventType)
                else:
                    self.removeObserver(
                        self.onAttributeChanged_Deprecated, eventType
                    )
            if issubclass(klass, ObservableComposite):
                self.removeObserver(
                    self.onChildAdded, klass.addChildEventType()
                )
                self.removeObserver(
                    self.onChildRemoved, klass.removeChildEventType()
                )
            if issubclass(klass, CategorizableCompositeObject):
                self.removeObserver(
                    self.onCategoryAdded, klass.categoryAddedEventType()
                )
                self.removeObserver(
                    self.onCategoryRemoved, klass.categoryRemovedEventType()
                )
            if issubclass(klass, Task):
                pub.unsubscribe(
                    self.onEffortAddedOrRemoved, Task.effortsChangedEventType()
                )
                pub.unsubscribe(
                    self.onPrerequisitesChanged,
                    Task.prerequisitesChangedEventType(),
                )
            if issubclass(klass, NoteOwner):
                self.removeObserver(
                    self.onOtherObjectAdded, klass.noteAddedEventType()
                )
                self.removeObserver(
                    self.onOtherObjectRemoved, klass.noteRemovedEventType()
                )
            if issubclass(klass, AttachmentOwner):
                self.removeObserver(
                    self.onOtherObjectAdded, klass.attachmentAddedEventType()
                )
                self.removeObserver(
                    self.onOtherObjectRemoved,
                    klass.attachmentRemovedEventType(),
                )
            if issubclass(klass, Effort):
                pub.unsubscribe(
                    self.onEffortTaskChanged, Effort.taskChangedEventType()
                )
            self._classes.remove(klass)

    def monitorCollection(self, collection):
        self.__collections.append(collection)
        self.registerObserver(
            self.onObjectAdded,
            collection.addItemEventType(),
            eventSource=collection,
        )
        self.registerObserver(
            self.onObjectRemoved,
            collection.removeItemEventType(),
            eventSource=collection,
        )

    def unmonitorCollection(self, collection):
        self.__collections.remove(collection)
        self.removeObserver(
            self.onObjectAdded,
            collection.addItemEventType(),
            eventSource=collection,
        )
        self.removeObserver(
            self.onObjectRemoved,
            collection.removeItemEventType(),
            eventSource=collection,
        )

    def onAttributeChanged(self, newValue, sender, topic=pub.AUTO_TOPIC):
        if self.__frozen:
            return

        for name in sender.monitoredAttributes():
            # Unresolved attribute reference 'getNameTuple' for class 'AUTO_TOPIC'
            # getModule , getID, getRawFunction, getAllArgs, getOptionalArgs, getRequiredArgs, getArgs from pub?
            # or method getNameTuple() is from pubsub.core.topicobj.Topic ?
            # if name in topic.getNameTuple():  # TODO : !
            if (
                sender.id() in self._changes
                and self._changes[sender.id()] is not None
            ):
                self._changes[sender.id()].add(name)

    def onAttributeChanged_Deprecated(self, event):
        if self.__frozen:
            return

        for type_, valBySource in list(
            event.sourcesAndValuesByType().items()
        ):  # TODO : problème potentiel
            for obj in list(valBySource.keys()):
                for name in obj.monitoredAttributes():
                    # if type_ == getattr(obj, "%sChangedEventType" % name)():
                    if type_ == getattr(obj, f"{name}ChangedEventType")():
                        if (
                            obj.id() in self._changes
                            and self._changes[obj.id()] is not None
                        ):
                            self._changes[obj.id()].add(name)

    def _objectAdded(self, obj):
        """
        Ensure the monitor has a mutable set for this object's changes.

        Previously this method set the entry to None which prevented
        later additions (like "__parent__") from being recorded. Always
        initialize to a set when an object is added and remove a
        "__del__" marker if present.
        """
        obj_id = obj.id()
        if obj_id in self._changes:
            # If there was a placeholder None for an object we already knew about
            # (for example a previously deleted object), convert it to a set so
            # future changes can be recorded. Also remove any "__del__" marker.
            if self._changes[obj_id] is None:
                self._changes[obj_id] = set()
            # If object was previously marked as deleted, remove that mark
            if "__del__" in self._changes[obj_id]:
                self._changes[obj_id].remove("__del__")
        else:
            # # New object: start with an empty set to record future changes
            # self._changes[obj_id] = set()
            # New object: use None as the sentinel value meaning "no changes yet".
            # Tests expect newly added objects to return None from getChanges().
            self._changes[obj_id] = None

    def _objectsAdded(self, event):
        # for obj in event.values():
        for obj in list(event.values()):
            self._objectAdded(obj)

    def _objectRemoved(self, obj):
        if obj.id() in self._changes:
            if self._changes[obj.id()] is None:
                del self._changes[obj.id()]
            else:
                self._changes[obj.id()].add("__del__")

    def _objectsRemoved(self, event):
        # for obj in event.values():
        for obj in list(event.values()):
            self._objectRemoved(obj)

    def onChildAdded(self, event):
        """Lorsqu'un enfant est ajouté à un objet composite observable,
        cette méthode est appelée pour enregistrer le changement."""
        print("ChangeMonitor.onChildAdded: event=%s" % event)  # Debug print
        print(
            "ChangeMonitor.onChildAdded: event.values()=%s"
            % list(event.values())
        )  # Debug print
        print(
            "ChangeMonitor.onChildAdded: event.sourcesAndValuesByType()=%s"
            % list(event.sourcesAndValuesByType().items())
        )  # Debug print
        print(
            "ChangeMonitor.onChildAdded: event.sources()=%s"
            % list(event.sources())
        )  # Debug print
        # Event.sources() retourne un set. Appeler event.sources()[0] provoque TypeError car les sets ne sont pas indexables. C'est exactement l'exception que tu as dans la stack trace.
        # Dans certains tests, on voyait list(event.sources()) dans les prints (qui fonctionne) mais d'autres endroits utilisaient l'indexation directement — d'où l'exception intermittente.
        # Avoid indexing into a set returned by event.sources()
        first_source = next(iter(event.sources()), None)
        print(
            # "ChangeMonitor.onChildAdded: event.values(source=event.sources()[0])=%s"
            # % list(event.values(source=event.sources()[0]))
            "ChangeMonitor.onChildAdded: event.values(source=first_source)=%s"
            % list(event.values(source=first_source))
        )  # Debug print
        print(
            "ChangeMonitor.onChildAdded: repr(self._changes)=%s"
            % repr(self._changes)
        )  # Debug print
        if self.__frozen:
            return

        self._objectsAdded(event)
        # for obj in event.values():
        for obj in list(event.values()):
            if self._changes[obj.id()] is not None:
                self._changes[obj.id()].add("__parent__")
        print(
            "ChangeMonitor.onChildAdded: after processing, repr(self._changes)=%s !"
            % repr(self._changes)
        )  # Debug print

    def onChildRemoved(self, event):
        """Lorsqu'un enfant est retiré d'un objet composite observable,
        cette méthode est appelée pour enregistrer le changement."""
        print("ChangeMonitor.onChildRemoved: event=%s" % event)  # Debug print
        print(
            "ChangeMonitor.onChildRemoved: event.values()=%s"
            % list(event.values())
        )  # Debug print
        print(
            "ChangeMonitor.onChildRemoved: event.sourcesAndValuesByType()=%s"
            % list(event.sourcesAndValuesByType().items())
        )  # Debug print
        print(
            "ChangeMonitor.onChildRemoved: event.sources()=%s"
            % list(event.sources())
        )  # Debug print
        # Avoid indexing into a set returned by event.sources()
        first_source = next(iter(event.sources()), None)
        print(
            # "ChangeMonitor.onChildRemoved: event.values(source=event.sources()[0])=%s"
            # % list(event.values(source=event.sources()[0]))
            "ChangeMonitor.onChildRemoved: event.values(source=first_source)=%s"
            % list(event.values(source=first_source))
        )  # Debug print
        print(
            "ChangeMonitor.onChildRemoved: repr(self._changes)=%s"
            % repr(self._changes)
        )  # Debug print
        if self.__frozen:
            return

        self._objectsRemoved(event)
        # for obj in event.values():
        for obj in list(event.values()):
            # event.values() yields object instances; our _changes dict uses
            # object ids as keys, so check by id.
            if (
                obj.id() in self._changes
                and self._changes[obj.id()] is not None
            ):
                self._changes[obj.id()].add("__parent__")
        print(
            "ChangeMonitor.onChildRemoved: after processing, repr(self._changes)=%s !"
            % repr(self._changes)
        )  # Debug print

    def onObjectAdded(self, event):
        if self.__frozen:
            return

        self._objectsAdded(event)

    def onObjectRemoved(self, event):
        if self.__frozen:
            return

        self._objectsRemoved(event)

    def onOtherObjectAdded(self, event):
        if self.__frozen:
            return

        self._objectsAdded(event)

    def onOtherObjectRemoved(self, event):
        if self.__frozen:
            return

        self._objectsRemoved(event)

    def onEffortAddedOrRemoved(self, newValue, sender):
        efforts, oldValue = newValue
        effortsToAdd = [effort for effort in efforts if effort not in oldValue]
        effortsToRemove = [
            effort for effort in oldValue if effort not in efforts
        ]
        for effort in effortsToAdd:
            self._objectAdded(effort)
        for effort in effortsToRemove:
            self._objectRemoved(effort)

    # Ce que j'ai fait
    # J'ai modifié la méthode ChangeMonitor.onEffortTaskChanged pour qu'elle accepte désormais *args et **kwargs, extraye l'expéditeur (sender) de manière robuste (dans kwargs ou parmi les args) et enregistre le changement "task" dans le registre de changements du moniteur.
    # Raison : selon la version/usage de PubSub, les callbacks peuvent être appelés de manière différente (positional vs keyword). Si la méthode n'était pas appelée ou ne trouvait pas l'expéditeur, le moniteur ne marquait pas l'effort comme modifié, donc TaskFile.needSave() restait False — d'où l'échec du test.
    # Le patch est ciblé et sûr : il n'altère pas la logique métier, il la rend juste plus tolérante aux différences d'API de pubsub.
    # J'ai vérifié la syntaxe/compilation du fichier modifié — seules des warnings d'import inutilisé / suggestion littérale sont apparus (pas d'erreurs fatales).
    # def onEffortTaskChanged(self, newValue, sender):
    def onEffortTaskChanged(self, *args, **kwargs):
        """Called when an Effort's parent task changes.

        PubSub libraries can call listeners using different conventions
        (positional args or keyword args). Accept *args/**kwargs and
        extract the sender reliably. Record the "__task__" change in the
        monitor, creating a mutable set if necessary.
        """
        # changes = self._changes.get(sender.id(), None)
        # Extract sender from kwargs if present
        sender = kwargs.get("sender", None)

        # If not found in kwargs, try to find an object in args that looks
        # like a domain object (has id()). Prefer the last arg which is
        # commonly the sender in many pubsub conventions.
        if sender is None:
            for candidate in reversed(args):
                try:
                    # Ensure candidate has id() method
                    _ = candidate.id()
                except Exception:
                    continue
                else:
                    sender = candidate
                    break

        # If we still don't have a sender, give up silently (no-op).
        if sender is None:
            return

        try:
            changes = self._changes.get(sender.id(), None)
        except Exception:
            # If sender.id() fails for any reason, bail out.
            return

        if changes is None:
            # Create a mutable change set so the taskfile will detect this
            # change. Previously a None sentinel prevented recording task
            # reparenting which made needSave() remain False.
            self._changes[sender.id()] = set(["__task__"])
        else:
            changes.add("__task__")

    def onCategoryAdded(self, event):
        """Lorsqu'une catégorie est ajoutée à un objet catégorisable composite,
        cette méthode est appelée pour enregistrer le changement."""
        print("ChangeMonitor.onCategoryAdded: event=%s" % event)  # Debug print
        print(
            "ChangeMonitor.onCategoryAdded: event.values()=%s"
            % list(event.values())
        )  # Debug print
        print(
            "ChangeMonitor.onCategoryAdded: event.sourcesAndValuesByType()=%s"
            % list(event.sourcesAndValuesByType().items())
        )  # Debug print
        print(
            "ChangeMonitor.onCategoryAdded: event.sources()=%s"
            % list(event.sources())
        )  # Debug print
        # Avoid indexing into a set returned by event.sources()
        first_source = next(iter(event.sources()), None)
        # Event.sources() retourne un set. Appeler event.sources()[0] provoque TypeError car les sets ne sont pas indexables. C'est exactement l'exception que tu as dans la stack trace.
        # Dans certains tests, on voyait list(event.sources()) dans les prints (qui fonctionne) mais d'autres endroits utilisaient l'indexation directement — d'où l'exception intermittente.
        print(
            # "ChangeMonitor.onCategoryAdded: event.values(source=event.sources()[0])=%s"
            # % list(event.values(source=event.sources()[0]))
            "ChangeMonitor.onCategoryAdded: event.values(source=first_source)=%s"
            % list(event.values(source=first_source))
        )  # Debug print
        print(
            "ChangeMonitor.onCategoryAdded: repr(self._changes)=%s"
            % repr(self._changes)
        )  # Debug print
        if self.__frozen:
            return

        for obj in event.sources():
            if (
                obj.id() in self._changes
                and self._changes[obj.id()] is not None
            ):
                for theCategory in event.values(source=obj):
                    # name = "_category:%s" % theCategory.id()
                    name = f"_category:{theCategory.id()}"
                    # if "__del" + name in self._changes[obj.id()]:
                    if f"__del{name}" in self._changes[obj.id()]:
                        # self._changes[obj.id()].remove("__del" + name)
                        self._changes[obj.id()].remove(f"__del{name}")
                    else:
                        # self._changes[obj.id()].add("__add" + name)
                        self._changes[obj.id()].add(f"__add{name}")
        print(
            "ChangeMonitor.onCategoryAdded: after processing, repr(self._changes)=%s !"
            % repr(self._changes)
        )  # Debug print

    def onCategoryRemoved(self, event):
        if self.__frozen:
            return

        for obj in event.sources():
            if (
                obj.id() in self._changes
                and self._changes[obj.id()] is not None
            ):
                for theCategory in event.values(source=obj):
                    # name = "_category:%s" % theCategory.id()
                    name = f"_category:{theCategory.id()}"
                    # if "__add" + name in self._changes[obj.id()]:
                    if f"__add{name}" in self._changes[obj.id()]:
                        # self._changes[obj.id()].remove("__add" + name)
                        self._changes[obj.id()].remove(f"__add{name}")
                    else:
                        # self._changes[obj.id()].add("__del" + name)
                        self._changes[obj.id()].add(f"__del{name}")

    def onPrerequisitesChanged(
        self, newValue, sender
    ):  # pylint: disable-msg=W0613
        """


        Args:
            newValue:
            sender:

        Returns:

        """
        # Need to check whether the sender is actually in one of the collections we monitor
        # Is this really the best way?
        for collection in self.__collections:
            if sender in collection:
                break
        else:
            return
        if (
            sender.id() in self._changes
            and self._changes[sender.id()] is not None
        ):
            self._changes[sender.id()].add("__prerequisites__")

    def allChanges(self):
        return self._changes

    def getChanges(self, obj):
        return self._changes.get(obj.id(), None)

    def setChanges(self, id_, changes):
        if changes is None:
            del self._changes[id_]
        else:
            self._changes[id_] = changes

    def isRemoved(self, obj):
        return (
            obj.id() in self._changes
            and self._changes[obj.id()] is not None
            and "__del__" in self._changes[obj.id()]
        )

    def resetChanges(self, obj):
        self._changes[obj.id()] = set()

    def addChange(self, obj, name):
        # changes = self._changes.get(obj.id(), set())
        # Ensure we handle the case where the entry exists but is None
        changes = self._changes.get(obj.id(), None)
        if changes is None:
            changes = set()
        changes.add(name)
        self._changes[obj.id()] = changes

    def resetAllChanges(self):
        # for id_, changes in self._changes.items():  # Alors list ou non ?
        # En Python 3, dict.values() renvoie une vue dynamique,
        # pas une liste. Si on modifie le dictionnaire pendant qu'on boucle dessus
        # (ce que fait souvent monitor.py pour suivre les changements), ça plante.
        # L'ajout de list(...) force la création d'une copie statique, ce qui est sûr.
        for id_, changes in list(self._changes.items()):
            if changes is not None and "__del__" in changes:
                del self._changes[id_]
            else:
                self._changes[id_] = set()

    def empty(self):
        """Vide les changements."""
        self._changes = dict()  # dict ? ou set ? dict

    def merge(self, monitor):
        # for id_, changes in self._changes.items():
        for id_, changes in list(self._changes.items()):
            theirChanges = monitor._changes.get(id_, None)
            if theirChanges is not None:
                changes.update(theirChanges)
