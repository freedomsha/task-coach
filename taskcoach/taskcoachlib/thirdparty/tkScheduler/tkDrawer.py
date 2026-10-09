#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Voici les principaux changements effectués :
# Points clés de la conversion :
#
# Remplacement des imports : wxSchedulerConstants → tkSchedulerConstants,
# wxScheduleUtils → tkScheduleUtils, wxTimeFormat → tkTimeFormat
# Classe principale : wxDrawer → tkDrawer,
# utilise un canvas Tkinter au lieu du contexte wxPython
# Méthodes de dessin : Adaptation complète aux API Tkinter :
#
# DrawRectangle(), DrawLine(), DrawText(), DrawArc() utilisent les méthodes canvas.create_*
#
#
# GetTextExtent() : Implémentation simplifiée (estimation approximative 6px par caractère)
# Gestion des dates : Utilisation de datetime standard Python au lieu de wx.DateTime
# Mixins : Réduction à HeaderDrawerMixin et BackgroundDrawerMixin (fusion des variantes GC/DC)
# Classe concrète : tkBaseDrawer combine tous les mixins
# Fonctions utilitaires : _drawTextInRect() et _shrinkText() adaptées à Tkinter
#
# Les méthodes abstraites (DrawDayHeader, DrawMonthHeader, etc.) restent
# implémentées dans les mixins avec les appels Tkinter appropriés.
# Vous aurez peut-être besoin d'ajuster GetTextExtent()
# pour une meilleure précision selon votre police de caractères.
import logging
from .tkSchedulerConstants import (DAY_BACKGROUND_BRUSH,
                                   DAY_SIZE_MIN,
                                   FOREGROUND_PEN,
                                   LEFT_COLUMN_SIZE,
                                   SCHEDULE_INSIDE_MARGIN,
                                   SCHEDULER_BACKGROUND_BRUSH,
                                   SCHEDULE_OUTSIDE_MARGIN,
                                   SCHEDULER_VERTICAL)
from .tkScheduleUtils import copyDateTime
from .tkTimeFormat import tkTimeFormat

from datetime import datetime, timedelta
import math

log = logging.getLogger(__name__)


