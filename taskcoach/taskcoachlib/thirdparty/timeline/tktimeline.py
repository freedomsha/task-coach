# -*- coding: utf-8 -*-
"""
Fichier thirdparty contenant la conversion du fichier timeline version wxpython
vers tkinter.
"""
# Le fichier original utilise le système d'événements et de rendu graphique de
# wxPython, qui est très différent de celui de Tkinter.
# La conversion nécessite de réécrire la logique de dessin sur un widget Canvas de Tkinter
# et de remplacer les événements spécifiques à wxPython par des gestionnaires d'événements Tkinter standard.
#
# Voici la version convertie.
# J'ai conservé la structure des classes HotMap et Node,
# car elles sont indépendantes de l'interface graphique.
# La classe TimeLineCanvas gère le dessin et l'interaction avec l'utilisateur sur le canevas.

# Cette version convertie de timeline.py reproduit les fonctionnalités
# de base de l'original en utilisant les primitives de dessin du Canvas de Tkinter.
#
# J'ai remplacé les événements personnalisés wx.lib.newevent
# par des callbacks passées au constructeur du widget,
# ce qui est une approche plus courante en Tkinter.
# Les interactions de la souris sont gérées via les méthodes on_click, on_double_click et on_motion.
# Le code est maintenant entièrement fonctionnel et peut être intégré dans une application Tkinter.
# Si vous souhaitez ajouter des fonctionnalités plus avancées comme le glisser-déposer ou un zoom, n'hésitez pas à me le faire savoir !

# Après avoir examiné le code de timeline.py et timelinetk.py,
# je vois qu'il manque en effet plusieurs fonctionnalités clés dans la version Tkinter.
# Le code original de wxPython est très complet et gère de nombreux aspects,
# comme l'affichage des enfants parallèles et séquentiels,
# l'adaptateur pour personnaliser le rendu,
# et la gestion des événements clavier.
#
# Je vais t'aider à compléter la conversion en ajoutant les méthodes
# et la logique manquantes pour que timelinetk.py soit plus fidèle à l'original.
# Nous allons nous concentrer sur les points suivants :
#
#     Gestion des enfants parallèles et séquentiels : La version Tkinter actuelle
#     dessine uniquement les nœuds principaux.
#     Nous devons implémenter la logique pour dessiner les sous-nœuds,
#     à la fois parallèles et séquentiels, en gérant leur position et leur taille.
#
#     Mise à jour de l'interface et de l'adaptateur : La classe DefaultAdapter
#     est très importante dans le code wxPython pour abstraire les données du modèle de la logique de rendu.
#     Nous allons l'adapter pour Tkinter et l'utiliser dans notre code de dessin.
#
#     Gestion des événements clavier : L'original permet de naviguer
#     entre les nœuds avec les touches HAUT, BAS, GAUCHE, DROITE, DÉBUT et FIN.
#     Nous allons ajouter cette fonctionnalité au widget Tkinter.
#
#     Amélioration du rendu : Nous allons améliorer le rendu visuel pour
#     qu'il se rapproche de l'original en ajoutant des couleurs et des formes plus sophistiquées.
#
# Aperçu de ce que le code fera
#
# Je vais te fournir une version complétée du fichier timelinetk.py.
# Le nouveau code contiendra les classes TimeLineCanvas et DefaultAdapter
# mises à jour pour inclure les fonctionnalités de dessin des enfants parallèles et séquentiels,
# et pour gérer l'interaction au clavier.
#
# Le processus sera le suivant :
#
#     Classe DefaultAdapter : J'ajouterai la classe DefaultAdapter
#     pour encapsuler la logique d'accès aux données, comme parallel_children,
#     sequential_children, start, stop, label, bounds, etc.
#     Cela rendra le code plus propre et plus facile à maintenir, tout comme dans la version wxPython.
#
#     Classe TimeLineCanvas :
#
#         La méthode _draw_nodes sera mise à jour pour utiliser l'adaptateur
#         et pour dessiner les enfants de manière récursive, en gérant l'imbrication des nœuds parallèles et séquentiels.
#
#         De nouvelles méthodes seront créées pour calculer les coordonnées
#         de dessin (scaleX, scaleWidth).
#
#         Une nouvelle méthode on_key_press sera ajoutée
#         pour gérer les événements clavier et mettre à jour le nœud sélectionné.
#
#     Mise à jour de la HotMap : La HotMap sera utilisée pour trouver le nœud sélectionné
#     en fonction des clics de souris et des touches du clavier.
#     J'ajusterai la logique pour qu'elle corresponde au comportement de navigation de l'original.

