# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2012 Nicola Chiapolini <nicola.chiapolini@physik.uzh.ch>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

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


Module `editor.py` - Gère les pages d'édition des objets dans Task Coach.

Ce module contient diverses classes pour représenter des pages d'édition pour différents
types d'objets (tâches, catégories, notes, etc.) dans Task Coach. Il fournit également
les mécanismes pour observer les changements sur ces objets et les refléter dans
l'interface utilisateur.

Classes :
    Page : Classe de base pour les pages d'édition.
    SubjectPage : Gère l'édition du sujet d'un objet.
    TaskSubjectPage : Gère l'édition du sujet d'une tâche avec des priorités.
    CategorySubjectPage : Gère l'édition des catégories.
    AttachmentSubjectPage : Gère l'édition des pièces jointes.
    TaskAppearancePage : Gère l'apparence d'une tâche.
    DatesPage : Gère les dates liées aux tâches.
    ProgressPage : Gère les informations de progression d'une tâche.
    BudgetPage : Gère le budget associé à une tâche.
    EffortPage : Gère l'effort d'une tâche.
    CategoriesPage : Gère les catégories associées aux objets.
    AttachmentsPage : Gère les pièces jointes associées à une tâche ou autre objet.
    NotesPage : Gère les notes associées à un objet.
    PrerequisitesPage : Gère les prérequis associés à une tâche.
    TaskEditBook : Conteneur pour les pages d'édition des tâches.
    CategoryEditBook : Conteneur pour les pages d'édition des catégories.
    NoteEditBook : Conteneur pour les pages d'édition des notes.
    AttachmentEditBook : Conteneur pour les pages d'édition des pièces jointes.
    EffortEditBook : Gère l'édition des efforts.
    Editor : Fenêtre principale de l'éditeur pour différents objets.
"""

# from builtins import str
# from builtins import range
# import datetime
import wx
import logging

import os.path

# try:
from pubsub import pub

# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub

from taskcoachlib import widgets, patterns, command, operating_system, render
from taskcoachlib.domain import task, date, note, attachment, base

# from taskcoachlib.gui import uicommand, windowdimensionstracker
from taskcoachlib.gui.uicommand import uicommand
from taskcoachlib.gui import windowdimensionstracker, artprovider

# import taskcoachlib.gui.viewer
from taskcoachlib.gui import viewer
from taskcoachlib.gui.viewer.attachment import AttachmentViewer
from taskcoachlib.gui.viewer.category import (
    BaseCategoryViewer,
)  # circular import !
from taskcoachlib.gui.viewer.effort import EffortViewer
from taskcoachlib.gui.viewer.note import BaseNoteViewer
from taskcoachlib.gui.viewer.task import CheckableTaskViewer

# for don't have AttributeError: partially initialized module 'taskcoachlib.gui.*'
# has no attribute '*' (most likely due to a circular import) :
# from taskcoachlib.gui.viewer import category, attachment, note, task
# from . import entry, attributesync
from taskcoachlib.gui.dialog import entry, attributesync
from taskcoachlib.gui.newid import IdProvider
from taskcoachlib.i18n import _

from taskcoachlib.thirdparty import smartdatetimectrl as sdtc
from taskcoachlib.help.balloontips import BalloonTipManager

log = logging.getLogger(__name__)


# --- System Theme Resolution Helpers ---
# Single point for converting domain symbolic constants to wx values.
# Domain SSOT methods return these constants; UI uses these helpers to resolve.


def resolve_color(value):
    """Convert domain color value to wx.Colour.

    Args:
        value: Color tuple (r,g,b), symbolic constant, or wx.Colour

    Returns:
        wx.Colour instance
    """
    if value == base.SYSTEM_FG_COLOR:
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    elif value == base.SYSTEM_BG_COLOR:
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    elif isinstance(value, (tuple, list)):
        return wx.Colour(*value)
    elif isinstance(value, wx.Colour):
        return value
    else:
        import inspect

        caller = inspect.stack()[1]
        log.debug(
            f"resolve_color: unhandled value {repr(value)}"
            f"from {caller[1]}:{caller[1]:d} in {caller[3]}"
        )
        return wx.NullColour


def resolve_font(value):
    """Convert domain font value to wx.Font.

    Args:
        value: wx.Font or symbolic constant (SYSTEM_FONT)

    Returns:
        wx.Font instance, or wx.NullFont if value is unhandled (bug)
    """
    if value == base.SYSTEM_FONT:
        return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    elif isinstance(value, wx.Font):
        return value
    else:
        import inspect

        caller = inspect.stack()[1]
        log.debug(
            f"resolve_font: unhandled value {repr(value)}"
            f"from {caller[1]}:{caller[1]:d} in {caller[3]}"
        )
        return wx.NullFont


# Classe Page qui représente une page d'édition
class Page(patterns.Observer, widgets.BookPage):
    """
    Classe de base pour les pages d'édition dans Task Coach.

    Gère l'affichage et la synchronisation des attributs des objets de domaine.

    Attributs :
        columns (int) : Nombre de colonnes dans la page.

    Méthodes :
        __init__(self, items, *args, **kwargs) : Initialise la page avec les objets à éditer.
        selected (self) : Méthode appelée lorsque la page est sélectionnée.
        addEntries (self) : Ajoute les entrées à la page (doit être implémentée par les sous-classes).
        entries (self) : Retourne un dictionnaire des entrées par nom de colonne.
        setFocusOnEntry (self, column_name) : Définit le focus sur une entrée spécifique.
        close (self) : Ferme la page et libère les ressources.
    """

    columns = 2  # Par défaut, deux colonnes pour l'édition.

    def __init__(self, items, parent, *args, **kwargs):
        # def __init__(self, items: List, *args, **kwargs) -> None:
        """
        Initialise la page avec les éléments à éditer.

        Args :
            items (list) : Liste des objets de domaine à éditer.
            parent (wx.Window) : La fenêtre parente de cette page.
            *args : Arguments positionnels génériques.
            **kwargs : Arguments de mots clés génériques.
        """
        # --- LOG 1 : À l'entrée de __init__ de Page ---
        log.debug(f"--- Page.__init__ entrée ---")
        log.debug(f"  items: {items}")
        log.debug(f"  parent (reçu par Page): {parent}")
        log.debug(f"  *args (reçus par Page): {args}")
        log.debug(f"  **kwargs (reçus par Page): {kwargs}")
        log.debug("Page : Initialisation MRO:", Page.__mro__)
        self.items = items
        self.__observers = []
        # # super().__init__(columns=self.columns, *args, **kwargs)
        # super().__init__(*args, **kwargs)

        # --- LOG 2 : Avant la vérification/ajout de 'columns' ---
        log.debug(f"  Page.__init__ - kwargs avant 'columns' check: {kwargs}")
        # # Assurez-vous que 'columns' n'est pas déjà dans kwargs
        # # et passez-le en tant qu'argument positionnel au constructeur de BookPage via super()
        # # Note: Cela suppose que 'columns' est destiné à BookPage et que BookPage attend un argument positionnel pour cela.
        # if 'columns' in kwargs:
        #     # Si columns est déjà dans kwargs, c'est probablement un problème d'appelant
        #     # ou un cas où l'appelant veut surcharger self.columns.
        #     # Dans ce cas, il faut décider quelle valeur prendre.
        #     # Pour l'erreur "multiple values", la solution est de le retirer de kwargs.
        #     passed_columns = kwargs.pop('columns')
        #     if passed_columns != self.columns:
        #         print(f"Warning: Page.columns ({self.columns}) is different from columns passed in kwargs ({passed_columns}). Using {self.columns}.")
        #     # Ou, si vous voulez toujours que la valeur passée dans kwargs prenne le dessus:
        #     # self.columns = passed_columns
        #
        # # Passer self.columns comme premier argument positionnel attendu par BookPage
        # # L'ordre dans *args est crucial ici.
        # # Si BookPage attend (parent, columns, ...) alors le 'parent' doit venir des *args ou être passé explicitement.
        # # Vous devez savoir comment BookPage est censé être appelé.
        # # D'après votre BookPage.__init__(self, parent, columns, growableColumn=None, *args, **kwargs):
        # # Il attend `parent` et `columns` comme arguments positionnels.
        #
        # # Donc, vous devez extraire le 'parent' des *args ou le passer directement.
        # # Si 'parent' est le premier dans *args:
        # parent_arg = args[0] if args else None # Assurez-vous que parent est bien passé
        # remaining_args = args[1:] if args else args
        #
        # # Appel à super() en passant les arguments dans l'ordre attendu par BookPage
        # # et en s'assurant que 'columns' n'est pas passé deux fois.
        # # C'est la ligne la plus critique.
        # super().__init__(parent_arg, self.columns, *remaining_args, **kwargs)

        # S'assurer que 'columns' est dans kwargs avant d'appeler super().
        # La valeur de 'Page.columns' est utilisée ici comme valeur par défaut pour *cette* page,
        # mais elle peut être surchargée si 'columns' est déjà dans kwargs.
        if "columns" not in kwargs:
            kwargs["columns"] = self.columns
            # --- LOG 3 : Après l'ajout de 'columns' ---
            log.debug(
                f"  Page.__init__ - Ajout de 'columns' à kwargs: {self.columns}"
            )
        log.debug(f"  Page.__init__ - kwargs après 'columns' check: {kwargs}")

        # Appelle le constructeur de la super-classe (via le MRO).
        # Ici, 'parent' n'est PAS passé explicitement car c'est la classe appelante (TaskCoach)
        # qui devrait passer 'parent' au premier constructeur dans le MRO (probablement Observer ou Page elle-même).
        # Chaque __init__ dans la chaîne super() va ensuite se passer les arguments nécessaires.
        # Il est important que la classe qui *crée* une instance de Page fournisse le 'parent'.

        # Si Page *doit* prendre un parent comme argument:
        # def __init__(self, items, parent, *args, **kwargs):
        #    self.items = items
        #    if 'columns' not in kwargs:
        #        kwargs['columns'] = self.columns
        #    super().__init__(parent, *args, **kwargs)
        # Cela suppose que le parent est toujours le premier argument positionnel après 'items'.

        # --- LOG 4 : Avant l'appel à super().__init__ ---
        log.debug(f"  Page.__init__ - Appel de super().__init__ avec:")
        log.debug(f"    parent passé à super: {parent}")
        log.debug(f"    *args passés à super: {args}")
        log.debug(f"    **kwargs passés à super: {kwargs}")
        # Appelle le constructeur de la super-classe via le MRO.
        # # Si le parent est déjà géré par l'infrastructure de TaskCoach via le MRO et les kwargs:
        # super().__init__(*args, **kwargs)  # Ceci est l'appel standard pour super() dans héritage multiple.
        # # Il transmet *tous* les arguments restants.
        # Le 'parent' est explicitement passé comme premier argument positionnel
        # car wx.Panel (via BookPage) s'attend à cela.
        super().__init__(parent, **kwargs)
        # parent est passé explicitement : Vous passez parent directement
        # comme le premier argument positionnel de super()
        # (qui est BookPage via le MRO).
        # Cela satisfait le premier paramètre attendu par BookPage.__init__.
        # *args est supprimé : En retirant *args de l'appel à super(),
        # le tuple problématique ((), {}) n'est plus passé comme argument positionnel.
        # **kwargs est dépaqueté correctement :
        # La ligne if 'columns' not in kwargs: kwargs['columns'] = self.columns
        # garantit que kwargs contient {'columns': 2}.
        # En passant **kwargs à super(), BookPage.__init__ reçoit columns=2
        # comme argument nommé, ce qui est tout à fait valide car BookPage.__init__
        # a un paramètre columns=None.

        # --- LOG 5 : Après l'appel à super().__init__ ---
        log.debug(f"--- Page.__init__ super().__init__ terminé ---")
        # ⚠️ NE PAS appeler addEntries ici, pour laisser les sous-classes décider
        # self.addEntries()
        self.fit()

    def selected(self):
        """Méthode appelée lorsque la page est sélectionnée.

        Méthode appelée lorsque la page est sélectionnée dans l'interface utilisateur.
        Peut être utilisée pour mettre à jour ou rafraîchir la page.
        """
        pass  # Implémentation des actions lors de la sélection de la page.

    def addEntries(self):
        """Ajoute les entrées de la page. Doit être implémentée par les sous-classes.

        Méthode à implémenter dans les sous-classes pour ajouter des champs d'entrée (widgets).
        Cette méthode définit la logique spécifique à chaque type de page.
        """
        # raise NotImplementedError  # Méthode à implémenter par les sous-classes.
        pass

    def entries(self):
        """Un mappage des noms de colonnes avec les entrées de cette page d'éditeur.

        Retourne un dictionnaire des entrées de la page par nom de colonne.

        Retourne un dictionnaire contenant les champs d'entrée ajoutés à la page.

        Returns :
            dict : Les champs d'entrée ajoutés par `addEntries`."""
        return dict()  # Retourne les champs d'édition.

    def setFocusOnEntry(self, column_name):
        """
        Définit le focus sur une entrée spécifique.

        Définit le focus sur un champ d'entrée spécifique basé sur le nom de la colonne.

        Args :
            column_name (str) : Le nom de la colonne de l'entrée sur laquelle positionner le focus.
        """
        # Définit le focus sur une colonne particulière.
        try:
            the_entry = self.entries()[column_name]
        except KeyError:
            the_entry = self.entries()["firstEntry"]
            # the_entry = self.entries().get("firstEntry")
            if the_entry is None:
                return
        self.__set_selection_and_focus(the_entry)

    def __set_selection_and_focus(self, the_entry):
        """Définit la sélection et le focus sur une entrée.

        Si l'entrée contient du texte sélectionnable, sélectionnez le texte afin que l'utilisateur
        puisse commencer à taper dessus immédiatement, sauf sous Linux car il
        écrase le presse-papiers X.

        Args :
            the_entry (TextCtrl) : L'entrée à sélectionner et à mettre en focus.
        """
        if the_entry is not None and self.focusTextControl():
            the_entry.SetFocus()
            try:
                if operating_system.isWindows() and isinstance(
                    the_entry, wx.TextCtrl
                ):
                    # # XXXFIXME: See SR #325. Disable this for Now.
                    #
                    # # This ensures that if the TextCtrl value is more than can
                    # # be displayed, it will display the start instead of the
                    # # end:
                    # try:
                    #     import SendKeys
                    # except ImportError:
                    #     from taskcoachlib.thirdparty import (
                    #         SendKeys,
                    #     )  # pylint: disable=W0404
                    # SendKeys.SendKeys("{END}+{HOME}")

                    # Scrol to left...
                    the_entry.SetInsertionPoint(0)
                the_entry.SetSelection(-1, -1)  # Sélectionner tout le texte
            except (AttributeError, TypeError):
                pass  # Not a TextCtrl

    def focusTextControl(self):
        """Retourne True si le contrôle de texte doit recevoir le focus."""
        return True

    def close(self):
        """Ferme la page et nettoie les ressources.

        Ferme la page d'édition et nettoie les ressources associées.
        Peut être utilisé pour libérer les ressources graphiques ou observer les objets.
        """
        self.removeInstance()
        for entry in list(self.entries().values()):
            if isinstance(entry, widgets.DateTimeCtrl):
                entry.Cleanup()
        # TODO: try:
        # for each_entry in list(self.entries().values()):
        #     if isinstance(each_entry, widgets.DateTimeCtrl):
        #         each_entry.Cleanup()


class ScrolledPage(patterns.Observer, widgets.notebook.ScrolledBookPage):
    """A scrollable page for dialogs with lots of content (e.g., Appearance tab)."""

    columns = 2

    def __init__(self, items, *args, **kwargs):
        self.items = items
        super().__init__(columns=self.columns, *args, **kwargs)
        self.addEntries()
        self.fit()


# Les autres classes de la même manière...


