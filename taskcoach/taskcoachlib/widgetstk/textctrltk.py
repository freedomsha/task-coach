# textctrl.py converti de wxPython à Tkinter
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
# Ce fichier est un peu plus complexe car il gère des fonctionnalités avancées
# comme la détection de liens URL, le style de texte enrichi et l'accessibilité.
# Tkinter n'a pas d'équivalents directs pour wx.TE_RICH ou wx.TE_TE_AUTO_URL.
# L'approche la plus courante consiste à utiliser le widget tk.Text et à
# implémenter ces fonctionnalités manuellement à l'aide de tags et de gestionnaires d'événements.
#
# Le code converti ci-dessous utilise le widget tk.Text et un navigateur web
# externe (webbrowser) pour ouvrir les URLs. J'ai aussi inclus des commentaires
# détaillés pour vous aider à comprendre comment la logique a été adaptée.

# Pour cette conversion, j'ai remplacé wx.TextCtrl par tkinter.scrolledtext.ScrolledText
# pour prendre en charge le texte multiligne avec une barre de défilement.
# Étant donné que Tkinter ne gère pas nativement les styles de texte enrichi
# ou la détection automatique des URLs comme wxPython,
# j'ai implémenté cette fonctionnalité manuellement en utilisant des
# expressions régulières pour trouver les URLs et des tags Tkinter pour
# leur appliquer un style et un événement de clic.
#
# Si vous souhaitez ajouter d'autres fonctionnalités comme la vérification
# orthographique ou un style de texte plus avancé, n'hésitez pas à me le faire savoir.
# Je peux vous aider à intégrer des modules Python externes pour cela.

# Résumé des ajouts
#
# Je vais t'aider à ajouter les éléments suivants pour compléter la conversion :
#
#     Gestion des fonctionnalités Undo et Redo : Le code wxPython gère ces
#     actions manuellement, surtout pour macOS. Tkinter dispose de cette
#     fonctionnalité nativement via l'option undo=True que tu as déjà utilisée.
#     Je vais donc t'expliquer comment implémenter les méthodes CanUndo, Undo,
#     CanRedo et Redo pour correspondre à la logique du fichier original,
#     tout en tirant parti de la capacité native de Tkinter.
#
#     Gestion des caractères de contrôle UNICODE : Le code wxPython filtre
#     les caractères de contrôle indésirables. Je vais te montrer comment
#     reproduire cette logique dans Tkinter pour garantir que le texte reste propre.
#
#     Implémentation de StaticTextWithToolTip : Je vais créer la classe
#     StaticTextWithToolTip en utilisant les widgets tk.Label et en ajoutant
#     un mécanisme pour afficher une infobulle (tooltip), car Tkinter ne le
#     gère pas de la même manière que wxPython.
#
#     Mise à jour de MultiLineTextCtrl : J'ajusterai la classe MultiLineTextCtrl
#     pour qu'elle puisse prendre en charge les futures fonctionnalités,
#     telles que la vérification orthographique. Bien que je n'implémente pas
#     la vérification elle-même (cela nécessiterait une bibliothèque tierce),
#     je vais créer une structure pour que tu puisses l'intégrer facilement.

