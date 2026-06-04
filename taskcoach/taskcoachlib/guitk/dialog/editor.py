# -*- coding: utf-8 -*-

"""
Task Coach - Votre gestionnaire de tâches amical
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2012 Nicola Chiapolini <nicola.chiapolini@physik.uzh.ch>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

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


Module `editor.py` - Gère les pages d'édition des objets dans Task Coach.

Ce module contient diverses classes pour représenter des pages d'édition pour différents
types d'objets (tâches, catégories, notes, etc.) dans Task Coach. Il fournit également
les mécanismes pour observer les changements sur ces objets et les refléter dans
l'interface utilisateur.
"""

# C'est un bon point de départ car il gère les boîtes de dialogue d'édition pour divers objets.
#
# Voici une première version convertie en utilisant le module tkinter et tkinter.ttk pour une apparence plus moderne. J'ai gardé les commentaires en français pour plus de clarté. Notez que j'ai dû simplifier certaines fonctionnalités de WxPython, car elles n'ont pas d'équivalent direct dans Tkinter. J'ai aussi ajouté des commentaires expliquant les choix de conception et les différences entre les deux frameworks.

# Ce code fournit un point de départ fonctionnel pour la migration. Il imite la structure de classes de votre fichier editor.py tout en utilisant les widgets et la logique de Tkinter.
#
# Points clés de la conversion :
#
#     Classes de dialogue : wx.Dialog est remplacé par tk.Toplevel pour créer une fenêtre de dialogue séparée.
#
#     Widgets : wx.Notebook est remplacé par ttk.Notebook. Les autres widgets comme wx.TextCtrl et wx.StaticText sont remplacés par ttk.Entry et ttk.Label.
#
#     Gestion des événements : Les liaisons Bind de wxPython sont remplacées par la méthode bind de Tkinter.
#
#     Structure de classe : L'approche modulaire avec les classes Page et Editor est maintenue, ce qui facilite la migration.

# En examinant votre fichier editortk.py, je vois que c'est un bon début de conversion, mais il y a plusieurs points importants à améliorer pour maintenir la fidélité avec l'architecture complexe d'editor.py. Voici mes observations :
# Points positifs
#
# La structure de base avec les classes Page et Editor est correcte
# L'utilisation de ttk.Notebook pour remplacer wx.Notebook est appropriée
# La gestion des événements avec bind suit la logique Tkinter
#
# Problèmes majeurs identifiés
# 1. Architecture simplifiée à l'excès
# Votre version actuelle ne capture pas la complexité de l'original :
# # Dans editor.py, il y a une hiérarchie complexe :
# class Page(patterns.Observer, widgets.BookPage):  # Héritage multiple
# class PageWithViewer(Page):  # Pages avec visualiseurs intégrés
# class EditBook(widgets.Notebook):  # Conteneur de pages avec gestion des perspectives
# 2. Gestion des objets de domaine
# L'original gère des collections d'items avec synchronisation :
# # editor.py
# def __init__(self, items, parent, settings, *args, **kwargs):
#     self.items = items  # Liste d'objets, pas un seul
#     self._subjectSync = attributesync.AttributeSync(...)
# Votre version ne gère qu'un seul item par page.
# 3. Pages manquantes
# L'original a de nombreuses pages spécialisées que vous n'avez pas encore converties :
#
# DatesPage, ProgressPage, BudgetPage
# CategoriesPage, NotesPage, AttachmentsPage
# Pages avec visualiseurs complexes
#
# Suggestions d'amélioration :
# Corrections architecturales importantes
# 1. Gestion des collections d'items
# # Au lieu de gérer un seul item par page
# self.items = items  # Liste d'objets comme dans l'original
# 2. Structure de pages plus fidèle
#
# Ajout de addEntry() pour gérer la mise en page
# Système de entries() pour retrouver les widgets
# Gestion des flags et options de croissance
#
# 3. Pages spécialisées complètes
#
# TaskSubjectPage avec gestion de priorité
# CategorySubjectPage avec sous-catégories exclusives
# AttachmentSubjectPage avec sélection de fichiers
#
# 4. EditBook fidèle à l'original
#
# Utilise ttk.Notebook correctement
# Gère les pages selon le type d'objet
# Support pour l'édition multiple conditionnelle
#
# Points restants à implémenter
# 1. Pages manquantes
# Vous devrez encore ajouter :
#
# DatesPage, ProgressPage, BudgetPage
# CategoriesPage, NotesPage, AttachmentsPage (avec visualiseurs)
# TaskAppearancePage
#
# 2. Synchronisation des données
# L'original utilise attributesync.AttributeSync. Vous devrez implémenter :
# class AttributeSync:
#     """Synchronise les widgets Tkinter avec les objets de domaine"""
#     def __init__(self, attr_name, widget, initial_value, items, command_class, event, event_type):
#         # Implémentation de la synchronisation
#         pass
# 3. Gestion des événements
# Remplacer le système patterns.Observer de l'original par les événements Tkinter.
# 4. Perspectives et configuration
# L'original sauvegarde la disposition des pages. Vous pourriez utiliser :
# def save_perspective(self):
#     """Sauvegarde l'état actuel de l'interface"""
#     pass
#

# Voici une approche pour convertir ces classes, en tenant compte des
# équivalents Tkinter et des défis potentiels :
#
# TaskAppearancePage :
#
# Objectif : Gérer l'apparence des tâches (couleur, police, icône).
# editor.py : Utilise wx.ColourDialog, wx.FontDialog, et des contrôles personnalisés (entry.ColorEntry, entry.FontEntry, entry.IconEntry).
# editortk.py : Implémentation de base définie.
# Conversion :
# Remplacer wx.ColourDialog par tk.colorchooser.askcolor.
# Remplacer wx.FontDialog par tk.fontchooser.askfont (peut nécessiter une installation séparée).
# Adapter ou recréer les contrôles personnalisés avec des widgets Tkinter standard (par exemple, ttk.Frame, ttk.Label, ttk.Entry, ttk.Button).
#
# DatesPage :
#
# Objectif : Éditer les dates liées aux tâches (début planifié, échéance, etc.).
# editor.py : ,  Utilise smartdatetimectrl (probablement un contrôle date/heure personnalisé de taskcoachlib).
# editortk.py : Non implémenté.
# Conversion :
#
# Rechercher un équivalent Tkinter pour smartdatetimectrl ou utiliser tkcalendar (nécessite une installation séparée) ou ttk.DateEntry.
# Gérer les options relatives de date/heure avec des menus déroulants ou des entrées Tkinter.
#
# ProgressPage :
#
# Objectif : Suivre et modifier l'avancement d'une tâche (pourcentage d'achèvement).
# editor.py : Utilise un contrôle personnalisé entry.PercentageEntry.
# editortk.py : Non implémenté.
# Conversion :
# Remplacer entry.PercentageEntry par un ttk.Scale (curseur) ou une combinaison de ttk.Entry et ttk.Spinbox.
#
# BudgetPage :
#
# Objectif : Gérer le budget alloué à une tâche (coûts prévus, dépenses réelles).
# editor.py : Utilise entry.TimeDeltaEntry et entry.AmountEntry (contrôles personnalisés).
# editortk.py : Non implémenté.
# Conversion :
#
# Remplacer entry.TimeDeltaEntry par une combinaison de ttk.Entry et de sélecteurs d'unité (jours, heures, minutes).
# Remplacer entry.AmountEntry par ttk.Entry avec validation d'entrée.
#
# PageWithViewer :
#
# Objectif : Classe de base pour les pages qui affichent un visualiseur (catégories, notes, pièces jointes, prérequis).
# editor.py : Agit comme une classe de base abstraite.
# editortk.py : Ne semble pas avoir cette notion, il faudra l'implémenter.
# Conversion :
# Créer une classe de base PageWithViewer en Tkinter qui gère la création et l'intégration d'un widget "visualiseur" (par exemple, un ttk.Treeview ou une zone de texte).
#
# EffortPage :
#
# Objectif : Gérer l'effort alloué à une tâche (suivi du temps).
# editor.py : Utilise EffortViewer (un contrôle personnalisé).
# editortk.py : Non implémenté.
# Conversion :
# Adapter EffortViewer en utilisant ttk.Treeview ou un autre widget d'affichage de liste Tkinter.
# Gérer les actions de suivi du temps avec des boutons et des mises à jour d'interface.
#
# LocalCategoryViewer, CategoriesPage :
#
# Objectif : Afficher et gérer les catégories associées à un objet.
# editor.py : Utilise BaseCategoryViewer et un wx.CheckListBox.
# editortk.py : Non implémenté.
# Conversion :
# Remplacer wx.CheckListBox par un ttk.Treeview avec des cases à cocher.
# Adapter la logique de BaseCategoryViewer pour Tkinter.
#
# LocalAttachmentViewer, AttachmentsPage :
#
# Objectif : Afficher et gérer les pièces jointes associées à un objet.
# editor.py : Utilise AttachmentViewer (un contrôle personnalisé).
# editortk.py : Non implémenté.
# Conversion :
# Adapter AttachmentViewer en utilisant ttk.Treeview ou un autre widget d'affichage de liste Tkinter.
# Gérer les actions d'ouverture, de suppression et de modification des pièces jointes.
#
# LocalNoteViewer, NotesPage :
#
# Objectif : Afficher et gérer les notes associées à un objet.
# editor.py : Utilise BaseNoteViewer (un contrôle personnalisé).
# editortk.py : Non implémenté.
# Conversion :
# Adapter BaseNoteViewer en utilisant tk.Text ou un autre widget d'affichage de texte Tkinter.
# Gérer les actions d'ajout, de suppression et de modification des notes.
#
# LocalPrerequisiteViewer, PrerequisitesPage :
#
# Objectif : Afficher et gérer les prérequis d'une tâche.
# editor.py : Utilise CheckableTaskViewer (un contrôle personnalisé).
# editortk.py : Non implémenté.
# Conversion :
# Remplacer CheckableTaskViewer par un ttk.Treeview avec des cases à cocher.
#
# EffortEditBook :
#
# Objectif : Fournir une interface d'édition pour les entrées d'effort.
# editor.py : Gère la sélection des tâches, les heures de début et de fin, et la description de l'effort.
# editortk.py : Non implémenté.
# Conversion :
# Créer une classe EffortEditBook en Tkinter qui utilise les widgets appropriés
# (par exemple, ttk.Combobox pour la sélection des tâches,
# ttk.Entry pour les heures de début et de fin,
# tk.Text pour la description).

# Puisque nous n'avons pas la version Tkinter complète de tous les widgets personnalisés (ColorEntry, FontEntry, IconEntry) ni du système de synchronisation (AttributeSync), je vais créer des versions simplifiées (mocks) en Tkinter pour ces contrôles personnalisés. Cela permettra à la page d'être fonctionnelle et de refléter la structure de l'original en wxPython.
#
# Pour que la nouvelle page fonctionne, nous devons également ajouter
# une implémentation simplifiée de la méthode addEntry
# (qui gère la mise en page en grille) à la classe de base Page de editortk.py,
# si elle n'existe pas déjà. Je vais supposer que vous avez une classe Page
# basée sur ttk.Frame et que je dois ajouter les utilitaires.


import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import colorchooser, font as tk_font  # Ajout pour l'apparence
from tkinter import simpledialog, messagebox  # (Utile pour les mocks)
from abc import ABC, abstractmethod
from pubsub import pub

from taskcoachlib.help.balloontipstk import BalloonTipManager
from taskcoachlib.i18n import _
from taskcoachlib import (
    meta,
    widgetstk,
    patterns,
    command,
    operating_system,
    render,
)
from taskcoachlib.guitk.dialog import entrytk as entry
from taskcoachlib.guitk.dialog import attributesynctk as attributesync
from taskcoachlib.guitk import viewer, newidtk, windowdimensionstrackertk
from taskcoachlib.guitk.uicommand import uicommandtk
from taskcoachlib.guitk.viewer import efforttk, categorytk, tasktk
from taskcoachlib.guitk.viewer.efforttk import Effortviewer
from taskcoachlib.guitk.viewer.categorytk import (
    BaseCategoryViewer,
)  # Crée une boucle

# L'import devient local dans LocalCategoryViewer
from taskcoachlib.guitk.viewer.attachmenttk import Attachmentviewer
from taskcoachlib.guitk.viewer.notetk import BaseNoteViewer
from taskcoachlib.guitk.viewer.tasktk import CheckableTaskViewer

# ImportError: cannot import name 'CheckableTaskViewer' from partially initialized module 'taskcoachlib.guitk.viewer.tasktk' (most likely due to a circular import)
from taskcoachlib.guitk.newidtk import IdProvider
from taskcoachlib.domain import task, date, note, attachment

# from taskcoachlib.widgetstk import notebooktk, textctrltk, dialogtk, datectrltk
from taskcoachlib.widgetstk import textctrltk, dialogtk, datectrltk
from taskcoachlib.widgetstk.notebooktk import BookPage  # circular import !

log = logging.getLogger(__name__)

# Note sur la migration :
# Tkinter ne dispose pas des concepts de "SizedDialog", "Notebook" ou "EditBook"
# de manière native. Nous utilisons des widgets standard de Tkinter et des
# classes pour imiter ces fonctionnalités.
# Le modèle de gestion d'événements est basé sur les `bind` de Tkinter,
# et non sur les `Bind` de wxPython.


# class Page(ttk.Frame):
class Page(patterns.Observer, widgetstk.notebooktk.BookPage):
    """
    Classe de base pour les pages d'édition.
    Équivalent à la classe Page de editor.py mais utilisant Tkinter.
    Dans Tkinter, une "page" est simplement un Frame qui sera placé
    dans un widget Notebook.
    """

    pageName = "base"
    pageTitle = "Base Page"
    pageIcon = None
    columns = 2  # Par défaut, deux colonnes pour l'édition

    # def __init__(self, parent, *args, **kwargs):
    def __init__(self, items, parent, *args, **kwargs):
        """
        Initialise la page avec les éléments à éditer.

        Args :
            items (list) : Liste des objets de domaine à éditer
            parent (tk.Widget) : Le widget parent de cette page
        """
        super().__init__(parent, *args, **kwargs)
        self.items = items
        self.entries_dict = {}
        self.__observers = []

        # Configuration du grid pour une mise en page en colonnes
        for i in range(self.columns):
            self.columnconfigure(i, weight=1 if i % 2 == 1 else 0)

    def selected(self):
        """
        Méthode appelée lorsque la page est sélectionnée.
        """
        pass

    def addEntry(self, label, widget, row=None, flags=None, growable=False):
        """
        Ajoute une entrée (label + widget) à la page.

        Args:
            label (str): Texte du label
            widget (tk.Widget): Widget de saisie
            row (int): Ligne où placer l'entrée (auto si None)
            flags (list): Flags de placement (ignorés en Tkinter)
            growable (bool): Si True, le widget peut s'étendre
        """
        if row is None:
            row = len(self.entries_dict)

        if label:
            label_widget = ttk.Label(self, text=label)
            label_widget.grid(row=row, column=0, sticky="w", padx=5, pady=2)

        sticky = "ew" if growable else "w"
        widget.grid(row=row, column=1, sticky=sticky, padx=5, pady=2)

        # Stockage pour retrouver les widgets
        if label:
            self.entries_dict[label.lower().replace(" ", "_")] = widget

    def addEntries(self):
        """
        Ajoute les entrées de la page.
        À implémenter dans les sous-classes.
        """
        pass

    def entries(self):
        """
        Retourne un dictionnaire des entrées de cette page.
        """
        return self.entries_dict

    def setFocusOnEntry(self, entry_name):
        """
        Définit le focus sur une entrée spécifique.
        """
        if entry_name in self.entries_dict:
            self.entries_dict[entry_name].focus_set()

    def close(self):
        """
        Ferme la page et libère les ressources.
        """
        # pass
        # # code wx :
        self.removeInstance()
        for entry in list(self.entries().values()):
            if isinstance(entry, widgetstk.datectrltk.DateTimeCtrl):
                entry.Cleanup()