class SubjectPage(Page):
    """
    Page d'édition pour modifier le sujet d'un objet dans Task Coach.

    Cette page permet à l'utilisateur de modifier le champ "sujet" des objets,
    qui peut représenter le titre ou la description courte de l'objet.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition du sujet.
        subject (self) : Retourne l'objet d'édition du sujet.
    """

    pageName = "subject"
    pageTitle = _("Description")
    pageIcon = "pencil_icon"

    def __init__(self, items, parent, settings, *args, **kwargs):
        """
        Initializes the SubjectPage with the following arguments:

        - items: A list of task objects representing the selected tasks.
        - parent: The parent window of this page.
        - settings: The application settings object.
        """
        # --- LOG 1 : À l'entrée de __init__ de SubjectPage ---
        log.debug(f"--- SubjectPage.__init__ entrée ---")
        log.debug(f"  items: {items}")
        log.debug(f"  parent (reçu par SubjectPage): {parent}")
        log.debug(f"  settings (reçu par SubjectPAge): {settings}")
        log.debug(f"  *args (reçus par SubjectPage): {args}")
        log.debug(f"  **kwargs (reçus par SubjectPage): {kwargs}")
        self._modificationTextEntry = None
        self._descriptionSync = None
        self._subjectSync = None
        self._descriptionEntry = None
        self._subjectEntry = None
        self._settings = settings
        # --- LOG 2 : Avant l'appel à super().__init__ ---
        log.debug(f"  SubjectPage.__init__ - Appel de super().__init__ avec:")
        log.debug(f"    items passé à super: {items}")
        log.debug(f"    parent passé à super: {parent}")
        log.debug(f"    *args passés à super: {args}")
        log.debug(f"    **kwargs passés à super: {kwargs}")
        super().__init__(items, parent, *args, **kwargs)
        # Ajouter les champs d'entrée (comme les textCtrl pour le sujet et la description) :
        self.addEntries()

    def SetFocus(self):
        """
        Sets focus to the page, but avoids selecting the text control on GTK platforms
        to prevent overriding the X selection.
        """
        # Skip this on GTK because it selects the control's text, which
        # overrides the X selection. Simply commenting out the SetFocus() in
        # __load_perspective is not enough because the aui notebook calls this
        # when the user selects a tab.
        if self.focusTextControl():
            super().SetFocus()

    def focusTextControl(self):
        """
        Checks the application settings to determine if text controls should receive
        focus on GTK platforms.
        """
        return self._settings.getboolean("os_linux", "focustextentry")

    def addEntries(self):
        """
        Ajoute les champs d'entrée spécifiques pour l'édition du sujet.

        Adds controls for subject, description, creation date/time, and modification date/time.
        """
        # Ajoute les widgets pour éditer le sujet.
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()
        # TODO : à remplacer par
        # self.addDateTimeEntries("Creation", "creationDateTime")
        # self.addDateTimeEntries("Modification", "modificationDateTime")

    # def subject(self):
    #     """
    #     Retourne l'objet sujet à éditer.
    #
    #     Returns :
    #         Objet à éditer, généralement un texte.
    #     """
    #     pass

    def addSubjectEntry(self):
        # pylint: disable=W0201
        """Adds a subject entry to the page.

        Adds a single-line text control for editing the subject of the selected task(s).
        It also creates an AttributeSync object to manage synchronization between the control
        and the task object(s).

        Returns :
            None
        """
        current_subject = (
            self.items[0].subject()
            if len(self.items) == 1
            else _("Edit to change all subjects")
        )
        self._subjectEntry = widgets.SingleLineTextCtrl(self, current_subject)
        self._subjectSync = attributesync.AttributeSync(
            "subject",
            self._subjectEntry,
            current_subject,
            self.items,
            command.EditSubjectCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].subjectChangedEventType(),
        )
        # TODO: Ajoutez un commentaire pour expliquer le but de ce code:
        self.addEntry(  # de BookPage !
            _("Subject"),  # Ceci devient controls[0] (le texte du libellé)
            self._subjectEntry,  # Ceci devient controls[1] (le wx.TextCtrl)
            flags=[
                wx.ALIGN_RIGHT,
                wx.EXPAND,
            ],  # Ceci devient flags[0] et flags[1]
        )
        # Add a comment to explain the purpose of this code

    def __modification_text(self):
        # def __modification_text(self) -> str:
        """Calculates the modification text for the page.

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
        # essai:
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
        # pylint: disable=W0201
        """
        Adds a multi-line text control for editing the description of the selected task(s).
        It also creates an AttributeSync object to manage synchronization between the control
        and the task object(s). Optionally sets a custom font based on application settings.
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
        self._descriptionEntry = widgets.MultiLineTextCtrl(
            self, current_description
        )
        native_info_string = self._settings.get("editor", "descriptionfont")
        # font = wx.FontFromNativeInfoString(native_info_string) if native_info_string else None
        # https://pythonhosted.org/wxPython/wx.Font.html#wx.Font
        font = wx.Font(native_info_string) if native_info_string else None

        if font:
            self._descriptionEntry.SetFont(font)
        self._descriptionSync = attributesync.AttributeSync(
            "description",
            self._descriptionEntry,
            current_description,
            self.items,
            command.EditDescriptionCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].descriptionChangedEventType(),
        )
        self.addEntry(
            _("Description"),
            self._descriptionEntry,
            growable=True,
            flags=[wx.ALIGN_TOP | wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addDateTimeEntries(self, label, attribute_name):
        # TODO: remplacer les 2 fonctions suivantes pas celle-ci, régler le problème de dateTime_range
        date_times = [getattr(item, attribute_name)() for item in self.items]
        min_date, max_date = min(date_times), max(date_times)
        # date_text = render.dateTime_range(min_date, max_date)
        date_text = render.dateTime(range(min_date, max_date))

    def addCreationDateTimeEntry(self):
        """Cette méthode ajoute des étiquettes affichant les dates de création
        des tâches sélectionnées.
        Elles calculent les dates minimale et maximale pour les tâches multiples
        et affichent un intervalle si nécessaire.
        Elles s'abonnent à des événements pour mettre à jour l'affichage
        de la date de modification lorsque celle-ci change.
        """
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
        self.addEntry(
            _("Creation date"),
            creation_text,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addModificationDateTimeEntry(self):
        """Cette méthode ajoute des étiquettes affichant les dates de modification des tâches sélectionnées.

        Elles calculent les dates minimale et maximale pour les tâches multiples et affichent un intervalle si nécessaire.
        Elles s'abonnent à des événements pour mettre à jour l'affichage de la date de modification lorsque celle-ci change.
        """
        self._modificationTextEntry = wx.StaticText(
            self, label=self.__modification_text()
        )
        self.addEntry(
            _("Modification date"),
            self._modificationTextEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )
        for eventType in self.items[0].modificationEventTypes():
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                patterns.Publisher().registerObserver(
                    self.onAttributeChanged_Deprecated,
                    eventType=eventType,
                    eventSource=self.items[0],
                )

    def __modification_text(self):
        modification_datetimes = [
            item.modificationDateTime() for item in self.items
        ]
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

    def onAttributeChanged(self, newValue, sender):
        """Ces méthodes sont des callbacks appelés lorsque la date de modification
        d'une tâche change.
        Elles mettent à jour le texte de l'étiquette correspondante.
        """
        self._modificationTextEntry.SetLabel(self.__modification_text())

    def onAttributeChanged_Deprecated(self, *args, **kwargs):
        """Ces méthodes sont des callbacks appelés lorsque la date de modification d'une tâche change.
        Elles mettent à jour le texte de l'étiquette correspondante.
        """
        self._modificationTextEntry.SetLabel(self.__modification_text())

    def close(self):
        """Cette méthode est appelée lors de la fermeture de la page.
        Elle se désabonne des événements pour éviter les fuites de mémoire.
        """
        super().close()
        for eventType in self.items[0].modificationEventTypes():
            try:
                pub.unsubscribe(self.onAttributeChanged, eventType)
            except pub.TopicNameError:
                pass
        patterns.Publisher().removeObserver(self.onAttributeChanged_Deprecated)

    def entries(self):
        """Cette méthode retourne un dictionnaire contenant des références
        vers les contrôles de la page,
        utilisé probablement pour la navigation ou d'autres fonctionnalités.
        """
        return dict(
            firstEntry=self._subjectEntry,
            subject=self._subjectEntry,
            description=self._descriptionEntry,
            creationDateTime=self._subjectEntry,
            modificationDateTime=self._subjectEntry,
        )


class TaskSubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet et la priorité d'une tâche.

    Cette classe hérite de SubjectPage et ajoute la gestion de la priorité.
    Cette page permet de modifier le titre et la priorité d'une tâche dans Task Coach.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition du sujet et de la priorité.
                            Méthode lancée dans la classe SubjectPage.
    """

    # J'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    #     self._prioritySync = None
    #     self._priorityEntry = None

    def __init__(self, items, parent, settings, *args, **kwargs):
        # --- LOG 1 : À l'entrée de __init__ de SubjectPage ---
        log.debug(f"--- TaskSubjectPage.__init__ entrée ---")
        log.debug(f"  items: {items}")
        log.debug(f"  parent (reçu par SubjectPage): {parent}")
        log.debug(f"  settings (reçu par SubjectPAge): {settings}")
        log.debug(f"  *args (reçus par SubjectPage): {args}")
        log.debug(f"  **kwargs (reçus par SubjectPage): {kwargs}")
        # --- LOG 2 : Avant l'appel à super().__init__ ---
        log.debug(
            f"  TaskSubjectPage.__init__ - Appel de super().__init__ avec:"
        )
        log.debug(f"    items passé à super: {items}")
        log.debug(f"    parent passé à super: {parent}")
        log.debug(f"    settings passé à super: {settings}")
        log.debug(f"    *args passés à super: {args}")
        log.debug(f"    **kwargs passés à super: {kwargs}")
        super().__init__(items, parent, settings, args, kwargs)
        self._prioritySync = None
        self._priorityEntry = None

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour le sujet et la priorité de la tâche.

        Ajoute les entrées de l'interface, en insérant le champ de priorité.
        """
        # Ajoute les widgets pour éditer le sujet et la priorité de la tâche.
        # Override to insert a priority entry between the description and the
        # creation Date/time entry
        self.addSubjectEntry()
        self.addDescriptionEntry()
        self.addPriorityEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addPriorityEntry(self):
        # pylint: disable=W0201
        """Ajoute un champ pour modifier la priorité de la tâche.

        Cette méthode ajoute un contrôle spin (widgets.SpinCtrl) à la page pour modifier la priorité de la ou des tâches sélectionnées.
        Elle récupère la priorité actuelle de la première tâche (si une seule est sélectionnée) ou la met à 0. (par défaut).
        Il crée un objet AttributeSync pour synchroniser la valeur du contrôle de rotation avec l'attribut "priorité" du ou des objets de tâche.
        Il ajoute une étiquette d'entrée pour "Priorité" et le faites tourner le contrôle sur la page en utilisant self.addEntry.
        """
        current_priority = (
            self.items[0].priority() if len(self.items) == 1 else 0
        )
        # Nous introduisons une constante nommée MAX_PRIORITY pour améliorer la lisibilité
        # et faciliter la modification de la valeur de priorité maximale à l'avenir.
        MAX_PRIORITY = 10
        self._priorityEntry = widgets.SpinCtrl(
            self,
            size=(100, -1),
            value=current_priority,
            min=0,
            max=MAX_PRIORITY,
        )
        self._prioritySync = attributesync.AttributeSync(
            "priority",
            self._priorityEntry,
            current_priority,
            self.items,
            command.EditPriorityCommand,
            wx.EVT_SPINCTRL,
            self.items[0].priorityChangedEventType(),
        )
        # self.addEntry(_("Priority"), self._priorityEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Priority"),
            self._priorityEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def entries(self):
        """Retourne un dictionnaire contenant les références aux contrôles.

        This method overrides the entries method from the parent class.
        It calls the parent's entries method to get a dictionary containing references to existing controls.
        It adds a new key-value pair to the dictionary, where the key is "priority" and the value is the reference to the spin control (self._priorityEntry).
        It returns the updated dictionary containing references to all controls on the page.
        """
        entries = super().entries()
        entries["priority"] = self._priorityEntry
        return entries


class CategorySubjectPage(SubjectPage):
    """
    Page d'édition pour le sujet des catégories.

    Cette classe hérite de SubjectPage et ajoute la gestion des sous-catégories exclusives.
    Cette page permet de modifier le titre d'une catégorie dans Task Coach.
    """

    # Utilise la logique d'édition du sujet de base.
    # J'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    #     self._exclusiveSubcategoriesSync = None
    #     self._exclusiveSubcategoriesCheckBox = None

    def addEntries(self):
        """
        Ajoute les entrées de l'interface, en insérant le champ de sous-catégories exclusives.
        """
        # Override to insert an exclusive subcategories entry
        # between the description and the creation Date/time entry
        self.addSubjectEntry()  # Sujet
        self.addDescriptionEntry()  # Description
        self.addExclusiveSubcategoriesEntry()  # Sous-catégories exclusives (ajouté ici)
        self.addStylePriorityEntry()
        self.addCreationDateTimeEntry()  # Date de création
        self.addModificationDateTimeEntry()  # Date de modification

    def addExclusiveSubcategoriesEntry(self):
        # pylint: disable=W0201
        """
        Ajoute un champ pour définir si les sous-catégories doivent être exclusives.
        """
        currentExclusivity = (
            self.items[0].hasExclusiveSubcategories()
            if len(self.items) == 1
            else False
        )
        panel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._exclusiveSubcategoriesCheckBox = wx.CheckBox(
            panel, label=_("Mutually exclusive")
        )
        self._exclusiveSubcategoriesCheckBox.SetValue(currentExclusivity)
        panelSizer.Add(
            self._exclusiveSubcategoriesCheckBox, 0, wx.ALIGN_CENTER_VERTICAL
        )
        hintText = wx.StaticText(
            panel, label=_("Subcategories are mutually exclusive")
        )
        hintText.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        panelSizer.Add(hintText, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        panel.SetSizer(panelSizer)
        self._exclusiveSubcategoriesSync = attributesync.AttributeSync(
            "hasExclusiveSubcategories",
            self._exclusiveSubcategoriesCheckBox,
            currentExclusivity,
            self.items,
            command.EditExclusiveSubcategoriesCommand,
            wx.EVT_CHECKBOX,
            self.items[0].exclusiveSubcategoriesChangedEventType(),
        )
        self.addEntry(
            _("Subcategories"),
            panel,
            flags=[None, wx.ALL],
        )

    def addStylePriorityEntry(self):
        # pylint: disable=W0201
        currentPriority = (
            self.items[0].stylePriority() if len(self.items) == 1 else 0
        )
        self._stylePriorityEntry = widgets.SpinCtrl(
            self, size=(100, -1), value=currentPriority, min=-999, max=999
        )
        self._stylePrioritySync = attributesync.AttributeSync(
            "stylePriority",
            self._stylePriorityEntry,
            currentPriority,
            self.items,
            command.EditStylePriorityCommand,
            wx.EVT_SPINCTRL,
            self.items[0].stylePriorityChangedEventType(),
        )
        self.addEntry(_("Style priority"), self._stylePriorityEntry)


class AttachmentSubjectPage(SubjectPage):
    """
    Classe de page d'édition pour les pièces jointes.

    Cette classe hérite de `SubjectPage` et fournit des champs d'édition spécifiques aux pièces jointes, y compris :

       * Sujet (hérité de `SubjectPage`)
       * Emplacement du fichier
       * Description (hérité de `SubjectPage`)
       * Date/heure de création (hérité de `SubjectPage`)
       * Date/heure de modification (hérité de `SubjectPage`)

    La classe ajoute un champ d'édition supplémentaire pour l'emplacement du fichier de la pièce jointe.
    Elle gère également la synchronisation de l'emplacement avec l'objet de tâche sous-jacent à l'aide de la classe `attributesync.AttributeSync`.

    Attributs :
        _locationSync (attributesync.AttributeSync, optionnel) : Objet de synchronisation pour l'attribut "location" des pièces jointes.
        _locationEntry (widgets.SingleLineTextCtrl): Champ de saisie pour l'emplacement du fichier de la pièce jointe.

    Méthodes :
        addEntries (self) :
           Ajoute les champs d'édition spécifiques aux pièces jointes.

        addLocationEntry (self) :
           Ajoute un champ d'édition pour l'emplacement du fichier de la pièce jointe. Gère également la synchronisation de l'emplacement avec l'objet de tâche.

        onSelectLocation (self, event) :
           Permet à l'utilisateur de sélectionner un fichier à l'aide d'un sélecteur de pièces jointes. Met à jour le champ d'emplacement et le sujet en conséquence.
    """

    # Map type_ values to human-readable names and icons
    TYPE_INFO = {
        "file": (_("File"), "document_icon"),
        "folder": (_("Folder"), "folder_blue_icon"),
        "uri": (_("Link"), "earth_blue_icon"),
        "mail": (_("Email"), "envelope_icon"),
        "unknown": (_("Unknown"), None),
    }

    def _isFolderUri(self, item):
        """Check if a URI attachment points to a local folder."""
        if item.type_ != "uri":
            return False
        location = item.location()
        if location.startswith("file://"):
            import urllib.request
            import os

            try:
                path = urllib.request.url2pathname(location[7:])
                return os.path.isdir(path)
            except Exception:
                return False
        return False

    # j'ai ajouté __init__
    # def __init__(self, items, parent, settings, *args, **kwargs):
    #     super().__init__(items, parent, settings, args, kwargs)
    # Objet de synchronisation pour l'attribut "location" des pièces jointes.
    #     self._locationSync = None
    # Champ de saisie pour l'emplacement du fichier de la pièce jointe.
    #     self._locationEntry = None

    def addEntries(self):
        """Ajoute les champs d'édition spécifiques aux pièces jointes."""
        # Remplacer pour insérer une entrée d'emplacement entre le sujet et
        # l'entrée de description
        self.addSubjectEntry()
        self.addTypeEntry()
        self.addLocationEntry()
        self.addDescriptionEntry()
        self.addCreationDateTimeEntry()
        self.addModificationDateTimeEntry()

    def addTypeEntry(self):
        """Add a read-only type field with icon."""
        import os

        if len(self.items) == 1:
            item = self.items[0]
            if self._isFolderUri(item):
                type_name, icon_name = self.TYPE_INFO.get("folder")
            else:
                item_type = item.type_
                type_name, icon_name = self.TYPE_INFO.get(
                    item_type, (item_type, None)
                )
                # Check if file exists for file attachments
                if item_type == "file":
                    attachmentBase = self._settings.get(
                        "file", "attachmentbase"
                    )
                    if not os.path.exists(
                        item.normalizedLocation(attachmentBase)
                    ):
                        icon_name = "fileopen_red"
        else:
            # Multiple items - show type if all same, otherwise "Mixed"
            types = set(item.type_ for item in self.items)
            if len(types) == 1:
                item_type = types.pop()
                type_name, icon_name = self.TYPE_INFO.get(
                    item_type, (_("Unknown"), None)
                )
            else:
                type_name = _("Mixed")
                icon_name = None

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if icon_name:
            bitmap = wx.ArtProvider.GetBitmap(icon_name, wx.ART_MENU, (16, 16))
            if bitmap.IsOk():
                icon = wx.StaticBitmap(panel, bitmap=bitmap)
                sizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        type_label = wx.StaticText(panel, label=type_name)
        sizer.Add(type_label, 0, wx.ALIGN_CENTER_VERTICAL)
        panel.SetSizer(sizer)
        self.addEntry(_("Type"), panel, flags=[None, wx.ALIGN_CENTER_VERTICAL])

    def addLocationEntry(self):
        """Ajoute un champ d'édition pour l'emplacement du fichier de la pièce jointe.
        Gère également la synchronisation de l'emplacement avec l'objet de tâche.
        """
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        # pylint: disable=W0201
        current_location = (
            self.items[0].location()
            if len(self.items) == 1
            else _("Edit to change location of all attachments")
        )
        # Objet de synchronisation pour l'attribut "location" des pièces jointes.
        self._locationEntry = widgets.SingleLineTextCtrl(
            panel,
            current_location,
            spellCheck=False,  # File paths/URLs shouldn't be spell checked
        )
        # Champ de saisie pour l'emplacement du fichier de la pièce jointe.
        self._locationSync = attributesync.AttributeSync(
            "location",
            self._locationEntry,
            current_location,
            self.items,
            command.EditAttachmentLocationCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].locationChangedEventType(),
        )
        sizer.Add(self._locationEntry, 1, wx.ALL, 3)
        if all(item.type_ == "file" for item in self.items):
            button = wx.Button(panel, wx.ID_ANY, _("Browse"))
            sizer.Add(button, 0, wx.ALL, 3)
            # wx.EVT_BUTTON(button, wx.ID_ANY, self.onSelectLocation)
            button.Bind(wx.EVT_BUTTON, self.onSelectLocation)
        panel.SetSizer(sizer)
        self.addEntry(_("Location"), panel, flags=[None, wx.ALL | wx.EXPAND])

    def onSelectLocation(self, event):  # pylint: disable=W0613
        """Permet à l'utilisateur de sélectionner un fichier à l'aide d'un
        sélecteur de pièces jointes.
        Met à jour le champ d'emplacement et le sujet en conséquence."""
        base_path = self._settings.get("file", "lastattachmentpath")
        if not base_path:
            base_path = os.getcwd()
        filename = widgets.AttachmentSelector(default_path=base_path)

        if filename:
            self._settings.set(
                "file",
                "lastattachmentpath",
                os.path.abspath(os.path.split(filename)[0]),
            )
            if self._settings.get("file", "attachmentbase"):
                filename = attachment.getRelativePath(
                    filename, self._settings.get("file", "attachmentbase")
                )
            self._subjectEntry.SetValue(os.path.split(filename)[-1])
            self._locationEntry.SetValue(filename)
            self._subjectSync.onAttributeEdited(event)
            self._locationSync.onAttributeEdited(event)


class TaskAppearancePage(Page):
    """
    Page d'édition de l'apparence des tâches.

    Cette page permet de modifier des éléments visuels liés aux tâches, comme la couleur,
    la mise en forme, ou d'autres attributs visuels.

    Objectif : Gérer l'apparence des tâches (couleur, police, icône).

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition de l'apparence.
    """

    pageName = "appearance"
    pageTitle = _("Appearance")
    pageIcon = "palette_icon"
    # columns = 5
    columns = 3  # Label, Control, Source
    _vgap = 2
    _hgap = 5
    _borderWidth = 2

    # j'ai ajouté __init__
    def __init__(self, items, *args, **kwargs):
        super().__init__(items, *args, **kwargs)
        self._foregroundColorEntry = None
        self._fontEntry = None
        self._fontSync = None
        self._fontColorSync = None
        self._iconEntry = None
        self._iconSync = None
        self.addEntries()

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour modifier l'apparence de la tâche (couleur, style, etc.).
        """
        self.addCalculatedSection()
        # Show "Override values" header for all single-item edits
        if len(self.items) == 1:
            self.addLine()
            self.addSectionHeader(_("Override values"))
        self.addIconEntry()
        self.addColorEntries()
        self.addFontEntry()
        self.addEffectiveSection()
        # Update derived values now that all widgets exist
        if len(self.items) == 1:
            self._updateDerivedValues()

    def addSectionHeader(self, title, sourceLabel=None):
        """Add a bold section header spanning columns 0-1, optional label in column 2."""
        header = wx.StaticText(self, label=title)
        header.SetFont(header.GetFont().Bold())
        flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT
        self._sizer.Add(
            header,
            self._position.next(2),
            span=(1, 2),
            flag=flag,
            border=self._borderWidth,
        )
        if sourceLabel:
            source = wx.StaticText(self, label=sourceLabel)
            source.SetFont(source.GetFont().Bold())
            self._sizer.Add(
                source,
                self._position.next(1),
                span=(1, 1),
                flag=flag,
                border=self._borderWidth,
            )
        else:
            self._sizer.Add((0, 0), self._position.next(1), span=(1, 1))

    def addCalculatedSection(self):
        """Add read-only display of derived appearance values.

        Layout: 3 columns - Label, Control, Source
        - Tasks: derived from category/parent/status
        - Categories: derived from parent category
        - Notes: derived from parent note (or System Theme)
        - Efforts/Attachments: always System Theme (no inheritance)
        """
        if len(self.items) != 1:
            return
        item = self.items[0]

        self.addSectionHeader(_("Derived values"), _("Source"))
        entryFlags = [
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Label
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Control
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Source
        ]

        # Icon - panel with both bitmap and "N/A" text (show one or the other)
        def rejectNav(evt):
            evt.GetEventObject().Navigate(evt.GetDirection())

        def rejectFocus(evt):
            forward = not wx.GetKeyState(wx.WXK_SHIFT)
            wx.CallAfter(evt.GetEventObject().Navigate, forward)

        self._derivedIconPanel = wx.Panel(self, style=0)
        self._derivedIconPanel.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._derivedIconPanel.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        iconSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._derivedIconDisplay = wx.StaticBitmap(self._derivedIconPanel)
        self._derivedIconDisplay.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._derivedIconDisplay.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._derivedIconName = wx.StaticText(self._derivedIconPanel, label="")
        self._derivedIconName.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._derivedIconName.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._derivedIconNA = wx.StaticText(
            self._derivedIconPanel, label=_("N/A")
        )
        self._derivedIconNA.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._derivedIconNA.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._derivedIconNA.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        iconSizer.Add(self._derivedIconDisplay, 0, wx.ALIGN_CENTER_VERTICAL)
        iconSizer.Add(
            self._derivedIconName, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5
        )
        iconSizer.Add(self._derivedIconNA, 0, wx.ALIGN_CENTER_VERTICAL)
        self._derivedIconPanel.SetSizer(iconSizer)
        self._derivedIconSource = wx.StaticText(self, label="")
        self._derivedIconSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Icon"),
            self._derivedIconPanel,
            self._derivedIconSource,
            flags=entryFlags,
        )

        # Foreground
        # self._derivedFgPicker = widgets.ColourPickerCtrl(
        self._derivedFgPicker = wx.ColourPickerCtrl(
            self,
            colour=wx.BLACK,
            # readOnly=True,
        )
        self._derivedFgSource = wx.StaticText(self, label="")
        self._derivedFgSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Foreground"),
            self._derivedFgPicker,
            self._derivedFgSource,
            flags=entryFlags,
        )

        # Background
        # self._derivedBgPicker = widgets.ColourPickerCtrl(
        self._derivedBgPicker = wx.ColourPickerCtrl(
            self,
            colour=wx.WHITE,  # readOnly=True,
            # colour=WHITE,
        )
        self._derivedBgSource = wx.StaticText(self, label="")
        self._derivedBgSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Background"),
            self._derivedBgPicker,
            self._derivedBgSource,
            flags=entryFlags,
        )

        # Font
        defaultFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self._derivedFontPicker = widgets.FontPickerCtrl(
            self,
            font=defaultFont,
            colour=(0, 0, 0, 255),  # readOnly=True
        )
        self._derivedFontSource = wx.StaticText(self, label="")
        self._derivedFontSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Font"),
            self._derivedFontPicker,
            self._derivedFontSource,
            flags=entryFlags,
        )

        # Note: _updateDerivedValues() is called at end of addEntries() after all widgets exist

        # Subscribe to SSOT derived change events for automatic updates
        for eventType in (
            item.derivedFgColorChangedEventType(),
            item.derivedBgColorChangedEventType(),
            item.derivedIconChangedEventType(),
            item.derivedFontChangedEventType(),
        ):
            self.registerObserver(
                self._onDerivedAppearanceChanged,
                eventType=eventType,
                eventSource=item,
            )

    def _onDerivedAppearanceChanged(self, event):
        """Update derived display when SSOT appearance changes."""
        self._updateDerivedValues()

    def _updateDerivedValues(self):
        """Refresh the derived icon and color displays (pre-override values).

        Unified display logic for all item types. Always shows pickers with
        system theme colors as fallback. No N/A, no hiding.
        """
        if len(self.items) != 1:
            return
        # Guard: only update if derived display widgets exist
        if not hasattr(self, "_derivedIconDisplay"):
            return

        # Get derived values based on item type
        (
            iconValue,
            iconSource,
            fgValue,
            fgSource,
            bgValue,
            bgSource,
            fontValue,
            fontSource,
        ) = self._getDerivedValuesForItem(self.items[0])

        # Display derived values (unified for all item types)
        self._displayDerivedValues(
            iconValue,
            iconSource,
            fgValue,
            fgSource,
            bgValue,
            bgSource,
            fontValue,
            fontSource,
        )

    def _getDerivedValuesForItem(self, item):
        """Get derived appearance values from SSOT accessors.

        Returns: (iconValue, iconSource, fgValue, fgSource, bgValue, bgSource, fontValue, fontSource)

        Uses separate derivedXxx() and derivedXxxSource() accessors.
        """
        # Get derived values and sources using separate accessors
        iconActual = item.derivedIcon()
        iconSource = item.derivedIconSource()
        fgActual = item.derivedFgColor()
        fgSource = item.derivedFgColorSource()
        bgActual = item.derivedBgColor()
        bgSource = item.derivedBgColorSource()
        fontActual = item.derivedFont()
        fontSource = item.derivedFontSource()

        # Get defaults for fallback
        iconDefault = (
            item.effectiveIconDefault()
            if hasattr(item, "effectiveIconDefault")
            else ""
        )
        fgDefault = (
            item.effectiveFgColorDefault()
            if hasattr(item, "effectiveFgColorDefault")
            else base.SYSTEM_FG_COLOR
        )
        bgDefault = (
            item.effectiveBgColorDefault()
            if hasattr(item, "effectiveBgColorDefault")
            else base.SYSTEM_BG_COLOR
        )
        fontDefault = (
            item.effectiveFontDefault()
            if hasattr(item, "effectiveFontDefault")
            else base.SYSTEM_FONT
        )

        # Resolve to wx values: use actual if set, otherwise default
        iconValue = iconActual if iconActual else iconDefault
        fgValue = resolve_color(fgActual if fgActual else fgDefault)
        bgValue = resolve_color(bgActual if bgActual else bgDefault)
        fontValue = resolve_font(fontActual if fontActual else fontDefault)

        return (
            iconValue,
            iconSource,
            fgValue,
            fgSource,
            bgValue,
            bgSource,
            fontValue,
            fontSource,
        )

    def _displayDerivedValues(
        self,
        iconValue,
        iconSource,
        fgValue,
        fgSource,
        bgValue,
        bgSource,
        fontValue,
        fontSource,
    ):
        """Display derived values in the UI.

        Domain SSOT methods (derivedXxx) return:
        - Actual value + source when inherited from parent
        - Symbolic constant (e.g., base.SYSTEM_FG_COLOR) + "System Theme" when no parent

        This method uses resolve_color/resolve_font helpers to convert
        symbolic constants to actual wx values. No fallback logic here -
        domain is the single source of truth.

        Icons are special: no system theme exists, so empty icon shows "N/A".
        """
        # --- Icon ---
        # Icons have no system theme - show "N/A" when no inherited value
        if iconValue:
            bitmap = wx.ArtProvider.GetBitmap(iconValue, wx.ART_MENU, (16, 16))
            self._derivedIconDisplay.SetBitmap(bitmap)
            self._derivedIconDisplay.Show()
            # Look up icon name from artprovider metadata
            iconData = artprovider.chooseableItems.get(iconValue, {})
            iconName = iconData.get("name", iconValue)
            self._derivedIconName.SetLabel(iconName)
            self._derivedIconName.Show()
            self._derivedIconNA.Hide()
            self._derivedIconSource.SetLabel(
                iconSource or _("Initializing...")
            )
        else:
            self._derivedIconDisplay.Hide()
            self._derivedIconName.Hide()
            self._derivedIconNA.Show()
            self._derivedIconSource.SetLabel(_("N/A"))
        self._derivedIconPanel.Layout()

        # --- Foreground Color ---
        # fgValue is either a color tuple or base.SYSTEM_FG_COLOR constant
        # fgSource is either "[Category] Name" or "System Theme"
        derivedFgColour = resolve_color(fgValue)
        self._derivedFgPicker.SetColour(derivedFgColour)
        self._derivedFgPicker.Show()
        self._derivedFgSource.SetLabel(fgSource or _("Initializing..."))

        # --- Background Color ---
        # bgValue is either a color tuple or base.SYSTEM_BG_COLOR constant
        # bgSource is either "[Category] Name" or "System Theme"
        derivedBgColour = resolve_color(bgValue)
        self._derivedBgPicker.SetColour(derivedBgColour)
        self._derivedBgPicker.Show()
        self._derivedBgSource.SetLabel(bgSource or _("Initializing..."))

        # --- Font ---
        # fontValue is either a wx.Font or base.SYSTEM_FONT constant
        # fontSource is either "[Category] Name" or "System Theme"
        derivedFont = resolve_font(fontValue)
        self._derivedFontPicker.SetSelectedFont(derivedFont)
        self._derivedFontPicker.Show()
        self._derivedFontSource.SetLabel(fontSource or _("Initializing..."))

        # Update font picker demo colors to match derived colors
        self._derivedFontPicker.SetSelectedColour(derivedFgColour)
        self._derivedFontPicker.SetSelectedBgColour(derivedBgColour)

        # Note: override entries now track effective values, not derived
        # (updated in _updateEffectiveValues)

    def addColorEntries(self):
        self.addColorEntry(_("Foreground color"), "foreground", wx.BLACK)
        self.addColorEntry(_("Background color"), "background", wx.WHITE)

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
            entry.EVT_COLORENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        setattr(self, "_%sColorSync" % colorType, colorSync)
        # self.addEntry(labelText, colorEntry, flags=[None, wx.ALL])
        self.addEntry(labelText, colorEntry, flags=[wx.ALIGN_RIGHT, wx.ALL])

    def addFontEntry(self):
        # pylint: disable=W0201,E1101
        currentFont = self.items[0].font() if len(self.items) == 1 else None
        # currentColor = self._foregroundColorEntry.GetValue()  # d'où ça vient ?
        # Use override color if set, otherwise use effective/inherited color
        # Tasks and Categories have effectiveFgColor() (SSOT)
        # Notes/Efforts/Attachments use foregroundColor(recursive=True)
        overrideFgColor = self._foregroundColorEntry.GetValue()
        overrideBgColor = self._backgroundColorEntry.GetValue()
        # self._fontEntry = entry.FontEntry(self, currentFont, currentColor)
        if len(self.items) == 1:
            item = self.items[0]
            if hasattr(item, "effectiveFgColor"):
                # Tasks and Categories use SSOT effective methods
                currentColor = (
                    overrideFgColor
                    if overrideFgColor
                    else item.effectiveFgColor()
                )
                currentBgColor = (
                    overrideBgColor
                    if overrideBgColor
                    else item.effectiveBgColor()
                )
            else:
                # Notes inherit from parent notes, Efforts/Attachments have no inheritance
                currentColor = (
                    overrideFgColor
                    if overrideFgColor
                    else item.foregroundColor(recursive=True)
                )
                currentBgColor = (
                    overrideBgColor
                    if overrideBgColor
                    else item.backgroundColor(recursive=True)
                )
        else:
            currentColor = overrideFgColor
            currentBgColor = overrideBgColor
        # Convert to wx.Colour using generic resolve helper (handles tuples and symbolic constants)
        currentColor = resolve_color(currentColor) if currentColor else None
        currentBgColor = (
            resolve_color(currentBgColor) if currentBgColor else None
        )
        self._fontEntry = entry.FontEntry(
            self, currentFont, currentColor, currentBgColor
        )
        self._fontSync = attributesync.AttributeSync(
            "font",
            self._fontEntry,
            currentFont,
            self.items,
            command.EditFontCommand,
            entry.EVT_FONTENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        self._fontColorSync = attributesync.FontColorSync(
            "foregroundColor",
            self._fontEntry,
            currentColor,
            self.items,
            command.EditForegroundColorCommand,
            entry.EVT_FONTENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        # self.addEntry(_("Font"), self._fontEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Font"), self._fontEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def addEffectiveSection(self):
        """Add read-only display of effective/final appearance values.

        Layout: 3 columns - Label, Control, Source
        - Tasks/Categories: have effectiveXxx() SSOT methods
        - Notes: effective = override or parent (recursive lookup)
        - Attachments: effective = override or System Theme
        """
        if len(self.items) != 1:
            return
        item = self.items[0]

        self.addLine()
        self.addSectionHeader(_("Effective values"), _("Source"))
        entryFlags = [
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Label
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Control
            wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,  # Source
        ]

        # Icon - panel with bitmap and "N/A" text (show one or the other)
        def rejectNav(evt):
            evt.GetEventObject().Navigate(evt.GetDirection())

        def rejectFocus(evt):
            forward = not wx.GetKeyState(wx.WXK_SHIFT)
            wx.CallAfter(evt.GetEventObject().Navigate, forward)

        self._effectiveIconPanel = wx.Panel(self, style=0)
        self._effectiveIconPanel.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._effectiveIconPanel.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        iconSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._effectiveIconDisplay = wx.StaticBitmap(self._effectiveIconPanel)
        self._effectiveIconDisplay.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._effectiveIconDisplay.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._effectiveIconName = wx.StaticText(
            self._effectiveIconPanel, label=""
        )
        self._effectiveIconName.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._effectiveIconName.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._effectiveIconNA = wx.StaticText(
            self._effectiveIconPanel, label=_("N/A")
        )
        self._effectiveIconNA.Bind(wx.EVT_NAVIGATION_KEY, rejectNav)
        self._effectiveIconNA.Bind(wx.EVT_SET_FOCUS, rejectFocus)
        self._effectiveIconNA.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        iconSizer.Add(self._effectiveIconDisplay, 0, wx.ALIGN_CENTER_VERTICAL)
        iconSizer.Add(
            self._effectiveIconName, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5
        )
        iconSizer.Add(self._effectiveIconNA, 0, wx.ALIGN_CENTER_VERTICAL)
        self._effectiveIconPanel.SetSizer(iconSizer)
        self._effectiveIconSource = wx.StaticText(self, label="")
        self._effectiveIconSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Icon"),
            self._effectiveIconPanel,
            self._effectiveIconSource,
            flags=entryFlags,
        )

        # Foreground - read-only color picker with source
        self._effectiveFgPicker = widgets.ColourPickerCtrl(
            self, colour=wx.BLACK, readOnly=True
        )
        self._effectiveFgSource = wx.StaticText(self, label="")
        self._effectiveFgSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Foreground"),
            self._effectiveFgPicker,
            self._effectiveFgSource,
            flags=entryFlags,
        )

        # Background - read-only color picker with source
        self._effectiveBgPicker = widgets.ColourPickerCtrl(
            self, colour=wx.WHITE, readOnly=True
        )
        self._effectiveBgSource = wx.StaticText(self, label="")
        self._effectiveBgSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Background"),
            self._effectiveBgPicker,
            self._effectiveBgSource,
            flags=entryFlags,
        )

        # Font - read-only font picker with source
        defaultFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self._effectiveFontPicker = widgets.FontPickerCtrl(
            self,
            font=defaultFont,
            colour=wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
            bgColour=wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
            readOnly=True,
        )
        self._effectiveFontSource = wx.StaticText(self, label="")
        self._effectiveFontSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )
        self.addEntry(
            _("Font"),
            self._effectiveFontPicker,
            self._effectiveFontSource,
            flags=entryFlags,
        )

        # Initial update
        self._updateEffectiveValues()

        # Subscribe to SSOT effective change events for automatic updates
        for eventType in (
            item.effectiveFgColorChangedEventType(),
            item.effectiveBgColorChangedEventType(),
            item.effectiveIconChangedEventType(),
            item.effectiveFontChangedEventType(),
        ):
            self.registerObserver(
                self._onEffectiveAppearanceChanged,
                eventType=eventType,
                eventSource=item,
            )

    def _onEffectiveAppearanceChanged(self, event):
        self._updateEffectiveValues()
        self._updateFontDemoColors()

    def _updateEffectiveValues(self):
        """Refresh the effective appearance display from item's effective fields.

        All domain objects (Task, Category, Note, Attachment) use the same SSOT
        accessor pattern: effectiveXxx(), effectiveXxxSource(), and effectiveXxxDefault()
        (except icon which has no default).
        """
        if len(self.items) != 1:
            return
        if not hasattr(self, "_effectiveIconDisplay"):
            return
        item = self.items[0]

        # --- Icon ---
        iconActual = item.effectiveIcon()
        iconSource = item.effectiveIconSource()
        # Icons have no system default - use empty string if no value
        iconValue = iconActual if iconActual else ""
        if iconValue:
            bitmap = wx.ArtProvider.GetBitmap(iconValue, wx.ART_MENU, (16, 16))
            self._effectiveIconDisplay.SetBitmap(bitmap)
            self._effectiveIconDisplay.Show()
            # Look up icon name from artprovider metadata
            iconData = artprovider.chooseableItems.get(iconValue, {})
            iconName = iconData.get("name", iconValue)
            self._effectiveIconName.SetLabel(iconName)
            self._effectiveIconName.Show()
            self._effectiveIconNA.Hide()
            self._effectiveIconSource.SetLabel(
                iconSource or _("Initializing...")
            )
        else:
            self._effectiveIconDisplay.Hide()
            self._effectiveIconName.Hide()
            self._effectiveIconNA.Show()
            self._effectiveIconSource.SetLabel(_("N/A"))
        self._effectiveIconPanel.Layout()

        # --- Foreground Color ---
        fgActual = item.effectiveFgColor()
        fgDefault = item.effectiveFgColorDefault()
        fgSource = item.effectiveFgColorSource()
        effectiveFgColour = resolve_color(fgActual if fgActual else fgDefault)
        self._effectiveFgPicker.SetColour(effectiveFgColour)
        self._effectiveFgSource.SetLabel(fgSource or _("Initializing..."))

        # --- Background Color ---
        bgActual = item.effectiveBgColor()
        bgDefault = item.effectiveBgColorDefault()
        bgSource = item.effectiveBgColorSource()
        effectiveBgColour = resolve_color(bgActual if bgActual else bgDefault)
        self._effectiveBgPicker.SetColour(effectiveBgColour)
        self._effectiveBgSource.SetLabel(bgSource or _("Initializing..."))

        # --- Font ---
        fontActual = item.effectiveFont()
        fontDefault = item.effectiveFontDefault()
        fontSource = item.effectiveFontSource()
        self._effectiveFontPicker.SetSelectedFont(
            resolve_font(fontActual if fontActual else fontDefault)
        )
        self._effectiveFontSource.SetLabel(fontSource or _("Initializing..."))

        # Update font picker demo colors
        self._effectiveFontPicker.SetSelectedColour(effectiveFgColour)
        self._effectiveFontPicker.SetSelectedBgColour(effectiveBgColour)

        # Update override entries to track effective values
        # (shown when override checkbox is unchecked; always for colors on font picker)
        effectiveFont = resolve_font(fontActual if fontActual else fontDefault)
        if hasattr(self, "_foregroundColorEntry"):
            self._foregroundColorEntry.setEffectiveColor(effectiveFgColour)
        if hasattr(self, "_backgroundColorEntry"):
            self._backgroundColorEntry.setEffectiveColor(effectiveBgColour)
        if hasattr(self, "_fontEntry"):
            self._fontEntry.setEffectiveFont(effectiveFont)

    def _updateFontDemoColors(self):
        if len(self.items) != 1:
            return
        item = self.items[0]
        self._fontEntry.SetColor(
            resolve_color(
                item.effectiveFgColor() or item.effectiveFgColorDefault()
            )
        )
        self._fontEntry.SetBgColor(
            resolve_color(
                item.effectiveBgColor() or item.effectiveBgColorDefault()
            )
        )

    def addIconEntry(self):
        # pylint: disable=W0201,E1101
        currentIcon = self.items[0].icon() if len(self.items) == 1 else ""
        self._iconEntry = entry.IconEntry(self, currentIcon)
        # TODO ? Recopier le debug logging for Priority categories
        self._iconSync = attributesync.AttributeSync(
            "icon",
            self._iconEntry,
            currentIcon,
            self.items,
            command.EditIconCommand,
            entry.EVT_ICONENTRY,
            self.items[0].appearanceChangedEventType(),
        )
        # self.addEntry(_("Icon"), self._iconEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Icon"), self._iconEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def entries(self):
        # return dict(firstEntry=self._foregroundColorEntry)  # pylint: disable=E1101
        if self._foregroundColorEntry:
            return dict(firstEntry=self._foregroundColorEntry)
        return dict()

    def close(self):
        super().close()


class DatesPage(Page):
    """
    Page d'édition des dates d'une tâche.

    Cette page permet de définir les dates importantes pour une tâche, comme la date de début,
    la date d'échéance, ou d'autres dates spécifiques.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition des dates.
    """

    pageName = "dates"
    pageTitle = _("Dates")
    pageIcon = "calendar_icon"
    columns = 3  # label, datetime row, rest

    def __init__(
        self, theTask, parent, settings, items_are_new, *args, **kwargs
    ):
        self._actualStartDateTimeEntry = None
        self._completionDateTimeEntry = None
        self._dueDateTimeEntry = None
        self._plannedStartDateTimeEntry = None
        self._recurrenceEntry = None
        self._recurrenceSync = None
        self._reminderDateTimeEntry = None
        self._reminderDateTimeSync = None
        self.__settings = settings
        self._duration = None
        self.__items_are_new = items_are_new
        super().__init__(theTask, parent, *args, **kwargs)
        pub.subscribe(
            self.__onChoicesConfigChanged, "settings.feature.sdtcspans"
        )
        # Ajouter les champs d'entrée :
        self.addEntries()

    def close(self):
        if len(self.items) == 1 and hasattr(self, "_statusLabel"):
            try:
                pub.unsubscribe(
                    self._onStatusMayHaveChanged,
                    self.items[0].statusChangedEventType(),
                )
            except Exception:
                pass
        if len(self.items) == 1:
            try:
                pub.unsubscribe(
                    self._onDomainPlannedDurationModeChanged,
                    self.items[0].plannedDurationModeChangedEventType(),
                )
            except Exception:
                pass
            try:
                pub.unsubscribe(
                    self.__onTaskDurationDomainChanged,
                    self.items[0].plannedDurationChangedEventType(),
                )
            except Exception:
                pass
        super().close()

    def __onChoicesConfigChanged(self, value=""):
        self._dueDateTimeEntry.LoadChoices(value)

    def __onTimeChoicesChange(self, event):
        self.__settings.settext("feature", "sdtcspans", event.GetValue())

    def __onPlannedStartChanged(self, value):
        """AttributeSync callback for planned start date changes."""
        self._currentPlannedStartDateTime = value
        self.__onPlannedStartDateTimeChanged(value)

    def __onPlannedStartDateTimeChanged(self, value):
        """Called when planned start date changes - update based on mode."""
        # if hasattr(self, '_currentPlannedDurationMode'):
        #     self.__syncTaskState(sourceField='start')
        self._dueDateTimeEntry.SetRelativeChoicesStart(
            None if value == date.DateTime() else value
        )

    def __onDueDateChanged(self, value):
        """AttributeSync callback for due date changes."""
        self._currentDueDateTime = value
        self.__onDueDateTimeChanged(value)

    def __onDueDateTimeChanged(self, value):
        """Called when due date changes - update based on mode."""
        if hasattr(self, "_currentPlannedDurationMode"):
            self.__syncTaskState(sourceField="due")

    def _onDomainPlannedDurationModeChanged(self, newValue, sender):
        """Layer 2: Domain plannedDurationMode changed externally."""
        if sender not in self.items:
            return
        self._currentPlannedDurationMode = newValue
        self.__updateDurationModeDropdown()
        self.__syncTaskState()

    def __onPlannedDurationSyncCallback(self, value):
        """AttributeSync callback: duration committed or changed externally."""
        self.__syncTaskState(sourceField="duration")

    def __onTaskDurationDomainChanged(self, newValue, sender):
        """Domain duration changed — update preset dropdown to match."""
        if sender in self.items:
            self.__updatePresetSelection()

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer les dates associées à la tâche.
        """
        self.addStatusEntry()
        self.addLine()
        self.addDateEntries()
        self.addLine()
        self.addReminderEntry()
        self.addLine()
        self.addRecurrenceEntry()

    def addStatusEntry(self):
        """Add a read-only status display showing icon, color, and status text."""
        if len(self.items) != 1:
            return  # Only show for single task editing

        # Create panel that doesn't accept keyboard focus (skipped in tab order)
        class NoFocusPanel(wx.Panel):
            def AcceptsFocusFromKeyboard(self):
                return False

        self._statusPanel = NoFocusPanel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._statusIcon = wx.StaticBitmap(self._statusPanel)
        sizer.Add(self._statusIcon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self._statusLabel = wx.StaticText(self._statusPanel, label="")
        sizer.Add(self._statusLabel, 0, wx.ALIGN_CENTER_VERTICAL)

        self._statusPanel.SetSizer(sizer)

        # Source explanation (gray text)
        self._statusSource = wx.StaticText(self, label="")
        self._statusSource.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
        )

        # 3 controls: label + panel + source
        self.addEntry(
            _("Status"),
            self._statusPanel,
            self._statusSource,
            flags=[
                None,
                wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
                wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
            ],
        )

        # Initial display
        self._updateStatusDisplay()

        # Subscribe to status change event (fired by computeStoredStatus when status changes)
        pub.subscribe(
            self._onStatusMayHaveChanged,
            self.items[0].statusChangedEventType(),
        )

    def _onStatusMayHaveChanged(self, newValue, sender):
        if sender == self.items[0] or sender is None:
            self._updateStatusDisplay()

    def _updateStatusDisplay(self):
        if not hasattr(self, "_statusLabel"):
            return
        theTask = self.items[0]
        # Use centralized computedStatus(explain=True) for status and source
        taskStatus, statusSource = theTask.computedStatus(explain=True)

        # Update icon
        icon_name = taskStatus.getBitmap(self.__settings)
        bitmap = wx.ArtProvider.GetBitmap(icon_name, wx.ART_MENU, (16, 16))
        if bitmap.IsOk():
            self._statusIcon.SetBitmap(bitmap)

        # Update text and foreground color only (no background painting)
        statusText = (
            taskStatus.pluralLabel.replace(" tasks", "")
            .replace("tasks", "")
            .strip()
        )
        self._statusLabel.SetLabel(statusText)
        self._statusLabel.SetForegroundColour(theTask.statusFgColor())

        # Update source explanation
        if hasattr(self, "_statusSource"):
            self._statusSource.SetLabel(statusSource or _("Initializing..."))
            self._statusSource.InvalidateBestSize()

        # Relayout panel and parent to accommodate new text sizes
        self._statusLabel.InvalidateBestSize()
        self._statusPanel.Layout()
        self._statusPanel.Fit()
        self.Layout()

    def addDateEntries(self):  # TODO ? Recopier la nouvelle version !
        self.addDateEntry(_("Planned start date"), "plannedStartDateTime")
        self.addDateEntry(_("Due date"), "dueDateTime")
        # # Create panel for planned date section with table layout
        # self._addPlannedDateSection()
        self.addLine()
        self.addDateEntry(_("Actual start date"), "actualStartDateTime")
        self.addDateEntry(_("Completion date"), "completionDateTime")
        # self._addActualStartDateEntry()
        # self._addCompletionDateEntry()

        start = self._plannedStartDateTimeEntry.GetValue()
        self._dueDateTimeEntry.SetRelativeChoicesStart(
            start=None if start == date.DateTime() else start
        )
        self._dueDateTimeEntry.LoadChoices(
            self.__settings.get("feature", "sdtcspans")
        )
        # sdtc.EVT_TIME_CHOICES_CHANGE(self._dueDateTimeEntry, self.__onTimeChoicesChange)
        self._dueDateTimeEntry.Bind(
            sdtc.EVT_TIME_CHOICES_CHANGE, self.__onTimeChoicesChange
        )

    def addDateEntry(self, label, taskMethodName):
        # def add_date_entry(self, label: str, task_method_name: str) -> None:
        """Ajoute une entrée de date à la page.

        Args :
            label : L'étiquette de l'entrée de date.
            taskMethodName : Le nom de la méthode utilisée pour obtenir la date de la tâche.
        """
        TaskMethodName = taskMethodName[0].capitalize() + taskMethodName[1:]
        dateTime = (
            getattr(self.items[0], taskMethodName)()
            if len(self.items) == 1
            else date.DateTime()
        )
        setattr(self, "_current%s" % TaskMethodName, dateTime)
        suggestedDateTimeMethodName = "suggested" + TaskMethodName
        suggestedDateTime = getattr(
            self.items[0], suggestedDateTimeMethodName
        )()
        dateTimeEntry = entry.DateTimeEntry(
            self,
            self.__settings,
            dateTime,
            suggestedDateTime=suggestedDateTime,
            showRelative=taskMethodName == "dueDateTime",
            adjustEndOfDay=taskMethodName == "dueDateTime",
        )
        setattr(self, "_%sEntry" % taskMethodName, dateTimeEntry)
        commandClass = getattr(command, "Edit%sCommand" % TaskMethodName)
        eventType = getattr(
            self.items[0], "%sChangedEventType" % taskMethodName
        )()
        keep_delta = self.__keep_delta(taskMethodName)
        datetimeSync = attributesync.AttributeSync(
            taskMethodName,
            dateTimeEntry,
            dateTime,
            self.items,
            commandClass,
            entry.EVT_DATETIMEENTRY,
            eventType,
            keep_delta=keep_delta,
            callback=(
                self.__onPlannedStartDateTimeChanged
                if taskMethodName == "plannedStartDateTime"
                else None
            ),
        )
        setattr(self, "_%sSync" % taskMethodName, datetimeSync)
        self.addEntry(label, dateTimeEntry, flags=[wx.ALIGN_RIGHT, wx.EXPAND])

    def __keep_delta(self, taskMethodName):
        datesTied = self.__settings.get("view", "datestied")
        return (
            datesTied == "startdue"
            and taskMethodName == "plannedStartDateTime"
        ) or (datesTied == "duestart" and taskMethodName == "dueDateTime")

    def addReminderEntry(self):
        # pylint: disable=W0201
        reminderDateTime = (
            self.items[0].reminder()
            if len(self.items) == 1
            else date.DateTime()
        )
        suggestedDateTime = self.items[0].suggestedReminderDateTime()
        self._reminderDateTimeEntry = entry.DateTimeEntry(
            self,
            self.__settings,
            reminderDateTime,
            suggestedDateTime=suggestedDateTime,
        )
        self._reminderDateTimeSync = attributesync.AttributeSync(
            "reminder",
            self._reminderDateTimeEntry,
            reminderDateTime,
            self.items,
            command.EditReminderDateTimeCommand,
            entry.EVT_DATETIMEENTRY,
            self.items[0].reminderChangedEventType(),
        )
        self.addEntry(
            _("Reminder"),
            self._reminderDateTimeEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def addRecurrenceEntry(self):
        # pylint: disable=W0201
        currentRecurrence = (
            self.items[0].recurrence()
            if len(self.items) == 1
            else date.Recurrence()
        )
        self._recurrenceEntry = entry.RecurrenceEntry(
            self, currentRecurrence, self.__settings
        )
        self._recurrenceSync = attributesync.AttributeSync(
            "recurrence",
            self._recurrenceEntry,
            currentRecurrence,
            self.items,
            command.EditRecurrenceCommand,
            entry.EVT_RECURRENCEENTRY,
            self.items[0].recurrenceChangedEventType(),
        )
        self.addEntry(
            _("Recurrence"),
            self._recurrenceEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def entries(self):
        # pylint: disable=E1101
        # For DateTimeComboCtrl controls, return the date control as the focusable widget
        return dict(
            firstEntry=self._plannedStartDateTimeEntry,
            plannedStartDateTime=self._plannedStartDateTimeEntry,
            dueDateTime=self._dueDateTimeEntry,
            actualStartDateTime=self._actualStartDateTimeEntry,
            completionDateTime=self._completionDateTimeEntry,
            timeLeft=self._dueDateTimeEntry,
            reminder=self._reminderDateTimeEntry,
            recurrence=self._recurrenceEntry,
        )

    def close(self):
        """Clean up resources when dialog closes."""
        # Unsubscribe from pubsub topics
        try:
            pub.unsubscribe(
                self.__onPresetsConfigChanged,
                "settings.feature.task_duration_presets",
            )
        except Exception:
            pass
        super().close()


class ProgressPage(Page):
    """
    Page d'édition de la progression d'une tâche.

    Cette page permet à l'utilisateur de suivre et modifier l'avancement d'une tâche.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition de la progression.
    """

    pageName = "progress"
    pageTitle = _("Progress")
    pageIcon = "progress"

    # j'ai ajouté __init_
    def __init__(self, items, *args, **kwargs):
        super().__init__(items, *args, **kwargs)
        self._percentageCompleteEntry = None
        self._percentageCompleteSync = None
        self._shouldMarkCompletedEntry = None
        self._shouldMarkCompletedSync = None
        # # Ajouter les champs d'entrée :
        self.addEntries()

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer les informations de progression.
        """
        self.addProgressEntry()
        self.addBehaviorEntry()

    def addProgressEntry(self):
        # pylint: disable=W0201
        currentPercentageComplete = (
            self.items[0].percentageComplete()
            if len(self.items) == 1
            else self.averagePercentageComplete(self.items)
        )
        self._percentageCompleteEntry = entry.PercentageEntry(
            self, currentPercentageComplete
        )
        self._percentageCompleteSync = attributesync.AttributeSync(
            "percentageComplete",
            self._percentageCompleteEntry,
            currentPercentageComplete,
            self.items,
            command.EditPercentageCompleteCommand,
            entry.EVT_PERCENTAGEENTRY,
            self.items[0].percentageCompleteChangedEventType(),
        )
        self.addEntry(
            _("Percentage complete"),
            self._percentageCompleteEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    @staticmethod
    def averagePercentageComplete(items):
        return (
            sum([item.percentageComplete() for item in items])
            // float(len(items))  # with // ? yes
            if items
            else 0
        )

    def addBehaviorEntry(self):
        # pylint: disable=W0201
        choices = [
            (None, _("Use application-wide setting")),
            (False, _("No")),
            (True, _("Yes")),
        ]
        currentChoice = (
            self.items[0].shouldMarkCompletedWhenAllChildrenCompleted()
            if len(self.items) == 1
            else None
        )
        self._shouldMarkCompletedEntry = entry.ChoiceEntry(
            self, choices, currentChoice
        )
        self._shouldMarkCompletedSync = attributesync.AttributeSync(
            "shouldMarkCompletedWhenAllChildrenCompleted",
            self._shouldMarkCompletedEntry,
            currentChoice,
            self.items,
            command.EditShouldMarkCompletedCommand,
            entry.EVT_CHOICEENTRY,
            task.Task.shouldMarkCompletedWhenAllChildrenCompletedChangedEventType(),
        )
        self.addEntry(
            _("Mark task completed when all children are completed?"),
            self._shouldMarkCompletedEntry,
            flags=[wx.ALIGN_RIGHT, wx.EXPAND],
        )

    def entries(self):
        return dict(
            firstEntry=self._percentageCompleteEntry,
            percentageComplete=self._percentageCompleteEntry,
        )


class BudgetPage(Page):
    """
    Page d'édition du budget d'une tâche.

    Cette page permet de gérer le budget alloué à une tâche, y compris les coûts prévus
    et les dépenses réelles.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition du budget.
    """

    pageName = "budget"
    pageTitle = _("Budget")
    pageIcon = "calculator_icon"

    # j'ai ajouté __init__
    def __init__(self, items, *args, **kwargs):
        super().__init__(items, *args, **kwargs)
        self._budgetEntry = None
        self._budgetLeftEntry = None
        self._budgetSync = None
        self._fixedFeeEntry = None
        self._fixedFeeSync = None
        self._hourlyFeeEntry = None
        self._hourlyFeeSync = None
        self._revenueEntry = None
        self._timeSpentEntry = None
        # # Ajouter les champs d'entrée pour éditer le budget de la tâche :
        self.addEntries()  # Ne doit être appelé qu'une seule fois par page.

    def NavigateBook(self, forward):
        self.GetParent().NavigateBook(forward)

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour éditer le budget de la tâche.
        """
        self.addBudgetEntries()
        self.addLine()
        self.addRevenueEntries()
        self.observeTracking()

    def addBudgetEntries(self):
        self.addBudgetEntry()
        if len(self.items) == 1:
            self.addTimeSpentEntry()
            self.addBudgetLeftEntry()

    def addBudgetEntry(self):
        # pylint: disable=W0201,W0212
        currentBudget = (
            self.items[0].budget()
            if len(self.items) == 1
            else date.TimeDelta()
        )
        self._budgetEntry = entry.TimeDeltaEntry(self, currentBudget)
        self._budgetSync = attributesync.AttributeSync(
            "budget",
            self._budgetEntry,
            currentBudget,
            self.items,
            command.EditBudgetCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].budgetChangedEventType(),
        )
        # self.addEntry(_("Budget"), self._budgetEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Budget"), self._budgetEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def addTimeSpentEntry(self):
        assert len(self.items) == 1
        # pylint: disable=W0201
        self._timeSpentEntry = entry.TimeDeltaEntry(
            self, self.items[0].timeSpent(), readonly=True
        )
        # self.addEntry(_("Time spent"), self._timeSpentEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Time spent"),
            self._timeSpentEntry,
            flags=[wx.ALIGN_RIGHT, wx.ALL],
        )
        pub.subscribe(
            self.onTimeSpentChanged, self.items[0].timeSpentChangedEventType()
        )

    def onTimeSpentChanged(self, newValue, sender):
        if sender == self.items[0]:
            time_spent = sender.timeSpent()
            if time_spent != self._timeSpentEntry.GetValue():
                self._timeSpentEntry.SetValue(time_spent)

    def addBudgetLeftEntry(self):
        assert len(self.items) == 1
        # pylint: disable=W0201
        self._budgetLeftEntry = entry.TimeDeltaEntry(
            self, self.items[0].budgetLeft(), readonly=True
        )
        # self.addEntry(_("Budget left"), self._budgetLeftEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Budget left"),
            self._budgetLeftEntry,
            flags=[wx.ALIGN_RIGHT, wx.ALL],
        )
        pub.subscribe(
            self.onBudgetLeftChanged,
            self.items[0].budgetLeftChangedEventType(),
        )

    def onBudgetLeftChanged(self, newValue, sender):  # pylint: disable=W0613
        if sender == self.items[0]:
            budget_left = sender.budgetLeft()
            if budget_left != self._budgetLeftEntry.GetValue():
                self._budgetLeftEntry.SetValue(budget_left)

    def addRevenueEntries(self):
        self.addHourlyFeeEntry()
        self.addFixedFeeEntry()
        if len(self.items) == 1:
            self.addRevenueEntry()

    def addHourlyFeeEntry(self):
        # pylint: disable=W0201,W0212
        currentHourlyFee = (
            self.items[0].hourlyFee() if len(self.items) == 1 else 0
        )
        self._hourlyFeeEntry = entry.AmountEntry(self, currentHourlyFee)
        self._hourlyFeeSync = attributesync.AttributeSync(
            "hourlyFee",
            self._hourlyFeeEntry,
            currentHourlyFee,
            self.items,
            command.EditHourlyFeeCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].hourlyFeeChangedEventType(),
        )
        # self.addEntry(_("Hourly fee"), self._hourlyFeeEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Hourly fee"),
            self._hourlyFeeEntry,
            flags=[wx.ALIGN_RIGHT, wx.ALL],
        )

    def addFixedFeeEntry(self):
        # pylint: disable=W0201,W0212
        currentFixedFee = (
            self.items[0].fixedFee() if len(self.items) == 1 else 0
        )
        self._fixedFeeEntry = entry.AmountEntry(self, currentFixedFee)
        self._fixedFeeSync = attributesync.AttributeSync(
            "fixedFee",
            self._fixedFeeEntry,
            currentFixedFee,
            self.items,
            command.EditFixedFeeCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].fixedFeeChangedEventType(),
        )
        # self.addEntry(_("Fixed fee"), self._fixedFeeEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Fixed fee"), self._fixedFeeEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )

    def addRevenueEntry(self):
        assert len(self.items) == 1
        revenue = self.items[0].revenue()
        self._revenueEntry = entry.AmountEntry(
            self, revenue, readonly=True
        )  # pylint: disable=W0201
        # Instance attribute _revenueEntry defined outside __init__
        # self.addEntry(_("Revenue"), self._revenueEntry, flags=[None, wx.ALL])
        self.addEntry(
            _("Revenue"), self._revenueEntry, flags=[wx.ALIGN_RIGHT, wx.ALL]
        )
        pub.subscribe(
            self.onRevenueChanged, self.items[0].revenueChangedEventType()
        )

    def onRevenueChanged(self, newValue, sender):
        if sender == self.items[0]:
            if newValue != self._revenueEntry.GetValue():
                self._revenueEntry.SetValue(newValue)

    def observeTracking(self):
        if len(self.items) != 1:
            return
        item = self.items[0]
        pub.subscribe(self.onTrackingChanged, item.trackingChangedEventType())
        if item.isBeingTracked():
            self.onTrackingChanged(True, item)

    def onTrackingChanged(self, newValue, sender):
        if newValue:
            if sender in self.items:
                date.Scheduler().schedule_interval(
                    self.onEverySecond, seconds=1
                )
        else:
            # We might need to keep tracking the clock if the user was tracking this
            # task with multiple effort records simultaneously
            if not self.items[0].isBeingTracked():
                date.Scheduler().unschedule(self.onEverySecond)

    def onEverySecond(self):
        taskDisplayed = self.items[0]
        self.onTimeSpentChanged(taskDisplayed.timeSpent(), taskDisplayed)
        self.onBudgetLeftChanged(taskDisplayed.budgetLeft(), taskDisplayed)
        self.onRevenueChanged(taskDisplayed.revenue(), taskDisplayed)

    def close(self):
        date.Scheduler().unschedule(self.onEverySecond)
        super().close()

    def entries(self):
        return dict(
            firstEntry=self._budgetEntry,
            budget=self._budgetEntry,
            budgetLeft=self._budgetEntry,
            hourlyFee=self._hourlyFeeEntry,
            fixedFee=self._fixedFeeEntry,
            revenue=self._hourlyFeeEntry,
        )


