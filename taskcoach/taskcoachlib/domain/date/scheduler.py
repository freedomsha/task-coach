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

Ce module définit la classe `Scheduler` pour planifier des tâches à des dates et heures spécifiques dans Task Coach.

**Classes principales:**

* **ScheduledMethod(object):**
    - Encapsule une méthode à appeler via le planificateur.
    - Stocke la référence à la méthode et un identifiant unique.
    - Permet la comparaison d'objets `ScheduledMethod` pour vérifier l'égalité.
    - Fournit une méthode `__call__` pour exécuter la méthode encapsulée en vérifiant si l'objet parent existe toujours.

* **TwistedScheduler(object):**
    - Implémente l'interface du planificateur en utilisant Twisted pour la gestion des appels différés.
    - Stocke les tâches planifiées dans une liste triée par date et heure d'exécution.
    - Fournit des méthodes pour planifier des tâches à une date ou à intervalles réguliers, ainsi que pour annuler des tâches ou vérifier si une tâche est planifiée.

* **Scheduler(object, metaclass=patterns.Singleton):**
    - Singleton qui fournit une interface unique pour le planificateur.
    - Délégue les appels de planification et d'annulation au planificateur interne `TwistedScheduler`.
    - Permet de planifier des tâches à des dates et heures spécifiques, à intervalles réguliers, ainsi que d'annuler des tâches et de récupérer la liste des tâches planifiées.

**Remarques:**

- La classe `Scheduler` est un singleton, ce qui signifie qu'une seule instance peut exister dans l'application.
- L'utilisation de Twisted permet d'éviter les attentes bloquantes et de gérer les tâches de manière asynchrone.
- La méthode `schedule_interval` permet de planifier des tâches à intervalles réguliers en spécifiant le nombre de jours, minutes et secondes.

Explications supplémentaires:

    ScheduledMethod.__call__: Explique clairement que cette méthode sert à exécuter la tâche planifiée et vérifie la validité de l'objet associé.
    Méthodes de TwistedScheduler: Décrivent de manière concise le but de chaque méthode et les paramètres attendus.
    Méthodes de Scheduler: Expliquent comment planifier des tâches et fournissent des informations sur les types de retour.

Améliorations possibles:

    Détails supplémentaires: Vous pouvez ajouter des détails sur les exceptions qui pourraient être levées et sur le comportement du planificateur dans des situations d'erreur.
    Exemples: Des exemples d'utilisation peuvent rendre les docstrings plus claires et faciles à comprendre.
    Formatage: Assurez-vous que le formatage des docstrings est cohérent avec le reste de votre code.
