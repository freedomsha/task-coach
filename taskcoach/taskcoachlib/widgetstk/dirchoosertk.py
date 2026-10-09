# dirchooser.py pour Tkinter, converti depuis wxPython
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
# Ce widget est assez simple et se prête bien à une conversion.
# L'équivalent Tkinter de wx.DirPickerCtrl est tkinter.filedialog.askdirectory.
#
# Voici la version Tkinter de dirchooser.py,
# qui utilise une entrée de texte et un bouton pour
# ouvrir une boîte de dialogue de sélection de répertoire.
# La case à cocher pour "Aucun" est gérée avec un ttk.Checkbutton.

# J'ai converti le code de dirchooser.py pour qu'il soit fonctionnel sous Tkinter.
# La principale différence est l'utilisation de filedialog.askdirectory pour
# la sélection de répertoire et la gestion des événements de la case à cocher
# via une variable de contrôle BooleanVar.
#
# Le code wxPython original mentionnait un "bug wx" qui rendait nécessaire
# un SetPath("/") après une activation, mais cela n'est pas pertinent pour
# l'implémentation Tkinter. J'ai donc omis ce contournement.

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os


class DirectoryChooser(ttk.Frame):
    """
    Panneau personnalisé pour Tkinter contenant une entrée de texte pour un chemin de répertoire
    et un bouton pour ouvrir une boîte de dialogue de sélection, avec une case à cocher
    pour sélectionner "Aucun".
    """
    def __init__(self, master=None, **kwargs):
        """
        Initialise le panneau DirectoryChooser.

        :param master: Le widget parent.
        :param kwargs: Arguments additionnels pour ttk.Frame.
        """
        super().__init__(master, **kwargs)

        # Variable pour stocker le chemin
        self.path_var = tk.StringVar()
        self.path_var.set("")

        # Variable pour la case à cocher
        self.check_var = tk.BooleanVar()
        self.check_var.set(False)

        # Crée un champ d'entrée de texte pour afficher le chemin
        self.entry = ttk.Entry(self, textvariable=self.path_var, state='!disabled')
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Crée un bouton pour ouvrir la boîte de dialogue de sélection de répertoire
        self.chooser_btn = ttk.Button(self, text="...", command=self.on_choose)
        self.chooser_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Crée la case à cocher "None"
        self.checkbx = ttk.Checkbutton(self, text="None", variable=self.check_var, command=self.on_check)
        self.checkbx.pack(side=tk.LEFT)

    def on_choose(self):
        """
        Ouvre la boîte de dialogue de sélection de répertoire et met à jour le champ.
        """
        # Récupère le chemin actuel pour l'initialiser
        initial_dir = self.path_var.get()
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")  # Revenir au répertoire de l'utilisateur si le chemin n'est pas valide

        # Utilise la fonction standard de Tkinter pour la sélection de répertoire
        selected_dir = filedialog.askdirectory(initialdir=initial_dir)
        if selected_dir:
            self.SetPath(selected_dir)

    def on_check(self):
        """
        Gère l'événement de la case à cocher pour activer/désactiver les contrôles.
        """
        is_checked = self.check_var.get()
        if is_checked:
            self.entry.config(state='disabled')
            self.chooser_btn.config(state='disabled')
            self.path_var.set("")
        else:
            self.entry.config(state='!disabled')
            self.chooser_btn.config(state='!disabled')
            # Le "bug wx" n'existe pas dans Tkinter, donc pas besoin de SetPath("/")

    def SetPath(self, pth):
        """
        Définit le chemin du répertoire et met à jour les contrôles.

        :param pth: Le chemin du répertoire.
        """
        if pth:
            self.check_var.set(False)
            self.entry.config(state='!disabled')
            self.chooser_btn.config(state='!disabled')
            self.path_var.set(pth)
        else:
            self.check_var.set(True)
            self.entry.config(state='disabled')
            self.chooser_btn.config(state='disabled')
            self.path_var.set("")

    def GetPath(self):
        """
        Retourne le chemin du répertoire si la case n'est pas cochée, sinon une chaîne vide.

        :return: Le chemin ou une chaîne vide.
        """
        if self.check_var.get():
            return ""
        return self.path_var.get()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test DirectoryChooser Tkinter")

    def print_path():
        path = chooser.GetPath()
        print(f"Le chemin sélectionné est : '{path}'")

    chooser_frame = ttk.LabelFrame(root, text="Sélection de répertoire")
    chooser_frame.pack(padx=10, pady=10, fill=tk.X)

    chooser = DirectoryChooser(chooser_frame)
    chooser.pack(fill=tk.X, padx=5, pady=5)

    # Exemple d'initialisation du chemin
    chooser.SetPath(os.path.expanduser("~"))

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=5)

    print_btn = ttk.Button(btn_frame, text="Afficher le chemin", command=print_path)
    print_btn.pack(side=tk.LEFT, padx=5)

    clear_btn = ttk.Button(btn_frame, text="Effacer le chemin", command=lambda: chooser.SetPath(None))
    clear_btn.pack(side=tk.LEFT, padx=5)

    root.mainloop()