class PageWithViewer(Page):
    columns = 1

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
        self.__taskFile = taskFile
        self.__settings = settings
        self.__settingsSection = settingsSection
        self.viewer = None  # Permet l'affichage de la page !
        # self.addEntries()  # Non pas maintenant !
        # Laisser les classes enfants (comme EffortPage, NotesPage, etc.) l'appeler à la fin.
        # self.viewer = self.createViewer(
        #     self.__taskFile, self.__settings, self.__settingsSection
        # )  # Trop tôt aussi !
        super().__init__(items, parent, *args, **kwargs)
        # self.addEntries()  # ? self.addEntries() ne doit être appelé qu'une seule fois par page.
        # Prérequisites, Categories le lancent avec selected

    def addEntries(self):
        # pylint: disable=W0201
        """
        Ajoute les champs d'entrée pour l'édition de 4 pages
        (Catégories, Effort, Notes et Prérequis) consacré à une tâche.
        """
        if not hasattr(self, "items"):
            log.warning(
                "addEntries appelé trop tôt, items pas encore initialisé."
            )
            return
        self.viewer = self.createViewer(
            self.__taskFile, self.__settings, self.__settingsSection
        )
        # self.addEntry(self.viewer, growable=True)
        self.addEntry(self.viewer, growable=True, flags=[wx.EXPAND])

    def entries(self):
        return {"firstEntry": self.viewer}

    def createViewer(self, taskFile, settings, settingsSection):
        raise NotImplementedError

    def close(self):
        # I guess this happens because of CallAfter in context of #1437...
        # Clean up the viewer immediately now that the SearchCtrl timer
        # cleanup is properly implemented (see PYTHON3_MIGRATION_NOTES.md)
        if hasattr(self, "viewer"):
            self.viewer.detach()
            # Don't Notify the viewer about any changes anymore, it's about
            # to be deleted, but don't delete it too soon.
            wx.CallAfter(self.deleteViewer)
        super().close()

    def deleteViewer(self):
        if hasattr(self, "viewer"):
            del self.viewer


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
        return EffortViewer(
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

    # -> Voir EffortEditBook
    # # def addEntries(self):
    # #     """
    # #     Ajoute les champs d'entrée pour l'édition de l'effort consacré à une tâche.
    # #     """
    # #     pass
    # def addEntries(self):
    #     # ... code pour ajouter les sélecteurs de date ...
    #     self._startDateTimeEntry = widgets.DateTimeCtrl(...)
    #     # Il est crucial que l'objet "parent" (EditBook) puisse y accéder
    #     # ou que la page les expose.


class LocalCategoryViewer(BaseCategoryViewer):  # pylint: disable=W0223
    # AttributeError: partially initialized module 'taskcoachlib.gui.viewer' has no attribute 'BaseCategoryViewer'
    # (most likely due to a circular import)
    def __init__(self, items, *args, **kwargs):
        self.__items = items
        # Track original category state for each item to support tri-state "no change"
        self.__originalCategories = {
            item: set(item.categories()) for item in items
        }
        super().__init__(*args, **kwargs)
        for item in self.domainObjectsToView():
            item.expand(context=self.settingsSection(), notify=False)

    def getIsItemChecked(self, category):  # pylint: disable=W0621
        # for item in self.__items:
        #     if category in item.categories():
        #         return True
        # return False
        items_with_category = sum(
            1 for item in self.__items if category in item.categories()
        )
        if items_with_category == 0:
            return False  # No items have category
        elif items_with_category == len(self.__items):
            return True  # All items have category
        else:
            return None  # Mixed state

    def onCheck(self, event, final):
        """Ici, nous gardons une trace des éléments cochés par l'utilisateur afin que ces éléments
        restent cochés lors de l'actualisation de la visionneuse.
        """
        if final:
            category = self.widget.GetItemPyData(
                event.GetItem()
            )  # TODO: try GetItemData
            command.ToggleCategoryCommand(
                None, self.__items, category=category
            ).do()

    def checkAllCategories(self):
        """Assign all categories to the items being edited."""
        log.debug(f"Checking all categories for items: {self.__items}")
        for cat in self.presentation():
            for item in self.__items:
                if cat not in item.categories():
                    item.addCategory(cat)
        self.widget.refreshAllCheckStates()

    def uncheckAllCategories(self):
        """Remove all categories from the items being edited."""
        log.debug(f"Unchecking all categories for items: {self.__items}")
        for cat in self.presentation():
            for item in self.__items:
                if cat in item.categories():
                    item.removeCategory(cat)
        self.widget.refreshAllCheckStates()

    def createActionToolBarUICommands(self):
        """UI commands for check/uncheck all in the edit task categories tab."""
        return (
            uicommand.CategoryCheckAll(viewer=self),
            uicommand.CategoryUncheckAll(viewer=self),
        )

    def createCategoryPopupMenu(self, localOnly=True):  # pylint: disable=W0221
        # def createCategoryPopupMenu(self):  # pylint: disable=W0221
        # Signature of method 'LocalCategoryViewer.createCategoryPopupMenu()'
        # does not match signature of the base method in class 'BaseCategoryViewer'
        return super().createCategoryPopupMenu(True)


class CategoriesPage(PageWithViewer):
    """
    Page d'édition des catégories d'un objet.

    Permet d'assigner des catégories à un objet comme une tâche ou une note.
    Cette classe permet d'assigner des catégories à un objet comme une tâche ou une note. Elle hérite de la classe `PageWithViewer` qui gère l'affichage d'un visualiseur de contenu.

    Attributs :
        __realized (bool) : Indique si les champs d'édition ont été ajoutés (évite les doublons d'ajout).

    Méthodes :
        __init__(self, *args, **kwargs):
            Initialise la page d'édition des catégories.

        addEntries (self) :
            Ajoute les champs d'entrée pour l'édition des catégories.

        selected (self) :
            Gère la sélection de la page et ajoute les champs d'édition seulement lors du premier affichage.

        createViewer (self, taskFile, settings, settingsSection) :
            Crée le visualiseur de catégories associé à l'objet.

        onCategoryChanged (self, event) :
            Rafraîchit les éléments affichés dans le visualiseur de catégories en fonction des modifications.

        entries (self) :
            Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur de catégories (si affiché).
    """

    # Constantes :
    # Nom interne de la page ("categories") :
    pageName = "categories"
    # Titre affiché à l'utilisateur ("Catégories") :
    pageTitle = _("Categories")
    # Nom de l'icône associée à la page ("folder_blue_arrow_icon") :
    pageIcon = "folder_blue_arrow_icon"

    def __init__(self, *args, **kwargs):
        """Initialise la page d'édition des catégories."""
        # Indique si les champs d'édition ont été ajoutés (évite les doublons d'ajout) :
        self.__realized = False
        super().__init__(*args, **kwargs)

    def addEntries(self):
        """
        Ajoute les champs d'entrée pour gérer les catégories associées à l'objet.
        """
        pass

    def selected(self):
        if not self.__realized:
            self.__realized = True
            super().addEntries()
            self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée le visualiseur de catégories associé à l'objet."""
        assert len(self.items) == 1
        # for item in self.items:  # TODO : à essayer.
        item = self.items[0]
        for eventType in (
            item.categoryAddedEventType(),
            item.categoryRemovedEventType(),
        ):
            self.registerObserver(
                self.onCategoryChanged, eventType=eventType, eventSource=item
            )
        return LocalCategoryViewer(
            self.items,
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
        )

    def onCategoryChanged(self, event):
        """Rafraîchit les éléments affichés dans le visualiseur de catégories en fonction des modifications."""
        self.viewer.refreshItems(*list(event.values()))

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page,
        y compris le visualiseur de catégories (si affiché)."""
        # Always include "categories" key so setFocus() can find this page
        # before it's realized. The actual viewer is used if available.
        if self.__realized and hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, categories=self.viewer)
        # return dict()
        return dict(firstEntry=self, categories=self)


class LocalAttachmentViewer(AttachmentViewer):  # pylint: disable=W0223
    # class LocalAttachmentViewer(viewer.AttachmentViewer):  # pylint: disable=W0223
    """
    Classe de visualiseur d'attachements locaux.

    Cette classe hérite de la classe `AttachmentViewer` et est spécialisée pour gérer les pièces jointes locales.

    Attributs :
        attachmentOwner : L'objet propriétaire des pièces jointes (par exemple, une tâche).

    Méthodes :
        newItemCommand (self, *args, **kwargs) :
            Crée une commande pour ajouter une nouvelle pièce jointe à l'objet propriétaire.

        deleteItemCommand (self) :
            Crée une commande pour supprimer les pièces jointes sélectionnées.

        cutItemCommand (self) :
            Crée une commande pour couper les pièces jointes sélectionnées.

    Note :
        La classe LocalAttachmentViewer hérite de la classe AttachmentViewer,
        qui est une classe de base définie taskcoachlib.gui.viewer.attachment,
        et LocalAttachmentViewer en hérite pour bénéficier de certaines fonctionnalités communes.

        La classe AttachmentViewer gère l'affichage, le tri, la recherche,
        et l'interaction avec les pièces jointes associées aux tâches.
        Elle permet également la gestion des colonnes et des menus contextuels pour les pièces jointes.

        Les méthodes newItemCommand, deleteItemCommand et cutItemCommand
        sont spécifiques aux opérations sur les pièces jointes locales
        et sont redéfinies dans cette classe.
    """

    # AttributeError: partially initialized module 'taskcoachlib.gui.viewer'
    # has no attribute 'AttachmentViewer' (most likely due to a circular import)
    def __init__(self, *args, **kwargs):
        # L'objet propriétaire des pièces jointes (par exemple, une tâche) :
        self.attachmentOwner = kwargs.pop("owner")
        attachments = attachment.AttachmentList(
            self.attachmentOwner.attachments()
        )
        super().__init__(attachmentsToShow=attachments, *args, **kwargs)

    def newItemCommand(self, *args, **kwargs):
        """Crée une commande pour ajouter une nouvelle pièce jointe à l'objet propriétaire."""
        return command.AddAttachmentCommand(
            None, [self.attachmentOwner], *args, **kwargs
        )

    def deleteItemCommand(self):
        """Crée une commande pour supprimer les pièces jointes sélectionnées."""
        return command.RemoveAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )

    def cutItemCommand(self):
        """Crée une commande pour couper les pièces jointes sélectionnées."""
        return command.CutAttachmentCommand(
            None, [self.attachmentOwner], attachments=self.curselection()
        )

    def pasteItemCommand(self):
        """Paste attachments from clipboard to this task's attachments."""
        from taskcoachlib.command.clipboard import Clipboard

        items, source = Clipboard().get()
        copies = [item.copy() for item in items]
        return command.AddAttachmentCommand(
            None, [self.attachmentOwner], attachments=copies
        )


