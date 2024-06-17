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

import wx, sys, platform

# This module is meant to be imported like this:
#   from taskcoachlib import operating_system
# so that the function calls read:
#   operating_system.isWindows(), operating_system.isMac(), etc.


def isMac():
    """
    Check if the current platform is macOS.

    Returns:
        bool: True if the current platform is macOS, False otherwise.
    """
    return isPlatform("MAC")


def isWindows():
    """
    Check if the current platform is Windows.

    Returns:
        bool: True if the current platform is Windows, False otherwise.
    """
    return isPlatform("MSW")


def isGTK():
    """
    Check if the current platform is GTK.

    Returns:
        bool: True if the current platform is GTK, False otherwise.
    """
    return isPlatform("GTK")


def isPlatform(threeLetterPlatformAbbreviation, wxPlatform=wx.Platform):
    """
    Check if the current platform matches the given three-letter abbreviation.

    Args:
        threeLetterPlatformAbbreviation (str): The three-letter platform abbreviation (e.g., "MAC", "MSW", "GTK").
        wxPlatform (str, optional): The wxPython platform string. Defaults to wx.Platform.

    Returns:
        bool: True if the current platform matches the given abbreviation, False otherwise.
    """
    return "__WX%s__" % threeLetterPlatformAbbreviation == wxPlatform


def isWindows7_OrNewer():  # pragma: no cover
    """
    Check if the current platform is Windows 7 or newer.

    Returns:
        bool: True if the current platform is Windows 7 or newer, False otherwise.
    """
    if isWindows():
        major, minor = sys.getwindowsversion()[:2]  # pylint: disable=E1101
        return (major, minor) >= (6, 1)
    else:
        return False


def _platformVersion():
    """
    Get the platform version as a tuple of integers.

    Returns:
        tuple: The platform version.
    """
    return tuple(map(int, platform.release().split(".")))


def isMacOsXLion_OrNewer():  # pragma: no cover
    """
    Check if the current platform is macOS Lion (10.7) or newer.

    Returns:
        bool: True if the current platform is macOS Lion or newer, False otherwise.
    """
    if isMac():
        return _platformVersion() >= (11, 1)
    else:
        return False


def isMacOsXTiger_OrOlder():  # pragma no cover
    """
    Check if the current platform is macOS Tiger (10.4) or older.

    Returns:
        bool: True if the current platform is macOS Tiger or older, False otherwise.
    """
    if isMac():
        return _platformVersion() <= (
            8,
            11,
            1,
        )  # Darwin release number for Tiger
    else:
        return False


def isMacOsXMountainLion_OrNewer():  # pragma no cover
    """
    Check if the current platform is macOS Mountain Lion (10.8) or newer.

    Returns:
        bool: True if the current platform is macOS Mountain Lion or newer, False otherwise.
    """
    if isMac():
        return _platformVersion() >= (12,)
    else:
        return False


def isMacOsXMavericks_OrNewer():  # pragma no cover
    """
    Check if the current platform is macOS Mavericks (10.9) or newer.

    Returns:
        bool: True if the current platform is macOS Mavericks or newer, False otherwise.
    """
    if isMac():
        return _platformVersion() >= (13,)
    else:
        return False


def defaultEncodingName():
    """
    Get the default system encoding name.

    Returns:
        str: The default system encoding name.
    """
    return wx.Locale.GetSystemEncodingName() or "utf-8"


def decodeSystemString(s):
    """
    Decode a system string using the default system encoding.

    Args:
        s (str or bytes): The string to decode.

    Returns:
        str: The decoded string.
    """
    if isinstance(s, str):
        return s
    encoding = defaultEncodingName()
    # Python does not define the windows_XXX aliases for every code page...
    if encoding.startswith("windows-"):
        encoding = "cp" + encoding[8:]
    if not encoding:
        encoding = "utf-8"
    return s.decode(encoding, "ignore")