"""
# from __future__ import division

# from past.utils import old_div
# from builtins import object
from taskcoachlib import patterns
from . import dateandtime, timedelta
# import logging
import weakref
import bisect


class ScheduledMethod(object):
    def __init__(self, method):
        self.__func = method.__func__
        self.__self = weakref.ref(method.__self__)
        self.__id = None

    def setId(self, id_):
        self.__id = id_

    def __eq__(self, other):
        return self.__func is other.__func and self.__self() is other.__self() and self.__id == other.__id

    def __hash__(self):
        return hash((self.__dict__["_ScheduledMethod__func"], self.__id))

    def __call__(self, *args, **kwargs):
        """Exécute la méthode planifiée.

        Vérifie si l'objet associé à la méthode existe toujours.
        Si c'est le cas, appelle la méthode avec les arguments fournis.
        Sinon, annule la tâche planifiée.

        :param *args: Arguments positionnels à passer à la méthode.
        :param **kwargs: Arguments nommés à passer à la méthode.
        """
        obj = self.__self()
        if obj is None:
            Scheduler().unschedule(self)
        else:
            self.__func(obj, *args, **kwargs)


class TwistedScheduler(object):
    """
    Une classe pour planifier des tâches à une date/heure spécifiée. Contrairement à apscheduler, this
    utilise Twisted au lieu du threading, afin d'éviter les attentes chargées.
    """
    def __init__(self):
        super().__init__()
        self.__jobs = []
        self.__nextCall = None
        self.__firing = False

    def __schedule(self, job, dateTime, interval):
        if self.__nextCall is not None:
            self.__nextCall.cancel()
            self.__nextCall = None
        index = bisect.bisect_right([v[0] for v in self.__jobs], dateTime)
        self.__jobs.insert(index, (dateTime, job, interval))
        # remplacé par:(mais ne fonctionne pas! à revoir)
        # bisect.insort_right(self.__jobs, (dateTime, job, interval))  # TypeError: '<' not supported between instances of 'ScheduledMethod' and 'ScheduledMethod'
        if not self.__firing:
            self.__fire()

    def scheduleDate(self, job, dateTime):
        """
        Planifie que le « travail » soit appelé à « dateTime ». Cela suppose que l'appelant soit le thread de boucle principal.

        Planifie une tâche à une date et heure spécifiques.

        :param job: La tâche à exécuter.
        :param dateTime: La date et l'heure auxquelles exécuter la tâche.
         """
        self.__schedule(job, dateTime, None)

    def scheduleInterval(self, job, interval, startDateTime=None):
        """Planifie une tâche à intervalles réguliers.

        :param job: La tâche à exécuter.
        :param interval: L'intervalle entre chaque exécution (objet timedelta).
        :param startDateTime: La date et l'heure de la première exécution.
        """
        self.__schedule(job, startDateTime or dateandtime.Now() + interval, interval)

    def unschedule(self, theJob):
        """Annule une tâche planifiée.

        :param theJob: La tâche à annuler.
        """
        for idx, (ts, job, interval) in enumerate(self.__jobs):
            if job == theJob:
                del self.__jobs[idx]
                break

    def isScheduled(self, theJob):
        for ts, job, interval in self.__jobs:
            if job == theJob:
                return True
        return False

    def shutdown(self):
        if self.__nextCall is not None:
            self.__nextCall.cancel()
            self.__nextCall = None
        self.__jobs = []

    def jobs(self):
        return [job for ts, job, interval in self.__jobs]

    def __fire(self):
        self.__firing = True
        try:
            while self.__jobs and self.__jobs[0][0] <= dateandtime.Now():
                ts, job, interval = self.__jobs.pop(0)
                try:
                    job()
                except Exception:  # not finally
                    # Hum.
                    import traceback
                    traceback.print_exc()
                if interval is not None:
                    self.__schedule(job, ts + interval, interval)
        finally:
            self.__firing = False
            if self.__jobs and self.__nextCall is None:
                dt = self.__jobs[0][0] - dateandtime.Now()
                # nextDuration = int(old_div((dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6), 10**3))
                nextDuration = round((dt.microseconds + (dt.seconds + dt.days * 24 * 3600) * 10**6) / 10**3)
                nextDuration = max(nextDuration, 1)
                nextDuration = min(nextDuration, 2**31 - 1)
                from twisted.internet import reactor
                self.__nextCall = reactor.callLater(1.0 * nextDuration // 1000, self.__callback)

    def __callback(self):
        self.__nextCall = None
        self.__fire()


# class Scheduler(metaclass=patterns.Singleton):
class Scheduler(object, metaclass=patterns.Singleton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__scheduler = TwistedScheduler()

    def shutdown(self):
        self.__scheduler.shutdown()

    def schedule(self, function, dateTime):
        """Planifie une fonction à une date et heure spécifiques.

        :param function: La fonction à exécuter.
        :param dateTime: La date et l'heure auxquelles exécuter la fonction.

        :return: Un objet `ScheduledMethod` représentant la tâche planifiée.
        """
        job = ScheduledMethod(function)
        self.__scheduler.scheduleDate(job, dateTime)
        return job

    def schedule_interval(self, function, days=0, minutes=0, seconds=0):
        """Planifie une fonction à intervalles réguliers.

        :param function: La fonction à exécuter.
        :param days: Nombre de jours entre chaque exécution.
        :param minutes: Nombre de minutes entre chaque exécution.
        :param seconds: Nombre de secondes entre chaque exécution.

        :return: Un objet `ScheduledMethod` représentant la tâche planifiée.
        """
        job = ScheduledMethod(function)
        if not self.__scheduler.isScheduled(job):
            startDate = dateandtime.Now().endOfDay() if days > 0 else None
            self.__scheduler.scheduleInterval(job, timedelta.TimeDelta(days=days, minutes=minutes, seconds=seconds),
                                              startDateTime=startDate)
            return job

    def unschedule(self, function):
        job = function if isinstance(function, ScheduledMethod) else ScheduledMethod(function)
        self.__scheduler.unschedule(job)

    def is_scheduled(self, function):
        return self.__scheduler.isScheduled(ScheduledMethod(function))

    def get_jobs(self):
        return self.__scheduler.jobs()