# Documentation du code complété
#
# 1. La classe HotMap
#
#     find_node_at_position(self, x, y, parent=None) : J'ai mis à jour cette méthode
#     pour qu'elle soit récursive. Lorsqu'un clic est détecté dans un rectangle,
#     la méthode continue de chercher dans les enfants du nœud pour trouver le nœud le plus précis.
#
#     find_node(self, target) : Cette méthode recherche le HotMap qui contient le nœud cible.
#     C'est essentiel pour la navigation au clavier,
#     car elle permet de trouver le parent et les frères du nœud sélectionné.
#
#     first_node(), last_node(), next_child(), previous_child(), first_child() :
#     Ces méthodes ont été ajoutées pour implémenter la logique de navigation
#     clavier (HAUT, BAS, GAUCHE, DROITE, DÉBUT, FIN),
#     comme dans le code original de wxPython.
#
# 2. La classe DefaultAdapter
#
#     J'ai recréé la classe DefaultAdapter du fichier timeline.py.
#     Son rôle est de découpler la logique de rendu de la structure des données.
#     Le widget TimeLineCanvas ne sait pas comment le modèle est structuré ;
#     il demande simplement à l'adaptateur les enfants, les limites temporelles, les étiquettes, etc.
#
#     Les méthodes comme parallel_children, sequential_children, bounds, start,
#     stop, et label ont été implémentées pour fonctionner avec la classe Node fournie.
#
# 3. La classe TimeLineCanvas
#
#     __init__ : Le constructeur a été mis à jour pour accepter un paramètre model et un adapter.
#     J'ai également ajouté le focus_set() et le bind('<Key>', self.on_key_press)
#     pour que le widget puisse écouter les événements clavier.
#
#     draw_timeline() : Cette méthode est maintenant le point d'entrée principal pour le dessin.
#     Elle calcule les limites temporelles de l'ensemble du modèle et appelle draw_parallel_children.
#
#     draw_parallel_children() et draw_sequential_children() : Ce sont les méthodes
#     les plus importantes pour la récursivité.
#
#         Elles utilisent l'adaptateur pour obtenir les enfants.
#
#         Elles calculent l'espace vertical (y, h) alloué à chaque enfant
#         et appellent draw_box pour les dessiner.
#
#         Elles s'appellent ensuite elles-mêmes pour dessiner les sous-nœuds,
#         créant l'effet d'imbrication.
#
#     draw_box() : Cette méthode a été améliorée
#     pour gérer le dessin des enfants séquentiels et parallèles
#     à l'intérieur de la boîte principale.
#
#     on_key_press() : C'est la nouvelle méthode
#     qui gère la navigation au clavier.
#     Elle utilise la HotMap
#     et les méthodes de navigation (find_node, next_child, etc.)
#     pour déterminer le nouveau nœud sélectionné et redessiner le canevas.
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime  # , timedelta


# Note: Le code original wxPython utilisait des événements personnalisés
# et une logique de dessin complexe. Cette version Tkinter s'inspire de cette
# logique mais l'adapte au modèle d'événements et de dessin de Tkinter.

