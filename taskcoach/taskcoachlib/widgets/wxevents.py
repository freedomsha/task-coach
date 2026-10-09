"""
Task Coach - Your friendly task manager
Copyright (C) 2014 Task Coach developers <developers@taskcoach.org>

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

import logging
import wx
import datetime
import math

log = logging.getLogger(__name__)


# Define new event types and binders
wxEVT_EVENT_SELECTION_CHANGED = wx.NewEventType()
EVT_EVENT_SELECTION_CHANGED = wx.PyEventBinder(wxEVT_EVENT_SELECTION_CHANGED)

wxEVT_EVENT_DATES_CHANGED = wx.NewEventType()
EVT_EVENT_DATES_CHANGED = wx.PyEventBinder(wxEVT_EVENT_DATES_CHANGED)


class _HitResult(object):
    """
    Une classe d'assistance pour stocker le résultat des tests d'accès sur le canevas du calendrier.
    """

    HIT_START = 0
    HIT_IN = 1
    HIT_END = 2

    def __init__(self, x, y, event, dateTime):
        """
        Initialisez l'instance _HitResult.

        Args:
            x (int): The x-coordinate of the hit.
            y (int): The y-coordinate of the hit.
            event: The event that was hit.
            dateTime (datetime.datetime): The date and time of the hit.
        """
        self.x, self.y = x, y
        self.event = event
        self.dateTime = dateTime
        self.position = self.HIT_IN


class _Watermark(object):
    """
    Une classe d'assistance pour gérer les hauteurs de filigrane pour les événements.
    """

    def __init__(self):
        """
        Initialisez l'instance _Watermark.
        """
        self.__values = []

    def height(self, start, end):
        """
        Obtenez la hauteur maximale des filigranes(watermarks) entre les heures de début et de fin.

        Args:
            start (int): The start time index.
            end (int): The end time index.

        Returns:
            int: The maximum height of watermarks.
        """
        r = 0
        for ints, inte, h in self.__values:
            if not (end < ints or start >= inte):
                r = max(r, h)
        return r

    def totalHeight(self):
        """
        Obtenez la hauteur totale de tous les filigranes(watermarks).

        Returns:
            int: The total height of all watermarks.
        """
        return (
            max([h for ints, inte, h in self.__values]) if self.__values else 0
        )

    def add(self, start, end, h):
        """
        Ajoutez un nouveau filigrane avec le début, la fin et la hauteur donnés.

        Args:
            start (int): The start time index.
            end (int): The end time index.
            h (int): The height of the watermark.
        """
        self.__values.append((start, end, h))


def total_seconds(td):  # Method new in 2.7
    """
    Obtenez le nombre total de secondes dans un objet timedelta.

    Args:
        td (datetime.timedelta): The timedelta object.

    Returns:
        float: The total number of seconds.
    """
    return (
            1.0 * td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6
    ) / 10 ** 6


def shortenText(gc, text, maxW):
    """
    Raccourcissez le texte donné pour qu'il tienne dans la largeur spécifiée.

    Args:
        gc (wx.GraphicsContext): The graphics context.
        text (str): The text to shorten.
        maxW (int): The maximum width.

    Returns:
        str: The shortened text.
    """
    shortText = text
    idx = len(text) // 2
    while True:
        # w, h = gc.GetFullTextExtent(shortText)
        # w, h, d, eL = gc.GetFullTextExtent(shortText)
        w, h, _, _ = gc.GetFullTextExtent(shortText)
        if w <= maxW:
            return shortText
        idx -= 1
        if idx == 0:
            return "\u2026"
        shortText = text[:idx] + "\u2026" + text[-idx:]


class CalendarCanvas(wx.Panel):
    """
    Un canevas pour afficher et interagir avec les événements du calendrier.
    """

    _gradVal = 0.2

    MS_IDLE = 0
    MS_HOVER_LEFT = 1
    MS_HOVER_RIGHT = 2
    MS_DRAG_LEFT = 3
    MS_DRAG_RIGHT = 4
    MS_DRAG_START = 5
    MS_DRAGGING = 6

    def __init__(self, parent, start=None, end=None):
        """
        Initialisez l'instance de CalendarCanvas.

        Args:
            parent (wx.Window): The parent window.
            start (datetime.datetime, optional): The start date and time. Defaults to None.
            end (datetime.datetime, optional): The end date and time. Defaults to None.
        """
        self._start = start or datetime.datetime.combine(
            datetime.datetime.now().date(), datetime.time(0, 0, 0)
        )
        self._end = end or self._start + datetime.timedelta(days=7)
        super(CalendarCanvas, self).__init__(
            parent, wx.ID_ANY, style=wx.FULL_REPAINT_ON_RESIZE
        )

        self._coords = (
            dict()
        )  # Event => (startIdx, endIdx, startIdxRecursive, endIdxRecursive, yMin, yMax)
        self._maxIndex = 0
        self._minSize = (0, 0)

        # Attributs du dessin
        self._precision = 1  # Minutes
        self._gridSize = 15  # Minutes
        self._eventHeight = 32.0
        self._eventWidthMin = 0.1
        self._eventWidth = 0.1
        self._margin = 5.0
        # self._marginTop = 22.0
        self._marginTop = 22
        self._outlineColorDark = wx.Colour(180, 180, 180)
        self._outlineColorLight = wx.Colour(210, 210, 210)
        self._headerSpans = []
        self._daySpans = []
        self._selection = set()
        self._mouseState = self.MS_IDLE
        self._mouseOrigin = None
        self._mouseDragPos = None
        self._todayColor = wx.Colour(0, 0, 128)

        self._hScroll = wx.ScrollBar(self, wx.ID_ANY, style=wx.SB_HORIZONTAL)
        self._vScroll = wx.ScrollBar(self, wx.ID_ANY, style=wx.SB_VERTICAL)

        self._hScroll.Hide()
        self._vScroll.Hide()

        # TODO: wxPyDeprecationWarning: Call to deprecated item __call__. Use :meth:`EvtHandler.Bind` instead.
        # wx.EVT_SCROLL(self._hScroll, self._OnScroll)
        self._hScroll.Bind(wx.EVT_SCROLL, self._OnScroll)
        # wx.EVT_SCROLL(self._vScroll, self._OnScroll)
        self._vScroll.Bind(wx.EVT_SCROLL, self._OnScroll)

        # wx.EVT_PAINT(self, self._OnPaint)
        self.Bind(wx.EVT_PAINT, self._OnPaint)
        # wx.EVT_SIZE(self, self._OnResize)
        self.Bind(wx.EVT_SIZE, self._OnResize)
        # wx.EVT_LEFT_DOWN(self, self._OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self._OnLeftDown)
        # wx.EVT_LEFT_UP(self, self._OnLeftUp)
        self.Bind(wx.EVT_LEFT_UP, self._OnLeftUp)
        # wx.EVT_RIGHT_DOWN(self, self._OnRightDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self._OnRightDown)
        # wx.EVT_MOTION(self, self._OnMotion)
        self.Bind(wx.EVT_MOTION, self._OnMotion)
        self._Invalidate()

    # Methods to override
    def IsWorked(self, date):
        """
        Vérifiez si la date indiquée est un jour ouvrable.

        Args :
            date (date) : (datetime.date) La date à vérifer.

        Returns :
            bool : Vrai si la date est un jour ouvrable, Faux sinon.
        """
        return date.isoweekday() not in [6, 7]

    def FormatDateTime(self, dateTime):
        """
        Formatez la date et l'heure données sous forme de chaîne.

        Args:
            dateTime (datetime.datetime): The date and time to format.

        Returns:
            str: The formatted date and time.
        """
        return dateTime.strftime("%A")

    def GetRootEvents(self):
        """
        Obtenez les événements racine du calendrier.

        Returns :
            list : A list of root events.
        """
        return list()

    def GetStart(self, event):
        """
        Obtenez la date et l'heure de début de l'événement donné.

        Args:
            event: The event to get the start date and time for.

        Returns:
            (datetime.datetime) : The start date and time.
        """
        raise NotImplementedError

    def GetEnd(self, event):
        """
        Obtenez la date et l'heure de fin de l'événement donné.

        Args:
            event: The event to get the end date and time for.

        Returns:
            datetime.datetime: The end date and time.
        """
        raise NotImplementedError

    def GetText(self, event):
        """
        Obtenez le texte de l'événement donné.

        Args:
            event: The event to get the text for.

        Returns:
            str: The text of the event.
        """
        raise NotImplementedError

    def GetChildren(self, event):
        """
        Obtenez les enfants de l'événement donné.

        Args :
            event : L'événement pour lequel rechercher les enfants.

        Returns :
            list : Une liste d'événements enfants.
        """
        # Signature of method 'GetChildren()' does not match signature of the base method in class 'Window'
        # only (self)
        raise NotImplementedError

    def GetBackgroundColor(self, event):
        """
        Obtenez la couleur d'arrière-plan de l'événement donné.

        Args:
            event: The event to get the background color for.

        Returns:
            wx.Colour: The background color.
        """
        raise NotImplementedError

    def GetForegroundColor(self, event):
        """
        Obtenez la couleur de premier plan pour l'événement donné.

        Args:
            event: The event to get the foreground color for.

        Returns:
            wx.Colour: The foreground color.
        """
        raise NotImplementedError

    def GetProgress(self, event):
        """
        Obtenez la progression de l'événement donné.

        Args:
            event: The event to get the progress for.

        Returns:
            float: The progress of the event.
        """
        raise NotImplementedError

    def GetIcons(self, event):
        """
        Obtenez les icônes pour l'événement donné.

        Args:
            event: The event to get the icons for.

        Returns:
            list: A list of icons.
        """
        raise NotImplementedError

    def GetFont(self, event):
        """
        Obtenez la police pour l'événement donné.

        Args:
            event: The event to get the font for.

        Returns:
            wx.Font: The font.
        """
        # Signature of method 'GetFont()' does not match signature of the base method in class 'Window'
        # only (self)
        raise NotImplementedError

    # Get/Set

    def GetPrecision(self):
        """
        Obtenez la précision du calendrier.

        Returns:
            int: The precision in minutes.
        """
        return self._precision

    def SetPrecision(self, precision):
        """
        Définissez la précision du calendrier.

        Args:
            precision (int): The precision in minutes.
        """
        self._precision = precision
        self._Invalidate()
        self.Refresh()

    def GetEventHeight(self):
        """
        Obtenez la hauteur des événements.

        Returns:
            float: The event height.
        """
        return self._eventHeight

    def SetEventHeight(self, height):
        """
        Définissez la hauteur des événements.

        Args:
            height (float): The event height.
        """
        self._eventHeight = 1.0 * height
        self._Invalidate()
        self.Refresh()

    def GetEventWidth(self):
        """
        Obtenez la largeur minimale des événements.

        Returns:
            float: The event width.
        """
        return self._eventWidthMin

    def SetEventWidth(self, width):
        """
        Définissez la largeur minimale des événements.

        Args:
            width (float): The event width.
        """
        self._eventWidthMin = width
        self._Invalidate()
        self.Refresh()

    def GetMargin(self):
        """
        Obtenez la taille de la marge.

        Returns:
            float: The margin size.
        """
        return self._margin

    def SetMargin(self, margin):
        """
        Définissez la taille de la marge.

        Args:
            margin (float): The margin size.
        """
        self._margin = 1.0 * margin
        self._Invalidate()
        self.Refresh()

    def OutlineColorDark(self):
        """
        Obtenez la couleur du contour sombre.

        Returns:
            wx.Colour: The dark outline color.
        """
        return self._outlineColorDark

    def SetOutlineColorDark(self, color):
        """
        Définissez la couleur du contour sombre.

        Args:
            color (wx.Colour): The dark outline color.
        """
        self._outlineColorDark = color
        self.Refresh()

    def OutlineColorLight(self):
        """
        Obtenez la couleur du contour clair.

        Returns:
            wx.Colour: The light outline color.
        """
        return self._outlineColorLight

    def SetOutlineColorLight(self, color):
        """
        Définissez la couleur du contour clair.

        Args:
            color (wx.Colour): The light outline color.
        """
        self._outlineColorLight = color
        self.Refresh()

    def TodayColor(self):
        """
        Obtenez la couleur de la date d'aujourd'hui.

        Returns :
            (wx.Colour) : The color for Today's date.
        """
        return self._todayColor

    def SetTodayColor(self, color):
        """
        Définissez la couleur de la date d'aujourd'hui.

        Args:
            color (wx.Colour): The color for Today's date.
        """
        self._todayColor = color
        self.Refresh()

    def ViewSpan(self):
        """
        Obtenez les dates de début et de fin de la durée d’affichage.

        Returns :
            tuple : The start and end dates.
        """
        return (self._start, self._end)

    def SetViewSpan(self, start, end):
        """
        Définissez les dates de début et de fin de la période de visualisation.

        Args :
            start (datetime.datetime) : The start date.
            end (datetime.datetime) : The end date.
        """
        self._start = start
        self._end = end
        self._Invalidate()
        self.Refresh()

    def Selection(self):
        """
        Obtenez les événements sélectionnés.

        Returns :
            (set) : The set of selected events.
        """
        return self._selection

    def Select(self, events):
        """
        Sélectionnez les événements donnés.

        Args :
            events (list) : The events to select.
        """
        self._selection = set(events) & set(self._coords.keys())
        e = wx.PyCommandEvent(wxEVT_EVENT_SELECTION_CHANGED)
        e.selection = set(self._selection)
        e.SetEventObject(self)
        self.ProcessEvent(e)
        self.Refresh()

    def HitTest(self, x: int, y:int):
        """
        Effectuez un test de réussite pour déterminer quel événement se trouve sous les coordonnées données.

        Args :
            x (int) : The x-coordinate.
            y (int) : The y-coordinate.

        Returns :
            _HitResult : The result of the hit test.
        """
        w, h = self.GetClientSize()

        if y <= self._marginTop:
            return None
        # Vérification de l'existence de la barre de défilement et ajustement de la hauteur
        if self._hScroll.IsShown():
            h -= self._hScroll.GetClientSize()[1]
            if y >= h:
                return None
        # Vérification de l'existence de la barre de défilement et ajustement de la largeur
        if self._vScroll.IsShown():
            w -= self._vScroll.GetClientSize()[0]
            if x >= w:
                return None

        if self._hScroll.IsShown():
            x += self._hScroll.GetThumbPosition()
        if self._vScroll.IsShown():
            y += self._vScroll.GetThumbPosition()

        xIndex = int(x / self._eventWidth)
        yIndex = int(
            (y - self._marginTop) / (self._eventHeight + self._margin)
        )
        dateTime = self._start + datetime.timedelta(
            minutes=self._precision * xIndex
        )

        for event, (
                startIndex,
                endIndex,
                startIndexRecursive,
                endIndexRecursive,
                yMin,
                yMax,
        ) in list(self._coords.items()):
            if (
                    startIndexRecursive <= xIndex < endIndexRecursive
                    and yMin <= yIndex < yMax
            ):
                # Peut-être un enfant
                children = []
                self._Flatten(event, children)
                for candidate in reversed(children):
                    if candidate in self._coords:
                        si, ei, sir, eir, ymin, ymax = self._coords[candidate]
                        if (
                                si is not None
                                and abs(x - si * self._eventWidth) <= self._margin
                                and ymin <= yIndex < ymax
                        ):
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_START
                            return _result
                        if (
                                ei is not None
                                and abs(x - ei * self._eventWidth) <= self._margin
                                and ymin <= yIndex < ymax
                        ):
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_END
                            return _result
                        if sir <= xIndex < eir and ymin <= yIndex < ymax:
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_IN
                            return _result
                # Puisque la liste contient au moins "event"...
                assert 0

        # Nous n’avons touché aucun événement.
        _result = _HitResult(x, y, None, dateTime)
        return _result

    def _Flatten(self, event, result):
        """
        Aplatissez la hiérarchie des événements dans une liste.

        Args:
            event: The event to flatten.
            result (list): The list to store the flattened events.
        """
        result.append(event)
        for child in self.GetChildren(event):
            self._Flatten(child, result)

    def _DrawEvent(self, gc, event):
        """
        Dessinez l’événement donné.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            event: The event to draw.
        """
        if event in self._coords:
            (
                startIndex,
                endIndex,
                startIndexRecursive,
                endIndexRecursive,
                yMin,
                yMax,
            ) = self._coords[event]
            if self.GetChildren(event):
                self._DrawParent(
                    gc,
                    startIndex,
                    endIndex,
                    startIndexRecursive,
                    endIndexRecursive,
                    yMin,
                    yMax,
                    event,
                    self._eventWidth,
                )
            else:
                self._DrawLeaf(
                    gc,
                    startIndex,
                    endIndex,
                    yMin,
                    yMax,
                    event,
                    self._eventWidth,
                )
        for child in self.GetChildren(event):
            self._DrawEvent(gc, child)

    def _OnPaint(self, event):
        """
        Gérez l’événement de peinture.

        Args:
            event (wx.PaintEvent): The paint event.
        """
        log.debug(f"CalendarCanvas._OnPaint : lancé pour event={event}")
        w, h = self.GetClientSize()
        log.debug("CalendarCanvas._OnPaint : w=%s et h=%s", w, h)
        vw = max(w, self._minSize[0])
        vh = max(h, self._minSize[1])
        log.debug("CalendarCanvas._OnPaint : vw=%s et vh=%s", vw, vh)
        dx = dy = 0
        if self._hScroll.IsShown():
            vh -= self._hScroll.GetClientSize()[1]
            dx = self._hScroll.GetThumbPosition()
        if self._vScroll.IsShown():
            vw -= self._vScroll.GetClientSize()[0]
            dy = self._vScroll.GetThumbPosition()
        log.debug("CalendarCanvas._OnPaint : vw=%s, vh=%s, dx=%s et dy=%s", vw, vh, dx, dy)

        # Crée un bitmap tampon pour dessiner hors écran
        bmp = wx.Bitmap(vw, vh)
        # Créer un contexte de périphérique de mémoire pour dessiner des graphiques dans le bitmap.
        memDC = wx.MemoryDC()
        memDC.SelectObject(bmp)
        log.debug("CalendarCanvas._OnPaint : wx.MemoryDC.IsOk ? %s", memDC.IsOk())
        try:
            memDC.SetBackground(wx.WHITE_BRUSH)
            memDC.Clear()
            # Créer un context graphique pour memDC
            gc = wx.GraphicsContext.Create(memDC)
            self._Draw(gc, vw, vh, dx, dy)
            # Appelle la méthode de dessin principale pour remplir le DC
            dc = wx.PaintDC(self)
            dc.Blit(0, 0, vw, vh, memDC, 0, 0)
        finally:
            # Libère le bitmap du contexte mémoire
            memDC.SelectObject(wx.NullBitmap)

    def _Draw(self, gc, vw, vh, dx, dy):
        """
        Dessinez la vue du calendrier.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            vw (int): The view width.
            vh (int): The view height.
            dx (int): The horizontal offset.
            dy (int): The vertical offset.
        """
        log.debug(f"CalendarCanvas._Draw : Lancé avec gc={gc}, vw={vw}, vh={vh}, dx={dx}, dy={dy}.")
        gc.PushState()
        try:
            gc.Translate(-dx, 0.0)
            self._DrawHeader(gc, vw, vh)
        finally:
            gc.PopState()

        gc.PushState()
        try:
            gc.Translate(-dx, -dy)
            gc.Clip(0, self._marginTop + dy, vw, vh)
            for event in self.GetRootEvents():
                self._DrawEvent(gc, event)
            self._DrawNow(gc, vh + dy)
            self._DrawDragImage(gc)
        finally:
            gc.PopState()

    def _DrawHeader(self, gc, w, h):
        """
        Dessinez l'en-tête de la vue du calendrier.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            w (int): The width.
            h (int): The height.
        """
        log.debug(f"CalendarCanvas._DrawHeader: Dessinez l'en-tête de la vue du calendrier avec gc={gc}, w={w}, h={h}.")
        gc.SetPen(wx.Pen(self._outlineColorDark))
        for startIndex, endIndex in self._daySpans:
            date = (
                    self._start
                    + datetime.timedelta(minutes=self._precision * startIndex)
            ).date()
            x0 = startIndex * self._eventWidth
            x1 = endIndex * self._eventWidth
            if date == datetime.datetime.now().date():
                gc.SetBrush(
                    self._Gradient(
                        gc, self._todayColor, x0, self._marginTop, x1 - x0, h
                    )
                )
            elif self.IsWorked(date):
                gc.SetBrush(wx.WHITE_BRUSH)
            else:
                gc.SetBrush(
                    self._Gradient(
                        gc,
                        self._outlineColorDark,
                        x0,
                        self._marginTop,
                        x1 - x0,
                        h,
                    )
                )
            gc.DrawRectangle(x0, self._marginTop, x1 - x0, h)

        gc.SetFont(wx.NORMAL_FONT, wx.BLACK)
        gc.SetPen(wx.Pen(self._outlineColorDark))
        for startIndex, endIndex in self._headerSpans:
            x0 = startIndex * self._eventWidth
            x1 = endIndex * self._eventWidth
            gc.SetBrush(
                self._Gradient(
                    gc,
                    self._outlineColorLight,
                    x0,
                    0,
                    x1 - x0,
                    self._marginTop - 2.0,
                )
            )
            gc.DrawRectangle(x0, 0, x1 - x0, self._marginTop - 2.0)
            text = shortenText(
                gc,
                self.FormatDateTime(
                    self._start
                    + datetime.timedelta(minutes=self._precision * startIndex)
                ),
                x1 - x0,
            )
            tw, th, _, _ = gc.GetFullTextExtent(text)
            gc.DrawText(
                text, x0 + (x1 - x0 - tw) / 2, (self._marginTop - 2.0 - th) / 2
            )

    def _DrawNow(self, gc, h):
        """
        Dessinez un marqueur pour l’heure actuelle.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            h (int): The height.
        """
        now = datetime.datetime.now()
        x = (
                int(
                    (now - self._start).total_seconds()
                    / 60.0
                    / self._precision
                    * self._eventWidth
                )
                - 0.5
        )
        gc.SetPen(wx.Pen(wx.Colour(0, 128, 0)))
        gc.SetBrush(wx.Brush(wx.Colour(0, 128, 0)))

        path = gc.CreatePath()
        path.MoveToPoint(x - 4.0, self._marginTop)
        path.AddLineToPoint(x + 4.0, self._marginTop)
        path.AddLineToPoint(x, self._marginTop + 4.0)
        path.AddLineToPoint(x, h + self._marginTop)
        path.AddLineToPoint(x, self._marginTop + 4.0)
        path.CloseSubpath()
        gc.DrawPath(path)

    def _DrawDragImage(self, gc):
        """
        Dessinez l'image de déplacement pour l'événement en cours de déplacement.

        Args:
            gc (wx.GraphicsContext): The graphics context.
        """
        if self._mouseDragPos is not None:
            if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:
                d1 = self._mouseDragPos
                d2 = (
                    self.GetEnd(self._mouseOrigin.event)
                    if self._mouseState == self.MS_DRAG_LEFT
                    else self.GetStart(self._mouseOrigin.event)
                )
                d1, d2 = min(d1, d2), max(d1, d2)

                x0 = (
                        int(total_seconds(d1 - self._start) / 60 / self._precision)
                        * self._eventWidth
                )
                x1 = (
                        int(total_seconds(d2 - self._start) / 60 / self._precision)
                        * self._eventWidth
                )
                y0 = (
                        self._coords[self._mouseOrigin.event][4]
                        * (self._eventHeight + self._margin)
                        + self._marginTop
                )
                y1 = (
                        self._coords[self._mouseOrigin.event][5]
                        * (self._eventHeight + self._margin)
                        + self._marginTop
                        - self._margin
                )

                gc.SetBrush(wx.Brush(wx.Colour(0, 0, 128, 128)))
                gc.DrawRoundedRectangle(x0, y0, x1 - x0, y1 - y0, 5.0)

                gc.SetFont(wx.NORMAL_FONT, wx.RED)
                text = self._mouseDragPos.strftime("%c")
                tw, th, _, _ = gc.GetFullTextExtent(text)
                tx = 0
                if self._mouseState == self.MS_DRAG_LEFT:
                    tx = x0 + self._margin
                elif self._mouseState == self.MS_DRAG_RIGHT:
                    tx = x1 - self._margin - tw
                ty = y0 + (y1 - y0 - th) / 2
                gc.DrawText(text, tx, ty)
            elif self._mouseState == self.MS_DRAGGING:
                x0 = (
                        int(
                            total_seconds(self._mouseDragPos - self._start)
                            / 60
                            / self._precision
                        )
                        * self._eventWidth
                )
                x1 = (
                        int(
                            total_seconds(
                                self._mouseDragPos
                                + (
                                        self.GetEnd(self._mouseOrigin.event)
                                        - self.GetStart(self._mouseOrigin.event)
                                )
                                - self._start
                            )
                            / 60
                            / self._precision
                        )
                        * self._eventWidth
                )
                y0 = (
                        self._coords[self._mouseOrigin.event][4]
                        * (self._eventHeight + self._margin)
                        + self._marginTop
                )
                y1 = (
                        self._coords[self._mouseOrigin.event][5]
                        * (self._eventHeight + self._margin)
                        + self._marginTop
                        - self._margin
                )

                gc.SetBrush(wx.Brush(wx.Colour(0, 0, 128, 128)))
                gc.DrawRoundedRectangle(x0, y0, x1 - x0, y1 - y0, 5.0)

                gc.SetFont(wx.NORMAL_FONT, wx.RED)
                text = "%s -> %s" % (
                    self._mouseDragPos.strftime("%c"),
                    (
                            self._mouseDragPos
                            + (
                                    self.GetEnd(self._mouseOrigin.event)
                                    - self.GetStart(self._mouseOrigin.event)
                            )
                    ).strftime("%c"),
                )
                tw, th, _, _ = gc.GetFullTextExtent(text)
                gc.DrawText(
                    text, x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2
                )

    def _GetCursorDate(self):
        """
        Get the date and time at the current cursor position.

        Returns:
            datetime.datetime: The date and time at the cursor position.
        """
        # x, y = self.ScreenToClientXY(*wx.GetMousePosition())
        x, y = self.ScreenToClient(*wx.GetMousePosition())
        if self._hScroll.IsShown():
            x += self._hScroll.GetThumbPosition()
        return self._start + datetime.timedelta(
            minutes=int(self._precision * x / self._eventWidth)
        )

    def _OnResize(self, event=None):
        """
        Handle the resize event.

        Args:
            event (wx.SizeEvent, optional): The resize event. Defaults to None.
        """
        if event is None:
            w, h = self.GetClientSize()
        else:
            w, h = event.GetSize()

        _, hh = self._hScroll.GetClientSize()
        vw, _ = self._vScroll.GetClientSize()

        # DID: wxPyDeprecationWarning: Call to deprecated item. Use SetSize instead.
        # self._hScroll.SetDimensions(0, h - hh, w - vw, hh)
        self._hScroll.SetSize(0, h - hh, w - vw, hh)
        # DID: wxPyDeprecationWarning: Call to deprecated item. Use SetSize instead.
        # self._vScroll.SetDimensions(
        #     w - vw, self._marginTop, int(vw), h - hh - self._marginTop
        # )
        self._vScroll.SetSize(w - vw,
                              self._marginTop,
                              int(vw),
                              h - hh - self._marginTop)

        minW, minH = self._minSize

        # Not perfect, but it will do.
        if w - vw < minW:
            self._hScroll.SetScrollbar(
                self._hScroll.GetThumbPosition(), w - vw, minW, w - vw, True
            )
            self._hScroll.Show()
            h -= hh
        else:
            self._hScroll.Hide()

        if h - hh - self._marginTop < minH:
            self._vScroll.SetScrollbar(
                self._vScroll.GetThumbPosition(),
                h - hh - self._marginTop,
                int(minH),
                h - hh - self._marginTop,
                True,
            )
            self._vScroll.Show()
            w -= vw
        else:
            self._vScroll.Hide()

        self._eventWidth = max(
            self._eventWidthMin, 1.0 * max(w, minW) / self._maxIndex
        )

        if event is not None:
            event.Skip()

    def _OnLeftDown(self, event):
        """
        Handle the left mouse button down event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        result = self.HitTest(event.GetX(), event.GetY())
        if result is None:
            return

        if self._mouseState == self.MS_IDLE:
            changed = False
            if result.event is None:
                if self._selection:
                    changed = True
                    self._selection = set()
                    self.Refresh()
            else:
                if event.ShiftDown():
                    events = []
                    self._Flatten(result.event, events)
                else:
                    events = [result.event]
                events = set(events) & set(self._coords.keys())

                if event.CmdDown():
                    for e in events:
                        if e in self._selection:
                            self._selection.remove(e)
                            changed = True
                        else:
                            self._selection.add(e)
                            changed = True
                else:
                    if self._selection != events:
                        changed = True
                        self._selection = events

                if result.position == result.HIT_IN:
                    self._mouseOrigin = result
                    self._mouseState = self.MS_DRAG_START
                self.Refresh()

            if changed:
                e = wx.PyCommandEvent(wxEVT_EVENT_SELECTION_CHANGED)
                e.selection = set(self._selection)
                e.SetEventObject(self)
                self.ProcessEvent(e)
        elif self._mouseState in [self.MS_HOVER_LEFT, self.MS_HOVER_RIGHT]:
            self.CaptureMouse()
            self._mouseState += self.MS_DRAG_LEFT - self.MS_HOVER_LEFT

    def _OnLeftUp(self, event):
        """
        Handle the left mouse button up event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:
            self.ReleaseMouse()
            wx.SetCursor(wx.NullCursor)

            e = wx.PyCommandEvent(wxEVT_EVENT_DATES_CHANGED)
            e.event = self._mouseOrigin.event
            e.start = (
                self._mouseDragPos
                if self._mouseState == self.MS_DRAG_LEFT
                else self.GetStart(self._mouseOrigin.event)
            )
            e.end = (
                self._mouseDragPos
                if self._mouseState == self.MS_DRAG_RIGHT
                else self.GetEnd(self._mouseOrigin.event)
            )
            e.SetEventObject(self)
            self.ProcessEvent(e)
        elif self._mouseState == self.MS_DRAGGING:
            self.ReleaseMouse()
            wx.SetCursor(wx.NullCursor)

            e = wx.PyCommandEvent(wxEVT_EVENT_DATES_CHANGED)
            e.event = self._mouseOrigin.event
            e.start = self._mouseDragPos
            e.end = e.start + (
                    self.GetEnd(self._mouseOrigin.event)
                    - self.GetStart(self._mouseOrigin.event)
            )
            e.SetEventObject(self)
            self.ProcessEvent(e)

        self._mouseState = self.MS_IDLE
        self._mouseOrigin = None
        self._mouseDragPos = None
        self.Refresh()

    def _OnRightDown(self, event):
        """
        Handle the right mouse button down event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        result = self.HitTest(event.GetX(), event.GetY())
        if result is None:
            return

        changed = False
        if result.event is None:
            if self._selection:
                self._selection = set()
                changed = True
                self.Refresh()
        else:
            if result.event not in self._selection:
                # self._selection = set([result.event])
                self._selection = {result.event}
                changed = True
                self.Refresh()

        if changed:
            e = wx.PyCommandEvent(wxEVT_EVENT_SELECTION_CHANGED)
            e.selection = set(self._selection)
            e.SetEventObject(self)
            self.ProcessEvent(e)

    def _OnMotion(self, event):
        """
        Handle the mouse motion event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        result = self.HitTest(event.GetX(), event.GetY())

        if result is not None:
            if self._mouseState == self.MS_IDLE:
                if result.event is not None and result.position in [
                    result.HIT_START,
                    result.HIT_END,
                ]:
                    self._mouseOrigin = result
                    self._mouseState = (
                        self.MS_HOVER_LEFT
                        if result.position == result.HIT_START
                        else self.MS_HOVER_RIGHT
                    )
                    wx.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
            elif self._mouseState in [self.MS_HOVER_LEFT, self.MS_HOVER_RIGHT]:
                if result.event is None or result.position not in [
                    result.HIT_START,
                    result.HIT_END,
                ]:
                    self._mouseOrigin = None
                    self._mouseDragPos = None
                    self._mouseState = self.MS_IDLE
                    wx.SetCursor(wx.NullCursor)

        if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:
            dateTime = self._GetCursorDate()
            precision = (
                self._gridSize if event.ShiftDown() else self._precision
            )
            if self._mouseState == self.MS_DRAG_LEFT:
                dateTime = self._start + datetime.timedelta(
                    seconds=math.floor(
                        total_seconds(dateTime - self._start) / 60 / precision
                    ) * precision * 60
                )
                dateTime = min(
                    self.GetEnd(self._mouseOrigin.event)
                    - datetime.timedelta(minutes=precision),
                    dateTime,
                )
            if self._mouseState == self.MS_DRAG_RIGHT:
                dateTime = self._start + datetime.timedelta(
                    seconds=math.ceil(
                        total_seconds(dateTime - self._start) / 60 / precision
                    ) * precision * 60
                )
                dateTime = max(
                    self.GetStart(self._mouseOrigin.event)
                    + datetime.timedelta(minutes=precision),
                    dateTime,
                )
            self._mouseDragPos = dateTime

            self.Refresh()
        elif self._mouseState == self.MS_DRAG_START:
            if (
                    self.GetStart(self._mouseOrigin.event) is not None
                    and self.GetEnd(self._mouseOrigin.event) is not None
            ):
                dx = abs(event.GetX() - self._mouseOrigin.x)
                dy = abs(event.GetY() - self._mouseOrigin.y)
                if (
                        dx > wx.SystemSettings.GetMetric(wx.SYS_DRAG_X) / 2
                        or dy > wx.SystemSettings.GetMetric(wx.SYS_DRAG_Y) / 2
                ):
                    self.CaptureMouse()
                    wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                    self._mouseState = self.MS_DRAGGING
                    self.Refresh()
        elif self._mouseState == self.MS_DRAGGING:
            dx = event.GetX() - self._mouseOrigin.x
            precision = (
                self._gridSize if event.ShiftDown() else self._precision
            )
            delta = datetime.timedelta(
                minutes=math.floor(
                    dx / self._eventWidth * self._precision / precision
                )
                        * precision
            )
            self._mouseDragPos = self.GetStart(self._mouseOrigin.event) + delta
            self.Refresh()

    def _OnScroll(self, event):
        """
        Handle the scroll event.

        Args:
            event (wx.ScrollEvent): The scroll event.
        """
        self.Refresh()
        event.Skip()

    def _Gradient(self, gc, color, x, y, w, h):
        """
        Create a gradient brush.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            color (wx.Colour): The color.
            x (float): The x-coordinate.
            y (float): The y-coordinate.
            w (float): The width.
            h (float): The height.

        Returns:
            wx.GraphicsBrush: The gradient brush.
        """
        r = color.Red()
        g = color.Green()
        b = color.Blue()
        return gc.CreateLinearGradientBrush(
            x,
            y,
            x + w,
            y + h,
            color,
            wx.Colour(
                int(self._gradVal * r + (1.0 - self._gradVal) * 255),
                int(self._gradVal * g + (1.0 - self._gradVal) * 255),
                int(self._gradVal * b + (1.0 - self._gradVal) * 255),
            ),
        )

    def _DrawParent(
            self,
            gc,
            startIndex,
            endIndex,
            startIndexRecursive,
            endIndexRecursive,
            y,
            yMax,
            event,
            w,
    ):
        """
        Draw a parent event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            startIndex (int): The start index.
            endIndex (int): The end index.
            startIndexRecursive (int): The recursive start index.
            endIndexRecursive (int): The recursive end index.
            y (int): The y-coordinate.
            yMax (int): The maximum y-coordinate.
            event: The event to draw.
            w (float): The width.
        """
        x0 = startIndexRecursive * w
        x1 = endIndexRecursive * w - 1.0
        y0 = y * (self._eventHeight + self._margin) + self._marginTop
        y1 = y0 + self._eventHeight
        y2 = (
                yMax * (self._eventHeight + self._margin)
                + self._marginTop
                - self._margin
        )
        color = self.GetBackgroundColor(event)

        # Overall box
        self._DrawBox(
            gc,
            event,
            x0 - self._margin / 3,
            y0 - self._margin / 3,
            x1 + self._margin / 3,
            y2 + self._margin / 3,
            wx.Colour(
                int((color.Red() + self._outlineColorLight[0]) / 2),
                int((color.Green() + self._outlineColorLight[1]) / 2),
                int((color.Blue() + self._outlineColorLight[2]) / 2),
            ),
        )

        if startIndex is not None:
            x0 = startIndex * w
        if endIndex is not None:
            x1 = endIndex * w - 1.0

        # Span
        path = gc.CreatePath()
        delta = self._eventHeight / 4
        path.MoveToPoint(x0, y0)
        path.AddLineToPoint(x1, y0)
        path.AddLineToPoint(x1, y1 - delta)
        path.AddLineToPoint(x1 - delta, y1)
        path.AddLineToPoint(x1 - 2 * delta, y1 - delta)
        path.AddLineToPoint(x0 + 2 * delta, y1 - delta)
        path.AddLineToPoint(x0 + delta, y1)
        path.AddLineToPoint(x0, y1 - delta)
        path.CloseSubpath()

        gc.SetBrush(self._Gradient(gc, color, x0, y0, x1 - x0, y1 - y0))
        gc.FillPath(path)

        gc.SetPen(wx.Pen(wx.Colour(*self._outlineColorDark)))
        gc.DrawPath(path)

        x0 = max(0.0, x0)
        x1 = min(self._maxIndex * self._eventWidth, x1)

        # Progress
        x0, y0, x1, y1 = self._DrawProgress(gc, event, x0, y0, x1, y1)

        y1 -= delta

        # Text & icons
        x0, y0, x1, y1 = self._DrawIcons(gc, event, x0, y0, x1, y1)
        self._DrawText(gc, event, x0, y0, x1, y1)

    def _DrawLeaf(self, gc, startIndex, endIndex, yMin, yMax, event, w):
        """
        Draw a leaf event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            startIndex (int): The start index.
            endIndex (int): The end index.
            yMin (int): The minimum y-coordinate.
            yMax (int): The maximum y-coordinate.
            event: The event to draw.
            w (float): The width.
        """
        x0 = startIndex * w
        x1 = endIndex * w - 1.0
        y0 = yMin * (self._eventHeight + self._margin) + self._marginTop
        y1 = (
                yMax * (self._eventHeight + self._margin)
                + self._marginTop
                - self._margin
        )

        # Box
        self._DrawBox(
            gc, event, x0, y0, x1, y1, self.GetBackgroundColor(event)
        )

        x0 = max(0.0, x0)
        x1 = min(self._maxIndex * self._eventWidth, x1)

        # Progress
        x0, y0, x1, y1 = self._DrawProgress(gc, event, x0, y0, x1, y1)

        # Text & icons
        x0, y0, x1, y1 = self._DrawIcons(gc, event, x0, y0, x1, y1)
        self._DrawText(gc, event, x0, y0, x1, y1)

    def _DrawBox(self, gc, event, x0, y0, x1, y1, color):
        """
        Draw a box around the event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            event: The event to draw.
            x0 (float): The x-coordinate of the top-left corner.
            y0 (float): The y-coordinate of the top-left corner.
            x1 (float): The x-coordinate of the bottom-right corner.
            y1 (float): The y-coordinate of the bottom-right corner.
            color (wx.Colour): The color of the box.
        """
        outline = wx.Colour(*self._outlineColorLight)

        if event in self._selection:
            outline = wx.BLUE
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)

        path = gc.CreatePath()
        path.AddRoundedRectangle(x0, y0, x1 - x0, y1 - y0, 5.0)
        gc.SetBrush(self._Gradient(gc, color, x0, y0, x1, y1))
        gc.FillPath(path)

        gc.SetPen(wx.Pen(outline))
        gc.DrawPath(path)

    def _DrawProgress(self, gc, event, x0, y0, x1, y1):
        """
        Draw the progress of the event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            event: The event to draw.
            x0 (float): The x-coordinate of the top-left corner.
            y0 (float): The y-coordinate of the top-left corner.
            x1 (float): The x-coordinate of the bottom-right corner.
            y1 (float): The y-coordinate of the bottom-right corner.

        Returns:
            tuple: The updated coordinates (x0, y0, x1, y1).
        """
        p = self.GetProgress(event)
        if p is not None:
            px0 = x0 + self._eventHeight / 2
            px1 = x1 - self._eventHeight / 2
            py0 = y0 + (self._eventHeight / 4 - self._eventHeight / 8) / 2
            py1 = py0 + self._eventHeight / 8

            gc.SetBrush(wx.Brush(self._outlineColorDark))
            gc.DrawRectangle(px0, py0, px1 - px0, py1 - py0)

            gc.SetBrush(
                self._Gradient(
                    gc, wx.BLUE, px0, py0, px0 + (px1 - px0) * p, py1
                )
            )
            gc.DrawRectangle(px0, py0, (px1 - px0) * p, py1 - py0)

            y0 = py1
        return x0, y0, x1, y1

    def _DrawText(self, gc, event, x0, y0, x1, y1):
        """
        Draw the text of the event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            event: The event to draw.
            x0 (float): The x-coordinate of the top-left corner.
            y0 (float): The y-coordinate of the top-left corner.
            x1 (float): The x-coordinate of the bottom-right corner.
            y1 (float): The y-coordinate of the bottom-right corner.
        """
        log.debug(f"CalendarCanvas._DrawText : Dessine le texte avec gc={gc}, event={event}, x0={x0}, y0={y0}, x1={x1}, y1={y1}.")
        gc.SetFont(
            self.GetFont(event),
            (
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
                if event in self._selection
                else self.GetForegroundColor(event)
            ),
        )
        text = shortenText(gc, self.GetText(event), int(x1 - x0 - self._margin * 2))
        w, h, _, _ = gc.GetFullTextExtent(text)
        log.debug(f"CalendarCanvas._DrawText : Dessine {text} ici : ({x0 + self._margin}, {y0 + self._eventHeight / 3 + (y1 - y0 - h - 2 * self._eventHeight / 3) / 2}).")
        gc.DrawText(
            text,
            x0 + self._margin,
            y0
            + self._eventHeight / 3
            + (y1 - y0 - h - 2 * self._eventHeight / 3) / 2,
        )

    def _DrawIcons(self, gc, event, x0, y0, x1, y1):
        """
        Draw the icons of the event.

        Args:
            gc (wx.GraphicsContext): The graphics context.
            event: The event to draw.
            x0 (float): The x-coordinate of the top-left corner.
            y0 (float): The y-coordinate of the top-left corner.
            x1 (float): The x-coordinate of the bottom-right corner.
            y1 (float): The y-coordinate of the bottom-right corner.

        Returns:
            tuple: The updated coordinates (x0, y0, x1, y1).
        """
        cx = x0
        icons = self.GetIcons(event)
        if icons:
            cx += self._margin
            for icon in icons:
                w = icon.GetWidth()
                h = icon.GetHeight()
                gc.DrawIcon(icon, cx, y0 + (y1 - y0 - h) / 2, w, h)
                cx += w + self._margin
        return cx, y0, x1, y1

    def _GetStartRecursive(self, event):
        """
        Get the recursive start date and time for the event.

        Args:
            event: The event to get the start date and time for.

        Returns:
            datetime.datetime: The recursive start date and time.
        """
        dt = self.GetStart(event)
        ls = [] if dt is None else [dt]
        for child in self.GetChildren(event):
            dt = self._GetStartRecursive(child)
            if dt is not None:
                ls.append(dt)
        return min(ls) if ls else None

    def _GetEndRecursive(self, event):
        """
        Get the recursive end date and time for the event.

        Args:
            event: The event to get the end date and time for.

        Returns:
            datetime.datetime: The recursive end date and time.
        """
        dt = self.GetEnd(event)
        ls = [] if dt is None else [dt]
        for child in self.GetChildren(event):
            dt = self._GetEndRecursive(child)
            if dt is not None:
                ls.append(dt)
        return max(ls) if ls else None

    def _Invalidate(self):
        """
        Invalidate the calendar view and recalculate the coordinates of events.
        """
        self._coords = dict()
        watermark = _Watermark()
        self._maxIndex = int(
            total_seconds(self._end - self._start) / self._precision / 60
        )

        def computeEvent(event):
            eventStart = self.GetStart(event)
            eventEnd = self.GetEnd(event)
            eventRStart = self._GetStartRecursive(event)
            eventREnd = self._GetEndRecursive(event)

            if (
                    eventRStart is not None
                    and eventREnd is not None
                    and not (eventRStart >= self._end or eventREnd < self._start)
            ):
                rstart = int(
                    math.floor(
                        total_seconds(eventRStart - self._start)
                        / self._precision
                        / 60
                    )
                )
                start = (
                    None
                    if eventStart is None
                    else int(
                        math.floor(
                            total_seconds(eventStart - self._start)
                            / self._precision
                            / 60
                        )
                    )
                )
                rend = int(
                    math.floor(
                        total_seconds(eventREnd - self._start)
                        / self._precision
                        / 60
                    )
                )
                end = (
                    None
                    if eventEnd is None
                    else int(
                        math.floor(
                            total_seconds(eventEnd - self._start)
                            / self._precision
                            / 60
                        )
                    )
                )
                if rend > rstart:
                    y = watermark.height(rstart, rend)
                    watermark.add(rstart, rend, y + 1)
                    yMax = y + 1
                    for child in self.GetChildren(event):
                        yMax = max(yMax, computeEvent(child))
                    self._coords[event] = (start, end, rstart, rend, y, yMax)
                    return yMax

        for rootEvent in self.GetRootEvents():
            computeEvent(rootEvent)

        bmp = wx.EmptyBitmap(10, 10)  # Don't care
        memDC = wx.MemoryDC()
        memDC.SelectObject(bmp)
        try:
            gc = wx.GraphicsContext.Create(memDC)
            gc.SetFont(wx.NORMAL_FONT, wx.BLACK)

            self._headerSpans = []
            self._daySpans = []
            startIdxHeader = 0
            startIdxDay = 0
            currentFmt = self.FormatDateTime(self._start)
            currentDay = self._start.date()
            headerWidth = gc.GetTextExtent(currentFmt)[0]
            for idx in range(1, self._maxIndex):
                dateTime = self._start + datetime.timedelta(
                    minutes=self._precision * idx
                )
                fmt = self.FormatDateTime(dateTime)
                if fmt != currentFmt:
                    headerWidth += gc.GetTextExtent(fmt)[0]
                    self._headerSpans.append((startIdxHeader, idx))
                    startIdxHeader = idx
                    currentFmt = fmt
                if dateTime.date() != currentDay:
                    self._daySpans.append((startIdxDay, idx))
                    startIdxDay = idx
                    currentDay = dateTime.date()
            self._headerSpans.append((startIdxHeader, self._maxIndex))
            self._daySpans.append((startIdxDay, self._maxIndex))
            headerWidth += self._margin * 2 * len(self._headerSpans)

            self._minSize = (
                int(max(headerWidth, self._eventWidthMin * self._maxIndex)),
                self._marginTop
                + (watermark.totalHeight() - 1)
                * (self._eventHeight + self._margin),
            )
            self._OnResize()
        finally:
            memDC.SelectObject(wx.NullBitmap)


class CalendarPrintout(wx.Printout):
    """
    A printout class for printing the calendar view.
    """

    def __init__(self, calendar, settings, *args, **kwargs):
        """
        Initialize the CalendarPrintout instance.

        Args:
            calendar (CalendarCanvas): The calendar canvas to print.
            settings (dict): The print settings.
        """
        super().__init__(*args, **kwargs)
        self._calendar = calendar
        self._settings = settings
        self._count = None

    def _PageCount(self):
        """
        Calculate the number of pages required to print the calendar.

        Returns:
            int: The number of pages.
        """
        if self._count is None:
            minW, minH = self._calendar._minSize
            dc = self.GetDC()
            dcw, dch = dc.GetSize()
            cw = minW
            ch = minW * dch / dcw
            cells = int(
                math.ceil(
                    1.0
                    * (ch - self._calendar._marginTop)
                    / (self._calendar._eventHeight + self._calendar._margin)
                )
            )
            total = (
                    int(
                        math.ceil(
                            1.0
                            * (minH - self._calendar._marginTop)
                            / (
                                    self._calendar._eventHeight
                                    + self._calendar._margin
                            )
                        )
                    )
                    + 1
            )
            self._count = int(math.ceil(1.0 * total / cells))
        return self._count

    def GetPageInfo(self):
        """
        Get the page information for printing.

        Returns:
            tuple: The page information (minPage, maxPage, fromPage, toPage).
        """
        return 1, self._PageCount(), 1, 1

    def HasPage(self, page):
        """
        Check if the specified page exists.

        Args:
            page (int): The page number.

        Returns:
            bool: True if the page exists, False otherwise.
        """
        return page <= self._PageCount()

    def OnPrintPage(self, page):
        """
        Print the specified page.

        Args:
            page (int): The page number.
        """
        # Returns:
        #    bool: True if the page was printed successfully, False otherwise.
        # """
        # Cannot print with a GraphicsContext...
        minW, minH = self._calendar._minSize
        dc = self.GetDC()
        dcw, dch = dc.GetSize()
        cw = minW
        ch = minW * dch / dcw
        cells = int(
            math.ceil(
                1.0
                * (ch - self._calendar._marginTop)
                / (self._calendar._eventHeight + self._calendar._margin)
            )
        )
        dy = int(
            1.0
            * cells
            * (self._calendar._eventHeight + self._calendar._margin)
            * (page - 1)
        )

        bmp = wx.Bitmap(cw, ch)
        memDC = wx.MemoryDC()
        memDC.SelectObject(bmp)
        try:
            memDC.SetBackground(wx.WHITE_BRUSH)
            memDC.Clear()

            oldWidth = self._calendar._eventWidth
            self._calendar._eventWidth = self._calendar._eventWidthMin
            try:
                gc = wx.GraphicsContext.Create(memDC)
                self._calendar._Draw(gc, cw, ch, 0, dy)
            finally:
                self._calendar._eventWidth = oldWidth
            dc.SetUserScale(1.0 * dcw / cw, 1.0 * dch / ch)
            dc.Blit(0, 0, cw, ch, memDC, 0, 0)
        finally:
            memDC.SelectObject(wx.NullBitmap)
        # return True
