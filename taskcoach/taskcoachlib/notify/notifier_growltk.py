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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
#  Comme Growl est un système de notification pour macOS,
#  une conversion directe vers Tkinter impliquera l'utilisation de
#  solutions alternatives comme messagebox ou des fenêtres personnalisées,
#  car Tkinter ne possède pas d'intégration native avec Growl.
#  Voici une version convertie de notifier_growl.py utilisant tkinter.messagebox :

# Explications de la conversion :
#
# Importation des modules : Importation de tkinter, messagebox, os et tempfile.
#                           On importe également AbstractNotifier [[3, 4]] et meta 1.
# Classe TkinterGrowlNotifier :
#
# getName(): Retourne "Growl" comme nom du notifier.
# isAvailable(): Retourne toujours True car Tkinter est considéré comme toujours disponible.
# notify():
#
# Crée un fichier temporaire pour sauvegarder le bitmap (comme dans l'implémentation originale) 1.
# Utilise tkinter.messagebox.showinfo() pour afficher la notification avec le titre et le résumé fournis.
# Supprime le fichier temporaire après l'affichage.
#
#
#
#
# Enregistrement du notifier : AbstractNotifier.register(TkinterGrowlNotifier())
#                              enregistre le notifier pour qu'il puisse être
#                              utilisé par TaskCoach [[4, 7]].
#
# Points importants :
#
# Dépendance à wxPython : Notez que la ligne bitmap.SaveFile(filename, wx.BITMAP_TYPE_PNG) 1
#                         nécessite toujours wxPython pour la manipulation du bitmap.
#                         Si vous souhaitez éliminer complètement la dépendance à wxPython,
#                         vous devrez trouver une autre bibliothèque de traitement d'image
#                         (par exemple, Pillow) pour sauvegarder le bitmap au format PNG.
#                         Il est préférable d'éliminer complètement la dépendance à wxPython.
#                         Je vais modifier le code de notifier_growl.py pour utiliser Pillow (PIL)
#                         à la place de wxPython pour sauvegarder le bitmap au format PNG.
# Fichier temporaire : La création d'un fichier temporaire est conservée de la version originale pour potentiellement permettre une utilisation future de l'icône dans la notification (bien que messagebox ne le supporte pas directement).  Si vous n'avez pas besoin de cette fonctionnalité, vous pouvez supprimer cette partie du code.
# Absence de fonctionnalités Growl spécifiques : Cette version ne réplique pas les fonctionnalités avancées de Growl, comme les notifications persistantes ou les actions personnalisées.  Elle utilise simplement une boîte de message Tkinter pour afficher le titre et le contenu.
#
# Prochaines étapes :
#
# Testez le code : Intégrez ce code dans votre projet et
#                  vérifiez si les notifications apparaissent correctement.
# Considérez d'autres options de notification : Explorez d'autres bibliothèques Tkinter
#                                               ou des approches plus sophistiquées
#                                               pour créer des notifications visuellement
#                                               plus attrayantes si messagebox ne suffit pas.

