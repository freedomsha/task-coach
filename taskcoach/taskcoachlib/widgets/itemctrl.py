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

Module `itemctrl.py`

Ce module fournit des mixins pour gérer des contrôles avec des éléments tels que
`wx.ListCtrl`, `wx.TreeCtrl`, et `wx.TreeListCtrl`. Il étend la fonctionnalité
de ces contrôles pour inclure :
- Gestion des menus contextuels sur les éléments ou les colonnes.
- Prise en charge des événements de glisser-déposer.
- Colonnes masquables et redimensionnables.
- Colonnes avec tri et indicateurs de tri.

Classes principales :
- `_CtrlWithItemsMixin` : Classe de base pour les contrôles avec des éléments.
- `_CtrlWithPopupMenuMixin` : Ajoute la prise en charge des menus contextuels.
- `_CtrlWithItemPopupMenuMixin` : Menu contextuel pour des éléments spécifiques.
- `_CtrlWithColumnPopupMenuMixin` : Menu contextuel pour les colonnes.
- `_CtrlWithDropTargetMixin` : Permet de déposer des fichiers, URL ou e-mails.
- `CtrlWithToolTipMixin` : Ajoute des info-bulles spécifiques à chaque élément.
- `_CtrlWithHideableColumnsMixin` : Colonnes masquables.
- `_CtrlWithSortableColumnsMixin` : Colonnes avec tri et indicateurs de tri.
- `_CtrlWithAutoResizedColumnsMixin` : Colonnes redimensionnables automatiquement.
- `CtrlWithColumnsMixin` : Combine toutes les fonctionnalités ci-dessus.

Dépendances :
- wxPython : Le module utilise des classes comme `wx.ListCtrl`, `wx.TreeCtrl`, et
  `wx.TreeListCtrl`.
- wx.lib.agw.hypertreelist : Pour gérer des contrôles avancés.

Ce module dépend de méthodes spécifiques disponibles dans les contrôles hérités de
wxPython :
- `Bind`, `Unbind` : Gestion des événements.
- `PopupMenu`, `PopupMenuXY` : Gestion des menus contextuels.
- `GetMainWindow` : Accès à la fenêtre principale contenant le contrôle.
- `InsertColumn`, `DeleteColumn`, `GetColumnWidth`, etc. : Gestion des colonnes.