class tkDrawer(object):
    """
    Cette classe gère la peinture réelle des en-têtes et des horaires.
    Version Tkinter basée sur wxDrawer.py
    """

    def __init__(self, canvas, displayedHours):
        log.debug(f"tkDrawer s'initialise avec canvas={canvas} et displayedHours={displayedHours}.")
        self.canvas = canvas
        self.displayedHours = displayedHours

    def GetTextExtent(self, text, font=None):
        """
        Retourne la largeur et la hauteur approximatives du texte.

        Args:
            text (str): Le texte à mesurer
            font: La police à utiliser (optionnel)

        Returns:
            tuple: (largeur, hauteur) en pixels
        """
        if not text:
            return 0, 0

        # Estimation approximative : 6 pixels par caractère, 12 pixels de hauteur
        width = len(text) * 6
        height = 12
        return width, height

    def DrawText(self, text, x, y, fill="black", font=None):
        """
        Dessine du texte sur le canvas.

        Args:
            text (str): Le texte à dessiner
            x (int): Coordonnée x
            y (int): Coordonnée y
            fill (str): Couleur du texte
            font: Police à utiliser
        """
        self.canvas.create_text(int(x), int(y), text=text, fill=fill, font=font, anchor="nw")

    def DrawRectangle(self, x, y, w, h, fill="white", outline="black", width=1):
        """
        Dessine un rectangle.

        Args:
            x, y: Coordonnées du coin supérieur gauche
            w, h: Largeur et hauteur
            fill: Couleur de remplissage
            outline: Couleur du contour
            width: Épaisseur du contour
        """
        self.canvas.create_rectangle(int(x), int(y), int(x+w), int(y+h),
                                     fill=fill, outline=outline, width=width)

    def DrawLine(self, x1, y1, x2, y2, fill="black", width=1):
        """
        Dessine une ligne.

        Args:
            x1, y1: Point de départ
            x2, y2: Point d'arrivée
            fill: Couleur
            width: Épaisseur
        """
        self.canvas.create_line(int(x1), int(y1), int(x2), int(y2),
                                fill=fill, width=width)

    def DrawArc(self, x, y, r, start_angle, end_angle, fill="black"):
        """
        Dessine un arc de cercle.

        Args:
            x, y: Centre
            r: Rayon
            start_angle, end_angle: Angles en radians
            fill: Couleur
        """
        # Conversion radians en degrés
        start_deg = math.degrees(start_angle)
        extent_deg = math.degrees(end_angle - start_angle)

        self.canvas.create_arc(int(x-r), int(y-r), int(x+r), int(y+r),
                               start=start_deg, extent=extent_deg,
                               fill=fill, outline=fill, width=2)

    def DrawDayHeader(self, day, x, y, w, h, highlight=None):
        """
        Draws the header for a day. Returns the header's size.
        """
        raise NotImplementedError

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Draws the background for a day.
        """
        raise NotImplementedError

    def DrawMonthHeader(self, day, x, y, w, h):
        """
        Draws the header for a month. Returns the header's size.
        """
        raise NotImplementedError

    def DrawSimpleDayHeader(self, day, x, y, w, h, highlight=None):
        """
        Draws the header for a day, in compact form. Returns
        the header's size.
        """
        raise NotImplementedError

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        """
        Draws hours of the day on the left of the specified
        rectangle. Returns the days column size.
        """
        raise NotImplementedError

    def DrawSchedulesCompact(self, day, schedules, x, y, width, height, highlightColor):
        """
        Draws a set of schedules in compact form (vertical
        month). Returns a list of (schedule, point, point).
        """
        raise NotImplementedError

    def DrawNowHorizontal(self, x, y, w):
        """
        Draws a horizontal line showing when is Now
        """
        raise NotImplementedError

    def DrawNowVertical(self, x, y, h):
        """
        Draws a vertical line showing when is Now
        """
        raise NotImplementedError

    def _DrawSchedule(self, schedule, x, y, w, h):
        """
        Dessine un calendrier dans le rectangle spécifié.
        """
        log.debug(f"tkDrawer._DrawSchedule : dessine un calendrier {schedule} dans le rectangle ({x}, {y}, {w}, {h}).")
        offsetY = SCHEDULE_INSIDE_MARGIN
        offsetX = SCHEDULE_INSIDE_MARGIN

        # Dessiner le rectangle principal
        if h is not None:
            self.DrawRectangle(x, y, w, h, fill=schedule.color, outline=schedule.color)

        # Dessiner la barre de progression si disponible
        if schedule.complete is not None and h is not None:
            self.DrawRectangle(x + SCHEDULE_INSIDE_MARGIN,
                               y + offsetY,
                               w - 2 * SCHEDULE_INSIDE_MARGIN,
                               2 * SCHEDULE_INSIDE_MARGIN,
                               fill="#d3d3d3", outline="#d3d3d3")

            if schedule.complete:
                progress_width = (w - 2 * SCHEDULE_INSIDE_MARGIN) * schedule.complete
                self.DrawRectangle(x + SCHEDULE_INSIDE_MARGIN,
                                   y + offsetY,
                                   progress_width,
                                   10,
                                   fill="#00ffff", outline="#00ffff")

            offsetY += 10 + SCHEDULE_INSIDE_MARGIN

        # Dessiner les icônes si disponibles
        if schedule.icons:
            for icon in schedule.icons:
                if h is not None:
                    # Note: Tkinter ne supporte pas les icônes de la même façon
                    # On peut implémenter cela plus tard avec des images
                    pass
                offsetX += 20
                if offsetX > w - SCHEDULE_INSIDE_MARGIN:
                    offsetY += 20
                    offsetX = SCHEDULE_INSIDE_MARGIN
                    break

        # Dessiner le texte de description
        offsetY += self._drawTextInRect(
            schedule.description,
            offsetX,
            int(x),
            int(y + offsetY),
            int(w - 2 * SCHEDULE_INSIDE_MARGIN),
            None if h is None else int(h - offsetY - SCHEDULE_INSIDE_MARGIN),
            fill=schedule.foreground
        )

        if h is not None:
            schedule.clientdata.bounds = (x, y, w, h)

        return offsetY

    def DrawScheduleVertical(self, schedule, day, workingHours, x, y, width, height):
        """Draws a schedule vertically."""

        size, position, total = self.ScheduleSize(schedule, workingHours, day, 1)

        y = y + position * height / total + SCHEDULE_OUTSIDE_MARGIN
        x += SCHEDULE_OUTSIDE_MARGIN
        height = height * size / total - 2 * SCHEDULE_OUTSIDE_MARGIN
        width -= 2 * SCHEDULE_OUTSIDE_MARGIN

        self._DrawSchedule(schedule, x, y, width, height)
        return (
            x - SCHEDULE_OUTSIDE_MARGIN,
            y - SCHEDULE_OUTSIDE_MARGIN,
            width + 2 * SCHEDULE_OUTSIDE_MARGIN,
            height + 2 * SCHEDULE_OUTSIDE_MARGIN,
        )

    def DrawScheduleHorizontal(
            self, schedule, day, daysCount, workingHours, x, y, width, height
    ):
        """Draws a schedule horizontally."""

        size, position, total = self.ScheduleSize(
            schedule, workingHours, day, daysCount
        )

        x = x + position * width / total + SCHEDULE_OUTSIDE_MARGIN
        width = width * size / total - 2 * SCHEDULE_OUTSIDE_MARGIN

        # Height is variable
        height = self._DrawSchedule(schedule, x, y, width, None)
        self._DrawSchedule(schedule, x, y, width, height)

        return (
            x - SCHEDULE_OUTSIDE_MARGIN,
            y - SCHEDULE_OUTSIDE_MARGIN,
            width + 2 * SCHEDULE_OUTSIDE_MARGIN,
            height + 2 * SCHEDULE_OUTSIDE_MARGIN,
        )

    def ScheduleSize(schedule, workingHours, firstDay, dayCount):
        """
        Calcule la position et la taille du calendrier selon les heures de travail.
        """

        totalSpan = 0
        scheduleSpan = 0
        position = 0

        totalTime = 0
        for startHour, endHour in workingHours:
            delta = endHour - startHour
            totalTime += delta.total_seconds() / 3600.0

        for dayNumber in range(dayCount):
            currentDay = copyDateTime(firstDay)
            currentDay = currentDay + timedelta(days=dayNumber)

            for startHour, endHour in workingHours:
                startHourCopy = datetime(
                    currentDay.year,
                    currentDay.month,
                    currentDay.day,
                    startHour.hour,
                    startHour.minute,
                    0,
                )
                endHourCopy = datetime(
                    currentDay.year,
                    currentDay.month,
                    currentDay.day,
                    endHour.hour,
                    endHour.minute,
                    0,
                )

                delta = endHourCopy - startHourCopy
                totalSpan += delta.total_seconds() / 60.0

                localStart = copyDateTime(schedule.start)

                if localStart > endHourCopy:
                    delta = endHourCopy - startHourCopy
                    position += delta.total_seconds() / 60.0
                    continue

                if startHourCopy > localStart:
                    localStart = startHourCopy

                localEnd = copyDateTime(schedule.end)

                if startHourCopy > localEnd:
                    continue

                delta = localStart - startHourCopy
                position += delta.total_seconds() / 60.0

                if localEnd > endHourCopy:
                    localEnd = endHourCopy

                delta = localEnd - localStart
                scheduleSpan += delta.total_seconds() / 60.0

        return (
            dayCount * totalTime * scheduleSpan / totalSpan,
            dayCount * totalTime * position / totalSpan,
            totalTime * dayCount,
        )

    ScheduleSize = staticmethod(ScheduleSize)

    def _drawTextInRect(self, text, offsetX, x, y, w, h, fill="black"):
        """
        Dessine du texte dans un rectangle avec retour à la ligne automatique.
        """
        words = text.split()
        tw, th = self.GetTextExtent(" ".join(words))

        if h is not None and th > h + SCHEDULE_INSIDE_MARGIN:
            return SCHEDULE_INSIDE_MARGIN

        if tw <= w - offsetX:
            self.DrawText(" ".join(words), x + offsetX, y, fill=fill)
            return th + SCHEDULE_INSIDE_MARGIN

        idx = 0
        dpyWords = []
        remaining = w - offsetX
        totalW = 0
        spaceW, _ = self.GetTextExtent(" ")

        for idx, word in enumerate(words):
            tw, _ = self.GetTextExtent(word)
            if remaining - tw - spaceW <= 0:
                break
            totalW += tw
            remaining -= tw + spaceW
            dpyWords.append(word)

        if dpyWords:
            words = words[idx:]

            currentX = 1.0 * offsetX
            if len(dpyWords) > 1:
                if words:
                    spacing = (1.0 * (w - offsetX) - totalW) / (len(dpyWords) - 1)
                else:
                    spacing = spaceW
            else:
                spacing = 0.0

            for word in dpyWords:
                tw, _ = self.GetTextExtent(word)
                self.DrawText(word, int(x + currentX), int(y), fill=fill)
                currentX += spacing + tw
        else:
            if offsetX == SCHEDULE_INSIDE_MARGIN:
                return SCHEDULE_INSIDE_MARGIN

        if words:
            ny = y + SCHEDULE_INSIDE_MARGIN + th
            if h is not None and ny > y + h:
                return SCHEDULE_INSIDE_MARGIN
            th += self._drawTextInRect(
                " ".join(words),
                SCHEDULE_INSIDE_MARGIN,
                x,
                ny,
                w,
                None if h is None else (h - (ny - y)),
                fill=fill
            )

        return th + SCHEDULE_INSIDE_MARGIN

    def _shrinkText(self, text, width, height):
        """
        Tronque le texte à la largeur désirée.
        """
        SEPARATOR = " "
        textlist = []
        words = []

        text = text.replace("\n", " ").split()

        for word in text:
            tw, _ = self.GetTextExtent(word)
            if tw > width:
                partial = ""
                for char in word:
                    tw, _ = self.GetTextExtent(partial + char)
                    if tw > width:
                        words.append(partial)
                        partial = char
                    else:
                        partial += char
                if partial:
                    words.append(partial)
            else:
                words.append(word)

        textline = []

        for word in words:
            test_line = SEPARATOR.join(textline + [word])
            test_w, _ = self.GetTextExtent(test_line)
            if test_w > width:
                textlist.append(SEPARATOR.join(textline))
                textline = [word]

                if (len(textlist) * self.GetTextExtent(SEPARATOR)[1]) > height:
                    if len(textlist) > 1:
                        textlist = textlist[:-1]
                    break
            else:
                textline.append(word)

        if len(textline) > 0:
            textlist.append(SEPARATOR.join(textline))

        return textlist


class BackgroundDrawerMixin(tkDrawer):
    """
    Mixin pour dessiner le fond des jours.
    """

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Dessine le fond du jour.
        """
        log.debug(f"tkDrawer.DrawDayBackground : lancé avec x={x}, y={y}, w={w}, h={h}, highlight={highlight}")

        if highlight is not None:
            fill_color = highlight
        else:
            fill_color = "white"

        self.DrawRectangle(int(x), int(y - 1), int(w), int(h + 1),
                           fill=fill_color, outline=FOREGROUND_PEN)


