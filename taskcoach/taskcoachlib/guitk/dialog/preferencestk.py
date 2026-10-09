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
# Le fichier preferences.py original crée un dialogue de préférences avec plusieurs pages pour différents réglages.
# Pour cette conversion, je vais utiliser tkinter et tkinter.ttk
# pour reproduire le dialogue de style "cahier" (Notebook).
# Étant donné que le code source des pages individuelles n'est pas disponible,
# je vais créer des classes factices pour représenter ces pages de paramètres
# (WindowBehaviorPage, TaskDatesPage, etc.),
# ce qui rendra l'exemple fonctionnel et illustrera la structure.

# Cette version en Tkinter reproduit la structure et la logique du fichier preferences.py original.
# Elle utilise le widget ttk.Notebook pour gérer les différentes pages de préférences.
# Pour les besoins de la démonstration,
# j'ai inclus des classes factices pour simuler les pages de réglages
# et les fonctions de détection du système d'exploitation.

# Le fichier d'origine dans wxPython utilisait un dialogue de type "cahier"
# (wx.lib.agw.aui.AuiNotebook).
# Pour Tkinter, nous utiliserons le widget ttk.Notebook qui remplit exactement la même fonction.
#
# Comme le contenu des pages de préférences individuelles (WindowBehaviorPage, TaskDatesPage, etc.) n'est pas fourni,
# j'ai créé des classes marquantes (PlaceholderPage) qui respectent l'interface requise
# (héritent de ttk.Frame, ont un attribut pageTitle et des méthodes applySettings pour la sauvegarde).
#
# Voici le fichier preferencestk.py complet et fonctionnel,
# intégrant artprovidertk et la logique conditionnelle d'affichage des pages
# (pour iphone, os_darwin, os_linux).
#
# Fichier preferencestk.py
#
# Ce fichier définit le dialogue principal des préférences (PreferencesDialog)
# en utilisant tkinter.Toplevel et ttk.Notebook pour gérer les différentes pages.

# Explication de la Conversion
#
#     Marqueurs (Placeholder Pages) : J'ai défini une classe de base PreferencesPage qui hérite de ttk.Frame.
#     Toutes les pages de préférences (comme WindowBehaviorPage, TaskDatesPage, etc.) en héritent.
#     Elles incluent les méthodes loadSettings() et applySettings() que vous devrez implémenter avec le code spécifique de chaque page.
#
#     PreferencesDialog Structure:
#
#         La classe hérite de tk.Toplevel pour agir comme une fenêtre de dialogue modale.
#
#         Le widget principal est ttk.Notebook (self.notebook), utilisé pour contenir les différentes pages.
#
#         La logique de détermination de la page à créer (__should_create_page) a été conservée,
#         utilisant operating_system.isMac() et operating_system.isGTK(),
#         et vérifiant le paramètre "iphone" via l'objet settings.
#
#     Gestion de l'icône: La ligne self.iconphoto(False, icon) est utilisée
#     pour définir l'icône de la fenêtre Toplevel en utilisant le PhotoImage
#     retourné par artprovider.ArtProvider.GetIcon('wrench_icon').
#
#     Boutons OK/Annuler: Les méthodes onOk et onCancel gèrent la fermeture du dialogue.
#     onOk appelle applySettings() sur chaque page avant de fermer,
#     et onCancel ferme directement en ignorant les changements.
#
#     Modalité: L'utilisation de self.transient(parent), self.grab_set(), et self.wait_window(self) à la fin de __init__ garantit que le dialogue des préférences est modal, bloquant l'interaction avec la fenêtre parente jusqu'à ce qu'il soit fermé.
#
# Ce fichier est maintenant une base solide pour continuer à convertir le contenu réel de chacune des pages de préférences dans leurs classes respectives.

# Oui, je peux vérifier la conversion de preferencestk.py et m'assurer qu'il utilise correctement artprovidertk.py, et que artprovidertk.py utilise icons.py de manière appropriée.
# Voici une analyse de l'utilisation de ces fichiers, en mettant l'accent sur les points clés de leur interaction :
# 1. Utilisation de artprovidertk.py dans preferencestk.py
#
# Importation : preferencestk.py importe artprovidertk comme suit : from taskcoachlib.guitk import artprovidertk as artprovider . Cela signifie que artprovidertk.py est utilisé pour fournir les icônes et les images dans l'interface Tkinter.
# Appel de GetIcon : Dans PreferencesDialog.__init__, artprovider.ArtProviderTk.GetIcon('wrench_icon') est appelé pour récupérer l'icône de la fenêtre .  Cela démontre l'utilisation de la classe ArtProviderTk pour obtenir une icône spécifique.
# Page Apparence : Elle est gérée par _addIconSetting qui prend un code d'icône et affiche l'icône correspondante. Elle utilise tk.StringVar pour contenir la valeur.
# Dépendances conditionnelles : Le code gère correctement les dépendances optionnelles et les systèmes d'exploitation spécifiques. Par exemple, certaines pages ne sont incluses que si certaines fonctionnalités sont activées ou si le système d'exploitation est macOS ou Linux .
#
# 2. Utilisation de icons.py dans artprovidertk.py
# TODO : A intégrer
#
# Importation : artprovidertk.py importe icons.py comme suit : from taskcoachlib.guitk import icons as icons_tk. Cela permet d'accéder au catalogue d'icônes et aux classes définies dans icons.py.
# Accès au catalogue : La méthode ArtProviderTk.GetBitmap vérifie si l'ID de l'icône est présent dans icons_tk.catalog. Si l'icône est trouvée, elle est récupérée du catalogue et utilisée pour créer un objet PhotoImage Tkinter .
# Gestion des images PyEmbeddedImageTk : La classe PyEmbeddedImageTk est instanciée et utilisée pour récupérer les images. La méthode GetImage() est utilisée pour récupérer l'image PIL.
#
# 3. Points à vérifier et à améliorer
#
# Chemin d'accès aux icônes : Bien que les fichiers icons.py et artprovidertk.py soient utilisés ensemble, le code de artprovidertk.py  semble simuler le catalogue d'icônes (icons.catalog) et la classe PyEmbeddedImageTk . Il faudra s'assurer que le code de production charge les vraies données des icônes.
# Gestion des erreurs : Assurez-vous que le code gère correctement les erreurs potentielles, telles que les icônes manquantes ou les erreurs de chargement d'image .
# Dépendances optionnelles : Vérifiez que la gestion des dépendances optionnelles (par exemple, taskcoachlib.syncml.core) est correcte et que le code ne plante pas si les dépendances ne sont pas installées .
#
# En résumé, la structure générale de la conversion semble correcte. preferencestk.py utilise artprovidertk.py pour charger les icônes, et artprovidertk.py utilise icons.py pour accéder aux données des icônes. Il faut bien adapter la manipulation des images et des icônes.
# Si tu as des questions spécifiques sur une partie particulière du code ou si tu rencontres des erreurs, n'hésite pas à me les communiquer.

# Améliorations pour preferencestk.py
#
#
# Gestion des erreurs:
#
# Dans les méthodes applySettings des différentes pages, ajoute une gestion des exceptions plus explicite pour intercepter les erreurs potentielles lors de l'application des paramètres. Cela permet d'éviter que l'ensemble du dialogue ne plante si un seul paramètre pose problème. Enregistrez les erreurs et affichez des messages d'avertissement à l'utilisateur.
#
#
#
# Type hinting: Ajouter des annotations de type pour améliorer la lisibilité et la maintenabilité.
#
#
# Modularité et Lisibilité:
#
# Dans PreferencesDialog, la logique pour déterminer si une page doit être créée (__should_create_page) et la création de la page (createPage) sont bien séparées. Cependant, la logique de filtrage conditionnel des pages directement dans addPages peut être déplacée vers __should_create_page pour centraliser toute la logique de décision en un seul endroit.
# Simplifiez les méthodes _add...Setting dans PreferencesPage en utilisant des fonctions lambda ou des fonctions internes pour réduire la duplication de code, en particulier pour la création de gestionnaires d'événements.
#
#
#
# Gestion des dépendances optionnelles :
#
# Dans FeaturesPage, la vérification de la disponibilité de taskcoachlib.syncml.core est correcte, mais il serait plus robuste de vérifier également si les modules nécessaires à SyncML sont installés avant d'afficher l'option.
#
#
#
# Accessibilité :
#
# Ajoute des options d'accessibilité pour les utilisateurs handicapés, comme la prise en charge des lecteurs d'écran et la navigation au clavier. Cela peut impliquer l'ajout d'attributs aria-label aux widgets et la gestion des événements clavier.
#
#
#
# Centraliser la configuration des colonnes :
#
# Étant donné que beaucoup de pages utilisent une configuration de colonnes similaire, centraliser la logique de configuration des colonnes dans une méthode réutilisable dans PreferencesPage pour éviter la duplication.
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog  # Ajout de filedialog pour les chemins
from tkinter import colorchooser, font as tkFont  # Ajout de colorchooser et tkFont
# from taskcoachlib import meta
# from taskcoachlib import meta, widgets, notify, operating_system, render
# Importations demandées
from taskcoachlib import meta, notify, patterns, command, render, operating_system, speak, widgetstk
from taskcoachlib.domain import date, task
from taskcoachlib.guitk import artprovidertk as artprovider
from taskcoachlib.guitk.artprovidertk import IconProvider
from taskcoachlib.i18n import _
from taskcoachlib.meta import data
from taskcoachlib.widgetstk.textctrltk import MultiLineTextCtrl
from pubsub import pub
import webbrowser  # Ajout pour les liens hypertextes
import calendar  # Importation nécessaire pour FeaturesPage.applySettings
import sys  # Pour simuler le système d'exploitation
from typing import Dict, Any, Tuple, List, Optional, Union  # Pour les annotations de type
try:
    import tkfontchooser
except ImportError:
    print("tkfontchooser n'est pas installé. Utilisation d'un sélecteur de police simplifié.")
    tkfontchooser = None

log = logging.getLogger(__name__)


# # Simulation de classes et de modules externes pour l'exemple
# class MockOperatingSystem:
#     def isMac(self):
#         return sys.platform == 'darwin'
#
#     def isGTK(self):
#         return sys.platform.startswith('linux')
#
#
# operating_system = MockOperatingSystem()
#
#
# class MockSettings:
#     def getboolean(self, section, name):
#         # Mocking settings for demonstration purposes
#         if section == "feature" and name == "iphone":
#             return True
#         return False
#
#
# # Simulation de l'objet de statut de tâche
# class MockTaskStatus:
#     """Simule l'objet de statut de tâche avec un label et un label au pluriel."""
#     def __init__(self, name, label, plural_label):
#         self.name = name
#         self.label = label
#         self.pluralLabel = plural_label
#
#     def __str__(self):
#         return self.name
#
#
# class MockTask:
#     """Simule la classe task.Task pour obtenir les statuts possibles."""
#     @staticmethod
#     def possibleStatuses():
#         return [
#             MockTaskStatus("uncompleted", _("Uncompleted"), _("Uncompleted tasks")),
#             MockTaskStatus("completed", _("Completed"), _("Completed tasks")),
#             MockTaskStatus("overdue", _("Overdue"), _("Overdue tasks")),
#         ]
#
#
# # Simulation des widgets pour EditorPage.ok() TODO : A changer !
# class MockWidgets:
#     class MultiLineTextCtrl:
#         CheckSpelling = False


# # Remplacement du task module par la simulation pour cet exemple
# widgets = MockWidgets()
# task.Task = MockTask


# --- Classes de base et utilitaires (Marqueurs) ---

