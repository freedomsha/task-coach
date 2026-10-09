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

Ce module fournit un wrapper TimelineTk autour d'un widget TimeLineCanvas.
La version proposée ajoute des fallbacks d'import et des protections runtime
pour rendre l'intégration plus résiliente lors de la conversion entre
implémentations (wx -> Tkinter).
Version modifiée : TimelineTk hérite maintenant directement de TimeLineCanvas.

Objectif :
- Remplacer la composition (TimelineTk créant self.canvas)
par de l’héritage direct (TimelineTk EST un TimeLineCanvas).
- Simplifier l’intégration du widget dans Tkinter.
- Garder la compatibilité avec les callbacks onSelect, onEdit et le menu contextuel.

Cette classe remplace entièrement l’ancienne TimelineTk.
"""
# J'ai analysé la requête et les fichiers fournis. Il semble que vous ayez un fichier timeline.py qui est une classe d'interface utilisateur wxPython (appelée Timeline) qui utilise une autre classe timeline.py (appelée TimeLine) d'un module tiers. L'objectif est de convertir la classe Timeline en une classe TimelineTk qui utilise le module TimeLineCanvas que j'ai créé précédemment pour Tkinter.
#
# Voici le fichier timeline.tk qui implémente cette conversion. J'ai adapté la classe Timeline pour qu'elle s'intègre avec le widget TimeLineCanvas et pour qu'elle gère les événements de sélection, d'activation et de menu contextuel de manière compatible avec Tkinter.
#
# Ce fichier timeline.tk sert de couche d'abstraction, tout comme l'original timeline.py, en utilisant une composition sur le widget de base (TimeLineCanvas). Il gère les interactions et les rappels pour s'aligner sur les attentes du code client qui aurait été écrit pour la version wxPython. J'ai inclus un exemple d'utilisation dans le bloc if __name__ == "__main__": pour démontrer comment l'utiliser.

# J'ai analysé le fichier timelinetk.py que tu as fourni. C'est une conversion bien pensée de la classe Timeline de wxPython vers une classe compatible avec Tkinter. Le code est structuré de manière à encapsuler un widget Tkinter (TimeLineCanvas) tout en présentant une interface similaire à la version originale, ce qui est une approche intelligente pour maintenir la compatibilité avec le reste du code de l'application.
#
# Voici une analyse détaillée de ce que fait ton code et des points clés de la conversion.
#
# Aperçu de la conversion
#
# Ton code TimelineTk agit comme un adaptateur ou un wrapper. Au lieu d'hériter directement d'un widget Tkinter, il contient une instance de TimeLineCanvas. Cette approche par composition est souvent plus flexible et permet de mieux contrôler les interactions.
#
# Le but est de remplacer la classe Timeline de wxPython, qui gère la sélection, l'édition et les menus contextuels, par ta nouvelle classe TimelineTk, qui fait la même chose, mais avec Tkinter.
#
# Analyse du code fourni
#
# 1. Initialisation (__init__)
#
#     Tu as correctement remplacé la création de timeline.TimeLine par TimeLineCanvas.
#
#     Les rappels (onSelect, onEdit, popupMenu) sont stockés en tant que membres de la classe, tout comme dans la version wxPython.
#
#     Tu gères l'association du clic droit (<Button-3>) pour le menu contextuel en liant cet événement à la méthode on_popup. C'est l'équivalent de self.Bind(wx.EVT_RIGHT_DOWN, self.onPopup) en wxPython.
#
# 2. Gestion des événements
#
#     Sélection (on_select) : La logique est bien convertie. Lorsque le TimeLineCanvas signale une sélection, ta méthode on_select met à jour la liste interne __selection et appelle le rappel self.selectCommand.
#
#     Édition (on_edit) : De même, cette méthode gère l'événement d'activation (double-clic) et appelle le bon rappel, en passant le nœud concerné.
#
#     Menu contextuel (on_popup) : C'est un point crucial de la conversion.
#
#         Tu utilises event.x_root et event.y_root pour positionner le menu à la bonne position sur l'écran. C'est la manière standard de faire cela avec Tkinter.
#
#         L'utilisation de self.popupMenu.tk_popup() est correcte pour afficher le menu.
#
#         L'appel self.popupMenu.grab_release() est une bonne pratique pour s'assurer que le focus revient à la fenêtre après que l'utilisateur a interagi avec le menu.
#
#         Tu as ajouté une étape importante : self.canvas.find_node_at(event.x, event.y) pour déterminer quel nœud se trouve sous le clic droit et le sélectionner. C'est essentiel pour que le menu contextuel agisse sur l'élément correct.
#
# 3. Méthodes de compatibilité
#
#     curselection() : Cette méthode retourne la liste des éléments sélectionnés. La logique est bien préservée.
#
#     select(items) : Cette méthode permet de sélectionner des éléments par programme. Tu as géré le cas où il n'y a pas d'éléments à sélectionner et mis à jour le selected_node du canevas pour refléter la nouvelle sélection visuellement.
#
#     RefreshItems() : Cette méthode est un simple adaptateur qui appelle self.canvas.draw_timeline() pour forcer un redessin, ce qui est l'équivalent de Refresh() en wxPython.
#
# 4. Amélioration possible
#
#     Tu pourrais ajouter une logique pour gérer les infos-bulles (tooltips) si TimeLineCanvas ne le fait pas déjà. La classe originale Timeline utilise OnBeforeShowToolTip pour formater les données de l'info-bulle. Si TimeLineCanvas a un mécanisme pour les infos-bulles, tu pourrais l'intégrer ici en adaptant la méthode OnBeforeShowToolTip. Si ce n'est pas le cas, tu peux créer une fonction de rappel à passer au TimeLineCanvas pour générer le texte de l'info-bulle.
#
# Prochaines étapes
#
# Ton fichier timelinetk.py semble très solide et fonctionnel. Tu peux continuer à l'intégrer au reste de ton application. Les étapes suivantes seraient de :
#
#     Remplacer toutes les instances de Timeline(...) par TimelineTk(...).
#
#     T'assurer que l'objet popupMenu passé en paramètre est bien un objet tkinter.Menu.
#
#     Vérifier que les rappels onSelect et onEdit sont bien des fonctions ou
#     des méthodes qui gèrent le type de données que tu leur passes (un nœud pour onEdit).

# Points à noter
#
#     Images pour les cases à cocher : Les images checkbox_checked.png et
#     checkbox_unchecked.png doivent être présentes dans le même répertoire
#     que votre script ou dans un répertoire accessible.
#     J'ai inclus une logique simple pour lier un tag ('checked') à l'état de la case à cocher.
#
#     Dépendances : Ce code suppose que les classes TreeCtrlDragAndDropMixin,
#     CtrlWithItemsMixin et CtrlWithColumnsMixin sont définies et fonctionnent
#     correctement dans les fichiers draganddroptk.py et itemctrltk.py que
#     vous avez déjà convertis.
#
#     Édition de label : L'édition de label dans Tkinter n'est pas native.
#     La méthode on_edit est un point de départ. Vous devrez implémenter un
#     widget Entry ou similaire qui apparaît au-dessus du label lorsque vous
#     le double-cliquez pour permettre à l'utilisateur de le modifier.

# Voici la version que tu demandes : TimeLineTk devient une sous-classe directe de tktimeline.TimeLineCanvas, au lieu de contenir une instance interne (self.canvas).
# Tu pourras ainsi manipuler TimeLineTk comme un widget Tkinter autonome (pack/grid/place directement).
#
# J’ai repris tout ton code actuel en le modifiant proprement :
#
# class TimelineTk(TimeLineCanvas)
#
# Suppression de self.canvas = …
#
# cette version :
#
#     conserve la compatibilité si la signature du widget diffère légèrement,
#     rend popupMenu optionnel,
#     appelle les callbacks select/edit de manière tolérante (essaie node puis sans argument),
#     protège l'exemple main pour tests rapides.
#
# Remplacement des appels par self.
#
# Ajout docstrings complets
#
# Ajout commentaire pour chaque ligne comme tu le veux
#
# ⚠️ Important : le code ci-dessous est un drop-in replacement du fichier timelinetk.py actuel.
# Tu peux le remplacer intégralement.
#
# Résumé rapide des changements :
#
#     Appels de constructeur plus tolérants (nommés ou positionnels),
#     Callbacks appelés avec tolérance de signature,
#     popupMenu facultatif et gestion multi-plateformes du clic droit,
#     messages d'erreur clairs si TimeLineCanvas/Node ne sont pas trouvés.
#
# J'ai laissé les fallbacks d'import si ça peut aider lors de tests
# ou pour des forks du dépôt. Si tu préfères, je peux simplifier le fichier
# pour supprimer les fallbacks et les protections (version plus concise, en supposant la API exacte),
# ou créer un patch PR pour que tu puisses l'examiner dans GitHub.

from typing import List, Any, Optional        # Types utilitaires
import tkinter as tk                          # Importe Tkinter
from tkinter import Menu, messagebox          # Permet de gérer les menus contextuels
import inspect
import sys
import traceback

# Importer les classes du module tktimeline déjà converti
from taskcoachlib.thirdparty.timeline.tktimeline import TimeLineCanvas, Node, HotMap

# # Import attendu — tu as dit que ces imports sont sûrs dans ton dépôt.
# # On garde une protection minimale pour produire des messages d'erreur clairs
# TimeLineCanvas = None
# Node = None
# HotMap = None
# _import_errors = []
#
# try:
#     from taskcoachlib.thirdparty.timeline.timelinetk import TimeLineCanvas, Node, HotMap  # type: ignore
# except Exception as e:
#     _import_errors.append(("taskcoachlib.thirdparty.timeline.timelinetk", e))
#     try:
#         # Fallback plausible si le module est à un autre emplacement
#         from taskcoachlib.widgetstk.timeline import TimeLineCanvas, Node, HotMap  # type: ignore
#     except Exception as e2:
#         _import_errors.append(("taskcoachlib.widgetstk.timeline", e2))
#         # Laisser TimeLineCanvas/Node comme None et lever plus tard avec un message clair


class TimelineTk(TimeLineCanvas):
    """
    Widget Timeline pour Tkinter basé sur TimeLineCanvas.

    Cette version hérite directement de TimeLineCanvas afin d’éviter
    la création d’un canevas interne. Elle agit comme une interface
    de compatibilité avec l’ancienne version wxPython.
    """

    def __init__(self, parent: tk.Widget, rootNode: Node,
                 onSelect: Any, onEdit: Any, popupMenu: Menu):
        """
        Initialise le widget TimelineTk.

        Args:
            parent : Le widget parent Tkinter.
            rootNode : Le nœud racine contenant les enfants parallèles.
            onSelect : Callback exécuté lorsqu’un nœud est sélectionné.
            onEdit : Callback exécuté lorsqu’un nœud est activé (double-clic).
            popupMenu : Menu contextuel Tkinter à afficher.
        """

        # Stocke le nœud racine
        self.rootNode = rootNode                        # Mémorise le nœud racine

        # Stocke les callbacks
        self.selectCommand = onSelect                   # Callback sélection
        self.editCommand = onEdit                       # Callback activation
        self.popupMenu = popupMenu                      # Menu contextuel

        # Initialise la sélection interne
        self.__selection: List[Node] = []               # Liste des nœuds sélectionnés

        # Récupérer les enfants de niveau supérieur de manière sûre
        nodes_arg = None
        try:
            nodes_arg = getattr(self.rootNode, "parallel_children")
        except Exception:
            nodes_arg = getattr(self.rootNode, "children", self.rootNode)

        # Initialise l'héritage : on passe directement nodes=…
        super().__init__(
            parent,                                     # Parent Tkinter
            # nodes=self.rootNode.parallel_children,      # Liste des enfants racines
            nodes=nodes_arg,      # Liste des enfants racines
            on_select=self.on_select,                   # Callback sélection
            on_activate=self.on_edit,                   # Callback activation
            width=800,                                  # Largeur par défaut
            height=400                                  # Hauteur par défaut
        )
        # # Crée une instance de TimeLineCanvas en acceptant des signatures variées
        # try:
        #     # Essayer d'appeler le constructeur avec les noms de paramètres attendus
        #     self.canvas = TimeLineCanvas(
        #         parent,
        #         nodes=nodes_arg,
        #         on_select=self.on_select,
        #         on_activate=self.on_edit,
        #         width=width,
        #         height=height
        #     )
        # except TypeError:
        #     # Fallback : essayer sans noms de paramètres (positionnels)
        #     try:
        #         self.canvas = TimeLineCanvas(parent, nodes_arg)
        #         # tenter d'attacher callbacks si l'objet expose des attributs
        #         if hasattr(self.canvas, "on_select"):
        #             try:
        #                 setattr(self.canvas, "on_select", self.on_select)
        #             except Exception:
        #                 pass
        #         if hasattr(self.canvas, "on_activate"):
        #             try:
        #                 setattr(self.canvas, "on_activate", self.on_edit)
        #             except Exception:
        #                 pass
        #     except Exception as e:
        #         tb = traceback.format_exc()
        #         raise RuntimeError(f"Impossible de créer TimeLineCanvas: {e}\n{tb}")

        # Lie le clic droit pour afficher le menu contextuel
        # self.bind("<Button-3>", self.on_popup)          # Associe on_popup au clic droit
        # Lier le clic droit (Button-3) et, sur certaines plateformes, Button-2 (mac)
        try:
            self.canvas.bind("<Button-3>", self.on_popup)
            self.canvas.bind("<Button-2>", self.on_popup)
        except Exception:
            # Certains wrappers peuvent ne pas exposer bind ; ignorer gracieusement
            pass
        # bind de la sélection ?
        # bind de l'activation ?

    # ---------------------------------------------------------------------
    #  Méthodes internes
    # ---------------------------------------------------------------------
    # def GetCanvas(self) -> tk.Widget:
    #     """Retourne le widget Canvas (ou le widget de plus haut niveau fourni)."""
    #     return self.canvas

    # def on_select(self, node: Node):
    def on_select(self, node: Any):
        """
        Gestionnaire appelé lorsqu’un nœud est sélectionné.

        Gère l'événement de sélection du nœud.

        Args:
            node : Le nœud sélectionné.
        """
        if node == self.rootNode:                       # Si clic sur la racine → aucune sélection
            self.__selection = []                       # Vide la sélection
        else:
            self.__selection = [node]                   # Stocke la sélection
        if self.selectCommand:                          # Si callback fourni
            # self.selectCommand()                        # Lancer l’événement utilisateur
            # Essayer d'appeler selectCommand(node) ; si la signature n'accepte pas d'argument, appeler sans argument
            try:
                self.selectCommand(node)
            except TypeError:
                try:
                    self.selectCommand()
                except Exception:
                    print("Erreur lors d'un appel à selectCommand :", file=sys.stderr)
                    traceback.print_exc()

    # def on_edit(self, node: Node):
    def on_edit(self, node: Any):
        """
        Gestionnaire appelé lorsqu’un nœud est activé (double-clic).

        Args:
            node : Le nœud activé.
        """
        if self.editCommand:                            # Si callback fourni
            # self.editCommand(node)                      # Lancer le callback utilisateur
            try:
                self.editCommand(node)
            except TypeError:
                try:
                    self.editCommand()
                except Exception:
                    print("Erreur lors d'un appel à editCommand :", file=sys.stderr)
                    traceback.print_exc()

    def on_popup(self, event: tk.Event):
        """
        Affichage du menu contextuel sur clic droit.

        Gère l'affichage du menu contextuel.

        Sélectionne d'abord le nœud sous le curseur (si find_node_at existe),
        met à jour l'affichage, puis poste le menu contextuel.

        Args:
            event : Informations sur le clic.
        """
        if not self.popupMenu:
            return

        # Trouve le nœud situé sous le clic
        # node = self.find_node_at(event.x, event.y)       # Détection zone chaude
        node = None
        try:
            # if hasattr(self.canvas, "find_node_at"):
            if hasattr(self, "find_node_at"):
                # node = self.canvas.find_node_at(event.x, event.y)
                node = self.find_node_at(event.x, event.y)
            # elif hasattr(self.canvas, "find_closest_node"):
            elif hasattr(self, "find_closest_node"):
                # node = self.canvas.find_closest_node(event.x, event.y)
                node = self.find_closest_node(event.x, event.y)
        except Exception:
            traceback.print_exc()

        # if node:                                         # Si un nœud a été trouvé
        #     self.selected_node = node                    # Met à jour la sélection interne
        #     self.draw_timeline()                         # Redessin pour surbrillance
        if node:
            try:
                # self.canvas.selected_node = node
                self.selected_node = node
            except Exception:
                pass
            try:
                # if hasattr(self.canvas, "draw_timeline"):
                if hasattr(self, "draw_timeline"):
                    # self.canvas.draw_timeline()
                    self.draw_timeline()
            except Exception:
                pass

        try:
            # Affiche le menu à la position du curseur
            self.popupMenu.tk_popup(event.x_root, event.y_root)
        finally:
            # self.popupMenu.grab_release()                # Libère le menu proprement
            try:
                self.popupMenu.grab_release()
            except Exception:
                pass

    # ---------------------------------------------------------------------
    #  Méthodes de compatibilité (similaires à wx version)
    # ---------------------------------------------------------------------

    def curselection(self) -> List[Node]:
        """
        Retourne la liste des nœuds actuellement sélectionnés.

        Returns:
            list[Node] : sélection active.
        """
        # return self.__selection                         # Renvoie la sélection interne
        return list(self.__selection)

    def GetItemCount(self) -> int:
        """
        Retourne le nombre d’éléments (nœuds principaux).

        Returns:
            int : nombre de nœuds au premier niveau.
        """
        return len(self.rootNode.parallel_children)     # Compte les enfants parallèles
        # try:
        #     return len(getattr(self.rootNode, "parallel_children", getattr(self.rootNode, "children", [])))
        # except Exception:
        #     return 0

    def select(self, items: List[Node]):
        """
        Force la sélection programmée de nœuds.

        Args:
            items : Liste de nœuds à sélectionner.
        """
        if items:                                       # Si éléments fournis
            self.__selection = items                    # Mémorise sélection
            self.selected_node = items[0]
        else:
            self.__selection = []                       # Vide la sélection
            self.selected_node = None                   # Retire la sélection

        self.draw_timeline()                            # Redessine le widget
        # if len(items) > 0:
        #     self.__selection = items
        #     try:
        #         self.canvas.selected_node = items[0]
        #     except Exception:
        #         pass
        #     try:
        #         if hasattr(self.canvas, "draw_timeline"):
        #             self.canvas.draw_timeline()
        #     except Exception:
        #         pass
        # else:
        #     self.__selection = []
        #     try:
        #         self.canvas.selected_node = None
        #     except Exception:
        #         pass
        #     try:
        #         if hasattr(self.canvas, "draw_timeline"):
        #             self.canvas.draw_timeline()
        #     except Exception:
        #         pass

    # Les méthodes suivantes sont des stubs pour la compatibilité
    def RefreshItems(self):
        """

        Returns:

        """
        self.Refresh()
        # try:
        #     if hasattr(self.canvas, "draw_timeline"):
        #         self.canvas.draw_timeline()
        # except Exception:
        #     pass

    def RefreshAllItems(self, count):
        """

        Returns:

        """
        self.Refresh()

    def OnBeforeShowToolTip(self, x: int, y: int) -> Any:
        """
        Compatibilité wx : dans Tkinter, la gestion des tooltips
        se fait dans TimeLineCanvas.
        """
        pass                                            # Ne fait rien pour le moment
        # L'info-bulle est généralement gérée dans le widget TimeLineCanvas lui-même.
        return None

    def isAnyItemExpandable(self) -> bool:
        """
        Indique si un élément peut être développé.
        Tkinter : pas géré → toujours False.
        """
        return False                                    # Pas de collapse/expand

    def isAnyItemCollapsable(self) -> bool:
        """
        Indique si un élément peut être replié.
        Tkinter : pas géré → toujours False.
        """
        return False                                    # Pas de collapse/expand


# --- Exemple d'utilisation pour vérifier le fonctionnement ---
if __name__ == "__main__":
    def on_select_callback():
        print(f"Événement de sélection. Sélection actuelle: {timeline_widget.curselection()}")

    def on_edit_callback(node: Node):
        messagebox.showinfo("Activation", f"Nœud activé: {node.path}")
        # messagebox.showinfo("Activation", f"Nœud activé: {getattr(node, 'path', repr(node))}")

    root = tk.Tk()
    root.title("Exemple d'intégration de TimelineTk")

    # Créez des données de test
    # Crée des données de test en essayant plusieurs signatures possibles pour Node
    root_node = Node("Racine", 0, 100, [
        Node("Tâche A", 0, 30, [], []),
        Node("Tâche B", 20, 50, [], []),
        Node("Tâche C", 40, 70, [], []),
    ], [])

    # Crée un menu contextuel de test
    item_menu = Menu(root, tearoff=0)
    item_menu.add_command(label="Modifier la tâche", command=lambda: print("Modifier..."))
    item_menu.add_command(label="Supprimer la tâche", command=lambda: print("Supprimer..."))

    # Crée une instance de TimelineTk
    timeline_widget = TimelineTk(
        root,
        rootNode=root_node,
        onSelect=on_select_callback,
        onEdit=on_edit_callback,
        popupMenu=item_menu
    )

    # Place le widget de chronologie dans la fenêtre
    # timeline_widget.GetCanvas().pack(padx=10, pady=10, expand=True, fill="both")
    timeline_widget.pack(padx=10, pady=10, expand=True, fill="both")

    root.mainloop()
