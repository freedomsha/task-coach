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

# from builtins import range
# from builtins import str
# from taskcoachlib.tools import wxhelper
import wx

# import wxhelper
from taskcoachlib.i18n import _
from wx.lib import sized_controls, newevent

# from wx.lib import sized_controls
from taskcoachlib import meta, widgets


class ExportDialog(sized_controls.SizedDialog):
    """Classe de base pour tous les dialogues d'exportation.

    Utilisez les classes de contrôle ci-dessous pour ajouter des fonctionnalités.
    """

    title = "Override in subclass"
    section = "export"

    def __init__(self, *args, **kwargs):
        """Initialise la boîte de dialogue d'exportation,
        crée l'interface utilisateur et configure les boutons.
        """
        self.window = args[0]
        self.settings = kwargs.pop("settings")
        super().__init__(title=self.title, *args, **kwargs)
        pane = self.GetContentsPane()
        pane.SetSizerType("vertical")
        self.components = self.createInterior(pane)
        # buttonSizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        buttonSizer = wx.StdDialogButtonSizer()
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        buttonSizer.SetAffirmativeButton(okButton)
        # SetAffirmativeButton() sert à enregistrer un bouton créé explicitement ;
        # il ne le retourne pas. Le dialogue crée donc okButton,
        # l’enregistre avec SetAffirmativeButton(), puis lie directement
        # okButton.Bind(...).
        buttonSizer.SetCancelButton(cancelButton)
        buttonSizer.Realize()
        self.SetButtonSizer(buttonSizer)
        # buttonSizer.GetAffirmativeButton().Bind(wx.EVT_BUTTON, self.onOk)
        # # wxhelper.getButtonFromStdDialogButtonSizer(buttonSizer, wx.ID_OK).Bind(
        # #     wx.EVT_BUTTON, self.onOk
        # # )
        okButton.Bind(wx.EVT_BUTTON, self.onOk)
        self.Fit()
        # Set starting size to 600x700 for better usability
        self.SetSize(600, 700)
        self.SetMinSize((500, 400))
        self.CentreOnParent()

    def createInterior(self, pane):
        """Crée et retourne les composants internes du dialogue d'exportation.
        À redéfinir dans les sous-classes."""
        raise NotImplementedError

    def exportableViewers(self):
        """Retourne la liste des viewers exportables de la fenêtre principale."""
        return self.window.viewer

    def activeViewer(self):
        """Retourne le viewer actuellement actif dans la fenêtre principale."""
        return self.window.viewer.activeViewer()

    def options(self):
        """Retourne un dictionnaire contenant les options sélectionnées
        par l'utilisateur dans la boîte de dialogue.
        """
        result = dict()
        for component in self.components:
            result.update(component.options())
        return result

    def onOk(self, event):
        """Gère l'événement de validation (OK)
        en sauvegardant les paramètres des composants.
        """
        event.Skip()
        for component in self.components:
            component.saveSettings()


# Controls for adding behavior to the base export dialog:

# ViewerPickedEvent, EVT_VIEWERPICKED = newevent.NewEvent()
ViewerPickedEvent, EVT_VIEWERPICKED = wx.lib.newevent.NewEvent()


