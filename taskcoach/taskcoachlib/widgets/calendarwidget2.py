"""
Module calendarwidget.py - Implémente le widget de calendrier pour Task Coach.

Ce module contient les classes nécessaires pour afficher un calendrier interactif
dans l'application Task Coach, utilisant la bibliothèque wxScheduler. Il gère
la récupération et l'affichage des tâches, les interactions utilisateur telles
que la sélection, le double-clic, le clic droit, le glisser-déposer de tâches,
ainsi que la mise à jour dynamique du calendrier.

Classes principales :
    _CalendarContentProvider: Fournit les données de tâches pour le calendrier.
    CalendarWidget: Le widget wxPython principal qui intègre wxScheduler
                    et gère la logique d'affichage et d'interaction des tâches.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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
"""

# from __future__ import division # Importation future pour la division (déjà gérée en Python 3).
# from past.utils import old_div # Compatibilité pour la division entière avec Python 2.
import logging  # Module de journalisation.
import wx  # La bibliothèque principale wxPython.
from taskcoachlib.thirdparty.wxScheduler import (wxScheduler, wxSchedule,
                                                 wxReportScheduler, wxTimeFormat)  # Composants de wxScheduler.
from taskcoachlib.thirdparty.wxScheduler.wxSchedulerPaint import (
    EVT_SCHEDULE_ACTIVATED,  # Événement : un élément de calendrier est activé.
    EVT_SCHEDULE_RIGHT_CLICK,  # Événement : clic droit sur un élément.
    EVT_SCHEDULE_DCLICK,  # Événement : double-clic sur un élément.
    EVT_PERIODWIDTH_CHANGED)  # Événement : la largeur de la période d'affichage a changé.
from taskcoachlib.thirdparty.wxScheduler.wxSchedulerConstants import (
    wxSCHEDULER_WEEKSTART_MONDAY,  # Constante : la semaine commence le lundi.
    wxSCHEDULER_WEEKSTART_SUNDAY)  # Constante : la semaine commence le dimanche.
from taskcoachlib.domain import date  # Module pour la gestion des dates et heures spécifiques à Task Coach.
from taskcoachlib.widgets import draganddrop  # Module pour la gestion du glisser-déposer.
from taskcoachlib import command, render  # Modules pour les commandes et le rendu.
from . import tooltip  # Module pour les info-bulles.

log = logging.getLogger(__name__)  # Initialise le logger pour ce module.


