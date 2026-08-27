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

Module `menu.py` - Gestion des menus dans Task Coach.

Ce module contient les classes pour gérer les différents types de menus utilisés dans Task Coach,
tels que les menus contextuels, les menus dynamiques, et les menus de la barre d'outils.
Il permet de configurer et de manipuler les éléments de menu, et d'ajouter des commandes UI.

Classes :
    - Menu : Classe de base pour les menus.
    - DynamicMenu : Un menu qui se met à jour automatiquement.
    - MainMenu : Le menu principal de l'application Task Coach.
    - FileMenu, ExportMenu, ImportMenu, etc. : Différentes classes pour gérer des menus spécifiques comme le menu Fichier, Exporter, Importer, etc.

    - CategoryPopupMenu : Le menu s’appuie fortement sur UICommandContainerMixin.
"""

from wx.py.introspect import getAttributeNames

# from builtins import object
from taskcoachlib import operating_system
import logging
import os
import wx

# try:
from pubsub import pub

# except ImportError:
# try:
#    from ..thirdparty.pubsub import pub
# except ImportError:
#    from wx.lib.pubsub import pub
# import taskcoachlib  # but cannot find reference gui in __init__.py
from taskcoachlib import patterns, persistence, help  # pylint: disable=W0622
from taskcoachlib.domain import task, base, category
from taskcoachlib.i18n import _
from taskcoachlib.gui import artprovider
from taskcoachlib.gui.newid import IdProvider

# from taskcoachlib.gui import uicommand
from taskcoachlib.gui import viewer
from taskcoachlib.gui.uicommand import (
    base_uicommand,
)  # ? à ajouter Peut-être ! ou à retirer ?
from taskcoachlib.gui.uicommand import uicommand
from taskcoachlib.gui.uicommand import uicommandcontainer

# from .settings_uicommand import UIRadioCommand, UICheckCommand
from taskcoachlib.gui.uicommand import settings_uicommand
import taskcoachlib.gui.viewer

log = logging.getLogger(__name__)


class Menu(
    uicommandcontainer.UICommandContainerMixin, wx.Menu
):  # Crée des problème d'initialisation avec self._window !
    # class Menu(wx.Menu, uicommandcontainer.UICommandContainerMixin):  # Fonctionne mieux !
    """
    Classe de base pour les menus dans Task Coach (comme Fichier, Editer,
    Affichage, Nouveau, Actions et Aide)

    Cette classe gère les éléments de menu, les accélérateurs,
    et les commandes UI associées.

    Héritage :
        La classe Menu hérite de uicommandcontainer.UICommandContainerMixin,
        ce qui signifie qu'elle possède la méthode appendUICommands.
        Elle hérite également de wx.Menu, ce qui en fait un menu graphique de wxPython.

    Attributs :
        _window : Référence à la fenêtre principale.
        _accels : Liste des accélérateurs du menu.
        _observers : Liste des observateurs liés au menu.

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

    # Veiller à la Libération des identifiants lors de la destruction des éléments de menu
    def __init__(self, window):
        log.info(
            "Menu : Création du menu de base. Initialisation du menu contextuel : %s",
            self.__class__.__name__,
        )
        # log.debug(f"Menu : Initialisation de Menu. (self={self} window={window})")
        # Prend une référence à la fenêtre principale (window).
        # Cette fenêtre est utilisée lors de l'ajout de commandes UI
        # pour lier les événements.
        # Si cette window n'est pas correctement initialisée
        # ou n'est pas la fenêtre qui doit gérer les événements du menu,
        # cela pourrait être une source de problèmes.
        super().__init__()  # Initialisez la classe de base wx.Menu
        self._window = window  # Stockez la référence à la fenêtre principale.
        log.debug(f"Menu : self._window={self._window}")
        # Très important : Vérifiez que window est bien
        # une instance valide de wx.Window (ou une de ses sous-classes).
        # log.debug(f"Menu : Type réel de window : {type(window)}")  # Inutile car déjà donné dans {self._window} !
        if window:
            # log.info("Menu : window est une instance valide et non None.")
            if isinstance(window, wx.Window):
                log.info("Menu : window est une instance valide de wx.Window.")
            else:
                log.error(
                    "Menu : window n'est PAS une instance valide de wx.Window."
                )
        else:
            log.error("Menu : window est None.")
        # if not self._window or self._window is None:
        #     self._window = wx.GetActiveWindow()
        # Il est crucial que cette self._window reste valide pendant
        # toute la durée de vie du menu.
        # Si self._window est détruite avant le menu,self._window is None
        # cela pourrait causer des problèmes d'ID.
        self._accels = list()  # Liste des accélérateurs du menu.
        self._observers = list()  # Liste des menus/observateurs liés au menu.
        log.info(
            f"Menu : Fin d'Initialisation de Menu ! (self est {self.__class__.__name__}, window est {window.__class__.__name__})"
        )

    def __len__(self):
        return (
            self.GetMenuItemCount()
        )  # wx. Returns the number of items in the menu.

    def DestroyItem(self, menuItem):
        """
        Supprime un élément de menu.

        Args :
            menuItem (wx.MenuItem) : L'élément de menu à supprimer.
        """
        # log.info(
        #     f"Menu.DestroyItem supprime {menuItem} de {self.__class__.__name__}"
        # )
        # Supprime un élément de menu et tente de délier les événements associés
        # (wx.EVT_MENU, wx.EVT_UPDATE_UI) de self._window.
        # Si self._window n'est pas la fenêtre à laquelle
        # les événements ont été liés à l'origine,
        # cette déliaison pourrait ne pas avoir l'effet escompté.

        # Un menuItem représente un élément dans un menu.
        # print(
        #     f"tclib.gui.menu.py Menu.DestroyItem essaie de retirer: menuItem = {menuItem} de self: {self} avec id: {id}")
        menuItem_id = menuItem.GetId()
        if menuItem.GetSubMenu():
            menuItem.GetSubMenu().clearMenu()
        # self._window.Unbind(wx.EVT_MENU, id=menuItem.get_id())
        self._window.Unbind(wx.EVT_MENU, id=menuItem.GetId())
        # get_id Return an identifier for the table.
        # self._window.Unbind(wx.EVT_UPDATE_UI, id=menuItem.get_id())
        self._window.Unbind(wx.EVT_UPDATE_UI, id=menuItem.GetId())
        # Ajout de journalisation:
        # print(f" destruction de: menuItem = {menuItem} de self: {self} avec id: {id}")
        super().DestroyItem(menuItem)
        # nouvelle ligne conseillée par chatGPT
        # IdProvider.put(menuItem.GetId())  # Libérer l'identifiant. Incorrect call arguments option. Parameter 'id_' unfilled
        IdProvider.put(
            menuItem_id
        )  # Libérer l'identifiant. Incorrect call arguments option. Parameter 'id_' unfilled
        # log.info(
        #     f"Menu.DestroyItem : {menuItem} supprimé de {self.__class__.__name__} !"
        # )

    def clearMenu(self):
        """Remove all menu items.

        Supprimez tous les éléments de menu et les observateurs associés.
        """
        # log.debug(f"Menu.clearMenu supprime tout les éléments de menu de {self}")
        # log.debug("Menu.clearMenu : %d éléments de menu à supprimer.", len(self.MenuItems))

        for menuItem in self.MenuItems:
            self.DestroyItem(menuItem)
        for observer in self._observers:
            observer.removeInstance()
        self._observers = list()
        # log.debug("Menu.clearMenu : Tous les éléments et observateurs ont été supprimés.")

    def accelerators(self):
        """Retourne la liste des accélérateurs du menu."""
        return self._accels

    def appendUICommand(self, uiCommand):
        """Ajoute uiCommand à la liste des menus.

        Cette méthode est responsable d'ajouter une seule UICommand à ce menu.

        Fonctionnalité : Cette méthode prend une instance de UICommand
        et l'ajoute au menu actuel (self).

        Args :
            uiCommand : Commande à ajouter au menus.

        Returns :
            cmd (int) : L'ID de la commande ajoutée.
        """
        # log.debug(f"Menu.appendUICommand ajoute {uiCommand} à la liste des menus de {self}")
        # log.info(f"Menu.appendUICommand ajoute l' uiCommand {uiCommand.__class__.__name__} à la liste des menus de {self.__class__.__name__} dans {self._window} winId={self._window.GetId()}")
        # En comprenant comment appendUICommand interagit avec UICommand.addToMenu
        # et en s'assurant que la fenêtre et les données (comme les noms de bitmap) sont valides,
        # vous augmenterez vos chances de résoudre les problèmes d'affichage des menus.
        # La gestion des erreurs commentée dans appendUICommand est un point d'investigation important.

        # Vieille ligne
        # Ligne clé. Ici, la méthode addToMenu de l'objet UICommand
        # (définie dans base_uicommand.py) est appelée.
        # Il est crucial de noter que self (l'instance de Menu)
        # est passée comme le menu argument à UICommand.addToMenu,
        # et self._window (la fenêtre principale) est passée comme l'argument window.
        #  L'affichage correct des éléments de menu (texte, icône)
        #  dépend fortement de l'implémentation de UICommand.addToMenu.
        #  Si cette méthode dans base_uicommand.py ne fonctionne pas correctement
        #  (par exemple, ne charge pas les icônes, ne définit pas le texte correctement,
        #  ou ne lie pas les événements à la bonne fenêtre),
        #  les menus ne s'afficheront pas comme prévu.
        #  Potentiels problèmes avec la fenêtre self._window :
        #  Si la fenêtre principale référencée par self._window n'est pas valide
        #  ou n'est pas correctement initialisée au moment où appendUICommand est appelé,
        #  cela pourrait entraîner des problèmes lors de
        #  la liaison des événements dans UICommand.addToMenu.

        # cmd = uiCommand.addToMenu(self, self._window)
        # self._accels.extend(uiCommand.accelerators())
        # if isinstance(uiCommand, patterns.Observer):
        #     self._observers.append(uiCommand)
        # return cmd

        # # test conseillé par chatGPT
        # # Why this line try ?
        cmd = None
        try:
            log.debug(
                f"Menu.appendUICommand Essaie d'ajouter {uiCommand.__class__.__name__} au menu {self.__class__.__name__}"
                f" dans la classe {self._window.ClassName} {type(self._window).__name__} winId={self._window.GetId()}"
            )
            cmd = uiCommand.addToMenu(self, self._window)
            # cmd = self.addToMenu(uiCommand, self._window)
            # AttributeError: 'tuple' object has no attribute 'addToMenu'
            # Mais l'erreur MenuItem(): argument 1 has unexpected type 'module'
            # signifie que self ici n’est pas un wx.Menu mais probablement
            # le module menu lui-même.
        except (wx._core.wxAssertionError, AttributeError) as e:
            # print(f"Error adding UI command to menu: {e}")
            log.error(
                f"Menu.appendUICommand : Erreur en ajoutant UI command {uiCommand.__class__.__name__} au menu {self.__class__.__name__}: {e}"
            )
            # raise AssertionError(e)
            # Handle the error or create a new ID manually
            # new_id = wx.NewIdRef().GetId()
            # new_id = wx.ID_ANY
            # # Un élément de menu MenuItem représente un élément dans un menu.
            # log.info(f"uiCommand.menuText={uiCommand.menuText}")
            # cmd = wx.MenuItem(uicommand, parentMenu=self, id=new_id, text=uiCommand.menuText,
            #                   helpString=uiCommand.helpText, kind=uiCommand.kind)
            # AttributeError: 'tuple' object has no attribute 'menuText'
        except Exception as e:
            log.exception(
                "Menu.appendUICommand : Une erreur inattendue est survenue lors de l'ajout de uiCommand: %s",
                e,
            )
        # Ajout des accélérateurs :
        #  Les accélérateurs définis dans la UICommand sont ajoutés
        #  à la liste des accélérateurs du menu.
        self._accels.extend(uiCommand.accelerators())
        # Gestion des observateurs :
        #  Si la UICommand est également un observateur (selon le pattern.Observer),
        #  elle est ajoutée à la liste des observateurs du menu.
        if isinstance(uiCommand, patterns.Observer):
            # Ajoute le menu uiCommand à la liste de menus _observers
            self._observers.append(uiCommand)
        # Retourne cmd :
        #  La variable cmd (qui devrait être l'ID de l'élément de menu retourné
        #  par uiCommand.addToMenu) est retournée.
        return cmd

    # def appendMenu(self, text, subMenu, bitmap=None):
    def appendMenu(
        self, text, subMenu, bitmap=None, viewer=None, enableCondition=None
    ):
        """
        Ajoute un sous-menu au menu.

        Args :
            text (str) : Le texte du sous-menu.
            subMenu (Menu) : Le sous-menu à ajouter.
            bitmap (str | None) : (optionnel) Un bitmap optionnel pour l'icône du sous-menu.
        """
        # log.debug(f"Menu.appendMenu : ajoute un sous-menu {text}{subMenu} à la liste des menus de {self}")
        #  Elle crée un wx.MenuItem pour le sous-menu et
        #  lui associe éventuellement un bitmap.
        #  Elle étend également la liste des accélérateurs avec ceux du sous-menu.
        #  Il semble que le bitmap soit chargé directement ici en utilisant wx.ArtProvider.GetBitmap.
        #  Si le bitmap n'est pas valide,
        #  cela pourrait potentiellement causer des problèmes d'affichage ou même des erreurs.
        # subMenuItem = wx.MenuItem(self, id=IdProvider.get(), text=text, subMenu=subMenu)
        # # Nouvelle ligne conseillée par chatGPT
        subMenuId = IdProvider.get()  # Obtenir un nouvel identifiant unique
        # subMenuId = wx.ID_ANY  # Obtenir un nouvel identifiant unique
        subMenuItem = wx.MenuItem(
            self, id=subMenuId, text=text, subMenu=subMenu
        )  # TypeError(MenuItem argument subMenu has unexpected type ResetCategoryFilter)
        # print(f"tclib.gui.menu.py appendMenu: self:{self} .id:{subMenuId}, text={text}, subMenu={subMenu}")
        if bitmap:
            # subMenuItem.SetBitmap(wx.ArtProvider.GetBitmap(bitmap,
            #                                                wx.ART_MENU, (16, 16)))
            subMenuItem.SetBitmap(
                artprovider.ArtProvider.GetBitmap(
                    bitmap, wx.ART_MENU, (16, 16)
                )
            )
        self._accels.extend(subMenu.accelerators())
        # Création du sous-menu :
        # self.AppendItem(subMenuItem)
        # Préférer :
        log.debug(
            f"Menu.appendMenu : Ajout du sous-menu {type(subMenuItem).__name__} à self={type(self).__name__}."
        )
        self.Append(subMenuItem)

        # If custom condition provided, use it; otherwise check selection
        if enableCondition is not None:
            menuId = subMenuItem.GetId()

            def onUpdateUI(event, cond=enableCondition):
                event.Enable(cond())

            self._window.Bind(wx.EVT_UPDATE_UI, onUpdateUI, id=menuId)
        elif viewer is not None:
            menuId = subMenuItem.GetId()

            def onUpdateUI(event, v=viewer):
                event.Enable(bool(v.curselection()))

            self._window.Bind(wx.EVT_UPDATE_UI, onUpdateUI, id=menuId)
        # nouvelle ligne conseillée par chatGPT
        # return subMenuItem

    # Nouvelle fonction conseillée par chatGPT
    # def __del__(self):
    #    for menuItem in self.MenuItems:
    #        IdProvider.put(menuItem.GetId())  # Libérer l'identifiant lors de la destruction

    def invokeMenuItem(self, menuItem):
        """Programmatically invoke the menuItem. This is mainly for testing
        purposes."""
        # log.debug("Menu.invokeMenuItem : Déclenchement programmatique de %s", menuItem)
        # self._window.ProcessEvent(wx.CommandEvent(
        #     wx.wxEVT_COMMAND_MENU_SELECTED, winid=menuItem.GetId()))
        self._window.ProcessEvent(
            wx.CommandEvent(
                wx.wxEVT_COMMAND_MENU_SELECTED, id=menuItem.GetId()
            )
        )

    def openMenu(self):
        """Programmatically open the menu. This is mainly for testing
        purposes."""
        # On Mac OSX, an explicit UpdateWindowUI is needed to ensure that
        # menu items are updated before the menu is opened. This is not needed
        # on other platforms, but it doesn't hurt either.
        self._window.UpdateWindowUI()
        self._window.ProcessEvent(wx.MenuEvent(wx.wxEVT_MENU_OPEN, menu=self))

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Crée un sous-menu et y ajoute une liste de commandes UI.

        Args :
            menuTitle : Titre du sous-menu.
            uiCommands : Liste des commandes à ajouter.
        """
        # from taskcoachlib.gui import menu
        # log.debug(f"appendSubMenuWithUICommands ajoute {uiCommands} au nouveau menu {menuTitle} dans {self}")
        subMenu = Menu(self._window)
        # log.debug(f"Menu.appendSubMenuWithUICommands Ajoute un sous-menu {menuTitle}{subMenu} à {self}")

        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(*uiCommands)  # pylint: disable=W0142


class DynamicMenu(Menu):
    """Un menu dynamique qui s'enregistre pour des événements et se met à jour automatiquement.

    Un menu qui s'inscrit pour les événements puis se met à jour chaque fois que l'événement est licencié.

    Méthodes :
        __init__(self, window, parentMenu=None, labelInParentMenu="") :
            Initialise le menu dynamique.
        registerForMenuUpdate (self) :
            Méthode abstraite pour enregistrer le menu aux événements de mise à jour.
        onUpdateMenu (self, newValue, sender) : Met à jour le menu lorsque l'événement est déclenché.
        updateMenu (self) : Met à jour les éléments du menu.
    """

    def __init__(self, window, parentMenu=None, labelInParentMenu=""):
        """Initialise le menu. labelInParentMenu est nécessaire pour pouvoir
        trouver ce menu dans son parentMenu."""
        log.info(
            "DynamicMenu : Création du menu Dynamique. Initialisation du menu contextuel : %s",
            self.__class__.__name__,
        )
        # log.debug(f"Initialisation de DynamicMenu. (self={self} window={window} parentMenu={parentMenu})")
        super().__init__(window)
        # log.info("DynamicMenu : méthode super() passé.")

        self._parentMenu = parentMenu
        self._labelInParentMenu = self.__GetLabelText(labelInParentMenu)
        # log.info("DynamicMenu : Attributs configurés.")
        self.registerForMenuUpdate()
        # log.info("DynamicMenu : Enregistrement pour update effectué.")
        self.updateMenu()
        log.info(
            f"DynamicMenu : menu Dynamique {self.__class__.__name__} créé."
        )

    def registerForMenuUpdate(self):
        """Les sous-classes sont chargées de lier un événement à onUpdateMenu afin
        que le menu ait la possibilité de se mettre à jour au bon moment."""
        raise NotImplementedError

    def onUpdateMenu(self, newValue, sender):
        """Ce gestionnaire d'événements doit être appelé au bon moment afin que
        le menu ait une chance de se mettre à jour."""
        # log.debug(f"DynamicMenu.onUpdateMenu : Mise à jour.")
        # log.debug("DynamicMenu.onUpdateMenu appelé par %s, nouvelle valeur : %s", sender, newValue)
        try:  # Préparez-vous à ce que le menu ou la fenêtre soit détruit
            self.updateMenu()
            # except wx.PyDeadObjectError:
        except RuntimeError as e:
            log.error("DynamicMenu.onUpdateMenu : erreur : %s", e)
            pass

    def onUpdateMenu_Deprecated(self, event=None):
        """Ce gestionnaire d'événements doit être appelé au bon moment afin que
        le menu ait une chance de se mettre à jour."""
        # Si ceci est appelé par wx, 'ignorez' l'événement afin que l'autre événement
        # gestionnaires ait également une chance:
        if event and hasattr(event, "Skip"):
            event.Skip()
            if event.GetMenu() != self._parentMenu:
                return
        try:  # Vous prépare à ce que le menu ou la fenêtre soit détruit
            self.updateMenu()
            # except wx.PyDeadObjectError:
        except RuntimeError:
            # except:  # TODO: a essayer
            pass

    def updateMenu(self):
        """La mise à jour du menu se compose de deux étapes : mettre à jour l'élément de menu
        de ce menu dans son menu parent, par ex. pour l'activer ou le désactiver, et
        la mise à jour des éléments de menu de ce menu."""
        # log.debug(f"updateMenu : Début de mise à jour du menu {self}")
        self.updateMenuItemInParentMenu()
        self.updateMenuItems()

    def updateMenuItemInParentMenu(self):
        """Renvoie Activer ou désactiver l'élément de menu dans le menu parent en fonction de
        ce qui est activé()."""
        if self._parentMenu:
            myId = self.myId()
            if myId != wx.NOT_FOUND:
                log.debug(
                    f"DynamicMenu.updateMenuItemInParentMenu : Activation de l'ID={myId} dans le menu parent {type(self._parentMenu)}."
                )
                self._parentMenu.Enable(myId, self.enabled())
                # TypeError: Menu.Enable(): argument 1 has unexpected type 'NoneType'
            else:
                log.warning(
                    f"DynamicMenu.updateMenuItemInParentMenu : ID du menu introuvable dans le parent {self._parentMenu}."
                )

    def myId(self):
        """Renvoie l'identifiant de notre élément de menu dans le menu parent."""
        # Je préfère utiliser wx.Menu.FindItem, mais
        # il semble que cette méthode ne fonctionne actuellement pas
        # pour les éléments de menu avec accélérateurs (wxPython 2.8.6 sur Ubuntu).
        # TODO: Lorsque cela sera corrigé, remplacez les 7 lignes ci-dessous par celle-ci:
        # myId = self._parentMenu.FindItem(self._labelInParentMenu)
        log.info(f"DynamicMenu.myId : Appelé pour self={type(self).__name__}")
        for item in self._parentMenu.MenuItems:

            log.info(
                f"DynamicMenu.myId : pour item={type(item).__name__}  dans les {len(self._parentMenu.MenuItems)} éléments de {type(self._parentMenu.MenuItems)}"
            )
            log.info(
                f"{self.__GetLabelText(item.GetItemLabel())} comparé à {self._labelInParentMenu}"
            )
            # if self.__GetLabelText(item.GetText()) == self._labelInParentMenu:
            #     # AttributeError: 'MenuItem' object has no attribute 'GetText'
            if (
                self.__GetLabelText(item.GetItemLabel())
                == self._labelInParentMenu
            ):  # TODO : A REVOIR !
                return item.Id
        log.warning(f"⚡DynamicMenu.myId : self={type(self)} non trouvé !")
        return wx.NOT_FOUND
        # return myId

    def updateMenuItems(self):
        """Met à jour les éléments de menu de ce menu."""
        pass

    def enabled(self):
        """Renvoie un booléen indiquant si ce menu doit être activé dans
        son menu parent. Cette méthode est appelée par
        updateMenuItemInParentMenu(). Il renvoie True par défaut. Outrepasser
        dans une sous-classe selon les besoins."""
        return True

    @staticmethod
    def __GetLabelText(menuText):
        """Supprimez les accélérateurs du menuTexte. Ceci est nécessaire car sur
        certaines plates-formes '&' sont remplacés par '_' afin que les menuTexts puissent être comparés
        différents même s'ils sont en réalité les mêmes."""
        return menuText.replace("&", "").replace("_", "")


