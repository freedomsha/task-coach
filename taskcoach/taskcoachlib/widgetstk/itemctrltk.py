# Résumé de la conversion de itemctrl.py pour Tkinter
#
# La conversion directe du fichier itemctrl.py de wxPython vers Tkinter
# est impossible en raison de différences fondamentales d'architecture
# entre les deux frameworks. L'approche correcte consiste à
# réécrire la logique en utilisant les classes et les méthodes de Tkinter
# et de son module ttk.
#
# J'ai réécrit le code de itemctrl.py en créant des mixins et des classes
# adaptées à l'environnement Tkinter. Ce nouveau code, conçu pour
# être utilisé dans le dossier widgetstk que vous avez mentionné,
# permet de reproduire les fonctionnalités principales de la version wxPython.
#
# Points clés de la conversion
#
#     Remplacement des classes wxPython : Les classes de base comme
#     _CtrlWithItemsMixin, _CtrlWithPopupMenuMixin, et les autres mixins
#     de la version wxPython ont été remplacés par des mixins Tkinter.
#     Le ttk.Treeview est utilisé comme équivalent du wx.TreeCtrl et du wx.TreeListCtrl.
#
#     Gestion des événements : Les événements wxPython
#     (ex: wx.EVT_CONTEXT_MENU, wx.EVT_LIST_COL_CLICK) sont remplacés par
#     les événements correspondants de Tkinter (ex: <Button-3>, <Button-1>).
#
#     Mixins et dépendances :
#
#         _CtrlWithDropTargetMixin : J'ai utilisé le module tkinter.dnd et
#         la classe FileTextDropTarget pour gérer les opérations de
#         glisser-déposer de fichiers et de texte, en s'appuyant sur le code
#         que vous aviez déjà pour draganddroptk.py.
#
#         CtrlWithToolTipMixin : Le code réécrit utilise la classe ToolTip
#         du module tooltiptk.py pour afficher les info-bulles.
#
#         _CtrlWithAutoResizedColumnsMixin : Cette fonctionnalité est gérée
#         par la classe TaskList de votre fichier autowidth.py en
#         liant l'événement <Configure>. Une logique pour la colonne redimensionnable a été intégrée.
#
#     Logique de tri et de colonne : La logique pour gérer le tri des colonnes
#     (_CtrlWithSortableColumnsMixin) et les colonnes masquables
#     (_CtrlWithHideableColumnsMixin) a été adaptée à la manière dont le
#     ttk.Treeview gère les en-têtes et les largeurs de colonnes.

# Voici un résumé des points clés de la conversion et des éléments à considérer
# pour compléter le fichier itemctrltk.py afin de le rendre fonctionnel:
# 1. Architecture Générale et Mixins
#
# L'approche de conversion consiste à utiliser des mixins
# pour ajouter des fonctionnalités au widget principal, qui est un ttk.Treeview.
# Les mixins fournissent un moyen d'ajouter des fonctionnalités
# telles que la gestion du menu contextuel, la prise en charge du glisser-déposer,
# l'affichage des info-bulles, le masquage des colonnes et le tri des colonnes.
# Les classes de base wxPython ont été remplacées par des mixins Tkinter,
# notamment _CtrlWithItemsMixin, _CtrlWithPopupMenuMixin et d'autres.
# Le ttk.Treeview est utilisé comme équivalent de wx.TreeCtrl et wx.TreeListCtrl .
#
# 2. Dépendances et Modules Externes
#
# draganddroptk.py : utilisé pour la gestion du glisser-déposer de fichiers et de texte via _CtrlWithDropTargetMixin  .
# tooltiptk.py : utilisé pour afficher les info-bulles via la classe ToolTip et le mixin CtrlWithToolTipMixin .
# autowidthtk.py : utilisé pour la gestion automatique de la largeur des colonnes via la classe TaskList et l'événement <Configure> .
# Il est important de noter que le module tkinter.dnd est utilisé
# pour gérer les opérations de glisser-déposer.
# Le module tkinter.dnd est assez basique et nécessite que la source
# et la cible implémentent des méthodes spécifiques.
# PIL (Pillow) : C'est un module externe très courant pour gérer les images et les icônes .
#
# 3. Éléments à vérifier et à compléter
#
# Gestion des événements: Assurez-vous que tous les événements nécessaires sont correctement liés dans Tkinter. Les événements wxPython comme wx.EVT_CONTEXT_MENU et wx.EVT_LIST_COL_CLICK doivent être remplacés par leurs équivalents Tkinter comme <Button-3> (clic droit) et <Button-1> (clic gauche) .
# Implémentation des méthodes abstraites: La classe TreeCtrlDragAndDropMixin dans draganddroptk.py requiert que la méthode OnDrop soit surchargée dans la classe dérivée . Assurez-vous que cette méthode est correctement implémentée dans votre classe TaskList ou toute autre classe qui utilise ce mixin.
# Compatibilité du glisser-déposer: Le module tkinter.dnd a des limitations. Il faut donc s'assurer que les méthodes requises par tkinter.dnd sont implémentées correctement, comme dnd_enter_callback, dnd_leave_callback et dnd_end_callback  .
# Gestion des données: Dans wxPython, les données sont gérées par les DataObjects . Dans Tkinter, il faut stocker les informations directement dans l'instance de la classe, par exemple en utilisant les tags des éléments du Treeview  .
# Implémentation de getItemTooltipData: La classe CtrlWithToolTipMixin utilise la méthode getItemTooltipData pour obtenir le texte de l'info-bulle. Vous devez implémenter cette méthode dans votre classe dérivée (par exemple, TaskList) pour retourner la chaîne d'info-bulle appropriée  .
# Menu contextuel: La gestion des menus contextuels pour les éléments et les en-têtes de colonnes (_CtrlWithItemPopupMenuMixin et _CtrlWithColumnPopupMenuMixin) nécessite une attention particulière, car Tkinter ne fournit pas d'événements directs pour les en-têtes . Il faut donc gérer les clics manuellement.
# Colonnes masquables et triables : Assurez-vous que la logique pour masquer/afficher les colonnes et pour le tri fonctionne correctement avec le ttk.Treeview .
# Gestion de la largeur des colonnes :  Dans la méthode on_resize, assurez-vous que le calcul de la largeur de la colonne redimensionnable est correct et que la largeur minimale est respectée .
#
# En complétant ces éléments, vous devriez être en mesure de rendre votre widget itemctrltk.py fonctionnel et de reproduire les fonctionnalités de la version wxPython.

# D'après les fichiers que vous avez fournis, itemctrltk.py est une réécriture de itemctrl.py en utilisant Tkinter et ttk pour remplacer wxPython. L'idée est d'utiliser des mixins pour ajouter des fonctionnalités à un ttk.Treeview, comme la gestion des menus contextuels, le glisser-déposer, les info-bulles, le masquage et le tri des colonnes  .
# Analyse des fichiers et des mixins disponibles:
#
# _CtrlWithItemsMixin: Fournit des méthodes de base pour interagir avec les éléments du Treeview .
# _CtrlWithPopupMenuMixin: Ajoute la gestion des menus contextuels .
# _CtrlWithItemPopupMenuMixin: Gère les menus contextuels spécifiques aux éléments .
# _CtrlWithColumnPopupMenuMixin: Gère les menus contextuels pour les en-têtes de colonne .
# _CtrlWithDropTargetMixin: Permet le glisser-déposer de fichiers et d'URLs . Utilise draganddroptk.py pour la gestion du drag-and-drop .
# CtrlWithToolTipMixin: Ajoute des info-bulles à chaque élément. Utilise tooltiptk.py pour afficher les info-bulles .
# _CtrlWithHideableColumnsMixin: Gère l'affichage et le masquage des colonnes .
# _CtrlWithSortableColumnsMixin: Ajoute le tri des colonnes en cliquant sur l'en-tête .
# _CtrlWithAutoResizedColumnsMixin: Gère le redimensionnement automatique des colonnes. Utilise autowidthtk.py pour cette fonctionnalité .
# CtrlWithColumnsMixin: Combine les mixins pour la gestion des colonnes .
# TaskList: La classe principale qui combine tous les mixins et hérite de ttk.Treeview .
#
# Implémentation des méthodes manquantes et finalisation de la conversion:
# Voici une liste de points à vérifier et à compléter, en m'appuyant sur les mixins et les classes disponibles :
#
#
# OnDrop (Glisser-Déposer) :
#
# La classe TreeCtrlDragAndDropMixin dans draganddroptk.py requiert que la méthode OnDrop soit surchargée dans la classe dérivée (TaskList ou une autre classe). Cette méthode est essentielle pour définir ce qui se passe lorsqu'un élément est déposé [[15]]  .
# Assurez-vous que la méthode OnDrop est correctement implémentée dans votre classe TaskList ou toute autre classe qui utilise le mixin TreeCtrlDragAndDropMixin.
# Cette méthode doit définir la logique de déplacement des éléments dans l'arborescence, en utilisant les méthodes move du ttk.Treeview  .
#
# Gestion des colonnes et des en-têtes :
#
# Assurez-vous que la logique pour masquer/afficher les colonnes et pour le tri fonctionne correctement avec le ttk.Treeview  .
# La classe Column dans itemctrltk.py définit les propriétés des colonnes .
# Les mixins _CtrlWithHideableColumnsMixin et _CtrlWithSortableColumnsMixin utilisent ces propriétés pour gérer l'affichage, le masquage et le tri des colonnes  .
# Vérifiez que les méthodes showColumn, sort_by, etc., fonctionnent comme prévu et que les en-têtes des colonnes sont correctement configurés.
#
#
#
# Gestion de la largeur des colonnes :
#
# Dans la méthode on_resize de la classe TaskList, assurez-vous que le calcul de la largeur de la colonne redimensionnable est correct et que la largeur minimale est respectée  .
# Utilisez autowidthtk.py comme référence pour cette implémentation .
#
#
#
# Menu contextuel pour les en-têtes de colonne :
#
# La gestion des menus contextuels pour les éléments et les en-têtes de colonnes (_CtrlWithItemPopupMenuMixin et _CtrlWithColumnPopupMenuMixin) nécessite une attention particulière, car Tkinter ne fournit pas d'événements directs pour les en-têtes  .
# Vous devrez peut-être créer un widget personnalisé pour les en-têtes de colonnes afin de gérer les clics droit et d'afficher le menu contextuel correspondant.
#
#
#
# Compatibilité du glisser-déposer :
#
# Le module tkinter.dnd a des limitations.
# Assurez-vous que les méthodes requises par tkinter.dnd sont implémentées correctement,
# comme dnd_enter_callback, dnd_leave_callback et dnd_end_callback.

# La Solution : Rendre les Mixins "Non-Coopératifs"
#
# Puisque VirtualListCtrl (votre "TreeListCtrl" pour listes) gère l'initialisation explicitement,
# les mixins dans itemctrltk.py ne doivent pas utiliser super().__init__ pour propager les arguments.
# Ils doivent agir comme de simples fonctions de configuration.
# Voici les modifications requises dans itemctrltk.py pour s'adapter à votre architecture :
#
# 1. Fichier : itemctrltk.py
#
# Modifiez les __init__ de tous les mixins de base pour qu'ils n'appellent plus super().__init__.

# Résumé des corrections
#
#     notetk.py : Vous utilisiez un ttk.Treeview basique. Nous l'avons remplacé par votre treectrltk.TreeListCtrl personnalisé, qui est ce que les classes de base (comme SortableViewerWithColumns) attendent.
#
#     itemctrltk.py : Nous avons implémenté les méthodes showSortColumn et showSortOrder (attendues par basetk.py) dans le mixin _CtrlWithSortableColumnsMixin. Ces méthodes gèrent maintenant l'affichage des flèches de tri dans les en-têtes du Treeview.
"""
Compatibilité tkinter pour TreeListCtrl + mixin de colonnes.
Ce module fournit une implémentation sûre qui évite l'erreur:
'TreeListCtrl' object has no attribute 'tk'
"""

