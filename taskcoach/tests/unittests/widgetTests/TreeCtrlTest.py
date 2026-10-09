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

**Module TreeCtrlTest**

Ce module contient les tests unitaires pour les widgets d'arborescence de Task Coach,
notamment `TreeListCtrl` et `CheckTreeCtrl`. Il utilise des objets de domaine fictifs
et simule l'interface de l'adaptateur pour vérifier le bon comportement de l'affichage,
de la hiérarchie et de la sélection.

Ce module fournit l'infrastructure de test pour les composants d'arborescence
(`TreeListCtrl` et `CheckTreeCtrl`).

Il utilise des objets de domaine fictifs (Mocks) et simule l'interface de l'adaptateur
(le Viewer) pour vérifier le bon comportement de l'affichage, de la hiérarchie
et de la sélection, sans dépendre de toute la logique métier de Task Coach.

La structure repose sur trois piliers :
1. **TreeCtrlTestCase** : Configure un environnement wxPython minimaliste et
   simule l'API de l'adaptateur (le Viewer) attendue par les widgets.
2. **DummyDomainObject** : Simule les objets métier (Tâches/Catégories) sans
   charger la logique complexe du domaine réel.
3. **CommonTestsMixin** : Factorise les tests de structure arborescente (ajout,
   suppression, réordonnancement) pour éviter la duplication entre les types
   de contrôles.
