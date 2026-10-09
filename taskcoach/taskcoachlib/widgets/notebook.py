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
"""

import logging
import wx
from wx.lib.agw import aui

# import wx.lib.agw.aui as aui
import wx.lib.scrolledpanel as scrolledpanel

log = logging.getLogger(__name__)  # Logger pour ce fichier


class GridCursor:
    """
    Classe utilitaire pour aider lors de l’ajout de contrôles à un GridBagSizer.

    Attributes :
        __columns (int) : Le nombre de colonnes dans la grille.
        __nextPosition (tuple) : Position suivante pour ajouter un contrôle.
    """

    def __init__(self, columns):
        """
        Initialisez l'instance GridCursor.

        Args :
            columns (int) : Le nombre de colonnes dans la grille.
        """
        self.__columns = columns
        self.__nextPosition = (0, 0)

    def __updatePosition(self, colspan):
        """
        Met à jour la position du curseur en tenant compte de colspan.

        Args :
            colspan (int) : Nombre de colonnes couvertes (spanned) par le contrôle.
        """
        row, column = self.__nextPosition
        if column == self.__columns - colspan:
            row += 1
            column = 0
        else:
            column += colspan
        self.__nextPosition = (row, column)

    def next(self, colspan=1):
        """
        Obtenez la position suivante pour un contrôle.

        Args :
            colspan (int) : (optional) Le nombre de colonnes couvertes (spanned) par le contrôle. Defaults à 1.

        Returns :
            (tuple) : La prochaine position (row, column).
        """
        row, column = self.__nextPosition
        self.__updatePosition(colspan)
        return row, column

    def maxRow(self):
        """
        Obtenir l'index de ligne maximum.

        Returns:
            (int) : L'index de ligne maximum.
        """
        row, column = self.__nextPosition
        return max(0, row - 1) if column == 0 else row


class BookPage(wx.Panel):
    """
    Une page dans un cahier (notebook).

    Attributes :
        _sizer (wx.GridBagSizer) : Le sizer pour organiser les contrôles.
        _columns (int) : Le nombre de colonnes dans la grille.
        _position (GridCursor) : Le curseur pour les contrôles de positionnement.
        _growableColumn (int) : L'index de la colonne extensible.
        _borderWidth (int) : La largeur de la bordure autour des contrôles.
    """

    # Outer margin around page content (modern UI best practice: 10-12px)
    _outerMargin = 10
    # Grid spacing - subclasses can override
    _vgap = 0
    _hgap = 5
    _borderWidth = 5

    def __init__(self, parent, columns, growableColumn=None, *args, **kwargs):
        """
        Initialise l'instance BookPage.

        Args :
            parent (wx.Window) : La fenêtre parente.
            *args : Liste d’arguments de longueur variable.
            columns (int) : Le nombre de colonnes dans la grille.
            growableColumn (int, optional) : L'index de la colonne augmentable. Defaults to None.
            **kwargs : Arguments de mots clés arbitraires.
        """
        # --- LOG 1 : À l'entrée de __init__ de BookPage ---
        log.debug(f"--- BookPage.__init__ entrée ---")
        log.debug(f"  parent (reçu par BookPage): {parent}")
        log.debug(f"  *args (reçus par BookPage): {args}")
        log.debug(f"  columns (arg direct): {columns}")
        log.debug(f"  growableColumn (arg direct): {growableColumn}")
        log.debug(f"  **kwargs (reçus par BookPage): {kwargs}")

        # --- LOG 2 : Avant les pop de kwargs ---
        log.debug(f"  BookPage.__init__ - kwargs avant les pops: {kwargs}")
        # Récupère la valeur de 'columns' et 'growableColumn' des kwargs s'ils y sont,
        # sinon utilise les valeurs par défaut définies dans la signature (__init__ arguments).
        _columns_val = kwargs.pop("columns", columns)
        _growable_column_val = kwargs.pop("growableColumn", growableColumn)
        # --- LOG 3 : Après les pop de kwargs ---
        log.debug(f"  BookPage.__init__ - kwargs après les pops: {kwargs}")
        log.debug(
            f"  BookPage.__init__ - Valeur extraite _columns_val: {_columns_val}"
        )
        log.debug(
            f"  BookPage.__init__ - Valeur extraite _growable_column_val: {_growable_column_val}"
        )

        # Assurez-vous d'avoir une valeur par défaut si 'columns' n'est pas passé du tout.
        # Par exemple, si vous voulez que 2 soit la valeur par défaut pour BookPage:
        if _columns_val is None:
            _columns_val = (
                2  # Valeur par défaut pour BookPage si non spécifiée
            )
            # --- LOG 4 : Quand _columns_val est mis par défaut ---
            log.debug(
                f"  BookPage.__init__ - _columns_val mis par défaut à: {_columns_val}"
            )

        # --- LOG 5 : Avant l'appel à super().__init__ (wx.Panel) ---
        log.debug(
            f"  BookPage.__init__ - Appel de super().__init__ (wx.Panel) avec:"
        )
        log.debug(f"    parent passé à super: {parent}")
        log.debug(f"    style passé à super: {wx.TAB_TRAVERSAL}")
        log.debug(f"    *args passés à super: {args}")
        log.debug(f"    **kwargs passés à super: {kwargs}")
        # Appelle le constructeur de la super-classe (wx.Panel),
        # en passant les arguments génériques restants (*args, **kwargs)
        super().__init__(parent, style=wx.TAB_TRAVERSAL, *args, **kwargs)
        # --- LOG 6 : Après l'appel à super().__init__ (wx.Panel) ---
        log.debug(
            f"--- BookPage.__init__ super().__init__ (wx.Panel) terminé ---"
        )

        # Affectez les valeurs consommées aux attributs internes
        # self._columns = columns
        # self._position = GridCursor(columns)
        self._columns = _columns_val
        self._position = GridCursor(
            self._columns
        )  # Utilise la valeur correcte
        # if growableColumn is None:
        if _growable_column_val is None:
            # self._growableColumn = columns - 1
            self._growableColumn = (
                self._columns - 1
            )  # Le calcul est maintenant sûr

        else:
            # self._growableColumn = growableColumn
            self._growableColumn = _growable_column_val
        self._borderWidth = 5
        self._sizer = wx.GridBagSizer(
            vgap=5, hgap=5
        )  # type de sizer pour organiser ses contrôles
        # --- LOG 7 : Après l'initialisation des attributs de BookPage ---
        log.debug(
            f"  BookPage.__init__ - self._columns final: {self._columns}"
        )
        log.debug(f"--- BookPage.__init__ terminé ---")

    def fit(self):
        """
        Régle le dimensionneur et ajuste le panneau à son contenu.
        """
        self.SetSizerAndFit(self._sizer)
        # # Wrap GridBagSizer in outer BoxSizer with margins for proper spacing
        # # Only create the outer sizer once - calling fit() multiple times is safe
        # if not hasattr(self, '_outerSizer') or self._outerSizer is None:
        #     self._outerSizer = wx.BoxSizer(wx.VERTICAL)
        #     self._outerSizer.Add(self._sizer, 1, wx.EXPAND | wx.ALL, self._outerMargin)
        #     self.SetSizer(self._outerSizer)
        # self.Layout()  # Force layout recalculation (needed on Windows for lazy-loaded pages)

    def __defaultFlags(self, controls):
        """
        Renvoie les indicateurs par défaut pour placer une liste de contrôles.

        Args :
            controls (list) : La liste des contrôles.

        Returns :
            (list) : La liste des indicateurs par défaut.
        """
        labelInFirstColumn = type(controls[0]) in [type(""), type("")]
        # TODO: essayer:
        # labelInFirstColumn = isinstance(controls[0], str)
        flags = []
        for columnIndex in range(len(controls)):
            flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL
            if columnIndex == 0 and labelInFirstColumn:
                flag |= wx.ALIGN_LEFT
            else:
                flag |= wx.ALIGN_RIGHT | wx.EXPAND
            flags.append(flag)
        return flags

    def __determineFlags(self, controls, flagsPassed):
        """
        Renvoie une liste fusionnée d'indicateurs en remplaçant les indicateurs par défaut par les indicateurs transmis par l'appelant.

        Args :
            controls (list) : La liste des contrôles.
            flagsPassed (list or None) : La liste des indicateurs transmis par l'appelant.

        Returns :
            (list) : La liste des drapeaux fusionnés(merged).
        """
        flagsPassed = flagsPassed or [None] * len(controls)
        # flagsPassed = (flagsPassed or [None]) * len(controls)
        # ou
        # flagsPassed = flagsPassed or ([None] * len(controls))

        # TODO : try to replaced by:
        # if not isinstance(flagsPassed, list):
        #     flagsPassed = [flagsPassed] * len(controls)
        #
        defaultFlags = self.__defaultFlags(controls)
        return [
            defaultFlag if flagPassed is None else flagPassed
            for flagPassed, defaultFlag in zip(flagsPassed, defaultFlags)
        ]  # TypeError: 'Alignment' object is not iterable

    def addEntry(self, *controls, **kwargs):
        """
        Ajoute un certain nombre de contrôles à la page. Tous les contrôles sont placés sur une seule ligne et forment ensemble une seule entrée.

        Par exemple, une étiquette, un champ de texte et une étiquette explicative. Les indicateurs par défaut
        pour placer les contrôles peuvent être remplacés en
        fournissant un paramètre de mot-clé « flags ». les drapeaux doivent être une liste de drapeaux
        (wx.ALIGN_LEFT et autres). La liste peut
        contenir Aucun pour les contrôles qui doivent être placés à l'aide de l'indicateur par défaut.
        Si la liste des indicateurs est plus courte que le nombre de contrôles,
        elle est étendue avec autant de « Aucun » que nécessaire.
        Ainsi, addEntry (aLabel, aTextCtrl, flags=[None, wx.ALIGN_LEFT])
        le fera. placez l'étiquette avec le drapeau par défaut et placera le textCtrl
        aligné à gauche.

        Args :
            *controls : Liste de contrôles de longueur variable.
            **kwargs : Arguments de mots clés arbitraires, notamment :
                - flags (list) : Liste des drapeaux pour placer les contrôles.
                - growable (bool) : Indique si la ligne doit pouvoir être développée.
        """
        flags = self.__determineFlags(controls, kwargs.get("flags", None))
        controls = [
            self.__createStaticTextControlIfNeeded(control)
            for control in controls
            if control is not None
        ]
        lastColumnIndex = len(controls) - 1
        # Itère sur les contrôles (libellé, puis champ de texte) :
        for columnIndex, control in enumerate(controls):
            self.__addControl(  # Pour chaque contrôle, ajoute un contrôle au sizer
                columnIndex,  # 0 pour le libellé, 1 pour le contrôle
                control,  # l'objet wx.StaticText, puis le wx.TextCtrl
                flags[
                    columnIndex
                ],  # flags[0] pour le libellé, flags[1] pour le contrôle
                lastColumn=columnIndex == lastColumnIndex,
            )
            if columnIndex > 0:
                control.MoveAfterInTabOrder(controls[columnIndex - 1])
        if kwargs.get("growable", False):
            self._sizer.AddGrowableRow(self._position.maxRow())
        # Move growable column definition here
        # There are asserts to fail if the column is already
        # marked growable or if there is no column yet created
        if (
            self._growableColumn > -1
            and self._growableColumn >= lastColumnIndex
        ):
            self._sizer.AddGrowableCol(self._growableColumn)
            self._growableColumn = -1

    def addLine(self):
        """
        Ajoutez une ligne horizontale à la page.
        """
        line = wx.StaticLine(self)
        self.__addControl(
            0, line, flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL, lastColumn=True
        )

    def __addControl(self, columnIndex, control, flag, lastColumn):
        """
        Ajoutez un contrôle au sizer.

        Place les éléments dans des colonnes spécifiques de la grille.

        Args :
            columnIndex (int) : L'index de la colonne.
            control (wx.Window) : Le contrôle à ajouter.
            flag (int) : Les drapeaux pour placer le contrôle.
            lastColumn (bool) : Si le contrôle est dans la dernière colonne.
        """
        colspan = max(self._columns - columnIndex, 1) if lastColumn else 1
        # Le calcul de la position et l'avancement du curseur :
        position = self._position.next(colspan)
        #
        # # Sortie de débogage pour vérifier les valeurs transmises
        logging.debug(
            f"notebook.py:Adding control : {control}, Position: {position}, Span: {(1, colspan)}, Flag: {flag}, Border: {self._borderWidth}"
        )
        #
        # # Assurez-vous que l'indicateur est un entier
        # if isinstance(flag, tuple):
        #     flag = flag[0]  # Extraire le premier élément s'il s'agit d'un tuple

        self._sizer.Add(
            control,
            position,
            # self._position.next(colspan),
            span=(1, colspan),
            flag=flag,
            border=self._borderWidth,
        )

    def __createStaticTextControlIfNeeded(self, control):
        """
        Créez un contrôle StaticText si le contrôle donné est une chaîne.

        Args :
            control : Le contrôle ou la chaîne.

        Returns :
            control (wx.Window) : Le contrôle.
        """
        if type(control) in [
            type(""),
            type(""),
        ]:  # TODO: essayer de le remplacer par
            # if isinstance(control, str):
            # ou
            # if isinstance(control, list):
            control = wx.StaticText(self, label=control)
        return control


class ScrolledBookPage(scrolledpanel.ScrolledPanel):
    """A scrollable page in a notebook. Use for pages with lots of content."""

    # Outer margin around page content
    _outerMargin = 10
    # Grid spacing - subclasses can override
    _vgap = 0
    _hgap = 5
    _borderWidth = 5

    def __init__(self, parent, columns, growableColumn=None, *args, **kwargs):
        super().__init__(parent, style=wx.TAB_TRAVERSAL, *args, **kwargs)
        self._sizer = wx.GridBagSizer(vgap=self._vgap, hgap=self._hgap)
        self._columns = columns
        self._position = GridCursor(columns)
        if growableColumn is None:
            self._growableColumn = columns - 1
        else:
            self._growableColumn = growableColumn

    def fit(self):
        # Wrap GridBagSizer in outer BoxSizer with margins for proper spacing
        if not hasattr(self, "_outerSizer") or self._outerSizer is None:
            self._outerSizer = wx.BoxSizer(wx.VERTICAL)
            self._outerSizer.Add(
                self._sizer, 1, wx.EXPAND | wx.ALL, self._outerMargin
            )
            self.SetSizer(self._outerSizer)
        self.SetupScrolling(scroll_x=True, scroll_y=True)
        self.Layout()

    def __defaultFlags(self, controls):
        """Return the default flags for placing a list of controls."""
        flags = []
        for columnIndex in range(len(controls)):
            flag = wx.ALL | wx.ALIGN_TOP | wx.ALIGN_LEFT
            flags.append(flag)
        return flags

    def __determineFlags(self, controls, flagsPassed):
        """Return a merged list of flags by overriding the default
        flags with flags passed by the caller."""
        flagsPassed = flagsPassed or [None] * len(controls)
        defaultFlags = self.__defaultFlags(controls)
        return [
            defaultFlag if flagPassed is None else flagPassed
            for flagPassed, defaultFlag in zip(flagsPassed, defaultFlags)
        ]

    def addEntry(self, *controls, **kwargs):
        """Add controls to the page on one row."""
        flags = self.__determineFlags(controls, kwargs.get("flags", None))
        controls = [
            self._ScrolledBookPage__createStaticTextControlIfNeeded(control)
            for control in controls
            if control is not None
        ]
        lastColumnIndex = len(controls) - 1
        for columnIndex, control in enumerate(controls):
            self._ScrolledBookPage__addControl(
                columnIndex,
                control,
                flags[columnIndex],
                columnIndex == lastColumnIndex,
            )
        if kwargs.get("growable", False):
            self._sizer.AddGrowableRow(self._position.maxRow())
        # Add growable column once, when first entry has been added
        if (
            self._growableColumn >= 0
            and self._sizer.GetItemCount() >= self._columns
        ):
            self._sizer.AddGrowableCol(self._growableColumn)
            self._growableColumn = -1

    def addLine(self):
        line = wx.StaticLine(self)
        colspan = max(self._columns, 1)
        self._sizer.Add(
            line,
            self._position.next(colspan),
            span=(1, colspan),
            flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM,
            border=5,
        )

    def __addControl(self, columnIndex, control, flag, lastColumn):
        colspan = max(self._columns - columnIndex, 1) if lastColumn else 1
        self._sizer.Add(
            control,
            self._position.next(colspan),
            span=(1, colspan),
            flag=flag,
            border=self._borderWidth,
        )

    def __createStaticTextControlIfNeeded(self, control):
        if type(control) in [type(""), type("")]:
            control = wx.StaticText(self, label=control)
        return control


class BookMixin(object):
    """
    Classe Mixin pour les composants *book.

    Attributes :
        _bitmapSize (tuple) : La taille du bitmap.
        pageChangedEvent (str) : L'événement pour les changements de page.
    """

    _bitmapSize = (16, 16)
    pageChangedEvent = "Subclass responsibility"

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize the BookMixin instance.

        Args:
            parent (wx.Window): The parent window.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(parent, id=-1, *args, **kwargs)
        self.Bind(self.pageChangedEvent, self.onPageChanged)

    def __getitem__(self, index):
        """
        Obtenez une page spécifique par index.

        Manière plus pythonique d'obtenir une page spécifique, également utile pour itérer
        sur toutes les pages, par exemple : pour la page du cahier : ...

        Args :
            index (int) : L'index de la page.

        Returns :
            (wx.Window) : La page.

        Raises :
            IndexError : Si l'index est hors de portée.
        """
        if (
            index < self.GetPageCount()
        ):  # Unresolved attribute reference 'GetPageCount' for class 'BookMixin'
            return self.GetPage(
                index
            )  # Unresolved attribute reference 'GetPage' for class 'BookMixin'
            # Normal, c'est un mixin !
        else:
            raise IndexError

    def onPageChanged(self, event):
        """
        Gérer l’événement de modification de page. Peut être remplacé dans une sous-classe pour faire quelque chose d'utile.

        Args :
            event (wx.Event) : Événement de changement de page.
        """
        event.Skip()

    def AddPage(self, page, name, bitmap=None):
        """
        Remplace AddPage pour permettre de spécifier simplement le nom du bitmap.

        Args :
            page (wx.Window) : La page à ajouter.
            name (str) : Le nom de la page.
            bitmap (str, optional) : Le nom du bitmap. La valeur par défaut est None (Aucun).
        """
        bitmap = wx.ArtProvider.GetBitmap(
            bitmap, wx.ART_MENU, self._bitmapSize
        )
        super().AddPage(
            page, name, bitmap=bitmap
        )  # Unresolved attribute reference 'AddPage' for class 'object'

    def ok(self, *args, **kwargs):
        """
        Effectuez l'action « ok » pour toutes les pages.

        Args :
            *args : Liste d’arguments de longueur variable.
            **kwargs : Arguments de mots clés arbitraires.
        """
        for page in self:
            page.ok(
                *args, **kwargs
            )  # Unresolved attribute reference 'ok' for class 'Window'


class Notebook(BookMixin, aui.AuiNotebook):
    """
    Un Notebook doté de fonctionnalités AUI (Advanced User Interface).

    Attributes :
        pageChangedEvent (str) : L'événement pour les changements de page.
    """

    pageChangedEvent = aui.EVT_AUINOTEBOOK_PAGE_CHANGED

    def __init__(self, *args, **kwargs):
        """
        Initialise l'instance Notebook.

        Args:
            *args: Liste d’arguments de longueur variable.
            **kwargs: Arguments de mots clés arbitraires.
        """
        defaultStyle = kwargs.get("agwStyle", aui.AUI_NB_DEFAULT_STYLE)
        kwargs["agwStyle"] = (
            defaultStyle
            & ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
            & ~aui.AUI_NB_MIDDLE_CLICK_CLOSE
        )
        super().__init__(*args, **kwargs)
        # Bind mouse wheel directly on the tab control for tab scrolling
        tabCtrl = self.GetActiveTabCtrl()
        if tabCtrl:
            tabCtrl.Bind(wx.EVT_MOUSEWHEEL, self.__onTabMouseWheel)
        # Disable focus on internal AUI TabFrame to prevent "lost" tab keypress
        self.__disableTabFrameFocus()

    def __disableTabFrameFocus(self):
        """Disable focus on internal AUI TabFrame windows."""
        for child in self.GetChildren():
            if child.__class__.__name__ == "TabFrame":
                child.SetCanFocus(False)

    def __onTabMouseWheel(self, event):
        """Handle mouse wheel scrolling on the tab bar to switch tabs."""
        rotation = event.GetWheelRotation()
        if rotation > 0:
            self.AdvanceSelection(False)  # Previous tab
        elif rotation < 0:
            self.AdvanceSelection(True)  # Next tab

    def AdvanceSelectionForward(self):
        """Move to the next tab (wraps around)."""
        self.AdvanceSelection(True)

    def AdvanceSelectionBackward(self):
        """Move to the previous tab (wraps around)."""
        self.AdvanceSelection(False)