class AttachmentsPage(PageWithViewer):
    """
    Page d'édition des pièces jointes d'un objet.

    Cette classe hérite de `PageWithViewer` et gère l'affichage et l'édition des pièces jointes associées à un objet.

    Attributs :
        pageName (str) : Nom interne de la page ("attachments").
        pageTitle (str) : Titre affiché à l'utilisateur ("Attachments").
        pageIcon (str) : Nom de l'icône associée à la page ("paperclip_icon").

    Méthodes :
        createViewer (self, taskFile, settings, settingsSection) :
            Crée un visualiseur d'attachements local pour l'objet.

        onAttachmentsChanged (self, event) :
            Rafraîchit le visualiseur d'attachements lorsque la liste des pièces jointes change.

        entries (self) :
            Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur d'attachements.
    """

    # Attributs :
    # Nom interne de la page ("attachments") :
    pageName = "attachments"
    # Titre affiché à l'utilisateur ("Attachments") :
    pageTitle = _("Attachments")
    # Nom de l'icône associée à la page ("paperclip_icon") :
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
        super().__init__(
            items, parent, taskFile, settings, settingsSection, *args, **kwargs
        )
        self.addEntries()

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée un visualiseur d'attachements local pour l'objet.

        Cette méthode crée un LocalAttachmentViewer pour afficher
        et gérer les pièces jointes de l'objet.
        Elle s'assure également d'observer les changements
        dans la liste des pièces jointes afin de mettre à jour le visualiseur.
        """
        assert len(self.items) == 1
        item = self.items[0]
        self.registerObserver(
            self.onAttachmentsChanged,
            eventType=item.attachmentsChangedEventType(),
            eventSource=item,
        )
        return LocalAttachmentViewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,
        )

    def onAttachmentsChanged(self, event):  # pylint: disable=W0613
        """Rafraîchit le visualiseur d'attachements lorsque la liste des pièces jointes change.

        Cette méthode est appelée lorsque la liste des pièces jointes change.
        Elle met à jour le visualiseur pour refléter les modifications."""
        self.viewer.domainObjectsToView().clear()
        self.viewer.domainObjectsToView().extend(self.items[0].attachments())

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page,
        y compris le visualiseur d'attachements.

        Cette méthode renvoie un dictionnaire contenant les éléments d'entrée de la page,
        y compris le visualiseur d'attachements,
        qui sera utilisé pour l'affichage dans la boîte de dialogue d'édition.
        """
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, attachments=self.viewer)
        return dict()


