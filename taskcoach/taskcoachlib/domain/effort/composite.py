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

# from builtins import str
# from builtins import object
from taskcoachlib import render
from taskcoachlib.domain import date
from taskcoachlib.i18n import _  # à ne pas oublier !

# try:
#    from taskcoachlib.thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
# except ModuleNotFoundError:
from pubsub import pub
from . import base


class BaseCompositeEffort(base.BaseEffort):  # pylint: disable=W0223
    """
    Classe de base pour les efforts composites, qui sont des efforts qui se composent d'autres efforts.

    Cette classe fournit une implémentation de base pour les efforts composites,
    y compris les méthodes de calcul de la durée, des revenus et d'autres propriétés.
    """

    def parent(self):
        """
        Renvoie None, car les efforts composites n'ont pas de parent.
        """
        # Composite efforts don't have a parent.
        return None

    def _inPeriod(self, effort):
        """
        Vérifiez si un effort est dans le délai de cet effort composite.

        Args :
            effort : L'effort pour vérifier.

        Returns :
            Vrai si l'effort est dans le délai, faux autrement.
        """
        return self.getStart() <= effort.getStart() <= self.getStop()

    def mayContain(self, effort):
        """Renvoie si l'effort est contenu dans cet effort composite
        s'il existe.

        Renvoyez si l'effort serait contenu dans cet effort composite s'il existait.

        Args :
            effort : L'effort à vérifier.

        Returns :
            Vrai si l'effort était contenu, faux autrement.
        """
        return self._inPeriod(effort)

    def __contains__(self, effort):
        """
        Vérifiez si un effort est contenu dans cet effort composite.

        Args :
            effort : L'effort à vérifier.

        Returns :
            Vrai si l'effort est contenu, faux autrement.
        """
        return effort in self._getEfforts()

    def __getitem__(self, index):
        """
        Obtenir un effort à un index spécifique.

        Args :
            index : L'indice de l'effort pour obtenir.

        Returns :
            L'effort à l'indice spécifié.
        """
        return self._getEfforts()[index]

    def __len__(self):
        """
        Obtenir le nombre d'efforts dans cet effort composite.

        Returns :
            Le nombre d'efforts.
        """
        return len(self._getEfforts())

    def _getEfforts(self, recursive=False):
        """
        Obtenez la liste des efforts dans cet effort composite.

        Cette méthode doit être implémentée par sous-classes.

        Raises :
            NotImplementedError : Si la méthode n'est pas implémentée.
        """
        raise NotImplementedError

    def markDirty(self):
        """
        Marquez cet effort composite comme sale.

        Cette méthode ne fait rien, car les efforts composites ne peuvent pas être sales.
        """
        pass  # CompositeEfforts cannot be dirty

    def __doRound(self, duration, rounding, roundUp):  # MAY BE STATIC
        """
        Autour d'une durée à un nombre spécifique de secondes.

        Args :
            duration : La durée pour ronde.
            rounding : Le nombre de secondes à arrondir.
            roundUp : Que ce soit toujours rassemblé.

        Returns :
            La durée arrondie.
        """
        if rounding:
            return duration.round(seconds=rounding, alwaysUp=roundUp)
        return duration

    def duration(
        self, recursive=False, rounding=0, roundUp=False, consolidate=False
    ):
        """
        Calcule la durée totale de cet effort composite.

        Args :
            recursive : S'il faut inclure la durée des efforts des enfants.
            rounding : Le nombre de secondes à arrondir.
            roundUp : Que ce soit toujours rassemblé.
            consolidate : S'il faut consolider les efforts avant de calculer la durée.

        Returns :
            La durée totale de cet effort composite.
        """
        if consolidate:
            totalEffort = sum(
                (
                    self.__doRound(effort.duration(), 0, False)
                    for effort in self._getEfforts(recursive)
                ),
                date.TimeDelta(),
            )
            return totalEffort.round(seconds=rounding, alwaysUp=roundUp)
        return sum(
            (
                self.__doRound(effort.duration(), rounding, roundUp)
                for effort in self._getEfforts(recursive)
            ),
            date.TimeDelta(),
        )

    def isBeingTracked(self, recursive=False):  # pylint: disable=W0613
        """
        Vérifie si l'un des efforts de cet effort composite est suivi.

        Args :
            recursive : S'il faut inclure des efforts d'enfants.

        Returns :
            Vrai si l'un des efforts est suivi, faux autrement.
        """
        return any(effort.isBeingTracked() for effort in self._getEfforts())

    def durationDay(
        self, dayOffset, rounding=0, roundUp=False, consolidate=False
    ):
        """Retournez la durée de cet effort composite un jour spécifique.

        Args :
            dayOffset : Le nombre de jours à partir de la date de début.
            rounding : Le nombre de secondes à arrondir.
            roundUp : Que ce soit toujours rassemblé.
            consolidate : S'il faut consolider les efforts avant de calculer la durée.

        Returns :
            La durée de cet effort composite le jour spécifié.
        """
        startOfDay = self.getStart() + date.TimeDelta(days=dayOffset)
        endOfDay = self.getStart() + date.TimeDelta(days=dayOffset + 1)
        if consolidate:
            totalEffort = sum(
                (
                    self.__doRound(effort.duration(), 0, False)
                    for effort in self._getEfforts(recursive=False)
                    if startOfDay <= effort.getStart() <= endOfDay
                ),
                date.TimeDelta(),
            )
            return self.__doRound(totalEffort, rounding, roundUp)
        return sum(
            (
                self.__doRound(effort.duration(), rounding, roundUp)
                for effort in self._getEfforts(recursive=False)
                if startOfDay <= effort.getStart() <= endOfDay
            ),
            date.TimeDelta(),
        )

    def notifyObserversOfDurationOrEmpty(self):
        """
        Informer les observateurs que la durée de cet effort composite a changé.

        Si l'effort composite est vide, envoyez un message CompositeEmptyEventType.
        """
        if self._getEfforts():
            self.sendDurationChangedMessage()
        else:
            pub.sendMessage(self.compositeEmptyEventType(), sender=self)

    @classmethod
    def compositeEmptyEventType(class_):
        """
        Renvoyez le type d'événement pour quand un effort composite est vide.

        Returns :
            Le type d'événement.
        """
        return "pubsub.effort.composite.empty"

    @classmethod
    def modificationEventTypes(class_):
        """
        Renvoyez les types d'événements qui indiquent que cet effort composite a été modifié.

        Returns :
            Une liste vide, car les efforts composites ne peuvent pas être
            «sales» car leur contenu est déterminé par les efforts contenus.
        """
        # return []  # A composite effort cannot be 'dirty' since its contents
        return (
            list()
        )  # A composite effort cannot be 'dirty' since its contents
        # are determined by the contained efforts.

    def onTimeSpentChanged(self, newValue, sender):  # pylint: disable=W0613
        """
        Gérer l'événement lorsque le temps passé sur un effort change.

        Args :
            newValue : La nouvelle valeur du temps passé.
            sender : L'objet qui a envoyé l'événement.
        """
        if self._refreshCache():
            # Besoin de notifier si notre temps passé a réellement changé
            self.notifyObserversOfDurationOrEmpty()

    def onRevenueChanged(self, newValue, sender):  # pylint: disable=W0613
        """
        Gérer l'événement lorsque les revenus d'un effort changent.

        Args :
            newValue : La nouvelle valeur des revenus.
            sender : L'objet qui a envoyé l'événement.
        """
        self.sendRevenueChangedMessage()

    def revenue(self, recursive=False):
        """
        Calcule le revenu total de cet effort composite.

        Args :
            recursive (bool) : S'il faut inclure les revenus des efforts des enfants.

        Raises :
            NotImplementedError : Si la méthode n'est pas implémentée par une sous-classe.
        """
        raise NotImplementedError  # pragma: no cover

    def _invalidateCache(self):
        """Videz le cache pour qu'il soit rempli à la recherche.

        Invalider le cache de cet effort composite.

        Cette méthode doit être implémentée par les sous-classes.

        Raises :
            NotImplementedError : Si la méthode n'est pas implémentée.
        """
        raise NotImplementedError  # pragma: no cover

    def _refreshCache(self):
        """Actualisez le cache immédiatement et renvoyez si le cache a
        réellement changé.

        Actualiser le cache de cet effort composite.

        Cette méthode doit être implémentée par les sous-classes.

        Raises :
            NotImplementedError : Si la méthode n'est pas implémentée.
        """
        raise NotImplementedError  # pragma: no cover