class SubjectPage(Page):
    """
    Gère l'édition du sujet d'un objet.

    Page d'édition pour modifier le sujet d'un objet dans Task Coach.
    """

    # pageTitle = _("Subject")
    pageName = "subject"
    pageTitle = _("Description")
    pageIcon = "pencil_icon"

    # def __init__(self, parent, item, *args, **kwargs):
    def __init__(self, items, parent, settings, *args, **kwargs):
        self._settings = settings
        # super().__init__(parent, *args, **kwargs)
        super().__init__(items, parent, *args, **kwargs)
        # self.item = item
        self._modificationTextEntry = None
        self._descriptionSync = None
        self._subjectSync = None
        self.addEntries()
        self.subject_entry = None
        self._descriptionEntry = None
        self._settings = settings
        #
        # # Le widget de sujet (similaire à wx.TextCtrl)
        # self.subject_label = ttk.Label(self, text=_("Subject:"))
        # self.subject_label.pack(side="left", padx=5, pady=5)
        # self.subject_entry = ttk.Entry(self)
        # self.subject_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        #
        # # Mettre à jour la valeur initiale
        # self.subject_entry.insert(0, self.item.subject())
        #
        # # Lier l'événement de modification pour mettre à jour le titre de la fenêtre.
        # # Le concept de "on_subject_changed" est géré ici par la liaison.
        # self.subject_entry.bind('<KeyRelease>', self.on_subject_changed)
        # Ajouter les champs d'entrée (comme les textCtrl pour le sujet et la description) :
        self.addEntries()

    def addEntries(self):
        """
        Ajoute les champs d'entrée spécifiques pour l'édition du sujet.
        """
        # Ajoute les widgets pour éditer le sujet.
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addSubjectEntry(self):
        """
        Ajoute un champ de saisie pour le sujet.
        """
        current_subject = (
            self.items[0].subject()
            if len(self.items) == 1
            else _("Edit to change all subjects")
        )
        try:
            self.subject_entry = widgetstk.textctrltk.SingleLineTextCtrl(
                self, current_subject
            )
            self._subjectSync = attributesync.AttributeSync(
                "subject",
                self.subject_entry,
                current_subject,
                self.items,
                command.EditSubjectCommand,
                "<FocusOut>",
                self.items[0].subjectChangedEventType(),
            )
            # TODO: Ajoutez un commentaire pour expliquer le but de ce code:
            self.addEntry(  # de BookPage !
                _("Subject"),  # Ceci devient controls[0] (le texte du libellé)
                self.subject_entry,  # Ceci devient controls[1] (le wx.TextCtrl)
            )
        except:
            self.subject_entry = ttk.Entry(self)
            self.subject_entry.insert(0, current_subject)

            # Binding pour la synchronisation (simplifié)
            self.subject_entry.bind("<KeyRelease>", self.on_subject_changed)

            self.addEntry(_("Subject"), self.subject_entry)
            self.entries_dict["subject"] = self.subject_entry
            self.entries_dict["firstEntry"] = self.subject_entry

    def __modification_text(self):
        # def __modification_text(self) -> str:
        """Calculer la modification du texte pour la page.

        Cette méthode privée calcule le texte à afficher pour la date de modification,
        en tenant compte des dates minimale et maximale.
        """
        modification_datetimes = [
            item.modificationDateTime() for item in self.items
        ]
        # TODO: A ESSAYER :
        # modification_datetimes: List[datetime.datetime] = [
        #     item.modificationDateTime() for item in self.items
        # ]
        # # essai:
        # try:
        #     return render.dateTime_range(min(modification_datetimes), max(modification_datetimes))
        #     # return render.dateRange(min(modification_datetimes), max(modification_datetimes))
        #     # return render.dateTime(range(min(modification_datetimes), max(modification_datetimes)))  # TODO : A essayer !
        #     return render.dateTimePeriod(min(modification_datetimes), max(modification_datetimes))
        # except ReferenceError or AttributeError as e:
        #     # print(f"tclib.gui.dialog.editor: {str(e)}")
        #     logging.error(f"tclib.gui.dialog.editor: {str(e)}")
        #     # vieux code:
        min_modification_datetime = min(modification_datetimes)
        max_modification_datetime = max(modification_datetimes)
        modification_text = render.dateTime(
            min_modification_datetime, humanReadable=True
        )
        if (
            max_modification_datetime - min_modification_datetime
            > date.ONE_MINUTE
        ):
            modification_text += " - %s" % render.dateTime(
                max_modification_datetime, humanReadable=True
            )
        return modification_text

    def addDescriptionEntry(self):
        """
        Ajoute un champ de saisie multiligne pour la description.
        """

        def combined_description(items):
            return "[%s]\n\n" % _(
                "Edit to change all descriptions"
            ) + "\n\n".join(item.description() for item in items)

        current_description = (
            self.items[0].description()
            if len(self.items) == 1
            else combined_description(self.items)
        )

        try:
            self._descriptionEntry = widgetstk.textctrltk.MultiLineTextCtrl(
                self, current_description
            )
            self.addEntry(
                _("Description"),
                self._descriptionEntry,
                growable=True,
            )
        except:
            # Frame pour contenir le Text et la scrollbar
            desc_frame = ttk.Frame(self)

            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(
                desc_frame, orient="vertical", command=desc_text.yview
            )
            desc_text.configure(yscrollcommand=scrollbar.set)

            desc_text.insert("1.0", current_description)

            desc_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            self.addEntry(_("Description"), desc_frame, growable=True)
            self.entries_dict["description"] = desc_text

    def addDateTimeEntries(self, label, attribute_name):
        # TODO: remplacer les 2 fonctions suivantes pas celle-ci, régler le problème de dateTime_range
        date_times = [getattr(item, attribute_name)() for item in self.items]
        min_date, max_date = min(date_times), max(date_times)
        # date_text = render.dateTime_range(min_date, max_date)
        date_text = render.dateTime(range(min_date, max_date))

    def addCreationDateTimeEntry(self):
        """
        Ajoute un champ d'affichage pour la date de création.
        """
        # creation_text = "Creation date display"  # Simplifié pour l'exemple
        creation_datetimes = [item.creationDateTime() for item in self.items]
        min_creation_datetime = min(creation_datetimes)
        max_creation_datetime = max(creation_datetimes)
        creation_text = render.dateTime(
            min_creation_datetime, humanReadable=True
        )
        if max_creation_datetime - min_creation_datetime > date.ONE_MINUTE:
            creation_text += " - %s" % render.dateTime(
                max_creation_datetime, humanReadable=True
            )
        creation_label = ttk.Label(self, text=creation_text)
        self.addEntry(_("Creation date"), creation_label)

    def addModificationDateTimeEntry(self):
        """
        Ajoute un champ d'affichage pour la date de modification.
        """
        modification_text = (
            "Modification date display"  # Simplifié pour l'exemple
        )
        modification_label = ttk.Label(self, text=modification_text)
        self.addEntry(_("Modification date"), modification_label)
        for eventType in self.items[0].modificationEventTypes():
            if eventType.startswith("pubsub"):
                pub.subscribe(self.on_subject_changed, eventType)
            else:
                patterns.Publisher().registerObserver(
                    self.on_subject_changed,
                    eventType=eventType,
                    eventSource=self.items[0],
                )

    def on_subject_changed(self, event):  # Remplace onAttributeChanged
        """Gère l'événement de modification du sujet."""
        # On pourrait déclencher un événement pour mettre à jour le titre
        # du dialogue parent, mais pour l'instant, nous le laissons au
        # gestionnaire de dialogue parent.
        # Ici on pourrait déclencher la mise à jour du titre
        # et synchroniser avec l'objet de domaine
        # pass
        self._modificationTextEntry.SetLabel(self.__modification_text())

    def update_item_value(self):
        """Met à jour le sujet de l'objet de domaine."""
        new_subject = self.subject_entry.get()
        # new_subject = subject_entry.get()
        # if new_subject != self.item.subject():
        if new_subject != self.items.subject():
            # Dans une implémentation complète, il faudrait ici une commande
            # pour modifier l'objet de domaine de manière réversible.
            # self.item.set_subject(new_subject)
            self.items.set_subject(new_subject)

    def close(self):
        """Cette méthode est appelée lors de la fermeture de la page.
        Elle se désabonne des événements pour éviter les fuites de mémoire.
        """
        super().close()
        for eventType in self.items[0].modificationEventTypes():
            try:
                pub.unsubscribe(self.on_subject_changed, eventType)
            except pub.TopicNameError:
                pass
        patterns.Publisher().removeObserver(self.on_subject_changed)

    def entries(self):
        """Cette méthode retourne un dictionnaire contenant des références
        vers les contrôles de la page,
        utilisé probablement pour la navigation ou d'autres fonctionnalités.
        """
        return dict(
            firstEntry=self.subject_entry,
            subject=self.subject_entry,
            description=self._descriptionEntry,
            creationDateTime=self.subject_entry,
            modificationDateTime=self.subject_entry,
        )


class TaskSubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet et la priorité d'une tâche.
    """

    # pageTitle = _("Task Subject")
    def addEntries(self):
        """
        Ajoute les champs d'entrée pour le sujet et la priorité de la tâche.
        """
        # Ajoute les widgets pour éditer le sujet et la priorité de la tâche.
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addPriorityEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addPriorityEntry(self):
        """
        Ajoute un champ pour modifier la priorité de la tâche.
        """
        current_priority = (
            self.items[0].priority() if len(self.items) == 1 else 0
        )

        priority_spinbox = tk.Spinbox(
            self, from_=0, to=10, value=current_priority, width=10
        )

        # il manque cette partie :
        self._prioritySync = attributesync.AttributeSync(
            "priority",
            self._priorityEntry,
            current_priority,
            self.items,
            command.EditPriorityCommand,
            "<Tk.Spinbox.activate>",
            self.items[0].priorityChangedEventType(),
        )

        self.addEntry(_("Priority"), priority_spinbox)
        self.entries_dict["priority"] = priority_spinbox

    def entries(self):
        """Retourne un dictionnaire contenant les références aux contrôles.

        This method overrides the entries method from the parent class.
        It calls the parent's entries method to get a dictionary containing references to existing controls.
        It adds a new key-value pair to the dictionary, where the key is "priority" and the value is the reference to the spin control (self._priorityEntry).
        It returns the updated dictionary containing references to all controls on the page.
        """
        entries = super().entries()
        # entries["priority"] = self._priorityEntry
        entries["priority"] = self.entries_dict["priority"]
        return entries


class CategorySubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet des catégories.
    """

    # pageTitle = _("Category Subject")
    def addEntries(self):
        """
        Ajoute les entrées de l'interface, y compris les sous-catégories exclusives.
        """
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addExclusiveSubcategoriesEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addExclusiveSubcategoriesEntry(self):
        """
        Ajoute un champ pour définir si les sous-catégories doivent être exclusives.
        """
        current_exclusivity = (
            self.items[0].hasExclusiveSubcategories()
            if len(self.items) == 1
            else False
        )

        exclusive_var = tk.BooleanVar(value=current_exclusivity)
        exclusive_check = ttk.Checkbutton(
            self,
            command=command.EditExclusiveSubcategoriesCommand,
            text=_("Mutually exclusive"),
            variable=exclusive_var,
        )
        # Pour remplacer wx.EVT_CHECKBOX de wxPython par une solution compatible avec Tkinter,
        # utilisez command= dans la méthode Checkbutton de Tkinter.
        # Par exemple : Checkbutton(root, text="Option", variable=var, command=callback_function).
        self._exclusiveSubcategoriesSync = attributesync.AttributeSync(
            "hasExclusiveSubcategories",
            exclusive_var,
            current_exclusivity,
            self.items,
            command.EditExclusiveSubcategoriesCommand,
            # wx.EVT_CHECKBOX,  # TODO : A convertir
            self.items[0].exclusiveSubcategoriesChangedEventType(),
        )
        self.addEntry(_("Subcategories"), exclusive_check)


# class NoteSubjectPage(SubjectPage):
#     pageTitle = _("Note Subject")


class AttachmentSubjectPage(SubjectPage):
    """
    Page d'édition pour les pièces jointes.
    """

    # pageTitle = _("Attachment Subject")
    def addEntries(self):
        """
        Ajoute les champs d'édition spécifiques aux pièces jointes.
        """
        self.addSubjectEntry()
        self.addLocationEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addLocationEntry(self):
        """
        Ajoute un champ d'édition pour l'emplacement du fichier.
        """
        current_location = (
            self.items[0].location()
            if len(self.items) == 1
            else _("Edit to change location of all attachments")
        )

        location_frame = ttk.Frame(self)
        location_entry = ttk.Entry(location_frame)
        location_entry.insert(0, current_location)
        location_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_button = ttk.Button(
            location_frame, text=_("Browse"), command=self.on_browse_location
        )
        browse_button.pack(side="right")

        self.addEntry(_("Location"), location_frame, growable=True)
        self.entries_dict["location"] = location_entry

    def on_browse_location(self):  # Remplace onSelectLocation
        """
        Ouvre un dialogue de sélection de fichier.
        """
        from tkinter import filedialog

        filename = filedialog.askopenfilename()
        if filename:
            self.entries_dict["location"].delete(0, tk.END)
            self.entries_dict["location"].insert(0, filename)


