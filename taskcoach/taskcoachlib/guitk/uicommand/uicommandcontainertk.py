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
along with this program. If not, see <http://www.gnu.org/licenses/>.

Le mixin UICommandContainerMixin est conçu pour ajouter des commandes
d’interface utilisateur dans des menus ou des barres d’outils.

L'attribut _window est essentiel car il représente la fenêtre Tkinter
à laquelle le menu ou la barre d'outils est associé.
"""

# coding=utf-8
# """ Mixin pour les conteneurs de commandes d'interface utilisateur Tkinter.
# Ce mixin fournit la méthode appendUICommands pour ajouter des commandes UI
# Fonctionnement actuel de UICommandContainerMixin
# Le mixin UICommandContainerMixin est conçu pour faciliter l'ajout de commandes d'interface utilisateur (UI) à des menus et des barres d'outils dans une application Tkinter 1 2 3. Il fournit une méthode appendUICommands pour ajouter des commandes UI à un conteneur (menu ou barre d'outils) 4. Il gère les séparateurs et les sous-menus 4.
# Points à vérifier et à compléter :
#
# Initialisation (__init__):
# Vérifier que la fenêtre parente est bien un objet Tkinter valide (soit tk.Tk, tk.Frame ou tk.Menu) 4 5 6.
# S'assurer que l'attribut _tearoff est correctement initialisé et est soit 0 ou 1 5 6.
# Ajouter des vérifications pour s'assurer que les méthodes appendUICommand, add_h_separator et appendSubMenuWithUICommands sont implémentées par la classe qui utilise ce mixin 7 8.
# Ajouter une gestion des erreurs plus robuste si la fenêtre parent n'est pas fournie.
#
#
# appendUICommands:
# Gérer correctement les séparateurs (None dans la liste des commandes) 9.
# Gérer les sous-menus (tuples dans la liste des commandes) en appelant récursivement appendUICommands 10.
# S'assurer que la méthode appendUICommand est appelée pour ajouter les commandes individuelles 10.
# Ajouter une gestion des erreurs si uiCommand n'est ni None, ni un tuple, ni une instance de UICommand.
# Ajouter un log d'erreur si parent_window n’a pas été fourni dans les kwargs 9.
#
#
# appendSubMenuWithUICommands:
# Créer un sous-menu Tkinter et l'ajouter au menu parent 11 12.
# Appeler récursivement appendUICommands pour ajouter les commandes au sous-menu 12.
#
#
# appendUICommand:
# Cette méthode doit être implémentée par la classe qui utilise le mixin. Elle est responsable de l'ajout réel de la commande à l'élément d'interface utilisateur (menu ou barre d'outils) 12.
#
#
# add_h_separator:
# Cette méthode doit être implémentée par la classe qui utilise le mixin. Elle est responsable de l'ajout d'un séparateur horizontal à l'élément d'interface utilisateur (menu ou barre d'outils) 13.
#
#
# Explications des améliorations :
# Gestion des erreurs améliorée: Ajout de vérifications et de logs pour s'assurer que les méthodes requises sont implémentées et que les arguments sont valides.
# Clarté accrue : Ajout de commentaires pour expliquer le fonctionnement de chaque méthode.
# Robustesse : Gestion des exceptions lors de l'ajout de commandes individuelles.
#
# Pour la suite :
# Dans menutk.py et toolbartk.py, vous devrez implémenter les méthodes appendUICommand et add_h_separator pour qu'elles fonctionnent avec les menus et barres d'outils Tkinter.
# Assurez-vous que les classes de commandes UI (UICommand) sont compatibles avec Tkinter (c'est-à-dire qu'elles peuvent être appelées comme des fonctions Tkinter).
import logging
import tkinter as tk
import tkinterdnd2
from tkinterdnd2 import *
from tkinter import ttk

# from tkinter import Menu

# Assurez-vous que taskcoachlib.gui.newid existe et est compatible avec Tkinter
# Sauf qu'il est inutile !
# from taskcoachlib.guitk.newid import IdProvider

log = logging.getLogger(__name__)


