# Utility module to provide a small UI backend shim for code that expects a `wx`
# namespace. This module exports a single name `wx` which is either the real wx
# module (when available and selected) or a lightweight fallback that uses
# tkinter when possible and otherwise a pure-Python dummy implementation.
#
# The idea is to centralize the "work with or without wx" logic so other modules
# (like persistence/xml/reader.py) can simply `from taskcoachlib.ui.backend import wx`.
#
# This file is a new helper and should be usable by modules that need only a few
# wx abstractions (SystemSettings.GetFont, Font(), some logging helpers and a
# SYS_DEFAULT_GUI_FONT constant).
#
# It intentionally avoids creating a permanent tkinter root window; it will try
# to use tkinter.font.Font where possible but falls back to a small DummyFont
# class which simply parses a point size from the textual description.

from typing import Any
import logging
import re

# get selection ("wx" or "tk") if available
try:
    from taskcoachlib.config.arguments import (
        get_gui,
    )  # may raise during early import
except Exception:

    def get_gui() -> Any:  # fallback if config not importable yet
        return None


_WX_AVAILABLE = False
_wx = None

# Try to import real wx only when the configured GUI isn't explicitly "tk"
if get_gui() != "tk":
    try:
        import wx as _wx  # type: ignore

        _WX_AVAILABLE = True
    except Exception:
        _WX_AVAILABLE = False
        _wx = None

if _WX_AVAILABLE and get_gui() == "wx":
    # Use real wx if available and explicitly selected (or not forced to tk)
    wx = _wx
else:
    # Provide a fallback namespace that implements the small subset used in the
    # repository. Prefer tkinter.font when available (for a closer mapping), but
    # don't require it.
    try:
        import tkinter as _tk
        import tkinter.font as _tkfont

        _TK_AVAILABLE = True
    except Exception:
        _TK_AVAILABLE = False
        _tk = None
        _tkfont = None

    class _ProxyFont:
        """Proxy that provides IsOk(), GetPointSize(), SetPointSize() as wx.Font."""

        def __init__(self, source=None, default_size: int = 10):
            self._default_size = default_size
            self._size = default_size
            # If source is a tkinter.font.Font instance, read its size.
            if _TK_AVAILABLE and isinstance(source, _tkfont.Font):
                try:
                    s = source.cget("size")
                    # tkinter uses positive/negative sizes depending on units;
                    # normalize to positive integer
                    self._size = abs(int(s))
                except Exception:
                    self._size = default_size
            else:
                # try to extract integer from the textual description
                if source:
                    m = re.search(r"(\d+)", str(source))
                    if m:
                        try:
                            self._size = int(m.group(1))
                        except Exception:
                            self._size = default_size

        def IsOk(self) -> bool:
            return True

        def GetPointSize(self) -> int:
            return self._size

        def SetPointSize(self, s: int) -> None:
            try:
                self._size = int(s)
            except Exception:
                pass

    class _SystemSettings:
        @staticmethod
        def GetFont(arg):
            # Try to return a proxy based on tkinter.font if present, otherwise a
            # simple proxy with a reasonable default.
            if _TK_AVAILABLE:
                try:
                    # Create a tk Font to parse the description (won't show a window)
                    f = _tkfont.Font()
                    return _ProxyFont(f)
                except Exception:
                    return _ProxyFont(default_size=10)
            return _ProxyFont(default_size=10)

    def _FontFactory(text: Any = None) -> _ProxyFont:
        # Try to create a tkinter Font from text if possible for better fidelity
        if _TK_AVAILABLE:
            try:
                # Using `Font` with actual attributes requires structured input;
                # as we don't know the exact format, create a default and try to
                # set a size if present in `text`.
                tkf = _tkfont.Font()
                m = re.search(r"(\d+)", str(text)) if text else None
                if m:
                    tkf.configure(size=int(m.group(1)))
                return _ProxyFont(tkf)
            except Exception:
                return _ProxyFont(text, default_size=10)
        return _ProxyFont(text, default_size=10)

    class _WxFallbackNamespace:
        # Constant used in code
        SYS_DEFAULT_GUI_FONT = "SYS_DEFAULT_GUI_FONT"
        SystemSettings = _SystemSettings
        Font = staticmethod(_FontFactory)

        # Logging helpers used in some modules: map to python logging
        @staticmethod
        def LogError(msg: str) -> None:
            logging.getLogger(__name__).error(msg)

        @staticmethod
        def LogWarning(msg: str) -> None:
            logging.getLogger(__name__).warning(msg)

        @staticmethod
        def LogDebug(msg: str) -> None:
            logging.getLogger(__name__).debug(msg)

        @staticmethod
        def LogInfo(msg: str) -> None:
            logging.getLogger(__name__).info(msg)

    wx = _WxFallbackNamespace()