class DynamicMenuThatGetsUICommandsFromViewer(DynamicMenu):
    def __init__(
        self, viewer, parentMenu=None, labelInParentMenu=""
    ):  # pylint: disable=W0621
        # Shadows name 'viewer' from outer scope
        # log.info("DynamiqueThatGetsUICommandsFromViewer : Création du menu. Initialisation du menu contextuel : %s", self.__class__.__name__)

        self._uiCommands = None
        super().__init__(viewer, parentMenu, labelInParentMenu)

    def registerForMenuUpdate(self):
        # Refill the menu whenever the menu is opened, because the menu might
        # depend on the status of the viewer:
        # log.info("DynamicMenuThatGetsUICommandsFromViewer.registerForMenuUpdate: Commande exécutée : self.onUpdateMenu_Deprecated.")

        self._window.Bind(
            wx.EVT_MENU_OPEN, self.onUpdateMenu_Deprecated
        )  # ancien
        # self._window.bind(wx.EVT_MENU_OPEN, self.onUpdateMenu_Deprecated)  # j'essaie d'utiliser celui de window sauf que wx.EVT_MENU_OPEN n'est pas une fenêtre.

    def updateMenuItems(self):
        newCommands = self.getUICommands()
        try:
            if newCommands == self._uiCommands:
                log.debug(
                    "DynamicMenuThatGetsUICommandsFromViewer.updateMenuItems : Aucune mise à jour nécessaire pour le menu : les commandes sont inchangées."
                )
                return
        # except wx._core.PyDeadObjectError:  # pylint: disable=W0212
        # except wx.PyDeadObjectError:  # pylint: disable=W0212
        except RuntimeError as e:
            log.debug(
                f"DynamicMenuThatGetsUICommandsFromViewer.updateMenuItems : Erreur lors la mise à jour du menu: {e}"
            )
            pass  # Old viewer was closed
        log.debug(
            "DynamicMenuThatGetsUICommandsFromViewer.updateMenuItems : Les commandes UI ont changé, mise à jour du menu."
        )
        self.clearMenu()
        self.fillMenu(newCommands)
        self._uiCommands = newCommands

    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands)  # pylint: disable=W0142

    def getUICommands(self):
        raise NotImplementedError


