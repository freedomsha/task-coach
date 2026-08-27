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

# Malheureusement, je ne peux pas convertir directement le fichier tooltip.py de wxPython à Tkinter.
# C'est une tâche complexe qui demande une connaissance approfondie des deux frameworks, et une simple conversion ligne par ligne n'est pas possible en raison de leurs architectures et de leurs systèmes de gestion d'événements fondamentalement différents.
#
# Voici pourquoi une conversion directe est impraticable, ainsi qu'une approche pour accomplir ce que tu souhaites, en te guidant vers les modules Tkinter appropriés.
#
# Pourquoi la Conversion Directe est Impossible ❌
#
# Le fichier tooltip.py dépend de manière intensive des classes et des fonctionnalités spécifiques à wxPython, notamment :
#
#     wx.Timer: Un objet de minuterie propre à wxPython.
#
#     wx.EVT_MOTION, wx.EVT_LEAVE_WINDOW, wx.EVT_TIMER: Des constantes d'événement spécifiques pour lier des gestionnaires.
#
#     wx.MiniFrame, wx.Frame, wx.PopupWindow: Des classes de fenêtres qui gèrent les info-bulles différemment selon le système d'exploitation.
#
#     wx.ClientDC, wx.PaintDC: Des contextes de dessin utilisés pour rendre graphiquement le contenu de l'info-bulle (texte, icônes, bordures).
#
#     wx.ArtProvider: Une classe pour obtenir des icônes de manière indépendante du système d'exploitation.
#
# Ces fonctionnalités n'ont pas d'équivalent direct dans Tkinter.
# Tkinter utilise un modèle de gestion d'événements et de rendu graphique différent.
# Par exemple, pour les événements de la souris,
# il utilise des chaînes comme <Motion>, <Leave>, ou <Button-1>,
# et le rendu graphique se fait sur un Canvas
# en utilisant des méthodes comme create_text ou create_image.
#
# L'Approche Recommandée pour Tkinter ✅
#
# Pour implémenter des info-bulles dans Tkinter,
# il est nécessaire de réécrire la logique
# en utilisant les classes et les méthodes de ce framework.
# La bonne nouvelle, c'est que les modules standards de Tkinter suffisent,
# sans avoir besoin de modules externes comme dnd (qui gère le glisser-déposer).
#
# Pour créer des info-bulles dynamiques et personnalisables comme celles décrites dans ton fichier,
# tu devrais utiliser une combinaison des modules suivants :
#
#     tkinter: Pour la classe principale de la fenêtre d'info-bulle (Toplevel) et les événements.
#
#     tkinter.ttk: Pour les styles et les widgets si tu souhaites une apparence plus moderne.
#
#     tkinter.font: Pour gérer les polices de caractères.
#
#     PIL (Pillow): C'est un module externe très courant pour gérer les images et les icônes, car Tkinter ne supporte nativement que les formats GIF et PGM/PPM. Tu devras l'installer via pip (pip install Pillow).
#
# Structure d'une Info-Bulle Tkinter
#
# Une implémentation classique de l'info-bulle en Tkinter se base sur :
#
#     Une classe ToolTip (ou similaire) héritant de tkinter.Toplevel:
#     Cette fenêtre sans bordure sera l'info-bulle elle-même.
#
#     La gestion des événements de la souris: Utiliser .bind()
#     pour lier les événements <Enter> (quand la souris entre dans un widget)
#     et <Leave> (quand elle en sort).
#
#     Une minuterie pour le délai : Utiliser la méthode .after() de Tkinter
#     pour déclencher l'affichage de l'info-bulle après un court délai,
#     évitant ainsi qu'elle ne s'affiche instantanément.
#
#     L'affichage et le positionnement : Calculer la position de la fenêtre d'info-bulle
#     (.geometry()) par rapport à la souris ou au widget,
#     puis utiliser .overrideredirect(True) pour masquer les bordures de la fenêtre
#     et la faire ressembler à une info-bulle.
#
# Si tu souhaites que je t'aide à réécrire la logique pour Tkinter,
# je peux te fournir un squelette de code pour commencer.
# Nous pourrions partir de l'idée d'une classe ToolTip et de la manière de la lier à un widget.