class _CalendarContentProvider(object):
    """
    Fournit des données de contenu (tâches) pour le widget de calendrier.

    Cette classe adapte les objets tâches de Task Coach aux objets
    attendus par le wxScheduler (wxSchedule). Elle gère la conversion
    des dates et heures, l'état des tâches, et les icônes associées.
    """

    def __init__(self, settings, taskFile):
        """
        Initialise le fournisseur de contenu du calendrier.

        Args:
            settings: L'objet de configuration de l'application.
            taskFile: Le fichier de tâches actuel (TaskFile).
        """
        self._settings = settings  # Référence aux paramètres de l'application.
        self._taskFile = taskFile  # Référence au fichier de tâches.
        # Initialise un dictionnaire pour stocker les objets wxSchedule par ID de tâche.
        self._wxSchedules = {}
        # Initialise un dictionnaire pour stocker les objets wxSchedule par ID wxSchedule.
        self._wxSchedulesById = {}

    def getSchedules(self, firstDay, lastDay):
        """
        Retourne une liste d'objets wxSchedule pour une plage de dates donnée.

        Cette méthode itère sur toutes les tâches actives et non complétées,
        filtre celles qui se trouvent dans la plage de dates spécifiée
        et crée un objet wxSchedule pour chacune d'elles.

        Args:
            firstDay (date.Date): Le premier jour de la période à récupérer.
            lastDay (date.Date): Le dernier jour de la période à récupérer.

        Returns:
            list: Une liste d'objets wxSchedule.
        """
        # Réinitialise les mappings de wxSchedule.
        self._wxSchedules = {}
        self._wxSchedulesById = {}
        schedules = []  # Liste pour stocker les wxSchedule à retourner.

        # Récupère les paramètres de filtrage de la configuration du calendrier.
        showNoStart = self._settings.getboolean("calendar", "shownostart")
        showNoDue = self._settings.getboolean("calendar", "shownodue")
        showUnplanned = self._settings.getboolean("calendar", "showunplanned")

        # Parcourt toutes les tâches dans le fichier de tâches.
        for task in self._taskFile.tasks():
            # Filtre les tâches non actives ou complétées si l'option est désactivée.
            if (not showUnplanned and not task.isPlanned() and
                    not task.isDue() and not task.hasStartTime()):
                continue  # Passe à la tâche suivante si elle est "unplanned" et ne doit pas être affichée.

            # Filtre les tâches sans date de début planifiée si l'option est désactivée.
            if not showNoStart and not task.plannedStartTime():
                continue  # Passe à la tâche suivante.

            # Filtre les tâches sans date d'échéance si l'option est désactivée.
            if not showNoDue and not task.dueDate():
                continue  # Passe à la tâche suivante.

            # Si la tâche n'est ni active ni complétée, ne pas l'afficher (à moins qu'elle ait une date de début/fin).
            if not task.isActive() and not task.isCompleted():
                # Si la tâche est terminée mais qu'elle a une date de fin, elle doit être affichée
                # dans la période où elle est terminée.
                if task.completionDate() and firstDay <= task.completionDate().date() <= lastDay:
                    pass
                else:
                    continue  # Passe à la tâche suivante.

            # Crée un wxSchedule à partir de l'objet tâche.
            wxSchedule = _CalendarSchedule(task)
            # Met à jour les dates de début et de fin du wxSchedule en fonction de la tâche.
            # Définit la date de début planifiée comme heure de début (ou maintenant si non définie).
            wxSchedule.SetStartDateTime(
                self.wxDateTime(task.plannedStartTime(),
                                date.DateTime.now().tuple())
            )
            # Définit la date d'échéance comme heure de fin (ou maintenant si non définie).
            wxSchedule.SetEndDateTime(
                self.wxDateTime(task.dueDate(), date.DateTime.now().tuple())
            )

            # Lie l'objet tâche au wxSchedule pour un accès ultérieur.
            wxSchedule.SetClientData(task)

            # Vérifie si le wxSchedule est visible dans la période.
            if wxSchedule.IsVisible(firstDay, lastDay):
                schedules.append(wxSchedule)  # Ajoute le wxSchedule à la liste.
                # Stocke les mappings pour référence rapide.
                self._wxSchedules[task.id()] = wxSchedule
                self._wxSchedulesById[wxSchedule.GetId()] = wxSchedule
        return schedules  # Retourne la liste des wxSchedule.

    def wxSchedule(self, item):
        """
        Récupère l'objet wxSchedule associé à un objet tâche donné.

        Args:
            item: L'objet tâche dont on veut le wxSchedule.

        Returns:
            wxSchedule: L'objet wxSchedule correspondant.
        """
        return self._wxSchedules[item.id()]  # Retourne le wxSchedule à partir de son ID de tâche.

    def task(self, wxSchedule):
        """
        Récupère l'objet tâche associé à un objet wxSchedule donné.

        Args:
            wxSchedule (wxSchedule): L'objet wxSchedule dont on veut la tâche.

        Returns:
            Task: L'objet tâche correspondant.
        """
        return wxSchedule.GetClientData()  # La tâche est stockée comme ClientData dans wxSchedule.

    def wxScheduleById(self, id):
        """
        Récupère l'objet wxSchedule par son ID wxSchedule.

        Args:
            id (int): L'ID de l'objet wxSchedule.

        Returns:
            wxSchedule: L'objet wxSchedule correspondant.
        """
        return self._wxSchedulesById[id]  # Retourne le wxSchedule à partir de son ID wxSchedule.

    @staticmethod
    def tupleFromDateTime(dateTime):
        """
        Convertit un objet date.DateTime de Task Coach en un tuple de date/heure.

        Le format du tuple est (jour, mois-1, année, heure, minute, seconde)
        pour être compatible avec wx.DateTimeFromDMY.

        Args:
            dateTime (date.DateTime): L'objet date.DateTime à convertir.

        Returns:
            tuple: Un tuple représentant la date et l'heure.
        """
        return (dateTime.day,  # Jour du mois.
                dateTime.month - 1,  # Mois (0-11 pour wxPython).
                dateTime.year,  # Année.
                dateTime.hour,  # Heure.
                dateTime.minute,  # Minute.
                dateTime.second)  # Seconde.

    @staticmethod
    def wxDateTime(dateTime, default):
        """
        Convertit un objet date.DateTime de Task Coach en un objet wx.DateTime.

        Si l'objet date.DateTime est un objet date.DateTime() par défaut (vide),
        alors les valeurs par défaut fournies sont utilisées.

        Args:
            dateTime (date.DateTime): L'objet date.DateTime à convertir.
            default (tuple): Un tuple de valeurs par défaut si dateTime est vide.

        Returns:
            wx.DateTime: L'objet wx.DateTime converti.
        """
        # Utilise les valeurs par défaut si dateTime est l'objet DateTime() par défaut (vide).
        args = default if dateTime == date.DateTime() else \
            (dateTime.day, dateTime.month - 1, dateTime.year,
             dateTime.hour, dateTime.minute, dateTime.second)
        # Crée un objet wx.DateTime à partir du tuple d'arguments.
        return wx.DateTimeFromDMY(*args)  # pylint: disable=W0142 # L'unpacking d'args est standard.

    @staticmethod
    def tcDateTime(dateTime):
        """
        Convertit un objet wx.DateTime en un objet date.DateTime de Task Coach.

        Args:
            dateTime (wx.DateTime): L'objet wx.DateTime à convertir.

        Returns:
            date.DateTime: L'objet date.DateTime converti.
        """
        # Crée un objet date.DateTime à partir des composants de wx.DateTime.
        # Note : Le mois de wx.DateTime est 0-indexé, donc on ajoute 1 pour Task Coach.
        return date.DateTime(dateTime.GetYear(),
                             dateTime.GetMonth() + 1,  # Ajustement du mois.
                             dateTime.GetDay(),
                             dateTime.GetHour(),
                             dateTime.GetMinute(),
                             dateTime.GetSecond())


