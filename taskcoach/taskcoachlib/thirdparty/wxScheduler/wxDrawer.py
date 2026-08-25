#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# from .wxSchedulerConstants import *
from .wxSchedulerConstants import (
    DAY_BACKGROUND_BRUSH,
    DAY_SIZE_MIN,
    FOREGROUND_PEN,
    LEFT_COLUMN_SIZE,
    SCHEDULE_INSIDE_MARGIN,
    SCHEDULER_BACKGROUND_BRUSH,
    SCHEDULE_OUTSIDE_MARGIN,
    wxSCHEDULER_VERTICAL,
)

# from . import wxSchedulerConstants as wxSC
from .wxScheduleUtils import copyDateTime
from .wxTimeFormat import wxTimeFormat

import wx
import math

log = logging.getLogger(__name__)


class wxDrawer(object):
    """
    Cette classe gère la peinture réelle des en-têtes et des horaires.
    """

    # Définissez ceci sur true si vous voulez que vos méthodes soient
    # transmises à un wx.graphicsContext au lieu de WX.DC.
    use_gc = False

    def __init__(self, context, displayedHours):
        log.debug(
            f"wxDrawer s'initialise avec context={context} et displayedHours={displayedHours}."
        )
        self.context = context
        self.displayedHours = displayedHours

    def AdjustFontForHeight(self, font, height):
        pointSize = 18
        while True:
            font.SetPointSize(pointSize)
            _, th = self.context.GetTextExtent(
                " "
                + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
            )
            if th <= height:
                return
            pointSize -= 1
            # if pointSize == 1:
            if pointSize <= 1:
                return  # Hum

    def AdjustFontForWidth(self, font, width):
        pointSize = 18
        while True:
            font.SetPointSize(pointSize)
            self.context.SetFont(font)
            tw, _ = self.context.GetTextExtent(
                " "
                + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
            )
            if tw <= width:
                return
            pointSize -= 1
            # if pointSize == 1:
            if pointSize <= 1:
                return  # Hum

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

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
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
        log.debug(
            f"wxDrawer._DrawSchedule : self={self.__class__.__name__} dessine un calendrier {schedule} dans le rectangle ({x}, {y}, {w}, {h})."
        )
        # Ensure coordinates are integers for wxPython compatibility
        x, y, w = int(x), int(y), int(w)
        if h is not None:
            h = int(h)

        offsetY = SCHEDULE_INSIDE_MARGIN
        offsetX = SCHEDULE_INSIDE_MARGIN

        if self.use_gc:
            if h is not None:
                pen = wx.Pen(schedule.color)
                self.context.SetPen(self.context.CreatePen(pen))

                brush = self.context.CreateLinearGradientBrush(
                    x,
                    y,
                    x + w,
                    y + h,
                    schedule.color,
                    SCHEDULER_BACKGROUND_BRUSH(),
                )
                self.context.SetBrush(brush)
                self.context.DrawRoundedRectangle(
                    x, y, w, h, SCHEDULE_INSIDE_MARGIN
                )

            if schedule.complete is not None:
                if h is not None:
                    self.context.SetPen(
                        self.context.CreatePen(
                            wx.Pen(
                                wx.SystemSettings.GetColour(
                                    wx.SYS_COLOUR_SCROLLBAR
                                )
                            )
                        )
                    )
                    self.context.SetBrush(
                        self.context.CreateBrush(
                            wx.Brush(
                                wx.SystemSettings.GetColour(
                                    wx.SYS_COLOUR_SCROLLBAR
                                )
                            )
                        )
                    )
                    self.context.DrawRoundedRectangle(
                        x + SCHEDULE_INSIDE_MARGIN,
                        y + offsetY,
                        w - 2 * SCHEDULE_INSIDE_MARGIN,
                        2 * SCHEDULE_INSIDE_MARGIN,
                        SCHEDULE_INSIDE_MARGIN,
                    )

                    if schedule.complete:
                        self.context.SetBrush(
                            self.context.CreateLinearGradientBrush(
                                x + SCHEDULE_INSIDE_MARGIN,
                                y + offsetY,
                                x
                                + (w - 2 * SCHEDULE_INSIDE_MARGIN)
                                * schedule.complete,
                                y + offsetY + 10,
                                wx.Colour(0, 0, 255),
                                wx.Colour(0, 255, 255),
                            )
                        )
                        self.context.DrawRoundedRectangle(
                            x + SCHEDULE_INSIDE_MARGIN,
                            y + offsetY,
                            (w - 2 * SCHEDULE_INSIDE_MARGIN)
                            * schedule.complete,
                            10,
                            5,
                        )

                offsetY += 10 + SCHEDULE_INSIDE_MARGIN

            if schedule.icons:
                for icon in schedule.icons:
                    if h is not None:
                        bitmap = wx.ArtProvider.GetBitmap(
                            icon, wx.ART_FRAME_ICON, (16, 16)
                        )
                        self.context.DrawBitmap(
                            bitmap, int(x + offsetX), int(y + offsetY), 16, 16
                        )
                    offsetX += 20
                    if offsetX > w - SCHEDULE_INSIDE_MARGIN:
                        offsetY += 20
                        offsetX = SCHEDULE_INSIDE_MARGIN
                        break

            font = schedule.font
            self.context.SetFont(font, schedule.foreground)
            offsetY += self._drawTextInRect(
                self.context,
                schedule.description,
                offsetX,
                int(x),
                int(y + offsetY),
                int(w - 2 * SCHEDULE_INSIDE_MARGIN),
                (
                    None
                    if h is None
                    else int(h - offsetY - SCHEDULE_INSIDE_MARGIN)
                ),
            )
        else:
            if h is not None:
                self.context.SetBrush(wx.Brush(schedule.color))
                self.context.DrawRectangle(int(x), int(y), int(w), int(h))

            if schedule.complete is not None:
                if h is not None:
                    self.context.SetPen(
                        wx.Pen(
                            wx.SystemSettings.GetColour(
                                wx.SYS_COLOUR_SCROLLBAR
                            )
                        )
                    )
                    self.context.SetBrush(
                        wx.Brush(
                            wx.SystemSettings.GetColour(
                                wx.SYS_COLOUR_SCROLLBAR
                            )
                        )
                    )
                    self.context.DrawRectangle(
                        int(x + SCHEDULE_INSIDE_MARGIN),
                        int(y + offsetY),
                        int(w - 2 * SCHEDULE_INSIDE_MARGIN),
                        10,
                    )
                    if schedule.complete:
                        self.context.SetPen(
                            wx.Pen(
                                wx.SystemSettings.GetColour(
                                    wx.SYS_COLOUR_HIGHLIGHT
                                )
                            )
                        )
                        self.context.SetBrush(
                            wx.Brush(
                                wx.SystemSettings.GetColour(
                                    wx.SYS_COLOUR_HIGHLIGHT
                                )
                            )
                        )
                        self.context.DrawRectangle(
                            int(x + SCHEDULE_INSIDE_MARGIN),
                            int(y + offsetY),
                            int(
                                (w - 2 * SCHEDULE_INSIDE_MARGIN)
                                * schedule.complete
                            ),
                            10,
                        )

                offsetY += 10 + SCHEDULE_INSIDE_MARGIN

            if schedule.icons:
                for icon in schedule.icons:
                    if h is not None:
                        bitmap = wx.ArtProvider.GetBitmap(
                            icon, wx.ART_FRAME_ICON, (16, 16)
                        )
                        self.context.DrawBitmap(
                            bitmap, int(x + offsetX), int(y + offsetY), True
                        )
                    offsetX += 20
                    if offsetX > w - SCHEDULE_INSIDE_MARGIN:
                        offsetY += 20
                        offsetX = SCHEDULE_INSIDE_MARGIN
                        break

            font = schedule.font
            self.context.SetFont(font)

            self.context.SetTextForeground(schedule.foreground)
            offsetY += self._drawTextInRect(
                self.context,
                schedule.description,
                offsetX,
                x,
                y + offsetY,
                w - 2 * SCHEDULE_INSIDE_MARGIN,
                None if h is None else h - offsetY - SCHEDULE_INSIDE_MARGIN,
            )

        if h is not None:
            schedule.clientdata.bounds = (x, y, w, h)

        return offsetY

    def DrawScheduleVertical(
        self, schedule, day, workingHours, x, y, width, height
    ):
        """Draws a schedule vertically."""

        size, position, total = self.ScheduleSize(
            schedule, workingHours, day, 1
        )

        if self.use_gc:
            font = schedule.font
            self.context.SetFont(font, schedule.color)
        else:
            font = schedule.font
            self.context.SetTextForeground(schedule.foreground)
            self.context.SetFont(font)

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

        if self.use_gc:
            font = schedule.font
            self.context.SetFont(font, schedule.color)
        else:
            font = schedule.font
            self.context.SetTextForeground(schedule.color)
            self.context.SetFont(font)

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
        This convenience  static method computes  the position
        and size  size of the  schedule in the  direction that
        represent time,  according to a set  of working hours.
        The workingHours  parameter is  a list of  2-tuples of
        wx.DateTime  objects   defining  intervals  which  are
        indeed worked.  startPeriod and endPeriod  delimit the
        period.
        """

        totalSpan = 0
        scheduleSpan = 0
        position = 0

        totalTime = 0
        for startHour, endHour in workingHours:
            totalTime += (
                copyDateTime(endHour).Subtract(startHour).GetMinutes() / 60.0
            )

        for dayNumber in range(dayCount):
            currentDay = copyDateTime(firstDay)
            # currentDay.AddDS(wx.DateSpan(days=dayNumber))
            currentDay += wx.DateSpan(days=dayNumber)

            for startHour, endHour in workingHours:
                startHourCopy = wx.DateTimeFromDMY(
                    currentDay.GetDay(),
                    currentDay.GetMonth(),
                    currentDay.GetYear(),
                    startHour.GetHour(),
                    startHour.GetMinute(),
                    0,
                )
                endHourCopy = wx.DateTimeFromDMY(
                    currentDay.GetDay(),
                    currentDay.GetMonth(),
                    currentDay.GetYear(),
                    endHour.GetHour(),
                    endHour.GetMinute(),
                    0,
                )

                totalSpan += endHourCopy.Subtract(startHourCopy).GetMinutes()

                localStart = copyDateTime(schedule.start)

                if localStart.IsLaterThan(endHourCopy):
                    position += endHourCopy.Subtract(
                        startHourCopy
                    ).GetMinutes()
                    continue

                if startHourCopy.IsLaterThan(localStart):
                    localStart = startHourCopy

                localEnd = copyDateTime(schedule.end)

                if startHourCopy.IsLaterThan(localEnd):
                    continue

                position += localStart.Subtract(startHourCopy).GetMinutes()

                if localEnd.IsLaterThan(endHourCopy):
                    localEnd = endHourCopy

                scheduleSpan += localEnd.Subtract(localStart).GetMinutes()

        return (
            dayCount * totalTime * scheduleSpan / totalSpan,
            dayCount * totalTime * position / totalSpan,
            totalTime * dayCount,
        )

    ScheduleSize = staticmethod(ScheduleSize)

    def _drawTextInRect(self, context, text, offsetX, x, y, w, h):
        words = text.split()
        tw, th = context.GetTextExtent(" ".join(words))

        if h is not None and th > h + SCHEDULE_INSIDE_MARGIN:
            return SCHEDULE_INSIDE_MARGIN

        if tw <= w - offsetX:
            context.DrawText(" ".join(words), x + offsetX, y)
            return th + SCHEDULE_INSIDE_MARGIN

        idx = 0
        dpyWords = []
        remaining = w - offsetX
        totalW = 0
        spaceW, _ = context.GetTextExtent(" ")

        for idx, word in enumerate(words):
            tw, _ = context.GetTextExtent(word)
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
                    spacing = (1.0 * (w - offsetX) - totalW) / (
                        len(dpyWords) - 1
                    )
                else:
                    spacing = spaceW
            else:
                spacing = 0.0

            for word in dpyWords:
                tw, _ = context.GetTextExtent(word)
                context.DrawText(word, int(x + currentX), int(y))
                currentX += spacing + tw
        else:
            if offsetX == SCHEDULE_INSIDE_MARGIN:
                # Can't display anything...
                return SCHEDULE_INSIDE_MARGIN

        if words:
            ny = y + SCHEDULE_INSIDE_MARGIN + th
            if h is not None and ny > y + h:
                return SCHEDULE_INSIDE_MARGIN
            th += self._drawTextInRect(
                context,
                " ".join(words),
                SCHEDULE_INSIDE_MARGIN,
                x,
                ny,
                w,
                (
                    None if h is None else (h - (ny - y))
                ),  # Cannot find reference '-' in 'None'
            )

        return th + SCHEDULE_INSIDE_MARGIN

    def _shrinkText(self, dc, text, width, height):
        """
        Truncate text at desired width
        """
        MORE_SIGNAL = "..."  # F841 Local variable `MORE_SIGNAL` is assigned to but never used
        SEPARATOR = " "

        textlist = list()  # List returned by this method
        words = list()  # Wordlist for itermediate elaboration

        # Split text in single words and split words when yours width is over
        # available width
        text = text.replace("\n", " ").split()

        for word in text:
            if dc.GetTextExtent(word)[0] > width:
                # Cycle trought every char until word width is minor or equal
                # to available width
                partial = ""

                for char in word:
                    if dc.GetTextExtent(partial + char)[0] > width:
                        words.append(partial)
                        partial = char
                    else:
                        partial += char
            else:
                words.append(word)

        # Create list of text lines for output
        textline = list()

        for word in words:
            if dc.GetTextExtent(SEPARATOR.join(textline + [word]))[0] > width:
                textlist.append(SEPARATOR.join(textline))
                textline = [word]

                # Break if there's no vertical space available
                if (len(textlist) * dc.GetTextExtent(SEPARATOR)[0]) > height:
                    # Must exists almost one line of description
                    if len(textlist) > 1:
                        textlist = textlist[:-1]

                    break
            else:
                textline.append(word)

        # Add remained words to text list
        if len(textline) > 0:
            textlist.append(SEPARATOR.join(textline))

        return textlist


# class BackgroundDrawerDCMixin(wxDrawer, wx.DC):
class BackgroundDrawerDCMixin(wxDrawer, wx.GCDC):
    """
    Mixin to draw day background with a DC.
    """

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Dessine le fond du jour.

        Args:
            x:
            y:
            w:
            h:
            highlight:

        Returns:

        """
        log.debug(
            f"wxDrawer.DrawDayBackground : lancé avec x={x}, y={y}, w={w}, h={h}, highlight={highlight}"
        )
        if highlight is not None:
            self.context.SetBrush(wx.Brush(highlight))
            # self.context.SetBackground(wx.Brush(highlight))
        else:
            self.context.SetBrush(wx.TRANSPARENT_BRUSH)
            # self.context.SetBackground(wx.TRANSPARENT_BRUSH)

        self.context.SetPen(FOREGROUND_PEN)

        self.context.DrawRectangle(int(x), int(y - 1), int(w), int(h + 1))


