"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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

# 1.
# watchdog : C'est une bibliothèque Python standard pour surveiller les fichiers.
# L'utiliser permet de simplifier le code
# en remplaçant potentiellement plusieurs fichiers spécifiques à chaque OS
# (fs_inotify, fs_win32, etc.) par une seule interface unifiée.
import logging
import platform

# from taskcoachlib.filesystem.fs_poller import *
from taskcoachlib.filesystem.fs_poller import FilesystemPollerNotifier

log = logging.getLogger(__name__)

try:
    from .fs_watchdog import *
except ImportError:
    log.warning(
        "watchdog library not installed. File monitoring will use polling fallback "
        "(less efficient). Install watchdog for better performance: pip install watchdog"
    )

_system = platform.system()
log.info("__init__ : _system=%s", _system)
if _system == "Linux":
    from .fs_inotify import *
elif _system == "Windows":
    from .fs_win32 import *
elif _system == "Darwin":
    from .fs_darwin import *
else:

    class FilesystemNotifier(FilesystemPollerNotifier):
        """
        Cette classe se base sur FilesystemPollerNotifier qui interroge le système de fichiers pour les modifications.

        Cette classe étend la classe de base `NotifierBase` et utilise le threading pour vérifier périodiquement
        si le fichier associé a été modifié. Si une modification est détectée, la méthode `onFileChanged`
        est appelée.
        """

        pass