class _CalendarSchedule(wxSchedule):
    """
    Représente une tâche de Task Coach comme un événement de calendrier pour wxScheduler.

    Cette classe hérite de wxSchedule et surcharge certaines méthodes
    pour adapter l'affichage d'une tâche (couleur, icônes, texte, barre de progression)
    aux capacités de rendu de wxScheduler.
    """

    def __init__(self, task):
        """
        Initialise un _CalendarSchedule à partir d'une tâche Task Coach.

        Args:
            task (Task): L'objet tâche Task Coach à représenter.
        """
        super().__init__()  # Appelle le constructeur de la classe parente wxSchedule.
        self.task = task  # Stocke la référence à la tâche associée.
        self.Bind(EVT_SCHEDULE_ACTIVATED, self.onActivated)  # Lie l'événement d'activation.

        # Initialise les propriétés d'affichage qui seront rendues par wxScheduler.
        self.description = None
        self.descriptionColor = None
        self.backgroundBrush = None
        self.icons = []
        self.complete = None
        self.tooltip = None  # Ajout d'un attribut pour la chaîne de l'info-bulle.

        # Renseigne les propriétés d'affichage.
        self.update()

    def update(self):
        """
        Met à jour les propriétés d'affichage de l'événement de calendrier
        basées sur l'état actuel de la tâche associée.

        Cette méthode est appelée pour rafraîchir l'apparence de l'événement
        lorsque la tâche change.
        """
        self.Freeze()  # Gèle les mises à jour visuelles pour des performances optimales.
        try:
            # Récupère le rendu HTML du sujet de la tâche.
            self.description = render.html(self.task.subject())
            # Définit la couleur de la description en fonction de l'état de la tâche.
            self.descriptionColor = wx.BLACK  # Couleur par défaut.
            if self.task.isOverdue():
                self.descriptionColor = wx.RED  # Rouge si la tâche est en retard.
            elif self.task.isCompleted():
                self.descriptionColor = wx.GREEN  # Vert si la tâche est complétée.

            # Définit la couleur de fond de l'événement.
            self.backgroundBrush = wx.Brush(wx.WHITE)  # Blanc par défaut.
            if self.task.isToday():
                # Si la tâche est pour aujourd'hui, utilise la couleur de surbrillance du système.
                self.backgroundBrush = wx.Brush(
                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
                )

            # Génère le texte de l'info-bulle pour la tâche.
            self.tooltip = tooltip.tooltip(self.task)

            self.icons = []  # Réinitialise la liste des icônes.
            # Ajoute des icônes en fonction des propriétés de la tâche.
            if self.task.recurs():
                self.icons.append("recurring_task_icon")  # Icône si la tâche est récurrente.
            if self.task.hasAttachment():
                self.icons.append("attachment_icon")  # Icône si la tâche a une pièce jointe.
            if self.task.notes():
                self.icons.append("note_icon")  # Icône si la tâche a des notes.

            # Calcule le pourcentage d'achèvement pour la barre de progression.
            if self.task.percentageComplete(recursive=True):
                # Si le pourcentage est 0, 'complete' reste None pour ne pas dessiner la barre.
                # old_div est pour Python 2, en Python 3 la division est flottante par défaut.
                # self.complete = old_div(1.0 * self.task.percentageComplete(recursive=True), 100)
                self.complete = (
                        1.0 * self.task.percentageComplete(recursive=True) / 100
                )  # Convertit en décimal (0.0 à 1.0).
            else:
                self.complete = None  # Pas de barre de progression si pas de pourcentage.
        finally:
            self.Thaw()  # Dégèle les mises à jour visuelles.

    # Les méthodes suivantes sont des méthodes statiques héritées ou utilitaires,
    # leur rôle est de convertir les formats de date/heure entre Task Coach et wxPython.
    @staticmethod
    def tupleFromDateTime(dateTime):
        """
        Convertit un objet date.DateTime de Task Coach en un tuple de date/heure
        compatible avec les constructeurs de wx.DateTime.

        Args:
            dateTime (date.DateTime): L'objet date.DateTime à convertir.

        Returns:
            tuple: Un tuple (jour, mois-1, année, heure, minute, seconde).
        """
        return (dateTime.day,
                dateTime.month - 1,  # wx.DateTime est 0-indexé pour le mois.
                dateTime.year,
                dateTime.hour,
                dateTime.minute,
                dateTime.second)

    @staticmethod
    def wxDateTime(dateTime, default):
        """
        Convertit un objet date.DateTime de Task Coach en un objet wx.DateTime.

        Si l'objet date.DateTime est l'objet par défaut (date.DateTime()),
        alors les valeurs par défaut fournies sont utilisées pour créer le wx.DateTime.

        Args:
            dateTime (date.DateTime): L'objet date.DateTime de Task Coach.
            default (tuple): Un tuple de valeurs par défaut (jour, mois-1, année, etc.)
                             si dateTime est l'objet date.DateTime() par défaut.

        Returns:
            wx.DateTime: L'objet wx.DateTime résultant.
        """
        # Utilise les valeurs par défaut si dateTime est l'objet DateTime() par défaut (vide).
        args = default if dateTime == date.DateTime() else \
            (_CalendarContentProvider.tupleFromDateTime(dateTime))  # Utilise la méthode statique pour obtenir le tuple.
        return wx.DateTimeFromDMY(*args)  # pylint: disable=W0142 # L'unpacking d'arguments est standard.

    @staticmethod
    def tcDateTime(dateTime):
        """
        Convertit un objet wx.DateTime en un objet date.DateTime de Task Coach.

        Args:
            dateTime (wx.DateTime): L'objet wx.DateTime à convertir.

        Returns:
            date.DateTime: L'objet date.DateTime de Task Coach.
        """
        return date.DateTime(dateTime.GetYear(),
                             dateTime.GetMonth() + 1,  # Ajustement car wx.DateTime est 0-indexé pour le mois.
                             dateTime.GetDay(),
                             dateTime.GetHour(),
                             dateTime.GetMinute(),
                             dateTime.GetSecond())