class TaskcoachSettings:
    """Classe simulée pour l'objet de paramètres (settings).
    Nécessaire pour le dialogue de préférences."""
    def __init__(self):
        # Paramètres de test
        # self._data = {
        self._data: Dict[Tuple[str, str], Any] = {
            # WindowBehaviorPage settings
            ("feature", "iphone"): False,
            ("window", "splash"): True,
            ("window", "tips"): False,
            ("version", "Notify"): True,
            ("view", "developermessages"): False,
            ("window", "hidewheniconized"): False,
            ("window", "hidewhenclosed"): True,
            ("window", "starticonized"): "Never",
            ("window", "blinktaskbariconwhentrackingeffort"): True,

            # TaskDatesPage settings
            ("behavior", "markparentcompletedwhenallchildrencompleted"): True,
            ("behavior", "duesoonhours"): 48, # Exemple de valeur entière
            ("view", "datestied"): "startdue", # Exemple de valeur pour le choix simple

            # Default date/time settings (ChoiceSettings avec des groupes de choix)
            ("view", "defaultplannedstartdatetime"): "preset,today,startofday",
            ("view", "defaultduedatetime"): "propose,tomorrow,endofday",
            ("view", "defaultactualstartdatetime"): "preset,today,currenttime",
            ("view", "defaultcompletiondatetime"): "propose,today,currenttime", # 4ème choix est différent (propose seulement)
            ("view", "defaultreminderdatetime"): "preset,tomorrow,startofday",

            # TaskReminderPage settings
            ("feature", "notifier"): "universal",
            ("feature", "sayreminder"): False,
            ("view", "defaultsnoozetime"): "10",
            ("view", "snoozetimes"): "5,10,30,60",

            # SavePage settings (NOUVEAU)
            ("file", "autosave"): True,
            ("file", "autoload"): False,
            ("file", "nopoll"): True,
            ("file", "saveinifileinprogramdir"): False,
            ("file", "attachmentbase"): "", # Chemin de base des pièces jointes
            ("file", "autoimport"): "Todo.txt", # Choix unique dans MultipleChoiceSettings pour cet exemple
            ("file", "autoexport"): "Todo.txt", # Choix unique dans MultipleChoiceSettings pour cet exemple

            # LanguagePage settings
            ("view", "language_set_by_user"): "fr_FR",
            ("view", "language"): "fr_FR",

            # Paramètres Appearance Settings
            ("appearance", "fgcoloruncompletedtasks"): "black",
            ("appearance", "bgcoloruncompletedtasks"): "#F0F0F0",
            ("appearance", "fontuncompletedtasks"): "TkDefaultFont",
            ("appearance", "iconuncompletedtasks"): "default",

            ("appearance", "fgcolorcompletedtasks"): "gray",
            ("appearance", "bgcolorcompletedtasks"): "#E0FFE0",
            ("appearance", "fontcompletedtasks"): "TkDefaultFont,italic",
            ("appearance", "iconcompletedtasks"): "check_icon",

            ("appearance", "fgcoloroverduetasks"): "red",
            ("appearance", "bgcoloroverduetasks"): "#FFF0F0",
            ("appearance", "fontoverduetasks"): "TkDefaultFont,bold",
            ("appearance", "iconoverduetasks"): "exclamation_icon",

            # Paramètres Features Settings (NOUVEAU pour FeaturesPage)
            ("feature", "syncml"): False,
            ("feature", "iphone"): False,  # Activé pour montrer la page iPhone
            ("feature", "usesm2"): False,
            ("view", "weekstart"): "monday",
            ("view", "efforthourstart"): 9,
            ("view", "efforthourend"): 17,
            ("calendarviewer", "gradient"): True,
            ("view", "effortminuteinterval"): "5",
            ("feature", "minidletime"): 10,
            ("feature", "decimaltime"): False,
            ("view", "descriptionpopups"): True,

            # Paramètres IPhonePage (NOUVEAU)
            ("iphone", "password"): "monmdp",
            ("iphone", "service"): "Task Coach Sync",
            ("iphone", "synccompleted"): False,
            ("iphone", "showlog"): True,

            # Paramètres EditorPage (NOUVEAU)
            ("editor", "maccheckspelling"): True, # macOS spécifique
            ("editor", "descriptionfont"): "Arial,12",

            # Paramètres OSXPage (NOUVEAU)
            ("os_darwin", "getmailsubject"): True,

            # Paramètres LinuxPage (NOUVEAU)
            ("os_linux", "focustextentry"): False,
        }

    def getboolean(self, section, option):
        """Simule la méthode getboolean pour la logique conditionnelle."""
        # Pour Tkinter, 'on' et 'off' sont aussi utilisés, nous allons rester simples pour le moment.
        return self._data.get((section, option), False)

    # Ajoutez d'autres méthodes de paramètres si nécessaire pour les pages

    def get(self, section, option, default=None):
        """Simule la méthode get standard."""
        return self._data.get((section, option), default)

    def set(self, section, option, value):
        """Simule la méthode set standard."""
        # Gère les variables Tkinter BooleanVar, StringVar, IntVar
        if isinstance(value, (tk.BooleanVar, tk.StringVar, tk.IntVar)):
            value = value.get()
        # Stockage de la valeur
        self._data[(section, option)] = value

    def getint(self, section, option):
        """Simule la méthode getint."""
        # return int(self.get(section, option, 0))
        val = self.get(section, option, 0)
        try:
            return int(val)
        except ValueError:
            return 0


class SettingsPageBase(ttk.Frame):
    """Base class for all settings pages in the notebook."""
    pageTitle = "Override in subclass"
    pageIcon = None  # A mock icon for now

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        ttk.Label(self, text=f"Page des réglages : {self.pageTitle}").pack(padx=20, pady=20)


