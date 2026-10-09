"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

This is a Tkinter conversion of the original wxPython idlecontroller.py.

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

# J'ai converti le fichier idlecontroller.py de wxPython à Tkinter.
# Ce code remplace les éléments d'interface utilisateur de wxPython
# par leurs équivalents Tkinter, tout en maintenant la logique originale.
#
# Le code inclut des classes et des fonctions pour gérer les notifications d'inactivité,
# y compris une fenêtre de notification et le contrôleur principal.
# J'ai utilisé tkinter.Toplevel pour la fenêtre de notification et
# j'ai remplacé les gestionnaires d'événements wx par des méthodes de liaison Tkinter (.bind).

# J'ai converti le code pour qu'il utilise Tkinter.
# J'ai remplacé wx.StaticText par tk.Label et wx.Button par tk.Button.
# J'ai également ajusté la logique des boutons pour qu'elle corresponde à la syntaxe Tkinter.
#
# Veuillez noter que le code NotificationCenter().NotifyFrame(frm) a été commenté
# et remplacé par une version simplifiée,
# car je n'ai pas les détails de son implémentation dans le contexte Tkinter.
# TODO : Il se peut que vous deviez ajuster cela en fonction de votre structure de code pour les notifications.

# Changements clés :
#
# IdleController n’hérite désormais que de l’Observer.
# Au lieu d’hériter d’IdleNotifier, une instance de IdleNotifier est créée en tant que membre d’IdleController ( self._idle_notifier = idletk. IdleNotifier(root=mainWindow, min_idle_time=min_idle_time)).
# Les méthodes poweroff, poweron, pause et resume appellent désormais les méthodes correspondantes sur l’instance self._idle_notifier.

import logging
from taskcoachlib.command import (
    NewEffortCommand,
    EditEffortStopDateTimeCommand,
)
from taskcoachlib.domain import effort, date
from taskcoachlib.i18n import _

# from taskcoachlib.notify import NotificationFrameBase, NotificationCenter  # En cours de conversion
from taskcoachlib.notify import notifier_universaltk
from taskcoachlib.patterns import Observer
from taskcoachlib.powermgt import idletk
from pubsub import pub
from taskcoachlib import render
import tkinter as tk
from tkinter import messagebox

log = logging.getLogger(__name__)


# class WakeFromIdleFrame(NotificationFrameBase):
class WakeFromIdleFrame(tk.Toplevel):
    """
    Fenêtre de notification affichée lorsque le système est réveillé de l'inactivité.
    Remplace la classe WakeFromIdleFrame basée sur wx.
    """

    def __init__(self, parent, idleTime, effort, displayedEfforts, title):
        super().__init__(parent)
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.DoClose)

        self._idleTime = idleTime
        self._effort = effort
        self._displayed = displayedEfforts
        self._lastActivity = 0

        self.AddInnerContent()

    def AddInnerContent(self):
        """
        Crée les widgets à l'intérieur de la fenêtre.
        """
        idleTimeFormatted = render.dateTime(self._idleTime)

        # Labels
        tk.Label(
            self,
            text=(
                _(
                    "No user input since %s. The following task was\nbeing tracked:"
                )
                % idleTimeFormatted
            ),
        ).pack(pady=5, padx=5)
        tk.Label(
            self,
            text=self._effort.task().subject(),
            font=("Arial", 10, "bold"),
        ).pack(pady=5, padx=5)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        btn_nothing = tk.Button(
            btn_frame, text=_("Do nothing"), command=self.DoNothing
        )
        btn_nothing.pack(side=tk.LEFT, padx=5)

        btn_stop_at = tk.Button(
            btn_frame,
            text=_("Stop it at %s") % idleTimeFormatted,
            command=self.DoStopAt,
        )
        btn_stop_at.pack(side=tk.LEFT, padx=5)

        btn_stop_resume = tk.Button(
            btn_frame,
            text=_("Stop it at %s and resume Now") % idleTimeFormatted,
            command=self.DoStopResume,
        )
        btn_stop_resume.pack(side=tk.LEFT, padx=5)

        # Center the window on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def DoNothing(self):
        """
        Action pour le bouton "Do nothing".
        """
        if self._effort in self._displayed:
            self._displayed.remove(self._effort)
        self.DoClose()

    def DoStopAt(self):
        """
        Action pour le bouton "Stop it at...".
        """
        if self._effort in self._displayed:
            self._displayed.remove(self._effort)
        EditEffortStopDateTimeCommand(
            newValue=self._idleTime, items=[self._effort]
        ).do()
        self.DoClose()

    def DoStopResume(self):
        """
        Action pour le bouton "Stop it at... and resume Now".
        """
        if self._effort in self._displayed:
            self._displayed.remove(self._effort)
        EditEffortStopDateTimeCommand(
            newValue=self._idleTime, items=[self._effort]
        ).do()
        NewEffortCommand(items=[self._effort.task()]).do()
        self.DoClose()

    def DoClose(self):
        """
        Ferme la fenêtre.
        """
        self.destroy()


