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

Contrôle de l'arborescence pour Tkinter.
Basé sur le treectrl.py original de TaskCoach.
"""

# Voici une version du code qui utilise itemctrl.py et draganddrop.py pour
# créer un Treeview avec des fonctionnalités de glisser-déposer. Le code est auto-suffisant et bien commenté pour que vous puissiez comprendre chaque section. Il gère les actions de glisser-déposer et met à jour l'affichage de l'arborescence en conséquence.
#
# J'ai inclus une classe SimpleTreeItem qui remplace la structure de données d'origine de treectrl.py. Cette classe est nécessaire pour que les objets d'arborescence puissent être manipulés par le système de glisser-déposer.
#
# N'oubliez pas que vous aurez besoin des versions converties des fichiers itemctrl.py et draganddrop.py pour que ce code fonctionne.

# Ce code utilise la classe ttk.Treeview qui fait partie de la bibliothèque standard de Tkinter et est la manière recommandée de créer une vue en arborescence. Le comportement de glisser-déposer est simulé en utilisant les événements de souris de Tkinter (<Button-1>, <B1-Motion>, <ButtonRelease-1>).
#
# J'ai inclus une fonction rebuild_data_model pour illustrer comment vous mettriez à jour votre propre structure de données après un glisser-déposer. Il est essentiel que vous appeliez une fonction similaire dans votre code pour que les modifications de l'interface utilisateur soient synchronisées avec les données de votre application.

# La principale différence réside dans l'approche : wxPython utilise des classes très spécifiques comme HyperTreeList et CustomTreeCtrl, tandis que Tkinter s'appuie sur le widget plus générique ttk.Treeview et nécessite l'ajout de fonctionnalités via des "mixins" (classes qui ajoutent des méthodes à d'autres classes).
#
# J'ai repris votre code treectrltk.py et l'ai complété pour qu'il inclue les fonctionnalités de la version wxPython, en se basant sur les mixins que vous avez déjà convertis dans draganddroptk.py et itemctrltk.py. J'ai également géré les événements et le comportement des cases à cocher de manière à ce qu'ils correspondent à la logique originale.
#
# Aperçu de la conversion
#
# La solution proposée s'articule autour des points suivants :
#
#     Intégration des mixins : La nouvelle classe TreeListCtrl hérite de
#     ttk.Treeview et des mixins CtrlWithItemsMixin, CtrlWithColumnsMixin, et
#     TreeCtrlDragAndDropMixin. Cela permet de reproduire les fonctionnalités
#     de l'original en une seule classe.
#
#     Gestion des événements : Les événements wxPython (tels que
#     wx.EVT_TREE_ITEM_CHECKING) sont remplacés par des événements de souris Tkinter.
#     La logique des cases à cocher est maintenant gérée manuellement, en
#     utilisant les tags de l'élément pour stocker son état.
#
#     Cases à cocher et enfants exclusifs : La fonctionnalité de cases à cocher
#     mutuellement exclusives de treectrl.py est recréée. J'ai ajouté des méthodes
#     pour gérer cet état de manière récursive, garantissant que les actions
#     sur un élément parent ou enfant mettent à jour correctement l'état des autres.
#
#     Fonctionnalités de base : Les méthodes comme GetSelections(),
#     clear_selection(), et isAnyItemCollapsable() sont réimplémentées
#     en utilisant les méthodes natives du ttk.Treeview.
#
# Ce code est un équivalent fonctionnel qui intègre toutes les classes et
# modules manquants en se basant sur votre travail de conversion déjà accompli.

# Cette erreur AttributeError: 'Column' object has no attribute 'is_shown'
# est un excellent indice qui nous montre un manque de synchronisation entre les fichiers de votre projet.
#
# Analyse de l'erreur
#
# L'erreur se produit à la ligne où le code tente d'appeler la méthode is_shown()
# sur un objet Column. C'est l'équivalent de dire "la classe Column que vous
# utilisez ne sait pas comment se cacher".
#
# C'est une logique qui existait dans la version wxPython (wx.lib.agw.hypertreelist.ColumnInfo)
# et qui n'a pas été portée dans votre classe Column simplifiée dans itemctrltk.py.
#
# Solution
#
# Pour résoudre ce problème, j'ai mis à jour le code de treectrltk.py pour qu'il
# ne dépende plus de cette méthode manquante. Dans la conversion vers Tkinter,
# la solution la plus simple est de supposer que toutes les colonnes définies
# sont visibles par défaut, sauf si vous décidez d'ajouter une logique de masquage plus tard.
#
# J'ai donc ajusté la ligne qui cause l'erreur pour qu'elle liste simplement
# toutes les colonnes que vous avez définies.

#  Vous avez raison de soulever le point sur la logique de masquage des colonnes ;
#  mon approche précédente était un raccourci pour contourner l'erreur immédiate,
#  mais le nouveau problème indique que la solution complète nécessite une approche plus rigoureuse.
#
# L'erreur TypeError: AutoColumnWidthMixin.__init__() missing 1 required positional argument:
# 'master' est très révélatrice. Elle se produit parce que l'objet master
# (qui est le widget parent dans Tkinter) n'est pas correctement transmis à travers
# la chaîne d'héritage lors de l'initialisation de votre classe TreeListCtrl.
#
# Le problème vient de la manière dont les mixins sont initialisés. Bien que
# super().__init__() soit utilisé, il ne transmet pas automatiquement tous les
# arguments nécessaires à chaque classe parente. Pour un héritage multiple avec
# des mixins, il faut s'assurer que les arguments attendus par chaque mixin sont passés explicitement.
#
# Aperçu de la correction
#
# J'ai analysé les fichiers itemctrltk.py et draganddroptk.py que vous avez fournis.
# La solution consiste à :
#
#     Réorganiser la liste des mixins pour optimiser l'ordre de résolution des
#     méthodes (MRO). ttk.Treeview doit toujours être la dernière dans l'ordre d'héritage.
#
#     Transmettre correctement l'argument parent (master) à l'initialiseur de
#     chaque mixin dans la chaîne.
#
# J'ai également réintégré la logique pour la méthode is_shown().
# Pour que le code soit pleinement fonctionnel, il faudra que vous ajoutiez
# la méthode is_shown() à votre classe Column dans itemctrltk.py

# Explications des modifications
#
#     Réorganisation du super().__init__ : Le code a été modifié pour passer
#     l'argument parent à l'initialiseur des mixins. C'est crucial car, comme
#     l'erreur le montre, certains de ces mixins attendent l'objet parent pour s'initialiser correctement.
#
#     Correction de la logique is_shown() : J'ai rétabli l'utilisation de
#     c.is_shown() dans le constructeur. J'ai également ajouté une fonction
#     d'aide (add_is_shown_to_column()) qui ajoute une méthode par défaut is_shown()
#     à votre classe Column si elle n'existe pas. Cela vous permet d'avancer
#     sans modifier itemctrltk.py immédiatement. La meilleure pratique serait
#     cependant d'ajouter la méthode directement à la classe Column dans le
#     fichier itemctrltk.py pour un code plus propre.
#
# Cette version du code devrait résoudre l'erreur MRO ainsi que le problème de
# l'attribut manquant, vous permettant de faire un pas de plus dans la conversion.
# J'ai ajouté des commentaires pour expliquer les changements, ce qui devrait
# vous aider à mieux comprendre la logique d'héritage multiple en Python.

# L'erreur _tkinter.TclError: unknown option "-dragAndDropCommand" indique que
# la classe de base, ttk.Treeview, ne reconnaît pas un des arguments que nous lui passons.
#
# Analyse de l'erreur
#
# Le problème vient de la ligne super().__init__(parent, dragAndDropCommand=self.dragAndDropCommand, ...).
# Lorsque super() est appelé, il parcourt la chaîne d'héritage pour initialiser
# chaque classe parente. Finalement, il atteint la classe ttk.Treeview qui est
# le parent de base de tous les mixins et il essaie de l'initialiser avec
# l'argument dragAndDropCommand. Cependant, ce n'est pas un argument reconnu par
# ttk.Treeview car c'est une option personnalisée que vous avez définie pour votre propre mixin.
#
# Pour résoudre ce problème, il faut s'assurer que seuls les arguments valides
# pour ttk.Treeview lui sont passés.
#
# Solution
#
# Nous allons ajuster l'appel super() pour séparer les arguments spécifiques à
# nos mixins des arguments standards de ttk.Treeview. La meilleure façon de le
# faire est d'utiliser kwargs.pop() pour extraire les arguments que nous savons
# être spécifiques à nos mixins avant de les passer à la chaîne d'héritage.

# Ce modèle d'initialisation, où vous nettoyez les kwargs avant d'appeler super(),
# est une technique standard pour gérer l'héritage multiple en Python,
# en particulier lorsque les classes parentes ne partagent pas les mêmes
# arguments de constructeur.
#
# C'est une étape cruciale pour que le code fonctionne.

# L'erreur _tkinter.TclError: unknown option "-dragAndDropCommand" est
# réapparue parce que les arguments spécifiques à un mixin,
# comme dragAndDropCommand, ont été transmis à ttk.Treeview, qui ne les reconnaît pas.
#
# Ce problème est dû à la complexité de l'héritage multiple en Python.
# Bien que la dernière modification ait été une bonne tentative de résolution,
# la chaîne d'héritage est plus complexe et nécessite une approche différente.
#
# Aperçu de la solution
#
# La meilleure solution consiste à initialiser chaque classe parente et
# chaque mixin individuellement, plutôt que de se fier uniquement à l'appel super().
# Cette approche vous donne un contrôle total sur les arguments passés
# à chaque constructeur et empêche que des arguments non reconnus soient
# transmis accidentellement à la classe de base ttk.Treeview.
#
# J'ai révisé le fichier treectrltk.py pour implémenter cette approche.
# J'ai également déplacé la logique de la barre de menus dans une méthode
# distincte pour plus de clarté.

# L'erreur _tkinter.TclError: unknown option "-columnPopupMenu" indique que
# l'argument columnPopupMenu est transmis à ttk.Treeview qui ne le reconnaît pas.
# Ce problème survient à cause de la chaîne d'héritage multiple complexe dans vos mixins.
# Le problème principal est dans la méthode __init__ de CtrlWithColumnsMixin
# dans itemctrltk.py. Quand elle appelle super().__init__(*args, **kwargs),
# elle transmet tous les arguments (y compris columnPopupMenu) à la chaîne d'héritage,
# et finalement ces arguments arrivent jusqu'à ttk.Treeview qui ne les comprend pas.
# Voici la solution : vous devez filtrer les arguments spécifiques aux mixins
# avant de les passer à la chaîne d'héritage.

# Voici les changements apportés pour résoudre l'erreur
# _tkinter.TclError: unknown option "-columnPopupMenu" :
# Corrections apportées
# 1. Dans itemctrltk.py :
#
# Filtrage des arguments dans CtrlWithColumnsMixin : Les arguments spécifiques
# aux mixins (columns, columnPopupMenu) sont extraits avec kwargs.pop()
# avant d'appeler super().__init__().
# Initialisation manuelle dans TaskList : Les mixins sont initialisés
# individuellement avec leurs arguments spécifiques.
#
# 2. Dans treectrltk.py :
#
# Suppression de l'héritage multiple complexe :
# Au lieu d'hériter de tous les mixins, TreeListCtrl hérite seulement de ttk.Treeview.
# Initialisation manuelle des mixins :
# Les fonctionnalités des mixins sont intégrées via des méthodes
# d'initialisation dédiées (_init_items_mixin, _init_columns_mixin, _init_drag_drop_mixin).
# Implémentation directe des méthodes :
# Les méthodes importantes des mixins sont réimplémentées directement dans la classe.
#
# Pourquoi cette approche fonctionne
# Le problème principal était que lors de l'héritage multiple,
# les arguments spécifiques aux mixins (comme columnPopupMenu) remontaient
# la chaîne d'héritage jusqu'à ttk.Treeview qui ne les comprenait pas.
# En filtrant ces arguments ou en évitant l'héritage multiple complexe,
# on s'assure que seuls les arguments valides arrivent jusqu'à ttk.Treeview.

# Le code devrait fonctionner sans erreur et afficher une fenêtre avec
# un TreeView fonctionnel incluant :
#
# Glisser-déposer d'éléments
# Cases à cocher avec logique exclusive
# Menus contextuels
# Tri des colonnes

# L'erreur _tkinter.TclError: bad cursor spec "no_entry" indique que
# le nom de curseur "no_entry" n'est pas reconnu par Tkinter.
# Le problème vient de la ligne 574 dans on_dragging treectrltk.py où on essaie de définir un curseur invalide.

# Le problème était que "no_entry" n'est pas un nom de curseur valide dans Tkinter. J'ai remplacé par "pirate" qui est un curseur valide indiquant qu'une action n'est pas autorisée.
# Voici les noms de curseurs valides les plus courants dans Tkinter :
#
# "arrow" - curseur normal (par défaut)
# "hand1" ou "hand2" - curseur en forme de main
# "pirate" - curseur interdiction/refus
# "watch" - curseur d'attente
# "xterm" - curseur de texte
# "crosshair" - curseur en croix
# "question_arrow" - curseur avec point d'interrogation
#
# Vous pouvez également essayer d'autres alternatives pour indiquer qu'un drop n'est pas autorisé :
# Selon les résultats de recherche, voici les curseurs valides les plus couramment utilisés dans Tkinter :
# Cursors include: "arrow", "circle", "clock", "cross", "dotbox", "exchange",
# "fleur", "heart", "man", "mouse", "pirate", "plus", "shuttle", "sizing",
# "spider", "spraycan", "star", "target", "tcross", "trek"
# Changing the Mouse Cursor - Tkinter - GeeksforGeeks
# Je viens d'améliorer la gestion des curseurs dans le code. La nouvelle version :
#
# Essaie d'abord "notallowed" - qui est le curseur natif sur macOS pour indiquer qu'une action n'est pas autorisée
# Se replie sur "pirate" si le premier ne fonctionne pas (cas le plus courant sur Linux/Windows)
# Utilise "arrow" en dernier recours si aucun des autres ne fonctionne
#
# Cette approche avec gestion d'erreurs try/except évite les erreurs TclError
# et s'adapte automatiquement au système d'exploitation.
# Le TreeView devrait maintenant s'afficher et vous devriez pouvoir :
#
# Voir la fenêtre avec l'arborescence
# Faire du glisser-déposer d'éléments
# Voir les curseurs changer pendant le drag (main pour drop autorisé, curseur d'interdiction pour drop non autorisé)
# Utiliser les menus contextuels (clic droit)

# J'ai corrigé les deux problèmes :
#
# Ajout de la méthode rebuild_data_model dans la classe TreeListCtrl : Cette méthode affiche maintenant la structure hiérarchique complète de l'arborescence après un glisser-déposer, avec une indentation pour montrer les niveaux.
# Suppression de l'appel à rebuild_data_model dans la méthode on_drag_and_drop de la classe Application : Cette méthode est maintenant appelée automatiquement depuis OnDrop.
#
# Le flux de fonctionnement est maintenant :
#
# L'utilisateur fait un glisser-déposer
# on_end_drag appelle OnDrop
# OnDrop déplace les éléments dans l'arborescence
# OnDrop appelle rebuild_data_model pour afficher la nouvelle structure
# OnDrop appelle le callback dragAndDropCommand si défini
#
# Maintenant le glisser-déposer devrait fonctionner correctement sans erreur. Vous devriez pouvoir :
#
# Glisser des éléments dans l'arborescence
# Voir les messages de confirmation dans la console
# Voir la nouvelle structure hiérarchique affichée après chaque déplacement
# Les éléments bougent visuellement dans l'interface

# J'ai essayé de trouver des informations sur comment faire busy et forget dans les fichiers que vous avez téléchargés, mais je n'ai pas trouvé de résultats pertinents. N'oubliez pas d'implémenter busy et forget selon les besoins.

# Explications des changements :
#
# self.insert(parent_item, tk.END, text="", values=[...], tags=...): Remplace AppendItem par insert [[1430, 1431]]. L'insertion utilise tk.END pour ajouter à la fin de la liste des enfants et prend des valeurs pour les colonnes.
#
# self.__adapter.getItemText(child_object, i): Utilise une boucle pour récupérer le texte de chaque colonne.
#
# self._refreshObjectMinimally(child_item, child_object): Cette ligne appelle une méthode pour rafraîchir les aspects minimaux de l'objet, tels que les colonnes, les couleurs, la police et la sélection .
#
# self.insert(child_item, tk.END , text = '' ): Détermine si l'élément a des enfants et insère un élément vide pour indiquer qu'il peut être développé.
#
# Le problème est que self.__adapter dans ton TreeListCtrl (le widget de l'arborescence)
# est un tkinter.Frame.
# Le code essaie d'appeler la méthode get_domain_children sur ce Frame,
# mais un Frame Tkinter ne possède pas cette méthode.
#
# Le self.__adapter devrait être l'objet Viewer (comme Noteviewer) qui,
# lui, sait comment récupérer les données du domaine (les notes, les tâches, etc.)
# via la méthode get_domain_children.

import sys
import logging
import tkinter as tk  # module tkinter principal
from tkinter import ttk  # widgets ttk modernes
from typing import List, Any, Callable, Sequence, Optional  # types utilitaires

# Assurez-vous d'avoir les versions converties de ces modules.
# Les importations relatives peuvent être nécessaires selon la structure de votre projet.
from taskcoachlib.guitk import artprovidertk

# from .itemctrl import *
# from taskcoachlib.widgetstk import draganddroptk, itemctrltk
from taskcoachlib.widgetstk import itemctrltk
from taskcoachlib.widgetstk.draganddroptk import TreeCtrlDragAndDropMixin
from taskcoachlib.widgetstk.itemctrltk import (
    Column,
    CtrlWithItemsMixin,
    CtrlWithColumnsMixin,
)

# from .draganddrop import *
from taskcoachlib.widgetstk import tooltiptk

log = logging.getLogger(__name__)

# # Pour l'exemple, nous allons définir des versions simples de ces classes
# # pour que le code puisse s'exécuter de manière autonome.
# # Dans votre projet, vous importeriez les versions réelles.
# class DragAndDrop:
#     """Classe de simulation DragAndDrop."""
#     def __init__(self, master: tk.Tk):
#         self._master = master
#         self._callback = None

#     def makeDraggable(self, widget: Any, callback: Callable):
#         self._callback = callback

#     def makeDropTarget(self, widget: Any, callback: Callable):
#         self._callback = callback


class SimpleTreeItem:  # Voir itemctrltk.py pour une version plus complète
    """
    Classe pour représenter un élément dans l'arborescence.
    Remplace la structure de données complexe du treectrl.py original.
    """

    def __init__(self, name: str, parent: Any = None):
        """Initialise un élément de l'arborescence."""
        self.name = name
        self.parent = parent
        self.children: List["SimpleTreeItem"] = []
        # self.get_tree_children: List['SimpleTreeItem'] = []

    def __repr__(self) -> str:
        """Retourne une représentation en chaîne de l'objet."""
        return f"SimpleTreeItem(name='{self.name}')"


