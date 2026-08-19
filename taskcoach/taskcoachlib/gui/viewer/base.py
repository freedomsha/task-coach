# -*- coding: utf-8 -*-

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

# from __future__ import print_function

# from builtins import object
# from builtins import str

import logging
import wx
from taskcoachlib import (
    patterns,
    widgets,
    command,
    render,
)  # base à besoin des widgets .tooltip.ToolTipMixin, .itemctrl.Column,
from taskcoachlib.widgets.tooltip import ToolTipMixin
from taskcoachlib.widgets.balloontip import (
    BalloonTipManager,
)  # pour __DisplayBallon
from taskcoachlib.i18n import _
from taskcoachlib.gui.uicommand import uicommand
from taskcoachlib.gui import toolbar, artprovider

# try:
#    from taskcoachlib.thirdparty.agw import hypertreelist
# except ImportError:
#    from agw import hypertreelist
# try:
from wx.lib.agw import hypertreelist

# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub
from pubsub import pub

from . import mixin

log = logging.getLogger(__name__)

# debug the metaclass :
# print('le mro de patterns.Observer est ', patterns.Observer.__mro__)
# print('le mro de wx.Panel est ', wx.Panel.__mro__)
# print('le mro de patterns.NumberedInstances est ', patterns.NumberedInstances.__mro__)


# class PreViewer(type(wx.Panel), metaclass=patterns.NumberedInstances):
class PreViewer(type(wx.Panel), patterns.NumberedInstances):
    # def __init__(self):
    # instanceNumber =
    pass


