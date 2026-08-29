# -*- coding: utf-8 -*-
"""
Ce module gère la création et l'ajout de visualisateurs (viewers) à l'interface utilisateur.
Basé sur le fichier factory.py original de Task Coach.
"""

# Le fichier factory.py est une partie importante de la logique de l'application,
# car il gère l'instanciation de différents types de vues
# (TaskViewer, NoteViewer, etc.) de manière dynamique.
# La principale adaptation pour cette version Tkinter consiste à
# s'assurer que les classes addViewers et addOneViewer utilisent les bons objets de conteneur de vues (viewerContainer) et les classes de vues converties.
#
# J'ai inclus des classes de simulation pour tous les modules et classes de vues (task, effort, category, note, ViewerContainer) afin que le fichier soit autonome et puisse être exécuté pour démontrer son fonctionnement.
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Type

from taskcoachlib.config import settings

# from taskcoachlib.config.settings import settings  # erreur
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.guitk import uicommand

# Importations des classes de viewers réelles
from taskcoachlib.guitk.viewer import basetk
from taskcoachlib.guitk.viewer import categorytk
from taskcoachlib.guitk.viewer import notetk
from taskcoachlib.guitk.viewer import tasktk
from taskcoachlib.guitk.viewer import efforttk

# Importation de la classe de base Viewer
from taskcoachlib.guitk.viewer.basetk import Viewer
from taskcoachlib.i18n import _

log = logging.getLogger(__name__)


# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# def _(text: str) -> str:
#     return text
#
#
# class settings:
#     def __init__(self):
#         self._data: Dict[str, Any] = {
#             "view": {
#                 "taskviewer": "1",
#                 "noteviewer": "0",
#                 "categoryviewer": "0"
#             }
#         }
#
#     def getint(self, section: str, option: str) -> int:
#         return int(self._data.get(section, {}).get(option, "0"))


# class task:
#     class Taskviewer(ttk.Frame):
#         def __init__(self, parent: Any, settings_obj: Any, task_file: Any, **kwargs: Any):
#             super().__init__(parent, **kwargs)
#             ttk.Label(self, text="TaskViewer").pack(expand=True)
#             self._tasks_to_show = ["Tâche 1", "Tâche 2"]
#             print("TaskViewer créé.")
#
#         def isShowingTasks(self) -> bool:
#             return True
#
#         def curselection(self) -> List[Any]:
#             return []


# class effort:
#     class EffortViewerForSelectedTasks(ttk.Frame):
#         def __init__(self, parent: Any, viewerContainer: Any, **kwargs: Any):
#             super().__init__(parent, **kwargs)
#             ttk.Label(self, text="EffortViewerForSelectedTasks").pack(expand=True)
#             print("EffortViewer créé.")


# class category:
#     class Categoryviewer(ttk.Frame):
#         def __init__(self, parent: Any, settings_obj: Any, task_file: Any, **kwargs: Any):
#             super().__init__(parent, **kwargs)
#             ttk.Label(self, text="CategoryViewer").pack(expand=True)
#             print("CategoryViewer créé.")


# class note:
#     class Noteviewer(ttk.Frame):
#         def __init__(self, parent: Any, settings_obj: Any, task_file: Any, **kwargs: Any):
#             super().__init__(parent, **kwargs)
#             ttk.Label(self, text="NoteViewer").pack(expand=True)
#             print("NoteViewer créé.")


def viewerTypes() -> List[str]:
    """
    Renvoie les types de visualisateurs disponibles, en utilisant les noms
    utilisés dans les paramètres.
    """
    types = [
        "timelineviewer",
        "squaretaskviewer",
        "taskviewer",
        "taskstatsviewer",
        "noteviewer",
        "categoryviewer",
        "effortviewer",
        "calendarviewer",
        "hierarchicalcalendarviewer",
        "effortviewerforselectedtasks",
    ]
    try:
        import igraph
    except ImportError:
        pass
    else:
        types.append("taskinterdepsviewer")
    return tuple(types)


