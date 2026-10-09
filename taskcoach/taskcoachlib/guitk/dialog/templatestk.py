# -*- coding: utf-8 -*-
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

Conversion vers Tkinter de templates.py.

Classe principale : TemplatesDialog

Cette classe implémente une boîte de dialogue pour la gestion des modèles de tâches
dans l'application Task Coach.
Elle permet de visualiser, modifier et supprimer des modèles de tâches existants,
ainsi que d'en créer de nouveaux.

Fonctionnalités principales

    Affichage d'une liste d'arborescence pour parcourir les modèles de tâches.
    Edition des propriétés d'un modèle de tâche sélectionné (sujet, dates de début, d'échéance, d'achèvement et de rappel).
    Suppression d'un modèle de tâche sélectionné.
    Déplacement d'un modèle de tâche vers le haut ou le bas dans la liste.
    Ajout d'un nouveau modèle de tâche.
    Sauvegarde des modifications apportées aux modèles de tâches.

Classes et méthodes utilisées

    TimeExpressionEntry : Une classe dérivée de wx.TextCtrl permettant la saisie et la validation d'expressions temporelles.
    createTemplateList : Crée la liste d'arborescence pour afficher les modèles de tâches.
    createTemplateEntries : Crée les champs d'édition pour les propriétés d'un modèle de tâche.
    enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection d'un modèle.
    appendTemplate : Ajoute un modèle de tâche et ses enfants à la liste d'arborescence.
    onValueChanged : Gère les modifications apportées aux champs d'édition d'un modèle de tâche.
    OnSelectionChanged : Gère la sélection d'un modèle de tâche dans la liste, met à jour les champs d'édition et active/désactive les boutons de suppression et de déplacement.
    onDelete : Supprime le modèle de tâche sélectionné.
    OnUp : Déplace le modèle de tâche sélectionné vers le haut dans la liste.
    OnDown : Déplace le modèle de tâche sélectionné vers le bas dans la liste.
    onAdd : Ajoute un nouveau modèle de tâche vide à la liste.
    ok : Sauvegarde les modifications apportées aux modèles de tâches lors de la validation de la boîte de dialogue.

Méthodes liées à l'interface utilisateur :

    createTemplateList, createTemplateEntries, createButton : Ces méthodes sont responsables de la construction de l'interface graphique de la boîte de dialogue, en créant les différents éléments tels que la liste d'arborescence, les champs de saisie et les boutons.
    enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection de l'utilisateur.
    appendTemplate : Ajoute un nouveau nœud à l'arbre des modèles de tâches.

Méthodes liées à la gestion des modèles de tâches :

    onValueChanged, OnSelectionChanged : Ces méthodes gèrent les événements utilisateur, tels que la modification du contenu d'un champ de saisie ou la sélection d'un élément dans la liste. Elles mettent à jour l'état interne de l'application en conséquence.
    onDelete, OnUp, OnDown, onAdd : Ces méthodes permettent à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en supprimant, déplaçant ou ajoutant des éléments.
    ok : Cette méthode est appelée lorsque l'utilisateur clique sur le bouton "OK" de la boîte de dialogue. Elle sauvegarde les modifications apportées aux modèles de tâches.

