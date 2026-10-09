# -*- coding: utf-8 -*-

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
# TODO : imports à revoir !(uicommand)
import logging

# from builtins import str
# from builtins import object
import wx
# from ....taskcoachlib.thirdparty.pubsub import pub

from pubsub import pub
from ... import tctest
from taskcoachlib import gui, config
from taskcoachlib.gui import uicommand, menu
from taskcoachlib.gui.uicommand import settings_uicommand
from taskcoachlib.gui.uicommand.uicommand import ViewerSortCaseSensitive
from taskcoachlib.gui.uicommand.uicommand import ViewerSortOrderCommand,  ViewerSortByTaskStatusFirst, ViewerSortByCommand
# from .base_uicommand import UICommand
# from .settings_uicommand import UIRadioCommand, UICheckCommand
# from .uicommand import *
# from .uicommandcontainer import UICommandContainerMixin
from taskcoachlib.domain import task, category, date

log = logging.getLogger(__name__)


class MockViewerContainer(object):
    def __init__(self):
        self.__sortBy = "subject"
        self.__ascending = True
        self.selection = []
        self.showingCategories = False

    def settingsSection(self):
        return "section"

    def curselection(self):
        return self.selection  # pragma: no cover

    def isShowingCategories(self):
        return self.showingCategories  # pragma: no cover

    def isSortable(self):
        return True

    def sortBy(self, sortKey):
        self.__sortBy = sortKey

    def isSortedBy(self, sortKey):
        return sortKey == self.__sortBy

    def isSortOrderAscending(self, *args, **kwargs):  # pylint: disable=W0613
        return self.__ascending

    def setSortOrderAscending(self, ascending=True):
        self.__ascending = ascending

    def isSortByTaskStatusFirst(self):
        return True

    def isSortCaseSensitive(self):
        return True

    def getSortUICommands(self):
        return [
            uicommand.uicommand.ViewerSortOrderCommand(viewer=self),
            uicommand.uicommand.ViewerSortCaseSensitive(viewer=self),
            uicommand.uicommand.ViewerSortByTaskStatusFirst(viewer=self),
            None,
            uicommand.uicommand.ViewerSortByCommand(
                viewer=self, value="subject", menuText="Sub&ject", helpText="help"
            ),
            uicommand.uicommand.ViewerSortByCommand(
                viewer=self,
                value="description",
                menuText="&Description",
                helpText="help",
            ),
        ]


class MenuTestCase(tctest.wxTestCase):
    def setUp(self):
        super().setUp()
        self.frame.viewer = MockViewerContainer()
        self.menu = gui.menu.Menu(self.frame)
        menuBar = wx.MenuBar()
        menuBar.Append(self.menu, "menu")
        self.frame.SetMenuBar(menuBar)


class MenuTest(MenuTestCase):
    def testLenEmptyMenu(self):
        self.assertEqual(0, len(self.menu))

    def testLenNonEmptyMenu(self):
        self.menu.AppendSeparator()
        self.assertEqual(1, len(self.menu))