Assurez-vous que les classes utilisant ces mixins héritent des contrôles wxPython
appropriés pour éviter des erreurs.
"""

# pylint: disable=W0105

# from builtins import str
# from builtins import range
# from builtins import object
import logging
import wx
import inspect
from taskcoachlib.widgets import draganddrop
from taskcoachlib.widgets import autowidth
from taskcoachlib.widgets import tooltip

# from taskcoachlib.thirdparty import hypertreelist
# from taskcoachlib.thirdparty.customtreectrl import *
from wx.lib.agw import hypertreelist

# from wx.lib.agw.hypertreelist import *

log = logging.getLogger(__name__)


class _CtrlWithItemsMixin(object):
    """
    Classe de base pour les contrôles contenant des éléments, comme `ListCtrl`,
    `TreeCtrl`, ou `TreeListCtrl`.

    Fournit des méthodes génériques pour vérifier les éléments, accéder aux
    données associées, et gérer les sélections.

    Méthodes principales :
        - `_itemIsOk` : Vérifie si un élément est valide.
        - `_objectBelongingTo` : Retourne l'objet associé à un élément.
        - `SelectItem` : Sélectionne ou désélectionne un élément.
    """

    def _itemIsOk(self, item):
        """
        Vérifie si un élément est valide.

        Args :
            item : L'élément à vérifier.

        Returns :
            bool : `True` si l'élément est valide, sinon `False`.
        """
        try:
            return item.IsOk()  # for Tree(List)Ctrl
        except AttributeError:
            return item != wx.NOT_FOUND  # for ListCtrl

    def _objectBelongingTo(self, item):
        """
        Retourne l'objet associé à un élément.

        Args:
            item: L'élément dont on veut récupérer l'objet associé.

        Returns :
            L'objet associé à l'élément, ou `None` si l'élément n'est pas valide ou n'a pas d'objet associé.
        """
        if not self._itemIsOk(item):
            return None
        try:
            # return self.GetItemPyData(
            #     item
            # )  # TreeListCtrl  TODO: essayer GetItemData
            item_data = self.GetItemPyData(item)  # ListCtrl
            log.debug(
                f"_CtrlWithItemsMixin._objectBelongingTo : Récupération de l'objet associé à l'élément {item} : {item_data}"
            )
            return item_data if item_data is not None else None
        except AttributeError:
            item_data = self.getItemWithIndex(item)  # ListCtrl
            # return self.getItemWithIndex(item)  # ListCtrl
            return item_data if item_data is not None else None

    def SelectItem(self, item, *args, **kwargs):
        """
        Sélectionne ou désélectionne un élément.

        Pour les `TreeCtrl` et `TreeListCtrl`, utilise `SelectItem`. Pour les
        `ListCtrl`, utilise `SetItemState`.

        Args :
            item : L'élément à sélectionner ou désélectionner.
            select (bool) : Si `True`, sélectionne l'élément. Sinon, le désélectionne.
        """
        try:
            # Tree(List)Ctrl:
            super().SelectItem(item, *args, **kwargs)
        except AttributeError:
            # ListCtrl:
            select = kwargs.get("select", True)
            newState = wx.LIST_STATE_SELECTED
            if not select:
                newState = ~newState
            self.SetItemState(item, newState, wx.LIST_STATE_SELECTED)


class _CtrlWithPopupMenuMixin(_CtrlWithItemsMixin):
    """Classe de base pour les contrôles avec PopupMenu.

    Ajoute la prise en charge des menus contextuels.

    Méthodes principales :
        - `_attachPopupMenu` : Lie un gestionnaire d'événements pour afficher
          un menu contextuel.
    """

    @staticmethod
    def _attachPopupMenu(eventSource, eventTypes, eventHandler):
        """
        Méthode utilitaire qui lie un gestionnaire d'événements pour afficher un menu contextuel.

        Args :
            eventSource : La source de l'événement.
            eventTypes (list) : Liste des types d'événements.
            eventHandler : Gestionnaire d'événements pour afficher le menu.
        """
        for eventType in eventTypes:
            eventSource.Bind(eventType, eventHandler)


class _CtrlWithItemPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """Le menu contextuel est sur les éléments.

    Ajoute un menu contextuel spécifique aux éléments.

    Méthodes principales :
        - `onItemPopupMenu` : Affiche le menu contextuel pour un élément.
    """

    def __init__(self, *args, **kwargs):
        log.debug(
            "_CtrlWithItemPopupMenuMixin.__init__ : Initialisation du menu contextuel sur les éléments."
        )
        self._itemPopupMenu = kwargs.pop("itemPopupMenu")
        super().__init__(*args, **kwargs)
        if self._itemPopupMenu is not None:
            # Determine if this is a ListCtrl or tree control
            # ListCtrl has GetItemRect but not GetRootItem
            isListCtrl = hasattr(self, "GetItemRect") and not hasattr(
                self, "GetRootItem"
            )
            if isListCtrl:
                # For ListCtrl: use EVT_LIST_ITEM_RIGHT_CLICK for item clicks
                # (provides GetIndex() directly) and EVT_CONTEXT_MENU for empty space
                self._attachPopupMenu(
                    self,
                    (wx.EVT_LIST_ITEM_RIGHT_CLICK,),
                    self.onListItemRightClick,
                )
                self._attachPopupMenu(
                    self,
                    (wx.EVT_CONTEXT_MENU,),
                    self.onListContextMenu,
                )
            else:
                # For tree controls: use EVT_TREE_ITEM_RIGHT_CLICK and EVT_CONTEXT_MENU
                self._attachPopupMenu(
                    self,
                    (wx.EVT_TREE_ITEM_RIGHT_CLICK, wx.EVT_CONTEXT_MENU),
                    self.onItemPopupMenu,
                )
                # Also bind to MainWindow to catch right-clicks on empty space
                self.GetMainWindow().Bind(
                    wx.EVT_RIGHT_DOWN, self._onMainWindowRightDown
                )
        log.debug("_CtrlWithItemPopupMenuMixin initialisé !")

    def _onMainWindowRightDown(self, event):
        """Handle right-click on MainWindow for tree controls.

        This catches clicks on empty space that EVT_TREE_ITEM_RIGHT_CLICK misses.
        """
        point = event.GetPosition()
        item = self.HitTest(point)[0]
        if not self._itemIsOk(item):
            # Clicked on empty space - clear selection and show popup
            self.clear_selection()
            self._updateMenuUI()
            self.PopupMenu(self._itemPopupMenu)
        else:
            # Clicked on an item - let normal event handling take over
            event.Skip()

    def _updateMenuUI(self):
        """Update enabled state of menu items based on current selection.

        Menu items are bound to a window with EVT_UPDATE_UI handlers, but those
        handlers don't fire automatically for popup menus. We manually process
        UpdateUIEvent for each menu item to update their enabled state.
        """
        menuWindow = getattr(self._itemPopupMenu, "_window", None)
        if menuWindow and self._itemPopupMenu:
            for menuItem in self._itemPopupMenu.GetMenuItems():
                if menuItem.IsSeparator():
                    continue
                itemId = menuItem.GetId()
                event = wx.UpdateUIEvent(itemId)
                menuWindow.ProcessEvent(event)
                if event.GetSetEnabled():
                    menuItem.Enable(event.GetEnabled())

    def onItemPopupMenu(self, event):
        """
        Affiche le menu contextuel pour un élément.

        Sélectionne l'élément sous le curseur avant d'afficher le menu.

        Args :
            event (wx.Event) : Événement déclenchant le menu contextuel.
        """
        # Assurez-vous que la fenêtre de ce contrôle est au foyer:
        try:
            window = event.GetEventObject().MainWindow
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        # Get click position - GetPoint() for tree item events, GetPosition() for context menu
        point = None
        # if hasattr(event, "GetPoint"):
        #     # Make sure the item under the mouse is selected because that
        #     # is what users expect and what is most user-friendly. Not all
        #     # widgets do this by default, e.g. the TreeListCtrl does not.
        #     item = self.HitTest(event.GetPoint())[0]
        #     if not self._itemIsOk(item):
        #         return
        #     if not self.IsSelected(item):
        #         self.UnselectAll()
        #         self.SelectItem(item)
        if hasattr(event, "GetPoint"):
            point = event.GetPoint()
        elif hasattr(event, "GetPosition"):
            pos = event.GetPosition()
            if pos != wx.DefaultPosition:
                point = self.ScreenToClient(pos)
        if point is not None:
            # Make sure the item under the mouse is selected because that
            # is what users expect and what is most user-friendly. Not all
            # widgets do this by default, e.g. the TreeListCtrl does not.
            item = self.HitTest(point)[0]
            if not self._itemIsOk(item):
                # Clicked on empty space - clear selection so menu items
                # properly reflect no selection
                self.clear_selection()
                self._updateMenuUI()
                self.PopupMenu(self._itemPopupMenu)
                return
            if not self.IsSelected(item):
                self.clear_selection()
                self.SelectItem(item)
        # Update menu item enabled states and show popup
        self._updateMenuUI()
        self.PopupMenu(self._itemPopupMenu)

    def onListItemRightClick(self, event):
        """Handle EVT_LIST_ITEM_RIGHT_CLICK for ListCtrl controls.

        This event fires when right-clicking on an item and provides
        GetIndex() to get the clicked item directly - the proper way
        to handle ListCtrl right-clicks.
        """
        self.SetFocus()
        # Get the clicked item index from the event
        itemIndex = event.GetIndex()
        # Select the item if not already selected
        if not self.IsSelected(itemIndex):
            self.clear_selection()
            self.Select(itemIndex, True)
        # Update menu and show popup
        self._updateMenuUI()
        self.PopupMenu(self._itemPopupMenu)

    def onListContextMenu(self, event):
        """Handle EVT_CONTEXT_MENU for ListCtrl controls.

        This handles right-clicks on empty space (EVT_LIST_ITEM_RIGHT_CLICK
        only fires for item clicks). Also handles keyboard context menu key.
        """
        self.SetFocus()
        pos = event.GetPosition()
        if pos != wx.DefaultPosition:
            # Mouse-triggered context menu - check if on empty space
            clientPoint = self.ScreenToClient(pos)
            item = self.HitTest(clientPoint)[0]
            if self._itemIsOk(item):
                # Click was on an item - EVT_LIST_ITEM_RIGHT_CLICK already handled it
                return
            # Click on empty space - clear selection
            self.clear_selection()
        # Update menu and show popup
        self._updateMenuUI()
        self.PopupMenu(self._itemPopupMenu)


class _CtrlWithColumnPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """Cette classe active un menu contextuel par clic droit sur les en-têtes de colonnes. Le menu contextuel
    doit s'attendre à ce qu'un columnIndex de propriété publique soit défini de sorte
    que le contrôle puisse indiquer au menu sur quelle colonne l'utilisateur a cliqué pour
    faire apparaître le menu.
    """

    def __init__(self, *args, **kwargs):
        log.debug(
            "_CtrlWithColumnPopupMenuMixin.__init__ : initialisation  pour activer un menu contextuel sur les en-têtes de colonnes."
        )
        self.__popupMenu = kwargs.pop("columnPopupMenu")
        super().__init__(*args, **kwargs)
        if self.__popupMenu is not None:
            self._attachPopupMenu(
                self, [wx.EVT_LIST_COL_RIGHT_CLICK], self.onColumnPopupMenu
            )
        log.debug("_CtrlWithColumnPopupMenuMixin initialisé !")

    def onColumnPopupMenu(self, event):
        # We store the columnIndex in the menu, because it's near to
        # impossible for commands in the menu to determine on what column the
        # menu was popped up.
        columnIndex = event.GetColumn()
        self.__popupMenu.columnIndex = columnIndex
        # Parce qu'un clic droit sur les en-têtes de colonnes ne donne pas automatiquement le focus
        # au contrôle, nous forçons le focus :
        try:
            window = event.GetEventObject().GetMainWindow()
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        # self.PopupMenuXY(self.__popupMenu, *event.GetPosition())  # TODO : A changer !
        self.PopupMenu(self.__popupMenu)
        event.Skip(False)


class _CtrlWithDropTargetMixin(_CtrlWithItemsMixin):
    """
    Mixin qui Permet aux contrôles d'accepter des fichiers, URL ou e-mails déposés.

    Contrôle qui accepte que des fichiers, des e-mails ou des URL soient déposés sur des éléments.

    Méthodes principales :
        - `onDropURL` : Gère le dépôt d'une URL.
        - `onDropFiles` : Gère le dépôt de fichiers.
        - `onDropMail` : Gère le dépôt de courriers électroniques.
    """

    def __init__(self, *args, **kwargs):
        log.debug(
            "_CtrlWithDropTargetMixin.__init__ : initialise le mixin qui permet aux contrôles d'accepter des fichiers déposés."
        )
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)
        self.__dropHighlightItem = None  # Track highlighted item during drag
        # Hover-expand timer: auto-expand collapsed items after hover delay
        self.__hoverExpandTimerId = wx.NewIdRef()
        self.__hoverExpandTimer = (
            None  # Created lazily when drop target is set
        )
        self.__hoverExpandItem = (
            None  # Item currently being hovered for expansion
        )
        super().__init__(*args, **kwargs)

        # Initialise la gestionnaire de glisser-déposer de draganddrop.py
        if (
            self.__onDropURLCallback
            or self.__onDropFilesCallback
            or self.__onDropMailCallback
        ):
            dropTarget = draganddrop.DropTarget(
                self.onDropURL,
                self.onDropFiles,
                self.onDropMail,
                self.onDragOver,
            )
            self.GetMainWindow().SetDropTarget(dropTarget)
            # Initialize hover-expand timer
            self.__hoverExpandTimer = wx.Timer(self, self.__hoverExpandTimerId)
            self.Bind(
                wx.EVT_TIMER,
                self.__onHoverExpandTimer,
                id=self.__hoverExpandTimerId,
            )
        log.debug("_CtrlWithDropTargetMixin initialisé !")

    def onDropURL(self, x, y, url):
        """
        Gère le dépôt d'une URL sur un élément.

        Args :
            x (int) : Coordonnée X du point de dépôt.
            y (int) : Coordonnée Y du point de dépôt.
            url (str) : URL déposée.
        """
        self._clearDropHighlight()  # Clear highlight on drop
        self.__stopHoverExpandTimer()  # Cancel any pending expand
        item = self.HitTest((x, y))[0]
        if self.__onDropURLCallback:
            self.__onDropURLCallback(self._objectBelongingTo(item), url)

    def onDropFiles(self, x, y, filenames):
        self._clearDropHighlight()  # Clear highlight on drop
        self.__stopHoverExpandTimer()  # Cancel any pending expand
        item = self.HitTest((x, y))[0]
        if self.__onDropFilesCallback:
            self.__onDropFilesCallback(
                self._objectBelongingTo(item), filenames
            )

    def onDropMail(self, x, y, mail):
        self._clearDropHighlight()  # Clear highlight on drop
        self.__stopHoverExpandTimer()  # Cancel any pending expand
        item = self.HitTest((x, y))[0]
        if self.__onDropMailCallback:
            self.__onDropMailCallback(self._objectBelongingTo(item), mail)

    def onDragOver(self, x, y, defaultResult):
        item, flags = self.HitTest((x, y))[:2]
        if self._itemIsOk(item):
            # if flags & wx.TREE_HITTEST_ONITEMBUTTON:
            #     self.Expand(item)
            # Auto-expand collapsed items on hover (modern UX behavior)
            self.__handleHoverExpand(item, flags)
            # Highlight the row being hovered over
            self._setDropHighlight(item)
        else:
            self._clearDropHighlight()
            self.__stopHoverExpandTimer()
        return defaultResult

    def __handleHoverExpand(self, item, flags):
        """Handle auto-expand of collapsed items during drag hover.

        Expands collapsed items after a brief hover delay (500ms) for better UX.
        Immediate expand when hovering directly on the expand button.
        """
        # Immediate expand when on the expand/collapse button
        if flags & wx.TREE_HITTEST_ONITEMBUTTON:
            self.__stopHoverExpandTimer()
            self.Expand(item)
            return

        # Check if item is expandable (has children and is collapsed)
        try:
            isExpandable = self.ItemHasChildren(item) and not self.IsExpanded(
                item
            )
        except (RuntimeError, AttributeError):
            isExpandable = False

        if isExpandable:
            # Start or continue timer for this item
            if item != self.__hoverExpandItem:
                self.__hoverExpandItem = item
                if self.__hoverExpandTimer:
                    self.__hoverExpandTimer.Start(500, oneShot=True)
        else:
            # Not over an expandable item, cancel any pending expand
            self.__stopHoverExpandTimer()

    def __stopHoverExpandTimer(self):
        """Stop the hover-expand timer and clear state."""
        if self.__hoverExpandTimer:
            self.__hoverExpandTimer.Stop()
        self.__hoverExpandItem = None

    def __onHoverExpandTimer(self, event):
        """Timer fired - expand the hovered item."""
        if self.__hoverExpandItem:
            try:
                if self.ItemHasChildren(
                    self.__hoverExpandItem
                ) and not self.IsExpanded(self.__hoverExpandItem):
                    self.Expand(self.__hoverExpandItem)
            except (RuntimeError, AttributeError):
                pass  # Item may have been deleted
        self.__hoverExpandItem = None

    def _setDropHighlight(self, item):
        """Set visual highlight on item during drag-over."""
        if item != self.__dropHighlightItem:
            self.__dropHighlightItem = item
            # Use SetDragItem which is used by internal DnD for highlighting
            if hasattr(self, "SetDragItem"):
                self.SetDragItem(item)

    def _clearDropHighlight(self):
        """Clear any existing drop highlight."""
        if self.__dropHighlightItem is not None:
            self.__dropHighlightItem = None
            if hasattr(self, "SetDragItem"):
                try:
                    self.SetDragItem(None)
                except Exception:
                    pass  # Item may have been deleted

    def GetMainWindow(self):
        try:
            return super().GetMainWindow()
        except AttributeError:
            # return self
            return (
                self.GetCustomTreeCtrlInstance()
            )  # Retourner une instance de CustomTreeCtrl

    def GetCustomTreeCtrlInstance(self):
        # Retourner une instance de CustomTreeCtrl, par exemple :
        return self.parent.GetTreeCtrl()


class CtrlWithToolTipMixin(_CtrlWithItemsMixin, tooltip.ToolTipMixin):
    """Contrôle qui a une info-bulle différente pour chaque élément."""

    def __init__(self, *args, **kwargs):
        log.debug(
            "CtrlWithToolTipMixin.__init__ : initialise le contrôle qui a une info-bulle différente pour chaque élément."
        )
        super().__init__(*args, **kwargs)
        self.__tip = tooltip.SimpleToolTip(self)
        log.debug("CtrlWithToolTipMixin initialisé !")

    def OnBeforeShowToolTip(self, x, y):
        item, _, column = self.HitTest(wx.Point(x, y))
        domainObject = self._objectBelongingTo(item)
        if domainObject:
            tooltipData = self.getItemTooltipData(domainObject)
            doShow = any([data[1] for data in tooltipData])
            if doShow:
                self.__tip.SetData(tooltipData)
                return self.__tip
        return None


class CtrlWithItemsMixin(
    _CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin
):
    pass


class Column(object):
    def __init__(self, name, columnHeader, *eventTypes, **kwargs):
        self.__name = name
        self.__columnHeader = columnHeader
        # self.width = kwargs.pop(
        #     "width", hypertreelist._DEFAULT_COL_WIDTH
        # )  # pylint: disable=W0212 Access to a protected member _DEFAULT_COL_WIDTH of a module
        self.width = kwargs.pop("width", 100)
        # The event types to use for registering an observer that is
        # interested in changes that affect this column:
        self.__eventTypes = eventTypes
        self.__sortCallback = kwargs.pop("sortCallback", None)
        self.__renderCallback = kwargs.pop(
            "renderCallback", self.defaultRenderer
        )
        self.__resizeCallback = kwargs.pop("resizeCallback", None)
        self.__alignment = kwargs.pop("alignment", wx.LIST_FORMAT_LEFT)
        self.__hasImages = "imageIndicesCallback" in kwargs
        self.__imageIndicesCallback = (
            kwargs.pop("imageIndicesCallback", self.defaultImageIndices)
            or self.defaultImageIndices
        )
        # NB: because the header image is needed for sorting a fixed header
        # image cannot be combined with a sortable column
        self.__headerImageIndex = kwargs.pop("headerImageIndex", -1)
        self.__editCallback = kwargs.get("editCallback", None)
        self.__editControlClass = kwargs.get("editControl", None)
        self.__parse = kwargs.get("parse", lambda value: value)
        self.__settings = kwargs.get(
            "settings", None
        )  # FIXME: Column shouldn't need to know about settings
        # La colonne ne devrait pas avoir besoin de connaître les paramètres.

    def name(self):
        return self.__name

    def header(self):
        return self.__columnHeader

    def headerImageIndex(self):
        return self.__headerImageIndex

    def eventTypes(self):
        return self.__eventTypes

    def setWidth(self, width):
        self.width = width
        if self.__resizeCallback:
            self.__resizeCallback(self, width)

    def sort(self, *args, **kwargs):
        if self.__sortCallback:
            self.__sortCallback(*args, **kwargs)

    def __filterArgs(self, func, kwargs):
        # actualKwargs = dict()  # Jamais utilisé !
        argNames = inspect.getfullargspec(func).args
        return dict(
            [
                (name, value)
                for name, value in list(kwargs.items())
                if name in argNames
            ]
        )

    def render(self, *args, **kwargs):
        return self.__renderCallback(
            *args, **self.__filterArgs(self.__renderCallback, kwargs)
        )

    def defaultRenderer(self, *args, **kwargs):  # pylint: disable=W0613
        return str(args[0])

    def alignment(self):
        return self.__alignment

    def defaultImageIndices(self, *args, **kwargs):  # pylint: disable=W0613
        return {wx.TreeItemIcon_Normal: -1}

    def imageIndices(self, *args, **kwargs):
        return self.__imageIndicesCallback(*args, **kwargs)

    def hasImages(self):
        return self.__hasImages

    def isEditable(self):
        return (
            self.__editControlClass is not None
            and self.__editCallback is not None
        )

    def onEndEdit(self, item, newValue):
        self.__editCallback(item, newValue)

    def editControl(self, parent, item, columnIndex, domainObject):
        value = self.value(domainObject)
        kwargs = dict(settings=self.__settings) if self.__settings else dict()
        # pylint: disable=W0142
        return self.__editControlClass(
            parent, wx.ID_ANY, item, columnIndex, parent, value, **kwargs
        )

    def parse(self, value):
        return self.__parse(value)

    def value(self, domainObject):
        """Récupère la valeur de la colonne pour un objet métier donné.

        Par défaut appelle l'attribut/méthode nommée comme la colonne sur domainObject.
        """
        return getattr(domainObject, self.name())()

    def __eq__(self, other):
        return self.name() == other.name()

    # # TODO : Faut-il ajouter une méthode __hash__ pour que les instances de Column soient hashables ?
    # # Cela pourrait être nécessaire si nous voulons les utiliser comme clés
    # # dans des dictionnaires ou les stocker dans des ensembles. Par exemple :
    # def __hash__(self):
    #     return hash(self.name())


class _BaseCtrlWithColumnsMixin(object):
    """Une classe de base pour tous les contrôles avec des colonnes. Notez que cette classe et
    ses sous-classes ne prennent pas en charge l'ajout ou la suppression de colonnes après
    le paramètre initial des colonnes."""

    def __init__(self, *args, **kwargs):
        log.debug(
            "_BaseCtrlWithColumnsMixin.__init__ : initialisation de tous les contrôles avec des colonnes."
        )
        self.__allColumns = kwargs.pop("columns")
        super().__init__(*args, **kwargs)
        # Ceci est utilisé pour garder une trace de quelle colonne a quel
        # index. La seule autre façon serait (et était) de trouver une colonne
        # en utilisant son en-tête, ce qui pose des problèmes lorsque plusieurs colonnes
        # ont le même en-tête. C'est une liste de tuples (index, colonne).
        self.__indexMap = []
        self._setColumns()
        log.debug(
            "_BaseCtrlWithColumnsMixin initialisé avec les colonnes : %s",
            self.__allColumns,
        )

    def _setColumns(self):
        for columnIndex, column in enumerate(self.__allColumns):
            self._insertColumn(columnIndex, column)

    def _insertColumn(self, columnIndex, column):
        newMap = []
        for colIndex, col in self.__indexMap:
            if colIndex >= columnIndex:
                newMap.append((colIndex + 1, col))
            else:
                newMap.append((colIndex, col))
        newMap.append((columnIndex, column))
        self.__indexMap = newMap

        self.InsertColumn(
            columnIndex,
            column.header() if column.headerImageIndex() == -1 else "",
            format=column.alignment(),
            width=column.width,
        )

        columnInfo = self.GetColumn(columnIndex)
        columnInfo.SetImage(column.headerImageIndex())
        self.SetColumn(columnIndex, columnInfo)

    def _deleteColumn(self, columnIndex):
        newMap = []
        for colIndex, col in self.__indexMap:
            if colIndex > columnIndex:
                newMap.append((colIndex - 1, col))
            elif colIndex < columnIndex:
                newMap.append((colIndex, col))
        self.__indexMap = newMap
        self.DeleteColumn(columnIndex)

    def _allColumns(self):
        return self.__allColumns

    def _getColumn(self, columnIndex):
        for colIndex, col in self.__indexMap:
            if colIndex == columnIndex:
                return col
        raise IndexError

    def _getColumnHeader(self, columnIndex):
        """En-tête de colonne actuellement affiché dans la colonne avec index
        columnIndex."""
        return self.GetColumn(columnIndex).GetText()

    def _getColumnIndex(self, column):
        """L'index de colonne actuel de la colonne 'colonne'."""
        try:
            return self.__allColumns.index(column)  # Uses overriden __eq__
        except ValueError:
            # raise ValueError("%s: unknown column" % column.name())
            raise ValueError(f"{column.name()}: unknown column")


