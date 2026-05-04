import tkinter as tk
from tkinter import ttk
import sys
import os


class TkApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TaskCoach - Tkinter")
        self.root.geometry("1000x700")

        # Configuration de l'application
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_content()

        # Variables pour les vues
        self.task_viewer = None
        self.category_viewer = None
        self.effort_viewer = None

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau", command=self.new_file)
        file_menu.add_command(label="Ouvrir", command=self.open_file)
        file_menu.add_command(label="Enregistrer", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)

        # Menu Édition
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Ajouter tâche", command=self.add_task)
        edit_menu.add_command(label="Modifier", command=self.edit_task)
        edit_menu.add_command(label="Supprimer", command=self.delete_task)

        # Menu Vue
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Vue", menu=view_menu)
        view_menu.add_command(label="Tâches", command=self.show_tasks)
        view_menu.add_command(label="Catégories", command=self.show_categories)
        view_menu.add_command(label="Efforts", command=self.show_efforts)

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root, relief=tk.RAISED, bd=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Boutons de la toolbar
        tk.Button(toolbar, text="Nouveau", command=self.new_file).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        tk.Button(toolbar, text="Ouvrir", command=self.open_file).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        tk.Button(toolbar, text="Enregistrer", command=self.save_file).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        tk.Button(toolbar, text="Tâches", command=self.show_tasks).pack(
            side=tk.LEFT, padx=2, pady=2
        )
        tk.Button(
            toolbar, text="Catégories", command=self.show_categories
        ).pack(side=tk.LEFT, padx=2, pady=2)

    def setup_main_content(self):
        # Zone principale avec séparation
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Pour simuler le comportement AUI, on utilisera des panes
        self.create_panes()

    def create_panes(self):
        # Création de panes pour les différents viewers
        self.pane_container = tk.PanedWindow(
            self.main_frame, orient=tk.VERTICAL
        )
        self.pane_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Zone pour le viewer de tâches
        self.task_frame = tk.Frame(self.pane_container)
        self.pane_container.add(self.task_frame)

        # Zone pour le viewer de catégories
        self.category_frame = tk.Frame(self.pane_container)
        self.pane_container.add(self.category_frame)

        # Zone pour le viewer d'efforts
        self.effort_frame = tk.Frame(self.pane_container)
        self.pane_container.add(self.effort_frame)

        # Initialiser les viewers
        self.init_task_viewer()
        self.init_category_viewer()
        self.init_effort_viewer()

    def init_task_viewer(self):
        # Création de la vue des tâches
        task_label = tk.Label(
            self.task_frame, text="Vue des Tâches", font=("Arial", 12, "bold")
        )
        task_label.pack(pady=5)

        # Liste des tâches (exemple simple)
        self.task_listbox = tk.Listbox(self.task_frame)
        self.task_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajouter quelques tâches d'exemple
        sample_tasks = ["Tâche 1", "Tâche 2", "Tâche 3"]
        for task in sample_tasks:
            self.task_listbox.insert(tk.END, task)

    def init_category_viewer(self):
        # Création de la vue des catégories
        category_label = tk.Label(
            self.category_frame,
            text="Vue des Catégories",
            font=("Arial", 12, "bold"),
        )
        category_label.pack(pady=5)

        # Liste des catégories (exemple simple)
        self.category_listbox = tk.Listbox(self.category_frame)
        self.category_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajouter quelques catégories d'exemple
        sample_categories = ["Catégorie 1", "Catégorie 2", "Catégorie 3"]
        for category in sample_categories:
            self.category_listbox.insert(tk.END, category)

    def init_effort_viewer(self):
        # Création de la vue des efforts
        effort_label = tk.Label(
            self.effort_frame,
            text="Vue des Efforts",
            font=("Arial", 12, "bold"),
        )
        effort_label.pack(pady=5)

        # Liste des efforts (exemple simple)
        self.effort_listbox = tk.Listbox(self.effort_frame)
        self.effort_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Ajouter quelques efforts d'exemple
        sample_efforts = ["Effort 1", "Effort 2", "Effort 3"]
        for effort in sample_efforts:
            self.effort_listbox.insert(tk.END, effort)

    def show_tasks(self):
        # Afficher la vue des tâches
        self.task_frame.pack(fill=tk.BOTH, expand=True)
        self.category_frame.pack_forget()
        self.effort_frame.pack_forget()

    def show_categories(self):
        # Afficher la vue des catégories
        self.category_frame.pack(fill=tk.BOTH, expand=True)
        self.task_frame.pack_forget()
        self.effort_frame.pack_forget()

    def show_efforts(self):
        # Afficher la vue des efforts
        self.effort_frame.pack(fill=tk.BOTH, expand=True)
        self.task_frame.pack_forget()
        self.category_frame.pack_forget()

    # Méthodes de gestion de fichiers
    def new_file(self):
        print("Nouveau fichier")

    def open_file(self):
        print("Ouvrir fichier")

    def save_file(self):
        print("Enregistrer fichier")

    def edit_task(self):
        print("Modifier tâche")

    def delete_task(self):
        print("Supprimer tâche")

    def quit_app(self):
        self.root.quit()

    def run(self):
        self.root.mainloop()
