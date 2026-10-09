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
# Explications des changements :
#
#
# wx.Frame → tk.Toplevel :
#
# DummyWidget hérite maintenant de tk.Toplevel au lieu de wx.Frame.
#
#
# wx.ITEM_NORMAL → tk.NORMAL :
#
# Le paramètre kind dans DummyUICommand utilise tk.NORMAL au lieu de wx.ITEM_NORMAL.
#
#
# Bind → bind :
#
# La méthode Bind est remplacée par bind (en minuscule, convention Tkinter).
#
#
# Suppression des dépendances wxPython :
#
# Les imports et références à wx sont supprimés ou remplacés par des équivalents Tkinter.
#
#
# Logique inchangée :
#
# Les méthodes comme RefreshItems, curselection, select, etc., restent des stubs vides, car leur implémentation dépend de votre logique métier.
#
#
# MainWindow :
#
# La classe MainWindow est conservée comme une classe factice, sans héritage spécifique (équivalent à object en Python 3).

import tkinter as tk
from tkinter import ttk
from taskcoachlib import persistence
from taskcoachlib.guitk.uicommand import base_uicommandtk
from taskcoachlib.guitk.viewer import basetk as viewer_base


class Event:
    """Classe factice pour simuler un événement."""

    def Skip(self):
        pass


class DummyWidget(tk.Toplevel):
    """Widget factice pour les tests, équivalent à wx.Frame."""

    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer

    def RefreshItems(self, *items):
        pass

    def curselection(self):
        return []

    def select(self, *args):
        pass

    def clear_selection(self):
        pass

    def GetItemCount(self):
        return len(self.viewer.presentation())

    def RefreshAllItems(self, *args, **kwargs):
        pass

    def IsAutoResizing(self):
        return False

    def GetMainWindow(self):
        return self

    def bind(self, *args, **kwargs):
        # Équivalent de Bind pour Tkinter
        pass


class DummyUICommand(base_uicommandtk.UICommand):
    """Commande UI factice pour les tests."""

    bitmap = "undo"
    section = "view"
    setting = "setting"

    def __init__(
        self,
        menuText="",
        helpText="",
        bitmap="nobitmap",
        kind=tk.NORMAL,
        id=None,
        bitmap2=None,
        *args,
        **kwargs
    ):
        super().__init__(
            menuText, helpText, bitmap, kind, id, bitmap2, *args, **kwargs
        )
        self.activated = None

    def onCommandActivate(self, event, *args, **kwargs):
        self.activated = True


class ViewerWithDummyWidget(viewer_base.Viewer):
    """Viewer avec un widget factice pour les tests."""

    defaultTitle = "ViewerWithDummyWidget"
    defaultBitmap = ""

    def __init__(self, parent, taskFile, settings, *args, **kwargs):
        super().__init__(parent, taskFile, settings, *args, **kwargs)
        self._columns = None

    def domainObjectsToView(self):
        return self.taskFile.tasks()

    def createWidget(self):
        self._columns = self._createColumns()
        return DummyWidget(self)

    def _createColumns(self):
        return []


class TaskFile(persistence.TaskFile):
    """Classe factice pour simuler un fichier de tâches."""

    raiseError = None

    def load(self, *args, **kwargs):
        if self.raiseError:
            raise self.raiseError

    merge = save = saveas = load


class MainWindow:
    """Classe factice pour simuler la fenêtre principale."""

    showFindDialog = None
