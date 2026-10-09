# -*- coding: utf-8 -*-

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

Explication des classes :

    HideCurrentColumn : Cette classe permet de masquer la colonne sous la souris, en utilisant la position actuelle de la souris pour déterminer quelle colonne masquer.
    ViewColumn : Cette classe gère l'affichage ou le masquage d'une colonne spécifique en fonction du nom de la colonne.
    ViewColumns : Cette classe permet de gérer plusieurs colonnes simultanément, en affichant ou en masquant un groupe de colonnes dans la visionneuse.
"""

# from builtins import str
# from builtins import object
# from io import open as file

import logging
import wx
import re
import operator
import wx.lib.agw.aui as aui

from functools import reduce

# from .taskcoachlib.thirdparty.agw import hypertreelist
from wx.lib.agw import hypertreelist

# try:
#    from ...thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
from pubsub import pub

from taskcoachlib import (
    patterns,
    meta,
    command,
    help,
    widgets,
    persistence,
    # thirdparty,
    render,
    operating_system,
)  # pylint: disable=W0622
from taskcoachlib.domain import (
    base,
    task,
    note,
    category,
    attachment,
    effort,
    date,
)
from taskcoachlib.gui import dialog, printer

# import taskcoachlib.gui.dialog
# import taskcoachlib.gui.printer
from taskcoachlib.gui.wizard import CSVImportWizard
from taskcoachlib.i18n import _
from taskcoachlib.mailer import sendMail

from taskcoachlib.thirdparty.wxScheduler import (
    wxSCHEDULER_NEXT,
    wxSCHEDULER_PREV,
    wxSCHEDULER_TODAY,
)
from taskcoachlib.tools import anonymize, openfile
from taskcoachlib.workarounds import ExceptionAsUnicode

from taskcoachlib.gui.uicommand import base_uicommand
from taskcoachlib.gui.uicommand import mixin_uicommand
from taskcoachlib.gui.uicommand import settings_uicommand

log = logging.getLogger(__name__)


class IOCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande d'entrée/sortie (IOCommand) de base qui gère les opérations d'entrée/sortie
    (comme ouvrir ou sauvegarder un fichier) via un contrôleur I/O.

    Attributs :
        iocontroller (IOController) : Le contrôleur I/O responsable des opérations sur les fichiers.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande IOCommand avec un contrôleur I/O fourni via les arguments.

        Args :
            iocontroller (IOController) : Contrôleur I/O chargé de gérer les fichiers.
        """
        # Extract the iocontroller from kwargs and initialize the base class
        # log.debug(f"tclib.gui.uicommand.uicommand.IOCommand Initializing IOCommand with {args} and {kwargs} et y retire iocontroller.")  # Débogage
        self.iocontroller = kwargs.pop("iocontroller", None)
        super().__init__(*args, **kwargs)


class TaskListCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande spécifique à la gestion d'une liste de tâches. Utilisée pour manipuler et interagir avec une liste de tâches.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de tâches fournie.

        Args :
            taskList (TaskList) : La liste des tâches à manipuler.
        """
        self.taskList = kwargs.pop("taskList", None)
        super().__init__(*args, **kwargs)


class EffortListCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande spécifique à la gestion d'une liste d'efforts (suivi du temps). Utilisée pour manipuler et interagir avec une liste d'efforts.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste d'efforts fournie.

        Args :
            effortList (EffortList) : La liste des efforts à manipuler.
        """
        self.effortList = kwargs.pop("effortList", None)
        super().__init__(*args, **kwargs)


class CategoriesCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour gérer les catégories. Utilisée pour interagir avec une liste de catégories.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de catégories fournie.

        Args :
            categories (CategoryList) : La liste des catégories.
        """
        self.categories = kwargs.pop("categories", None)
        super().__init__(*args, **kwargs)


class NotesCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour gérer les notes. Utilisée pour interagir avec une liste de notes.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de notes fournie.

        Args :
            notes (NoteList) : La liste des notes.
        """
        self.notes = kwargs.pop("notes", None)
        super().__init__(*args, **kwargs)


class AttachmentsCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour gérer les fichiers joints. Utilisée pour interagir avec une liste de fichiers joints.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une liste de fichiers joints fournis.

        Args :
            attachments : La liste des fichiers joints.
        """
        self.attachments = kwargs.pop("attachments", None)
        super().__init__(*args, **kwargs)


class ViewerCommand(base_uicommand.UICommand):  # pylint: disable=W0223
    """
    Commande pour interagir avec une visionneuse (viewer). Permet d'exécuter des actions liées à l'affichage d'une présentation de données.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec une visionneuse fournie.

        Args :
            viewer (Viewer) : La visionneuse pour laquelle la commande est exécutée.
        """
        self.viewer = kwargs.pop("viewer", None)
        super().__init__(*args, **kwargs)

    # def __eq__(self, other) -> bool:
    def __eq__(self, other):
        """
        Compare cette commande avec une autre pour vérifier si elles sont égales. Deux commandes sont égales si elles partagent la même section de paramètres de la visionneuse.

        Args :
            other (ViewerCommand) : La commande avec laquelle comparer.

        Returns :
            (bool) : True si les commandes sont égales, False sinon.
        """
        return (
            super().__eq__(other)
            and self.viewer.settingsSection() == other.viewer.settingsSection()
        )


# Commands:


class FileOpen(IOCommand):
    """
    Commande pour ouvrir un fichier. Utilise un contrôleur I/O pour ouvrir un fichier de tâche.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'ouverture de fichier.

        Avec des paramètres spécifiques pour l'interface utilisateur,
        comme le texte du menu et l'icône associée.
        """
        super().__init__(
            menuText=_("&Open...\tCtrl+O"),
            helpText=help.fileOpen,
            bitmap="fileopen",
            id=wx.ID_OPEN,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileOpen command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande d'ouverture de fichier. Ouvre un fichier en utilisant le contrôleur I/O.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        log.info(
            "FileOpen.doCommand() appelé. Ouvre self.iocontroller.open()"
        )  # Débogage
        # self.iocontroller.open()
        try:
            self.iocontroller.open()
        except Exception as e:
            log.exception(f"FileOpen.doCommand : Error: {e}", exc_info=True)
            # log.debug(f"FileOpen.doCommand : Error opening file: {e}")  # Débogage


class RecentFileOpen(IOCommand):
    """
    Commande pour ouvrir un fichier récemment utilisé. Utilise un contrôleur I/O pour ouvrir le fichier spécifié.

    Attributs :
        __filename (str) : Le chemin ou nom du fichier à ouvrir.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec le nom du fichier à ouvrir.

        Args :
            filename (str) : Le nom du fichier récent.
            index (int) : L'indice dans la liste des fichiers récents.
        """
        self.__filename = kwargs.pop("filename")
        log.debug(f"RecentFileOpen: self.__filename={self.__filename}")
        index = kwargs.pop("index")
        super().__init__(
            # menuText="%d %s" % (index, self.__filename),
            menuText=f"{index:d} {self.__filename}",
            # helpText=_("Open %s") % self.__filename,
            helpText=_(f"Open {self.__filename}"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """Ouvre le fichier récent sélectionné."""
        log.debug(
            f"RecentFileOpen.doCommand : Appelé et appelle self.iocontroller.open({self.__filename})"
        )
        self.iocontroller.open(self.__filename)


class FileMerge(IOCommand):
    """
    Commande pour fusionner des tâches d'un autre fichier avec le fichier actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de fusion.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Merge..."),
            helpText=_("Merge tasks from another file with the current file"),
            # bitmap="merge",
            bitmap="mergedisk",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileMerge command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande pour fusionner les tâches."""
        self.iocontroller.merge()


class FileClose(IOCommand):
    """
    Commande pour fermer le fichier actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de fermeture de fichier.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Close\tCtrl+W"),
            helpText=help.fileClose,
            bitmap="Close",
            id=wx.ID_CLOSE,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileClose command initialized")  # Débogage

    def doCommand(self, event):
        """Ferme le fichier et les éditeurs associés."""
        self.mainWindow().closeEditors()
        # self.iocontroller.Close()  # IOController ne possède pas de méthode Close()
        self.iocontroller.close()


class FileSave(IOCommand):
    """
    Commande pour sauvegarder le fichier actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Save\tCtrl+S"),
            helpText=help.fileSave,
            bitmap="save",
            id=wx.ID_SAVE,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileSave command initialized")  # Débogage

    def doCommand(self, event):
        """Sauvegarde le fichier actuel."""
        self.iocontroller.save()

    def enabled(self, event):
        """Vérifie si la sauvegarde est nécessaire."""
        return self.iocontroller.needSave()


class FileMergeDiskChanges(IOCommand):
    """
    Commande pour fusionner les changements sur disque avec le fichier actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour fusionner les changements.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Merge &disk changes\tShift-Ctrl-M"),
            helpText=help.fileMergeDiskChanges,
            bitmap="mergedisk",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileMergeDiskChanges command initialized")  # Débogage

    def doCommand(self, event):
        """Fusionne les changements détectés sur disque."""
        self.iocontroller.mergeDiskChanges()

    def enabled(self, event):
        """Active la commande si des changements ont été détectés sur disque."""
        return self.iocontroller.changedOnDisk()


class FileSaveAs(IOCommand):
    """
    Commande pour sauvegarder le fichier actuel sous un autre nom.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde sous un autre nom.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("S&ave as...\tShift+Ctrl+S"),
            helpText=help.fileSaveAs,
            bitmap="saveas",
            id=wx.ID_SAVEAS,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileSaveAs command initialized")  # Débogage

    def doCommand(self, event):
        """Sauvegarde le fichier sous un autre nom."""
        self.iocontroller.saveas()


class FileSaveSelection(
    mixin_uicommand.NeedsSelectedTasksMixin, IOCommand, ViewerCommand
):
    """
    Commande pour sauvegarder les tâches sélectionnées dans un nouveau fichier de tâches.

    Attributs :
        viewer (Viewer) : La visionneuse de tâches utilisée pour obtenir les tâches sélectionnées.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde des tâches sélectionnées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Sa&ve selected tasks to new taskfile..."),
            helpText=_("Save the selected tasks to a separate taskfile"),
            bitmap="saveselection",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileSaveSelection command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande pour sauvegarder les tâches sélectionnées."""
        self.iocontroller.saveselection(self.viewer.curselection())


class FileSaveSelectedTaskAsTemplate(
    mixin_uicommand.NeedsOneSelectedTaskMixin, IOCommand, ViewerCommand
):
    """
    Commande pour sauvegarder la tâche sélectionnée en tant que modèle de tâche.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour obtenir la tâche sélectionnée.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de sauvegarde de la tâche en tant que modèle.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Save selected task as &template"),
            helpText=_("Save the selected task as a task template"),
            bitmap="saveselection",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileSaveSelectedTaskAsTemplate command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande pour sauvegarder la tâche sélectionnée en tant que modèle."""
        self.iocontroller.saveastemplate(self.viewer.curselection()[0])


class FileImportTemplate(IOCommand):
    """
    Commande pour importer un modèle depuis un fichier de modèles.

    Attributs :
        iocontroller (IOController) : Le contrôleur utilisé pour gérer les fichiers.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de modèle.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Import template..."),
            helpText=_("Import a new template from a template file"),
            bitmap="fileopen",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileImportTemplate command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande pour importer un modèle depuis un fichier."""
        self.iocontroller.importTemplate()


class FileEditTemplates(
    settings_uicommand.SettingsCommand, base_uicommand.UICommand
):
    """
    Commande pour éditer les modèles existants.

    Attributs :
        settings (Settings) : Les paramètres de l'application.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'édition des modèles.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Edit templates..."),
            helpText=_("Edit existing templates"),
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileEditTemplates command initialized")  # Débogage

    def doCommand(self, event):
        """Affiche la boîte de dialogue pour éditer les modèles existants."""
        templateDialog = dialog.templates.TemplatesDialog(
            self.settings, self.mainWindow(), title=_("Edit templates")
        )
        templateDialog.Show()


class FilePurgeDeletedItems(mixin_uicommand.NeedsDeletedItemsMixin, IOCommand):
    """
    Commande pour purger définitivement les éléments supprimés (tâches et notes).

    Utilisée lorsque l'on souhaite supprimer de manière irréversible des éléments marqués comme supprimés.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour purger les éléments supprimés.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Purge deleted items"),
            helpText=_(
                "Actually delete deleted tasks and notes "
                "(see the SyncML chapter in Help)"
            ),
            bitmap="delete",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FilePurgeDeletedItems command initialized")  # Débogage

    def doCommand(self, event):
        """
        Purge les éléments supprimés après confirmation de l'utilisateur.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        if (
            wx.MessageBox(
                _("""Purging deleted items is undoable.
                    If you're planning on enabling
                    the SyncML feature again with the
                    same server you used previously,
                    these items will probably come back.
                    
                    Do you still want to purge?"""),
                _("Warning"),
                wx.YES_NO,
            )
            == wx.YES
        ):
            self.iocontroller.purgeDeletedItems()


class PrintPageSetup(
    settings_uicommand.SettingsCommand, base_uicommand.UICommand
):
    """
    Commande pour changer les paramètres de la page. Les paramètres de la page sont sauvegardés dans les réglages de l'application.

    Attributs :
        settings (Settings) : Les paramètres de l'application pour sauvegarder les configurations de la page.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Page setup...\tShift+Ctrl+P"),
            helpText=help.printPageSetup,
            bitmap="pagesetup",
            id=wx.ID_PRINT_SETUP,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.PrintPageSetup command initialized")  # Débogage

    def doCommand(self, event):
        """
        Ouvre une boîte de dialogue pour modifier les paramètres de la page et les applique aux réglages de l'application.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        printerSettings = printer.PrinterSettings(self.settings)
        pageSetupDialog = wx.PageSetupDialog(
            self.mainWindow(), printerSettings.pageSetupData
        )
        result = pageSetupDialog.ShowModal()
        if result == wx.ID_OK:
            pageSetupData = pageSetupDialog.GetPageSetupData()
            printerSettings.updatePageSetupData(pageSetupData)
        pageSetupDialog.Destroy()


class PrintPreview(ViewerCommand, settings_uicommand.SettingsCommand):
    """
    Commande pour afficher un aperçu de l'impression du contenu actuel de la visionneuse.

    Attributs :
        viewer (Viewer) : La visionneuse de l'application dont le contenu sera imprimé.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Print preview..."),
            helpText=_("Show a preview of what the print will look like"),
            bitmap="printpreview",
            id=wx.ID_PREVIEW,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.PrintPreview command initialized")  # Débogage

    def doCommand(self, event):
        """
        Affiche la fenêtre d'aperçu de l'impression avec deux versions de sortie pour l'impression.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        printout, printout2 = printer.Printout(
            self.viewer, self.settings, twoPrintouts=True
        )
        printerSettings = printer.PrinterSettings(self.settings)
        preview = wx.PrintPreview(
            printout, printout2, printerSettings.printData
        )
        if not preview.IsOk():
            wx.MessageBox(
                _("There was a problem creating the print preview."),
                _("Print Preview Error"),
                wx.OK | wx.ICON_ERROR,
            )
            return
        previewFrame = wx.PreviewFrame(
            preview, self.mainWindow(), _("Print preview"), size=(750, 700)
        )
        previewFrame.Initialize()
        previewFrame.Show()


class Print(ViewerCommand, settings_uicommand.SettingsCommand):
    """
    Commande pour imprimer le contenu actuel de la visionneuse.

    Attributs :
        viewer (Viewer) : La visionneuse dont le contenu sera imprimé.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de texte et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Print...\tCtrl+P"),
            helpText=help.print_,
            bitmap="print",
            id=wx.ID_PRINT,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.Print command initialized")  # Débogage

    def doCommand(self, event):
        """
        Ouvre une boîte de dialogue d'impression, configure les options, et imprime le contenu sélectionné ou l'intégralité du document.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        printerSettings = printer.PrinterSettings(self.settings)
        printDialogData = wx.PrintDialogData(printerSettings.printData)
        printDialogData.EnableSelection(True)
        wxPrinter = wx.Printer(printDialogData)
        if not wxPrinter.PrintDialog(self.mainWindow()):
            return
        printout = printer.Printout(
            self.viewer,
            self.settings,
            printSelectionOnly=wxPrinter.PrintDialogData.Selection,
        )
        # Si l'utilisateur coche le bouton radio de sélection, la propriété ToPage
        # est définie sur 1. Cela me semble être un bug. La solution simple consiste à
        # réinitialiser la propriété ToPage à la valeur MaxPage si nécessaire :
        # Si l'utilisateur sélectionne l'option de sélection, ajuste les pages à imprimer:
        if wxPrinter.PrintDialogData.Selection:
            wxPrinter.PrintDialogData.ToPage = (
                wxPrinter.PrintDialogData.MaxPage
            )
        wxPrinter.Print(self.mainWindow(), printout, prompt=False)


class FileExportCommand(IOCommand, settings_uicommand.SettingsCommand):
    """
    Classe de base pour les actions d'exportation.

    Permet d'exporter des éléments depuis une visionneuse vers différents formats de fichier.
    """

    def doCommand(self, event):
        """
        Exécute la commande d'exportation. Ouvre la boîte de dialogue pour définir les options d'exportation et appelle la fonction d'exportation correspondante.
        """
        exportDialog = self.getExportDialogClass()(
            self.mainWindow(), settings=self.settings
        )  # pylint: disable=E1101
        if wx.ID_OK == exportDialog.ShowModal():
            exportOptions = exportDialog.options()
            selectedViewer = exportOptions.pop("selectedViewer")
            # pylint: disable=W0142
            self.exportFunction()(selectedViewer, **exportOptions)
        exportDialog.Destroy()

    @staticmethod
    def getExportDialogClass():
        """Retourne la classe à utiliser pour la boîte de dialogue d'exportation."""
        raise NotImplementedError

    def exportFunction(self):
        """Retourne une fonction qui effectue l'exportation réelle. Cette fonction prend la visionneuse sélectionnée et les options d'exportation en paramètres."""
        raise NotImplementedError  # pragma: no cover


class FileManageBackups(IOCommand, settings_uicommand.SettingsCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Manage backups..."),
            helpText=_("Manage all task file backups"),
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileManageBackups command initialized")  # Débogage

    def doCommand(self, event):
        # dlg = dialog.BackupManagerDialog(
        #     self.mainWindow(), self.settings, self.iocontroller.filename()
        # )
        # try:
        #     if dlg.ShowModal() == wx.ID_OK:
        #         self.iocontroller.open(dlg.restoredFilename())
        # finally:
        #     dlg.Destroy()

        # Voici quelques suggestions pour moderniser votre code :
        #
        # Context manager with: Au lieu d'appeler explicitement dlg.Destroy(), utilisez le mot-clé with. Cela garantit que la fenêtre sera fermée même si une exception se produit :
        #     Python
        #
        #     def doCommand(self, event):
        with dialog.BackupManagerDialog(
            self.mainWindow(), self.settings, self.iocontroller.filename()
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                # self.iocontroller.open(dlg.restoredFilename())
                # restored_file = dlg.restoredFilename()
                try:
                    self.iocontroller.open(dlg.restoredFilename())
                except IOError as e:
                    log.error(
                        f"Erreur lors de l'ouverture de {dlg.restoredFilename()}: {e}"
                    )

    # F-strings: Pour formater des chaînes, privilégiez les f-strings (introduites en Python 3.6) qui offrent une syntaxe plus concise et lisible :
    #     Python
    #
    #     print(f"Le fichier {filename} a été ouvert.")
    # Annotations de type: Bien que facultatives, les annotations de type peuvent améliorer la lisibilité et la maintenabilité de votre code, en particulier pour des projets de plus grande envergure :
    #     Python
    #
    #     def doCommand(self, event: wx.Event) -> None:
    # Autres considérations:
    #
    #     Bibliothèque wxPython: Assurez-vous d'utiliser une version de wxPython compatible avec Python 3.
    #     Gestion des exceptions: Examinez si la gestion des exceptions peut être améliorée en utilisant des exceptions plus spécifiques ou en ajoutant des messages d'erreur plus informatifs.
    #     Style de codage: Adoptez un style de codage cohérent (PEP 8) pour faciliter la lecture et la collaboration.
    # TODO : changer la méthode en ceci :
    # def doCommand(self, event: wx.Event) -> None:
    #     with dialog.BackupManagerDialog(
    #             self.mainWindow(), self.settings, self.iocontroller.filename()
    #     ) as dlg:
    #         if dlg.ShowModal() == wx.ID_OK:
    #             restored_file = dlg.restoredFilename()
    #             try:
    #                 self.iocontroller.open(restored_file)
    #             except IOError as e:
    #                 print(f"Erreur lors de l'ouverture de {restored_file}: {e}")


class FileExportAsHTML(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format HTML.

    Uses a non-modal dialog to allow users to change selections while
    the export dialog is open."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &HTML..."),
            helpText=_("Export items from a viewer in HTML format"),
            bitmap="exportashtml",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileExportAsHTML command initialized")  # Débogage

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsHTMLDialog

    def exportFunction(self):
        return self.iocontroller.exportAsHTML

    def enabled(self, event):
        return True


class FileExportAsCSV(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format CSV.

    Uses a non-modal dialog to allow users to change selections while
    the export dialog is open."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &CSV..."),
            helpText=_(
                "Export items from a viewer in Comma Separated Values "
                "(CSV) format"
            ),
            bitmap="exportascsv",
            *args,
            **kwargs,
        )
        self._exportDialog = None
        # print("tclib.gui.uicommand.uicommand.FileExportAsCSV command initialized")  # Débogage

    def doCommand(self, event):
        """Show non-modal export dialog."""
        if self._exportDialog:
            self._exportDialog.Raise()
            return
        self._exportDialog = self.getExportDialogClass()(
            self.mainWindow(),
            settings=self.settings,
            exportCallback=self.exportFunction(),
        )
        self._exportDialog.Show()
        self._exportDialog.Bind(wx.EVT_WINDOW_DESTROY, self._onDialogDestroyed)

    def _onDialogDestroyed(self, event):
        """Clear dialog reference when destroyed."""
        self._exportDialog = None
        event.Skip()

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsCSVDialog

    def exportFunction(self):
        return self.iocontroller.exportAsCSV

    def enabled(self, event):
        return True


class FileExportAsICalendar(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format iCalendar.

    Uses a non-modal dialog to allow users to change selections while
    the export dialog is open."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &iCalendar..."),
            helpText=_("Export items from a viewer in iCalendar format"),
            bitmap="exportasvcal",
            *args,
            **kwargs,
        )
        self._exportDialog = None
        # print("tclib.gui.uicommand.uicommand.FileExportAsICalendar command initialized")  # Débogage

    def doCommand(self, event):
        """Show non-modal export dialog."""
        # If dialog already open, just raise it
        if self._exportDialog:
            self._exportDialog.Raise()
            return

        self._exportDialog = self.getExportDialogClass()(
            self.mainWindow(),
            settings=self.settings,
            exportCallback=self.exportFunction(),
        )
        # Use Show() for non-modal dialog
        self._exportDialog.Show()
        # Clear reference when dialog is destroyed
        self._exportDialog.Bind(wx.EVT_WINDOW_DESTROY, self._onDialogDestroyed)

    def _onDialogDestroyed(self, event):
        """Clear dialog reference when destroyed."""
        self._exportDialog = None
        event.Skip()

    def exportFunction(self):
        return self.iocontroller.exportAsICalendar

    def enabled(self, event):
        """Indique si la commande est activable"""
        return any(
            self.exportableViewer(viewer)
            for viewer in self.mainWindow().viewer
        )

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsICalendarDialog

    @staticmethod
    def exportableViewer(aViewer) -> bool:
        """Vérifie si la visionneuse peut être exportée au format iCalendar."""
        return aViewer.isShowingTasks() or (
            aViewer.isShowingEffort()
            and not aViewer.isShowingAggregatedEffort()
        )


