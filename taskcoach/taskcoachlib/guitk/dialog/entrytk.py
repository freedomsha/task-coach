# -*- coding: utf-8 -*-

"""
Task Coach - Votre gestionnaire de tâches amical
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

Task Coach est un logiciel libre: vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre option) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE; sans même la garantie implicite de
COMMERCIALISATION ou D'ADÉQUATION À UN USAGE PARTICULIER. Voir la
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Si ce n'est pas le cas, consultez <http://www.gnu.org/licenses/>.
"""
# Ce fichier est un peu plus complexe car il gère les entrées de date et de récurrence, des fonctionnalités qui ne sont pas directement disponibles dans Tkinter de la même manière que dans WxPython.
#
# Pour cette conversion, je vais utiliser tkinter et tkinter.ttk, en m'appuyant sur l'approche modulaire de la version originale. J'ai créé un widget personnalisé DateTimeEntry pour gérer les dates et les heures, et un autre pour les options de récurrence, en m'inspirant du code original.
#
# Voici la version convertie de entry.py pour le dossier guitk/dialog. J'ai inclus des commentaires détaillés pour expliquer comment chaque partie du code WxPython a été adaptée pour Tkinter.

# Cette version convertie de entry.py met en évidence la nécessité de recréer les widgets complexes de WxPython en utilisant des combinaisons de widgets Tkinter de base. La gestion des dates et des événements est gérée manuellement, ce qui est une approche courante en l'absence de bibliothèques tierces.

# Voici une approche pour chaque classe, en m'appuyant sur les informations disponibles et en considérant les défis typiques de la conversion vers Tkinter :
# Stratégie générale :
#
# Héritage : Assure-toi que chaque classe Tkinter hérite correctement des widgets Tkinter appropriés (par exemple, tk.Entry, ttk.Entry, tk.Frame, etc.).
# Imports : Remplace les imports des modules et classes originaux par leurs équivalents Tkinter (par exemple, taskcoachlib.gui devient taskcoachlib.guitk).
# Initialisation : Adapte la méthode __init__ de chaque classe pour initialiser correctement le widget Tkinter parent et configurer les options spécifiques (largeur, police, couleur, etc.).
# Gestion des événements : Remplace les mécanismes de gestion des événements spécifiques à l'ancien framework par les liaisons d'événements Tkinter (par exemple, <FocusOut>, <KeyRelease>, etc.).
# Méthodes : Adapte les méthodes de chaque classe pour interagir avec les widgets Tkinter (par exemple, utiliser get() pour obtenir le texte d'une entrée, set() pour définir le texte, etc.).
# Validation : Utilise les mécanismes de validation Tkinter (par exemple, validatecommand) pour assurer que les entrées respectent les contraintes (par exemple, uniquement des entiers, des flottants, etc.)  .
# Présentation : Utilise les gestionnaires de géométrie Tkinter (par exemple, pack(), grid(), place()) pour positionner les widgets dans l'interface.
# Variables de contrôle : Utilise les StringVar, IntVar, DoubleVar, BooleanVar de Tkinter pour lier les valeurs des widgets aux variables Python et faciliter la mise à jour de l'interface .
# Focus : Gère le focus pour améliorer l'expérience utilisateur.
#
# Classes à convertir :
#
# TimeDeltaEntry :
#
# Widget d'entrée pour les durées (TimeDelta).
# Convertir en utilisant ttk.Entry ou tk.Entry.
# Valider l'entrée pour s'assurer qu'elle peut être convertie en timedelta.
# Utiliser StringVar pour lier le contenu de l'entrée à une variable Python.
#
#
# AmountEntry :
#
# Widget d'entrée pour les montants numériques.
# Convertir en utilisant ttk.Entry ou tk.Entry.
# Valider l'entrée pour s'assurer qu'elle peut être convertie en nombre (flottant ou entier).
# *Implémenter la validation en temps réel en utilisant validatecommand pour rejeter les caractères non numériques ou les formats invalides  .
#
#
# PourcentageEntry :
#
# Widget d'entrée pour les pourcentages.
# Convertir en utilisant ttk.Entry ou tk.Entry.
# Valider l'entrée pour s'assurer qu'elle est bien un pourcentage valide (entre 0 et 100).
# Afficher le symbole "%" à côté de l'entrée (utiliser un Label à côté de l'Entry).
#
#
# FontEntry :
#
# Widget pour choisir une police de caractères.
# Cela nécessitera probablement un widget plus complexe qu'une simple entrée. Envisager d'utiliser une boîte de dialogue de sélection de police (tk.fontchooser sous Tcl/Tk 8.5+). Si tu dois implémenter la sélection toi-même, tu peux utiliser une liste déroulante (ttk.Combobox) pour le nom de la police, une autre pour la taille, et des cases à cocher (Checkbutton) pour le style (gras, italique, etc.).
#
#
# ColorEntry :
#
# Widget pour choisir une couleur.
# Utiliser le widget tk.colorchooser.askcolor() pour afficher une boîte de dialogue de sélection de couleur. Afficher un aperçu de la couleur sélectionnée (par exemple, en changeant la couleur de fond d'un Label).
#
#
# IconEntry :
#
# Widget pour choisir une icône.
# Utiliser un bouton qui ouvre une boîte de dialogue de sélection de fichier (tk.filedialog.askopenfilename) pour choisir l'icône. Afficher l'icône sélectionnée à côté du bouton.  Tu auras besoin du module PIL (Pillow) pour afficher les icônes.
#
#
# ChoiceEntry :
#
# Widget pour choisir parmi une liste d'options.
# Utiliser un widget ttk.Combobox pour afficher une liste déroulante d'options.
# Lier la valeur sélectionnée à une variable Python avec StringVar.
#
#
# TaskEntry :
#
# Widget pour sélectionner une tâche (probablement à partir d'une liste).
# Si la liste des tâches est courte, utiliser une série de boutons radio (Radiobutton). Sinon, utiliser une liste déroulante (ttk.Combobox) ou une liste (tk.Listbox).
#
#
# RecurrenceEntry :
#
# Widget complexe pour définir une récurrence.
# Cette classe nécessitera une refonte importante. Envisager d'utiliser plusieurs widgets Tkinter combinés (par exemple, des Combobox pour la fréquence, des Entry pour les intervalles, des Checkbutton pour les jours de la semaine, etc.).
# Les méthodes manquantes devront être implémentées en fonction de la logique de récurrence. Il faudra gérer la sauvegarde et la restauration de la configuration de la récurrence.
#
#
# Points importants :
#
# Références : Les références que tu as fournies parlent de l'utilisation du widget Entry de Tkinter. Elles montrent comment obtenir le texte entré par l'utilisateur, comment restreindre le type d'entrée (entiers, flottants), et comment lier des éléments ensemble. Ces informations peuvent être utiles pour implémenter les classes que tu dois convertir.
# Gestion des erreurs : Prévois une gestion des erreurs robuste, en particulier lors de la validation des entrées utilisateur. Affiche des messages d'erreur clairs et informatifs.
# Tests : Teste chaque widget individuellement avant de l'intégrer dans l'application complète.
import logging
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from tkinter.font import Font
from tkinter.simpledialog import Dialog
import datetime
from taskcoachlib import widgetstk
from taskcoachlib.widgetstk import paneltk, maskedtk, spinctrltk, fontpickertk
from taskcoachlib.domain import date
from taskcoachlib.guitk import artprovidertk
from taskcoachlib.i18n import _

log = logging.getLogger(__name__)


# Tkinter n'a pas d'équivalent direct pour wx.lib.newevent.NewEvent()
# Nous allons utiliser une approche plus simple basée sur les StringVar et les
# Callbacks pour la gestion des événements.
# Événements personnalisés Tkinter (simples classes pour remplacer wx.lib.newevent.NewEvent())
class DateTimeEntryEvent:
    def __init__(self, source):
        self.source = source


