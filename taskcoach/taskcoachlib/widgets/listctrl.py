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

=======
# Documentation Technique : `taskcoachlib/widgets/listctrl.py`

## 1. Aperçu Général

Ce module fournit la classe `VirtualListCtrl`, un widget de contrôle de liste personnalisé basé sur `wx.ListCtrl` de `wxPython`. Il est spécifiquement conçu pour afficher de grands ensembles de données de manière efficace en utilisant le mode "virtuel".

**Fonctionnalités principales :**
- **Mode Virtuel** : Le contrôle ne charge en mémoire que les données des éléments actuellement visibles à l'écran, ce qui le rend très performant pour les listes contenant des milliers d'éléments.
- **Gestion des Colonnes** : S'intègre avec `CtrlWithColumnsMixin` pour une gestion flexible des colonnes.
- **Info-bulles (Tooltips)** : Supporte l'affichage d'info-bulles personnalisées pour chaque élément via `CtrlWithToolTipMixin`.
- **Gestion de la Sélection** : Fournit des méthodes pour gérer la sélection d'un ou plusieurs éléments.
- **Intégration avec l'Application** : Conçu pour déléguer la logique de récupération des données et la gestion des événements à un widget parent, favorisant une séparation claire des préoccupations.

Dans l'application Task Coach, ce widget est notamment utilisé pour afficher les listes de pièces jointes et les enregistrements d'efforts.

## 2. Architecture et Patrons de Conception

L'architecture de `VirtualListCtrl` repose sur plusieurs patrons de conception clés.

### Héritage Multiple
`VirtualListCtrl` utilise l'héritage multiple pour combiner les fonctionnalités de `wx.ListCtrl` avec plusieurs "mixins" personnalisés.