# class Viewer(wx.Panel, patterns.Observer, metaclass=patterns.makecls(patterns.NumberedInstances)):
class Viewer(wx.Panel, patterns.Observer, metaclass=PreViewer):
    # class Viewer(wx.Panel, with_metaclass(patterns.NumberedInstances), patterns.Observer):
    # TypeError: metaclass conflict: the metaclass of a derived class must be
    # a (non-strict) subclass of the metaclasses of all its bases
    """
    Classe de base pour les visionneuses dans Task Coach.

    Une visionneuse affiche les objets du domaine (par exemple, les tâches ou les efforts) au moyen d'un widget
    comme un ListCtrl ou un TreeListCtrl. Cette classe gère la présentation et l'interaction avec ces objets.

    Attributs :
        defaultTitle (str) : Le titre par défaut de la visionneuse.
        defaultBitmap (str) : L'icône par défaut pour la visionneuse.
        viewerImages (list) : Les images utilisées pour afficher les objets de la visionneuse.
    """

    defaultTitle = "Subclass responsibility"
    defaultBitmap = "Subclass responsibility"
    coreObjectType = None
    viewerImages = artprovider.itemImages

    # Les objectifs de cette version :
    # supprimer la double création de la présentation
    # éviter les KeyError sur les kwargs
    # garantir que Filter → Sorter → Viewer reste correctement connecté
    # éviter les bugs lors du freeze/thaw pendant les I/O
    # rendre le code plus lisible pour la maintenance
    def __init__(self, parent, taskFile, settings, *args, **kwargs):
        """
        Initialise une nouvelle visionneuse.

        Cette méthode crée l'interface graphique du viewer et construit
        la chaîne de présentation des données :

            domaine -> filtre -> tri -> viewer

        Args :
            parent (wx.Window) : La fenêtre parente de la visionneuse.
            taskFile (TaskFile) : Le fichier de tâches à visualiser. Modèle contenant les objets du domaine.
            settings (Settings) : Les paramètres de configuration de l'application.
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        # journalisation pour tracer la création du viewer
        log.info(
            f"DEBUG Viewer.__init__ appelé {id(self)}, taskFile:, {id(taskFile)}"
        )  # écrit dans le log l'identifiant du viewer et du modèle
        # initialisation du système d'observateur
        patterns.Observer.__init__(self)
        # journalisation du type de parent
        log.debug(
            f"Viewer : Initialisation d'une nouvelle visionneuse self={self.__class__.__name__}, parent={parent.__class__.__name__}."
        )  # écrit le type de la fenêtre parente
        # initialisation du widget wxPython
        super().__init__(
            parent, -1
        )  # Pourquoi -1 ? Pour définir l'Id automatiquement.
        # new_id = wx.NewIdRef().GetId()
        # new_id = wx.ID_ANY
        # super().__init__(parent, new_id)
        # print('le mro de gui.viewer.base.Viewer est ', Viewer.__mro__)

        # mémorisation de la fenêtre parente
        self.parent = parent  # conserve la référence vers la fenêtre parente
        # mémorisation du modèle
        self.taskFile = (
            taskFile  # stocke le fichier de tâches utilisé par le viewer
        )
        # mémorisation des paramètres
        self.settings = settings  # stocke l'objet de configuration
        # récupération de la section de configuration
        self.__settingsSection = kwargs.pop(
            "settingsSection"
        )  # extrait la section settings associée à ce viewer
        # compteur de gel des événements
        self.__freezeCount = 0  # nombre de freeze actifs
        # Track items changed during bulk operations
        # ensemble des items à rafraîchir après opérations groupées
        self.__pendingRefreshItems = set()  # stocke les objets à rafraîchir
        # The how maniest of this viewer type are we? Used for settings
        # Le quel plus grand nombre de ce type de visualiseur avons-nous? Utilisé pour les paramètres
        # récupération du numéro d'instance du viewer
        self.__instanceNumber = kwargs.pop(
            # "instanceNumber"
            "instanceNumber",
            0,
        )  # KeyError: 'instanceNumber', le "0" évite KeyError si absent
        # indique si ce viewer utilise une section de settings séparée
        self.__use_separate_settings_section = kwargs.pop(
            "use_separate_settings_section", True
        )  # True par défaut
        # cache de sélection
        self.__curselection = []  # stocke les objets actuellement sélectionnés
        # Indicateur pour que nous n'informions pas les observateurs pendant que nous sélectionnons tous les éléments
        # indicateur pour éviter les notifications pendant selectAll
        self.__selectingAllItems = (
            False  # bloque les notifications pendant sélection massive
        )
        # Menus contextuels que nous devons détruire avant de fermer le visualiseur pour empêcher
        # les fuites de mémoire :
        # liste des menus popup à détruire à la fermeture
        self._popupMenus = (
            []
        )  # Menus contextuels, empêche les fuites mémoire wx
        log.debug(
            f"Viewer.__ini__ : avant création de la présentation DEBUG domainObjectsToView: {len(self.domainObjectsToView())}"
        )
        # # Que présentons-nous:
        # self.__presentation = self.createSorter(
        #     self.createFilter(self.domainObjectsToView())
        # )
        #     Viewer est un Observer.
        #     Il stocke une référence à self.__presentation.
        #     Cette __presentation est passée via les kwargs à l'initialisation.
        #
        #     Si self.__presentation est None lors de l'appel à thaw()
        #     ou s'il est un objet NoneType pour une raison quelconque,
        #     ou s'il n'a pas été correctement initialisé avec un observable valide,
        #     l'erreur se produira.
        #
        # La cause de l'erreur confirmée
        # L'erreur AttributeError: 'NoneType' object has no attribute 'parent'
        # se produit parce que :
        #     taskcoachlib/gui/viewer/base.py (votre Viewer ou une sous-classe)
        #     appelle self.__presentation.thaw().
        #
        #     self.__presentation est une instance de Sorter
        #     (ou une classe qui hérite de Sorter, ici createSorter() ou un descendant de domainObjectsToView()).
        #
        #     Sorter.thaw() appelle super().thaw(),
        #     qui remonte à patterns.observer.CollectionDecorator.thaw().
        #
        #     Dans CollectionDecorator.thaw(), il y a la ligne self.observable().thaw().
        #     À ce moment-là, self.observable() retourne None
        #     pour l'instance __presentation.
        #     L'erreur AttributeError: 'NoneType' object has no attribute 'parent'
        #     est étrange, elle suggère que la méthode thaw()
        #     (ou une méthode appelée par elle) d'une classe parente
        #     essaie d'accéder à parent sur ce None juste
        #     avant que le NoneType ne cause l'erreur sur thaw().
        #     Mais la cause sous-jacente est bien self.observable() étant None.
        # Création de la collection filtrée
        # journalisation avant création de la présentation
        domain_objects = (
            self.domainObjectsToView()
        )  # récupère les objets du modèle
        log.debug(
            f"Viewer.__init__ : objets domaine initiaux = {len(domain_objects)}"
        )  # écrit le nombre d'objets du modèle

        # ------------------------------
        # Création de la chaîne modèle
        # ------------------------------

        # création du filtre appliqué aux objets
        filtered_collection = self.createFilter(
            # self.domainObjectsToView()
            domain_objects
        )  # construit la collection filtrée
        log.debug(
            f"Viewer.__init__ : après filtre : {len(filtered_collection)}"
        )  # journalise le nombre d'objets filtrés
        # sorted_ = self.createSorter(filtered)
        # création du tri appliqué à la collection filtrée
        self.__presentation = self.createSorter(
            filtered_collection
        )  # crée la collection triée utilisée par le viewer
        # log.debug(f"Viewer.__init__ : DEBUG after sorter: {len(sorted_)}")
        log.debug(
            f"Viewer.__init__ : présentation créée avec {len(self.__presentation)} objets."
        )  # journalise la taille de la présentation

        # ------------------------------
        # Création du widget graphique
        # ------------------------------

        # création du contrôle wx affichant les données
        # Le widget utilisé pour présenter la présentation:
        self.widget = self.createWidget()  # construit le widget graphique
        # log.error(f"VIEWER : Ici, s'arrête après cela ? : {self.widget} présente la présentation.")
        # définit la couleur de fond
        self.widget.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        )  # applique la couleur système
        # création de la barre d'outils du viewer
        self.toolbar = toolbar.ToolBar(
            self, settings, (16, 16)
        )  # initialise la toolbar
        # création de la mise en page
        self.initLayout()  # construit le layout du viewer
        # enregistrement des observateurs de la présentation
        self.registerPresentationObservers()  # écoute les changements du modèle
        # self.widget.Refresh()  # Manquait pour afficher les catégories
        # rafraîchissement initial de l'affichage
        self.refresh()  # met à jour l'interface

        pub.subscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.subscribe(self.onEndIO, "taskfile.justRead")
        pub.subscribe(self.onEndIO, "taskfile.justCleared")
        pub.subscribe(self.onEndIO, "taskfile.justSaved")
        # Subscribe to bulk operation signals to freeze/thaw during batch updates
        pub.subscribe(self.onBeginBulkOperation, "command.aboutToBulkModify")
        pub.subscribe(self.onEndBulkOperation, "command.justBulkModified")

        if isinstance(
            self.widget, ToolTipMixin
        ):  # si widget est une instance de ToolTipMixin
            # Informer l'utilisateur
            pub.subscribe(
                self.onShowTooltipsChanged, "settings.view.descriptionpopups"
            )
            # Régler les infos du widget
            self.widget.SetToolTipsEnabled(
                settings.getboolean("view", "descriptionpopups")
            )

        log.debug("Viewer.__init__ : Appel de CallAfter.")
        wx.CallAfter(self.__DisplayBalloon)
        log.debug("Viewer.__init__ : CallAfter passé avec succès.")
        # journalisation de fin d'initialisation
        log.debug(
            f"Viewer.__init__ : Nouvelle visionneuse self={self.__class__.__name__} initialisée !"
        )  # indique que l'initialisation est terminée

    def __DisplayBalloon(self):
        """Affiche une info-bulle pour informer l'utilisateur que la barre d'outils est personnalisable."""
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction (e.g., closing nested dialogs)
        try:
            if not self or self.IsBeingDeleted():
                return
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            return
        # AuiFloatingFrame is instantiated from framemanager, we can't derive it from BalloonTipManager
        if self.toolbar.IsShownOnScreen() and hasattr(
            wx.GetTopLevelParent(self), "AddBalloonTip"
        ):
            log.debug(
                f"Viewer.__DisplayBalloon : Affichage de l'info-bulle pour {self.__class__.__name__}."
            )
            try:
                wx.GetTopLevelParent(
                    self
                ).AddBalloonTip(  # Unresolved attribute reference 'AddBalloonTip' for class 'Window'
                    self.settings,
                    "customizabletoolbars",
                    self.toolbar,
                    # "customizabletoolbars",
                    title=_("Toolbars are customizable"),
                    getRect=lambda: self.toolbar.GetToolRect(
                        self.toolbar.getToolIdByCommand(
                            "EditToolBarPerspective"
                        )
                    ),
                    message=_(
                        """Click on the gear icon on the right to add buttons and rearrange them."""
                    ),
                )
            except Exception as e:
                log.error(
                    f"Viewer.__DisplayBalloon : Failed to display balloon tip: {e}"
                )

    def onShowTooltipsChanged(self, value):
        self.widget.SetToolTipsEnabled(value)

    def onBeginIO(self, taskFile):
        """Débute les opérations de lecture/écriture dans le fichier de tâches."""
        log.debug(
            f"Viewer.onBeginIO : Appel de __presentation.freeze pour {self.__class__.__name__}, self.__freezeCount={self.__freezeCount}."
        )
        self.__freezeCount += 1
        self.__presentation.freeze()
        log.debug(
            f"Viewer.onBeginIO : Freeze terminé ! self.__freezeCount={self.__freezeCount}"
        )

    def onEndIO(
        self, taskFile
    ):  # Cette méthode est appelée lors de l'événement pubsub "taskfile.justRead"
        """Termine les opérations de lecture/écriture dans le fichier de tâches."""
        self.__freezeCount -= 1
        log.debug(
            f"Viewer.onEndIO : Appel de thaw pour {self.__class__.__name__}, self.__freezeCount={self.__freezeCount}."
        )
        # # Voici l'appel initial de la traceback de thaw():
        # self.__presentation.thaw()  # TypeError: UltimateListCtrl.Append() got an unexpected keyword argument 'data'
        try:
            self.__presentation.thaw()
        except (AttributeError, RuntimeError) as e:
            log.warning(
                f"Viewer.onEndIO : ERREUR, thaw() ignoré pour {self.__class__.__name__} : {e}"
            )
        if self.__freezeCount == 0:
            # 🔥 Recréer la presentation après chargement
            log.warning(
                f"Viewer.onEndIO : Recréation de la présentation pour {self.__class__.__name__} après thaw."
            )
            # Supprimer la recréation — elle cause des bugs:
            self.__presentation = self.createSorter(
                self.createFilter(self.domainObjectsToView())
            )  # Recréation de self.__presentation ! DANGER ! Nous devons recréer la présentation après le chargement pour refléter les nouvelles données du fichier de tâches. Cependant, cela peut entraîner des problèmes si d'autres parties du code conservent des références à l'ancienne présentation. Nous devons nous assurer que toutes les références à l'ancienne présentation sont mises à jour ou que nous utilisons une approche qui ne nécessite pas de recréer la présentation.
            # Non, pas besoin, self.__presentation.thaw() s'en occupe déjà.
            log.error(f"observable: {self.__presentation.observable()}")
            log.debug(
                f"Viewer.onEndIO : Appel de refresh pour {self.__class__.__name__} après thaw, self.__freezeCount={self.__freezeCount}."
            )
            self.refresh()
            # wx.CallLater(100, self.refresh)  # 100ms pour laisser le layout se faire
        log.debug(f"Viewer.onEndIO : thaw terminé !")

    def onBeginBulkOperation(self):
        """Freeze viewer and presentation to batch updates during bulk operations."""
        self.__freezeCount += 1
        log.debug(
            f"Viewer.onBeginBulkOperation : Appel de freeze pour {self.__class__.__name__}, self.__freezeCount={self.__freezeCount}."
        )
        self.__presentation.freeze()

    def onEndBulkOperation(self):
        """Thaw viewer and presentation after bulk operation, refresh only changed items."""
        self.__freezeCount -= 1
        log.debug(
            f"Viewer.onEndBulkOperation : Appel de thaw pour {self.__class__.__name__}, self.__freezeCount={self.__freezeCount}."
        )
        self.__presentation.thaw()
        if self.__freezeCount == 0 and self.__pendingRefreshItems:
            # Refresh only items that changed during the bulk operation
            items = [
                item
                for item in self.__pendingRefreshItems
                if item in self.presentation()
            ]
            self.__pendingRefreshItems.clear()
            if items:
                self.widget.RefreshItems(*items)

    def activate(self):
        pass

    def _bindActivationEvents(self, window):
        """Bind click events to activate this viewer's pane.

        This ensures clicking anywhere on the viewer (toolbar, title bar area,
        empty space) will activate the pane. We skip text controls to avoid
        interfering with text input focus.
        """
        # Skip text input controls - they handle their own focus
        if isinstance(window, (wx.TextCtrl, wx.SearchCtrl, wx.ComboBox)):
            return
        window.Bind(wx.EVT_LEFT_DOWN, self._onViewerClick)
        # Recursively bind to children, but skip the main widget (tree/list)
        for child in window.GetChildren():
            if child != self.widget:
                self._bindActivationEvents(child)

    def _onViewerClick(self, event):
        """Handle clicks on the viewer to activate its pane."""
        wx.PostEvent(self, wx.ChildFocusEvent(self))
        self.SetFocus()  # Clear focus from other controls (e.g., search box)
        event.Skip()

    def domainObjectsToView(self):
        """Retourne les objets du domaine que cette visionneuse doit afficher.
        Doit être implémentée dans les sous-classes.

        Renvoie les objets de domaine que cette visionneuse doit afficher.
        Pour les visualiseurs globaux, cela fera partie du fichier de tâches,
        par ex. self.taskFile.tasks(), pour les visualiseurs locaux, ce sera une liste
        d'objets transmis au constructeur du visualiseur."""
        raise NotImplementedError

    def registerPresentationObservers(self):
        """Enregistre les observateurs pour suivre les changements dans la présentation."""
        log.debug(
            f"Viewer.registerPresentationObservers : Enregistrement des observateurs pour {self.__class__.__name__}."
        )
        self.removeObserver(self.onPresentationChanged)
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().addItemEventType(),
            eventSource=self.presentation(),
        )
        log.debug(
            "Viewer.registerPresentationObservers : Observateur onPresentationChanged enregistré pour addItemEventType."
        )
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().removeItemEventType(),
            eventSource=self.presentation(),
        )
        self.registerObserver(self.onNewItem, eventType="newitem")

    def detach(self):
        """Should be called by viewer.container before closing the viewer"""
        log.debug(
            f"Viewer.detach : Détachement de la visionneuse {self.__class__.__name__} en cours."
        )
        observers = [self, self.presentation()]
        observable = self.presentation()
        while True:
            try:
                observable = observable.observable()
            except AttributeError:
                break
            else:
                observers.append(observable)
        for observer in observers:
            try:
                observer.removeInstance()
            except AttributeError:
                pass  # Ignore observables that are not an observer themselves

        for popupMenu in self._popupMenus:
            # try:
            #     popupMenu.clearMenu()
            #     popupMenu.Destroy()
            # except wx.PyDeadObjectError:
            #     pass
            #     # https://stackoverflow.com/questions/34202195/import-pydeadobjecterror-with-wx-version-3-0-3
            #     # https://wxpython.org/Phoenix/docs/html/MigrationGuide.html#wx-pydeadobjecterror-runtimeerror
            #     # try with:
            #     # if someWindow:
            #     #     someWindow.doSomething()
            # except RuntimeError:
            #     pass
            # TODO: Essayer plutôt ça :
            if popupMenu:
                popupMenu.clearMenu()
                popupMenu.Destroy()

        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.unsubscribe(self.onEndIO, "taskfile.justRead")
        pub.unsubscribe(self.onEndIO, "taskfile.justCleared")
        pub.unsubscribe(self.onEndIO, "taskfile.justSaved")
        pub.unsubscribe(self.onBeginBulkOperation, "command.aboutToBulkModify")
        pub.unsubscribe(self.onEndBulkOperation, "command.justBulkModified")

        log.debug(
            f"Viewer.detach : Détachement de la visionneuse {self.__class__.__name__}."
        )
        self.presentation().detach()
        self.toolbar.detach()

    def viewerStatusEventType(self):
        # def viewerStatusEventType(self) -> str:
        """Retourne le type d'événement à utiliser pour les mises à jour de statut.

        Returns :
            str : Le type d'événement de mise à jour de statut.
        """
        # return "viewer%s.status" % id(self)
        return f"viewer{id(self)}.status"

    def sendViewerStatusEvent(self):
        """Envoie un événement pour indiquer que l'état de la visionneuse a changé."""
        pub.sendMessage(self.viewerStatusEventType(), viewer=self)

    def statusMessages(self):
        return "", ""

    def title(self):
        # def title(self) -> str:
        """Retourne le titre actuel de la visionneuse.

        Returns :
            (str) : Le titre actuel de la visionneuse.
        """
        return (
            self.settings.get(self.settingsSection(), "title")
            or self.defaultTitle
        )

    def setTitle(self, title):
        """Modifie le titre de la visionneuse.

        Args :
            title (str) : Le nouveau titre à définir.
        """
        titleToSaveInSettings = "" if title == self.defaultTitle else title
        self.settings.set(
            self.settingsSection(), "title", titleToSaveInSettings
        )
        self.parent.setPaneTitle(
            self, title
        )  # setPaneTitle is for frame ! not window. SetLabel or SetName for window !
        self.parent.manager.Update()  # L'affichage

    def initLayout(self):
        """
        Initialise la mise en page de la visionneuse.

        !!!TRES IMPORTANTE !!!
        """

        log.debug(
            f"Viewer.initLayout : Initialisation de la mise en page de la visionneuse {self.__class__.__name__} title:{self.title()}."
        )
        self._sizer = wx.BoxSizer(wx.VERTICAL)  # pylint: disable=W0201
        # log.debug(f"Viewer.initLayout : _sizer de {self} créé: {self._sizer}")
        self._sizer.Add(self.toolbar, flag=wx.EXPAND)
        # log.debug(f"Viewer.initLayout : toolbar ajoutée, toolbar: {self.toolbar}, taille: {self.toolbar.GetSize()}")
        self._sizer.Add(self.widget, proportion=1, flag=wx.EXPAND)
        # log.debug(f"Viewer.initLayout : widget ajoutée, widget: {self.widget}, taille: {self.widget.GetSize()}")
        # self.SetSizerAndFit(self._sizer)
        self.SetSizer(
            self._sizer
        )  # Changed from SetSizerAndFit to prevent locking MinSize
        # Prevent GetEffectiveMinSize() from returning child's BestSize
        self.SetMinSize((100, 50))
        # Bind click events to activate pane when clicking on toolbar/empty space
        self._bindActivationEvents(self)
        log.debug(
            f"Viewer.initLayout : initLayout de {self.__class__.__name__} terminé, taille: {self.GetSize()}"
        )

    def createWidget(self, *args):
        """Crée le widget utilisé pour afficher les objets. À implémenter dans les sous-classes.

        Returns :
            Widget : Le widget à utiliser pour l'affichage des objets.

        Raises :
            NotImplementedError : Si non implémenté dans une sous-classe.
        """
        raise NotImplementedError

    def createImageList(self):
        size = (16, 16)
        imageList = wx.ImageList(*size)  # pylint: disable=W0142
        self.imageIndex = {}  # pylint: disable=W0201
        for index, image in enumerate(self.viewerImages):
            try:
                # # imageList.Add(wx.ArtProvider_GetBitmap(image, wx.ART_MENU, size))
                # # print(image)
                # imageList.Add(
                #     wx.ArtProvider.GetBitmap(image, wx.ART_MENU, size)
                # )
                bitmap = wx.ArtProvider.GetBitmap(image, wx.ART_MENU, size)
                if not bitmap.IsOk():
                    from taskcoachlib.meta.debug import log_step

                    log_step(
                        f"ERROR: Failed to load bitmap for '{image}' size={size}",
                        prefix="ICON",
                    )
                    bitmap = wx.Bitmap(*size)
                imageList.Add(bitmap)
                # print(imageList)
            except Exception:
                print(image)
                raise
            self.imageIndex[image] = index
        return imageList

    def getWidget(self):
        return self.widget

    def SetFocus(self, *args, **kwargs):
        # try:
        #     self.widget.SetFocus(*args, **kwargs)
        # except wx.PyDeadObjectError:
        #     # https://stackoverflow.com/questions/34202195/import-pydeadobjecterror-with-wx-version-3-0-3
        #     # https://wxpython.org/Phoenix/docs/html/MigrationGuide.html#wx-pydeadobjecterror-runtimeerror
        #     # try with:
        #     # if someWindow:
        #     #     someWindow.doSomething()
        #     # except RuntimeError:
        #     pass
        if self.widget:
            self.widget.SetFocus(*args, **kwargs)
        # else:
        #     pass

    # @staticmethod
    def createSorter(self, collection):
        """Crée un trieur pour organiser la présentation.

        Cette méthode peut être remplacée pour décorer la présentation avec un trieur.
        """
        return collection

    def createFilter(self, collection):
        """Crée un filtre pour organiser la présentation.

        Cette méthode peut être remplacée pour décorer la présentation avec un filtre.
        """
        return collection

    def onAttributeChanged(self, newValue, sender):  # pylint: disable=W0613
        # print(
        log.debug(
            "Viewer.onAttributeChanged : Appel de onAttributeChanged pour %s avec newValue=%s et sender=%s."
            % (self.__class__.__name__, newValue, sender)
        )
        # print(
        log.debug(
            "Viewer.onAttributeChanged",
            sender,
            sender.id(),
            newValue,
        )
        if self:
            # self.refreshItems(sender)
            if self.__freezeCount:
                # During bulk operation, collect items to refresh later
                self.__pendingRefreshItems.add(sender)
            else:
                self.refreshItems(sender)

    def onAttributeChanged_Deprecated(self, event):
        log.debug(
            "Viewer.onAttributeChanged : Appel de onAttributeChanged pour %s avec event=%s.",
            self.__class__.__name__,
            event,
        )
        # self.refreshItems(*event.sources())
        if self.__freezeCount:
            # During bulk operation, collect items to refresh later
            self.__pendingRefreshItems.update(event.sources())
        else:
            self.refreshItems(*event.sources())

    def onNewItem(self, event):
        """Sélectionne un nouvel élément ajouté à la présentation.

        Args :
            event (Event) : L'événement indiquant l'ajout d'un nouvel élément.
        """
        log.debug(
            f"Viewer.onNewItem : Appel de onNewItem pour {self.__class__.__name__} avec event={event}."
        )
        self.select(
            [
                item
                for item in list(event.values())
                if item in self.presentation()
            ]
        )

    def onPresentationChanged(self, event):  # pylint: disable=W0613
        """Gère les changements dans la présentation et rafraîchit la visionneuse.

        Chaque fois que notre présentation est modifiée (éléments ajoutés,
        éléments supprimés), la visionneuse se rafraîchit.
        """
        log.debug(
            f"Viewer.onPresentationChanged : Appel de onPresentationChanged pour {self.__class__.__name__} avec event={event}."  # Le sorter reçoit bien un .add.
        )

        def itemsRemoved():
            """Vérifie si des éléments ont été supprimés de la présentation."""
            log.debug(
                f"Viewer.onPresentationChanged : Vérification si des éléments ont été supprimés pour {self.__class__.__name__} avec event={event}."
            )
            return event.type() == self.presentation().removeItemEventType()

        def allItemsAreSelected():
            """Vérifie si tous les éléments sélectionnés sont encore dans la présentation."""
            return set(self.__curselection).issubset(set(event.values()))

        self.refresh()
        if itemsRemoved() and allItemsAreSelected():
            self.selectNextItemsAfterRemoval(list(event.values()))
        self.updateSelection(sendViewerStatusEvent=False)
        self.sendViewerStatusEvent()
        # self.refresh()  # TODO : A vérifier si nécessaire !

    def selectNextItemsAfterRemoval(self, removedItems):
        """Select the next item after items were removed.

        Args:
            removedItems: Selection state captured before refresh (parent + index)
        """
        raise NotImplementedError

    def onSelect(self, event=None):  # pylint: disable=W0613
        """The selection of items in the widget has been changed. Notify
        our observers."""

        # try:
        if self.IsBeingDeleted() or self.__selectingAllItems:
            # Some widgets change the selection and send selection events when
            # deleting all items as part of the Destroy process. Ignore.
            return
        # Be sure all wx events are handled before we update our selection
        # cache and Notify our observers:
        # wx.CallAfter(self.updateSelection)
        wx.CallAfter(self.sendViewerStatusEvent)
        # except RuntimeError:
        #     # RuntimeError: wrapped C/C++ object of type EffortViewer has been deleted
        #     # FIXME: It's a bug?
        #     # wx.PyDeadObjectError create now RuntimeError !
        #     pass

    def updateSelection(self, sendViewerStatusEvent=True):
        """Met à jour la sélection actuelle."""
        log.debug(
            f"Viewer.updateSelection : Mise à jour de la sélection pour {self.__class__.__name__}."
        )
        newSelection = self.widget.curselection()
        if newSelection != self.__curselection:
            self.__curselection = newSelection
            if sendViewerStatusEvent:
                self.sendViewerStatusEvent()

    def freeze(self):
        """
        Gèle la fenêtre ou, en d'autres termes, empêche les mises à jour
        qui se déroulent à l'écran, la fenêtre n'est pas du tout redessinée.

        Returns :
            None
        """
        self.widget.Freeze()

    def thaw(self):
        """
        Réévaluer la mise à jour de la fenêtre après un appel précédent de freeze().

        Returns :
        """
        # self.widget.Thaw()
        # Ne PAS appeler super().thaw() ici — évite la boucle dans CollectionDecorator
        try:
            self.widget.Thaw()
        except RuntimeError:
            pass  # widget détruit

    # def refresh(self):
    def refresh(self, *args, **kwargs):
        """Rafraîchir les éléments affichés dans la visionneuse.
        On n'affiche que les racines. La hiérarchie est gérée par le widget
        via les appels récursifs à children()."""
        log.debug(
            f"Viewer.refresh : Appel de refresh pour {self.__class__.__name__} !"
        )
        log.error(
            f"Viewer.refresh - tasks in model: {len(self.taskFile.tasks())}"
        )
        log.error(f"PRESENTATION TASKS: {len(self.presentation())}")
        log.debug(f"Viewer.refresh - self.taskFile id : {id(self.taskFile)}")
        # !!! Important : self.presentation() est une collection décorée (ex: Sorter) qui observe la collection de base (ex: self.taskFile.tasks()).
        # Si self.presentation() n'observe pas correctement la collection de base, ou si la collection de base n'est pas correctement initialisée, alors self.presentation() peut être vide ou ne pas refléter les éléments attendus, ce qui entraînera un rafraîchissement avec 0 éléments.
        # Par conséquent, il est crucial de vérifier que self.presentation() est correctement initialisée et observe la collection de base avant d'appeler refresh(), sinon nous risquons de rafraîchir la visionneuse avec une présentation vide.
        # Si les IDs sont différents → 💥 on a gagné. Le bug est confirmé : self.presentation() n'observe pas correctement la collection de base, ou la collection de base n'est pas correctement initialisée, ce qui entraîne un rafraîchissement avec 0 éléments.
        log.debug(
            f"Viewer.refresh : DEBUG id taskFile.tasks(): {id(self.taskFile.tasks())}"
        )
        log.debug(
            f"Viewer.refresh : DEBUG id __presentation.observable(): {id(self.__presentation.observable())}"
        )
        # Si les IDs diffèrent, ce n'est pas forcément un bug, cela peut être dû à la création d'une nouvelle présentation (ex: self.__presentation = self.createSorter(self.createFilter(self.domainObjectsToView())) dans onEndIO) qui observe une nouvelle collection de base. Cependant, si la nouvelle présentation n'observe pas correctement la collection de base, ou si la collection de base n'est pas correctement initialisée, alors nous risquons toujours d'avoir une présentation vide. Il est donc important de vérifier que la nouvelle présentation est correctement initialisée et observe la collection de base avant d'appeler refresh() après un chargement.
        # Cela peut être normal : presentation.observable() est le Filter
        # pas la TaskList directement.
        log.debug(
            f"Viewer.refresh DEBUG id presentation.observable(): {id(self.presentation().observable())}"
        )
        if self and not self.__freezeCount:
            # On vérifie si laméthode existe pour éviter le plantage sur ListViewer
            if self.isTreeViewer() and self.getRootItems():
                count = len(self.getRootItems())
            else:
                count = len(self.presentation())
            # log.debug(
            #     f"Viewer.refresh : Rafraîchissement de la visionneuse {self.__class__.__name__} avec {len(self.presentation())} éléments."
            # )
            log.debug(
                f"Viewer.refresh : Rafraîchissement de la visionneuse {self.__class__.__name__} avec {count} éléments."
            )
            # # self.widget.RefreshAllItems(
            # #     len(self.presentation())
            # # )  # c’est le widget qui doit gérer le coalescing.
            # # self.widget.scheduleRefresh(len(self.presentation()))
            # self.widget.scheduleRefresh(count)  # Fait planter !
            # # self.widget.RefreshAllItems(count)
            # # Unresolved attribute reference 'RefreshAllItems' for class 'Window'
            # Utiliser scheduleRefresh seulement si le widget le supporte (ex: TreeListCtrl)
            # Sinon utiliser RefreshAllItems (ex: VirtualListCtrl pour EffortViewer)
            if hasattr(self.widget, "scheduleRefresh"):
                log.debug(
                    f"Viewer.refresh : Appel de scheduleRefresh pour {self.__class__.__name__} avec count={count}."
                )
                self.widget.scheduleRefresh(count)
            else:
                log.debug(
                    f"Viewer.refresh : Appel de RefreshAllItems pour {self.__class__.__name__} avec count={count}."
                )
                self.widget.RefreshAllItems(count)

        log.debug(f"Viewer.refresh : Refresh du widget {self.widget}.")
        self.widget.Refresh()
        self.widget.Update()
        log.debug(
            f"Viewer.refresh : Fin de refresh pour {self.__class__.__name__} !"
        )

    # def scheduleRefresh(self):
    #     if getattr(self, "_refreshScheduled", False):
    #         return
    #     self._refreshScheduled = True
    #
    #     def doRefresh():
    #         self._refreshScheduled = False
    #         print("REAL REFRESH EXECUTED")
    #         self.refresh()
    #
    #     self.after(1, doRefresh)

    def refreshItems(self, *items):
        """
        Rafraîchit les éléments spécifiés dans la visionneuse.

        Args:
            *items: Liste d'éléments à rafraîchir dans la visionneuse.

        Returns:

        """
        log.debug(
            f"Viewer.refreshItems : Appel de refreshItems pour {self.__class__.__name__} avec items={items}."
        )
        if not self.__freezeCount:
            items = [item for item in items if item in self.presentation()]
            log.debug(
                f"Viewer.refreshItems : Items à rafraîchir après filtrage : {items}."
            )
            self.widget.RefreshItems(*items)  # pylint: disable=W0142
            # Unresolved attribute reference 'RefreshItems' for class 'Window'

    def select(self, items):
        """Sélectionne des éléments dans la présentation.

        Args :
            items (list) : Liste des objets à sélectionner.
        """
        self.__curselection = items
        self.widget.select(items)

    # def curselection(self):
    def curselection(self, forceUpdate=False):
        """Retourne la sélection actuelle dans la visionneuse.

        Renvoie une liste d'éléments (objets de domaine) actuellement sélectionnés dans notre widget .
        If forceUpdate is True, refresh the cached selection from the widget
        before returning. This is useful when selection may have changed but
        the cached value hasn't been updated yet (e.g., during double-click
        handling where wx.CallAfter hasn't executed yet).
        """
        if forceUpdate:
            self.updateSelection(sendViewerStatusEvent=False)
        return self.__curselection
        return self.widget.curselection()

    def curselectionIsInstanceOf(self, class_):
        """Return whether all items in the current selection are instances of
        class_. Can be overridden in subclasses that show only one type
        of items to simply check the class."""
        return all(isinstance(item, class_) for item in self.curselection())

    def isselected(self, item):
        """Returns True if the given item is selected. See
        L{EffortViewer} for an explanation of why this may be
        different than 'if item in viewer.curselection()'."""
        return item in self.curselection()

    def select_all(self):
        """Select all items in the presentation. Since some of the widgets we
        use may send events for each individual item (!) we stop processing
        selection events while we select all items."""
        self.__selectingAllItems = True
        self.widget.select_all()
        # Use CallAfter to make sure we start processing selection events
        # after all selection events have been fired (and ignored):
        wx.CallAfter(self.endOfSelectAll)

    def endOfSelectAll(self):
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction (e.g., closing nested dialogs)
        try:
            if not self or self.IsBeingDeleted():
                return
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            return
        log.debug(
            f"Viewer.endOfSelectAll : Fin de select_all pour {self.__class__.__name__}."
        )
        self.__curselection = self.presentation()
        self.__selectingAllItems = False
        # Pretend we received one selection event for the select_all() call:
        self.onSelect()

    def clear_selection(self):
        """Clear the current selection."""
        self.__curselection = []
        self.widget.clear_selection()

    def size(self):
        return self.widget.GetItemCount()

    # Dans TaskCoach original :
    # La presentation() est déjà un objet Filter/Sorter intelligent.
    # Il expose :
    # presentation.rootItems()
    # presentation.childrenOf(parent)
    # ET PAS directement parent.children().
    def presentation(self):
        """Renvoie les objets de domaine que cette visionneuse affiche actuellement."""
        # log.warning("Viewer.presentation : méthode appelée régulièrement et risque de polluer le log.")
        # log.debug(
        #     f"Viewer.presentation : DEBUG presentation taskfile: {id(self.taskFile)}"
        # )
        # return self.__presentation
        to_return = self.__presentation
        # log.debug(
        #     f"Viewer.presentation : Retour de la présentation de {self.__class__.__name__} avec {len(to_return)} éléments."
        # )
        # log.debug(
        #     f"Viewer.presentation : Les éléments de la présentation sont : {to_return}."
        # )
        return to_return

    def setPresentation(self, presentation):
        """Change the presentation of the viewer.
        Changer la présentation de la visionneuse."""
        log.debug(
            f"Viewer.setPresentation : Changement de la présentation de {self.__class__.__name__} de {self.__presentation} en {presentation}."
        )
        self.__presentation = presentation

    # @staticmethod
    def widgetCreationKeywordArguments(self):
        return {}

    # @staticmethod
    def isTreeViewer(self):
        # def isTreeViewer(self) -> bool:
        """
        Indique si la vue est une vue arborescente.

        Returns :
            (bool) : False, car cette vue n'est ni une vue en liste et ni en arbre.
        """
        # return False
        raise NotImplementedError

    # @staticmethod
    def isViewerContainer(self):
        """Retourne si c'est un conteneur de viewer."""
        return False

    def isShowingTasks(self):
        """Retourne si ce viewer affiche des tâches."""
        return False

    def isShowingEffort(self):
        """Retourne si ce viewer affiche les efforts."""
        return False

    def isShowingCategories(self):
        """Retourne si ce viewer affiche les catégories."""
        return False

    def isShowingNotes(self):
        """Retourne si ce viewer affiche les notes."""
        return False

    def isShowingAttachments(self):
        """Retourne les objets du domaine que cette visionneuse doit afficher.
        Doit être implémentée dans les sous-classes."""
        return False

    def visibleColumns(self):
        """Retourne la liste des colonnes visibles."""
        return [widgets.Column("subject", _("Subject"))]

    def bitmap(self):
        """Return the bitmap that represents this viewer. Used for the
        'Viewer->New viewer' menu item, for example."""
        return self.defaultBitmap  # Class attribute of concrete viewers

    def settingsSection(self):
        """Retourner la section Paramètres de cette visionneuse."""
        section = self.__settingsSection
        if self.__use_separate_settings_section and self.__instanceNumber > 0:
            # We're not the first viewer of our class, so we need a different
            # settings section than the default one.
            section += str(self.__instanceNumber)
            if not self.settings.has_section(section):
                # Our section does not exist yet. Create it and copy the
                # settings from the previous section as starting point. We're
                # copying from the previous section instead of the default
                # section so that when the user closes a viewer and then opens
                # a new one, the settings of that closed viewer are reused.
                self.settings.add_section(
                    section, copyFromSection=self.previousSettingsSection()
                )
        return section

    def previousSettingsSection(self):
        """Return the settings section of the previous viewer of this
        class."""
        previousSectionNumber = self.__instanceNumber - 1
        while previousSectionNumber > 0:
            previousSection = self.__settingsSection + str(
                previousSectionNumber
            )
            if self.settings.has_section(previousSection):
                return previousSection
            previousSectionNumber -= 1
        return self.__settingsSection

    def hasModes(self):
        """Retourne si le viewer a des modes."""
        return False

    def getModeUICommands(self):
        """Retourne la liste des UICommands de mode."""
        return []

    # @staticmethod
    def isSortable(self):
        """Retourne si le viewer est sortable."""
        return False

    # @staticmethod
    def getSortUICommands(self):
        """Retourne la liste des UICommands de sort."""
        return []

    # @staticmethod
    def isSearchable(self):
        """Retourne si le viewer a une fonction recherche."""
        return False

    def hasHideableColumns(self):
        """Retourne si le viewer a des colonnes cachables."""
        return False

    def getColumnUICommands(self):
        """Retourne la liste des UICommands pour les colonnes."""
        return []

    # @staticmethod
    def isFilterable(self):
        """Retourne si l'affichage du viewer est filtrable."""
        return False

    # @staticmethod
    def getFilterUICommands(self):
        """Retourne la liste des UICommands de filtrage."""
        return []

    def supportsRounding(self):
        """Retourne si le viewer supporte les arrondis."""
        return False

    def getRoundingUICommands(self):
        """Retourne la liste des UICommands d'arrondi."""
        return []

    def createToolBarUICommands(self):
        """UI commands to put on the toolbar of this viewer."""
        table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CMD, ord("X"), wx.ID_CUT),
                (wx.ACCEL_CMD, ord("C"), wx.ID_COPY),
                (wx.ACCEL_CMD, ord("V"), wx.ID_PASTE),
                (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT),
                (wx.ACCEL_CTRL, wx.WXK_DELETE, wx.ID_DELETE),
            ]
        )
        self.SetAcceleratorTable(table)

        clipboardToolBarUICommands = self.createClipboardToolBarUICommands()
        creationToolBarUICommands = self.createCreationToolBarUICommands()
        editToolBarUICommands = self.createEditToolBarUICommands()
        actionToolBarUICommands = self.createActionToolBarUICommands()
        modeToolBarUICommands = self.createModeToolBarUICommands()

        def separator(uiCommands, *otherUICommands):
            """Retourne un ensemble d'uiCommands."""
            return (None,) if (uiCommands and any(otherUICommands)) else ()

        clipboardSeparator = separator(
            clipboardToolBarUICommands,
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        creationSeparator = separator(
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        editSeparator = separator(
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        actionSeparator = separator(
            actionToolBarUICommands, modeToolBarUICommands
        )

        return (
            clipboardToolBarUICommands
            + clipboardSeparator
            + creationToolBarUICommands
            + creationSeparator
            + editToolBarUICommands
            + editSeparator
            + actionToolBarUICommands
            + actionSeparator
            + modeToolBarUICommands
        )

    def getToolBarPerspective(self):
        """Retourne la perspective de la barre d'outils."""
        return self.settings.get(self.settingsSection(), "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        """Règle la perspective de la barre d'outils."""
        self.settings.set(
            self.settingsSection(), "toolbarperspective", perspective
        )

    def createClipboardToolBarUICommands(self):
        """UI commands for manipulating the clipboard (cut, copy, paste)."""
        cutCommand = uicommand.EditCut(viewer=self)
        copyCommand = uicommand.EditCopy(viewer=self)
        pasteCommand = uicommand.EditPaste(viewer=self)
        # cutCommand.Bind(self, wx.ID_CUT)
        cutCommand.bind(self, wx.ID_CUT)
        # copyCommand.Bind(self, wx.ID_COPY)
        copyCommand.bind(self, wx.ID_COPY)
        # pasteCommand.Bind(self, wx.ID_PASTE)
        pasteCommand.bind(self, wx.ID_PASTE)
        return cutCommand, copyCommand, pasteCommand

    def createCreationToolBarUICommands(self):
        """UI commands for creating new items."""
        return ()

    def createEditToolBarUICommands(self):
        """UI commands for editing items."""
        editCommand = uicommand.Edit(viewer=self)
        self.deleteUICommand = uicommand.Delete(
            viewer=self
        )  # For unittests pylint: disable=W0201
        # Instance attribute deleteUICommand defined outside __init__
        editCommand.bind(self, wx.ID_EDIT)
        # editCommand.bind(editCommand, self, wx.ID_EDIT)
        self.deleteUICommand.bind(self, wx.ID_DELETE)
        # self.deleteUICommand.bind(self.deleteUICommand, self, wx.ID_DELETE)
        return editCommand, self.deleteUICommand

    def createActionToolBarUICommands(self):
        """UI commands for actions."""
        return ()

    def createModeToolBarUICommands(self):
        """UI commands for mode switches (e.g. list versus tree mode)."""
        return ()

    def newItemDialog(self, *args, **kwargs):
        bitmap = kwargs.pop("bitmap")
        newItemCommand = self.newItemCommand(*args, **kwargs)
        newItemCommand.do()
        return self.editItemDialog(
            newItemCommand.items, bitmap, items_are_new=True
        )

    def newSubItemDialog(self, bitmap):
        parents = self.curselection()
        newSubItemCommand = self.newSubItemCommand()
        newSubItemCommand.do()
        # Expand parent notes so the newly created subnotes are visible
        for parent in parents:
            parent.expand(True, context=self.settingsSection())
        return self.editItemDialog(
            newSubItemCommand.items, bitmap, items_are_new=True
        )

    def editItemDialog(
        self, items, bitmap, columnName="", items_are_new=False
    ):
        Editor = self.itemEditorClass()
        log.debug(
            f"Viewer.editItemDialog : Création de l'éditeur pour {self.__class__.__name__} avec items={items}, bitmap={bitmap}, columnName='{columnName}', items_are_new={items_are_new}."
        )
        return Editor(
            wx.GetTopLevelParent(self),
            items,
            self.settings,
            self.presentation(),
            self.taskFile,
            bitmap=bitmap,
            columnName=columnName,
            items_are_new=items_are_new,
        )

    def itemEditorClass(self):
        raise NotImplementedError

    def newItemCommand(self, *args, **kwargs):
        """Retourne la commande du nouvel élément."""
        log.debug(
            f"Viewer.newItemCommand : Création de la commande de nouvel élément pour {self.__class__.__name__} avec args={args}, kwargs={kwargs}."
        )
        return self.newItemCommandClass()(self.presentation(), *args, **kwargs)

    def newItemCommandClass(self):
        raise NotImplementedError

    def newSubItemCommand(self):
        log.debug(
            f"Viewer.newSubItemCommand : Création de la commande de nouvel élément pour {self.__class__.__name__} avec curselection={self.curselection()}."
        )
        return self.newSubItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def newSubItemCommandClass(self):
        raise NotImplementedError

    def deleteItemCommand(self):
        log.debug(
            f"Viewer.deleteItemCommand : Création de la commande de suppression pour {self.__class__.__name__} avec curselection={self.curselection()}."
        )
        return self.deleteItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def deleteItemCommandClass(self):
        return command.DeleteCommand

    def cutItemCommand(self):
        log.debug(
            f"Viewer.cutItemCommand : Création de la commande de coupe pour {self.__class__.__name__}) avec curselection={self.curselection()}."
        )
        return self.cutItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def cutItemCommandClass(self):
        return command.CutCommand

    def pasteItemCommand(self):
        log.debug(
            f"Viewer.pasteItemCommand : Création de la commande de collage pour {self.__class__.__name__}."
        )
        return self.pasteItemCommandClass()(self.presentation())

    def pasteItemCommandClass(self):
        return command.PasteCommand

    def getSupportedPasteTypes(self):
        """Return tuple of domain object types that can be pasted into this viewer.

        Override in subclasses to restrict paste to specific types.
        Return None to accept any type (default behavior).
        """
        return None

    # @staticmethod
    def onEditSubject(self, item, newValue):
        command.EditSubjectCommand(items=[item], newValue=newValue).do()

    # @staticmethod
    def onEditDescription(self, item, newValue):
        command.EditDescriptionCommand(items=[item], newValue=newValue).do()

    def getItemTooltipData(self, item):
        lines = [line.rstrip("\r") for line in item.description().split("\n")]
        return [(None, lines)] if lines and lines != [""] else []


class CategorizableViewerMixin(object):
    """Classe Mixin."""

    def getItemTooltipData(self, item):
        return [
            (
                "folder_blue_arrow_icon",
                (
                    [
                        ", ".join(
                            sorted(
                                [cat.subject() for cat in item.categories()]
                            )
                        )
                    ]
                    if item.categories()
                    else []
                ),
            )
        ] + super().getItemTooltipData(
            item
        )  # It's a mixin.


class WithAttachmentsViewerMixin(object):
    def getItemTooltipData(self, item):
        return [
            (
                "paperclip_icon",
                sorted([str(attachment) for attachment in item.attachments()]),
            )
        ] + super().getItemTooltipData(item)


class ListViewer(Viewer):  # pylint: disable=W0223
    """
    Classe ListViewer, héritant de Viewer.

    Cette classe est utilisée pour afficher des objets dans une vue en liste,
    contrairement à une vue arborescente.
    Elle implémente des méthodes spécifiques pour gérer les objets sous forme de liste.

    Explication des méthodes :

    isTreeViewer : Retourne False car cette classe ne représente pas une vue arborescente, mais une vue en liste.
    visibleItems : Cette méthode génère tous les éléments visibles dans la présentation en les itérant.
    getItemWithIndex : Récupère un élément particulier dans la liste en fonction de son index.
    getIndexOfItem : Donne l'index d'un élément particulier dans la présentation.
    selectNextItemsAfterRemoval : Cette méthode est utilisée pour sélectionner les éléments après la suppression.
     Dans ce cas, elle ne fait rien, car les contrôles de liste gèrent cette sélection automatiquement.
    """

    # @staticmethod
    def isTreeViewer(self):
        # def isTreeViewer(self) -> bool:
        """
        Indique si la vue est une vue arborescente.

        Returns :
            (bool) : False, car cette vue est une vue en liste et non en arbre.
        """
        return False

    def visibleItems(self):
        """
        Itère sur les éléments visibles dans la présentation.

        Yields :
            Chaque objet visible dans la présentation.
        """
        for item in self.presentation():
            yield item

    def getItemWithIndex(self, index):
        # def getItemWithIndex(self, index) -> object:
        """
        Récupère un élément spécifique dans la présentation en fonction de son index.

        Args :
            index (int) : L'index de l'élément à récupérer.

        Returns :
            L'objet à l'index spécifié.
        """
        return self.presentation()[index]

    def getIndexOfItem(self, item):
        # def getIndexOfItem(self, item) -> int:
        """
        Récupère l'index d'un élément spécifique dans la présentation.

        Args :
            item (object) : L'objet dont on souhaite connaître l'index.

        Returns :
            (int) : L'index de l'objet dans la présentation.
        """
        return self.presentation().index(item)

    def selectNextItemsAfterRemoval(self, removedItems):
        """
        Sélectionne les éléments suivants après suppression.

        Cette méthode est spécifique aux contrôles de liste où la sélection
        est gérée automatiquement après la suppression d'éléments.

        Args :
            removedItems (list) : La liste des éléments qui ont été supprimés.
        """
        pass  # Gestion automatique par les contrôles de liste.


class TreeViewer(Viewer):  # pylint: disable=W0223
    """
    Classe TreeViewer, héritant de Viewer.

    Cette classe est utilisée pour afficher des objets dans une vue arborescente, permettant d'expander
    ou de réduire les nœuds de l'arbre. Elle gère les événements de sélection et d'expansion des éléments.

    **Explication des méthodes** :

    onItemExpanded et onItemCollapsed : Gèrent les événements d'expansion ou de réduction des nœuds d'un arbre.

    expandAll et collapseAll : Permettent d'expander ou de réduire tous les éléments de manière récursive.

    select et selectNextItemsAfterRemoval : Sélectionnent des éléments, en expandeant leurs parents si nécessaire,
    et sélectionnent des éléments après suppression.

    visibleItems : Itère sur les éléments visibles dans l'arbre, y compris leurs enfants.

    getRootItems, getItemParent, et children : Gèrent la relation parent-enfant dans l'arbre.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise TreeViewer avec gestion des événements d'expansion et de collapse des éléments.

        Args :
            *args : Arguments supplémentaires pour l'initialisation.
            **kwargs : Arguments nommés pour l'initialisation.
        """
        log.debug(
            f"TreeViewer : Initialisation de {self.__class__.__name__} avec args={args} et kwargs={kwargs}."
        )
        # Initialisation de la sélection et des paramètres spécifiques à TreeViewer
        self.__selectionIndex = 0
        super().__init__(*args, **kwargs)
        # Liaison des événements d'expansion et de collapse
        # log.info(f"TreeViewer : Liaison des événements d'expansion.")
        # self.widget.bind(wx.EVT_TREE_ITEM_EXPANDED, self.onItemExpanded)
        self.widget.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.onItemExpanded)
        # log.info(f"TreeViewer : Liaison des événements de collapse.")
        # self.widget.bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)
        self.widget.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)
        log.debug(f"TreeViewer : {self.__class__.__name__} Initialisé !")

    def onItemExpanded(self, event):
        """Gère l'événement d'expansion d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=True)

    def onItemCollapsed(self, event):
        """Gère l'événement de collapse d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=False)

    def __handleExpandedOrCollapsedItem(self, event, expanded):
        """
        Gère les changements d'état d'expansion ou de collapse d'un élément.

        Args :
            event : (wx.Event) L'événement lié à l'expansion ou au collapse.
            expanded (bool) : Indique si l'élément doit être expansé ou réduit.
        """
        log.debug(
            f"TreeViewer.__handleExpandedOrCollapsedItem : Gestion de l'événement d'{'expansion' if expanded else 'collapse'} pour {self.__class__.__name__}."
        )
        event.Skip()
        treeItem = event.GetItem()
        log.debug(
            f"TreeViewer.__handleExpandedOrCollapsedItem : Item concerné par l'événement : {treeItem}."
        )
        # treeItem = event.GetEventObject()
        # If we get an expanded or collapsed event for the root item, ignore it
        if treeItem == self.widget.GetRootItem():
            log.debug(
                f"TreeViewer.__handleExpandedOrCollapsedItem : Ignoring event for root item."
            )
            return
        # item = self.widget.GetItemPyData(treeItem)  # TODO: try GetItemData
        item = self.widget.GetItemData(treeItem)  # TODO: try GetItemData
        # item = self.widget.GetPyData(treeItem)  # TODO: try
        log.debug(
            f"TreeViewer.__handleExpandedOrCollapsedItem : Item data retrieved: {item}."
        )
        item.expand(expanded, context=self.settingsSection())

    def expandAll(self):
        """Expande tous les éléments de manière récursive."""
        # Since the widget does not send EVT_TREE_ITEM_EXPANDED when expanding
        # all items, we have to do the bookkeeping ourselves:
        for item in self.visibleItems():
            log.debug(f"TreeViewer.expandAll : Expanding item {item}.")
            item.expand(True, context=self.settingsSection(), notify=False)
        self.refresh()

    def collapseAll(self):
        """Réduit tous les éléments de manière récursive."""
        # Since the widget does not send EVT_TREE_ITEM_COLLAPSED when collapsing
        # all items, we have to do the bookkeeping ourselves:
        for item in self.visibleItems():
            item.expand(False, context=self.settingsSection(), notify=False)
        self.refresh()

    def isAnyItemExpandable(self):
        """Vérifie si un élément est expansible."""
        return self.widget.isAnyItemExpandable()

    def isAnyItemCollapsable(self):
        """Vérifie si un élément est collapsable."""
        return self.widget.isAnyItemCollapsable()

    def createModeToolBarUICommands(self):
        return super().createModeToolBarUICommands() + (
            uicommand.ViewExpandAll(viewer=self),
            uicommand.ViewCollapseAll(viewer=self),
        )

    def isTreeViewer(self):
        # def isTreeViewer(self) -> bool:
        """Indique que cette vue est une vue arborescente.

        Returns :
            bool : True, car cette vue est une vue en arbre et non en liste."""
        return True

    def select(self, items):
        # def select(self, items: list):
        """
        Sélectionne les éléments spécifiés et expande leurs parents de manière récursive.

        Args :
            items (list) : La liste des éléments à sélectionner.
        """
        for item in items:
            self.__expandItemRecursively(item)
        self.refresh()
        super().select(items)
        # self.refresh()

    def __expandItemRecursively(self, item):
        # def __expandItemRecursively(self, item: object):
        """
        Expande les parents de l'élément donné de manière récursive.

        Args :
            item : L'élément dont les parents doivent être expansés.
        """
        parent = self.getItemParent(item)
        if parent:
            parent.expand(True, context=self.settingsSection(), notify=False)
            self.__expandItemRecursively(parent)
        # self.refresh()

    def selectNextItemsAfterRemoval(self, removedItems):
        # def selectNextItemsAfterRemoval(self, removedItems: list):
        """
        Sélectionne les éléments suivants après la suppression de certains éléments.

        Args :
            removedItems : Liste des éléments supprimés.
        """
        log.debug(
            f"TreeViewer.selectNextItemsAfterRemoval : Sélection des éléments suivants après suppression pour {self.__class__.__name__} avec removedItems={removedItems}."
        )
        parents = [self.getItemParent(item) for item in removedItems]
        parents = [
            parent for parent in parents if parent in self.presentation()
        ]
        parent = parents[0] if parents else None
        siblings = self.children(parent)
        newSelection = (
            siblings[min(len(siblings) - 1, self.__selectionIndex)]
            if siblings
            else parent
        )
        if newSelection:
            self.select([newSelection])

    def updateSelection(self, *args, **kwargs):
        """
        Met à jour la sélection actuelle et garde une trace de l'index sélectionné.

        Args :
            *args : Arguments supplémentaires pour la mise à jour de la sélection.
            **kwargs : Arguments nommés pour la mise à jour.
        """
        super().updateSelection(*args, **kwargs)
        curselection = self.curselection()
        if curselection:
            siblings = self.children(self.getItemParent(curselection[0]))
            self.__selectionIndex = (
                siblings.index(curselection[0])
                if curselection[0] in siblings
                else 0
            )
        else:
            self.__selectionIndex = 0

    def visibleItems(self):
        """
        Itère sur les éléments visibles dans la présentation, y compris les enfants.

        Yields :
            Chaque élément visible et ses enfants.
        """
        log.debug(
            f"TreeViewer.visibleItems : Itération sur les éléments visibles dans {self.__class__.__name__}."
        )

        def yieldItemsAndChildren(items):
            log.debug(
                "TreeViewer.visibleItems : Yielding items and their children."
            )
            sortedItems = [
                item for item in self.presentation() if item in items
            ]
            for item in sortedItems:
                yield item
                children = self.children(item)
                if children:
                    for child in yieldItemsAndChildren(children):
                        yield child

        for item in yieldItemsAndChildren(self.getRootItems()):
            log.debug(f"TreeViewer.visibleItems : Yielding item {item}.")
            yield item

    def getRootItems(self):
        # def getRootItems(self) -> list:
        """
        Retourne les éléments racines de la présentation.

        Autoriser le remplacement des rootItems.

        Returns :
            (list) : Liste des éléments racines.
        """
        log.debug(
            f"TreeViewer.getRootItems() : Récupération des éléments racines de la présentation pour {self.__class__.__name__}."
        )
        rootItems_to_return = self.presentation().rootItems()
        # return self.presentation().rootItems()
        log.debug(
            f"TreeViewer.getRootItems() : retourne la racine  {rootItems_to_return} de la présentation {self.presentation()}."
        )
        return rootItems_to_return

    def getItemParent(self, item):
        # def getItemParent(self, item) -> object:
        """
        Retourne le parent de l'élément donné.

        Autoriser le remplacement du parent d'un élément.

        Args :
            item : L'élément dont le parent est à retourner.

        Returns :
            Le parent de l'élément.
        """
        return item.parent()

    def getItemExpanded(self, item):
        # def getItemExpanded(self, item) -> bool:
        """
        Vérifie si un élément est expansé dans la vue actuelle.

        Args :
            item : L'élément à vérifier.

        Returns :
            True si l'élément est expansé, False sinon.
        """
        return item.isExpanded(context=self.settingsSection())

    def children(self, parent=None):
        # def children(self, parent=None) -> list:
        """
        Retourne les enfants d'un élément donné.

        Args :
            parent : (optionnel) L'élément parent. Si aucun parent n'est fourni, retourne les éléments racines.

        Returns :
            (list) : Liste des enfants de l'élément parent, ou des éléments racines si aucun parent n'est spécifié.
        """
        log.debug(
            f"TreeViewer.children : Récupération des enfants pour le parent {parent} dans {self.__class__.__name__}."
        )
        log.debug(
            "TreeViewer.children : PRESENTATION IDS: %s",
            [id(x) for x in self.presentation()],
        )
        log.debug(
            "TreeViewer.children : PARENT CHILD IDS: %s",
            [id(x) for x in parent.children()] if parent else "N/A",
        )
        # # if parent:
        # #     # En Python, ça ne veut PAS dire : si parent n’est pas None
        # #     # Ça veut dire : si bool(parent) est True
        # #     # Or Les objets Task héritent de CompositeObject,
        # #     # et certains objets peuvent redéfinir __bool__ ou __len__.
        # #     #
        # #     # Si un objet parent :
        # #     # a 0 enfants
        # #     # ou définit __len__
        # #     # ou définit __bool__
        # #     # Alors "if parent:" peut retourner False
        # #     # même si parent n’est PAS None.
        #
        # # if parent is not None:  # None est le SEUL cas racine
        # #     # Un objet Task vide reste traité comme parent valide
        # #     # L’arbre ne repart plus à la racine
        # #     # _addObjectRecursively va réellement insérer les tâches
        # #     children = parent.children()
        # #     if children:
        # #         return [
        # #             child for child in self.presentation() if child in children
        # #         ]
        # #     else:
        # #         return []
        # # else:
        # #     return self.getRootItems()  # exécuté à tort
        #
        # if not self.presentation().treeMode():
        #     if parent is None:
        #         return list(self.presentation())
        #     else:
        #         return []
        # else:
        #     if parent is None:
        #         return self.getRootItems()
        #     else:
        #         return list(parent.children())

        # !!! Toujours passer par la presentation. !!!
        # Il ne faut JAMAIS contourner la presentation dans TaskCoach.
        presentation = self.presentation()
        log.debug(
            f"TreeViewer.children : mode arborescence actuel du filtre presentation.treeMode() = {presentation.treeMode()} pour presentation {presentation}."
        )

        if parent is None:
            # # result = list(presentation)
            # result = self.getRootItems()
            # Return only the root items from the presentation. Using the
            # presentation iterable directly may yield all items (flattened)
            # which causes a flat list instead of a hierarchical tree. Use
            # getRootItems() which delegates to presentation.rootItems()
            # and therefore returns only true root elements (parent() is None).
            log.debug(
                f"TreeViewer.children : parent est None, retourne les éléments racines de la présentation {presentation}."
            )
            # result = presentation
            # retourner presentation peut renvoyer tous les éléments (flatten), (c'est qu'il y a une erreur dans la construction de presentation puisque l'on est dans un TreeViewer !)
            # ce qui fait que tous les objets apparaissent
            # comme enfants directs de la racine et donne un affichage aplati.
            # rootItems() renvoie uniquement les éléments dont parent() is None
            # (les vrais racines), ce qui permet ensuite la récursivité correcte
            # (les vrais enfants seront retournés par parent.children() plus bas).
            result = self.getRootItems()
        else:
            # result = list(presentation.childrenOf(parent))
            result = parent.children()
            log.debug(
                f"TreeViewer.children : parent est {parent}, retourne les enfants {result} de ce parent."
            )

        # DEBUG CRITIQUE
        for obj in result:
            if obj is None:
                raise Exception("ERREUR : children() retourne None !")
            # Si ça plante ici → on sait que presentation.childrenOf() renvoie du None.
            # Si ça ne plante pas → le problème est dans _addObjectRecursively.

        log.debug(
            f"TreeViewer.children : Retourne les Enfants de {parent} dans {self.__class__.__name__} : {result}."
        )
        return result

    def getItemText(self, item):
        # def getItemText(self, item: object) -> str:
        """
        Retourne le texte (sujet) associé à un élément.

        Args :
            item : L'élément dont le texte est à retourner.

        Returns :
            (str) : Le texte (sujet) de l'élément.
        """
        return item.subject()


class ViewerWithColumns(
    Viewer
):  # pylint: disable=W0223 better TreeViewer than Viewer ? Non, il y a ListViewer ou TreeViewer. A la rigueur, un mixin !?
    """
    Classe ViewerWithColumns, héritant de Viewer.

    Cette classe permet de gérer des visionneuses avec des colonnes. Elle permet de gérer
    l'affichage dynamique des colonnes, la sélection, et les interactions avec les éléments
    dans une interface de type liste ou arbre avec des colonnes.

    Attributs :
        __initDone (bool) : Indique si l'initialisation est terminée.
        _columns (list) : Liste des colonnes disponibles.
        __visibleColumns (list) : Liste des colonnes actuellement visibles.
        __columnUICommands (list) : Liste des commandes de l'interface utilisateur liées aux colonnes.

    Explication des méthodes :
        * hasHideableColumns : Indique si certaines colonnes peuvent être masquées.
        * hasOrderingColumn : Vérifie si une colonne de tri est présente.
        * getColumnUICommands : Récupère ou génère les commandes pour gérer les colonnes.
        * initColumns et initColumn : Initialisent les colonnes et déterminent si elles sont visibles ou masquées.
        * showColumn et hideColumn : Permettent d'afficher ou de masquer des colonnes.
        * validateDrag : Valide si un élément peut être déplacé dans la colonne sélectionnée.
        * __startObserving et __stopObserving : Ces méthodes gèrent l'abonnement aux événements en fonction des colonnes visibles.
          Lorsqu'une colonne devient visible, les événements associés à cette colonne sont observés,
          et lorsque la colonne est masquée, les événements ne sont plus observés.
        * renderCategories et renderSubjectsOfRelatedItems : Ces méthodes permettent d'afficher les catégories
          ou d'autres éléments liés à l'élément courant. Elles rassemblent les sujets des éléments et les présentent sous forme de chaîne de texte.
        * renderSubjects, renderCreationDateTime, et renderModificationDateTime : Ces méthodes formatent et affichent
          les sujets, ainsi que les dates de création et de modification des éléments.
        * isItemCollapsed : Cette méthode vérifie si un élément est réduit dans une vue arborescente.
          Elle dépend de deux méthodes qui devraient être définies dans une sous-classe (par exemple, TreeViewer),
          à savoir getItemExpanded et isTreeViewer. Celles-ci sont utilisées pour déterminer l'état d'expansion ou de réduction d'un élément.

    Concernant les méthodes isTreeViewer et getItemExpanded :
        * isTreeViewer : Cette méthode est définie dans les sous-classe
          TreeViewer et ListViewer. Elle permet de différencier les vues
          arborescentes des vues en liste.
        * getItemExpanded : De même, cette méthode est définie dans la
          sous-classe Treeviewer pour gérer l'état d'expansion ou de collapse
          d'un élément dans une vue arborescente.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la visionneuse avec des colonnes.

        Args :
            *args : Arguments supplémentaires pour l'initialisation.
            **kwargs : Arguments nommés supplémentaires pour l'initialisation.
        """
        log.debug(
            f"ViewerWithColumns : Initialisation Création de la visionneuse {self.__class__.__name__} avec des colonnes."
        )
        # Indique si l'initialisation est terminée.
        self.__initDone = False
        # Liste des colonnes disponibles.
        self._columns = []
        # Liste des colonnes actuellement visibles.
        self.__visibleColumns = []
        # Liste des commandes de l'interface utilisateur liées aux colonnes.
        self.__columnUICommands = []
        super().__init__(*args, **kwargs)
        self.initColumns()
        self.__initDone = True
        # refresh permet d'afficher les listes des tâches et catégories dans les colonnes.
        self.refresh()
        # log.debug("ViewerWithColumns initialisé !")
        log.debug(
            f"ViewerWithColumns initialisé ! : Colonnes disponibles : {self._columns}. Colonnes visibles : {self.__visibleColumns}."
        )

    def hasHideableColumns(self):
        """
        Indique si la visionneuse a des colonnes masquables.

        Returns :
            (bool) : True si certaines colonnes peuvent être masquées, sinon False.
        """
        return True

    def hasOrderingColumn(self):
        """
        Vérifie si une colonne de tri (ordering) est présente parmi les colonnes visibles.

        Returns :
            (bool) : True si une colonne "ordering" est visible, sinon False.
        """
        for column in self.__visibleColumns:
            if column.name() == "ordering":
                return True
        return False

    def getColumnUICommands(self):
        """
        Retourne les commandes de l'interface utilisateur pour gérer les colonnes.

        Returns :
            (list) : Liste des commandes UI pour les colonnes.
        """
        if not self.__columnUICommands:
            self.__columnUICommands = self.createColumnUICommands()
        return self.__columnUICommands

    def createColumnUICommands(self):
        """
        Crée les commandes de l'interface utilisateur pour les colonnes.

        Raises :
            NotImplementedError : Si non implémenté dans une sous-classe.
        """
        raise NotImplementedError

    def refresh(self, *args, **kwargs):
        """
        Rafraîchit la vue si l'initialisation est terminée.

        Args :
            *args : Arguments supplémentaires pour la méthode de rafraîchissement.
            **kwargs : Arguments nommés supplémentaires.
        """
        log.debug(
            f"ViewerWithColumns.refresh : Rafraichissement de la vue si l'initialisation est terminée."
        )
        if self and self.__initDone:
            log.debug(
                f"ViewerWithColumns.refresh : Rafraichissement de la vue."
            )
            super().refresh(*args, **kwargs)
        log.debug(f"ViewerWithColumns.refresh : Rafraichissement terminé !")

    def initColumns(self):
        """
        Initialise les colonnes de la visionneuse en les rendant visibles ou non en fonction des paramètres.
        """
        for column in self.columns():
            self.initColumn(column)
        if self.hasOrderingColumn():
            self.widget.SetResizeColumn(1)
            self.widget.SetMainColumn(1)
        # self.refresh()

    def initColumn(self, column):
        """
        Initialise une colonne et détermine si elle doit être visible ou non.

        Args :
            column : La colonne à initialiser.
        """
        if column.name() in self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        ):
            log.debug(
                f"ViewerWithColumns.initColumn : la colonne {column.name()} est toujours visible selon les paramètres."
            )
            show = True
        else:
            show = column.name() in self.settings.getlist(
                self.settingsSection(), "columns"
            )
            log.debug(
                f"ViewerWithColumns.initColumn : la colonne {column.name()} est {'visible' if show else 'masquée'} selon les paramètres."
            )
            self.widget.showColumn(column, show=show)
        if show:
            log.debug(
                f"ViewerWithColumns.initColumn : ajoute la colonne {column.name()} aux colonnes visibles : {self.__visibleColumns}"
            )
            self.__visibleColumns.append(column)
            self.__startObserving(column.eventTypes())
        # self.refresh()

    def showColumnByName(self, columnName, show=True):
        """
        Affiche ou masque une colonne par son nom.

        Args :
            columnName (str) : Le nom de la colonne à afficher ou masquer.
            show (bool) : True pour afficher, False pour masquer.
        """
        for column in self.hideableColumns():
            if columnName == column.name():
                isVisibleColumn = self.isVisibleColumn(column)
                if (show and not isVisibleColumn) or (
                    not show and isVisibleColumn
                ):
                    self.showColumn(column, show)
                break
        # self.refresh()

    def showColumn(self, column, show=True, refresh=True):
        """
        Affiche ou masque une colonne et met à jour la vue.

        Args :
            column : La colonne à afficher ou masquer.
            show (bool) : True pour afficher, False pour masquer.
            refresh (bool) : True pour rafraîchir la vue après l'opération.
        """
        if column.name() == "ordering":
            self.widget.SetResizeColumn(1 if show else 0)
            self.widget.SetMainColumn(1 if show else 0)

        if show:
            self.__visibleColumns.append(column)
            # Make sure we keep the columns in the right order:
            self.__visibleColumns = [
                c for c in self.columns() if c in self.__visibleColumns
            ]
            self.__startObserving(column.eventTypes())
        else:
            self.__visibleColumns.remove(column)
            self.__stopObserving(column.eventTypes())
        self.widget.showColumn(column, show)
        # Set main column AFTER inserting/removing the ordering column
        if column.name() == "ordering":
            self.widget.SetResizeColumn(1 if show else 0)
            self.widget.SetMainColumn(1 if show else 0)
        self.settings.set(
            self.settingsSection(),
            "columns",
            str([column.name() for column in self.__visibleColumns]),
        )
        log.debug(
            f"ViewerWithColumns.showColumn : la colonne {column.name()} est maintenant {'affichée' if show else 'masquée'}. Vérifie si rafraîchir la vue."
        )
        if refresh:
            log.debug(
                f"ViewerWithColumns.showColumn : rafraîchissement de la vue après avoir {'affiché' if show else 'masqué'} la colonne {column.name()}."
            )
            # self.widget.RefreshAllItems(len(self.presentation()))
            self.widget.scheduleRefresh(
                len(self.presentation())
            )  # AttributeError: 'VirtualListCtrl' object has no attribute 'scheduleRefresh'

    def hideColumn(self, visibleColumnIndex):
        """
        Masque une colonne visible par son index.

        Args :
            visibleColumnIndex (int) : L'index de la colonne à masquer.
        """
        column = self.visibleColumns()[visibleColumnIndex]
        self.showColumn(column, show=False)
        # self.refresh()

    def columns(self):
        # def columns(self) -> list:
        """
        Retourne toutes les colonnes disponibles dans la visionneuse.

        Returns :
            (list) : Liste des colonnes.
        """
        return self._columns

    def selectableColumns(self):
        # def selectableColumns(self) -> list:
        """
        Retourne les colonnes sélectionnables.

        Returns :
            (list) : Liste des colonnes sélectionnables.
        """
        return self._columns

    def isVisibleColumnByName(self, columnName):
        # def isVisibleColumnByName(self, columnName: str) -> bool:
        """
        Vérifie si une colonne est visible par son nom.

        Args :
            columnName (str) : Le nom de la colonne à vérifier.

        Returns :
            (bool) : True si la colonne est visible, sinon False.
        """
        return columnName in [
            column.name() for column in self.__visibleColumns
        ]

    def isVisibleColumn(self, column):
        # def isVisibleColumn(self, column) -> bool:
        """
        Vérifie si une colonne est visible.

        Args :
            column : La colonne à vérifier.

        Returns :
            (bool) : True si la colonne est visible, sinon False.
        """
        return column in self.__visibleColumns

    def visibleColumns(self):
        # def visibleColumns(self) -> list:
        """
        Retourne la liste des colonnes visibles.

        Returns :
            Liste des colonnes actuellement visibles.
        """
        return self.__visibleColumns

    def hideableColumns(self):
        # def hideableColumns(self) -> list:
        """
        Retourne les colonnes qui peuvent être masquées.

        Returns :
            Liste des colonnes masquables.
        """
        return [
            column
            for column in self._columns
            if column.name()
            not in self.settings.getlist(
                self.settingsSection(), "columnsalwaysvisible"
            )
        ]

    def isHideableColumn(self, visibleColumnIndex):
        column = self.visibleColumns()[visibleColumnIndex]
        unhideableColumns = self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        )
        return column.name() not in unhideableColumns

    def getColumnWidth(self, columnName):
        # def getColumnWidth(self, columnName: str) -> int:
        """
        Retourne la largeur d'une colonne recherchée par son nom.

        Args :
            columnName (str) : Le nom de la colonne.

        Returns :
            (int) : La largeur de la colonne.
        """
        # log.debug(f"ViewerWithColumns.getColumnWidth est appelé par self={self}, pour columnName={columnName}")
        columnWidths = self.settings.getdict(
            self.settingsSection(), "columnwidths"
        )
        # defaultWidth = (
        #     28 if columnName == "ordering" else hypertreelist._DEFAULT_COL_WIDTH
        # )  # pylint: disable=W0212
        # Access to a protected member _DEFAULT_COL_WIDTH of a module
        # Dans hypertreelist _DEFAULT_COL_WIDTH = 100
        defaultWidth = (
            28 if columnName == "ordering" else 100
        )  # pylint: disable=W0212
        columnWidthGot = columnWidths.get(columnName, defaultWidth)
        # log.debug(f"ViewerWithColumns.getColumnWidth retourne la largeur de la colonne {columnName} : {columnWidthGot} pour self.={self.__class__.Name}")
        return columnWidthGot

    def onResizeColumn(self, column, width):
        # def onResizeColumn(self, column, width: int):
        """
        Gère le redimensionnement d'une colonne et met à jour les paramètres.

        Args :
            column : La colonne redimensionnée.
            width (int) : La nouvelle largeur de la colonne.
        """
        columnWidths = self.settings.getdict(
            self.settingsSection(), "columnwidths"
        )
        columnWidths[column.name()] = width
        self.settings.setdict(
            self.settingsSection(), "columnwidths", columnWidths
        )

    def validateDrag(self, dropItem, dragItems, columnIndex):
        # def validateDrag(self, dropItem, dragItems, columnIndex: int) -> bool:
        """
        Valide si un élément peut être déplacé (drag and drop) dans une colonne.

        Args :
            dropItem : L'élément où l'élément est déposé.
            dragItems : Les éléments en cours de déplacement.
            columnIndex (int) : L'index de la colonne affectée.

        Returns :
            (bool | None) : True si le déplacement est valide, sinon False.
        """
        log.debug(f"ViewerWithColumns.validateDrag est appelé.")
        if (
            columnIndex == -1
            or self.visibleColumns()[columnIndex].name() != "ordering"
        ):
            return None  # Normal behavior

        # Ordering
        # if issubclass((TreeViewer, ListViewer), self):  # à mettre ou similaire ?
        if not self.isTreeViewer():  # where come from ?
            # isTreeViewer : Cette méthode est définie dans les sous-classe TreeViewer et ListViewer.
            # Elle permet de différencier les vues arborescentes des vues en liste.
            # Ici, pour ListViewer, validateDrag doit être True !
            return True

        # Tree mode. Only allow drag if all selected items are siblings.
        # Mode arborescence. Autorisez la glisser si tous les éléments sélectionnés sont des frères et sœurs.
        if len(set([item.parent() for item in dragItems])) >= 2:
            wx.GetTopLevelParent(self).AddBalloonTip(
                self.settings,
                "treemanualordering",
                self,
                title=_("Reordering in tree mode"),
                getRect=lambda: wx.Rect(0, 0, 28, 16),
                message=_(
                    """When in tree mode, manual ordering is only possible when all selected items are siblings."""
                ),
            )
            return False

        # S'ils sont parent, autorisez seulement la déplacer au même niveau.
        if dragItems[0].parent() != (
            None if dropItem is None else dropItem.parent()
        ):
            wx.GetTopLevelParent(self).AddBalloonTip(
                self.settings,
                "treechildrenmanualordering",
                self,
                title=_("Reordering in tree mode"),
                getRect=lambda: wx.Rect(0, 0, 28, 16),
                message=_(
                    """When in tree mode, you can only put objects at the same level (parent)."""
                ),
            )
            return False

        return True

    def getItemText(self, item, column=None):
        # def getItemText(self, item, column=None) -> str:
        """
        Retourne le texte d'un élément pour une colonne spécifique.

        Args :
            item : L'élément dont on veut obtenir le texte.
            column : La colonne à utiliser pour récupérer le texte.

        Returns :
            (str) : Le texte de l'élément pour la colonne spécifiée.
        """
        if column is None:
            column = 1 if self.hasOrderingColumn() else 0
        column = self.visibleColumns()[column]
        # log.debug(
        #     "ViewerWithColumns.getItemText : Visible columns: %s",
        #     self.visibleColumns(),
        # )
        log.debug(
            "ViewerWithColumns.getItemText : Column index demandé: %s des colonnes visibles %s",
            column,
            self.visibleColumns(),
        )
        log.debug("ViewerWithColumns.getItemText : Item: %s", item)
        return column.render(item)

    def getItemImages(self, item, column=0):
        # def getItemImages(self, item, column: int = 0) -> dict:
        """
        Retourne les images associées à un élément pour une colonne spécifique.

        Args :
            item : L'élément dont on veut obtenir les images.
            column int : L'index de la colonne.

        Returns :
            Dictionnaire des images associées à l'élément.
        """
        column = self.visibleColumns()[column]
        return column.imageIndices(item)

    def hasColumnImages(self, column):
        """
        Vérifie si une colonne contient des images.

        Args :
            column : (int?) La colonne à vérifier.

        Returns :
            (bool) : True si la colonne contient des images, sinon False.
        """
        return self.visibleColumns()[column].hasImages()

    def subjectImageIndices(self, item):
        # def subjectImageIndices(self, item) -> dict:
        """
        Retourne les indices des images associées au sujet d'un élément.

        Args :
            item : L'élément dont on veut obtenir les indices d'images.

        Returns :
            Dictionnaire des indices d'images associés.
        """
        normalIcon = item.icon(recursive=True)
        selectedIcon = item.selectedIcon(recursive=True) or normalIcon
        normalImageIndex = self.imageIndex[normalIcon] if normalIcon else -1
        selectedImageIndex = (
            self.imageIndex[selectedIcon] if selectedIcon else -1
        )
        return {
            wx.TreeItemIcon_Normal: normalImageIndex,
            wx.TreeItemIcon_Expanded: selectedImageIndex,
        }

    def __startObserving(self, eventTypes):
        # def __startObserving(self, eventTypes: list):
        """
        Commence à observer les événements spécifiés pour les colonnes visibles.

        Args :
            eventTypes : Liste des types d'événements à observer.
        """
        for eventType in eventTypes:
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType=eventType
                )

    def __stopObserving(self, eventTypes):
        # def __stopObserving(self, eventTypes: list):
        """
        Arrête d'observer les événements spécifiés pour les colonnes qui ne sont plus visibles.

        Args :
            eventTypes : Liste des types d'événements à arrêter d'observer.
        """
        # Collecte les types d'événements auxquels les colonnes visibles sont encore intéressées
        # Collect the event types that the currently visible columns are
        # interested in and make sure we don't stop observing those event types.
        eventTypesOfVisibleColumns = []
        for column in self.visibleColumns():
            eventTypesOfVisibleColumns.extend(column.eventTypes())
        for eventType in eventTypes:
            if eventType not in eventTypesOfVisibleColumns:
                if eventType.startswith("pubsub"):
                    pub.unsubscribe(self.onAttributeChanged, eventType)
                else:
                    self.removeObserver(
                        self.onAttributeChanged_Deprecated, eventType=eventType
                    )

    def renderCategories(self, item):
        # def renderCategories(self, item: object) -> str:
        """
        Rendre les catégories associées à un élément donné.

        Args :
            item : L'élément dont on veut afficher les catégories.

        Returns :
            (str) : Une chaîne contenant les catégories de l'élément.
        """
        return self.renderSubjectsOfRelatedItems(item, item.categories)

    def renderSubjectsOfRelatedItems(self, item, getItems):
        # def renderSubjectsOfRelatedItems(self, item: object, getItems) -> str:
        """
        Rendre les sujets des éléments liés (catégories ou autres relations).

        Args :
            item : L'élément pour lequel on veut afficher les sujets liés.
            getItems : (callable) Fonction pour récupérer les éléments liés.

        Returns :
            (str) : Une chaîne des sujets des éléments liés.
        """
        subjects = []
        ownItems = getItems(recursive=False)
        if ownItems:
            subjects.append(self.renderSubjects(ownItems))
        isListViewer = (
            not self.isTreeViewer()
        )  # pylint: disable=E1101  # where come from ?
        if isListViewer or self.isItemCollapsed(item):
            childItems = [
                theItem
                for theItem in getItems(recursive=True, upwards=isListViewer)
                if theItem not in ownItems
            ]
            if childItems:
                # subjects.append("(%s)" % self.renderSubjects(childItems))
                subjects.append(f"({self.renderSubjects(childItems)})")
        return " ".join(subjects)

    @staticmethod
    def renderSubjects(items):
        # def renderSubjects(items: list) -> str:
        """
        Rendre les sujets d'une liste d'éléments.

        Args :
            items : Liste des éléments dont on veut obtenir les sujets.

        Returns :
            (str) : Une chaîne contenant les sujets des éléments, triés par ordre alphabétique.
        """
        subjects = [item.subject(recursive=True) for item in items]
        return ", ".join(sorted(subjects))

    @staticmethod
    def renderCreationDateTime(item, humanReadable=True):
        # def renderCreationDateTime(item: object, humanReadable: bool = True) -> str:
        """
        Rendre la date et l'heure de création d'un élément.

        Args :
            item : L'élément dont on veut afficher la date de création.
            humanReadable (bool) : Indique si la date doit être formatée de manière lisible.

        Returns :
            (str) : La date et l'heure de création de l'élément.
        """
        return render.dateTime(
            item.creationDateTime(), humanReadable=humanReadable
        )

    @staticmethod
    def renderModificationDateTime(item, humanReadable=True):
        # def renderModificationDateTime(item: object, humanReadable: bool = True) -> str:
        """
        Rendre la date et l'heure de modification d'un élément.

        Args :
            item : L'élément dont on veut afficher la date de modification.
            humanReadable (bool) : Indique si la date doit être formatée de manière lisible.

        Returns :
            (str) : La date et l'heure de modification de l'élément.
        """
        return render.dateTime(
            item.modificationDateTime(), humanReadable=humanReadable
        )

    def isItemCollapsed(self, item):
        # def isItemCollapsed(self, item: object) -> bool:
        # pylint: disable=E1101
        """
        Vérifie si un élément est réduit dans la vue actuelle (uniquement pertinent pour les vues arborescentes).

        Args :
            item : L'élément à vérifier.

        Returns :
            (bool) : True si l'élément est réduit, False sinon.
        """
        return (
            not self.getItemExpanded(item)
            if self.isTreeViewer() and item.children()
            else False
        )

    # Unresolved attribute reference 'getItemExpanded' for class 'ViewerWithColumns'
    # Unresolved attribute reference 'isTreeViewer' for class 'ViewerWithColumns'  # where come from ? TreeViewer?
    # Non, cette méthode vient de Viewer dont il est enfant ! Pourquoi ne la reconnaît-il pas ?


