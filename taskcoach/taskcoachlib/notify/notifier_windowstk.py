"""Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
# J'ai converti notifier_windows.py pour utiliser Tkinter à la place de wxPython et Snarl.
# Comme Snarl est un système de notification pour Windows,
# l'approche consistera à utiliser tkinter.messagebox
# ou des fenêtres personnalisées.
# Voici la version convertie :

# Explications de la conversion :
#
# Importation des modules : Importation de tkinter, messagebox, os, tempfile
#                           et PIL (Pillow).
# Classe TkinterWindowsNotifier :
#
# getName(): Retourne "Snarl" pour conserver la compatibilité
#            avec d'éventuelles configurations existantes.
#
# isAvailable(): Retourne toujours True car Tkinter est utilisé directement
#                et est considéré comme toujours disponible.
#                L'ancienne dépendance à Snarl est supprimée. TODO : a voir
#
# notify(): Crée un fichier temporaire pour sauvegarder le bitmap.
#
# Convertit wx.Bitmap en PIL Image et sauvegarde l'image au format PNG en utilisant Pillow
#       Utilise tkinter.messagebox.showinfo() pour afficher la notification avec le titre et le résumé.
#       Supprime le fichier temporaire après l'affichage.
#
#
# Enregistrement du notifier : AbstractNotifier.register(TkinterWindowsNotifier())
#                              enregistre le notifier.
#
# Points importants :
# Dépendance à Pillow :  N'oubliez pas d'installer Pillow (pip install Pillow).
# Compatibilité : Le nom du notifier reste "Snarl" pour éviter de casser
#                 d'éventuelles configurations existantes qui dépendent de ce nom.
# La conversion du bitmap est identique à celle que j'ai faite dans notifier_growl.py
#
# Prochaines étapes :
# Installez Pillow : pip install Pillow
# Testez le code :  TODO : Intégrez ce code dans votre projet et vérifiez si les notifications apparaissent correctement.
import tkinter
from tkinter import messagebox
import os
import tempfile
from PIL import Image  # Importation de Pillow pour la gestion des bitmaps
from .notifier import AbstractNotifier
# from taskcoachlib.thirdparty import snarl


class TkinterWindowsNotifier(AbstractNotifier):
    def getName(self):
        return "TkinterSnarl"  # Garder le même nom pour compatibilité

    def isAvailable(self):
        # try:
        #     return bool(snarl.snGetVersion())
        # except Exception:
        #     return False
        # Snarl n'est plus nécessaire, Tkinter est toujours disponible
        return True

    def notify(self, title, summary, bitmap, **kwargs):
        # Sauvegarde temporaire du bitmap et affichage via messagebox
        fd, filename = tempfile.mkstemp(".png")
        os.close(fd)
        # bitmap.SaveFile(filename, wx.BITMAP_TYPE_PNG)
        # try:
        #     # snarl.snShowMessage(
        #     #     title.encode("UTF-8"),
        #     #     summary.encode("UTF-8"),
        #     #     iconPath=filename,
        #     # )
        #     snarl.snShowMessage(
        #         title,
        #         summary,
        #         iconPath=filename,
        #     )
        try:
            # Convertir wx.Bitmap en PIL Image
            width, height = bitmap.GetWidth(), bitmap.GetHeight()
            buffer = bitmap.ConvertToImage().GetData()
            pil_image = Image.frombuffer("RGB", (width, height), buffer, "raw", "RGB", 0, 1)
            pil_image.save(filename, "PNG")

            tkinter.Tk().withdraw()  # Masque la fenêtre principale Tkinter
            messagebox.showinfo(title, summary)

        finally:
            os.remove(filename)


AbstractNotifier.register(TkinterWindowsNotifier())