Dialogues Tkinter pour la gestion des modèles.
Basé sur le fichier templates.py original de Task Coach.
"""
# Le fichier templates.py est beaucoup plus complexe, car
# il gère à la fois l'interface utilisateur
# (boîte de dialogue, liste d'arborescence, champs de saisie)
# et la logique de l'application (gestion des modèles, sauvegarde).
#
# J'ai réécrit le code pour utiliser Tkinter et sa bibliothèque ttk.
# Voici les principaux changements que j'ai effectués :
#
#     TemplatesDialog : Converti en une classe TemplatesDialog basée sur tk.Toplevel.
#     Elle est modale et gère la disposition des widgets.
#
#     TimeExpressionEntry : Converti en une classe TimeExpressionEntry basée sur ttk.Entry.
#     La validation de l'entrée est gérée par la méthode _onTextChanged.
#
#     TreeCtrl : J'ai utilisé ttk.Treeview pour l'affichage de l'arborescence.
#
#     Glisser-déposer : Le déplacement des éléments dans la liste (OnUp, OnDown)
#     est géré par la logique du Treeview. J'ai également créé des méthodes pour
#     ajouter (onAdd), supprimer (onDelete) et mettre à jour les éléments.
#
#     Passage de données : J'ai remplacé l'utilisation de wx.TreeItemData par
#     une approche plus simple où les objets de tâche sont stockés directement
#     dans un dictionnaire, lié à l'ID de l'élément de l'arborescence.
#
# Comme le fichier original dépend de plusieurs modules
# (thirdparty.deltaTime, domain.task, persistence, operating_system),
# j'ai dû créer des simulations simplifiées de ces classes et fonctions
# pour que le code soit auto-suffisant et exécutable.
# Vous devrez les remplacer par vos versions réelles pour intégrer ce code dans votre projet.

# Voici un aperçu des modifications :
#
#     Imports : J'ajouterai les imports pour Task, TemplateList, operating_system, nlTimeExpression et le traducteur _ à partir des fichiers que vous avez fournis.
#
#     Initialisation : J'adapterai l'initialisation de la classe TemplatesDialog pour utiliser l'objet TemplateList réel (que j'ai simulé par un chargement initial dans la méthode _init__) et la classe Task.
#
#     Fonctionnalités manquantes : J'implémenterai une version simplifiée des méthodes on_delete et _edit_template (pour l'édition du sujet) pour que la boîte de dialogue soit fonctionnelle, en alignement avec la logique de templates.py. J'ai également ajusté la logique de déplacement pour mieux correspondre à l'original.

# J'ai mis à jour le fichier templatestk.py en ajoutant les imports demandés, en implémentant la logique d'édition et de suppression (pour les tâches racines uniquement, pour rester cohérent avec l'original), et en corrigeant les méthodes de déplacement pour qu'elles mettent à jour à la fois le ttk.Treeview et l'objet TemplateList sous-jacent.
#
# Pour tester cette version, assurez-vous que les fichiers task.py, templatelist.py et __init__.py (qui contient la fonction _) sont accessibles par l'importateur Python. J'ai ajouté un bloc if __name__ == "__main__": pour vous permettre de lancer la boîte de dialogue pour la tester.

#
import logging
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, StringVar, Label, Entry, Button, LEFT, RIGHT
from typing import Any, Callable, Dict, List

# --- Imports des fichiers fournis par l'utilisateur ---
# Task
from taskcoachlib.domain.task.task import Task

# TemplateList
from taskcoachlib.persistence.templatelist import TemplateList

# Traduction (_)
from taskcoachlib.i18n import _

# Autres imports demandés
from taskcoachlib import operating_system
from taskcoachlib.thirdparty import deltaTime
nlTimeExpression = deltaTime.nlTimeExpression

log = logging.getLogger(__name__)

# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# class Task:
#     def __init__(self, subject: str):
#         self._subject = subject
#         self._children: List[Task] = []
#         self.plannedstartdatetmpl = None
#         self.duedatetmpl = None
#         self.completiondatetmpl = None
#         self.remindertmpl = None
#
#     def subject(self) -> str:
#         return self._subject
#
#     def setSubject(self, subject: str):
#         self._subject = subject
#
#     def get_domain_children(self) -> List['Task']:
#         return self._children
#
#
# class TemplateList:
#     def __init__(self, templates: List[Task]):
#         self._templates = templates
#
#     def tasks(self) -> List[Task]:
#         return self._templates
#
#     def addTemplate(self, template: Task) -> Task:
#         self._templates.append(template)
#         return template
#
#     def deleteTemplate(self, index: int):
#         del self._templates[index]
#
#     def swapTemplates(self, index1: int, index2: int):
#         self._templates[index1], self._templates[index2] = self._templates[index2], self._templates[index1]
#
#     def save(self):
#         print("Les modèles ont été sauvegardés.")
#
#
# # Simuler le module i18n
# def _(text):
#     return text


class TimeExpressionEntry(ttk.Entry):
    """
    Un champ de saisie qui valide les expressions temporelles.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.__defaultColor = self["bg"] or self["background"]  # Couleur de fond initiale
        # self.__invalidColor = wx.Colour(255, 128, 128)  # Couleur rouge clair pour les erreurs
        self.__invalidColor = "#fff0f0"

        # Ajoutez ces lignes de débogage
        log.warning(f"DEBUG - Type de self._onTextChanged: {type(self._onTextChanged)}")
        log.warning(f"DEBUG - Est-ce que self._onTextChanged est callable ? {callable(self._onTextChanged)}")
        # Fin des lignes de débogage

        # Lie l'événement de modification du texte à la méthode _onTextChanged.
        self.bind("<KeyRelease>", self._onTextChanged)
        self.is_valid = True

    @staticmethod
    def isValid(value: str) -> bool:
        """Simuler la validation, retourne toujours True pour la démo."""
        # return True
        if value:
            try:
                # Tente d'analyser la chaîne comme une expression temporelle
                # (nécessite l'importation de nlTimeExpression)
                res = nlTimeExpression.parseString(value)
            except Exception as e:
                # Enregistre l'exception si l'analyse échoue
                logging.exception(f"Exception: {e}", exc_info=True)
                return False  # pylint: disable=W0702 L'expression est invalide
            return "calculatedTime" in res  # Vérifie si le résultat contient un temps calculé
        return True  # Une chaîne vide est toujours valide.

    def _onTextChanged(self, event):
        value = self.get()
        self.is_valid = self.isValid(value)
        # La couleur de fond n'est pas facilement modifiable pour ttk.Entry
        # mais on peut le faire pour un widget tk.Entry.
        # Pour cet exemple, nous allons ignorer le changement de couleur.
        self.configure(
            fieldbackground=self.__defaultColor  # Couleur par défaut si valide
                # if self.isValid(self.GetValue())  # Vérifie la validité de la valeur actuelle
                if self.is_valid  # Vérifie la validité de la valeur actuelle
                else self.__invalidColor  # Couleur d'erreur si invalide
        )
        self.event_generate("<<TimeExpressionChanged>>")