# class HeaderDrawerDCMixin(wxDrawer, wx.DC):
# class HeaderDrawerDCMixin(wxDrawer):
class HeaderDrawerDCMixin(wxDrawer, wx.GCDC):
    """
    A mixin to draw headers with a regular DC.
    """

    def _DrawHeader(
        self,
        text,
        x,
        y,
        w,
        h,
        pointSize=12,
        weight=wx.FONTWEIGHT_BOLD,
        alignRight=False,
        highlight=None,
    ):
        log.debug(
            "HeaderDrawerDCMixin._DrawHeader : lancé avec text:%s, x=%s, y=%s, w=%s, h=%s, pointSize=%s, weight=%s, alignRight=%s et highlight=%s",
            text,
            x,
            y,
            w,
            h,
            pointSize,
            weight,
            alignRight,
            highlight,
        )
        # Coordonnées inadaptées ? :
        if h <= 0:
            log.warning(
                "Hauteur invalide pour DrawHeader: %s — forcée à 20", h
            )
            h = 20

        # x = int(x)
        # y = int(y)
        # w = int(w)
        # h = int(h)
        font = self.context.GetFont()  # police trop grande ou non appliquée ?
        font.SetPointSize(pointSize)
        font.SetWeight(weight)
        self.context.SetFont(
            font
        )  # invalide ? Si le DC ou GC n’est pas bien configuré !
        self.context.SetTextForeground(
            wx.RED
        )  # Test S'assurer que le texte est rouge.
        log.debug(
            "font=%s avec pointSize=%s, family=%s, weight=%s",
            font.GetNativeFontInfoDesc(),
            font.GetPointSize(),
            font.GetFamily(),
            font.GetWeight(),
        )

        textW, textH = self.context.GetTextExtent(text)
        log.debug(
            f"HeaderDrawerDCMixin._DrawHeader : textW={textW}, textH={textH}."
        )

        # !!! Si le fond est blanc et le texte aussi -> invisible !!!:
        if highlight is not None:
            self.context.SetBrush(wx.Brush(highlight))
        else:
            self.context.SetBrush(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))

        log.debug(
            f"HeaderDrawerDCMixin._DrawHeader : dessine un rectangle ({x}, {y}, {w}, {textH * 1.5})."
        )
        self.context.DrawRectangle(int(x), int(y), int(w), int(textH * 1.5))

        # C’est ici que la chaîne contenant le jour et la date est affichée sur le calendrier.:
        # self.context.SetTextForeground(wx.BLACK)  # C'est ici que l'on règle le texte en noir !

        # Calcul de la position du texte
        padding = 5  # Marge intérieure
        if alignRight:
            text_x = x + w - textW - padding
        else:
            text_x = x + (w - textW) / 2
        text_y = (
            y + (textH * 1.5 - textH) / 2
        )  # Centrage vertical dans la hauteur de l'en-tête

        # if alignRight:
        #     log.debug(f"HeaderDrawerDCMixin._DrawHeader écrit {text} avec alignRight ici : ({int(x + w - textW * 1.5)}, {int(y + textH * 0.25)})")
        #     self.context.DrawText(text, int(x - textW * 1.5), int(y + textH * 0.25))
        # else:
        #     log.debug(f"HeaderDrawerDCMixin._DrawHeader écrit {text} sans alignRight ici : ({int(x + w - textW * 1.5)}, {int(y + textH * 0.25)})")
        #     self.context.DrawText(text, int((x - textW) / 2), int(y + textH * 0.25))

        log.debug(
            f"HeaderDrawerDCMixin._DrawHeader écrit {text} à ({int(text_x)}, {int(text_y)})"
        )
        self.context.DrawText(text, int(text_x), int(text_y))

        log.debug(
            f"HeaderDrawerDCMixin._DrawHeader retourne : {w}, {textH * 1.5}."
        )
        return w, textH * 1.5
        # return max(1, int(w)), max(0, int(textH * 1.5))

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
        # x = int(x)
        # y = int(y)
        # width = int(width)
        # height = int(height)
        if day is None:
            self.context.SetBrush(wx.LIGHT_GREY_BRUSH)
        else:
            self.context.SetBrush(wx.Brush(DAY_BACKGROUND_BRUSH()))

        self.context.DrawRectangle(int(x), int(y), int(width), int(height))

        results = []

        if day is not None:
            if day.IsSameDate(wx.DateTime.Now()):
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

            self.context.SetPen(FOREGROUND_PEN)

            totalHeight = 0

            for schedule in schedules:
                if schedule.start.Format("%H%M") != "0000":
                    # description = "%s %s" % (
                    #     wxTimeFormat.FormatTime(schedule.start, includeMinutes=True),
                    #     schedule.description,
                    # )
                    # description = f"{wxTimeFormat.FormatTime(self, schedule.start, includeMinutes=True)} {schedule.description}"
                    description = f"{wxTimeFormat.FormatTime(schedule.start, includeMinutes=True)} {schedule.description}"
                else:
                    description = schedule.description
                description = self._shrinkText(
                    self.context,
                    description,
                    width - 2 * SCHEDULE_INSIDE_MARGIN,
                    headerH,
                )[0]

                textW, textH = self.context.GetTextExtent(description)
                if totalHeight + textH > height:
                    break

                self.context.SetBrush(wx.Brush(schedule.color))
                self.context.DrawRectangle(
                    int(x), int(y), int(width), int(textH * 1.2)
                )
                results.append(
                    (
                        schedule,
                        wx.Point(int(x), int(y)),
                        wx.Point(int(x + width), int(y + textH * 1.2)),
                    )
                )

                self.context.SetTextForeground(schedule.foreground)
                self.context.DrawText(
                    description,
                    int(x + SCHEDULE_INSIDE_MARGIN),
                    int(y + textH * 0.1),
                )

                y += textH * 1.2
                totalHeight += textH * 1.2

        return results


