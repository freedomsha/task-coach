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
"""

# J'ai remplacé les éléments spécifiques à wxPython par leurs équivalents dans tkinter :
#     wx a été remplacé par tkinter.
#
#     wx.EVT_MENU et wx.EVT_UPDATE_UI n'existent pas directement.
#     J'ai utilisé l'option command de tkinter.Menu.add_command et
#     de tkinter.Button pour lier les actions.
#
#     wx.ArtProvider.GetBitmap a été remplacé par une méthode __getBitmap
#     qui suppose l'existence d'une classe ArtProvider pour Tkinter.
#     Tu devras créer cette classe (tkartprovider.py)
#     qui gérera le chargement des icônes (.png, .gif, etc.) en tkinter.PhotoImage.
#
#     Les méthodes bind et unbind ont été retirées
#     car la liaison se fait directement lors de la création du widget.
#
#     J'ai fait quelques ajustements pour que la classe UICommand
#     puisse être utilisée pour créer des boutons de barre d'outils,
#     ce qui correspond à la logique de la méthode appendToToolBar.
#
# Ce code devrait te donner une base solide.
# TODO :
# Il y a quelques points à revoir, notamment la gestion des icônes (tkartprovider.py)
# et la mise à jour des labels de menu.
#
# J'ai mis à jour la méthode mainWindow() pour qu'elle tente d'obtenir
# l'instance de l'application TkinterApplication via une méthode statique getInstance().
# J'ai également importé TkinterApplication pour que la référence soit disponible.
# Ce changement permettra à la classe UICommand d'interagir correctement
# avec la fenêtre principale de l'application, en supposant que le singleton TkinterApplication
# a une référence à MainWindow.
#
# Pour que cela fonctionne, tu devras t'assurer que la classe TkinterApplication
# a une méthode de classe getInstance() qui retourne l'instance unique du singleton,
# et que cette instance a un attribut mainwindow qui référence la fenêtre principale.

# 20/01/2026
# Points Clés et Améliorations Potentielles
# Voici une liste des points à considérer et des améliorations que je vous propose, en m'appuyant sur le code fourni et sur les meilleures pratiques de développement Python :
#
#
# Gestion des Icônes
#
# La gestion des icônes est un point critique. Le code actuel s'appuie sur artprovidertk.py et les fonctions ArtProviderTk.Bitmap() ou artprovidertk.getIcon() 1, 2. Assurez-vous que ce module est bien implémenté et qu'il gère correctement le chargement des images dans différents formats (PNG, GIF, etc.) pour Tkinter.
# Dans la méthode __getBitmap, une gestion d'erreur est présente, mais il serait bon d'avoir une image par défaut en cas d'échec de chargement d'une icône spécifique 1. Vous avez déjà mis en place une solution de repli avec self.__getBitmap("", (16, 16)), ce qui est une bonne chose 3.
# Pensez à la gestion des tailles d'icônes. Tkinter n'a pas de méthode native comme wx.core.ToolBar.GEtToolBitmapSize() 3. Il faudra peut-être adapter les icônes à la taille désirée lors du chargement.
#
#
#
# Gestion des États des Commandes (Activé/Désactivé)
#
# La méthode enabled() est essentielle pour déterminer si une commande peut être exécutée. Elle doit être implémentée correctement dans les sous-classes 4 5.
# La méthode onUpdateUI() est responsable de la mise à jour de l'état des boutons de la barre d'outils et des éléments de menu 6. Assurez-vous qu'elle fonctionne correctement et qu'elle est appelée régulièrement pour refléter l'état actuel de l'application.
# La logique de mise à jour de l'état des boutons dans onUpdateUI et update_ui_binding semble redondante. Unifiez cette logique pour éviter les incohérences 6 7 8.
#
#
#
# Gestion des Menus
#
# La méthode addToMenu() gère l'ajout des commandes aux menus. Elle prend en charge les types de menu "normal", "checkbutton" et "radiobutton" 9.
# Pour les "checkbutton" et "radiobutton", l'utilisation de variables Tkinter (tk.BooleanVar, tk.StringVar) est cruciale pour maintenir l'état de ces éléments 10 11 12. Assurez-vous que ces variables sont correctement liées et mises à jour.
# La méthode removeFromMenu() est un peu délicate car elle recherche l'élément à supprimer par son texte 13. Cela peut être fragile si le texte du menu change. Une meilleure approche serait d'utiliser un identifiant unique pour chaque élément de menu, si possible.
# La gestion de la position (insertion) des éléments de menu est bien gérée 9 14.
# La méthode updateMenuText est marquée comme non implémentée 15. Si vous avez besoin de modifier dynamiquement le texte des menus, il faudra implémenter cette fonctionnalité.
#
#
#
# Gestion de la Barre d'Outils
#
# La méthode appendToToolBar() ajoute les commandes à la barre d'outils. Elle crée un tk.Button pour chaque commande 16.
# La gestion des images pour les boutons de la barre d'outils est similaire à celle des menus. Assurez-vous que les icônes sont chargées correctement et que la taille est appropriée 3.
# Pour les "checkbutton" dans la barre d'outils, le code indique qu'il reste du travail à faire 17. Il faudra implémenter la logique pour gérer l'état de ces boutons.
# La méthode updateToolHelp() gère l'aide contextuelle (tooltips) pour les boutons de la barre d'outils 15.
#
#
#
# Raccourcis Clavier (Accelerators)
#
# La méthode _convert_accelerator() convertit les raccourcis clavier de TaskCoach au format Tkinter 18 19.
# La liaison des raccourcis clavier à la méthode onCommandActivate() est gérée via root.bind_all() 20. Assurez-vous que cela fonctionne correctement et que les raccourcis sont bien activés.
#
#
#
# Gestion des Erreurs et Logs
#
# Le code contient déjà des instructions try...except pour gérer les erreurs potentielles 3 4 7 1. C'est une bonne pratique. Assurez-vous que les erreurs sont correctement loguées pour faciliter le débogage.
# Utilisez le module logging pour enregistrer les événements importants, les erreurs et les avertissements 21. Cela vous aidera à comprendre ce qui se passe dans votre application et à résoudre les problèmes plus facilement.
#
#
#
# Architecture et Conception
#
# La classe UICommand suit le patron Taskmaster, ce qui est une bonne chose 22. Assurez-vous que les sous-classes implémentent correctement la méthode doCommand() 4.
# L'accès à l'instance principale de l'application Tkinter se fait via la méthode mainWindow() et le singleton TkinterApplication 23. C'est une approche raisonnable, mais assurez-vous que le singleton est bien géré et que l'instance de TkinterApplication est toujours disponible.
# Pensez à la modularité et à la réutilisabilité de votre code. Essayez de factoriser le code commun dans des fonctions ou des classes utilitaires pour éviter la duplication.
#
#
# Ce qui a été fait :
#
# Gestion des erreurs améliorée : Ajout de vérifications et de gestion des erreurs pour les cas où les icônes ne peuvent pas être chargées ou lorsque les variables Tkinter sont manquantes pour les checkbuttons et radiobuttons.
# Cohérence de l'état des boutons : Unification de la logique de mise à jour de l'état des boutons dans onUpdateUI et update_ui_binding pour éviter les incohérences.
# Gestion des types de boutons : Amélioration de la gestion des types de boutons (normal, checkbutton, radiobutton) lors de l'ajout aux menus et aux barres d'outils.
# Tooltips : Les tooltips sont gérés avec les méthodes _show_tooltip et _hide_tooltip.
# Ajout des docstrings : Ajout des docstrings manquantes.
#
# Prochaines Étapes
#
# Implémentez les parties TODO : Terminez l'implémentation des "checkbutton" dans la barre d'outils.
# Testez chaque méthode : Testez soigneusement chaque méthode pour vous assurer qu'elle fonctionne comme prévu.
# Documentez le code : Ajoutez des commentaires clairs et concis pour expliquer le fonctionnement du code.
# Revoyez l'architecture : Assurez-vous que l'architecture de votre code est claire et cohérente.

# 20260201 :
# La modification dans toolbarttk.py est claire et appropriée, et le nouveau log montre que l'erreur AttributeError ('NoneType' object has no attribute 'ui_command_id') n'apparaît plus au démarrage.
# Ce que fait exactement votre correctif dans appendUICommand(résumé)
#
# Vous appelez ui_command.appendToToolBar(self) mais vous traitez explicitement le cas où cette méthode renvoie None : vous repérez les nouveaux enfants créés (winfo_children), vous utilisez ui_command._widget si présent, puis vous abandonnez si aucun widget n'est détecté. Voir la logique d'appoint dans ToolBar.appendUICommand 5, 9.
# Vous évitez de vous appuyer uniquement sur l'ajout d'attributs arbitraires sur l'objet widget : si l'affectation widget.ui_command_id échoue, vous tombez sur un mapping interne self._tool_by_id[ui_command.id] = widget (évite les problèmes sur les objets sans dict). Voir la clause try/except et le mapping fallback 9.
# Vous conservez des logs de debug autour de l'appel pour tracer la valeur retournée par appendToToolBar (log.debug("ToolBar.appendUICommand : appendToToolBar(%r) returned %r", ...)) ce qui facilite la traçabilité 9.
#
# Contexte / pourquoi c’était nécessaire
#
# L'erreur d'origine provenait d'un appendToToolBar qui renvoyait None ; le code appelant faisait ensuite button.ui_command_id = ui_command.id sans vérifier que button n'était pas None, provoquant AttributeError — c'est exactement la situation que vous aviez dans les traces précédentes (UICommandContainerMixin.appendUICommands catch de l'exception) 8.
# Le code de base de UICommand.appendToToolBar est censé retourner le bouton/contrôle ; dans votre base_uicommandtk.appendToToolBar la méthode retourne bien le bouton créé (return button) et journalise la fin de l'ajout 10, 7. Mais certaines implémentations de commandes (ou cas "checkbutton pour toolbar" non implémentés) pouvaient retourner None → nécessité d’un traitement côté ToolBar 10, 11.
#
# Preuves dans les fichiers fournis
#
# ToolBar.appendUICommand : logique robuste (détection du widget créé / fallback / mapping).
# UICommand.appendToToolBar : implémentation qui crée et retourne explicitement un tk.Button (retourne button) et journalise la fin de l'ajout.
# UICommandContainerMixin.appendUICommands : c’est l’appelant qui capturait alors l’exception montrée dans votre ancien log ; la trace d’erreur précédente provenait bien de là.
#
# Vérification dans le log fourni
# J’ai cherché dans le log récent (taskcoachlog20260201a.log.txt) : celui-ci contient l’initialisation complète de l’application et la création des composants (MainWindow, viewers, images, colonnes…) sans la trace d’AttributeError que vous aviez auparavant. Exemples d’entrées de démarrage et création d’images/objets : démarrage et analyse d’arguments 1, 2 ; création du viewer et de la liste d’images (PhotoImage) 3, 4. Je n’ai pas trouvé la précédente exception 'NoneType' dans ce log récent, ce qui suggère que le démarrage s’est déroulé sans reproduire l’erreur. Voir notamment les messages de création d’images et viewers qui montrent un démarrage normal 3, 4.
#
# Recommandations (suivantes étapes)
#
# Consolider l’API : idéalement chaque appendToToolBar() doit retourner explicitement le widget créé. Corriger les UICommand qui renvoient None (p.ex. checkbuttons toolbar non implémentés) évitera d’avoir à maintenir des heuristiques côté ToolBar. (base_uicommandtk.appendToToolBar montre le pattern attendu : return button) 10, 7.
# Garder le comportement résilient côté ToolBar tant que toutes les appendToToolBar ne sont pas corrigées : la détection via before/after children + _widget + mapping _tool_by_id est un bon filet de sécurité 5, 9, 6.
# Conserver (au moins temporairement) le log debug autour de l’appel appendToToolBar pour repérer les UICommands problématiques ; le code actuel logge déjà appendToToolBar(%r) returned %r 9. Si vous trouvez des UICommands qui retournent None, corrigez-les pour renvoyer le widget et stocker self._widget si nécessaire.
# Une fois que toutes les UICommands renvoient correctement le widget, envisagez de supprimer la détection heuristique (winfo_children) pour simplifier le code, en gardant uniquement le mapping _tool_by_id si vous voulez éviter d’ajouter des attributs sur les widgets.
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import uuid

from taskcoachlib import operating_system

# from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.guitk.artprovidertk import (
    IconProvider,
    art_provider_tk,
    getIcon,
)
from taskcoachlib.guitk.artprovidertk import (
    ArtProvider,
)  # Assumes you have created this
from taskcoachlib.guitk.artprovidertk import (
    ArtProviderTk,
)  # Assumes you have created this

# from taskcoachlib.application.tkapplication import TkinterApplication

log = logging.getLogger(__name__)

""" User interface commands (subclasses of UICommand) are actions that can
    be invoked by the user via the user interface (menu's, toolbar, etc.).
    See the Taskmaster pattern described here:
    http://www.objectmentor.com/resources/articles/taskmast.pdf
"""  # pylint: disable=W0105


class UICommand(object):
    """
    Commande d'interface utilisateur de base pour Tkinter.

    Une classe pour représenter une commande UI.

    Une UICommand est une action qui peut être associée à des menus ou des barres d'outils.
    Elle contient le texte du menu, l'aide contextuelle à afficher, et gère les événements.
    Les sous-classes doivent implémenter la méthode doCommand() et peuvent
    remplacer enabled() pour personnaliser l'activation des commandes.

    Attributs :
        menuText (str) : Texte du menu.
        helpText (str) : Texte d'aide.
        bitmap (str) : Nom de l'icône à afficher.
        bitmap2 (str) : Nom de l'icône secondaire.
        kind (str) : Type d'élément (normal, checkbutton, etc.).
        id (int) : Identifiant unique pour l'élément.
        toolbar (tk.Frame) : Barre d'outils associée.
        menuItems (list) : Liste des éléments de menu auxquels cette commande est associée.
        app (tk.Tk) : L'instance principale de l'application Tkinter.
    """

    def __init__(
        self,
        menuText="",
        helpText="",
        # bitmap="nobitmap",
        bitmap="",
        kind="normal",
        id=None,
        bitmap2=None,
        is_checked=False,
        *args,
        **kwargs,
    ):  # pylint: disable=W0622
        """
        Initialise la commande d'interface utilisateur.

        Args :
            menuText (str, optionnel) : Le texte à afficher dans le menu. Par défaut à "".
            helpText (str, optionnel) : Le texte d'aide contextuelle. Par défaut à "".
            bitmap (str, optionnel) : L'icône du menu ou de la barre d'outils. Par défaut à "nobitmap".
            kind (wx.ItemKind, optionnel) : Le type d'élément (normal, checkable, etc.). Par défaut à wx.ITEM_NORMAL.
            id (int, optionnel) : L'identifiant de la commande. Si non spécifié, un identifiant unique sera généré.
            bitmap2 (str, optionnel) : Icône secondaire pour les éléments checkables. Par défaut à None.
        """
        super().__init__()
        # Le texte à afficher dans le menu :
        menuText = menuText or f"<{_('None')}>"
        # self.menuText = menuText
        self.menuText = menuText if "&" in menuText else "&" + menuText
        # Le texte d'aide contextuelle :
        self.helpText = helpText
        # Le nom de l'icône :
        self.bitmap = bitmap
        # Nom de l'icône secondaire pour les éléments checkables :
        self.bitmap2 = bitmap2
        # Le type d'élément (normal, checkbutton, radiobutton) :
        self.kind = kind
        # if self.kind is "checkbutton":
        if self.kind == "checkbutton":
            log.debug(
                f"UICommand.__init__ : kind est 'checkbutton' pour {self.menuText}."
            )
            self._variable = (
                tk.BooleanVar()
            )  # Variable Tkinter pour le checkbutton
            # self._variable.set(is_checked := False)  # Initialise l'état à False
            self._variable.set(is_checked)  # Initialise l'état à False
        # L'identifiant de la commande.
        # self.id = id if id is not None else IdProvider.get()
        if id is None:
            self.id = str(uuid.uuid4())  # Génère un UUID par défaut
        else:
            self.id = id  # IdProvider.get() ?
        #
        self._kwargs = kwargs  # Stocke les arguments supplémentaires
        # L'instance principale de l'application Tkinter
        self.app = self.mainWindow()
        self.toolbar = None
        self.menuItems = []

    def __del__(self):
        """Libère l'identifiant lors de la destruction de l'objet."""
        # IdProvider.put(self.id)  # À réactiver si IdProvider est utilisé
        pass

    def __eq__(self, other):
        return self is other

    def uniqueName(self):
        """Retourne le nom unique de la classe de commande."""
        return self.__class__.__name__

    # Le problème : Tkinter n'accepte pas d'option type.
    # Pour créer un "checkbutton" dans un menu,
    # il faut appeler une méthode différente : menu.add_checkbutton().
    # Explication de la correction
    #
    #     Plus d'option type : J'ai supprimé menu_item_options['type'] = 'checkbutton'.
    #
    #     Appel de la bonne méthode : Le code vérifie maintenant self.kind.
    #
    #         Si self.kind == "checkbutton", il utilise menu.add_checkbutton().
    #
    #         Si self.kind == "radiobutton", il utilise menu.add_radiobutton().
    #
    #         Sinon, il utilise menu.add_command().
    #
    #     Variables Tkinter : Pour que les checkbutton et radiobutton fonctionnent,
    #     ils ont besoin d'une variable Tkinter (tk.BooleanVar ou tk.StringVar).
    #     J'ai ajouté la logique pour les lier (vous les aviez déjà définis dans settings_uicommandtk.py,
    #     donc ils devraient être trouvés).
    #
    #     Gestion de la position : J'ai corrigé la logique pour utiliser menu.insert_...()
    #     si une position est donnée, et menu.add_...() sinon.
    # Ne pas utiliser add_to_menu pour être raccord avec le reste de l'application compatible wxpython.
    def addToMenu(self, menu, window, position=None):
        # """ Ajoute un sous-menu au Menu menu.
        """
        Ajoute cette commande à un menu.

        Les paramètres du menu doivent être menuText, HelpText et kind.

        Args :
            menu (tk.Menu) : Le menu parent auquel ajouter la commande.
            window (tk.Tk ou tk.Toplevel) : La fenêtre parente associée.
            position (int, optionnel) : La position dans le menu.
        """
        assert isinstance(
            menu, tk.Menu
        ), f"[BUG] addToMenu() appelé avec un mauvais argument : type(menu) = {type(menu)}"

        log.debug(
            f"💥UICommand.addToMenu essaye d'ajouter le sous-menu {self.menuText} d'ID={self.id} dans le menu {menu} à la position {position}."
        )

        # menu_index = menu.index("end")
        menu_index = 0  # Position initiale remise à 0 !
        # --- Options communes à tous les types ---
        # menu_item_options = {
        #     'label': self.getMenuText(),
        #     'command': self.onCommandActivate,
        # }
        menu_item_options = {
            "label": self.getMenuText(),
            "command": self.onCommandActivate,  # ne pas mettre de parenthèse !
            "state": "normal" if self.enabled() else "disabled",
        }
        log.debug(
            f"UICommand.addToMenu : création de menu_item_options={menu_item_options}."
        )
        # menu_item_options['label'] = self.getMenuText()
        # menu_item_options['command'] = self.onCommandActivate
        # menu_item_options['state'] = 'normal' if self.enabled() else 'disabled'

        # --- Détermination du type de commande ---

        # Cas 1 : cette UICommand représente un sous-menu
        is_submenu = hasattr(self, "getMenu") and callable(self.getMenu)

        # Cas 2 : commande simple
        is_command = not is_submenu

        # --- Sécurité : un menu Tkinter est requis ---
        assert menu is not None, "UICommand.addToMenu : menu est None"
        assert hasattr(
            menu, "add_command"
        ), "UICommand.addToMenu : menu n'est pas un tk.Menu"

        # Accélérateur (texte affiché)
        # Note : 'accelerator' est un attribut défini dans uicommandtk.py
        # if hasattr(self, 'accelerator') and self.accelerator:
        #     menu_item_options['accelerator'] = self.accelerator
        #     shortcut_text

        # Icône
        # # Check for bitmap and add it if available
        # if self.bitmap:
        #     bitmap = self.__getBitmap(self.bitmap)
        #     # bitmap = ArtProviderTk.GetBitmap(self.bitmap, self)
        #     if bitmap:
        #         # Assurez-vous que l'icône est une instance de PhotoImage de Tkinter
        #         menu_item_options['image'] = bitmap
        #         menu_item_options['compound'] = 'left'  # Place l'image à gauche du texte

        # TODO : à revoir une fois la barre de menu bien implémentée !
        # # Cette condition crée un problème : les listes de menu ne s'affichent plus !
        # ❗ Problème fondamental
        # Dans TaskCoach, UICommand est utilisé à la fois pour :
        # des commandes simples (command=...)
        # des menus (File, Edit, View, etc.)
        # des sous-menus dynamiques
        #
        # 👉 Or, un menu Tkinter (tk.Menu) ne doit JAMAIS recevoir :
        # image
        # compound
        # command
        #
        # Ces options sont valides uniquement pour les entrées de menu, pas pour les menus conteneurs.
        # Résultat :
        # Tkinter accepte silencieusement certaines options
        # mais refuse de créer le sous-menu
        # sans lever d’exception claire
        # ⇒ le menu File disparaît
        # C’est exactement ce que tu as observé.
        #
        # Règle Tkinter à respecter (importante) :
        # Un sous-menu (add_cascade) ne doit PAS avoir d’icône
        # Tkinter ne gère les icônes que sur des entrées finales, pas sur les cascades.
        #
        # # --- Gestion des icônes --- # TODO : à décommenter quand le menu sera prêt à avoir des icônes mais pas sur les add_cascade !
        # if is_command:
        #     # Les icônes sont AUTORISÉES pour les commandes simples uniquement
        #     if hasattr(self, 'bitmap') and self.bitmap:
        #         # menu_item_options['image'] = self.bitmap  # Erreur, il faut obtenir l'image ici, le nom ne suffit pas !
        #         try:
        #             # Récupération de l'image Tkinter depuis l'ArtProvider
        #             menu_item_options['image'] = artprovidertk.getIcon(self.bitmap)
        #             # Placement de l'icône à gauche du texte
        #             menu_item_options['compound'] = 'left'  # Place l'icône à gauche du texte
        #         except Exception as e:
        #             # Journalisation sans bloquer l'affichage du menu
        #             log.error(f"UICommand.addToMenu : Erreur lors de la récupération de l'icône '{self.bitmap}' :", exc_info=True)
        #             # menu_item_options['image'] = artprovidertk.getIcon('No icon')
        #
        #         # compound : Cette option est utilisée pour spécifier la position de l'icône
        #         # par rapport au texte. 'left' place l'icône à gauche du texte.
        # else:
        #     # Sécurité explicite : un sous-menu ne doit PAS avoir d'image
        #     assert 'image' not in menu_item_options, (
        #         "UICommand.addToMenu : tentative d'ajout d'une icône à un sous-menu"
        #     )

        # --- Logique spécifique au type ---

        # Déterminer la méthode d'ajout (add ou insert)
        use_insert = position is not None
        if use_insert:
            # L'option 'index' n'est pas un argument standard pour add/insert,
            # nous devons l'utiliser séparément.
            # del menu_item_options['label']  # 'label' est géré par 'index' pour insert
            pass  # La logique d'insertion est gérée ci-dessous

        # add_method = None
        add_method = menu.add_command  # méthode standard si non définit

        # Handle different kinds of menu items
        log.debug(
            f"Vérification de self.kind={self.kind} qui doit être 'normal', 'checkbutton' ou 'radiobutton'"
        )
        if self.kind == "checkbutton":
            # menu_item_options['type'] = 'checkbutton'
            # # You would need a variable to track the state, like a tkinter.BooleanVar
            # # For now, we'll just add the command
            # # TODO: Implement state variable for checkbutton
            # log.warning("Tkinter checkbutton kind not fully implemented, state variable is missing.")
            # Les checkbuttons (de settings_uicommandtk.py) ont un attribut _variable
            if hasattr(self, "_variable") and isinstance(
                self._variable, (tk.BooleanVar, tk.StringVar)
            ):
                menu_item_options["variable"] = self._variable
                log.debug(
                    f"UICommand '{self.menuText}' est un 'checkbutton' avec variable={self._variable}"
                )
                add_method = (
                    menu.insert_checkbutton
                    if use_insert
                    else menu.add_checkbutton
                )
            else:
                log.warning(
                    f"UICommand '{self.menuText}' est 'checkbutton' mais n'a pas de '_variable' Tkinter."
                )
        elif self.kind == "radiobutton":
            # Les radiobuttons (de settings_uicommandtk.py) ont _variable et value
            if hasattr(self, "_variable") and isinstance(
                self._variable, (tk.StringVar, tk.IntVar)
            ):
                menu_item_options["variable"] = self._variable
                # La 'value' est cruciale pour un radiobutton
                if hasattr(self, "value"):
                    menu_item_options["value"] = self.value
                    log.debug(
                        f"UICommand '{self.menuText}' est un 'radiobutton' avec value={self.value}"
                    )
                    add_method = (
                        menu.insert_radiobutton
                        if use_insert
                        else menu.add_radiobutton
                    )
                else:
                    log.error(
                        f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas d'attribut 'value'."
                    )
                    return
            else:
                log.warning(
                    f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas de '_variable' Tkinter."
                )
        elif self.kind == "normal":
            log.debug(f"Add normal Command : {self.menuText}.")
            # self._menu.add_command(
            # self.add_command(
            #     label=menu_text,
            #     command=command_func,
            #     accelerator=shortcut_text,
            #     state=state
            # )
            # add_method = menu.insert_command if use_insert else menu.add_command
            if use_insert:
                add_method = menu.insert_command
                log.debug("Utilisation de menu.insert_command")
            else:
                add_method = menu.add_command
                log.debug("Utilisation de menu.add_command")

        else:  # "normal"
            # add_method = menu.insert_command if use_insert else menu.add_command
            log.debug(f"! self.kind={self.kind} est inconnu !")

        # if position is None:
        #     menu.add_command(**menu_item_options)
        # else:
        #     menu.insert_command(position, **menu_item_options)
        # --- Ajout final ---
        # Ajouter l'élément au menu
        try:
            if use_insert:
                # La méthode insert prend la position comme premier argument
                add_method(position, **menu_item_options)
                menu_index = position
                log.debug(
                    f"Ajout de '{self.menuText}' au menu avec position={position} et options={menu_item_options}"
                )
            elif is_command:
                # Ajouter l'icône
                menu_index = menu.index("end")
                add_method(**menu_item_options)
                log.debug(
                    f"Ajout de '{self.menuText}' au menu {menu} avec options={menu_item_options}"
                )
            elif is_submenu:
                # Tkinter INTERDIT ces options pour add_cascade
                menu_item_options.pop("command", None)
                menu_item_options.pop("image", None)
                menu_item_options.pop("compound", None)
                menu_item_options.pop("state", None)
                # menu.add_cascade(**menu_item_options)
                submenu = self.getMenu()

                assert isinstance(
                    submenu, tk.Menu
                ), "UICommand.addToMenu : getMenu() n'a pas retourné un tk.Menu"

                menu_index = menu.index("end")
                menu.add_cascade(
                    label=menu_item_options["label"], menu=submenu
                )

                log.debug(
                    f"Ajout du sous-menu '{self.menuText}' au menu {menu}"
                )
        except tk.TclError as e:
            log.error(
                f"Erreur Tcl lors de l'ajout de '{self.menuText}' au menu : {e}. Options: {menu_item_options}",
                exc_info=True,
            )
            # pass  # Ne pas planter si une option est mauvaise
            return

        self.menuItems.append(
            # menu
            (
                menu,
                menu_index,
            )
        )  # Stocke la référence au menu. Est-ce nécessaire avec tkinter ? Oui, pour Taskcoach
        log.debug(
            f"Le premier menu de {menu} est {menu.entrycget(0, 'label')}."
        )
        log.debug(
            f"Le menu {menu} est référencé dans {self.menuItems}."
        )  # Est-ce nécessaire avec tkinter ?

    def addBitmapToMenuItem(self, menuItem) -> None:
        """Ignorer! Tkinter gère les icônes directement via les options du menu."""
        pass

    def removeFromMenu(self, menu):
        # Cette méthode est un peu plus complexe avec Tkinter car il n'y a pas
        # d'ID d'élément de menu à proprement parler pour le unbind.
        # Nous pouvons essayer de trouver l'index de l'élément par son texte.
        # TODO: A revoir pour une suppression plus fiable
        for i in range(menu.index("end") + 1):
            try:
                if menu.entrycget(i, "label") == self.getMenuText():
                    menu.delete(i)
                    break
            except tk.TclError:
                # Gérer les erreurs si l'index n'est pas valide
                log.error(
                    f"UICommand.removeFromMenu : l'index n'est pas valide.",
                    stack_info=True,
                )
            if menu in self.menuItems:
                self.menuItems.remove(menu)

    # Explication des vérifications :
    #
    # self.toolbar : Avant d'utiliser self.toolbar, on vérifie s'il est défini et non None. Si ce n'est pas le cas, on affiche une erreur et on retourne None.
    # Chargement de l'image : On encapsule le chargement de l'image dans un bloc try...except pour gérer les erreurs potentielles. Si le chargement échoue, on affiche un message d'avertissement et on continue.
    # Attribut command : On vérifie que l'attribut command est bien défini dans button_options et que sa valeur est une fonction callable.
    # Retour de la méthode : La méthode retourne l'instance du bouton créé.
    # La version de base UICommand.appendToToolBar crée/retourne un tk.Button ; les mixins doivent faire de même (ne jamais retourner None) — voir l’ajout d’un bouton par UICommand dans les logs.
    def appendToToolBar(self, toolbar):
        """
        Ajoute cette commande à une barre d'outils (Frame).

        Crée un tk.Button pour la barre d'outils.

        Args :
            toolbar (tk.Frame) : La barre d'outils à laquelle ajouter la commande.

        Returns :
            (tk.Button) : L'instance du bouton créé.
        """
        #    (int) : L'identifiant de la commande.

        log.debug(
            f"UICommand.appendToToolBar : Début d'ajout de la commande '{self.menuText}' à la barre d'outils."
        )
        # Vérification de l'attribut toolbar
        if not hasattr(self, "toolbar") or toolbar is None:
            log.error(
                f"UICommand.appendToToolBar : L'attribut toolbar n'est pas correctement défini pour la commande '{self.menuText}'."
            )
            return None  # Retourne None si la barre d'outils n'est pas valide

        self.toolbar = toolbar  # Assurez-vous que self.toolbar est défini

        # Load the bitmap
        # the_bitmap = self.__getBitmap(_("No icon"))
        # Tentative de récupération de l'image
        the_bitmap = None
        # bitmap = Image.open(self.image_path)
        # self.normal_image = ImageTk.PhotoImage(bitmap) # Store the normal image
        if hasattr(self, "bitmap") and self.bitmap:
            # the_bitmap = self.__getBitmap(self.bitmap)  # TODO : trouver une alternative à wx.core.ToolBar.GEtToolBitmapSize()
            try:
                the_bitmap = self.__getBitmap(self.bitmap)
                # Vérification du chargement de l'image
                if the_bitmap is None:
                    log.warning(
                        f"UICommand.appendToToolBar : L'image '{self.bitmap}' n'a pas pu être chargée pour la commande '{self.menuText}'."
                    )
                    the_bitmap = self.__getBitmap(
                        "", (16, 16)
                    )  # Image vide par défaut
            except Exception as e:
                log.error(
                    f"UICommand.appendToToolBar : Erreur lors du chargement de l'image '{self.bitmap}' pour la commande '{self.menuText}': {e}"
                )
                the_bitmap = self.__getBitmap("")  # Image vide par défaut

        # # Si l'image spécifique échoue, on tente l'image par défaut
        # if not the_bitmap:
        #     # the_bitmap = self.__getBitmap(_("No icon"))
        #     the_bitmap = self.__getBitmap("")

        # # Create a disabled version (e.g., grayscale)
        # # Création de la version désactivée (par exemple en niveaux de gris)
        # disabled_image = the_bitmap.convert('L')  # Convert to grayscale
        # self.disabled_image = ImageTk.PhotoImage(disabled_image)  # Store the disabled image

        # button = ttk.Button(toolbar,
        #                     # image=self.normal_image,  # Use the normal image initially
        #                     state=tk.NORMAL,        # Start as enabled
        #                     command=self.do_command,
        #                     # compound=tk.TOP          # To put image above text
        #                     )
        button_options = {
            # 'image': the_bitmap,
            # image=self.normal_image,  # Use the normal image initially  # TODO
            # 'state': tk.NORMAL,        # Start as enabled
            "command": self.onCommandActivate,  # ou self.doCommand ?  # TODO
            "bd": 0,
            "relief": "flat",
            "padx": 5,
            "pady": 5,
            # compound=tk.TOP          # To put image above text
            "state": (
                tk.NORMAL if self.enabled() else tk.DISABLED
            ),  # Initialise l'état du bouton
        }

        # Si on a une image, on l'utilise. Sinon, on met du texte.
        if the_bitmap:
            button_options["image"] = the_bitmap
        else:
            # Fallback : Utiliser le texte du menu ou un point d'interrogation
            text_label = self.getMenuText()
            # On nettoie le texte (retirer les raccourcis clavier ex: "New\tCtrl+N")
            if "\t" in text_label:
                text_label = text_label.split("\t")[0]
            button_options["text"] = text_label if text_label else "??"
            # Optionnel : ajouter compound si on veut gérer texte et image
            # button_options['compound'] = tk.LEFT

        if self.kind == "checkbutton":
            # Pour un checkbutton, on utiliserait tk.Checkbutton avec indicatoron=0
            # Les checkbuttons (de settings_uicommandtk.py) ont un attribut _variable
            log.debug(
                "UICommand.appendToToolBar : création d'un Checkbutton pour '%s'.",
                self.menuText,
            )
            # Variable Tkinter existante : self._variable (définie dans init si kind == "checkbutton")
            # if hasattr(self, '_variable') and isinstance(self._variable, (tk.BooleanVar, tk.StringVar)):
            if not hasattr(self, "_variable") or not isinstance(
                self._variable, (tk.BooleanVar, tk.StringVar, tk.IntVar)
            ):
                self._variable = tk.BooleanVar(
                    value=bool(getattr(self, "_is_checked", False))
                )

            # Crée un Checkbutton sans indicateur (bouton visuel)
            btn = tk.Checkbutton(
                toolbar,
                text=self.getMenuText(),
                variable=self._variable,
                indicatoron=0,  # 0 = bouton "toggle"
                command=self.onCommandActivate,
                bd=0,
                relief="flat",
                padx=5,
                pady=2,
            )
            btn.pack(side="left", padx=2, pady=2)
            self._widget = btn
            self._kwargs["button"] = btn
            log.debug(
                "UICommand.appendToToolBar : Checkbutton créé pour '%s' -> %r",
                self.menuText,
                btn,
            )
            return btn
            # Explication : cela évite le retour None et respecte la liaison variable ↔ état du Checkbutton.
        elif self.kind == "radiobutton":
            # Les radiobuttons (de settings_uicommandtk.py) ont _variable et value
            log.debug(
                "TaskViewerTreeOrListChoice.appendToToolBar : création du contrôle de choix"
            )
            # if hasattr(self, '_variable') and isinstance(self._variable, (tk.StringVar, tk.IntVar)):
            if not hasattr(self, "_variable") or not isinstance(
                self._variable, (tk.BooleanVar, tk.StringVar, tk.IntVar)
            ):
                # self._var = tk.StringVar(value=self.default_value)
                self._variable = tk.StringVar(
                    value=getattr(self, "_is_checked", self.default_value)
                )
            #     menu_item_options['variable'] = self._variable
            #     # La 'value' est cruciale pour un radiobutton
            #     if hasattr(self, 'value'):
            #         menu_item_options['value'] = self.value
            #         log.debug(f"UICommand '{self.menuText}' est un 'radiobutton' avec value={self.value}")
            #         add_method = menu.insert_radiobutton if use_insert else menu.add_radiobutton
            #     else:
            #         log.error(f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas d'attribut 'value'.")
            #         return
            # else:
            #     log.warning(f"UICommand '{self.menuText}' est 'radiobutton' mais n'a pas de '_variable' Tkinter.")
            combo = ttk.Combobox(
                toolbar,
                textvariable=self._var,
                values=self.choices,
                width=max(6, max(len(c) for c in self.choices)),
            )
            combo.bind(
                "<<ComboboxSelected>>", lambda e: self.onChoiceChanged()
            )
            combo.pack(side="left", padx=2, pady=2)
            self._widget = combo
            self._kwargs["button"] = combo
            return combo

        # Vérification de l'attribut command
        if "command" not in button_options or not callable(
            button_options["command"]
        ):
            log.error(
                f"UICommand.appendToToolBar : L'attribut command n'est pas correctement défini ou n'est pas callable pour la commande '{self.menuText}'."
            )
            return None

        # if the_bitmap:
        #     button = tk.Button(toolbar, **button_options)  # TODO : la variante quand le bouton est grisé
        #     button.image = the_bitmap
        #     button.pack(side="left", padx=2, pady=2)  # ou (padx, padx)=(2,2)
        #     # Stocke le bouton pour la gestion de l'état
        #     self._kwargs['button'] = button
        #     log.debug(f"UICommand.appendToToolBar : le bouton {button.__class__.__name__} avec les options {button_options} a été ajouté à la toolbar {toolbar.__class__.__name__}.")

        # Création du bouton (qu'il y ait une image ou non)
        log.debug(
            "UICommand.appendToToolBar : Création du bouton avec les options : "
        )
        log.debug(f"{button_options} dans la toolbar {toolbar}.")
        button = tk.Button(toolbar, **button_options)

        # Important : Garder une référence à l'image pour éviter le Garbage Collector
        if the_bitmap:
            button.image = the_bitmap

        # button.pack(side=tk.LEFT, padx=1, pady=1)  # Pack the button into the toolbar
        button.pack(side="left", padx=2, pady=2)

        # Stocke le bouton pour la gestion de l'état (enable/disable)
        self._kwargs["button"] = button

        log.debug(
            f"UICommand.appendToToolBar : Bouton créé pour '{self.menuText}' (Icone trouvée: {bool(the_bitmap)})"
        )

        # TODO : Lier l'action du button !
        # Avec ces changements, le bouton sera :
        #     Fonctionnel via l'attribut command lors du clic.
        #     Activable via le raccourci clavier.
        #     Mis à jour dynamiquement (activé/désactivé) par la boucle onUpdateUI.
        # toolbar.bind(self, self.id)
        # Remplacé par :
        self.update_ui_binding()  # Démarre la boucle de mise à jour de l'UI

        # Retour de la méthode
        log.debug(
            f"UICommand.appendToToolBar : Fin d'ajout de la commande '{self.menuText}' à la barre d'outils. Retourne l'instance du bouton."
        )
        # return self.id
        return button  # Return the button instance. Retourne l'instance du bouton créé

    def onCommandActivate(self, event=None):
        """
        Active la commande.
        """
        log.info(
            f"UICommand.onCommandActivate appelée pour {self.menuText} avec event={event}."
        )
        if self.enabled(event):
            try:
                # return self.doCommand(event)
                return self.doCommand()
            except Exception as e:
                log.error(
                    f"UICommand.onCommandActivate : Error executing command: {e}",
                    exc_info=True,
                )
                messagebox.showerror(
                    "Error",
                    f"UICommand.onCommandActivate : An error occurred: {e}",
                )
        else:
            log.warning(
                f"Commande {self.menuText} désactivée, donc doCommand n'est pas appelée."
            )
            return None

    def __call__(self, *args, **kwargs):
        self.onCommandActivate()

    def doCommand(self):
        """
        Méthode à implémenter dans les sous-classes pour exécuter la commande.
        """
        raise NotImplementedError  # pragma: no cover

    # def enabled(self):
    def enabled(self, event=None):
        """
        Détermine si la commande est activée.

        Peut être remplacé dans une sous-classe.

        Args:
            event: L'événement qui a déclenché la vérification (non utilisé
                   dans la classe de base, mais requis pour la compatibilité
                   avec les sous-classes et mixins).

        Returns :
            (bool) : True si la commande est activée, sinon False.
        """
        # return True
        # # Cette correction est indispensable en Tk, wx ne posait pas ce problème.:
        # try:
        #     window_with_focus = self.mainWindow().focus_get()
        # except KeyError:
        #     # Le focus est sur un widget virtuel (menu en construction)
        #     return False
        #
        # if window_with_focus is None:
        #     return False
        #
        # return super().enabled(event)
        main_window = self.mainWindow()  # Récupère la fenêtre principale
        if not main_window:
            # Fenêtre pas encore prête → on désactive la commande
            return False
            # À utiliser seulement si la commande n’est pas dangereuse.:
            # return True  # autoriser pendant l'initialisation

        if event is None:
            # window_with_focus = main_window.focus_get()  # KeyError: '#!mainmenu'
            window_with_focus = self._safe_focus_get(
                main_window
            )  # Focus sécurisé
        else:
            window_with_focus = event
            log.warning(
                f"UICommand.enabled : window_with_focus = event = {window_with_focus}."
            )
        if not window_with_focus:
            return False

        # Log pour voir à quel moment la fenêtre devient disponible.
        # log.debug("enabled(): mainWindow=%r", self.mainWindow())

        # return self.enabled(window_with_focus)
        return True  # À n’utiliser que temporairement.

    # def bind(self):
    #     """
    #     Lie les raccourcis clavier (accelerators) et les événements de mise à jour de l'UI.
    #     """
    #     # 1. Liaison du Raccourci Clavier
    #     if hasattr(self, 'accelerator') and self.accelerator:
    #         try:
    #             # Convertir l'accélérateur Task Coach/wxPython (ex: "Ctrl+N") en format Tkinter (ex: "<Control-n>")
    #             tk_accelerator = self._convert_accelerator(self.accelerator)
    #
    #             # Récupérer la fenêtre racine (root) de l'application
    #             # root = self._getWindowRoot()
    #             root = self.mainWindow()
    #
    #             if root and tk_accelerator:
    #                 # Lier l'événement à la méthode onCommandActivate
    #                 # bind_all lie l'événement à n'importe quel widget de l'application.
    #                 root.bind_all(tk_accelerator, lambda event: self.onCommandActivate())
    #                 log.debug(f"UICommand.bind() : Raccourci lié : {self.accelerator} -> {tk_accelerator}")
    #
    #         except Exception as e:
    #             log.error(f"Erreur lors de la liaison de l'accélérateur '{self.accelerator}' : {e}")
    #
    #     # # 2. Mise en place de la mise à jour de l'UI (voir section suivante)
    #     # self.update_ui_binding()
    #     # 2. Démarrage de la boucle de Mise à Jour de l'UI
    #     # On appelle une première fois onUpdateUI, qui se rappellera lui-même périodiquement.
    #     self.onUpdateUI()

    def _convert_accelerator(self, accelerator_str):
        """
        Convertit une chaîne d'accélérateur de Task Coach (ex: "Ctrl+N") en format Tkinter (ex: "<Control-n>").
        """
        # Remplace les mots-clés
        mapping = {
            "Ctrl+": "Control-",
            "Shift+": "Shift-",
            "Alt+": "Alt-",
            "Del": "Delete",
            "Space": "space",
            # Ajouter d'autres mappings au besoin
        }

        tk_accel = accelerator_str
        for old, new in mapping.items():
            tk_accel = tk_accel.replace(old, new)

        # # Ajoute les chevrons Tkinter et met la dernière lettre en minuscule
        # if tk_accel.startswith(('<', '[')): # Si déjà formaté
        #     return tk_accel
        #
        # parts = tk_accel.split('-')
        # last_part = parts[-1]
        #
        # if len(parts) > 1:
        #     # Reconstruit la chaîne avec la dernière partie en minuscule
        #     tk_accel = "".join(parts[:-1]) + last_part.lower()
        # else:
        #     tk_accel = tk_accel.lower()

        # Met la dernière partie en minuscule (ex: Control-N -> Control-n)
        parts = tk_accel.split("-")
        if parts and parts[-1]:
            parts[-1] = parts[-1].lower()
        tk_accel = "-".join(parts)

        return f"<{tk_accel}>"

    def onUpdateUI(self, event=None) -> None:
        """Met à jour l'état d'activation du widget Tkinter."""
        # Récupère le bouton de la toolbar associé à la commande s'il existe
        button = self._kwargs.get("button")

        # # Vérifie si la commande est activée
        # is_enabled = bool(self.enabled(event))
        #
        # # Met à jour l'état du bouton de la toolbar s'il existe
        # if button and isinstance(button, tk.Button):
        #     button.configure(state='normal' if is_enabled else 'disabled')
        #
        # # Met à jour les éléments de menu associés
        # for menu in self.menuItems:
        #     if isinstance(menu, tk.Menu):
        #         for i in range(menu.index('end') + 1):
        #             try:
        #                 if menu.entrycget(i, 'label') == self.getMenuText():
        #                     menu.entryconfigure(i, state='normal' if is_enabled else 'disabled')
        #             except tk.TclError:
        #                 continue
        #
        # # Met à jour l'aide de la toolbar si nécessaire
        # if self.toolbar and (not self.helpText or self.menuText == "?"):
        #     self.updateToolHelp()

        if button:
            try:
                # 2. Vérifie si la commande peut s'exécuter
                # enabled = self.canExecute()
                enabled = bool(self.enabled(event))

                # 3. Met à jour l'état du bouton si nécessaire
                if enabled and button["state"] == tk.DISABLED:
                    button["state"] = tk.NORMAL
                elif not enabled and button["state"] == tk.NORMAL:
                    button["state"] = tk.DISABLED

            except Exception as e:
                # Log l'erreur mais continue la boucle de rafraîchissement
                logging.error(
                    f"Erreur dans onUpdateUI pour {self.uniqueName()}: {e}"
                )

            # 4. Planifie la prochaine vérification (ex: toutes les 250 ms)
            if self.toolbar and self.toolbar.winfo_exists():
                self.toolbar.after(250, self.onUpdateUI)

    def update_ui_binding(self):
        """
        Met en place la boucle de rafraîchissement pour l'état du bouton.
        """
        # Récupère le bouton créé (stocké dans le constructeur appendToToolBar)
        button = self._kwargs.get("button")

        if button:
            # On vérifie si la commande devrait être activée ou désactivée
            # enabled = self.canExecute()  # canExecute() n'existe pas !
            enabled = self.enabled()  # Utiliser self.enabled() directement

            # On met à jour l'état du bouton
            if enabled and button["state"] == tk.DISABLED:
                button["state"] = tk.NORMAL
            elif not enabled and button["state"] == tk.NORMAL:
                button["state"] = tk.DISABLED

            # On planifie la prochaine vérification (par exemple, toutes les 500 ms)
            # On suppose que `self.toolbar` (le parent) est un widget valide
            # if self.toolbar:
            if self.toolbar and self.toolbar.winfo_exists():
                # `after` est la méthode Tkinter standard pour les appels différés
                self.toolbar.after(500, self.update_ui_binding)

    def updateMenuText(self, menuText):
        self.menuText = menuText
        # Tkinter ne gère pas la mise à jour automatique des labels de menu.
        # Il faudrait recréer le menu ou trouver l'index de l'élément pour le configurer.
        # Pour simplifier, nous ne gérons pas cette fonctionnalité pour l'instant.
        log.warning("Tkinter updateMenuText is not fully implemented.")

    def updateToolHelp(self):
        """Met à jour l'aide contextuelle de la barre d'outils."""
        if not self.toolbar:
            return  # Not attached to a toolbar or it's hidden

        button = self._kwargs.get("button")
        if not button:
            return

        # Met à jour l'aide courte (tooltip)
        short_help = self.getMenuText()
        if hasattr(button, "_short_help") and button._short_help != short_help:
            button._short_help = short_help
            button.bind("<Enter>", lambda e: self._show_tooltip(e, short_help))
            button.bind("<Leave>", lambda e: self._hide_tooltip(e))

        # Met à jour l'aide longue
        long_help = self.getHelpText()
        if hasattr(button, "_long_help") and button._long_help != long_help:
            button._long_help = long_help

    def _show_tooltip(self, event, text):
        """Affiche un tooltip avec le texte donné."""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25

        # Détruit le tooltip existant s'il y en a un
        self._hide_tooltip(event)

        # Crée le tooltip
        tooltip = tk.Toplevel(event.widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tooltip,
            text=text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
        )
        label.pack()

        # Stocke la référence au tooltip
        event.widget._tooltip = tooltip

    def _hide_tooltip(self, event):
        """Cache le tooltip."""
        widget = event.widget
        if hasattr(widget, "_tooltip"):
            widget._tooltip.destroy()
            del widget._tooltip

    def mainWindow(self):
        """
        Retourne l'instance principale de l'application Tkinter.

        Cette méthode utilise le singleton TkinterApplication pour obtenir
        une référence à la fenêtre principale (MainWindow).
        """
        # Cela suppose que l'instance de Tkinter a été créée ailleurs et est accessible
        # via un moyen global ou un singleton.
        # Pour l'instant, on suppose qu'il y a une instance de la classe TkinterApplication
        # quelque part. On pourrait aussi passer l'instance de root en argument.
        # TODO: Assurer l'accès à l'instance de root
        # return None  # tk.Tk()
        from taskcoachlib.application.tkapplication import TkinterApplication

        try:
            app_instance = TkinterApplication.getInstance()
            # app_instance = taskcoachlib.application.tkapplication.TkinterApplication.getInstance()
            # app_instance = app.getInstance()
            if hasattr(app_instance, "mainwindow"):
                return app_instance.mainwindow
            return None
        except Exception:
            return None

    def getMenuText(self):
        """Retourne le texte du menu."""
        return self.menuText

    def getHelpText(self):
        """Retourne le texte d'aide."""
        return self.helpText

    def __getBitmap(self, bitmapName, bitmapSize=(16, 16)):
        """
        Obtient une icône à partir du nom spécifié en utilisant tkartprovider.

        Args :
            bitmapName (str) : Le nom de l'icône.
            bitmapSize (tuple, optionnel) : La taille de l'icône. Par défaut à (16, 16).

        Returns :
            (tk.PhotoImage) : L'icône PhotoImage obtenue, ou None en cas d'erreur.
        """
        log.debug(
            f"UICommand.__getBitmap() appelé avec self={self}, self.uniqueName={self.uniqueName()} bitmapName={bitmapName}"
        )
        try:
            # On suppose ici que tkartprovider.py est une version de ArtProvider pour Tkinter
            # qui peut charger des images.
            # return ArtProvider.getPhotoImage(bitmapName)
            # return ArtProviderTk.GetBitmap(bitmapName)
            return artprovidertk.getIcon(bitmapName, bitmapSize)
            # return artprovidertk.ArtProvider.CreateBitmap(bitmapName, bitmapSize)
        except Exception as e:
            # print(f"UICommand.__getBitmap : Error getting bitmap: {e}")
            logging.error(
                f"UICommand.__getBitmap : Error loading bitmap '{bitmapName}': {str(e)}"
            )
            # raise FileNotFoundError(f"Bitmap '{bitmapName}' not found")
            return None

    def _safe_focus_get(self, main_window):
        """
        Retourne le widget ayant le focus de manière sécurisée.

        Tkinter peut lever un KeyError si le focus est sur un menu
        (ex: '#!mainmenu') ou sur un widget détruit.

        :param main_window: fenêtre principale Tk (Tk ou TkinterDnD.Tk)
        :return: widget Tk ou None si le focus est invalide
        """
        try:
            # Tente de récupérer le widget ayant le focus
            return main_window.focus_get()
        except KeyError:
            # Cas classique : focus sur un menu Tk
            return None
        except Exception:
            # Protection maximale contre tout état incohérent
            return None

    def _ensure_toolwidget(self, toolbar, widget):
        """
        Utilisez ce helper en fin d’appendToToolBar
        (ou appelez-le depuis ToolBar.appendUICommand au besoin).

        Args:
            toolbar:
            widget:

        Returns:

        """
        if widget is None:
            widget = getattr(self, "_widget", None)
        if widget is None:
            # fallback : bouton texte simple
            btn = tk.Button(
                toolbar,
                text=self.getMenuText(),
                command=self.onCommandActivate,
            )
            btn.pack(side="left", padx=2, pady=2)
            self._widget = btn
            self._kwargs["button"] = btn
            log.warning(
                "UICommand._ensure_toolwidget : appendToToolBar n'a pas retourné de widget ; fallback créé pour %r",
                self,
            )
            return btn
        # normal : on stocke la référence au widget si besoin
        self._widget = widget
        self._kwargs["button"] = widget
        return widget