# --- CLASSE CONVERTIE ---
#  la classe addViewers n'a pas besoin de l'argument parent dans son constructeur __init__().
#  La raison en est que l'objet viewer_container lui-même
#  contient une référence à son propre widget parent (viewer_container.containerWidget)
#  qui est utilisé lors de l'initialisation des visualisateurs individuels.


# Double initialisation : Je vois deux initialisations des visionneuses dans les journaux.
# Cela se produit parce que l’initialisation des visionneuses se trouve dans la classe factory,
# mais aussi dans addViewersToContainer.
# Supprimez l’initialisation de la fabrique et
# laissez addViewersToContainer exécuter les initialisations des utilisateurs.
class addViewers:
    """
    Classe se faisant passer pour une méthode pour ajouter des visualisateurs.
    """

    floating = False

    # def __init__(self, viewer_container: Any, task_file: Any, settings: settings):
    def __init__(self, viewer_container: Any, task_file: Any, settings):
        log.debug(
            f"addViewers.__init__ : Ajoute des visualiseurs dans le viewer_container={viewer_container} avec task_file={task_file} et settings={settings}."
        )
        self.__viewer_container = viewer_container  # Conteneur de visualiseurs
        self.__task_file = task_file
        self.__settings = settings
        self.floating = (
            False  # Start viewers floating? Not when restoring layout
        )
        self.__viewer_init_args = (
            viewer_container.containerWidget,
            task_file,
            settings,
        )  # si container est mainwindow pour wx, containerWidget est Tk
        self.__add_all_viewers()
        # self.__viewer_container.__add_all_viewers()

        log.debug("addViewers.__init__ : Tout les visualiseurs sont ajoutés !")

    # def __call__(self):
    #     """Ajoute les visualisateurs à la fenêtre principale."""
    #     viewer_classes = self._viewer_classes()
    #     for viewer_class in viewer_classes:
    #         self._add_viewer(viewer_class)

    def __add_all_viewers(self):
        """Open viewers as saved previously in the settings.

        Ouvrez les visionneuses telles qu'elles ont été enregistrées précédemment dans les paramètres.
        """
        log.debug(
            "addViewers.__add_all_viewers : Ouvre toutes les visionneuses."
        )
        # self._add_viewer(notetk.Noteviewer)  # Il échoue parce que ne fournit pas d'implémentations pour les méthodes abstraites requises, comme décrit dans l'erreur console.

        # self._add_viewer(category.Categoryviewer)
        self._add_viewer(
            tasktk.Taskviewer
        )  # 24/11/2025 échoue, passe le 03/12
        # self._add_viewer(tasktk.TaskStatsViewer)  # 03/12/2025
        # self._add_viewer(tasktk.SquareTaskViewer)  # 03/12/2025 il faut trouver une alternative au module squaremap(wxpython)
        # self._add_viewer(tasktk.TimelineViewer)
        # self._add_viewer(task.CalendarViewer)
        # self._add_viewer(task.HierarchicalCalendarViewer)
        # try:
        #     import igraph
        # except ImportError:
        #     pass
        # else:
        #     self._add_viewer(task.TaskInterdepsViewer)
        # self._add_viewer(efforttk.Effortviewer)
        # self._add_viewer(effort.EffortViewerForSelectedTasks)
        # self._add_viewer(categorytk.Categoryviewer)
        # self._add_viewer(notetk.Noteviewer)  # Il échoue parce que ne fournit pas d'implémentations pour les méthodes abstraites requises, comme décrit dans l'erreur console.
        #
        # # viewer_classes: List[Type[Viewer]] = [task.Taskviewer, category.Categoryviewer, effort.Effortviewer, note.Noteviewer]
        # #
        # # for viewer_class in viewer_classes:
        # #     if self.__settings.getboolean("view", viewer_class.settingsSection()):
        # #         self._add_viewer(viewer_class)

        # Pas cela qui démarre les Viewers wxpython :
        # for viewer_type in viewerTypes():
        #     viewer_count = self._number_of_viewers_to_add(
        #         getattr(task, viewer_type.replace("viewer", "").capitalize() + "Viewer")
        #     )  # Dynamically get the viewer class
        #     for _ in range(viewer_count):
        #         viewer_class = getattr(
        #             task, viewer_type.replace("viewer", "").capitalize() + "Viewer"
        #         )  # Dynamically get the viewer class
        #         self._add_viewer(viewer_class)

        # # C'est cela qui démarre les viewers tkinter :
        # for viewer_type in viewerTypes():
        #     viewer_count = self._number_of_viewers_to_add(
        #         getattr(task, viewer_type.replace("viewer", "").capitalize() + "viewer")
        #     )  # Dynamically get the viewer class
        #     for _ in range(viewer_count):
        #         viewer_class = getattr(
        #             task, viewer_type.replace("viewer", "").capitalize() + "viewer"
        #         )  # Dynamically get the viewer class
        #         self._add_viewer(viewer_class)

        # # Importations dynamiques : la fabrique essaie de lire et de
        # # démarrer différentes classes au moment de l’exécution.
        # # Cela peut entraîner des complications lors de la recherche de ces classes dans le runtime,
        # # j’ajoute donc une exception d’erreur au cas où les classes n’existeraient pas.
        # for viewer_type in viewerTypes():
        #     try:
        #         viewer_class = getattr(
        #             task, viewer_type.replace("viewer", "").capitalize() + "viewer"
        #         )  # Dynamically get the viewer class
        #         viewer_count = self._number_of_viewers_to_add(viewer_class)
        #         for _ in range(viewer_count):
        #             self._add_viewer(viewer_class)
        #     except AttributeError as e:
        #         print(f"Error: Could not find viewer class for type {viewer_type}: {e}")

        # #
        # for viewer_name in self.__settings.get('viewers', 'showed_viewers'):
        #     try:
        #         # Récupérer la classe du visualisateur à partir de son nom
        #         viewer_class = self._viewer_classes[viewer_name]
        #         self.addOneViewer(viewer_class)
        #     except KeyError:
        #         log.warning(f"Impossible de trouver la classe de visualisateur pour : {viewer_name}")

        log.debug(
            "addViewers.__add_all_viewers : Tout les visualiseurs sont ouverts !"
        )

    # def add_viewers(self, viewer_type: str) -> List[Type[ttk.Frame]]:
    #     """Ajoute les visualisateurs du type spécifié."""
    #     viewer_classes: List[Type[ttk.Frame]] = []
    #     number_of_viewers: int = self._number_of_viewers_to_add(viewer_type)
    #
    #     # for _ in range(number_of_viewers):
    #     #     viewer_classes.append(
    #     #         globals()[viewer_type.replace("viewer", "")].__dict__[viewer_type.capitalize()]
    #     #     )
    #     return viewer_classes

    # def _add_viewer(self, viewer_class: Type[ttk.Frame]):
    def _add_viewer(self, viewer_class: Type[Viewer]) -> None:
        # def _add_viewer(self, viewer_class, config_section, new_item_type):
        """Ajoute un seul visualisateur (viewer) de la classe spécifiée au conteneur."""
        log.debug(
            f"addViewers._add_viewer : Ajoute le visualiseur {viewer_class.__name__}."
        )
        # # Le nom de la section des paramètres est maintenant un argument à part entière.
        # settings_section = viewer_class.settingsSection()
        # # viewer_kwargs = self._viewer_kwargs(viewer_class)
        # # viewer_kwargs = {
        # #     "settingsSection": settings_section,
        # #     "taskFile": self.__task_file,
        # #     "settings": self.__settings
        # # }

        # Instanciation de la classe de visualiseur en passant les arguments requis.
        # viewer = viewer_class(self.__viewer_container, self.__settings, self.__task_file, **viewer_kwargs)
        # Pass the containerWidget as the parent
        # viewer = viewer_class(self.__viewer_container.containerWidget, self.__settings, self.__task_file, **viewer_kwargs)
        # viewer = viewer_class(self.__viewer_container.containerWidget, **viewer_kwargs)
        viewer_instance = viewer_class(
            self.__viewer_container.containerWidget,
            self.__task_file,
            self.__settings,
            **self._viewer_kwargs(viewer_class),
        )  # Corrected line

        # TypeError: Can't instantiate abstract class Taskviewer without an implementation for abstract methods 'bitmap', 'createWidget', 'isShowingAttachments', 'isShowingCategories', 'isShowingEffort', 'isShowingNotes', 'isShowingTasks', 'isTreeViewer', 'isViewerContainer', 'visibleColumns'
        # Besoin de changer Taskviewer. Descendant d'autres classes et ajouter des méthodes.
        # Le code que vous avez fourni pour la classe Taskviewer utilise déjà ttk.Treeview pour créer une vue en arborescence, ce qui est l'équivalent moderne de wx.TreeCtrl en Tkinter. Les deux méthodes wxpython que vous souhaitez intégrer à la classe sont déjà gérées, pour la plupart, par votre code Tkinter existant.
        #
        # Voici comment adapter ces méthodes et où les intégrer dans votre classe Taskviewer existante :
        #
        #     createWidget : La méthode createWidget de wxpython est obsolète.
        #     Sa fonctionnalité principale a été intégrée directement dans le constructeur __init__ de votre classe Taskviewer en utilisant ttk.Treeview. Les éléments tels que la création du widget TreeListCtrl, l'assignation des colonnes, et la liaison des événements (comme le tri par colonne) sont déjà présents dans votre code. Les menus contextuels, la gestion du glisser-déposer, et l'édition de libellés sont des fonctionnalités qui doivent être ajoutées séparément en utilisant les événements et méthodes de ttk.Treeview.
        #
        #     isTreeViewer : La méthode isTreeViewer de wxpython est utilisée pour déterminer le mode d'affichage, soit arborescence, soit liste. Votre code Tkinter gère déjà ce comportement en utilisant l'attribut self.__viewMode dans le constructeur et en définissant les colonnes par défaut. Vous pouvez créer une nouvelle méthode appelée isTreeMode pour encapsuler cette logique.

        # # Ajout du visualiseur au conteneur
        # # self.__viewer_container.addViewer(viewer)
        self.__viewer_container.addViewer(viewer_instance)
        # self.__viewer_container.addViewer(viewer_instance, floating=self.floating)
        # self.__viewer_container.pack(fill="both", expand=True, padx=10, pady=5)
        # viewer.grid(row=self.viewer_count + 1, column=0, padx=10, pady=5)

        # Sauf qu'il faut instancier le visualiseur avec le nom du parent.
        # Remplacez l'instanciation ici
        # Par un appel à la nouvelle méthode addViewer dans le conteneur
        # self.__viewer_container.addViewer(
        #     viewer_class,
        #     self.__viewer_container.containerWidget,
        #     self.__settings,
        #     self.taskFile  # ,
        #     # configSection=config_section,
        #     # newItemType=new_item_type
        # )
        log.debug(
            f"addViewers._add_viewer : Le visualiseur {viewer_class.__name__} a été ajouté au conteneur {self.__viewer_container} !"
        )

    def addViewersToContainer(self):
        self.__add_all_viewers()

    def _viewer_classes(self) -> List[Type[ttk.Frame]]:
        """Retourne la liste des classes de visualisateurs à ajouter."""
        viewer_classes: List[Type[ttk.Frame]] = []
        for viewer_type in viewerTypes():
            number_of_viewers = self._number_of_viewers_to_add(
                globals()[viewer_type.replace("viewer", "")].__dict__[
                    viewer_type.capitalize()
                ]
            )
            for _ in range(number_of_viewers):
                viewer_classes.append(
                    globals()[viewer_type.replace("viewer", "")].__dict__[
                        viewer_type.capitalize()
                    ]
                )
        return viewer_classes

    def _number_of_viewers_to_add(self, viewer_class: Type[ttk.Frame]) -> int:
        """Détermine le nombre de visualisateurs à ajouter pour une classe donnée."""
        return self.__settings.getint(
            "view", viewer_class.__name__.lower() + "count"
        )

    # def _viewer_kwargs(self, viewer_class: Type[ttk.Frame]) -> Dict[str, Any]:
    def _viewer_kwargs(self, viewer_class: Type[ttk.Frame]) -> Dict[str, Any]:
        """Retourne les arguments de mots-clés pour l'initialiseur du visualisateur."""
        # return dict()
        # # return dict(viewerContainer=self.__viewer_container) if issubclass(viewer_class, effort.EffortViewerForSelectedTasks) else dict()
        # # kwargs = super()._viewer_kwargs(viewer_class)
        # kwargs = {}  #super()._viewer_kwargs(viewer_class) # Remove super call
        # kwargs.update(self.__kwargs)
        # return kwargs
        # return {}
        return {"settingsSection": viewer_class.__name__.lower()}

    # Analysons le code et fournissons la version correcte.


