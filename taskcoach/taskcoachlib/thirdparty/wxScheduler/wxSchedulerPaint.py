#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from typing import Any, Tuple
from .wxSchedule import wxSchedule
from .wxDrawer import wxBaseDrawer, wxFancyDrawer
from .wxSchedulerConstants import (
    wxSCHEDULER_VERTICAL,
    wxSCHEDULER_HORIZONTAL,
    DAY_BACKGROUND_BRUSH,
    DAY_SIZE_MIN,
    LEFT_COLUMN_SIZE,
    MONTH_CELL_SIZE_MIN,
    SCHEDULE_INSIDE_MARGIN,
    SCHEDULER_BACKGROUND_BRUSH,
    SCHEDULE_OUTSIDE_MARGIN,
    FOREGROUND_PEN,
    WEEK_SIZE_MIN,
    wxSCHEDULER_DAILY,
    wxSCHEDULER_WEEKLY,
    wxSCHEDULER_MONTHLY,
)

# from .wxSchedulerCore import *
# from .wxSchedulerCore import InvalidSchedule, wxSchedulerCore
import calendar

# from wx.adv import CalendarCtrl  # pour ProcessEvent ?
import math
import sys
import wx

# from wx.core import *
from . import wxScheduleUtils as Utils
from .wxScheduleUtils import copyDateTime

log = logging.getLogger(__name__)

# if sys.version.startswith( "2.3" ):
# 	from sets import Set as set
# set() est intégré dans python 3
xrange = range

# Events
wxEVT_COMMAND_SCHEDULE_ACTIVATED = wx.NewEventType()
EVT_SCHEDULE_ACTIVATED = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_ACTIVATED)

wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK = wx.NewEventType()
EVT_SCHEDULE_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK)

wxEVT_COMMAND_SCHEDULE_DCLICK = wx.NewEventType()
EVT_SCHEDULE_DCLICK = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_DCLICK)

wxEVT_COMMAND_PERIODWIDTH_CHANGED = wx.NewEventType()
EVT_PERIODWIDTH_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_PERIODWIDTH_CHANGED)


# class wxSchedulerSizer(wx.PySizer):  # PySizer deprecated , use Sizer instead
class wxSchedulerSizer(wx.Sizer):
    """
    Sizer personnalisé pour le planificateur, permettant de calculer
    dynamiquement la taille minimale grâce à un callback.
    """

    def __init__(self, minSizeCallback):
        """
        Initialise le sizer avec une fonction de rappel pour la taille minimale.
        :param minSizeCallback: Fonction retournant la taille minimale actuelle.
        """
        super().__init__()
        self._minSizeCallback = minSizeCallback

    def CalcMin(self):
        """
        Calcule et retourne la taille minimale à utiliser pour le sizer.
        :return: Taille minimale (wx.Size)
        """
        # Méthode indispensable requise par wx.Sizer.
        return self._minSizeCallback()

    def RecalcSizes(self):
        """
        Dispose et dimensionne les enfants du panel intérieur du panneau
        en fonction de la direction et du décalage de la flèche.
        Doit être implémentée pour tout sizer custom wxPython.
        """
        # Méthode indispensable requise par wx.Sizer.
        # Si tu n’as qu’un enfant, on le positionne plein cadre
        # window = self.GetContainingWindow()
        if self.GetChildren():
            child = self.GetChildren()[0]
            # size = window.GetClientSize()  # Utiliser plutôt GetVirtualSize pour déterminer la taille du bitmap
            size = self.GetSize()
            # # Positionne et redimensionne tous les enfants
            for child in self.GetChildren():
                if child.IsShown():
                    child.SetDimension((0, 0), size)
            # child.SetDimension((0, 0), size)


