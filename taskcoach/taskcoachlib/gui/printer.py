"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

# from builtins import str
import logging
from taskcoachlib import persistence, patterns, operating_system
from taskcoachlib.i18n import _
import wx
import wx.html

# from wx import *

log = logging.getLogger(__name__)

# Prepare for printing. On Jolicloud, printing crashes unless we do this:

# BUT on Fedora, if we do this, TaskCoach doesn't even start. My opinion is that
# Fedora is more widely used than Jolicloud.

# # if operating_system.isGTK():
# #     try:
# #         import gtk  # pylint: disable=F0401
# #         gtk.remove_log_handlers()
# #     except ImportError:
# #         pass


# class PrinterSettings(metaclass=patterns.Singleton):
class PrinterSettings(object, metaclass=patterns.Singleton):
    """Classe pour gérer les paramètres d'impression."""

    edges = ("top", "left", "bottom", "right")

    def __init__(self, settings):
        self.settings = settings
        self.printData = wx.PrintData()
        self.pageSetupData = wx.PageSetupDialogData(self.printData)
        self.__initialize_from_settings()

    def updatePageSetupData(self, data):
        self.pageSetupData = wx.PageSetupDialogData(data)
        self.__update_print_data(data.GetPrintData())
        self.__save_to_settings()

    def __update_print_data(self, printData):
        self.printData = wx.PrintData(printData)
        self.pageSetupData.SetPrintData(self.printData)

    def __getattr__(self, attr):
        try:
            return getattr(self.pageSetupData, attr)
        except AttributeError:
            return getattr(self.printData, attr)

    def __initialize_from_settings(self):
        """Load the printer settings from the user settings."""
        margin = dict()
        for edge in self.edges:
            margin[edge] = self.__get_setting("margin_" + edge)
        top_left = wx.Point(margin["left"], margin["top"])
        bottom_right = wx.Point(margin["right"], margin["bottom"])
        self.SetMarginTopLeft(top_left)
        self.SetMarginBottomRight(bottom_right)
        self.SetPaperId(self.__get_setting("paper_id"))
        self.SetOrientation(self.__get_setting("orientation"))

    def __save_to_settings(self):
        """Save the printer settings to the user settings."""
        margin = dict()
        margin["left"], margin["top"] = self.GetMarginTopLeft()
        margin["right"], margin["bottom"] = self.GetMarginBottomRight()
        for edge in self.edges:
            self.__set_setting("margin_" + edge, margin[edge])
        self.__set_setting("paper_id", self.GetPaperId())
        self.__set_setting("orientation", self.GetOrientation())

    def __get_setting(self, option):
        return self.settings.getint("printer", option)

    def __set_setting(self, option, value):
        self.settings.set("printer", option, str(value))


class HTMLPrintout(wx.html.HtmlPrintout):
    """Classe pour imprimer du contenu HTML."""

    def __init__(self, html_text, settings):
        super().__init__()
        # Définit le contenu HTML à imprimer
        self.SetHtmlText(html_text)
        # Définit le pied de page avec numéro de page
        self.SetFooter(_("Page") + " @PAGENUM@/@PAGESCNT@", wx.html.PAGE_ALL)
        # Ancien code :
        # Définit les polices serif, sans serif et les tailles
        self.SetFonts(
            "Arial", "Courier", [7, 8, 10, 12, 14, 16, 18, 22, 24, 30]
        )
        # # Nouveau code :
        # Quand tu voudras remettre la personnalisation des polices :
        #     Assure-toi que settings transmis à HTMLPrintout est bien l’objet de configuration de Task Coach.
        #     Tu peux ajouter une vérification simple comme :
        # assert hasattr(settings, "get"), "settings doit être l'objet Settings, pas un wx.PrintData"
        #
        # Et garde ce modèle :
        #   serif = settings.get("editor", "seriffont", default="Times New Roman")
        #   sans = settings.get("editor", "sansseriffont", default="Arial")
        #   sizes = [7, 8, 10, 12, 14, 18, 24]  # ou lu depuis settings
        #   self.SetFonts(serif, sans, sizes)
        #
        # # Lecture des polices depuis les préférences utilisateur
        # serif_font = settings.get("editor", "seriffont", default="Times New Roman")
        # # settings est en réalité une instance de wx.PrintData ou wx.PageSetupDialogData, pas l’objet Settings de Task Coach.
        # sans_serif_font = settings.get("editor", "sansseriffont", default="Arial")
        #
        # # Lecture des tailles de police, séparées par virgule ou utilise une valeur par défaut
        # try:
        #     font_sizes_str = settings.get("editor", "fontsizes", default="7,8,10,12,14,18,24")
        #     font_sizes = [int(size) for size in font_sizes_str.split(",")]
        #     if len(font_sizes) != 7:
        #         raise ValueError
        # except Exception:
        #     font_sizes = [7, 8, 10, 12, 14, 18, 24]  # Valeurs de secours
        #
        # # Applique les polices et tailles
        # self.SetFonts(serif_font, sans_serif_font, font_sizes)

        # Configure les marges à partir des paramètres
        printer_settings = PrinterSettings(settings)
        left, top = printer_settings.pageSetupData.GetMarginTopLeft()
        right, bottom = printer_settings.pageSetupData.GetMarginBottomRight()
        self.SetMargins(top, bottom, left, right)


class DCPrintout(wx.Printout):
    """Classe pour imprimer le contenu d'un widget."""

    def __init__(self, widget):
        self.widget = widget
        super().__init__()

    def OnPrintPage(self, page):  # pylint: disable=W0613
        self.widget.Draw(self.GetDC())

    # @staticmethod
    def GetPageInfo(self):  # pylint: disable=W0221
        # return (1, 1, 1, 1)
        return 1, 1, 1, 1


def Printout(viewer, settings, printSelectionOnly=False, twoPrintouts=False):
    """Fonction principale pour gérer l'impression."""
    widget = viewer.getWidget()
    if hasattr(widget, "GetPrintout"):
        _printout = widget.GetPrintout
    elif hasattr(widget, "Draw"):

        def _printout(settings):
            return DCPrintout(widget)

    else:
        html_text = persistence.viewer2html(
            viewer, settings, selectionOnly=printSelectionOnly
        )[0]

        def _printout(settings):
            return HTMLPrintout(html_text, settings)

    result = _printout(PrinterSettings(settings))
    if twoPrintouts:
        result = (result, _printout(PrinterSettings(settings)))
    return result