# L’objectif est de faire en sorte que addViewers crée des visionneuses
# en fonction des paramètres, et qu’addOneViewer crée une visionneuse
# avec des arguments de mots-clés potentiellement supplémentaires.


class addOneViewer(addViewers):
    """
    Classe pour ajouter un seul visualisateur d'une classe spécifiée.
    """

    floating = True

    # def __init__(self, viewer_container: Any, task_file: Any, settings: settings, viewer_class: Type[ttk.Frame], **kwargs: Any):
    def __init__(
        self,
        viewer_container: Any,
        task_file: Any,
        settings,
        viewer_class: Type[ttk.Frame],
        **kwargs: Any,
    ):
        log.debug(
            f"addOneViewer.__init__ : Ajoute le visualiseur {viewer_class.__name__}."
        )
        self.__viewer_class = viewer_class
        self.__kwargs = kwargs
        super().__init__(viewer_container, task_file, settings)
        log.debug(
            f"addOneViewer.__init__ : Le visualiseur {viewer_class.__name__} a été ajouté."
        )

    def _number_of_viewers_to_add(self, viewer_class: Type[ttk.Frame]) -> int:
        return 1 if viewer_class == self.__viewer_class else 0

    def _viewer_kwargs(self, viewer_class: Type[ttk.Frame]) -> Dict[str, Any]:
        kwargs = super()._viewer_kwargs(viewer_class)
        # kwargs = {}
        kwargs.update(self.__kwargs)
        return kwargs


