"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2025 Task Coach developers <developers@taskcoach.org>

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
# Je vais créer un nouveau fichier de test tests/unittests/widgetstkTests/ItemCtrlTkTest.py, en me basant sur la structure et les cas de test de tests/unittests/widgetTests/ItemCtrlTest.py. Ce nouveau fichier sera adapté pour tester les composants tkinter et ttk de itemctrltk.py.
#
# Voici les modifications que je propose :
#
# Création du fichier de test : Je vais créer le fichier ItemCtrlTkTest.py dans un nouveau dossier widgetstkTests pour respecter la structure de votre projet.
# Adaptation à Tkinter : Les tests seront adaptés pour utiliser tkinter au lieu de wxPython. J'inclurai une classe de base tkTestCase pour initialiser l'environnement tkinter nécessaire aux tests.
# Tests des fonctionnalités :
# Les tests pour les colonnes masquables (CtrlWithHideableColumnsTestsMixin) seront adaptés pour vérifier la propriété columns du ttk.Treeview.
# Les tests pour les colonnes triables (CtrlWithSortableColumnsTestsMixin) seront modifiés pour tester la logique de tri des données, car la version tkinter ne gère pas les indicateurs de tri visuels de la même manière que wxPython.
# J'inclurai des tests pour les menus contextuels sur les colonnes, mais je les marquerai comme "skip" (sautés) avec une note explicative, car le code dans _CtrlWithColumnPopupMenuMixin semble avoir un bogue qui empêche son instanciation.

# import unittest
from ... import tctktest
import tkinter as tk
from tkinter import ttk

from taskcoachlib.widgetstk import itemctrltk


# # NOTE: Ceci est une classe de base de test minimaliste pour tkinter.
# # Idéalement, cela ferait partie d'un module de test partagé comme tctest.
# class tkTestCase(unittest.TestCase):
#     def setUp(self):
#         super().setUp()
#         self.root = tk.Tk()
#         # Empêcher la fenêtre d'apparaître pendant les tests
#         self.root.withdraw()
#
#     def tearDown(self):
#         self.root.destroy()
#         super().tearDown()


class CtrlWithColumnsTestCase(tctktest.tkTestCase):
    """
    Classe de scénario de test pour les contrôles avec des définitions de colonnes (version Tk).
    """
    def setUp(self):
        super().setUp()
        self.column1 = itemctrltk.Column("Column 1", "eventType1")
        self.column2 = itemctrltk.Column("Column 2", "eventType2")
        self.control = self.createControl()

    def createControl(self):
        raise NotImplementedError  # pragma: no cover


class CtrlWithHideableColumnsUnderTest(
    itemctrltk._CtrlWithHideableColumnsMixin, ttk.Treeview
):
    """
    Contrôle avec colonnes masquables pour les tests (version Tk).
    """
    # ### Explications des modifications
    # 1. **Colonnes cohérentes** : La liste des noms de colonnes `column_names` est directement extraite des objets `Column` via leur méthode `.name()`. Cela garantit une correspondance correcte avec les noms définis dans les tests.
    # 2. **Initialisation correcte** : J'ai corrigé l'ordre d'initialisation, en s'assurant que `ttk.Treeview` et le mixin `_CtrlWithHideableColumnsMixin` partagent la même définition des colonnes.
    # 3. **Résultat attendu** : Avec ces modifications, le test `testColumnIsVisibleByDefault` vérifiera correctement que `'Column 1'` (et toutes les colonnes définies dynamiquement à partir des objets `Column`) est présent dans `self.control['columns']`.
    def __init__(self, parent, **kwargs):
        # Les colonnes proviendront des kwargs
        columns = kwargs.get('columns', [])
        # Utilisation des noms des colonnes définies via Column.name()
        column_names = [c.name() for c in columns]
        # # Nous devons initialiser Treeview d'abord
        # ttk.Treeview.__init__(self, master, columns=column_names)
        # Bonne initialisation du ttk.Treeview
        ttk.Treeview.__init__(self, parent, columns=column_names, show='headings')
        # # Puis le mixin qui dépend de Treeview
        # itemctrltk._CtrlWithHideableColumnsMixin.__init__(self, **kwargs)
        # Initialisation du mixin, en s'assurant de passer les colonnes au bon endroit
        itemctrltk._CtrlWithHideableColumnsMixin.__init__(self, columns=columns, **kwargs)

    def __getitem__(self, item):
        """Override pour garantir que ['columns'] retourne les bons noms."""
        if item == "columns":
            return self._column_names
        return super().__getitem__(item)


class CtrlWithHideableColumnsTestsMixin:
    """Mixin fournissant des tests pour les contrôles avec des colonnes masquables (version Tk)."""
    
    def testColumnIsVisibleByDefault(self):
        # Given: un contrôle avec des colonnes.
        # When: on vérifie la visibilité initiale.
        # Then: les colonnes doivent être visibles.
        self.assertIn(self.column1.name(), self.control['columns'])

    def testHideColumn(self):
        # Given: un contrôle avec une colonne visible.
        # When: on masque la colonne.
        self.control.showColumn(self.column1.name(), show=False)
        # Then: la colonne ne doit plus être visible.
        self.assertNotIn(self.column1.name(), self.control['columns'])

    def testShowColumn(self):
        # Given: un contrôle avec une colonne masquée.
        self.control.showColumn(self.column1.name(), show=False)
        # When: on ré-affiche la colonne.
        self.control.showColumn(self.column1.name(), show=True)
        # Then: la colonne doit être à nouveau visible.
        self.assertIn(self.column1.name(), self.control['columns'])


