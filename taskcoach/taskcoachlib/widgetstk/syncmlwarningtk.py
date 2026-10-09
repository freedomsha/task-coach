# syncmlwarning.py pour Tkinter, converti de wxPython
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
# La conversion de syncmlwarning.py est plus simple que les précédentes car
# elle ne contient pas de logique complexe de gestion d'événements ou de données.
# C'est un simple dialogue d'avertissement.
#
# Pour Tkinter, l'équivalent est une boîte de dialogue personnalisée ou une Toplevel.
# J'ai choisi d'utiliser tkinter.messagebox car cela correspond bien à l'objectif
# d'un simple avertissement. J'ai aussi inclus une version de la classe du
# dialogue pour une réutilisation plus aisée, si jamais d'autres dialogues
# simples devaient être convertis.

# J'ai converti le code de syncmlwarning.py pour qu'il soit fonctionnel avec Tkinter.
#
# Le code converti propose deux approches :
#
#     L'utilisation de tkinter.messagebox pour une solution simple, car un
#     dialogue d'avertissement est un cas d'usage typique pour les boîtes de message standard.
#
#     La création d'une classe SyncMLWarningDialog qui hérite de tk.Toplevel
#     pour une réimplémentation plus fidèle au code original de wxPython.
#     Cette version inclut la case à cocher et un bouton OK, tout en garantissant
#     que le dialogue est modal.
#
# Cette conversion vous permet d'avoir soit un simple avertissement via une boîte de message,
# soit un dialogue personnalisé si vous avez besoin d'une interface plus complexe
# pour d'autres avertissements.
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Union


# Une version simplifiée du dialogue d'avertissement en utilisant Toplevel
class SyncMLWarningDialog(tk.Toplevel):
    """
    Dialogue d'avertissement SyncML pour Tkinter.
    """
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Avertissement de compatibilité")

        self.transient(parent)  # Rendre le dialogue modal par rapport à la fenêtre parente
        self.grab_set()  # Capturer les événements, ce qui rend le dialogue modal
        self.resizable(False, False)

        # Texte de l'avertissement
        text_message = (
            "La fonctionnalité SyncML est désactivée, car le module\n"
            "n'a pas pu être chargé. Cela peut être dû au fait que votre plateforme\n"
            "n'est pas prise en charge ou, sous Windows, qu'il vous manque\n"
            "certaines DLL obligatoires. Veuillez consulter la section SyncML de\n"
            "l'aide en ligne pour plus de détails (sous \"Dépannage\")."
        )
        self.text_widget = ttk.Label(self, text=text_message, justify=tk.LEFT)
        self.text_widget.pack(padx=10, pady=10)

        # Case à cocher "Ne plus afficher ce dialogue"
        self.show_again_var = tk.BooleanVar(value=True)
        self.checkbox = ttk.Checkbutton(
            self, text="Ne plus afficher ce dialogue", variable=self.show_again_var
        )
        self.checkbox.pack(pady=5)

        # Bouton OK
        self.ok_button = ttk.Button(self, text="OK", command=self.on_ok)
        self.ok_button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_ok)  # Gérer la fermeture de la fenêtre

    def on_ok(self):
        """ Gère le clic sur le bouton OK. """
        self.destroy()

    def get_checkbox_value(self) -> bool:
        """ Retourne la valeur de la case à cocher. """
        return self.show_again_var.get()


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    def show_dialog_as_messagebox():
        """ Exemple d'utilisation de la boîte de message standard. """
        result = messagebox.showwarning(
            title="Avertissement de compatibilité",
            message=(
                "La fonctionnalité SyncML est désactivée, car le module\n"
                "n'a pas pu être chargé. Cela peut être dû au fait que votre plateforme\n"
                "n'est pas prise en charge ou, sous Windows, qu'il vous manque\n"
                "certaines DLL obligatoires. Veuillez consulter la section SyncML de\n"
                "l'aide en ligne pour plus de détails (sous \"Dépannage\")."
            ),
        )

    def show_custom_dialog():
        """ Exemple d'utilisation du dialogue personnalisé. """
        dialog = SyncMLWarningDialog(root)
        root.wait_window(dialog)  # Attendre la fermeture du dialogue
        print(f"La case à cocher 'Ne plus afficher' était cochée : {dialog.get_checkbox_value()}")

    root = tk.Tk()
    root.title("Exemple d'avertissement SyncML")

    ttk.Button(root, text="Afficher le dialogue (messagebox)", command=show_dialog_as_messagebox).pack(pady=5)
    ttk.Button(root, text="Afficher le dialogue (personnalisé)", command=show_custom_dialog).pack(pady=5)

    root.mainloop()
