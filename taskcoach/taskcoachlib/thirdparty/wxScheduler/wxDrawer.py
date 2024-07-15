#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import wx

from .wxSchedulerConstants import *
from .wxScheduleUtils import copyDateTime
from .wxTimeFormat import wxTimeFormat


class wxDrawer(object):
    """
    This class handles the actual painting of headers and schedules.

    Attributes:
        context (wx.DC or wx.GraphicsContext): The drawing context.
        displayedHours (list): The list of displayed hours.
    """

    # Set this to True if you want your methods to be passed a
    # wx.GraphicsContext instead of wx.DC.
    use_gc = False

    def __init__(self, context, displayedHours):
        """
        Initialize the wxDrawer instance.

        Args:
            context (wx.DC or wx.GraphicsContext): The drawing context.
            displayedHours (list): The list of displayed hours.
        """
        self.context = context
        self.displayedHours = displayedHours

    def AdjustFontForHeight(self, font, height):
        """
        Adjust the font size to fit within the specified height.

        Args:
            font (wx.Font): The font to adjust.
            height (int): The maximum height.
        """
        pointSize = 18
        while True:
            font.SetPointSize(pointSize)
            _, th = self.context.GetTextExtent(
                " " + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
            )
            if th <= height:
                return
            pointSize -= 1
            if pointSize == 1:
                return  # Hum

    def AdjustFontForWidth(self, font, width):
        """
        Adjust the font size to fit within the specified width.

        Args:
            font (wx.Font): The font to adjust.
            width (int): The maximum width.
        """
        pointSize = 18
        while True:
            font.SetPointSize(pointSize)
            self.context.SetFont(font)
            tw, _ = self.context.GetTextExtent(
                " " + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
            )
            if tw <= width:
                return
            pointSize -= 1
            if pointSize == 1:
                return  # Hum

    def DrawDayHeader(self, day, x, y, w, h, highlight=None):
        """
        Draw the header for a day.

        Args:
            day (wx.DateTime): The date for the day header.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the header.
            h (int): The height of the header.
            highlight (wx.Colour, optional): The highlight color (default is None).

        Returns:
            int: The header's height.
        """
        raise NotImplementedError

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Draw the background for a day.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the background.
            h (int): The height of the background.
            highlight (wx.Colour, optional): The highlight color (default is None).
        """
        raise NotImplementedError

    def DrawMonthHeader(self, day, x, y, w, h):
        """
        Draw the header for a month.

        Args:
            day (wx.DateTime): The date for the month header.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the header.
            h (int): The height of the header.

        Returns:
            int: The header's height.
        """
        raise NotImplementedError

    def DrawSimpleDayHeader(self, day, x, y, w, h, highlight=None):
        """
        Draw the header for a day in compact form.

        Args:
            day (wx.DateTime): The date for the day header.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the header.
            h (int): The height of the header.
            highlight (wx.Colour, optional): The highlight color (default is None).

        Returns:
            int: The header's height.
        """
        raise NotImplementedError

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        """
        Draw hours of the day on the left of the specified rectangle.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            direction (int): The direction of the drawing (horizontal or vertical).
            includeText (bool, optional): Whether to include text (default is True).

        Returns:
            int: The width or height of the column depending on direction.
        """
        raise NotImplementedError

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
        """
        Draw a set of schedules in compact form.

        Args:
            day (wx.DateTime): The date for the schedules.
            schedules (list): The list of schedules to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            width (int): The width of the drawing area.
            height (int): The height of the drawing area.
            highlightColor (wx.Colour): The highlight color.

        Returns:
            list: A list of tuples containing (schedule, start point, end point).
        """
        raise NotImplementedError

    def DrawNowHorizontal(self, x, y, w):
        """
        Draw a horizontal line showing the current time.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the line.
        """
        raise NotImplementedError

    def DrawNowVertical(self, x, y, h):
        """
        Draw a vertical line showing the current time.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            h (int): The height of the line.
        """
        raise NotImplementedError

    def _DrawSchedule(self, schedule, x, y, w, h):
        """
        Draw a schedule in the specified rectangle.

        Args:
            schedule: The schedule to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.

        Returns:
            int: The height of the drawn schedule.
        """
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
                            bitmap, x + offsetX, y + offsetY, 16, 16
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
                x,
                y + offsetY,
                w - 2 * SCHEDULE_INSIDE_MARGIN,
                None if h is None else h - offsetY - SCHEDULE_INSIDE_MARGIN,
            )
        else:
            if h is not None:
                self.context.SetBrush(wx.Brush(schedule.color))
                self.context.DrawRectangle(x, y, w, h)

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
                        x + SCHEDULE_INSIDE_MARGIN,
                        y + offsetY,
                        w - 2 * SCHEDULE_INSIDE_MARGIN,
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
                            x + SCHEDULE_INSIDE_MARGIN,
                            y + offsetY,
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
                            bitmap, x + offsetX, y + offsetY, True
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
        """
        Draw a schedule vertically.

        Args:
            schedule: The schedule to draw.
            day (wx.DateTime): The day of the schedule.
            workingHours (list): The list of working hours.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            width (int): The width of the drawing area.
            height (int): The height of the drawing area.

        Returns:
            tuple: The bounding box of the drawn schedule.
        """
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

        y = y + position * height // total + SCHEDULE_OUTSIDE_MARGIN
        x += SCHEDULE_OUTSIDE_MARGIN
        height = height * size // total - 2 * SCHEDULE_OUTSIDE_MARGIN
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
        """
        Draw a schedule horizontally.

        Args:
            schedule: The schedule to draw.
            day (wx.DateTime): The start day of the schedule.
            daysCount (int): The number of days.
            workingHours (list): The list of working hours.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            width (int): The width of the drawing area.
            height (int): The height of the drawing area.

        Returns:
            tuple: The bounding box of the drawn schedule.
        """
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

        x = x + position * width // total + SCHEDULE_OUTSIDE_MARGIN
        width = width * size // total - 2 * SCHEDULE_OUTSIDE_MARGIN

        # Height is variable
        height = self._DrawSchedule(schedule, x, y, width, None)
        self._DrawSchedule(schedule, x, y, width, height)

        return (
            x - SCHEDULE_OUTSIDE_MARGIN,
            y - SCHEDULE_OUTSIDE_MARGIN,
            width + 2 * SCHEDULE_OUTSIDE_MARGIN,
            height + 2 * SCHEDULE_OUTSIDE_MARGIN,
        )

    @staticmethod
    def ScheduleSize(schedule, workingHours, firstDay, dayCount):
        """
        Compute the position and size of the schedule in the direction representing time.

        Args:
            schedule: The schedule to size.
            workingHours (list): The list of working hours.
            firstDay (wx.DateTime): The first day.
            dayCount (int): The number of days.

        Returns:
            tuple: The size, position, and total time of the schedule.
        """
        totalSpan = 0
        scheduleSpan = 0
        position = 0

        totalTime = 0
        for startHour, endHour in workingHours:
            totalTime += (
                copyDateTime(endHour).Subtract(startHour).GetMinutes() // 60.0
            )

        for dayNumber in range(dayCount):
            currentDay = copyDateTime(firstDay)
            currentDay = currentDay.Add(wx.DateSpan(days=dayNumber))

            for startHour, endHour in workingHours:
                startHourCopy = wx.DateTime.FromDMY(
                    currentDay.GetDay(),
                    currentDay.GetMonth(),
                    currentDay.GetYear(),
                    startHour.GetHour(),
                    startHour.GetMinute(),
                    0,
                )
                endHourCopy = wx.DateTime.FromDMY(
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
            dayCount * totalTime * scheduleSpan // totalSpan,
            dayCount * totalTime * position // totalSpan,
            totalTime * dayCount,
        )

    ScheduleSize = staticmethod(ScheduleSize)

    def _drawTextInRect(self, context, text, offsetX, x, y, w, h):
        """
        Draw text within a specified rectangle.

        Args:
            context (wx.DC or wx.GraphicsContext): The drawing context.
            text (str): The text to draw.
            offsetX (int): The horizontal offset.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.

        Returns:
            int: The height of the drawn text.
        """
        words = text.split()
        result = context.GetFullTextExtent(" ".join(words))
        tw, th = result[0], result[1]

        if h is not None and th > h + SCHEDULE_INSIDE_MARGIN:
            return SCHEDULE_INSIDE_MARGIN

        if tw <= w - offsetX:
            context.DrawText(" ".join(words), x + offsetX, y)
            return th + SCHEDULE_INSIDE_MARGIN

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
                0 if h == 0 else int(h - (ny - y)),
            )

        return th + SCHEDULE_INSIDE_MARGIN

    def _shrinkText(self, dc, text, width, height):
        """
        Truncate text to fit within the desired width.

        Args:
            dc (wx.DC): The device context.
            text (str): The text to truncate.
            width (int): The maximum width.
            height (int): The maximum height.

        Returns:
            list: A list of truncated text lines.
        """
        MORE_SIGNAL = "..."
        SEPARATOR = " "

        textlist = list()  # List returned by this method
        words = list()  # Wordlist for intermediate elaboration

        # Split text in single words and split words when their(yours) width is over
        # available width
        text = text.replace("\n", " ").split()

        for word in text:
            if dc.GetTextExtent(word)[0] > width:
                # Cycle through every char until word width is minor or equal
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
                    # Must exist at least(almost) one line of description
                    if len(textlist) > 1:
                        textlist = textlist[:-1]

                    break
            else:
                textline.append(word)

        # Add remaining words to text list
        if len(textline) > 0:
            textlist.append(SEPARATOR.join(textline))

        return textlist


class BackgroundDrawerDCMixin(object):
    """
    Mixin to draw day background with a DC.
    """

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Draw the background for a day using a DC.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the background.
            h (int): The height of the background.
            highlight (wx.Colour, optional): The highlight color (default is None).
        """
        if highlight is not None:
            self.context.SetBrush(wx.Brush(highlight))
        else:
            self.context.SetBrush(wx.TRANSPARENT_BRUSH)

        self.context.SetPen(FOREGROUND_PEN)

        self.context.DrawRectangle(int(x), int(y - 1), int(w), int(h + 1))


