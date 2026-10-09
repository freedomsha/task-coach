# -*- coding: utf-8 -*-
"""
Dialogue d'avertissement pour les problèmes XFCE4 avec Tkinter.
Basé sur le fichier xfce4warning.py original de Task Coach, utilisant
la classe de base dialogtk.Dialog.
"""
# Le fichier original utilise des fonctionnalités spécifiques à wxPython pour créer une boîte de dialogue avec un message d'avertissement et une case à cocher. J'ai réécrit ce code pour qu'il soit entièrement compatible avec Tkinter, en utilisant tk.Toplevel pour la fenêtre de dialogue et ttk pour les widgets.
#
# Voici le code converti. J'ai inclus une classe de démonstration pour que vous puissiez l'exécuter et voir le résultat. Le code est auto-suffisant et bien commenté pour que vous puissiez comprendre comment il s'adapte à Tkinter et à vos besoins.

# Je vais refactoriser votre fichier xfce4warningtk.py existant pour qu'il hérite de la classe dialogtk.Dialog, ce qui est la bonne approche pour assurer la cohérence avec le reste de votre conversion Tkinter.
#
# J'utiliserai :
#
#     from taskcoachlib.widgetstk.dialogtk import Dialog pour l'héritage.
#
#     La méthode fillInterior pour ajouter le contenu (le Label et le Checkbutton).
#
#     La méthode ok pour gérer la sauvegarde du paramètre, en vous assurant que l'appel à super().ok() ferme correctement la boîte de dialogue.
#
#     L'import _ est déjà en place.

# Cette nouvelle version est plus propre car elle tire parti de la structure de boîte de dialogue modale et de la gestion des boutons déjà implémentées dans votre fichier dialogtk.py.
#
# Pour récapituler les changements :
#
#     La classe XFCE4WarningDialog hérite maintenant de Dialog.
#
#     L'initialisation utilise super().__init__(..., button_types=("ok",))
#     pour s'aligner sur wx.OK.
#
#     Le contenu est créé dans fillInterior en utilisant ttk.Label
#     et ttk.Checkbutton avec un tk.BooleanVar.
#
#     La logique de sauvegarde des paramètres est déplacée
#     dans la méthode ok (qui est déclenchée par le bouton OK automatique de Dialog).
#
# C'est beaucoup plus proche de la manière dont les boîtes de dialogue sont structurées dans Task Coach !

#  Le fait d'avoir accès à la classe Settings réelle dans taskcoachlib.config nous permet de rendre xfce4warningtk.py beaucoup plus fidèle à l'application originale.
#
# Je vais mettre à jour xfce4warningtk.py pour :
#
#     Remplacer la classe Settings simulée par un import de la classe réelle : from taskcoachlib.config.settings import Settings.
#
#     Supprimer la classe Settings simulée et le bloc de test associé (if __name__ == '__main__':) qui ne sont plus nécessaires, car le fichier importera la classe réelle.

import sys
import tkinter as tk
from tkinter import ttk, messagebox
# Import des composants Task Coach convertis
from taskcoachlib.i18n import _
# Import de la classe Dialog convertie
from taskcoachlib.widgetstk.dialogtk import Dialog
# Import de la classe Settings réelle que vous venez de fournir
from taskcoachlib.config.settings import Settings


# # --- SIMULATIONS DE MODULES POUR LA DÉMONSTRATION ---
# # Dans votre code, vous importeriez les modules réels.
# def _(text):
#     return text


# class Settings:
#     """
#     Classe simulée pour gérer les paramètres.
#     """
#     def __init__(self):
#         self._settings = {"feature": {"showsmwarning": True}}
#
#     def getboolean(self, section, option):
#         return self._settings.get(section, {}).get(option, False)
#
#     def setboolean(self, section, option, value):
#         if section not in self._settings:
#             self._settings[section] = {}
#         self._settings[section][option] = value


