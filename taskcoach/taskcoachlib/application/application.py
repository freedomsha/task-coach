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

Programme Principal

Module: application

Ce module fait partie de l'application Task Coach et contient
la logique principale de l'application,
y compris l'initialisation,
la configuration et
la boucle d'événements principale.

Classes:
    Application: Gère l'initialisation et l'exécution de l'application Task Coach.

Functions:
    start():
        Démarre l'application Task Coach.

    showHelp(parser):
        Affiche le message d'aide et quitte.

    showVersion():
        Affiche la version actuelle de l'application Task Coach et quitte.

    __init__(self, options, args):
        Initialise l'application avec les options et arguments de ligne de commande donnés.

    init(self, **kwargs):
        Initialise divers composants de l'application, tels que les paramètres, le contrôleur io
        , les fichiers de tâches, etc.

    __init_config(self, loadSettings):
        Initialise les paramètres de configuration de l'application.

    run(self):
        Exécute la boucle d'événements principale de l'application.

    stop(self):
        Arrête l'application et effectue le nettoyage nécessaire.

Attributes:

    _instance: Instance singleton de la classe Application.

    _options: Options de ligne de commande analysées à partir des arguments.

    _args: Arguments supplémentaires transmis à l’application.

    iocontroller: Gère les opérations d’entrée/sortie.

    taskfiles: Liste des fichiers de tâches gérés par l'application.

    settings: Paramètres de l'application.

    mainwindow: La fenêtre principale de l'application Task Coach.

Usage:
    Ce module est utilisé pour initialiser et exécuter l'application Task Coach.
    Il gère les arguments de ligne de commande, configure la configuration
    et démarre la boucle d'événements principale.

    Example:
        from taskcoachlib.application import application
        app = application.Application(options, args)
        app.run()

Dependencies:
    - wx: wxPython pour les composants GUI.
    - taskcoachlib.config: Gestion de la configuration.
    - taskcoachlib.iocontroller: Contrôleur d'entrée/sortie.
    - taskcoachlib.domain.task: Modèle de domaine de tâches.
    - taskcoachlib.gui.mainwindow: Fenêtre principale de l'application.
"""

# Ce module contourne les bugs des modules tiers, principalement en appliquant des correctifs singe,
# alors importez-le d'abord
# 2 ajouts de futurize : map et object
# from builtins import map  # Unused import statement 'from builtins import map'
# from builtins import object

import calendar
import datetime
import locale
import logging  # Attendre avant son implantation
import os
import re
import subprocess
import sys
import threading  # Unused import
import traceback
import time
import wx

# try:
from pubsub import pub

# except ImportError:
#    try:
#       # from ..thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
from io import open

# from taskcoachlib import workarounds  # pylint: disable=W0611  unused import statement
from taskcoachlib import patterns, operating_system, workarounds

# nouveau :
from taskcoachlib.i18n import _
from taskcoachlib.config import Settings
from taskcoachlib import gui, persistence

log = logging.getLogger(__name__)


def detect_dark_theme():
    """Detect if system is using dark theme.

    Returns True if dark theme detected, False otherwise.
    Requires wxApp to be initialized.
    """
    # import wx  # Import local
    app = wx.GetApp()  # Récupère l'application wx actuelle
    if not app:  # Si aucune application wx n'existe
        return False  # On évite tout appel dangereux

    try:
        appearance = (
            wx.SystemSettings.GetAppearance()
        )  # Accès au thème système
        return appearance.IsDark()  # Retourne True si sombre
    except AttributeError:
        # Older wxPython without GetAppearance()
        # Fallback: check if window background is dark
        try:
            bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            # Consider dark if luminance < 128
            luminance = (
                0.299 * bg.Red() + 0.587 * bg.Green() + 0.114 * bg.Blue()
            )
            return luminance < 128
        except Exception:
            return False
    except Exception:  # En cas de problème (wx pas prêt)
        return False  # Valeur par défaut sécurisée


class RedirectedOutput(object):
    """Classe objet de redirection de la sortie."""

    # TODO : A VERIFIER si la virgule est nécessaire
    _rx_ignore = [
        re.compile(
            "RuntimeWarning: PyOS_InputHook",
        )
    ]

    def __init__(self):
        """Fonction qui initialise l'argument du fichier à utiliser et l'argument du chemin du fichier taskcoachlog.txt"""
        # Argument fichier à utiliser
        self.__handle = None
        # chemin de taskcoachlog.txt
        self.__path = os.path.join(
            Settings.pathToDocumentsDir(), "taskcoachlog.txt"
        )

    def write(self, bf):
        """Fonction-méthode pour ouvrir puis écrire la Date et l'heure actuelle et bf dans taskcoachlog.txt"""
        for rx in self._rx_ignore:
            if rx.search(bf):
                return

        # Ancien code:
        # Si l'argument-fichier à utiliser n'existe pas
        if self.__handle is None:
            # le définir comme l'ouverture pour écriture du fichier taskcoachlog.txt
            # self.__handle = file(self.__path, 'a+')
            self.__handle = open(self.__path, "a+")
            # écrire la Date et l'heure actuelle dans taskcoachlog.txt
            # self.__handle.write("============= %s\n" % time.ctime())
            # self.__handle.write("============= {}\n".format(time.ctime()))
            # self.__handle.write(f"============= {time.ctime()}\n")
            # Écriture de l'horodatage et du contenu dans le fichier
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # if bf != "" or " ":
            # self.__handle.write("[%s] %s\n" % (timestamp, bf))
            self.__handle.write(f"[{timestamp}] {bf}\n")

        # écrire bf dans taskcoachlog.txt
        # self.__handle.write(bf)

    def flush(self):
        pass

    def close(self):
        """Fonction-méthode pour fermer taskcoachlog.txt"""
        # si l'Argument-fichier à utiliser existe, le fermer et le rendre inaccessible.
        if self.__handle is not None:
            self.__handle.close()
            self.__handle = None
            # self.__path = None

    def summary(self):
        """Fonction-méthode pour afficher une info sur ce qu'il vient d'être écrit dans taskcoachlog.txt"""
        if self.__handle is not None:
            self.close()  # fermer RedirectionOutput
            # if operating_system.isWindows():
            #     wx.MessageBox(
            #         _(
            #             'Errors have occured. Please see "taskcoachlog.txt" in your "My Documents" folder.'
            #         ),
            #         _("Error"),
            #         wx.OK,
            #     )
            # else:
            wx.MessageBox(
                _('Errors have occured. Please see "%s"') % self.__path,
                _("Error"),
                wx.OK,
            )
            # wx.MessageBox(_('Errors have occured. Please see "{}"'.format(self.__path)), _('Error'), wx.OK)
            # wx.MessageBox(_(f'Errors have occured. Please see "{self.__path}"'), _('Error'), wx.OK)


# pylint: disable=W0404


class wxApp(wx.App):
    """Classe App pour wxpython"""

    # {AttributeError}AttributeError("'ArtProvider' object has no attribute '_Application__wx_app'")
    # Pour pouvoir lancer un interface graphique wxPython,
    # on doit obligatoirement passer par un objet chargé de créer l'instance de la classe principale de l'interface (le Top Level).
    # Cet objet doit lui-même être construit et dériver de la classe wx.App

    def __init__(self, sessionCallback, reopenCallback, *args, **kwargs):
        self.sessionCallback = sessionCallback
        self.reopenCallback = reopenCallback
        self.__shutdownInProgress = False
        # super(wxApp, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

    def MacReopenApp(self):
        """Fonction-méthode pour rouvrir l'application sur Mac."""
        self.reopenCallback()

    def OnInit(self):
        # La classe wx.App est initialisée différemment des classes Python classiques.
        # Ce n'est pas la méthode __init__() qui doit être implémentée,
        # mais une méthode OnInit() sans paramètre (sauf le mot clé self qui lui permet de s'auto-référencer).
        """Fonction-méthode wxPython qui gère la sortie standard renvoie true sur l'initialisation.

        Initialise l'application et gère la redirection de sortie standard sur des plates-formes spécifiques.

        - Binds to `wx.EVT_QUERY_END_ SESSION` on Windows to manage session ending.
        - Redirects standard output to `sys.stderr` if running a frozen executable or not in a terminal.

        Returns :
            (bool) : True on successful initialization.
        """
        # La séquence d'initialisation de la méthode OnInit() est alors toujours la même :
        #    fen = Bonjour("Exemple 1")  # Création d'une instance de la fenêtre principale.
        #    fen.Show(True)  # Affichage de la fenêtre par la méthode Show() dérivée de la classe wx.Window.
        #    self.SetTopWindow(fen)  # Désignation de la fenêtre en tant que principale par la méthode SetTopWindow() spécifique à la classe wx.App
        #    return True  # Retour de la valeur True marquant la fin de l'initialisation
        # voir https://docs.python.org/fr/3.11/library/sys.html#sys.stdout
        # if operating_system.isWindows():
        #     self.Bind(wx.EVT_QUERY_END_SESSION, self.onQueryEndSession)

        try:
            isatty = sys.stdout.isatty()  # isatty is False !
        except AttributeError:
            isatty = False

        if (
            operating_system.isWindows()
            and hasattr(sys, "frozen")
            and not isatty
        ) or not isatty:
            sys.stdout = sys.stderr = RedirectedOutput()
            self.Bind(wx.EVT_QUERY_END_SESSION, self.onQueryEndSession)

        return True

    def onQueryEndSession(self, event=None):
        """
        Gère la session se terminant gracieusement, en appelant `sessionCallback` une seule fois.

        Args :
            event (wx.Event, optional) : L'objet événement si disponible. La valeur par défaut est None.
        """
        if not self.__shutdownInProgress:
            self.__shutdownInProgress = True
            self.sessionCallback()

        if event is not None:
            event.Skip()

    def OnExceptionInMainLoop(self):
        """Called by wx when an unhandled exception occurs during event dispatch.

        Logs the full traceback to stderr so crashes during event handling
        are visible instead of being silently swallowed. Returns True to
        continue running (the event that caused the error is skipped).
        See docs/CRASH_GUARD.md for details.
        """
        import traceback

        # from taskcoachlib.meta.debug import log_step

        log.debug(
            "Unhandled exception in MainLoop: %s", traceback.format_exc()
        )
        return True

    # disparition de :
    def ProcessIdle(self):
        """
        Conservée pour des raisons de compatibilité avec les tests existants et `quitApplication`.

        Cette méthode peut être utile pour le traitement inactif personnalisé dans votre application.
        Cependant, son implémentation spécifique dépend de vos besoins.
        """
        pass

    # dans le fichier application.py pourtant elle est utilisée dans les tests et dans quitApplication