class TaskAppearancePage(Page):
    """
    Page d'édition de l'apparence des tâches.

    Page d'édition pour modifier l'apparence (couleur, police, icône) d'une tâche.
    Cette page permet de modifier des éléments visuels liés aux tâches, comme la couleur,
    la mise en forme, ou d'autres attributs visuels.

    Objectif : Gérer l'apparence des tâches (couleur, police, icône).

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition de l'apparence.
    """

    pageName = "appearance"
    pageTitle = _("Appearance")
    # pageIcon = "palette_icon"
    pageIcon = "eye_icon"
    columns = 5

    # j'ai ajouté __init__
    def __init__(self, items, parent, settings, *args, **kwargs):
        # Initialisation des références pour la synchronisation
        self._foregroundColorSync = None
        self._backgroundColorSync = None
        self._fontSync = None
        self._iconSync = None

        self._foregroundColorEntry = None
        self._backgroundColorEntry = None
        self._fontEntry = None
        self._iconEntry = None

        super().__init__(items, parent, settings, *args, **kwargs)
        self.addEntries()

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour modifier l'apparence de la tâche (couleur, style, etc.).
        """
        # 1. Couleur de premier plan (Foreground Color)
        # 2. Couleur d'arrière-plan (Background Color)
        self.addColorEntries()
        # 3. Police (Font)
        self.addFontEntry()
        # 4. Icône (Icon)
        self.addIconEntry()

    def addColorEntries(self):
        # 1. Couleur de premier plan (Foreground Color)
        current_fg_color = (
            self.items[0].foregroundColor()
            if len(self.items) == 1
            else "#000000"
        )
        self._foregroundColorEntry = entry.ColorEntry(self, current_fg_color)
        # Note : On utilise 'tk.StringVar' ou les événements Tkinter pour simuler wx.EVT_KILL_FOCUS
        self._foregroundColorSync = attributesync.AttributeSync(
            "foregroundColor",
            self._foregroundColorEntry,
            current_fg_color,
            self.items,
            command.EditForegroundColorCommand,
            "<<ColorChanged>>",  # Événement Tkinter mocké
            self.items[0].foregroundColorChangedEventType(),
        )
        self.addEntry(_("Foreground color"), self._foregroundColorEntry)

        # 2. Couleur d'arrière-plan (Background Color)
        current_bg_color = (
            self.items[0].backgroundColor()
            if len(self.items) == 1
            else "#FFFFFF"
        )
        self._backgroundColorEntry = entry.ColorEntry(self, current_bg_color)
        self._backgroundColorSync = attributesync.AttributeSync(
            "backgroundColor",
            self._backgroundColorEntry,
            current_bg_color,
            self.items,
            command.EditBackgroundColorCommand,
            "<<ColorChanged>>",  # Événement Tkinter mocké
            self.items[0].backgroundColorChangedEventType(),
        )
        self.addEntry(_("Background color"), self._backgroundColorEntry)

    def addColorEntry(self, labelText, colorType, defaultColor):
        currentColor = (
            getattr(self.items[0], "%sColor" % colorType)(recursive=False)
            if len(self.items) == 1
            else None
        )
        colorEntry = entry.ColorEntry(self, currentColor, defaultColor)
        setattr(self, "_%sColorEntry" % colorType, colorEntry)
        commandClass = getattr(
            command, "Edit%sColorCommand" % colorType.capitalize()
        )
        colorSync = attributesync.AttributeSync(
            "%sColor" % colorType,
            colorEntry,
            currentColor,
            self.items,
            commandClass,
            # entry.EVT_COLORENTRY,
            "<<ColorChanged>>",
            self.items[0].appearanceChangedEventType(),
        )
        setattr(self, "_%sColorSync" % colorType, colorSync)
        # self.addEntry(labelText, colorEntry, flags=[None, wx.ALL])
        # self.addEntry(labelText, colorEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])
        self.addEntry(labelText, colorEntry)

    def addFontEntry(self):
        # 3. Police (Font)
        current_font = self.items[0].font() if len(self.items) == 1 else ""
        self._fontEntry = entry.FontEntry(self, current_font)
        self._fontSync = attributesync.AttributeSync(
            "font",
            self._fontEntry,
            current_font,
            self.items,
            command.EditFontCommand,
            "<<FontChanged>>",  # Événement Tkinter mocké
            self.items[0].fontChangedEventType(),
        )
        self.addEntry(_("Font"), self._fontEntry)

    def addIconEntry(self):
        # 4. Icône (Icon)
        current_icon = (
            self.items[0].iconName()
            if len(self.items) == 1
            else "task_icon_default"
        )
        self._iconEntry = entry.IconEntry(self, current_icon)
        self._iconSync = attributesync.AttributeSync(
            "iconName",
            self._iconEntry,
            current_icon,
            self.items,
            command.EditIconCommand,
            "<<IconChanged>>",  # Événement Tkinter mocké
            self.items[0].iconNameChangedEventType(),
        )
        self.addEntry(_("Icon"), self._iconEntry)

    def entries(self):
        """Retourne les entrées pour le focus et la navigation."""
        return dict(
            firstEntry=self._foregroundColorEntry,
            foregroundColor=self._foregroundColorEntry,
            backgroundColor=self._backgroundColorEntry,
            font=self._fontEntry,
            iconName=self._iconEntry,
        )


# Cette page gère l'édition des dates de début, d'échéance et de récurrence de la tâche.
# Ce code utilise :
#
#     entry.DateTimeEntry(self) : Pour les champs de date de début et d'échéance.
#     entry.RecurrenceEntry(self, ...) : Pour le champ de récurrence.
#     attributesync.AttributeSync(...) : Pour lier chaque widget au modèle de données de la tâche (items) et déclencher les commandes d'édition appropriées (command.EditStartDateCommand, etc.) lors des modifications du widget.
#     entry.DateTimeEntry.ValueChangedEventType et entry.RecurrenceEntry.ValueChangedEventType : Ce sont les événements personnalisés que vos widgets Tkinter doivent générer pour notifier AttributeSync d'un changement, simulant le comportement de wx.EVT_KILL_FOCUS.
class DatesPage(Page):
    """
    Page d'édition pour modifier les dates d'une tâche (début, échéance, récurrence).
    """

    pageName = "dates"
    pageTitle = _("Dates")
    pageIcon = "calendar_icon"  # icône de calendrier

    def __init__(self, items, parent, settings, *args, **kwargs):
        # Initialisation des références pour la synchronisation
        self._startDateSync = None
        self._dueDateSync = None
        self._recurrenceSync = None

        self._startDateEntry = None
        self._dueDateEntry = None
        self._recurrenceEntry = None

        super().__init__(items, parent, settings, *args, **kwargs)
        self.addEntries()

    def addEntries(self):
        """Ajoute les champs d'entrée spécifiques pour l'édition des dates."""

        # 1. Date de Début (Start Date)
        # On utilise entry.DateTimeEntry pour un contrôle Date/Heure
        self._startDateEntry = entry.DateTimeEntry(self)
        self._startDateSync = attributesync.AttributeSync(
            "startDate",
            self._startDateEntry,
            self.items[0].startDate(),  # Récupérer la valeur actuelle
            self.items,
            command.EditStartDateCommand,
            # L'événement Tkinter de DateTimeEntry
            entry.DateTimeEntry.ValueChangedEventType,
            self.items[0].startDateChangedEventType(),
        )
        self.addEntry(_("Start date"), self._startDateEntry)

        # 2. Date d'Échéance (Due Date)
        # On utilise entry.DateTimeEntry pour un contrôle Date/Heure
        self._dueDateEntry = entry.DateTimeEntry(self)
        self._dueDateSync = attributesync.AttributeSync(
            "dueDate",
            self._dueDateEntry,
            self.items[0].dueDate(),  # Récupérer la valeur actuelle
            self.items,
            command.EditDueDateCommand,
            # L'événement Tkinter de DateTimeEntry
            entry.DateTimeEntry.ValueChangedEventType,
            self.items[0].dueDateChangedEventType(),
        )
        self.addEntry(_("Due date"), self._dueDateEntry)

        # 3. Récurrence (Recurrence)
        # On utilise entry.RecurrenceEntry pour le contrôle de récurrence
        self._recurrenceEntry = entry.RecurrenceEntry(
            self, self.items[0].recurrence(), self.settings
        )
        self._recurrenceSync = attributesync.AttributeSync(
            "recurrence",
            self._recurrenceEntry,
            self.items[
                0
            ].recurrence(),  # Récupérer la valeur actuelle (objet Recurrence)
            self.items,
            command.EditRecurrenceCommand,
            # L'événement Tkinter de RecurrenceEntry
            entry.RecurrenceEntry.ValueChangedEventType,
            self.items[0].recurrenceChangedEventType(),
        )
        self.addEntry(_("Recurrence"), self._recurrenceEntry)

    def entries(self):
        """Retourne les entrées pour le focus et la navigation."""
        return dict(
            firstEntry=self._startDateEntry,
            startDate=self._startDateEntry,
            dueDate=self._dueDateEntry,
            recurrence=self._recurrenceEntry,
        )


# Cette page gère le statut d'achèvement (completion) et la priorité (priority) d'une tâche.
#
# Nous allons nous appuyer sur vos classes existantes attributesynctk.py et entrytk.py, en supposant que entrytk.py contient des widgets Tkinter pour IntegerEntry et PercentEntry (pour le pourcentage d'achèvement) ou que nous devons les implémenter. Pour être sûr, je vais m'inspirer de la version originale de TaskCoach et utiliser des widgets standards (ou mockés si nécessaire) liés à AttributeSync.


# Documentation et Raisonnement
#
#     entry.ChoiceEntry pour le Statut : Le statut de la tâche (en attente, démarrée, terminée) est un choix dans une liste. ChoiceEntry (que j'assume exister dans entrytk.py) est l'équivalent Tkinter de wx.Choice ou wx.ComboBox pour cette fonction. J'ai ajouté une logique pour récupérer les valeurs de statut à partir de task_file.
#     entry.IntEntry pour le Pourcentage : Le pourcentage d'achèvement est un nombre entier entre 0 et 100. L'utilisation de IntEntry assure que seules des valeurs numériques valides sont saisies, reproduisant le contrôle wx.SpinCtrl ou wx.TextCtrl validé.
#     entry.DurationEntry pour l'Effort Estimé : L'effort estimé est généralement stocké sous forme de durée (par exemple, en secondes) et affiché dans un format lisible (par exemple, HH:MM). DurationEntry gère cette conversion pour l'utilisateur.
#     attributesync.AttributeSync : Comme pour la page précédente, chaque champ est lié à l'attribut du domaine et à la commande d'édition correspondante (command.EditStatusCommand, command.EditProgressCommand, etc.) via AttributeSync pour maintenir la cohérence MVC (Modèle-Vue-Contrôleur).
class ProgressPage(Page):
    """
    Page d'édition pour modifier le pourcentage d'achèvement (completion) et
    la priorité (priority) d'une tâche.
    """

    pageName = "progress"
    pageTitle = _("Progress")
    pageIcon = "progress_icon"  # icône de progression

    def __init__(self, items, parent, settings, *args, **kwargs):
        # Initialisation des références pour la synchronisation
        self._completionSync = None
        self._prioritySync = None
        self._statusSync = None
        self._progressSync = None
        self._estimatedEffortSync = None

        self._completionEntry = None
        self._priorityEntry = None
        self._statusEntry = None
        self._progressEntry = None
        self._estimatedEffortEntry = None

        super().__init__(items, parent, settings, *args, **kwargs)
        self.addEntries()

    def addEntries(self):
        """Ajoute les champs d'entrée spécifiques pour l'édition de la progression."""

        # Récupération de la liste des statuts possibles pour l'objet TaskFile
        task_file = self.items[0].taskFile()
        # Si task_file est un Mock ou non accessible, nous devons fournir une liste par défaut.
        # Sinon, nous utilisons task_file.statusValues().
        status_values = getattr(
            task_file,
            "statusValues",
            lambda: ["pending", "started", "complete"],
        )()

        # 1. Statut (Status)
        # On utilise entry.ChoiceEntry pour sélectionner un statut dans une liste.
        # Le status par défaut est 'pending' si l'édition est multiple.
        current_status = (
            self.items[0].status() if len(self.items) == 1 else "pending"
        )

        self._statusEntry = entry.ChoiceEntry(self, choices=status_values)
        self._statusSync = attributesync.AttributeSync(
            "status",
            self._statusEntry,
            current_status,
            self.items,
            command.EditStatusCommand,
            # L'événement Tkinter de ChoiceEntry (similaire à wx.EVT_CHOICE)
            entry.ChoiceEntry.ValueChangedEventType,
            self.items[0].statusChangedEventType(),
        )
        self.addEntry(_("Status"), self._statusEntry)

        # 2. Pourcentage d'achèvement (Progress)
        # On utilise entry.IntEntry pour un nombre entier (0-100)
        current_progress = (
            self.items[0].progress() if len(self.items) == 1 else 0
        )

        self._progressEntry = entry.IntEntry(self, minValue=0, maxValue=100)
        self._progressSync = attributesync.AttributeSync(
            "progress",
            self._progressEntry,
            current_progress,
            self.items,
            command.EditProgressCommand,
            # L'événement Tkinter de IntEntry (similaire à wx.EVT_KILL_FOCUS)
            entry.IntEntry.ValueChangedEventType,
            self.items[0].progressChangedEventType(),
        )
        self.addEntry(_("Progress (%)"), self._progressEntry)

        # 3. Effort estimé (Estimated Effort)
        # On utilise entry.DurationEntry pour une durée (format HH:MM)
        current_effort = (
            self.items[0].estimatedEffort() if len(self.items) == 1 else 0
        )

        self._estimatedEffortEntry = entry.DurationEntry(self)
        self._estimatedEffortSync = attributesync.AttributeSync(
            "estimatedEffort",
            self._estimatedEffortEntry,
            current_effort,  # Attribut de type duration
            self.items,
            command.EditEstimatedEffortCommand,
            # L'événement Tkinter de DurationEntry
            entry.DurationEntry.ValueChangedEventType,
            self.items[0].estimatedEffortChangedEventType(),
        )
        self.addEntry(_("Estimated effort"), self._estimatedEffortEntry)

    def entries(self):
        """Retourne les entrées pour le focus et la navigation."""
        return dict(
            firstEntry=self._statusEntry,
            status=self._statusEntry,
            progress=self._progressEntry,
            estimatedEffort=self._estimatedEffortEntry,
        )


# Note sur l'implémentation
#
# Cette conversion suit la structure des précédentes :
#
#     Utilisation de widgets spécialisés (entry.FloatEntry) pour garantir le type de saisie (nombres décimaux).
#     Chaque champ est lié à son attribut de domaine ("budget" ou "cost") et à sa commande d'édition (command.EditBudgetCommand ou command.EditCostCommand) via attributesync.AttributeSync.
#     Les valeurs sont initialisées en récupérant l'attribut du premier élément (self.items[0].budget()).
class BudgetPage(Page):
    """
    Page d'édition pour modifier le budget et le coût d'une tâche.
    """

    pageName = "budget"
    pageTitle = _("Budget")
    pageIcon = "money_icon"  # icône de budget/argent

    def __init__(self, items, parent, settings, *args, **kwargs):
        # Initialisation des références pour la synchronisation
        self._budgetSync = None
        self._costSync = None

        self._budgetEntry = None
        self._costEntry = None

        super().__init__(items, parent, settings, *args, **kwargs)
        self.addEntries()

    def addEntries(self):
        """Ajoute les champs d'entrée spécifiques pour l'édition du budget."""

        # NOTE : Je vais utiliser entry.FloatEntry pour ces valeurs
        # car elles sont typiquement des nombres décimaux (monnaie).
        # Si vous avez une MoneyEntry spécifique dans entrytk.py, remplacez-le.

        # 1. Budget
        # Récupère la valeur actuelle du budget
        current_budget = (
            self.items[0].budget() if len(self.items) == 1 else 0.0
        )

        # self._budgetEntry = entry.FloatEntry(self, minValue=0.0)
        self._budgetEntry = entry.AmountEntry(self, minValue=0.0)
        self._budgetSync = attributesync.AttributeSync(
            "budget",
            self._budgetEntry,
            current_budget,  # Valeur de type float
            self.items,
            command.EditBudgetCommand,
            # Événement Tkinter pour FloatEntry
            # entry.FloatEntry.ValueChangedEventType,
            entry.AmountEntry.ValueChangedEventType,  # bind ou GetValue ?
            self.items[0].budgetChangedEventType(),
        )
        self.addEntry(_("Budget"), self._budgetEntry)

        # 2. Coût (Cost)
        # Récupère la valeur actuelle du coût
        current_cost = self.items[0].cost() if len(self.items) == 1 else 0.0

        self._costEntry = entry.AmountEntry(self, minValue=0.0)
        self._costSync = attributesync.AttributeSync(
            "cost",
            self._costEntry,
            current_cost,  # Valeur de type float
            self.items,
            command.EditCostCommand,
            # Événement Tkinter pour FloatEntry
            # entry.FloatEntry.ValueChangedEventType,
            entry.AmountEntry.ValueChangedEventType,  # bind ou GetValue ?
            self.items[0].costChangedEventType(),
        )
        # Le coût est souvent en lecture seule ou calculé à partir des efforts enregistrés,
        # mais ici, nous le traitons comme un champ éditable standard pour la cohérence
        # avec le fichier original, s'il était éditable.
        self.addEntry(_("Cost"), self._costEntry)

    def entries(self):
        """Retourne les entrées pour le focus et la navigation."""
        return dict(
            firstEntry=self._budgetEntry,
            budget=self._budgetEntry,
            cost=self._costEntry,
        )


# La classe PageWithViewer est essentielle car elle introduit un Viewer (visualiseur) pour les pages qui gèrent des collections d'éléments (Catégories, Pièces jointes, Notes, etc.).
#
# Dans wxPython, ce viewer est souvent un wx.ListCtrl ou wx.DataViewCtrl. Dans Tkinter, l'équivalent le plus proche pour afficher des données tabulaires ou en liste est le tkinter.ttk.Treeview.
#
# Nous devons convertir PageWithViewer en une classe de base Tkinter, en adaptant notamment la gestion du viewer.
#
# 1. Conversion de PageWithViewer en Tkinter
#
# Voici la version Tkinter de PageWithViewer, à placer dans editortk.py. J'ai adapté la méthode addEntries pour utiliser le système de grille de Tkinter/Ttk, et j'ai remplacé l'appel à wx.CallAfter (qui retarde l'exécution) par une simple exécution, car la suppression des objets Tkinter est souvent synchrone ou gérée par Python/Tkinter lui-même dans ce contexte simple.


# Prochaine étape : Le Viewer de Catégories (LocalCategoryViewer)
#
# Maintenant que la classe de base est prête, nous devons créer le Viewer réel qui sera utilisé par CategoriesPage.
#
# La classe de Taskcoach s'appelle LocalCategoryViewer dans editor.py. Elle doit probablement hériter d'une classe de base de Viewer (TaskFileViewer ou similaire) qui utilise ttk.Treeview.
class PageWithViewer(Page):
    """
    Classe de base pour les pages d'édition qui contiennent un Viewer (Treeview)
    pour afficher et gérer une collection d'éléments (Catégories, Efforts, Notes, etc.).
    """

    columns = 1

    # Nous n'avons pas besoin de self.viewer = None ici car il sera initialisé
    # dans __init__ après l'appel à super().__init__.
    def __init__(
        self,
        items,
        parent,
        taskFile,
        settings,
        settingsSection,
        *args,
        **kwargs,
    ):
        # Référence au modèle de données et aux réglages
        self.__taskFile = taskFile
        self.__settings = settings
        self.__settingsSection = settingsSection
        self.viewer = None  # Initialiser la référence

        super().__init__(items, parent, *args, **kwargs)
        # Note : La méthode addEntries() est appelée ici par les classes
        # enfants, donc nous allons l'exécuter à la fin du constructeur,
        # comme c'est la pratique courante dans les classes Page,
        # SAUF si la classe enfant a une raison de ne pas le faire.
        self.addEntries()

    def addEntries(self):
        """
        Crée et ajoute le Viewer à la page.
        Doit être appelé une seule fois.
        """
        # Note: L'attribut 'items' est garanti d'exister grâce à l'appel
        # à super().__init__(...)

        # 1. Création du Viewer (implémentée par la classe enfant)
        self.viewer = self.createViewer(
            self.__taskFile, self.__settings, self.__settingsSection
        )

        # 2. Ajout du Viewer à la page
        # Nous utilisons la méthode addEntry de la classe Page de base.
        # growable=True est l'équivalent de flags=[wx.EXPAND]
        # et permet au Treeview de prendre tout l'espace restant.
        self.addEntry(self.viewer, growable=True)

    def entries(self):
        """Retourne le Viewer comme première entrée pour le focus."""
        return {"firstEntry": self.viewer}

    def createViewer(self, taskFile, settings, settingsSection):
        """
        Méthode abstraite. Doit être implémentée par les classes enfants
        pour créer le Viewer spécifique (ex: LocalCategoryViewer).
        """
        raise NotImplementedError(
            "La classe enfant doit implémenter createViewer()"
        )

    def close(self):
        """
        Détache et supprime le Viewer avant la fermeture de la page.
        """
        if self.viewer:
            # 1. Détachement : Arrête l'observation des événements de TaskFile
            self.viewer.detach()

            # 2. Suppression : En Tkinter, nous pouvons simplement supprimer la référence.
            # L'équivalent de wx.CallAfter est généralement superflu pour la suppression
            # de références Python.
            self.deleteViewer()

        super().close()

    def deleteViewer(self):
        """Supprime la référence au Viewer."""
        if hasattr(self, "viewer"):
            # Si le widget a une méthode .destroy() (ce qui est le cas pour les Ttk/Tk widgets),
            # nous l'appelons également pour nettoyer les ressources Tkinter.
            if hasattr(self.viewer, "destroy"):
                self.viewer.destroy()
            del self.viewer


# Excellent ! La classe CategoriesPage est la première page concrète à hériter de PageWithViewer, et elle montre une logique d'initialisation intéressante : elle ne crée son contenu (le Viewer) que lorsque la page est sélectionnée pour la première fois (selected()).
#
# Voici la conversion complète de CategoriesPage pour votre fichier editortk.py.
# Explication de l'approche
#
# L'aspect le plus important de cette conversion est la gestion de l'initialisation :
#
#     __realized et selected() : La page utilise un drapeau __realized pour différer la création du contenu lourd (LocalCategoryViewer). Le contenu n'est créé (via super().addEntries(), qui appelle createViewer()) que la première fois que l'utilisateur sélectionne l'onglet correspondant.
#
#     addEntries() neutralisé : La méthode addEntries de cette classe est vide (pass) pour empêcher que le contenu soit ajouté prématurément par l'initialisation de la classe de base.
#
#     Observateurs : createViewer() enregistre la méthode onCategoryChanged pour écouter les événements de modification de catégorie (categoryAddedEventType, categoryRemovedEventType) sur l'élément en cours d'édition. Cela garantit que le viewer est mis à jour si un changement survient ailleurs (par exemple, via le menu contextuel du viewer ou une autre opération).
class CategoriesPage(PageWithViewer):
    """
    Page d'édition des catégories d'un objet.

    Permet d'assigner des catégories à un objet comme une tâche ou une note.
    Elle hérite de PageWithViewer qui gère l'affichage d'un visualiseur de contenu.
    """

    # Constantes :
    pageName = "categories"
    pageTitle = _("Categories")
    pageIcon = "folder_blue_arrow_icon"  # Nom de l'icône associée à la page

    def __init__(self, *args, **kwargs):
        """Initialise la page d'édition des catégories."""
        # Indique si les champs d'édition ont été ajoutés (évite les doublons d'ajout)
        self.__realized = False

        # Note : On n'appelle PAS super().__init__ tout de suite ici,
        # car PageWithViewer l'appelle et exécute self.addEntries(),
        # ce qui est prématuré pour CategoriesPage.
        # Dans le modèle Taskcoach, PageWithViewer.__init__ est parfois contourné
        # ou ajusté pour ce cas. Ici, nous allons ajuster le flux.

        # Puisque la classe CategoriesPage que vous avez fournie appelle
        # super().__init__ AVANT de définir le comportement de addEntries/selected,
        # nous devons neutraliser addEntries dans la classe de base
        # si elle est appelée automatiquement, ou, plus simplement,
        # s'assurer que l'appel est fait au bon moment.

        # Pour maintenir la fidélité au code original qui gère 'realized'
        # et appelle addEntries() dans selected():
        super().__init__(
            *args, **kwargs
        )  # Ceci initialise self.items, self.parent, etc.

    def addEntries(self):
        """
        Neutralise l'appel automatique de addEntries par PageWithViewer ou la classe de base Page.
        Le contenu est ajouté uniquement dans selected().
        """
        pass

    def selected(self):
        """
        Gère la sélection de la page et ajoute les champs d'édition
        seulement lors du premier affichage.
        """
        if not self.__realized:
            self.__realized = True
            # Appelle la version de PageWithViewer.addEntries pour créer et ajouter le viewer
            # Note: Si la classe PageWithViewer que j'ai implémentée avait déjà
            # appelé self.addEntries() dans son __init__, nous devrions être vigilants.
            # Pour l'instant, on suppose que l'appel de super().addEntries() est nécessaire.
            PageWithViewer.addEntries(self)

            # La méthode fit() est un concept wxPython pour ajuster la taille.
            # En Tkinter, si le parent est bien géré par un gestionnaire de géométrie (grid/pack),
            # on peut souvent l'omettre, ou appeler un éventuel gestionnaire de géométrie
            # du conteneur parent si nécessaire. On l'omet pour le moment.
            # self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée le visualiseur de catégories associé à l'objet (LocalCategoryViewer)."""
        # On suppose que l'édition de catégories n'est permise que pour un seul élément à la fois
        assert len(self.items) == 1
        item = self.items[0]

        # Enregistrement des observateurs pour rafraîchir la page si les catégories de l'élément changent
        for eventType in (
            item.categoryAddedEventType(),
            item.categoryRemovedEventType(),
        ):
            # Utilisation de la méthode d'enregistrement de la classe de base Page/Observer
            self.registerObserver(
                self.onCategoryChanged, eventType=eventType, eventSource=item
            )

        # Retourne l'instance de LocalCategoryViewer implémentée précédemment
        return LocalCategoryViewer(
            self.items,
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            # use_separate_settings_section est spécifique à Taskcoach, on l'inclut pour la fidélité
            use_separate_settings_section=False,
        )

    def onCategoryChanged(self, event):
        """Rafraîchit les éléments affichés dans le visualiseur de catégories en fonction des modifications."""
        # On suppose que self.viewer a une méthode refreshItems qui peut gérer une liste de valeurs
        if self.__realized and hasattr(self, "viewer"):
            # L'original utilise event.values(), qui renvoie les objets de catégorie modifiés/ajoutés/supprimés.
            # On passe ces valeurs à une méthode du viewer (à implémenter dans LocalCategoryViewer)
            # self.viewer.refreshItems(*list(event.values()))

            # Comme LocalCategoryViewerTK n'a qu'un simple refresh(), on l'appelle :
            self.viewer.refresh()  # Rafraîchissement complet pour simplifier

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur de catégories (si affiché)."""
        if self.__realized and hasattr(self, "viewer"):
            # Dans Taskcoach, le viewer est souvent le premier élément de focus
            return dict(firstEntry=self.viewer, categories=self.viewer)
        return dict()


# class EffortSubjectPage(SubjectPage):
#     pageTitle = _("Effort Subject")


class EffortPage(PageWithViewer):
    """
    Page d'édition de l'effort d'une tâche.

    Permet de gérer l'effort alloué à une tâche, souvent utilisé pour le suivi du temps.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition de l'effort.
                            Lancé dans PageWithViewer.
    """

    pageName = "effort"
    pageTitle = _("Effort")
    pageIcon = "clock_icon"

    def __init__(
        self,
        items,
        parent,
        taskFile,
        settings,
        settingsSection,
        *args,
        **kwargs,
    ):
        super().__init__(
            items, parent, taskFile, settings, settingsSection, *args, **kwargs
        )
        self.addEntries()

    def createViewer(self, taskFile, settings, settingsSection):
        # TODO: remplacer viewer.EffortViewer par EffortViewer
        return viewer.efforttk.Effortviewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            tasksToShowEffortFor=task.TaskList(self.items),
        )

    def entries(self):
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, timeSpent=self.viewer)
        return dict()


# Puisque cette classe hérite de BaseCategoryViewer (qui n'est pas fourni) et utilise des méthodes spécifiques à wxPython (self.widget.GetItemPyData, event.GetItem()), je dois :
#
#     Créer un BaseCategoryViewerTK minimal (ou TreeviewViewerTK) qui fournit le squelette nécessaire (ttk.Treeview) pour Tkinter.
#
#     Convertir LocalCategoryViewer en adaptant les appels aux événements de Treeview de Tkinter.
#
# J'assume que la structure du Treeview est implémentée dans un Viewer de base qui hérite de ttk.Frame et encapsule un ttk.Treeview.
#
# Voici l'implémentation pour editortk.py.
# Cette conversion remplace les spécificités de wxPython par :
#
#     BaseCategoryViewerTK : Un mock basé sur ttk.Frame et ttk.Treeview pour servir de base Tkinter.
#
#     Affichage : Le Treeview est rempli via refresh(). L'état coché/décoché est simulé à l'aide de tags du Treeview ('checked', 'unchecked').
#
#     Gestion des événements : Le gestionnaire onCheck de l'original est remplacé par _on_treeview_click de Tkinter, qui retrouve l'objet de catégorie et exécute directement command.ToggleCategoryCommand.
#
# Nous avons maintenant le Viewer. La prochaine étape est simple : intégrer ce Viewer dans la page d'édition correspondante, CategoriesPage. Voulez-vous que je continue avec cette classe ?
class BaseTreeviewViewerTK(ttk.Frame, patterns.Observer):
    """
    Classe de base pour les Viewers basés sur ttk.Treeview.
    Gère la mise en place du Treeview et les méthodes d'observateur.
    """

    def __init__(self, taskFile, settings, settingsSection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.taskFile = taskFile
        self.settings = settings
        self.settingsSection = settingsSection
        self.widget = ttk.Treeview(
            self, selectmode="none", show="tree headings"
        )  # Le Treeview lui-même
        self.widget.pack(expand=True, fill="both")

        # Initialisation de l'observation
        self.taskFile.addObserver(self)
        self.taskFile.taskFileChangedEvent().addObserver(self)

    # Méthode mock pour la création du menu contextuel
    def createCategoryPopupMenu(self, localOnly=False):
        # Ceci serait normalement le menu contextuel pour ajouter/éditer des catégories
        return None

    # Méthodes d'observateur nécessaires par patterns.Observer
    def update(self, *args, **kwargs):
        # Gérer les mises à jour du domaine (par ex., après une édition)
        self.refresh()

    def detach(self):
        # Arrêter l'observation
        self.taskFile.removeObserver(self)
        self.taskFile.taskFileChangedEvent().removeObserver(self)

    def refresh(self):
        # Recharger les données dans le Treeview (à implémenter dans les classes filles)
        pass


# Renommons-le pour correspondre au nom de base requis par LocalCategoryViewer
# BaseCategoryViewerTK = BaseTreeviewViewerTK
# BaseCategoryViewerTK = BaseCategoryViewer
# BaseCategoryViewerTK = categorytk.BaseCategoryViewer(self)
# Nouveau code pour briser la dépendance :
# Importez BaseCategoryViewer directement ici, car 'categorytk' est déjà
# un module connu mais incomplet. Nous utilisons un autre nom pour éviter
# un conflit de noms avec un éventuel import de BaseCategoryViewer ailleurs.
# from taskcoachlib.guitk.viewer.categorytk import BaseCategoryViewer as _BaseCategoryViewer


class LocalCategoryViewer(BaseCategoryViewer):
    # class LocalCategoryViewer(categorytk.BaseCategoryViewer):
    """
    Viewer pour l'édition locale des catégories d'une tâche.
    Affiche toutes les catégories et permet de cocher celles qui sont associées
    aux tâches en cours d'édition (self.__items).
    """

    # Nous désactivons l'avertissement car BaseCategoryViewerTK est un mock simplifié
    # pylint: disable=W0223, W0221

    def __init__(self, items, *args, **kwargs):
        self.__items = items
        super().__init__(*args, **kwargs)

        # Le Treeview de Tkinter ne prend pas en charge les cases à cocher
        # directement comme wx.CheckTreeCtrl. Nous devons configurer le Treeview
        # pour gérer les cases à cocher si possible (ou utiliser une colonne
        # spécifique pour cela si une extension comme ttkwidgets n'est pas utilisée).
        # Pour simplifier, nous allons simuler le cochage/décochage via un clic
        # sur l'élément.
        self.widget.bind("<Button-1>", self._on_treeview_click)

        # Initialisation du Treeview (méthode de BaseCategoryViewerTK)
        self.refresh()

        # Expansion : Simuler l'expansion des éléments persistants
        for (
            item
        ) in (
            self.domainObjectsToView()
        ):  # domainObjectsToView est à mocker/implémenter
            # Il est dans viewer.category.BaseCategoryViewer
            # Note: Pour une implémentation complète, il faudrait une méthode
            # pour expandre les items du Treeview. Pour l'instant, on ignore
            # la ligne de l'original pour l'expansion visuelle, mais on
            # garde la notification du modèle.
            # item.expand(context=self.settingsSection(), notify=False)
            pass

    # def domainObjectsToView(self):
    #     """Mock: Renvoie la liste des objets de domaine à afficher (les catégories)."""
    #     # Dans TaskCoach, c'est généralement taskFile.categories()
    #     return self.taskFile.categories()

    def refresh(self):
        """Vide le Treeview et le remplit avec les catégories du TaskFile."""
        # Vider l'ancien contenu
        for item in self.widget.get_children():
            self.widget.delete(item)

        # Remplir le Treeview avec les catégories (mock)
        # Ceci est un exemple très simplifié. L'implémentation réelle est complexe.
        for category in self.domainObjectsToView():
            tag = "checked" if self.getIsItemChecked(category) else "unchecked"
            self.widget.insert(
                "",
                "end",
                iid=str(
                    id(category)
                ),  # Utilise l'ID de l'objet comme identifiant Tkinter
                text=category.subject(),
                tags=(tag,),
            )

        # Configurer l'affichage des tags pour simuler les cases à cocher
        self.widget.tag_configure(
            "checked", foreground="blue"
        )  # Exemple visuel
        self.widget.tag_configure("unchecked", foreground="black")

    def getIsItemChecked(self, category):
        """Vérifie si la catégorie est associée à AU MOINS un des éléments édités."""
        for item in self.__items:
            # On suppose que item.categories() retourne l'ensemble des catégories
            if category in item.categories():
                return True
        return False

    def _on_treeview_click(self, event):
        """Gère le clic sur un élément du Treeview pour simuler l'événement onCheck."""
        iid = self.widget.identify_row(event.y)
        if not iid:
            return

        # Récupérer l'objet de catégorie correspondant à l'iid (identifiant Tkinter)
        # Dans une implémentation Treeview complète, on stockerait l'objet de domaine
        # dans une structure de données liée à l'iid. Ici, nous devons le retrouver.
        category = self._get_category_from_iid(iid)

        if category:
            # Exécuter la commande de bascule (simule onCheck avec final=True)
            self._do_toggle_command(category)

            # Rafraîchir l'affichage après la commande
            self.refresh()

    def _get_category_from_iid(self, iid):
        """Mock: Trouve l'objet catégorie à partir de son IID (simulé par id())."""
        # Ceci est une recherche inverse, nécessaire car Tkinter ne stocke pas
        # directement les objets Python comme wx.SetItemPyData
        for category in self.domainObjectsToView():
            if str(id(category)) == iid:
                return category
        return None

    def _do_toggle_command(self, category):
        """Exécute la commande de bascule de catégorie."""
        # L'événement wxPython est géré directement ici.
        command.ToggleCategoryCommand(
            None, self.__items, category=category
        ).do()

    def createCategoryPopupMenu(self, localOnly=True):
        """Appelle la version de la classe de base en forçant localOnly à True."""
        return super().createCategoryPopupMenu(True)


