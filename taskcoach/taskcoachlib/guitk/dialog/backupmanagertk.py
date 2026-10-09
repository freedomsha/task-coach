# -*- coding: utf-8 -*-

"""
Task Coach - Votre gestionnaire de tâches amical
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre option) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION ou D'ADÉQUATION À UN USAGE PARTICULIER. Voir la
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Si ce n'est pas le cas, consultez <http://www.gnu.org/licenses/>.
"""
# gère des listes de fichiers et des sélections.

# J'ai recréé la boîte de dialogue de gestion des sauvegardes en utilisant
# tk.Toplevel et des widgets comme ttk.Listbox pour les listes de fichiers
# et de sauvegardes, ainsi que des boutons et des étiquettes pour l'interface utilisateur.

# J'ai adapté le code pour utiliser Tkinter, en remplaçant les composants
# spécifiques à wxPython. J'ai aussi ajouté un gestionnaire pour le cas où
# un fichier initial est sélectionné, et j'ai recréé la logique des boutons
# et des listes de sélection pour qu'elle fonctionne avec les widgets Tkinter.

# Principales améliorations apportées :
# 1. Structure fidèle à l'original
#
# Utilisation de ttk.Treeview au lieu de Listbox pour reproduire les colonnes de wx.ListCtrl
# Conservation de la méthode restoredFilename() pour la compatibilité
# Utilisation de listFiles() au lieu de listFilenames() pour correspondre à l'original
#
# 2. Interface utilisateur améliorée
#
# Layout en colonnes avec ttk.LabelFrame pour une meilleure organisation
# Barres de défilement pour les listes
# Bouton "Restore" positionné comme dans l'original
# Fenêtre redimensionnable avec taille minimale
#
# 3. Gestion des événements
#
# Conversion correcte des événements wxPython vers Tkinter
# <<TreeviewSelect>> remplace wx.EVT_LIST_ITEM_SELECTED
# Gestion cohérente de la sélection/désélection
#
# 4. Corrections importantes
#
# Bug dans listFilenames() : L'original utilise listFiles(), pas listFilenames()
# Gestion des index : Utilisation correcte des index de Treeview
# État des widgets : Activation/désactivation appropriée des contrôles
# Gestion d'erreurs : Ajout de try/catch et logging
#
# 5. Compatibilité
#
# Conservation de la variable __filename pour restoredFilename()
# Méthode DoClose() au lieu de on_close() pour correspondre à l'original
# Même logique de sélection de fichier initial
#
# 6. Améliorations Tkinter
#
# Fenêtre modale correcte avec transient() et grab_set()
# Centrage automatique de la fenêtre
# Libération correcte du grab lors de la fermeture
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from taskcoachlib.i18n import _
from taskcoachlib.persistence import BackupManifest
from taskcoachlib import render
# Les importations pour wx sont remplacées par celles de Tkinter
# et les classes correspondantes.

log = logging.getLogger(__name__)