class BackgroundDrawerGCMixin(wxDrawer):
    """
    Mixin to draw day background with a GC.
    """

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        if highlight is not None:
            self.context.SetBrush(
                self.context.CreateLinearGradientBrush(
                    x,
                    y,
                    x + w,
                    y + h,
                    wx.Colour(128, 128, 128, 128),
                    wx.Colour(
                        highlight.Red(),
                        highlight.Green(),
                        highlight.Blue(),
                        128,
                    ),
                )
            )
        else:
            self.context.SetBrush(
                self.context.CreateBrush(wx.TRANSPARENT_BRUSH)
            )

        self.context.SetPen(self.context.CreatePen(FOREGROUND_PEN))

        self.context.DrawRectangle(int(x), int(y - 1), int(w), int(h + 1))


class HeaderDrawerGCMixin(wxDrawer):
    """
    A mixin to draw headers with a GraphicsContext.
    """

    def _DrawHeader(
        self,
        text,
        x,
        y,
        w,
        h,
        pointSize=12,
        weight=wx.FONTWEIGHT_BOLD,
        alignRight=False,
        highlight=None,
    ):
        log.debug(
            f"HeaderDrawerGCMixin._DrawHeader : Lancé par self={self.__class__.__name__} avec text, x={x}, y={y}, w={w}, h={h}, pointSize=12, weight=wx.FONTWEIGHT_BOLD, alignRight=False, highlight=None,"
        )
        font = wx.NORMAL_FONT
        fsize = font.GetPointSize()
        fweight = font.GetWeight()

        try:
            font.SetPointSize(pointSize)
            font.SetWeight(weight)
            self.context.SetFont(font, wx.BLACK)

            textW, textH = self.context.GetTextExtent(text)
            log.debug(
                f"HeaderDrawerGCMixin._DrawHeader : textW={textW} et textH={textH}."
            )

            x1 = x
            y1 = y
            x2 = x + w
            y2 = y + textH * 1.5  # Hauteur de l'en-tête

            if highlight is not None:
                self.context.SetBrush(
                    self.context.CreateLinearGradientBrush(
                        x1, y1, x2, y2, wx.Colour(128, 128, 128), highlight
                    )
                )
            else:
                self.context.SetBrush(
                    self.context.CreateLinearGradientBrush(
                        x1,
                        y1,
                        x2,
                        y2,
                        wx.Colour(128, 128, 128),
                        SCHEDULER_BACKGROUND_BRUSH(),
                    )
                )
            self.context.DrawRectangle(
                int(x1), int(y1), int(x2 - x1), int(y2 - y1)
            )

            # Calcul de la position du texte
            padding = 5  # Marge intérieure
            if alignRight:
                newx = x + w - 1.5 * textW
                text_x = x + w - textW - padding
                newy = y + textH * 0.25
                log.debug(
                    f"HeaderDrawerGCMixin._DrawHeader : Dessine un texte à x={newx} et y={newy}"
                )
                # self.context.DrawText(text, int(x + w - 1.5 * textW), int(y + textH * 0.25))
            else:
                newx = x + (w - textW) / 2
                text_x = newx
                newy = y + textH * 0.25
                log.debug(
                    f"HeaderDrawerGCMixin._DrawHeader : Dessine un texte à x={newx} et y={newy}"
                )
                # self.context.DrawText(text, int(x + (w - textW) / 2), int(y + textH * 0.25))
            text_y = (
                y + (textH * 1.5 - textH) / 2
            )  # Centrage vertical dans la hauteur de l'en-tête

            log.debug(
                f"HeaderDrawerDCMixin._DrawHeader écrit {text} à ({int(text_x)}, {int(text_y)})"
            )
            self.context.DrawText(text, int(text_x), int(text_y))

            log.debug(
                f"HeaderDrawerGCMixin._DrawHeader : retourne w={w}, h={textH * 1,5}"
            )
            return w, textH * 1.5
            # return max(1, int(w)), max(0, int(textH * 1.5))
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
        if day is None:
            brush = self.context.CreateLinearGradientBrush(
                x,
                y,
                x + width,
                y + height,
                wx.BLACK,
                SCHEDULER_BACKGROUND_BRUSH(),
            )
        else:
            brush = self.context.CreateLinearGradientBrush(
                x,
                y,
                x + width,
                y + height,
                wx.LIGHT_GREY,
                DAY_BACKGROUND_BRUSH(),
            )

        self.context.SetBrush(brush)
        self.context.DrawRectangle(int(x), int(y), int(width), int(height))

        font = wx.NORMAL_FONT
        fsize = font.GetPointSize()
        fweight = font.GetWeight()

        try:
            font.SetPointSize(10)
            font.SetWeight(wx.FONTWEIGHT_NORMAL)

            results = []

            if day is not None:
                if day.IsSameDate(wx.DateTime.Now()):
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

                self.context.SetPen(FOREGROUND_PEN)

                totalHeight = 0

                for schedule in schedules:
                    if schedule.start.Format("%H%M") != "0000":
                        # description = "%s %s" % (
                        #     wxTimeFormat.FormatTime(
                        #         schedule.start, includeMinutes=True
                        #     ),
                        #     schedule.description,
                        # )
                        # description = f"{wxTimeFormat.FormatTime(self, schedule.start, includeMinutes=True)} {schedule.description}"
                        description = f"{wxTimeFormat.FormatTime(schedule.start, includeMinutes=True)} {schedule.description}"
                    else:
                        description = schedule.description
                    description = self._shrinkText(
                        self.context,
                        description,
                        width - 2 * SCHEDULE_INSIDE_MARGIN,
                        headerH,
                    )[0]

                    textW, textH = self.context.GetTextExtent(description)
                    if totalHeight + textH > height:
                        break

                    brush = self.context.CreateLinearGradientBrush(
                        x,
                        y,
                        x + width,
                        y + height,
                        schedule.color,
                        DAY_BACKGROUND_BRUSH(),
                    )
                    self.context.SetBrush(brush)
                    self.context.DrawRoundedRectangle(
                        int(x),
                        int(y),
                        int(width),
                        int(textH * 1.2, 1.0 * textH / 2),
                    )
                    results.append(
                        (
                            schedule,
                            wx.Point(int(x), int(y)),
                            wx.Point(int(x + width), int(y + textH * 1.2)),
                        )
                    )

                    self.context.SetFont(schedule.font, schedule.foreground)
                    self.context.DrawText(
                        description,
                        int(x + SCHEDULE_INSIDE_MARGIN),
                        int(y + textH * 0.1),
                    )

                    y += textH * 1.2
                    totalHeight += textH * 1.2

            return results
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)


