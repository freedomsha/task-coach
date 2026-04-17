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

Design note — comportements wx/AGW et contournements
Ce module contient plusieurs contournements (workarounds) destinés
à pallier des comportements spécifiques de wxPython/AGW (HyperTreeList / CustomTreeCtrl), notamment :
    - recalcul des scrollbars après redimensionnement (Windows / AUI panes),
    - gestion de la racine interne quand wx.TR_HIDE_ROOT est utilisé,
    - coalescing / scheduling des rafraîchissements pour éviter des rebuilds redondants.
      Les méthodes scheduleRefresh, forceRefresh et RefreshAllItems contiennent
    des logiques particulières qui doivent être conservées ou mises à jour avec soin.
"""

# from builtins import range
from taskcoachlib import operating_system
import logging
import wx
from wx.lib.agw import customtreectrl as customtree
from wx.lib.agw import hypertreelist
from wx.lib.agw.ultimatelistctrl import (
    UltimateListCtrl,
    UltimateListMainWindow,
)

# from wx.dataview import TreeListCtrl
from taskcoachlib.widgets import itemctrl, draganddrop

log = logging.getLogger(__name__)


# class BaseHyperTreeList(
#     hypertreelist.HyperTreeList, customtree.CustomTreeCtrl
# ):
class BaseHyperTreeList(hypertreelist.HyperTreeList):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,  # HyperTreeList n'utilise pas d'ID, mais wx.ID_ANY est nécessaire pour l'appel au constructeur de la classe parente.
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=0,
        agwStyle=wx.TR_DEFAULT_STYLE,
        validator=wx.DefaultValidator,
        name="HyperTreeList",
        *args,
        **kwargs,
    ):
        super().__init__(
            parent, id, pos, size, style, agwStyle, validator, name
        )
        # Bind our own size handler to fix scrollbar issues on Windows.
        # The base HyperTreeList.OnSize only calls DoHeaderLayout() which
        # repositions child windows but doesn't recalculate scrollbars.
        self.Bind(wx.EVT_SIZE, self.__onSize)

    def __onSize(self, event):
        """Handle size events to ensure scrollbars are recalculated.

        On Windows, side-docked AUI panes don't get scrollbars when the content
        exceeds the visible area because HyperTreeList's OnSize handler only
        repositions child windows without recalculating scrollbars. We fix this
        by calling AdjustMyScrollbars() after the base OnSize handler runs.
        """
        event.Skip()  # Let base class handle layout first
        # Il faut décommenter ce qui suit et l'adapter:
        # # Si on a des items à afficher mais que l'arbre est vide, rafraîchir
        # if self.__adapter and len(list(self.__adapter.presentation())) > 0:
        #     wx.CallAfter(self.__doRefresh)
        # Mais attention — il ne faut pas appeler self.__doRefresh (qui n'existe plus),
        # mais self.scheduleRefresh.
        # Et il faut contourner le flag __refresh_scheduled en le réinitialisant d'abord.
        # Voici la correction :
        # Forcer un refresh si le widget a des données à afficher
        # (cas du redimensionnement après initialisation en petite taille)
        # # if self.__adapter and len(list(self.__adapter.presentation())) > 0:
        if (
            hasattr(self, "_TreeListCtrl__adapter")
            and self._TreeListCtrl__adapter
            and len(list(self._TreeListCtrl__adapter.presentation())) > 0
        ):
            # adapter = self.getAdapter() if hasattr(self, 'getAdapter') else None
            # if adapter and len(list(adapter.presentation())) > 0:
            log.debug(
                f"BaseHyperTreeList.__onSize : force le rafraîchissement."
            )
            # # self.__refresh_scheduled = (
            # #     False  # réinitialiser le flag (!!! nom manglé !!!)
            # # )
            # # Réinitialiser le flag pour forcer le refresh
            # if hasattr(self, "_TreeListCtrl__refresh_scheduled"):
            #     self._TreeListCtrl__refresh_scheduled = False
            # self.scheduleRefresh()
            # Remplacé par la ligne suivante :
            self.forceRefresh()  # Le flag bloquait le rafraîchissement !
        # Schedule scrollbar adjustment after the layout is complete
        wx.CallAfter(self.__safeAdjustScrollbars)

    def __safeAdjustScrollbars(self):
        """Safely adjust scrollbars, guarding against deleted C++ objects."""
        try:
            main_win = self.GetMainWindow()
            if main_win:
                main_win.AdjustMyScrollbars()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass


# class HyperTreeList(BaseHyperTreeList, draganddrop.TreeCtrlDragAndDropMixin):
class HyperTreeList(draganddrop.TreeCtrlDragAndDropMixin, BaseHyperTreeList):
    def __init__(self, *args, **kwargs):
        log.debug("HyperTreeList.__init__ : initialisation d'HyperTreeList.")
        self._editCtrl = None  # nouvel attribut pour TreeListCtrl
        super().__init__(*args, **kwargs)
        BaseHyperTreeList.__init__(self, *args, **kwargs)
        if operating_system.isGTK():
            self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.__on_item_collapsed)

    def __on_item_collapsed(self, event):
        event.Skip()
        # On Ubuntu, when the user has scrolled to the bottom of the tree
        # and collapses an item, the tree is not redrawn correctly. Refreshing
        # solves this. See http://trac.wxwidgets.org/ticket/11704
        # wx.CallAfter(self.MainWindow.Refresh)
        wx.CallAfter(self.__safeRefresh)

    def __safeRefresh(self):
        """Safely refresh the main window, guarding against deleted C++ objects."""
        try:
            if self.MainWindow:
                self.MainWindow.Refresh()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def GetSelections(self):  # pylint: disable=C0103
        """
        Si l'élément racine est masqué, il ne doit jamais être sélectionné.
        Malheureusement, CustomTreeCtrl et HyperTreeList permettent de le sélectionner.
        Remplacez GetSelections pour résoudre ce problème.
        """
        # Obtenez la sélection de la classe parente, puis filtrez-la si TR_HIDE_ROOT est défini.
        selections = super().GetSelections()
        log.debug(
            f"HyperTreeList.GetSelections : selections avant filtrage={selections}"
        )
        if self.HasFlag(wx.TR_HIDE_ROOT):
            log.debug(
                "HyperTreeList.GetSelections : TR_HIDE_ROOT est défini, filtrage de la sélection pour exclure la racine."
            )
            root_item = self.GetRootItem()
            # return self.widget.curselection()
            # Si root_item est dans la sélection, on le retire. Notez que GetRootItem() peut retourner un TreeItemId invalide (mais pas None), donc vérifiez sa validité avant de l'utiliser.
            log.debug(f"HyperTreeList.GetSelections : root_item={root_item}.")
            if root_item and root_item in selections:
                selections.remove(root_item)
        log.debug(
            f"HyperTreeList.GetSelections : retourne {selections} après avoir filtré la sélection."
        )
        return selections

    def GetMainWindow(self, *args, **kwargs):  # pylint: disable=C0103
        """
        Avoir un GetMainWindow local afin que nous puissions créer une propriété MainWindow.
        """
        return super().GetMainWindow(
            *args, **kwargs
        )  # *args et **kwargs semblent inutiles ici !
        # return (
        #     super().GetMainWindow()
        # )  # *args et **kwargs semblent inutiles ici !

    MainWindow = property(fget=GetMainWindow)

    def HitTest(self, point, flags=0):  # pylint: disable=W0221, C0103
        """Renvoie toujours un triple-tuple (item, flags, column)."""
        # if type(point) == type(()):  # isinstance (tuple ?)
        if type(point) is type(()):  # isinstance (tuple ?)
            point = wx.Point(point[0], point[1])
        hit_test_result = super().HitTest(point)
        if len(hit_test_result) == 2:
            hit_test_result += (0,)
        if hit_test_result[0] is None:
            hit_test_result = (wx.TreeItemId(),) + hit_test_result[1:]
        return hit_test_result

    def isClickablePartOfNodeClicked(self, event):
        """
        Indique si l'utilisateur a double-cliqué sur une partie du nœud qui
        peut également recevoir des clics de souris réguliers.
        """
        return self.__is_collapse_expand_button_clicked(event)

    def __is_collapse_expand_button_clicked(self, event):
        flags = self.HitTest(event.GetPosition())[1]
        # return flags & wx.TREE_HITTEST_ONITEMBUTTON  # Class 'TreeItemId' does not define '__and__', so the '&' operator cannot be used on its instances
        if not isinstance(flags, int):
            flags = int(flags)
        return bool(flags & wx.TREE_HITTEST_ONITEMBUTTON)

    def select(self, selection):
        """Select items whose PyData is in the selection list.
        Returns the first selected tree item (for scrolling).

        Note: UnselectAll() is required before SelectItem() after a tree rebuild.
        This appears to be a HyperTreeList quirk/bug - SelectItem() silently fails
        without it, even though DoSelectItem has unselect_others=True by default.
        See: https://github.com/wxWidgets/Phoenix/issues/1164 for related issues.
        """
        first_selected_item = None
        self.UnselectAll()
        for item in self.GetItemChildren(recursively=True):
            # self.SelectItem(item, self.GetItemPyData(item) in selection)
            pydata = self.GetItemPyData(item)
            if pydata in selection:
                self.SelectItem(item, True)
                if first_selected_item is None:
                    first_selected_item = item
        return first_selected_item

    def clear_selection(self):
        self.UnselectAll()
        self.selectCommand()

    def select_all(self):
        if self.GetItemCount() > 0:
            self.SelectAll()
        self.selectCommand()

    def isAnyItemCollapsable(self):
        for item in self.GetItemChildren():
            if self.__is_item_collapsable(item):
                return True
        return False

    def isAnyItemExpandable(self):
        for item in self.GetItemChildren():
            if self.__is_item_expandable(item):
                return True
        return False

    def __is_item_expandable(self, item):
        return self.ItemHasChildren(item) and not self.IsExpanded(item)

    def __is_item_collapsable(self, item):
        return self.ItemHasChildren(item) and self.IsExpanded(item)

    def IsLabelBeingEdited(self):
        # # return bool(self.GetLabelTextCtrl())
        # # # Ancien code
        return bool(self._editCtrl)
        # return (
        #     self.GetMainWindow().IsEditing()
        # )  # Méthode officielle de wxPython Phoenix pour vérifier si un label est en cours d'édition
        # Sauf que AttributeError: 'TreeListMainWindow' object has no attribute 'IsEditing'
        # Cela suggère que la classe TreeListMainWindow utilisée par HyperTreeList n'a pas de méthode IsEditing, ce qui est surprenant car c'est une méthode standard pour les contrôles d'édition de labels dans wxPython Phoenix. Vérifiez la documentation de wxPython Phoenix et la classe TreeListMainWindow pour voir si IsEditing est disponible ou si une autre méthode doit être utilisée pour vérifier l'état d'édition des labels.

    def StopEditing(self):
        if self.IsLabelBeingEdited():
            # self.GetLabelTextCtrl().StopEditing()
            self.GetMainWindow().CancelEdit()

    def GetLabelTextCtrl(self):
        # # return self.GetMainWindow()._editCtrl  # pylint: disable=W0212
        # return (
        #     self._editCtrl
        # )  # pylint: disable=W0212 AttributeError: 'TreeListCtrl' object has no attribute '_editCtrl'
        # # if self.GetMainWindow().IsEditing():
        # #     return self.GetEditControl()  # Méthode wxPython Phoenix
        # # return None
        #
        # # Vérifiez la définition de la classe MainWindow pour voir si _Editctrl
        # # est initialisé. S'il est censé être un widget pour l'édition,
        # # assurez-vous qu'il est correctement créé et affecté à la variable d'instance.
        # # S'il n'est pas censé exister, ajustez la méthode getLabelTextCtrl
        # # pour ne pas le référencer ou gérer son absence potentielle.
        # # TODO : _editCtrl est un attribut interne de wxPython Classic.
        # # Dans wxPython Phoenix (4.x), l'édition des labels est gérée via des événements et des méthodes publiques.
        # # Remplace l'accès à _editCtrl par l'API officielle.
        if self.IsLabelBeingEdited():
            return self.GetMainWindow().GetEditControl()
        return None

    def GetItemCount(self):
        """Retourne le nombre total d'items dans l'arbre, en excluant la racine si elle est masquée."""
        root_item = self.GetRootItem()
        # return (
        #     self.GetChildrenCount(root_item, recursively=True)
        #     if root_item
        #     else 0
        # )
        nb_of_item = (
            self.GetChildrenCount(root_item, recursively=True)
            if root_item
            else 0
        )
        log.debug(
            f"HyperTreeList.GetItemCount : root_item={root_item}, retourne nb_of_item={nb_of_item}"
        )
        return nb_of_item


class TreeListCtrl(
    itemctrl.CtrlWithItemsMixin,
    itemctrl.CtrlWithColumnsMixin,
    itemctrl.CtrlWithToolTipMixin,
    HyperTreeList,
):
    # itemctrl.CtrlWithToolTipMixin, HyperTreeList, UltimateListCtrl, hypertreelist.TreeListMainWindow):  TODO
    """
    Contrôle de liste en arbre qui affiche les éléments fournis par un adaptateur
    (souvent appelé « viewer » dans le projet) dans une structure hiérarchique.

    Note de conception - API attendue de l'adaptateur
    -----------------------------------------------
    Le widget s'attend à ce que l'adaptateur (stocké dans
    `self.__adapter`) fournisse au minimum les méthodes suivantes :

    - children(parent_object) -> iterable
        Retourne les objets enfants pour `parent_object` (None pour la racine).
    - getItemText(domain_object, column_index=0) -> str
        Retourne le texte à afficher pour `domain_object` dans la colonne.
    - getItemImages(domain_object, column_index) -> dict
        Retourne un mapping {which: image_index} pour les images à afficher.
    - getItemExpanded(domain_object) -> bool
        Indique si l'objet doit être affiché développé par défaut.
    - getIsItemChecked(domain_object) -> bool|None
        Pour les arbres cochables : True/False/None (mixed).
    - getItemParentHasExclusiveChildren(domain_object) -> bool
        Indique si les enfants sont mutuellement exclusifs (radio).
    - domainObjectsToView() -> iterable
        Retourne l'ensemble d'objets racines visibles (utilisé pour debug/compteurs).
    - presentation() -> iterable
        (optionnel) présentation plate des objets, utilisée par certains handlers.
    - getItemTooltipData(domain_object) -> list
        Données pour les info-bulles spécifiques à chaque élément.
    - isTreeViewer() -> bool
        Indique si la vue est réellement arborescente (utilisé pour décider de la récursivité).
    - hasColumnImages(index) -> bool
        Indique si une colonne peut contenir des images.

    Comportement important
    - Le widget peut recréer entièrement l'arbre via `RefreshAllItems()` ce qui
      appelle `DeleteAllItems()` suivi d'un `AddRoot()` ; le code doit donc
      considérer que les TreeItemId peuvent devenir invalides après un rebuild.
    - Le style AGW `wx.TR_HIDE_ROOT` est supporté : la racine interne est créée
      mais cachée ; les enfants doivent rester visibles même quand la racine est
      masquée.

    Ce docstring sert de contrat minimal ; si un adaptateur n'implémente pas
    ces méthodes, le widget risque des erreurs ou un affichage incomplet.

    Exemple d’adaptateur minimal attendu (pseudo-code) class ExampleAdapter:
    def children(self, parent_object):
        # return iterable of children; None => root
    def getItemText(self, domain_object, column_index=0):
        # return str
    def getItemImages(self, domain_object, column_index):
        # return {which: image_index}
    def getItemExpanded(self, domain_object):
        # return bool
    def getIsItemChecked(self, domain_object):
        # return True/False/None
    def getItemParentHasExclusiveChildren(self, domain_object):
        # return bool
    def domainObjectsToView(self):
        # return iterable of domain root objects
    def isTreeViewer(self):
        # return bool
    """
    # TreeListCtrl uses ALIGN_LEFT, ..., ListCtrl uses LIST_FORMAT_LEFT, ... for
    # specifying alignment of columns. This dictionary allows us to map from the
    # ListCtrl constants to the TreeListCtrl constants:
    alignmentMap = {
        wx.LIST_FORMAT_LEFT: wx.ALIGN_LEFT,
        wx.LIST_FORMAT_CENTRE: wx.ALIGN_CENTRE,
        wx.LIST_FORMAT_CENTER: wx.ALIGN_CENTER,
        wx.LIST_FORMAT_RIGHT: wx.ALIGN_RIGHT,
    }
    ct_type = 0

    def __init__(
        self,
        parent,
        columns,
        selectCommand,
        editCommand,
        dragAndDropCommand,
        itemPopupMenu=None,
        columnPopupMenu=None,
        *args,
        **kwargs,
    ):
        """
        Initialisation du contrôle de liste en arbre.

        Args:
            parent: La fenêtre parente pour le contrôle de liste en arbre.
            columns: Le nombre de colonnes dans le contrôle.
            selectCommand: La commande à exécuter lors de la sélection d'un élément.
            editCommand: La commande à exécuter lors de l'édition d'un élément.
            dragAndDropCommand: La commande à exécuter lors d'une opération de glisser-déposer.
            itemPopupMenu: Le menu contextuel à afficher pour les éléments (optionnel).
            columnPopupMenu: Le menu contextuel à afficher pour les en-têtes de colonnes (optionnel).
            *args: Les arguments supplémentaires à passer au constructeur de la classe parente.
            **kwargs: Les arguments nommés supplémentaires à passer au constructeur de la classe parente.
        """
        log.debug(
            "TreeListCtrl.__init__ : initialisation du contrôle de liste en arbre."
        )
        # Fenêtre principale pour la gestion du focus avec AuiManager
        self.__adapter = parent  # L'adaptateur qui fournit les données et les comportements pour le TreeListCtrl
        log.debug(
            f"TreeListCtrl.__init__ : parent={parent}, self.__adapter={self.__adapter}, ADAPTER TYPE: {type(self.__adapter)}"
        )
        # TODO : essayez de remplacer parent par l'appel direct à la fenêtre principale, soit
        # Liste des objets actuellement sélectionnés
        self.__selection = []
        # Information sur le double-clic de l'utilisateur
        self.__user_double_clicked = False
        # Liste des colonnes qui peuvent contenir des images
        self.__columns_with_images = []
        # Police par défaut
        self.__default_font = wx.NORMAL_FONT
        # On ne refresh PAS immédiatement.
        #
        # On planifie un refresh unique via wx.CallAfter
        # et on empêche toute replanification tant qu’il n’est pas exécuté.
        self.__refresh_scheduled = False
        self.__refreshing = (
            False  # Flag to suppress selection events during refresh
        )
        # ajout d'attribut :
        self._editCtrl = None  # Initialise explicitement ici
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        kwargs.setdefault("resizeableColumn", 0)
        self._mainWin = None
        # # self.root_item = self.AddRoot(
        # #     ""
        # # )  # Ajouter une racine vide pour éviter les problèmes de GetRootItem() qui retourne un item invalide. L'item racine est nécessaire pour que les autres éléments soient affichés, même si TR_HIDE_ROOT est défini.
        # # # ça plante ! La racine existe déjà !
        # # Création explicite de la racine de l'arbre.
        # # HyperTreeList ne crée pas toujours une racine valide automatiquement.
        # # Sans racine valide, les éléments ajoutés via AppendItem ne seront jamais visibles.
        # self._root = self.AddRoot("")  # AttributeError: 'TreeListCtrl' object has no attribute '_main_win'
        # # -> self._main_win n'est pas encore défini à ce stade, ce qui suggère que l'appel à AddRoot() dans le constructeur de TreeListCtrl se produit avant que l'initialisation de la classe parente HyperTreeList ne soit terminée. Cela peut entraîner des problèmes si HyperTreeList dépend de certains attributs ou méthodes qui ne sont pas encore disponibles lors de l'appel à AddRoot().
        # # Il faut créer la racine après l'appel à super().__init__() pour s'assurer que tous les attributs et méthodes nécessaires sont disponibles. Cependant, cela peut poser un problème si HyperTreeList ou CustomTreeCtrl attendent que la racine soit créée avant de terminer leur propre initialisation. Il est important de vérifier l'ordre d'initialisation des classes parente et de s'assurer que la création de la racine se fait au bon moment dans le cycle de vie du widget.
        #
        # # On s'assure que la racine est bien visible et développée.
        # # Cela permet de voir immédiatement les enfants ajoutés.
        # self.Expand(self._root)
        #
        # # Journalisation pour vérifier que la racine existe correctement.
        # log.debug(
        #     "TreeListCtrl.__init__ : racine créée explicitement : %s (IsOk=%s)",
        #     self._root,
        #     self._root.IsOk(),
        # )
        log.debug("TreeListCtrl.__init__ : avant super().")
        super().__init__(
            parent,
            style=self.__get_style(),
            agwStyle=self.__get_agw_style(),
            columns=columns,
            itemPopupMenu=itemPopupMenu,
            columnPopupMenu=columnPopupMenu,
            *args,
            **kwargs,
        )
        log.debug("TreeListCtrl.__init__ : après super()")
        # if not self.GetRootItem().IsOk():
        #     root = self.AddRoot("ROOT")
        #     log.debug("Racine créée manuellement.")
        # Création explicite de la racine
        if not self.GetRootItem():
            self._root = self.AddRoot("")
            log.debug(
                f"TreeListCtrl.__init__ : racine créée manuellement : {self._root}"
            )
        else:
            self._root = self.GetRootItem()
            log.debug(
                f"TreeListCtrl.__init__ : racine obtenue avec GetRootItem() : {self._root}"
            )
        log.debug(
            "TreeListCtrl.__init__ : racine créée : %s (IsOk=%s)",
            self._root,
            self._root.IsOk(),
        )
        # # On s'assure que la racine est bien visible et développée.
        # # Cela permet de voir immédiatement les enfants ajoutés.
        # self.Expand(
        #     self._root
        # )  # Il faut expanser seulement si la racine est visible.
        # On vérifie si la racine est visible avant d'essayer de l'étendre
        style = self.GetWindowStyle()

        # # Si la racine n'est pas cachée
        # # if not (style & wx.TR_HIDE_ROOT):
        # # Ne jamais Expand si la racine est cachée
        # if not (self.GetAGWWindowStyleFlag() & wx.TR_HIDE_ROOT):
        #     # # On peut étendre la racine sans provoquer d'erreur
        #     log.debug(
        #         f"TreeListCtrl.__init__ : la racine est visible, on peut l'étendre."
        #     )
        #     # root_item.Expand()
        #     self.Expand(self._root)  # C'est cette ligne qui provoque l'erreur lorsque la racine est cachée, même si la racine existe et est valide. Expand() ne peut pas être appelé sur un item qui n'est pas visible, même s'il est valide.
        #     log.debug(f"TreeListCtrl.__init__ : racine étendue")
        # # C'est self.Expand(self._root) qui provoquait l'erreur d'affichage des tâches dans la taskviewer.

        # Journalisation pour vérifier que la racine existe correctement.
        log.debug(
            "TreeListCtrl.__init__ : racine créée explicitement : %s (IsOk=%s)",
            self._root,
            self._root.IsOk(),
        )
        self.bindEventHandlers(selectCommand, editCommand, dragAndDropCommand)

    def bindEventHandlers(
        self, selectCommand, editCommand, dragAndDropCommand
    ):
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelect)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onItemActivated)
        # We deal with double clicks ourselves, to prevent the default behaviour
        # of collapsing or expanding nodes on double click.
        self.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.onDoubleClick)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.onItemExpanding)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)

    def onSetFocus(self, event):  # pylint: disable=W0613
        # Envoyez un événement de focus enfant pour informer AuiManager que nous avons reçu le focus
        # afin qu'il active notre volet
        wx.PostEvent(self._main_win, wx.ChildFocusEvent(self._main_win))
        # wx.PostEvent(self, wx.ChildFocusEvent(self))
        self.SetFocus()
        # event.Skip()

    def getItemTooltipData(self, item):
        return self.__adapter.getItemTooltipData(item)

    def getItemCTType(self, item):  # pylint: disable=W0613
        log.debug(
            f"TreeListCtrl.getItemCTTType : retourne self.ct_type : {self.ct_type}."
        )
        return self.ct_type

    def getAdapter(self):
        """
        Retourne l'adaptateur (viewer) associé au contrôle.

        L'adaptateur est responsable de fournir les données et la logique métier
        (attention au contrat décrit dans la docstring de TreeListCtrl).

        Returns:
            L'adaptateur qui fournit les données et les comportements pour le TreeListCtrl.
        """
        return self.__adapter

    def curselection(self):
        """
        Retourne la liste des objets métier correspondant à la sélection courante.

        Renvoie une liste vide si l'objet wx a été détruit
        ou si aucun élément n'est sélectionné.

        Returns:
            list: Une liste d'objets métier correspondant à la sélection courante.
        """
        # return [self.GetItemPyData(item) for item in self.GetSelections()]
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction (e.g., closing nested dialogs)
        try:
            # Filter out None values - GetItemPyData can return None for some items
            # (e.g., root items or items without associated PyData)
            return [
                data
                for item in self.GetSelections()
                if (data := self.GetItemPyData(item)) is not None
            ]
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            return []

    # def RefreshAllItems(self, count=0):  # pylint: disable=W0613
    #     """
    #     Rafraîchit tous les éléments de l'arbre en reconstruisant l'interface
    #     à partir de l'adaptateur.
    #
    #     Reconstruit complètement l'arbre affiché dans le TreeListCtrl.
    #
    #     Cette méthode :
    #     - supprime tous les items existants
    #     - recrée la racine
    #     - reconstruit l'arbre via l'adaptateur
    #     """
    #     # RefreshAllItems() est trop sensible aux notifications.
    #     #
    #     # Il doit être :
    #     # soit coalescé (regrouper les refresh)
    #     # soit différé
    #     # soit protégé contre les appels multiples rapprochés
    #     log.debug(
    #         f"TreeListCtrl.RefreshAllItems : début du rafraîchissement de tous les éléments."
    #     )
    #     # if self.__refreshing:
    #     #     log.debug("Refresh ignoré (déjà en cours)")
    #     #     return
    #     # self.Freeze()
    #     # On gèle le widget pour éviter les scintillements et préparer le Thaw(),
    #     # seulement si ce n'est pas déjà fait
    #     already_frozen = self.IsFrozen()
    #     # if not self.IsFrozen():
    #     if not already_frozen:
    #         self.Freeze()
    #     self.__refreshing = True
    #     try:
    #         self.StopEditing()
    #         # self.__refreshing = True  # Supprime les événements de sélection pendant la reconstruction
    #         self.__selection = self.curselection()
    #         # Logique root ! :
    #         # Supprimer tous les éléments avant de reconstruire. Cela garantit que les éléments obsolètes sont supprimés, même si l'adaptateur ne gère pas correctement les éléments supprimés.
    #         self.DeleteAllItems()  # Dans HyperTreeList (ou CustomTreeCtrl),
    #         # DeleteAllItems supprime tout, AUSSI la racine.
    #         # Donc le root_item obtenu avec self.GetRootItem() est invalide !
    #
    #         self.__columns_with_images = [
    #             index
    #             for index in range(self.GetColumnCount())
    #             if self.__adapter.hasColumnImages(index)
    #         ]
    #
    #         # root_item = (
    #         #     self.GetRootItem()
    #         # )  # Unresolved attribute reference 'GetRootItem' for class 'TreeListCtrl'
    #         root_item = self.AddRoot("")
    #         # # Si GetRootItem() retourne quelque chose, on l'utilise.
    #         root_item.Expand()
    #         # log.debug(
    #         #     f"TreeListCtrl.RefreshAllItems : avec GetRootItem() root_item={root_item}"
    #         # )
    #         log.debug(
    #             f"TreeListCtrl.RefreshAllItems : Nouvelle racine créée : {root_item}"
    #         )
    #         # # Si GetRootItem() retourne un objet invalide (mais pas None ou False),
    #         # # alors if not root_item: est faux, et on utilise cet item invalide pour _addObjectRecursively.
    #         # # Dans wxPython, TreeItemId peut être testé pour la validité avec IsOk().
    #         # # Si GetRootItem() retourne un TreeItemId qui n'est pas Ok,
    #         # # alors if not root_item: pourrait être vrai ou faux selon l'implémentation de __bool__ ou __nonzero__ de TreeItemId.
    #         # if (
    #         #     not root_item or not root_item.IsOk()
    #         # ):  # Vérifie si GetRootItem() a retourné un item valide
    #         #     log.debug(
    #         #         f"TreeListCtrl.RefreshAllItems : root_item n'existe pas ou est invalide, ajout d'une racine."
    #         #     )
    #         #     log.debug("Root invalide → création d'une nouvelle racine")
    #         #     self.DeleteAllItems()
    #         #     # On ajoute une racine.
    #         #     # root_item = self.AddRoot("Hidden root")
    #         #     root_item = self.AddRoot(
    #         #         ""
    #         #     )  # Ajouter une racine vide pour éviter les problèmes de GetRootItem() qui retourne un item invalide. L'item racine est nécessaire pour que les autres éléments soient affichés, même si TR_HIDE_ROOT est défini.
    #         #     log.info(
    #         #         f"TreeListCtrl.RefreshAllItems : root_item créé={root_item}"
    #         #     )
    #         #     log.info("ROOT APRÈS ADD :", root_item.IsOk())
    #         #     log.info(
    #         #         "ROOT APRÈS ADD avec GetRootItem :",
    #         #         self.GetRootItem().IsOk(),
    #         #     )
    #         # else:
    #         #
    #         #     # log.debug(f"TreeListCtrl.RefreshAllItems : root_item existe, suppression de ses enfants.")
    #         #     log.debug(
    #         #         f"TreeListCtrl.RefreshAllItems : root_item est valide, suppression de ses enfants."
    #         #     )
    #         #     # self.DeleteChildren(root_item)  # Est-ce judicieux ?
    #         #     # # Ensure root is expanded, otherwise nothing is shown when TR_HIDE_ROOT is set
    #         #     # self.Expand(root_item)
    #         #     # Ajouter les éléments de l'adaptateur à l'interface, en commençant par la racine.
    #         #     # self._addObjectRecursively(root_item)
    #         log.debug(
    #             f"TreeListCtrl.RefreshAllItems : root_item après vérification={root_item}"
    #         )
    #         # # # Ensure root is expanded, otherwise nothing is shown when TR_HIDE_ROOT is set
    #         # # self.Expand(root_item)
    #         # # Ajouter les éléments de l'adaptateur à l'interface, en commençant par la racine.
    #         self._addObjectRecursively(root_item, None)
    #
    #         # FIX: Force l'expansion de la racine immédiatement pour que les enfants soient visibles
    #         # avec le style TR_HIDE_ROOT.
    #         if self.GetChildrenCount(root_item, recursively=False) > 0:
    #             self.SetItemHasChildren(root_item, True)
    #         self.Expand(root_item)
    #         # Fin de la logique root !
    #     finally:
    #         # # self.Thaw()
    #         # # On ne dégèle que si le widget est effectivement gelé
    #         # if self.IsFrozen():
    #         #     self.Thaw()
    #         # 2. On libère le flag de rafraîchissement
    #         self.__refreshing = False
    #         # 3. On ne dégèle que si nous avons nous-mêmes appelé Freeze
    #         if not already_frozen and self.IsFrozen():
    #             try:
    #                 self.Thaw()
    #             except Exception as e:
    #                 log.debug(
    #                     "TreeListCtrl.RefreshAllItems : Erreur lors du Thaw (ignorée) : %s",
    #                     e,
    #                 )
    #
    #     # Force le redessin de la fenêtre principale pour s'assurer que les items sont visibles
    #     if self.GetMainWindow():
    #         self.GetMainWindow().Refresh()
    #         self.GetMainWindow().Update()
    #
    #     # # Restore selection AFTER Thaw - SelectItem doesn't work while Frozen
    #     # selected_item = None
    #     # if self.__selection:
    #     #     selected_item = self.select(self.__selection)
    #     # selections = self.GetSelections()
    #     # # Use the item returned by select() for scrolling if GetSelections fails
    #     # scroll_target = selections[0] if selections else selected_item
    #     # # if selections:
    #     # if scroll_target:
    #     #     self.GetMainWindow()._current = (
    #     #         self.GetMainWindow()._key_current
    #     #         # ) = selections[0]
    #     #         # self.ScrollTo(selections[0])
    #     #     ) = scroll_target
    #     #     self.ScrollTo(scroll_target)
    #     # # self.Thaw()
    #     # # On ne dégèle que si le widget est effectivement gelé
    #     # if self.IsFrozen():
    #     #     self.Thaw()
    #     # # Force immediate repaint to reduce visible flicker after rebuild
    #     # self.GetMainWindow().Refresh(eraseBackground=False)

    def RefreshAllItems(self):
        """
        Reconstruit complètement l'arbre affiché dans le TreeListCtrl à partir de l'adaptateur.

        Effets : Cette méthode :
        - supprime tous les items graphiques existants (DeleteAllItems),
        - recrée une nouvelle racine interne (AddRoot("")) et met à jour self._root,
        - reconstruit l'arbre via l'adaptateur en Remplissant récursivement
          les enfants en appelant l'adaptateur via _addObjectRecursively.
        - rafraîchit l'affichage via Refresh(),
        - ne lève pas d'exception sauf si la racine résultante est invalide.

        Notes :
        - Conçu pour être appelé depuis scheduleRefresh ou manuellement.
        - Conserver et restaurer la sélection doit se faire avant/après l'appel si nécessaire.

        Remarques :
        - Cette opération invalide tous les TreeItemId préexistants ;
          ne conservez pas d'anciens identifiants entre deux rebuilds.
        - Si wx.TR_HIDE_ROOT est utilisé, la racine interne est cachée
          mais nécessaire comme conteneur ;
          l'appel à Expand() sur la racine doit être évité
          si la racine est effectivement cachée.
        """
        log.debug(
            f"TreeListCtrl.RefreshAllItems : début du rafraîchissement de tous les éléments."
        )
        self.__refreshing = True  # Supprime les événements de sélection pendant la reconstruction
        # Gèle le widget pour éviter le scintillement pendant la reconstruction
        self.Freeze()
        try:
            # 1. Sauvegarde la sélection actuelle (objets métier)
            self.__selection = self.curselection()

            # Supprime tous les éléments existants du contrôle
            self.DeleteAllItems()  # vide complètement le TreeCtrl, self._root devient invalide !

            log.debug(
                f"TreeListCtrl.RefreshAllItems : suppression de ses enfants."
            )
            # Crée un nouvel item racine
            root_item = self.AddRoot(
                ""
            )  # crée une racine vide utilisée comme conteneur interne

            # Met à jour self._root avec la nouvelle racine (l'ancienne a été supprimée par DeleteAllItems)
            self._root = root_item
            # # IMPORTANT : utiliser GetRootItem ensuite pour obtenir la racine actuelle, car AddRoot() peut retourner un nouvel item différent de l'ancien root_item, surtout si HyperTreeList gère une racine cachée. GetRootItem() garantit que nous avons la référence correcte à la racine actuelle du contrôle, même après un rebuild.
            # # self._root = self.GetRootItem()
            # root = self.GetRootItem()

            # Log pour vérifier que la racine existe
            log.debug(
                f"TreeListCtrl.RefreshAllItems : Nouvelle racine créée : root_item={root_item}, self._root={self._root}"
            )

            # Vérifie que la racine est valide
            if (
                not root_item.IsOk() and not self._root.IsOk()
            ):  # teste si l'objet TreeItem est valide
                raise RuntimeError("La racine du TreeListCtrl est invalide")

            # # S'assurer que l'item racine est étendu
            # try:
            #     self.Expand(root_item)
            # except RuntimeError:
            #     log.error(
            #         "TreeListCtrl.RefreshAllItems : Impossible d'étendre la racine.",
            #         exc_info=True,
            #     )
            # except Exception:
            #     log.error(
            #         "TreeListCtrl.RefreshAllItems : Impossible d'étendre la racine. Can't Expand An Hidden Root.",
            #         exc_info=True,
            #     )

            # Peuple récursivement l'arbre avec les objets du modèle
            self._addObjectRecursively(
                root_item,  # item graphique parent
                # # self._root,  # item graphique parent
                # root,  # item graphique parent
                None,  # objet métier parent (None = racine)
            )
            log.debug(
                f"TreeListCtrl.RefreshAllItems : Tree count after build: {self.GetCount()}"
            )

            # # # IMPORTANT : force l'expansion de la racine
            # # # Sinon les enfants ne sont pas visibles si TR_HIDE_ROOT est utilisé
            # # # root_item.Expand()
            # # self.Expand(
            # #     root_item
            # # )  # Parce que TreeListItem ne gère pas toujours bien l'expansion directe.
            # # Vérifie si la racine est cachée avant de tenter une expansion
            # style = self.GetWindowStyle()
            #
            # # Si la racine est visible
            # if not (style & wx.TR_HIDE_ROOT):
            #     log.debug(
            #         f"TreeListCtrl.RefreshAllItems : la racine est visible, on peut l'étendre."
            #     )
            #     # On peut étendre la racine
            #     self.Expand(self._root)
            #     # self.Expand(root_item)
            # else:
            #     log.debug(f"TreeListCtrl.RefreshAllItems : la racine est cachée.")
            # PAS d'appel à self.Expand(root_item) — la racine est cachée dans HyperTreeList
            # Les enfants sont directement visibles via _addObjectRecursively
            # Expand n'est ni nécessaire ni compatible.

            # self.Expand(
            #     self._root
            # )  # ✅ OBLIGATOIRE pour que les enfants soient visibles, même si la racine est cachée.
            # Faux avec HyperTreeList, contrairement à wx.TreeCtrl.
            # # Interdit avec une racine cachée !

            # Le test testRetainSelectionWhenAddingSubTask() échoue car la sélection n'est pas restaurée après le rafraîchissement de l'arbre. La méthode RefreshAllItems() reconstruit l'arbre, ce qui invalide les TreeItemId précédemment sélectionnés. Bien que la logique pour stocker la sélection (self.__selection = self.curselection()) soit présente dans scheduleRefresh (qui appelle RefreshAllItems), la restauration de cette sélection n'est pas effectuée après la reconstruction de l'arbre.
            # Pour corriger cela, je vais ajouter un appel à self.select(self.__selection) et self.ScrollTo(selected_item) dans la méthode RefreshAllItems() de taskcoach/taskcoachlib/widgets/treectrl.py, après que l'arbre a été entièrement reconstruit.
        finally:
            # Dégèle le widget
            self.Thaw()
            self.__refreshing = False

        # Restaure la sélection
        selected_item = None
        if self.__selection:
            selected_item = self.select(self.__selection)
            if selected_item:
                # On s'assure que l'élément est bien sélectionné et visible
                self.SelectItem(selected_item)
                self.ScrollTo(selected_item)

        # Rafraîchit l'affichage du contrôle
        self.Refresh()
        log.debug(f"TreeListCtrl.RefreshAllItems : fin du rafraîchissement !")

    def __safeExpand(self, item):
        """Safely expand an item, guarding against deleted C++ objects."""
        try:
            if self and item:
                log.debug(
                    f"TreeListCtrl.__safeExpand : Expansion de l'item {item}"
                )
                self.Expand(item)
                log.debug(
                    f"TreeListCtrl.__safeExpand : Item étendu. Nombre d'enfants visibles : {self.GetChildrenCount(item)}"
                )
                self.Refresh()
                self.Update()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            log.debug(
                f"TreeListCtrl.__safeExpand : Impossible d'étendre l'item {item} car l'objet a été supprimé."
            )
            pass

    def RefreshItems(self, *objects):
        """
        Rafraîchit les éléments correspondant aux objets de domaine donnés.

        Si un objet de domaine est dans la liste des objets donnés,
        tous les éléments de l'arbre qui ont cet objet de domaine
        comme PyData seront rafraîchis.

        Args :
            *objects : Les objets de domaine pour lesquels les éléments correspondants doivent être rafraîchis.

        Returns :
            None
        """
        log.debug(
            f"TreeListCtrl.RefreshItems : rafraîchissement des éléments pour les objets {objects}."
        )
        # 1. On arrête l'édition en cours pour éviter les conflits de mise à jour pendant le rafraîchissement.
        self.StopEditing()  # TODO : Assurez-vous que StopEditing() gère correctement les cas où aucun label n'est en cours d'édition, pour éviter les erreurs.
        # 2. On stocke la sélection actuelle pour la restaurer après le rafraîchissement.
        # Cela garantit que les éléments sélectionnés restent sélectionnés
        # même après la reconstruction de l'arbre.
        self.__selection = self.curselection()
        # 3. On rafraîchit les éléments correspondants aux objets de domaine donnés.
        self._refreshTargetObjects(self.GetRootItem(), *objects)
        log.debug(
            f"TreeListCtrl.RefreshItems : rafraîchissement terminé pour les objets {objects} !"
        )

    def _refreshTargetObjects(self, parent_item, *target_objects):
        child_item, cookie = self.GetFirstChild(parent_item)
        while child_item:
            item_object = self.GetItemPyData(child_item)
            if item_object in target_objects:
                self._refreshObjectCompletely(
                    item=child_item, domain_object=item_object
                )
            self._refreshTargetObjects(child_item, *target_objects)
            child_item, cookie = self.GetNextChild(parent_item, cookie)

    def _refreshObjectCompletely(self, item, domain_object=None, *args):
        """
        Rafraîchit complètement un élément de l'arbre en mettant à jour
        tous les aspects (type, colonnes, couleurs, police, sélection)
        en fonction de l'objet de domaine associé.

        Args:
            item: L'élément de l'arbre à rafraîchir.
            domain_object: L'objet de domaine associé à l'élément,
                           utilisé pour récupérer les données nécessaires au rafraîchissement.
            *args: Les arguments supplémentaires à passer aux méthodes de rafraîchissement des aspects, si nécessaire.

        Returns:
            None
        """
        # Rafraîchit tous les aspects de l'élément en fonction de l'objet de domaine associé.
        self.__refresh_aspects(
            ("ItemType", "Columns", "Font", "Colors", "Selection"),
            item,
            domain_object,
            check=True,
            *args,
        )
        # Après avoir rafraîchi les aspects,
        # nous appelons RefreshLine pour forcer la mise à jour de l'affichage de l'élément.
        # Cela est nécessaire pour que les changements de type d'item soient pris en compte visuellement.
        if isinstance(
            self.GetMainWindow(), customtree.CustomTreeCtrl
        ):  # Semble plutôt être une instance de _CtrlWithDropTargetMixin
            self.GetMainWindow().RefreshLine(
                item
            )  # Seule customtreectrl a une méthode RefreshLine.

    def _addObjectRecursively(self, parent_item, parent_object=None):
        """
        Méthode qui peuple l'interface.

        Ajoute récursivement les objets métier enfants fournis par l'adaptateur dans l'arbre graphique.

        Args:
            parent_item (wx.TreeItemId|None) : Item graphique parent dans le TreeListCtrl auquel les enfants seront ajoutés. (peut être None -> utilise la racine).
            parent_object : Objet métier parent de domaine correspondant à parent_item, utilisé pour récupérer les enfants via l'adaptateur (None pour la racine).

        Comportement :
        - Récupère la liste des enfants via self.__adapter.children(parent_object).
        - Pour chaque enfant, crée un item graphique via AppendItem en associant data=child_object,
        - Remplit les colonnes via SetItemText.
        - Appelle _refreshObjectMinimally pour mettre à jour les aspects en réglant type/texte/images/couleurs/police/sélection.
        - Si l'objet est marqué expansé par l'adaptateur, descend récursivement.
        - Si l'adaptateur indique que l'objet est expansé (getItemExpanded), la méthode descend récursivement et étend l'item si nécessaire.

        Returns:
            None
        """
        log.debug(
            f"TreeListCtrl._addObjectRecursively : début du peuplement de l'interface. self={self}, parent_item={parent_item}, parent_object={parent_object}."
        )
        log.error(
            f"ROOT = {self._root}, IsOk = {self._root.IsOk() if self._root else 'None'}"
        )
        if parent_item is None or not parent_item.IsOk():
            # parent_item = self._root  # Racine cachée !
            parent_item = self.GetRootItem()
            log.debug(
                f"TreeListCtrl._addObjectRecursively : parent_item invalide, utilisation de la racine {parent_item} à la place."
            )
        log.debug(
            f"TreeListCtrl._addObjectRecursively : ajout de l'objet {parent_object} à l'interface grace à self.__adapter={self.__adapter}."
        )
        # log.debug(
        #     "TreeListCtrl._addObjectRecursively : Adapter root objects: %s",
        #     self.__adapter.domainObjectsToView(),
        # )  # Erreur dans les tests : AttributeError: 'TestCaseFrame' object has no attribute 'domainObjectsToView'
        log.debug(
            "TreeListCtrl._addObjectRecursively : Children of root: %s",
            self.__adapter.children(None),
        )
        log.debug(
            f"TreeListCtrl._addObjectRecursively : parent_item IsOk: {parent_item.IsOk()}"
        )
        # log.debug(
        #     f"TreeListCtrl._addObjectRecursively : ROOT ITEM: {self.GetRootItem()}, IsOk: {self.GetRootItem().IsOk()}"
        # )
        # log.debug(
        #     f"TreeListCtrl._addObjectRecursively : Item count: {self.GetCount()}"
        # )
        log.debug(
            "TreeListCtrl._addObjectRecursively: parent_object=%r, parent_item=%r, parent_item.IsOk=%s",
            parent_object,
            parent_item,
            (
                parent_item.IsOk()
                if getattr(parent_item, "IsOk", None)
                else "<no IsOk>"
            ),
        )
        children = list(self.__adapter.children(parent_object))
        log.debug(
            f"TreeListCtrl._addObjectRecursively : Children returned (len={len(children)}): {children}"
        )

        # Récupère les enfants de l'objet parent à partir de l'adaptateur et ajoute-les récursivement à l'interface.
        # for child_object in self.__adapter.children(parent_object):
        #
        #     # Si self.AppendItem échoue ou ne fait rien, rien ne s'affiche.
        #     #  l'appel à AppendItem utilise self.getItemCTType(child_object) comme 3ème argument.
        #     #  Or, le 3ème argument de AppendItem dans HyperTreeList est l'index de l'image (image),
        #     #  pas le type de case à cocher (ct_type).
        #     #  De plus, le type de l'item (case à cocher, radio, etc.)
        #     #  n'est jamais défini explicitement lors de la création,
        #     #  et _refreshObjectMinimally ne le mettait pas à jour non plus.
        for child_object in children:
            if child_object is None:
                log.error("child_object est None !")
                return
            log.debug(
                f"TreeListCtrl._addObjectRecursively : Processing child_object: {child_object}"
            )
            col_count = (
                self.GetColumnCount() if hasattr(self, "GetColumnCount") else 0
            )
            log.debug(
                "TreeListCtrl._addObjectRecursively: GetColumnCount=%s",
                col_count,
            )
            # build column_values (ce que nous avons déjà corrigé)
            # Voici les corrections pour taskcoachlib/widgets/treectrl.py :
            # 1. Corriger l'appel à AppendItem pour ne pas passer le type comme index d'image.
            # Récupère les textes de colonnes fournis par l'adaptateur.
            # L'adaptateur expose getItemText(item, column=None) qui retourne
            # le texte pour une colonne donnée. Construisons donc la liste des
            # valeurs de colonnes en interrogeant explicitement chaque colonne.
            column_values = [
                self.__adapter.getItemText(child_object, col_index)
                for col_index in range(self.GetColumnCount())
            ]
            # 2. Ajouter ItemType à la liste des aspects rafraîchis
            # dans _refreshObjectMinimally pour s'assurer que les cases à cocher s'affichent.
            # On récupère le type de case à cocher (0=rien, 1=checkbox, 2=radio)
            # Récupère le type de case à cocher pour cet objet
            log.debug(
                f"TreeListCtrl._addObjectRecursively : récupère le ct_type du child_object {child_object}."
            )
            ct_type = self.getItemCTType(child_object)
            log.debug(
                f"TreeListCtrl._addObjectRecursively : Ajoute l'ItemType ct_type={ct_type} à la liste des aspect rafraîchis."
            )

            # Récupère le texte de la première colonne
            first_text = str(column_values[0]) if column_values else ""

            # Création de l'item dans l'arbre sans texte initial
            # Création de l'item AVEC texte
            child_item = self.AppendItem(  # Unresolved attribute reference 'AppendItem' for class 'TreeListCtrl'
                parent_item,  # item parent dans l'arbre
                # self.GetRootItem(),  # Ne change rien ! ?
                # "",  # Problème : le texte de la première colonne est géré par les valeurs, pas par 'text'. Tu insères chaque ligne avec un texte vide.
                # # # # Cela casse l'affichage de la première colonne, qui est censée afficher le texte de l'item. En Tkinter, le texte de la première colonne doit être passé via 'text', et les autres colonnes via 'values'.
                # # text=column_values[0] if column_values else "",
                # # self.getItemCTType(child_object),
                # # text=column_values[0],  # incorrect
                first_text,  # ✅ TEXTE PRINCIPAL de l'item, affiché dans la première colonne. Les autres colonnes sont gérées par SetItemText.
                # column_values[0],
                ct_type=ct_type,  # type de checkbox
                image=-1,  # pas d'image
                # setImage=-1,
                data=child_object,  # associe l'objet métier à l'item
            )
            # Attention, 'TreeListItem' object is not iterable
            # child_item = self.AppendItem(
            #     parent_item,
            #     "VISIBLE TEST",
            #     -1,
            #     -1,
            #     child_object,
            # )
            # Vérification immédiate
            log.error(f"AppendItem returned: {child_item}")
            if not child_item or (
                hasattr(child_item, "IsOk") and not child_item.IsOk()
            ):
                log.error(
                    "TreeListCtrl._addObjectRecursively: AppendItem FAILED for child_object=%r parent_item=%r column_values=%r",
                    child_object,
                    parent_item,
                    column_values,
                )
            else:
                try:
                    is_ok = child_item.IsOk()
                except Exception:
                    is_ok = "<no IsOk>"
                log.debug(
                    "TreeListCtrl._addObjectRecursively: AppendItem OK -> child_item=%r IsOk=%s",
                    child_item,
                    is_ok,
                )
                log.debug(
                    "TreeListCtrl._addObjectRecursively: Tree count after append: GetItemCount=%s",
                    (
                        self.GetItemCount()
                        if hasattr(self, "GetItemCount")
                        else "<no GetItemCount>"
                    ),
                )
            log.debug(
                "TreeListCtrl._addObjectRecursively : Tree count after append: %s",
                # self.GetCount(),
                self.GetItemCount(),
            )
            # Remplit toutes les colonnes
            # for col, value in enumerate(column_values[1:], start=1):
            for column_index, value in enumerate(column_values):
                if column_index == 0:
                    continue  # déjà mis dans AppendItem
                # Définit le texte dans la colonne correspondante
                # self.SetItemText(child_item, value, col)
                self.SetItemText(  # Unresolved attribute reference 'SetItemText' for class 'TreeListCtrl'
                    child_item,  # item à modifier
                    str(value),  # texte affiché
                    column_index,  # numéro de colonne
                )
                # Explication des changements
                # • Dans _addObjectRecursively : J'ai remplacé self.getItemCTType(child_object) par image=-1. getItemCTType renvoie 0, 1 ou 2 (pour les types de cases à cocher), ce qui était interprété à tort comme un index d'image par AppendItem. Cela pouvait afficher une mauvaise icône ou rien du tout, et surtout ne configurait pas la case à cocher.
                # • Dans _refreshObjectMinimally : J'ai ajouté "ItemType" à la liste des aspects à rafraîchir. Comme _addObjectRecursively appelle cette méthode juste après la création de l'item, cela garantit que _refreshItemType sera appelé, configurant ainsi correctement les cases à cocher (checkboxes) pour chaque tâche.
                # Ces modifications devraient rendre vos tâches visibles avec leurs cases à cocher correctes. Relancez l'application et vérifiez le TaskViewer.
                log.debug(
                    "TreeListCtrl._addObjectRecursively: set text for column %d -> %r",
                    column_index,
                    str(value),
                )
                log.debug(
                    f"TreeListCtrl._addObjectRecursively : L'item {child_item.__class__.__name__} {child_item} de value {str(value)} pour l'objet {child_object} est ajouté dans la colonne {column_index} de l'interface {self.__class__.__name__}."
                )  # Attention, 'TreeListItem' object child_item is not iterable, list() ne fonctionne pas dessus.
            log.debug("COLUMN VALUES: %s", column_values)
            self._refreshObjectMinimally(child_item, child_object)
            expanded = self.__adapter.getItemExpanded(child_object)
            # if expanded:
            if expanded and self.__adapter.isTreeViewer():
                log.debug(
                    f"TreeListCtrl._addObjectRecursively : child_item {child_item} est expansé, ajout récursif de ses enfants."
                )
                # récursion
                self._addObjectRecursively(child_item, child_object)
                # Call Expand on the item instead of on the tree
                # (self.Expand(childItem)) to prevent lots of events
                # (EVT_TREE_ITEM_EXPANDING/EXPANDED) being sent
                # child_item.Expand()
                self.Expand(child_item)
            else:
                log.debug(
                    f"TreeListCtrl._addObjectRecursively : child_item {child_item} n'est pas expansé, pas de récursivité de ses enfants."
                )
                # # Important : ne jamais descendre récursivement en mode flat.
                # self.SetItemHasChildren(
                #     child_item, self.__adapter.children(child_object)
                # )
                # Le test testIsAnyItemExpandable_OneCollapsedParent() échoue car isAnyItemExpandable() retourne False au lieu de True. Cela est dû au fait que la méthode _addObjectRecursively dans TreeListCtrl ne définit pas correctement l'état ItemHasChildren pour les éléments qui ne sont pas initialement développés.
                # Lorsque self.__adapter.getItemExpanded(child_object) est False (c'est-à-dire que l'élément est replié), la récursion pour ajouter ses enfants n'est pas effectuée. Cependant, le widget doit quand même savoir que cet élément a des enfants pour afficher le bouton d'expansion et pour que ItemHasChildren() retourne True.
                # Set ItemHasChildren so that the expand button is visible
                # and ItemHasChildren returns True, even if children are not
                # added recursively yet.
                # Réintroduction de la ligne en vérifiant si l'élément a réellement des enfants, pour corriger le comportement.
                if self.__adapter.children(child_object):
                    self.SetItemHasChildren(child_item, True)
                    # Attention risque de faux négatif !?

        log.debug(
            f"TreeListCtrl._addObjectRecursively : fin du peuplement de l'interface !"
        )

    def _refreshObjectMinimally(self, *args, **kwargs):
        # log.debug("TreeListCtrl._refreshObjectMinimally: item=%r domain_object=%r ct_type=%s current_item_type=%s", item, domain_object, ct_type, self.GetItemType(item) if hasattr(self, "GetItemType") else "<no GetItemType>")
        self.__refresh_aspects(
            ("ItemType", "Columns", "Colors", "Font", "Selection"),
            *args,
            **kwargs,
        )

    def __refresh_aspects(self, aspects, domain_object, *args, **kwargs):
        for aspect in aspects:
            # refresh_aspect = getattr(self, "_refresh%s" % aspect)
            refresh_aspect = getattr(self, f"_refresh{aspect}")
            refresh_aspect(domain_object, *args, **kwargs)

    def _refreshItemType(self, item, domain_object, check=False):
        """
        Rafraîchit le

        Args:
            item:
            domain_object:
            check:

        Returns:

        """
        log.debug(f"TreeListCtrl._refreshItemType : début.")
        ct_type = self.getItemCTType(domain_object)
        if not check or (check and ct_type != self.GetItemType(item)):
            self.SetItemType(item, ct_type)
        log.debug(
            "TreeListCtrl._refreshItemType: item=%r domain_object=%r ct_type=%s current_item_type=%s",
            item,
            domain_object,
            ct_type,
            (
                self.GetItemType(item)
                if hasattr(self, "GetItemType")
                else "<no GetItemType>"
            ),
        )
        log.debug(f"TreeListCtrl._refreshItemType : terminé !")

    def _refreshColumns(self, item, domain_object, check=False):
        for column_index in range(self.GetColumnCount()):
            self._refreshColumn(item, domain_object, column_index, check=check)

    def _refreshColumn(self, item, domain_object, column_index, check=False):
        aspects = (
            ("Text", "Image")
            if column_index in self.__columns_with_images
            else ("Text",)
        )
        self.__refresh_aspects(
            aspects, item, domain_object, column_index, check=check
        )

    def _refreshText(self, item, domain_object, column_index, check=False):
        text = self.__adapter.getItemText(domain_object, column_index)
        if text.count("\n") > 3:
            text = "\n".join(text.split("\n")[:4]) + " ..."
        if not check or (check and text != item.GetText(column_index)):
            item.SetText(column_index, text)

    def _refreshImage(self, item, domain_object, column_index, check=False):
        images = self.__adapter.getItemImages(domain_object, column_index)
        for which, image in list(images.items()):
            image = image if image >= 0 else -1
            if not check or (
                check and image != item.GetImage(which, column_index)
            ):
                item.SetImage(column_index, image, which)

    def _refreshColors(self, item, domain_object, check=False):
        bg_color = (
            domain_object.backgroundColor(recursive=True) or wx.NullColour
        )
        if not check or (
            check and bg_color != self.GetItemBackgroundColour(item)
        ):
            self.SetItemBackgroundColour(item, bg_color)
        fg_color = (
            domain_object.foregroundColor(recursive=True) or wx.NullColour
        )
        if not check or (check and fg_color != self.GetItemTextColour(item)):
            self.SetItemTextColour(item, fg_color)

    def _refreshFont(self, item, domain_object, check=False):
        font = domain_object.font(recursive=True) or self.__default_font
        if not check or (check and font != self.GetItemFont(item)):
            self.SetItemFont(item, font)

    def _refreshSelection(self, item, domain_object, check=False):
        select = domain_object in self.__selection
        if not check or (check and select != item.IsSelected()):
            # Use SetHilight for visual highlighting during tree construction.
            # Actual selection is done via select() after tree is fully built.
            item.SetHilight(select)

    def scheduleRefresh(self, count=0):
        """Programme un rafraîchissement différé pour éviter les multiples appels à RefreshAllItems().

        Planifie un rafraîchissement différé (coalescing) pour éviter les rebuilds multiples.

        La méthode évite les rafraîchissements redondants
        en gardant un flag __refresh_scheduled.
        Lors de l'ordonnancement, elle posera le flag,
        et exécutera finalement RefreshAllItems pour reconstruire l'arbre.
        forceRefresh() réinitialise le flag et force la replanification.
        """
        log.debug(
            f"TreeListCtrl.scheduleRefresh : début du rafraîchissement différé."
        )
        if self.__refresh_scheduled:
            log.debug(f"TreeListCtrl.scheduleRefresh : déjà planifié !")
            return  # ← RETOUR IMMÉDIAT si déjà planifié
        self.__refresh_scheduled = True

        # def doRefresh():
        #     # C'est la seule correction nécessaire :
        #     # remettre __refresh_scheduled = False dans tous les chemins de sortie de doRefresh,
        #     # pas seulement dans le chemin nominal.
        #
        #     # Protection contre la destruction de l'objet
        #     # if not self:
        #     try:
        #         if not self:
        #             log.debug(f"TreeListCtrl.doRefresh : objet déjà supprimé.")
        #             # solution :
        #             self.__refresh_scheduled = (
        #                 False  # ← remettre le flag même en cas d'abort
        #             )
        #             return
        #     except RuntimeError:
        #         # L'objet C++ a été supprimé
        #         log.warning(
        #             f"TreeListCtrl.doRefresh : erreur de suppression de l'objet déjà supprimé."
        #         )
        #         self.__refresh_scheduled = False  # ← idem
        #         return
        #     self.__refresh_scheduled = False
        #     log.debug(
        #         f"TreeListCtrl.doRefresh : exécution du rafraîchissement planifié."
        #     )
        #     # self.RefreshAllItems(count)  # Faux, RefreshAllItems() ne prend aucun argument.
        #     self.RefreshAllItems()
        #     # Le problème est le suivant :
        #     # lors du thaw, refresh() est appelé 3 fois (on le voit dans le log :
        #     # 3 × "Rafraîchissement de la visionneuse CategoryViewer avec 8 éléments").
        #     # La première appelle scheduleRefresh qui pose __refresh_scheduled = True.
        #     # Les 2 suivantes retournent immédiatement car le flag est déjà posé.
        #     # Puis doRefresh s'exécute via wx.CallAfter — mais à ce moment
        #     # le widget est encore à 20×20 pixels,
        #     # donc RefreshAllItems s'exécute mais le widget n'est pas encore dans sa taille finale.
        #     # Quand la fenêtre s'agrandit après, aucun nouveau refresh n'est planifié.

        # # Important : ici after doit être celui de ton widget Tkinter.
        # self.after(1, doRefresh)
        # Utilisation de wx.CallAfter pour wxPython
        # wx.CallAfter(doRefresh)
        log.debug(
            "TreeListCtrl.doRefresh : exécution du rafraîchissement planifié."
        )
        self.__refresh_scheduled = False
        self.RefreshAllItems()
        log.debug(
            f"TreeListCtrl.scheduleRefresh : fin du rafraîchissement planifié différé !"
        )

    def forceRefresh(self):
        """Force un rafraîchissement même si un autre est déjà planifié.

        Remise à zéro du flag __refresh_scheduled puis appel de scheduleRefresh().
        """
        log.debug(f"TreeListCtrl.forceRefresh : début du rafraîchissement.")
        self.__refresh_scheduled = False
        self.scheduleRefresh()
        # self.RefreshAllItems()
        log.debug(f"TreeListCtrl.forceRefresh : fin du rafraîchissement !")

    # Event handlers

    def onSelect(self, event):
        # Skip selection events during refresh to avoid spurious updates
        if self.__refreshing:
            event.Skip()
            return
        # Use CallAfter to prevent handling the select while items are
        # being deleted:
        # wx.CallAfter(self.selectCommand)
        wx.CallAfter(self.__safeSelectCommand)
        event.Skip()

    def __safeSelectCommand(self):
        """Safely call selectCommand, guarding against deleted C++ objects."""
        try:
            if self:
                self.selectCommand()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def onKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.editCommand(event)
        elif event.GetKeyCode() == wx.WXK_F2 and self.GetSelections():
            # self.EditLabel(self.GetSelections()[0])
            self.EditLabel(self.GetSelections()[0], column=0)
        else:
            event.Skip()

    def OnDrop(self, drop_item, drag_items, part, column):
        drop_item = (
            None
            if drop_item == self.GetRootItem()
            else self.GetItemPyData(drop_item)
        )
        drag_items = list(
            self.GetItemPyData(drag_item) for drag_item in drag_items
        )
        wx.CallAfter(
            # self.dragAndDropCommand, drop_item, drag_items, part, column
            self.__safeDragAndDropCommand,
            drop_item,
            drag_items,
            part,
            column,
        )

    def __safeDragAndDropCommand(self, drop_item, drag_items, part, column):
        """Safely call dragAndDropCommand, guarding against deleted C++ objects."""
        try:
            if self:
                self.dragAndDropCommand(drop_item, drag_items, part, column)
                # Expand the drop target if items were dropped on it
                if drop_item is not None:
                    self._expandDropTarget(drop_item)
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def _expandDropTarget(self, drop_item):
        """Expand the drop target item so the dropped children are visible."""
        # Find the tree item for the drop target
        for item in self.GetItemChildren(recursively=True):
            if self.GetItemPyData(item) == drop_item:
                if self.GetChildrenCount(
                    item, recursively=False
                ) > 0 or self.ItemHasChildren(item):
                    self.Expand(item)
                break

    def onItemExpanding(self, event):
        event.Skip()
        item = event.GetItem()
        if self.GetChildrenCount(item, recursively=False) == 0:
            domain_object = self.GetItemPyData(item)
            self._addObjectRecursively(item, domain_object)

    def onDoubleClick(self, event):
        self.__user_double_clicked = True
        if self.isClickablePartOfNodeClicked(event):
            event.Skip(False)
        else:
            self.onItemActivated(event)

    def onItemActivated(self, event):
        """
        Attacher la colonne sur laquelle vous avez cliqué à l'événement
        afin que nous puissions l'utiliser ailleurs.
        """
        column_index = self.__column_under_mouse()
        if column_index >= 0:
            event.columnName = self._getColumn(column_index).name()
        self.editCommand(event)
        event.Skip(False)

    def __column_under_mouse(self):
        log.debug("TreeListCtrl.__column_under_mouse : début")
        mouse_position = self.GetMainWindow().ScreenToClient(
            wx.GetMousePosition()
        )
        item, _, column = self.HitTest(mouse_position)
        if item:
            # Only get the column name if the hittest returned an item,
            # otherwise the item was activated from the menu or by double-clicking
            #  on a portion of the tree view not containing an item.
            log.debug(
                f"TreeListCtrl.__column_under_mouse : fin1 colonne={column}"
            )
            return max(0, column)
        else:
            log.debug("TreeListCtrl.__column_under_mouse : fin2")
            return -1

    # Inline editing

    def onBeginEdit(self, event):
        if self.__user_double_clicked:
            event.Veto()
            self.__user_double_clicked = False
        elif self.IsLabelBeingEdited():
            # Don't start editing another label when the user is still editing
            # a label. This prevents left-over text controls in the tree.
            event.Veto()
        else:
            event.Skip()

    def onEndEdit(self, event):
        if event._editCancelled:  # pylint: disable=W0212
            event.Skip()
            return
        event.Veto()  # Let us update the tree
        domain_object = self.GetItemPyData(event.GetItem())
        new_value = event.GetLabel()
        column = self._getColumn(event.GetInt())
        column.onEndEdit(domain_object, new_value)

    def CreateEditCtrl(self, item, column_index):
        column = self._getColumn(column_index)
        domain_object = self.GetItemPyData(item)
        return column.editControl(
            self.GetMainWindow(), item, column_index, domain_object
        )

    # Override CtrlWithColumnsMixin with TreeListCtrl specific behaviour:

    def _setColumns(self, *args, **kwargs):
        super()._setColumns(*args, **kwargs)
        self.SetMainColumn(0)
        for column_index in range(self.GetColumnCount()):
            self.SetColumnEditable(
                column_index, self._getColumn(column_index).isEditable()
            )

    # Extend TreeMixin with TreeListCtrl specific behaviour:

    @staticmethod
    def __get_style():
        # return wx.WANTS_CHARS
        # Enable horizontal scrollbar for natural column resizing
        return wx.WANTS_CHARS | wx.HSCROLL

    @staticmethod
    def __get_agw_style():
        agw_style = (
            wx.TR_DEFAULT_STYLE
            | wx.TR_HIDE_ROOT
            | wx.TR_MULTIPLE
            | wx.TR_EDIT_LABELS
            | wx.TR_HAS_BUTTONS
            | wx.TR_FULL_ROW_HIGHLIGHT
            | customtree.TR_HAS_VARIABLE_ROW_HEIGHT
        )
        #  L'initialisation de la classe parente est fondamentale.
        #  Les styles agwStyle (TR_NO_HEADER_BUTTONS, TR_FULL_ROW_HIGHLIGHT,
        #  TR_COLUMN_LOCK, etc.) influencent le comportement de l'en-tête et des colonnes.
        if operating_system.isMac():
            agw_style |= wx.TR_NO_LINES
        agw_style &= ~hypertreelist.TR_NO_HEADER  # TR_NO_HEADER_BUTTONS ?
        return agw_style

    def DeleteColumn(self, column_index):
        self.RemoveColumn(column_index)

    def InsertColumn(self, column_index, column_header, *args, **kwargs):
        """Map ListCtrl alignment constants to TreeListCtrl alignment constants.
        Also set the column to be editable if the corresponding column in the
        adapter is editable.

        """
        alignment = self.alignmentMap[
            kwargs.pop("format", wx.LIST_FORMAT_LEFT)
        ]
        if column_index == self.GetColumnCount():
            self.AddColumn(column_header, *args, **kwargs)
        else:
            super().InsertColumn(column_index, column_header, *args, **kwargs)
        self.SetColumnAlignment(column_index, alignment)
        self.SetColumnEditable(
            column_index, self._getColumn(column_index).isEditable()
        )

    def showColumn(self, *args, **kwargs):
        """
        Arrêter l'édition avant de masquer ou d'afficher une colonne
        pour éviter les problèmes
        lors du redessinage du contenu du contrôle de la liste arborescente.
        """
        self.StopEditing()
        super().showColumn(*args, **kwargs)