class MainMenu(wx.MenuBar):
    """
    Barre de Menu principal de Task Coach.

    Ce menu regroupe plusieurs menus, tels que le menu Fichier, Éditer, Affichage, Nouveau, Actions et Aide, ainsi que leurs sous-menus respectifs.

    Méthodes :
        __init__(self, mainwindow, settings, iocontroller, viewerContainer, taskFile) :
            Initialise la barre de menu principale avec tous les sous-menus.
    """

    # Appelé par MainWindow.__create_menu_bar
    def __init__(
        self, mainwindow, settings, iocontroller, viewerContainer, taskFile
    ):
        """
        Initialise la barre de menu principale avec tous les sous-menus.

        Args :
            mainwindow :
            settings :
            iocontroller :
            viewerContainer :
            taskFile :
        """
        log.info("MainMenu : Création du menu principal.")
        # log.info("MainMenu : Initialisation du menu contextuel : %s", self.__class__.__name__)
        # log.debug(f"Initialisation de MainMenu avec self={self}, mainwindow={mainwindow}, settings={settings}")
        # log.debug(f"iocontroller={str(iocontroller)}, viewerContainer={viewerContainer}, taskFile={taskFile}")
        super().__init__()
        accels = list()
        _mainWin = mainwindow
        for menulisted, text in [
            (
                FileMenu(mainwindow, settings, iocontroller, viewerContainer),
                _("&File"),
            ),
            (
                EditMenu(mainwindow, settings, iocontroller, viewerContainer),
                _("&Edit"),
            ),
            (
                ViewMenu(mainwindow, settings, viewerContainer, taskFile),
                _("&View"),
            ),
            (
                NewMenu(mainwindow, settings, taskFile, viewerContainer),
                _("&New"),
            ),
            (
                ActionMenu(mainwindow, settings, taskFile, viewerContainer),
                _("&Actions"),
            ),
            (HelpMenu(mainwindow, settings, iocontroller), _("&Help")),
        ]:
            # log.debug(f"MainMenu : Ajout du menu {menulisted}{text} au menuBar MainMenu {self}")

            self.Append(
                menulisted, text
            )  # Tous doivent être de forme (wx.Menu(), '&Name')
            accels.extend(menulisted.accelerators())
        mainwindow.SetAcceleratorTable(wx.AcceleratorTable(accels))
        log.info("MainMenu : Menu principal créé !")