class HeaderDrawerMixin(HeaderDrawerDCMixin):
    """
    A mixin that draws header using the _DrawHeader method.
    """

    def DrawDayHeader(self, day, x, y, width, height, highlight=None):
        """
        Cela affiche une date dans le format "Lun 1 Janvier" en appelant ensuite _DrawHeader.

        Args:
            day:
            x:
            y:
            width:
            height:
            highlight:

        Returns :
            La méthode _DrawHeader.
        """
        log.debug(
            "HeaderDrawerMixin.DrawDayHeader : lancé avec day:%s, x=%s, y=%s, w=%s, h=%s et highlight=%s",
            day.FormatISODate(),
            x,
            y,
            width,
            height,
            highlight,
        )
        # Le texte est bien converti en nom du jour, jour, mois !
        return self._DrawHeader(
            "%s %s %s"
            % (
                day.GetWeekDayName(day.GetWeekDay())[:3],
                day.GetDay(),
                day.GetMonthName(day.GetMonth()),
            ),
            x,
            y,
            width,
            height,
            highlight=highlight,
        )

    def DrawMonthHeader(self, day, x, y, w, h):
        # return self._DrawHeader(
        #     "%s %s" % (day.GetMonthName(day.GetMonth()), day.GetYear()), x, y, w, h
        # )
        return self._DrawHeader(
            f"{day.GetMonthName(day.GetMonth())} {day.GetYear()}", x, y, w, h
        )

    def DrawSimpleDayHeader(self, day, x, y, w, h, highlight=None):
        return self._DrawHeader(
            day.Format("%a %d"),
            x,
            y,
            w,
            h,
            weight=wx.FONTWEIGHT_NORMAL,
            alignRight=True,
            highlight=highlight,
        )