class FileExportAsTodoTxt(FileExportCommand):
    """
    Action pour exporter le contenu d'une visionneuse au format Todo.txt.

    Uses a non-modal dialog to allow users to change selections while
    the export dialog is open."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Export as &Todo.txt..."),
            helpText=_(
                "Export items from a viewer in Todo.txt format "
                "(see todotxt.com)"
            ),
            bitmap="exportascsv",
            *args,
            **kwargs,
        )
        self._exportDialog = None
        # print("tclib.gui.uicommand.uicommand.FileExportAsTodoTxt command initialized")  # Débogage

    def doCommand(self, event):
        """Show non-modal export dialog."""
        if self._exportDialog:
            self._exportDialog.Raise()
            return
        self._exportDialog = self.getExportDialogClass()(
            self.mainWindow(),
            settings=self.settings,
            exportCallback=self.exportFunction(),
        )
        self._exportDialog.Show()
        self._exportDialog.Bind(wx.EVT_WINDOW_DESTROY, self._onDialogDestroyed)

    def _onDialogDestroyed(self, event):
        """Clear dialog reference when destroyed."""
        self._exportDialog = None
        event.Skip()

    def exportFunction(self):
        return self.iocontroller.exportAsTodoTxt

    def enabled(self, event):
        """Indique si la commande est activable"""
        return any(
            self.exportableViewer(viewer)
            for viewer in self.mainWindow().viewer
        )

    @staticmethod
    def getExportDialogClass():
        return dialog.export.ExportAsTodoTxtDialog

    @staticmethod
    def exportableViewer(aViewer):
        """Vérifie si la visionneuse peut être exportée au format Todo.txt."""
        return aViewer.isShowingTasks()


class FileImportCSV(IOCommand):
    """
    Action pour importer des données à partir d'un fichier CSV dans le fichier de tâches actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de CSV avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Import CSV..."),
            helpText=_(
                "Import tasks from a Comma Separated Values (CSV) file"
            ),
            bitmap="exportascsv",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileImportCSV command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande d'importation de CSV. Ouvre une boîte de dialogue pour sélectionner un fichier CSV et lance l'importation.
        """
        while True:
            filename = wx.FileSelector(_("Import CSV"), wildcard="*.csv")
            if filename:
                if len(open(filename, "rb").read()) == 0:
                    wx.MessageBox(
                        _(
                            "The selected file is empty. "
                            "Please select a different file."
                        ),
                        _("Import CSV"),
                    )
                    continue
                wizard = CSVImportWizard(
                    filename, None, wx.ID_ANY, _("Import CSV")
                )
                if wizard.RunWizard():
                    self.iocontroller.importCSV(**wizard.GetOptions())
                    break
            else:
                break


class FileImportTodoTxt(IOCommand):
    """
    Action pour importer des données à partir d'un fichier Todo.txt dans le fichier de tâches actuel.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'importation de Todo.txt avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Import Todo.txt..."),
            helpText=_("Import tasks from a Todo.txt (see todotxt.com) file"),
            bitmap="exportascsv",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileImportTodoTxt command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande d'importation de Todo.txt.

        Ouvre une boîte de dialogue pour sélectionner un fichier Todo.txt et lance l'importation.
        """
        filename = wx.FileSelector(_("Import Todo.txt"), wildcard="*.txt")
        if filename:
            self.iocontroller.importTodoTxt(filename)


class FileSynchronize(IOCommand, settings_uicommand.SettingsCommand):
    """
    Action pour synchroniser le fichier de tâches actuel avec un serveur SyncML.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de synchronisation avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("S&yncML synchronization..."),
            helpText=_("Synchronize with a SyncML server"),
            bitmap="arrows_looped_icon",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileSynchronize command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande de synchronisation. Lance le processus de synchronisation avec le serveur SyncML configuré.
        """
        self.iocontroller.synchronize()


class FileQuit(base_uicommand.UICommand):
    """
    Action pour quitter l'application.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour quitter avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Quit\tCtrl+Q"),
            helpText=help.fileQuit,
            bitmap="exit",
            id=wx.ID_EXIT,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.FileQuit command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour quitter l'application. Ferme la fenêtre principale de l'application.
        """
        log.debug(
            f"FileQuit.doCommand : Essaie de forcer à fermer {self.mainWindow()}."
        )
        self.mainWindow().Close(force=True)
        log.debug(
            "FileQuit.doCommand : self.mainWindow={self.mainWindow()} est fermé."
        )


class EditUndo(base_uicommand.UICommand):
    """
    Action pour annuler la dernière action effectuée par l'utilisateur.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les actions de l'utilisateur.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande d'annulation.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=self.getUndoMenuText(),
            helpText=help.editUndo,
            bitmap="undo",
            id=wx.ID_UNDO,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditUndo command initialized")  # Débogage

    @staticmethod
    def getUndoMenuText():
        """Retourne le texte du menu pour la commande d'annulation,
        en incluant la description de la dernière action utilisateur."""
        return "%s\tCtrl+Z" % patterns.CommandHistory().undostr(_("&Undo"))

    def doCommand(self, event):
        """Exécute la commande d'annulation en utilisant l'historique des commandes."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Undo()
        else:
            patterns.CommandHistory().undo()

    def onUpdateUI(self, event):
        """Met à jour le texte du menu avec la dernière action utilisateur."""
        self.updateMenuText(self.getUndoMenuText())
        super().onUpdateUI(event)

    def enabled(self, event):
        """Vérifie si l'annulation est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanUndo()
        else:
            # TODO: hasHistory is a list !? a bool was better ?
            return patterns.CommandHistory().hasHistory() and super().enabled(
                event
            )


class EditRedo(base_uicommand.UICommand):
    """
    Action pour rétablir la dernière action annulée par l'utilisateur.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les actions utilisateur.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de rétablissement.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=self.getRedoMenuText(),
            helpText=help.editRedo,
            bitmap="redo",
            id=wx.ID_REDO,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditRedo command initialized")  # Débogage

    @staticmethod
    def getRedoMenuText() -> str:
        """Retourne le texte du menu pour la commande de rétablissement, incluant une description de l'action suivante à rétablir."""
        # return "%s\tCtrl+Y" % patterns.CommandHistory().redostr(_("&Redo"))
        return f"{patterns.CommandHistory().redostr(_('&Redo'))}\tCtrl+Y"

    def doCommand(self, event):
        """Exécute la commande de rétablissement en utilisant l'historique des commandes."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Redo()
        else:
            patterns.CommandHistory().redo()

    def onUpdateUI(self, event):
        """Met à jour le texte du menu avec la prochaine action à rétablir."""
        self.updateMenuText(self.getRedoMenuText())
        super().onUpdateUI(event)

    def enabled(self, event):
        """Vérifie si le rétablissement est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanRedo()
        else:
            # Todo: hasFuture is a List ! not a bool !
            return patterns.CommandHistory().hasFuture() and super().enabled(
                event
            )


class EditCut(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour couper les éléments sélectionnés et les placer dans le presse-papier.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de découpage.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Cu&t\tCtrl+X"),
            helpText=help.editCut,
            bitmap="cut",
            # id=wx.ID_CUT,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditCut command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande de découpage."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Cut()
        else:
            cutCommand = self.viewer.cutItemCommand()
            cutCommand.do()

    def enabled(self, event):
        """Vérifie si le découpage est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanCut can be None ! a bool would be better !?
            return windowWithFocus.CanCut()
        else:
            return super().enabled(event)


class EditCopy(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour copier les éléments sélectionnés dans le presse-papier.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour gérer les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de copie.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Copy\tCtrl+C"),
            helpText=help.editCopy,
            bitmap="copy",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditCopy command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande de copie."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Copy()
        else:
            copyCommand = command.CopyCommand(
                self.viewer.presentation(), self.viewer.curselection()
            )
            copyCommand.do()

    def enabled(self, event):
        """Vérifie si la copie est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanCut can be None ! a bool would be better !?
            return windowWithFocus.CanCopy()
        else:
            return super().enabled(event)


class EditPaste(base_uicommand.UICommand):
    """
    Action pour coller le(s) élément(s) du presse-papier dans le fichier de tâches actuel.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour coller les éléments.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de collage.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Paste\tCtrl+V"),
            helpText=help.editPaste,
            bitmap="paste",
            id=wx.ID_PASTE,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditPaste command initialized")  # Débogage

    def doCommand(self, event):
        """Exécute la commande de collage."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Paste()
        else:
            pasteCommand = command.PasteCommand()
            pasteCommand.do()

    def enabled(self, event):
        """Vérifie si le collage est disponible."""
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            # Todo: CanPaste can be None ! a bool would be better !?
            return windowWithFocus.CanPaste()
        else:
            # return command.Clipboard() and super().enabled(event)
            clipboard = command.Clipboard()
            if not clipboard:
                return False
            if not super().enabled(event):
                return False
            # Check if clipboard contents are compatible with viewer
            if self.viewer and hasattr(self.viewer, "getSupportedPasteTypes"):
                supportedTypes = self.viewer.getSupportedPasteTypes()
                if supportedTypes:
                    items = clipboard.peek()
                    for item in items:
                        if not isinstance(item, supportedTypes):
                            return False
            return True


class EditPasteAsSubItem(
    mixin_uicommand.NeedsSelectedCompositeMixin, ViewerCommand
):
    """
    Action pour coller les éléments du presse-papier dans le fichier de tâches actuel,
    en tant que sous-élément de l'élément actuellement sélectionné.

    Attributs :
        viewer (Viewer) : La visionneuse utilisée pour coller les éléments en tant que sous-éléments.
    """

    shortcut = "\tShift+Ctrl+V"
    defaultMenuText = _("P&aste as subitem") + shortcut
    labels = {
        task.Task: _("P&aste as subtask"),
        note.Note: _("P&aste as subnote"),
        category.Category: _("P&aste as subcategory"),
    }

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande avec les options de menu et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("P&aste as subitem\tShift+Ctrl+V"),
            helpText=help.editPasteAsSubitem,
            bitmap="pasteintotask",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditPasteAsSubItem command initialized")  # Débogage

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        self.updateMenuText(self.__menuText())

    def __menuText(self):
        for class_ in self.labels:
            if self.viewer.curselectionIsInstanceOf(class_):
                return self.labels[class_] + self.shortcut
        return self.defaultMenuText

    def doCommand(self, event):
        """
        Exécute la commande de collage en tant que sous-élément.
        """
        # pasteCommand = command.PasteAsSubItemCommand(
        #     items=self.viewer.curselection()
        # )
        # pasteCommand.do()
        # Use viewer's pasteAsSubItemCommand if available
        viewer = self.viewer
        # If no viewer set, try to find one from the focused window hierarchy
        if viewer is None:
            windowWithFocus = wx.Window.FindFocus()
            viewer = self._findViewerFromFocus(windowWithFocus)
        if viewer is not None and hasattr(viewer, "pasteAsSubItemCommand"):
            parents = viewer.curselection()
            pasteCommand = viewer.pasteAsSubItemCommand()
        else:
            parents = self.viewer.curselection() if self.viewer else []
            pasteCommand = command.PasteAsSubItemCommand(items=parents)
        if pasteCommand:
            pasteCommand.do()
            # Expand parent items so the pasted subitems are visible
            if viewer is not None and hasattr(viewer, "settingsSection"):
                for parent in parents:
                    parent.expand(True, context=viewer.settingsSection())

    def _findViewerFromFocus(self, window):
        """Walk up the window hierarchy to find a viewer with pasteAsSubItemCommand.

        This is needed when paste-as-subitem is triggered from menus that don't
        have a viewer reference, but the focused window is inside a viewer.
        """
        while window is not None:
            if hasattr(window, "pasteAsSubItemCommand"):
                return window
            window = window.GetParent()
        return None

    def enabled(self, event) -> bool:
        """
        Vérifie si le collage en tant que sous-élément est possible.
        """
        if not (super().enabled(event) and command.Clipboard()):
            return False
        targetClass = self.viewer.curselection()[0].__class__
        pastedClasses = [item.__class__ for item in command.Clipboard().peek()]
        return self.__targetAndPastedAreEqual(
            targetClass, pastedClasses
        ) or self.__targetIsTaskAndPastedIsEffort(targetClass, pastedClasses)

    @classmethod
    def __targetIsTaskAndPastedIsEffort(
        cls, targetClass, pastedClasses
    ) -> bool:
        """Vérifie si la classe cible est une tâche et les éléments collés sont tous des efforts."""
        if targetClass != task.Task:
            return False
        return cls.__targetAndPastedAreEqual(effort.Effort, pastedClasses)

    @staticmethod
    def __targetAndPastedAreEqual(targetClass, pastedClasses) -> bool:
        """Vérifie si les classes de la cible et les éléments collés sont identiques."""
        for pastedClass in pastedClasses:
            if pastedClass != targetClass:
                return False
        return True


class EditPreferences(settings_uicommand.SettingsCommand):
    """
    Action pour ouvrir la boîte de dialogue des préférences.

    Attributs :
        settings (Settings) : Les paramètres de l'application.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande des préférences avec les options de menu et d'icône associées.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Preferences...\tAlt+P"),
            helpText=help.editPreferences,
            bitmap="wrench_icon",
            id=wx.ID_PREFERENCES,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditPreferences command initialized")  # Débogage

    def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
        """
        Affiche la boîte de dialogue des préférences.

        Args :
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si la boîte de dialogue doit être affichée.
        """
        editor = dialog.preferences.Preferences(
            parent=self.mainWindow(),
            title=_("Preferences"),
            settings=self.settings,
            taskFile=self.mainWindow().taskFile,
        )
        editor.Show(show)


class EditSyncPreferences(IOCommand):
    """
    Action pour afficher les préférences de synchronisation SyncML.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande des préférences de synchronisation.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&SyncML preferences..."),
            helpText=_("Edit SyncML preferences"),
            bitmap="arrows_looped_icon",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditSyncPreferences command initialized")  # Débogage

    def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
        """
        Affiche la boîte de dialogue des préférences de synchronisation SyncML.

        Args :
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si la boîte de dialogue doit être affichée.
        """
        editor = dialog.syncpreferences.SyncMLPreferences(
            parent=self.mainWindow(),
            iocontroller=self.iocontroller,
            title=_("SyncML preferences"),
        )
        editor.Show(show)


class EditToolBarPerspective(settings_uicommand.SettingsCommand):
    """
    Action pour éditer une barre d'outils personnalisable.

    Attributs :
        toolbar (wx.ToolBar) : La barre d'outils à personnaliser.
        editorClass (Class) : La classe utilisée pour éditer la barre d'outils.
    """

    def __init__(self, toolbar, editorClass, *args, **kwargs):
        """
        Initialise la commande pour personnaliser la barre d'outils.

        Args :
            toolbar (wx.ToolBar) : La barre d'outils à personnaliser.
            editorClass (Class) : La classe utilisée pour éditer la barre d'outils.
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        self.__toolbar = toolbar
        self.__editorClass = editorClass
        super().__init__(
            helpText=_("Customize toolbar"),
            bitmap="cogwheel_icon",
            menuText=_("Customize"),
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.EditToolBarPerspective command initialized")  # Débogage

    def doCommand(self, event):
        """
        Affiche la boîte de dialogue de personnalisation de la barre d'outils.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.__editorClass(
            self.__toolbar,
            self.settings,
            self.mainWindow(),
            _("Customize toolbar"),
        ).ShowModal()


class SelectAll(mixin_uicommand.NeedsItemsMixin, ViewerCommand):
    """
    Action pour sélectionner tous les éléments dans une visionneuse.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour sélectionner tous les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&All\tCtrl+A"),
            helpText=help.editSelectAll,
            bitmap="selectall",
            id=wx.ID_SELECTALL,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.SelectAll command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour sélectionner tous les éléments visibles dans la visionneuse.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            windowWithFocus.SetSelection(-1, -1)  # Sélectionne tout le texte
        else:
            self.viewer.select_all()

    @staticmethod
    def windowIsTextCtrl(window) -> bool:
        """
        Vérifie si la fenêtre actuelle est un contrôle de texte.
        """
        return isinstance(window, wx.TextCtrl) or isinstance(
            window, hypertreelist.EditCtrl
        )


class ClearSelection(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Action pour désélectionner tous les éléments dans une visionneuse.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour désélectionner tous les éléments avec les options de menu appropriées.
        """
        super().__init__(
            menuText=_("&Clear selection"),
            helpText=_("Unselect all items"),
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.ClearSelection command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour désélectionner tous les éléments.
        """
        self.viewer.clear_selection()


class ResetFilter(ViewerCommand):
    """
    Action pour réinitialiser tous les filtres afin que tous les éléments deviennent visibles dans toutes les visionneuses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réinitialiser tous les filtres avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Clear all filters\tShift-Ctrl-R"),
            helpText=help.resetFilter,
            bitmap="viewalltasks",
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.ResetFilter command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour réinitialiser tous les filtres actifs dans la visionneuse.
        """
        self.viewer.resetFilter()

    def enabled(self, event):
        """
        Vérifie si la commande est activée, c'est-à-dire s'il y a des filtres actifs à réinitialiser.
        """
        return self.viewer.hasFilter()


class ResetCategoryFilter(
    mixin_uicommand.NeedsAtLeastOneCategoryMixin, CategoriesCommand
):
    """
    Action pour réinitialiser tous les filtres de catégories afin que les éléments ne soient plus cachés en fonction des catégories.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réinitialiser les filtres de catégories avec les options de menu appropriées.
        """
        super().__init__(
            menuText=_("&Reset all categories\tCtrl-R"),
            helpText=help.resetCategoryFilter,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.ResetCategoryFilter command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour réinitialiser les filtres de catégories actifs.
        """
        self.categories.resetAllFilteredCategories()


class ToggleCategoryFilter(base_uicommand.UICommand):
    """
    Action pour activer ou désactiver le filtrage sur une catégorie spécifique.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de filtrage par catégorie avec les options de menu appropriées.
        """
        self.category = kwargs.pop("category")
        subject = self.category.subject()
        # Would like to use wx.ITEM_RADIO for mutually exclusive categories, but
        # a menu with radio items always has to have at least of the items
        # checked, while we allow none of the mutually exclusive categories to
        # be checked. Dynamically changing between wx.ITEM_CHECK and
        # wx.ITEM_RADIO would be a work-around in theory, using wx.ITEM_CHECK
        # when none of the mutually exclusive categories is checked and
        # wx.ITEM_RADIO otherwise, but dynamically changing the type of menu
        # items isn't possible. Hence, we use wx.ITEM_CHECK, even for mutual
        # exclusive categories.
        kind = wx.ITEM_CHECK
        super().__init__(
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Show/hide items belonging to %s") % subject,
            kind=kind,
            *args,
            **kwargs,
        )
        # print("tclib.gui.uicommand.uicommand.ToggleCategoryFilter command initialized")  # Débogage

    def doCommand(self, event):
        """
        Exécute la commande pour activer ou désactiver le filtrage sur la catégorie spécifiée.
        """
        self.category.setFiltered(event.IsChecked())


class ViewViewer(settings_uicommand.SettingsCommand, ViewerCommand):
    """
    Action pour ouvrir une nouvelle visionneuse d'une classe spécifique.

    Attributs :
        taskFile (TaskFile) : Le fichier de tâches utilisé par la visionneuse.
        viewerClass (class) : La classe de la visionneuse à ouvrir.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour ouvrir une nouvelle visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires, y compris 'taskFile' et 'viewerClass'.
        """
        self.taskFile = kwargs.pop("taskFile")
        self.viewerClass = kwargs.pop("viewerClass")
        kwargs.setdefault("bitmap", self.viewerClass.defaultBitmap)
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Ouvre une nouvelle instance de la visionneuse spécifiée.
        """
        from taskcoachlib.gui import viewer

        viewer.addOneViewer(
            self.viewer, self.taskFile, self.settings, self.viewerClass
        )
        self.increaseViewerCount()

    def increaseViewerCount(self):
        """
        Augmente le compteur de la classe visionneuses ouvertes, ouvre et enregistre la valeur dans les paramètres.
        """
        setting = self.viewerClass.__name__.lower() + "count"
        viewerCount = self.settings.getint("view", setting)
        self.settings.set("view", setting, str(viewerCount + 1))


class ViewEffortViewerForSelectedTask(
    settings_uicommand.SettingsCommand, ViewerCommand
):
    """
    Action pour ouvrir une visionneuse d'efforts pour les tâches sélectionnées.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour ouvrir une visionneuse d'efforts.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires, y compris 'taskFile'.
        """
        from taskcoachlib.gui import viewer

        self.viewerClass = viewer.EffortViewerForSelectedTasks
        self.taskFile = kwargs.pop("taskFile")
        kwargs["bitmap"] = viewer.EffortViewer.defaultBitmap
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Ouvre une visionneuse d'efforts pour les tâches sélectionnées.
        """
        from taskcoachlib.gui import viewer

        viewer.addOneViewer(
            self.viewer, self.taskFile, self.settings, self.viewerClass
        )


class RenameViewer(ViewerCommand):
    """
    Action pour renommer la visionneuse sélectionnée.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande de renommage de la visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Rename viewer..."),
            helpText=_("Rename the selected viewer"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Renomme la visionneuse active avec un nouveau nom.
        """
        activeViewer = self.viewer.activeViewer()
        viewerNameDialog = wx.TextEntryDialog(
            self.mainWindow(),  # parent
            _("New title for the viewer:"),  # message
            _("Rename viewer"),  # caption
            activeViewer.title(),  # default value
        )
        if viewerNameDialog.ShowModal() == wx.ID_OK:
            activeViewer.setTitle(viewerNameDialog.GetValue())
        viewerNameDialog.Destroy()

    def enabled(self, event):
        """
        Active la commande uniquement si une visionneuse est active.
        """
        return bool(self.viewer.activeViewer())


class ActivateViewer(ViewerCommand):
    """
    Action pour activer une autre visionneuse dans la direction spécifiée.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour changer de visionneuse.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        self.direction = kwargs.pop("forward")
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Change de visionneuse dans la direction spécifiée.
        """
        self.viewer.containerWidget.advanceSelection(self.direction)

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a plus d'une visionneuse.
        """
        return self.viewer.containerWidget.viewerCount() > 1


class HideCurrentColumn(ViewerCommand):
    """
    Action pour masquer la colonne actuellement sélectionnée dans la visionneuse.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour masquer la colonne sélectionnée.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("&Hide this column"),
            helpText=_("Hide the selected column"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Masque la colonne sélectionnée dans la visionneuse.

        Exécute la commande pour masquer la colonne sélectionnée dans la visionneuse.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        columnPopupMenu = event.GetEventObject()
        self.viewer.hideColumn(columnPopupMenu.columnIndex)

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande peut être exécutée, en déterminant la colonne actuelle basée sur la position de la souris.

        Args :
            event (wx.Event) : L'événement pour lequel la disponibilité de la commande est vérifiée.

        Returns :
            (bool) : True si la colonne peut être masquée, sinon False.
        """
        # Unfortunately the event (an UpdateUIEvent) does not give us any
        # information to determine the current column, so we have to find
        # the column ourselves. We use the current mouse position to do so.
        widget = (
            self.viewer.getWidget()
        )  # Must use method to make sure viewer dispatch works!
        # Utilise une méthode pour garantir que la vue est bien dispatchée.
        x, y = widget.ScreenToClient(wx.GetMousePosition())
        # Position actuelle de la souris.
        # Use wx.Point because CustomTreeCtrl assumes a wx.Point instance:
        columnIndex = widget.HitTest(wx.Point(x, y))[2]
        # Détermine la colonne à partir de la position de la souris.

        # Corrige un problème où -1 est retourné parfois pour la première colonne :
        # The TreeListCtrl returns -1 for the first column sometimes,
        # don't understand why. Work around as follows:
        if columnIndex == -1:
            columnIndex = 0
        return self.viewer.isHideableColumn(columnIndex)


class ViewColumn(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour afficher ou masquer une colonne spécifique dans la visionneuse.

    Cette commande contrôle la visibilité d'une colonne unique en fonction du nom de la colonne et de son état actuel (affiché ou masqué).
    """

    def isSettingChecked(self) -> bool:
        """
        Vérifie si la colonne est actuellement visible.

        Returns :
            (bool) : True si la colonne est visible, sinon False.
        """
        return self.viewer.isVisibleColumnByName(self.setting)

    def doCommand(self, event):
        """
        Exécute la commande pour afficher ou masquer la colonne en fonction de l'état du menu.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.showColumnByName(
            self.setting, self._isMenuItemChecked(event)
        )


class ViewColumns(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour afficher ou masquer un groupe de colonnes dans la visionneuse.

    Cette commande contrôle la visibilité de plusieurs colonnes à la fois en fonction de leur nom.
    """

    def isSettingChecked(self) -> bool:
        """
        Vérifie si toutes les colonnes du groupe sont actuellement visibles.

        Returns :
            (bool) : True si toutes les colonnes sont visibles, sinon False.
        """
        for columnName in self.setting:
            if not self.viewer.isVisibleColumnByName(columnName):
                return False
        return True

    def doCommand(self, event):
        """
        Exécute la commande pour afficher ou masquer les colonnes en fonction de l'état du menu.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        show = self._isMenuItemChecked(event)
        for columnName in self.setting:
            self.viewer.showColumnByName(columnName, show)


class ViewExpandAll(mixin_uicommand.NeedsTreeViewerMixin, ViewerCommand):
    """
    Action pour étendre tous les éléments dans une visionneuse arborescente.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour étendre tous les éléments.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            bitmap="tree_expand_all",
            menuText=_("&Expand all items\tShift+Ctrl+E"),
            helpText=help.viewExpandAll,
            *args,
            **kwargs,
        )

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a des éléments extensibles.
        """
        return super().enabled(event) and self.viewer.isAnyItemExpandable()

    def doCommand(self, event):
        """
        Étend tous les éléments dans la visionneuse.
        """
        self.viewer.expandAll()


class ViewCollapseAll(mixin_uicommand.NeedsTreeViewerMixin, ViewerCommand):
    """
    Action pour réduire tous les éléments dans une visionneuse arborescente.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour réduire tous les éléments.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            bitmap="tree_collapse_all",
            menuText=_("&Collapse all items\tShift+Ctrl+C"),
            helpText=help.viewCollapseAll,
            *args,
            **kwargs,
        )

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement s'il y a des éléments réductibles.
        """
        return super().enabled(event) and self.viewer.isAnyItemCollapsable()

    def doCommand(self, event):
        """
        Réduit tous les éléments dans la visionneuse.
        """
        self.viewer.collapseAll()


class ViewerSortByCommand(ViewerCommand, settings_uicommand.UIRadioCommand):
    """
    Action pour trier la visionneuse par une colonne spécifique.

    Méthodes :
        isSettingChecked() : Vérifie si la visionneuse est triée par la colonne spécifiée.
        doCommand(event) : Trie la visionneuse par la colonne spécifiée.
    """

    def isSettingChecked(self) -> bool:
        """
        Vérifie si la visionneuse est triée par la colonne spécifiée.

        Returns :
            (bool) : True si la visionneuse est triée par cette colonne, sinon False.
        """
        return self.viewer.isSortedBy(self.value)

    def doCommand(self, event):
        """
        Exécute la commande pour trier la visionneuse par la colonne spécifiée.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.sortBy(self.value)


