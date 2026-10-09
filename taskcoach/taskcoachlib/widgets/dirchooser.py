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
from taskcoachlib.i18n import _


class DirectoryChooser(wx.Panel):
    """
    Panneau personnalisé contenant un contrôle de sélection de répertoire (DirPickerCtrl)
    et une case à cocher pour sélectionner "Aucun".
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise le panneau DirectoryChooser avec un DirPickerCtrl et une CheckBox.

        :param args: Arguments positionnels transmis à wx.Panel.
        :param kwargs: Arguments nommés transmis à wx.Panel.
        """
        super().__init__(*args, **kwargs)  # Appelle le constructeur de wx.Panel

        self.chooser = wx.DirPickerCtrl(self, wx.ID_ANY, "")  # Crée un contrôle de choix de dossier
        self.checkbx = wx.CheckBox(self, wx.ID_ANY, _("None"))  # Crée une case à cocher "None"

        sz = wx.BoxSizer(wx.VERTICAL)  # Crée un sizer vertical
        sz.Add(self.chooser, 1, wx.EXPAND)  # Ajoute le DirPickerCtrl avec expansion
        sz.Add(self.checkbx, 1)  # Ajoute la CheckBox sans option d'expansion

        self.SetSizer(sz)  # Applique le sizer au panneau
        self.Fit()  # Ajuste la taille du panneau à son contenu

        # Lie l'événement de clic sur la case à cocher à la méthode OnCheck
        # wx.EVT_CHECKBOX(self.checkbx, wx.ID_ANY, self.OnCheck)
        # self.checkbx.Bind(wx.EVT_CHECKBOX, wx.ID_ANY, self.OnCheck)  # Provoque une assertion
        self.checkbx.Bind(wx.EVT_CHECKBOX, self.OnCheck)

    def SetPath(self, pth):
        """
        Coche la case “None” si aucun chemin n’est fourni.

        Sinon, elle configure le chemin et active le contrôle.

        Args :
            pth : Chemin

        Returns:

        """
        if pth:
            self.checkbx.SetValue(False)
            self.chooser.Enable(True)
            self.chooser.SetPath(pth)
        else:
            self.checkbx.SetValue(True)
            self.chooser.SetPath("")
            self.chooser.Enable(False)

    def GetPath(self):
        """
        Retourne le chemin si la case n’est pas cochée,

        Sinon, retourne "".

        Returns :
            Le chemin si la case n’est pas cochée, sinon ""

        """
        if not self.checkbx.GetValue():
            return self.chooser.GetPath()
        return ""

    def OnCheck(self, evt):
        """
        Méthode appelée lors du clic sur la case à cocher.

        Elle fait deux choses :

            Active ou désactive self.chooser selon l’état de la case.

            Fait un SetPath("/") pour contourner un bug wx
            (souvent nécessaire car sinon DirPickerCtrl reste vide
            après un .Disable()/.Enable()).

        Args :
            event : L'événement EVT_CHECKBOX généré.
        """
        # self.chooser.Enable(not evt.IsChecked())   # Active le choix
        # self.chooser.SetPath("/")  # Workaround for a wx bug
        if not evt.IsChecked():
            self.chooser.Enable(True)  # Active le choix de dossier
            self.chooser.SetPath("/")  # Contourne le bug wx
        else:
            self.chooser.Enable(False)  # Désactive le choix de dossier