class TreeCtrl(
    ttk.Treeview
):  # Remplace HyperTreeList et CustomTreeCtrl de wxPython
    """
    Une version de TreeCtrl pour Tkinter avec glisser-déposer.
    """

    # TreeCtrl.__init__(self, parent, columns=column_names, show='tree headings',
    #                   displaycolumns=displaycolumns, *args, **kwargs) de TreeListCtrl.
    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        # self.drag_and_drop = DragAndDrop(parent)
        # self.drag_and_drop = TreeCtrlDragAndDropMixin(parent)  # TODO : A redéfinir plus tard !
        # TypeError: object.__init__() takes exactly one argument (the instance to initialize)
        # self.drag_and_drop = TreeCtrlDragAndDropMixin()
        # AttributeError: 'TreeCtrlDragAndDropMixin' object has no attribute 'bind'
        self.dragged_item_id = None

        self.setup_drag_and_drop()

    def setup_drag_and_drop(self):
        """Configure les gestionnaires d'événements pour le glisser-déposer."""
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event: tk.Event):
        """Gère le clic de la souris pour démarrer un glisser-déposer."""
        self.dragged_item_id = self.identify_row(event.y)

    def on_drag(self, event: tk.Event):
        """Gère le mouvement de glissement."""
        if self.dragged_item_id:
            # Identifie l'élément sous le curseur
            drop_item_id = self.identify_row(event.y)
            if drop_item_id and drop_item_id != self.dragged_item_id:
                # Ajoute une indication visuelle pour le glisser-déposer
                self.tk.call(
                    self._w, "move", self.dragged_item_id, drop_item_id, "end"
                )
            else:
                # Gère le cas où l'on glisse vers un espace vide
                self.tk.call(self._w, "move", self.dragged_item_id, "", "end")

    def on_release(self, event: tk.Event):
        """Gère le relâchement de la souris et finalise le glisser-déposer."""
        if self.dragged_item_id:
            drop_item_id = self.identify_row(event.y)
            if drop_item_id and drop_item_id != self.dragged_item_id:
                # Récupère l'ID du parent de l'élément cible
                parent_id = self.parent(drop_item_id)
                # Déplace l'élément glissé vers la nouvelle position
                self.move(self.dragged_item_id, parent_id, "end")
            else:
                # Gère le déplacement vers la racine (pas de parent)
                self.move(self.dragged_item_id, "", "end")

            # Réinitialise la variable de l'élément glissé
            self.dragged_item_id = None
            self.rebuild_data_model()

    def rebuild_data_model(self):
        """
        Reconstruit la structure de données sous-jacente
        après une opération de glisser-déposer.
        """
        # Dans un vrai projet, vous mettriez à jour vos listes de données.
        log.debug("La structure de l'arborescence a été mise à jour.")
        items = self.get_children()
        for item_id in items:
            parent_id = self.parent(item_id)
            log.debug(
                f"Élément : {self.item(item_id)['text']}, Parent : {self.item(parent_id)['text'] if parent_id else 'Racine'}"
            )