class LocalAttachmentViewer(Attachmentviewer):  # pylint: disable=W0223
    """
    Viewer pour l'édition locale des pièces jointes d'une tâche.
    """

    def __init__(self, *args, **kwargs):
        # Récupère l'objet propriétaire (tâche ou note)
        self.attachmentOwner = kwargs.pop("owner")

        # Crée la liste d'attachements à afficher
        attachments = attachment.AttachmentList(
            self.attachmentOwner.attachments()
        )

        # Initialisation de la classe de base
        # On passe attachmentsToShow au parent (AttachmentViewerTK)
        super().__init__(attachmentsToShow=attachments, *args, **kwargs)

    def newItemCommand(self, *args, **kwargs):
        """Crée une commande pour ajouter une nouvelle pièce jointe à l'objet propriétaire."""
        return command.AddAttachmentCommand(
            None, [self.attachmentOwner], *args, **kwargs
        )

    def deleteItemCommand(self):
        """Crée une commande pour supprimer les pièces jointes sélectionnées."""
        # Utilise curselection() du viewer pour obtenir les objets à supprimer
        return command.RemoveAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )

    def cutItemCommand(self):
        """Crée une commande pour couper les pièces jointes sélectionnées."""
        # Utilise curselection() du viewer pour obtenir les objets à couper
        return command.CutAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )


class AttachmentsPage(PageWithViewer):
    """
    Page d'édition des pièces jointes d'un objet.
    """

    # Attributs :
    pageName = "attachments"
    pageTitle = _("Attachments")
    pageIcon = "paperclip_icon"

    def __init__(
        self,
        items,
        parent,
        taskFile,
        settings,
        settingsSection,
        *args,
        **kwargs,
    ):
        # Cette page crée immédiatement son contenu (le Viewer)
        super().__init__(
            items, parent, taskFile, settings, settingsSection, *args, **kwargs
        )

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée un visualiseur d'attachements local pour l'objet."""
        assert len(self.items) == 1
        item = self.items[0]

        # 1. Enregistrement de l'observateur pour les changements de la liste d'attachements
        self.registerObserver(
            self.onAttachmentsChanged,
            eventType=item.attachmentsChangedEventType(),
            eventSource=item,
        )

        # 2. Création et retour du Viewer
        return LocalAttachmentViewer(
            self,  # Parent (la page elle-même)
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,  # Passage de l'objet propriétaire au viewer
        )  # Cannot instantiate abstract class 'LocalAttachmentViewer'

    def onAttachmentsChanged(self, event):  # pylint: disable=W0613
        """Rafraîchit le visualiseur d'attachements lorsque la liste des pièces jointes change."""
        if hasattr(self, "viewer") and self.viewer:
            # Vider la liste affichée dans le Viewer
            self.viewer.domainObjectsToView().clear()
            # Étendre la liste interne du viewer avec les pièces jointes actuelles
            self.viewer.domainObjectsToView().extend(
                self.items[0].attachments()
            )
            # Rafraîchir l'affichage du Treeview
            self.viewer.refresh()

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page,
        y compris le visualiseur d'attachements."""
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, attachments=self.viewer)
        return dict()


# Continuons avec la conversion des classes de gestion des notes : LocalNoteViewer et NotesPage.
#
# C'est très similaire aux pièces jointes, mais le Viewer de notes gère en plus la structure hiérarchique (sous-notes). Nous allons nous appuyer sur le mock BaseTreeviewViewerTK créé précédemment pour l'affichage hiérarchique dans le ttk.Treeview.
# Cette classe définit les commandes d'action spécifiques aux notes (Ajouter, Ajouter une sous-note, Supprimer).
class LocalNoteViewer(BaseNoteViewer):  # pylint: disable=W0223
    """
    Viewer pour l'édition locale des notes d'une tâche ou d'un objet.
    Gère la hiérarchie des notes.
    """

    def __init__(self, *args, **kwargs):
        # Récupère l'objet propriétaire (tâche ou autre)
        self.__note_owner = kwargs.pop("owner")

        # Crée un NoteContainer à partir des notes de l'objet propriétaire
        notes = note.NoteContainer(self.__note_owner.notes())

        # Initialisation de la classe de base
        super().__init__(notesToShow=notes, *args, **kwargs)

    def newItemCommand(self, *args, **kwargs):
        """Crée une commande pour ajouter une nouvelle note (au niveau racine) à l'objet propriétaire."""
        return command.AddNoteCommand(None, [self.__note_owner])

    def newSubItemCommand(self):
        """Crée une commande pour ajouter une note enfant à la note sélectionnée."""
        # La note parent est l'élément sélectionné
        selected_notes = self.curselection()
        if selected_notes:
            return command.AddSubNoteCommand(
                None, selected_notes, owner=self.__note_owner
            )
        # Retourne None si aucune note n'est sélectionnée ou si la commande ne peut être exécutée
        return None

    def deleteItemCommand(self):
        """Crée une commande pour supprimer les notes sélectionnées."""
        # Utilise curselection() du viewer pour obtenir les objets à supprimer
        return command.RemoveNoteCommand(
            None, [self.__note_owner], notes=self.curselection()
        )


# Cette classe intègre le visualiseur de notes dans la page et gère les mises à jour lorsque la liste des notes change.
class NotesPage(PageWithViewer):
    """
    Page d'édition des notes d'un objet.
    Permet d'ajouter ou modifier des notes attachées à un objet.
    """

    # Attributs :
    pageName = "notes"
    pageTitle = _("Notes")
    pageIcon = "note_icon"

    def __init__(
        self,
        items,
        parent,
        taskFile,
        settings,
        settingsSection,
        *args,
        **kwargs,
    ):
        # Cette page crée immédiatement son contenu (le Viewer)
        super().__init__(
            items, parent, taskFile, settings, settingsSection, *args, **kwargs
        )
        # Note : self.addEntries() est déjà appelé par super().__init__ (PageWithViewer)

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée un visualiseur de notes local pour l'objet."""
        assert len(self.items) == 1
        item = self.items[0]

        # 1. Enregistrement de l'observateur pour les changements de la liste de notes
        self.registerObserver(
            self.onNotesChanged,
            eventType=item.notesChangedEventType(),
            eventSource=item,
        )

        # 2. Création et retour du Viewer
        return LocalNoteViewer(
            self,  # Parent (la page elle-même)
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,  # Passage de l'objet propriétaire au viewer
        )

    def onNotesChanged(self, event):  # pylint: disable=W0613
        """Rafraîchit le visualiseur de notes lorsque la liste des notes change."""
        if hasattr(self, "viewer") and self.viewer:
            # Vider la liste affichée dans le Viewer
            self.viewer.domainObjectsToView().clear()
            # Étendre la liste interne du viewer avec les notes actuelles
            # Note : item.notes() retourne la liste de notes de niveau supérieur
            self.viewer.domainObjectsToView().extend(self.items[0].notes())
            # Rafraîchir l'affichage du Treeview
            self.viewer.refresh()

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur de notes."""
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, notes=self.viewer)
        return dict()


# Cette classe concrétise les méthodes de vérification pour les prérequis.
class LocalPrerequisiteViewer(
    tasktk.CheckableTaskViewer
):  # pylint: disable=W0223
    """
    Viewer pour l'édition locale des prérequis d'une tâche.
    """

    def __init__(self, items, *args, **kwargs):
        # La liste des tâches dont on gère les prérequis (le/les objet(s) édité(s))
        self.__items = items
        # taskFile est passé dans **kwargs et géré par la classe de base
        super().__init__(*args, **kwargs)

    def getIsItemChecked(self, item):
        """Détermine si une tâche donnée est sélectionnée comme prérequis."""
        # On suppose que l'édition est pour un seul élément (assert len(self.__items) == 1)
        return item in self.__items[0].prerequisites()

    def getIsItemCheckable(self, item):
        """Détermine si une tâche donnée peut être sélectionnée comme prérequis."""
        # Une tâche ne peut pas être son propre prérequis ni le prérequis d'une autre tâche éditée
        return item not in self.__items

    def onCheck(self, item, is_checked, final):
        """Gère l'événement de sélection/désélection d'une tâche en tant que prérequis."""
        # L'événement wxPython est géré ici avec les arguments adaptés (item, new_state, final)
        if final:
            # item est l'objet de tâche (le prérequis)
            # is_checked est le nouvel état (True pour coché, False pour décoché)

            checked, unchecked = ([item], []) if is_checked else ([], [item])

            command.TogglePrerequisiteCommand(
                None,
                self.__items,  # Les tâches en cours d'édition
                checkedPrerequisites=checked,
                uncheckedPrerequisites=unchecked,
            ).do()


# Cette classe gère l'initialisation tardive du viewer (comme CategoriesPage) et la mise à jour lors du changement des prérequis.
class PrerequisitesPage(PageWithViewer):
    """
    Page d'édition des prérequis d'une tâche.
    """

    pageName = "prerequisites"
    pageTitle = _("Prerequisites")
    pageIcon = "trafficlight_icon"

    def __init__(self, *args, **kwargs):
        self.__realized = False
        super().__init__(*args, **kwargs)
        # Note : addEntries est neutralisé par défaut dans cette implémentation
        # et est appelé dans selected()

    def addEntries(self):
        """
        Appel explicite de la méthode de base PageWithViewer.addEntries.
        """
        # Appel du parent pour créer et ajouter self.viewer
        PageWithViewer.addEntries(self)

    def selected(self):
        """Gère la sélection de la page et ajoute les champs d'édition seulement lors du premier affichage."""
        if not self.__realized:
            self.__realized = True
            # Appelle la version explicite de addEntries (qui appelle PageWithViewer.addEntries)
            self.addEntries()
            # fit() est une fonction wxPython. On l'omet en Tkinter.
            # self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        item = self.items[0]

        # Enregistrement de l'observateur pour les changements de prérequis
        # Note: L'original utilise pub.subscribe, nous utilisons self.registerObserver du Page/Observer
        self.registerObserver(
            self.onPrerequisitesChanged,
            eventType=item.prerequisitesChangedEventType(),
            eventSource=item,
        )

        return LocalPrerequisiteViewer(
            self.items,  # Passons la liste des items pour qu'elle puisse vérifier item not in self.__items
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
        )

    def onPrerequisitesChanged(self, event):
        """Rafraîchit les éléments affichés dans le visualiseur en fonction des modifications de prérequis."""
        # L'original utilise l'ancien système pubsub (newValue, sender), je m'adapte à la signature event
        if event.eventSource == self.items[0] and hasattr(self, "viewer"):
            # L'original utilise event.newValue pour rafraîchir. Nous allons faire un rafraîchissement complet.
            self.viewer.refresh()

    def entries(self):
        if self.__realized and hasattr(self, "viewer"):
            return dict(
                firstEntry=self.viewer,
                prerequisites=self.viewer,
                dependencies=self.viewer,
            )
        return dict()