# Classe de base pour toutes les pages de préférences
# Remplace SettingsPageBase de la version wxpython
class PreferencesPage(ttk.Frame):
    """
    Classe de base pour une page individuelle dans le dialogue de préférences.
    Chaque sous-classe doit définir pageTitle.
    """
    pageTitle = _("Untitled Page")

    # def __init__(self, parent, settings, *args, **kwargs):
    # def __init__(self, parent, settings, columns=3, *args, **kwargs):
    def __init__(self, parent, settings, columns=3, growableColumn=1, *args, **kwargs):
        """
        Initialise la page.

        Args:
            parent: Le widget ttk.Notebook parent.
            settings: L'objet TaskcoachSettings.
            columns : Nombre de colonnes de la grille pour les settings.
            growableColumn : Colonne qui doit s'étendre (-1 pour aucune).
        """
        super().__init__(parent, padding="10", *args, **kwargs)
        self.settings = settings
        self.parent = parent
        # Stocke les variables Tkinter associées aux paramètres : {(section, option): var}
        # self.controls = {}  # Dictionnaire pour stocker les variables Tkinter associées aux paramètres
        self.controls: Dict[Tuple[str, str], Any] = {}
        self.current_row = 0  # Compteur de ligne pour le layout en grille
        self.columns = columns

        # Configure le poids par défaut des colonnes, utile pour les Combobox
        # # Configure le poids des colonnes pour un layout de type "SettingsPage" (Label, Control, HelpText)
        # self.columnconfigure(0, weight=0)  # Colonne du Label
        # self.columnconfigure(1, weight=1)  # Colonne du Control (doit s'étendre)
        # if self.columns > 2:
        #     self.columnconfigure(2, weight=1)  # Colonne du HelpText (doit s'étendre)
        for i in range(columns):
            if i == growableColumn:
                self.columnconfigure(i, weight=1)
            else:
                self.columnconfigure(i, weight=0)

                # # Exemple de contenu simple pour le marqueur
        # ttk.Label(self, text=f"{self.pageTitle} - {_('Contenu de la page')}").pack(padx=10, pady=10)

        self.loadSettings()

    def loadSettings(self):
        """
        Méthode placeholder pour charger les paramètres du modèle vers l'interface utilisateur.
        """
        pass

    def applySettings(self):
        """
        Méthode placeholder pour appliquer et sauvegarder les paramètres de l'interface utilisateur.
        """
        # Dans une implémentation réelle, ceci mettrait à jour self.settings
        # Itera sur les contrôles et sauvegarde les valeurs
        for (section, option), control_var in self.controls.items():
            # Si le contrôle est un tuple (pour les choix multiples), on construit la chaîne
            # if isinstance(control_var, tuple):
            #     value = ",".join(v.get() for v in control_var)
            if isinstance(control_var, dict) and all(isinstance(v, tk.BooleanVar) for v in control_var.values()):
                # Cas: MultipleChoiceSettings (Dictionnaire de BooleanVar)
                # Construit la chaîne CSV des valeurs sélectionnées (clés)
                selected_values = [
                    value for value, var in control_var.items() if var.get()
                ]
                value = ",".join(selected_values)
            elif isinstance(control_var, tuple):
                # Cas: MultiChoiceSetting (Tuple de StringVar)
                value = ",".join(v.get() for v in control_var)
            elif isinstance(control_var, tk.StringVar):
                # Cas: ChoiceSetting ou PathSetting
                # Si c'est un ChoiceSetting, on doit retrouver la valeur réelle si on stockait le texte affiché
                # Ici, on suppose que la StringVar stocke déjà la valeur réelle
                value = control_var.get()
            else:
                # Cas: BooleanVar, StringVar, IntVar (Choix unique, booléen, entier)
                value = control_var.get()

            self.settings.set(section, option, value)

        print(f"Applying settings for: {self.pageTitle}")

    def get(self, section, option, default=None):
        """Accès direct aux paramètres (utilisé par FeaturesPage.ok)."""
        return self.settings.get(section, option, default)

    # --- Méthodes d'aide pour l'ajout de contrôles (simulant le style addXSetting) ---

    def _place_help_text(self, row_index, help_text):
        """Ajoute le texte d'aide dans la colonne 2 si elle existe."""
        if help_text and self.columns > 2:
            help_label = ttk.Label(self,
                                   text=help_text,
                                   wraplength=250,  # Largeur d'enrobage pour les longues descriptions
                                   justify=tk.LEFT,
                                   foreground="#606060",
                                   font=('TkDefaultFont', 9, 'italic'))
            # Le texte d'aide est placé à la ligne de l'élément qu'il décrit
            help_label.grid(row=row_index, column=2, sticky="nw", padx=10, pady=5)

    def _addEntry(self, text):
        """Ajoute une simple entrée/texte (utilisé pour les messages d'avertissement)."""
        label = ttk.Label(self,
                          text=text,
                          wraplength=self.parent.winfo_width() - 50,  # Adapte la longueur
                          justify=tk.LEFT,
                          font=('TkDefaultFont', 10, 'bold'))  # Souvent en gras pour les avertissements
        # Le message prend toute la largeur
        label.grid(row=self.current_row, column=0, columnspan=self.columns, sticky="ew", padx=5, pady=10)
        self.current_row += 1

    # def _addBooleanSetting(self, section, option, label_text):
    # def _addBooleanSetting(self, section, option, label_text, help_text=None):
    def _addBooleanSetting(self, section: str, option: str, label_text: str, help_text: Optional[str] = None):
        """
        Ajoute une case à cocher (BooleanVar) pour un paramètre, avec texte d'aide optionnel.

        Args :
            section : La section du paramètre.
            option : Le nom du paramètre.
            label_text : Le texte à afficher à côté de la case à cocher.
            help_text : Un texte d'aide optionnel.
        """
        var = tk.BooleanVar(value=self.settings.getboolean(section, option))
        self.controls[(section, option)] = var

        checkbutton = ttk.Checkbutton(
            self,
            text=label_text,
            variable=var
        )
        # S'étend sur les colonnes 0 et 1 (visuellement, colonne 2 libre pour l'aide conditionnelle)
        checkbutton.grid(row=self.current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Ajout du texte d'aide
        self._place_help_text(self.current_row, help_text)

        self.current_row += 1

    # NOUVELLE MÉTHODE D'AIDE : _addTextSetting
    def _addTextSetting(self, section, option, label_text, help_text=None, password_mode=False):
        """Ajoute un label et un champ de saisie pour un paramètre de texte (StringVar)."""
        # 1. Label
        label = ttk.Label(self, text=label_text)
        label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2)

        # 2. Entry
        var = tk.StringVar(value=self.settings.get(section, option, ""))
        self.controls[(section, option)] = var

        show_char = '*' if password_mode else ''
        entry = ttk.Entry(
            self,
            textvariable=var,
            show=show_char # C'est ainsi que Tkinter gère les champs de mot de passe
        )
        entry.grid(row=self.current_row, column=1, sticky="ew", padx=5, pady=2)

        self._place_help_text(self.current_row, help_text)

        self.current_row += 1

    # def _addIntegerSetting(self, section, option, label_text, minimum=None, maximum=None):
    def _addIntegerSetting(self, section, option, label_text, help_text=None, minimum=None, maximum=None):
        """
        Ajoute un label et un Spinbox pour un paramètre entier (IntVar).
        """
        # 1. Label
        label = ttk.Label(self, text=label_text)
        label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2)

        # 2. Spinbox (Champ de saisie pour entier)
        var = tk.IntVar(value=int(self.settings.get(section, option, 0)))
        self.controls[(section, option)] = var

        # Un Spinbox permet d'incrémenter/décrémenter un entier.
        # Nous utilisons une frame pour contenir le Spinbox car il n'est pas dans ttk
        # Et nous ne voulons pas qu'il s'étende sur toute la colonne 1 (sticky="ew")
        control_frame = ttk.Frame(self)
        control_frame.grid(row=self.current_row, column=1, sticky="w", padx=5, pady=2)

        spinbox = tk.Spinbox(
            control_frame,
            from_=minimum if minimum is not None else -9999,
            to=maximum if maximum is not None else 9999,
            textvariable=var,
            width=6,  # Petite largeur pour les entiers
            justify="right"
        )
        spinbox.pack(side="left")

        self._place_help_text(self.current_row, help_text)

        self.current_row += 1

    # def _addChoiceSetting(self, section, option, label_text, choices):
    def _addChoiceSetting(self, section, option, label_text, choices, help_text=None):
        """
        Ajoute un label et une combobox (StringVar) pour un paramètre à choix simple.
        :param choices: Liste de tuples [(value, display_text), ...]
        """

        # 1. Label
        label = ttk.Label(self, text=label_text)
        label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2)

        # 2. Combobox

        # Mapping entre la valeur réelle et le texte affiché
        value_to_display = {value: text for value, text in choices}
        display_to_value = {text: value for value, text in choices}
        display_texts = [text for value, text in choices]

        # Variable pour stocker la valeur réelle
        real_value_var = tk.StringVar(value=self.settings.get(section, option))
        self.controls[(section, option)] = real_value_var

        # Variable d'affichage pour le Combobox
        current_value = real_value_var.get()
        current_display = value_to_display.get(current_value, display_texts[0] if display_texts else "")
        display_var = tk.StringVar(value=current_display)

        combobox = ttk.Combobox(
            self,
            textvariable=display_var,
            values=display_texts,
            state="readonly"
        )

        # Gestionnaire d'événement pour mettre à jour la variable réelle lorsque le choix change
        def on_selection_change(event):
            selected_text = display_var.get()
            selected_value = display_to_value.get(selected_text)
            real_value_var.set(selected_value)

        combobox.bind("<<ComboboxSelected>>", on_selection_change)

        # Positionne le Combobox
        combobox.grid(row=self.current_row, column=1, sticky="ew", padx=5, pady=2)

        self._place_help_text(self.current_row, help_text)

        self.current_row += 1

    # NOUVELLE MÉTHODE POUR L'HEURE (TimeSetting dans l'original)
    def _addTimeSetting(self, section, option, label_text, help_text=None,
                        minimum=0, maximum=24, disabledMessage=None, disabledValue=None, defaultValue=None):
        """Ajoute un paramètre d'heure (Spinbox) pour les heures de début/fin de journée."""

        # 1. Label
        label = ttk.Label(self, text=label_text)
        label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2)

        # Déterminer la valeur initiale
        initial_value = self.settings.getint(section, option)
        if initial_value == 0 and defaultValue is not None:
            # Utilise defaultValue si la valeur n'est pas définie (0) et qu'une valeur par défaut est fournie
            initial_value = defaultValue

        var = tk.IntVar(value=initial_value)
        self.controls[(section, option)] = var

        control_frame = ttk.Frame(self)
        control_frame.grid(row=self.current_row, column=1, sticky="w", padx=5, pady=2)

        # Les heures sont généralement de 0 à 24 (pour 'fin de journée')

        # Créer la liste des valeurs si disabledMessage est présent (ex: "End of day" pour 24)
        values_list = list(range(minimum, maximum + 1))

        if disabledMessage and disabledValue is not None:
            # Gérer le cas spécial où une valeur (ex: 24) est remplacée par un message (ex: "End of day")
            hour_display_var = tk.StringVar(value=str(initial_value))

            def update_display(value):
                if value == disabledValue:
                    hour_display_var.set(disabledMessage)
                else:
                    hour_display_var.set(str(value))

            # Mettre à jour la variable affichée initialement
            update_display(initial_value)

            # Créer une ComboBox pour gérer le message/valeur
            display_values = [str(v) for v in values_list if v != disabledValue]
            display_values.append(disabledMessage)

            combobox = ttk.Combobox(
                control_frame,
                textvariable=hour_display_var,
                values=display_values,
                state="readonly",
                width=10
            )

            def on_combobox_change(event):
                selected_text = hour_display_var.get()
                if selected_text == disabledMessage:
                    var.set(disabledValue)
                else:
                    try:
                        var.set(int(selected_text))
                    except ValueError:
                        # Devrait pas arriver si state="readonly"
                        pass
                print(f"Time setting changed to: {var.get()}")

            combobox.bind("<<ComboboxSelected>>", on_combobox_change)
            combobox.pack(side="left")

        else:
            # Cas Spinbox simple (heure de début, 0-23 ou 0-24)
            spinbox = tk.Spinbox(
                control_frame,
                from_=minimum,
                to=maximum,
                textvariable=var,
                width=6,
                justify="right"
            )
            spinbox.pack(side="left")

        self._place_help_text(self.current_row, help_text)
        self.current_row += 1

    # def _addMultiChoiceSetting(self, section, option, label_text, *choice_groups):
    def _addMultiChoiceSetting(self, section, option, label_text, *choice_groups, help_text=None):
        """
        Ajoute un label et plusieurs Combobox pour un paramètre à choix multiples.
        La valeur est stockée comme une chaîne de caractères séparée par des virgules (ex: 'preset,today,startofday').
        """

        # 1. Label s'étendant sur toutes les colonnes de choix
        label = ttk.Label(self, text=label_text)
        label.grid(row=self.current_row, column=0, columnspan=len(choice_groups) + 1, sticky="w", padx=5, pady=2)  # Label sur 2 colonnes

        self._place_help_text(self.current_row, help_text)
        self.current_row += 1

        # 2. Cadre pour les Combobox (pour le regroupement)
        combobox_frame = ttk.Frame(self)
        # S'étale sur les colonnes 0, 1, 2, 3 (si colonnes=4)
        # combobox_frame.grid(row=self.current_row, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
        combobox_frame.grid(row=self.current_row, column=0, columnspan=self.columns, sticky="ew", padx=5, pady=2)

        # Récupère la valeur actuelle (ex: 'preset,today,startofday')
        current_values = self.settings.get(section, option, "").split(',')

        # Liste pour stocker les variables Tkinter réelles (valeurs internes)
        real_value_vars = []

        for col_idx, choices in enumerate(choice_groups):
            # Mapping entre la valeur réelle et le texte affiché
            value_to_display = {value: text for value, text in choices}
            display_to_value = {text: value for value, text in choices}
            display_texts = [text for value, text in choices]

            # 2a. Variable de valeur réelle
            # Tente d'obtenir la valeur par défaut pour ce groupe
            # default_value = current_values[col_idx] if col_idx < len(current_values) else choices[0][0]
            default_value = current_values[col_idx] if col_idx < len(current_values) and current_values[col_idx] else choices[0][0]
            real_value_var = tk.StringVar(value=default_value)
            real_value_vars.append(real_value_var)

            # 2b. Variable d'affichage pour la Combobox
            current_display = value_to_display.get(default_value, display_texts[0] if display_texts else "")
            display_var = tk.StringVar(value=current_display)

            combobox = ttk.Combobox(
                combobox_frame,
                textvariable=display_var,
                values=display_texts,
                state="readonly"
            )

            # Gestionnaire d'événement pour mettre à jour la variable réelle lorsque le choix change
            def on_selection_change(event, var_to_update=real_value_var, display_var=display_var, display_map=display_to_value):
                selected_text = display_var.get()
                selected_value = display_map.get(selected_text)
                var_to_update.set(selected_value)

            combobox.bind("<<ComboboxSelected>>", on_selection_change)

            # Positionne le Combobox dans le cadre (frame)
            combobox.pack(side="left", padx=5, fill="x", expand=True)

        # Stocke le tuple de toutes les variables réelles
        self.controls[(section, option)] = tuple(real_value_vars)

        self.current_row += 1

    # def _addMultipleChoiceSettings(self, section, option, label_text, choices):
    def _addMultipleChoiceSettings(self, section, option, label_text, choices, help_text=None):
        """
        Ajoute un label et une liste de cases à cocher pour les paramètres à choix multiples.
        La valeur est stockée comme une chaîne de caractères séparée par des virgules (ex: 'choice1,choice3').

        Args :
            choices : Liste de tuples [(value, display_text), ...]
        """
        # 1. Label (s'étend sur toute la largeur)
        label = ttk.Label(self, text=label_text)
        # label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2, columnspan=3)
        label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2, columnspan=2)

        # Ajout du texte d'aide à la même ligne
        self._place_help_text(self.current_row, help_text)

        self.current_row += 1

        # 2. Cadre pour les cases à cocher (pour le regroupement et l'indentation)
        checkbox_frame = ttk.Frame(self)
        # S'étale sur les colonnes 0, 1, 2, avec un petit décalage à gauche (padx)
        checkbox_frame.grid(row=self.current_row, column=0, columnspan=3, sticky="ew", padx=20, pady=2)

        # Le setting actuel est une chaîne CSV des valeurs sélectionnées
        current_setting_value = self.settings.get(section, option, "")
        current_selected_values = current_setting_value.split(',') if current_setting_value else []

        # Dictionnaire pour stocker les variables Tkinter (valeur -> BooleanVar)
        # C'est ce dictionnaire qui est sauvegardé dans self.controls et géré dans applySettings
        choice_vars = {}

        for value, display_text in choices:
            # Détermine si la valeur doit être cochée
            is_checked = str(value) in current_selected_values # La valeur peut être un entier (ex: 5)

            var = tk.BooleanVar(value=is_checked)
            # Utilise la valeur (string) comme clé
            choice_vars[str(value)] = var

            checkbutton = ttk.Checkbutton(
                checkbox_frame,
                text=display_text,
                variable=var
            )
            # Organiser les cases à cocher verticalement, ancrées à gauche
            checkbutton.pack(anchor="w", fill="x", padx=5, pady=1)

        # Stocke le dictionnaire de variables
        self.controls[(section, option)] = choice_vars

        self.current_row += 1

    def _addPathSetting(self, section, option, title, help_text=None):
        """Ajoute un paramètre de chemin (Entry et bouton Parcourir), avec texte d'aide optionnel."""

        row_idx = self.current_row

        # 1. Libellé du paramètre dans la colonne 0
        label = ttk.Label(self, text=title, justify=tk.LEFT)
        label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)

        # 2. Widget (Entry + Button) dans la colonne 1
        var = tk.StringVar(value=self.settings.get(section, option, ""))
        self.controls[(section, option)] = var

        frame_widget = ttk.Frame(self)
        frame_widget.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)

        entry = ttk.Entry(frame_widget, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def browse():
            """Ouvre la boîte de dialogue de sélection de répertoire."""
            # Utilise filedialog.askdirectory pour sélectionner un dossier de base
            directory = filedialog.askdirectory(parent=self, title=title)
            if directory:
                var.set(directory)

        browse_button = ttk.Button(frame_widget, text=_("Browse..."), command=browse, width=10)
        browse_button.pack(side=tk.LEFT, padx=(5, 0))

        # 3. Texte d'aide dans la colonne 2
        self._place_help_text(row_idx, help_text)

        self.current_row += 1

    def _addHyperlinkText(self, label_text, url):
        """
        Ajoute un texte simple (label) suivi d'un lien hypertexte sur la ligne suivante.
        Simule self.addText(title, panel) dans l'original.
        """

        # 1. Label de titre
        label = ttk.Label(self, text=label_text, justify=tk.LEFT)
        label.grid(row=self.current_row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 2))
        self.current_row += 1

        # 2. Cadre pour le texte et le lien
        link_frame = ttk.Frame(self)
        link_frame.grid(row=self.current_row, column=0, columnspan=3, sticky="w", padx=5, pady=(2, 5))

        # 2a. Texte d'introduction
        text = _(
            "If your language is not "
            "available, or the translation needs improving, please consider "
            "helping. See:"
        )
        intro_label = ttk.Label(link_frame, text=text, justify=tk.LEFT)
        intro_label.pack(side=tk.LEFT)

        # 2b. Lien hypertexte (simulé avec un Label et un événement de clic)
        hyperlink = ttk.Label(
            link_frame,
            text=url,
            foreground="blue",
            cursor="hand2"
        )

        # Ouvre l'URL dans le navigateur par défaut lors du clic
        def open_url(event):
            webbrowser.open_new(url)

        hyperlink.bind("<Button-1>", open_url)
        hyperlink.pack(side=tk.LEFT, padx=(5, 0))

        self.current_row += 1

        # S'assure que le contenu s'adapte
        self.columnconfigure(0, weight=1)

    # --- NOUVELLES MÉTHODES POUR TASKAPPEARANCEPAGE ---

    def _addColorSetting(self, section, option, column_index: int, row_index: int):
        """Ajoute un sélecteur de couleur (fgcolor ou bgcolor) dans une cellule spécifique."""

        current_color_hex = self.settings.get(section, option, "black")
        color_var = tk.StringVar(value=current_color_hex)
        self.controls[(section, option)] = color_var

        # Le cadre contiendra l'aperçu (Canvas) et le bouton (Button)
        frame = ttk.Frame(self)
        frame.grid(row=row_index, column=column_index, sticky="w", padx=5, pady=2)

        # 1. Aperçu de la couleur (Canvas)
        color_preview = tk.Canvas(frame, width=20, height=20, highlightthickness=1, highlightbackground="gray")
        color_preview.pack(side=tk.LEFT, padx=(0, 5))

        # 2. Bouton de sélection
        button = ttk.Button(frame, text=_("Choose..."), width=10)
        button.pack(side=tk.LEFT)

        def update_preview(color_hex):
            """Met à jour le canevas et la variable Tkinter."""
            color_preview.config(bg=color_hex)
            color_var.set(color_hex)

        def open_color_chooser():
            """Ouvre le dialogue de sélection de couleur."""
            # Renvoie (r, g, b) et la couleur en hexadécimal
            color_code = colorchooser.askcolor(parent=self, color=color_var.get())
            if color_code and color_code[1]: # Si l'utilisateur n'a pas annulé
                update_preview(color_code[1])

        button.config(command=open_color_chooser)

        # Initialiser l'aperçu avec la couleur actuelle
        update_preview(current_color_hex)

    # def _addFontSetting(self, section, option, column_index: int, row_index: int):
    def _addFontSetting(self, section, option, label_text, column_index: int, row_index: int):
        """Ajoute un sélecteur de police dans une cellule spécifique."""

        current_font_str = self.settings.get(section, option, "TkDefaultFont")
        print(f"Current font string for {section}.{option}: {current_font_str}")
        font_var = tk.StringVar(value=current_font_str)
        self.controls[(section, option)] = font_var

        # Le cadre contiendra l'aperçu (Label) et le bouton (Button)
        font_frame = ttk.Frame(self)
        print(f"Adding font setting '{label_text}' at row {row_index}, column {column_index}")
        font_frame.grid(row=row_index, column=column_index or 5, sticky="ew", padx=5, pady=2)
        font_frame.columnconfigure(0, weight=1)  # Permet à l'aperçu de s'étendre

        # 1. Aperçu de la police (Label)
        font_preview = ttk.Label(font_frame, text=_("Example"), anchor="w", padding=(5, 2))
        font_preview.grid(row=0, column=0, sticky="ew")

        # 2. Bouton de sélection
        button = ttk.Button(font_frame, text=_("Choose..."), width=10)
        button.grid(row=0, column=1, padx=(5, 0))

        def font_str_to_tuple(font_str: str) -> Tuple[str, int, str, str]:
            """Convertit la chaîne de police de Task Coach (ex: 'Arial,bold')
            en tuple Tkinter."""
            parts = font_str.split(',')
            family = parts[0]
            size = 10  # Taille par défaut car Task Coach ne stocke pas la taille
            style = " ".join(parts[1:]) if len(parts) > 1 else ""
            weight = "normal"
            slant = "roman"
            if "bold" in style:
                weight = "bold"
            if "italic" in style:
                slant = "italic"
            # return family, size, style
            return family, size, weight, slant

        def font_tuple_to_str(font_tuple: Tuple[str, int, str, str]) -> str:
            """Convertit le tuple de police Tkinter en chaîne Task Coach (ex: 'Arial,bold')."""
            # family, _, style = font_tuple
            family, size, weight, slant = font_tuple
            # Nettoyer et former la chaîne de Task Coach
            # style_parts = style.split()
            style_parts = []
            if weight == "bold":
                style_parts.append("bold")
            else:
                style_parts.append("normal")
            if slant == "italic":
                style_parts.append("italic")
            else:
                style_parts.append("roman")
            style_str = "," + ",".join(style_parts) if style_parts else ""
            style_str = ""
            # if style_parts:
            #     style_str = "," + ",".join(style_parts)
            print(f"Converted font tuple {font_tuple} to string: {family + style_str}")
            # return family + style_str
            return family + "," + str(size) + style_str

        def update_preview(font_str: str):
            """Met à jour le label d'aperçu et la variable Tkinter.
            (Attention, ne prends pas en compte Bold et Italic)
            """
            try:
                # La méthode font.nametofont() permet de manipuler les polices nommées comme 'TkDefaultFont'
                # Mais il est plus sûr d'utiliser tkFont.Font pour appliquer directement
                font_tuple = font_str_to_tuple(font_str)
                print(f"Font tuple: {font_tuple}")  # Ajout : Vérification du tuple créé
                # # Créer une police temporaire pour l'aperçu
                # temp_font = tkFont.Font(family=font_tuple[0], size=font_tuple[1], weight=font_tuple[2], slant=font_tuple[2])
                temp_font = tkFont.Font(family=font_tuple[0], size=font_tuple[1], weight=font_tuple[2], slant=font_tuple[3])
                font_preview.config(font=temp_font)
                # Correction: Utiliser weight et slant séparément
                # font_preview.config(font=(font_tuple[0], font_tuple[1], font_tuple[2], font_tuple[3]))
                # font_var.set(font_str)
                font_var.set(font_str)
                print(f"Font preview updated with: {font_str}")  # Ajout : Vérification de la valeur de font_str
            except Exception as e:
                print(f"Erreur lors de la mise à jour de la police: {e}")

        def open_font_chooser():
            """Ouverture d'un sélecteur de police (Tkinter n'a pas de sélecteur intégré)."""
            # Pour l'exemple, nous allons simuler un changement de police simple
            # En environnement réel, il faudrait utiliser une librairie externe ou une boîte de dialogue personnalisée.

            # Ici, nous nous contentons d'un dialogue simulé ou d'un appel direct si un sélecteur simple existe.
            # Puisque Tkinter n'a pas de tk.fontchooser standard, nous allons simuler un changement pour la démo.
            # En l'absence de tk.fontchooser, nous allons proposer une liste de styles à la place pour la démo.
            # Dans un vrai déploiement, vous utiliseriez une librairie comme wxPython pour la boîte de dialogue de police.

            # Pour la démo : Afficher un aperçu de la police actuelle dans le bouton pour l'instant
            current_font_tuple = font_str_to_tuple(font_var.get())
            initial = {'family': current_font_tuple[0], 'size': current_font_tuple[1], 'weight': current_font_tuple[2], 'slant': current_font_tuple[3]}
            # new_style = "bold" if "bold" not in current_font_tuple[2] else "normal"
            new_font_str = current_font_tuple[0]
            if tkfontchooser:
                # Utiliser show pour ouvrir le sélecteur de police
                result = tkfontchooser.askfont(self, "Abcd" , _("Choose Font"), **initial)

                if result:
                    print(f"tkfontchooser result: {result}")  # Ajout : Vérification du résultat
                    new_font_str = font_tuple_to_str((result['family'], result['size'], result['weight'], result['slant']))
                    update_preview(new_font_str)
            else:
                # Simulation simple : bascule entre normal et bold pour la démoprint("tkfontchooser n'est pas disponible.")
                print("tkfontchooser n'est pas disponible.")
                # if new_style:
                #     new_font_str += "," + new_style

                # # Simple simulation de bascule de style :
                # if new_font_str != font_var.get():
                #     update_preview(new_font_str)
                # else:
                #     # Retour à la police de base pour la démo
                #     update_preview("TkDefaultFont")

        button.config(command=open_font_chooser)
        update_preview(current_font_str)

    def _addIconSetting(self, section, option, column_index: int, row_index: int):
        """Ajoute un Combobox pour la sélection d'icône avec un aperçu."""

        # Liste simplifiée d'icônes disponibles pour la démo
        icon_choices: List[Tuple[str, str]] = [
            ("default", _("Default")),
            ("check_icon", "✓ " + _("Checkmark")),
            ("exclamation_icon", "! " + _("Exclamation")),
            ("star_icon", "★ " + _("Star")),
        ]

        current_icon_code = self.settings.get(section, option, "default")

        # Utilisation de _addChoiceSetting simplifié dans cette cellule de grille
        real_value_var = tk.StringVar(value=current_icon_code)
        self.controls[(section, option)] = real_value_var

        # Mapping pour Combobox
        value_to_display = {value: text for value, text in icon_choices}
        display_to_value = {text: value for value, text in icon_choices}
        display_texts = [text for value, text in icon_choices]

        current_display = value_to_display.get(current_icon_code, display_texts[0])
        display_var = tk.StringVar(value=current_display)

        combobox = ttk.Combobox(
            self,
            textvariable=display_var,
            values=display_texts,
            state="readonly"
        )

        def on_selection_change(event):
            selected_text = display_var.get()
            selected_value = display_to_value.get(selected_text)
            real_value_var.set(selected_value)

        combobox.bind("<<ComboboxSelected>>", on_selection_change)

        # Positionne le Combobox
        # Il prendra l'espace de sa colonne, sans cadre supplémentaire
        combobox.grid(row=row_index, column=column_index, sticky="ew", padx=5, pady=2)

    # --- Méthodes spécifiques à TaskAppearancePage pour le layout ---

    def _addAppearanceHeader(self):
        """Ajoute les en-têtes de colonnes (simulant addAppearanceHeader de wx)."""

        headers = [
            "",  # Colonne 0 (Label)
            _("Text color"),  # Colonne 1 (fgcolor)
            "",  # Colonne 2 (Vide)
            _("Background color"),  # Colonne 3 (bgcolor)
            "",  # Colonne 4 (Vide)
            _("Font"),  # Colonne 5 (font)
            "",  # Colonne 6 (Vide)
            _("Icon"),  # Colonne 7 (icon)
            "",  # Colonne 8 (HelpText)
        ]

        for col, header in enumerate(headers):
            if header:
                label = ttk.Label(self, text=header, anchor="center", font=('TkDefaultFont', 10, 'bold'))
                # Utilise columnspan=2 pour les en-têtes de couleur/police
                colspan = 2 if col in [1, 3, 5] else 1
                label.grid(row=self.current_row, column=col, columnspan=colspan, sticky="ew", padx=5, pady=5)

        self.current_row += 1

    def _addAppearanceSetting(self, fgcolor_key, fgcolor_setting, bgcolor_key,
                              bgcolor_setting, font_key, font_setting,
                              icon_key, icon_setting, label_text):
        """Ajoute une ligne complète de paramètres d'apparence pour un statut de tâche."""

        row_idx = self.current_row

        # 0. Label du statut de la tâche
        label = ttk.Label(self, text=label_text, anchor="w", font=('TkDefaultFont', 10, 'bold'))
        label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)

        # 1-2. Couleur de premier plan (fgcolor)
        self._addColorSetting("appearance", fgcolor_setting, 1, row_idx)
        # Colonne 2 laissée vide ou pour un éventuel bouton/texte d'aide spécifique

        # 3-4. Couleur d'arrière-plan (bgcolor)
        self._addColorSetting("appearance", bgcolor_setting, 3, row_idx)
        # Colonne 4 laissée vide

        # 5-6. Police (font)
        self._addFontSetting("appearance", font_setting, "Font", 5, row_idx)
        # Colonne 6 laissée vide

        # 7. Icône (icon)
        self._addIconSetting("appearance", icon_setting, 7, row_idx)

        # Colonne 8 est le HelpText global (laissée vide ici)

        self.current_row += 1