class CalendarWidget(wxScheduler):
    """
    Un widget wxPython qui affiche un calendrier des tâches.

    Ce widget intègre le composant wxScheduler et agit comme un contrôleur
    pour l'affichage et l'interaction avec les tâches dans une vue calendaire.
    Il gère les événements utilisateur (double-clic, clic droit, etc.),
    la mise à jour des paramètres du calendrier, et la synchronisation
    avec le fichier de tâches.
    """

    def __init__(self, parent, taskFile, settings, *args, **kwargs):
        """
        Initialise le widget de calendrier.

        Args:
            parent (wx.Window): La fenêtre parente du widget.
            taskFile: Le fichier de tâches actuel.
            settings: Les paramètres de l'application.
            *args: Arguments positionnels à passer au constructeur de wxScheduler.
            **kwargs: Arguments nommés à passer au constructeur de wxScheduler.
        """
        super().__init__(parent, *args, **kwargs)  # Appelle le constructeur de la classe parente wxScheduler.
        self._taskFile = taskFile  # Stocke la référence au fichier de tâches.
        self._settings = settings  # Stocke la référence aux paramètres.

        # Crée une instance du fournisseur de contenu pour les tâches.
        self._contentProvider = _CalendarContentProvider(settings, taskFile)
        # Définit le fournisseur de contenu pour wxScheduler.
        self.SetContentProvider(self._contentProvider)

        # Lie les événements de wxScheduler à leurs gestionnaires de méthode.
        self.Bind(EVT_SCHEDULE_ACTIVATED, self.onScheduleActivated)
        self.Bind(EVT_SCHEDULE_RIGHT_CLICK, self.onScheduleRightClick)
        self.Bind(EVT_SCHEDULE_DCLICK, self.onScheduleDoubleClick)
        self.Bind(EVT_PERIODWIDTH_CHANGED, self.onPeriodWidthChanged)

        # Lie les événements de changement de données du fichier de tâches.
        taskFile.AddObserver(self.onFileChanged)  # Lorsque le fichier de tâches change (ajout/suppression).
        taskFile.AddObserver(self.onTaskChanged, taskFile.EVT_ITEM_CHANGED)  # Lorsque des tâches individuelles changent.
        taskFile.AddObserver(self.onTaskAboutToBeDeleted, taskFile.EVT_ITEM_ABOUT_TO_BE_DELETED)  # Avant suppression de tâche.

        self._taskFile.addCommandHistoryObserver(self.onCommandExecuted)  # Observe l'historique des commandes.

        # Charge les paramètres initiaux du calendrier et les applique.
        self.loadSettings()
        # Active le glisser-déposer de tâches.
        draganddrop.DropTarget(self, self.onTaskDropped)

        # Définit le point de départ par défaut de la semaine (lundi ou dimanche).
        if self._settings.get("general", "weekstart") == "monday":
            self.SetWeekStart(wxSCHEDULER_WEEKSTART_MONDAY)
        else:
            self.SetWeekStart(wxSCHEDULER_WEEKSTART_SUNDAY)

    def loadSettings(self):
        """
        Charge les paramètres de configuration du calendrier depuis l'objet settings
        et les applique au widget wxScheduler.
        """
        # Récupère le nombre de périodes à afficher (ex: 7 pour une semaine).
        self.SetPeriodCount(
            self._settings.getint("calendar", "periodcount")
        )
        # Récupère le type de vue (journalière, hebdomadaire, mensuelle).
        self.SetViewType(
            self._settings.getint("calendar", "viewtype")
        )
        # Récupère l'orientation de la vue (horizontale ou verticale).
        self.SetViewOrientation(
            self._settings.getint("calendar", "vieworientation")
        )
        # Indique si la ligne de l'heure actuelle doit être affichée.
        self.ShowNow(
            self._settings.getboolean("calendar", "shownow")
        )
        # Récupère la couleur de surbrillance du jour actuel.
        hcolor = self._settings.get("calendar", "highlightcolor")
        if hcolor:  # Si une couleur est définie.
            # Convertit la chaîne "R, G, B" en un tuple d'entiers et crée un objet wx.Colour.
            color = wx.Colour(*tuple(map(int, hcolor.split(","))))
            self.SetHighlightColour(color)  # Applique la couleur de surbrillance.

    def onFileChanged(self, event):
        """
        Gère l'événement lorsque le fichier de tâches a changé (ajout/suppression d'éléments).

        Cette méthode déclenche un rafraîchissement complet du calendrier.

        Args:
            event (taskcoachlib.patterns.ObserverEvent): L'événement de changement de fichier.
        """
        self.RefreshAll()  # Rafraîchit l'intégralité du calendrier.

    def onTaskChanged(self, event):
        """
        Gère l'événement lorsqu'une tâche individuelle a été modifiée.

        Cette méthode met à jour l'objet wxSchedule correspondant à la tâche modifiée
        et rafraîchit le calendrier pour refléter ces changements.

        Args:
            event (taskcoachlib.patterns.ObserverEvent): L'événement de modification de tâche.
        """
        log.debug("onTaskChanged : %s", event.item)  # Log pour débogage.
        if isinstance(event.item, self._taskFile.taskClass()):  # S'assure que l'élément est bien une tâche.
            # Met à jour les propriétés du wxSchedule correspondant à la tâche.
            self._contentProvider.wxSchedule(event.item).update()
            self.RefreshAll()  # Rafraîchit l'intégralité du calendrier.

    def onTaskAboutToBeDeleted(self, event):
        """
        Gère l'événement juste avant qu'une tâche ne soit supprimée.

        Cette méthode supprime l'observateur de la tâche pour éviter les fuites de mémoire
        et rafraîchit le calendrier.

        Args:
            event (taskcoachlib.patterns.ObserverEvent): L'événement de suppression de tâche imminente.
        """
        if isinstance(event.item, self._taskFile.taskClass()):  # S'assure que l'élément est bien une tâche.
            # Supprime l'observateur de l'élément pour éviter les références mortes.
            self._taskFile.RemoveObserver(self.onTaskChanged, event.item, self._taskFile.EVT_ITEM_CHANGED)
            self._taskFile.RemoveObserver(self.onTaskAboutToBeDeleted, event.item, self._taskFile.EVT_ITEM_ABOUT_TO_BE_DELETED)
            self.RefreshAll()  # Rafraîchit l'intégralité du calendrier.

    def onScheduleActivated(self, event):
        """
        Gère l'événement lorsqu'un élément de calendrier (wxSchedule) est activé
        (par ex., sélectionné).

        Cette méthode sélectionne la tâche correspondante dans le fichier de tâches.

        Args:
            event (wx.Event): L'événement d'activation de wxSchedule.
        """
        log.debug("onScheduleActivated: %s", event.GetSchedule().GetClientData())  # Log pour débogage.
        # Sélectionne la tâche associée dans le fichier de tâches.
        self._taskFile.select(self._contentProvider.task(event.GetSchedule()))

    def onScheduleRightClick(self, event):
        """
        Gère l'événement de clic droit sur un élément de calendrier.

        Cette méthode sélectionne la tâche et affiche un menu contextuel.

        Args:
            event (wx.Event): L'événement de clic droit de wxSchedule.
        """
        # Sélectionne la tâche associée.
        self._taskFile.select(self._contentProvider.task(event.GetSchedule()))
        # Affiche le menu contextuel pour la tâche.
        self._taskFile.popupMenu(self._taskFile.selectedItems(), event=event)

    def onScheduleDoubleClick(self, event):
        """
        Gère l'événement de double-clic sur un élément de calendrier.

        Cette méthode édite la tâche correspondante.

        Args:
            event (wx.Event): L'événement de double-clic de wxSchedule.
        """
        # Exécute la commande d'édition pour la tâche.
        self._taskFile.commandHistory().Execute(
            command.Edit(self._taskFile.selectedItems(), self._taskFile)
        )

    def onPeriodWidthChanged(self, event):
        """
        Gère l'événement lorsque la largeur de la période affichée dans le calendrier change.

        Args:
            event (wx.Event): L'événement de changement de largeur de période.
        """
        # Pour l'instant, cette méthode est un placeholder et ne fait rien.
        pass

    def onCommandExecuted(self, event):
        """
        Gère l'événement lorsqu'une commande est exécutée.

        Cette méthode rafraîchit le calendrier après l'exécution d'une commande,
        ce qui peut avoir modifié les tâches.

        Args:
            event (taskcoachlib.patterns.ObserverEvent): L'événement d'exécution de commande.
        """
        self.RefreshAll()  # Rafraîchit l'intégralité du calendrier.

    def onTaskDropped(self, tasks):
        """
        Gère l'événement de glisser-déposer de tâches sur le calendrier.

        Args:
            tasks (list): Une liste d'objets tâches qui ont été déposées.
        """
        # Pour l'instant, cette méthode est un placeholder et ne fait rien.
        pass

    def update(self):
        """
        Met à jour le contenu du calendrier.

        Cette méthode est appelée pour forcer un rafraîchissement des données affichées.
        """
        self.RefreshAll()  # Rafraîchit l'intégralité du calendrier.