class ViewerSortOrderCommand(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour définir l'ordre de tri de la visionneuse (ascendant ou descendant).

    Méthodes :
        isSettingChecked() : Vérifie si l'ordre de tri est ascendant.
        doCommand(event) : Change l'ordre de tri en fonction de l'état du menu.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Ascending"),
            helpText=_("Sort ascending (checked) or descending (unchecked)"),
            *args,
            **kwargs,
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si l'ordre de tri est ascendant.

        Returns :
            (bool) : True si l'ordre est ascendant, sinon False.
        """
        return self.viewer.isSortOrderAscending()

    def doCommand(self, event):
        """
        Exécute la commande pour changer l'ordre de tri.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortOrderAscending(self._isMenuItemChecked(event))


class ViewerSortCaseSensitive(
    ViewerCommand, settings_uicommand.UICheckCommand
):
    """
    Action pour définir si le tri est sensible à la casse.

    Méthodes :
        isSettingChecked() : Vérifie si le tri est sensible à la casse.
        doCommand(event) : Change la sensibilité à la casse du tri.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Sort &case sensitive"),
            helpText=_(
                "When comparing text, sorting is case sensitive "
                "(checked) or insensitive (unchecked)"
            ),
            *args,
            **kwargs,
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si le tri est sensible à la casse.

        Returns :
            bool : True si le tri est sensible à la casse, sinon False.
        """
        return self.viewer.isSortCaseSensitive()

    def doCommand(self, event):
        """
        Exécute la commande pour activer ou désactiver la sensibilité à la casse du tri.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortCaseSensitive(self._isMenuItemChecked(event))


class ViewerSortByTaskStatusFirst(
    ViewerCommand, settings_uicommand.UICheckCommand
):
    """
    Action pour trier les tâches par statut (actif/inactif/terminé) en priorité.

    Méthodes :
        isSettingChecked() : Vérifie si le tri est effectué d'abord par statut.
        doCommand(event) : Change la priorité de tri par statut.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Sort by status &first"),
            helpText=_(
                "Sort tasks by status (active/inactive/completed) " "first"
            ),
            *args,
            **kwargs,
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches sont triées d'abord par statut.

        Returns :
            (bool) : True si les tâches sont triées par statut en premier, sinon False.
        """
        return self.viewer.isSortByTaskStatusFirst()

    def doCommand(self, event):
        """
        Exécute la commande pour trier les tâches en premier par leur statut.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.setSortByTaskStatusFirst(self._isMenuItemChecked(event))


class ViewerHideTasks(ViewerCommand, settings_uicommand.UICheckCommand):
    """
    Action pour masquer les tâches en fonction de leur statut.

    Méthodes :
        isSettingChecked() : Vérifie si les tâches avec un certain statut sont masquées.
        doCommand(event) : Masque ou affiche les tâches en fonction de leur statut.
    """

    def __init__(self, taskStatus, *args, **kwargs):
        """
        Initialise la commande avec le statut des tâches à masquer ou afficher.

        Args :
            taskStatus : Le statut des tâches (actif/inactif/terminé).
        """
        self.__taskStatus = taskStatus
        super().__init__(
            menuText=taskStatus.hideMenuText,
            helpText=taskStatus.hideHelpText,
            bitmap=taskStatus.getHideBitmap(kwargs["settings"]),
            *args,
            **kwargs,
        )

    def uniqueName(self) -> str:
        """
        Retourne un nom unique pour cette commande en fonction du statut des tâches.
        """
        return super().uniqueName() + "_" + str(self.__taskStatus)

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches avec le statut spécifié sont masquées.

        Returns :
            (bool) : True si ces tâches sont masquées, sinon False.
        """
        return self.viewer.isHidingTaskStatus(self.__taskStatus)

    def doCommand(self, event):
        """
        Exécute la commande pour masquer ou afficher les tâches avec le statut spécifié.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        if wx.GetKeyState(wx.WXK_SHIFT):
            self.viewer.showOnlyTaskStatus(self.__taskStatus)
        else:
            self.viewer.hideTaskStatus(
                self.__taskStatus, self._isMenuItemChecked(event)
            )


class ViewerHideCompositeTasks(
    ViewerCommand, settings_uicommand.UICheckCommand
):
    """
    Action pour masquer les tâches composites (ayant des sous-tâches).

    Méthodes :
        isSettingChecked() : Vérifie si les tâches composites sont masquées.
        doCommand(event) : Masque ou affiche les tâches composites.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour masquer les tâches composites.

        Args :
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        super().__init__(
            menuText=_("Hide c&omposite tasks"),
            helpText=_("Show/hide tasks with subtasks in list mode"),
            *args,
            **kwargs,
        )

    def isSettingChecked(self) -> bool:
        """
        Vérifie si les tâches composites sont actuellement masquées.

        Returns :
            bool : True si les tâches composites sont masquées, sinon False.
        """
        return self.viewer.isHidingCompositeTasks()

    def enabled(self, event) -> bool:
        """
        Active la commande uniquement si la visionneuse n'est pas en mode arborescence.

        Returns :
            (bool) : True si la visionneuse est en mode liste, sinon False.
        """
        return not self.viewer.isTreeViewer()

    def doCommand(self, event):
        """
        Exécute la commande pour masquer ou afficher les tâches composites.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        self.viewer.hideCompositeTasks(self._isMenuItemChecked(event))


class Edit(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Commande pour modifier les éléments sélectionnés dans une visionneuse.

    Cette commande permet d'ouvrir un éditeur pour modifier l'élément sélectionné
    ou d'accepter les modifications dans un champ de texte en cours d'édition.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour éditer les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Edit...\tRETURN"),
            helpText=_("Edit the selected item(s)"),
            bitmap="edit",
            *args,
            **kwargs,
        )

    # def doCommand(self, event, show: bool = True):  # pylint: disable=W0221
    def doCommand(self, event, show=True):  # pylint: disable=W0221
        """
        Exécute la commande pour ouvrir un éditeur d'éléments ou accepter les modifications d'un champ de texte.

        Args :
            event (wx.Event) : L'événement déclencheur.
            show (bool) : Indique si l'éditeur doit être affiché.
        """
        windowWithFocus = wx.Window.FindFocus()
        editCtrl = self.findEditCtrl(windowWithFocus)
        if editCtrl:
            # editCtrl.AcceptChanges()
            editCtrl.AcceptsFocus()  # A vérifier !
            if editCtrl:
                editCtrl.Finish()  # Est-ce encore nécessaire ?
            return
        try:
            columnName = event.columnName
        except AttributeError:
            columnName = ""
        # Use forceUpdate=True to ensure we get the current selection,
        # not a stale cached value (important for fast double-click)
        items = self.viewer.curselection(forceUpdate=True)
        # editor = self.viewer.editItemDialog(
        #     self.viewer.curselection(), self.bitmap, columnName
        # )
        editor = self.viewer.editItemDialog(items, self.bitmap, columnName)
        if len(items) > 1:
            # Use modal dialog for multi-item editing to prevent selection
            # changes while editing
            editor.ShowModal()
        else:
            editor.Show(show)

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande est activée, c'est-à-dire s'il y a un élément sélectionné ou un champ en cours d'édition.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.findEditCtrl(windowWithFocus):
            return True
        elif operating_system.isMac() and isinstance(
            windowWithFocus, wx.TextCtrl
        ):
            return False
        else:
            return super().enabled(event)

    # @staticmethod
    def findEditCtrl(self, windowWithFocus):
        """
        Trouve le contrôle d'édition actif si disponible.

        Args :
            windowWithFocus (wx.Window) : La fenêtre actuellement active.

        Returns :
            (wx.Window) : Le contrôle d'édition si trouvé, sinon None.
        """
        while windowWithFocus:
            # if isinstance(windowWithFocus, thirdparty.hypertreelist.EditCtrl):
            if isinstance(windowWithFocus, hypertreelist.EditCtrl):
                break
            windowWithFocus = windowWithFocus.GetParent()
        return windowWithFocus


class EditTrackedTasks(TaskListCommand, settings_uicommand.SettingsCommand):
    """
    Modifier les tâches suivies.

    Cette commande permet de modifier les tâches actuellement suivies.

    Arguments :
        * aucun

    Paramètres :
        * aucun

    Retours :
        * une boîte de dialogue d'édition de tâche

    Exceptions :
        * aucune
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Edit &tracked task...\tShift-Alt-T"),
            helpText=_("Edit the currently tracked task(s)"),
            bitmap="edit",
            *args,
            **kwargs,
        )

    def doCommand(self, event, show: bool = True):
        """
        Ouvre la boîte de dialogue de modification de la tâche suivie.

        Args :
            event :
            show :

        Returns :
        """
        editTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            self.taskList.tasksBeingTracked(),
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        editTaskDialog.Show(show)
        return editTaskDialog  # for testing purposes

    def enabled(self, event):
        """
        Vérifie si les tâches sont suivies.

        Args :
            event:

        Returns :
        """
        return any(self.taskList.tasksBeingTracked())


class Delete(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Commande pour supprimer les éléments sélectionnés dans une visionneuse.

    Cette commande permet de supprimer les éléments sélectionnés ou de simuler
    une suppression de texte dans un champ de texte actif.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande pour supprimer les éléments avec les options de menu et d'icône appropriées.
        """
        super().__init__(
            menuText=_("&Delete\tCtrl+DEL"),
            helpText=_("Delete the selected item(s)"),
            bitmap="delete",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Exécute la commande pour supprimer les éléments ou le texte sélectionné.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            # Simulate Delete key press
            fromIndex, toIndex = windowWithFocus.GetSelection()
            if fromIndex == toIndex:
                pos = windowWithFocus.GetInsertionPoint()
                fromIndex, toIndex = pos, pos + 1
            windowWithFocus.Remove(fromIndex, toIndex)
        else:
            # Check if we're deleting categories that have assigned objects
            selectedItems = self.viewer.curselection()
            if selectedItems and isinstance(
                selectedItems[0], category.Category
            ):
                assignedObjects = self._getAssignedObjectsForCategories(
                    selectedItems
                )
                if assignedObjects:
                    self._showCategoryInUseDialog(assignedObjects)
                    return
            deleteCommand = self.viewer.deleteItemCommand()
            deleteCommand.do()

    def _getAssignedObjectsForCategories(self, categories):
        """Collect all objects assigned to the given categories and their subcategories."""
        allAssigned = {}
        for cat in categories:
            # Get all children of this category (including nested subcategories)
            allCategories = [cat] + list(cat.children(recursive=True))
            for c in allCategories:
                categorizables = c.categorizables()
                if categorizables:
                    allAssigned[c] = list(categorizables)
        return allAssigned

    def _findNoteOwner(self, targetNote, taskFile):
        """Find the owner (task or category) of a note."""
        # Search through all tasks
        for aTask in taskFile.tasks():
            if hasattr(aTask, "notes"):
                for aNote in aTask.notes(recursive=True):
                    if aNote is targetNote:
                        return aTask
        # Search through all categories
        for aCat in taskFile.categories():
            if hasattr(aCat, "notes"):
                for aNote in aCat.notes(recursive=True):
                    if aNote is targetNote:
                        return aCat
        return None

    def _getObjectDisplayPath(self, obj, taskFile):
        """Get the full display path for an object, including its owner if applicable."""
        objType = obj.__class__.__name__
        objSubject = obj.subject(recursive=True)

        # For notes, try to find their owner (task or category)
        if isinstance(obj, note.Note):
            owner = self._findNoteOwner(obj, taskFile)
            if owner:
                ownerPath = owner.subject(recursive=True)
                ownerType = owner.__class__.__name__
                return "[%s] %s -> [%s] %s" % (
                    ownerType,
                    ownerPath,
                    objType,
                    objSubject,
                )

        return "[%s] %s" % (objType, objSubject)

    def _showCategoryInUseDialog(self, assignedObjects):
        """Show a scrollable dialog listing all objects that prevent category deletion."""
        # Build the list content only (no header/footer)
        lines = []

        # Get taskFile for finding note owners
        taskFile = self.mainWindow().taskFile

        for cat, objects in assignedObjects.items():
            catName = cat.subject(recursive=True)
            lines.append(_("Category: %s") % catName)
            for obj in sorted(
                objects, key=lambda x: x.subject(recursive=True)
            ):
                displayPath = self._getObjectDisplayPath(obj, taskFile)
                lines.append("  - %s" % displayPath)
            lines.append("")

        # Create a scrollable dialog for potentially long lists
        dlg = wx.Dialog(
            self.mainWindow(),
            title=_("Cannot Delete - Category In Use"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header message (outside the scrollable area)
        headerText = wx.StaticText(
            dlg,
            label=_(
                "Cannot delete the selected category/categories because they have assigned objects:"
            ),
        )
        sizer.Add(headerText, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # Scrollable text area with the list
        textCtrl = wx.TextCtrl(
            dlg,
            value="\n".join(lines),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP,
            size=(600, 400),
        )
        sizer.Add(textCtrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Footer message (outside the scrollable area)
        footerText = wx.StaticText(
            dlg,
            label=_(
                "Please remove these assignments before deleting the category."
            ),
        )
        sizer.Add(footerText, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        # OK button
        okBtn = wx.Button(dlg, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        sizer.Add(okBtn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        dlg.SetSizer(sizer)
        dlg.Fit()
        dlg.CentreOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def enabled(self, event) -> bool:
        """
        Vérifie si la commande est activée, c'est-à-dire si des éléments ou du texte peuvent être supprimés.

        Args :
            event (wx.Event) : L'événement déclencheur.
        """
        windowWithFocus = wx.Window.FindFocus()
        if self.windowIsTextCtrl(windowWithFocus):
            return True
        else:
            return super().enabled(event)

    @staticmethod
    def windowIsTextCtrl(window) -> bool:
        """
        Vérifie si la fenêtre active est un contrôle de texte.

        Args :
            window (wx.Window) : La fenêtre active.

        Returns :
            (bool) : True si la fenêtre est un contrôle de texte, sinon False.
        """
        return isinstance(window, wx.TextCtrl) or isinstance(
            window, hypertreelist.EditCtrl
        )


class TaskNew(TaskListCommand, settings_uicommand.SettingsCommand):
    """
    Commande d'interface utilisateur permettant de créer une nouvelle tâche.

    Cette classe hérite de `TaskListCommand` et `settings_uicommand.SettingsCommand`.
    Elle encapsule la logique de création d'une nouvelle tâche en tenant compte des paramètres
    fournis par l'utilisateur et les paramètres par défaut configurés.

    Args :
        taskList (taskcoachlib.model.TaskList) : Liste de tâches dans laquelle créer la nouvelle tâche.
        *args, **kwargs : Arguments supplémentaires passés au constructeur de la classe de base.

    Keyword Arguments (optionnels) :
        taskKeywords (dict) : Dictionnaire de mots-clés à utiliser pour la création de la tâche.
            Prioritaire sur les paramètres par défaut.
        menuText (str) : Texte à afficher dans le menu pour la commande.
            Utilisé uniquement si non fourni dans `kwargs`.
        helpText (str) : Texte d'aide à afficher pour la commande.
            Utilisé uniquement si non fourni dans `kwargs`.

    Returns :
        (taskcoachlib.dialogs.TaskEditor) : Objet de dialogue d'édition de tâche nouvellement créé.


    **Explication de la classe TaskNew**

    La classe TaskNew implémente une commande d'interface utilisateur permettant à l'utilisateur de créer une nouvelle tâche. Elle hérite de deux classes :

        TaskListCommand : Fournit des fonctionnalités de base liées à la gestion des listes de tâches.
        settings_uicommand.SettingsCommand : Permet l'intégration avec les paramètres de configuration de l'application.

    Lors de l'exécution de la commande (doCommand), TaskNew effectue les actions suivantes :

        Préparation des mots-clés de la tâche :
            Copie les mots-clés fournis par l'utilisateur dans le constructeur (taskKeywords).
            Vérifie si des paramètres par défaut doivent être appliqués pour les dates et rappels en fonction des paramètres de configuration.
        Création de la commande NewTaskCommand :
            Utilise la classe command.NewTaskCommand pour créer une nouvelle tâche en tenant compte des mots-clés préparés.
            Inclut les catégories, prérequis et dépendances définies par les méthodes categoriesForTheNewTask, prerequisitesForTheNewTask et dependenciesForTheNewTask.
        Exécution de la commande de création de tâche :
            Exécute la commande NewTaskCommand pour créer la nouvelle tâche dans la liste de tâches.
        Affichage du dialogue d'édition de tâche :
            Crée un dialogue d'édition de tâche à l'aide de la classe dialog.editor.TaskEditor.
            Initialise le dialogue avec les éléments de la tâche nouvellement créée (newTaskCommand.items).
            Affiche le dialogue d'édition de tâche (Show) avec l'option de contrôle de l'affichage (show).

    Cette classe fournit un point d'entrée unique pour la création de nouvelles tâches, en gérant les paramètres par défaut et l'ouverture du dialogue d'édition consécutive.
    Points à considérer

    Les méthodes categoriesForTheNewTask, prerequisitesForTheNewTask, et dependenciesForTheNewTask peuvent être adaptées pour implémenter des logiques spécifiques de définition des catégories, prérequis et dépendances pour la nouvelle tâche.
    La méthode __shouldPreset*DateTime peut être étendue pour prendre en charge d'autres paramètres de date et d'heure par défaut.
    """

    def __init__(self, *args, **kwargs):
        # Dictionnaire de mots-clés à utiliser pour la création de la tâche :
        self.taskKeywords = kwargs.pop("taskKeywords", dict())
        #  Liste de tâches dans laquelle créer la nouvelle tâche :
        taskList = kwargs["taskList"]
        if "menuText" not in kwargs:  # Provide for subclassing
            kwargs["menuText"] = taskList.newItemMenuText
            kwargs["helpText"] = taskList.newItemHelpText
        super().__init__(bitmap="new", *args, **kwargs)

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        """Lors de l'exécution de la commande (doCommand), TaskNew effectue les actions suivantes :

        Préparation des mots-clés de la tâche :
            Copie les mots-clés fournis par l'utilisateur dans le constructeur (taskKeywords).
            Vérifie si des paramètres par défaut doivent être appliqués pour les dates et rappels en fonction des paramètres de configuration.
        Création de la commande NewTaskCommand :
            Utilise la classe command.NewTaskCommand pour créer une nouvelle tâche en tenant compte des mots-clés préparés.
            Inclut les catégories, prérequis et dépendances définies par les méthodes categoriesForTheNewTask, prerequisitesForTheNewTask et dependenciesForTheNewTask.
        Exécution de la commande de création de tâche :
            Exécute la commande NewTaskCommand pour créer la nouvelle tâche dans la liste de tâches.
        Affichage du dialogue d'édition de tâche :
            Crée un dialogue d'édition de tâche à l'aide de la classe dialog.editor.TaskEditor.
            Initialise le dialogue avec les éléments de la tâche nouvellement créée (newTaskCommand.items).
            Affiche le dialogue d'édition de tâche (Show) avec l'option de contrôle de l'affichage (show).
        """
        # Préparation des mots-clés de la tâche :
        # Copie les mots-clés fournis par l'utilisateur dans le constructeur (taskKeywords) :
        kwargs = self.taskKeywords.copy()
        # Vérifie si des paramètres par défaut doivent être appliqués pour les dates et rappels en fonction des paramètres de configuration :
        if self.__shouldPresetPlannedStartDateTime():
            kwargs["plannedStartDateTime"] = (
                task.Task.suggestedPlannedStartDateTime()
            )
        if self.__shouldPresetDueDateTime():
            kwargs["dueDateTime"] = task.Task.suggestedDueDateTime()
        if self.__shouldPresetActualStartDateTime():
            kwargs["actualStartDateTime"] = (
                task.Task.suggestedActualStartDateTime()
            )
        if self.__shouldPresetCompletionDateTime():
            kwargs["completionDateTime"] = (
                task.Task.suggestedCompletionDateTime()
            )
        if self.__shouldPresetReminderDateTime():
            kwargs["reminder"] = task.Task.suggestedReminderDateTime()
        #  Création de la commande NewTaskCommand :
        #             Utilise la classe command.NewTaskCommand pour créer une nouvelle tâche en tenant compte des mots-clés préparés.
        #             Inclut les catégories, prérequis et dépendances définies par les méthodes categoriesForTheNewTask, prerequisitesForTheNewTask et dependenciesForTheNewTask.
        newTaskCommand = command.NewTaskCommand(
            self.taskList,
            categories=self.categoriesForTheNewTask(),
            prerequisites=self.prerequisitesForTheNewTask(),
            dependencies=self.dependenciesForTheNewTask(),
            **kwargs,
        )
        # Exécution de la commande de création de tâche :
        #             Exécute la commande NewTaskCommand pour créer la nouvelle tâche dans la liste de tâches.
        newTaskCommand.do()
        # Affichage du dialogue d'édition de tâche :
        # Crée un dialogue d'édition de tâche à l'aide de la classe dialog.editor.TaskEditor.
        # Initialise le dialogue avec les éléments de la tâche nouvellement créée (newTaskCommand.items).
        newTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            newTaskCommand.items,
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
            items_are_new=True,
        )
        # Affiche le dialogue d'édition de tâche (Show) avec l'option de contrôle de l'affichage (show).
        newTaskDialog.Show(show)
        return newTaskDialog  # for testing purposes

    def categoriesForTheNewTask(self):
        """
        Détermine les catégories à attribuer à la nouvelle tâche.

        Retourne une liste de catégories filtrées à partir du fichier de tâches courant.
        """
        return self.mainWindow().taskFile.categories().filteredCategories()

    def prerequisitesForTheNewTask(self):
        """
        Détermine les tâches prérequises pour la nouvelle tâche.

        Actuellement, cette méthode retourne une liste vide, indiquant qu'aucune tâche
        n'est prérequise.
        """
        return []

    def dependenciesForTheNewTask(self):
        """
        Détermine les tâches dépendantes de la nouvelle tâche.

        Actuellement, cette méthode retourne une liste vide, indiquant qu'aucune tâche
        ne dépend de la nouvelle tâche.
        """
        return []

    def __shouldPresetPlannedStartDateTime(self):
        """
        Détermine si la date de début prévue doit être préremplie.

        Vérifie si une date de début n'a pas été spécifiée dans les mots-clés de la tâche
        et si le paramètre de configuration `defaultplannedstartdatetime` est défini sur "preset".

        Returns :
            bool : True si la date de début prévue doit être préremplie, False sinon.
        """
        return (
            "plannedStartDateTime" not in self.taskKeywords
            and self.settings.get(
                "view", "defaultplannedstartdatetime"
            ).startswith("preset")
        )

    def __shouldPresetDueDateTime(self):
        """
        Détermine si la date d'échéance doit être préremplie.

        Vérifie si une date d'échéance n'a pas été spécifiée dans les mots-clés de la tâche
        et si le paramètre de configuration `defaultduedatetime` est défini sur "preset".

        Returns :
            bool : True si la date d'échéance doit être préremplie, False sinon.
        """
        return "dueDateTime" not in self.taskKeywords and self.settings.get(
            "view", "defaultduedatetime"
        ).startswith("preset")

    def __shouldPresetActualStartDateTime(self):
        """
        Détermine si la date de début réelle doit être préremplie.

        Vérifie si une date de début réelle n'a pas été spécifiée dans les mots-clés de la tâche
        et si le paramètre de configuration `defaultactualstartdatetime` est défini sur "preset".

        Returns :
            bool : True si la date de début réelle doit être préremplie, False sinon.
        """
        return (
            "actualStartDateTime" not in self.taskKeywords
            and self.settings.get(
                "view", "defaultactualstartdatetime"
            ).startswith("preset")
        )

    def __shouldPresetCompletionDateTime(self):
        """
        Détermine si la date de fin doit être préremplie.

        Vérifie si une date de fin n'a pas été spécifiée dans les mots-clés de la tâche
        et si le paramètre de configuration `defaultcompletiondatetime` est défini sur "preset".

        Returns :
            bool : True si la date de fin doit être préremplie, False sinon.
        """
        return (
            "completionDateTime" not in self.taskKeywords
            and self.settings.get(
                "view", "defaultcompletiondatetime"
            ).startswith("preset")
        )

    def __shouldPresetReminderDateTime(self):
        """
        Détermine si la date de rappel doit être préremplie.

        Vérifie si une date de rappel n'a pas été spécifiée dans les mots-clés de la tâche
        et si le paramètre de configuration `defaultreminderdatetime` est défini sur "preset".

        Returns :
            bool : True si la date de rappel doit être préremplie, False sinon.
        """
        return "reminder" not in self.taskKeywords and self.settings.get(
            "view", "defaultreminderdatetime"
        ).startswith("preset")


class TaskNewFromTemplate(TaskNew):
    """
    Commande d'interface utilisateur permettant de créer une nouvelle tâche à partir d'un modèle.

    Hérite de la classe `TaskNew` et étend ses fonctionnalités pour la création de tâches
    en se basant sur un modèle de tâche stocké dans un fichier XML.

    Args :
        filename (str) : Chemin d'accès au fichier de modèle de tâche XML.
        *args, **kwargs : Arguments supplémentaires passés au constructeur de la classe de base.

    **Explication de TaskNewFromTemplate**

    La classe TaskNewFromTemplate s'appuie sur les fonctionnalités de TaskNew en permettant la création de nouvelles tâches basées sur un modèle prédéfini stocké dans un fichier XML.

    Voici une répartition de la classe et ses méthodes :

    Constructeur (__init__) :
        Hérite des arguments de TaskNew.
        Stocke le nom de fichier du modèle (self.__filename).
        Lit la tâche modèle à l'aide de __readTemplate et définit le texte du menu basé sur le sujet du modèle.

    __readTemplate :
        Lit les données de tâche à partir du fichier modèle XML à l'aide de persistence.TemplateXMLReader.
        Il est important d'envisager d'utiliser io.open pour une compatibilité plus large.

    doCommand (remplace TaskNew.doCommand) :
        Lit à nouveau la tâche modèle (pour capturer les valeurs dynamiques) à l'aide de __readTemplate.
        Obtient les attributs de la tâche à l'aide de __getcopystate__ (envisagez un nom de méthode plus descriptif).
        Fusionne les attributs du modèle avec les catégories decategoriesForTheNewTask.
        Crée une nouvelle commande de tâche à l'aide de command.NewTaskCommand.
        Exécute la nouvelle commande de tâche pour créer la tâche.
        Crée une boîte de dialogue d'éditeur de tâches à l'aide de dialog.editor.TaskEditor et affiche it.

    Points à prendre en compte :

        La méthode __readTemplate lit le modèle à chaque fois que doCommand est appelé. Cela peut s'avérer inefficace si le modèle ne change pas fréquemment. Pensez à mettre en cache les données du modèle, le cas échéant.
        Le nom de la méthode __getcopystate__ n'est pas très descriptif. Un nom plus spécifique lié à la récupération des attributs de tâche améliorerait la lisibilité.

    Docstrings pour les méthodes d'assistance

    Vous pouvez envisager d'ajouter des docstrings aux méthodes d'assistance comme __readTemplate avec des explications sur leur objectif et leurs valeurs de retour.
    """

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__filename = filename
        templateTask = self.__readTemplate()
        self.menuText = "&" + templateTask.subject().replace(
            "&", "&&"
        )  # pylint: disable=E1103

    def __readTemplate(self):
        """
        Lit le modèle de tâche à partir du fichier XML spécifié.

        Cette méthode charge les informations de la tâche à partir du fichier de modèle
        XML dont le chemin a été fourni lors de l'instanciation de la classe. Le modèle
        sert de base pour créer une nouvelle tâche.

        Note :
        * **Lecture à chaque appel :** Le modèle est relu à chaque appel de cette méthode
          pour s'assurer que les valeurs dynamiques (comme les dates) sont évaluées au
          moment de la création de la tâche.
        * **Utiliser `io.open` :** Il est recommandé d'utiliser `io.open` pour une meilleure
          compatibilité avec différents systèmes d'exploitation et encodages.

        Returns :
            taskcoachlib.model.Task : Un objet représentant la tâche définie dans le modèle.
        """
        # file -> open !!!? import io.open
        # return persistence.TemplateXMLReader(open(self.__filename, "rU")).read()
        return persistence.TemplateXMLReader(
            # open(self.__filename, "r", encoding="utf-8", newline=None)
            # # Le fichier est ouvert en mode texte ("r" avec encoding="utf-8").
            # # C'est pourquoi XMLReader reçoit un TextIOWrapper et que self.__fd.read() retourne une str.
            open(self.__filename, "rb")
        ).read()

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        """
        Exécute la commande de création d'une nouvelle tâche à partir du modèle.

        Cette méthode est appelée lorsque l'utilisateur sélectionne la commande dans l'interface.
        Elle crée une nouvelle tâche en se basant sur le modèle spécifié et ouvre un dialogue
        d'édition pour permettre à l'utilisateur de personnaliser la tâche.

        1. **Lecture du modèle :** Le modèle de tâche est relu à chaque appel pour garantir
           que les valeurs dynamiques sont actualisées.
        2. **Création d'une nouvelle tâche :** Un nouvel objet tâche est créé en copiant les
           attributs du modèle. Les catégories sont ajoutées à partir de la méthode
           `categoriesForTheNewTask`.
        3. **Exécution de la commande de création :** La commande de création de tâche est
           exécutée pour ajouter la nouvelle tâche à la liste de tâches.
        4. **Ouverture du dialogue d'édition :** Un dialogue d'édition est ouvert pour permettre
           à l'utilisateur de modifier les propriétés de la nouvelle tâche.

        Args :
            event (wx.CommandEvent) : Événement déclenché par l'utilisateur.
            show (bool, optionnel) : Indique si le dialogue d'édition doit être affiché.

        Returns :
            dialog.editor.TaskEditor : L'objet de dialogue d'édition de tâche.
        """
        # Le modèle de tâche est lu à chaque fois car c'est le
        # TemplateXMLReader qui évalue les valeurs dynamiques (Now()
        # doit être évalué lors de la création de la tâche par exemple).
        templateTask = self.__readTemplate()
        kwargs = templateTask.__getcopystate__()  # pylint: disable=E1103
        kwargs["categories"] = self.categoriesForTheNewTask()
        # Création d'une nouvelle tâche :
        newTaskCommand = command.NewTaskCommand(self.taskList, **kwargs)
        # Exécution de la commande de création :
        newTaskCommand.do()
        # pylint: disable=W0142
        # Ouverture du dialogue d'édition :
        newTaskDialog = dialog.editor.TaskEditor(
            self.mainWindow(),
            newTaskCommand.items,
            self.settings,
            self.taskList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
            items_are_new=True,
        )
        newTaskDialog.Show(show)
        return newTaskDialog  # for testing purposes


class TaskNewFromTemplateButton(
    mixin_uicommand.PopupButtonMixin,
    TaskListCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour créer une nouvelle tâche à partir d'un modèle.

    Cette classe combine les fonctionnalités de `mixin_uicommand.PopupButtonMixin`,
    `TaskListCommand` et `settings_uicommand.SettingsCommand` pour fournir une
    commande de bouton contextuel qui ouvre un menu de modèles de tâches.

    Lorsqu'un modèle de tâche est sélectionné, une nouvelle tâche est créée en
    utilisant le modèle comme base.
    """

    def createPopupMenu(self):
        """
        Crée le menu contextuel pour la commande.

        Cette méthode crée un menu contextuel contenant des options pour créer une nouvelle
        tâche à partir de différents modèles de tâches.

        Returns :
            (wx.Menu) : Le menu contextuel créé.
        """
        from taskcoachlib.gui import menu

        return menu.TaskTemplateMenu(
            self.mainWindow(), self.taskList, self.settings
        )

    def getMenuText(self):
        """
        Obtient le texte à afficher pour la commande dans le menu principal.

        Returns :
            (str) : Le texte à afficher dans le menu.
        """
        return _("New task from &template")

    def getHelpText(self):
        """
        Obtient le texte d'aide pour la commande.

        Returns :
            (str) : Le texte d'aide à afficher pour la commande.
        """
        return _("Create a new task from a template")


class NewTaskWithSelectedCategories(TaskNew, ViewerCommand):
    """
    Commande d'interface utilisateur pour créer une nouvelle tâche avec les catégories sélectionnées.

    Cette classe hérite de `TaskNew` et `ViewerCommand` pour créer une nouvelle tâche avec les catégories
    actuellement sélectionnées dans la vue courante.

    Args :
        *args, **kwargs : Arguments supplémentaires passés au constructeur de la classe de base.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected &categories..."),
            helpText=_(
                "Insert a new task with the selected categories checked"
            ),
            *args,
            **kwargs,
        )

    def enabled(self, event):
        return super().enabled(event) and bool(
            self.viewer.curselection(forceUpdate=True)
        )

    def categoriesForTheNewTask(self):
        """
        Détermine les catégories à attribuer à la nouvelle tâche en fonction des catégories sélectionnées dans la vue courante.

        Returns :
            (list) : Une liste des catégories sélectionnées.
        """
        return self.viewer.curselection()


class NewTaskWithSelectedTasksAsPrerequisites(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskNew, ViewerCommand
):
    """
    Commande d'interface utilisateur pour créer une nouvelle tâche avec les tâches sélectionnées comme prérequis.

    Cette classe hérite de `mixin_uicommand.NeedsSelectedTasksMixin`, `TaskNew` et `ViewerCommand`.
    Elle crée une nouvelle tâche avec les tâches sélectionnées dans la vue courante comme prérequis.

    Args :
        *args, **kwargs : Arguments supplémentaires passés au constructeur de la classe de base.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected tasks as &prerequisites..."),
            helpText=_(
                "Insert a new task with the selected tasks as prerequisite tasks"
            ),
            *args,
            **kwargs,
        )

    def prerequisitesForTheNewTask(self):
        """
        Détermine les tâches prérequises pour la nouvelle tâche en fonction des tâches sélectionnées dans la vue courante.

        Returns :
            (list) : Une liste des tâches sélectionnées en tant que prérequis.
        """
        return self.viewer.curselection()


class NewTaskWithSelectedTasksAsDependencies(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskNew, ViewerCommand
):
    """
    Commande d'interface utilisateur pour créer une nouvelle tâche avec les tâches sélectionnées comme dépendances.

    Cette classe hérite de `mixin_uicommand.NeedsSelectedTasksMixin`, `TaskNew` et `ViewerCommand`.
    Elle crée une nouvelle tâche avec les tâches sélectionnées dans la vue courante comme dépendances.

    Args :
        *args, **kwargs : Arguments supplémentaires passés au constructeur de la classe de base.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("New task with selected tasks as &dependents..."),
            helpText=_(
                "Insert a new task with the selected tasks as dependent tasks"
            ),
            *args,
            **kwargs,
        )

    def dependenciesForTheNewTask(self):
        """
        Détermine les tâches dépendantes de la nouvelle tâche en fonction des tâches sélectionnées dans la vue courante.

        Returns :
            (list) : Une liste des tâches sélectionnées en tant que dépendances.
        """
        return self.viewer.curselection()


class NewSubItem(
    mixin_uicommand.NeedsOneSelectedCompositeItemMixin, ViewerCommand
):
    """
    Commande d'interface utilisateur pour créer un nouvel élément enfant.

    Cette classe hérite de `mixin_uicommand.NeedsOneSelectedCompositeItemMixin` et `ViewerCommand`.
    Elle permet de créer un nouvel élément enfant (sous-tâche, sous-note ou sous-catégorie)
    pour l'élément sélectionné dans la vue courante.

    Le texte du menu et l'icône de la commande sont adaptés en fonction du type de l'élément
    parent sélectionné.
    """

    shortcut = (
        "\tCtrl+INS" if operating_system.isWindows() else "\tShift+Ctrl+N"
    )
    # defaultMenuText = _('New &subitem...') + shortcut
    # TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
    defaultMenuText = _("New &subitem...") + shortcut
    labels = {
        task.Task: _("New &subtask..."),
        note.Note: _("New &subnote..."),
        category.Category: _("New &subcategory..."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.defaultMenuText,
            helpText=_("Insert a new subitem of the selected item"),
            bitmap="newsub",
            *args,
            **kwargs,
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        self.viewer.newSubItemDialog(bitmap=self.bitmap).Show(show)

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        self.updateMenuText(self.__menuText())

    def __menuText(self):
        for class_ in self.labels:
            if self.viewer.curselectionIsInstanceOf(class_):
                return self.labels[class_] + self.shortcut
        return self.defaultMenuText


class TaskMarkActive(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    """
    Commande d'interface utilisateur pour marquer des tâches comme actives.

    Cette classe permet de marquer les tâches sélectionnées comme actives. Une tâche est
    considérée active si sa date de début réelle est antérieure à la date actuelle ou si
    elle est déjà marquée comme terminée.

    La commande nécessite la sélection d'au moins une tâche et vérifie si les tâches
    sélectionnées peuvent être marquées comme actives avant d'exécuter l'action.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.active.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &active\tAlt+RETURN"),
            helpText=_("Mark the selected task(s) active"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        command.MarkActiveCommand(
            self.viewer.presentation(), self.viewer.curselection()
        ).do()

    def enabled(self, event):
        def canBeMarkedActive(aTask):
            return (
                aTask.actualStartDateTime() > date.Now() or aTask.completed()
            )

        return super().enabled(event) and any(
            [canBeMarkedActive(task) for task in self.viewer.curselection()]
        )


class TaskMarkInactive(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    """
    Commande d'interface utilisateur pour marquer des tâches comme inactives.

    Cette classe permet de marquer les tâches sélectionnées comme inactives. Une tâche peut
    être marquée inactive si elle n'est pas déjà inactive et n'est pas considérée en retard.

    La commande nécessite la sélection d'au moins une tâche et vérifie si les tâches
    sélectionnées peuvent être marquées comme inactives avant d'exécuter l'action.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.inactive.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &inactive\tCtrl+Alt+RETURN"),
            helpText=_("Mark the selected task(s) inactive"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        command.MarkInactiveCommand(
            self.viewer.presentation(), self.viewer.curselection()
        ).do()

    def enabled(self, event):
        def canBeMarkedInactive(aTask):
            return not aTask.inactive() and not aTask.late()

        return super().enabled(event) and any(
            [canBeMarkedInactive(task) for task in self.viewer.curselection()]
        )


class TaskMarkCompleted(
    mixin_uicommand.NeedsSelectedTasksMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    """
    Commande d'interface utilisateur pour marquer des tâches comme terminées.

    Cette classe permet de marquer les tâches sélectionnées comme terminées. Une tâche est
    considérée terminée si elle n'est pas déjà marquée comme terminée.

    La commande nécessite la sélection d'au moins une tâche et vérifie si les tâches
    sélectionnées peuvent être marquées comme terminées avant d'exécuter l'action.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap=task.completed.getBitmap(kwargs["settings"]),
            menuText=_("Mark task &completed\tCtrl+RETURN"),
            helpText=_("Mark the selected task(s) completed"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        markCompletedCommand = command.MarkCompletedCommand(
            self.viewer.presentation(), self.viewer.curselection()
        )
        markCompletedCommand.do()

    def enabled(self, event):
        def canBeMarkedCompleted(task):
            return not task.completed()

        return super().enabled(event) and any(
            [canBeMarkedCompleted(task) for task in self.viewer.curselection()]
        )


class TaskMaxPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour définir la priorité maximale des tâches sélectionnées.

    Cette classe permet de définir la priorité maximale pour les tâches sélectionnées.
    Elle utilise la commande `MaxPriorityCommand` pour effectuer l'action.

    La commande nécessite la sélection d'au moins une tâche avant de pouvoir être exécutée.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Maximize priority\tShift+Ctrl+I"),
            helpText=help.taskMaxPriority,
            bitmap="maxpriority",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        maxPriority = command.MaxPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        maxPriority.do()


class TaskMinPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour définir la priorité minimale des tâches sélectionnées.

    Cette classe permet de définir la priorité minimale pour les tâches sélectionnées.
    Elle utilise la commande `MinPriorityCommand` pour effectuer l'action.

    La commande nécessite la sélection d'au moins une tâche avant de pouvoir être exécutée.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Minimize priority\tShift+Ctrl+D"),
            helpText=help.taskMinPriority,
            bitmap="minpriority",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        minPriority = command.MinPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        minPriority.do()


class TaskIncPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour augmenter la priorité des tâches sélectionnées.

    Cette classe permet d'augmenter la priorité des tâches sélectionnées d'un niveau.
    Elle utilise la commande `IncPriorityCommand` pour effectuer l'action.

    La commande nécessite la sélection d'au moins une tâche avant de pouvoir être exécutée.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Increase priority\tCtrl+I"),
            helpText=help.taskIncreasePriority,
            bitmap="incpriority",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        incPriority = command.IncPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        incPriority.do()


class TaskDecPriority(
    mixin_uicommand.NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour diminuer la priorité des tâches sélectionnées.

    Cette classe permet de diminuer la priorité des tâches sélectionnées d'un niveau.
    Elle utilise la commande `DecPriorityCommand` pour effectuer l'action.

    La commande nécessite la sélection d'au moins une tâche avant de pouvoir être exécutée.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Decrease priority\tCtrl+D"),
            helpText=help.taskDecreasePriority,
            bitmap="decpriority",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        decPriority = command.DecPriorityCommand(
            self.taskList, self.viewer.curselection()
        )
        decPriority.do()


class DragAndDropCommand(ViewerCommand):
    """
    Classe abstraite de base pour gérer les opérations de glisser-déposer dans la vue.

    Cette classe de base définit le comportement commun pour les opérations de glisser-déposer
    dans la vue. Elle fournit des méthodes pour activer la commande (`onCommandActivate`) et
    exécuter l'action de glisser-déposer (`doCommand`).

    La méthode `createCommand` est une implémentation abstraite qui doit être redéfinie
    par les classes filles pour créer la commande spécifique en fonction des éléments
    glissés et déposés, de la partie de la vue affectée et de la colonne concernée (si applicable).

    La classe ne gère pas le traitement spécifique de l'opération de glisser-déposer.
    Les classes filles doivent implémenter la logique de déplacement des éléments.
    """

    def onCommandActivate(
        self, dropItem, dragItems, part, column
    ):  # pylint: disable=W0221
        """Méthode appelée lors de l'activation de la commande de glisser-déposer.

        Remplace onCommandActivate pour pouvoir accepter deux éléments au lieu
        d'un événement.

        Cette méthode est appelée lorsque l'utilisateur active la commande de glisser-déposer
        (par exemple, en relâchant la souris sur un élément de dépôt). Elle transmet les
        informations sur l'élément de dépôt, les éléments glissés, la partie de la vue affectée
        et la colonne concernée (si applicable) à la méthode `doCommand` pour exécuter l'action.
        """

        self.doCommand(
            dropItem,
            dragItems,
            part,
            column=(
                None if column == -1 else self.viewer.visibleColumns()[column]
            ),
        )

    def doCommand(
        self, dropItem, dragItems, part, column, dropColumn=-1
    ):  # pylint: disable=W0221
        """Méthode principale pour exécuter l'opération de glisser-déposer.

        Cette méthode crée la commande spécifique en utilisant la méthode `createCommand` et
        l'exécute si possible. Elle renvoie la commande créée pour une gestion potentielle
        supplémentaire.

        La classe fille doit implémenter la logique de création de la commande appropriée
        et sa méthode `canDo` pour vérifier si l'opération est possible.
        """
        dragAndDropCommand = self.createCommand(
            dropItem=dropItem,
            dragItems=dragItems,
            part=part,
            column=column,
            isTree=self.viewer.isTreeViewer(),
            dropColumn=dropColumn,
        )
        if dragAndDropCommand.canDo():
            dragAndDropCommand.do()
            return dragAndDropCommand

    def createCommand(
        self, dropItem, dragItems, part, column, isTree, dropColumn=-1
    ):
        """Méthode abstraite à implémenter pour créer la commande de glisser-déposer.

        Cette méthode doit être redéfinie par les classes filles pour créer la commande
        spécifique en fonction des informations fournies (élément de dépôt, éléments glissés,
        partie de la vue, colonne et structure arborescente).

        La commande créée doit encapsuler la logique de déplacement des éléments.
        """
        raise NotImplementedError  # pragma: no cover


class OrderingDragAndDropCommand(DragAndDropCommand):
    """
    Classe concrète qui gère les opérations de glisser-déposer pour l'ordre des éléments.

    Cette classe hérite de `DragAndDropCommand` et implémente un comportement supplémentaire
    pour les opérations de glisser-déposer qui affectent l'ordre des éléments dans la vue.
    Si une opération de tri est détectée après l'exécution de la commande de base,
    une commande de tri supplémentaire est déclenchée pour garantir un ordre correct.

    Cette classe gère le cas spécifique où le glisser-déposer a pour but de réorganiser
    les éléments.
    """

    def doCommand(self, dropItem, dragItems, part, column, dropColumn=-1):
        """Exécute la commande de glisser-déposer et trie les éléments si nécessaire.

        Cette méthode se base sur la méthode `doCommand` de la classe parent,
        mais vérifie ensuite si la commande créée concerne le réarrangement des
        éléments. Si c'est le cas, une commande de tri est déclenchée pour
        s'assurer que l'ordre de la vue est cohérent avec l'ordre des tâches.
        """
        command = super().doCommand(
            dropItem, dragItems, part, column, dropColumn
        )  # command à renommer !
        if command is not None and command.isOrdering():
            sortCommand = ViewerSortByCommand(
                viewer=self.viewer, value="ordering"
            )
            sortCommand.doCommand(None)


class TaskDragAndDrop(OrderingDragAndDropCommand, TaskListCommand):
    """
    Commande de glisser-déposer spécifique aux tâches.

    Cette classe combine les fonctionnalités de `OrderingDragAndDropCommand` et
    `TaskListCommand` pour gérer le glisser-déposer des tâches. Elle crée une
    commande `DragAndDropTaskCommand` spécifique aux tâches en fonction des éléments
    glissés et déposés, de la partie de la vue affectée et de la colonne concernée.

    Cette classe permet de déplacer des tâches et de maintenir l'ordre de la liste
    de tâches à jour après un glisser-déposer.
    """

    def createCommand(
        self, dropItem, dragItems, part, column, isTree, dropColumn=-1
    ):
        # Get column name if dropColumn is valid
        dropColumnName = None
        if dropColumn >= 0:
            visibleCols = self.viewer.visibleColumns()
            if dropColumn < len(visibleCols):
                dropColumnName = visibleCols[dropColumn].name()

        return command.DragAndDropTaskCommand(
            self.taskList,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
            dropColumn=dropColumn,
            dropColumnName=dropColumnName,
        )


class ToggleCategory(
    mixin_uicommand.NeedsSelectedCategorizableMixin, ViewerCommand
):
    """
    Commande d'interface utilisateur pour activer/désactiver une catégorie pour les éléments sélectionnés.

    Cette classe permet d'activer ou de désactiver une catégorie spécifique pour les éléments sélectionnés
    dans la vue courante.

    La commande gère les catégories mutuellement exclusives, mais en raison de limitations de wxPython,
    elle utilise des cases à cocher (wx.ITEM_CHECK) même si la sélection de plusieurs catégories mutuellement
    exclusives n'est pas autorisée.

    La commande met à jour son texte d'affichage en fonction du libellé de la catégorie et vérifie son état d'activation
    pour les éléments sélectionnés avant l'exécution.

    Attributes :
        category (Category) : La catégorie à activer/désactiver.
    """

    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category")
        subject = self.category.subject()
        # J'aimerais utiliser wx.ITEM_RADIO pour les catégories mutuellement exclusives, mais
        # un menu avec des éléments radio doit toujours avoir au moins des éléments
        # cochés, alors que nous n'autorisons aucune des catégories mutuellement exclusives à
        # être vérifié. Changer dynamiquement entre wx.ITEM_CHECK et
        # wx.ITEM_RADIO serait une solution de contournement en théorie, en utilisant wx.ITEM_CHECK
        # lorsqu'aucune des catégories mutuellement exclusives n'est cochée et
        # wx.ITEM_RADIO sinon, mais changer dynamiquement le type d'éléments du menu
        # n'est pas possible. Par conséquent, nous utilisons wx.ITEM_CHECK,
        # même pour les catégories exclusives mutuelles.
        kind = wx.ITEM_CHECK
        super().__init__(
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Toggle %s") % subject,
            kind=kind,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Exécute la commande pour activer ou désactiver le filtrage sur la catégorie spécifiée.
        """
        check = command.ToggleCategoryCommand(
            category=self.category, items=self.viewer.curselection()
        )
        check.do()

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        if self.enabled(event):
            check = self.__all_selected_items_are_in_category()
            for menuItem in self.menuItems:
                menuItem.Check(check)

    def __all_selected_items_are_in_category(self):
        selected_items_in_category = [
            item
            for item in self.viewer.curselection()
            if self.category in item.categories()
        ]
        return selected_items_in_category == self.viewer.curselection()

    def enabled(self, event):
        viewerHasSelection = super().enabled(event)
        if not viewerHasSelection or self.viewer.isShowingCategories():
            return False
        mutual_exclusive_ancestors = [
            ancestor
            for ancestor in self.category.ancestors()
            if ancestor.isMutualExclusive()
        ]
        for categorizable in self.viewer.curselection():
            for ancestor in mutual_exclusive_ancestors:
                if ancestor not in categorizable.categories():
                    return False  # Not all mutually exclusive ancestors are checked
        return True  # All mutually exclusive ancestors are checked


class Mail(mixin_uicommand.NeedsSelectionMixin, ViewerCommand):
    """
    Commande d'interface utilisateur pour envoyer un email à partir des éléments sélectionnés.

    Cette classe permet d'envoyer un email en utilisant les informations des éléments sélectionnés
    dans la vue courante.

    La commande gère la génération du sujet, du corps du message, de la liste des destinataires principaux
    (To) et en copie (Cc) en se basant sur les attributs et la description des éléments sélectionnés.

    Elle prend en charge également la gestion des cas d'erreur lors de l'envoi de l'email.

    Attributes :
        rx_attr (re.compile) : Expression régulière pour extraire les destinataires (To et Cc)
            à partir des attributs des éléments sélectionnés.
    """

    rx_attr = re.compile(r"(cc|to)=(.*)")

    def __init__(self, *args, **kwargs):
        menuText = (
            _("&Mail...\tShift-Ctrl-M")
            if operating_system.isMac()
            else _("&Mail...\tCtrl-M")
        )
        super().__init__(
            menuText=menuText,
            helpText=help.mailItem,
            bitmap="envelope_icon",
            *args,
            **kwargs,
        )

    def doCommand(
        self, event, mail=sendMail, showerror=wx.MessageBox
    ):  # pylint: disable=W0221
        items = self.viewer.curselection()
        subject = self.subject(items)
        body = self.body(items)
        to = self.to(items)
        cc = self.cc(items)
        self.mail(to, cc, subject, body, mail, showerror)

    # @staticmethod
    def subject(self, items):
        assert items
        if len(items) > 2:
            return _("Several things")
        elif len(items) == 2:
            subjects = [item.subject(recursive=True) for item in items]
            return " ".join([subjects[0], _("and"), subjects[1]])
        else:
            return items[0].subject(recursive=True)

    def body(self, items):
        if len(items) > 1:
            bodyLines = []
            for item in items:
                bodyLines.extend(self.itemToLines(item))
        else:
            bodyLines = items[0].description().splitlines()
        return "\r\n".join(bodyLines)

    def to(self, items):
        return self._mailAttr("to", items)

    def cc(self, items):
        return self._mailAttr("cc", items)

    # @staticmethod
    def _mailAttr(self, name, items):
        sets = []
        for item in items:
            sets.append(
                set(
                    [
                        value[len(name) + 1 :]
                        for value in item.customAttributes("mailto")
                        if value.startswith("%s=" % name)
                    ]
                )
            )
        return reduce(operator.or_, sets)

    # @staticmethod
    def itemToLines(self, item):
        lines = []
        subject = item.subject(recursive=True)
        lines.append(subject)
        if item.description():
            lines.extend(item.description().splitlines())
            lines.extend("\r\n")
        return lines

    # @staticmethod
    def mail(self, to, cc, subject, body, mail, showerror):
        try:
            mail(to, subject, body, cc=cc)
        except Exception:
            # Try again with a dummy recipient:
            try:
                mail("recipient@domain.com", subject, body)
            except Exception as reason:  # pylint: disable=W0703
                showerror(
                    # _("Cannot send email:\n%s") % ExceptionAsUnicode(reason),
                    _("Cannot send email:\n%s") % str(reason),
                    caption=_("%s mail error") % meta.name,
                    style=wx.ICON_ERROR,
                )


class AddNote(
    mixin_uicommand.NeedsSelectedNoteOwnersMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour ajouter une note à des éléments sélectionnés.

    Cette classe permet d'ajouter une note aux éléments sélectionnés dans la vue courante.
    Elle utilise la commande `AddNoteCommand` pour créer la note et ensuite ouvre une fenêtre d'édition
    pour la saisie du contenu de la note.

    La commande nécessite la sélection d'éléments qui possèdent des notes.

    Attributes :
        bitmap (str) : Le chemin vers l'icône de la commande (facultatif).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Add &note...\tCtrl+B"),
            helpText=help.addNote,
            bitmap="note_icon",
            *args,
            **kwargs,
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        addNoteCommand = command.AddNoteCommand(
            self.viewer.presentation(), self.viewer.curselection()
        )
        addNoteCommand.do()
        editDialog = dialog.editor.NoteEditor(
            self.mainWindow(),
            addNoteCommand.items,
            self.settings,
            self.viewer.presentation(),
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        editDialog.Show(show)
        return editDialog  # à des fins de tests


class OpenAllNotes(
    mixin_uicommand.NeedsSelectedNoteOwnersMixinWithNotes,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour ouvrir toutes les notes des éléments sélectionnés.

    Cette classe permet d'ouvrir toutes les notes associées aux éléments sélectionnés
    dans la vue courante.

    La commande nécessite la sélection d'éléments qui possèdent des notes.

    Attributes :
        bitmap (str) : Le chemin vers l'icône de la commande (facultatif).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Open all notes...\tShift+Ctrl+B"),
            helpText=help.openAllNotes,
            bitmap="edit",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        for item in self.viewer.curselection():
            for note in item.notes():
                editDialog = dialog.editor.NoteEditor(
                    self.mainWindow(),
                    [note],
                    self.settings,
                    self.viewer.presentation(),
                    self.mainWindow().taskFile,
                    bitmap=self.bitmap,
                )
                editDialog.Show()


class EffortNew(
    mixin_uicommand.NeedsAtLeastOneTaskMixin,
    ViewerCommand,
    EffortListCommand,
    TaskListCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour créer un nouvel effort pour une tâche sélectionnée.

    Cette classe permet de créer un nouvel effort lié à une tâche sélectionnée dans la vue courante.
    Elle utilise la commande `NewEffortCommand` pour créer l'effort et ensuite ouvre une fenêtre d'édition
    pour la saisie des détails de l'effort.

    La commande nécessite la sélection d'au moins une tâche.

    Attributes :
        bitmap (str) : Le chemin vers l'icône de la commande (facultatif).
        effortList (EffortList) : La liste d'efforts utilisée pour gérer les efforts.
    """

    def __init__(self, *args, **kwargs):
        effortList = kwargs["effortList"]
        super().__init__(
            bitmap="new",
            menuText=effortList.newItemMenuText,
            helpText=effortList.newItemHelpText,
            *args,
            **kwargs,
        )

    def enabled(self, event):
        if not super().enabled(event):
            return False
        # When viewer is showing tasks, require a task to be selected
        if self.viewer and self.viewer.isShowingTasks():
            return bool(self.viewer.curselection(forceUpdate=True))
        return True

    def doCommand(self, event, show=True):
        if (
            self.viewer
            and self.viewer.isShowingTasks()
            and self.viewer.curselection()
        ):
            selectedTasks = self.viewer.curselection()
        elif self.viewer and self.viewer.isShowingEffort():
            selectedEfforts = self.viewer.curselection()
            if selectedEfforts:
                selectedTasks = [selectedEfforts[0].task()]
            else:
                selectedTasks = [
                    self.firstTask(self.viewer.domainObjectsToView())
                ]
        else:
            selectedTasks = [self.firstTask(self.taskList)]

        newEffortCommand = command.NewEffortCommand(
            self.effortList, selectedTasks
        )
        newEffortCommand.do()
        newEffortDialog = dialog.editor.EffortEditor(
            self.mainWindow(),
            newEffortCommand.items,
            self.settings,
            self.effortList,
            self.mainWindow().taskFile,
            bitmap=self.bitmap,
        )
        if show:
            newEffortDialog.Show()
        return newEffortDialog

    @staticmethod
    def firstTask(tasks):
        subjectDecoratedTasks = [
            (eachTask.subject(recursive=True), eachTask) for eachTask in tasks
        ]
        subjectDecoratedTasks.sort()
        return subjectDecoratedTasks[0][1]


class EffortStart(
    mixin_uicommand.NeedsSelectedTasksMixin, ViewerCommand, TaskListCommand
):
    """UICommand pour commencer à suivre l’effort pour la ou les tâches sélectionnées.

    Commande d'interface utilisateur pour démarrer le suivi des efforts pour les tâches sélectionnées.

    Cette classe permet de lancer le suivi des efforts pour les tâches sélectionnées dans la vue courante.
    Elle utilise la commande `StartEffortCommand` pour démarrer le suivi.

    La commande nécessite la sélection de tâches qui ne sont pas terminées et qui ne sont pas déjà en cours de suivi.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="clock_icon",
            menuText=_("&Start tracking effort\tCtrl-T"),
            helpText=help.effortStart,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(
            self.taskList, self.viewer.curselection()
        )
        start.do()

    def enabled(self, event):
        return super().enabled(event) and any(
            not task.completed() and not task.isBeingTracked()
            for task in self.viewer.curselection()
        )


class EffortStartForEffort(
    mixin_uicommand.NeedsSelectedEffortMixin, ViewerCommand, TaskListCommand
):
    """UICommand pour démarrer le suivi des tâches des efforts sélectionnés.

    Commande d'interface utilisateur pour démarrer le suivi des efforts pour les tâches associées aux efforts sélectionnés.

    Cette classe permet de lancer le suivi des efforts pour les tâches associées aux efforts sélectionnés
    dans la vue courante. Elle utilise la commande `StartEffortCommand` pour démarrer le suivi.

    La commande nécessite la sélection d'efforts.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="clock_icon",
            menuText=_("&Start tracking effort"),
            helpText=_(
                "Start tracking effort for the task(s) of the selected effort(s)"
            ),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(
            self.taskList, self.trackableTasks()
        )
        start.do()

    def enabled(self, event):
        return super().enabled(event) and self.trackableTasks()

    def trackableTasks(self):
        tasks = set([effort.task() for effort in self.viewer.curselection()])
        return [
            task
            for task in tasks
            if not task.completed() and not task.isBeingTracked()
        ]


class EffortStartForTask(TaskListCommand):
    """UICommand(Commande d'interface utilisateur) pour démarrer le suivi d’une tâche spécifique.


    Cette commande peut être utilisée
    pour créer un menu avec des éléments de menu séparés pour toutes les tâches.
    Voir gui.menu.StartEffortForTaskMenu.

    Cette classe permet de lancer le suivi des efforts pour une tâche spécifique. Elle peut être utilisée
    pour créer un menu contextuel avec des options de démarrage de suivi pour chaque tâche.

    Attributes :
        task (Task) : La tâche pour laquelle démarrer le suivi des efforts.
    """

    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop("task")
        subject = self.task.subject() or _("(No subject)")
        super().__init__(
            bitmap=self.task.icon(recursive=True),
            menuText="&" + subject.replace("&", "&&"),
            helpText=_("Start tracking effort for %s") % subject,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, [self.task])
        start.do()

    def enabled(self, event):
        return not self.task.isBeingTracked() and not self.task.completed()


class EffortStartButton(mixin_uicommand.PopupButtonMixin, TaskListCommand):
    """
    Bouton de la barre d'outils pour démarrer le suivi des efforts.

    Ce bouton affiche un menu contextuel avec des options de démarrage de suivi pour chaque tâche de la liste de tâches.

    La commande nécessite la présence d'au moins une tâche non terminée dans la liste de tâches.
    """

    def __init__(self, *args, **kwargs):
        kwargs["taskList"] = base.filter.DeletedFilter(kwargs["taskList"])
        super().__init__(
            bitmap="clock_menu_icon",
            menuText=_("&Start tracking effort"),
            helpText=_(
                "Select a task via the menu and start tracking effort for it"
            ),
            *args,
            **kwargs,
        )

    def createPopupMenu(self):
        from taskcoachlib.gui import menu

        return menu.StartEffortForTaskMenu(self.mainWindow(), self.taskList)

    def enabled(self, event):
        return any(not task.completed() for task in self.taskList)


class EffortStop(EffortListCommand, TaskListCommand, ViewerCommand):
    """
        Commande d'interface utilisateur pour arrêter ou reprendre le suivi des efforts.

         Cette classe permet d'arrêter le suivi des efforts en cours ou de reprendre le suivi
         du dernier arrêt. Elle utilise la commande `StopEffortCommand` pour arrêter le suivi
         et `StartEffortCommand` pour le reprendre.

         La commande peut être utilisée via un bouton de la barre d'outils avec un menu contextuel
         qui affiche des options en fonction de l'état actuel du suivi.

         Le comportement de la commande change en fonction de l'état du suivi des efforts:

         * Si un ou plusieurs efforts sont en cours de suivi, la commande les arrête.
         * Si aucun effort n'est en cours de suivi mais qu'il y a eu des arrêts précédents,
           la commande reprend le suivi de la dernière tâche arrêtée.

         Attributes :
             defaultMenuText (str) : Texte par défaut du menu ("Stop tracking or resume tracking effort\tShift+Ctrl+T")
             defaultHelpText (str) : Texte d'aide par défaut ("Stop or resume tracking effort")
             stopMenuText (str) : Texte du menu pour arrêter le suivi ("Stop tracking %s\tShift+Ctrl+T")
             stopHelpText (str) : Texte d'aide pour arrêter le suivi ("Stop tracking effort for the active task(s)")
             resumeMenuText (str) : Texte du menu pour reprendre le suivi ("Resume tracking %s\tShift+Ctrl+T")
             resumeHelpText (str) : Texte d'aide pour reprendre le suivi ("Resume tracking effort for the last tracked task")
             bitmap (str) : Chemin vers l'icône de la commande pour le suivi en cours (facultatif).
             bitmap2 (str) : Chemin vers l'icône de la commande pour le suivi arrêté (facultatif).

        Les méthodes clés de cette classe sont les suivantes :
    **Méthodes de gestion de l'état et de l'interface utilisateur :**

        __onEffortsChanged(efforts) : Cette méthode privée est appelée lorsqu'il y a une modification dans la liste des efforts. Elle déclenche la mise à jour de l'interface utilisateur pour refléter les changements d'état.
        updateUI() : Cette méthode met à jour l'interface utilisateur en fonction de l'état actuel du suivi :
            État du bouton de la barre d'outils : Active ou désactive le bouton en fonction de si des efforts peuvent être démarrés ou arrêtés.
            Icône du bouton : Change l'icône du bouton en fonction de si le suivi est en cours ou arrêté.
            Texte du menu : Met à jour le texte du menu pour indiquer l'action à effectuer (arrêter ou reprendre).
            État des éléments de menu : Met à jour l'état des éléments de menu pour refléter l'état du suivi.

    **Méthodes de récupération des informations sur l'état du suivi :**

        efforts () : Cette méthode retourne un ensemble des efforts actuellement suivis, en tenant compte de la sélection de l'utilisateur et de l'état des efforts dans la liste.
        anyStoppedEfforts () : Cette méthode indique s'il y a eu des efforts arrêtés précédemment.
        anyTrackedEfforts () : Cette méthode indique s'il y a des efforts actuellement en cours de suivi.
        mostRecentTrackedTask () : Cette méthode retourne la tâche pour laquelle le suivi a été arrêté le plus récemment.

    **Méthodes pour effectuer les actions de démarrage et d'arrêt :**

        doCommand (event=None) : Cette méthode est appelée lorsque l'utilisateur clique sur le bouton ou le menu. Elle détermine si le suivi doit être démarré ou arrêté en fonction de l'état actuel et exécute la commande correspondante (StartEffortCommand ou StopEffortCommand).

    **Méthodes utilitaires :**

        trimmedSubject (subject, maxLength=35, postFix="...") : Cette méthode tronque un sujet trop long pour l'affichage dans le menu.

    **Fonctionnement général :**

        Initialisation : Lors de la création de l'instance, la classe s'abonne aux événements de modification de la liste des efforts pour pouvoir mettre à jour l'interface utilisateur en temps réel.
        Mise à jour de l'interface utilisateur : L'interface utilisateur est mise à jour régulièrement pour refléter l'état actuel du suivi. Le texte du menu, l'icône du bouton et l'état des éléments de menu sont ajustés en conséquence.
        Exécution de la commande : Lorsque l'utilisateur clique sur le bouton ou le menu, la méthode doCommand est appelée. Elle détermine l'action à effectuer (démarrer ou arrêter le suivi) et exécute la commande correspondante.

    En résumé, cette classe offre une interface utilisateur flexible et réactive pour gérer le démarrage et l'arrêt du suivi des efforts dans une application de gestion de tâches. Elle s'adapte aux différents états du système et fournit à l'utilisateur des informations claires sur l'action en cours.

    Points clés:

        Flexibilité: La classe peut gérer différents scénarios (aucun effort en cours, plusieurs efforts en cours, reprise d'un effort arrêté).
        Réactivité: L'interface utilisateur est mise à jour en temps réel pour refléter les changements d'état.
        Clarté: Les textes des menus et les icônes sont clairs et concis.
        Extensibilité: La classe peut être facilement adaptée à d'autres types d'applications de gestion de tâches.
    """

    defaultMenuText = _(
        "Stop tracking or resume tracking effort\tShift+Ctrl+T"
    )
    defaultHelpText = help.effortStopOrResume
    stopMenuText = _("St&op tracking %s\tShift+Ctrl+T")
    stopHelpText = _("Stop tracking effort for the active task(s)")
    resumeMenuText = _("&Resume tracking %s\tShift+Ctrl+T")
    resumeHelpText = _("Resume tracking effort for the last tracked task")

    def __init__(self, *args, **kwargs):
        """Lors de la création de l'instance,
        la classe s'abonne aux événements de modification de la liste des efforts
        pour pouvoir mettre à jour l'interface utilisateur en temps réel."""
        super().__init__(
            bitmap="clock_resume_icon",
            bitmap2="clock_stop_icon",
            menuText=self.defaultMenuText,
            helpText=self.defaultHelpText,
            kind=wx.ITEM_CHECK,
            *args,
            **kwargs,
        )
        self.__tracker = effort.EffortListTracker(self.effortList)
        for subtype in ["", ".added", ".removed"]:
            self.__tracker.subscribe(
                self.__onEffortsChanged, "effortlisttracker%s" % subtype
            )
        self.__currentBitmap = None  # Don't know yet what our bitmap is

    def __onEffortsChanged(self, efforts):
        """Cette méthode privée est appelée lorsqu'il y a une modification dans la liste des efforts.
        Elle déclenche la mise à jour de l'interface utilisateur pour refléter les changements d'état.
        """
        self.updateUI()

    def efforts(self):
        """Cette méthode retourne un ensemble des efforts actuellement suivis,
        en tenant compte de la sélection de l'utilisateur et de l'état des efforts dans la liste.
        """
        selectedEfforts = set()
        for item in self.viewer.curselection():
            if isinstance(item, task.Task):
                selectedEfforts |= set(item.efforts())
            elif isinstance(item, effort.Effort):
                selectedEfforts.add(item)
        selectedEfforts &= set(self.__tracker.trackedEfforts())
        return (
            selectedEfforts
            if selectedEfforts
            else self.__tracker.trackedEfforts()
        )

    def doCommand(self, event=None):
        """Cette méthode est appelée lorsque l'utilisateur clique sur le bouton ou le menu.
        Elle détermine si le suivi doit être démarré ou arrêté en fonction de l'état actuel
        et exécute la commande correspondante (StartEffortCommand ou StopEffortCommand).
        """
        efforts = self.efforts()
        if efforts:
            # Arrête les efforts suivis
            effortCommand = command.StopEffortCommand(self.effortList, efforts)
        else:
            # Reprend le suivi de la dernière tâche
            effortCommand = command.StartEffortCommand(
                self.taskList, [self.mostRecentTrackedTask()]
            )
        effortCommand.do()

    def enabled(self, event=None):
        """S'il y a des efforts suivis, cette commande les arrêtera. S'il y a
        efforts non suivis, cette commande les reprendra. Sinon, cette commande
        est désactivée."""
        return self.anyTrackedEfforts() or self.anyStoppedEfforts()

    def onUpdateUI(self, event):
        super().onUpdateUI(event)
        self.updateUI()

    def updateUI(self):
        """Cette méthode met à jour l'interface utilisateur en fonction de l'état actuel du suivi :

        État du bouton de la barre d'outils : Active ou désactive le bouton en fonction de si des efforts peuvent être démarrés ou arrêtés.
        Icône du bouton : Change l'icône du bouton en fonction de si le suivi est en cours ou arrêté.
        Texte du menu : Met à jour le texte du menu pour indiquer l'action à effectuer (arrêter ou reprendre).
        État des éléments de menu : Met à jour l'état des éléments de menu pour refléter l'état du suivi.

        L'interface utilisateur est mise à jour régulièrement pour refléter l'état actuel du suivi.
        Le texte du menu, l'icône du bouton et l'état des éléments de menu sont ajustés en conséquence.
        """
        paused = self.anyStoppedEfforts() and not self.anyTrackedEfforts()
        self.updateToolState(not paused)
        bitmapName = self.bitmap if paused else self.bitmap2
        menuText = self.getMenuText(paused)
        if (bitmapName != self.__currentBitmap) or bool(
            [
                item
                for item in self.menuItems
                if item.GetItemLabel() != menuText
            ]
        ):
            self.__currentBitmap = bitmapName
            self.updateToolBitmap(bitmapName)
            self.updateToolHelp()
            self.updateMenuItems(paused)

    def updateToolState(self, paused):
        if not self.toolbar:
            return  # La barre d'outils est masquée
        if paused != self.toolbar.GetToolState(self.id):
            self.toolbar.ToggleTool(self.id, paused)

    def updateToolBitmap(self, bitmapName):
        if not self.toolbar:
            return  # La barre d'outils est masquée
        bitmap = wx.ArtProvider.GetBitmap(
            bitmapName, wx.ART_TOOLBAR, self.toolbar.GetToolBitmapSize()
        )
        # Sur wxGTK, la modification du bitmap ne fonctionne pas lorsque l'outil est
        # désactivé, nous l'activons donc d'abord si nécessaire :
        disable = False
        if not self.toolbar.GetToolEnabled(self.id):
            self.toolbar.EnableTool(self.id, True)
            disable = True
        self.toolbar.SetToolNormalBitmap(self.id, bitmap)
        if disable:
            self.toolbar.EnableTool(self.id, False)
        self.toolbar.Realize()

    def updateMenuItems(self, paused):
        menuText = self.getMenuText(paused)
        helpText = self.getHelpText(paused)
        for menuItem in self.menuItems:
            menuItem.Check(paused)
            menuItem.SetItemLabel(menuText)
            menuItem.SetHelp(helpText)

    def getMenuText(self, paused=None):  # pylint: disable=W0221
        if self.anyTrackedEfforts():
            trackedEfforts = list(self.efforts())
            subject = (
                _("multiple tasks")
                if len(trackedEfforts) > 1
                else trackedEfforts[0].task().subject()
            )
            return self.stopMenuText % self.trimmedSubject(subject)
        if paused is None:
            paused = self.anyStoppedEfforts()
        if paused:
            return self.resumeMenuText % self.trimmedSubject(
                self.mostRecentTrackedTask().subject()
            )
        else:
            return self.defaultMenuText

    def getHelpText(self, paused=None):  # pylint: disable=W0221
        if self.anyTrackedEfforts():
            return self.stopHelpText
        if paused is None:
            paused = self.anyStoppedEfforts()
        return self.resumeHelpText if paused else self.defaultHelpText

    def anyStoppedEfforts(self):
        """Cette méthode indique s'il y a des efforts arrêtés précédemment."""
        return bool(self.effortList.maxDateTime())

    def anyTrackedEfforts(self):
        """Cette méthode indique s'il y a des efforts actuellement en cours de suivi."""
        return bool(self.efforts())

    def mostRecentTrackedTask(self):
        """Cette méthode retourne la tâche pour laquelle le suivi a été arrêté le plus récemment."""
        stopTimes = [
            (effort.getStop(), effort)
            for effort in self.effortList
            if effort.getStop() is not None
        ]
        return max(stopTimes)[1].task()

    @staticmethod
    def trimmedSubject(subject, maxLength=35, postFix="..."):
        """Cette méthode tronque un sujet trop long pour l'affichage dans le menu."""
        trim = len(subject) > maxLength
        return (
            subject[: maxLength - len(postFix)] + postFix if trim else subject
        )


class CategoryNew(CategoriesCommand, settings_uicommand.SettingsCommand):
    """
    Commande d'interface utilisateur pour créer une nouvelle catégorie.

    Cette classe permet de créer une nouvelle catégorie via un menu contextuel
    ou un bouton de la barre d'outils.

    Attributes :
        bitmap (str) : Chemin vers l'icône de la commande (facultatif).
        menuText (str) : Texte du menu contextuel ("New category...\tCtrl-G").
        helpText (str) : Texte d'aide pour la commande.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="new",
            menuText=_("New category...\tCtrl-G"),
            helpText=help.categoryNew,
            *args,
            **kwargs,
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        newCategoryCommand = command.NewCategoryCommand(self.categories)
        newCategoryCommand.do()
        taskFile = self.mainWindow().taskFile
        newCategoryDialog = dialog.editor.CategoryEditor(
            self.mainWindow(),
            newCategoryCommand.items,
            self.settings,
            taskFile.categories(),
            taskFile,
            bitmap=self.bitmap,
        )
        newCategoryDialog.Show(show)


class CategoryDragAndDrop(OrderingDragAndDropCommand, CategoriesCommand):
    """
    Commande de gestion du glisser-déposer pour les catégories.

    Cette classe permet de réorganiser les catégories par glisser-déposer.
    Elle utilise la commande `DragAndDropCategoryCommand` pour effectuer
    l'opération de réorganisation.

    Elle hérite de deux classes :
     - `OrderingDragAndDropCommand` : Fournit les fonctionnalités de base
       pour le glisser-déposer avec réorganisation.
     - `CategoriesCommand` : Permet d'accéder aux informations et aux
       fonctionnalités liées aux catégories.

    Attributes :
        # Héritées de OrderingDragAndDropCommand
        # ... (attributs de OrderingDragAndDropCommand)
        # Héritées de CategoriesCommand
        # ... (attributs de CategoriesCommand)
    """

    def createCommand(
        self, dropItem, dragItems, part, column, isTree, dropColumn=-1
    ):
        """
        Crée une commande `DragAndDropCategoryCommand` pour effectuer
        l'opération de réorganisation de catégorie.

        Args :
            dropItem : L'élément de catégorie sur lequel on dépose.
            dragItems : Les éléments de catégorie à déplacer.
            part : La partie de la liste des catégories concernée (par ex.,
                   toutes les catégories, celles d'une tâche spécifique).
            column : La colonne de la liste des catégories concernée
                   (pas utilisé pour les catégories).
            isTree : Indique s'il s'agit d'un glisser-déposer d'arborescence
                   (pas applicable pour les catégories).

        Returns :
            Une instance de `DragAndDropCategoryCommand` configurée pour
            l'opération de réorganisation.
        """
        return command.DragAndDropCategoryCommand(
            self.categories,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
            dropColumn=dropColumn,
        )


class CategoryCheckAll(ViewerCommand):
    """Command to check all category checkboxes in the viewer.

    Used in the category viewer to quickly select all categories for
    filtering or assignment.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="checkall",
            menuText=_("Check &all categories"),
            helpText=_("Check all category checkboxes"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.checkAllCategories()


class CategoryUncheckAll(ViewerCommand):
    """Command to uncheck all category checkboxes in the viewer.

    Used in the category viewer to quickly deselect all categories.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            bitmap="uncheckall",
            menuText=_("&Uncheck all categories"),
            helpText=_("Uncheck all category checkboxes"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.uncheckAllCategories()


class NoteNew(NotesCommand, settings_uicommand.SettingsCommand, ViewerCommand):
    """
    Commande d'interface utilisateur pour créer une nouvelle note.

    Cette classe permet de créer une nouvelle note via un menu contextuel
    ou un bouton de la barre d'outils.

    Le comportement de la commande dépend du contexte d'utilisation :

    * Si la visionneuse affiche des notes, la commande ouvre une fenêtre d'édition
      vide pour la création d'une nouvelle note.
    * Si la visionneuse n'affiche pas de notes, la commande crée d'abord la
      nouvelle note en interne puis ouvre une fenêtre d'édition pour la modifier.

    Attributes :
        menuText (str) : Texte du menu contextuel ("New note...\tCtrl-J").
        helpText (str) : Texte d'aide pour la commande.
        bitmap (str) : Chemin vers l'icône de la commande (facultatif).
    """

    menuText = _("New note...\tCtrl-J")
    helpText = help.noteNew

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap="new",
            *args,
            **kwargs,
        )

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        if self.viewer and self.viewer.isShowingNotes():
            noteDialog = self.viewer.newItemDialog(bitmap=self.bitmap)
        else:
            newNoteCommand = command.NewNoteCommand(
                self.notes, categories=self.categoriesForTheNewNote()
            )
            newNoteCommand.do()
            noteDialog = dialog.editor.NoteEditor(
                self.mainWindow(),
                newNoteCommand.items,
                self.settings,
                self.notes,
                self.mainWindow().taskFile,
                bitmap=self.bitmap,
            )
        noteDialog.Show(show)
        return noteDialog  # à des fins de tests

    def categoriesForTheNewNote(self):
        """
        Retourne les catégories à utiliser pour la nouvelle note.

        Cette méthode est appelée pour déterminer les catégories associées à
        la nouvelle note. Son comportement peut être personnalisé pour répondre
        à des besoins spécifiques (par exemple, filtrage des catégories).

        Returns :
            Une liste des catégories à associer à la nouvelle note.
        """
        return self.mainWindow().taskFile.categories().filteredCategories()


class NewNoteWithSelectedCategories(NoteNew, ViewerCommand):
    """
    Commande d'interface utilisateur pour créer une nouvelle note avec
    les catégories sélectionnées.

    Cette classe est une extension de la classe `NoteNew`.
    Elle crée une nouvelle note en utilisant les catégories actuellement
    sélectionnées dans la visionneuse.

    Attributes :
        menuText (str) : Texte du menu contextuel ("New note with selected categories...")
        helpText (str) : Texte d'aide pour la commande.
    """

    menuText = _("New &note with selected categories...")
    helpText = _("Insert a new note with the selected categories checked")

    def enabled(self, event):
        return super().enabled(event) and bool(
            self.viewer.curselection(forceUpdate=True)
        )

    def categoriesForTheNewNote(self):
        """
        Retourne les catégories sélectionnées dans la visionneuse.

        Cette méthode est une surcharge de la méthode héritée de `NoteNew`.
        Elle retourne les catégories sélectionnées dans la visionneuse
        plutôt que d'utiliser les catégories filtrées de la tâche.

        Returns :
            Une liste des catégories sélectionnées dans la visionneuse.
        """
        return self.viewer.curselection()


class NoteDragAndDrop(OrderingDragAndDropCommand, NotesCommand):
    """
    Commande de gestion du glisser-déposer pour les notes.

    Cette classe permet de réorganiser les notes par glisser-déposer.
    Elle utilise la commande `DragAndDropNoteCommand` pour effectuer
    l'opération de réorganisation.

    Elle hérite de deux classes :
     - `OrderingDragAndDropCommand` : Fournit les fonctionnalités de base
       pour le glisser-déposer avec réorganisation.
     - `NotesCommand` : Permet d'accéder aux informations et aux
       fonctionnalités liées aux notes.

    Attributes :
        # Héritées de OrderingDragAndDropCommand
        # ... (attributs de OrderingDragAndDropCommand)
        # Héritées de NotesCommand
        # ... (attributs de NotesCommand)
    """

    def createCommand(
        self, dropItem, dragItems, part, column, isTree, dropColumn=-1
    ):
        """
        Crée une commande `DragAndDropNoteCommand` pour effectuer
        l'opération de réorganisation de note.

        Args :
            dropItem : L'élément de note sur lequel on dépose.
            dragItems : Les éléments de note à déplacer.
            part : La partie de la liste des notes concernée (par ex.,
                   toutes les notes, celles d'une tâche spécifique).
            column : La colonne de la liste des notes concernée
                   (pas utilisé pour les notes).
            isTree : Indique s'il s'agit d'un glisser-déposer d'arborescence
                   (pas applicable pour les notes).
        """
        return command.DragAndDropNoteCommand(
            self.notes,
            dragItems,
            drop=[dropItem],
            part=part,
            column=column,
            isTree=isTree,
            dropColumn=dropColumn,
        )


class AttachmentNew(
    AttachmentsCommand, ViewerCommand, settings_uicommand.SettingsCommand
):
    """
    Commande d'interface utilisateur pour créer une nouvelle pièce jointe.

    Cette classe permet de créer une nouvelle pièce jointe via une fenêtre de
    dialogue. Le texte du menu et l'aide contextuelle sont récupérés
    automatiquement à partir de la classe `AttachmentsCommand`.

    Attributes :
        bitmap (str) : Chemin vers l'icône de la commande (facultatif).
        # Héritées de AttachmentsCommand et ViewerCommand
        # ... (attributs de AttachmentsCommand et ViewerCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande en récupérant le texte du menu et l'aide
        contextuelle à partir de la classe `AttachmentsCommand`.

        Args :
            *args : Arguments supplémentaires passés au constructeur parent.
            **kwargs : Arguments supplémentaires passés au constructeur parent.
        """
        attachments = kwargs["attachments"]
        if "menuText" not in kwargs:
            kwargs["menuText"] = attachments.newItemMenuText
            kwargs["helpText"] = attachments.newItemHelpText
        super().__init__(bitmap="new", *args, **kwargs)

    def doCommand(self, event, show=True):  # pylint: disable=W0221
        """
        Ouvre une fenêtre de dialogue pour la création d'une nouvelle
        pièce jointe et l'affiche.

        Args :
            event : L'événement déclenchant la commande (peut être None).
            show : Indique si la fenêtre de dialogue doit être affichée
                  immédiatement (utilisé pour les tests).

        Returns :
            La fenêtre de dialogue pour la création d'une pièce jointe.
        """
        attachmentDialog = self.viewer.newItemDialog(bitmap=self.bitmap)
        attachmentDialog.Show(show)
        return attachmentDialog  # à des fins de tests


class AddAttachment(
    mixin_uicommand.NeedsSelectedAttachmentOwnersMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour ajouter une pièce jointe
    sélectionnée depuis le système de fichiers.

    Cette classe permet de sélectionner un fichier sur le système
    de fichiers et de l'ajouter comme pièce jointe aux éléments sélectionnés
    dans la visionneuse.

    Attributes :
        menuText (str) : Texte du menu contextuel ("Add attachment...\tShift-Ctrl-A").
        helpText (str) : Texte d'aide pour la commande.
        bitmap (str) : Chemin vers l'icône de la commande ("paperclip_icon").
        # Héritées de NeedsSelectedAttachmentOwnersMixin, ViewerCommand et SettingsCommand
        # ... (attributs hérités)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser la commande en définissant le texte du menu, l'aide
        contextuelle, l'icône et d'autres paramètres.

        Args :
            *args : Arguments supplémentaires passés au constructeur parent.
            **kwargs : Arguments supplémentaires passés au constructeur parent.
        """
        super().__init__(
            menuText=_("&Add attachment...\tShift+Ctrl+A"),
            helpText=help.addAttachment,
            bitmap="paperclip_icon",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Ouvre un sélecteur de fichiers pour choisir une pièce jointe
        à ajouter et l'ajoute aux éléments sélectionnés dans la visionneuse.

        Args :
            event : L'événement déclenchant la commande.
        """
        print(
            f"uicommand.AddAttachment.doCommand : 📌 [DEBUG] Ajout d’un attachement : {attachment}"
        )
        filename = widgets.AttachmentSelector()
        if not filename:
            return
        attachmentBase = self.settings.get("file", "attachmentbase")
        if attachmentBase:
            filename = attachment.getRelativePath(filename, attachmentBase)
        addAttachmentCommand = command.AddAttachmentCommand(
            self.viewer.presentation(),
            self.viewer.curselection(),
            attachments=[attachment.FileAttachment(filename)],
        )
        addAttachmentCommand.do()


def openAttachments(attachments, settings, showerror):
    """
    Ouvre une liste de pièces jointes.

    Cette fonction ouvre une par une les pièces jointes fournies dans la liste.
    Elle utilise le chemin de base des pièces jointes stocké dans les paramètres
    pour construire le chemin complet du fichier à ouvrir. En cas d'erreur
    d'ouverture, un message d'erreur est affiché à l'utilisateur.

    Args :
        attachments (list) : Une liste d'objets `Attachment`.
        settings (dict) : Dictionnaire contenant les paramètres de l'application.
        showerror (func) : Fonction utilisée pour afficher les messages d'erreur.
    """
    attachmentBase = settings.get("file", "attachmentbase")
    for eachAttachment in attachments:
        try:
            log.debug(f"openAttachments essaie d'ouvrir {attachmentBase}.")
            eachAttachment.open(attachmentBase)
        except Exception as instance:  # pylint: disable=W0703
            showerror(
                render.exception(Exception, instance),
                caption=_("Error opening attachment"),
                style=wx.ICON_ERROR,
            )


class AttachmentOpen(
    mixin_uicommand.NeedsSelectedAttachmentsMixin,
    ViewerCommand,
    AttachmentsCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour ouvrir les pièces jointes
    sélectionnées.

    Cette classe permet d'ouvrir les pièces jointes des éléments actuellement
    sélectionnés dans la visionneuse. Elle utilise la fonction `openAttachments`
    pour effectuer l'ouverture.

    Attributes :
        bitmap (str) : Chemin vers l'icône de la commande ("fileopen").
        menuText (str) : Texte du menu contextuel (défini par la classe `AttachmentsCommand`).
        helpText (str) : Texte d'aide pour la commande (défini par la classe `AttachmentsCommand`).
        # Héritées de NeedsSelectedAttachmentsMixin, ViewerCommand, AttachmentsCommand et SettingsCommand
        # ... (attributs hérités)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande en récupérant le texte du menu et l'aide
        contextuelle à partir de la classe `AttachmentsCommand`.

        Args :
            *args : Arguments supplémentaires passés au constructeur parent.
            **kwargs : Arguments supplémentaires passés au constructeur parent.
        """
        attachments = kwargs["attachments"]
        super().__init__(
            bitmap="fileopen",
            menuText=attachments.openItemMenuText,
            helpText=attachments.openItemHelpText,
            *args,
            **kwargs,
        )

    def doCommand(
        self, event, showerror=wx.MessageBox
    ):  # pylint: disable=W0221
        """
        Ouvre les pièces jointes des éléments sélectionnés dans la visionneuse.

        Args :
            event : L'événement déclenchant la commande.
            showerror (func) : Fonction utilisée pour afficher les messages d'erreur.
        """
        openAttachments(self.viewer.curselection(), self.settings, showerror)


class OpenAllAttachments(
    mixin_uicommand.NeedsSelectionWithAttachmentsMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour ouvrir toutes les pièces jointes
    des éléments sélectionnés.

    Cette classe permet d'ouvrir toutes les pièces jointes présentes dans
    les éléments sélectionnés de la visionneuse. Elle collecte toutes les
    pièces jointes des éléments sélectionnés puis les ouvre à l'aide de
    la fonction `openAttachments`.

    Attributes :
        menuText (str) : Texte du menu contextuel ("Open all attachments...\tShift-Ctrl-O").
        helpText (str) : Texte d'aide pour la commande (défini par `help.openAllAttachments`).
        bitmap (str) : Chemin vers l'icône de la commande ("paperclip_icon").
       # Héritées de NeedsSelectedAttachmentsMixin, ViewerCommand, AttachmentsCommand et SettingsCommand
       # ... (attributs hérités)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande en définissant le texte du menu, l'aide
        contextuelle, l'icône et d'autres paramètres.

        Args :
            *args : Arguments supplémentaires passés au constructeur parent.
            **kwargs : Arguments supplémentaires passés au constructeur parent.
        """
        super().__init__(
            menuText=_("&Open all attachments...\tShift+Ctrl+O"),
            helpText=help.openAllAttachments,
            bitmap="paperclip_icon",
            *args,
            **kwargs,
        )

    def doCommand(
        self, event, showerror=wx.MessageBox
    ):  # pylint: disable=W0221
        """
        Ouvre toutes les pièces jointes des éléments sélectionnés dans la visionneuse.

        Args :
            event : L'événement déclenchant la commande.
            showerror (func) : Fonction utilisée pour afficher les messages d'erreur.
        """
        allAttachments = []
        for item in self.viewer.curselection():
            allAttachments.extend(item.attachments())
        openAttachments(allAttachments, self.settings, showerror)


class DialogCommand(base_uicommand.UICommand):
    """
    Commande d'interface utilisateur pour afficher une boîte de dialogue
    personnalisée.

    Cette classe permet d'afficher une boîte de dialogue HTML avec un titre,
    un texte et des options de personnalisation. La commande est désactivée
    tant que la boîte de dialogue précédente n'est pas fermée.

    Attributes :
        _dialogTitle (str) : Titre de la boîte de dialogue.
        _dialogText (str) : Texte HTML affiché dans la boîte de dialogue.
        _direction (wx.HORIZONTAL ou wx.VERTICAL, optionnel) :
            Direction de l'alignement du contenu. Par défaut, None (horizontal).
        closed (bool) : Indique si la boîte de dialogue précédente est fermée
                       (True) ou ouverte (False).
        bitmap (str, optionnel) : Chemin vers l'icône de la commande.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande en stockant les paramètres de la boîte de dialogue.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent :
                - dialogTitle (str) : Titre de la boîte de dialogue.
                - dialogText (str) : Texte HTML affiché dans la boîte de dialogue.
                - direction (wx.HORIZONTAL ou wx.VERTICAL, optionnel) :
                    Direction de l'alignement du contenu (par défaut, None).
                - bitmap (str, optionnel) : Chemin vers l'icône de la commande.
        """
        self._dialogTitle = kwargs.pop("dialogTitle")
        self._dialogText = kwargs.pop("dialogText")
        self._direction = kwargs.pop("direction", None)
        self.closed = True
        self.dialog = None
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Affiche une boîte de dialogue HTML avec les paramètres stockés.

        Args :
            event : L'événement déclenchant la commande (peut être None).
        """
        self.closed = False
        # pylint: disable=W0201
        self.dialog = widgets.HTMLDialog(
            self._dialogTitle,
            self._dialogText,
            parent=wx.GetApp().GetTopWindow(),
            bitmap=self.bitmap,
            direction=self._direction,
        )  # TODO : Instance attribute dialog defined outside __init__ : pourquoi défini ici ?
        for event in wx.EVT_CLOSE, wx.EVT_BUTTON:
            self.dialog.Bind(event, self.onClose)
        # (lie les événements de fermeture et de bouton à la méthode onClose)
        self.dialog.Show()

    def onClose(self, event):
        """
        Gère la fermeture de la boîte de dialogue.

        - Met l'attribut 'closed' à True.
        - Détruit la fenêtre de dialogue.
        - Propage l'événement pour un traitement ultérieur (si nécessaire).

        Args :
            event : L'événement de fermeture ou de bouton de la boîte de dialogue.
        """
        self.closed = True
        self.dialog.Destroy()
        event.Skip()

    def enabled(self, event):
        """
        Indique si la commande est activée ou désactivée.

        La commande est activée uniquement si la boîte de dialogue précédente
        est fermée (attribut 'closed' est True).

        Args :
            event : L'événement déclenchant la vérification d'activation
                   (peut être None).

        Returns :
            bool : True si la commande est activée, False sinon.
        """
        return self.closed


class Help(DialogCommand):
    """
    Commande d'interface utilisateur pour afficher l'aide de l'application.

    Cette classe hérite de `DialogCommand` pour afficher une boîte de dialogue HTML
    contenant le contenu de l'aide de l'application. Le texte du menu et
    l'aide contextuelle sont définis en fonction du système d'exploitation
    utilisé (Mac OS X ou autre).

    Attributes :
        # Héritées de DialogCommand
        # ... (attributs de DialogCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la commande en définissant le texte du menu, l'aide
        contextuelle, les icônes et d'autres paramètres en fonction du système
        d'exploitation.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent.
        """
        if operating_system.isMac():
            # Utiliser le raccourci clavier par défaut pour Mac OS X :
            menuText = _("&Help contents\tCtrl+?")
        else:
            # Utilisez une lettre, car « Ctrl- ? » ne fonctionne pas sous Windows :
            menuText = _("&Help contents\tCtrl+H")
        super().__init__(
            menuText=menuText,
            helpText=help.help,
            bitmap="led_blue_questionmark_icon",
            dialogTitle=_("Help"),
            dialogText=help.helpHTML,
            id=wx.ID_HELP,
            *args,
            **kwargs,
        )


class Tips(settings_uicommand.SettingsCommand):
    """
    Commande d'interface utilisateur pour afficher des conseils d'utilisation.

    Cette classe permet d'afficher des conseils d'utilisation de l'application
    dans une fenêtre distincte.

    Attributes :
        menuText (str) : Texte du menu contextuel ("Tips").
        helpText (str) : Texte d'aide pour la commande ("Tips about the program").
        bitmap (str) : Chemin vers l'icône de la commande ("lamp_icon").
        # Héritées de SettingsCommand
        # ... (attributs de SettingsCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiset la commande en définissant le texte du menu, l'aide
        contextuelle et l'icône.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent.
        """
        super().__init__(
            menuText=_("&Tips"),
            helpText=_("Tips about the program"),
            bitmap="lamp_icon",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Affiche une fenêtre de conseils d'utilisation.

        Args :
            event : L'événement déclenchant la commande.
        """
        help.showTips(self.mainWindow(), self.settings)


class Anonymize(IOCommand):
    """
    Commande d'interface utilisateur pour anonymiser un fichier de tâche.

    Cette classe permet d'anonymiser un fichier de tâche afin de le joindre à
    un rapport de bogue. L'anonymisation supprime les informations sensibles
    contenues dans le fichier.

    Attributes :
        menuText (str) : Texte du menu contextuel ("Anonymize").
        helpText (str) : Texte d'aide pour la commande
                        ("Anonymize a task file to attach it to a bug report").
        # Héritées de IOCommand
        # ... (attributs de IOCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser la commande en définissant le texte du menu et l'aide
        contextuelle.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent.
        """
        super().__init__(
            menuText=_("Anonymize"),
            helpText=_("Anonymize a task file to attach it to a bug report"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Anonymise le fichier de tâche en cours et affiche un message de
        confirmation.

        Args :
            event : L'événement déclenchant la commande.
        """
        anonymized_filename = anonymize(self.iocontroller.filename())
        wx.MessageBox(
            _("Your task file has been anonymized and saved to:")
            + "\n"
            + anonymized_filename,
            _("Finished"),
            wx.OK,
        )

    def enabled(self, event):
        """
        Indique si la commande est activée ou désactivée.

        La commande est activée uniquement si un fichier de tâche est ouvert
        (vérifié par la méthode `filename` de l'IOController).

        Args :
            event : L'événement déclenchant la vérification d'activation
                   (peut être None).

        Returns :
            bool : True si la commande est activée, False sinon.
        """
        return bool(self.iocontroller.filename())


class HelpAbout(DialogCommand):
    """
    Commande d'interface utilisateur pour afficher la boîte de dialogue "À propos".

    Cette classe hérite de `DialogCommand` pour afficher une boîte de dialogue HTML
    contenant des informations sur l'application, telles que le nom, la version
    et les contacts.

    Attributes :
        # Héritées de DialogCommand
        # ... (attributs de DialogCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser la commande en définissant le texte du menu, l'aide
        contextuelle, le titre, le contenu HTML et d'autres paramètres
        en utilisant les informations de l'application.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent.
        """
        super().__init__(
            menuText=_("&About %s") % meta.name,
            helpText=_("Version and contact information about %s") % meta.name,
            dialogTitle=_("About %s") % meta.name,
            dialogText=help.aboutHTML,
            id=wx.ID_ABOUT,
            bitmap="led_blue_information_icon",
            *args,
            **kwargs,
        )


class HelpLicense(DialogCommand):
    """
    Commande d'interface utilisateur pour afficher la boîte de dialogue de licence.

    Cette classe hérite de `DialogCommand` pour afficher une boîte de dialogue HTML
    contenant la licence de l'application.

    Attributes :
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&License"),
            helpText=_("%s license") % meta.name,
            dialogTitle=_("%s license") % meta.name,
            dialogText=meta.licenseHTML,
            direction=wx.Layout_LeftToRight,
            bitmap="document_icon",
            *args,
            **kwargs,
        )


class CheckForUpdate(settings_uicommand.SettingsCommand):
    """
    Commande d'interface utilisateur pour rechercher une mise à jour.

    Cette classe permet de vérifier la disponibilité d'une nouvelle version
    de l'application. Elle utilise le vérificateur de version de la librairie
    `meta` et démarre la vérification en mode verbeux (affichage des messages).

    Attributes :
        menuText (str) : Texte du menu contextuel ("Check for update").
        helpText (str) : Texte d'aide pour la commande
                        ("Check for the availability of a new version of %s") % meta.name.
        bitmap (str) : Chemin vers l'icône de la commande ("box_icon").
        # Héritées de SettingsCommand
        # ... (attributs de SettingsCommand)
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser la commande en définissant le texte du menu, l'aide
        contextuelle et l'icône.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent.
        """
        super().__init__(
            menuText=_("Check for update"),
            helpText=_("Check for the availability of a new version of %s")
            % meta.name,
            bitmap="box_icon",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """
        Démarre la vérification de la mise à jour.

        Args :
            event : L'événement déclenchant la commande.
        """
        meta.VersionChecker(self.settings, verbose=True).start()


class URLCommand(base_uicommand.UICommand):
    """
    Commande d'interface utilisateur pour ouvrir une URL.

    Cette classe de base permet d'ouvrir une URL externe dans le navigateur
    web par défaut de l'utilisateur.

    Attributes :
        url (str) : URL à ouvrir.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialiser la commande en stockant l'URL et en appelant le
        constructeur parent.

        Args :
            *args : Arguments supplémentaires transmis au constructeur parent.
            **kwargs : Arguments supplémentaires transmis au constructeur parent :
                - url (str) : URL à ouvrir.
                - urlpo (str, optionnel) : Attribut non utilisé (probablement une erreur de frappe).
        """
        self.url = kwargs.pop("url")
        # self.url = kwargs.pop("urlpo")
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        """
        Ouvre l'URL dans le navigateur web par défaut.

        Args :
            event : L'événement déclenchant la commande.
        """
        try:
            openfile.openFile(self.url)
        except Exception as reason:
            wx.MessageBox(
                # _("Cannot open URL:\n%s") % reason,
                _("Cannot open URL:\n%s") % str(reason),
                caption=_("%s URL error") % meta.name,
                style=wx.ICON_ERROR,
            )


class FAQ(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de FAQ.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page de questions
    fréquentes de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de FAQ, définie dans `meta.faq_url`.

    **Méthodes :**
    - `__init__(self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        """Initialiser la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés."""
        super().__init__(
            menuText=_("&Frequently asked questions"),
            helpText=_("Browse the frequently asked questions and answers"),
            bitmap="led_blue_questionmark_icon",
            url=meta.faq_url,
            *args,
            **kwargs,
        )


class ReportBug(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de rapport de bug.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page de rapport
    de bug de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de rapport de bug, définie dans `meta.known_bugs_url`.

    **Méthodes :**
    - `__init__(self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        """Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés."""
        super().__init__(
            menuText=_("Report a &bug..."),
            helpText=_("Report a bug or browse known bugs"),
            bitmap="bug_icon",
            url=meta.known_bugs_url,
            *args,
            **kwargs,
        )


class RequestFeature(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de demande de fonctionnalité.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page de demande
    de fonctionnalité de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de demande de fonctionnalité, définie dans `meta.feature_request_url`.

    **Méthodes :**
    - `__init__(self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        """Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés."""
        super().__init__(
            menuText=_("Request a &feature..."),
            helpText=_("Request a new feature or vote for existing requests"),
            bitmap="cogwheel_icon",
            url=meta.feature_request_url,
            *args,
            **kwargs,
        )


class RequestSupport(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de demande de support.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page permettant
    de demander de l'aide aux développeurs de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de demande de support, définie dans `meta.support_request_url`.

    **Méthodes :**
    - `__init__ (self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Request &support..."),
            helpText=_("Request user support from the developers"),
            bitmap="life_ring_icon",
            url=meta.support_request_url,
            *args,
            **kwargs,
        )


class HelpTranslate(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de contribution à la traduction.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page permettant
    de contribuer à la traduction de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de contribution à la traduction, définie dans `meta.translations_url`.

    **Méthodes :**
    - `__init__ (self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Help improve &translations..."),
            helpText=_("Help improve the translations of %s") % meta.name,
            bitmap="person_talking_icon",
            url=meta.translations_url,
            *args,
            **kwargs,
        )


class CheckForUpdate(URLCommand):
    def __init__(self, *args, **kwargs):
        # Remove settings from kwargs if present (not needed for URLCommand)
        kwargs.pop("settings", None)
        super().__init__(
            menuText=_("Check for update"),
            helpText=_("Check for the availability of a new version of %s")
            % meta.name,
            bitmap="box_icon",
            url=meta.github_url,
            *args,
            **kwargs,
        )


class Donate(URLCommand):
    """
    Commande d'interface utilisateur pour ouvrir la page de don.

    Cette classe hérite de `URLCommand` et est spécialisée pour ouvrir la page permettant
    de faire un don pour soutenir le développement de l'application.

    **Attributs :**
    - `url` (str) : L'URL de la page de don, définie dans `meta.donate_url`.

    **Méthodes :**
    - `__init__ (self, *args, **kwargs)` : Initialise la commande avec le texte du menu,
        l'aide contextuelle et l'icône appropriés.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Donate..."),
            helpText=_("Donate to support the development of %s") % meta.name,
            bitmap="heart_icon",
            url=meta.donate_url,
            *args,
            **kwargs,
        )


class MainWindowRestore(base_uicommand.UICommand):
    """
    Commande d'interface utilisateur pour restaurer la fenêtre principale.

    Cette classe permet de créer une commande qui, lorsqu'exécutée, restaure la fenêtre
    principale de l'application à son état précédent (taille et position).

    **Méthodes :**
    - `doCommand (self, event)` : Restaure la fenêtre principale.
    - `mainWindow (self)` (méthode interne) : Renvoie la référence à la fenêtre principale.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Restore"),
            helpText=_("Restore the window to its previous state"),
            bitmap="restore",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """Restaure la fenêtre principale."""
        self.mainWindow().restore(event)


class ResetWindowLayout(base_uicommand.UICommand):
    """Reset the window layout (AUI panes) to default positions."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("Reset &window layout"),
            helpText=_("Reset all panes to their default positions"),
            bitmap="reset",
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.mainWindow().resetWindowLayout()


class Search(ViewerCommand, settings_uicommand.SettingsCommand):
    # Search can only be attached to a real viewer, not to a viewercontainer
    """
    Commande d'interface utilisateur pour la recherche dans la vue.

    Cette classe permet d'ajouter un contrôle de recherche à la barre d'outils de la vue,
    et de gérer les événements liés à la recherche, tels que la saisie de texte, la modification
    des options de recherche et la navigation dans les résultats.

    **Attributs :**
    - `searchControl` : Le contrôle de recherche ajouté à la barre d'outils.
    - `__bound` : Indique si le contrôle de recherche est lié à la vue.

    **Méthodes :**
    - `onFind (searchString, matchCase, includeSubItems, searchDescription, regularExpression)` :
        Met à jour le filtre de recherche de la vue avec les paramètres spécifiés.
    - `appendToToolBar (toolbar)` : Ajoute le contrôle de recherche à la barre d'outils,
        lie les événements clavier appropriés et initialise le contrôle avec les paramètres
        de recherche courants.
    - `bindKeyDownInViewer (self)` : Lie l'événement `wx.EVT_KEY_DOWN` à la méthode `onViewerKeyDown`
        pour détecter la combinaison de touches Ctrl+F.
    - `bindKeyDownInSearchCtrl (self)` : Lie l'événement `wx.EVT_KEY_DOWN` au contrôle de recherche
        pour détecter les touches Escape et Ctrl+Flèche Bas.
    - `unbind (self, window, id_)` : Détache les liaisons d'événements du contrôle de recherche.
    - `onViewerKeyDown (self, event)` : Gère l'événement `wx.EVT_KEY_DOWN` sur la vue pour
        détecter la combinaison de touches Ctrl+F et déplacer le focus vers le contrôle de recherche.
    - `onSearchCtrlKeyDown (self, event)` : Gère l'événement `wx.EVT_KEY_DOWN` sur le contrôle de recherche
        pour détecter les touches Escape et Ctrl+Flèche Bas et effectuer les actions appropriées.
    - `doCommand (self, event)` : Cette méthode n'est pas utilisée dans cette classe.
    """

    def __init__(self, *args, **kwargs):
        self.searchControl = None
        self.__bound = False
        super().__init__(*args, helpText=_("Search"), **kwargs)
        assert self.viewer.isSearchable()

    def onFind(
        self,
        searchString,
        matchCase,
        includeSubItems,
        searchDescription,
        regularExpression,
    ):
        """Met à jour le filtre de recherche de la vue avec les paramètres spécifiés."""
        if self.__bound:
            self.viewer.setSearchFilter(
                searchString,
                matchCase,
                includeSubItems,
                searchDescription,
                regularExpression,
            )

    def appendToToolBar(self, toolbar):
        """Ajoute le contrôle de recherche à la barre d'outils,
        lie les événements clavier appropriés et initialise le contrôle avec les paramètres
        de recherche courants."""
        self.__bound = True
        (
            searchString,
            matchCase,
            includeSubItems,
            searchDescription,
            regularExpression,
        ) = self.viewer.getSearchFilter()
        # pylint: disable=W0201
        self.searchControl = widgets.SearchCtrl(
            toolbar,
            value=searchString,
            style=wx.TE_PROCESS_ENTER,
            matchCase=matchCase,
            includeSubItems=includeSubItems,
            searchDescription=searchDescription,
            regularExpression=regularExpression,
            callback=self.onFind,
        )
        # Set minimum size to ensure the text input is visible in AUI toolbars
        # that use AUI_TB_NO_AUTORESIZE flag
        self.searchControl.SetMinSize((150, -1))
        toolbar.AddControl(self.searchControl)
        self.bindKeyDownInViewer()
        self.bindKeyDownInSearchCtrl()

    def bindKeyDownInViewer(self):
        """Lie l'événement `wx.EVT_KEY_DOWN` à la méthode `onViewerKeyDown`
        pour détecter la combinaison de touches Ctrl+F.

        Bind wx.EVT_KEY_DOWN to self.onViewerKeyDown so we can catch
        Ctrl-F."""
        widget = self.viewer.getWidget()
        try:
            window = widget.GetMainWindow()
        except AttributeError:
            window = widget
        window.Bind(wx.EVT_KEY_DOWN, self.onViewerKeyDown)

    def bindKeyDownInSearchCtrl(self):
        """Lie l'événement `wx.EVT_KEY_DOWN` au contrôle de recherche
        pour détecter les touches Escape et Ctrl+Flèche Bas.

        Bind wx.EVT_KEY_DOWN to self.onSearchCtrlKeyDown so we can catch
        the Escape key and drop down the menu on Ctrl-Down."""
        self.searchControl.getTextCtrl().Bind(
            wx.EVT_KEY_DOWN, self.onSearchCtrlKeyDown
        )

    def unbind(self, window, id_):
        """Détache les liaisons d'événements du contrôle de recherche."""
        self.__bound = False
        if hasattr(self, "searchControl") and self.searchControl:
            self.searchControl.cleanup()
        super().unbind(window, id_)

    def onViewerKeyDown(self, event):
        """Gère l'événement `wx.EVT_KEY_DOWN` sur la vue pour
        détecter la combinaison de touches Ctrl+F et déplacer le focus vers le contrôle de recherche.

        On Ctrl-F, move focus to the search control."""
        if (
            event.KeyCode == ord("F")
            and event.CmdDown()
            and not event.AltDown()
        ):
            self.searchControl.SetFocus()
        else:
            event.Skip()

    def onSearchCtrlKeyDown(self, event):
        """Gère l'événement `wx.EVT_KEY_DOWN` sur le contrôle de recherche
        pour détecter les touches Escape et Ctrl+Flèche Bas et effectuer les actions appropriées.

        On Escape, move focus to the viewer, on Ctrl-Down popup the
        menu."""
        if event.KeyCode == wx.WXK_ESCAPE:
            self.viewer.SetFocus()
        elif event.KeyCode == wx.WXK_DOWN and event.AltDown():
            self.searchControl.PopupMenu()
        else:
            event.Skip()

    def doCommand(self, event):
        """
        Cette méthode n'est pas utilisée dans cette classe.
        """
        pass  # non utilisé


class ToolbarChoiceCommandMixin(object):
    """
    Mixin pour ajouter un contrôle de choix à une barre d'outils.

    Ce mixin fournit des fonctionnalités pour ajouter un contrôle de choix à une barre d'outils
    et gérer les événements liés aux sélections.

    **Attribut :**
    - `currentChoice` : L'indice de l'option actuellement sélectionnée.
    - `choiceCtrl` : Le contrôle de choix ajouté à la barre d'outils.

    **Méthodes :**
    - `appendToToolBar (toolbar)` : Ajoute le contrôle de choix à la barre d'outils spécifiée.
    - `unbind (window, id_)` : Détache les liaisons d'événements du contrôle de choix.
    - `onChoice (event)` : Gère l'événement de sélection d'une option dans le contrôle de choix.
    - `doChoice (choice)` : Méthode abstraite à implémenter dans les classes dérivées pour gérer
        l'action à effectuer en fonction de l'option sélectionnée.
    - `doCommand (event)` : Cette méthode n'est pas utilisée.
    - `setChoice (choice)` : Définit l'option sélectionnée programmatiquement.
    - `enable (enable=True)` : Active ou désactive le contrôle de choix.
    """

    def __init__(self, *args, **kwargs):
        self.currentChoice = None
        self.choiceCtrl = None
        super().__init__(*args, **kwargs)

    def appendToToolBar(self, toolbar):
        """Ajoutez notre contrôle de choix à la barre d’outils.

        Ajoute le contrôle de choix à la barre d'outils spécifiée."""
        # pylint: disable=W0201
        self.choiceCtrl = wx.Choice(toolbar, choices=self.choiceLabels)
        self.currentChoice = self.choiceCtrl.Selection
        self.choiceCtrl.Bind(wx.EVT_CHOICE, self.onChoice)
        toolbar.AddControl(self.choiceCtrl)

    def unbind(self, window, id_):
        """Détache les liaisons d'événements du contrôle de choix."""
        if self.choiceCtrl is not None:
            self.choiceCtrl.Unbind(wx.EVT_CHOICE)
            self.choiceCtrl = None
        super().unbind(window, id_)

    def onChoice(self, event):
        """Gère l'événement de sélection d'une option dans le contrôle de choix.

        L'utilisateur a sélectionné un choix dans le contrôle de choix."""
        choiceIndex = event.GetInt()
        if choiceIndex == self.currentChoice:
            return
        self.currentChoice = choiceIndex
        self.doChoice(self.choiceData[choiceIndex])

    def doChoice(self, choice):
        """Méthode abstraite à implémenter dans les classes dérivées pour gérer
        l'action à effectuer en fonction de l'option sélectionnée."""
        raise NotImplementedError  # pragma: no cover

    def doCommand(self, event):
        """Cette méthode n'est pas utilisée."""
        pass  # Non utilisée

    def setChoice(self, choice):
        """Définit l'option sélectionnée programmatiquement.

        Définit par le programme le choix actuel dans le contrôle de choix."""
        if self.choiceCtrl is not None:
            index = self.choiceData.index(choice)
            self.choiceCtrl.Selection = index
            self.currentChoice = index

    def enable(self, enable=True):
        """Active ou désactive le contrôle de choix."""
        if self.choiceCtrl is not None:
            self.choiceCtrl.Enable(enable)


class EffortViewerAggregationChoice(
    ToolbarChoiceCommandMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    """
    Commande d'interface utilisateur pour choisir le mode d'agrégation des efforts.

    Cette classe permet de choisir le mode d'agrégation des efforts affichés dans la vue.
    Elle utilise un contrôle de choix pour sélectionner le mode d'agrégation souhaité.

    **Attributs :**
    - `choiceLabels` : Liste des labels pour les différentes options d'agrégation.
    - `choiceData` : Liste des valeurs correspondantes aux options d'agrégation.

    **Méthodes :**
    - `appendToToolBar (self, *args, **kwargs)` : Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction des paramètres enregistrés.
    - `doChoice (self, choice)` : Enregistre le choix d'agrégation dans les paramètres de l'application.
    - `on_setting_changed (self, value)` : Met à jour le choix dans le contrôle en fonction du paramètre enregistré.
    """

    choiceLabels = [
        _("Effort details"),
        _("Effort per day"),
        _("Effort per week"),
        _("Effort per month"),
    ]
    choiceData = ["details", "day", "week", "month"]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Aggregation mode"), **kwargs)

    def appendToToolBar(self, *args, **kwargs):
        """Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré."""
        super().appendToToolBar(*args, **kwargs)
        self.setChoice(
            self.settings.gettext(self.viewer.settingsSection(), "aggregation")
        )
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.aggregation" % self.viewer.settingsSection(),
        )

    def doChoice(self, choice):
        """Enregistre le choix d'agrégation dans les paramètres de l'application."""
        self.settings.settext(
            self.viewer.settingsSection(), "aggregation", choice
        )

    def on_setting_changed(self, value):
        """Met à jour le choix dans le contrôle en fonction du paramètre enregistré."""
        self.setChoice(value)


class EffortViewerAggregationOption(
    settings_uicommand.UIRadioCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour sélectionner une option d'agrégation des efforts.

    Cette classe permet de sélectionner une option d'agrégation des efforts dans un menu ou
    une boîte de dialogue. Elle utilise les paramètres de l'application pour déterminer
    l'état initial de l'option.

    **Méthodes :**
    - `isSettingChecked (self)` : Vérifie si l'option d'agrégation est actuellement sélectionnée.
    - `doCommand (self, event)` : Enregistre l'option d'agrégation dans les paramètres de l'application.
    """

    def isSettingChecked(self):
        """Vérifie si l'option d'agrégation est actuellement sélectionnée."""
        return (
            self.settings.gettext(self.viewer.settingsSection(), "aggregation")
            == self.value
        )

    def doCommand(self, event):
        """Enregistre l'option d'agrégation dans les paramètres de l'application."""
        self.settings.settext(
            self.viewer.settingsSection(), "aggregation", self.value
        )


class TaskViewerTreeOrListChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.UICheckCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour choisir le mode d'affichage des tâches.

    Cette classe permet de choisir entre l'affichage des tâches sous forme d'arborescence
    ou sous forme de liste. Elle utilise un contrôle de choix pour sélectionner le mode
    d'affichage souhaité.

    **Attributs :**
    - `choiceLabels` : Liste des labels pour les différentes options d'affichage.
    - `choiceData` : Liste des valeurs booléennes correspondantes aux options d'affichage.

    **Méthodes :**
    - `appendToToolBar (self, *args, **kwargs)` : Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction des paramètres enregistrés.
    - `doChoice (self, choice)` : Enregistre le choix d'affichage dans les paramètres de l'application.
    - `on_setting_changed (self, value)` : Met à jour le choix dans le contrôle en fonction du paramètre enregistré.
    """

    choiceLabels = [_("Tree"), _("List")]
    choiceData = [True, False]

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.choiceLabels[0],
            helpText=_(
                "When checked, show tasks as tree, "
                "otherwise show tasks as list"
            ),
            *args,
            **kwargs,
        )

    def appendToToolBar(self, *args, **kwargs):
        """Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré."""
        super().appendToToolBar(*args, **kwargs)
        self.setChoice(
            self.settings.getboolean(self.viewer.settingsSection(), "treemode")
        )
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.treemode" % self.viewer.settingsSection(),
        )
        # pub.subscribe(
        #     self.on_setting_changed,
        #     f"settings.{self.viewer.settingsSection()}.treemode",
        # )

    def doChoice(self, choice):
        """Enregistre le choix d'affichage dans les paramètres de l'application."""
        self.settings.setboolean(
            self.viewer.settingsSection(), "treemode", choice
        )

    def on_setting_changed(self, value):
        """Met à jour le choix dans le contrôle en fonction du paramètre enregistré."""
        self.setChoice(value)


class TaskViewerTreeOrListOption(
    settings_uicommand.UIRadioCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour sélectionner le mode d'affichage des tâches.

    Cette classe permet de sélectionner le mode d'affichage des tâches dans un menu ou
    une boîte de dialogue. Elle utilise les paramètres de l'application pour déterminer
    l'état initial de l'option.

    **Méthodes :**
    - `isSettingChecked (self)` : Vérifie si l'option d'affichage est actuellement sélectionnée.
    - `doCommand (self, event)` : Enregistre l'option d'affichage dans les paramètres de l'application.
    """

    def isSettingChecked(self):
        """Vérifie si l'option d'affichage est actuellement sélectionnée."""
        return (
            self.settings.getboolean(self.viewer.settingsSection(), "treemode")
            == self.value
        )

    def doCommand(self, event):
        """Enregistre l'option d'affichage dans les paramètres de l'application."""
        self.settings.setboolean(
            self.viewer.settingsSection(), "treemode", self.value
        )


class CategoryViewerFilterChoice(
    ToolbarChoiceCommandMixin, settings_uicommand.UICheckCommand
):
    """
    Commande d'interface utilisateur pour choisir le mode de filtrage des catégories.

    Cette classe permet de choisir entre deux modes de filtrage des catégories :
    - Filtrer sur toutes les catégories sélectionnées
    - Filtrer sur n'importe quelle catégorie sélectionnée

    Elle utilise un contrôle de choix pour sélectionner le mode de filtrage souhaité.

    **Attributs :**
    - `choiceLabels` : Liste des labels pour les différentes options d'filtrage.
    - `choiceData` : Liste des valeurs booléennes correspondantes aux options de filtrage.

    **Méthodes :**
    - `appendToToolBar (self, *args, **kwargs)` : Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré.
    - `isSettingChecked (self)` : Vérifie si le mode de filtrage "toutes les catégories" est sélectionné.
    - `doChoice (self, choice)` : Enregistre le mode de filtrage dans les paramètres de l'application.
    - `doCommand (self, event)` : Enregistre le mode de filtrage en fonction de l'état de la case à cocher.
    - `on_setting_changed (self, value)` : Met à jour le choix dans le contrôle en fonction du paramètre enregistré.
    """

    choiceLabels = [
        _("Filter on all checked categories"),
        _("Filter on any checked category"),
    ]
    choiceData = [True, False]

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.choiceLabels[0],
            helpText=_(
                "When checked, filter on all checked categories, "
                "otherwise on any checked category"
            ),
            *args,
            **kwargs,
        )

    def appendToToolBar(self, *args, **kwargs):
        """Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré."""
        super().appendToToolBar(*args, **kwargs)
        pub.subscribe(
            self.on_setting_changed, "settings.view.categoryfiltermatchall"
        )

    def isSettingChecked(self):
        """Vérifie si le mode de filtrage "toutes les catégories" est sélectionné."""
        return self.settings.getboolean("view", "categoryfiltermatchall")

    def doChoice(self, choice):
        """Enregistre le mode de filtrage dans les paramètres de l'application."""
        self.settings.setboolean("view", "categoryfiltermatchall", choice)

    def doCommand(self, event):
        """Enregistre le mode de filtrage en fonction de l'état de la case à cocher."""
        self.settings.setboolean(
            "view", "categoryfiltermatchall", self._isMenuItemChecked(event)
        )

    def on_setting_changed(self, value):
        """Met à jour le choix dans le contrôle en fonction du paramètre enregistré."""
        self.setChoice(value)


class SquareTaskViewerOrderChoice(
    ToolbarChoiceCommandMixin,
    settings_uicommand.SettingsCommand,
    ViewerCommand,
):
    """
    Commande d'interface utilisateur pour choisir le critère de tri des tâches.

    Cette classe permet de choisir le critère de tri des tâches dans la vue.
    Elle utilise un contrôle de choix pour sélectionner le critère de tri souhaité.

    **Attributs :**
    - `choiceLabels` : Liste des labels pour les différents critères de tri.
    - `choiceData` : Liste des valeurs correspondantes aux critères de tri.

    **Méthodes :**
    - `appendToToolBar (self, *args, **kwargs)` : Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré.
    - `doChoice (self, choice)` : Enregistre le critère de tri dans les paramètres de l'application.
    - `on_setting_changed (self, value)` : Met à jour le choix dans le contrôle en fonction du paramètre enregistré.
    """

    choiceLabels = [
        _("Budget"),
        _("Time spent"),
        _("Fixed fee"),
        _("Revenue"),
        _("Priority"),
    ]
    choiceData = ["budget", "timeSpent", "fixedFee", "revenue", "priority"]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Order choice"), **kwargs)

    def appendToToolBar(self, *args, **kwargs):
        """Ajoute le contrôle de choix à la barre d'outils
        et initialise la sélection en fonction du paramètre enregistré."""
        super().appendToToolBar(*args, **kwargs)
        pub.subscribe(
            self.on_setting_changed,
            "settings.%s.sortby" % self.viewer.settingsSection(),
        )
        # pub.subscribe(
        #     self.on_setting_changed,
        #     f"settings.{self.viewer.settingsSection()}.sortby",
        # )

    def doChoice(self, choice):
        """Enregistre le critère de tri dans les paramètres de l'application."""
        self.settings.settext(self.viewer.settingsSection(), "sortby", choice)

    def on_setting_changed(self, value):
        """Met à jour le choix dans le contrôle en fonction du paramètre enregistré."""
        self.setChoice(value)


class SquareTaskViewerOrderByOption(
    settings_uicommand.UIRadioCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour sélectionner le critère de tri des tâches.

    Cette classe permet de sélectionner le critère de tri des tâches dans un menu ou
    une boîte de dialogue. Elle utilise les paramètres de l'application pour déterminer
    l'état initial de l'option.

    **Méthodes :**
    - `isSettingChecked (self)` : Vérifie si l'option de tri est actuellement sélectionnée.
    - `doCommand (self, event)` : Enregistre le critère de tri dans les paramètres de l'application.
    """

    def isSettingChecked(self):
        """Vérifie si l'option de tri est actuellement sélectionnée."""
        return (
            self.settings.gettext(self.viewer.settingsSection(), "sortby")
            == self.value
        )

    def doCommand(self, event):
        """Enregistre le critère de tri dans les paramètres de l'application."""
        self.settings.settext(
            self.viewer.settingsSection(), "sortby", self.value
        )


class CalendarViewerConfigure(ViewerCommand):
    """
    Commande d'interface utilisateur pour configurer l'affichage du calendrier.

    Cette classe permet d'ouvrir une boîte de dialogue de configuration pour le
    calendrier.

    **Attributs :**
    - `menuText` : Texte affiché dans le menu.
    - `helpText` : Infobulle affichée au survol de la commande.
    - `bitmap` : Nom de l'icône associée à la commande.
    """

    menuText = _("&Configure")
    helpText = _("Configure the calendar viewer")
    bitmap = "wrench_icon"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.configure()


class HierarchicalCalendarViewerConfigure(CalendarViewerConfigure):
    helpText = _("Configure the hierarchical calendar viewer")


class CalendarViewerNavigationCommand(ViewerCommand):
    """
    Commande d'interface utilisateur pour la navigation dans le calendrier.

    Cette classe fournie une base pour les commandes de navigation dans le calendrier.
    Elle gèle temporairement l'affichage du calendrier pour éviter des conflits lors
    de la modification de la vue, puis appelle la méthode `SetViewType` du widget
    calendrier pour modifier la période affichée.

    **Attributs :**
    - `menuText` : Texte affiché dans le menu.
    - `helpText` : Infobulle affichée au survol de la commande.
    - `bitmap` : Nom de l'icône associée à la commande.
    - `calendarViewType` (Abstract) : Valeur à passer à la méthode `SetViewType`
        pour définir la période à afficher.

    **Méthodes :**
    - `doCommand (self, event)` : Gèle le calendrier, modifie la vue, puis le débloque.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        """Gèle le calendrier, modifie la vue, puis le débloque."""
        self.viewer.freeze()
        try:
            self.viewer.SetViewType(
                self.calendarViewType
            )  # pylint: disable=E1101
        finally:
            self.viewer.thaw()


# **Concrete Navigation Classes**
#
# Ces classes fournissent des fonctionnalités spécifiques pour naviguer dans le calendrier :
class CalendarViewerNextPeriod(CalendarViewerNavigationCommand):
    """
    Commande d'interface utilisateur pour afficher la période suivante.

    Cette classe permet d'afficher la période suivante dans le calendrier.
    """

    menuText = _("&Next period")
    helpText = _("Show next period")
    bitmap = "next"
    calendarViewType = wxSCHEDULER_NEXT


# **3. HierarchicalCalendarViewer Classes**
#
# Ces classes sont spécifiques aux visionneuses de calendrier hiérarchiques et
# peuvent implémenter la navigation différemment.
#
# ### Classe `HierarchicalCalendarViewerConfigure` (hérite de `CalendarViewerConfigure`)
#
# Ceci la classe hérite de `CalendarViewerConfigure` et ajoute potentiellement des fonctionnalités spécifiques à la configuration hiérarchique du calendrier.
#
# ### Classes `HierarchicalCalendarViewerNextPeriod`, `HierarchicalCalendarViewerPreviousPeriod` et `HierarchicalCalendarViewerToday`
#
# Ces classes peuvent ne pas hériter de `CalendarViewerNavigationCommand` et implémenter leur propre logique de navigation spécifique aux calendriers hiérarchiques.
#
# **Remarques :**
#
# - L'attribut `calendarViewType` dans `CalendarViewerNavigationCommand` est marqué comme abstrait car il doit être défini par des sous-classes avec une valeur spécifique des constantes `wxSCHEDULER_XXX`.
# - L'implémentation de la navigation pour `HierarchicalCalendarViewerToday` peut différer et pourrait appeler directement une méthode sur le attribut `widget` au lieu d'utiliser `SetViewType`.
class HierarchicalCalendarViewerNextPeriod(ViewerCommand):
    menuText = _("&Next period")
    helpText = _("Show next period")
    bitmap = "next"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.widget.Next()


class CalendarViewerPreviousPeriod(CalendarViewerNavigationCommand):
    """
    Commande d'interface utilisateur pour afficher la période précédente.

    Cette classe permet d'afficher la période précédente dans le calendrier.
    """

    menuText = _("&Previous period")
    helpText = _("Show previous period")
    bitmap = "prev"
    calendarViewType = wxSCHEDULER_PREV


class HierarchicalCalendarViewerPreviousPeriod(ViewerCommand):
    menuText = _("&Previous period")
    helpText = _("Show previous period")
    bitmap = "prev"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.widget.Prev()


class CalendarViewerToday(CalendarViewerNavigationCommand):
    """
    Commande d'interface utilisateur pour afficher la vue "Aujourd'hui".

    Cette classe permet d'afficher la vue "Aujourd'hui" dans le calendrier.
    """

    menuText = _("&Today")
    helpText = _("Show today")
    bitmap = "calendar_icon"
    calendarViewType = wxSCHEDULER_TODAY


class HierarchicalCalendarViewerToday(ViewerCommand):
    menuText = _("&Today")
    helpText = _("Show today")
    bitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=self.menuText,
            helpText=self.helpText,
            bitmap=self.bitmap,
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        self.viewer.widget.Today()  # Today or Today ?


class ToggleAutoColumnResizing(
    settings_uicommand.UICheckCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour activer/désactiver le redimensionnement automatique des colonnes.

    Cette classe permet de contrôler le redimensionnement automatique des colonnes dans la vue.
    Elle utilise un contrôle de type case à cocher pour activer ou désactiver cette fonctionnalité.

    **Méthodes :**
    - `updateWidget()` : Met à jour l'état du redimensionnement automatique dans le widget de la vue.
    - `isSettingChecked()` : Vérifie si le redimensionnement automatique est actuellement activé.
    - `doCommand (self, event)` : Enregistre l'état du redimensionnement automatique dans les paramètres de l'application et met à jour le widget.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            menuText=_("&Automatic column resizing"),
            helpText=_(
                "When checked, automatically resize columns to fill"
                " available space"
            ),
            *args,
            **kwargs,
        )
        wx.CallAfter(self.updateWidget)

    def updateWidget(self):
        """Met à jour l'état du redimensionnement automatique dans le widget de la vue."""
        # self.viewer.getWidget().ToggleAutoResizing(self.isSettingChecked())
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction
        try:
            widget = self.viewer.getWidget()
            if widget:
                widget.ToggleAutoResizing(self.isSettingChecked())
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def isSettingChecked(self):
        """Vérifie si le redimensionnement automatique est actuellement activé."""
        return self.settings.getboolean(
            self.viewer.settingsSection(), "columnautoresizing"
        )

    def doCommand(self, event):
        """Enregistre l'état du redimensionnement automatique dans les paramètres de l'application et met à jour le widget."""
        self.settings.set(
            self.viewer.settingsSection(),
            "columnautoresizing",
            str(self._isMenuItemChecked(event)),
        )
        self.updateWidget()


class ViewerPieChartAngle(ViewerCommand, settings_uicommand.SettingsCommand):
    """
    Commande d'interface utilisateur pour régler l'angle du diagramme circulaire.

    Cette classe permet de régler l'angle du diagramme circulaire dans la vue à l'aide d'un curseur
    ajouté à la barre d'outils.

    **Attributs :**
    - `sliderCtrl` : Le contrôle de curseur ajouté à la barre d'outils.

    **Méthodes :**
    - `appendToToolBar (self, toolbar)` : Ajoute le contrôle de curseur à la barre d'outils spécifiée
        et initialise sa valeur en fonction des paramètres enregistrés.
    - `unbind (self, window, itemId)` : Détache les liaisons d'événements du contrôle de curseur.
    - `onSlider (self, event)` : Gère l'événement de changement de valeur du curseur et enregistre
        la nouvelle valeur dans les paramètres de l'application.
    - `getCurrentAngle()` : Récupère l'angle actuel enregistré dans les paramètres de l'application.
    - `setCurrentAngle()` : Enregistre la valeur actuelle du curseur dans les paramètres de l'application.
    """

    def __init__(self, *args, **kwargs):
        self.sliderCtrl = None
        super().__init__(helpText=_("Set pie chart angle"), *args, **kwargs)

    def appendToToolBar(self, toolbar):
        """Ajoute notre contrôle de curseur à la barre d’outils.

        Ajoute le contrôle de curseur à la barre d'outils spécifiée
        et initialise sa valeur en fonction des paramètres enregistrés."""
        # pylint: disable=W0201
        self.sliderCtrl = wx.Slider(
            toolbar,
            minValue=0,
            maxValue=90,
            value=self.getCurrentAngle(),
            size=(120, -1),
        )
        self.sliderCtrl.Bind(wx.EVT_SLIDER, self.onSlider)
        toolbar.AddControl(self.sliderCtrl)

    def unbind(self, window, itemId):
        """Détache les liaisons d'événements du contrôle de curseur."""
        if self.sliderCtrl is not None:
            self.sliderCtrl.Unbind(wx.EVT_SLIDER)
            self.sliderCtrl = None
        super().unbind(window, itemId)

    def onSlider(self, event):
        """L'utilisateur a choisi un nouvel angle.

        Gère l'événement de changement de valeur du curseur et enregistre
        la nouvelle valeur dans les paramètres de l'application."""
        event.Skip()
        self.setCurrentAngle()

    def doCommand(self, event):
        pass  # Not used

    def getCurrentAngle(self):
        """Récupère l'angle actuel enregistré dans les paramètres de l'application."""
        return self.settings.getint(
            self.viewer.settingsSection(), "piechartangle"
        )

    def setCurrentAngle(self):
        """Enregistre la valeur actuelle du curseur dans les paramètres de l'application."""
        if self.sliderCtrl is not None:
            self.settings.setint(
                self.viewer.settingsSection(),
                "piechartangle",
                self.sliderCtrl.GetValue(),
            )


class RoundingPrecision(
    ToolbarChoiceCommandMixin,
    ViewerCommand,
    settings_uicommand.SettingsCommand,
):
    """
    Commande d'interface utilisateur pour choisir la précision d'arrondi.

    Cette classe permet de choisir la précision d'arrondi des durées affichées dans la vue.
    Elle utilise un contrôle de choix pour sélectionner la précision souhaitée.

    **Attributs :**
    - `roundingChoices` : Liste des options de précision en minutes.
    - `choiceData` : Liste des valeurs correspondantes en secondes.

    **Méthodes :**
    - `doChoice (self, choice)` : Enregistre la précision d'arrondi dans les paramètres de l'application.
    """

    roundingChoices = (0, 1, 3, 5, 6, 10, 15, 20, 30, 60)  # Minutes
    choiceData = [minutes * 60 for minutes in roundingChoices]  # Seconds
    # choiceLabels = [_('No rounding'), _('1 minute')] + [_('%d minutes') % minutes for minutes in roundingChoices[2:]]
    choiceLabels = [_("No rounding"), _("1 minute")] + [
        _("{} minutes".format(minutes for minutes in roundingChoices[2:]))
    ]
    # choiceLabels = [_("No rounding"), _("1 minute")] + [
    #     _(f"{minutes for minutes in roundingChoices[2:]} minutes")
    # ]

    def __init__(self, **kwargs):
        super().__init__(helpText=_("Rounding precision"), **kwargs)

    def doChoice(self, choice):
        """Enregistre la précision d'arrondi dans les paramètres de l'application."""
        self.settings.setint(self.viewer.settingsSection(), "round", choice)


class RoundBy(settings_uicommand.UIRadioCommand, ViewerCommand):
    """
    Commande d'interface utilisateur pour sélectionner une option d'arrondi.

    Cette classe permet de sélectionner une option d'arrondi parmi plusieurs choix.
    Elle utilise les paramètres de l'application pour déterminer l'option actuellement sélectionnée.

    **Méthodes :**
    - `isSettingChecked (self)` : Vérifie si l'option d'arrondi est actuellement sélectionnée.
    - `doCommand (self, event)` : Enregistre l'option d'arrondi dans les paramètres de l'application.
    """

    def isSettingChecked(self):
        """Vérifie si l'option d'arrondi est actuellement sélectionnée."""
        return (
            self.settings.getint(self.viewer.settingsSection(), "round")
            == self.value
        )

    def doCommand(self, event):
        """Enregistre l'option d'arrondi dans les paramètres de l'application."""
        self.settings.setint(
            self.viewer.settingsSection(), "round", self.value
        )


class AlwaysRoundUp(settings_uicommand.UICheckCommand, ViewerCommand):
    """
    Commande d'interface utilisateur pour activer/désactiver l'arrondi au supérieur.

    Cette classe permet d'activer ou désactiver l'arrondi au supérieur des durées.
    Elle utilise une case à cocher pour contrôler cette option.

    **Attributs :**
    - `checkboxCtrl` : Le contrôle de la case à cocher.

    **Méthodes :**
    - `appendToToolBar (self, toolbar)` : Ajoute la case à cocher à la barre d'outils.
    - `unbind (self, window, itemId)` : Détache les liaisons d'événements de la case à cocher.
    - `isSettingChecked ()` : Vérifie si l'arrondi au supérieur est activé.
    - `onCheck (self, event)` : Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application.
    - `doCommand (self, event)` : Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application.
    - `setSetting (self, alwaysRoundUp)` : Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application.
    - `setValue (self, value)` : Définit l'état de la case à cocher.
    - `enable (self, enable=True)` : Active ou désactive la case à cocher.
    """

    def __init__(self, *args, **kwargs):
        self.checkboxCtrl = None
        super().__init__(
            menuText=_("&Always round up"),
            helpText=_("Always round up to the next rounding increment"),
            *args,
            **kwargs,
        )

    def appendToToolBar(self, toolbar):
        """Ajoute la case à cocher à la barre d'outils.

        Ajoute un contrôle de case à cocher à la barre d’outils."""
        # pylint: disable=W0201
        self.checkboxCtrl = wx.CheckBox(toolbar, label=self.menuText)
        self.checkboxCtrl.Bind(wx.EVT_CHECKBOX, self.onCheck)
        toolbar.AddControl(self.checkboxCtrl)

    def unbind(self, window, itemId):
        """Détache les liaisons d'événements de la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Unbind(wx.EVT_CHECKBOX)
            self.checkboxCtrl = None
        super().unbind(window, itemId)

    def isSettingChecked(self):
        """Vérifie si l'arrondi au supérieur est activé."""
        return self.settings.getboolean(
            self.viewer.settingsSection(), "alwaysroundup"
        )

    def onCheck(self, event):
        """Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application."""
        self.setSetting(self._isMenuItemChecked(event))

    def doCommand(self, event):
        """Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application."""
        self.setSetting(self._isMenuItemChecked(event))

    def setSetting(self, alwaysRoundUp):
        """Enregistre l'état de l'arrondi au supérieur dans les paramètres de l'application."""
        self.settings.setboolean(
            self.viewer.settingsSection(), "alwaysroundup", alwaysRoundUp
        )

    def setValue(self, value):
        """Définit l'état de la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.SetValue(value)

    def enable(self, enable=True):
        """Active ou désactive la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Enable(enable)


class ConsolidateEffortsPerTask(
    settings_uicommand.UICheckCommand, ViewerCommand
):
    """
    Commande d'interface utilisateur pour activer/désactiver la consolidation des efforts par tâche.

    Cette classe permet de contrôler si les efforts pour une même tâche doivent être additionnés en un seul effort avant l'arrondi.
    Elle utilise une case à cocher pour activer ou désactiver cette option.

    **Attributs :**
    - `checkboxCtrl` : Le contrôle de la case à cocher.

    **Méthodes :**
    - `appendToToolBar (self, toolbar)` : Ajoute la case à cocher à la barre d'outils.
    - `unbind (self, window, itemId)` : Détache les liaisons d'événements de la case à cocher.
    - `isSettingChecked ()` : Vérifie si la consolidation des efforts est activée.
    - `onCheck (self, event)` : Enregistre l'état de la consolidation dans les paramètres de l'application.
    - `doCommand (self, event)` : Enregistre l'état de la consolidation dans les paramètres de l'application.
    - `setSetting (self, consolidateEffortsPerTask)` : Enregistre l'état de la consolidation dans les paramètres de l'application.
    - `setValue (self, value)` : Définit l'état de la case à cocher.
    - `enable (self, enable=True)` : Active ou désactive la case à cocher.
    """

    def __init__(self, *args, **kwargs):
        self.checkboxCtrl = None
        super().__init__(
            menuText=_("&Consolidate efforts per task"),
            helpText=_(
                "Consolidate all efforts per task to a single effort before rounding"
            ),
            *args,
            **kwargs,
        )

    def appendToToolBar(self, toolbar):
        """Ajoute la case à cocher à la barre d'outils.

        Ajoutez un contrôle de case à cocher à la barre d’outils."""
        # pylint: disable=W0201
        self.checkboxCtrl = wx.CheckBox(toolbar, label=self.menuText)
        self.checkboxCtrl.Bind(wx.EVT_CHECKBOX, self.onCheck)
        toolbar.AddControl(self.checkboxCtrl)

    def unbind(self, window, itemId):
        """Détache les liaisons d'événements de la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Unbind(wx.EVT_CHECKBOX)
            self.checkboxCtrl = None
        super().unbind(window, itemId)

    def isSettingChecked(self):
        """Vérifie si la consolidation des efforts est activée."""
        return self.settings.getboolean(
            self.viewer.settingsSection(), "consolidateeffortspertask"
        )

    def onCheck(self, event):
        """Enregistre l'état de la consolidation dans les paramètres de l'application."""
        self.setSetting(self._isMenuItemChecked(event))

    def doCommand(self, event):
        """Enregistre l'état de la consolidation dans les paramètres de l'application."""
        self.setSetting(self._isMenuItemChecked(event))

    def setSetting(self, consolidateEffortsPerTask):
        """Enregistre l'état de la consolidation dans les paramètres de l'application."""
        self.settings.setboolean(
            self.viewer.settingsSection(),
            "consolidateeffortspertask",
            consolidateEffortsPerTask,
        )

    def setValue(self, value):
        """Définit l'état de la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.SetValue(value)

    def enable(self, enable=True):
        """Active ou désactive la case à cocher."""
        if self.checkboxCtrl is not None:
            self.checkboxCtrl.Enable(enable)


class MoveViewerCommand(ViewerCommand):
    """
    Commande pour déplacer la visionneuse active vers une nouvelle position d'ancrage.
    """

    def __init__(self, *args, **kwargs):
        self.direction = kwargs.pop("direction")
        self.layer = kwargs.pop("layer", 0)
        super().__init__(*args, **kwargs)

    def doCommand(self, event):
        viewer = self.viewer.activeViewer()
        if viewer:
            # On doit accéder au manager AUI via la fenêtre principale
            manager = self.mainWindow().manager
            pane = manager.GetPane(viewer)
            if pane.IsOk():
                pane.Dock().Direction(self.direction).Layer(
                    self.layer
                ).Position(0)
                manager.Update()

    def enabled(self, event):
        return self.viewer.activeViewer() is not None


class MoveViewerLeft(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_LEFT
        super().__init__(
            menuText=_("Move viewer &Left"),
            helpText=_("Dock the current viewer to the left"),
            *args,
            **kwargs,
        )


class MoveViewerRight(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_RIGHT
        super().__init__(
            menuText=_("Move viewer &Right"),
            helpText=_("Dock the current viewer to the right"),
            *args,
            **kwargs,
        )


class MoveViewerTop(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_TOP
        super().__init__(
            menuText=_("Move viewer &Top"),
            helpText=_("Dock the current viewer to the top"),
            *args,
            **kwargs,
        )


class MoveViewerBottom(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_BOTTOM
        super().__init__(
            menuText=_("Move viewer &Bottom"),
            helpText=_("Dock the current viewer to the bottom"),
            *args,
            **kwargs,
        )


class MoveViewerLeftOuter(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_LEFT
        kwargs["layer"] = 1
        super().__init__(
            menuText=_("Move viewer &Left (Outer)"),
            helpText=_("Dock the current viewer to the far left"),
            *args,
            **kwargs,
        )


class MoveViewerRightOuter(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_RIGHT
        kwargs["layer"] = 1
        super().__init__(
            menuText=_("Move viewer &Right (Outer)"),
            helpText=_("Dock the current viewer to the far right"),
            *args,
            **kwargs,
        )


class MoveViewerTopOuter(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_TOP
        kwargs["layer"] = 1
        super().__init__(
            menuText=_("Move viewer &Top (Outer)"),
            helpText=_("Dock the current viewer to the far top"),
            *args,
            **kwargs,
        )


class MoveViewerBottomOuter(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_BOTTOM
        kwargs["layer"] = 1
        super().__init__(
            menuText=_("Move viewer &Bottom (Outer)"),
            helpText=_("Dock the current viewer to the far bottom"),
            *args,
            **kwargs,
        )


class MoveViewerCenter(MoveViewerCommand):
    def __init__(self, *args, **kwargs):
        kwargs["direction"] = aui.AUI_DOCK_CENTER
        super().__init__(
            menuText=_("Move viewer &Center"),
            helpText=_("Dock the current viewer to the center"),
            *args,
            **kwargs,
        )

    def doCommand(self, event):
        viewer = self.viewer.activeViewer()
        if viewer:
            manager = self.mainWindow().manager
            pane = manager.GetPane(viewer)
            if pane.IsOk():
                pane.CenterPane()
                manager.Update()
