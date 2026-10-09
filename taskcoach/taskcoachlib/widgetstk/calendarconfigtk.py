"""
Module calendarconfig.py - Gère la boîte de dialogue de configuration du calendrier dans Task Coach.

Ce module définit la classe CalendarConfigDialog, qui est une boîte de dialogue
permettant à l'utilisateur de configurer divers aspects de l'affichage du calendrier
dans l'application Task Coach. Cela inclut le type et le nombre de périodes affichées,
l'orientation du calendrier, les filtres de tâches à afficher,
et la couleur de surbrillance du jour actuel.

Copyright (C) 2011-2012 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre discrétion) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION OU D'ADAPTATION À UN USAGE PARTICULIER. Voir le
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Sinon, voir <http://www.gnu.org/licenses/>.
"""
# Principales conversions effectuées :
# 1. Structure de la classe
#
# Hérite de tk.Toplevel au lieu de sized_controls.SizedDialog
# Utilisation de grid pour la disposition au lieu de SizedDialog
#
# 2. Widgets remplacés
#
# wx.SpinCtrl → tk.Spinbox
# wx.Choice → ttk.Combobox
# wx.CheckBox → ttk.Checkbutton avec BooleanVar
# wx.ColourSelect → tk.Button + colorchooser.askcolor
#
# 3. Gestion des couleurs
#
# Remplacement de wx.Colour par des tuples RGB
# Conversion hexadécimale pour l'affichage
# Utilisation de colorchooser.askcolor() pour la sélection
#
# 4. Événements
#
# wx.EVT_CHOICE → <<ComboboxSelected>>
# wx.EVT_BUTTON → command= pour les boutons
# Binding des touches <Return> et <Escape>
#
# 5. Disposition
#
# Utilisation de grid() pour un layout en forme de formulaire
# Ajout d'un padding cohérent
# Centrage automatique de la fenêtre
#
# 6. Fonctionnalités ajoutées
#
# center_window() : centre la fenêtre sur le parent ou l'écran
# update_color_button() : met à jour visuellement la couleur sélectionnée
# result : attribut pour savoir si OK a été cliqué
#
# 7. Compatibilité
#
# Gestion des événements avec bind()
# Fenêtre modale avec grab_set() et transient()
# Code de test inclus avec MockSettings

import logging
import tkinter as tk
from tkinter import ttk, colorchooser

from taskcoachlib.i18n import _
from taskcoachlib.thirdparty.tkScheduler.tkSchedulerConstants import (
    SCHEDULER_DAILY,
    SCHEDULER_WEEKLY,
    SCHEDULER_MONTHLY,
    SCHEDULER_HORIZONTAL,
    SCHEDULER_VERTICAL
)

log = logging.getLogger(__name__)


