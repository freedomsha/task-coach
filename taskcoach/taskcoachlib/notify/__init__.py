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

from taskcoachlib import operating_system

# TODO: changer les import !
if operating_system.isWindows():
    from .notifier_windows import *
    from .notifier_growl import GrowlNotifier
elif operating_system.isMac():
    from .notifier_growl import GrowlNotifier

# Todo : 
# get selection ("wx" or "tk") if available
try:
    from taskcoachlib.config.arguments import get_gui  # may raise during early import
except Exception:
    def get_gui() -> Any:  # fallback if config not importable yet
        return None
# Si wx
if get_gui() == "wx":
    from .notifier_universal import *
# Si tk
elif get_gui() == "tk":
    from .notifier_universaltk import *

from .notifier import AbstractNotifier
