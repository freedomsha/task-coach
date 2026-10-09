# -*- coding: utf-8 -*-

# Voici une proposition de fichier tkhelper.py pour Tkinter. Comme les API de wxPython et Tkinter sont très différentes, les fonctions n'auront pas de correspondance exacte. J'ai donc réimplémenté la logique de base en utilisant les concepts de Tkinter et PIL (Pillow) pour la gestion des images, qui est le standard pour les manipulations d'images avec Tkinter.
#
# Le fichier tkhelper.py que je vous propose :
#
#     get_button_from_frame_by_id : J'ai adapté la fonction getButtonFromStdDialogButtonSizer pour rechercher un widget bouton dans un conteneur (comme un Frame) en utilisant son _id personnalisé, car Tkinter n'a pas de concept de buttonId comme wxPython.
#
#     Les fonctions de gestion de l'alpha : Tkinter ne gère pas nativement le canal alpha d'une image de la même manière que wxPython. J'ai donc inclus le module Pillow (PIL) pour les opérations sur les images. Les fonctions utilisent PIL.Image et PIL.ImageTk.PhotoImage pour manipuler et afficher les images, ce qui est la méthode standard en Python.
#
# J'ai inclus des commentaires détaillés dans le code pour expliquer chaque partie de la conversion.

from typing import Union, List
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


# Cette fonction est une adaptation de getButtonFromStdDialogButtonSizer de wxPython.
# Elle recherche un widget bouton à l'intérieur d'un conteneur (comme un Frame).
# Comme Tkinter n'a pas de concept de "buttonId" par défaut, nous utilisons un
# attribut personnalisé '_id' pour identifier les widgets.
def get_button_from_frame_by_id(
        parent: Union[tk.Frame, ttk.Frame], button_id: str
) -> Union[ttk.Button, tk.Button, None]:
    """
    Recherche un widget bouton dans un conteneur (Frame) par son ID personnalisé.

    Args:
        parent: Le widget conteneur dans lequel rechercher le bouton.
        button_id: L'ID personnalisé du bouton.

    Returns:
        Le widget bouton s'il est trouvé, sinon None.
    """
    for child in parent.winfo_children():
        # Vérifie si le widget est un bouton et a l'attribut '_id' correspondant
        if (
                isinstance(child, (ttk.Button, tk.Button))
                and hasattr(child, '_id')
                and getattr(child, '_id') == button_id
        ):
            return child

    return None


# Les fonctions suivantes gèrent le canal alpha d'une image.
# Elles utilisent la bibliothèque Pillow (PIL), qui est la manière standard
# de manipuler des images avec Tkinter.

def get_alpha_data_from_image(image: Image.Image) -> List[int]:
    """
    Extrait les données du canal alpha d'une image PIL.

    Args:
        image: L'objet image PIL.

    Returns:
        Une liste d'entiers représentant le canal alpha.
    """
    if image.mode not in ("RGBA", "LA"):
        image = image.convert("RGBA")

    alpha_channel = image.split()[-1]
    return list(alpha_channel.getdata())


def set_alpha_data_to_image(image: Image.Image, data: List[int]):
    """
    Définit les données du canal alpha d'une image PIL.

    Args:
        image: L'objet image PIL.
        data: La liste des entiers représentant le canal alpha.
    """
    if image.mode not in ("RGBA", "LA"):
        image = image.convert("RGBA")

    alpha_channel = Image.new("L", image.size)
    alpha_channel.putdata(data)

    image.putalpha(alpha_channel)


def clear_alpha_data_of_image(image: Image.Image, value: int):
    """
    Définit une valeur uniforme pour tout le canal alpha d'une image PIL.

    Args:
        image: L'objet image PIL.
        value: La valeur entière à appliquer (0-255).
    """
    if image.mode not in ("RGBA", "LA"):
        image = image.convert("RGBA")

    alpha_channel = Image.new("L", image.size, color=value)
    image.putalpha(alpha_channel)


# Exemple d'utilisation (pour démonstration seulement)
if __name__ == "__main__":

    # Création d'une fenêtre Tkinter
    root = tk.Tk()
    root.title("Tkinter Helper Demo")

    # Création d'un conteneur principal
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Création de boutons avec des IDs personnalisés
    # Assigner un ID personnalisé au bouton pour le retrouver plus tard
    btn1 = ttk.Button(main_frame, text="Button 1")
    btn1._id = "button1_id"
    btn1.pack(pady=5)

    btn2 = ttk.Button(main_frame, text="Button 2")
    btn2._id = "button2_id"
    btn2.pack(pady=5)

    # Recherche du bouton par son ID
    found_button = get_button_from_frame_by_id(main_frame, "button2_id")
    if found_button:
        found_button.config(text="Found!")
        print(f"Bouton trouvé: {found_button.cget('text')}")
    else:
        print("Bouton non trouvé.")

    # Démonstration des fonctions de gestion de l'alpha

    # Créer une image de démonstration (carré blanc)
    demo_image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))

    # Créer une image Tkinter pour l'affichage
    photo_image = ImageTk.PhotoImage(demo_image)

    # Afficher l'image dans un Label
    label_image = ttk.Label(main_frame, image=photo_image)
    label_image.image = photo_image
    label_image.pack(pady=10)

    # Obtenir les données alpha initiales
    alpha_data = get_alpha_data_from_image(demo_image)
    print(f"Taille des données alpha initiales: {len(alpha_data)}")

    # Assombrir la moitié supérieure de l'image en modifiant les données alpha
    for i in range(len(alpha_data) // 2):
        alpha_data[i] = 128

    # Appliquer les nouvelles données alpha
    set_alpha_data_to_image(demo_image, alpha_data)

    # Mettre à jour l'image affichée
    photo_image = ImageTk.PhotoImage(demo_image)
    label_image.config(image=photo_image)
    label_image.image = photo_image

    # Nettoyer l'image pour la rendre complètement opaque (alpha = 255)
    clear_alpha_data_of_image(demo_image, 255)

    # Mettre à jour l'image affichée une dernière fois
    photo_image = ImageTk.PhotoImage(demo_image)
    label_image.config(image=photo_image)
    label_image.image = photo_image

    # Lancer la boucle principale de Tkinter
    root.mainloop()