# ... D'autres classes de pages peuvent être ajoutées ici ...
# La classe EditBook est le conteneur principal à onglets (widgets.Notebook en Tkinter, wx.Notebook en wxPython) qui orchestre l'affichage de toutes les pages d'édition que nous avons converties (Sujet, Dates, Catégories, etc.).
#
# La conversion nécessite de remplacer les appels spécifiques à wxPython (comme self.GetSelection(), self.AddPage, wx.GetTopLevelParent, self.LoadPerspective, self.SavePerspective) par leurs équivalents Tkinter/Ttk.
#
# Puisque nous n'avons pas la définition de widgets.Notebook, je vais me baser sur l'utilisation du widget standard tkinter.ttk.Notebook et adapter les méthodes pour qu'elles correspondent au comportement de l'original.
#
# Voici la conversion de EditBook pour votre fichier editortk.py.
class EditBook(ttk.Notebook):
    """
    Fenêtre principale de l'éditeur dans Task Coach, implémentée avec ttk.Notebook.

    Contient les différentes pages d'édition (sujet, apparence, dates, etc.)
    pour modifier les objets de Task Coach.

    Conteneur principal de l'éditeur dans Task Coach (version Tkinter).
    Équivalent à EditBook de editor.py mais utilisant ttk.Notebook.
    """

    # Attributs de classe qui doivent être définis par les sous-classes (TaskEditBook, NoteEditBook, etc.)
    allPageNames = ["subclass responsibility"]
    domainObject = "subclass responsibility"

    def __init__(self, parent, items, taskFile, settings, items_are_new):
        """Initialise l'éditeur avec les objets à éditer."""
        # Initialisation du Notebook Tkinter
        super().__init__(parent)
        self.items = items
        self.settings = settings
        self.taskFile = taskFile  # Ajout de taskFile pour le rendre accessible
        self.items_are_new = items_are_new
        self.pages = {}

        # self.addPages()
        self.addPages(taskFile, items_are_new)
        self.__load_perspective(items_are_new)
        # Liaison de l'événement de changement d'onglet
        self.bind("<<NotebookTabChanged>>", self.on_page_changed)

        # Rendre le Notebook extensible dans son conteneur parent (si pack/grid est utilisé)
        # Ceci est géré par la classe Editor de niveau supérieur

    def NavigateBook(self, forward):
        """Naviguer entre les différentes pages de l'éditeur."""
        # ttk.Notebook utilise self.index(self.select()) pour l'onglet actif
        curSel = self.index(self.select())
        curSel = curSel + 1 if forward else curSel - 1

        if (
            0 <= curSel < self.winfo_children().__len__()
        ):  # Utilise le nombre de widgets
            self.select(curSel)  # tk.Notebook.select(index)

    def addPages(self):
        """
        Ajoute les différentes pages d'édition à l'éditeur.
        """
        # for page_name in self.allPageNames:
        #     if self.should_create_page(page_name):
        #         page = self.createPage(page_name)
        #         self.add(page, text=page.pageTitle)
        #         self.pages[page_name] = page
        page_names = self.settings.getlist(self.settings_section(), "pages")

        for page_name in page_names:
            page = self.createPage(page_name, task_file, self.items_are_new)
            # Ajout de la page au Notebook
            # Note: Tkinter n'a pas d'icône directement dans l'onglet sans extensions
            # On utilise page.pageTitle pour le texte de l'onglet
            self.add(page, text=page.pageTitle)

            # Adaptation de SetMinSize
        # En Tkinter, c'est généralement le conteneur parent qui gère le redimensionnement.
        # On peut calculer la taille minimale mais l'appliquer est moins direct qu'en wxPython.
        # width, height = self.__get_minimum_page_size()
        # self.SetMinSize((width, self.GetHeightForPageHeight(height))) # Non implémenté

    def getPage(self, page_name):
        """Récupère une page par son nom."""
        index = self.getPageIndex(page_name)
        if index is not None:
            return self.winfo_children()[index]
        return None

    def getPageIndex(self, page_name):
        """Récupère l'index d'une page par son nom."""
        for index, page in enumerate(self.winfo_children()):
            if page_name == getattr(page, "pageName", None):
                return index
        return None

    # Méthodes de calcul de taille (à adapter si nécessaire, simplifiées ici)
    def __get_minimum_page_size(self):
        """Calcule la taille minimale de l'éditeur (simplifié)."""
        # En Tkinter, la taille min est souvent gérée par la configuration du widget
        return 0, 0

    def __pages_to_create(self):
        """Détermine quelles pages doivent être incluses dans l'éditeur."""
        return [
            page_name
            for page_name in self.allPageNames
            if self.__should_create_page(page_name)
        ]

    def should_create_page(self, page_name):
        """
        Vérifie si une page spécifique doit être créée.
        """
        # if len(self.items) > 1:
        #     return self.page_supports_mass_editing(page_name)
        # return True
        return (
            self.__page_supports_mass_editing(page_name)
            if len(self.items) > 1
            else True
        )

    @staticmethod
    def page_supports_mass_editing(page_name):
        """
        Indique si la page prend en charge l'édition de plusieurs éléments.
        """
        return page_name in (
            "subject",
            "dates",
            "progress",
            "budget",
            "appearance",
        )

    def createPage(self, page_name):
        """
        Crée la page appropriée en fonction du nom de la page.
        """
        # if page_name == "subject":
        #     return self.create_subject_page()
        # # Ajoutez d'autres pages selon les besoins
        # else:
        #     # Page par défaut
        #     return Page(self.items, self)
        # Récupération de la classe de la page (simplification sans 'eval'/'globals')
        # On suppose que toutes les classes de Page sont disponibles globalement
        page_class = None

        # Construction des arguments communs
        args = [self.items, self]  # items, parent
        kwargs = {}

        # Logique pour créer chaque type de page
        if page_name == "subject":
            # NOTE : create_subject_page est une méthode distincte
            return self.create_subject_page()

        elif page_name == "dates":
            # Requires items_are_new
            from . import TaskDatesPage  # Supposition d'importation

            page_class = TaskDatesPage
            args.extend(
                [self.settings, self.items_are_new]
            )  # settings, items_are_new

        elif page_name == "prerequisites":
            from . import PrerequisitesPage

            page_class = PrerequisitesPage
            kwargs = {
                "taskFile": task_file,
                "settings": self.settings,
                "settingsSection": f"prerequisiteviewerin{self.domainObject}editor",
            }

        elif page_name == "progress":
            from . import ProgressPage

            page_class = ProgressPage

        elif page_name == "categories":
            from . import CategoriesPage

            page_class = CategoriesPage
            kwargs = {
                "taskFile": task_file,
                "settings": self.settings,
                "settingsSection": f"categoryviewerin{self.domainObject}editor",
            }

        elif page_name == "budget":
            from . import BudgetPage

            page_class = BudgetPage

        elif page_name == "effort":
            from . import EffortPage

            page_class = EffortPage
            kwargs = {
                "taskFile": task_file,
                "settings": self.settings,
                "settingsSection": f"effortviewerin{self.domainObject}editor",
            }

        elif page_name == "notes":
            from . import NotesPage

            page_class = NotesPage
            kwargs = {
                "taskFile": task_file,
                "settings": self.settings,
                "settingsSection": f"noteviewerin{self.domainObject}editor",
            }

        elif page_name == "attachments":
            from . import AttachmentsPage

            page_class = AttachmentsPage
            kwargs = {
                "taskFile": task_file,
                "settings": self.settings,
                "settingsSection": f"attachmentviewerin{self.domainObject}editor",
            }

        elif page_name == "appearance":
            from . import TaskAppearancePage

            page_class = TaskAppearancePage

        if page_class:
            return page_class(*args, **kwargs)

        # Retourne une page de base si la page n'est pas trouvée
        # (devrait être remplacé par une gestion d'erreur appropriée)
        return Page(
            self.items,
            self,
            self.settings,
            pageName=page_name,
            pageTitle=_("Erreur Page"),
        )

    def create_subject_page(self):
        """
        Crée la page sujet pour modifier le titre de l'objet.
        """
        return SubjectPage(self.items, self, self.settings)

    def on_page_changed(self, event):
        """
        Gère les événements de changement de page.
        """
        # Récupérer l'index de la page sélectionnée
        # selected_index = self.index(self.select())
        current_index = self.index(self.select())

        # Récupérer l'objet Page
        # Les pages sont stockées comme les enfants du Notebook
        selected_page = self.winfo_children()[current_index]

        # Appeler la méthode selected() sur la page active
        # if selected_index < len(self.pages):
        #     # Notifier la page qu'elle a été sélectionnée
        #     for page in self.pages.values():
        #         page.selected()
        if hasattr(selected_page, "selected"):
            selected_page.selected()

        # if operating_system.isMac(): # Non pertinent pour Tkinter dans ce contexte simple
        #     wx.GetTopLevelParent(self).Raise()

    def setFocus(self, column_name):
        """
        Définit le focus sur un contrôle spécifique sur une page spécifique.
        """
        # for page in self.pages.values():
        #     if column_name in page.entries():
        #         # Sélectionner la page
        #         self.select(page)
        #         page.setFocusOnEntry(column_name)
        #         break
        page_index = 0

        # 1. Trouver l'index de la page qui contient la colonne (l'entrée)
        for index in range(self.index("end")):
            page = self.winfo_children()[index]
            if column_name in getattr(page, "entries", lambda: {})():
                page_index = index
                break

        # 2. Sélectionner la page
        self.select(page_index)

        # 3. Définir le focus sur le contrôle de l'entrée dans la page
        selected_page = self.winfo_children()[page_index]
        if hasattr(selected_page, "setFocusOnEntry"):
            selected_page.setFocusOnEntry(column_name)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        """Vérifie si un élément donné est en cours de modification ou si l'un de ses enfants est en cours de modification."""
        ancestors = []
        for item in self.items:
            ancestors.extend(item.ancestors())
        return targetItem in self.items + ancestors

    def perspective(self):
        """Renvoie la configuration de mise en page enregistrée (perspective)."""
        # La gestion de perspective est complexe en Tkinter, nous simplifions en retournant une chaîne basée sur les paramètres.
        return self.settings.gettext(self.settings_section(), "perspective")

    def __load_perspective(self, items_are_new=False):
        """Charge la configuration de mise en page enregistrée pour l'éditeur (simplifié)."""
        perspective = self.perspective()

        current_page_index = 0

        # Logique de sélection de page
        if items_are_new:
            # Pour les nouveaux éléments, commencez par la page sujet.
            current_page_index = self.getPageIndex("subject") or 0
        elif perspective:
            # Tentative d'extraire l'index de la page actuelle à partir de la perspective
            try:
                # Dans wxPython, perspective.split("@")[0].split("+")[1].split(",")[0] est l'index
                # Simplification : nous lisons le dernier index enregistré dans les settings, si possible
                # Ou on se contente de 0
                pass
            except (IndexError, ValueError):
                current_page_index = 0

        self.select(current_page_index)

        # Définir le focus sur la page active et appeler selected()
        if self.winfo_children():
            current_page = self.winfo_children()[current_page_index]
            current_page.focus_set()  # Définit le focus Tkinter
            if hasattr(current_page, "selected"):
                current_page.selected()

            for idx in range(self.index("end")):
                page = self.winfo_children()[idx]
                # Appeler selected() si la page est affichée (simplification: toutes sont affichées)
                if hasattr(page, "selected"):
                    page.selected()

    def __save_perspective(self):
        """Enregistre la configuration de mise en page actuelle pour une utilisation ultérieure (simplifié)."""
        page_names = [
            self.winfo_children()[index].pageName
            for index in range(self.index("end"))
        ]
        section = self.settings_section()

        # Sauvegarde de l'état actuel de l'onglet sélectionné
        current_index = self.index(self.select())
        # Enregistrement des données (perspective est une chaîne complexe en wxPython, ici on simplifie)

        # Tkinter n'a pas de LoadPerspective/SavePerspective direct. On sauve les noms de page et l'index actif.
        self.settings.settext(
            section, "perspective", f"active_page={current_index}"
        )
        self.settings.setlist(section, "pages", page_names)

    def settings_section(self):
        """Renvoie le nom de la section des paramètres pour la configuration actuelle de l'éditeur."""
        section = self.__settings_section_name()
        if not self.settings.has_section(section):
            self.__create_settings_section(section)
        return section

    def __settings_section_name(self):
        """Renvoie le nom de la section de ce bloc-notes."""
        page_names = self.__pages_to_create()
        sorted_page_names = "_".join(sorted(page_names))
        return f"{self.domainObject}dialog_with_{sorted_page_names}"

    def __create_settings_section(self, section):
        """Crée une nouvelle section de paramètres si elle n'existe pas."""
        self.settings.add_section(section)
        # Initialisation des options
        initial_settings = dict(
            perspective="",
            pages=str(self.__pages_to_create()),
            size="(-1, -1)",
            position="(-1, -1)",
            maximized="False",
        )
        for option, value in initial_settings.items():
            self.settings.init(section, option, value)

    def close_edit_book(self):
        """
        Ferme l'éditeur et libère les ressources.

        Ferme toutes les pages du livre d'édition et enregistre la mise en page actuelle.
        """
        # for page in self.pages.values():
        #     page.close()
        for page in self.winfo_children():
            if hasattr(page, "close"):
                page.close()  # Appelle la méthode close() de la classe Page

        self.__save_perspective()


class TaskEditBook(EditBook):
    """
    Classe d'édition spécifique pour les tâches.
    """

    allPageNames = [
        "subject",
        "dates",
        "prerequisites",
        "progress",
        "categories",
        "budget",
        "effort",
        "notes",
        "attachments",
        "appearance",
    ]
    domainObject = "task"

    def create_subject_page(self):
        """
        Méthode pour créer les pages de l'éditeur.

        Returns :
            Une instance de TaskSubjectPage avec self.items, self, et self.settings.
        """
        return TaskSubjectPage(self.items, self, self.settings)


class CategoryEditBook(EditBook):
    """
    Classe d'édition spécifique pour les catégories.
    """

    allPageNames = ["subject", "notes", "attachments", "appearance"]
    domainObject = "category"

    def create_subject_page(self):
        return CategorySubjectPage(self.items, self, self.settings)


