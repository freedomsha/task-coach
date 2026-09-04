# -*- coding: utf-8 -*-

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

Vous devez spécifier les classes de mixin avant les autres classes.
"""

# Analyse et Compléments potentiels :
#
#
# En-tête et Licence : L'en-tête du fichier est correct et inclut les informations de copyright et la licence GPL.
#
#
# Imports : Les imports de modules logging, tkinter et des modules de domaine (task, note, category, effort, attachment) sont corrects 2.
#
#
# Classes Mixin existantes :
#
# NeedsSelectionMixin 2 : Gère l'état activé/désactivé des commandes nécessitant une sélection.
# NeedsSelectedCategorizableMixin 2 : Pour les commandes nécessitant un élément catégorisé sélectionné (tâche ou note).
# NeedsOneSelectedItemMixin 3 : Pour les commandes nécessitant exactement un élément sélectionné.
# NeedsSelectedCompositeMixin 3 : Pour les commandes nécessitant un élément composite sélectionné (tâche, note ou catégorie).
# NeedsOneSelectedCompositeItemMixin 3 : Combinaison des mixins NeedsOneSelectedItemMixin et NeedsSelectedCompositeMixin.
# NeedsAttachmentViewerMixin 4 : Pour les commandes nécessitant une visionneuse de pièces jointes.
# NeedsSelectedTasksMixin 4 : Pour les commandes nécessitant une ou plusieurs tâches sélectionnées.
# NeedsSelectedNoteOwnersMixin 4 : Pour les commandes nécessitant un propriétaire de note sélectionné (tâche, catégorie ou pièce jointe).
# NeedsSelectedNoteOwnersMixinWithNotes 5 : Pour les commandes nécessitant un propriétaire de note sélectionné avec des notes.
# NeedsSelectedAttachmentOwnersMixin 5 : Pour les commandes nécessitant un propriétaire de pièce jointe sélectionné (tâche, catégorie ou note).
# NeedsOneSelectedTaskMixin 6 : Combinaison des mixins NeedsSelectedTasksMixin et NeedsOneSelectedItemMixin.
# NeedsSelectionWithAttachmentsMixin 6 : Pour les commandes nécessitant un élément sélectionné avec des pièces jointes.
# NeedsSelectedEffortMixin 7 : Pour les commandes nécessitant un effort sélectionné.
# NeedsSelectedAttachmentsMixin 7 : Pour les commandes nécessitant une pièce jointe sélectionnée.
# NeedsAtLeastOneTaskMixin 7 : Pour les commandes nécessitant au moins une tâche.
# NeedsAtLeastOneCategoryMixin 8 : Pour les commandes nécessitant au moins une catégorie.
# NeedsItemsMixin 8 : Pour les commandes nécessitant au moins un élément dans la visionneuse.
# NeedsTreeViewerMixin 8 : Pour les commandes nécessitant une visionneuse d'arborescence.
# NeedsDeletedItemsMixin 9 : Pour les commandes nécessitant des éléments supprimés.
# PopupButtonMixin 10 : Pour l'implémentation de menu contextuel.
#
#
#
# Remarques Importantes
#
# L'argument event est rendu optionnel pour la compatibilité Tkinter 2.
# La classe PopupButtonMixin a été adaptée pour Tkinter 11. L'implémentation utilise tk.Menu pour les menus contextuels et calcule la position du menu en fonction de la position du widget 11 10. La méthode createPopupMenu doit être implémentée par la classe qui utilise ce mixin 12.
#
#
#
# Vérification et Améliorations Potentielles :
#
# Gestion des erreurs : Dans PopupButtonMixin, la gestion des erreurs tk.TclError lors de l'affichage du menu est bien présente 13 14.
# Méthodes Abstraites : La méthode createPopupMenu est définie comme NotImplementedError, ce qui force les classes héritantes à l'implémenter 15 16. C'est une bonne pratique.
#
# Complétude :
# Le fichier semble couvrir un large éventail de cas d'utilisation pour les commandes d'interface utilisateur dans TaskCoach. Les mixins fournissent des fonctionnalités pour gérer la sélection, le type d'élément sélectionné, la présence de pièces jointes, etc.
# Avant de considérer ce fichier comme "définitif", je vous recommande de :
#
# Tester chaque mixin dans le contexte de votre application TaskCoach migrée vers Tkinter.
# Vérifier si d'autres mixins wxPython dans votre code source n'ont pas été transposés ici.
# Documenter chaque mixin avec des exemples d'utilisation pour faciliter la maintenance future.

# from builtins import object
import logging
from taskcoachlib.domain import task, note, category, effort, attachment
import tkinter as tk  # Remplacer 'wx' par 'tkinter'
from tkinter import ttk

log = logging.getLogger(__name__)


class ViewerRequiredMixin:
    """
    Mixin assurant que la visionneuse fournie est compatible.

    Ne lève jamais d'exception bloquante pour l'interface.
    """

    def _assert_viewer_api(self, *methods):
        """
        Vérifie que la visionneuse expose les méthodes attendues.

        Log un warning si ce n'est pas le cas.
        """
        viewer = getattr(self, "viewer", None)

        # Aucun viewer → on désactive la commande
        if viewer is None:
            log.debug("UICommand sans viewer : commande désactivée.")
            return False

        for method in methods:
            if not hasattr(viewer, method):
                log.warning(
                    "UICommand '%s' : méthode manquante '%s' sur %s",
                    self.__class__.__name__,
                    method,
                    type(viewer).__name__,
                )
                return False

        return True


# Quels sont ces types de classes ? Mixin
# class NeedsSelectionMixin:
# class NeedsSelectionMixin(object):
class NeedsSelectionMixin(ViewerRequiredMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné."""

    def enabled(
        self, event=None
    ):  # L'argument `event` est rendu optionnel pour la compatibilité Tkinter
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselection"):
            return False

        # Comportement normal
        return super().enabled(event) and self.viewer.curselection()


class NeedsSelectedCategorizableMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un catégorisable sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(note.Note)
        )


class NeedsOneSelectedItemMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur qui nécessitent exactement un élément sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselection"):
            return False

        # Comportement normal
        return super().enabled(event) and len(self.viewer.curselection()) == 1


class NeedsSelectedCompositeMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément composite
    sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(note.Note)
            or self.viewer.curselectionIsInstanceOf(category.Category)
        )


class NeedsOneSelectedCompositeItemMixin(
    NeedsOneSelectedItemMixin, NeedsSelectedCompositeMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent exactement un élément composite sélectionné."""

    pass


class NeedsAttachmentViewerMixin(object):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant une visionneuse affichant les pièces jointes."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("isShowingAttachments"):
            return False

        # Comportement normal
        return super().enabled(event) and self.viewer.isShowingAttachments()


class NeedsSelectedTasksMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant une ou plusieurs tâches sélectionnées."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        log.debug(
            f"NeedsSelectedTasksMixin.enabled : retourne {super()}.enabled() et {self.viewer}.curselectionIsInstanceOf() !"
        )
        return super().enabled(event) and self.viewer.curselectionIsInstanceOf(
            task.Task
        )


class NeedsSelectedNoteOwnersMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de note sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(category.Category)
            or self.viewer.curselectionIsInstanceOf(attachment.Attachment)
        )


class NeedsSelectedNoteOwnersMixinWithNotes(NeedsSelectedNoteOwnersMixin):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins un propriétaire de note sélectionné
    avec des notes."""

    def enabled(self, event=None):
        # pylint: disable=E1101
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselection"):
            return False

        # Comportement normal
        return super().enabled(event) and any(
            [item.notes() for item in self.viewer.curselection()]
        )


class NeedsSelectedAttachmentOwnersMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de pièce jointe sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(category.Category)
            or self.viewer.curselectionIsInstanceOf(note.Note)
        )