# Modifications apportées :
#
# Importation de Pillow : from PIL import Image importe la bibliothèque Pillow.
#                         Pillow est constructed on top of Python Image Library (PIL) 1.
#                         The image formats it supports are JPEG, PNG, PPM, GIF 1.
#                         PNG is a practical kind of format 2.
#                         It is also possible using ready-made programming tools
#                         such as Python library called Pillow 3.
# Conversion du bitmap : La partie la plus importante est la conversion du wx.Bitmap en PIL Image.
# Voici comment cela fonctionne :
#
# width, height = bitmap.GetWidth(), bitmap.GetHeight() : Obtient la largeur et la hauteur du wx.Bitmap.
# buffer = bitmap.ConvertToImage().GetData() : Récupère les données brutes de l'image du wx.Bitmap.
# pil_image = Image.frombuffer("RGB", (width, height), buffer, "raw", "RGB", 0, 1) :
#               Crée une PIL Image à partir des données brutes.
#               Les arguments spécifient le format des données ("RGB"),
#               la taille, les données elles-mêmes, et d'autres paramètres
#               nécessaires pour interpréter correctement les données.
# pil_image.save(filename, "PNG") : Sauvegarde l'image au format PNG en utilisant Pillow 4.
#                                   PNG format allows you to save color images
#                                   with a depth of up to 48 bits per pixel 5.
#
# Points importants :
#
# Dépendance à Pillow : Vous devez installer Pillow (pip install Pillow)
#                       pour que ce code fonctionne.
# Conversion du format de couleur :  TODO : Assurez-vous que le format de couleur "RGB"
#                                     correspond au format des données de votre wx.Bitmap.
#                                     Si ce n'est pas le cas, vous devrez peut-être
#                                     ajuster les paramètres de Image.frombuffer.
# Qualité de l'image : Vous pouvez ajuster les paramètres de pil_image.save()
#                      pour contrôler la qualité et la compression de l'image PNG.
#
# Prochaines étapes :
#
# Installez Pillow : pip install Pillow
# Testez le code : Intégrez ce code dans votre projet et
#                  vérifiez si les notifications apparaissent correctement et
#                  si les images sont sauvegardées correctement.
# Ajustez les paramètres : Si nécessaire, ajustez les paramètres de conversion
#                          et de sauvegarde pour obtenir la qualité d'image souhaitée.
import tkinter
from tkinter import messagebox
import os
import tempfile
from PIL import Image  # Importation de Pillow
from .notifier import AbstractNotifier
from taskcoachlib import meta  # [1](https://app.textcortex.com/file?id=file_01kan16xjjf0eswjzssvbx2ha8&state=eyJzbmlwcGV0IjoiZnJvbSUyMGdudHAlMjBpbXBvcnQlMjBub3RpZmllciUyMGFzJTIwZ3Jvd2wlMjBmcm9tJTIwdGFza2NvYWNobGliJTIwaW1wb3J0JTIwbWV0YSUyMGZyb20lMjAubm90aWZpZXIlMjBpbXBvcnQlMjBBYnN0cmFjdE5vdGlmaWVyJTIwJTIwJTIwY2xhc3MlMjBHcm93bE5vdGlmaWVyKEFic3RyYWN0Tm90aWZpZXIpJTNBJTIwJTIwJTIwJTIwJTIwZGVmJTIwX19pbml0X18oc2VsZiklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzdXBlcigpLl9faW5pdF9fKCklMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjB0cnklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjMlMjBweWxpbnQlM0ElMjBkaXNhYmxlJTNERTExMDElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9ub3RpZmllciUyMCUzRCUyMGdyb3dsLkdyb3dsTm90aWZpZXIoYXBwbGljYXRpb25OYW1lJTNEbWV0YS5uYW1lJTJDJTIwbm90aWZpY2F0aW9ucyUzRCU1QiUyMlJlbWluZGVyJTIyJTVEKSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHNlbGYuX25vdGlmaWVyLnJlZ2lzdGVyKCklMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBleGNlcHQlM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9hdmFpbGFibGUlMjAlM0QlMjBGYWxzZSUyMCUyMCUyMyUyMHB5bGludCUzQSUyMGRpc2FibGUlM0RXMDcwMiUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMGVsc2UlM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9hdmFpbGFibGUlMjAlM0QlMjBUcnVlJTIwJTIwJTIwJTIwJTIwJTIwZGVmJTIwZ2V0TmFtZShzZWxmKSUzQSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHJldHVybiUyMCUyMkdyb3dsJTIyJTIwJTIwJTIwJTIwJTIwJTIwZGVmJTIwaXNBdmFpbGFibGUoc2VsZiklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjByZXR1cm4lMjBzZWxmLl9hdmFpbGFibGUlMjAlMjAlMjAlMjAlMjAlMjBkZWYlMjBub3RpZnkoc2VsZiUyQyUyMHRpdGxlJTJDJTIwc3VtbWFyeSUyQyUyMGJpdG1hcCUyQyUyMCoqa3dhcmdzKSUzQSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMyUyME5vdCUyMHJlYWxseSUyMGVmZmljaWVudC4uLiUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMGZkJTJDJTIwZmlsZW5hbWUlMjAlM0QlMjB0ZW1wZmlsZS5ta3N0ZW1wKCUyMi5wbmclMjIpJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwb3MuY2xvc2UoZmQpJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwdHJ5JTNBJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwYml0bWFwLlNhdmVGaWxlKGZpbGVuYW1lJTJDJTIwd3guQklUTUFQX1RZUEVfUE5HKSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHNlbGYuX25vdGlmaWVyLm5vdGlmeSgiLCJtZXRhZGF0YSI6eyJkaXNwbGF5X25hbWUiOiJub3RpZmllcl9ncm93bC5weSIsIm1pbWVfdHlwZSI6InRleHQvcGxhaW4iLCJmaWxlX3NpemUiOjIwNTYsImNyZWF0ZWRfdGltZSI6IjIwMjUtMTEtMjJUMDU6Mzk6NTQiLCJ1cGRhdGVkX3RpbWUiOiIyMDI1LTExLTIyVDA1OjM5OjU0IiwibGFiZWwiOiIxIn19)