class LocalNoteViewer(BaseNoteViewer):  # pylint: disable=W0223
    # class LocalNoteViewer(viewer.BaseNoteViewer):  # pylint: disable=W0223
    """
    Classe de visualiseur de notes locales.

    Cette classe hérite de la classe `BaseNoteViewer` et est spécialisée pour gérer les notes locales.

    Attributs :
        __note_owner : L'objet propriétaire des notes (par exemple, une tâche).

    Méthodes :
        newItemCommand (self, *args, **kwargs) :
            Crée une commande pour ajouter une nouvelle note à l'objet propriétaire.

        newSubItemCommand (self) :
            Crée une commande pour ajouter une note enfant à la note sélectionnée.

        deleteItemCommand (self) :
            Crée une commande pour supprimer les notes sélectionnées.

    Explication :

    Héritage : La classe LocalNoteViewer hérite de la classe BaseNoteViewer,
    qui fournit probablement des fonctionnalités communes pour l'affichage et la modification des notes.

    Propriété des notes : L'attribut __note_owner stocke une référence
    à l'objet propriétaire des notes.
    Cela permet au visualiseur de gérer correctement la création,
    la suppression et la modification de notes.

    Création de commandes : Les méthodes newItemCommand, newSubItemCommand et deleteItemCommand
    créent des objets de commande spécifiques pour gérer respectivement la création,
    la suppression et la création de sous-notes.
    Ces commandes sont probablement utilisées pour exécuter les actions correspondantes au sein de l'application.
    """

    # from taskcoachlib.gui.viewer
    def __init__(self, *args, **kwargs):
        # L'objet propriétaire des notes (par exemple, une tâche) :
        self.__note_owner = kwargs.pop("owner")
        notes = note.NoteContainer(self.__note_owner.notes())
        super().__init__(notesToShow=notes, *args, **kwargs)

    def newItemCommand(self, *args, **kwargs):
        """Crée une commande pour ajouter une nouvelle note à l'objet propriétaire."""
        return command.AddNoteCommand(None, [self.__note_owner])

    def newSubItemCommand(self):
        """Crée une commande pour ajouter une note enfant à la note sélectionnée."""
        return command.AddSubNoteCommand(
            None, self.curselection(), owner=self.__note_owner
        )

    def deleteItemCommand(self):
        """Crée une commande pour supprimer les notes sélectionnées."""
        return command.RemoveNoteCommand(
            None, [self.__note_owner], notes=self.curselection()
        )

    def _expandNoteAndChildren(self, aNote):
        """Recursively expand a note and all its children in this viewer."""
        context = self.settingsSection()
        aNote.expand(True, context=context, notify=False)
        for child in aNote.children():
            self._expandNoteAndChildren(child)

    def pasteItemCommand(self):
        """Paste notes from clipboard to this task's notes as top-level notes.

        Clears parent reference so notes always become top-level, even if
        copied from a nested location.
        """
        from taskcoachlib.command.clipboard import Clipboard

        items, source = Clipboard().get()
        copies = [item.copy() for item in items]
        # Clear parent so notes become top-level (even if source was nested)
        # and expand all pasted notes so children are visible
        for n in copies:
            n.setParent(None)
            self._expandNoteAndChildren(n)
        return command.AddNoteCommand(None, [self.__note_owner], notes=copies)

    def pasteAsSubItemCommand(self):
        """Paste notes as subnotes of the selected note.

        Uses AddSubNoteCommand which properly adds notes as children only,
        not to the owner's notes list (which would cause duplicates).
        """
        selected = self.curselection()
        if not selected:
            return None
        parent_note = selected[0]
        from taskcoachlib.command.clipboard import Clipboard

        items, source = Clipboard().get()
        copies = [item.copy() for item in items]
        # Clear parent references - AddSubNoteCommand will set correct parent via addChild
        # and expand all pasted notes so children are visible
        for n in copies:
            n.setParent(None)
            self._expandNoteAndChildren(n)
        # Also expand the parent note so the pasted subnotes are visible
        parent_note.expand(True, context=self.settingsSection(), notify=False)
        # Repeat parent_note for each copy so zip in AddSubNoteCommand pairs correctly
        parents = [parent_note] * len(copies)
        return command.AddSubNoteCommand(
            None, parents, owner=self.__note_owner, notes=copies
        )


class NotesPage(PageWithViewer):
    """
    Page d'édition des notes d'un objet.

    Permet d'ajouter ou modifier des notes attachées à un objet.
    Cette classe permet d'ajouter, modifier et supprimer des notes associées à un objet.
    Elle hérite de la classe `PageWithViewer` pour gérer l'affichage et l'édition des notes.

    Attributs :
        pageName (str) : Nom interne de la page ("notes").
        pageTitle (str) : Titre affiché à l'utilisateur ("Notes").
        pageIcon (str) : Nom de l'icône associée à la page ("note_icon").

    Méthodes :
        createViewer (self, taskFile, settings, settingsSection) :
            Crée un visualiseur de notes local pour l'objet.

        onNotesChanged (self, event) :
            Rafraîchit le visualiseur de notes lorsque la liste des notes change.

        entries (self) : Ajoute les champs d'entrée pour l'édition des notes.
            Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur de notes.

    Explication :

    Héritage de PageWithViewer : Cette classe hérite de PageWithViewer
    pour bénéficier des fonctionnalités de base de la page d'édition.

    Création du Visualiseur de Notes : La méthode createViewer
    crée un LocalNoteViewer pour afficher et gérer les notes associées à l'objet.

    Gestion des Changements de Notes : La méthode onNotesChanged est appelée
    lorsque la liste des notes change, ce qui permet de rafraîchir le visualiseur pour refléter les modifications.

    Affichage des Éléments : La méthode entries renvoie un dictionnaire contenant
    les éléments d'entrée de la page, y compris le visualiseur de notes,
    qui sera utilisé pour l'affichage dans la boîte de dialogue d'édition.
    """

    # Attributs :
    # Nom interne de la page ("notes") :
    pageName = "notes"
    # Titre affiché à l'utilisateur ("Notes") :
    pageTitle = _("Notes")
    # Nom de l'icône associée à la page ("note_icon") :
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
        super().__init__(
            items, parent, taskFile, settings, settingsSection, *args, **kwargs
        )
        self.addEntries()

    def createViewer(self, taskFile, settings, settingsSection):
        """Crée un visualiseur de notes local pour l'objet."""
        assert len(self.items) == 1
        item = self.items[0]
        self.registerObserver(
            self.onNotesChanged,
            eventType=item.notesChangedEventType(),
            eventSource=item,
        )
        return LocalNoteViewer(
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
            owner=item,
        )

    def onNotesChanged(self, event):  # pylint: disable=W0613
        """Rafraîchit le visualiseur de notes lorsque la liste des notes change."""
        self.viewer.domainObjectsToView().clear()
        self.viewer.domainObjectsToView().extend(self.items[0].notes())

    def entries(self):
        """Renvoie un dictionnaire contenant les éléments d'entrée de la page, y compris le visualiseur de notes."""
        if hasattr(self, "viewer"):
            return dict(firstEntry=self.viewer, notes=self.viewer)
        return dict()

    # def addEntries(self):
    #     """
    #     Ajoute les champs d'entrée pour l'édition des notes associées à un objet.
    #     """
    #     pass


class LocalPrerequisiteViewer(CheckableTaskViewer):  # pylint: disable=W0223
    # class LocalPrerequisiteViewer(viewer.CheckableTaskViewer):  # pylint: disable=W0223
    """
    Classe de visualiseur de prérequis locaux.

    Cette classe hérite de `CheckableTaskViewer` et est spécialisée pour gérer les prérequis des tâches.

    Attributs :
        __items : La liste des tâches dont on gère les prérequis.

    Méthodes :
        getIsItemChecked (self, item) :
            Détermine si une tâche donnée est sélectionnée comme prérequis.

        getIsItemCheckable (self, item) :
            Détermine si une tâche donnée peut être sélectionnée comme prérequis.

        onCheck (self, event, final) :
            Gère l'événement de sélection/désélection d'une tâche en tant que prérequis.

    Explication :

    Héritage : cette classe hérite de CheckableTaskViewer, qui fournit la fonctionnalité de base pour afficher une liste de tâches avec des cases à cocher.

    Propriété des tâches : l'attribut __items stocke la liste des tâches dont les prérequis sont gérés.

    Cocher/décocher des tâches : les méthodes getIsItemChecked et getIsItemCheckable déterminent l'état de vérification initial et si une tâche peut être cochée ou décochée.

    Gestion des modifications de vérification : la méthode onCheck est déclenchée lorsqu'un utilisateur coche ou décoche une tâche. Il crée et exécute une TogglePrerequisiteCommand pour mettre à jour les prérequis de la tâche.
    """

    # from taskcoachlib.gui.viewer
    def __init__(self, items, *args, **kwargs):
        # La liste des tâches dont on gère les prérequis.
        self.__items = items
        super().__init__(*args, **kwargs)

    def getIsItemChecked(self, item):
        """Détermine si une tâche donnée est sélectionnée comme prérequis."""
        return item in self.__items[0].prerequisites()

    def getIsItemCheckable(self, item):
        """Détermine si une tâche donnée peut être sélectionnée comme prérequis."""
        log.debug(
            f"LocalPrerequisiteViewer.getIsItemCheckable(item={item}): retourne {item not in self.__items}"
        )
        return item not in self.__items

    def onCheck(self, event, final):
        """Gère l'événement de sélection/désélection d'une tâche en tant que prérequis."""
        item = self.widget.GetItemPyData(
            event.GetItem()
        )  # TODO: test with GetItemData
        is_checked = event.GetItem().IsChecked()
        if is_checked != self.getIsItemChecked(item):
            checked, unchecked = ([item], []) if is_checked else ([], [item])
            command.TogglePrerequisiteCommand(
                None,
                self.__items,
                checkedPrerequisites=checked,
                uncheckedPrerequisites=unchecked,
            ).do()