# class Application(object):
#     __metaclass__ = patterns.Singleton
# class Application(metaclass=patterns.Singleton):
class Application(object, metaclass=patterns.Singleton):
    """Classe principale de l'application TaskCoach.

    Gère le lancement et l'arrêt de l'application,
    ainsi que l'initialisation de ses différents composants.

    La méthode initTwisted initialise et lance le réacteur Twisted,
    qui permet de gérer les événements asynchrones de l'application.

    La méthode start lance l'application en affichant la fenêtre principale
    et en démarrant la boucle d'événements de Twisted.

    La méthode quitApplication permet de quitter l'application
    en sauvegardant les paramètres et l'état de l'application.

    DESIGN NOTE (Twisted Removal - 2024):
    Previously used Twisted's wxreactor to integrate Twisted's event loop with
    wxPython. This has been replaced with native wxPython functionality:
    - wxreactor.install() → removed (wx.App.MainLoop() used directly)
    - reactor.registerWxApp() → removed (not needed)
    - reactor.run() → wx.App.MainLoop()
    - reactor.stop() → wx.App.ExitMainLoop() via EVT_CLOSE handlers
    - reactor.callLater() → wx.CallLater() (in scheduler.py)

    This simplifies the event loop architecture and eliminates potential
    race conditions between two event loops.
    """

    def __init__(self, options=None, args=None, **kwargs):
        # !!! fait TROP de choses !!!
        # crée GUI, charge fichiers, appelle wx, etc.
        # Un constructeur doit être léger, sinon:
        # impossible de mock, impossible de tester sans GUI, crash wx
        """La méthode init est appelée avant le démarrage de l'application.

        Elle configure divers aspects de l'application, notamment la langue,
        le correcteur orthographique,
        la gestion des signaux et la création d'icônes de barre des tâches.

        Args :
            options (Namespace, optional) : Les options de ligne de commande analysées. La valeur par défaut est None.
            args (list, optional) : Les arguments supplémentaires transmis à l'application. La valeur par défaut est None.
            **kwargs : Arguments supplémentaires pour la configuration de l'application.

        Attributes :
            __message_checker : Vérificateur de messages pour les notifications.
            __version_checker : Vérificateur de version pour les mises à jour.
            mainwindow : La fenêtre principale de l'application.
            iocontroller : Contrôleur d'entrée/sortie pour la gestion des fichiers.
            __auto_backup : Gestionnaire de sauvegarde automatique.
            __auto_exporter : Gestionnaire d'exportation automatique.
            __auto_saver : Gestionnaire de sauvegarde automatique.
            taskFile : Fichier de tâches actuellement ouvert.
            __early_lock_result : Résultat précoce de la tentative de verrouillage du fichier INI.
            _options : Options de ligne de commande analysées.
            _args : Arguments supplémentaires transmis à l'application.
            _wx_app : Instance de wx.App pour la gestion de l'interface graphique.
            settings : Paramètres de l'application.
            sessionMonitor : Moniteur de session pour gérer les événements de fin de session sur les systèmes compatibles.
        """
        # ... (initialisation des attributs d'instance)
        # log.critical("🔥 Application.__init__() APPELÉE")
        # traceback.print_stack()
        # nouveaux Attributs d'instance :
        #   # Défini dans start
        self.__message_checker = None
        self.__version_checker = None
        # Défini dans self.init :
        self.mainwindow = None
        self.iocontroller = None
        self.__auto_backup = None
        self.__auto_exporter = None
        self.__auto_saver = None
        self.taskFile = None
        self.__early_lock_result = None

        self._options = options
        self._args = args
        # # Initialisation de Twisted (1-3/5)
        # # self.initTwisted()
        # try:
        #     self.initTwisted()
        # except Exception as e:
        #     log.exception(
        #         f"application.py: Error initializing Twisted: {str(e)}",
        #         exc_info=True,
        #     )
        #     # print(f"application.py: Error initializing Twisted: {e}")
        #     # wx.MessageBox(f"application.py Application.__init__: Error initializing Twisted: {e}",
        #     #               "Error", wx.OK | wx.ICON_ERROR)
        # # print("application.Application.__init__: Twisted initialized")
        # log.info("Application : Twisted initialisé avec succès.")
        # # 1. Log environment info first (no dependencies)
        # _log_environment()

        # Ne pas lancer le GUI dans __init__ -> anti-pattern
        # # 1. wx-1-Create a new app FIRST to initialize traits (StandardPaths, etc.)
        # self.__wx_app = wx.GetApp()
        # if not self.__wx_app:
        #     self.__wx_app = wxApp(
        #         self.on_end_session, self.on_reopen_app, redirect=False
        #     )
        # Cette section est déplacée dans init()
        # Pas de wx ici
        self.__wx_app = None
        #
        # # 2. Load settings AFTER wxApp is initialized
        # self.__init_config(kwargs.get("loadSettings", True))
        #
        # # myapp = MyApp() # functions normally. Stdio is redirected to its own window
        # # myapp = MyApp(0) #does not redirect stdout. Tracebacks will show up at the console.
        # # myapp = MyApp(1, 'filespec') #redirects stdout to the file 'filespec'
        # # # NOTE: These are named parameters, so you can do this for improved readability:
        # # myapp = MyApp(redirect = 1, filename = 'filespec') # will redirect stdout to 'filespec'
        # # myapp = MyApp(redirect = 0) #stdio will stay at the console...
        # # self.__wx_app = wxApp(self.on_end_session, self.on_reopen_app, redirect=1, filename=RedirectedOutput().__path)
        # # Après cela, wx-2-création d'une Frame !(-> voir Dans init)
        #
        # # print("application.Application.__init__: self.__wx_app défini !")
        # # log.debug("Application wxApp créée.")
        #
        # # # Twisted (4/5) Enregistrement de l'application dans Twisted
        # # self.registerApp()
        # # # print("application.Application.__init__: self.registerApp() !")
        # # Expose settings on wxApp so wx.GetApp().settings works everywhere
        # self.__wx_app.settings = self.settings
        self.settings = None  # sera initialisé plus tard
        #
        # # # 4. Log wx-specific info (needs wxApp)
        # # _log_wx_info()
        #
        # # 5. Acquire INI lock (needs wxApp for error dialog)
        # self.settings.acquire_ini_lock()
        # # wx-2 :
        # # log.debug("Appel de la Méthode init().")
        # self.init(**kwargs)  # passe mais n'atteint pas la suite ! goto l540
        # # print("application.Application.__init__: self.init() !")
        # # log.debug("Méthode init() appelée.")
        #
        # # self est Application (tclib.application.application.Application)
        # # # Attributs d'instance définis en dehors de __init__ , nécessaires dans start:
        # # # __version_checker, __message_checker
        # # # taskFile, __auto_saver, __auto_exporter, __auto_backup, iocontroller, mainwindow
        # # # 6 nouveaux paramètres nécessaires dans init
        # # self.__version_checker = None
        # # self.__message_checker = None
        # # # Instance attribute taskFile, __auto_saver, __auto_exporter, __auto_backup, iocontroller, mainwindow
        # # # defined outside __init__
        # # # 6 nouveaux paramètres nécessaires dans init :
        # # self.taskFile = None
        # # self.__auto_saver = None
        # # self.__auto_exporter = None
        # # self.__auto_backup = None
        # # self.iocontroller = None
        # # self.mainwindow = None

        # if operating_system.isGTK():
        #     if self.settings.getboolean("feature", "usesm2"):
        #         from taskcoachlib.powermgt import xsm
        #
        #         class LinuxSessionMonitor(xsm.SessionMonitor):
        #             def __init__(self, callback):
        #                 super().__init__()
        #                 self._callback = callback
        #                 self.setProperty(xsm.SmCloneCommand, sys.argv)
        #                 self.setProperty(xsm.SmRestartCommand, sys.argv)
        #                 self.setProperty(xsm.SmCurrentDirectory, os.getcwd())
        #                 self.setProperty(xsm.SmProgram, sys.argv[0])
        #                 self.setProperty(
        #                     xsm.SmRestartStyleHint, xsm.SmRestartNever
        #                 )
        #
        #             def saveYourself(
        #                 self, saveType, shutdown, interactStyle, fast
        #             ):  # pylint: disable=W0613
        #                 if shutdown:
        #                     wx.CallAfter(self._callback)
        #                 self.saveYourselfDone(True)
        #
        #             def die(self):
        #                 pass
        #
        #             def saveComplete(self):
        #                 pass
        #
        #             def shutdownCancelled(self):
        #                 pass
        #
        #         self.sessionMonitor = LinuxSessionMonitor(
        #             self.on_end_session
        #         )  # pylint: disable=W0201
        #     else:
        #         self.sessionMonitor = None
        #
        # # print("application.Application.__init__: isGTK? !")
        # calendar.setfirstweekday(
        #     dict(monday=0, sunday=6)[self.settings.get("view", "weekstart")]
        # )
        self.sessionMonitor = None

    # # NOTE: initTwisted(), stopTwisted(), and registerApp() methods removed.
    # # Previously used Twisted's wxreactor for event loop integration.
    # # Now using native wx.App.MainLoop() which is simpler and more reliable.
    # # See class docstring for migration details.
    # def initTwisted(self):
    #     """Fonction-méthode pour initialiser et lancer Twisted.
    #
    #     Initialise et lance le réacteur Twisted, qui permet de gérer les événements asynchrones de l'application.
    #     Centralise aussi tous les logs (Twisted inclus).
    #     """
    #     # voir peut-être https://docs.twisted.org/en/stable/core/howto/design.html
    #     # et https://docs.twisted.org/en/stable/core/howto/process.html
    #     # et pour python 3 : https://docs.twisted.org/en/stable/core/howto/python3.html
    #     # https://docs.twisted.org/en/stable/core/howto/choosing-reactor.html
    #     # Twisted (1/5) to use Twisted
    #     from twisted.internet import wxreactor
    #
    #     # twisted.python.log s'est sensiblement déplacé vers le texte des str
    #     # à partir de lignes d'octets.
    #     # Événements d'exploitation forestière,
    #     # en particulier ceux produits par un Appel comme msg("foo"),
    #     # doit maintenant être des chaînes de texte.
    #     # Par conséquent, sur Python 3, les dictionnaires d'événements
    #     # passés aux enregistrements de journaliser
    #     # confulent une chaîne de texte où
    #     # elles contenaient précédemment des chaînes d'octets.
    #     # twisted.python.filepath.FilePath n'a pas changé.
    #     # Il ne supporte que des lignes d'octets.
    #     # Cela nécessitera probablement des demandes pour
    #     # mettre à jour leur utilisation de FilePath,
    #     # au moins pour passer un octet explicite littérales de chaîne
    #     # plutôt que "native" littérales de chaîne (qui sont du texte sur Python 3).
    #
    #     # Twisted (2/5)
    #     wxreactor.install()
    #
    #     # Monkey-patching older versions because of https://twistedmatrix.com/trac/ticket/3948
    #     # J'ai deux alternatives à :
    #     #         if map(int, twisted.__version__.split('.')) < (11,):
    #     #             from twisted.internet import reactor
    #     #             if wxreactor.WxReactor.callFromThread is not None:
    #     #                 oldStop = wxreactor.WxReactor.stop
    #     #                 def stopFromThread(self):
    #     #                     self.callFromThread(oldStop, self)
    #     #                 wxreactor.WxReactor.stop = stopFromThread
    #     # celle généré par futurize:
    #     # import twisted  # Unused import
    #
    #     # if list(map(int, twisted.__version__.split('.'))) < (11,):
    #     # if list(twisted.__version__.split(".")) < ['11', ]:
    #     # if tuple(map(int, twisted.__version__.split("."))) < (11,):
    #     # ValueError: invalid literal for int() with base 10: '0rc1'
    #     # Est-ce nécessaire ?
    #     # Twisted (3/5), when Wxapp has been created :
    #     # from twisted.internet import wxreactor, threads  # unused import
    #     from twisted.internet import wxreactor
    #
    #     # TODO: retrouver dans twisted de quoi remplacer callFromThread
    #     # une piste sur https://stackoverflow.com/questions/4081578/python-twisted-with-callinthread
    #     # https://docs.twistedmatrix.com/en/stable/core/howto/threading.html#getting-results
    #     if wxreactor.WxReactor.callFromThread is not None:
    #         # if threads.deferToThread is not None:
    #         oldStop = wxreactor.WxReactor.stop
    #
    #         def stopFromThread(self):
    #             self.callFromThread(oldStop, self)
    #             # self.deferToThread(oldStop, self)
    #             # ou
    #             # self.blockingCallFromThread(oldStop, self)
    #
    #         wxreactor.WxReactor.stop = stopFromThread
    #         # wxreactor.WxReactor.stop = wxreactor.WxReactor.callFromThread(wxreactor.WxReactor.stop, self)  # Ne fonctionne pas !
    #         # <taskcoachlib.application.application.Application object at 0x7c07fff70110> is not callable
    #     # ou
    #     # import twisted
    #     # print(list(twisted.__version__.split('.')))
    #     # if list(twisted.__version__.split('.')) < ['11', '0']:
    #     #    # essayer list seul sinon list(map())
    #     #    # from twisted.internet import reactor  # doublon soit-disant déjà installé
    #     #    if wxreactor.WxReactor.callFromThread is not None:
    #     #        oldStop = wxreactor.WxReactor.stop
    #     #        def stopFromThread(self):
    #     #            self.callFromThread(oldStop, self)
    #     #        wxreactor.WxReactor.stop = stopFromThread
    #     #        # ou essayer avec https://www.programcreek.com/python/example/117947/twisted.internet.error
    #     #        # .ReactorAlreadyInstalledError
    #
    #     # Centraliser tous les logs (Twisted inclus) :
    #     from twisted.python import log as twisted_log
    #
    #     twisted_log.startLoggingWithObserver(
    #         lambda msg: log.info(msg.get("message"))
    #     )
    #     # msg("Log opened.")

    # def stopTwisted(self):
    #     """Fonction-méthode pour arrêter twisted-reactor"""
    #     # voir https://stackoverflow.com/questions/6526923/stop-twisted-reactor-on-a-condition
    #     # from twisted.internet import reactor, error
    #     from twisted.internet import reactor, error
    #
    #     log.debug("Application.stopTwisted : Essaie d'arrêter reactor.")
    #     try:
    #         reactor.stop()  # cannot find stop in reactor, but don't use yourApp.ExitMainLoop()
    #         log.debug("Application.stopTwisted : A lancé reactorstop().")
    #     except error.ReactorNotRunning as e:
    #         # Happens on Fedora 14 when running unit tests. Old Twisted ?
    #         # in Arch, reference 'stop' not find in 'reactor.py'
    #         log.error(
    #             "Application.stopTwisted : Reactor n'a pas démarré !",
    #             exc_info=True,
    #             stack_info=True,
    #         )
    #         pass
    #     # Arrêter les threads workers
    #     log.debug(
    #         "Application.stopTwisted : Essaie d'arrêter les threads workers"
    #     )
    #     try:
    #         reactor.getThreadPool().stop()
    #         log.debug(
    #             "Application.stopTwisted : avec la méthode getThreadPool().stop()."
    #         )
    #     except AttributeError:
    #         # Certains réacteurs n'ont pas de threadpool explicite
    #         try:
    #             reactor.threadpool.stop()
    #             log.debug(
    #                 "Application.stopTwisted : avec la méthode threadpool().stop()."
    #             )
    #         except AttributeError:
    #             log.debug(
    #                 "Application.stopTwisted : aucune méthode ne fonctionne pour arrêter les workers."
    #             )
    #     time.sleep(0.1)  # Donne un peu de temps au worker pour s'arrêter

    # def registerApp(self):
    #     """Fonction-méthode pour Enregistrez l'instance d'application avec Twisted:"""
    #     # try:
    #     # Twisted (3/5), when Wxapp has been created :
    #     from twisted.internet import reactor
    #
    #     # voir peut-etre aussi twisted.internet.wxreactor.WxReactor !
    #     # Twisted (4/5) : (5/5) est dans start !
    #     reactor.registerWxApp(self.__wx_app)
    #     # except ModuleNotFoundError:
    #     #     from twisted.internet import wxreactor
    #     #     # https://docs.twistedmatrix.com/en/stable/api/twisted.internet.wxreactor.WxReactor.html#registerWxApp
    #     #     wxreactor.WxReactor.registerWxApp(self.__wx_app)
    #     # except TypeError:
    #     #     print("registerWxApp missing 1 argument")
    #     #     pass

    def start(self):
        """Fonction-méthode d'Appel pour démarrer l'application.

        Lance l'application en affichant la fenêtre principale et en démarrant la boucle d'événements de Twisted.

        """
        # pylint: disable=W0201
        from taskcoachlib import meta

        log.info("Application.start : Lancement de la fenêtre principale")
        if self.settings.getboolean("version", "notify"):
            self.__version_checker = meta.VersionChecker(self.settings)
            self.__version_checker.start()
        if self.settings.getboolean("view", "developermessages"):
            self.__message_checker = meta.DeveloperMessageChecker(
                self.settings
            )
            self.__message_checker.start()
        self.__copy_default_templates()

        # Redirect wx log messages to stderr instead of popup dialogs
        if operating_system.isGTK():
            wx.Log.SetActiveTarget(wx.LogStderr())
            wx.Log.SetLogLevel(wx.LOG_Info)
            wx.Log.SetVerbose(True)

        # Show the frame.
        # self.mainwindow.Show()  # ligne qui devrait être la 2e dans OnInit, ou en 3e après frame !
        self.mainwindow.Show(True)
        # Ensuite, il devrait y avoir self.__wx_app.MainLoop() !
        # Ici, c'est remplacé par twisted.reactor.

        # # vieux code
        # #  from twisted.internet import reactor
        # #         reactor.run()
        # # Twisted (3/5) :
        # from twisted.internet import reactor
        #
        # # Twisted (4/5) : est dans RegisterApp

        # # voir https://github.com/twisted/twisted/blob/63df84e454978bd7a2d57ed292913384ca352e1a/src/twisted/internet/wxreactor.py#L74
        # # start the event loop:
        # # Démarre la boucle des événements:
        # # Twisted (5/5):
        # # reactor.run()
        # try:
        #     reactor.run()
        # except Exception as e:
        #     # logging.error("application.py: Error running Twisted reactor: %s", str(e))
        #     # wx.MessageBox(f"application.py: Error running Twisted reactor: {e}",
        #     #               "Error", wx.OK | wx.ICON_ERROR)
        #     wx.MessageDialog(
        #         self,
        #         message=f"application.py: Error running Twisted reactor: {e}",
        #         caption="Error",
        #         style=wx.OK | wx.ICON_ERROR,
        #     )
        #     # Gérer l'erreur de manière appropriée (par exemple, afficher un message à l'utilisateur)
        # IMPORTANT: tests will fail when run under this reactor. This is
        # expected and probably does not reflect on the reactor's ability to run
        # real applications.
        #
        # ou essayer :
        # from twisted.internet.interfaces import IReactorCore
        # ou twisted.internet.wxreactor.WxReactor.run
        # IReactorCore.run()
        # https://docs.twisted.org/en/stable/api/nameIndex.html#R
        # twisted.application.app.ApplicationRunner.run
        # twisted.application.app.AppProfiler.run
        # twisted.application.app.CProfileRunner.run
        # twisted.application.app.ProfileRunner.run
        # twisted.application.app.run
        # twisted.conch.scripts.cftp.run
        # twisted.conch.scripts.ckeygen.run
        # twisted.conch.scripts.conch.run
        # twisted.conch.scripts.tkconch.run
        # twisted.internet.asyncioreactor.AsyncioSelectorReactor.run
        # twisted.internet.base.ReactorBase.run
        # twisted.internet.interfaces.IReactorCore.run
        # twisted.internet.testing.MemoryReactor.run
        # twisted.internet.wxreactor.WxReactor.run
        # twisted.internet.wxsupport.wxRunner.run
        # Position correction is handled automatically by WindowDimensionsTracker
        # via EVT_MOVE detection until EVT_ACTIVATE fires (window ready for input)
        # Use native wxPython main loop instead of Twisted reactor
        # NOTE: Previously used reactor.run() with wxreactor integration.
        # Now using wx.App.MainLoop() directly for simpler event handling.
        try:
            self.__wx_app.MainLoop()
        finally:
            # Explicitly cleanup wx.App to prevent crashes during Python shutdown
            # See: https://github.com/wxWidgets/Phoenix/issues/429
            if (
                hasattr(self, "_signal_check_timer")
                and self._signal_check_timer
            ):
                self._signal_check_timer.Stop()

            # On Windows with console (python.exe), detach from console before cleanup
            # The crash only happens with python.exe (console subsystem), not pythonw.exe (GUI subsystem)
            # This suggests the crash is related to console cleanup during Python shutdown
            if operating_system.isWindows():
                sys.stderr.flush()
                sys.stdout.flush()
                try:
                    import ctypes

                    # FreeConsole detaches the process from its console
                    # This prevents console-related cleanup issues during Python shutdown
                    ctypes.windll.kernel32.FreeConsole()
                except Exception:
                    pass
                # Redirect stdout/stderr to devnull to prevent write errors after console detach
                sys.stderr = open(os.devnull, "w")
                sys.stdout = open(os.devnull, "w")

            # Prevent destructor issues by explicitly destroying the app
            self.__wx_app.Destroy()
        log.info("Application.start : Terminé.")

    def __copy_default_templates(self):
        """Copie les modèles par défaut qui n'existent pas encore dans le répertoire de modèles de l'utilisateur."""

        # class getDefaultTemplates créé par templates.in/make.py
        from taskcoachlib.persistence import getDefaultTemplates

        # créé par templates.in/make

        template_dir = self.settings.pathToTemplatesDir()
        if (
            len(
                [
                    name
                    for name in os.listdir(template_dir)
                    if name.endswith(".tsktmpl")
                ]
            )
            == 0
        ):
            for name, template in getDefaultTemplates():
                filename = os.path.join(template_dir, name + ".tsktmpl")
                if not os.path.exists(filename):
                    # # ouverture du fichier filename en mode bytes !!! et y écrire template
                    # # file(filename, "wb").write(template)
                    # open(filename, "wb").write(template)
                    # Decode bytes to string for text mode writing
                    template_str = (
                        template.decode("utf-8")
                        if isinstance(template, bytes)
                        else template
                    )
                    open(filename, "w", encoding="utf-8").write(template_str)

    def init(self, loadSettings=True, loadTaskFile=True):
        """Initialiser l'application.

        Appelé par __init__.
        Doit être appelé avant Application.start().

        Args:
            loadSettings (bool, optional): Charger les paramètres de l'application. Defaults to True.
            loadTaskFile (bool, optional): Charger le fichier de tâches. Defaults to True.
        """
        # log.critical("⚠️ Application.init() APPELÉE")
        # traceback.print_stack()
        log.info(
            "Application.init: Initialisation des composants de l'application."
        )

        # 1. Initialiser wx AVANT tout appel GUI, autrefois dans __init__
        # import wx
        self.__wx_app = wx.GetApp()
        if not wx.GetApp():
            self.__wx_app = wxApp(
                self.on_end_session, self.on_reopen_app, redirect=False
            )

        # 2. Charger config APRÈS wx
        self.__init_config(loadSettings)

        # 3. Exposer settings à wx
        self.__wx_app.settings = self.settings

        # 4. Lock fichier
        self.settings.acquire_ini_lock()
        # fin du changement de __init__

        # try:
        # Attributs d'instance:
        # self.__init_config(loadSettings)  # Recréation de self.settings déjà appelé dans __init__. -> erreur
        self.__init_language()
        #  Fournir aux objets de domaine pertinents un accès aux paramètres :
        # log.info("Application.init: Fournir aux objets de domaine pertinents un accès aux paramètres :")
        self.__init_domain_objects()  # Passe directement à l556 !? après avoir affiché 6 lignes debug image handler for
        self.__init_application()  # Réglage des paramètres nom et auteurs de l'application.
        # Problème de doublon d'image ! : réglé, double entrée de .mainwindow dans gui/init.py
        # print("application.Application.init : attributs ok !")
        if operating_system.isGTK():
            if self.settings.getboolean("feature", "usesm2"):
                from taskcoachlib.powermgt import xsm

                class LinuxSessionMonitor(xsm.SessionMonitor):
                    def __init__(self, callback):
                        super().__init__()
                        self._callback = callback
                        self.setProperty(xsm.SmCloneCommand, sys.argv)
                        self.setProperty(xsm.SmRestartCommand, sys.argv)
                        self.setProperty(xsm.SmCurrentDirectory, os.getcwd())
                        self.setProperty(xsm.SmProgram, sys.argv[0])
                        self.setProperty(
                            xsm.SmRestartStyleHint, xsm.SmRestartNever
                        )

                    def saveYourself(
                        self, saveType, shutdown, interactStyle, fast
                    ):  # pylint: disable=W0613
                        if shutdown:
                            wx.CallAfter(self._callback)
                        self.saveYourselfDone(True)

                    def die(self):
                        pass

                    def saveComplete(self):
                        pass

                    def shutdownCancelled(self):
                        pass

                self.sessionMonitor = LinuxSessionMonitor(
                    self.on_end_session
                )  # pylint: disable=W0201
            else:
                self.sessionMonitor = None

        # print("application.Application.__init__: isGTK? !")
        calendar.setfirstweekday(
            dict(monday=0, sunday=6)[self.settings.get("view", "weekstart")]
        )

        # Check file lock BEFORE creating main window to avoid dialog/focus issues
        # This is done early because showing dialogs after main window creation
        # causes GTK focus fighting and dialog disappearing issues
        # Note: INI file lock is already checked in __init_config() above
        self.__early_lock_result = None  # None=no file, 'ok'=proceed, 'break'=break lock, 'skip'=don't open file
        if loadTaskFile:
            self.__check_file_lock_early()
            # If user said "No" to break lock, we continue but don't open the file
            # (program starts with no file open, like a fresh start)

        # from taskcoachlib import gui, persistence  # TODO : à mettre au début !

        gui.init()  # goto gui.artprovider.init : Initialise l'ArtProvider
        # print("application.Application.init : gui.init(), Problème de doublons ? C'était MainWindow en double dans gui/init.py")
        show_splash_screen = self.settings.getboolean(
            "window", "splash"
        )  # = True puis l560
        splash = gui.SplashScreen() if show_splash_screen else None
        # pylint: disable=W0201
        # 1. Création du taskFile
        self.taskFile = persistence.taskfile.LockedTaskFile(
            # poll=not self.settings.getboolean("file", "nopoll")
            poll=self.settings.getboolean("file", "fspoll")
        )  # Application.taskFile puis passe à l160 flush . Pourquoi ? Parce que persistence.LockedTaskFile plante.
        # log.debug(
        #     f"Application.init: persistence.LockedTaskFile créé avec poll={self.taskFile.poll}."
        # )  # Crée un problème et arrête net le programme ! Pourquoi ? Parce que persistence.LockedTaskFile plante car il est vide.
        log.debug(
            f"Application.init: le fichier à ouvrir est self.taskfile = {self.taskFile.lastFilename()}."
        )
        self.__auto_saver = persistence.AutoSaver(self.settings)
        self.__auto_exporter = persistence.AutoImporterExporter(self.settings)
        self.__auto_backup = persistence.AutoBackup(self.settings)
        # 2. Création IOController
        self.iocontroller = gui.iocontroller.IOController(
            self.taskFile, self.displayMessage, self.settings, splash
        )
        log.warning(
            "Application.init:  id(self.taskFile) : %s", id(self.taskFile)
        )
        # log.warning("Real taskfile id:", id(application.taskFile))
        log.warning(
            "Application.init: Nb tâches viewer: %s",
            len(self.taskFile.tasks()),
        )
        # log.warning("Nb tâches réel:", len(application.taskFile.tasks()))

        # wx-2-Création d'une instance de la fenêtre Principale (objet de gui.mainwindow.MainWindow, wx.Frame):
        # ligne qui devrait être la première dans OnInit (ou en tout cas juste après self.__wx_app = wxApp() dans __init__):
        log.info("Application.init: Initialisation de la fenêtre principale.")
        self.mainwindow = gui.mainwindow.MainWindow(
            self.iocontroller, self.taskFile, self.settings, splash=splash
        )  # A Frame is a top-level window.
        # Initialisation GUI tardive (wx prêt)
        wx.CallAfter(self.__post_gui_init)
        log.info("Application.init: TASKS: %s", len(self.taskFile.tasks()))
        log.info(
            "Application.init: VIEWER: %s",
            len(self.mainwindow.viewer.presentation()),
        )
        # self.mainwindow.refresh()  # Fait planter !
        # for viewer in self.mainwindow.viewer.viewers():
        #     viewer.refresh()
        # log.info(f"Application : self.mainwindow.winId = {self.mainwindow.winId}")
        # Après il devrait y avoir self.mainwindow.Show(true) !(Voir start())

        # Désignation de la fenêtre en tant que principale par la méthode SetTopWindow() spécifique à la classe wx.App
        # ligne qui devrait être en 3e position dans OnInit:
        log.info("Application.init: Fenêtre principale mise en avant.")
        # Notre classe dérivée de WXApp normale, comme d'habitude (même avec wx.lib.agw.aui).
        self.__wx_app.SetTopWindow(self.mainwindow)
        # Ensuite : frame.Show()
        log.critical("Application taskFile id: %s", id(self.taskFile))
        log.critical(
            "MainWindow taskFile id: %s", id(self.mainwindow.taskFile)
        )
        # log.critical(
        #     "IOController taskFile id: %s", id(self.iocontroller.taskFile)
        # )  # fait planter ! Pourquoi ? Parce que persistence.LockedTaskFile plante car il est vide.
        log.critical("IOController dict: %s", self.iocontroller.__dict__)

        log.info("Application.init : loadTaskFile est coché ?")
        # # Si loadTaskFile est configuré sur True ouvrir le fichier de self._args avec openAfterStart:
        # if loadTaskFile and self._args:
        #     log.info(
        #         f"Oui, Application.init ouvre un fichier grâce à _args={self._args} et self.__early_lock_result={self.__early_lock_result}."
        #     )
        #     # self.iocontroller.openAfterStart(self._args)
        #     self.iocontroller.openAfterStart(
        #         self._args, self.__early_lock_result
        #     )
        # else:
        #     log.info("Non, Application.init n'ouvre pas de fichier.")
        if loadTaskFile:
            if self._args:
                log.info(
                    f"Application.init : Ouverture du fichier depuis args : {self._args}."
                )
                self.iocontroller.openAfterStart(
                    self._args, self.__early_lock_result
                )
            else:
                lastfile = self.settings.get("file", "lastfile")
                # if lastfile and os.path.exists(lastfile):
                if lastfile:
                    log.info(
                        "Ouverture automatique du dernier fichier : %s",
                        lastfile,
                    )
                    self.iocontroller.openAfterStart(
                        [lastfile], self.__early_lock_result
                    )
                else:
                    log.info("Aucun fichier à ouvrir au démarrage.")

        log.warning("Application.taskFile id = %s", id(self.taskFile))
        log.warning(
            "Application.taskFile.tasks id = %s", id(self.taskFile.tasks())
        )

        self.__init_spell_checking()  # Attention changements
        if not self.settings.getboolean("file", "inifileloaded"):
            self.__close_splash(splash)
            self.__warn_user_that_ini_file_was_not_loaded()

        self.__register_signal_handlers()  # Est-elle bien implémentée ?
        self.__create_mutex()
        self.__create_task_bar_icon()
        # wxPython ferme l'écran splash.
        wx.CallAfter(self.__close_splash, splash)
        # wxPython affiche un écran Tips.
        wx.CallAfter(self.__show_tips)
        # except Exception as e:
        #     print(
        #         "application.py: Erreur lors de l'initialisation de l'application: %s",
        #         str(e),
        #     )
        #     logging.error(
        #         "application.py: Erreur lors de l'initialisation de l'application: %s",
        #         str(e),
        #     )
        #     return False
        # self.mainwindow.Show()  # Ré-affiche la fenêtre principale pour éviter de voir les scintillements ! Ne fonctionne pas !
        log.info(
            "Application.init : Composants de l'application initialisés. ✅Terminé"
        )

    def __check_file_lock_early(self):
        """Check file lock before main window creation.

        This avoids GTK dialog/focus issues by showing any lock dialogs
        before any windows exist.
        """
        from taskcoachlib import persistence, meta

        # Get filename from args or last file
        if self._args:
            log.debug(
                f"Application.__check_file_lock_early : Checking lock for file from args: {self._args[0]}"
            )
            filename = self._args[0]
        else:
            filename = self.settings.get("file", "lastfile")
            log.debug(
                f"Application.__check_file_lock_early : Checking lock for last file: {filename}"
            )
        log.debug(
            f"Application.__check_file_lock_early : filename to check for lock: {filename}"
        )

        if not filename or not os.path.exists(filename):
            self.__early_lock_result = None
            log.debug(
                "Application.__check_file_lock_early : No file to check for lock."
            )
            return

        # Try to check if file is locked
        lock_file_path = filename + ".lock"
        try:
            import fasteners

            lock = fasteners.InterProcessLock(lock_file_path)
            acquired = lock.acquire(blocking=False)
            log.debug(
                f"Application.__check_file_lock_early : Lock file path: {lock_file_path}, acquired: {acquired}"
            )
            if acquired:
                # Not locked - release and proceed normally
                lock.release()
                self.__early_lock_result = "ok"
                # return
            else:
                # File is locked - show dialog BEFORE main window
                result = wx.MessageBox(
                    _("""Cannot open %s because it is locked.

This means either that another instance of TaskCoach
is running and has this file opened, or that a previous
instance of Task Coach crashed. If no other instance is
running, you can safely break the lock.

Break the lock?""") % filename,
                    _("%s: file locked") % meta.name,
                    style=wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
                )
                if result == wx.YES:
                    self.__early_lock_result = "break"
                else:
                    # User said No - don't open file, start with empty/new
                    self.__early_lock_result = "skip"
            log.debug(
                f"Application.__check_file_lock_early : User chose to {'break' if self.__early_lock_result == 'break' else 'skip'} the lock."
            )
        except Exception:
            # Lock check failed (e.g., network drive) - proceed normally
            self.__early_lock_result = "ok"
            log.debug(
                f"Application.__check_file_lock_early : Lock check failed with exception, proceeding with result: {self.__early_lock_result}"
            )
        log.debug(
            f"Application.__check_file_lock_early : Final early lock result: {self.__early_lock_result}"
        )

    def __init_config(self, load_settings):
        """Fonction-méthode d'initialisation de la configuration.

        Args :
            load_settings (bool) : Charger les paramètres de l'application.
        """
        try:
            # from taskcoachlib import config  # Settings est importé au début

            ini_file = self._options.inifile if self._options else None
            # est-ce qu'il existe un fichier inifile ? si non load_settings is False !
            # AttributeError: 'Values' object has no attribute 'inifile'
            # AttributeError: 'Namespace' object has no attribute 'inifile'
            # pylint: disable=W0201
            # self.settings = config.Settings(load_settings, ini_file)  #
            # self.settings = Settings(load_settings, ini_file)  #
            self.settings = Settings(
                load_settings, ini_file, gui_used="wx"
            )  # avec wx, pas tk !
            # TODO : ini_file is None !
        except IOError or Exception as e:
            # print(
            #     "application.py: Erreur lors de la lecture du fichier de configuration: %s",
            #     str(e),
            # )
            log.error(
                "Application.__init_config :  Erreur lors de la lecture du fichier de configuration: %s",
                str(e),
            )
            raise

    def __init_language(self):
        """Initialisez la traduction actuelle."""
        try:
            from taskcoachlib import i18n

            i18n.Translator(
                self.determine_language(self._options, self.settings)
            )
        except Exception as e:
            # print(
            #     "application.py: Erreur lors de l'initialisation de la langue: %s",
            #     str(e),
            # )
            log.error(
                "Application.__init_language : Erreur lors de l'initialisation de la langue: %s",
                str(e),
            )

    def __post_gui_init(self):
        """Initialisation dépendante du GUI (appelée après wx prêt)."""
        self.is_dark_theme = detect_dark_theme()

    @staticmethod
    def determine_language(
        options, settings, locale=locale
    ):  # pylint: disable=W0621
        # Shadows name 'locale' from outer scope
        """Détermine la langue locale utilisée.

        Args :
            options : Options de la ligne de commande.
            settings : Paramètres de l'application.
            locale : Module locale (par défaut, le module locale standard).

        Returns :
            str : La langue locale à utiliser.
        """
        language = None
        if options:
            # User specified language or .po file on command line
            language = options.pofile or options.language
        if not language:
            # Get language as set by the user via the preferences dialog
            language = settings.get("view", "language_set_by_user")
        if not language:
            # Get language as set by the user or externally (e.g. PortableApps)
            language = settings.get("view", "language")
        if not language:
            # # Use the user's locale
            # language = locale.getdefaultlocale()[0]
            # # language = locale.getlocale()[0]
            # Note: locale.getdefaultlocale() is deprecated since Python 3.11
            # and doesn't reliably read LANG on Linux. We check env vars directly.
            language = os.environ.get("LANG", os.environ.get("LC_ALL", ""))
            # if language == "C":
            #     # TODO: essayer:
            #     # locale.setlocale(locale.LC_ALL, "C")
            #     # language = locale.setlocale(locale.LC_ALL, "C")
            #     language = None
            if language:
                # Strip encoding suffix (e.g., "de_DE.UTF-8" -> "de_DE")
                language = language.split(".")[0]
                if not language or language == "C" or language == "POSIX":
                    language = None
        if not language:
            # Fallback to locale.getlocale() which may work after setlocale
            try:
                language = locale.getlocale(locale.LC_MESSAGES)[0]
                if language == "C" or language == "POSIX":
                    language = None
            except Exception:
                language = None
        if not language:
            # Fall back on what the majority of our users use
            language = "en_US"
        return language

    def __init_domain_objects(self):
        """Fonction-méthode qui fournit aux objets de domaine pertinents
        un accès aux paramètres.
        """
        from taskcoachlib.domain import task, attachment

        task.Task.settings = self.settings
        attachment.Attachment.settings = self.settings

    def __init_application(self):
        """Fonction-méthode qui règle les paramètres nom et auteurs de l'application."""
        from taskcoachlib import meta

        # Attributs d'instance
        self.__wx_app.SetAppName(meta.name)
        self.__wx_app.SetVendorName(meta.author)
        # Set WM_CLASS for Linux app grouping (must match StartupWMClass in .desktop)
        self.__wx_app.SetClassName("taskcoach")
        # Set AppUserModelID for Windows 7+ taskbar grouping
        if operating_system.isWindows():
            try:
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "org.taskcoach.TaskCoach"
                )
            except (ImportError, AttributeError, OSError):
                pass  # Not on Windows or API not available

    def __init_spell_checking(self):
        """Fonction-méthode qui règle-initialise."""
        log.debug("Vérification orthographique initialisée")

        self.on_spell_checking(
            self.settings.getboolean("editor", "maccheckspelling")
        )
        pub.subscribe(
            self.on_spell_checking, "settings.editor.maccheckspelling"
        )

    def on_spell_checking(self, value):
        """Fonction-méthode qui utilise SystemOptions qui stocke les paires option/valeur que wxWidgets lui-même
        ou les applications peuvent utiliser pour modifier le comportement au moment de l'exécution.
        """
        # SystemOptions stocke les paires option/valeur que wxWidgets lui-même ou les applications
        # peuvent utiliser pour modifier le comportement au moment de l'exécution.
        if (
            operating_system.isMac()
            and not operating_system.isMacOsXMountainLion_OrNewer()
        ):
            # wx.SystemOptions.SetOptionInt("mac.textcontrol-use-spell-checker", value)
            wx.SystemOptions.SetOption(
                "mac.textcontrol-use-spell-checker", value
            )

    def __register_signal_handlers(self):
        """Fonction-méthode pour quitter à cause d'un signal.

        DESIGN NOTE (Twisted Removal - 2024):
        Previously used Twisted's reactor which properly handled SIGINT.
        Now using Python's signal module with direct cleanup.

        Key challenges with native wxPython:
        1. Python signal handlers only run when main thread has control
        2. GUI event loops block in C code, preventing signal delivery
        3. Must save settings before exit

        Solution:
        - Custom signal handler uses wx.CallAfter for clean shutdown
        - Periodic timer wakes event loop so Python can check signals
        """
        # if operating_system.isWindows():
        #     import win32api  # pylint: disable=F0401
        #
        #     def quit_adapter(*args):
        #         # Parameter 'args' value is not used
        #         # Le gestionnaire est appelé depuis quelque chose qui n'est pas le thread principal,
        #         # nous ne pouvons donc pas faire grand-chose en rapport avec wx.
        #         event = threading.Event()
        #
        #         def quit():
        #             # Shadows built-in name 'quit'
        #             try:
        #                 self.quitApplication()
        #             finally:
        #                 event.set()
        #
        #         wx.CallAfter(quit)
        #         event.wait()
        #         return True
        #
        #     win32api.SetConsoleCtrlHandler(quit_adapter, True)
        # else:
        import signal

        log.debug(
            "Application.__register_signal_handlers : Quitter à cause d'un signal !"
        )

        def handle_signal(signum, frame):
            """Handle SIGINT/SIGTERM by scheduling clean shutdown."""
            # Use CallAfter to run shutdown in the main event loop
            # This ensures proper cleanup of wx resources
            wx.CallAfter(self.quitApplication)

            # Register SIGINT/SIGTERM handlers for Unix
            if not operating_system.isWindows():
                signal.signal(signal.SIGINT, handle_signal)
                signal.signal(signal.SIGTERM, handle_signal)

                # Start a timer to periodically wake the event loop
                # This allows Python to check for pending signals
                self._signal_check_timer = wx.Timer()
                self._signal_check_timer.Start(500)  # Check every 500ms

            # NOTE: We intentionally do NOT use SetConsoleCtrlHandler on Windows.
            # According to Microsoft docs, if an app loads gdi32.dll or user32.dll
            # (which wxPython does), the handler doesn't receive CTRL_LOGOFF_EVENT
            # or CTRL_SHUTDOWN_EVENT. It can also cause shutdown issues.
            # Instead, we rely on wxPython's EVT_CLOSE and EVT_END_SESSION events.
            # See: https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler

        def quit_adapter(*args):
            """
            Fonction pour quitter l'application.

            Args :
                *args :

            Returns :
                La fonction-méthode pour quitter.
            """
            # Parameter 'args' value is not used
            log.debug(
                "Application.__register_signal_handlers.quit_adapter : Retourne la fonction pour quitter l'application."
            )
            return self.quitApplication()

        log.debug(
            "Application.__register_signal_handlers : Signale pour quitter l'application."
        )
        signal.signal(signal.SIGTERM, quit_adapter)
        if hasattr(signal, "SIGHUP"):
            # forced_quit = lambda *args: self.quitApplication(force=True)
            def forced_quit(*args):
                """
                Fonction pour forcer à quitter l'application.

                Args :
                    *args :

                Returns :
                    La fonction-méthode pour quitter avec l'option force.
                """
                # Parameter 'args' value is not used
                log.debug(
                    "Application.__register_signal_handlers.forced_quit : Force à quitter l'application."
                )
                return self.quitApplication(force=True)

            log.debug(
                "Application.__register_signal_handlers : Signale de forçage pour quitter l'application."
            )
            signal.signal(signal.SIGHUP, forced_quit)  # pylint: disable=E1101

    @staticmethod
    def __create_mutex():
        """Sous Windows, crée un mutex pour qu'InnoSetup puisse vérifier
        si l'application est en cours d'exécution."""
        if operating_system.isWindows():
            import ctypes
            from taskcoachlib import meta

            # # ctypes.windll.kernel32.CreateMutexA(None, False, meta.filename)
            # ctypes.windll.kernel32.CreateMutexW(
            #     None, False, meta.filename
            # )  # Use CreateMutexW for Unicode support
            try:
                # Try to open existing mutex to check if another instance is running
                mutex = ctypes.windll.kernel32.OpenMutexW(
                    0x1F0001, False, meta.filename
                )  # Use OpenMutexW for Unicode support
                if mutex:
                    ctypes.windll.kernel32.CloseHandle(mutex)
                    log.debug(
                        "Application.__create_mutex : Mutex already exists, another instance is running."
                    )
                else:
                    log.debug(
                        "Application.__create_mutex : No existing mutex, creating new one."
                    )
            except Exception as e:
                log.error(
                    "Application.__create_mutex : Error checking/creating mutex: %s",
                    str(e),
                )

    def __create_task_bar_icon(self):
        """Fonction-Méthode pour créer une icône avec menu dans la barre de tâche."""
        # Le problème est effectivement que TaskBarIcon n'est pas
        # une sous-classe de wx.Window, et les menus wxPython
        # (comme ceux gérés par UICommandContainerMixin)
        # sont conçus pour être associés à des wx.Window.
        if self.__can_create_task_bar_icon():
            from taskcoachlib.gui import taskbaricon, menu

            # Use factory function to get the appropriate icon type
            # (AppIndicator on Wayland, wx.adv.TaskBarIcon otherwise)
            self.taskBarIcon = taskbaricon.TaskBarIcon(
                self.mainwindow,  # pylint: disable=W0201
                self.taskFile.tasks(),
                self.settings,
            )
            # self.taskBarIcon.setPopupMenu(
            #     menu.TaskBarMenu(
            #         self.taskBarIcon,
            #         self.settings,
            #         self.taskFile,
            #         self.mainwindow.viewer,
            #     )
            # )
            self.taskBarIcon.setPopupMenu(
                menu.TaskBarMenu(
                    # self.taskBarIcon,
                    self.mainwindow,  # Passer self.mainwindow au lieu de self.taskBarIcon.
                    self.settings,
                    self.taskFile,
                    self.mainwindow.viewer,
                    # self.mainwindow.__dict__.get("viewer"),  # TODO : essayer ceci
                )
            )
            # En passant self.mainwindow à TaskBarMenu,
            # nous fournissons au menu une référence à une instance de wx.Window,
            # ce qui satisfait les exigences de wx.Menu et UICommandContainerMixin.
            # L'affichage du menu est toujours géré correctement par TaskBarIcon
            # en utilisant self.PopupMenu(), car c'est la manière appropriée
            # d'afficher un menu contextuel pour une icône de barre des tâches.
            # Cohérence : S'Assurer que l'utilisation de self._window dans Menu
            # et UICommandContainerMixin est cohérente avec le fait
            # qu'il peut maintenant s'agir de la fenêtre principale
            # et non de l'icône de la barre des tâches.

    # @staticmethod
    def __can_create_task_bar_icon(self):
        """Fonction qui définit si une icône de barre de tâche peut être créée.

        Returns :
            bool
        """
        # Le problème est effectivement que TaskBarIcon n'est pas
        # une sous-classe de wx.Window, et les menus wxPython
        # (comme ceux gérés par UICommandContainerMixin)
        # sont conçus pour être associés à des wx.Window.
        try:
            from taskcoachlib.gui import (
                taskbaricon,
            )  # pylint: disable=W0612  # noqa: F401

            return True
            # except:
        except ImportError:
            return False  # pylint: disable=W0702

    @staticmethod
    def __close_splash(splash):
        """Fonction-méthode si splash, ferme et le détruit."""
        if splash:
            splash.Destroy()

    def __show_tips(self):
        """Fonction-méthode d'affichage des fenêtres d'astuces."""
        if self.settings.getboolean("window", "tips"):
            from taskcoachlib import help  # pylint: disable=W0622

            help.showTips(self.mainwindow, self.settings)

    def __warn_user_that_ini_file_was_not_loaded(self):
        """Fonction-méthode pour avertir l'utilisateur que le fichier ini n'a pas été démarré."""
        from taskcoachlib import meta

        reason = self.settings.get("file", "inifileloaderror")
        log.warning("Fichier ini non chargé : %s", reason)
        wx.MessageBox(
            _("Couldn't load settings from TaskCoach.ini:\n%s") % reason,
            # _(f"Couldn't load settings from TaskCoach.ini:\n{reason}"),
            _("%s file error") % meta.name,
            style=wx.OK | wx.ICON_ERROR,
        )
        # _(f"{meta.name} file error"), style=wx.OK | wx.ICON_ERROR)
        self.settings.setboolean("file", "inifileloaded", True)  # Reset

    def displayMessage(self, message):
        """Fonction-méthode pour afficher le message."""
        # self.mainwindow.displayMessage(message)
        # Guard against deleted mainwindow during shutdown
        if getattr(self, "_quitting", False):
            return
        try:
            self.mainwindow.displayMessage(message)
        except RuntimeError:
            pass  # MainWindow C++ object already deleted

    def on_end_session(self):
        """Fonction de fin de session.

        Termine la session de l'application en sauvegardant les paramètres et l'état avant la fermeture.

        Raises :
            Exception : Une exception peut être levée si la fermeture de l'application échoue.
        """
        # self.mainwindow.setShutdownInProgress()
        # self.quitApplication(force=True)
        log.debug(
            "Application.on_end_session : Essaie de terminer la session et fermer l'application."
        )
        try:
            self.mainwindow.setShutdownInProgress()
            self.quitApplication(force=True)
        except Exception as e:
            # print(
            #     "application.py: Erreur lors de la fermeture de la session: %s", str(e)
            # )
            log.exception(
                f"Application : Erreur lors de la fermeture de la session : {e}"
            )

    def on_reopen_app(self):
        """Fonction-méthode pour rouvrir l'application."""
        self.taskBarIcon.onTaskbarClick(None)

    def save_all_settings(self):
        """Save all settings to disk. Called on normal exit and signal handlers.

        This is the single place for saving settings, ensuring consistency
        between normal close, Ctrl-C, and other exit paths.
        """
        try:
            # Remember what the user was working on
            if hasattr(self, "taskFile"):
                self.settings.set(
                    "file", "lastfile", self.taskFile.lastFilename()
                )
            # Save window position, size, perspective
            if hasattr(self, "mainwindow"):
                self.mainwindow.save_settings()
            # Write settings to disk
            self.settings.save()
            # Release ini file lock after saving
            self.settings.release_ini_lock()
        except Exception:
            pass  # Best effort - don't prevent exit

    def _stopAllTimers(self):
        """Stop all known timers to prevent crashes during shutdown.

        Timer events can be delivered after frames are destroyed but before
        the program ends, causing access violations on Windows.
        See: https://github.com/wxWidgets/Phoenix/issues/429
        """
        import sys

        # Stop signal check timer
        if hasattr(self, "_signal_check_timer") and self._signal_check_timer:
            try:
                self._signal_check_timer.Stop()
            except Exception:
                pass

        # Stop all wx.Timer instances we can find
        # Walk through all top-level windows and their children
        def stop_timers_in_window(window):
            if window is None:
                return
            # Check for timer attributes
            for attr_name in [
                "__timer",
                "_timer",
                "timer",
                "_sizeTimer",
                "_refreshTimer",
                "_dragTimer",
                "_findTimer",
                "_editTimer",
                "__tmr",
                "scheduledStatusDisplay",
                "_globalTimer",
            ]:
                # Try both public and name-mangled private attributes
                for prefix in ["", "_" + window.__class__.__name__]:
                    full_name = prefix + attr_name
                    timer = getattr(window, full_name, None)
                    if timer is not None and hasattr(timer, "Stop"):
                        try:
                            if (
                                hasattr(timer, "IsRunning")
                                and timer.IsRunning()
                            ):
                                timer.Stop()
                        except Exception:
                            pass
            # Recurse into children
            if hasattr(window, "GetChildren"):
                try:
                    for child in window.GetChildren():
                        stop_timers_in_window(child)
                except Exception:
                    pass

        # Stop timers in all top-level windows
        for window in wx.GetTopLevelWindows():
            stop_timers_in_window(window)

    def quitApplication(self, force=False):
        """Fonction-méthode pour quitter l'application.

        Quitte l'application en sauvegardant les paramètres et l'état de l'application.

        Args :
            force (bool) : Si True, force l'arrêt de l'application sans demander de confirmation.

        Returns :
            bool : True si l'application a été arrêtée avec succès, False sinon.
        """
        # Voir https://pythonhosted.org/wxPython/window_deletion_overview.html#window-deletion
        log.info(
            "Application.quitApplication : Début de la Fermeture de l'application"
        )
        # Prevent re-entry - quitApplication may be called multiple times
        # (e.g., from window close, signal handler, console ctrl handler)
        if getattr(self, "_quitting", False):
            return True
        self._quitting = True

        if not self.iocontroller.close(force=force):
            return False
        # # Rappelez-vous sur quoi l'utilisateur travaillait :
        # self.settings.set("file", "lastfile", self.taskFile.lastFilename())
        # self.mainwindow.save_settings()
        # self.settings.save()
        self.save_all_settings()
        if self.taskFile:
            self.taskFile.stop()
        log.info("Avant suppression de l'icône barre de tâches")
        if hasattr(self, "taskBarIcon"):
            self.taskBarIcon.RemoveIcon()
            self.taskBarIcon.Destroy()
        if self.mainwindow.bonjourRegister is not None:
            self.mainwindow.bonjourRegister.stop()
        # Stop notification timers to prevent crashes during shutdown
        from taskcoachlib.notify.notifier_universal import NotificationCenter

        NotificationCenter().cleanup()
        from taskcoachlib.domain import date

        date.Scheduler().shutdown()
        # self.__wx_app.ProcessIdle()  # wxApp/ProcessIdle is not in application.py but used in tests !
        # wx.GUIEventLoop.GetActive().ProcessIdle()  # wxApp/ProcessIdle is not in application.py but used in tests !
        wx.EventLoop.GetActive().ProcessIdle()

        # For PowerStateMixin
        log.info("Avant appel à mainwindow.OnQuit")
        self.mainwindow.OnQuit()

        if operating_system.isGTK() and self.sessionMonitor is not None:
            self.sessionMonitor.stop()

        # Stop all timers before closing windows to prevent crashes
        # See: https://github.com/wxWidgets/Phoenix/issues/429
        self._stopAllTimers()

        if isinstance(sys.stdout, RedirectedOutput):
            sys.stdout.summary()

        # log.info("Avant appel stopTwisted()")
        # log.debug("Application.quitApplication : Essaie d'arrêter Twisted.")
        # try:
        #     self.stopTwisted()
        # except Exception as e:
        #     # print(
        #     #     "application.py:Erreur lors de l'arrêt de Twisted: %s", str(e)
        #     # )
        #     log.error(
        #         f"Application.quitApplication : Erreur lors de l'arrêt de Twisted: {str(e)}",
        #         exc_info=True,
        #     )

        # End any modal dialogs before closing - modal dialogs have their own
        # nested event loops that prevent ExitMainLoop() from working
        has_modal_dialogs = False
        for window in wx.GetTopLevelWindows():
            if isinstance(window, wx.Dialog) and window.IsModal():
                has_modal_dialogs = True
                window.EndModal(wx.ID_CANCEL)

        # Explicitly close the main window to trigger exit.
        # Set shutdown flag so onClose() won't veto or recurse into quitApplication.
        self.mainwindow.setShutdownInProgress()
        self.mainwindow.Close()

        log.info("Avant appel sys.exit()")
        if self.mainwindow:
            try:
                self.mainwindow.Destroy()
            except Exception as e:
                log.error(
                    f"Erreur lors de la destruction de la fenêtre principale: {e}"
                )
        log.info("Fenêtre principale détruite, appel de sys.exit()")

        if has_modal_dialogs:
            # Modal dialogs have nested event loops. Use ScheduleExit on the
            # main loop - it will exit when the nested modal loop terminates.
            # See: https://docs.wxpython.org/wx.EventLoopBase.html
            main_loop = wx.GetApp().GetMainLoop()
            if main_loop:
                main_loop.ScheduleExit(0)
            else:
                wx.GetApp().ExitMainLoop()
        else:
            # Force MainLoop to exit in case something is keeping it alive
            # See: https://discuss.wxpython.org/t/wxpython-app-hanging-not-ending-mainloop/29797
            wx.GetApp().ExitMainLoop()

        def _stack_for_thread(t, frames=None):
            import sys
            import traceback

            frames = frames or sys._current_frames()
            if not t.is_alive():
                return "Thread not alive"
            ident = t.ident
            if ident is None:
                return "Thread alive but no ident (not started?)"
            frame = frames.get(ident)  # Modified line
            if frame is None:
                return "Thread alive but no frame available (it may have just exited)"
            try:
                return "".join(traceback.format_stack(frame))
            except Exception as e:
                return f"Unable to format stack: {e}"

        log.info("Threads actifs avant sys.exit(): %s", threading.enumerate())
        frames = sys._current_frames()
        for t in threading.enumerate():
            log.debug(
                f"Thread: {t.name}, Daemon: {t.daemon}, Class: {type(t)}"
            )
            # log.debug(
            #     f"Stack for thread {t.name}:\n{''.join(traceback.format_stack(sys._current_frames()[t.ident])) if t.is_alive() else 'Thread not alive'}"
            # )
            # frames = sys._current_frames()
            # if t.is_alive():
            #     if t.ident is not None and frames.get(t.ident) is not None:
            #         # Ce genre de protection est recommandé dès qu’on interroge sys._current_frames()
            #         # pour diagnostiquer des threads (cf. documentation/ressources sur threading & wxPython)
            #         try:
            #             stack = "".join(
            #                 traceback.format_stack(frames[t.ident])
            #             )
            #         except Exception as exc:
            #             stack = f"Unable to format stack: {exc}"
            #     else:
            #         stack = "Thread alive but no frame available (it may have just exited)"
            # else:
            #     stack = "Thread not alive"
            # log.debug(f"Stack for thread {t.name}:\n{stack}")
            # frames = sys._current_frames()
            stack = _stack_for_thread(t, frames)
            # msg = f"Stack for thread {t.name}:\n{stack}"
            # log.debug(msg)
            # Utiliser la méthode de log avec paramètres (évite le formatage inutile si le niveau est désactivé).
            # J’ai mis log.debug("...", t.name, stack) au lieu de f-strings
            # pour laisser logging gérer l’encodage et la mise en forme.
            # Cela prévient aussi d’éventuels problèmes
            # si stack contient des caractères non imprimables/encodages inattendus.
            log.debug("Stack for thread %s:\n%s", t.name, stack.rstrip())
            # Supprimer les newlines superflus en fin de stack
            # traceback.format_stack(frame) renvoie des lignes finissant par '\n',
            # ce qui peut laisser une ligne vide après l’affichage.
            # Utiliser stack.rstrip() évite la ligne vide si cela vous gêne.

        log.debug(
            "Application.quitApplication : Essaie de quitter proprement l'application avec sys.exit()."
        )
        # sys.exit()  # Quitter proprement l'application
        #
        # Toutes les étapes avant sys.exit() doivent être exécutées sans erreur (fermeture du fichier de tâches, sauvegarde des paramètres, suppression de l’icône de la barre, etc).
        # Si iocontroller.close(force=force) retourne False, la méthode quitte sans jamais appeler sys.exit().
        # Si une exception est levée avant d’atteindre sys.exit(), la fermeture peut échouer.
        # S’il existe des threads ou des boucles événementielles Twisted encore actives, la fermeture peut être bloquée.
        # Raisons fréquentes pour lesquelles la fenêtre ne se ferme pas :
        #
        #     iocontroller.close(force=force) retourne False
        #     Cela signifie que la fermeture a été annulée (ex : dialogue de confirmation, fichier non sauvegardé, etc).
        #
        #     Un bug ou une exception dans la séquence de fermeture
        #     Si une exception est levée, elle peut empêcher l’appel à sys.exit().
        #
        #     La boucle d’événements Twisted/Wx n’est pas arrêtée
        #     Si le réacteur Twisted ne s’arrête pas, la fenêtre principale peut rester ouverte.
        #
        #     Le bouton "Quitter" n’appelle pas vraiment quitApplication.
        #     Il faut vérifier que l’action du bouton "Quitter" déclenche bien cette méthode.

        # Même si tu appelles sys.exit(), il existe des situations (notamment sous Linux/GTK) où :
        #
        #     Le process ne se termine pas si la boucle d’événements wxPython n’est pas proprement arrêtée.
        #     Un thread, timer, ou callback wx/Twisted reste actif et garde le process vivant.

        # 1. Problème d’intégration wxPython/Twisted
        #
        # Même si tu appelles sys.exit(), il existe des situations (notamment sous Linux/GTK) où :
        #
        #     Le process ne se termine pas si la boucle d’événements wxPython n’est pas proprement arrêtée.
        #     Un thread, timer, ou callback wx/Twisted reste actif et garde le process vivant.
        #
        # 2. sys.exit() dans un callback wx
        #
        # Si tu appelles sys.exit() dans un contexte qui n’est pas le thread principal, ou dans un callback wx, cela peut ne pas tuer le process (ou lever une exception SystemExit qui est attrapée “quelque part”).
        # Il est parfois recommandé d’appeler directement à la place de sys.exit():
        # --- Fermeture forcée du process ---
        # Nous utilisons os._exit(0) au lieu de sys.exit() pour garantir une terminaison immédiate du process.
        # En effet, Twisted crée un thread worker interne non-daemon ("Thread-4 (work)") qui reste vivant
        # même après reactor.stop() et threadpool.stop(). Tant qu'il existe, sys.exit() ne termine pas
        # le process Python (car tous les threads non-daemon doivent être morts pour cela).
        # Comme tout nettoyage/sauvegarde a déjà été fait à ce stade, il n'y a pas de risque de fuite.
        # Voir : https://github.com/freedomsha/taskcoach/issues/<ton-issue> pour le détail du diagnostic.
        os._exit(
            0
        )  # TODO : Attention, c'est brutal ! Revenir à sys.exit() dès que possible.

        # Si ça ferme tout instantanément,
        # c’est bien un problème de threads/boucles non stoppés proprement dans wx/Twisted.
        # 3. Destruction de la fenêtre wx
        #
        # Si la fenêtre principale n’est pas explicitement détruite avant la fin du process, wxPython peut garder le process vivant.
        # Tu as ajouté mainwindow.Destroy(), c’est bien, mais parfois il faut forcer la destruction :
        # Python
        #
        # if self.mainwindow:
        #     self.mainwindow.Close(True)
        #     self.mainwindow.Destroy()

        # 4. Threads ou timers en arrière-plan
        #
        # Des threads Python ou des timers wx peuvent garder le process vivant. Vérifie si tu utilises des threads, timers, ou des callbacks récurrents dans Task Coach.
        return True  # This code is unreachable

    @classmethod
    def delete_instance(cls):
        """Réinitialise proprement le singleton pour les tests unitaires."""
        if cls in cls._instances:
            del cls._instances[cls]
        if wx.GetApp():
            wx.GetApp().ExitMainLoop()
