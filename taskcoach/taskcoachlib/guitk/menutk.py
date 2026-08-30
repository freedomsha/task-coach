"""
menu.py - Gestion des menus dans Task Coach pour Tkinter.

Ce module contient les classes pour gérer les différents types de menus
utilisés dans Task Coach, adaptés pour une utilisation avec Tkinter.
Il s'agit d'une conversion du module wxPython original.
"""

# C'est un code wxPython assez complexe qui utilise des mixins,
# un système d'observateurs et des commandes UI pour gérer les menus.
#
# Convertir cela en tkinter demande une réécriture significative,
# car l'approche de tkinter est plus simple et moins orienté objet
# que celle de wxWidgets. Les concepts de mixins pour les commandes UI
# (UICommandContainerMixin) et la gestion des événements via pubsub devront
# être adaptés ou remplacés par des mécanismes tkinter équivalents.

# En examinant menutk.py et la façon dont il interagit avec vos autres fichiers
# (en particulier base_uicommandtk.py), je peux vous donner une réponse précise.
#
# 🐛 Analyse de menutk.py
#
# Voici le bilan de votre fichier menutk.py :
#
#     Affichage des noms (Labels) : Oui, cela devrait fonctionner.
#
#         Votre classe Menu dans menutk.py appelle self.add_command(label=menu_text, ...)
#
#         Elle récupère correctement le menu_text depuis l'attribut menuText de vos classes UICommand
#         (définies dans uicommandtk.py).
#
#     Affichage des icônes (Bitmaps) : Non, cela ne fonctionnera pas.
#
#         La raison est simple : dans la méthode Menu.appendUICommand de votre fichier menutk.py,
#         la logique permettant d'ajouter l'icône est commentée.
import tkinter as tk
from tkinter import PhotoImage, ttk
import logging
from os import path as ospath

from taskcoachlib import (
    guitk,
    patterns,
    persistence,
    help,
)  # pylint: disable=W0622
from taskcoachlib.domain import task, base, category
from taskcoachlib.i18n import _

# Les modules suivants devront être adaptés pour Tkinter
# et le reste de votre application.
from taskcoachlib.guitk import artprovidertk, uicommand, viewer
from taskcoachlib.guitk.uicommand import (
    base_uicommandtk,
)  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import (
    uicommandtk as uicommand,
)  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import (
    uicommandcontainertk,
)  # Ceci doit être converti
from taskcoachlib.guitk.uicommand import (
    settings_uicommandtk,
)  # Ceci doit être converti
from taskcoachlib.guitk.viewer import categorytk, efforttk, notetk, tasktk
from pubsub import (
    pub,
)  # Ceci doit être converti ou remplacé par un autre mécanisme
from taskcoachlib import patterns  # Ceci doit être converti

log = logging.getLogger(__name__)


# Je n'ai pas utilisé tk.Menu comme classe parente pour la classe Menu
# pour conserver la structure du code original de Task Coach en wxPython.
#
# Dans le code original, la classe Menu n'hérite pas directement de wx.Menu.
# Au lieu de cela, elle contient une instance de wx.Menu et
# l'utilise pour gérer les commandes.
# C'est un modèle de conception par composition,
# qui dissocie la logique métier de la présentation de l'interface utilisateur.
#
# En suivant ce modèle, ma version tkinter de la classe Menu est un "wrapper" pour tk.Menu.
# Elle encapsule l'objet tk.Menu dans l'attribut _menu et offre une interface
# pour le manipuler (par exemple, appendUICommand).
# Cette approche rend le code plus modulaire et potentiellement plus facile
# à adapter à d'autres frameworks à l'avenir si nécessaire.