class UICommandContainerMixin(object):
    """Mixin pour les classes qui agissent comme des conteneurs de commandes
    d'interface utilisateur (comme les menus ou les barres d'outils).

    Fournit la méthode appendUICommands nécessaire aux classes
    qui veulent ajouter des commandes UI à des menus ou barres d'outils.
    """

    # Ce mixin fournit la méthode appendUICommands
    # pour ajouter des commandes UI à un conteneur (comme un menu ou une barre d'outils).
    # Il gère les séparateurs et les sous-menus

    def __init__(self, parent_window, tearoff=0):
        """
        Initialise le mixin conteneur de commande UI.

        Args :
            parent_window (tk.Tk | tk.Toplevel):
                Fenêtre principale Tkinter ou menu parent valide.
            tearoff :
                Indique si le menu peut être détaché (Tkinter).
        """
        # Assertion centrale : Vérification immédiate de la validité de la fenêtre parente qui garantit l'architecture
        assert_valid_parent_window(parent_window, self)

        # Stocke la fenêtre ou le menu parent (vérité unique)
        self.__window = parent_window
        # Stocke la configuration tearoff
        self._tearoff = tearoff
        log.debug(
            f"UICommandContainerMixin : La classe {self.__class__.__name__} initialise pour ajouter des commandes UI dans self.__window={self.__window} de classe {self.__window.__class__.__name__}."
        )
        # if not isinstance(parent_window, (tk.Tk, tk.Frame, tk.Menu)):
        #     log.warning(f"UICommandContainerMixin : parent_window={parent_window.__class__.__name__}(type={type(parent_window)}) doit être de type tk.Tk ou tk.Frame ou tk.Menu!")
        #     log.warning(f"UICommandContainerMixin : self={self.__class__.__name__}(type={type(self)}) doit être un menu !")
        # if not hasattr(self, '__window') or self.__window is None:
        #     log.warning("UICommandContainerMixin.__init__ : l'attribut __window est manquant ou None.")
        #     self.__window = getattr(self, '__window', None)
        # if not hasattr(self, "__window") or self.__window is None:
        #     # log.error("UICommandContainerMixin.__init__ : parent_window n’a pas été fourni et __window est également None.")
        #     log.error("UICommandContainerMixin.__init__ : parent_window n’a pas été fourni.")
        if not hasattr(self, "_tearoff"):
            log.warning(
                "UICommandContainerMixin.__init__ : l'attribut _tearoff est manquant."
            )
        if not isinstance(
            self.__window,
            (
                tk.Tk,
                tk.Frame,
                tk.LabelFrame,
                tk.Menu,
                tkinterdnd2.TkinterDnD.Tk,
            ),
        ) or not issubclass(
            type(self.__window),
            (
                tk.Tk,
                tk.LabelFrame,
                tk.Frame,
                tk.Menu,
                tkinterdnd2.TkinterDnD.Tk,
            ),
        ):
            log.warning(
                f"UICommandContainerMixin.__init__ : parent_window={self.__window.__class__.__name__}(type={type(self.__window)}) doit être de type tk.Tk ou tk.Frame ou tk.Menu!"
            )
        if not isinstance(self, tk.Menu):
            log.warning(
                f"UICommandContainerMixin.__init__ : self={self.__class__.__name__}(type={type(self)}) doit être un menu !"
            )
        if not isinstance(self._tearoff, int):
            log.warning(
                f"UICommandContainerMixin.__init__ : tearoff={self._tearoff}(type={type(self._tearoff)}) doit être un entier !"
            )
        if not (self._tearoff == 0 or self._tearoff == 1):
            log.warning(
                f"UICommandContainerMixin.__init__ : tearoff={self._tearoff} doit être 0 ou 1 !"
            )
        # if isinstance(self.__window, tk.Menu):
        #     log.debug(f"UICommandContainerMixin.__init__ : Crée un menu Tkinter avec tearoff={self._tearoff}.")
        #     tk.Menu.__init__(self, self.__window, tearoff=self._tearoff)
        # else:
        #     log.debug(f"UICommandContainerMixin.__init__ : Crée un menu Tkinter avec tearoff={self._tearoff}.")
        #     tk.Menu.__init__(self, self.__window, tearoff=self._tearoff)
        # if isinstance(self.__window, tk.Menu):
        #     log.debug(f"UICommandContainerMixin.__init__ : Ajoute le menu Tkinter à self._window={self.__window}.")
        #     self.__window.add_cascade(label="Menu", menu=self)  # Label par défaut "Menu"
        # if isinstance(self.__window, (tk.Tk, tk.Frame)):
        #     log.debug(f"UICommandContainerMixin.__init__ : Ajoute le menu Tkinter à self._window={self.__window}.")
        #     self.__window.config(menu=self)  # Définit le menu de la fenêtre principale
        # if not hasattr(self, 'appendUICommand'):
        #     log.warning("UICommandContainerMixin.__init__ : la méthode appendUICommand doit être implémentée par la classe qui utilise ce mixin.")
        # if not hasattr(self, 'add_h_separator'):
        #     log.warning("UICommandContainerMixin.__init__ : la méthode add_h_separator doit être implémentée par la classe qui utilise ce mixin.")
        # if not hasattr(self, 'appendSubMenuWithUICommands'):
        #     log.warning("UICommandContainerMixin.__init__ : la méthode appendSubMenuWithUICommands doit être implémentée par la classe qui utilise ce mixin.")
        # if not hasattr(self, 'subMenu'):
        #     log.debug("UICommandContainerMixin.__init__ : l'attribut subMenu n'existe pas encore.")

    def appendUICommands(self, *uiCommands, **kwargs):
        """Ajout des *uiCommands.

        Cette méthode, qui est mélangée dans une classe de menu,
        prend une liste de UICommand et les ajoute au menu.
        Elle gère également les séparateurs et les sous-menus.

        Args :
            *uiCommands : Instances de UICommand ou tuples pour les sous-menus.
        """
        # if not hasattr(self, "_window") or self.__window is None:
        #     log.warning("UICommandContainerMixin.appendUICommands : l'attribut _window est manquant ou None.")
        #     # return
        #     self.__window = kwargs.get('parent_window', None)
        #     if self.__window is None:
        #         log.error("UICommandContainerMixin.appendUICommands : parent_window n’a pas été fourni dans les kwargs.")
        #         return
        # parent_window = kwargs.get('parent_window', None)
        # if parent_window is None and (not hasattr(self, "_window") or self.__window is None):
        # if self.__window is None or (not hasattr(self, "__window") or self.__window is None):
        # if not hasattr(self, "__window") or self.__window is None:
        #     log.error("UICommandContainerMixin.appendUICommands : parent_window n’a pas été fourni ni en argument, ni dans l'initialisation.")
        #     return  # Pourquoi ne pas utiliser parent_window des kwargs ?

        if not uiCommands:
            log.warning("Aucune UICommand n’a été fournie à appendUICommands.")
            return

        # Ajouter les commandes au menu
        for uiCommand in uiCommands:
            if uiCommand is None:
                # None : Ajoute un séparateur.
                # self.AppendSeparator()
                self.add_separator()
                log.debug(
                    f"UICommandContainerMixin.appendUICommands : ajoute un séparateur dans {self.__class__.__name__}!"
                )
                # self.add_separator()
                # elif isinstance(uiCommand, (str, str)):  # TODO : A convertir ?
                # label = wx.MenuItem(self, text=uiCommand)
                # label = tk.Menu(self, title=uiCommand)
                # must append item before disable to insure
                # that internal object exists
                # self.AppendItem(label)
                # self.add_command(label=uiCommand.MenuText, command=uiCommand)
                # label.Enable(False)
            elif isinstance(uiCommand, tuple):
                # tuple : Crée un sous-menu et y ajoute les commandes UI.
                menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
                log.debug(
                    f"UICommandContainerMixin.appendUICommands : ajoute le sous-menu {menuTitle} avec une liste de commandes {menuUICommands}!"
                )
                self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
            else:
                # Autre (supposé être une instance de UICommand) : ajoute la commande.
                # self.appendUICommand(uiCommand)
                # log.debug(f"UICommandContainerMixin.appendUICommands : ajoute la commande {uiCommand} !")
                try:
                    log.debug(
                        f"UICommandContainerMixin.appendUICommands : ajoute la commande {uiCommand} !"
                    )
                    self.appendUICommand(uiCommand)
                except NotImplementedError:
                    log.error(
                        f"UICommandContainerMixin.appendUICommands : La méthode appendUICommand n'est pas implémentée dans {self.__class__.__name__}."
                    )
                except Exception as e:
                    log.error(
                        f"UICommandContainerMixin.appendUICommands : Erreur lors de l'ajout de la commande {uiCommand}: {e}",
                        exc_info=True,
                    )

            # fileopen_command = uicommand.FileOpen(iocontroller=self._iocontroller)
            # fileopen_command.addToMenu(self, parent_window)

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        """
        Cette méthode crée un nouveau menu Tkinter,
        l'ajoute comme sous-menu au menu actuel,
        puis appelle récursivement subMenu.appendUICommands()
        pour ajouter les commandes au sous-menu.

        Args :
            menuTitle : Nom du sous-menu à créer.
            uiCommands : Liste des commandes à y ajouter.
        """
        # Pour éviter une importation circulaire, nous supposons
        # que la classe Menu est disponible dans taskcoachlib.guitk
        from taskcoachlib.guitk import menutk

        if not hasattr(self, "_window") or self.__window is None:
            log.warning(
                "UICommandContainerMixin.appendSubMenuWithUICommands : l'attribut _window est manquant ou None."
            )
            return
        self.subMenu = menutk.Menu(self.__window, tearoff=0)
        log.warning(
            f"UICommandContainerMixin.appendSubMenuWithUICommands : Crée la sous-menu {self.submenu} à self.__window={self.__window}."
        )
        # self.add_cascade(label=menuTitle, menu=subMenu)
        log.info(
            f"UICommandContainerMixin.appendSubMenuWithUICommands : Ajoute le sous-menu {menuTitle} à self.__window={self.__window}."
        )
        self.subMenu.appendUICommands(*uiCommands)
        self.__window.add_cascade(label=menuTitle, menu=self.subMenu)

    def appendUICommand(self, uiCommand):
        """
        Ajoute une seule commande UI au conteneur.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        raise NotImplementedError(
            "La méthode 'appendUICommand' doit être implémentée par la classe qui utilise ce mixin."
        )

    def add_separator(self):
        # def appendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        # self.add_separator()
        # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, padx=2)  # Ne fonctionne pas directement ici !
        # raise NotImplementedError("La méthode 'AppendSeparator' doit être implémentée par la classe qui utilise ce mixin.")
        # raise NotImplementedError("La méthode 'Add_h_Separator' doit être implémentée par la classe qui utilise ce mixin.")
        if isinstance(self, tk.Menu):
            # self.add_separator()
            super().add_separator()
        else:
            separator = ttk.Separator(self, orient=tk.VERTICAL)
            separator.pack(side=tk.LEFT, padx=2)

    # def add_cascade(self, label, menu):
    #     """
    #     Ajoute un sous-menu.
    #     Cette méthode doit être implémentée par la classe qui utilise ce mixin.
    #     """
    #     # Menu.add_cascade(self, label=label, menu=menu)
    #     from taskcoachlib.guitk import menutk
    #     menutk.Menu.add_cascade(self, label=label, menu=menu)
    #     # raise NotImplementedError("La méthode 'add_cascade' doit être implémentée par la classe qui utilise ce mixin.")

    # Pourquoi c’est vital ?
    # Toutes les UICommand l’utilisent
    # C’est l’équivalent Tkinter de wx.GetTopLevelParent
    def mainWindow(self):
        """
        Retourne la fenêtre Tk principale associée au conteneur.

        Cette méthode est utilisée par les UICommand pour accéder
        à la fenêtre active (focus, sélection, etc.).
        """
        # Si __window est directement la fenêtre Tk, on la retourne
        if isinstance(self.__window, tk.Tk):
            return self.__window  # Fenêtre principale trouvée

        # Si __window est un menu, on remonte récursivement
        if isinstance(self.__window, tk.Menu):
            # Tkinter stocke le parent réel dans master
            parent = getattr(self.__window, "master", None)
            if parent is not None:
                return parent  # Fenêtre ou frame parente

        # Cas d’erreur : rien trouvé
        log.error(
            "UICommandContainerMixin.mainWindow : "
            "impossible de déterminer la fenêtre principale."
        )
        return None