# class XFCE4WarningDialog(tk.Toplevel):
class XFCE4WarningDialog(Dialog):
    """
    Boîte de dialogue modale pour avertir des problèmes de gestion de session XFCE4.
    Elle hérite de dialogtk.Dialog pour la structure et la gestion des boutons.
    """
    def __init__(self, parent: tk.Tk, settings: Settings):
        # settings est l'instance réelle de taskcoachlib.config.settings.Settings
        # super().__init__(parent)
        # self.transient(parent)
        # self.grab_set()
        # self.title(_('Avertissement'))

        self.__settings = settings
        # self.value = False
        #
        # self.protocol("WM_DELETE_WINDOW", self.on_ok)
        #
        # main_frame = ttk.Frame(self, padding=10)
        # main_frame.pack(fill="both", expand=True)
        #
        # self.fillInterior(main_frame)
        #
        # ok_button = ttk.Button(main_frame, text=_("OK"), command=self.on_ok)
        # ok_button.pack(pady=10)
        #
        # self.update_idletasks()
        # self.wait_window(self)

        # Utiliser super().__init__ et spécifier le type de bouton (par défaut est ("ok", "cancel")).
        # Dans l'original, c'était wx.OK, nous utilisons donc seulement "ok".
        super().__init__(parent, _('Warning'), button_types=("ok",))

    def createInterior(self, parent: ttk.Frame):
        """
        Crée le conteneur pour le contenu intérieur.
        """
        # Nous allons utiliser un Frame pour l'intérieur afin de mieux organiser le contenu
        interior = ttk.Frame(parent)
        return interior

    # def fillInterior(self, panel: ttk.Frame):
    def fillInterior(self):
        """
        Crée le contenu de la boîte de dialogue (texte d'avertissement et case à cocher).
        self._interior_frame fait référence au Frame créé par dialogtk.Dialog pour contenir les widgets.
        """
        # Construction du message à afficher
        # message = _('Task Coach a des problèmes connus avec la gestion de session XFCE4.\\n') + \
        #           _('Si vous rencontrez des blocages aléatoires au démarrage, veuillez décocher\\n') + \
        #           _('la case "Utiliser la gestion de session X11" dans l\'onglet Fonctionnalités des préférences.')
        message = _('Task Coach has known issues with XFCE4 session management.\n') + \
                  _('If you experience random freeze at startup, please uncheck\n'
                    'the "Use X11 session management" in the Features tab of the preferences.\n')

        # 1. Texte d'avertissement (wx.StaticText -> ttk.Label)
        # ttk.Label(panel, text=message).pack(pady=5)
        ttk.Label(self._interior_frame, text=message, justify=tk.LEFT).pack(pady=10, padx=10, fill='x')

        # Variable Tkinter pour l'état de la case à cocher
        # La case est cochée par défaut dans l'original (wx.CheckBox.SetValue(True))
        self._checkbox_var = tk.BooleanVar(value=True)

        # 2. Case à cocher (wx.CheckBox -> ttk.Checkbutton)
        # self._checkbox = ttk.Checkbutton(panel, text=_('Ne plus afficher ce dialogue au démarrage'))
        # self._checkbox.state(['selected'])
        self._checkbox = ttk.Checkbutton(
            self._interior_frame,
            text=_('Do not show this dialog at startup'),
            variable=self._checkbox_var
        )
        # self._checkbox.pack(pady=5)
        self._checkbox.pack(pady=5, padx=10, anchor='w')

    def on_ok(self):
        """
        Méthode appelée lorsque l'utilisateur clique sur OK.
        """
        show_warning = not self._checkbox.instate(['selected'])
        self.__settings.setboolean('feature', 'showsmwarning', show_warning)
        self.destroy()

    def ok(self, event=None):
        """
        Surcharge de la méthode ok pour sauvegarder le paramètre avant de fermer.
        """
        # L'original: self.__settings.setboolean('feature', 'showsmwarning', not self._checkbox.GetValue())
        # Si la case est cochée (True), nous voulons que le paramètre 'showsmwarning' soit False (ne pas montrer).
        show_warning = not self._checkbox_var.get()
        self.__settings.setboolean('feature', 'showsmwarning', show_warning)

        # Appel de la méthode parente pour détruire la fenêtre de dialogue
        super().ok(event)

# Note : le bloc if __name__ == '__main__': de test a été supprimé
# car il nécessiterait d'initialiser toute l'application Task Coach pour


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    settings = Settings()
    dialog = XFCE4WarningDialog(root, settings)

    # Afficher les paramètres après la fermeture du dialogue
    if not settings.getboolean('feature', 'showsmwarning'):
        messagebox.showinfo("Paramètres", "Le paramètre 'showsmwarning' est maintenant désactivé.")
    else:
        messagebox.showinfo("Paramètres", "Le paramètre 'showsmwarning' est toujours activé.")

    root.mainloop()