# class Menu(uicommandcontainer.UICommandContainerMixin):
# class Menu(tk.Menu, uicommandcontainertk.UICommandContainerMixin):
class Menu(uicommandcontainertk.UICommandContainerMixin, tk.Menu):
    """
    Classe de base pour les menus dans Task Coach
    (comme Fichier, Editer, Affichage, Nouveau, Actions et Aide),
    adaptée pour Tkinter.

    Cette classe gère les éléments de menu, les commandes UI associées
    et même les accélérateurs (raccourcis clavier).
    L'approche est de créer une instance de `tkinter.Menu` et de l'associer
    à un objet parent (par exemple, la fenêtre principale).

    Héritage :
        Elle hérite également de tkinter.Menu, ce qui en fait un menu graphique de Python.
        La classe Menu hérite de uicommandcontainer.UICommandContainerMixin,
        ce qui signifie qu'elle possède la méthode appendUICommands.

    Attributs :
        _window (tk.Tk ou tk.Frame) : Référence à la fenêtre principale.
        # _menu (tk.Menu) -> self : L'instance du menu Tkinter.
        _accels (list) : Liste des raccourcis clavier du menu.
        _observers (list) : Liste des observateurs liés au menu.

    Méthodes :
        __init__(self, window) : Initialise le menu.
        DestroyItem (self, menuItem) : Supprime un élément du menu.
        clearMenu (self) : Supprime tous les éléments du menu.
        appendUICommand (self, uiCommand) : Ajoute une commande UI au menu.
        appendMenu (self, text, subMenu, bitmap=None) : Ajoute un sous-menu.
        invokeMenuItem (self, menuItem) : Invoque un élément de menu de manière programmatique.
        openMenu (self) : Ouvre le menu de manière programmatique.
        accelerators (self) : Retourne la liste des accélérateurs.
    """

    # # def __init__(self, window, tearoff=0):
    def __init__(
        self, parent, parent_mainwindow=None, tearoff=0, *args, **kwargs
    ):
        # def __init__(self, parent_window, *args, **kwargs):
        """
        Initialise un nouveau Menu Tkinter Task Coach.

        Args :
            parent :
                Widget Tkinter parent direct (Menu, Frame ou Tk).
            parent_mainwindow (tk.Tk | tk.Frame) :
                La fenêtre principale Tkinter.
            tearoff :
                Menu détachable ou non.
        """
        #     parent : Fenêtre parente directe.
        #     parent_mainwindow : Fenêtre parente principale.
        #     tearoff : choix de menu déchirable ou non.
        #     *args : Arguments supplémentaires.
        #     **kwargs : Arguments nommés supplémentaires.
        # """
        log.info(
            f"Menu : Création du menu de base pour Tkinter."
            f"Menu : Initialisation de self={self.__class__.__name__}"
        )
        # Appel du constructeur de la classe parente tk.Menu
        # tearoff, menu déchirable ou non.
        # Si vous définissez tearoff = 0,
        # le menu n'aura pas de fonction de déchirement et des choix seront ajoutés à partir de la position 0.
        # --- Détermination de la fenêtre principale AVANT toute assertion ---
        log.debug(
            f"Menu : avec parent={parent} de type {type(parent)} et parent_mainwindow={parent_mainwindow} de type {type(parent_mainwindow)}."
        )
        # Si parent_mainwindow n'est pas fourni, on suppose que parent est la fenêtre principale
        # Je préfère que ce soit clair dans l'appel.
        # À supprimer (ou ne plus utiliser comme fallback) :
        # if parent_mainwindow is None:
        #     # parent_mainwindow = parent
        #     parent_mainwindow = parent.winfo_toplevel()  # Récupère la fenêtre principale Tkinter
        # À imposer :
        # assert parent_mainwindow is not None
        #
        # log.debug(f"Menu : récupère le nom de la fenêtre principale parente parent_mainwindow={parent_mainwindow}.")
        # if not isinstance(parent_mainwindow, (tk.Tk, tk.Toplevel)):
        #     raise AssertionError(
        #         f"{self.__class__.__name__} : parent_mainwindow invalide "
        #         f"({type(parent_mainwindow)}). "
        #         "Types acceptés : tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame, tk.Menu."
        #     )
        uicommandcontainertk.assert_valid_parent_window(
            parent_mainwindow, self
        )
        log.debug(
            f"Menu : récupère le nom de la fenêtre principale parente parent_mainwindow={parent_mainwindow}."
        )
        # --- Initialisation du mixin UICommand (assertion ici) ---
        # uicommandcontainertk.UICommandContainerMixin.__init__(self, parent_window=parent_mainwindow, tearoff=tearoff)
        uicommandcontainertk.UICommandContainerMixin.__init__(
            self, parent_window=parent_mainwindow
        )

        # --- Initialisation du menu Tkinter ---
        # super().__init__(window, tearoff=tearoff)
        # tk.Menu.__init__(self, parent, tearoff=tearoff, *args, **kwargs)
        # uicommandcontainertk.UICommandContainerMixin.__init__(self, parent_window=parent, tearoff=tearoff)
        tk.Menu.__init__(self, parent, tearoff=tearoff, *args, **kwargs)
        # tk.Menu.__init__(self, parent_window, *args, **kwargs)

        # --- Stockage explicite et unique ---
        # self._window = window
        self.__parent = parent  # Stockez la référence au parent direct
        self.__window = parent_mainwindow  # Stockez la référence à la fenêtre principale comme dans la version wxPython
        log.debug(
            f"Menu : self={self.__class__.__name__} et self._window={self.__window.__class__.__name__}"
        )
        # La version wxPython vérifie que _window est bien une instance valide
        # de wx.Window (ou une de ses sous-classes) ici !
        # self._menu = tk.Menu(window, tearoff=tearoff)
        self._accels = []
        self._observers = []
        log.info(
            f"Menu : Fin d'Initialisation de Menu ! (self est {self.__class__.__name__})"
            f"fenêtre principale = {self.__window.__class__.__name__}"
        )

    # @property
    # def tk_menu(self):
    #     """Retourne l'objet tk.Menu pour l'utiliser avec un widget parent."""
    #     return self._menu

    # def __len__(self):
    #     return self.GetMenuItemCount()  # wx. Returns the number of items in the menu.

    def DestroyItem(self, menuItem_id):
        """
        Supprime un élément de menu par son ID.

        Note : Tkinter ne gère pas les objets 'MenuItem' comme wxPython.
        Nous devons utiliser l'ID ou l'index. Ici, nous utilisons l'ID.
        """
        log.info(
            f"Menu.DestroyItem supprime l'élément avec l'ID {menuItem_id}"
        )
        # Suppression de tous les éléments du menu.  TODO ?
        # Retirer tous les liens bind. TODO ?
        # Supprimer l'élément (avec la méthode super()). TODO ?
        try:
            # self._menu.delete(menuItem_id)
            self.delete(menuItem_id)
        except tk.TclError as e:
            log.error(
                f"Erreur lors de la suppression de l'élément de menu avec l'ID {menuItem_id}: {e}"
            )
        # Libérer l'identifiant. TODO ?

    def clearMenu(self):
        """Supprimez tous les éléments du menu."""
        # self._menu.delete(0, tk.END)
        self.delete(0, tk.END)
        # self.delete(0, "end")
        self._accels = []
        self._observers = []
        log.debug(
            "Menu.clearMenu : Tous les éléments et observateurs ont été supprimés."
        )

    def accelerators(self):
        """Retourne la liste des raccourcis clavier du menu."""
        return self._accels

    # def appendUICommands(self, *uiCommands):
    #     """
    #     Ajoute une liste de commandes UI au menu.
    #
    #     Args:
    #         *uiCommands: Une liste de commandes UI ou de séparateurs (None).
    #     """
    #     log.debug(f"Menu.appendUICommands : Ajout des commandes UI au menu {self.__class__.__name__}")
    #     for uiCommand in uiCommands:
    #         if uiCommand is None:
    #             log.debug(f"Menu.appendUICommands : Ajout d'un séparateur au menu {self.__class__.__name__}")
    #             self.add_separator()
    #         else:
    #             try:
    #                 self.appendUICommand(uiCommand)
    #                 log.debug(f"Menu.appendUICommands : Commande {uiCommand.__class__.__name__} ajoutée !")
    #             except Exception as e:
    #                 log.error(f"Menu.appendUICommands : Échec de l'ajout de la commande {uiCommand.__class__.__name__} à cause de {e}", exc_info=True)
    #
    #     # try:
    #     #     # S'il y a un appel à super() ici, il devrait être supprimé
    #     #     # pour utiliser la logique du mixin.
    #     #     # Remplacer cette méthode pour utiliser la logique fournie par UICommandContainerMixin
    #     #     super().appendUICommands(*uiCommands)  # L'appel super() est une erreur car il n'existe pas
    #     #     logging.debug("ColumnPopupMenu.appendUICommands : Commande ajoutée !")
    #     # except Exception as e:
    #     #     logging.error(f"ColumnPopupMenu.appendUICommands : La méthode super plante à cause de {e}.", exc_info=True)
    #     #     # Implémentation manuelle de la logique d'ajout
    #     #     for uiCommand in uiCommands:
    #     #         if uiCommand is None:
    #     #             self.add_separator()
    #     #         else:
    #     #             self.appendUICommand(uiCommand)

    # Le véritable problème est que votre fichier menutk.py essaie de
    # réimplémenter la logique d'ajout d'une commande au menu,
    # alors que vous l'avez déjà parfaitement définie dans votre fichier base_uicommandtk.py !
    #
    # Regardez votre fichier base_uicommandtk.py :
    # la méthode UICommand.addToMenu contient déjà toute la logique nécessaire,
    # y compris la gestion des icônes.
    # La solution : Simplifier menutk.py
    #
    # Pour tout corriger (icônes, noms, et structure du code),
    # il vous suffit de modifier une seule méthode dans menutk.py.
    #
    # Au lieu de dupliquer la logique, la méthode Menu.appendUICommand
    # doit simplement déléguer l'ajout à la méthode addToMenu de la commande elle-même.
    def appendUICommand(self, uiCommand):
        """
        Ajoute une seule commande UI au conteneur, en gérant l'icône si elle est disponible.

        Cette méthode simule le comportement de `wxPython` en utilisant
        les méthodes de `tkinter.Menu`. La logique pour gérer
        les commandes (`uicommand`) et les observateurs devra être
        implémentée dans une classe `UICommand` compatible avec Tkinter.
        """
        # log.info("Menu.appendUICommand called")
        # log.info(f"Menu.appendUICommand ajoute l' uiCommand {uiCommand.__class__.__name__} au menu {self.__class__.__name__}")
        log.info(
            f"Menu.appendUICommand ajoute l' uiCommand {uiCommand.menuText} au menu {self.__class__.__name__} délégué à uiCommand.addToMenu."
        )

        # # Le code wxPython original appelait `uiCommand.addToMenu`.
        # # Pour Tkinter, nous devrons adapter cette logique.
        # # Par exemple, `uiCommand` pourrait avoir une méthode `add_to_tkinter_menu`.
        # # Pour cet exemple, nous allons simuler cela.
        #
        # menu_text = getattr(uiCommand, 'menuText', 'Commande inconnue')
        # command_func = getattr(uiCommand, 'do', None)
        # command_func = uiCommand.onCommandActivate
        # shortcut_text = ''
        # if getattr(uiCommand, 'accelerator', None):
        #     shortcut_text = uiCommand.accelerator
        #
        # # # essai:
        # # menu_options = {
        # #     'label': uiCommand.getMenuText(),
        # #     # 'command': uiCommand.doCommand,
        # #     'command': uiCommand.onCommandActivate,
        # #     'state': 'normal' if uiCommand.enabled() else 'disabled'
        # # }
        #
        # # Tkinter ne gère pas l'état des items de menu de manière aussi directe
        # # que wxWidgets. Le state doit être géré manuellement.
        # state = tk.NORMAL if getattr(uiCommand, 'enabled', True) else tk.DISABLED
        #
        # # # Ajoutez l'icône si elle est disponible
        # # bitmap = uiCommand.getBitmap()
        # # if bitmap:
        # #     # Assurez-vous que l'icône est une instance de PhotoImage de Tkinter
        # #     menu_options['image'] = bitmap
        # #     menu_options['compound'] = tk.LEFT  # Place l'image à gauche du texte
        #
        # # Gérer les différents types de commandes
        # item_type = getattr(uiCommand, 'kind', 'normal')
        #
        # if item_type == 'normal':
        #     log.debug(f"Add normal Command function: {command_func}")
        #     # self._menu.add_command(
        #     self.add_command(
        #         label=menu_text,
        #         command=command_func,
        #         accelerator=shortcut_text,
        #         state=state
        #     )
        # elif item_type == 'check':
        #     log.debug(f"Add checkbutton Command function: {command_func}")
        #     var = tk.BooleanVar(value=getattr(uiCommand, 'checked', False))
        #     # self._menu.add_checkbutton(
        #     self.add_checkbutton(
        #         label=menu_text,
        #         command=command_func,
        #         variable=var,
        #         state=state
        #     )
        # elif item_type == 'radio':
        #     # Les boutons radio nécessitent une variable partagée.
        #     # Cela doit être géré par une classe `UIRadioCommand`.
        #     log.debug(f"Add radiobutton Command function: {command_func}")
        #     log.warning("Les commandes de type 'radio' ne sont pas encore complètement implémentées dans cette version Tkinter.")
        #     # self._menu.add_radiobutton(
        #     self.add_radiobutton(
        #         label=menu_text,
        #         command=command_func,
        #         state=state
        #     )

        # Helper : assure qu'une UICommand a une référence à la fenêtre principale
        def _ensure_main_window(cmd, window):
            if window is None or cmd is None:
                return
            # préférence : méthode publique setMainWindow(window)
            if hasattr(cmd, "setMainWindow"):
                try:
                    cmd.setMainWindow(window)
                    return
                except Exception:
                    log.debug(
                        "Échec de l'appel setMainWindow sur uiCommand, tentative d'affectation d'attributs."
                    )
            # essais d'attributs internes connus
            for attr in (
                "_mainWindow",
                "_window",
                "parent_window",
                "mainwindow",
            ):
                try:
                    if hasattr(cmd, attr) or True:
                        setattr(cmd, attr, window)
                except Exception:
                    # ne pas arrêter sur une erreur d'affectation
                    log.debug(
                        "Impossible d'affecter %s sur %s",
                        attr,
                        cmd.__class__.__name__,
                        exc_info=True,
                    )

        # assure que la commande a une référence à la fenêtre principale utilisée ici
        try:
            _ensure_main_window(uiCommand, self.__window)
        except Exception:
            log.debug(
                "Problème lors de l'initialisation de la main window sur uiCommand",
                exc_info=True,
            )

        # # Utilisez une condition pour déterminer le type de commande à ajouter
        # if hasattr(uiCommand, 'kind'):
        #     # Gérez les cases à cocher et les boutons radio
        #     menu_options['variable'] = uiCommand._variable
        #     menu_options['onvalue'] = True
        #     menu_options['offvalue'] = False
        #     self.add(uiCommand.kind, **menu_options)
        # else:
        #     self.add_command(**menu_options)
        cmd = None
        try:
            # 'self' EST le menu (car Menu hérite de tk.Menu)
            # 'self._window' est la fenêtre parente (définie dans __init__)
            # Attention à ne pas mettre addToMenu 2 fois, sinon duplication de la liste des commandes !
            # uiCommand.addToMenu(menu=self, window=self._window)
            # peut-être faire comme dans la version wxPython
            cmd = uiCommand.addToMenu(
                menu=self, window=self.__window
            )  # TODO : Est-ce que cela fonctionne ? Pas pour 'Save selected task as template'
            # La méthode appendUICommand de menutk.py doit simplement
            # appeler la méthode addToMenu de l'objet UICommand.
            # Cela permet à la classe UICommand de gérer sa propre logique d'ajout au menu.

            # Le reste de la logique pour les accélérateurs et observateurs est correcte
            # self._accels.extend(uiCommand.accelerators())
            # self._accels.extend(getattr(uiCommand, 'accelerators', lambda: [])())  # au cas où c'est vide !
            # récupérer les accélérateurs si la commande les expose
            accels = []
            try:
                accels = getattr(uiCommand, "accelerators", lambda: [])()
            except Exception:
                try:
                    # parfois c'est une propriété liste
                    accels = getattr(uiCommand, "accelerators", []) or []
                except Exception:
                    accels = []
            if accels:
                self._accels.extend(accels)
            log.debug(
                f"Menu.appendUICommand : Le conteneur self={self.__class__.__name__} a les accelerateurs {self._accels}."
            )

            # Gestion des observateurs - observer pattern :
            if isinstance(uiCommand, patterns.Observer):
                self._observers.append(uiCommand)

        except Exception as e:
            log.error(
                f"Menu.appendUICommand : Échec de l'ajout de UICommand '{uiCommand.menuText}' : {e}",
                exc_info=True,
            )
            # Échec de l'ajout de UICommand 'Save selected task as &template' : 'IOController' object has no attribute 'curselection'

        # garde une seconde chance d'ajouter les accélérateurs si la commande expose une méthode différente
        # Ajout des accélérateurs :
        #  Les accélérateurs définis dans la UICommand sont ajoutés
        #  à la liste des accélérateurs du menu.
        try:
            if hasattr(uiCommand, "accelerators"):
                self._accels.extend(uiCommand.accelerators())
        except Exception:
            pass
        # # Gestion des observateurs :
        # #  Si la UICommand est également un observateur (selon le pattern.Observer),
        # #  elle est ajoutée à la liste des observateurs du menu.
        # if isinstance(uiCommand, patterns.Observer):
        #     # Ajoute le menu uiCommand à la liste de menus _observers
        #     self._observers.append(uiCommand)
        if (
            isinstance(uiCommand, patterns.Observer)
            and uiCommand not in self._observers
        ):
            self._observers.append(uiCommand)
        # Retourne cmd :
        #  La variable cmd (qui devrait être l'ID de l'élément de menu retourné
        #  par uiCommand.addToMenu) est retournée.
        return cmd

    def appendMenu(self, text, subMenu, bitmap=None):
        """
        Ajoute un sous-menu à ce menu en vérifiant sa cohérence.

        Cette méthode garantit que tout sous-menu ajouté :
        - est bien un menu Tkinter
        - possède une référence valide vers la fenêtre principale
        - est compatible avec le menu parent

        Args :
            text (str) : Le texte du sous-menu affiché dans le menu parent.
            subMenu (tk.Menu) : Instance du sous-menu à ajouter.
            bitmap (str, optional) : Nom du bitmap optionnel pour l'icône du sous-menu.

        Raises:
            AssertionError:
                Si le sous-menu est mal initialisé ou incohérent.
        """
        # --- Vérification 1 : type du sous-menu ---
        if not isinstance(subMenu, tk.Menu):
            raise AssertionError(
                f"{self.__class__.__name__}.appendMenu : "
                f"le sous-menu '{text}' n'est pas une instance de tk.Menu "
                f"(reçu : {type(subMenu)})."
            )

        # --- Vérification 2 : le menu parent connaît sa fenêtre principale ---
        parent_window = None
        if hasattr(self, "mainWindow"):
            parent_window = self.mainWindow()

        if parent_window is None:
            raise AssertionError(
                f"{self.__class__.__name__}.appendMenu : "
                f"le menu parent ne connaît pas la fenêtre principale. "
                f"Impossible d'ajouter le sous-menu '{text}'."
            )

        # --- Vérification 3 : le sous-menu connaît sa fenêtre principale ---
        submenu_window = None
        if hasattr(subMenu, "mainWindow"):
            submenu_window = subMenu.mainWindow()

        if submenu_window is None:
            raise AssertionError(
                f"{subMenu.__class__.__name__} : "
                f"sous-menu ajouté via appendMenu('{text}') "
                f"sans référence vers la fenêtre principale Tk."
            )

        # --- Vérification 4 : cohérence parent / enfant ---
        if submenu_window is not parent_window:
            raise AssertionError(
                f"{subMenu.__class__.__name__} : incohérence de fenêtre principale.\n"
                f"Menu parent : {parent_window}\n"
                f"Sous-menu     : {submenu_window}\n"
                "Les deux doivent référencer la même fenêtre Tk."
            )

        # TODO : Ajouter les lignes avec icon pour leur intégration dans le sous-menu
        icon = None
        if bitmap:
            icon = artprovidertk.getIcon(bitmap, (16, 16))
        log.debug(
            f"appendMenu : Ajout du sous-menu {text} à la liste des menus de {self.__class__.__name__} et la méthode add_cascade avec l'icône {icon}."
        )
        # --- Ajout effectif du menu ---
        # # self._menu.add_cascade(label=text, menu=subMenu.tk_menu)
        self.add_cascade(label=text, menu=subMenu)
        # self.add_cascade(label=text, menu=subMenu, bitmap=icon)
        # self.add_cascade(label=text, menu=subMenu, bitmap=icon, accelerator=subMenu.accelerators())
        log.debug(
            "%s.appendMenu : sous-menu '%s' (%s) ajouté avec succès.",
            self.__class__.__name__,
            text,
            subMenu.__class__.__name__,
        )
        self._accels.extend(subMenu.accelerators())
        log.debug(f"appendMenu : Sous-menu accelerator {text} ajouté.")

    def add_h_separator(self):
        # def appendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        # self.add_separator()
        # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(
            side=tk.BOTTOM, padx=2
        )  # Ne fonctionne pas directement ici !
        # raise NotImplementedError("La méthode 'AppendSeparator' doit être implémentée par la classe qui utilise ce mixin.")

    # def invokeMenuItem(self, menuItem):
    #     """ Programmatically invoke the menuItem. This is mainly for testing
    #         purposes. """
    #     # log.debug("Menu.invokeMenuItem : Déclenchement programmatique de %s", menuItem)
    #     # self._window.ProcessEvent(wx.CommandEvent(
    #     #     wx.wxEVT_COMMAND_MENU_SELECTED, winid=menuItem.GetId()))
    #     self._window.ProcessEvent(wx.CommandEvent(
    #         wx.wxEVT_COMMAND_MENU_SELECTED, id=menuItem.GetId()))

    # def openMenu(self):
    #     """ Programmatically open the menu. This is mainly for testing
    #         purposes. """
    #     # On Mac OSX, an explicit UpdateWindowUI is needed to ensure that
    #     # menu items are updated before the menu is opened. This is not needed
    #     # on other platforms, but it doesn't hurt either.
    #     self._window.UpdateWindowUI()
    #     self._window.ProcessEvent(wx.MenuEvent(wx.wxEVT_MENU_OPEN, menu=self))

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Crée un sous-menu et y ajoute une liste de commandes UI.

        Args :
            menuTitle : Titre du sous-menu.
            uiCommands : Liste des commandes à ajouter.
        """
        subMenu = Menu(self.__window, tearoff=0)
        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(
            *uiCommands
        )  # Sauf que appendUICommands devrait appartenir à uicommandcontainer.UICommandContainerMixin


class DynamicMenu(Menu):
    """
    Menu dynamique qui se met à jour automatiquement.
    """

    def __init__(
        self, parent, parent_mainwindow, parentMenu=None, labelInParentMenu=""
    ):
        """
        Initialise un menu dynamique.

        Args:
            parent:
                Widget Tkinter parent direct.
            parent_mainwindow:
                Fenêtre principale Tkinter.
            parentMenu:
                Menu parent.
            labelInParentMenu:
                Libellé du menu dans le menu parent.
        """
        log.info("DynamicMenu : Création du menu Dynamique pour Tkinter.")
        log.debug(
            f"DynamicMenu : self={self.__class__.__name__} avec parent={parent} de type {type(parent)} et parent_mainwindow={parent_mainwindow} de type {type(parent_mainwindow)}."
        )
        super().__init__(parent=parent, parent_mainwindow=parent_mainwindow)
        self._parentMenu = parentMenu
        self._labelInParentMenu = self.__GetLabelText(labelInParentMenu)
        self.registerForMenuUpdate()
        # self.updateMenu()
        # self.mainWindow().after_idle(self.updateMenu)  # Différe l'update sauf qu'il ne faut jamais utiliser mainWindow() dans un __init__ !
        parent_mainwindow.after_idle(self.updateMenu)  # Différe l'update

    def registerForMenuUpdate(self):
        """
        Méthode abstraite pour enregistrer le menu aux événements de mise à jour.

        Les sous-classes doivent implémenter cette méthode pour lier des
        événements (`pubsub` ou un autre mécanisme) à `onUpdateMenu`.
        """
        raise NotImplementedError

    def onUpdateMenu(self, newValue=None, sender=None):
        """
        Met à jour le menu lorsque l'événement est déclenché.
        """
        log.debug("DynamicMenu.onUpdateMenu : Mise à jour.")
        self.updateMenu()

    def updateMenu(self):
        """Met à jour les éléments du menu."""
        self.updateMenuItems()

    def updateMenuItems(self):
        """
        La mise à jour des éléments de menu doit être implémentée dans les
        sous-classes.
        """
        pass
        # self.clearMenu()
        # Ici, vous ajouteriez la logique pour peupler le menu
        # en fonction de l'état actuel de l'application.

    def enabled(self):
        """Renvoie un booléen indiquant si ce menu doit être activé."""
        return True

    @staticmethod
    def __GetLabelText(menuText):
        """Supprimez les accélérateurs du menuTexte."""
        return menuText.replace("&", "")


class DynamicMenuThatGetsUICommandsFromViewer(DynamicMenu):
    """
    Menu dynamique qui obtient ses commandes UI d'un visualiseur (`viewer`).
    """

    def __init__(self, viewer, parentMenu=None, labelInParentMenu=""):
        # Super() est appelé sur le constructeur de DynamicMenu, qui lui-même
        # appelle le constructeur de Menu (la classe parente).
        # if parentMenu is None:
        #     parentMenu = self.winfo_toplevel()
        self.__parent = self._viewer = viewer
        self.__window = parentMenu
        self._uiCommands = None
        super().__init__(viewer, parentMenu, parentMenu, labelInParentMenu)

    def registerForMenuUpdate(self):
        """
        Enregistre le menu pour se mettre à jour lorsque la sélection
        du visualiseur change.

        Note : Cette partie doit être adaptée à votre système de
        gestion d'événements pour `viewer`. Pour cet exemple, nous
        supposons un événement `selection_changed`.
        """
        # Vous devrez adapter cette ligne pour votre système d'événements
        # de viewer.
        # Exemple avec pubsub si vous le convertissez :
        # pub.subscribe(self.onUpdateMenu, "viewer.selection_changed")
        log.warning(
            "`DynamicMenuThatGetsUICommandsFromViewer.registerForMenuUpdate` est un placeholder. L'événement doit être lié à votre système de gestion des événements."
        )

    def updateMenuItems(self):
        """
        Met à jour les items du menu en fonction des commandes UI
        disponibles dans le visualiseur.
        """
        self.clearMenu()
        if self._viewer and hasattr(self._viewer, "uiCommands"):
            self._uiCommands = self._viewer.uiCommands()
            self.appendUICommands(*self._uiCommands)

    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands)  # pylint: disable=W0142

    def getUICommands(self):
        raise NotImplementedError


# Ajout de la classe MainMenu
class MainMenu(Menu):
    # class MainMenu(tk.Menu):  # TODO : A essayer
    # MainMenu est celui qui connaît la fenêtre principale (parent).
    # Il doit la transmettre à tous ses enfants.
    """
    Le menu principal de l'application Task Coach, adapté pour Tkinter.

    Classe principale pour la barre de menus.

    Ce menu regroupe plusieurs menus, tels que
    les menus Fichier, Éditer, Affichage, Nouveau, Actions et Aide,
    ainsi que leurs sous-menus respectifs.

    """

    # la classe MainMenu qui prend en charge la création de la barre de menus
    # principale et de ses sous-menus (Fichier, Édition, etc.).
    # Notez que les commandes UI (uicommand.FileNew, uicommand.EditUndo, etc.)
    # devront être converties pour fonctionner correctement avec Tkinter.
    # def __init__(self, parent, iocontroler, settings):
    def __init__(
        self,
        parent,
        parent_window,
        settings,
        iocontroller,
        viewerContainer,
        taskFile,
    ):
        """
        Initialise la barre de menu principale avec tous les sous-menus.

        Args:
            parent : Widget Tkinter auquel le menu est attaché (souvent la fenêtre).
            parent_window: Fenêtre principale Tkinter.
            settings:
            iocontroller:
            viewerContainer:
            taskFile:
        """
        log.info("MainMenu : Création du menu principal.")
        # Assertion explicite pour MainMenu
        # assert parent_window is not None, (
        #     "MainMenu : parent_window est None. "
        #     "La barre de menu doit impérativement connaître la fenêtre principale."
        # )

        assert isinstance(parent_window, tk.Tk), (
            f"MainMenu : parent_window doit être une instance de tk.Tk "
            f"(reçu : {type(parent_window)})."
        )
        log.info(
            f"MainMenu : self={self.__class__.__name__}, parent={parent.__class__.__name__}, parent_window={parent_window.__class__.__name__ if parent_window else 'None'}."
        )
        # Initialisation du menu Tkinter + mixin
        # super().__init__(parent, tearoff=0)  # Ici, parent EST la mainwindow
        # super().__init__(parent, parent_window, tearoff=0)  # Ici, parent EST la mainwindow
        # super().__init__(parent, tearoff=0)  # Ici, parent EST la mainwindow
        super().__init__(
            parent, parent_mainwindow=parent_window, tearoff=0
        )  # Ici, parent EST la mainwindow
        # Stockage des dépendances
        self.taskFile = taskFile  # Ajout de taskFile
        self.settings = settings  # Ajout de settings
        self.viewerContainer = viewerContainer  # Ajout de viewerContainer
        self._iocontroller = iocontroller  # Ajout de iocontroller
        self._settings = settings
        self.parent = parent
        # self.parent_window = parent_window if parent_window else parent
        # self.parent_window = self.winfo_toplevel()
        # if parent_window is None:
        #     parent_window = parent.winfo_toplevel()
        self.parent_window = parent_window

        # Création des sous-menus
        self._create_menus()

        # # 🔥 LIGNE CRUCIALE POUR L’AFFICHAGE 🔥
        # parent_window.config(menu=self)

    def _create_menus(self):
        """Crée et ajoute les menus principaux."""
        # Création des sous-menus
        # self._fileMenu = self.appendSubMenuWithUICommands(
        #     "&Fichier",
        #     (
        #         # uicommand.FileNew(iocontroller=iocontroller),
        #         uicommand.FileOpen(iocontroller=self._iocontroller),
        #         uicommand.FileSave(iocontroller=self._iocontroller),
        #         uicommand.FileSaveAs(iocontroller=self._iocontroller),
        #         None, # Séparateur
        #         # uicommand.RecentFilesMenu(iocontroler),
        #         # None,
        #         # uicommand.ImportMenu(),
        #         # uicommand.ExportMenu(iocontroler),
        #         # None,
        #         uicommand.FileQuit(),
        #     )
        # )
        # Les sous-menus sont des instances de classes de menu dédiées
        # Instanciation des menus
        # self._fileMenu = FileMenu(parent, iocontroler)
        # self._fileMenu = FileMenu(self, self.parent_window, settings, self._iocontroller, viewerContainer)
        # _fileMenu = FileMenu(self, self.parent_window, settings, self._iocontroller, viewerContainer)
        # log.debug(f"FileMenu created: {self._fileMenu}")
        # log.debug(f"FileMenu created: {_fileMenu}")
        # log.debug(f" avec les arguments self={self}, self.parent_window={self.parent_window}, settings={self._settings}, self._iocontroller={self._iocontroller}, viewerContainer={self.viewerContainer}.")
        # Ajout des menus à la barre de menus principale
        # self.appendMenu("&Fichier", self._fileMenu)
        # self.add_cascade(label="&Fichier", menu=self._fileMenu)
        # self.add_cascade(label="&Fichier", menu=_fileMenu)

        # self._editMenu = self.appendSubMenuWithUICommands(
        #     "&Édition",
        #     (
        #         uicommand.EditUndo(),
        #         uicommand.EditRedo(),
        #         None,
        #         uicommand.EditCut(),
        #         uicommand.EditCopy(),
        #         uicommand.EditPaste(),
        #         None,
        #         uicommand.EditFind(),
        #         uicommand.EditFindNext(),
        #         uicommand.EditFindPrevious(),
        #         None,
        #         uicommand.EditSelectAll(),
        #     )
        # )
        # self._editMenu = EditMenu(self, self.parent_window, settings, iocontroller, viewerContainer)
        # # self.appendMenu("&Édition", self._editMenu)
        # self.add_cascade(label="&Édition", menu=self._editMenu)
        #
        # # Les autres menus (View, Tools, Help, etc.) devraient être
        # # ajoutés ici de la même manière que FileMenu et EditMenu.
        # # Pour le moment, ce sont des placeholders.
        # # ajoutés ici en instanciant leurs classes dédiées.
        # self.add_cascade(label="&Vue", menu=Menu(parent, tearoff=0))
        # self.add_cascade(label="&Outils", menu=Menu(parent, tearoff=0))
        # self.add_cascade(label="&Aide", menu=Menu(parent, tearoff=0))
        # for menulisted, text in [
        #     (FileMenu(parent, settings, iocontroller, viewerContainer), _("&File")),
        #     (EditMenu(parent, settings, iocontroller, viewerContainer), _("&Edit")),
        #     (ViewMenu(parent, settings, viewerContainer, taskFile), _("&View")),
        #     (NewMenu(parent, settings, taskFile, viewerContainer), _("&New")),
        #     (ActionMenu(parent, settings, taskFile, viewerContainer), _("&Actions")),
        #     (HelpMenu(parent, settings, iocontroller), _("&Help"))]:
        #     # Mauvaise configuration comme enfant de MainMenu ! :
        #     # création les menus en passant parent(la fenêtre principale) comme maître.
        #     # Problème les menus sont créés comme des nouveaux menu de haut niveau
        #     # rattachés à la fenêtre, au lieu d'être des menus enfant rattachés à MainMenu.
        #     # Les commandes n'apparaitront pas car elles n'appartiennent pas à la bonne hiérarchie.

        # # Correction : Simple. Lors de la création des sous-menus, il faut leur donner self (le mainMenu lui-même)
        # # comme parent, et non la fenêtre principale (parent).
        # # 'parent' est la fenêtre principale (mainwindow)
        # # 'self' est la barre de menu (MainMenu)
        # # Nous passons 'self' comme parent Tkinter aux sous-menus
        # # et 'parent' (la mainwindow) comme 'parent_window' pour les commandes
        # for menulisted, text in [
        #     (FileMenu(self, parent_window, settings, iocontroller, viewerContainer), _("&File")),
        #     (EditMenu(self, parent_window, settings, iocontroller, viewerContainer), _("&Edit")),
        #     (ViewMenu(self, parent_window, settings, viewerContainer, taskFile), _("&View")),
        #     (NewMenu(self, parent_window, settings, taskFile, viewerContainer), _("&New")),
        #     (ActionMenu(self, parent_window, settings, taskFile, viewerContainer), _("&Actions")),
        #     (HelpMenu(self, parent_window, settings, iocontroller), _("&Help"))]:
        for menulisted, text in [
            (
                FileMenu(
                    self,
                    self.parent_window,
                    self.settings,
                    self._iocontroller,
                    self.viewerContainer,
                ),
                _("&File"),
            ),
            (
                EditMenu(
                    self,
                    self.parent_window,
                    self.settings,
                    self._iocontroller,
                    self.viewerContainer,
                ),
                _("&Edit"),
            ),
            (
                ViewMenu(
                    self,
                    self.parent_window,
                    self.settings,
                    self.viewerContainer,
                    self.taskFile,
                ),
                _("&View"),
            ),
            (
                NewMenu(
                    self,
                    self.parent_window,
                    self.settings,
                    self.taskFile,
                    self.viewerContainer,
                ),
                _("&New"),
            ),
            (
                ActionMenu(
                    self,
                    self.parent_window,
                    self.settings,
                    self.taskFile,
                    self.viewerContainer,
                ),
                _("&Actions"),
            ),
            (
                HelpMenu(
                    self, self.parent_window, self.settings, self._iocontroller
                ),
                _("&Help"),
            ),
        ]:
            log.debug(
                f"MainMenu._create_menus : Création du menu {text} avec la liste {menulisted}."
            )
            self._menulisted = menulisted
            log.debug(
                f"MainMenu._create_menus : Appel de appendMenu pour {text}"
            )
            # log.debug(f"MainMenu : Ajout du menu {menulisted}{text} au menuBar MainMenu {self}")
            self.appendMenu(
                text, self._menulisted
            )  # Tous doivent être de forme ('&Name', tk.Menu)
            # self.add_cascade(label=text, menu=self._menulisted)  # Tous doivent être de forme ('&Name', tk.Menu)
            # self.add_cascade(label=text, menu=menulisted)  # Tous doivent être de forme ('&Name', tk.Menu)
            log.debug(f"Menu {text} ajouté avec succès !")

        # Lier le menu à la fenêtre
        # parent.config(menu=self)  # Problème ?
        # self.parent_window.config(menu=self)  # Problème ?
        # self.parent.config(menu=self)  # A essayer !
        log.info(
            "MainMenu : Menu principal configuré pour la fenêtre parente."
        )


class FileMenu(Menu):
    """
    Classe pour le menu "Fichier", adapté pour Tkinter.
    """

    # def __init__(self, parent, settings, iocontroller, viewerContainer):
    def __init__(
        self, parent, parent_window, settings, iocontroller, viewerContainer
    ):
        log.info("FileMenu : Création du menu Fichier.")
        log.info(
            f"FileMenu : self={self.__class__.__name__}, parent={parent.__class__.__name__}, parent_window={parent_window.__class__.__name__ if parent_window else 'None'}."
        )
        # super().__init__(parent, tearoff=0)
        super().__init__(parent, parent_mainwindow=parent_window, tearoff=0)
        self.parent = parent
        self.__window = parent_window
        self.settings = settings
        self._iocontroller = iocontroller
        self._viewerContainer = viewerContainer
        self.add_file_commands()

    def add_file_commands(self):
        """Ajoute les commandes spécifiques au menu Fichier."""
        log.debug("FileMenu : Ajout des commandes.")
        self.appendUICommands(
            # self.appendSubMenuWithUICommands(
            # _("&File"),
            # uicommand.FileNew(iocontroler=iocontroller),
            # (
            uicommand.FileOpen(iocontroller=self._iocontroller),
            uicommand.FileMerge(iocontroller=self._iocontroller),
            uicommand.FileClose(iocontroller=self._iocontroller),
            None,
            uicommand.FileSave(iocontroller=self._iocontroller),
            uicommand.FileMergeDiskChanges(iocontroller=self._iocontroller),
            uicommand.FileSaveAs(iocontroller=self._iocontroller),
            uicommand.FileSaveSelection(
                iocontroller=self._iocontroller, viewer=self._viewerContainer
            ),
            # ),
        )
        # self.add_command(label=uicommand.FileNew[menuText])
        if not self.settings.getboolean("feature", "syncml"):
            self.appendUICommands(
                uicommand.FilePurgeDeletedItems(
                    iocontroller=self._iocontroller
                )
            )
        self.appendUICommands(
            None,
            uicommand.FileSaveSelectedTaskAsTemplate(
                iocontroller=self._iocontroller, viewer=self._iocontroller
            ),
            uicommand.FileImportTemplate(iocontroller=self._iocontroller),
            uicommand.FileEditTemplates(settings=self.settings),
            None,
            uicommand.PrintPageSetup(settings=self.settings),
            uicommand.PrintPreview(
                viewer=self._viewerContainer, settings=self.settings
            ),
            uicommand.Print(
                viewer=self._viewerContainer, settings=self.settings
            ),
            None,  # Séparateur
        )
        self.appendUICommands(
            # uicommand.RecentFilesMenu(iocontroler),  # Ceci est un menu dynamique, à implémenter séparément
            None,
            # uicommand.ImportMenu(), # Ceci est un sous-menu, à implémenter
            # uicommand.ExportMenu(iocontroler), # Ceci est un sous-menu, à implémenter
        )
        self.appendUICommands(
            None,
            uicommand.FileManageBackups(
                iocontroller=self._iocontroller, settings=self.settings
            ),
        )
        if self.settings.getboolean("feature", "syncml"):
            try:
                import taskcoachlib.syncml.core  # pylint: disable=W0612,W0404
            except ImportError:
                pass
            else:
                self.appendUICommands(
                    uicommand.FileSynchronize(
                        iocontroller=self._iocontroller, settings=self.settings
                    )
                )
        # self.__recentFilesStartPosition = len(self)  # ?
        self.appendUICommands(
            None,
            uicommand.FileQuit(),
            # uicommand.FileExit(),
        )
        log.debug("FileMenu : ajouté avec succès !")


class ExportMenu(Menu):
    """
    Le sous-menu "Exporter", adapté pour Tkinter.
    """

    # def __init__(self, parent, iocontroller, settings):
    def __init__(self, parent, parent_window, iocontroller, settings):
        log.info("ExportMenu : Création du menu Exporter.")
        log.info(
            f"ExportMenu : self={self.__class__.__name__}, parent={parent.__class__.__name__}, parent_window={parent_window.__class__.__name__ if parent_window else 'None'}."
        )
        # super().__init__(parent, tearoff=0)
        super().__init__(parent, parent_mainwindow=parent_window, tearoff=0)

        self.appendUICommands(
            # uicommand.ExportToFile(iocontroler=iocontroler, settings=settings),
            # uicommand.ExportAsText(iocontroler=iocontroler, settings=settings),
            uicommand.FileExportAsHTML(
                iocontroller=iocontroller, settings=settings
            ),
            uicommand.FileExportAsCSV(
                iocontroller=iocontroller, settings=settings
            ),
            uicommand.FileExportAsICalendar(
                iocontroller=iocontroller, settings=settings
            ),
            uicommand.FileExportAsTodoTxt(
                iocontroller=iocontroller, settings=settings
            ),
        )


class ImportMenu(Menu):
    """
    Le sous-menu "Importer", adapté pour Tkinter.
    """

    # def __init__(self, parent, iocontroller):
    def __init__(self, parent, parent_window, iocontroller):
        log.info("ImportMenu : Création du menu Importer.")
        log.info(
            f"ImportMenu : self={self.__class__.__name__}, parent={parent.__class__.__name__}, parent_window={parent_window.__class__.__name__ if parent_window else 'None'}."
        )
        # super().__init__(parent, tearoff=0)
        super().__init__(parent, parent_mainwindow=parent_window, tearoff=0)
        self.appendUICommands(
            uicommand.FileImportCSV(iocontroller=iocontroller),
            uicommand.FileImportTodoTxt(iocontroller=iocontroller),
            # uicommand.ImportFromFile(),
            # uicommand.ImportFromIcal(),
        )


class TaskTemplateMenu(DynamicMenu):
    """
    Menu des modèles de tâches dans Task Coach.

    Ce menu permet de gérer les modèles de tâches enregistrés et d'en créer de nouvelles à partir de ces modèles.

    Méthodes :
        registerForMenuUpdate (self) : Enregistre le menu pour recevoir les événements de mise à jour.
        onTemplatesSaved (self) : Met à jour le menu lorsque les modèles sont enregistrés.
        updateMenuItems (self) : Met à jour les éléments du menu.
        fillMenu (self, uiCommands) : Remplit le menu avec les commandes UI.
        getUICommands (self) : Récupère les commandes UI liées aux modèles de tâches.
    """

    # def __init__(self, parent, taskList, settings):
    def __init__(self, parent, parent_window, taskList, settings):
        log.debug("TaskTemplateMenu : Création du menu Modèle de Tâche.")
        log.debug(
            f"TaskTemplateMenu : self={self.__class__.__name__} avec parent={parent} de type {type(parent)} et parent_mainwindow={parent_window} de type {type(parent_window)}."
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.settings = settings
        self.taskList = taskList
        # # super().__init__(parent)
        # super().__init__(parent, parent_mainwindow=self.mainWindow(), parentMenu=parent_window)  # AttributeError: 'TaskTemplateMenu' object has no attribute '_UICommandContainerMixin__window'
        # # Règle ABSOLUE
        # # ❌ Ne jamais appeler self.mainWindow() dans un __init__
        # parent_window est déjà la fenêtre principale Tk, inutile (et dangereux) de la recalculer.
        super().__init__(
            parent, parent_mainwindow=parent_window, parentMenu=parent_window
        )  # TODO : parentMenu=parent ou parent_window ?

    def registerForMenuUpdate(self):
        pub.subscribe(self.onTemplatesSaved, "templates.saved")

    def onTemplatesSaved(self):
        self.onUpdateMenu(None, None)

    def updateMenuItems(self):
        self.clearMenu()
        self.fillMenu(self.getUICommands())

    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands)  # pylint: disable=W0142

    def getUICommands(self):
        path = self.settings.pathToTemplatesDir()
        commands = [
            uicommand.TaskTemplateNew(
                ospath.join(path, name),
                taskList=self.taskList,
                settings=self.settings,
            )
            for name in persistence.TemplateList(path).names()
        ]
        if not commands:
            log.info("Aucun modèle de tâche trouvé dans : %s", path)
        return commands


class EditMenu(Menu):
    """
    Le menu "Édition", adapté pour Tkinter.
    """

    # def __init__(self, parent, settings, iocontroler, viewerContainer):
    def __init__(
        self, parent, parent_window, settings, iocontroler, viewerContainer
    ):
        log.info("EditMenu : Création du menu Édition.")
        # super().__init__(parent, tearoff=0)
        super().__init__(parent, parent_mainwindow=parent_window, tearoff=0)
        self.appendUICommands(
            uicommand.EditUndo(),
            uicommand.EditRedo(),
            None,
            uicommand.EditCut(viewer=viewerContainer),
            uicommand.EditCopy(viewer=viewerContainer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=viewerContainer),
            None,
            uicommand.Edit(viewer=viewerContainer),
            uicommand.Delete(viewer=viewerContainer),
            None,
        )
        #     None,
        #     uicommand.EditFind(),
        #     uicommand.EditFindNext(),
        #     uicommand.EditFindPrevious(),
        #     None,
        #     uicommand.EditSelectAll(),
        # )
        log.debug("EditMenu : devrait être ajouté !")


class SelectMenu(Menu):
    # def __init__(self, parent, viewerContainer):
    def __init__(self, parent, parent_window, viewerContainer):
        log.debug("Création du menu Select/Sélectionner.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        kwargs = dict(viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.SelectAll(**kwargs), uicommand.ClearSelection(**kwargs)
        )


class ViewMenu(Menu):
    """
    Menu View/Affichage dans Task Coach.

    Ce menu contient des options pour gérer l'affichage, les modes de vue, les filtres, les colonnes, etc.
    """

    # def __init__(self, parent, settings, viewerContainer, taskFile):
    def __init__(
        self, parent, parent_window, settings, viewerContainer, taskFile
    ):
        """
        Initialise le menu Voir avec divers sous-menus comme les options d'affichage et les colonnes.

        Args :
            parent :
            settings :
            viewerContainer :
            taskFile :
        """
        log.info(
            f"ViewMenu : Création du menu View/Affichage. {self.__class__.__name__}"
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        # log.debug("ViewMenu : Ajout du menu Nouvelle visualisation.")
        self.appendMenu(
            _("&New viewer"),
            # ViewViewerMenu(parent, settings, viewerContainer, taskFile),
            ViewViewerMenu(
                parent, parent_window, settings, viewerContainer, taskFile
            ),
            # "viewnewviewer",
        )
        activateNextViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("&Activate next viewer\tCtrl+PgDn"),
            helpText=help.viewNextViewer,
            forward=True,
            bitmap="activatenextviewer",
            # id=activateNextViewerId,
        )
        activatePreviousViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("Activate &previous viewer\tCtrl+PgUp"),
            helpText=help.viewPreviousViewer,
            forward=False,
            bitmap="activatepreviousviewer",
            # id=activatePreviousViewerId,
        )
        self.appendUICommands(
            activateNextViewer,
            activatePreviousViewer,
            uicommand.RenameViewer(viewer=viewerContainer),
            None,
        )
        # log.debug("ViewMenu : Ajout du menu : Mode")
        # self.appendMenu(_("&Mode"), ModeMenu(parent, self, _("&Mode")))
        self.appendMenu(
            _("&Mode"), ModeMenu(parent, self.mainWindow(), _("&Mode"))
        )
        # self.appendMenu(
        #     _("&Mode"),
        #     ModeMenu(
        #         parent=parent,
        #         parent_window=self.mainWindow(),
        #         labelInParentMenu=_("&Mode"),
        #     )
        # )

        # # log.debug("ViewMenu : Ajout du menu : Filtre")
        # self.appendMenu(
        #     _("&Filter"), FilterMenu(parent, self, _("&Filter"))
        # )
        self.appendMenu(
            _("&Filter"), FilterMenu(parent, self.mainWindow(), _("&Filter"))
        )
        # log.debug("ViewMenu : Ajout du menu : Sort/tri")
        # self.appendMenu(_("&Sort"), SortMenu(parent, self, _("&Sort")))
        self.appendMenu(
            _("&Sort"), SortMenu(parent, self.mainWindow(), _("&Sort"))
        )
        # # log.debug("ViewMenu : Ajout du menu : Colonnes")
        # self.appendMenu(
        #     _("&Columns"), ColumnMenu(parent, self, _("&Columns"))
        # )
        self.appendMenu(
            _("&Columns"), ColumnMenu(parent, self.mainWindow(), _("&Columns"))
        )
        # # log.debug("ViewMenu : Ajout du menu : Rounding/arrondi")
        # self.appendMenu(
        #     _("&Rounding"), RoundingMenu(parent, self, _("&Rounding"))
        # )
        self.appendMenu(
            _("&Rounding"),
            RoundingMenu(parent, self.mainWindow(), _("&Rounding")),
        )
        self.appendUICommands(None)
        # log.debug("ViewMenu : Ajout du menu : Options d'arborescence")
        self.appendMenu(
            _("&Tree options"),
            # ViewTreeOptionsMenu(parent, viewerContainer),
            ViewTreeOptionsMenu(parent, parent_window, viewerContainer),
            # "treeview"
        )
        self.appendUICommands(None)
        # log.debug("ViewMenu : Ajout du menu : Barre d'Outils")
        # self.appendMenu(_("T&oolbar"), ToolBarMenu(parent, settings))
        self.appendMenu(
            _("T&oolbar"), ToolBarMenu(parent, parent_window, settings)
        )
        self.appendUICommands(
            # uicommand.UICheckCommand(
            settings_uicommandtk.UICheckCommand(
                settings=settings,
                menuText=_("Status&bar"),
                helpText=_("Show/hide status bar"),
                setting="statusbar",
            )
        )
        log.debug("ViewMenu initialisé avec succès !")


class ViewViewerMenu(Menu):
    # def __init__(self, parent, settings, viewerContainer, taskFile):
    def __init__(
        self, parent, parent_window, settings, viewerContainer, taskFile
    ):
        log.info("Création du menu View Viewer.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # import taskcoachlib
        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        ViewViewer = uicommand.ViewViewer
        kwargs = dict(
            viewer=viewerContainer, taskFile=taskFile, settings=settings
        )
        # pylint: disable=W0142
        # TODO : A remettre ! ->
        viewViewerCommands = [
            ViewViewer(
                menuText=_("&Task"),
                helpText=_("Open a new tab with a viewer that displays tasks"),
                viewerClass=guitk.viewer.tasktk.Taskviewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("Task &statistics"),
                helpText=_(
                    "Open a new tab with a viewer that displays task statistics"
                ),
                viewerClass=guitk.viewer.tasktk.TaskStatsViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("Task &square map"),
                helpText=_(
                    "Open a new tab with a viewer that displays tasks in a square map"
                ),
                viewerClass=guitk.viewer.tasktk.SquareTaskViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("T&imeline"),
                helpText=_(
                    "Open a new tab with a viewer that displays a timeline of tasks and effort"
                ),
                viewerClass=guitk.viewer.tasktk.TimelineViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Calendar"),
                helpText=_(
                    "Open a new tab with a viewer that displays tasks in a calendar"
                ),
                viewerClass=guitk.viewer.tasktk.CalendarViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Hierarchical calendar"),
                helpText=_(
                    "Open a new tab with a viewer that displays task hierarchy in a calendar"
                ),
                viewerClass=guitk.viewer.tasktk.HierarchicalCalendarViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Category"),
                helpText=_(
                    "Open a new tab with a viewer that displays categories"
                ),
                viewerClass=guitk.viewer.categorytk.Categoryviewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Effort"),
                helpText=_(
                    "Open a new tab with a viewer that displays efforts"
                ),
                viewerClass=guitk.viewer.efforttk.Effortviewer,
                **kwargs,
            ),
            uicommand.ViewEffortViewerForSelectedTask(
                menuText=_("Eff&ort for selected task(s)"),
                helpText=_(
                    "Open a new tab with a viewer that displays efforts for the selected task"
                ),
                viewerClass=guitk.viewer.efforttk.EffortViewerForSelectedTasks,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Note"),
                helpText=_("Open a new tab with a viewer that displays notes"),
                viewerClass=guitk.viewer.notetk.Noteviewer,
                **kwargs,
            ),
        ]
        try:
            import igraph

            viewViewerCommands.append(
                ViewViewer(
                    menuText=_("&Dependency Graph"),
                    helpText=_(
                        "Open a new tab with a viewer that dependencies between weighted tasks over time"
                    ),
                    viewerClass=guitk.viewer.tasktk.TaskInterdepsViewer,
                    **kwargs,
                )
            )
        except ImportError:
            pass
        self.appendUICommands(*viewViewerCommands)
        log.debug("ViewViewerMenu : devrait être ajouté !")


class ViewTreeOptionsMenu(Menu):
    # def __init__(self, parent, viewerContainer):
    def __init__(self, parent, parent_window, viewerContainer):
        log.info(
            "ViewTreeOptionsMenu : Création du menu des Options de vue Arborescente."
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        self.appendUICommands(
            uicommand.ViewExpandAll(viewer=viewerContainer),
            uicommand.ViewCollapseAll(viewer=viewerContainer),
        )


class ModeMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self.__window.viewer.hasModes() and bool(
            self.__window.viewer.getModeUICommands()
        )

    def getUICommands(self):
        return self.__window.viewer.getModeUICommands()


class FilterMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self.__window.viewer.isFilterable() and bool(
            self.__window.viewer.getFilterUICommands()
        )

    def getUICommands(self):
        return self.__window.viewer.getFilterUICommands()


class ColumnMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self.__window.viewer.hasHideableColumns()

    def getUICommands(self):
        return self.__window.viewer.getColumnUICommands()


class SortMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self.__window.viewer.isSortable()

    def getUICommands(self):
        return self.__window.viewer.getSortUICommands()


class RoundingMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self.__window.viewer.supportsRounding()

    def getUICommands(self):
        return self.__window.viewer.getRoundingUICommands()


class ToolBarMenu(Menu):
    """
    Création du menu de ToolBar.
    """

    # def __init__(self, parent, settings):
    def __init__(self, parent, parent_window, settings):
        log.info("Création du menu de la Barre d'Outils.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        toolbarCommands = []  # ?
        for value, menuText, helpText in [
            (None, _("&Hide"), _("Hide the toolbar")),
            (
                (16, 16),
                _("&Small images"),
                _("Small images (16x16) on the toolbar"),
            ),
            (
                (22, 22),
                _("&Medium-sized images"),
                _("Medium-sized images (22x22) on the toolbar"),
            ),
            (
                (32, 32),
                _("&Large images"),
                _("Large images (32x32) on the toolbar"),
            ),
        ]:
            toolbarCommands.append(
                # uicommand.UIRadioCommand(
                settings_uicommandtk.UIRadioCommand(
                    settings=settings,
                    setting="toolbar",
                    value=value,
                    menuText=menuText,
                    helpText=helpText,
                )
            )
        # pylint: disable=W0142
        self.appendUICommands(*toolbarCommands)


class NewMenu(Menu):
    """
    Création du menu Nouveau dans la barre de Menu.
    """

    # def __init__(self, parent, settings, taskFile, viewerContainer):
    def __init__(
        self, parent, parent_window, settings, taskFile, viewerContainer
    ):
        log.info("Création du menu New/Nouveau.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        tasks = taskFile.tasks()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings),
            uicommand.NewTaskWithSelectedTasksAsPrerequisites(
                taskList=tasks, viewer=viewerContainer, settings=settings
            ),
            uicommand.NewTaskWithSelectedTasksAsDependencies(
                taskList=tasks, viewer=viewerContainer, settings=settings
            ),
        )
        # log.debug("NewMenu : Ajout du menu : Nouvelle tâche depuis les archives")
        self.appendMenu(
            _("New task from &template"),
            # TaskTemplateMenu(parent, taskList=tasks, settings=settings),
            TaskTemplateMenu(
                parent, parent_window, taskList=tasks, settings=settings
            ),
            # "newtmpl"
        )
        self.appendUICommands(
            None,
            uicommand.EffortNew(
                viewer=viewerContainer,
                effortList=taskFile.efforts(),
                taskList=tasks,
                settings=settings,
            ),
            uicommand.CategoryNew(
                categories=taskFile.categories(), settings=settings
            ),
            uicommand.NoteNew(notes=taskFile.notes(), settings=settings),
            None,
            uicommand.NewSubItem(viewer=viewerContainer),
        )
        log.debug("NewMenu : devrait être ajouté !")


class ActionMenu(Menu):
    # def __init__(self, parent, settings, taskFile, viewerContainer):
    def __init__(
        self, parent, parent_window, settings, taskFile, viewerContainer
    ):
        log.info("Création du menu Action.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        categories = taskFile.categories()

        self._check_var = tk.BooleanVar()
        # Generic actions, applicable to all/most domain objects:
        # log.debug("📌 [DEBUG] ActionMenu : Ajout d’un attachement :")
        self.appendUICommands(
            uicommand.AddAttachment(viewer=viewerContainer, settings=settings),
            uicommand.OpenAllAttachments(
                viewer=viewerContainer, settings=settings
            ),
            None,
            uicommand.AddNote(viewer=viewerContainer, settings=settings),
            uicommand.OpenAllNotes(viewer=viewerContainer, settings=settings),
            None,
            uicommand.Mail(viewer=viewerContainer),
            None,
        )
        # log.debug("ActionMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(
            _("&Toggle category"),
            ToggleCategoryMenu(
                # parent, categories=categories, viewer=viewerContainer
                # parent, parent_window, categories=categories, viewer=viewerContainer
                parent=parent,
                parent_window=parent_window,
                categories=categories,
                viewer=viewerContainer,
            ),
            # "folder_blue_arrow_icon"
        )
        # Start of task specific actions:
        self.appendUICommands(
            None,
            uicommand.TaskMarkInactive(
                settings=settings, viewer=viewerContainer
            ),
            uicommand.TaskMarkActive(
                settings=settings, viewer=viewerContainer
            ),
            uicommand.TaskMarkCompleted(
                settings=settings, viewer=viewerContainer
            ),
            None,
        )
        # log.debug("ActionMenu : Ajout du menu : Changement de priorité/tâche")
        self.appendMenu(
            _("Change task &priority"),
            # TaskPriorityMenu(parent, tasks, viewerContainer),
            TaskPriorityMenu(parent, parent_window, tasks, viewerContainer),
            # "incpriority"
        )
        self.appendUICommands(
            None,
            uicommand.EffortStart(viewer=viewerContainer, taskList=tasks),
            uicommand.EffortStop(
                viewer=viewerContainer, effortList=efforts, taskList=tasks
            ),
            uicommand.EditTrackedTasks(taskList=tasks, settings=settings),
        )

    def Check(self, checked):
        """Méthode de compatibilité wxPython pour cocher/décocher le menu"""
        if hasattr(self, "_check_var"):
            self._check_var.set(checked)


class TaskPriorityMenu(Menu):
    # def __init__(self, parent, taskList, viewerContainer):
    def __init__(self, parent, parent_window, taskList, viewerContainer):
        log.info("Création du menu Priorité de Tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        kwargs = dict(taskList=taskList, viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.TaskIncPriority(**kwargs),
            uicommand.TaskDecPriority(**kwargs),
            uicommand.TaskMaxPriority(**kwargs),
            uicommand.TaskMinPriority(**kwargs),
        )


class HelpMenu(Menu):
    # def __init__(self, parent, settings, iocontroller):
    def __init__(self, parent, parent_window, settings, iocontroller):
        log.info("Création du menu Help/Aide.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        self.appendUICommands(
            uicommand.Help(),
            uicommand.FAQ(),
            uicommand.Tips(settings=settings),
            uicommand.Anonymize(iocontroller=iocontroller),
            None,
            uicommand.RequestSupport(),
            uicommand.ReportBug(),
            uicommand.RequestFeature(),
            None,
            uicommand.HelpTranslate(),
            uicommand.Donate(),
            None,
            uicommand.HelpAbout(),
            uicommand.CheckForUpdate(settings=settings),
            uicommand.HelpLicense(),
        )
        log.debug("HelpMenu : devrait être ajouté !")


class TaskBarMenu(Menu):
    """
    Menu de la barre de tâche pour TaskCoach.
    """

    #     Problème : Le problème est effectivement que TaskBarIcon
    #     n'est pas une sous-classe de wx.Window, et les menus wxPython
    #     (comme ceux gérés par UICommandContainerMixin) sont
    #     conçus pour être associés à des wx.Window.
    def __init__(self, taskBarIcon, settings, taskFile, viewer):
        log.info("TaskBarMenu : Création du menu de Barre de tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(taskBarIcon)
        # super().__init__()
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings)
        )
        # log.debug("TaskBarMenu : Ajout du menu : Nouvelle tâche depuis les archives.")
        self.appendMenu(
            _("New task from &template"),
            TaskTemplateMenu(taskBarIcon, taskList=tasks, settings=settings),
            # "newtmpl"
        )
        self.appendUICommands(None)  # Separator
        self.appendUICommands(
            uicommand.EffortNew(
                effortList=efforts, taskList=tasks, settings=settings
            ),
            uicommand.CategoryNew(
                categories=taskFile.categories(), settings=settings
            ),
            uicommand.NoteNew(notes=taskFile.notes(), settings=settings),
        )
        self.appendUICommands(None)  # Separator
        label = _("&Start tracking effort")
        # log.debug("taskBArMenu : Ajout du menu : Départ d'effort pour la tâche.")
        # self.appendMenu(
        #     label,
        #     StartEffortForTaskMenu(
        #         taskBarIcon, taskcoachlib.domain.base.filter.DeletedFilter(tasks), self, label
        #     ),
        #     "clock_icon"
        # )
        self.appendUICommands(
            uicommand.EffortStop(
                viewer=viewer, effortList=efforts, taskList=tasks
            )
        )
        self.appendUICommands(
            None, uicommand.MainWindowRestore(), uicommand.FileQuit()
        )
        log.debug("TaskBarMenu : devrait être ajouté !")


class ToggleCategoryMenu(DynamicMenu):
    def __init__(
        self, parent, parent_window, categories, viewer
    ):  # pylint: disable=W0621
        log.info("Création du menu Toggle Catégorie.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.categories = categories
        self.viewer = viewer
        self.__window = parent_window
        # super().__init__(parent)
        super().__init__(parent, parent_window)
        log.info("Menu Toggle Catégorie initialisé.")

    def registerForMenuUpdate(self):
        for eventType in (
            self.categories.addItemEventType(),
            self.categories.removeItemEventType(),
        ):
            patterns.Publisher().registerObserver(
                self.onUpdateMenu,
                eventType=eventType,
                eventSource=self.categories,
            )
        patterns.Publisher().registerObserver(
            self.onUpdateMenu,
            eventType=category.Category.subjectChangedEventType(),
        )

    def updateMenuItems(self):
        self.clearMenu()
        self.addMenuItemsForCategories(self.categories.rootItems(), self)

    def addMenuItemsForCategories(self, categories, menuToAdd):
        """
        Ajoute des éléments de Menu, Trie et construit le menu pour les catégories

        Args :
            categories :
            menu :

        Returns :

        """
        # pylint: disable=W0621
        # Trie et construit le menu pour les catégories
        # log.debug("ToggleCategoryMenu.addMenuItemsForCategories : Ajout de %d catégories au menu.", len(categories))
        categories = categories[:]
        categories.sort(key=lambda category: category.subject().lower())
        for category in categories:
            uiCommand = uicommand.ToggleCategory(
                category=category, viewer=self.viewer
            )
            log.debug(
                f"ToggleCategoryMenu.addMenuItemsForCategories : Ajout du sous-menu : {uiCommand} dans {menuToAdd} fenêtre {self.__window}"
            )
            uiCommand.addToMenu(menuToAdd, self.__window)
        categoriesWithChildren = [
            category for category in categories if category.children()
        ]
        if categoriesWithChildren:
            menuToAdd.AppendSeparator()
            for category in categoriesWithChildren:
                # log.debug("ToggleCategoryMenu.addMenuItemsForCategories : est-ce là l'erreur!")
                subMenu = Menu(self.__window)
                # log.debug(f"subMenu={subMenu}")
                # self.addMenuItemsForCategories(category.children(), subMenu)
                self.addMenuItemsForCategories(
                    category.get_tree_children(), subMenu
                )
                # log.debug(f"ToggleCategoryMenu.addMenuItemsForCategories : Ajout du sous-menu : {self.subMenuLabel(category)}{subMenu} dans {menuToAdd}")
                menuToAdd.AppendSubMenu(subMenu, self.subMenuLabel(category))

    @staticmethod
    def subMenuLabel(category):  # pylint: disable=W0621
        # return _("%s (subcategories)") % category.subject()
        return _(f"{category.subject()} (subcategories)")

    def enabled(self):
        return bool(self.categories)


class StartEffortForTaskMenu(DynamicMenu):
    def __init__(
        self, taskBarIcon, tasks, parentMenu=None, labelInParentMenu=""
    ):
        log.info("Création du menu Début d'effort de tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.tasks = tasks
        super().__init__(taskBarIcon, parentMenu, labelInParentMenu)
        log.info(
            "StartEffortForTaskMenu : Menu début d'effort de tâche créé !"
        )

    def registerForMenuUpdate(self):
        for eventType in (
            self.tasks.addItemEventType(),
            self.tasks.removeItemEventType(),
        ):
            # patterns.Publisher().registerObserver(self.onUpdateMenu_Deprecated,
            patterns.Publisher().registerObserver(
                self.onUpdateMenu, eventType=eventType, eventSource=self.tasks
            )
        # for eventType in (task.Task.subjectChangedEventType(),
        #                   task.Task.trackingChangedEventType(),
        #                   task.Task.plannedStartDateTimeChangedEventType(),
        #                   task.Task.dueDateTimeChangedEventType(),
        #                   task.Task.actualStartDateTimeChangedEventType(),
        #                   task.Task.completionDateTimeChangedEventType()):
        #     if eventType.startswith("pubsub"):
        #         pub.subscribe(self.onUpdateMenu, eventType)
        #     else:
        #         patterns.Publisher().registerObserver(self.onUpdateMenu_Deprecated,
        #                                               eventType)

    def updateMenuItems(self):
        self.clearMenu()
        trackableRootTasks = self._trackableRootTasks()
        trackableRootTasks.sort(key=lambda task: task.subject())
        for trackableRootTask in trackableRootTasks:
            self.addMenuItemForTask(trackableRootTask, self)

    def addMenuItemForTask(self, task, menuItem):  # pylint: disable=W0621
        uiCommand = uicommand.EffortStartForTask(
            task=task, taskList=self.tasks
        )
        log.debug(
            f"StartEffortForTaskMenu.addMenuItemForTask Ajoute le menu {uiCommand} à {menuItem} fenêtre {self.__window}"
        )
        uiCommand.addToMenu(menuItem, self.__window)
        trackableChildren = [
            child
            for child in task.children()
            if child in self.tasks and not child.completed()
        ]
        if trackableChildren:
            trackableChildren.sort(key=lambda child: child.subject())
            subMenu = Menu(self.__window)
            for child in trackableChildren:
                self.addMenuItemForTask(child, subMenu)
            log.debug(
                f"StartEffortForTaskMenu.addMenuItemForTask : Ajout du sous-menu : {task.subject()} (subtasks){subMenu} dans {menuItem}"
            )
            menuItem.AppendSubMenu(
                subMenu, _("%s (subtasks)") % task.subject()
            )

    def enabled(self):
        return bool(self._trackableRootTasks())

    def _trackableRootTasks(self):
        return [
            rootTask
            for rootTask in self.tasks.rootItems()
            if not rootTask.completed()
        ]


class TaskPopupMenu(Menu):
    """
    Menu contextuel pour les tâches dans Task Coach.

    Ce menu contextuel est utilisé pour afficher des options d'action sur les tâches telles que couper, copier, coller, ajouter une note, etc.

    Méthodes :
        __init__ (self, mainwindow, settings, tasks, efforts, categories, taskViewer) :
            Initialise le menu contextuel des tâches.
    """

    def __init__(
        self,
        parent,
        settings,
        tasks,
        efforts,
        categories,
        taskViewer,
        parent_window=None,
        **kwargs,
    ):
        log.info("TaskPopupMenu : Création du menu Popup de Tâche.")
        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window, **kwargs)
        # log.info("TaskPopuMenu : Initialisation du menu contextuel : %s", self.__class__.__name__)
        # log.debug(f"mainwindow={mainwindow}, settings={settings},"
        #           f"tasks={tasks}, efforts={efforts},"
        #           f"categories={categories}, taskViewer={taskViewer}")
        # Les commandes de menu sont ici :
        # log.debug("TaskPopupMenu : Ajoute une liste d'UICommands.")

        self.appendUICommands(
            uicommand.EditCut(viewer=taskViewer),
            uicommand.EditCopy(viewer=taskViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=taskViewer),
            None,
            uicommand.Edit(viewer=taskViewer),
            uicommand.Delete(viewer=taskViewer),
            None,
            uicommand.AddAttachment(viewer=taskViewer, settings=settings),
            uicommand.OpenAllAttachments(viewer=taskViewer, settings=settings),
            None,
            uicommand.AddNote(viewer=taskViewer, settings=settings),
            uicommand.OpenAllNotes(viewer=taskViewer, settings=settings),
            None,
            uicommand.Mail(viewer=taskViewer),
            None,
        )
        # log.debug("TaskPopupMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(
            _("&Toggle category"),
            ToggleCategoryMenu(
                parent=parent,
                parent_window=parent_window,
                categories=categories,
                viewer=taskViewer,
            ),
            # "folder_blue_arrow_icon"
        )
        # Les commandes de menu sont ici
        # log.debug("TaskPopupMenu - Ajout du menu Toggle Categorie : Ajout des commandes :")
        self.appendUICommands(
            None,
            uicommand.TaskMarkInactive(settings=settings, viewer=taskViewer),
            uicommand.TaskMarkActive(settings=settings, viewer=taskViewer),
            uicommand.TaskMarkCompleted(settings=settings, viewer=taskViewer),
            None,
        )
        # log.debug("TaskPopupMenu : Ajout du menu : Priorité")
        self.appendMenu(
            _("&Priority"),
            TaskPriorityMenu(parent, parent_window, tasks, taskViewer),
            # "incpriority"
        )
        # Les commandes de menu sont ici :
        self.appendUICommands(
            None,
            uicommand.EffortNew(
                viewer=taskViewer,
                effortList=efforts,
                taskList=tasks,
                settings=settings,
            ),
            uicommand.EffortStart(viewer=taskViewer, taskList=tasks),
            uicommand.EffortStop(
                viewer=taskViewer, effortList=efforts, taskList=tasks
            ),
            None,
            uicommand.NewSubItem(viewer=taskViewer),
        )
        log.info("TaskPopupMenu : Terminée - Menu Popup de Tâche créé.")


# Recontextualisation du problème
# L'erreur AttributeError: 'EffortPopupMenu' object has no attribute 'Check'
# se produit lors du chargement du fichier XML dans taskfile.py.
# Cela suggère que le problème n'est pas directement lié à l'affichage du menu contextuel,
# mais plutôt à la manière dont l'état de certains éléments du menu contextuel
# est restauré lors du chargement des données.
# L'appel à menuItem.Check(paused) indique qu'on essaie de restaurer
# l'état coché/décoché d'un élément de menu,
# mais que la méthode Check n'existe pas dans l'implémentation Tkinter.
# Analyse approfondie de menutk.py
# En examinant menutk.py, on trouve la définition de EffortPopupMenu.
# Cependant, cette classe n'implémente aucune logique spécifique
# pour gérer l'état coché/décoché des éléments de menu.
# De plus, elle n'hérite pas de UICheckCommand,
# qui est la classe utilisée pour gérer l'état des éléments de menu cochés dans Task Coach.
# Analyse approfondie de uicommandtk.py
# Dans uicommandtk.py, on trouve la classe EffortStart 4 et EffortStop 4,
# qui sont probablement les commandes associées aux actions de démarrage et d'arrêt des efforts.
# Il est crucial de comprendre comment ces commandes sont liées au menu contextuel
# et comment leur état est géré.
# Identification de la source du problème
# Le problème se situe probablement dans la manière dont EffortPopupMenu est construit
# et dans la façon dont les commandes EffortStart et EffortStop sont ajoutées à ce menu.
# Il est possible que le code essaie d'accéder à une méthode Check
# qui n'existe pas sur les éléments de menu Tkinter.
# Solutions possibles
# Voici une approche plus détaillée pour résoudre le problème :
#
# Vérifier la construction de EffortPopupMenu :
#
# Assurez-vous que EffortPopupMenu est correctement instancié et que les commandes EffortStart et EffortStop sont correctement ajoutées au menu.
# Vérifiez si des arguments incorrects sont passés aux éléments de menu lors de leur création.
#
# Adapter la gestion de l'état coché/décoché :
#
# Comme mentionné précédemment, Tkinter n'a pas de méthode Check intégrée pour les éléments de menu.
# Vous devez utiliser des variables de contrôle (IntVar ou BooleanVar) associées aux éléments de menu pour gérer leur état coché/décoché.
# Modifiez le code pour utiliser ces variables de contrôle et mettre à jour l'état des éléments de menu en conséquence.
#
# Vérifier la logique de sérialisation/désérialisation :
#
# Le traceback indique que l'erreur se produit lors du chargement du fichier XML. Vérifiez comment l'état des éléments de menu est sérialisé dans le fichier XML et comment il est désérialisé lors du chargement.
# Assurez-vous que la logique de sérialisation/désérialisation est compatible avec l'approche Tkinter pour gérer l'état coché/décoché des éléments de menu.
#
# Utiliser les classes UICommand appropriées :
#
# Assurez-vous que les commandes EffortStart et EffortStop héritent de la classe UICheckCommand ou d'une classe similaire qui fournit la logique nécessaire pour gérer l'état coché/décoché des éléments de menu.
# Si ce n'est pas le cas, vous devrez peut-être adapter ces classes pour qu'elles fonctionnent correctement avec Tkinter.
#
# Mise en œuvre
# Voici une façon possible d'implémenter la gestion de l'état coché/décoché en utilisant des variables de contrôle Tkinter :
class EffortPopupMenu(Menu):
    def __init__(self, parent, tasks, efforts, settings, effortViewer):
        # def __init__(self, parent, parent_window, tasks, efforts, settings, effortViewer):
        log.info("Création du menu Popup Effort.")
        # log.debug("Affichage du menu contextuel pour les efforts.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, tearoff=0)
        # super().__init__(parent, parent_mainwindow=parent_window)
        self.tasks = tasks
        self.efforts = efforts
        self.settings = settings
        self.effortViewer = effortViewer
        self.effort_start_var = (
            tk.BooleanVar()
        )  # Variable de contrôle pour EffortStart
        self.effort_stop_var = (
            tk.BooleanVar()
        )  # Variable de contrôle pour EffortStop
        self.appendUICommands(
            uicommand.EditCut(viewer=effortViewer),
            uicommand.EditCopy(viewer=effortViewer),
            uicommand.EditPaste(),
            None,
            uicommand.Edit(viewer=effortViewer),
            uicommand.Delete(viewer=effortViewer),
            None,
            uicommand.EffortNew(
                viewer=effortViewer,
                effortList=efforts,
                taskList=tasks,
                settings=settings,
            ),
            uicommand.EffortStartForEffort(
                viewer=effortViewer, taskList=tasks
            ),
            uicommand.EffortStop(
                viewer=effortViewer, effortList=efforts, taskList=tasks
            ),
        )
        self.add_commands()
        log.info("EffortPopupMenu : Menu Popup Effort créé !")

    def add_commands(self):
        # Ajouter les commandes EffortStart et EffortStop
        self.add_checkbutton(
            label="Démarrer l'effort",
            variable=self.effort_start_var,
            command=self.on_effort_start,
        )
        self.add_checkbutton(
            label="Arrêter l'effort",
            variable=self.effort_stop_var,
            command=self.on_effort_stop,
        )

    def on_effort_start(self):
        # Logique pour démarrer l'effort
        self.effort_start_var.set(True)
        self.effort_stop_var.set(False)

    def on_effort_stop(self):
        # Logique pour arrêter l'effort
        self.effort_start_var.set(False)
        self.effort_stop_var.set(True)


# Dans cet exemple :
#
# effort_start_var et effort_stop_var sont des variables de contrôle de type BooleanVar qui stockent l'état coché/décoché des éléments de menu.
# add_checkbutton crée des éléments de menu avec des cases à cocher associées aux variables de contrôle.
# on_effort_start et on_effort_stop sont appelées lorsque les éléments de menu sont cliqués. Elles mettent à jour l'état des variables de contrôle et effectuent les actions appropriées.
#
# Remarques importantes
#
# Vous devrez adapter cet exemple à votre code spécifique et à la logique de vos commandes EffortStart et EffortStop.
# Assurez-vous que l'état des variables de contrôle est correctement restauré lors du chargement du fichier XML.
# Testez minutieusement votre code pour vous assurer qu'il fonctionne correctement dans toutes les situations.


class CategoryPopupMenu(Menu):
    """
    Le menu CategoryPopupMenu s’appuie fortement sur UICommandContainerMixin,
    notamment avec 'self.appendUICommands([...])'.
    """

    # def __init__(self, parent, settings, taskFile, categoryViewer,
    def __init__(
        self,
        parent,
        parent_window,
        settings,
        taskFile,
        categoryViewer,
        localOnly=False,
    ):
        log.info("Création du menu Popup Catégorie.")
        # log.debug("Affichage du menu contextuel pour les catégories.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        categories = categoryViewer.presentation()
        tasks = taskFile.tasks()
        notes = taskFile.notes()
        self.appendUICommands(
            uicommand.EditCut(viewer=categoryViewer),
            uicommand.EditCopy(viewer=categoryViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=categoryViewer),
            None,
            uicommand.Edit(viewer=categoryViewer),
            uicommand.Delete(viewer=categoryViewer),
            None,
            uicommand.AddAttachment(viewer=categoryViewer, settings=settings),
            uicommand.OpenAllAttachments(
                viewer=categoryViewer, settings=settings
            ),
            None,
            uicommand.AddNote(viewer=categoryViewer, settings=settings),
            uicommand.OpenAllNotes(viewer=categoryViewer, settings=settings),
            None,
            uicommand.Mail(viewer=categoryViewer),
        )
        if not localOnly:
            self.appendUICommands(
                None,
                uicommand.NewTaskWithSelectedCategories(
                    taskList=tasks,
                    settings=settings,
                    categories=categories,
                    viewer=categoryViewer,
                ),
                uicommand.NewNoteWithSelectedCategories(
                    notes=notes,
                    settings=settings,
                    categories=categories,
                    viewer=categoryViewer,
                ),
            )
        self.appendUICommands(
            None, uicommand.NewSubItem(viewer=categoryViewer)
        )
        log.info("CategoryPopupMenu : Menu Popup Catégorie créé !")


class NotePopupMenu(Menu):
    # def __init__(self, parent, settings, categories, noteViewer):
    def __init__(
        self, parent, parent_window, settings, categories, noteViewer
    ):
        log.info("Création du menu Popup Note.")
        # log.debug("Affichage du menu contextuel pour les notes.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        self.appendUICommands(
            uicommand.EditCut(viewer=noteViewer),
            uicommand.EditCopy(viewer=noteViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=noteViewer),
            None,
            uicommand.Edit(viewer=noteViewer),
            uicommand.Delete(viewer=noteViewer),
            None,
            uicommand.AddAttachment(viewer=noteViewer, settings=settings),
            uicommand.OpenAllAttachments(viewer=noteViewer, settings=settings),
            None,
            uicommand.Mail(viewer=noteViewer),
            None,
        )
        # log.debug("NotePopupMenu : Ajout du menu : Toggle Categorie")
        self.appendMenu(
            _("&Toggle category"),
            ToggleCategoryMenu(
                parent, parent_window, categories=categories, viewer=noteViewer
            ),
            # "folder_blue_arrow_icon"
        )
        self.appendUICommands(None, uicommand.NewSubItem(viewer=noteViewer))
        log.debug("NotePopupMenu : Menu créé !")


class ColumnPopupMenuMixin(object):
    """Mixin class for column header popup menu's. These menu's get the
    column index property set by the control popping up the menu to
    indicate which column the user clicked. See
    widgets._CtrlWithColumnPopupMenuMixin."""

    def __setColumn(self, columnIndex):
        self.__columnIndex = columnIndex  # pylint: disable=W0201

    def __getColumn(self):
        return self.__columnIndex

    columnIndex = property(__getColumn, __setColumn)

    def getUICommands(self):
        """Get the UI commands for the column popup menu.

        Obtenez les commandes de l'interface utilisateur pour le menu contextuel de la colonne.
        """
        # # if not self.__window:  # Prevent PyDeadObject exception when running tests
        # #     return []
        # # self.columnIndex = self.__window.getPopupColumnIndex()
        # # self.columnIndex = self.__getColumn()
        # return [
        #     uicommand.HideCurrentColumn(viewer=self.__window),
        #     # uicommand.HideColumn(viewer=self.__window,
        #     #                      columnIndex=self.columnIndex),
        #     None,
        # ] + self.__window.getColumnUICommands()
        log.error(
            f"ColumnPopupMenuMixin.getUICommands : La méthode doit être implémentée dans la classe dérivée."
        )


# TODO : Vérifier l'ordre d'héritage, car il peut être crucial.
# Voir la discussion ci-dessous.
# Problème de self.__window dans  ColumnPopupMenuMixin.getUICommands
# class ColumnPopupMenu(ColumnPopupMenuMixin, Menu):
class ColumnPopupMenu(
    Menu, ColumnPopupMenuMixin
):  # Inversion de l'ordre d'héritage
    # L'ordre d'héritage est crucial.
    # Il faut que Menu (qui est tk.Menu et UICommandContainerMixin) soit en premier,
    # et ColumnPopupMenuMixin en second.
    # Cela garantit que ColumnPopupMenu est bien un menu Tkinter
    # et qu'il hérite des fonctionnalités de gestion des commandes UI de Menu.
    # De plus, cela permet d'initialiser correctement les mixins.
    """Column header popup menu.
    Menu contextuel pour les colonnes.
    """

    def __init__(self, parent, parent_mainwindow):
        # def __init__(self, parent, parent_window, viewer):
        log.info(
            f"ColumnPopupMenu : Création du menu Popup Colonne dans la fenêtre parente {parent}."
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(window)
        # super().__init__(window, parent_window)
        # self.__window = window  # Needed for getUICommands
        Menu.__init__(
            self, parent, parent_mainwindow, tearoff=0
        )  # Initialise tk.Menu et UICommandContainerMixin
        self.__window = parent  # Needed for getUICommands. Stocke la référence à la fenêtre.
        ColumnPopupMenuMixin.__init__(self)  # Initialise ColumnPopupMenuMixin
        # Cette ligne stocke la référence à la fenêtre dans un attribut privé __window.
        # C'est important car ColumnPopupMenuMixin a besoin d'accéder à cette fenêtre
        # pour obtenir des informations sur la colonne et les commandes UI.
        # Notez que dans menutk.py, la méthode getUICommands fait référence à self.__window.
        log.debug("ColumnPopupMenu : Appel de CallAfter.")
        # Cette ligne planifie l'appel à self.appendUICommands
        # après que la fenêtre a été affichée.
        # Cela permet d'éviter les erreurs liées à la création des commandes UI
        # avant que la fenêtre ne soit prête.
        # L'appel à self.getUICommands() permet de récupérer les commandes UI
        # à ajouter au menu contextuel.
        # window.after(0, self.appendUICommands, *self.getUICommands())  # TODO
        log.debug(
            "ColumnPopupMenu : CallAfter passé avec succès. Menu Popup Colonne terminé !"
        )

    def appendUICommands(self, *args, **kwargs):
        # Prepare for PyDeadObjectError since we're called from wx.CallAfter
        log.debug(
            "ColumnPopupMenu.appendUICommands essaie d'ajouter une commande via la méthode super."
        )
        try:
            super().appendUICommands(*args, **kwargs)
            # print(f"tclib.gui.menu.AppendUICommands: {uiCommand}, id = {uiCommand.id}") # Ajout de journalisation
        # except wx.PyDeadObjectError:
        except RuntimeError as e:
            log.error(
                f"ColumnPopupMenu.appendUICommands : La méthode super plante à cause de {e}.",
                exc_info=True,
            )
        log.debug("ColumnPopupMenu.appendUICommands : Commande ajoutée !")


class EffortViewerColumnPopupMenu(
    ColumnPopupMenuMixin, DynamicMenuThatGetsUICommandsFromViewer
):
    """Column header popup menu."""

    def registerForMenuUpdate(self):
        pub.subscribe(self.onChangeAggregation, "effortviewer.aggregation")

    def onChangeAggregation(self):
        self.onUpdateMenu(None, None)


class AttachmentPopupMenu(Menu):
    # def __init__(self, parent, settings, attachments, attachmentViewer):
    def __init__(
        self, parent, parent_window, settings, attachments, attachmentViewer
    ):
        log.info("Création du menu Popup Attachment.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # super().__init__(parent)
        super().__init__(parent, parent_mainwindow=parent_window)
        self.appendUICommands(
            uicommand.EditCut(viewer=attachmentViewer),
            uicommand.EditCopy(viewer=attachmentViewer),
            uicommand.EditPaste(),
            None,
            uicommand.Edit(viewer=attachmentViewer),
            uicommand.Delete(viewer=attachmentViewer),
            None,
            uicommand.AddNote(viewer=attachmentViewer, settings=settings),
            uicommand.OpenAllNotes(viewer=attachmentViewer, settings=settings),
            None,
            uicommand.AttachmentOpen(
                viewer=attachmentViewer,
                attachments=attachments,
                settings=settings,
            ),
        )
