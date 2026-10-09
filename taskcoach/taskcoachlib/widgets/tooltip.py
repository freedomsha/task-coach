"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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

Module `tooltip.py`

Ce module fournit des classes et des fonctionnalités pour gérer les info-bulles
dynamique dans Task Coach. Ces info-bulles offrent des informations détaillées
et enrichies, pouvant inclure des icônes et du texte formaté.

Les classes principales incluent :
    - `ToolTipMixin` : Permet d'ajouter une prise en charge des info-bulles dynamiques
      à un contrôle existant.
    - `ToolTipBase` : Classe de base pour les fenêtres d'info-bulles.
    - `SimpleToolTip` : Une implémentation simple d'info-bulles avec du texte et des icônes.

Compatibilité :
    - Le comportement des info-bulles varie en fonction du système d'exploitation
      (Windows, MacOS ou autres).

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.
"""

# from builtins import range
# from builtins import object
import logging
from taskcoachlib import operating_system
import wx
import textwrap

log = logging.getLogger(__name__)


class ToolTipMixin(object):
    # class ToolTipMixin(wx.Window):  # à essayer pour retrouver des unresolved attribute reference 'GetMainWindow' bind et autres
    """Mixin permettant d'ajouter des info-bulles dynamiques à un contrôle.

    Sous-classez ceci et remplacez OnBeforeShowToolTip pour fournir
    une info-bulle dynamique sur un contrôle.
    Cette classe s'attend à ce que les classes dans lesquelles elle est
    intégrée définissent une méthode `GetMainWindow` pour fournir la fenêtre
    principale associée.
        Ce mixin dépend de la méthode `GetMainWindow`, qui doit être implémentée
        par les classes finales. Les classes suivantes utilisent ce mixin et
        fournissent une implémentation de `GetMainWindow` :
            - calendarwidget
            - hcalendar
            - itemctrl
            - searchctrl
            - squaremap
            - timeline

    Utilisez ce mixin uniquement avec des classes fournissant cette méthode.

    Ce mixin dépend de fonctionnalités spécifiques à wxPython, notamment :
    - `Bind` : Méthode pour lier des événements.
    - `PopupMenu` : Méthode pour afficher un menu contextuel.
    - `ClientToScreenXY` : Méthode pour convertir des coordonnées locales en
      coordonnées de l'écran.

    Ce mixin suppose que la classe finale hérite d'une classe wxPython comme
    `wx.Window` ou `wx.Control`.

    Cette classe peut être sous-classée pour ajouter un comportement d'info-bulles à
    un contrôle. Les info-bulles sont affichées lorsqu'une souris survole le contrôle,
    et leur contenu peut être défini dynamiquement en redéfinissant `OnBeforeShowToolTip`.

    Attributs :
        - `__enabled` : Indique si les info-bulles sont activées.
        - `__timer` : Minuterie utilisée pour retarder l'affichage des info-bulles.
        - `__tip` : Instance actuelle de la fenêtre d'info-bulle affichée.
        - `__position` : Position de l'info-bulle par rapport à la souris.
        - `__text` : Texte de l'info-bulle.
        - `__frozen` : Indique si l'info-bulle est figée (ne doit pas changer).

    Méthodes principales :
        - `SetToolTipsEnabled` : Active ou désactive les info-bulles.
        - `ShowTip` : Affiche une info-bulle à une position donnée.
        - `HideTip` : Masque l'info-bulle actuelle.
        - `OnBeforeShowToolTip` : Définit dynamiquement le contenu de l'info-bulle.

    Méthodes privées :
        - `__OnMotion` : Gère le mouvement de la souris pour afficher ou cacher les info-bulles.
        - `__OnLeave` : Masque l'info-bulle lorsque la souris quitte la fenêtre.
        - `__OnTimer` : Affiche l'info-bulle après une minuterie.
    """

    def __init__(self, *args, **kwargs):
        # def __init__(self, parent, id=wx.ID_ANY,  *args, **kwargs):
        log.debug(f"ToolTipMixin.__init__ : avant super args={args}, kwargs={kwargs}")
        try:
            super().__init__(*args, **kwargs)
        except Exception as e:
            log.error("La méthode super pose problème", exc_info=True)
            log.debug(f"Plante après ça !")
        self.__enabled = kwargs.pop("tooltipsEnabled", True)
        # super().__init__(parent, id, *args, **kwargs)

        # self.__timer = wx.Timer(self, wx.NewId())
        # self.__timer = wx.Timer(self, wx.NewIdRef().GetId())
        self.__timer = wx.Timer(self, wx.ID_ANY)

        self.__tip = None
        self.__position = (0, 0)
        self.__text = None
        self.__frozen = True

        # Unresolved attribute reference 'GetMainWindow' for class 'ToolTipMixin' :
        self.GetMainWindow().Bind(wx.EVT_MOTION, self.__OnMotion)
        self.GetMainWindow().Bind(wx.EVT_LEAVE_WINDOW, self.__OnLeave)
        self.Bind(wx.EVT_TIMER, self.__OnTimer, id=self.__timer.GetId())
        log.debug(f"ToolTipMixin initialisé !")

    # # Cette méthode ne passe pas le test TreeCtrlTest ! :
    # def GetMainWindow(self):
    #     """
    #     Retourne la fenêtre principale associée à ce widget.
    #
    #     Doit être implémenté dans les classes qui utilisent ce mixin.
    #     Si cette méthode n'est pas redéfinie, une exception est levée.
    #
    #     Returns :
    #         (wx.Window) : La fenêtre principale associée.
    #
    #     Raises :
    #         NotImplementedError : Si la méthode n'est pas implémentée dans
    #                               la classe finale.
    #     """
    #     # raise NotImplementedError(
    #     #     "GetMainWindow doit être implémenté dans une sous-classe qui utilise ToolTipMixin."
    #     # )
    #     # Utiliser un mécanisme basé sur wx.GetTopLevelParent comme solution de secours
    #     #
    #     # Si ToolTipMixin est toujours utilisé dans des widgets wxPython,
    #     # ajouter une implémentation par défaut basée sur wx.GetTopLevelParent.
    #     # Cela couvre les cas où GetMainWindow n'est pas explicitement défini dans une sous-classe.
    #     # """
    #     # Retourne la fenêtre principale associée à ce widget en utilisant
    #     # `wx.GetTopLevelParent`.
    #     #
    #     # Cette méthode peut être redéfinie dans les sous-classes si nécessaire.
    #     #
    #     # Returns :
    #     #     wx.Window : La fenêtre principale du widget.
    #     # """
    #     if isinstance(self, wx.Window):
    #         return wx.GetTopLevelParent(self)
    #     return None

    # def Bind(self, event, handler, *args, **kwargs):
    #     """
    #     Lie un événement à un gestionnaire si la méthode est disponible.
    #
    #     Args :
    #         event : Type d'événement à lier.
    #         handler : Gestionnaire à exécuter lorsque l'événement est déclenché.
    #     """
    #     log.debug("ToolTipMixin.Bind : Essaie de lier un événement {event} avec un gestionnaire {handler} si disponible.")
    #     if hasattr(super(), "Bind"):
    #         return super().Bind(event, handler, *args, **kwargs)
    #     raise NotImplementedError(
    #         "Bind est indisponible dans cette classe. "
    #         "Assurez-vous que ToolTipMixin est utilisé avec une classe wxPython."
    #     )

    # def ClientToScreenXY(self, x, y):
    #     """
    #     Convertit les coordonnées du client en coordonnées de l'écran.
    #
    #     Args :
    #         x (int) : Coordonnée X dans le référentiel local du client.
    #         y (int) : Coordonnée Y dans le référentiel local du client.
    #
    #     Returns :
    #         tuple : Coordonnées X et Y dans le référentiel de l'écran.
    #     """
    #     if hasattr(super(), "ClientToScreenXY"):
    #         return super().ClientToScreenXY(x, y)
    #     elif hasattr(super(), "ClientToScreen"):
    #         return super().ClientToScreen(x, y)
    #     raise NotImplementedError(
    #         "ClientToScreenXY est indisponible. Cette méthode nécessite "
    #         "un widget wxPython valide."
    #     )

    def SetToolTipsEnabled(self, enabled):
        """
        Activer ou désactiver les info-bulles pour ce contrôle.

        Args :
            enabled (bool) : `True` pour activer les info-bulles, `False` pour les désactiver.
        """
        self.__enabled = enabled

    def PopupMenu(self, menu):
        self.__frozen = False
        super().PopupMenu(menu)
        self.__frozen = True

    def ShowTip(self, x, y):
        """
        Affiche une info-bulle à la position spécifiée.

        L'info-bulle est ajustée pour s'assurer qu'elle reste visible dans
        la zone d'affichage de l'écran.

        Args :
            x (int) : Position X de l'info-bulle.
            y (int) : Position Y de l'info-bulle.
        """
        # Assurez-vous que nous ne sommes pas trop grands (dans la direction Y
        # de toute façon) pour la zone d'affichage du bureau.
        # Cela ne fonctionne pas sous Linux car
        # ClientDisplayRect() renvoie la taille totale de l'affichage, pas
        # en tenant compte de la barre des tâches...

        if self.__frozen:
            theDisplay = wx.Display(wx.Display.GetFromPoint(wx.Point(x, y)))
            displayX, displayY, displayWidth, displayHeight = theDisplay.GetClientArea()
            # tipWidth, tipHeight = self.__tip.GetSizeTuple()
            tipWidth, tipHeight = self.__tip.GetSize()

            if tipHeight > displayHeight:
                # Too big. Take as much space as possible.
                y = 5
                tipHeight = displayHeight - 10
            elif y + tipHeight > displayY + displayHeight:
                # Ajustez y pour que toute la pointe soit visible.
                y = displayY + displayHeight - tipHeight - 5

            if tipWidth > displayWidth:
                x = 5
            elif x + tipWidth > displayX + displayWidth:
                x = displayX + displayWidth - tipWidth - 5

            self.__tip.Show(x, y, tipWidth, tipHeight)

    def DoShowTip(self, x, y, tip):
        self.__tip = tip
        self.ShowTip(x, y)

    def HideTip(self):
        if self.__tip:
            self.__tip.Hide()

    def OnBeforeShowToolTip(self, x, y):
        """Doit renvoyer une instance de wx.Frame qui sera affichée sous la forme
        d'info-bulle, ou Aucun.

        Doit être redéfinie pour fournir dynamiquement une info-bulle.

        Cette méthode est appelée juste avant l'affichage de l'info-bulle.
        Retournez une instance de `wx.Frame` représentant l'info-bulle, ou `None`
        si aucune info-bulle ne doit être affichée.

        Args :
            x (int) : Position X de la souris.
            y (int) : Position Y de la souris.

        Returns :
            wx.Frame | None : Contenu de l'info-bulle ou `None`.
        """
        raise NotImplementedError  # pragma: no cover

    def __OnMotion(self, event):
        x, y = event.GetPosition()

        self.__timer.Stop()

        if self.__tip is not None:
            self.HideTip()
            self.__tip = None

        if self.__enabled:
            newTip = self.OnBeforeShowToolTip(x, y)
            if newTip is not None:
                self.__tip = newTip
                self.__tip.Bind(wx.EVT_MOTION, self.__OnTipMotion)
                self.__position = (x + 20, y + 10)
                self.__timer.Start(200, True)

        event.Skip()

    def __OnTipMotion(self, event):  # pylint: disable=W0613
        self.HideTip()

    def __OnLeave(self, event):
        self.__timer.Stop()

        if self.__tip is not None:
            self.HideTip()
            self.__tip = None

        event.Skip()

    def __OnTimer(self, event):  # pylint: disable=W0613
        self.ShowTip(*self.GetMainWindow().ClientToScreenXY(*self.__position))
        # self.ShowTip(*self.GetMainWindow().ClientToScreen(*self.__position))


