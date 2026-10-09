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

import logging  # Module pour la journalisation
import wx  # Bibliothèque wxPython pour l'interface graphique

# from taskcoachlib.thirdparty import aui
# import aui2 as aui
# from wx.lib.agw import aui  # Importation de l'AUI avancé (Advanced User Interface)
from taskcoachlib import (
    operating_system,
)  # Détection du système d'exploitation pour des réglages spécifiques

log = logging.getLogger(__name__)

# Détection automatique du meilleur module AUI disponible
# try:
#     import wx.aui as aui
#     USING_AGW = False
#     log.info("wx.aui (natif) utilisé.")
# except ImportError:
# from wx.lib.agw import aui
import wx.lib.agw.aui as aui

USING_AGW = True
# log.warning("wx.lib.agw.aui utilisé (fallback), wx.aui ne fonctionne pas, AGW est plus flexible!")


class AuiManagedFrameWithDynamicCenterPane(wx.Frame):
    """
    Une classe de fenêtre wx.Frame personnalisée utilisant le gestionnaire AUI
    (Advanced User Interface).
    Elle permet l'ajout de panneaux (panes) dynamiques
    avec une gestion automatique du panneau central.
    Cadre principal personnalisé avec gestion de panneaux dynamiques via wx.aui ou wx.lib.agw.aui.
    Permet de gérer un panneau central protégé, des panneaux ancrés et flottants, avec fallback automatique.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise le cadre avec un gestionnaire AUI
        et définit les styles de gestion et événements selon l'OS.

        :param args: Arguments positionnels transmis à wx.Frame
        :param kwargs: Arguments nommés transmis à wx.Frame
        """
        super().__init__(
            *args, **kwargs
        )  # Appel au constructeur de la classe parente
        # Style AUI : autorise panneau actif, et miniframe natif hors Windows
        agwStyle = (
            aui.AUI_MGR_DEFAULT | aui.AUI_MGR_ALLOW_ACTIVE_PANE
        )  # Style de base avec panneau actif autorisé
        # --- MODIFICATION POUR WAYLAND ---
        if operating_system.isWayland():
            # Utiliser des guides rectangulaires simples sous Wayland
            # car les fenêtres transparentes (TRANSPARENT_HINT) posent problème.
            # On retire le style par défaut qui inclut souvent TRANSPARENT_HINT
            # et on force RECTANGLE_HINT.

            # Note: AUI_MGR_DEFAULT inclut AUI_MGR_TRANSPARENT_HINT.
            # On doit le retirer explicitement.
            agwStyle &= ~aui.AUI_MGR_TRANSPARENT_HINT
            agwStyle |= aui.AUI_MGR_RECTANGLE_HINT
            # Ou essayer AUI_MGR_VENETIAN_BLINDS_HINT si RECTANGLE ne marche pas
            # agwStyle |= aui.AUI_MGR_VENETIAN_BLINDS_HINT
        # ---------------------------------
        if (
            not operating_system.isWindows()
            or not operating_system.isWayland()
        ):
            # With this style on Windows, you can't dock back floating frames
            # Sur Windows, ce style empêche le redockage des fenêtres flottantes, donc on l'active ailleurs
            agwStyle |= aui.AUI_MGR_USE_NATIVE_MINIFRAMES

        # Initialisation du gestionnaire AUI
        self.manager = aui.AuiManager(
            self, agwStyle
        )  # Création du gestionnaire AUI
        # self.manager = aui.AuiManager(self, options=agwStyle)  # Variante avec aui à la place de AGW.
        # notify AUI which frame to use
        self.manager.SetManagedWindow(self)

        # Configuration des onglets (si AGW, on peut utiliser des options avancées) :
        if USING_AGW:
            self.manager.SetAutoNotebookStyle(
                aui.AUI_NB_TOP  # Configuration des onglets automatiques
                | aui.AUI_NB_CLOSE_BUTTON
                | aui.AUI_NB_SUB_NOTEBOOK
                | aui.AUI_NB_SCROLL_BUTTONS
            )
        else:
            # Configuration de base des notebooks (moins avancée que AGW)
            # wx.aui ne gère pas les notebooks imbriqués comme AGW
            # TODO : A vérifier
            notebook_art = aui.AuiDefaultTabArt()
            self.manager.SetArtProvider(notebook_art)
        self.manager.Update()
        self.bindEvents()  # Liaison des événements personnalisés

    def bindEvents(self):
        """
        Lie les événements liés à la fermeture ou au passage en flottant d'un panneau à un gestionnaire personnalisé.
        """
        for eventType in aui.EVT_AUI_PANE_CLOSE, aui.EVT_AUI_PANE_FLOATING:
            self.manager.Bind(
                eventType, self.onPaneClosingOrFloating
            )  # Lien avec méthode personnalisée

    def onPaneClosingOrFloating(self, event):
        """
        Empêche la fermeture ou le flottement du dernier panneau central.

        :param event: Événement AUI déclenché
        """
        pane = event.GetPane()  # Récupération du panneau concerné
        dockedPanes = self.dockedPanes()  # Liste des panneaux ancrés

        if self.isCenterPane(pane) and len(dockedPanes) == 1:
            event.Veto()  # Empêche la fermeture si c’est le dernier panneau central
        else:
            event.Skip()  # Laisse passer l'événement
            if self.isCenterPane(pane):
                if pane in dockedPanes:
                    dockedPanes.remove(pane)  # Retire le panneau de la liste
                if USING_AGW:  # TODO : A vérifier !
                    dockedPanes[0].Center()  # Centre un autre panneau
                else:
                    dockedPanes[0].dock_direction = (
                        aui.AUI_DOCK_CENTRE
                    )  # Version AUI

    def addPane(self, window, caption, name, floating=False):
        """
        Ajoute une fenêtre comme panneau dans l'interface AUI.

        :param window: La fenêtre à ajouter
        :param caption: Le titre du panneau
        :param name: Le nom interne du panneau
        :param floating: Indique si le panneau doit être initialement flottant
        """
        # # x, y = window.GetPositionTuple()
        # # wxPyDeprecationWarning: Call to deprecated item. Use GetPosition instead
        window.Show()  # Assure que la fenêtre est visible
        self.Show()  # Assure que le cadre principal est visible

        x, y = window.GetPosition()  # Position initiale de la fenêtre
        # # # x, y = window.ClientToScreenXY(x, y)
        # # # AttributeError: 'TaskViewer' object has no attribute 'ClientToScreenXY'. Did you mean: 'ClientToScreen'?
        # # # Debug: ClientToScreen cannot work when toplevel window is not shown
        # if window.Shown:
        # x, y = window.ClientToScreen(x, y)  # J'ai ClientToScreen cannot work when toplevel window is not shown même si window.shown est True
        # #     # pour window CategoryViewer (gui.viewer.category.CategoryViewer)
        if window.IsShown():
            # x, y = window.ClientToScreenXY(
            x, y = window.ClientToScreen(
                x, y
            )  # Convertit la position en coordonnées écran si affichée
        else:
            log.debug(
                "La fenêtre %s n'est pas encore affiché, ClientToScreen ignoré.",
                window,
            )
        #     print("frame.py: Debug: ClientToScreen cannot work when toplevel window is not shown")
        # RESOLUTION DE "ClientToScreen cannot work when toplevel window is not shown" :

        # Configuration des propriétés du panneau, création des options du panneau
        paneInfo = aui.AuiPaneInfo()
        if USING_AGW:
            paneInfo = (
                paneInfo.CloseButton(True)
                .Floatable(True)
                .Name(name)
                .Caption(caption)
                .Right()
                .FloatingSize((300, 200))
                .BestSize((200, 200))
                .FloatingPosition((x + 30, y + 30))
                .CaptionVisible()
                .MaximizeButton()
                .DestroyOnClose()
            )
            # paneInfo = paneInfo.CloseButton(True).Floatable(True). \
            #     Name(name).Caption(caption).Right(). \
            #     FloatingSize((300, 200)).BestSize((200, 200)). \
            #     CaptionVisible().MaximizeButton().DestroyOnClose()
        else:
            # Version AUI :
            paneInfo = (
                paneInfo.Name(name)
                .Caption(caption)
                .Floatable(True)
                .CloseButton(True)
                .BestSize((200, 200))
                .FloatingSize((300, 200))
                .MaximizeButton(True)
                .DestroyOnClose(True)
                .CaptionVisible(True)
                .Right()
            )

        if floating:
            # Positionner la fenêtre flottante de manière relative à l'écran ou à la fenêtre principale après l'ajout.
            paneInfo.Float()  # Active le mode flottant (voir description de wx.lib.agw.aui.framemanager)
            # Vous pourriez définir une position initiale approximative ici,
            # puis potentiellement l'ajuster après l'affichage.
            # Par exemple, centrer approximativement :
            screen_rect = (
                wx.GetClientDisplayRect()
            )  # Récupère la taille de l'écran client
            float_x = (
                screen_rect.width - 300
            ) // 2 + 30  # Position horizontale centrée
            float_y = (
                screen_rect.height - 200
            ) // 2 + 30  # Position verticale centrée
            paneInfo = paneInfo.FloatingPosition(
                (float_x, float_y)
            )  # Positionne le panneau flottant

        if not self.dockedPanes():  # S'il n'y a aucun panneau ancré
            paneInfo = (
                paneInfo.CenterPane()
            )  # Définit ce panneau comme central

        # Ajoute les panneaux au gestionnaire :
        self.manager.AddPane(window, paneInfo)
        self.manager.Update()  # Rafraîchit l'affichage

    def setPaneTitle(self, window, title):
        """
        Modifie le titre (caption) d’un panneau donné.

        :param window: La fenêtre/panneau cible
        :param title: Nouveau titre à appliquer
        """
        self.manager.GetPane(window).Caption(title)  # Mise à jour du titre
        # self.manager.Update()  # Rafraîchit l'affichage

    def dockedPanes(self):
        """
        Retourne la liste des panneaux ancrés
        (ni flottants, ni dans une barre d'outils, ni dans un notebook).

        :return: Liste des objets AuiPaneInfo ancrés
        """
        if USING_AGW:
            return [
                pane
                for pane in self.manager.GetAllPanes()
                if not pane.IsToolbar()
                and not pane.IsFloating()
                and not pane.IsNotebookPage()
            ]
        else:
            # Version AUI:
            return [
                pane
                for pane in self.manager.GetAllPanes()
                if not pane.IsFloating() and not pane.IsToolbar()
            ]
        # self.manager.Update()  # Rafraîchit l'affichage

    def float(self, window):
        """
        Rend flottante la fenêtre donnée.

        :param window: La fenêtre à détacher
        """
        # Met le panneau en mode flottant
        self.manager.GetPane(window).Float()
        # self.manager.Update()  # Rafraîchit l'affichage

    @staticmethod
    def isCenterPane(pane):
        """
        Détermine si un panneau est positionné au centre.

        :param pane: Un objet AuiPaneInfo
        :return: True si c’est le panneau central, False sinon
        """
        # Vérifie la direction de dockage
        if USING_AGW:
            # Version AGW :
            # return pane.dock_direction_get() == aui.AUI_DOCK_CENTER
            return pane.dock_direction == aui.AUI_DOCK_CENTER
        else:
            # Version wx.aui :
            return (
                pane.dock_direction == aui.AUI_DOCK_CENTRE
            )  # (orthographe britannique !)
