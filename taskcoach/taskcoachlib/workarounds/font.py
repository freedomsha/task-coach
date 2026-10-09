"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

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

# wxFontFromNativeInfoString = wx.FontFromNativeInfoString  # obsolète
# wxFontFromNativeInfoString = wx.Font


def FontFromNativeInfoString(nativeInfoString):
    """ wx.font_from_native_info_string may throw an wx.PyAssertionError when the
        PointSize is zero. This may happen when fonts are set on one platform
        and then used on another platform. Catch the exception and return None
        instead. """
    if nativeInfoString:
        try:
            # return wxFontFromNativeInfoString(native_info_string)
            # Old wx.FontFromNativeInfoString not exists in wxPython4, use
            # nfi.FromString instead
            nfi = wx.NativeFontInfo()
            if nfi.FromString(nativeInfoString):
                return wx.Font(nfi)
            return None
        # except wx.PyAssertionError:  # cannot find reference
        except wx.wxAssertionError:
            pass
    return None


wx.FontFromNativeInfoString = FontFromNativeInfoString