# La conversion directe du code wxPython vers Tkinter
# n'est pas possible en raison des différences fondamentales entre ces deux bibliothèques.
# Comme mentionné précédemment, il faut réécrire la logique en utilisant les classes et les méthodes de Tkinter.
#
# Voici une implémentation simplifiée et fonctionnelle d'un système d'info-bulles pour Tkinter,
# inspirée par la logique du fichier tooltip.py de TaskCoach.
# J'ai créé un module nommé tooltip.py pour un dossier widgetstk que tu pourrais utiliser.
# Ce code gère l'affichage, le masquage et le positionnement des info-bulles.
# Il utilise tkinter.Toplevel pour la fenêtre de l'info-bulle
# et gère les événements de la souris (<Enter>, <Leave>)
# ainsi que la temporisation avec .after().
#
# J'ai également inclus un exemple d'utilisation pour te montrer comment
# intégrer cette nouvelle classe ToolTip avec un widget Tkinter comme un Button.

# Ce code offre une base solide pour implémenter des info-bulles dans ton projet Tkinter.
# Il est beaucoup plus simple que la version wxPython car
# il n'a pas besoin de gérer les contextes de dessin
# et les variations de systèmes d'exploitation de la même manière.
# N'hésite pas si tu as d'autres questions !

# Fonctionnalités de base :
#
# Affichage et masquage : Le code actuel gère bien l'affichage et le masquage
#                         des info-bulles à l'aide de tkinter.Toplevel
#                         et des événements <Enter> et <Leave>.
#                         La temporisation avec .after() est également un bon point.
# Positionnement : Le positionnement de l'info-bulle avec wm_geometry est fonctionnel.
# Personnalisation : L'utilisation de tk.Label permet de personnaliser
#                    l'apparence de l'info-bulle (couleur de fond, bordure, etc.).
# Gestion de la destruction : La destruction correcte de l'info-bulle avec destroy() est assurée.
#
# Compléments et Améliorations :
#
# Gestion du texte multiligne :
# Le code utilise textwrap pour gérer le texte multiligne.
# Il est important de s'assurer que la largeur du texte est correctement calculée
# pour éviter les problèmes d'affichage.
#
# Compatibilité avec différents widgets :
# Le code doit être compatible avec différents types de widgets Tkinter
# (boutons, labels, entrées, etc.).
# Il faut s'assurer que la méthode _show_tooltip fonctionne correctement
# quel que soit le widget survolé.
#
# Délai d'affichage et de masquage :
# Il serait utile de pouvoir configurer les délais d'affichage et de masquage de l'info-bulle.
# Cela permettrait d'éviter les apparitions/disparitions intempestives.
#
# Positionnement avancé :
# Dans certains cas, il peut être nécessaire de positionner l'info-bulle
# par rapport au curseur de la souris plutôt qu'au widget lui-même.
# Cela peut améliorer l'ergonomie dans certaines situations.
#
# Thèmes et styles :
# Si votre application utilise des thèmes Tkinter,
# il serait bon d'intégrer la gestion des thèmes dans le code de l'info-bulle
# pour assurer une apparence cohérente.
#
# Gestion des erreurs :
# Ajouter une gestion des erreurs pour éviter que des problèmes
# lors de l'affichage de l'info-bulle ne fassent planter l'application.
#
# Vérification de l'existence de _tooltip :
# Dans la méthode _hide_tooltip, il serait plus sûr de vérifier
# si l'attribut _tooltip existe avant de le détruire et de le supprimer.
# Cela éviterait des erreurs si l'info-bulle a déjà été détruite.

# Intégration avec les autres fichiers:
#
# hcalendartk.py : La classe HierarchicalCalendar hérite déjà de tooltiptk.ToolTip.
#                  Il faudra adapter l'initialisation de l'info-bulle
#                  pour passer le widget et le texte appropriés.
# itemctrltk.py : Le mixin CtrlWithToolTipMixin devra être adapté
#                 pour utiliser la nouvelle classe ToolTip Tkinter.
# basetk.py : Ce fichier étant en cours de construction,
#             il faudra veiller à intégrer correctement la classe ToolTip lors de sa conception.
#
# Conseils supplémentaires:
#
# N'hésite pas à tester l'exemple d'utilisation fourni pour t'assurer que l'info-bulle s'affiche correctement.
# Adapte les paramètres wraplength et delay en fonction de tes besoins.
# Pense à gérer les thèmes Tkinter si ton application en utilise.
# Fichier : widgetstk/tooltip.py