class _CtrlWithHideableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Prend en charge le masquage et l'affichage des colonnes.

    Méthodes principales :
        - `showColumn` : Affiche ou masque une colonne.
        - `isColumnVisible` : Vérifie si une colonne est visible.
    """

    def showColumn(self, column, show=True):
        # def showColumn(self, column_name: str, show: bool = True):
        """
        Affiche ou masque une colonne.

        showColumn affiche ou masque la colonne de la colonne.
        La colonne est en fait supprimée ou insérée dans le contrôle car
        bien que TreeListCtrl prenne en charge le masquage des colonnes,
        ListCtrl ne le fait pas.

        Args :
        column (Column) : La colonne à afficher ou masquer.
        show (bool) : Si `True`, affiche la colonne. Sinon, la masque.
        """
        # visible = list(self['displaycolumns'])

        columnIndex = self._getColumnIndex(column)
        if show and not self.isColumnVisible(column):
            # if show and column_name not in visible:
            self._insertColumn(columnIndex, column)
            # visible.append(column_name)
            # visible.sort(key=lambda x: [c.name() for c in self._columns].index(x))
        elif not show and self.isColumnVisible(column):
            # elif not show and column_name in visible:
            self._deleteColumn(columnIndex)
            # visible.remove(column_name)

        # self['displaycolumns'] = visible

    def isColumnVisible(self, column):
        return column in self._visibleColumns()

    def _getColumnIndex(self, column):
        """_getColumnIndex renvoie le columnIndex réel de la colonne si elle
        est visible, ou la position qu'elle aurait si elle était visible."""
        log.debug(
            f"_CtrlWithHideableColumnsMixin._getColumnIndex : appelé par {self.__class__.__name__} avec column ={column}"
        )
        columnIndexWhenAllColumnsVisible = super()._getColumnIndex(column)
        for columnIndex, visibleColumn in enumerate(self._visibleColumns()):
            if (
                super()._getColumnIndex(visibleColumn)
                >= columnIndexWhenAllColumnsVisible
            ):
                log.debug(
                    f"_CtrlWithHideableColumnsMixin._getColumnIndex : renvoie l'index {columnIndex} de la colonne {column.name()} visible si toutes les colonnes sont visibles."
                )
                return columnIndex
        # log.debug(
        #     f"_CtrlWithHideableColumnsMixin._getColumnIndex : renvoie l'index {self.GetColumnCount()} de la colonne {column} !"
        # )
        log.debug(
            f"_CtrlWithHideableColumnsMixin._getColumnIndex : la colonne {column.name()} n'est pas visible, renvoie l'index {self._getColumnIndex(column)} !"
        )
        return self.GetColumnCount()  # Column header not found

    def _visibleColumns(self):
        return [
            self._getColumn(columnIndex)
            for columnIndex in range(self.GetColumnCount())
        ]


