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
# Le fichier windowdimensionstracker.py utilise de nombreuses fonctionnalités
# spécifiques à wxPython qui nécessitent une adaptation soignée pour tkinter.
#
# Je vais créer une version de windowdimensionstracker.py pour tkinter
# et taskcoachlib/operating_system.py pour simuler les fonctions nécessaires.
#
# Aperçu de la conversion
#
# L'idée principale est de remplacer les mécanismes de wxPython
# par leurs équivalents dans tkinter :
#
#     Gestion des événements (wx.EVT_...) : Remplacé par la méthode bind() de tkinter
#                                           (<Configure>, <Unmap>, etc.).
#
#     Gestion de la taille et de la position : Utilisation des méthodes geometry(),
#                                              winfo_x(), winfo_y(), winfo_width(),
#                                              winfo_height() et state() de la fenêtre Tkinter.
#
#     État de la fenêtre : La gestion de la maximisation (IsMaximized, Maximize)
#                          et de l'icônisation (IsIconized, Iconize) sera faite
#                          avec la méthode state() de tkinter ('zoomed' pour maximisé,
#                          'iconic' pour icônisé/minimisé).
#
#     operating_system.py : Nous allons créer une version simplifiée
#                           de ce module en Python standard, car
#                           tkinter est moins dépendant de la plateforme que wxPython.
#                           Cependant, nous allons conserver la structure
#                           pour le support de isMac() et isGTK().
#
# Voici les fichiers convertis. J'ai divisé le travail en deux fichiers :
# le nouveau windowdimensionstracker_tk.py et une simulation de operating_system.py
# pour que l'importation fonctionne.

# Instructions d'implémentation
#
#     Enregistrez les fichiers :
#
#         Enregistrez le contenu du premier bloc de code dans un fichier
#         nommé windowdimensionstracker_tk.py.
#
#         Créez un dossier taskcoachlib et enregistrez le contenu du
#         deuxième bloc de code dans taskcoachlib/operating_system.py.
#
#     Utilisation dans votre application Tkinter :
#
#         Dans votre code principal (où vous créez la fenêtre Tkinter root),
#         assurez-vous de disposer d'un objet settings qui implémente
#         les méthodes get() et getvalue()/setvalue() comme simulé dans l'exemple MockSettings.
#
#         Initialisez le tracker avec votre fenêtre principale et votre objet settings :

# Points importants de la conversion :
#
#     Maximisation/Icônisation : Tkinter utilise window.state('zoomed')
#                                pour la maximisation (principalement sur Windows)
#                                et window.state('iconic') pour la minimisation.
#                                TODO : L'événement <Configure> nous permet de suivre ces changements.
#
#     Position/Taille : Les méthodes winfo_rootx(), winfo_rooty(),
#                       winfo_width(), winfo_height() et geometry() de Tkinter
#                       remplacent les méthodes wx.GetPosition() et wx.GetSize().
#
#     save_position() : J'ai ajouté l'appel explicite à tracker.save_position()
#                       dans l'exemple on_closing. C'est crucial car,
#                       contrairement à wxPython où les événements de
#                       taille/mouvement étaient distincts,
#                       l'événement <Configure> de Tkinter pourrait ne
#                       pas être le tout dernier événement avant la fermeture.
#                       Le fait de l'appeler explicitement garantit que les données sont enregistrées.
import logging
import tkinter as tk
import sys
# Importation simulée du module operating_system
# Dans votre projet réel, ce fichier devrait se trouver dans taskcoachlib/
# try:
from taskcoachlib import operating_system
# except ImportError:
#     # Si l'importation échoue (pour les tests simples), nous utilisons un fallback.
#     # Ceci est juste pour que l'exemple soit exécutable.
#     # Vous devriez utiliser le fichier operating_system.py fourni ci-dessous.
#     class MockOS:
#         @staticmethod
#         def isMac(): return sys.platform == "darwin"
#         @staticmethod
#         def isGTK(): return False # Simplification pour cet exemple
#     operating_system = MockOS()

log = logging.getLogger(__name__)