if operating_system.isWindows():

    class ToolTipBase(wx.MiniFrame):
        """
        Classe de base pour afficher une fenêtre d'info-bulle.

        Le comportement de cette classe dépend du système d'exploitation :
        - Sur Windows, une fenêtre `wx.MiniFrame` est utilisée.
        - Sur MacOS, une fenêtre `wx.Frame` est utilisée.
        - Sur les autres systèmes, une fenêtre `wx.PopupWindow` est utilisée.

        Méthodes principales :
            - `Show` : Affiche l'info-bulle à une position et taille données.
            - `Hide` : Masque l'info-bulle (implémentation spécifique selon l'OS).
        """
        def __init__(self, parent):
            style = wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT | wx.NO_BORDER
            super().__init__(parent, wx.ID_ANY, "Tooltip", style=style)

        def Show(self, x, y, w, h, show):  # pylint: disable=W0221 Window:def Show(self, show=True):
            """
            Affiche l'info-bulle à la position spécifiée avec la taille donnée.

            Args :
                x (int) : Position X de l'info-bulle.
                y (int) : Position Y de l'info-bulle.
                w (int) : Largeur de l'info-bulle.
                h (int) : Hauteur de l'info-bulle.
                show (bool) :
            """
            # self.SetDimensions(x, y, w, h)
            self.SetSize(x, y, w, h)  # Inverser les 2 lignes ? non ?
            try:
                super().Show(show=show)
            except Exception:
                pass

