#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import wx
from itertools import chain
# from .wxSchedule import *
from .wxSchedule import wxSchedule, EVT_SCHEDULE_CHANGE
# from .wxSchedulerConstants import *
from .wxSchedulerConstants import (
    wxSCHEDULER_WEEKSTART_MONDAY,
    wxSCHEDULER_DAILY,
    wxSCHEDULER_WEEKLY,
    wxSCHEDULER_MONTHLY,
    wxSCHEDULER_TODAY,
    wxSCHEDULER_NEXT,
    wxSCHEDULER_PREV,
)
# from .wxSchedulerPaint import *
from .wxSchedulerPaint import wxSchedulerPaint
from . import wxScheduleUtils as Utils

log = logging.getLogger(__name__)

# if sys.version.startswith("2.3"):
# 	from sets import Set as set
# set() est intégré dans python 3


class InvalidSchedule(Exception):
    """
    Exception levée lorsqu'un objet planning (schedule) invalide est fourni.
    """
    def __init__(self, value):
        """
        Initialise l'exception avec la valeur donnée.
        :param value: Valeur décrivant l'erreur.
        """
        self.value = value

    def __str__(self):
        """
        Retourne la représentation textuelle de l'exception.
        """
        return repr(self.value)


class wxSchedulerCore(wxSchedulerPaint, wxSchedule):
    """
    Classe principale pour la gestion et l'affichage des plannings dans wxScheduler.

    Hérite des fonctionnalités de rendu et de gestion de planning de wxSchedulerPaint et de wxSchedule.
    """
    def __init__(self, *args, **kwds):
        # def __init__(self, parent=None, id=wx.ID_ANY,  *args, **kwds):
        """
        Initialise le cœur du planificateur avec les paramètres par défaut.
        Configure les heures de travail et autres paramètres initiaux.
        """
        log.debug(f"wxSchedulerCore.__init__ : reçoit args={args}, kwargs={kwds}")
        log.debug(f"wxSchedulerCore.__init__ : avant super args={args}, kwargs={kwds}")
        super().__init__(*args, **kwds)
        # super().__init__(parent, id, *args, **kwds)
        self._viewType = None
        self._currentDate = wx.DateTime.Now()
        self._weekstart = wxSCHEDULER_WEEKSTART_MONDAY
        kwds.pop('style', None)  # retirer style non utilisé

        self._showOnlyWorkHour = True
        self._dc = None

        self._schedules = []
        self._schBind = []
        self._periodCount = 1

        # Internal (extenal?) init values
        self._startingHour = wx.DateTime().Now()
        self._endingHour = wx.DateTime().Now()
        self._startingPauseHour = wx.DateTime().Now()
        self._endingPauseHour = wx.DateTime().Now()

        self._startingHour.SetHour(8)
        self._startingHour.SetMinute(00)

        self._endingHour.SetHour(18)
        self._endingHour.SetMinute(00)

        self._startingPauseHour.SetHour(13)
        self._startingPauseHour.SetMinute(00)

        self._endingPauseHour.SetHour(14)
        self._endingPauseHour.SetMinute(00)

        self._calculateWorkHour()
        wxSchedulerCore.SetViewType(self)
        log.info("wxSchedulerCore initialisé !")

    # -----------------------
    #   Internal methods
    # -----------------------

    def _calculateWorkHour(self):
        """
        Calcule les heures de travail à afficher.
        TODO : À améliorer pour une gestion plus précise.
        """

        # Update the current Date according to
        for idate in (
            self._startingHour,
            self._startingPauseHour,
            self._endingPauseHour,
            self._endingPauseHour,
        ):
            idate = Utils.copyDate(self._currentDate)  # ? A revoir

        # Create the list
        self._lstDisplayedHours = []
        if self._showOnlyWorkHour:
            morningWorkTime = range(
                self._startingHour.GetHour(), self._startingPauseHour.GetHour()
            )
            afternoonWorkTime = range(
                self._endingPauseHour.GetHour(), self._endingHour.GetHour()
            )
            # rangeWorkHour = morningWorkTime + afternoonWorkTime
            rangeWorkHour = chain(morningWorkTime, afternoonWorkTime)
            # ou
            # rangeWorkHour = list(chain(morningWorkTime, afternoonWorkTime))

        else:
            # Show all the hours
            rangeWorkHour = range(
                self._startingHour.GetHour(), self._endingHour.GetHour()
            )

        for H in rangeWorkHour:
            for M in (0, 30):
                hour = wx.DateTime().Now()
                hour = Utils.copyDate(self._currentDate)
                hour.SetHour(H)
                hour.SetMinute(M)
                self._lstDisplayedHours.append(hour)

    def _calcRightDateOnMove(self, side):
        """
        Calcule la date correcte lors du déplacement (avant/arrière) dans la période.
        :param side: Indique si on avance ou recule dans la période.
        """
        offset = wx.DateSpan(days=1)  # Initialisation de l'offset
        if self._viewType == wxSCHEDULER_DAILY:
            offset = wx.DateSpan(days=1)
        elif self._viewType == wxSCHEDULER_WEEKLY:
            offset = wx.DateSpan(weeks=1)
        elif self._viewType == wxSCHEDULER_MONTHLY:
            # daysAdd = self._currentDate.GetNumberOfDaysInMonth(
            #     self._currentDate.GetMonth()
            # )
            daysAdd = self._currentDate.GetNumberOfDays(
                self._currentDate.GetMonth()
            )
            offset = wx.DateSpan(months=1)

        if side == wxSCHEDULER_NEXT:
            # self._currentDate.AddDS(offset)
            self._currentDate += offset
        elif side == wxSCHEDULER_PREV:
            # self._currentDate.SubtractDS(offset)
            self._currentDate -= offset

    # -----------------------
    #  External methods
    # -----------------------

    def Add(self, schedules):
        """
        Ajoute un ou plusieurs plannings à la liste pour visualisation.
        Rafraîchit l'affichage si au moins un planning est dans la plage visible.

        :param schedules: Objet wxSchedule ou liste/tuple de wxSchedule.
        """
        # Add schedules in list for visualization. Default is empty list
        # Call automatically Refresh() if at least one schedule is in range of
        # current visualization
        if isinstance(schedules, wxSchedule):
            self._schedules.append(schedules)

        elif isinstance(schedules, (list, tuple)):
            # Control the schedule(s) passed
            for sc in schedules:
                if not isinstance(sc, wxSchedule):
                    raise InvalidSchedule("Not a valid schedule")

                self._schedules.append(sc)

        else:
            raise ValueError("Invalid value passed")

        self.Refresh()

    def Delete(self, index):
        """Delete schedule in specified position or that specific wxSchedule
        Unbind also the event
        """
        if isinstance(index, int):
            schedule = self._schedules.pop(index)
        elif isinstance(index, wxSchedule):
            # Remove the schedule from our list
            self._schedules.remove(index)
            schedule = index
        else:
            raise ValueError("Passme only int or wxSchedule istances")

        # Remove from our bind list and unbind the event
        self._schBind.remove(schedule)
        schedule.Unbind(EVT_SCHEDULE_CHANGE)

        # Without that the object is never actually freed
        schedule.Destroy()

        self.Refresh()

    def DeleteAll(self):
        """
        Supprime tous les plannings.
        Gèle l'affichage pendant l'opération pour éviter les clignotements.
        """
        self.Freeze()  # dans wxScheduler ou plutôt wxSchedule ?
        try:
            while len(self._schedules) > 0:
                self.Delete(0)
        finally:
            self.Thaw()  # dans wxScheduler ou plutôt wxSchedule ?
            # self.Refresh()

    def GetDate(self):
        """
        Retourne la date courante affichée.
        Si la vue n'est pas journalière, retourne le premier jour de la période.
        :return: wx.DateTime de la date affichée.
        """
        return Utils.copyDateTime(self._currentDate)

    def GetDc(self):
        """
        Retourne le contexte graphique (DC) courant utilisé pour l'affichage.
        :return: Objet DC courant.
        """
        return self._dc

    def GetSchedules(self):
        """
        Retourne la liste des plannings dans la plage de jours affichée.
        Utile pour le rendu.
        :return: Liste des plannings affichés.
        """
        # Returns schedules in current days range. Useful for retrieve schedules
        # in rendering mode
        return self._schedules

    def GetShowWorkHour(self):
        """
        Indique si seules les heures de travail sont affichées.
        :return: Booléen indiquant le mode d'affichage.
        """
        return self._showOnlyWorkHour

    def GetViewType(self):
        """
        Retourne le type de vue courant (journalier, hebdomadaire, mensuel, etc.).
        :return: Type de vue.
        """
        return self._viewType

    def GetWeekdayDate(self, weekday, day):
        """
        Retourne la date correspondant au jour de la semaine donné dans la même semaine.
        :param weekday: Jour de la semaine (0 à 6).
        :param day: wx.DateTime de référence.
        :return: wx.DateTime du jour demandé.
        """
        if weekday == 6:
            weekday = 0
        else:
            weekday += 1

        date = day.GetWeekDayInSameWeek(weekday, self._weekstart)

        return Utils.copyDateTime(date)

    def IsInRange(self, date=None, schedule=None):
        """
        Indique si la date ou le planning spécifié se trouve dans la plage visible actuelle.
        :param date: wx.DateTime à vérifier.
        :param schedule: wxSchedule à vérifier.
        :return: Booléen.
        """

        # Make the control
        if not (date or schedule) or not (
            isinstance(date, (wx.DateTime, wxSchedule))
            or isinstance(schedule, wxSchedule)
        ):
            raise ValueError("Pass me at least one value")

        # Do a bad, but very useful hack that leave the developer pass an schedule at the first parameter
        if isinstance(date, wxSchedule):
            schedule = date
            date = None

        # Create two new dates
        start = wx.DateTime.Now()
        end = wx.DateTime.Now()

        # Set the right, starting, parameters

        for DT, getPar in zip((start, end), (self._startingHour, self._endingHour)):
            DT.SetYear(self._currentDate.GetYear())
            DT.SetMonth(self._currentDate.GetMonth())
            DT.SetDay(self._currentDate.GetDay())
            DT.SetHour(getPar.GetHour())
            DT.SetMinute(getPar.GetMinute())

        # Nothing to do
        if self._viewType == wxSCHEDULER_DAILY:
            pass
        # Set the right week
        elif self._viewType == wxSCHEDULER_WEEKLY:
            start = self.GetWeekdayDate(0, start)
            end = self.GetWeekdayDate(6, end)
        # End the end day
        elif self._viewType == wxSCHEDULER_MONTHLY:
            start.SetDay(1)
            # end.SetDay(wx.DateTime.GetNumberOfDaysInMonth(end.GetMonth()))
            end.SetDay(wx.DateTime.GetNumberOfDays(end.GetMonth()))
        else:
            print("Why I'm here?")
            return

        # Make the control
        if date:
            return date.IsBetween(start, end)
        else:
            return start.IsEarlierThan(schedule.start) and end.IsLaterThan(schedule.end)

    def Next(self, steps=1):
        """
        Passe à la période suivante (jour, semaine ou mois) selon la vue courante.
        :param steps: Nombre de périodes à avancer.
        """
        self.Freeze()
        try:
            for step in range(steps):
                self.SetViewType(wxSCHEDULER_NEXT)
        finally:
            self.Thaw()

    def Previous(self, steps=1):
        """
        Revient à la période précédente selon la vue courante.
        :param steps: Nombre de périodes à reculer.
        """
        self.Freeze()
        try:
            for step in range(steps):
                self.SetViewType(wxSCHEDULER_PREV)
        finally:
            self.Thaw()

    def SetDate(self, date=None):
        """
        Définit la date courante affichée. Par défaut, utilise la date du jour.
        :param date: wx.DateTime à afficher.
        """
        # Go to the Date. Default is Today.
        if date is None:
            date = wx.DateTime.Now()
        self._currentDate = date
        self._calculateWorkHour()
        self.Refresh()

    def SetDc(self, dc=None):
        """
        Définit un contexte graphique utilisateur personnalisé (DC).
        Si aucun argument n'est fourni, utilise wx.PaintDC lors de OnPaint().
        :param dc: Objet DC à utiliser.
        """
        self._dc = dc

    def SetShowWorkHour(self, value):
        """
        Active ou désactive l'affichage des seules heures de travail.
        :param value: Booléen ou entier.
        """
        if not isinstance(value, (bool, int)):
            raise ValueError("Passme a bool at SetShowWorkHour")

        self._showOnlyWorkHour = value
        self._calculateWorkHour()
        self.InvalidateMinSize()
        self.Refresh()

    def SetDrawHeaders(self, doDraw=True):
        """
        Active ou désactive l'affichage des en-têtes de jours (numéros de date) dans le calendrier.

        :param doDraw: booléen, True pour afficher les dates, False pour les masquer.
        """
        self._drawHeaders = bool(doDraw)
        self.Refresh()  # Redessine le calendrier

    def SetViewType(self, view=None):
        """
        Définit le type de visualisation (journalier, hebdomadaire, mensuel, etc.).
        Par défaut, utilise la vue journalière.
        :param view: Type de vue à utiliser.
        """
        if view is None:
            view = wxSCHEDULER_DAILY

        if view not in (
            wxSCHEDULER_DAILY,
            wxSCHEDULER_WEEKLY,
            wxSCHEDULER_MONTHLY,
            wxSCHEDULER_TODAY,
            wxSCHEDULER_PREV,
            wxSCHEDULER_NEXT,
        ):
            raise ValueError("Pass me a valid view value")

        if view in (wxSCHEDULER_TODAY, wxSCHEDULER_NEXT, wxSCHEDULER_PREV):
            if view == wxSCHEDULER_TODAY:
                self._currentDate = wx.DateTime.Now()
            else:
                self._calcRightDateOnMove(view)
            view = self._viewType

        self._viewType = view
        self._calculateWorkHour()

    def SetWeekStart(self, weekstart):
        """
        Définit le jour de début de semaine (lundi ou dimanche).
        Par défaut, la semaine commence le lundi.
        :param weekstart: Jour de début de la semaine.
        """
        self._weekstart = weekstart
        self.Refresh()

    def GetWeekStart(self):
        """
        Retourne le jour où commence la semaine (lundi ou dimanche).
        :return: Jour de début de la semaine.
        """
        return self._weekstart

    def SetWorkHours(self, start, stop):
        """
        Définit l'heure de début et de fin de la journée de travail.
        :param start: Heure de début.
        :param stop: Heure de fin.
        """
        self._startingHour.SetHour(max(0, start))
        self._endingHour.SetHour(min(23, stop))
        self._calculateWorkHour()
        self.InvalidateMinSize()
        self.Refresh()

    def SetPeriodCount(self, count):
        """
        Définit le nombre de périodes à afficher.
        :param count: Nombre de périodes.
        """
        self._periodCount = count
        self.InvalidateMinSize()
        self.Refresh()

    def GetPeriodCount(self):
        """
        Retourne le nombre de périodes affichées.
        :return: Nombre de périodes.
        """
        return self._periodCount
