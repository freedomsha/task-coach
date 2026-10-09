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

# from builtins import object
import wx
from ... import tctest
from taskcoachlib import widgets


class CtrlWithColumnsTestCase(tctest.wxTestCase):
    """
    Classe de scénario de test pour les contrôles avec des définitions de colonnes.

    Cette classe fournit une structure pour tester les contrôles qui
    s'appuient sur des définitions de colonnes. Il initialise les colonnes
    par défaut et configure une instance de contrôle
    à utiliser pour d'autres tests via l'héritage. Le contrôle spécifique
    à tester doit être créé en remplaçant la méthode `createControl`.

    Attributes:
        column1 (widgets.Column): La première colonne avec un type d'événement associé.
        column2 (widgets.Column): La deuxième colonne avec un type d'événement
            associé distinct.
        control: Une instance du contrôle en cours de test. Ceci est censé être
            instancié dans les classes dérivées en remplaçant la méthode `createControl`.
    """

    def setUp(self):
        super().setUp()
        self.column1 = widgets.Column("Column 1", "eventType1")
        self.column2 = widgets.Column("Column 2", "eventType2")
        self.control = self.createControl()

    def createControl(self):
        raise NotImplementedError  # pragma: no cover


class CtrlWithHideableColumnsUnderTest(
    widgets.itemctrl._CtrlWithHideableColumnsMixin,
    wx.ListCtrl,  # pylint: disable=W0212
):
    """
    Cette classe représente un contrôle avec des colonnes masquables conçu
    pour les widgets basés sur des listes.

    La classe est destinée à fournir des fonctionnalités qui combinent
    les fonctionnalités d'un contrôle de liste avec la possibilité supplémentaire
    de masquer les colonnes si nécessaire. Il est principalement utilisé pour gérer et afficher des données tabulaires où les colonnes peuvent être
    activées ou désactivées en fonction des besoins de l'utilisateur.
    """

    pass


class CtrlWithHideableColumnsTestsMixin(object):
    """Mixin fournissant des tests pour les contrôles avec des colonnes masquables.

    Ce mixin est conçu pour fournir des cas de test pour vérifier le comportement des colonnes
    qui peuvent être affichées ou masquées dans un contrôle. Il garantit que les colonnes
    sont visibles par défaut, peuvent être explicitement masquées, puis rendues à nouveau visibles.

    Attributes:
        control (object): L'instance de contrôle qui comporte des colonnes qui peuvent être
            affichées ou masquées.
        column1 (object): Instance de colonne utilisée dans les scénarios de test pour valider la fonctionnalité de visibilité
            .
    """

    def testColumnIsVisibleByDefault(self):
        self.assertTrue(self.control.isColumnVisible(self.column1))

    def testHideColumn(self):
        self.control.showColumn(self.column1, show=False)
        self.assertFalse(self.control.isColumnVisible(self.column1))

    def testShowColumn(self):
        self.control.showColumn(self.column1, show=False)
        self.control.showColumn(self.column1, show=True)
        self.assertTrue(self.control.isColumnVisible(self.column1))


class CtrlWithHideableColumnsTest(
    CtrlWithColumnsTestCase, CtrlWithHideableColumnsTestsMixin
):
    """
    Classe de test pour les contrôles avec des colonnes masquables.

    Cette classe est conçue pour tester la fonctionnalité des contrôles qui incluent des colonnes masquables
    dans un contrôle de liste de style rapport. Il étend les cas de test de base et les mixins
    pour garantir des tests complets des comportements liés aux colonnes.

    Attributes:
        frame (Frame): Cadre parent dans lequel le contrôle fonctionne.
        column1 (type): Première colonne utilisée dans les tests.
        column2 (type): Deuxième colonne utilisée dans les tests.
    """

    def createControl(self):
        return CtrlWithHideableColumnsUnderTest(
            self.frame,
            style=wx.LC_REPORT,
            columns=[self.column1, self.column2],
        )


class CtrlWithSortableColumnsUnderTest(
    widgets.itemctrl._CtrlWithSortableColumnsMixin,
    wx.ListCtrl,  # pylint: disable=W0212
):
    """
    Gère un contrôle avec des colonnes triables.

    Cette classe combine les fonctionnalités d'un mixin de colonnes triables
    et d'un wx.ListCtrl pour fournir un contrôle qui prend en charge le tri des colonnes.
    Elle est conçue pour gérer le comportement de tri et conserver l'apparence et les fonctionnalités
    du contrôle de liste.

    Attributes:
        None
    """

    pass


class CtrlWithSortableColumnsTestsMixin(object):
    """
    Classe Mixin pour fournir des tests pour la fonctionnalité des colonnes triables dans un contrôle.

    Cette classe mixin est conçue pour être utilisée avec des classes de test pour vérifier le comportement correct
    des colonnes triables dans un contrôle. Il fournit des méthodes utilitaires et des tests
    pour vérifier et affirmer la colonne de tri actuelle dans un contrôle.

    Attributes:
        control (Any): Instance de contrôle en cours de test.
        column1 (Any): La colonne par défaut utilisée pour le tri dans les tests.
        column2 (Any): Une colonne alternative utilisée pour le tri dans les tests.
    """

    def assertCurrentSortColumn(self, expectedSortColumn):
        currentSortColumn = (
            self.control._currentSortColumn()
        )  # pylint: disable=W0212
        self.assertEqual(expectedSortColumn, currentSortColumn)

    def testDefaultSortColumn(self):
        self.assertCurrentSortColumn(self.column1)

    def testShowSortColumn(self):
        self.control.showSortColumn(self.column2)
        self.assertCurrentSortColumn(self.column2)