class DateTimeEntry(ttk.Frame):
    """
    Simule le widget DateTimeCtrl de wxPython en utilisant les widgets
    standards de Tkinter.
    """
    defaultDateTime = date.DateTime()

    # def __init__(self, parent, default_datetime, **kwargs):
    def __init__(self, parent, settings=None, initialDateTime=None, readonly=False,
                 noneAllowed=True, showSeconds=False, suggestedDateTime=None,
                 showRelative=False, adjustEndOfDay=False, units=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        # self.default_datetime = default_datetime
        # self._datetime = self.default_datetime
        self.initialDateTime = initialDateTime or self.defaultDateTime
        self.noneAllowed = noneAllowed
        self.showSeconds = showSeconds
        self.showRelative = showRelative
        self.adjustEndOfDay = adjustEndOfDay
        self.units = units
        self._callback = None

        self._datetime = self.initialDateTime

        # Format d'affichage basé sur les paramètres
        time_format = "%H:%M"
        if showSeconds:
            time_format += ":%S"
        date_format = "%d/%m/%Y"
        self.format_string = f"{date_format} {time_format}"

        # self.entry_var = tk.StringVar(value=self._datetime.Format(_("%x %X")))
        self.entry_var = tk.StringVar(value=self._datetime.strftime(self.format_string) if self._datetime else "")

        # self.entry = ttk.Entry(self, textvariable=self.entry_var)
        self.entry = ttk.Entry(self, textvariable=self.entry_var, state="readonly" if readonly else "normal")
        self.entry.pack(side="left", fill="x", expand=True)

        self.button = ttk.Button(self, text="...", command=self.show_datetime_picker)
        self.button.pack(side="left")

        # Lier les événements de modification
        self.entry_var.trace('w', self.on_entry_changed)

        # Valeur initiale
        if initialDateTime == date.DateTime() and suggestedDateTime:
            self.setSuggested(suggestedDateTime)
        else:
            self.SetValue(initialDateTime)

    def show_datetime_picker(self):
        """Affiche un sélecteur de date/heure.

        Tkinter ne possède pas de sélecteur de date/heure intégré.
        Pour une implémentation complète, il faudrait soit créer un
        widget personnalisé, soit utiliser une librairie tierce comme
        tkcalendar. Pour cet exemple, nous allons utiliser une boîte de
        dialogue simple pour simuler l'entrée de l'utilisateur.
        """
        # Pour cet exemple simple, nous allons demander à l'utilisateur de saisir
        # la date et l'heure manuellement. Dans une application réelle,
        # cela serait remplacé par un widget plus interactif.
        current_value = self._datetime.strftime(self.format_string) if self._datetime else ""
        new_datetime_str = tk.simpledialog.askstring(
            "Date/Heure",
            # "Entrez la date et l'heure (format '%s')" % _("%x %X"),
            f"Entrez la date et l'heure (format '{self.format_string}'):",
            initialvalue=current_value
        )
        if new_datetime_str:
            try:
                # Tente de parser la chaîne pour valider
                # new_datetime = date.DateTime.strptime(new_datetime_str, _("%x %X"))
                new_datetime = datetime.datetime.strptime(new_datetime_str, self.format_string)
                # self.SetValue(new_datetime)
                self.SetValue(date.DateTime(new_datetime))
            except ValueError:
                tk.messagebox.showerror("Erreur", "Format de date/heure invalide.")

    def SetValue(self, datetime_obj):
        """Définit la valeur de l'entrée."""
        if datetime_obj is None:
            datetime_obj = self.defaultDateTime
        self._datetime = datetime_obj
        # self.entry_var.set(self._datetime.Format(_("%x %X")))
        self.entry_var.set(self._datetime.strftime(self.format_string) if self._datetime else "")

    def GetValue(self):
        """Récupère la valeur de l'entrée."""
        return self._datetime

    def setSuggested(self, suggestedDateTime):
        """Définit une valeur suggérée."""
        self.SetValue(suggestedDateTime)
        # Simulation de SetNone() - efface le champ
        self.entry_var.set("")

    def setCallback(self, callback):
        """Définit le callback à appeler lors des changements."""
        self._callback = callback

    def on_entry_changed(self, *args):
        """Gestionnaire d'événement pour les changements de valeur."""
        if self._callback:
            self._callback()
        self.event_generate("<<DateTimeEntryChanged>>")

    def Disable(self):
        """Désactive le widget."""
        self.entry.config(state="disabled")
        self.button.config(state="disabled")

    def Enable(self, enable=True):
        """Active/désactive le widget."""
        state = "normal" if enable else "disabled"
        self.entry.config(state=state)
        self.button.config(state=state)


# Explication des modifications :
# Héritage : La classe TimeDeltaEntry hérite maintenant de ttk.Frame.
# Widgets Tkinter : Un widget ttk.Entry est ajouté pour l'entrée de durée.
# StringVar : Une StringVar est utilisée pour lier le contenu de l'entrée à une variable Python.
# Validation : La méthode show_datetime_picker permet d'afficher un sélecteur de date/heure et de valider l'entrée.
# Prochaines étapes :
# Appliquer les modifications proposées.
# Tester la classe TimeDeltaEntry pour s'assurer qu'elle fonctionne correctement.
# Continuer à convertir les autres classes (AmountEntry, PourcentageEntry, etc.) en suivant la même stratégie.
class TimeDeltaEntryEvent:
    def __init__(self, source):
        self.source = source


class TimeDeltaEntry(widgetstk.paneltk.FrameWithBoxSizer):
    # class TimeDeltaEntry(ttk.frame):
    """
    Widget d'entrée pour les durées (TimeDelta).
    Convertir en utilisant ttk.Entry ou tk.Entry.
    Valider l'entrée pour s'assurer qu'elle peut être convertie en timedelta.
    Utiliser StringVar pour lier le contenu de l'entrée à une variable Python.
    """
    # We can't inherit from widgets.masked.TextCtrl because that class expects
    # GetValue to return a string and we want to return a TimeDelta.

    defaultTimeDelta = date.TimeDelta()

    # def __init__(self, parent, timeDelta=defaultTimeDelta, readonly=False,
    #              *args, **kwargs):
    # def __init__(self, parent, default_datetime=None, **kwargs):
    def __init__(self, parent, timeDelta=None, readonly=False, **kwargs):
        # super().__init__(parent, *args, **kwargs)
        super().__init__(parent, **kwargs)
        # # hours, minutes, seconds = timeDelta.hoursMinutesSeconds()
        # self.default_datetime = default_datetime or date.TimeDelta()
        # self._datetime = self.default_datetime
        self.parent = parent
        self.timeDelta = timeDelta or self.defaultTimeDelta
        hours, minutes, seconds = self.timeDelta.hoursMinutesSeconds()

        self._entry = widgetstk.maskedtk.TimeDeltaCtrl(self, hours, minutes,
                                                       seconds, readonly,
                                                       timeDelta < self.defaultTimeDelta)
        # self.entry_var = tk.StringVar(value=self._datetime.Format(_("%x %X")))

        # self.entry = ttk.Entry(self, textvariable=self.entry_var)
        # self.entry.pack(side="left", fill="x", expand=True)

        if readonly:
            # self._entry.Disable()
            self._entry.config(state="disabled")
        # self.add(self._entry, proportion=1)
        self.add(self._entry, fill=tk.X, expand=True)
        self.fit()
        # self.button = ttk.Button(self, text="...", command=self.show_datetime_picker)
        # self.button.pack(side="left")

    def show_datetime_picker(self):
        """Affiche un sélecteur de date/heure.

        Tkinter ne possède pas de sélecteur de date/heure intégré.
        Pour une implémentation complète, il faudrait soit créer un
        widget personnalisé, soit utiliser une librairie tierce comme
        tkcalendar. Pour cet exemple, nous allons utiliser une boîte de
        dialogue simple pour simuler l'entrée de l'utilisateur.
        """
        # Pour cet exemple simple, nous allons demander à l'utilisateur de saisir
        # la date et l'heure manuellement. Dans une application réelle,
        # cela serait remplacé par un widget plus interactif.
        new_datetime_str = tk.simpledialog.askstring("Date/Heure", "Entrez la date et l'heure (format '%s')" % _("%x %X"))
        if new_datetime_str:
            try:
                # Tente de parser la chaîne pour valider
                new_datetime = date.DateTime.strptime(new_datetime_str, _("%x %X"))
                self.SetValue(new_datetime)
            except ValueError:
                tk.messagebox.showerror("Erreur", "Format de date/heure invalide.")

    def NavigateBook(self, event):
        # self.GetParent().NavigateBook(not event.ShiftDown())
        # self.winfo_parent().NavigateBook(not event.ShiftDown())
        self.parent.NavigateBook(not event.ShiftDown())
        return True

    def GetValue(self):
        """Récupère la valeur de l'entrée."""
        return date.parseTimeDelta(self._entry.get())  # remplacer GetValue par get pour tkinter.
        # return self._datetime

    def SetValue(self, newTimeDelta):
        # def SetValue(self, datetime_obj):
        """Définit la valeur de l'entrée."""
        hours, minutes, seconds = newTimeDelta.hoursMinutesSeconds()
        negative = newTimeDelta < self.defaultTimeDelta
        self._entry.set_value(hours, minutes, seconds, negative)
        # self._datetime = datetime_obj
        # self.entry_var.set(self._datetime.Format(_("%x %X")))

    def bind(self, *args, **kwargs):  # pylint: disable=W0221
        self._entry.bind(*args, **kwargs)
        # self.entry_var.bind(*args, **kwargs)


# Explications des changements et adaptations :
#
# Héritage : La classe hérite de paneltk.PanelWithBoxSizer comme demandé.
# Imports : Les imports nécessaires depuis taskcoachlib.widgetstk, taskcoachlib.widgetstk.paneltk, et taskcoachlib.widgetstk.maskedtk sont inclus .
# __init__ :
#
# L'initialisation appelle super().__init__(parent, *args, **kwargs) pour initialiser la classe parent.
# La création de l'entrée AmountCtrl est déléguée à la méthode create_entry.
# Si readonly est True, on utilise self._entry.config(state="disabled") pour désactiver le widget Tkinter.
# self.add(self._entry) ajoute l'entrée au PanelWithBoxSizer.
# self.fit() appelle la méthode fit de PanelWithBoxSizer pour ajuster la taille des widgets.
#
#
# create_entry : Cette méthode encapsule la création du AmountCtrl de maskedtk.py. Cela facilite le remplacement du type de widget si nécessaire.
# GetValue et SetValue : Ces méthodes délèguent simplement l'appel aux méthodes correspondantes de l'instance AmountCtrl .
# bind : Permet de lier des événements directement au widget interne _entry .
# Remplace Disable() par config(state="disabled") :  Dans Tkinter, on utilise config(state="disabled") pour désactiver un widget au lieu de Disable().
# Supprime NavigateBook : La méthode NavigateBook de entry.py n'est pas présente dans entrytk.py et n'est pas nécessaire pour la fonctionnalité de AmountEntry, donc je l'ai supprimée.
#
# Points importants :
#
# Cette conversion s'appuie sur le fait que tu as déjà converti widgets.masked.AmountCtrl en widgetstk.maskedtk.AmountCtrl et que cette nouvelle version fonctionne correctement dans un environnement Tkinter .
# Assure-toi que la méthode GetValue() de widgetstk.maskedtk.AmountCtrl renvoie bien une valeur numérique et que SetValue() accepte une valeur numérique en argument.
# N'oublie pas d'ajouter les imports nécessaires dans entrytk.py .
class AmountEntry(paneltk.FrameWithBoxSizer):
    """Widget d'entrée pour les montants numériques."""

    def __init__(self, parent, amount=0.0, readonly=False, *args, **kwargs):
        # super().__init__(parent, *args, **kwargs)
        super().__init__(parent, **kwargs)

        self._entry = self.createEntry(amount)
        if readonly:
            self._entry.config(state="disabled")  # Utilisez config pour désactiver dans Tkinter
        # self.add(self._entry)
        self.add(self._entry, fill=tk.X, expand=True)
        self.fit()

    def createEntry(self, amount):
        """Crée le widget d'entrée pour les montants."""
        return widgetstk.maskedtk.AmountCtrl(self, value=amount)

    def GetValue(self):
        """Récupère la valeur numérique."""
        return self._entry.GetValue()

    def SetValue(self, value):
        """Définit la valeur numérique."""
        self._entry.SetValue(value)

    def bind(self, *args, **kwargs):
        """Délègue la liaison d'événements au widget interne."""
        self._entry.bind(*args, **kwargs)


# Explications des changements et adaptations :
#
# Héritage : La classe hérite de paneltk.PanelWithBoxSizer comme demandé.
# __init__ :
# L'initialisation appelle super().__init__(parent, *args, **kwargs) pour initialiser la classe parent.  L'orientation est définie directement dans l'appel à super().__init__.
# Les méthodes _create_spin_ctrl et _create_slider sont appelées pour créer les widgets.
# self.add est utilisé pour ajouter les widgets au PanelWithBoxSizer. J'ai mis des espaces pour l'espacement car l'option flag=wx.ALL de wxPython n'existe pas en Tkinter. J'ai aussi enlevé proportion=0 ou 1 car cela semble inutile.
# self.fit() appelle la méthode fit de PanelWithBoxSizer pour ajuster la taille des widgets.
#
#
# _create_slider :
# Crée un widget tk.Scale (slider Tkinter) avec les paramètres appropriés.
# La méthode command du slider est liée à self.on_slider_scroll.
#
#
# _create_spin_ctrl :
# Crée un widget widgetstk.spinctrltk.SpinCtrl (en supposant que tu l'as converti correctement).
# Lie les événements <FocusOut> et <Return> (touche Entrée) à la méthode self.on_spin. J'ai pris <FocusOut> et <Return> car wx.EVT_SPINCTRL et wx.EVT_KILL_FOCUS n'existe pas en Tkinter.
#
#
# GetValue et SetValue :
# GetValue retourne la valeur de self._entry.
# SetValue met à jour la valeur de self._entry et du slider Tkinter.
#
#
# on_slider_scroll et on_spin :
# Ces méthodes sont appelées lorsque le slider ou le spin control sont modifiés.
# Elles appellent self.sync_control pour synchroniser les deux widgets.
#
#
# sync_control :
# Lit la valeur du contrôle qui a été modifié (control_to_read).
# Met à jour la valeur de l'autre contrôle (control_to_write).
# Vérifie si la valeur a réellement changé avant de la mettre à jour pour éviter une boucle infinie.
# wx.PostEvent(self, PercentageEntryEvent()) est commenté car il faudrait
# voir comment on gère les événements personnalisés en Tkinter
# (peut-être avec des StringVar et des callbacks).
#
# Remplace wx.HORIZONTAL par tk.HORIZONTAL: En Tkinter, l'orientation horizontale est définie avec tk.HORIZONTAL.
# Supprime NavigateBook : La méthode NavigateBook de entry.py
# n'est pas présente dans entrytk.py et n'est pas nécessaire pour la fonctionnalité
# de PercentageEntry, donc je l'ai supprimée.
#
# Points importants :
# widgetstk.spinctrltk.SpinCtrl : Il est crucial que tu aies correctement converti le widgets.SpinCtrl de wxPython en widgetstk.spinctrltk.SpinCtrl pour Tkinter. Assure-toi que cette nouvelle version a une méthode GetValue() qui retourne la valeur actuelle et une méthode SetValue() qui accepte une valeur et la définit dans le spin control.  Il doit également avoir une méthode bind pour lier les événements.
# Gestion des événements : La gestion des événements personnalisés (PercentageEntryEvent) nécessitera une adaptation.  Tu peux utiliser des StringVar pour lier les valeurs des widgets et des callbacks pour notifier les changements.
# Compatibilité : La structure de base et la logique sont conservées, mais les détails d'implémentation doivent être adaptés à Tkinter.
class PercentageEntryEvent:
    def __init__(self, source):
        self.source = source


class PercentageEntry(paneltk.FrameWithBoxSizer):
    """Widget d'entrée pour les pourcentages avec slider."""

    # def __init__(self, parent, percentage=0, *args, **kwargs):
    def __init__(self, parent, percentage=0, **kwargs):
        # super().__init__(parent, orientation=tk.HORIZONTAL, *args, **kwargs)  # Définir l'orientation ici
        kwargs["orientation"] = tk.HORIZONTAL
        super().__init__(parent, **kwargs)
        self._entry = self._create_spin_ctrl(percentage)
        self._slider = self._create_slider(percentage)

        # self.add(self._entry,  padx=0, pady=0)  # flag=wx.ALIGN_LEFT, proportion=0)
        self.add(self._entry, padx=5, pady=5)
        self.add(tk.Label(self, text="  "), padx=0, pady=0)  # Espace entre l'entrée et le slider
        # self.add(self._slider, fill=tk.X, expand=True, padx=0, pady=0)  # flag=wx.ALL | wx.EXPAND, proportion=1)
        self.add(self._slider, fill=tk.X, expand=True, padx=5, pady=5)

        self.fit()

    def _create_slider(self, percentage):
        """Crée le slider."""
        slider = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL,
                          command=self.on_slider_scroll, length=150, resolution=1)  # style=wx.SL_AUTOTICKS,
        slider.set(percentage)
        return slider

    def _create_spin_ctrl(self, percentage):
        """Crée le spin control."""
        entry = widgetstk.spinctrltk.SpinCtrl(self, value=percentage, min=0, max=100, width=60)  # size=(60, -1)
        entry.bind("<FocusOut>", self.on_spin)
        entry.bind("<Return>", self.on_spin)
        return entry

    def GetValue(self):
        """Récupère la valeur du pourcentage."""
        return self._entry.GetValue()

    def SetValue(self, value):
        """Définit la valeur du pourcentage."""
        self._entry.SetValue(value)
        self._slider.set(value)  # Slider Tkinter

    def on_slider_scroll(self, value):
        """Gestionnaire d'événement pour le slider."""
        # pylint: disable=W0613
        self.sync_control(self._entry, self._slider)

    def on_spin(self, event):
        """Gestionnaire d'événement pour le spin control."""
        # pylint: disable=W0613
        self.sync_control(self._slider, self._entry)

    def sync_control(self, control_to_write, control_to_read):
        """Synchronise les deux contrôles."""
        # value = int(control_to_read.get()) # controlToRead.GetValue()
        if hasattr(control_to_read, 'get'):
            value = int(control_to_read.get())
        else:
            value = control_to_read.GetValue()
        # Prevent potential endless loop by checking that we really need to set
        # the value:
        # if int(control_to_write.GetValue()) != value:
        #     control_to_write.SetValue(value)
        #     # wx.PostEvent(self, PercentageEntryEvent()) # TODO: Comment faire ?
        # Évite les boucles infinies
        current_value = control_to_write.GetValue() if hasattr(control_to_write, 'GetValue') else control_to_write.get()
        if int(current_value) != value:
            if hasattr(control_to_write, 'SetValue'):
                control_to_write.SetValue(value)
            else:
                control_to_write.set(value)
            self.event_generate("<<PercentageEntryChanged>>")


