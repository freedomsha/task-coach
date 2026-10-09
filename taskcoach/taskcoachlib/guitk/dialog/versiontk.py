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

Dialogues Tkinter pour l'affichage de la version.
Basé sur le fichier version.py original de Task Coach.
"""
# Le fichier version.py contient plusieurs boîtes de dialogue pour afficher des informations sur la version de l'application. J'ai converti ces classes de wxPython à Tkinter, en utilisant tk.Toplevel pour les boîtes de dialogue modales et ttk.Label pour les textes.
#
# Pour les liens hypertexte, j'ai utilisé une étiquette ttk.Label avec un style de lien (foreground="blue", cursor="hand2") et j'ai lié l'événement de clic à la fonction webbrowser.open(), ce qui rend le code portable sur différents systèmes d'exploitation.

# J'ai inclus une section if __name__ == '__main__': à la fin du code pour vous permettre de tester chaque dialogue. Il suffit de décommenter la ligne de la boîte de dialogue que vous voulez voir.
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Any, Dict, Optional
from taskcoachlib import meta
from taskcoachlib.i18n import _


# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# class meta:
#     class data:
#         name = "Task Coach"
#         url = "https://www.taskcoach.org/"


# # Simuler le module i18n
# def _(text):
#     return text


class VersionDialog(tk.Toplevel):
    """
    Classe de base pour les dialogues de version.
    """
    dialog_title = ''

    def __init__(self, parent: tk.Tk, settings: Dict[str, Any], message: str, version: str):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(self.dialog_title)

        self.settings = settings
        self.message = message
        self.messageInfo = {
            "version": version,
            "currentVersion": version,
            "name": meta.data.name
        }

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.createInterior(main_frame)

        ok_button = ttk.Button(main_frame, text=_("OK"), command=self.on_ok)
        ok_button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_ok)

        self.update_idletasks() # Ajuste la taille de la fenêtre
        self.wait_window(self)

    def createInterior(self, panel: ttk.Frame):
        """Méthode à surcharger pour créer le contenu du dialogue."""
        raise NotImplementedError("createInterior doit être implémenté par les sous-classes.")

    def on_ok(self):
        self.destroy()


class NewVersionDialog(VersionDialog):
    dialog_title = _("Nouvelle version de %(name)s disponible") % {"name": meta.data.name}

    def __init__(self, parent: tk.Tk, settings: Dict[str, Any], message: str, version: str):
        super().__init__(parent, settings, message, version)

    def createInterior(self, panel: ttk.Frame):
        label_text = _('Une nouvelle version de %(name)s, version %(version)s, est disponible.') % self.messageInfo
        ttk.Label(panel, text=label_text).pack(pady=5)

        ttk.Label(panel, text=_('Vous utilisez %(name)s version %(currentVersion)s.') % self.messageInfo).pack(pady=5)

        url_frame = ttk.Frame(panel)
        url_frame.pack(pady=5)

        ttk.Label(url_frame, text=_('La version %(version)s de %(name)s est disponible sur') % self.messageInfo).pack(side="left")

        hyperlink_label = ttk.Label(url_frame, text=meta.data.url, foreground="blue", cursor="hand2")
        hyperlink_label.pack(side="left")
        hyperlink_label.bind("<Button-1>", lambda e: webbrowser.open(meta.data.url))


class VersionUpToDateDialog(VersionDialog):
    dialog_title = _('%(name)s est à jour') % {"name": meta.data.name}

    def createInterior(self, panel: ttk.Frame):
        label_text = _('%(name)s est à jour à la version %(version)s.') % self.messageInfo
        ttk.Label(panel, text=label_text).pack(pady=5)


class NoVersionDialog(VersionDialog):
    title = _("Impossible de trouver la dernière version")

    def createInterior(self, panel: ttk.Frame):
        label_text = _("Impossible de savoir quelle est la dernière version de %(name)s.") % self.messageInfo
        ttk.Label(panel, text=label_text).pack(pady=5)
        ttk.Label(panel, text=self.message).pack(pady=5)


class PrereleaseVersionDialog(VersionDialog):
    dialog_title = _("Version de pré-lancement")

    def createInterior(self, panel: ttk.Frame):
        label_text_1 = _('Vous utilisez une version de pré-lancement de %(name)s version %(currentVersion)s.') % self.messageInfo
        ttk.Label(panel, text=label_text_1).pack(pady=5)

        label_text_2 = _('La dernière version publiée de %(name)s est la version %(version)s.') % self.messageInfo
        ttk.Label(panel, text=label_text_2).pack(pady=5)

        url_frame = ttk.Frame(panel)
        url_frame.pack(pady=5)

        ttk.Label(url_frame, text=_('La version %(version)s de %(name)s est disponible sur') % self.messageInfo).pack(side="left")

        hyperlink_label = ttk.Label(url_frame, text=meta.data.url, foreground="blue", cursor="hand2")
        hyperlink_label.pack(side="left")
        hyperlink_label.bind("<Button-1>", lambda e: webbrowser.open(meta.data.url))


if __name__ == '__main__':
    # Démonstration des différents dialogues
    root = tk.Tk()
    # root.withdraw()
    settings = {}

    # Afficher le dialogue pour une nouvelle version
    # NewVersionDialog(root, settings, message="", version="2.0.0")

    # Afficher le dialogue pour la version à jour
    # VersionUpToDateDialog(root, settings, message="", version="1.9.0")

    # Afficher le dialogue en cas d'erreur
    # NoVersionDialog(root, settings, message="Erreur de connexion.", version="1.9.0")

    # Afficher le dialogue pour une version de pré-lancement
    PrereleaseVersionDialog(root, settings, message="", version="2.0.0-rc1")

    root.mainloop()