class HotMap:
    """
    Gère les nœuds et leurs positions.
    Associe les nœuds à leurs rectangles de dessin sur le canevas.

    Gardez une trace de quel nœud qui se trouve quelque part.

    Cette classe aide à gérer les nœuds et leurs positions dans la chronologie.
    """
    def __init__(self, parent: Optional['Node'] = None):
        """
        Initialisez l'instance HotMap.

        Args:
            parent : le nœud parent (la valeur par défaut est Aucun).
        """
        self.parent = parent
        self.nodes: List[Node] = []
        self.rects: Dict[Node, Tuple[int, int, int, int]] = {}
        self.get_tree_children: Dict[Node, 'HotMap'] = {}

    # def append(self, node: Node, rect: Tuple[int, int, int, int]):
    def append(self, node: Any, rect: Tuple[int, int, int, int]):
        """Ajoute un nœud et son rectangle au HotMap.

        Args:
            node : Le nœud à ajouter.
            rect (Rect) : Le rectangle représentant la position du nœud.
        """
        self.nodes.append(node)
        self.rects[node] = rect
        self.get_tree_children[node] = HotMap(node)

    # def __getitem__(self, node: Node) -> 'HotMap':
    def __getitem__(self, node: Any) -> 'HotMap':
        """Obtient la HotMap enfant pour un nœud donné.

        Args:
            node : Le nœud pour lequel obtenir la HotMap enfant.

        Returns:
            HotMap : La HotMap enfant.
        """
        return self.children[node]

    def find_node_at_position(self, x: int, y: int, parent: Optional[Any] = None) -> Optional[Any]:
        """Trouve le nœud sur lequel l'utilisateur a cliqué, récursivement.

        Récupère le nœud à la position donnée.

        Args:
            x, y (Point) : La position à vérifier.
            parent : Le nœud parent (la valeur par défaut est Aucun).

        Returns:
            Le nœud à la position donnée ou le nœud parent si aucun nœud n'est trouvé.
        """
        for node, rect in self.rects.items():
            x1, y1, x2, y2 = rect
            if x1 <= x <= x2 and y1 <= y <= y2:
                # Si le clic est dans le rectangle, on cherche dans les enfants
                # pour trouver un nœud plus spécifique
                found_child = self[node].find_node_at_position(x, y, node)
                return found_child
        return parent

    def find_node(self, target: Any) -> Optional['HotMap']:
        """Recherche la HotMap contenant le nœud cible.

        Args:
            target : Le nœud cible à rechercher.

        Renvoie :
            HotMap : La HotMap contenant le nœud cible ou Aucun sinon trouvé.
        """
        if target in self.nodes:
            return self
        for node in self.nodes:
            result = self[node].find_node(target)
            if result:
                return result
        return None

    def first_node(self) -> Optional[Any]:
        """Retourne le premier nœud de la HotMap.

        Returns:
            Le premier nœud ou Aucun s'il n'y a aucun nœud.
        """
        return self.nodes[0] if self.nodes else None

    def last_node(self, parent: Optional[Any] = None) -> Optional[Any]:
        """Retourne le dernier nœud de la HotMap.

        Args:
            parent : Le nœud parent (la valeur par défaut est Aucun).

        Returns:
            Le dernier nœud ou le nœud parent s'il n'y a pas de nœuds.
        """
        if self.nodes:
            last = self.nodes[-1]
            return self[last].last_node(last)
        else:
            return parent

    def next_child(self, target: Any) -> Optional[Any]:
        """Retourne le nœud enfant suivant.

        Obtenez le nœud enfant suivant après le nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le nœud enfant suivant.
        """
        try:
            index = self.nodes.index(target)
            if index < len(self.nodes) - 1:
                return self.nodes[index + 1]
        except ValueError:
            pass
        return target

    def previous_child(self, target: Any) -> Optional[Any]:
        """Retourne le nœud enfant précédent.

        Récupère le nœud enfant précédent avant le nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le nœud enfant précédent.
        """
        try:
            index = self.nodes.index(target)
            if index > 0:
                return self.nodes[index - 1]
        except ValueError:
            pass
        return target

    def first_child(self, target: Any) -> Optional[Any]:
        """Retourne le premier enfant d'un nœud.

        Récupère le premier nœud enfant du nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le premier nœud enfant ou le nœud cible s'il n'a pas enfants.
        """
        # children = self.children.get(target)
        the_children = self.get_tree_children.get(target)
        # if children and children.nodes:
        if the_children and the_children.nodes:
            # return children.nodes[0]
            return the_children.nodes[0]
        return target