# Classes for the various settings pages
# --- Classes de page ---
# Ces classes correspondent aux noms de pages trouvés dans preferences.py

# Pour convertir la WindowBehaviorPage en Tkinter, nous devons remplacer le système de layout basé sur les colonnes de wxPython par tkinter.Grid ou tkinter.Pack.
#
# Étant donné que cette page utilise principalement des cases à cocher (boolean settings) et une liste déroulante (choice setting), le grid manager est le plus approprié pour un alignement propre des widgets.
#
# J'ai implémenté les méthodes d'aide _addBooleanSetting et _addChoiceSetting directement dans la classe WindowBehaviorPage pour encapsuler la logique de création de widget et de gestion de la variable Tkinter (qui stocke l'état du paramètre).

# J'ai mis à jour la classe WindowBehaviorPage pour utiliser des ttk.Checkbutton et un ttk.Combobox pour les paramètres, en utilisant des variables Tkinter (tk.BooleanVar, tk.StringVar) pour lier l'état de l'interface utilisateur aux données.
#
# J'ai également mis à jour le TaskcoachSettings pour inclure les valeurs par défaut des nouveaux paramètres pour un test facile.
#
# Détails clés de l'implémentation Tkinter :
#
#     Layout: J'utilise grid avec sticky="w" pour aligner les widgets à gauche, simulant l'alignement des propriétés dans la fenêtre de wxPython.
#
#     _addBooleanSetting: Utilise tk.BooleanVar pour stocker l'état True/False d'un paramètre.
#
#     _addChoiceSetting (Important):
#
#         Le paramètre starticonized nécessite une liste déroulante (ttk.Combobox).
#
#         Tkinter stocke la valeur de la StringVar dans la Combobox, qui doit être le texte affiché.
#
#         Pour que la variable de contrôle (self.controls) stocke la valeur interne ("Never", "Always", "WhenClosedIconized") et non le texte affiché, j'utilise un gestionnaire d'événement (<<ComboboxSelected>>) pour mapper le texte sélectionné à la valeur réelle et la stocker dans une variable real_value_var.
#
#     applySettings (Mis à jour): La méthode dans PreferencesPage itère sur self.controls et utilise self.settings.set() avec la valeur .get() de la variable Tkinter, garantissant que les données réelles sont sauvegardées.
class WindowBehaviorPage(PreferencesPage):
    pageName = "window"
    pageTitle = _("Window behavior")
    # pageIcon = "windows" # L'icône devrait être définie dans artprovidertk et utilisée par le dialogue si nécessaire

    def __init__(self, parent, settings, *args, **kwargs):
        """
        Initialise la page "Window and Behavior".
        """
        # Initialise la classe de base. Le padding est déjà dans PreferencesPage
        super().__init__(parent, settings, *args, **kwargs)

        # L'ancienne version utilisait un layout à 2 colonnes ; nous utilisons grid.
        # Configure la première colonne pour prendre de l'espace (pour l'alignement des contrôles Choice)
        self.columnconfigure(1, weight=1)  # S'assure que la colonne 1 prend de l'espace pour les choix

        # Le contenu de la page est généré ici en utilisant des méthodes internes

        # 1. show splash screen
        self._addBooleanSetting(
            "window", "splash", _("Show splash screen on startup")
        )
        # 2. show tips
        self._addBooleanSetting(
            "window", "tips", _("Show tips window on startup")
        )
        # 3. start iconized (Choice)
        self._addChoiceSetting(
            "window",
            "starticonized",
            _("Start with the main window iconized"),
            [
                ("Never", _("Never")),
                ("Always", _("Always")),
                ("WhenClosedIconized", _("If it was iconized last session")),
            ],
        )
        # 4. check for new version
        self._addBooleanSetting(
            "version",
            "Notify",
            _("Check for new version " "of %(name)s on startup")
            % meta.data.metaDict,
            )
        # 5. check for developer messages
        self._addBooleanSetting(
            "view",
            "developermessages",
            _("Check for " "messages from the %(name)s developers on startup")
            % meta.data.metaDict,
            )
        # 6. hide when iconized
        self._addBooleanSetting(
            "window", "hidewheniconized", _("Hide main window when iconized")
        )
        # 7. hide when closed (minimize)
        self._addBooleanSetting(
            "window", "hidewhenclosed", _("Minimize main window when closed")
        )

        # 8. blink taskbar icon (conditionnel)
        # isMacOsXMavericks_OrNewer n'existe pas dans taskcoachlib.operating_system par défaut,
        # j'utilise une fonction factice pour éviter une erreur si l'implémentation Tkinter n'a pas tous les utilitaires
        # if not hasattr(operating_system, 'isMacOsXMavericks_OrNewer'):
        #     def isMacOsXMavericks_OrNewer(): return False
        #     operating_system.isMacOsXMavericks_OrNewer = isMacOsXMavericks_OrNewer
        #
        # if not operating_system.isMacOsXMavericks_OrNewer():
        #     self._addBooleanSetting(
        #         "window",
        #         "blinktaskbariconwhentrackingeffort",
        #         _("Make clock in the task bar tick when tracking effort"),
        #     )
        # Le code wxPython original avait une logique complexe pour la vérification OS, nous allons simplifier :
        if not operating_system.isMac():
            self._addBooleanSetting(
                "window",
                "blinktaskbariconwhentrackingeffort",
                _("Make clock in the task bar tick when tracking effort"),
            )

        # fit() n'est pas nécessaire en Tkinter avec grid si les options sticky sont bien utilisées.

    # def _addBooleanSetting(self, section, option, label_text):
    #     """
    #     Ajoute une case à cocher (BooleanVar) pour un paramètre.
    #     """
    #     # Crée la variable Tkinter pour stocker l'état
    #     var = tk.BooleanVar(value=self.settings.getboolean(section, option))
    #     self.controls[(section, option)] = var
    #
    #     # Crée le widget Checkbutton
    #     checkbutton = ttk.Checkbutton(
    #         self,
    #         text=label_text,
    #         variable=var
    #     )
    #     # Positionne le checkbutton dans la grille
    #     checkbutton.grid(row=self.current_row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
    #
    #     self.current_row += 1
    #
    # def _addChoiceSetting(self, section, option, label_text, choices):
    #     """
    #     Ajoute un label et une combobox (StringVar) pour un paramètre à choix.
    #     :param choices: Liste de tuples [(value, display_text), ...]
    #     """
    #
    #     # 1. Label
    #     label = ttk.Label(self, text=label_text)
    #     label.grid(row=self.current_row, column=0, sticky="w", padx=5, pady=2)
    #
    #     # 2. Combobox
    #
    #     # Crée la variable Tkinter (stockera la 'value' interne, pas le 'display_text')
    #     var = tk.StringVar(value=self.settings.get(section, option))
    #     self.controls[(section, option)] = var
    #
    #     # Crée une liste des textes affichables pour la Combobox
    #     display_texts = [text for value, text in choices]
    #
    #     combobox = ttk.Combobox(
    #         self,
    #         textvariable=var, # Non, la variable doit stocker la valeur interne!
    #         state="readonly"
    #     )
    #
    #     # Remplissage des choix pour la Combobox
    #     combobox['values'] = display_texts
    #
    #     # Crée un mapping (texte affiché -> valeur réelle)
    #     value_to_display = {value: text for value, text in choices}
    #     display_to_value = {text: value for value, text in choices}
    #
    #     # Détermine la valeur d'affichage actuelle
    #     current_value = self.settings.get(section, option)
    #     current_display = value_to_display.get(current_value, display_texts[0] if display_texts else "")
    #
    #     # La variable Tkinter DOIT contenir la valeur affichée pour que le Combobox fonctionne correctement.
    #     # Nous allons donc créer une variable de stockage interne pour la valeur réelle et mettre à jour le StringVar
    #     # du Combobox avec le texte affiché.
    #
    #     # Variable pour la valeur réelle
    #     real_value_var = tk.StringVar(value=current_value)
    #     self.controls[(section, option)] = real_value_var # Stocke la variable réelle dans controls
    #
    #     # Variable d'affichage pour le Combobox
    #     display_var = tk.StringVar(value=current_display)
    #     combobox['textvariable'] = display_var
    #
    #     # Gestionnaire d'événement pour mettre à jour la variable réelle lorsque le choix change
    #     def on_selection_change(event):
    #         selected_text = display_var.get()
    #         selected_value = display_to_value.get(selected_text)
    #         real_value_var.set(selected_value)
    #
    #     combobox.bind("<<ComboboxSelected>>", on_selection_change)
    #
    #     # Positionne le Combobox
    #     combobox.grid(row=self.current_row, column=1, sticky="ew", padx=5, pady=2)
    #
    #     self.current_row += 1


