# L'objectif est de convertir le fichier csvimport.py pour qu'il utilise Tkinter
# au lieu de wxPython, en tirant parti des widgets Tkinter existants et
# en adaptant la logique de gestion de l'interface.
# Après avoir examiné les fichiers uicommand.py et csvimport.py,
# je peux confirmer que csvimport.py utilise intensivement wxPython
# pour la création de l'interface utilisateur,
# la gestion des événements et l'affichage des données dans une grille.
# Voici une approche pour convertir csvimport.py en utilisant Tkinter :
# 1. Remplacer les widgets wxPython par leurs équivalents Tkinter
#
# wx.Choice → tkinter.ttk.Combobox ou tkinter.OptionMenu
# wx.RadioButton → tkinter.Radiobutton wx.TextCtrl → tkinter.Entry
# wx.CheckBox → tkinter.Checkbutton
# wx.grid.Grid → tkinter.ttk.Treeview (pour un affichage tabulaire plus simple)
# ou une librairie externe comme tkintertable si vous avez besoin d'un contrôle
# de grille plus avancé
# wx.wizard.Wizard et wx.wizard.WizardPageSimple → Il n'y a pas d'équivalent direct.
# Vous devrez utiliser tkinter.Toplevel pour créer une fenêtre de dialogue et
# gérer la navigation entre les "pages" avec des boutons et des frames.
#
# 2. Adapter la structure de l'interface et la gestion du layout
#
# wx.BoxSizer → tkinter.Frame et les gestionnaires de géométrie pack, grid ou place
# wx.FlexGridSizer → tkinter.Frame et le gestionnaire de géométrie grid avec
# configuration des poids pour obtenir un comportement flexible
# Utiliser des tkinter.Label pour remplacer wx.StaticText

# 3. Convertir la gestion des événements
#
# wx.EVT_CHOICE → combobox.bind("<<ComboboxSelected>>", callback) ou optionmenu.bind("<Configure>", callback)
# wx.EVT_CHECKBOX → checkbutton.bind("<ButtonRelease-1>", callback)
# wx.EVT_RADIOBUTTON → radiobutton.bind("<ButtonRelease-1>", callback)
# wx.EVT_TEXT → entry.bind("<KeyRelease>", callback)
# wx.EVT_WIZARD_PAGE_CHANGING et wx.EVT_WIZARD_PAGE_CHANGED → Gérer la logique
# de navigation du wizard manuellement en utilisant des fonctions callback
# sur les boutons "Suivant" et "Précédent" de votre fenêtre Tkinter

# 4. Adapter la lecture et l'affichage du CSV
#
# Le code utilise csv.reader pour lire le fichier CSV. Cela peut être conservé,
# mais il faut s'assurer que l'ouverture du fichier et la gestion de l'encoding
# sont compatibles avec Tkinter.
# Adapter la logique d'affichage dans la grille Tkinter (Treeview ou autre)
# pour afficher les données correctement.
#
# Points spécifiques et adaptation du code existant :
#
#
# Classe CSVDialect : Cette classe peut être conservée car elle définit
#                     simplement le dialecte CSV utilisé par le csv.reader.
#
#
# Classe CSVImportOptionsPage : C'est ici que la majeure partie du travail de
#                               conversion doit être effectuée.
#                               Il faut remplacer tous les widgets wxPython
#                               par leurs équivalents Tkinter et
#                               adapter le layout en conséquence.
#                               La gestion des événements devra également être adaptée.
#                               La logique de détection de l'encoding (chardet) peut être conservée.
#
#
# Classe CSVImportMappingPage : Comme pour CSVImportOptionsPage,
#                               il faut remplacer les widgets wxPython par
#                               leurs équivalents Tkinter et
#                               adapter le layout et la gestion des événements.
#
#
# Classe CSVImportWizard : Il faut remplacer wx.wizard.Wizard par une fenêtre
#                          tkinter.Toplevel et gérer la navigation entre les
#                          "pages" manuellement.
#                          Les événements wx.EVT_WIZARD_PAGE_CHANGING et
#                          wx.EVT_WIZARD_PAGE_CHANGED doivent être remplacés par
#                          une logique de contrôle de la navigation basée sur
#                          des fonctions appelées lors des clics sur les
#                          boutons "Suivant" et "Précédent".
#

