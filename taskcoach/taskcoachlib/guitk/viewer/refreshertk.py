# -*- coding: utf-8 -*-
"""
Ce module fournit des classes qui implémentent des stratégies de rafraîchissement
pour les visualisateurs.
Basé sur le fichier refresher.py original de Task Coach.
"""

# Le fichier refresher.py est responsable de la mise à jour périodique des vues, en particulier pour les éléments qui changent avec le temps, comme le temps restant sur une tâche. Dans la version wxPython originale, cela est géré par un wx.Timer.
#
# Dans cette conversion pour Tkinter, j'ai remplacé le wx.Timer par la méthode after() de Tkinter, qui permet de planifier l'exécution d'une fonction après un certain délai. Cela simule le comportement du minuteur et permet de mettre à jour l'interface utilisateur à intervalles réguliers sans bloquer l'application.
#
# Voici les principaux changements :
#
#     J'ai remplacé l'utilisation de wx par tkinter.
#
#     J'ai converti le MinuteRefresher pour utiliser la méthode after() de Tkinter.
#
#     J'ai inclus un exemple de classe MockViewer pour simuler le comportement d'une vue, ce qui vous permet de tester le Refresher directement.
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Set, Type
from taskcoachlib import patterns
from taskcoachlib.domain import date
from pubsub import pub
from taskcoachlib.guitk.newidtk import IdProvider
from taskcoachlib.i18n import _

# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# def _(text: str) -> str:
#     return text
#
#
# class patterns:
#     class Publisher:
#         def __init__(self):
#             self.observers: Dict[str, List[Callable]] = {}
#
#         def registerObserver(self, observer: Callable, eventType: str):
#             if eventType not in self.observers:
#                 self.observers[eventType] = []
#             self.observers[eventType].append(observer)
#
#         def removeObserver(self, observer: Callable):
#             for eventType in self.observers:
#                 if observer in self.observers[eventType]:
#                     self.observers[eventType].remove(observer)
#
#         def notify(self, eventType: str, *args: Any, **kwargs: Any):
#             if eventType in self.observers:
#                 for observer in self.observers[eventType]:
#                     observer(*args, **kwargs)
#
#
# class pubsub:
#     def __init__(self):
#         self.subscribers: Dict[str, List[Callable]] = {}
#
#     def subscribe(self, listener: Callable, topic: str):
#         if topic not in self.subscribers:
#             self.subscribers[topic] = []
#         self.subscribers[topic].append(listener)
#
#     def unsubscribe(self, listener: Callable, topic: str):
#         if topic in self.subscribers and listener in self.subscribers[topic]:
#             self.subscribers[topic].remove(listener)
#
#
# pub = pubsub()
#
#
# class IdProvider:
#     def __init__(self):
#         self.nextId = 0
#
#     def get(self) -> int:
#         self.nextId += 1
#         return self.nextId
#
#     def put(self, anId: int):
#         pass
#
#
# idProvider = IdProvider()


