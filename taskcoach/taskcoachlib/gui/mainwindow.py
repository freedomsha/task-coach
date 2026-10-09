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

    License: GNU General Public License (GPL) v3 or later.
    Description: Cette classe définit la fenêtre principale de l'application pour Task Coach.
    Imports: Various libraries like wxPython, ctypes, pubsub, and taskcoachlib modules.


Module mainwindow.py - Fenêtre principale de Task Coach.

Ce module définit la fenêtre principale de l'application Task Coach.
Il gère l'interface graphique, la gestion des événements,
ainsi que des fonctionnalités telles que la gestion de la barre d'outils, de la barre de statut, et des visionneuses de tâches.

Classes :
    - MainWindow : Classe principale représentant la fenêtre de l'application.

Fonctionnalités clés :

    Initialisation :
        Hérite des classes PowerStateMixin, BalloonTipManager et AuiManagedFrameWithDynamicCenterPane.
        Initialise les variables membres telles que iocontroller, taskFile, les paramètres et les indicateurs d'état sale et d'arrêt.
        Lie les événements comme EVT_CLOSE, EVT_ICONIZE et EVT_SIZE.
        Crée des composants de fenêtre tels que les visionneuses, la barre d'état, la barre de menus et le contrôleur de rappel (en utilisant des méthodes comme _create_window_components).
        Restaure la perspective à partir des paramètres (si disponible).
        Définit la fenêtre titre basé sur le nom de fichier et l'état sale.
    Gestion des fenêtres :
        Fournit des méthodes pour ajouter des volets, afficher/masquer la barre d'outils et la barre d'état et enregistrer l'état de la fenêtre (perspective, position).
        Gère les événements comme la fermeture de la fenêtre, iconiser et redimensionner.
    Interaction avec la visionneuse :
        Fournit des méthodes pour faire avancer la sélection et obtenir le nombre de spectateurs.
        Interagit avec ViewerContainer pour gérer différentes vues de tâches.
    Gestion de l'alimentation :
        Répond à l'état d'alimentation modifie (activé/désactivé) et envoie des notifications.
    Synchronisation iPhone :
        Crée un cadre de progression pour la synchronisation iPhone.
        Définit les méthodes de gestion des types de synchronisation iPhone, des échecs de protocole et de la modification/ajout/suppression de tâches et de catégories. .

Remarques supplémentaires :

    Le code utilise pubsub pour la communication entre les composants.
    Plusieurs méthodes liées à la synchronisation de l'iPhone semblent être commentées ou marquées comme méthodes statiques, ce qui suggère qu'elles pourraient ne pas l'être. activement utilisé.
    La classe utilise diverses classes d'assistance de taskcoachlib pour des fonctionnalités spécifiques.
