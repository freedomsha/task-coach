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

# use https://lokalise.com/blog/beginners-guide-to-python-i18n/

import wx
import os
import sys
# from imp import load_source as Load_Source # obsolète à remplacer par importlib.
# Pour imp.load_source remplacer par importlib.machinery.SourceFileLoader
from importlib.machinery import SourceFileLoader as Load_Source
import tempfile
import locale
import gettext
from gettext import *
from taskcoachlib import patterns, operating_system
from . import po2dict  # XXXFIXME get rid of this later
import builtins


class Translator(metaclass=patterns.Singleton):
    def __init__(self, language):
        # def __init__(self):  # Unresolved reference 'language'
        if language.endswith('.po'):
            load = self._loadPoFile
        else:
            load = self._loadModule
        module, language = load(language)  # unexpected argument language
        self._installModule(module)
        self._setLocale(language)
        # new
        appname = 'taskcoach'
        localedir = './i18n.in'
        # Set up Gettext
        en_i18n = gettext.translation(appname, localedir, fallback=True, languages=['en'])
        fr_i18n = gettext.translation(appname, localedir, fallback=True, languages=['fr'])
        nl_i18n = gettext.translation(appname, localedir, fallback=True, languages=['nl'])

        # Create the "magic" function
        en_i18n.install()
        fr_i18n.install()
        nl_i18n.install()

    def _loadPoFile(self, poFilename):
        """ Load the translation from a .po file by creating a python
            module with po2dict and them importing that module. """
        # Chargez la traduction à partir d'un fichier .po en créant
        # un module python avec po2dict et en important ce module.
        language = self._languageFromPoFilename(poFilename)
        pyFilename = self._tmpPyFilename()
        po2dict.make(poFilename, pyFilename)
        module = Load_Source(language, pyFilename)  # imp déprécié. Remplacer par importlib.machinery.SourceFileLoader
        os.remove(pyFilename)
        return module, language

    # @staticmethod
    def _tmpPyFilename(self) -> str:
        """ Return a filename of a (closed) temporary .py file. """
        # Renvoie le nom d'un fichier .py temporaire (fermé).
        tmpFile = tempfile.NamedTemporaryFile(suffix='.py')
        pyFilename = tmpFile.name
        tmpFile.close()
        return pyFilename

    def _loadModule(self, language: str) -> tuple:
        """ Load the translation from a python module that has been
            created from a .po file with po2dict before. """
        # Chargez la traduction à partir d'un module python qui a été
        # créé auparavant à partir d'un fichier .po avec po2dict.
        module = None  # d'où ça sort ? Local variable 'module' might be referenced before assignment
        for moduleName in self._localeStrings(language):
            try:
                module = __import__(moduleName, globals())
                break
            except ImportError:
                module = None
        return module, language

    def _installModule(self, module):
        """ Make the module's translation dictionary and encoding available. """
        # Rendre disponible le dictionnaire de traduction et l'encodage du module.
        # pylint: disable=W0201
        if module:
            self.__language = module.dict
            self.__encoding = module.encoding

    def _setLocale(self, language):
        """ Try to set the locale, trying possibly multiple localeStrings. """
        # Essayez de définir les paramètres régionaux, en essayant éventuellement plusieurs localeStrings.
        if not operating_system.isGTK():
            locale.setlocale(locale.LC_ALL, '')
        # Set the wxPython locale:
        for localeString in self._localeStrings(language):
            languageInfo = wx.Locale.FindLanguageInfo(localeString)
            if languageInfo:
                self.__locale = wx.Locale(languageInfo.Language)  # pylint: disable=W0201
                # Add the wxWidgets message catalog. This is really only for
                # py2exe'ified versions, but it doesn't seem to hurt on other
                # platforms...
                # localedir = os.path.join(wx.StandardPaths_Get().GetResourcesDir(), 'locale')
                localedir = os.path.join(wx.StandardPaths.Get().GetResourcesDir(), 'locale')
                self.__locale.AddCatalogLookupPathPrefix(localedir)
                self.__locale.AddCatalog('wxstd')
                break
        if operating_system.isGTK():
            try:
                locale.setlocale(locale.LC_ALL, '')
            except locale.Error:
                # Mmmh. wx will display a message box later, so don't do anything.
                pass
        self._fixBrokenLocales()

    # @staticmethod
    def _fixBrokenLocales(self):
        current_language = locale.getlocale(locale.LC_TIME)[0]
        if current_language and '_NO' in current_language:
            # nb_BO and ny_NO cause crashes in the wx.DatePicker. Set the
            # time part of the locale to some other locale. Since we don't
            # know which ones are available we try a few. First we try the
            # default locale of the user (''). It's probably *_NO, but it
            # might be some other language so we try just in case. Then we try
            # English (GB) so the user at least gets a European Date and time
            # format if that works. If all else fails we use the default
            # 'C' locale.
            for lang in ['', 'en_GB.utf8', 'C']:
                try:
                    locale.setlocale(locale.LC_TIME, lang)
                except locale.Error:
                    continue
                current_language = locale.getlocale(locale.LC_TIME)[0]
                if current_language and '_NO' in current_language:
                    continue
                else:
                    break

    # def _localeStrings(language):
    # TypeError: Translator._localeStrings() takes 1 positional argument but 2 were given
    # Method '_localeStrings' may be 'static'
    def _localeStrings(self, language: str) -> list:
        """ Extract language and language_country from language if possible. """
        # Extrayez la langue et la langue_pays de language si possible.
        localeStrings = []
        if language:
            localeStrings.append(language)
            if '_' in language:
                localeStrings.append(language.split('_')[0])
        return localeStrings

    # Method '_languageFromPoFilename' may be 'static'
    def _languageFromPoFilename(self, poFilename: str) -> str:
        return os.path.splitext(os.path.basename(poFilename))[0]

    # def translate(self, string):
    def translate(self, string: str) -> str:
        """ Look up string in the current language dictionary. Return the
            passed string if no language dictionary is available or if the
            dictionary doesn't contain the string. """
        # Recherchez une chaîne dans le dictionnaire de langue actuel.
        # Renvoie la chaîne transmise si aucun dictionnaire de langue n'est disponible
        # ou si le dictionnaire ne contient pas la chaîne.
        try:
            return self.__language[string].decode(self.__encoding)
        except (AttributeError, KeyError):
            return string


def currentLanguageIsRightToLeft():
    return wx.GetApp().GetLayoutDirection() == wx.Layout_RightToLeft


def translate(string):
    return Translator().translate(string)
    # Parameter 'language' unfilled
    # TypeError: Translator.translate() missing 1 required positional argument: 'string'
    # return Translator(language=?).translate(string)
    # return Translator(language=language).translate(string)


_ = translate  # This prevents a warning from pygettext.py

# Inject into builtins for 3rdparty packages
# #import __builtin__
# #__builtin__.__dict__['_'] = _

# builtins.__dict__['_'] = _