class CompositeEffort(BaseCompositeEffort):
    """CompositeEffort est une liste paresseuse (mais met en cache) des efforts
    pour une tâche (et ses enfants) et dans un certain délai. La tâche, le début
    de la période de temps et la période de fin de temps doivent être fournis
    lorsqu'on initialise le composite effort et cela ne peut pas être modifié
    par la suite."""

    def __init__(self, task, start, stop):  # pylint: disable=W0621
        """
        Initialisez une nouvelle instance CompositeFort.

        Args:
            task: La tâche pour laquelle cet effort composite est pour.
            start (datetime): La date de début de la période.
            stop (datetime): La date de fin de la période.
        """
        # 1. Initialiser le cache avant tout appel parent/super()
        # Effort cache: {True: [efforts recursively], False: [efforts]}
        self.__effort_cache = dict()
        self.__hash_value = hash((task, start))
        # 2. Appeler super() après l'initialisation des attributs requis par __len__ / _getEfforts
        super().__init__(task, start, stop)

        """
        FIMXE! CompositeEffort ne dérive pas de base.Object
        patterns.Publisher().registerObserver(self.onAppearanceChanged,
        eventType=task.appearanceChangedEventType(), eventSource=task)
        """

    def __hash__(self):
        """
        Renvoyez la valeur de hachage de cet effort composite.

        Returns :
            int : La valeur de hachage.
        """
        return self.__hash_value

    def __repr__(self):
        """
        Renvoyez une représentation de string de cet effort composite.

        Returns :
            str : Une représentation de cet effort composite.
        """
        # return "CompositeEffort(task=%s, start=%s, stop=%s, efforts=%s)" % \
        #     (self.task(), self.getStart(), self.getStop(),
        #      str([e for e in self._getEfforts()]))
        return (
            f"CompositeEffort(task={self.task()},"
            f" start={self.getStart()}, stop={self.getStop()},"
            f" efforts={str([e for e in self._getEfforts()])})"
        )

    def addEffort(self, anEffort):
        """
        Ajoutez un effort à cet effort composite.

        Args :
            anEffort (BaseEffort) : L'effort pour ajouter.
        """
        assert self._inPeriod(anEffort)
        self.__effort_cache.setdefault(True, set()).add(anEffort)
        if anEffort.task() == self.task():
            self.__effort_cache.setdefault(False, set()).add(anEffort)

    def revenue(self, recursive=False):
        """
        Calculez le revenu total de cet effort composite.

        Args :
            recursive (bool) : S'il faut inclure les revenus des efforts des enfants.

        Returns :
            float : Le chiffre d'affaires total.
        """
        return sum(effort.revenue() for effort in self._getEfforts(recursive))

    def _invalidateCache(self):
        """
        Invalider le cache de cet effort composite.
        """
        self.__effort_cache = dict()

    def _refreshCache(self, recursive=None):
        """
        Actualiser le cache de cet effort composite.

        Args :
            recursive (bool, optional) : S'il faut actualiser le cache récursivement. None par défaut.

        Returns :
            bool : Vrai si le cache a été modifié, faux sinon.
        """
        recursive_values = (False, True) if recursive is None else (recursive,)
        previous_cache = self.__effort_cache.copy()
        cache_changed = False
        for recursive in recursive_values:
            cache = self.__effort_cache[recursive] = set(
                [
                    effort
                    for effort in self.task().efforts(recursive=recursive)
                    if self._inPeriod(effort)
                ]
            )
            if cache != previous_cache.get(recursive, set()):
                cache_changed = True
        return cache_changed

    def _getEfforts(self, recursive=True):  # pylint: disable=W0221
        """
        Obtenez la liste des efforts dans cet effort composite.

        Args :
            recursive (bool) : S'il faut inclure des efforts d'enfants.

        Returns :
            list : La liste des efforts.
        """
        if recursive not in self.__effort_cache:
            self._refreshCache(recursive=recursive)
        return list(self.__effort_cache[recursive])

    def mayContain(self, effort):
        """Renvoyez si l'effort serait contenu dans cet effort composite
        s'il existait.

        Args :
            effort (BaseEffort) : L'effort pour vérifier.

        Returns :
            bool : Vrai si l'effort était contenu, faux autrement.
        """
        return effort.task() == self.task() and super().mayContain(effort)

    def description(self):
        """
        Renvoyez la description de cet effort composite.

        Si tous les efforts ont la même description, renvoyez cette description.
        Sinon, renvoyez une liste de descriptions séparées de Newline.

        Returns :
            str : La description de cet effort composite.
        """
        if (
            len(
                set(effort.description() for effort in self._getEfforts(False))
            )
            == 1
        ):
            # if len(set(effort.getDescription() for effort in self._getEfforts(False))) == 1:
            return self._getEfforts(False)[0].description()
            # return self._getEfforts(False)[0].getDescription()
        # effortDescriptions = [effort.getDescription() for effort in
        effortDescriptions = [
            effort.description()
            for effort in sorted(
                self._getEfforts(False), key=lambda effort: effort.getStart()
            )
            if effort.description()
        ]
        # key=lambda effort: effort.getStart()) if effort.getDescription()]
        return "\n".join(effortDescriptions)

    def onAppearanceChanged(self, event):
        """
        Gérer l'événement lorsque l'apparence de la tâche change.

        Args :
            event : L'objet de l'événement.
        """
        return  # FIXME: CompositeEffort ne dérive pas de base.Object
        # patterns.Event(self.appearanceChangedEventType(), self, event.value()).send()