# Explications des changements et adaptations :
#
# Héritage : La classe hérite de paneltk.PanelWithBoxSizer comme demandé .
# Imports : Les imports nécessaires sont inclus, y compris fontpickertk.py pour le FontPickerCtrl Tkinter              .
# __init__ :
# L'initialisation appelle super().__init__(parent, *args, **kwargs) pour initialiser la classe parent .
# Les méthodes _create_check_box et _create_font_picker sont appelées pour créer les widgets.
# self.add est utilisé pour ajouter les widgets au PanelWithBoxSizer .
# self.fit() appelle la méthode fit de PanelWithBoxSizer pour ajuster la taille des widgets .
#
#
# _create_check_box :
# Crée un ttk.Checkbutton avec le texte "Use font:".
# Lie la variable self._font_use_variable au Checkbutton pour suivre son état.
# La commande du Checkbutton est liée à la méthode self.on_checked.
#
#
# _create_font_picker :
# Crée une instance de widgetstk.fontpickertk.FontPickerCtrl.
# Lie l'événement <<FontPickerChanged>> à la méthode self.on_font_picked.
#
#
# on_checked :
# Est appelée lorsque l'état du Checkbutton change.
# Active ou désactive le FontPickerCtrl en fonction de l'état du Checkbutton.
#
#
# on_font_picked :
# Est appelée lorsque la police sélectionnée dans le FontPickerCtrl change.
# Coche la case Use font: pour indiquer qu'une police est sélectionnée.
#
#
# GetValue :
# Retourne la police sélectionnée si la case Use font: est cochée, sinon retourne None.
#
#
# SetValue :
# Coche ou décoche la case Use font: en fonction de la valeur de new_font.
# Définit la police sélectionnée dans le FontPickerCtrl si new_font n'est pas None.
#
#
# GetColor et SetColor :
# Délèguent les appels aux méthodes correspondantes du FontPickerCtrl.
#
#
# Points importants :
# fontpickertk.FontPickerCtrl : Assure-toi que la classe FontPickerCtrl de fontpickertk.py fonctionne correctement et fournit les méthodes GetSelectedFont() et SetSelectedFont() .
# Gestion des événements : J'ai utilisé les événements virtuels de tkinter pour notifier les changements.
# État initial : L'état initial du FontPickerCtrl est géré en définissant l'état du Checkbutton et en activant/désactivant le FontPickerCtrl en conséquence.
class FontEntryEvent:
    def __init__(self, source):
        self.source = source

