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

# from builtins import range
from ... import tctest
import wx
from ...unittests import dummy
from taskcoachlib import widgets


class VirtualListCtrlTestCase(tctest.wxTestCase):
    """Test class for VirtualListCtrl functionality."""

    onSelect = lambda *args: None

    def createListCtrl(self):
        """Crée une instance de VirtualListCtrl."""
        self.frame.getItemWithIndex = lambda index: index
        self.frame.getIndexOfItem = lambda item: (
            item if type(item) is type(0) else 0
        )
        self.frame.getItemText = lambda item, column: ""
        self.frame.getItemTooltipData = lambda item: []
        self.frame.getItemImages = lambda item, column: {
            wx.TreeItemIcon_Normal: -1
        }
        return widgets.VirtualListCtrl(
            self.frame, self.columns, self.onSelect, dummy.DummyUICommand()
        )

    def createColumns(self, nrColumns):
        """Crée une liste de colonnes."""
        columns = []
        for columnIndex in range(1, nrColumns + 1):
            name = "column%d" % columnIndex
            columns.append(widgets.Column(name, name, None, None))
        return columns

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.columns = self.createColumns(nrColumns=3)
        self.listctrl = self.createListCtrl()

    def testOneItem(self):
        """Test that ListCtrl can be created successfully."""
        self.listctrl.RefreshAllItems(1)
        self.assertEqual(1, self.listctrl.GetItemCount())

    def testNrOfColumns(self):
        """Test that ListCtrl can be created successfully with 3 columns."""
        self.assertEqual(3, self.listctrl.GetColumnCount())

    def testCurselection_EmptyList(self):
        """Teste la sélection courante vide."""
        self.assertEqual([], self.listctrl.curselection())

    def testShowColumn_Hide(self):
        """Teste la cachement d'une colonne."""
        self.listctrl.showColumn(self.columns[2], False)
        self.assertEqual(
            2, self.listctrl.GetColumnCount()
        )  # ListCtrl a GetColumnCount
        # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter

    def testShowColumn_HideAndShow(self):
        """Teste le cachement et l'affichage d'une colonne."""
        self.listctrl.showColumn(self.columns[2], False)
        self.listctrl.showColumn(self.columns[2], True)
        self.assertEqual(
            3, self.listctrl.GetColumnCount()
        )  # ListCtrl a GetColumnCount()
        # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter

    def testShowColumn_ColumnOrderIsKept(self):
        """Teste l'ordre des colonnes."""
        self.listctrl.showColumn(self.columns[1], False)
        self.listctrl.showColumn(self.columns[2], False)
        self.listctrl.showColumn(self.columns[1], True)
        self.listctrl.showColumn(self.columns[2], True)
        # pylint: disable=W0212
        self.assertEqual(
            self.columns[1].header(), self.listctrl._getColumnHeader(1)
        )
        self.assertEqual(
            self.columns[2].header(), self.listctrl._getColumnHeader(2)
        )

    def testShowColumn_HideTwice(self):
        """Teste le cachement d'une colonne deux fois."""
        self.listctrl.showColumn(self.columns[2], False)
        self.listctrl.showColumn(self.columns[2], False)
        self.assertEqual(
            2, self.listctrl.GetColumnCount()
        )  # ListCtrl a GetColumnCount()
        # len(self.viewer.widget._columns) ou self.widget.GetHeaderWindow().GetColumnCount() et, essayer cget avec tkinter

    def testSelect(self):
        """Teste la sélection d'un élément."""
        self.listctrl.RefreshAllItems(1)
        self.listctrl.select([0])
        self.assertEqual([0], self.listctrl.curselection())

    def testSelect_EmptySelection(self):
        """Teste la sélection vide."""
        self.listctrl.RefreshAllItems(1)
        self.listctrl.select([])
        self.assertEqual([], self.listctrl.curselection())

    def testSelect_MultipleSelection(self):
        """Teste la sélection multiple."""
        self.listctrl.RefreshAllItems(2)
        self.listctrl.select([0, 1])
        self.assertEqual([0, 1], self.listctrl.curselection())

    def testSelect_DisjunctMultipleSelection(self):
        """Teste la sélection multiple disjointe."""
        self.listctrl.RefreshAllItems(3)
        self.listctrl.select([0, 2])
        self.assertEqual([0, 2], self.listctrl.curselection())

    def testSelect_SetsFocus(self):
        """Teste la sélection et le focus sur un élément."""
        self.listctrl.RefreshAllItems(1)
        self.listctrl.select([0])
        self.assertEqual(0, self.listctrl.GetFocusedItem())

    def testSelect_EmptySelection_SetsFocus(self):
        """Teste la sélection vide et le focus sur un élément."""
        self.listctrl.RefreshAllItems(1)
        self.listctrl.select([])
        self.assertEqual(-1, self.listctrl.GetFocusedItem())

    def testSelect_MultipleSelection_SetsFocus(self):
        """Teste la sélection multiple et le focus sur un élément."""
        self.listctrl.RefreshAllItems(2)
        self.listctrl.select([0, 1])
        self.assertEqual(0, self.listctrl.GetFocusedItem())

    def testSelect_DisjunctMultipleSelection_SetsFocus(self):
        """Teste le focus sur l'élément sélectionné d'une sélection multiple disjointe."""
        self.listctrl.RefreshAllItems(3)
        self.listctrl.select([0, 2])
        self.assertEqual(0, self.listctrl.GetFocusedItem())
