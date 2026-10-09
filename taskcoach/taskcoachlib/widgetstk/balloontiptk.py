"""
Task Coach - Your friendly task manager
Copyright (C) 2012 Task Coach developers <developers@taskcoach.org>

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
# Voici une proposition de code pour ballontiptk.py
# qui reproduit les fonctionnalités du wxPython BalloonTip en utilisant Tkinter.
# Ce code utilise la classe Toplevel de Tkinter pour créer la fenêtre flottante
# sans bordure et gère le positionnement par rapport au widget cible.

# Ce code devrait vous donner une bonne base pour continuer la migration.
# Pour l'utilisation, il vous suffit de créer une instance de BalloonTip
# en lui passant la fenêtre parente et le widget cible,
# comme dans l'exemple if __name__ == "__main__":.

# N'hésitez pas à me dire si vous souhaitez des ajustements,
# comme par exemple le support pour une icône de flèche différente
# ou d'autres options de personnalisation.

#  Le problème principal se trouve, comme nous l'avons déjà identifié, dans la
#  méthode _draw_tip où la taille du texte est calculée.
#
# Depuis les versions plus récentes de Pillow (à partir de la version 9.2.0),
# la manière de calculer la taille du texte a changé.
# La méthode getsize est obsolète et a été remplacée par de nouvelles méthodes.
#
# Pour corriger ce problème, tu dois remplacer l'appel à getsize par la méthode
# appropriée. La méthode recommandée est textbbox.
#
# Pillow a effectivement supprimé la méthode getsize et l'a remplacée par des
# méthodes plus modernes et précises comme textbbox ou textlength.
# Le code que tu as actuellement utilise une méthode obsolète, ce qui provoque l'erreur.
#
# J'ai mis à jour le fichier balloontip.py en corrigeant cette partie,
# ainsi que quelques autres petites optimisations.

# Aperçu des modifications
#
#     Correction de AttributeError : La méthode textbbox est maintenant utilisée
#     à la place de getsize pour calculer les dimensions du titre et du message.
#     Cela assure une compatibilité avec les versions récentes de la librairie Pillow.
#
#     Améliorations mineures : J'ai ajusté quelques calculs de positionnement
#     pour s'assurer que les éléments s'affichent correctement.

# Mon code précédent avait une erreur dans la fonction de création des champs de saisie.
# Au lieu d'utiliser les classes de champs numériques et autres (NumericField, etc.),
# le code créait des objets de type Entry qui affichaient uniquement le nom du format (YYYY, MM, DD).
#
# Pour corriger cela, j'ai révisé la méthode _parse_format de la classe Entry
# pour qu'elle utilise correctement les classes NumericField, DateField, MonthField,
# et YearField en fonction des caractères de format donnés (Y, M, D).

#  L'erreur AttributeError: 'str' object has no attribute 'pack' se produit
#  parce qu'un simple caractère de chaîne de caractères
#  (comme un slash / ou un tiret -) est traité à tort comme un widget Tkinter,
#  ce qui est une erreur de ma part.
#
# Pour corriger cela, j'ai retravaillé la logique dans la classe Entry.
# Désormais, les séparateurs de format (comme - ou /) sont correctement gérés
# et convertis en widgets ttk.Label qui sont ensuite emballés (packed)
# dans l'interface, plutôt que d'être laissés sous forme de chaînes de caractères.

from __future__ import print_function
from __future__ import unicode_literals
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import Toplevel
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import logging
from math import floor

log = logging.getLogger(__name__)


class BalloonTip(Toplevel):
    # tk.messagebox.showinfo(title=None, message=None, **options)
    """
    Fenêtre flottante personnalisée de type 'info-bulle' (balloon tip) pour Tkinter.
    Reproduit le comportement du wxPython BalloonTip en utilisant un Toplevel
    sans bordure et un canevas pour dessiner la forme de la bulle avec une flèche.
    """
    ARROWSIZE = 16
    MAXWIDTH = 300

    def __init__(self, parent, target, message=None, title=None, bitmap=None, getRect=None):
        """
        Initialise une nouvelle info-bulle.

        :param parent: Fenêtre parente (une instance de tk.Tk ou tk.Toplevel).
        :param target: Widget cible auquel la bulle est associée (Button, Label, etc.).
        :param message: (optionnel) Message principal de l'info-bulle.
        :param title: (optionnel) Titre affiché en haut de la bulle.
        :param bitmap: (optionnel) Image à afficher dans la bulle (compatible PIL).
        :param getRect: (optionnel) Fonction pour obtenir la position/zone du widget cible.
        """
        # Appeler le constructeur de Toplevel avec le parent
        super().__init__(parent)

        self._parent = parent
        self._target = target
        self._getRect = getRect
        self._title = title
        self._message = message
        self._bitmap = bitmap
        self._background = "#FFFFE1"
        self._border = 1
        self._font_name = None
        self._font_size = 12
        self._is_visible = False

        self._width = 0
        self._height = 0
        self._title_font = self._get_font(self._font_size + 2, True)
        self._message_font = self._get_font(self._font_size, False)

        # Configuration de la fenêtre Toplevel
        self.wm_overrideredirect(True)  # Supprime les bordures et la barre de titre
        self.attributes('-alpha', 0.95)  # Ajoute une légère transparence
        self.wm_attributes("-topmost", True)  # Reste au-dessus des autres fenêtres
        self.transient(parent)

        # Gestionnaire d'événement de clic pour fermer la bulle
        self.bind("<Button-1>", self.do_close)

        # Le contenu de la bulle est dessiné sur un canevas
        self._canvas = tk.Canvas(self, bg=self._background, highlightthickness=0)
        # self._canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas.pack(fill="both", expand=True)

        # Dessiner la bulle initiale et la positionner
        self._draw_tip()
        self.position()

        # Lier les événements de déplacement et de redimensionnement de la fenêtre parente
        self.update_id = None
        self._target.bind("<Configure>", self._on_configure)

    def _get_font(self, size, bold):
        """Helper to get a font."""
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()

    def do_close(self, event=None):
        """
        Ferme la bulle.
        """
        if self.update_id:
            self.after_cancel(self.update_id)
        self.destroy()

    def _draw_tip(self):
        """
        Crée l'image de l'info-bulle avec la flèche et le contenu (titre, message, icône).
        """
        title_text_width = 0
        title_text_height = 0
        message_text_width = 0
        message_text_height = 0

        # # Créer une image de fond (virtuelle) pour le dessin
        # padding = 10
        # arrow_height = self.ARROWSIZE
        #
        # # Calculer la taille du contenu
        # dummy_label = ttk.Label(self, text=self._message, wraplength=self.MAXWIDTH)
        # dummy_label.pack()
        # self.update_idletasks()
        # content_width = dummy_label.winfo_width()
        # content_height = dummy_label.winfo_height()
        # dummy_label.destroy()

        # Utilisez textbbox pour obtenir la taille du texte
        if self._title:
            # title_bbox = self._title_font.textbbox((0, 0), self._title)
            title_bbox = self._title_font.getbbox(self._title)
            title_text_width = title_bbox[2] - title_bbox[0]
            title_text_height = title_bbox[3] - title_bbox[1]

        if self._message:
            # message_bbox = self._message_font.textbbox((0, 0), self._message)
            message_bbox = self._message_font.getbbox(self._message)
            message_text_width = message_bbox[2] - message_bbox[0]
            message_text_height = message_bbox[3] - message_bbox[1]

        # # Utiliser une image PIL pour dessiner la forme et le contenu
        # total_width = content_width + padding * 2
        # total_height = content_height + arrow_height + padding * 2

        # # Ajouter de l'espace pour le titre et le bitmap
        # title_width = 0
        # title_height = 0
        # if self._title:
        #     # title_font = ("TkDefaultFont", 12, "bold")
        #     self.title_font = ("TkDefaultFont", 12, "bold")
        #     # TODO : voir avec ImageFont.FreeTypeFont comment obtenir width et height
        #     # title_text_width = ImageFont.FreeTypeFont.getsize(self._title, font=ImageFont.FreeTypeFont.load_default())[0]
        #     # # title_text_width = ImageFont.FreeTypeFont.getlength(self._title, font=ImageFont.FreeTypeFont.load_default())[0]
        #     # title_text_height = ImageFont.FreeTypeFont.getsize(self._title, font=ImageFont.FreeTypeFont.load_default())[1]
        #     # # _, _, title_text_width, title_text_height = ImageFont.FreeTypeFont.getbbox(self._title, font=ImageFont.FreeTypeFont.load_default())
        #     # title_width = title_text_width
        #     # title_height = title_text_height + padding
        #
        #     # Utilise ImageFont.FreeTypeFont.getbbox pour obtenir la boîte englobante du texte
        #     # Le tuple retourné est (left, top, right, bottom)
        #     # L'argument text= est nécessaire pour la méthode textbbox
        #     # title_bbox = self._title_font.textbbox((0, 0), self._title)
        #     title_bbox = self.title_font.textbbox((0, 0), self._title)
        #     title_text_width = title_bbox[2] - title_bbox[0]  # width = right - left
        #
        #     # Pour les versions plus anciennes de Pillow, tu peux utiliser textsize
        #     # title_text_width = self._title_font.textsize(self._title)[0]
        # else:
        #     title_text_width = 0

        # icon_width = 0
        # if self._bitmap:
        #     icon_width = self._bitmap.width

        icon_size = (0, 0)
        if self._bitmap:
            icon_size = self._bitmap.size

        margin = 10
        padding = 5
        arrow_size = 20

        # Mettre à jour la largeur totale si le titre/l'icône sont plus grands
        # total_width = max(total_width, title_width + icon_width + padding * 3)
        # total_height += title_height
        #
        # image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        # draw = ImageDraw.Draw(image)

        content_width = max(title_text_width + icon_size[0] + padding, message_text_width)
        content_height = title_text_height + message_text_height + padding

        self._width = content_width + 2 * margin
        self._height = content_height + 2 * margin + arrow_size

        img_width = self._width
        img_height = self._height
        image = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        # # Dessiner le fond (arrondi) de la bulle
        # box_rect = [0, 0, total_width, total_height - arrow_height]
        # draw.rounded_rectangle(box_rect, radius=10, fill='wheat')
        #
        # # Dessiner le contenu (titre, message, bitmap)
        # current_x = padding
        # if self._bitmap:
        #     image.paste(self._bitmap, (current_x, padding))
        #     current_x += self._bitmap.width + padding
        #
        # if self._title:
        #     # TODO : a revoir !
        #     draw.text((current_x, padding), self._title, fill='black', font=title_font)

        # Draw the balloon body
        points = [
            (self._border, self._border),
            (self._width - self._border, self._border),
            (self._width - self._border, self._height - arrow_size - self._border),
            (self._width / 2 + arrow_size / 2, self._height - arrow_size - self._border),
            (self._width / 2, self._height - self._border),
            (self._width / 2 - arrow_size / 2, self._height - arrow_size - self._border),
            (self._border, self._height - arrow_size - self._border),
            (self._border, self._border)
        ]
        draw.polygon(points, fill=self._background, outline="#888")

        # Add content to the image
        text_x = margin
        text_y = margin

        if self._bitmap:
            image.paste(self._bitmap, (margin, margin))
            text_x += icon_size[0] + padding

        if self._title:
            draw.text((text_x, text_y), self._title, font=self._title_font, fill="black")
            text_y += title_text_height + padding

        if self._message:
            draw.text((margin, text_y), self._message, font=self._message_font, fill="black")

        self._tk_image = ImageTk.PhotoImage(image)
        self._canvas.config(width=img_width, height=img_height)
        self._canvas.create_image(0, 0, image=self._tk_image, anchor="nw")

        self.geometry(f"{img_width}x{img_height}+{self._get_position()}")

        # # Position du message après le titre/l'icône
        # msg_y = padding + (self._bitmap.height if self._bitmap else 0) + (title_height if self._title else 0)
        # draw.text((padding, msg_y), self._message, fill='black')
        #
        # # Créer l'objet PhotoImage pour le canevas Tkinter
        # self._photoimage = ImageTk.PhotoImage(image)
        # self._canvas.config(width=total_width, height=total_height)
        # self._canvas.create_image(0, 0, image=self._photoimage, anchor=tk.NW)
        #
        # # Mettre à jour la flèche après le dessin du contenu
        # self.update_idletasks()
        # self.arrow_x = 0
        # self.arrow_y = 0

    def _get_position(self):
        """Calculates the position of the tip."""
        target_x, target_y = self._target.winfo_rootx(), self._target.winfo_rooty()
        target_width, target_height = self._target.winfo_width(), self._target.winfo_height()

        # Position below the widget
        x = target_x + (target_width / 2) - (self._width / 2)
        y = target_y + target_height

        return f"{int(x)}+{int(y)}"

    def position(self):
        """
        Calcule et définit la position de la bulle par rapport à son widget cible.
        Gère la direction de la flèche (haut/bas) selon la place disponible.
        """
        # Récupérer la géométrie du widget cible
        target_x = self._target.winfo_rootx()
        target_y = self._target.winfo_rooty()
        target_width = self._target.winfo_width()
        target_height = self._target.winfo_height()

        # Calculer la position x de la bulle
        tip_width = self.winfo_width()
        tip_height = self.winfo_height()

        # Centrer la bulle au-dessus/en-dessous du widget cible
        x = target_x + floor(target_width / 2) - floor(tip_width / 2)
        y = target_y - tip_height

        direction = "top"

        # Vérifier si la bulle sort de l'écran en haut
        if y < 0:
            y = target_y + target_height
            direction = "bottom"

        # Déplacer la fenêtre
        self.geometry(f'+{x}+{y}')

        # Dessiner la flèche sur le canevas en fonction de la direction
        self.draw_arrow(direction)

    def _on_configure(self, event):
        """
        Gestionnaire d'événement pour repositionner la bulle si la fenêtre parente bouge.
        """
        if self.update_id:
            self.after_cancel(self.update_id)
        # Utiliser un délai pour éviter de multiples repositionnements trop rapides
        self.update_id = self.after(50, self.position)

    def on_click(self, event):
        """Hides the tip when clicked."""
        self.hide()

    def show(self):
        """Shows the balloon tip."""
        self.update_idletasks()
        self.lift()
        self.wm_deiconify()
        self._is_visible = True

    def hide(self):
        """Hides the balloon tip."""
        self.withdraw()
        self._is_visible = False

    @staticmethod
    def show_tip(parent, target_widget, message, title="", bitmap=None):
        """Convenience method to show a tip and hide it after a delay."""
        tip = BalloonTip(parent, target_widget, message, title, bitmap)
        tip.show()
        # You might want to add a self-destruct mechanism here
        # E.g., tip.after(5000, tip.hide)

    def draw_arrow(self, direction):
        """
        Dessine la flèche sur le canevas.
        """
        # Nettoyer l'ancienne flèche si elle existe
        self._canvas.delete("arrow")

        tip_width = self.winfo_width()

        # Calculer la position x de la flèche par rapport au widget cible
        target_x_relative_to_tip = self._target.winfo_rootx() - self.winfo_rootx()
        arrow_tip_x = target_x_relative_to_tip + floor(self._target.winfo_width() / 2)

        if direction == "bottom":
            points = [
                (arrow_tip_x - self.ARROWSIZE / 2, self.winfo_height() - self.ARROWSIZE),
                (arrow_tip_x, self.winfo_height()),
                (arrow_tip_x + self.ARROWSIZE / 2, self.winfo_height() - self.ARROWSIZE)
            ]
            self._canvas.create_polygon(points, fill='wheat', outline='wheat', tags="arrow")
        else:  # "top"
            points = [
                (arrow_tip_x - self.ARROWSIZE / 2, self.ARROWSIZE),
                (arrow_tip_x, 0),
                (arrow_tip_x + self.ARROWSIZE / 2, self.ARROWSIZE)
            ]
            self._canvas.create_polygon(points, fill='wheat', outline='wheat', tags="arrow")


# Le BalloonTipManager gère une file d'attente d'info-bulles pour s'assurer qu'elles ne s'affichent pas toutes en même temps et gère les événements de fermeture de la fenêtre parente.
class BalloonTipManager(object):
    """
    Utilisez-le comme un mixin dans la fenêtre de niveau supérieur (tk.Tk ou tk.Toplevel)
    qui héberge les cibles de la bulle d'aide, pour éviter qu'ils n'apparaissent
    en une seule fois et gérer les événements de fermeture.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise le gestionnaire de tips.

        Note : En tant que mixin, l'appel à super().__init__ doit être
        géré par la classe parente si elle hérite de tk.Tk ou tk.Toplevel.
        Ici, nous l'appelons par sécurité pour les mixins Python.
        """
        self.__tips = list()
        self.__displaying = None
        self.__kwargs = dict()
        self.__shutdown = False
        # Assurez-vous que l'initialisation de la classe parente est appelée
        # si ce manager est utilisé dans une structure d'héritage multiple.
        if super().__init__ is not object.__init__:
            super().__init__(*args, **kwargs)

        # Lier l'événement de fermeture de la fenêtre de niveau supérieur
        # self représente l'instance de tk.Tk ou tk.Toplevel
        self.bind("<Destroy>", self.__OnClose)  # Anticipation car mixin !

    def AddBalloonTip(self, target, message=None, title=None, bitmap=None, getRect=None, **kwargs):
        """
        Planifie l'affichage d'une info-bulle. Les arguments mots-clés
        supplémentaires seront transmis à L{OnBalloonTipShow} et L{OnBalloonTipClosed}.
        """
        # Vérifie si un tip identique (titre et message) est déjà en file
        for eTarget, eMessage, eTitle, eBitmap, eGetRect, eArgs in self.__tips:
            if (eTitle, eMessage) == (title, message):
                return
        self.__tips.append((target, message, title, bitmap, getRect, kwargs))
        self.__Try()

    def __Try(self):
        """
        Tente d'afficher le prochain tip en file s'il n'y en a pas déjà un d'affiché
        et si le manager n'est pas en cours d'arrêt.
        """
        if self.__tips and not self.__shutdown and self.__displaying is None:
            # Récupère le prochain tip de la file
            target, message, title, bitmap, getRect, kwargs = self.__tips.pop(0)

            # Crée et affiche le BalloonTip (utilise self comme parent)
            tip = BalloonTip(self, target, message=message, title=title,
                             bitmap=bitmap, getRect=getRect)

            self.__displaying = tip
            self.OnBalloonTipShow(**kwargs)  # Appel au hook
            self.__kwargs = kwargs

            # Lier l'événement de destruction du tip pour passer au suivant
            # Tkinter utilise l'événement <Destroy> pour la fermeture/destruction d'un widget
            tip.bind("<Destroy>", self.__OnCloseTip)
            tip.show()  # Affiche explicitement la fenêtre toplevel

    def __OnClose(self, event):
        """
        Gestionnaire d'événement de fermeture de la fenêtre principale.
        Empêche l'affichage de nouveaux tips.
        """
        # L'événement <Destroy> n'a pas besoin d'être 'skippé' dans le sens de wxPython.
        # On vérifie si l'événement provient bien de 'self' pour éviter les boucles
        # si un enfant se ferme et déclenche le <Destroy> sur le parent.
        if event.widget == self:
            self.__shutdown = True

    def __OnCloseTip(self, event):
        """
        Gestionnaire d'événement de fermeture du tip affiché.
        Déclenche l'affichage du tip suivant.
        """
        # Assurez-vous que c'est bien l'info-bulle en cours qui est détruite
        if event.widget == self.__displaying:
            self.__displaying = None
            self.OnBalloonTipClosed(**self.__kwargs)  # Appel au hook
            self.__Try()

    def OnBalloonTipShow(self, **kwargs):
        """Hook appelé juste après l'affichage d'un BalloonTip."""
        pass

    def OnBalloonTipClosed(self, **kwargs):
        """Hook appelé juste après la fermeture d'un BalloonTip."""
        pass


