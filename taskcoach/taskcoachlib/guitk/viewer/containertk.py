# D'accord, convertissons le fichier container.py de wxPython vers Tkinter,
# en remplaçant aui par tkinter.ttk.Notebook.
# Voici une version convertie du code,
# accompagnée d'explications sur les changements.
# Notez que cette conversion est complexe et peut nécessiter d'autres ajustements.

# Explications des changements :
#
# Importations : Remplacement des importations wx et wx.lib.agw.aui
# par tkinter et tkinter.ttk.
# __init__ :
# containerWidget est maintenant une référence à une fenêtre Tkinter.
# self.notebook = ttk.Notebook(containerWidget) :
#   Création d'un ttk.Notebook pour gérer les onglets.
# self.notebook.pack(expand=True, fill="both") :
# Assurer que le notebook prend toute la place.
#
#
# addViewer :
# Création d'un ttk.Frame pour chaque viewer.
# C'est important, car chaque onglet du Notebook a besoin d'un conteneur.
# viewer.pack(in_=viewer_frame, expand=True, fill="both") :
#   Placer le viewer dans le Frame.
# self.notebook.add(viewer_frame, text=viewer.title()) :
#   Ajouter un nouvel onglet au Notebook avec le titre du viewer.
#
# closeViewer :
# Recherche de l'index de l'onglet correspondant au viewer.
# Utilisation de self.notebook.forget(tab_id) pour supprimer l'onglet.
#
# activeViewer :
# Utilisation de self.notebook.select() pour obtenir l'ID de l'onglet sélectionné.
# Retourne le viewer correspondant à l'onglet sélectionné.
#
# activateViewer :
# Recherche de l'index du viewer à activer.
# Utilisation de self.notebook.select(tab_id) pour sélectionner l'onglet.
#
# onPageChanged :
# Gère l'événement <<NotebookTabChanged>> du ttk.Notebook.
#
# __ensure_active_viewer_has_focus :
# Adaptation de la logique de recherche du focus pour Tkinter.
# Utilisation de self.container_widget.after(0, self.activeViewer().focus_set)
# pour définir le focus après que Tkinter ait traité les autres événements.
#
#
# Points Importants :
#
# Gestion du Layout : aui offrait des fonctionnalités de docking complexes.
#   Avec ttk.Notebook, on se concentre sur une gestion simple des onglets.
#   Si tu as besoin de plus de flexibilité (docking, etc.),
#   tu devras envisager d'autres bibliothèques
#   (il n'y a pas d'équivalent direct à AUI dans Tkinter standard).
# Événements : Les événements ont été adaptés pour Tkinter.
# Exemple d'utilisation : J'ai inclus un exemple minimaliste
#   pour illustrer comment utiliser ViewerContainer avec des DummyViewer.
#   Tu devras adapter cet exemple à ta propre application.
#
# Pour la suite :
#
# Teste ce code : Adapte l'exemple d'utilisation à la fin du fichier pour tester le code.
# Crée de vrais viewers à la place des DummyViewer.
# Gère le Focus : Assure-toi que le focus est correctement géré lorsque tu changes d'onglet.
# Adapte les autres fichiers : Adapte le code des autres fichiers pour fonctionner
# avec cette nouvelle architecture.

# L'erreur TypeError: object.__init__() takes exactly one argument survient
# car le constructeur de la classe parente de ViewerContainer (super().__init__)
# ne s'attend pas à recevoir l'argument settings que vous lui transmettez.
#
# Votre classe ViewerContainer hérite de tkinter.ttk.Frame,
# dont le constructeur n'accepte qu'un seul argument positionnel :
# le widget parent.
# Le super().__init__(containerWidget, settings, *args, **kwargs)
# que vous avez dans le fichier container.py tente de passer settings à la classe parente,
# ce qui provoque l'erreur.
#
# Correction
#
# Pour résoudre ce problème, il vous suffit de modifier le fichier container.py
# en ne transmettant au constructeur parent que le widget parent (containerWidget).
# L'argument settings doit être géré à l'intérieur de la méthode __init__ de ViewerContainer.
# Je comprends que l'erreur persiste. Après une analyse plus approfondie,
# le problème vient du fait que la classe ViewerContainer ne déclare pas explicitement
# qu'elle est un widget Tkinter.
# Par conséquent, l'appel à super().__init__ se réfère au constructeur de la classe
# de base object, qui ne s'attend pas à recevoir d'arguments en plus de l'instance (self).
#
# Pour corriger cela, vous devez modifier la définition de la classe ViewerContainer
# pour qu'elle hérite de tkinter.ttk.Frame. Cela permet à la classe d'utiliser
# les fonctionnalités des widgets Tkinter et de gérer correctement son propre constructeur.
# Explication du Changement
#
# La ligne class ViewerContainer(ttk.Frame): est la clé.
# Elle indique au système de classes de Python que ViewerContainer est un type de ttk.Frame,
# ce qui résout le problème de l'appel à super().__init__
# en lui donnant la bonne classe parente à initialiser.