elif operating_system.isMac():

    class ToolTipBase(wx.Frame):
        def __init__(self, parent):  # pylint: disable=E1003
            style = wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT | wx.NO_BORDER
            super().__init__(parent, wx.ID_ANY, "ToolTip", style=style)

            # There are some subtleties on Mac regarding multi-monitor
            # displays...

            self.__maxWidth, self.__maxHeight = 0, 0
            for index in range(wx.Display.GetCount()):
                x, y, width, height = wx.Display(index).GetGeometry()
                self.__maxWidth = max(self.__maxWidth, x + width)
                self.__maxHeight = max(self.__maxHeight, y + height)

            self.MoveXY(self.__maxWidth, self.__maxHeight)
            try:
                super().Show()
            except Exception:
                pass

        def Show(self, x, y, width, height):  # pylint: disable=W0221
            # self.SetDimensions(x, y, width, height)
            self.SetSize(x, y, width, height)

        def Hide(self):  # pylint: disable=W0221
            self.MoveXY(self.__maxWidth, self.__maxHeight)

else:

    class ToolTipBase(wx.PopupWindow):
        def Show(self, x, y, width, height, show):  # pylint: disable=E1003,W0221
            # self.SetDimensions(x, y, width, height)
            self.SetSize(x, y, width, height)
            try:
                super().Show(show=show)  # méthode wx ! n'a pas d'équivalent sur tkinter.
            except Exception:
                pass