class AttachmentEditBook(EditBook):
    """
    Classe d'édition spécifique pour les pièces jointes.
    """

    allPageNames = ["subject", "notes", "appearance"]
    domainObject = "attachment"

    def create_subject_page(self):
        return AttachmentSubjectPage(self.items, self, self.settings)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        return targetItem in self.items


class NoteEditBook(EditBook):
    """
    Classe d'édition spécifique pour les notes.

    Cette classe hérite de `EditBook` et fournit des pages d'édition spécifiques aux notes, telles que :
        - Sujet
        - Catégories
        - Pièces jointes
        - Apparence
    """

    allPageNames = ["subject", "categories", "attachments", "appearance"]
    domainObject = "note"


# L'EffortEditBook est une classe intéressante car, malgré son nom, elle hérite de Page (et non de EditBook) et agit comme un formulaire d'édition complet pour un effort, sans utiliser d'onglets. C'est un conteneur qui organise de nombreux widgets complexes pour la sélection de tâches et l'édition des heures de début/fin.
#
class EffortEditBook(Page):
    """
    Éditeur spécialisé pour l'édition des entrées d'effort (utilise Page et Grid).
    Hérite de la classe Page de base et ajoute des fonctionnalités spécifiques pour modifier les détails de l'effort.
    """

    domainObject = "effort"
    columns = 3  # Utilisation de 3 colonnes pour la mise en page Tkinter Grid

    def __init__(
        self,
        parent,
        efforts,
        taskFile,
        settings,
        items_are_new,
        *args,
        **kwargs,
    ):  # pylint: disable=W0613
        """Initialise l'éditeur avec les efforts et le fichier de tâches donnés."""
        self._descriptionSync = None
        self._descriptionEntry = None
        self._effortList = taskFile.efforts()

        # Initialisation de la liste des tâches
        task_list = taskFile.tasks()
        self._taskList = task.TaskList(task_list)
        self._taskList.extend(
            [
                effort.task()
                for effort in efforts
                if effort.task() not in task_list
            ]
        )
        self._settings = settings
        self._taskFile = taskFile

        # Initialisation de la classe de base (Page)
        super().__init__(efforts, parent, *args, **kwargs)

        # En Tkinter, l'appel pub.subscribe doit être adapté ou mocké.
        # pub.subscribe(self.__onChoicesConfigChanged, "settings.feature.sdtcspans_effort")

        self.addEntries()  # Appel des entrées après l'initialisation

    def __onChoicesConfigChanged(self, value=""):
        """Gère le changement de configuration des options de temps relatif pour l'heure d'arrêt."""
        # Mock : Appelle la méthode si elle existe
        if hasattr(self, "_stopDateTimeEntry"):
            self._stopDateTimeEntry.LoadChoices(value)

    def getPage(self, pageName):  # pylint: disable=W0613
        return None  # Un EffortEditBook n'est pas un notebook/onglets

    def settings_section(self):
        """Renvoie la section des paramètres pour la boîte de dialogue d'effort."""
        return "effortdialog"

    def perspective(self):
        """Renvoie la perspective de la boîte de dialogue d'effort."""
        return "effort dialog perspective"

    def addEntries(self):
        """Ajoute les différentes entrées (tâche, heure de début, heure d'arrêt, description) à l'éditeur."""
        self.__add_task_entry()
        self.__add_start_and_stop_entries()
        self.addDescriptionEntry()

        # Configurer le grid pour que la description s'étende
        self.grid_columnconfigure(self.columns - 1, weight=1)
        self.grid_rowconfigure(self._next_row - 1, weight=1)

    def __add_task_entry(self):
        """Ajoute l'entrée de sélection de tâche et le bouton d'édition."""
        # Utilisation d'un cadre pour contenir l'entrée de tâche et le bouton d'édition
        panel = ttk.Frame(self)

        current_task = self.items[0].task()
        self._taskEntry = entry.TaskEntry(
            panel,
            rootTasks=self._taskList.rootItems(),
            selectedTask=current_task,
        )

        # Synchronisation d'attributs (mockée ou réutilisée)
        self._taskSync = attributesync.AttributeSync(
            "task",
            self._taskEntry,
            current_task,
            self.items,
            command.EditTaskCommand,
            event_name="<<TaskEntryChanged>>",  # Adaptation Tkinter
            domain_event_type=self.items[0].taskChangedEventType(),
        )

        edit_task_button = ttk.Button(
            panel, text=_("Edit task"), command=self.onEditTask
        )

        # Mise en page du panel interne (simulant un BoxSizer Horizontal)
        self._taskEntry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        edit_task_button.pack(side=tk.RIGHT, padx=5)  # padx pour l'espacement
        panel.grid_columnconfigure(
            0, weight=1
        )  # S'assurer que l'entrée s'étend

        # Utilisation de la méthode addEntry de Page (qui utilise Grid)
        self.addEntry(_("Task"), panel, flags=[None, tk.NSEW, tk.NSEW])

    def __add_start_and_stop_entries(self):
        """Ajoute les entrées d'heure de début et d'arrêt, y compris les options de temps relatif."""
        # Arguments pour DateTimeEntry
        date_time_entry_kw_args = dict(showSeconds=True)

        # Entrée Heure de début
        current_start_date_time = self.items[0].getStart()
        self._startDateTimeEntry = entry.DateTimeEntry(
            self,
            self._settings,
            current_start_date_time,
            noneAllowed=False,
            showRelative=True,
            **date_time_entry_kw_args,
        )
        # Pas d'équivalent direct pour HideRelativeButton, on l'ignore ou on le mocke.
        # wx.CallAfter(self._startDateTimeEntry.HideRelativeButton)

        self._startDateTimeSync = attributesync.AttributeSync(
            "getStart",
            self._startDateTimeEntry,
            current_start_date_time,
            self.items,
            command.EditEffortStartDateTimeCommand,
            event_name="<<DateTimeEntryChanged>>",
            domain_event_type=self.items[0].startChangedEventType(),
            callback=self.__onStartDateTimeChanged,
        )
        self._startDateTimeEntry.bind(
            "<<DateTimeEntryChanged>>", self.onDateTimeChanged
        )

        start_from_last_effort_button = (
            self.__create_start_from_last_effort_button()
        )
        self.addEntry(
            _("Start"),
            self._startDateTimeEntry,
            start_from_last_effort_button,
            flags=[tk.W, tk.NSEW, tk.W],  # Adaptation des flags
        )

        # Entrée Heure d'arrêt
        current_stop_date_time = self.items[0].getStop()
        self._stopDateTimeEntry = entry.DateTimeEntry(
            self,
            self._settings,
            current_stop_date_time,
            noneAllowed=True,
            showRelative=True,
            units=[
                (_("Minute(s)"), 60),
                (_("Hour(s)"), 3600),
                (_("Day(s)"), 24 * 3600),
                (_("Week(s)"), 7 * 24 * 3600),
            ],
            **date_time_entry_kw_args,
        )

        self._stopDateTimeSync = attributesync.AttributeSync(
            "getStop",
            self._stopDateTimeEntry,
            current_stop_date_time,
            self.items,
            command.EditEffortStopDateTimeCommand,
            event_name="<<DateTimeEntryChanged>>",
            domain_event_type=self.items[0].stopChangedEventType(),
            callback=self.__onStopDateTimeChanged,
        )
        self._stopDateTimeEntry.bind(
            "<<DateTimeEntryChanged>>", self.onStopDateTimeChanged
        )

        stop_now_button = self.__create_stop_now_button()
        self._invalidPeriodMessage = self.__create_invalid_period_message()

        self.addEntry(
            _("Stop"),
            self._stopDateTimeEntry,
            stop_now_button,
            flags=[tk.W, tk.NSEW, tk.W],
        )

        # Mise à jour et message d'erreur
        self.__onStartDateTimeChanged(current_start_date_time)
        self._stopDateTimeEntry.LoadChoices(
            self._settings.get("feature", "sdtcspans_effort")
        )

        # MOCK : La liaison EVT_TIME_CHOICES_CHANGE est ignorée car c'est une fonctionnalité wxPython complexe
        # self._stopDateTimeEntry.bind(sdtc.EVT_TIME_CHOICES_CHANGE, self.__onChoicesChanged)

        self.addEntry(
            "", self._invalidPeriodMessage
        )  # Message d'erreur sans label

    def __onStartDateTimeChanged(self, value):
        """Met à jour le point de départ des options de temps relatif pour l'heure d'arrêt."""
        self._stopDateTimeEntry.SetRelativeChoicesStart(start=value)

    def __create_start_from_last_effort_button(self):
        """Crée un bouton pour démarrer l'effort à partir du dernier effort arrêté."""
        button = ttk.Button(
            self,
            text=_("Start tracking from last stop time"),
            command=self.onStartFromLastEffort,
        )
        if self._effortList.maxDateTime() is None:
            button.configure(state=tk.DISABLED)  # Désactiver le bouton
        return button

    def __create_stop_now_button(self):
        """Crée un bouton pour arrêter l'effort en cours."""
        button = ttk.Button(
            self, text=_("Stop tracking now"), command=self.onStopNow
        )
        return button

    def __create_invalid_period_message(self):
        """Crée un message à afficher si l'heure de début est après l'heure d'arrêt."""
        text = ttk.Label(self, text="", foreground="red")
        # En Tkinter, il est plus simple de changer la couleur que la police pour un statut.
        # font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        # font.SetWeight(wx.FONTWEIGHT_BOLD)
        # text.SetFont(font)
        return text

    def onStartFromLastEffort(self, event=None):
        """Gère l'événement de démarrage de l'effort depuis le dernier effort arrêté."""
        maxDateTime = self._effortList.maxDateTime()
        if self._startDateTimeEntry.GetValue() != maxDateTime:
            self._startDateTimeEntry.SetValue(self._effortList.maxDateTime())
            # Déclenche la synchronisation manuellement après SetValue (l'entrée TK mockée ne le fait pas automatiquement)
            self._startDateTimeSync.onAttributeEdited(event)
        self.onDateTimeChanged(event)

    def onStopNow(self):
        """Gère l'événement d'arrêt de l'effort en cours."""
        command.StopEffortCommand(self._effortList, self.items).do()

    def onStopDateTimeChanged(self, event=None):
        """Gère les modifications apportées à l'heure d'arrêt."""
        self.onDateTimeChanged(event)

    def __onStopDateTimeChanged(self, new_value):
        """Force la vérification de l'heure de début pour ne pas être après l'heure d'arrêt."""
        # Ceci est une commande de vérification dans l'original
        command.EditEffortStartDateTimeCommand(
            None, self.items, newValue=self._startDateTimeEntry.GetValue()
        ).do()

    def onDateTimeChanged(self, event=None):
        """Gère les modifications apportées à l'heure de début ou de fin et met à jour le message de période invalide."""
        # event.Skip() # Non pertinent en Tkinter
        self.__update_invalid_period_message()

    def __update_invalid_period_message(self):
        """Met à jour le message de période invalide en fonction des heures de début et de fin."""
        message = (
            ""
            if self.__is_period_valid()
            else _("Warning: start must be earlier than stop")
        )
        self._invalidPeriodMessage.config(text=message)

    def __is_period_valid(self):
        """Indique si la période actuelle est valide."""
        try:
            # Récupérer les valeurs de l'entrée (mockées ou réelles)
            start_value = self._startDateTimeEntry.GetValue()
            stop_value = self._stopDateTimeEntry.GetValue()
            # Si stop_value est None (pas d'heure d'arrêt), la période est valide
            if stop_value is None:
                return True
            # Comparer (nécessite que les mocks retournent des objets comparables, comme datetime)
            return start_value < stop_value
        except AttributeError:
            return True  # Entries not created yet

    def onEditTask(self):
        """Ouvre l'éditeur de tâches pour la tâche sélectionnée."""
        task_to_edit = self._taskEntry.GetValue()
        # MOCK : TaskEditor doit être défini quelque part (TaskEditor(root, [task_to_edit], ...))
        # from . import TaskEditor # Importation mockée
        # TaskEditor(
        #     None, [task_to_edit], self._settings, self._taskFile
        # ).show()
        # Pour le mock, on simule l'action avec un message de console.
        print(
            f"Ouverture de l'éditeur pour la tâche: {task_to_edit.subject()}"
        )

    def addDescriptionEntry(self):
        # pylint: disable=W0201
        """Ajoute l'entrée de description."""

        def combined_description(items):
            distinctDescriptions = set(item.description() for item in items)
            if len(distinctDescriptions) == 1 and distinctDescriptions.pop():
                return items[0].description()
            lines = ["[%s]" % _("Edit to change all descriptions")]
            lines.extend(
                item.description() for item in items if item.description()
            )
            return "\n\n".join(lines)

        current_description = (
            self.items[0].description()
            if len(self.items) == 1
            else combined_description(self.items)
        )
        self._descriptionEntry = widgetstk.textctrltk.MultiLineTextCtrl(
            self, current_description
        )
        # La gestion des polices est complexe en Tkinter et est ignorée pour l'instant.

        self._descriptionSync = attributesync.AttributeSync(
            "description",
            self._descriptionEntry,
            current_description,
            self.items,
            command.EditDescriptionCommand,
            event_name="<FocusOut>",  # wx.EVT_KILL_FOCUS équivalent Tkinter
            domain_event_type=self.items[0].descriptionChangedEventType(),
        )
        self.addEntry(_("Description"), self._descriptionEntry, growable=True)

    def setFocus(self, column_name):
        """Définit le focus sur une entrée spécifique."""
        self.setFocusOnEntry(column_name)

    def isDisplayingItemOrChildOfItem(self, item):
        """Détermine si un élément donné est en cours de modification."""
        if hasattr(item, "setTask"):
            return self.items[0] == item  # Effort régulier
        else:
            return item.mayContain(
                self.items[0]
            )  # Effort composite (tâche/catégorie)

    def entries(self):
        """Renvoie les entrées clés de l'éditeur."""
        return dict(
            firstEntry=getattr(self, "_startDateTimeEntry", None),
            task=getattr(self, "_taskEntry", None),
            period=getattr(self, "_stopDateTimeEntry", None),
            description=getattr(self, "_descriptionEntry", None),
            timeSpent=getattr(self, "_stopDateTimeEntry", None),
            revenue=getattr(self, "_taskEntry", None),
        )

    def close_edit_book(self):
        """Ferme l'éditeur sans actions spécifiques."""
        pass