# Je vais vous aider à convertir le fichier container.py de Task Coach,
# qui utilise wxPython et aui, vers Tkinter en utilisant ttk.PanedWindow.
# Cependant, une conversion complète nécessiterait une refonte significative
# de l'architecture, car wxPython et Tkinter ont des philosophies très différentes.
# Je vais donc vous fournir une structure de base et des indications pour adapter
# chaque partie clé.
# Le fichier container.py gère un ensemble de "viewers" (visualiseurs)
# à l'aide d'un AUI (Advanced User Interface) pane manager de wxPython.
# L'objectif est de transposer cette gestion des viewers
# dans un environnement Tkinter en utilisant ttk.PanedWindow
# pour organiser les différents viewers.
# Voici les étapes à suivre et le code converti:
# 1. Analyse du code existant :
#
# ViewerContainer : La classe principale qui gère les viewers. Elle s'occupe de l'ajout, de la suppression, de l'activation et de la distribution des événements aux viewers.
# AUI Pane Management : Le code utilise aui.AuiManager pour organiser les viewers dans des panneaux dockables et flottants. Il faudra remplacer cela par ttk.PanedWindow.
# Event Handling : Le code gère des événements comme la fermeture, l'activation et le flottement des panneaux (aui.EVT_AUI_PANE_CLOSE, aui.EVT_AUI_PANE_ACTIVATED, aui.EVT_AUI_PANE_FLOATED). Il faudra adapter cela au système d'événements de Tkinter.
# Active Viewer : Le code suit quel viewer est actif et relaie les appels de méthode vers ce viewer.
# PubSub : Le code utilise pubsub pour la communication entre les composants.
#
# 2. Structure Tkinter avec ttk.PanedWindow :
# ttk.PanedWindow permet de diviser une fenêtre en panneaux redimensionnables. Chaque "viewer" deviendra un enfant d'un de ces panneaux. On peut imbriquer les PanedWindow pour créer des dispositions complexes.
# 3. Conversion du code :
# Voici une ébauche de conversion du code. Notez que ceci est une base et nécessitera des ajustements importants pour fonctionner complètement avec votre application TaskCoach :

# Explications et adaptations nécessaires :
#
# Remplacement d'AUI : ttk.PanedWindow remplace le AuiManager. Il offre une fonctionnalité de base pour diviser l'espace en panneaux redimensionnables. Si vous avez besoin de fonctionnalités plus avancées (docking, flottement, etc.), il faudra envisager des bibliothèques tierces ou implémenter ces fonctionnalités vous-même.  Il n'y a pas d'équivalent direct et simple à AUI dans Tkinter standard.
# Gestion des événements : Les événements wxPython (aui.EVT_AUI_PANE_CLOSE, etc.) doivent être remplacés par les événements Tkinter correspondants. Par exemple, pour la fermeture, vous pouvez intercepter l'événement de fermeture de la fenêtre (WM_DELETE_WINDOW) et exécuter votre logique de fermeture de viewer.
# Viewers : Les "viewers" doivent être des widgets Tkinter (par exemple, tk.Text, tk.Canvas, ttk.Frame). Vous devrez adapter le code de vos viewers existants pour qu'ils héritent de tk.Widget ou ttk.Widget.
# PubSub : Si vous utilisez pubsub pour la communication, il faudra trouver une alternative appropriée dans Tkinter. Vous pouvez utiliser les événements Tkinter ou un système de messagerie personnalisé.  Une option serait d'utiliser les événements virtuels de Tkinter (<<MyEvent>>).
# Floating : La fonctionnalité de "floating" (fenêtres flottantes) n'est pas directement prise en charge par ttk.PanedWindow. Pour obtenir un comportement similaire, vous devrez créer de nouvelles fenêtres tk.Toplevel et y déplacer les viewers.
# Focus : La gestion du focus est importante. Assurez-vous que la visionneuse active reçoit le focus correctement en utilisant widget.focus_set().
# Adaptation des Viewers : La partie la plus importante sera d'adapter chaque viewer (attachment.py, base.py, etc.) pour qu'ils soient des widgets Tkinter et qu'ils interagissent correctement avec le ViewerContainer basé sur ttk.PanedWindow.
# Boucle principale Tkinter : Assurez-vous que votre application démarre la boucle principale Tkinter (root.mainloop()) pour que l'interface graphique fonctionne.
#
# Problèmes potentiels et considérations :
#
# Complexité de la conversion : La conversion de wxPython à Tkinter est un projet conséquent,
#   surtout avec l'utilisation d'AUI.
# Fonctionnalités manquantes : ttk.PanedWindow est moins riche en fonctionnalités que wxPython AUI.
#   Vous devrez peut-être sacrifier certaines fonctionnalités ou les réimplémenter.
# Apparence : L'apparence des widgets Tkinter peut être différente de celle des widgets wxPython.
#   Vous devrez peut-être personnaliser l'apparence avec des thèmes ttk.
import logging
import tkinter as tk
import tkinter.ttk as ttk
from taskcoachlib import operating_system
import taskcoachlib.guitk.menutk
from pubsub import pub  # pip install PyPubSub