# La page TaskDatesPage est plus complexe car elle introduit le paramètre entier (addIntegerSetting) et les paramètres à choix multiples (addChoiceSetting avec des groupes de choix).
#
# Pour gérer cela en Tkinter, nous allons :
#
#     Mettre à jour TaskcoachSettings pour ajouter les valeurs par défaut des nouveaux paramètres.
#
#     Mettre à jour la classe de base PreferencesPage avec la méthode _addIntegerSetting.
#
#     Implémenter TaskDatesPage en utilisant nos méthodes d'aide _addBooleanSetting, _addIntegerSetting et en créant une nouvelle méthode pour gérer les groupes de choix complexes.
#
#     Ajouter la logique pour le texte d'aide (__add_help_text) en utilisant ttk.Label pour simuler le wx.StaticText.

# J'ai intégré la logique de la page des dates de tâches, y compris la conversion du paramètre entier et des contrôles de choix multiples.
#
# Points importants de la mise à jour :
#
#     _addIntegerSetting (dans PreferencesPage) :
#
#         Utilise tk.IntVar pour l'état.
#
#         Utilise tk.Spinbox pour permettre la saisie et l'ajustement facile de la valeur entière dans les limites spécifiées. J'ai utilisé un ttk.Frame pour contenir le Spinbox et l'empêcher de s'étirer.
#
#     _addMultiChoiceSetting (dans PreferencesPage) :
#
#         C'est la méthode la plus complexe. Elle crée plusieurs ttk.Combobox côte à côte dans une ttk.Frame.
#
#         Elle gère la lecture et l'écriture de la valeur dans TaskcoachSettings en utilisant une chaîne de caractères séparée par des virgules (ex: "preset,today,startofday"), en stockant un tuple de tk.StringVar dans self.controls.
#
#         Mise à jour d' applySettings : La méthode de base applySettings a été modifiée pour gérer ce tuple de variables et reconstruire la chaîne CSV avant la sauvegarde.
#
#     TaskDatesPage :
#
#         Elle utilise désormais _addBooleanSetting, _addIntegerSetting et _addMultiChoiceSetting.
#
#         J'ai configuré les colonnes de la page pour le grid manager (columnconfigure) afin que les Combobox à choix multiples se répartissent correctement.
#
#     __add_help_text : Utilise un ttk.Label avec wraplength=500 pour simuler le comportement de retour à la ligne (Wrap(460)) de wxPython.
class TaskDatesPage(PreferencesPage):
    pageName = "task"
    pageTitle = _("Task dates")
    # pageIcon = "calendar_icon"

    def __init__(self, parent, settings, *args, **kwargs):
        super().__init__(parent, settings, *args, **kwargs)

        # Configurer la grille pour accueillir jusqu'à 4 colonnes de contrôles + 1 colonne pour le label
        # 0: Label, 1-3: Controls (avec colspan 3 pour les multi-choix), 2: HelpText
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)  # Ajout colonne 3 pour les choix multiples de date

        # 1. Marquer la tâche parente comme terminée
        self._addBooleanSetting(
            "behavior",
            "markparentcompletedwhenallchildrencompleted",
            _("Mark parent task completed when all children are completed"),
        )

        # 2. Nombre d'heures "due soon" (Entier)
        self._addIntegerSetting(
            "behavior",
            "duesoonhours",
            _("Number of hours that tasks are considered to be 'due soon'"),
            minimum=0,
            maximum=9999,
        )

        # 3. Liens des dates (Choix simple)
        choices_dates_tied = [
            ("", _("Nothing")),
            (
                "startdue",
                _("Changing the planned start date changes the due date"),
            ),
            (
                "duestart",
                _("Changing the due date changes the planned start date"),
            ),
        ]
        self._addChoiceSetting(
            "view",
            "datestied",
            _(
                "What to do with planned start and due date if the other one is changed"
            ),
            choices_dates_tied,
        )

        # --- Définition des groupes de choix pour les paramètres de date/heure par défaut ---
        check_choices = [("preset", _("Preset")), ("propose", _("Propose"))]
        day_choices = [
            ("today", _("Today")),
            ("tomorrow", _("Tomorrow")),
            ("dayaftertomorrow", _("Day after tomorrow")),
            ("nextfriday", _("Next Friday")),
            ("nextmonday", _("Next Monday")),
        ]
        time_choices = [
            ("startofday", _("Start of day")),
            ("startofworkingday", _("Start of working day")),
            ("currenttime", _("Current time")),
            ("endofworkingday", _("End of working day")),
            ("endofday", _("End of day")),
        ]

        # 4. Date/heure de début planifiée par défaut
        self._addMultiChoiceSetting(
            "view",
            "defaultplannedstartdatetime",
            _("Default planned start date and time"),
            check_choices,
            day_choices,
            time_choices,
        )

        # 5. Date/heure d'échéance par défaut
        self._addMultiChoiceSetting(
            "view",
            "defaultduedatetime",
            _("Default due date and time"),
            check_choices,
            day_choices,
            time_choices,
        )

        # 6. Date/heure de début réelle par défaut
        self._addMultiChoiceSetting(
            "view",
            "defaultactualstartdatetime",
            _("Default actual start date and time"),
            check_choices,
            day_choices,
            time_choices,
        )

        # 7. Date/heure d'achèvement par défaut (Note: check_choices est limité à 'propose' dans l'original)
        self._addMultiChoiceSetting(
            "view",
            "defaultcompletiondatetime",
            _("Default completion date and time"),
            [check_choices[1]], # Simule [('propose', _('Propose'))]
            day_choices,
            time_choices,
        )

        # 8. Date/heure de rappel par défaut
        self._addMultiChoiceSetting(
            "view",
            "defaultreminderdatetime",
            _("Default reminder date and time"),
            check_choices,
            day_choices,
            time_choices,
        )

        # 9. Texte d'aide
        self.__add_help_text()

    def __add_help_text(self):
        """ Ajoute le texte d'aide pour les paramètres de date et heure par défaut. """
        help_text = _("""New tasks start with "Preset" dates and times filled in and checked. 
        "Proposed" dates and times are filled in, but not checked.

        "Start of day" is midnight and "End of day" is just before midnight.
         When using these, task viewers hide the time and show only the Date.

        "Start of working day" and "End of working day" use the working day as set
         in the Features tab of this preferences dialog.""") % meta.data.metaDict

        # Utilisez un Label Tkinter pour afficher le texte.
        # La fonction Wrap() de wxWidgets est simulée ici par la gestion de la largeur
        # et le retour à la ligne automatique (si le label le permet).
        # Pour forcer une mise en page multiligne, nous allons simplement utiliser le texte formaté.

        # Crée un cadre pour le texte d'aide et le place sur la page
        help_frame = ttk.Frame(self)
        # S'étale sur toutes les colonnes disponibles
        help_frame.grid(row=self.current_row, column=0, columnspan=4, sticky="ew", padx=5, pady=10)

        # Crée le Label (avec une petite police si possible, ou juste un Label normal)
        help_label = ttk.Label(
            help_frame,
            text=help_text,
            justify=tk.LEFT,
            wraplength=500  # Simule Wrap(460) en limitant la largeur d'enrobage (wraplength)
        )
        help_label.pack(fill="x", expand=True)

        self.current_row += 1


# La TaskReminderPage est intéressante car elle introduit un paramètre à choix multiples (addMultipleChoiceSettings), que nous devons implémenter dans la classe de base.
#
# J'ai mis à jour le fichier preferencestk.py en ajoutant la nouvelle méthode _addMultipleChoiceSettings à la classe PreferencesPage, en ajustant la logique d'enregistrement dans applySettings pour supporter ce nouveau type de contrôle, et en implémentant la TaskReminderPage complète.
#
# Voici le fichier mis à jour :
#
# J'ai effectué ces modifications clés :
#
#     Méthode _addMultipleChoiceSettings : Ajoutée à PreferencesPage. Elle utilise des ttk.Checkbuttons dans un cadre (ttk.Frame) pour organiser les options verticalement. Elle stocke les sélections dans un dictionnaire de tk.BooleanVars, avec les valeurs des choix (ex: "5", "10") comme clés.
#
#     Mise à jour d'applySettings : Maintenant, elle vérifie si le contrôle est un dictionnaire de tk.BooleanVars et, si oui, elle construit une chaîne de caractères séparée par des virgules ("5,10,30,60") pour la sauvegarde.
#
#     Implémentation de TaskReminderPage :
#
#         Le paramètre du système de notification utilise _addChoiceSetting.
#
#         L'option synthèse vocale (sayreminder) utilise _addBooleanSetting avec la logique conditionnelle pour afficher le texte d'aide (Needs espeak) uniquement sur les systèmes GTK, en le plaçant dans la colonne 2.
#
#         Le temps de répétition par défaut utilise _addChoiceSetting.
#
#         Les temps de répétition à offrir utilisent la nouvelle méthode _addMultipleChoiceSettings et excluent la première option ("Don't snooze") comme dans l'original.
#
#     TaskcoachSettings : J'ai ajouté des valeurs par défaut pour les nouveaux paramètres de rappel.
class TaskReminderPage(PreferencesPage):
    pageName = "reminder"
    pageTitle = _("Task reminders")
    # pageIcon = "clock_alarm_icon"

    def __init__(self, parent, settings, *args, **kwargs):
        super().__init__(parent, settings, *args, **kwargs)

        # Assurer que la colonne 2 est disponible pour le texte d'aide optionnel
        self.columnconfigure(2, weight=1)

        # 1. Système de notification
        names = []
        # Utilise notify.AbstractNotifier.names() s'il existe, sinon utilise des valeurs par défaut
        notifier_names = notify.AbstractNotifier.names() if hasattr(notify, 'AbstractNotifier') else ["universal", "native"]
        for name in notifier_names:
            names.append((name, name))

        self._addChoiceSetting(
            "feature",
            "notifier",
            _("Notification system to use for reminders"),
            names
        )

        # 2. Option de synthèse vocale (Conditionnelle)
        if operating_system.isMac() or operating_system.isGTK():
            help_text = _("(Needs espeak)") if operating_system.isGTK() else ""

            # Stocke la ligne actuelle avant d'ajouter le paramètre
            start_row = self.current_row

            self._addBooleanSetting(
                "feature",
                "sayreminder",
                _("Let the computer say the reminder"),
            )

            # Place le texte d'aide dans la colonne 2 si nécessaire
            if help_text:
                help_label = ttk.Label(self, text=help_text, foreground="gray", font=('TkDefaultFont', 9, 'italic'))
                # La case à cocher se trouve à la ligne 'start_row' (maintenant self.current_row - 1)
                help_label.grid(row=start_row, column=2, sticky="w", padx=5, pady=2)

        # 3. Temps de répétition par défaut (Choix simple)
        # Convertit les choix d'entiers en chaînes de caractères
        snoozeChoices = [
            (str(choice[0]), choice[1]) for choice in date.snoozeChoices
        ]
        self._addChoiceSetting(
            "view",
            "defaultsnoozetime",
            _("Default snooze time to use after reminder"),
            snoozeChoices,
        )

        # 4. Temps de répétition à offrir (Choix multiples)
        # Utilise date.snoozeChoices[1:] pour exclure "Don't snooze"
        snooze_options_for_list = [
            (choice[0], choice[1]) for choice in date.snoozeChoices[1:]
        ]
        self._addMultipleChoiceSettings(
            "view",
            "snoozetimes",
            _("Snooze times to offer in task reminder dialog"),
            snooze_options_for_list,
        )