class ViewerPicker(sized_controls.SizedPanel):
    """Contrôle permettant d'ajouter un sélecteur de viewer au dialogue d'exportation."""

    # Attention à l'utilisation des SizedPanel :
    # self.SetSizerType("horizontal")
    #
    # b1 = wx.Button(self, wx.ID_ANY)
    # t1 = wx.TextCtrl(self, -1)
    # t1.SetSizerProps(expand=True)
    #
    # AddChild(self, child)
    #   Called automatically by wx, do not call it from user code.

    def __init__(self, parent, viewers, activeViewer):
        """Initialise le sélecteur de viewer avec la liste des viewers disponibles et le viewer actif."""
        super().__init__(parent)
        self.SetSizerType("horizontal")
        self.createPicker()
        self.populatePicker(viewers)
        self.selectActiveViewer(viewers, activeViewer)

    def createPicker(self):
        """Crée le composant graphique pour choisir un viewer."""
        label = wx.StaticText(self, label=_("Export items from:"))
        # label = wx.TextCtrl(self, value=_("Export items from:"))  # TODO : A Essayer
        # TextCtrl(parent, id=ID_ANY, value='', pos=DefaultPosition,
        # size=DefaultSize, style=0, validator=DefaultValidator,
        # name=TextCtrlNameStr) -> None
        label.SetSizerProps(valign="center")
        # label.SetSizerProps(valign="center", expand=True)
        # valid strings are “proportion”, “hgrow”, “vgrow”, “align”, “halign”, “valign”, “border”, “minsize” and “expand”
        self.viewerComboBox = wx.ComboBox(
            self, style=wx.CB_READONLY | wx.CB_SORT
        )  # pylint: disable=W0201
        self.viewerComboBox.Bind(wx.EVT_COMBOBOX, self.onViewerChanged)

    def populatePicker(self, viewers):
        """Remplit le composant de sélection avec les viewers disponibles."""
        self.titleToViewer = dict()  # pylint: disable=W0201
        for viewer in viewers:
            self.viewerComboBox.Append(viewer.title())  # pylint: disable=E1101
            # Would like to user client data in the combobox, but that
            # doesn't work on all platforms
            self.titleToViewer[viewer.title()] = viewer

    def selectActiveViewer(self, viewers, activeViewer):
        """Sélectionne le viewer actif dans la liste déroulante."""
        selectedViewer = (
            activeViewer if activeViewer in viewers else viewers[0]
        )
        self.viewerComboBox.SetValue(selectedViewer.title())

    def selectedViewer(self):
        """Retourne le viewer actuellement sélectionné par l'utilisateur."""
        return self.titleToViewer[self.viewerComboBox.GetValue()]

    def options(self):
        """Retourne le viewer sélectionné sous forme de dictionnaire d'options."""
        return dict(selectedViewer=self.selectedViewer())

    def onViewerChanged(self, event):
        """Gère le changement de viewer sélectionné par l'utilisateur."""
        event.Skip()
        wx.PostEvent(self, ViewerPickedEvent(viewer=self.selectedViewer()))

    def saveSettings(self):
        """Sauvegarde les paramètres du sélecteur de viewer
        (aucun paramètre à sauvegarder ici).
        """
        pass  # No settings to remember


class SelectionOnlyCheckBox(wx.CheckBox):
    """Contrôle permettant à l'utilisateur de choisir d'exporter
    uniquement les éléments sélectionnés.
    """

    def __init__(self, parent, settings, section, setting):
        """Initialise la case à cocher selon la configuration existante."""
        super().__init__(parent, label=_("Export only the selected items"))
        self.settings = settings
        self.section = section
        self.setting = setting
        self.initializeCheckBox()

    def initializeCheckBox(self):
        """Initialise l'état de la case à cocher à partir des paramètres enregistrés."""
        selectionOnly = self.settings.getboolean(self.section, self.setting)
        self.SetValue(selectionOnly)

    def options(self):
        """Retourne l'état de la case à cocher sous forme de dictionnaire d'options."""
        return dict(selectionOnly=self.GetValue())

    def saveSettings(self):
        """Sauvegarde l'état de la case à cocher dans les paramètres."""
        self.settings.set(
            self.section,
            self.setting,  # pylint: disable=E1101
            str(self.GetValue()),
        )