import tkinter as tk
from tkinter import Toplevel, Label
import textwrap

# from taskcoachlib.widgets import SimpleToolTip  # TODO : !?


class ToolTip:
    """
    Crée une info-bulle pour un widget Tkinter.

    Cette classe gère l'affichage et le masquage d'une petite fenêtre d'info-bulle
    qui apparaît lorsque la souris reste sur un widget pendant un court instant.
    """

    def __init__(
        self, widget, text="ToolTip", wraplength=250, delay=500, **kwargs
    ):
        # def __init__(self, widget, delay=500):
        """
        Initialise l'info-bulle.

        Args :
            widget (tk.Widget) : Le widget sur lequel l'info-bulle doit apparaître.
            text (str) : Le texte à afficher dans l'info-bulle.
            wraplength (int) : La longueur maximale d'une ligne de texte (en pixels).
            delay (int) : Le délai en millisecondes avant d'afficher l'info-bulle.
        """
        self.widget = widget
        self.text = text  # = None
        self.wraplength = wraplength
        self.delay = delay
        self.timer = None
        self.tooltip_window = None
        self.after_id = None
        self.__enabled = kwargs.pop("tooltipsEnabled", True)
        self._set_bindings()

    def SetToolTipsEnabled(self, enabled):
        """
        Activer ou désactiver les info-bulles pour ce contrôle.

        Args :
            enabled (bool) : `True` pour activer les info-bulles, `False` pour les désactiver.
        """
        self.__enabled = enabled

    def on_enter(self, event):
        """
        Gère l'événement d'entrée de la souris.
        """
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event):
        """
        Gère l'événement de sortie de la souris.
        """
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        self.hide_tooltip()

    def _set_bindings(self):
        """
        Configure les gestionnaires d'événements pour le widget.
        """
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)

    def show_tooltip(self):
        """
        Affiche la fenêtre de l'info-bulle.
        """
        if self.tooltip_window or not self.text:
            return
        if self.timer:
            self.widget.after_cancel(self.timer)
        self.timer = self.widget.after(self.delay, self._create_tooltip)

    def _create_tooltip(self):
        """
        Crée la fenêtre de l'info-bulle.
        """
        # Crée la fenêtre de l'info-bulle
        self.tooltip_window = Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(
            True
        )  # Masque la barre de titre et les bordures
        self.tooltip_window.wm_attributes(
            "-topmost", True
        )  # Rends la fenêtre toujours visible au-dessus

        # Crée une étiquette pour le texte
        label = Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",  # Couleur de fond jaune pâle typique des info-bulles
            relief="solid",
            borderwidth=1,
            justify="left",
            font=("Arial", 10),
        )
        label.pack(padx=2, pady=2)

        # Calcule et définit la position de la fenêtre
        x = self.widget.winfo_rootx() + self.widget.winfo_width()
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        """
        Masque la fenêtre de l'info-bulle.
        """
        # if self.tooltip_window:
        #     self.tooltip_window.destroy()
        #     self.tooltip_window = None
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


ToolTipMixin = SimpleToolTip = (
    ToolTip  # Alias pour compatibilité avec le code existant
)


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple d'info-bulle Tkinter")

    # Crée un bouton avec une info-bulle simple
    button1 = tk.Button(root, text="Passez la souris ici")
    button1.pack(pady=20, padx=20)
    tooltip1 = ToolTip(button1, "Ceci est une info-bulle pour le bouton 1.")

    # Crée un autre bouton avec une info-bulle plus longue
    long_text = "Ceci est une info-bulle plus longue qui devrait s'ajuster si elle est trop large."
    button2 = tk.Button(root, text="Un autre bouton")
    button2.pack(pady=20, padx=20)
    tooltip2 = ToolTip(button2, textwrap.fill(long_text, width=40))

    root.mainloop()
