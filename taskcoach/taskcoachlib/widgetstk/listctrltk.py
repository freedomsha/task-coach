# listctrl.py pour Tkinter, converti de wxPython
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
# Je vais te donner la structure exacte attendue par ListViewer dans TaskCoach,
# en restant fidèle à l’architecture wx d’origine, mais adaptée proprement à Tkinter / ttk.Treeview.
# Je vais aussi expliquer pourquoi chaque pièce existe, pour que tu puisses raisonner seul ensuite.
#
# 🧠 Architecture réelle de ListViewer dans TaskCoach
#
# Dans TaskCoach, un ListViewer n’est PAS propriétaire des données.
# Il est seulement un adaptateur graphique entre :
#
# un modèle métier (Task, Category, Effort…)
# et un contrôle graphique (ListCtrl / Treeview)
#
# 👉 C’est la clé pour comprendre pourquoi ton Treeview est vide.
#
# 1️⃣ Rôles des objets (très important)
# 🔹 1. ListViewer
# décide quelles colonnes existent
# décide dans quel ordre
# sait comment lire les données
# ne stocke PAS les items
#
# 🔹 2. VirtualListCtrl
# n’a aucune logique métier
# affiche ce que le ListViewer lui demande
# appelle le viewer pour chaque cellule
#
# 🔹 3. Modèle (Task, Category, …)
# contient les vraies données
# ne connaît PAS Tkinter

# J'ai converti listctrl.py en tkinter en utilisant la logique de itemctrl.py déjà adaptée.
# La conversion est complexe car wx.ListCtrl est une classe
# avec des fonctionnalités avancées (colonnes, sélection, affichage virtuel)
# qui n'ont pas d'équivalent direct dans tkinter.
#
# Pour cette conversion, j'ai utilisé ttk.Treeview, qui est
# le widget le plus proche de wx.ListCtrl et wx.TreeListCtrl.
# J'ai également créé une nouvelle classe VirtualListCtrl pour
# encapsuler la logique de gestion des colonnes, de la sélection et du test d'accès (HitTest).
#
# Voici le code converti, en supposant que itemctrl.py se trouve dans le même dossier
# ou est importable.

# J'ai converti listctrl.py pour qu'il fonctionne avec Tkinter.
# Voici les points clés de la conversion :
#
#     Widget de base : Le wx.ListCtrl a été remplacé par ttk.Treeview,
#                      qui est le widget le plus flexible
#                      pour afficher des données en colonnes dans Tkinter.
#
#     Fonctionnalités héritées : J'ai fait en sorte que VirtualListCtrl
#                                hérite de la classe TaskList de itemctrl.py,
#                                ce qui permet de réutiliser toute la logique
#                                de gestion des colonnes et des menus contextuels
#                                que nous avons déjà convertie.
#
#     Gestion des événements : Les événements wxPython (wx.EVT_...) ont été remplacés
#                              par des liaisons Tkinter (<Button-1>, <Double-Button-1>).
#
#     Méthodes d'aide : Les méthodes wxPython comme curselection(), select(),
#                       et clear_selection() ont été réimplémentées
#                       pour utiliser les méthodes de ttk.Treeview
#                       et correspondre au comportement attendu.
#
# Le code inclut une section de test pour vous montrer comment utiliser
# le nouveau widget et interagir avec lui.

# Voici les étapes à suivre pour compléter la conversion :
# 1. Comprendre la structure de listctrl.py et itemctrl.py   :
#
# listctrl.py hérite de itemctrl.CtrlWithItemsMixin, itemctrl.CtrlWithColumnsMixin,
# itemctrl.CtrlWithToolTipMixin et wx.ListCtrl .
# Il utilise un wx.ListCtrl en mode virtuel (wx.LC_REPORT | wx.LC_VIRTUAL).
# Il délègue la gestion des données à un parent (appelé __parent) qui doit
# implémenter les méthodes getItemWithIndex, getItemText, getItemTooltipData et getItemImage.
# Il gère les événements de sélection et d'activation des éléments, ainsi que le focus.
# Il utilise wx.lib.mixins.listctrl.getListCtrlSelection pour obtenir la sélection actuelle .
#
# 2. Créer listctrltk.py en utilisant ttk.Treeview et les mixins de itemctrltk.py :
#
# Utiliser ttk.Treeview en mode "liste" comme équivalent de wx.ListCtrl.
# Cela signifie que vous n'aurez qu'une seule colonne visible.
# Les autres colonnes serviront à stocker les données.
# Utiliser les mixins de itemctrltk.py pour ajouter les fonctionnalités de
# gestion des éléments, des colonnes et des info-bulles .
#
# 3. Implémenter les méthodes déléguées :
#
# Dans listctrltk.py, vous devrez implémenter les méthodes getItemWithIndex,
# getItemText, getItemTooltipData et getItemImage,
# en déléguant leur exécution à l'objet parent.
# La méthode getItemWithIndex est utilisée pour récupérer l'élément de données
# correspondant à un index donné.
# La méthode getItemText est utilisée pour récupérer le texte à afficher dans
# une cellule spécifique du ListCtrl.
# La méthode getItemTooltipData est utilisée pour récupérer les informations
# à afficher dans l'info-bulle d'un élément.
# La méthode getItemImage est utilisée pour récupérer l'image à afficher pour un élément .
#
# 4. Gérer les événements :
#
# Lier les événements de sélection (<ButtonRelease-1>) et d'activation
# (<Double-Button-1>) aux méthodes correspondantes.
# Adapter la logique de onSelect et onItemActivated pour Tkinter en utilisant
# les méthodes du ttk.Treeview  .
#
# 5. Adapter les méthodes de rafraîchissement :
#
# Implémenter RefreshAllItems et RefreshItems pour mettre à jour l'affichage
# du ttk.Treeview lorsque les données changent.
# Utiliser insert et delete du ttk.Treeview pour ajouter et supprimer des éléments .
#
# 6. Gérer la sélection :
#
# Implémenter les méthodes curselection, select, clear_selection et select_all
# en utilisant les méthodes selection_set, selection_remove et get_children du ttk.Treeview.