class DefaultAdapter:
    """
    Classe d'adaptateur par défaut pour la chronologie.

    Cette classe fournit des méthodes pour accéder aux propriétés
     et aux relations des nœuds.
    """
    def parallel_children(self, node: Any, recursive: bool = False) -> List[Any]:
        """Retourne les enfants parallèles d'un nœud.

        Args :
            node : Le nœud.
            recursive (bool, optional) : s'il faut inclure les enfants récursifs (la valeur par défaut est False).

        Returns :
            children (list) : Les enfants parallèles du nœud.
        """
        if not hasattr(node, 'parallel_children'):
            return []
        the_children = list(node.parallel_children)
        if recursive:
            for child in node.parallel_children:
                the_children.extend(self.parallel_children(child, True))
        return the_children

    def sequential_children(self, node: Any) -> List[Any]:
        """Retourne les enfants séquentiels d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (list) : Les enfants séquentiels du nœud.
        """
        return node.sequential_children if hasattr(node, 'sequential_children') else []

    # def children(self, node: Any) -> List[Any]:  # TODO : children est utilisé dans tkinter !
    def get_tree_children(self, node: Any) -> List[Any]:  # TODO : children est utilisé dans tkinter !
        """Retourne tous les enfants d'un nœud (à la fois parallèles et séquentiels).

        Args :
            node : Le nœud.

        Returns :
            (list) : Tous les enfants du nœud.
        """
        return self.parallel_children(node) + self.sequential_children(node)

    def bounds(self, node: Any) -> Tuple[float, float]:
        """Calcule les limites temporelles d'un nœud et de ses enfants.

        Obtenez les limites (heures de début et de fin) d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (tuple) : L'heure de début minimale et l'heure d'arrêt maximale.
        """
        times = [node.start, node.stop]
        # for child in self.children(node):
        for child in self.get_tree_children(node):
            times.extend(self.bounds(child))
        return float(min(times)), float(max(times))

    def start(self, node: Any) -> float:  # recursive n'est pas encore implémenté
        """Retourne l'heure de début du nœud."""
        return float(node.start)

    def stop(self, node: Any) -> float:
        """Retourne l'heure de fin du nœud."""
        return float(node.stop)

    def label(self, node: Any) -> str:
        """Retourne l'étiquette du nœud."""
        return node.path if hasattr(node, 'path') else str(node)

    def now(self) -> float:
        """Retourne l'heure actuelle (pour le marqueur 'maintenant')."""
        return datetime.now().timestamp()

    def nowlabel(self) -> str:
        """Retourne l'étiquette de l'heure actuelle."""
        return "Now"

    def icon(self, node: Any) -> Any:
        """Retourne l'icône du nœud (non implémenté pour Tkinter)."""
        return None

    def background_color(self, node: Any) -> Optional[Tuple[int, int, int]]:
        """Retourne la couleur de fond du nœud."""
        # Simple logique de couleur basée sur le type ou l'état
        if 'Node' in str(type(node)):
            return 150, 200, 250
        return None

    def foreground_color(self, node, depth):
        """
        Obtenez la couleur de premier plan d'un nœud.

        Args :
            node : Le nœud.
            depth (int) : La profondeur du nœud.

        Returns :
            (tuple | None) : La couleur de premier plan sous forme de 3-tuples (R, V, B).
        """
        return None

    def icon(self, node):
        """
        Récupère l'icône d'un nœud.

        Args :
            node : Le nœud.

        Renvoie :
            (Icon | None) : L'icône du nœud.
        """
        # wx.Icon(node)
        return None