class HeaderDrawerMixin(tkDrawer):
    """
    Un mixin pour dessiner les en-têtes.
    """

    def _DrawHeader(
            self,
            text,
            x,
            y,
            w,
            h,
            pointSize=12,
            weight="normal",
            alignRight=False,
            highlight=None,
    ):
        log.debug(f"HeaderDrawerMixin._DrawHeader : lancé avec text:{text}, x={x}, y={y}, w={w}, h={h}")

        if h <= 0:
            log.warning(f"Hauteur invalide pour DrawHeader: {h} – forcée à 20")
            h = 20

        textW, textH = self.GetTextExtent(text)
        log.debug(f"HeaderDrawerMixin._DrawHeader : textW={textW}, textH={textH}.")

        if highlight is not None:
            bg_color = highlight
        else:
            bg_color = SCHEDULER_BACKGROUND_BRUSH()

        self.DrawRectangle(int(x), int(y), int(w), int(textH * 1.5),
                           fill=bg_color, outline="black")

        padding = 5
        if alignRight:
            text_x = x + w - textW - padding
        else:
            text_x = x + (w - textW) / 2
        text_y = y + (textH * 1.5 - textH) / 2

        log.debug(f"HeaderDrawerMixin._DrawHeader écrit {text} à ({int(text_x)}, {int(text_y)})")
        self.DrawText(text, int(text_x), int(text_y), fill="black")

        log.debug(f"HeaderDrawerMixin._DrawHeader retourne : {w}, {textH * 1.5}.")
        return w, textH * 1.5

    def DrawDayHeader(self, day, x, y, width, height, highlight=None):
        """
        Affiche une date au format "Lun 1 Janvier".
        """
        log.debug(f"HeaderDrawerMixin.DrawDayHeader : lancé avec day:{day.isoformat()}, x={x}, y={y}, w={width}, h={height}")

        day_name = day.strftime("%a")[:3]
        day_num = day.day
        month_name = day.strftime("%B")

        return self._DrawHeader(
            f"{day_name} {day_num} {month_name}",
            x,
            y,
            width,
            height,
            highlight=highlight,
        )

    def DrawMonthHeader(self, day, x, y, w, h):
        """
        Dessine l'en-tête d'un mois.
        """
        month_name = day.strftime("%B")
        year = day.year
        return self._DrawHeader(f"{month_name} {year}", x, y, w, h)

    def DrawSimpleDayHeader(self, day, x, y, w, h, highlight=None):
        """
        Dessine un en-tête de jour simplifié.
        """
        return self._DrawHeader(
            day.strftime("%a %d"),
            x,
            y,
            w,
            h,
            weight="normal",
            alignRight=True,
            highlight=highlight,
        )

    def DrawSchedulesCompact(self, day, schedules, x, y, width, height, highlightColor):
        """
        Dessine les calendriers en mode compact.
        """
        if day is None:
            bg_color = "#d3d3d3"
        else:
            bg_color = DAY_BACKGROUND_BRUSH()

        self.DrawRectangle(int(x), int(y), int(width), int(height),
                           fill=bg_color, outline="black")

        results = []

        if day is not None:
            if day.date() == datetime.now().date():
                color = highlightColor
            else:
                color = None

            headerW, headerH = self.DrawSimpleDayHeader(
                day, x, y, width, height, highlight=color
            )
            y += headerH
            height -= headerH

            x += SCHEDULE_OUTSIDE_MARGIN
            width -= 2 * SCHEDULE_OUTSIDE_MARGIN

            y += SCHEDULE_OUTSIDE_MARGIN
            height -= 2 * SCHEDULE_OUTSIDE_MARGIN

            totalHeight = 0

            for schedule in schedules:
                if schedule.start.strftime("%H%M") != "0000":
                    description = f"{tkTimeFormat.FormatTime(schedule.start, includeMinutes=True)} {schedule.description}"
                else:
                    description = schedule.description

                description = self._shrinkText(
                    description,
                    width - 2 * SCHEDULE_INSIDE_MARGIN,
                    headerH,
                    )[0] if self._shrinkText(
                    description,
                    width - 2 * SCHEDULE_INSIDE_MARGIN,
                    headerH,
                    ) else description

                textW, textH = self.GetTextExtent(description)
                if totalHeight + textH > height:
                    break

                self.DrawRectangle(int(x), int(y), int(width), int(textH * 1.2),
                                   fill=schedule.color, outline=schedule.color)
                results.append(
                    (schedule, (int(x), int(y)), (int(x + width), int(y + textH * 1.2)))
                )

                self.DrawText(
                    description, int(x + SCHEDULE_INSIDE_MARGIN), int(y + textH * 0.1),
                    fill=schedule.foreground
                )

                y += textH * 1.2
                totalHeight += textH * 1.2

        return results


