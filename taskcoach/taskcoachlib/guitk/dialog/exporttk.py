# -*- coding: utf-8 -*-

"""
Task Coach - Votre gestionnaire de tâches amical
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre option) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION ou D'ADÉQUATION À UN USAGE PARTICULIER. Voir la
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Si ce n'est pas le cas, consultez <http://www.gnu.org/licenses/>.
"""

# La conversion vers Tkinter impliquera de
# recréer les dialogues d'exportation qui gèrent les sélecteurs de vue et de colonnes,
# ainsi que les cases à cocher pour les options d'exportation.
#
# Voici la version convertie de export.py pour le dossier guitk/dialog.
# J'ai utilisé une combinaison de ttk.Frame, ttk.Combobox, ttk.Checkbutton et tk.Toplevel
# pour imiter le comportement des dialogues de wxPython.

# J'ai adapté la structure pour qu'elle corresponde au comportement original de export.py,
# en utilisant des classes distinctes pour les différents sélecteurs.
# La gestion des événements onViewerChanged est maintenant implémentée
# via une liaison <<ComboboxSelected>> pour mettre à jour dynamiquement les colonnes affichées.
#
# L'exemple à la fin du fichier vous permet de tester la fenêtre de dialogue d'exportation HTML.

#  Le fichier export.py de base définit plusieurs contrôles réutilisables (ViewerPicker, ColumnPicker, SelectionOnlyCheckBox, etc.) ainsi que les dialogues spécifiques à chaque format d'exportation.
#
# Votre version partielle, exporttk.py, a déjà posé les bases de la structure Tkinter. Je vais maintenant la compléter en ajoutant les classes de contrôle et les dialogues d'exportation manquants (CSV, iCalendar, Todo.txt, et les utilitaires de cases à cocher), en m'assurant que la gestion des options et la persistance des paramètres (options() et saveSettings()) sont correctement implémentées pour Tkinter.
#
# J'ai aussi ajouté des classes de simulation (MockSettings, MockWindow) pour que l'exemple d'utilisation à la fin du fichier soit fonctionnel et démontre l'interaction entre les contrôles.

# J'ai complété la conversion en incluant toutes les classes de contrôle et de dialogue présentes dans export.py.
#
#     Les contrôles SelectionOnlyCheckBox, SeparateDateAndTimeColumnsCheckBox et SeparateCSSCheckBox sont maintenant des composants Tkinter autonomes qui gèrent l'initialisation et la sauvegarde des paramètres (settings.getboolean/settings.setboolean).
#
#     Les dialogues spécialisés (ExportAsCSVDialog, ExportAsICalendarDialog, ExportAsHTMLDialog, ExportAsTodoTxtDialog) sont implémentés et utilisent les contrôles complétés.
#
#     L'intégration des événements (comme la mise à jour des colonnes lors du changement de viewer dans ExportAsCSVDialog et ExportAsHTMLDialog) est assurée par un callback direct dans la classe ViewerPicker, ce qui est une approche plus idiomatique en Tkinter.

# L'erreur TypeError: 'str' object is not callable se produit dans le constructeur de tk.Toplevel (la classe parente de ExportDialog) à cause de la façon dont Tkinter gère l'héritage et l'initialisation dans certaines versions de Python.
#
# Cela indique que, dans le constructeur de tk.Toplevel, il essaie d'appeler root.title() pour récupérer le titre de la fenêtre principale. Cependant, si l'objet root que vous passez n'est pas une vraie instance tk.Tk ou si son attribut title a été écrasé (ce qui est peu probable dans votre cas de test simple), cela peut lever une erreur.
#
# Le problème le plus courant est que si vous appelez le constructeur tk.Toplevel avec des arguments positionnels (au lieu de mots-clés) après le parent, ils peuvent être mal interprétés.
#
# La Correction
#
# La correction la plus propre est de s'assurer que vous appelez le constructeur de la classe parente (tk.Toplevel) correctement sans perturber son initialisation interne, tout en gérant le titre de votre propre dialogue après l'appel à super().__init__.
#
# Dans la classe ExportDialog, modifions la méthode __init__ pour qu'elle ne reçoive que parent en premier argument, et gère les arguments *args et **kwargs si nécessaire, mais en s'assurant que parent est bien la racine Tkinter.
#
# J'ai simplifié l'appel super().__init__(parent, **kwargs) pour éviter tout conflit potentiel avec la façon dont tk.Toplevel est initialisé.
#
# Voici le fichier exporttk.py mis à jour :
#
# J'ai corrigé l'erreur en ajustant l'appel à la méthode super().__init__ dans la classe ExportDialog.
import logging
import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import Dialog
from taskcoachlib.i18n import _
from taskcoachlib import meta, widgets
import typing as t

