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

# import wxversion
# wxversion.ensureMinimal("2.8")
import sys
try:
    import wxversion  # in python 3 try with wx.__version__ ?
    wxversion.ensureMinimal("2.8")
except ImportError:
    pass
from io import open as file
import os
from wx.tools import img2py  # introuvable !


def extracticon(iconzipfile, pngfilename, pngzipped):
    pngfile = file(pngfilename, 'wb')  # ATTENTION: fichier de type bytes
    pngfile.write(iconzipfile.read(pngzipped))
    pngfile.close()


def addicon(pngname, pngfilename, iconpyfile, first):
    options = ['-F', '-i', '-c', '-a', '-n%s' % pngname, pngfilename, iconpyfile]
    if first:
        options.remove('-a')
    img2py.main(options)


def extractandaddicon(iconzipfile, iconpyfile, pngname, pngzipped, first):
    pngfilename = '%s.png' % pngname
    extracticon(iconzipfile, pngfilename, pngzipped)
    addicon(pngname, pngfilename, iconpyfile, first)
    os.remove(pngfilename)


def extractandaddicons(iconzipfile, iconpyfile):
    import iconmap
    first = True
    for pngName, pngZipped in list(iconmap.icons.items()):
        extractandaddicon(iconzipfile, iconpyfile, pngName, pngZipped, first)
        first = False


def makeiconpyfile(iconpyfile):
    if os.path.isfile(iconpyfile):
        os.remove(iconpyfile)

    import zipfile
    iconzipfile = zipfile.ZipFile('nuvola.zip', 'r')
    extractandaddicons(iconzipfile, iconpyfile)
    iconzipfile.close()


def makesplashscreen(iconpyfile):
    options = ['-F', '-c', '-a', '-nsplash', 'splash.png', iconpyfile]
    img2py.main(options)


if __name__ == '__main__':
    iconFileName = '../taskcoachlib/gui/icons.py'
    makeiconpyfile(iconFileName)
    makesplashscreen(iconFileName)