# Pourquoi c’est bien conçu :
# owner permet d’identifier exactement le menu fautif
# Message lisible pour un humain
# Aucun effet secondaire
# Utilisable partout, pas seulement dans les menus
def assert_valid_parent_window(parent_window, owner):
    """
    Vérifie que la fenêtre parente fournie est valide.

    Cette fonction est utilisée pour garantir que tous les menus
    et conteneurs de commandes UI disposent d'une référence correcte
    à la fenêtre principale Tkinter.

    Args:
        parent_window:
            Objet censé représenter la fenêtre principale Tkinter.
        owner:
            Instance ou classe appelante (menu, toolbar, etc.)
            utilisée uniquement pour améliorer les messages de debug.

    Raises:
        AssertionError:
            Si parent_window est None ou n'est pas un objet Tkinter valide.
    """
    # Vérifie l'absence totale de parent_window
    if parent_window is None:
        raise AssertionError(
            f"{owner.__class__.__name__} : parent_window est None. "
            "Chaque menu doit recevoir une référence vers la fenêtre principale Tk."
        )

    # Vérifie que parent_window est un type Tkinter autorisé
    # if not isinstance(parent_window, (tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame, tk.Menu)):
    if not isinstance(
        parent_window, (tk.Tk, tk.Toplevel, tkinterdnd2.TkinterDnD.Tk)
    ):
        raise AssertionError(
            f"{owner.__class__.__name__} : parent_window invalide "
            f"({type(parent_window)}). "
            "Types acceptés : tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame, tk.Menu."
        )