# Remarques importantes :
#
# Ce code est un squelette et doit être adapté à votre application spécifique.
# Vous devrez implémenter les méthodes getItemWithIndex, getItemText,
# getItemTooltipData et getItemImage dans la classe parent qui utilise VirtualListCtrl.
# Vous devrez également adapter la logique de tri en fonction de vos besoins.
#
# J'ai essayé de chercher des informations concernant la conversion de la
# méthode SelectItem de la classe _CtrlWithItemsMixin, les classes
# _CtrlWithDropTargetMixin, Column, _BaseCtrlWithColumnsMixin et
# _CtrlWithAutoResizedColumnsMixin dans les fichiers que vous avez fournis,
# mais je n'ai trouvé aucun résultat pertinent.
# Je vous recommande de consulter la réponse précédente pour obtenir des informations à ce sujet.

# Dans ttk.Treeview, il existe une subtilité d'ordre :
#
#     La colonne d'arborescence #0 doit être correctement configurée
#     (généralement masquée ou réduite) avant de configurer les en-têtes des colonnes nommées.
#
#     Dans une vue en liste, toutes les colonnes de données sont des colonnes nommées.
#
#     Si l'on ne spécifie pas displaycolumns lors de l'initialisation,
#     ttk.Treeview peut être capricieux et exiger que
#     la configuration des en-têtes utilise l'indice numérique (#1, #2, etc.)
#     plutôt que le nom ('task_name').

# La Solution : Rendre les Mixins "Non-Coopératifs"
#
# Puisque VirtualListCtrl (votre "TreeListCtrl" pour listes) gère l'initialisation explicitement,
# les mixins dans itemctrltk.py ne doivent pas utiliser super().__init__ pour propager les arguments.
# Ils doivent agir comme de simples fonctions de configuration.
# Résumé de la Correction
#
# Votre approche dans listctrltk.py (initialiser ttk.Treeview d'abord,
# puis les mixins) est la bonne solution pour contourner les problèmes d'initialisation de Tkinter.
#
# Le bug résiduel était que les mixins dans itemctrltk.py utilisaient super(),
# ce qui n'est pas compatible avec cette stratégie d'initialisation manuelle.
# En remplaçant les super().__init__() par des appels MixinParent.__init__() explicites
# (ou en les supprimant s'ils n'ont pas de parent mixin),
# vous cassez la chaîne MRO indésirable et empêchez les arguments d'être passés à object.__init__.
import logging
import tkinter as tk
from tkinter import ttk

# Assurez-vous d'importer la classe TaskList de votre version convertie de itemctrl.py
# ou toute autre classe équivalente qui gère le Treeview.
from taskcoachlib.widgetstk import itemctrltk
from taskcoachlib.widgetstk.itemctrltk import Column

# Il n'y a pas d'équivalent direct à wx.lib.mixins.listctrl, donc nous
# devons réimplémenter les fonctionnalités dans la classe elle-même.

log = logging.getLogger(__name__)