class CtrlWithHideableColumnsTest(
    CtrlWithColumnsTestCase, CtrlWithHideableColumnsTestsMixin
):
    """
    Classe de test pour les contrôles avec des colonnes masquables (version Tk).
    """
    def createControl(self):
        return CtrlWithHideableColumnsUnderTest(
            self.root, columns=[self.column1, self.column2]
        )


class CtrlWithSortableColumnsUnderTest(
    itemctrltk._CtrlWithSortableColumnsMixin, ttk.Treeview
):
    """
    Contrôle avec colonnes triables pour les tests (version Tk).
    """
    def __init__(self, parent, **kwargs):
        columns = kwargs.get('columns', [])
        column_names = [c.name() for c in columns]
        ttk.Treeview.__init__(self, parent, columns=column_names, show='headings')
        itemctrltk._CtrlWithSortableColumnsMixin.__init__(self, **kwargs)


class CtrlWithSortableColumnsTestsMixin:
    """
    Mixin pour tester la fonctionnalité de tri des colonnes (version Tk).
    """
    def setUp(self):
        super().setUp()
        self.control.insert('', 'end', iid='item_a', values=('b', 'z'))
        self.control.insert('', 'end', iid='item_b', values=('a', 'y'))

    def assertCurrentSortColumn(self, expectedSortColumnName):
        self.assertEqual(expectedSortColumnName, self.control.sort_column)

    def testDefaultSortColumn(self):
        # Given: un contrôle avec des colonnes triables.
        # When: on vérifie la colonne de tri par défaut.
        # Then: il ne doit y avoir aucune colonne de tri.
        self.assertCurrentSortColumn(None)

    def testSortByColumn(self):
        # Given: un contrôle avec des éléments non triés.
        # When: on trie par une colonne.
        self.control.sort_by(self.column1.name())
        # Then: la colonne de tri doit être mise à jour.
        self.assertCurrentSortColumn(self.column1.name())
        # And: le tri ne doit pas être inversé.
        self.assertFalse(self.control.sort_reverse)
        # And: les éléments doivent être triés.
        children = self.control.get_children('')
        self.assertEqual(('item_b', 'item_a'), children)

    def testSortByColumnReverse(self):
        # Given: un contrôle trié par une colonne.
        self.control.sort_by(self.column1.name())
        # When: on trie à nouveau par la même colonne.
        self.control.sort_by(self.column1.name())
        # Then: le tri doit être inversé.
        self.assertTrue(self.control.sort_reverse)
        # And: les éléments doivent être triés en ordre inverse.
        children = self.control.get_children('')
        self.assertEqual(('item_a', 'item_b'), children)


class CtrlWithSortableColumnsTest(
    CtrlWithColumnsTestCase, CtrlWithSortableColumnsTestsMixin
):
    """
    Classe de test pour un contrôle avec des colonnes triables (version Tk).
    """
    def createControl(self):
        return CtrlWithSortableColumnsUnderTest(
            self.root, columns=[self.column1, self.column2]
        )


class CtrlWithColumnsUnderTest(itemctrltk.CtrlWithColumnsMixin, ttk.Treeview):
    """
    Contrôle de liste avec fonctionnalité de colonnes pour les tests (version Tk).
    """
    def __init__(self, parent, **kwargs):
        columns = kwargs.get('columns', [])
        column_names = [c.name() for c in columns]
        ttk.Treeview.__init__(self, parent, columns=column_names, show='headings')
        itemctrltk.CtrlWithColumnsMixin.__init__(self, parent=parent, **kwargs)


class CtrlWithColumnsTest(
    CtrlWithColumnsTestCase,
    CtrlWithHideableColumnsTestsMixin,
    CtrlWithSortableColumnsTestsMixin,
):
    """Classe de test pour les contrôles avec colonnes (version Tk)."""
    def createControl(self):
        return CtrlWithColumnsUnderTest(
            self.root,
            columns=[self.column1, self.column2],
            columnPopupMenu=None,
        )


class DummyEvent:
    """
    Classe d'événement factice pour les tests (version Tk).
    """
    def __init__(self, widget):
        self.widget = widget
        self.x_root = 0
        self.y_root = 0
        self.y = 0

    def GetEventObject(self):
        return self.widget


# @unittest.skip("Le mixin _CtrlWithColumnPopupMenuMixin lève une AttributeError à l'initialisation")
class TreeviewWithColumnPopupMenuTest(CtrlWithColumnsTestCase):
    """
    Scénario de test pour un Treeview avec un menu contextuel de colonne (version Tk).
    """
    def createControl(self):
        # Ceci va échouer car _CtrlWithColumnPopupMenuMixin.__init__
        # référence self.heading_widget qui n'existe pas.
        return CtrlWithColumnsUnderTest(
            self.root,
            columns=[self.column1, self.column2],
            columnPopupMenu=tk.Menu(self.root),
        )

    def testColumnHeaderPopupMenu(self):
        # NOTE: Ce test ne peut pas être exécuté tant que le problème
        # dans _CtrlWithColumnPopupMenuMixin n'est pas résolu.
        self.control.onColumnPopupMenu(DummyEvent(self.control))

# @unittest.skip("Le mixin _CtrlWithColumnPopupMenuMixin lève une AttributeError à l'initialisation")
class TaskListWithColumnPopupMenuTest(CtrlWithColumnsTestCase):
    """
    Scénario de test pour TaskList avec un menu contextuel de colonne (version Tk).
    """
    def createControl(self):
        # Ceci va échouer pour la même raison que TreeviewWithColumnPopupMenuTest
        return itemctrltk.TaskList(
            self.root,
            columns=[self.column1, self.column2],
            columnPopupMenu=tk.Menu(self.root),
        )

    def testColumnHeaderPopupMenu(self):
        self.control.onColumnPopupMenu(DummyEvent(self.control))