#  La classe Editor sert de gestionnaire de fenêtre de niveau supérieur, remplaçant le wx.Dialog de wxPython par un tk.Toplevel de Tkinter. Elle orchestre le cycle de vie de la fenêtre d'édition, gère les événements de fermeture et les raccourcis clavier.
#
# Voici la conversion de la classe Editor en utilisant tk.Toplevel, ainsi que les adaptations nécessaires pour les dépendances wxPython. J'ai inclus les classes d'éditeurs spécialisés (TaskEditor, EffortEditor, etc.) pour maintenir la cohérence structurelle.
# class Editor(tk.Toplevel):
class Editor(BalloonTipManager, widgetstk.dialogtk.Dialog):
    """
    Fenêtre principale de l'éditeur dans Task Coach (version Tkinter).

    Classe de base pour les éditeurs dans Task Coach (implémentée avec tk.Toplevel).
    Classe de base pour toutes les fenêtres d'édition.
    Fournit un cadre pour gérer le processus d'édition et les événements.
    Tkinter n'a pas de concept de "dialogue" modale comme wxPython,
    nous utilisons `Toplevel` pour créer une nouvelle fenêtre.
    """

    # @classmethod
    # def EditBookClass(cls, *args) -> str:
    #     """Doit être remplacé par la classe EditBook spécialisée (TaskEditBook, EffortEditBook, etc.)."""
    #     return "Subclass responsibility"
    plural_title = _("Multiple items")
    singular_title = _("%s")
    EditBookClass = None  # À définir dans les sous-classes

    # def __init__(self, parent, items, **kwargs):
    def __init__(
        self, parent, items, settings, container, task_file, *args, **kwargs
    ):
        """Initialise l'éditeur."""
        # super().__init__(parent, **kwargs)
        super().__init__(parent)
        self.parent = parent
        self._items = items
        self._settings = settings
        self._taskFile = task_file
        self.__items_are_new = kwargs.pop("items_are_new", False)
        column_name = kwargs.pop("columnName", "")
        self.__timer = None
        self.__timer_id = None

        self.transient(
            parent
        )  # Rendre la fenêtre modale par rapport au parent
        self.grab_set()  # Rendre la fenêtre modale

        # 1. Définir le titre
        # self.title(self.get_title())
        self.title(self.__title())
        self.geometry("600x400")

        # # Le concept de "notebook" est géré par le widget ttk.Notebook.
        # self.notebook = ttk.Notebook(self)
        # self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        #
        # 2. Créer l'intérieur (EditBook/EffortEditBook)
        # # Création des pages
        # self.pages = {}
        # for item in self._items:
        #     page_frame = self.EditBookClass(self.notebook, item)
        #     self.notebook.add(page_frame, text=page_frame.pageTitle)
        #     self.pages[item.subject()] = page_frame
        # Création du contenu principal
        # self.create_interior()
        self.createInterior()

        # self.SetTitle()

        # 3. Définir le focus initial
        # Logique simplifiée pour trouver le nom de colonne de la page sélectionnée/initiale
        if (
            not column_name
            and hasattr(self._interior, "getPageCount")
            and self._interior.index("end") > 0
        ):
            try:
                selected_index = self._interior.index(self._interior.select())
                column_name = self._interior.winfo_children()[
                    selected_index
                ].pageName
            except Exception:
                column_name = "subject"
        else:
            column_name = column_name or "subject"

        if column_name:
            # On appelle setFocus sur le Toplevel, qui le délègue à l'intérieur
            self.after(
                0, lambda: self._interior.setFocus(column_name)
            )  # Utilisation de after pour assurer que le widget est mappé

        # 4. Gérer les événements de notification (TaskCoach Publisher)
        patterns.Publisher().registerObserver(
            self.on_item_removed,
            eventType=container.removeItemEventType(),
            eventSource=container,
        )
        if len(self._items) == 1:
            patterns.Publisher().registerObserver(
                self.on_subject_changed,
                eventType=self._items[0].subjectChangedEventType(),
                eventSource=self._items[0],
            )

        # Boutons OK/Cancel
        self.create_buttons()

        # # On gère la fermeture de la fenêtre
        # self.protocol("WM_DELETE_WINDOW", self.on_close)
        # 5. Gérer l'événement de fermeture de la fenêtre
        # WM_DELETE_WINDOW est l'événement pour le bouton X de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self.on_close_editor)

        # 6. Minuterie macOS (adaptée à Tkinter.after)
        if operating_system.isMac():
            self.__timer_id = IdProvider.get()
            self.__timer = self.after(
                1000, self.__on_timer
            )  # Démarrer la minuterie Tkinter

        # Centrer sur le parent
        self.center_on_parent()
        # 7. Centrage de la fenêtre (CentreOnParent)
        self.update_idletasks()
        self.__center_on_parent(parent)

        # 8. Créer les commandes UI et le suivi de dimension
        self.__create_ui_commands()
        self.__dimensions_tracker = (
            windowdimensionstrackertk.WindowSizeAndPositionTracker(
                self, settings, self._interior.settings_section()
            )
        )

    def create_interior(self):
        """
        Crée l'intérieur de la boîte de dialogue.

        Crée et retourne l'instance de EditBook ou EffortEditBook appropriée.
        """
        # self._interior = self.EditBookClass(
        #     self, self._items, self._taskFile, self._settings, self.items_are_new
        # )
        # self._interior.pack(expand=True, fill="both", padx=10, pady=10)
        self._interior = self.createInterior()
        self._interior.pack(fill=tk.BOTH, expand=True)

    def createInterior(self):
        """Crée et retourne l'instance de EditBook ou EffortEditBook appropriée."""
        # Note: self.EditBookClass doit être défini dans les sous-classes (TaskEditor, EffortEditor, etc.)
        return self.EditBookClass(
            self,  # Le parent pour l'intérieur est l'instance Editor
            self._items,
            self._taskFile,
            self._settings,
            self.__items_are_new,
        )

    def create_buttons(self):
        """
        Crée les boutons OK/Cancel.
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        ok_button = ttk.Button(button_frame, text=_("OK"), command=self.on_ok)
        ok_button.pack(side="right", padx=(5, 0))

        cancel_button = ttk.Button(
            button_frame, text=_("Cancel"), command=self.on_cancel
        )
        cancel_button.pack(side="right")

    def __create_ui_commands(self):
        """Crée des commandes d'interface utilisateur et les lie aux raccourcis clavier."""

        self.__new_effort_id = IdProvider.get()

        # 1. Créer les instances de commande (Mock/Adapter)
        self.__undo_command = uicommandtk.EditUndo()
        self.__redo_command = uicommandtk.EditRedo()

        effort_page = self._interior.getPage("effort")
        effort_viewer = getattr(effort_page, "viewer", None)

        self.__new_effort_command = uicommandtk.EffortNew(
            viewer=effort_viewer,
            taskList=self._taskFile.tasks(),
            effortList=self._taskFile.efforts(),
            settings=self._settings,
        )

        # 2. Définir les raccourcis clavier Tkinter (bind_all pour les commandes globales)
        # <Command> = Ctrl sur Win/Linux, Cmd sur macOS
        # Utilisation d'une lambda pour exécuter la commande mockée
        self.bind_all(
            "<Command-z>", lambda event: self.__undo_command.execute()
        )
        self.bind_all(
            "<Command-y>", lambda event: self.__redo_command.execute()
        )
        self.bind_all(
            "<Command-e>", lambda event: self.__new_effort_command.execute()
        )

    def SetTitle(self):
        """Met à jour le titre de la fenêtre."""
        if len(self._items) > 1:
            title = self.plural_title
        else:
            title = self.singular_title % self._items[0].subject()
        self.title(title)

    def get_title(self):
        """
        Retourne le titre approprié pour l'éditeur.
        """
        if len(self._items) > 1:
            return self.plural_title
        else:
            return self.singular_title % self._items[0].subject()

    def center_on_parent(self):
        """
        Centre la fenêtre sur son parent.
        """
        self.update_idletasks()

        # Obtenir les dimensions
        width = self.winfo_width()
        height = self.winfo_height()

        # Calculer la position pour centrer
        x = (
            self.master.winfo_x()
            + (self.master.winfo_width() // 2)
            - (width // 2)
        )
        y = (
            self.master.winfo_y()
            + (self.master.winfo_height() // 2)
            - (height // 2)
        )

        self.geometry(f"{width}x{height}+{x}+{y}")

    def __center_on_parent(self, parent):
        """Centre la fenêtre de l'éditeur sur la fenêtre parente."""
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        parent_x = (
            parent.winfo_rootx() if parent else self.winfo_screenwidth() // 2
        )
        parent_y = (
            parent.winfo_rooty() if parent else self.winfo_screenheight() // 2
        )
        parent_width = (
            parent.winfo_width() if parent else self.winfo_screenwidth()
        )
        parent_height = (
            parent.winfo_height() if parent else self.winfo_screenheight()
        )

        # Centrage sur le parent
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        # Assurer que la fenêtre est dans l'écran
        x = max(0, x)
        y = max(0, y)

        self.geometry(f"+{x}+{y}")

    def __on_timer(self):
        """Gère l'événement de minuterie (équivalent macOS)."""
        # winfo_ismapped() retourne True si la fenêtre est affichée (mappée)
        if not self.winfo_ismapped():
            self.on_close_editor()
        elif self.__timer is not None:
            # Replanifier le timer Tkinter
            self.__timer = self.after(1000, self.__on_timer)

    def on_ok(self):
        """
        Gère le clic sur OK - applique les changements.
        """
        # Ici vous implémenterez la logique pour sauvegarder les changements
        self.destroy()

    def on_cancel(self):
        """
        Gère le clic sur Cancel - annule les changements.
        """
        self.destroy()

    def on_close(self):
        """Gère la fermeture de la boîte de dialogue."""
        # # Ici, nous mettrions à jour l'objet de domaine avant de fermer.
        # # Pour cet exemple simple, nous n'avons que le sujet.
        # for item in self._items:
        #     # Assurez-vous que la page correspondante existe avant de l'appeler.
        #     if item.subject() in self.pages:
        #         self.pages[item.subject()].update_item_value()
        self._interior.close_edit_book()

        self.destroy()  # Fermer la fenêtre

    def on_close_editor(self, event=None):
        """Gère la fermeture de l'éditeur."""
        # 1. Fermer l'intérieur et sauvegarder la perspective
        self._interior.close_edit_book()

        # 2. Arrêter le timer si actif
        if self.__timer is not None:
            self.after_cancel(self.__timer)
            IdProvider.put(id_=self.__timer_id)
            self.__timer = None
            self.__timer_id = None

        # 3. Libérer l'ID de la commande
        IdProvider.put(id_=self.__new_effort_id)

        # 4. Nettoyage et destruction des observers
        patterns.Publisher().removeObserver(self.on_item_removed)
        patterns.Publisher().removeObserver(self.on_subject_changed)

        # 5. Fermer la fenêtre Tkinter
        self.destroy()

    # @staticmethod
    def on_activate(self, event=None):
        """Simule l'activation de la fenêtre (non nécessaire en Tkinter)."""
        pass

    def on_item_removed(self, event):
        """Gère l'événement de suppression d'un élément."""
        # Utiliser self.after(0, ...) pour exécuter la vérification après la boucle d'événements courante
        self.after(
            0, lambda: self.__close_if_item_is_deleted(list(event.values()))
        )

    def __close_if_item_is_deleted(self, items):
        """Ferme l'éditeur si l'élément modifié ou un de ses ancêtres est supprimé."""
        for item in items:
            # item not in self._taskFile est la condition pour la suppression
            if (
                self._interior.isDisplayingItemOrChildOfItem(item)
                and item not in self._taskFile
            ):
                self.on_close_editor()
                break

    def on_subject_changed(self, event=None):
        """Gère l'événement de modification du sujet et met à jour le titre de la fenêtre."""
        self.title(self.__title())

    def __title(self):
        """Renvoie le titre approprié pour l'éditeur."""
        return (
            self.plural_title
            if len(self._items) > 1
            else self.singular_title % self._items[0].subject()
        )


class TaskEditor(Editor):
    """Éditeur pour les tâches."""

    plural_title = _("Multiple tasks")
    singular_title = _("%s (task)")
    # NOTE: TaskEditBook doit être définie dans editortk.py et hériter de EditBook
    # EditBookClass = TaskSubjectPage
    EditBookClass = TaskEditBook


class CategoryEditor(Editor):
    """Éditeur pour les catégories."""

    plural_title = _("Multiple categories")
    singular_title = _("%s (category)")
    # NOTE: CategoryEditBook doit être définie
    # EditBookClass = CategorySubjectPage
    EditBookClass = CategoryEditBook


class NoteEditor(Editor):
    """Éditeur pour les notes."""

    plural_title = _("Multiple notes")
    singular_title = _("%s (note)")
    # NOTE: NoteEditBook doit être définie
    # EditBookClass = NoteSubjectPage
    EditBookClass = NoteEditBook


class AttachmentEditor(Editor):
    """Éditeur pour les pièces jointes."""

    plural_title = _("Multiple attachments")
    singular_title = _("%s (attachment)")
    # NOTE: AttachmentEditBook doit être définie
    # EditBookClass = AttachmentSubjectPage
    EditBookClass = AttachmentEditBook


class EffortEditor(Editor):
    """Éditeur pour les efforts (utilise EffortEditBook qui n'a pas d'onglets)."""

    plural_title = _("Multiple efforts")
    singular_title = _("%s (effort)")
    # NOTE: EffortEditBook doit être définie (nous l'avons convertie précédemment)
    # EditBookClass = EffortSubjectPage
    EditBookClass = EffortEditBook


# Un exemple simple d'objet de domaine pour les tests.
class MockDomainItem:
    # def __init__(self, subject):
    def __init__(self, subject, description=""):
        self._subject = subject
        self._description = description

    def subject(self):
        return self._subject

    def description(self):
        return self._description

    def set_subject(self, new_subject):
        print(f"Sujet de {self._subject} mis à jour en {new_subject}")
        self._subject = new_subject

    def set_description(self, new_description):
        self._description = new_description


class MockTask(MockDomainItem):
    def __init__(self, subject, description="", priority=0):
        super().__init__(subject, description)
        self._priority = priority

    def priority(self):
        return self._priority

    def set_priority(self, new_priority):
        self._priority = new_priority


class MockCategory(MockDomainItem):
    def __init__(self, subject, description="", exclusive_subcategories=False):
        super().__init__(subject, description)
        self._exclusive_subcategories = exclusive_subcategories

    def hasExclusiveSubcategories(self):
        return self._exclusive_subcategories


class MockAttachment(MockDomainItem):
    def __init__(self, subject, description="", location=""):
        super().__init__(subject, description)
        self._location = location

    def location(self):
        return self._location

    def set_location(self, new_location):
        self._location = new_location


# Pour exécuter un exemple :
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale

    # Mock settings et taskFile
    class MockSettings:
        def get(self, section, key):
            return ""

    class MockTaskFile:
        pass

    # Créez quelques objets de domaine mock
    # task1 = MockDomainItem("Faire les courses")
    task1 = MockTask("Faire les courses", "Acheter du lait et du pain", 5)
    # task2 = MockDomainItem("Rédiger le rapport")
    task2 = MockTask("Rédiger le rapport", "Rapport mensuel", 8)

    settings = MockSettings()
    task_file = MockTaskFile()

    # Créez un éditeur pour une seule tâche
    # editor_task = TaskEditor(root, [task1])
    editor = TaskEditor(root, [task1], settings, None, task_file)
    # editor_task.mainloop()
    editor.mainloop()

    # Créez un éditeur pour plusieurs tâches
    editor_tasks = TaskEditor(root, [task1, task2])
    editor_tasks.mainloop()
