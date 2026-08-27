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
    Imports: Various libraries like tkinter, PIL, and taskcoachlib modules.


Module mainwindow.py - Fenêtre principale de Task Coach.

Ce module définit la fenêtre principale de l'application Task Coach.
Il gère l'interface graphique, la gestion des événements,
ainsi que des fonctionnalités telles que la gestion de la barre d'outils, de la barre de statut, et des visionneuses de tâches.

Classes :
    - MainWindow : Classe principale représentant la fenêtre de l'application.

Fonctionnalités clés :

    Initialisation :
        Hérite de tkinter.Frame.
        Initialise les variables membres telles que iocontroller, taskFile, les paramètres et les indicateurs d'état sale et d'arrêt.
        # Lie les événements de fenêtre.
        Crée des composants de fenêtre tels que les visionneuses, la barre d'état, la barre de menus et le contrôleur de rappel.
        # Définit la fenêtre titre basé sur le nom de fichier et l'état sale.
        Met à jour le titre de la fenêtre racine en fonction du nom du fichier et de l'état sale.
    Gestion des fenêtres :
        Fournit des méthodes pour afficher/masquer la barre d'outils et la barre d'état.
        # Gère les événements comme la fermeture de la fenêtre, l'iconification et le redimensionnement.
    Interaction avec la visionneuse :
        Fournit des méthodes pour faire avancer la sélection et obtenir le nombre de spectateurs.
    Gestion de l'alimentation :
        Répond à l'état d'alimentation et envoie des notifications.
    Synchronisation iPhone :
        Crée un cadre de progression pour la synchronisation iPhone.
        Définit les méthodes de gestion des types de synchronisation iPhone, des échecs de protocole et de la modification/ajout/suppression de tâches et de catégories.