class _CtrlWithSortableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """Cette classe ajoute des indicateurs de tri et des en-têtes de colonnes cliquables qui
    déclenchent des rappels pour (re)trier le contenu du contrôle."""

    def __init__(self, *args, **kwargs):
        log.debug(
            "_CtrlWithSortableColumnsMixin.__init__ : Initialisation des ajouts des indicateurs de tri."
        )
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.onColumnClick)
        self.__currentSortColumn = self._getColumn(0)
        self.__currentSortImageIndex = -1
        log.debug(
            "_CtrlWithSortableColumnsMixin initialisé ! Ajout des indicateurs de tri !"
        )

    def onColumnClick(self, event):
        event.Skip(False)
        # Assurez-vous que la fenêtre dans laquelle se trouve ce contrôle a le focus :
        try:
            window = event.GetEventObject().GetMainWindow()
        except AttributeError:
            window = event.GetEventObject()
        window.SetFocus()
        columnIndex = event.GetColumn()
        if 0 <= columnIndex < self.GetColumnCount():
            column = self._getColumn(columnIndex)
            # Utilisez CallAfter pour vous assurer que la fenêtre dans laquelle se trouve ce contrôle est
            # activée avant de traiter le clic sur la colonne :
            # wx.CallAfter(column.sort, event)
            wx.CallAfter(self.__safeColumnSort, column, event)

    def __safeColumnSort(self, column, event):
        """Safely call column.sort, guarding against deleted C++ objects."""
        try:
            if self:
                column.sort(event)
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def showSortColumn(self, column):
        if column != self.__currentSortColumn:
            self._clearSortImage()
        self.__currentSortColumn = column
        self._showSortImage()

    def showSortOrder(self, imageIndex):
        """Affiche l'ordre de tri actuel dans la visionneuse."""
        self.__currentSortImageIndex = imageIndex
        self._showSortImage()

    def _clearSortImage(self):
        self.__setSortColumnImage(-1)

    def _showSortImage(self):
        self.__setSortColumnImage(self.__currentSortImageIndex)

    def _currentSortColumn(self):
        return self.__currentSortColumn

    def __setSortColumnImage(self, imageIndex):
        columnIndex = self._getColumnIndex(self.__currentSortColumn)
        columnInfo = self.GetColumn(columnIndex)
        if columnInfo.GetImage() == imageIndex:
            pass  # The column is already showing the right image, so we're done
        else:
            columnInfo.SetImage(imageIndex)
            self.SetColumn(columnIndex, columnInfo)