# wx.wizard.Wizard ne peut pas être directement remplacé par tkinter.simpledialog.Dialog
# ou tkinter.commondialog.Dialog pour les raisons suivantes :
#
#
# Fonctionnalité et complexité : wx.wizard.Wizard est conçu pour créer des
#                                interfaces de type assistant,
#                                qui guident l'utilisateur à travers une série
#                                d'étapes ou de pages.
#                                Il gère la navigation entre ces pages,
#                                les événements liés au changement de page,
#                                et offre une structure pour organiser des
#                                tâches complexes en étapes plus petites.
#                                tkinter.simpledialog.Dialog et
#                                tkinter.commondialog.Dialog sont conçus pour
#                                des interactions plus simples,
#                                comme demander une seule valeur à l'utilisateur
#                                (chaîne, entier, etc.) ou
#                                ouvrir une boîte de dialogue standard pour
#                                choisir un fichier ou une couleur.
#
#
# Structure et contrôle : Un wx.wizard.Wizard est une fenêtre modale contenant
#                         plusieurs pages, chacune pouvant avoir ses propres
#                         widgets et sa propre logique.
#                         La navigation est gérée par des boutons "Suivant",
#                         "Précédent" et "Annuler".
#                         Avec tkinter.simpledialog.Dialog ou
#                         tkinter.commondialog.Dialog,
#                         vous avez beaucoup moins de contrôle
#                         sur la structure de la boîte de dialogue
#                         et la séquence des interactions.
#
#
# Alternatives Tkinter : Pour recréer un assistant avec Tkinter,
#                        il est plus approprié d'utiliser une fenêtre tkinter.Toplevel
#                        et d'y organiser plusieurs tkinter.Frame,
#                        chacun représentant une page de l'assistant.
#                        La navigation entre les pages peut être gérée
#                        manuellement avec des boutons et
#                        des fonctions qui affichent ou
#                        masquent les frames appropriés.
#
#
# En résumé, tkinter.simpledialog.Dialog et tkinter.commondialog.Dialog sont
# conçus pour des tâches simples, tandis que wx.wizard.Wizard est un outil
# plus puissant pour créer des interfaces complexes à plusieurs étapes.
# Pour migrer un wx.wizard.Wizard vers Tkinter,
# il faut recréer la structure de l'assistant manuellement
# en utilisant des Toplevel et des Frame.
#
# Exemple de conversion d'un widget :
# Ancien code (wxPython)
# self.delimiter = wx.Choice(self, wx.ID_ANY)
# self.delimiter.Append(_('Comma'))
# self.delimiter.Append(_('Tab'))
# self.delimiter.SetSelection(0)
#
# # Nouveau code (Tkinter)
# self.delimiter = ttk.Combobox(self, values=[_('Comma'), _('Tab')])
# self.delimiter.set(_('Comma')) # Définit la valeur par défaut
# Gestion des dépendances
# Assurez-vous d'importer les modules Tkinter nécessaires :
# import tkinter as tk
# from tkinter import ttk
# from tkinter import messagebox

# Ce processus nécessitera une réécriture significative du code,
# mais en suivant cette approche étape par étape,
# vous devriez être en mesure de convertir csvimport.py pour
# qu'il fonctionne avec Tkinter.

# Explications des changements :
#
#
# wx.Panel → tk.Frame : wx.Panel est l'équivalent de tk.Frame en Tkinter.
#                       Il sert de conteneur pour les autres widgets.
#
#
# wx.RadioButton → tk.Radiobutton : wx.RadioButton est remplacé par tk.Radiobutton.
#                                   Il est important de noter que les Radiobutton
#                                   Tkinter nécessitent une value associée
#                                   à chaque bouton et une variable partagée
#                                   (généralement un tk.IntVar ou tk.StringVar)
#                                   pour stocker la valeur sélectionnée.
#                                   Ici, j'ai simplifié en utilisant value=1 et value=2,
#                                   mais dans votre code,
#                                   vous devrez probablement utiliser une variable Tkinter
#                                   pour récupérer la valeur sélectionnée.
#                                   J'ai utilisé self.doubleQuote.invoke()
#                                   pour simuler un click et sélectionner
#                                   le bouton par défaut.
#
#
# wx.TextCtrl → tk.Entry : wx.TextCtrl est remplacé par tk.Entry.
#                          La taille est gérée par l'attribut width.
#                          Enable(False) est remplacé par config(state='disabled')
#                          et SetMaxLength(1) par config(maxlength=1).
#                          Il faut utiliser insert(0, '\\')
#                          pour insérer la valeur par défaut.
#
#
# Enable(False) et Enable(True): En Tkinter, on utilise widget.config(state='disabled')
#                                pour désactiver un widget et widget.config(state='normal')
#                                pour l'activer.
#
#
# Gestion des événements pour activer/désactiver escapeChar :
#   J'ai ajouté des commandes aux boutons radio pour activer ou désactiver
#   le champ de texte escapeChar en fonction de la sélection.
#
#
# Positionnement des widgets : J'ai utilisé le gestionnaire de géométrie grid
#                              pour positionner les widgets dans le quotePanel.
#                              Vous pouvez ajuster les options row, column et
#                              sticky pour obtenir le layout souhaité.
#                              sticky="w" aligne les widgets à gauche.
#
#
# Points importants :
#
# N'oubliez pas d'importer les modules tkinter et tkinter.ttk au début de votre fichier.
# Adaptez le positionnement des widgets en utilisant pack, grid ou place selon vos besoins.
# Si vous avez besoin de récupérer la valeur du bouton radio sélectionné,
# utilisez une variable Tkinter (par exemple, tk.IntVar)
# et associez-la aux boutons radio avec l'option variable.