from typing import (
    Sequence,
    Optional,
    Callable,
    Any,
    Dict,
    List,
)  # types utilitaires pour lisibilité
import tkinter as tk  # module tkinter principal
from tkinter import ttk, Menu, PhotoImage  # widgets ttk modernes
import logging  # journalisation
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.widgetstk import draganddroptk
from taskcoachlib.widgetstk import tooltiptk
from taskcoachlib.widgetstk import autowidthtk

log = logging.getLogger(__name__)


# --- Mixins de base pour Tkinter (équivalent des mixins wxPython) ---

# Étapes d’intégration
#
# Ajouter des attributs internes dans _CtrlWithItemsMixin pour stocker :
#
# l’item actuellement édité,
#
# la colonne actuellement éditée,
#
# et le widget Entry temporaire.
#
# Gérer le double-clic pour déclencher l’édition.
#
# Créer un champ Entry temporaire pour saisir le nouveau texte.
#
# Mettre à jour la cellule quand l’utilisateur valide (ou annule).
#
# Fournir une méthode publique item_being_edited() (équivalent de TreeTextCtrl.item()).


# Ce que cela fait :
#
# Double-clic → création d’un champ Entry pour modifier la cellule.
#
# Appuyer sur Entrée → enregistre le texte.
#
# Appuyer sur Échap ou cliquer ailleurs → annule.
#
# Tu peux appeler self.item_being_edited() pour savoir quel item est en train d’être modifié.
class _CtrlWithItemsMixin:
    """
    Classe de base pour les contrôles contenant des éléments (ici, ttk.Treeview).

    Fournit des méthodes de base pour interagir avec les éléments du Treeview.

    Responsabilités STRICTES :
    - Vérifier la validité d’un item
    - Associer un objet métier à un item
    - Gérer la sélection

    Ce mixin NE DOIT PAS :
    - Créer de widgets
    - Gérer des événements
    """

    # Solution : Retirer les Arguments de Callback dans _CtrlWithItemsMixin
    # def __init__(self, *args, **kwargs):
    def __init__(
        self, parent, *args, **kwargs
    ):  # master est le premier argument positionnel
        """
        Initialise les structures internes du mixin.

        IMPORTANT :
        - Aucun appel à super().__init__ ici
        - VirtualListCtrl / TreeListCtrl initialise déjà le widget Tkinter
        """
        # Ce mixin est le point où super() atteint finalement object.
        # self est l'instance de VirtualListCtrl (le widget).
        # master, *args, **kwargs sont les arguments passés par VirtualListCtrl.
        # Stockons master pour qu'il soit disponible pour les callbacks (ex: tooltips)
        self.__parent = (
            parent  # Stocker master pour utilisation ultérieure si nécessaire
        )

        # NOUVEAU CODE : Retirer les callbacks de kwargs spécifiques à ce mixin (items)
        self.selectCommand = kwargs.pop("selectCommand", None)
        self.editCommand = kwargs.pop("editCommand", None)
        # Solution : Retirer l'Appel super().__init__ dans les Mixins Abstraits
        #
        # Nous allons corriger les constructeurs des mixins
        # qui n'héritent pas d'un widget Tkinter
        # pour qu'ils n'appellent pas super().__init__(master, ...)
        # et stoppent la propagation de ces arguments vers object.__init__.
        # super().__init__(*args, **kwargs)
        # Consommer le 'master' positionnel pour ne pas le propager à object.__init__
        # Nous n'avons pas besoin de stocker master car self est le widget.

        # MRO va propager l'appel super() à object.
        # object.__init__ n'accepte que self.
        # Donc, nous appelons super() SANS arguments.
        # Nous devons appeler le constructeur de object sans lui passer d'arguments.
        # L'appel super().__init__() atteindra object.__init__()
        # et doit être appelé SANS arguments, car object.__init__(self) n'en prend pas.

        # ATTENTION : Si _CtrlWithItemsMixin est le premier mixin de la liste d'héritage
        # de VirtualListCtrl, il doit appeler le constructeur de ttk.Treeview/Frame
        # S'il ne l'est pas, il doit appeler super() sans arguments.

        # Puisque VirtualListCtrl gère l'initialisation de ttk.Treeview explicitement
        # dans listctrltk.py, les mixins abstraits ne doivent rien propager à object.

        # # Si le mixin est une classe abstraite qui n'hérite de rien d'autre que object:
        # super().__init__()  # Appelle object.__init__(self), fonctionne.
        # NE PAS appeler super().__init__()
        # Note : Étant donné l'héritage complexe, assurez-vous que object.__init__()
        # est le seul constructeur appelé par ce super()
        # et non un autre mixin qui aurait besoin de ces arguments.
        # L'approche la plus simple est de ne propager aucun argument vers object.

        # Note : Si ces arguments étaient passés positionnellement ou via *args,
        # ils ne seraient pas dans **kwargs. Cependant,
        # le code de listctrltk.py les passe par mot-clé,
        # donc .pop() est la bonne solution.
        # Retirer les arguments qui ne sont pas consommés par ce mixin mais qui sont propagés
        # par des appels super() (car ils sont destinés à ttk.Treeview)

        # Correction de la propagation (les mixins abstraits ne doivent pas propager d'arguments non consommés)

        self._entry = None
        self._editing_item = None
        self._editing_column = None
        # # Règle CRITIQUE
        # # 👉 L’objet métier ne doit PAS être stocké dans les tags
        # # ✔️ Utilise un dictionnaire interne :
        # self._item_to_object = {}
        # Dictionnaire interne : item_id -> objet métier
        self._item_to_object: Dict[str, Any] = {}

        # # Bind double-clic pour activer l’édition
        # ANCIEN CODE (CAUSE L'ERREUR DANS LE MRO)
        # self.bind("<Double-1>", self._on_double_click)
        # NOUVEAU CODE (Corriger l'erreur en retirant les bindings ici)
        # La logique de binding doit être déplacée vers la classe CONCRÈTE (VirtualListCtrl ou TaskTree)
        # ou gérée par un mixin qui sait qu'il est la racine du widget.

        # Solution : Laisser _CtrlWithItemsMixin abstrait et gérer le bind dans la classe concrète.
        # En résumé : Le problème était que
        # le code bind s'exécutait sur une instance de mixin non-widget.
        # En le retirant du mixin abstrait, et
        # en ne le plaçant que sur les classes concrètes (comme VirtualListCtrl),
        # nous évitons l'erreur d'architecture.

    def _itemIsOk(self, item: str) -> bool:
        """Vérifie si un élément (item) du Treeview est valide.

        En Tkinter :
        - item == "" signifie « aucun item »

        Args :
            item : identifiant Treeview
        Return :
            True si valide, False sinon
        """
        return bool(item)
        return item != ""

    def _objectBelongingTo(self, item: str) -> Any:
        """Retourne les tags (ou autres données associées) d’un item.

        Retourne l’objet métier associé à un item.

        Équivalent fonctionnel de wx.GetItemPyData.

        Args :
            item: identifiant Treeview
        Return :
            objet métier ou None
        """
        # Si l’item n’est pas valide, aucun objet associé
        if not self._itemIsOk(item):
            return None

        # return self.item(item, 'tags')  # Utilise les tags pour stocker les données
        # # En Tkinter, item() retourne un dictionnaire avec toutes les propriétés
        # return self.item(item).get('tags', None)
        # # acceptable via tags, mais ce n’est pas équivalent à GetItemPyData !

        # item(self) vient de thirdparty.customtreectrl.TreeTextCtrl
        # qui est une classe héritée de wx.lib.expando.ExpandoTextCtrl hérité de wx.TextCtrl.
        # Returns the item currently edited.

        # Retourne l’objet associé ou None
        return self._item_to_object.get(item, None)

    def _setObjectForItem(self, item: str, obj: Any) -> None:
        """
        Associe explicitement un objet métier à un item.

        Cette méthode DOIT être appelée par le viewer lors de l’insertion.

        Args :
            item : identifiant Treeview
            obj : objet métier TaskCoach
        """
        self._item_to_object[item] = obj

    # Description : Cette méthode sélectionne ou désélectionne un élément dans le contrôle.
    # Dans wxPython, elle utilise SelectItem pour TreeCtrl et TreeListCtrl,
    # et SetItemState pour ListCtrl .
    # Version Tkinter : La version Tkinter utilise selection_set et selection_remove du ttk.Treeview .
    def SelectItem(self, item: str, select: bool = True) -> None:
        """Sélectionne ou désélectionne un élément item.

        Args :
            item (str) : identifiant Treeview de l’élément à sélectionner/désélectionner."
            select (bool) : True pour sélectionner, False pour désélectionner.""
        """
        if not self._itemIsOk(item):
            return

        if select:
            self.selection_set(item)  # Sélection Tkinter
        else:
            self.selection_remove(item)  # Désélection Tkinter

    # # --- Partie édition directe ---
    # def _on_double_click(self, event):
    #     """Commence l’édition du texte d’une cellule."""
    #     region = self.identify_region(event.x, event.y)
    #     if region != "cell":
    #         return
    #
    #     item = self.identify_row(event.y)
    #     column = self.identify_column(event.x)
    #     x, y, width, height = self.bbox(item, column)
    #     value = self.set(item, column)
    #
    #     # Création de l’Entry
    #     self._entry = tk.Entry(self)
    #     self._entry.place(x=x, y=y, width=width, height=height)
    #     self._entry.insert(0, value)
    #     self._entry.focus()
    #
    #     self._editing_item = item
    #     self._editing_column = column
    #
    #     # Bindings pour valider ou annuler
    #     self._entry.bind("<Return>", self._save_edit)
    #     self._entry.bind("<Escape>", self._cancel_edit)
    #     self._entry.bind("<FocusOut>", self._cancel_edit)
    #
    # def _save_edit(self, event=None):
    #     """Valide la modification du texte."""
    #     new_value = self._entry.get()
    #     self.set(self._editing_item, self._editing_column, new_value)
    #     self._end_edit()
    #
    # def _cancel_edit(self, event=None):
    #     """Annule l’édition sans enregistrer."""
    #     self._end_edit()
    #
    # def _end_edit(self):
    #     """Nettoie les variables et détruit l’Entry."""
    #     if self._entry:
    #         self._entry.destroy()
    #         self._entry = None
    #         self._editing_item = None
    #         self._editing_column = None
    #
    # def item_being_edited(self):
    #     """Équivalent de TreeTextCtrl.item() — retourne l’item en cours d’édition."""
    #     return self._editing_item