log = logging.getLogger(__name__)


# Note sur la migration :
# Tkinter n'a pas de concept direct de `SizedDialog` ou de gestionnaire
# de layout complexe comme WxPython. Nous utilisons `tk.Toplevel` pour
# les boîtes de dialogue et les gestionnaires de géométrie (`pack`, `grid`)
# pour la disposition des widgets.


class ViewerPicker(ttk.Frame):
    """
    Simule le sélecteur de vue pour l'exportation.
    """

    def __init__(
        self,
        parent,
        exportable_viewers,
        active_viewer,
        viewer_change_callback=None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.exportable_viewers = exportable_viewers
        self.active_viewer = active_viewer
        self._viewer_change_callback = viewer_change_callback

        # self.label = ttk.Label(self, text=_("Viewer:"))
        # self.label.pack(side="left", padx=5, pady=5)
        ttk.Label(self, text=_("Export items from:")).pack(
            side="left", padx=5, pady=5
        )

        self.viewer_names = [v.name for v in self.exportable_viewers]
        self.viewer_map = {v.title(): v for v in self.exportable_viewers}
        initial_title = (
            active_viewer.title()
            if active_viewer in exportable_viewers
            else exportable_viewers[0].title()
        )
        # self.viewer_var = tk.StringVar(value=self.active_viewer.name)
        self.viewer_var = tk.StringVar(value=initial_title)

        self.combobox = ttk.Combobox(
            self,
            textvariable=self.viewer_var,
            # values=self.viewer_names, state="readonly")
            values=list(self.viewer_map.keys()),
            state="readonly",
        )
        self.combobox.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.combobox.bind("<<ComboboxSelected>>", self.onViewerChanged)

    @property
    def selectedViewer(self):
        """Retourne le viewer sélectionné."""
        selected_name = self.viewer_var.get()
        # return next((v for v in self.exportable_viewers if v.name == selected_name), None)
        return self.viewer_map.get(self.viewer_var.get())

    def onViewerChanged(self, event):
        """Gère le changement de viewer."""
        # Dans une application réelle, cela déclencherait un événement pour
        # mettre à jour les colonnes.
        log.debug(f"Le viewer a changé pour: {self.selectedViewer.title()}")
        if self._viewer_change_callback:
            self._viewer_change_callback(self.selectedViewer)

    def options(self):
        """Retourne le viewer sélectionné sous forme de dictionnaire d'options."""
        return dict(selectedViewer=self.selectedViewer)

    def saveSettings(self):
        """Aucun paramètre à sauvegarder dans le ViewerPicker lui-même."""
        pass


class ColumnPicker(ttk.Frame):
    """
    Simule le sélecteur de colonnes.
    """

    def __init__(self, parent, viewer, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.viewer = viewer
        # self.label = ttk.Label(self, text=_("Columns to include:"))
        # self.label.pack(side="top", anchor="w", padx=5, pady=5)
        ttk.Label(self, text=_("Columns to export:")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.column_vars = {}  # {column_name: tk.BooleanVar}
        self.columns_data = {}  # {column_name: MockColumn}

        self.columns_frame = ttk.Frame(self)
        # self.columns_frame.pack(side="top", fill="both", expand=True)
        self.columns_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Tkinter n'a pas de CheckListBox natif, nous utilisons une Frame de Checkbuttons
        # self.populateColumnPicker(self.viewer)
        self.populateColumnPicker(viewer)

    def populateColumnPicker(self, viewer):
        """Popule les cases à cocher des colonnes en fonction du viewer."""
        for widget in self.columns_frame.winfo_children():
            widget.destroy()

        self.viewer = viewer

        self.column_vars.clear()
        self.columns_data.clear()

        if not viewer.hasHideableColumns():
            ttk.Label(
                self.columns_frame,
                text=_("No hideable columns in this viewer."),
            ).pack(side="top", anchor="w")
            return

        visible_columns = [col.name for col in viewer.visibleColumns()]

        # for col in self.viewer.columns():
        #     var = tk.BooleanVar(value=True) # Par défaut, toutes les colonnes sont cochées
        #     chk = ttk.Checkbutton(self.columns_frame, text=col.label, variable=var)
        #     chk.pack(side="top", anchor="w", padx=5)
        #     self.column_vars[col.name] = var
        for col in viewer.selectableColumns():
            var = tk.BooleanVar(value=col.name in visible_columns)
            chk = ttk.Checkbutton(
                self.columns_frame, text=col.header(), variable=var
            )
            chk.pack(side="top", anchor="w", padx=5)
            self.column_vars[col.name] = var
            self.columns_data[col.name] = col

    def selectedColumns(self):
        """Retourne la liste des colonnes actuellement sélectionnées (objets MockColumn)."""
        return [
            self.columns_data[name]
            for name, var in self.column_vars.items()
            if var.get()
        ]

    def options(self):
        """Retourne les colonnes sélectionnées sous forme de dictionnaire d'options."""
        return dict(columns=self.selectedColumns())

    def saveSettings(self):
        """Aucun paramètre à sauvegarder ici (les colonnes sélectionnées sont éphémères)."""
        pass


class TkCheckBoxControl(ttk.Frame):
    """Classe de base pour les contrôles basés sur une case à cocher, gérant les options et les paramètres."""

    def __init__(self, parent, settings, section, setting, label, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self.section = section
        self.setting = setting

        self.var = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(self, text=label, variable=self.var)
        self.checkbox.pack(side="left", anchor="w")

        self.initializeCheckBox()

    def initializeCheckBox(self):
        """Initialise l'état de la case à cocher à partir des paramètres enregistrés."""
        try:
            initial_value = self.settings.getboolean(
                self.section, self.setting
            )
        except Exception:
            initial_value = False  # Valeur par défaut si non trouvée/corrompue
        self.var.set(initial_value)

    def options(self):
        """Retourne l'état de la case à cocher sous forme de dictionnaire d'options.
        Doit être surchargé dans les sous-classes pour le nom de l'option.
        """
        raise NotImplementedError

    def saveSettings(self):
        """Sauvegarde l'état de la case à cocher dans les paramètres."""
        self.settings.setboolean(self.section, self.setting, self.var.get())


class SelectionOnlyCheckBox(TkCheckBoxControl):
    """Contrôle pour choisir d'exporter uniquement les éléments sélectionnés."""

    def __init__(self, parent, settings, section, setting):
        label = _("Export only the selected items")
        super().__init__(parent, settings, section, setting, label)

    def options(self):
        return dict(selectionOnly=self.var.get())


class SeparateDateAndTimeColumnsCheckBox(TkCheckBoxControl):
    """Contrôle pour séparer les dates et heures dans l'export."""

    def __init__(self, parent, settings, section, setting):
        label = _("Put task dates and times in separate columns")
        super().__init__(parent, settings, section, setting, label)

    def options(self):
        return dict(separateDateAndTimeColumns=self.var.get())


class SeparateCSSCheckBox(ttk.Frame):
    """Contrôle pour choisir si le CSS doit être écrit dans un fichier séparé, avec aide."""

    def __init__(self, parent, settings, section, setting):
        super().__init__(parent)
        self.settings = settings
        self.section = section
        self.setting = setting

        self.var = tk.BooleanVar()
        self.createCheckBox()
        self.createHelpInformation()

    def createCheckBox(self):
        """Crée la case à cocher pour l'option de CSS séparé."""
        self.checkbox = ttk.Checkbutton(
            self,
            text=_("Write style information to a separate CSS file"),
            variable=self.var,
        )
        self.checkbox.pack(side="top", anchor="w", padx=5, pady=2)

        try:
            separateCSS = self.settings.getboolean(self.section, self.setting)
        except Exception:
            separateCSS = False
        self.var.set(separateCSS)

    def createHelpInformation(self):
        """Affiche une aide expliquant le fonctionnement de l'option CSS séparé."""
        info_text = (
            _(
                "If a CSS file exists for the exported file, %(name)s will not overwrite it. "
                "This allows you to change the style information without losing your changes "
                "on the next export."
            )
            % meta.metaDict
        )

        # Utilisation d'un Label pour afficher le texte d'aide
        info_label = ttk.Label(
            self, text=info_text, wraplength=400, justify="left"
        )
        info_label.pack(side="top", anchor="w", padx=10, pady=(0, 5))

    def options(self):
        """Retourne l'état de l'option CSS séparé sous forme de dictionnaire d'options."""
        return dict(separateCSS=self.var.get())

    def saveSettings(self):
        """Sauvegarde l'état de l'option CSS séparé dans les paramètres."""
        self.settings.setboolean(self.section, self.setting, self.var.get())


# --- Dialogue de Base ---
class ExportDialog(tk.Toplevel):
    """
    Classe de base pour tous les dialogues d'exportation (version Tkinter).
    """

    dialog_title = "Override in subclass"
    section = "export"

    def __init__(self, parent, settings, window, *args, **kwargs):
        # super().__init__(parent, **kwargs)
        # Appel de super().__init__ avec seulement le parent.
        # Tkinter (en particulier tk.Toplevel) gère l'initialisation de 'self'
        # et peut mal interpréter les arguments positionnels supplémentaires
        # comme des options de configuration.
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.window = window
        # Le titre est défini ici APRES l'appel à super()
        self.title(self.dialog_title)

        # Rendre le dialogue modal (bloque l'interaction avec le parent)
        self.transient(parent)
        self.grab_set()

        self.frame = ttk.Frame(self)
        self.frame.pack(padx=10, pady=10, fill="both", expand=True)

        # self.createInterior(self.frame)
        self.components = self.createInterior(self.frame)

        # Boutons OK et Annuler
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ok_button = ttk.Button(button_frame, text=_("OK"), command=self.on_ok)
        ok_button.pack(side="right", padx=5)

        cancel_button = ttk.Button(
            button_frame, text=_("Cancel"), command=self.on_cancel
        )
        cancel_button.pack(side="right")

        self.protocol(
            "WM_DELETE_WINDOW", self.on_cancel
        )  # Gérer la fermeture de la fenêtre
        self.update_idletasks()
        self.center_window()

        # Attendre que la fenêtre soit détruite pour rendre le dialogue modal
        self.wait_window(self)

    def center_window(self):
        """Centre la fenêtre sur l'écran."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def createInterior(self, pane):
        """Crée et retourne les composants internes.
        À surcharger dans les sous-classes.
        """
        # pass
        return []

    def exportableViewers(self):
        """Retourne la liste des viewers exportables de la fenêtre principale."""
        # return self.window.viewer
        # On suppose que self.window.viewer est une liste ou un itérable
        return list(self.window.viewer_container)

    def activeViewer(self):
        """Retourne le viewer actuellement actif dans la fenêtre principale."""
        # return self.window.viewer.activeViewer()
        return self.window.activeViewer()

    def options(self):
        """Retourne un dictionnaire contenant les options sélectionnées
        par l'utilisateur dans la boîte de dialogue.
        """
        # result = dict()
        result = {}
        for component in self.components:
            result.update(component.options())
        return result

    def on_ok(self):
        """Gère le clic sur le bouton OK, sauvegarde les paramètres et ferme."""
        # print("OK clicked. Exporting...")
        log.info(f"OK clicked for {self.title}. Options: {self.options()}")
        for component in self.components:
            component.saveSettings()

        self.destroy()

    def on_cancel(self):
        """Gère le clic sur le bouton Annuler."""
        self.destroy()


# --- Dialogues d'Exportation Spécialisés ---
class ExportAsCSVDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format CSV."""

    dialog_title = _("Export as CSV")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export CSV."""

        # 1. Viewer Picker
        viewer_picker = ViewerPicker(
            pane,
            self.exportableViewers(),
            self.activeViewer(),
            viewer_change_callback=self.onViewerChanged,
        )
        viewer_picker.pack(side="top", fill="x", padx=5, pady=5)

        # 2. Column Picker
        self.column_picker = ColumnPicker(pane, viewer_picker.selectedViewer)
        self.column_picker.pack(
            side="top", fill="both", expand=True, padx=5, pady=5
        )

        # 3. Selection Only Checkbox
        selection_only_check = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "csv_selectiononly"
        )
        selection_only_check.pack(side="top", anchor="w", padx=5)

        # 4. Separate Date and Time Checkbox
        self.separate_date_and_time_check = SeparateDateAndTimeColumnsCheckBox(
            pane, self.settings, self.section, "csv_separatedateandtimecolumns"
        )
        self.separate_date_and_time_check.pack(side="top", anchor="w", padx=5)

        # Vérification initiale de l'état du contrôle de date/heure
        self.__check(viewer_picker.selectedViewer)

        return [
            viewer_picker,
            self.column_picker,
            selection_only_check,
            self.separate_date_and_time_check,
        ]

    def onViewerChanged(self, viewer):
        """Met à jour le sélecteur de colonnes et l'option de date/heure."""
        self.column_picker.populateColumnPicker(viewer)
        self.__check(viewer)

    def __check(self, viewer):
        """Active ou désactive l'option de séparation des dates et heures."""
        enable = viewer.isShowingTasks() or viewer.isShowingEffort()
        if enable:
            self.separate_date_and_time_check.checkbox.state(["!disabled"])
        else:
            self.separate_date_and_time_check.checkbox.state(["disabled"])


class ExportAsICalendarDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format iCalendar."""

    dialog_title = _("Export as iCalendar")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export iCalendar."""
        viewer_picker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        viewer_picker.pack(side="top", fill="x", padx=5, pady=5)

        selection_only_check = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "ical_selectiononly"
        )
        selection_only_check.pack(side="top", anchor="w", padx=5)

        return [viewer_picker, selection_only_check]

    def exportableViewers(self):
        """Retourne la liste des viewers exportables pour l'iCalendar."""
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


class ExportAsHtmlDialog(ExportDialog):
    """
    Dialogue permettant d'exporter les données au format HTML.
    """

    dialog_title = _("Export as HTML")

    # def __init__(self, *args, **kwargs):
    #     # On simule les viewers et l'active_viewer pour les besoins de l'exemple
    #     self.all_viewers = [MockViewer("Task Viewer"), MockViewer("Category Viewer")]
    #     self.active_viewer = self.all_viewers[0]
    #     super().__init__(*args, **kwargs)

    # def exportableViewers(self):
    #     return self.all_viewers
    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export HTML."""
        # viewer_picker = ViewerPicker(pane, self.exportableViewers(), self.active_viewer)
        viewer_picker = ViewerPicker(
            pane,
            self.exportableViewers(),
            self.activeViewer(),
            viewer_change_callback=self.onViewerChanged,
        )
        viewer_picker.pack(side="top", fill="x", padx=5, pady=5)

        self.column_picker = ColumnPicker(pane, viewer_picker.selectedViewer)
        self.column_picker.pack(
            side="top", fill="both", expand=True, padx=5, pady=5
        )

        # selection_only_check = ttk.Checkbutton(pane, text=_("Selection only"))
        selection_only_check = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "html_selectiononly"
        )
        selection_only_check.pack(side="top", anchor="w", padx=5)

        # separate_css_check = ttk.Checkbutton(pane, text=_("Separate CSS file"))
        separate_css_chooser = SeparateCSSCheckBox(
            pane, self.settings, self.section, "html_separatecss"
        )
        # separate_css_check.pack(side="top", anchor="w", padx=5)
        separate_css_chooser.pack(side="top", fill="x", padx=5, pady=5)

        # # Lier la mise à jour des colonnes au changement de viewer
        # viewer_picker.combobox.bind("<<ComboboxSelected>>", self.onViewerChanged)

        return [
            viewer_picker,
            self.column_picker,
            selection_only_check,
            separate_css_chooser,
        ]

    # def onViewerChanged(self, event):
    def onViewerChanged(self, viewer):
        """Met à jour le sélecteur de colonnes lors d'un changement de viewer."""
        # selected_viewer = event.widget.master.selectedViewer
        # self.column_picker.populateColumnPicker(selected_viewer)
        self.column_picker.populateColumnPicker(viewer)


class ExportAsTodoTxtDialog(ExportDialog):
    """Dialogue permettant d'exporter les données au format Todo.txt."""

    dialog_title = _("Export as Todo.txt")

    def createInterior(self, pane):
        """Crée et retourne les composants internes spécifiques à l'export Todo.txt."""
        viewer_picker = ViewerPicker(
            pane, self.exportableViewers(), self.activeViewer()
        )
        viewer_picker.pack(side="top", fill="x", padx=5, pady=5)

        selection_only_check = SelectionOnlyCheckBox(
            pane, self.settings, self.section, "todotxt_selectiononly"
        )
        selection_only_check.pack(side="top", anchor="w", padx=5)

        return [viewer_picker, selection_only_check]

    def exportableViewers(self):
        """Retourne la liste des viewers exportables pour Todo.txt (uniquement les tâches)."""
        viewers = super().exportableViewers()
        return [viewer for viewer in viewers if viewer.isShowingTasks()]


class MockViewer:
    """Classe de simulation pour les besoins de l'exemple."""

    # def __init__(self, name):
    def __init__(
        self,
        name,
        viewer_title,
        is_task=False,
        is_effort=False,
        is_aggregated_effort=False,
    ):
        self.name = name
        # self.isShowingTasks = lambda: "Task" in self.name
        # self.columns = lambda: [
        #     MockColumn("subject", _("Subject")),
        #     MockColumn("due_date", _("Due Date")),
        #     MockColumn("completed", _("Completed")),
        # ] if self.isShowingTasks() else [
        #     MockColumn("name", _("Category Name")),
        #     MockColumn("note_count", _("Number of Notes")),
        # ]
        self._viewer_title = viewer_title
        self._is_task = is_task
        self._is_effort = is_effort
        self._is_aggregated_effort = is_aggregated_effort

    def title(self):
        return self._viewer_title

    def isShowingTasks(self):
        return self._is_task

    def isShowingEffort(self):
        return self._is_effort

    def isShowingAggregatedEffort(self):
        return self._is_aggregated_effort

    def hasHideableColumns(self):
        return True

    def visibleColumns(self):
        # Simule les colonnes visibles par défaut
        return self.selectableColumns()[:2]

    def selectableColumns(self):
        """Retourne la liste des colonnes sélectionnables."""
        if self.isShowingTasks():
            return [
                MockColumn("subject", _("Subject")),
                MockColumn("due_date", _("Due Date")),
                MockColumn("completed", _("Completed")),
                MockColumn("category", _("Category")),
            ]
        elif self.isShowingEffort():
            return [
                MockColumn("start_time", _("Start Time")),
                MockColumn("duration", _("Duration")),
                MockColumn("task_subject", _("Task Subject")),
            ]
        else:
            return [
                MockColumn("name", _("Category Name")),
                MockColumn("note_count", _("Number of Notes")),
            ]


class MockColumn:
    """Classe de simulation pour les colonnes."""

    # def __init__(self, name, label):
    def __init__(self, name, label, is_hideable=True):
        self.name = name
        self.label = label
        self._is_hideable = is_hideable

    def header(self):
        return self.label


class MockSettings:
    """Simule la classe de paramètres pour charger/sauvegarder."""

    def __init__(self, initial_values=None):
        self._settings = initial_values or {}

    def getboolean(self, section, setting):
        return self._settings.get(section, {}).get(setting, False)

    def set(self, section, setting, value):
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][setting] = str(value)
        log.debug(f"Settings saved: [{section}] {setting} = {value}")

    def get(self, section, setting):
        return self._settings.get(section, {}).get(setting, "")

    # Ajouté pour correspondre à l'original export.py
    def setboolean(self, section, setting, value):
        self.set(section, setting, value)


class MockWindow:
    """Simule la fenêtre principale pour l'accès aux viewers."""

    def __init__(self, viewers, active_viewer):
        self.viewer = self
        self._viewers = viewers
        self._active_viewer = active_viewer

    def activeViewer(self):
        return self._active_viewer

    def __iter__(self):
        return iter(self._viewers)


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration pour le test
    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)s: %(message)s"
    )

    root = tk.Tk()
    # root.withdraw()  # Cacher la fenêtre principale

    # Simuler les viewers
    task_viewer = MockViewer(
        name="tasks", viewer_title=_("Task Viewer"), is_task=True
    )
    effort_viewer = MockViewer(
        name="effort", viewer_title=_("Effort Viewer"), is_effort=True
    )
    category_viewer = MockViewer(
        name="categories", viewer_title=_("Category Viewer")
    )

    all_viewers = [task_viewer, effort_viewer, category_viewer]

    # Simuler les paramètres et la fenêtre
    mock_settings = MockSettings(
        initial_values={
            "export": {
                "csv_selectiononly": "True",
                "html_separatecss": "False",
            }
        }
    )
    mock_window = MockWindow(viewers=all_viewers, active_viewer=task_viewer)

    print("\n--- Test 1: Export CSV Dialogue ---")
    export_csv_dialog = ExportAsCSVDialog(
        root, settings=mock_settings, window=mock_window
    )
    # Après la fermeture du dialogue, vous pouvez vérifier les options ou les paramètres sauvegardés
    # print(f"CSV Options: {export_csv_dialog.options()}")
    # print(f"CSV Selection Only setting saved: {mock_settings.get('export', 'csv_selectiononly')}")

    # Créer une instance de dialogue
    # export_dialog = ExportAsHtmlDialog(root, settings=None, window=None)
    print("\n--- Test 2: Export HTML Dialogue ---")
    export_html_dialog = ExportAsHtmlDialog(
        root, settings=mock_settings, window=mock_window
    )
    # print(f"HTML Options: {export_html_dialog.options()}")

    print("\n--- Test 3: Export Todo.txt Dialogue ---")
    export_todotxt_dialog = ExportAsTodoTxtDialog(
        root, settings=mock_settings, window=mock_window
    )
    # print(f"Todo.txt Options: {export_todotxt_dialog.options()}")

    # export_dialog.mainloop()
    # Vous pouvez ajouter root.mainloop() ici si vous voulez voir les fenêtres
    # en boucle tant qu'elles ne sont pas fermées.
    root.mainloop()

    print("\nTests des dialogues terminés.")
