# Il s'agit d'une classe de base très importante, je vais procéder étape par étape.
# 1. Analyse du Fichier et Identification des Composants à Convertir
# Après avoir examiné le code source de base.py,
# voici les principaux points à considérer pour la conversion :
#
# Héritage : La classe Viewer hérite de wx.Panel et patterns.Observer.
#   Il faudra la faire hériter de ttk.Frame et patterns.Observer.
# Mise en Page : Utilisation de wx.BoxSizer pour organiser les éléments.
#   Cela devra être remplacé par pack, grid ou place de Tkinter.
# Gestion des Événements : Nombreux événements wx.EVT_XXX utilisés.
#   Il faudra trouver les équivalents Tkinter et adapter la syntaxe de Bind.
# Toolbar : Utilisation d'une classe toolbar.ToolBar qui semble être spécifique à wxPython.
#   Il faudra adapter ou remplacer cette classe.
# ImageList : Utilisation de wx.ImageList pour gérer les images.
#   Il faudra utiliser tkinter.PhotoImage.
# Abstract Methods : Les méthodes domainObjectsToView et createWidget sont abstraites
# et doivent être implémentées par les sous-classes.
# PubSub : Le code utilise pubsub. Il faudra le conserver tel quel,
# à condition qu'il soit compatible avec Tkinter.
# ToolTipMixin: Le code fait référence à ToolTipMixin, il faudra aussi l'intégrer.

# Conclusion
#
# Ce code fournit un point de départ solide pour la classe Viewer en Tkinter.
# Les principales modifications consistent à
# remplacer les classes de widgets wxPython (wx.Panel, wx.BoxSizer, wx.CallAfter)
# par leurs équivalents Tkinter (ttk.Frame, pack, after).
#
# Les points cruciaux à noter pour la suite de la migration sont :
#
#     Gestion des événements : Tkinter utilise des méthodes bind pour les événements,
#       ce qui remplace le système d'événements de wxPython.
#
#     Création des widgets : Les méthodes createWidget et createImageList
#       sont des points d'entrée essentiels qui devront être implémentés
#       dans chaque sous-classe pour définir le widget spécifique
#       (par exemple, un ttk.Treeview pour une vue arborescente).
#
#     Intégration des mixins : Les mixins devront être adaptés
#       pour ne pas dépendre des classes wxPython.
#
#     Communication : Le module pubsub est maintenu pour la communication
#       inter-modules, ce qui facilite la transition.
#
# L'étape suivante serait de convertir un des fichiers de viewer concrets,
# comme task.py, en se basant sur cette nouvelle classe Viewer.
# Fais-moi savoir si tu souhaites que je m'attaque à l'un de ces fichiers.


# Explications des changements :
#
# ViewerWithColumns.showColumn :
#   J'ai commenté les lignes self.widget.showColumn(column, show)
#   et self.settings.set(...) car elles sont spécifiques à wxPython.
#   Il faudra les remplacer par le code Tkinter équivalent
#   pour manipuler la visibilité des colonnes dans le Treeview
#   et sauvegarder les paramètres.

# SortableViewerWithColumns :
#   J'ai commenté les lignes self.widget.showSortColumn(column)
#   et self.widget.showSortOrder(self.imageIndex[self.getSortOrderImage()])
#   car elles sont spécifiques à wxPython.
#   Il faudra les remplacer par le code Tkinter équivalent
#   pour afficher l'icône de tri dans l'en-tête de la colonne.
#
#
#
# Points Importants :
#
# Gestion des Colonnes : Le plus gros défi est d'adapter la gestion
#   des colonnes du wx.ListCtrl (ou wx.TreeListCtrl) à tkinter.ttk.Treeview.
#   Cela implique de manipuler les en-têtes de colonnes, les largeurs, et la visibilité.
# Icônes de Tri : Afficher les icônes de tri dans les en-têtes de colonnes
#   demandera un peu de code supplémentaire. Tu peux utiliser des images Tkinter
#   (PhotoImage) pour les icônes, et les afficher en utilisant la méthode heading du Treeview.
# Drag and Drop : L'implémentation de la validation du Drag and Drop
#   dépendra du widget que tu utilises pour afficher les données.
#
# Prochaines Étapes :
#
# Implémente la Gestion des Colonnes dans Treeview :
#   Remplace les commentaires # A adapter pour Tkinter dans ViewerWithColumns.showColumn
#   par le code Tkinter pour afficher ou masquer les colonnes.
# Gère les Icônes de Tri :
#   Remplace les commentaires # A adapter pour Tkinter dans SortableViewerWithColumns
#   par le code Tkinter pour afficher les icônes de tri.
# Teste le Code : Adapte les exemples d'utilisation pour tester le code.
# Continue la Conversion : Adapte les autres fichiers en suivant les mêmes principes.
#
# J'ai essayé de rechercher des informations spécifiques dans les fichiers que vous avez fournis, mais je n'ai pas trouvé de résultats pertinents concernant la conversion vers Tkinter.

import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type
import tkinter as tk

# import tkinter.ttk as ttk
from tkinter import ttk, PhotoImage
from abc import ABC, abstractmethod
from pubsub import pub  # pip install PyPubSub
from taskcoachlib import patterns, command, render  # , widgetstk
from taskcoachlib.config import settings
from taskcoachlib.i18n import _
from taskcoachlib.guitk.uicommand import uicommandtk as uicommand
from taskcoachlib.guitk import toolbarttk, artprovidertk
from taskcoachlib.guitk.viewer import mixintk  # Import relatif
from taskcoachlib.widgetstk import itemctrltk
from taskcoachlib.widgetstk.tooltiptk import ToolTip

from taskcoachlib.help.balloontipstk import (
    BalloonTipManager,
)  # contient AddBalloonTip

log = logging.getLogger(__name__)


# La classe PreViewer et la gestion des métaclasses ont été simplifiées
# pour Tkinter, car la complexité de wxPython n'est pas nécessaire ici.
# On utilise une approche plus simple avec une classe de base abstraite.

# Ordre d’appel des __init__ / initLayout (Viewer et mixins)
# Situation actuelle
#
# Viewer.__init__ (dans basetk.py) crée d’abord la présentation, puis appelle self.initLayout().
# Dans CategoryViewer (categorytk.py),
# createWidget crée un TreeListCtrl avec les colonnes self._columns = self.createColumns().

# Donc, pour la vue catégories :
#
# BaseCategoryViewer.__init__ appelle super().__init__, ce qui finit dans Viewer.__init__.
# Viewer.__init__ appelle initLayout, qui finit par appeler createWidget.
# CategoryViewer.createWidget crée le TreeListCtrl après avoir créé les colonnes.
# ✅ L’ordre est donc logique : les colonnes sont créées avant le TreeListCtrl.