"""

# La conversion de mainwindow.py de wxPython à tkinter est une tâche complexe
# en raison des différences fondamentales entre les deux frameworks GUI,
# en particulier la gestion des mises en page (AUI),
# des événements et des composants spécifiques.
# Le fichier mainwindow.py s'appuie fortement sur des classes et
# des comportements spécifiques à wxPython provenant de taskcoachlib.
#
# Une conversion directe et fonctionnelle de l'ensemble du fichier n'est pas possible
# sans une réécriture significative des modules taskcoachlib dépendants
# (comme viewer, toolbar, menu, status, etc.) pour qu'ils fonctionnent avec tkinter.
#
# Cependant, je peux vous fournir une conversion conceptuelle de la structure
# de base de MainWindow vers tkinter, en remplaçant les éléments wxPython
# par leurs équivalents tkinter et en utilisant des placeholders
# pour les fonctionnalités complexes qui nécessiteraient une réimplémentation complète des dépendances.
#
# Voici les principales adaptations :
#
#     wx.Frame et AuiManagedFrameWithDynamicCenterPane sont remplacés par tkinter.Tk.
#     tkinter utilise un modèle de gestion de géométrie différent (pack, grid, place)
#     et n'a pas d'équivalent direct à AUI.
#     Pour une application complexe comme Task Coach, cela nécessiterait une refonte majeure de la mise en page.
#
#     La gestion des événements wx.EVT_CLOSE, wx.EVT_ICONIZE, wx.EVT_SIZE est
#     remplacée par les méthodes de protocole de fenêtre et les bind de tkinter.
#
#     Les barres d'état (wx.StatusBar) et les barres de menus (wx.MenuBar, wx.Menu)
#     sont remplacées par tkinter.Label (ou Frame) et tkinter.Menu.
#
#     Les appels à wx.ArtProvider et wx.MessageBox sont remplacés par
#     des équivalents Pillow (PIL.ImageTk.PhotoImage) et tkinter.messagebox.
#
#     Les dépendances taskcoachlib : C'est le plus grand défi.
#     Des modules comme viewer, toolbar, uicommand, remindercontroller, windowdimensionstracker,
#     iphone sont très probablement écrits spécifiquement pour wxPython.
#     Pour que cette conversion soit pleinement fonctionnelle,
#     ces modules devraient également être convertis ou réimplémentés pour tkinter.
#     Dans l'exemple ci-dessous, je les ai traités comme des mocks ou des placeholders.
#
#
# Explication des changements et limitations :
#
#     Héritage de tk.Tk : La classe MainWindow hérite maintenant directement de tkinter.Tk,
#     la classe de base pour la fenêtre principale d'une application tkinter.
#     MainWindow hérite désormais de tk.Frame et prend le parent (tk.Tk) en argument dans son constructeur.
#
#     Initialisation :
#
#         super().__init__() initialise la fenêtre tkinter.
#         Le constructeur de MainWindow accepte maintenant un argument parent
#         qui est la fenêtre tk.Tk racine.
#
#         Les appels aux méthodes de fenêtre (comme title, geometry, protocol,
#         iconphoto et bind) ont été déplacés dans le bloc
#         if __name__ == "__main__": et sont appliqués à l'objet root,
#         qui est une instance de tk.Tk.
#         sont déplacés dans tkapplication.py.
#         self.title() définit le titre de la fenêtre.
#
#         self.geometry("800x600") définit une taille par défaut.
#
#         self.protocol("WM_DELETE_WINDOW", self.onClose) gère l'événement de fermeture de la fenêtre.
#
#         self.bind("<Unmap>", self.onIconify) gère la minimisation de la fenêtre
#         (l'événement <Unmap> est déclenché sur X11 lorsque la fenêtre est iconifiée).
#
#         self.bind("<Configure>", self.onResize) gère le redimensionnement.
#
#     Gestion des composants UI :
#
#         Barre de statut (_create_status_bar) : Remplacée par un tk.Label packé en bas de la fenêtre.
#
#         Barre de menus (__create_menu_bar) : Remplacée par un tk.Menu configuré via self.config(menu=self.menu_bar).
#
#         Conteneur de visionneuses (_create_viewer_container) : Un simple tk.Frame est utilisé comme placeholder.
#         La complexité de la gestion des multiples vues et de leur disposition (AUI) est abstraite.
#
#         Barre d'outils (showToolBar) : Un tk.Frame contenant des tk.Button factices est créé et packé en haut.
#         La logique de AuiPaneInfo est simplifiée.
#
#     Gestion des événements :
#
#         onClose, onIconify, onResize sont adaptés pour les événements tkinter.
#         La logique de la méthode onClose est modifiée pour qu'elle
#         appelle self.parent.destroy() ou self.parent.withdraw(),
#         car c'est la fenêtre racine qui doit être fermée ou cachée, et non le Frame.
#
#         event.Skip() n'est pas utilisé dans tkinter de la même manière que dans wxPython.
#         Pour onClose, self.destroy() ferme la fenêtre, et self.withdraw() la cache.
#
#         De même, la méthode __setTitle a été modifiée pour définir le titre
#         de la fenêtre racine (self.parent.title(...))
#         au lieu d'essayer de le faire sur le Frame lui-même.
#
#     Dépendances taskcoachlib :
#
#         Toutes les classes de taskcoachlib (comme IOController, Settings, ViewerContainer, ArtProvider, UICommand, etc.)
#         sont remplacées par des mocks (objets factices).
#         Ces mocks implémentent les méthodes minimales nécessaires pour que le code
#         de MainWindow puisse s'exécuter sans erreur.
#
#         Pour une application fonctionnelle, chaque module de taskcoachlib devrait
#         être réécrit ou adapté pour tkinter, ce qui est une tâche considérable.
#
#     wx.CallAfter : Ce mécanisme de wxPython pour différer l'exécution d'une fonction sur le thread principal de l'UI
#     est généralement remplacé par widget.after() dans tkinter, mais dans de nombreux cas,
#     il n'est plus nécessaire si la logique de disposition est gérée différemment.
#
#     AUI (wx.lib.agw.aui) : Le gestionnaire de mise en page AUI est une fonctionnalité majeure de wxPython
#     qui n'a pas d'équivalent direct dans tkinter.
#     La gestion des "panes" (volets) et des "perspectives"
#     (__restore_perspective, __save_perspective) est donc simulée ou omise.
#
# Cette conversion vous donne une base tkinter pour MainWindow,
# mais elle met en évidence l'ampleur du travail de réécriture nécessaire
# pour adapter une application wxPython complexe à tkinter.


import logging
import tkinter
import tkinter as tk

# from tkinterdnd2 import *
# from tkinterdnd2 import TkinterDnD as tk
from tkinter import ttk
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk

# from pubsub import pub # pubsub est cross-platform, mais son intégration peut varier


# --- Simulation des dépendances taskcoachlib pour tkinter ---
# Ces classes sont des placeholders. Elles devraient être converties
# ou réécrites pour tkinter pour une fonctionnalité complète.

# class MockIOController:
#     def __init__(self):
#         self.filename_changed_callbacks = []
#         self.dirty_changed_callbacks = []
#     def filename(self): return "mock_taskfile.tsk"
#     def isDirty(self): return False
#     def stop(self): logging.info("MockIOController: Arrêt.")
#     def clear(self, save): logging.info(f"MockIOController: Effacement (sauvegarde: {save}).")
#     def tasks(self): return []
#     def efforts(self): return []
#     def categories(self): return []


# class MockSettings:
#     def __init__(self):
#         self._settings = {
#             "window": {"hidewhenclosed": False, "hidewheniconized": False, "maximized": False},
#             "view": {"toolbar": True, "statusbar": True, "perspective": "", "toolbarperspective": ""},
#             "feature": {"syncml": False, "iphone": False, "usesm2": False, "showsmwarning": False},
#             "syncml": {"showwarning": True}
#         }
#     def getboolean(self, section, option): return self._settings.get(section, {}).get(option, False)
#     def get(self, section, option): return self._settings.get(section, {}).get(option)
#     def getvalue(self, section, option): return self._settings.get(section, {}).get(option)
#     def set(self, section, option, value):
#         if section not in self._settings: self._settings[section] = {}
#         self._settings[section][option] = value
#     def setboolean(self, section, option, value): self.set(section, option, value)
#     def getint(self, section, option): return int(self._settings.get(section, {}).get(option, 0))


# class MockApplication:
#     def quitApplication(self): return True
#     def sessionMonitor(self): return None # Pour simplifier XFCE4 check


# class MockViewerContainer:
#     def __init__(self, parent, settings):
#         self.parent = parent
#         self.settings = settings
#         self._viewers = []
#     def advanceSelection(self, forward): logging.info(f"MockViewerContainer: Avance la sélection (forward: {forward}).")
#     def __len__(self): return len(self._viewers)
#     def add(self, viewer_instance): self._viewers.append(viewer_instance)
#     def componentsCreated(self): logging.info("MockViewerContainer: Composants créés.")


# class MockStatusBar(tk.Label):
#     def __init__(self, parent, viewer_container):
#         super().__init__(parent, text="Barre de statut", bd=1, relief=tk.SUNKEN, anchor=tk.W)
#         self.viewer = viewer_container
#
#     def SetStatusText(self, text, pane=0): self.config(text=text)  # Simplifié pour tkinter


# class MockMainMenu(tk.Menu):
#     def __init__(self, parent, settings, iocontroller, viewer, taskfile):
#         super().__init__(parent)
#         self.add_command(label="Fichier (Mock)")
#         self.add_command(label="Édition (Mock)")
#         # Ajoutez d'autres menus et commandes factices si nécessaire
#         parent.config(menu=self)


# class MockReminderController:
#     def __init__(self, parent, tasks, efforts, settings): logging.info("MockReminderController: Initialisé.")


# class MockIdleController:
#     def __init__(self, parent, settings, efforts): logging.info("MockIdleController: Initialisé.")
#     def stop(self): logging.info("MockIdleController: Arrêt.")


class MockIPhoneSyncFrame(tk.Toplevel):
    def __init__(self, settings, title, icon, parent):
        super().__init__(parent)
        self.title(title)
        self.iconphoto(False, icon)  # Définir l'icône de la fenêtre
        self.geometry("300x200")
        # tk.Label(self, text="Progression de la synchronisation iPhone").pack(pady=20)
        tk.Label(self, text="Progression de la synchronisation iPhone").grid(
            pady=20
        )


class MockIPhoneSyncTypeDialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.value = 0  # Valeur par défaut
        # tk.Label(self, text="Type de synchronisation (Mock)").pack(pady=10)
        tk.Label(self, text="Type de synchronisation (Mock)").grid(pady=10)
        # tk.Button(self, text="OK", command=self.destroy).pack()
        tk.Button(self, text="OK", command=self.destroy).grid()


class MockXFCE4WarningDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("Avertissement XFCE4 (Mock)")
        # tk.Label(self, text="Avertissement XFCE4 (Mock)").pack(pady=10)
        tk.Label(self, text="Avertissement XFCE4 (Mock)").grid(pady=10)
        # tk.Button(self, text="OK", command=self.destroy).pack()
        tk.Button(self, text="OK", command=self.destroy).grid()


# class MockEditor(tk.Toplevel):
#     def __init__(self, parent):
#         super().__init__(parent)
#         self.title("Éditeur (Mock)")
#         tk.Label(self, text="Ceci est un éditeur factice.").pack(pady=10)
#
#     def Close(self): self.destroy()

# class MockArtProvider:
#     @staticmethod
#     def iconBundle(icon_title):
#         # Retourne une PhotoImage factice pour simuler un bundle d'icônes
#         img = Image.new('RGBA', (16, 16), color='blue')
#         return ImageTk.PhotoImage(img)
#     @staticmethod
#     def GetBitmap(name, client, size):
#         # Retourne une PhotoImage factice pour simuler une bitmap
#         img = Image.new('RGBA', size, color='green')
#         return ImageTk.PhotoImage(img)


# Remplacer les imports wx par nos mocks ou tkinter
from taskcoachlib import application, meta, widgetstk, operating_system
from taskcoachlib.config.settings import Settings
from taskcoachlib.guitk import (
    toolbarttk,
    artprovidertk,
    idlecontrollertk,
    iocontrollertk,
    remindercontrollertk,
    statustk,
)  # , viewer,  windowdimensionstracker

# , remindercontroller, status
# !!! viewer crée une boucle infinie d'import avec dialog.editor
from taskcoachlib.guitk.viewer import factorytk

# from taskcoachlib.guitk.uicommand import uicommand
# from taskcoachlib.gui.newid import IdProvider  # ? wx.newid n'a pas d'équivalent !
# from taskcoachlib.gui.dialog.iphone import IPhoneSyncTypeDialog
# from taskcoachlib.gui.dialog.xfce4warning import XFCE4WarningDialog
from taskcoachlib.guitk.dialog.editor import Editor

# from taskcoachlib.gui.iphone import IPhoneSyncFrame
from taskcoachlib.guitk.viewer import factorytk, containertk
from taskcoachlib.widgetstk import frametk
from taskcoachlib.i18n import _

# from taskcoachlib.powermgt import PowerStateMixin # Pas de PowerStateMixin direct dans tkinter
# from taskcoachlib.help.balloontips import BalloonTipManager # Pas de BalloonTipManager direct dans tkinter

# # Utilisation des mocks
# application = MockApplication()
# meta = type('Meta', (object,), {'name': 'Task Coach (Tkinter)', 'version': '1.0'})()
# settings = MockSettings()
# _ = lambda s: s # Simplification pour i18n

# Dépendances pour MainWindow
# Note: Ces dépendances devraient être converties ou réécrites pour tkinter
# Pour l'instant, nous utilisons des mocks ou des équivalents tkinter
# artprovider = MockArtProvider()
# idlecontroller = MockIdleController
# remindercontroller = MockReminderController
# status = type('Status', (object,), {'StatusBar': MockStatusBar})()  # Mock pour StatusBar
# viewer = type('Viewer', (object,), {'container': type('Container', (object,), {'ViewerContainer': MockViewerContainer})(), 'viewerTypes': lambda: []})()
# windowdimensionstracker = type('WindowDimensionsTracker', (object,), {'WindowDimensionsTracker': lambda a, b: type('Tracker', (object,), {'save_position': lambda: None})()})()
# uicommand = type('UICommand', (object,), {
#     'FileOpen': lambda iocontroller: type('Cmd', (object,), {'name': 'FileOpen'})(),
#     'FileSave': lambda iocontroller: type('Cmd', (object,), {'name': 'FileSave'})(),
#     'FileMergeDiskChanges': lambda iocontroller: type('Cmd', (object,), {'name': 'FileMergeDiskChanges'})(),
#     'Print': lambda viewer, settings: type('Cmd', (object,), {'name': 'Print'})(),
#     'EditUndo': lambda: type('Cmd', (object,), {'name': 'EditUndo'})(),
#     'EditRedo': lambda: type('Cmd', (object,), {'name': 'EditRedo'})(),
#     'EffortStartButton': lambda taskList: type('Cmd', (object,), {'name': 'EffortStartButton'})(),
#     'EffortStop': lambda viewer, effortList, taskList: type('Cmd', (object,), {'name': 'EffortStop'})(),
# })()
IdProvider = type(
    "IdProvider", (object,), {"get": lambda: 1}
)()  # Mock pour IdProvider
IPhoneSyncTypeDialog = MockIPhoneSyncTypeDialog
XFCE4WarningDialog = MockXFCE4WarningDialog
# Editor = MockEditor
IPhoneSyncFrame = MockIPhoneSyncFrame

# logging.basicConfig(level=logging.DEBUG) # Décommenter pour les logs
log = logging.getLogger(__name__)


# class MainWindow(tk.Frame):  # Hérite de tk.Frame
class MainWindow(
    tk.LabelFrame, widgetstk.frametk.TtkManagedFrame
):  # Hérite de tk.Frame
    #     PowerStateMixin, BalloonTipManager, widgets.AuiManagedFrameWithDynamicCenterPane
    # ):
    # TODO : convertir AuiManagedFrameWithDynamicCenterPane pour tkinter !
    """
    Classe représentant le cadre/frame principale de Task Coach pour Tkinter.
    """

    def __init__(
        self, parent, iocontroller, taskFile, settings, *args, **kwargs
    ):
        """
        Initialise la fenêtre principale de Task Coach avec les paramètres fournis.

        Cette méthode configure les variables membres, lie les événements, crée les composants de la fenêtre,
        et restaure la perspective de la fenêtre depuis les paramètres.

        Attributs :
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
            parent (tk.Tk) : Classe/fenêtre parente contenant MainWindow.
            iocontroller (IOController) : Contrôleur d'entrée/sortie pour gérer les fichiers.
            taskFile (TaskFile) : Fichier de tâches à manipuler, contenant les tâches, catégories, et efforts.
            settings (Settings) : Paramètres utilisateur de l'application à appliquer à la fenêtre principale.
            *args, **kwargs : Arguments supplémentaires pour la fenêtre.
        """
        log.info("****************************************************")
        log.info("* Début d'initialisation de MainWindow (Tkinter) *****")
        log.info("****************************************************")
        self.__splash = kwargs.pop("splash", None)
        super().__init__(
            parent, *args, text="MainWindow", **kwargs
        )  # Initialisation de tk.Frame

        # Le parent est maintenant la fenêtre racine (tk.Tk)
        self.parent = parent
        # self.root = tk.Toplevel(parent)  # NON
        # self.root.title("Fenêtre principale (maquette)")  # NON
        # self.root.protocol("WM_DELETE_WINDOW", iocontroller.close)  # NON
        # self.title(meta.name)
        # self.title("MainWindow")
        # self.geometry("800x600")  # Taille par défaut
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Pour le viewer

        # self.protocol("WM_DELETE_WINDOW", self.onClose)  # Gérer la fermeture de la fenêtre
        # self.bind("<Unmap>", self.onIconify)  # Gérer la minimisation (Unmap sur X11)
        # self.bind("<Configure>", self.onResize)  # Gérer le redimensionnement

        # Attributs :
        self.iocontroller = iocontroller  # Contrôleur d'entrée/sortie pour la gestion des fichiers.
        self.taskFile = taskFile  # Fichier de tâches contenant les tâches, catégories, et efforts.
        self.settings = settings  # Paramètres utilisateur de l'application.
        self.__filename = None  # Nom du fichier de tâches actuellement ouvert (None par défaut).
        self.__dirty = False  # Indicateur indiquant si le fichier a été modifié sans être sauvegardé (initialisé à False).
        self.__shutdown = False  # Indicateur indiquant si l'application est en cours d'arrêt (initialisé à False).
        self.toolbar_frame = None  # Initialisation de la Barre d'outils pour les actions courantes

        self._handling_resize = False
        # self.__dimensions_tracker = windowdimensionstracker.WindowDimensionsTracker(self, settings)

        log.info(
            "MainWindow: Création et initialisation des composants de la fenêtre :"
        )
        self._create_window_components()  # Crée les composants de la fenêtre (Les viewer, la barre de statut, la barre de menu, les barres d'outils, et le contrôleur de rappel sont créés ici.)
        log.debug(
            "MainWindow: ✅ Création effectuée et initialisation des différents composants de la fenêtre."
        )

        self.__init_window_components()
        log.debug(
            "MainWindow: ✅ Initialisation des composants principaux de la fenêtre terminée et perspective de la fenêtre restaurée."
        )

        self.toolbar_frame.grid(
            row=0, column=0, sticky="ew"
        )  # TODO : A revoir où mettre cette ligne !
        self.viewer.grid(row=1, column=0, sticky="nsew")
        self.status_bar.grid(row=2, column=0, sticky="ew")

        try:
            self.__init_window()
        except Exception as e:
            log.exception(
                f"Problème avec __init__window() : {e}", exc_info=True
            )
        log.debug("MainWindow: ✅ Fenêtre principale Initialisée.")

        self.__register_for_window_component_changes()
        log.debug(
            "MainWindow: ✅ Enregistrement effectué pour recevoir des notifications de changement de composants de fenêtre, comme les barres d'outils et les barres de statut."
        )
        log.debug("MainWindow: ✅ Composants de fenêtre créés.")

        # Simplification pour SyncML et iPhone, car pybonjour n'est pas directement compatible
        if self.settings.getboolean("feature", "iphone"):
            log.warning(
                "La synchronisation iPhone n'est pas supportée dans cette version Tkinter."
            )

        # Contrôleur d'inactivité utilisé pour suivre les efforts sur les tâches. :
        log.debug(
            "MainWindow: Initialise le contrôleur d'inactivité pour le suivi des efforts"
        )
        self._idleController = idlecontrollertk.IdleController(
            self, self.settings, self.taskFile.efforts()
        )

        # wx.CallAfter n'est pas directement nécessaire ici si les composants sont déjà packés/gridés
        # self.after(100, self.checkXFCE4) # Utiliser after pour différer l'appel

        # Placeholder pour l'icône de la fenêtre
        # self.iconphoto(False, artprovidertk.iconBundle("taskcoach"))
        log.info("*********************************************")
        log.info("* MainWindow: ✅ Initialisé avec succès ! *****")
        log.info("*********************************************")

    def onClose(self):
        """
        Gère la fermeture de la fenêtre, en arrêtant le suivi des tâches et en vérifiant si l'application doit quitter.
        """
        log.info(
            "MainWindow.onClose: Fermeture de la fenêtre par l'utilisateur."
        )
        try:
            # Vérifier les paramètres de l'application. :
            app_instance = (
                application.tkapplication.TkinterApplication.getInstance()
            )
            # should_quit = application.TkinterApplication.quitApplication(force=True)
            # should_quit = application.TkinterApplication.quitApplication(self, force=True)  # ?
            should_quit = app_instance.quitApplication(force=True)  # ?
            should_hide = self.settings.getboolean("window", "hidewhenclosed")

            self.closeEditors()

            if should_quit or self.__shutdown:
                log.debug("MainWindow.onClose: Quitter l'application.")
                # self.saveSettings()  # !!! Peut-être déjà trop tard ! quitApplication a déjà enregistré !
                # Assurer la fermeture propre des ressources.
                self.taskFile.stop()  # Arrêter le suivi des tâches.
                self._idleController.stop()  # Arrêter le contrôleur d'inactivité.
                # self.closeEditors()  # Fermer les éditeurs.
                # self.destroy()  # Détruit la fenêtre Tkinter
                # self.parent.destroy()  # Détruit la fenêtre Tkinter racine  # _tkinter.TclError: can't invoke "destroy" command: application has been destroyed
                # self.root.destroy()
            elif should_hide:
                log.debug("MainWindow.onClose: Fenêtre minimisée/cachée.")
                # self.withdraw()  # Cache la fenêtre
                self.parent.withdraw()  # Cache la fenêtre racine
            else:
                log.debug("MainWindow.onClose: Fermeture par défaut.")
                self.saveSettings()
                self.taskFile.stop()
                self._idleController.stop()
                # self.destroy()
                self.parent.destroy()
                # self.root.destroy()
        except Exception as e:
            log.exception(
                "MainWindow.onClose: Erreur inattendue lors de la fermeture : %s",
                e,
            )
        # Arrêtez le thread de détection d'inactivité à la fin du programme.
        self._idleController.stop()
        log.info("MainWindow.onClose: Fenêtre fermée par l'utilisateur.")

    def onIconify(self, event):
        """
        Gère la minimisation de la fenêtre.
         Cache la fenêtre si l'option "hidewheniconized" est activée dans les paramètres.
        """
        # # Pour Tkinter, <Unmap> est déclenché quand la fenêtre est minimisée
        # if self.settings.getboolean("window", "hidewheniconized"):
        #     # Remplacez <Unmap> par une vérification de l'état de la fenêtre :
        if self.parent.wm_state() == "iconic":
            # self.withdraw()  # Cache la fenêtre
            self.parent.withdraw()  # Cache la fenêtre racine
            log.debug("MainWindow.onIconify: Fenêtre iconifiée et cachée.")
        else:
            log.debug("MainWindow.onIconify: Fenêtre iconifiée (non cachée).")

    def show(self):
        """Met la fenêtre racine au premier plan"""
        # self.parent.pack()  # ?
        self.parent.lift()  # Met la fenêtre racine au premier plan

    def onResize(self, event):
        """
        Gère le redimensionnement de la fenêtre, notamment l'ajustement de la barre d'outils.
        """
        # ignorer les événements déclenchés par ton propre code
        if self._handling_resize:
            return
        self._handling_resize = True
        # Tkinter gère automatiquement le redimensionnement des widgets packés/gridés
        # Cette méthode peut être utilisée pour des logiques de redimensionnement personnalisées
        # new_width = self.winfo_width()
        new_width = self.parent.winfo_width()
        # new_height = self.winfo_height()
        new_height = self.parent.winfo_height()
        self.after(10, lambda: setattr(self, "_handling_resize", False))
        log.debug(
            f"MainWindow.onResize: Fenêtre redimensionnée à {new_width}x{new_height}."
        )

        # Pour les barres d'outils et de statut, Tkinter gère la géométrie automatiquement
        # si elles sont packées ou gridées correctement.
        # Pas besoin de manager.Update() comme dans AUI.

    # méthodes suivantes :
    def setShutdownInProgress(self) -> None:
        """
        Indique que le processus d'arrêt de l'application est en cours, afin d'éviter toute autre action durant cette phase.
        """
        log.info(
            "MainWindow.setShutdownInProgress: Le processus d'arrêt de l'application est en cours."
        )
        self.__shutdown = True

    def _create_window_components(self) -> None:
        """
        Crée et initialise les différents composants de la fenêtre,
        comme les barres d'outils, les barres de statut, et les autres éléments de l'interface graphique.

        Les viewer, la barre de statut, la barre de menu, et le contrôleur de rappel sont créés ici.
        """
        # La méthode _create_window_components dans MainWindow appelle showToolBar
        # pour s'assurer que la barre d'outils est instanciée lors de la création de la fenêtre.
        log.debug(
            "MainWindow._create_window_components: Création du conteneur pour les visionneuses."
        )
        self._create_viewer_container()
        log.debug(
            "mainWindow._create_window_components : Lance une classe-méthode pour ajouter des viewers dans self.viewer."
        )
        # viewer.factorytk.addViewers(self.viewer, self.taskFile, self.settings)
        factorytk.addViewers(
            self.viewer, self.taskFile, self.settings
        )  # Ajoute les visualiseurs
        # add_viewers_strategy = addViewers(viewer_container, mock_task_file, mock_settings)
        # add_viewers_strategy = viewer.factory.addViewers(self.viewer, self.taskFile, self.settings)
        # add_viewers_strategy()
        # self.viewer.addViewer(self.viewer, self.taskFile, self.settings)

        log.debug(
            "MainWindow._create_window_components: Création de la barre de statut."
        )
        self._create_status_bar()
        log.debug(
            "MainWindow._create_window_components: Création de la barre de menu."
        )
        self.__create_menu_bar()
        log.debug(
            "MainWindow._create_window_components: Création du contrôleur de rappel des tâches et efforts."
        )
        self.__create_reminder_controller()
        log.debug("MainWindow._create_window_components: Composants créés.")
        self.viewer.componentsCreated()  # Appeler la méthode
        log.debug("mainWindow._create_window_components : Terminé !")
        # self.showToolBar(self.settings.getboolean("view", "toolbar"))
        self.showToolBar(
            True
        )  # Toujours afficher la barre d'outils pour l'instant

    def _create_viewer_container(self) -> None:
        """
        Crée le conteneur pour les visionneuses (tâches, notes, etc.) dans la fenêtre principale.
        Ce conteneur gère l'affichage et l'organisation des différentes visionneuses.
        """
        # Le cadre (Frame) que vous voyez est très probablement la fenêtre principale de l'application (MainWindow),
        # qui est une instance de tkinter.Frame.
        #
        # Le fait que vous voyez ce cadre signifie que la solution précédente a fonctionné :
        # votre fenêtre principale s'affiche désormais.
        # Le Taskviewer est un composant qui s'affiche à l'intérieur de cette fenêtre principale, ce qui est l'étape suivante.
        #
        # D'après les fichiers que vous avez fournis, le Taskviewer est créé et géré par le MainWindow.
        # Le MainWindow est responsable d'initialiser ses composants internes.
        #
        # Prochaine étape : Vérifier l'initialisation du Taskviewer
        #
        # Le problème est probablement que le Taskviewer n'est pas correctement créé ou positionné
        # à l'intérieur de la MainWindow.
        #
        # Pour que le Taskviewer s'affiche, vous devez
        # vérifier et/ou modifier le fichier mainwindowtk.py pour
        # vous assurer que ces actions sont effectuées :
        #
        #     La classe MainWindow doit créer une instance du ViewerContainer pour gérer les vues.
        #
        #     Elle doit ensuite utiliser la factory (la fabrique de vues) pour instancier le Taskviewer.
        #
        #     Enfin, elle doit ajouter le Taskviewer au ViewerContainer.
        #
        # Pour le moment, votre journal (taskcoach.log) confirme que la MainWindow est initialisée avec succès, mais il n'y a pas de mention explicite de l'initialisation du Taskviewer après cette étape.
        # Assurez-vous que cette partie est bien présente et fonctionnelle
        log.debug(
            "MainWindow._create_viewer_container : utilise viewer.container.ViewerContainer pour créer le conteneur de visionneuses self.viewer."
        )
        # self.viewer = viewer.containertk.ViewerContainer(self, self.settings)
        log.debug(
            f"MainWindow._create_viewer_container : création de self.viewer avec parent_widget={self}."
        )
        self.viewer = containertk.ViewerContainer(self, self.settings)
        # Tkinter: Les viewers seraient des widgets Tkinter packés ou gridés
        # Pour l'exemple, nous allons juste créer un Frame comme conteneur principal
        # self.viewer_frame = tk.Frame(self, bg="lightgray")
        # self.viewer_frame.pack(expand=True, fill=tk.BOTH)
        # TODO : A retirer quand viewertk sera créé !
        # Non, le code que je vous ai suggéré ne devrait pas être dans une méthode séparée nommée _create_viewer_container.
        # Bien que cette méthode puisse exister dans la version originale de Task Coach pour wxPython,
        # d'après les fichiers que vous avez fournis,
        # le code pour créer le conteneur de vues (ViewerContainer)
        # et la fabrique de vues (ViewerFactory) est directement placé dans la méthode constructeur __init__() de la classe MainWindow.
        #
        # La méthode __init__() est l'endroit approprié pour initialiser les composants de votre interface utilisateur.
        #
        # Solution:
        #
        # Pour que le Taskviewer s'affiche correctement, vous devez
        # vous assurer que la méthode __init__ de la classe MainWindow dans mainwindowtk.py contient les lignes suivantes :
        # # Crée le conteneur pour les viewers
        # log.debug("MainWindow._create_viewer_container : crée le conteneur pour les viewers.")
        # self._frame_view = ttk.Frame(self, relief=tk.SUNKEN)
        # self._frame_view.pack(side="right", fill="both", expand=True)
        #
        # self._viewer_container = viewer.container.ViewerContainer(self._frame_view, self.settings)
        # self._viewer_container.pack(fill="both", expand=True)
        #
        # # Crée une fabrique pour les viewers et leur ajoute
        # # Cette ligne de code instancie la classe addViewers en lui passant
        # # le conteneur de vues, le fichier de tâches et les paramètres.
        # # Dès que cette instance est créée, sa méthode __init__ appellera __add_all_viewers(),
        # # qui à son tour créera et ajoutera les visualisateurs à l'intérieur du conteneur.
        # log.debug("MainWindow._create_viewer_container : crée une fabrique pour les viewers.")
        # # self._viewer_factory = factory.add_viewers(self._viewer_container, self, self.taskFile, self.settings)
        # self._viewer_factory = factory.addViewers(self._viewer_container, self.taskFile, self.settings)
        # # En ajoutant ce code, vous vous assurez que le ViewerContainer et le Taskviewer (créé par la factory)
        # sont correctement instanciés et positionnés dans le MainWindow.
        # C'est la raison pour laquelle vous ne voyiez qu'un cadre vide,
        # car la fenêtre principale était bien affichée,
        # mais son contenu n'était pas encore correctement chargé.
        # log.debug("MainWindow._create_viewer_container : Le ViewerContainer pour les viewers sont instanciés et positionnés dans le MainWindow.")

        # self.viewer.pack(anchor="center", fill="both", expand=True)  # Colle le conteneur pour qu'il remplisse l'espace disponible
        self.viewer.grid(
            row=0, column=0, sticky="news"
        )  # Colle le conteneur pour qu'il remplisse l'espace disponible
        log.debug(
            f"MainWindow._create_viewer_container : Conteneur {self.viewer} de visionneuses créé !"
        )

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
            f"MainWindow._create_status_bar : Création d'une barre de status et association avec la fenêtre principale {self}."
        )
        self.status_bar = statustk.StatusBar(self, self.viewer)
        # self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.grid(row=10, column=0, sticky="ews")
        log.info(
            "MainWindow._create_status_bar: Barre de statut créée et associée."
        )

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
        # Tkinter utilise self.config(menu=...) pour la barre de menus
        # Tkinter utilise self.parent.config(menu=...) pour la barre de menus de la fenêtre racine

        from taskcoachlib.guitk import menutk as menu

        log.info(
            f"MainWindow.__create_menu_bar : Création d'une barre de menus et association avec la fenêtre principale {self.parent.__class__.__name__}."
        )
        # self.menu_bar = MockMainMenu(self, self.settings, self.iocontroller, self.viewer, self.taskFile)
        # self.menu_bar = MockMainMenu(self.parent, self.settings, self.iocontroller, self.viewer, self.taskFile)
        # self.menu_bar = menu.MainMenu(self.parent, self.settings, self.iocontroller, self.viewer, self.taskFile)
        log.debug(
            f"MainWindow.__create_menu_bar : création de menu_bar avec self={self} avec self.parent={self.parent} de type {type(self.parent)} et parent_window=self.parent."
        )
        self.menu_bar = menu.MainMenu(
            parent=self.parent,
            parent_window=self.parent,
            settings=self.settings,
            iocontroller=self.iocontroller,
            viewerContainer=self.viewer,
            taskFile=self.taskFile,
        )
        log.debug(
            f"MainWindow.__create_menu_bar : Menu bar created: {self.menu_bar}"
        )
        # self.config(menu=self.menu_bar)
        self.parent.config(menu=self.menu_bar)  # c'est tk qui a le menu.
        # root.config(menu=self.menu_bar)  # root non défini !
        log.debug(
            f"MainWindow.__create_menu_bar : Menu bar attached to parent."
        )
        # self.parent["menu"] = self.menu_bar
        # # menu_bar = tk.Menu(self.root)
        # menu_bar = tk.Menu(self.parent)
        # # self.root.config(menu=menu_bar)
        # self.parent.config(menu=menu_bar)
        # file_menu = tk.Menu(self.menu_bar, tearoff=0)
        # self.menu_bar.add_cascade(label="Fichier", menu=file_menu)
        # self.menu_bar.appendMenu(menu=, label=) ?
        # file_menu.add_command(label="Quitter", command=self.on_quit)

        # log.info("MainWindow.__create_menu_bar: Barre de menus créée et associée.")
        log.info(
            "MainWindow.__create_menu_bar: Barre de menus créée et associée à la fenêtre racine."
        )

    def __create_reminder_controller(self) -> None:
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
        pass
        # self.reminderController = remindercontroller(self, self.taskFile.tasks(), self.taskFile.efforts(), self.settings)

    def addPane(self, page, caption, name, floating: bool = False) -> None:
        """
        Ajoute un volet (pane) à la fenêtre principale.

        Args :
            page : Le volet à ajouter.
            caption (str) : Le titre du volet.
            name (str) : Nom unique du volet.
            floating (bool) : Indique si le volet doit être flottant.
        """
        # Tkinter n'a pas de concept direct de "panes" comme AUI.
        # Cela nécessiterait une logique de gestion de layout personnalisée.
        # Pour l'exemple, nous allons juste "pack" le widget dans le viewer_frame.
        log.warning(
            f"MainWindow.addPane: La gestion des volets (panes) est simplifiée pour Tkinter. Ajout de {caption} ({name})."
        )
        # page.pack(expand=True, fill=tk.BOTH) # Ceci est une simplification.
        # Dans une vraie conversion, il faudrait gérer la disposition des viewers.

    def __init_window(self):
        """
        Initialise la fenêtre principale de Task Coach en définissant la disposition des composants (barres d'outils, barres de statut, etc.)
        et en appliquant les paramètres d'affichage sauvegardés.
        """
        log.debug(
            "MainWindow._init_window : Initialisation de la fenêtre principale."
        )
        # Définition du nom du fichier de tâches
        self.__filename = self.taskFile.filename()
        self.__setTitle()
        # self.SetIcons(artprovider.iconBundle("taskcoach")) # Déjà fait dans __init__
        self.displayMessage(
            _("Welcome to %(name)s version %(version)s")
            % {"name": meta.name, "version": meta.version}
        )
        log.debug("MainWindow.__init_window: Fenêtre principale initialisée.")

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
        # La méthode __init_window_components appelle également showToolBar
        # pour s'assurer que la barre d'outils est affichée au démarrage,
        # en fonction du paramètre "view", "toolbar".
        log.debug(
            "MainWindow.__init_window_components: Initialisation des composants principaux."
        )
        log.debug(
            f"MainWindow.__init_window_components: Affichage de la barre d'outils selon le paramètre : {self.settings.getvalue('view', 'toolbar')}."
        )
        self.showToolBar(
            self.settings.getvalue("view", "toolbar")
        )  # TODO : a remettre dès que possible.
        self.showStatusBar(self.settings.getboolean("view", "statusbar"))
        self.__restore_perspective()  # Appelle la méthode mock
        log.debug(
            "MainWindow.__init_window_components: Composants de fenêtre initialisés."
        )

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
            "MainWindow.__restore_perspective: Restauration de la perspective depuis les paramètres (mock)."
        )
        # Tkinter n'a pas de "perspective" AUI. Cette logique serait à réimplémenter.
        # Pour l'exemple, nous ne faisons rien de fonctionnel ici.
        perspective = self.settings.get("view", "perspective")
        if not perspective:
            log.info(
                "MainWindow.__restore_perspective: Pas de perspective sauvegardée, utilisation de la disposition par défaut."
            )
        else:
            log.info(
                "MainWindow.__restore_perspective: Perspective sauvegardée trouvée (mock)."
            )
            for viewer_type in [
                "taskviewer",
                "categoryviewer",
                "noteviewer",
                "effortviewer",
            ]:
                if self.__perspective_and_settings_viewer_count_differ(
                    viewer_type
                ):
                    log.info(
                        f"MainWindow.__restore_perspective: Le nombre de visionneuses pour {viewer_type} diffère, réinitialisation de la perspective."
                    )
                    perspective = None
                    break

        # Dans une vraie application, vous chargeriez ici une disposition de widgets.
        try:
            if perspective:
                log.info(
                    "MainWindow.__restore_perspective: Restauration de la perspective sauvegardée (mock)."
                )
                # Charger la perspective (logique spécifique à AUI/wxPython à réimplémenter pour Tkinter)
            else:
                log.info(
                    "MainWindow.__restore_perspective: Utilisation de la perspective par défaut (mock)."
                )
                # Charger la perspective par défaut (logique spécifique à AUI/wxPython à réimplémenter pour Tkinter)
                self.settings.set("view", "perspective", "default_perspective")
        except Exception as e:
            log.exception(
                f"MainWindow.__restore_perspective: Erreur lors de la restauration de la perspective : {e}"
            )
            messagebox.showerror(
                _("Error"),
                _(
                    "Could not restore window layout. Using default layout instead."
                ),
            )
            # Charger la perspective par défaut (logique spécifique à AUI/wxPython à réimplémenter pour Tkinter)
            self.settings.set("view", "perspective", "default_perspective")

        # S'assurer que tous les panneaux sont visibles pour éviter les "panneaux zombies".
        # for Frame in self.paned_windows():
        #     # Frame.Show()  # wxPython
        #     Frame.pack()  # Tkinter
        if self.viewer.winfo_viewable():
            log.debug(
                f"MainWindow.__restore_perspective: Les panneaux {self.viewer} sont déjà visibles."
            )
        else:
            log.debug(
                f"MainWindow.__restore_perspective: Rendre les panneaux {self.viewer} visibles."
            )
            # self.viewer.grid()  # Tkinter
            self.viewer.grid_info()  # Tkinter
            # for frame in self.viewer.get_all_frames():
            # frame.grid()  # Tkinter
            # if hasattr(frame.window, "title"):
            # if hasattr(self.viewer, "title"):
            #     # frame.window.title(frame.get_translated_title())
            #     self.viewer.title(self.viewer.winfo_name())

        log.debug(
            "MainWindow.__restore_perspective: Perspective restaurée (mock)."
        )

    def __perspective_and_settings_viewer_count_differ(self, viewer_type):
        """
        Vérifie si le nombre de visionneuses dans la perspective actuelle de la fenêtre diffère de celui sauvegardé dans les paramètres.

        Returns :
            (bool) : True si le nombre de visionneuses diffère, sinon False.
        """
        # Cette logique est spécifique à AUI. Dans Tkinter, cela dépendrait de votre gestionnaire de layout.
        # return False  # Simplifié pour le mock
        log.debug(
            f"MainWindow.__perspective_and_settings_viewer_count_differ: Vérification du nombre de visionneuses pour {viewer_type} (mock)."
        )
        perspective = self.settings.get("view", "perspective")
        perspective_viewer_count = 1  # Mock : extraire le nombre de viewers du type viewer_type dans la perspective
        perspective_viewer_count = perspective.count(f"name={viewer_type}")
        # settings_viewer_count = self.settings.getint("view", f"{viewer_type}_count")  # TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
        # settings_viewer_count = self.settings.getint("view", f"{viewer_type}count")
        settings_viewer_count = (
            self.settings.getint("view", f"{viewer_type}_count") or 1
        )  # Mock : obtenir le nombre de viewers du type viewer_type dans les paramètres
        log.debug(
            f"MainWindow.__perspective_and_settings_viewer_count_differ: perspective_viewer_count={perspective_viewer_count}, settings_viewer_count={settings_viewer_count}"
        )
        if perspective_viewer_count == settings_viewer_count:
            return False
        if not perspective:
            return True
        return True

    def __register_for_window_component_changes(self):
        """
        S'enregistre pour recevoir des notifications de changement de composants de fenêtre, comme les barres d'outils et les barres de statut.
        Cela permet de mettre à jour l'affichage des composants en fonction des événements de l'application.
        """
        # Pour Tkinter, on utiliserait des mécanismes de callback ou des systèmes de messages personnalisés
        # si pubsub n'est pas utilisé ou si l'intégration wxPython de pubsub est retirée.
        # pub.subscribe(self.__onFilenameChanged, "taskfile.filenameChanged")
        # pub.subscribe(self.__onDirtyChanged, "taskfile.dirty")
        # pub.subscribe(self.__onDirtyChanged, "taskfile.clean")
        # pub.subscribe(self.showStatusBar, "settings.view.statusbar")
        # pub.subscribe(self.showToolBar, "settings.view.toolbar")
        # Pas d'équivalent direct à EVT_AUI_PANE_CLOSE pour les toolbars dans Tkinter sans AUI.
        pass

    def __onFilenameChanged(self, filename):
        """
        Gère les changements de nom de fichier dans Task Coach et met à jour le titre de la fenêtre en conséquence.

        Args :
            filename (str) : Nom du fichier.
        """
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
        )  # Met à jour l'état interne selon l'état "dirty" du fichier de tâches.
        self.__setTitle()  # Met à jour le titre de la fenêtre pour refléter cet état.

    def __setTitle(self):
        """
        Met à jour le titre de la fenêtre principale en fonction du fichier de tâches actuel.
        Si le fichier a été modifié sans être sauvegardé, un indicateur est ajouté au titre.
        """
        the_title = meta.name
        if self.__filename:
            the_title += f" - {self.__filename}"
        if self.__dirty:
            the_title += " *"
        # self.title(the_title)  # Définit le titre de la fenêtre principale Tkinter
        self.parent.title(the_title)  # Définit le titre de la fenêtre racine

    def displayMessage(self, message, pane=0):
        """
        Affiche un message dans la barre de statut de la fenêtre principale.

        Si une barre de statut est présente, le message est affiché dans le panneau spécifié.

        Args :
            message (str) : Le message à afficher dans la barre de statut.
            pane (int) : Le panneau de la barre de statut où le message doit être affiché (par défaut, le premier panneau).
        """
        if hasattr(self, "status_bar") and self.status_bar:
            # self.status_bar.SetStatusText(message, pane)
            self.status_bar.set_status_text(message, pane)

    def saveSettings(self):
        """
        Sauvegarder les paramètres actuels de la fenêtre,
        y compris les dimensions, la perspective et le nombre de visionneuses.
        """
        log.info(
            "save.Settings : Sauvegarde des paramètres actuels de la fenêtre.(simulation)"
        )
        self.__save_viewer_counts()
        self.__save_perspective()
        self.__save_position()

    def __save_viewer_counts(self):
        """Enregistrez le nombre de visionneuses pour chaque type de visionneuse."""
        log.debug(
            "MainWindow.__save_viewer_counts: Sauvegarde du nombre de viewers (mock)."
        )
        # Logique spécifique à AUI/wxPython à réimplémenter pour Tkinter.
        pass

    def __save_perspective(self):
        """
        Sauvegarde la perspective actuelle de la fenêtre,
        c'est-à-dire l'organisation des différents volets et composants
        (barre d'outils, visionneuses, etc.).
        """
        log.debug(
            "MainWindow.__save_perspective: Sauvegarde de la perspective (mock)."
        )
        # Logique spécifique à AUI/wxPython à réimplémenter pour Tkinter.
        self.settings.set("view", "perspective", "mock_perspective_data")
        # perspective = self.manager.SavePerspective()
        # perspective = self.main_frame.grid_info()
        perspective = self.grid_info()
        self.settings.set("view", "perspective", perspective)

    def __save_position(self) -> None:
        """
        Sauvegarde la position et la taille actuelles de la fenêtre principale dans les paramètres de l'application.
        Cela permet de restaurer la fenêtre à la même position lors de la prochaine ouverture.
        """
        log.debug(
            "MainWindow.__save_position: Sauvegarde de la position (mock)."
        )
        # self.__dimensions_tracker.save_position()  # TODO : convertir windowdimensionstracker pour tkinter

    def closeEditors(self) -> None:
        """
        Ferme tous les éditeurs ouverts dans la fenêtre principale.
        """
        log.info(
            "MainWindow.closeEditors: Fermeture de tous les éditeurs ouverts (mock)."
        )
        # Dans Tkinter, vous devriez garder une liste des Toplevels (éditeurs) ouverts
        # et les détruire ici.
        # Exemple:
        # for editor_instance in self._open_editors:
        #     editor_instance.destroy()
        # self._open_editors.clear()
        pass

    # onCLose est autre part.

    def OnQuit(self):
        pass

    def on_quit(self):
        self.parent.destroy()

    def restore(
        self,
    ) -> (
        None
    ):  # Pas d'événement direct pour restore dans Tkinter comme dans wx
        """
        Restaure la fenêtre principale à partir de la barre des tâches
        lorsque l'application a été minimisée ou réduite dans la barre d'état système.
        """
        if self.settings.getboolean("window", "maximized"):
            # self.state('zoomed')  # Maximise la fenêtre
            self.parent.state("zoomed")  # Maximise la fenêtre racine
        # self.deiconify()  # Restaure la fenêtre si elle est minimisée
        self.parent.deiconify()  # Restaure la fenêtre racine si elle est minimisée
        # self.lift()  # Met la fenêtre au premier plan
        self.parent.lift()  # Met la fenêtre racine au premier plan
        log.debug("MainWindow.restore: Fenêtre restaurée.")

    # onIconify() et onResize() sont autre part.

    def showStatusBar(self, value: bool = True) -> None:
        """
        Affiche ou masque la barre de statut en fonction de la valeur fournie.

        Args :
            value (bool) : True pour afficher, False pour masquer.
        """
        log.debug(
            f"MainWindow.showStatusBar: Affichage de la barre de statut: {value}"
        )
        if hasattr(self, "status_bar") and self.status_bar:
            if value:
                # self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
                self.status_bar.grid(row=10, column=0, sticky="ews")
            else:
                # self.status_bar.pack_forget()
                self.status_bar.grid_forget()

    # Principales modifications et explications :
    #
    # Importer la barre d’outils :
    # Le code importe désormais la classe ToolBar de taskcoachlib.guitk.toolbarttk
    #
    # .
    # createToolBarUICommands : Adapté pour fonctionner avec taskcoachlib.guitk.uicommand
    # au lieu de taskcoachlib.gui.uicommand et les objets Mock ne sont pas définis
    # dans cette version. En conséquence, j’ai commenté les UICommands
    # qui n’avaient pas de taskcoachlib.guitk.uicommand définie dans le mock
    # .
    # showToolBar : Cette méthode crée désormais une instance de toolbarttk.ToolBar
    # et l’intègre dans la fenêtre principale. Si un cadre de barre d’outils existe déjà,
    # il est d’abord détruit pour s’assurer qu’une seule barre d’outils est affichée à la fois
    # .
    # onCloseToolBar : Cette méthode décompresse désormais la barre d’outils
    # à l’aide de pack_forget au lieu de s’appuyer sur des méthodes spécifiques à AUI.
    # .
    # _create_window_components : la méthode showToolBar est appelée ici
    # pour s’assurer qu’elle est instanciée pour la première fois
    # .
    # __init_window_components\u00A0: Maintenant, il appelle showStatusBar
    # pour s’assurer que la barre des statuts est affichée et lancer les composants
    # .
    # Méthodes Perspective : les méthodes getToolBarPerspective et saveToolBarPerspective
    # restent pratiquement inchangées, car elles interagissent principalement avec l’objet settings.

    # Considérations importantes :
    #
    # taskcoachlib.guitk.uicommand : Assurez-vous que le module de commande taskcoachlib.guitk.uicommand
    # est correctement implémenté et contient les sous-classes UICommand nécessaires pour la version Tkinter.
    # Cours simulés (Mock Classes): J’ai laissé le reste des cours simulés définis comme tels.
    # Mise en page : La barre d’outils est affichée en haut de la fenêtre principale.
    # Vous devrez peut-être ajuster la gestion de la mise en page
    # en fonction de la conception globale de votre interface utilisateur.
    #
    # En apportant ces modifications, la classe MainWindow devrait maintenant
    # être en mesure de créer et de gérer une barre d’outils basée sur Tkinter
    # à l’aide de toolbarttk. Classe ToolBar.
    # J’ai essayé d’interroger les fichiers téléchargés mainwindow.py,
    # toolbarttk.py et mainwindowtk.py fournis par l’utilisateur,
    # mais cela n’a pas renvoyé de résultats pertinents,
    # donc la réponse est basée sur les instructions générales fournies.

    def createToolBarUICommands(self):
        """Commandes d'interface utilisateur à mettre sur la barre d'outils de cette fenêtre.

        Crée les commandes UI à afficher dans la barre d'outils de la fenêtre.

        Returns :
            (list) : Une liste d'instances de commandes UI.
        """
        # La méthode createToolBarUICommands dans MainWindow
        # crée la liste des commandes UI qui doivent apparaître dans la barre d'outils.
        # La méthode appendToToolBar dans la classe UICommand
        # (dans base_uicommandtk.py) est responsable de la création du bouton Tkinter
        # pour chaque commande et de son ajout à la barre d'outils.
        # Il faut s'assurer que self.toolbar est correctement défini
        # et que le bouton est bien packé.
        log.debug(
            "MainWindow.createToolBarUICommands: Création des commandes UI de la barre d'outils."
        )
        # Cette liste est manuellement construite et peut contenir :
        #     - des instances de UICommand comme FileOpen, EditUndo, etc.
        #     - None pour indiquer un séparateur.
        #     - 1 pour un espace extensible.
        # Appelée par gui.toolbar.ToolBar.uiCommands
        from taskcoachlib.guitk.uicommand import uicommandtk as uicommand

        # return [
        #     uicommand.FileOpen(iocontroller=self.iocontroller),
        #     uicommand.FileSave(iocontroller=self.iocontroller),
        #     None,
        #     uicommand.EditUndo(),
        #     uicommand.EditRedo(),
        # ]
        uiCommands = [
            uicommand.FileOpen(iocontroller=self.iocontroller),
            uicommand.FileSave(iocontroller=self.iocontroller),
            uicommand.FileMergeDiskChanges(iocontroller=self.iocontroller),
            uicommand.Print(viewer=self.viewer, settings=self.settings),
            None,
            uicommand.EditUndo(),
            uicommand.EditRedo(),
        ]
        # uiCommands.extend(
        #     [
        #         None,
        #         uicommand.EffortStartButton(taskList=self.taskFile.tasks()),
        #         uicommand.EffortStop(
        #             viewer=self.viewer,
        #             effortList=self.taskFile.efforts(),
        #             taskList=self.taskFile.tasks(),
        #         ),
        #     ]
        # )
        # # Retourne explicitement une liste d’instances de UICommand
        return uiCommands

    def getToolBarPerspective(self):
        """
        Retourne la perspective actuelle de la barre d'outils,
        c'est-à-dire l'organisation des boutons et des commandes dans la barre d'outils.

        Returns :
            (str) : La perspective de la barre d'outils.
        """
        log.debug(
            "MainWindow.getToolBarPerspective: Récupération de la perspective de la barre d'outils."
        )
        return self.settings.get("view", "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        """
        Sauvegarde la perspective actuelle de la barre d'outils dans les paramètres de l'application.

        Args :
            perspective (str) : La perspective à sauvegarder.
        """
        log.debug(
            "MainWindow.saveToolBarPerspective: Sauvegarde de la perspective de la barre d'outils."
        )
        self.settings.set("view", "toolbarperspective", perspective)

    # def showToolBar(self, value) -> None:
    def showToolBar(self, show: bool | int | tuple = True) -> None:
        """
        Affiche ou cache la barre d'outils en fonction de la valeur fournie.

        Cette méthode permet de gérer l'affichage de la barre d'outils dans la fenêtre principale de l'application.
        Si une barre d'outils existe déjà, elle est détachée et supprimée avant d'en créer une nouvelle si nécessaire.
        La nouvelle barre d'outils est alors ajoutée à la fenêtre selon les paramètres spécifiés, notamment sa position
        et son comportement de redockage.
        Cette méthode est responsable de la création et de l'affichage de la barre d'outils.
        Elle doit être appelée avec la valeur True pour afficher la barre.
        Elle vérifie d'abord si une barre d'outils existe déjà et,
        si c'est le cas, la détruit avant d'en créer une nouvelle.
        Elle crée une instance de toolbarttk.ToolBar
        et l'intègre dans la fenêtre principale en utilisant pack.
        Si la valeur est False, la barre d'outils est simplement masquée.

        Args :
            show (bool | int) : Si `value` est `False`, la barre d'outils est masquée et supprimée. Si `value` est un
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
        # log.debug(f"MainWindow.showToolBar: Affichage de la barre d'outils: {value}")
        log.debug(
            f"MainWindow.showToolBar: Affichage de la barre d'outils: {show}"
        )
        log.debug(
            f"MainWindow.showToolBar: self.toolbar_frame avant modification: {self.toolbar_frame}"
        )
        log.debug(
            f"MainWindow.showToolBar: self.settings avant modification: {self.settings}"
        )
        # Dans Tkinter, cela impliquerait de créer/détruire ou de pack/pack_forget un Frame contenant les boutons.
        # TODO : s'aider de gui.Mainwindow.showtoolbar et toolbartk:
        # if value:
        #     if not hasattr(self, 'toolbar_frame'):
        #         self.toolbar_frame = tk.Frame(self, bd=1, relief=tk.RAISED)
        #         # Ajouter des boutons factices
        #         for cmd in self.createToolBarUICommands():
        #             if cmd:
        #                 tk.Button(self.toolbar_frame, text=cmd.name).pack(side=tk.LEFT, padx=2, pady=2)
        #             else:
        #                 tk.Frame(self.toolbar_frame, width=10).pack(side=tk.LEFT)  # Séparateur
        #         self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        #     else:
        #         self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        # else:
        #     if hasattr(self, 'toolbar_frame'):
        #         self.toolbar_frame.pack_forget()

        # if hasattr(self, 'toolbar_frame'):
        #     self.toolbar_frame.destroy()  # Remove existing toolbar
        #
        # if value:
        if show:
            if self.toolbar_frame is None:
                # VERSION ACTUELLE (incorrecte)
                # self.toolbar_frame = toolbarttk.ToolBar(self, self.settings)

                # VERSION CORRIGÉE : Ajouter les arguments manquants
                # Ici, la MainWindow est à la fois le parent et le contrôleur.
                # Utilise une taille par défaut pour les icônes (à ajuster si besoin).
                # self.toolbar_frame = toolbarttk.ToolBar(self, self, self.settings, (16, 16))
                self.toolbar_frame = toolbarttk.ToolBar(
                    self, self, self.settings, size=show
                )
                # self.toolbar_frame = toolbarttk.ToolBar(self, self, self.settings, (16, 16), relief=tk.RAISED, border=2)
                log.debug(
                    f"MainWindow.showToolBar: Nouvelle barre d'outils créée: {self.toolbar_frame}."
                )
                # S'assurer que la barre d'outils est placée correctement (ex: en haut)
                # self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, expand=False)
                self.toolbar_frame.grid(row=0, column=0, sticky="ewn")
            else:
                # self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, expand=False)  # Assure-toi qu'elle réapparaît
                self.toolbar_frame.grid(
                    row=0, column=0, sticky="ewn"
                )  # Assure-toi qu'elle réapparaît
        else:
            if self.toolbar_frame:
                # self.toolbar_frame.pack_forget()  # Cache la barre d'outils
                self.toolbar_frame.grid_forget()  # Cache la barre d'outils
        # Example Usage (in your main application window):
        # self.toolbar = ToolBar(self, self.settings, relief=tk.RAISED, bd=2)
        # self.toolbar.pack(side=tk.TOP, fill=tk.X)

    def onCloseToolBar(self, event) -> None:
        """
        Gère la fermeture de la barre d'outils. Si la barre d'outils est fermée, elle est masquée et les paramètres sont mis à jour.

        Args :
            event (wx.Event) : L'événement de fermeture de la barre d'outils.
        """
        log.debug(
            "MainWindow.onCloseToolBar: Fermeture de la barre d'outils (mock)."
        )
        # # Cette méthode est spécifique à AUI. Dans Tkinter, la barre d'outils serait gérée via pack_forget ou destroy.
        # self.settings.setvalue("view", "toolbar", False)  # Mettre à jour les paramètres
        if hasattr(self, "toolbar_frame"):
            # self.toolbar_frame.pack_forget()  # Hide toolbar
            self.toolbar_frame.grid_forget()  # Hide toolbar
        self.settings.setvalue(
            "view", "toolbar", False
        )  # Mettre à jour les paramètres

    # Viewers
    def advanceSelection(self, forward) -> None:
        """
        Fait avancer la sélection des tâches dans les visionneuses de l'application.

        Args :
            forward (bool) : Si True, avance vers l'élément suivant. Si False, recule vers l'élément précédent.
        """
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
        log.debug(
            f"MainWindow.viewerCount: Retourne le nombre de viewers : {len(self.viewer)}."
        )
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
        # Pas d'équivalent direct à PowerStateMixin dans Tkinter.
        # La logique de pubsub devrait être gérée indépendamment du framework GUI.
        log.info(
            f"MainWindow.OnPowerState: État d'alimentation: {state} (mock)."
        )

    # iPhone-related methods.
    def createIPhoneProgressFrame(self):
        """
        Crée et retourne une fenêtre de progression pour la synchronisation avec un iPhone ou un iPod Touch.

        Cette méthode initialise une fenêtre de progression (`IPhoneSyncFrame`) utilisée pour afficher l'état de la synchronisation
        des tâches avec un appareil iPhone ou iPod Touch. Elle configure également l'icône de la fenêtre et son titre.

        Returns :
            IPhoneSyncFrame : La fenêtre de progression pour la synchronisation avec l'iPhone/iPod.
        """
        log.debug(
            "MainWindow.createIPhoneProgressFrame: Création de la fenêtre de progression iPhone (mock)."
        )
        # Utilise MockIPhoneSyncFrame
        return IPhoneSyncFrame(
            self.settings,
            _("iPhone/iPod"),
            # icon=artprovider.GetBitmap("taskcoach", "ART_FRAME_ICON", (16, 16)),  # Utilise MockArtProvider
            # utiliser artprovidertk.MockImage.GetBitmap() ou artprovidertk.IconProvider.getIcon() ?
            # icon=artprovidertk.MockImage.GetBitmap("taskcoach", "ART_FRAME_ICON", (16, 16)),  # Utilise ArtProviderTk
            icon=artprovidertk.ArtProviderTk.GetBitmap(
                "taskcoach", "ART_FRAME_ICON", (16, 16)
            ),  # Utilise ArtProviderTk
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
        log.debug(
            f"MainWindow.getIPhoneSyncType: Obtention du type de synchronisation iPhone pour GUID: {guid} (mock)."
        )
        if (
            guid == self.taskFile.filename()
        ):  # Utilise le nom de fichier comme GUID factice
            return 0  # two-way. Synchronisation bidirectionnelle.
        dlg = IPhoneSyncTypeDialog(self, _("Synchronization type"))
        # dlg.ShowModal() # Tkinter utilise grab_set() pour les modales
        dlg.grab_set()
        self.wait_window(dlg)
        return (
            dlg.value
        )  # Retourne le type de synchronisation choisi par l'utilisateur.

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
        log.debug(
            "MainWindow.notifyIPhoneProtocolFailed: Notification d'échec du protocole iPhone (mock)."
        )
        messagebox.showerror(
            _("Error"),
            _(
                """An iPhone or iPod Touch device tried to synchronize with this\n"""
                """task file, but the protocol negotiation failed. Please file a\n"""
                """bug report."""
            ),
        )

    def clearTasks(self) -> None:
        """
        Efface toutes les tâches actuellement affichées dans les visionneuses de l'application.
        Cette méthode est souvent utilisée lors de la fermeture d'un fichier ou avant l'ouverture d'un nouveau fichier de tâches.
        """
        log.debug("MainWindow.clearTasks: Effacement des tâches (mock).")
        self.taskFile.clear(False)

    def restoreTasks(self, categories, tasks) -> None:
        """
        Restaure les catégories et tâches dans le fichier de tâches.

        Cette méthode efface d'abord les tâches et catégories actuelles, puis ajoute celles fournies en paramètre.

        Args :
            categories (list) : Liste des catégories à restaurer.
            tasks (list) : Liste des tâches à restaurer.
        """
        log.debug(
            f"MainWindow.restoreTasks: Restauration des tâches: {len(categories)} catégories, {len(tasks)} tâches (mock)."
        )
        self.taskFile.clear(False)
        # Ces listes seraient normalement étendues aux vraies listes de tâches/catégories
        # self.taskFile.categories().extend(categories)  # Ajoute les nouvelles catégories.
        # self.taskFile.tasks().extend(tasks)  # Ajoute les nouvelles tâches.

    def addIPhoneCategory(self, category) -> None:
        """
        Ajoute une catégorie synchronisée à partir d'un iPhone.

        Args :
            category (Category) : La catégorie à ajouter.
        """
        log.debug(
            f"MainWindow.addIPhoneCategory: Ajout de la catégorie iPhone: {category} (mock)."
        )
        # self.taskFile.categories().append(category)  # Ajoute la catégorie à la liste des catégories.

    def removeIPhoneCategory(self, category) -> None:
        """
        Supprime une catégorie synchronisée avec un iPhone.

        Args :
            category (Category) : La catégorie à supprimer.
        """
        log.debug(
            f"MainWindow.removeIPhoneCategory: Suppression de la catégorie iPhone: {category} (mock)."
        )
        # self.taskFile.categories().remove(category)  # Supprime la catégorie de la liste.

    def modifyIPhoneCategory(self, category, name) -> None:
        """
        Modifie le nom d'une catégorie synchronisée depuis un iPhone.

        Args :
            category (Category) : La catégorie à modifier.
            name (str) : Le nouveau nom de la catégorie.
        """
        log.debug(
            f"MainWindow.modifyIPhoneCategory: Modification de la catégorie iPhone {category} en {name} (mock)."
        )
        # category.setSubject(name)  # Modifie le sujet (nom) de la catégorie.

    def addIPhoneTask(self, task, categories) -> None:
        """
        Ajoute une tâche synchronisée depuis un iPhone et lui associe des catégories.

        Args :
            task (Task) : La tâche à ajouter.
            categories (list) : Les catégories à associer à la tâche.
        """
        log.debug(
            f"MainWindow.addIPhoneTask: Ajout de la tâche iPhone {task} avec {len(categories)} catégories (mock)."
        )
        # self.taskFile.tasks().append(task)  # Ajoute la tâche à la liste.
        # for category in categories:  # Associe les catégories à la tâche.
        #     task.addCategory(category)
        #     category.addCategorizable(task)

    def removeIPhoneTask(self, task) -> None:
        """
        Supprime une tâche synchronisée depuis un iPhone.

        Args :
            task (Task) : La tâche à supprimer.
        """
        log.debug(
            f"MainWindow.removeIPhoneTask: Suppression de la tâche iPhone: {task} (mock)."
        )
        # self.taskFile.tasks().remove(task)  # Supprime la tâche de la liste.

    def addIPhoneEffort(self, task, effort) -> None:
        """
        Ajoute un effort à une tâche synchronisée depuis un iPhone.

        Args :
            task (Task) : La tâche à laquelle l'effort est ajouté.
            effort (Effort) : L'effort à ajouter.
        """
        log.debug(
            f"MainWindow.addIPhoneEffort: Ajout de l'effort iPhone {effort} à la tâche {task} (mock)."
        )
        # if task is not None:
        #     task.addEffort(effort)  # Ajoute l'effort à la tâche.

    def modifyIPhoneEffort(self, effort, subject, started, ended) -> None:
        """
        Modifie un effort synchronisé depuis un iPhone.

        Args :
            effort (Effort) : L'effort à modifier.
            subject (str) : Le sujet (nom) de l'effort.
            started (datetime) : La date et l'heure de début de l'effort.
            ended (datetime) : La date et l'heure de fin de l'effort.
        """
        log.debug(
            f"MainWindow.modifyIPhoneEffort: Modification de l'effort iPhone {effort} (mock)."
        )
        effort.setSubject(subject)  # Modifie le sujet (nom) de l'effort.
        effort.setStart(started)  # Modifie la date de début.
        effort.setStop(ended)  # Modifie la date de fin.

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
        log.debug(
            f"MainWindow.modifyIPhoneTask: Modification de la tâche iPhone {task} (mock)."
        )
        # task.setSubject(subject)  # Modifie le sujet de la tâche.
        # task.setDescription(description)  # Modifie la description.
        # task.setPlannedStartDateTime(plannedStartDateTime)  # Modifie la date de début planifiée.
        # task.setDueDateTime(dueDateTime)  # Modifie la date d'échéance.
        # task.setCompletionDateTime(completionDateTime)  # Modifie la date de complétion.
        # task.setReminder(reminderDateTime)  # Modifie la date du rappel.
        # task.setRecurrence(recurrence)  # Modifie la récurrence.
        # task.setPriority(priority)  # Modifie la priorité.
        # if categories is not None:  # Protocole v2
        #     for toRemove in task.categories() - categories:
        #         task.removeCategory(toRemove)
        #         toRemove.removeCategorizable(task)
        #     for toAdd in categories - task.categories():
        #         task.addCategory(toAdd)
        #         toAdd.addCategorizable(task)


# # --- Exemple d'utilisation (pour tester la fenêtre Tkinter) ---
# if __name__ == "__main__":
#     # Configurez le logging pour voir les messages de débogage
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
#     # Créez la fenêtre racine (root)
#     root = tk.Tk()
#     root.title(f"{meta.name} (Root Window)")
#     root.geometry("800x600")
#
#     # # Créez des instances factices pour les dépendances
#     # mock_iocontroller = MockIOController()
#     mock_iocontroller = iocontrollertk.IOController(root, mock_taskFile, "messageCallback", Settings)
#     # mock_taskfile = MockIOController()  # Utilisation de MockIOController comme mock pour TaskFile
#     mock_taskfile = mock_iocontroller  # Utilisation de MockIOController comme mock pour TaskFile
#     # mock_settings = MockSettings()
#     mock_settings = Settings()
#
#     # Créez et packez l'instance de MainWindow dans la fenêtre racine
#     # app = MainWindow(root, mock_iocontroller, mock_taskfile, mock_settings)
#     app = MainWindow(root, iocontroller, taskFile, settings)
#     # app.pack(fill=tk.BOTH, expand=True)
#     app.grid()
#
#     # Liez les événements de la fenêtre racine à l'instance de MainWindow
#     root.protocol("WM_DELETE_WINDOW", app.onClose)
#     root.bind("<Unmap>", app.onIconify)
#     root.bind("<Configure>", app.onResize)
#
#     # Définir l'icône de la fenêtre racine
#     root.iconphoto(False, artprovidertk.iconBundle("taskcoach"))
#
#     # Exécutez la boucle principale
#     root.mainloop()
# #     # Instanciez et exécutez la fenêtre principale
# #     app = MainWindow(mock_iocontroller, mock_taskfile, mock_settings)
# #     app.mainloop()