class CalendarConfigDialog(tk.Toplevel):
    """
    Boîte de dialogue de configuration pour le calendrier de Task Coach.

    Cette boîte de dialogue permet à l'utilisateur de modifier les paramètres
    d'affichage du calendrier, tels que la période affichée (jour, semaine, mois),
    l'orientation (horizontale/verticale), les filtres de tâches à afficher
    et les options d'affichage spécifiques (ex: ligne de temps actuelle, couleur de surbrillance).
    """

    # Constantes de classe pour les types de vue, d'orientation et de filtres.
    VIEWTYPES = [SCHEDULER_DAILY, SCHEDULER_WEEKLY, SCHEDULER_MONTHLY]
    VIEWORIENTATIONS = [SCHEDULER_HORIZONTAL, SCHEDULER_VERTICAL]
    # Les filtres sont des tuples (show_no_start, show_no_due, show_unplanned)
    VIEWFILTERS = [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, False),
        (True, True, True)
    ]

    def __init__(self, settings, settingsSection, parent=None, *args, **kwargs):
        """
        Initialise la boîte de dialogue de configuration du calendrier.

        Args:
            settings: L'objet de configuration de l'application.
            settingsSection (str): La section des paramètres où les préférences du calendrier sont stockées.
            parent: Widget parent (optionnel).
            *args: Arguments positionnels supplémentaires.
            **kwargs: Arguments nommés supplémentaires (comme 'title').
        """
        log.debug("CalendarConfigDialog.__init__ : Lancé.")

        # Extraction du titre depuis kwargs
        title = kwargs.pop('title', _("Configuration du calendrier"))

        super().__init__(parent, *args, **kwargs)

        self._settings = settings
        self._settingsSection = settingsSection
        self.result = False  # Pour savoir si l'utilisateur a cliqué sur OK

        # Configuration de la fenêtre
        self.title(title)
        self.transient(parent)
        self.grab_set()

        # Création du contenu
        self.createInterior()

        # Création des boutons OK et Annuler
        self._spanCount: tk.Spinbox
        self._spanType: ttk.Combobox
        self._orientation: ttk.Combobox
        self._display: ttk.Combobox
        self._shownow_var: tk.BooleanVar
        self._shownow: tk.Checkbutton
        self._current_color: tuple
        self._color_button: ttk.Button
        self.createButtons()

        # Centrer la fenêtre
        self.center_window()

        # Ajuster la taille
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def center_window(self):
        """Centre la fenêtre sur l'écran ou sur le parent."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() - width) // 2
            y = self.master.winfo_y() + (self.master.winfo_height() - height) // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2

        self.geometry(f"+{x}+{y}")

    def createInterior(self):
        """
        Crée et organise les différents groupes de contrôles à l'intérieur de la boîte de dialogue.
        """
        log.debug("CalendarConfigDialog.createInterior : Crée les différents groupes de contrôles.")

        # Frame principal avec padding
        main_frame = ttk.Frame(self, padding="10")
        # main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid(row=0, column=0, sticky="wens")

        self.createPeriodEntry(main_frame)
        self.createOrientationEntry(main_frame)
        self.createDisplayEntry(main_frame)
        self.createLineEntry(main_frame)
        self.createColorEntry(main_frame)

    def createPeriodEntry(self, parent):
        """
        Crée les contrôles pour configurer le type et le nombre de périodes affichées.

        Args:
            parent: Le widget parent sur lequel les contrôles doivent être placés.
        """
        log.debug("CalendarConfigDialog.createPeriodEntry : Crée les contrôles de période.")

        row = 0

        # Label
        label = ttk.Label(parent, text=_("Kind of period displayed and its count"))
        label.grid(row=row, column=0, sticky=tk.W, pady=5)

        # Frame pour le SpinBox et le Combobox
        period_frame = ttk.Frame(parent)
        # period_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        period_frame.grid(row=row, column=1, sticky="we", pady=5, padx=5)

        # SpinBox pour le nombre de périodes
        self._spanCount = tk.Spinbox(
            period_frame,
            from_=1,
            to=100,
            width=5
        )
        # self._spanCount.pack(side=tk.LEFT, padx=(0, 5))
        self._spanCount.pack(side="left", padx=(0, 5))

        # Combobox pour le type de période
        periods = [_("Day(s)"), _("Week(s)"), _("Month")]
        self._spanType = ttk.Combobox(
            period_frame,
            values=periods,
            state='readonly',
            width=15
        )
        # self._spanType.pack(side=tk.LEFT)
        self._spanType.pack(side="left")

        # Charger les valeurs depuis les paramètres
        self._spanCount.delete(0, tk.END)
        self._spanCount.insert(0, str(self._settings.getint(self._settingsSection, "periodcount")))

        selection = self.VIEWTYPES.index(
            self._settings.getint(self._settingsSection, "viewtype")
        )
        self._spanType.current(selection)

        # Lier l'événement de changement
        self._spanType.bind("<<ComboboxSelected>>", self.onChangeViewType)

    def createOrientationEntry(self, parent):
        """
        Crée les contrôles pour configurer l'orientation du calendrier.

        Args:
            parent: Le widget parent.
        """
        log.debug("CalendarConfigDialog.createOrientationEntry : Crée les contrôles d'orientation.")

        row = 1

        # Label
        label = ttk.Label(parent, text=_("Calendar orientation"))
        label.grid(row=row, column=0, sticky=tk.W, pady=5)

        # Combobox pour l'orientation
        orientations = [_("Horizontal"), _("Vertical")]
        self._orientation = ttk.Combobox(
            parent,
            values=orientations,
            state='readonly',
            width=15
        )
        self._orientation.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)

        # Charger la valeur depuis les paramètres
        selection = self.VIEWORIENTATIONS.index(
            self._settings.getint(self._settingsSection, "vieworientation")
        )
        self._orientation.current(selection)

    def createDisplayEntry(self, parent):
        """
        Crée les contrôles pour configurer quels types de tâches afficher.

        Args:
            parent: Le widget parent.
        """
        log.debug("CalendarConfigDialog.createDisplayEntry : Crée les contrôles d'affichage.")

        row = 2

        # Label
        label = ttk.Label(parent, text=_("Which tasks to display"))
        label.grid(row=row, column=0, sticky=tk.W, pady=5)

        # Combobox pour les filtres
        choices = [
            _("Tasks with a planned start date and a due date"),
            _("Tasks with a planned start date"),
            _("Tasks with a due date"),
            _("All tasks, except unplanned tasks"),
            _("All tasks"),
        ]
        self._display = ttk.Combobox(
            parent,
            values=choices,
            state='readonly',
            width=40
        )
        # self._display.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        self._display.grid(row=row, column=1, sticky="we", pady=5, padx=5)

        # Charger la valeur depuis les paramètres
        selection = self.VIEWFILTERS.index(
            (
                self._settings.getboolean(self._settingsSection, "shownostart"),
                self._settings.getboolean(self._settingsSection, "shownodue"),
                self._settings.getboolean(self._settingsSection, "showunplanned"),
            )
        )
        self._display.current(selection)

    def createLineEntry(self, parent):
        """
        Crée un contrôle pour activer/désactiver l'affichage d'une ligne
        indiquant l'heure actuelle.

        Args:
            parent: Le widget parent.
        """
        log.debug("CalendarConfigDialog.createLineEntry : Crée le contrôle de ligne de temps.")

        row = 3

        # Label
        label = ttk.Label(parent, text=_("Draw a line showing the current time"))
        label.grid(row=row, column=0, sticky=tk.W, pady=5)

        # Checkbutton
        self._shownow_var = tk.BooleanVar()
        self._shownow = ttk.Checkbutton(parent, variable=self._shownow_var)
        self._shownow.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)

        # Charger la valeur depuis les paramètres
        self._shownow_var.set(
            self._settings.getboolean(self._settingsSection, "shownow")
        )

    def createColorEntry(self, parent):
        """
        Crée un contrôle pour sélectionner la couleur de surbrillance du jour actuel.

        Args:
            parent: Le widget parent.
        """
        log.debug("CalendarConfigDialog.createColorEntry : Crée le contrôle de couleur.")

        row = 4

        # Label
        label = ttk.Label(parent, text=_("Color used to highlight the current day"))
        label.grid(row=row, column=0, sticky=tk.W, pady=5)

        # Frame pour le bouton de couleur
        color_frame = ttk.Frame(parent)
        color_frame.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)

        # Récupérer la couleur depuis les paramètres
        hcolor = self._settings.get(self._settingsSection, "highlightcolor")
        if not hcolor:
            # Couleur par défaut (bleu clair)
            self._current_color = (128, 192, 255)
        else:
            self._current_color = tuple(int(c) for c in hcolor.split(","))

        # Bouton pour choisir la couleur
        self._color_button = tk.Button(
            color_frame,
            width=10,
            height=1,
            command=self.choose_color
        )
        # self._color_button.pack(side=tk.LEFT)
        self._color_button.pack(side="left")

        # Mettre à jour la couleur du bouton
        self.update_color_button()

    def update_color_button(self):
        """Met à jour la couleur d'affichage du bouton de sélection de couleur."""
        r, g, b = self._current_color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self._color_button.configure(bg=hex_color)

    def choose_color(self):
        """Ouvre le sélecteur de couleur."""
        r, g, b = self._current_color
        initial_color = f"#{r:02x}{g:02x}{b:02x}"

        color = colorchooser.askcolor(
            color=initial_color,
            title=_("Choose highlight color"),
            parent=self
        )

        if color[0]:  # color[0] contient le tuple RGB
            self._current_color = tuple(int(c) for c in color[0]) or None
            self.update_color_button()

    def createButtons(self):
        """Crée les boutons OK et Annuler."""
        button_frame = ttk.Frame(self)
        # button_frame.grid(row=1, column=0, sticky=(tk.E, tk.W), pady=10, padx=10)
        button_frame.grid(row=1, column=0, sticky="ew", pady=10, padx=10)

        ok_button = ttk.Button(
            button_frame,
            text=_("OK"),
            command=self.ok,
            # default=tk.ACTIVE
            default="active"
        )
        # ok_button.pack(side=tk.RIGHT, padx=5)
        ok_button.pack(side="right", padx=5)

        cancel_button = ttk.Button(
            button_frame,
            text=_("Cancel"),
            command=self.cancel
        )
        # cancel_button.pack(side=tk.RIGHT)
        cancel_button.pack(side="right")

        # Lier la touche Entrée au bouton OK
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancel())

    def onChangeViewType(self, event=None):
        """
        Gère l'événement lorsque le type de période change.

        Si le type de vue sélectionné est "Mois", le SpinBox est désactivé.
        """
        if self.VIEWTYPES[self._spanType.current()] == SCHEDULER_MONTHLY:
            self._spanCount.delete(0, tk.END)
            self._spanCount.insert(0, "1")
            self._spanCount.configure(state='disabled')
        else:
            self._spanCount.configure(state='normal')

    def ok(self, event=None):
        """
        Gère l'action de l'utilisateur lorsqu'il clique sur OK.

        Sauvegarde toutes les valeurs dans les paramètres et ferme la boîte de dialogue.
        """
        settings, section = self._settings, self._settingsSection

        # Sauvegarder le nombre de périodes
        settings.set(section, "periodcount", self._spanCount.get())

        # Sauvegarder le type de vue
        settings.set(
            section,
            "viewtype",
            str(self.VIEWTYPES[self._spanType.current()])
        )

        # Sauvegarder l'orientation
        settings.set(
            section,
            "vieworientation",
            str(self.VIEWORIENTATIONS[self._orientation.current()])
        )

        # Sauvegarder les filtres d'affichage
        shownostart, shownodue, showunplanned = self.VIEWFILTERS[
            self._display.current()
        ]
        settings.set(section, "shownostart", str(shownostart))
        settings.set(section, "shownodue", str(shownodue))
        settings.set(section, "showunplanned", str(showunplanned))

        # Sauvegarder l'option "afficher maintenant"
        settings.set(section, "shownow", str(self._shownow_var.get()))

        # Sauvegarder la couleur de surbrillance
        r, g, b = self._current_color
        settings.set(section, "highlightcolor", f"{r},{g},{b}")

        # Indiquer que OK a été cliqué
        self.result = True

        # Fermer la boîte de dialogue
        self.destroy()

    def cancel(self, event=None):
        """
        Gère l'action de l'utilisateur lorsqu'il clique sur Annuler.
        """
        self.result = False
        self.destroy()