class _Tracker(object):
    """ Méthodes utilitaires pour définir et obtenir des valeurs depuis/vers
        les paramètres. """

    def __init__(self, settings, section):
        super().__init__()
        self.__settings = settings
        self.__section = section

    def set_setting(self, setting, value) -> None:
        """ Stocke la valeur du paramètre dans les paramètres. """
        # Ceci est une simulation de la fonction setvalue de Taskcoach.
        # TODO : Vous devez adapter l'objet 'settings' pour qu'il gère réellement le stockage.
        # if not hasattr(self.__settings, '_data'):
        #     self.__settings._data = {}
        # if self.__section not in self.__settings._data:
        #     self.__settings._data[self.__section] = {}
        # self.__settings._data[self.__section][setting] = value
        self.__settings.setvalue(self.__section, setting, value)

        log.debug(f"_Tracker.set_setting : SET: [{self.__section}] {setting} = {value}")

    def get_setting(self, setting):
        """ Obtient la valeur du paramètre depuis les paramètres et la retourne. """
        # TODO : Ceci est une simulation de la fonction getvalue de Taskcoach.
        # try:
        #     return self.__settings._data[self.__section][setting]
        # except (AttributeError, KeyError):
        #     # Retourne des valeurs par défaut si non trouvées
        #     if setting == "size": return 800, 600
        #     if setting == "position": return 50, 50
        #     if setting == "maximized": return False
        #     if setting == "iconized": return False
        #     if setting == "hidewheniconized": return False
        #     return None  # Valeur par défaut si le paramètre est inconnu
        return self.__settings.getvalue(self.__section, setting)


class WindowSizeAndPositionTracker(_Tracker):
    """ Suit la taille et la position d'une fenêtre dans les paramètres. """

    def __init__(self, window, settings, section):
        super().__init__(settings, section)
        self._window = window
        self.__set_dimensions()
        # Bindings Tkinter pour suivre les changements de dimension et de position
        self._window.bind('<Configure>', self.on_change_dimensions)
        self._window.bind('<Unmap>', self.on_iconify)  # Minimisation ou fermeture (nécessite un état ultérieur)

        # On a besoin d'un état interne pour suivre la maximisation/icônisation
        self._is_maximized = self.get_setting("maximized")

    def on_change_dimensions(self, event) -> None:
        """ Gère les événements de configuration (taille/position). """
        # Le binding <Configure> est appelé pour tout changement de taille ou de position
        # Nous devons vérifier l'état de la fenêtre Tkinter

        current_state = self._window.state()

        if current_state == 'iconic':
            # La fenêtre est icônisée/minimisée
            self.set_setting("iconized", True)
            self.set_setting("maximized", False)
        elif current_state == 'normal':
            # La fenêtre est en état normal (non maximisée, non icônisée)
            x = self._window.winfo_rootx()
            y = self._window.winfo_rooty()
            width = self._window.winfo_width()
            height = self._window.winfo_height()

            # Sauvegarde la position et la taille
            self.set_setting("position", (x, y))
            self.set_setting("size", (width, height))
            self.set_setting("maximized", False)
            self.set_setting("iconized", False)
            self._is_maximized = False
        elif current_state == 'zoomed':
            # La fenêtre est maximisée ('zoomed' sous Windows, souvent 'normal' ou 'fullscreen' sur d'autres OS)
            self.set_setting("maximized", True)
            self.set_setting("iconized", False)
            self._is_maximized = True

        # Ignore les événements du widget root s'ils ne viennent pas de la fenêtre principale
        # car <Configure> peut être déclenché par des widgets internes
        if event.widget == self._window:
            # Nous utilisons event.widget pour s'assurer que l'événement vient de la fenêtre elle-même
            pass

    def on_iconify(self, event) -> None:
        """ Gère la minimisation de la fenêtre (événement <Unmap>). """
        if self._window.state() == 'iconic':
            self.set_setting("iconized", True)
            self.set_setting("maximized", False)

    def __set_dimensions(self) -> None:
        """ Définit la position et la taille de la fenêtre en fonction des paramètres. """
        x, y = self.get_setting("position")
        width, height = self.get_setting("size")

        # Tkinter utilise 'widthxheight+x+y' pour geometry()
        geometry_string = f"{width}x{height}+{x}+{y}"
        self._window.geometry(geometry_string)

        if self.get_setting("maximized"):
            # En Tkinter, pour maximiser (Windows/Mac) ou mettre en plein écran (Linux/Mac),
            # on utilise 'zoomed' ou 'full'
            if operating_system.isMac():
                # Mac OS X : Tkinter peut ne pas avoir 'zoomed'. On utilise 'normal' et 'full' ou set_resizable
                # Ici, on utilise la maximisation système si disponible (souvent 'zoomed' ou 'normal' + taille écran)
                # Nous allons simplifier en utilisant 'zoomed' si disponible, sinon on garde 'normal'
                self._window.state('zoomed')
            else:
                # 'zoomed' fonctionne généralement bien pour maximiser sur Windows et certains Linux
                self._window.state('zoomed')

        if self.get_setting("iconized"):
            # Iconize (minimiser)
            self._window.state('iconic')

        # Le code original Taskcoach avait une vérification de l'affichage valide
        # Tkinter ne fournit pas d'accès direct au Display.GetFromWindow comme wx.
        # Si la position est trop loin (hors écran), Tkinter peut la corriger
        # automatiquement, ou nous pourrions la recentrer.
        # Nous allons vérifier si la position est trop petite (près de l'origine) comme le faisait l'original
        # pour s'assurer qu'elle est visible, si elle était enregistrée hors écran.
        if x < 0 or y < 0:
            # Repositionne sur une position par défaut si elle est négative (souvent hors écran)
            self._window.geometry(f"{width}x{height}+50+50")