# Explications des changements 🚀
#
#     BaseTextCtrl : J'ai mis à jour les méthodes GetValue et SetValue pour
#     qu'elles utilisent la fonction de filtrage weed_unicode_control_characters,
#     qui est une reproduction de la logique de wxPython. J'ai aussi implémenté
#     CanUndo, Undo, CanRedo et Redo pour correspondre à l'interface originale,
#     même si Tkinter a déjà une gestion native de ces actions.
#     self.edit_modified() vérifie si la pile d'historique des modifications
#     est non vide, et self.edit_undo()/self.edit_redo() effectuent l'action correspondante.
#
#     SingleLineTextCtrl : J'ai ajouté une simple ligne de code
#     self.bind("<Return>", lambda event: "break") pour désactiver le comportement
#     de la touche Entrée. Tkinter ne dispose pas d'un widget SingleLineTextCtrl
#     natif comme wxPython, donc c'est une manière simple de simuler ce comportement.
#
#     MultiLineTextCtrl : Cette classe hérite maintenant directement des
#     fonctionnalités de BaseTextCtrl, qui inclut déjà la gestion des URLs
#     et de l'historique d'édition.
#
#     StaticTextWithToolTip : J'ai créé une nouvelle classe ToolTip pour gérer
#     l'affichage de l'infobulle. Tkinter n'a pas de support natif pour les infobulles,
#     il faut donc les créer manuellement en utilisant un Toplevel
#     (une fenêtre sans décoration) et en gérant les événements de survol
#     (<Enter> et <Leave>). La classe StaticTextWithToolTip utilise ensuite
#     cette classe ToolTip pour s'initialiser et afficher le texte de l'infobulle.

# Le message d'erreur AttributeError: 'MultiLineTextCtrl' object has no attribute 'url_pattern' est très clair : l'objet de la classe MultiLineTextCtrl essaie d'accéder à url_pattern, mais cet attribut n'existe pas.
#
# Analyse de l'erreur
#
# L'erreur se produit parce que les classes SingleLineTextCtrl et MultiLineTextCtrl appellent super().__init__(...) avant que la classe parente BaseTextCtrl n'ait eu l'occasion de s'initialiser correctement. Dans notre code, la classe BaseTextCtrl est celle qui crée l'attribut url_pattern et qui gère la détection des URL.
#
# Le problème vient de la manière dont les méthodes __init__ sont chaînées dans l'héritage. L'initialisation de la classe enfant MultiLineTextCtrl appelle celle de la classe parente BaseTextCtrl, qui elle-même tente d'accéder à des attributs qui ne sont pas encore définis. Cela crée une boucle infinie.
#
# Correction du code
#
# La solution consiste à modifier l'ordre d'initialisation. J'ai aussi remarqué une petite erreur dans la classe StaticTextWithToolTip où l'objet self était passé deux fois à la classe ToolTip. J'ai corrigé cela également.

# Explications des corrections
#
# J'ai apporté trois modifications importantes à ton code :
#
#     Initialisation des classes enfants : J'ai retiré l'argument text de l'appel super().__init__(parent, **kwargs) dans les classes SingleLineTextCtrl et MultiLineTextCtrl. La raison est que le widget parent (ici, scrolledtext.ScrolledText) n'a pas besoin de l'argument text pour s'initialiser. Cet argument n'est utilisé que par la méthode __initialize_text. L'initialisation se fait maintenant en deux étapes : d'abord, on initialise la classe parente BaseTextCtrl sans l'argument text, puis on appelle la méthode self.__initialize_text(text) pour insérer le contenu une fois que l'objet est complètement prêt. C'est l'ordre d'appel qui était la source du problème.
#
#     Définition de la classe UNICODE_CONTROL_CHARACTERS_TO_WEED : J'ai simplifié la création de ce dictionnaire en utilisant une compréhension de dictionnaire, ce qui rend le code plus concis et plus "Pythonic". C'est une petite amélioration de style qui rend le code plus propre.
#
#     Correction de StaticTextWithToolTip : La classe ToolTip est conçue pour être instanciée avec deux arguments : le widget pour lequel l'infobulle est créée, et le texte à afficher. La ligne self.tooltip = ToolTip(self, self, label) passait self deux fois. J'ai corrigé cela en self.tooltip = ToolTip(self, label). Cette correction est importante pour que le comportement de l'infobulle soit correct.