# class IdleController(Observer, IdleNotifier):
class IdleController(Observer):
    """
    Contrôleur pour l'inactivité du système.
    """

    def __init__(self, mainWindow, settings, effortList):
        self._mainWindow = mainWindow
        self._settings = settings
        self._effortList = effortList
        self._displayed = set()

        # super().__init__(self._mainWindow)
        # super().__init__(mainWindow)
        min_idle_time = settings.getint("feature", "minidletime") * 60
        # IdleNotifier.__init__(self, root=mainWindow, min_idle_time=min_idle_time)
        self._idle_notifier = idletk.IdleNotifier(
            root=mainWindow, min_idle_time=min_idle_time
        )
        # Observer.__init__(self)
        super().__init__()

        self.__tracker = effort.EffortListTracker(self._effortList)
        self.__tracker.subscribe(self.__onTrackedChanged, "effortlisttracker")

        pub.subscribe(self.poweroff, "powermgt.off")
        pub.subscribe(self.poweron, "powermgt.on")

    def __onTrackedChanged(self, efforts):
        """
        Gère les changements dans la liste des efforts suivis.
        """
        if len(efforts):
            self.resume()
        else:
            self.pause()

    def getMinIdleTime(self):
        """
        Retourne le temps d'inactivité minimum.
        """
        return self._settings.getint("feature", "minidletime") * 60

    def wake(self, timestamp):
        """
        Est appelée lorsque le système est réveillé.
        """
        self._lastActivity = timestamp
        self.OnWake()

    def OnWake(self):
        """
        Gère le réveil du système et affiche la notification si nécessaire.
        """
        for effort in self.__tracker.trackedEfforts():
            if effort not in self._displayed:
                self._displayed.add(effort)
                # Remplace le cadre de notification wxPython par Tkinter
                frm = WakeFromIdleFrame(
                    parent=self._mainWindow,
                    idleTime=date.DateTime.fromtimestamp(self._lastActivity),
                    effort=effort,
                    displayedEfforts=self._displayed,
                    title=_("Notification"),
                )
                # La ligne ci-dessous est une version simplifiée de NotificationCenter().NotifyFrame(frm)
                # car nous ne savons pas comment NotificationCenter est implémenté dans Tkinter
                self._mainWindow.after(0, lambda: None)
                # NotificationCenter().NotifyFrame(frm)

    def poweroff(self):
        """Called when a 'powermgt.off' message is received."""
        # print("Power Off signal received (IdleController)")
        log.debug("Power Off signal received (IdleController)")
        self.pause()  # Pause the idle checker when powering off
        self._idle_notifier.stop()

    def poweron(self):
        """Called when a 'powermgt.on' message is received."""
        # print("Power On signal received (IdleController)")
        log.debug("Power On signal received (IdleController)")
        self.resume()  # Resume the idle checker when powering on
        self._idle_notifier.start()

    def pause(self):
        """Pause the idle checker."""
        log.debug("Idle checker paused (IdleController).")
        # Implement any logic to pause the idle checker (e.g., stop the timer)
        self._idle_notifier.stop()

    def resume(self):
        """Resume the idle checker."""
        log.debug("Idle checker resumed (IdleController).")
        # Implement any logic to resume the idle checker (e.g., start the timer)
        self._idle_notifier.start()

    def stop(self):
        """Arrête le Contrôleur pour l'inactivité du système."""
        log.debug("Idle checker and IdleController stop.")
        self._idle_notifier.stop()