class FileMenu(Menu):
    """
    Menu Fichier dans Task Coach.

    Ce menu contient des options telles que Ouvrir, Enregistrer, Importer, Exporter, etc.
    """

    def __init__(self, mainwindow, settings, iocontroller, viewerContainer):
        """
        Initialise le menu Fichier.

        Args :
            mainwindow :
            settings :
            iocontroller :
            viewerContainer :
        """
        # log.info("FileMenu : Création du menu File/Fichier. Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.__settings = settings
        self.__iocontroller = iocontroller
        self.__recentFileUICommands = []
        self.__separator = None
        # Ajout des commandes :
        self.appendUICommands(
            uicommand.FileOpen(iocontroller=iocontroller),
            uicommand.FileMerge(iocontroller=iocontroller),
            uicommand.FileClose(iocontroller=iocontroller),
            None,
            uicommand.FileSave(iocontroller=iocontroller),
            uicommand.FileMergeDiskChanges(iocontroller=iocontroller),
            uicommand.FileSaveAs(iocontroller=iocontroller),
            uicommand.FileSaveSelection(
                iocontroller=iocontroller, viewer=viewerContainer
            ),
        )
        if not settings.getboolean("feature", "syncml"):
            self.appendUICommands(
                uicommand.FilePurgeDeletedItems(iocontroller=iocontroller)
            )
        self.appendUICommands(
            None,
            uicommand.FileSaveSelectedTaskAsTemplate(
                iocontroller=iocontroller, viewer=viewerContainer
            ),
            uicommand.FileImportTemplate(iocontroller=iocontroller),
            uicommand.FileEditTemplates(settings=settings),
            None,
            uicommand.PrintPageSetup(settings=settings),
            uicommand.PrintPreview(viewer=viewerContainer, settings=settings),
            uicommand.Print(viewer=viewerContainer, settings=settings),
            None,
        )
        # log.debug("FileMenu Ajoute un sous-menu Import")

        self.appendMenu(_("&Import"), ImportMenu(mainwindow, iocontroller))
        # log.debug("FileMenu Ajoute un sous-menu Export")
        self.appendMenu(
            _("&Export"),
            ExportMenu(mainwindow, iocontroller, settings),
            "export",
        )
        self.appendUICommands(
            None,
            uicommand.FileManageBackups(
                iocontroller=iocontroller, settings=settings
            ),
        )
        if settings.getboolean("feature", "syncml"):
            try:
                import taskcoachlib.syncml.core  # pylint: disable=W0612,W0404
            except ImportError:
                pass
            else:
                self.appendUICommands(
                    uicommand.FileSynchronize(
                        iocontroller=iocontroller, settings=settings
                    )
                )
        self.__recentFilesStartPosition = len(self)
        self.appendUICommands(None, uicommand.FileQuit())
        # self._window.bind(wx.EVT_MENU_OPEN, self.onOpenMenu)
        # AttributeError: 'MainWindow' object has no attribute 'bind'. Did you mean: 'Bind'?
        # S'agit-il de gui.uicommand.base_uicommand.UICommand.bind ?
        log.info("FileMenu : Commande exécutée : Ouvrir le menu")
        self._window.Bind(wx.EVT_MENU_OPEN, self.onOpenMenu)
        # Populate recent files at init (fixes GTK3 menu size bug)
        self.__insertRecentFileMenuItems()

        # Subscribe to settings changes to update recent files list
        # This replaces the broken EVT_MENU_OPEN approach
        # pub.subscribe(self.__onRecentFilesChanged, "settings.file.recentfiles")
        pub.subscribe(self.onOpenMenu, "settings.file.recentfiles")

    def onOpenMenu(self, event):
        """
        Gère l'ouverture du menu pour insérer les fichiers récents.

        Update recent files menu when settings change.

        Called via pub/sub when a file is opened or the recent files list
        is modified. This is the correct way to update dynamic menu content -
        update when data changes, not on every menu open.
        Args :
            event :

        Returns :

        """
        if event.GetMenu() == self:
            self.__removeRecentFileMenuItems()
            self.__insertRecentFileMenuItems()
        if event.GetMenu() != self:
            log.warning(
                "FileMenu.onOpenMenu appelé pour un autre menu : %s",
                event.GetMenu(),
            )
        event.Skip()

    def __insertRecentFileMenuItems(self):
        """
        Insère les fichiers récents dans le menu.

        Returns :

        """
        recentFiles = self.__settings.getlist("file", "recentfiles")
        if not recentFiles:
            return
        maximumNumberOfRecentFiles = self.__settings.getint(
            "file", "maxrecentfiles"
        )
        recentFiles = recentFiles[:maximumNumberOfRecentFiles]
        self.__separator = self.InsertSeparator(
            self.__recentFilesStartPosition
        )
        for index, recentFile in enumerate(recentFiles):
            recentFileNumber = (
                index + 1
            )  # Only computer nerds start counting at 0 :-)
            recentFileMenuPosition = (
                self.__recentFilesStartPosition + 1 + index
            )
            recentFileOpenUICommand = uicommand.RecentFileOpen(
                filename=recentFile,
                index=recentFileNumber,
                iocontroller=self.__iocontroller,
            )
            log.debug(
                f"FileMenu.__insertRecentFileMenuItems : Ajout du sous-menu recentFileOpenUICommand à {self} fenêtre {self._window}."
            )
            recentFileOpenUICommand.addToMenu(
                self, self._window, recentFileMenuPosition
            )
            self.__recentFileUICommands.append(recentFileOpenUICommand)

    def __removeRecentFileMenuItems(self):
        """
        Supprime les fichiers récents du menu.

        Returns :

        """
        for recentFileUICommand in self.__recentFileUICommands:
            log.debug(
                f"FileMenu.__removeRecentFileMenuItems Supprime recentFileUICommand du menu {self} fenêtre {self._window}"
            )

            recentFileUICommand.removeFromMenu(self, self._window)
        self.__recentFileUICommands = []
        if self.__separator:
            # self.RemoveItem(self.__separator)
            self.Remove(self.__separator)
            self.__separator = None


