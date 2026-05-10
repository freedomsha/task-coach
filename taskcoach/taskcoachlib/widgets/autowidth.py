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

Module `autowidth.py`

Ce module fournit le mixin `AutoColumnWidthMixin`, qui permet de redimensionner
automatiquement une colonne dans un contrôle à colonnes (par exemple, `wx.ListCtrl`,
`wx.TreeListCtrl`, ou `wx.lib.agw.hypertreelist.HyperTreeList`).

Fonctionnalités principales :
- Ajuste dynamiquement la largeur d'une colonne pour utiliser tout l'espace
  disponible sans créer d'espace inutile ou de barres de défilement horizontales.
- Gère les événements comme le redimensionnement ou le glissement des colonnes.

Dépendances :
- wxPython : Ce mixin suppose que les classes qui l'utilisent héritent de
  `wx.Window` ou de contrôles similaires (`wx.ListCtrl`, `wx.TreeListCtrl`).

Classes :
- `AutoColumnWidthMixin` : Fournit le comportement de redimensionnement
  automatique des colonnes.

Avertissements :
- Lorsque vous utilisez ce mixin, assurez-vous que votre contrôle est configuré
  pour un mode "rapport" (report mode) si nécessaire.
- Si vous surchargez `EVT_SIZE`, appelez `event.Skip()` pour garantir que la
  méthode `OnResize` du mixin est appelée.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.
