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

import logging

# gui_used ?
from taskcoachlib.config.arguments import get_gui

log = logging.getLogger(__name__)
gui_name = get_gui()
if gui_name == "wx":
    log.info("application avec wx")
    from taskcoachlib.application.application import Application
# try:
#     from .application import Application
#
# except ImportError:
#     from taskcoachlib.application.application import Application, TkinterApplication
elif gui_name == "tk":
    log.info("application avec tk")
    from taskcoachlib.application.tkapplication import TkinterApplication