class ExportMenu(Menu):
    """
    Menu Exporter dans Task Coach.

    Ce menu contient des options pour exporter des tâches au format HTML, CSV, iCalendar, etc.

    Méthodes :
        __init__(self, mainwindow, iocontroller, settings) :
            Initialise le menu Exporter.
    """

    def __init__(self, mainwindow, iocontroller, settings):
        log.info(
            "ExportMenu : Création du menu Export. Initialisation du menu contextuel : %s",
            self.__class__.__name__,
        )

        super().__init__(mainwindow)
        kwargs = dict(iocontroller=iocontroller, settings=settings)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.FileExportAsHTML(**kwargs),
            uicommand.FileExportAsCSV(**kwargs),
            uicommand.FileExportAsICalendar(**kwargs),
            uicommand.FileExportAsTodoTxt(**kwargs),
        )


class ImportMenu(Menu):
    """
    Menu Importer dans Task Coach.

    Ce menu contient des options pour importer des tâches à partir de fichiers CSV, TodoTxt, etc.

    Méthodes :
        __init__(self, mainwindow, iocontroller) :
            Initialise le menu Importer.
    """

    def __init__(self, mainwindow, iocontroller):
        log.debug("Création du menu Import.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.FileImportCSV(iocontroller=iocontroller),
            uicommand.FileImportTodoTxt(iocontroller=iocontroller),
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

    def __init__(self, mainwindow, taskList, settings):
        log.debug("Création du menu Modèle de Tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.settings = settings
        self.taskList = taskList
        super().__init__(mainwindow)

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
            uicommand.TaskNewFromTemplate(
                os.path.join(path, name),
                taskList=self.taskList,
                settings=self.settings,
            )
            for name in persistence.TemplateList(path).names()
        ]
        if not commands:
            log.info("Aucun modèle de tâche trouvé dans : %s", path)
        return commands


class EditMenu(Menu):
    def __init__(self, mainwindow, settings, iocontroller, viewerContainer):
        log.debug("Création du menu Edit.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditUndo(),
            uicommand.EditRedo(),
            None,
            uicommand.EditCut(viewer=viewerContainer, id=wx.ID_CUT),
            uicommand.EditCopy(viewer=viewerContainer, id=wx.ID_COPY),
            uicommand.EditPaste(viewer=viewerContainer),
            uicommand.EditPasteAsSubItem(viewer=viewerContainer),
            None,
            uicommand.Edit(viewer=viewerContainer, id=wx.ID_EDIT),
            uicommand.Delete(viewer=viewerContainer, id=wx.ID_DELETE),
            None,
            uicommand.SelectAll(viewer=viewerContainer),
            uicommand.ClearSelection(viewer=viewerContainer),
            None,
            uicommand.EditPreferences(settings),
        )
        # Leave sufficient room for command names in the Undo and Redo menu
        # items:
        # log.debug("EditMenu Ajoute le menu : Sélectionner")
        self.appendMenu(
            _("&Select") + " " * 50, SelectMenu(mainwindow, viewerContainer)
        )
        # self.appendUICommands(None, uicommand.EditPreferences(settings))
        if settings.getboolean("feature", "syncml"):
            try:
                import taskcoachlib.syncml.core  # pylint: disable=W0612,W0404
            except ImportError:
                pass
            else:
                self.appendUICommands(
                    uicommand.EditSyncPreferences(
                        mainwindow=mainwindow, iocontroller=iocontroller
                    )
                )


class SelectMenu(Menu):
    def __init__(self, mainwindow, viewerContainer):
        log.debug("Création du menu Select/Sélectionner.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        kwargs = dict(viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.SelectAll(**kwargs), uicommand.ClearSelection(**kwargs)
        )


# Ancienne ligne (obsolète)
# activateNextViewerId = wx.NewId()
# activatePreviousViewerId = wx.NewId()

# Nouvelle ligne (correcte)
# activateNextViewerId = wx.Window.NewControlId()
# activatePreviousViewerId = wx.Window.NewControlId()
# essayer
# activateNextViewerId = wx.NewIdRef()
# activatePreviousViewerId = wx.NewIdRef()

activateNextViewerId = wx.ID_ANY
# activateNextViewerId = wx.NewId()
# activateNextViewerId = wx.NewIdRef(count=1)
activatePreviousViewerId = wx.ID_ANY
# activatePreviousViewerId = wx.NewId()
# activatePreviousViewerId = wx.NewIdRef(count=1)

# activateNextViewerId = wx.NewIdRef().GetId()
# activatePreviousViewerId = wx.NewIdRef().GetId()


class ViewMenu(Menu):
    """
    Menu View/Affichage dans Task Coach.

    Ce menu contient des options pour gérer l'affichage, les modes de vue, les filtres, les colonnes, etc.
    """

    def __init__(self, mainwindow, settings, viewerContainer, taskFile):
        """
        Initialise le menu Voir avec divers sous-menus comme les options d'affichage et les colonnes.

        Args :
            mainwindow :
            settings :
            viewerContainer :
            taskFile :
        """
        log.info(
            f"ViewMenu : Création du menu View/Affichage. {self.__class__.__name__}"
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        # log.debug("ViewMenu : Ajout du menu Nouvelle visualisation.")
        self.appendMenu(
            _("&New viewer"),
            ViewViewerMenu(mainwindow, settings, viewerContainer, taskFile),
            "viewnewviewer",
        )
        self.appendMenu(
            _("&Move viewer"),
            MoveViewerMenu(mainwindow, viewerContainer),
            "moveviewer",
        )
        activateNextViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("&Activate next viewer\tCtrl+PgDn"),
            helpText=help.viewNextViewer,
            forward=True,
            bitmap="activatenextviewer",
            id=activateNextViewerId,
        )
        activatePreviousViewer = uicommand.ActivateViewer(
            viewer=viewerContainer,
            menuText=_("Activate &previous viewer\tCtrl+PgUp"),
            helpText=help.viewPreviousViewer,
            forward=False,
            bitmap="activatepreviousviewer",
            id=activatePreviousViewerId,
        )
        self.appendUICommands(
            activateNextViewer,
            activatePreviousViewer,
            uicommand.RenameViewer(viewer=viewerContainer),
            None,
        )
        # log.debug("ViewMenu : Ajout du menu : Mode")
        self.appendMenu(_("&Mode"), ModeMenu(mainwindow, self, _("&Mode")))
        # log.debug("ViewMenu : Ajout du menu : Filtre")
        self.appendMenu(
            _("&Filter"), FilterMenu(mainwindow, self, _("&Filter"))
        )
        # log.debug("ViewMenu : Ajout du menu : Sort/tri")
        self.appendMenu(_("&Sort"), SortMenu(mainwindow, self, _("&Sort")))
        # log.debug("ViewMenu : Ajout du menu : Colonnes")
        self.appendMenu(
            _("&Columns"), ColumnMenu(mainwindow, self, _("&Columns"))
        )
        # log.debug("ViewMenu : Ajout du menu : Rounding/arrondi")
        self.appendMenu(
            _("&Rounding"), RoundingMenu(mainwindow, self, _("&Rounding"))
        )
        # self.appendUICommands(None)
        # # log.debug("ViewMenu : Ajout du menu : Options d'arborescence")
        # self.appendMenu(
        #     _("&Tree options"),
        #     ViewTreeOptionsMenu(mainwindow, viewerContainer),
        #     "treeview"
        # )
        # self.appendUICommands(None)
        self.appendUICommands(
            None,
            uicommand.ViewExpandAll(viewer=viewerContainer),
            uicommand.ViewCollapseAll(viewer=viewerContainer),
            None,
        )
        # log.debug("ViewMenu : Ajout du menu : Barre d'Outils")
        self.appendMenu(_("T&oolbar"), ToolBarMenu(mainwindow, settings))
        self.appendUICommands(
            # uicommand.UICheckCommand(
            settings_uicommand.UICheckCommand(
                settings=settings,
                menuText=_("Status&bar"),
                helpText=_("Show/hide status bar"),
                setting="statusbar",
            ),
            None,
            uicommand.ResetWindowLayout(),
        )
        log.debug("ViewMenu initialisé avec succès.")


class ViewViewerMenu(Menu):
    def __init__(self, mainwindow, settings, viewerContainer, taskFile):
        log.info("Création du menu View Viewer.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        # import taskcoachlib
        super().__init__(mainwindow)
        ViewViewer = uicommand.ViewViewer
        kwargs = dict(
            viewer=viewerContainer, taskFile=taskFile, settings=settings
        )
        # pylint: disable=W0142
        viewViewerCommands = [
            ViewViewer(
                menuText=_("&Task"),
                helpText=_("Open a new tab with a viewer that displays tasks"),
                viewerClass=taskcoachlib.gui.viewer.TaskViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("Task &statistics"),
                helpText=_(
                    "Open a new tab with a viewer that displays task statistics"
                ),
                viewerClass=taskcoachlib.gui.viewer.TaskStatsViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("Task &square map"),
                helpText=_(
                    "Open a new tab with a viewer that displays tasks in a square map"
                ),
                viewerClass=taskcoachlib.gui.viewer.SquareTaskViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("T&imeline"),
                helpText=_(
                    "Open a new tab with a viewer that displays a timeline of tasks and effort"
                ),
                viewerClass=taskcoachlib.gui.viewer.TimelineViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Calendar"),
                helpText=_(
                    "Open a new tab with a viewer that displays tasks in a calendar"
                ),
                viewerClass=taskcoachlib.gui.viewer.CalendarViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Hierarchical calendar"),
                helpText=_(
                    "Open a new tab with a viewer that displays task hierarchy in a calendar"
                ),
                viewerClass=taskcoachlib.gui.viewer.HierarchicalCalendarViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Category"),
                helpText=_(
                    "Open a new tab with a viewer that displays categories"
                ),
                viewerClass=taskcoachlib.gui.viewer.CategoryViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Effort"),
                helpText=_(
                    "Open a new tab with a viewer that displays efforts"
                ),
                viewerClass=taskcoachlib.gui.viewer.EffortViewer,
                **kwargs,
            ),
            uicommand.ViewEffortViewerForSelectedTask(
                menuText=_("Eff&ort for selected task(s)"),
                helpText=_(
                    "Open a new tab with a viewer that displays efforts for the selected task"
                ),
                viewerClass=taskcoachlib.gui.viewer.EffortViewer,
                **kwargs,
            ),
            ViewViewer(
                menuText=_("&Note"),
                helpText=_("Open a new tab with a viewer that displays notes"),
                viewerClass=taskcoachlib.gui.viewer.NoteViewer,
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
                    viewerClass=taskcoachlib.gui.viewer.TaskInterdepsViewer,
                    **kwargs,
                )
            )
        except ImportError:
            pass
        self.appendUICommands(*viewViewerCommands)


class MoveViewerMenu(Menu):
    def __init__(self, mainwindow, viewerContainer):
        log.info("Création du menu Move Viewer.")
        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.MoveViewerLeft(viewer=viewerContainer),
            uicommand.MoveViewerRight(viewer=viewerContainer),
            uicommand.MoveViewerTop(viewer=viewerContainer),
            uicommand.MoveViewerBottom(viewer=viewerContainer),
            None,
            uicommand.MoveViewerLeftOuter(viewer=viewerContainer),
            uicommand.MoveViewerRightOuter(viewer=viewerContainer),
            uicommand.MoveViewerTopOuter(viewer=viewerContainer),
            uicommand.MoveViewerBottomOuter(viewer=viewerContainer),
            None,
            uicommand.MoveViewerCenter(viewer=viewerContainer),
        )


class ViewTreeOptionsMenu(Menu):
    def __init__(self, mainwindow, viewerContainer):
        log.info(
            "ViewTreeOptionsMenu : Création du menu des Options de vue Arborescente."
        )
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.ViewExpandAll(viewer=viewerContainer),
            uicommand.ViewCollapseAll(viewer=viewerContainer),
        )


class ModeMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.hasModes() and bool(
            self._window.viewer.getModeUICommands()
        )

    def getUICommands(self):
        return self._window.viewer.getModeUICommands()


class FilterMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isFilterable() and bool(
            self._window.viewer.getFilterUICommands()
        )

    def getUICommands(self):
        return self._window.viewer.getFilterUICommands()


class ColumnMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.hasHideableColumns()

    def getUICommands(self):
        return self._window.viewer.getColumnUICommands()


class SortMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isSortable()

    def getUICommands(self):
        return self._window.viewer.getSortUICommands()


class RoundingMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.supportsRounding()

    def getUICommands(self):
        return self._window.viewer.getRoundingUICommands()


class ToolBarMenu(Menu):
    """
    Création du menu de ToolBar.
    """

    def __init__(self, mainwindow, settings):
        log.info("Création du menu de la Barre d'Outils.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
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
                settings_uicommand.UIRadioCommand(
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

    def __init__(self, mainwindow, settings, taskFile, viewerContainer):
        log.info("Création du menu New/Nouveau.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
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
            TaskTemplateMenu(mainwindow, taskList=tasks, settings=settings),
            "newtmpl",
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


class ActionMenu(Menu):
    def __init__(self, mainwindow, settings, taskFile, viewerContainer):
        log.info("Création du menu Action.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        categories = taskFile.categories()
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
                mainwindow, categories=categories, viewer=viewerContainer
            ),
            "folder_blue_arrow_icon",
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
            TaskPriorityMenu(mainwindow, tasks, viewerContainer),
            "incpriority",
        )
        self.appendUICommands(
            None,
            uicommand.EffortStart(viewer=viewerContainer, taskList=tasks),
            uicommand.EffortStop(
                viewer=viewerContainer, effortList=efforts, taskList=tasks
            ),
            uicommand.EditTrackedTasks(taskList=tasks, settings=settings),
        )


class TaskPriorityMenu(Menu):
    def __init__(self, mainwindow, taskList, viewerContainer):
        log.info("Création du menu Priorité de Tâche.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        kwargs = dict(taskList=taskList, viewer=viewerContainer)
        # pylint: disable=W0142
        self.appendUICommands(
            uicommand.TaskIncPriority(**kwargs),
            uicommand.TaskDecPriority(**kwargs),
            uicommand.TaskMaxPriority(**kwargs),
            uicommand.TaskMinPriority(**kwargs),
        )


class HelpMenu(Menu):
    def __init__(self, mainwindow, settings, iocontroller):
        log.info("Création du menu Help/Aide.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
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


class TaskBarMenu(Menu):
    """
    Problème : Le problème est effectivement que TaskBarIcon
    n'est pas une sous-classe de wx.Window, et les menus wxPython
    (comme ceux gérés par UICommandContainerMixin) sont
    conçus pour être associés à des wx.Window.
    """

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
            "newtmpl",
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
        self.appendMenu(
            label,
            StartEffortForTaskMenu(
                taskBarIcon, base.filter.DeletedFilter(tasks), self, label
            ),
            "clock_icon",
        )
        self.appendUICommands(
            uicommand.EffortStop(
                viewer=viewer, effortList=efforts, taskList=tasks
            )
        )
        self.appendUICommands(
            None, uicommand.MainWindowRestore(), uicommand.FileQuit()
        )


class ToggleCategoryMenu(DynamicMenu):
    def __init__(
        self, mainwindow, categories, viewer
    ):  # pylint: disable=W0621
        log.info("Création du menu Toggle Catégorie.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        self.categories = categories
        self.viewer = viewer
        super().__init__(mainwindow)
        log.info("Toggle Catégorie initialisé.")

    def registerForMenuUpdate(self):
        for eventType in (
            self.categories.addItemEventType(),
            self.categories.removeItemEventType(),
        ):
            patterns.Publisher().registerObserver(
                self.onUpdateMenu_Deprecated,
                eventType=eventType,
                eventSource=self.categories,
            )
        patterns.Publisher().registerObserver(
            self.onUpdateMenu_Deprecated,
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
                f"ToggleCategoryMenu.addMenuItemsForCategories : Ajout du sous-menu : {uiCommand} dans {menuToAdd} fenêtre {self._window}"
            )
            uiCommand.addToMenu(menuToAdd, self._window)
        categoriesWithChildren = [
            category for category in categories if category.children()
        ]
        if categoriesWithChildren:
            menuToAdd.AppendSeparator()
            for category in categoriesWithChildren:
                # log.debug("ToggleCategoryMenu.addMenuItemsForCategories : est-ce là l'erreur!")
                subMenu = Menu(self._window)
                # log.debug(f"subMenu={subMenu}")
                self.addMenuItemsForCategories(category.children(), subMenu)
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
            patterns.Publisher().registerObserver(
                self.onUpdateMenu_Deprecated,
                eventType=eventType,
                eventSource=self.tasks,
            )
        for eventType in (
            task.Task.subjectChangedEventType(),
            task.Task.trackingChangedEventType(),
            task.Task.plannedStartDateTimeChangedEventType(),
            task.Task.dueDateTimeChangedEventType(),
            task.Task.actualStartDateTimeChangedEventType(),
            task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onUpdateMenu, eventType)
            else:
                patterns.Publisher().registerObserver(
                    self.onUpdateMenu_Deprecated, eventType
                )

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
            f"StartEffortForTaskMenu.addMenuItemForTask Ajoute le menu {uiCommand} à {menuItem} fenêtre {self._window}"
        )
        uiCommand.addToMenu(menuItem, self._window)
        trackableChildren = [
            child
            for child in task.children()
            if child in self.tasks and not child.completed()
        ]
        if trackableChildren:
            trackableChildren.sort(key=lambda child: child.subject())
            subMenu = Menu(self._window)
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
        self, mainwindow, settings, tasks, efforts, categories, taskViewer
    ):
        log.info("TaskPopupMenu : Création du menu Popup de Tâche.")
        super().__init__(mainwindow)
        # log.info("TaskPopuMenu : Initialisation du menu contextuel : %s", self.__class__.__name__)
        # log.debug(f"mainwindow={mainwindow}, settings={settings},"
        #           f"tasks={tasks}, efforts={efforts},"
        #           f"categories={categories}, taskViewer={taskViewer}")
        # Les commandes de menu sont ici :
        # log.debug("TaskPopupMenu : Ajoute une liste d'UICommands.")

        self.appendUICommands(
            uicommand.EditCut(viewer=taskViewer),
            uicommand.EditCopy(viewer=taskViewer),
            uicommand.EditPaste(viewer=taskViewer),
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
                mainwindow=mainwindow, categories=categories, viewer=taskViewer
            ),
            "folder_blue_arrow_icon",
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
            TaskPriorityMenu(mainwindow, tasks, taskViewer),
            "incpriority",
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
            uicommand.TaskNew(taskList=tasks, settings=settings),
            uicommand.NewSubItem(viewer=taskViewer),
        )
        log.info("TaskPopupMenu : Terminé - Menu Popup de Tâche créé !")


class EffortPopupMenu(Menu):
    def __init__(self, mainwindow, tasks, efforts, settings, effortViewer):
        log.info("Création du menu Popup Effort.")
        # log.debug("Affichage du menu contextuel pour les efforts.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=effortViewer),
            uicommand.EditCopy(viewer=effortViewer),
            uicommand.EditPaste(viewer=effortViewer),
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
        log.info("EffortPopupMenu : Menu Popup Effort créé !")


class CategoryPopupMenu(Menu):
    """
    Le menu CategoryPopupMenu s’appuie fortement sur UICommandContainerMixin,
    notamment avec 'self.appendUICommands([...])'.
    """

    def __init__(
        self, mainwindow, settings, taskFile, categoryViewer, localOnly=False
    ):
        log.info("Création du menu Popup Catégorie.")
        # log.debug("Affichage du menu contextuel pour les catégories.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        log.debug(
            "CategoryPopupMenu : Récupération des catégories, tâches et notes pour le menu."
        )
        categories = categoryViewer.presentation()
        tasks = taskFile.tasks()
        notes = taskFile.notes()
        self.appendUICommands(
            uicommand.EditCut(viewer=categoryViewer),
            uicommand.EditCopy(viewer=categoryViewer),
            uicommand.EditPaste(viewer=categoryViewer),
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
    def __init__(self, mainwindow, settings, categories, noteViewer):
        log.info("Création du menu Popup Note.")
        # log.debug("Affichage du menu contextuel pour les notes.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=noteViewer),
            uicommand.EditCopy(viewer=noteViewer),
            uicommand.EditPaste(viewer=noteViewer),
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
                mainwindow, categories=categories, viewer=noteViewer
            ),
            "folder_blue_arrow_icon",
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
        # if not self._window:  # Prevent PyDeadObject exception when running tests
        #     return []
        return [
            uicommand.HideCurrentColumn(viewer=self._window),
            None,
        ] + self._window.getColumnUICommands()


class ColumnPopupMenu(ColumnPopupMenuMixin, Menu):
    """Column header popup menu."""

    def __init__(self, window):
        log.info("Création du menu Popup Colonne.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(window)
        log.debug("ColumnPopupMenu : Appel de CallAfter.")
        wx.CallAfter(self.appendUICommands, *self.getUICommands())
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
    def __init__(self, mainwindow, settings, attachments, attachmentViewer):
        log.info("Création du menu Popup Attachment.")
        # log.info("Initialisation du menu contextuel : %s", self.__class__.__name__)

        super().__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=attachmentViewer),
            uicommand.EditCopy(viewer=attachmentViewer),
            uicommand.EditPaste(viewer=attachmentViewer),
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