# --- CLASSE CONVERTIE ---
class MinuteRefresher:
    """
    Cette classe peut être utilisée par les visualisateurs pour se rafraîchir
    toutes les minutes pour mettre à jour des attributs comme le temps restant.
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


class SecondRefresher(patterns.Observer):
    """Cette classe peut être utilisée par les téléspectateurs pour se rafraîchir chaque seconde
    chaque fois que des éléments (tâches, efforts) sont suivis.
    """

    def __init__(
        self,
        viewer: Any,
        onRefresh: Optional[Callable] = None,
        interval: int = 1000,
    ):
        self.__viewer = viewer
        self.__id = IdProvider.get()
        self.__timerId: Optional[str] = None
        self.__interval = interval
        self.__trackedItems: Set[Any] = set()

        self.__onRefresh = (
            onRefresh if onRefresh is not None else viewer._refresh
        )

        pub.subscribe(self.onModified, "domain.event.item.modified")
        pub.subscribe(self.onDeleted, "domain.event.item.deleted")
        pub.subscribe(self.onAdded, "domain.event.item.added")

        self.updatePresentation()

    # def removeInstance(self):  # N'existe plus pour tkinter
    #     pass

    # def onItemAdded(self):  # remplacé par onAdded, voir addTrackedItems

    # def onItemRemoved(self):  # remplacé par

    # def onTrackingChanged(self):  # retiré pour tkinter

    def onModified(self, item: Any, **kwargs: Any):
        if item in self.__trackedItems:
            self.setTrackedItems(
                self.trackedItems(self.__viewer.presentation())
            )

    def onDeleted(self, item: Any):
        # try:
        #     if self.secondRefresher is not None:
        #         self.secondRefresher.stop()
        # except Exception:
        #     log.exception("Impossible d'arrêter secondRefresher")
        #
        # try:
        #     if self.minuteRefresher is not None:
        #         self.minuteRefresher.stop()
        # except Exception:
        #     log.exception("Impossible d'arrêter minuteRefresher")
        if item in self.__trackedItems:
            self.setTrackedItems(
                self.trackedItems(self.__viewer.presentation())
            )

    def onAdded(self, item: Any, parent: Any):
        if self.trackedItems([item]):
            self.setTrackedItems(
                self.trackedItems(self.__viewer.presentation())
            )

    # def onEverySecond(self, event=None):  # Retiré pour tkinter

    # def refreshItems(self, items):  # Retiré pour tkinter

    def setTrackedItems(self, items: List[Any]):
        self.__trackedItems = set(items)
        self.startOrStopClock()

    def updatePresentation(self):
        self.__presentation = self.__viewer.presentation()
        self.setTrackedItems(self.trackedItems(self.__presentation))

    def addTrackedItems(self, items: List[Any]):
        if items:
            self.__trackedItems.update(items)
            self.startOrStopClock()

    def removeTrackedItems(self, items: List[Any]):
        if items:
            self.__trackedItems.difference_update(items)
            self.startOrStopClock()

    def startOrStopClock(self):
        if self.__trackedItems:
            self.startClock()
        else:
            self.stopClock()

    def startClock(self):
        if self.__timerId is None:
            self.__timerId = self.__viewer.after(
                self.__interval, self._onTimer
            )

    def stopClock(self):
        if self.__timerId is not None:
            self.__viewer.after_cancel(self.__timerId)
            self.__timerId = None

    def _onTimer(self):
        # Nouvelle fonction
        if not self.__viewer.winfo_exists():
            self.stopClock()
            return

        self.__onRefresh()
        self.__timerId = self.__viewer.after(self.__interval, self._onTimer)

    def isClockStarted(self) -> bool:
        return self.__timerId is not None

    def currentlyTrackedItems(self) -> List[Any]:
        return list(self.__trackedItems)

    @staticmethod
    def trackedItems(items: List[Any]) -> List[Any]:
        return [
            item
            for item in items
            if hasattr(item, "isBeingTracked")
            and item.isBeingTracked(recursive=True)
        ]


# --- DÉMONSTRATION ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title(_("Minute Refresher Demo"))

    class MockTask:
        def __init__(self, name: str, tracked: bool):
            self.name = name
            self._is_tracked = tracked

        def isBeingTracked(self, recursive: bool = True) -> bool:
            return self._is_tracked

        def __repr__(self) -> str:
            return f"MockTask('{self.name}', tracked={self._is_tracked})"

    class MockViewer(tk.Frame):
        def __init__(self, parent: tk.Tk, tasks: List[MockTask]):
            super().__init__(parent)
            self._tasks = tasks
            self._label = tk.Label(
                self, text="Démarrage du rafraîchissement..."
            )
            self._label.pack(pady=20)
            self._refresh_count = 0

            # Initialisation du Refresher
            self.refresher = SecondRefresher(
                self, interval=1000
            )  # Intervalle d'1 seconde pour la démo

        def _refresh(self):
            self._refresh_count += 1
            self._label.config(
                text=f"Rafraîchissement #{self._refresh_count}\nObjets suivis: {len(self.refresher.currentlyTrackedItems())}"
            )
            print(
                f"Rafraîchissement #{self._refresh_count}. Objets suivis: {self.refresher.currentlyTrackedItems()}"
            )

        def presentation(self) -> List[MockTask]:
            return self._tasks

    tasks_to_track = [
        MockTask("Tâche A", True),
        MockTask("Tâche B", False),
        MockTask("Tâche C", True),
    ]

    viewer = MockViewer(root, tasks_to_track)
    viewer.pack(fill="both", expand=True)

    root.mainloop()