class MenuWithBooleanMenuItemsTestCase(MenuTestCase):
    def setUp(self):
        super().setUp()
        self.settings = config.Settings(load=False)
        self.commands = self.createCommands()

    def createCommands(self):
        raise NotImplementedError  # pragma: no cover

    def assertMenuItemsChecked(self, *expectedStates):
        self.menu.clearMenu()  # Assurez-vous que le menu est vide avant d'ajouter les commandes
        for command in self.commands:
            log.debug(f"MenuTest.assertMenuItemsChecked: Ajout de la commande: {command}")
            self.menu.appendUICommand(command)
        self.menu.UpdateUI()  # Force la mise à jour de l'interface utilisateur
        log.error(f"MenuTest.assertMenuItemsChecked: Après UpdateUI()", stack_info=True)
        # self.menu.openMenu()
        # print(f"MenuTest.assertMenuItemsChecked: Menu ouvert")

        for index, shouldBeChecked in enumerate(expectedStates):
            # isChecked = self.menu.FindItemByPosition(index).IsChecked()
            menuItem = self.menu.FindItemByPosition(index)
            # if shouldBeChecked:
            #     # self.failUnless(isChecked)
            #     self.assertTrue(isChecked)
            # else:
            #     # self.failIf(isChecked)
            #     self.assertFalse(isChecked)
            if menuItem:
                isChecked = menuItem.IsChecked()
                log.debug(f"MenuTest.assertMenuItemsChecked: Élément à l'index {index}, isChecked: {isChecked}, shouldBeChecked: {shouldBeChecked}")
                # if shouldBeChecked:
                self.assertTrue(isChecked, f"L'élément à l'index {index} devrait être coché.")
                # else:
                #     self.assertFalse(isChecked, f"L'élément à l'index {index} ne devrait pas être coché.")
            else:
                self.fail(f"Aucun élément trouvé à la position {index} dans le menu.")
        # self.menu.Close()  # Fermer le menu après la vérification (bonne pratique pour les tests)
        # self.frame.Close()  # Fermer le menu après la vérification (bonne pratique pour les tests)
        # print(f"MenuTest.assertMenuItemsChecked: Menu fermé")


class MenuWithCheckItemsTest(MenuWithBooleanMenuItemsTestCase):
    def createCommands(self):
        return [
            uicommand.settings_uicommand.UICheckCommand(
                settings=self.settings, section="view", setting="statusbar"
            )
        ]

    def testCheckedItem(self):
        self.settings.set("view", "statusbar", "True")
        self.assertMenuItemsChecked(True)

    def testUncheckedItem(self):
        self.settings.set("view", "statusbar", "False")
        self.assertMenuItemsChecked(False)


class MenuWithRadioItemsTest(MenuWithBooleanMenuItemsTestCase):
    def createCommands(self):
        return [
            settings_uicommand.UIRadioCommand(
                settings=self.settings, section="view", setting="toolbar", value=value
            )
            for value in [None, (16, 16)]
        ]

    def testRadioItem_FirstChecked(self):
        self.settings.setvalue("view", "toolbar", None)
        self.assertMenuItemsChecked(True, False)

    def testRadioItem_SecondChecked(self):
        self.settings.setvalue("view", "toolbar", (16, 16))
        self.assertMenuItemsChecked(False, True)


class MockIOController(object):
    def __init__(self):
        self.openCalled = False

    def open(self, *args, **kwargs):  # pylint: disable=W0613
        self.openCalled = True


