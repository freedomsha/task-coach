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

Cette version utilise Tkinter pour créer une fenêtre splash similaire à celle
créée avec wxPython. Assurez-vous d'avoir installé les bibliothèques nécessaires,
notamment Pillow pour la manipulation des images (pip install Pillow).

Explications :

    Importation des modules nécessaires : Nous utilisons tkinter pour
    l'interface graphique et PIL (Python Imaging Library) pour manipuler les images.

    Création de la fenêtre SplashScreen : Nous utilisons tk.Toplevel pour
    créer une fenêtre splash sans bordure (overrideredirect(True)).

    Chargement et affichage de l'image : L'image est chargée et convertie
    en un format compatible avec Tkinter. Si la langue est de droite à gauche,
    l'image est retournée horizontalement.

    Centrage de la fenêtre : La fenêtre splash est centrée sur l'écran
    en utilisant les dimensions de l'écran et de la fenêtre.

    Fermeture automatique : La fenêtre splash est fermée automatiquement
    après 4 secondes en utilisant la méthode after.

"""

import logging
import tkinter as tk  # Pour l'interface graphique.
from io import BytesIO
from PIL import Image, ImageTk  # (Python Imaging Library) pour manipuler les images.
from taskcoachlib import i18n

log = logging.getLogger(__name__)

try:
    from . import icons
except ImportError:  # pragma: no cover
    log.error("ERROR: couldn't import icons.py.")
    log.error("You need to generate the icons file.")
    log.error("Run 'make prepare' in the Task Coach root folder.")
    import sys
    sys.exit(1)


class SplashScreen:
    # class SplashScreen(tk.Toplevel):  # SplashScreen hérite de tk.Toplevel
    def __init__(self, root):
        # __init__(self, parent, image_path):  # Ajout de image_path
        # log.debug("SplashScreen.__init__ : Début")
        # tk.Toplevel.__init__(self, parent)  # Appel correct de __init__
        self.root = root
        # self.parent = parent  # Stockage de la référence au parent
        self.root.withdraw()  # Hide the main window

        # Créer une fenêtre Toplevel pour l'écran Splash
        self.splash = tk.Toplevel()
        self.splash.overrideredirect(True)  # Remove window decorations

        # # Création de l'image de splash screen
        # try:
        #     self.splash_image = tk.PhotoImage(file=image_path)
        #     label = tk.Label(self, image=self.splash_image, borderwidth=0)
        #     label.pack()
        # except tk.TclError as e:
        #     print(f"Erreur lors du chargement de l'image: {e}")

        # Charger l'image
        splash_image = icons.catalog["splash"]

        # Convertir l'image en un format que Tkinter peut utiliser
        # if i18n.currentLanguageIsRightToLeft():
        #     # Refléter l'image si la langue se lit de droite à gauche
        #     image = ImageTk.PhotoImage(splash_image.transpose(Image.FLIP_LEFT_RIGHT))
        # else:
        #     image = ImageTk.PhotoImage(splash_image)
        # image_data = splash_image.GetData()
        # pil_image = Image.open(BytesIO(image_data))
        pil_image = splash_image.GetImage()
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Créez une étiquette (label) pour maintenir l'image
        # label = tk.Label(self.splash, image=image)
        label = tk.Label(self.splash, image=self.photo_image)
        # label.image = image  # Gardez une référence pour éviter la collecte des ordures
        label.image = self.photo_image  # Gardez une référence pour éviter la collecte des ordures
        label.pack()

        # # Suppression de la décoration de la fenêtre
        # self.overrideredirect(True)

        # Centrer l'écran splash sur l'écran
        # self.update_idletasks()
        self.splash.update_idletasks()
        width = self.splash.winfo_width()
        height = self.splash.winfo_height()
        x = (self.splash.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash.winfo_screenheight() // 2) - (height // 2)
        self.splash.geometry(f'{width}x{height}+{x}+{y}')

        # Fermez l'écran splash après 4000 millisecondes (4 seconds)
        self.splash.after(4000, self.close_splash)

    # def destroy(self):
    #     """Destruction correcte de la fenêtre (correction de la casse)"""
    #     super().destroy()  # Appel de la méthode destroy de la classe parente

    def close_splash(self):
        """Méthode interne pour fermer le splash screen."""
        self.splash.destroy()
        self.root.deiconify()  # Afficher à nouveau la fenêtre principale

# # Example usage
# if __name__ == "__main__":
#     root = tk.Tk()
#     splash = SplashScreen(root)
#     root.mainloop()