class HeaderDrawerDCMixin(object):
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
        """
        Draw a header with the specified properties.

        Args:
            text (str): The header text.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the header.
            h (int): The height of the header.
            pointSize (int, optional): The font point size (default is 12).
            weight (int, optional): The font weight (default is wx.FONTWEIGHT_BOLD).
            alignRight (bool, optional): Whether to align the text to the right (default is False).
            highlight (wx.Colour, optional): The highlight color (default is None).

        Returns:
            int: The width and height of the drawn header.
        """
        font = self.context.GetFont()
        font.SetPointSize(pointSize)
        font.SetWeight(weight)
        self.context.SetFont(font)

        textW, textH = self.context.GetTextExtent(text)

        if highlight is not None:
            self.context.SetBrush(wx.Brush(highlight))
        else:
            self.context.SetBrush(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))

        self.context.DrawRectangle(int(x), int(y), int(w), int(textH * 1.5))

        self.context.SetTextForeground(wx.BLACK)

        if alignRight:
            self.context.DrawText(
                text, int(x + w - textW * 1.5), int(y + textH * 0.25)
            )
        else:
            self.context.DrawText(
                text, int(x + (w - textW) / 2), int(y + textH * 0.25)
            )

        return w, int(textH * 1.5)

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
        """
        Draw schedules in compact form.

        Args:
            day (wx.DateTime): The date for the schedules.
            schedules (list): The list of schedules to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            width (int): The width of the drawing area.
            height (int): The height of the drawing area.
            highlightColor (wx.Colour): The highlight color.

        Returns:
            list: A list of tuples containing (schedule, start point, end point).
        """
        if day is None:
            self.context.SetBrush(wx.LIGHT_GREY_BRUSH)
        else:
            self.context.SetBrush(wx.Brush(DAY_BACKGROUND_BRUSH()))

        self.context.DrawRectangle(x, y, width, height)

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
                    description = "%s %s" % (
                        wxTimeFormat.FormatTime(
                            schedule.start, includeMinutes=True
                        ),
                        schedule.description,
                    )
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
                self.context.DrawRectangle(x, y, width, textH * 1.2)
                results.append(
                    (
                        schedule,
                        wx.Point(x, y),
                        wx.Point(x + width, y + textH * 1.2),
                    )
                )

                self.context.SetTextForeground(schedule.foreground)
                self.context.DrawText(
                    description, x + SCHEDULE_INSIDE_MARGIN, y + textH * 0.1
                )

                y += textH * 1.2
                totalHeight += textH * 1.2

        return results


