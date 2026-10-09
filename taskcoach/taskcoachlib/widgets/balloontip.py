"""
Task Coach - Your friendly task manager
Copyright (C) 2012 Task Coach developers <developers@taskcoach.org>

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

# Not using agw.balloontip because it doesn't position properly and
# lacks events

# from __future__ import division
# from builtins import object
# from past.utils import old_div
import logging
import wx
from wx.lib.embeddedimage import PyEmbeddedImage

log = logging.getLogger(__name__)


class BalloonTip(wx.Frame):
    """
    Fenêtre flottante affichant une info-bulle personnalisée (balloon tip)
    avec flèche directionnelle, message, titre, et éventuellement une icône.
    Utilisée pour mettre en avant une information liée à un widget cible,
    avec gestion fine de la disposition et de la forme.
    """

    ARROWSIZE = 16
    MAXWIDTH = 300

    def __init__(
        self,
        parent,
        target,
        message=None,
        title=None,
        bitmap=None,
        getRect=None,
    ):
        """Baloon tip.

        Initialise une nouvelle info-bulle (BalloonTip).

        :param parent: Fenêtre parente (wx.Window).
        :param target: Widget cible auquel la bulle est associée.
        :param message: (optionnel) Message de l'info-bulle.
        :param title: (optionnel) Titre affiché en haut de la bulle.
        :param bitmap: (optionnel) wx.Bitmap à afficher dans la bulle.
        :param getRect: (optionnel) Fonction pour obtenir la position/zone du widget cible.
        """

        super().__init__(
            parent,
            style=wx.NO_BORDER
            | wx.FRAME_FLOAT_ON_PARENT
            | wx.FRAME_NO_TASKBAR
            | wx.FRAME_SHAPED
            | wx.POPUP_WINDOW,
        )

        wheat = wx.ColourDatabase().Find("WHEAT")
        self.SetBackgroundColour(wheat)

        self._target = target
        self._getRect = getRect
        self._interior = wx.Panel(self)
        self._interior.Bind(wx.EVT_LEFT_DOWN, self.DoClose)
        self._interior.SetBackgroundColour(wheat)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        if bitmap is not None:
            hsizer.Add(
                wx.StaticBitmap(self._interior, wx.ID_ANY, bitmap),
                0,
                wx.ALIGN_CENTRE | wx.ALL,
                3,
            )
        if title is not None:
            titleCtrl = wx.StaticText(self._interior, wx.ID_ANY, title)
            hsizer.Add(titleCtrl, 1, wx.ALL | wx.ALIGN_CENTRE, 3)
            titleCtrl.Bind(wx.EVT_LEFT_DOWN, self.DoClose)
        vsizer.Add(hsizer, 0, wx.EXPAND)
        if message is not None:
            msg = wx.StaticText(self._interior, wx.ID_ANY, message)
            msg.Wrap(self.MAXWIDTH)
            vsizer.Add(msg, 1, wx.EXPAND | wx.ALL, 3)
            msg.Bind(wx.EVT_LEFT_DOWN, self.DoClose)

        self._interior.SetSizer(vsizer)
        self._interior.Fit()

        # class Sizer(wx.PySizer):
        class Sizer(wx.Sizer):
            """
            Sizer personnalisé pour disposer le contenu de l'info-bulle (BalloonTip)
            en tenant compte de la flèche directionnelle et du décalage associé.
            """

            # Tout sizer custom doit impérativement positionner
            # ET dimensionner ses enfants dans RecalcSizes.
            # Sans cela, wxWidgets/wxPython plante ou affiche des warnings/erreurs.
            # Ajoute un appel à SetSize dans RecalcSizes pour chaque enfant géré.

            def __init__(self, interior, direction, offset):
                """
                Initialise le sizer personnalisé.

                :param interior: Panel intérieur contenant le contenu de la bulle.
                :param direction: Direction de la flèche ("bottom", etc.).
                :param offset: Décalage vertical dû à la flèche.
                """
                self._interior = interior
                self._direction = direction
                self._offset = offset
                super().__init__()

            def SetDirection(self, direction):
                """
                Modifie la direction de la flèche de l'info-bulle.

                :param direction: Nouvelle direction ("bottom", etc.).
                """
                self._direction = direction

            def CalcMin(self):
                """
                Calcule la taille minimale nécessaire pour le contenu et la flèche.

                :return: wx.Size correspondant à la taille minimale.
                """
                w, h = self._interior.GetClientSize()
                return wx.Size(w, h + self._offset)

            def RecalcSizes(self):
                """
                Dispose et dimensionne le panel intérieur de la bulle en fonction de la direction
                et du décalage de la flèche. Doit être implémentée pour tout sizer custom wxPython.
                """
                # if self._direction == "bottom":
                #     self._interior.SetPosition((0, 0))
                # else:
                #     self._interior.SetPosition((0, self._offset))
                # GetContainingWindow() donne le widget parent dont tu dois occuper tout l’espace.
                parent_size = self.GetContainingWindow().GetClientSize()
                # Tu positionnes l’intérieur et tu le redimensionnes.
                # dans wxPython, un sizer custom DOIT
                # positionner et dimensionner ses enfants dans RecalcSizes.
                if self._direction == "bottom":
                    self._interior.SetPosition((0, 0))
                    self._interior.SetSize(parent_size)
                else:
                    self._interior.SetPosition((0, self._offset))
                    self._interior.SetSize(
                        (parent_size[0], parent_size[1] - self._offset)
                    )

        self._sizer = Sizer(self._interior, "bottom", self.ARROWSIZE)
        self.SetSizer(self._sizer)
        self.Position()
        self.Show()

        wx.GetTopLevelParent(target).Bind(wx.EVT_SIZE, self._OnDim)
        wx.GetTopLevelParent(target).Bind(wx.EVT_MOVE, self._OnDim)

    def _Unbind(self):
        """
        Détache les gestionnaires d'événements de redimensionnement et de déplacement
        (EVT_SIZE, EVT_MOVE) du parent top-level du widget cible associé à la bulle.
        Cela évite que la bulle se repositionne ou reste affichée après fermeture.
        """
        # Attention, si d’autres gestionnaires EVT_SIZE/EVT_MOVE
        # sont ajoutés ailleurs sur ce parent, ils seront tous retirés.
        # Si tu veux être plus précis,
        # conserve le handler ID lors du Bind pour ne retirer que celui de la bulle.
        wx.GetTopLevelParent(self._target).Unbind(wx.EVT_SIZE)
        wx.GetTopLevelParent(self._target).Unbind(wx.EVT_MOVE)

    def _OnDim(self, event):
        """
        Gestionnaire d'événement appelé lors du déplacement ou du redimensionnement du parent cible.
        Redemande le positionnement de la bulle après l'événement.

        :param event: Événement wxPython à propager.
        """
        # Utilisation correcte de CallAfter(Position)
        # pour éviter les glitchs de repaint dans wxPython.
        # wx.CallAfter(self.Position)
        wx.CallAfter(self.__safePosition)
        event.Skip()

    def __safePosition(self):
        """Safely call Position, guarding against deleted C++ objects."""
        try:
            if self:
                self.Position()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def DoClose(self, event=None, unbind=True):
        """
        Ferme la bulle et détache les gestionnaires d'événements si demandé.

        :param event: Événement wxPython (clic souris, etc.).
        :param unbind: (bool) Si vrai, détache les gestionnaires d'événements liés à la bulle.
        """
        # Tu pourrais accepter event=None par sécurité si tu veux pouvoir appeler DoClose sans événement.
        if unbind:
            self._Unbind()
        self.Close()

    def Position(self):
        """
        Calcule et définit la position, la forme (shape) et la taille de la bulle par rapport à son widget cible.
        Gère la direction de la flèche (haut/bas) selon la place disponible à l'écran.
        Applique également un masque de forme pour donner l'effet 'balloon' avec flèche.
        """
        # Idée d’amélioration :
        #
        #     Si la bulle risque d’être en dehors de l’écran sur les petits écrans, tu pourrais ajouter une vérification supplémentaire pour ajuster x et y.
        #     Si la cible est détruite (_target), tu pourrais vérifier et ne pas tenter de repositionner.
        #
        # Modernise les divisions :
        #
        #     Tu utilises parfois / et parfois //. Privilégie // pour un résultat entier.
        #
        # Utilise bien wx.Bitmap (et non wx.EmptyBitmap) pour compatibilité Phoenix.
        # w, h = self._interior.GetClientSizeTuple()
        # https://docs.wxpython.org/wx.Window.html?highlight=getclientsize#wx.Window.GetClientSize
        w, h = self._interior.GetClientSize()
        h += self.ARROWSIZE
        if self._getRect is None:
            # tw, th = self._target.GetSizeTuple()
            tw, th = self._target.GetSize()
            tx, ty = 0, 0
        else:
            tx, ty, tw, th = self._getRect()
        if self.Shown:
            tx, ty = self._target.ClientToScreen(wx.Point(tx, ty))
        dpyIndex = max(0, wx.Display.GetFromPoint(wx.Point(tx, ty)) or 0)
        rect = wx.Display(dpyIndex).GetClientArea()

        # x = max(rect.GetLeft(), min(rect.GetRight() - w, int(tx + tw / 2 - w / 2)))
        # x = max(rect.GetLeft(), min(rect.GetRight() - w, int(tx + old_div(tw, 2) - old_div(w, 2))))
        x = max(
            rect.GetLeft(),
            min(rect.GetRight() - w, int(tx + tw // 2 - w // 2)),
        )
        y = ty - h
        direction = "bottom"
        if y < rect.GetTop():
            y = ty + th
            direction = "top"

        # mask = wx.EmptyBitmap(w, h)
        mask = wx.Bitmap(
            w, h
        )  # Pas wx.EmptyBitmap pour la compatibilité Phoenix.
        memDC = wx.MemoryDC()
        memDC.SelectObject(mask)
        try:
            memDC.SetBrush(wx.BLACK_BRUSH)
            memDC.SetPen(wx.BLACK_PEN)
            memDC.DrawRectangle(0, 0, w, h)

            memDC.SetBrush(wx.WHITE_BRUSH)
            memDC.SetPen(wx.WHITE_PEN)
            if direction == "bottom":
                memDC.DrawPolygon(
                    [
                        (0, 0),
                        (w, 0),
                        (w, h - self.ARROWSIZE),
                        (
                            tx + int(tw // 2) - x + int(self.ARROWSIZE // 2),
                            h - self.ARROWSIZE,
                        ),
                        (tx + int(tw // 2) - x, h),
                        (
                            tx + int(tw // 2) - x - int(self.ARROWSIZE // 2),
                            h - self.ARROWSIZE,
                        ),
                        (0, h - self.ARROWSIZE),
                    ]
                )
            else:
                memDC.DrawPolygon(
                    [
                        (0, self.ARROWSIZE),
                        (
                            tx + int(tw // 2) - x - int(self.ARROWSIZE // 2),
                            self.ARROWSIZE,
                        ),
                        (tx + int(tw // 2) - x, 0),
                        (
                            tx + int(tw // 2) - x + int(self.ARROWSIZE // 2),
                            self.ARROWSIZE,
                        ),
                        (w, self.ARROWSIZE),
                        (w, h),
                        (0, h),
                    ]
                )
            self._sizer.SetDirection(direction)
        finally:
            memDC.SelectObject(wx.NullBitmap)
        # self.SetDimensions(x, y, w, h)
        self.SetSize(int(x), int(y), int(w), int(h))
        # self.SetShape(wx.RegionFromBitmapColour(mask, wx.Colour(0, 0, 0)))
        # https://docs.wxpython.org/wx.Region.html#wx-region
        # https://pythonhosted.org/wxPython/classic_vs_phoenix.html
        self.SetShape(wx.Region(mask, wx.Colour(0, 0, 0)))
        self.Layout()


class BalloonTipManager(object):
    """
    Utilisez-le comme un mixin dans la fenêtre de niveau supérieur
    qui héberge les cibles de la bulle d'aide, pour
    éviter qu'ils n'apparaissent en une seule fois.
    """

    def __init__(self, *args, **kwargs):
        self.__tips = list()
        self.__displaying = None
        self.__kwargs = dict()
        self.__shutdown = False
        super().__init__(*args, **kwargs)

        # self.Bind(wx.EVT_CLOSE, self.__OnClose)
        # Unresolved attribute reference 'Bind' for class 'BalloonTipManager'
        # https://docs.wxpython.org/wx.PyEventBinder.html?highlight=bind#wx.PyEventBinder.Bind
        # Bind() = wx.PyEventBinder.Bind()
        # ou https://docs.wxpython.org/wx.EvtHandler.html?highlight=bind#wx.EvtHandler.Bind
        # Bind = wx.EvtHandler.Bind()
        self.Bind(wx.EVT_CLOSE, self.__OnClose)

    def AddBalloonTip(
        self,
        target,
        message=None,
        title=None,
        bitmap=None,
        getRect=None,
        **kwargs
    ):
        """Schedules a tip. Extra keyword arguments will be passed to L{OnBalloonTipShow} and L{OnBalloonTipClosed}."""
        for eTarget, eMessage, eTitle, eBitmap, eGetRect, eArgs in self.__tips:
            if (eTitle, eMessage) == (title, message):
                return
        self.__tips.append((target, message, title, bitmap, getRect, kwargs))
        self.__Try()

    def __Try(self):
        if self.__tips and not self.__shutdown and self.__displaying is None:
            target, message, title, bitmap, getRect, kwargs = self.__tips.pop(
                0
            )
            tip = BalloonTip(
                self,
                target,
                message=message,
                title=title,
                bitmap=bitmap,
                getRect=getRect,
            )
            self.__displaying = tip
            self.OnBalloonTipShow(**kwargs)
            self.__kwargs = kwargs
            tip.Bind(wx.EVT_CLOSE, self.__OnCloseTip)

    def __OnClose(self, event):
        self.__shutdown = True
        event.Skip()

    def __OnCloseTip(self, event):
        event.Skip()
        self.__displaying = None
        self.OnBalloonTipClosed(**self.__kwargs)
        self.__Try()

    def OnBalloonTipShow(self, **kwargs):
        pass

    def OnBalloonTipClosed(self, **kwargs):
        pass


if __name__ == "__main__":

    class Frame(wx.Frame):
        def __init__(self):
            log.debug(
                "BallonTipManager-Frame : Création du Frame principal BallonTip."
            )

            super().__init__(None, wx.ID_ANY, "Test")
            # wx.Frame.__init__(self,None, wx.ID_ANY, "Test")

            # Le sizer va servir à positionner les éléments et dimensionner la fenêtre.
            s = wx.BoxSizer()
            self.btn = wx.Button(self, wx.ID_ANY, "Show balloon")
            # wx.EVT_BUTTON(self.btn, wx.ID_ANY, self.OnClick)
            self.btn.Bind(wx.EVT_BUTTON, self.OnClick)  # TODO : A Essayer !
            # self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)  # TODO : ou ceci !
            s.Add(self.btn, 1, wx.EXPAND)
            # L'appel SetSizer () indique à votre fenêtre (ou cadre) quel créateur utiliser.
            self.SetSizer(s)
            # self.Fit()
            s.Fit(self)  # TODO : Essayer plutôt ceci !

        def OnClick(self, event):
            BalloonTip(
                self,
                self.btn,
                """Your bones don't break, mine do. That's clear. Your cells react to bacteria 
                       and viruses differently than mine. You don't get sick, I do. That's also clear. But for some 
                       reason, you and I react the exact same way to water. We swallow it too fast, we choke. We get 
                       some in our lungs, we drown. However unreal it may seem, we are connected, you and I. We're on 
                       the same curve, just on opposite ends.""",
                title="Title",
                # bitmap=wx.ArtProvider.getBitmap(wx.ART_TIP, wx.ART_MENU, (16, 16)))
                bitmap=wx.ArtProvider.GetBitmap(
                    wx.ART_TIP, wx.ART_MENU, (16, 16)
                ),
            )

    class App(wx.App):
        def OnInit(self):
            Frame().Show()
            return True

    App(0).MainLoop()
