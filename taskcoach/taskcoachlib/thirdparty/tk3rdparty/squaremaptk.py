#!/usr/bin/env python3
"""
SquareMap – version Tkinter
Conversion complète depuis wxPython vers tkinter
"""
# Le buffering wx (wx.BufferedDC) est remplacé par un Canvas
#
# Tkinter redessine suffisamment vite → pas besoin de double buffer complexe
#
# Les événements wx personnalisés (wx.lib.newevent)
# Remplacés par :
# event_generate("<<SquareSelected>>")
# event_generate("<<SquareHighlighted>>")
# event_generate("<<SquareActivated>>")
#
# wx.Rect
# Remplacé par un tuple (x, y, w, h) + fonction contains_point()
#
# wx.Pen / wx.Brush
# Remplacés par outline=, fill=, width=

import os  # Gestion du système de fichiers
import sys  # Accès aux arguments et à la plateforme
import logging  # Journalisation
import operator  # Outils de tri
import tkinter as tk  # Interface graphique Tkinter
from tkinter import font  # Gestion des polices

# Initialisation du logger
log = logging.getLogger("squaremap")  # Logger nommé


def contains_point(rect, point):
    """
    Vérifie si un point est contenu dans un rectangle.
    """
    x, y, w, h = rect  # Décomposition du rectangle
    px, py = point  # Coordonnées du point
    return x <= px <= x + w and y <= py <= y + h  # Inclusion


class HotMapNavigator:
    """
    Classe utilitaire pour naviguer dans la hot_map.
    """

    @classmethod
    def findNode(cls, hot_map, target, parent=None):
        """Recherche un nœud dans la hot_map."""
        for index, (rect, node, children) in enumerate(hot_map):  # Parcours
            if node == target:  # Nœud trouvé
                return parent, hot_map, index  # Retour infos
            result = cls.findNode(children, target, node)  # Recherche récursive
            if result:  # Résultat trouvé
                return result
        return None  # Aucun résultat

    @classmethod
    def findNodeAtPosition(cls, hot_map, position, parent=None):
        """Trouve le nœud à une position donnée."""
        for rect, node, children in hot_map:  # Parcours
            if contains_point(rect, position):  # Si le point est dedans
                return cls.findNodeAtPosition(children, position, node)  # Descente
        return parent  # Dernier parent valide

    @staticmethod
    def firstNode(hot_map):
        """Retourne le premier nœud."""
        return hot_map[0][1]

    @classmethod
    def lastNode(cls, hot_map):
        """Retourne le dernier nœud."""
        children = hot_map[-1][2]
        return cls.lastNode(children) if children else hot_map[-1][1]

    @staticmethod
    def nextChild(children, index):
        """Retourne le frère suivant."""
        return children[min(index + 1, len(children) - 1)][1]

    @staticmethod
    def previousChild(children, index):
        """Retourne le frère précédent."""
        return children[max(0, index - 1)][1]