# class Viewer(ttk.Frame, patterns.Observer, ABC):
class Viewer(ttk.Frame, patterns.Observer):
    """
    Classe de base pour les visionneuses dans Task Coach (Tkinter).

    Une visionneuse affiche les objets du domaine
    (par exemple, les tâches ou les efforts)
    au moyen d'un widget comme un Listbox ou un Treeview.
    Cette classe gère la présentation
    et l'interaction avec ces objets.

    Attributs :
        defaultTitle (str) : Le titre par défaut de la visionneuse.
        defaultBitmap (str) : L'icône par défaut pour la visionneuse.
        viewerImages (list) : Les images utilisées pour afficher les objets de la visionneuse.
    """

    defaultTitle = "Subclass responsibility"
    defaultBitmap = "Subclass responsibility"
    # Les images seront gérées par un ArtProvider adapté à Tkinter
    viewerImages = artprovidertk.itemImages

    def __init__(self, parent, taskFile, settings, *args, **kwargs):
        """
        Initialise une nouvelle visionneuse.

        Args :
            parent (tk.Widget) : Le widget parent de la visionneuse.
            taskFile (TaskFile) : Le fichier de tâches à visualiser.
            settings (Settings) : Les paramètres de l'application.
            *args : Arguments supplémentaires.
            **kwargs : Arguments nommés supplémentaires.
        """
        log.debug(
            f"Viewer.__init__ : Initialisation d'une nouvelle visionneuse self={self.__class__.__name__} avec parent={parent}."
        )
        ttk.Frame.__init__(self, parent)  # Initialisation de ttk.Frame
        # ttk.Frame.__init__(self, parent, *args, **kwargs)  # Initialisation de ttk.Frame
        # init du Frame avant ou après l'Observer ?  Après.
        patterns.Observer.__init__(self)  # initialisation de Observer

        self.parent = parent  # window or frame ?
        self.taskFile = taskFile
        self.settings = settings
        self.__settingsSection = kwargs.pop("settingsSection")
        self.__freezeCount = 0
        # The how maniest of this viewer type are we? Used for settings
        # Le quel plus grand nombre de ce type de visualiseur avons-nous? Utilisé pour les paramètres
        # self.__instanceNumber = kwargs.pop("instanceNumber")
        # KeyError: 'instanceNumber'
        self.__instanceNumber = kwargs.pop("instanceNumber", 0)
        self.__use_separate_settings_section = kwargs.pop(
            "use_separate_settings_section", True
        )

        # Selection cache:
        self.__curselection = []
        # Indicateur pour que nous n'informions pas les observateurs pendant que nous sélectionnons tous les éléments
        self.__selectingAllItems = False

        self._popupMenus = []  # Menus contextuels

        # Le widget de la barre d'outils sera créé par un module adapté
        # Le widget principal (par exemple, Treeview) doit être créé par la sous-classe TreeViewer
        # Présentation :
        self.__presentation = self.createSorter(
            self.createFilter(self.domainObjectsToView())
        )

        # En résumé, l'erreur principale est un problème de hiérarchie de widgets Tkinter.
        # La solution est de s'assurer que tu crées les widgets dans le bon ordre
        # (Parent d'abord, puis Enfant) et que tu passes le bon widget parent lors de l'instanciation.
        # # Widget pour la présentation :
        # self.widget = self.createWidget()  # Initialize self.widget to None  # -> déplacer dans initLayout
        # # efforttk.Effortviewer.createWidget, crée VirtualListCtrl
        # *** CHANGEMENT ***
        # Initialiser les widgets à None. Ils seront créés dans initLayout.
        self._sizer = None
        self.toolbar = None
        # log.debug(
        #     f"Viewer.__init__ : crée le widget {self} avec parent={parent}."
        # )
        # self.widget = self.createWidget(
        #     parent
        # )  # Crée le widget pour afficher les objets.(Taskviewer,...)
        #
        # # self.widget.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        # self.widget.grid(row=1, column=0, sticky="news")
        # !!! self.widget est aussi créé dans initLayout dans un parent=_sizer ! ?
        # Appeler initLayout MAINTENANT pour créer la structure.
        self.initLayout()

        # self.toolbar = toolbarttk.ToolBar(self, settings, (16, 16))  # -> déplacer dans initLayout
        # # self.toolbar.pack(fill="both", side="top", expand=True)  # -> déplacer dans initLayout
        # self.initLayout()
        self.registerPresentationObservers()
        # self.createWidget()  # Call createWidget to instantiate self.widget
        # Déjà instancié !, pourquoi l'appeler ?
        self.refresh()

        pub.subscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.subscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.subscribe(self.onEndIO, "taskfile.justRead")
        pub.subscribe(self.onEndIO, "taskfile.justCleared")
        pub.subscribe(self.onEndIO, "taskfile.justSaved")

        # Gestion des info-bulles (à adapter pour Tkinter)
        # Tkinter n'a pas de ToolTipMixin intégré, il faudrait le créer
        # ou utiliser une bibliothèque externe comme "tooltiptk".

        # Tooltips (à adapter si ToolTipMixin est utilisé)
        # if isinstance(self.widget, ToolTipMixin):  # si widget est une instance de ToolTipMixin
        if isinstance(
            self.widget, ToolTip
        ):  # si widget est une instance de ToolTipMixin
            # Informer l'utilisateur
            pub.subscribe(
                self.onShowTooltipsChanged, "settings.view.descriptionpopups"
            )
            # Régler les infos du widget
            self.widget.SetToolTipsEnabled(
                settings.getboolean("view", "descriptionpopups")
            )

        # tk.callAfter(self.__DisplayBalloon)  # Utilisation de tk.callAfter
        self.after(0, self.__DisplayBalloon)  # Utilisation de tk.after
        log.debug(
            f"Viewer.__init__ : La nouvelle visionneuse self={self.__class__.__name__} est initialisée !"
        )

    def __DisplayBalloon(self):
        """Affiche une info-bulle pour informer l'utilisateur que la barre d'outils est personnalisable."""
        # AuiFloatingFrame is instantiated from framemanager, we can't derive it from BalloonTipManager
        if self.toolbar.winfo_ismapped() and hasattr(
            self.winfo_toplevel(), "AddBalloonTip"
        ):  # Tests avec winfo
            self.winfo_toplevel().AddBalloonTip(  # Utilisation de self.winfo_toplevel()
                self.settings,
                "customizabletoolbars",
                self.toolbar,
                title=_("Toolbars are customizable"),
                getRect=lambda: (
                    0,
                    0,
                    28,
                    16,
                ),  # Rect factice, car on ne peut pas vraiment obtenir la position du Tool
                message=_(
                    """Click on the gear icon on the right to add buttons and rearrange them."""
                ),
            )

    def onShowTooltipsChanged(self, value):
        """Gère le changement de l'état des info-bulles."""
        self.widget.ToolTipsEnabled(
            value
        )  # A adapter si ToolTipMixin est utilisé
        # pass  # Enlever ? TODO

    def onBeginIO(self, taskFile):
        """Débute les opérations de lecture/écriture dans le fichier de tâches."""
        self.__freezeCount += 1
        self.__presentation.freeze()
        # # La méthode freeze() doit être implémentée dans les sous-classes
        # # ou dans le widget lui-même
        # if hasattr(self.widget, 'freeze'):
        #     self.widget.freeze()

    def onEndIO(self, taskFile):
        """Termine les opérations de lecture/écriture dans le fichier de tâches."""
        self.__freezeCount -= 1
        # if hasattr(self.widget, 'thaw'):
        #     self.widget.thaw()
        self.__presentation.thaw()
        if self.__freezeCount == 0:
            self.refresh()

    def activate(self):
        """Active la visionneuse, lui donnant le focus."""
        if self.widget:
            self.widget.focus_set()
        # pass

    # ## Explication détaillée
    # 1. **Méthode abstraite** : La classe de base définit
    #       `domainObjectsToView()` comme une méthode abstraite qui doit
    #       être implémentée par toutes les classes dérivées. comme Noteviewer
    # 2. **Objectif de la méthode** : Elle permet à chaque visualiseur
    #       de spécifier quel type d'objets de domaine doit être affiché
    #       (tâches, notes, efforts, etc.).
    # 3. **Implémentation pour Noteviewer** : Pour un visualiseur de notes,
    #       la méthode doit retourner `self.taskFile.notes()`,
    #       qui est la collection de toutes les notes dans le fichier de tâches.
    # 4. **Architecture** : Cette approche permet une architecture flexible
    #       où chaque visualiseur peut afficher différents types d'objets
    #       sans modifier la classe de base.
    def domainObjectsToView(self):
        """Retourne les objets du domaine que cette visionneuse doit afficher.
        Doit être implémentée dans les sous-classes.

        Renvoie les objets de domaine que cette visionneuse doit afficher.
        Pour les visualiseurs globaux, cela fera partie du fichier de tâches,
        par ex. self.taskFile.tasks(), pour les visualiseurs locaux, ce sera une liste
        d'objets transmis au constructeur du visualiseur.
        À implémenter."""
        raise NotImplementedError

    def registerPresentationObservers(self):
        """Enregistre les observateurs pour suivre les changements dans la présentation."""
        self.removeObserver(self.onPresentationChanged)
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().addItemEventType(),
            eventSource=self.presentation(),
        )
        self.registerObserver(
            self.onPresentationChanged,
            eventType=self.presentation().removeItemEventType(),
            eventSource=self.presentation(),
        )
        self.registerObserver(self.onNewItem, eventType="newitem")
        # # Les observateurs sont gérés par la classe Observer, pas besoin de les recréer
        # pass

    def detach(self):
        """Doit être appelé par viewer.container avant de fermer la visionneuse."""
        observers = [self, self.presentation()]
        observable = self.presentation()
        while True:
            try:
                observable = observable.observable()
            except AttributeError:
                break
            else:
                observers.append(observable)

        for observer in observers:
            try:
                observer.removeInstance()
            except AttributeError:
                pass  # Ignore observables that are not an observer themselves

        for popupMenu in self._popupMenus:
            if popupMenu:
                popupMenu.clearMenu()  # A adapter si la classe menu est conservée
                popupMenu.Destroy()
                # pass
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToRead")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToClear")
        pub.unsubscribe(self.onBeginIO, "taskfile.aboutToSave")
        pub.unsubscribe(self.onEndIO, "taskfile.justRead")
        pub.unsubscribe(self.onEndIO, "taskfile.justCleared")
        pub.unsubscribe(self.onEndIO, "taskfile.justSaved")

        self.presentation().detach()
        self.toolbar.detach()
        # self.toolbar.destroy()
        # # Destruction des menus contextuels
        # for menu in self._popupMenus:
        #     menu.destroy()

    #         self.destroy() # Détruit le Frame Tkinter

    def viewerStatusEventType(self):
        """Retourne le type d'événement à utiliser pour les mises à jour de statut."""
        return f"viewer{id(self)}.status"

    def sendViewerStatusEvent(self):
        """Envoie un événement pour indiquer que l'état de la visionneuse a changé."""
        pub.sendMessage(self.viewerStatusEventType(), viewer=self)

    def statusMessages(self):
        return "", ""

    def title(self):
        """Retourne le titre actuel de la visionneuse."""
        return (
            self.settings.get(self.settingsSection(), "title")
            or self.defaultTitle
        )

    def setTitle(self, the_title):
        """Modifie le titre de la visionneuse."""
        titleToSaveInSettings = (
            "" if the_title == self.defaultTitle else the_title
        )
        self.settings.set(
            self.settingsSection(), "title", titleToSaveInSettings
        )
        # self.parent.setPaneTitle(self, title) # setPaneTitle is for frame ! not window. SetLabel or SetName for window !
        # self.parent.manager.Update() # L'affichage

        # L'affichage du titre dépendra du conteneur Tkinter
        # Par exemple, si le parent est une fenêtre, on pourrait faire parent.title(title)
        # self.parent.title(the_title)  # A adapter pour tkinter
        # TODO : Mais si le parent est un widget, comment faire ?
        # Si le parent a une méthode 'title', on l’utilise
        if hasattr(self.parent, "title"):
            self.parent.title(the_title)
        # Sinon, on cherche un moyen visuel dans le widget lui-même
        elif hasattr(self, "label_title"):
            self.label_title.config(text=the_title)
        else:
            # On garde le titre en mémoire, au moins
            self.currentTitle = the_title

    def initLayout(self):
        """
        Initialise la mise en page de la visionneuse.

        Crée _sizer, toolbar, et widget dans la bonne hiérarchie.
        !!! TRES IMPORTANT !!!
        """
        log.debug(
            f"Viewer.initLayout : Initialisation de la mise en page de la visionneuse {self.__class__.__name__} title:{self.title()}."
        )
        # 1. Créer le sizer principal, enfant de 'self'
        self._sizer = tk.Frame(self)  # Utilisation de Frame pour le sizer
        # self._sizer.pack(side="top", fill="both", expand=True)  # Gérez votre layout avec pack, grid ou place
        self._sizer.grid(
            row=0, column=0, sticky="news"
        )  # Utilisation de grid pour le layout

        # 2. Créer la barre d'outils, enfant de 'self._sizer'
        # self.toolbar = toolbarttk.ToolBar(self._sizer, self.settings, (16, 16))
        # CHANGEMENT : On passe 'self._sizer' comme parent, et 'self' (le Viewer) comme window
        self.toolbar = toolbarttk.ToolBar(
            self._sizer, self, self.settings, (16, 16)
        )
        # ToolBar sera créé à l'intérieur de self._sizer, mais
        # il communiquera avec self (le Viewer) pour obtenir les informations dont il a besoin.
        #
        # Cette erreur est très courante lors de la conversion de code.
        # C'est une excellente étape de franchie pour bien séparer la structure de l'interface
        # (la hiérarchie des widgets) de la logique de l'application (qui fait quoi).
        # Ajout de la toolbar
        # self._sizer.add(self.toolbar, flag=wx.EXPAND)
        # Utilisation de pack() pour la disposition verticale
        # self.toolbar.pack(in_=self._sizer, fill=tk.X, expand=False)  # Remplissage horizontal, pas d'expansion verticale
        # # self.toolbar.pack(fill=tk.X, expand=False, pady=5)
        # self.toolbar.pack(fill=tk.X, expand=False, side=tk.TOP)
        self.toolbar.grid(
            row=0, column=0, sticky="ewn"
        )  # Positionnement en haut

        # log.debug(
        #     f"Viewer.__init__ : crée le widget {self} avec parent={parent}."
        # )
        # self.widget = self.createWidget(
        #     parent
        # )  # Crée le widget pour afficher les objets.(Taskviewer,...)
        #
        # # self.widget.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        # self.widget.grid(row=2, column=2, sticky="news")

        # 3. Créer le widget principal, enfant de 'self._sizer'
        #    On passe self._sizer comme parent à la méthode createWidget
        # self.widget = self.createWidget(self._sizer)
        self.widget = self.createWidget(parent=self._sizer)
        log.debug(
            f"Viewer.__init__ : crée le widget {self} avec parent={self._sizer}."
        )
        # Ajout du widget principal
        # 4. Packer le widget principal à l'intérieur de 'self._sizer'
        # # self._sizer.Add(self.widget, proportion=1, flag=wx.EXPAND)
        # self.widget.pack(in_=self._sizer, fill=tk.BOTH, expand=True)  # Remplissage horizontal et vertical, expansion
        # self.widget.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.widget.grid(row=1, column=0, sticky="new")
        # if hasattr(self.widget, "GetCanvas"):
        #     self.widget.GetCanvas().pack(padx=10, pady=10, expand=True, fill="both")
        # else:
        #     self.widget.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        # En Tkinter, un widget (comme un bouton, un cadre, ou ta liste)
        # ne peut être "packé" (placé) que à l'intérieur de son parent direct.
        # Le parent est le widget que tu passes comme premier argument lors de sa création
        # (par exemple mon_cadre = tk.Frame(fenetre_principale)).
        #
        # L'erreur dit que tu essaies de packer ton widget (.!...virtualistctrl)
        # à l'intérieur d'un autre widget (.!...frame ou self._sizer) qui n'est pas son parent.

        # 5. Packer le sizer principal pour qu'il remplisse 'self'
        # self._sizer.pack(expand=True, fill="both")  # Mise en place finale du sizer

        # Tentative de configuration du background avec gestion d'erreur
        try:
            # self.widget.configure(background="#f0f0f0")  # Couleur par défaut (à adapter)
            self.widget.config(
                background="#f0f0f0"
            )  # Couleur par défaut (à adapter)
        except tk.TclError:
            # Pour les widgets ttk, utiliser le système de style
            if isinstance(self.widget, ttk.Widget):
                style = ttk.Style()
                widget_class = self.widget.winfo_class()
                style_name = f"Custom.{widget_class}"
                try:
                    style.configure(style_name, background="#f0f0f0")
                    self.widget.configure(style=style_name)
                except tk.TclError:
                    # Certains widgets ttk ne supportent même pas les styles personnalisés
                    pass
        log.debug(
            f"Viewer.initLayout : initLayout de {self.__class__.__name__} terminé."
        )

    # @abstractmethod  # Laisser @abstractmethod si ABC est utilisé
    # def createWidget(self, *args):
    def createWidget(self, parent):  # CHANGEMENT: Ajout de 'parent'
        """Crée le widget utilisé pour afficher les objets.
        (penser à gérer sa géométrie)
        À implémenter dans les sous-classes."""
        raise NotImplementedError

    def createImageList(self):
        """Crée une liste d'images Tkinter et un index des images."""
        # TODO : Voir si cela fonctionne !
        size = (16, 16)
        # # Récupérer la taille de l'image (doit être implémentée)
        # size = self.getImageSize()
        # imageList = wx.ImageList(*size)
        imageList = []

        # for index, image in enumerate(self.viewerImages):
        #     try:
        #         imageList.Add(wx.ArtProvider_GetBitmap(image, wx.ART_MENU, size))
        #     except:
        #         print(image)
        #         raise
        #     self.imageIndex[image] = index
        # return imageList

        # return {}  # A adapter

        # Tkinter n'a pas d'ImageList comme wxPython.
        # Les images doivent être chargées individuellement avec PhotoImage.
        # Cette méthode pourrait retourner un dictionnaire de PhotoImage.
        # Dictionnaire de mapping pour associer le nom de l'image à son index dans la liste
        self.imageIndex = {}
        images = {}
        # LIGNE CORRIGÉE : Utiliser enumerate pour générer l'index (image_index)
        # et itérer sur les noms (image_name).
        # for image_index, image_name in self.viewerImages:
        for image_index, image_name in enumerate(self.viewerImages):
            # # Supposons qu'un ArtProvider pour Tkinter existe
            # # img_path = artprovidertk.get_image_path(image_name)
            # img_path = artprovidertk.art_provider_tk.GetBitmap(image_name)
            # # img_path = artprovidertk.art_provider_tk.GetIcon(image_name)
            # images[image_name] = PhotoImage(file=img_path)
            # self.imageIndex[image_name] = image_index
            # # self.imageIndex[image_name] = images[image_name]
            # Récupérer l'icône via ArtProvider
            # artprovidertk.getIcon(name, size) doit retourner un objet PhotoImage ou None
            image = artprovidertk.getIcon(image_name, size)
            if image:
                imageList.append(image)
                self.imageIndex[image_name] = (
                    image_index  # Mapper le nom à l'index généré
                )
            else:
                # Gérer les cas où l'icône n'est pas trouvée (pour ne pas casser l'index)
                log.warning(
                    f"Image {image_name} non trouvée dans ArtProvider."
                )
        # return images
        log.debug(
            f"Viewer.createImageList : Liste d'image créée : {imageList}"
        )
        return imageList

    def getWidget(self):
        return self.widget

    def focus_set(self, *args, **kwargs):
        """Définit le focus sur le widget."""
        if self.widget:
            self.widget.focus_set(*args, **kwargs)

    def createSorter(self, collection):
        """Crée un trieur pour organiser la présentation.

        Cette méthode peut être remplacée pour décorer la présentation avec un trieur.
        """
        return collection

    def createFilter(self, collection):
        """Crée un filtre pour organiser la présentation.
        Cette méthode peut être remplacée pour décorer la présentation avec un trieur.
        """
        return collection

    def onAttributeChanged(self, newValue, sender):
        """Gère les changements d'attribut."""
        if self:
            self.refreshItems(sender)

    def onAttributeChanged_Deprecated(self, event):
        """Gère les changements d'attributs (obsolète)."""
        self.refreshItems(*event.sources())

    def onNewItem(self, event):
        """Sélectionne un nouvel élément ajouté à la présentation."""
        self.select(
            [
                item
                for item in list(event.values())
                if item in self.presentation()
            ]
        )

    def onPresentationChanged(self, event):
        """
        Gère les changements dans la présentation.

        Chaque fois que notre présentation est modifiée (éléments ajoutés,
        éléments supprimés), la visionneuse se rafraîchit.
        """

        def itemsRemoved():
            return event.type() == self.presentation().removeItemEventType()

        def allItemsAreSelected():
            return set(self.__curselection).issubset(set(event.values()))

        self.refresh()
        if itemsRemoved() and allItemsAreSelected():
            self.selectNextItemsAfterRemoval(list(event.values()))
        self.updateSelection(sendViewerStatusEvent=False)
        self.sendViewerStatusEvent()

    def selectNextItemsAfterRemoval(self, removedItems):
        raise NotImplementedError

    def onSelect(self, event=None):
        """Gère la sélection d'éléments et les changements de sélection."""
        # if self.__selectingAllItems:
        #     return
        # self.updateSelection()
        # # ou :
        # try:
        # if self.IsBeingDeleted() or self.__selectingAllItems:
        if self.destroy() or self.__selectingAllItems:  # TODO : A vérifier !
            return

        #     tk.callAfter(self.updateSelection) # Assurez-vous que tous les événements Tk sont gérés
        # except RuntimeError:
        #     pass
        self.after(
            0, self.updateSelection
        )  # Assurez-vous que tous les événements Tk sont gérés

    def updateSelection(self, sendViewerStatusEvent=True):
        """Met à jour la sélection actuelle."""
        # ✅ FIX:  Utiliser self.widget.curselection() seulement si c'est un widget avec cette méthode
        # Sinon, chercher le Treeview enfant
        # self.widget.curselection() dépendra du widget utilisé
        log.debug(f"Viewer.updateSelection : self.widget={self.widget}")
        # # newSelection = self.widget.curselection()  # A adapter en fonction du type de widget
        # if isinstance(self.widget, ttk.Treeview):
        #     newSelection = self.widget.selection()  # A adapter en fonction du type de widget
        # else:
        #     newSelection = self.widget.curselection()  # A adapter en fonction du type de widget
        try:
            if hasattr(self.widget, "curselection"):
                # Pour les widgets qui supportent curselection (Treeview, Listbox, etc.)
                newSelection = self.widget.curselection()
            elif hasattr(self, "_Taskviewer__tree"):
                # Pour Taskviewer:  utiliser le Treeview interne
                newSelection = self._Taskviewer__tree.selection()
            elif hasattr(self, "__tree"):
                # Généralisé pour d'autres viewers
                newSelection = self.__tree.selection()
            else:
                # Fallback:  pas de widget à sélectionner
                newSelection = []
        except AttributeError as e:
            log.warning(
                f"updateSelection:  Impossible d'obtenir la sélection:  {e}"
            )
            newSelection = []

        if newSelection != self.__curselection:
            self.__curselection = newSelection
            if sendViewerStatusEvent:
                self.sendViewerStatusEvent()

    def freeze(self):
        """Gèle la fenêtre.

        Gèle le widget (empêche les mises à jour).
        """
        # if hasattr(self.widget, 'freeze'):
        #     self.widget.freeze()
        self.widget.busy()  # A adapter en fonction du widget
        self.update()
        # pass

    def thaw(self):
        """Réactive la fenêtre.

        Réactive le widget (permet les mises à jour).
        """
        # if hasattr(self.widget, 'thaw'):
        #     self.widget.thaw()
        # self.widget.Thaw() # A adapter en fonction du widget
        self.widget.busy().forget()
        # pass

    def refresh(self, *args, **kwargs):
        """Rafraîchit les éléments affichés dans la visionneuse."""
        if self and not self.__freezeCount:
            # # Cette méthode devra être implémentée dans les sous-classes
            # # en fonction du widget (Listbox, Treeview)
            # self.widget.RefreshAllItems(len(self.presentation()))  # A adapter en fonction du widget
            # ✅ FIX:  Ne pas appeler RefreshAllItems si c'est un Frame simple
            # Vérifier si le widget a la méthode RefreshAllItems (TreeListCtrl)
            # Sinon, c'est un Frame simple - appeler _refresh_tasks() si disponible
            if hasattr(self.widget, "RefreshAllItems"):
                # Pour les widgets personnalisés (TreeListCtrl, etc.)
                # self.widget.RefreshAllItems(len(self.presentation()))
                self.widget.scheduleRefresh(len(self.presentation()))
            elif hasattr(self, "_refresh_tasks"):
                # Pour les viewers Tkinter qui implémentent _refresh_tasks
                self._refresh_tasks()
            elif hasattr(self, "refresh_items"):
                # Fallback sur refresh_items
                self.refresh_items()
            # Sinon, ne rien faire (le widget simple ne nécessite pas de refresh)
            # pass

    def refreshItems(self, *items):
        """Rafraîchit les éléments spécifiés."""
        if not self.__freezeCount:
            items = [item for item in items if item in self.presentation()]
            # # Cette méthode devra être implémentée dans les sous-classes
            # self.widget.RefreshItems(*items)  # A adapter en fonction du widget
            # ✅ FIX:  Vérifier avant d'appeler RefreshItems
            if hasattr(self.widget, "RefreshItems"):
                self.widget.RefreshItems(*items)
            elif hasattr(self, "refresh_items"):
                self.refresh_items(*items)
            # Sinon, ne rien faire
            # pass

    def select(self, items):
        """Sélectionne des éléments dans la présentation."""
        self.__curselection = items
        # if hasattr(self.widget, 'select'):
        #     self.widget.select(items)
        # self.widget.select(items) # A adapter en fonction du widget
        self.widget.selection_set(items)  # pour listbox ou Treeview

    def curselection(self):
        """Retourne la sélection actuelle dans la visionneuse."""
        return self.__curselection

    def curselectionIsInstanceOf(self, class_):
        """Vérifie si la sélection courante est une instance de class_."""
        return all(isinstance(item, class_) for item in self.curselection())

    def isselected(self, item):
        """Retourne True si l'élément donné est sélectionné."""
        return item in self.curselection()

    def select_all(self):
        """Sélectionne tous les éléments."""
        self.__selectingAllItems = True
        # if hasattr(self.widget, 'select_all'):
        #     self.widget.select_all()
        self.widget.select_all()  # A adapter en fonction du widget
        #
        # Non Direct : tree.selection_add(tree.get_children()) (Seulement pour les éléments de niveau 1)
        # Pour tous les niveaux, cela nécessite de parcourir récursivement l'arbre et d'utiliser tree.selection_add(all_item_ids).

        # On utilise after() pour simuler CallAfter() de wxPython
        # tk.callAfter(self.endOfSelectAll)
        self.after(0, self.endOfSelectAll)

    def endOfSelectAll(self):
        """Termine la sélection de tous les éléments."""
        self.__curselection = self.presentation()
        self.__selectingAllItems = False
        self.onSelect()

    def clear_selection(self):
        """Efface la sélection."""
        self.__curselection = []
        # if hasattr(self.widget, 'clear_selection'):
        #     self.widget.clear_selection()
        # self.widget.clear_selection() # A adapter en fonction du widget
        self.widget.selection_set(self.__curselection)

    def size(self):
        """Retourne la taille (nombre d'éléments).

        Retourne le nombre d'éléments dans la présentation.
        """
        # return self.widget.GetItemCount() # A adapter en fonction du widget
        return len(self.presentation()) if self.presentation() else 0
        # return 0  # Valeur par défaut

    def presentation(self):
        """Retourne les objets de domaine que cette visionneuse affiche actuellement."""
        log.debug(
            f"Viewer.presentation : renvoie les objets de domaine que la visionneuse {self.__class__.__name__} affiche actuellement : {self.__presentation}."
        )
        return self.__presentation
        # if hasattr(self, '__presentation'):
        #     return self.__presentation
        # return []

    def setPresentation(self, presentation):
        """Change the presentation of the viewer."""
        self.__presentation = presentation

    def widgetCreationKeywordArguments(self):
        return {}

    # Il semble que @abstractmethod ne fonctionne pas !?
    # @abstractmethod
    def isTreeViewer(self):
        """Indique si la vue est une vue arborescente."""
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isViewerContainer(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isShowingTasks(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isShowingEffort(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isShowingCategories(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isShowingNotes(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def isShowingAttachments(self):
        raise NotImplementedError
        # return False

    # @abstractmethod
    def visibleColumns(self):
        """
        Retourne une liste des colonnes visibles du widget.

        La colonne Subject reste toujours visible.
        """
        # return [widgetstk.itemctrltk.Column("subject", _("Subject"))]  # TODO : Adapter la classe Column
        return [itemctrltk.Column("subject", _("Subject"))]

    # @abstractmethod
    def bitmap(self):
        """Retourne le bitmap qui représente cette visionneuse."""
        return self.defaultBitmap

    def settingsSection(self):
        """Retourner la section Paramètres de cette visionneuse."""
        section = self.__settingsSection
        if self.__use_separate_settings_section and self.__instanceNumber > 0:
            section += str(self.__instanceNumber)
            if not self.settings.has_section(section):
                self.settings.add_section(
                    section, copyFromSection=self.previousSettingsSection()
                )
        return section

    def previousSettingsSection(self):
        """Retourne la section de paramètres de la visionneuse précédente de cette classe."""
        previousSectionNumber = self.__instanceNumber - 1
        while previousSectionNumber > 0:
            previousSection = self.__settingsSection + str(
                previousSectionNumber
            )
            if self.settings.has_section(previousSection):
                return previousSection
            previousSectionNumber -= 1
        return self.__settingsSection

    def hasModes(self):
        return False

    def getModeUICommands(self):
        return []

    def isSortable(self):
        return False

    def getSortUICommands(self):
        return []

    def isSearchable(self):
        return False

    def hasHideableColumns(self):
        return False

    def getColumnUICommands(self):
        return []

    def isFilterable(self):
        return False

    def getFilterUICommands(self):
        return []

    def supportsRounding(self):
        return False

    def getRoundingUICommands(self):
        return []

    def createToolBarUICommands(self):
        """UI commands to put on the toolbar of this viewer.

        Crée les commandes de l'interface utilisateur pour la barre d'outils.

        Cette méthode est destinée à être surchargée par les sous-classes pour
        fournir des boutons spécifiques à leur vue.
        """
        # Dans Tk il faut utiliser des bindings clavier et des mécanismes
        # comme bind sur les widgets et des raccourcis système via des menus,
        # plutôt que wx.AcceleratorTable ;
        # Tk gère les raccourcis au niveau des événements (<Ctrl-n>, etc.)
        # sans table d’accélérations équivalente.
        # Ces raccourcis sont créé dans createClipboardToolBarUICommands et createEditToolBarUICommands!
        # table = wx.AcceleratorTable(
        #     [
        #         (wx.ACCEL_CMD, ord("X"), wx.ID_CUT),
        #         (wx.ACCEL_CMD, ord("C"), wx.ID_COPY),
        #         (wx.ACCEL_CMD, ord("V"), wx.ID_PASTE),
        #         (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT),
        #         (wx.ACCEL_CTRL, wx.WXK_DELETE, wx.ID_DELETE),
        #     ]
        # )
        # self.SetAcceleratorTable(table)
        clipboardToolBarUICommands = self.createClipboardToolBarUICommands()
        creationToolBarUICommands = self.createCreationToolBarUICommands()
        editToolBarUICommands = self.createEditToolBarUICommands()
        actionToolBarUICommands = self.createActionToolBarUICommands()
        modeToolBarUICommands = self.createModeToolBarUICommands()

        def separator(uiCommands, *otherUICommands):
            return (None,) if (uiCommands and any(otherUICommands)) else ()

        clipboardSeparator = separator(
            clipboardToolBarUICommands,
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        creationSeparator = separator(
            creationToolBarUICommands,
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        editSeparator = separator(
            editToolBarUICommands,
            actionToolBarUICommands,
            modeToolBarUICommands,
        )
        actionSeparator = separator(
            actionToolBarUICommands, modeToolBarUICommands
        )

        return (
            clipboardToolBarUICommands
            + clipboardSeparator
            + creationToolBarUICommands
            + creationSeparator
            + editToolBarUICommands
            + editSeparator
            + actionToolBarUICommands
            + actionSeparator
            + modeToolBarUICommands
        )

    def getToolBarPerspective(self):
        return self.settings.get(self.settingsSection(), "toolbarperspective")

    def saveToolBarPerspective(self, perspective):
        self.settings.set(
            self.settingsSection(), "toolbarperspective", perspective
        )

    def createClipboardToolBarUICommands(self):
        """UI commands for manipulating the clipboard (cut, copy, paste)."""
        cutCommand = uicommand.EditCut(viewer=self)
        copyCommand = uicommand.EditCopy(viewer=self)
        pasteCommand = uicommand.EditPaste()

        # Pour remplacer une liaison d’événement de wxPython par Tkinter,
        # il faut mapper les concepts et la syntaxe d’un framework à l’autre.
        #
        # wxPython (Bind) → Tkinter (bind)
        # wxPython: widget.Bind(event, callback)
        # Tkinter: widget.bind("<Event>", callback)

        # cutCommand.Bind(self, wx.ID_CUT)
        # cutCommand.bind(self, ID_CUT)  # ? cela ou le suivant ?
        # self.bind("<cutCommand>", ID_CUT?)
        # self.bind("<cutCommand>", cutCommand)  # _tkinter.TclError: bad event type or keysym "cutCommand"
        self.bind("<Control-x>", lambda event: cutCommand.doCommand())
        # copyCommand.Bind(self, wx.ID_COPY)
        # self.bind("<copyCommand>", ID_COPY?)
        self.bind("<Control-c>", lambda event: copyCommand.doCommand())
        # pasteCommand.Bind(self, wx.ID_PASTE)
        # self.bind("<pasteCommand>", ID_PASTE?)
        self.bind("<Control-v>", lambda event: pasteCommand.doCommand())

        return cutCommand, copyCommand, pasteCommand

    def createCreationToolBarUICommands(self):
        """UI commands for creating new items."""
        return ()

    def createEditToolBarUICommands(self):
        """UI commands for editing items."""
        # Laquelle des deux est la meilleure façon de faire !
        editCommand = uicommand.Edit(viewer=self)
        self.deleteUICommand = uicommand.Delete(
            viewer=self
        )  # For unittests pylint: disable=W0201

        # editCommand.bind(self, wx.ID_EDIT)
        # self.deleteUICommand.bind(self, wx.ID_DELETE)
        self.bind("<Return>", lambda event: editCommand.doCommand())
        self.bind(
            "<Control-Delete>", lambda event: self.deleteUICommand.doCommand()
        )

        return editCommand, self.deleteUICommand

    def createActionToolBarUICommands(self):
        """UI commands for actions."""
        return ()

    def createModeToolBarUICommands(self):
        """UI commands for mode switches (e.g. list versus tree mode)."""
        return ()

    def newItemDialog(self, *args, **kwargs):
        """Ouvre une fenêtre de dialogue pour créer un nouvel item."""
        bitmap = kwargs.pop("bitmap")
        newItemCommand = self.newItemCommand(*args, **kwargs)
        newItemCommand.do()
        return self.editItemDialog(
            newItemCommand.items, bitmap, items_are_new=True
        )

    def newSubItemDialog(self, bitmap):
        """Ouvre une fenêtre de dialogue pour créer un sous-item."""
        newSubItemCommand = self.newSubItemCommand()
        newSubItemCommand.do()
        return self.editItemDialog(
            newSubItemCommand.items, bitmap, items_are_new=True
        )

    def editItemDialog(
        self, items, bitmap, columnName="", items_are_new=False
    ):
        """Ouvre la fenêtre d'édition pour un item."""
        Editor = self.itemEditorClass()
        # return Editor(wx.GetTopLevelParent(self), items, self.settings, self.presentation(), self.taskFile,
        #               bitmap=bitmap, columnName=columnName, items_are_new=items_are_new)
        return Editor(
            self.winfo_toplevel(),  # Remplacer GetTopLevelParent par winfo_toplevel
            items,
            self.settings,
            self.presentation(),
            self.taskFile,
            bitmap=bitmap,
            columnName=columnName,
            items_are_new=items_are_new,
        )

    def itemEditorClass(self):
        raise NotImplementedError

    def newItemCommand(self, *args, **kwargs):
        return self.newItemCommandClass()(self.presentation(), *args, **kwargs)

    def newItemCommandClass(self):
        raise NotImplementedError

    def newSubItemCommand(self):
        return self.newSubItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def newSubItemCommandClass(self):
        raise NotImplementedError

    def deleteItemCommand(self):
        return self.deleteItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def deleteItemCommandClass(self):
        return command.DeleteCommand

    def cutItemCommand(self):
        return self.cutItemCommandClass()(
            self.presentation(), self.curselection()
        )

    def cutItemCommandClass(self):
        return command.CutCommand

    def onEditSubject(self, item, newValue):
        command.EditSubjectCommand(items=[item], newValue=newValue).do()

    def onEditDescription(self, item, newValue):
        command.EditDescriptionCommand(items=[item], newValue=newValue).do()

    def getItemTooltipData(self, item):
        """Retourne les données de l'info-bulle pour un élément."""
        lines = [line.rstrip("\r") for line in item.description().split("\n")]
        return [(None, lines)] if lines and lines != [""] else []


class CategorizableViewerMixin(object):
    """Mixin class for categorizable viewers."""

    def getItemTooltipData(self, item):
        return [
            (
                "folder_blue_arrow_icon",
                (
                    [
                        ", ".join(
                            sorted(
                                [cat.subject() for cat in item.categories()]
                            )
                        )
                    ]
                    if item.categories()
                    else []
                ),
            )
        ] + super().getItemTooltipData(
            item
        )  # It's a mixin.


class WithAttachmentsViewerMixin(object):
    """Mixin class for viewers with attachments."""

    def getItemTooltipData(self, item):
        """Retourne les données de l'info-bulle pour un élément."""
        return [
            (
                "paperclip_icon",
                sorted([str(attachment) for attachment in item.attachments()]),
            )
        ] + super().getItemTooltipData(item)


class ListViewer(Viewer):
    """
    Classe de base pour les vues en liste.

    Interface logique attendue par VirtualListCtrl.
    Hérite de Viewer.

    Cette classe est utilisée pour afficher des objets dans une vue en liste,
    contrairement à une vue arborescente.
    Elle implémente des méthodes spécifiques pour gérer les objets sous forme de liste.
    """

    def isTreeViewer(self):
        """
        Indique si la vue est une vue arborescente.

        Returns :
            (bool) : False, car cette vue est une vue en liste et non en arbre.
        """
        return False

    def visibleItems(self):
        """
        Itère sur les éléments visibles dans la présentation.

        Yields :
            Chaque objet visible dans la présentation.
        """
        for item in self.presentation():
            yield item

    def getItemCount(self):
        """
        Retourne le nombre total d’éléments à afficher.
        """
        # raise NotImplementedError
        return len(self.presentation())

    def getItemWithIndex(self, index):
        """
        Récupère un élément spécifique dans la présentation en fonction de son index.

        Args :
            index (int) : L'index de l'élément à récupérer.

        Returns :
            L'objet à l'index spécifié.
        """
        return self.presentation()[index]

    def getItemText(self, domain_object, column_name):
        """
        Retourne le texte à afficher pour une cellule.
        """
        # raise NotImplementedError
        return domain_object.get(column_name, "")

    def getItemImage(self, domain_object, column_name=None):
        """
        (Optionnel) retourne une image Tkinter (PhotoImage).
        """
        return None

    def getItemTooltipData(self, domain_object):
        """
        Retourne le texte de l’info-bulle.
        """
        # return None
        return f"Tâche : {domain_object['task']}"

    # Si une seule de ces méthodes manque → l’affichage est incomplet ou vide.

    def getIndexOfItem(self, item):
        """
        Récupère l'index d'un élément spécifique dans la présentation.

        Args :
            item (object) : L'objet dont on souhaite connaître l'index.

        Returns :
            (int) : L'index de l'objet dans la présentation.
        """
        return self.presentation().index(item)

    def selectNextItemsAfterRemoval(self, removedItems):
        """
        Sélectionne les éléments suivants après suppression.

        Cette méthode est spécifique aux contrôles de liste où la sélection
        est gérée automatiquement après la suppression d'éléments.

        Args :
            removedItems (list) : La liste des éléments qui ont été supprimés.
        """
        pass  # Gestion automatique par les contrôles de liste.


class TreeViewer(Viewer):
    """Classe de base pour les visualiseurs en arborescence.

    Hérite de Viewer.
    """

    def __init__(self, *args, **kwargs):
        log.debug(
            "TreeViewer : Initialisation du visualiseur en arborescence."
        )
        self.__selectionIndex = 0
        super().__init__(*args, **kwargs)

        # Liaison des événements d'expansion et de collapse (à adapter pour Tkinter)
        # log.info(f"TreeViewer : Liaison des événements d'expansion.")
        # self.widget.bind(wx.EVT_TREE_ITEM_EXPANDED, self.onItemExpanded)
        # log.info(f"TreeViewer : Liaison des événements de collapse.")
        # self.widget.bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)
        # EVENEMENT SPECIFIQUE  DES ARBORESCENCES ET TABLEAUX.
        #  "<<TreeviewClose>>" : la descendance de l'élément vient d'être cachée.
        self.widget.bind("<<TreeviewOpen>>", self.onItemExpanded)
        #  "<<TreeviewOpen>>" : la descendance de l'élément vient d'être affichée.
        self.widget.bind("<<TreeviewClose>>", self.onItemCollapsed)
        #  "<<TreeviewSelect>>" : la sélection à été modifiée.
        # self.widget.bind("<<TreeviewSelect>>", self.select)  # TODO : à essayer !
        self.widget.bind(
            "<<TreeviewSelect>>", self.onSelect
        )  # TODO : à essayer !
        log.debug("TreeViewer : Initialisé !")

    def onItemExpanded(self, event):
        """Gère l'événement d'expansion d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=True)

    def onItemCollapsed(self, event):
        """Gère l'événement de collapse d'un élément."""
        self.__handleExpandedOrCollapsedItem(event, expanded=False)

    def __handleExpandedOrCollapsedItem(self, event, expanded):
        """Gère les changements d'état d'expansion ou de collapse."""
        event.Skip()
        # TODO :
        # taskcoachlib.thirdparty.customtreectrl.CommandTreeEvent.GetItem()
        treeItem = event.GetItem()  # Adapter pour Tkinter
        if treeItem == self.widget.GetRootItem():  # Adapter pour Tkinter
            return
        item = self.widget.GetItemData(treeItem)  # Adapter pour Tkinter
        item.expand(expanded, context=self.settingsSection())
        # pass  # Tout adapter

    def expandAll(self):
        """Expande tous les éléments de manière récursive."""
        for item in self.visibleItems():
            item.expand(True, context=self.settingsSection(), notify=False)

    def collapseAll(self):
        """Réduit tous les éléments de manière récursive."""
        for item in self.visibleItems():
            item.expand(False, context=self.settingsSection(), notify=False)

    def isAnyItemExpandable(self):
        """Vérifie si un élément est expansible."""
        return (
            self.widget.isAnyItemExpandable()
        )  # TODO : Normalement Adapté pour Tkinter
        # return False

    def isAnyItemCollapsable(self):
        """Vérifie si un élément est collapsable."""
        return (
            self.widget.isAnyItemCollapsable()
        )  # TODO : Normalement Adapté pour Tkinter
        # return False

    def isTreeViewer(self):
        """Indique que cette vue est une vue arborescente."""
        return True

    def select(self, items):
        """Sélectionne les éléments spécifiés et expande leurs parents."""
        for item in items:
            self.__expandItemRecursively(item)
        self.refresh()
        super().select(items)

    def __expandItemRecursively(self, item):
        """Expande les parents de l'élément donné de manière récursive."""
        parent = self.getItemParent(item)
        if parent:
            parent.expand(True, context=self.settingsSection(), notify=False)
            self.__expandItemRecursively(parent)

    def selectNextItemsAfterRemoval(self, removedItems):
        """Sélectionne les éléments suivants après la suppression."""
        parents = [self.getItemParent(item) for item in removedItems]
        parents = [
            parent for parent in parents if parent in self.presentation()
        ]
        parent = parents[0] if parents else None
        # siblings = self.get_domain_children(parent)
        log.debug(
            f"TreeViewer.selectNextItemsAfterRemoval : parent={parent}, self={self.__class__.__name__}, self.__dict__={self.__dict__}, siblings={self.children}"
        )
        # siblings = self.children(parent)  # TypeError: 'dict' object is not callable
        # sibling_list = self.children(parent)  # TypeError: 'dict' object is not callable
        sibling_list = self.get_tree_children(
            parent
        )  # TypeError: 'dict' object is not callable
        newSelection = (
            # siblings[min(len(siblings) - 1, self.__selectionIndex)]
            sibling_list[min(len(sibling_list) - 1, self.__selectionIndex)]
            # if siblings
            if sibling_list
            else parent
        )
        if newSelection:
            self.select([newSelection])

    def updateSelection(self, *args, **kwargs):
        """Met à jour la sélection courante et garde une trace de l'index sélectionné."""
        super().updateSelection(*args, **kwargs)
        curselection = self.curselection()
        if curselection:
            siblings = self.get_tree_children(
                self.getItemParent(curselection[0])
            )
            # siblings = self.children(self.getItemParent(curselection[0]))
            self.__selectionIndex = (
                siblings.index(curselection[0])
                if curselection[0] in siblings
                else 0
            )
        else:
            self.__selectionIndex = 0

    def visibleItems(self):
        """Itère sur les éléments visibles dans la présentation, y compris les enfants.

        Yields :
            Chaque élément visible et ses enfants.
        """

        def yieldItemsAndChildren(items):
            """Itère de manière récursive sur les éléments et leurs enfants."""
            sortedItems = [
                item for item in self.presentation() if item in items
            ]
            for item in sortedItems:
                yield item
                the_children = self.get_tree_children(item)
                # children = self.children(item)
                if the_children:
                    for child in yieldItemsAndChildren(the_children):
                        yield child

        for item in yieldItemsAndChildren(self.getRootItems()):
            yield item

    def getRootItems(self):
        """Retourne les éléments racines de la présentation."""
        return self.presentation().rootItems()

    def getItemParent(self, item):
        """Retourne le parent de l'élément donné."""
        return item.parent()

    def getItemExpanded(self, item):
        """Vérifie si un élément est expansé dans la vue actuelle."""
        return item.isExpanded(context=self.settingsSection())

    # def get_domain_children(self, parent=None):
    # def children(self, parent=None):
    def get_tree_children(self, parent=None):
        """Retourne les enfants d'un élément donné."""
        if parent:
            # children = parent.get_domain_children()
            the_children = parent.get_tree_children()
            if the_children:
                return [
                    child
                    for child in self.presentation()
                    if child in the_children
                ]
            else:
                return []
        else:
            return self.getRootItems()

    def getItemText(self, item):
        """Retourne le texte (sujet) associé à un élément."""
        return item.subject()


class ViewerWithColumns(Viewer):
    """Classe de Base pour des visualiseurs avec des colonnes."""

    def __init__(self, *args, **kwargs):
        """Initialise la visionneuse avec des colonnes."""
        log.debug(
            f"ViewerWithColumns.__init__ : Initialisation Création de la visionneuse avec des colonnes."
        )
        self.__initDone = False
        self._columns = []
        self.__visibleColumns = []
        self.__columnUICommands = []
        super().__init__(*args, **kwargs)
        self.initColumns()
        self.__initDone = True
        self.refresh()
        log.debug("ViewerWithColumns initialisé !")

    def hasHideableColumns(self):
        """Indique si la visionneuse a des colonnes masquables."""
        return True

    def hasOrderingColumn(self):
        """Vérifie si une colonne de tri est présente."""
        for column in self.__visibleColumns:
            if column.name() == "ordering":
                return True
        return False

    def getColumnUICommands(self):
        """Retourne les commandes de l'interface utilisateur pour gérer les colonnes."""
        if not self.__columnUICommands:
            self.__columnUICommands = self.createColumnUICommands()
        return self.__columnUICommands

    def createColumnUICommands(self):
        """Crée les commandes de l'interface utilisateur pour les colonnes."""
        raise NotImplementedError

    def refresh(self, *args, **kwargs):
        """Rafraîchit la vue si l'initialisation est terminée."""
        if self and self.__initDone:
            super().refresh(*args, **kwargs)

    def initColumns(self):
        """Initialise les colonnes de la visionneuse."""
        for column in self.columns():
            # # retirer les parenthèses pour accéder à la liste directement au lieu de tenter de l'appeler comme une fonction.
            # for column in self.columns:
            self.initColumn(column)
        if self.hasOrderingColumn():
            self.widget.SetResizeColumn(
                1
            )  # TODO : Normalement adapté pour Tkinter
            # de AutoColumnWidthMixin ! Le resize est automatique dans tkinter !
            self.widget.SetMainColumn(
                1
            )  # TODO : Normalement adapté pour Tkinter
            pass

    def initColumn(self, column):
        """Initialise une colonne et détermine si elle doit être visible."""
        if column.name() in self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        ):
            show = True
        else:
            show = column.name() in self.settings.getlist(
                self.settingsSection(), "columns"
            )
            # self.widget.showColumn(column, show=show)  # Adapter pour Tkinter
        if show:
            log.debug(
                f"ViewerWithColumns.initColumn : ajoute la colonne {type(column).__name__} aux colonnes visibles : {self.__visibleColumns}"
            )
            self.__visibleColumns.append(column)
            self.__startObserving(column.eventTypes())

    def showColumnByName(self, columnName, show=True):
        """Affiche ou masque une colonne par son nom."""
        for column in self.hideableColumns():
            if columnName == column.name():
                isVisibleColumn = self.isVisibleColumn(column)
                if (show and not isVisibleColumn) or (
                    not show and isVisibleColumn
                ):
                    self.showColumn(column, show)
                break

    def showColumn(self, column, show=True, refresh=True):
        """
        Affiche ou masque une colonne et met à jour la vue.

        Args:
            column: La colonne à afficher ou masquer.
            show (bool): True pour afficher, False pour masquer.
            refresh (bool): True pour rafraîchir la vue après l'opération.
        """
        # Remplace les commentaires # A adapter pour Tkinter
        # par le code Tkinter pour afficher ou masquer les colonnes.
        if column.name() == "ordering":
            self.widget.SetResizeColumn(
                1 if show else 0
            )  # TODO : Normalement adapté pour Tkinter
            # de AutoColumnWidthMixin ! Le resize est automatique dans tkinter !
            self.widget.SetMainColumn(
                1 if show else 0
            )  # TODO : Normalement adapté pour Tkinter
            # SetMainColumn vient de hypertreelist !
            # Sets the HyperTreeList main column (i.e. the position of the underlying CustomTreeCtrl.
            pass  # A adapter !

        if show:
            self.__visibleColumns.append(column)
            # Make sure we keep the columns in the right order:
            self.__visibleColumns = [
                c for c in self.columns() if c in self.__visibleColumns
            ]
            self.__startObserving(column.eventTypes())
        else:
            self.__visibleColumns.remove(column)
            self.__stopObserving(column.eventTypes())
            self.widget.showColumn(
                column, show
            )  # TODO : Normalement adapter pour Tkinter
        self.settings.set(
            self.settingsSection(),
            "columns",
            # str([column.id() for column in self.__visibleColumns]),
            str([column.name() for column in self.__visibleColumns]),
        )  # TODO :  Adapter column.name() pour Tkinter -> column.id ?
        if refresh:
            # self.widget.RefreshAllItems(len(self.presentation()))
            self.widget.scheduleRefresh(len(self.presentation()))
            # self.refresh()  # Utiliser refresh pour la mise à jour
            # self.widget.update()

    def hideColumn(self, visibleColumnIndex):
        """
        Masque une colonne visible par son index.

        Args:
            visibleColumnIndex (int): L'index de la colonne à masquer.
        """
        column = self.visibleColumns()[visibleColumnIndex]
        self.showColumn(column, show=False)

    def columns(self):
        """
        Retourne toutes les colonnes disponibles dans la visionneuse.

        Returns :
            (list) : Liste des colonnes.
        """
        return self._columns

    def selectableColumns(self):
        """
        Retourne les colonnes sélectionnables.

        Returns :
            (list) : Liste des colonnes sélectionnables.
        """
        return self._columns

    def isVisibleColumnByName(self, columnName):
        """
        Vérifie si une colonne est visible par son nom.

        Args:
            columnName (str): Le nom de la colonne à vérifier.

        Returns:
            (bool): True si la colonne est visible, sinon False.
        """
        return columnName in [
            column.name() for column in self.__visibleColumns
        ]

    def isVisibleColumn(self, column):
        """
        Vérifie si une colonne est visible.

        Args:
            column: La colonne à vérifier.

        Returns:
            (bool): True si la colonne est visible, sinon False.
        """
        return column in self.__visibleColumns

    # def visibleColumns(self):
    def visibleColumns(self) -> List[str]:
        """
        Retourne la liste des colonnes visibles.

        Returns :
            Liste des colonnes actuellement visibles.
        """
        # return self.__visibleColumns
        # Retourne une liste des colonnes visibles du widget.
        # La colonne Subject reste toujours visible.
        return [
            itemctrltk.Column("subject", _("Subject"))
        ]  # TODO : la classe Column est normalement adaptée maintenant !

    def hideableColumns(self):
        """
        Retourne les colonnes qui peuvent être masquées.

        Returns :
            Liste des colonnes masquables.
        """
        return [
            column
            for column in self._columns
            if column.name()
            not in self.settings.getlist(
                self.settingsSection(), "columnsalwaysvisible"
            )
        ]

    def isHideableColumn(self, visibleColumnIndex):
        column = self.visibleColumns()[visibleColumnIndex]
        unhideableColumns = self.settings.getlist(
            self.settingsSection(), "columnsalwaysvisible"
        )
        return column.name() not in unhideableColumns

    def getColumnWidth(self, columnName):
        """
        Retourne la largeur d'une colonne recherchée par son nom.

        Args:
            columnName (str): Le nom de la colonne.

        Returns:
            (int): La largeur de la colonne.
        """
        columnWidths = self.settings.getdict(
            self.settingsSection(), "columnwidths"
        )
        defaultWidth = 28 if columnName == "ordering" else 100
        return columnWidths.get(columnName, defaultWidth)

    def onResizeColumn(self, column, width):
        """
        Gère le redimensionnement d'une colonne et met à jour les paramètres.

        Args:
            column: La colonne redimensionnée.
            width (int): La nouvelle largeur de la colonne.
        """
        columnWidths = self.settings.getdict(
            self.settingsSection(), "columnwidths"
        )
        columnWidths[column.name()] = width
        self.settings.setdict(
            self.settingsSection(), "columnwidths", columnWidths
        )

    def validateDrag(self, dropItem, dragItems, columnIndex):
        """
        Valide si un élément peut être déplacé (drag and drop) dans une colonne.

        Args:
            dropItem: L'élément où l'élément est déposé.
            dragItems: Les éléments en cours de déplacement.
            columnIndex (int): L'index de la colonne affectée.

        Returns:
            (bool | None): True si le déplacement est valide, sinon False.
        """
        # return None  # TODO : A adapter
        log.debug(f"ViewerWithColumns.validateDrag est appelé.")
        if (
            columnIndex == -1
            or self.visibleColumns()[columnIndex].name() != "ordering"
        ):
            return None  # Normal behavior

        # Ordering
        # if issubclass((TreeViewer, ListViewer), self):  # à mettre ou similaire ?
        if not self.isTreeViewer():  # where come from ?
            # isTreeViewer : Cette méthode est définie dans les sous-classe TreeViewer et ListViewer.
            # Elle permet de différencier les vues arborescentes des vues en liste.
            # Ici, pour ListViewer, validateDrag doit être True !
            return True

        # # Tree mode. Only allow drag if all selected items are siblings.
        # # Mode arborescence. Autorisez la glisser si tous les éléments sélectionnés sont des frères et sœurs.
        # if len(set([item.parent() for item in dragItems])) >= 2:
        #     wx.GetTopLevelParent(self).AddBalloonTip(
        #         self.settings,
        #         "treemanualordering",
        #         self,
        #         title=_("Reordering in tree mode"),
        #         getRect=lambda: wx.Rect(0, 0, 28, 16),
        #         message=_(
        #             """When in tree mode, manual ordering is only possible when all selected items are siblings."""
        #         ),
        #     )
        #     return False

        # # S'ils sont parent, autorisez seulement la déplacer au même niveau.
        # if dragItems[0].parent() != (None if dropItem is None else dropItem.parent()):
        #     wx.GetTopLevelParent(self).AddBalloonTip(
        #         self.settings,
        #         "treechildrenmanualordering",
        #         self,
        #         title=_("Reordering in tree mode"),
        #         getRect=lambda: wx.Rect(0, 0, 28, 16),
        #         message=_(
        #             """When in tree mode, you can only put objects at the same level (parent)."""
        #         ),
        #     )
        #     return False

        return True

    def getItemText(self, item, column=None):
        """
        Retourne le texte d'un élément pour une colonne spécifique.

        Args:
            item: L'élément dont on veut obtenir le texte.
            column: La colonne à utiliser pour récupérer le texte.

        Returns:
            (str): Le texte de l'élément pour la colonne spécifiée.
        """
        if column is None:
            column = 1 if self.hasOrderingColumn() else 0
        column = self.visibleColumns()[column]
        return column.render(item)

    def getItemImages(self, item, column=0):
        """
        Retourne les images associées à un élément pour une colonne spécifique.

        Args:
            item: L'élément dont on veut obtenir les images.
            column int: L'index de la colonne.

        Returns:
            Dictionnaire des images associées à l'élément.
        """
        column = self.visibleColumns()[column]
        return column.imageIndices(item)

    def hasColumnImages(self, column):
        """
        Vérifie si une colonne contient des images.

        Args :
            column : (int?) La colonne à vérifier.

        Returns :
            (bool) : True si la colonne contient des images, sinon False.
        """
        return self.visibleColumns()[column].hasImages()
        pass  # TODO : La gestion des images est en cours de développement

    def subjectImageIndices(self, item):
        """
        Retourne les indices des images associées au sujet d'un élément.

        Args:
            item: L'élément dont on veut obtenir les indices d'images.

        Returns:
            Dictionnaire des indices d'images associés.
        """
        normalIcon = item.icon(recursive=True)
        selectedIcon = item.selectedIcon(recursive=True) or normalIcon
        normalImageIndex = self.imageIndex[normalIcon] if normalIcon else -1
        selectedImageIndex = (
            self.imageIndex[selectedIcon] if selectedIcon else -1
        )
        return {
            # wx.TreeItemIcon_Normal: normalImageIndex,  # TODO : A adapter
            # wx.TreeItemIcon_Expanded: selectedImageIndex,  # TODO : A adapter
        }

    def __startObserving(self, eventTypes):
        """
        Commence à observer les événements spécifiés pour les colonnes visibles.

        Args:
            eventTypes: Liste des types d'événements à observer.
        """
        for eventType in eventTypes:
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType=eventType
                )

    def __stopObserving(self, eventTypes):
        """
        Arrête d'observer les événements spécifiés pour les colonnes qui ne sont plus visibles.

        Args:
            eventTypes: Liste des types d'événements à arrêter d'observer.
        """
        # Collecte les types d'événements auxquels les colonnes visibles sont encore intéressées
        # Collect the event types that the currently visible columns are
        # interested in and make sure we don't stop observing those event types.
        eventTypesOfVisibleColumns = []
        for column in self.visibleColumns():
            eventTypesOfVisibleColumns.extend(column.eventTypes())
        for eventType in eventTypes:
            if eventType not in eventTypesOfVisibleColumns:
                if eventType.startswith("pubsub"):
                    pub.unsubscribe(self.onAttributeChanged, eventType)
                else:
                    self.removeObserver(
                        self.onAttributeChanged_Deprecated, eventType=eventType
                    )

    def renderCategories(self, item):
        """
        Rendre les catégories associées à un élément donné.

        Args :
            item : L'élément dont on veut afficher les catégories.

        Returns :
            (str) : Une chaîne contenant les catégories de l'élément.
        """
        return self.renderSubjectsOfRelatedItems(item, item.categories)

    def renderSubjectsOfRelatedItems(self, item, getItems):
        """
        Rendre les sujets des éléments liés (catégories ou autres relations).

        Args :
            item : L'élément pour lequel on veut afficher les sujets liés.
            getItems : (callable) Fonction pour récupérer les éléments liés.

        Returns :
            (str) : Une chaîne des sujets des éléments liés.
        """
        subjects = []
        ownItems = getItems(recursive=False)
        if ownItems:
            subjects.append(self.renderSubjects(ownItems))
        isListViewer = not self.isTreeViewer()
        if isListViewer or self.isItemCollapsed(item):
            childItems = [
                theItem
                for theItem in getItems(recursive=True, upwards=isListViewer)
                if theItem not in ownItems
            ]
            if childItems:
                subjects.append(f"({self.renderSubjects(childItems)})")
        return " ".join(subjects)

    @staticmethod
    def renderSubjects(items):
        """
        Rendre les sujets d'une liste d'éléments.

        Args :
            items : Liste des éléments dont on veut obtenir les sujets.

        Returns :
            (str) : Une chaîne contenant les sujets des éléments, triés par ordre alphabétique.
        """
        subjects = [item.subject(recursive=True) for item in items]
        return ", ".join(sorted(subjects))

    @staticmethod
    def renderCreationDateTime(item, humanReadable=True):
        """
        Rendre la date et l'heure de création d'un élément.

        Args:
            item: L'élément dont on veut afficher la date de création.
            humanReadable (bool): Indique si la date doit être formatée de manière lisible.

        Returns:
            (str): La date et l'heure de création de l'élément.
        """
        return render.dateTime(
            item.creationDateTime(), humanReadable=humanReadable
        )

    @staticmethod
    def renderModificationDateTime(item, humanReadable=True):
        """
        Rendre la date et l'heure de modification d'un élément.

        Args :
            item : L'élément dont on veut afficher la date de modification.
            humanReadable (bool) : Indique si la date doit être formatée de manière lisible.

        Returns :
            (str) : La date et l'heure de modification de l'élément.
        """
        return render.dateTime(
            item.modificationDateTime(), humanReadable=humanReadable
        )

    def isItemCollapsed(self, item):
        """
        Vérifie si un élément est réduit dans la vue actuelle (uniquement pertinent pour les vues arborescentes).

        Args:
            item: L'élément à vérifier.

        Returns:
            (bool): True si l'élément est réduit, False sinon.
        """
        return (
            not self.getItemExpanded(item)
            if self.isTreeViewer() and item.children()
            else False
        )


class SortableViewerWithColumns(
    mixintk.SortableViewerMixin, ViewerWithColumns
):
    """
    Classe SortableViewerWithColumns, héritant de ViewerWithColumns et du mixin SortableViewerMixin.
    """

    def initColumn(self, column):
        """
        Initialise une colonne et, si elle est utilisée pour le tri, affiche l'icône de tri correspondante.

        Args:
            column: La colonne à initialiser.
        """
        super().initColumn(column)
        if self.isSortedBy(column.name()):
            log.debug(
                f"SortableViewerWithColumns.initColumns : sur self.widget={self.widget}."
            )
            # self.widget.showSortColumn(column)  # TODO : Normalement adapté pour Tkinter
            # Actuellement 02/12/2025 showSortColumn Ne fonctionne pas !
            pass
        self.showSortOrder()

    def setSortOrderAscending(self, *args, **kwargs):
        """
        Définit l'ordre de tri en croissant et met à jour l'affichage de l'icône de tri.

        Args :
            *args: Arguments supplémentaires pour la méthode de tri.
            **kwargs: Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().setSortOrderAscending(*args, **kwargs)
        self.showSortOrder()

    def sortBy(self, *args, **kwargs):
        """
        Trie les éléments de la visionneuse par une colonne spécifique et met à jour l'affichage de l'icône de tri.

        Args:
            *args: Arguments supplémentaires pour la méthode de tri.
            **kwargs: Arguments nommés supplémentaires pour la méthode de tri.
        """
        super().sortBy(*args, **kwargs)
        # self.showSortColumn()  # TODO : A adapter pour Tkinter
        self.showSortOrder()

    def showSortColumn(self):
        """
        Affiche la colonne actuellement utilisée pour le tri, avec l'icône correspondante.
        """
        for column in self.columns():
            if self.isSortedBy(column.name()):
                log.debug(
                    f"SortableViewerWithColumns.showSortColumn : sur self.widget={self.widget}."
                )
                self.widget.showSortColumn(
                    column
                )  # TODO : Normalement adapté pour Tkinter
                break

    def showSortOrder(self):
        """
        Affiche l'icône indiquant l'ordre du tri (ascendant ou descendant) dans la visionneuse.
        """
        # self.widget.showSortOrder(self.imageIndex[self.getSortOrderImage()][0])  # A adapter pour Tkinter
        pass

    def getSortOrderImage(self):
        """
        Retourne l'image associée à la direction du tri.

        Returns :
            (str) : Le nom de l'icône pour indiquer le tri ascendant ou descendant.
        """
        return (
            "arrow_up_icon"
            if self.isSortOrderAscending()
            else "arrow_down_icon"
        )


# Explications et adaptations nécessaires :
#
# Importations : Assure-toi que toutes les classes et modules nécessaires sont importés, y compris tkinter, ttk, artprovidertk, et tes propres classes de viewers.
# Initialisation de Tkinter : Crée une instance de tk.Tk() pour la fenêtre principale.
# Simulation des données : La démo nécessite des instances de TaskFile et Settings. J'ai inclus des simulations minimales. Tu devras les remplacer par tes vraies instances.
# Création des Viewers :
#
# Crée des classes qui héritent de ListViewer ou TreeViewer. Implémente les méthodes abstraites comme createWidget et domainObjectsToView.  createWidget doit créer une instance du widget Tkinter que tu utilises (par exemple, ttk.Treeview ou tk.Listbox).  domainObjectsToView doit retourner une liste d'objets que ton viewer affichera.
# Instancie tes classes de viewer et ajoute-les au ttk.Notebook.
#
#
# ArtProvider : L'exemple utilise artprovidertk pour charger les icônes.
# Vérifie que l'ArtProvider est correctement initialisé et que les icônes sont disponibles.
# Boucle principale : Lance la boucle principale Tkinter avec root.mainloop().
#
# Points importants :
#
# Remplace les classes MonListViewer et MonTreeViewer par tes propres classes de viewers.
# Adapte les méthodes createWidget et domainObjectsToView pour afficher tes données réelles.
# Assure-toi que les icônes spécifiées dans defaultBitmap existent dans ton catalogue d'icônes.

# Démonstration et tests
if __name__ == "__main__":
    # import tkinter as tk
    # from tkinter import ttk
    # from taskcoachlib.guitk import artprovidertk
    from taskcoachlib.config import settings
    from taskcoachlib.persistencetk.taskfile import TaskFile

    # Initialisation de Tkinter
    root = tk.Tk()
    root.title("Démonstration des Viewers Task Coach (Tkinter)")

    # Création d'un Notebook pour afficher plusieurs viewers
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # # Simulation des objets taskFile et settings (à remplacer par vos vrais objets)
    # class MockTaskFile:
    #     pass
    # taskFile = MockTaskFile()
    taskFile = TaskFile(notebook)
    settings = settings.Settings()
    # settings.add_section("view")
    settings.set("view", "descriptionpopups", True)

    # Fonction pour ajouter un viewer au Notebook
    def ajouter_viewer(viewer_class, nom_onglet):
        viewer = viewer_class(
            notebook, taskFile, settings, settingsSection="viewer_demo"
        )
        notebook.add(viewer, text=nom_onglet)
        return viewer

    # Exemple d'utilisation avec un ListViewer (à adapter avec tes propres classes de viewer)
    # NOTE: Il faut créer une classe qui hérite de ListViewer pour que cela fonctionne
    class MonListViewer(ListViewer):
        defaultTitle = "Mon List Viewer"
        defaultBitmap = "book_icon"  # Remplace par une icône valide

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Ajoute un widget exemple pour la démonstration
            # self.widget existe déjà grâce à super().__init__()
            label = ttk.Label(
                self.widget, text="Ceci est un ListViewer de démonstration"
            )
            label.pack(padx=10, pady=10)

        # def createWidget(self):
        def createWidget(self, parent):  # CHANGEMENT: Ajout de 'parent'
            # Crée un widget (par exemple, un Treeview ou une Listbox)
            # self.widget = tk.Listbox(self)
            # self.widget = tk.Frame(self)  # Remplace par le widget approprié -> Ancien code
            frame = tk.Frame(parent)  # CHANGEMENT: Utilise 'parent'
            # Note: on ne sauvegarde pas dans self.widget ici, on le retourne.
            # La classe de base s'en occupe.
            # return self.widget
            return frame

        def domainObjectsToView(self):
            # Retourne une liste d'objets à afficher
            return [
                "Objet 1",
                "Objet 2",
                "Objet 3",
            ]  # Remplace par tes données

        def isTreeViewer(self):
            return False

        def isViewerContainer(self):
            return False

        def isShowingTasks(self):
            return False

        def isShowingEffort(self):
            return False

        def isShowingCategories(self):
            return False

        def isShowingNotes(self):
            return False

        def isShowingAttachments(self):
            return False

        def visibleColumns(self):
            return []

        def bitmap(self):
            return "book_icon"  # À remplacer par une icône valide

        def itemEditorClass(self):
            pass

        def newItemCommandClass(self):
            pass

        def newSubItemCommandClass(self):
            pass

            # Exemple d'utilisation avec un TreeViewer (à adapter)

    class MonTreeViewer(TreeViewer):
        defaultTitle = "Mon Tree Viewer"
        defaultBitmap = "folder_blue_icon"  # Remplace par une icône valide

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # # Exemple d'ajout d'un Treeview pour la démonstration
            # self.widget (le Treeview) existe déjà grâce à super().__init__()
            # Insérer des éléments dans l'arbre (exemple)
            # self.tree = ttk.Treeview(self)
            # self.tree.pack(padx=10, pady=10)
            # # Insérer des éléments dans l'arbre (exemple)
            # self.tree.insert("", "end", text="Élément racine")
            self.widget.insert("", "end", text="Élément racine")

        # def createWidget(self):
        #     self.widget = self.tree
        #     return self.widget
        def createWidget(self, parent):  # CHANGEMENT: Ajout de 'parent'
            # self.tree = ttk.Treeview(self) # Ancien code
            tree = ttk.Treeview(parent)  # CHANGEMENT: Utilise 'parent'
            # self.widget = self.tree # Ancien code
            return tree

        def domainObjectsToView(self):
            return []

        def isTreeViewer(self):
            return True

        def isViewerContainer(self):
            return False

        def isShowingTasks(self):
            return False

        def isShowingEffort(self):
            return False

        def isShowingCategories(self):
            return False

        def isShowingNotes(self):
            return False

        def isShowingAttachments(self):
            return False

        def visibleColumns(self):
            return []

        def bitmap(self):
            return "folder_blue_icon"  # À remplacer par une icône valide

        def itemEditorClass(self):
            pass

        def newItemCommandClass(self):
            pass

        def newSubItemCommandClass(self):
            pass

        def getRootItems(self):
            return []

    # Ajoute les viewers au Notebook
    list_viewer = ajouter_viewer(MonListViewer, "List Viewer Démo")
    tree_viewer = ajouter_viewer(MonTreeViewer, "Tree Viewer Démo")

    # Lancement de la boucle principale Tkinter
    root.mainloop()