class ColumnPicker(sized_controls.SizedPanel):
    """Contrôle permettant à l'utilisateur de sélectionner les colonnes à exporter."""

    def __init__(self, parent, viewer):
        """Initialise le sélecteur de colonnes avec le viewer donné."""
        super().__init__(parent)
        self.SetSizerType("horizontal")
        # self.SetSizerType("vertical")
        self.SetSizerProps(expand=True, proportion=1)
        # self._columnMap = {}  # Maps tree item to Column object
        self.createColumnPicker()
        self.populateColumnPicker(viewer)
        # self.populateFromViewer(viewer)

    def createColumnPicker(self):
        """Crée le composant graphique pour sélectionner les colonnes à exporter."""
        label = wx.StaticText(self, label=_("Columns to export:"))
        # label = wx.TextCtrl(self, value=_("Columns to export:"))  # TODO : A Essayer ! plus approprié !?
        label.SetSizerProps(valign="top")
        self.columnPicker = widgets.CheckListBox(self)  # pylint: disable=W0201
        self.columnPicker.SetSizerProps(expand=True, proportion=1)

    def populateColumnPicker(self, viewer):
        """Remplit le sélecteur de colonnes avec les colonnes disponibles du viewer."""
        self.columnPicker.Clear()
        self.fillColumnPicker(viewer)

    def fillColumnPicker(self, viewer):
        """Ajoute les colonnes sélectionnables et coche celles qui sont visibles."""
        if not viewer.hasHideableColumns():
            return
        visibleColumns = viewer.visibleColumns()
        for column in viewer.selectableColumns():
            if column.header():
                index = self.columnPicker.Append(
                    column.header(), clientData=column
                )
                self.columnPicker.Check(index, column in visibleColumns)

    def selectedColumns(self):
        """Retourne la liste des colonnes actuellement sélectionnées par l'utilisateur."""
        indices = [
            index
            for index in range(self.columnPicker.GetCount())
            if self.columnPicker.IsChecked(index)
        ]
        return [self.columnPicker.GetClientData(index) for index in indices]

    def options(self):
        """Retourne les colonnes sélectionnées sous forme de dictionnaire d'options."""
        return dict(columns=self.selectedColumns())

    def saveSettings(self):
        """Sauvegarde les paramètres du sélecteur de colonnes
        (aucun paramètre à sauvegarder ici).
        """
        pass  # No settings to save


class SeparateDateAndTimeColumnsCheckBox(wx.CheckBox):
    """Contrôle permettant de choisir si les dates et heures
    doivent être séparées dans l'export.
    """

    def __init__(self, parent, settings, section, setting):
        """Initialise la case à cocher selon la configuration existante."""
        super().__init__(
            parent, label=_("Put task dates and times in separate columns")
        )
        self.settings = settings
        self.section = section
        self.setting = setting
        self.initializeCheckBox()

    def initializeCheckBox(self):
        """Initialise l'état de la case à cocher à partir des paramètres enregistrés."""
        separateDateAndTimeColumns = self.settings.getboolean(
            self.section, self.setting
        )
        self.SetValue(separateDateAndTimeColumns)

    def options(self):
        """Retourne l'état de la case à cocher sous forme de dictionnaire d'options."""
        return dict(separateDateAndTimeColumns=self.GetValue())

    def saveSettings(self):
        """Sauvegarde l'état de la case à cocher dans les paramètres."""
        self.settings.setboolean(self.section, self.setting, self.GetValue())


class SeparateCSSCheckBox(sized_controls.SizedPanel):
    """Contrôle permettant de choisir si les informations de style CSS
    doivent être écrites dans un fichier séparé.
    """

    def __init__(self, parent, settings, section, setting):
        """Initialise le contrôle pour la gestion du CSS séparé."""
        super().__init__(parent)
        self.SetSizerProps(expand=True)
        self.settings = settings
        self.section = section
        self.setting = setting
        self.separateCSSCheckBox = None  # Définit dans createCheckBox()
        self.createCheckBox()
        self.createHelpInformation(parent)

    def createCheckBox(self):
        """Crée la case à cocher pour l'option de CSS séparé."""
        self.separateCSSCheckBox = wx.CheckBox(
            self,  # pylint: disable=W0201
            label=_("Write style information to a separate CSS file"),
        )
        separateCSS = self.settings.getboolean(self.section, self.setting)
        self.separateCSSCheckBox.SetValue(separateCSS)

    def createHelpInformation(self, parent):
        """Affiche une aide expliquant le fonctionnement de l'option CSS séparé."""
        width = max(
            [
                child.GetSize()[0]
                for child in [self.separateCSSCheckBox]
                + list(parent.GetChildren())
            ]
        )
        info = wx.StaticText(
            self,
            label=_(
                "If a CSS file exists for the exported file, %(name)s will not overwrite it. "
                "This allows you to change the style information without losing your changes"
                " on the next export."
            )
            % meta.metaDict,
        )
        info.Wrap(width)

    def options(self):
        """Retourne l'état de l'option CSS séparé sous forme de dictionnaire d'options."""
        return dict(separateCSS=self.separateCSSCheckBox.GetValue())

    def saveSettings(self):
        """Sauvegarde l'état de l'option CSS séparé dans les paramètres."""
        self.settings.set(
            self.section,
            self.setting,
            str(self.separateCSSCheckBox.GetValue()),
        )