class PrerequisitesPage(PageWithViewer):
    """
    Page d'édition des prérequis d'une tâche.

    Permet de définir des tâches prérequises à accomplir avant celle en cours.

    Méthodes :
        addEntries (self) : Ajoute les champs d'entrée pour l'édition des prérequis.
    """

    pageName = "prerequisites"
    pageTitle = _("Prerequisites")
    pageIcon = "trafficlight_icon"

    def __init__(self, *args, **kwargs):
        self.__realized = False
        super().__init__(*args, **kwargs)
        # # Ajoute les champs d'entrée :
        # self.addEntries()

    def addEntries(self):
        pass

    # def addEntries(self):
    #     """
    #     Ajoute les champs d'entrée pour définir les prérequis d'une tâche.
    #     """
    #     self.viewer = self.createViewer(
    #         self.taskFile, self.settings, self.settingsSection
    #     )
    #     self.addEntry(self.viewer)

    # def addEntries(self):
    #     self.viewer = self.createViewer(
    #         self.items[0].taskFile,  # à adapter selon le code
    #         self.settings,
    #         self.settingsSection
    #     )
    #     self.addEntry(self.viewer)

    def selected(self):
        """Gère la sélection de la page et ajoute les champs d'édition seulement lors du premier affichage."""
        if not self.__realized:
            self.__realized = True
            # super().addEntries()  # Non, plutôt :
            self.addEntries()
            self.fit()

    def createViewer(self, taskFile, settings, settingsSection):
        assert len(self.items) == 1
        pub.subscribe(
            self.onPrerequisitesChanged,
            self.items[0].prerequisitesChangedEventType(),
        )
        return LocalPrerequisiteViewer(
            self.items,
            self,
            taskFile,
            settings,
            settingsSection=settingsSection,
            use_separate_settings_section=False,
        )

    def onPrerequisitesChanged(self, newValue, sender):
        if sender == self.items[0]:
            self.viewer.refreshItems(*newValue)

    def entries(self):
        if self.__realized and hasattr(self, "viewer"):
            return dict(
                firstEntry=self.viewer,
                prerequisites=self.viewer,
                dependencies=self.viewer,
            )
        return dict()


class PathPage(Page):
    # class PathPage(ScrolledPage):
    """Page that displays the hierarchical path (nesting) of the current object.

    The path is built only when the tab is selected (lazy loading).
    It subscribes to ALL modification events to catch any change that might
    affect the path, and rebuilds when the tab is visible.
    """

    pageName = "path"
    pageTitle = _("Path")
    pageIcon = "arrow_down_right"
    columns = 1

    def __init__(self, items, parent, taskFile, *args, **kwargs):
        self._taskFile = taskFile
        self._pathPanel = None
        self._pathSizer = None
        self._subscribed = False
        self._realized = False
        self._iconWidgets = (
            {}
        )  # Dict of object -> StaticBitmap for icon updates
        self._iconSubscribed = False
        super().__init__(items, parent, *args, **kwargs)

    def addEntries(self):
        """Create the container panel (content built lazily in selected())."""
        self._pathPanel = wx.Panel(self)
        self._pathSizer = wx.BoxSizer(wx.VERTICAL)
        self._pathPanel.SetSizer(self._pathSizer)
        self.addEntry(self._pathPanel, growable=True, flags=[wx.EXPAND])

    def selected(self):
        """Called when this tab is selected. Build/rebuild the path display."""
        if not self._realized:
            self._realized = True
            self._subscribeToChanges()
        self._rebuildPathDisplay()

    def _subscribeToChanges(self):
        """Subscribe to all modification events that could affect the path."""
        if self._subscribed:
            return
        self._subscribed = True

        # Subscribe to effective icon changes for individual icon updates
        self._ensureIconSubscription()

        from taskcoachlib.domain import (
            task,
            category,
            note,
            attachment,
            effort,
        )

        # Subscribe to parent pubsub topics (pubsub uses hierarchical topics)
        # This catches all child topic messages (e.g., pubsub.task covers
        # pubsub.task.subject, pubsub.task.dependencies, etc.)
        pubsub_parent_topics = [
            "pubsub.task",
            "pubsub.category",
            "pubsub.note",
            "pubsub.attachment",
        ]
        for topic in pubsub_parent_topics:
            pub.subscribe(self._onAnyChange, topic)

        # Subscribe to deprecated event types via patterns.Publisher
        all_event_types = (
            task.Task.modificationEventTypes()
            + category.Category.modificationEventTypes()
            + note.Note.modificationEventTypes()
            + effort.Effort.modificationEventTypes()
            + attachment.FileAttachment.modificationEventTypes()
            + attachment.URIAttachment.modificationEventTypes()
            + attachment.MailAttachment.modificationEventTypes()
        )

        for eventType in all_event_types:
            if not eventType.startswith("pubsub"):
                patterns.Publisher().registerObserver(
                    self._onAnyChange,
                    eventType=eventType,
                )

    def _onAnyChange(self, event=None, **kwargs):
        """Called when any domain object changes. Rebuild if visible."""
        if self._realized and self._pathPanel:
            try:
                if self._pathPanel.IsShownOnScreen():
                    wx.CallAfter(self._rebuildPathDisplay)
            except RuntimeError:
                pass  # Window destroyed

    def _rebuildPathDisplay(self):
        """Rebuild the path display with all sections."""
        if not self._pathPanel or not self._pathSizer:
            return
        try:
            self._pathPanel.GetName()  # Check if still valid
        except RuntimeError:
            return

        # Unsubscribe existing icon handlers before clearing
        self._unsubscribeIconUpdates()

        # Clear existing content
        self._pathSizer.Clear(True)

        # Only show sections for single item
        if len(self.items) != 1:
            label = wx.StaticText(
                self._pathPanel, label=_("Path is only shown for single items")
            )
            self._pathSizer.Add(label, 0, wx.EXPAND)
            self._pathPanel.Layout()
            return

        item = self.items[0]

        # Section: Path
        self._buildPathSection(item)

        # Section: Categories (Tasks and Notes only)
        from taskcoachlib.domain import task as task_module, note

        if isinstance(item, (task_module.Task, note.Note)):
            self._buildCategoriesSection(item)

        # Section: Prerequisites (Tasks only)
        if isinstance(item, task_module.Task):
            self._buildPrerequisitesSection(item)

        # Section: Dependants (Tasks only)
        if isinstance(item, task_module.Task):
            self._buildDependantsSection(item)

        self._pathPanel.Layout()
        self.Layout()
        self.SetupScrolling(scroll_x=True, scroll_y=True)

    # -- Section builders --------------------------------------------------

    def _buildPathSection(self, item):
        """Build the Path section: header + hierarchical path display."""
        self._addSectionHeader(_("Path"))
        path_objects = self._buildPathObjects(item)

        if not path_objects:
            label = wx.StaticText(
                self._pathPanel, label=_("This item has no parent objects")
            )
            self._pathSizer.Add(label, 0, wx.EXPAND | wx.LEFT, 5)
            return

        for index, obj in enumerate(path_objects):
            obj_type, icon_name = self._getTypeInfo(obj)
            subject = obj.subject()

            item_panel = wx.Panel(self._pathPanel)
            item_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # Add indentation based on depth
            if index > 0:
                indent = wx.Panel(item_panel, size=(index * 20, 1))
                item_sizer.Add(indent, 0)
                arrow_bitmap = wx.ArtProvider.GetBitmap(
                    "arrow_down_right", wx.ART_MENU, (16, 16)
                )
                if arrow_bitmap.IsOk():
                    arrow = wx.StaticBitmap(item_panel, bitmap=arrow_bitmap)
                    item_sizer.Add(
                        arrow, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
                    )

            # Add type icon if available
            if icon_name:
                bitmap = wx.ArtProvider.GetBitmap(
                    icon_name, wx.ART_MENU, (16, 16)
                )
                if bitmap.IsOk():
                    icon = wx.StaticBitmap(item_panel, bitmap=bitmap)
                    item_sizer.Add(
                        icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
                    )
                    self._subscribeIconToObject(obj, icon)

            label_text = "[%s] %s" % (obj_type, subject)
            label = wx.StaticText(item_panel, label=label_text)

            # Make current item bold
            if index == len(path_objects) - 1:
                font = label.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                label.SetFont(font)

            item_sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
            item_panel.SetSizer(item_sizer)
            self._pathSizer.Add(item_panel, 0, wx.EXPAND | wx.ALL, 2)

    def _buildCategoriesSection(self, item):
        """Build the Categories section: separator, header, category list."""
        self._addSectionSeparator()
        self._addSectionHeader(_("Categories"))
        categories = sorted(item.categories(), key=lambda c: c.subject())
        if not categories:
            self._addNoneLabel()
            return
        for cat in categories:
            # Build breadcrumb path: "Parent > Child > Grandchild"
            ancestors = cat.ancestors()
            if ancestors:
                display = " > ".join(a.subject() for a in ancestors)
                display += " > " + cat.subject()
            else:
                display = cat.subject()
            self._addItemRow(cat, display_text=display)

    def _buildPrerequisitesSection(self, item):
        """Build the Prerequisites section: separator, header, task list."""
        self._addSectionSeparator()
        self._addSectionHeader(_("Prerequisites"))
        prerequisites = sorted(item.prerequisites(), key=lambda t: t.subject())
        if not prerequisites:
            self._addNoneLabel()
            return
        for prereq in prerequisites:
            self._addItemRow(prereq)

    def _buildDependantsSection(self, item):
        """Build the Dependants section: separator, header, task list."""
        self._addSectionSeparator()
        self._addSectionHeader(_("Dependants"))
        dependants = sorted(item.dependencies(), key=lambda t: t.subject())
        if not dependants:
            self._addNoneLabel()
            return
        for dep in dependants:
            self._addItemRow(dep)

    # -- Shared helpers ----------------------------------------------------

    def _addSectionSeparator(self):
        """Add a horizontal line separator to the path panel."""
        line = wx.StaticLine(self._pathPanel)
        self._pathSizer.Add(line, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)

    def _addSectionHeader(self, title):
        """Add a bold section header to the path panel."""
        header = wx.StaticText(self._pathPanel, label=title)
        font = header.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        self._pathSizer.Add(header, 0, wx.EXPAND | wx.BOTTOM, 4)

    def _addNoneLabel(self):
        """Add a '(none)' label for empty sections."""
        label = wx.StaticText(self._pathPanel, label=_("(none)"))
        self._pathSizer.Add(label, 0, wx.LEFT, 20)

    def _addItemRow(self, obj, display_text=None):
        """Add an item row with icon and label to the path panel."""
        obj_type, icon_name = self._getTypeInfo(obj)
        item_panel = wx.Panel(self._pathPanel)
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add type icon if available
        if icon_name:
            bitmap = wx.ArtProvider.GetBitmap(icon_name, wx.ART_MENU, (16, 16))
            if bitmap.IsOk():
                icon = wx.StaticBitmap(item_panel, bitmap=bitmap)
                item_sizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
                self._subscribeIconToObject(obj, icon)

        label_text = display_text or ("[%s] %s" % (obj_type, obj.subject()))
        label = wx.StaticText(item_panel, label=label_text)
        item_sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)

        item_panel.SetSizer(item_sizer)
        self._pathSizer.Add(item_panel, 0, wx.EXPAND | wx.ALL, 2)

    def _subscribeIconToObject(self, obj, bitmap):
        """Register a StaticBitmap for updates when object's effective icon changes."""
        if not hasattr(obj, "effectiveIconChangedEventType"):
            return
        self._iconWidgets[id(obj)] = (obj, bitmap)

    def _ensureIconSubscription(self):
        """Subscribe to effective icon changes (once per rebuild)."""
        if self._iconSubscribed:
            return
        self._iconSubscribed = True
        self.registerObserver(
            self._onEffectiveIconChanged, eventType="pubsub.effective.icon"
        )

    def _onEffectiveIconChanged(self, event):
        """Handle effective icon changes - update only the matching icon widget."""
        for source in event.sources():
            obj_id = id(source)
            if obj_id in self._iconWidgets:
                obj, bitmap = self._iconWidgets[obj_id]
                try:
                    _, icon_name = self._getTypeInfo(obj)
                    if icon_name:
                        new_bitmap = wx.ArtProvider.GetBitmap(
                            icon_name, wx.ART_MENU, (16, 16)
                        )
                        if new_bitmap.IsOk():
                            bitmap.SetBitmap(new_bitmap)
                            bitmap.Refresh()
                except RuntimeError:
                    pass  # Widget destroyed

    def _unsubscribeIconUpdates(self):
        """Clear icon widget tracking (subscription cleaned up on page close)."""
        self._iconWidgets = {}

    def _buildPathObjects(self, item):
        """Build the path from root to current item.

        Returns a list of actual objects for display.
        """
        path = []

        # Find owner for notes and attachments
        owner = self._findOwner(item)
        if owner:
            owner_path = self._buildPathObjects(owner)
            path.extend(owner_path)

        # Add ancestors for composite objects
        if hasattr(item, "ancestors"):
            path.extend(item.ancestors())

        # Add current item
        path.append(item)
        return path

    def close(self):
        """Clean up observers when the page is closed."""
        # Unsubscribe icon-specific handlers
        self._unsubscribeIconUpdates()

        if self._subscribed:
            from taskcoachlib.domain import (
                task,
                category,
                note,
                attachment,
                effort,
            )

            all_event_types = (
                task.Task.modificationEventTypes()
                + category.Category.modificationEventTypes()
                + note.Note.modificationEventTypes()
                + effort.Effort.modificationEventTypes()
                + attachment.FileAttachment.modificationEventTypes()
                + attachment.URIAttachment.modificationEventTypes()
                + attachment.MailAttachment.modificationEventTypes()
            )
            for eventType in all_event_types:
                if eventType.startswith("pubsub"):
                    try:
                        pub.unsubscribe(self._onAnyChange, eventType)
                    except Exception:
                        pass
            patterns.Publisher().removeObserver(self._onAnyChange)
        super().close()

    def _getTypeInfo(self, obj):
        """Get the type name and effective icon for an object."""
        from taskcoachlib.domain import task as task_module
        from taskcoachlib.domain import category, note, attachment, effort

        if isinstance(obj, task_module.Task):
            return (_("Task"), obj.effectiveIcon())
        elif isinstance(obj, category.Category):
            return (_("Category"), obj.effectiveIcon())
        elif isinstance(obj, note.Note):
            return (_("Note"), obj.effectiveIcon())
        elif isinstance(obj, attachment.Attachment):
            return (_("Attachment"), obj.effectiveIcon())
        elif isinstance(obj, effort.Effort):
            return (_("Effort"), "clock_icon")
        else:
            return (_("Item"), None)

    def _findOwner(self, item):
        """Find the immediate owner of a note or attachment.

        Notes can be owned by: tasks, categories, attachments, or other notes (parent)
        Attachments can be owned by: tasks, categories, or notes
        Efforts are owned by their task

        For notes with a parent note, returns None (ancestors() handles the hierarchy).
        For root-level notes, finds the task/category/attachment that owns it.
        """
        from taskcoachlib.domain import note, attachment, effort

        # Efforts have a task() method that returns their owner
        if isinstance(item, effort.Effort):
            return item.task()

        if not isinstance(item, (note.Note, attachment.Attachment)):
            return None

        # For notes with a parent note, the parent relationship is handled by ancestors()
        # But we still need to find the owner of the ROOT note in the hierarchy
        if isinstance(item, note.Note) and item.parent():
            # Get the root note (the one without a parent)
            root_note = item
            while root_note.parent():
                root_note = root_note.parent()
            # Find owner of root note
            return self._findNoteOwner(root_note)

        # For root-level notes
        if isinstance(item, note.Note):
            return self._findNoteOwner(item)

        # For attachments
        return self._findAttachmentOwner(item)

    def _findNoteOwner(self, target_note):
        """Find the owner of a root-level note (task, category, or attachment)."""
        # Check tasks
        for t in self._taskFile.tasks():
            if target_note in t.notes(recursive=False):
                return t

        # Check categories
        for c in self._taskFile.categories():
            if target_note in c.notes(recursive=False):
                return c

        # Check all attachments (they can own notes too)
        # This requires searching through all attachments in the system
        owner = self._findNoteOwnerInAttachments(target_note)
        if owner:
            return owner

        return None

    def _findNoteOwnerInAttachments(self, target_note):
        """Search for a note's owner among all attachments in the system."""
        # We need to search ALL attachments, including deeply nested ones
        # Attachments can be owned by tasks, categories, notes, and notes owned by attachments...

        visited = set()
        attachments_to_check = []

        # Collect all "root" attachments from tasks and categories
        for t in self._taskFile.tasks():
            attachments_to_check.extend(t.attachments())
        for c in self._taskFile.categories():
            attachments_to_check.extend(c.attachments())

        # Also from global notes and their children
        for n in self._taskFile.notes():
            attachments_to_check.extend(n.attachments())
            for child in n.children(recursive=True):
                attachments_to_check.extend(child.attachments())

        # From task notes
        for t in self._taskFile.tasks():
            for n in t.notes(recursive=True):
                attachments_to_check.extend(n.attachments())

        # From category notes
        for c in self._taskFile.categories():
            for n in c.notes(recursive=True):
                attachments_to_check.extend(n.attachments())

        # Now search through all attachments, including their nested notes' attachments
        while attachments_to_check:
            att = attachments_to_check.pop()
            att_id = att.id()
            if att_id in visited:
                continue
            visited.add(att_id)

            # Check if this attachment owns our target note
            if hasattr(att, "notes"):
                if target_note in att.notes(recursive=False):
                    return att
                # Add attachments from this attachment's notes to search
                for n in att.notes(recursive=True):
                    attachments_to_check.extend(n.attachments())

        return None

    def _findAttachmentOwner(self, target_attachment):
        """Find the owner of an attachment (task, category, or note)."""
        # Check tasks
        for t in self._taskFile.tasks():
            if target_attachment in t.attachments():
                return t

        # Check categories
        for c in self._taskFile.categories():
            if target_attachment in c.attachments():
                return c

        # Check all notes (including deeply nested ones)
        owner = self._findAttachmentOwnerInNotes(target_attachment)
        if owner:
            return owner

        return None

    def _findAttachmentOwnerInNotes(self, target_attachment):
        """Search for an attachment's owner among all notes in the system."""
        visited = set()
        notes_to_check = []

        # Collect all "root" notes from tasks and categories
        for t in self._taskFile.tasks():
            notes_to_check.extend(t.notes(recursive=True))
        for c in self._taskFile.categories():
            notes_to_check.extend(c.notes(recursive=True))

        # Global notes
        for n in self._taskFile.notes():
            notes_to_check.append(n)
            notes_to_check.extend(n.children(recursive=True))

        # Now we also need to check notes owned by attachments
        # First, collect all attachments from tasks, categories, and notes
        attachments_checked = set()
        attachments_to_check = []
        for t in self._taskFile.tasks():
            attachments_to_check.extend(t.attachments())
        for c in self._taskFile.categories():
            attachments_to_check.extend(c.attachments())
        # Also from global notes
        for n in self._taskFile.notes():
            attachments_to_check.extend(n.attachments())
            for child in n.children(recursive=True):
                attachments_to_check.extend(child.attachments())

        # Search notes, and also add notes from attachments
        while notes_to_check or attachments_to_check:
            # Process notes
            while notes_to_check:
                n = notes_to_check.pop()
                note_id = n.id()
                if note_id in visited:
                    continue
                visited.add(note_id)

                # Check if this note owns our target attachment
                if target_attachment in n.attachments():
                    return n

                # Add this note's attachments to check for more notes
                for att in n.attachments():
                    if att.id() not in attachments_checked:
                        attachments_to_check.append(att)

            # Process attachments to find more notes
            while attachments_to_check:
                att = attachments_to_check.pop()
                att_id = att.id()
                if att_id in attachments_checked:
                    continue
                attachments_checked.add(att_id)

                # Add notes from this attachment
                if hasattr(att, "notes"):
                    for n in att.notes(recursive=True):
                        if n.id() not in visited:
                            notes_to_check.append(n)

        return None

    def entries(self):
        return dict(firstEntry=self, path=self)