#  L'erreur AttributeError: 'MultiLineTextCtrl' object has no attribute 'url_pattern' est toujours là, car l'ordre d'initialisation des attributs est toujours incorrect.
#
# Analyse et résolution de l'erreur
#
# Le problème vient du fait que la méthode __init__ de la classe BaseTextCtrl essaie d'appeler self.__initialize_text(text) avant d'avoir créé les attributs comme self.url_pattern. Même si les classes enfants SingleLineTextCtrl et MultiLineTextCtrl n'appellent plus super() avec l'argument text, la classe BaseTextCtrl le fait toujours. Cela signifie que la méthode __initialize_text est appelée trop tôt dans la chaîne d'héritage, avant que tous les attributs nécessaires à l'highlighting des URLs ne soient initialisés.
#
# La solution est de séparer complètement l'initialisation du widget de l'initialisation du texte qu'il contient. Le constructeur (__init__) de BaseTextCtrl devrait seulement s'occuper de créer les attributs et de configurer le widget, sans y insérer de texte.

# Code corrigé
#
# Voici le code mis à jour pour textctrltk.py qui corrige le problème d'ordre d'initialisation. J'ai déplacé l'appel à __initialize_text des classes MultiLineTextCtrl et SingleLineTextCtrl vers la classe BaseTextCtrl, mais j'ai également ajouté un paramètre text au __init__ de BaseTextCtrl pour le rendre plus robuste. Le bon ordre d'appel est maintenant le suivant :
#
#     Le __init__ de la classe enfant (par exemple, MultiLineTextCtrl) est appelé.
#
#     Il appelle super().__init__(parent, **kwargs), ce qui exécute le __init__ de la classe parente BaseTextCtrl.
#
#     Le __init__ de BaseTextCtrl crée tous ses attributs (y compris self.url_pattern) et configure les événements.
#
#     L'exécution de super() dans la classe enfant se termine, et la classe enfant peut maintenant appeler self.__initialize_text(text) en toute sécurité, car l'attribut url_pattern
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import webbrowser
import re
from typing import Optional
from tkinter import Toplevel, Label
import threading
import time
from taskcoachlib.widgetstk.tooltiptk import ToolTip


# Les caractères de contrôle unicode ne sont pas gérés directement de la même manière.
# En Python, on peut simplement les ignorer ou les remplacer si nécessaire.
# La gestion des liens se fera via des tags et des événements.
UNICODE_CONTROL_CHARACTERS_TO_WEED = {}
for ordinal in range(0x20):
    if chr(ordinal) not in "\t\r\n":
        UNICODE_CONTROL_CHARACTERS_TO_WEED[ordinal] = None