class CtrlWithSortableColumnsTest(
    CtrlWithColumnsTestCase, CtrlWithSortableColumnsTestsMixin
):
    """
    Classe de test de base pour un contrôle avec des colonnes triables.

    Cette classe est conçue pour faciliter le test des fonctionnalités spécifiques à
    un contrôle qui prend en charge les colonnes triables. Il combine les fonctionnalités
    définies dans `CtrlWithColumnsTestCase` et `CtrlWithSortableColumnsTestsMixin`.
    Utilisez cette classe pour créer des tests pour tous les contrôles qui s'alignent sur ces spécifications
    .

    Attributes:
        frame (wx.Frame): Cadre parent du contrôle testé.
        column1 (type): Première colonne utilisée dans le contrôle.
        column2 (type): La deuxième colonne utilisée dans le contrôle.
    """

    def createControl(self):
        return CtrlWithSortableColumnsUnderTest(
            self.frame,
            style=wx.LC_REPORT,
            columns=[self.column1, self.column2],
        )


class CtrlWithColumnsUnderTest(
    widgets.itemctrl.CtrlWithColumnsMixin, wx.ListCtrl
):
    """
    Gère le contrôle de liste avec une fonctionnalité basée sur les colonnes.

    Fournit un contrôle de liste spécialisé avec des fonctionnalités étendues qui incluent
    la gestion des colonnes. Cette classe hérite de CtrlWithColumnsMixin et
    wx.ListCtrl pour combiner les fonctionnalités des deux.

    Attributes:
        None
    """

    pass


class CtrlWithColumnsTest(
    CtrlWithColumnsTestCase,
    CtrlWithHideableColumnsTestsMixin,
    CtrlWithSortableColumnsTestsMixin,
):
    """Classe de scénarios de test pour les contrôles avec colonnes.

    Cette classe fournit des scénarios de test pour les contrôles qui gèrent les colonnes. Il
    combine des fonctionnalités de test pour les colonnes masquables et les colonnes triables.
    La classe utilise des mix-ins pour étendre son comportement pour des fonctionnalités spécifiques liées aux colonnes
    .

    Attributes:
        column1 (Any): The first column used for testing.
        column2 (Any): The second column used for testing.
        frame (Any): The parent frame or container for the control being tested.
    """

    def createControl(self):
        # NOTE: the resizeableColumn is the column that is not hidden
        return CtrlWithColumnsUnderTest(
            self.frame,
            style=wx.LC_REPORT,
            columns=[self.column1, self.column2],
            resizeableColumn=1,
            columnPopupMenu=None,
        )


class DummyEvent(object):
    """
    Représente une classe d'événement factice pour gérer les objets d'événement.

    Cette classe est un espace réservé ou une implémentation fictive d'un système d'événement
    . Il fournit des méthodes pour interagir avec les objets d'événement tout en
    offrant des fonctionnalités limitées pour la gestion des événements dans un contexte
    donné.

    Attributes:
        eventObject: The event object associated with this instance.
    """

    def __init__(self, eventObject):
        self.eventObject = eventObject

    def Skip(self, *args):
        """Méthode qui ne fait rien pour passer."""
        pass

    def GetColumn(self):
        """Méthode qui retourne le numéro de colonne."""
        return 0

    def GetEventObject(self):
        """Retourne l'objet d'événement associé."""
        return self.eventObject

    def GetPosition(self):
        """Retourne une position fictive."""
        return 0, 0


class ListCtrlWithColumnPopupMenuTest(CtrlWithColumnsTestCase):
    """
    Représente un scénario de test pour un contrôle avec des colonnes, garantissant qu'il prend en charge un menu contextuel de colonnes.

    Cette classe est conçue pour valider la fonctionnalité des contrôles avec prise en charge de colonnes
    dans wxPython. Il comprend la création d'un contrôle de test et d'une méthode test
    pour vérifier le comportement des menus contextuels sur les en-têtes de colonnes.

    Attributes:
        column1 (type): Represents the first column configuration.
        column2 (type): Represents the second column configuration.
        frame (type): The parent frame associated with the control under test.
        control (type): The instance of the control being tested.
    """

    def createControl(self):
        return CtrlWithColumnsUnderTest(
            self.frame,
            style=wx.LC_REPORT,
            columns=[self.column1, self.column2],
            resizeableColumn=1,
            columnPopupMenu=wx.Menu(),
        )

    @tctest.skipOnPlatform("__WXGTK__")  # Popup menu hangs the test
    def testColumnHeaderPopupMenu(self):
        self.control.onColumnPopupMenu(DummyEvent(self.control))


class HyperListTreeCtrlWithColumnPopupMenuTest(CtrlWithColumnsTestCase):
    """
    Represents a test case for a TreeList control with a column popup menu.

    This class is designed to test the functionality of the TreeList control in
    the presence of a popup menu specific to column headers. Il étend les fonctionnalités
    d'un scénario de test de base pour les contrôles avec colonnes et garantit
    que les fonctionnalités spécifiques liées aux menus contextuels fonctionnent comme prévu.

    Methods:
        createControl: Creates and returns the TreeList control with column
            popup menu support.
        testColumnHeaderPopupMenu: Tests the functionality of column header
            popup menu in the TreeList control.
    """

    def createControl(self):
        return widgets.TreeListCtrl(
            self.frame,
            [self.column1, self.column2],
            None,
            None,
            None,
            None,
            columnPopupMenu=wx.Menu(),
        )

    @tctest.skipOnPlatform("__WXGTK__")  # Popup menu hangs the test
    def testColumnHeaderPopupMenu(self):
        self.control.onColumnPopupMenu(DummyEvent(self.control))