# Vous avez bien analysé la tâche à accomplir en identifiant les principaux défis
# de la migration de wxPython vers Tkinter.
# L'approche que vous avez définie est tout à fait pertinente.
#
# Voici la conversion de la méthode __init__ pour la classe CSVImportOptionsPage.
# J'ai remplacé les widgets wxPython par leurs équivalents Tkinter et
# adapté la structure de l'interface en utilisant les gestionnaires de géométrie grid et pack.

# J'ai effectué les modifications suivantes pour la conversion de __init__ :
#
#     J'ai remplacé wx.Choice par ttk.Combobox pour les listes déroulantes.
#
#     J'ai utilisé ttk.Radiobutton et une StringVar pour gérer le groupe de boutons radio.
#
#     J'ai remplacé wx.TextCtrl par tk.Entry.
#
#     J'ai utilisé des tk.Frame pour les conteneurs et la gestion du layout.
#
#     J'ai remplacé wx.BoxSizer et wx.FlexGridSizer par les gestionnaires de géométrie grid et pack de Tkinter.
#
#     wx.grid.Grid a été remplacé par ttk.Treeview, qui est plus adapté pour afficher des données tabulaires simples. J'ai ajouté un exemple de on_option_changed pour vous montrer comment il peut mettre à jour la Treeview avec un aperçu du fichier CSV.
#
#     Les appels à wx.EVT_* ont été remplacés par des méthodes bind de Tkinter.

#  La méthode OnOptionChanged est au cœur de la logique de prévisualisation du fichier.
#  Voici une version complète et convertie de cette méthode, intégrée au fichier csvimporttk.py.
#
# J'ai analysé l'implémentation wxPython et j'ai adapté la logique en utilisant
# les fonctionnalités et les conventions de Tkinter, notamment :
#
#     Gestion de l'interface : La modification de l'état du champ de texte escapeChar
#     est gérée de manière dynamique via l'état de la variable Tkinter associée aux boutons radio.
#
#     Gestion du fichier : La lecture du fichier est simplifiée en utilisant
#     directement open() avec l'encodage détecté,
#     ce qui évite le recours à un fichier temporaire et résout les problèmes
#     d'encodage et de décodage qui étaient présents dans le code original.
#
#     Mise à jour de la grille : Les opérations de la grille wx.grid sont
#     remplacées par les méthodes équivalentes de ttk.Treeview pour effacer les données,
#     définir les en-têtes de colonne et insérer les lignes.

# Voici les modifications que j'ai apportées :
#
#     GetOptions(self) : J'ai adapté la méthode pour utiliser les méthodes de
#     Tkinter pour récupérer les valeurs des widgets, comme self.date.current()
#     pour la sélection de la date et self.importSelectedRowsOnly.instate(['selected'])
#     pour les cases à cocher. J'ai également remplacé self.GetSelectedRows()
#     qui n'existe pas encore dans le code.
#     J'ai aussi ajouté self.GetSelectedRows() dans la classe.
#
#     GetSelectedRows(self) : Cette méthode est une adaptation de la version wxPython
#     qui récupère les lignes sélectionnées dans le Treeview.
#     Contrairement à wx.grid, ttk.Treeview utilise une autre logique pour
#     la sélection multiple. J'ai donc réimplémenté la méthode en utilisant self.grid.selection().
#
#     CanGoNext(self) : J'ai adapté la logique de cette méthode pour la
#     structure du "wizard" que nous sommes en train de construire avec Tkinter.
#     Plutôt que de s'appuyer sur une méthode GetNext() qui n'existe pas,
#     elle renvoie simplement un booléen et un message,
#     comme dans la version originale.
#     La logique pour passer à la page suivante sera gérée dans la classe
#     CSVImportWizard que nous avons commencée.