class RecentFilesMenuTest(tctest.wxTestCase):
    def setUp(self):
        super().setUp()
        self.ioController = MockIOController()
        self.settings = config.Settings(load=False)
        self.initialFileMenuLength = len(self.createFileMenu())
        self.filename1 = "c:/Program Files/TaskCoach/test.tsk"
        self.filename2 = "c:/two.tsk"
        self.filenames = []
        # self.menu = RecentFilesMenu()  # Initialisez le menu récent.
        # Remplacez par les chemins réels des fichiers récents
        self.expected_recent_files = [self.filename1, self.filename2]

    def createFileMenu(self):
        return gui.menu.FileMenu(self.frame, self.settings, self.ioController, None)

    def setRecentFilesAndCreateMenu(self, *filenames):
        self.addRecentFiles(*filenames)
        self.menu = self.createFileMenu()  # pylint: disable=W0201

    def addRecentFiles(self, *filenames):
        self.filenames.extend(filenames)
        self.settings.set("file", "recentfiles", str(list(self.filenames)))

    def assertRecentFileMenuItems(self, *expectedFilenames):

        expectedFilenames = expectedFilenames or self.filenames
        self.openMenu()
        # Assurez-vous que le nombre d'éléments récents est correct
        # self.assertEqual(len(self.menu.GetMenuItems()), len(self.expected_recent_files))
        # AssertionError: 10 != 2

        numberOfMenuItemsAdded = len(expectedFilenames)
        if numberOfMenuItemsAdded > 0:
            numberOfMenuItemsAdded += 1  # the extra separator
        self.assertEqual(
            self.initialFileMenuLength + numberOfMenuItemsAdded, len(self.menu)
        )

        # for expected_label in self.expected_recent_files:
        #     # Trouver l'élément du menu correspondant
        #     item = next((item for item in self.menu.GetMenuItems() if expected_label in
        #                  item.GetItemLabelText()), None)
        #     if not item:
        #         raise AssertionError(f"Élément récent {expected_label} non trouvé dans le menu")
        #
        #     # Vérifier que l'étiquette de l'élément correspond à ce qui est attendu
        #     self.assertEqual(expected_label, item.GetItemLabelText()[1:].strip())

        for index, expectedFilename in enumerate(expectedFilenames):
            menuItem = self.menu.FindItemByPosition(
                self.initialFileMenuLength - 1 + index
            )
            # Apparently the '&' can also be a '_' (seen on Ubuntu)
            # expectedLabel = u'&%d %s' % (index + 1, expectedFilename)
            expectedLabel = f"&{index + 1:d} {expectedFilename}"
            # self.assertEqual(expectedLabel[1:], menuItem.GetText()[1:])
            # GetText Deprecated since version 4.0.0: This function is deprecated in favour of GetItemLabel.
            log.debug(f"expectedLabel={expectedLabel}")
            log.debug(f"menuItem={menuItem.GetItemLabel()}")
            self.assertEqual(expectedLabel[1:], menuItem.GetItemLabelText()[1:])  # AssertionError

    def openMenu(self):
        self.menu.onOpenMenu(wx.MenuEvent(menu=self.menu))

    def testNoRecentFiles(self):
        self.setRecentFilesAndCreateMenu()
        self.assertRecentFileMenuItems()

    def testOneRecentFileWhenCreatingMenu(self):
        self.setRecentFilesAndCreateMenu(self.filename1)
        self.assertRecentFileMenuItems()

    def testTwoRecentFilesWhenCreatingMenu(self):
        self.setRecentFilesAndCreateMenu(self.filename1, self.filename2)
        self.assertRecentFileMenuItems()

    def testAddRecentFileAfterCreatingMenu(self):
        self.setRecentFilesAndCreateMenu()
        self.addRecentFiles(self.filename1)
        self.assertRecentFileMenuItems()

    def testOneRecentFileWhenCreatingMenuAndAddOneRecentFileAfterCreatingMenu(self):
        self.setRecentFilesAndCreateMenu(self.filename1)
        self.addRecentFiles(self.filename2)
        self.assertRecentFileMenuItems()

    def testOpenARecentFile(self):
        self.setRecentFilesAndCreateMenu(self.filename1)
        self.openMenu()
        menuItem = self.menu.FindItemByPosition(self.initialFileMenuLength - 1)
        self.menu.invokeMenuItem(menuItem)
        # self.failUnless(self.ioController.openCalled)
        self.assertTrue(self.ioController.openCalled)

    def testNeverShowMoreThanTheMaximumNumberAllowed(self):
        self.setRecentFilesAndCreateMenu(self.filename1, self.filename2)
        self.settings.set("file", "maxrecentfiles", "1")
        self.assertRecentFileMenuItems(self.filename1)


