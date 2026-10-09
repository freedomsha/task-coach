import tkinter as tk
from tkinter import ttk
import sys
import os


class TkApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TaskCoach - Tkinter")
        self.root.geometry("1200x800")

        # Initialiser les vues
        self.init_views()

        # Configuration de l'application
        self.setup_menu()
        self.setup_toolbar()
        self.setup_main_content()

        # Initialiser les données
        self.init_data()

    def init_views(self):
        # Importer les vues
        try:
            from taskcoachlib.guitk.taskviewer import TaskViewer
            from taskcoachlib.guitk.categoryviewer import CategoryViewer
            from taskcoachlib.guitk.effortviewer import EffortViewer

            self.task_viewer = TaskViewer(self.root)
            self.category_viewer = CategoryViewer(self.root)
            self.effort_viewer = EffortViewer(self.root)
        except ImportError as e:
            print(f"Erreur d'importation des vues : {e}")
            # Créer des vues de secours
            self.create_fallback_views()

    def create_fallback_views(self):
        # Vue de secours si import échoue
        self.task_viewer = None
        self.category_viewer = None
        self.effort_viewer = None
        print("Vues de secours créées")

    def init_data(self):
        # Initialiser les données
        print("Initialisation des données...")
        try:
            # Simuler l'initialisation des données
            self.load_sample_data()
        except Exception as e:
            print(f"Erreur lors du chargement des données : {e}")

    def load_sample_data(self):
        # Charger des données d'exemple
        print("Chargement des données d'exemple...")

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

        # Menu Vue
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Vue", menu=view_menu)
        view_menu.add_command(label="Tâches", command=self.show_tasks)
        view_menu.add_command(label="Catégories", command=self.show_categories)
        view_menu.add_command(label="Efforts", command=self.show_efforts)

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root, relief=tk.RAISED, bd=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="Nouveau", command=self.new_file).pack(
            side=tk.LEFT, padx=2
        )
        tk.Button(toolbar, text="Ouvrir", command=self.open_file).pack(
            side=tk.LEFT, padx=2
        )
        tk.Button(toolbar, text="Enregistrer", command=self.save_file).pack(
            side=tk.LEFT, padx=2
        )

    def setup_main_content(self):
        # Zone principale
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Afficher la vue des tâches par défaut
        self.show_tasks()

    def show_tasks(self):
        # Nettoyer le contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Afficher la vue des tâches
        if hasattr(self, "task_viewer") and self.task_viewer:
            self.task_viewer.frame.pack(fill=tk.BOTH, expand=True)
        else:
            # Vue de secours
            self.create_fallback_view("Tâches")

    def show_categories(self):
        # Nettoyer le contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Afficher la vue des catégories
        if hasattr(self, "category_viewer") and self.category_viewer:
            self.category_viewer.frame.pack(fill=tk.BOTH, expand=True)
        else:
            # Vue de secours
            self.create_fallback_view("Catégories")

    def show_efforts(self):
        # Nettoyer le contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Afficher la vue des efforts
        if hasattr(self, "effort_viewer") and self.effort_viewer:
            self.effort_viewer.frame.pack(fill=tk.BOTH, expand=True)
        else:
            # Vue de secours
            self.create_fallback_view("Efforts")

    def create_fallback_view(self, title):
        # Vue de secours simple
        frame = tk.Frame(self.content_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            frame,
            text=f"Vue {title} (vue de secours)",
            font=("Arial", 12, "bold"),
        )
        label.pack(pady=20)

        text = tk.Text(frame)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(
            tk.END,
            f"Contenu de la vue {title} (à remplacer par l'implémentation complète)",
        )

    def new_file(self):
        print("Nouveau fichier")

    def open_file(self):
        print("Ouvrir fichier")

    def save_file(self):
        print("Enregistrer fichier")

    def quit_app(self):
        self.root.quit()

    def run(self):
        self.root.mainloop()