log = logging.getLogger(__name__)


# class ViewerContainer:
# class ViewerContainer(ttk.Frame):  # ttk.PanedWindow
# class ViewerContainer(ttk.LabelFrame):
class ViewerContainer(ttk.PanedWindow):
    """
    ViewerContainer est un conteneur de visionneuses. Il utilise un Panedwindow Tkinter
    pour afficher les visionneuses. Le ViewerContainer sait lequel de ses visualiseurs
    est actif et distribue les appels de méthode au visualiseur actif.
    Il hérite maintenant de ttk.Frame pour être un widget Tkinter à part entière.

    Cette classe délègue explicitement certaines méthodes attendues
    par les UICommand vers la visionneuse actuellement active.

    Methods:
        __init__ (self, parent_widget, settings, *args, **kwargs) : Initialise le conteneur de visionneuses.
        componentsCreated : Méthode appelée lorsque les composants sont créés.
        advanceSelection (self, forward) : Avancer ou reculer dans la liste des visionneuses.
        isViewerContainer : Retourne qu'il s'agit d'un conteneur de visionneuse.
        isTreViewer : Retourne si la visionneuse active est une visionneuse arborescente.
        __bind_event_handlers : Inscrit les gestionnaires d'événements pour la fermeture et le changement d'onglet.
        __getitem__ (self, index) : Retourne la visionneuse à l'index défini.
        __len__ : Retourne le nombre de visionneuses.
        addViewer (self, viewer, *args, *kwargs) : Crée et ajoute une visionneuse au conteneur.
    """

    # def __init__(self, containerWidget, settings, *args, **kwargs):
    def __init__(self, parent_widget, settings, *args, **kwargs):
        """
        Initialise le conteneur de visionneuses.

        Args:
            parent_Widget: Le widget conteneur (par exemple, une fenêtre Tk).
            settings: Paramètres de l'application.
            *args: Arguments supplémentaires.
            **kwargs: Arguments nommés supplémentaires.

        Attributes:
            self.viewer_count :
            self._label : Titre du conteneur
            self.containerWidget : Le widget conteneur (par exemple, une fenêtre Tk, toplevel, ou ici MainWindow).
            self._settings : Paramètres de l'application.
            self.viewers : list des visionneuses contenus.
            self._active_viewer : Le viewer actif.
            self._notify_active_viewer :
        """
        # Vous avez deux problèmes.
        # Tout d’abord, super().__init__ ne doit recevoir que parent_widget,
        # puis la visionneuse doit être ajoutée directement au bloc-notes.
        log.debug(
            "ViwerContainer.__init__ : Initialisation du conteneur de visionneuses."
        )
        # super().__init__(containerWidget)
        # super().__init__(parent_widget)
        # super().__init__(parent_widget, *args, text="ViewerContainer", **kwargs)  # text ne fonctionne pas dans PanedWindow
        super().__init__(
            parent_widget, *args, **kwargs
        )  # text ne fonctionne pas dans PanedWindow
        # TODO : copier factorytk Mock
        self.viewer_count = 0  # copie de factorytk.MockViewerContainer
        self._label = ttk.Label(
            self,
            name="visual_conteneur",
            text="Conteneur de visualisateurs...",
        )
        # self._label.pack(pady=20)
        self._label.grid(row=1, column=0, padx=10, pady=10)
        # self.containerWidget = containerWidget  # Le widget conteneur (par exemple, une fenêtre Tk).
        self.containerWidget = parent_widget  # Le widget conteneur (par exemple, une fenêtre Tk, toplevel, ou ici MainWindow).
        self._settings = settings
        self.viewers = []  # Liste des visionneuses
        # # self.notebook = ttk.Notebook(containerWidget)  # Utilisation de ttk.Notebook. On utilise 'self' ici, car ViewerContainer est le parent du notebook.
        # # On utilise 'self' ici, car ViewerContainer est le parent du notebook.
        # self.notebook = ttk.Notebook(self)  # Utilisation de ttk.Notebook. On utilise 'self' ici, car ViewerContainer est le parent du notebook.
        # self.notebook.pack(expand=True, fill="both")  # Assurez-vous que le Notebook prend toute la place
        # self.paned_window = ttk.PanedWindow(parent_widget, orient=tk.HORIZONTAL)  # Ou VERTICAL selon votre disposition
        # self.paned_window = ttk.PanedWindow(self.containerWidget, orient=tk.HORIZONTAL)
        # self.paned_window.containerWidget = self
        # self.paned_window.pack(fill=tk.BOTH, expand=True)

        self._active_viewer = None  # Initialisation importante
        self._notify_active_viewer = (
            False  # A ajuster en fonction de l'utilisation
        )
        self.__bind_event_handlers()
        # super().__init__(*args, **kwargs)
        # super().__init__(containerWidget, settings, *args, **kwargs)
        log.debug("ViewerContainer.__init__ : Conteneur initialisé !")

    def componentsCreated(self):
        """
        Enregistre dans l'attribut _notify_active_viewer que les éléments sont créés.
        """
        self._notify_active_viewer = True

    def advanceSelection(self, forward):
        """Active la visionneuse suivante si forward est True, sinon la visionneuse précédente."""
        if len(self.viewers) <= 1:
            return  # Pas assez de visionneuses pour avancer la sélection

        active_viewer = self.activeViewer()
        current_index = (
            self.viewers.index(active_viewer) if active_viewer else 0
        )
        minimum_index, maximum_index = 0, len(self.viewers) - 1

        if forward:
            new_index = (
                current_index + 1
                if minimum_index <= current_index < maximum_index
                else minimum_index
            )
        else:
            new_index = (
                current_index - 1
                if minimum_index < current_index <= maximum_index
                else maximum_index
            )

        self.activateViewer(self.viewers[new_index])

    def isViewerContainer(self):
        """Indique s'il s'agit d'un conteneur de visionneuse."""
        return True

    def isTreeViewer(self):
        """
        Indique si le viewer/la visionneuse actif est un TreeViewer/une visionneuse arborescente.

        Retourne False si aucune visionneuse active n'est disponible.
        """
        # viewer = self.activeViewer
        # # Si aucune visionneuse n'est active, on ne bloque pas le menu
        # if not self.activeViewer:
        #     return False  # Aucun viewer → pas un TreeViewer

        # Délégation vers la visionneuse active
        # return hasattr(viewer, "isTreeViewer") and viewer.isTreeViewer()
        # return hasattr(self.activeViewer, "isTreeViewer") and self.activeViewer.isTreeViewer()
        viewer = self.activeViewer()
        return hasattr(viewer, "isTreeViewer") and viewer.isTreeViewer()

    def __bind_event_handlers(self):
        """Inscrit les gestionnaires d'événements pour la fermeture et le changement d'onglet."""
        # self.notebook.bind("<<NotebookTabChanged>>", self.onPageChanged)  # Changement d'onglet

    def __getitem__(self, index):
        """Retourne la visionneuse à l'index défini."""
        return self.viewers[index]

    def __len__(self):
        """Retourne le nombre de visionneuses."""
        return len(self.viewers)

    # def addViewer(self, viewer, title: str, floating=False):
    #     """Ajoute une nouvelle visionneuse (viewer) au conteneur."""
    #     log.info(f"ViewerContainer.addViewer : Ajout du visualiseur {viewer.title()}.")
    #
    #     # # name = viewer.settingsSection()
    #     # viewer_frame = ttk.Frame(self.notebook)  # Crée un Frame pour chaque viewer
    #     # # viewer_frame.pack(expand=True, fill="both")  # Affiche le Frame
    #     # # viewer.pack(in_=viewer_frame, expand=True, fill="both")  # Place le viewer dans le frame
    #     # viewer.pack(in_=viewer_frame, expand=True, fill="both", padx=10, pady=5)  # Place le viewer dans le frame
    #     # # Le Taskviewer n'est pas visible car la méthode addViewer de votre fichier container.py
    #     # # crée un ttk.Frame supplémentaire pour chaque visualiseur.
    #     # # C'est incorrect, car le Taskviewer (et les autres visualisateurs)
    #     # # sont déjà des sous-classes de ttk.Frame et doivent être ajoutés
    #     # # directement au ttk.Notebook qui gère les onglets.
    #     # #
    #     # # En essayant de placer le Taskviewer (qui est déjà un Frame
    #     # # et un enfant du MainWindow) dans un nouveau Frame qui est l'enfant du Notebook,
    #     # # vous créez une structure de widget invalide,
    #     # # et le Taskviewer ne s'affiche jamais correctement.
    #     # # self.notebook.add(viewer_frame, text=viewer.title())  # Ajoute un onglet au Notebook
    #     # self.notebook.add(viewer_frame, text=title)  # Ajoute un onglet au Notebook
    #     # Pour corriger ce problème, ajouter le visualiseur directement au Notebook sans créer de Frame intermédiaire.
    #     # self.notebook.add(viewer, text=title)  # Ajoute un onglet au Notebook
    #     # Le viewer lui-même est déjà une sous-classe de ttk.Frame,
    #     # il doit donc être ajouté directement au Notebook.
    #     # Vous n'avez pas besoin de créer un Frame supplémentaire.
    #     self.notebook.add(viewer, text=viewer.title())
    #
    #     # Met à jour les listes de viewers
    #     self.viewers.append(viewer)
    #     self.viewer_widget_map[viewer] = viewer
    #     self.viewer_count += 1
    #
    #     # if len(self.viewers) == 1:
    #     #     self.activateViewer(viewer)
    #     #
    #     # pub.subscribe(self.onStatusChanged, viewer.viewerStatusEventType())
    #     log.info(f"ViewerContainer.addViewer : Visualiseur : {viewer.title()} ajouté !")

    # Modifiez la signature de la méthode addViewer
    # def addViewer(self, viewer_class, *args, **kwargs):
    def addViewer(self, viewer, *args, **kwargs):
        # def _add_viewer(self, viewer, *args, **kwargs):
        """
        Crée et ajoute une visionneuse (viewer) au conteneur.
        """
        # Cette méthode fait double emploi avec celle de factorytk.py !
        # C'est factorytk.py qui s'occupe de l'affichage des visionneuses !
        # log.info(f"ViewerContainer.addViewer : Ajout du visualiseur {viewer_class.__name__}.")
        # log.info(f"ViewerContainer.addViewer : Ajout du visualiseur {viewer.__name__}.")
        log.info(
            f"ViewerContainer.addViewer : Ajout du visualiseur {viewer.title()}."
        )

        # viewer_frame = ttk.Frame(self.notebook)

        # Créez le visualiseur avec le nouveau cadre comme parent
        # viewer = viewer_class(viewer_frame, *args, **kwargs)
        # Ajoute le viewer à la liste des viewers.
        self.viewers.append(viewer)

        # Ajoute le viewer au bandeau de viewers
        # self.paned_window.add(viewer)  # viewer doit être un widget Tkinter

        # Placez le visualiseur à l'intérieur du nouveau cadre
        # viewer.pack(expand=True, fill="both")
        # viewer.pack(fill="both", expand=True, padx=10, pady=5)  # copie de factorytk.MockViewerContainer
        # viewer.grid(row=0, column=0)  # A essayer !
        viewer.grid(
            row=self.viewer_count + 1, column=0, padx=10, pady=5
        )  # TODO : Attention, peut-être double avec celui de factory addViewers ! A retirer ?

        # if isinstance(viewer, ViewerContainer):
        #     # viewer.pack(fill="both", expand=True, padx=10, pady=5)
        #     viewer.grid(row=self.viewer_count+1, column=0, padx=10, pady=5)
        # else:
        #     viewer.grid(row=self.viewer_count+1, column=0, padx=10, pady=5)

        # Ajoutez le nouveau cadre (qui contient le visualiseur) comme onglet
        # self.notebook.add(viewer_frame, text=viewer.title())

        # Met à jour les listes de viewers
        # self.viewers.append(viewer)
        # self.viewer_widget_map[viewer] = viewer_frame
        self.viewer_count += 1

        if len(self.viewers) == 1:
            self.activateViewer(viewer)
        if self._active_viewer is None:
            self.activateViewer(viewer)
        log.info(
            # f"ViewerContainer.addViewer : Le visualiseur {viewer.title()} a été ajouté au conteneur. Total = {self.viewer_count} visionneuses."
            f"ViewerContainer.addViewer : Le visualiseur {viewer.title()} a été ajouté au conteneur. Total = {self.__len__()} visionneuses."
        )

    def removeViewer(self, viewer):
        """Retire un visualiseur du conteneur."""
        for i, (v, frame) in enumerate(self.viewers):
            if v == viewer:
                # Retire la visionneuse de la liste
                # self.notebook.forget(i)
                self.viewers.pop(i)
                viewer.grid_forget()  # Important pour libérer les ressources
                break

    def selectViewer(self, viewer):
        """Sélectionne un visualiseur."""
        for i, (v, frame) in enumerate(self.viewers):
            if v == viewer:
                # self.notebook.select(i)
                viewer.select()
                break

    def get_active_viewer(self):
        """Retourne le visualiseur actif."""
        # # try:
        # #     # tab_id = self.notebook.select()
        # #     if tab_id:
        # #         frame = self.notebook.nametowidget(tab_id)
        # #         viewer = frame.winfo_children()[0]
        # #         return viewer
        # # except tk.TclError:
        # #     return None
        # return None
        self._active_viewer = self.focus_get()
        return self._active_viewer

    def onPageChanged(self, event):
        """Gestionnaire de l'événement de changement de page.

        Gère l'événement de changement d'onglet.
        """
        # À adapter en fonction de la façon dont vous gérez les onglets/pages
        log.debug("ViewerContainer.onPageChanged : L'onglet a changé.")
        if self._active_viewer:
            self._active_viewer.focus_set()
        self.sendViewerStatusEvent()
        # # La logique de rafraîchissement doit être implémentée ici
        # # self.refresh()
        # pass

    def closeViewer(self, viewer):
        """Ferme la visionneuse spécifiée."""
        # # if viewer == self.activeViewer():
        # #     self.advanceSelection(False)
        # #
        # #     # Trouver l'onglet correspondant au viewer
        # # for i, v in enumerate(self.viewers):
        # #     if v == viewer:
        # #         tab_id = i
        # #         break
        # # else:
        # #     return  # Viewer non trouvé
        # #
        # # # Supprimer l'onglet du Notebook
        # # self.notebook.forget(tab_id)
        # # self.viewers.remove(viewer)
        # # viewer.detach()
        # # if self.viewers:
        # #     self.activateViewer(self.viewers[0])  # Activer un autre viewer si possible
        # self.removeViewer(viewer)
        if viewer in self.viewers:
            # self.paned_window.remove(viewer)
            self.viewers.remove(viewer)
            viewer.destroy()  # Important pour libérer les ressources

            if self._active_viewer == viewer:
                self._active_viewer = None
                if self.viewers:
                    self.activateViewer(
                        self.viewers[0]
                    )  # Activer une autre visionneuse si possible

    def activateViewer(self, viewer_to_activate):
        """Active la visionneuse spécifiée."""
        log.info(
            f"ViewerContainer.activateViewer : Activation du visualiseur {viewer_to_activate.title()}."
        )
        # # Trouver l'index de l'onglet correspondant au viewer
        # for i, v in enumerate(self.viewers):
        #     if v == viewer_to_activate:
        #         tab_id = i
        #         break
        # else:
        #     return  # Viewer non trouvé
        #
        # # Sélectionner l'onglet dans le Notebook
        # # self.notebook.select(tab_id)
        # self.sendViewerStatusEvent()
        self._active_viewer = viewer_to_activate
        #  Mettre en évidence la visionneuse active (changement de couleur de fond, focus, etc.)
        for v in self.viewers:
            if v == viewer_to_activate:
                v.config(relief=tk.SUNKEN)  # exemple
            else:
                v.config(relief=tk.RAISED)  # exemple

    # def activeViewer(self):
    def activeViewer(self):
        """Renvoie la visionneuse active (sélectionnée)."""
        # current_tab = self.notebook.select()  # ID de l'onglet sélectionné
        # if not current_tab:
        #     return None  # Aucun onglet sélectionné
        #
        # tab_index = self.notebook.index(current_tab)
        # if 0 <= tab_index < len(self.viewers):
        #     return self.viewers[tab_index]
        # else:
        #     return None
        # return self.viewer.focus_get()
        return self.focus_get()
        # return self._active_viewer
        # return self._active_viewer

    def __getattr__(self, attribute):
        """
        Transfère les attributs inconnus au visualiseur actif.
        """
        viewer = self.activeViewer()
        if viewer is None:
            raise AttributeError(
                f"'ViewerContainer' object has no attribute '{attribute}'"
            )
        return getattr(viewer, attribute)
        # if self._active_viewer:
        #     try:
        #         return getattr(self._active_viewer, attribute)
        #     except AttributeError:
        #         log.error(f"La visionneuse active n'a pas l'attribut : {attribute}")
        #         raise
        # else:
        #     # raise AttributeError("Aucune visionneuse active.")
        #     log.error("Aucune visionneuse active.")

    def onStatusChanged(self, viewer):
        if self.activeViewer() == viewer:
            self.sendViewerStatusEvent()
        pub.sendMessage("all.viewer.status", viewer=viewer)

    # def onPageChanged(self, event=None):
    #     """Gère l'événement de changement d'onglet."""
    #     self.__ensure_active_viewer_has_focus()
    #     self.sendViewerStatusEvent()
    #     if self._notify_active_viewer and self.activeViewer() is not None:
    #         self.activeViewer().activate()

    def sendViewerStatusEvent(self):
        """Envoie un événement de statut de la visionneuse."""
        pub.sendMessage(
            "viewer.status"
        )  # À adapter ou supprimer si pubsub n'est pas utilisé
        pass

    def __ensure_active_viewer_has_focus(self):
        if not self.activeViewer():
            return

        window_focused = (
            tk.Tk().focus_displayof()
        )  # équivalent de wx.Window.FindFocus()
        if operating_system.isMacOsXTiger_OrOlder() and window_focused is None:
            # Si SearchCtrl a le focus sur Mac OS X Tiger,
            # tk.Tk().focus_displayof() renvoie None.
            # Si nous continuions, le focus serait immédiatement placé sur le visualiseur actif,
            # ce qui rendrait impossible pour l'utilisateur de saisir le contrôle de recherche.
            return

            # Trouver si le visualiseur actif est un parent de la fenêtre de focus
        parent = window_focused
        while parent:
            if parent == self.activeViewer():
                return
            try:
                parent = parent.master  # tk equivalent de GetParent
            except AttributeError:
                parent = None

                # Si le visualiseur actif n'a pas le focus, le définir
        self.containerWidget.after(
            0, self.activeViewer().focus_set
        )  # Utilisation de after pour éviter les problèmes de focus

    def onPageChanged(self, event=None):
        """Gestionnaire de l'événement de changement de page."""
        # À adapter en fonction de la façon dont vous gérez les onglets/pages
        if self._active_viewer:
            self._active_viewer.focus_set()
        self.sendViewerStatusEvent()

    #  Ajouter d'autres méthodes pour gérer les événements, la configuration, etc.
    def curselection(self):
        """
        Retourne la sélection courante du viewer actif/de la visionneuse active.

        Retourne une liste vide si non supporté.
        """
        # # viewer = self.activeViewer
        # # # ou viewer = self._active_viewer
        # # if hasattr(viewer, "curselection"):
        # #     return viewer.curselection()
        # # Aucun viewer actif → aucune sélection
        # if not self.activeViewer:
        #     return []
        #
        # # Si la visionneuse ne supporte pas la sélection, on renvoie vide
        # if not hasattr(self.activeViewer, "curselection"):
        #     return []

        # Délégation vers le viewer actif
        # return self.activeViewer.curselection()
        viewer = self.activeViewer()
        if hasattr(viewer, "curselection"):
            return viewer.curselection()
        return []
        return ()

    def isAnyItemExpandable(self):
        """
        Indique si au moins un élément peut être étendu dans la visionneuse active.
        """
        # if not self.activeViewer:
        #     return False
        #
        # if not hasattr(self.activeViewer, "isAnyItemExpandable"):
        #     return False
        #
        # return self.activeViewer.isAnyItemExpandable()
        viewer = self.activeViewer()
        if hasattr(viewer, "isAnyItemExpandable"):
            return viewer.isAnyItemExpandable()
        return False

    def isAnyItemCollapsable(self):
        """
        Indique si au moins un élément peut être replié dans la visionneuse active.
        """
        # if not self.activeViewer:
        #     return False
        #
        # if not hasattr(self.activeViewer, "isAnyItemCollapsable"):
        #     return False
        #
        # return self.activeViewer.isAnyItemCollapsable()
        viewer = self.activeViewer()
        if hasattr(viewer, "isAnyItemCollapsable"):
            return viewer.isAnyItemCollapsable()
        return False


