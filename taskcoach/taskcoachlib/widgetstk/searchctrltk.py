# searchctrl.py pour Tkinter, converti de wxPython
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
"""
# Le fichier searchctrl.py de wxPython est assez complexe et dépend de plusieurs
# fonctionnalités spécifiques, notamment les boutons intégrés et les menus contextuels.
# Pour la conversion, j'ai utilisé les widgets ttk.Entry et ttk.Button pour
# créer une interface de recherche similaire.
# J'ai également réimplémenté la logique des menus contextuels en utilisant le module tkinter.Menu.

# J'ai réécrit le code de searchctrl.py pour Tkinter. L'implémentation utilise ttk.Frame pour contenir le champ de saisie (ttk.Entry) et les boutons. Le menu contextuel est géré par tkinter.Menu, et la logique de l'historique de recherche est gérée par une liste interne.
#
# J'ai inclus une version simplifiée de la classe ToolTipMixin pour que la classe SearchCtrl puisse en hériter, comme dans la version wxPython. J'ai aussi ajouté un exemple d'utilisation pour montrer comment le widget fonctionne dans une application Tkinter.

# 21/01/2026
# Vérification des fonctionnalités existantes:
#
# Je vais m'assurer que toutes les fonctionnalités de base sont implémentées correctement, telles que la saisie de texte, l'affichage du bouton d'annulation, le menu contextuel, l'historique de recherche et le rappel de la fonction de recherche.
# Je vérifierai la gestion des événements, notamment la liaison des événements clavier et des clics de souris aux fonctions appropriées.
#
#
# Compléments et améliorations:
#
# Info-bulles: Je vais intégrer complètement la classe ToolTip de tooltiptk.py pour afficher des info-bulles contextuelles sur le champ de recherche et les boutons.
# Icônes: Ajouter des icônes pour les boutons de recherche et d'annulation afin d'améliorer l'aspect visuel. Cela nécessitera l'utilisation du module PIL (Pillow) pour gérer les images, car Tkinter ne prend en charge que les formats GIF et PGM/PPM nativement 1.
# Thèmes et styles: Assurer l'intégration avec les thèmes Tkinter pour une apparence cohérente avec le reste de l'application 2.
# Validation des expressions régulières: Ajouter une validation pour s'assurer que l'expression régulière entrée par l'utilisateur est valide avant de lancer la recherche 3.
# Accessibilité: Améliorer l'accessibilité du widget pour les utilisateurs ayant des besoins spécifiques (par exemple, en utilisant des raccourcis clavier).
# Personnalisation: Offrir davantage d'options de personnalisation, telles que la possibilité de modifier les couleurs, les polices et les délais d'affichage de l'info-bulle.
#
#
# Anticipation des problèmes potentiels:
#
# Je vais identifier et corriger les éventuels problèmes de compatibilité avec différents widgets Tkinter 2.
# Je vais ajouter une gestion des erreurs pour éviter que des problèmes lors de l'affichage de l'info-bulle ne fassent planter l'application 4.
# Je vais vérifier l'existence de _tooltip dans la méthode _hide_tooltip pour éviter des erreurs si l'info-bulle a déjà été détruite 4.
#
#
# Intégration avec uicommandtk.py:
#
# Étant donné que uicommandtk.py est en cours de construction, je vais veiller à ce que la classe SearchCtrl soit facilement intégrable et configurable dans ce fichier.
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import Menu
import re
from taskcoachlib.widgetstk.tooltiptk import ToolTip
from taskcoachlib.i18n import _
from taskcoachlib.guitk.artprovidertk import getIcon
# try:
#     from PIL import Image, ImageTk  # Import Pillow modules
# except ImportError:
#     Image = None
#     ImageTk = None

log = logging.getLogger(__name__)


# # L'équivalent de la classe ToolTipMixin de tooltip.py
# # pour que SearchCtrl puisse l'utiliser.
# # Cette implémentation simplifiée n'affiche pas encore de tooltip.
# class ToolTipMixin:
#     def __init__(self):
#         self.tooltip_text = ""
#
#     def bind_tooltip(self, text):
#         self.tooltip_text = text
#         self.bind("<Enter>", self.on_enter)
#         self.bind("<Leave>", self.on_leave)
#
#     def on_enter(self, event):
#         # Logique pour afficher l'info-bulle (non implémentée ici)
#         print(f"Afficher l'info-bulle : {self.tooltip_text}")
#
#     def on_leave(self, event):
#         # Logique pour cacher l'info-bulle (non implémentée ici)
#         print("Cacher l'info-bulle")


# class SearchCtrl(ttk.Frame, ToolTipMixin):
# class SearchCtrl(ttk.Frame, ToolTip):
class SearchCtrl(ttk.Frame):
    """
    Une adaptation de wx.SearchCtrl pour Tkinter.
    """
    def __init__(self, parent, callback=None, matchCase=False,
                 includeSubItems=False, searchDescription=False,
                 regularExpression=False, value="", *args, **kwargs):

        # self.__callback = kwargs.pop("callback")
        # self.__matchCase = kwargs.pop("matchCase", False)
        # self.__includeSubItems = kwargs.pop("includeSubItems", False)
        # self.__searchDescription = kwargs.pop("searchDescription", False)
        # self.__regularExpression = kwargs.pop("regularExpression", False)
        # self.__bitmapSize = kwargs.pop("size", (16, 16))
        # value = kwargs.pop("value", "")
        super().__init__(parent, *args, **kwargs)
        # ToolTipMixin.__init__(self)
        # ToolTip.__init__(self, parent, *args, **kwargs)  # self, widget, text, delay=500, **kwargs

        self.__callback = callback
        # self.__callback = kwargs.pop("callback")
        self.__matchCase = tk.BooleanVar(value=matchCase)
        # self.__matchCase = kwargs.pop("matchCase", False)
        self.__includeSubItems = tk.BooleanVar(value=includeSubItems)
        # self.__includeSubItems = kwargs.pop("includeSubItems", False)
        self.__searchDescription = tk.BooleanVar(value=searchDescription)
        # self.__searchDescription = kwargs.pop("searchDescription", False)
        self.__regularExpression = tk.BooleanVar(value=regularExpression)
        # self.__regularExpression = kwargs.pop("regularExpression", False)
        # self.__bitmapSize = kwargs.pop("size", (16, 16))
        # value = kwargs.pop("value", "")
        self.__recentSearches = []
        self.__maxRecentSearches = 10  # Nombre maximum de recherches récentes à conserver
        self.__recentSearchMenuItemIds = []
        # value = value

        # self.columnconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Champ de recherche
        self.__entry = ttk.Entry(self)
        self.__entry.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self.__entry.bind("<Return>", self.on_search_button)
        self.__entry.bind("<KeyRelease>", self.on_entry_key_release)
        # self.__entry.setvar("value", value)  # Le nom de la variable ? "value"?
        self.__entry.insert(0, value)
        self.tooltip = ToolTip(self.__entry, text=_("Enter your search term here."))  # Info-bulle

        # Bouton d'annulation
        # # self.__cancel_button = ttk.Button(self, text="×", width=2, command=self.clear_search)
        # if Image and ImageTk:
        #     # cancel_img = Image.open("cancel_icon.png")  # Remplacez par le chemin de votre icône
        # cancel_icon = ImageTk.PhotoImage(cancel_img)
        cancel_icon = getIcon("cross_red_icon", (16,16))
        self.__cancel_button = ttk.Button(self, image=cancel_icon, width=2, command=self.clear_search)
        self.__cancel_button.image = cancel_icon  # Garder une référence pour éviter la suppression par le garbage collector
        # else:
        #     self.__cancel_button = ttk.Button(self, text="×", width=2, command=self.clear_search)
        self.__cancel_button.grid(row=0, column=1, sticky='e', padx=(0, 5))
        self.__cancel_button.grid_remove()  # Cacher par défaut
        self.cancel_tooltip = ToolTip(self.__cancel_button, text=_("Clear search"))

        # Bouton de recherche/menu
        # self.__search_button = ttk.Button(self, text="🔍", width=2, command=self.on_search_button)
        # if Image and ImageTk:
        #     search_img = Image.open("search_icon.png")  # Remplacez par le chemin de votre icône
        #     search_icon = ImageTk.PhotoImage(search_img)
        search_icon = getIcon("magnifier_glass_icon", (16,16))
        self.__search_button = ttk.Button(self, image=search_icon, width=2, command=self.on_search_button)
        self.__search_button.image = search_icon  # Garder une référence
        # else:
        #     self.__search_button = ttk.Button(self, text="🔍", width=2, command=self.on_search_button)
        self.__search_button.grid(row=0, column=2, sticky='e')
        self.__search_button.bind("<Button-1>", self.on_search_button)
        self.search_tooltip = ToolTip(self.__search_button, text=_("Show search options"))

        self.__create_menu()

    def getTextCtrl(self):
        """
        Retourne le contrôle de texte associé à la barre de recherche.

        Returns:
            ttk.Entry: Le contrôle de texte s'il existe, sinon None.
        """
        return self.__entry

    def __create_menu(self):
        """ Crée le menu contextuel. """
        self.menu = Menu(self, tearoff=0)
        self.menu.add_checkbutton(label="Match case", variable=self.__matchCase)
        self.menu.add_checkbutton(label="Include sub-items", variable=self.__includeSubItems)
        self.menu.add_checkbutton(label="Search description", variable=self.__searchDescription)
        self.menu.add_checkbutton(label="Regular expression", variable=self.__regularExpression)
        self.menu.add_separator()
        self.menu.add_command(label="Clear search history", command=self.clear_history)
        self.menu.add_separator()
        self.recent_searches_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Recent searches", menu=self.recent_searches_menu)
        self.__search_button.bind("<Button-1>", self.show_menu)

    def show_menu(self, event):
        """ Affiche le menu contextuel. """
        # TODO : utiliser ToolTip.show_tooltip() ! Non ?
        self.recent_searches_menu.delete(0, tk.END)
        for search_string in self.__recentSearches:
            self.recent_searches_menu.add_command(
                label=search_string,
                command=lambda s=search_string: self.set_value(s)
            )
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def on_entry_key_release(self, event):
        """ Met à jour la visibilité du bouton d'annulation. """
        if self.__entry.get():
            self.__cancel_button.grid()
        else:
            self.__cancel_button.grid_remove()

    def on_search_button(self, event=None):
        """ Appelle le callback de recherche et met à jour l'historique. """
        search_string = self.__entry.get()
        # if search_string and search_string not in self.__recentSearches:
        #     self.__recentSearches.insert(0, search_string)
        #     if len(self.__recentSearches) > 10:
        #         self.__recentSearches.pop()
        if search_string:
            self.remember_search_string(search_string)

        if self.__callback:
            # self.__callback(self.get_search_params())
            params = self.get_search_params()
            if params['regularExpression'] and not self.is_valid_regex(params['value']):
                self.tooltip.text = _("Invalid regular expression")
                self.tooltip.show_tooltip()  # Montrer l'info-bulle d'erreur
            else:
                self.tooltip.hide_tooltip()  # Cacher l'info-bulle si elle est visible
                self.__callback(params)

    def get_search_params(self):
        """ Retourne les paramètres de recherche. """
        return {
            'value': self.__entry.get(),
            'matchCase': self.__matchCase.get(),
            'includeSubItems': self.__includeSubItems.get(),
            'searchDescription': self.__searchDescription.get(),
            'regularExpression': self.__regularExpression.get()
        }

    def set_value(self, value):
        """ Définit la valeur du champ de recherche. """
        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, value)
        self.on_entry_key_release(None)

    def clear_search(self):
        """ Efface le champ de recherche. """
        self.__entry.delete(0, tk.END)
        self.on_entry_key_release(None)
        self.on_search_button()

    def clear_history(self):
        """ Efface l'historique des recherches. """
        self.__recentSearches.clear()
        self.update_recent_searches()


    def remember_search_string(self, search_string):
        """ Ajoute une chaîne de recherche à l'historique. """
        if search_string in self.__recentSearches:
            self.__recentSearches.remove(search_string)
        self.__recentSearches.insert(0, search_string)
        if len(self.__recentSearches) > self.__maxRecentSearches:
            self.__recentSearches.pop()
        self.update_recent_searches()

    def update_recent_searches(self):
        """ Met à jour le menu des recherches récentes. """
        self.recent_searches_menu.delete(0, tk.END)
        for search_string in self.__recentSearches:
            self.recent_searches_menu.add_command(
                label=search_string,
                command=lambda s=search_string: self.set_value(s)
            )

    def is_valid_regex(self, regex):
        """ Vérifie si une expression régulière est valide. """
        try:
            re.compile(regex)
            return True
        except re.error:
            return False

        # --- Exemple d'utilisation ---
if __name__ == '__main__':
    def my_search_callback(params):
        print("Recherche lancée avec les paramètres :")
        for key, value in params.items():
            print(f"- {key}: {value}")

    root = tk.Tk()
    root.title("Exemple de SearchCtrl")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    search_control = SearchCtrl(frame, callback=my_search_callback, matchCase=True)
    search_control.pack(fill=tk.X, padx=10, pady=10)

    # L'info-bulle est gérée par le mixin
    # search_control.bind_tooltip("Entrez votre terme de recherche ici.")
    # search_control._set_bindings()

    root.mainloop()