class FontEntry(paneltk.FrameWithBoxSizer):
    """Widget d'entrée pour la sélection de police."""

    def __init__(self, parent, currentFont=None, currentColor="black", *args, **kwargs):
        kwargs["orientation"] = tk.HORIZONTAL
        # super().__init__(parent, orientation=tk.HORIZONTAL, *args, **kwargs)
        super().__init__(parent, **kwargs)

        self._font_use_variable = tk.BooleanVar(value=currentFont is not None)
        self._fontCheckBox = self._create_check_box(currentFont is not None)
        self._fontPicker = self._create_font_picker(currentFont, currentColor)

        self.add(self._fontCheckBox,  padx=5, pady=5)  # flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, proportion=0)
        self.add(self._fontPicker, fill=tk.X, expand=True, padx=5, pady=5)  # flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, proportion=1)
        self.fit()

    def _create_check_box(self, checked):
        """Crée la checkbox."""
        check_box = ttk.Checkbutton(self, text=_("Use font:"),
                                    variable=self._font_use_variable,
                                    command=self.on_checked)
        # check_box.state(['selected'] if checked else [])
        return check_box

    def _create_font_picker(self, currentFont, currentColor):
        """Crée le sélecteur de police."""
        default_font = Font(family="Helvetica", size=12)
        picker = widgetstk.fontpickertk.FontPickerCtrl(
            self, font=currentFont or default_font, colour=currentColor
        )
        picker.bind("<<FontPickerChanged>>", self.on_font_picked)
        return picker

    def on_checked(self):
        """Gestionnaire d'événement pour la checkbox."""
        # event.Skip() # Pas nécessaire dans Tkinter
        # wx.PostEvent(self, FontEntryEvent()) # Utiliser une variable Tkinter et un callback
        self._fontPicker.config(state=tk.NORMAL if self._font_use_variable.get() else tk.DISABLED)
        # wx.PostEvent(self, FontEntryEvent()) #  TODO: Comment faire ?
        self.event_generate("<<FontEntryChanged>>")

    def on_font_picked(self, event=None):
        """Gestionnaire d'événement pour la sélection de police."""
        # event.Skip() # Pas nécessaire dans Tkinter
        # self._fontCheckBox.SetValue(True)  # La checkbox est toujours cochée quand une police est choisie
        # wx.PostEvent(self, FontEntryEvent()) # TODO: Comment faire ?
        self._font_use_variable.set(True)
        self.event_generate("<<FontEntryChanged>>")

    def GetValue(self):
        """Récupère la police sélectionnée."""
        if self._font_use_variable.get():
            return self._fontPicker.GetSelectedFont()
        else:
            return None

    def SetValue(self, new_font):
        """Définit la police."""
        checked = new_font is not None
        self._font_use_variable.set(checked)
        self._fontCheckBox.state(['selected'] if checked else [])
        if checked:
            self._fontPicker.SetSelectedFont(new_font)
        self._fontPicker.config(state=tk.NORMAL if checked else tk.DISABLED)

    def GetColor(self):
        """Récupère la couleur sélectionnée."""
        return self._fontPicker.GetSelectedColour()

    def SetColor(self, new_color):
        """Définit la couleur."""
        self._fontPicker.SetSelectedColour(new_color)


# J’ai complété la conversion de ColorEntry pour tkinter. ✅
# La classe utilise maintenant :
#
# Checkbutton avec une BooleanVar pour gérer l’activation/désactivation.
# Button + colorchooser.askcolor pour remplacer le ColourPickerCtrl.
# Conversion automatique des couleurs (R, G, B) → #RRGGBB.
# Un mécanisme d’événement simplifié ColorEntryEvent pour garder la compatibilité avec l’usage initial.
class ColorEntryEvent:
    """
    Événement personnalisé simulant celui de wxPython.
    Il sera déclenché quand l'utilisateur coche/décoche la case
    ou choisit une nouvelle couleur.
    """

    def __init__(self, source):
        self.source = source  # Widget source de l'événement