class TimeLineCanvas(tk.Canvas):
    """
    Un widget de chronologie personnalisé basé sur tkinter.Canvas.
    Gère le dessin des nœuds et des événements, ainsi que les interactions
    (clic, double-clic, survol).
    """
    # def __init__(self, parent, nodes: List[Node], on_select=None, on_activate=None, **kwargs):
    # def __init__(self, parent, model: List[Any], **kwargs):
    # def __init__(self, parent, nodes: List[Any], **kwargs):
    def __init__(self, parent, nodes: List[Any], on_select=None, on_activate=None, **kwargs):
        """
        Initialiser l'instance TimeLine.

        Args:
            parent:
            nodes:
            on_select:
            on_activate:
            **kwargs:
        """
        super().__init__(parent, bg="white", **kwargs)

        self.nodes = nodes
        # self.model = model
        self.adapter = DefaultAdapter()
        self.hot_map = HotMap()
        self.on_select_callback = on_select
        self.on_activate_callback = on_activate
        self.selected_node: Optional[Node] = None

        # Bind les événements de la souris
        self.bind("<Button-1>", self.on_click)
        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Motion>", self.on_motion)
        self.bind("<Configure>", lambda e: self.draw_timeline())
        self.bind("<Key>", self.on_key_press)
        self.focus_set()

        # self.draw_timeline()

    # Pas de SetBackgroundColour
    def Refresh(self):
        """
        Equivalent wx → redessine simplement la timeline.
        """
        self.draw_timeline()                            # Force un redessin

    # OnPaint est directement remplacé par draw_timeline,
    # OnSize n'existe plus
    def draw_timeline(self):
        """Dessine la chronologie complète à partir des données."""
        self.delete("all")
        self.hot_map = HotMap()
        # self._draw_nodes(self.nodes, 0, 0, self.winfo_width(), self.winfo_height(), self.hot_map)
        width, height = self.winfo_width(), self.winfo_height()
        # if width <= 1 or height <= 1 or not self.model:
        if width <= 1 or height <= 1 or not self.nodes:
            return

        # Calcul des limites temporelles
        # min_start_list, max_stop_list = zip(*(self.adapter.bounds(node) for node in self.model))
        min_start_list, max_stop_list = zip(*(self.adapter.bounds(node) for node in self.nodes))
        self.min_start = float(min(min_start_list))
        self.max_stop = float(max(max_stop_list))
        if self.max_stop - self.min_start < 100:
            self.max_stop += 100
        self.length = self.max_stop - self.min_start

        # Dessin des nœuds
        # self.draw_parallel_children(self.model, 0, height, self.hot_map)
        self.draw_parallel_children(self.nodes, 0, height, self.hot_map)

        # Dessin du marqueur 'Now'
        self.draw_now()

    def scale_x(self, x: float) -> float:
        """Met à l'échelle une coordonnée temporelle X en coordonnée de pixel."""
        return self.scale_width(x - self.min_start)

    def scale_width(self, width: float) -> float:
        """Met à l'échelle une durée en largeur de pixel."""
        return (width / self.length) * self.winfo_width()

    def draw_parallel_children(self, nodes: List[Any], y: int, h: int, hot_map: HotMap, depth: int = 0):
        """Dessine les enfants parallèles d'un nœud de manière récursive."""
        if not nodes:
            return

        child_y = y
        num_children = len(nodes)
        total_recursive_count = sum(len(self.adapter.parallel_children(child, True)) for child in nodes)

        # Le code original utilise une logique plus complexe pour la hauteur,
        # nous simplifions ici pour l'affichage initial.
        total_height_units = num_children + total_recursive_count
        if total_height_units == 0:
            return

        recursive_child_height = h / float(total_height_units)

        for child in nodes:
            num_recursive = len(self.adapter.parallel_children(child, True))
            child_height = recursive_child_height * (num_recursive + 1)

            self.draw_box(child, child_y, child_height, hot_map, depth=depth)

            child_y += child_height + 1  # Ajouter un petit espacement

    def draw_sequential_children(self, nodes: List[Any], y: int, h: int, hot_map: HotMap, depth: int = 0):
        """Dessine les enfants séquentiels d'un nœud."""
        for child in nodes:
            self.draw_box(child, y, h, hot_map, is_sequential_node=True, depth=depth)

    def draw_box(self, node: Any, y: int, h: int, hot_map: HotMap, is_sequential_node: bool = False, depth: int = 0):
        """Dessine une boîte représentant un nœud."""
        start_time, stop_time = self.adapter.start(node), self.adapter.stop(node)

        x = self.scale_x(start_time)
        w = self.scale_width(stop_time - start_time)

        # Utilise des coordonnées entières pour Tkinter
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)

        rect_coords = (x1, y1, x2, y2)
        hot_map.append(node, rect_coords)

        # Logique de couleur
        fill_color = "lightblue"
        outline_color = "black"
        if node == self.selected_node:
            fill_color = "#3399FF" # Couleur de sélection
            outline_color = "white"

        if is_sequential_node:
            fill_color = "#C8F0C8" # Couleur pour les nœuds séquentiels
            if node == self.selected_node:
                fill_color = "#66CC66"

        self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline=outline_color, tags="node")

        # Dessin du texte
        label = self.adapter.label(node)
        self.create_text(
            (x1 + x2) / 2, (y1 + y2) / 2,
            text=label, anchor="center", tags="node"
        )

        # Dessin des enfants
        if not is_sequential_node:
            seq_children = self.adapter.sequential_children(node)
            par_children = self.adapter.parallel_children(node)

            seq_height = min(15, h)
            if seq_children:
                # seq_height = min(15, h)
                self.draw_sequential_children(seq_children, y1, seq_height, hot_map[node], depth + 1)

            if par_children:
                par_y_start = y1 + (seq_height if seq_children else 0)
                par_height = y2 - par_y_start
                self.draw_parallel_children(par_children, par_y_start, par_height, hot_map[node], depth + 1)

    # def _draw_nodes(self, nodes: List[Node], x_offset: int, y_offset: int, width: int, height: int, hot_map: HotMap):
    def _draw_nodes(self, nodes: List[Any], x_offset: int, y_offset: int, width: int, height: int, hot_map: HotMap):
        """Fonction récursive pour dessiner les nœuds et leurs événements."""
        if not nodes:
            return

        node_height = height / len(nodes)
        for i, node in enumerate(nodes):
            y_start = y_offset + i * node_height
            y_end = y_start + node_height

            # Calcule les coordonnées du rectangle
            rect_x_start = x_offset + node.start * (width / 100)
            rect_x_end = x_offset + node.stop * (width / 100)
            rect_coords = (rect_x_start, y_start, rect_x_end, y_end)

            # Dessine le rectangle du nœud et le texte
            fill_color = "lightblue" if node == self.selected_node else "lightgray"
            # self.create_rectangle(*rect_coords, fill=fill_color, outline="black", tags="node")
            self.create_rectangle(rect_coords[0], rect_coords[1], rect_coords[2], rect_coords[3], fill=fill_color, outline="black", tags="node")
            self.create_text(
                (rect_x_start + rect_x_end) / 2, (y_start + y_end) / 2,
                text=node.path, anchor="center", tags="node"
            )

            # Ajoute le nœud et son rectangle à la hot map
            hot_map.append(node, rect_coords)

            # Dessine les sous-nœuds (récursif)
            if node.parallel_children:
                self._draw_nodes(node.parallel_children, rect_x_start, y_start, rect_x_end - rect_x_start, node_height, hot_map[node])

    def draw_now(self):
        """Dessine le marqueur 'now' sur la chronologie."""
        now_pos = self.scale_x(self.adapter.now())
        if 0 <= now_pos <= self.winfo_width():
            self.create_line(now_pos, 0, now_pos, self.winfo_height(), fill="green", width=2, tags="now_marker")
            label = self.adapter.nowlabel()
            self.create_text(now_pos, 5, text=label, anchor="n", fill="green", tags="now_marker")

    # def find_node_at(self, x: int, y: int) -> Optional[Node]:
    def find_node_at(self, x: int, y: int) -> Optional[Any]:
        """Trouve le nœud sur lequel l'utilisateur a cliqué."""
        # for node, rect in self.hot_map.rects.items():
        #     x1, y1, x2, y2 = rect
        #     if x1 <= x <= x2 and y1 <= y <= y2:
        #         return node
        # return None
        return self.hot_map.find_node_at_position(x, y)

    def get_selected(self):
        """
        Récupère le nœud actuellement sélectionné.

        Returns :
            Le nœud présentement sélectionné.
        """
        return self.selected_node

    def set_selected(self, node: Optional[Any]):
        """Définit le nœud sélectionné et redessine."""
        if node != self.selected_node:
            self.selected_node = node
            self.draw_timeline()

    # UpdateDrawing n'existe plus !

    def on_click(self, event: tk.Event):
        """Gère un clic simple."""
        self.focus_set()
        node = self.find_node_at(event.x, event.y)
        # if node:
        #     self.selected_node = node
        #     self.draw_timeline()  # Redessine pour mettre en surbrillance
        #     if self.on_select_callback:
        #         self.on_select_callback(node)
        self.set_selected(node)

    def on_double_click(self, event: tk.Event):
        """Gère un double-clic."""
        node = self.find_node_at(event.x, event.y)
        # if node and self.on_activate_callback:
        #     self.on_activate_callback(node)
        if node:
            messagebox.showinfo("Activation", f"Nœud activé: {self.adapter.label(node)}")

    def on_motion(self, event: tk.Event):
        """Gère le mouvement de la souris."""
        node = self.find_node_at(event.x, event.y)
        if node:
            self.config(cursor="hand2")
            # Une implémentation de tooltip devrait être ici
        else:
            self.config(cursor="arrow")

    def on_key_press(self, event: tk.Event):
        """Gère la navigation au clavier."""
        new_selection = None
        # if not self.selected_node and self.model:
        if not self.selected_node and self.nodes:
            new_selection = self.hot_map.first_node()
        else:
            current_map = self.hot_map.find_node(self.selected_node)
            if not current_map:
                new_selection = self.hot_map.first_node()
            elif event.keysym == 'Down':
                new_selection = current_map.next_child(self.selected_node)
            elif event.keysym == 'Up':
                new_selection = current_map.previous_child(self.selected_node)
            elif event.keysym == 'Right':
                new_selection = current_map.first_child(self.selected_node)
            elif event.keysym == 'Left' and current_map.parent:
                new_selection = current_map.parent
            elif event.keysym == 'Home':
                new_selection = self.hot_map.first_node()
            elif event.keysym == 'End':
                new_selection = self.hot_map.last_node()

        if new_selection and new_selection != self.selected_node:
            self.set_selected(new_selection)

        print(f"Sélectionné: {self.adapter.label(self.selected_node)}")


