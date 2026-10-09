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

from taskcoachlib.widgets import balloontip
import wx
from taskcoachlib.gui import artprovider


class BalloonTipManager(balloontip.BalloonTipManager):
    def AddBalloonTip(
        self,
        target,
        message=None,
        title=None,
        bitmap=None,
        getRect=None,
        **kwargs
    ):
        # BallonTipManager.AddBalloonTip(self, target, message=None, title=None, bitmap=None, getRect=None, **kwargs):
        # Signature of method 'BalloonTipManager.AddBalloonTip()' does not match signature of the base
        # method in class 'BalloonTipManager'
        # (self, parent, target, message=None, title=None, bitmap=None, getRect=None):
        # Match base class signature but handle our specific parameters
        settings = kwargs.get("settings")
        name = kwargs.get("name")
        # if settings.getboolean("balloontips", name):
        if settings and name and settings.getboolean("balloontips", name):
            if bitmap is None:
                bitmap = artprovider.ArtProvider.CreateBitmap(
                    "lamp_icon", wx.ART_MENU, (16, 16)
                )

            # super().AddBalloonTip(target, message=message, title=title,
            #                      bitmap=wx.ArtProvider.getBitmap('lamp_icon', wx.ART_MENU, (16, 16)),
            #                      getRect=get_rect, name=name, settings=settings)
            # Unresolved attribute reference 'getBitmap' for class 'ArtProvider'
            # super().AddBalloonTip(settings=settings, name=name, target=target, message=message, title=title,
            #                       bitmap=wx.ArtProvider.GetBitmap("lamp_icon", wx.ART_MENU, (16, 16)),
            #                       getRect=getRect)
            super().AddBalloonTip(
                target=target,
                message=message,
                title=title,
                # bitmap=wx.ArtProvider.GetBitmap("lamp_icon", wx.ART_MENU, (16, 16)),
                bitmap=bitmap,
                getRect=getRect,
                # name=name,
                # settings=settings,
                **kwargs
            )

    def OnBalloonTipShow(self, name=None, settings=None):
        settings.setboolean("balloontips", name, False)