class CompositeEffortPerPeriod(BaseCompositeEffort):
    """
    CompositeEffortPerPeriod est un effort composite qui représente l'effort
    total pendant une période de temps spécifique.
    """

    class Total(object):
        """
        Une classe factice pour représenter l'effort total.
        """

        # pylint: disable=W0613
        def subject(self, *args, **kwargs):
            """
            Renvoie le sujet de cet effort total.

            Returns :
                str : Le sujet de cet effort total.
            """
            return _("Total")

        def foregroundColor(self, *args, **kwargs):  # may be static
            """
            Renvoyez la couleur de premier plan de cet effort total.

            Returns :
                None : Renvoie toujours None.
            """
            return None

        def backgroundColor(self, *args, **kwargs):  # may be static
            """
            Renvoyez la couleur d'arrière-plan de cet effort total.

            Returns :
                None : Renvoie toujours None.
            """
            return None

        def font(self, *args, **kwargs):  # may be static
            """
            Renvoyez la police de cet effort total.

            Returns :
                None : Renvoie toujours None.
            """
            return None

    total = Total()

    def __init__(self, start, stop, taskList, initialEffort=None):
        """
        Initialiser une nouvelle instance CompositeEffortPerPeriod.

        Args :
            start (datetime) : La date de début de la période.
            stop (datetime) : La date de fin de la période.
            taskList (list) : La liste des tâches à inclure dans cet effort composite.
            initialEffort (BaseEffort, optional) : Un effort initial facultatif à inclure. None par défaut.
        """
        # 1. Initialiser
        self.taskList = taskList
        # 2. Appeler super() après l'initialisation des attributs requis par __len__ / _getEfforts
        super().__init__(None, start, stop)
        if initialEffort:
            assert self._inPeriod(initialEffort)
            self.__effort_cache = [initialEffort]
        else:
            self._invalidateCache()

    def addEffort(self, anEffort):
        """
        Ajoutez un effort à cet effort composite.

        Args :
            anEffort (BaseEffort) : L'effort pour ajouter.
        """
        assert self._inPeriod(anEffort)
        if anEffort not in self.__effort_cache:
            self.__effort_cache.append(anEffort)

    @classmethod
    def task(cls):
        """
        Renvoyez la tâche pour laquelle cet effort composite est pour.

        Returns :
            Total : La tâche pour laquelle cet effort composite est pour.
        """
        return cls.total

    def isTotal(self):
        """
        Renvoyez si cet effort composite est un effort total.

        Returns :
            bool : Vrai si cet effort composite est un effort total, faux autrement.
        """
        return True

    def description(self, *args, **kwargs):  # pylint: disable=W0613
        """
        Renvoyez la description de cet effort composite.

        Returns :
            str : La description de cet effort composite.
        """
        return _("Total for %s") % render.dateTimePeriod(
            self.getStart(), self.getStop()
        )

    def revenue(self, recursive=False):  # pylint: disable=W0613
        """
        Calculer le revenu total de cet effort composite.

        Args :
            recursive (bool) : S'il faut inclure les revenus des efforts des enfants.

        Returns :
            float : Le chiffre d'affaires total.
        """
        return sum(effort.revenue() for effort in self._getEfforts())

    def categories(self, *args, **kwargs):
        """
        Renvoie les catégories de cet effort composite.

        Returns :
            list : Une liste vide.
        """
        return []

    def tasks(self):
        """Renvoyez les tâches qui ont des efforts pendant cette période.

        Returns :
            set : Un ensemble de tâches qui ont des efforts pendant cette période.
        """
        return set([effort.task() for effort in self._getEfforts()])

    def __repr__(self):
        """
        Renvoyez une représentation de chaîne de cet effort composite.

        Returns :
            str : Un texte de représentation de cet effort composite.
        """
        # return "CompositeEffortPerPeriod(start=%s, stop=%s, efforts=%s)" % \
        #     (self.getStart(), self.getStop(),
        #      str([e for e in self._getEfforts()]))
        return (
            f"CompositeEffortPerPeriod(start={self.getStart()},"
            f" stop={self.getStop()},"
            f" efforts={str([e for e in self._getEfforts()])})"
        )

    # Cache handling:

    def _getEfforts(self, recursive=False):  # pylint: disable=W0613,W0221
        """
        Obtenez la liste des efforts dans cet effort composite.

        Args :
            recursive (bool) : S'il faut inclure des efforts d'enfants.

        Returns :
            list : La liste des efforts.
        """
        if self.__effort_cache is None:
            self._refreshCache()
        return self.__effort_cache

    def _invalidateCache(self):
        """
        Invalider le cache de cet effort composite.
        """
        self.__effort_cache = None

    def _refreshCache(self):
        """
        Actualiser le cache de cet effort composite.

        Returns :
            bool : Vrai si le cache a été modifié, sinon faux.
        """
        previous_cache = (
            [] if self.__effort_cache is None else self.__effort_cache[:]
        )
        self.__effort_cache = []
        self.__add_task_effort_to_cache(self.taskList)
        return previous_cache != self.__effort_cache

    def __add_task_effort_to_cache(self, tasks):
        """Ajoutez l'effort des tâches au cache.

        Args :
            tasks (list) : La liste des tâches pour ajouter l'effort.
        """
        for task in tasks:
            effort_in_period = [
                effort for effort in task.efforts() if self._inPeriod(effort)
            ]
            self.__effort_cache.extend(effort_in_period)