# class VirtualListCtrl(TaskList):
# class VirtualListCtrl(itemctrltk.CtrlWithItemsMixin,
# class VirtualListCtrl(  # ttk.Treeview,  # ttk.Treeview doit être la première classe de base concrète.
#                       # Remarque : Les mixins doivent être initialisés après Tkinter.
#                       itemctrltk.CtrlWithColumnsMixin,
#                       itemctrltk.CtrlWithItemsMixin,
#                       # itemctrltk.CtrlWithToolTipMixin,  # Mixin ToolTip en dernier # <--- RETIRÉ DE L'HÉRITAGE DIRECT
#                       ttk.Treeview):  # ttk.Treeview en dernier (pour être le parent concret)
# Cela fonctionnait avant cela :
# NOUVELLE DÉFINITION (Ajout de CtrlWithToolTipMixin)
class VirtualListCtrl(itemctrltk.CtrlWithItemsMixin,
                      itemctrltk.CtrlWithColumnsMixin,
                      itemctrltk.CtrlWithToolTipMixin,  # <--- RÉINTRODUIT ICI
                      ttk.Treeview):
    """
    Une adaptation de wx.ListCtrl pour Tkinter, utilisant ttk.Treeview
    en mode LC_REPORT | LC_VIRTUAL.
    """
    def __init__(self, parent, columns, selectCommand=None, editCommand=None,
                 itemPopupMenu=None, columnPopupMenu=None, resizeableColumn=0,
                 *args, **kwargs):
        log.debug(f"VirtualListCtrl.__init__ called by {self.__class__.__name__} with {len(columns)} columns={columns!r}")
        log.debug(f"VirtualListCtrl.__init__ avec selectCommand={selectCommand}, editCommand={editCommand}, itemPopupMenu={itemPopupMenu}, columnPopupMenu={columnPopupMenu}, resizeableColumn={resizeableColumn}, args={args!r}")
        log.debug(f"VirtualListCtrl.__init__ kwargs before filtering: {kwargs!r}")
        # Note : L'approche MRO dans listctrltk.py est déjà complexe,
        # forcer l'initialisation explicite (comme ci-dessus) est
        # la façon la plus sûre de résoudre les TclError dans la phase de conversion.
        # # 1. Extrait les arguments pour les mixins AVANT l'appel à Tkinter
        # 1. Extraction et nettoyage des arguments pour éviter la TclError de Tkinter
        # # # FILTRAGE DES ARGUMENTS DESTINÉS AUX MIXINS (CRITIQUE)
        # _columns = columns
        self._columns = columns  # Stocker la liste des colonnes
        self.__parent = parent
        self.__selectCommand = selectCommand
        self.__editCommand = editCommand
        # _itemPopupMenu = itemPopupMenu
        # _columnPopupMenu = columnPopupMenu
        # _resizeableColumn = columns[resizeableColumn].name()
        #
        # # # Liste des arguments mixins à retirer de kwargs pour éviter la TclError
        # # # ANCIEN FILTRAGE (à retirer pour selectCommand/editCommand)
        # # mixin_kwargs = {}
        # # for arg_name in ['itemPopupMenu', 'columnPopupMenu', 'selectCommand', 'editCommand']:
        # #     if arg_name in kwargs:
        # #         mixin_kwargs[arg_name] = kwargs.pop(arg_name)
        # # NOUVEAU FILTRAGE (plus simple)
        # Stocker les valeurs
        # _itemPopupMenu = kwargs.pop('itemPopupMenu', itemPopupMenu)
        # _columnPopupMenu = kwargs.pop('columnPopupMenu', columnPopupMenu)
        # _selectCommand = kwargs.pop('selectCommand', selectCommand) # <--- Retirer ici, mais doit être injecté
        # _editCommand = kwargs.pop('editCommand', editCommand)       # <--- Retirer ici, mais doit être injecté
        # _columns = columns
        # FILTRAGE DES ARGUMENTS EN COMMUN AVEC TKINTER (AUCUN)

        # 1. Initialisation explicite de ttk.Treeview
        # Ici, TOUS les kwargs doivent être nettoyés avant l'appel.

        # # On stocke d'abord tous les arguments mixin dans un dictionnaire pour les filtrer
        # all_mixin_args = {
        #     'columns': columns,
        #     'itemPopupMenu': itemPopupMenu,
        #     'columnPopupMenu': columnPopupMenu,
        #     'selectCommand': selectCommand,
        #     'editCommand': editCommand,
        # }
        # NOUVEAU FILTRAGE dans VirtualListCtrl (Retirer TOUT argument mixin de kwargs global)
        # all_mixin_keys = ['columns', 'itemPopupMenu', 'columnPopupMenu', 'selectCommand', 'editCommand']

        # # Retirer les arguments mixins de kwargs avant de les passer à Tkinter
        # for key in all_mixin_args:
        #     kwargs.pop(key, None)  # <--- C'est ici que ça devrait marcher !

        # Stockage local des arguments mixins avant de nettoyer kwargs
        # mixin_args = {key: kwargs.pop(key, None) for key in all_mixin_keys}

        # # # super().__init__(parent, columns=columns, show="headings",
        # # #                  selectmode=tk.EXTENDED, itemPopupMenu=itemPopupMenu,
        # # #                  *args, **kwargs)
        # # # 2. Initialisation de la classe de base concrète Tkinter
        # # # ^— Cette ligne est maintenant gérée par le super() des mixins
        # # #    qui héritent de ttk.Treeview (si l'ordre est bon) ou doit être forcée.
        # #
        # # # Dans l'approche mixin multiple, on doit initier les parents spécifiquement
        # # # ou s'assurer que le MRO appelle ttk.Treeview avant CtrlWithToolTipMixin
        # #
        # # # FORCER L'INITIALISATION DE TK.Treeview AVANT TOUT
        # # 1. Initialisation explicite de ttk.Treeview (Utilise kwargs FILTRÉS)
        # # TclError peut encore se produire ici si un mixin a ajouté un autre argument
        # # non standard de Tkinter à **kwargs.
        # # ttk.Treeview.__init__(self, parent, columns=[c.name for c in _columns], show="headings",
        # ttk.Treeview.__init__(self, parent, columns=[c.name() for c in columns], show="headings",
        #                       selectmode=tk.EXTENDED, *args, **kwargs)  # <-- kwargs est maintenant propre

        # NOUVEAU CODE : Extraction des noms de colonnes
        # column_names = [c.name() for c in _columns]
        column_names = [c.name() for c in columns]
        # column_names = [c.name() for c in mixin_args['columns']]
        log.debug("column_names = %r", column_names)
        # 1. Initialisation explicite de ttk.Treeview
        # Utiliser la liste de noms extraite
        # AJOUT DE displaycolumns POUR FORCER L'ORDRE D'AFFICHAGE (crucial pour ListViewer)

        # On filtre les arguments qui ne sont pas supportés par ttk.Treeview
        treeview_kwargs = kwargs.copy()
        for key in ['itemPopupMenu', 'columnPopupMenu', 'selectCommand', 'editCommand']:
            treeview_kwargs.pop(key, None)

        # 2. Initialisation du widget de base
        ttk.Treeview.__init__(self, parent, columns=column_names,
                              displaycolumns=column_names, show="headings",
                              # selectmode=tk.EXTENDED, *args, **kwargs)
                              selectmode=tk.EXTENDED, *args, **treeview_kwargs)

        # 1. Configurer la colonne #0 pour qu'elle ne prenne pas d'espace (comme dans une vue en liste).
        # Normalement, la colonne #0 devrait afficher la colonne 'period' (la première).
        # self.column('#0', width=0, stretch=tk.NO)
        # self.heading('#0', text="")
        log.debug("Si tout s'est bien passé VirtualListCtrl est un treeview avec cette liste de colonne : %r", self['columns'])

        # # 3. Initialisation manuelle du ToolTip (après que self est un widget Tk valide)
        # # Cette deuxième approche (initialisation manuelle) est la plus fiable
        # # pour résoudre le problème de l'ordre d'initialisation des mixins/widgets Tk.
        # # ANCIEN CODE (RETIRÉ)
        # # self.tooltip_mixin = itemctrltk.CtrlWithToolTipMixin(self, *args, **kwargs)
        #
        # self.__parent = parent
        # self.__selectCommand = selectCommand
        # self.__editCommand = editCommand
        # self.__columnPopupMenu = columnPopupMenu
        # # self.resize_column = columns[resizeableColumn].name()
        # self.resize_column = _resizeableColumn

        # # # 3. Initialisation des mixins (passant les kwargs)
        # # # ATTENTION: Il faut s'assurer que l'appel super() dans itemctrltk.py
        # # # transmet correctement le 'self' initialisé à Tkinter.
        # #
        # # # Appeler le reste de la chaîne d'héritage via la première classe de mixin
        # # # ATTENTION: Retirons le ToolTip de la chaîne d'héritage multiple temporairement pour le tester.
        # #
        # # # Tentons l'initialisation des mixins requis (avec l'ordre du MRO implicite)
        # # 2. Initialisation des mixins restants (doit respecter le MRO pour le super et utiliser les arguments stockés)
        # # Puisque les mixins n'héritent plus de ttk.Treeview, on peut les initialiser
        # # en appelant directement leur __init__ ou en gérant l'ordre du MRO.
        #
        # # Pour simplifier, nous appelons les mixins pertinents qui font le set-up.
        # # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=_itemPopupMenu, *args, **kwargs)
        # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=_itemPopupMenu, selectCommand=selectCommand, editCommand=editCommand, *args, **kwargs)
        # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu, selectCommand=_selectCommand, editCommand=_editCommand)
        # # # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu, *args, **kwargs)
        # # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, columns=_columns, columnPopupMenu=_columnPopupMenu, *args, **kwargs)
        # # # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, columns=columns, columnPopupMenu=columnPopupMenu, *args, **kwargs)
        # # # NOUVEAU: Appel explicite du mixin ToolTip
        # # itemctrltk.CtrlWithToolTipMixin.__init__(self, self, *args, **kwargs)  # Initialisation ToolTip après Tkinter
        #
        # # 2. Initialisation des mixins. Nous devons passer les arguments de callback via **kwargs
        # # en nous assurant qu'ils ne sont pas passés deux fois (d'où le pop ci-dessus)
        # 2. Initialisation des mixins. On passe TOUS les arguments à chaque mixin,
        #    qui les consommera lui-même (grâce à l'étape 1).
        #
        # 3. Initialisation des mixins
        # # # Reconstruire les kwargs pour les mixins car ils ne sont plus dans **kwargs général
        # # mixin_args = {
        # #     'itemPopupMenu': _itemPopupMenu,
        # #     'columnPopupMenu': _columnPopupMenu,
        # #     'selectCommand': _selectCommand,  # <--- Injecté ici
        # #     'editCommand': _editCommand       # <--- Injecté ici
        # # }
        # #
        # # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, **mixin_args)
        # # A. Initialisation des Mixins d'Items (retire itemPopupMenu/selectCommand/editCommand/columnPopupMenu)
        # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, **all_mixin_args)
        # itemctrltk.CtrlWithItemsMixin.__init__(self, parent, **mixin_args)
        itemctrltk.CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu,
                                               selectCommand=selectCommand, editCommand=editCommand)
        # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, columns=_columns, **mixin_args)
        # B. Initialisation des Mixins de Colonnes (retire columnPopupMenu/selectCommand/editCommand/columns)
        # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, **all_mixin_args)
        # itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, **mixin_args)
        itemctrltk.CtrlWithColumnsMixin.__init__(self, parent, columns=columns,
                                                 columnPopupMenu=columnPopupMenu)
        # itemctrltk.CtrlWithToolTipMixin.__init__(self, self, **mixin_args)
        # C. Initialisation du ToolTip (doit appeler super() sans les arguments spécifiques)
        # itemctrltk.CtrlWithToolTipMixin.__init__(self, self, **all_mixin_args)
        # itemctrltk.CtrlWithToolTipMixin.__init__(self, parent, **mixin_args)
        itemctrltk.CtrlWithToolTipMixin.__init__(self, parent)

        # 4. Configuration visuelle
        # Tkinter Treeview n'a pas de concept de "client data" comme wx.
        # Vous devez gérer les données séparément, par exemple via un dictionnaire.
        # self.__item_data = {}

        #  Créer les en-têtes de colonne
        # Nous avons besoin de configurer la colonne #0 pour qu'elle soit masquée ou utilisée
        # comme première colonne de données (period).

        # Option A (La plus courante pour une vue en liste) : Utiliser la colonne #0 pour la première donnée, et cacher le reste.
        # ATTENTION : Si le Treeview a été initialisé avec show="headings",
        # la colonne #0 est masquée par défaut (ou ne montre pas d'en-tête),
        # mais doit quand même être configurée.

        # 1. Configurer la colonne #0 pour qu'elle ne prenne pas d'espace (comme dans une vue en liste).
        # Normalement, la colonne #0 devrait afficher la colonne 'period' (la première).
        self.column('#0', width=0, stretch=tk.NO)  # Masquer la colonne d'arborescence
        # self.heading('#0', text="")

        # 2. Configurer les colonnes nommées (period, task, etc.)
        # for col in _columns:
        for col in columns:
            log.debug(f"VirtualListCtrl.__init__ : configuration de la colonne {col.name()}")
            # Correction : Itérer sur l'index numérique à partir de 1
            # for index, col in enumerate(_columns):
            # L'identifiant de colonne dans heading/column doit être l'indice numérique
            # de la colonne (car la colonne #0 est spéciale).

            # On s'assure que le nom de la colonne est utilisé comme identifiant
            self.heading(col.name(), text=col.header(),
                         command=lambda the_col=col: self.sort_by(the_col.name()))
            # # Identifiant numérique de la colonne (commence à 1, car #0 est géré)
            # column_id = f'#{index + 1}'
            # self.column(col._name, width=col.width, minwidth=20)
            self.column(col.name(), width=col.width, minwidth=20, anchor='w', stretch=tk.YES)  # Force l'extension
            log.debug(f"VirtualListCtrl.__init__ : configuration de la colonne pour self={self}")
            log.debug(f"VirtualListCtrl.__init__ : CONFIGURATION A REVOIR !!!")
            # self.column(col.name(), width=col.width, minwidth=20)
            # # self.column(column_id, width=col.width, minwidth=20)
            # # self.heading(col._name, text=col._header,
            # #              command=lambda _col=col: self.sort_by(_col._name))
            # log.debug(f"VirtualListCtrl.__init__ : configuration de la colonne {col.name()}")
            # self.heading(col.name(), text=col.header(),
            #              command=lambda the_col=col: self.sort_by(the_col.name()))
            # # Utiliser le nom de la colonne pour le tri, mais l'ID numérique pour le heading/column
            #
            # self.heading(column_id, text=col.header(),
            #              command=lambda the_col=col: self.sort_by(the_col.name()))

            self.bindEventHandlers()

        # Analyse de l'Erreur
        #
        # Cause
        # Dans ttk.Treeview, la première colonne affichée
        # (qui n'a pas de nom dans l'attribut columns) est la colonne d'arborescence
        # (ou de données de base). Cette colonne est toujours référencée par #0.
        # Toutes les colonnes supplémentaires, définies dans l'attribut columns,
        # sont référencées par leurs noms
        # ou par des indices numériques à partir de #1 (par exemple, #1, #2, etc.).
        #
        # Dans votre VirtualListCtrl.__init__, vous créez les en-têtes de colonne :
        # En réalité, dans une implémentation ListViewer basée sur ttk.Treeview,
        # la colonne #0 doit être traitée comme la colonne d'arborescence
        # (même si elle est plate), et les autres colonnes sont accessibles par leur nom.
        #
        # Le MIEUX est de forcer l'ajout de la colonne #0 à la liste _columns
        # et de la configurer comme la colonne d'arborescence
        # si vous voulez que la colonne period soit la première à s'afficher.
        #
        # Puisque nous n'avons pas accès à la liste complète des colonnes
        # pour la modification, la solution la plus simple est
        # d'appliquer la correction de nom que nous avons faite
        # (méthode appelée name() et header())
        # et d'assurer que la configuration de l'en-tête est faite correctement.
        #
        # Vérification : L'erreur indique que col.name() (qui renvoie 'period')
        # n'est pas reconnu comme un index valide à ce moment.
        #
        # La correction est d'utiliser le nom de la colonne directement
        # comme index de colonne, ce qui est déjà le cas dans votre code,
        # mais l'erreur persiste.
        # Cela implique que le Treeview n'a pas été initialisé avec la liste columns !
        # Raisonnement :
        #
        #     ttk.Treeview est initialisé avec columns=[col1_name, col2_name, ...].
        #
        #     La colonne #0 (arborescence) est configurée et masquée.
        #
        #     Les colonnes de données (nommées) sont accessibles par leurs noms
        #     ou par les indices numériques #1, #2, ...
        #
        #     Puisque Tkinter semble avoir des difficultés à résoudre
        #     le nom 'period' ou 'task_name' à ce stade,
        #     l'utilisation de l'indice numérique garantit que
        #     l'objet self.heading est appelé avec une référence valide.

    def bindEventHandlers(self):
        """
        Associe les gestionnaires d'événements aux événements Tkinter.
        """
        # self.bind("<Button-1>", self.on_left_click)
        # self.bind("<Double-Button-1>", self.on_double_click)

        # self.bind("<Button-1>", self.on_left_click)
        self.bind("<ButtonRelease-1>", self.onSelect)  # Single click
        # self.bind("<Double-Button-1>", self.on_double_click)
        self.bind("<Double-Button-1>", self.onItemActivated)  # Double click
        self.bind("<Button-3>", self.on_right_click)
        self.bind("<Motion>", self.on_motion_update_tooltip)
        # Laissez les bindings de sélection et d'activation en place,
        # mais vérifiez si vous avez besoin des bindings d'édition de _CtrlWithItemsMixin.
        # self.bind("<Double-1>", self._on_double_click)

    def getItemCount(self):
        """
        Retourne le nombre total d’éléments à afficher.
        """
        raise NotImplementedError

    # def getItemWithIndex(self, Index):
    def getItemWithIndex(self, rowIndex):
        """
        Retourne l'objet métier correspondant à un index donné.

        Délègue à l'objet parent la récupération de l'élément
        correspondant à l'index donné.

        Args:
            rowIndex: Index de la ligne à récupérer.

        Returns:
            Elément de données correspondant à l'index.
        """
        return self.__parent.getItemWithIndex(rowIndex)
        # raise NotImplementedError

    # getItemText(self, domainObject, columnIndex):
    def getItemText(self, domain_object, column_name):
        """
        Retourne le texte à afficher pour une cellule.

        Délègue à l'objet parent la récupération de l'élément
        correspondant à la cellule donnée.

        """
        # # return self.__parent.getItemText(domainObject, columnIndex)
        # raise NotImplementedError
        return self.__parent.getItemText(domain_object, column_name)

    # deux méthodes déléguées pour l'interface TaskCoach
    def getItemTooltipData(self, domainObject):
        """
        Retourne le texte de l’info-bulle.
        """
        return self.__parent.getItemTooltipData(domainObject)

    # def getItemImage(self, domainObject, columnIndex=0):
    def getItemImage(self, domain_object, column_name=None):
        """
        (Optionnel) retourne une image Tkinter (PhotoImage).
        """
        # # return self.__parent.getItemImage(domainObject, columnIndex)
        # return None
        return self.__parent.getItemImage(domain_object, column_name)

    def on_left_click(self, event):
        """
        Gère le clic gauche de la souris.
        """
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            if self.__selectCommand:
                # self.__selectCommand(self.getItemWithId(item_id))
                self.__selectCommand(self.getItemWithIndex(item_id))

    def onSelect(self, event):
        # if self.selectCommand:
        #     self.selectCommand(event)
        item_id = self.identify_row(event.y)
        if item_id and self.__selectCommand:
            # On récupère l'objet métier via le mixin
            obj = self._objectBelongingTo(item_id)
            if obj:
                self.__selectCommand(obj)

    # def on_double_click(self, event):
    #     """
    #     Gère le double-clic gauche.
    #     """
    #     item_id = self.identify_row(event.y)
    #     if item_id and self.__editCommand:
    #         self.__editCommand(self.getItemWithId(item_id))
    # Remplacé par onItemActivated.

    def onItemActivated(self, event):
        # if self.editCommand:
        #     item = self.identify_row(event.y)
        #     if item:
        #         event.columnName = self.identify_column(event.x)
        #         self.editCommand(event)
        item_id = self.identify_row(event.y)
        if item_id and self.__editCommand:
            obj = self._objectBelongingTo(item_id)
            if obj:
                self.__editCommand(obj)

    def on_right_click(self, event):
        """
        Gère le clic droit pour le menu contextuel.
        """
        item_id = self.identify_row(event.y)
        if item_id:
            self.selection_set(item_id)
            if hasattr(self, 'itemPopupMenu') and self.itemPopupMenu:
                self.itemPopupMenu.post(event.x_root, event.y_root)
        # if self.itemPopupMenu:
        #     self.itemPopupMenu.post(event.x_root, event.y_root)

    # # Méthode indispensable pour remplir le Treeview
    # # Dans wxPython : le ListCtrl virtuel appelle automatiquement le viewer
    # # Dans Tkinter : tu dois remplir le Treeview toi-même
    # def populate(self):  # TODO : non fonctionnel !
    #     """
    #     Remplit le Treeview à partir des données du parent (viewer).
    #     """
    #     self.delete(*self.get_children())
    #
    #     if not hasattr(self.__parent, 'getItemCount'):
    #         return
    #     count = self.__parent.getItemCount()
    #
    #     for index in range(count):
    #         domain_object = self.__parent.getItemWithIndex(index)
    #         values = [self.__parent.getItemText(domain_object, col.name()) for col in self._columns]
    #
    #         # values = []
    #         # for col in self._columns:
    #         #     text = self.__parent.getItemText(domain_object, col.name())
    #         #     values.append(text)
    #
    #         # self.insert("", "end", values=values)
    #         # On utilise l'index ou l'ID de l'objet comme identifiant de ligne
    #         node_id = self.insert("", tk.END, values=values)
    #         self.insert("", tk.END, values=values)
    #         # Liaison cruciale pour que _objectBelongingTo fonctionne
    #         # self._mapObjectToNode(domain_object, node_id)

    def RefreshAllItems(self, count):
        # Effacer tous les éléments existants
        for item in self.get_children():
            self.delete(item)
        # Insérer les nouveaux éléments
        for i in range(count):
            # ANCIEN CODE
            # item = self.__parent.getItemWithIndex(i)  # AttributeError: 'Frame' object has no attribute 'getItemWithIndex'
            # # item = self.getItemWithIndex(i)  # AttributeError: 'Frame' object has no attribute 'getItemWithIndex'
            # # Le problème est que self.__parent est un Frame au lieu d'être le viewer parent qui contient cette méthode.

            # NOUVEAU CODE - Vérifier si la méthode existe
            if hasattr(self.__parent, 'getItemWithIndex'):
                item = self.__parent.getItemWithIndex(i)
            else:
                # # Fallback - utiliser directement la présentation
                # if i < len(self.presentation()):  # AttributeError: 'VirtualListCtrl' object has no attribute 'presentation'
                #     item = self.presentation()[i]
                # else:
                continue  # Ignorer cet index
            values = [self.getItemText(item, j) for j in range(len(self['columns']))]
            self.insert("", tk.END, values=values, tags=item)
        # self.populate()  # Utiliser la méthode populate pour rafraîchir tous les éléments

    def RefreshItems(self, *items):
        for item in items:
            index = self.__parent.getIndexOfItem(item)
            if index is not None:
                # Mettre à jour l'élément existant
                values = [self.getItemText(item, j) for j in range(len(self['columns']))]
                self.item(item, values=values, tags=item)
            else:
                # Ajouter un nouvel élément s'il n'existe pas
                values = [self.getItemText(item, j) for j in range(len(self['columns']))]
                self.insert("", tk.END, values=values, tags=item)

    def HitTest(self, xxx_todo_changeme, *args, **kwargs):
        """
        Adapte la méthode HitTest pour Tkinter.
        """
        (x, y) = xxx_todo_changeme
        item_id = self.identify_row(y)

        if not item_id:
            return -1, None, -1

        column_id = self.identify_column(x)
        column_index = int(column_id.replace('#', '')) - 1

        # En Tkinter, l'index de l'élément est son identifiant (string).
        # On renvoie une valeur compatible avec la structure wx (index, flags, column).
        # On utilise l'index de l'élément dans la liste des enfants du parent pour simuler l'index numérique.
        index = self.parent(item_id)  # Retourne l'identifiant du parent
        return index, 'flags_placeholder', column_index

    def curselection(self):
        """
        Retourne une liste des éléments actuellement sélectionnés.
        """
        # return [self.item(item_id, 'values') for item_id in self.selection()]
        return [self._objectBelongingTo(item) for item in self.selection()]

    def select(self, items):
        """
        Sélectionne les éléments donnés.
        """
        # # Pour une implémentation complète, vous devez lier les "items"
        # # aux identifiants Treeview.
        # # Cette implémentation suppose une correspondance simple.
        # all_items = self.get_children()
        # for item_id in all_items:
        #     item_data = self.item(item_id, 'values')
        #     if item_data in items:
        #         self.selection_add(item_id)
        #     else:
        #         self.selection_remove(item_id)
        for item in items:
            tree_item = self.__parent.getTreeItem(item)
            if tree_item:
                self.selection_set(tree_item)

    def clear_selection(self):
        """
        Désélectionne tous les éléments.
        """
        # self.selection_remove(self.selection())
        for item in self.selection():
            self.selection_remove(item)

    def select_all(self):
        """
        Sélectionne tous les éléments.
        """
        # self.selection_set(self.get_children())
        for item in self.get_children():
            self.selection_set(item)

    def sort_by(self, col_name):
        """Tri les éléments du Treeview par colonne."""
        data = [(self.set(item, col_name), item) for item in self.get_children('')]
        # if col == self.sort_column:
        #     self.sort_reverse = not self.sort_reverse
        # else:
        #     self.sort_column = col
        #     self.sort_reverse = False
        # data.sort(reverse=False)  # self.sort_reverse
        data.sort()  # self.sort_reverse
        for index, (val, item) in enumerate(data):
            self.move(item, '', index)