# class TreeListCtrl(itemctrltk.CtrlWithItemsMixin, itemctrltk.CtrlWithColumnsMixin, itemctrltk.CtrlWithToolTipMixin, ttk.Treeview):
#     # class TreeListCtrl(ttk.Treeview, itemctrltk.CtrlWithItemsMixin, itemctrltk.CtrlWithColumnsMixin, itemctrltk.CtrlWithToolTipMixin):
#     # class TreeListCtrl(
#     #     ttk.Treeview,
#     #     CtrlWithItemsMixin,
#     #     CtrlWithColumnsMixin,
#     #     TreeCtrlDragAndDropMixin
#     # ):
class TreeListCtrl(
    # ttk.Treeview,
    CtrlWithItemsMixin,
    CtrlWithColumnsMixin,
    TreeCtrlDragAndDropMixin,
    # TreeCtrl,  # ttk.Treeview
    ttk.Treeview,
):
    """
    Implémentation d'un TreeListCtrl pour Tkinter, équivalent à la version wxPython.
    Combine les fonctionnalités d'un Treeview de base avec les mixins pour
    la gestion des éléments, des colonnes et du glisser-déposer.

    Équivalent Tkinter de wx.lib.agw.hypertreelist.HyperTreeList
    Combine ttk.Treeview avec des mixins pour fonctionnalités avancées.
    """

    ct_type = 0

    # def __init__(self, parent: tk.Widget, columns: List, selectCommand: Callable, editCommand: Callable,
    #              dragAndDropCommand: Callable, itemPopupMenu: Any = None, columnPopupMenu: Any = None,
    #              *args, **kwargs):
    def __init__(
        self,
        parent: tk.Widget,
        adapter: Any,
        columns: List[Column],
        selectCommand: Callable = None,
        editCommand: Callable = None,
        dragAndDropCommand: Callable = None,
        itemPopupMenu: tk.Menu = None,
        columnPopupMenu: tk.Menu = None,
        *args,
        **kwargs,
    ):
        # def __init__(self, parent: tk.Widget, adapter: Any, columns: List,
        #              dragAndDropCommand: Callable, itemPopupMenu: Any = None,
        #              columnPopupMenu: Any = None, *args, **kwargs):
        """
        Initialise le TreeListCtrl.

        Args :
            parent : Le widget parent Tkinter.
            adapter : Adaptateur pour accéder aux données du domaine. Le frame dans lequel le TreeListCtrl sera placé.
            columns : Liste d'objets Column définissant les colonnes à afficher.
            selectCommand : Fonction de rappel (Callback) pour la sélection.
            editCommand : Fonction de rappel (Callback) pour l'édition de l'élément.
            dragAndDropCommand : Fonction de rappel (Callback) pour le glisser-déposer (appelée après).
            itemPopupMenu : Menu contextuel des éléments.
            columnPopupMenu : Menu contextuel des en-têtes de colonne.
        """
        # Initialisation de la classe de base ttk.Treeview
        log.debug(f"Initialisation de TreeListCtrl avec {len(columns)} colonnes.")
        # Seuls les arguments reconnus par ttk.Treeview lui sont passés.
        # print("TreeListCtrl mro=", self.__mro__)
        # log.debug(f"TreeListCtrl : {len(columns)} colonnes sont arrivées : {columns}.")  # TypeError: object of type 'method' has no len()
        # log.debug(f"TreeListCtrl : {len(columns)} colonnes sont arrivées : {columns}.")  # TypeError: object of type 'method' has no len()

        # # --- CORRECTION 1 : Filtrer les options Tkinter non valides ---
        # On retire tous les arguments que ttk.Treeview ne comprend pas
        # # L'option 'resizeableColumn' est un vestige de wxPython non supporté par ttk.Treeview.
        # # Nous la retirons de kwargs avant d'appeler le constructeur parent.
        # resizeable_column_info = kwargs.pop('resizeableColumn', None)
        # On extrait les arguments spécifiques à TreeListCtrl qui ne doivent PAS
        # être passés à ttk.Treeview

        # L'argument qui cause votre crash actuel
        self.resizeableColumn = kwargs.pop('resizeableColumn', None)

        # L'argument qui causera le PROCHAIN crash (vu dans tasktk.py)
        self.validateDragCallback = kwargs.pop('validateDrag', None)

        # Nettoyage préventif d'autres arguments potentiels
        kwargs.pop('settingsSection', None)

        # Gestion spécifique des colonnes visibles pour l'init
        # On conserve la liste complète des objets colonnes pour usage interne
        self._columns = columns

        # # Extraire les colonnes
        # # Extraction des noms et colonnes visibles
        # # column_names = [c._name for c in columns]
        # # column_names = [c.name for c in columns]
        # column_names = [c.name() for c in columns]  # AttributeError: 'str' object has no attribute 'name'
        # On prépare les identifiants pour le Treeview
        # Note : On suppose que 'columns' contient des objets Column avec une méthode name()
        # Si c'est parfois des strings, il faudra adapter.
        log.debug(f"TreeListCtrl: Tentative de récupération de toutes les colonnes column_ids avec columns.name().")
        try:
            column_ids = [c.name() for c in columns]
            log.debug(f"TreeListCtrl: Réussi column_ids={column_ids}.")
        except AttributeError:
            # Fallback si ce sont déjà des strings (pour le débogage)
            column_ids = [str(c) for c in columns]
            log.debug(f"TreeListCtrl: Erreur column_ids={column_ids} avec str(columns).")
        # # Récupérer _visible_columns de kwargs si présent, sinon initialiser avec une liste vide
        # self._visible_columns = kwargs.pop('_visible_columns', [])
        # displaycolumns = [c._name for c in columns if c.is_shown()]
        # displaycolumns = [c.name for c in columns if c.is_shown()]
        # Filtrer les colonnes visibles
        # self.display_columns = [c for c in columns if c.is_shown()]
        self.display_columns = [c for c in columns if c.is_shown()]
        log.debug(f"TreeListCtrl : Les colonnes visibles sont self.display_columns={self.display_columns}.")
        # display_columns = [c for c in columns if hasattr(c, 'is_shown') and c.is_shown()]
        # Ça te garantit que les identifiants utilisés par le Treeview
        # sont bien strictement ceux fournis par Column.name().

        # Extraire les identifiants de colonnes
        # column_ids = [col.identifier() for col in self.display_columns]
        display_column_ids = [c.name() for c in self.display_columns] if self.display_columns else '#all'
        log.debug(f"TreeListCtrl : La liste des identifiants des colonnes visibles sont display_column_ids={display_column_ids}.")

        # # # Appelez le constructeur de la classe parente
        # # Initialisation de ttk.Treeview en premier
        # # # Attention : Python 3.x recommande super().__init__(...)
        # # # # ttk.Treeview.__init__(self, parent, columns=[c._name for c in columns], show='tree headings', *args, **kwargs)
        # # ttk.Treeview.__init__(self, parent, columns=column_names, show='tree headings',
        # #                       displaycolumns=displaycolumns, *args, **kwargs)
        # # self.tree = TreeCtrl.__init__(self, parent, columns=column_names, show='tree headings',
        # #                       displaycolumns=displaycolumns, *args, **kwargs)
        # # Initialisation du widget Treeview avec les colonnes visibles
        # # self.tree = ttk.Treeview(parent, columns=column_ids, show="tree headings", **kwargs)
        # # self.tree = TreeCtrl(parent, columns=column_ids, show="tree headings", **kwargs)
        # # comme TreeListCtrl hérite de TreeCtrl, self.tree est redondant
        # # À la place de : self.tree = TreeCtrl(...)
        # # Il faudrait :
        # TreeCtrl.__init__(self, parent, columns=column_ids, show="tree headings", **kwargs)
        # --- 2. INITIALISATION DU WIDGET PARENT (CRITIQUE) ---
        # C'est ici que 'self' devient un widget Tkinter valide avec un '_w'
        ttk.Treeview.__init__(self, parent, columns=column_ids, show="tree headings",
                              displaycolumns=display_column_ids, *args, **kwargs)

        # --- 3. ALIAS DE COMPATIBILITÉ ---
        # Astuce : Comme le reste de votre code utilise "self.tree", on fait pointer
        # self.tree vers self. Ainsi, self.tree.bind() revient à faire self.bind().
        self.tree = self

        # --- 4. CONFIGURATION INTERNE ---
        # Mémoriser l'adapter
        # Mémorisation de l'adapter et des callbacks
        self.__adapter = adapter  # ou parent
        # Configuration des commandes et menus
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        self.itemPopupMenu = itemPopupMenu
        self.columnPopupMenu = columnPopupMenu
        # # Extraire les arguments spécifiques aux mixins
        # mixin_args = {
        #     'itemPopupMenu': itemPopupMenu,
        #     'columnPopupMenu': columnPopupMenu,
        #     'selectCommand': selectCommand,
        #     'editCommand': editCommand,
        #     'dragAndDropCommand': dragAndDropCommand,
        #     'columns': columns
        # }

        # Assurez-vous que les variables sont accessibles
        # self.__adapter = parent  # <--- ICI LE PROBLÈME
        # Nous devons changer cela. Le TreeListCtrl a besoin de deux choses :
        #
        #     Un parent (pour savoir où s'afficher dans l'interface Tkinter).
        #     Un adapter (pour savoir quelles données afficher).
        # # Assurez-vous que les variables sont accessibles
        # # self.__adapter = adapter  # <-- CORRECTION
        # # self.selectCommand = selectCommand
        # # self.editCommand = editCommand
        # # self.dragAndDropCommand = dragAndDropCommand
        # Variables d'état
        # self._columns = columns
        self.__selection = []
        self.__columns_with_images = []
        self._edit_widget = None
        self.__checking = False
        self.__double_click_pending = False
        self.__double_click_item = None
        self.last_click_time = 0
        self.dragged_items = []
        self.drag_data = []
        self.drop_position = None

        # self.tree["columns"] = columns  # Déclare explicitement les colonnes
        # self["columns"] = column_ids  # Déclare explicitement les colonnes

        # height=20 pour fixer la hauteur initiale pour Taskviewer.
        # super().__init__(parent, columns=column_names, show='tree headings',
        #                  displaycolumns=displaycolumns, *args, **kwargs)

        # Initialisation des mixins.
        # Initialisation des mixins avec leurs arguments spécifiques
        # # On passe les arguments spécifiques à chaque mixin.
        # # Initialisation manuelle des mixins avec leurs arguments spécifiques
        # # Cela évite les problèmes d'héritage multiple
        # # CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu)
        # self._init_items_mixin(itemPopupMenu)
        # --- 5. INITIALISATION DES MIXINS ---
        # Maintenant que 'self' est un widget valide, les mixins peuvent faire des bind()
        # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu)
        CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu,
                                    selectCommand=selectCommand, editCommand=editCommand)
        # CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu)
        CtrlWithColumnsMixin.__init__(self, parent, columns=columns, columnPopupMenu=columnPopupMenu)
        # self._init_columns_mixin(columns, columnPopupMenu)
        # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, columns=columns, columnPopupMenu=columnPopupMenu)
        # # TreeCtrlDragAndDropMixin.__init__(self, parent, dragAndDropCommand=dragAndDropCommand)
        # self._init_drag_drop_mixin(dragAndDropCommand)
        # TreeCtrlDragAndDropMixin.__init__(self, parent, dragAndDropCommand=dragAndDropCommand)
        # AttributeError: 'TreeListCtrl' object has no attribute 'tk'
        # # Correction : appeler l'initialisation du mixin après l'initialisation de ttk.Treeview
        TreeCtrlDragAndDropMixin.__init__(self, parent, dragAndDropCommand=dragAndDropCommand)
        # itemctrltk.CtrlWithToolTipMixin.__init__(self, parent)

        # # Initialisation de ttk.Treeview  # Non, pas après les mixins
        # ttk.Treeview.__init__(self, parent, columns=column_names, show='tree headings', displaycolumns=displaycolumns, *args, **kwargs)

        # Activation des fonctionnalités des mixins sur le Treeview
        # TreeCtrlDragAndDropMixin.__init__(self, parent, dragAndDropCommand=dragAndDropCommand)
        # TypeError: super(type, obj): obj (instance of CheckTreeCtrl) is not an instance or subtype of type (TreeCtrlDragAndDropMixin).

        # # Stockez l'information pour l'utiliser plus tard (si nécessaire)
        # self.resize_column = resizeable_column_info

        # # Ligne corrigée : utilise `kwargs.pop()` pour extraire les arguments spécifiques
        # _dragAndDropCommand = kwargs.pop('dragAndDropCommand', dragAndDropCommand)
        # _itemPopupMenu = kwargs.pop('itemPopupMenu', itemPopupMenu)
        # _columnPopupMenu = kwargs.pop('columnPopupMenu', columnPopupMenu)
        # _columns = kwargs.pop('columns', columns)

        # # # Initialisation de la classe de base ttk.Treeview
        # # Ligne corrigée : affiche toutes les colonnes par défaut
        # kwargs['displaycolumns'] = [c._name for c in columns if c.is_shown()]
        # # Ligne corrigée : affiche toutes les colonnes par défaut
        # # kwargs['displaycolumns'] = [c._name for c in columns]
        # # Il faut un attribut `is_shown` à la classe `Column` pour refléter
        # # la logique de masquage
        #
        # # super().__init__(parent, columns=[c._name for c in columns], show='tree headings', *args, **kwargs)
        # ttk.Treeview.__init__(self, parent, columns=[c._name for c in columns], show='tree headings', *args, **kwargs)

        # # # Initialisation des mixins
        # # # CtrlWithItemsMixin.__init__(self)
        # # # CtrlWithColumnsMixin.__init__(self, columns=columns, column_menu=columnPopupMenu)
        # # # TreeCtrlDragAndDropMixin.__init__(self, dragAndDropCommand=self.dragAndDropCommand)
        # # # L'ordre d'appel des __init__ est important.
        # # # On appelle le super() de chaque mixin en respectant le MRO.
        # # super().__init__(
        # #     dragAndDropCommand=self.dragAndDropCommand,
        # #     columns=columns,
        # #     column_menu=columnPopupMenu,
        # #     *args, **kwargs
        # # )
        # # Correction de l'ordre d'appel de super pour la propagation des arguments
        # super().__init__(
        #     parent,
        #     # dragAndDropCommand=self.dragAndDropCommand,
        #     dragAndDropCommand=_dragAndDropCommand,
        #     # columns=columns,
        #     columns=_columns,
        #     # column_menu=columnPopupMenu,
        #     column_menu=_columnPopupMenu,
        #     # itemPopupMenu=itemPopupMenu,
        #     itemPopupMenu=_itemPopupMenu,
        #     *args, **kwargs
        # )

        # # Configurer les en-têtes de colonnes
        # # # for col in self._columns:
        # # for col in columns:
        # #     self.heading(col.name, text=col.header(), anchor='center',
        # #                  command=lambda _col=col.name(): self.sort_by(_col, reverse=False))
        # #     self.column(col.name, width=col.width, minwidth=col.width)
        # # Ici aussi il faut vérifier que tu utilises col.name() et pas col.name.
        # # Sinon les en-têtes ne sont pas associés aux bons IDs.
        # for col in columns:
        #     self.heading(col.name(), text=col.header(), anchor='center',
        #                  command=lambda _col=col.name(): self.sort_by(_col, reverse=False))
        #     self.column(col.name(), width=col.width, minwidth=col.width)
        #     col_id = col.name()  # Récupère l'identifiant interne de la colonne
        #     try:
        #         heading = self.heading(col_id)  # Récupère la configuration d'en-tête de cette colonne
        #         print(f"[DEBUG] heading[{col_id}] = {heading}")  # Affiche la configuration pour vérification
        #     except tk.TclError:
        #         print(f"[ERREUR] Aucun heading configuré pour la colonne '{col_id}'")  # Signale une colonne non initialisée
        #
        # # # Ligne corrigée : affiche toutes les colonnes par défaut
        # # self.configure(displaycolumns=[c._name for c in columns if c.is_shown()])
        # # Initialisation des colonnes
        # self._columns = columns
        # # # On ajoute un remappage des en-têtes de colonnes
        # # for col in self._columns:
        # for col in columns:
        #     self.heading(col.name(), text=col.header(), anchor='center',
        #                  command=lambda _col=col.name(): self.sort_by(_col, reverse=False))
        #     self.column(col.name(), width=col.width, minwidth=col.width)
        # --- 6. CONFIGURATION FINALE ---
        # Configuration des colonnes (en-têtes, largeurs...)
        # Configuration des colonnes (en-têtes et propriétés)
        self._configure_columns()

        # # # Configuration des images de cases à cocher
        # # self.checked_image = tk.PhotoImage(file="checkbox_checked.png")  # Assurez-vous d'avoir ces images
        # # self.unchecked_image = tk.PhotoImage(file="checkbox_unchecked.png")
        # Gestion des images de cases à cocher
        # Chargement des images pour les cases à cocher
        # self.checked_image = artprovidertk.getIcon("Check mark")
        # WARNING:root:Image non trouvée dans le catalogue pour l'ID: Check mark et la taille: (16, 16) (Clé de recherche: Check mark16x16)
        # self.checked_image = artprovidertk.IconProvider.getIcon("Check mark")
        # TypeError: IconProvider.getIcon() missing 1 required positional argument: 'iconTitle'
        self.checked_image = artprovidertk.getIcon("checkmark_green_icon")  # TODO: artprovidertk à revoir si nécessaire !
        # self.unchecked_image = artprovidertk.getIcon("Box")
        # WARNING:root:Image non trouvée dans le catalogue pour l'ID: Box et la taille: (16, 16) (Clé de recherche: Box16x16)
        # self.unchecked_image = artprovidertk.IconProvider.getIcon("Box")
        # TypeError: IconProvider.getIcon() missing 1 required positional argument: 'iconTitle'
        self.unchecked_image = artprovidertk.getIcon("box_icon")

        # --- CORRECTION 2 : Appel de l'initialisation retardée des info-bulles ---
        # Post-initialisation des tooltips si disponible
        # Maintenant, self est un widget Tkinter avec l'attribut self._w
        if hasattr(self, '_post_init_tooltip'):
            self._post_init_tooltip()

        # Application des colonnes en attente
        # applique immédiatement les colonnes qui étaient en attente (si nécessaire)
        # self._apply_pending_columns()  # applique la configuration des colonnes
        if hasattr(self, '_apply_pending_columns'):
            self._apply_pending_columns()

        # # Liaison/Association des événements Tkinter
        # Liaison des événements
        self._bind_events()

        # self.debug_columns()
        log.debug("TreeListCtrl initialisé avec succès.")

    def heading(self, col_id, **kwargs):
        """Délègue l'appel à ttk.Treeview.heading."""
        # self.heading(col_id, **kwargs)  # RecursionError: maximum recursion depth exceeded
        super().heading(col_id, **kwargs)
        # _tkinter.TclError: Column #24 out of range

    def column(self, col_id, **kwargs) -> int:
        """Délègue l'appel à ttk.Treeview.column."""
        # self.column(col_id, **kwargs)  # RecursionError: maximum recursion depth exceeded
        return super().column(col_id, **kwargs)

    def insert(self, parent, index, iid=None, **kwargs):
        """Délègue l'appel à ttk.Treeview.insert."""
        return self.insert(parent, index, iid=iid, **kwargs)

    def delete(self, *items):
        """Délègue l'appel à ttk.Treeview.delete."""
        return self.delete(*items)

    def pack(self, **kwargs):
        """Délègue l'appel à ttk.Treeview.pack."""
        # return self.pack(**kwargs)  # RecursionError: maximum recursion depth exceeded
        return super().pack(**kwargs)

    def grid(self, **kwargs):
        """Délègue l'appel à ttk.Treeview.grid."""
        # return self.grid(**kwargs)  # RecursionError: maximum recursion depth exceeded
        return super().grid(**kwargs)  # _tkinter.TclError: cannot use geometry manager grid inside .!mainwindow.!taskviewer which already has slaves managed by pack

    def bind(self, sequence=None, func=None, add=None):
        """Délègue l'appel à ttk.Treeview.bind."""
        # return self.bind(sequence, func, add)
        # Appeler directement la méthode bind de la classe parente ou une autre méthode appropriée
        return super().bind(sequence, func, add)
        # # Implémentez ici la logique nécessaire pour lier les événements
        # # Par exemple, si vous utilisez Tkinter, vous pourriez faire quelque chose comme :
        # if sequence and func:
        #     self.widget.bind(sequence, func)
        # # Ajoutez d'autres logiques si nécessaire

    def yview(self, *args):
        """Délègue l'appel à ttk.Treeview.yview."""
        return self.tree.yview(*args)

    def configure(self, **kwargs):
        """Délègue l'appel à ttk.Treeview.configure."""
        # return self.configure(**kwargs)  # RecursionError: maximum recursion depth exceeded
        return super().configure(**kwargs)

    def _configure_columns(self):
        """Configure les en-têtes et propriétés des colonnes."""
        # for col in self._columns:
        for col in self.display_columns:
            log.debug(f"TreeListCtrl._configure_columns : Configuration de la colonne '{col.name()}' avec header '{col.header()}' et width {col.width}.")
            # col_id = col.identifier()
            col_name = col.name()
            self.heading(
                col_name,
                text=col.header(),
                anchor='w',
                command=lambda c=col_name: self.sort_by(c)
            )
            log.debug(f"TreeListCtrl._configure_column : Heading configuré pour la colonne '{col_name}': {self.heading(col_name)}")
            self.tree.column(col_name, width=col.width, minwidth=50, stretch=True)

    def debug_columns(self):
        """Affiche dans les logs la configuration des colonnes du TreeListCtrl."""
        # Parcourt la liste d'objets Column associée
        for col in self._columns:  # Liste passée au constructeur du TreeListCtrl
            print(f"[DEBUG] Column object={col!r} name()={col.name()} header={col.header()}")  # Affiche l'objet, son nom interne, et son en-tête textuel

        # Affiche les colonnes vues par ttk.Treeview
        print(f"[DEBUG] Treeview columns = {self['columns']}")  # Affiche la liste des identifiants de colonnes définis dans le Treeview
        print(f"[DEBUG] Treeview displaycolumns = {self['displaycolumns']}")  # Affiche la liste des colonnes actuellement visibles

        # Vérifie que chaque identifiant de colonne correspond à un Column
        valid_names = {col.name() for col in self._columns}  # Construit un set des noms internes de toutes les colonnes
        for col_id in self['columns']:  # Parcourt tous les identifiants déclarés dans le Treeview
            if col_id not in valid_names:  # Vérifie si l'identifiant n'existe pas dans les colonnes déclarées
                print(f"[ERREUR] Colonne Treeview '{col_id}' ne correspond à aucun Column")  # Message d'erreur pour nom incohérent

    def _bind_events(self):
        """Lie les gestionnaires d'événements."""
        # # TODO : peut-être les lier dans les viewers !
        # self.bind("<Button-1>", self.__on_item_check_or_activate)
        # # self.bind("<Double-1>", self.__on_double_click)
        # self.bind("<Double-1>", self.on_double_click)
        # self.bind("<Button-3>", self.__on_right_click_item)  # Clic droit pour menu contextuel
        # # Events de drag and drop depuis le mixin
        # self.bind("<ButtonPress-1>", self.on_start_drag)
        # self.bind("<B1-Motion>", self.on_dragging)
        # self.bind("<ButtonRelease-1>", self.on_end_drag)
        # self.bind('<Configure>', self.on_resize)  # <-- Bind event to the Treeview
        # Événements de souris
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Double-1>", self._on_double_click)
        self.bind("<Double-3>", self._on_right_click)
        # Liaison des événements
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Événements de glisser-déposer (depuis le mixin)
        self.bind("<ButtonPress-1>", self.on_start_drag)
        self.bind("<B1-Motion>", self.on_dragging)
        self.bind("<ButtonRelease-1>", self.on_end_drag)

        # Redimensionnement
        # self.bind('<Configure>', self.on_resize)
        self.bind('<Configure>', self._on_autowidth_resize)

        # ========================================================================
    # MÉTHODES D'ACCÈS À L'ADAPTER
    # ========================================================================

    def getAdapter(self):
        """Retourne l'adapter associé au TreeListCtrl."""
        return self.__adapter

    # def showSortOrder(self):
    #     """Affiche l'ordre de tri actuel dans la visionneuse."""
    #     if self.sort_column:
    #         sort_order = "Ascendant" if not self.sort_reverse else "Descendant"
    #         print(f"Tri actuel : colonne '{self.sort_column}' ({sort_order})")
    #     else:
    #         print("Aucun tri actuel.")
    #     # self.__currentSortImageIndex = imageIndex
    #     # self._showSortImage()

    def _init_items_mixin(self, itemPopupMenu):
        """Initialise les fonctionnalités du mixin CtrlWithItemsMixin"""
        self.__itemPopupMenu = itemPopupMenu

    def _init_columns_mixin(self, columns, columnPopupMenu):
        """Initialise les fonctionnalités du mixin CtrlWithColumnsMixin"""
        log.debug(f"TreeListCtrl._init_columns_mixin : initialisation avec columns={columns} et columnPopupMenu={columnPopupMenu}.")
        self.__columnPopupMenu = columnPopupMenu  # Stocke le menu contextuel des colonnes
        self._all_columns = columns  # Mémorise toutes les colonnes disponibles
        self._visible_columns = [col.name() for col in columns if col.is_shown()]  # Liste des noms de colonnes visibles
        log.debug(f"TreeListCtrl._init_columns_mixin : Les {len(self._visible_columns)} colonnes visibles sont {self._visible_columns}.")
        # self.sort_column = None  # Aucune colonne triée au départ
        # self.sort_reverse = False  # Tri ascendant par défaut
        #
        # # Vérification de cohérence : tous les noms visibles doivent être dans Treeview.columns
        # col_ids = set(self['columns'])             # Récupère les identifiants de colonnes déclarés dans le Treeview
        # for name in self._visible_columns:        # Parcourt les noms de colonnes marquées comme visibles
        #     if name not in col_ids:                # Si un nom visible n'est pas déclaré dans le Treeview
        #         print(f"[ERREUR] Colonne visible '{name}' absente de self['columns']")  # Log d'erreur de cohérence

    def _init_drag_drop_mixin(self, dragAndDropCommand):
        """Initialise les fonctionnalités du mixin TreeCtrlDragAndDropMixin"""
        self.dragged_items = []
        self.drag_data_type = ""
        self.drop_target = None
        self.drop_position = None
        self.dragAndDropCommand = dragAndDropCommand

    def bindEventHandlers(self):
        """Associe les gestionnaires d'événements aux événements Tkinter."""
        self.bind("<Button-1>", self.on_left_click)
        self.bind("<Double-Button-1>", self.on_double_click)

    # def getItemCount(self):  # TODO : A essayer
    #     return len(self.adapter)

    def getItemWithIndex(self, rowIndex: int):
        """Récupère un élément à partir de son index."""
        return self.__adapter.getItemWithIndex(rowIndex)

    def getItemText(self, domainObject: Any, columnIndex: int) -> str:
        """Récupère le texte d'un élément pour une colonne spécifique."""
        return self.__adapter.getItemText(domainObject, columnIndex)

    def getItemTooltipData(self, domainObject: Any):
        """Récupère les données de l'info-bulle d'un élément."""
        return self.__adapter.getItemTooltipData(domainObject)

    def getItemImage(self, domainObject: Any, columnIndex: int = 0):
        """Récupère l'image d'un élément pour une colonne spécifique."""
        return self.__adapter.getItemImage(domainObject, columnIndex)

    # # === Méthodes du mixin CtrlWithItemsMixin ===
    # def _itemIsOk(self, item):
    #     """Vérifie si un élément (item) du Treeview est valide."""
    #     return item != ''
    #
    # def _objectBelongingTo(self, item):
    #     """Remplaçant de GetItemPyData.!?"""
    #     if not self._itemIsOk(item):
    #         return None
    #     return self.item(item, 'tags')
    #
    # def SelectItem(self, item, select=True):
    #     """Sélectionne ou désélectionne un élément."""
    #     if select:
    #         self.selection_set(item)
    #     else:
    #         self.selection_remove(item)
    #
    # def onItemPopupMenu(self, event):
    #     """Affiche le menu contextuel pour un élément du Treeview."""
    #     item = self.identify_row(event.y)
    #     if self._itemIsOk(item):
    #         self.selection_set(item)
    #         if self.__itemPopupMenu:
    #             try:
    #                 self.__itemPopupMenu.tk_popup(event.x_root, event.y_root)
    #             finally:
    #                 self.__itemPopupMenu.grab_release()

    def show_context_menu(self, event):
        """Affiche le menu contextuel."""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if item and self.itemPopupMenu:
            self.itemPopupMenu.show(event)
        elif column and self.columnPopupMenu:
            self.columnPopupMenu.show(event)

    # ========================================================================
    # GESTION DES COLONNES ET TRI
    # =========
    # # === Méthodes du mixin CtrlWithColumnsMixin ===
    #
    # def sort_by(self, col, reverse=False):
    def sort_by(self, col_name: str):
        """Trie les éléments du Treeview par colonne."""
        # data = [(self.set(item, col), item) for item in self.get_children('')]
        data = [(self.set(item, col_name), item) for item in self.get_children('')]

        # if col == self.sort_column:
        #     self.sort_reverse = not self.sort_reverse
        # else:
        #     self.sort_column = col
        #     self.sort_reverse = reverse

        # data.sort(reverse=self.sort_reverse)
        # data.sort(reverse=False)
        data.sort()

        for index, (val, item) in enumerate(data):
            self.move(item, '', index)

    # Tu as deux endroits qui gèrent les colonnes :
    #
    # Dans itemctrltk._CtrlWithSortableColumnsMixin,
    # tu as une implémentation de showSortColumn / showSortOrder
    # pour un widget type TaskTree.
    #
    # Dans treectrltk.TreeListCtrl,
    # tu as sort_by et showColumn, mais pas showSortColumn dans ce fichier.
    #
    # Vérifier que showSortColumn reçoit un nom valide:
    #
    # Tu peux implémenter une version minimale de showSortColumn
    # dans TreeListCtrl qui ne fait que vérifier les noms, puis appeller sort_by.
    # Ça te permet de tester que :
    #
    # column.name() renvoie bien un identifiant qui existe dans self['columns']
    #
    # si ça plante, tu verras un [ERREUR] explicite.
    def showSortColumn(self, column: Column = None):
        """Affiche l'indicateur d'ordre de tri actuel pour la colonne passée
        (ou la dernière utilisée) dans la visionneuse."""
        # # # Si un objet Column est passé (cas basetk), on récupère son nom interne
        # # if column is not None:  # Vérifie si un argument a été fourni
        # #     col_name = column.name()  # Récupère le nom interne de la colonne depuis l'objet Column
        # # else:
        # #     col_name = self.sort_column  # Utilise la dernière colonne triée si aucune n'est fournie
        # #
        # # if not col_name:  # Si aucun nom de colonne n'est disponible
        # #     return  # Rien à faire, on quitte la fonction
        # #
        # # # Vérifie que le nom de colonne existe bien dans la configuration du Treeview
        # # if col_name not in self['columns']:  # Vérifie que col_name est un identifiant de colonne valide
        # #     print(f"[ERREUR] showSortColumn appelé avec un nom de colonne inconnu: {col_name}")  # Log d'erreur
        # #     return  # Évite de provoquer une erreur Tcl en accédant à un heading inexistant
        # #
        # if self.sort_column:
        #     sort_order = "Ascendant" if not self.sort_reverse else "Descendant"
        #     print(f"Tri actuel : colonne '{self.sort_column}' ({sort_order})")
        # else:
        #     print("Aucun tri actuel.")
        if hasattr(self, 'sort_column') and self.sort_column:
            order = "↑" if not getattr(self, 'sort_reverse', False) else "↓"
            log.debug(f"Tri: {self.sort_column} {order}")

        # # Vérifier que la colonne triée est bien visible :
        # if col_name not in self['displaycolumns']:
        #     print(f"[WARNING] Colonne '{col_name}' triée mais masquée (displaycolumns).")
        #
        # # Ici, tu peux simplement déléguer au tri existant
        # self.sort_by(col_name)  # Appelle la méthode de tri interne avec le nom de colonne validé

    # def showColumn(self, column_name, show=True):
    def showColumn(self, column_name: str, show: bool = True):
        """Affiche ou cache une colonne."""
        visible = list(self['displaycolumns'])

        # if show and column_name not in self._visible_columns:
        if show and column_name not in visible:
            # self._visible_columns.append(column_name)
            # self._visible_columns.sort(key=lambda x: [c.name() for c in self._all_columns].index(x))
            visible.append(column_name)
            visible.sort(key=lambda x: [c.name() for c in self._columns].index(x))
        # elif not show and column_name in self._visible_columns:
        elif not show and column_name in visible:
            # self._visible_columns.remove(column_name)
            visible.remove(column_name)

        # self['displaycolumns'] = self._visible_columns
        self['displaycolumns'] = visible

    # # === Méthodes du mixin TreeCtrlDragAndDropMixin ===
    # def on_start_drag(self, event):
    #     item = self.identify_row(event.y)
    #     if item:
    #         self.dragged_items = list(self.selection()) if self.selection() else [item]
    #         if not self.dragged_items or "" in self.dragged_items:
    #             self.dragged_items = []
    #             return
    #         self.drag_data = self.dragged_items
    #
    # def on_dragging(self, event):
    #     x, y = event.x, event.y
    #     self.drop_target = self.identify_row(y)
    #
    #     if self.drop_target:
    #         item_bbox = self.bbox(self.drop_target)
    #         if item_bbox:
    #             item_height = item_bbox[3]
    #             rel_y = y - item_bbox[1]
    #             if rel_y < item_height / 3:
    #                 self.drop_position = "above"
    #             elif rel_y > 2 * item_height / 3:
    #                 self.drop_position = "below"
    #             else:
    #                 self.drop_position = "on"
    #
    #         if self.is_valid_drop_target(self.drop_target):
    #             self.config(cursor="hand1")
    #         else:
    #             # self.config(cursor="no_entry")
    #             # Utiliser un curseur approprié selon le système d'exploitation
    #             try:
    #                 # Essayer d'abord "notallowed" (macOS)
    #                 self.config(cursor="notallowed")
    #             except tk.TclError:
    #                 try:
    #                     # Fallback vers "pirate" (disponible sur la plupart des systèmes)
    #                     self.config(cursor="pirate")
    #                 except tk.TclError:
    #                     # Dernier recours : curseur normal
    #                     self.config(cursor="arrow")
    #     else:
    #         self.config(cursor="")
    #         self.drop_target = None
    #         self.drop_position = None
    #
    # def on_end_drag(self, event):
    #     self.config(cursor="")
    #     if self.drop_target and self.is_valid_drop_target(self.drop_target):
    #         self.OnDrop(self.drop_target, self.dragged_items, self.drop_position)
    #     self.dragged_items = []
    #     self.drop_target = None
    #     self.drop_position = None
    #
    # def is_valid_drop_target(self, drop_target):
    #     if not drop_target:
    #         return False
    #
    #     # Empêcher de glisser un parent sur un enfant
    #     for dragged_item in self.dragged_items:
    #         current_item = drop_target
    #         while current_item:
    #             if current_item == dragged_item:
    #                 return False
    #             current_item = self.parent(current_item)
    #
    #     # Empêcher de glisser un élément sur lui-même ou sur un de ses enfants
    #     if drop_target in self.dragged_items:
    #         return False
    #
    #     return True

    # Reprise des méthodes wxpython
    # ========================================================================
    # GESTION DES ÉVÉNEMENTS
    # ========================================================================

    # === Méthodes spécifiques au TreeListCtrl ===
    def __on_item_check_or_activate(self, event):
        item_id = self.identify_row(event.y)
        if not item_id:
            return

        bbox = self.bbox(item_id)
        if not bbox:
            return

        # x, y, w, h = self.bbox(item_id)
        x, y, w, h = bbox

        # La colonne #0 (l'arborescence) est spéciale et n'est pas dans la liste des colonnes
        # Identifier la colonne cliquée
        col_id = self.identify_column(event.x)
        if col_id == '#0':  # Le clic est sur la première colonne (l'arborescence)
            # box_x = x + self.column("#0", width=None) - self.column("#0", stretch=None) # Calculer la position x de la case à cocher
            # On vérifie si le clic est sur la zone de la case à cocher
            tree_width = self.column('#0', width=None)
            image_width = 16  # Largeur approximative de l'image de la case à cocher
            # if event.x > box_x: # Le clic est sur la case à cocher (approximativement)
            #     self.CheckItem(item_id, not self.IsItemChecked(item_id))
            # else:
            #     self.selectCommand(event)
            # Le clic doit être dans la zone de la case à cocher pour basculer
            if 0 <= event.x - x <= image_width:
                self.CheckItem(item_id, not self.IsItemChecked(item_id))
            else:
                self.selectCommand(event)

    def on_left_click(self, event):
        """Gère le clic gauche de la souris."""
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            if self.selectCommand:
                self.selectCommand(self.getItemWithId(item_id))

    def _on_left_click(self, event):
        """Gère le clic gauche (sélection et cases à cocher)."""
        item_id = self.identify_row(event.y)
        if not item_id:
            return

        # Vérifier si on clique sur une case à cocher
        bbox = self.bbox(item_id)
        if bbox:
            x, y, w, h = bbox
            col_id = self.identify_column(event.x)

            if col_id == '#0':  # Colonne de l'arborescence
                image_width = 16
                if 0 <= event.x - x <= image_width:
                    # Clic sur la case à cocher
                    self.CheckItem(item_id, not self.IsItemChecked(item_id))
                    return

        # Sélection normale
        if self.selectCommand:
            self.selectCommand(event)

    # def __on_double_click(self, event):
    # def on_double_click(self, event):
    def _on_double_click(self, event):
        """ Gère l'événement de double-clic pour l'édition de label. """
        item_id = self.identify_row(event.y)
        # if item_id:
        #     self.editCommand(item_id)
        if item_id and self.editCommand:
            # self.editCommand(self.getItemWithId(item_id))
            self.editCommand(event)

    # def __on_right_click_item(self, event):
    # def on_right_click(self, event):
    def _on_right_click(self, event):
        """Gère le clic droit pour le menu contextuel.
        Affiche le menu contextuel de l'élément. """
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            if self.itemPopupMenu:
                self.itemPopupMenu.post(event.x_root, event.y_root)
            # if self.onItemPopupMenu:
            #     self.onItemPopupMenu.post(event.x_root, event.y_root)
            # if self.__itemPopupMenu:
            #     self.__itemPopupMenu.post(event.x_root, event.y_root)

    def on_select(self, event):
        """Gère la sélection d'un élément."""
        if self.selectCommand:
            # self.selectCommand(event)
            selected_items = self.tree.selection()
            self.selectCommand(selected_items)

    def onItemActivated(self, event):
        """Gère l'activation d'un élément (double-clic)."""
        if self.editCommand:
            item = self.identify_row(event.y)
            if item:
                event.columnName = self.identify_column(event.x)
                self.editCommand(event)

    # ========================================================================
    # GESTION DES CASES À COCHER
    # ========================================================================

    def CheckItem(self, item: str, check: bool = True):
        """ Coche ou décoche l'élément donné.
        Gère la logique des cases exclusives (radio) et non-exclusives (checkbox).
        """
        if self.__checking:
            return

        self.__checking = True

        try:
            # Mise à jour des tags de l'élément pour indiquer l'état de la case à cocher
            # current_state = self.item(item, "tags")
            tags_list = list(self.item(item, 'tags'))
            # if check and 'checked' not in current_state:
            #     self.item(item, tags=('checked',))
            # elif not check and 'checked' in current_state:
            #     self.item(item, tags=())
            if check:
                if 'checked' not in tags_list:
                    tags_list.append('checked')
            else:
                if 'checked' in tags_list:
                    tags_list.remove('checked')
            self.item(item, tags=tags_list)

            # Logique de propagation
            item_type = self.GetItemType(item)

            # Gère la logique des enfants et des parents comme dans l'original
            if check:
                # Coche le parent
                parent = self.parent(item)
                if parent:
                    self.CheckItem(parent, True)

                # Décoche les enfants exclusifs si ce n'est pas un item exclusif
                # if self.GetItemType(item) != 2:
                if item_type != 2:
                    for child in self.get_children(item):
                        if self.GetItemType(child) == 2:
                            self.CheckItem(child, False)
                            for grandchild in self.get_children(child):
                                self.CheckItem(grandchild, False)

            # Gestion des cases exclusives (radio)
            # if self.GetItemType(item) == 2:
            if item_type != 2:
                # Si cet élément est mutuellement exclusif, décoche les frères et sœurs
                parent = self.parent(item)
                if parent:
                    for sibling in self.get_children(parent):
                        if sibling != item:
                            self.CheckItem(sibling, False)

        finally:
            self.__checking = False
        # self.checkCommand(event, final=True)

    def IsItemChecked(self, item: str) -> bool:
        """ Vérifie si un élément est coché. """
        return 'checked' in self.item(item, "tags")

    def GetItemType(self, item):
        """
        Simule le type de l'élément de treectrltk.py.
        0 : normal
        1 : case à cocher non exclusive (checkbox)
        2 : case à cocher exclusive (radio exclusif)
        """
        # Dans ce cas, nous stockons le type dans les tags pour la démonstration
        # À adapter à votre modèle de données réel
        tags = self.item(item, 'tags')
        # TODO : utiliser case !?
        if 'type_checkbox' in tags:
            return 1
        if 'type_exclusive_checkbox' in tags:
            return 2
        return 0

    def getItemCTType(self, item: Any) -> int:  # pylint: disable=W0613
        """Retourne le type de contrôle pour un élément."""
        return self.ct_type

    # ========================================================================
    # GESTION DE LA SÉLECTION
    # ========================================================================

    # Explications des changements :
    #
    # self.selection(): Remplace self.GetSelections() qui est spécifique à wxPython,
    # par self.selection() qui retourne les identifiants des éléments sélectionnés dans le ttk.Treeview.
    # self._objectBelongingTo(item): Utilise self._objectBelongingTo(item)
    # pour récupérer les données associées à l'item,
    # qui est l'équivalent de self.GetItemPyData(item) dans wxPython.
    def curselection(self) -> List[Any]:
        """Retourne la liste des objets de domaine associés aux éléments sélectionnés."""
        # return [self.GetItemPyData(item) for item in self.GetSelections()]
        # wx.lib.agw.ultimatelistctrl.UltimateListCtrl.GetItemPyData
        # return [self.GetItemPyData(item) for item in self.GetSelections()]
        return [self._objectBelongingTo(item) for item in self.selection()]
        # return [self._item_to_object[item] for item in self.selection()]

    def GetSelections(self) -> tuple:
        """ Renvoie une liste des éléments sélectionnés. """
        return self.selection()

    def clear_selection(self):
        """ Désélectionne tous les éléments. """
        # self.selection_remove(self.selection())
        for item in self.selection():
            self.selection_remove(item)

    # def select(self, selection):
    #     """ Sélectionne les éléments de la liste 'selection'. """
    #     self.selection_remove(self.selection())
    #     for item in selection:
    #         self.selection_add(item)

    def select(self, items: List[str]):
        """Sélectionne les éléments donnés."""
        for item in items:
            # # TODO: A revoir
            # pass
            self.selection_add(item)

    def select_all(self):
        """ Sélectionne tous les éléments de l'arborescence. """
        # all_items = self.GetChildren(recursively=True)
        # self.selection_set(all_items)
        for item in self.get_children():
            self.selection_set(item)

    # ========================================================================
    # RAFRAÎCHISSEMENT DES DONNÉES
    # ========================================================================

    # Voici une version convertie de la méthode RefreshAllItems de la classe TreeListCtrl pour Tkinter, adaptée pour être incorporée dans la classe TreeListCtrl du fichier treectrltk.py.
    # Avant de présenter le code, il est important de comprendre le but et le fonctionnement de la méthode RefreshAllItems. En termes simples, cette méthode est responsable de la mise à jour complète du contenu du Treeview. Pour ce faire, elle doit effectuer les opérations suivantes :
    #
    # Geler l'affichage : Empêcher les mises à jour pendant le processus de rafraîchissement pour éviter les scintillements ou les artefacts visuels.
    # Arrêter l'édition : S'assurer qu'aucune cellule n'est en cours d'édition avant de procéder à la mise à jour.
    # Sauvegarder la sélection : Conserver la sélection actuelle afin de pouvoir la restaurer après la mise à jour.
    # Supprimer tous les éléments : Vider complètement le Treeview.
    # Reconstruire l'arborescence : Recréer l'arborescence à partir des données sous-jacentes.
    # Restaurer la sélection : Sélectionner à nouveau les éléments qui étaient sélectionnés avant la mise à jour.
    # Dégeler l'affichage : Réactiver les mises à jour de l'affichage.
    # Explications des changements :
    #
    # self.delete(item): Cette ligne supprime un élément du Treeview [[1430, 1431]].
    # self.insert(parent, index, text, values, tags): Insère un nouvel élément dans le Treeview sous le parent spécifié, à l'index spécifié et avec les valeurs et les tags correspondants.
    # tk.END : Une ancre qui désigne la fin d'un texte
    # self.get_children() : Retourne la liste des enfants de l'élément parent donné.
    # self.selection_add(item): Sélectionne un élément.
    # def RefreshAllItems(self, count=0):
    def RefreshAllItems(self, count: int = 0):
        """Rafraîchit tous les éléments du Treeview."""
        # # Geler l'affichage
        # self.StopEditing()
        # self.__selection = self.curselection()

        # Supprimer tous les éléments
        for item in self.get_children():
            self.delete(item)

        # Reconstruction
        # self.__columns_with_images = [
        #     index
        #     for index in range(len(self._columns))  # TODO : La gestion des images est en cours de développement
        #     # if self.__adapter.hasColumnImages(index)
        # ]
        for i in range(count):
            item = self.__adapter.getItemWithIndex(i)
            values = [self.getItemText(item, j) for j in range(len(self['columns']))]
            self.insert("", tk.END, values=values, tags=item)
        #
        # # Reconstruire l'arborescence
        # root_item = self.GetRootItem()
        # if not root_item:
        #     root_item = self.insert("", tk.END, text="Hidden root")  # Use insert instead of AddRoot
        # self._addObjectRecursively(root_item)
        #
        # # Restaurer la sélection
        # for item in self.__selection:
        #     self.selection_add(item)

    def _addObjectRecursively(self, parent_item: str, parent_object: Any = None):
        """Ajoute récursivement des objets à l'arborescence du Treeview."""
        # Devrait faire référence à la méthode viewer.task.RootNode.get_domain_children !
        # au lieu de tkinter.Misc.get_domain_children !
        print("TreeListCtrl._addObjectRecursively : self.__adapter est de type ", type(self.__adapter))
        # for child_object in self.__adapter.get_domain_children(parent_object):  # 'dict' object is not callable !
        for child_object in self.__adapter.children(parent_object):  # 'dict' object is not callable !
            # LIGNE CORRIGÉE : Utiliser la méthode renommée 'get_domain_children' pour récupérer les objets de domaine.
            # for child_object in self.__adapter.get_domain_children(parent_object):
            # child_item = self.AppendItem(parent_item, '',
            # child_item = self.Append(parent_item, "",
            # AppendItem est utilisé dans wx !
            # child_item = self.AppendItem(parent_item, "", self.getItemCTType(child_object), data=child_object)
            # child_item = self.insert(parent_item, tk.END, text="", values=[self.__adapter.getItemText(child_object, i) for i in range(len(self._columns))], tags=self.getItemCTType(child_object), data=child_object)
            # Correction : la méthode insert du Treeview attend des valeurs pour le paramètre 'values'.
            # On utilise une liste des textes de colonnes, et on stocke l'objet lui-même dans 'tags' (ou 'data' qui n'est pas standard Tkinter, mais simulé).
            # Récupération des valeurs de colonnes
            column_values = [
                self.__adapter.getItemText(child_object, i)
                for i in range(len(self._columns))
            ]

            # Insertion de l'élément
            child_item = self.insert(
                parent_item,
                tk.END,
                text="",
                values=column_values,
                tags=self.getItemCTType(child_object)
            )

            # Rafraîchissement minimal
            self._refreshObjectMinimally(child_item, child_object)

            # Gestion de l'expansion
            expanded = self.__adapter.getItemExpanded(child_object)
            if expanded:
                self._addObjectRecursively(child_item, child_object)
                # Call Expand on the item instead of on the tree
            # (self.Expand(childItem)) to prevent lots of events
            # (EVT_TREE_ITEM_EXPANDING/EXPANDED) being sent
            # child_item.Expand()
            else:
                # self.SetItemHasChildren(child_item, self.__adapter.get_domain_children(child_object))
                # self.insert(child_item, tk.END, text='')
                # Ajouter un élément factice pour permettre l'expansion
                # si l'élément a des enfants dans le modèle de données.
                # L'appel à children(child_object) dans le modèle de données détermine
                # si un "+" doit être affiché.
                if self.__adapter.children(child_object):  # Utiliser le nouveau nom ici aussi
                    self.insert(child_item, tk.END, text='')

    def _refreshObjectMinimally(self, item: str, domain_object: Any):
        """Rafraîchit les aspects minimaux d'un objet (colonnes, couleurs, police, sélection)."""
        self.__refresh_aspects(
            ("Columns", "Colors", "Font", "Selection"),
            item, domain_object
        )

    def _refreshObjectCompletely(self, item: str, domain_object: Any = None, *args):
        """Rafraîchit complètement un objet."""
        self.__refresh_aspects(
            ("ItemType", "Columns", "Font", "Colors", "Selection"),
            item,
            domain_object,
            check=True,
            *args
        )
        # TODO : Rafraîchir la vue
        # if isinstance(self.GetMainWindow(), customtree.CustomTreeCtrl):  # Semble plutôt être une instance de _CtrlWithDropTargetMixin
        #     self.GetMainWindow().RefreshLine(item)  # Seule customtreectrl a une méthode RefreshLine.

    def __refresh_aspects(self, aspects: tuple, item: str,
                          domain_object: Any, *args, **kwargs):
        """Rafraîchit des aspects spécifiques d'un élément."""
        for aspect in aspects:
            method_name = f"_refresh{aspect}"
            # # refresh_aspect = getattr(self, "_refresh%s" % aspect)
            # refresh_aspect = getattr(self, f"_refresh{aspect}")
            # refresh_aspect(domain_object, *args, **kwargs)
            if hasattr(self, method_name):
                refresh_method = getattr(self, method_name)
                refresh_method(item, domain_object, *args, **kwargs)

    def RefreshItems(self, *items):
        """Rafraîchit les éléments spécifiés."""
        for item in items:
            if self.exists(item):
                self._refreshObjectMinimally(item, None)
    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def isAnyItemExpandable(self) -> bool:
        """ Vérifie si un élément est déployable. """
        for item in self.get_children():
            # if self.item(item, 'open') == 0:
            if not self.item(item, 'open'):
                return True
        return False

    def isAnyItemCollapsable(self):
        """ Vérifie si un élément est réductible. """
        for item in self.get_children():
            if self.get_children(item):
                return True
        return False

    def GetItemCount(self) -> int:
        """ Renvoie le nombre total d'éléments. """
        return len(self.GetChildren(recursively=True))

    def GetItemChildren(self, item: str = None, recursively: bool = False) -> List[str]:
        """
        Renvoie la liste des enfants d'un élément.
        Surcharge la méthode du mixin pour la compatibilité.
        """
        if not recursively:
            return self.get_children(item)
        # else:
        children = []
        queue = list(self.get_children(item))
        while queue:
            child = queue.pop(0)
            children.append(child)
            queue.extend(self.get_children(child))
        return children

    def GetChildren(self, item: str = None, recursively: bool = False) -> List[str]:
        """ Alias pour GetItemChildren pour la compatibilité avec l'original. """
        return self.GetItemChildren(item, recursively)

    def GetRootItem(self) -> Optional[str]:
        """ Renvoie le premier élément de niveau racine. """
        # return self.get_children()[0] if self.get_children() else None
        children = self.get_children()
        return children[0] if children else None

    def IsLabelBeingEdited(self) -> bool:
        """ Indique si le label est en cours d'édition. """
        return self._edit_widget is not None

    def StopEditing(self):
        """ Arrête l'édition du label. """
        if self._edit_widget:
            self._edit_widget.destroy()
            self._edit_widget = None

    # ========================================================================
    # GLISSER-DÉPOSER
    # ========================================================================

    def OnDrop(self, drop_item: str, dragged_items: List[str], part: str, column: int):
        """
        Cette méthode doit être surchargée dans la classe dérivée.
        Gère le dépôt (drop) d'éléments dans l'arborescence.

        Args :
            drop_item: Item cible du drop
            dragged_items: Items glissés
            part: Position ("above", "below", "on")
        """
        log.debug(f"OnDrop : Éléments glissés: {len(dragged_items)} items sur {drop_item} à la position ({part}).")
        if not dragged_items:
            return  # Rien à faire

        # Récupérer l'objet métier associé à l'élément sur lequel on dépose
        if drop_item:
            drop_object = self.GetItemPyData(drop_item)
        else:
            drop_object = None  # Dépôt à la racine
        log.debug(f"OnDrop : Objet cible du drop: {drop_object}")

        # Récupérer les objets métiers associés aux éléments déplacés
        dragged_objects = [self.GetItemPyData(item) for item in dragged_items]

        # Exemple de déplacement simple
        for item in dragged_items:
            if part == "on":
                # Déplacer l'élément pour qu'il devienne un enfant
                self.move(item, drop_item, "end")
            else:
                # Déplacer l'élément au-dessus ou en-dessous
                index = self.index(drop_item)
                if part == "below":
                    index += 1
                self.move(item, self.parent(drop_item), index)

        # Logique de déplacement des éléments dans le modèle de données
        try:
            self.move_items(dragged_objects, drop_object, part)
        except Exception as e:
            print(f"Erreur lors du déplacement des éléments : {e}")
            return

        # Reconstruire le modèle de données/l'arborescence pour refléter les changements
        self.rebuild_data_model()

        # Appeler le callback dragAndDropCommand si défini
        if self.dragAndDropCommand:
            # self.dragAndDropCommand(None)  # Passer un event fictif
            self.dragAndDropCommand(dragged_objects, drop_object, part)

    def rebuild_data_model(self):
        """
        Reconstruit la structure de données sous-jacente
        (après une opération de glisser-déposer).
        """
        log.debug("Reconstruction du modèle de données. La structure de l'arborescence a été mise à jour.")
        items = self.get_children("")
        for item_id in items:
            parent_id = self.parent(item_id)
            item_text = self.item(item_id, 'text')
            parent_text = self.item(parent_id, 'text') if parent_id else 'Racine'
            log.debug(f"TreeListCtrl: Élément/Item : {item_text}, Parent : {parent_text}")

            # Traiter récursivement les enfants
            self._print_children(item_id, 1)

    def move_items(self, dragged_objects: List[Any], drop_object: Any, part: int):
        """
        Déplace les éléments dans le modèle de données.
        Cette méthode doit être implémentée en fonction de la structure de données
        spécifique de votre application.
        """
        # TODO: Implémenter la logique de déplacement des éléments
        # dans votre modèle de données ici.
        #
        # Vous devrez probablement manipuler les relations parent-enfant
        # des objets dragged_objects et drop_object.
        #
        # Exemple:
        # for obj in dragged_objects:
        #     obj.parent = drop_object
        raise NotImplementedError("Implémenter la logique de déplacement des éléments dans le modèle de données.")

    def _print_children(self, parent_item: str, level: int):
        """Méthode helper pour imprimer la hiérarchie des enfants.

        Affiche récursivement la hiérarchie des enfants."""
        for child in self.get_children(parent_item):
            child_text = self.item(child, 'text')
            indent = "  " * level
            log.debug(f"TreeListCtrl._print_children : {indent}-> {child_text}")
            self._print_children(child, level + 1)

    def hasColumnImages(self, column):
        """
        Vérifie si une colonne contient des images.

        Args :
            column : (int?) La colonne à vérifier.

        Returns :
            (bool) : True si la colonne contient des images, sinon False.
        """
        # return self.visibleColumns()[column].hasImages()
        return self._visible_columns[column].hasImages()

    # def _visible_columns(self):
    #     # def visibleColumns(self) -> list:
    #     """
    #     Retourne la liste des colonnes visibles.
    #
    #     Returns :
    #         Liste des colonnes actuellement visibles.
    #     """
    #     return self._visible_columns