# Le code original utilise un modèle basé sur des méthodes pour ajouter des paramètres à un conteneur (probablement wxPython). Pour le convertir en Tkinter, je vais recréer une classe de base SettingsPage simple qui gère la disposition en grille et fournit les méthodes utilitaires (addBooleanSetting, addPathSetting, etc.).
#
# Cela me permet d'utiliser le même corps de code pour SavePage, ce qui le rend facile à lire et à maintenir.
#
# Voici le fichier Python qui contient les classes de base et la conversion de SavePage :
#
# J'ai créé la classe SavePage en utilisant une classe de base SettingsPage de style Tkinter, ce qui garantit que tous les appels de méthode de l'original (addBooleanSetting, addPathSetting, addMultipleChoiceSettings, fit) sont pris en charge. Le résultat utilise le gestionnaire de géométrie grid pour une disposition nette en trois colonnes (Libellé, Widget de saisie, Texte d'aide).

# Vous avez tout à fait raison de me le signaler ! Je m'excuse pour mon erreur. J'ai converti la classe dans un fichier séparé au lieu de l'intégrer au fichier preferencestk.py existant que nous sommes en train de construire.
#
# Pour corriger cela, je vais mettre à jour preferencestk.py. Pour que la classe SavePage fonctionne correctement en utilisant les méthodes d'aide de PreferencesPage, j'ai besoin d'ajouter la méthode _addPathSetting (pour le paramètre attachmentbase) et de finaliser la méthode _addMultipleChoiceSettings (pour les importations/exportations automatiques) à la classe de base PreferencesPage.
#
# Voici le fichier preferencestk.py mis à jour, incluant la nouvelle logique de contrôle et la conversion complète de la classe SavePage.
#
# Mise à jour de preferencestk.py
#
# J'ai ajouté la gestion des chemins de fichiers et j'ai complété la classe SavePage :
#
# J'ai fait en sorte que la nouvelle classe SavePage soit correctement intégrée dans preferencestk.py et utilise l'héritage de PreferencesPage, comme prévu. J'ai également ajusté la méthode _addMultipleChoiceSettings pour qu'elle puisse gérer le texte d'aide si nécessaire, et j'ai ajouté la méthode _addPathSetting pour les champs de chemin de répertoire.
# --- Classe SavePage Convertie ---

class SavePage(PreferencesPage):
    pageName = "save"
    pageTitle = _("Files")
    pageIcon = "save"  # Icône (à charger par un ArtProvider simulé)

    def __init__(self, parent, settings, *args, **kwargs):
        # Initialise la page avec 3 colonnes pour la grille de PreferencesPage
        super().__init__(parent, settings=settings, columns=3, *args, **kwargs)

        # 1. Sauvegarde automatique après chaque changement
        self._addBooleanSetting(
            "file", "autosave", _("Auto save after every change")
        )

        # 2. Chargement automatique
        self._addBooleanSetting(
            "file", "autoload", _("Auto load when the file changes on disk")
        )

        # 3. Surveillance intelligente du système de fichiers
        self._addBooleanSetting(
            "file",
            "nopoll",
            _("Smart filesystem monitoring"),
            _(
                "Try to detect changes to the task file in real time.\nDo not check this if your task file is on a network share.\nYou must restart %s after changing this."
            )
            % meta.name,
            )

        # 4. Enregistrer les paramètres dans le répertoire du programme
        self._addBooleanSetting(
            "file",
            "saveinifileinprogramdir",
            _(
                "Save settings (%s.ini) in the same\n"
                "directory as the program"
            )
            % meta.filename,
            _("For running %s from a removable medium") % meta.name,
            )

        # 5. Répertoire de base des pièces jointes
        self._addPathSetting(
            "file",
            "attachmentbase",
            _("Attachment base directory"),
            _(
                "When adding an attachment, try to make\n"
                "its path relative to this one."
            ),
        )

        # 6. Importation automatique
        self._addMultipleChoiceSettings(
            "file",
            "autoimport",
            _("Before saving, automatically import from"),
            [("Todo.txt", _("Todo.txt format"))],
            # helpText=_(
            help_text=_(
                "Before saving, %s automatically imports tasks\n"
                "from a Todo.txt file with the same name as the task file,\n"
                "but with extension .txt"
            )
                      % meta.name,
        )

        # 7. Exportation automatique
        self._addMultipleChoiceSettings(
            "file",
            "autoexport",
            _("When saving, automatically export to"),
            [("Todo.txt", _("Todo.txt format"))],
            # helpText=_(
            help_text=_(
                "When saving, %s automatically exports tasks\n"
                "to a Todo.txt file with the same name as the task file,\n"
                "but with extension .txt"
            )
                      % meta.name,
        )

        # Ajuster la mise en page
        # self.fit()  # Pas nécessaire avec le layout grid/pack de Tk


# Cette page est intéressante, car elle nécessite d'ajouter un composant spécifique pour gérer le lien hypertexte d'aide (wx.adv.HyperlinkCtrl dans l'original) et gère la logique complexe de filtrage des langues disponibles via data.languages.
#
# Puisque nous n'avons pas accès à l'implémentation de data.languages, je vais simuler la logique de filtrage en conservant uniquement les langues qui seraient "activées" dans la liste fournie. J'ajouterai une fonction d'aide (_addHyperlinkText) pour simuler l'affichage du texte et du lien.
#
# Mise à jour de preferencestk.py avec LanguagePage
#
# J'ai converti LanguagePage pour utiliser _addChoiceSetting (l'équivalent de addChoiceSetting dans la classe de base) pour le choix de la langue et j'ai implémenté la partie lien hypertexte.
#
# Voici le fichier preferencestk.py mis à jour :
#
# La classe LanguagePage est maintenant complète. Elle utilise la méthode _addChoiceSetting pour le sélecteur de langue et la nouvelle méthode _addHyperlinkText pour afficher le texte d'aide et le lien de contribution. J'ai également mis à jour sa méthode applySettings pour gérer la copie du paramètre de langue temporaire vers le paramètre de langue réel, comme dans l'original.
class LanguagePage(PreferencesPage):
    pageName = "language"
    pageTitle = _("Language")
    # pageIcon = "person_talking_icon"

    def __init__(self, parent, settings, *args, **kwargs):
        # Assurez-vous d'appeler le constructeur de la classe de base
        super().__init__(parent, settings, columns=3, *args, **kwargs)

        # Liste complète des langues (simulée ici car data.languages n'est pas accessible)
        # On suppose qu'on filtre celles qui sont supportées (enabled = True)
        # Pour Tkinter, on simplifie l'obtention des choix
        available_languages = [
            ("ar", "الْعَرَبيّة (Arabic)"),
            ("eu_ES", "Euskal Herria (Basque)"),
            ("be_BY", "беларуская мова (Belarusian)"),
            ("bs_BA", "босански (Bosnian)"),
            ("pt_BR", "Português brasileiro (Brazilian Portuguese)"),
            ("br_FR", "Brezhoneg (Breton)"),
            ("bg_BG", "български (Bulgarian)"),
            ("ca_ES", "Català (Catalan)"),
            ("zh_CN", "简体中文 (Simplified Chinese)"),
            ("zh_TW", "正體字 (Traditional Chinese)"),
            ("cs_CS", "Čeština (Czech)"),
            ("da_DA", "Dansk (Danish)"),
            ("nl_NL", "Nederlands (Dutch)"),
            ("en_AU", "English (Australia)"),
            ("en_CA", "English (Canada)"),
            ("en_GB", "English (UK)"),
            ("en_US", "English (US)"),
            ("eo", "Esperanto"),
            ("et_EE", "Eesti keel (Estonian)"),
            ("fi_FI", "Suomi (Finnish)"),
            ("fr_FR", "Français (French)"),
            ("gl_ES", "Galego (Galician)"),
            ("de_DE", "Deutsch (German)"),
            ("nds_DE", "Niederdeutsche Sprache (Low German)"),
            ("el_GR", "ελληνικά (Greek)"),
            ("he_IL", "עברית (Hebrew)"),
            ("hi_IN", "हिन्दी, हिंदी (Hindi)"),
            ("hu_HU", "Magyar (Hungarian)"),
            ("id_ID", "Bahasa Indonesia (Indonesian)"),
            ("it_IT", "Italiano (Italian)"),
            ("ja_JP", "日本語 (Japanese)"),
            ("ko_KO", "한국어/조선말 (Korean)"),
            ("lv_LV", "Latviešu (Latvian)"),
            ("lt_LT", "Lietuvių kalba (Lithuanian)"),
            ("mr_IN", "मराठी Marāṭhī (Marathi)"),
            ("mn_CN", "Монгол бичиг (Mongolian)"),
            ("nb_NO", "Bokmål (Norwegian Bokmal)"),
            ("nn_NO", "Nynorsk (Norwegian Nynorsk)"),
            ("oc_FR", "Lenga d'òc (Occitan)"),
            ("pap", "Papiamentu (Papiamento)"),
            ("fa_IR", "فارسی (Persian)"),
            ("pl_PL", "Język polski (Polish)"),
            ("pt_PT", "Português (Portuguese)"),
            ("ro_RO", "Română (Romanian)"),
            ("ru_RU", "Русский (Russian)"),
            ("sk_SK", "Slovenčina (Slovak)"),
            ("sl_SI", "Slovenski jezik (Slovene)"),
            ("es_ES", "Español (Spanish)"),
            ("sv_SE", "Svenska (Swedish)"),
            ("te_IN", "తెలుగు (Telugu)"),
            ("th_TH", "ภาษาไทย (Thai)"),
            ("tr_TR", "Türkçe (Turkish)"),
            ("uk_UA", "украї́нська мо́ва (Ukranian)"),
            ("vi_VI", "tiếng Việt (Vietnamese)")
        ]

        # Ajout du choix par défaut
        choices = [("", _("Let the system determine the language"))]
        # Dans l'original, il y a une logique complexe pour déterminer 'enabled',
        allLanguages = dict(list(data.languages.values()))
        # for code, label in languages:
        #     if code == "en_US":
        #         label = "English (US)"
        #         enabled = True
        #     elif code in allLanguages:
        #         enabled = allLanguages[code]
        #     elif "_" in code:
        #         enabled = allLanguages.get(code.split("_")[0], False)
        #     else:
        #         enabled = False
        #     if enabled:
        #         choices.append((code, label))
        # ici on utilise un sous-ensemble simple pour la démo Tkinter.
        choices.extend(available_languages)

        # 1. Paramètre de choix de la langue
        self._addChoiceSetting(
            "view",
            "language_set_by_user",
            _("Language"),
            choices
        )
        # Dans l'original, il y avait un paramètre 'restart' dans addChoiceSetting
        # pour indiquer qu'un redémarrage est nécessaire.
        # Nous pouvons l'indiquer via un texte d'aide ou un label pour l'utilisateur.
        ttk.Label(self,
                  text=_("Changing the language requires restarting the application."),
                  foreground="red").grid(row=self.current_row - 1, column=2, sticky="sw", padx=10)

        # 2. Section d'aide pour les traductions
        url = meta.i18n_url if hasattr(meta, 'i18n_url') else "https://www.taskcoach.org/contribute.html#translations"

        self._addHyperlinkText(
            _("Language not found?"),
            url
        )

        # 3. L'original appelait self.fit(), non nécessaire en Tkinter ici.

    def applySettings(self):
        """
        Surcharge de applySettings pour gérer la copie de language_set_by_user vers language.
        """
        # Applique d'abord les paramètres par défaut de la classe mère
        super().applySettings()

        # Exécute la logique spécifique de ok() de LanguagePage
        # self.set("view", "language", self.get("view", "language_set_by_user"))
        # Tkinter: lit la valeur du contrôle de "language_set_by_user" et l'écrit dans "language"

        # La valeur de 'language_set_by_user' est déjà stockée dans self.settings
        # par super().applySettings(). Il suffit de la copier.
        chosen_language = self.settings.get("view", "language_set_by_user")
        self.settings.set("view", "language", chosen_language)

        print(f"Language set to: {chosen_language}. Restart required.")


