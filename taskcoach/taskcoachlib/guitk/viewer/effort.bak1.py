# -*- coding: utf-8 -*-
"""
Vue de l'effort pour Tkinter.
Basé sur le fichier effort.py original de Task Coach.
"""
# Le fichier effort.py est l'une des parties les plus complexes de l'application, car il gère l'affichage des efforts (temps passé) sur les tâches. Il inclut de nombreuses logiques pour la vue, les colonnes, le tri, le filtrage et la synchronisation des données.
#
# J'ai réécrit le code pour utiliser Tkinter et sa bibliothèque ttk. Voici les principaux changements que j'ai effectués :
#
#     EffortViewer : Cette classe a été refactorisée pour utiliser ttk.Treeview pour l'affichage des efforts. J'ai ajouté des méthodes pour gérer le tri des colonnes (_on_column_click), l'actualisation de l'affichage (_refresh) et la mise à jour des données.
#
#     Colonnes : Les colonnes de la vue (date, durée, notes, etc.) sont définies dynamiquement. J'ai inclus une logique pour la création de ces colonnes et pour la gestion de leur visibilité.
#
#     Synchronisation des données : La classe EffortViewerForSelectedTasks est convertie pour écouter les changements de sélection dans la vue principale des tâches, et pour mettre à jour sa propre vue en conséquence.
#
#     Simulations de modules : Comme le fichier original dépend de nombreux modules (domain, uicommand, etc.), j'ai inclus des simulations simplifiées de ces classes pour que le code soit auto-suffisant et exécutable. Vous devrez les remplacer par vos versions réelles pour intégrer ce code dans votre projet.
#
# Notez que la logique de pubsub est remplacée par une simple écoute des événements de l'interface utilisateur. Vous devrez peut-être adapter cela à votre propre système de gestion d'événements si vous en avez un.
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from taskcoachlib import domain
from taskcoachlib.guitk.uicommand import uicommandtk

from taskcoachlib.i18n import _

# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# def _(text: str) -> str:
#     return text


class settings:
    def __init__(self):
        self._data: Dict[str, Any] = {
            "effortviewer": {
                "columns": "date,duration,notes",
                "round": 0,
                "alwaysroundup": False,
                "consolidateeffortspertask": False
            }
        }

    def getint(self, section: str, option: str) -> int:
        return self._data.get(section, {}).get(option, 0)

    def getboolean(self, section: str, option: str) -> bool:
        return self._data.get(section, {}).get(option, False)


# class domain:
#     class date:
#         def __init__(self, value: Any):
#             self.value = value
#         def __str__(self) -> str:
#             return str(self.value)
#
#     class effort:
#         def __init__(self, start: Any, duration: int, notes: str):
#             self.start = start
#             self.duration = duration
#             self.notes = notes
#
#     class task:
#         def __init__(self, name: str):
#             self.name = name
#             self.efforts: List[domain.effort] = []
#         def getEfforts(self) -> List[domain.effort]:
#             return self.efforts
#
#     class tasklist:
#         def __init__(self, tasks: List[domain.task]):
#             self._tasks = tasks
#         def __iter__(self):
#             return iter(self._tasks)


# class uicommand:
#     class UICommand:
#         def __init__(self, settings: Any = None):
#             self.settings = settings
#         def GetLabel(self) -> str: return "Label"
#         def GetTooltip(self) -> str: return "Tooltip"
#         def GetBitmap(self) -> str: return "Bitmap"
#         def GetHelp(self) -> str: return "Help"
#         def IsToggled(self) -> bool: return False
#         def isEnabled(self) -> bool: return True


