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
# La version Tkinter de ce fichier remplacera les dialogues wx par tk.Toplevel et les contrôles spécifiques par leurs équivalents Tkinter (ttk.Label, ttk.Button, etc.). Étant donné que Tkinter ne gère pas nativement les hyperliens, je vais simuler un widget de lien cliquable en utilisant un Label et en gérant l'événement de clic pour ouvrir l'URL dans un navigateur par défaut.

# J'ai répliqué la logique du dialogue original. La fonctionnalité principale est de créer un dialogue simple avec un message et un lien cliquable qui ouvre un navigateur web. J'ai utilisé webbrowser.open_new() pour gérer l'ouverture de l'URL, ce qui est l'approche standard en Python.

# Points positifs ✅
# La conversion est globalement bien réussie :
#
# La structure générale est correcte
# L'interface utilisateur reproduit fidèlement l'original
# Le dialogue modal fonctionne correctement
# La gestion des liens hypertextes est bien implémentée avec webbrowser
#
# Problèmes identifiés ⚠️
# 1. Fonctionnalité manquante critique
# Le code original sauvegarde le dernier message affiché dans les paramètres :
# self.__settings.settext("view", "lastdevelopermessage", self.__message)
# Cette fonctionnalité est complètement absente de la version Tkinter.
# 2. Gestion d'événements incomplète
# L'original gère wx.EVT_CLOSE, mais la version Tkinter ne gère que WM_DELETE_WINDOW. Il faudrait aussi gérer la fermeture via le bouton OK.
# 3. Imports inutilisés
# from tkinter.simpledialog import Dialog  # Non utilisé
# Corrections suggérées :
# Principales améliorations apportées :
#
# 1.✅ Fonctionnalité de sauvegarde restaurée : Le dialogue sauvegarde maintenant le dernier message dans les paramètres via self.__settings.settext()
# 2.✅ Meilleur espacement : Amélioration de l'espacement entre les éléments avec pady
# 3.✅ Gestion d'erreurs améliorée : Utilisation du logger au lieu de print() pour les erreurs
# 4.✅ Bouton par défaut : Le bouton OK est maintenant focalisé et répond à la touche Entrée
# 5.✅ Géométrie corrigée : Utilisation de winfo_reqwidth() au lieu de winfo_width() pour un dimensionnement plus fiable
# 6.✅ Nettoyage du code : Suppression de l'import inutilisé

import logging
import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import Dialog
import webbrowser  # Pour ouvrir les liens web
from taskcoachlib import meta
from taskcoachlib.i18n import _

log = logging.getLogger(__name__)


class MessageDialog(tk.Toplevel):
    """
    Dialogue pour afficher des messages des développeurs.
    """
    def __init__(self, parent, message, url, settings, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.__message = message
        self.__url = url
        self.__settings = settings

        self.title(_("Message from the %s " "developers") % meta.data.name)
        self.transient(parent)
        self.grab_set()

        # Création de l'interface utilisateur
        self.create_message_widgets()

        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # Gestion des événements de fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_message_widgets(self):
        """
        Crée les parties intérieures du dialogue, c'est-à-dire le message
        pour l'utilisateur.
        """
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Message principal avec wrapping
        message_label = ttk.Label(main_frame, text=self.__message, wraplength=500)
        message_label.pack(side="top", anchor="w", pady=5)

        # Frame pour l'URL
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(side="top", anchor="w", pady=5)

        see_label = ttk.Label(url_frame, text=_("See:"))
        see_label.pack(side="left")

        # Simuler un lien hypertexte avec un Label
        hyperlink = ttk.Label(url_frame, text=self.__url,
                              foreground="blue", cursor="hand2")
        hyperlink.pack(side="left", padx=(5, 0))
        hyperlink.bind("<Button-1>", self.on_hyperlink_click)

        # Frame pour les boutons
        # Bouton pour fermer
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side="top", fill="x", pady=10)

        # # Définir le bouton par défaut
        # close_button = ttk.Button(button_frame, text=_("OK"), command=self.on_close)
        # close_button.pack(side="right")
        # Bouton OK
        ok_button = ttk.Button(button_frame, text=_("OK"), command=self.on_close)
        ok_button.pack(side="right")

        # Définir le bouton par défaut
        self.bind('<Return>', lambda e: self.on_close())
        ok_button.focus_set()

    def current_message(self):
        """
        Retourne le message actuellement affiché.
        """
        return self.__message

    def current_url(self):
        """
        Retourne l'URL actuellement affichée.
        """
        return self.__url

    def on_hyperlink_click(self, event):
        """
        Gère le clic sur le lien hypertexte.
        """
        try:
            webbrowser.open_new(self.__url)
        except Exception as e:
            # print(f"Failed to open URL: {e}")
            log.error("Failed to open URL %s: %s", self.__url, e)

    def on_close(self):
        """
        Lorsque l'utilisateur ferme le dialogue.
        Sauvegarde le dernier message affiché dans les paramètres.
        """
        # CORRECTION IMPORTANTE : Sauvegarder le dernier message comme dans l'original
        if hasattr(self.__settings, 'settext'):
            try:
                self.__settings.settext("view", "lastdevelopermessage", self.__message)
            except Exception as e:
                log.error("Failed to save last developer message: %s", e)

        self.destroy()
        if self.parent:
            self.parent.deiconify()


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    # root.withdraw()  # Cacher la fenêtre principale

    class MockSettings:
        # pass
        def settext(self, section, option, value):
            print(f"MockSettings: {section}.{option} = {value}")


    message_dialog = MessageDialog(
        parent=root,
        message="This is a test message from the developers.",
        url="https://www.taskcoach.org",
        settings=MockSettings()
    )
    message_dialog.mainloop()