# # Exemple COMPLET de ListViewer fonctionnel
# #
# # Voici LA référence que tu peux garder.
# class DummyListViewer:
#     """
#     Exemple minimal conforme à ListViewer TaskCoach.
#     """
#
#     def __init__(self):
#         # Données simulées (remplacera Task, Category, etc.)
#         self._items = [
#             {"period": "Aujourd’hui", "task": "Tester Tkinter", "status": "En cours"},
#             {"period": "Demain", "task": "Corriger ListCtrl", "status": "À faire"},
#         ]
#
#         # Colonnes déclarées
#         self.columns = [
#             Column("period", "Période", width=120),
#             Column("task", "Tâche", width=250),
#             Column("status", "Statut", width=100),
#         ]
#
#     def getItemCount(self):
#         return len(self._items)
#
#     def getItemWithIndex(self, index):
#         return self._items[index]
#
#     def getItemText(self, domain_object, column_name):
#         return domain_object.get(column_name, "")
#
#     def getItemTooltipData(self, domain_object):
#         return f"Tâche : {domain_object['task']}"


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUG, Tu peux passer à INFO ou WARNING en production
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("taskcoach.log", mode='w', encoding='utf-8'),
            logging.StreamHandler()  # Affiche aussi dans la console
        ]
    )
    class MockViewer:
        def __init__(self):
            self.data = [
                {'id': 1, 'task': 'Acheter du pain', 'status': 'Fait'},
                {'id': 2, 'task': 'Coder en Python', 'status': 'En cours'}
            ]
        def getItemCount(self): return len(self.data)
        def getItemWithIndex(self, i): return self.data[i]
        def getItemText(self, obj, col): return obj.get(col, "")
        def getItemTooltipData(self, obj): return f"Détails: {obj['task']}"
        def getItemImage(self, obj, col): return None

    root = tk.Tk()
    root.title("Exemple de VirtualListCtrl (Tkinter)")

    # Définition des colonnes
    columns = [
        Column('task_name', 'Tâche', width=400),
        Column('due_date', 'Date d’échéance', width=120),
        Column('priority', 'Priorité', width=80),
    ]

    # Données factices
    data = [
        {'task_name': 'Acheter du pain', 'due_date': '2023-10-27', 'priority': 'Haute'},
        {'task_name': 'Rédiger le rapport', 'due_date': '2023-11-01', 'priority': 'Moyenne'},
        {'task_name': 'Appeler le client', 'due_date': '2023-10-28', 'priority': 'Basse'},
    ]

    viewer = MockViewer()

    # Fonctions de rappel pour l'exemple
    def on_select(item):
        print("Élément sélectionné:", item)

    def on_edit(item):
        print("Édition de l'élément:", item)

    def getItemCount(self):
        return len(self._items)

    def getItemWithIndex(self, index):
        return self._items[index]

    def getItemText(self, domain_object, column_name):
        return domain_object.get(column_name, "")

    def getItemTooltipData(self, domain_object):
        return f"Tâche : {domain_object['task']}"

    # Créer le menu contextuel
    item_menu = tk.Menu(root, tearoff=0)
    item_menu.add_command(label="Modifier")
    item_menu.add_command(label="Supprimer")

    # Création de l'instance du VirtualListCtrl
    list_ctrl = VirtualListCtrl(root, columns=columns, selectCommand=on_select,
                                editCommand=on_edit, itemPopupMenu=item_menu)
    # Injection du viewer comme parent pour que la délégation fonctionne
    list_ctrl._VirtualListCtrl__parent = viewer
    list_ctrl.pack(fill=tk.BOTH, expand=True)

    # Remplir le Treeview avec les données factices
    list_ctrl.delete(*list_ctrl.get_children())
    for item in data:
        list_ctrl.insert('', tk.END, values=(item['task_name'], item['due_date'], item['priority']))
    # list_ctrl.populate(data)

    root.mainloop()