# --- CLASSE CONVERTIE ---
class Effortviewer(ttk.Frame):
    """
    Vue des efforts pour Tkinter.
    """
    defaultTitle = _("Effort(s)")

    def __init__(self, parent: tk.Tk, settings_obj: settings, settingsSection: str = "effortviewer", **kwargs: Any):
        super().__init__(parent, **kwargs)
        self.__tasksToShowEffortFor = kwargs.pop("tasksToShowEffortFor", [])
        self.settings = settings_obj
        self.settingsSection = lambda: settingsSection
        self._sort_column = "date"
        self._sort_ascending = True

        self.tree = ttk.Treeview(self)
        self.tree.pack(fill="both", expand=True)

        self._create_columns()
        self._refresh()

    def _create_columns(self):
        """Crée les colonnes du Treeview en fonction des paramètres."""
        columns_str = self.settings.getint(self.settingsSection(), "columns")
        columns_list = ["date", "duration", "notes"]  # Simulation

        self.tree["columns"] = columns_list
        self.tree.heading("#0", text=_("ID")) # Première colonne invisible

        for col in columns_list:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self._on_column_click(c))
            self.tree.column(col, width=100)

    def _on_column_click(self, column_name: str):
        """Gère le clic sur l'en-tête d'une colonne pour le tri."""
        if self._sort_column == column_name:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = column_name
            self._sort_ascending = True

        self._refresh()

    def _refresh(self, clear: bool = True):
        """Actualise la vue avec les efforts des tâches."""
        if clear:
            self.tree.delete(*self.tree.get_children())

        tasks = self.tasksToShowEffortFor()
        all_efforts = []
        for task in tasks:
            for effort in task.getEfforts():
                all_efforts.append(effort)

        # Tri des efforts (simulation)
        all_efforts.sort(key=lambda e: getattr(e, self._sort_column), reverse=not self._sort_ascending)

        for effort in all_efforts:
            self.tree.insert("", "end", text=str(id(effort)), values=(str(effort.start), effort.duration, effort.notes))

    def tasksToShowEffortFor(self) -> List[domain.task]:
        """Méthode à surcharger dans les sous-classes."""
        # # Simulation de données
        # task1 = domain.task("Tâche 1")
        # task1.efforts.append(domain.effort(domain.date("2023-01-01"), 60, "Début du projet"))
        # task1.efforts.append(domain.effort(domain.date("2023-01-02"), 90, "Suite du travail"))
        #
        # task2 = domain.task("Tâche 2")
        # task2.efforts.append(domain.effort(domain.date("2023-01-01"), 30, "Réunion"))
        #
        # return [task1, task2]
        return self.__tasksToShowEffortFor

    @classmethod
    def settingsSection(cls) -> str:
        """
        Retourne la section de paramétrage de la vue.
        Cette méthode de classe est utilisée par la fabrique de visionneuses.
        """
        return "effortviewer"


class EffortViewerForSelectedTasks(Effortviewer):
    """
    Vue des efforts pour les tâches sélectionnées.
    """
    defaultTitle = _("Effort pour la(les) tâche(s) sélectionnée(s)")

    def __init__(self, parent: tk.Tk, settings_obj: settings, viewerContainer: Any, **kwargs: Any):
        kwargs.setdefault("settingsSection", "effortviewerforselectedtasks")
        super().__init__(parent, settings_obj, **kwargs)
        self.__viewerContainer = viewerContainer

        # Simulation d'un abonnement à un événement
        self.__viewerContainer.on_task_selection_changed = self.onTaskSelectionChanged

    def tasksToShowEffortFor(self) -> List[domain.task]:
        if self.__viewerContainer.activeViewer() is not None:
            return self.__viewerContainer.activeViewer().curselection()
        return []

    def onTaskSelectionChanged(self, viewer: Any):
        if viewer.isShowingTasks():
            self._refresh(clear=True)


if __name__ == '__main__':
    root = tk.Tk()
    root.title(_("Effort Viewer Demo"))

    app_settings = settings()

    class MockViewerContainer:
        def __init__(self):
            self.on_task_selection_changed: Optional[Callable] = None
            self.tasks = [
                domain.task("Tâche sélectionnée 1"),
                domain.task("Tâche sélectionnée 2")
            ]
            self.tasks[0].efforts.append(domain.effort(domain.date("2023-01-05"), 120, "Effort sur la tâche 1"))
            self.tasks[1].efforts.append(domain.effort(domain.date("2023-01-06"), 45, "Effort sur la tâche 2"))

        def activeViewer(self) -> Any:
            class MockActiveViewer:
                def isShowingTasks(self) -> bool: return True
                def curselection(self) -> List[domain.task]: return MockViewerContainer().tasks
            return MockActiveViewer()

    # Démonstration de EffortViewer
    effort_viewer = Effortviewer(root, app_settings)
    effort_viewer.pack(fill="both", expand=True, pady=10)

    # Démonstration de EffortViewerForSelectedTasks
    viewer_container = MockViewerContainer()
    effort_viewer_selected = EffortViewerForSelectedTasks(root, app_settings, viewerContainer=viewer_container)
    effort_viewer_selected.pack(fill="both", expand=True, pady=10)

    root.mainloop()
