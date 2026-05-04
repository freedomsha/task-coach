# -*- coding: utf-8 -*-
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

Dialogues Tkinter pour la synchronisation iPhone/iPod Touch.
Basé sur le fichier iphone.py original de Task Coach.
"""
# Le fichier iphone.py original utilise wxPython pour créer des boîtes de dialogue et dépend de modules spécifiques à l'OS pour les hyperliens. J'ai réécrit le code pour utiliser tkinter à la place, en créant des fenêtres de dialogue modales qui imitent le comportement des classes wx.Dialog.
#
# J'ai converti les deux dialogues présents dans le fichier original :
#
#     IPhoneSyncTypeDialog : Converti en une classe SyncTypeDialog Tkinter.
#
#     IPhoneBonjourDialog : Converti en une classe BonjourDialog Tkinter.
#
# Pour gérer les liens hypertexte et les spécificités de l'OS, j'utilise le module standard webbrowser de Python, qui est plus portable que la méthode originale.

# J'ai également inclus une section de démonstration `if __name__ == '__main__':` qui vous montre comment appeler ces dialogues. J'ai ajouté un `messagebox` pour afficher le résultat du choix de l'utilisateur.
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from taskcoachlib.i18n import _


class SyncTypeDialog(tk.Toplevel):
    """
    Boîte de dialogue modale pour choisir le type de synchronisation.
    Remplace IPhoneSyncTypeDialog.
    """
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()  # Rendre la fenêtre modale
        self.title("Type de synchronisation")

        self.value = None # Valeur de retour du dialogue (1, 2, ou None)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        message = _('''Un appareil iPhone ou iPod Touch essaie\nde se synchroniser avec ce fichier de tâches pour\nla première fois. Quel type de synchronisation\nsouhaitez-vous utiliser ?''')
        ttk.Label(main_frame, text=message).pack(pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text=_('Actualiser depuis le bureau'), command=self.on_type1).pack(side="left", padx=5)
        ttk.Button(button_frame, text=_('Actualiser depuis l\'appareil'), command=self.on_type2).pack(side="left", padx=5)
        ttk.Button(button_frame, text=_('Annuler'), command=self.on_cancel).pack(side="left", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window(self)

    def on_type1(self):
        """Action pour le bouton 'Actualiser depuis le bureau'."""
        self.value = 1
        self.destroy()

    def on_type2(self):
        """Action pour le bouton 'Actualiser depuis l\'appareil'."""
        self.value = 2
        self.destroy()

    def on_cancel(self):
        """Action pour le bouton 'Annuler' ou la fermeture de la fenêtre."""
        self.value = None
        self.destroy()


class BonjourDialog(tk.Toplevel):
    """
    Boîte de dialogue modale pour informer sur l'installation de Bonjour.
    Remplace IPhoneBonjourDialog.
    """
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set() # Rendre la fenêtre modale
        self.title("Support Bonjour")

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text=_('Vous avez activé la fonctionnalité de synchronisation iPhone, qui\n'
                                   'nécessite Bonjour. Bonjour ne semble pas être installé sur\n'
                                   'votre système.')).pack(pady=5)

        if sys.platform == "win32":
            ttk.Label(main_frame, text=_('Veuillez télécharger et installer Bonjour pour Windows depuis\n')).pack(pady=5)
            link = ttk.Label(main_frame, text=_('le site web d\'Apple'), foreground="blue", cursor="hand2")
            link.pack(pady=5)
            link.bind("<Button-1>", lambda e: webbrowser.open("http://support.apple.com/downloads/Bonjour_for_Windows"))
        else: # On suppose MacOS ou Linux
            ttk.Label(main_frame, text=_('Le support de Bonjour pour Linux est généralement fourni par\n'
                                       'Avahi.')).pack(pady=5)
            link = ttk.Label(main_frame, text=_('Vous pouvez trouver des détails pour votre distribution ici'), foreground="blue", cursor="hand2")
            link.pack(pady=5)
            link.bind("<Button-1>", lambda e: webbrowser.open("http://avahi.org/wiki/AboutAvahi#Distributions"))
            ttk.Label(main_frame, text=_('Notez que sur certains systèmes (Fedora), vous devrez peut-être\n'
                                       'installer le paquet avahi-compat-libdns_sd ainsi qu\'Avahi pour que\n'
                                       'cela fonctionne.')).pack(pady=5)
            ttk.Label(main_frame, text=_('De plus, si vous avez un pare-feu, vérifiez que les ports 4096-4100 sont ouverts.')).pack(pady=5)

        ttk.Button(main_frame, text=_('OK'), command=self.on_ok).pack(pady=10)
        self.protocol("WM_DELETE_WINDOW", self.on_ok)
        self.wait_window(self)

    def on_ok(self):
        """Action pour le bouton 'OK' ou la fermeture de la fenêtre."""
        self.destroy()


# Démonstration de l'utilisation des dialogues
def show_sync_dialog():
    root = tk.Tk()
    root.withdraw() # Cache la fenêtre racine
    dialog = SyncTypeDialog(root)
    if dialog.value:
        messagebox.showinfo("Résultat", f"Type de synchronisation choisi : {dialog.value}")
    else:
        messagebox.showinfo("Résultat", "Synchronisation annulée.")
    root.destroy()


def show_bonjour_dialog():
    root = tk.Tk()
    root.withdraw()
    BonjourDialog(root)
    root.destroy()


if __name__ == '__main__':
    # Décommenter la ligne que vous souhaitez tester
    show_sync_dialog()
    # show_bonjour_dialog()
