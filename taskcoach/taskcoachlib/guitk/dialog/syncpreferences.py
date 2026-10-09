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
"""
# Points clés de la conversion :
#
#
# Héritage et imports :
#
# taskcoachlib.gui.dialog.preferences est remplacé par taskcoachlib.guitk.dialog.preferencestk .
# taskcoachlib.widgets.NotebookDialog est remplacé par taskcoachlib.guitk.dialog.dialogtk.Dialog car on n'utilise plus NotebookDialog de wxPython mais un Dialog de base et un Notebook de tkinter.ttk .
#
#
#
# Adaptation de l'initialisation :
#
# J'ai adapté les appels à super().__init__ pour correspondre à la syntaxe de Tkinter et aux classes de base que tu m'as fournies.
# J'ai ajouté self.parent = parent dans les constructeurs pour conserver une référence à la fenêtre parente, ce qui est utile pour certaines opérations de Tkinter.
#
#
#
# Méthodes d'ajout de paramètres :
#
# J'ai utilisé les méthodes _add...Setting de la classe de base PreferencesPage (dans preferencestk.py) pour créer les différents éléments de l'interface utilisateur (cases à cocher, champs de texte, listes déroulantes).
#
#
#
# Gestion des événements :
#
# Les liaisons d'événements wx.EVT_* ont été supprimées, car Tkinter gère les événements différemment.
# J'ai simulé le comportement des événements en appelant directement les fonctions de mise à jour de l'état des champs. Dans une application réelle, tu devrais utiliser les mécanismes d'événements de Tkinter (bind).
#
#
#
# État des champs :
#
# J'ai ajouté des méthodes enable_text_setting et enable_choice_setting pour activer ou désactiver les champs en fonction de l'état des cases à cocher.
#
#
#
# Simulations :
#
# J'ai inclus une classe MockSyncMLConfig pour simuler la configuration SyncML, car l'implémentation complète n'est pas disponible. Tu devras remplacer cette simulation par la logique réelle de ton application.
# J'ai commenté les lignes de code qui font référence à des fonctionnalités spécifiques de wxPython (par exemple, self.CentreOnParent()). Tu devras trouver des alternatives Tkinter si tu as besoin de ces fonctionnalités.
#
#
#
# Titre des pages
#
# J'ai ajouté pageTitle dans SyncMLAccessPage pour afficher le titre.
#
#
#
# Remplacement applySettings par ok
#
# J'ai remplacé ok par applySettings pour correspondre au nouveau nommage de la fonction.
#
#
#
# Comment utiliser ce code :
#
# Remplace les simulations : Remplace les classes et fonctions simulées par les implémentations réelles de ton application.
# Teste et adapte : Teste attentivement le code et adapte-le en fonction des besoins de ton application.
# Intègre les événements : Si tu as besoin de gérer des événements spécifiques (par exemple, la modification d'une case à cocher), utilise les mécanismes d'événements de Tkinter (bind).
from builtins import str
import tkinter as tk
from tkinter import ttk

from taskcoachlib.widgetstk import dialogtk  # Remplacement de l'import wx
from taskcoachlib.guitk.dialog.preferencestk import PreferencesPage  # Import ajusté
from taskcoachlib import operating_system
from taskcoachlib.i18n import _
from tkinter import messagebox


class SyncMLBasePage(PreferencesPage):
    """Base class for SyncML preference pages."""
    pageTitle = _("Untitled SyncML Page")

    # def __init__(self, iocontroller=None, *args, **kwargs):
    def __init__(self, parent, settings, iocontroller=None, *args, **kwargs):
        self.iocontroller = iocontroller
        # NOTE : PreferencesPage.__init__ requiert parent et settings comme arguments positionnels/nommés.
        # super().__init__(*args, **kwargs)
        # Appel à la classe mère (PreferencesPage) avec les arguments requis.
        super().__init__(parent=parent, settings=settings, *args, **kwargs)
        # self.parent = parent # Déjà géré par PreferencesPage.__init__ mais peut être conservé si nécessaire
        # # Simuler self.config car l'implémentation complète n'est pas fournie
        # self.config = MockSyncMLConfig()
        # self.config = iocontroller.syncMLConfig()
        self.sync_config = iocontroller.syncMLConfig()

    # def get(self, section, name):
    def get(self, section, name, default=None):
        # Implémentation simulée pour l'exemple
        if section == 'access':
            if name in ['syncUrl']:
                return self.config.access_syncUrl
            elif name in ['username']:
                return self.config.access_username
        elif section == 'task':
            if name == 'dosync':
                return self.config.task_dosync
            elif name == 'uri':
                return self.config.task_uri
            elif name == 'preferredsyncmode':
                return self.config.task_preferredsyncmode
        elif section == 'note':
            if name == 'dosync':
                return self.config.note_dosync
            elif name == 'uri':
                return self.config.note_uri
            elif name == 'preferredsyncmode':
                return self.config.note_preferredsyncmode
        return ''

    def set(self, section, name, value):
        # Implémentation simulée pour l'exemple
        if section == 'access':
            if name in ['syncUrl']:
                self.config.access_syncUrl = value
            elif name in ['username']:
                self.config.access_username = value
        elif section == 'task':
            if name == 'dosync':
                self.config.task_dosync = value
            elif name == 'uri':
                self.config.task_uri = value
            elif name == 'preferredsyncmode':
                self.config.task_preferredsyncmode = value
        elif section == 'note':
            if name == 'dosync':
                self.config.note_dosync = value
            elif name == 'uri':
                self.config.note_uri = value
            elif name == 'preferredsyncmode':
                self.config.note_preferredsyncmode = value

    def applySettings(self):  # Renommée en applySettings pour correspondre à preferencestk.py
        super().applySettings()
        self.iocontroller.SyncMLConfig(self.config)  # La logique réelle n'est pas disponible


class SyncMLAccessPage(SyncMLBasePage):
    pageTitle = _("SyncML Access")  # Ajout du titre de la page

    # def __init__(self, parent, iocontroller=None, *args, **kwargs):  # Ajout de parent
    def __init__(self, parent, iocontroller=None, settings=None, *args, **kwargs):  # Ajout de parent
        self.config = settings # Stocke l'objet SyncMLConfig (alias 'settings' dans ce contexte)
        # Nous appelons SyncMLPage.__init__ qui doit transmettre settings à PreferencesPage.
        # Nous passons explicitement settings
        # super().__init__(iocontroller=iocontroller, parent=parent, *args, **kwargs)  # Ajout de parent
        super().__init__(parent=parent, iocontroller=iocontroller, settings=settings, *args, **kwargs)
        self.parent = parent  # Stockage du parent
        self.settings = settings

        # SyncML Server (Choix)
        choices_preset = [('0', _('Custom')), ('1', _('MemoToo (http://www.memotoo.com/)')),
                          ('2', _('Horde-based'))]
        self.preset_var = tk.StringVar(value=self.get('access', 'preset'))
        self._addChoiceSetting('access', 'preset', _('SyncML server'), choices_preset)

        # SyncML server URL
        self._addTextSetting('access', 'syncUrl', _('SyncML server URL'))

        # User name/ID
        self._addTextSetting('access', 'username', _('User name/ID'))

        # Tasks synchronization
        self._addBooleanSetting('task', 'dosync', _('Enable tasks synchronization'))

        # Tasks database name
        self._addTextSetting('task', 'uri', _('Tasks database name'))

        # Preferred synchronization mode
        choices_sync_mode = [('TWO_WAY', _('Two way')), ('SLOW', _('Slow')), ('ONE_WAY_FROM_CLIENT', _('One way from client')),
                             ('REFRESH_FROM_CLIENT', _('Refresh from client')), ('ONE_WAY_FROM_SERVER', _('One way from server')),
                             ('REFRESH_FROM_SERVER', _('Refresh from server'))]
        self._addChoiceSetting('task', 'preferredsyncmode', _('Preferred synchronization mode'), choices_sync_mode)

        # Notes synchronization
        self._addBooleanSetting('note', 'dosync', _('Enable notes synchronization'))

        # Notes database name
        self._addTextSetting('note', 'uri', _('Notes database name'))

        # Preferred synchronization mode (Notes)
        self._addChoiceSetting('note', 'preferredsyncmode', _('Preferred synchronization mode'), choices_sync_mode)

        # Initialisation de l'état des champs
        self.update_field_states()

    def update_field_states(self):
        # Activation/désactivation des champs en fonction des cases à cocher
        task_dosync = self.settings.getboolean('task', 'dosync')
        self.enable_text_setting('task', 'uri', task_dosync)
        self.enable_choice_setting('task', 'preferredsyncmode', task_dosync)

        note_dosync = self.settings.getboolean('note', 'dosync')
        self.enable_text_setting('note', 'uri', note_dosync)
        self.enable_choice_setting('note', 'preferredsyncmode', note_dosync)

    def enable_text_setting(self, section, name, enabled):
        # Active/désactive le champ de texte
        for child in self.winfo_children():
            if isinstance(child, ttk.Entry) and child.winfo_name() == f"{section}_{name}":
                child.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def enable_choice_setting(self, section, name, enabled):
        # Active/désactive le combobox
        for child in self.winfo_children():
            if isinstance(child, ttk.Combobox) and child.winfo_name() == f"{section}_{name}":
                child.config(state='readonly' if enabled else tk.DISABLED)


class SyncMLPreferences(dialogtk.Dialog):  # Correction de l'héritage
    def __init__(self, parent, iocontroller=None, *args, **kwargs):  # Ajout de parent
        self.iocontroller = iocontroller
        super().__init__(parent, title=_("SyncML Preferences"), *args, **kwargs)  # Correction de l'appel à super()
        self.parent = parent
        self.geometry("700x500")
        if operating_system.isMac():
            pass  # self.CentreOnParent()  # À voir si nécessaire en Tkinter
        self.add_pages()

    def add_pages(self):
        kwargs = dict(parent=self, iocontroller=self.iocontroller)  # Correction du parent
        config = self.iocontroller.syncMLConfig()
        # pages = [(SyncMLAccessPage(parent=self, iocontroller=self.iocontroller,
        #                            settings=self.iocontroller), _('Access'), 'earth_blue_icon')]  # Correction du parent
        pages = [(SyncMLAccessPage(parent=self, iocontroller=self.iocontroller,
                                   settings=config), _('Access'), 'earth_blue_icon')]  # Correction du parent
        for page, title, bitmap in pages:
            # self.notebook.add(page, text=title)  # À adapter à votre système d'onglets
            # Créer un onglet (frame) pour chaque page
            tab = page
            self.add_tab(tab, title)  # Ajout de la page au dialogue

    def add_tab(self, page, title):
        # Ajoute une page (onglet) au dialogue
        page.pack(fill="both", expand=True, padx=10, pady=10)  # Afficher la page
        self.title(title)

    def Show(self, show=True):
        """

        Args:
            show (bool) : Indique si la boîte de dialogue doit être affichée.

        Returns:

        """
        if show:
            self.wait_window(self)  # Affiche le dialogue modal


# Mock classes for demonstration purposes
class MockSyncMLConfig:
    def __init__(self):
        self.access_syncUrl = "http://example.com/syncml"
        self.access_username = "testuser"
        self.task_dosync = True
        self.task_uri = "tasks"
        self.task_preferredsyncmode = "TWO_WAY"
        self.note_dosync = False
        self.note_uri = "notes"
        self.note_preferredsyncmode = "ONE_WAY_FROM_SERVER"

    def children(self):
        return []  # Simplified for the example

    def get(self, section, option, default=None):
        if section == 'general':
            if option == 'syncUrl':
                return self.general_syncurl
        # if section == 'access':
        elif section == 'access':
            if option == 'syncUrl':
                return self.access_syncUrl
            elif option == 'username':
                return self.access_username
            elif option == 'preset':
                return '0'  # Valeur par défaut
        elif section == 'task':
            if option == 'dosync':
                return self.task_dosync
            elif option == 'uri':
                return self.task_uri
            elif option == 'preferredsyncmode':
                return self.task_preferredsyncmode
        elif section == 'note':
            if option == 'dosync':
                return self.note_dosync
            elif option == 'uri':
                return self.note_uri
            elif option == 'preferredsyncmode':
                return self.note_preferredsyncmode
        # Si la valeur n'est pas trouvée, retourne la valeur par défaut passée en argument.
        if default is not None:
            return default

        # Si aucun défaut n'est spécifié (i.e., default=None) et que rien n'a été trouvé
        return ''

    def getboolean(self, section, option):
        value = self.get(section, option)
        if isinstance(value, bool):
            return value
        return value.lower() in ('true', '1', 'yes')


# Exemple d'utilisation (pour tester le dialogue)
if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    root.title(_("Task Coach - Main Window"))
    root.geometry("400x300")

    # Création d'une instance de iocontroller simulée
    class MockIOController:
        def syncMLConfig(self):
            return MockSyncMLConfig()

        def SyncMLConfig(self, config):
            print("SyncML config updated (mock)")

    mock_iocontroller = MockIOController()

    def show_syncml_preferences():
        # Affiche le dialogue modal des préférences SyncML
        dialog = SyncMLPreferences(root, iocontroller=mock_iocontroller)
        root.wait_window(dialog)

    ttk.Label(root, text=_("Cliquez sur le bouton pour ouvrir le dialogue des préférences SyncML.")).pack(pady=20)
    ttk.Button(root, text=_("Open SyncML Preferences"), command=show_syncml_preferences).pack(pady=10)

    root.mainloop()