class EditBook(widgets.Notebook):
    """
    Fenêtre principale de l'éditeur dans Task Coach.

    Cette fenêtre contient les différentes pages d'édition (sujet, apparence, dates, etc.)
    pour modifier les objets de Task Coach.

    Objectif :
        Cette classe sert de fenêtre principale pour modifier divers objets
        dans Task Coach, tels que des tâches, des notes, etc.
        Elle fournit une interface à onglets avec différentes pages
        pour modifier divers aspects de l'objet.

    Méthodes clés :

        __init__ (self, *args, **kwargs) : initialise l'éditeur avec les objets à modifier.
        addPages (self) : ajoute les pages pertinentes à l'éditeur en fonction du type d'objet et des paramètres configurés.
        NavigateBook : navigue entre les différentes pages de l'éditeur.
        onPageChanged : Gère les événements de changement de page, en s'assurant que la page active est correctement initialisée.
        getPage et getPageIndex : Méthodes d'assistance pour récupérer une page par son nom ou son index.
        __get_minimum_page_size : Calcule la taille minimale de l'éditeur en fonction de la taille de ses pages.
        __pages_to_create : Détermine quelles pages doivent être incluses dans l'éditeur en fonction du type d'objet et du mode d'édition.
        __should_create_page : Vérifie si une page spécifique doit être créé en fonction du type d'objet et du mode d'édition.
        __page_supports_mass_editing (page_name) : Indique si la page_module prend en charge la modification de plusieurs éléments à la fois.
        createPage : crée la page appropriée en fonction du nom de la page et du type d'objet.
        create_subject_page : crée la page sujet pour modifier le titre de l'objet.
        setFocus : Définit le focus sur un contrôle spécifique sur une page spécifique.
        isDisplayingItemOrChildOfItem : Vérifie si un élément donné est en cours de modification ou si l'un de ses enfants est en cours de modification.
        perspective : Renvoie la configuration de mise en page actuelle de l'éditeur.
        __load_perspective : charge la configuration de mise en page enregistrée pour l'éditeur.
        __save_perspective : enregistre la configuration de mise en page actuelle pour une utilisation ultérieure.
        settings_section : renvoie le nom de la section des paramètres pour la configuration actuelle de l'éditeur.
        __create_settings_section : crée un nouvelle section de paramètres si elle n'existe pas.
        close_edit_book : ferme l'éditeur et enregistre la mise en page actuelle.
    """

    allPageNames = ["subclass responsibility"]
    domainObject = "subclass responsibility"

    def __init__(self, parent, items, taskFile, settings, items_are_new):
        """
        Initialise l'éditeur avec les objets à éditer.
        """
        # --- LOG 1 : À l'entrée de __init__ de Page ---
        log.debug(
            f"--- EditBook.__init__ Début de la boucle de création de pages ---"
        )
        log.debug(f"  parent (reçu par EditBook): {parent}")
        log.debug(f"  items (reçu par EditBook): {items}")
        log.debug(f"  taskFile (reçus par EditBook): {taskFile}")
        log.debug(f"  settings (reçus par EditBook): {settings}")
        log.debug(f"  items_are_new (reçus par EditBook): {items_are_new}")
        log.debug("EditBook : Initialisation MRO:", Page.__mro__)
        self.items = items
        self.settings = settings
        # --- LOG 2 : Avant l'appel à super().__init__ ---
        log.debug(f"  EditBook.__init__ - Appel de super().__init__ avec:")
        log.debug(f"    parent passé à super: {parent}")
        super().__init__(parent)
        self.addPages(taskFile, items_are_new)
        self.__load_perspective(items_are_new)

    def NavigateBook(self, forward):
        """Naviguer entre les différentes pages de l'éditeur."""
        curSel = self.GetSelection()
        curSel = curSel + 1 if forward else curSel - 1
        if 0 <= curSel < self.GetPageCount():
            self.SetSelection(curSel)

    def addPages(self, task_file, items_are_new):
        """
        Ajoute les différentes pages d'édition à l'éditeur.

        Ajoute les pages d'édition spécifiques à l'éditeur.
        Ajoute les pages pertinentes à l'éditeur en fonction du type d'objet et des paramètres configurés.
        Chaque type d'objet (tâche, note, etc.) aura ses propres pages d'édition (sujet, apparence, etc.).
        """
        page_names = self.settings.getlist(self.settings_section(), "pages")
        for page_name in page_names:
            page = self.createPage(page_name, task_file, items_are_new)
            self.AddPage(page, page.pageTitle, page.pageIcon)
        # # DISABLED: SetMinSize was locking entire notebook to max page size
        # width, height = self.__get_minimum_page_size()
        # self.SetMinSize((width, self.GetHeightForPageHeight(height)))

    def onPageChanged(self, event):
        """Gère les événements de changement de page, en s'assurant que la page active est correctement initialisée."""
        self.GetPage(
            event.Selection
        ).selected()  # Unresolved attribute reference 'Selection' for class 'Event'->events
        event.Skip()
        if operating_system.isMac():
            # The dialog loses focus sometimes...
            wx.GetTopLevelParent(self).Raise()

    def getPage(self, page_name):
        """getPage et getPageIndex : Méthodes d'assistance pour récupérer une page par son nom ou son index."""
        index = self.getPageIndex(page_name)
        if index is not None:
            return self[index]
        return None

    def getPageIndex(self, page_name):
        """getPage et getPageIndex : Méthodes d'assistance pour récupérer une page par son nom ou son index."""
        for index in range(self.GetPageCount()):
            if page_name == self[index].pageName:
                return index
        return None

    def __get_minimum_page_size(self):
        """Calcule la taille minimale de l'éditeur en fonction de la taille de ses pages."""
        min_widths, min_heights = [], []
        for page in self:
            min_width, min_height = page.GetMinSize()
            min_widths.append(min_width)
            min_heights.append(min_height)
        return max(min_widths), max(min_heights)

    def __pages_to_create(self):
        """Détermine quelles pages doivent être incluses dans l'éditeur en fonction du type d'objet et du mode d'édition."""
        return [
            page_name
            for page_name in self.allPageNames
            if self.__should_create_page(page_name)
        ]

    def __should_create_page(self, page_name):
        """Vérifie si une page spécifique doit être créé en fonction du type d'objet et du mode d'édition."""
        return (
            self.__page_supports_mass_editing(page_name)
            if len(self.items) > 1
            else True
        )

    @staticmethod
    def __page_supports_mass_editing(page_name):
        """Indique si la page_module prend en charge la modification de plusieurs éléments
        à la fois."""
        return page_name in (
            "subject",
            "dates",
            "progress",
            "budget",
            "appearance",
            "categories",
        )

    def createPage(self, page_name, task_file, items_are_new):
        """Crée la page appropriée en fonction du nom de la page et du type d'objet."""
        # TODO : changer la méthode. sans les if serait plus rapide ! utiliser plutôt with for!
        log.debug("EditBook.createPage : avec :")
        log.debug(f" page_name={page_name}")
        log.debug(f" task_file={task_file}")
        log.debug(f" items_are_new={items_are_new}")
        if page_name == "subject":
            return self.create_subject_page()
        elif page_name == "dates":
            return DatesPage(self.items, self, self.settings, items_are_new)
        elif page_name == "prerequisites":
            return PrerequisitesPage(
                self.items,
                self,
                task_file,
                self.settings,
                # settingsSection="prerequisiteviewerin%seditor" % self.domainObject,
                settingsSection=f"prerequisiteviewerin{self.domainObject}editor",
            )
        elif page_name == "progress":
            return ProgressPage(self.items, self)
        elif page_name == "categories":
            return CategoriesPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="categoryviewerin%seditor" % self.domainObject,
            )
        elif page_name == "budget":
            return BudgetPage(self.items, self)
        elif page_name == "effort":
            return EffortPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="effortviewerin%seditor" % self.domainObject,
            )
        elif page_name == "notes":
            return NotesPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="noteviewerin%seditor" % self.domainObject,
            )
        elif page_name == "attachments":
            return AttachmentsPage(
                self.items,
                self,
                task_file,
                self.settings,
                settingsSection="attachmentviewerin%seditor"
                % self.domainObject,
            )
        elif page_name == "appearance":
            return TaskAppearancePage(self.items, self)
        elif page_name == "path":
            return PathPage(self.items, self, task_file)

    def create_subject_page(self):
        """Créer la page sujet pour modifier le titre de l'objet."""
        log.debug(
            "EditBook.create_subject_page: retourne une instance de SubjectPage avec les arguments :"
        )
        log.debug(f"self.items={self.items}")
        log.debug(f"self={self}")
        log.debug(f"self.settings={self.settings}")
        return SubjectPage(self.items, self, self.settings)

    def setFocus(self, columnName):
        """Définit le focus sur un contrôle spécifique sur une page spécifique.

        Sélectionnez la bonne page de l'éditeur et le contrôle correct sur une page
        en fonction de la colonne sur laquelle l'utilisateur a double-cliqué.
        """
        page = 0
        for page_index in range(self.GetPageCount()):
            if (
                columnName in self[page_index].entries()
            ):  # Unresolved attribute reference 'entries' for class 'Window'
                page = page_index
                break
        self.SetSelection(page)
        self[page].setFocusOnEntry(columnName)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        """Vérifie si un élément donné est en cours de modification
        ou si l'un de ses enfants est en cours de modification."""
        ancestors = []
        for item in self.items:
            ancestors.extend(item.ancestors())
        return targetItem in self.items + ancestors

    def perspective(self):
        """Renvoie la perspective du bloc-notes.

        Renvoie la configuration de mise en page actuelle de l'éditeur."""
        return self.settings.gettext(self.settings_section(), "perspective")

    def __load_perspective(self, items_are_new=False):
        """charge la configuration de mise en page enregistrée pour l'éditeur.

        Chargez la perspective (mise en page) pour la combinaison actuelle de pages visibles
        à partir des paramètres."""
        perspective = self.perspective()
        if perspective:
            try:
                # TODO : DISABLED: LoadPerspective was restoring stale AuiNotebook perspective with broken sizing
                # self.LoadPerspective(perspective)
                pass
            except Exception:  # pylint: disable=W0702  finally not except
                pass
        if items_are_new:
            current_page = (
                self.getPageIndex("subject") or 0
            )  # Pour les nouveaux éléments, commencez par la page sujet.
        else:
            # Bien que la page active/actuelle soit écrite dans la chaîne perspective
            # (un + avant le numéro de la page active), la page actuelle
            # n'est pas définie lors de la restauration de la perspective.
            # Ça le fait à la main :
            try:
                current_page = int(
                    perspective.split("@")[0].split("+")[1].split(",")[0]
                )
            except (IndexError, ValueError):
                current_page = 0
        self.SetSelection(current_page)
        self.GetPage(current_page).SetFocus()

        for idx in range(self.GetPageCount()):
            page = self.GetPage(idx)
            if page.IsShown():
                page.selected()

    def __save_perspective(self):
        """Enregistre la configuration de mise en page actuelle pour une utilisation ultérieure.

        Enregistrez la perspective actuelle de l'éditeur dans les paramètres.
        Plusieurs perspectives sont prises en charge, pour chaque ensemble de pages visibles.
        Cela permet différentes perspectives, par ex. éditeurs à élément unique et
        éditeurs à éléments multiples.
        """
        page_names = [
            self[index].pageName for index in range(self.GetPageCount())
        ]
        section = self.settings_section()
        self.settings.settext(section, "perspective", self.SavePerspective())
        self.settings.setlist(section, "pages", page_names)

    def settings_section(self):
        """Renvoie le nom de la section des paramètres pour la configuration actuelle de l'éditeur.

        Créez la section des paramètres pour cette boîte de dialogue si nécessaire et
        renvoyez-la."""
        section = self.__settings_section_name()
        if not self.settings.has_section(section):
            self.__create_settings_section(section)
        else:
            # Ensure parent_offset exists for backward compatibility with old sections
            if not self.settings.has_option(section, "parent_offset"):
                self.settings.init(section, "parent_offset", "(-1, -1)")
        return section

    def __settings_section_name(self):
        """Renvoie le nom de la section de ce bloc-notes. Le nom de la section
        dépend des pages visibles afin que différentes variantes du carnet
        stockent leurs paramètres dans différentes sections.
        """
        page_names = self.__pages_to_create()
        sorted_page_names = "_".join(sorted(page_names))
        return "%sdialog_with_%s" % (self.domainObject, sorted_page_names)

    def __create_settings_section(self, section):
        """Créez la section et initialisez les options dans la section.

        Crée une nouvelle section de paramètres si elle n'existe pas.
        """
        self.settings.add_section(section)
        for option, value in list(
            dict(
                perspective="",
                pages=str(self.__pages_to_create()),
                size="(-1, -1)",
                position="(-1, -1)",
                parent_offset="(-1, -1)",  # Offset from parent window for multi-monitor support
                maximized="False",
            ).items()
        ):
            self.settings.init(section, option, value)

    def close_edit_book(self):
        """Fermez toutes les pages du livre d'édition et enregistrez la mise en page actuelle dans
        les paramètres.


        Ferme l'éditeur, enregistre la mise en page actuelle et libère les ressources associées.
        Cette méthode est appelée lors de la fermeture de la fenêtre d'édition.
        """
        for page in self:
            # page.Close()
            page.close()
        self.__save_perspective()


class TaskEditBook(EditBook):
    """
    Classe d'édition spécifique pour les tâches.

    Cette classe hérite de `EditBook` et fournit des pages d'édition spécifiques aux tâches, telles que :
        - Sujet
        - Dates
        - Prérequis
        - Progression
        - Catégories
        - Budget
        - Effort
        - Notes
        - Pièces jointes
        - Apparence
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
        "path",
    ]
    domainObject = "task"

    def create_subject_page(self):
        """
        Méthode pour créer les pages de l'éditeur.

        Returns :
            Une instance de TaskSubjectPage avec self.items, self, et self.settings.
        """
        log.debug(
            "TaskEditBook.create_subject_page: retourne une instance de TaskSubjectPage avec les arguments :"
        )
        log.debug(f"self.items={self.items}")
        log.debug(f"self={self}")
        log.debug(f"self.settings={self.settings}")
        return TaskSubjectPage(self.items, self, self.settings)


class CategoryEditBook(EditBook):
    """
    Classe d'édition spécifique pour les catégories.

    Cette classe hérite de `EditBook` et fournit des pages d'édition spécifiques aux catégories, telles que :
        - Sujet
        - Notes
        - Pièces jointes
        - Apparence
    """

    # allPageNames = ["subject", "notes", "attachments", "appearance"]
    allPageNames = ["subject", "notes", "attachments", "appearance", "path"]
    domainObject = "category"

    def create_subject_page(self):
        return CategorySubjectPage(self.items, self, self.settings)


class NoteEditBook(EditBook):
    """
    Classe d'édition spécifique pour les notes.

    Cette classe hérite de `EditBook` et fournit des pages d'édition spécifiques aux notes, telles que :
        - Sujet
        - Catégories
        - Pièces jointes
        - Apparence
    """

    # allPageNames = ["subject", "categories", "attachments", "appearance"]
    allPageNames = [
        "subject",
        "categories",
        "attachments",
        "appearance",
        "path",
    ]
    domainObject = "note"


class AttachmentEditBook(EditBook):
    """
    Classe d'édition spécifique pour les pièces jointes.

    Cette classe hérite de `EditBook` et fournit des pages d'édition spécifiques aux pièces jointes, telles que :
        - Sujet
        - Notes
        - Apparence

    Cette classe redéfinie la méthode `isDisplayingItemOrChildOfItem` pour s'assurer que seules les pièces jointes directement sélectionnées sont prises en compte.
    """

    # allPageNames = ["subject", "notes", "appearance"]
    allPageNames = ["subject", "notes", "appearance", "path"]
    domainObject = "attachment"

    def create_subject_page(self):
        return AttachmentSubjectPage(self.items, self, self.settings)

    def isDisplayingItemOrChildOfItem(self, targetItem):
        return targetItem in self.items


class EffortEditBook(Page):
    """Cette classe fournit un éditeur spécialisé pour l'édition des entrées d'effort.
    Il hérite de la classe Page de base et ajoute des fonctionnalités spécifiques pour modifier les détails de l'effort.

    Principales fonctionnalités :

        Sélection de tâches : permet à l'utilisateur de sélectionner la tâche associée à l'effort.
        Démarrer et Modification de l'heure d'arrêt : fournit des contrôles pour définir les heures de début et de fin de l'effort, y compris les options de temps relatif.
        Modification de la description : permet de modifier la description de l'effort.
        Modification des tâches : permet à l'utilisateur de modifier la tâche directement depuis l'éditeur d'effort.

    Méthodes :

        __init__ : Initialise l'éditeur avec les efforts et le fichier de tâches donnés.
        __onChoicesConfigChanged :
        getPage :
        settings_section (self) : Renvoie la section des paramètres pour la boîte de dialogue d'effort.
        perspective (self) : Renvoie la perspective de la boîte de dialogue d'effort.
        addEntries : Ajoute les différentes entrées (tâche, heure de début, heure d'arrêt time, description) à l'éditeur.
        __add_task_entry : ajoute l'entrée de sélection de tâche.
        __onStartDateTimeChanged (self, value) :
        __onChoicesChanged (self, event) :
        __add_start_and_stop_entries : ajoute les entrées d'heure de début et d'arrêt, y compris les options de temps relatif.
        __create_start_from_last_effort_button : crée un bouton pour démarrer l'effort à partir du dernier effort arrêté.
        __create_stop_now_button : Crée un bouton pour arrêter l'effort en cours.
        __create_invalid_period_message : Crée un message à afficher si l'heure de début est après l'heure d'arrêt.
        onStartFromLastEffort : Gère l'événement de démarrage de l'effort depuis le dernier effort arrêté.
        onStopNow : Gère l'événement d'arrêt de l'effort en cours.
        onStopDateTimeChanged : Gère les modifications apportées à l'heure d'arrêt, en s'assurant que l'heure de début n'est pas ultérieure.
        onDateTimeChanged : Gère les modifications apportées à l'heure de début ou de fin et met à jour le message de période invalide.
        __update_invalid_period_message : Met à jour le message de période invalide en fonction des heures de début et de fin.
        __is_period_valid (self) : Indique si la période actuelle est valide, c'est-à-dire que la date et l'heure de début sont antérieures à la date et à l'heure de fin.
        onEditTask : Ouvre l'éditeur de tâches pour la tâche sélectionnée.
        addDescriptionEntry : Ajoute l'entrée de description.
        setFocus : Définit le focus sur une entrée spécifique.
        isDisplayingItemOrChildOfItem : Détermine si un élément donné est en cours de modification.
        entries : Renvoie les entrées clés de l'éditeur.
        close_edit_book : Ferme l'éditeur sans actions spécifiques.

        Cette classe fournit une interface conviviale pour modifier les détails de l'effort,
        y compris la sélection des tâches, le suivi du temps et l'édition de la description.
    """

    # allPageNames = ['subject', 'dates'] # ou les pages pertinentes pour l'effort
    domainObject = "effort"
    columns = 3  # Label, DateTime row, Button/Rest (matches DatesPage)

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
        # Initialisation des attributs qui seront utilisés dans entries()
        self._startDateTimeEntry = None  # Initialisation préventive
        self._stopDateTimeEntry = None
        self._taskEntry = None
        self._invalidPeriodMessage = None
        self._taskSync = None
        self._startDateTimeSync = None
        self._stopDateTimeSync = None

        self._effortList = taskFile.efforts()
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
        super().__init__(efforts, parent, *args, **kwargs)
        pub.subscribe(
            self.__onChoicesConfigChanged, "settings.feature.sdtcspans_effort"
        )

    def __onChoicesConfigChanged(self, value=""):
        self._stopDateTimeEntry.LoadChoices(value)

    # @staticmethod
    def getPage(self, pageName):  # pylint: disable=W0613
        return None  # An EffortEditBook is not really a notebook...

    # @staticmethod
    def settings_section(self):
        """Renvoie la section des paramètres pour la boîte de dialogue d'effort."""
        # Puisque la boîte de dialogue d'effort n'a pas d'onglets, la section des paramètres ne
        # dépend pas des onglets visibles.
        # renvoie la "boîte de dialogue d'effort"
        return "effortdialog"

    # @staticmethod
    def perspective(self):
        """Renvoie la perspective de la boîte de dialogue d'effort."""
        # Puisque la boîte de dialogue d'effort n'a pas d'onglets, la perspective est toujours la
        # la même et la valeur n'a pas d'importance.
        return "effort dialog perspective"

    def addEntries(self):
        """Ajoute les différentes entrées (tâche, heure de début, heure d'arrêt time, description) à l'éditeur."""
        self.__add_task_entry()
        self.__add_start_and_stop_entries()
        self.addDescriptionEntry()

    def __add_task_entry(self):
        """Ajoute l'entrée de sélection de tâche.

        Ajoutez une entrée pour modifier la tâche à laquelle appartient cet enregistrement d'effort.
        """
        # pylint: disable=W0201,W0212
        panel = wx.Panel(self)
        current_task = self.items[0].task()
        self._taskEntry = entry.TaskEntry(
            panel,
            rootTasks=self._taskList.rootItems(),
            selectedTask=current_task,
        )
        self._taskSync = attributesync.AttributeSync(
            "task",
            self._taskEntry,
            current_task,
            self.items,
            command.EditTaskCommand,
            entry.EVT_TASKENTRY,
            self.items[0].taskChangedEventType(),
        )
        edit_task_button = wx.Button(panel, label=_("Edit task"))
        edit_task_button.Bind(wx.EVT_BUTTON, self.onEditTask)
        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_sizer.Add(
            self._taskEntry,
            proportion=1,
            # flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
            # proposition de starofrainnight:
            flag=wx.EXPAND,
        )

        panel_sizer.Add((3, -1))
        panel_sizer.Add(
            edit_task_button, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL
        )
        panel.SetSizerAndFit(panel_sizer)
        self.addEntry(_("Task"), panel, flags=[None, wx.ALL | wx.EXPAND])

    def __onStartDateTimeChanged(self, value):
        self._stopDateTimeEntry.SetRelativeChoicesStart(start=value)

    def __onChoicesChanged(self, event):
        self._settings.settext("feature", "sdtcspans_effort", event.GetValue())

    def __add_start_and_stop_entries(self):
        # pylint: disable=W0201,W0142
        """Ajoute les entrées d'heure de début et d'arrêt, y compris les options de temps relatif."""
        # utilise 3 colonnes : Label, DateTime row, Button/Rest (matches DatesPage)
        # Définir l'entrée date_time comme dictionnaire d'arguments
        date_time_entry_kw_args = dict(showSeconds=True)
        flags = [
            None,
            wx.ALIGN_RIGHT | wx.ALL,
            wx.ALIGN_LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            None,
        ]

        # Définir l'entrée date_time courante de début et d'arrêt
        current_start_date_time = self.items[0].getStart()
        self._startDateTimeEntry = entry.DateTimeEntry(
            self,
            self._settings,
            current_start_date_time,
            noneAllowed=False,
            showRelative=True,
            **date_time_entry_kw_args,
        )
        wx.CallAfter(self._startDateTimeEntry.HideRelativeButton)
        self._startDateTimeSync = attributesync.AttributeSync(
            "getStart",
            self._startDateTimeEntry,
            current_start_date_time,
            self.items,
            command.EditEffortStartDateTimeCommand,
            entry.EVT_DATETIMEENTRY,
            self.items[0].startChangedEventType(),
            callback=self.__onStartDateTimeChanged,
        )
        self._startDateTimeEntry.Bind(
            entry.EVT_DATETIMEENTRY, self.onDateTimeChanged
        )
        start_from_last_effort_button = (
            self.__create_start_from_last_effort_button()
        )
        self.addEntry(
            _("Start"),
            self._startDateTimeEntry,
            start_from_last_effort_button,
            flags=flags,
        )

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
            entry.EVT_DATETIMEENTRY,
            self.items[0].stopChangedEventType(),
            callback=self.__onStopDateTimeChanged,
        )
        self._stopDateTimeEntry.Bind(
            entry.EVT_DATETIMEENTRY, self.onStopDateTimeChanged
        )
        stop_now_button = self.__create_stop_now_button()
        self._invalidPeriodMessage = self.__create_invalid_period_message()
        self.addEntry(
            _("Stop"), self._stopDateTimeEntry, stop_now_button, flags=flags
        )
        self.__onStartDateTimeChanged(current_start_date_time)
        self._stopDateTimeEntry.LoadChoices(
            self._settings.get("feature", "sdtcspans_effort")
        )
        # sdtc.EVT_TIME_CHOICES_CHANGE(self._stopDateTimeEntry, self.__onChoicesChanged)
        # self._stopDateTimeEntry.Bind(wx.adv.EVT_TIME_CHANGED, self.__onChoicesChanged)
        self._stopDateTimeEntry.Bind(
            sdtc.EVT_TIME_CHOICES_CHANGE, self.__onChoicesChanged
        )  # TODO : à vérifier

        self.addEntry("", self._invalidPeriodMessage)

    def __create_start_from_last_effort_button(self):
        """Crée un bouton pour démarrer l'effort à partir du dernier effort arrêté."""
        button = wx.Button(self, label=_("Start tracking from last stop time"))
        self.Bind(wx.EVT_BUTTON, self.onStartFromLastEffort, button)
        if self._effortList.maxDateTime() is None:
            button.Disable()
        return button

    def __create_stop_now_button(self):
        """Crée un bouton pour arrêter l'effort en cours."""
        button = wx.Button(self, label=_("Stop tracking now"))
        self.Bind(wx.EVT_BUTTON, self.onStopNow, button)
        return button

    def __create_invalid_period_message(self):
        """Crée un message à afficher si l'heure de début est après l'heure d'arrêt."""
        text = wx.StaticText(self, label="")
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        text.SetFont(font)
        text.SetForegroundColour(wx.RED)
        return text

    def onStartFromLastEffort(self, event):  # pylint: disable=W0613
        """Gère l'événement de démarrage de l'effort depuis le dernier effort arrêté."""
        maxDateTime = self._effortList.maxDateTime()
        if self._startDateTimeEntry.GetValue() != maxDateTime:
            self._startDateTimeEntry.SetValue(self._effortList.maxDateTime())
            self._startDateTimeSync.onAttributeEdited(event)
        self.onDateTimeChanged(event)

    def onStopNow(self, event):
        """Gère l'événement d'arrêt de l'effort en cours."""
        command.StopEffortCommand(self._effortList, self.items).do()

    def onStopDateTimeChanged(self, *args, **kwargs):
        """Gère les modifications apportées à l'heure d'arrêt, en s'assurant que l'heure de début n'est pas ultérieure."""
        self.onDateTimeChanged(*args, **kwargs)

    def __onStopDateTimeChanged(self, new_value):
        """Gère les modifications apportées à l'heure d'arrêt, en s'assurant que l'heure de début n'est pas ultérieure."""
        # La date/heure de début réelle n'a pas été modifiée (la classe de commande vérifie que) si
        # c'était supérieure à la date/heure d'arrêt, alors assurez-vous que c'est le cas si tout est
        # OK Maintenant.
        command.EditEffortStartDateTimeCommand(
            None, self.items, newValue=self._startDateTimeEntry.GetValue()
        ).do()

    def onDateTimeChanged(self, event):
        """Gère les modifications apportées à l'heure de début ou de fin et met à jour le message de période invalide."""
        event.Skip()
        self.__update_invalid_period_message()

    def __update_invalid_period_message(self):
        """Met à jour le message de période invalide en fonction des heures de début et de fin."""
        message = (
            ""
            if self.__is_period_valid()
            else _("Warning: start must be earlier than stop")
        )
        self._invalidPeriodMessage.SetLabel(message)

    def __is_period_valid(self):
        """Indique si la période actuelle est valide, c'est-à-dire que la date et l'heure de début
        sont antérieures à la date et à l'heure de fin."""
        try:
            return (
                self._startDateTimeEntry.GetValue()
                < self._stopDateTimeEntry.GetValue()
            )
        except AttributeError:
            return True  # Entries not created yet

    def onEditTask(self, event):  # pylint: disable=W0613
        """Ouvre l'éditeur de tâches pour la tâche sélectionnée."""
        task_to_edit = self._taskEntry.GetValue()
        TaskEditor(
            None,
            [task_to_edit],
            self._settings,
            self._taskFile.tasks(),
            self._taskFile,
        ).Show()

    def addDescriptionEntry(self):
        # pylint: disable=W0201
        """Ajoute l'entrée de description."""

        def combined_description(items):
            """Méthode de description de combinaison pour les éléments de description."""
            distinctDescriptions = set(item.description() for item in items)
            if len(distinctDescriptions) == 1 and distinctDescriptions.pop():
                return items[0].description()
            lines = ["[%s]" % _("Edit to change all descriptions")]
            # lines = [f"[{_('Edit to change all descriptions')}]"]
            lines.extend(
                item.description() for item in items if item.description()
            )
            return "\n\n".join(lines)

        current_description = (
            self.items[0].description()
            if len(self.items) == 1
            else combined_description(self.items)
        )
        self._descriptionEntry = widgets.MultiLineTextCtrl(
            self, current_description, settings=self._settings
        )
        native_info_string = self._settings.get("editor", "descriptionfont")
        # font = wx.FontFromNativeInfoString(native_info_string) if native_info_string else None
        font = wx.Font(native_info_string) if native_info_string else None
        if font:
            self._descriptionEntry.SetFont(font)
        self._descriptionEntry.SetSizeHints(300, 150)
        self._descriptionSync = attributesync.AttributeSync(
            "description",
            self._descriptionEntry,
            current_description,
            self.items,
            command.EditDescriptionCommand,
            wx.EVT_KILL_FOCUS,
            self.items[0].descriptionChangedEventType(),
        )
        self.addEntry(_("Description"), self._descriptionEntry, growable=True)

    def setFocus(self, column_name):
        """Définit le focus sur une entrée spécifique."""
        self.setFocusOnEntry(column_name)

    def isDisplayingItemOrChildOfItem(self, item):
        """Détermine si un élément donné est en cours de modification."""
        if hasattr(item, "setTask"):
            return self.items[0] == item  # Regular effort
        else:
            return item.mayContain(self.items[0])  # Composite effort

    def entries(self):
        """Renvoie les entrées clés de l'éditeur."""
        # Cette méthode est appelée par setFocus pour trouver les entrées à partir desquelles le focus peut être défini.
        # Si EffortEditBook doit exposer les entrées directement :
        # Il faut s'assurer que ces attributs sont remplis par la page qui crée les widgets !
        # Elle semble indiquer que EffortEditBook.entries() est codé en dur pour s'attendre à cet attribut. Si vous avez modifié editor.py récemment pour simplifier les constructeurs, vous avez peut-être oublié de migrer la définition de ces membres privés.
        return dict(
            firstEntry=self._startDateTimeEntry,
            task=self._taskEntry,
            startDateTime=self._startDateTimeEntry,
            stopDateTime=self._stopDateTimeEntry,
            period=self._stopDateTimeEntry,
            description=self._descriptionEntry,
            timeSpent=self._stopDateTimeEntry,
            revenue=self._taskEntry,
        )

    def close_edit_book(self):
        """Ferme l'éditeur sans actions spécifiques."""
        pass