"""

import ctypes
import logging
import wx

# try:
#    from ..thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub

# from taskcoachlib.thirdparty import aui
# import aui2 as aui
import wx.lib.agw.aui as aui

# from builtins import str
from taskcoachlib import (
    application,
    meta,
    widgets,
    operating_system,
)  # pylint: disable=W0622

# from taskcoachlib.application.application import detect_dark_theme
from taskcoachlib.config.settings import Settings

# from . import viewer, toolbar, uicommand, remindercontroller, \
# !!! éviter les boucles d'import !!!
from taskcoachlib.gui import (
    artprovider,
    idlecontroller,
    # menu,  # crée ImportError: cannot import name 'CheckableTaskViewer' from partially initialized module 'taskcoachlib.gui.viewer.task' (most likely due to a circular import) (*/taskcoach/taskcoachlib/gui/viewer/task.py)
    remindercontroller,
    status,
    timer as globaltimer,
    toolbar,
    # uicommand,
    viewer,
    windowdimensionstracker,
)
from taskcoachlib.gui.uicommand import uicommand

# from taskcoachlib.gui.uicommand import base_uicommand
# from taskcoachlib.gui.uicommand import settings_uicommand
# from taskcoachlib.gui.uicommand import uicommandcontainer
# from .viewer import addViewers, ViewerContainer, viewerTypes
from taskcoachlib.gui.newid import IdProvider

# from .viewer import container, factory
from taskcoachlib.gui.dialog.iphone import IPhoneSyncTypeDialog
from taskcoachlib.gui.dialog.xfce4warning import XFCE4WarningDialog
from taskcoachlib.gui.dialog.editor import Editor
from taskcoachlib.gui.iphone import IPhoneSyncFrame
from taskcoachlib.i18n import _
from taskcoachlib.powermgt import PowerStateMixin
from taskcoachlib.help.balloontips import BalloonTipManager

log = logging.getLogger(__name__)


def turn_on_double_buffering_on_windows(window):
    # # Cela a en fait un effet négatif lorsque Aero est activé...
    # from ctypes import wintypes
    #
    # dll = ctypes.WinDLL("dwmapi.dll")
    # ret = wintypes.BOOL()
    # if dll.DwmIsCompositionEnabled(ctypes.pointer(ret)) == 0 and ret.value:
    #     return
    # import win32gui
    # import win32con  # pylint: disable=F0401
    #
    # exstyle = win32gui.GetWindowLong(window.GetHandle(), win32con.GWL_EXSTYLE)
    # exstyle |= win32con.WS_EX_COMPOSITED
    # win32gui.SetWindowLong(window.GetHandle(), win32con.GWL_EXSTYLE, exstyle)
    pass


class MainWindow(
    PowerStateMixin,
    BalloonTipManager,
    widgets.AuiManagedFrameWithDynamicCenterPane,
):
    """
    Classe représentant la fenêtre/frame principale de Task Coach.

    Cette classe gère l'interface utilisateur de l'application,
    y compris les barres d'outils, les menus, la gestion des tâches,
    la synchronisation avec des dispositifs externes comme l'iPhone, et bien plus encore.

    Attributs :
        iocontroller : Contrôleur d'entrée/sortie pour les fichiers.
        taskFile : Fichier de tâches en cours.
        settings : Paramètres utilisateur.
        viewer : Conteneur des visionneuses de tâches.
        reminderController : Gère les rappels de tâches.
        bonjourRegister : Service Bonjour pour la synchronisation iPhone.
        bonjourAcceptor : Accepte les connexions iPhone.
        _idleController : Gère les actions d'inactivité (suivi du temps).

    Méthodes :
        __init__(self, iocontroller, taskFile, settings, *args, **kwargs) :
            Initialise la fenêtre principale avec les paramètres fournis.
        onClose (self, event) :
            Gère la fermeture de la fenêtre.
        onIconify (self, event) :
            Gère la minimisation de la fenêtre.
        onResize (self, event) :
            Gère le redimensionnement de la fenêtre.
        setShutdownInProgress (self) :
            Marque que l'arrêt de l'application est en cours.
        advanceSelection (self, forward) :
            Fait avancer la sélection des tâches dans les visionneuses.
        viewerCount (self) :
            Retourne le nombre de visionneuses actives.
        createToolBarUICommands (self) :
            Crée les commandes UI à afficher dans la barre d'outils.
        showStatusBar (self, value=True) :
            Affiche ou masque la barre de statut.
        save_settings (self) :
            Sauvegarde les paramètres de la fenêtre.
        closeEditors (self) :
            Ferme tous les éditeurs ouverts.
        restore (self, event) :
            Restaure la fenêtre depuis la barre des tâches.
        showToolBar (self, value) :
            Affiche ou masque la barre d'outils.
        checkXFCE4 (self) :
            Vérifie si l'utilisateur utilise XFCE4 pour afficher un avertissement.
        getToolBarPerspective (self) :
            Retourne la perspective de la barre d'outils.
        saveToolBarPerspective (self, perspective) :
            Sauvegarde la perspective de la barre d'outils.
        addPane (self, page, caption, name, floating=False) :
            Ajoute un volet à la fenêtre.
    """

    def __init__(
        self, iocontroller, taskFile, settings: Settings, *args, **kwargs
    ):
        """
        Initialise la fenêtre principale de Task Coach avec les paramètres fournis.

        Cette méthode configure les variables membres, lie les événements, crée les composants de la fenêtre,
        et restaure la perspective de la fenêtre depuis les paramètres.

        Attributs :
            iocontroller (IOController) : Contrôleur d'entrée/sortie pour la gestion des fichiers.
            taskFile (TaskFile) : Fichier de tâches contenant les tâches, catégories, et efforts.
            settings (Settings) : Paramètres utilisateur de l'application.
            __filename (str) : Nom du fichier de tâches actuellement ouvert (None par défaut).
            __dirty (bool) : Indicateur indiquant si le fichier a été modifié sans être sauvegardé (initialisé à False).
            __shutdown (bool) : Indicateur indiquant si l'application est en cours d'arrêt (initialisé à False).
            bonjourRegister : Service Bonjour pour la synchronisation avec un iPhone (None par défaut).
            bonjourAcceptor : Accepte les connexions Bonjour pour la synchronisation (None par défaut).
            _idleController : Contrôleur d'inactivité utilisé pour suivre les efforts sur les tâches.

        Composants créés :
            - Barre d'état (status bar).
            - Barre de menus (menu bar).
            - Visionneuses (pour afficher les tâches, catégories, etc.).
            - Composants pour le suivi des rappels de tâches.

        Méthodes appelées :
            - `_create_window_components` : Crée les composants de la fenêtre (barres d'outils, barre d'état, etc.).
            - `__init_window_components` : Initialise les composants supplémentaires après leur création.
            - `__init_window` : Restaure la perspective de la fenêtre à partir des paramètres sauvegardés.
            - `__register_for_window_component_changes` : S'enregistre pour les événements de changement de composants de la fenêtre.
            - `checkXFCE4` : Vérifie si le gestionnaire de fenêtres XFCE4 est utilisé pour afficher un avertissement.

        Liens d'événements :
            - EVT_CLOSE : Lie la fermeture de la fenêtre à la méthode `onClose`.
            - EVT_ICONIZE : Gère la minimisation de la fenêtre avec `onIconify`.
            - EVT_SIZE : Gère le redimensionnement de la fenêtre avec `onResize`.

        Args :
            iocontroller (IOController) : Contrôleur d'entrée/sortie pour gérer les fichiers.
            taskFile (TaskFile) : Fichier de tâches à manipuler.
            settings (Settings) : Paramètres utilisateur à appliquer à la fenêtre principale.
            *args, **kwargs : Arguments supplémentaires pour la fenêtre.
        """
        log.info("Début d'initialisation de MainWindow")
        self.__splash = kwargs.pop("splash", None)
        # Initialize with valid default size to prevent GTK warnings
        # The WindowDimensionsTracker will set the actual saved size/position
        if "size" not in kwargs:
            kwargs["size"] = (800, 600)
        # super(MainWindow, self).__init__(None, -1, '', *args, **kwargs)
        super().__init__(
            None, -1, "", *args, **kwargs
        )  # -1 est-ce height ? Non, c'est pour l'assignation d'id automatique.
        log.info(f"MainWindow : self.GetId() id={self.GetId()}")
        # Après il devrait y avoir self.mainwindow.Show(true) !(Voir start())
        # Active le double buffering pour éviter le scintillement des visionneuses sur Windows 7 et supérieur
        # if operating_system.isWindows7_OrNewer():
        #     turn_on_double_buffering_on_windows(self)

        self.__dimensions_tracker = (
            windowdimensionstracker.WindowDimensionsTracker(self, settings)
        )
        log.info(
            "MainWindow : Initialisation de WindowDimensionsTracker pour la gestion de la taille et de la position de la fenêtre."
        )
        # Attributs :
        self.iocontroller = iocontroller  # Contrôleur d'entrée/sortie pour la gestion des fichiers.
        self.taskFile = taskFile  # Fichier de tâches contenant les tâches, catégories, et efforts.
        self.settings = settings  # Paramètres utilisateur de l'application.
        self.__filename = None  # Nom du fichier de tâches actuellement ouvert (None par défaut).
        self.__dirty = False  # Indicateur indiquant si le fichier a été modifié sans être sauvegardé (initialisé à False).
        self.__shutdown = False  # Indicateur indiquant si l'application est en cours d'arrêt (initialisé à False).

        # Lie les événements à leurs gestionnaires
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_ICONIZE, self.onIconify)
        self.Bind(wx.EVT_SIZE, self.onResize)

        # Crée et initialise les composants de la fenêtre
        log.info(
            "MainWindow : Création et initialisation des composants de la fenêtre :"
        )
        self._create_window_components()  # Not private for test purposes, doit être précédé du réglage du menu :
        log.debug(
            "MainWindow : ✅ Création et initialisation des différents composants de la fenêtre effectuée."
        )
        # # Setting up the menu.
        # # filemenu= wx.Menu()
        # Voir menu.MainMenu
        # Ici, nous en avons plusieurs FileMenu, Editer, Actions... basés sur gui.menu.Menu (une surcharge de wx.Menu)
        # log.debug("MainWindow : Initialisation des composants principaux de la fenêtre (barre d'outils, barre d'état) et restauration de la perspective de la fenêtre:")
        self.__init_window_components()
        log.debug(
            "MainWindow : ✅ Initialisation des composants principaux de la fenêtre terminée et perspective de la fenêtre restaurée."
        )
        # log.debug("MainWindow : Initialisation de la fenêtre principale de Task Coach en définissant la disposition des composants:")
        try:
            self.__init_window()
        except Exception as e:
            log.exception(
                f"Problème avec __init__window() : {e}", exc_info=True
            )
        log.debug("MainWindow : ✅ Fenêtre principale Initialisée.")
        # log.debug("MainWindow : Enregistrement pour recevoir des notifications de changement de composants de fenêtre, comme les barres d'outils et les barres de statut:")
        self.__register_for_window_component_changes()
        log.debug(
            "MainWindow : ✅ Enregistrement effectué pour recevoir des notifications de changement de composants de fenêtre, comme les barres d'outils et les barres de statut."
        )
        log.debug("MainWindow : ✅ Composants de fenêtre créés")

        # Gère l'importation SyncML et affiche un avertissement si nécessaire
        if settings.getboolean("feature", "syncml"):
            try:
                import taskcoachlib.syncml.core  # pylint: disable=W0612,W0404
            except ImportError:
                if settings.getboolean("syncml", "showwarning"):
                    dlg = widgets.SyncMLWarningDialog(self)
                    try:
                        if dlg.ShowModal() == wx.ID_OK:
                            settings.setboolean("syncml", "showwarning", False)
                    finally:
                        dlg.Destroy()

        # Attributs :
        # Gère la synchronisation avec un iPhone via Bonjour
        self.bonjourRegister = None  # Service Bonjour pour la synchronisation avec un iPhone (None par défaut).
        self.bonjourAcceptor = None  # Accepte les connexions Bonjour pour la synchronisation (None par défaut).
        self._registerBonjour()
        pub.subscribe(self._registerBonjour, "settings.feature.iphone")

        # Attribut :
        # Contrôleur d'inactivité utilisé pour suivre les efforts sur les tâches. :
        log.debug(
            "MainWindow: Initialise le contrôleur d'inactivité pour le suivi des efforts"
        )
        self._idleController = idlecontroller.IdleController(
            self, self.settings, self.taskFile.efforts()
        )
        # try:
        #     self._idleController.start()
        # except Exception as e:
        #     log.error(
        #         f"MainWindow : erreur d'initialisation d'inactivité : {e}",
        #         stack_info=True,
        #     )

        # Vérifie XFCE4 après l'initialisation complète
        log.debug("MainWindow : Appel de CallAfter(self.checkXFCE4).")
        wx.CallAfter(self.checkXFCE4)
        log.debug("MainWindow : CallAfter(self.checkXFCE4) passé avec succès.")

        # Gestionnaire d'événements global pour tous les événements de menu:
        # self.Bind(wx.EVT_MENU, self.onAnyMenu)

        # self.task_tree_viewer = self.create_task_tree_viewer()  # Créez le viewer
        # self.task_popup_menu = self.createTaskPopupMenu()  # Créez le menu ici
        # System theme change monitor (Windows/macOS)
        # self._lastDetectedDark = detect_dark_theme()
        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self._onSysColourChanged)
        self.manager.Update()
        log.info("MainWindow : ✅ Initialisé avec succès")

    # def create_task_tree_viewer(self):
    #     """Crée et retourne une instance de BaseTaskTreeViewer (ou une de ses sous-classes).
    #     Vous devrez peut-être ajuster ceci en fonction de votre configuration."""
    #     #  Ceci est une hypothèse. Vous devrez peut-être importer la classe concrète
    #     #  du viewer que vous utilisez.
    #     return viewer.task.BaseTaskTreeViewer(
    #         parent=self,  # Passez la MainWindow comme parent
    #         taskFile=self.taskFile,  # Assurez-vous d'avoir accès à taskFile
    #         settings=self.settings,  # et settings ici
    #         #  ... (autres arguments nécessaires au viewer)
    #         presentation=self.task_tree_viewer.presentation,
    #         efforts=self.taskFile.efforts(),
    #         categories=self.taskFile.categories(),
    #         taskViewer=self.task_tree_viewer
    #     )

    def onAnyMenu(self, event):
        """

        Args:
            event:

        Returns:
            None
        """
        log.debug(
            f"gui.mainwindow.MainWindow.onAnyMenu: Menu event triggered. ID: {event.GetId()}"
        )
        event.Skip()

    def _registerBonjour(self, value=True):
        """
        Enregistre ou supprime les services Bonjour pour la synchronisation avec un iPhone.

        Cette méthode gère l'enregistrement ou l'arrêt de la synchronisation avec un iPhone via Bonjour.
        Elle s'assure que les services Bonjour sont actifs uniquement si la fonctionnalité iPhone est activée dans les paramètres.
        En cas d'échec lors de l'enregistrement du service Bonjour, un message d'erreur est affiché.

        Attributs modifiés :
            bonjourRegister : Le service Bonjour actif, qui est utilisé pour la synchronisation avec un iPhone.
            bonjourAcceptor : Accepte les connexions Bonjour depuis un iPhone.

        Args :
            value (bool) : Indique si le service Bonjour doit être enregistré (True par défaut).

        Actions :
            - Si un service Bonjour est déjà actif, il est arrêté et nettoyé.
            - Si la fonctionnalité iPhone est activée dans les paramètres :
                - Tente de charger les modules `pybonjour` et `IPhoneAcceptor` pour la synchronisation.
                - Enregistre le service Bonjour et configure les gestionnaires de succès et d'erreur.
            - En cas d'échec du chargement de `pybonjour`, affiche une boîte de dialogue d'avertissement pour l'utilisateur.
        """
        log.info("MainWindow._registerBonjour : Enregistrement Bonjour lancé")
        if self.bonjourRegister is not None:
            # Si un service Bonjour est actif, on l'arrête et on nettoie
            self.bonjourRegister.stop()
            self.bonjourAcceptor.Close()
            self.bonjourRegister = self.bonjourAcceptor = None

        # Si la fonctionnalité iPhone est activée dans les paramètres
        if self.settings.getboolean("feature", "iphone"):
            # pylint: disable=W0612,W0404,W0702
            try:
                # Tente de charger les modules nécessaires pour la synchronisation iPhone
                from taskcoachlib.thirdparty import pybonjour
                from taskcoachlib.iphone import (
                    IPhoneAcceptor,
                    BonjourServiceRegister,
                )

                acceptor = IPhoneAcceptor(
                    self, self.settings, self.iocontroller
                )

                # Callback de succès lors de l'enregistrement du service Bonjour
                def success(reader):
                    self.bonjourRegister = reader
                    self.bonjourAcceptor = acceptor

                # Callback d'erreur lors de l'enregistrement du service Bonjour
                def error(reason):
                    acceptor.close()
                    wx.MessageBox(reason.getErrorMessage(), _("Error"), wx.OK)

                # Enregistre le service Bonjour et configure les callbacks
                BonjourServiceRegister(
                    self.settings, acceptor.port
                ).addCallbacks(success, error)

            except Exception as e:
                # Si le chargement échoue, affiche un avertissement pour l'utilisateur
                from taskcoachlib.gui.dialog.iphone import IPhoneBonjourDialog

                # log.error("Erreur Bonjour : %s", reason.getErrorMessage())
                log.error("Erreur Bonjour : %s", e)
                dlg = IPhoneBonjourDialog(self, wx.ID_ANY, _("Warning"))
                try:
                    dlg.ShowModal()
                finally:
                    dlg.Destroy()

    def checkXFCE4(self):
        """
        Vérifie si l'utilisateur utilise le gestionnaire de fenêtres XFCE4. Si c'est le cas,
        un avertissement est affiché à l'utilisateur, car XFCE4 peut causer des problèmes avec certaines fonctionnalités de Task Coach.
        """
        log.info("MainWindow : Vérification de l'utilisation de XFCE4.")
        if operating_system.isGTK():
            # mon = application.Application().sessionMonitor
            mon = wx.GetApp().sessionMonitor
            if (
                mon is not None
                and self.settings.getboolean("feature", "usesm2")
                and self.settings.getboolean("feature", "showsmwarning")
                and mon.vendor == "xfce4-session"
            ):
                dlg = XFCE4WarningDialog(self, self.settings)
                dlg.Show()

    def setShutdownInProgress(self) -> None:
        """
        Indique que le processus d'arrêt de l'application est en cours, afin d'éviter toute autre action durant cette phase.
        """
        log.info(
            "MainWindow.setShutdownInProgress : Le processus d'arrêt de l'application est en cours. Plus aucune action durant cette phase !"
        )
        self.__shutdown = True

    def _create_window_components(
        self,
    ) -> None:  # Not private for test purposes
        """
        Crée et initialise les différents composants de la fenêtre,
        comme les barres d'outils, les barres de statut, et les autres éléments de l'interface graphique.
        """
        log.debug(
            "MainWindow._create_window_components : création du conteneur pour les visionneuses."
        )
        # Freeze to prevent flickering during viewer creation
        self.Freeze()
        try:
            # Start global timer FIRST - other components subscribe to its events
            self._globalTimer = globaltimer.GlobalTimer(self)
            self._globalTimer.start()
            # ComputeStyles handles per-second polling for status + appearance SSOT updates
            from taskcoachlib.domain.base.appearance import ComputeStyles

            self._computeStyles = ComputeStyles(self.taskFile)

            self._create_viewer_container()
            log.debug(
                "MainWindow._create_window_components : Lance une classe-méthode pour ajouter des viewers."
            )
            viewer.addViewers(self.viewer, self.taskFile, self.settings)
            # viewer.factory.addViewers(self.viewer, self.taskFile, self.settings)
            # # Setting up the menu. :
            # # filemenu= wx.Menu()  # Devrait exister avant la création du menu ! (->Voir menu.MainMenu)
            # Ici, nous en avons plusieurs FileMenu, Editer, Actions... basés sur gui.menu.Menu (une surcharge de wx.Menu)
            log.debug(
                "MainWindow._create_window_components : création de la barre de status."
            )
            self._create_status_bar()  # Crée la barre de status en bas de la fenêtre.
            log.debug(
                "MainWindow._create_window_components : création de la barre de menu."
            )
            self.__create_menu_bar()  # Crée la barre de menu.
            log.debug(
                "MainWindow._create_window_components : création du contrôleur de rappel des tâches et efforts."
            )
            self.__create_reminder_controller()
            log.debug(
                "MainWindow._create_window_components : rafraîchissement !"
            )
            # self.Refresh()
        finally:
            self.Thaw()
        log.debug(
            "MainWindow._create_window_components : utilisation de CallAfter"
        )
        wx.CallAfter(self.viewer.componentsCreated)
        log.debug(
            "MainWindow._create_window_components : CallAfter passé ! Terminé !"
        )

    def _create_viewer_container(
        self,
    ) -> None:  # Not private for test purposes
        # pylint: disable=W0201
        """
        Crée le conteneur pour les visionneuses (tâches, notes, etc.) dans la fenêtre principale.
        Ce conteneur gère l'affichage et l'organisation des différentes visionneuses.
        """
        log.debug(
            "MainWindow._create_viewer_container : utilise viewer.container.ViewerContainer pour créer le conteneur de visionneuses."
        )
        # self.viewer = viewer.ViewerContainer(self, self.settings)
        self.viewer = viewer.container.ViewerContainer(self, self.settings)
        # self.viewer = container.ViewerContainer(self, self.settings)
        log.debug(
            "MainWindow._create_viewer_container : conteneur de visionneuses créé !"
        )
        # self.Refresh()

    def _create_status_bar(self) -> None:
        """
        Crée et associe une barre de statut à la fenêtre principale.

        Cette méthode importe le module `status` et utilise la classe `StatusBar` pour
        initialiser la barre de statut. La barre de statut est associée à la fenêtre principale
        et est utilisée pour afficher des messages d'état, des informations sur les tâches,
        etc.

        Modules importés :
            taskcoachlib.gui.status : Fournit la classe `StatusBar` pour gérer la barre de statut.

        Actions :
            - La barre de statut est créée en passant la fenêtre principale (`self`) et les visionneuses (`self.viewer`).
            - La barre de statut est ensuite associée à la fenêtre principale à l'aide de `SetStatusBar`.
        """
        log.info(
            "MainWindow._create_status_bar : Création d'une barre de status et association avec la fenêtre principale."
        )
        # from taskcoachlib.gui import status  # pylint: disable=W0404

        # self.CreateStatusBar(1, STB_DEFAULT_STYLE, IdProvider.get(), "")  # TODO : à essayer
        self.SetStatusBar(status.StatusBar(self, self.viewer))  # Erreur ?
        # self.Update()

    def __create_menu_bar(self) -> None:
        """
        Crée et associe la barre de menus à la fenêtre principale.

        Cette méthode importe le module `menu` et utilise la classe `MainMenu` pour
        initialiser la barre de menus. La barre de menus contient les différentes options
        du menu principal (Fichier, Édition, Voir, etc.) et est associée à la fenêtre principale.

        Modules importés :
            taskcoachlib.gui.menu : Fournit la classe `MainMenu` pour gérer la barre de menus.

        Actions :
            - La barre de menus est créée en passant la fenêtre principale (`self`), les paramètres (`self.settings`),
              le contrôleur d'entrées/sorties (`self.iocontroller`), les visionneuses (`self.viewer`), et le fichier de tâches (`self.taskFile`).
            - La barre de menus est ensuite associée à la fenêtre principale à l'aide de `SetMenuBar`.
        """
        # Cette ligne d'import ne peut être au début !
        # Sinon : ImportError: cannot import name 'CheckableTaskViewer' from partially initialized module 'taskcoachlib.gui.viewer.task' (most likely due to a circular import) (/home/sylvain/Téléchargements/src/task-coach-git/taskcoach/taskcoachlib/gui/viewer/task.py)
        from taskcoachlib.gui import menu  # pylint: disable=W0404

        log.info(
            "MainWindow.__create_menu_bar : Création d'une barre de menus et association avec la fenêtre principale."
        )

        # Sauf si c'est programmé avant, devrait contenir :
        # La création des menus Fichiers, Editer, Affichage, Nouveau, etc.
        # # 09 # Setting up the menu.
        #   10         filemenu= wx.Menu()
        #   11
        #   12         # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        #   13         filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        #   14         filemenu.AppendSeparator()
        #   15         filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        #   16
        # Puis la création de la barre de menus :
        #   17         # Creating the menubar.
        #   18         menuBar = wx.MenuBar()
        #   19         menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        #   20         self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        # Voir menu.MainMenu
        # self.SetMenuBar(
        #     menu.MainMenu(
        #         self, self.settings, self.iocontroller, self.viewer, self.taskFile
        #     )
        # )
        # # menuBar = wx.MenuBar()  # MainMenu est un wx.MenuBar
        menuBar = menu.MainMenu(
            self, self.settings, self.iocontroller, self.viewer, self.taskFile
        )  # Création de l'objet menuBar
        # Ensuite, il faut créer l'objet menu :
        # fileMenu = wx.Menu()  # Où ? dans gui.menu!
        # Accrocher des menus item à l'objet menu :
        # fileItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')  # où ? Dans les menus de gui.menu en utilisant appendUICommands().
        # Accrocher le menu dans la barre de menu (& crée un accélérateur) :
        # menuBar.Append(fileMenu, '&File')  # Où ? créés dans menu.MainMenu
        # En fin de compte, nous appelons la méthode SetMenuBar() :
        # Cette méthode appartient à la Widget wx.Frame.
        self.SetMenuBar(menuBar)  # Il configure la barre de menus.
        # Et la suite ?
        # Binder l'événement Menu du menu item à la méthode OnQuit
        # self.Bind(wx.EVT_MENU, self.OnQuit, fileItem)
        #
        # self.SetSize((300, 200))
        # self.SetTitle('Simple menu')
        # self.Centre()
        # self.Refresh()

    def __create_reminder_controller(self) -> None:
        # pylint: disable=W0201
        """
        Crée et initialise le contrôleur de rappels pour la gestion des tâches et des efforts.

        Cette méthode initialise un contrôleur de rappels (`ReminderController`), qui est
        utilisé pour gérer les rappels associés aux tâches et aux efforts de l'application. Le
        contrôleur surveille les tâches et les efforts et envoie des notifications à l'utilisateur
        lorsque des rappels sont définis.

        Modules utilisés :
            remindercontroller.ReminderController : Classe utilisée pour gérer les rappels dans Task Coach.

        Actions :
            - Le contrôleur de rappels est initialisé avec la fenêtre principale (`self`), la liste des tâches (`self.taskFile.tasks()`),
              la liste des efforts (`self.taskFile.efforts()`), et les paramètres utilisateur (`self.settings`).
            - Le contrôleur est ensuite assigné à l'attribut `reminderController` de la fenêtre principale.
        """
        self.reminderController = remindercontroller.ReminderController(
            self, self.taskFile.tasks(), self.taskFile.efforts(), self.settings
        )

    def addPane(
        self, page, caption, name, floating: bool = False
    ) -> None:  # pylint: disable=W0221
        # Overrides method in widget.frame.AuiManagedFrameWithDynamicCenterPane
        """
        Ajoute un volet (pane) à la fenêtre principale.

        Args :
            page (wx.Window) : Le volet à ajouter.
            caption (str) : Le titre du volet.
            name (str) : Nom unique du volet.
            floating (bool) : Indique si le volet doit être flottant.
        """
        # TODO: si problème Essayer :
        # def addPane(self, page, caption, floating=False, **kwargs):  # pylint: disable=W0221
        # Signature of method 'MainWindow.addPane()' does not match signature of the base method
        # in class 'AuiManagedFrameWithDynamicCenterPane'
        # addPane vient de tclib/widgets/frame.py AuiManagedFrameWithDynamicCenterPane
        # Debug: ClientToScreen cannot work when toplevel window is not shown
        if operating_system.isWayland():
            floating = False

        # if self.Show() is True:
        name = page.settingsSection()
        super().addPane(page, caption, name, floating=floating)
        # self.Refresh()
        # else:
        #    pass

    def __init_window(self):
        """
        Initialise la fenêtre principale de Task Coach en définissant la disposition des composants (barres d'outils, barres de statut, etc.)
        et en appliquant les paramètres d'affichage sauvegardés.
        """
        log.debug(
            "MainWindow._init_window : Initialisation de la fenêtre principale."
        )
        # log.debug(f"MainWindow._init_window : self.taskFile = {self.taskFile}")  # Problème !
        self.__filename = self.taskFile.filename()
        # log.debug("MainWindow._init_window : s'arrêt après cela :")
        self.__setTitle()
        self.SetIcons(artprovider.iconBundle("taskcoach"))
        self.displayMessage(
            _("Welcome to %(name)s version %(version)s")
            % {"name": meta.name, "version": meta.version},
            pane=1,
        )
        # self.Refresh()
        log.debug("MainWindow._init_window : Fenêtre principale initialisée.")

    def __init_window_components(self):
        """
        Initialise les composants principaux de la fenêtre (barre d'outils, barre d'état) et restaure la perspective de la fenêtre.

        Cette méthode affiche ou masque la barre d'outils et la barre d'état selon les paramètres utilisateur. Elle utilise `wx.CallAfter`
        pour éviter un problème où la barre d'état s'affiche en haut de la fenêtre lorsque celle-ci est initialement cachée, puis montrée.
        Enfin, elle appelle `__restore_perspective` pour restaurer la disposition des panneaux à partir des paramètres sauvegardés.

        Actions :
            - Affiche ou masque la barre d'outils en fonction du paramètre "toolbar" des réglages utilisateur.
            - Affiche ou masque la barre d'état en fonction du paramètre "statusbar" des réglages utilisateur.
            - Restaure la disposition des panneaux de la fenêtre en appelant `__restore_perspective`.
        """
        # Freeze to prevent flickering during AUI layout restoration
        self.Freeze()

        try:
            self.showToolBar(self.settings.getvalue("view", "toolbar"))
            # Nous utilisons CallAfter car sinon la barre d'état apparaîtra en haut
            # de la fenêtre lorsqu'elle est initialement masquée puis affichée.
            wx.CallAfter(
                self.showStatusBar,
                self.settings.getboolean("view", "statusbar"),
            )
            # Restaure la perspective de la fenêtre
            self.__restore_perspective()
        finally:
            self.Thaw()
        # self.Refresh()
        # Reset toolbar position after perspective is loaded
        wx.CallAfter(self._resetToolbarPosition)

        # Note: Window position/size tracking uses debouncing to handle spurious
        # events from AUI LoadPerspective() and GTK window realization.
        # Events are bound immediately in __init__, no manual start needed.

    def __restore_perspective(self):
        """
        Restaure la disposition des panneaux de la fenêtre (perspective) à partir des paramètres sauvegardés.

        Cette méthode tente de restaurer la perspective (disposition des panneaux) à partir du fichier de configuration. Elle vérifie également
        si le nombre de visionneuses diffère entre la perspective actuelle et les réglages. Si c'est le cas, elle utilise une perspective par défaut.
        Si la restauration échoue, un message d'erreur est affiché à l'utilisateur, et la perspective par défaut est utilisée.

        Actions :
            - Charge la perspective à partir du paramètre "view" -> "perspective" des réglages utilisateur.
            - Vérifie si le nombre de visionneuses correspond entre la perspective et les réglages, sinon réinitialise la perspective.
            - Si une erreur se produit lors du chargement de la perspective, elle affiche un message d'erreur et charge une perspective par défaut.
            - Rend visible tous les panneaux et actualise leurs titres pour correspondre aux traductions actuelles.

        Exceptions :
            - Affiche une boîte de dialogue d'erreur si la restauration de la perspective échoue.

        Notes :
            - Empêche l'apparition de "panneaux zombies" en s'assurant que tous les panneaux sont visibles.
            - Met à jour les titres des panneaux pour refléter la traduction correcte en cas de changement de langue.
        """
        log.debug(
            "__restore_perspective : Restauration de la perspective depuis les paramètres"
        )
        perspective = self.settings.get("view", "perspective")
        #  Vérifie si le nombre de visionneuses a changé entre les versions
        for viewer_type in viewer.viewerTypes():
            # for viewer_type in factory.viewerTypes():
            if self.__perspective_and_settings_viewer_count_differ(
                viewer_type
            ):
                # Différents nombres de spectateurs peuvent se produire
                # lorsque le nom d'un spectateur
                # est modifié entre les versions
                perspective = (
                    ""  # Réinitialise la perspective en cas de différence
                )
                log.warning(
                    "__restore_perspective : Incompatibilité entre la perspective et les viewers."
                    "Le nombre de visionneuses dans la perspective actuelle de la fenêtre diffère de celui sauvegardé dans les paramètres"
                )
                break

        try:
            self.manager.LoadPerspective(
                perspective
            )  # Tente de charger la perspective sauvegardée
        except ValueError as reason:
            # Cela a été rapporté. Je ne sais pas pourquoi. Continuez
            # si c'est le cas.
            # Si la restauration échoue, affiche une erreur et utilise une perspective par défaut
            log.error(
                f"__restore_perspective : Erreur lors de la restauration de la perspective : {reason}",
                exc_info=True,
            )

            if self.__splash:
                self.__splash.Destroy()
            wx.MessageBox(
                _("""Couldn't restore the pane layout from TaskCoach.ini:
                    %s
                    
                    The default pane layout will be used.
                    
                    If this happens again, please make a copy of your TaskCoach.ini file
                    before closing the program, open a bug report, and attach the
                    copied TaskCoach.ini file to the bug report.""") % reason,
                _("%s settings error") % meta.name,
                style=wx.OK | wx.ICON_ERROR,
            )
            self.manager.LoadPerspective("")

        # Sur Wayland, forcer tous les panneaux flottants à s'ancrer
        # pour éviter qu'ils ne soient bloqués ou invisibles.
        if operating_system.isWayland():
            # Sur Wayland, forcer tous les panneaux flottants à s'ancrer
            # pour éviter qu'ils ne soient bloqués ou invisibles.
            for pane in self.manager.GetAllPanes():
                if pane.IsFloating():
                    pane.Dock()

        # S'assure que tous les panneaux sont visibles et actualise leurs titres
        for pane in self.manager.GetAllPanes():
            # Empêchez les volets zombies en vous assurant que tous les volets sont visibles
            if not pane.IsShown():
                pane.Show()  # Montre les panneaux non visibles
            # Ignorez les titres enregistrés-sauvegardés dans la perspective,
            # ils peuvent être incorrects lorsque l'utilisateur change de traduction :
            if hasattr(pane.window, "title"):
                pane.Caption(pane.window.title())
            # Reset toolbar MinSize - width is derived from window, not saved.
            # Old INI files may have hard-coded widths like minw=1840.
            # Use GetBestSize() for height - toolbar calculates this in Realize()
            if pane.name == "toolbar":
                best_size = pane.window.GetBestSize()
                pane.MinSize((-1, best_size.GetHeight()))
        self.manager.Update()
        # self.Refresh()

    def __perspective_and_settings_viewer_count_differ(self, viewer_type):
        """
        Vérifie si le nombre de visionneuses dans la perspective actuelle de la fenêtre diffère de celui sauvegardé dans les paramètres.

        Returns :
            (bool) : True si le nombre de visionneuses est différent, sinon False.
        """
        perspective = self.settings.get("view", "perspective")
        perspective_viewer_count = perspective.count("name=%s" % viewer_type)
        settings_viewer_count = self.settings.getint(
            "view", "%scount" % viewer_type
        )
        return perspective_viewer_count != settings_viewer_count

    def __register_for_window_component_changes(self):
        """
        S'enregistre pour recevoir des notifications de changement de composants de fenêtre, comme les barres d'outils et les barres de statut.
        Cela permet de mettre à jour l'affichage des composants en fonction des événements de l'application.
        """
        pub.subscribe(self.__onFilenameChanged, "taskfile.filenameChanged")
        pub.subscribe(self.__onDirtyChanged, "taskfile.dirty")
        pub.subscribe(self.__onDirtyChanged, "taskfile.clean")
        pub.subscribe(self.showStatusBar, "settings.view.statusbar")
        pub.subscribe(self.showToolBar, "settings.view.toolbar")
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.onCloseToolBar)
        # Detect toolbar drag-end and float-to-dock transitions to reset position
        self.manager.Bind(aui.EVT_AUI_RENDER, self._onAuiRender)

    def __onFilenameChanged(self, filename):
        """
        Gère les changements de nom de fichier dans Task Coach et met à jour le titre de la fenêtre en conséquence.

        Args :
            filename (str) : Nom du fichier.
        """
        #    event (Event) : L'événement de changement de nom de fichier.
        self.__filename = filename
        self.__setTitle()

    def __onDirtyChanged(self, taskFile):
        """
        Gère les changements dans l'état de modification (dirty) du fichier de tâches.

        Si le fichier de tâches a été modifié, cette méthode met à jour l'attribut interne `__dirty`
        et appelle la méthode `__setTitle` pour ajuster le titre de la fenêtre.

        Args :
            taskFile (TaskFile) : Le fichier de tâches dont l'état de modification a changé.
        """
        self.__dirty = (
            taskFile.isDirty()
        )  # Met à jour l'état interne selon l'état "dirty" du fichier de tâches
        self.__setTitle()  # Met à jour le titre de la fenêtre pour refléter cet état

    def __setTitle(self):
        """
        Met à jour le titre de la fenêtre principale en fonction du fichier de tâches actuel.
        Si le fichier a été modifié sans être sauvegardé, un indicateur est ajouté au titre.
        """
        title = meta.name
        if self.__filename:
            # title += " - %s" % self.__filename
            title += f" - {self.__filename}"
        if self.__dirty:
            title += " *"
        # Règle le titre de la fenêtre principale :
        self.SetTitle(title)

    # def Destroy(self):
    #     """Surcharge la méthode Destroy pour détruire proprement les menus."""
    #     log.debug("MainWindow.Destroy: Début de la destruction de MainWindow et de ses menus.")
    #     # if hasattr(self, 'task_popup_menu') and self.task_popup_menu:
    #     #     self.task_popup_menu.Destroy()
    #     #     del self.task_popup_menu  # Supprimez la référence pour éviter les problèmes
    #     # if hasattr(self, 'task_tree_viewer') and self.task_tree_viewer:
    #     #     self.task_tree_viewer.Destroy()  # Assurez-vous de détruire le viewer
    #     #     del self.task_tree_viewer
    #     super().Destroy()
    #     log.debug("MainWindow.Destroy: Fin de la destruction de MainWindow.")

    def displayMessage(self, message, pane=0):
        """
        Affiche un message dans la barre de statut de la fenêtre principale.

        Si une barre de statut est présente, le message est affiché dans le panneau spécifié.

        Args :
            message (str) : Le message à afficher dans la barre de statut.
            pane (int) : Le panneau de la barre de statut où le message doit être affiché (par défaut, le premier panneau).
        """
        statusBar = self.GetStatusBar()  # Récupère la barre de statut
        if statusBar:  # Vérifie si une barre de statut est présente
            statusBar.SetStatusText(
                message, pane
            )  # Affiche le message dans le panneau spécifié

    def save_settings(self):
        """
        Sauvegarde les paramètres actuels de la fenêtre, y compris les dimensions, la perspective et le nombre de visionneuses.
        """
        self.__save_viewer_counts()
        self.__save_perspective()
        self.__save_position()

    def __save_viewer_counts(self):
        """Enregistrez le nombre de visionneuses pour chaque type de visionneuse."""
        for viewer_type in viewer.viewerTypes():
            # for viewer_type in factory.viewerTypes():
            if hasattr(self, "viewer"):
                count = len(
                    [
                        v
                        for v in self.viewer
                        if v.__class__.__name__.lower() == viewer_type
                    ]
                )
            else:
                count = 0
            self.settings.set("view", viewer_type + "count", str(count))

    def __save_perspective(self):
        """
        Sauvegarde la perspective actuelle de la fenêtre, c'est-à-dire l'organisation des différents volets et composants (barre d'outils, visionneuses, etc.).
        """
        perspective = self.manager.SavePerspective()
        self.settings.set("view", "perspective", perspective)

    def __save_position(self) -> None:
        """
        Sauvegarde la position et la taille actuelles de la fenêtre principale dans les paramètres de l'application.
        Cela permet de restaurer la fenêtre à la même position lors de la prochaine ouverture.
        """
        self.__dimensions_tracker.save_position()

    def closeEditors(self) -> None:
        """
        Ferme tous les éditeurs ouverts dans la fenêtre principale.
        """
        log.info(
            "MainWindow.closeEditors : Fermeture de tous les éditeurs ouverts dans la fenêtre principale."
        )
        try:
            for child in self.GetChildren():
                if isinstance(child, Editor):
                    child.Close()
        except Exception as e:
            log.exception(
                "MainWindow.closeEditors : Erreur inattendue lors de la fermeture : %s",
                e,
            )
        self.Refresh()

    def _onSysColourChanged(self, event):
        """Handle system theme/colour change event (Windows/macOS)."""
        # currentDark = detect_dark_theme()
        # if currentDark != self._lastDetectedDark:
        #     self._lastDetectedDark = currentDark
        #     pub.sendMessage("system.appearance.changed")
        #     if self.settings.get("window", "theme") == "automatic":
        #         pub.sendMessage("settings.window.theme")
        event.Skip()

    def onClose(self, event):
        # TODO : A revoir https://docs.wxpython.org/wx.CloseEvent.html
        """
        Gère la fermeture de la fenêtre, en arrêtant le suivi des tâches et en vérifiant si l'application doit quitter.

        Args :
            event (wx.Event) : L'événement de fermeture de la fenêtre.
        """
        # Voir https://pythonhosted.org/wxPython/window_deletion_overview.html#window-deletion
        # print(f"mainwindow.MainWindow.onClose : Fermeture de la fenêtre self={self} avec event={event}!")
        # Causes possibles du problème de fermeture
        #
        # Plusieurs éléments dans cette fonction pourraient potentiellement causer des problèmes de fermeture de la fenêtre :
        #
        #     Logique conditionnelle complexe : La combinaison de conditions (si l'utilisateur a configuré pour cacher,
        #           si l'application doit quitter, etc.) peut rendre le comportement de la fermeture difficile à prévoir,
        #           notamment en cas d'erreurs ou de conditions inattendues.
        #     Appel à event.Skip() : Si event.Skip() n'est pas appelé dans les bonnes conditions,
        #           l'événement de fermeture peut être véto et la fenêtre ne se fermera pas.
        #     Problèmes avec les méthodes appelées : Les méthodes self.taskFile.stop(), self._idleController.stop()
        #           ou self.closeEditors() pourraient ne pas se terminer correctement, bloquant ainsi le processus de fermeture.
        #     Références circulaires : Si des objets ont des références circulaires,
        #           le garbage collector pourrait avoir du mal à libérer la mémoire,
        #           empêchant l'application de se fermer proprement.
        #     Problèmes externes : Des processus externes ou des bibliothèques tierces pourraient
        #           empêcher la fermeture de l'application.
        # Démarche pour résoudre le problème
        #
        #     Simplifier la logique : Essayez de simplifier la logique conditionnelle,
        #                           en particulier autour de event.Skip().
        #                           Vous pouvez utiliser des variables booléennes pour rendre le code plus lisible.
        #     Ajouter des logs : Ajoutez des messages de log à différents points de la fonction pour suivre
        #                       l'exécution et identifier les parties du code qui ne sont pas exécutées comme prévu.
        #     Isoler les problèmes : Essayez de commenter des parties de la fonction pour voir si le problème persiste.
        #                           Cela vous aidera à identifier la section de code qui cause le problème.
        #     Vérifier les méthodes appelées : Assurez-vous que les méthodes self.taskFile.stop(), self._idleController.stop()
        #                               et self.closeEditors() se terminent correctement et ne lèvent pas d'exceptions.
        #     Utiliser un débogueur : Un débogueur vous permettra d'exécuter votre code ligne par ligne et d'inspecter
        #                       les valeurs des variables, ce qui peut être très utile pour trouver des bogues subtils.
        #     Rechercher des références circulaires : Utilisez un outil d'analyse statique
        #                                               pour détecter les références circulaires potentielles.
        #     Vérifier les événements externes : Assurez-vous qu'aucun événement externe
        #     (par exemple, des timers, des threads en arrière-plan) n'empêche l'application de se fermer.

        # # Ancien code :
        # # print("Resetting IdProvider...")
        # # IdProvider.reset()
        # # Fermer les éditeurs:
        # print("onCLose : Fermeture des éditeurs")
        # self.closeEditors()
        #
        # # Permettre à l'application de quitter : Si l'application doit effectivement quitter, event.Skip() est appelé pour autoriser la fermeture.
        # if self.__shutdown:
        #     print("onClose - Appel de event.Skip()")
        #     event.Skip()
        #     return
        # # Vérifier les paramètres de l'application :
        # # Si l'utilisateur a configuré pour cacher la fenêtre plutôt que de la fermer, la fenêtre est minimisée. :
        # if event.CanVeto() and self.settings.getboolean("window", "hidewhenclosed"):
        #     print("onClose : Fenêtre minimisée.")
        #     event.Veto()
        #     self.Iconize()
        # else:
        #     if application.Application().quitApplication():
        #         print("onClose : Quitter avec event.Skip()")
        #         event.Skip()
        #         # Arrêter le suivi des tâches :
        #         self.taskFile.stop()
        #         # Arrêter le contrôleur d'inactivité :
        #         self._idleController.stop()

        log.info(
            "mainWindow.onClose : Fermeture de la fenêtre par l'utilisateur."
        )
        # Nouveau code :
        try:
            # Simplifier la logique
            # Vérifier les paramètres de l'application. :
            should_quit = (
                application.Application().quitApplication()
            )  # Assure que l'appel pour quitter se fait sur le bon objet.
            # should_quit = wx.GetApp().quitApplication()
            # should_hide = event.CanVeto() and self.settings.getboolean("window", "hidewhenclosed")
            should_hide = self.settings.getboolean("window", "hidewhenclosed")

            # TODO : Gérer la sauvegarde des données non enregistrées :
            #  Avant de fermer les éditeurs ou de quitter l'application,
            #  il serait crucial de vérifier s'il y a des données non enregistrées
            #  et de demander à l'utilisateur s'il souhaite les sauvegarder.
            #  Cela pourrait être intégré dans la méthode closeEditors()
            #  ou dans onClose() avant d'appeler closeEditors().
            # print("onClose : Fermeture des éditeurs")
            log.debug("MainWindow.onCLose : Fermeture des éditeurs")
            self.closeEditors()  # Fermer les éditeurs en premier

            if should_quit or self.__shutdown:
                # print("onClose : Quitter avec event.Skip()")
                log.debug("MainWindow.onClose : Quitter avec event.Skip()")
                # Assurer la fermeture propre des ressources.
                self.taskFile.stop()  # Arrêter le suivi des tâches.
                self._idleController.stop()  # Arrêter le contrôleur d'inactivité.
                self.closeEditors()  # Fermer les éditeurs.
                self.manager.UnInit()  # Désinitialise le manageur de trames. AUI
                event.Skip()  # Autoriser la fermeture.
            elif should_hide:
                # Si l'utilisateur a configuré pour cacher la fenêtre plutôt que de la fermer, la fenêtre est minimisée.
                # print("onClose : Fenêtre minimisée.")
                log.debug("MainWindow.onClose : Fenêtre minimisée.")
                event.Veto()
                self.Iconize()
            else:
                # Si aucune des conditions ci-dessus n'est remplie,
                # par défaut, on autorise la fermeture (peut-être après une confirmation).
                # print("onClose : Fermeture par défaut avec event.Skip()")
                log.debug(
                    "MainWindow.onClose : Fermeture par défaut avec event.Skip()"
                )
                self.taskFile.stop()
                self._idleController.stop()
                self.manager.Unit()  # Désinitialise le manageur de trame AUI.
                event.Skip()
        except Exception as e:
            log.exception(
                "MainWindow.onClose : Erreur inattendue lors de la fermeture : %s",
                e,
            )
        # Arrêtez le thread de détection d'inactivité à la fin du programme.
        self._idleController.stop()
        log.info("MainWindow.onCLose : Fenêtre fermée par l'utilisateur")

    def restore(self, event) -> None:  # pylint: disable=W0613
        """
        Restaure la fenêtre principale à partir de la barre des tâches lorsque l'application a été minimisée ou réduite dans la barre d'état système.

        Args :
            event (wx.Event) : L'événement de restauration de la fenêtre.
        """
        if self.settings.getboolean("window", "maximized"):
            self.Maximize()
        self.Iconize(False)
        self.Show()
        self.Raise()
        self.Refresh()

    def onIconify(self, event):
        """
        Gère la minimisation de la fenêtre. Cache la fenêtre si l'option "hidewheniconized" est activée dans les paramètres.

        Args :
            event (wx.Event) : L'événement de minimisation de la fenêtre.
        """
        # TODO Commentaire : Le commentaire TODO est pertinent.
        #  Il est important de s'assurer que l'état interne de la fenêtre
        #  (par exemple, une variable indiquant si elle est cachée car iconifiée)
        #  est correctement mis à jour si cela est nécessaire pour
        #  d'autres parties de l'application. Actuellement, la méthode
        #  se contente de cacher la fenêtre. Si d'autres actions doivent
        #  être entreprises lorsqu'elle est cachée de cette manière
        #  (par exemple, arrêter certains processus en arrière-plan),
        #  elles devraient être ajoutées.
        # TODO: Vérifiez que la méthode onIconify de MainWindow est correctement implémentée et qu'elle met à jour l'état interne de la fenêtre.
        #  Faire une recherche sur wx.IconizeEvent.IsIconized()
        #  See also :
        #  Events and Event Handling, wx.TopLevelWindow.Iconize , wx.TopLevelWindow.IsIconized

        # Fonctionnalité principale :
        #  La méthode semble implémenter correctement la logique de cacher
        #  la fenêtre lors de la minimisation si le paramètre hidewheniconized
        #  est True. Sinon, l'événement est passé aux gestionnaires suivants
        #  dans la chaîne (event.Skip()).
        # Utilisation de event.IsIconized() :
        #  C'est la manière correcte de vérifier si l'événement est
        #  une notification de minimisation. L'ancienne ligne commentée
        #  (event.Iconized()) est également valide car wx.IconizeEvent a
        #  une méthode IsIconized().
        # Gestion des erreurs :
        #  L'inclusion d'un bloc try...except RuntimeError est
        #  une bonne pratique pour prévenir des plantages inattendus.
        #  Cependant, il serait utile de loguer l'erreur de manière
        #  plus informative (par exemple, en incluant le type d'événement
        #  et potentiellement un traceback) pour faciliter le débogage
        #  si une RuntimeError se produit.
        try:
            # if event.Iconized() and self.settings.getboolean('window', 'hidewheniconized'):
            if event.IsIconized() and self.settings.getboolean(
                "window", "hidewheniconized"
            ):
                self.Hide()
                # Logging plus informatif en cas d'erreur :
                log.debug(
                    "MainWindow.onIconify : iconified and hidden."
                )  # Ajout d'un log
                log.debug("Fenêtre iconifiée")
                # Mise à jour de l'état interne (si nécessaire) :
                #  Ajoutez un attribut à MainWindow (par exemple, self._is_hidden_when_iconified)
                #  pour suivre si la fenêtre est cachée à cause de l'iconification.
                #  Cela pourrait être utile ailleurs dans l'application.
                self._is_hidden_when_iconified = (
                    True  # Exemple de mise à jour d'un état interne
                )
            else:
                event.Skip()
                self._is_hidden_when_iconified = False
        except RuntimeError as e:
            # print("mainwindow : Error onIconify :", str(e))
            # Logging plus informatif en cas d'erreur :
            log.error(
                f"MainWindow.onIconify : {e}", exc_info=True
            )  # Log avec traceback

    def onResize(self, event):
        """
        Gère le redimensionnement de la fenêtre, notamment l'ajustement de la barre d'outils.

        Args :
            event (wx.Event) : L'événement de redimensionnement.
        """
        # Fonctionnalité principale :
        #  La méthode tente d'ajuster la largeur de la barre d'outils
        #  (toolbar pane dans AuiManager) pour qu'elle corresponde
        #  à la nouvelle largeur de la fenêtre principale lors du redimensionnement.
        #  Elle fixe également une hauteur à -1 (qui signifie "taille par défaut"
        #  ou laisser le sizer gérer la hauteur) et une largeur minimale de 42 pixels.
        currentToolbar = self.manager.GetPane("toolbar")
        newSize = self.GetSize()
        # # Vérification de la barre d'outils :
        # #  currentToolbar.IsOk() est une vérification essentielle
        # #  pour s'assurer que le pane de la barre d'outils existe
        # #  et est valide avant d'essayer d'accéder à sa fenêtre.
        if currentToolbar.IsOk():
            width = event.GetSize().GetWidth()
            # Get height from toolbar's GetBestSize() - calculated during Realize()
            best_size = currentToolbar.window.GetBestSize()
            height = best_size.GetHeight()
            # Set size on the window widget for current display
            # currentToolbar.window.SetSize((event.GetSize().GetWidth(), -1))
            currentToolbar.window.SetSize((width, -1))
            # currentToolbar.window.SetMinSize((event.GetSize().GetWidth(), 42))
            currentToolbar.window.SetMinSize((width, height))
            # Use -1 for width on pane info so SavePerspective doesn't save
            # a hard-coded width value. The toolbar width is derived from
            # window width at runtime, not a user preference to persist.
            currentToolbar.MinSize((-1, height))
        if not hasattr(self, "_lastSize"):
            self._lastSize = newSize

        if newSize != self._lastSize:
            log.debug(
                f"MainWindow.onResize : Redimensionnement de la fenêtre : {newSize}, ancienne valeur={self._lastSize}"
            )
            self._lastSize = newSize
            # TODO : mettre self._lastSize = self._lastSize or self.GetSize() dans __init__
            log.info(
                f"MainWindow.onResize : Fenêtre redimensionnée, résultat : {self.GetSize()}"
            )

        event.Skip()

        # # Éventuellement, forcer une mise à jour de la mise en page (AuiManager.Update())
        # # après le redimensionnement de la barre d'outils,
        # # bien que cela puisse être implicitement
        # # géré par le redimensionnement de la fenêtre principale elle-même.
        # # Si vous remarquez des problèmes de disposition de la barre d'outils
        # # après le redimensionnement, l'ajout de self.manager.Update()
        # # après avoir défini la taille pourrait aider.
        self.manager.Update()
        # self.Refresh()
        self.Update()

    # def showStatusBar(self, value=True):
    def showStatusBar(self, value: bool = True) -> None:
        """
        Affiche ou masque la barre de statut en fonction de la valeur fournie.

        Args :
            value (bool) : True pour afficher, False pour masquer.
        """
        log.debug(
            "MainWindow.showStatusBar : Affichage de la barre de status : %s",
            value,
        )

        # FIXME: Masquer d'abord la barre d'état, puis masquer la barre d'outils, puis
        #  afficher la barre d'état la met au mauvais endroit (uniquement sous Linux ?)
        # self.GetStatusBar().Show(value)
        statusBar = self.GetStatusBar()
        if statusBar:
            statusBar.Show(value)
            self.SendSizeEvent()
        # self.SendSizeEvent()

    def createToolBarUICommands(self):
        """Commandes d'interface utilisateur à mettre sur la barre d'outils de cette fenêtre.

        Crée les commandes UI à afficher dans la barre d'outils de la fenêtre.

        Returns :
            (list) : Une liste d'instances de commandes UI.
        """
        log.debug(
            "MainWindow.createToolBarUICommands: Création des commandes UI de la barre d'outils."
        )
        # Cette liste est manuellement construite et peut contenir :
        #     - des instances de UICommand comme FileOpen, EditUndo, etc.
        #     - None pour indiquer un séparateur.
        #     - 1 pour un espace extensible.
        # Appelée par gui.toolbar.ToolBar.uiCommands
        uiCommands = [
            uicommand.FileOpen(iocontroller=self.iocontroller),
            uicommand.FileSave(iocontroller=self.iocontroller),
            uicommand.FileMergeDiskChanges(iocontroller=self.iocontroller),
            uicommand.Print(viewer=self.viewer, settings=self.settings),
            None,
            uicommand.EditUndo(),
            uicommand.EditRedo(),
        ]
        uiCommands.extend(
            [
                None,
                uicommand.EffortStartButton(taskList=self.taskFile.tasks()),
                uicommand.EffortStop(
                    viewer=self.viewer,
                    effortList=self.taskFile.efforts(),
                    taskList=self.taskFile.tasks(),
                ),
            ]
        )
        # Retourne explicitement une liste d’instances de UICommand
        return uiCommands

    def getToolBarPerspective(self):
        """
        Retourne la perspective actuelle de la barre d'outils, c'est-à-dire l'organisation des boutons et des commandes dans la barre d'outils.

        Returns :
            (str) : La perspective de la barre d'outils.
        """
        return self.settings.get("view", "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        """
        Sauvegarde la perspective actuelle de la barre d'outils dans les paramètres de l'application.

        Args :
            perspective (str) : La perspective à sauvegarder.
        """
        self.settings.set("view", "toolbarperspective", perspective)

    def showToolBar(self, value) -> None:
        """
        Affiche ou cache la barre d'outils en fonction de la valeur fournie.

        Cette méthode permet de gérer l'affichage de la barre d'outils dans la fenêtre principale de l'application.
        Si une barre d'outils existe déjà, elle est détachée et supprimée avant d'en créer une nouvelle si nécessaire.
        La nouvelle barre d'outils est alors ajoutée à la fenêtre selon les paramètres spécifiés, notamment sa position
        et son comportement de redockage.

        Args :
            value (bool | int) : Si `value` est `False`, la barre d'outils est masquée et supprimée. Si `value` est un
            entier, il est utilisé pour définir la taille de la nouvelle barre d'outils à afficher en haut de la fenêtre.

        Actions :
            1. Vérifie si une barre d'outils existe déjà :
               - Si oui, elle est détachée de la fenêtre et détruite.
            2. Si `value` est différent de `False`, une nouvelle barre d'outils est créée avec les paramètres actuels :
               - Elle est ajoutée au haut de la fenêtre (`Top()`).
               - Elle ne peut pas être redockée à gauche ou à droite.
               - La barre d'outils est configurée pour être détruite lors de sa fermeture.
            3. L'état de la fenêtre est mis à jour pour refléter les modifications.

        Notes :
            - `aui.AuiPaneInfo()` est utilisé pour configurer l'emplacement et le comportement de la barre d'outils.
            - `wx.CallAfter(bar.SetGripperVisible, False)` est utilisé pour masquer la poignée de redockage de la barre d'outils.

        Méthodes appelées :
            - `self.manager.GetPane("toolbar")` : Récupère le panneau de la barre d'outils actuelle.
            - `self.manager.DetachPane(pane)` : Détache un panneau de la fenêtre principale.
            - `bar.Destroy()` : Détruit la barre d'outils actuelle.
            - `self.manager.AddPane(pane, paneInfo)` : Ajoute un panneau à la fenêtre principale.
            - `self.manager.Update()` : Met à jour la disposition de la fenêtre après les modifications.
        """
        log.debug(
            "MainWindow.showToolBar : Affichage de la barre d’outils : %s",
            value,
        )

        currentToolbar = self.manager.GetPane(
            "toolbar"
        )  # La méthode vérifie d'abord s'il existe déjà une barre d'outils
        if currentToolbar.IsOk():
            # Détache et détruit la barre d'outils actuelle si elle existe
            self.manager.DetachPane(currentToolbar.window)
            currentToolbar.window.Destroy()

        if value:
            # Crée et ajoute une nouvelle barre d'outils si 'value' est différent de False
            bar = toolbar.MainToolBar(self, self.settings, size=value)
            # Use GetBestSize() for height - toolbar calculates this during Realize()
            best_size = bar.GetBestSize()
            self.manager.AddPane(
                bar,
                aui.AuiPaneInfo()
                .Name("toolbar")
                .Caption("Toolbar")
                .ToolbarPane()
                .Top()
                .MinSize((-1, best_size.GetHeight()))
                .DestroyOnClose()
                .LeftDockable(False)
                .RightDockable(False),
            )
            # Using .Gripper(False) does not work here
            # Appelle SetGripperVisible après la création de la barre d'outils pour masquer la poignée
            wx.CallAfter(bar.SetGripperVisible, False)
        # Met à jour la disposition de la fenêtre pour appliquer les modifications
        self.manager.Update()

    def onCloseToolBar(self, event) -> None:
        """
        Gère la fermeture de la barre d'outils. Si la barre d'outils est fermée, elle est masquée et les paramètres sont mis à jour.

        Args :
            event (wx.Event) : L'événement de fermeture de la barre d'outils.
        """
        log.debug(
            "mainwindows.MainWindow.onCloseToolBar : Debug"
            "Fermeture de la barre d'outils. Si la barre d'outils est fermée,"
            " elle est masquée et les paramètres sont mis à jour."
        )
        try:
            if (
                event.GetPane().IsToolbar()
            ):  # Unresolved attribute reference 'GetPane' for class 'Event'
                self.settings.setvalue("view", "toolbar", None)
            event.Skip()
        except Exception as e:
            log.exception(
                "MainWindow.onCloseToolBar : Erreur inattendue lors de la fermeture : %s",
                e,
            )
        self.Refresh()

    def _resetToolbarPosition(self):
        """Reset toolbar to position 0 to fill the dock area.

        Called on startup, drag-end, and float-to-dock transitions.
        For top/bottom docking: sticks left and fills width.
        For left/right docking: sticks up and fills height.
        Does nothing if toolbar is floating.
        """
        pane = self.manager.GetPane("toolbar")
        if not pane.IsOk() or pane.IsFloating():
            return

        direction = pane.dock_direction
        # Only handle docked positions: 1=top, 2=right, 3=bottom, 4=left
        if direction not in (1, 2, 3, 4):
            return

        if pane.dock_pos != 0:
            pane.Position(0)
            if direction in (1, 3):  # top/bottom: fill width
                pane.MinSize((self.GetSize().GetWidth(), -1))
            else:  # left/right: fill height
                pane.MinSize((-1, self.GetSize().GetHeight()))
            self.manager.Update()

    def _onAuiRender(self, event):
        """Detect toolbar drag-end and float-to-dock to reset position."""
        action = getattr(self.manager, "_action", 0)
        prev_action = getattr(self, "_prev_manager_action", 0)

        # Detect transition from dragging to idle
        if prev_action != 0 and action == 0:
            wx.CallAfter(self._resetToolbarPosition)

        # Detect floating->docked transition
        pane = self.manager.GetPane("toolbar")
        if pane.IsOk():
            was_floating = getattr(self, "_toolbar_was_floating", False)
            is_floating = pane.IsFloating()
            if was_floating and not is_floating:
                wx.CallAfter(self._resetToolbarPosition)
            self._toolbar_was_floating = is_floating

        self._prev_manager_action = action
        event.Skip()

    # Viewers

    def advanceSelection(self, forward) -> None:
        """
        Fait avancer la sélection des tâches dans les visionneuses de l'application.

        Args :
            forward (bool) : Si True, avance vers l'élément suivant. Si False, recule vers l'élément précédent.
        """
        # log.debug("MainWindow.advanceSelection : Sélection avancée dans les viewers")
        log.debug(
            f"MainWindow.advanceSelection: Avance la sélection des tâches (forward: {forward})."
        )
        self.viewer.advanceSelection(forward)

    def viewerCount(self) -> int:
        """
        Retourne le nombre actuel de visionneuses actives dans la fenêtre principale.

        Returns :
            (int) : Le nombre de visionneuses.
        """
        return len(self.viewer)

    # Power management

    def OnPowerState(self, state) -> None:
        """
        Envoie un message via le système de publication/souscription (pubsub) pour signaler un changement d'état d'alimentation.

        Cette méthode est déclenchée lorsqu'un changement d'état d'alimentation (mise sous tension ou hors tension) est détecté.
        Elle envoie un message "powermgt.on" ou "powermgt.off" via pubsub pour notifier les autres composants du système.

        Args :
            state (int) : L'état de l'alimentation. Peut être `self.POWERON` ou `self.POWEROFF`.
        """
        pub.sendMessage(
            "powermgt.%s" % {self.POWERON: "on", self.POWEROFF: "off"}[state]
        )
        # pub.sendMessage(
        #     f"powermgt.{{self.POWERON: 'on', self.POWEROFF: 'off'}[state]}"
        # )  # résultat bizarre !

    # iPhone-related methods.

    def createIPhoneProgressFrame(self):
        """
        Crée et retourne une fenêtre de progression pour la synchronisation avec un iPhone ou un iPod Touch.

        Cette méthode initialise une fenêtre de progression (`IPhoneSyncFrame`) utilisée pour afficher l'état de la synchronisation
        des tâches avec un appareil iPhone ou iPod Touch. Elle configure également l'icône de la fenêtre et son titre.

        Returns :
            IPhoneSyncFrame : La fenêtre de progression pour la synchronisation avec l'iPhone/iPod.
        """
        return IPhoneSyncFrame(
            self.settings,
            _("iPhone/iPod"),
            icon=wx.ArtProvider.GetBitmap(
                "taskcoach", wx.ART_FRAME_ICON, (16, 16)
            ),
            parent=self,
        )

    def getIPhoneSyncType(self, guid):
        """
        Détermine le type de synchronisation à utiliser pour un iPhone ou un iPod Touch.

        Cette méthode compare l'identifiant unique (GUID) fourni avec celui du fichier de tâches actuel. Si les GUID correspondent,
        elle effectue une synchronisation bidirectionnelle (retourne `0`). Sinon, elle affiche une boîte de dialogue
        (`IPhoneSyncTypeDialog`) pour demander à l'utilisateur le type de synchronisation à utiliser.

        Args :
            guid (str) : L'identifiant unique (GUID) de l'appareil ou du fichier de tâches.

        Returns :
            (int) : 0 pour une synchronisation bidirectionnelle, ou une autre valeur en fonction du choix de l'utilisateur.
        """
        if guid == self.taskFile.guid():
            return 0  # two-way. Synchronisation bidirectionnelle

        dlg = IPhoneSyncTypeDialog(self, wx.ID_ANY, _("Synchronization type"))
        try:
            dlg.ShowModal()
            return (
                dlg.value
            )  # Retourne le type de synchronisation choisi par l'utilisateur
        finally:
            dlg.Destroy()  # Ferme la boîte de dialogue après utilisation

    # @staticmethod
    def notifyIPhoneProtocolFailed(self) -> None:
        """
        Affiche un message d'erreur si la négociation du protocole avec un appareil iPhone ou iPod échoue.

        Cette méthode est appelée lorsqu'un appareil iPhone ou iPod tente de se synchroniser avec le fichier de tâches actuel,
        mais que la négociation du protocole échoue. Un message d'erreur est affiché pour informer l'utilisateur et l'encourager
        à signaler un bogue.

        Notes :
            Cette situation ne devrait normalement jamais se produire, mais un message d'erreur est affiché par précaution.

        Actions :
            - Affiche une boîte de dialogue avec un message d'erreur.
        """
        # This should actually never happen.
        wx.MessageBox(
            _(
                """An iPhone or iPod Touch device tried to synchronize with this\n"""
                """task file, but the protocol negotiation failed. Please file a\n"""
                """bug report."""
            ),
            _("Error"),
            wx.OK,
        )

    def clearTasks(self) -> None:
        """
        Efface toutes les tâches actuellement affichées dans les visionneuses de l'application.
        Cette méthode est souvent utilisée lors de la fermeture d'un fichier ou avant l'ouverture d'un nouveau fichier de tâches.
        """
        self.taskFile.clear(False)
        log.info(
            "MainWindow.clearTasks : Toutes les tâches ont été effacées de l’interface."
        )

    # def viewerIsActive(self):
    #     """
    #     Vérifie si une visionneuse est actuellement active dans la fenêtre principale.
    #
    #     Returns :
    #         bool : True si une visionneuse est active, sinon False.
    #     """
    #     pass
    #
    # def toggleVisibility(self):
    #     """
    #     Alterne la visibilité de la fenêtre principale entre minimisée et restaurée.
    #     """
    #     pass
    #
    # def startTrackingTime(self):
    #     """
    #     Démarre le suivi du temps pour les tâches sélectionnées, en gérant les événements de démarrage et d'arrêt pour les tâches.
    #     """
    #     pass
    #
    # def onRestoreToolBar(self, event):
    #     """
    #     Restaure la barre d'outils si elle est masquée.
    #
    #     Args :
    #         event (wx.Event) : L'événement déclencheur.
    #     """
    #     pass

    def restoreTasks(self, categories, tasks) -> None:
        """
        Restaure les catégories et tâches dans le fichier de tâches.

        Cette méthode efface d'abord les tâches et catégories actuelles, puis ajoute celles fournies en paramètre.

        Args :
            categories (list) : Liste des catégories à restaurer.
            tasks (list) : Liste des tâches à restaurer.
        """
        log.debug(
            "MainWindow.restoreTasks : Restauration des tâches : %d catégories, %d tâches",
            len(categories),
            len(tasks),
        )
        self.taskFile.clear(
            False
        )  # Efface les catégories et tâches actuelles sans sauvegarder.
        self.taskFile.categories().extend(
            categories
        )  # Ajoute les nouvelles catégories.
        self.taskFile.tasks().extend(tasks)  # Ajoute les nouvelles tâches.

    def addIPhoneCategory(self, category) -> None:
        """
        Ajoute une catégorie synchronisée à partir d'un iPhone.

        Args :
            category (Category) : La catégorie à ajouter.
        """
        log.info("Catégorie iPhone ajoutée : %s", category)
        self.taskFile.categories().append(
            category
        )  # Ajoute la catégorie à la liste des catégories.

    def removeIPhoneCategory(self, category) -> None:
        """
        Supprime une catégorie synchronisée avec un iPhone.

        Args :
            category (Category) : La catégorie à supprimer.
        """
        log.info(
            "MainWindow.removeIPhoneCategory : Catégorie iPhone supprimée : %s",
            category,
        )
        self.taskFile.categories().remove(
            category
        )  # Supprime la catégorie de la liste.

    # @staticmethod
    def modifyIPhoneCategory(self, category, name) -> None:
        """
        Modifie le nom d'une catégorie synchronisée depuis un iPhone.

        Args :
            category (Category) : La catégorie à modifier.
            name (str) : Le nouveau nom de la catégorie.
        """
        log.info(
            "Catégorie %s iPhone modifiée, nouveau nom : %s", category, name
        )
        category.setSubject(name)  # Modifie le sujet (nom) de la catégorie.

    def addIPhoneTask(self, task, categories) -> None:
        """
        Ajoute une tâche synchronisée depuis un iPhone et lui associe des catégories.

        Args :
            task (Task) : La tâche à ajouter.
            categories (list) : Les catégories à associer à la tâche.
        """
        log.info(
            "Tâche iPhone %s ajoutée avec %d catégories", task, len(categories)
        )
        self.taskFile.tasks().append(task)  # Ajoute la tâche à la liste.
        for category in categories:  # Associe les catégories à la tâche.
            task.addCategory(category)
            category.addCategorizable(task)

    def removeIPhoneTask(self, task) -> None:
        """
        Supprime une tâche synchronisée depuis un iPhone.

        Args :
            task (Task) : La tâche à supprimer.
        """
        log.info("Tâche iPhone supprimée : %s", task)
        self.taskFile.tasks().remove(task)  # Supprime la tâche de la liste.

    # @staticmethod
    def addIPhoneEffort(self, task, effort) -> None:
        """
        Ajoute un effort à une tâche synchronisée depuis un iPhone.

        Args :
            task (Task) : La tâche à laquelle l'effort est ajouté.
            effort (Effort) : L'effort à ajouter.
        """
        log.info("Effort iPhone %s ajoutée à la tâche %s", effort, task)
        if task is not None:
            task.addEffort(effort)  # Ajoute l'effort à la tâche.

    # @staticmethod
    def modifyIPhoneEffort(self, effort, subject, started, ended) -> None:
        """
        Modifie un effort synchronisé depuis un iPhone.

        Args :
            effort (Effort) : L'effort à modifier.
            subject (str) : Le sujet (nom) de l'effort.
            started (datetime) : La date et l'heure de début de l'effort.
            ended (datetime) : La date et l'heure de fin de l'effort.
        """
        log.info(
            "MainWindow.modifyIPhoneEffort: Effort iPhone %s modifié.", effort
        )
        effort.setSubject(subject)  # Modifie le sujet (nom) de l'effort.
        effort.setStart(started)  # Modifie la date de début.
        effort.setStop(ended)  # Modifie la date de fin.

    # @staticmethod
    def modifyIPhoneTask(
        self,
        task,
        subject,
        description,
        plannedStartDateTime,
        dueDateTime,
        completionDateTime,
        reminderDateTime,
        recurrence,
        priority,
        categories,
    ) -> None:
        """
        Modifie une tâche synchronisée depuis un iPhone.

        Args :
            task (Task) : La tâche à modifier.
            subject (str) : Le sujet (nom) de la tâche.
            description (str) : La description de la tâche.
            plannedStartDateTime (datetime) : La date de début planifiée.
            dueDateTime (datetime) : La date d'échéance.
            completionDateTime (datetime) : La date de complétion de la tâche.
            reminderDateTime (datetime) : La date du rappel.
            recurrence (Recurrence) : La récurrence de la tâche.
            priority (int) : La priorité de la tâche.
            categories (set) : Ensemble des catégories à associer à la tâche.
        """
        log.info("Tâche iPhone modifiée : %s", task)
        task.setSubject(subject)  # Modifie le sujet de la tâche.
        task.setDescription(description)  # Modifie la description.
        task.setPlannedStartDateTime(
            plannedStartDateTime
        )  # Modifie la date de début planifiée.
        task.setDueDateTime(dueDateTime)  # Modifie la date d'échéance.
        task.setCompletionDateTime(
            completionDateTime
        )  # Modifie la date de complétion.
        task.setReminder(reminderDateTime)  # Modifie la date du rappel.
        task.setRecurrence(recurrence)  # Modifie la récurrence.
        task.setPriority(priority)  # Modifie la priorité.

        if categories is not None:  # Protocole v2
            for toRemove in task.categories() - categories:
                task.removeCategory(toRemove)
                toRemove.removeCategorizable(task)

            for toAdd in categories - task.categories():
                task.addCategory(toAdd)
                toAdd.addCategorizable(task)
