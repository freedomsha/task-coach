"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

Le mixin UICommandContainerMixin est conçu pour
ajouter des commandes d’interface utilisateur dans des menus ou des barres d’outils.

L'attribut _window est essentiel car il représente la fenêtre wxPython
à laquelle le menu ou la barre d'outils est associé. Les événements de menu
(clics, mises à jour de l'interface utilisateur) sont liés à cette fenêtre.
Si _window est manquant ou None, les événements ne peuvent pas être
correctement gérés, et cela peut entraîner des erreurs.
"""

# from builtins import object
import logging
import wx

# from taskcoachlib import patterns
from taskcoachlib.gui.newid import IdProvider

# from taskcoachlib.gui.menu import AppendSeparator, AppendStretchSpacer, Append, appendUICommand, _window, appendMenu
# from taskcoachlib.gui.menu import Menu
# from taskcoachlib.gui.toolbar import ToolBar

log = logging.getLogger(__name__)


# class UICommandContainerMixin(object):
class UICommandContainerMixin(object):
    """Mixin avec la (sous-)classe wx.Menu ou wx.ToolBar.

    Fournit la méthode appendUICommands aux classes qui veulent
    ajouter des commandes UI (comme les Menu et potentiellement les ToolBar).
    """

    # def __init__(self):
    #     #     self._window = None  # Il faut que self._window du menu existe et soit différent de None !
    #     self._window = wx.GetActiveWindow()  # À tester si la fenêtre doit être active

    # def appendUICommands(self, *uiCommands):
    def appendUICommands(self, *uiCommands, **kwargs):
        """Ajout de *uiCommand.

        **Responsabilité** :
        Cette méthode, qui est mélangée dans la classe Menu,
        prend une liste de UICommand et les ajoute au menu.
        Elle gère également les séparateurs, les espaces (pour les barres d'outils),
        les éléments de menu désactivés et les sous-menus.

        La méthode est responsable de parcourir la liste des uiCommands et
        de les ajouter au conteneur (menu ou barre d'outils).

        Args :
            *uiCommands :
            **kwargs :

        Returns :

        """
        # Il faut s'assurer que l'ID du menu est valide à ce moment-là.
        if (
            not hasattr(self, "_window") or self._window is None
        ):  # Unresolved attribute reference '_window' for class 'UICommandContainerMixin'
            # log.warning("UICommandContainerMixin.appendUICommands : l'attribut _window est manquant ou None, cela peut causer une erreur.")
            if not hasattr(self, "_window"):
                log.warning(
                    "UICommandContainerMixin.appendUICommands : l'attribut _window est manquant, cela peut causer une erreur."
                )
            elif self._window is None:
                log.warning(
                    "UICommandContainerMixin.appendUICommands : l'attribut _window est None, cela peut causer une erreur."
                )
            self._window = (
                wx.GetActiveWindow()
            )  # Assigner une fenêtre active si manquante
            log.warning(
                f"UICommandContainerMixin.appendUICommands : Attribution : self._window={self._window}."
            )
        # log.debug(f"UICommandContainerMixin.appendUICommands ajoute les UI commands: {uiCommands} au menu {self} id=?")  # Débogage
        # uicommands : taskcoachlib.gui.uicommand.uicommand.EditCut, EditCopy, EditPaste, EditPasteAsSubItem, Edit,
        # Delete, AddAtachment, OpenAllAttachments, AddNote, OpenAllNotes, Mail,...
        # Ajout de logs en cas de commandes vides ou nulles :
        if not uiCommands:
            log.warning("Aucune UICommand n’a été fournie à appendUICommands.")

        # Ancien code :
        for uiCommand in uiCommands:
            # log.debug(f"UICommandContainerMixin.appendUICommands : dir(self)={dir(self)}")
            if uiCommand is None:
                self.AppendSeparator()
            elif isinstance(uiCommand, int):  # Toolbars only
                self.AppendStretchSpacer(uiCommand)
            # elif isinstance(uiCommand, (str, unicode)):
            # elif isinstance(uiCommand, (str, str)):
            elif isinstance(uiCommand, str):
                label = wx.MenuItem(self, text=uiCommand)
                # must append item before disable to insure
                # that internal object exists
                # self.AppendItem(label)
                self.Append(label)
                label.Enable(False)
            elif type(uiCommand) is type(()):  # This only works for menu's
                menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
                self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
            else:
                self.appendUICommand(uiCommand)

        # Nouveau code
        # # Itération sur les Commandes :
        # for uiCommand in uiCommands:
        #     # Gestion des Différents Types d'Éléments :
        #     # TODO : Essayer d'utiliser match/case !
        #     if uiCommand is None:
        #         # None : Ajoute un séparateur (self.AppendSeparator()).
        #         # print(f"tclib.gui.uicommand.uicommandcontainer Appending UI command: {uiCommand}")  # Débogage
        #         # print(f"tclib.gui.uicommand.uicommandcontainer Appending command: {command.__class__.__name__}")
        #         # log.debug("UICommandContainerMixin.appendUICommands : l' uiCommand est None donc ajoute un séparateur.")
        #         self.AppendSeparator()  # customtreectrl ou toolbar ou XxxMenu!
        #         # elif isinstance(type(uiCommand), type()):  # This only works for menu's
        #         # TODO revenir sur mon choix:
        #         # elif isinstance(uiCommand, type(())):
        #         # ou garder celui de rainfornight :
        #         # elif type(uiCommand) == type(()):
        #         # elif isinstance(uiCommand, tuple):
        #     # elif isinstance(uiCommand, (tuple, list)):
        #     #     # tuple : Crée un sous-menu et y ajoute les commandes UI du tuple en appelant self.appendSubMenuWithUICommands().
        #     #     log.debug(f"UICommandContainerMixin.appendUICommands : l' uiCommand {uiCommand} est un tuple donc crée un sous-menu et y ajoute les commandes UI.")
        #     #     menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
        #     #     self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
        #     elif isinstance(uiCommand, tuple):
        #         self.appendMenu(*uiCommand)
        #     elif isinstance(uiCommand, list):
        #         self.appendSubMenuWithUICommands(*uiCommand)
        #     elif isinstance(uiCommand, int):  # Toolbars only
        #         # int : Ajoute un espace extensible (pour les barres d'outils, non pertinent ici).
        #         # log.debug(f"UICommandContainerMixin.appendUICommands : l' uiCommand {uiCommand} est int donc ajoute un espace extensible.")
        #         self.AppendStretchSpacer(uiCommand)
        #         # elif isinstance(uiCommand, (str,)):
        #     elif isinstance(uiCommand, str):
        #         # str : Ajoute un élément de menu désactivé.
        #         # Ajoute un élément dans le menu
        #         # log.debug(f"UICommandContainerMixin.appendUICommands : l' uiCommand {uiCommand} est str donc ajoute un élément de menu désactivé.")
        #         label = wx.MenuItem(self, text=uiCommand)
        #         # doit ajouter un élément avant de le désactiver pour assurer
        #         # que l'objet interne existe
        #         # self.AppendItem(label)  # wxPyDeprecationWarning: Call to deprecated item. Use Append instead.
        #         self.Append(label)  # Unresolved attribute reference 'Append' for class 'UICommandContainerMixin'
        #         # TODO : Sauf qu'AppendItem est défini dans customtreectrl.py
        #         # Normal car il s'agit d'une Mixin.
        #         label.Enable(False)
        #     else:
        #         # Autre (supposé être une instance de UICommand) :
        #         # Appelle récursivement self.appendUICommands(uiCommand).
        #         # C'est ici qu'une erreur de récursion infinie se produit
        #         # si la condition d'arrêt n'est pas correctement gérée.
        #         log.debug(f"UICommandContainerMixin.appendUICommands : l' uiCommand {uiCommand}est un autre-chose donc ajoute la commande UI.")
        #         log.debug(f"Type de uiCommand : {type(uiCommand)}, contenu : {repr(uiCommand)}")
        #         # self.appendUICommand(uiCommand)  # [Previous line repeated 972 more times]
        #         # Vérification pour éviter une récursion infinie
        #         if not hasattr(uiCommand, "_appended"):
        #             log.debug(f"UICommandContainerMixin.appendUICommands : l' uiCommand {uiCommand} n'a pas _append.")
        #             try :
        #                 # self.appendUICommand(uiCommand)  # Méthode de Menu ou Toolbar
        #                 itemId = IdProvider.get()
        #                 log.debug(f"UICommandContainerMixin.appendUICommands: Ajout de la commande {uiCommand.menuText} avec l'ID {itemId} à la fenêtre {self._window.GetId() if self._window else None}")
        #                 if self._window:
        #                     if not self._window.IsBeingDeleted():
        #                         self.append(uiCommand, self._window, itemId)
        #                         self._uiCommands[itemId] = uiCommand
        #                         self._window.Bind(wx.EVT_MENU, self.onUICommand, id=itemId)
        #                         self._window.Bind(wx.EVT_UPDATE_UI, self.onUpdateUICommand, id=itemId)
        #                         if uiCommand.kind == wx.ITEM_CHECK:
        #                             self._window.Bind(wx.EVT_MENU, self.onCheckCommand, id=itemId)
        #                     else:
        #                         log.warning(f"appendUICommands: La fenêtre {self._window} est en cours de suppression, la commande {uiCommand} n'est pas ajoutée.")
        #                 else:
        #                     log.error(f"appendUICommands: self._window est None, impossible d'ajouter la commande {uiCommand}.")
        #             except Exception as e:
        #                 log.error(f"UICommandContainerMixin.appendUICommands n'arrive pas à ajouter {uiCommand} : erreur {e}")
        #                 # <taskcoachlib.gui.uicommand.uicommand.EditCopy object at 0x72988b94d790>
        #                 # erreur MenuItem(): argument 1 has unexpected type 'module'
        #             # Mettre un drapeau après l'ajout de l'ordre.
        #             uiCommand._appended = True
        #         # La récursion actuelle (self.appendUICommands(uiCommand))
        #         # est incorrecte et doit être corrigée.
        #         # RecursionError: maximum recursion depth exceeded
        #         # Corrigez l'Erreur de Récursion dans appendUICommands() :
        #         # log.debug(f"Appending UI command: {uiCommand}")  # Débogage
        #         # # Remplacement de la ligne récursive par l'appel direct à addToMenu() :
        #         # cmd = uiCommand.addToMenu(self, self._window)
        #         # print(f"Command added to menu: {cmd}")  # Débogage
        #         # self._accels.extend(uiCommand.accelerators())
        #         # # if isinstance(uiCommand, patterns.Observer):
        #         # #     self._observers.append(uiCommand)
        #         # # Notez que j'ai ajouté des vérifications pour s'assurer que
        #         # # les attributs _accels et _observers existent sur l'objet self
        #         # # avant d'y accéder.
        #         # if hasattr(self, '_accels'):
        #         #     self._accels.extend(uiCommand.accelerators())
        #         # if hasattr(self, '_observers') and isinstance(uiCommand, patterns.Observer):
        #         #     self._observers.append(uiCommand)
        #         # return cmd
        # log.debug(f"UICommandContainerMixin.appendUICommands a terminé d'ajouter les uiCommands={uiCommands}")
        log.debug(
            f"UICommandContainerMixin.appendUICommands a terminé d'ajouter les uiCommands !"
        )

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Cette méthode crée un nouveau menu.Menu,
        l'ajoute comme sous-menu au menu actuel,
        puis appelle récursivement subMenu.appendUICommands()
        pour ajouter les commandes au sous-menu.

        Args :
            menuTitle : Nom du sous-menu à créer.
            uiCommands : Liste des commandes à y ajouter

        Returns :

        """
        from taskcoachlib.gui import (
            menu,
        )  # Pas en début de fichier, risque de circular import (menu->viewer->viewer.task->viewer.base->toolbar->uicommandcontainer)

        if not hasattr(self, "_window") or self._window is None:
            log.warning(
                "UICommandContainerMixin.appendSubMenuWithUICommands : l'attribut _window est manquant ou None, cela peut causer une erreur."
            )

        subMenu = menu.Menu(self._window)
        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(*uiCommands)  # pylint: disable=W0142

    # def AppendSeparator(self):
    #     return wx.Menu.AppendSeparator(self)
    #
    # def AppendStretchSpacer(self, uiCommand):
    #     self.AddStretchSpacer(proportion)
    #     pass
    #
    # def AppendItem(self, label):
    #     pass
    #
    # def appendMenu(self, menuTitle, subMenu):
    #     pass
