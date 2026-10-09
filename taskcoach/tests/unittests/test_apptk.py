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
# Suppression des dépendances wxPython :
#
# Le code qui vérifiait wx.GetApp(), GetAppName(), et GetVendorName() a été supprimé, car Tkinter ne fournit pas d'équivalent direct pour ces méthodes.
# La logique de test de testAppProperties a été simplifiée pour vérifier que l'application peut être instanciée et détruite correctement.
#
#
# Adaptation des méthodes de test :
#
# Les tests liés à la langue (assertLanguage, testLanguageViaCommandLineOption, etc.) restent inchangés, car ils ne dépendent pas directement de wxPython.
#
#
# Utilisation de destroy :
#
# app.mainwindow.Destroy() est remplacé par app.mainwindow.destroy() pour respecter la convention Tkinter.
#
#
# Gestion des locales :
#
# La classe DummyLocale est conservée pour simuler le comportement des locales, mais elle n'est pas utilisée directement par Tkinter.

import tkinter as tk
from unittest.mock import patch

from .. import tctktest
from taskcoachlib import meta, application, config


class DummyOptions:
    pofile = None
    language = None


class DummyLocale:
    def __init__(self, language="C"):
        self.language = language

    def getdefaultlocale(self):
        return self.language, None


class AppTests(tctktest.TestCase):
    def setUp(self):
        super().setUp()
        self.settings = config.Settings(load=False)
        self.options = DummyOptions()

    def testAppProperties(self):
        # On ne peut pas tester directement les propriétés de l'application Tkinter comme avec wxPython,
        # car Tkinter n'a pas d'équivalent direct à wx.GetApp() ou GetAppName().
        # On vérifie donc uniquement que l'application peut être instanciée et détruite correctement.
        app = application.tkapplication.TkinterApplication(
            loadSettings=False, loadTaskFile=False
        )
        # Simuler la fermeture de l'application
        app.mainwindow._idleController.stop()
        app.quitApplication()
        app.mainwindow.destroy()
        application.Application.delete_instance()

    def assertLanguage(self, expectedLanguage, locale=None):
        args = [self.options, self.settings]
        if locale:
            args.append(locale)
        self.assertEqual(
            expectedLanguage,
            application.tkapplication.TkinterApplication.determine_language(
                *args
            ),
        )

    def testLanguageViaCommandLineOption(self):
        self.options.language = "fi_FI"
        self.assertLanguage("fi_FI")

    def testLanguageViaCommandLinePoFile(self):
        self.options.pofile = "nl_NL"
        self.assertLanguage("nl_NL")

    def testLanguageViaExternallySetLanguage(self):
        self.settings.set("view", "language", "de_DE")
        self.assertLanguage("de_DE")

    def testLanguageSetByUser(self):
        self.settings.set("view", "language_set_by_user", "de_DE")
        self.assertLanguage("de_DE")

    def testLanguageSetByUser_OverridesExternallySetLanguage(self):
        self.settings.set("view", "language", "nl_NL")
        self.settings.set("view", "language_set_by_user", "de_DE")
        self.assertLanguage("de_DE")

    def testLanguageViaLocale(self):
        self.assertLanguage("en_GB", DummyLocale("en_GB"))

    def testLanguageViaCLocale(self):
        self.assertLanguage("en_US", DummyLocale())