class SimpleToolTip(ToolTipBase):
    """
    Classe d'info-bulle simple affichant du texte et des icônes.

    Cette classe permet d'afficher des info-bulles contenant une liste de
    sections avec du texte et des icônes. Les lignes longues sont automatiquement
    adaptées pour s'ajuster à la largeur maximale spécifiée.

    Méthodes principales :
        - `SetData` : Définit les données (texte et icônes) à afficher.
        - `OnPaint` : Gère le rendu graphique de l'info-bulle.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.data = []
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetData(self, data):
        """
        Définit les données affichées dans l'info-bulle.

        Args :
            data (list) : Liste de tuples contenant des icônes et des lignes de texte.
        """
        self.data = self._wrapLongLines(data)
        self.SetSize(self._calculateSize())
        self.Refresh()  # Needed on Mac OS X

    def _wrapLongLines(self, data):
        """
        Ajuste les lignes longues pour qu'elles respectent une largeur maximale.

        Args :
            data (list) : Liste de données avec texte et icônes.

        Returns :
            list : Liste de données avec les lignes ajustées.
        """
        wrappedData = []
        wrapper = textwrap.TextWrapper(width=78)
        for icon, lines in data:
            wrappedLines = []
            for line in lines:
                wrappedLines.extend(wrapper.fill(line).split("\n"))
            wrappedData.append((icon, wrappedLines))
        return wrappedData

    def _calculateSize(self):
        dc = wx.ClientDC(self)
        self._setFontBrushAndPen(dc)
        width, height = 0, 0
        for sectionIndex in range(len(self.data)):
            sectionWidth, sectionHeight = self._calculateSectionSize(dc, sectionIndex)
            width = max(width, sectionWidth)
            height += sectionHeight
        return wx.Size(width + 6, height + 6)

    def _calculateSectionSize(self, dc, sectionIndex):
        icon, lines = self.data[sectionIndex]
        sectionWidth, sectionHeight = 0, 0
        for line in lines:
            lineWidth, lineHeight = self._calculateLineSize(dc, line)
            sectionHeight += lineHeight + 1
            sectionWidth = max(sectionWidth, lineWidth)
        if 0 < sectionIndex < len(self.data) - 1:
            sectionHeight += 3  # Horizontal space between sections
        if icon:
            sectionWidth += 24  # Reserve width for icon(s)
        return sectionWidth, sectionHeight

    def _calculateLineSize(self, dc, line):
        return dc.GetTextExtent(line)

    def OnPaint(self, event):  # pylint: disable=W0613
        dc = wx.PaintDC(self)
        # dc.BeginDrawing()  # DID: BeginDrawing n'existe plus, il n'est plus nécesaire !
        # try:
        self._setFontBrushAndPen(dc)
        self._drawBorder(dc)
        self._drawSections(dc)
        # finally:
        #     dc.EndDrawing()

    def _setFontBrushAndPen(self, dc):
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        textColour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOTEXT)
        backgroundColour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK)
        dc.SetFont(font)
        dc.SetTextForeground(textColour)
        dc.SetBrush(wx.Brush(backgroundColour))
        dc.SetPen(wx.Pen(textColour))

    def _drawBorder(self, dc):
        # width, height = self.GetClientSizeTuple()
        width, height = self.GetClientSize()
        dc.DrawRectangle(0, 0, width, height)

    def _drawSections(self, dc):
        y = 3
        for sectionIndex in range(len(self.data)):
            y = self._drawSection(dc, y, sectionIndex)

    def _drawSection(self, dc, y, sectionIndex):
        icon, lines = self.data[sectionIndex]
        if not lines:
            return y
        x = 3
        if sectionIndex != 0:
            y = self._drawSectionSeparator(dc, x, y)
        if icon:
            x = self._drawIcon(dc, icon, x, y)
        topOfSection = y
        bottomOfSection = self._drawTextLines(dc, lines, x, y)
        if icon:
            self._drawIconSeparator(dc, x - 2, topOfSection, bottomOfSection)
        return bottomOfSection

    def _drawSectionSeparator(self, dc, x, y):
        y += 1
        # width = self.GetClientSizeTuple()[0]
        width = self.GetClientSize()[0]
        dc.DrawLine(x, y, width - x, y)
        return y + 2

    def _drawIcon(self, dc, icon, x, y):
        bitmap = wx.ArtProvider.GetBitmap(icon, wx.ART_FRAME_ICON, (16, 16))
        dc.DrawBitmap(bitmap, x, y, True)
        return 23  # New x

    def _drawTextLines(self, dc, textLines, x, y):
        for textLine in textLines:
            y = self._drawTextLine(dc, textLine, x, y)
        return y

    def _drawTextLine(self, dc, textLine, x, y):
        try:
            dc.DrawText(textLine, x, y)
        except Exception as e:
            raise RuntimeError("Could not draw text %s" % repr(textLine)) from e
        textHeight = dc.GetTextExtent(textLine)[1]
        return y + textHeight + 1

    def _drawIconSeparator(self, dc, x, top, bottom):
        """Dessine une ligne verticale entre l'icône et le texte.

        Args :
            dc (wx.DC) : Contexte de dessin.
            x (int) : Position X de la ligne.
            top (int) : Position supérieure de la ligne.
            bottom (int) : Position inférieure de la ligne.
        """
        dc.DrawLine(x, top, x, bottom)
