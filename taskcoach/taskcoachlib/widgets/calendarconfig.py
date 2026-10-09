"""
Module calendarconfig.py - Gère la boîte de dialogue de configuration du calendrier dans Task Coach.

Ce module définit la classe CalendarConfigDialog, qui est une boîte de dialogue
permettant à l'utilisateur de configurer divers aspects de l'affichage du calendrier
dans l'application Task Coach. Cela inclut le type et le nombre de périodes affichées,
l'orientation du calendrier, les filtres de tâches à afficher,
et la couleur de surbrillance du jour actuel.

Copyright (C) 2011-2012 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre discrétion) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION OU D'ADAPTATION À UN USAGE PARTICULIER. Voir le
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Sinon, voir <http://www.gnu.org/licenses/>.


Task Coach - Your friendly task manager
Copyright (C) 2011-2012 Task Coach developers <developers@taskcoach.org>

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

# Importations nécessaires pour le fonctionnement de la boîte de dialogue de configuration.
# from __future__ import division  # Importation future pour la division (déjà gérée en Python 3).
#
# from builtins import str  # S'assure que 'str' est la fonction native de conversion en chaîne.
# from builtins import map # S'assure que 'map' est la fonction native de mappage.
# from past.utils import old_div # Compatibilité pour la division entière avec Python 2.
import logging
from taskcoachlib.tools import (
    wxhelper,
)  # Utilitaires wxPython pour Task Coach.
import wx  # La bibliothèque principale wxPython.
import wx.lib.colourselect as csel  # Contrôle de sélection de couleur.
from wx.lib import (
    sized_controls,
)  # Contrôles wxPython qui gèrent le dimensionnement automatique.
from taskcoachlib.i18n import (
    _,
)  # Fonction pour la traduction des chaînes de caractères.

# TODO: trouver une alternative à wxScheduler
from taskcoachlib.thirdparty.wxScheduler import (
    wxSCHEDULER_DAILY,
    wxSCHEDULER_WEEKLY,
    wxSCHEDULER_MONTHLY,
    wxSCHEDULER_HORIZONTAL,
    wxSCHEDULER_VERTICAL,
)  # Constantes pour les types de vue et d'orientation du calendrier.

log = logging.getLogger(__name__)


class CalendarConfigDialog(sized_controls.SizedDialog):
    """
    Boîte de dialogue de configuration pour le calendrier de Task Coach.

    Cette boîte de dialogue permet à l'utilisateur de modifier les paramètres
    d'affichage du calendrier, tels que la période affichée (jour, semaine, mois),
    l'orientation (horizontale/verticale), les filtres de tâches à afficher
    et les options d'affichage spécifiques (ex: ligne de temps actuelle, couleur de surbrillance).

    Hérite de sized_controls.SizedDialog pour une gestion automatique de la disposition.
    """

    # Constantes de classe pour les types de vue, d'orientation et de filtres.
    VIEWTYPES = [wxSCHEDULER_DAILY, wxSCHEDULER_WEEKLY, wxSCHEDULER_MONTHLY]
    VIEWORIENTATIONS = [wxSCHEDULER_HORIZONTAL, wxSCHEDULER_VERTICAL]
    # Les filtres sont des tuples (show_no_start, show_no_due, show_unplanned)
    VIEWFILTERS = [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, False),
        (True, True, True),
    ]

    def __init__(self, settings, settingsSection, *args, **kwargs):
        """
        Initialise la boîte de dialogue de configuration du calendrier.

        Args:
            settings: L'objet de configuration de l'application (par ex., taskcoachlib.config.Settings).
            settingsSection (str): La section des paramètres où les préférences du calendrier sont stockées.
            *args: Arguments positionnels à passer au constructeur de la classe parente (SizedDialog).
            **kwargs: Arguments nommés à passer au constructeur de la classe parente (SizedDialog).
        """
        log.debug("CalendarConfigDialog.__init__ : Lancé.")
        self._settings = (
            settings  # Stocke la référence à l'objet de paramètres.
        )
        self._settingsSection = settingsSection  # Stocke la section des paramètres spécifique au calendrier.
        super().__init__(
            *args, **kwargs
        )  # Appelle le constructeur de la classe parente.

        pane = (
            self.GetContentsPane()
        )  # Récupère le panneau principal de la boîte de dialogue.
        pane.SetSizerType(
            "form"
        )  # Définit le type de sizer pour le panneau principal comme un formulaire.
        # Cela arrange les contrôles en paires label/contrôle.

        self.createInterior(
            pane
        )  # Appelle une méthode pour créer et organiser les contrôles internes.

        # Crée les boutons standard OK et Annuler.
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetButtonSizer(
            buttonSizer
        )  # Attache les boutons à la boîte de dialogue.
        self.Fit()  # Redimensionne la boîte de dialogue pour s'adapter à son contenu.
        self.SetMinSize(self.GetSize())
        # Lie l'événement de clic du bouton OK à la méthode 'ok' de cette classe.
        # Utilise wxhelper pour obtenir le bouton OK de manière robuste.
        # buttonSizer.GetAffirmativeButton().Bind(wx.EVT_BUTTON, self.ok) # Ancienne méthode commentée.
        wxhelper.getButtonFromStdDialogButtonSizer(buttonSizer, wx.ID_OK).Bind(
            wx.EVT_BUTTON, self.ok
        )

    def createInterior(self, pane):
        """
        Crée et organise les différents groupes de contrôles à l'intérieur de la boîte de dialogue.

        Cette méthode est un point d'entrée central qui appelle d'autres méthodes
        plus spécifiques pour la création de chaque section de configuration.

        Args:
            pane (wx.Panel): Le panneau sur lequel les contrôles doivent être placés.
        """
        log.debug(
            "CalendarConfigDialog.createInterior : Crée les différents groupes de contrôles."
        )
        self.createPeriodEntry(
            pane
        )  # Crée les contrôles pour la période et le nombre de périodes.
        self.createOrientationEntry(
            pane
        )  # Crée les contrôles pour l'orientation du calendrier.
        self.createDisplayEntry(
            pane
        )  # Crée les contrôles pour les filtres d'affichage des tâches.
        self.createLineEntry(
            pane
        )  # Crée les contrôles pour l'affichage de la ligne de temps actuelle.
        self.createColorEntry(
            pane
        )  # Crée les contrôles pour la sélection de la couleur de surbrillance.

    def createPeriodEntry(self, pane):
        """
        Crée les contrôles pour configurer le type et le nombre de périodes affichées.

        Cela inclut un label, un wx.SpinCtrl pour le nombre (ex: 1, 2, 3...)
        et un wx.Choice pour le type de période (Jour(s), Semaine(s), Mois).
        Les valeurs initiales sont chargées depuis les paramètres.

        Args:
            pane (wx.Panel): Le panneau sur lequel les contrôles doivent être placés.
        """
        log.debug(
            f"CalendarConfigDialog.createPeriodEntry : crée les contrôles pour configurer le type et le nombre de périodes affichées."
        )
        label = wx.StaticText(
            pane, label=_("Kind of period displayed and its count")
        )  # Label descriptif.
        # label = wx.TextCtrl(pane,  # Ligne commentée: utilisation d'un TextCtrl au lieu de StaticText.
        #                     value=_("Kind of period displayed and its count"))
        # Définit les propriétés de sizer pour le label (alignement vertical au centre).
        label.SetSizerProps(
            valign="center"
        )  # Unresolved attribute reference 'SetSizerProps' for class 'StaticText'

        panel = sized_controls.SizedPanel(
            pane
        )  # Crée un sous-panneau pour regrouper les contrôles de période.
        panel.SetSizerType(
            "horizontal"
        )  # Le sizer du sous-panneau est horizontal.

        # Crée un SpinCtrl pour le nombre de périodes, avec une valeur par défaut de 1 et un minimum de 1.
        self._spanCount = wx.SpinCtrl(
            panel, value="1", min=1
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        self._spanCount.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre pour le SpinCtrl.

        # Définition des options pour le type de période (traduisibles).
        periods = (_("Day(s)"), _("Week(s)"), _("Month"))
        # Crée un wx.Choice (liste déroulante) pour le type de période.
        self._spanType = wx.Choice(
            panel, choices=periods
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        self._spanType.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre pour le Choice.

        # Charge la valeur du nombre de périodes depuis les paramètres et l'applique au SpinCtrl.
        self._spanCount.SetValue(
            self._settings.getint(self._settingsSection, "periodcount")
        )
        # Charge le type de vue depuis les paramètres et sélectionne l'option correspondante dans le Choice.
        selection = self.VIEWTYPES.index(
            self._settings.getint(self._settingsSection, "viewtype")
        )
        self._spanType.SetSelection(selection)

        panel.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre pour le sous-panneau.
        panel.Fit()  # Ajuste la taille du sous-panneau à son contenu.
        # Lie l'événement de changement de sélection du Choice à la méthode onChangeViewType.
        self._spanType.Bind(wx.EVT_CHOICE, self.onChangeViewType)

    def createOrientationEntry(self, pane):
        """
        Crée les contrôles pour configurer l'orientation du calendrier (Horizontal/Vertical).

        Args:
            pane (wx.Panel): Le panneau sur lequel les contrôles doivent être placés.
        """
        log.debug(
            f"CalendarConfigDialog.createOrientationEntry : Lancé sur pane={pane}."
        )
        label = wx.StaticText(
            pane, label=_("Calendar orientation")
        )  # Label descriptif.
        label.SetSizerProps(valign="center")  # Alignement vertical au centre.

        orientations = (
            _("Horizontal"),
            _("Vertical"),
        )  # Options d'orientation (traduisibles).
        # Crée un wx.Choice pour sélectionner l'orientation.
        self._orientation = wx.Choice(
            pane, choices=orientations
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        self._orientation.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre.

        # Charge l'orientation depuis les paramètres et sélectionne l'option correspondante.
        selection = self.VIEWORIENTATIONS.index(
            self._settings.getint(self._settingsSection, "vieworientation")
        )
        self._orientation.SetSelection(selection)

    def createDisplayEntry(self, pane):
        """
        Crée les contrôles pour configurer quels types de tâches doivent être affichées.

        Comprend un label et un wx.Choice avec différentes options de filtrage.
        Les valeurs initiales sont chargées depuis les paramètres.

        Args:
            pane (wx.Panel): Le panneau sur lequel les contrôles doivent être placés.
        """
        label = wx.StaticText(
            pane, label=_("Which tasks to display")
        )  # Label descriptif.
        label.SetSizerProps(valign="center")  # Alignement vertical au centre.

        # Options de filtrage des tâches (traduisibles).
        choices = (
            _("Tasks with a planned start date and a due date"),
            _("Tasks with a planned start date"),
            _("Tasks with a due date"),
            _("All tasks, except unplanned tasks"),
            _("All tasks"),
        )
        # Crée un wx.Choice pour sélectionner le filtre d'affichage.
        self._display = wx.Choice(
            pane, choices=choices
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        self._display.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre.

        # Charge les trois booléens de filtre depuis les paramètres.
        # Trouve l'index correspondant dans la liste VIEWFILTERS et sélectionne l'option.
        selection = self.VIEWFILTERS.index(
            (
                self._settings.getboolean(
                    self._settingsSection, "shownostart"
                ),  # Afficher les tâches sans date de début planifiée.
                self._settings.getboolean(
                    self._settingsSection, "shownodue"
                ),  # Afficher les tâches sans date d'échéance.
                self._settings.getboolean(
                    self._settingsSection, "showunplanned"
                ),  # Afficher les tâches non planifiées.
            )
        )
        self._display.SetSelection(selection)  # Applique la sélection.

    def createLineEntry(self, pane):
        """
        Crée un contrôle pour activer/désactiver l'affichage d'une ligne
        indiquant l'heure actuelle sur le calendrier.

        Args:
            pane (wx.Panel): Le panneau sur lequel le contrôle doit être placé.
        """
        label = wx.StaticText(
            pane, label=_("Draw a line showing the current time")
        )  # Label descriptif.
        label.SetSizerProps(valign="center")  # Alignement vertical au centre.

        # Crée une case à cocher (CheckBox) pour l'option d'affichage de la ligne de temps.
        self._shownow = wx.CheckBox(
            pane
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        self._shownow.SetSizerProps(
            valign="center"
        )  # Alignement vertical au centre.
        # Charge la valeur booléenne depuis les paramètres et l'applique à la CheckBox.
        self._shownow.SetValue(
            self._settings.getboolean(self._settingsSection, "shownow")
        )

    def createColorEntry(self, pane):
        """
        Crée un contrôle pour sélectionner la couleur de surbrillance utilisée
        pour le jour actuel dans le calendrier.

        Args:
            pane (wx.Panel): Le panneau sur lequel le contrôle doit être placé.
        """
        label = wx.StaticText(
            pane, label=_("Color used to highlight the current day")
        )  # Label descriptif.
        label.SetSizerProps(valign="center")  # Alignement vertical au centre.

        # Tente de récupérer la couleur de surbrillance depuis les paramètres.
        hcolor = self._settings.get(self._settingsSection, "highlightcolor")
        if not hcolor:
            # Si aucune couleur n'est définie dans les paramètres ou si elle est vide.
            # La couleur de surbrillance par défaut du système est souvent trop foncée pour être un fond.
            # Récupère la couleur de surbrillance du système.
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
            # Éclaircit la couleur en la mélangeant avec le blanc (255,255,255).
            color = wx.Colour(
                int((color.Red() + 255) / 2),
                int((color.Green() + 255) / 2),
                int((color.Blue() + 255) / 2),
            )
        else:
            # Si une couleur est définie dans les paramètres (format "R,G,B").
            # Convertit la chaîne "R,G,B" en un tuple d'entiers et crée un objet wx.Colour.
            color = wx.Colour(
                *tuple(
                    map(int, hcolor.split(","))
                )  # pylint: disable=W0141 # Utilisation de map est ok.
            )
        # Crée un contrôle ColourSelect pour permettre à l'utilisateur de choisir une couleur.
        self._highlight = csel.ColourSelect(
            pane, size=(100, 20)  # Définit la taille du contrôle.
        )  # pylint: disable=W0201 # Affectation dans __init__ est ok.
        label.SetSizerProps(
            valign="center"
        )  # Ré-aligne le label après la création du contrôle.
        self._highlight.SetColour(
            color
        )  # Définit la couleur initiale du sélecteur de couleur.

    def onChangeViewType(self, event):  # pylint: disable=W0613
        """
        Gère l'événement lorsque le type de période affichée (jour, semaine, mois) change.

        Si le type de vue sélectionné est "Mois", le nombre de périodes (SpinCtrl)
        est automatiquement réglé sur 1 et désactivé, car la vue mensuelle n'affiche
        qu'un seul mois à la fois. Sinon, le SpinCtrl est réactivé.

        Args:
            event (wx.Event): L'événement de changement de sélection du wx.Choice.
        """
        # Vérifie si le type de vue sélectionné est wxSCHEDULER_MONTHLY.
        if (
            self.VIEWTYPES[self._spanType.GetSelection()]
            == wxSCHEDULER_MONTHLY
        ):
            self._spanCount.SetValue(1)  # Définit le nombre de périodes à 1.
            self._spanCount.Enable(False)  # Désactive le SpinCtrl.
        else:
            self._spanCount.Enable(
                True
            )  # Réactive le SpinCtrl pour les autres vues.

    def ok(self, event=None):  # pylint: disable=W0613
        """
        Gère l'action de l'utilisateur lorsqu'il clique sur le bouton "OK".

        Cette méthode sauvegarde toutes les valeurs des contrôles dans l'objet
        de configuration de l'application et ferme la boîte de dialogue avec wx.ID_OK.

        Args:
            event (wx.Event, optional): L'événement de clic du bouton (peut être None si appelé manuellement).
        """
        settings, section = (
            self._settings,
            self._settingsSection,
        )  # Accès plus facile aux paramètres et à la section.

        # Sauvegarde le nombre de périodes dans les paramètres (converti en chaîne).
        settings.set(section, "periodcount", str(self._spanCount.GetValue()))
        # Sauvegarde le type de vue sélectionné (converti en chaîne).
        settings.set(
            section,
            "viewtype",
            str(self.VIEWTYPES[self._spanType.GetSelection()]),
        )
        # Sauvegarde l'orientation de la vue sélectionnée (convertie en chaîne).
        settings.set(
            section,
            "vieworientation",
            str(self.VIEWORIENTATIONS[self._orientation.GetSelection()]),
        )

        # Récupère les trois booléens du filtre d'affichage des tâches à partir de la sélection du Choice.
        shownostart, shownodue, showunplanned = self.VIEWFILTERS[
            self._display.GetSelection()
        ]
        # Sauvegarde chaque booléen de filtre dans les paramètres (converti en chaîne).
        settings.set(section, "shownostart", str(shownostart))
        settings.set(section, "shownodue", str(shownodue))
        settings.set(section, "showunplanned", str(showunplanned))

        # Sauvegarde la valeur de la case à cocher "afficher la ligne de temps" (convertie en chaîne).
        settings.set(section, "shownow", str(self._shownow.GetValue()))

        # Récupère la couleur sélectionnée par l'utilisateur.
        color = self._highlight.GetColour()
        # Sauvegarde la couleur de surbrillance dans les paramètres au format "R,G,B".
        settings.set(
            section,
            "highlightcolor",
            # "%d,%d,%d" % (color.Red(), color.Green(), color.Blue()), # Ancienne méthode de formatage de chaîne.
            f"{color.Red():d},{color.Green():d},{color.Blue():d}",  # Nouvelle méthode de formatage de chaîne (f-string).
        )
        # Ferme la boîte de dialogue avec un code de retour OK.
        self.EndModal(wx.ID_OK)