"""

# from builtins import object
import wx
from ... import tctest
from ...unittests import dummy
from taskcoachlib import widgets

from taskcoachlib.widgets import treectrl


class TreeCtrlTestCase(tctest.wxTestCase):
    """
    Harnais de test pour les TreeControls.

    Classe de base pour les tests de contrôles d'arborescence.
    Elle configure la frame de test pour qu'elle se comporte comme un adaptateur
    (viewer) en simulant les méthodes `children`, `getItemText`, etc.

    Cette classe injecte des méthodes fictives (mocks) directement dans `self.frame`.
    Comme les widgets `TreeListCtrl` interrogent leur parent pour obtenir les données,
    la frame de test "joue le rôle" du Viewer (adaptateur) en répondant aux appels
    `children`, `getItemText`, etc.
    """

    onSelect = None

    def getFirstTreeItem(self):
        """Récupère le premier élément graphique enfant de la racine.

        Utilitaire pour accéder au premier nœud graphique visible.

        Dans Task Coach, la racine est souvent masquée (`wx.TR_HIDE_ROOT`),
        donc le premier élément utile est le premier enfant de cette racine cachée.

        :return: Un identifiant `wx.TreeItemId`.
        """
        # pylint: disable=E1101
        return self.treeCtrl.GetFirstChild(self.treeCtrl.GetRootItem())[0]

    def setUp(self):
        """
        Initialise l'arborescence de test et configure les mocks sur la frame
        pour répondre aux appels du widget TreeCtrl.

        Les lambdas injectés simulent le contrat d'interface (API) entre le widget
        graphique et sa source de données :
        - `children` : définit la hiérarchie.
        - `getItemExpanded` : simule l'état de mémorisation de l'expansion.
        """
        super().setUp()
        self.children = dict()
        self.collapsedItems = []
        self.frame.children = lambda item: self.children.get(item, [])
        self.frame.getItemText = lambda item, column: item.subject()
        self.frame.hasColumnImages = lambda column: False
        self.frame.getItemImages = lambda item, column: {
            wx.TreeItemIcon_Normal: -1
        }
        self.frame.getIsItemChecked = lambda item: False
        self.frame.getItemExpanded = (
            lambda item: item not in self.collapsedItems
        )
        self.frame.isTreeViewer = (
            lambda: True
        )  # Ajout de la méthode isTreeViewer
        self.item0 = DummyDomainObject("item 0")
        self.item1 = DummyDomainObject("item 1")
        self.item0_0 = DummyDomainObject("item 0.0")
        self.item0_1 = DummyDomainObject("item 0.1")
        self.item1_0 = DummyDomainObject("item 1.0")


class DummyDomainObject(object):
    """
    Mock d'objet métier.

    Objet de domaine minimaliste utilisé pour simuler des tâches ou catégories
    dans les tests d'interface graphique.

    Implémente le strict minimum requis par `TreeListCtrl` pour l'affichage :
    un sujet (texte), et des méthodes pour la police et les couleurs qui
    retournent des valeurs neutres par défaut.
    """

    def __init__(self, subject):
        self.__subject = subject

    def subject(self):
        return self.__subject

    # pylint: disable=W0613

    def foregroundColor(self, recursive=False):
        return None

    def backgroundColor(self, recursive=False):
        return None

    def font(self, recursive=False):
        return None


class CommonTestsMixin(object):
    """
    Ensemble de tests structurels communs.

    Mixin contenant des tests génériques applicables à n'importe quel type
    de widget d'arborescence (reconstruction de l'arbre, conservation de la
    sélection, expansion/effondrement des nœuds).

    Ce mixin vérifie que le widget reflète correctement les changements du modèle :
    - Synchronisation du nombre d'éléments.
    - Respect de la hiérarchie Parent/Enfant.
    - Maintien de la sélection lors d'un rafraîchissement (rebuild).
    - Algorithmes de recherche d'état (`isAnyItemExpandable`).
    """

    def testCreate(self):
        """Vérifie qu'un arbre vide est bien initialisé sans nœuds visibles."""
        self.assertEqual(0, len(self.treeCtrl.GetItemChildren()))

    def testOneItem(self):
        """Vérifie que l'arbre affiche correctement un seul élément racine."""
        self.children[None] = [self.item0]  # Définition de l'élément racine
        # self.treeCtrl.RefreshAllItems(1)
        self.treeCtrl.scheduleRefresh(1)
        self.assertEqual(1, len(self.treeCtrl.GetItemChildren()))

    def testTwoItems(self):
        """Vérifie l'affichage de deux éléments à la racine."""
        self.children[None] = [self.item0, self.item1]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.assertEqual(2, len(self.treeCtrl.GetItemChildren()))

    def testRemoveAllItems(self):
        """Vérifie que vider le modèle vide aussi le widget."""
        self.children[None] = [self.item0, self.item1]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.children[None] = []
        # self.treeCtrl.RefreshAllItems(0)
        self.treeCtrl.scheduleRefresh(0)
        self.assertEqual(0, len(self.treeCtrl.GetItemChildren()))

    def testOneParentAndOneChild(self):
        """Vérifie la hiérarchie simple : un parent avec un enfant."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.assertEqual(1, len(self.treeCtrl.GetItemChildren()))
        self.assertEqual(
            1, len(self.treeCtrl.GetItemChildren(self.getFirstTreeItem()))
        )

    def testOneParentAndTwoChildren(self):
        """Vérifie un parent avec deux enfants."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0, self.item0_1]
        # self.treeCtrl.RefreshAllItems(3)
        self.treeCtrl.scheduleRefresh(3)
        self.assertEqual(1, len(self.treeCtrl.GetItemChildren()))
        self.assertEqual(
            2, len(self.treeCtrl.GetItemChildren(self.getFirstTreeItem()))
        )

    def testAddOneChild(self):
        """Vérifie que l'ajout dynamique d'un enfant est bien pris en compte au rafraîchissement."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.children[self.item0] = [self.item0_0, self.item0_1]
        # self.treeCtrl.RefreshAllItems(3)
        self.treeCtrl.scheduleRefresh(3)
        self.assertEqual(1, len(self.treeCtrl.GetItemChildren()))
        self.assertEqual(
            2, len(self.treeCtrl.GetItemChildren(self.getFirstTreeItem()))
        )

    def testDeleteOneChild(self):
        """Vérifie la suppression dynamique d'un enfant."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0, self.item0_1]
        # self.treeCtrl.RefreshAllItems(3)
        self.treeCtrl.scheduleRefresh(3)
        self.children[self.item0] = [self.item0_0]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.assertEqual(1, len(self.treeCtrl.GetItemChildren()))
        self.assertEqual(
            1, len(self.treeCtrl.GetItemChildren(self.getFirstTreeItem()))
        )

    def testReorderItems(self):
        """Vérifie que l'ordre d'affichage respecte l'ordre du modèle après changement."""
        self.children[None] = [self.item0, self.item1]
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.children[None] = [self.item1, self.item0]  # Inversion
        # self.treeCtrl.RefreshAllItems(2)
        self.treeCtrl.scheduleRefresh(2)
        self.assertEqual(
            "item 1", self.treeCtrl.GetItemText(self.getFirstTreeItem())
        )

    def testReorderChildren(self):
        """Vérifie le réordonnancement des enfants d'un nœud."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0, self.item0_1]
        self.treeCtrl.scheduleRefresh(3)
        self.children[self.item0] = [self.item0_1, self.item0_0]
        self.treeCtrl.scheduleRefresh(3)
        self.assertEqual(
            "item 0.1",
            self.treeCtrl.GetItemText(
                self.treeCtrl.GetFirstChild(self.getFirstTreeItem())[0]
            ),
        )

    def testReorderParentsAndOneChild(self):
        self.children[None] = [self.item0, self.item1]
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(3)
        self.children[None] = [self.item1, self.item0]
        self.treeCtrl.scheduleRefresh(3)
        self.assertEqual(
            "item 1", self.treeCtrl.GetItemText(self.getFirstTreeItem())
        )

    def testReorderParentsAndTwoChildren(self):
        self.children[None] = [self.item0, self.item1]
        self.children[self.item0] = [self.item0_0, self.item0_1]
        self.treeCtrl.scheduleRefresh(4)
        self.children[None] = [self.item1, self.item0]
        self.children[self.item0] = [self.item0_1, self.item0_0]
        self.treeCtrl.scheduleRefresh(4)
        self.assertEqual(
            "item 1", self.treeCtrl.GetItemText(self.getFirstTreeItem())
        )
        self.assertEqual(
            0, len(self.treeCtrl.GetItemChildren(self.getFirstTreeItem()))
        )

    def testRetainSelectionWhenEditingTask(self):
        """Vérifie que la sélection est conservée si l'objet sélectionné est mis à jour."""
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        item = self.getFirstTreeItem()
        self.treeCtrl.SelectItem(item)
        self.assertTrue(self.treeCtrl.IsSelected(item))
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        item = self.getFirstTreeItem()
        self.assertTrue(self.treeCtrl.IsSelected(item))

    def testRetainSelectionWhenEditingSubTask(self):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        item = self.getFirstTreeItem()
        self.treeCtrl.SelectItem(item)
        self.assertTrue(self.treeCtrl.IsSelected(item))
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        item = self.getFirstTreeItem()
        self.assertTrue(self.treeCtrl.IsSelected(item))

    def testRetainSelectionWhenAddingSubTask(self):
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        item = self.getFirstTreeItem()
        self.treeCtrl.SelectItem(item)
        self.assertTrue(self.treeCtrl.IsSelected(item))
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        item = self.getFirstTreeItem()
        self.assertTrue(self.treeCtrl.IsSelected(item))

    def testRetainSelectionWhenAddingSubTask_TwoToplevelTasks(self):
        self.children[None] = [self.item0, self.item1]
        self.treeCtrl.scheduleRefresh(2)
        item = self.getFirstTreeItem()
        self.treeCtrl.SelectItem(item)
        self.assertTrue(self.treeCtrl.IsSelected(item))
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(3)
        item = self.getFirstTreeItem()
        self.assertTrue(self.treeCtrl.IsSelected(item))

    def testRemovingASelectedItemDoesNotMakeAnotherOneSelected(self):
        """Vérifie que si on supprime l'élément sélectionné, la sélection est bien vidée."""
        self.children[None] = [self.item0, self.item1]
        self.treeCtrl.scheduleRefresh(2)
        item = self.getFirstTreeItem()
        self.treeCtrl.SelectItem(item)
        self.assertTrue(self.treeCtrl.IsSelected(item))
        self.children[None] = [self.item1]
        self.treeCtrl.scheduleRefresh(1)
        self.assertFalse(self.treeCtrl.curselection())

    def testRefreshItem(self):
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        self.treeCtrl.RefreshItems(self.item0)
        item = self.getFirstTreeItem()
        self.assertEqual("item 0", self.treeCtrl.GetItemText(item))

    def testIsAnyItemCollapsable_NoItems(self):
        self.assertFalse(self.treeCtrl.isAnyItemCollapsable())

    def testIsAnyItemExpandable_NoItems(self):
        self.assertFalse(self.treeCtrl.isAnyItemExpandable())

    def testIsAnyItemCollapsable_OneItem(self):
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        self.assertFalse(self.treeCtrl.isAnyItemCollapsable())

    def testIsAnyItemExpandable_OneItem(self):
        self.children[None] = [self.item0]
        self.treeCtrl.scheduleRefresh(1)
        self.assertFalse(self.treeCtrl.isAnyItemExpandable())

    def testIsAnyItemCollapsable_OneCollapsedParent(self):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.collapsedItems.append(self.item0)
        self.treeCtrl.scheduleRefresh(2)
        self.assertFalse(self.treeCtrl.isAnyItemCollapsable())

    def testIsAnyItemExpandable_OneCollapsedParent(self):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.collapsedItems.append(self.item0)
        self.treeCtrl.scheduleRefresh(2)
        self.assertTrue(self.treeCtrl.isAnyItemExpandable())

    def testIsAnyItemCollapsable_OneExpandedParent(self):
        """Vérifie la détection d'un nœud pouvant être replié."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        parent = self.getFirstTreeItem()
        self.treeCtrl.Expand(parent)
        self.assertTrue(self.treeCtrl.isAnyItemCollapsable())

    def testIsAnyItemExpandable_OneExpandedParent(self):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        parent = self.getFirstTreeItem()
        self.treeCtrl.Expand(parent)
        self.assertFalse(self.treeCtrl.isAnyItemExpandable())


class TreeListCtrlTest(TreeCtrlTestCase, CommonTestsMixin):
    """
    Suite de tests pour le composant `TreeListCtrl` (Arborescence multicolonne).

    Initialise le widget avec une colonne 'Subject' et valide les comportements
    hérités du `CommonTestsMixin`.
    """

    def setUp(self):
        super().setUp()
        columns = [widgets.Column("subject", "Subject")]
        self.treeCtrl = widgets.TreeListCtrl(
            self.frame,
            columns,
            self.onSelect,
            dummy.DummyUICommand(),
            dummy.DummyUICommand(),
            dummy.DummyUICommand(),
        )
        # Ajout d'une liste d'images pour simuler les icônes de tâches
        imageList = wx.ImageList(16, 16)
        for bitmapName in ["led_blue_icon", "folder_blue_icon"]:
            imageList.Add(
                wx.ArtProvider.GetBitmap(bitmapName, wx.ART_MENU, (16, 16))
            )
        self.treeCtrl.AssignImageList(imageList)  # pylint: disable=E1101


class CheckTreeCtrlTest(TreeCtrlTestCase, CommonTestsMixin):
    """
    Suite de tests pour le composant `CheckTreeCtrl`.

    Se concentre sur la logique métier des cases à cocher :
    - Propagation (ou non) de l'état coché du parent vers l'enfant.
    - Gestion de l'exclusion mutuelle (si un parent a des enfants exclusifs,
      cliquer sur l'un doit décocher les autres).
    """

    def setUp(self):
        """
        Configure une règle spéciale : les objets dont le sujet commence
        par "mutual" simulent des enfants en exclusion mutuelle (type radio).
        """
        self.frame.getItemParentHasExclusiveChildren = (
            lambda item: item.subject().startswith("mutual")
        )
        super().setUp()
        columns = [widgets.Column("subject", "Subject")]
        self.treeCtrl = widgets.CheckTreeCtrl(
            self.frame,
            columns,
            self.onSelect,
            self.onCheck,  # Callback lors du cochage
            dummy.DummyUICommand(),
            dummy.DummyUICommand(),
        )
        self.mutual1 = DummyDomainObject("mutual 1")
        self.mutual2 = DummyDomainObject("mutual 2")

    def onCheck(self, event, final):
        pass

    def testCheckParentDoesNotCheckChild(self):
        """Vérifie que cocher un parent ne coche pas automatiquement ses enfants (comportement Task Coach)."""
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.item0_0]
        self.treeCtrl.scheduleRefresh(2)
        self.treeCtrl.ExpandAll()  # pylint: disable=E1101
        parent = self.getFirstTreeItem()
        self.treeCtrl.CheckItem(parent)
        child = self.treeCtrl.GetItemChildren(parent)[0]
        self.assertFalse(child.IsChecked())

    def testCheckParentOfMutualExclusiveChildrenUnchecksAllChildren(self):
        """Vérifie que si on coche un parent 'exclusif', ses enfants sont décochés."""
        self.children[None] = [
            self.item0
        ]  # item0 ici simulera un parent exclusif via le mock
        # Note: Dans ce test, item0 devrait être nommé "mutual..." selon le mock défini en setUp
        self.children[self.item0] = [self.mutual1, self.mutual2]
        self.treeCtrl.scheduleRefresh(3)
        self.treeCtrl.ExpandAll()  # pylint: disable=E1101
        parent = self.getFirstTreeItem()
        children = self.treeCtrl.GetItemChildren(parent)
        self.treeCtrl.CheckItem(children[0])  # On en coche un
        self.treeCtrl.CheckItem(parent)  # On coche le parent
        for child in children:
            self.assertFalse(
                child.IsChecked()
            )  # Les enfants doivent être décochés

    def testCheckParentOfMutualExclusiveChildrenUnchecksAllChildrenRecursively(
        self,
    ):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.mutual1, self.mutual2]
        self.children[self.mutual1] = [self.item1_0]
        self.treeCtrl.scheduleRefresh(4)
        self.treeCtrl.ExpandAll()  # pylint: disable=E1101
        parent = self.getFirstTreeItem()
        children = self.treeCtrl.GetItemChildren(parent, recursively=True)
        grandchild = children[1]
        self.treeCtrl.CheckItem(grandchild)
        self.treeCtrl.CheckItem(parent)
        self.assertFalse(grandchild.IsChecked())

    def testCheckMutualExclusiveChildUnchecksParent(self):
        self.children[None] = [self.item0]
        self.children[self.item0] = [self.mutual1, self.mutual2]
        self.treeCtrl.scheduleRefresh(3)
        self.treeCtrl.ExpandAll()  # pylint: disable=E1101
        parent = self.getFirstTreeItem()
        children = self.treeCtrl.GetItemChildren(parent)
        self.treeCtrl.CheckItem(parent)
        self.treeCtrl.CheckItem(children[0])
        self.assertFalse(
            self.treeCtrl.IsItemChecked(parent)
        )  # pylint: disable=E1101