class ViewMenuTestCase(tctest.wxTestCase):
    def setUp(self):
        # super(ViewMenuTestCase, self).setUp()
        super().setUp()
        self.settings = config.Settings(load=False)
        self.viewerContainer = MockViewerContainer()
        self.menuBar = wx.MenuBar()
        self.parentMenu = wx.Menu()
        self.menuBar.Append(self.parentMenu, "parentMenu")
        self.menu = self.createMenu()
        self.parentMenu.AppendSubMenu(self.menu, "menu")
        self.frame.SetMenuBar(self.menuBar)

    def createMenu(self):
        self.frame.viewer = self.viewerContainer
        tcmenu = gui.menu.SortMenu(self.frame, self.parentMenu, "menu")
        tcmenu.updateMenu()
        return tcmenu

    def testSortOrderAscending(self):
        self.viewerContainer.setSortOrderAscending(True)
        self.menu.UpdateUI()
        self.menu.openMenu()
        # self.failUnless(self.menu.FindItemByPosition(0).IsChecked())
        self.assertTrue(self.menu.FindItemByPosition(0).IsChecked())

    def testSortOrderDescending(self):
        self.viewerContainer.setSortOrderAscending(False)
        self.menu.UpdateUI()
        self.menu.openMenu()
        # self.failIf(self.menu.FindItemByPosition(0).IsChecked())
        self.assertFalse(self.menu.FindItemByPosition(0).IsChecked())

    def testSortBySubject(self):
        self.viewerContainer.sortBy("subject")
        self.menu.UpdateUI()
        self.menu.openMenu()
        # self.failUnless(self.menu.FindItemByPosition(4).IsChecked())
        self.assertTrue(self.menu.FindItemByPosition(4).IsChecked())
        # self.failIf(self.menu.FindItemByPosition(5).IsChecked())
        self.assertFalse(self.menu.FindItemByPosition(5).IsChecked())

    def testSortByDescription(self):
        self.viewerContainer.sortBy("description")
        self.menu.UpdateUI()
        self.menu.openMenu()
        log.debug(f"MenuTest.ViewMenuTestCase.testSortByDescription : self.menu={self.menu}")
        # MenuTest.ViewMenuTestCase.testSortByDescription : self.menu=<taskcoachlib.gui.menu.SortMenu object at 0x7b1a7af935b0>
        # self.failIf(self.menu.FindItemByPosition(4).IsChecked())
        self.assertFalse(self.menu.FindItemByPosition(4).IsChecked())  # invalid menu index !
        # self.failUnless(self.menu.FindItemByPosition(5).IsChecked())
        self.assertTrue(self.menu.FindItemByPosition(5).IsChecked())


