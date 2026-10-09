"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
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

""" This module provides classes that implement refreshing strategies for
    viewers. """  # pylint: disable=W0105


# from builtins import object
import logging
from taskcoachlib import patterns
from taskcoachlib.domain import date

# try:
#     from taskcoachlib.thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub
from taskcoachlib.gui.newid import IdProvider
import wx

log = logging.getLogger(__name__)


class MinuteRefresher(object):
    """This class can be used by viewers to refresh themselves every minute
    to refresh attributes like time left. The user of this class is
    responsible for calling refresher.startClock() and stopClock().

    Cette classe peut être utilisée par les téléspectateurs pour s'actualiser chaque minute
    afin d'actualiser des attributs tels que le temps restant.
    L'utilisateur de cette classe est responsable de l'appel de Refresher.startClock() et stopClock().
    """

    def __init__(self, viewer):
        self.__viewer = viewer

    def startClock(self):
        date.Scheduler().schedule_interval(self.onEveryMinute, minutes=1)

    def stopClock(self):
        date.Scheduler().unschedule(self.onEveryMinute)

    def onEveryMinute(self):
        if self.__viewer:
            self.__viewer.refresh()
        else:
            self.stopClock()


class SecondRefresher(patterns.Observer, wx.EvtHandler):
    """Cette classe peut être utilisée par les téléspectateurs pour se rafraîchir chaque seconde
    chaque fois que des éléments (tâches, efforts) sont suivis.
    """

    # APScheduler seems to take a lot of resources in this setup, so we use a wx.Timer
    # Libération des identifiants

    def __init__(self, viewer, trackingChangedEventType):
        super().__init__()
        self.__viewer = viewer
        log.debug(f"Creating SecondRefresher for viewer {viewer}")
        self.__presentation = viewer.presentation()
        self.__trackedItems = set()
        # Utiliser IdProvider.get() pour obtenir un identifiant unique
        # TODO : essayer avec timer_id
        id_ = IdProvider.get()
        # id_ = wx.ID_ANY
        # self.__timer_id = IdProvider.get()
        self.__timer = wx.Timer(self, id_)
        # self.__timer = wx.Timer(self, self.__timer_id)
        # wx.EVT_TIMER(self, id_, self.onEverySecond)
        #  wxPyDeprecationWarning: Call to deprecated item __call__. Use :meth:`EvtHandler.Bind` instead.
        self.Bind(wx.EVT_TIMER, self.onEverySecond, id=id_)
        # self.Bind(wx.EVT_TIMER, self.onEverySecond, self.__timer)
        pub.subscribe(self.onTrackingChanged, trackingChangedEventType)
        self.registerObserver(
            self.onItemAdded,
            eventType=self.__presentation.addItemEventType(),
            eventSource=self.__presentation,
        )
        self.registerObserver(
            self.onItemRemoved,
            eventType=self.__presentation.removeItemEventType(),
            eventSource=self.__presentation,
        )
        self.setTrackedItems(self.trackedItems(self.__presentation))

    def removeInstance(self):
        # Lors de la destruction de l'objet,
        # s'assurer de libérer cet identifiant avec IdProvider.put().
        IdProvider.put(self.__timer.GetId())  # Libérer l'identifiant
        super().removeInstance()

    def onItemAdded(self, event):
        # Implémentez ici ce qui doit être fait lorsqu'un élément est ajouté
        self.addTrackedItems(self.trackedItems(list(event.values())))

    def onItemRemoved(self, event):
        # Implémentez ici ce qui doit être fait lorsqu'un élément est supprimé
        self.removeTrackedItems(self.trackedItems(list(event.values())))

    def onTrackingChanged(self, newValue, sender):
        # Implémentez ici ce qui doit être fait lorsque le suivi change
        if sender not in self.__presentation:
            self.setTrackedItems(self.trackedItems(self.__presentation))
            return
        if newValue:
            self.addTrackedItems([sender])
        else:
            self.removeTrackedItems([sender])
        self.refreshItems([sender])

    def onEverySecond(self, event=None):
        # def onEverySecond(self, event):
        # Implémentez ici ce qui doit être fait chaque seconde
        self.refreshItems(self.__trackedItems)

    def refreshItems(self, items):
        if self.__viewer:
            self.__viewer.refreshItems(*items)  # pylint: disable=W0142
        else:
            self.stopClock()

    def setTrackedItems(self, items):
        # Implémentez ici la logique pour définir les éléments suivis
        self.__trackedItems = set(items)
        self.startOrStopClock()

    def updatePresentation(self):
        log.debug("Updating presentation in SecondRefresher")
        self.__presentation = self.__viewer.presentation()
        self.setTrackedItems(self.trackedItems(self.__presentation))

    def addTrackedItems(self, items):
        if items:
            self.__trackedItems.update(items)
            self.startOrStopClock()

    def removeTrackedItems(self, items):
        if items:
            self.__trackedItems.difference_update(items)
            self.startOrStopClock()

    def startOrStopClock(self):
        if self.__trackedItems:
            self.startClock()
        else:
            self.stopClock()

    def startClock(self):
        self.__timer.Start(1000, False)
        # Démarrer le timer pour un intervalle de 1 seconde

    def stopClock(self):
        self.__timer.Stop()

    def isClockStarted(self):  # Unit tests
        return self.__timer.IsRunning()

    def currentlyTrackedItems(self):
        return list(self.__trackedItems)

    # def trackedItems(self, items):
    @staticmethod
    def trackedItems(items):
        # Implémentez ici la logique pour récupérer les éléments suivis
        return [item for item in items if item.isBeingTracked(recursive=True)]

    # def __del__(self):
    #     # Lors de la destruction de l'objet,
    #     # s'assurer de libérer cet identifiant avec IdProvider.put().
    #     if self.__timer.IsRunning():
    #         self.__timer.Stop()
    #     IdProvider.put(self.__timer_id)  # Libérer l'identifiant