class CheckTreeCtrl(TreeListCtrl):
    """
    Contrôle des listes en arbre avec bouton de vérification.
    """

    def __init__(
        self,
        parent,
        columns,
        selectCommand,
        checkCommand,
        editCommand,
        dragAndDropCommand,
        itemPopupMenu=None,
        *args,
        **kwargs,
    ):
        self.__checking = False
        # nouvel attribut :
        self._mainWin = None
        super().__init__(
            parent,
            columns,
            selectCommand,
            editCommand,
            dragAndDropCommand,
            itemPopupMenu,
            *args,
            **kwargs,
        )
        self.checkCommand = checkCommand
        self.Bind(customtree.EVT_TREE_ITEM_CHECKED, self.onItemChecked)
        # self.GetMainWindow().bind(wx.EVT_LEFT_DOWN, self.onMouseLeftDown)
        # AttributeError: 'TreeListMainWindow' object has no attribute 'bind'
        # Sauf que mainwindow crée la méthode bind() !
        self.GetMainWindow().Bind(wx.EVT_LEFT_DOWN, self.onMouseLeftDown)

    def getItemCTType(self, domain_object):
        """Use radio buttons (ct_type == 2) when the object has "exclusive"
        children, meaning that only one child can be checked at a time. Use
        check boxes (ct_type == 1) otherwise."""
        # if self.getIsItemCheckable(domain_object):  # Erreur, cette méthode est dans la version tkinter !
        #     return (
        #         2
        #         if self.getItemParentHasExclusiveChildren(domain_object)
        #         else 1
        #     )
        # else:
        #     return 0
        if domain_object:
            # return (
            #     2
            #     if self.getItemParentHasExclusiveChildren(domain_object)  # 'CheckTreeCtrl' object has no attribute 'getItemParentHasExclusiveChildren'
            #
            #     else 1
            # )
            to_return = (
                2
                # # if self.__adapter.getItemParentHasExclusiveChildren(
                # #     domain_object
                # # )  # 'CheckTreeCtrl' object has no attribute '_CheckTreeCtrl__adapter'
                # if self.getAdapter().getItemParentHasExclusiveChildren(
                #     domain_object
                # )
                if self._TreeListCtrl__adapter.getItemParentHasExclusiveChildren(
                    domain_object
                )  # Renvoie à CheckableTaskViewer.getItemParentHasExclusiveChildren
                # Ces deux méthodes (getItemParentHasExclusiveChildren et getIsItemChecked)
                # sont des méthodes du viewer/adaptateur, pas du widget.
                # Toutes les fois que CheckTreeCtrl doit interroger le viewer
                # pour l'état d'un objet, il doit passer par self._TreeListCtrl__adapter.
                else 1
            )
        else:
            to_return = 0
        log.debug(f"CheckTreeCtrl.getItemCTType : retourne {to_return}.")
        return to_return

    def CheckItem(self, item, checked=True):
        """Override CheckItem to allow unchecking radio items.

        By default, HyperTreeList does not allow unchecking radio items,
        but we want to allow it and just keep the tree consistent
        by unchecking all mutually exclusive siblings and children.
        """
        if self.GetItemType(item) == 2:
            # Use UnCheckRadioParent because CheckItem always keeps at least
            # one item selected, which we don't want to enforce
            log.debug(
                f"CheckTreeCtrl.CheckItem : appel de UnCheckRadioParent pour item {item} avec checked={checked}"
            )
            self.UnCheckRadioParent(item, checked)
        else:
            log.debug(
                f"CheckTreeCtrl.CheckItem : appel de super().CheckItem pour item {item} avec checked={checked}"
            )
            super().CheckItem(item, checked)

    def onMouseLeftDown(self, event):
        """Par défaut, le widget HyperTreeList ne permet pas de décocher
        un élément radio. Puisque nous souhaitons prendre en charge
        la décoche d'un élément radio, nous recherchons la souris
        laissée enfoncée et décochons l'élément et tous
        ses enfants si l'utilisateur clique sur un élément radio
        déjà sélectionné."""
        position = self.GetMainWindow().CalcUnscrolledPosition(
            event.GetPosition()
        )
        item, flags, dummy_column = self.HitTest(position)
        if (
            item
            and item.GetType() == 2
            and (flags & customtree.TREE_HITTEST_ONITEMCHECKICON)
            and self.IsItemChecked(item)
        ):
            self.__uncheck_item_recursively(item)
        else:
            event.Skip()

    def __uncheck_item_recursively(
        self, item, parent_is_expanded=True, disable_item=False
    ):
        if item.GetType():
            self.__uncheck_item(item, torefresh=parent_is_expanded)
        if disable_item:
            self.EnableItem(item, False, torefresh=parent_is_expanded)
        parent_is_expanded = item.IsExpanded()
        child, cookie = self.GetFirstChild(item)
        while child:
            self.__uncheck_item_recursively(
                child, parent_is_expanded, disable_item=True
            )
            child, cookie = self.GetNextChild(item, cookie)

    def __uncheck_item(self, item, torefresh):
        self.GetMainWindow().CheckItem2(
            item, checked=False, torefresh=torefresh
        )
        event = customtree.TreeEvent(
            customtree.wxEVT_TREE_ITEM_CHECKED, self.GetId()
        )
        event.SetItem(item)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def _refreshObjectCompletely(self, item, domain_object=None, *args):
        super()._refreshObjectCompletely(item, domain_object, *args)
        self._refreshCheckState(item, domain_object)

    def _refreshObjectMinimally(self, item, domain_object):
        super()._refreshObjectMinimally(item, domain_object)
        self._refreshCheckState(item, domain_object)

    def _refreshCheckState(self, item, domain_object):
        # # Use CheckItem2 so no events get sent:
        # # self.CheckItem2(item, self.getIsItemChecked(domain_object))
        # checked = self.getIsItemChecked(domain_object)
        checked = self._TreeListCtrl__adapter.getIsItemChecked(
            domain_object
        )  # Renvoie à LocalCategoryViewer dans editor.py.
        # Ces deux méthodes (getItemParentHasExclusiveChildren et getIsItemChecked)
        # sont des méthodes du viewer/adaptateur, pas du widget.
        # Toutes les fois que CheckTreeCtrl doit interroger le viewer pour l'état d'un objet,
        # il doit passer par self._TreeListCtrl__adapter.
        if checked is None:
            # Mixed state - enable 3-state and set undetermined
            item.Set3State(True)
            item.Set3StateValue(wx.CHK_UNDETERMINED)
        else:
            # Normal checked/unchecked state
            if item.Is3State():
                item.Set3State(False)
            self.CheckItem2(item, checked)
        parent = item.GetParent()
        while parent:
            if self.GetItemType(parent) == 2:
                self.EnableItem(item, self.IsItemChecked(parent))
                break
            parent = parent.GetParent()

    def refreshAllCheckStates(self):
        """Refresh the check state of all items without rebuilding the tree."""
        for item in self.GetItemChildren(recursively=True):
            domain_object = self.GetItemPyData(item)
            if domain_object is not None:
                self._refreshCheckState(item, domain_object)

    def onItemChecked(self, event):
        """When an item is checked or unchecked, uncheck all mutually exclusive
        siblings and children to keep the tree consistent, and then invoke the
        checkCommand callback with final=True to indicate that the tree is now
        consistent and any necessary actions can be taken based on the new
        check state.

        """
        if self.__checking:
            # Ignore checked events while we're making the tree consistent,
            # only invoke the callback:
            self.checkCommand(event, final=False)
            return
        self.__checking = True
        item = event.GetItem()
        # Uncheck mutually exclusive children:
        for child in self.GetItemChildren(item):
            if self.GetItemType(child) == 2:
                self.CheckItem(child, False)
                # Recursively uncheck children of mutually exclusive children:
                for grandchild in self.GetItemChildren(
                    child, recursively=True
                ):
                    self.CheckItem(grandchild, False)
        # If this item is mutually exclusive, recursively uncheck siblings
        # and parent:
        parent = item.GetParent()
        if parent and self.GetItemType(item) == 2:
            for child in self.GetItemChildren(parent):
                if child == item:
                    continue
                self.CheckItem(child, False)
                for grandchild in self.GetItemChildren(
                    child, recursively=True
                ):
                    self.CheckItem(grandchild, False)
            if self.GetItemType(parent) != 2:
                self.CheckItem(parent, False)
        self.__checking = False
        self.checkCommand(event, final=True)

    def onItemActivated(self, event):
        if self.__is_double_clicked(event):
            # Invoke super.onItemActivated to edit the item
            super().onItemActivated(event)
        else:
            # Item is activated, let another event handler deal with the event
            event.Skip()

    @staticmethod
    def __is_double_clicked(event):
        return hasattr(event, "LeftDClick") and event.LeftDClick()