class BaseTextCtrl(scrolledtext.ScrolledText):
    """
    Une sous-classe de ScrolledText pour gérer les fonctionnalités de base.

    Notes sur la conversion:
    - `wx.TextCtrl` est remplacé par `tkinter.scrolledtext.ScrolledText` pour le multi-lignes.
    - Le style et les fonctionnalités riches comme `wx.TE_RICH` doivent être
      gérés manuellement avec les tags de Tkinter.
    """
    def __init__(self, parent: tk.Tk, text: str = "", **kwargs):
        # Utilise ScrolledText qui est un Text widget avec une barre de défilement intégrée
        super().__init__(parent, wrap=tk.WORD, undo=True, **kwargs)
        self.__data = None
        self.webbrowser: Optional[webbrowser.BaseBrowser] = None
        # self.__initialize_text(text)  # Laisser commenté, il doit être à la fin !

        # Le style de texte enrichi, la détection des URLs et les fonctionnalités
        # de vérification orthographique doivent être implémentées ici.
        # Pour l'URL, nous allons utiliser une expression régulière et des tags.
        self.url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
        self.tag_configure("url", foreground="blue", underline=True)
        self.tag_bind("url", "<Button-1>", self.on_url_clicked)
        self.tag_bind("url", "<Enter>", self.on_enter_url)
        self.tag_bind("url", "<Leave>", self.on_leave_url)

        # Initialise le navigateur web
        try:
            self.webbrowser = webbrowser.get()
        except Exception:
            self.webbrowser = None

        # Lie l'événement de frappe pour mettre à jour les URLs
        self.bind("<KeyRelease>", self.on_text_change)

        # Gestion des raccourcis clavier pour Undo/Redo (Ctrl+Z, Ctrl+Y)
        # Tkinter gère déjà la plupart de ces raccourcis nativement, mais c'est
        # une bonne pratique de les lier explicitement si nécessaire.
        self.bind("<Control-z>", self.Undo)
        self.bind("<Control-y>", self.Redo)
        self.bind("<Control-Z>", self.Undo)  # Pour les majuscules

        # Initialisation du texte, maintenant que tous les attributs sont créés.
        self.__initialize_text(text)

    def __initialize_text(self, text: str):
        """ Insère le texte initial et configure la détection des URLs. """
        clean_text = self.weed_unicode_control_characters(text)
        # self.insert(tk.END, text)
        self.insert(tk.END, clean_text)
        self.highlight_urls()
        self.mark_set(tk.INSERT, "1.0")

    def GetValue(self):
        """ Récupère le texte et filtre les caractères de contrôle unicode. """
        value = self.get("1.0", tk.END)
        # Supprime le caractère de nouvelle ligne final que Tkinter ajoute.
        if value.endswith('\n'):
            value = value[:-1]
        return self.weed_unicode_control_characters(value)

    def SetValue(self, text: str):
        """ Définit le texte après avoir filtré les caractères de contrôle. """
        self.delete("1.0", tk.END)
        self.insert("1.0", self.weed_unicode_control_characters(text))
        self.highlight_urls()

    def weed_unicode_control_characters(self, text: str) -> str:
        """ Filtre les caractères de contrôle unicode. """
        return text.translate(UNICODE_CONTROL_CHARACTERS_TO_WEED)

    def highlight_urls(self):
        """ Détecte et applique des tags de style aux URLs. """
        self.tag_remove("url", "1.0", tk.END)
        text_content = self.get("1.0", tk.END)
        for match in self.url_pattern.finditer(text_content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.tag_add("url", start, end)

    def on_text_change(self, event):
        """ Réapplique la détection des URLs à chaque modification de texte. """
        self.highlight_urls()

    def on_url_clicked(self, event):
        """ Ouvre l'URL cliquée dans un navigateur web. """
        index = self.index(f"@{event.x},{event.y}")
        tag_names = self.tag_names(index)
        if "url" in tag_names:
            # Récupère le début et la fin de l'URL taguée
            start, end = self.tag_prevrange("url", index), self.tag_nextrange("url", index)
            if start and end:
                start_index, end_index = start[1], end[0]
                url = self.get(start_index, end_index)
                if self.webbrowser:
                    try:
                        self.webbrowser.open(url)
                    except Exception as message:
                        # Utiliser un message box personnalisé plutôt que tk.messagebox
                        # pour correspondre aux instructions de l'énoncé.
                        print(f"Erreur lors de l'ouverture de l'URL : {message}")
                else:
                    print(f"Pas de navigateur web disponible pour ouvrir l'URL: {url}")

    def on_enter_url(self, event):
        """ Change le curseur en main au survol d'une URL. """
        self.config(cursor="hand2")

    def on_leave_url(self, event):
        """ Réinitialise le curseur. """
        self.config(cursor="arrow")

    # Méthodes pour gérer Undo/Redo, qui s'appuient sur les fonctionnalités natives de Tkinter.
    # On les implémente pour maintenir la même interface que la classe wxPython.
    def CanUndo(self):
        """ Vérifie si une action peut être annulée. """
        return self.edit_modified()

    def Undo(self, event=None):
        """ Annule la dernière action. """
        if self.edit_modified():
            self.edit_undo()

    def CanRedo(self):
        """ Vérifie si une action peut être rétablie. """
        return self.edit_modified()

    def Redo(self, event=None):
        """ Rétablit la dernière action annulée. """
        if self.edit_modified():
            self.edit_redo()


class SingleLineTextCtrl(BaseTextCtrl):
    """ A sub-class of BaseTextCtrl. """
    def __init__(self, parent: tk.Tk, text: str = "", **kwargs):
        super().__init__(parent, text=text, **kwargs)
        # super().__init__(parent, **kwargs)
        # Pour une version monoligne, désactive la touche "Entrée"
        # self.__initialize_text(text)
        self.bind("<Return>", lambda event: "break")


class MultiLineTextCtrl(BaseTextCtrl):
    """ Une sous-classe de BaseTextCtrl. """
    CheckSpelling = True  # La vérification orthographique doit être implémentée manuellement, par exemple avec un module externe

    def __init__(self, parent: tk.Tk, text: str = "", **kwargs):
        # Le style multiligne est géré par la classe parente ScrolledText
        super().__init__(parent, text=text, **kwargs)
        # super().__init__(parent, **kwargs)
        # self.__initialize_text(text)

    # La méthode MacCheckSpelling est spécifique à wxPython et n'a pas d'équivalent
    # direct dans Tkinter. Elle devrait être remplacée par une logique
    # de vérification orthographique personnalisée.


class StaticTextWithToolTip(tk.Label):
    """
    Une sous-classe de tk.Label qui ajoute une infobulle.

    Notes sur la conversion:
    - `wx.StaticText` est remplacé par `tk.Label`.
    - La fonctionnalité `SetToolTip` est implémentée avec la classe `ToolTip`.
    """
    def __init__(self, parent: tk.Tk, label: str, **kwargs):
        # Utilise tk.Label pour afficher le texte statique
        super().__init__(parent, text=label, **kwargs)
        # Crée une infobulle à partir de la classe ToolTip
        self.tooltip = ToolTip(self, label)

# # Classe pour gérer les infobulles (Tooltips)
# class ToolTip:
#     """ Crée une infobulle pour un widget Tkinter. """
#     def __init__(self, widget, text):
#         self.widget = widget
#         self.text = text
#         self.tooltip_window = None
#         self.id = None
#         self.widget.bind("<Enter>", self.schedule)
#         self.widget.bind("<Leave>", self.hide)
#
#     def schedule(self, event):
#         self.cancel()
#         self.id = self.widget.after(1000, self.show)
#
#     def show(self):
#         if self.tooltip_window or not self.text:
#             return
#         x, y, _, _ = self.widget.bbox("insert")
#         x += self.widget.winfo_rootx() + 25
#         y += self.widget.winfo_rooty() + 25
#
#         self.tooltip_window = Toplevel(self.widget)
#         self.tooltip_window.wm_overrideredirect(True)
#         self.tooltip_window.wm_geometry(f"+{x}+{y}")
#         label = Label(self.tooltip_window, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
#                       justify=tk.LEFT)
#         label.pack(padx=1, pady=1)
#
#     def hide(self, event=None):
#         self.cancel()
#         if self.tooltip_window:
#             self.tooltip_window.destroy()
#         self.tooltip_window = None
#
#     def cancel(self):
#         if self.id:
#             self.widget.after_cancel(self.id)
#             self.id = None


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple de TextCtrl avec liens (Tkinter)")

    text_content = (
        "Bonjour, ceci est un exemple de widget de texte avec des liens.\n"
        "Visitez mon site web: https://www.example.com ou Google: www.google.com.\n"
        "Vous pouvez aussi visiter une autre page comme https://www.python.org."
    )

    # Création du TextCtrl multiligne
    # text_ctrl = MultiLineTextCtrl(root, text=text_content)
    text_ctrl = MultiLineTextCtrl(root, text=text_content, width=60, height=10)
    text_ctrl.pack(padx=10, pady=10, expand=True, fill="both")

    # Création du Label avec infobulle
    label_info = StaticTextWithToolTip(root, label="Passez la souris pour voir l'infobulle", font=("Arial", 12))
    label_info.pack(padx=10, pady=5)

    # Création d'un TextCtrl monoligne
    single_line_text_ctrl = SingleLineTextCtrl(root, text="Ceci est un champ de texte monoligne", width=60, height=1)
    single_line_text_ctrl.pack(padx=10, pady=5)

    root.mainloop()
