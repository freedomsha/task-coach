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

import os
import fnmatch
# Remove the distutils package. It was deprecated in Python 3.10 by PEP 632 “Deprecate distutils module”.
# For projects still using distutils and cannot be updated to something else, the setuptools project can be installed:
# it still provides distutils.
# Supprimez le package distutils. Il a été obsolète dans Python 3.10 par la PEP 632 « Module distutils obsolète ».
# Pour les projets utilisant toujours distutils et ne pouvant pas être mis à jour vers autre chose,
# le projet setuptools peut être installé : il fournit toujours distutils.
# from setuptools._distutils.command.clean import clean as base_clean_command
# from setuptools._distutils import log
from setuptools import Command
import logging
import pathlib


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# class clean(base_clean_command):
class clean(Command):
    # user_options = base_clean_command.user_options + \
    #                [("really-clean", "r", "remove even more files")]
    user_options = [
        ("really-clean", "r", "remove even more files"),
    ]
    # boolean_options = base_clean_command.boolean_options + ["really-clean"]
    boolean_options = ["really-clean"]

    def initialize_options(self):
        # def __init__(self):
        # Parameter 'dist' unfilled
        # super().__init__()
        # super(clean, self).initialize_options()
        super().initialize_options()
        # pylint: disable=W0201
        # TODO: Instance attributes are defined outside __init__
        self.really_clean = False
        self.cleaning_patterns = ["*.pyc"]
        self.really_clean_patterns = ["*.bak"]

    def finalize_options(self):
        # super(clean, self).finalize_options()
        super().finalize_options()
        if self.really_clean:
            self.cleaning_patterns.extend(self.really_clean_patterns)

    def run(self):
        # super(clean, self).run()
        super().run()
        # TODO:
        # Unresolved attribute reference 'verbose' and 'dry_run' for class 'Clean'
        # mais d'ou viennent-ils ?
        if not self.verbose:
            logging.info(
                "recursively removing '"
                + "', '".join(self.cleaning_patterns)
                + "'"
            )
        for root, _, files in os.walk("."):
            for pattern in self.cleaning_patterns:
                for filename in fnmatch.filter(files, pattern):
                    # filename = os.path.join(root, filename)
                    filepath = pathlib.Path(root) / filename
                    try:
                        if not self.dry_run:
                            # os.unlink(filename)
                            filepath.unlink()
                        if self.verbose:
                            # log.info("removing '%s'" % filename.strip(".\\"))
                            logging.info(f"removing '{filepath.relative_to(pathlib.Path('.')).as_posix()}'")
                    # except IOError:
                    except OSError:
                        pass
