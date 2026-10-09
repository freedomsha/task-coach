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

# from builtins import object
import wx

from .. import tctest
from taskcoachlib import meta, application, config


class DummyOptions(object):
    pofile = None
    language = None


class DummyLocale(object):
    def __init__(self, language="C"):
        self.language = language
        self.LC_MESSAGES = 1

    # def getdefaultlocale(self):
    def getdefaultlocale(self, category=None):
        return self.language, None


class AppTests(tctest.TestCase):
    def setUp(self):
        # On s'assure qu'aucune instance résiduelle ne pollue le test
        application.Application.delete_instance()

        # Pour les tests unitaires qui n'instancient pas Application,
        # on crée une wx.App minimale pour éviter le crash "traits".
        # self.wx_app = wx.GetApp() or wx.App()
        self.wx_app = wx.GetApp()
        if not self.wx_app:
            self.wx_app = wx.App(
                False
            )  # important: False = pas de redirection
            self.wx_app.SetAppName("TestApp")

        super(AppTests, self).setUp()
        self.settings = config.Settings(load=False)
        self.options = DummyOptions()

    def testAppProperties(self):
        import locale

        # if locale.getdefaultlocale()[0] != "en_US":
        # if locale.getlocale()[0] != "en_US":
        try:
            loc = locale.getdefaultlocale(locale.LC_MESSAGES)[0]
        except (IndexError, TypeError, AttributeError):
            loc = None
        if loc != "en_US" and loc != "en" and loc is not None:
            # Somehow wx displays an error dialog box if en_US is not installed, when
            # quitApplication() calls ProcessIdle and I don't know how to get rid of it.
            # I don't know how to find out if en_US is installed either, so skip if
            # it's not the default.
            self.skipTest("Locale is not en_US")
        else:
            # Normally I prefer one assert per test, but creating the app is
            # expensive, so we do all the queries in one test method.

            # On supprime l'instance de l'application précédente (dummy) pour
            # permettre au singleton Application de se réinitialiser proprement.
            application.Application.delete_instance()

            # app = application.Application(
            #     loadSettings=False, loadTaskFile=False
            # )
            app = application.Application()
            app.init(loadSettings=False, loadTaskFile=False)
            wxApp = wx.GetApp()
            self.assertEqual(meta.name, wxApp.GetAppName())
            self.assertEqual(meta.author, wxApp.GetVendorName())
            if hasattr(app, "mainwindow") and app.mainwindow:
                app.mainwindow._idleController.stop()
                # app.quitApplication()
                app.mainwindow.Destroy()
            # application.Application.delete_instance()
            app.delete_instance()

    def assertLanguage(self, expectedLanguage, locale=None):
        args = [self.options, self.settings]
        if locale:
            args.append(locale)
        self.assertEqual(
            expectedLanguage, application.Application.determine_language(*args)
        )  # pylint: disable=W0142

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