class Editor(BalloonTipManager, widgets.Dialog):
    """Cette classe sert de classe de base pour divers éditeurs dans Task Coach,
    fournissant un cadre pour gérer le processus d'édition,
    gérer les entrées de l'utilisateur et se coordonner avec le modèle de données sous-jacent.

    Principales caractéristiques :

        - Interface à onglets : fournit une interface à onglets avec différentes pages pour modifier divers aspects de l'objet.
        - Gestion des événements : gère les événements tels que la fermeture de la fenêtre, la suppression de tâches et les modifications de sujet.
        - Gestion de la minuterie : gère une minuterie sur macOS pour gérer les problèmes potentiels de fermeture de fenêtre.
        - Création de commandes d'interface utilisateur : crée des commandes d'interface utilisateur pour les actions courantes telles que l'annulation, le rétablissement et un nouvel effort.
        - Gestion des perspectives : enregistre et charge la mise en page et la configuration de l'éditeur.

    Méthodes :

        __init__ : initialise l'éditeur avec les éléments, les paramètres et le fichier de tâches donnés. Il configure également les gestionnaires d'événements et crée les commandes de l'interface utilisateur.
        addPages : ajoute les pages pertinentes à l'éditeur en fonction du type d'objet et des paramètres configurés.
        onPageChanged : gère les événements de changement de page, garantissant que la page active est correctement initialisée.
        getPage et getPageIndex : méthodes d'assistance pour récupérer une page par son nom ou son index.
        __get_minimum_page_size : Calcule la taille minimale de l'éditeur en fonction des tailles de ses pages.
        __pages_to_create : détermine quelles pages doivent être incluses dans l'éditeur en fonction du type d'objet et du mode d'édition.
        __should_create_page : vérifie si une page spécifique doit être créée en fonction du type d'objet et du mode d'édition.
        createPage : crée la page appropriée en fonction du nom de la page et du type d'objet.
        create_subject_page : crée la page sujet pour modifier le titre de l'objet.
        setFocus : définit le focus sur un contrôle spécifique sur une page spécifique.
        isDisplayingItemOrChildOfItem : vérifie si un élément donné est en cours de modification ou si l'un de ses enfants est en cours de modification.
        perspective : renvoie la configuration de mise en page actuelle de l'éditeur.
        __load_perspective : charge la configuration de mise en page enregistrée pour l'éditeur.
        __save_perspective : enregistre la configuration de mise en page actuelle pour une utilisation future.
        settings_section : renvoie le nom de la section des paramètres pour la configuration actuelle de l'éditeur.
        __create_settings_section : crée une nouvelle section de paramètres si elle n'existe pas.
        close_edit_book : ferme l'éditeur et enregistre la mise en page actuelle.

        __on_timer : gère l'événement de minuterie sur macOS pour garantir une fermeture correcte de la fenêtre.
        __create_ui_commands : crée des commandes d'interface utilisateur pour annuler, rétablir et nouvel effort.
        createInterior :
        on_close_editor :
        on_activate :
        on_item_removed : gère l'événement de suppression d'un élément, en fermant l'éditeur si nécessaire.
        __close_if_item_is_deleted :
        on_subject_changed : gère l'événement de modification du sujet et met à jour le titre de la fenêtre.
        __title : renvoie le titre approprié pour l'éditeur en fonction du nombre d'éléments en cours de modification.

    Cette classe fournit un cadre flexible et personnalisable pour modifier différents types d'objets dans Task Coach,
    garantissant une expérience utilisateur cohérente dans différents scénarios d'édition.
    """

    # Gestion du 'wx.Timer' pour macOS
    # EditBookClass = (
    #     lambda *args: "Subclass responsibility"
    # )  # TODO: PEP 8: E731 do not assign a lambda expression, use a def

    # @staticmethod
    def EditBookClass(*args) -> str:
        return "Subclass responsibility"

    singular_title = "Subclass responsibility %s"
    plural_title = "Subclass responsibility"
    item_type_plural = "Items"

    def __init__(
        self, parent, items, settings, container, task_file, *args, **kwargs
    ):
        """Initialise l'éditeur avec les éléments, les paramètres et le fichier de tâches donnés.
        Il configure également les gestionnaires d'événements et crée les commandes de l'interface utilisateur.
        """
        self._items = items
        self._settings = settings
        self._taskFile = task_file
        self.__items_are_new = kwargs.pop("items_are_new", False)
        column_name = kwargs.pop("columnName", "")
        self.__call_after = kwargs.get("call_after", wx.CallAfter)
        super().__init__(
            parent, self.__title(), buttonTypes=wx.ID_CLOSE, *args, **kwargs
        )
        if not column_name:
            if self._interior.perspective() and hasattr(
                self._interior, "GetSelection"
            ):
                column_name = self._interior[
                    self._interior.GetSelection()
                ].pageName
            else:
                column_name = "subject"
        if column_name:
            self._interior.setFocus(column_name)

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
        self.Bind(wx.EVT_CLOSE, self.on_close_editor)

        # Note: We intentionally do NOT freeze viewers while the dialog is open.
        # Updates should propagate immediately so other windows stay in sync.
        # Controls fire EVT_VALUE_CHANGED on blur (user edits) and from
        # programmatic setters — AttributeSync commits immediately.

        if operating_system.isMac():
            # Sigh. On OS X, if you open an editor, switch back to the main window, open
            # another editor, then hit Escape twice, the second editor disappears without any
            # notification (EVT_CLOSE, EVT_ACTIVATE), so poll for this, because there might
            # be pending changes...
            id_ = (
                IdProvider.get()
            )  # Parameter 'self' unfilled -> Obtenir un identifiant unique
            # id_ = wx.ID_ANY  # lequel utiliser ?
            self.__timer = wx.Timer(self, id_)
            # wx.EVT_TIMER(self, id_, self.__on_timer)
            # self.Bind(wx.EVT_TIMER, id_, self.__on_timer)
            self.Bind(wx.EVT_TIMER, self.__on_timer, id=id_)
            self.__timer.Start(1000, False)
        else:
            self.__timer = None

        # On Mac OS X, the frame opens by default in the top-left
        # corner of the first display. This gets annoying on a
        # 2560x1440 27" + 1920x1200 24" dual screen...

        # On Windows, for some reason, the Python 2.5 and 2.6 versions
        # of wxPython 2.8.11.0 behave differently; on Python 2.5 the
        # frame opens centered on its parent but on 2.6 it opens on
        # the first display!

        # On Linux this is not needed but doesn't do any harm.
        self.CentreOnParent()
        self.__create_ui_commands()
        self.__dimensions_tracker = (
            # windowdimensionstracker.WindowSizeAndPositionTracker(
            windowdimensionstracker.WindowGeometryTracker(
                self,
                settings,
                self._interior.settings_section(),
                parent=parent,
            )
        )

    def __on_timer(self, event):
        """Gère l'événement de minuterie sur macOS pour garantir une fermeture correcte de la fenêtre."""
        if not self.IsShown():
            self.Close()

    def __create_ui_commands(self):
        """Crée des commandes d'interface utilisateur pour annuler, rétablir et nouvel effort."""
        # FIXME: les raccourcis clavier sont codés en dur ici, mais ils peuvent être
        #  modifiés dans les traductions
        # FIXME: il y a d'autres raccourcis clavier qui ne fonctionnent pas dans les boîtes de dialogue
        #  pour le moment, comme DELETE
        self.__new_effort_id = IdProvider.get()
        # self.__new_effort_id = wx.ID_ANY
        self.__next_tab_id = IdProvider.get()
        self.__prev_tab_id = IdProvider.get()
        table = wx.AcceleratorTable(
            [
                (wx.ACCEL_CMD, ord("Z"), wx.ID_UNDO),
                (wx.ACCEL_CMD, ord("Y"), wx.ID_REDO),
                (wx.ACCEL_CMD, ord("E"), self.__new_effort_id),
                (wx.ACCEL_CTRL, wx.WXK_TAB, self.__next_tab_id),
                (
                    wx.ACCEL_CTRL | wx.ACCEL_SHIFT,
                    wx.WXK_TAB,
                    self.__prev_tab_id,
                ),
            ]
        )
        self._interior.SetAcceleratorTable(table)
        # Bind tab navigation commands
        self._interior.Bind(
            wx.EVT_MENU, self.__on_next_tab, id=self.__next_tab_id
        )
        self._interior.Bind(
            wx.EVT_MENU, self.__on_prev_tab, id=self.__prev_tab_id
        )
        # pylint: disable=W0201
        self.__undo_command = uicommand.EditUndo()
        self.__redo_command = uicommand.EditRedo()
        effort_page = self._interior.getPage("effort")
        effort_viewer = effort_page.viewer if effort_page else None
        self.__new_effort_command = uicommand.EffortNew(
            viewer=effort_viewer,
            taskList=self._taskFile.tasks(),
            effortList=self._taskFile.efforts(),
            settings=self._settings,
        )
        self.__undo_command.bind(self._interior, wx.ID_UNDO)
        self.__redo_command.bind(self._interior, wx.ID_REDO)
        self.__new_effort_command.bind(self._interior, self.__new_effort_id)

    def __on_next_tab(self, event):
        """Handle Ctrl+Tab to move to next tab."""
        self._interior.AdvanceSelectionForward()

    def __on_prev_tab(self, event):
        """Handle Ctrl+Shift+Tab to move to previous tab."""
        self._interior.AdvanceSelectionBackward()

    def createInterior(self):
        return self.EditBookClass(
            self._panel,
            self._items,
            self._taskFile,
            self._settings,
            self.__items_are_new,
        )

    def on_close_editor(self, event):
        event.Skip()
        # Save dialog position/size before closing
        self.__dimensions_tracker.save()
        self._interior.close_edit_book()
        patterns.Publisher().removeObserver(self.on_item_removed)
        patterns.Publisher().removeObserver(self.on_subject_changed)
        # On Mac OS X, the text control does not lose focus when
        # destroyed...
        if operating_system.isMac():
            self._interior.SetFocusIgnoringChildren()
        if self.__timer is not None:
            self.__timer.Stop()
            IdProvider.put(
                id_=self.__timer.GetId()
            )  # Libérer l'identifiant, self = self ou IdProvider ?
        IdProvider.put(
            id_=self.__new_effort_id
        )  # Libérer l'identifiant,  self = self ou IdProvider ?
        IdProvider.put(self.__next_tab_id)
        IdProvider.put(self.__prev_tab_id)
        self.Destroy()

    # Nouvelle fonction conseillée par chatGPT
    # def __del__(self):
    #    if self.__timer and self.__timer.IsRunning():
    #        self.__timer.Stop()
    #    if self.__timer:
    #        IdProvider.put(self.__timer.GetId())  # Libérer l'identifiant

    # @staticmethod
    def on_activate(self, event):
        event.Skip()

    def on_item_removed(self, event):
        """Gère l'événement de suppression d'un élément, en fermant l'éditeur si nécessaire.

        L'élément que nous modifions ou l'un de ses ancêtres a été supprimé ou
        est masqué par un filtre. Si l'élément est réellement supprimé, fermez l'onglet
        de l'élément concerné et fermez tout l'éditeur s'il ne reste plus d'onglets
        ."""
        if self:  # Prevent _wxPyDeadObject TypeError
            self.__call_after(
                self.__close_if_item_is_deleted, list(event.values())
            )

    def __close_if_item_is_deleted(self, items):
        for item in items:
            # if (
            #     self._interior.isDisplayingItemOrChildOfItem(item)
            #     and not item in self._taskFile
            # ):  # PEP 8: E713 test for membership should be 'not in'
            if (
                self._interior.isDisplayingItemOrChildOfItem(item)
                in self._taskFile
                and item not in self._taskFile
            ):
                self.Close()
                break

    def on_subject_changed(self, event):  # pylint: disable=W0613
        """Gère l'événement de modification du sujet et met à jour le titre de la fenêtre."""
        self.SetTitle(self.__title())

    def __title(self):
        """Renvoie le titre approprié pour l'éditeur en fonction du nombre d'éléments en cours de modification."""
        return (
            self.plural_title
            if len(self._items) > 1
            else self.singular_title % self._items[0].subject()
        )


class TaskEditor(Editor):
    plural_title = _("Multiple tasks")
    singular_title = _("%s (task)")
    EditBookClass = TaskEditBook


class CategoryEditor(Editor):
    plural_title = _("Multiple categories")
    singular_title = _("%s (category)")
    EditBookClass = CategoryEditBook


class NoteEditor(Editor):
    plural_title = _("Multiple notes")
    singular_title = _("%s (note)")
    EditBookClass = NoteEditBook


class AttachmentEditor(Editor):
    plural_title = _("Multiple attachments")
    singular_title = _("%s (attachment)")
    EditBookClass = AttachmentEditBook


class EffortEditor(Editor):
    plural_title = _("Multiple efforts")
    singular_title = _("%s (effort)")
    EditBookClass = EffortEditBook