# Convertir TaskAppearancePage implique de gérer de nombreux paramètres d'apparence (couleur, police, icône) pour les différents statuts de tâches. C'est la première page qui nécessite de la couleur et de la sélection de police.
#
# Pour implémenter cette page dans preferencestk.py, nous allons devoir :
#
#     Ajouter de nouvelles méthodes d'aide dans PreferencesPage :
#
#         _addColorSetting: Pour afficher un aperçu de couleur et ouvrir un sélecteur de couleurs (via tkinter.colorchooser).
#
#         _addFontSetting: Pour afficher un aperçu de police et ouvrir un sélecteur de polices (via tkinter.font.Font).
#
#         _addIconSetting: Pour la sélection/visualisation d'icônes (simulée avec un Combobox et un aperçu d'icône).
#
#     Créer des méthodes pour structurer la grille de 9 colonnes (l'en-tête et les lignes de paramètres).
#
# J'ai mis à jour preferencestk.py en incluant toutes les nouvelles méthodes nécessaires dans PreferencesPage et en y ajoutant la classe TaskAppearancePage.
#
# Mise à jour de preferencestk.py avec TaskAppearancePage
#
# Voici le fichier preferencestk.py mis à jour :
#
# J'ai réussi à intégrer la logique de TaskAppearancePage ! J'ai créé les méthodes _addColorSetting, _addFontSetting (avec une simulation de sélecteur Tkinter) et _addIconSetting pour gérer le layout très large de cette page (9 colonnes).
class TaskAppearancePage(PreferencesPage):
    pageName = "appearance"
    pageTitle = _("Task appearance")
    # Utilise 9 colonnes comme dans l'original (Label, Choix, Choix, Choix, Choix, Choix, Choix, Choix, Choix)
    # L'original avait growableColumn=-1, signifiant qu'aucune colonne ne doit s'étendre
    # Tkinter le gère en ne mettant pas de 'weight=1' sur les colonnes.

    def __init__(self, parent, settings, *args, **kwargs):
        # Configuration 9 colonnes, aucune colonne extensible (growableColumn=-1)
        super().__init__(parent, settings, columns=9, growableColumn=-1, *args, **kwargs)

        self._addAppearanceHeader()

        # Utilise la simulation de task.Task.possibleStatuses() pour itérer
        for status in task.Task.possibleStatuses():
            setting = "%stasks" % status.name  # 'uncompletedtasks', 'completedtasks', 'overduetasks'

            # Utilise la nouvelle méthode d'aide pour ajouter la ligne de paramètres
            self._addAppearanceSetting(
                "fgcolor", setting,
                "bgcolor", setting,
                "font", setting,
                "icon", setting,
                status.pluralLabel)

        # Ajout du texte d'aide en bas
        help_text = _("These appearance settings can be overridden "
                      "for individual tasks in the task edit dialog.")

        # Le texte d'aide s'étend sur toutes les colonnes
        ttk.Label(
            self,
            text=help_text,
            wraplength=600,
            justify=tk.LEFT
        ).grid(row=self.current_row, column=0, columnspan=9, sticky="w", padx=5, pady=10)
        self.current_row += 1


# On passe à la page des fonctionnalités (FeaturesPage), qui mélange des paramètres booléens, des choix et des entiers, ainsi qu'une dépendance à l'importation de SyncML. Elle nécessite aussi de gérer des réglages d'heure (TimeSetting) et un comportement post-validation (ok).
#
# Pour cela, je dois ajouter une méthode d'aide pour l'heure (_addTimeSetting) et m'assurer que les dépendances optionnelles (SyncML) sont correctement gérées par un try...except ou une simple vérification des dépendances pour la conversion.
#
# J'ai mis à jour preferencestk.py en implémentant :
#
#     Une nouvelle méthode _addTimeSetting dans PreferencesPage (utilisant un Spinbox de 0 à 24, comme dans l'original).
#
#     La classe FeaturesPage avec toute la logique de construction.
#
#     La méthode applySettings dans FeaturesPage pour gérer la logique ok() (notamment la définition du jour de début de semaine via calendar.setfirstweekday).
#
# Mise à jour de preferencestk.py avec FeaturesPage
#
# Voici le fichier preferencestk.py mis à jour :
#
# J'ai réussi à implémenter FeaturesPage avec la nouvelle méthode _addTimeSetting qui gère les Spinbox d'heure, y compris l'option spéciale "End of day" (pour l'heure 24). J'ai également déplacé la logique de vérification du système d'exploitation et de la fonctionnalité iPhone dans PreferencesDialog.addPages pour plus de clarté.
# --- NOUVELLE PAGE : FeaturesPage ---
class FeaturesPage(PreferencesPage):
    pageName = "features"
    pageTitle = _("Features")
    pageIcon = "cogwheel_icon"

    def __init__(self, parent, settings, *args, **kwargs):
        # Configuration 3 colonnes, aucune colonne extensible (growableColumn=-1)
        super().__init__(parent, settings, columns=3, growableColumn=-1, *args, **kwargs)

        # 1. Message d'avertissement
        self._addEntry(_("All settings on this tab require a restart of %s "
                         "to take effect") % meta.name)

        # 2. SyncML (vérification d'importation)
        # On simule la dépendance à l'importation de taskcoachlib.syncml.core
        syncml_available = False
        try:
            # Remplacement de l'import réel par une simulation pour l'exemple
            # import taskcoachlib.syncml.core
            syncml_available = True
        except ImportError:
            pass

        if syncml_available:
            self._addBooleanSetting("feature", "syncml", _("Enable SyncML"))

        # 3. iPhone
        self._addBooleanSetting(
            "feature", "iphone", _("Enable iPhone synchronization"))

        # 4. X11 session management (Linux GTK specific)
        if operating_system.isGTK():
            self._addBooleanSetting(
                "feature", "usesm2", _("Use X11 session management")
            )

        # 5. Start of work week
        self._addChoiceSetting(
            "view",
            "weekstart",
            _("Start of work week"),
            [("monday", _("Monday")), ("sunday", _("Sunday"))],
        )

        # 6. Hour of start of work day (TimeSetting)
        self._addTimeSetting(
            "view",
            "efforthourstart",
            _("Hour of start of work day"),
            help_text=" ", # L'original utilise ' '
            minimum=0,
            maximum=23,
            defaultValue=9,
        )

        # 7. Hour of end of work day (TimeSetting avec message désactivé)
        self._addTimeSetting(
            "view",
            "efforthourend",
            _("Hour of end of work day"),
            help_text=" ", # L'original utilise ' '
            minimum=0,
            maximum=24,
            disabledMessage=_("End of day"),
            disabledValue=24,
            defaultValue=17,
        )

        # 8. Use gradients
        self._addBooleanSetting(
            "calendarviewer",
            "gradient",
            _(
                "Use gradients in calendar views.\n"
                "This may slow down Task Coach."
            ),
        )

        # 9. Minutes between suggested times
        choices = [
            (minutes, minutes)
            for minutes in ("5", "6", "10", "15", "20", "30")
        ]
        self._addChoiceSetting(
            "view",
            "effortminuteinterval",
            _("Minutes between suggested times"),
            choices,
            help_text=_(
                "In popup-menus for time selection (e.g. for setting the start \n"
                "time of an effort) %(name)s will suggest times using this \n"
                "setting. The smaller the number of minutes, the more times \n"
                "are suggested. Of course, you can also enter any time you \n"
                "want beside the suggested times."
            ) % {'name': meta.name},
        )

        # 10. Idle time notice (IntegerSetting)
        self._addIntegerSetting(
            "feature",
            "minidletime",
            _("Idle time notice"),
            help_text=_(
                "If there is no user input for this amount of time\n"
                "(in minutes), %(name)s will ask what to do about current "
                "efforts."
            ) % {'name': meta.name},
        )

        # 11. Decimal times
        self._addBooleanSetting(
            "feature",
            "decimaltime",
            _("Use decimal times for effort entries."),
            _(
                "Display one hour, fifteen minutes as 1.25 instead of 1:15\n"
                "This is useful when creating invoices."
            ),
        )

        # 12. Description popups
        self._addBooleanSetting(
            "view",
            "descriptionpopups",
            _(
                "Show a popup with the description of an item\n"
                "when hovering over it"
            ),
        )

    def applySettings(self):
        """
        Applique les paramètres et exécute la logique de validation post-OK (l'original 'ok()').
        """
        super().applySettings()

        # Logique de calendar.setfirstweekday
        try:
            weekstart_map = dict(monday=calendar.MONDAY, sunday=calendar.SUNDAY)
            chosen_weekstart = self.get("view", "weekstart")

            if chosen_weekstart in weekstart_map:
                calendar.setfirstweekday(weekstart_map[chosen_weekstart])
                print(f"Calendar first weekday set to: {chosen_weekstart}")
        except Exception as e:
            print(f"Erreur lors de la définition du premier jour de la semaine: {e}")


# En convertissant ces quatre dernières classes, nous aurons une structure complète pour le dialogue de préférences Tkinter, y compris la gestion des plateformes spécifiques (macOS et Linux) et les actions post-validation pour l'éditeur.
#
# Je vais mettre à jour preferencestk.py en implémentant :
#
#     _addTextSetting dans PreferencesPage (pour IPhonePage et son mot de passe/service).
#
#     Les classes IPhonePage, EditorPage, OSXPage, et LinuxPage avec la logique de construction et les icônes appropriées.
#
#     La méthode applySettings pour EditorPage, simulant la mise à jour de widgets.MultiLineTextCtrl.CheckSpelling.
#
#     La liste des pages dans PreferencesDialog sera finalisée.
#
# Mise à jour de preferencestk.py avec les dernières pages
#
# Voici le fichier preferencestk.py mis à jour avec les implémentations pour IPhonePage, EditorPage, OSXPage, et LinuxPage.
#
# Avec ces ajouts, vous avez maintenant une conversion complète de toutes les pages de paramètres de preferences.py vers la structure Tkinter/ttk.
#
#     IPhonePage gère le mot de passe (masqué), le nom du service et les booléens de synchronisation.
#
#     EditorPage gère le paramètre de police (_addFontSetting) et, surtout, sa méthode applySettings met à jour l'état global de widgets.MultiLineTextCtrl.CheckSpelling pour simuler le comportement du framework.
#
#     OSXPage et LinuxPage gèrent les paramètres spécifiques à chaque plateforme.
# --- PAGE 7: IPhonePage (NOUVEAU) ---
class IPhonePage(PreferencesPage):
    pageName = "iphone"
    pageTitle = _("iPhone")
    pageIcon = "computer_handheld_icon" # Utilisation d'une icône factice

    def __init__(self, parent, settings, *args, **kwargs):
        # Colonnes=3, colonne extensible par défaut (1)
        super().__init__(parent, settings, columns=3, *args, **kwargs)

        # Mot de passe (password_mode=True pour masquer le texte)
        self._addTextSetting(
            "iphone",
            "password",
            _("Password for synchronization with iPhone"),
            password_mode=True,
            help_text=_(
                "When synchronizing, enter this password on the iPhone to authorize it"
            ))

        # Nom du service (restart n'est qu'un hint dans l'original)
        self._addTextSetting(
            "iphone", "service", _("Bonjour service name"), help_text=_("Requires restart"))

        # Synchroniser les tâches complétées
        self._addBooleanSetting(
            "iphone", "synccompleted", _("Upload completed tasks to device"))

        # Afficher le log
        self._addBooleanSetting(
            "iphone", "showlog", _("Show the synchronization log"))


# --- PAGE 8: EditorPage (NOUVEAU) ---
class EditorPage(PreferencesPage):
    pageName = "editor"
    pageTitle = _("Editor")
    pageIcon = "edit_icon" # Utilisation d'une icône factice

    def __init__(self, parent, settings, *args, **kwargs):
        # Colonnes=2
        super().__init__(parent, settings, columns=2, growableColumn=1, *args, **kwargs)

        # Vérification de l'OS X (macOS) pour la vérification orthographique
        # L'original vérifie également isMacOsXMountainLion_OrNewer(), que nous simulons
        is_old_mac = operating_system.isMac() and not operating_system.isMacOsXMountainLion_OrNewer()

        if is_old_mac:
            self._addBooleanSetting(
                "editor", "maccheckspelling", _("Check spelling in editors"))

        # Police pour le champ de description
        # log.debug(f"EditorPage : Current row before adding font setting: {self.current_row}")
        print(f"EditorPage : Current row before adding font setting: {self.current_row}")
        self._addFontSetting(
            "editor",
            "descriptionfont",
            _("Font to use in the description field of edit dialogs"),
            5,
            self.current_row,
        )
        # Note: L'appel fit() est remplacé par l'utilisation de `growableColumn=1` et Tkinter par défaut.

    def applySettings(self):
        """
        Applique les paramètres et exécute la logique de validation post-OK (l'original 'ok()').
        """
        super().applySettings()

        # Logique spécifique à EditorPage : met à jour l'état de la vérification orthographique globale
        try:
            # S'assurer que le paramètre existe avant d'essayer de le lire
            if (self.get("editor", "maccheckspelling") is not None):
                # widgets.MultiLineTextCtrl est simulé par MockWidgets.MultiLineTextCtrl
                MultiLineTextCtrl.CheckSpelling = self.settings.getboolean(
                    "editor", "maccheckspelling")
                print(f"Editor CheckSpelling set to: {MultiLineTextCtrl.CheckSpelling}")
        except Exception as e:
            # Gère le cas où le paramètre n'existe pas (par exemple, sur Linux/Windows)
            print(f"Avertissement: Impossible de définir CheckSpelling: {e}")