class SquareMap(tk.Frame):
    """
    Vue graphique de type treemap basée sur Canvas Tkinter.
    """

    def __init__(self, parent, model=None, adapter=None,
                 padding=2, margin=0, labels=True, highlight=True):
        """Initialisation du SquareMap."""
        super().__init__(parent)  # Initialisation Frame
        self.pack(fill="both", expand=True)  # Remplissage

        self.model = model  # Modèle de données
        self.adapter = adapter or DefaultAdapter()  # Adaptateur
        self.padding = padding  # Padding interne
        self.margin = margin  # Marges
        self.labels = labels  # Affichage des labels
        self.highlight = highlight  # Surbrillance

        self.selectedNode = None  # Nœud sélectionné
        self.highlightedNode = None  # Nœud survolé
        self.hot_map = []  # Carte interactive

        self.canvas = tk.Canvas(self, bg="#808080", highlightthickness=0)  # Canvas
        self.canvas.pack(fill="both", expand=True)  # Placement

        self.font = font.nametofont("TkDefaultFont")  # Police par défaut
        self.em_size = self.font.measure("m")  # Taille em

        self.canvas.bind("<Motion>", self.on_mouse_move)  # Survol
        self.canvas.bind("<ButtonRelease-1>", self.on_click)  # Clic
        self.canvas.bind("<Double-Button-1>", self.on_double_click)  # Double clic
        self.canvas.bind("<Key>", self.on_key)  # Clavier
        self.canvas.bind("<Configure>", self.on_resize)  # Redimensionnement
        self.canvas.focus_set()  # Focus clavier

        self.redraw()  # Premier dessin

    def on_resize(self, event):
        """Redessine lors d'un resize."""
        self.redraw()

    def on_mouse_move(self, event):
        """Gestion du survol."""
        node = HotMapNavigator.findNodeAtPosition(
            self.hot_map, (event.x, event.y)
        )
        self.set_highlight(node)

    def on_click(self, event):
        """Gestion clic."""
        node = HotMapNavigator.findNodeAtPosition(
            self.hot_map, (event.x, event.y)
        )
        self.set_selected(node)

    def on_double_click(self, event):
        """Gestion double clic."""
        if self.selectedNode:
            self.event_generate("<<SquareActivated>>")

    def on_key(self, event):
        """Gestion clavier."""
        if not self.selectedNode:
            return

        try:
            parent, children, index = HotMapNavigator.findNode(
                self.hot_map, self.selectedNode
            )
        except TypeError:
            return

        if event.keysym == "Home":
            self.set_selected(HotMapNavigator.firstNode(self.hot_map))
        elif event.keysym == "End":
            self.set_selected(HotMapNavigator.lastNode(self.hot_map))
        elif event.keysym == "Down":
            self.set_selected(HotMapNavigator.nextChild(children, index))
        elif event.keysym == "Up":
            self.set_selected(HotMapNavigator.previousChild(children, index))
        elif event.keysym == "Return":
            self.event_generate("<<SquareActivated>>")

    def set_selected(self, node):
        """Sélectionne un nœud."""
        if node == self.selectedNode:
            return
        self.selectedNode = node
        self.redraw()
        self.event_generate("<<SquareSelected>>")

    def set_highlight(self, node):
        """Surbrillance."""
        if node == self.highlightedNode:
            return
        self.highlightedNode = node
        self.redraw()
        self.event_generate("<<SquareHighlighted>>")

    def redraw(self):
        """Redessine la carte."""
        self.canvas.delete("all")
        self.hot_map = []
        if self.model:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            self.draw_box(self.model, 0, 0, w, h, self.hot_map)

    def draw_box(self, node, x, y, w, h, hot_map, depth=0):
        """Dessine un rectangle et ses enfants."""
        color = self.adapter.background_color(node, depth) or "#%02x%02x%02x" % (
            (depth * 10) % 255,
            (255 - depth * 5) % 255,
            (depth * 25) % 255,
        )

        outline = "white" if node == self.selectedNode else "black"

        rect_id = self.canvas.create_rectangle(
            x + self.margin,
            y + self.margin,
            x + w - self.margin,
            y + h - self.margin,
            fill=color,
            outline=outline,
            width=2 if node == self.selectedNode else 1
        )

        children_hot_map = []
        hot_map.append(((x, y, w, h), node, children_hot_map))

        if self.labels and w > self.em_size * 2 and h > self.em_size:
            self.canvas.create_text(
                x + 4,
                y + 4,
                text=self.adapter.label(node),
                anchor="nw",
                fill="white"
            )

        children = self.adapter.children(node)
        if not children:
            return

        total = self.adapter.children_sum(children, node)
        offset = 0

        for child in sorted(children, key=lambda n: self.adapter.value(n, node)):
            frac = self.adapter.value(child, node) / total if total else 0
            cw = int(w * frac)
            self.draw_box(child, x + offset, y + self.padding, cw, h - self.padding * 2, children_hot_map, depth + 1)
            offset += cw


class DefaultAdapter:
    """Adaptateur par défaut."""

    def children(self, node):
        return node.children

    def value(self, node, parent=None):
        return node.size

    def label(self, node):
        return node.path

    def children_sum(self, children, node):
        return sum(self.value(c, node) for c in children)

    def background_color(self, node, depth):
        return None


class Node:
    """Nœud simple."""

    def __init__(self, path, size, children):
        self.path = path
        self.size = size
        self.children = children


def build_model(path):
    """Construit un arbre Node depuis le filesystem."""
    children = []
    size = 0
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isfile(full):
            s = os.path.getsize(full)
            children.append(Node(full, s, []))
            size += s
        elif os.path.isdir(full):
            child = build_model(full)
            children.append(child)
            size += child.size
    return Node(path, size, children)


def main():
    """Point d’entrée."""
    if not sys.argv[1:]:
        print("Usage: squaremap.py <directory>")
        return

    root = tk.Tk()
    root.title("SquareMap – Tkinter")

    model = build_model(sys.argv[1])
    squaremap = SquareMap(root, model=model)

    root.mainloop()


if __name__ == "__main__":
    main()
