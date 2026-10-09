"""
Task Coach - Your friendly task manager
SquareMap viewer – version Tkinter
"""

import operator  # Opérateurs logiques
from functools import reduce  # Réduction logique
import tkinter as tk  # Interface graphique Tkinter

from taskcoachlib.thirdparty.tk3rdparty import squaremaptk as squaremap  # SquareMap Tkinter converti
from . import tooltiptk as tooltip  # Tooltip TaskCoach


# class SquareMap(tooltip.ToolTipMixin, squaremap.SquareMap):
class SquareMap(tooltip.ToolTipMixin, squaremap.SquareMap):
    """
    Adaptateur SquareMap pour TaskCoach (Tkinter).
    """

    def __init__(self, parent, rootNode, onSelect, onEdit, popupMenu):
        """
        Initialise la vue SquareMap TaskCoach.
        """
        # Sélection courante
        self.__selection = []  # Liste des éléments sélectionnés

        # Fonction tooltip fournie par le parent (viewer)
        self.getItemTooltipData = parent.getItemTooltipData  # Callback tooltip

        # Initialisation SquareMap Tkinter
        super().__init__(
            parent,
            model=rootNode,
            adapter=parent,
            highlight=False
        )

        # Tooltip simple
        self.__tip = tooltip.SimpleToolTip(self)  # Instance tooltip

        # Commandes externes TaskCoach
        self.selectCommand = onSelect  # Callback sélection
        self.editCommand = onEdit  # Callback édition
        self.popupMenu = popupMenu  # Menu contextuel Tkinter

        # Bind événements SquareMap Tkinter
        self.bind("<<SquareSelected>>", self.onSelect)  # Sélection
        self.bind("<<SquareActivated>>", self.onEdit)  # Activation

        # Bind clic droit (menu contextuel)
        self.bind("<Button-3>", self.onPopup)  # Clic droit

    def RefreshAllItems(self, count):  # pylint: disable=W0613
        """
        Rafraîchit tous les items (API TaskCoach).
        """
        self.redraw()  # Redessin complet

    def RefreshItems(self, *args):  # pylint: disable=W0613
        """
        Rafraîchit certains items (API TaskCoach).
        """
        self.redraw()  # Redessin complet

    def onSelect(self, event):
        """
        Gestion de la sélection d’un nœud.
        """
        node = self.selectedNode  # Nœud sélectionné dans SquareMap

        if node == self.model:  # Si racine
            self.__selection = []  # Aucune sélection
        else:
            self.__selection = [node]  # Sélection simple

        # Appel différé du callback TaskCoach
        self.after_idle(self.selectCommand)

    def select(self, items):
        """
        Sélection programmée (non utilisée ici).
        """
        pass  # API requise par TaskCoach

    def onEdit(self, event):
        """
        Gestion de l’activation (double clic / entrée).
        """
        self.editCommand(event)  # Appel callback édition

    def OnBeforeShowToolTip(self, x, y):
        """
        Prépare l’affichage du tooltip si nécessaire.
        """
        # Recherche du nœud sous la souris
        item = squaremap.HotMapNavigator.findNodeAtPosition(
            self.hot_map,
            (x, y)
        )

        # Aucun tooltip pour la racine ou le vide
        if item is None or item == self.model:
            return None

        # Données tooltip fournies par TaskCoach
        tooltipData = self.getItemTooltipData(item)

        # Vérifie si au moins une ligne contient une valeur
        doShow = reduce(
            operator.__or__,
            list(map(bool, [data[1] for data in tooltipData])),
            False
        )

        if doShow:
            self.__tip.SetData(tooltipData)  # Injecte données
            return self.__tip  # Tooltip à afficher

        return None  # Rien à afficher

    def onPopup(self, event):
        """
        Affiche le menu contextuel.
        """
        # Sélectionne l’élément sous le curseur
        self.on_click(event)  # Méthode SquareMap Tkinter

        # Donne le focus clavier
        self.focus_set()

        # Affiche le menu contextuel Tkinter
        try:
            self.popupMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popupMenu.grab_release()

    def curselection(self):
        """
        Retourne la sélection courante.
        """
        return self.__selection

    def GetItemCount(self):
        """
        API TaskCoach – nombre d’items.
        """
        return 0

    def isAnyItemExpandable(self):
        """
        API TaskCoach – extensibilité.
        """
        return False

    isAnyItemCollapsable = isAnyItemExpandable  # Alias API

    def GetMainWindow(self):
        """
        Retourne la fenêtre principale.
        """
        return self

    MainWindow = property(GetMainWindow)  # Propriété TaskCoach