# # # Exemple d'utilisation (à adapter à ton application)
# # if __name__ == '__main__':
# #     import tkinter as tk
# #     import tkinter.ttk as ttk
# #
# #     class DummyViewer(ttk.Frame):
# #         def __init__(self, parent, title):
# #             super().__init__(parent)
# #             self.title_str = title
# #             self.label = ttk.Label(self, text=f"Viewer: {title}")
# #             self.label.pack(padx=10, pady=10)
# #
# #         def title(self):
# #             return self.title_str
# #         def settingsSection(self):
# #             return "dummy"
# #         def detach(self):
# #             pass
# #         def focus_set(self):
# #             print(f"Focus set to viewer {self.title_str}")
# #
# #     class App:
# #         def __init__(self, root):
# #             self.root = root
# #             self.root.title("Viewer Container Example")
# #             self.settings = {}  # Remplacez par vos propres paramètres
# #
# #             self.container = ViewerContainer(self.root, self.settings)
# #
# #             viewer1 = DummyViewer(None, "Task Viewer")
# #             viewer2 = DummyViewer(None, "Category Viewer")
# #             self.container.addViewer(viewer1)
# #             self.container.addViewer(viewer2)
# #
# #     root = tk.Tk()
# #     app = App(root)
# #     root.mainloop()
#
# # Exemple d'utilisation (à adapter)
# if __name__ == '__main__':
#     root = tk.Tk()
#     root.title("ViewerContainer avec ttk.PanedWindow")
#
#     settings = {}  # Vos paramètres
#
#     container = ViewerContainer(root, settings)
#
#     # Créer des viewers de test (doivent être des widgets Tkinter)
#     viewer1 = tk.Text(container.paned_window, bg="lightblue")
#     viewer1.insert(tk.END, "Viewer 1 Content")
#     viewer2 = tk.Text(container.paned_window, bg="lightgreen")
#     viewer2.insert(tk.END, "Viewer 2 Content")
#
#     container.addViewer(viewer1)
#     container.addViewer(viewer2)
#
#     root.mainloop()
# Exemple d'utilisation (à adapter)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("ViewerContainer avec ttk.PanedWindow")
    settings = {}  # Vos paramètres

    container = ViewerContainer(root, settings)  # root est le parent

    # Créer des viewers de test (doivent être des widgets Tkinter)
    class DummyViewer(
        tk.Text
    ):  # Définir DummyViewer comme sous-classe de tk.Text
        def __init__(self, parent, title, *args, **kwargs):
            super().__init__(parent, *args, **kwargs)
            self.title_str = title

        def title(self):
            return self.title_str

    viewer1 = DummyViewer(
        container.paned_window, "Viewer 1", bg="lightblue"
    )  # container.paned_window est le parent
    viewer1.insert(tk.END, "Viewer 1 Content")
    viewer2 = DummyViewer(
        container.paned_window, "Viewer 2", bg="lightgreen"
    )  # container.paned_window est le parent
    viewer2.insert(tk.END, "Viewer 2 Content")

    container.addViewer(viewer1)
    container.addViewer(viewer2)
    # container.pack(fill=tk.BOTH, expand=True)  # Afficher le ViewerContainer
    container.grid(
        row=0, column=0, sticky="nsew"
    )  # Utiliser grid pour afficher le ViewerContainer
    root.mainloop()