"""

# from __future__ import division
#
# from builtins import range
# from builtins import object
# from past.utils import old_div
import logging
import os
import wx
from wx.lib.agw import hypertreelist

# from wx.lib.agw.hypertreelist import HyperTreeList
# from wx.lib.agw.hypertreelist.HyperTreeList import GetColumnWidth
# from wx.lib.agw.hypertreelist import HyperTreeList
# try:
#    from ..thirdparty import hypertreelist
# except ImportError:
#    from ..thirdparty.agw import hypertreelist

from taskcoachlib import operating_system

log = logging.getLogger(__name__)


class AutoColumnWidthMixin(object):
    """Mixin pour ajouter un redimensionnement automatique des colonnes dans un contrôle.

    Ce mixin ajuste dynamiquement la largeur d'une colonne spécifique pour
    occuper tout l'espace disponible du contrôle, en réduisant ou en évitant
    les barres de défilement horizontales.

    Une classe mixte qui redimensionne automatiquement une colonne pour occuper
    la largeur restante d'un contrôle avec des colonnes (c'est-à-dire ListCtrl,
    TreeListCtrl).

    Cela amène le contrôle à occuper automatiquement la totalité width
    disponible, sans barre de défilement horizontale (sauf si absolument
    nécessaire) ni espace vide à droite de la dernière colonne.

    REMARQUE : Lorsque vous utilisez ce mixin avec un ListCtrl, assurez-vous que ListCtrl
               est en mode rapport.

    AVERTISSEMENT : Si vous remplacez l'événement EVT_SIZE dans votre contrôle, assurez-vous
                    d'appeler event.Skip() pour garantir que la méthode OnResize du mixin
                    est appelée.

    Attributs :
        ResizeColumn (int) : Index de la colonne à redimensionner automatiquement.
        ResizeColumnMinWidth (int) : Largeur minimale de la colonne redimensionnable.
        __is_auto_resizing (bool) : Indique si le redimensionnement automatique est activé.

    Méthodes principales :
        - `SetResizeColumn` : Définit la colonne à redimensionner automatiquement.
        - `ToggleAutoResizing` : Active ou désactive le redimensionnement automatique.
        - `OnResize` : Gère l'événement de redimensionnement de la fenêtre.
        - `DoResize` : Effectue le calcul et applique les nouvelles largeurs de colonnes.
        - `DistributeWidthAcrossColumns` : Répartit l'espace supplémentaire ou manquant
          sur les colonnes non redimensionnables.

    Remarque :
    Ce mixin dépend des méthodes suivantes, qui doivent être disponibles dans
    la classe finale :
        - `Bind`, `Unbind` : Gestion des événements wxPython.
        - `GetColumnWidth`, `SetColumnWidth` : Gestion des colonnes.
        - `GetColumnCount` : Nombre total de colonnes.-> Remplacé par len(self._columns) !
        - `GetClientSize`, `GetSize` : Dimensions du contrôle.

    Les méthodes comme Bind, Unbind, GetColumnWidth, etc., dépendent de wxPython.
    Ce mixin doit être utilisé dans des classes héritant de wx.ListCtrl,
    wx.TreeListCtrl, ou wx.lib.agw.hypertreelist.HyperTreeList.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise le mixin avec des paramètres spécifiques.

        Args :
            resizeableColumn (int) : Index de la colonne à redimensionner
                                     automatiquement (par défaut : -1).
            resizeableColumnMinWidth (int) : Largeur minimale de la colonne
                                             redimensionnable (par défaut : 50).
        """
        log.debug(
            "AutoColumnWidthMixin.__init__ : initialisation du Mixin pour ajouter un redimensionnement automatique des colonnes dans un contrôle."
        )
        self.__is_auto_resizing = False
        self.__header_window = None
        self.__resize_cursor = wx.Cursor(wx.CURSOR_SIZEWE)
        self.__no_entry_cursor = wx.Cursor(wx.CURSOR_NO_ENTRY)
        self.__current_cursor = wx.STANDARD_CURSOR
        self.ResizeColumn = kwargs.pop("resizeableColumn", -1)
        self.ResizeColumnMinWidth = kwargs.pop("resizeableColumnMinWidth", 50)
        super().__init__(
            *args, **kwargs
        )  # TODO : Rendre le mixin non-coopératif ! ?
        log.debug("AutoColumnWidthMixin initialisé !")

    def SetResizeColumn(self, column):
        """
        Définit la colonne à redimensionner automatiquement.

        Args :
            column (int) : Index de la colonne.
        """
        self.ResizeColumn = column

    # def ToggleAutoResizing(self, on):
    def ToggleAutoResizing(self, on=True):
        """
        Active ou désactive le redimensionnement automatique des colonnes.

        Args :
            on (bool) : Si `True`, active le redimensionnement automatique.
        """
        if on == self.__is_auto_resizing:
            return
        self.__is_auto_resizing = on
        if on:
            self.Bind(wx.EVT_SIZE, self.OnResize)  # wx.PyEventBinder.Bind
            self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnBeginColumnDrag)
            self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnEndColumnDrag)
            # self.DoResize()
            self._bindHeaderMotion()
            wx.CallAfter(self.DoResize)
        else:
            self.Unbind(wx.EVT_SIZE)  # wx.PyEventBinder.Unbind
            self.Unbind(wx.EVT_LIST_COL_BEGIN_DRAG)
            self.Unbind(wx.EVT_LIST_COL_END_DRAG)
            self._unbindHeaderMotion()

    def IsAutoResizing(self):
        return self.__is_auto_resizing

    def OnBeginColumnDrag(self, event):
        # pylint: disable=W0201
        # Block resizing of the auto-fill column (ResizeColumn) when auto-resize
        # is enabled. This column always fills remaining space automatically.
        # Users can resize other columns, which will take/give space from the
        # ResizeColumn. This follows modern UX patterns where auto-fill columns
        # are not directly resizable.
        if event.Column == self.ResizeColumn:
            # self.__oldResizeColumnWidth = self.GetColumnWidth(self.ResizeColumn)  # wx.lib.agw.hypertreelist.HyperTreeList.GetColumnWidth
            event.Veto()
            return
        # Temporarily unbind the EVT_SIZE to prevent resizing during dragging
        self.Unbind(wx.EVT_SIZE)
        # if operating_system.isWindows():
        event.Skip()

    def OnEndColumnDrag(self, event):
        if event.Column == self.ResizeColumn and self.GetColumnCount() > 1:
            # # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # if (
            #     event.Column == self.ResizeColumn
            #     and self.GetHeaderWindow().GetColumnCount() > 1
            # ):  # ou essayer self._columns
            extra_width = self.__oldResizeColumnWidth - self.GetColumnWidth(
                self.ResizeColumn
            )
            self.DistributeWidthAcrossColumns(extra_width)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        wx.CallAfter(self.DoResize)
        event.Skip()

    def _getHeaderWindow(self):
        """Get the header window of the list control (if it exists).

        For wx.ListCtrl, the header is a child window named 'wxlistctrlcolumntitles'.
        For HyperTreeList, header cursor is handled by TreeListHeaderWindow.
        """
        if self.__header_window is not None:
            return self.__header_window
        # Only look for header in wx.ListCtrl, not HyperTreeList
        if isinstance(self, hypertreelist.HyperTreeList):
            return None
        for child in self.GetChildren():
            if child.GetName() == "wxlistctrlcolumntitles":
                self.__header_window = child
                return child
        return None

    def _bindHeaderMotion(self):
        """Bind motion event to header window for cursor feedback."""
        header = self._getHeaderWindow()
        if header:
            header.Bind(wx.EVT_MOTION, self._onHeaderMotion)

    def _unbindHeaderMotion(self):
        """Unbind motion event from header window."""
        header = self._getHeaderWindow()
        if header:
            header.Unbind(wx.EVT_MOTION)
            # Reset cursor to default
            header.SetCursor(wx.STANDARD_CURSOR)

    def _onHeaderMotion(self, event):
        """Handle mouse motion over header to show appropriate cursor.

        Shows 'no entry' cursor when hovering over the resize border of
        the auto-fill column (ResizeColumn), since it cannot be manually resized.

        When on a non-resizable border, we don't call Skip() to prevent the
        native wx.ListCtrl header from overriding our cursor.
        """
        header = self._getHeaderWindow()
        if not header:
            event.Skip()
            return

        x = event.GetX()
        # Determine which column border (if any) the mouse is near
        column_at_border = self._getColumnBorderAtX(x)

        if (
            column_at_border is not None
            and column_at_border == self.ResizeColumn
        ):
            # This is the auto-fill column border - show no-entry cursor
            # Don't call Skip() to prevent native cursor override
            if self.__current_cursor != self.__no_entry_cursor:
                self.__current_cursor = self.__no_entry_cursor
                header.SetCursor(self.__no_entry_cursor)
        else:
            # Reset to standard cursor if we were showing no-entry
            if self.__current_cursor == self.__no_entry_cursor:
                self.__current_cursor = wx.STANDARD_CURSOR
                header.SetCursor(wx.STANDARD_CURSOR)
            # Let native handling take over for other cases
            event.Skip()

    def _getColumnBorderAtX(self, x, tolerance=3):
        """Get the column index whose right border is at x position.

        Returns column index if x is within tolerance of a column's right edge,
        or None if not near any border.
        """
        cumulative_width = 0
        for col_index in range(self.GetColumnCount()):
            # # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # for col_index in range(len(self._columns)):
            cumulative_width += self.GetColumnWidth(col_index)
            if abs(x - cumulative_width) <= tolerance:
                return col_index
        return None

    def OnResize(self, event):
        """
        Gère l'événement de redimensionnement de la fenêtre et ajuste
        automatiquement les colonnes.

        Args :
            event (wx.Event) : Événement de redimensionnement.
        """
        event.Skip()
        # if operating_system.isWindows():
        #     wx.CallAfter(self.DoResize)
        # else:
        #     self.DoResize()
        # Always defer column resize to avoid cascade repaints during resize operations.
        # This is especially important during AUI sash drag where immediate column
        # recalculation can cause flickering.
        wx.CallAfter(self.DoResize)

    def DoResize(self):
        """
        Effectue le calcul et applique les nouvelles largeurs des colonnes.

        Ne redimensionne que si :
        - Le contrôle est visible.
        - Le redimensionnement automatique est activé.
        - La colonne à redimensionner existe.
        """
        # if not self:
        #     return  # Évite une erreur potentielle de PyDeadObject
        # if not self.IsAutoResizing():
        if not self or not self.IsAutoResizing():
            return  # Avoid a potential PyDeadObject error
        # Skip resize if widget isn't shown on screen yet or too small
        if not self.IsShownOnScreen():
            return
        if self.GetSize().height < 32:  # Évite les bugs de hauteur minimale.
            return  # Évite un bug de mise à jour sans fin lorsque la hauteur est petite.
        if self.GetColumnCount() <= self.ResizeColumn:
            # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # if len(self.cget("columns")) <= self.ResizeColumn:
            return  # Nothing to resize.

        unused_width = max(self.AvailableWidth - self.NecessaryWidth, 0)
        resize_column_width = self.ResizeColumnMinWidth + unused_width
        self.SetColumnWidth(self.ResizeColumn, resize_column_width)

    def DistributeWidthAcrossColumns(self, extra_width):
        """
        Répartit l'espace supplémentaire ou manquant sur les colonnes
        autres que `ResizeColumn`.

        Args :
            extra_width (int) : Espace supplémentaire ou manquant à répartir.
        """
        # Lorsque l'utilisateur redimensionne ResizeColumn, répartissez l'espace supplémentaire disponible
        # sur les autres colonnes, ou obtenez l'espace supplémentaire nécessaire à partir de
        # les autres colonnes. Les autres colonnes sont redimensionnées proportionnellement à
        # leur largeur précédente.
        other_columns = [
            index
            for index in range(self.GetColumnCount())
            # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # for index in range(self.GetHeaderWindow().GetColumnCount())
            if index != self.ResizeColumn
        ]
        total_width = float(
            sum(self.GetColumnWidth(index) for index in other_columns)
        )
        for column_index in other_columns:
            this_column_width = self.GetColumnWidth(column_index)
            # this_column_width += this_column_width / total_width * extra_width
            # this_column_width += old_div(this_column_width, total_width) * extra_width
            this_column_width += this_column_width // total_width * extra_width
            self.SetColumnWidth(column_index, this_column_width)
            # ou essayer :
            # adjusted_width = current_width + (current_width / total_width) * extra_width
            # self.SetColumnWidth(column_index, adjusted_width)

    def GetResizeColumn(self):
        if self.__resize_column == -1:
            return self.GetColumnCount() - 1
            # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # return self.widget.GetHeaderWindow().GetColumnCount() - 1
        else:
            return self.__resize_column

    def SetResizeColumn(self, column_index):
        self.__resize_column = column_index  # pylint: disable=W0201

    ResizeColumn = property(GetResizeColumn, SetResizeColumn)

    def GetAvailableWidth(self):
        available_width = self.GetClientSize().width
        if (
            self.__is_scrollbar_visible()
            and self.__is_scrollbar_included_in_client_size()
        ):
            # scrollbar_width = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
            scrollbar_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            available_width -= scrollbar_width
        return available_width

    AvailableWidth = property(GetAvailableWidth)

    def GetNecessaryWidth(self):
        necessary_width = 0
        for column_index in range(self.GetColumnCount()):
            # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter
            # for column_index in range(self.GetHeaderWindow().GetColumnCount()):
            if column_index == self.ResizeColumn:
                necessary_width += self.ResizeColumnMinWidth
            else:
                necessary_width += self.GetColumnWidth(column_index)
        return necessary_width

    NecessaryWidth = property(GetNecessaryWidth)

    # Remplacez toutes les méthodes qui manipulent les colonnes pour pouvoir redimensionner les
    # colonnes après tout ajout ou suppression.

    def InsertColumn(self, *args, **kwargs):
        """Insérez la nouvelle colonne, puis redimensionnez."""
        result = super().InsertColumn(*args, **kwargs)
        # self.DoResize()
        wx.CallAfter(self.DoResize)
        return result

    def DeleteColumn(self, *args, **kwargs):
        """Supprimez la colonne, puis redimensionnez-la."""
        result = super().DeleteColumn(*args, **kwargs)
        # self.DoResize()
        wx.CallAfter(self.DoResize)
        return result

    def RemoveColumn(self, *args, **kwargs):
        """Retirez la colonne, puis redimensionnez."""
        result = super().RemoveColumn(*args, **kwargs)
        # self.DoResize()
        wx.CallAfter(self.DoResize)
        return result

    def AddColumn(self, *args, **kwargs):
        """Ajoutez la colonne, puis redimensionnez-la."""
        result = super().AddColumn(*args, **kwargs)
        # self.DoResize()
        wx.CallAfter(self.DoResize)
        return result

    # Private helper methods:
    # Méthodes d'assistance privées :

    def __is_scrollbar_visible(self):
        """
        Vérifie si la barre de défilement verticale est visible.

        Returns :
            bool : `True` si visible, sinon `False`.
        """
        return self.MainWindow.HasScrollbar(wx.VERTICAL)

    def __is_scrollbar_included_in_client_size(self):
        """
        Vérifie si la barre de défilement est incluse dans la taille client.

        Returns :
            bool : `True` si incluse, sinon `False`.
        """
        # NOTE: Sur GTK, la barre de défilement est incluse dans la taille du client, mais sur
        # Windows, elle n'est pas incluse.
        if operating_system.isWindows():
            # Windows Win32: fixed scrollbars, but only included in client size
            # for HyperTreeList widgets
            return isinstance(self, hypertreelist.HyperTreeList)

        if operating_system.isMac():
            # macOS: overlay scrollbars by default since 10.7
            # User can change in System Preferences, but overlay is the norm
            return False

        # Linux/BSD with GTK
        if self.__has_overlay_scrollbars():
            # Overlay scrollbars don't take layout space
            return False
        else:
            # Fixed scrollbars (GTK2 or GTK3 with overlay disabled)
            # are included in client size
            return True

    def __has_overlay_scrollbars(self):
        """Detect if the system uses overlay scrollbars (GTK3/GTK4 default).

        GTK3 and GTK4 use overlay scrollbars by default. This can be disabled
        by setting GTK_OVERLAY_SCROLLING=0 environment variable.
        GTK2 always uses fixed scrollbars.
        """
        # Check for GTK3 or GTK4 in wx.PlatformInfo
        platform_info = wx.PlatformInfo
        has_gtk3_or_gtk4 = "gtk3" in platform_info or "gtk4" in platform_info

        if not has_gtk3_or_gtk4:
            # GTK2 or unknown: no overlay scrollbars
            return False

        # GTK3/GTK4: overlay is default, but can be disabled via env var
        if os.environ.get("GTK_OVERLAY_SCROLLING") == "0":
            return False

        return True