# Main class
class wxSchedulerPaint(object):
    """
    Classe principale responsable de la gestion du rendu graphique du planificateur (scheduler).

    Gère l'affichage, le dessin, l'interaction avec les événements souris et le redimensionnement.

    Utilisée comme mixin dans wxSchedulerCore.

    Il a un rôle de moteur de rendu.
    """

    def __init__(self, *args, **kwds):
        # def __init__(self, parent=None, id=wx.ID_ANY, *args, **kwds):
        """
        Initialise les paramètres graphiques, les états d'interaction et les options de rendu du planificateur.
        """
        log.debug(
            f"wxSchedulerPaint.__init__ : avant super args={args}, kwargs={kwds}"
        )
        # Indique à l'analyseur que ces attributs existent dans wxSchedulerCore :
        self._lstDisplayedHours: Any | Tuple
        _lstDisplayedHours: Any | Tuple
        self._periodCount: Any
        self._schedules: Any
        self._viewType: Any
        self._showOnlyWorkHour: Any
        # kwds.pop('style', None)  # Retirer style non utilisé
        super().__init__(*args, **kwds)

        # super().__init__(parent, id, *args, **kwds)
        # super().__init__(*args, style=style, **kwds)
        # Le bug : tu passes style dans **kwds à une classe qui ne l’accepte pas.
        # wxPython attend le paramètre style en tant qu’argument positionnel,
        # pas dans **kwds.
        # Il faut donc que toutes les classes de la hiérarchie transmettent
        # style en positionnel.
        # Donc :
        #     Modifie la signature de chaque classe héritée de wx.Panel
        #     (wxSchedule, wxScheduler, etc.) pour inclure style=... et
        #     le transmettre en positionnel à super().__init__.
        # Le fix propre : mets style explicitement dans la signature de chaque init,
        # et transmets-le à wx.Panel en argument positionnel.

        # def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
        #              style=wx.TAB_TRAVERSAL | wx.FULL_REPAINT_ON_RESIZE, name="wxSchedule"):
        #     super().__init__(parent, id, pos, size, style, name)

        self._resizable = False
        self._style = wxSCHEDULER_VERTICAL

        self._drawerClass = wxBaseDrawer
        self._headerPanel = None

        self._schedulesCoords = list()
        self._schedulesPages = dict()

        self._datetimeCoords = []

        self._bitmap = None
        self._minSize = None
        self._drawHeaders = True
        self._guardRedraw = False

        self._periodWidth = 150
        self._headerBounds = []
        self._headerCursorState = 0
        self._headerDragOrigin = None
        self._headerDragBase = None

        # State:
        # 0 None
        # 1 Clicked, waiting for release or drag
        # 2 Dragging
        # 3 hovering up/left edge
        # 4 hovering down/right edge
        # 5 dragging up/left edige
        # 6 dragging down/right edge

        self._scheduleDraggingState = 0
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None
        self._scheduleDraggingStick = False

        # The highlight colour is too dark
        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self._highlightColor = wx.Colour(
            int((color.Red() + 255) / 2),
            int((color.Green() + 255) / 2),
            int((color.Blue() + 255) / 2),
        )

        self.pageNumber = None
        self.pageCount = 1

        if isinstance(self, wx.ScrolledWindow):
            self.SetSizer(wxSchedulerSizer(self.CalcMinSize))
            # self.SetSizer(wxSchedulerSizer(self.CalcMin))
        log.info("wxSchedulerPaint initialisé !")

    def _doClickControl(self, point, shiftDown=False):
        """
        Gère le clic de souris sur le planificateur (sélection, début de déplacement/redimensionnement d'un planning).
        :param point: Position du clic (wx.Point)
        :param shiftDown: Indique si la touche Shift était enfoncée
        """
        if self._scheduleDraggingState in [3, 4]:
            self._scheduleDraggingState += 2
            self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
            self._scheduleDraggingStick = shiftDown
        else:
            try:
                pMin, pMax, sch = self._findSchedule(point)
            except TypeError:  # returned None
                return
            if isinstance(sch, wxSchedule):
                self._scheduleDragged = pMin, pMax, sch
                self._scheduleDraggingState = 1
                self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
                self._scheduleDraggingStick = shiftDown
            else:
                self._processEvt(wxEVT_COMMAND_SCHEDULE_ACTIVATED, point)

    def _doEndClickControl(self, point):
        """
        Gère la fin du clic (relâchement souris) sur le planificateur, finalise le déplacement ou le redimensionnement.
        :param point (point): Position du relâchement
        """
        if self._scheduleDraggingState == 1:
            self._processEvt(wxEVT_COMMAND_SCHEDULE_ACTIVATED, point)
        elif self._scheduleDraggingState == 2:
            _, dateTime = self._computeCoords(point, 0, 0)

            sched = self._scheduleDragged[2]
            self._drawDragging(None, self._computeAllCoords)
            sched.Offset(dateTime.Subtract(self._scheduleDraggingOrigin[1]))
            self._scheduleDraggingState = 0

        elif self._scheduleDraggingState in [5, 6]:
            coords = {5: self._computeStartCoords, 6: self._computeEndCoords}[
                self._scheduleDraggingState
            ]
            _, _, dateTime = coords(point)

            sched = self._scheduleDragged[2]
            if self._scheduleDraggingState == 5:
                sched.SetStart(Utils.copyDateTime(dateTime))
            else:
                sched.SetEnd(Utils.copyDateTime(dateTime))

            self._scheduleDraggingState = 0
            self._drawDragging(None, coords)
            self.SetCursor(
                wx.STANDARD_CURSOR
            )  # Utilisable avec wxScheduler et Windows!

        self._scheduleDraggingState = 0
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None

    def _doMove(self, point):
        """
        Gère le déplacement de la souris sur le planificateur, met à jour l'état de survol/déplacement/redimensionnement.
        :param point: Position actuelle de la souris
        """
        if self._scheduleDraggingState in [0, 3, 4]:
            for sched, pointMin, pointMax in self._schedulesCoords:
                if self._style == wxSCHEDULER_VERTICAL:
                    if pointMin.x < point.x < pointMax.x:
                        if abs(point.y - pointMin.y) < 4:
                            self._scheduleDraggingState = 3
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                        if abs(point.y - pointMax.y) < 4:
                            self._scheduleDraggingState = 4
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                else:
                    if pointMin.y < point.y < pointMax.y:
                        if abs(point.x - pointMin.x) < 4:
                            self._scheduleDraggingState = 3
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return
                        if abs(point.x - pointMax.x) < 4:
                            self._scheduleDraggingState = 4
                            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
                            self._scheduleDragged = (
                                pointMin,
                                pointMax,
                                sched.GetClientData(),
                            )
                            return

            if self._scheduleDraggingState in [3, 4]:
                self._scheduleDraggingState = 0
                self.SetCursor(
                    wx.STANDARD_CURSOR
                )  # de Scrolled.ScrolledPanel utilisé dans wxScheduler
                # self.SetCursor(wx.StockCursor(wx.STANDARD_CURSOR))  # de Scrolled.ScrolledPanel utilisé dans wxScheduler
                self._scheduleDragged = None
        elif self._scheduleDraggingState in [5, 6]:
            self._drawDragging(
                point,
                {5: self._computeStartCoords, 6: self._computeEndCoords}[
                    self._scheduleDraggingState
                ],
            )
        elif self._scheduleDraggingState == 1:
            dx = abs(self._scheduleDraggingOrigin[0].x - point.x)
            dy = abs(self._scheduleDraggingOrigin[0].y - point.y)
            if dx >= wx.SystemSettings.GetMetric(
                wx.SYS_DRAG_X
            ) or dy >= wx.SystemSettings.GetMetric(wx.SYS_DRAG_Y):
                self._scheduleDraggingState = 2
                self._drawDragging(point, self._computeAllCoords)
        elif self._scheduleDraggingState == 2:
            self._drawDragging(point, self._computeAllCoords)

    def _computeCoords(self, point, dx, dy):
        """
        Calcule les coordonnées ajustées dans le planificateur en fonction du déplacement.
        :param point: Position du point de base
        :param dx: Décalage en X
        :param dy: Décalage en Y
        :return: (wx.Point, wx.DateTime) coordonnées et heure correspondante
        """
        log.debug(
            f"wxSchedulzePaint._computeCoords: Calcule des coordonnées à partir du point ({point.x}, {point.y}), décalé de dx={dx} et dy={dy}"
        )
        pp = wx.Point(point.x + dx, point.y + dy)
        if pp.y < 0:
            pp.y = 0
        if pp.y >= self._bitmap.GetHeight():
            pp.y = self._bitmap.GetHeight() - 1
        if pp.x < 0:
            pp.x = 0
        if pp.x >= self._bitmap.GetWidth():
            pp.x = self._bitmap.GetWidth() - 1

        # dt, pointMin, pointMax = 0, 0, 0
        for idx, (dt, pointMin, pointMax) in enumerate(self._datetimeCoords):
            if (
                pointMin.y <= pp.y <= pointMax.y
                and pointMin.x <= pp.x <= pointMax.x
            ):
                break
        else:
            idx = -1

        if idx >= 0:
            if self._scheduleDraggingStick:
                if self._style == wxSCHEDULER_VERTICAL:
                    pp = wx.Point(pp.x, pointMin.y)
                else:
                    pp = wx.Point(pointMin.x, pp.y)

            theTime = Utils.copyDateTime(dt)
            if self._style == wxSCHEDULER_VERTICAL:
                # theTime.AddTS(
                #     wx.TimeSpan.Minutes(
                #         int(30.0 * (pp.y - pointMin.y) / (pointMax.y - pointMin.y))
                #     )
                # )
                # ou :
                # theTime.Add(
                #     wx.TimeSpan.Minutes(
                #         int(30.0 * (pp.y - pointMin.y) / (pointMax.y - pointMin.y))
                #     )
                # )
                theTime += wx.TimeSpan.Minutes(
                    30.0 * (pp.y - pointMin.y) / (pointMax.y - pointMin.y)
                )
            else:
                # theTime.AddTS(
                #     wx.TimeSpan.Minutes(
                #         int(30.0 * (pp.x - pointMin.x) / (pointMax.x - pointMin.x))
                #     )
                # )
                # ou :
                # theTime.Add(
                #     wx.TimeSpan.Minutes(
                #         int(30.0 * (pp.x - pointMin.x) / (pointMax.x - pointMin.x))
                #     )
                # )
                theTime += wx.TimeSpan.Minutes(
                    30.0 * (pp.x - pointMin.x) / (pointMax.x - pointMin.x)
                )
        else:
            raise ValueError("Not found: %d %d" % (pp.x, pp.y))

        log.debug(
            f"wxSchedulerPaint._computeCoords : renvoie pp=({pp.x}, {pp.y}), theTime={theTime}."
        )
        return pp, theTime

    def _computeAllCoords(self, point):
        """
        Calcule les nouvelles coordonnées pour un planning lors d'un déplacement complet.
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """

        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        rMin, theTime = self._computeCoords(pMin, dx, dy)
        rMax = wx.Point(rMin.x + pMax.x - pMin.x, rMin.y + pMax.y - pMin.y)

        return rMin, rMax, theTime

    def _computeStartCoords(self, point):
        """
        Calcule les coordonnées lors du redimensionnement du début d'un planning (gauche/haut).
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """
        log.debug(
            f"wxSchedulerPaint._computeStartCoords : Lancé par self={self} avec point({point.x}, {point.y})."
        )
        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        if self._style == wxSCHEDULER_VERTICAL:
            x = self._scheduleDraggingOrigin[0].x
            y = pMin.y
        else:
            x = pMin.x
            y = self._scheduleDraggingOrigin[0].y

        rMin, theTime = self._computeCoords(wx.Point(x, y), dx, dy)
        rMax = pMax

        if self._style == wxSCHEDULER_VERTICAL:
            rMin.x = pMin.x
        else:
            rMin.y = pMin.y

        log.debug(
            f"wxSchedulerPaint._computeStartCoords : Retourne rMin={rMin}, rMax={rMax}, theTime={theTime}."
        )
        return rMin, rMax, theTime

    def _computeEndCoords(self, point):
        """
        Calcule les coordonnées lors du redimensionnement de la fin d'un planning (droite/bas).
        :param point: Position de la souris
        :return: Tuple (rMin, rMax, theTime)
        """
        log.debug(
            f"wxSchedulerPaint._computeEndCoords : Lancé par self={self} avec point({point.x}, {point.y})."
        )
        pMin, pMax, sch = self._scheduleDragged

        dx = point.x - self._scheduleDraggingOrigin[0].x
        dy = point.y - self._scheduleDraggingOrigin[0].y

        rMin = pMin
        rMax, theTime = self._computeCoords(pMax, dx, dy)

        firstTime = self._lstDisplayedHours[0]
        lastTime = self._lstDisplayedHours[-1]

        if (
            theTime.GetHour() == firstTime.GetHour()
            and theTime.GetMinute() == firstTime.GetMinute()
        ):
            # theTime.SubtractTS(wx.TimeSpan.Days(1))
            theTime -= wx.TimeSpan.Days(1)
            theTime.SetHour(lastTime.GetHour() + 1)
            theTime.SetMinute(0)

        log.debug(
            f"wxSchedulerPaint._computeEndCoords : Retourne rMin={rMin}, rMax={rMax}, theTime={theTime}."
        )
        return rMin, rMax, theTime

    def _drawDragging(self, point, coords):
        """
        Dessine le planning pendant une opération de déplacement ou de redimensionnement.
        :param point: Position courante de la souris
        :param coords: Fonction de calcul des coordonnées à utiliser
        """
        # Remarque
        #
        # Pendant que wx.ClientDC peut également être utilisé
        # pour dessiner sur la zone client d’une fenêtre
        # à partir de l’extérieur d’un gestionnaire EVT_PAINT()
        # dans certains ports, cela ne fonctionne pas sur toutes les plates-formes
        # (ni wxOSX ni wxGTK avec GTK 3 Wayland backend ne le supportent,
        # donc dessiner en utilisant wx.ClientDC n’a tout simplement aucun effet là-bas)
        # et la seule façon portable de dessiner est via wx.PaintDC.
        # Pour redessiner une petite partie de la fenêtre,
        # utilisez wx.Window.RefreshRect pour invalider uniquement cette partie
        # et vérifier wx.Window.GetUpdateRegion dans le gestionnaire d’événements
        # paint pour redessiner cette partie uniquement.
        log.info(
            "wxSchedulerPaint._drawDragging : Dessine le planning pendant une opération de déplacement ou de redimensionnement."
        )
        if self._scheduleDraggingPrevious is not None:
            x, y = (
                self.GetViewStart()
            )  # Soit de ScrolledWindowBase, soit deScrolledCanvas, dePropertyGrid ou de Scrolled ?
            mx, my = (
                self.GetScrollPixelsPerUnit()
            )  # Soit de ScrolledWindowBase, soit deScrolledCanvas, dePropertyGrid ou de Scrolled ?
            x *= mx
            y *= my
            rMin, rMax, _ = coords(self._scheduleDraggingPrevious)
            self.RefreshRect(  # De Window !
                wx.Rect(
                    rMin.x - x, rMin.y - y, rMax.x - rMin.x, rMax.y - rMin.y
                )
            )
            try:
                wx.Yield()
            except:
                pass

        self._scheduleDraggingPrevious = point

        if point is not None:
            rMin, rMax, _ = coords(point)

            # TODO : A VERIFIER !
            dc = wx.ClientDC(self)
            # dc = wx.PaintDC(self)  # A la place ?
            self.PrepareDC(
                dc
            )  # Plus besoin de preparer avec DC ? Si, Soit de ScrolledWindowBase, soit deScrolledCanvas, dePropertyGrid ou de Scrolled ?
            # self.DoPrepareDC(dc)  # Plus besoin de preparer avec DC ? Si, Soit de ScrolledWindowBase, soit deScrolledCanvas, dePropertyGrid ou de Scrolled ?
            dc.SetBrush(wx.Brush(self._scheduleDragged[2].GetColor()))
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawRoundedRectangle(
                rMin.x, rMin.y, rMax.x - rMin.x, rMax.y - rMin.y, 5
            )
        log.info(
            "wxSchedulerPaint._drawDragging : A fini de redessiner le planning après le déplacement."
        )

    def _doRightClickControl(self, point):
        """
        Gère le clic droit sur le planificateur (affiche le menu contextuel ou équivalent).
        :param point: Position du clic droit
        """
        self._processEvt(wxEVT_COMMAND_SCHEDULE_RIGHT_CLICK, point)

    def _doDClickControl(self, point):
        """
        Gère le double-clic sur le planificateur (édition rapide ou autre action).
        :param point: Position du double-clic
        """
        self._processEvt(wxEVT_COMMAND_SCHEDULE_DCLICK, point)

    def _findSchedule(self, point):
        """
        Vérifie si le point donné se trouve sur un planning et retourne ce planning avec ses coordonnées.
        :param point: Position à tester
        :return: (pointMin, pointMax, schedule) ou (pointMin, pointMax, date)
        """
        for schedule, pointMin, pointMax in self._schedulesCoords:
            inX = (pointMin.x <= point.x) & (point.x <= pointMax.x)
            inY = (pointMin.y <= point.y) & (point.y <= pointMax.y)

            if inX & inY:
                return pointMin, pointMax, schedule.GetClientData()

        for dt, pointMin, pointMax in self._datetimeCoords:
            inX = (pointMin.x <= point.x) & (point.x <= pointMax.x)
            inY = (pointMin.y <= point.y) & (point.y <= pointMax.y)

            if inX & inY:
                return pointMin, pointMax, dt

    @staticmethod
    def _getSchedInPeriod(schedules, start, end):
        """
        Retourne la liste des plannings qui intersectent la période définie par 'start' et 'end'.
        Les dates de début/fin sont ajustées à la plage si nécessaire.
        :param schedules: Liste de plannings
        :param start: Date de début
        :param end: Date de fin
        :return: Liste de plannings ajustés
        """
        results = []

        for schedule in schedules:
            try:
                schedule.bounds = None

                if schedule.start.IsLaterThan(end) or schedule.start.IsEqualTo(
                    end
                ):
                    continue
                if start.IsLaterThan(schedule.end):
                    continue

                newSchedule = schedule.Clone()
                # This is used to find the original schedule object in _findSchedule.
                newSchedule.clientdata = schedule

                if start.IsLaterThan(schedule.start):
                    newSchedule.start = Utils.copyDateTime(start)
                if schedule.end.IsLaterThan(end):
                    newSchedule.end = Utils.copyDateTime(end)

                results.append(newSchedule)
            # except wx.PyDeadObjectError:
            except RuntimeError:
                pass

        return results

    # _getSchedInPeriod = staticmethod(_getSchedInPeriod)

    def _splitSchedules(self, schedules):
        """
        Sépare les plannings en groupes qui ne se chevauchent pas mutuellement.
        :param schedules: Liste de plannings
        :return: Liste de listes de plannings non chevauchants
        """
        results = []
        current = []

        schedules = schedules[:]  # Don't alter original list

        def findNext(schedule):
            # Among schedules that start after this one ends, find the "nearest".
            candidateSchedule = None
            minDelta = None
            for sched in schedules:
                if sched.start.IsLaterThan(
                    schedule.end
                ) or sched.start.IsEqualTo(schedule.end):
                    delta = sched.start.Subtract(schedule.end)
                    if minDelta is None or minDelta > delta:
                        minDelta = delta
                        candidateSchedule = sched
            return candidateSchedule

        while schedules:
            schedule = schedules[0]
            while schedule:
                current.append(schedule)
                schedules.remove(schedule)
                schedule = findNext(schedule)
            results.append(current)
            current = []

        return results

    def _paintPeriod(
        self, drawer, start, daysCount, x, y, width, height, highlight=None
    ):
        """
        Effectue le rendu des plannings pour une période donnée (jour/semaine/mois).
        :param drawer: Objet de dessin
        :param start: Date de début
        :param daysCount: Nombre de jours à afficher
        :param x: Position X
        :param y: Position Y
        :param width: Largeur d'affichage
        :param height: Hauteur d'affichage
        :param highlight: Couleur de surbrillance optionnelle
        :return: Dimensions réelles utilisées (width, height)
        """
        log.debug(
            f"wxShcedulerPaint._paintPeriod : lancé avec drawer={drawer}, start={start}, daysCount={daysCount}, x={x}, y={y}, width={width}, height={height}, highlight={highlight}"
        )
        end = Utils.copyDateTime(start)
        # end.AddDS(wx.DateSpan(days=daysCount))
        # try:
        #     end.AddSpan(wx.DateSpan(days=daysCount))
        # except Exception:
        end += wx.DateSpan(days=daysCount)

        blocks = self._splitSchedules(
            self._getSchedInPeriod(
                self._schedules, start, end
            )  # _schedules défini dans wxSchedulerCore !
        )
        offsetY = 0

        if (
            self._showOnlyWorkHour
        ):  # _showOnlyWorkHour définit dans wxSchedulerCore
            workingHours = [
                (self._startingHour, self._startingPauseHour),
                (self._endingPauseHour, self._endingHour),
            ]
        else:
            workingHours = [(self._startingHour, self._endingHour)]

        if not self.pageNumber:
            self.pageCount = 1
            self.pageLimits = [0]

            pageHeight = self.GetSize().GetHeight() - 20
            currentPageHeight = y

        for dayN in xrange(daysCount):
            theDay = Utils.copyDateTime(start)
            # theDay.AddDS(wx.DateSpan(days=dayN))
            # try:
            #     theDay.AddSpan(wx.DateSpan(days=dayN))
            # except Exception:
            theDay += wx.DateSpan(days=dayN)
            theDay.SetSecond(0)
            color = highlight
            if theDay.IsSameDate(wx.DateTime.Now()):
                if self._viewType != wxSCHEDULER_DAILY or daysCount >= 2:
                    color = self._highlightColor
            drawer.DrawDayBackground(
                x + 1.0 * width / daysCount * dayN,
                y,
                1.0 * width / daysCount,
                height,
                highlight=color,
            )

        if blocks:
            dayWidth = width / len(blocks)

            for idx, block in enumerate(blocks):
                maxDY = 0

                for schedule in block:
                    show = True
                    if self.pageNumber is not None:
                        if (
                            self._schedulesPages.get(schedule.GetId(), None)
                            != self.pageNumber
                        ):
                            show = False

                    if show:
                        if self._style == wxSCHEDULER_VERTICAL:
                            xx, yy, w, h = drawer.DrawScheduleVertical(
                                schedule,
                                start,
                                workingHours,
                                x + dayWidth * idx,
                                y,
                                dayWidth,
                                height,
                            )
                        elif self._style == wxSCHEDULER_HORIZONTAL:
                            xx, yy, w, h = drawer.DrawScheduleHorizontal(
                                schedule,
                                start,
                                daysCount,
                                workingHours,
                                x,
                                y + offsetY,
                                width,
                                height,
                            )
                            maxDY = max(maxDY, h)

                        if self.pageNumber is None:
                            if currentPageHeight + h >= pageHeight:
                                pageNo = self.pageCount + 1
                            else:
                                pageNo = self.pageCount

                            self._schedulesPages[schedule.GetId()] = pageNo

                        self._schedulesCoords.append(
                            (
                                schedule,
                                wx.Point(xx, yy),
                                wx.Point(xx + w, yy + h),
                            )
                        )
                    else:
                        schedule.Destroy()

                offsetY += maxDY

                if not self.pageNumber:
                    currentPageHeight += maxDY
                    if currentPageHeight >= pageHeight:
                        self.pageLimits.append(currentPageHeight - maxDY)
                        currentPageHeight = maxDY
                        self.pageCount += 1

        now = wx.DateTime.Now()

        for dayN in xrange(daysCount):
            theDay = Utils.copyDateTime(start)
            # theDay.AddDS(wx.DateSpan(days=dayN))
            # try:
            #     theDay.AddDS(wx.DateSpan(days=dayN))
            # except Exception:
            theDay += wx.DateSpan(days=dayN)
            theDay.SetSecond(0)

            nbHours = len(self._lstDisplayedHours)

            for idx, hour in enumerate(self._lstDisplayedHours):
                theDay.SetHour(hour.GetHour())
                theDay.SetMinute(hour.GetMinute())

                if self._minSize is None or not self._resizable:
                    if self._style == wxSCHEDULER_VERTICAL:
                        self._datetimeCoords.append(
                            (
                                Utils.copyDateTime(theDay),
                                wx.Point(
                                    int(x + 1.0 * width * dayN / daysCount),
                                    int(y + 1.0 * height * idx / nbHours),
                                ),
                                wx.Point(
                                    int(
                                        x
                                        + 1.0 * width * (dayN + 1) / daysCount
                                    ),
                                    int(
                                        y + 1.0 * height * (idx + 1) / nbHours
                                    ),
                                ),
                            )
                        )
                    else:
                        self._datetimeCoords.append(
                            (
                                Utils.copyDateTime(theDay),
                                wx.Point(
                                    int(
                                        x
                                        + 1.0
                                        * width
                                        * (nbHours * dayN + idx)
                                        / (nbHours * daysCount)
                                    ),
                                    int(y),
                                ),
                                wx.Point(
                                    int(
                                        x
                                        + 1.0
                                        * width
                                        * (nbHours * dayN + idx + 1)
                                        / (nbHours * daysCount)
                                    ),
                                    int(y + height),
                                ),
                            )
                        )

        if isinstance(self, wx.ScrolledWindow) and self._showNow:
            now = wx.DateTime.Now()
            # This assumes self._lstDisplayedHours is sorted of course
            for dayN in xrange(daysCount):
                theDay = Utils.copyDateTime(start)
                # theDay.AddDS(wx.DateSpan(days=dayN))
                theDay += wx.DateSpan(days=dayN)
                if theDay.IsSameDate(now):
                    theDay.SetSecond(0)
                    previous = None
                    for idx, hour in enumerate(self._lstDisplayedHours):
                        theDay.SetHour(hour.GetHour())
                        theDay.SetMinute(hour.GetMinute())
                        if theDay.IsLaterThan(now):
                            if idx != 0:
                                if self._style == wxSCHEDULER_VERTICAL:
                                    yPrev = (
                                        y + 1.0 * height * (idx - 1) / nbHours
                                    )
                                    delta = (
                                        1.0
                                        * height
                                        / nbHours
                                        * now.Subtract(previous).GetSeconds()
                                        / theDay.Subtract(
                                            previous
                                        ).GetSeconds()
                                    )
                                    drawer.DrawNowHorizontal(
                                        x, yPrev + delta, width
                                    )
                                else:
                                    xPrev = x + 1.0 * width * (
                                        nbHours * dayN + idx - 1
                                    ) / (nbHours * daysCount)
                                    delta = (
                                        1.0
                                        * width
                                        / (nbHours * daysCount)
                                        * now.Subtract(previous).GetSeconds()
                                        / theDay.Subtract(
                                            previous
                                        ).GetSeconds()
                                    )
                                    drawer.DrawNowVertical(
                                        xPrev + delta, y, height
                                    )
                            break
                        previous = Utils.copyDateTime(theDay)
                    break

        # self.Refresh()

        if self._style == wxSCHEDULER_VERTICAL:
            return max(width, DAY_SIZE_MIN.width), max(
                height, DAY_SIZE_MIN.height
            )
        else:
            return max(width, self._periodWidth), offsetY

    def _paintDay(self, drawer, day, x, y, width, height):
        """
        Dessine les plannings d'une journée dans la colonne correspondante.
        :param drawer: Objet de dessin
        :param day: Date du jour à afficher
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        log.debug(
            f"wxSchedulerPaint._paintDay : Lancé avec drawer={drawer}, day={day}, x={x}, y={y}, width={width}, height={height}"
        )
        start = Utils.copyDateTime(day)
        start.SetHour(0)
        start.SetMinute(0)
        start.SetSecond(0)

        color = None
        if day.IsSameDate(wx.DateTime.Now()) and self._periodCount >= 2:
            color = self._highlightColor

        # self.Refresh()

        # Renvoie le rendu des plannings pour une période donnée (jour/semaine/mois).
        log.debug(f"wxShcedulerPaint._paintDay : Renvoie self._paintPeriod()")
        return self._paintPeriod(
            drawer, start, 1, x, y, width, height, highlight=color
        )

    def _paintDailyHeaders(
        self, drawer, day, x, y, width, height, includeText=True
    ):
        """
        Dessine les en-têtes de la vue journalière.

        Appellé par _paintDaily().
        Appelle DrawDayHeader(day, x, y, ...), qui est censé dessiner la date.
        Mais la méthode ne fait rien si includeText=False ou si _drawHeaders est désactivé.

        :param drawer: Objet de dessin
        :param day: Date du jour
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :param includeText: Affiche le texte de la date si vrai
        :return: Largeur et hauteur occupées
        """
        log.debug(
            "wxScheduler._paintDailyHeaders: pour _draHeaders:%s day:%s includeText:%s avec %s",
            self._drawHeaders,
            day,
            includeText,
            drawer,
        )
        # x = int(x)
        # y = int(y)
        # width = int(width)
        # height = int(height)
        if self._style == wxSCHEDULER_HORIZONTAL:
            self._headerBounds.append((x, y, height))

        if includeText:
            color = None
            if day.IsSameDate(wx.DateTime.Now()):
                if (
                    self._viewType != wxSCHEDULER_DAILY
                    or self._periodCount >= 2
                ):
                    color = self._highlightColor
            w, h = drawer.DrawDayHeader(
                day, x, y, width, height, highlight=color
            )  # Il faut que ce soit de HeaderDrawerMixin(HeaderDrawerDCMixin)
        else:
            w, h = width, 0

        if not (self._style == wxSCHEDULER_VERTICAL or self._drawHeaders):
            hw, hh = drawer.DrawHours(
                x,
                y + h,
                width,
                height - h,
                self._style,
                includeText=includeText,
            )
            h += hh

        if w is None or not isinstance(w, (int, float)):
            w = width
        if h is None or not isinstance(h, (int, float)):
            h = 0
            # h = 1

        # w = max(1, int(w))
        # # h = max(0, int(h))
        # h = max(1, int(h))

        # self.Refresh()

        log.debug(
            f"wxSchedulerPaint._paintDailyHeaders a w={w}, h={h} avant retour."
        )
        return w, h
        # return max(1, int(w)), max(0, int(h))
        # return max(1, int(w)), max(1, int(h))

    def _paintDaily(self, drawer, day, x, y, width, height):
        """
        Affiche les plannings de la journée (vue journalière, éventuellement multi-jours).

        Appellé par DoPaint().
        _paintDailyHeaders() est appelé si _drawHeaders est vrai.

        :param drawer: Objet de dessin
        :param day: Date de départ
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        log.debug(
            f"wxSchedulerPaint._paintDaily : Affiche les plannings de la journée avec drawer={drawer}, day={day}, x={x}, y={y}, width={width}, height={height}."
        )
        # Dans le contexte wxPython Phoenix, il est crucial d’avoir
        # des dimensions toujours > 0 et de type int.
        minWidth = minHeight = 0

        if self._style == wxSCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        theDay = Utils.copyDateTime(day)

        if self._drawHeaders:
            maxDY = 0
            for idx in xrange(self._periodCount):
                w, h = self._paintDailyHeaders(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    # int(x + float(width) / self._periodCount * idx),
                    y,
                    1.0 * width / self._periodCount,
                    # int(float(width) / self._periodCount),
                    height,
                )
                maxDY = max(maxDY, h)
                # theDay.AddDS(wx.DateSpan(days=1))
                # try:
                #     theDay.AddSpan(wx.DateSpan(days=1))
                # except Exception:
                theDay += wx.DateSpan(days=1)
            minHeight += maxDY
            y += maxDY
            height -= maxDY
        else:
            for idx in xrange(self._periodCount):
                self._paintDailyHeaders(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    # int(x + float(width) / self._periodCount * idx),
                    y,
                    1.0 * width / self._periodCount,
                    # int(float(width) / self._periodCount),
                    height,
                    includeText=False,
                )
                # theDay.AddDS(wx.DateSpan(days=1))
                theDay += wx.DateSpan(days=1)

        if self._style == wxSCHEDULER_VERTICAL:
            x -= LEFT_COLUMN_SIZE
            width += LEFT_COLUMN_SIZE

        if self._style == wxSCHEDULER_VERTICAL or self._drawHeaders:
            if self._style == wxSCHEDULER_VERTICAL:
                w, h = drawer.DrawHours(x, y, width, height, self._style)
            else:
                maxDY = 0
                for idx in xrange(self._periodCount):
                    _, h = drawer.DrawHours(
                        x + 1.0 * width / self._periodCount * idx,
                        # int(x + float(width) / self._periodCount * idx),
                        y,
                        1.0 * width / self._periodCount,
                        # int(float(width) / self._periodCount),
                        height,
                        self._style,
                    )
                    maxDY = max(maxDY, h)
                w = 0
                h = maxDY
        else:
            w, h = 0, 0

        if self._style == wxSCHEDULER_VERTICAL:
            minWidth += w
            x += w
            width -= w
        else:
            minHeight += h
            y += h
            height -= h

        if self._style == wxSCHEDULER_HORIZONTAL:
            # Use directly paintPeriod or pagination fails
            w, h = self._paintPeriod(
                drawer, day, self._periodCount, x, y, width, height
            )
        else:
            w = 0
            maxDY = 0
            theDay = Utils.copyDateTime(day)
            for idx in xrange(self._periodCount):
                dw, dh = self._paintDay(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    # int(x + float(width) / self._periodCount * idx),
                    y,
                    1.0 * width / self._periodCount,
                    # int(float(width) / self._periodCount),
                    height,
                )
                w += dw
                maxDY = max(maxDY, dh)
                # theDay.AddDS(wx.DateSpan(days=1))
                theDay += wx.DateSpan(days=1)

        minWidth += w
        minHeight += h

        # self.Refresh()

        # Toujours retourner des entiers strictement positifs
        log.debug(
            f"wxSchedulerPaint._paintDaily : retourne minWidth={minWidth}, minHeight={minHeight}."
        )
        return minWidth, minHeight
        # return max(1, int(minWidth)), max(1, int(minHeight))

    def _paintWeeklyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes des jours pour la vue hebdomadaire.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :return: Hauteur occupée
        """
        log.debug(
            "wxScheduler._paintWeeklyHeaders: pour _drawHeaders:%s day:%s x=%s y=%s width=%s height=%s avec %s",
            self._drawHeaders,
            day,
            x,
            y,
            width,
            height,
            drawer,
        )
        firstDay = Utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        firstDay.SetHour(0)
        firstDay.SetMinute(0)
        firstDay.SetSecond(0)

        maxDY = 0

        for weekday in xrange(7):
            theDay = Utils.setToWeekDayInSameWeek(
                Utils.copyDateTime(firstDay), weekday, self._weekstart
            )
            if theDay.IsSameDate(wx.DateTime.Now()):
                color = self._highlightColor
            else:
                color = None
            w, h = drawer.DrawDayHeader(
                theDay,
                int(x + weekday * 1.0 * width / 7),
                int(y),
                int(1.0 * width / 7),
                int(height),
                highlight=color,
            )
            self._headerBounds.append(
                (int(x + (weekday + 1) * 1.0 * width / 7), int(y), int(height))
            )
            maxDY = max(maxDY, h)

        # self.Refresh()
        log.debug(
            f"wxSchedulerPaint._paintWeeklyHeaders retourne maxDY={maxDY}"
        )
        return maxDY

    def _paintWeekly(self, drawer, day, x, y, width, height):
        """
        Dessine les plannings de la semaine courante.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        log.debug(
            f"wxSchedulerPaint._paintWeekly : Affiche les plannings de la semaine courante avec drawer={drawer}, day={day}, x={x}, y={y}, width={width}, height={height}."
        )
        firstDay = Utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        firstDay.SetHour(0)
        firstDay.SetMinute(0)
        firstDay.SetSecond(0)

        minWidth = minHeight = 0

        if self._style == wxSCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        maxDY = 0

        if self._drawHeaders:
            theDay = Utils.copyDateTime(day)
            for idx in xrange(self._periodCount):
                maxDY = max(
                    maxDY,
                    self._paintWeeklyHeaders(
                        drawer,
                        theDay,
                        int(x + 1.0 * width / self._periodCount * idx),
                        int(y),
                        int(1.0 * width / self._periodCount),
                        int(height),
                    ),
                )
                # theDay.AddDS(wx.DateSpan(weeks=1))
                theDay += wx.DateSpan(weeks=1)

        if self._style == wxSCHEDULER_VERTICAL:
            x -= LEFT_COLUMN_SIZE
            width += LEFT_COLUMN_SIZE

        minHeight += maxDY
        y += maxDY
        height -= maxDY

        if self._style == wxSCHEDULER_VERTICAL:
            w, h = drawer.DrawHours(
                int(x), int(y), int(width), int(height), self._style
            )

            minWidth += w
            x += w
            width -= w

            day = Utils.copyDateTime(firstDay)

            for idx in xrange(self._periodCount):
                for weekday in xrange(7):
                    theDay = Utils.setToWeekDayInSameWeek(
                        Utils.copyDateTime(day), weekday, self._weekstart
                    )
                    self._paintDay(
                        drawer,
                        theDay,
                        # x + (weekday + 7 * idx) * 1.0 * width / 7 / self._periodCount),
                        int(
                            x
                            + float(weekday + 7 * idx)
                            * width
                            / 7
                            / self._periodCount
                        ),
                        int(y),
                        # 1.0 * width / 7 / self._periodCount,
                        int(float(width) / 7 / self._periodCount),
                        int(height),
                    )
                # day.AddDS(wx.DateSpan(weeks=1))
                day += wx.DateSpan(weeks=1)

            # self.Refresh()

            return max(
                WEEK_SIZE_MIN.width * self._periodCount + LEFT_COLUMN_SIZE,
                width,
            ), max(WEEK_SIZE_MIN.height, height)
        else:
            w, h = self._paintPeriod(
                drawer,
                firstDay,
                7 * self._periodCount,
                int(x),
                int(y),
                int(width),
                int(height),
            )

            minWidth += w
            minHeight += h

            # self.Refresh()

            log.debug(
                f"wxSchedulerPaint._paintWeekly a minWidth={minWidth}, minHeight={minHeight} avant retour."
            )
            return (
                max(
                    self._periodWidth * self._periodCount + LEFT_COLUMN_SIZE,
                    minWidth,
                ),
                max(0, minHeight),
            )

    def _paintMonthlyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes pour la vue mensuelle.
        :param drawer: Objet de dessin
        :param day: Date de référence
        :param x, y, width, height: Dimensions de la zone d'en-tête
        :return: Largeur et hauteur occupées
        """
        log.debug(
            "wxScheduler._paintMonthlyHeaders: pour _drawHeaders:%s day:%s x=%s y=%s width=%s height=%s avec %s",
            self._drawHeaders,
            day,
            x,
            y,
            width,
            height,
            drawer,
        )
        if isinstance(self, wx.ScrolledWindow):
            _, h = drawer.DrawMonthHeader(
                day, 0, 0, self.GetSizeTuple()[0], height
            )
            # _, h = int(
            #     drawer.DrawMonthHeader(day, 0, 0, int(self.GetSize()[0]), int(height))
            # )
            w = width
        else:
            w, h = drawer.DrawMonthHeader(
                day, int(x), int(y), int(width), int(height)
            )

        if self._style == wxSCHEDULER_HORIZONTAL:
            day.SetDay(1)
            day.SetHour(0)
            day.SetMinute(0)
            day.SetSecond(0)

            # daysCount = wx.DateTime.GetNumberOfDaysInMonth(day.GetMonth())
            daysCount = wx.DateTime.GetNumberOfDays(day.GetMonth())

            maxDY = 0
            for idx in xrange(daysCount):
                theDay = Utils.copyDateTime(day)
                # theDay.AddDS(wx.DateSpan(days=idx))
                theDay += wx.DateSpan(days=idx)
                if theDay.IsSameDate(wx.DateTime.Now()):
                    color = self._highlightColor
                else:
                    color = None
                w, h = drawer.DrawSimpleDayHeader(
                    theDay,
                    x + 1.0 * idx * width / daysCount,
                    y + h,
                    1.0 * width / daysCount,
                    # int(float(width) / daysCount),
                    height,
                    highlight=color,
                )
                self._headerBounds.append(
                    (x + 1.0 * (idx + 1) * width / daysCount, y + h, height)
                )
                maxDY = max(maxDY, h)

            h += maxDY

        # self.Refresh()

        log.debug(
            f"wxSchedulerPaint._paintMonthlyHeaders a w={w}, h={h} avant retour."
        )
        return w, h
        # return max(1, int(w)), max(0, int(h))

    def _paintMonthly(self, drawer, day, x, y, width, height):
        """
        Affiche la grille du mois en utilisant le module calendar.
        :param drawer: Objet de dessin
        :param day: Date de référence (premier jour du mois)
        :param x: Position X
        :param y: Position Y
        :param width: Largeur
        :param height: Hauteur
        :return: Dimensions utilisées (width, height)
        """
        log.debug(
            f"wxSchedulerPaint._paintDaily : Affiche la grille du mois avec drawer={drawer}, day={day}, x={x}, y={y}, width={width}, height={height}."
        )
        if self._drawHeaders:
            w, h = self._paintMonthlyHeaders(
                drawer, day, int(x), int(y), int(width), int(height)
            )
        else:
            w, h = int(width), 0

        y += h
        height -= h

        if self._style == wxSCHEDULER_VERTICAL:
            month = calendar.monthcalendar(day.GetYear(), day.GetMonth() + 1)

            for w, monthWeek in enumerate(month):
                for d, monthDay in enumerate(monthWeek):
                    cellW, cellH = 1.0 * width / 7, 1.0 * height / len(month)

                    if monthDay == 0:
                        theDay = None
                        schedules = []
                    else:
                        theDay = day
                        theDay.SetDay(monthDay)
                        theDay.SetHour(0)
                        theDay.SetMinute(0)
                        theDay.SetSecond(0)

                        end = Utils.copyDateTime(theDay)
                        # end.AddDS(wx.DateSpan(days=1))
                        end += wx.DateSpan(days=1)

                        schedules = self._getSchedInPeriod(
                            self._schedules, theDay, end
                        )

                        if self._minSize is None or not self._resizable:
                            self._datetimeCoords.append(
                                (
                                    Utils.copyDateTime(theDay),
                                    wx.Point(int(d * cellW), int(w * cellH)),
                                    wx.Point(
                                        int(d * cellW + cellW),
                                        int(w * cellH + cellH),
                                    ),
                                )
                            )

                    displayed = drawer.DrawSchedulesCompact(
                        theDay,
                        schedules,
                        int(d * cellW),
                        int(w * cellH + y),
                        int(cellW),
                        int(cellH),
                        self._highlightColor,
                    )
                    self._schedulesCoords.extend(displayed)

                    for schedule in set(schedules) - set(
                        [sched for sched, _, _ in displayed]
                    ):
                        schedule.Destroy()

            # self.Refresh()
            return (
                max(MONTH_CELL_SIZE_MIN.width * 7, width),
                max(MONTH_CELL_SIZE_MIN.height * (w + 1), height),
            )
        else:
            day.SetDay(1)
            day.SetHour(0)
            day.SetMinute(0)
            day.SetSecond(0)

            # daysCount = wx.DateTime.GetNumberOfDaysInMonth(day.GetMonth())
            daysCount = wx.DateTime.GetNumberOfDays(day.GetMonth())

            minHeight = h

            w, h = self._paintPeriod(
                drawer, day, daysCount, x, y, width, height
            )
            minHeight += h

            # self.Refresh()
            log.debug(
                f"wxSchedulerPaint._paintMonthly a w={w}, minHeight={minHeight} avant retour."
            )
            return w, minHeight
            # return max(1, int(w)), max(0, int(minHeight))

    def _processEvt(self, commandEvent, point):
        """
        Traite un événement de commande utilisateur à la position spécifiée.
        :param commandEvent: Type d'événement wxPython
        :param point: Position concernée
        """
        evt = wx.PyCommandEvent(commandEvent)
        _, _, sch = self._findSchedule(point)
        if isinstance(sch, wxSchedule):
            mySch = sch
            myDate = None
        else:
            mySch = None
            myDate = sch

        evt.schedule = mySch
        evt.date = myDate
        evt.SetEventObject(self)
        self.ProcessEvent(evt)

    def DoPaint(self, drawer, x, y, width, height):
        """
        Effectue le rendu principal du planificateur selon la vue courante.

        Appelé par DrawBuffer().

        :param drawer: Objet de dessin
        :param x, y: Position d'origine
        :param width, height: Dimensions d'affichage
        :return: Dimensions utilisées (width, height)
        """
        log.debug(
            "wxSchedulerPaint.DoPaint : Effectue le rendu principal du planificateur selon la vue courante."
        )
        # Le plus important : que chaque méthode de paint
        # (daily/weekly/monthly) retourne bien deux entiers strictement positifs.
        for schedule, _, _ in self._schedulesCoords:
            schedule.Destroy()

        self._schedulesCoords = list()

        day = Utils.copyDate(self.GetDate())

        # if self._viewType == wxSCHEDULER_DAILY:
        #     return self._paintDaily(drawer, day, x, y, width, height)
        # elif self._viewType == wxSCHEDULER_WEEKLY:
        #     return self._paintWeekly(drawer, day, x, y, width, height)
        # elif self._viewType == wxSCHEDULER_MONTHLY:
        #     return self._paintMonthly(drawer, day, x, y, width, height)
        if self._viewType == wxSCHEDULER_DAILY:
            result = self._paintDaily(drawer, day, x, y, width, height)
        elif self._viewType == wxSCHEDULER_WEEKLY:
            result = self._paintWeekly(drawer, day, x, y, width, height)
        elif self._viewType == wxSCHEDULER_MONTHLY:
            result = self._paintMonthly(drawer, day, x, y, width, height)
        else:
            result = None

        # Sécurisation
        if (
            not result
            or not isinstance(result, (tuple, list))
            or len(result) != 2
            or not all(isinstance(v, (int, float)) for v in result)
        ):
            # Valeur de secours
            log.debug(
                f"wxSchedulerPaint.DoPaint retourne width={width}, height={height}"
            )
            return width, height
        # Toujours >= 1
        w, h = max(1, int(result[0])), max(
            1, int(result[1])
        )  # mais ce ne serait pas plutôt result[4] et result[5] ? Non, car result est un tuple de 2 éléments.
        log.debug(f"wxSchedulerPaint.DoPaint retourne w={w}, h={h}")
        return w, h

    def GetViewSize(self):
        """
        Retourne la taille réelle de la vue planificateur (pour gestion du rapport).
        :return: wx.Size
        """
        # Used by wxSchedulerReport
        size = self.GetSize()  # ou GetVirtualSize ?
        minSize = self.CalcMinSize()

        return wx.Size(
            max(size.width, minSize.width), max(size.height, minSize.height)
        )

    def _CalcMinSize(self):
        """
        Calcule la taille minimale nécessaire du planificateur selon la vue courante.
        :return: wx.Size
        """
        # minW, minH = DAY_SIZE_MIN.width, DAY_SIZE_MIN.height  # Initialisation
        if self._viewType == wxSCHEDULER_DAILY:
            minW, minH = DAY_SIZE_MIN.width, DAY_SIZE_MIN.height
        elif self._viewType == wxSCHEDULER_WEEKLY:
            minW, minH = WEEK_SIZE_MIN.width, WEEK_SIZE_MIN.height
        elif self._viewType == wxSCHEDULER_MONTHLY:
            minW, minH = MONTH_CELL_SIZE_MIN.width * 7, 0  # will be computed

        if (
            self._viewType == wxSCHEDULER_MONTHLY
            or self._style == wxSCHEDULER_HORIZONTAL
        ):
            # Créer un contexte de dispositif de mémoire
            memDC = wx.MemoryDC()
            # bmp = wx.EmptyBitmap(1, 1)
            bmp = wx.Bitmap(1, 1)  # Phoenix-compatible
            memDC.SelectObject(bmp)
            # memDC.SelectObject(wx.NullBitmap)
            try:
                if self._drawerClass.use_gc:
                    context = wx.GraphicsContext.Create(memDC)
                    context.SetFont(wx.NORMAL_FONT, wx.BLACK)
                else:
                    context = memDC
                    context.SetFont(wx.NORMAL_FONT)

                if isinstance(self, wx.ScrolledWindow):
                    size = self.GetVirtualSize()
                else:
                    size = self.GetSize()

                # Actually, only the min height may vary...
                result = self.DoPaint(
                    self._drawerClass(context, self._lstDisplayedHours),
                    0,
                    0,
                    size.GetWidth(),
                    0,
                )
                if (
                    not result
                    or not isinstance(result, (tuple, list))
                    or len(result) != 2
                ):
                    minH = 0
                else:
                    _, minH = result

                minH = max(1, int(minH))  # Toujours >= 1

                if self._style == wxSCHEDULER_HORIZONTAL:
                    if self._viewType == wxSCHEDULER_DAILY:
                        minW = self._periodWidth * 4
                    elif self._viewType == wxSCHEDULER_WEEKLY:
                        minW = self._periodWidth * 7
                    elif self._viewType == wxSCHEDULER_MONTHLY:
                        # return wx.Size(
                        #     self._periodWidth
                        #     * wx.DateTime.GetNumberOfDaysInMonth(
                        #         self.GetDate().GetMonth()
                        #     ),
                        #     minH,
                        # )
                        # Autre :
                        # return wx.Size(
                        #     self._periodWidth
                        #     * wx.DateTime.GetNumberOfDays(
                        #         self.GetDate().GetMonth()
                        #     ),
                        #     minH,
                        # )
                        # Correction pour wx.DateTime API :
                        dt = self.GetDate()
                        days_in_month = dt.GetNumberOfDays()
                        minW = self._periodWidth * days_in_month
                        return wx.Size(max(1, int(minW)), minH)
                elif self._viewType == wxSCHEDULER_MONTHLY:
                    return wx.Size(max(1, int(minW)), minH)
            finally:
                memDC.SelectObject(wx.NullBitmap)
        elif self._style == wxSCHEDULER_VERTICAL:
            return wx.Size(
                max(1, int(minW * self._periodCount + LEFT_COLUMN_SIZE)),
                max(1, int(minH)),
            )

        return wx.Size(
            max(1, int(minW * self._periodCount)), max(1, int(minH))
        )

    def CalcMinSize(self):
        """
        Retourne la taille minimale, en la recalculant si nécessaire.
        :return: wx.Size
        """
        if self._minSize is None:
            self._minSize = self._CalcMinSize()
        return self._minSize

    def InvalidateMinSize(self):
        """
        Invalide la taille minimale mémorisée pour forcer un recalcul.
        """
        self._minSize = None
        self._datetimeCoords = list()

    def DrawBuffer(self):
        """
        Prépare le dessin en mémoire (backbuffer) pour le calendrier.

        Méthode principale pour Dessiner le contenu du planificateur dans un bitmap tampon pour l'affichage.
        Celle-ci appelle DoPaint(), qui appelle _paintDaily() ou _paintWeekly() ou _paintMonthly() selon la vue active.
        """
        # 1. Taille à utiliser pour le bitmap
        if isinstance(self, wx.ScrolledWindow):
            # if self._resizable:
            if getattr(self, "_resizable", False):
                size = self.GetVirtualSize()  # Correct
            else:
                size = self.CalcMinSize()
        else:
            size = self.GetSize()

        # 2. Toujours >=1 pour éviter crash
        bitmap_width = max(1, int(abs(size.GetWidth())))
        bitmap_height = max(1, int(abs(size.GetHeight())))
        log.debug(
            f"wxSchedulerPaint.DrawBuffer: bitmap_width={bitmap_width}, bitmap_height={bitmap_height}"
        )

        # self._bitmap = wx.EmptyBitmap(size.GetWidth(), size.GetHeight())
        # self._bitmap = wx.Bitmap(size.GetWidth(), size.GetHeight())
        # self._bitmap = wx.Bitmap(bitmap_width, bitmap_height)
        # --- Correction HiDPI --- :
        # Crée un bitmap tampon pour dessiner hors écran
        self._bitmap = wx.Bitmap(bitmap_width, bitmap_height)
        self._bitmap.CreateWithDIPSize(
            (bitmap_width, bitmap_height), self.GetDPIScaleFactor()
        )
        # Créer un contexte de dispositif de mémoire pour dessiner dans le bitmap
        memDC = wx.MemoryDC()
        # Un contexte de dispositif de mémoire fournit un moyen de dessiner des graphiques sur un bitmap.
        memDC.SelectObject(self._bitmap)
        # We can now draw into the memory DC...
        # Copy from this DC to another DC.
        # Permettre d'utiliser cet objet de contexte de dispositif
        # pour modifier le contenu bitmap donné.
        #
        # Notez que si vous n'avez besoin d'utiliser que le contenu bitmap existant
        # au lieu de le modifier, vous devez utiliser SelectObjectAsSourceà la place.
        #
        # Avant d'utiliser les données de bitmap mises à jour,
        # assurez-vous de les sélectionner d'abord hors contexte
        # soit en sélectionnant wx.NullBitmapdans le contexte du dispositif
        # ou en détruisant entièrement le contexte du dispositif.
        #
        # Si le bitmap est déjà sélectionné dans ce contexte de dispositif,
        # rien n'est fait. S'il est sélectionné dans un autre contexte,
        # la fonction affirme et dessiner sur le bitmap ne fonctionnera pas correctement.
        # memDC.SelectObjectAsSource(self._bitmap)

        # memDC.BeginDrawing()  # Inutile dans le nouveau wxPython(phoenix)
        # try:
        memDC.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
        memDC.SetPen(FOREGROUND_PEN)
        memDC.Clear()
        memDC.SetFont(wx.NORMAL_FONT)

        if self._drawerClass.use_gc:
            context = wx.GraphicsContext.Create(memDC)
            context.SetFont(wx.NORMAL_FONT, wx.BLACK)
        else:
            context = memDC
            context.SetFont(wx.NORMAL_FONT)

        # width, height = self.DoPaint(
        #     self._drawerClass(context, self._lstDisplayedHours),
        #     # en wxPython Phoenix (4.x et plus), wx.DC est une classe abstraite
        #     # (non instanciable, non héritée directement).
        #     # → Il faut utiliser une sous-classe concrète adaptée, typiquement :
        #     #
        #     #     wx.MemoryDC
        #     #     wx.PaintDC
        #     #     wx.ClientDC
        #     #     etc.
        #     # self.wxBaseDrawer(context, self._lstDisplayedHours),
        #     0,
        #     0,
        #     size.GetWidth(),
        #     size.GetHeight(),
        # )
        # Plus robuste :
        # Appelle la méthode de dessin principale pour remplir le DC :
        # Dessiner tout le calendrier dans le btimap:
        # wh = self.DoPaint(  # Dessin effectif
        #     self._drawerClass(context, self._lstDisplayedHours),
        #     # en wxPython Phoenix (4.x et plus), wx.DC est une classe abstraite
        #     # (non instanciable, non héritée directement).
        #     # → Il faut utiliser une sous-classe concrète adaptée, typiquement :
        #     #
        #     #     wx.MemoryDC
        #     #     wx.PaintDC
        #     #     wx.ClientDC
        #     #     etc.
        #     # self.wxBaseDrawer(context, self._lstDisplayedHours),
        #     0,
        #     0,
        #     int(bitmap_width),
        #     int(bitmap_height),
        # )
        wh = self.DoPaint(
            self._drawerClass(memDC, self._lstDisplayedHours),
            0,
            0,
            size.GetWidth(),
            size.GetHeight(),
        )
        if wh is not None:
            log.debug(
                "wxSchedulerPaint.DrawBuffer: wh is not None : width=%d, height=%d",
                wh[0],
                wh[1],
            )
        else:
            log.debug("wxSchedulerPaint.DrawBuffer: wh is None.")

        if wh is None:
            width, height = bitmap_width, bitmap_height
            log.debug(
                f"wxSchedulerPaint.DrawBuffer: wh is None : width={width}, height={height}"
            )
        else:
            width, height = wh
            log.debug(
                f"wxSchedulerPaint.DrawBuffer: wh is not None : width={width}, height={height}"
            )
        # finally:
        #    # memDC.EndDrawing()  # Inutile dans wxPython(phoenix)
        width = max(1, int(width))
        height = max(1, int(height))

        # Libère le bitmap du contexte mémoire (obligatoire pour éviter des bugs):
        memDC.SelectObject(wx.NullBitmap)
        self._buffer = self._bitmap

        # 3. Redimensionnement virtuel si besoin
        # Bad things may happen here from time to time.
        if isinstance(self, wx.ScrolledWindow):
            # if self._resizable and not self._guardRedraw:
            # Plus robuste :
            if getattr(self, "_resizable", False) and not getattr(
                self, "_guardRedraw", False
            ):
                self._guardRedraw = True
                try:
                    # Correction : Ne pas appeler DrawBuffer() récursivement ici.
                    # SetVirtualSize déclenchera un redessin si nécessaire.
                    # if int(width) > size.GetWidth() or int(height) > size.GetHeight():
                    if width > bitmap_width or height > bitmap_height:
                        # self.SetVirtualSize(wx.Size(int(width), int(height)))
                        if width < 1 or height < 1:
                            log.error(
                                f"[wxSchedulerPaint.DrawBuffer] ERROR: Tried to set virtual size to ({width},{height})"
                            )
                            width = max(1, int(width))
                            height = max(1, int(height))
                        try:
                            width = max(1, int(width))
                            height = max(1, int(height))
                        except Exception as e:
                            log.error(
                                "[DrawBuffer] Exception in width/height casting:",
                                repr(e),
                            )
                            width, height = 1, 1
                        if width < 1:
                            log.debug(
                                f"[DrawBuffer] width < 1 ({width}), correction en 1"
                            )
                            width = 1
                        if height < 1:
                            log.debug(
                                f"[DrawBuffer] height < 1 ({height}), correction en 1"
                            )
                            height = 1
                        log.debug(
                            f"[DrawBuffer] width={width}, height={height} (avant SetVirtualSize)",
                            # stack_info=True,
                        )
                        print(
                            f"[DrawBuffer] width={width}, height={height} (avant SetVirtualSize)",
                            flush=True,
                        )
                        import traceback

                        traceback.print_stack()
                        self.SetVirtualSize(wx.Size(width, height))
                        # wx._core.wxAssertionError: C++ assertion
                        # ""Assert failure"" failed at /tmp/pip-install-4_0bs8yv/wxpython_03edf520c8784772bf93c2c3901a2867/ext/wxWidgets/src/common/sizer.cpp(1179) in RecalcSizes(): Must be overridden if RepositionChildren() is not
                        # self.DrawBuffer()  # Risque de boucle infinie !
                finally:
                    self._guardRedraw = False
                    # # Afficher le résultat sur la fenêtre
                    # paintDC = wx.ClientDC(self)
                    # # Blitte le dessin à l'écran, dans la vraie fenêtre.
                    # paintDC.DrawBitmap(self._bitmap, 0, 0, True)

    def RefreshSchedule(self, schedule):
        """
        Rafraîchit uniquement la zone d'un planning donné.
        :param schedule: Planning à rafraîchir
        """
        # C'est une optimisation pour la fluidité de l'interface.
        log.info(
            f"xcSchedulerPaint.RefreshSchedule : Rafraîchit uniquement la zone du planning {schedule}."
        )
        if schedule.bounds is not None:
            memDC = wx.MemoryDC()
            memDC.SelectObject(self._bitmap)
            try:
                # memDC.BeginDrawing()  # Inutile avec Phoenix
                memDC.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
                memDC.SetPen(FOREGROUND_PEN)
                memDC.SetFont(wx.NORMAL_FONT)

                if self._drawerClass.use_gc:
                    context = wx.GraphicsContext.Create(memDC)
                    context.SetFont(wx.NORMAL_FONT, wx.BLACK)
                else:
                    context = memDC
                    context.SetFont(wx.NORMAL_FONT)

                self._drawerClass(
                    context, self._lstDisplayedHours
                )._DrawSchedule(schedule, *schedule.bounds)
            finally:
                memDC.SelectObject(wx.NullBitmap)

            originX, originY = self.GetViewStart()
            unitX, unitY = self.GetScrollPixelsPerUnit()
            x, y, w, h = schedule.bounds
            self.RefreshRect(
                wx.Rect(
                    math.floor(x - originX * unitX) - 1,
                    math.floor(y - originY * unitY) - 1,
                    math.ceil(w) + 2,
                    math.ceil(h) + 2,
                )
            )
        log.info(
            "wxSchedulePaint.RefreshSchedule a fini le rafraîchissement !"
        )

    def OnPaint(self, evt=None):
        """
        Gère l'événement de dessin (paint) du widget wxPython.
        :param evt: Événement wxPython (optionnel)
        """
        # Certainement plus nécessaire depuis Phoenix !? Si si, C'est définit dans getDc.
        log.debug(
            f"wxSchedulerPaint.OnPaint : appelé par {self} avec l'événement {evt}."
        )
        # Correction : Toujours utiliser wx.PaintDC pour les événements EVT_PAINT
        # et s'assurer que le bitmap est prêt.
        if self._dc:
            dc = self._dc
        else:
            dc = wx.PaintDC(self)
        self.PrepareDC(dc)  # Prépare le DC pour le défilement
        # self.DoPrepareDC(dc)  # unresolved

        # dc.BeginDrawing()
        # try:
        dc.DrawBitmap(self._bitmap, 0, 0, False)
        # dc.DrawBitmap(self._bitmap, wx.Point(0, 0), False)
        # if hasattr(self, '_buffer') and self._buffer.IsOk():
        #     # Obtenir le décalage de défilement
        #     x_scroll, y_scroll = self.GetViewStart()
        #     unit_x, unit_y = self.GetScrollPixelsPerUnit()
        #     # Blitter le bitmap avec le décalage de défilement
        #     dc.DrawBitmap(self._buffer, -x_scroll * unit_x, -y_scroll * unit_y, False)
        #     log.debug(f"wxSchedulerPaint.OnPaint : dc.DrawBitmap({self._buffer}, {-x_scroll * unit_x}, {-y_scroll * unit_y}, False)")
        # else:
        #     log.warning("wxSchedulerPaint.OnPaint : _buffer n'est pas prêt ou invalide.")
        #     # Optionnel: Dessiner un fond vide ou un message d'erreur si le buffer n'est pas prêt
        #     dc.Clear()
        log.debug(
            "wxSchedulerPaint.OnPaint : wx.PaintDC is OK ? %s", dc.IsOk()
        )
        log.debug(
            f"wxSchedulerPaint.OnPaint : a fini dc.DrawBitmap({self._bitmap}, 0, 0, False) !"
        )
        # finally:
        #     dc.EndDrawing()

    def SetResizable(self, value):
        """
        Définit si la vue doit être redimensionnable proportionnellement à la zone disponible.
        :param value: booléen
        """
        self._resizable = bool(value)

    def SetStyle(self, style):
        """
        Définit le style d'affichage (vertical ou horizontal).
        :param style: wxSCHEDULER_VERTICAL ou wxSCHEDULER_HORIZONTAL
        """
        self._style = style
        self.InvalidateMinSize()
        self.Refresh()

    def GetStyle(self):
        """
        Retourne le style d'affichage courant.
        :return: Style
        """
        return self._style

    def SetHighlightColor(self, color):
        """
        Définit la couleur de surbrillance (pour aujourd'hui par exemple).
        :param color: Couleur wx.Colour
        """
        # Permet de configurer l'apparence, ce qui est bon pour la personnalisation et la visibilité.
        self._highlightColor = color

    def GetHighlightColor(self):
        """
        Retourne la couleur de surbrillance actuelle.
        :return: (wx.Colour)
        """
        return self._highlightColor

    def SetDrawer(self, drawerClass):
        """
        Définit la classe de dessin à utiliser pour le rendu graphique.
        :param drawerClass: Classe de dessin
        """
        # Permet de configurer l'apparence, ce qui est bon pour la personnalisation et la visibilité.
        log.debug(
            f"wxSchedulerPaint.SetDrawer : Définit la classe de dessin {drawerClass} à utiliser pour le rendu graphique."
        )
        self._drawerClass = drawerClass
        self.InvalidateMinSize()
        # self.Refresh()

    def GetDrawer(self):
        """
        Retourne la classe de dessin actuelle.
        :return: La classe de dessin.
        """
        log.debug(
            f"wxSchedulerPaint.GetDrawer : Retourne la classe de dessin actuelle pour le rendu graphique = {self._drawerClass}."
        )
        return self._drawerClass

    def SetPeriodWidth(self, width):
        """
        Définit la largeur d'une période (jour) en mode horizontal.
        :param width: Largeur en pixels
        """
        self._periodWidth = width

    def GetPeriodWidth(self):
        return self._periodWidth

    def Refresh(self):
        """
        Rafraîchit le planificateur et force le redessin du contenu et de l'en-tête si présent.
        """
        log.info(
            f"wxSchedulerPaint.Refresh : est appelé sur self={self.__class__.__name__}!"
        )
        self.DrawBuffer()
        super().Refresh()
        if self._headerPanel is not None:
            self._headerPanel.Refresh()
        log.info("wxSchedulerPaint.Refresh est terminé !")

    def SetHeaderPanel(self, panel):
        """
        Définit un panneau wx.Panel comme zone d'en-tête indépendante.
        Les en-têtes seront alors dessinés sur ce panneau, indépendamment du scroll vertical.
        :param panel: Instance de wx.Panel
        """
        # log.debug(f"wxSchedulerPaint.SetHeaderPanel : définit {panel} comme zone d'en-tête indépendante.")
        log.debug(
            f"wxSchedulerPaint.SetHeaderPanel : self._drawHeaders=False donc les en-têtes seront alors dessinés sur ce panneau, indépendamment du scroll vertical."
        )
        self._drawHeaders = False
        # self._drawHeaders = True
        self._headerPanel = panel

        panel.Bind(wx.EVT_PAINT, self._OnPaintHeaders)
        panel.Bind(wx.EVT_MOTION, self._OnMoveHeaders)
        panel.Bind(wx.EVT_LEAVE_WINDOW, self._OnLeaveHeaders)
        panel.Bind(wx.EVT_LEFT_DOWN, self._OnLeftDownHeaders)
        panel.Bind(wx.EVT_LEFT_UP, self._OnLeftUpHeaders)
        panel.SetSize(wx.Size(-1, 1))
        self.Bind(wx.EVT_SCROLLWIN, self._OnScroll)  # EvtHandler !
        # panel.Bind(wx.EVT_SCROLLWIN, self._OnScroll)  # EvtHandler !

        panel.Refresh()
        log.debug(
            f"wxSchedulerPaint.SetHeaderPanel : Terminé ! {panel}=zone d'en-tête."
        )

    # Headers stuff

    def _OnPaintHeaders(self, evt):
        """
        Gère l'événement de peinture pour dessiner les en-têtes du calendrier.

        Cette méthode est responsable de la représentation graphique des en-têtes
        (jours, semaines, mois) en fonction du type de vue et du style du planificateur.
        Elle initialise le contexte de dessin, calcule les dimensions, prend en compte
        le défilement horizontal et délègue le dessin spécifique aux méthodes
        `_paintDailyHeaders`, `_paintWeeklyHeaders` ou `_paintMonthlyHeaders`.
        Elle ajuste également la taille minimale du panneau d'en-tête si nécessaire.

        Args:
            evt (wx.PaintEvent): L'événement de peinture qui a déclenché cette méthode.
        """
        log.debug(
            f"wxSchedulerPaint._OnPaintHeaders : lancé avec evt={evt}. Dessine les en-têtes sur un panneau séparé."
        )
        # Initialisation des variables de position et de taille pour le dessin.
        x, y, width, h = 0, 0, 0, 0
        # Crée un contexte de périphérique de dessin (DC) pour le panneau d'en-tête.
        # wx.PaintDC est utilisé pour les événements de peinture.
        dc = wx.PaintDC(self._headerPanel)
        # Début des opérations de dessin (optionnel dans les versions récentes de wxPython).
        # dc.BeginDrawing()
        # try:
        # Définit la couleur de fond du DC avec une brosse spécifiée par SCHEDULER_BACKGROUND_BRUSH().
        dc.SetBackground(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
        # Définit le stylo de dessin (couleur, épaisseur) pour les tracés.
        dc.SetPen(FOREGROUND_PEN)
        # Efface le contenu du DC avec la couleur de fond définie.
        dc.Clear()
        # Définit la police de caractères pour les opérations de texte.
        dc.SetFont(wx.NORMAL_FONT)

        # Vérifie si le 'drawerClass' (classe de dessin) préfère utiliser le contexte graphique moderne (wx.GraphicsContext).
        if self._drawerClass.use_gc:
            # Crée un contexte graphique à partir du DC pour un rendu de haute qualité.
            context = wx.GraphicsContext.Create(dc)
            # Définit la police et la couleur pour le contexte graphique.
            context.SetFont(wx.NORMAL_FONT, wx.BLACK)
        else:
            # Si le contexte graphique n'est pas utilisé, le DC standard est le contexte de dessin.
            context = dc
            # Définit la police pour le DC standard.
            context.SetFont(wx.NORMAL_FONT)

        # Crée une instance de la classe de dessin, en lui passant le contexte de dessin
        # et la liste des heures affichées.
        drawer = self._drawerClass(
            context, self._lstDisplayedHours
        )  # de wxSchedulerCore

        # Détermine la largeur de la zone de dessin.
        if self._resizable:
            # Si le panneau est redimensionnable, utilise la taille virtuelle actuelle.
            width, _ = (
                self.GetVirtualSize()
            )  # de Window (une classe parente de wxSchedulerPaint)
        else:
            # Sinon, utilise la taille minimale calculée.
            width, _ = self.CalcMinSize()

        # Récupère la date actuelle affichée dans le planificateur.
        day = Utils.copyDate(self.GetDate())  # de wxSchedulerCore !

        # Take horizontal scrolling into account
        # Prend en compte le défilement horizontal.
        # x0: position de départ du défilement en unités.
        x0, _ = (
            self.GetViewStart()
        )  # dans Scrolled, PropertyGrid, ScrolledCanvas ou ScrolledWindowBase !
        # xu: nombre de pixels par unité de défilement.
        xu, _ = (
            self.GetScrollPixelsPerUnit()
        )  # dans Scrolled, PropertyGrid, ScrolledCanvas ou ScrolledWindowBase !
        # Calcule la position horizontale de défilement en pixels.
        x0 *= xu
        # Ajuste la position de départ du dessin pour compenser le défilement.
        x -= x0

        # Initialise une liste pour stocker les limites des en-têtes (pour les clics, par exemple).
        self._headerBounds = []

        # Logique de dessin basée sur le type de vue actuel (journalier, hebdomadaire, mensuel).
        if self._viewType == wxSCHEDULER_DAILY:
            # Si le style est vertical, ajuste la position X et la largeur pour laisser de la place
            # à la colonne de gauche (souvent pour les heures).
            if self._style == wxSCHEDULER_VERTICAL:
                x += LEFT_COLUMN_SIZE
                width -= LEFT_COLUMN_SIZE
            # Copie la date du jour pour l'itération.
            theDay = Utils.copyDateTime(day)
            # Initialise la hauteur maximale des en-têtes de jour.
            maxDY = 0
            # Itère sur le nombre de périodes (jours) à afficher.
            for idx in xrange(self._periodCount):
                # Appelle une méthode privée pour dessiner les en-têtes quotidiens.
                # Retourne la hauteur h occupée par l'en-tête du jour.
                _, h = self._paintDailyHeaders(
                    drawer,  # L'objet dessinateur
                    theDay,  # La date du jour actuel
                    x
                    + 1.0
                    * width
                    / self._periodCount
                    * idx,  # Position X pour ce jour
                    y,  # Position Y (haut du panneau)
                    1.0
                    * width
                    / self._periodCount,  # Largeur allouée à ce jour
                    36,  # Hauteur fixe pour l'en-tête de jour (peut-être une hauteur minimale)
                )
                # Met à jour la hauteur maximale si l'en-tête actuel est plus grand.
                maxDY = max(maxDY, h)
                # Avance la date au jour suivant.
                # theDay.AddDS(wx.DateSpan(days=1))
                theDay += wx.DateSpan(days=1)
            # La hauteur finale pour le panneau d'en-tête est la hauteur maximale trouvée.
            h = maxDY
        elif self._viewType == wxSCHEDULER_WEEKLY:
            # Logique similaire à la vue journalière, mais pour les semaines.
            if self._style == wxSCHEDULER_VERTICAL:
                x += LEFT_COLUMN_SIZE
                width -= LEFT_COLUMN_SIZE
            theDay = Utils.copyDateTime(day)
            maxDY = 0
            for idx in xrange(self._periodCount):
                # Appelle une méthode privée pour dessiner les en-têtes hebdomadaires.
                h = self._paintWeeklyHeaders(
                    drawer,
                    theDay,
                    x + 1.0 * width / self._periodCount * idx,
                    y,
                    1.0 * width / self._periodCount,
                    36,
                )
                maxDY = max(maxDY, h)
                # Avance la date à la semaine suivante.
                # theDay.AddDS(wx.DateSpan(weeks=1))
                theDay += wx.DateSpan(
                    weeks=1
                )  # Utilisation de l'opérateur += pour l'addition de DateSpan.
            h = maxDY
        elif self._viewType == wxSCHEDULER_MONTHLY:
            # Logique pour la vue mensuelle, ne dessine qu'une seule période (le mois entier).
            _, h = self._paintMonthlyHeaders(drawer, day, x, y, width, 36)

        # Récupère la taille minimale actuelle du panneau d'en-tête.
        minW, minH = self._headerPanel.GetMinSize()
        # Si la hauteur minimale actuelle est différente de la hauteur calculée pour les en-têtes.
        if int(minH) != int(h):
            # Met à jour la taille minimale du panneau d'en-tête pour correspondre à la hauteur calculée.
            # Le -1 pour la largeur signifie qu'elle ne change pas ou est déterminée automatiquement.
            self._headerPanel.SetMinSize(wx.Size(-1, h))  # width -1 !!!
            # self._headerPanel.SetMinSize(wx.Size(1, h))
            # Demande au parent du panneau d'en-tête de re-calculer sa disposition.
            self._headerPanel.GetParent().Layout()

        # Mmmmh, maybe we'll support this later, but not right Now
        # Si le style est vertical, les limites des en-têtes sont réinitialisées.
        # Ceci pourrait être lié à la façon dont les clics sont gérés dans un affichage vertical.
        if self._style == wxSCHEDULER_VERTICAL:
            self._headerBounds = []
        # Fin des opérations de dessin (optionnel dans les versions récentes de wxPython).
        # finally:
        #     # dc.EndDrawing()
        # self.Refresh()
        log.info("wxSchedulerPaint._OnPaintHeaders : Terminé !")

    def _OnMoveHeaders(self, evt):
        if self._headerDragOrigin is None:
            for x, y, h in self._headerBounds:
                if abs(evt.GetX() - x) < 5 and y <= evt.GetY() < y + h:
                    if self._headerCursorState == 0:
                        self._headerCursorState = 1
                        self._headerPanel.SetCursor(
                            wx.StockCursor(wx.CURSOR_SIZEWE)
                        )
                    break
            else:
                if self._headerCursorState == 1:
                    self._headerPanel.SetCursor(wx.STANDARD_CURSOR)
                    self._headerCursorState = 0
        else:
            deltaX = evt.GetX() - self._headerDragOrigin
            self.SetPeriodWidth(max(50, self._headerDragBase + deltaX))

            evt = wx.PyCommandEvent(wxEVT_COMMAND_PERIODWIDTH_CHANGED)
            evt.SetEventObject(self)
            self.ProcessEvent(evt)

            self.InvalidateMinSize()
            self.Refresh()

    def _OnLeaveHeaders(self, evt):
        if self._headerCursorState == 1 and self._headerDragOrigin is None:
            self._headerPanel.SetCursor(wx.STANDARD_CURSOR)
            self._headerCursorState = 0

    def _OnLeftDownHeaders(self, evt):
        if self._headerCursorState == 1:
            self._headerDragOrigin = evt.GetX()
            self._headerDragBase = self._periodWidth
            self._headerPanel.CaptureMouse()
        else:
            evt.Skip()

    def _OnLeftUpHeaders(self, evt):
        if self._headerCursorState == 1:
            self._headerPanel.ReleaseMouse()
            self._headerDragOrigin = None
        else:
            evt.Skip()

    def _OnScroll(self, evt):
        self._headerPanel.Refresh()
        evt.Skip()

    def SetOtherMonthColor(self, color=None):
        """Méthode de compatibilité pour la couleur de fond des mois adjacents."""
        pass