class wxBaseDrawer(
    HeaderDrawerMixin, HeaderDrawerDCMixin, BackgroundDrawerDCMixin, wxDrawer
):
    """
    Sous-classe concrète de wxDrawer et des mixins HeaderDrawer, HeaderDrawerDC et BackgroundDrawerDC; regular style.
    """

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        """
        Dessine les heures.

        Args:
            x:
            y:
            w:
            h:
            direction:
            includeText:

        Returns:

        """
        log.debug(f"wxBaseDrawer.DrawHours : dessine des heures.")
        if direction == wxSCHEDULER_VERTICAL:
            self.context.SetBrush(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
            log.debug(
                f"wxBaseDrawer.DrawHours : dessine un rectangle ({x}, {y}, {LEFT_COLUMN_SIZE}, {h})."
            )
            self.context.DrawRectangle(
                int(x), int(y), LEFT_COLUMN_SIZE, int(h)
            )

        font = self.context.GetFont()
        fWeight = font.GetWeight()
        fSize = font.GetPointSize()
        try:
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
            self.context.SetFont(font)
            # self.context.SetTextForeground(wx.BLACK)  # Problème d'écrire en noir sur un fond noir !
            self.context.SetTextForeground(
                wx.Colour(0, 128, 0)
            )  # Couleur de texte verte.

            padding = 5  # Marge intérieure

            if direction == wxSCHEDULER_VERTICAL:
                hourH = 1.0 * h / len(self.displayedHours)
                self.AdjustFontForHeight(font, hourH)
                hourW, _ = self.context.GetTextExtent(
                    # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                )
            else:
                hourW = 1.0 * w / len(self.displayedHours)
                self.AdjustFontForWidth(font, int(hourW * 2 * 0.9))
                _, hourH = self.context.GetTextExtent(
                    # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                )

            if not includeText:
                hourH = 0

            for i, hour in enumerate(self.displayedHours):
                if hour.GetMinute() == 0:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLine(
                            int(x + LEFT_COLUMN_SIZE - hourW // 2),
                            int(y + i * hourH),
                            int(x + w),
                            int(y + i * hourH),
                        )
                        if includeText:
                            # Positionnement du texte pour les heures verticales
                            text_x = x + LEFT_COLUMN_SIZE - hourW - padding
                            text_y = (
                                y + i * hourH - hourH / 2
                            )  # Centrage vertical sur la ligne
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                # wxTimeFormat.FormatTime(self, hour),
                                # int(x + LEFT_COLUMN_SIZE - hourW - 5),
                                int(text_x),
                                # int(y + i * hourH),
                                int(text_y),
                            )
                    else:
                        self.context.DrawLine(
                            int(x + i * hourW),
                            int(y + hourH * 1.25),
                            int(x + i * hourW),
                            int(y + h),
                        )
                        if includeText:
                            # Positionnement du texte pour les heures horizontales
                            text_x = x + i * hourW + padding
                            text_y = (
                                y + hourH * 0.25
                            )  # Positionnement en haut de la zone
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                # wxTimeFormat.FormatTime(self, hour),
                                # int(x + i * hourW + 5),
                                int(text_x),
                                # int(y + hourH * 0.25),
                                int(text_y),
                            )
                else:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLine(
                            int(x + LEFT_COLUMN_SIZE),
                            int(y + i * hourH),
                            int(x + w),
                            int(y + i * hourH),
                        )
                    else:
                        self.context.DrawLine(
                            int(x + i * hourW),
                            int(y + hourH * 1.4),
                            int(x + i * hourW),
                            int(y + h),
                        )

            if direction == wxSCHEDULER_VERTICAL:
                self.context.DrawLine(
                    int(x + LEFT_COLUMN_SIZE - 1),
                    int(y),
                    int(x + LEFT_COLUMN_SIZE - 1),
                    int(y + h),
                )
                return LEFT_COLUMN_SIZE, max(h, DAY_SIZE_MIN.height)
            else:
                self.context.DrawLine(
                    int(x),
                    int(y + hourH * 1.5 - 1),
                    int(x + w),
                    int(y + hourH * 1.5 - 1),
                )
                return max(w, DAY_SIZE_MIN.width), hourH * 1.5
        finally:
            font.SetWeight(fWeight)
            font.SetPointSize(fSize)

    def DrawNowHorizontal(self, x, y, w):
        """
        Dessine maintenant horizontalement.

        Args :
            x : coordonnée
            y : coordonnée
            w : coordonnée

        Returns :

        """
        self.context.SetBrush(wx.Brush(wx.Colour(0, 128, 0)))
        self.context.SetPen(wx.Pen(wx.Colour(0, 128, 0)))
        self.context.DrawArc(
            int(x), int(y + 5), int(x), int(y - 5), int(x), int(y)
        )
        self.context.DrawRectangle(int(x), int(y - 1), int(w), 3)

    def DrawNowVertical(self, x, y, h):
        """
        Dessine Maintenant verticalement.

        Args :
            x :
            y :
            h :

        Returns :

        """
        log.debug(
            f"wxBaseDrawer.DrawNowVertical : Dessine maintenant verticalement."
        )
        # Règle le pinceau et le crayon sur la couleur verte.
        self.context.SetBrush(wx.Brush(wx.Colour(0, 128, 0)))
        self.context.SetPen(wx.Pen(wx.Colour(0, 128, 0)))
        # Dessine un arc de cercle et un rectangle
        self.context.DrawArc(
            int(x - 5), int(y), int(x + 5), int(y), int(x), int(y)
        )
        self.context.DrawRectangle(int(x - 1), int(y), 3, int(h))


class wxFancyDrawer(
    BackgroundDrawerGCMixin, HeaderDrawerGCMixin, HeaderDrawerMixin, wxDrawer
):
    """
    Concrete subclass of wxDrawer; fancy eye-candy using wx.GraphicsContext.
    """

    use_gc = True

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        """
        Dessine des heures.

        Args:
            x:
            y:
            w:
            h:
            direction:
            includeText:

        Returns:

        """
        log.debug(f"wxFancyDrawer.DrawHours : Dessine des heures.")
        if direction == wxSCHEDULER_VERTICAL:
            brush = self.context.CreateLinearGradientBrush(
                x,
                y,
                x + w,
                y + h,
                SCHEDULER_BACKGROUND_BRUSH(),
                DAY_BACKGROUND_BRUSH(),
            )
            self.context.SetBrush(brush)
            self.context.DrawRectangle(
                int(x), int(y), int(LEFT_COLUMN_SIZE), int(h)
            )

        font = wx.NORMAL_FONT
        fsize = font.GetPointSize()
        fweight = font.GetWeight()

        try:
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
            self.context.SetFont(font, wx.BLACK)

            self.context.SetPen(FOREGROUND_PEN)

            padding = 5  # Marge intérieure

            if direction == wxSCHEDULER_VERTICAL:
                hourH = 1.0 * h / len(self.displayedHours)
                self.AdjustFontForHeight(font, int(hourH))
                hourW, _ = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTimeFromHMS(23, 59, 59))
                    # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
                )
            else:
                hourW = 1.0 * w / len(self.displayedHours)
                self.AdjustFontForWidth(font, int(hourW * 2 * 0.9))
                _, hourH = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTimeFromHMS(23, 59, 59))
                    # " " + wxTimeFormat.FormatTime(self, wx.DateTimeFromHMS(23, 59, 59))
                )

            if not includeText:
                hourH = 0

            for i, hour in enumerate(self.displayedHours):
                if hour.GetMinute() == 0:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLines(
                            [
                                (
                                    int(x + LEFT_COLUMN_SIZE - hourW / 2),
                                    int(y + i * hourH),
                                ),
                                (int(x + w), int(y + i * hourH)),
                            ]
                        )
                        if includeText:
                            # Positionnement du texte pour les heures verticales
                            text_x = x + LEFT_COLUMN_SIZE - hourW - padding
                            text_y = (
                                y + i * hourH - hourH / 2
                            )  # Centrage vertical sur la ligne
                            self.context.DrawText(
                                " " + wxTimeFormat.FormatTime(hour),
                                # " " + wxTimeFormat.FormatTime(self, hour),
                                # int(x + LEFT_COLUMN_SIZE - hourW - 10),
                                int(text_x),
                                # int(y + i * hourH),
                                int(text_y),
                            )
                    else:
                        self.context.DrawLines(
                            [
                                (int(x + i * hourW), int(y + hourH * 1.25)),
                                (int(x + i * hourW), int(y + h + 10)),
                            ]
                        )
                        if includeText:
                            # Positionnement du texte pour les heures horizontales
                            text_x = x + i * hourW + padding
                            text_y = (
                                y + hourH * 0.25
                            )  # Positionnement en haut de la zone
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                # wxTimeFormat.FormatTime(self, hour),
                                # int(x + i * hourW + 5),
                                int(text_x),
                                # int(y + hourH * 0.25),
                                int(text_y),
                            )
                else:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLines(
                            [
                                (
                                    int(x + LEFT_COLUMN_SIZE),
                                    int(y + i * hourH),
                                ),
                                (int(x + w), int(y + i * hourH)),
                            ]
                        )
                    else:
                        self.context.DrawLines(
                            [
                                (int(x + i * hourW), int(y + hourH * 1.4)),
                                (int(x + i * hourW), int(y + h)),
                            ]
                        )

            if direction == wxSCHEDULER_VERTICAL:
                self.context.DrawLines(
                    [
                        (int(x + LEFT_COLUMN_SIZE - 1), int(y)),
                        (int(x + LEFT_COLUMN_SIZE - 1), int(y + h)),
                    ]
                )
                log.debug(
                    f"wxFancyDrawer.DrawHours : retourne LEFT_COLUMN_SIZE={LEFT_COLUMN_SIZE}, max(h, DAY_SIZE_MIN.height)={max(h, DAY_SIZE_MIN.height)}."
                )
                return LEFT_COLUMN_SIZE, max(h, DAY_SIZE_MIN.height)
            else:
                self.context.DrawLines(
                    [
                        (int(x), int(y + hourH * 1.5 - 1)),
                        (int(x + w), int(y + hourH * 1.5 - 1)),
                    ]
                )
                log.debug(
                    f"wxFancyDrawer.DrawHours : retourne max(w, DAY_SIZE_MIN.width)={max(w, DAY_SIZE_MIN.width)}, hourH * 1.5={hourH * 1.5}."
                )
                return max(w, DAY_SIZE_MIN.width), hourH * 1.5
                # return max(1, int(max(w, DAY_SIZE_MIN.width))), max(0, int(hourH * 1.5))
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)

    def DrawNowHorizontal(self, x, y, w):
        log.debug(
            f"wxFancyDrawer.DrawNowHorizontal : Dessine maintenant horizontalement en vert."
        )
        brush = self.context.CreateLinearGradientBrush(
            x + 4,
            y - 1,
            x + w,
            y + 1,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)
        self.context.DrawRectangle(int(x + 4), int(y - 2), int(w - 4), 3)

        brush = self.context.CreateRadialGradientBrush(
            x,
            y - 5,
            x,
            y,
            5,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)

        path = self.context.CreatePath()
        path.AddArc(x, y, 5, -math.pi / 2, math.pi / 2, True)
        self.context.FillPath(path)

    def DrawNowVertical(self, x, y, h):
        """
        Dessine maintenant verticalement en vert.
        Args:
            x:
            y:
            h:

        Returns:

        """
        log.debug(
            f"wxFancyDrawer.DrawNowVertical : Dessine maintenant verticalement en vert."
        )
        brush = self.context.CreateLinearGradientBrush(
            x - 1,
            y + 4,
            x + 1,
            y + h,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)
        self.context.DrawRectangle(int(x - 2), int(y + 4), 3, int(h - 4))

        brush = self.context.CreateRadialGradientBrush(
            x - 5,
            y,
            x,
            y,
            5,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)

        path = self.context.CreatePath()
        path.AddArc(x, y, 5, 0.0, math.pi, True)
        self.context.FillPath(path)