# --- DÉMONSTRATION ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Factory Demo")

    class MockTaskFile:
        def tasks(self):
            return []

    class MockViewerContainer(ttk.Frame):
        def __init__(self, parent: tk.Tk):
            super().__init__(parent)
            self.viewer_count = 0  # Copié dans containertk.ViewerContainer
            self.pack(
                fill="both", expand=True
            )  # Copié dans mainmenutk._create_viewer_container
            self._label = ttk.Label(
                self, text="Conteneur de visualisateurs..."
            )
            self._label.pack(pady=20)
            print("Conteneur de visualisateurs créé.")

        def add_viewer(self, viewer: ttk.Frame):
            viewer.pack(fill="both", expand=True, padx=10, pady=5)
            self.viewer_count += 1
            self._label.config(
                text=f"Visualisateurs ajoutés: {self.viewer_count}"
            )

    # Création des objets de simulation
    # mock_settings = settings()
    mock_task_file = MockTaskFile()
    viewer_container = MockViewerContainer(root)

    # Démonstration de addViewers (ajoute les visualisateurs selon les paramètres)
    print("--- Démarrage de la démonstration addViewers ---")
    # add_viewers_strategy = addViewers(viewer_container, mock_task_file, mock_settings)
    add_viewers_strategy = addViewers(
        viewer_container, mock_task_file, settings
    )
    add_viewers_strategy()

    root.mainloop()