# Export dialogs for different file types:


class ExportAsCSVDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format CSV."""

    title = _("Export as CSV")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export CSV."""
        viewerPicker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        viewerPicker.Bind(EVT_VIEWERPICKED, self.onViewerChanged)
        # pylint: disable=W0201
        self.columnPicker = ColumnPicker(pane, viewerPicker.selectedViewer())
        selectionOnlyCheckBox = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "csv_selectiononly"
        )
        self.separateDateAndTimeColumnsCheckBox = (
            SeparateDateAndTimeColumnsCheckBox(
                pane,
                self.settings,
                self.section,
                "csv_separatedateandtimecolumns",
            )
        )
        self.__check(viewerPicker.selectedViewer())
        return (
            viewerPicker,
            self.columnPicker,
            selectionOnlyCheckBox,
            self.separateDateAndTimeColumnsCheckBox,
        )

    def onViewerChanged(self, event):
        """Met à jour le sélecteur de colonnes et les options lors d'un changement de viewer."""
        event.Skip()
        self.columnPicker.populateColumnPicker(event.viewer)
        self.__check(event.viewer)

    def __check(self, viewer):
        """Active ou désactive l'option de séparation des dates et heures suivant le type de viewer."""
        self.separateDateAndTimeColumnsCheckBox.Enable(
            viewer.isShowingTasks() or viewer.isShowingEffort()
        )


class ExportAsICalendarDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format iCalendar."""

    title = _("Export as iCalendar")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export iCalendar."""
        viewerPicker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        selectionOnlyCheckBox = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "ical_selectiononly"
        )
        return viewerPicker, selectionOnlyCheckBox

    def exportableViewers(self):
        """Retourne la liste des viewers exportables pour l'iCalendar (tâches et efforts non agrégés)."""
        viewers = super().exportableViewers()
        return [
            viewer
            for viewer in viewers
            if viewer.isShowingTasks()
            or (
                viewer.isShowingEffort()
                and not viewer.isShowingAggregatedEffort()
            )
        ]


class ExportAsHTMLDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format HTML."""

    title = _("Export as HTML")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export HTML."""
        viewerPicker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        viewerPicker.Bind(EVT_VIEWERPICKED, self.onViewerChanged)
        self.columnPicker = ColumnPicker(
            pane, viewerPicker.selectedViewer()
        )  # pylint: disable=W0201
        selectionOnlyCheckBox = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "html_selectiononly"
        )
        separateCSSChooser = SeparateCSSCheckBox(
            pane, self.settings, self.section, "html_separatecss"
        )
        return (
            viewerPicker,
            self.columnPicker,
            selectionOnlyCheckBox,
            separateCSSChooser,
        )

    def onViewerChanged(self, event):
        """Met à jour le sélecteur de colonnes lors d'un changement de viewer."""
        event.Skip()
        self.columnPicker.populateColumnPicker(event.viewer)


class ExportAsTodoTxtDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format Todo.txt."""

    title = _("Export as Todo.txt")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export Todo.txt."""
        viewerPicker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        selectionOnlyCheckBox = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "todotxt_selectiononly"
        )
        return viewerPicker, selectionOnlyCheckBox

    def exportableViewers(self):
        """Retourne la liste des viewers exportables pour Todo.txt (uniquement les tâches)."""
        viewers = super().exportableViewers()
        return [viewer for viewer in viewers if viewer.isShowingTasks()]
