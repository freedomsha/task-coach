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

# Futurize ajoute 3 ligne :
from __future__ import print_function
# from future import standard_library
# standard_library.install_aliases()
try:
    from taskcoachlib.i18n import po2dict
except ImportError:
    from ..taskcoachlib.i18n import po2dict

import glob
import shutil
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import tarfile


# urllib.request est seul nécessaire, parse & error sont inutils


""" crée le répertoire de traduction taskcoachlib/i18n """
projectRoot = os.path.abspath('..')
if projectRoot not in sys.path:
    sys.path.insert(0, projectRoot)


# Shadows name 'url' from outer scope
def downloadtranslations(url):  # url -> urlpos ?
    def po_files(members):
        for member in members:
            if os.path.splitext(member.name)[1] == ".po":  # is it ok in python 2 and 3 ?
                yield member

    # filename, info = urllib.urlretrieve(url)
    filename, info = urllib.request.urlretrieve(url)  # url -> urlpos ?
    tarfiled = tarfile.open(filename, 'r:gz')
    folder = [member for member in tarfiled if member.isdir()][0].name
    tarfiled.extractall(members=po_files(tarfiled))
    tarfiled.close()
    os.remove(filename)

    for poFile in glob.glob('*.po'):
        newPoFile = os.path.join(folder, 'i18n.in-%s' % poFile)
        shutil.copy(newPoFile, poFile)
        print('Updating', poFile)
    shutil.rmtree(folder)


def downloadtranslation(url):  # todo: url -> urlpo ?
    # http://launchpadlibrarian.net/70943850/i18n.in_i18n.in-nl.po
    filename, info = urllib.request.urlretrieve(url)
    shutil.move(filename, url.split('-')[1])


def createpodicts():
    for poFile in sorted(glob.glob('*.po')):
        print('Creating python dictionary from', poFile)
        pyfile = po2dict.make(poFile)
        shutil.move(pyfile, '../taskcoachlib/i18n/%s' % pyfile)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        url = sys.argv[1]
        if url.endswith('.po'):
            downloadtranslation(url)
        else:
            downloadtranslations(url)
    else:
        createpodicts()