class _CtrlWithAutoResizedColumnsMixin(autowidth.AutoColumnWidthMixin):
    """
    Classe de contrôle avec redimensionnement automatique des colonnes.
    """

    def __init__(self, *args, **kwargs):
        log.debug(
            "_CtrlWithAutoResizedColumnsMixin.__init__ : initialisation."
        )
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.onEndColumnResize)
        log.debug("_CtrlWithAutoResizedColumnsMixin initialisé !")

    def onEndColumnResize(self, event):
        """Enregistrer les largeurs de colonne après que l'utilisateur a fait un redimensionnement."""
        for index, column in enumerate(self._visibleColumns()):
            column.setWidth(self.GetColumnWidth(index))
        event.Skip()


class CtrlWithColumnsMixin(
    _CtrlWithAutoResizedColumnsMixin,
    _CtrlWithHideableColumnsMixin,
    _CtrlWithSortableColumnsMixin,
    _CtrlWithColumnPopupMenuMixin,
):
    """Combine toutes les fonctionnalités de ses quatre classes parents
    pour les contrôles avec colonnes. :
    - Redimensionnement automatique des colonnes.
    - Colonnes masquables.
    - Colonnes avec tri et indicateurs de tri.
    - Menu contextuel pour les colonnes.
    """

    # GESTION DES COLONNES ET TRI
    def showColumn(self, column, show=True):
        # def showColumn(self, column_name: str, show: bool = True):
        """Affiche ou cache une colonne."""
        # méthode dans _CtrlWithHideableColumnsMixin
        super().showColumn(column, show)
        # Afficher l'indicateur de tri si la colonne
        # qui vient d'être rendue visible est en cours de tri.
        if show and column == self._currentSortColumn():
            self._showSortImage()

    def _clearSortImage(self):
        """Effacer l'image de tri si la colonne en question est visible."""
        if self.isColumnVisible(self._currentSortColumn()):
            super()._clearSortImage()

    def _showSortImage(self):
        """Affichez uniquement l'image de tri si la colonne en question est visible."""
        if self.isColumnVisible(self._currentSortColumn()):
            super()._showSortImage()