class NeedsOneSelectedTaskMixin(
    NeedsSelectedTasksMixin, NeedsOneSelectedItemMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins une tâche sélectionnée."""

    pass


class NeedsSelectionWithAttachmentsMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné avec
    une ou plusieurs pièces jointes."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselection"):
            return False

        # Comportement normal
        return super().enabled(event) and any(
            item.attachments()
            for item in self.viewer.curselection()
            if not isinstance(item, effort.Effort)
        )


class NeedsSelectedEffortMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un effort sélectionné."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("curselectionIsInstanceOf"):
            return False

        # Comportement normal
        return super().enabled(event) and self.viewer.curselectionIsInstanceOf(
            effort.Effort
        )


class NeedsSelectedAttachmentsMixin(
    NeedsAttachmentViewerMixin, NeedsSelectionMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins une pièce jointe sélectionnée
    ."""

    pass


class NeedsAtLeastOneTaskMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une tâche."""

    def enabled(self, event=None):  # pylint: disable=W0613
        return len(self.taskList) > 0


class NeedsAtLeastOneCategoryMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une catégorie."""

    def enabled(self, event=None):  # pylint: disable=W0613
        return len(self.categories) > 0


# class NeedsItemsMixin(object):
class NeedsItemsMixin(ViewerRequiredMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément dans leur visionneuse."""

    def enabled(self, event=None):  # pylint: disable=W0613
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("size"):
            return False

        # Comportement normal
        return self.viewer.size()


# class NeedsTreeViewerMixin(object):
class NeedsTreeViewerMixin(ViewerRequiredMixin):
    """Classe Mixin pour les commandes d'interface utilisateur
    nécessitant une visionneuse d'arborescence.
    """

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("isTreeViewer"):
            return False

        # Comportement normal
        return super().enabled(event) and self.viewer.isTreeViewer()


# class NeedsDeletedItemsMixin(object):
class NeedsDeletedItemsMixin(ViewerRequiredMixin):
    """Classe Mixin pour les commandes d’interface utilisateur qui nécessitent la présence d’éléments supprimés."""

    def enabled(self, event=None):
        """
        Indique si la commande est activable.
        """
        # Vérification douce de l'API attendue
        if not self._assert_viewer_api("hasDeletedItems"):
            return False

        # Comportement normal
        return super().enabled(event) and self.iocontroller.hasDeletedItems()


# --- PopupButtonMixin a été omis car il utilise des fonctionnalités wxPython qui n'ont pas d'équivalent direct dans Tkinter ---
# Le code ci-dessous est commenté pour l'instant. L'implémentation d'un PopupButton nécessiterait une approche
# complètement différente dans Tkinter, en utilisant des menus de type 'Menu'.
# C'est le cas !
# TODO : remplacer les fonction wx par des version tk !
# Le mixin wxPython que vous montrez est conçu pour être ajouté à un objet (probablement un contrôleur d'événement)
# qui gère un bouton de barre d'outils.
# Il calcule ensuite où afficher un menu contextuel (juste en dessous de la barre d'outils) lorsque la commande est exécutée.
#
# En tkinter, l'approche est un peu différente et, à mon avis, plus directe.
# Nous allons créer un mixin qui sera mélangé directement avec le widget tkinter lui-même (comme un tk.Button ou tk.Menubutton).
# Résumé des changements :
#
#     Héritage direct : Le mixin est utilisé directement par la classe du bouton (MyToolbarButton(tk.Button, PopupButtonMixin)), ce qui rend le self beaucoup plus simple. self est le bouton lui-même.
#
#     Calcul de position : wxPython a ScreenToClient et GetScreenPosition. En tkinter, c'est plus simple :
#
#         self.winfo_rootx() / self.winfo_rooty() donnent les coordonnées X/Y du widget par rapport à l'écran.
#
#         self.winfo_height() donne la hauteur du widget.
#
#         La position y est donc simplement self.winfo_rooty() + self.winfo_height().
#
#     Affichage du menu : self.mainWindow().PopupMenu() devient self.__menu.post(x, y).
#
#     Liaison d'événement : J'ai lié l'action command du tk.Button (équivalent à un clic gauche) à la méthode self.show_popup_menu, ce qui correspond à l'intention de votre doCommand.


class PopupButtonMixin(object):
    """Mélange cela avec un UICommand pour un menu contextuel de barre d'outils.

    Mélangez (Mixin) cette classe avec un widget tkinter (ex: tk.Button)
    pour lui donner la capacité d'afficher un menu contextuel.

    La classe qui hérite doit implémenter la méthode :
     - create_popup_menu(self)
    """

    def __init__(self):
        """
        Initialise le mixin.
        S'assure que le menu n'est pas encore créé.
        """
        # __menu est mis en cache pour ne pas le recréer à chaque fois
        self.__menu = None

    def show_popup_menu(self):
        """
        Crée (si nécessaire) et affiche le menu contextuel
        juste en dessous du widget.
        """
        if not self.__menu:
            # Le menu n'existe pas encore, on le crée en appelant
            # la méthode que la classe enfant DOIT implémenter.
            # self.__menu = self.create_popup_menu()
            self.__menu = self.createPopupMenu()
            if not self.__menu:
                # Si create_popup_menu ne retourne rien, on arrête.
                print("Erreur : create_popup_menu() n'a pas retourné de menu.")
                return

        # --- Calcul de la position ---
        # C'est l'équivalent de vos méthodes menuX, menuY et menuXY.

        # On s'assure que la géométrie du widget est à jour
        self.update_idletasks()

        # Coordonnées X de l'écran pour le coin supérieur gauche du widget
        x = self.winfo_rootx()

        # Coordonnées Y de l'écran, juste SOUS le widget
        y = self.winfo_rooty() + self.winfo_height()

        # --- Affichage du menu ---
        # C'est l'équivalent de self.mainWindow().PopupMenu(*args)
        try:
            # .post() affiche le menu aux coordonnées X, Y de l'ÉCRAN
            self.__menu.post(x, y)
        except tk.TclError as e:
            # Gère les erreurs (ex: si le menu est déjà affiché)
            print(f"Erreur Tcl lors de l'affichage du menu : {e}")

    def doCommand(self, event=None):  # pylint: disable=W0613
        try:
            args = [self.__menu]
        except AttributeError:
            self.__menu = self.createPopupMenu()  # pylint: disable=W0201
            args = [self.__menu]
        # if self.toolbar:
        if self.winfo_ismapped():
            args.append(self.menuXY())

        # if not self.__menu:
        #     # Le menu n'existe pas encore, on le crée en appelant
        #     # la méthode que la classe enfant DOIT implémenter.
        #     self.__menu = self.create_popup_menu()
        #     if not self.__menu:
        #         # Si create_popup_menu ne retourne rien, on arrête.
        #         print("Erreur : create_popup_menu() n'a pas retourné de menu.")
        #         return
        # --- Affichage du menu ---
        # self.mainWindow().PopupMenu(*args)  # pylint: disable=W0142
        # C'est l'équivalent de self.mainWindow().PopupMenu(*args)
        try:
            # .post() affiche le menu aux coordonnées X, Y de l'ÉCRAN
            self.__menu.post(self.menuX(), self.menuY())
        except tk.TclError as e:
            # Gère les erreurs (ex: si le menu est déjà affiché)
            print(f"Erreur Tcl lors de l'affichage du menu : {e}")

    def menuXY(self):
        """Emplacement pour afficher le menu."""
        log.warning(
            "PopupButtonMixin.menuXY : retourne une fonction anciennement wx.ScreenToClient() !"
        )
        # return self.mainWindow().ScreenToClient((self.menuX(), self.menuY()))  # ScreenToClient est une méthode wx !
        return self.menuX(), self.menuY()

    def menuX(self):
        # buttonWidth = self.toolbar.GetToolSize()[0]
        buttonWidth = self.winfo_width()
        # mouseX = wx.GetMousePosition()[0]
        mouseX = self.winfo_rootx()
        return mouseX - 0.5 * buttonWidth

    def menuY(self):
        # toolbarY = self.toolbar.GetScreenPosition()[1]
        toolbarY = self.winfo_rooty()
        # toolbarHeight = self.toolbar.GetSize()[1]
        toolbarHeight = self.winfo_height()
        return toolbarY + toolbarHeight

    def createPopupMenu(self):
        raise NotImplementedError  # pragma: no cover

    # def create_popup_menu(self):
    #     """
    #     Méthode abstraite (non implémentée) à surcharger.
    #
    #     Cette méthode DOIT être implémentée par la classe qui utilise
    #     ce mixin. Elle doit construire et retourner un objet tk.Menu.
    #     """
    #     raise NotImplementedError(
    #         "La classe héritière doit implémenter create_popup_menu()"
    #     )


class TkUtilsMixin:
    """Fournit des méthodes utilitaires Tkinter pour les classes de commandes."""

    # Si toutes vos classes (comme ViewerCommand, IOCommand, etc.)
    # finissent par hériter d'une classe mère commune appelée UICommand (ou UICommandTk),
    # c'est là qu'il faut les placer.
    # En les déclarant en @staticmethod,
    # vous pouvez même les appeler sans instance si besoin via UICommand.windowIsTextCtrl(w).

    def windowIsTextCtrl(self, window):
        """Vérifie si le widget est un champ de saisie de texte."""
        return isinstance(window, (tk.Text, tk.Entry, ttk.Entry, tk.Spinbox))

    def findEditCtrl(self, window_with_focus):
        """Remonte l'arbre des widgets pour trouver un éditeur actif."""
        curr = window_with_focus
        while curr:
            # Vérifie si c'est un widget d'édition (selon votre implémentation)
            if hasattr(curr, "is_editing") and curr.is_editing():
                return curr

            parent_name = curr.winfo_parent()
            if not parent_name:
                break
            curr = curr.nametowidget(parent_name)
        return None
