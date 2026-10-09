#!/usr/bin/env python

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

from io import open as file
import os
# Warning: CamelCase variable imported as constant ou lowercase
from xml.etree import ElementTree as xET


# templates.in exporte et les fichiers et dossiers personnels


def dumptemplate(filename, fd):
    # décomposition du nom de fichier
    # chemin
    path, name = os.path.split(filename)
    # fichier
    name, ext = os.path.splitext(name)
    # penser à spliter le résultat sur plusieurs lignes
    # Si l'extension du fichier est .tsktmpl:
    if ext == ".tsktmpl":
        # écrire (en binaire)
        # Warning : Unexpected argument 'rb' et Unresolved attribute reference 'read' for class 'str'
        fd.write("    templates.append((%s, %s))\n" % (repr(name),
                                                       repr(file(filename, "rb").read())))
        # fd.write('    templates.append(({}, {}))\n'.format(repr(name),
        #                                                   repr(file(filename, 'rb').read())))
        # fd.write(f'    templates.append(({repr(name)}, {repr(file(filename, 'rb').read())}))\n')
        # Python version 3.11 does not allow nesting of string literals with the same quote type inside f-strings
        # Python version 3.11 n'autorise pas l'imbrication de chaînes littérales avec le même type de guillemets dans les f-strings
        tree = xET.parse(file(filename, "rb"))
        root = tree.getroot()
        subject = root.find("task").attrib["subject"]
        fd.write("    _(%s)\n" % repr(subject.encode(encoding="UTF-8")))


def dumpDirectory(path):
    fd = file(
        os.path.join(
            "..", "taskcoachlib", "persistence", "xml", "templates.py"
        ),
        "w",
        encoding="utf-8",
    )
    fd.write("# -*- coding: UTF-8 -*-\n\n")
    fd.write("from taskcoachlib.i18n import _\n\n")
    fd.write("def getDefaultTemplates():\n")
    fd.write("    templates = []\n")

    for name in os.listdir(path):
        dumptemplate(os.path.join(path, name), fd)

    fd.write("\n    return templates\n")


if __name__ == "__main__":
    dumpDirectory(".")
