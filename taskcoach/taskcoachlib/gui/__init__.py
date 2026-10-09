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

#  Les packages les plus importants et les plus volumineux sont les packages
#  de domaine qui contiennent des classes pour les objets de domaine et
#  le package gui qui contient des visualiseurs, des boîtes de dialogue et d'autres composants gui.


# print("gui.init: initialisation de splash")
from .splash import SplashScreen

# def SplashScreen(*args, **kwargs):
#     """Proxy vers SplashScreen avec import différé."""
#     from .splash import SplashScreen
#
#     return SplashScreen(*args, **kwargs)


# print("gui.init: initialisation de MainWindow")
from .mainwindow import MainWindow

# def MainWindow(*args, **kwargs):
#     from .mainwindow import MainWindow
#
#     return MainWindow(*args, **kwargs)


# print("gui.init: initialisation de editor")
from .dialog.editor import TaskEditor, EffortEditor, CategoryEditor

# print("gui.init: initialisation de Preferences")
from .dialog.preferences import Preferences

# print("gui.init: initialisation de IOController")
from .iocontroller import IOController

# def IOController(*args, **kwargs):
#     from .iocontroller import IOController
#
#     return IOController(*args, **kwargs)


# from .mainwindow import MainWindow  # Doublon !
# print("gui.init: initialisation de ReminderController")
from .remindercontroller import ReminderController

# print("gui.init: initialisation de TaskBarIcon")
from .taskbaricon import TaskBarIcon

# def TaskBarIcon(*args, **kwargs):
#     """Proxy vers TaskBarIcon avec import différé."""
#     from .taskbaricon import TaskBarIcon
#
#     return TaskBarIcon(*args, **kwargs)


# print("gui.init: initialisation de ArtProvider")
# from .artprovider import init, itemImages
# Remplacer par un import différé:
def init():
    from taskcoachlib.gui import artprovider

    artprovider.init()


# from .artprovider import itemImages
def itemImages(*args, **kwargs):
    """Proxy vers artprovider.itemImages avec import différé."""
    from taskcoachlib.gui import artprovider  # Import tardif

    return artprovider.itemImages(*args, **kwargs)


# print("gui.init: initialisation de viewer")
from . import viewer

# __all__ = ["dialog", "icons", "idlecontroller", "init", "IOController", "iphone", "itemImages", "mainwindow", "menu", "newid", "printer", "remindercontroller", "splash", "status", "toolbar", "uicommand", "viewer", "windowdimensionstracker", "wizard"]
