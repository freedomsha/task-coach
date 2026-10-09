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

import wx
from ... import tctest
from .. import dummy
from taskcoachlib import gui as gui
from taskcoachlib import config
import taskcoachlib.gui.toolbar


class ToolBar(gui.toolbar.ToolBar):

    def uiCommands(self, cache=True):
        return []


class ToolBarTest(tctest.wxTestCase):
    def setUp(self):
        """
        Initialisation de l'application et de la fenêtre

        Returns :

        """
        # app = wx.App(False)
        # self.frame = wx.Frame(None)
        gui.init()  # Créer l'application wxPython et une fenêtre
        self.settings = config.Settings(load=False)
        # Création d'une instance de la classe 'ToolBar'
        self.toolbar = ToolBar(self.frame, self.settings)

    def testAppendUICommand(self):
        # gui.init()
        # settings = config.Settings(load=False)
        # toolbar = ToolBar(self.frame, settings)

        # Ajouter une assertion supplémentaire pour vérifier que l'outil a été ajouté avec succés
        uiCommand = dummy.DummyUICommand(menuText="undo", bitmap="undo")
        toolId = self.toolbar.appendUICommand(uiCommand)
        self.assertNotEqual(wx.NOT_FOUND, toolId, "L'outil n'a pas été correctement ajouté à la barre d'outils")

        # Vérifiez si l'outil est effectivement ajouté
        pos = self.toolbar.GetToolPos(toolId)
        self.assertNotEqual(pos, wx.NOT_FOUND, f"L'outil avec l'ID {toolId} "
                                               f"n'a pas été trouvé dans le barre d'outils")

        self.assertNotEqual(wx.NOT_FOUND, self.toolbar.GetToolPos(toolId))


class ToolBarSizeTest(tctest.wxTestCase):
    def testSizeDefault(self):
        self.createToolBarAndTestSize(None, (32, 32))

    def testSizeSmall(self):
        self.createToolBarAndTestSize((16, 16))

    def testSizeMedium(self):
        self.createToolBarAndTestSize((22, 22))

    def testSizeBig(self):
        self.createToolBarAndTestSize((32, 32))

    def createToolBarAndTestSize(self, size, expectedSize=None):
        settings = config.Settings(load=False)
        toolbarArgs = [self.frame, settings]
        if size:
            toolbarArgs.append(size)
        toolbar = ToolBar(*toolbarArgs)
        if not expectedSize:
            expectedSize = size
        self.assertEqual(wx.Size(*expectedSize), toolbar.GetToolBitmapSize())


class ToolBarPerspectiveTest(tctest.wxTestCase):
    def setUp(self):
        class NoBitmapUICommand(dummy.DummyUICommand):
            def appendToToolBar(self, toolbar):
                pass

        class TestFrame(tctest.TestCaseFrame):
            def createToolBarUICommands(self):
                class Test1(NoBitmapUICommand):
                    pass

                class Test2(NoBitmapUICommand):
                    pass

                return [Test1(), None, Test2(), 1]

        self.tbFrame = TestFrame()
        self.settings = config.Settings(load=False)

    def tearDown(self):
        self.tbFrame.Close()

    def test_empty(self):
        bar = gui.toolbar.ToolBar(self.tbFrame, self.settings)
        self.assertEqual(bar.perspective(), "Test1,Separator,Test2,Spacer")

    def test_restrict(self):
        self.tbFrame.toolbarPerspective = "Test1,Spacer"
        bar = gui.toolbar.ToolBar(self.tbFrame, self.settings)
        self.assertEqual(bar.perspective(), "Test1,Spacer")

    def test_does_not_exist(self):
        self.tbFrame.toolbarPerspective = "Test1,Spacer,Test3"
        bar = gui.toolbar.ToolBar(self.tbFrame, self.settings)
        self.assertEqual(bar.perspective(), "Test1,Spacer")
