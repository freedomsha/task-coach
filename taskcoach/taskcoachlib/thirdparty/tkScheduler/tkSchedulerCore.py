#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module tkSchedulerCore
======================

Ce module est le cœur du composant de planification pour Tkinter. Il a été
converti depuis la version wxPython (wxSchedulerCore.py).

Rôle principal :
- Orchestrer l'affichage des plannings (en utilisant tkSchedulerPaint).
- Gérer les données des plannings (objets tkSchedule).
- Répondre aux actions de l'utilisateur (navigation, ajout/suppression).
- Maintenir l'état courant (date affichée, type de vue).

Il ne s'agit plus d'un widget, mais d'une classe de contrôle qui opère sur
un widget Canvas de Tkinter.
"""
# La logique de la conversion
#
#     Héritage et Initialisation : La nouvelle classe tkSchedulerCore hérite de tkSchedulerPaint (pour le dessin) et de tkSchedule (pour la logique de base d'un événement). Son initialisation est un peu différente : au lieu d'être un widget elle-même, elle gère un widget Canvas de Tkinter. C'est pourquoi son __init__ prend maintenant un canvas en argument.
#
#     Remplacement de wx.DateTime : C'est le changement le plus important. Toutes les instances de wx.DateTime sont remplacées par l'objet datetime standard de Python. De même, wx.DateSpan est remplacé par timedelta. Heureusement, le fichier tkScheduleUtils.py que tu as fourni contient déjà les fonctions d'aide nécessaires.
#
#     Gestion des Événements : Le système d'événements de wxPython (EVT_SCHEDULE_CHANGE, Bind, Unbind) est remplacé par le système de callbacks simple que nous avons défini dans tkSchedule.py.
#
#     Simplification des Méthodes d'UI : Les fonctions spécifiques à wxPython comme Freeze(), Thaw() (pour éviter le scintillement) et Refresh() sont conservées, mais leur implémentation est adaptée. Freeze/Thaw utilisent un simple drapeau pour empêcher les redessins multiples, et Refresh appelle la méthode de dessin de tkSchedulerPaint. Les concepts comme le Device Context (GetDc, SetDc) n'existent pas en Tkinter et ont été supprimés.

import logging
from datetime import datetime, timedelta
from itertools import chain
import calendar

# --- Imports des modules Tkinter convertis ---
from .tkSchedule import tkSchedule, EVT_SCHEDULE_CHANGE
from .tkSchedulerConstants import (
    SCHEDULER_WEEKSTART_MONDAY,
    SCHEDULER_DAILY,
    SCHEDULER_WEEKLY,
    SCHEDULER_MONTHLY,
    SCHEDULER_TODAY,
    SCHEDULER_NEXT,
    SCHEDULER_PREV,
)
from .tkSchedulerPaint import tkSchedulerPaint
from . import tkScheduleUtils as Utils

log = logging.getLogger(__name__)


class InvalidSchedule(Exception):
    """
    Exception levée lorsqu'un objet planning (schedule) invalide est fourni.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class tkSchedulerCore(tkSchedulerPaint, tkSchedule):
    """
    Classe principale pour la gestion et l'affichage des plannings.

    Hérite de tkSchedulerPaint pour le rendu et de tkSchedule pour les
    fonctionnalités de base des événements.
    """
    def __init__(self, canvas, *args, **kwds):
        """
        Initialise le cœur du planificateur.

        Args:
            canvas (tk.Canvas): Le widget canevas sur lequel tout sera dessiné.
        """
        log.debug(f"tkSchedulerCore.__init__ : reçoit args={args}, kwargs={kwds}")
        # L'appel super() initialise les classes parentes, notamment tkSchedulerPaint
        # en lui passant le canevas.
        super().__init__(canvas=canvas, *args, **kwds)

        self._viewType = None
        self._currentDate = datetime.now()
        self._weekstart = SCHEDULER_WEEKSTART_MONDAY

        self._showOnlyWorkHour = True
        self._freeze_level = 0  # Pour gérer Freeze/Thaw

        self._schedules = []
        self._periodCount = 1

        # --- Heures de travail par défaut ---
        now = datetime.now()
        self._startingHour = now.replace(hour=8, minute=0, second=0, microsecond=0)
        self._endingHour = now.replace(hour=18, minute=0, second=0, microsecond=0)
        self._startingPauseHour = now.replace(hour=13, minute=0, second=0, microsecond=0)
        self._endingPauseHour = now.replace(hour=14, minute=0, second=0, microsecond=0)

        self._calculateWorkHour()
        self.SetViewType()  # Applique la vue par défaut (journalière)
        log.info("tkSchedulerCore initialisé !")

    # -----------------------
    #   Méthodes internes
    # -----------------------

    def _calculateWorkHour(self):
        """
        Calcule la liste des heures à afficher dans la grille horaire.
        """
        # Crée la liste des heures affichées (par tranches de 30 min)
        self._lstDisplayedHours = []

        if self._showOnlyWorkHour:
            # Concatène les heures du matin et de l'après-midi
            morning_hours = range(self._startingHour.hour, self._startingPauseHour.hour)
            afternoon_hours = range(self._endingPauseHour.hour, self._endingHour.hour)
            hour_range = chain(morning_hours, afternoon_hours)
        else:
            # Affiche toutes les heures de la journée de travail
            hour_range = range(self._startingHour.hour, self._endingHour.hour)

        now = datetime.now()
        for h in hour_range:
            for m in (0, 30):
                # Crée un objet datetime pour chaque tranche horaire
                hour_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                self._lstDisplayedHours.append(hour_dt)

    def _calcRightDateOnMove(self, side):
        """
        Calcule la date suivante ou précédente en fonction de la vue actuelle.

        Args:
            side (int): SCHEDULER_NEXT ou SCHEDULER_PREV.
        """
        offset = timedelta(days=1)  # Par défaut pour la vue journalière
        if self._viewType == SCHEDULER_DAILY:
            offset = timedelta(days=self._periodCount)
        elif self._viewType == SCHEDULER_WEEKLY:
            offset = timedelta(weeks=self._periodCount)
        elif self._viewType == SCHEDULER_MONTHLY:
            # Pour le mois, on avance de mois en mois
            # Le calcul exact se fait en ajoutant/soustrayant les mois
            new_month = self._currentDate.month + (1 if side == SCHEDULER_NEXT else -1)
            new_year = self._currentDate.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            elif new_month < 1:
                new_month = 12
                new_year -= 1

            # Gère le cas où le jour n'existe pas dans le nouveau mois (ex: 31 Avril)
            last_day_of_new_month = calendar.monthrange(new_year, new_month)[1]
            new_day = min(self._currentDate.day, last_day_of_new_month)

            self._currentDate = self._currentDate.replace(year=new_year, month=new_month, day=new_day)
            return

        if side == SCHEDULER_NEXT:
            self._currentDate += offset
        elif side == SCHEDULER_PREV:
            self._currentDate -= offset

    # -----------------------
    #  Méthodes publiques
    # -----------------------

    def Add(self, schedules):
        """
        Ajoute un ou plusieurs plannings à la liste pour visualisation.

        Args:
            schedules (tkSchedule or list/tuple): Le ou les plannings à ajouter.
        """
        if isinstance(schedules, tkSchedule):
            self._schedules.append(schedules)
        elif isinstance(schedules, (list, tuple)):
            for sc in schedules:
                if not isinstance(sc, tkSchedule):
                    raise InvalidSchedule("L'objet fourni n'est pas un tkSchedule valide.")
                self._schedules.append(sc)
        else:
            raise ValueError("La valeur passée est invalide. Fournissez un tkSchedule ou une liste.")

        self.Refresh()

    def Delete(self, schedule_or_index):
        """
        Supprime un planning à une position donnée ou un objet tkSchedule spécifique.

        Args:
            schedule_or_index (int or tkSchedule): L'index ou l'objet à supprimer.
        """
        schedule_to_delete = None
        if isinstance(schedule_or_index, int):
            schedule_to_delete = self._schedules.pop(schedule_or_index)
        elif isinstance(schedule_or_index, tkSchedule):
            self._schedules.remove(schedule_or_index)
            schedule_to_delete = schedule_or_index
        else:
            raise ValueError("Passez un entier (index) ou une instance de tkSchedule.")

        # Note : La gestion Unbind/Destroy de wxPython est supprimée.
        # En Python, la suppression de la liste suffit si aucune autre référence
        # n'existe sur l'objet.

        self.Refresh()

    def DeleteAll(self):
        """Supprime tous les plannings."""
        self.Freeze()
        try:
            self._schedules.clear()
        finally:
            self.Thaw()
        self.Refresh()

    def GetDate(self):
        """Retourne la date courante affichée."""
        return Utils.copyDateTime(self._currentDate)

    def GetSchedules(self):
        """Retourne la liste complète des plannings."""
        return self._schedules

    def GetShowWorkHour(self):
        """Retourne True si seules les heures de travail sont affichées."""
        return self._showOnlyWorkHour

    def GetViewType(self):
        """Retourne le type de vue courant (journalier, hebdomadaire, etc.)."""
        return self._viewType

    def IsInRange(self, date=None, schedule=None):
        """
        Vérifie si une date ou un planning est dans la plage de dates visible.

        Args:
            date (datetime, optional): La date à vérifier.
            schedule (tkSchedule, optional): Le planning à vérifier.

        Returns:
            bool: True si dans la plage visible, sinon False.
        """
        if not (date or schedule):
            raise ValueError("Veuillez me passer au moins une date ou un planning.")

        if isinstance(date, tkSchedule):
            schedule = date
            date = None

        # Calcule les dates de début et de fin de la vue actuelle
        start_view = self._currentDate.replace(hour=0, minute=0, second=0)

        if self._viewType == SCHEDULER_DAILY:
            end_view = start_view + timedelta(days=self._periodCount)
        elif self._viewType == SCHEDULER_WEEKLY:
            start_view = Utils.setToWeekDayInSameWeek(start_view, 0, self._weekstart)
            end_view = start_view + timedelta(weeks=self._periodCount)
        elif self._viewType == SCHEDULER_MONTHLY:
            start_view = start_view.replace(day=1)
            # Calcule la fin du mois
            _, days_in_month = calendar.monthrange(start_view.year, start_view.month)
            end_view = start_view + timedelta(days=days_in_month)
        else:
            return False

        # Effectue la comparaison
        if date:
            return start_view <= date < end_view
        if schedule:
            return schedule.start < end_view and schedule.end > start_view

        return False

    def Next(self, steps=1):
        """Passe à la période suivante (jour, semaine, mois)."""
        self.Freeze()
        try:
            for _ in range(steps):
                self._calcRightDateOnMove(SCHEDULER_NEXT)
        finally:
            self.Thaw()
        self.Refresh()

    def Previous(self, steps=1):
        """Revient à la période précédente."""
        self.Freeze()
        try:
            for _ in range(steps):
                self._calcRightDateOnMove(SCHEDULER_PREV)
        finally:
            self.Thaw()
        self.Refresh()

    def Freeze(self):
        """Empêche le redessin du canevas."""
        self._freeze_level += 1

    def Thaw(self):
        """Autorise à nouveau le redessin du canevas."""
        self._freeze_level = max(0, self._freeze_level - 1)
        if self._freeze_level == 0:
            self.Refresh()

    def Refresh(self):
        """
        Rafraîchit l'affichage. Appelle la méthode de dessin de tkSchedulerPaint.
        Le dessin n'a lieu que si le composant n'est pas "gelé".
        """
        if self._freeze_level == 0:
            super().Refresh()

    def SetDate(self, date=None):
        """
        Définit la date courante. Si None, utilise la date d'aujourd'hui.
        """
        if date is None:
            date = datetime.now()
        self._currentDate = date
        self._calculateWorkHour()
        self.Refresh()

    def SetShowWorkHour(self, value):
        """Active/désactive l'affichage des seules heures de travail."""
        if not isinstance(value, (bool, int)):
            raise ValueError("Veuillez passer une valeur booléenne (True/False).")

        self._showOnlyWorkHour = bool(value)
        self._calculateWorkHour()
        self.Refresh()

    def SetDrawHeaders(self, doDraw=True):
        """Active ou désactive l'affichage des en-têtes."""
        self._drawHeaders = bool(doDraw)
        self.Refresh()

    def SetViewType(self, view=None):
        """Définit le type de vue (journalier, hebdomadaire, etc.)."""
        if view is None:
            view = SCHEDULER_DAILY

        if view not in (
                SCHEDULER_DAILY, SCHEDULER_WEEKLY, SCHEDULER_MONTHLY,
                SCHEDULER_TODAY, SCHEDULER_PREV, SCHEDULER_NEXT
        ):
            raise ValueError("Type de vue invalide.")

        if view == SCHEDULER_TODAY:
            self._currentDate = datetime.now()
            # Conserve le type de vue précédent (ex: si on était en vue semaine, on reste en semaine)
            if self._viewType is None:
                self._viewType = SCHEDULER_DAILY
        elif view in (SCHEDULER_NEXT, SCHEDULER_PREV):
            self._calcRightDateOnMove(view)
        else:
            self._viewType = view

        self._calculateWorkHour()
        self.Refresh()

    def SetWeekStart(self, weekstart):
        """Définit le jour de début de semaine (Lundi ou Dimanche)."""
        self._weekstart = weekstart
        self.Refresh()

    def GetWeekStart(self):
        """Retourne le jour de début de semaine."""
        return self._weekstart

    def SetWorkHours(self, start_hour, end_hour):
        """Définit les heures de début et de fin de la journée de travail."""
        self._startingHour = self._startingHour.replace(hour=max(0, start_hour))
        self._endingHour = self._endingHour.replace(hour=min(23, end_hour))
        self._calculateWorkHour()
        self.Refresh()

    def SetPeriodCount(self, count):
        """Définit le nombre de périodes à afficher (ex: 2 jours, 3 semaines)."""
        self._periodCount = max(1, count)
        self.Refresh()

    def GetPeriodCount(self):
        """Retourne le nombre de périodes affichées."""
        return self._periodCount