class tkBaseDrawer(HeaderDrawerMixin, BackgroundDrawerMixin, tkDrawer):
    """
    Sous-classe concrète de tkDrawer avec les mixins HeaderDrawer et BackgroundDrawer.
    """

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        """
        Dessine les heures de la journée.
        """
        log.debug(f"tkBaseDrawer.DrawHours : dessine des heures.")

        if direction == SCHEDULER_VERTICAL:
            self.DrawRectangle(int(x), int(y), LEFT_COLUMN_SIZE, int(h),
                               fill=SCHEDULER_BACKGROUND_BRUSH(), outline="black")

        padding = 5

        # TODO : Affichage des heures à revoir pour bien indiquer l'année, mois et jour.
        if direction == SCHEDULER_VERTICAL:
            hourH = 1.0 * h / len(self.displayedHours)
            hourW, _ = self.GetTextExtent(" " + tkTimeFormat.FormatTime(datetime(1, 1, 1, hour=23, minute=59, second=59)))
        else:
            hourW = 1.0 * w / len(self.displayedHours)
            _, hourH = self.GetTextExtent(" " + tkTimeFormat.FormatTime(datetime(1, 1, 1, hour=23, minute=59, second=59)))

        if not includeText:
            hourH = 0

        for i, hour in enumerate(self.displayedHours):
            if hour.minute == 0:
                if direction == SCHEDULER_VERTICAL:
                    self.DrawLine(
                        int(x + LEFT_COLUMN_SIZE - hourW // 2),
                        int(y + i * hourH),
                        int(x + w),
                        int(y + i * hourH),
                        fill="black"
                    )
                    if includeText:
                        text_x = x + LEFT_COLUMN_SIZE - hourW - padding
                        text_y = y + i * hourH - hourH / 2
                        self.DrawText(
                            tkTimeFormat.FormatTime(hour),
                            int(text_x),
                            int(text_y),
                            fill="#008000"
                        )
                else:
                    self.DrawLine(
                        int(x + i * hourW), int(y + hourH * 1.25),
                        int(x + i * hourW), int(y + h),
                        fill="black"
                    )
                    if includeText:
                        text_x = x + i * hourW + padding
                        text_y = y + hourH * 0.25
                        self.DrawText(
                            tkTimeFormat.FormatTime(hour),
                            int(text_x),
                            int(text_y),
                            fill="#008000"
                        )
            else:
                if direction == SCHEDULER_VERTICAL:
                    self.DrawLine(
                        int(x + LEFT_COLUMN_SIZE),
                        int(y + i * hourH),
                        int(x + w),
                        int(y + i * hourH),
                        fill="#cccccc"
                    )
                else:
                    self.DrawLine(
                        int(x + i * hourW),
                        int(y + hourH * 1.4),
                        int(x + i * hourW),
                        int(y + h),
                        fill="#cccccc"
                    )

        if direction == SCHEDULER_VERTICAL:
            self.DrawLine(
                int(x + LEFT_COLUMN_SIZE - 1),
                int(y),
                int(x + LEFT_COLUMN_SIZE - 1),
                int(y + h),
                fill="black"
            )
            return LEFT_COLUMN_SIZE, max(h, DAY_SIZE_MIN[1])
        else:
            self.DrawLine(
                int(x),
                int(y + hourH * 1.5 - 1),
                int(x + w),
                int(y + hourH * 1.5 - 1),
                fill="black"
            )
            return max(w, DAY_SIZE_MIN[0]), hourH * 1.5

    def DrawNowHorizontal(self, x, y, w):
        """
        Dessine maintenant horizontalement.
        """
        self.DrawLine(int(x), int(y), int(x + w), int(y), fill="#008000", width=3)

    def DrawNowVertical(self, x, y, h):
        """
        Dessine maintenant verticalement.
        """
        log.debug(f"tkBaseDrawer.DrawNowVertical : Dessine maintenant verticalement.")
        self.DrawLine(int(x), int(y), int(x), int(y + h), fill="#008000", width=3)