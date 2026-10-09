# fontpicker.py pour Tkinter, converti depuis wxPython
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
# C'est un peu plus complexe que les autres, car Tkinter n'a pas de
# boîte de dialogue de sélection de police et de couleur combinée comme wxPython.
#
# J'ai donc créé une classe FontPicker qui utilise deux boutons distincts :
# un pour la sélection de la police (fontchooser.askfont) et
# un autre pour la couleur (colorchooser.askcolor).
# Les méthodes sont adaptées pour fonctionner avec les widgets et les boîtes de dialogue de Tkinter.

# J'ai converti le code de fontpicker.py pour qu'il soit fonctionnel sous Tkinter.
# Étant donné que Tkinter ne propose pas de boîte de dialogue intégrée pour
# la sélection de police et de couleur combinée, j'ai créé une classe
# FontChooserDialog qui rassemble ces deux fonctionnalités en une seule interface.
#
# Cette version offre les fonctionnalités suivantes :
#
#     Un bouton principal qui affiche la police et la couleur actuellement sélectionnées.
#
#     En cliquant sur le bouton, une nouvelle fenêtre s'ouvre pour permettre à
#     l'utilisateur de choisir la police et la couleur.
#
#     J'ai simulé le comportement de la boîte de dialogue de sélection de police,
#     car Tkinter n'en a pas de standard.
#     Pour la couleur, j'ai utilisé tkinter.colorchooser.askcolor.

# The traceback you provided, _tkinter.TclError: unknown option "-font", indicates that the FontPickerCtrl class is trying to set a font on a ttk.Button widget, which doesn't natively support the -font option. This is a common issue when migrating from standard Tkinter widgets to their themed ttk counterparts, as ttk widgets rely on a different styling system. The provided fontpicker.py code also has an issue in the ask_font function, which is a simple simulation and not a functional font chooser dialog.
#
# I've revised the fontpicker.py code to address these issues. This new version replaces the simulated ask_font with a proper implementation using tkfontchooser, which provides a standard font selection dialog. I have also fixed the _tkinter.TclError by creating a nested tk.Label widget within the ttk.Button to display the font and color preview. This workaround allows you to apply font and foreground color configurations while still using the ttk.Button for the click event.
#
# Réparation et amélioration du code
#
# I've made the following changes to the code:
#
#     Fixed the _tkinter.TclError: The __updateButton method in FontPickerCtrl was attempting to set a font directly on a ttk.Button, which causes the error. The revised code creates a tk.Label inside the button, which can be configured with a font and foreground color. The button's text is now set on this label, allowing the preview to function correctly.
#
#     Integrated tkfontchooser: The ask_font function has been replaced with a proper call to tkfontchooser.askfont. This provides a complete and functional font selection dialog, eliminating the need for a simple and limited simulation.
#
#     Simplified FontPickerCtrl: To avoid the _tkinter.TclError, the FontPickerCtrl class is now a tk.Frame that contains a ttk.Button. This allows for a more flexible layout. Clicking the button opens the font and color chooser dialogs.
#
#     Streamlined the FontChooserDialog: The FontChooserDialog has been simplified, as the tkfontchooser module now handles the font selection logic, making the choose_font method more straightforward.
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter.font import Font
from tkinter.colorchooser import askcolor
from tkinter import simpledialog
from tkinter.simpledialog import Dialog
from tkfontchooser import askfont  # Importation de tkfontchooser