# La classe CSVImportMappingPage est cruciale car elle permet à l'utilisateur
# d'associer les colonnes du fichier CSV aux attributs de Task Coach.
#
# J'ai analysé le code wxPython et je l'ai converti en utilisant les widgets
# Tkinter appropriés, tout en conservant la même logique.
# Voici les principales modifications :
#
#     Remplacement des widgets :
#
#         wx.ScrolledWindow a été remplacé par un tkinter.Canvas avec une
#         ttk.Scrollbar pour gérer le défilement.
#
#         wx.FlexGridSizer est converti en un tk.Frame avec le gestionnaire de géométrie grid.
#
#         wx.StaticText est remplacé par ttk.Label.
#
#         wx.Choice est remplacé par ttk.Combobox.
#
#     Logique de mappage : La logique de la méthode SetOptions a été réimplémentée
#     pour Tkinter. Elle efface le contenu précédent, crée une nouvelle grille
#     de widgets et la remplit avec les en-têtes de colonne du fichier CSV et
#     les menus déroulants pour le mappage.
#
#     Méthodes CanGoNext et GetOptions : J'ai converti la logique de ces méthodes
#     pour qu'elles fonctionnent avec les widgets Tkinter.

# Convertissons la classe CSVImportWizard pour qu'elle fonctionne avec Tkinter.
#
# Dans la version wxPython, le système de "wizard" (assistant) est géré de
# manière assez automatique via des événements et des méthodes dédiées comme
# SetNext() et RunWizard(). Pour Tkinter, il faut recréer cette logique manuellement.
#
# Voici les modifications que j'ai apportées :
#
#     Gestion des pages : Au lieu d'utiliser les méthodes de wx.wizard,
#     j'ai implémenté les méthodes show_prev() et show_next() dans la classe
#     CSVImportWizard. Elles gèrent l'affichage des pages en utilisant pack_forget()
#     pour masquer la page actuelle et pack() pour afficher la suivante.
#
#     Validation : La logique de validation CanGoNext() est directement
#     intégrée dans la méthode show_next(). Si la page actuelle ne peut pas
#     passer à la suivante, un message d'information s'affiche via tkinter.messagebox.showinfo.
#
#     Passage des options : La méthode show_next() est également responsable de
#     la transmission des options de la page des options à la page de mappage
#     en appelant self.mappingPage.SetOptions(self.optionsPage.GetOptions()).
#
#     Boutons et état : Les boutons "Précédent" et "Suivant" sont gérés
#     dynamiquement pour être activés ou désactivés en fonction de la page affichée.
#     Le bouton "Précédent" est désactivé sur la première page et activé sur la seconde.

# C'est une erreur subtile mais très révélatrice qui nous rapproche de la solution.
#
# Analyse de l'erreur
#
# L'erreur est la suivante : _csv.Error: "escapechar" must be a 1-character string.
#
# Cela signifie que le module Python csv n'accepte pas une chaîne de caractères
# vide ('') pour l'argument escapechar.
# Il attend soit une chaîne d'un seul caractère (par exemple '\'' ou '\t'),
# soit la valeur None si aucun caractère d'échappement n'est utilisé.
#
# Dans votre code, lorsque l'assistant se lance, le bouton radio "Escape with"
# n'est pas sélectionné. La logique de la méthode on_option_changed
# passe donc une chaîne vide ('') à la classe CSVDialect, ce qui est la cause du plantage.
#
# Correction
#
# J'ai mis à jour le code pour résoudre ce problème.
# J'ai modifié la méthode on_option_changed pour passer la valeur None
# au paramètre escapechar lorsque l'option "échappement" n'est pas sélectionnée.
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
import chardet
from io import open as file
from builtins import zip, range, next
from taskcoachlib import meta
from taskcoachlib.i18n import _
import tempfile
import sys


# La classe CSVDialect peut être conservée telle quelle, car elle ne dépend pas de l'interface utilisateur.
class CSVDialect(csv.Dialect):
    # def __init__(self, delimiter=',', quotechar='"', doublequote=True, escapechar=''):
    def __init__(self, delimiter=',', quotechar='"', doublequote=True, escapechar=None):
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.quoting = csv.QUOTE_MINIMAL
        self.lineterminator = '\r\n'
        self.doublequote = doublequote
        # Correction pour s'assurer que l'escapechar est None si une chaîne vide est passée.
        if escapechar == '':
            escapechar = None
        self.escapechar = escapechar

        csv.Dialect.__init__(self)