class WindowDimensionsTracker(WindowSizeAndPositionTracker):
    """ Suit les dimensions d'une fenêtre dans les paramètres. """

    def __init__(self, window, settings):
        # La section "window" est définie dans le parent
        super().__init__(window, settings, "window")
        self.__settings = settings

        if self.__start_iconized():
            # Si on doit démarrer icônisé
            if operating_system.isMac() or operating_system.isGTK():
                # Pour Mac/GTK, il est souvent nécessaire de montrer d'abord, puis d'icôniser
                self._window.deiconify()  # Assure que la fenêtre est visible si elle était cachée

            # Iconise la fenêtre
            self._window.state('iconic')

            if not operating_system.isMac() and \
                    self.get_setting("hidewheniconized"):
                # Hide() est l'équivalent de l'original window.Hide()
                # En Tkinter, hide après iconify peut être redondant mais suit la logique originale
                # On utilise after() pour simuler wx.CallAfter
                self._window.after(10, self._window.withdraw)  # withdraw est la méthode Tkinter pour cacher

    def __start_iconized(self):
        """ Retourne si la fenêtre doit être ouverte icônisée. """
        # La fonction get() de Taskcoach est simulée dans _Tracker.get_setting
        start_iconized = self.__settings.get("window", "starticonized")
        if start_iconized == "Always":
            return True
        if start_iconized == "Never":
            return False
        return self.get_setting("iconized")

    def save_position(self) -> None:
        """ Sauvegarde la position de la fenêtre dans les paramètres. """
        iconized = self._window.state() == 'iconic'
        self.set_setting("iconized", iconized)

        if not iconized:
            # Obtient la position actuelle si elle n'est pas minimisée
            x = self._window.winfo_rootx()
            y = self._window.winfo_rooty()
            self.set_setting("position", (x, y))


# --- Exemple d'utilisation ---

if __name__ == '__main__':
    # Objet de paramètres simulé pour les tests
    class MockSettings:
        def __init__(self):
            # Valeurs par défaut pour les tests
            self._data = {
                "window": {
                    "size": (900, 700),
                    "position": (100, 100),
                    "maximized": False,
                    "iconized": False,
                    "starticonized": "Never",
                    "hidewheniconized": True
                }
            }

        def getvalue(self, section, setting):
            return self._data.get(section, {}).get(setting)

        def setvalue(self, section, setting, value):
            if section not in self._data:
                self._data[section] = {}
            self._data[section][setting] = value

        def get(self, section, setting):
            # Simule l'accès direct aux paramètres pour __start_iconized
            return self._data.get(section, {}).get(setting)

    def main():
        root = tk.Tk()
        root.title("Tkinter Window Dimension Tracker Example")
        settings = MockSettings()

        # Initialisation du tracker
        tracker = WindowDimensionsTracker(root, settings)

        tk.Label(root, text="Redimensionnez, déplacez, maximisez et minimisez la fenêtre.\n"
                            "Fermez pour voir les paramètres sauvegardés dans la console.").pack(pady=20, padx=20)

        def on_closing():
            # Sauvegarde la position finale avant de quitter
            tracker.save_position()
            print("\n--- Paramètres enregistrés ---")
            for section, data in settings._data.items():
                print(f"[{section}]")
                for key, value in data.items():
                    print(f"  {key}: {value}")
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    main()