class BackgroundDrawerGCMixin(object):
    """
    Mixin to draw day background with a GC.
    """

    def DrawDayBackground(self, x, y, w, h, highlight=None):
        """
        Draw the background for a day using a GC.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the background.
            h (int): The height of the background.
            highlight (wx.Colour, optional): The highlight color (default is None).
        """
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

        self.context.DrawRectangle(x, y - 1, w, h + 1)


class HeaderDrawerGCMixin(object):
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
        """
        Draw a header with the specified properties.

        Args:
            text (str): The header text.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the header.
            h (int): The height of the header.
            pointSize (int, optional): The font point size (default is 12).
            weight (int, optional): The font weight (default is wx.FONTWEIGHT_BOLD).
            alignRight (bool, optional): Whether to align the text to the right (default is False).
            highlight (wx.Colour, optional): The highlight color (default is None).

        Returns:
            int: The width and height of the drawn header.
        """
        font = wx.NORMAL_FONT
        fsize = font.GetPointSize()
        fweight = font.GetWeight()

        try:
            font.SetPointSize(pointSize)
            font.SetWeight(weight)
            self.context.SetFont(font, wx.BLACK)

            textW, textH = self.context.GetTextExtent(text)

            x1 = x
            y1 = y
            x2 = x + w
            y2 = y + textH * 1.5

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
            self.context.DrawRectangle(x1, y1, x2 - x1, y2 - y1)

            if alignRight:
                self.context.DrawText(
                    text, int(x + w - 1.5 * textW), int(y + textH * 0.25)
                )
            else:
                self.context.DrawText(
                    text, x + (w - textW) // 2, int(y + textH * 0.25)
                )

            return w, int(textH * 1.5)
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)

    def DrawSchedulesCompact(
        self, day, schedules, x, y, width, height, highlightColor
    ):
        """
        Draw schedules in compact form.

        Args:
            day (wx.DateTime): The date for the schedules.
            schedules (list): The list of schedules to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            width (int): The width of the drawing area.
            height (int): The height of the drawing area.
            highlightColor (wx.Colour): The highlight color.

        Returns:
            list: A list of tuples containing (schedule, start point, end point).
        """
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
        self.context.DrawRectangle(x, y, width, height)

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
                        description = "%s %s" % (
                            wxTimeFormat.FormatTime(
                                schedule.start, includeMinutes=True
                            ),
                            schedule.description,
                        )
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
                        x, y, width, int(textH * 1.2), int(1.0 * textH // 2)
                    )
                    results.append(
                        (
                            schedule,
                            wx.Point(x, y),
                            wx.Point(x + width, int(y + textH * 1.2)),
                        )
                    )

                    self.context.SetFont(schedule.font, schedule.foreground)
                    self.context.DrawText(
                        description,
                        x + SCHEDULE_INSIDE_MARGIN,
                        y + textH * 0.1,
                    )

                    y += textH * 1.2
                    totalHeight += textH * 1.2

            return results
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)


