"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
from taskcoachlib.domain import date, base
from taskcoachlib.domain import task as domain_task
from taskcoachlib.domain.base.attribute import Attribute

#    try:
#        from taskcoachlib.thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
#    except ModuleNotFoundError:
from pubsub import pub
from . import base as baseeffort
import functools
import weakref
import logging

log = logging.getLogger(__name__)


@functools.total_ordering
class Effort(baseeffort.BaseEffort, base.object.Object):
    def __init__(
        self,
        task=None,
        start=None,
        stop=None,
        entryMode="standard",
        *args,
        **kwargs,
    ):
        print("DEBUG Effort.__init__ : task =", task, type(task))
        super().__init__(
            task, start or date.DateTime.now(), stop, *args, **kwargs
        )
        self.__entryMode = Attribute(entryMode, self, self._onEntryModeChanged)
        # __duration est la référence, la source de vérité ! Pas __cachedDuration !
        self.__duration = Attribute(
            self._computeDuration(), self, self._onDurationChanged
        )
        # Utilisation de __cachedDuration comme un état de synchronisation implicite (pas seulement comme un cache de performance).
        self.__updateDurationCache()  # Obsolète puisque Attribute joue déjà ce rôle.
        print(vars(self))

    def __getattribute__(self, name):
        """Remplacer pour empêcher les méthodes d'être masquées par les attributs d'instance.

        Lors des opérations de copier/coller, les kwargs de __getcopystate__ peuvent finir
        en tant qu'attributs d'instance qui masquent les méthodes de classe. Ce remplacement
        garantit que les recherches de méthode trouvent toujours la méthode de classe, et non les attributs d'instance.
        """
        # Methods that might get shadowed - check directly to avoid recursion
        _protected = (
            "id",
            "task",
            "subject",
            "description",
            "font",
            "foregroundColor",
            "backgroundColor",
            "icon",
            "selectedIcon",
            "ordering",
            "creationDateTime",
            "modificationDateTime",
        )
        if name in _protected:
            # Get the method from the class, not the instance
            for cls in type(self).__mro__:
                if name in cls.__dict__:
                    method = cls.__dict__[name]
                    if callable(method):
                        # Return bound method
                        return method.__get__(self, type(self))
                    break
        return object.__getattribute__(self, name)

    # def setTask(self, task):
    def setTask(self, task, event=None):
        """
        Setter - normalise et délègue à l'attribut.
        Remarque : nous ne vérifions pas si la nouvelle tâche est la même que la tâche actuelle
            car nous voulons lui permettre de la définir sur la même tâche
            (par exemple lors de l'initialisation) sans ignorer la logique
            qui met à jour la liste des efforts de la tâche et envoie des notifications.
            La liste des efforts de la tâche doit être mise à jour
            pour inclure cet effort, et les observateurs doivent être informés
            du changement de tâche même s'il s'agit de la même tâche,
            pour garantir la cohérence et la bonne gestion des événements.
            Ceci est particulièrement important lors de l'initialisation
            lorsque la tâche est définie pour la première fois.
        """
        # Debug tracing to determine why setTask may not send messages in tests
        try:
            print(
                f"Effort.setTask called: self._task={getattr(self, '_task', None)}, current task()={self.task()}, arg task={task}"
            )
        except Exception:
            pass
        if self._task is None:
            # Nous n'avons pas encore été complètement initialisés, alors autorisez le paramétrage de la tâche,
            # sans en avertir les observateurs. De plus, n'appelez pas addEffort()
            # sur la nouvelle tâche, car nous supposons que setTask a été invoqué par la
            # nouvelle tâche elle-même.
            self._task = None if task is None else weakref.ref(task)
            try:
                print(
                    "Effort.setTask: early return because self._task was None; set weakref and returned"
                )
            except Exception:
                pass
            return
            # if task in (self.task(), None):
            # Only ignore when explicitly setting to None or when the
            # exact same object instance is supplied. Using `in (self.task(), None)`
            # relies on equality and can give false positives if __eq__ for
            # Task compares by id or other semantics. Use identity test so
            # that a different Task instance that happens to be equal still
            # triggers the reassignment and notifications.
        if task is None or task is self.task():
            # command.PasteCommand may try to set the parent to None
            try:
                print(
                    "Effort.setTask: early return because task is same as current or None"
                )
            except Exception:
                pass
            return

        event = (
            patterns.Event()
        )  # Change monitor needs one event to detect task change
        # self._task().removeEffort(self)
        self.task().removeEffort(self)
        self._task = weakref.ref(task)
        # self._task().addEffort(self)
        self.task().addEffort(self)
        event.send()
        # Debug prints pour s'assurer que le message est bien envoyé pendant les tests
        print(
            f"Effort.setTask : Envoi de l'événement de changement de tâche pour l'effort {self}, nouvelle tâche={task}"
        )
        pub.sendMessage(
            self.taskChangedEventType(), newValue=task, sender=self
        )  # La migration vers pubsub 4.0 nécessite de passer les arguments en positionnels ou de les encapsuler dans un Event, car pubsub 4.0 ne supporte plus les arguments nommés arbitraires.
        # pub.sendMessage(
        #     self.taskChangedEventType(),
        # )  # S'assurer que les observateurs reçoivent bien la notification, même sans args
        # Use positional args to avoid topic arg-spec mismatches in some
        # pubsub configurations (some listeners register different argnames).
        # pub.sendMessage(self.taskChangedEventType(), task, self)
        # Create an Event object with the necessary data
        # change_event = patterns.Event(
        #     newValue=task, sender=self
        # )  # N'existent pas dans Event, mais on peut les ajouter dynamiquement
        # pub.sendMessage(self.taskChangedEventType(), event=change_event)

        print(
            f"Effort.setTask : Événement envoyé pour {self.taskChangedEventType()}"
        )

        # 1. Mise à jour du cache (important pour la durée)
        # self.__updateDurationCache()  # Probablement inutile.
        # 2. NOTIFICATION : C'est cette ligne qui réveille TaskFile !
        # 2. NOTIFICATION : C'est cette ligne qui réveille TaskFile!
        # On ne passe pas d'arguments complexes (newValue, sender) pour éviter
        # les conflits de signature avec le setModified de TaskFile.

        # # vérifie ceci : Si cela fonctionne vérifier les lignes précédentes !
        # if task != self._task:
        #     self._task = task
        #     pub.sendMessage(
        #         self.taskChangedEventType(), newValue=task, sender=self
        #     )

    setParent = setTask  # FIXME: should we create a common superclass for Effort and Task?

    @classmethod
    def monitoredAttributes(class_):
        return base.Object.monitoredAttributes() + ["start", "stop"]

    def task(self):
        """Return the actual Task object or None.

        Internally self._task is stored as a weakref.ReferenceType (or None),
        so dereference it before returning. This prevents callers from
        accidentally getting a weakref object and calling methods on it.
        """
        # return self._task
        return None if self._task is None else self._task()

    # TODO : Note: task() and id() are now handled by __getattribute__ to prevent
    # attribute shadowing issues during copy/paste operations.

    @classmethod
    def taskChangedEventType(class_):
        """The event type for changes to the task of an effort.

        Observers can subscribe to this event type to be notified
        when the task associated with an effort changes.

        Retourne le topic PubSub utilisé
        lorsque la tâche associée à un effort change.

        Returns:
            str: Topic PubSub.
        """
        return "pubsub.effort.task"

    def __str__(self):
        # task = self._task() if self._task else None
        # return "Effort(%s, %s, %s)" % (self.task(), self._start, self._stop)
        # Utilisation systématique de getStart()/getStop() au lieu d'accéder directement à _start et _stop (qui sont maintenant des objets Attribute).
        log.debug(
            f"Effort.__str__ : retourne Effort({self.task()}, {self.getStart()}, {self.getStop()})."
        )
        return "Effort(%s, %s, %s)" % (
            self.task(),
            self.getStart(),
            self.getStop(),
        )

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, Effort):
            return NotImplemented
        # Access _Object__id directly to avoid potential attribute shadowing
        return self._Object__id == other._Object__id

    def __lt__(self, other):
        if not isinstance(other, Effort):
            return NotImplemented
        # Compare by start time first, then stop time, then id for total ordering
        self_stop = (
            # self._stop.get()
            self.getStop()
            # if self._stop.get() is not None
            if self.getStop() is not None
            else date.DateTime.max
        )
        other_stop = (
            # other._stop.get()
            other.getStop()
            # if other._stop.get() is not None
            if other.getStop() is not None
            else date.DateTime.max
        )
        # return (self._start.get(), self_stop, self._Object__id) < (
        return (self.getStart(), self_stop, self._Object__id) < (
            # other._start.get(),
            other.getStart(),
            other_stop,
            other._Object__id,
        )

    def __hash__(self):
        return hash(self._Object__id)

    def __getstate__(self):
        state = super().__getstate__()
        # task = self._task() if self._task else None
        # state.update(dict(task=self.task(), start=self._start, stop=self._stop))
        state.update(
            dict(
                # task=task,
                task=self.task(),
                # start=self._start.get(),
                start=self.getStart(),
                # stop=self._stop.get(),
                stop=self.getStop(),
                entryMode=self.__entryMode.get(),
                duration=self.__duration.get(),
            )
        )
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        super().__setstate__(state, event=event)
        # self.setTask(state["task"])
        self.setTask(state["task"], event=event)
        # self.setStart(state["start"])
        # self.setStop(state["stop"])
        self.setStart(state["start"], event=event)
        self.setStop(state["stop"], event=event)
        self.setEntryMode(state.get("entryMode", "standard"), event=event)
        self.setDuration(state.get("duration"), event=event)

    def __getcopystate__(self):
        state = super().__getcopystate__()
        # task = self._task() if self._task else None
        # state.update(dict(task=self.task(), start=self._start, stop=self._stop))
        state.update(
            dict(
                task=self.task(),
                # start=self._start.get(),
                start=self.getStart(),
                # stop=self._stop.get(),
                stop=self.getStop(),
                entryMode=self.__entryMode.get(),
                duration=self.__duration.get(),
            )
        )
        print(
            "DEBUG Effort.__getcopystate__ :", self.task(), type(self.task())
        )
        return state

    def _computeDuration(self):
        # stop = self._stop.get()
        stop = self.getStop()
        # return stop - self._start.get() if stop else None
        return stop - self.getStart() if stop else None
        # return stop - self.getStart() if stop else now() - self.getStart()

    def _onDurationChanged(self, event):
        """
        Réagir au changement de durée.

        Args:
            event:
        """
        self.sendDurationChangedMessage()
        # task = self._task() if self._task else None
        task = self.task()
        if task and task.hourlyFee():
            self.sendRevenueChangedMessage()

    def sendDurationChangedMessage(self):
        """Override to send stored value, not live-computed value.

        BaseEffort.sendDurationChangedMessage sends self.duration() which
        returns now()-start when duration is None (tracking). We send
        self.__duration.get() (the stored value) to match how start/stop
        send their stored values via getters.
        """
        # # self.__duration = self.__cachedDuration  # !
        # stored = self.__duration.get()
        # Mais il faut gérer la cas où l'effort est encore actif !
        from pubsub import pub

        pub.sendMessage(
            self.durationChangedEventType(),
            # newValue=stored,
            newValue=self.duration(),
            sender=self,
        )

    def timeSpent(self, now=date.DateTime.now):
        """Always compute elapsed time from start/stop."""
        # stop = self._stop.get()
        stop = self.getStop()
        if stop is not None:
            # return stop - self._start.get()
            return stop - self.getStart()
        # return now() - self._start.get()
        return now() - self.getStart()

    def duration(self, now=date.DateTime.now):
        """Retourne la durée actuelle de l'effort.

        Un effort arrêté retourne la durée stockée.
        Un effort encore en cours retourne le temps écoulé
        depuis son démarrage.

        Args:
            now: Fonction retournant l'heure actuelle.

        Returns:
            date.TimeDelta: Durée de l'effort.
        """
        # return (
        #     # now() - self._start
        #     now() - self.getStart()
        #     # if self.__cachedDuration is None
        #     if self.getStop() is None
        #     # else self.__cachedDuration
        #     else self.__duration.get()
        # )
        if self.getStop() is None:
            return now() - self.getStart()

        return self.__duration.get()
        # __duration est la référence

    def setDuration(self, newDuration, event=None):
        """Setter — normalizes and delegates to Attribute."""
        if newDuration is not None and newDuration == date.TimeDelta():
            newDuration = None
        self.__duration.set(newDuration, event=event)

    # def setStart(self, startDateTime):
    def setStart(self, startDateTime, event=None):
        # if startDateTime == self._start:
        if startDateTime == self.getStart():
            return
        # self._start = startDateTime
        self._start.set(
            startDateTime, event=event
        )  # Correction ici : utiliser .set()
        # 1. Mise à jour du cache (important pour la durée)
        # self.__updateDurationCache()  # Déjà fait dans _start.set()
        # 2. NOTIFICATION : C'est cette ligne qui réveille TaskFile !
        # On ne passe pas d'arguments complexes (newValue, sender) pour éviter
        # les conflits de signature avec le setModified de TaskFile.
        # # pub.sendMessage(self.startChangedEventType())
        # pub.sendMessage(
        #     self.startChangedEventType(), newValue=startDateTime, sender=self
        # )  # _onStartChanged() s'en occupe de gérer la notification.

        # self.task().sendTimeSpentChangedMessage()
        # self.sendDurationChangedMessage()
        # if self.task().hourlyFee():
        #     self.sendRevenueChangedMessage()
        # 3. Notification à la tâche parente (pour recalculer le temps total)
        if self.task():
            self.task().sendTimeSpentChangedMessage()
        # # self._start.set(startDateTime, event=event)

    def _onStartChanged(self, event):
        """Met à jour la durée après changement du début."""
        self.__duration.set(self._computeDuration())
        self.__updateDurationCache()
        pub.sendMessage(
            self.startChangedEventType(), newValue=self.getStart(), sender=self
        )
        # task = self._task() if self._task else None
        task = self.task()
        if task:
            task.sendTimeSpentChangedMessage()
            # if task.hourlyFee():
            #     self.sendRevenueChangedMessage()  # _onDurationChanged() s'en charge !
        # self.sendDurationChangedMessage()

    @classmethod
    def startChangedEventType(class_):
        """The event type for changes to the start of an effort.

        Observers can subscribe to this event type to be notified
        when the start time of an effort changes.

        Returns:
            str: The PubSub topic for start time changes of an effort.
        """
        return "pubsub.effort.start"

    # def setStop(self, newStop=None):
    def setStop(self, newStop=None, event=None):
        if newStop is None:
            newStop = date.DateTime.now()
        # elif newStop == date.DateTime.max:
        elif newStop == date.DateTime.max or newStop == date.DateTime():
            newStop = None
        # if newStop == self._stop:
        if newStop == self.getStop():
            return
        # previousStop = self._stop
        # self._previousStop = self._stop.get()
        self._previousStop = self.getStop()
        # self._stop = newStop
        self._stop.set(newStop, event=event)
        # self.__updateDurationCache()  # Déjà fait dans _stop.set()
        # if newStop is None:
        #     pub.sendMessage(
        #         self.trackingChangedEventType(), newValue=True, sender=self
        #     )
        #     self.task().sendTrackingChangedMessage(tracking=True)
        # # elif previousStop is None:
        # elif self._previousStop is None:
        #     pub.sendMessage(
        #         self.trackingChangedEventType(), newValue=False, sender=self
        #     )
        #     self.task().sendTrackingChangedMessage(tracking=False)
        # self.task().sendTimeSpentChangedMessage()
        # On décommente aussi ici
        # # pub.sendMessage(self.stopChangedEventType())
        # # pub.sendMessage(
        # #     self.stopChangedEventType(), newValue=self._stop, sender=self
        # # )
        # pub.sendMessage(
        #     self.stopChangedEventType(), newValue=newStop, sender=self
        # )  # _onStopChanged() s'en occupe déjà !
        # self.sendDurationChangedMessage()
        # if self.task().hourlyFee():
        #     self.sendRevenueChangedMessage()
        if self.task():
            self.task().sendTimeSpentChangedMessage()

    def _onStopChanged(self, event):
        """Met à jour la durée après changement de la fin."""
        self.__duration.set(self._computeDuration())
        self.__updateDurationCache()

        previousStop = getattr(self, "_previousStop", None)
        # newStop = self._stop.get()
        newStop = self.getStop()
        # task = self._task() if self._task else None
        task = self.task()
        if newStop is None:
            pub.sendMessage(
                self.trackingChangedEventType(), newValue=True, sender=self
            )
            if task:
                task.sendTrackingChangedMessage(tracking=True)
        elif previousStop is None:
            pub.sendMessage(
                self.trackingChangedEventType(), newValue=False, sender=self
            )
            if task:
                task.sendTrackingChangedMessage(tracking=False)
        if task:
            task.sendTimeSpentChangedMessage()
            # if task.hourlyFee():
            #     self.sendRevenueChangedMessage()  # _onDurationChanged() s'en charge.
        pub.sendMessage(
            self.stopChangedEventType(), newValue=newStop, sender=self
        )
        # self.sendDurationChangedMessage()

    @classmethod
    def stopChangedEventType(class_):
        """
        The event type for changes to the stop of an effort.

        Observers can subscribe to this event type to be notified
        when the stop time of an effort changes.

        Returns:
            str: The PubSub topic for stop time changes of an effort.
        """
        return "pubsub.effort.stop"

    def __updateDurationCache(self):
        # self.__cachedDuration = (
        #     self._stop - self._start if self._stop else None
        # )
        self.__cachedDuration = (
            # self._stop.get() - self._start.get() if self._stop else None
            self.getStop() - self.getStart()
            if self.getStop()
            else None
        )

    def isBeingTracked(self, recursive=False):  # pylint: disable=W0613
        # return self._stop is None
        return self.getStop() is None

    def revenue(self, recursive=False):
        return self.duration().hours() * self.task().hourlyFee()

    @staticmethod
    def periodSortFunction(**kwargs):
        # Sort by start of effort first, then make sure the Total entry comes
        # first and finally sort by task subject:
        return lambda effort: (
            effort.getStart(),
            effort.isTotal(),
            effort.task().subject(recursive=True),
        )

    @classmethod
    def periodSortEventTypes(class_):
        """The event types that influence the effort sort order."""
        return (
            class_.startChangedEventType(),
            class_.taskChangedEventType(),
            domain_task.Task.subjectChangedEventType(),
        )

    @classmethod
    def modificationEventTypes(class_):
        eventTypes = super().modificationEventTypes()
        return eventTypes + [
            class_.taskChangedEventType(),
            class_.startChangedEventType(),
            class_.stopChangedEventType(),
            class_.entryModeChangedEventType(),
        ]

    # Entry mode (standard, retroactive, or implicit)

    def entryMode(self):
        """Return the entry mode: 'standard', 'retroactive', or 'implicit'."""
        return self.__entryMode.get()

    def setEntryMode(self, mode, event=None):
        """Setter — normalizes and delegates to Attribute."""
        self.__entryMode.set(mode, event=event)

    def _onEntryModeChanged(self, event):
        pub.sendMessage(
            self.entryModeChangedEventType(),
            newValue=self.entryMode(),
            sender=self,
        )

    @classmethod
    def entryModeChangedEventType(class_):
        """The event type for changes to the entry mode."""
        return "pubsub.effort.entryMode"