# Conversion de la classe CSVImportOptionsPage
# class CSVImportOptionsPage(tk.Toplevel):
class CSVImportOptionsPage(tk.Frame):
    def __init__(self, parent, filename, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Utilisation de ttk.Combobox pour remplacer wx.Choice
        # self.delimiter = ttk.Combobox(self, values=[_('Comma'), _('Tab'), _('Space'), _('Colon'), _('Semicolon'), _('Pipe')])
        self.delimiter = ttk.Combobox(self, state="readonly", values=[_('Comma'), _('Tab'), _('Space'), _('Colon'), _('Semicolon'), _('Pipe')])
        # self.delimiter.set(_('Comma'))  # Définit la valeur par défaut
        self.delimiter.current(0)

        # self.date = ttk.Combobox(self, values=[_('DD/MM (day first)'), _('MM/DD (month first)')])
        self.date = ttk.Combobox(self, state="readonly", values=[_('DD/MM (day first)'), _('MM/DD (month first)')])
        # self.date.set(_('DD/MM (day first)'))
        self.date.current(0)

        # self.quoteChar = ttk.Combobox(self, values=[_('Simple quote'), _('Double quote')])
        self.quoteChar = ttk.Combobox(self, state="readonly", values=[_('Simple quote'), _('Double quote')])
        # self.quoteChar.set(_('Double quote'))
        self.quoteChar.current(1)

        # Utilisation de tk.Frame pour remplacer wx.Panel
        # remplacement de quotePanel par quoteFrame pour être raccord avec tkinter
        self.quoteFrame = ttk.Frame(self)
        self.quote_var = tk.StringVar(value='double')
        # self.doubleQuote = ttk.Radiobutton(self.quoteFrame, text=_('Double it'), value=1)  # Ajout de value
        self.doubleQuote = ttk.Radiobutton(self.quoteFrame, text=_('Double it'), variable=self.quote_var, value='double')
        # self.doubleQuote.invoke()  # Sélectionne le radiobutton par défaut
        # self.escapeQuote = tk.Radiobutton(self.quoteFrame, text=_('Escape with'), value=2)  # Ajout de value
        self.escapeQuote = ttk.Radiobutton(self.quoteFrame, text=_('Escape with'), variable=self.quote_var, value='escape')
        # self.escapeChar = tk.Entry(self.quoteFrame, width=3)  # Size est géré par width dans Tkinter
        self.escapeChar = tk.Entry(self.quoteFrame, width=5)
        self.escapeChar.insert(0, '\\')  # Définit la valeur initiale
        self.escapeChar.config(state='disabled')  # Remplace Enable(False)
        # self.escapeChar.config(maxlength=1)  # Remplace SetMaxLength(1)

        # Placement des Radiobuttons et Entry dans le quotePanel avec pack
        self.doubleQuote.pack(side=tk.LEFT, padx=3)
        self.escapeQuote.pack(side=tk.LEFT, padx=3)
        self.escapeChar.pack(side=tk.LEFT, padx=3)

        self.importSelectedRowsOnly = ttk.Checkbutton(self, text=_('Import only the selected rows'))
        self.hasHeaders = ttk.Checkbutton(self, text=_('First line describes fields'))
        self.hasHeaders.state(['selected'])

        # Remplacement de wx.grid.Grid par ttk.Treeview
        # NOTE : J'ai renommé cette variable de `self.grid` à `self.treeview`
        # pour éviter un conflit de noms avec la méthode `.grid()` du widget.
        columns = ('col1',)
        # self.grid = ttk.Treeview(self, columns=columns, show='headings')
        # self.grid.heading('col1', text='Preview')  # En attendant de remplir les en-têtes
        self.treeview = ttk.Treeview(self, columns=columns, show='headings')
        self.treeview.heading('col1', text='Preview') # En attendant de remplir les en-têtes

        # Configuration du layout avec grid pour tous les widgets
        # grid_frame = tk.Frame(self)
        # grid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=3)

        row = 0
        # tk.Label(grid_frame, text=_('Delimiter')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        tk.Label(self, text=_('Delimiter')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        self.delimiter.grid(row=row, column=1, sticky=tk.EW, padx=3, pady=3)
        row += 1

        # tk.Label(grid_frame, text=_('Date format')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        tk.Label(self, text=_('Date format')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        self.date.grid(row=row, column=1, sticky=tk.EW, padx=3, pady=3)
        row += 1

        # tk.Label(grid_frame, text=_('Quote character')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        tk.Label(self, text=_('Quote character')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        self.quoteChar.grid(row=row, column=1, sticky=tk.EW, padx=3, pady=3)
        row += 1

        # tk.Label(grid_frame, text=_('Escape quote')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        tk.Label(self, text=_('Escape quote')).grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
        self.quoteFrame.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)
        row += 1

        self.importSelectedRowsOnly.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=3)
        row += 1

        self.hasHeaders.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=3)
        row += 1

        # grid_frame.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # self.grid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=3, pady=3)
        # Remplacement de pack() par grid() pour le Treeview
        # self.grid.grid(row=row, column=0, columnspan=2, sticky=tk.NSEW, padx=3, pady=3)
        self.treeview.grid(row=row, column=0, columnspan=2, sticky=tk.NSEW, padx=3, pady=3)
        self.grid_rowconfigure(row, weight=1)  # Permet au Treeview de s'étendre verticalement

        self.headers = None

        self.filename = filename

        if self.filename:
            try:
                with open(self.filename, 'rb') as f:
                    self.encoding = chardet.detect(f.read())['encoding']
            except FileNotFoundError:
                self.encoding = 'utf-8'  # Fallback
            except Exception as e:
                print(f"Error detecting encoding: {e}")
                self.encoding = 'utf-8'

        self.on_option_changed()

        # Bindings des événements
        self.delimiter.bind("<<ComboboxSelected>>", self.on_option_changed)
        self.date.bind("<<ComboboxSelected>>", self.on_option_changed)
        self.quoteChar.bind("<<ComboboxSelected>>", self.on_option_changed)
        self.importSelectedRowsOnly.bind("<ButtonRelease-1>", self.on_option_changed)
        self.hasHeaders.bind("<ButtonRelease-1>", self.on_option_changed)
        self.doubleQuote.bind("<ButtonRelease-1>", self.on_option_changed)
        self.escapeQuote.bind("<ButtonRelease-1>", self.on_option_changed)
        self.escapeChar.bind("<KeyRelease>", self.on_option_changed)

    def on_option_changed(self, event=None):
        if self.quote_var.get() == 'escape':
            self.escapeChar.config(state='normal')
        else:
            self.escapeChar.config(state='disabled')
        # ... Reste de la logique de OnOptionChanged à implémenter ici
        # Je vais ajouter une implémentation de base pour la démo

        # Effacer l'ancienne grille
        # for item in self.grid.get_children():
        for item in self.treeview.get_children():
            # self.grid.delete(item)
            self.treeview.delete(item)

        if not self.filename:
            return

        delimiter_map = {0: ',', 1: '\t', 2: ' ', 3: ':', 4: ';', 5: '|'}
        quotechar_map = {0: "'", 1: '"'}

        # delimiter = {0: ',', 1: '\t', 2: ' ', 3: ':', 4: ';', 5: '|'}[self.delimiter.current()]
        delimiter = delimiter_map[self.delimiter.current()]
        # quotechar = {0: "'", 1: '"'}[self.quoteChar.current()]
        quotechar = quotechar_map[self.quoteChar.current()]
        doublequote = (self.quote_var.get() == 'double')
        # escapechar = self.escapeChar.get() if not doublequote else ''
        escapechar = self.escapeChar.get() if self.escapeChar['state'] == 'normal' else ''

        self.dialect = CSVDialect(
            delimiter=delimiter,
            quotechar=quotechar,
            doublequote=doublequote,
            escapechar=escapechar
        )

        try:
            with open(self.filename, 'r', encoding=self.encoding, errors='ignore') as f:
                reader = csv.reader(f, dialect=self.dialect)

                # Lire et afficher les 5 premières lignes
                preview_data = []
                for i, row in enumerate(reader):
                    if i >= 5:  # On lit seulement les 5 premières lignes pour l'aperçu
                        break
                    preview_data.append(row)

                if self.hasHeaders.instate(['selected']):
                    self.headers = preview_data.pop(0) if preview_data else []
                else:
                    max_cols = max(len(row) for row in preview_data) if preview_data else 0
                    self.headers = [_('Field #%d') % (i+1) for i in range(max_cols)]

                # Mise à jour des colonnes de la Treeview
                # self.grid['columns'] = self.headers
                self.treeview['columns'] = self.headers
                # for col in self.headers:
                #     self.grid.heading(col, text=col)
                for col_name in self.headers:
                    # self.grid.heading(col_name, text=col_name)
                    self.treeview.heading(col_name, text=col_name)
                    # self.grid.column(col_name, width=100)
                    self.treeview.column(col_name, width=100)
                # self.grid.column('#0', width=0, stretch=tk.NO)  # Cacher la colonne par défaut
                self.treeview.column('#0', width=0, stretch=tk.NO)  # Cacher la colonne par défaut

                # Remplir la grille avec les données d'aperçu
                for row_data in preview_data:
                    # self.grid.insert('', 'end', values=row_data)
                    self.treeview.insert('', 'end', values=row_data)

        except Exception as e:
            print(f"Error reading CSV: {e}")

    # Les méthodes CanGoNext, GetOptions, et GetSelectedRows devront être adaptées
    # pour le contexte de Tkinter.

    def GetOptions(self):
        return dict(dialect=self.dialect,
                    dayfirst=self.date.current() == 0,
                    importSelectedRowsOnly=self.importSelectedRowsOnly.instate(['selected']),
                    selectedRows=self.GetSelectedRows(),
                    hasHeaders=self.hasHeaders.instate(['selected']),
                    filename=self.filename,
                    encoding=self.encoding,
                    fields=self.headers)

    def GetSelectedRows(self):
        # Treeview returns item IDs, we need to map them back to row indices
        # selected_item_ids = self.grid.selection()
        selected_item_ids = self.treeview.selection()
        # all_item_ids = self.grid.get_children()
        all_item_ids = self.treeview.get_children()
        selected_rows = [all_item_ids.index(item_id) for item_id in selected_item_ids]
        return selected_rows

    def CanGoNext(self):
        if self.filename is not None:
            # We will handle the setting of options in the main wizard class
            return True, None
        return False, _('Please select a file.')