class HeaderDrawerMixin(object):
    """
    A mixin that draws headers using the _DrawHeader method.
    """

    def DrawDayHeader(self, day, x, y, width, height, highlight=None):
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
        return self._DrawHeader(
            "%s %s" % (day.GetMonthName(day.GetMonth()), day.GetYear()),
            x,
            y,
            w,
            h,
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
    BackgroundDrawerDCMixin, HeaderDrawerDCMixin, HeaderDrawerMixin, wxDrawer
):
    """
    Concrete subclass of wxDrawer; regular style.
    """

    def DrawHours(self, x, y, w, h, direction, includeText=True):
        if direction == wxSCHEDULER_VERTICAL:
            self.context.SetBrush(wx.Brush(SCHEDULER_BACKGROUND_BRUSH()))
            self.context.DrawRectangle(x, y, LEFT_COLUMN_SIZE, h)

        font = self.context.GetFont()
        fWeight = font.GetWeight()
        fSize = font.GetPointSize()
        try:
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
            self.context.SetFont(font)
            self.context.SetTextForeground(wx.BLACK)

            if direction == wxSCHEDULER_VERTICAL:
                hourH = int(1.0 * h // len(self.displayedHours))
                self.AdjustFontForHeight(font, hourH)
                hourW, _ = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                )
            else:
                hourW = int(1.0 * w // len(self.displayedHours))
                self.AdjustFontForWidth(font, int(hourW * 2 * 0.9))
                _, hourH = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                )

            if not includeText:
                hourH = 0

            for i, hour in enumerate(self.displayedHours):
                if hour.GetMinute() == 0:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLine(
                            x + LEFT_COLUMN_SIZE - hourW // 2,
                            y + i * hourH,
                            x + w,
                            y + i * hourH,
                        )
                        if includeText:
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                x + LEFT_COLUMN_SIZE - hourW - 5,
                                y + i * hourH,
                            )
                    else:
                        self.context.DrawLine(
                            x + i * hourW,
                            int(y + hourH * 1.25),
                            x + i * hourW,
                            y + h,
                        )
                        if includeText:
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                x + i * hourW + 5,
                                int(y + hourH * 0.25),
                            )
                else:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLine(
                            x + LEFT_COLUMN_SIZE,
                            y + i * hourH,
                            x + w,
                            y + i * hourH,
                        )
                    else:
                        self.context.DrawLine(
                            x + i * hourW,
                            int(y + hourH * 1.4),
                            x + i * hourW,
                            y + h,
                        )

            if direction == wxSCHEDULER_VERTICAL:
                self.context.DrawLine(
                    x + LEFT_COLUMN_SIZE - 1,
                    y,
                    x + LEFT_COLUMN_SIZE - 1,
                    y + h,
                )
                return LEFT_COLUMN_SIZE, max(h, DAY_SIZE_MIN.height)
            else:
                self.context.DrawLine(
                    x,
                    int(y + hourH * 1.5 - 1),
                    x + w,
                    int(y + hourH * 1.5 - 1),
                )
                return max(w, DAY_SIZE_MIN.width), int(hourH * 1.5)
        finally:
            font.SetWeight(fWeight)
            font.SetPointSize(fSize)

    def DrawNowHorizontal(self, x, y, w):
        self.context.SetBrush(wx.Brush(wx.Colour(0, 128, 0)))
        self.context.SetPen(wx.Pen(wx.Colour(0, 128, 0)))
        self.context.DrawArc(
            int(x), int(y + 5), int(x), int(y - 5), int(x), int(y)
        )
        self.context.DrawRectangle(int(x), int(y - 1), int(w), 3)

    def DrawNowVertical(self, x, y, h):
        self.context.SetBrush(wx.Brush(wx.Colour(0, 128, 0)))
        self.context.SetPen(wx.Pen(wx.Colour(0, 128, 0)))
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
            self.context.DrawRectangle(x, y, LEFT_COLUMN_SIZE, h)

        font = wx.NORMAL_FONT
        fsize = font.GetPointSize()
        fweight = font.GetWeight()

        try:
            font.SetWeight(wx.FONTWEIGHT_NORMAL)
            self.context.SetFont(font, wx.BLACK)

            self.context.SetPen(FOREGROUND_PEN)

            if direction == wxSCHEDULER_VERTICAL:
                hourH = int(1.0 * h / len(self.displayedHours))
                self.AdjustFontForHeight(font, hourH)
                hourW, _ = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
                )
            else:
                hourW = int(1.0 * w / len(self.displayedHours))
                self.AdjustFontForWidth(font, int(hourW * 2 * 0.9))
                _, hourH = self.context.GetTextExtent(
                    " "
                    + wxTimeFormat.FormatTime(wx.DateTime.FromHMS(23, 59, 59))
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
                                    y + i * hourH,
                                ),
                                (x + w, y + i * hourH),
                            ]
                        )
                        if includeText:
                            self.context.DrawText(
                                " " + wxTimeFormat.FormatTime(hour),
                                x + LEFT_COLUMN_SIZE - hourW - 10,
                                y + i * hourH,
                            )
                    else:
                        self.context.DrawLines(
                            [
                                int(x + i * hourW, y + hourH * 1.25),
                                (x + i * hourW, y + h + 10),
                            ]
                        )
                        if includeText:
                            self.context.DrawText(
                                wxTimeFormat.FormatTime(hour),
                                x + i * hourW + 5,
                                int(y + hourH * 0.25),
                            )
                else:
                    if direction == wxSCHEDULER_VERTICAL:
                        self.context.DrawLines(
                            [
                                (x + LEFT_COLUMN_SIZE, y + i * hourH),
                                (x + w, y + i * hourH),
                            ]
                        )
                    else:
                        self.context.DrawLines(
                            [
                                int(x + i * hourW, y + hourH * 1.4),
                                (x + i * hourW, y + h),
                            ]
                        )

            if direction == wxSCHEDULER_VERTICAL:
                self.context.DrawLines(
                    [
                        (x + LEFT_COLUMN_SIZE - 1, y),
                        (x + LEFT_COLUMN_SIZE - 1, y + h),
                    ]
                )
                return LEFT_COLUMN_SIZE, max(h, DAY_SIZE_MIN.height)
            else:
                self.context.DrawLines(
                    [
                        (int(x), int(y + hourH * 1.5 - 1)),
                        (int(x + w), int(y + hourH * 1.5 - 1)),
                    ]
                )
                return max(w, DAY_SIZE_MIN.width), int(hourH * 1.5)
        finally:
            font.SetPointSize(fsize)
            font.SetWeight(fweight)

    def DrawNowHorizontal(self, x, y, w):
        brush = self.context.CreateLinearGradientBrush(
            x + 4,
            y - 1,
            x + w,
            y + 1,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)
        self.context.DrawRectangle(x + 4, y - 2, w - 4, 3)

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
        path.AddArc(x, y, 5, int(-math.pi / 2), int(math.pi / 2), True)
        self.context.FillPath(path)

    def DrawNowVertical(self, x, y, h):
        brush = self.context.CreateLinearGradientBrush(
            x - 1,
            y + 4,
            x + 1,
            y + h,
            wx.Colour(0, 128, 0, 128),
            wx.Colour(0, 255, 0, 128),
        )
        self.context.SetBrush(brush)
        self.context.DrawRectangle(x - 2, y + 4, 3, h - 4)

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