class BackupManagerDialog(tk.Toplevel):
    """
    Dialogue pour gérer les sauvegardes de fichiers.
    """
    def __init__(self, parent, settings, selectedFile=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.title(_("Backup Manager"))
        self.transient(parent)  # Rendre la fenêtre modale
        self.grab_set()

        # Variables d'instance
        self.__manifest = BackupManifest(settings)
        # self.__selected_file = selectedFile
        self.__filenames = self.__manifest.listFiles()  # Utiliser listFiles() comme dans l'original
        self.__filename = selectedFile  # Pour compatibilité avec restoredFilename()
        self.__selection = (None, None)

        # Sélectionner le fichier initial si fourni
        # self.__filenames = self.__manifest.listFilenames()
        # if self.__selected_file in self.__filenames:
        #     self.__filenames.remove(self.__selected_file)
        #     self.__filenames.insert(0, self.__selected_file)
        if selectedFile and selectedFile in self.__filenames:
            index = self.__filenames.index(selectedFile)
            self.__files_listbox.selection_set(index)
            self.__files_listbox.activate(index)
            self._OnSelectFile(None)

        # Création de l'interface utilisateur
        self.create_widgets()

        # if self.__selected_file:
        #     self.select_initial_file()

        # Configurer la fenêtre
        self.geometry("600x400")
        self.minsize(400, 300)

        # Centrer la fenêtre
        self.center_window()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """
        Crée et organise les widgets dans le dialogue.
        """
        # Frame principal avec padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Frame horizontal pour les listes
        lists_frame = ttk.Frame(main_frame)
        lists_frame.pack(fill="both", expand=True, pady=(0, 10))

        # # Section des fichiers
        # files_label = ttk.Label(main_frame, text=_("Files:"))
        # files_label.pack(anchor="w")

        # Section fichiers
        # files_frame = ttk.Frame(main_frame)
        files_frame = ttk.LabelFrame(lists_frame, text=_("Files"), padding="5")
        # files_frame.pack(fill="both", expand=True)
        files_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.__files_listbox = tk.Listbox(files_frame, selectmode="single")
        self.__files_listbox.pack(side="left", fill="both", expand=True)
        self.__files_listbox.bind("<<ListboxSelect>>", self._OnSelectFile)
        # Treeview pour les fichiers (pour avoir des colonnes comme dans l'original)
        self.__files = ttk.Treeview(files_frame, columns=("fullpath",), show="tree headings", selectmode="browse")
        self.__files.heading("#0", text=_("File"))
        self.__files.heading("fullpath", text=_("Full path"))

        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.__files.yview)
        self.__files.configure(yscrollcommand=files_scrollbar.set)

        self.__files.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")

        # # Remplir la liste des fichiers
        # for filename in self.__filenames:
        #     self.__files_listbox.insert("end", os.path.basename(filename))

        # Section des sauvegardes
        # backups_label = ttk.Label(main_frame, text=_("Backups:"))
        # backups_label.pack(anchor="w", pady=(10, 0))

        # backups_frame = ttk.Frame(main_frame)
        backups_frame = ttk.LabelFrame(lists_frame, text=_("Backups"), padding="5")
        # backups_frame.pack(fill="both", expand=True)
        backups_frame.pack(side="left", fill="both", expand=True, padx=(5, 5))

        # self.__backups_listbox = tk.Listbox(backups_frame, selectmode="single", state="disabled")
        # self.__backups_listbox.pack(side="left", fill="both", expand=True)
        # self.__backups_listbox.bind("<<ListboxSelect>>", self._OnSelectBackup)
        # Treeview pour les sauvegardes
        self.__backups = ttk.Treeview(backups_frame, columns=(), show="tree", selectmode="browse")
        self.__backups.heading("#0", text=_("Date"))

        backups_scrollbar = ttk.Scrollbar(backups_frame, orient="vertical", command=self.__backups.yview)
        self.__backups.configure(yscrollcommand=backups_scrollbar.set)

        self.__backups.pack(side="left", fill="both", expand=True)
        backups_scrollbar.pack(side="right", fill="y")

        # Initialement désactivé
        self.__backups.configure(state="disabled")

        # # Boutons
        # button_frame = ttk.Frame(self)
        # button_frame.pack(fill="x", pady=(0, 10), padx=10)

        # self.__btnRestore = ttk.Button(button_frame, text=_("Restore"), command=self._OnRestore, state="disabled")
        # self.__btnRestore.pack(side="right", padx=5)
        # Frame pour le bouton Restore
        restore_frame = ttk.Frame(lists_frame)
        restore_frame.pack(side="right", fill="y", padx=(5, 0))

        self.__btnRestore = ttk.Button(restore_frame, text=_("Restore"), command=self._OnRestore)
        self.__btnRestore.pack(anchor="n", pady=(0, 5))
        self.__btnRestore.configure(state="disabled")

        # btnCancel = ttk.Button(button_frame, text=_("Cancel"), command=self.on_close)
        # btnCancel.pack(side="right")
        # Frame pour les boutons de fermeture
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")

        close_btn = ttk.Button(buttons_frame, text=_("Close"), command=self.DoClose)
        close_btn.pack(side="right")

        # Remplir la liste des fichiers
        self.populate_files()

        # Bind des événements
        self.__files.bind("<<TreeviewSelect>>", self._OnSelectFile)
        self.__backups.bind("<<TreeviewSelect>>", self._OnSelectBackup)

    def populate_files(self):
        """Remplit la liste des fichiers."""
        for filename in self.__filenames:
            basename = os.path.basename(filename)
            self.__files.insert("", "end", text=basename, values=(filename,))

    def center_window(self):
        """Centre la fenêtre sur son parent."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def restoredFilename(self):
        """Retourne le nom du fichier restauré (compatibilité avec l'original)."""
        return self.__filename

    def DoClose(self):
        """Ferme le dialogue."""
        self.grab_release()
        self.destroy()

    def select_initial_file(self):
        """
        Sélectionne initialement le fichier si un a été passé en paramètre.
        """
        if self.__selected_file:
            try:
                index = self.__filenames.index(self.__selected_file)
                self.__files_listbox.selection_set(index)
                self._OnSelectFile(None)
            except ValueError:
                pass

    def _OnSelectFile(self, event):
        """
        Gère la sélection d'un fichier dans la liste.
        """
        # selected_index = self.__files_listbox.curselection()
        selection = self.__files.selection()
        # if not selected_index:
        if not selection:
            self._OnDeselectFile(event)
            return

        # index = selected_index[0]
        item = selection[0]
        # filename = self.__filenames[index]
        filename = self.__files.item(item, "values")[0]
        # self.__selection = (filename, None)

        # self.__backups_listbox.config(state="normal")
        # self.__backups_listbox.delete(0, "end")
        # Effacer la liste des sauvegardes
        for item in self.__backups.get_children():
            self.__backups.delete(item)

        try:
            # Remplir la liste des sauvegardes
            backups = self.__manifest.listBackups(filename)
            # for backup_time in backups:
            #     self.__backups_listbox.insert("end", backup_time.strftime("%Y-%m-%d %H:%M:%S"))
            for dateTime in backups:
                date_str = render.dateTime(dateTime, humanReadable=True)
                self.__backups.insert("", "end", text=date_str)

            # Activer la liste des sauvegardes
            self.__backups.configure(state="normal")
            self.__selection = (filename, None)
        except Exception as e:
            log.error(f"Erreur lors du chargement des sauvegardes: {e}")
            messagebox.showerror(_("Error"), _("Could not list backups for the selected file."))
            # print(e)
            self._OnDeselectFile(event)

    def _OnDeselectFile(self, event):
        """
        Gère la désélection d'un fichier.
        """
        # self.__btnRestore.config(state="disabled")
        self.__btnRestore.configure(state="disabled")
        # self.__backups_listbox.delete(0, "end")
        for item in self.__backups.get_children():
            self.__backups.delete(item)
        # self.__backups_listbox.config(state="disabled")
        self.__backups.configure(state="disabled")
        self.__selection = (None, None)

    def _OnSelectBackup(self, event):
        """
        Gère la sélection d'une sauvegarde.
        """
        # selected_index = self.__backups_listbox.curselection()
        selection = self.__backups.selection()
        # if not selected_index:
        if not selection or self.__selection[0] is None:
            self._OnDeselectBackup(event)
            return

        # filename = self.__selection[0]
        item = selection[0]
        index = self.__backups.index(item)
        filename = self.__selection[0]

        # backup_time_str = self.__backups_listbox.get(selected_index[0])
        # backup_time = datetime.strptime(backup_time_str, "%Y-%m-%d %H:%M:%S")
        # self.__selection = (filename, backup_time)
        # self.__btnRestore.config(state="normal")
        try:
            backups = self.__manifest.listBackups(filename)
            dateTime = backups[index]
            self.__selection = (filename, dateTime)
            self.__btnRestore.configure(state="normal")
        except (IndexError, Exception) as e:
            log.error(f"Erreur lors de la sélection de la sauvegarde: {e}")
            self._OnDeselectBackup(event)

    def _OnDeselectBackup(self, event):
        """
        Gère la désélection d'une sauvegarde.
        """
        # self.__btnRestore.config(state="disabled")
        self.__btnRestore.configure(state="disabled")
        # self.__selection = (self.__selection[0], None)
        if self.__selection[0] is not None:
            self.__selection = (self.__selection[0], None)

    def _OnRestore(self, event=None):
        """
        Gère le processus de restauration.
        """
        filename, dateTime = self.__selection
        if not filename or not dateTime:
            return

        # Dialogue de sauvegarde
        # destination_filename = filedialog.asksaveasfilename(
        destination = filedialog.asksaveasfilename(
            parent=self,
            title=_("Choose the restoration destination"),
            initialdir=os.path.dirname(filename),
            initialfile=os.path.basename(filename),
            defaultextension=".tsk",
            filetypes=[(_("Task Coach files"), "*.tsk")],
        )

        # if destination_filename:
        if destination:
            try:
                # self.__manifest.restoreFile(filename, dateTime, destination_filename)
                self.__filename = destination
                self.__manifest.restoreFile(filename, dateTime, destination)
                messagebox.showinfo(_("Success"), _("File restored successfully!"))
                self.grab_release()
                self.destroy()
            except Exception as e:
                log.error(f"Erreur lors de la restauration: {e}")
                messagebox.showerror(_("Error"), _("Could not restore the file."))
                # print(e)

        self.on_close()

    def on_close(self):
        """
        Ferme le dialogue.
        """
        self.destroy()
        self.parent.deiconify()  # Restaurer la fenêtre parente si elle était masquée


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    # root.withdraw()  # Cacher la fenêtre principale

    # Créer une instance de dialogue
    # Note: `settings` doit être une instance de `Settings` de Task Coach
    # J'utilise une classe factice pour cet exemple
    class MockSettings:
        def get(self, section, name, default=None):
            return ""

    # class MockApp:
    #     def __init__(self):
    #         self.settings = MockSettings()

    # app = MockApp()
    # backup_dialog = BackupManagerDialog(root, settings=app.settings)
    # backup_dialog.mainloop()
    try:
        dialog = BackupManagerDialog(root, MockSettings())
        dialog.mainloop()
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        root.destroy()
