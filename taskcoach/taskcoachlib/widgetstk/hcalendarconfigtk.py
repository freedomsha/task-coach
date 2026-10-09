# hcalendarconfig.py pour Tkinter, converti de wxPython
"""
Task Coach - Your friendly task manager
Copyright (C) 2014 Task Coach developers <developers@taskcoach.org>

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
# Voici la conversion de hcalendarconfig.py en utilisant Tkinter.
# Ce fichier est un peu plus complexe car il gère la configuration via un dialogue,
# ce qui est une adaptation du dialogue SizedDialog de wxPython.
#
# J'ai converti le code en utilisant tkinter et ttk et en m'appuyant sur les
# modules tkhelper.py et fontpicker.py que nous avons convertis précédemment.
# Pour la gestion de la configuration, j'ai utilisé configparser,
# un module standard de Python, pour remplacer wx.Config.
# J'ai également créé un dialogue personnalisé car Tkinter n'a pas de dialogue
# de configuration "taille".

# J'ai converti le fichier hcalendarconfig.py en une version Tkinter.
# Voici les points clés de la conversion :
#
#     Dialogue personnalisé : Tkinter n'a pas de dialogue avec une gestion de
#     la taille comme wx.lib.sized_controls.SizedDialog,
#     j'ai donc créé une classe qui hérite de tkinter.simpledialog.Dialog.
#
#     Gestion de la configuration : J'ai remplacé l'objet de configuration
#     wx.Config par configparser, un module standard de Python qui est idéal
#     pour lire et écrire des fichiers .ini.
#
#     Sélecteur de couleur : Le sélecteur de couleur wx.lib.colourselect a été
#     remplacé par tkinter.colorchooser.askcolor, une boîte de dialogue de couleur standard.
#
#     Widgets : J'ai utilisé des widgets ttk (Themed Tkinter) pour une interface
#     plus moderne et cohérente.
#
# Le code inclut également un exemple simple qui montre comment créer une instance
# de la classe de dialogue et l'afficher.

# TODO : A refaire car fontpicker a changé ! et l'exemple est vide !
# J'ai examiné le code hcalendarconfigtk.py que vous avez fourni et le code
# wxPython d'origine. C'est un bon début, mais il manque quelques éléments pour
# que le dialogue de configuration soit entièrement fonctionnel.
# Le défi principal est de recréer les widgets spécifiques à wxPython,
# comme wx.RadioBox et wx.lib.colourselect, avec des composants Tkinter.
#
# J'ai complété le code en utilisant des Radiobutton pour le format du calendrier,
# une Checkbutton pour l'affichage de l'heure actuelle,
# et un bouton qui ouvre une boîte de dialogue de sélection de couleur de Tkinter.
# J'ai aussi veillé à ce que la logique de sauvegarde des paramètres corresponde
# au format attendu par le fichier hcalendar.py d'origine.

# Dans ce fichier, j'ai apporté les modifications suivantes pour le rendre
# fonctionnel et proche de l'original :
#
#     Dialogue Tkinter : J'ai utilisé tk.Toplevel pour créer une fenêtre
#     de dialogue modale qui empêche l'interaction avec la fenêtre principale
#     tant qu'elle est ouverte.
#
#     Widgets équivalents :
#
#         wx.RadioBox est remplacé par un ensemble de ttk.Radiobutton
#         à l'intérieur d'un ttk.LabelFrame.
#
#         wx.CheckBox est remplacé par ttk.Checkbutton.
#
#         wx.lib.colourselect est remplacé par un tk.Canvas pour afficher
#         la couleur et un ttk.Button qui appelle la boîte de dialogue de
#         sélection de couleur intégrée de Tkinter (tkinter.colorchooser.askcolor).
#
#     Logique de configuration : Les méthodes ok et cancel ont été complétées
#     pour lire les valeurs des nouveaux widgets et les enregistrer dans
#     l'objet configparser, en s'assurant que le format de la couleur est correct (R,G,B).
#
# Ce fichier est maintenant complet et peut être exécuté indépendamment
# (grâce au bloc if __name__ == '__main__':) pour le tester.
# Pour l'intégrer avec votre projet, vous devrez simplement importer
# la classe HierarchicalCalendarConfigDialog et l'utiliser là où vous avez
# besoin d'ouvrir le dialogue de configuration dans hcalendartk.py.
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter.colorchooser import askcolor
from tkinter.simpledialog import Dialog
import configparser
import os

# Importer les classes de la conversion précédente
from taskcoachlib.tools.tkhelper import get_button_from_frame_by_id
from taskcoachlib.widgetstk.fontpickertk import FontPickerCtrl


# class HierarchicalCalendarConfigDialog(Dialog):
class HierarchicalCalendarConfigDialog(tk.Toplevel):
    """
    Boîte de Dialogue de configuration pour le calendrier hiérarchique Tkinter.
    """
    def __init__(self, parent, settings, settingsSection):
        """
        Initialise la boîte de dialogue de configuration.

        Args :
            parent : Le widget parent (généralement la fenêtre principale).
            settings : L'objet configparser qui gère les paramètres.
            settingsSection : La section du fichier de configuration à utiliser.
        """
        super().__init__(parent)
        self.title("Configuration du Calendrier")
        self.transient(parent)
        self.grab_set()

        self._settings = settings
        self._settingsSection = settingsSection
        self._settings_section = self._settingsSection

        self._spanType = None
        self._shownow = None
        self._highlight = None

        self.calendar_format_var: tk.StringVar
        self._calendar_formats: list[str]
        self.show_now_var: tk.BooleanVar
        self.highlight_label: ttk.Label
        self.color_display: tk.Canvas
        self._highlight_color: str
        # super().__init__(parent, "Configuration du Calendrier")

        self.body()
        self.buttonbox()

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.parent = parent
        self.wait_window(self)

    # def body(self, master):
    def body(self):
        """
        Crée les widgets principaux de la boîte de dialogue.
        """
        # Cadre principal pour le contenu
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section Format du calendrier
        # 1. Option de format du calendrier
        # On utilise une LabelFrame pour regrouper les Radiobuttons, comme un StaticBoxSizer
        # format_frame = ttk.LabelFrame(master, text="Format du calendrier")
        format_frame = ttk.LabelFrame(main_frame, text="Format du calendrier")
        # format_frame.pack(padx=10, pady=5, fill="x")
        format_frame.pack(fill=tk.X, pady=(0, 10))

        self.calendar_format_var = tk.StringVar(self)
        self._calendar_formats = ["Semaine", "Semaine de travail", "Mois"]

        # Récupérer la valeur actuelle ou utiliser la valeur par défaut
        initial_format = self._settings.get(self._settings_section, 'calendarformat', fallback='0')
        self.calendar_format_var.set(self._calendar_formats[int(initial_format)])

        # self._spanType = ttk.Combobox(format_frame, values=["Semaine", "Semaine de travail", "Mois"])
        # self._spanType.set(self._settings.get(self._settingsSection, 'calendarformat', fallback="Semaine"))
        # self._spanType.pack(padx=5, pady=5, fill="x")

        for i, text in enumerate(self._calendar_formats):
            ttk.Radiobutton(format_frame, text=text, variable=self.calendar_format_var, value=text).pack(anchor=tk.W, padx=10, pady=2)

        # Section Affichage
        # 2. Option d'affichage de l'heure actuelle
        # display_frame = ttk.LabelFrame(master, text="Affichage")
        now_frame = ttk.Frame(main_frame)
        # display_frame.pack(padx=10, pady=5, fill="x")
        now_frame.pack(fill=tk.X, pady=(0, 10))

        self.show_now_var = tk.BooleanVar(self)
        # self._shownow = ttk.Checkbutton(display_frame, text="Afficher l'heure actuelle")
        # draw_now = self._settings.get(self._settingsSection, 'drawnow', fallback="True")
        initial_show_now = self._settings.getboolean(self._settings_section, 'drawnow', fallback=True)
        # self._shownow.state(['selected'] if draw_now.lower() == 'true' else ['!selected'])
        self.show_now_var.set(initial_show_now)
        # self._shownow.pack(padx=5, pady=5, anchor="w")
        ttk.Checkbutton(now_frame, text="Dessiner une ligne pour l'heure actuelle", variable=self.show_now_var).pack(anchor=tk.W)

        # 3. Option de surbrillance de la couleur d'aujourd'hui
        # highlight_frame = ttk.Frame(display_frame)
        highlight_frame = ttk.Frame(main_frame)
        # highlight_frame.pack(padx=5, pady=5, anchor="w")
        highlight_frame.pack(fill=tk.X)

        # ttk.Label(highlight_frame, text="Couleur d'aujourd'hui :").pack(side="left")
        self.highlight_label = ttk.Label(highlight_frame, text="Couleur de surbrillance d'aujourd'hui:")
        self.highlight_label.pack(side=tk.LEFT, padx=(0, 10))

        # Le sélecteur de couleur est une simplification par rapport à la version wxPython
        # Récupérer la couleur actuelle et la convertir
        # hcolor = self._settings.get(self._settingsSection, 'todaycolor', fallback=None)
        initial_color_str = self._settings.get(self._settings_section, 'todaycolor', fallback='128,128,128')
        # if hcolor:
        #     color = "#" + "".join([f"{int(c):02x}" for c in hcolor.split(',')])
        # else:
        #     color = "#000080"  # Couleur par défaut pour aujourd'hui
        try:
            initial_color_rgb = tuple(int(c) for c in initial_color_str.split(','))
        except (ValueError, IndexError):
            initial_color_rgb = (128, 128, 128)

        # Créer le widget de couleur et le bouton
        # self._highlight_button = ttk.Button(highlight_frame, text="Sélectionner la couleur")
        # self._highlight_button.pack(side="left", padx=5)
        # self._highlight_button.bind("<Button-1>", self.on_highlight_click)
        # self._highlight_color = color
        self.color_display = tk.Canvas(highlight_frame, width=20, height=20, relief=tk.SUNKEN, borderwidth=1)
        self.color_display.pack(side=tk.LEFT)
        self.color_display.configure(bg=f'#{initial_color_rgb[0]:02x}{initial_color_rgb[1]:02x}{initial_color_rgb[2]:02x}')

        ttk.Button(highlight_frame, text="Choisir la couleur", command=self.choose_highlight_color).pack(side=tk.LEFT, padx=5)

    def on_highlight_click(self, event):
        """
        Gère le clic sur le bouton de sélection de couleur.
        """
        color_code = askcolor(self._highlight_color)
        if color_code:
            rgb, hex_code = color_code
            self._highlight_color = hex_code

    def choose_highlight_color(self):
        """
        Ouvre la boîte de dialogue de sélection de couleur.
        """
        color_code, hex_color = askcolor(parent=self)
        if color_code:
            self.color_display.configure(bg=hex_color)
            self._highlight_color = hex_color

    def ok(self, event=None):
        """
        Gère le clic sur le bouton OK. Valide les paramètres et ferme la boîte de dialogue.
        """
        try:
            # Enregistrer les paramètres
            # self._settings.set(self._settingsSection, 'calendarformat', str(self._spanType.get()))
            # self._settings.set(self._settingsSection, 'drawnow', str(self._shownow.instate(['selected'])))
            calendar_format_index = self._calendar_formats.index(self.calendar_format_var.get())
            self._settings.set(self._settings_section, 'calendarformat', str(calendar_format_index))
            self._settings.set(self._settings_section, 'drawnow', str(self.show_now_var.get()))

            # # Convertir la couleur hexadécimale en format R,G,B pour la sauvegarde
            # hex_color = self._highlight_color.lstrip('#')
            # rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # self._settings.set(self._settingsSection, 'todaycolor', f"{rgb_color[0]},{rgb_color[1]},{rgb_color[2]}")

            # Obtenir la couleur du canvas et la convertir au format RGB
            hex_color = self.color_display.cget("bg")
            if hex_color.startswith('#'):
                hex_color = hex_color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            self._settings.set(self._settings_section, 'todaycolor', f"{rgb_color[0]},{rgb_color[1]},{rgb_color[2]}")

            # Sauvegarder les modifications dans le fichier
            with open('config.ini', 'w') as configfile:
                self._settings.write(configfile)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")

        self.destroy()

    def cancel(self):
        """
        Gère le clic sur le bouton Cancel. Ferme la boîte de dialogue.
        """
        self.destroy()

    def buttonbox(self):
        """
        Crée les boutons de la boîte de dialogue (OK, ANnuler).
        """
        box = ttk.Frame(self)
        ttk.Button(box, text="OK", width=10, command=self.ok, default="active").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(box, text="Annuler", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        box.pack(pady=10)

        # Raccourcis clavier
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)


# Exemple d'utilisation
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Exemple de Configuration du Calendrier")

    # Création d'une configuration factice pour le test
    config = configparser.ConfigParser()
    config.add_section('Calendar')
    # config.set('Calendar', 'calendarformat', 'Semaine')
    config.set('Calendar', 'calendarformat', '0')
    config.set('Calendar', 'drawnow', 'True')
    config.set('Calendar', 'todaycolor', '128,128,128')  # Exemple de couleur

    # Affiche la boîte de dialogue de configuration
    dialog = HierarchicalCalendarConfigDialog(root, settings=config, settingsSection='Calendar')

    root.mainloop()