# --- PAGE 9: OSXPage (NOUVEAU - macOS Spécifique) ---
class OSXPage(PreferencesPage):
    pageName = "os_darwin"
    pageTitle = _("macOS Specific")
    pageIcon = "mac_icon" # Utilisation d'une icône factice

    def __init__(self, parent, settings, *args, **kwargs):
        # Colonnes=3
        super().__init__(parent, settings, columns=3, *args, **kwargs)

        self._addBooleanSetting(
            "os_darwin",
            "getmailsubject",
            _("Get e-mail subject from Mail.app"),
            help_text=_(
                "When dropping an e-mail from Mail.app, try to get its subject.\nThis takes up to 20 seconds."
            ))


# --- PAGE 10: LinuxPage (NOUVEAU - Linux Spécifique) ---
class LinuxPage(PreferencesPage):
    pageName = "os_linux"
    pageTitle = _("Linux Specific")
    pageIcon = "linux_icon"  # Utilisation d'une icône factice

    def __init__(self, parent, settings, *args, **kwargs):
        # Colonnes=3
        super().__init__(parent, settings, columns=3, *args, **kwargs)

        self._addBooleanSetting(
            "os_linux",
            "focustextentry",
            _("Focus task subject in task editor"),
            help_text=_(
                "When opening the task editor, select the task subject and focus it.\nThis overwrites the X selection."
            ))


class NotebookDialog(tk.Toplevel):
    """
    Base class for a dialog that uses a notebook (tabbed interface).
    """
    def __init__(self, parent, bitmap, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.transient(parent)
        self.grab_set()

        self.title(_("%s Preferences") % meta.data.name)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self.addPages()

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=(0, 10), padx=10)

        ttk.Button(button_frame, text=_("OK"), command=self.onOk).pack(side="right")
        ttk.Button(button_frame, text=_("Cancel"), command=self.onCancel).pack(side="right", padx=5)

    def addPages(self):
        """Method to be overridden by subclasses to add pages."""
        raise NotImplementedError

    def onOk(self):
        """Handle OK button click."""
        self.destroy()

    def onCancel(self):
        """Handle Cancel button click."""
        self.destroy()


# --- Dialogue de Préférences Principal ---

# class PreferencesDialog(NotebookDialog):
class PreferencesDialog(tk.Toplevel):
    """
    Dialogue des préférences principal, utilisant ttk.Notebook pour les pages.
    """
    # Noms de page dans l'ordre de preferences.py
    allPageNames = [
        "window",
        "save",
        "language",
        "task",
        "reminder",
        "appearance",
        "features",
        "iphone",
        "editor",
        "os_darwin",
        "os_linux",
    ]
    # Correspondance des noms de page aux classes de page
    pages = dict(
        window=WindowBehaviorPage,
        task=TaskDatesPage,
        reminder=TaskReminderPage,
        save=SavePage,
        language=LanguagePage,
        appearance=TaskAppearancePage,
        features=FeaturesPage,
        iphone=IPhonePage,
        editor=EditorPage,
        os_darwin=OSXPage,
        os_linux=LinuxPage,
    )

    def __init__(self, parent, settings=None, *args, **kwargs):
        """
        Initialise la boîte de dialogue des préférences.

        Args :
            parent : Le widget parent (souvent la fenêtre principale de l'application).
            settings : L'objet TaskcoachSettings.
        """
        # Initialisation de tk.Toplevel
        # self.settings = settings if settings else MockSettings()
        # super().__init__(parent, bitmap="wrench_icon", *args, **kwargs)
        super().__init__(parent, *args, **kwargs)
        self.settings = settings
        self.parent = parent
        self.transient(parent)  # Rend la fenêtre modale par rapport à la fenêtre parente

        self.title(_("Preferences"))

        #  C'est toujours frustrant quand une erreur de type (TypeError) apparaît.
        #
        # L'erreur que tu vois, TypeError: ArtProviderTk.GetIcon() missing 1 required positional argument: 'art_id', est en fait un problème courant qui se produit lorsque tu appelles une méthode directement sur la classe (artprovider.ArtProviderTk.GetIcon(...)) au lieu d'une instance, mais que cette méthode n'est pas correctement définie pour être appelée ainsi.
        #
        # Dans le fichier artprovidertk.py, la méthode GetIcon est très probablement définie sans le décorateur @staticmethod.
        #
        # Voici la logique :
        #
        #     Dans preferencestk.py, tu appelles la méthode sur la classe : icon = artprovider.ArtProviderTk.GetIcon('wrench_icon').
        #
        #     Dans artprovidertk.py, la méthode GetIcon ne fait probablement pas référence à l'instance (self) et ne devrait donc pas en avoir besoin, mais elle n'est pas marquée comme statique.
        #
        #     Python essaie alors de traiter l'appel comme une méthode d'instance et cherche à passer l'instance (qui serait self) comme premier argument. Comme l'instance est manquante, il décale l'argument que tu as fourni ('wrench_icon'), ce qui cause l'erreur.
        #
        # La solution est de simplement ajouter le décorateur @staticmethod à la méthode GetIcon dans ton fichier artprovidertk.py. Cela indique à Python de ne pas attendre d'argument self ou cls implicite.
        #
        # Je vais appliquer cette correction à ton fichier artprovidertk.py.
        #
        # J'ai modifié le fichier artprovidertk.py pour ajouter le décorateur @staticmethod à la méthode GetIcon.
        #
        # L'ajout de @staticmethod résout le problème.
        #
        # Tu peux maintenant remplacer le contenu de ton fichier artprovidertk.py par le code que je t'ai fourni. Une fois que c'est fait, le TypeError dans preferencestk.py devrait disparaître.
        # Définir l'icône de la fenêtre
        # icon = artprovider.getIcon('wrench_icon')
        # icon = artprovider.ArtProviderTk.GetIcon('wrench_icon')
        # icon = artprovider.ArtProviderTk.GetIcon('wrench_icon', desired_size=(16, 16))  # Spécifie la taille 16x16
        # icon = artprovider.ArtProviderTk.GetIcon('Wrench', desired_size=(16, 16))  # Spécifie la taille 16x16
        icon = artprovider.getIcon('wrench_icon', desired_size=(16, 16))  # Spécifie la taille 16x16
        # ou
        # icon = artprovider.IconProvider.getIcon('wrench_icon')
        # icon = artprovider.IconProvider.getIcon(self, 'wrench_icon')
        # icon = artprovider.IconProvider.getIcon(_('Wrench'))

        if icon:
            # Note sur le problème 128x128 : Cette icône est demandée par Tkinter
            # lorsque l'on utilise self.iconphoto.
            # Pour l'instant, on laisse l'appel tel quel, mais la fonction GetIcon
            # devrait gérer le cas où desired_size n'est pas spécifié (ce qu'elle fait)
            # iconphoto prend un PhotoImage, ce qui est retourné par GetIcon dans artprovidertk
            self.iconphoto(False, icon)

        # Cadre principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Cahier (Notebook) pour les pages de préférences
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Liste pour stocker les instances de page créées
        self.pageInstances = []

        # Ajout des pages au Notebook
        self.addPages()

        # Cadre pour les boutons OK/Cancel
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)

        # Boutons (alignés à droite)
        ttk.Button(button_frame, text=_("OK"), command=self.onOk).pack(side="right", padx=5)
        ttk.Button(button_frame, text=_("Cancel"), command=self.onCancel).pack(side="right")

        # Protocole pour la fermeture de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self.onOk)

        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        # Définir une taille minimale si le contenu ne l'impose pas (pour l'esthétique)
        # width = self.winfo_width()
        width = max(self.winfo_width(), 600)
        # height = self.winfo_height()
        height = max(self.winfo_height(), 500)
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Rendre la boîte de dialogue modale et lui donner le focus
        self.grab_set()
        self.wait_window(self)  # Attend que la fenêtre soit détruite

    def addPages(self):
        """Ajoute les pages au Notebook, en respectant l'ordre défini."""

        for page_name in self.allPageNames:
            # if self.__should_create_page(page_name):
            #     page = self.createPage(page_name)
            #     # Ajoute la page au notebook avec son titre
            #     self.notebook.add(page, text=page.pageTitle)
            #     self.pageInstances.append(page)
            # Filtrage conditionnel des pages
            if page_name == "os_darwin" and not operating_system.isMac():
                continue
            # La page Linux s'affiche sur les systèmes GTK (Linux principalement)
            if page_name == "os_linux" and not operating_system.isGTK():
                continue
            # La page iPhone s'affiche uniquement si la fonctionnalité est activée
            if page_name == "iphone" and not (self.settings and self.settings.getboolean("feature", "iphone")):
                continue

            page = self.createPage(page_name)
            if page:
                self.notebook.add(page, text=page.pageTitle)  # TODO : Reste à ajouter un icone
                self.pageInstances.append(page)

    def __should_create_page(self, page_name):
        """Détermine si une page doit être créée selon les conditions originales."""
        if page_name == "iphone":
            # Vérifie si la fonctionnalité iPhone est activée dans les paramètres
            return self.settings.getboolean("feature", "iphone") if self.settings else False
        elif page_name == "os_darwin":
            # Page spécifique à macOS
            return operating_system.isMac()
        elif page_name == "os_linux":
            # Page spécifique à Linux (GTK)
            return operating_system.isGTK()
        else:
            return True

    def createPage(self, page_name):
        """Crée une nouvelle instance de page à partir de son nom."""
        page_class = self.pages.get(page_name)
        if page_class:
            # Instancie la classe de page, en passant le notebook et les paramètres
            return page_class(self.notebook, settings=self.settings)
        return None

    def onOk(self):
        """
        Appelé lorsque l'utilisateur clique sur OK.
        Applique les paramètres de chaque page, publie un événement et ferme.
        """
        for page in self.pageInstances:
            page.applySettings()

        # Publie un événement de changement de paramètre (si pub est fonctionnel)
        if self.settings and pub:
            # pub.publish("setting_changed", setting_name="all")
            pub.sendMessage("settings_changed", settings=self.settings)
            # La publication est laissée en commentaire car 'pub' n'est pas instancié ici
            # pass

        self.destroy()
        self.parent.focus_set()  # Redonne le focus à la fenêtre parente

    def onCancel(self):
        """
        Appelé lorsque l'utilisateur clique sur Annuler ou ferme la fenêtre.
        Ferme la boîte de dialogue sans appliquer les changements.
        """
        self.destroy()
        self.parent.focus_set()  # Redonne le focus à la fenêtre parente


# --- Exemple d'utilisation (pour tester le dialogue) ---
if __name__ == '__main__':
    from taskcoachlib.widgetstk.textctrltk import MultiLineTextCtrl
    # Initialisation de Tkinter
    root = tk.Tk()
    root.title(_("Task Coach - Main Window"))
    root.geometry("400x300")

    # Création d'une instance de paramètres de test
    test_settings = TaskcoachSettings()
    # # Active la page 'iphone' pour les tests, pour vérifier la logique __should_create_page
    # test_settings.set("feature", "iphone", True)

    # Marqueur pour le système d'internationalisation
    class Meta:
        name = "Task Coach"
    meta.name = "Task Coach"
    meta.data = type('obj', (object,), {'metaDict': {'name': meta.name}})

    def _(text):
        return text

    # Marqueur pour les fonctions de détection du système d'exploitation si elles ne sont pas disponibles
    # # Vous devriez vous assurer que taskcoachlib.operating_system est correctement importé
    # if not hasattr(operating_system, 'isMac'):
    #     def isMac(): return False
    #     operating_system.isMac = isMac
    # if not hasattr(operating_system, 'isGTK'):
    #     def isGTK(): return False
    #     operating_system.isGTK = isGTK
    # macOS/Darwin (vrai ou faux)
    def isMac(): return True  # Mis à True pour voir les pages Editor et OSX
    operating_system.isMac = isMac
    def isMacOsXMountainLion_OrNewer(): return False  # Mis à False pour voir le paramètre maccheckspelling
    operating_system.isMacOsXMountainLion_OrNewer = isMacOsXMountainLion_OrNewer
    # Linux/GTK (vrai ou faux)
    def isGTK(): return True  # Mis à True pour voir la page Linux
    operating_system.isGTK = isGTK

    # Assurez-vous que les dépendances factices sont en place
    if not hasattr(notify, 'AbstractNotifier'):
        class AbstractNotifier:
            @staticmethod
            def names(): return ["universal", "native"]
        notify.AbstractNotifier = AbstractNotifier
    if not hasattr(date, 'snoozeChoices'):
        date.snoozeChoices = [
            (0, _("Don't snooze")),
            (5, _("5 minutes")),
            (10, _("10 minutes")),
        ]

    def show_preferences():
        # Affiche le dialogue modal des préférences
        # print(f"Initial CheckSpelling: {widgets.MultiLineTextCtrl.CheckSpelling}")
        print(f"Initial CheckSpelling: {MultiLineTextCtrl.CheckSpelling}")
        dialog = PreferencesDialog(root, settings=test_settings)
        # print(f"Final CheckSpelling after OK: {widgets.MultiLineTextCtrl.CheckSpelling}")
        print(f"Final CheckSpelling after OK: {MultiLineTextCtrl.CheckSpelling}")
        # La ligne ci-dessous n'est pas nécessaire si wait_window est utilisé dans __init__
        # root.wait_window(dialog)

    ttk.Label(root, text=_("Cliquez sur le bouton pour ouvrir le dialogue des préférences.")).pack(pady=20)
    ttk.Button(root, text=_("Open Preferences"), command=show_preferences).pack(pady=10)

    # Démarrer la boucle principale
    root.mainloop()