```mermaid
classDiagram
    class wx.ListCtrl {
        +HitTest()
        +Select()
    }
    class CtrlWithItemsMixin {
        +getItemWithIndex()
    }
    class CtrlWithColumnsMixin {
        +getIndexOfColumn()
    }
    class CtrlWithToolTipMixin {
        +getItemTooltipData()
    }
    class VirtualListCtrl {
        +__init__()
        +bindEventHandlers()
        +OnGetItemText()
        +OnGetItemImage()
        +OnGetItemAttr()
        +HitTest()
        +select()
    }

    wx.ListCtrl <|-- VirtualListCtrl
    CtrlWithItemsMixin <|-- VirtualListCtrl
    CtrlWithColumnsMixin <|-- VirtualListCtrl
    CtrlWithToolTipMixin <|-- VirtualListCtrl

Mode Virtuel (Patron Flyweight)
Le widget est initialisé avec le style wx.LC_VIRTUAL.
Ce mode est une application du patron de conception Flyweight,
où le widget (VirtualListCtrl) est un objet léger qui ne contient pas les données.
Au lieu de cela, lorsque wxPython a besoin d'afficher un élément (son texte, son icône, ses attributs),
il appelle une méthode de rappel (OnGetItemText, OnGetItemImage, etc.).
VirtualListCtrl récupère alors uniquement les données nécessaires
pour cet élément spécifique auprès de sa source de données.

Délégation (Patron Delegate)
VirtualListCtrl ne connaît pas la structure des données qu'il affiche.
Il délègue entièrement la responsabilité de la récupération des données à son widget parent
(fourni lors de l'initialisation).
Le parent agit comme un "délégué" ou une source de données et
doit implémenter une interface implicite.

sequenceDiagram
    participant User
    participant wx.ListCtrl as wx.ListCtrl (backend)
    participant VirtualListCtrl
    participant ParentWidget as Parent Widget (Data Source)

    User->>wx.ListCtrl: Fait défiler la liste
    wx.ListCtrl->>VirtualListCtrl: OnGetItemText(rowIndex=10, colIndex=1)
    VirtualListCtrl->>VirtualListCtrl: getItemWithIndex(rowIndex=10)
    VirtualListCtrl->>ParentWidget: getItemWithIndex(rowIndex=10)
    ParentWidget-->>VirtualListCtrl: domainObject
    VirtualListCtrl->>VirtualListCtrl: getItemText(domainObject, colIndex=1)
    VirtualListCtrl->>ParentWidget: getItemText(domainObject, colIndex=1)
    ParentWidget-->>VirtualListCtrl: "Texte de l'item"
    VirtualListCtrl-->>wx.ListCtrl: "Texte de l'item"
    wx.ListCtrl->>User: Affiche le texte

3. Description des Composants Clés
Classe VirtualListCtrl
C'est la classe principale du module. Elle hérite de itemctrl.CtrlWithItemsMixin, itemctrl.CtrlWithColumnsMixin, itemctrl.CtrlWithToolTipMixin et wx.ListCtrl.

Méthodes de rappel (Callbacks) pour le mode virtuel
Ces méthodes sont appelées par le backend de wx.ListCtrl chaque fois qu'il a besoin d'informations sur un élément à afficher.

OnGetItemText(rowIndex, columnIndex): Retourne le texte à afficher pour un élément et une colonne donnés.
OnGetItemImage(rowIndex): Retourne l'index de l'image (dans une wx.ImageList) pour l'élément donné.
OnGetItemAttr(rowIndex): Retourne un objet wx.ItemAttr contenant les attributs de style (couleur de fond, couleur du texte, police) pour l'élément. Cela permet de personnaliser l'apparence de chaque ligne.
Gestion des Événements
__init__(..., selectCommand=None, editCommand=None, ...): Le constructeur accepte des commandes (callbacks) qui sont appelées en réponse aux actions de l'utilisateur.
bindEventHandlers(selectCommand, editCommand): Lie les événements wxPython (comme EVT_LIST_ITEM_SELECTED ou EVT_LIST_ITEM_ACTIVATED) aux commandes fournies.
onItemActivated(event): Surchargée pour déterminer sur quelle colonne l'utilisateur a double-cliqué et ajoute cette information à l'événement avant d'appeler editCommand.
Méthodes d'Interaction avec le Parent (Délégation)
getItemWithIndex(rowIndex): Demande au parent l'objet de domaine correspondant à un index de ligne.
getItemText(domainObject, columnIndex): Demande au parent le texte pour un objet de domaine et une colonne.
getItemTooltipData(domainObject): Demande au parent les données pour l'info-bulle d'un objet.
getItemImage(domainObject, columnIndex): Demande au parent l'image pour un objet.
Autres Méthodes Notables
HitTest(point): Surcharge de la méthode de wx.ListCtrl pour retourner non seulement l'index de l'élément et les "flags", mais aussi l'index de la colonne cliquée.
RefreshAllItems(count) / RefreshItems(*items): Permet de notifier le contrôle que les données ont changé et qu'il doit se redessiner.
curselection(), select(items), clear_selection(), select_all(): Méthodes utilitaires pour la gestion de la sélection des éléments.

4. Dépendances
graph TD
    A[VirtualListCtrl] --> B[wx.ListCtrl];
    A --> C[Mixins personnalisés<br>(itemctrl, etc.)];
    A --> D{Parent Widget};

    subgraph wxPython
        B
    end

    subgraph Task Coach Lib
        C
        D
    end

    style D fill:#f9f,stroke:#333,stroke-width:2px

wx.ListCtrl: Classe de base du framework wxPython.
Mixins (itemctrl.*): Fournissent des fonctionnalités réutilisables pour les contrôles d'items
                     de colonnes et d'info-bulles.
Parent Widget: Dépendance la plus critique. Le parent doit implémenter l'API attendue par VirtualListCtrl
               pour la récupération des données (ex: getItemWithIndex, getItemText, getIndexOfItem).
               Ce couplage est basé sur une interface implicite ("duck typing").

5. Exemple d'Utilisation
Voici un exemple conceptuel de la manière dont un widget parent (par exemple, un wx.Panel)
utiliserait VirtualListCtrl.

import wx
# Supposons que VirtualListCtrl et les objets de données (DataObject) sont définis

class MyDataViewer(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        # 1. Nos données (par exemple, une liste d'objets)
        self.data = [DataObject(f"Item {i}") for i in range(10000)]

        # 2. Définition des colonnes
        columns = [Column("Nom"), Column("Valeur")]

        # 3. Création du VirtualListCtrl
        self.list_ctrl = VirtualListCtrl(self, columns,
                                         selectCommand=self.on_item_selected,
                                         editCommand=self.on_item_edited)

        # 4. Configuration du layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # 5. Initialiser le nombre d'éléments
        self.list_ctrl.SetItemCount(len(self.data))

    # --- Implémentation de l'interface pour VirtualListCtrl ---

    def getItemWithIndex(self, rowIndex):
        "Retourne l'objet de données à un index donné."
        return self.data[rowIndex]

    def getIndexOfItem(self, item):
        "Retourne l'index d'un objet de données."
        return self.data.index(item)

    def getItemText(self, item, columnIndex):
        "Retourne le texte pour un item et une colonne."
        if columnIndex == 0:
            return item.name
        elif columnIndex == 1:
            return str(item.value)
        return ""

    def getItemImages(self, item, columnIndex):
        # Retourne des index d'images pour les icônes
        return [0, 0, 0, 0] # Normal, Selected, Expanded, SelectedExpanded

    def getItemTooltipData(self, item):
        "Retourne le texte de l'info-bulle."
        return f"Info pour {item.name}"

    # --- Commandes (callbacks) ---

    def on_item_selected(self, event=None):
        selected_items = self.list_ctrl.curselection()
        print(f"Sélection : {[item.name for item in selected_items]}")

    def on_item_edited(self, event):
        item = self.list_ctrl.GetItem(event.GetIndex())
        print(f"Édition de {item.name} sur la colonne {getattr(event, 'columnName', 'N/A')}")

Cet exemple illustre bien le patron de délégation :
MyDataViewer contient à la fois les données et la logique pour les interpréter,
tandis que VirtualListCtrl se concentre uniquement sur leur affichage efficace.
"""

# from builtins import range
import logging
from taskcoachlib import operating_system
from taskcoachlib.widgets import itemctrl
import wx.lib.mixins.listctrl

# Il serait préférable de remplacer wx.ListCtrl par wx.DataViewCtrl
# (qui est plus moderne et puissant pour les données structurées).
log = logging.getLogger(__name__)


class VirtualListCtrl(
    itemctrl.CtrlWithItemsMixin,
    itemctrl.CtrlWithColumnsMixin,
    itemctrl.CtrlWithToolTipMixin,
    wx.ListCtrl,
):
    """
    Contrôle de liste virtuel personnalisé pour Task Coach.

    Cette classe étend `wx.ListCtrl` en mode virtuel (`wx.LC_VIRTUAL`)
    et combine plusieurs mixins (gestion des items, colonnes et tooltips)
    pour afficher de grandes listes de manière efficace.
    Le contrôle est léger : il ne conserve pas les objets de domaine en mémoire
    mais délègue leur fourniture au parent (principe du "delegate").

    Comportement et responsabilités principales :
      - Fournir les callbacks wx pour le mode virtuel : `OnGetItemText`,
        `OnGetItemImage`, `OnGetItemAttr`, etc.; ces méthodes appellent le
        parent pour obtenir le texte, les images et les attributs d'un item.
      - Gérer la sélection, l'activation (édition) et les info-bulles.
      - Permettre le rafraîchissement coalescé des éléments via
        `scheduleRefresh()` / `RefreshAllItems()`.

    Fonctionnalités principales :
        - Mode virtuel (affichage efficace de milliers d’éléments)
        - Gestion des colonnes et des info-bulles
        - Rafraîchissement partiel ou complet des éléments
        - Sélection multiple et navigation clavier
        - Délégation des événements de sélection et d’édition à des callbacks externes

    Interface requise du parent : le parent doit implémenter (au moins) les
    méthodes suivantes, utilisées par ce contrôle :
        - getItemWithIndex(rowIndex) -> object
        - getIndexOfItem(item) -> int
        - getItemText(item, columnIndex) -> str
        - getItemImages(item, columnIndex) -> list[int]
        - getItemTooltipData(item) -> str
    Args:
        parent (wx.Window): widget parent (souvent un viewer fournissant l'API
            décrite ci-dessus).
        columns (list): liste des colonnes à afficher (objets décrivant les
            colonnes, tels que utilisés par le mixin de colonnes).
        selectCommand (callable|None): callback appelé lors d'une sélection.
        editCommand (callable|None): callback appelé lors d'une activation
            d'élément (double-clic). L'événement transmis peut recevoir un
            attribut `columnName` ajouté par `onItemActivated`.
        itemPopupMenu (wx.Menu|None): menu contextuel pour les items.
        columnPopupMenu (wx.Menu|None): menu contextuel pour les colonnes.
        resizeableColumn (int): index de la colonne redimensionnable par défaut.
        *args, **kwargs: transmis à `wx.ListCtrl`.
    """

    def __init__(
        self,
        parent,
        columns,
        selectCommand=None,
        editCommand=None,
        itemPopupMenu=None,
        columnPopupMenu=None,
        resizeableColumn=0,
        *args,
        **kwargs,
    ):
        """
        Initialise le contrôle virtuel et lie les événements nécessaires.

        Cette méthode configure le contrôle pour fonctionner en mode virtuel et
        relie les événements de sélection et d’édition aux commandes fournies.

        Args:
            parent (wx.Window) : Widget parent.
            columns (list) : Colonnes à afficher.
            selectCommand (callable, optionnel) : Fonction appelée lors de la sélection.
            editCommand (callable, optionnel) : Fonction appelée lors de l’édition (activation).
            itemPopupMenu (wx.Menu, optionnel) : Menu contextuel pour les items.
            columnPopupMenu (wx.Menu, optionnel) : Menu contextuel pour les colonnes.
            resizeableColumn (int) : Colonne redimensionnable par défaut.
        """
        # Ne pas transmettre de kwargs non supportés à wx.ListCtrl.
        # Récupérer le style et l'id si fournis, puis appeler l'initialiseur de
        # la classe de base avec des arguments compatibles.
        style = kwargs.pop("style", wx.LC_REPORT | wx.LC_VIRTUAL)
        listctrl_id = kwargs.pop("id", wx.ID_ANY)
        # Ne pas passer les kwargs "columns", "resizeableColumn",
        # "itemPopupMenu", "columnPopupMenu" à wx.ListCtrl; ils sont gérés
        # par cette classe.
        kwargs.pop("columns", None)
        kwargs.pop("resizeableColumn", None)
        kwargs.pop("itemPopupMenu", None)
        kwargs.pop("columnPopupMenu", None)

        # Initialiser la ListCtrl de façon standard (compatible wxPython)
        super().__init__(parent, id=listctrl_id, style=style)

        # Insérer les colonnes fournis via l'argument `columns`
        try:
            for idx, col in enumerate(columns or []):
                try:
                    label = col.name() if hasattr(col, "name") else str(col)
                except Exception:
                    label = str(col)
                try:
                    self.InsertColumn(idx, label)
                except Exception:
                    # Si InsertColumn n'est pas supporté dans une variante
                    # particulière, on ignore et poursuit.
                    pass

        except Exception:
            # Ignorer toute erreur lors de la création des colonnes
            pass

        self.__parent = parent
        # On ne refresh PAS immédiatement.
        #
        # On planifie un refresh unique via wx.CallAfter
        # et on empêche toute replanification tant qu’il n’est pas exécuté.
        self.__refresh_scheduled = False
        self.__refreshing = (
            False  # Flag to suppress selection events during refresh
        )
        # Stocke le dernier count demandé pour scheduleRefresh
        self.__refresh_count = 0
        self.bindEventHandlers(selectCommand, editCommand)

    def bindEventHandlers(self, selectCommand, editCommand):
        # pylint: disable=W0201
        """
        Lie les gestionnaires d’événements de sélection et d’édition.

        Cette méthode connecte les événements `wx.EVT_LIST_ITEM_*` aux commandes
        de rappel fournies, permettant à l’interface d’interagir avec le parent.

        Args:
            selectCommand (callable | None) : Fonction appelée lors de la sélection.
            editCommand (callable | None) : Fonction appelée lors d’une activation.
        """
        if selectCommand:
            self.selectCommand = selectCommand
            self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onSelect)
            self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect)
            self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelect)
        if editCommand:
            self.editCommand = editCommand
            self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)

    def onSetFocus(self, event):  # pylint: disable=W0613
        """
        Notifie le gestionnaire de fenêtres (AUI) que le contrôle a reçu le focus.

        Ceci est nécessaire pour que le gestionnaire `AuiManager` active correctement
        le panneau contenant ce contrôle.

        Args:
            event (wx.FocusEvent) : Événement de focus.
        """
        # Send a child focus event to let the AuiManager know we received focus
        # so it will activate our pane
        wx.PostEvent(self, wx.ChildFocusEvent(self))
        event.Skip()

    def getItemWithIndex(self, rowIndex):
        """
        Récupère l’objet de domaine correspondant à une ligne donnée.

        Args:
            rowIndex (int) : Index de la ligne.

        Returns:
            object : L’objet métier correspondant.
        """
        return self.__parent.getItemWithIndex(rowIndex)

    def getItemText(self, domainObject, columnIndex):
        """
        Demande au parent le texte à afficher pour une cellule donnée.

        Args:
            domainObject (object) : Objet métier correspondant à la ligne.
            columnIndex (int) : Index de la colonne.

        Returns :
            str : Texte à afficher.
        """
        # return self.__parent.getItemText(domainObject, columnIndex)
        return_itemText = self.__parent.getItemText(domainObject, columnIndex)
        # Utiliser lazy logging pour éviter l'interpolation si le niveau DEBUG n'est pas actif
        log.debug(
            "VirtualListCtrl.getItemText : renvoie %s pour %s colonne %s",
            return_itemText,
            domainObject,
            columnIndex,
        )
        return return_itemText

    def getItemTooltipData(self, domainObject):
        """
        Retourne les données de l’info-bulle pour un élément donné.

        Args:
            domainObject (object): Élément concerné.

        Returns:
            str: Texte de l’info-bulle.
        """
        return self.__parent.getItemTooltipData(domainObject)

    def getItemImage(self, domainObject, columnIndex=0):
        """
        Retourne l’image associée à un élément et une colonne donnés.

        Args:
            domainObject (object): Élément concerné.
            columnIndex (int, optionnel): Index de la colonne.

        Returns:
            int: Index de l’image dans la `wx.ImageList`.
        """
        return self.__parent.getItemImages(domainObject, columnIndex)[
            wx.TreeItemIcon_Normal
        ]

    def OnGetItemText(self, rowIndex, columnIndex):
        """
        Callback wxPython pour obtenir le texte d’un élément virtuel.

        Appelé automatiquement par le moteur de rendu du `ListCtrl`
        lorsqu’il doit afficher une cellule spécifique.

        Args:
            rowIndex (int): Ligne demandée.
            columnIndex (int): Colonne demandée.

        Returns:
            str: Texte à afficher.
        """
        item = self.getItemWithIndex(rowIndex)
        return self.getItemText(item, columnIndex)

    def OnGetItemTooltipData(self, rowIndex, columnIndex):
        """
        Retourne les données de l’info-bulle pour un élément donné.

        Args:
            rowIndex (int): Ligne demandée.
            columnIndex (int): Colonne demandée.

        Returns:

        """
        item = self.getItemWithIndex(rowIndex)
        return self.getItemTooltipData(item)

    def OnGetItemImage(self, rowIndex):
        """
        Retourne l’image associée à un élément donné.
        """
        item = self.getItemWithIndex(rowIndex)
        return self.getItemImage(item)

    def OnGetItemColumnImage(self, rowIndex, columnIndex):
        """
        Retourne l’image associée à un élément pour une colonne donnée.
        """
        item = self.getItemWithIndex(rowIndex)
        return self.getItemImage(item, columnIndex)

    def OnGetItemAttr(self, rowIndex):
        """
        Définit les attributs visuels pour une ligne donnée.
        """
        item = self.getItemWithIndex(rowIndex)
        foreground_color = item.foregroundColor(recursive=True)
        background_color = item.backgroundColor(recursive=True)
        item_attribute_arguments = [foreground_color, background_color]
        font = item.font(recursive=True)
        if font is None:
            # FIXME: Is the right way to get the font here?
            # wxItemAttr required a font for initialization, so we give one
            font = self.GetFont()
        if font:
            item_attribute_arguments.append(font)
        # We need to keep a reference to the item attribute to prevent it
        # from being garbage collected too soon:
        # self.__item_attribute = wx.ListItemAttr(
        #     *item_attribute_arguments)  # pylint: disable=W0142,W0201
        self.__item_attribute = wx.ItemAttr(
            *item_attribute_arguments
        )  # pylint: disable=W0142,W0201
        return self.__item_attribute

    def onSelect(self, event):
        """
        Callback wxPython pour gérer l’événement de sélection d’un élément.
        """
        event.Skip()
        self.selectCommand(event)

    def onItemActivated(self, event):
        """
        Remplacer le comportement par défaut pour attacher la colonne sur laquelle vous avez cliqué
        à l'événement afin que nous puissions l'utiliser ailleurs.
        """
        window = self.GetMainWindow()
        if operating_system.isMac():
            window = window.GetChildren()[0]
        mouse_position = window.ScreenToClient(wx.GetMousePosition())
        index, dummy_flags, column = self.HitTest(mouse_position)
        if index >= 0:
            # Only get the column name if the hittest returned an item,
            # otherwise the item was activated from the menu or by double
            # clicking on a portion of the tree view not containing an item.
            column = max(0, column)  # FIXME: Why can the column be -1?
            event.columnName = self._getColumn(
                column
            ).name()  # pylint: disable=E1101
        self.editCommand(event)

    def RefreshAllItems(self, count):
        """Mettre à jour tous les éléments de la liste."""
        # Marquer que l'on rafraîchit afin d'éviter certains événements
        self.__refreshing = True
        try:
            self.SetItemCount(count)
            if count == 0:
                self.DeleteAllItems()
            else:
                # The VirtualListCtrl makes sure only visible items are updated
                super().RefreshItems(0, count - 1)
        finally:
            # Toujours réinitialiser le flag et notifier la sélection
            self.__refreshing = False
            try:
                self.selectCommand()
            except Exception:
                # Préserver l'ancien comportement : loguer mais continuer
                log.exception(
                    "VirtualListCtrl.RefreshAllItems : erreur lors de selectCommand"
                )

    def RefreshItems(self, *items):
        """Actualisez des éléments spécifiques."""
        if len(items) <= 7:
            for item in items:
                self.RefreshItem(self.__parent.getIndexOfItem(item))
        else:
            self.RefreshAllItems(self.GetItemCount())

    def HitTest(self, xxx_todo_changeme, *args, **kwargs):
        """Always return a three-tuple (item, flag, column)."""
        x, y = xxx_todo_changeme
        index, flags = super().HitTest((x, y), *args, **kwargs)  # TODO
        column = 0
        if self.InReportView():
            # Determine the column in which the user clicked
            cumulative_column_width = 0
            for column_index in range(self.GetColumnCount()):
                # # self.viewer.widget._columns ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
                # # ListCtrl a GetColumnCount()
                # for column_index in range(len(self._columns)):
                cumulative_column_width += self.GetColumnWidth(column_index)
                if x <= cumulative_column_width:
                    column = column_index
                    break
        return index, flags, column

    def curselection(self):
        """Retourne la liste des éléments sélectionnés."""
        return [
            self.getItemWithIndex(index)
            for index in self.__curselection_indices()
        ]

    def select(self, items):
        """Sélectionnez les éléments spécifiés."""
        indices = [self.__parent.getIndexOfItem(item) for item in items]
        for index in range(self.GetItemCount()):
            self.Select(index, index in indices)
        if self.curselection():
            self.Focus(self.GetFirstSelected())

    def clear_selection(self):
        """Désélectionnez tous les éléments sélectionnés."""
        for index in self.__curselection_indices():
            self.Select(index, False)

    def select_all(self):
        """Sélectionnez tous les éléments."""
        for index in range(self.GetItemCount()):
            self.Select(index)

    def __curselection_indices(self):
        """Renvoie les indices des éléments actuellement sélectionnés."""
        return wx.lib.mixins.listctrl.getListCtrlSelection(self)

    def scheduleRefresh(self, count=0):
        """Programme un rafraîchissement différé pour éviter les multiples appels à RefreshAllItems().

        Planifie un rafraîchissement différé (coalescing) pour éviter les rebuilds multiples.

        La méthode évite les rafraîchissements redondants
        en gardant un flag __refresh_scheduled.
        Lors de l'ordonnancement, elle posera le flag,
        et exécutera finalement RefreshAllItems pour reconstruire l'arbre.
        forceRefresh() réinitialise le flag et force la replanification.
        Usage : appeler `scheduleRefresh(count)` à chaque fois que le modèle
        de données a changé. Les appels rapides successifs seront coalescés en
        un seul rafraîchissement effectif pour éviter les rebuilds coûteux.
        """

        log.debug(
            "TreeListCtrl.scheduleRefresh : début du rafraîchissement différé."
        )
        # Si un rafraîchissement est déjà planifié, ne rien faire (coalescing)
        if self.__refresh_scheduled:
            log.debug("TreeListCtrl.scheduleRefresh : déjà planifié !")
            # Mettre à jour le count demandé si nécessaire
            try:
                current = getattr(self, "_VirtualListCtrl__refresh_count", 0)
                self.__refresh_count = max(current, count)
            except Exception:
                # Si l'attribut ne peut être mis à jour, on ignore silencieusement
                pass
            return

        # Marquer comme planifié et stocker le count demandé
        self.__refresh_scheduled = True
        self.__refresh_count = max(
            getattr(self, "_VirtualListCtrl__refresh_count", 0), count
        )

        def doRefresh():
            """Exécute le refresh planifié. Garantit la réinitialisation du flag.

            Doit toujours remettre `__refresh_scheduled` à False, même en cas
            d'exception ou si l'objet C++ a été détruit.
            """
            try:
                # Protection contre la destruction de l'objet (objet native supprimé)
                try:
                    # Accessing self may raise RuntimeError if the underlying C++
                    # object was destroyed; capture et sortir proprement.
                    _ = self.GetId()
                except RuntimeError:
                    log.warning(
                        "TreeListCtrl.doRefresh : objet GUI déjà supprimé."
                    )
                    return

                # Utiliser le count le plus récent demandé, ou le nombre actuel
                count_to_use = (
                    getattr(self, "_VirtualListCtrl__refresh_count", 0)
                    or self.GetItemCount()
                )
                log.debug(
                    "TreeListCtrl.doRefresh : exécution du rafraîchissement avec count=%s.",
                    count_to_use,
                )
                # Appeler RefreshAllItems avec le count désiré
                try:
                    self.RefreshAllItems(count_to_use)
                except Exception:  # pylint: disable=broad-except
                    # En dernier recours, appeler sans argument
                    try:
                        self.RefreshAllItems(self.GetItemCount())
                    except Exception:  # pylint: disable=broad-except
                        log.exception(
                            "TreeListCtrl.doRefresh : échec du RefreshAllItems"
                        )
            finally:
                # Toujours réinitialiser l'état planifié
                try:
                    self.__refresh_scheduled = False
                    self.__refresh_count = 0
                except Exception:
                    # Ignorer les erreurs de nettoyage
                    pass

        # Planifier l'exécution différée (wx.CallAfter afin d'exécuter dans la boucle d'événements)
        try:
            wx.CallAfter(doRefresh)
        except Exception:
            # En cas d'impossibilité d'utiliser CallAfter, exécuter directement
            log.debug(
                "TreeListCtrl.scheduleRefresh : wx.CallAfter indisponible, exécution synchrone."
            )
            doRefresh()
        log.debug("TreeListCtrl.scheduleRefresh : rafraîchissement planifié.")
        #     # le widget est encore à 20×20 pixels,
        #     # donc RefreshAllItems s'exécute mais le widget n'est pas encore dans sa taille finale.
        #     # Quand la fenêtre s'agrandit après, aucun nouveau refresh n'est planifié.

        # # Important : ici after doit être celui de ton widget Tkinter.
        # self.after(1, doRefresh)
        # Utilisation de wx.CallAfter pour wxPython
        # wx.CallAfter(doRefresh)
        # log.debug(
        #     "TreeListCtrl.doRefresh : exécution du rafraîchissement planifié."
        # )
        # self.__refresh_scheduled = False
        # self.RefreshAllItems(count)
        # log.debug(
        #     f"TreeListCtrl.scheduleRefresh : fin du rafraîchissement planifié différé !"
        # )
