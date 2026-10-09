"""Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
# J'ai converti notifier_universal.py pour utiliser Tkinter.
# Ce fichier est plus complexe car il contient une implémentation
# complète de notifications avec des fenêtres personnalisées en utilisant wxPython.
# La conversion vers Tkinter impliquera de recréer cette logique avec les outils de Tkinter.
# Voici une version convertie de notifier_universal.py utilisant Tkinter.
# Compte tenu de la complexité du fichier original,
# cette conversion se concentrera sur la fonctionnalité de base :
# afficher une notification avec un titre et un message,
# en utilisant une fenêtre Tkinter personnalisée.

# Explications de la conversion :
#
# Importation des modules : Importation de tkinter, ttk, PIL (Pillow) et des modules nécessaires.
# Classe NotificationWindow :
#
# C'est une fenêtre Tkinter personnalisée (tk.Toplevel) pour afficher les notifications.
# __init__: Initialise la fenêtre, définit le titre, le message,
#           l'icône (si fournie) et le délai d'expiration.
#           Elle configure également l'interface utilisateur
#           et lance le minuteur de fermeture automatique.
# setup_ui: Crée les éléments de l'interface utilisateur :
#           un panneau principal, une icône (si fournie), un message et un bouton de fermeture.
#           Utilise ttk pour un style plus moderne.
# calculate_geometry: Calcule la position de la fenêtre de notification
#                     en bas à droite de l'écran.
# start_timer: Lance un minuteur qui ferme automatiquement la fenêtre après le délai spécifié.
#
#
# Classe TkinterUniversalNotifier :
#
# getName(): Retourne "Task Coach".
# isAvailable(): Retourne toujours True.
# notify():
#
# Crée un fichier temporaire pour sauvegarder le bitmap (si fourni).
# Convertit le wx.Bitmap en PIL Image et sauvegarde l'image au format PNG.
# Crée une instance de NotificationWindow avec le titre, le message et l'icône
# (le chemin du fichier temporaire).
#
#
# Enregistrement du notifier : AbstractNotifier.register(TkinterUniversalNotifier()).
# Exemple d'utilisation : Le bloc if __name__ == "__main__":
#                         contient un exemple d'utilisation du notifier.
#
# Points importants :
#
# Dépendance à Pillow : N'oubliez pas d'installer Pillow (pip install Pillow).
# Personnalisation : Cette version est une base. Vous pouvez personnaliser l'apparence de la fenêtre de notification en modifiant les styles et les widgets utilisés dans setup_ui.
# Gestion des événements : Vous pouvez ajouter des gestionnaires d'événements pour répondre aux clics sur la notification, etc.
#
# Prochaines étapes :
#
# Installez Pillow : pip install Pillow
# Testez le code : Intégrez ce code dans votre projet et TODO : vérifiez si les notifications apparaissent correctement.
# Personnalisez l'apparence : TODO : Modifiez l'interface utilisateur dans setup_ui pour obtenir l'apparence souhaitée.
# Ajoutez des fonctionnalités : Ajoutez des gestionnaires d'événements, des animations, etc., pour améliorer l'expérience utilisateur.
#
# Le fichier notifier_universal.py original contenait beaucoup de code
# spécifique à wxPython pour la gestion des fenêtres et des animations.
# La conversion complète de toutes ces fonctionnalités demanderait beaucoup de travail.
# Cette version fournit une base fonctionnelle que vous pouvez étendre selon vos besoins.

import tkinter as tk
import os
import tempfile
from tkinter import ttk
from PIL import Image, ImageTk  # Importation de Pillow pour la gestion des images
from .notifier import AbstractNotifier
from taskcoachlib import operating_system


class NotificationWindow(tk.Toplevel):
    """
    Fenêtre Tkinter personnalisée (tk.Toplevel) pour afficher les notifications.

    __init__: Initialise la fenêtre, définit le titre, le message,
              l'icône (si fournie) et le délai d'expiration.
              Elle configure également l'interface utilisateur
              et lance le minuteur de fermeture automatique.
    setup_ui: Crée les éléments de l'interface utilisateur :
              un panneau principal, une icône (si fournie), un message et un bouton de fermeture.
              Utilise ttk pour un style plus moderne.
    calculate_geometry: Calcule la position de la fenêtre de notification
                        en bas à droite de l'écran.
    start_timer: Lance un minuteur qui ferme automatiquement la fenêtre après le délai spécifié.
    """
    def __init__(self, title, message, icon=None, timeout=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        self.message = message
        self.icon_path = icon
        self.timeout = timeout * 1000  # Conversion en millisecondes
        self.overrideredirect(True)  # Enlève la bordure de la fenêtre
        self.attributes('-topmost', True)  # Garde la fenêtre au premier plan

        self.setup_ui()
        self.update_idletasks()
        self.geometry(self.calculate_geometry())
        self.start_timer()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Panel principal
        main_panel = ttk.Frame(self, padding=10)
        main_panel.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        # Configuration du panneau principal
        main_panel.grid_columnconfigure(0, weight=0)  # Colonne pour l'icône
        main_panel.grid_columnconfigure(1, weight=1)  # Colonne pour le texte

        # Icône (si fournie)
        if self.icon_path:
            try:
                self.pil_image = Image.open(self.icon_path)
                self.tk_image = ImageTk.PhotoImage(self.pil_image)
                icon_label = ttk.Label(main_panel, image=self.tk_image)
                icon_label.grid(column=0, row=0, rowspan=2, sticky=(tk.N, tk.W), padx=5)
            except FileNotFoundError:
                print(f"Image file not found: {self.icon_path}")

                # Message
        message_label = ttk.Label(main_panel, text=self.message, wraplength=250, justify=tk.LEFT)
        message_label.grid(column=1, row=0, sticky=(tk.N, tk.W, tk.E))

        # Bouton de fermeture
        close_button = ttk.Button(main_panel, text="X", width=2, command=self.destroy)
        close_button.grid(column=2, row=0, sticky=(tk.N, tk.E), padx=5)

        ttk.Separator(main_panel, orient=tk.HORIZONTAL).grid(column=0, row=2, columnspan=3, sticky=(tk.W, tk.E), pady=5)

    def calculate_geometry(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 300  # Largeur de la fenêtre
        window_height = 100  # Hauteur de la fenêtre

        x = screen_width - window_width - 20  # Position à droite
        y = screen_height - window_height - 50 # Position en bas
        return f"{window_width}x{window_height}+{x}+{y}"

    def start_timer(self):
        self.after(self.timeout, self.destroy)


class TkinterUniversalNotifier(AbstractNotifier):
    def getName(self):
        return "Tkinter notifier Task Coach"

    def isAvailable(self):
        return True

    def notify(self, title, summary, bitmap, **kwargs):
        # Sauvegarde temporaire du bitmap et affichage via la fenêtre Tkinter
        fd, filename = tempfile.mkstemp(".png")
        os.close(fd)
        try:
            if bitmap:
                # Convertir wx.Bitmap en PIL Image
                width, height = bitmap.GetWidth(), bitmap.GetHeight()
                buffer = bitmap.ConvertToImage().GetData()
                pil_image = Image.frombuffer("RGB", (width, height), buffer, "raw", "RGB", 0, 1)
                pil_image.save(filename, "PNG")
            else:
                filename = None

            NotificationWindow(title, summary, icon=filename, timeout=kwargs.get("timeout", 3))
        finally:
            if os.path.exists(filename):
                os.remove(filename)


AbstractNotifier.register(TkinterUniversalNotifier())

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Masque la fenêtre principale Tkinter

    # Exemple d'utilisation
    TkinterUniversalNotifier().notify("Test Title", "This is a test message from TaskCoach!", bitmap=None, timeout=5)

    root.mainloop()