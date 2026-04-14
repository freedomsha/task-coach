"""
Initialisation précoce de wx pour éviter les crashs en tests.
"""

import wx  # Import wx

# Créer wx.App AVANT tout autre import wx
if not wx.GetApp():
    wx.App(False)