class TemplatesDialog(tk.Toplevel):
    """
    Boîte de dialogue modale Tkinter pour la gestion des modèles de tâches.
    Remplace TemplatesDialog de wx.
    Elle simule les fonctionnalités de la TemplatesDialog originale en wxPython
    """
    def __init__(self, parent: tk.Tk, settings: Dict[str, Any] = None, *args, **kwargs):
        """
        Initialise la boîte de dialogue des modèles.

        Args:
            parent : La fenêtre parente (généralement la fenêtre principale de l'application Tkinter).
            settings : L'objet TemplateList à gérer.
        """
        super().__init__(parent, *args, **kwargs)
        self.title(_("Task Templates"))
        self.transient(parent)  # Définir comme fenêtre transitoire
        # self.grab_set()
        # self.title(_("Gérer les modèles de tâches"))

        # Initialisation du modèle de données
        # self.settings = settings
        # self._templates_data = TemplateList(self._load_templates())
        if settings is None:
            # Pour la démonstration, simuler la TemplateList
            # Dans une application réelle, le chemin Taskcoach doit être connu.
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "task_templates")
            os.makedirs(temp_path, exist_ok=True)
            self._templates = TemplateList(temp_path)
        else:
            self._templates = settings
        # Pour les tests sans TemplateList réelle (commenter si TemplateList est fonctionnelle)
        # self._templates = self._load_templates() # Utiliser self._templates_data comme dans le snippet

        self._task_map: Dict[str, Any] = {}  # Mappage item_id -> Task
        self._selected_item = None
        # self._changing = False

        # main_frame = ttk.Frame(self, padding=10)
        # main_frame.pack(fill="both", expand=True)

        self._create_widgets()
        self._load_templates_into_tree()

        # self._create_interior(main_frame)
        # self._create_buttons(main_frame)

        # Lier l'événement de double-clic pour l'édition
        self._template_tree.bind("<Double-1>", self._edit_template)
        # Lier la sélection
        self._template_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Centrer la fenêtre
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Crée et positionne tous les widgets de la boîte de dialogue."""
        # Cadre principal pour la liste des modèles et les boutons de contrôle
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Treeview pour les modèles de tâches
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Scrollbar verticale
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._template_tree = ttk.Treeview(
            tree_frame, columns=("subject"), show="tree", yscrollcommand=scrollbar.set
        )
        self._template_tree.heading("#0", text=_("Templates"), anchor="w")
        self._template_tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._template_tree.yview)

        # Cadre pour les boutons de contrôle (Ajouter, Supprimer, Monter, Descendre)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="right", fill="y")

        ttk.Button(control_frame, text=_("Add"), command=self.on_add).pack(fill="x", pady=2)
        ttk.Button(control_frame, text=_("Delete"), command=self.on_delete).pack(fill="x", pady=2)
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=5)
        self._up_button = ttk.Button(control_frame, text=_("Up"), command=self.on_up, state=tk.DISABLED)
        self._up_button.pack(fill="x", pady=2)
        self._down_button = ttk.Button(control_frame, text=_("Down"), command=self.on_down, state=tk.DISABLED)
        self._down_button.pack(fill="x", pady=2)

        # Cadre pour les boutons OK/Annuler
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(button_frame, text=_("OK"), command=self.on_ok).pack(side=RIGHT, padx=5)
        ttk.Button(button_frame, text=_("Cancel"), command=self.on_cancel).pack(side=RIGHT)

    def _create_interior(self, parent: ttk.Frame):
        pane = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        pane.pack(fill="both", expand=True, padx=5, pady=5)

        # Panneau de l'arborescence
        tree_frame = ttk.Frame(pane)
        self._template_tree = ttk.Treeview(tree_frame, selectmode="browse")
        self._template_tree.pack(side="left", fill="both", expand=True)
        self._template_tree.bind("<<TreeviewSelect>>", self.on_selection_changed)

        # Barres de défilement pour l'arborescence
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._template_tree.yview)
        vsb.pack(side="right", fill="y")
        self._template_tree.configure(yscrollcommand=vsb.set)

        self._populate_tree()
        pane.add(tree_frame)

        # Panneau d'édition
        self._edit_panel = ttk.Frame(pane, padding=10)
        self._create_template_entries(self._edit_panel)
        self._enable_edit_panel(False)
        pane.add(self._edit_panel)

    def _create_template_entries(self, pane: ttk.Frame):
        ttk.Label(pane, text=_("Sujet")).grid(row=0, column=0, sticky="w", pady=2)
        self._subject_ctrl = ttk.Entry(pane)
        self._subject_ctrl.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(pane, text=_("Date de début planifiée")).grid(row=1, column=0, sticky="w", pady=2)
        self._planned_start_ctrl = TimeExpressionEntry(pane)
        self._planned_start_ctrl.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(pane, text=_("Date d'échéance")).grid(row=2, column=0, sticky="w", pady=2)
        self._due_date_ctrl = TimeExpressionEntry(pane)
        self._due_date_ctrl.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(pane, text=_("Date d'achèvement")).grid(row=3, column=0, sticky="w", pady=2)
        self._completion_date_ctrl = TimeExpressionEntry(pane)
        self._completion_date_ctrl.grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(pane, text=_("Rappel")).grid(row=4, column=0, sticky="w", pady=2)
        self._reminder_ctrl = TimeExpressionEntry(pane)
        self._reminder_ctrl.grid(row=4, column=1, sticky="ew", pady=2)

        self._task_controls = {
            self._subject_ctrl: "subject",
            self._planned_start_ctrl: "plannedstartdatetmpl",
            self._due_date_ctrl: "duedatetmpl",
            self._completion_date_ctrl: "completiondatetmpl",
            self._reminder_ctrl: "remindertmpl"
        }

        for ctrl in self._task_controls:
            ctrl.bind("<<TimeExpressionChanged>>", self._on_value_changed)
            ctrl.bind("<KeyRelease>", self._on_value_changed)

    def _load_templates_into_tree(self):
        """Charge les modèles de TaskList dans la Treeview."""
        # Nettoyer l'arborescence et le mappage
        self._template_tree.delete(*self._template_tree.get_children())
        self._task_map.clear()

        # Charger les modèles de la TemplateList
        root_templates = self._templates.tasks()

        for template in root_templates:
            self._append_template("", template)

    def _create_buttons(self, parent: ttk.Frame):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)

        self._btn_add = ttk.Button(button_frame, text=_("Ajouter"), command=self.on_add)
        self._btn_add.pack(side="left", padx=5)

        self._btn_delete = ttk.Button(button_frame, text=_("Supprimer"), command=self.on_delete, state=tk.DISABLED)
        self._btn_delete.pack(side="left", padx=5)

        self._btn_up = ttk.Button(button_frame, text=_("Monter"), command=self.on_up, state=tk.DISABLED)
        self._btn_up.pack(side="left", padx=5)

        self._btn_down = ttk.Button(button_frame, text=_("Descendre"), command=self.on_down, state=tk.DISABLED)
        self._btn_down.pack(side="left", padx=5)

        ttk.Button(button_frame, text=_("OK"), command=self.on_ok).pack(side="left", padx=20)
        ttk.Button(button_frame, text=_("Annuler"), command=self.on_cancel).pack(side="left", padx=5)

    def _populate_tree(self):
        self._template_tree.delete(*self._template_tree.get_children())
        self._task_map.clear()

        # for task in self._templates_data.tasks():
        for task in self._templates.tasks():
            self._append_template(None, task)

    def _append_template(self, parent_id: str, task: Task):
        """Ajoute un modèle de tâche et ses enfants de manière récursive à la Treeview."""
        item_id = self._template_tree.insert(parent_id or "", "end", text=task.subject())
        self._task_map[item_id] = task

        for child in task.children():
            self._append_template(item_id, child)

        return item_id

    def _on_tree_select(self, event):
        """Gère la sélection d'un élément dans la Treeview."""
        selected = self._template_tree.selection()
        if selected:
            self._selected_item = selected[0]

            # Activer/Désactiver les boutons Up/Down
            parent_id = self._template_tree.parent(self._selected_item)
            if not parent_id:  # Seulement pour les tâches racines
                prev_id = self._template_tree.prev(self._selected_item)
                next_id = self._template_tree.next(self._selected_item)
                self._up_button.config(state=tk.NORMAL if prev_id else tk.DISABLED)
                self._down_button.config(state=tk.NORMAL if next_id else tk.DISABLED)
            else:
                self._up_button.config(state=tk.DISABLED)
                self._down_button.config(state=tk.DISABLED)
        else:
            self._selected_item = None
            self._up_button.config(state=tk.DISABLED)
            self._down_button.config(state=tk.DISABLED)

    def _enable_edit_panel(self, enable: bool):
        for ctrl in self._task_controls:
            if enable:
                ctrl.state(['!disabled'])
            else:
                ctrl.state(['disabled'])

    def _edit_template(self, event=None):
        """
        Ouvre une boîte de dialogue simplifiée pour éditer le sujet du modèle sélectionné.
        Ceci est un placeholder pour la boîte de dialogue d'édition de propriétés de tâche plus complexe.
        """
        if not self._selected_item:
            return

        item_id = self._selected_item
        task = self._task_map.get(item_id)

        if not task:
            return

        # Simple boîte de dialogue Toplevel pour éditer le sujet
        top = Toplevel(self.master)
        top.title(_("Edit Template"))
        top.transient(self) # Rendre modal par rapport à la fenêtre TemplatesDialog
        top.grab_set() # Capturer tous les événements

        Label(top, text=_("Subject:")).pack(padx=10, pady=5)

        subject_var = StringVar(value=task.subject() if task else "")
        subject_entry = Entry(top, textvariable=subject_var, width=50)
        subject_entry.pack(padx=10, pady=5)
        subject_entry.focus_set()

        def save_and_close():
            new_subject = subject_var.get().strip()
            if task and new_subject:
                # Assumer que la classe Task a une méthode setSubject()
                task.setSubject(new_subject)
                # Mettre à jour le texte dans la Treeview
                self._template_tree.item(item_id, text=new_subject)
            top.destroy()
            self.grab_set() # Rendre la boîte de dialogue TemplatesDialog à nouveau active

        Button(top, text=_("OK"), command=save_and_close).pack(side=LEFT, padx=5, pady=10)
        Button(top, text=_("Cancel"), command=top.destroy).pack(side=RIGHT, padx=5, pady=10)

        self.wait_window(top)

    def on_selection_changed(self, event):
        self._changing = True
        try:
            selected_items = self._template_tree.selection()
            if selected_items:
                self._selected_item = selected_items[0]
                task = self._task_map.get(self._selected_item)
                if task:
                    self._btn_delete.state(['!disabled'])
                    self._btn_up.state(['!disabled'])
                    self._btn_down.state(['!disabled'])
                    self._enable_edit_panel(True)

                    # Mettre à jour les champs de saisie
                    self._subject_ctrl.delete(0, tk.END)
                    self._subject_ctrl.insert(0, task.subject())
                    self._planned_start_ctrl.delete(0, tk.END)
                    self._planned_start_ctrl.insert(0, task.plannedstartdatetmpl or "")
                    self._due_date_ctrl.delete(0, tk.END)
                    self._due_date_ctrl.insert(0, task.duedatetmpl or "")
                    self._completion_date_ctrl.delete(0, tk.END)
                    self._completion_date_ctrl.insert(0, task.completiondatetmpl or "")
                    self._reminder_ctrl.delete(0, tk.END)
                    self._reminder_ctrl.insert(0, task.remindertmpl or "")
                else:
                    self._enable_edit_panel(False)
            else:
                self._selected_item = None
                self._btn_delete.state(['disabled'])
                self._btn_up.state(['disabled'])
                self._btn_down.state(['disabled'])
                self._enable_edit_panel(False)
        finally:
            self._changing = False

    def _on_value_changed(self, event):
        if not self._changing and self._selected_item:
            task = self._task_map.get(self._selected_item)
            if task:
                for ctrl, attr in self._task_controls.items():
                    if ctrl == event.widget:
                        if attr == "subject":
                            task.setSubject(ctrl.get())
                            self._template_tree.item(self._selected_item, text=task.subject())
                        else:
                            # Pour les autres champs, mettre à jour l'attribut
                            value = ctrl.get() or None
                            setattr(task, attr, value)

    def on_delete(self):
        """Supprime le modèle de tâche sélectionné, uniquement s'il s'agit d'une tâche racine."""
        if not self._selected_item:
            return

        item_id = self._selected_item
        # if self._selected_item:
        #     parent_id = self._template_tree.parent(self._selected_item)
        #     if not parent_id:  # Seulement supprimer les tâches de niveau racine
        #         task = self._task_map.get(self._selected_item)
        #         if task:
        #             index = self._templates_data.tasks().index(task)
        #             self._templates_data.deleteTemplate(index)
        #             self._template_tree.delete(self._selected_item)
        #             self._selected_item = None
        #             self._enable_edit_panel(False)
        parent_id = self._template_tree.parent(item_id)
        task = self._task_map.get(item_id)

        # Dans le TemplatesDialog original, seules les tâches racines sont supprimables via ce bouton.
        if not parent_id and task:
            # 1. Suppression dans le modèle de données (TemplateList)
            try:
                index = self._templates.tasks().index(task)
                self._templates.deleteTemplate(index)
            except ValueError as e:
                print(f"Erreur lors de la suppression du modèle : {e}")
                return

            # 2. Suppression dans la Treeview
            self._template_tree.delete(item_id)
            del self._task_map[item_id]
            self._selected_item = None
            self._on_tree_select(None)  # Mettre à jour l'état des boutons

    def on_up(self):
        """Déplace le modèle de tâche sélectionné vers le haut dans la liste des modèles racines."""
        if self._selected_item:
            parent_id = self._template_tree.parent(self._selected_item)
            # Ne déplace que les éléments racines
            if not parent_id:
                prev_id = self._template_tree.prev(self._selected_item)
                if prev_id:
                    # self._template_tree.move(self._selected_item, parent_id, "before", prev_id)
                    self._template_tree.move(self._selected_item, parent_id, prev_id)
                    # Mise à jour de la liste de données
                    task = self._task_map.get(self._selected_item)
                    # index = self._templates_data.tasks().index(task)
                    index = self._templates.tasks().index(task)
                    # self._templates_data.swapTemplates(index, index - 1)
                    self._templates.swapTemplates(index, index - 1)

                    # Sélectionner à nouveau l'élément après le déplacement
                    self._template_tree.selection_set(self._selected_item)
                    self._on_tree_select(None)

    def on_down(self):
        """Déplace le modèle de tâche sélectionné vers le bas dans la liste des modèles racines."""
        if self._selected_item:
            parent_id = self._template_tree.parent(self._selected_item)
            # Ne déplace que les éléments racines
            if not parent_id:
                next_id = self._template_tree.next(self._selected_item)
                if next_id:
                    # Pour déplacer vers le bas, on peut insérer l'élément sélectionné
                    # après le `next_id` de l'élément suivant.
                    # self._template_tree.move(self._selected_item, parent_id, "after", next_id)
                    next_next_id = self._template_tree.next(next_id)
                    if next_next_id:
                        self._template_tree.move(self._selected_item, parent_id, next_next_id)
                    else:
                        # Si next_id est le dernier, déplacer à la fin
                        self._template_tree.move(self._selected_item, parent_id, "end")

                    # Mise à jour de la liste de données
                    task = self._task_map.get(self._selected_item)
                    # index = self._templates_data.tasks().index(task)
                    index = self._templates.tasks().index(task)
                    # self._templates_data.swapTemplates(index, index + 1)
                    self._templates.swapTemplates(index, index + 1)

                    # Sélectionner à nouveau l'élément après le déplacement
                    self._template_tree.selection_set(self._selected_item)
                    self._on_tree_select(None)

    def on_add(self):
        """Ajoute un nouveau modèle de tâche."""
        # new_task = Task(subject=_("Nouveau modèle de tâche"))
        template = Task(subject=_("New task template"))

        # Initialiser les attributs comme dans templates.py:
        for name in (
                "plannedstartdatetmpl",
                "duedatetmpl",
                "completiondatetmpl",
                "remindertmpl",
        ):
            # Assumer que Task.plannedstartdatetmpl, etc. peuvent être définis
            setattr(template, name, None)

        # 1. Ajout au modèle de données
        # self._templates_data.addTemplate(new_task)
        theTask = self._templates.addTemplate(template)

        # 2. Ajout à la Treeview
        # self._append_template(None, new_task)
        item_id = self._append_template("", theTask)

        # Sélectionner et rendre visible le nouvel élément
        self._template_tree.selection_set(item_id)
        self._template_tree.see(item_id)
        self._on_tree_select(None)

    def on_ok(self):
        """Sauvegarde les modèles et ferme la boîte de dialogue."""
        # La sauvegarde est gérée par l'ordre actuel dans self._templates
        # self._templates_data.save()
        self._templates.save()
        self.destroy()

    def on_cancel(self):
        """Ferme la boîte de dialogue sans sauvegarder."""
        # Note: Si des modifications ont été faites via _edit_template, elles sont déjà
        # appliquées aux objets Task en mémoire. Le 'Cancel' dans l'original wxPython
        # annulait seulement la réorganisation. Dans cette version simplifiée,
        # nous ne gérons que la réorganisation et l'ajout/suppression ici.
        self.destroy()

    def _load_templates(self) -> List[Task]:
        """Fonction simulée pour charger des modèles."""
        task1 = Task(subject=_("Tâche modèle 1"))
        task2 = Task(subject=_("Tâche modèle 2"))
        child1 = Task(subject=_("Sous-tâche 1"))
        child2 = Task(subject=_("Sous-tâche 2"))
        child1._children.append(child2)
        task1._children.append(child1)
        return [task1, task2]


