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
"""

import wx

# FIXME: taskcoachlib/gui/splash.py:
# FIXME: Adding duplicate image handler for 'Windows bitmap file'
# FIXME: Adding duplicate animation handler for '1' type
# FIXME: Adding duplicate animation handler for '2' type
import wx.adv
from taskcoachlib import i18n
from wx.lib.embeddedimage import PyEmbeddedImage

# Try to import icons. If it fails, print an error message and exit.
try:
    from . import icons
except ImportError:  # pragma: no cover
    print("ERROR: couldn't import icons.py.")
    print("You need to generate the icons file.")
    print('Run "make prepare" in the Task Coach root folder.')
    import sys

    sys.exit(1)


class SplashScreen(wx.adv.SplashScreen):
    """
    A splash screen for Task Coach that displays an image on startup.

    This class creates a splash screen that shows a bitmap image for a
    specified duration when the application starts.
    """

    def __init__(self):
        """
        Initialize the SplashScreen instance.
        """
        # Get the splash image from the icons catalog.
        splash = icons.catalog["splash"]  # type: PyEmbeddedImage

        # Check if the current language is right-to-left.
        if i18n.currentLanguageIsRightToLeft():
            # Mirror the bitmap for RTL languages.
            # RTL languages cause the bitmap to be mirrored too, but because
            # the splash image is not internationalized, we have to mirror it
            # (back). Unfortunately using SetLayoutDirection() on the
            # SplashWindow doesn't work.
            # bitmap = wx.BitmapFromImage(splash.GetBitmap().Mirror())
            bitmap = wx.Bitmap(splash.GetBitmap().Mirror())
        else:
            # Use the bitmap as is for LTR languages.
            bitmap = splash.GetBitmap()

        # Initialize the wx.adv.SplashScreen with the bitmap.
        super().__init__(
            bitmap,
            wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
            4000,  # Display the splash screen for 4000 milliseconds (4 seconds).
            None,
            -1,
        )