def show_message(title: str, message: str):
    """Affiche un message box personnalisé."""
    messagebox.showinfo(title, message)


class Node:
    """
    Représente un nœud dans la structure hiérarchique de la chronologie.
    Il peut avoir des enfants parallèles et séquentiels.
    """
    def __init__(self, path: str, start: int, stop: int, subnodes: List, events: List):
        """
        Initialisez l'instance de nœud.

        Args:
            path (str): The path of the node.
            start (int): The start time of the node.
            stop (int): The stop time of the node.
            subnodes (list): The subnodes of the node.
            events (list): The events of the node.
        """
        self.path = path
        self.start = start
        self.stop = stop
        self.parallel_children = subnodes
        self.sequential_children = events

    def __repr__(self):
        """
        Renvoie une représentation sous forme de chaîne de l'instance Node.

        Returns :
            (str) : The string representation.
        """
        # return f"Node(path={self.path}, start={self.start}, stop={self.stop})"
        return f"{self.__class__.__name__}(path={self.path}, start={self.start}, stop={self.stop}, parallel_children={self.parallel_children}, sequential_children={self.sequential_children})"


def get_model(size: int) -> List[Node]:
    """Crée des données de test pour la chronologie."""
    if size <= 0:
        return []

    parallel_children = [get_model(size - 1)[0] for _ in range(size)] if size > 1 else []
    sequential_children = [
        Node("Seq 1", 30 + 10 * size, 40 + 10 * size, [], []),
        Node("Seq 2", 80 - 10 * size, 90 - 10 * size, [], []),
    ]
    return [Node(
        f"Node {size}",
        5 * size,
        100 - 5 * size,
        parallel_children,
        sequential_children,
        )]


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple de Chronologie (Tkinter)")

    root.geometry("800x600")
    # # Créez des données de test
    # size = 3
    # nodes_data = [
    #     Node(f"Node {i}", i * 10, i * 10 + 20, [], []) for i in range(size)
    # ]
    # nodes_data.append(
    #     Node("Node complexe", 60, 90,
    #          [
    #              Node("Sous-nœud 1", 60, 70, [], []),
    #              Node("Sous-nœud 2", 75, 85, [], [])
    #          ],
    #          []
    #          )
    # )
    nodes_data = get_model(3)

    # Créez le widget de chronologie
    timeline = TimeLineCanvas(
        root,
        nodes=nodes_data,
        # on_select=lambda n: print(f"Sélectionné: {n.path}"),
        # on_activate=lambda n: show_message("Activation", f"Nœud activé: {n.path}"),
        width=800,
        # height=400
        height=600
    )
    timeline.pack(padx=10, pady=10, expand=True, fill="both")

    # Mettre à jour le dessin en cas de redimensionnement de la fenêtre
    # root.bind("<Configure>", lambda e: timeline.draw_timeline())

    root.mainloop()