class SortableViewerWithColumns(
    mixin.SortableViewerMixin, ViewerWithColumns
):  # pylint: disable=W0223
    """
    Classe SortableViewerWithColumns, héritant de ViewerWithColumns et du mixin SortableViewerMixin.

    Cette classe permet de gérer des colonnes triables dans une vue. Elle ajoute la fonctionnalité de tri
    sur les colonnes d'une visionneuse. Lorsqu'une colonne est triée, la direction du tri (croissant ou décroissant)
    est indiquée par une icône spécifique.

    Hérite de :
        ViewerWithColumns : Gestion des colonnes dans la visionneuse.
        SortableViewerMixin : Ajoute la capacité de tri des éléments dans la visionneuse.

    Explication des méthodes :

    initColumn : Initialise une colonne et vérifie si cette colonne est celle utilisée
                 pour le tri. Si c'est le cas, elle affiche l'icône de tri dans la colonne
                 et montre l'ordre de tri (croissant ou décroissant).
    setSortOrderAscending : Définit l'ordre de tri en croissant et met à jour
                            l'affichage de l'icône de tri pour refléter cette direction.
    sortBy : Trie les éléments par une colonne donnée. Une fois le tri effectué,
             la colonne utilisée pour le tri et la direction du tri sont affichées dans la vue.
    showSortColumn : Affiche l'icône de tri dans la colonne actuellement utilisée pour le tri.
    showSortOrder : Affiche une icône indiquant la direction du tri (une flèche
                    vers le haut pour un tri ascendant, une flèche vers le bas pour un tri descendant).
    getSortOrderImage : Retourne le nom de l'icône correspondant à la direction
                        du tri (flèche vers le haut pour le tri ascendant et
                        flèche vers le bas pour le tri descendant).

    Cette classe utilise les fonctionnalités du mixin.SortableViewerMixin pour
    ajouter des capacités de tri à la visionneuse avec colonnes.

    Les méthodes gèrent aussi bien l'initialisation des colonnes que la gestion
    du tri avec des indicateurs visuels (icônes).
    """

    def initColumn(self, column):
        """
        Initialise une colonne et, si elle est utilisée pour le tri, affiche l'icône de tri correspondante.

        Args:
            column: La colonne à initialiser.
        """
        # log.debug(
        #     "SortableViewerWithColumns.initColumn Initialise une colonne."
        # )
        super().initColumn(column)
        # log.debug(
        #     f"SortableViewerWithColumns.initColumn : Vérifie si la colonne {column.name()} est utilisée pour le tri."
        # )
        if self.isSortedBy(column.name()):
            # log.debug(
            #     f"SortableViewerWithColumns.initColumn : La colonne {column.name()} est utilisée pour le tri. Affiche l'icône de tri."
            # )
            self.widget.showSortColumn(column)
            # log.debug(
            #     f"SortableViewerWithColumns.initColumn : Affiche l'ordre de tri pour la colonne {column.name()}."
            # )
            self.showSortOrder()
            log.debug(
                f"SortableViewerWithColumns.initColumn : La colonne {column.name()} est maintenant visible avec l'icône de tri."
            )
        # log.debug(
        #     f"SortableViewerWithColumns.initColumn : Colonnes visibles après initialisation de la colonne {column.name()}."
        # )

    def setSortOrderAscending(self, *args, **kwargs):  # pylint: disable=W0221
        """
        Définit l'ordre de tri en croissant et met à jour l'affichage de l'icône de tri.

        Args :
            *args : Arguments supplémentaires pour la méthode de tri.
            **kwargs : Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().setSortOrderAscending(*args, **kwargs)
        self.showSortOrder()

    def sortBy(self, *args, **kwargs):  # pylint: disable=W0221
        """
        Trie les éléments de la visionneuse par une colonne spécifique et met à jour l'affichage de l'icône de tri.

        Args :
            *args : Arguments supplémentaires pour la méthode de tri.
            **kwargs : Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().sortBy(*args, **kwargs)
        self.showSortColumn()
        self.showSortOrder()

    def showSortColumn(self):
        """
        Affiche la colonne actuellement utilisée pour le tri, avec l'icône correspondante.
        """
        for column in self.columns():
            if self.isSortedBy(column.name()):
                self.widget.showSortColumn(column)
                break

    def showSortOrder(self):
        """
        Affiche l'icône indiquant l'ordre du tri (ascendant ou descendant) dans la visionneuse.
        """
        self.widget.showSortOrder(self.imageIndex[self.getSortOrderImage()])

    def getSortOrderImage(self):
        # def getSortOrderImage(self) -> str:
        """
        Retourne l'image associée à la direction du tri.

        Returns :
            (str) : Le nom de l'icône pour indiquer le tri ascendant ou descendant.
        """
        return (
            "arrow_up_icon"
            if self.isSortOrderAscending()
            else "arrow_down_icon"
        )