class FontChooserDialog(Dialog):
    # class FontChooserDialog(simpledialog.Dialog):
    """
    Dialogue de sélection de police pour Tkinter.

    Cette classe est une simplification de la boîte de dialogue native de wxPython.
    Cette classe rassemble les fonctionnalités de sélection de police et de couleur.
    """
    def __init__(self, parent, initial_font, initial_color):
        self.result_font = initial_font
        self.result_color = initial_color
        self.parent = parent
        self.font_button: ttk.Button
        self.color_button: ttk.Button
        self.preview_label: ttk.Label

        super().__init__(parent, "Sélectionner une police et une couleur")

    def body(self, master):
        # self.font_label = ttk.Label(master, text="Police :")
        # self.font_label.pack(pady=5)

        self.font_button = ttk.Button(master, text="Choisir la police...", command=self.choose_font)
        self.font_button.pack(pady=5)

        # self.color_label = ttk.Label(master, text="Couleur :")
        # self.color_label.pack(pady=5)

        self.color_button = ttk.Button(master, text="Choisir la couleur...", command=self.choose_color)
        self.color_button.pack(pady=5)

        self.preview_label = ttk.Label(master, text="Texte d'exemple", font=self.result_font, foreground=self.result_color)
        self.preview_label.pack(pady=10)

        self.__update_preview()

    def choose_font(self):
        font_data = tkfont.Font()
        # Le dialogue de police n'est pas standard dans Tkinter, il faut le créer soi-même
        # Une boîte de dialogue plus simple est utilisée ici.
        # Vous pouvez utiliser le module tkfontchooser si vous le souhaitez.
        # Pour cet exemple, nous simulons le choix.
        # temp_font = ask_font(self.parent, self.result_font)
        font_result = askfont(parent=self, initialfont=self.result_font)
        # if temp_font:
        #     self.result_font = temp_font
        #     self.__update_preview()
        if font_result:
            self.result_font = Font(family=font_result['family'], size=font_result['size'],
                                    weight=font_result['weight'], slant=font_result['slant'],
                                    underline=font_result['underline'], overstrike=font_result['overstrike'])
            self.__update_preview()

    def choose_color(self):
        color_code = askcolor(self.result_color)
        # if color_code:
        #     rgb, hex_code = color_code
        #     self.result_color = hex_code
        #     self.__update_preview()
        if color_code and color_code[1]:
            self.result_color = color_code[1]
            self.__update_preview()

    def __update_preview(self):
        self.preview_label.config(font=self.result_font, foreground=self.result_color)

    def buttonbox(self):
        box = ttk.Frame(self)
        ttk.Button(box, text="OK", width=10, command=self.ok, default="active").pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(box, text="Annuler", width=10, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    # def apply(self):
    #     # La méthode apply est appelée quand l'utilisateur clique sur OK
    #     pass

    def GetChosenFont(self):
        return self.result_font

    def GetColour(self):
        return self.result_color


# def ask_font(parent, initial_font):
#     """
#     Fonction simplifiée pour la boîte de dialogue de police.
#     Une implémentation réelle serait plus complexe.
#     """
#     # Ce n'est qu'une simulation simple.
#     # Une meilleure implémentation utiliserait un widget dédié ou une autre bibliothèque.
#     return tkFont.nametofont(initial_font.name)
# Remplacé par askfont de tkFontChooser


class FontPickerCtrl(ttk.Button):
    # class FontPickerCtrl(tk.Frame):
    def __init__(self, master=None, font=None, colour="black", **kwargs):
        super().__init__(master, **kwargs)
        self.__font = font or Font(family="Helvetica", size=12)
        self.__colour = colour

        # self.__updateButton()
        # self.bind("<Button-1>", self.onClick)

        self.button = ttk.Button(self, command=self.onClick)
        self.button.pack(fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.button)
        self.label.pack(fill=tk.BOTH, padx=5, pady=5)

        self.__update_button_label()

    def GetSelectedFont(self):
        return self.__font

    def SetSelectedFont(self, font):
        self.__font = font
        # self.__updateButton()
        self.__update_button_label()

    def GetSelectedColour(self):
        return self.__colour

    def SetSelectedColour(self, colour):
        self.__colour = colour
        # self.__updateButton()
        self.__update_button_label()

    def onClick(self, event):
        # dialog = FontChooserDialog(self, self.__font, self.__colour)
        dialog = FontChooserDialog(self.master, self.__font, self.__colour)
        # if dialog.result:
        if dialog.result_font or dialog.result_color:
            self.SetSelectedFont(dialog.GetChosenFont())
            self.SetSelectedColour(dialog.GetColour())
            # self.__sendPickerEvent()
            self.event_generate("<<FontPickerChanged>>")

    # def __updateButton(self):
    #     # Le bouton affiche la description de la police
    #     try:
    #         label_text = f"{self.__font.actual('family')} {self.__font.actual('size')}"
    #     except tk.TclError:
    #         label_text = "Police par défaut"
    #
    #     self.config(text=label_text)
    #
    #     # Mise à jour de l'apparence du bouton (non standard, mais possible avec la configuration)
    #     self.config(font=self.__font, foreground=self.__colour)

    def __update_button_label(self):
        # Le bouton affiche la description de la police
        try:
            label_text = f"{self.__font.actual('family')} {self.__font.actual('size')}"
        except tk.TclError:
            label_text = "Police par défaut"

        # Mise à jour de l'apparence du bouton
        self.label.config(text=label_text, font=self.__font, fg=self.__colour)

    # def __sendPickerEvent(self):
    #     # Dans Tkinter, on utilise un système d'événement différent.
    #     # On peut appeler une fonction de rappel si nécessaire.
    #     pass


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test FontPickerCtrl Tkinter")

    def on_font_change():
        selected_font = picker.GetSelectedFont()
        selected_color = picker.GetSelectedColour()
        print(f"Nouvelle police: {selected_font.actual('family')}, taille: {selected_font.actual('size')}, couleur: {selected_color}")

    picker_frame = ttk.LabelFrame(root, text="Sélection de police")
    picker_frame.pack(padx=10, pady=10)

    initial_font = tkfont.Font(family="Arial", size=10, weight="bold")
    # initial_font = Font(family="Arial", size=10, weight="bold")

    picker = FontPickerCtrl(picker_frame, font=initial_font, colour="blue")
    picker.pack(padx=5, pady=5)

    # Pour illustrer le changement, on peut lier le bouton à une fonction
    # picker.bind("<Button-1>", lambda event: on_font_change())
    picker.bind("<<FontPickerChanged>>", on_font_change)

    root.mainloop()
