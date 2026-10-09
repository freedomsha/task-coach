"""
Task Coach - Your friendly task manager
Copyright (C) 2011-2023 Task Coach developers <developers@taskcoach.org>

Ported from wxPython to Tkinter.

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
# Points Clés des Modifications à idletk.py:
#
# Héritage: La classe IdleNotifier hérite maintenant uniquement de object et utilise une instance de IdleQuery pour obtenir le temps d'inactivité.
# pubsub: Les méthodes sleep et wake envoient des messages pubsub ("powermgt.off" et "powermgt.on").
# Initialisation: Le temps d'inactivité minimum est passé au constructeur.
# Logging: Ajout de logs pour faciliter le débogage.

import sys
import time
import threading
from tkinter import Tk
from ctypes import *
from pubsub import pub
from taskcoachlib import operating_system
import logging

log = logging.getLogger(__name__)

# ==============================================================================
# Linux/BSD

if operating_system.isGTK():
    class XScreenSaverInfo(Structure):
        _fields_ = [
            ("window", c_ulong),
            ("state", c_int),
            ("kind", c_int),
            ("til_or_since", c_ulong),
            ("idle", c_ulong),
            ("event_mask", c_ulong),
        ]

    class LinuxIdleQuery(object):
        def __init__(self):
            try:
                _x11 = CDLL("libX11.so.6")
                self.XOpenDisplay = CFUNCTYPE(c_ulong, c_char_p)(
                    ("XOpenDisplay", _x11)
                )
                # self.XOpenDisplay = _x11.XOpenDisplay
                # self.XOpenDisplay.restype = c_void_p
                self.XCloseDisplay = CFUNCTYPE(c_int, c_ulong)(
                    ("XCloseDisplay", _x11)
                )
                # self.XCloseDisplay = _x11.XCloseDisplay
                self.XRootWindow = CFUNCTYPE(c_ulong, c_ulong, c_int)(
                    ("XRootWindow", _x11)
                )
                # self.XRootWindow = _x11.XRootWindow
                # self.XRootWindow.restype = c_ulong
                # self.XRootWindow.argtypes = [c_void_p, c_int]

                self.dpy = self.XOpenDisplay(None)

                _xss = CDLL("libXss.so.1")
                self.XScreenSaverAllocInfo = CFUNCTYPE(POINTER(XScreenSaverInfo))(
                    ("XScreenSaverAllocInfo", _xss)
                )
                # self.XScreenSaverAllocInfo = _xss.XScreenSaverAllocInfo
                # self.XScreenSaverAllocInfo.restype = POINTER(XScreenSaverInfo)
                self.XScreenSaverQueryInfo = CFUNCTYPE(
                    c_int, c_ulong, c_ulong, POINTER(XScreenSaverInfo)
                )(("XScreenSaverQueryInfo", _xss))
                # self.XScreenSaverQueryInfo = _xss.XScreenSaverQueryInfo
                # self.XScreenSaverQueryInfo.argtypes = [c_void_p, c_ulong, POINTER(XScreenSaverInfo)]

                self.info = self.XScreenSaverAllocInfo()
            except OSError as e:
                log.error(f"Erreur de chargement des bibliothèques X11/Xss : {e}")
                self.dpy = None
                self.info = None

        def __del__(self):
            if self.dpy:
                self.XCloseDisplay(self.dpy)

        def getIdleSeconds(self):
            if not self.dpy or not self.info:
                return 0  # Retourne 0 si l'initialisation a échoué
            self.XScreenSaverQueryInfo(
                self.dpy, self.XRootWindow(self.dpy, 0), self.info
            )
            return 1.0 * self.info.contents.idle / 1000

    IdleQuery = LinuxIdleQuery

elif operating_system.isWindows():
    class LASTINPUTINFO(Structure):
        _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]

    class WindowsIdleQuery(object):
        def __init__(self):
            try:
                self.GetTickCount = windll.kernel32.GetTickCount
                self.GetLastInputInfo = windll.user32.GetLastInputInfo

                self.lastInputInfo = LASTINPUTINFO()
                self.lastInputInfo.cbSize = sizeof(self.lastInputInfo)
            except OSError as e:
                log.error(f"Erreur de chargement des bibliothèques Windows : {e}")
                self.GetTickCount = None
                self.GetLastInputInfo = None

        def getIdleSeconds(self):
            if not self.GetLastInputInfo:
                return 0
            self.GetLastInputInfo(byref(self.lastInputInfo))
            return (
                1.0 * self.GetTickCount() - self.lastInputInfo.dwTime
            ) / 1000

    IdleQuery = WindowsIdleQuery

elif operating_system.isMac():
    # Placeholder pour l'implémentation macOS
    # Tkinter ne fournit pas d'accès direct aux événements d'inactivité
    # Un module externe ou une API macOS serait nécessaire.
    class MacIdleQuery(object):
        def getIdleSeconds(self):
            # Implémentation réelle nécessaire ici, par exemple avec ctypes
            return 0
    IdleQuery = MacIdleQuery

else:
    # Implémentation par défaut pour les systèmes non supportés
    class DefaultIdleQuery(object):
        def getIdleSeconds(self):
            return 0
    IdleQuery = DefaultIdleQuery


# ==============================================================================
# La classe IdleNotifier est maintenant indépendante de la GUI pour une meilleure
# portabilité et utilise un thread pour la détection d'inactivité.
# Elle est conçue pour être utilisée avec n'importe quelle boucle d'événements Tkinter.
# 20/08/2025 Elle N'hérite PLUS d'IdleQuery.

# class IdleNotifier(IdleQuery):
class IdleNotifier():
    STATE_SLEEPING = 0
    STATE_AWAKE = 1

    # def __init__(self, root: Tk):
    def __init__(self, root: Tk, min_idle_time: int):
        # super(IdleNotifier, self).__init__() # No longer inheriting from IdleQuery
        self.idle_query = IdleQuery()  # Instance de IdleQuery pour obtenir le temps d'inactivité
        self.root = root  # Fenêtre principale Tkinter
        self.min_idle_time = min_idle_time  # Temps minimum en secondes
        self.state = self.STATE_AWAKE
        self.lastActivity = time.time()
        self.goneToSleep = None
        self._check_interval = 1000  # Intervalle de vérification en ms (1 seconde)
        self._thread = None
        self._running = False

        self.bind_events()
        log.debug("IdleNotifier initialisé.")

    def bind_events(self):
        """
        Lie les événements de la fenêtre principale pour détecter l'activité.
        """
        self.root.bind('<Motion>', self._on_activity)
        self.root.bind('<KeyPress>', self._on_activity)

    def _on_activity(self, event):
        """
        Met à jour le timestamp de la dernière activité.
        """
        self.lastActivity = time.time()
        # log.debug("Activité détectée, mise à jour du timestamp.")

    def start(self):
        """
        Démarre la détection d'inactivité.
        """
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_idle_check)
            self._thread.daemon = True
            self._thread.start()
            log.info("Détection d'inactivité démarrée dans un thread.")

    def stop(self):
        """
        Arrête la détection d'inactivité.
        """
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
            log.info("Détection d'inactivité arrêtée et thread terminé.")

    def _run_idle_check(self):
        """
        Boucle de vérification d'inactivité dans un thread séparé.
        """
        while self._running:
            self._check()
            time.sleep(self._check_interval / 1000)

    def _check(self):
        """
        Vérifie l'état d'inactivité et appelle les méthodes sleep/wake.
        """
        # current_idle_seconds = self.getIdleSeconds()
        current_idle_seconds = self.idle_query.getIdleSeconds()
        if self.state == self.STATE_AWAKE and current_idle_seconds >= self.getMinIdleTime():
            self.goneToSleep = self.lastActivity
            self.state = self.STATE_SLEEPING
            self.sleep()
            log.info("Passage en état d'inactivité.")
        elif self.state == self.STATE_SLEEPING and current_idle_seconds < self.getMinIdleTime():
            self.state = self.STATE_AWAKE
            self.wake(self.goneToSleep)
            log.info("Réveil de l'état d'inactivité.")

    def getMinIdleTime(self):
        """
        Doit retourner le temps minimum en secondes avant de passer en inactivité.
        """
        # raise NotImplementedError
        return self.min_idle_time

    def sleep(self):
        """
        Appelée lorsque le temps d'inactivité minimum s'est écoulé sans aucune
        saisie de l'utilisateur.
        """
        # pass
        log.info("Going to sleep...")
        # Envoyer un message à travers pubsub
        pub.sendMessage("powermgt.off")

    def wake(self, timestamp):
        """
        Appelée lorsque l'ordinateur n'est plus en inactivité.
        """
        # pass
        log.info(f"Waking up! Was idle since {timestamp}")
        # Envoyer un message à travers pubsub
        pub.sendMessage("powermgt.on")


# ==============================================================================
# Exemple d'utilisation

if __name__ == "__main__":
    class MyIdleNotifier(IdleNotifier):
        # def getMinIdleTime(self):
        #     return 5  # 5 secondes pour les tests
        #
        # def sleep(self):
        #     print("Going to sleep...")
        #
        # def wake(self, timestamp):
        #     print(f"Waking up! Was idle since {timestamp}")
        def __init__(self, root: Tk):
            super().__init__(root, min_idle_time=5)  # 5 secondes pour les tests

    root = Tk()
    root.title("Idle Notifier Test")
    root.geometry("400x200")

    notifier = MyIdleNotifier(root)
    notifier.start()

    print("Déplacez la souris ou appuyez sur une touche pour réinitialiser le temps d'inactivité.")
    print("Le programme passera en état 'inactif' après 5 secondes d'inactivité.")

    root.mainloop()

    # Arrêtez le thread de détection d'inactivité à la fin du programme.
    notifier.stop()