class TkinterGrowlNotifier(AbstractNotifier):
    def __init__(self):
        super().__init__()
        self._available = True  # Tkinter est toujours disponible

    def getName(self):
        return "TkinterGrowl"

    def isAvailable(self):
        return self._available

    def notify(self, title, summary, bitmap, **kwargs):
        # Sauvegarde temporaire du bitmap et affichage via messagebox
        fd, filename = tempfile.mkstemp(".png")
        os.close(fd)
        try:
            # bitmap.SaveFile(filename, wx.BITMAP_TYPE_PNG)  # [1](https://app.textcortex.com/file?id=file_01kan16xjjf0eswjzssvbx2ha8&state=eyJzbmlwcGV0IjoiZnJvbSUyMGdudHAlMjBpbXBvcnQlMjBub3RpZmllciUyMGFzJTIwZ3Jvd2wlMjBmcm9tJTIwdGFza2NvYWNobGliJTIwaW1wb3J0JTIwbWV0YSUyMGZyb20lMjAubm90aWZpZXIlMjBpbXBvcnQlMjBBYnN0cmFjdE5vdGlmaWVyJTIwJTIwJTIwY2xhc3MlMjBHcm93bE5vdGlmaWVyKEFic3RyYWN0Tm90aWZpZXIpJTNBJTIwJTIwJTIwJTIwJTIwZGVmJTIwX19pbml0X18oc2VsZiklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzdXBlcigpLl9faW5pdF9fKCklMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjB0cnklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjMlMjBweWxpbnQlM0ElMjBkaXNhYmxlJTNERTExMDElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9ub3RpZmllciUyMCUzRCUyMGdyb3dsLkdyb3dsTm90aWZpZXIoYXBwbGljYXRpb25OYW1lJTNEbWV0YS5uYW1lJTJDJTIwbm90aWZpY2F0aW9ucyUzRCU1QiUyMlJlbWluZGVyJTIyJTVEKSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHNlbGYuX25vdGlmaWVyLnJlZ2lzdGVyKCklMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBleGNlcHQlM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9hdmFpbGFibGUlMjAlM0QlMjBGYWxzZSUyMCUyMCUyMyUyMHB5bGludCUzQSUyMGRpc2FibGUlM0RXMDcwMiUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMGVsc2UlM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjBzZWxmLl9hdmFpbGFibGUlMjAlM0QlMjBUcnVlJTIwJTIwJTIwJTIwJTIwJTIwZGVmJTIwZ2V0TmFtZShzZWxmKSUzQSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHJldHVybiUyMCUyMkdyb3dsJTIyJTIwJTIwJTIwJTIwJTIwJTIwZGVmJTIwaXNBdmFpbGFibGUoc2VsZiklM0ElMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjAlMjByZXR1cm4lMjBzZWxmLl9hdmFpbGFibGUlMjAlMjAlMjAlMjAlMjAlMjBkZWYlMjBub3RpZnkoc2VsZiUyQyUyMHRpdGxlJTJDJTIwc3VtbWFyeSUyQyUyMGJpdG1hcCUyQyUyMCoqa3dhcmdzKSUzQSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMyUyME5vdCUyMHJlYWxseSUyMGVmZmljaWVudC4uLiUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMGZkJTJDJTIwZmlsZW5hbWUlMjAlM0QlMjB0ZW1wZmlsZS5ta3N0ZW1wKCUyMi5wbmclMjIpJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwb3MuY2xvc2UoZmQpJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwdHJ5JTNBJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwJTIwYml0bWFwLlNhdmVGaWxlKGZpbGVuYW1lJTJDJTIwd3guQklUTUFQX1RZUEVfUE5HKSUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMCUyMHNlbGYuX25vdGlmaWVyLm5vdGlmeSgiLCJtZXRhZGF0YSI6eyJkaXNwbGF5X25hbWUiOiJub3RpZmllcl9ncm93bC5weSIsIm1pbWVfdHlwZSI6InRleHQvcGxhaW4iLCJmaWxlX3NpemUiOjIwNTYsImNyZWF0ZWRfdGltZSI6IjIwMjUtMTEtMjJUMDU6Mzk6NTQiLCJ1cGRhdGVkX3RpbWUiOiIyMDI1LTExLTIyVDA1OjM5OjU0IiwibGFiZWwiOiIxIn19)
            # Convertir wx.Bimap en PIL Image
            width, height = bitmap.GetWidth(), bitmap.GetHeight()
            buffer = bitmap.ConvertToImage().GetData()
            pil_image = Image.frombuffer("RGB", (width, height), buffer, "raw", "RGB", 0, 1)
            pil_image.save(filename, "PNG")

            tkinter.Tk().withdraw()  # Masque la fenêtre principale Tkinter
            messagebox.showinfo(title, summary)
        finally:
            os.remove(filename)


AbstractNotifier.register(TkinterGrowlNotifier())