# --- Code pour l'exécution et le test (optionnel) ---
if __name__ == "__main__":
    # Ce bloc de code simule le setup nécessaire pour exécuter la boîte de dialogue
    # Veuillez vous assurer que les fichiers task.py, templatelist.py et __init__.py
    # sont présents dans le même répertoire ou dans le PYTHONPATH pour que cela fonctionne.

    root = tk.Tk()
    root.title("Task Coach Main Window (Simulated)")
    # root.withdraw()  # Cacher la fenêtre principale

    # --- CORRECTION DE L'ERREUR 'settings' MANQUANT ---
    # La classe Task essaie probablement d'accéder à Task.settings.
    # Nous ajoutons un mock d'objet settings minimaliste à la classe Task.
    class MockSettings:
        """Objet factice (mock) pour simuler les paramètres de l'application."""
        def get(self, key, default=None):
            if key == 'defaulttaskduedate':  # Exemple de clé que Task pourrait chercher
                return None
            return default

        def getint(self, section, key):
            """Simule la lecture d'une valeur entière depuis les paramètres."""
            # D'après la trace d'erreur, Task cherche 'duesoonhours'
            if key == 'duesoonhours' and section == 'behavior':
                # Retourner une valeur par défaut raisonnable (par exemple, 48 heures)
                return 48
            # Si d'autres clés entières sont nécessaires, ajoutez-les ici.
            return 0  # Retourner 0 par défaut pour les autres entiers inconnus

        def isSettingEnabled(self, key):
            # Simuler que l'option d'attacher des tâches est désactivée par défaut
            if key == 'task.autocreatesubtaskfromtemplate':
                return False
            return False  # Retourner False pour les autres paramètres inconnus

    # Attacher l'instance de MockSettings à la classe Task
    Task.settings = MockSettings()
    # --------------------------------------------------

    # Simuler une TemplateList (nécessite un chemin valide)
    # Dans un environnement de test, assurez-vous que le dossier 'temp_templates' existe.
    # Pour un test simple, nous allons créer des modèles mockés si TemplateList n'est pas fonctionnelle.

    # Création d'un répertoire temporaire pour les tests de TemplateList
    import tempfile
    test_path = tempfile.mkdtemp()

    try:
        # Initialiser une TemplateList
        templates = TemplateList(test_path)

        # Si la TemplateList est vide, ajouter quelques modèles pour le test
        if not templates.tasks():
            t1 = templates.addTemplate(Task(subject=_("Template 1 (Root)")))
            t2 = templates.addTemplate(Task(subject=_("Template 2 (Root)")))
            t1.addChild(Task(subject=_("Sub-Template 1.1")))
            t1.addChild(Task(subject=_("Sub-Template 1.2")))

        dialog = TemplatesDialog(root, templates)
        root.mainloop()

        # Nettoyage
        import shutil
        shutil.rmtree(test_path)


    except Exception as e:
        # Affiche l'erreur complète pour le débogage si un autre problème survient
        import traceback
        print(f"Impossible d'exécuter l'exemple de TemplatesDialog. Assurez-vous que TemplateList est correctement implémentée. Erreur: {e}")
        # print(sys.exc_info())  # Commenté car sys.exc_info() n'est pas fiable en Python 3
        # Afficher la trace complète pour une meilleure compréhension
        traceback.print_exc(file=sys.stdout)
        root.destroy()