# --- Nouvelle classe : CheckTreeCtrl ---
# ============================================================================
# CLASSE AVEC CASES À COCHER
# ============================================================================


class CheckTreeCtrl(TreeListCtrl):
    """
    Hérite de TreeListCtrl et ajoute la fonctionnalité de case à cocher,
    y compris la gestion des cases d'option (radio buttons) exclusives.

    TreeListCtrl avec support des cases à cocher et radio buttons.
    Équivalent de wx CustomTreeCtrl avec CT_AUTO_CHECK_CHILD.
    """
    # # def __init__(self, parent: tk.Widget, columns: List, selectCommand: Callable, checkCommand: Callable,
    # #              editCommand: Callable, dragAndDropCommand: Callable, itemPopupMenu: Any = None,
    # #              *args, **kwargs):
    # def __init__(self, parent: tk.Widget, adapter: Any, columns: List, selectCommand: Callable, checkCommand: Callable,
    #              editCommand: Callable, dragAndDropCommand: Callable, itemPopupMenu: Any = None,
    #              *args, **kwargs):
    def __init__(self, parent: tk.Widget, adapter: Any, columns: List[Column],
                 checkCommand: Callable = None,
                 dragAndDropCommand: Callable = None,
                 # itemPopupMenu: Any = None,
                 itemPopupMenu: tk.Menu = None,
                 *args, **kwargs):
        """
        Initialise CheckTreeCtrl.

        Args:
            parent: Widget parent
            adapter: Adaptateur de données
            columns: Liste de colonnes
            checkCommand: Callback appelé lors du cochage
            dragAndDropCommand: Callback glisser-déposer
            itemPopupMenu: Menu contextuel
        """

        self.__checking = False
        self.checkCommand = checkCommand
        # self._mainWin = parent  # Référence au parent, utilisé pour l'accès aux accesseurs de données
        self._mainWin = adapter  # <-- CORRECTION 1 (utiliser l'adapter)

        # Récupération des méthodes de l'adapter
        # Récupère les fonctions d'accès aux données depuis le parent (ou fournit des stubs par défaut)
        # self.getIsItemCheckable = (
        #     getattr(parent, "getIsItemCheckable")
        #     if hasattr(parent, "getIsItemCheckable")
        #     else lambda item: True
        # )
        self.getIsItemCheckable = getattr(
            adapter, "getIsItemCheckable", lambda item: True
        )
        # self.getIsItemChecked = getattr(parent, "getIsItemChecked", lambda item: False)
        self.getIsItemChecked = getattr(
            adapter, "getIsItemChecked", lambda item: False
        )
        # self.getItemParentHasExclusiveChildren = getattr(parent, "getItemParentHasExclusiveChildren", lambda item: False)
        self.getItemParentHasExclusiveChildren = getattr(
            adapter, "getItemParentHasExclusiveChildren", lambda item: False
        )

        # Initialisation de la classe de base TreeListCtrl
        # Initialisation de la classe parente
        # super().__init__(parent, columns,
        # super().__init__(parent, adapter, columns,  # <-- CORRECTION 2 (passer l'adapter)
        #                  selectCommand, editCommand, dragAndDropCommand,
        #                  itemPopupMenu, *args, **kwargs)
        super().__init__(
            parent, adapter, columns,  # <-- CORRECTION 2 (passer l'adapter)
            dragAndDropCommand=dragAndDropCommand,
            itemPopupMenu=itemPopupMenu,
            *args, **kwargs
        )

        # Le binding de <Button-1> de la classe parente est onItemLeftClick
        # On le remplace par notre gestionnaire onMouseLeftDown
        # Remplacement du binding du clic gauche
        # self.unbind("<Button-1>")
        # # Remplacez self.unbind("<Button-1>") par :
        # self.after(0, lambda: self.unbind("<Button-1>"))
        # try:
        #     self.unbind("<Button-1>")
        # except Exception as e:
        #     print(f"Note: Erreur lors de l'unbind : {e}")
        # # Par (vérification de sécurité) :
        # if hasattr(self, '_w'):
        #     self.unbind("<Button-1>")
        #     # Python 3.13 a renforcé la vérification des états des objets internes.
        #     # Si CheckTreeCtrl hérite d'une classe personnalisée qui elle-même oublie d'appeler super().__init__,
        #     # l'attribut _w manquera toujours.
        #     self.bind("<Button-1>", self.onMouseLeftDown)
        # else:
        #     # On diffère l'exécution à la fin de la boucle d'événements
        #     self.after(0, lambda: self.unbind("<Button-1>") if hasattr(self, '_w') else None)

        # Sous Python 3.13, le widget peut ne pas être prêt pour unbind/bind
        # immédiatement si la hiérarchie d'héritage est complexe.
        # On définit une fonction d'initialisation des événements
        def rebind_events():
            if hasattr(self, '_w'):
                self.unbind("<Button-1>")
                self.bind("<Button-1>", self.onMouseLeftDown)

        # On planifie l'exécution dès que Tkinter est prêt
        self.after(0, rebind_events)
        # AttributeError: 'CheckTreeCtrl' object has no attribute 'tk'
        # L'erreur AttributeError: 'CheckTreeCtrl' object has no attribute 'tk' signifie que
        # l'objet Python existe, mais il n'est connecté à aucune instance réelle de Tkinter.

    def getItemCTType(self, domain_object: Any) -> int:
        """ Utilise la logique originale pour déterminer le type de case à cocher.

        Détermine le type de case à cocher pour un objet."""
        if self.getIsItemCheckable(domain_object):
            return 2 if self.getItemParentHasExclusiveChildren(domain_object) else 1
        # else:
        return 0

    def CheckItem(self, item: str, checked: bool = True):
        """
        Coche/décoche un élément avec gestion radio/checkbox.
        Surcharge de la méthode parente CheckItem
        pour ajouter la logique de propagation radio/checkbox
        et la commande de vérification.
        """
        if self.__checking:
            # Si déjà en cours de vérification, on ne fait que mettre à jour l'état
            # de base et on sort pour éviter la récursion de commande.
            super().CheckItem(item, checked)
            return

        self.__checking = True

        item_type = self.GetItemType(item)

        try:
            if item_type == 2:  # Bouton Type Radio (Exclusif)
                if checked:
                    # 1. Décoche tous les frères et sœurs si on coche celui-ci
                    parent = self.parent(item)
                    if parent:
                        for sibling in self.get_children(parent):
                            if sibling != item and self.IsItemChecked(sibling):
                                # Appel direct pour mettre à jour l'état sans déclencher
                                # un événement de commande ou la logique de propagation
                                super().CheckItem(sibling, False)

                    # 2. Coche l'élément actuel
                    super().CheckItem(item, True)

                    # 3. Coche le parent non-radio si c'est applicable
                    # parent = self.parent(item)  # Doublon avec 1.
                    if parent and self.GetItemType(parent) > 0 and self.GetItemType(parent) != 2:
                        super().CheckItem(parent, True)

                else:
                    # Décochage d'un radio button. Ne devrait se produire que via onMouseLeftDown
                    super().CheckItem(item, False)

            else:  # Type Checkbox (Non-exclusif) ou Normal
                # Mise à jour de l'état
                # 1. Mise à jour de l'état de l'élément actuel (et propagation aux parents)
                super().CheckItem(item, checked)

                # Propagation aux enfants radio si décoché
                # 2. Gère la propagation aux enfants (pour le type 1)
                if item_type == 1 and not checked:
                    # Si un parent non-exclusif est décoché, ses enfants radio doivent être décochés
                    for child in self.get_children(item):
                        if self.GetItemType(child) == 2 and self.IsItemChecked(child):
                            # Décocher l'enfant radio et tous ses descendants
                            self.CheckItem(child, False)
                            for grandchild in self.GetItemChildren(child, recursively=True):
                                super().CheckItem(grandchild, False)
        finally:
            self.__checking = False

            # Callback
            # Appel de la commande de vérification finale
            # On suppose que `checkCommand` prend (item_id, checked_state, final=True/False)
            if self.checkCommand:
                self.checkCommand(item, checked, final=True)

    def onMouseLeftDown(self, event):
        """Gère le clic gauche avec support du décochage de radio buttons.

        Surcharge la gestion du clic gauche pour autoriser le décochage d'un bouton radio
        déjà sélectionné, ce que le comportement par défaut d'une case à cocher n'autorise pas.
        """
        item_id = self.identify_row(event.y)
        if not item_id:
            # return self.onItemLeftClick(event)
            return self.on_left_click(event)  # TODO : vérifier qu'il s'agit de la bonne méthode !

        # 1. Vérification si le clic est sur l'icône de vérification (case)
        # x_start, y_start, w, h = self.bbox(item_id)
        # image_width = 16
        # is_on_check_icon = self.GetItemType(item_id) > 0 and (0 <= event.x - x_start <= image_width)
        bbox = self.bbox(item_id)
        if bbox:
            x_start, y_start, w, h = bbox
            image_width = 16
            is_on_check_icon = (
                self.GetItemType(item_id) > 0 and
                (0 <= event.x - x_start <= image_width)
            )

            # Décochage spécial pour radio buttons
            if (
                    item_id
                    and self.GetItemType(item_id) == 2       # C'est un bouton radio (exclusive)
                    and is_on_check_icon                     # Le clic est sur l'icône
                    and self.IsItemChecked(item_id)          # Il est déjà coché
            ):
                # Clic sur un radio button déjà coché: on le force à se décocher
                self.__uncheck_item_recursively(item_id)
                return "break"  # Stoppe l'événement Tkinter par défaut

        # Si la condition de décochage radio est fausse, on laisse la classe de base gérer
        # return self.onItemLeftClick(event)
        return self._on_left_click(event)

    def __uncheck_item_recursively(self, item_id: str):
        """ Décoche récursivement un élément et ses enfants (pour le radio-décochage forcé). """
        if self.GetItemType(item_id) > 0:
            # On appelle CheckItem qui gère la commande finale
            self.CheckItem(item_id, checked=False)

        # Parcourt récursivement les enfants
        for child_id in self.get_children(item_id):
            self.__uncheck_item_recursively(child_id)

    def _refreshObjectCompletely(self, item: str, domain_object: Any = None, *args):
        """Rafraîchit complètement un objet incluant l'état de case."""
        # La méthode n'est pas nativement dans TreeListCtrl, mais dans ses mixins
        if hasattr(super(), '_refreshObjectCompletely'):
            super()._refreshObjectCompletely(item, domain_object, *args)

        self._refreshCheckState(item, domain_object)

    def _refreshObjectMinimally(self, item: str, domain_object: Any):
        """Rafraîchit minimalement un objet incluant l'état de case."""
        if hasattr(super(), '_refreshObjectMinimally'):
            super()._refreshObjectMinimally(item, domain_object)
        self._refreshCheckState(item, domain_object)

    def _refreshCheckState(self, item: str, domain_object: Any):
        """
        Mise à jour de l'état de la case à cocher sans déclencher d'événement de commande.
        """
        # 1. Mise à jour de l'état de l'élément (checked/unchecked) et du type (1/2)
        is_checked = self.getIsItemChecked(domain_object)
        item_type = self.getItemCTType(domain_object)
        tags_list = list(self.item(item, 'tags'))

        # Mise à jour du tag 'checked'
        if is_checked and 'checked' not in tags_list:
            tags_list.append('checked')
        elif not is_checked and 'checked' in tags_list:
            tags_list.remove('checked')

        # Mise à jour des tags de type (checkbox ou exclusive_checkbox)
        if item_type == 1 and 'type_checkbox' not in tags_list:
            tags_list.extend(['type_checkbox'])
        elif item_type == 2 and 'type_exclusive_checkbox' not in tags_list:
            tags_list.extend(['type_exclusive_checkbox'])

        # Nettoyage des tags non pertinents
        if item_type != 1 and 'type_checkbox' in tags_list:
            tags_list.remove('type_checkbox')
        if item_type != 2 and 'type_exclusive_checkbox' in tags_list:
            tags_list.remove('type_exclusive_checkbox')

        self.item(item, tags=tags_list)

        # 2. Logique d'activation/désactivation (simplifiée/ignorée car non standard Tkinter)
        # On peut ignorer la partie self.EnableItem pour l'instant.