class StartEffortForTaskMenuTest(tctest.wxTestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.tasks = task.TaskList()
        self.menu = gui.menu.StartEffortForTaskMenu(self.frame, self.tasks)

    def addTask(self, subject="Subject"):
        newTask = task.Task(subject=subject, plannedStartDateTime=date.Now())
        self.tasks.append(newTask)
        return newTask

    def addParentAndChild(self, parentSubject="Subject", childSubject="Subject"):
        parent = self.addTask(parentSubject)
        child = self.addTask(childSubject)
        parent.addChild(child)
        return parent, child

    def testMenuIsEmptyInitially(self):
        self.assertEqual(0, len(self.menu))

    def testNewTasksAreAdded(self):
        self.addTask()
        self.assertEqual(1, len(self.menu))

    def testDeletedTasksAreRemoved(self):
        newTask = self.addTask()
        self.tasks.remove(newTask)
        self.assertEqual(0, len(self.menu))

    def testNewChildTasksAreAdded(self):
        self.addParentAndChild()
        self.assertEqual(2, len(self.menu))

    def testDeletedChildTasksAreRemoved(self):
        child = self.addParentAndChild()[1]
        self.tasks.remove(child)
        self.assertEqual(1, len(self.menu))

    def testTaskWithNonAsciiSubject(self):
        self.addParentAndChild("Jérôme", "Jîrôme")
        self.menu.updateMenuItems()
        self.assertEqual(2, len(self.menu))


class ToggleCategoryMenuTest(tctest.wxTestCase):
    def setUp(self):
        self.categories = category.CategoryList()
        self.category1 = category.Category("Category 1")
        self.category2 = category.Category("Category 2")
        self.viewerContainer = MockViewerContainer()
        self.menu = gui.menu.ToggleCategoryMenu(
            self.frame, self.categories, self.viewerContainer
        )

    def setUpSubcategories(self):
        self.category1.addChild(self.category2)
        self.categories.append(self.category1)

    def testMenuInitiallyEmpty(self):
        self.assertEqual(0, len(self.menu))

    def testOneCategory(self):
        self.categories.append(self.category1)
        self.assertEqual(1, len(self.menu))

    def testTwoCategories(self):
        self.categories.extend([self.category1, self.category2])
        self.assertEqual(2, len(self.menu))

    def testSubcategory(self):
        self.setUpSubcategories()
        self.assertEqual(3, len(self.menu))

    def testSubcategorySubmenuLabel(self):
        self.setUpSubcategories()
        # self.assertEqual(
        #     gui.menu.ToggleCategoryMenu.subMenuLabel(self.category1),
        #     self.menu.GetMenuItems()[2].GetLabel(),
        # )
        checkedItems = [item for item in list(self.menu.GetMenuItems()) if item.IsChecked()]
        # self.assertEqual(
        #     gui.menu.ToggleCategoryMenu.subMenuLabel(self.category1),
        #     checkedItems[2].GetLabel(),
        # )
        # Erreurs AttributeError: 'MenuItem' object has no attribute 'GetLabel'.
        # Did you mean: 'GetAccel'? : Ces erreurs indiquent que la méthode GetLabel()
        # n'est plus disponible sur l'objet wx.MenuItem.
        # Le message suggère d'utiliser GetAccel().
        # Cependant, la méthode correcte pour obtenir le texte de l'étiquette
        # d'un élément de menu est GetItemLabelText().
        # Correction : Remplacez GetLabel() par GetItemLabelText() dans les tests concernés.
        self.assertEqual(
            gui.menu.ToggleCategoryMenu.subMenuLabel(self.category1),
            checkedItems[2].GetItemLabelText(),
        )

    def testSubcategorySubmenuItemLabel(self):
        self.setUpSubcategories()
        checkedItems = [item for item in list(self.menu.GetMenuItems()) if item.IsChecked()]
        # subMenu = self.menu.GetMenuItems()[2].GetSubMenu()
        subMenu = checkedItems[2].GetSubMenu()
        label = subMenu.GetMenuItems()[0].GetLabel()
        self.assertEqual(self.category2.subject(), label)

    def testMutualExclusiveSubcategories_AreCheckItems(self):
        self.category1.makeSubcategoriesExclusive()
        self.setUpSubcategories()
        category3 = category.Category("Category 3")
        self.category1.addChild(category3)
        # subMenu = self.menu.GetMenuItems()[2].GetSubMenu()
        checkedItems = [item for item in list(self.menu.GetMenuItems()) if item.IsChecked()]
        subMenu = checkedItems[2].GetSubMenu()

        for subMenuItem in subMenu.GetMenuItems():
            self.assertEqual(wx.ITEM_CHECK, subMenuItem.GetKind())

    def testMutualExclusiveSubcategories_NoneChecked(self):
        self.category1.makeSubcategoriesExclusive()
        self.setUpSubcategories()
        category3 = category.Category("Category 3")
        self.category1.addChild(category3)
        # checkedItems = [item for item in list(self.menu.GetMenuItems()) if item.IsChecked()]
        subMenuItems = self.menu.GetMenuItems()[2].GetSubMenu().GetMenuItems()
        checkedItems = [item for item in subMenuItems if item.IsChecked()]
        self.assertFalse(checkedItems)

    def testMutualExclusiveSubcategoriesWithSubcategories(self):
        self.category1.makeSubcategoriesExclusive()
        self.setUpSubcategories()
        category3 = category.Category("Category 3")
        self.category1.addChild(category3)
        category4 = category.Category("Category 4")
        category3.addChild(category4)
        # checkedItems = [item for item in list(self.menu.GetMenuItems()) if item.IsChecked()]
        subMenuItems = self.menu.GetMenuItems()[2].GetSubMenu().GetMenuItems()
        checkedItems = [item for item in subMenuItems if item.IsChecked()]
        # self.failIf(checkedItems)
        self.assertFalse(checkedItems)


class TaskTemplateMenuTest(tctest.wxTestCase):
    def testMenuIsUpdatedWhenTemplatesAreSaved(self):
        uicommands = [None]  # Just a separator for testing purposes

        class TaskTemplateMenu(gui.menu.TaskTemplateMenu):
            def getUICommands(self):
                return uicommands

        settings = config.Settings(load=False)
        taskList = task.TaskList()
        menu = TaskTemplateMenu(self.frame, taskList, settings)
        self.assertEqual(1, len(menu))
        uicommands.append(None)  # Add another separator
        pub.sendMessage("templates.saved")
        self.assertEqual(2, len(menu))
