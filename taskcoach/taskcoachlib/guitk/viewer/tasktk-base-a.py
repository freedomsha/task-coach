import tkinter as tk
from tkinter import ttk


class TaskViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.setup_ui()

    def setup_ui(self):
        # Titre
        title = tk.Label(
            self.frame, text="Vue des Tâches", font=("Arial", 16, "bold")
        )
        title.pack(pady=10)

        # Barre d'outils
        toolbar = tk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(toolbar, text="Ajouter").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Modifier").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Supprimer").pack(side=tk.LEFT, padx=2)

        # Zone de recherche
        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Rechercher:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Treeview pour les tâches
        tree_frame = tk.Frame(self.frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Création du Treeview
        self.task_tree = ttk.Treeview(
            tree_frame,
            columns=("Nom", "Catégorie", "Priorité", "Statut"),
            show="headings",
        )
        self.task_tree.heading("Nom", text="Nom")
        self.task_tree.heading("Catégorie", text="Catégorie")
        self.task_tree.heading("Priorité", text="Priorité")
        self.task_tree.heading("Statut", text="Statut")

        # Définir la largeur des colonnes
        self.task_tree.column("Nom", width=200)
        self.task_tree.column("Catégorie", width=150)
        self.task_tree.column("Priorité", width=100)
        self.task_tree.column("Statut", width=100)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar_y = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview
        )
        self.task_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Scrollbar horizontale
        scrollbar_x = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview
        )
        self.task_tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Ajouter des données d'exemple
        self.add_sample_tasks()

    def add_sample_tasks(self):
        tasks = [
            ("Tâche 1", "Développement", "Haute", "En cours"),
            ("Tâche 2", "Design", "Moyenne", "Terminée"),
            ("Tâche 3", "Test", "Basse", "À faire"),
            ("Tâche 4", "Documentation", "Moyenne", "En cours"),
            ("Tâche 5", "Déploiement", "Haute", "À faire"),
        ]

        for task in tasks:
            self.task_tree.insert("", tk.END, values=task)