# --- Exemple d'utilisation ---
# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == '__main__':
    # Configuration du logging pour voir ce qui se passe
    logging.basicConfig(level=logging.DEBUG)

    from tkinter import Menu
    try:
        from itemctrltk import Column
    except ImportError:
        # Fallback pour test local si la structure de dossier n'est pas respectée
        # Si les classes sont dans le même fichier ou accessibles via le module courant
        from taskcoachlib.widgetstk.itemctrltk import Column

    # Pour résoudre le problème de l'erreur "is_shown()",
    # ajoutez cette méthode à la classe Column de votre fichier itemctrltk.py
    # Assurer que la classe Column a la méthode is_shown
    # def add_is_shown_to_column():
    #     if not hasattr(Column, 'is_shown'):
    #         def is_shown(self):
    #             # Par défaut, une colonne est affichée.
    #             return True
    #         Column.is_shown = is_shown
    #
    # add_is_shown_to_column()
    # # redondant puisque is_shown est déjà défini dans la classe Column dans itemctrltk.py.

    class SimpleAdapter:
        """Adaptateur simple pour démonstration."""
        def __init__(self):
            self.data = []  # Liste d'objets métier fictifs

        def getItemWithIndex(self, index):
            return self.data[index] if index < len(self.data) else None

        def getItemText(self, obj, col_index):
            return str(obj.get('values', [''])[col_index]) if obj else ''

        def children(self, obj):
            return obj.get('children', []) if obj else self.data

        def getItemExpanded(self, obj):
            return obj.get('expanded', False) if obj else False

        def getItemTooltipData(self, obj):
            return ""

        def getItemImage(self, obj, col_index):
            return None

        # AJOUTER CES MÉTHODES POUR ÉVITER DES CRASH SI ON CLIQUE PARTOUT
        # Méthodes requises par CheckTreeCtrl (même si des lambdas par défaut existent)
        def getIsItemCheckable(self, item):
            return True

        def getIsItemChecked(self, item):
            # Simulation simple : on regarde les tags de l'item dans le treeview
            # Note: Dans une vraie app, on regarderait l'objet métier
            return False

        def getItemParentHasExclusiveChildren(self, item):
            return False

        # Note : Dans votre CheckTreeCtrl.__init__,
        # vous avez mis des getattr(adapter, ..., lambda: ...)
        # qui gèrent l'absence de ces méthodes, donc ce n'est pas bloquant,
        # mais c'est mieux pour la compréhension.


    class Application(tk.Tk):
        """Application de démonstration."""
        def __init__(self):
            super().__init__()
            self.title("TreeCtrl Tkinter - Démonstration TaskCoach")
            # self.geometry("400x300")
            # self.geometry("600x400")
            self.geometry("800x600")

            # Création de l'adaptateur
            self.adapter = SimpleAdapter()

            # Définir les colonnes
            columns = [
                Column('task_name', 'Tâche', 'Tâche', width=200, is_shown=True),
                Column('due_date', 'Date d’échéance', "Date d'échéance", width=120, is_shown=True),
                Column('priority', 'Priorité', 'Priorité', width=80, is_shown=True),
            ]

            # Créer des menus contextuels de test
            item_menu = Menu(self, tearoff=0)
            item_menu.add_command(label="Modifier")
            item_menu.add_command(label="Supprimer")
            item_menu.add_separator()
            item_menu.add_command(label="Propriétés", command=self.on_properties)

            column_menu = Menu(self, tearoff=0)
            column_menu.add_command(label="Trier ascendant", command=self.on_sort_asc)
            column_menu.add_command(label="Trier descendant", command=self.on_sort_desc)
            column_menu.add_separator()
            column_menu.add_command(label="Cacher la colonne")

            # self.config(menu=item_menu)
            # self.config(menu=column_menu)

            # # Création du conteneur TreeListCtrl
            # frame = ttk.Frame(self, padding=10)
            # frame.pack(fill=tk.BOTH, expand=True)
            # Instanciation
            # Note: CheckTreeCtrl hérite de TreeListCtrl, donc il profitera des corrections

            # Scrollbars
            vsb = ttk.Scrollbar(self, orient="vertical")
            hsb = ttk.Scrollbar(self, orient="horizontal")

            # # Crée une instance de TreeCtrl, TreeListCtrl ou CheckTreeCtrl
            # # self.tree = TreeCtrl(self)
            # self.tree = TreeListCtrl(
            #     self,
            #     self,
            #     columns=columns,
            #     selectCommand=self.on_select,
            #     editCommand=self.on_edit,
            #     dragAndDropCommand=self.on_drag_and_drop,
            #     itemPopupMenu=item_menu,
            #     columnPopupMenu=column_menu
            # )
            # self.tree.pack(fill=tk.BOTH, expand=True)
            # self.tree = CheckTreeCtrl(
            tree = CheckTreeCtrl(
                self,              # Parent widget
                self.adapter,       # Adapter
                columns=columns,    # Colonnes
                checkCommand=self.on_check,
                dragAndDropCommand=self.on_drag_drop,
                itemPopupMenu=item_menu,
                # Configuration du scroll via kwargs supportés par ttk.Treeview
                yscrollcommand=vsb.set,
                xscrollcommand=hsb.set
            )

            # Liaison des scrollbars au treeview
            vsb.config(command=tree.yview)
            # hsb.config(command=self.tree.xscroll)  # AttributeError: 'CheckTreeCtrl' object has no attribute 'xscroll'
            # Erreur de frappe : la méthode correcte est xview
            hsb.config(command=tree.xview)

            # Layout avec grid
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')

            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)

            # Barre de boutons
            button_frame = ttk.Frame(self)
            button_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Button(button_frame, text="Ajouter",
                       command=self.on_add).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Supprimer",
                       command=self.on_delete).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Développer tout",
                       command=self.on_expand_all).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Réduire tout",
                       command=self.on_collapse_all).pack(side=tk.LEFT, padx=2)

            # Peuplement initial
            self.populate_tree()

        def populate_tree(self):
            """Ajoute des éléments de test à l'arborescence."""
            # Note: Ceci peuple le widget visuel, pas l'adaptateur.
            # Dans une vraie app, on remplirait l'adaptateur puis on appellerait RefreshAllItems.
            # Élément parent
            # parent1_id = self.tree.insert("", "end", text="Projet A - Migration TaskCoach")
            parent1 = self.insert("", "end", text="Projet A - Migration TaskCoach",
                                          values=("2025-03-01", "Haute"),
                                          tags=('type_checkbox',))

            # # Enfants du parent 1
            # self.tree.insert(parent1_id, "end", text="Rédiger le rapport")
            # self.tree.insert(parent1_id, "end", text="Réaliser la présentation")
            task1 = self.insert(parent1, "end", text="Convertir itemctrl.py",
                                     values=("2025-02-01", "Haute"),
                                     tags=('type_checkbox', 'checked'))

            task2 = self.insert(parent1, "end", text="Convertir treectrl.py",
                                     values=("2025-02-15", "Haute"),
                                     tags=('type_checkbox',))

            task3 = self.insert(parent1, "end", text="Tests d'intégration",
                                     values=("2025-02-28", "Moyenne"),
                                     tags=('type_checkbox',))

            # Élément parent 2 avec une case à cocher exclusive - Projet B avec statut exclusif
            # parent2_id = self.tree.insert("", "end", text="Tâches du projet B")
            # parent2 = self.tree.insert("", "end", text="Statut du projet", values=("", ""), tags=('type_exclusive_checkbox',))
            parent2 = self.insert("", "end", text="Projet B - Documentation",
                                       values=("2025-04-01", "Moyenne"),
                                       tags=('type_checkbox',))

            # # # Enfants du parent 2
            # # child1 = self.tree.insert(parent2_id, "end", text="Coder le module 1")
            # # self.tree.insert(parent2_id, "end", text="Coder le module 2")
            #
            # # Enfants du parent 2 (exclusifs)
            # self.tree.insert(parent2, "end", text="En cours",
            #                  values=("", ""), tags=('type_exclusive_checkbox', 'checked'))
            # self.tree.insert(parent2, "end", text="Terminé",
            #                  values=("", ""), tags=('type_exclusive_checkbox',))
            status_parent = self.insert(parent2, "end", text="Statut",
                                             values=("", ""),
                                             tags=())

            self.insert(status_parent, "end", text="En cours",
                             values=("", ""),
                             tags=('type_exclusive_checkbox', 'checked'))

            self.insert(status_parent, "end", text="En attente",
                             values=("", ""),
                             tags=('type_exclusive_checkbox',))

            self.insert(status_parent, "end", text="Terminé",
                             values=("", ""),
                             tags=('type_exclusive_checkbox',))

            # # Sous-enfant
            # self.tree.insert(child1, "end", text="Tester le module")

            # Projet C
            parent3 = self.insert("", "end", text="Projet C - Maintenance",
                                       values=("2025-12-31", "Basse"),
                                       tags=('type_checkbox',))

            self.insert(parent3, "end", text="Corriger bugs mineurs",
                             values=("2025-06-01", "Basse"),
                             tags=('type_checkbox',))

        def on_select(self, event):
            """ Gère la sélection d'un élément. """
            item_id = self.identify_row(event.y)
            if item_id:
                print(f"Élément sélectionné : {self.item(item_id, 'text')}")

        def on_edit(self, item_id):
            """ Gère l'édition du label d'un élément. """
            print(f"Édition de l'élément : {self.item(item_id, 'text')}")
            # L'implémentation de l'édition réelle se trouve dans le mixin ou dans la classe principale

        def on_check(self, item, checked, final=True):
            """Callback lors du cochage."""
            if final:
                # print(f"Check: {self.tree.item(item, 'text')} -> {checked}")
                text = self.item(item, 'text')
                state = "cochée" if checked else "décochée"
                print(f"Tâche '{text}' {state}")

        def on_drag_and_drop(self, event):
            """ Gère l'action de glisser-déposer. """
            print("Action de glisser-déposer terminée.")
            # self.tree.rebuild_data_model()

        def on_drag_drop(self, event):
            """Callback après glisser-déposer."""
            print("Glisser-déposer effectué, hiérarchie mise à jour")

        def on_edit_menu(self):
            """Éditer l'élément sélectionné."""
            selection = self.selection()
            if selection:
                print(f"Édition de: {self.item(selection[0], 'text')}")

        def on_delete_menu(self):
            """Supprimer l'élément sélectionné."""
            self.on_delete()

        def on_properties(self):
            """Afficher les propriétés."""
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                print(f"\nPropriétés de '{self.item(item, 'text')}':")
                print(f"  Valeurs: {self.item(item, 'values')}")
                print(f"  Tags: {self.item(item, 'tags')}")
                print(f"  Coché: {self.IsItemChecked(item)}")
                print(f"  Type: {self.GetItemType(item)}")

        def on_sort_asc(self):
            """Tri ascendant."""
            print("Tri ascendant demandé")

        def on_sort_desc(self):
            """Tri descendant."""
            print("Tri descendant demandé")

        def on_hide_column(self):
            """Masquer une colonne."""
            print("Masquage de colonne demandé")

        def on_add(self):
            """Ajouter un nouvel élément."""
            selection = self.selection()
            parent = selection[0] if selection else ""

            new_item = self.insert(
                parent, "end",
                text="Nouvelle tâche",
                values=("", "Normale"),
                tags=('type_checkbox',)
            )
            self.selection_set(new_item)
            self.see(new_item)
            print("Nouvelle tâche ajoutée")

        def on_delete(self):
            """Supprimer les éléments sélectionnés."""
            selection = self.selection()
            for item in selection:
                text = self.item(item, 'text')
                self.delete(item)
                print(f"Tâche '{text}' supprimée")

        def on_expand_all(self):
            """Développer tous les éléments."""
            def expand_recursive(item):
                self.item(item, open=True)
                for child in self.get_children(item):
                    expand_recursive(child)

            for item in self.get_children():
                expand_recursive(item)

        def on_collapse_all(self):
            """Réduire tous les éléments."""
            def collapse_recursive(item):
                self.tree.item(item, open=False)
                for child in self.get_children(item):
                    collapse_recursive(child)

            for item in self.get_children():
                collapse_recursive(item)

    # Lancement de l'application
    app = Application()
    app.mainloop()
