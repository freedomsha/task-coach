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

Ce fichier de test unitaire vérifie le comportement de drag-and-drop (glisser-déposer)
dans l'arborescence `treectrl.HyperTreeList` de la bibliothèque `taskcoachlib`.

La classe `TreeCtrlDragAndDropMixinTest` hérite de `tctest.wxTestCase` et définit
plusieurs tests unitaires pour vérifier si les événements de drag-and-drop
sont déclenchés correctement selon la présence ou l'absence d'un élément sélectionné.

La classe `DummyEvent` est utilisée pour simuler des événements de drag-and-drop
pendant les tests. Elle permet de définir un élément associé à l'événement
ainsi que de contrôler si l'événement est autorisé ou interdit.

Les méthodes de test `testEventIsVetoedWhenDragBeginsWithoutItem`,
`testEventIsAllowedWhenDragBeginsWithItem`, et
`testEventIsAllowedWhenDragBeginWithSelectedItem` vérifient
si l'événement de début de drag-and-drop ( `OnBeginDrag` )
est correctement autorisé ou interdit selon les conditions suivantes :

* `testEventIsVetoedWhenDragBeginsWithoutItem` : L'événement est interdit
  si aucun élément n'est associé à l'événement.
* `testEventIsAllowedWhenDragBeginsWithItem` : L'événement est autorisé
  si un élément est associé à l'événement.
* `testEventIsAllowedWhenDragBeginWithSelectedItem` : L'événement est autorisé
  si un élément est sélectionné dans l'arborescence et associé à l'événement.

Les méthodes `assertEventIsVetoed` et `assertEventIsAllowed` permettent de vérifier
l'état de l'événement simulé (autorisé ou interdit).
"""

# from builtins import object
# import os
# import sys
#
# # Ajouter le répertoire parent au chemin Python
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ... import tctest
import wx
from taskcoachlib.widgets import treectrl




class DummyEvent(object):
    """
    Simule un événement, souvent utilisé dans des tests unitaires pour passer des événements simulés lors des appels de tests.

    Attributs :
        item (object, optionnel) : L'élément associé à l'événement.
        vetoed (bool) : Indique si l'événement a été interdit.
        allowed (bool) : Indique si l'événement a été autorisé.
    """
    def __init__(self, item=None):
        self.item = item
        self.vetoed = self.allowed = False

    def GetItem(self):
        return self.item

    def Veto(self):
        self.vetoed = True

    def Allow(self):
        self.allowed = True


class TreeCtrlDragAndDropMixinTest(tctest.wxTestCase):
    # pylint: disable=E1101

    def setUp(self):
        self.treeCtrl = treectrl.HyperTreeList(self.frame)
        self.treeCtrl.AddColumn("First")

        self.rootItem = self.treeCtrl.AddRoot("root")
        self.item = self.treeCtrl.AppendItem(self.rootItem, "item")
        # self.item = self.treeCtrl.Append(self.rootItem, "item")  # AttributeError: 'HyperTreeList' object has no attribute 'Append'

    def assertEventIsVetoed(self, event):
        self.assertTrue(event.vetoed)
        self.assertFalse(event.allowed)

    def assertEventIsAllowed(self, event):
        self.assertTrue(event.allowed)
        self.assertFalse(event.vetoed)

    def testEventIsVetoedWhenDragBeginsWithoutItem(self):
        """
        Vérifie que l'événement de début de drag-and-drop est interdit si aucun élément n'est associé à l'événement.
        """
        event = DummyEvent()
        self.treeCtrl._dragStartPos = wx.Point(0, 0)
        self.treeCtrl.OnBeginDrag(event)
        self.assertEventIsVetoed(event)

    def testEventIsAllowedWhenDragBeginsWithItem(self):
        """
        Vérifie que l'événement de début de drag-and-drop est autorisé si un élément est associé à l'événement.
        """
        self.treeCtrl.SelectItem(self.item)  # Assurez-vous que l'élément est sélectionné
        event = DummyEvent(self.item)
        self.treeCtrl._dragStartPos = wx.Point(0, 0)
        self.treeCtrl.OnBeginDrag(event)
        self.assertEventIsAllowed(event)

    def testEventIsAllowedWhenDragBeginWithSelectedItem(self):
        """
        Vérifie que l'événement de début de drag-and-drop est autorisé si l'élément sélectionné est associé à l'événement.
        """
        self.treeCtrl.SelectItem(self.item)
        event = DummyEvent(self.item)
        self.treeCtrl._dragStartPos = wx.Point(0, 0)
        self.treeCtrl.OnBeginDrag(event)
        self.assertEventIsAllowed(event)
