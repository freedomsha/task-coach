#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tkSchedulerPaint
=======================

Ce module, converti de la version wxPython (wxSchedulerPaint), gère le rendu
graphique du planificateur (scheduler) en utilisant le canevas Tkinter.

Il a un rôle de moteur de rendu :
- Dessin des vues journalières, hebdomadaires et mensuelles.
- Gestion des interactions utilisateur (clic, glisser-déposer) sur le canevas.
- Calcul des coordonnées et des dimensions des événements.
- Rendu des en-têtes et des grilles horaires.

La logique est basée sur un objet "drawer" (tkDrawer) qui abstrait les
opérations de dessin sur le canevas Tkinter.
"""
# Voici la conversion du fichier wxSchedulerPaint.py de wxPython vers Tkinter. J'ai adapté la logique de dessin, la gestion des événements et les calculs de taille pour qu'ils fonctionnent avec les widgets et les bibliothèques standards de Tkinter.
#
# Le fichier tkSchedulerPaint.py converti
#
# Ce code réimplémente la logique de rendu pour un widget de planification en utilisant le canevas de Tkinter. La structure de la classe est conservée, mais les appels spécifiques à wxPython sont remplacés par leurs équivalents Tkinter.

# Explications et prochaines étapes
#
#     Initialisation : La classe prend maintenant un widget tk.Canvas en argument.
#     C'est sur ce canevas que tout sera dessiné. Les événements de la souris
#     (<Button-1>, <B1-Motion>, etc.) sont liés à des méthodes internes
#     pour gérer les interactions.
#
#     Remplacement du "Device Context" (DC) : En wxPython, le dessin se fait
#     via un "Device Context" (wx.PaintDC, wx.MemoryDC).
#     Avec Tkinter, on dessine directement sur le Canvas.
#     J'ai créé une classe tkDrawer (dans le fichier tkDrawer.py)
#     qui encapsule les appels de dessin du canevas (create_rectangle, create_text, etc.).
#     La méthode DoPaint reçoit une instance de ce tkDrawer.
#
#     Gestion des événements :
#
#         Les gestionnaires d'événements wxPython (OnPaint, OnMouseMove)
#         sont remplacés par des méthodes liées aux événements Tkinter
#         (_on_motion, _on_left_down).
#
#         La génération d'événements personnalisés (wx.PyCommandEvent)
#         est remplacée par canvas.event_generate().
#         C'est un moyen simple de signaler des actions comme la sélection d'un événement.
#
#     Logique de dessin :
#
#         La méthode DrawBuffer est simplifiée. Elle efface le canevas
#         (canvas.delete("all")) puis appelle DoPaint pour tout redessiner.
#
#         Les méthodes _paintDaily, _paintDay et _paintPeriod conservent
#         la même logique de haut niveau, mais les appels de dessin passent par l'objet drawer.
#
#         Important : J'ai pour l'instant implémenté la logique de base pour
#         la vue journalière (_paintDaily).
#         TODO :Les vues hebdomadaire (_paintWeekly) et mensuelle (_paintMonthly)
#         doivent encore être développées, mais la structure est en place.
#
#     Coordonnées et calculs : La logique pour calculer la position des événements (_computeCoords, _splitSchedules, _getSchedInPeriod) a été conservée mais adaptée pour utiliser les objets datetime de Python au lieu de wx.DateTime.
#
# TODO :Pour continuer, vous devrez :
#
#     Intégrer cette classe dans votre application Tkinter principale.
#     Vous créerez une instance de tkSchedulerPaint en lui passant votre widget Canvas.
#
#     Compléter _paintWeekly et _paintMonthly en suivant le modèle de _paintDaily.
#     La logique consiste à diviser le canevas en sections (7 jours pour la semaine,
#     une grille pour le mois) et à appeler _paintPeriod ou _paintDay pour chaque section.
#
#     Gérer les événements générés (ex: <<ScheduleActivated>>)
#     dans votre code principal en utilisant widget.bind("<<ScheduleActivated>>", votre_fonction).
#
# Ce code constitue une base solide pour votre composant de planification Tkinter.

import logging
import math
import calendar
from datetime import datetime, timedelta

from .tkSchedule import tkSchedule
from .tkDrawer import tkBaseDrawer
from .tkSchedulerConstants import (
    SCHEDULER_VERTICAL,
    SCHEDULER_HORIZONTAL,
    DAY_BACKGROUND_BRUSH,
    DAY_SIZE_MIN,
    LEFT_COLUMN_SIZE,
    MONTH_CELL_SIZE_MIN,
    SCHEDULE_INSIDE_MARGIN,
    SCHEDULER_BACKGROUND_BRUSH,
    SCHEDULE_OUTSIDE_MARGIN,
    FOREGROUND_PEN,
    WEEK_SIZE_MIN,
    SCHEDULER_DAILY,
    SCHEDULER_WEEKLY,
    SCHEDULER_MONTHLY,
)
from . import tkScheduleUtils as Utils

log = logging.getLogger(__name__)

# --- Constantes pour les états d'interaction ---
STATE_NONE = 0
STATE_CLICKED = 1
STATE_DRAGGING = 2
STATE_HOVER_RESIZE_START = 3
STATE_HOVER_RESIZE_END = 4
STATE_DRAGGING_RESIZE_START = 5
STATE_DRAGGING_RESIZE_END = 6


class tkSchedulerPaint(object):
    """
    Classe principale responsable de la gestion du rendu graphique
    du planificateur (scheduler) pour Tkinter.

    Gère l'affichage, le dessin, l'interaction avec les événements souris
    et le redimensionnement. Utilisée comme mixin dans la classe principale
    du Scheduler.
    """

    def __init__(self, canvas, *args, **kwds):
        """
        Initialise les paramètres graphiques et les états d'interaction.

        Args:
            canvas (tk.Canvas): Le widget canevas sur lequel dessiner.
        """
        log.debug(f"tkSchedulerPaint.__init__ : args={args}, kwargs={kwds}")
        super().__init__(*args, **kwds)

        self.canvas = canvas
        self._resizable = False
        self._style = SCHEDULER_VERTICAL
        self._drawerClass = tkBaseDrawer
        self._headerPanel = None  # Ce sera un Canvas Tkinter

        self._schedulesCoords = []
        self._schedulesPages = {}
        self._datetimeCoords = []

        self._minSize = None
        self._drawHeaders = True
        self._guardRedraw = False

        self._periodWidth = 150
        self._headerBounds = []
        self._headerCursorState = 0
        self._headerDragOrigin = None
        self._headerDragBase = None

        # --- États d'interaction ---
        self._scheduleDraggingState = STATE_NONE
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None
        self._scheduleDraggingStick = False

        self._highlightColor = "#ADD8E6"  # Bleu clair

        self.pageNumber = None
        self.pageCount = 1

        self._bind_events()
        log.info("tkSchedulerPaint initialisé !")

    def _bind_events(self):
        """Lie les événements du canevas aux méthodes de gestion."""
        self.canvas.bind("<Button-1>", self._on_left_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_up)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<Motion>", self._on_motion) # Pour le survol
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

    # --- Gestionnaires d'événements Tkinter ---
    def _on_left_down(self, event):
        point = (event.x, event.y)
        shiftDown = bool(event.state & 0x0001)
        self._doClickControl(point, shiftDown)

    def _on_left_up(self, event):
        point = (event.x, event.y)
        self._doEndClickControl(point)

    def _on_motion(self, event):
        point = (event.x, event.y)
        self._doMove(point)

    def _on_right_click(self, event):
        point = (event.x, event.y)
        self._doRightClickControl(point)

    def _on_double_click(self, event):
        point = (event.x, event.y)
        self._doDClickControl(point)

    # --- Logique de contrôle (adaptée de wxPython) ---

    def _doClickControl(self, point, shiftDown=False):
        """Gère le clic de souris sur le planificateur."""
        if self._scheduleDraggingState in [STATE_HOVER_RESIZE_START, STATE_HOVER_RESIZE_END]:
            self._scheduleDraggingState += 2  # Passe en mode DRAGGING_RESIZE
            self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
            self._scheduleDraggingStick = shiftDown
        else:
            found = self._findSchedule(point)
            if not found:
                return

            pMin, pMax, sch = found
            if isinstance(sch, tkSchedule):
                self._scheduleDragged = pMin, pMax, sch
                self._scheduleDraggingState = STATE_CLICKED
                self._scheduleDraggingOrigin = self._computeCoords(point, 0, 0)
                self._scheduleDraggingStick = shiftDown
            else:
                self._processEvt("<<ScheduleActivated>>", point)

    def _doEndClickControl(self, point):
        """Gère la fin du clic (relâchement souris)."""
        if self._scheduleDraggingState == STATE_CLICKED:
            self._processEvt("<<ScheduleActivated>>", point)

        elif self._scheduleDraggingState == STATE_DRAGGING:
            _, dateTime = self._computeCoords(point, 0, 0)
            sched = self._scheduleDragged[2]
            # self._drawDragging(None, self._computeAllCoords) # Le redessin est géré par Refresh
            origin_dt = self._scheduleDraggingOrigin[1]
            offset = dateTime - origin_dt
            sched.Offset(offset)
            self.Refresh()

        elif self._scheduleDraggingState in [STATE_DRAGGING_RESIZE_START, STATE_DRAGGING_RESIZE_END]:
            coords_func = {
                STATE_DRAGGING_RESIZE_START: self._computeStartCoords,
                STATE_DRAGGING_RESIZE_END: self._computeEndCoords
            }[self._scheduleDraggingState]
            _, _, dateTime = coords_func(point)

            sched = self._scheduleDragged[2]
            if self._scheduleDraggingState == STATE_DRAGGING_RESIZE_START:
                sched.SetStart(dateTime)
            else:
                sched.SetEnd(dateTime)

            self.canvas.config(cursor="")
            self.Refresh()

        self._scheduleDraggingState = STATE_NONE
        self._scheduleDragged = None
        self._scheduleDraggingOrigin = None
        self._scheduleDraggingPrevious = None

    def _doMove(self, point):
        """Gère le déplacement de la souris."""
        if self._scheduleDraggingState in [STATE_NONE, STATE_HOVER_RESIZE_START, STATE_HOVER_RESIZE_END]:
            original_state = self._scheduleDraggingState
            self._scheduleDraggingState = STATE_NONE
            self.canvas.config(cursor="")
            self._scheduleDragged = None

            for sched, pointMin, pointMax in self._schedulesCoords:
                px, py = point
                minX, minY = pointMin
                maxX, maxY = pointMax

                if minX < px < maxX:
                    if abs(py - minY) < 4:
                        self._scheduleDraggingState = STATE_HOVER_RESIZE_START
                        self.canvas.config(cursor="sb_v_double_arrow")
                        self._scheduleDragged = (pointMin, pointMax, sched.clientdata)
                        return
                    if abs(py - maxY) < 4:
                        self._scheduleDraggingState = STATE_HOVER_RESIZE_END
                        self.canvas.config(cursor="sb_v_double_arrow")
                        self._scheduleDragged = (pointMin, pointMax, sched.clientdata)
                        return

        elif self._scheduleDraggingState in [STATE_DRAGGING_RESIZE_START, STATE_DRAGGING_RESIZE_END]:
            # Le redessin se fera dans un appel à Refresh pour éviter le scintillement
            pass

        elif self._scheduleDraggingState == STATE_CLICKED:
            origin_x, origin_y = self._scheduleDraggingOrigin[0]
            point_x, point_y = point
            # Démarre le glisser-déposer si la souris a bougé suffisamment
            if abs(origin_x - point_x) >= 4 or abs(origin_y - point_y) >= 4:
                self._scheduleDraggingState = STATE_DRAGGING

        elif self._scheduleDraggingState == STATE_DRAGGING:
            # Idem, on attend le relâchement pour rafraîchir
            pass

    def _computeCoords(self, point, dx, dy):
        """
        Calcule les coordonnées et l'heure correspondante dans le planificateur.

        Args:
            point (tuple): Position (x, y) de base.
            dx (int): Décalage en X.
            dy (int): Décalage en Y.

        Returns:
            tuple: ((x, y), datetime) - Coordonnées et heure correspondante.
        """
        px, py = point
        pp = (px + dx, py + dy)

        # Cherche la case horaire correspondante
        for dt, pointMin, pointMax in self._datetimeCoords:
            minX, minY = pointMin
            maxX, maxY = pointMax
            if minY <= pp[1] <= maxY and minX <= pp[0] <= maxX:
                theTime = Utils.copyDateTime(dt)
                if self._style == SCHEDULER_VERTICAL:
                    # Interpolation du temps en fonction de la position Y
                    ratio = (pp[1] - minY) / (maxY - minY)
                    theTime += timedelta(minutes=30 * ratio)
                else:
                    # Interpolation du temps en fonction de la position X
                    ratio = (pp[0] - minX) / (maxX - minX)
                    theTime += timedelta(minutes=30 * ratio)
                return pp, theTime

        # Si aucune case n'est trouvée (rare), retourner la dernière coordonnée
        if self._datetimeCoords:
            dt, _, _ = self._datetimeCoords[-1]
            return pp, Utils.copyDateTime(dt)

        raise ValueError(f"Coordonnées non trouvées : {pp}")

    # Manque _computeAllCoords, _computeStartCoords et _computeEndCoords
    # et _drawDraggind

    # --- Méthodes de dessin (logique de haut niveau) ---

    def DoPaint(self, drawer, x, y, width, height):
        """
        Effectue le rendu principal du planificateur selon la vue courante.
        """
        log.debug("tkSchedulerPaint.DoPaint: Démarrage du rendu.")
        self._schedulesCoords = []
        self._datetimeCoords = []

        day = self.GetDate().date() # Utilise un objet date
        day_dt = datetime(day.year, day.month, day.day) # Convertit en datetime

        if self._viewType == SCHEDULER_DAILY:
            return self._paintDaily(drawer, day_dt, x, y, width, height)
        elif self._viewType == SCHEDULER_WEEKLY:
            return self._paintWeekly(drawer, day_dt, x, y, width, height)
        elif self._viewType == SCHEDULER_MONTHLY:
            return self._paintMonthly(drawer, day_dt, x, y, width, height)

        return width, height

    def _paintDaily(self, drawer, day, x, y, width, height):
        """Affiche les plannings de la journée."""
        minWidth = minHeight = 0

        if self._style == SCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        theDay = Utils.copyDateTime(day)

        if self._drawHeaders:
            maxDY = 0
            for idx in range(self._periodCount):
                w, h = self._paintDailyHeaders(
                    drawer,
                    theDay,
                    x + width / self._periodCount * idx,
                    y,
                    width / self._periodCount,
                    height,
                    )
                maxDY = max(maxDY, h)
                theDay += timedelta(days=1)
            minHeight += maxDY
            y += maxDY
            height -= maxDY

        if self._style == SCHEDULER_VERTICAL:
            w, h = drawer.DrawHours(x - LEFT_COLUMN_SIZE, y, width + LEFT_COLUMN_SIZE, height, self._style)
            minWidth += w
            x += w
            width -= w

        theDay = Utils.copyDateTime(day)
        for idx in range(self._periodCount):
            dw, dh = self._paintDay(
                drawer,
                theDay,
                x + width / self._periodCount * idx,
                y,
                width / self._periodCount,
                height,
                )
            minWidth += dw
            minHeight += dh
            theDay += timedelta(days=1)

        return minWidth, minHeight

    def _paintDay(self, drawer, day, x, y, width, height):
        """Dessine les plannings d'une journée."""
        start = Utils.copyDateTime(day)
        color = self._highlightColor if day.date() == datetime.now().date() else None
        return self._paintPeriod(drawer, start, 1, x, y, width, height, highlight=color)

    def _paintDailyHeaders(self, drawer, day, x, y, width, height, includeText=True):
        """Dessine les en-têtes de la vue journalière."""
        if not self._drawHeaders or not includeText:
            return width, 0

        color = self._highlightColor if day.date() == datetime.now().date() else None
        w, h = drawer.DrawDayHeader(day, x, y, width, height, highlight=color)
        return w, h

    #  Partenaire de code
    #
    # Absolument ! Voici la conversion des méthodes _paintWeekly et _paintWeeklyHeaders pour votre classe tkSchedulerPaint.
    #
    # La logique reste très similaire à la version wxPython.
    # On détermine d'abord le premier jour de la semaine,
    # puis on dessine soit 7 colonnes verticales (une pour chaque jour),
    # soit une longue bande horizontale si le style est HORIZONTAL.

    # Explications du fonctionnement
    #
    #     _paintWeeklyHeaders :
    #
    #         La fonction trouve le premier jour de la semaine (par exemple, Lundi) en utilisant Utils.setToWeekDayInSameWeek.
    #
    #         Elle boucle 7 fois, une fois pour chaque jour.
    #
    #         À chaque itération, elle calcule la date du jour (the_day), vérifie si c'est aujourd'hui pour appliquer une couleur de surbrillance, puis appelle drawer.DrawDayHeader pour dessiner l'en-tête de ce jour.
    #
    #         La largeur de chaque en-tête de jour est simplement la largeur totale divisée par 7.
    #
    #     _paintWeekly (Style Vertical) :
    #
    #         Après avoir dessiné les en-têtes, la méthode dessine la colonne des heures sur le côté gauche en appelant drawer.DrawHours.
    #
    #         Ensuite, elle boucle sur le nombre total de jours à afficher (7 * self._periodCount).
    #
    #         Pour chaque jour, elle appelle self._paintDay, qui est la méthode de base pour dessiner une seule colonne de jour avec ses événements. Chaque jour occupe une fraction de la largeur totale disponible.
    #
    #     _paintWeekly (Style Horizontal) :
    #
    #         Comme pour la vue mensuelle, ce mode est plus simple. Il délègue tout le travail à _paintPeriod.
    #
    #         Il lui demande de dessiner une période de 7 * self._periodCount jours, en commençant par le premier jour de la semaine. Le résultat est une longue bande horizontale de jours.
    def _paintWeekly(self, drawer, day, x, y, width, height):
        """
        Dessine les plannings de la semaine courante (version Tkinter).

        Args:
            drawer: L'objet de dessin (tkDrawer).
            day (datetime): Une date dans la semaine à afficher.
            x, y, width, height: Dimensions de la zone de dessin.

        Returns:
            tuple: Dimensions minimales requises (min_width, min_height).
        """
        log.debug(f"tkSchedulerPaint._paintWeekly: Affichage de la grille pour la semaine du {day.strftime('%Y-%m-%d')}")

        # Détermine le premier jour de la période à afficher
        first_day = Utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        # firstDay.SetHour(0)
        # firstDay.SetMinute(0)
        # firstDay.SetSecond(0)

        # minWidth = minHeight = 0
        min_width = min_height = 0

        # Ajustement pour la colonne des heures en mode vertical
        if self._style == SCHEDULER_VERTICAL:
            x += LEFT_COLUMN_SIZE
            width -= LEFT_COLUMN_SIZE

        # 1. Dessiner les en-têtes
        # theDay = Utils.copyDateTime(day)
        # maxDY = 0
        max_dy = 0
        header_h = 0

        if self._drawHeaders:
            # maxDY = 0
            # theDay = Utils.copyDateTime(day)
            current_day = Utils.copyDateTime(day)
            for idx in range(self._periodCount):
                # # w, h = self._paintDailyHeaders(
                # #     drawer,
                # #     theDay,
                # #     x + width / self._periodCount * idx,
                # #     y,
                # #     width / self._periodCount,
                # #     height,
                # #     )
                # # maxDY = max(maxDY, h)
                # maxDY = max(
                #     maxDY,
                #     self._paintWeeklyHeaders(
                #         drawer,
                #         theDay,
                #         int(x + 1.0 * width / self._periodCount * idx),
                #         int(y),
                #         int(1.0 * width / self._periodCount),
                #         int(height),
                #     ),
                # )
                period_x = x + (idx * width / self._periodCount)
                period_width = width / self._periodCount

                h = self._paintWeeklyHeaders(
                    drawer, current_day, period_x, y, period_width, height
                )
                max_dy = max(max_dy, h)
                current_day += timedelta(weeks=1)

            header_h -= max_dy

        # Ajuster la zone de dessin principale sous les en-têtes
        min_height += header_h
        y += header_h
        height -= header_h

        # --- Mode d'affichage principal (colonnes verticales) ---
        if self._style == SCHEDULER_VERTICAL:
            # Dessiner la colonne des heures à gauche
            # w, h = drawer.DrawHours(x - LEFT_COLUMN_SIZE, y, width + LEFT_COLUMN_SIZE, height, self._style)
            hour_col_w, _ = drawer.DrawHours(
                x - LEFT_COLUMN_SIZE, y, width + LEFT_COLUMN_SIZE, height, self._style
            )
            # minWidth += w
            min_width += hour_col_w
            # # x += w
            # x -= LEFT_COLUMN_SIZE
            # # width -= w
            # width += LEFT_COLUMN_SIZE

            # Dessiner chaque jour de la semaine
            # minHeight += maxDY
            # y += maxDY
            # height -= maxDY
            current_day = Utils.copyDateTime(first_day)
            num_days_total = 7 * self._periodCount
            day_width = width / num_days_total

            for i in range(num_days_total):
                day_to_paint = current_day + timedelta(days=i)
                day_x = x + i * day_width

                self._paintDay(
                    drawer,
                    day_to_paint,
                    day_x,
                    y,
                    day_width,
                    height,
                )

            min_w = max(WEEK_SIZE_MIN[0] * self._periodCount + LEFT_COLUMN_SIZE, width)
            min_h = max(WEEK_SIZE_MIN[1], height)
            return min_w, min_h + header_h

        # --- Mode d'affichage horizontal (bandeau de jours) ---
        else:  # SCHEDULER_HORIZONTAL
            w, h = self._paintPeriod(
                drawer,
                first_day,
                7 * self._periodCount,
                x,
                y,
                width,
                height,
                )

            min_width += w
            min_height += h

            # self.Refresh()

            log.debug(
                f"wxSchedulerPaint._paintWeekly a minWidth={min_width}, minHeight={min_height} avant retour."
            )
            return (
                max(self._periodWidth * self._periodCount, min_width),
                max(0, min_height),
            )

    def _paintWeeklyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes des jours pour la vue hebdomadaire (version Tkinter).

        Args:
            drawer: L'objet de dessin (tkDrawer).
            day (datetime): Une date dans la semaine à afficher.
            x, y, width, height: Dimensions de la zone d'en-tête.

        Returns:
            int: La hauteur maximale occupée par les en-têtes.
        """
        # log.debug("wxScheduler._paintWeeklyHeaders: pour _drawHeaders:%s day:%s x=%s y=%s width=%s height=%s avec %s", self._drawHeaders, day, x, y, width, height, drawer)
        log.debug(f"tkSchedulerPaint._paintWeeklyHeaders: Dessin des en-têtes pour la semaine du {day.strftime('%Y-%m-%d')}")

        # Trouve le premier jour de la semaine (lundi ou dimanche)
        firstDay = Utils.setToWeekDayInSameWeek(day, 0, self._weekstart)
        # firstDay.SetHour(0)
        # firstDay.SetMinute(0)
        # firstDay.SetSecond(0)

        maxDY = 0
        day_width = width / 7

        for weekday in range(7):
            # Calcule la date pour chaque jour de la semaine
            # theDay = Utils.setToWeekDayInSameWeek(
            #     Utils.copyDateTime(firstDay), weekday, self._weekstart
            # )
            theDay = firstDay + timedelta(days=weekday)

            # # if theDay.IsSameDate(wx.DateTime.Now()):
            # color = self._highlightColor if day.date() == datetime.now().date() else None
            is_today = theDay.date() == datetime.now().date()
            color = self._highlightColor if is_today else None

            day_x = x + (weekday * day_width)

            # Dessine l'en-tête pour un jour (ex: "Lundi 13 Octobre")
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
            )  # Si nécessaire pour le redimensionnement
            maxDY = max(maxDY, h)

        # self.Refresh()
        log.debug(f"wxSchedulerPaint._paintWeeklyHeaders retourne maxDY={maxDY}")
        return maxDY

    # Comment ça marche et ce qu'il faut vérifier
    #
    #     Dépendances : Ce code suppose que votre tkDrawer
    #     (et plus spécifiquement le HeaderDrawerMixin) contient les méthodes
    #     DrawMonthHeader, DrawSimpleDayHeader et DrawSchedulesCompact.
    #     Ces méthodes sont cruciales :
    #
    #         DrawMonthHeader: Doit dessiner le titre du mois (ex: "Octobre 2025").
    #
    #         DrawSimpleDayHeader: Doit dessiner une version compacte du jour (ex: "Ven 10").
    #
    #         DrawSchedulesCompact: C'est la méthode la plus complexe.
    #         Elle doit dessiner le fond d'une cellule de jour,
    #         afficher le numéro du jour,
    #         puis lister les événements de manière compacte à l'intérieur de la cellule.
    #
    #     _paintMonthly (Style Vertical) :
    #
    #         C'est la vue "calendrier" classique.
    #
    #         On utilise calendar.monthcalendar pour obtenir une liste de listes,
    #         représentant parfaitement la grille.
    #
    #         On parcourt cette grille et on calcule la position (cell_x, cell_y)
    #         et la taille (cell_w, cell_h) de chaque "case" du calendrier.
    #
    #         Si le jour est 0, la case est vide (elle appartient au mois précédent ou suivant).
    #         Sinon, on récupère les événements du jour et on appelle drawer.DrawSchedulesCompact.
    #
    #         Les coordonnées des jours (_datetimeCoords) et des événements
    #         dessinés (_schedulesCoords) sont stockées pour permettre de
    #         détecter sur quoi l'utilisateur clique.
    #
    #     _paintMonthly (Style Horizontal) :
    #
    #         Cette vue est beaucoup plus simple.
    #         Elle affiche tous les jours du mois les uns à la suite des autres, horizontalement.
    #
    #         On utilise la méthode _paintPeriod que vous avez déjà convertie,
    #         en lui demandant simplement de dessiner tous les jours du mois.
    def _paintMonthly(self, drawer, day, x, y, width, height):
        """
        Affiche la grille du mois et les planifications (version Tkinter).

        Args:
            drawer: L'objet de dessin (tkDrawer).
            day (datetime): Une date dans le mois à afficher.
            x, y, width, height: Dimensions de la zone de dessin.

        Returns:
            tuple: Dimensions minimales requises (min_width, min_height).
        """
        log.debug(f"tkSchedulerPaint._paintMonthly: Affichage de la grille pour {day.strftime('%B %Y')}")

        # 1. Dessiner les en-têtes et obtenir leur hauteur
        header_w, header_h = 0, 0
        if self._drawHeaders:
            header_w, header_h = self._paintMonthlyHeaders(drawer, day, x, y, width, height)

        # Ajuster la zone de dessin pour la grille
        y += header_h
        height -= header_h

        # --- Mode d'affichage principal (grille verticale) ---
        if self._style == SCHEDULER_VERTICAL:
            # Obtenir la matrice du mois depuis le module calendar
            # Ex: [[0, 0, 1, 2, 3, 4, 5], [6, 7, ...]]
            month_grid = calendar.monthcalendar(day.year, day.month)
            num_weeks = len(month_grid)

            # Calculer les dimensions de chaque cellule
            cell_w = width / 7
            cell_h = height / num_weeks

            for week_idx, week in enumerate(month_grid):
                for day_idx, month_day in enumerate(week):

                    cell_x = x + day_idx * cell_w
                    cell_y = y + week_idx * cell_h

                    # Un jour à 0 signifie qu'il n'appartient pas à ce mois
                    if month_day == 0:
                        drawer.DrawSchedulesCompact(None, [], cell_x, cell_y, cell_w, cell_h, self._highlightColor)
                        continue

                    # C'est un jour valide, on le traite
                    the_day = datetime(day.year, day.month, month_day)
                    end_of_day = the_day + timedelta(days=1)

                    schedules = self._getSchedInPeriod(self._schedules, the_day, end_of_day)

                    # Enregistrer les coordonnées pour la détection de clic
                    self._datetimeCoords.append(
                        (the_day, (cell_x, cell_y), (cell_x + cell_w, cell_y + cell_h))
                    )

                    # Demander au drawer de dessiner la cellule et les événements compacts
                    displayed_coords = drawer.DrawSchedulesCompact(
                        the_day, schedules, cell_x, cell_y, cell_w, cell_h, self._highlightColor
                    )
                    self._schedulesCoords.extend(displayed_coords)

            # Retourner les dimensions minimales calculées
            min_w = max(MONTH_CELL_SIZE_MIN[0] * 7, width)
            min_h = max(MONTH_CELL_SIZE_MIN[1] * num_weeks, height) + header_h
            return min_w, min_h

        # --- Mode d'affichage horizontal (bandeau de jours) ---
        else: # SCHEDULER_HORIZONTAL
            first_day_of_month = day.replace(day=1)
            _, days_in_month = calendar.monthrange(day.year, day.month)

            # Utiliser _paintPeriod pour dessiner tous les jours séquentiellement
            w, h = self._paintPeriod(drawer, first_day_of_month, days_in_month, x, y, width, height)

            return w, h + header_h

    def _paintMonthlyHeaders(self, drawer, day, x, y, width, height):
        """
        Dessine les en-têtes pour la vue mensuelle (version Tkinter).

        Args:
            drawer: L'objet de dessin (tkDrawer).
            day (datetime): Une date dans le mois à afficher.
            x, y, width, height: Dimensions de la zone d'en-tête.

        Returns:
            tuple: (largeur, hauteur) occupées par l'en-tête.
        """
        log.debug(f"tkSchedulerPaint._paintMonthlyHeaders: Dessin de l'en-tête pour {day.strftime('%B %Y')}")

        # 1. Dessiner l'en-tête principal du mois (ex: "Octobre 2025")
        w, h = drawer.DrawMonthHeader(day, x, y, width, height)

        # 2. Si le style est horizontal, dessiner un en-tête pour chaque jour
        if self._style == SCHEDULER_HORIZONTAL:
            first_day_of_month = day.replace(day=1)
            # Obtenir le nombre de jours dans le mois
            _, days_in_month = calendar.monthrange(day.year, day.month)

            max_dy = 0
            header_y = y + h # Positionner les en-têtes des jours sous l'en-tête principal

            for day_num in range(days_in_month):
                current_day = first_day_of_month + timedelta(days=day_num)
                is_today = current_day.date() == datetime.now().date()
                color = self._highlightColor if is_today else None

                day_width = width / days_in_month
                day_x = x + day_num * day_width

                # Dessine "Ven 10", "Sam 11", etc.
                dw, dh = drawer.DrawSimpleDayHeader(
                    current_day,
                    day_x,
                    header_y,
                    day_width,
                    height, # Hauteur disponible restante
                    highlight=color
                )
                # self._headerBounds.append(...) # Si nécessaire pour la redimension des colonnes
                max_dy = max(max_dy, dh)

            h += max_dy # Ajouter la hauteur des en-têtes de jour à la hauteur totale

        log.debug(f"tkSchedulerPaint._paintMonthlyHeaders: Dimensions retournées: w={w}, h={h}")
        return w, h
    # La prochaine étape serait de connecter les actions de l'interface utilisateur
    # (boutons "Semaine", "Mois") pour changer l'attribut self._viewType
    # et appeler self.Refresh() afin de redessiner le canevas avec la nouvelle vue.

    def _paintPeriod(self, drawer, start, daysCount, x, y, width, height, highlight=None):
        """Effectue le rendu des plannings pour une période donnée."""
        end = start + timedelta(days=daysCount)

        schedules_in_period = self._getSchedInPeriod(self._schedules, start, end)
        blocks = self._splitSchedules(schedules_in_period)

        # Dessiner le fond des jours
        for dayN in range(daysCount):
            theDay = start + timedelta(days=dayN)
            is_today = theDay.date() == datetime.now().date()
            day_color = self._highlightColor if is_today else None
            drawer.DrawDayBackground(
                x + width / daysCount * dayN, y, width / daysCount, height, highlight=day_color
            )

        if blocks:
            dayWidth = width / len(blocks)
            for idx, block in enumerate(blocks):
                for schedule in block:
                    xx, yy, w, h = drawer.DrawScheduleVertical(
                        schedule, start, self._get_working_hours(),
                        x + dayWidth * idx, y, dayWidth, height
                    )
                    self._schedulesCoords.append(
                        (schedule, (xx, yy), (xx + w, yy + h))
                    )

        # Enregistrer les coordonnées pour la détection de clics
        nbHours = len(self._lstDisplayedHours)
        for dayN in range(daysCount):
            theDay = start + timedelta(days=dayN)
            for hour_idx, hour in enumerate(self._lstDisplayedHours):
                dt = theDay.replace(hour=hour.hour, minute=hour.minute, second=0)
                px = x + width * dayN / daysCount
                py = y + height * hour_idx / nbHours
                pw = width / daysCount
                ph = height / nbHours
                self._datetimeCoords.append((dt, (px, py), (px + pw, py + ph)))

        return width, height


    # --- Méthodes utilitaires ---

    def _get_working_hours(self):
        """Retourne les plages horaires de travail."""
        if self._showOnlyWorkHour:
            return [
                (self._startingHour, self._startingPauseHour),
                (self._endingPauseHour, self._endingHour),
            ]
        return [(self._startingHour, self._endingHour)]

    def Refresh(self):  # Remplace RefreshSchedule
        """Rafraîchit le canevas en redessinant tout."""
        log.info("tkSchedulerPaint.Refresh: Redessin du canevas.")
        self.DrawBuffer()

    def DrawBuffer(self):
        """Prépare et dessine le contenu dans le canevas."""
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1 or height <= 1:  # Ne rien dessiner si le canevas n'est pas visible
            return

        drawer = self._drawerClass(self.canvas, self._lstDisplayedHours)
        self.DoPaint(drawer, 0, 0, width, height)

    @staticmethod
    def _getSchedInPeriod(schedules, start, end):
        """Retourne les plannings qui intersectent la période donnée."""
        results = []
        for schedule in schedules:
            if schedule.start >= end or schedule.end <= start:
                continue

            newSchedule = schedule.Clone()
            newSchedule.clientdata = schedule # Garder une référence à l'original

            if newSchedule.start < start:
                newSchedule.start = Utils.copyDateTime(start)
            if newSchedule.end > end:
                newSchedule.end = Utils.copyDateTime(end)

            results.append(newSchedule)
        return results

    def _splitSchedules(self, schedules):
        """Sépare les plannings en groupes qui ne se chevauchent pas."""
        results = []
        schedules = sorted(schedules, key=lambda s: s.start)

        while schedules:
            current_column = []
            current_column.append(schedules.pop(0))
            last_schedule_in_column = current_column[0]

            remaining_schedules = []
            for schedule in schedules:
                if schedule.start >= last_schedule_in_column.end:
                    current_column.append(schedule)
                    last_schedule_in_column = schedule
                else:
                    remaining_schedules.append(schedule)

            results.append(current_column)
            schedules = remaining_schedules

        return results

    def _findSchedule(self, point):
        """Trouve le planning ou la date aux coordonnées données."""
        px, py = point
        for schedule, pMin, pMax in self._schedulesCoords:
            minX, minY = pMin
            maxX, maxY = pMax
            if minX <= px <= maxX and minY <= py <= maxY:
                return pMin, pMax, schedule.clientdata

        for dt, pMin, pMax in self._datetimeCoords:
            minX, minY = pMin
            maxX, maxY = pMax
            if minX <= px <= maxX and minY <= py <= maxY:
                return pMin, pMax, dt
        return None

    def _processEvt(self, event_name, point):
        """Génère un événement virtuel Tkinter."""
        found = self._findSchedule(point)
        if not found: return

        _, _, schedule_or_date = found

        # Pour passer des données complexes, on peut attacher des attributs à l'objet canevas
        if isinstance(schedule_or_date, tkSchedule):
            self.canvas.schedule_object = schedule_or_date
            self.canvas.date_object = None
        else:
            self.canvas.schedule_object = None
            self.canvas.date_object = schedule_or_date

        self.canvas.event_generate(event_name)

    # # --- Méthodes à implémenter pour les autres vues ---
    # def _paintWeekly(self, drawer, day, x, y, width, height):
    #     log.warning("_paintWeekly non implémenté")
    #     return width, height
    #
    # def _paintMonthly(self, drawer, day, x, y, width, height):
    #     log.warning("_paintMonthly non implémenté")
    #     return width, height