# Placeholder pour le reste du code
class CSVImportMappingPage(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # (field name, multiple values allowed)
        self.fields = [
            (_('None'), True),
            (_('ID'), False),
            (_('Subject'), False),
            (_('Description'), True),
            (_('Category'), True),
            (_('Priority'), False),
            (_('Planned start Date'), False),
            (_('Due Date'), False),
            (_('Actual start Date'), False),
            (_('Completion Date'), False),
            (_('Reminder Date'), False),
            (_('Budget'), False),
            (_('Fixed fee'), False),
            (_('Hourly fee'), False),
            (_('Percent complete'), False),
        ]
        self.choices = []
        self.options = {}

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def SetOptions(self, options):
        self.options = options

        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.choices = []

        gsz = ttk.Frame(self.scrollable_frame)
        gsz.grid(row=0, column=0, sticky="ew")
        gsz.columnconfigure(1, weight=1)

        row = 0
        # ttk.Label(gsz, text=_('Column header in CSV file'), font='TkDefaultFont bold').grid(row=row, column=0, padx=5, pady=2, sticky='w')
        # ttk.Label(gsz, text=_('%s attribute') % meta.name, font='TkDefaultFont bold').grid(row=row, column=1, padx=5, pady=2, sticky='w')
        # Correction ici : Utilisation d'un tuple pour la police
        ttk.Label(gsz, text=_('Column header in CSV file'), font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0, padx=5, pady=2, sticky='w')
        ttk.Label(gsz, text=_('%s attribute') % meta.name, font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=1, padx=5, pady=2, sticky='w')
        row += 1

        tcFieldNames = [field[0] for field in self.fields]
        for fieldName in self.options.get('fields', []):
            ttk.Label(gsz, text=fieldName).grid(row=row, column=0, padx=5, pady=2, sticky='w')

            choice = ttk.Combobox(gsz, state="readonly", values=tcFieldNames)
            choice.set(tcFieldNames[self.findFieldName(fieldName, tcFieldNames)])
            self.choices.append(choice)
            choice.grid(row=row, column=1, padx=5, pady=2, sticky='ew')
            row += 1

    def findFieldName(self, fieldName, fieldNames):
        def fieldNameIndex(fieldName, fieldNames):
            try:
                return fieldNames.index(fieldName)
            except ValueError:
                return 0

        index = fieldNameIndex(fieldName, fieldNames)
        if index != 0:
            return index

        # Fallback to partial match if full name not found
        try:
            short_field_names = [name[:6] for name in fieldNames]
            return short_field_names.index(fieldName[:6])
        except (ValueError, IndexError):
            return 0


    def CanGoNext(self):
        wrongFields = []
        countNotNone = 0

        for index, (fieldName, canMultiple) in enumerate(self.fields):
            count = 0
            for choice in self.choices:
                if choice.get() == fieldName:
                    count += 1
            if choice.get() != _('None'):
                countNotNone += 1
            if count > 1 and not canMultiple:
                wrongFields.append(fieldName)

        if countNotNone == 0:
            return False, _('No field mapping.')

        if len(wrongFields) == 1:
            return False, _('The "%s" field cannot be selected several times.') % wrongFields[0]

        if len(wrongFields):
            return False, _('The fields %s cannot be selected several times.') % ', '.join(
                ['"%s"' % fieldName for fieldName in wrongFields])

        return True, None

    def GetOptions(self):
        options = dict(self.options)
        options['mappings'] = [choice.get() for choice in self.choices]
        return options


class CSVImportWizard(tk.Toplevel):
    def __init__(self, parent, filename, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Assistant d'import CSV")
        self.filename = filename
        self.transient(self.master)
        self.grab_set()

        # Créez un conteneur pour les pages
        self.page_container = tk.Frame(self)
        self.page_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        # self.optionsPage = CSVImportOptionsPage(self, filename)
        # self.mappingPage = CSVImportMappingPage(self)
        # Les pages sont des enfants du conteneur
        self.optionsPage = CSVImportOptionsPage(self.page_container, filename)
        self.mappingPage = CSVImportMappingPage(self.page_container)

        # Placez les pages dans le conteneur en utilisant la grille
        self.optionsPage.grid(row=0, column=0, sticky="nsew")
        self.mappingPage.grid(row=0, column=0, sticky="nsew")

        # Gérer la navigation manuellement
        self.current_page = self.optionsPage
        # self.current_page.pack(fill=tk.BOTH, expand=True)
        # self.current_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.current_page.tkraise()

        # Les boutons de navigation
        button_frame = tk.Frame(self)
        # button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.prev_button = ttk.Button(button_frame, text="Précédent", command=self.show_prev)
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.prev_button.config(state=tk.DISABLED)  # Désactivé par défaut sur la première page

        self.next_button = ttk.Button(button_frame, text="Suivant", command=self.show_next)
        self.next_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def show_prev(self):
        # Logique pour passer à la page précédente
        if self.current_page == self.mappingPage:
            # self.mappingPage.pack_forget()
            # self.optionsPage.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.current_page = self.optionsPage
            self.optionsPage.tkraise()
            self.prev_button.config(state=tk.DISABLED)

    def show_next(self):
        # Logique pour passer à la page suivante
        can_go_next, msg = self.current_page.CanGoNext()

        if not can_go_next:
            messagebox.showinfo(_('Information'), msg)
            return

        if self.current_page == self.optionsPage:
            options = self.optionsPage.GetOptions()
            self.mappingPage.SetOptions(options)

            # self.optionsPage.pack_forget()
            # self.mappingPage.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.current_page = self.mappingPage
            self.mappingPage.tkraise()
            self.prev_button.config(state=tk.NORMAL)
        # Add logic for mappingPage -> next page here...
        # Ajoutez la logique pour la page de mapping -> page suivante ici...

    def GetOptions(self):
        return self.mappingPage.GetOptions()


# J'ai mis à jour le code pour inclure une instance de CSVImportWizard
# dans une boucle principale Tkinter pour qu'il puisse être affiché et testé,
# car il s'agit d'une application de bureau.
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Taskcoach Importer")
    # root.withdraw()  # Cache la fenêtre principale

    # Créer un fichier CSV temporaire pour la démo
    test_csv_content = """Date,Subject,Description
    2023-01-01,Task 1,Description for task 1
    2023-01-02,Task 2,Description for task 2
    2023-01-03,Task 3,Description for task 3
    """

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
        tmp_file.write(test_csv_content)
        temp_csv_path = tmp_file.name

    # wiz = CSVImportWizard(filename=temp_csv_path)
    wiz = CSVImportWizard(root, filename=temp_csv_path)
    # wiz.grab_set()
    wiz.wait_window()  # Attend la fermeture de la fenêtre de l'assistant
    # root.mainloop()

    # Nettoyage du fichier temporaire
    import os
    os.remove(temp_csv_path)

    # Démarrer la boucle d'événements principale Tkinter
    root.mainloop()