if __name__ == "__main__":

    # # Pour l'exemple, nous allons créer une image simple pour la "bitmap"
    # image_pil = Image.new('RGBA', (24, 24), (255, 255, 255, 0))
    # draw = ImageDraw.Draw(image_pil)
    # draw.ellipse((0, 0, 24, 24), fill='red', outline='black')
    #
    # # def on_click():
    # #     """
    # #     Fonction pour afficher l'info-bulle lorsque le bouton est cliqué.
    # #     """
    # #     # Le widget parent est la fenêtre principale
    # #     parent_window = root
    # #
    # #     # Le widget cible est le bouton
    # #     target_widget = btn
    # #
    # #     BalloonTip(parent_window, target_widget,
    # #                message="""Your bones don't break, mine do. That's clear. Your cells react to bacteria
    # #                    and viruses differently than mine. You don't get sick, I do. That's also clear. But for some
    # #                    reason, you and I react the exact same way to water. We swallow it too fast, we choke. We get
    # #                    some in our lungs, we drown. However unreal it may seem, we are connected, you and I. We're on
    # #                    the same curve, just on opposite ends.""",
    # #                title="Title",
    # #                bitmap=image_pil)
    #
    # root = tk.Tk()
    # root.title("Test BalloonTip Tkinter")
    # # root.geometry("800x600")
    # root.geometry("400x300")
    #
    # # main_frame = ttk.Frame(root)
    # # main_frame.pack(expand=True, padx=20, pady=20)
    #
    # # Check if PIL is installed
    # try:
    #     from PIL import Image, ImageTk
    #     has_pil = True
    #     print("Pillow (PIL) is installed. Images can be used.")
    # except ImportError:
    #     has_pil = False
    #     print("Pillow (PIL) is not installed. Images are disabled.")
    #
    # # Create a dummy image for the example
    # image_pil = None
    # if has_pil:
    #     image_pil = Image.new('RGB', (32, 32), color = 'red')
    #     d = ImageDraw.Draw(image_pil)
    #     d.rectangle([5, 5, 27, 27], fill='blue')
    #
    # def on_click():
    #     """Shows the balloon tip on button click."""
    #     BalloonTip.show_tip(
    #         root, btn,
    #         message="Ceci est un exemple de BalloonTip. "
    #                 "Il peut contenir un titre, un message et une image.",
    #         title="Titre du tip",
    #         bitmap=image_pil
    #     )
    #
    # # btn = ttk.Button(main_frame, text="Show balloon", command=on_click)
    # btn = tk.Button(root, text="Cliquez-moi", command=on_click)
    # # btn.pack(padx=10, pady=10)
    # btn.pack(pady=50)
    #
    # # # Créer un autre bouton pour tester la position sur un autre widget
    # # btn2 = ttk.Button(main_frame, text="Another Button", command=lambda: BalloonTip(root, btn2, "This is another tip."))
    # # btn2.pack(padx=10, pady=10)
    #
    # # Example of a static tip on a label
    # label_static = tk.Label(root, text="Passez la souris ici pour un autre tip")
    # label_static.pack(pady=20)
    #
    # tip_static = None
    #
    # def enter_tip(event):
    #     global tip_static
    #     if tip_static:
    #         tip_static.show()
    #     else:
    #         tip_static = BalloonTip(
    #             root, event.widget,
    #             message="Ceci est un tip statique.",
    #             title="Tip Statique"
    #         )
    #         tip_static.show()
    #
    # def leave_tip(event):
    #     global tip_static
    #     if tip_static:
    #         tip_static.hide()
    #
    # label_static.bind("<Enter>", enter_tip)
    # label_static.bind("<Leave>", leave_tip)
    #
    # root.mainloop()

    # ... (code de l'image_pil pour l'exemple reste ici) ...
    # Pour l'exemple, nous allons créer une image simple pour la "bitmap"
    image_pil = Image.new('RGBA', (24, 24), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image_pil)
    draw.ellipse((0, 0, 24, 24), fill='red', outline='black')

    try:
        from PIL import Image, ImageTk
        has_pil = True
    except ImportError:
        has_pil = False

    image_pil_example = None
    if has_pil:
        image_pil_example = Image.new('RGB', (32, 32), color='red')
        d = ImageDraw.Draw(image_pil_example)
        d.rectangle([5, 5, 27, 27], fill='blue')

    # Nouvelle classe de fenêtre principale
    class Application(tk.Tk, BalloonTipManager):
        def __init__(self):
            # Initialisation de tk.Tk et de BalloonTipManager
            tk.Tk.__init__(self)
            BalloonTipManager.__init__(self)

            self.title("Test BalloonTip Tkinter avec Manager")
            self.geometry("400x300")

            self.btn1 = tk.Button(self, text="Tip 1 (clic)", command=self.on_click_tip1)
            self.btn1.pack(pady=20, padx=10)

            self.btn2 = tk.Button(self, text="Tip 2 (clic)", command=self.on_click_tip2)
            self.btn2.pack(pady=10, padx=10)

        def on_click_tip1(self):
            """Ajoute le premier tip à la file."""
            self.AddBalloonTip(
                self.btn1,
                message="Ceci est le Premier Tip de la file. Il apparaîtra immédiatement.",
                title="Tip #1",
                bitmap=image_pil_example
            )

        def on_click_tip2(self):
            """Ajoute le second tip à la file (n'apparaîtra qu'après la fermeture du Tip 1)."""
            self.AddBalloonTip(
                self.btn2,
                message="Ceci est le Deuxième Tip. Il attendra son tour.",
                title="Tip #2",
                bitmap=image_pil_example
            )

        # Implémentations optionnelles des hooks du manager
        def OnBalloonTipShow(self, **kwargs):
            # Exemple de logique personnalisée lors de l'affichage
            print(f"Tip affiché avec kwargs: {kwargs}")

        def OnBalloonTipClosed(self, **kwargs):
            # Exemple de logique personnalisée après la fermeture
            print(f"Tip fermé avec kwargs: {kwargs}")

    app = Application()
    app.mainloop()