# Test de la boîte de dialogue
if __name__ == '__main__':
    import sys

    # Mock settings pour le test
    class MockSettings:
        def __init__(self):
            self._data = {
                'periodcount': 1,
                'viewtype': SCHEDULER_WEEKLY,
                'vieworientation': SCHEDULER_HORIZONTAL,
                'shownostart': False,
                'shownodue': False,
                'showunplanned': False,
                'shownow': True,
                'highlightcolor': '128,192,255'
            }

        def getint(self, section, key):
            return self._data.get(key, 0)

        def getboolean(self, section, key):
            return self._data.get(key, False)

        def get(self, section, key):
            return str(self._data.get(key, ''))

        def set(self, section, key, value):
            if value.lower() in ('true', 'false'):
                self._data[key] = value.lower() == 'true'
            elif value.isdigit():
                self._data[key] = int(value)
            else:
                self._data[key] = value
            print(f"Setting {key} = {value}")

    root = tk.Tk()
    root.withdraw()

    settings = MockSettings()

    dialog = CalendarConfigDialog(
        settings,
        'calendarviewer',
        root,
        title=_("Configuration du calendrier")
    )

    root.wait_window(dialog)

    print(f"\nRésultat: {'OK' if dialog.result else 'Annulé'}")
    print("\nParamètres finaux:")
    for key, value in settings._data.items():
        print(f"  {key}: {value}")
