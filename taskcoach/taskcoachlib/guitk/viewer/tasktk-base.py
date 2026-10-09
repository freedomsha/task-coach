import tkinter as tk
from tkinter import ttk


class TaskViewer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent)

        # Configuration de la vue
        self.setup_ui()

    def setup_ui(self):
        # Titre
        title = tk.Label(
            self.frame, text="Vue des Tâches", font=("Arial", 14, "bold")
        )
        title.pack(pady=5)

        # Barre de recherche
        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Rechercher:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Liste des tâches
        self.task_tree = ttk.Treeview(
            self.frame,
            columns=("Nom", "Catégorie", "Priorité"),
            show="headings",
        )
        self.task_tree.heading("Nom", text="Nom")
        self.task_tree.heading("Catégorie", text="Catégorie")
        self.task_tree.heading("Priorité", text="Priorité")

        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.task_tree.yview
        )
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Boutons d'action
        button_frame = tk.Frame(self.frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Ajouter").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Modifier").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Supprimer").pack(side=tk.LEFT, padx=2)