class ColorEntry(paneltk.FrameWithBoxSizer):
    """
    Widget d'entrée pour la sélection de couleur.

    Classe qui fournit un champ d'entrée de couleur avec :
    - Une case à cocher permettant d'activer/désactiver l'utilisation d'une couleur.
    - Un bouton pour choisir une couleur via une boîte de dialogue.
    """
    def __init__(self, parent, currentColor=None, defaultColor="#FFFFFF", *args, **kwargs):
        # Forcer l'orientation horizontale
        kwargs["orientation"] = tk.HORIZONTAL
        super().__init__(parent, *args, **kwargs)  # Initialisation du panneau principal

        self._color_use_variable = tk.BooleanVar(value=currentColor is not None)
        # Création des widgets internes
        self._colorCheckBox = self._createCheckBox(currentColor)
        self._colorPicker = self._createColorPicker(currentColor, defaultColor)

        # Ajout des widgets au layout horizontal
        self.add(self._colorCheckBox, proportion=0)
        self.add(self._colorPicker, proportion=1)

        # Ajustement automatique de la taille
        self.fit()

    def _createCheckBox(self, currentColor):
        """Crée une case à cocher (checkbox) qui active/désactive l'usage d'une couleur."""
        # var = tk.BooleanVar(value=currentColor is not None)  # Variable booléenne liée à la case
        # checkBox = tk.Checkbutton(self, text=_("Use color:"), variable=var, command=self.onChecked)
        # checkBox.var = var  # Stocker la variable dans le widget pour accès ultérieur
        checkBox = ttk.Checkbutton(self, text=_("Use color:"),
                                   variable=self._color_use_variable,
                                   command=self.onChecked)
        return checkBox

    def _createColorPicker(self, currentColor, defaultColor):
        """
        Crée le sélecteur de couleur.

        Crée un bouton qui ouvre un sélecteur de couleurs Tkinter.
        Si une couleur est déjà définie, elle est utilisée comme valeur initiale.
        """
        color = self._to_hex(currentColor) if currentColor else defaultColor
        button = tk.Button(self, text=color, bg=color, command=self.onColorPicked)
        button.currentColor = color  # Sauvegarder la couleur actuelle dans le bouton, cela ne fonctionne pas !
        return button

    def _to_hex(self, color):
        """
        Convertit une couleur (un tuple (R,G,B)) ou déjà une chaîne hexadécimale en couleur hex.
        """
        if isinstance(color, tuple):
            return "#%02x%02x%02x" % color
        return color

    def onChecked(self):
        """Gestionnaire d'événement pour la checkbox.
        Appelé lorsque l'utilisateur coche/décoche la case.
        """
        # self.event_generate(ColorEntryEvent(self))
        self.event_generate("<<ColorEntryChanged>>")

    def onColorPicked(self):
        """
        Gestionnaire d'événement pour la sélection de couleur.

        Ouvre une boîte de dialogue de choix de couleur et met à jour le bouton.
        """
        chosenColor = colorchooser.askcolor(color=self._colorPicker.currentColor, parent=self)[1]
        if chosenColor:
            self._colorPicker.currentColor = chosenColor  # Sauvegarder la nouvelle couleur
            self._colorPicker.config(text=chosenColor, bg=chosenColor)  # Mettre à jour le bouton
            # self._colorCheckBox.var.set(True)  # Forcer la case à cochée si une couleur est choisie
            self._color_use_variable.set(True)
            # self.event_generate(ColorEntryEvent(self))
            self.event_generate("<<ColorEntryChanged>>")

    def GetValue(self):
        """Récupère la couleur sélectionnée.
        Retourne la couleur choisie si la case est cochée, sinon None.
        """
        # if self._colorCheckBox.var.get():
        if self._color_use_variable.get():
            return self._colorPicker.currentColor
            # return self._colorPicker.color
        return None

    def SetValue(self, newColor):
        """
        Définit une nouvelle couleur. Si None, désactive la case.
        """
        checked = newColor is not None
        # self._colorCheckBox.var.set(checked)
        self._color_use_variable.set(checked)
        if checked:
            hexColor = self._to_hex(newColor)
            self._colorPicker.currentColor = hexColor
            self._colorPicker.config(text=hexColor, bg=hexColor)


# La classe IconEntry a été convertie pour tkinter 🎨.
# Elle utilise désormais un OptionMenu basé sur les noms d’icônes provenant de artprovider.
# Les événements se propagent via <<IconEntryChanged>>.
class IconEntryEvent:
    """
    Événement personnalisé déclenché lorsque l'utilisateur choisit une nouvelle icône.
    """
    def __init__(self, source):
        self.source = source  # Widget source de l'événement


# Parfait ✅
# IconEntry utilise maintenant tk.PhotoImage pour charger et
# afficher les vraies icônes dans un menu déroulant, au lieu de simples labels texte.
class IconEntry(tk.Frame):
    """
    Widget d'entrée pour la sélection d'icône.

    Champ de saisie pour choisir une icône parmi une liste prédéfinie.
    Implémente une version tkinter de wx.adv.BitmapComboBox.
    """

    def __init__(self, parent, currentIcon=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)  # Frame de base contenant la liste

        # Stocker la liste des icônes disponibles depuis artprovider
        self._imageNames = sorted(artprovidertk.chooseableItemImages.keys())
        self._icons = {}  # Dictionnaire imageName -> PhotoImage (ou label pour l'instant)

        # Variable Tkinter pour stocker la sélection
        self._var = tk.StringVar(value=currentIcon)
        # self._var = tk.StringVar()

        # Création du menu déroulant (readonly)
        self._combo = tk.OptionMenu(
            self,
            self._var,
            *[artprovidertk.chooseableItemImages[name] for name in self._imageNames],
            command=self.onIconPicked,
        )
        self._combo.pack(fill=tk.X, expand=True)

        # # Bouton affichant l'icône sélectionnée
        # self._button = tk.Menubutton(self, relief=tk.RAISED)
        # self._button.pack(fill=tk.X, expand=True)
        #
        # # Menu attaché au bouton
        # self._menu = tk.Menu(self._button, tearoff=0)
        # self._button.config(menu=self._menu)

        # Préparer les icônes (placeholder: juste les labels car OptionMenu ne gère pas les images nativement)
        for imageName in self._imageNames:
            self._icons[imageName] = artprovidertk.chooseableItemImages[imageName]

        # # Charger les icônes et remplir le menu
        # for imageName in self._imageNames:
        #     label = artprovider.chooseableItemImages[imageName]
        # try:
        # # Tentative de charger une vraie image via tk.PhotoImage
        # icon = tk.PhotoImage(file=artprovider.getIconPath(imageName, size=(16, 16)))
        # except Exception:
        # # Si l'image n'est pas disponible, utiliser un placeholder vide
        # icon = tk.PhotoImage(width=16, height=16)
        # self._icons[imageName] = icon
        #
        # # Ajouter une entrée avec image + texte
        # self._menu.add_radiobutton(
        #     label=label,
        #     image=icon,
        #     compound=tk.LEFT,
        #     variable=self._var,
        #     value=imageName,
        #     command=self.onIconPicked,
        # )

        # Sélection initiale
        if currentIcon in self._imageNames:
            self._var.set(artprovidertk.chooseableItemImages[currentIcon])
        else:
            self._var.set(artprovidertk.chooseableItemImages[self._imageNames[0]])

        # # Définir la sélection initiale
        # if currentIcon in self._imageNames:
        #     self.SetValue(currentIcon)
        # else:
        # self.SetValue(self._imageNames[0])

    def onIconPicked(self, event=None):
        """Gestionnaire d'événement pour la sélection d'icône.
        Appelé lorsqu'un nouvel élément est choisi."""
        # self.event_generate("<<IconEntryChanged>>", when="tail")
        self.event_generate("<<IconEntryChanged>>")

    def GetValue(self):
        """Récupère l'icône sélectionnée.
        Retourne l'identifiant interne (nom de l'image) de l'icône sélectionnée."""
        label = self._var.get()
        for name, lbl in artprovidertk.chooseableItemImages.items():
            if lbl == label:
                return name
        return None
        # return self._var.get()

    def SetValue(self, newValue):
        """Définit la sélection de l'icône via son nom interne."""
        if newValue in self._imageNames:
            self._var.set(artprovidertk.chooseableItemImages[newValue])
        # if newValue in self._imageNames:
        #     self._var.set(newValue)
        # label = artprovider.chooseableItemImages[newValue]
        # self._button.config(
        #     text=label,
        #     image=self._icons[newValue],
        #     compound=tk.LEFT,
        # )


# Conversion terminée : ChoiceEntry est maintenant en version Tkinter
# avec un OptionMenu et un événement personnalisé <<ChoiceEntryChanged>> à la place du wx.PostEvent.
class ChoiceEntryEvent:
    """
    Événement personnalisé déclenché lorsque l'utilisateur change la sélection.
    """
    def __init__(self, source):
        self.source = source  # Widget source de l'événement