class _CtrlWithPopupMenuMixin(_CtrlWithItemsMixin):
    """
    Classe de base pour les contrôles avec un menu contextuel.

    Mixin de base pour les contrôles avec menu contextuel (Tkinter).
    Cette classe fournit une méthode utilitaire permettant
    d’attacher un gestionnaire de menu contextuel à un widget Tkinter.
    Ajoute la gestion des menus contextuels.

    Elle NE :
    - crée PAS le menu
    - affiche PAS le menu
    - ne contient AUCUNE logique métier

    Elle se contente de lier des événements Tkinter à un gestionnaire.
    """

    def __init__(self, parent, *args, **kwargs):
        """Initialise le mixin."""
        log.debug(
            f"_CtrlWithPopupMenuMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        super().__init__(
            parent, *args, **kwargs
        )  # <-- Doit propager à _CtrlWithItemsMixin

    # def _attachPopupMenu(self, widget, handler):
    @staticmethod
    def _attachPopupMenu(eventSource, eventTypes, eventHandler):
        """
        Lie un gestionnaire d’événements Tkinter pour afficher un menu contextuel.

        Équivalent fonctionnel de wxPython.Bind pour les menus contextuels.

        Args :
            eventSource: widget Tkinter (Treeview, Listbox, etc.)
            eventTypes: liste de chaînes d’événements Tkinter
                        ex : ["<Button-3>", "<Control-Button-1>"]
            eventHandler: fonction appelée lors de l’événement
                          signature attendue : handler(event)
        """
        # widget.bind("<Button-3>", handler)  # Clic droit  TODO : ne fonctionne pas ici, le mettre dans treelistctrl ?
        # if hasattr(self, "handler"):
        #     if hasattr(self, "widget"):
        #         log.debug(f"_CtrlWithPopupMenuMixin._attachPopupMenu : Le bind sur widget={widget} avec handler={handler} ne fonctionne pas pour self={self}.")
        #         # widget.bind("<Button-3>", handler)
        #     else:
        #         log.debug(f"_CtrlWithPopupMenuMixin._attachPopupMenu : self={self}, Pas de widget, handler={handler} !")
        # else:
        #     if hasattr(self, "widget"):
        #         log.debug(f"_CtrlWithPopupMenuMixin._attachPopupMenu : self={self}, widget={widget}, pas de handler !")
        #     else:
        #         log.debug(f"_CtrlWithPopupMenuMixin._attachPopupMenu : self={self.__class__.__name__} n'a ni widget ni handler !")

        # Parcourt tous les types d’événements demandés
        log.debug(
            f"_CtrlWithPopupMenuMixin._attachPopupMenu : Attachement du menu contextuel sur {eventSource} pour les événements {eventTypes} avec handler {eventHandler}."
        )
        for eventType in eventTypes:
            # Attache le gestionnaire à l’événement Tkinter
            eventSource.bind(eventType, eventHandler)
            # eventSource.bind_class(eventType, eventHandler)

        # # Exemple d'utilisation concrète, dans un viewer :
        # self._attachPopupMenu(
        #     eventSource=self,
        #     eventTypes=["<Button-3>"],
        #     eventHandler=self._onPopupMenu
        # )
        # # et le handler :
        # def _onPopupMenu(self, event):
        #     item = self.identify_row(event.y)
        #     if not item:
        #         return
        #     self.SelectItem(item)
        #     self._popupMenu.tk_popup(event.x_root, event.y_root)

    def show_popup_menu(self, event: tk.Event, menu: tk.Menu) -> None:
        """Affiche le menu contextuel."""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class _CtrlWithItemPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """
    Menu contextuel pour des éléments spécifiques du Treeview.

    Gère les menus contextuels spécifiques aux éléments.
    """

    # def __init__(self, *args, **kwargs):
    def __init__(
        self, parent, *args, **kwargs
    ):  # <-- C'est correct, il propage tout à _CtrlWithItemsMixin
        """Initialise le mixin."""
        log.debug(
            "_CtrlWithItemPopupMenuMixin.__init__ : Initialisation du menu contextuel sur les éléments."
        )
        self.__popupMenu = kwargs.pop("itemPopupMenu", None)
        log.debug(
            f"_CtrlWithItemPopupMenuMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(*args, **kwargs)
        super().__init__(parent, *args, **kwargs)
        if self.__popupMenu:
            # self._attachPopupMenu(self, master, self.onItemPopupMenu)  # ?
            self._attachPopupMenu(
                self,
                # (wx.EVT_TREE_ITEM_RIGHT_CLICK, wx.EVT_CONTEXT_MENU),  # par quoi remplacer ?
                # "<Button-3>",  # Clic droit
                # _tkinter.TclError: no event type or button # or keysym
                ["<Button-3>"],  # Liste contenant Clic droit
                self.onItemPopupMenu,
            )
            # _tkinter.TclError: no event type or button # or keysym
            # problème réglé en utilisant bind_class dans _attachPopupMenu
        log.debug("_CtrlWithItemPopupMenuMixin initialisé !")

    def onItemPopupMenu(self, event):
        """Affiche le menu contextuel pour un élément du Treeview."""
        item = self.identify_row(event.y)
        if self._itemIsOk(item):
            # Sélectionne l'élément avant d'afficher le menu
            self.selection_set(item)
            try:
                self.__popupMenu.tk_popup(event.x_root, event.y_root)
            finally:
                self.__popupMenu.grab_release()


class _CtrlWithColumnPopupMenuMixin(_CtrlWithPopupMenuMixin):
    """
    Menu contextuel pour les en-têtes de colonnes du Treeview.

    Gère les menus contextuels pour les en-têtes de colonne.
    """

    # def __init__(self, master, *args, **kwargs):
    def __init__(self, parent, *args, **kwargs):
        """Initialise le mixin."""
        log.debug(
            "_CtrlWithColumnPopupMenuMixin.__init__ : Initialisation du menu contextuel sur les en-têtes de colonnes."
        )
        self.__popupMenu = kwargs.pop("columnPopupMenu", None)
        log.debug(
            f"_CtrlWithColumnPopupMenuMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(master,*args, **kwargs)
        super().__init__(parent, *args, **kwargs)
        if self.__popupMenu:
            # TODO: A revoir avec les nouveaux fichiers (s'il existe heading_widget)
            self._attachPopupMenu(self.heading_widget, self.onColumnPopupMenu)
        log.debug("_CtrlWithColumnPopupMenuMixin initialisé !")

    def onColumnPopupMenu(self, event):
        """Affiche le menu contextuel pour une colonne."""
        # Identification de la colonne cliquée
        # Tkinter ne fournit pas d'événement direct pour les en-têtes.
        # Nous devons donc le gérer manuellement via un surclassement ou une gestion des clics.
        # Pour cet exemple, on peut supposer que l'objet popupMenu gère l'information de la colonne.
        try:
            self.__popupMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.__popupMenu.grab_release()


# Description : Ce mixin permet aux contrôles d'accepter les fichiers,
# URLs ou e-mails déposés . Il utilise draganddrop.DropTarget de wxPython.
# Version Tkinter : La version Tkinter utilise draganddroptk.FileTextDropTarget
# pour gérer les drops. Les callbacks onDropURL, onDropFiles, et onDropMail
# sont gérés par une seule méthode _handle_drop_callback .
class _CtrlWithDropTargetMixin(
    _CtrlWithItemsMixin
):  # <--- Erreur MRO potentielle
    """
    Permet aux contrôles d'accepter des fichiers ou du texte déposés.

    Permet le glisser-déposer de fichiers et d'URLs.
    Utilise draganddroptk.py pour la gestion du drag-and-drop.
    """

    def __init__(self, parent, *args, **kwargs):
        """Initialise le mixin."""
        log.debug(
            "_CtrlWithDropTargetMixin.__init__ : Initialisation pour le glisser-déposer."
        )
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)
        # Propager le reste
        log.debug(
            f"_CtrlWithDropTargetMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        super().__init__(parent, *args, **kwargs)

        # Initialise le gestionnaire de glisser-déposer de draganddrop.py
        if (
            self.__onDropFilesCallback
            or self.__onDropURLCallback
            or self.__onDropMailCallback
        ):
            self.drop_target = draganddroptk.FileTextDropTarget(
                self, self._handle_drop_callback
            )
        log.debug("_CtrlWithDropTargetMixin initialisé !")

    # Assurez-vous que cette méthode gère correctement les différents types
    # de données déposées (fichiers, URLs, texte) et appelle les callbacks
    # appropriés (__onDropFilesCallback, __onDropURLCallback, __onDropMailCallback).
    # L'extrait de code suivant est une autre version de la méthode, plus claire.
    def _handle_drop_callback(self, data):
        """Gestionnaire de rappel générique pour le glisser-déposer."""
        # # On suppose que les données sont des fichiers ou du texte (URL, etc.)
        # if isinstance(data, list):  # C'est une liste de fichiers
        #     # C'est un eliste de fichiers
        #     if self.__onDropFilesCallback:
        #         # La méthode onDropFiles nécessite l'élément cible et la liste des fichiers
        #         # Note: ici, on n'a pas les coordonnées, donc on l'applique à la sélection active
        #         selected_item = self.focus()   # Obtient l'élément sélectionné
        #         self.__onDropFilesCallback(self._objectBelongingTo(selected_item), data)
        # else:  # C'est une chaîne de caractères (URL ou mail)
        #     if data.startswith("http://") or data.startswith("https://"):
        #         if self.__onDropURLCallback:
        #             selected_item = self.focus()
        #             self.__onDropURLCallback(self._objectBelongingTo(selected_item), data)
        #     # Logique pour le mail non implémentée dans la version Tkinter de draganddrop
        #     else:
        #         if self.__onDropMailCallback:
        #             selected_item = self.focus()
        #             self.__onDropMailCallback(self._objectBelongingTo(selected_item), data)
        # On suppose que les données sont des fichiers ou du texte (URL, etc.)
        selected_item = self.focus()  # Obtient l'élément sélectionné
        item_data = self._objectBelongingTo(
            selected_item
        )  # Récupère les données de l'élément

        if isinstance(data, list):  # C'est une liste de fichiers
            if self.__onDropFilesCallback:
                self.__onDropFilesCallback(
                    item_data, data
                )  # Passe les données à la callback
        elif isinstance(
            data, str
        ):  # C'est une chaîne de caractères (URL ou mail)
            if data.startswith("http://") or data.startswith("https://"):
                if self.__onDropURLCallback:
                    self.__onDropURLCallback(item_data, data)
            else:  # considéré comme "mail" ou autre texte
                if self.__onDropMailCallback:
                    self.__onDropMailCallback(item_data, data)

    def GetMainWindow(self):
        """Retourne la fenêtre principale."""
        # return self.winfo_toplevel()
        return self.__parent.winfo_toplevel()
        # TODO : A revoir si ne fonctionne pas !
        # try:
        # Tenter l'appel normal
        if isinstance(self, (tk.Tk, tk.Toplevel)):
            return self.winfo_toplevel()
        else:
            # except Exception as e:
            # log.error(f"Erreur lors de l'appel à winfo_toplevel: {e}")
            log.error(
                "_CtrlWithDropTargetMixin.GetMainWindow : Erreur lors de l'appel à winfo_toplevel sur self !"
            )
            # Retourner l'objet Tkinter racine s'il est accessible,
            # ou un objet parent connu (Viewer)
            if hasattr(self, "master") and self.parent:
                # Si le parent est disponible, retourner sa racine
                return self.parent.winfo_toplevel()
            # Sinon, retourner l'instance Tk la plus simple.
            # (Ceci est une mesure de dernier recours pour éviter le crash)
            return self.parent

    def OnDrop(self, drop_item, dragged_items, part):
        """Gère le drop d'éléments dans l'arborescence."""
        print(
            f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}"
        )
        # TODO : Implémenter la logique de déplacement des éléments
        # # Exemple de déplacement simple
        # for item in dragged_items:
        #     if part == "on":
        #         # Déplacer l'élément pour qu'il devienne un enfant
        #         self.move(item, drop_item, "end")
        #     else:
        #         # Déplacer l'élément au-dessus ou en-dessous
        #         index = self.index(drop_item)
        #         if part == "below":
        #             index += 1
        #         self.move(item, self.parent(drop_item), index)


# La classe CtrlWithToolTipMixin utilise la méthode getItemTooltipData
# pour obtenir le texte de l'info-bulle. Vous devez implémenter cette méthode
# dans votre classe dérivée (par exemple, TaskList) pour retourner la chaîne
# d'info-bulle appropriée.
# class CtrlWithToolTipMixin(_CtrlWithItemsMixin, tooltiptk.ToolTip):
class CtrlWithToolTipMixin(
    _CtrlWithItemsMixin
):  # Retirer l'héritage de tooltiptk.ToolTip qui se fait en interne
    """
    Mixin pour afficher des info-bulles par item.

    Ajoute des info-bulles personnalisées à chaque élément du Treeview.
    Ajoute des info-bulles à chaque élément.
    Utilise tooltiptk.py pour afficher les info-bulles.

    Contraintes :
    - Tooltip UNIQUE (pas par colonne)
    - Lecture seule
    - Dépend uniquement de getItemTooltipData()
    """

    def __init__(self, parent, *args, **kwargs):
        """Initialise le mixin Tooltip et l'info-bulle.

        Le widget Tkinter DOIT déjà exister à ce stade.
        """
        log.debug(
            "CtrlWithToolTipMixin.__init__ : Initialisation des info-bulles."
        )
        # self.item_tooltip = tooltiptk.ToolTip(self, text="Default")
        # L'objet `self` (VirtualListCtrl) est un widget Tkinter (Frame/Treeview).
        # # L'initialisation de l'objet ToolTip se fait en interne.
        # Initialisation des structures items
        _CtrlWithItemsMixin.__init__(self, parent, *args, **kwargs)
        log.debug(
            f"CtrlWithToolTipMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(*args, **kwargs)  # <-- PROBLÈME
        # super().__init__(master, *args, **kwargs)  # <-- PROBLÈME
        # Appel explicite au parent mixin
        # _CtrlWithItemsMixin.__init__(self, *args, **kwargs)  # revenir à super().__init__ ?
        # Le ToolTip est initialisé en lui passant le widget `self` (VirtualListCtrl)
        # Il faut s'assurer que self est correctement initialisé avant cet appel.
        # self.item_tooltip = tooltiptk.ToolTip(self, text="Default")  # `self` est maintenant le widget
        # (Note : L'argument pour ToolTip doit être self (le widget),
        # ce qui est correct car VirtualListCtrl a déjà appelé ttk.Treeview.__init__.)
        # Ligne 527 : L'initialisation prématurée est la cause de l'erreur.
        # self.item_tooltip = tooltiptk.ToolTip(self, text="Default")

        # CORRECTION : Initialisation retardée.
        # Création de l’info-bulle Tkinter
        # self.item_tooltip = None
        # self._tooltip = None
        # self._tooltip = tooltiptk.SimpleToolTip(self)  # TODO : Pas encore créé !
        self._tooltip = tooltiptk.ToolTip(self)  # TODO : en attendant !

        # Liaison du mouvement de souris
        # L'erreur `_w` vient de tooltiptk.ToolTip.__init__ -> self._set_bindings() -> self.widget.bind()
        # Dans tooltiptk.ToolTip, `self.widget` fait référence au widget parent passé au constructeur.
        # L'appel à `self.bind("<Motion>", ...)` doit être fait sur le widget lui-même
        # self.bind("<Motion>", self.on_motion_update_tooltip)
        self.bind("<Motion>", self._onMouseMotion)
        log.debug("CtrlWithToolTipMixin initialisé !")

    def _post_init_tooltip(self):
        """Initialise l'info-bulle après que le widget Tkinter (Treeview) est prêt."""
        # if self.item_tooltip is None:
        # if self._tooltip is None:
        if not hasattr(self, "_tooltip"):
            from taskcoachlib.widgetstk import tooltiptk

            # 'self' est maintenant un objet Treeview/TreeListCtrl entièrement initialisé.
            # self.item_tooltip = tooltiptk.ToolTip(self, text="Default")
            self._tooltip = tooltiptk.ToolTip(self, text="Default")

    def on_motion_update_tooltip(self, event):
        """Met à jour l'info-bulle en fonction de l'élément survolé."""
        item = self.identify_row(event.y)
        # if self._itemIsOk(item):
        #     domainObject = self._objectBelongingTo(item)
        #     if domainObject:
        #         # # Le code d'origine utilise getItemTooltipData qui doit être implémenté
        #         # # dans la classe dérivée.
        #         # tooltip_text = self.getItemTooltipData(domainObject)
        #         # La classe principale (Viewer) implémente getItemTooltipData
        #         tooltip_text = self.__adapter.getItemTooltipData(domainObject)  # Supposons que l'adapter est le viewer
        #         if tooltip_text:
        #             self.item_tooltip.text = tooltip_text
        #             self.item_tooltip.show_tooltip_now()
        #         else:
        #             self.item_tooltip.hide_tooltip()
        #     else:
        #         self.item_tooltip.hide_tooltip()
        # remplacer l’appel direct à __adapter par un appel sûr :
        if not self._itemIsOk(item):
            return
        domainObject = self._objectBelongingTo(item)
        if not domainObject:
            # if self.item_tooltip: self.item_tooltip.hide_tooltip()
            if self._tooltip:
                self._tooltip.hide_tooltip()
            return
        # résolution robuste du "provider" de tooltip
        provider = getattr(self, "_tooltip_provider", None) or getattr(
            self, "getItemTooltipData", None
        )
        tooltip_text = None
        if callable(provider):
            # provider peut être la méthode getItemTooltipData(domainObject)
            try:
                tooltip_text = provider(domainObject)
            except TypeError:
                # provider pourrait être un adaptateur ; essaye getItemTooltipData dessus
                if hasattr(provider, "getItemTooltipData"):
                    tooltip_text = provider.getItemTooltipData(domainObject)
        if tooltip_text:
            # self.item_tooltip.text = tooltip_text
            self._tooltip.text = tooltip_text
            # self.item_tooltip.show_tooltip_now()
            self._tooltip.show_tooltip_now()
        else:
            # self.item_tooltip.hide_tooltip()
            self._tooltip.hide_tooltip()
        # Et expose une méthode publique pour que le viewer
        # appelle tree._tooltip_provider = adapter après initialisation
        # (ou mieux, tree.set_tooltip_provider(adapter)).

    def _onMouseMotion(self, event: tk.Event) -> None:
        """
        Met à jour l’info-bulle lors du survol de la souris.

        :param event: événement Tkinter
        """
        # Détermine l’item sous la souris
        item = self.identify_row(event.y)

        # Si aucun item valide, masquer l’info-bulle
        if not self._itemIsOk(item):
            self._tooltip.hide()
            return

        # Récupération de l’objet métier
        obj = self._objectBelongingTo(item)

        # Si aucun objet, pas de tooltip
        if obj is None:
            self._tooltip.hide()
            return

        # Récupération des données de tooltip depuis le viewer
        try:
            tooltip_data = self.getItemTooltipData(obj)
        except AttributeError:
            # Le viewer n’implémente pas les tooltips
            self._tooltip.hide()
            return

        # tooltip_data est une liste de tuples (label, valeur)
        text_lines = [
            f"{label}: {value}" for label, value in tooltip_data if value
        ]

        # Si aucune donnée à afficher
        if not text_lines:
            self._tooltip.hide()
            return

        # Mise à jour du texte
        self._tooltip.set_text("\n".join(text_lines))


# NOTE : Il n'est pas nécessaire de lier "<Motion>" ici car `tooltiptk.ToolTip` le fait déjà
# MAIS, pour la compatibilité avec le code original qui surcharge la gestion de la souris,
# nous devons laisser `CtrlWithToolTipMixin` gérer la liaison d'événement.


# Explication : En forçant CtrlWithItemsMixin (Étape 1)
# à retirer columnPopupMenu et columns,
# nous neutralisons la propagation de ces arguments par la chaîne d'héritage d'Item.
# L'initialisation manuelle dans VirtualListCtrl (Étape 2) garantit que
# ces arguments sont retirés de **kwargs avant l'appel à ttk.Treeview.
#
# Ceci est la solution la plus complète pour gérer le chevauchement d'arguments
# dans cette architecture de mixins.
# En déplaçant le .pop() de selectCommand et editCommand dans CtrlWithItemsMixin
# (qui est le point où les chemins d'héritage se rejoignent),
# et en s'assurant que ttk.Treeview.__init__ est appelé avec des kwargs propres,
# vous devriez résoudre cette TclError persistante.
#
# Vérifiez ensuite si d'autres mixins nécessitent
# l'appel super().__init__(master, *args, **kwargs)
# ou super().__init__(*args, **kwargs)
# ou si la correction de _CtrlWithItemsMixin a suffi.
# class CtrlWithItemsMixin(_CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin, CtrlWithToolTipMixin):
# class CtrlWithItemsMixin(CtrlWithToolTipMixin, _CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin):
class CtrlWithItemsMixin(
    _CtrlWithItemPopupMenuMixin, _CtrlWithDropTargetMixin
):
    """
    Combinaison des mixins pour le comportement d'un Treeview.
    """

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    # pass
    # def __init__(self, master, *args, **kwargs):
    def __init__(self, parent, *args, **kwargs):
        """Initialise le mixin."""
        # # L'ordre d'appel des super() doit respecter le MRO pour passer 'master'
        # # L'ordre MRO va appeler :
        # # 1. _CtrlWithItemPopupMenuMixin.__init__ (retire itemPopupMenu de kwargs)
        # # 2. _CtrlWithDropTargetMixin.__init__ (appelle super(), ne fait rien avec itemPopupMenu)
        # # 3. etc., jusqu'à ttk.Treeview, qui ne devrait PLUS voir itemPopupMenu.
        #
        # # Consommer les arguments spécifiques AUX ITEMS qui ne sont pas consommés par les parents
        # # Ceci est le mixin principal qui doit retirer les arguments de callback.
        # _selectCommand = kwargs.pop("selectCommand", None)
        # _editCommand = kwargs.pop("editCommand", None)
        # # Le problème doit être que `itemPopupMenu` est passé aux mixins de la chaîne
        # # `_CtrlWithDropTargetMixin` (dans le MRO).
        #
        # # RETIRONS itemPopupMenu DANS CtrlWithItemsMixin POUR GÉRER LE MRO
        # # super().__init__(master, *args, **kwargs)
        # # # # Stocker l'adapter pour le tooltip
        # # # __adapter est initialisé dans le viewer lui-même
        # # # self.__adapter = master
        # # Le MRO va appeler les parents. Assurons-nous que itemPopupMenu est retiré
        # # avant que super() n'atteigne ttk.Treeview via l'autre mixin.
        #
        # # Méthode : Appeler explicitement les parents dans l'ordre pour Tkinter (car MRO est capricieux)
        # # Consommer les arguments spécifiques aux autres mixins pour ne pas les propager
        # # (même si _CtrlWithItemPopupMenuMixin et CtrlWithColumnsMixin le font,
        # # cette redondance est nécessaire dans l'approche d'initialisation explicite).
        # # 1. Argument pour le parent mixin (géré dans _CtrlWithItemPopupMenuMixin)
        # _itemPopupMenu = kwargs.pop("itemPopupMenu", None)  # Retirer ici pour la clarté.
        #
        # # 2. Arguments POUR LE MIXIN COLONNE (mais propagés via cette chaîne, donc on les retire)
        # # Ceci est nécessaire car CtrlWithItemsMixin appelle super() qui atteint ttk.Treeview via l'autre mixin.
        # _columnPopupMenu = kwargs.pop("columnPopupMenu", None)
        # _columns = kwargs.pop("columns", [])  # S'il y a des colonnes ici, on les retire aussi.
        #
        # # # Initialiser les parents sans super() pour Tkinter.
        # # Appels explicites au lieu de super()
        # _CtrlWithItemPopupMenuMixin.__init__(self, master, itemPopupMenu=_itemPopupMenu, *args, **kwargs)
        # _CtrlWithDropTargetMixin.__init__(self, master, *args, **kwargs)
        # # # Propagation à la chaîne d'héritage (qui inclut _CtrlWithItemPopupMenuMixin)
        # # # Propager les arguments RESTANTS (master, *args, **kwargs nettoyés)
        # # # à la chaîne d'héritage (qui atteindra _CtrlWithItemPopupMenuMixin)
        # # super().__init__(master, itemPopupMenu=_itemPopupMenu, *args, **kwargs)  # <-- PROBLÈME
        #
        # # Les arguments retirés (_columnPopupMenu, _columns) peuvent être stockés ici
        # # ou gérés par la classe appelante (VirtualListCtrl).
        # # Stocker les arguments pour la classe concrète si nécessaire
        # self.__selectCommand = _selectCommand
        # self.__editCommand = _editCommand
        # self.__columnPopupMenu = _columnPopupMenu
        # self.__columns = _columns  # Stocker si besoin
        #
        # # NOTE: CtrlWithItemsMixin est censé n'avoir QUE les args relatifs aux items/menu item/drag.
        #
        # # L'objet `self` DOIT être initialisé comme un widget Tk avant d'appeler d'autres constructeurs qui ne sont pas des mixins.
        # # Puisque VirtualListCtrl gère l'initialisation de ttk.Treeview (dans listctrltk.py)
        # # nous devons nous assurer que les arguments sont filtrés EN AMONT de l'appel.
        # pass  # Laissez le super() faire son travail. La solution est dans listctrltk.py.
        # log.debug(f"CtrlWithItemsMixin.__init__ : méthode super avec master={master}, args={args} et kwargs={kwargs}.")
        log.debug(
            f"CtrlWithItemsMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(master, *args, **kwargs)
        super().__init__(parent, *args, **kwargs)


# Description : Cette classe définit les propriétés d'une colonne.
# Version Tkinter : La version Tkinter reste similaire,
# mais sans les références spécifiques à wxPython comme wx.LIST_FORMAT_LEFT.
class Column(object):
    """
    Décrit une colonne logique du ListViewer.
    Définit les propriétés d'une colonne pour le ttk.Treeview.
    """

    # def __init__(self, name, header, *eventTypes, width=100, **kwargs):
    # def __init__(self, name, header, *eventTypes, **kwargs):
    # def __init__(self, id: str, name: str, header: str, *eventTypes,
    def __init__(
        self,
        name: str,
        header: str,
        *eventTypes,
        width: int = 100,
        renderCallback: Callable[[Any], str] = None,
        alignment: str = "w",
        is_shown: bool = True,
        **kwargs,
    ):
        """
        Initialise une colonne.

        Args:
            id: identifiant unique de la colonne
            name: nom interne (clé logique)
            header: texte affiché dans l’en-tête
            *eventTypes: types d'événements associés à la colonne
            width: largeur initiale
            renderCallback: fonction de rendu obj -> texte
            alignment: alignement du texte ('w', 'e', 'center')
            is_shown: colonne visible ou non
            **kwargs: autres arguments optionnels
        """
        # self.id = id
        self._name = name
        self._header = header
        self.width = width
        # ou :
        # self.width = kwargs.pop("width", 100)

        self.__eventTypes = eventTypes
        self.__sortCallback = kwargs.pop("sortCallback", None)
        # # self._render = renderCallback or (lambda obj: "")
        # self.__renderCallback = kwargs.pop(
        #     "renderCallback", self.defaultRenderer
        # )
        self.__renderCallback = renderCallback or self.defaultRenderer
        # self.__resizeCallback = kwargs.pop("resizeCallback", None)
        # self.__alignment = alignment
        # self.__alignment = kwargs.pop("alignment", wx.LIST_FORMAT_LEFT)
        self.__alignment = kwargs.pop("alignment", "w")
        self._is_shown = is_shown  # Ajout de l'attribut is_shown
        self.__hasImages = "imageIndicesCallback" in kwargs
        self.__imageIndicesCallback = (
            kwargs.pop("imageIndicesCallback", self.defaultImageIndices)
            or self.defaultImageIndices
        )
        # # NB: because the header image is needed for sorting a fixed header
        # # image cannot be combined with a sortable column
        self.__headerImageIndex = kwargs.pop("headerImageIndex", -1)
        self.__editCallback = kwargs.get("editCallback", None)
        self.__editControlClass = kwargs.get("editControl", None)
        self.__parse = kwargs.get(
            "parse", lambda value: value
        )  # utilisé dans parse()
        self.__settings = kwargs.get(
            "settings", None
        )  # FIXME: Column shouldn't need to know about settings

        # # La colonne ne devrait pas avoir besoin de connaître les paramètres.

    # def identifier(self) -> str:
    #     """Retourne l'identifiant unique de la colonne."""
    #     log.debug(f"Column.identifier() renvoie l'identifiant unique {self.id} de la colonne.")
    #     return self.id

    # def name(self):
    def name(self) -> str:
        """Retourne le nom interne de la colonne."""
        log.debug(
            f"Column.name() renvoie le nom interne {self._name} de la colonne self {self}."
        )
        return self._name

    # def header(self):
    def header(self) -> str:
        """Retourne le texte de l'en-tête de la colonne."""
        log.debug(
            f"Column.header() renvoie le texte {self._header} en-tête de la colonne."
        )
        return self._header

    # def eventTypes(self):
    def eventTypes(self) -> list:
        return self.__eventTypes

    # # def setWidth(self, width):
    # def setWidth(self, width: int):
    #     """Définit la largeur de la colonne."""
    #     self.width = width
    #     if self.__resizeCallback:
    #         self.__resizeCallback(self, width)

    def render(self, obj: Any) -> str:
        """
        Produit le texte à afficher pour un objet métier.

        Args :
            obj: objet TaskCoach
        Returns :
            texte affichable
        """
        return str(self.__renderCallback(obj))

    # def defaultRenderer(self, *args, **kwargs):  # pylint: disable=W0613
    def defaultRenderer(self, *args, **kwargs) -> str:  # pylint: disable=W0613
        """Retourne une représentation par défaut de la valeur."""
        return str(args[0])

    def alignment(self) -> str:
        """Retourne l’alignement Tkinter."""
        return self.__alignment

    def add_is_shown_to_column(self):
        """Ajoute la méthode is_shown à la classe Column si elle n'existe pas."""
        if not hasattr(Column, "is_shown"):
            Column.is_shown = self.is_shown()
            # ça affecte la valeur retournée, pas la méthode.
            # Il faut affecter la fonction et non appeler la méthode.
            # Column.is_shown = lambda self: True
            # def _default_is_shown(self): return True
            # Column.is_shown = _default_is_shown
            # (ou définir la méthode comme fonction normale).
            # Tu as déjà is_shown par défaut dans Column,
            # donc add_is_shown_to_column peut être supprimée ou simplifiée.

    # def defaultImageIndices(self, *args, **kwargs):  # pylint: disable=W0613
    def defaultImageIndices(
        self, *args, **kwargs
    ) -> dict:  # pylint: disable=W0613
        """Retourne un dictionnaire d'indices d'images par défaut.
        Tkinter n'en a pas, donc retourne un dictionnaire vide."""
        # return {wx.TreeItemIcon_Normal: -1}
        return {}

    # def imageIndices(self, *args, **kwargs):
    def imageIndices(self, *args, **kwargs) -> dict:
        """Retourne un dictionnaire d'indices d'images."""
        return self.__imageIndicesCallback(*args, **kwargs)

    # def hasImages(self):
    def hasImages(self) -> bool:
        """Indique si la colonne contient des images."""
        return self.__hasImages

    # Pour corriger l'erreur AttributeError: 'Column' object has no attribute 'is_shown',
    # vous devez ajouter la méthode is_shown à la classe Column dans le fichier itemctrltk.py.
    # def is_shown(self):
    def is_shown(self) -> bool:
        """Indique si la colonne est visible."""
        # Par défaut, une colonne est affichée.
        # return True
        return self._is_shown

    def isEditable(self):
        return (
            self.__editControlClass is not None
            and self.__editCallback is not None
        )

    def onEndEdit(self, item, newValue):
        self.__editCallback(item, newValue)

    def editControl(self, parent, item, columnIndex, domainObject):
        value = self.value(domainObject)
        kwargs = dict(settings=self.__settings) if self.__settings else dict()
        # FIXME: Column shouldn't need to know about settings
        # # La colonne ne devrait pas avoir besoin de connaître les paramètres.
        # # pylint: disable=W0142
        # return self.__editControlClass(parent, wx.ID_ANY, item, columnIndex,
        #                                parent, value, **kwargs)
        return self.__editControlClass(
            parent, item, columnIndex, parent, value, **kwargs
        )

    def parse(self, value):
        return self.__parse(value)

    def value(self, domainObject):
        """

        Args:
            domainObject:

        Returns:

        """
        return getattr(domainObject, self.name())()

    def __eq__(self, other):
        return self.name() == other.name()


# Description : Classe de base pour les contrôles avec des colonnes.
# Elle gère l'insertion et la suppression des colonnes.
# Version Tkinter : La version Tkinter adapte la logique d'insertion
# et de suppression des colonnes au ttk.Treeview.
# Explication des changements :
#
#     Nous utilisons maintenant self['displaycolumns'] pour contrôler la visibilité, ce qui est l'option correcte pour un ttk.Treeview existant.
#
#     La méthode _set_columns configure toujours les heading et column pour toutes les colonnes (self._all_columns) lors de l'initialisation du mixin, mais elle ne modifie plus la définition (columns), seulement la visibilité (displaycolumns).
#
#     La méthode showColumn met simplement à jour la liste __visible_columns et réassigne self['displaycolumns'].
# class _BaseCtrlWithColumnsMixin(tk.ttk.Treeview):  # Version pour les tests !!!
class _BaseCtrlWithColumnsMixin:  # Mixin sans hériter de Treeview directement
    """Une classe de base pour tous les contrôles avec des colonnes.

    Notez que cette classe et ses sous-classes ne prennent pas en charge
    l'ajout ou la suppression de colonnes après le paramètre initial des colonnes.

    Mixin qui gère la définition des colonnes et la propriété 'displaycolumns'
    de façon robuste : si le widget tkinter n'est pas encore initialisé
    (pas d'attribut 'tk'), les colonnes sont mises en attente et appliquées
    plus tard via _apply_pending_columns().
    """

    # def __init__(self, *args, **kwargs):
    # def __init__(self, *args, columns: Optional[Sequence[str]] = None,
    #              displaycolumns: Optional[Sequence[str]] = None, **kwargs):
    def __init__(
        self,
        parent,
        *args,
        columns: Optional[Sequence[str]] = None,
        displaycolumns: Optional[Sequence[str]] = None,
        **kwargs,
    ):
        """Initialise les structures internes de colonnes sans toucher au widget.

        Arguments:
        - columns: séquence de noms de colonnes (tous les noms possibles)
        - displaycolumns: sous-séquence de colonnes visibles initialement
        """
        log.debug(
            "_BaseCtrlWithColumnsMixin.__init__ : initialisation de tous les contrôles avec des colonnes."
        )
        # stocke les arguments reçus pour éventuellement les appliquer plus tard
        self.parent = parent  # Stocker une référence au parent
        self._pending_columns_args = (
            {}
        )  # crée le dict pour garder les options à appliquer
        # sauvegarde la liste complète de colonnes demandées (ou vide)
        # Extrait et stocke les colonnes
        # 'columns' est nécessaire pour _set_columns,
        # mais il a déjà été "popped" par CtrlWithColumnsMixin (ligne 587)
        # Assurons-nous que l'argument est bien 'columns'
        # self._all_columns = kwargs.pop("columns")
        # Utilise .pop() avec une valeur par défaut (None).
        # Si 'columns' n'est pas là (parce que _CtrlWithHideableColumnsMixin l'a pris),
        # self._all_columns sera None, et nous ne ferons rien.
        # self._all_columns = kwargs.pop("columns", None)
        self._all_columns = (
            list(columns) if columns is not None else []
        )  # copie sûre
        self._visible_columns = (
            list(displaycolumns)
            if displaycolumns is not None
            else [col.name() for col in self._all_columns if col.is_shown()]
        )
        # # super().__init__(*args, **kwargs)
        # # Nous devons nous assurer que tous les mixins dans la chaîne d'héritage
        # # de CtrlWithColumnsMixin appellent super().__init__()
        # # sans arguments supplémentaires s'ils n'héritent pas d'un widget.
        # super().__init__()  # <-- PROBLÈME
        # NE PAS appeler super().__init__()
        # self.__indexMap = []
        # CORRECTION 2 : Ne tente de configurer les colonnes que si elles ont été fournies
        # à ce mixin (ce qui n'est pas le cas si HideableMixin est actif).
        # if self._all_columns is not None:
        #     self._set_columns()
        # calcule quelles colonnes seront visibles par défaut
        # if displaycolumns is not None:
        #     # si displaycolumns fourni, on l'utilise directement
        #     self._visible_columns = list(displaycolumns)  # stocke la liste visible
        # else:
        #     # sinon, on cache la première colonne (habituel 'tree' affichée différemment)
        #     self._visible_columns = list(self._all_columns)  # par défaut toutes visibles
        # marque que les colonnes n'ont pas encore été appliquées au widget
        self._columns_applied = False  # indicateur d'application
        # prépare les arguments à appliquer quand le widget sera prêt
        self._pending_columns_args["displaycolumns"] = tuple(
            self._visible_columns
        )  # prépare tuple

        # essaye immédiatement d'appliquer si le widget est déjà initialisé
        try:
            # test de présence de 'tk' pour savoir si c'est un widget tkinter complet
            if hasattr(self, "tk") and getattr(self, "tk") is not None:
                # si présent, applique tout de suite
                self._apply_pending_columns()  # applique les colonnes
        except Exception:
            # si une erreur survient, on laisse en attente sans interrompre l'init
            self._columns_applied = (
                False  # s'assure que l'attribut reste cohérent
            )
        # Pourquoi ça marche :
        #
        #     Dans TreeListCtrl, vous appelez d'abord ttk.Treeview.__init__.
        #     Cela crée l'attribut self.tk.
        #
        #     Ensuite, vous appelez CtrlWithColumnsMixin.__init__.
        #
        #     Celui-ci détecte que self.tk existe déjà,
        #     et applique immédiatement la configuration des colonnes
        #     via configure(displaycolumns=...).
        #
        #     L'erreur AttributeError: 'TreeListCtrl' object has no attribute 'tk'
        #     est donc définitivement résolue.

        log.debug("_BaseCtrlWithColumnsMixin initialisé !")

    def setColumns(self, columns: List[Column]) -> None:
        """
        Définit les colonnes du Treeview.

        Args :
            columns: liste d’objets Column
        """
        log.debug(
            f"_BaseCtrlWithColumnsMixin : définit les colonnes {columns} du Treeview {self.__class__.__name__}."
        )
        self._columns = columns

        # Accéder à tk via le parent
        tk = self.parent.tk  # Utiliser le tk du parent

        # Configuration Tkinter des colonnes
        self["columns"] = [col.name() for col in self._columns]

        # for col in self._columns:
        #     # Configuration de l’en-tête
        #     self.heading(col.name(), text=col.header())
        #
        #     # Configuration largeur + alignement
        #     self.column(
        #         col.name(),
        #         width=col.width,
        #         anchor=col.alignment()
        #     )
        if tk is not None:
            # Configuration des colonnes
            for col in self._columns:
                # col_id = col.identifier()
                col_name = col.name()
                log.debug(
                    f"_BaseCtrlWithColumnsMixin.setColumns : définit la colonne {col_name} avec {col.header()}"
                )
                self.heading(
                    col_name,
                    text=col.header(),
                    anchor="w",
                    command=lambda c=col_name: self.sort_by(c),
                )
                self.column(
                    col_name, width=col.width, minwidth=50, stretch=True
                )
        else:
            log.warning(
                "_BaseCtrlWithColumnsMixin.setcolumns : tk du parent est None."
            )

    def _set_columns(self):
        """Configure les colonnes initiales."""
        for the_column in self._all_columns:
            log.debug(
                f"_BaseCtrlWithColumnsMixin._set_columns : définit la colonne {the_column.name()} avec {the_column.header()}"
            )
            self.heading(the_column.name(), text=the_column.header())
            self.column(the_column.name(), width=the_column.width, minwidth=20)

    # def _allColumns(self):
    def _all_columns(self) -> Sequence[str]:
        """Retourne toutes les colonnes."""
        return self._all_columns

    def _set_columns_now(self):
        """
        Méthode qui effectue réellement la configuration des colonnes sur le widget.
        Doit être appelée uniquement quand le widget tkinter est prêt (attribut 'tk').
        """
        # seulement appliquer si pas déjà appliqué et si _pending_columns_args existe
        if hasattr(self, "_columns_applied") and self._columns_applied:
            # si déjà appliqué, ne rien faire
            return
        # récupère la valeur pour displaycolumns
        if hasattr(self, "_pending_columns_args"):
            displaycols = self._pending_columns_args.get("displaycolumns", ())
            # si l'objet supporte configure (widget classique), on l'utilise
            if hasattr(self, "configure"):
                # applique la configuration 'displaycolumns' sur l'instance widget
                try:
                    self.configure(
                        displaycolumns=displaycols
                    )  # configure le widget ttk.Treeview
                except Exception:
                    # si configure échoue (par ex. options non reconnues), on ignore silencieusement
                    pass
            else:
                # si configure non disponible, on tente l'indexation dictionnaire (autre API)
                try:
                    self["displaycolumns"] = (
                        displaycols  # alternative, peut lever erreur
                    )
                except Exception:
                    # si encore échoue, on ne fait rien
                    pass
            # marque comme appliqué
            self._columns_applied = (
                True  # met à True pour éviter double-application
            )

    def _apply_pending_columns(self):
        """
        Si des colonnes sont en attente et que le widget est prêt, applique-les.
        Cette méthode est sûre à appeler plusieurs fois.
        """
        # vérifie que l'objet est un widget tkinter prêt
        if not (hasattr(self, "tk") and getattr(self, "tk") is not None):
            # si pas prêt, on ne fait rien
            return
        # appelle la méthode qui applique la configuration maintenant
        self._set_columns_now()  # effectue l'application réelle

    def get_all_columns(self) -> Sequence[str]:
        """Retourne la liste complète des colonnes connues."""
        return list(self._all_columns)  # renvoie une copie pour sécurité

    def get_visible_columns(self) -> Sequence[str]:
        """Retourne la liste des colonnes actuellement visibles (celle préparée)."""
        return list(self._visible_columns)  # renvoie une copie pour sécurité


class _CtrlWithHideableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Gère le masquage et l'affichage des colonnes pour un Treeview Tkinter.

    Gère l'affichage et le masquage des colonnes.

    Mixin gérant l'affichage/masquage des colonnes pour un ttk.Treeview.

    Important :
    - Utilise des attributs « protégés » (un seul underscore) pour que
      d'autres mixins / la classe principale puissent y accéder.
    - Ne pas utiliser de double underscore (name-mangling) ici.
    """

    # Utiliser displaycolumns
    #
    # Le mixin _CtrlWithHideableColumnsMixin ne devrait pas toucher à la définition des colonnes (columns).
    # Son rôle est de contrôler quelles colonnes, parmi celles qui sont définies, sont visibles.
    # C'est précisément ce que fait l'option displaycolumns du ttk.Treeview.
    # def __init__(self, *args, **kwargs):
    def __init__(
        self,
        parent,
        *args,
        columns: Optional[Sequence[str]] = None,
        displaycolumns: Optional[Sequence[str]] = None,
        **kwargs,
    ):
        """Initialise le mixin et configure les colonnes."""
        log.debug("_CtrlWithHideableColumnsMixin.__init__ : initialisation.")
        # Extrait la liste d'objets Column passée via kwargs
        # Extrait les colonnes AVANT d'appeler super()
        # self._all_columns = kwargs.pop("columns")
        # columns = kwargs.pop("columns")  # consomme l'argument 'columns'
        log.debug(
            f"_CtrlWithHideableColumnsMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(*args, **kwargs)  # initialise la logique de base des colonnes
        super().__init__(
            parent,
            *args,
            columns=columns,
            displaycolumns=displaycolumns,
            **kwargs,
        )
        # # AJOUTER CETTE LIGNE : Stocke la liste complète des colonnes
        # # Stocke toutes les colonnes dans un attribut accessible (_all_columns)
        # self._all_columns = columns  # <--- CORRECTION AJOUTÉE. copie de sécurité de la liste d'objets Column
        # # Calcule la liste des colonnes visibles par défaut (noms internes)
        # # Utilise la méthode is_shown() des objets Column, si elle existe.
        # # # self.__visible_columns = [col.name() for col in self.__allColumns]
        # # self.__visible_columns = [col.name() for col in columns]
        # self._visible_columns = [col.name() for col in self._all_columns if col.is_shown() ] if self._all_columns else None  # Utilise _all_columns ici
        # # self._visible_columns = [col.name() for col in self._all_columns if getattr(col, "is_shown", lambda: True)()]  # noms visibles
        # # self._set_columns()  # Appelle la méthode corrigée qui utilise displaycolumns
        # # Définit un état local indiquant que les colonnes n'ont pas encore été appliquées au widget
        # self._columns_initialized = False  # indicateur simple d'initialisation
        log.debug("_CtrlWithHideableColumnsMixin initialisé !")

    # def _set_columns(self):
    #     """Configure les en-têtes et les propriétés de toutes les colonnes (mais ne change que displaycolumns)."""
    #     # VERSION ACTUELLE (cause le crash)
    #     # self['columns'] = self.__visible_columns
    #
    #     # # VERSION CORRIGÉE : Manipule les colonnes visibles
    #     # self['displaycolumns'] = self._visible_columns
    #     # # TODO : AttributeError: 'TreeListCtrl' object has no attribute 'tk'
    #     # Assigne la liste des colonnes visibles à l'option 'displaycolumns' du Treeview
    #     # self.configure(displaycolumns=self._visible_columns)  # applique la visibilité
    #     # self.configure(displaycolumns=self.get_visible_columns())  # applique la visibilité
    #     self.configure(displaycolumns=self._visible_columns)  # applique la visibilité
    #     # Le reste de la méthode (configuration heading/column) est correct,
    #     # car il configure les propriétés des colonnes déjà définies.
    #     # Configure les propriétés d'en-tête (texte et largeur) pour TOUTES les colonnes
    #     for col in self._all_columns:  # parcourt les objets Column. Utilise _all_columns pour configurer TOUTES les colonnes
    #         self.heading(col.name(), text=col.header())  # définit le texte d'en-tête
    #         self.column(col.name(), width=col.width, minwidth=20)  # définit la largeur minimale
    #     # Marque comme initialisé pour éviter doubles applications
    #     self._columns_initialized = True  # évite ré-applications inutiles

    # j’utilise self.configure(...) au lieu d’indexation self['displaycolumns']
    # pour plus de robustesse ; si le widget n’est pas prêt,
    # j’écris en attente dans _pending_columns_args.
    # (_BaseCtrlWithColumnsMixin gère _apply_pending_columns).
    def showColumn(self, column_name, show=True):
        """Affiche ou cache une colonne identifiée par son nom interne."""
        # Si on veut montrer et que la colonne n'est pas déjà visible
        if show and column_name not in self._visible_columns:
            log.debug(
                f"_CtrlWithHideableColumnsMixin.showColumn : ajoute {column_name} à la liste {self._visible_columns}."
            )
            self._visible_columns.append(
                column_name
            )  # ajoute à la liste visible
            # Correction: Trie en fonction de l'ordre dans _all_columns
            # Trie la liste visible selon l'ordre défini par _all_columns
            # self._visible_columns.sort(key=lambda x: [c.name() for c in self._all_columns].index(x))
            order = [c.name() for c in self._all_columns]  # ordre maître
            self._visible_columns.sort(
                key=order.index
            )  # trie selon l'ordre maître
        # Si on veut cacher et que la colonne est visible
        elif not show and column_name in self._visible_columns:
            log.debug(
                f"_CtrlWithHideableColumnsMixin.showColumn : retire {column_name} de la liste {self._visible_columns} pour la cacher."
            )
            self._visible_columns.remove(
                column_name
            )  # supprime de la liste visible

        # # VERSION ACTUELLE (incorrecte)
        # # self['columns'] = self.__visible_columns
        # # VERSION CORRIGÉE : Met à jour les colonnes visibles
        # self['displaycolumns'] = self._visible_columns
        # # Pas besoin d'appeler _set_columns() ici, car les colonnes sont déjà définies.
        # # On change juste leur visibilité.
        # # self._set_columns() # <--- SUPPRIME CET APPEL
        # Applique immédiatement la nouvelle visibilité au Treeview
        # (si le widget est prêt, configure() va fonctionner)
        try:
            self.configure(
                displaycolumns=self._visible_columns
            )  # met à jour l'UI
        except Exception:
            # Si le widget n'est pas encore prêt, on laisse l'état en mémoire :
            # _apply_pending_columns() (défini dans _BaseCtrlWithColumnsMixin) l'appliquera plus tard.
            self._pending_columns_args["displaycolumns"] = tuple(
                self._visible_columns
            )  # mise en attente sûre

    def is_column_visible(self, column_name: str) -> bool:
        """Vérifie si une colonne est visible."""
        return column_name in self._visible_columns


# Implémenter showSortColumn dans itemctrltk.py
#
# Maintenant que self.widget est un TreeListCtrl, nous devons
# donner à ce TreeListCtrl (via son mixin _CtrlWithSortableColumnsMixin)
# les méthodes que basetk.py attend.
class _CtrlWithSortableColumnsMixin(_BaseCtrlWithColumnsMixin):
    """
    Ajoute le tri des colonnes en cliquant sur l'en-tête.
    """

    # def __init__(self, *args, **kwargs):
    def __init__(
        self,
        parent,
        *args,
        columns: Optional[Sequence[str]] = None,
        displaycolumns: Optional[Sequence[str]] = None,
        **kwargs,
    ):
        """Initialise le mixin et configure le tri."""
        log.debug(
            "_CtrlWithSortableColumnsMixin.__init__ : initialisation du tri des colonnes."
        )
        # --- MODIFICATION : Appel explicite au __init__ du parent direct ---
        log.debug(
            f"_CtrlWithSortableColumnsMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(*args, **kwargs) # Remplacé par l'appel ci-dessous
        super().__init__(
            parent,
            *args,
            columns=columns,
            displaycolumns=displaycolumns,
            **kwargs,
        )
        # _BaseCtrlWithColumnsMixin.__init__(self, *args, **kwargs)
        # --- Fin MODIFICATION ---
        self.sort_column = None
        self.sort_reverse = False

        # --- NOUVEAU : Charger les icônes de tri ---
        # # (Données brutes pour de petites flèches)
        # self._sort_arrow_up = PhotoImage(data=b'R0lGODlhEAAQAPMAAP///wAAAAAA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAAQAQzEALEhEAJkiRFsoHx+Fzx+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gy1AAA7')
        # self._sort_arrow_down = PhotoImage(data=b'R0lGODlhEAAQAPMAAP///wAAAAAA/wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAAQAQzEMhAhAAVkiRFsoHx+Fzx+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gz1+Gy1AAA7')
        # --- Fin NOUVEAU ---
        # --- MODIFIÉ : Charger les icônes depuis artprovidertk ---
        try:
            # Demander les icônes de taille 16x16 via art_provider_tk
            # Note: artprovidertk.getIcon s'attend au nom de base (sans la taille)
            self._sort_arrow_up = artprovidertk.getIcon(
                "arrow_up_icon", desired_size=(16, 16)
            )
            self._sort_arrow_down = artprovidertk.getIcon(
                "arrow_down_icon", desired_size=(16, 16)
            )

            # Vérifier si les icônes ont été chargées (getIcon retourne None si échec)
            if self._sort_arrow_up is None:
                log.error(
                    "Erreur: Impossible de charger 'arrow_up_icon16x16' depuis artprovidertk."
                )
                self._sort_arrow_up = (
                    PhotoImage()
                )  # Fallback : image vide pour éviter crash
            if self._sort_arrow_down is None:
                log.error(
                    "Erreur: Impossible de charger 'arrow_down_icon16x16' depuis artprovidertk."
                )
                self._sort_arrow_down = PhotoImage()  # Fallback : image vide

        except Exception as e:
            # Gestion d'autres erreurs potentielles (bien que getIcon devrait gérer None)
            log.exception(
                f"Erreur inattendue lors du chargement des icônes de tri via artprovidertk: {e}"
            )
            self._sort_arrow_up = PhotoImage()
            self._sort_arrow_down = PhotoImage()
        # --- Fin MODIFIÉ ---

        # CORRECTION ICI: Utiliser col.name() et appeler sort_by avec le nom de la colonne
        # Les liaisons 'command' sont gérées par TreeListCtrl/VirtualListCtrl
        # (Les lignes liant self.heading(...) ici doivent être supprimées si elles existent)
        # self.heading("#0", command=lambda: self.sort_by("#0"))
        # Correction : Ne pas utiliser self["columns"] car il n'est pas encore stable
        # et n'est pas censé configurer les en-têtes ici, car c'est la responsabilité
        # de la classe concrète (VirtualListCtrl).

        # RETIRER LA CONFIGURATION DES EN-TÊTES DANS CE MIXIN
        # La configuration complète des en-têtes est faite dans VirtualListCtrl.__init__ (lignes 278-282).

        # Retirez les lignes suivantes dans _CtrlWithSortableColumnsMixin.__init__:
        # for col in self["columns"]:  # <--- ATTENTION : self["columns"] retourne la liste des noms
        #     self.heading(col, command=lambda c=col: self.sort_by(c))  # <--- L'initialisation se fait ici
        # Le code wx original utilisait self["columns"] qui sont des chaînes.
        # Si vous aviez une boucle séparée pour initialiser l'en-tête qui accédait aux objets colonne,
        # la correction doit être appliquée là.
        log.debug("_CtrlWithSortableColumnsMixin initialisé !")

    # ========================================================================
    # GESTION DES COLONNES ET TRI
    # ========================================================================

    def sort_by(self, col_name):
        """Trie les éléments du Treeview par colonne (logique ET UI)."""
        data = [
            (self.set(item, col_name), item) for item in self.get_children("")
        ]

        # # 1. Retirer l'ancienne flèche (si la colonne change)
        # if self.sort_column and self.sort_column != col_name:
        #     self.heading(self.sort_column, image='')
        #
        # # 2. Mettre à jour le statut de tri
        # if col_name == self.sort_column:
        #     self.sort_reverse = not self.sort_reverse
        # else:
        #     self.sort_column = col_name
        #     self.sort_reverse = False
        #
        # # data.sort(reverse=self.sort_reverse)
        # # 3. Définir la nouvelle flèche
        # img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
        # # Assigner l'image à l'en-tête de colonne
        # self.heading(col_name, image=img)
        #
        # 4. Exécuter le tri (logique de données)
        # data = [(self.set(item, col_name), item) for item in self.get_children('')]
        data.sort()
        # data.sort(reverse=self.sort_reverse)
        for index, (val, item) in enumerate(data):
            self.move(item, "", index)

    # # def showSortColumn(self, column):
    # #     if column != self.__currentSortColumn:
    # #         self._clearSortImage()
    # #     self.__currentSortColumn = column
    # #     self._showSortImage()
    # def showSortColumn(self, column):
    #     self.sort_by(column)

    # (REMPLACER l'ancienne méthode showSortColumn (ligne 558))
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
    def showSortColumn(self, column: Column = None):
        """(UI) Affiche l'indicateur de tri sur la colonne actuelle."""
        # 'column' peut être un objet Column (de basetk) ou None (de sortBy)

        if hasattr(self, "sort_column") and self.sort_column:
            order = "↑" if not getattr(self, "sort_reverse", False) else "↓"
            log.debug(
                f"_CtrlWithSortableColumnsMixin.showSortColumn : Tri: {self.sort_column} {order}"
            )

        # # 1. Déterminer le nom de la colonne
        # # col_name = None
        # # if column:  # Appelé par basetk.initColumn
        # if column is not None:
        #     col_name = column.name()
        #     self.sort_column = col_name  # Mémoriser
        # # elif self.sort_column:  # Appelé par basetk.sortBy
        # else:
        #     col_name = self.sort_column
        #
        # if not col_name:
        #     return  # Pas de colonne à trier
        #
        # # # 2. Nettoyer les autres colonnes
        # # for col_id in self["columns"]:
        # #     if col_id != col_name:
        # #         self.heading(col_id, image='')
        # if col_name not in self['columns']:
        #     print(f"[ERREUR] showSortColumn appelé avec un nom de colonne inconnu: {col_name}")
        #     return
        #
        # # 3. Définir la flèche actuelle
        # img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
        # # img = "sort_arrow_down" if self.sort_reverse else "sort_arrow_up"
        # self.heading(col_name, image=img)

    # # (NOUVELLE MÉTHODE : pour corriger la prochaine erreur)
    # def showSortOrder(self, imageIndex=None):
    #     """(UI) Met à jour l'image de la flèche de tri (appelé par basetk)."""
    #     # imageIndex n'est pas pertinent pour Tkinter, on utilise self.sort_reverse
    #     if self.sort_column:
    #         img = self._sort_arrow_down if self.sort_reverse else self._sort_arrow_up
    #         self.heading(self.sort_column, image=img)


# Description : Ce mixin gère le redimensionnement automatique des colonnes.
# Version Tkinter : La version Tkinter utilise une approche basée sur
# l'événement <Configure> pour ajuster la largeur de la colonne redimensionnable.
# Il n'y a plus d'héritage de autowidth.AutoColumnWidthMixin, car cette classe
# a été modifiée pour Tkinter.
class _CtrlWithAutoResizedColumnsMixin(autowidthtk.AutoColumnWidthMixin):
    """Gère le redimensionnement automatique des colonnes.

    Classe de contrôle avec redimensionnement automatique des colonnes.
    Utilise autowidthtk.py pour cette fonctionnalité.
    """

    # def __init__(self, *args, **kwargs):
    def __init__(self, parent, *args, **kwargs):
        # def __init__(self):
        """Initialise le mixin."""
        log.debug(
            "_CtrlWithAutoResizedColumnsMixin.__init__ : initialisation."
        )
        # log.debug(f"_CtrlWithAutoResizedColumnsMixin.__init__ : méthode super avec parent={parent}, args={args} et kwargs={kwargs}.")
        # super().__init__(*args, **kwargs)
        super().__init__(parent, *args, **kwargs)
        # super().__init__()
        # self.bind('<Configure>', self.on_resize)  # <-- Bind event to the Treeview
        # self.bind("<Configure>", self._on_autowidth_resize)
        # TODO : le bind de autowidth.AutoColumnWidthMixin ne fonctionne pas non plus !
        # self.resize_column = None  # Laissez la classe dérivée définir quelle colonne redimensionner
        log.debug("_CtrlWithAutoResizedColumnsMixin initialisé !")

    # # Méthode de gestion de l'événement de redimensionnement
    # Voir dans autowidthtk.py qui la remplace.
    # Si vous gardez la méthode on_resize dans itemctrltk.py,
    # assurez-vous qu'elle n'entre pas en conflit avec _on_autowidth_resize.
    # Le mieux est de supprimer la méthode on_resize locale de itemctrltk.py
    # et de laisser ce fichier autowidthtk.py gérer la logique.
    # def on_resize(self, event):
    #     """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
    #     if self.winfo_width() > 1:
    #         total_width = self.winfo_width()
    #         fixed_width = 0
    #         # Calculer la largeur totale des colonnes à largeur fixe
    #         for col in self['columns']:
    #             if col != self.resize_column:
    #                 fixed_width += self.column(col)['width']
    #
    #                 # Définir la largeur de la colonne redimensionnable
    #         resize_width = total_width - fixed_width
    #         if resize_width > 50:
    #             self.column(self.resize_column, width=resize_width)


class CtrlWithColumnsMixin(
    _CtrlWithAutoResizedColumnsMixin,  # <- RETIRÉ car intégré dans Tk.treeviewer
    _CtrlWithHideableColumnsMixin,
    _CtrlWithSortableColumnsMixin,
    _CtrlWithColumnPopupMenuMixin,
):
    """
    Combinaison des mixins pour la gestion des colonnes.

    Fonctionnalités :
    - création des colonnes
    - affichage des valeurs
    """

    # def __init__(self, *args, **kwargs):
    def __init__(self, parent, *args, **kwargs):
        # def __init__(self, master, *args, columns: Optional[Sequence[str]] = None,
        #              displaycolumns: Optional[Sequence[str]] = None,
        #              itemPopupMenu: Any = None, columnPopupMenu: Any = None,
        #              selectCommand: Callable = None, editCommand: Callable = None,
        #              **kwargs):
        """Initialise le mixin Colonnes."""
        log.debug(
            f"CtrlWithColumnsMixin.__init__ : Initialisation avec parent={parent}, args={args} et kwargs={kwargs}."
        )
        # super().__init__(master, *args, **kwargs)
        # super().__init__(master, *args, columns=columns,
        #                  displaycolumns=displaycolumns,
        #                  itemPopupMenu=itemPopupMenu,
        #                  columnPopupMenu=columnPopupMenu,
        #                  selectCommand=selectCommand,
        #                  editCommand=editCommand, **kwargs)
        # # Filtrer les arguments spécifiques aux mixins avant de les passer à super()
        # # Cela empêche que ces arguments arrivent jusqu'à ttk.Treeview
        #
        # # # Extraire et traiter les arguments des mixins, !!! non, surtout pas ici !!!
        # # # 1. Consommer les arguments spécifiques aux colonnes
        # # On récupère les colonnes passées en argument
        # columns = kwargs.pop("columns", [])
        # self._columns = columns  # Stocke les colonnes pour un usage ultérieur
        # columnPopupMenu = kwargs.pop("columnPopupMenu", None)
        # self._columnPopupMenu = columnPopupMenu
        #
        # # 2. CORRECTION : Consommer les arguments spécifiques aux items (pour éviter la propagation à Tkinter via cette chaîne)
        # kwargs.pop("selectCommand", None)
        # kwargs.pop("editCommand", None)
        #
        # # 3. Propagation des arguments restants (master, *args, **kwargs nettoyés)
        # log.debug(f"CtrlWithColumnsMixin.__init__ : appel de super() avec master={master}, args={args}, columns={columns}, columnPopupMenu={columnPopupMenu}, kwargs={kwargs}.")
        log.debug(
            f"CtrlWithColumnsMixin.__init__ : appel de super() avec parent={parent}, args={args}, kwargs={kwargs}."
        )
        # # # Passer les arguments filtrés à la chaîne d'héritage
        super().__init__(parent, *args, **kwargs)
        # # # super().__init__(columns=columns, columnPopupMenu=columnPopupMenu, *args, **kwargs)
        # # super().__init__(master, columns=columns, columnPopupMenu=columnPopupMenu, *args, **kwargs)  # <-- PROBLÈME
        # # Appels explicites au lieu de super()
        # _CtrlWithAutoResizedColumnsMixin.__init__(self, master, *args, **kwargs)
        # _CtrlWithHideableColumnsMixin.__init__(self, master, columns=columns, *args, **kwargs)
        # _CtrlWithSortableColumnsMixin.__init__(self, master, columns=columns, *args, **kwargs)
        # _CtrlWithColumnPopupMenuMixin.__init__(self, master, columnPopupMenu=columnPopupMenu, *args, **kwargs)

        # Liste des colonnes Column
        self._columns: List[Column] = []
        log.debug("CtrlWithColumnsMixin initialisé !")

    # def setColumns(self, columns: List[Column]) -> None:
    #     """
    #     Définit les colonnes du Treeview.
    #
    #     :param columns: liste d’objets Column
    #     """
    #     self._columns = columns
    #
    #     # Configuration Tkinter des colonnes
    #     self["columns"] = [col.name() for col in columns]
    #
    #     for col in columns:
    #         # Configuration de l’en-tête
    #         self.heading(col.name(), text=col.header())
    #
    #         # Configuration largeur + alignement
    #         self.column(
    #             col.name(),
    #             width=col.width,
    #             anchor=col.alignment()
    #         )

    # def showColumn(self, column_name, show=True):
    def showColumn(self, column_name: str, show=True):
        """Affiche ou cache une colonne et gère l'indicateur de tri."""
        super().showColumn(column_name, show)
        # Afficher l'indicateur de tri si la colonne qui vient d'être rendue visible est en cours de tri.
        if show and column_name == self._currentSortColumn():
            self._showSortImage()

    def _clearSortImage(self):
        """Effacer l'image de tri si la colonne en question est visible."""
        if self.isColumnVisible(self._currentSortColumn()):
            super()._clearSortImage()

    def _showSortImage(self):
        """Affichez uniquement l'image de tri si la colonne en question est visible."""
        if self.isColumnVisible(self._currentSortColumn()):
            super()._showSortImage()

    def columns(self):
        """Retourne la liste complète des colonnes (objets Column)."""
        return self._all_columns

    def updateItemValues(self, item: str) -> None:
        """
        Met à jour l’affichage d’un item à partir de l’objet métier.

        Args :
            item: identifiant Treeview
        """
        # Vérification item valide
        if not self._itemIsOk(item):
            return

        # Récupération de l’objet métier
        obj = self._objectBelongingTo(item)
        if obj is None:
            return

        # Construction des valeurs de colonnes
        values = [col.render(obj) for col in self._columns]

        # Mise à jour Tkinter
        self.item(item, values=values)


# --- Classes principales combinées pour le Treeview ---
# Utilisée uniquement dans le test.
# TaskList est normalement dans domain.task.tasklist
# class TaskList(CtrlWithItemsMixin, CtrlWithColumnsMixin, ttk.Treeview):
class TaskTree(
    CtrlWithItemsMixin,
    CtrlWithColumnsMixin,
    CtrlWithToolTipMixin,
    ttk.Treeview,
):
    """
    Le Treeview principal de l'application, combinant toutes les fonctionnalités.

    La classe principale qui combine tous les mixins et hérite de ttk.Treeview.
    """

    def __init__(self, parent, **kwargs):
        # Récupère les colonnes si elles sont passées
        # Extraire les colonnes et autres arguments spécifiques
        columns = kwargs.pop("columns", [])
        itemPopupMenu = kwargs.pop("itemPopupMenu", None)
        columnPopupMenu = kwargs.pop("columnPopupMenu", None)

        # super().__init__(master, columns=columns, **kwargs)
        # Initialiser ttk.Treeview avec seulement les arguments qu'il comprend
        ttk.Treeview.__init__(
            self,
            parent,
            columns=[c.name() for c in columns],
            show="tree headings",
            **kwargs,
        )
        # ttk.Treeview.__init__(self, master, columns=[c.name() for c in columns], show='tree headings', **kwargs)

        # Initialiser les mixins avec leurs arguments spécifiques
        # CtrlWithItemsMixin.__init__(self, itemPopupMenu=itemPopupMenu)
        CtrlWithItemsMixin.__init__(self, parent, itemPopupMenu=itemPopupMenu)
        log.debug(
            f"TaskTree : {len(columns)} colonnes ({columns}) avant CtrWithColumnsMixin."
        )
        # CtrlWithColumnsMixin.__init__(self, columns=columns, columnPopupMenu=columnPopupMenu)
        # CtrlWithColumnsMixin.__init__(self, master, columns=columns, columnPopupMenu=columnPopupMenu)
        CtrlWithColumnsMixin.__init__(
            self,
            parent,
            columns=[c.name() for c in columns],
            columnPopupMenu=columnPopupMenu,
        )
        log.debug(
            f"TaskTree : {len(columns)} colonnes ({columns}) après CtrWithColumnsMixin."
        )

        # Liez la colonne redimensionnable à l'événement de configuration
        self.bind("<Configure>", self.on_resize)
        # self.bind("<Motion>", self.on_motion_update_tooltip)

        # self.resize_column = 'task_name'  # Définissez la colonne à redimensionner
        # Définir la colonne à étirer :
        #     Dans TaskTree (ou TaskList dans itemctrltk.py),
        #     après avoir créé les colonnes, vous devrez appeler :
        self.SetResizeColumn(
            "task_name"
        )  # ou 'subject', l'ID de la colonne principale
        # Cela garantira que la colonne "Sujet" prend tout l'espace disponible,
        # comportement typique de TaskCoach.
        self.pack(fill=tk.BOTH, expand=True)

    # def on_resize(self, event):
    #     """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
    #     if self.winfo_width() > 1:
    #         total_width = self.winfo_width()
    #         fixed_width = 0
    #
    #         # Calculer la largeur totale des colonnes à largeur fixe
    #         for col in self['columns']:
    #             if col != self.resize_column:
    #                 fixed_width += self.column(col)['width']
    #
    #         # Définir la largeur de la colonne redimensionnable
    #         resize_width = total_width - fixed_width
    #         if resize_width > 50:
    #             self.column(self.resize_column, width=resize_width)

    def getItemTooltipData(self, item_data):
        """
        Retourne le texte de l'info-bulle pour un élément.


        Cette méthode est utilisée par la classe CtrlWithToolTipMixin
        de itemctrltk.py pour obtenir le texte de l'info-bulle.
        Vous devez l'implémenter dans votre classe dérivée (par exemple,
        TaskList) pour retourner la chaîne d'info-bulle appropriée.

        Args:
            item_data:

        Returns:

        """
        # Implémentez la logique pour retourner la chaîne de l'info-bulle
        return f"Détails de l'élément : {item_data}"
        # Remplacez cette implémentation par une logique qui récupère
        # les informations pertinentes de l'objet de données associé
        # à l'élément et les formate en une chaîne à afficher dans l'info-bulle.

    def OnDrop(self, drop_item, dragged_items, part):
        """
        Gère le drop d'éléments.

        Cette méthode doit être surchargée dans la classe dérivée
        (TaskList ou une autre classe) qui utilise le mixin TreeCtrlDragAndDropMixin
        de draganddroptk.py. Elle définit ce qui se passe lorsqu'un élément est déposé.

        Args:
            drop_item:
            dragged_items:
            part:

        Returns:
            None
        """
        print(
            f"Éléments glissés: {dragged_items} sur {drop_item} à la position: {part}"
        )
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


# --- Exemple d'utilisation ---

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,  # DEBUG, Tu peux passer à INFO ou WARNING en production
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("taskcoach.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(),  # Affiche aussi dans la console
        ],
    )

    root = tk.Tk()
    root.title("Exemple de TaskList (Tkinter)")

    # # Définition des colonnes comme dans l'original
    # class Column:
    #     def __init__(self, name, header, width=100):
    #         self._name = name
    #         self._header = header
    #         self.width = width
    #     def name(self): return self._name
    #     def header(self): return self._header

    # Définition des colonnes
    columns = [
        Column("task_name", "Tâche", width=200),
        Column("due_date", "Date d’échéance", width=120),
        Column("priority", "Priorité", width=80),
    ]

    # Crée un menu contextuel de test
    item_menu = Menu(root, tearoff=0)
    item_menu.add_command(label="Modifier")
    item_menu.add_command(label="Supprimer")

    # Crée l'instance de la TaskList
    # task_list = TaskList(root, columns=columns, itemPopupMenu=item_menu, show="headings")
    task_list = TaskTree(root, columns=columns, itemPopupMenu=item_menu)

    # Définir la colonne redimensionnable
    task_list.resize_column = "task_name"

    # Insérer des données de test
    task_list.insert(
        "",
        "end",
        values=("Convertir itemctrl.py", "2025-09-01", "Haute"),
        tags=("task_1",),
    )
    task_list.insert(
        "",
        "end",
        values=("Réécrire la doc", "2025-09-15", "Moyenne"),
        tags=("task_2",),
    )

    root.mainloop()