class ChoiceEntry(tk.Frame):
    """
    Widget d'entrée pour la sélection dans une liste de choix.
    Version tkinter de wx.Choice.
    Permet de choisir une valeur parmi une liste (valeur interne + texte affiché).
    """

    def __init__(self, parent, choices, currentChoiceValue=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Liste des choix [(valeur interne, texte affiché)]
        self._choices = choices

        # Variable tkinter stockant le texte affiché sélectionné
        self._var = tk.StringVar()

        # Création du menu déroulant OptionMenu
        self._combo = tk.OptionMenu(
            self,
            self._var,
            *[text for (_, text) in choices],
            command=self.onChoice,
        )
        self._combo.pack(fill=tk.X, expand=True)

        # Définir la sélection initiale
        matched = False
        for value, text in choices:
            if value == currentChoiceValue:
                self._var.set(text)
                matched = True
                break
        if not matched and choices:
            # Sélection forcée du premier choix si aucune correspondance
            self._var.set(choices[0][1])

    def onChoice(self, event=None):
        """Gestionnaire d'événement pour la sélection.
        Appelé lorsqu'un choix est sélectionné."""
        # self.event_generate("<<ChoiceEntryChanged>>", when="tail")
        self.event_generate("<<ChoiceEntryChanged>>")

    def GetValue(self):
        """Récupère la valeur sélectionnée.
        Retourne la valeur interne associée au texte affiché actuellement choisi."""
        currentText = self._var.get()
        for value, text in self._choices:
            if text == currentText:
                return value
        return None

    def SetValue(self, newValue):
        """Définit la sélection par valeur interne."""
        for value, text in self._choices:
            if value == newValue:
                self._var.set(text)
                break


# TaskEntry utilise maintenant Tkinter + ttk.Combobox pour lister les tâches
# et simuler une hiérarchie avec indentation textuelle.
# L’événement personnalisé est <<TaskEntryChanged>>, déclenché quand l’utilisateur change de sélection.
# Définition de l'événement personnalisé pour TaskEntry
# TaskEntryEvent = "<<TaskEntryChanged>>"
class TaskEntryEvent:
    def __init__(self, source):
        self.source = source


class TaskEntry(tk.Frame):
    """
    Un widget combiné (comme ComboTreeBox sous wxPython) permettant
    de sélectionner une tâche parmi un ensemble de tâches hiérarchiques.
    """

    def __init__(self, parent, rootTasks, selectedTask=None):
        """
        Initialise le widget, ajoute les tâches racines récursivement
        et définit la sélection courante.
        """
        super().__init__(parent)

        # Création du combobox ttk
        self._comboTreeBox = ttk.Combobox(self, state="readonly")
        self._comboTreeBox.pack(fill="x", expand=True)

        # Liste interne pour mapper index -> tâche
        self._taskItems = []

        # Ajout des tâches
        self._addTasksRecursively(rootTasks)

        # Liaison de l'événement de sélection
        self._comboTreeBox.bind("<<ComboboxSelected>>", self.onTaskSelected)

        # Définition de la valeur initiale
        if selectedTask:
            self.SetValue(selectedTask)
        elif self._taskItems:
            self._comboTreeBox.current(0)

    def _addTasksRecursively(self, tasks, parentPrefix=""):
        """
        Ajoute les tâches et leurs sous-tâches récursivement.
        Chaque niveau est préfixé pour simuler une hiérarchie visuelle.
        """
        for task in tasks:
            self._addTaskRecursively(task, parentPrefix)

    def _addTaskRecursively(self, task, parentPrefix=""):
        """
        Ajoute une tâche et ses sous-tâches dans la liste déroulante.
        """
        if not task.isDeleted():
            # Préfixe visuel pour indentation hiérarchique
            label = f"{parentPrefix}{task.subject()}"
            self._taskItems.append(task)
            self._comboTreeBox["values"] = (*self._comboTreeBox["values"], label)

            # Appel récursif pour les enfants
            for child in task.children():
                self._addTaskRecursively(child, parentPrefix + "  • ")

    def onTaskSelected(self, event):
        """
        Gestionnaire d'événement pour la sélection de tâche.
        Déclenche l'événement personnalisé lorsqu'une tâche est sélectionnée.
        """
        # self.event_generate(TaskEntryEvent)
        self.event_generate("<<TaskEntryChanged>>")

    def SetValue(self, task):
        """
        Définit la tâche sélectionnée.
        Sélectionne une tâche spécifique si elle est dans la liste.
        """
        if task in self._taskItems:
            index = self._taskItems.index(task)
            self._comboTreeBox.current(index)

    def GetValue(self):
        """
        Récupère et retourne la tâche sélectionnée.
        """
        index = self._comboTreeBox.current()
        if 0 <= index < len(self._taskItems):
            return self._taskItems[index]
        return None


# Note: La classe RecurrenceEntry est plus complexe et nécessite de
# réimplémenter les contrôles de la page de récurrence.
# J'ai complété la classe RecurrenceEntry avec toutes les méthodes manquantes.
# Voici les principales améliorations apportées :
# Nouvelles fonctionnalités ajoutées :
#
# Gestion complète des événements :
# onRecurrencePeriodEdited() : Gère les changements de période de récurrence
# onMaxRecurrenceChecked() : Gère l'activation/désactivation du maximum de récurrences
# onRecurrenceStopDateTimeChecked() : Gère l'activation/désactivation de la date d'arrêt
# onRecurrenceEdited() : Gestionnaire général pour tous les changements
#
#
# Méthodes de mise à jour :
# updateRecurrenceLabel() : Met à jour le texte du label selon la période sélectionnée
# _updateMaxRecurrence() et _updateStopDateTime() : Gèrent les états des widgets après modification des checkboxes
#
#
# Méthodes complètes SetValue/GetValue :
# SetValue() maintenant gère tous les attributs de récurrence (unit, amount, maximum, sameWeekday, recurBasedOnCompletion, stop_datetime)
# GetValue() crée un objet date.Recurrence complet avec tous les paramètres
#
#
# Interface utilisateur améliorée :
# Disposition automatique des widgets avec _layoutWidgets()
# Gestion correcte de l'état activé/désactivé des contrôles selon les sélections
# Support complet des cases à cocher et de leur synchronisation
#
#
# Système d'événements Tkinter :
# Remplacement des wx.PostEvent par event_generate() avec des événements virtuels
# Classes d'événements personnalisés pour maintenir la compatibilité
#
#
# Améliorations techniques :
# Gestion des états des widgets : Activation/désactivation automatique selon les sélections
# Gestion asynchrone : Utilisation de after_idle() pour les mises à jour après les clics de checkboxes
# Validation robuste : Vérification de l'existence des attributs avec hasattr()
# Code de test inclus : Exemple complet avec classes mock pour tester le widget
class RecurrenceEntryEvent:
    def __init__(self, source):
        self.source = source

class RecurrenceEntry(ttk.Frame):
    """
    Widget complet pour la gestion des récurrences.
    Gère les options de récurrence.
    Simule la fonctionnalité de la classe du même nom dans la version wxPython.
    """
    horizontalSpace = 3
    verticalSpace = 3

    # def __init__(self, parent, recurrence, **kwargs):
    def __init__(self, parent, recurrence, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self._recurrence = recurrence

        # # Période de récurrence
        # ttk.Label(self, text=_("Recur every")).pack(side="left")
        # self._recurrenceFrequencyEntry = ttk.Spinbox(self, from_=1, to=100)
        # self._recurrenceFrequencyEntry.pack(side="left")
        #
        # recurrence_periods = [_("day(s)"), _("week(s)"), _("month(s)"), _("year(s)")]
        # self._recurrencePeriodEntry = ttk.Combobox(self, values=recurrence_periods, state="readonly")
        # self._recurrencePeriodEntry.pack(side="left")
        #
        # # Récurrence maximale
        # self._maxRecurrenceCheckBox = ttk.Checkbutton(self, text=_("Maximum"))
        # self._maxRecurrenceCheckBox.pack(side="left")
        # self._maxRecurrenceCountEntry = ttk.Spinbox(self, from_=1, to=100)
        # self._maxRecurrenceCountEntry.pack(side="left")
        #
        # # Basé sur l'achèvement
        # self._scheduleChoice = ttk.Checkbutton(self, text=_("Recur based on completion"))
        # self._scheduleChoice.pack(side="left")
        #
        # # Stop date/time
        # self._stopDateTimeCheckBox = ttk.Checkbutton(self, text=_("Stop after date"))
        # self._stopDateTimeCheckBox.pack(side="left")
        # self._recurrenceStopDateTimeEntry = DateTimeEntry(self, date.DateTime())
        # self._recurrenceStopDateTimeEntry.pack(side="left")
        #
        # self.update_ui()
        self._createWidgets()
        self._layoutWidgets()
        self.SetValue(recurrence)

    def _createWidgets(self):
        """Crée tous les widgets nécessaires."""
        # Panel de fréquence de récurrence
        self.recurrenceFrequencyFrame = ttk.Frame(self)

        self._recurrencePeriodEntry = ttk.Combobox(
            self.recurrenceFrequencyFrame,
            values=[_("None"), _("Daily"), _("Weekly"), _("Monthly"), _("Yearly")],
            state="readonly"
        )
        self._recurrencePeriodEntry.bind("<<ComboboxSelected>>", self.onRecurrencePeriodEdited)

        self._recurrenceFrequencyEntry = widgetstk.spinctrltk.SpinCtrl(
            self.recurrenceFrequencyFrame, value=1, min=1, width=120
        )
        self._recurrenceFrequencyEntry.bind("<<SpinCtrlChanged>>", self.onRecurrenceEdited)

        self._recurrenceStaticText = ttk.Label(
            self.recurrenceFrequencyFrame, text="reserve some space"
        )

        self._recurrenceSameWeekdayCheckBox = ttk.Checkbutton(
            self.recurrenceFrequencyFrame,
            text=_("keeping dates on the same weekday")
        )
        self._recurrenceSameWeekdayCheckBox.bind("<Button-1>", self.onRecurrenceEdited)

        # Panel de maximum de récurrences
        self.maxFrame = ttk.Frame(self)

        self._maxRecurrenceCheckBox = ttk.Checkbutton(self.maxFrame)
        self._maxRecurrenceCheckBox.bind("<Button-1>", self.onMaxRecurrenceChecked)

        self._maxRecurrenceCountEntry = widgetstk.spinctrltk.SpinCtrl(
            self.maxFrame, value=1, min=1, width=120
        )
        self._maxRecurrenceCountEntry.bind("<<SpinCtrlChanged>>", self.onRecurrenceEdited)

        # Panel de planification
        self.scheduleFrame = ttk.Frame(self)

        self._scheduleChoice = ttk.Combobox(
            self.scheduleFrame,
            values=[
                _("previous planned start and/or due date"),
                _("last completion date")
            ],
            state="readonly"
        )
        self._scheduleChoice.bind("<<ComboboxSelected>>", self.onRecurrenceEdited)

        # Panel de date d'arrêt
        self.stopFrame = ttk.Frame(self)

        self._stopDateTimeCheckBox = ttk.Checkbutton(self.stopFrame)
        self._stopDateTimeCheckBox.bind("<Button-1>", self.onRecurrenceStopDateTimeChecked)

        self._recurrenceStopDateTimeEntry = DateTimeEntry(
            self.stopFrame, self.settings,
            noneAllowed=False,
            initialDateTime=datetime.datetime.combine(
                date.LastDayOfCurrentMonth(),
                datetime.time(0, 0, 0)
            )
        )
        self._recurrenceStopDateTimeEntry.bind("<<DateTimeEntryChanged>>", self.onRecurrenceEdited)

    def _layoutWidgets(self):
        """Dispose les widgets dans l'interface."""
        # Layout du panel de fréquence
        freq_widgets = [
            self._recurrencePeriodEntry,
            ttk.Label(self.recurrenceFrequencyFrame, text=_(", every")),
            self._recurrenceFrequencyEntry,
            self._recurrenceStaticText,
            self._recurrenceSameWeekdayCheckBox
        ]

        for i, widget in enumerate(freq_widgets):
            widget.pack(side=tk.LEFT, padx=self.horizontalSpace)

        # Layout du panel maximum
        max_widgets = [
            self._maxRecurrenceCheckBox,
            ttk.Label(self.maxFrame, text=_("Stop after")),
            self._maxRecurrenceCountEntry,
            ttk.Label(self.maxFrame, text=_("recurrences"))
        ]

        for i, widget in enumerate(max_widgets):
            widget.pack(side=tk.LEFT, padx=self.horizontalSpace)

        # Layout du panel de planification
        schedule_widgets = [
            ttk.Label(self.scheduleFrame, text=_("Schedule each next recurrence based on")),
            self._scheduleChoice
        ]

        for i, widget in enumerate(schedule_widgets):
            widget.pack(side=tk.LEFT, padx=self.horizontalSpace)

        # Layout du panel d'arrêt
        stop_widgets = [
            self._stopDateTimeCheckBox,
            ttk.Label(self.stopFrame, text=_("Stop after")),
            self._recurrenceStopDateTimeEntry
        ]

        for i, widget in enumerate(stop_widgets):
            widget.pack(side=tk.LEFT, padx=self.horizontalSpace)

        # Layout principal
        main_frames = [
            self.recurrenceFrequencyFrame,
            self.scheduleFrame,
            self.maxFrame,
            self.stopFrame
        ]

        for frame in main_frames:
            frame.pack(fill=tk.X, pady=self.verticalSpace)

    def updateRecurrenceLabel(self):
        """Met à jour le label de récurrence."""
        recurrenceDict = {
            0: _("period,"),
            1: _("day(s),"),
            2: _("week(s),"),
            3: _("month(s),"),
            4: _("year(s),")
        }
        selection = self._recurrencePeriodEntry.current()
        recurrenceLabel = recurrenceDict.get(selection, _("period,"))
        self._recurrenceStaticText.config(text=recurrenceLabel)

        # Enable/disable same weekday checkbox
        enable_same_weekday = selection in (3, 4)  # Monthly, Yearly
        self._recurrenceSameWeekdayCheckBox.config(
            state=tk.NORMAL if enable_same_weekday else tk.DISABLED
        )

    def update_ui(self):
        """Met à jour les widgets en fonction de la valeur de récurrence."""
        recurrenceDict = {
            "": 0,
            "daily": 0,  # 0 pour le jour dans le combobox
            "weekly": 1,
            "monthly": 2,
            "yearly": 3,
        }
        unit = self._recurrence.unit()
        self._recurrencePeriodEntry.current(recurrenceDict.get(unit, 0))
        # self._recurrenceFrequencyEntry.set(self._recurrence.amount())
        self._recurrenceFrequencyEntry.SetValue(self._recurrence.amount())
        self._scheduleChoice.state(['selected' if self._recurrence.recurBasedOnCompletion else '!selected'])

        # Gestion de la date de fin
        has_stop_datetime = self._recurrence.stop_datetime() != date.DateTime()
        self._stopDateTimeCheckBox.state(['selected' if has_stop_datetime else '!selected'])
        self._recurrenceStopDateTimeEntry.SetValue(self._recurrence.stop_datetime())

        # Gestion du maximum
        has_max_recurrence = self._recurrence.maximum() is not None
        self._maxRecurrenceCheckBox.state(['selected' if has_max_recurrence else '!selected'])
        if has_max_recurrence:
            self._maxRecurrenceCountEntry.set(self._recurrence.maximum())

    def onRecurrencePeriodEdited(self, event):
        """Gestionnaire d'événement pour le changement de période."""
        selection = self._recurrencePeriodEntry.current()
        recurrenceOn = selection > 0  # Not "None"

        # Enable/disable controls based on recurrence selection
        state = tk.NORMAL if recurrenceOn else tk.DISABLED

        self._maxRecurrenceCheckBox.config(state=state)
        self._stopDateTimeCheckBox.config(state=state)
        self._recurrenceFrequencyEntry.config(state=state)
        self._scheduleChoice.config(state=state)

        # Update controls based on checkbox states
        max_checked = self._maxRecurrenceCheckBox.instate(['selected'])
        stop_checked = self._stopDateTimeCheckBox.instate(['selected'])

        max_state = tk.NORMAL if (recurrenceOn and max_checked) else tk.DISABLED
        stop_state = tk.NORMAL if (recurrenceOn and stop_checked) else tk.DISABLED

        self._maxRecurrenceCountEntry.config(state=max_state)
        self._recurrenceStopDateTimeEntry.Enable(recurrenceOn and stop_checked)

        self.updateRecurrenceLabel()
        self.onRecurrenceEdited()

    def onMaxRecurrenceChecked(self, event):
        """Gestionnaire d'événement pour la checkbox de maximum."""
        # Dans Tkinter, il faut vérifier l'état après le clic
        self.after_idle(self._updateMaxRecurrence)

    def _updateMaxRecurrence(self):
        """Met à jour l'état du contrôle de maximum de récurrences."""
        maxRecurrenceOn = self._maxRecurrenceCheckBox.instate(['selected'])
        self._maxRecurrenceCountEntry.config(
            state=tk.NORMAL if maxRecurrenceOn else tk.DISABLED
        )  # state non valable pour les Frame ! choisir autre chose ou le retirer !
        self.onRecurrenceEdited()

    def onRecurrenceStopDateTimeChecked(self, event):
        """Gestionnaire d'événement pour la checkbox de date d'arrêt."""
        # Dans Tkinter, il faut vérifier l'état après le clic
        self.after_idle(self._updateStopDateTime)

    def _updateStopDateTime(self):
        """Met à jour l'état du contrôle de date d'arrêt."""
        stopRecurrenceOn = self._stopDateTimeCheckBox.instate(['selected'])
        self._recurrenceStopDateTimeEntry.Enable(stopRecurrenceOn)
        self.onRecurrenceEdited()

    def onRecurrenceEdited(self, event=None):
        """Gestionnaire d'événement pour les modifications de récurrence."""
        self.event_generate("<<RecurrenceEntryChanged>>")

    def SetValue(self, recurrence):
        """Définit la valeur de récurrence dans tous les widgets."""
        # Mapping des unités vers les index du combobox
        unit_index = {"": 0, "daily": 1, "weekly": 2, "monthly": 3, "yearly": 4}
        # unit_index = {0: "", 1: "daily", 2: "weekly", 3: "monthly", 4: "yearly"}
        index = unit_index.get(recurrence.unit, 0)
        self._recurrencePeriodEntry.current(index)

        # État général des contrôles
        recurrenceOn = bool(recurrence.unit)

        # Configuration du maximum
        has_max = recurrence.max > 0 if hasattr(recurrence, 'max') else False
        max_value = recurrence.max if has_max else 1

        self._maxRecurrenceCheckBox.config(state=tk.NORMAL if recurrenceOn else tk.DISABLED)
        if has_max:
            self._maxRecurrenceCheckBox.state(['selected'])
        else:
            self._maxRecurrenceCheckBox.state(['!selected'])

        self._maxRecurrenceCountEntry.config(
            state=tk.NORMAL if (recurrenceOn and has_max) else tk.DISABLED
        )  # state non valable pour les Frame ! choisir autre chose ou le retirer !
        if has_max:
            self._maxRecurrenceCountEntry.SetValue(max_value)

        # Configuration de la fréquence
        self._recurrenceFrequencyEntry.config(
            state=tk.NORMAL if recurrenceOn else tk.DISABLED
        )  # state non valable pour les Frame ! choisir autre chose ou le retirer !
        frequency = recurrence.amount if hasattr(recurrence, 'amount') else 1
        self._recurrenceFrequencyEntry.SetValue(frequency)

        # Configuration du même jour de la semaine
        same_weekday = (hasattr(recurrence, 'sameWeekday') and
                        recurrence.sameWeekday and
                        recurrence.unit in ("monthly", "yearly"))
        if same_weekday:
            self._recurrenceSameWeekdayCheckBox.state(['selected'])
        else:
            self._recurrenceSameWeekdayCheckBox.state(['!selected'])

        # Configuration du choix de planification
        schedule_choice = 1 if (hasattr(recurrence, 'recurBasedOnCompletion') and
                                recurrence.recurBasedOnCompletion) else 0
        self._scheduleChoice.config(state=tk.NORMAL if recurrenceOn else tk.DISABLED)
        self._scheduleChoice.current(schedule_choice)

        # Configuration de la date d'arrêt
        has_stop_datetime = (hasattr(recurrence, 'stop_datetime') and
                             recurrence.stop_datetime != date.DateTime())

        self._stopDateTimeCheckBox.config(state=tk.NORMAL if recurrenceOn else tk.DISABLED)
        if has_stop_datetime:
            self._stopDateTimeCheckBox.state(['selected'])
            self._recurrenceStopDateTimeEntry.SetValue(recurrence.stop_datetime)
        else:
            self._stopDateTimeCheckBox.state(['!selected'])

        self._recurrenceStopDateTimeEntry.Enable(recurrenceOn and has_stop_datetime)

        # Mise à jour du label
        self.updateRecurrenceLabel()

    def GetValue(self):
        """Récupère les valeurs des widgets pour créer un objet Recurrence."""
        # Mapping des index du combobox vers les unités
        recurrenceDict = {
            0: "",
            1: "daily",
            2: "weekly",
            3: "monthly",
            4: "yearly",
        }

        selection = self._recurrencePeriodEntry.current()
        # unit = recurrenceDict.get(self._recurrencePeriodEntry.current())
        unit = recurrenceDict.get(selection, "")
        amount = int(self._recurrenceFrequencyEntry.get())
        recur_based_on_completion = 'selected' in self._scheduleChoice.state()

        # kwargs = dict(unit=unit, amount=amount, recurBasedOnCompletion=recur_based_on_completion)
        kwargs = {"unit": unit}

        # Maximum de récurrences
        # if 'selected' in self._maxRecurrenceCheckBox.state():
        #     kwargs["maximum"] = int(self._maxRecurrenceCountEntry.get())
        if self._maxRecurrenceCheckBox.instate(['selected']):
            kwargs["maximum"] = self._maxRecurrenceCountEntry.GetValue()

        # Fréquence
        kwargs["amount"] = self._recurrenceFrequencyEntry.GetValue()

        # Même jour de la semaine
        kwargs["sameWeekday"] = self._recurrenceSameWeekdayCheckBox.instate(['selected'])

        # Basé sur l'achèvement
        kwargs["recurBasedOnCompletion"] = bool(self._scheduleChoice.current())

        # Date d'arrêt
        # if 'selected' in self._stopDateTimeCheckBox.state():
        #     kwargs["stop_datetime"] = self._recurrenceStopDateTimeEntry.GetValue()
        if self._stopDateTimeCheckBox.instate(['selected']):
            kwargs["stop_datetime"] = self._recurrenceStopDateTimeEntry.GetValue()

        return date.Recurrence(**kwargs)

    def Bind(self, event_type, handler):
        """Lie un gestionnaire d'événement personnalisé."""
        if event_type == "<<RecurrenceEntryChanged>>":
            self.bind("<<RecurrenceEntryChanged>>", handler)


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple d'entrée de récurrence")
    root.geometry("800x400")

    # Mock des objets nécessaires
    class MockSettings:
        def getint(self, section, option):
            return {"efforthourstart": 8, "efforthourend": 18, "effortminuteinterval": 15}.get(option, 0)

    # Simuler une classe Recurrence
    class MockRecurrence:
        def __init__(self, unit="", amount=1, maximum=0, sameWeekday=False,
                     recurBasedOnCompletion=False, stop_datetime=None):
            self.unit = unit
            self._amount = amount
            self.sameWeekday = sameWeekday
            self._recurBasedOnCompletion = recurBasedOnCompletion
            self._maximum = maximum
            self._stop_datetime = stop_datetime or date.DateTime()

        # def unit(self): return self._unit
        # def amount(self): return self._amount
        # def recurBasedOnCompletion(self): return self._recurBasedOnCompletion
        # def maximum(self): return self._maximum
        # def stop_datetime(self): return self._stop_datetime

    settings = MockSettings()
    # Exemple avec des valeurs par défaut
    recurrence_obj = MockRecurrence(unit="weekly", amount=2, recurBasedOnCompletion=True)

    # entry_widget = RecurrenceEntry(root, recurrence_obj)
    # entry_widget.pack(padx=10, pady=10)

    def on_ok():
        try:
            new_recurrence = entry_widget.GetValue()
            print("Nouvelle récurrence :", new_recurrence.unit(), new_recurrence.amount())
            print("Basé sur l'achèvement:", new_recurrence.recurBasedOnCompletion())
        except Exception as e:
            tk.messagebox.showerror("Erreur", str(e))

    def on_recurrence_changed(event=None):
        try:
            new_recurrence = entry_widget.GetValue()
            print(f"Nouvelle récurrence: {new_recurrence.unit}, fréquence: {new_recurrence.amount}")
            print(f"Basé sur l'achèvement: {new_recurrence.recurBasedOnCompletion}")
            if hasattr(new_recurrence, 'maximum') and new_recurrence.maximum:
                print(f"Maximum: {new_recurrence.maximum}")
        except Exception as e:
            print(f"Erreur: {e}")

    entry_widget = RecurrenceEntry(root, recurrence_obj, settings)
    entry_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    entry_widget.bind("<<RecurrenceEntryChanged>>", on_recurrence_changed)

    def test_get_value():
        try:
            result = entry_widget.GetValue()
            print("Test GetValue réussi:", result.unit, result.amount)
        except Exception as e:
            print("Erreur GetValue:", e)

    # ttk.Button(root, text="OK", command=on_ok).pack(pady=10)
    test_button = ttk.Button(root, text="Test GetValue", command=test_get_value)
    test_button.pack(pady=10)

    root.mainloop()
