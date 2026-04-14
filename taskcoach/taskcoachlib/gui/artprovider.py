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

Module ArtProvider pour Task Coach.

Ce module gère la fourniture et la manipulation des icônes et images pour l'interface utilisateur de Task Coach.
Il utilise la classe wx.ArtProvider pour fournir des bitmaps et icônes avec la possibilité de superposer des images
ou d'ajuster les canaux alpha (transparence) des bitmaps.

Classes :
---------
- ArtProvider : Sous-classe de wx.ArtProvider, responsable de la création de bitmaps à partir de fichiers d'icônes, avec des fonctionnalités de superposition et de manipulation des canaux alpha.
- IconProvider : Singleton gérant un cache d'icônes pour éviter les fuites de mémoire dans les objets GDI. Fournit des icônes dans différentes tailles pour divers usages (boutons, menus, etc.).

Fonctions :
-----------
- iconBundle(iconTitle) : Crée un groupe d'icônes à partir d'un titre d'icône, avec plusieurs tailles pour différentes résolutions.
- getIcon(iconTitle) : Renvoie l'icône correspondant au titre donné, en utilisant un cache pour optimiser la gestion mémoire.
- init() : Initialise l'ArtProvider avec certaines options spécifiques à la plateforme, notamment sous Windows pour désactiver certains remappages d'icônes.

Les fonctions internes telles que `convertAlphaToMask` gèrent des détails spécifiques à l'affichage, comme la conversion des canaux alpha en masques pour certaines plateformes comme GTK.
"""

print("ARTPROVIDER IMPORT")
# from __future__ import division

# from builtins import chr
# from builtins import range
# from past.utils import old_div
from taskcoachlib import patterns, operating_system
from taskcoachlib.i18n import _
from taskcoachlib.tools import wxhelper
import numpy as np
import os
import sys
import wx
from taskcoachlib.gui import icons  # where?


# Création d'un nouveau fournisseur d'images
class ArtProvider(wx.ArtProvider):
    """Sous-classe de wx.ArtProvider, responsable de la création de bitmaps à partir de fichiers d'icônes,
    avec des fonctionnalités de superposition et de manipulation des canaux alpha.

    wx.ArtProvider est une classe qui gère la manière dont wxPython trouve et affiche les images (art) utilisées dans l'interface.
    """

    # Voir la méthode : https://docs.wxpython.org/wx.ArtProvider.html
    # Penser à Retirer le fournisseur d'images de la pile avec :
    # wx.ArtProvider.Pop()
    def CreateBitmap(self, artId, artClient, size):
        """Création de bitmap avec import wx différé."""
        # import wx  # Import local obligatoire

        # La méthode CreateIconBundle est similaire à CreateBitmap mais peut être utilisée lorsqu'un bitmap (ou une icône) existe en plusieurs tailles.
        if not wx.GetApp():
            return wx.NullBitmap  # sécurité anti crash

        # bitmap = wx.Bitmap(size[0], size[1])
        # dc = wx.MemoryDC(bitmap)
        # dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0, 0)))  # Transparent
        # dc.Clear()
        # del dc
        # return bitmap
        # Si l'Id contient "+", séparer en deux noms d'image.
        if "+" in artId:
            w, h = size
            main, overlay = artId.split("+")

            overlayImage = self._CreateBitmap(
                overlay, artClient, size
            ).ConvertToImage()  # type: wx.Image
            # overlayImage.Rescale(int(old_div(w, 2)), int(old_div(h, 2)), wx.IMAGE_QUALITY_HIGH)
            overlayImage.Rescale(w // 2, h // 2, wx.IMAGE_QUALITY_HIGH)
            # Utilisation de GetAlpha pour gérer la transparence sous GTK.
            # overlayAlpha = overlayImage.GetAlphaData()
            # AttributeError: 'Image' object has no attribute 'GetAlphaData'
            # if overlayImage.HasAlpha():
            #    # overlayAlpha = overlayImage.GetAlpha()
            # overlayAlpha = overlayImage.GetAlphaBuffer()  # I try
            # else:
            #    # Handle the case where there is no alpha channel
            #     overlayAlpha = None
            # overlayAlpha = overlayImage.GetAlphaBuffer()  # TODO: a essayer (starofrainnight)
            overlayAlpha = (
                overlayImage.GetAlpha() if overlayImage.HasAlpha() else None
            )
            overlayBitmap = (
                overlayImage.ConvertToBitmap()
            )  # self._Application__wx_app.Traits={AttributeError}AttributeError("'ArtProvider' object has no attribute '_Application__wx_app'")

            mainImage = self._CreateBitmap(
                main, artClient, size
            ).ConvertToImage()  # type: wx.Image
            # vieux code :
            # mainAlpha = mainImage.GetAlphaData()
            # AttributeError: 'Image' object has no attribute 'GetAlphaData'
            # nouveau code :
            # if mainImage.HasAlpha():
            #     # mainAlpha = mainImage.GetAlpha()
            # mainAlpha = wxhelper.getAlphaDataFromImage(mainImage)  # I try
            # else:
            #     # Handle the case where there is no alpha channel
            #     mainAlpha = None
            #     # mainImage.SetAlphaData(chr(255) * len(mainAlpha))
            #     # AttributeError: 'Image' object has no attribute 'SetAlphaData'
            #     # mainImage.SetAlpha(255 * len(mainAlpha))
            #     # TypeError: Image.SetAlpha(): arguments did not match any overloaded call:
            #     #   overload 1: not enough arguments
            #     #   overload 2: argument 1 has unexpected type 'int'
            #     mainAlphaToSet = [255] * (mainImage.GetWidth() * mainImage.GetHeight())

            # # Convertir le canal alpha en une liste d'entiers si ce n'est pas déjà fait
            # mainAlpha = list(map(int, mainAlphaToSet))

            # # Manipuler mainAlpha ici si nécessaire avant de le réappliquer à l'image
            # mainImage.SetAlpha(mainAlpha)
            # sinon essayer ses 2 lignes :
            mainAlpha = wxhelper.getAlphaDataFromImage(mainImage)
            wxhelper.clearAlphaDataOfImage(mainImage, 255)
            mainBitmap = mainImage.ConvertToBitmap()

            # dc = wx.MemoryDC(bitmap)
            # dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0, 0)))  # Transparent
            # dc.Clear()
            # del dc
            # return bitmap
            dstDC = wx.MemoryDC()
            dstDC.SelectObject(mainBitmap)
            try:
                # dstDC.DrawBitmap(overlayBitmap, w - int(old_div(w, 2)), h - int(old_div(h, 2)), True)
                dstDC.DrawBitmap(
                    overlayBitmap, w - (w // 2), h - (h // 2), True
                )
            finally:
                dstDC.SelectObject(wx.NullBitmap)

            mainImage = mainBitmap.ConvertToImage()

            # Just drawing works fine on OS X but clips to the destination bitmap on
            # other platforms. There doesn't seem to be anything better than this.
            # resultAlpha = list()
            # # TODO: essayer ça :
            # # resultAlpha = []
            # for y in range(h):
            #     for x in range(w):
            #         alpha = mainAlpha[y * w + x]
            #         # if x >= old_div(w, 2) and y >= old_div(h, 2):
            #         if x >= w // 2 and y >= h // 2 and overlayAlpha:
            #             # alpha = max(alpha, overlayAlpha[old_div((y - old_div(h, 2)) * w, 2) + x - old_div(w, 2)])
            #             alpha = max(
            #                 alpha,
            #                 overlayAlpha[(y - h // 2) * w // 2 + x - w // 2])
            #         resultAlpha.append(alpha)
            resultAlpha = [
                (
                    max(
                        mainAlpha[y * w + x],
                        overlayAlpha[(y - h // 2) * (w // 2) + x - w // 2],
                    )
                    if overlayAlpha and x >= w // 2 and y >= h // 2
                    else mainAlpha[y * w + x]
                )
                for y in range(h)
                for x in range(w)
            ]
            # mainImage.SetAlphaData(''.join(bytes(resultAlpha)))
            # mainImage.SetAlpha(bytes(resultAlpha))
            wxhelper.setAlphaDataToImage(mainImage, resultAlpha)

            return mainImage.ConvertToBitmap()
        else:
            return self._CreateBitmap(artId, artClient, size)

    def _CreateBitmap(self, artId, artClient, size) -> wx.Bitmap:
        """Création interne de bitmap."""

        # import wx  # Import local
        # from taskcoachlib.gui import icons  # Import différé

        # print("DEBUG: _CreateBitmap called")
        if not artId:
            # return wx.EmptyBitmap(*size)
            return wx.Bitmap(*size)
            # return wx.NullBitmap  # temporairement
        # catalogKey = "%s%dx%d" % (artId, size[0], size[1])
        catalogKey = f"{artId}{size[0]}x{size[1]}"
        # print(f"DEBUG: Checking catalog for key: {catalogKey}")
        # print(f"DEBUG: Available keys: {list(icons.catalog.keys())}")
        # if catalogKey in list(icons.catalog.keys()):
        if catalogKey in icons.catalog:
            # bitmap = icons.catalog[catalogKey].getBitmap()
            bitmap = icons.catalog[catalogKey].GetBitmap()
            # if artClient == wx.ART_FRAME_ICON:
            #     bitmap = self.convertAlphaToMask(bitmap)
            # return bitmap
            return (
                self.convertAlphaToMask(bitmap)
                if artClient == wx.ART_FRAME_ICON
                else bitmap
            )
            # return icons.catalog[catalogKey].GetBitmap()
        else:
            return wx.NullBitmap

    @staticmethod
    def convertAlphaToMask(bitmap):
        """Convertit alpha en masque."""

        # import wx  # Import local

        # Conversion des bitmaps:
        # image = wx.ImageFromBitmap(bitmap)
        image = bitmap.ConvertToImage()

        image.ConvertAlphaToMask()
        # image.ConvertToMono(255, 255, 255)
        # image.ConvertToMask(wx.Colour(255, 255, 255))
        # image = image.ConvertToDisabled(255)
        # image.ConvertToMono(0, 0, 0)  # Force une conversion stable en noir et blanc

        # return wx.BitmapFromImage(image)
        return wx.Bitmap(image)
        # return wx.Bitmap(image, depth=32)


# class IconProvider(metaclass=patterns.Singleton):
class IconProvider(object, metaclass=patterns.Singleton):
    """Singleton gérant un cache d'icônes pour éviter les fuites de mémoire dans les objets GDI.
    Fournit des icônes dans différentes tailles pour divers usages (boutons, menus, etc.).
    """

    def __init__(self):
        """Initialise l'ArtProvider avec certaines options spécifiques à la plateforme,
        notamment sous Windows pour désactiver certains remappages d'icônes."""
        self.__iconCache = dict()
        if operating_system.isMac():
            self.__iconSizeOnCurrentPlatform = 128
        elif operating_system.isGTK():
            self.__iconSizeOnCurrentPlatform = 48
        else:
            self.__iconSizeOnCurrentPlatform = 16

    def getIcon(self, iconTitle):
        """Renvoie l'icône. Utilisez un cache pour éviter la fuite du
        nombre d'objets GDI.

        Recommandé pour l'usage général. Utilise le cache pour la performance.
        """
        try:
            return self.__iconCache[iconTitle]
        except KeyError:
            icon = self.getIconFromArtProvider(iconTitle)
            self.__iconCache[iconTitle] = icon
            return icon

    def iconBundle(self, iconTitle):
        """Créez un groupe d'icônes avec des icônes de différentes tailles.

        Utilisé pour les icônes de fenêtres (le logo en haut à gauche)
        car il contient plusieurs tailles (16, 32, 48...)
        pour que Windows/Linux choisisse la meilleure selon le contexte.
        """
        # import wx

        bundle = wx.IconBundle()
        for size in (16, 22, 32, 48, 64, 128):
            bundle.AddIcon(self.getIconFromArtProvider(iconTitle, size))
        return bundle

    def getIconFromArtProvider(self, iconTitle, iconSize=None):
        """
        Recommandé pour la barre d'outils. Permet de forcer une taille précise (ex: 16x16 ou 32x32).

        Args:
            iconTitle:
            iconSize:

        Returns:

        """
        # import wx

        size = iconSize or self.__iconSizeOnCurrentPlatform
        # I just spent two hours trying to get rid of garbage in the icon
        # background on KDE. I give up.
        if operating_system.isGTK():
            if type(size) is not tuple:
                return wx.ArtProvider.GetIcon(
                    iconTitle, wx.ART_FRAME_ICON, (size, size)
                )
            # elif type(size) is tuple:
            #     return wx.ArtProvider.GetIcon(
            #         iconTitle, wx.ART_FRAME_ICON, size
            #     )  # NON, empêche de continuer sur les autres possibilités.

        # wx.ArtProvider_GetIcon doesn't convert alpha to mask, so we do it
        # ourselves:
        if type(size) is not tuple:
            bitmap = wx.ArtProvider.GetBitmap(
                iconTitle, wx.ART_FRAME_ICON, (size, size)
            )
        elif type(size) is tuple:
            bitmap = wx.ArtProvider.GetBitmap(
                iconTitle, wx.ART_FRAME_ICON, size
            )
        bitmap = ArtProvider.convertAlphaToMask(bitmap)
        # return wx.IconFromBitmap(bitmap)
        return wx.Icon(bitmap)


def iconBundle(iconTitle):
    """Crée un groupe d'icônes à partir d'un titre d'icône, avec plusieurs tailles pour différentes résolutions."""
    return IconProvider().iconBundle(iconTitle)


def getIcon(iconTitle):
    """Renvoie l'icône correspondant au titre donné, en utilisant un cache pour optimiser la gestion mémoire."""
    return IconProvider().getIcon(iconTitle)


def init():
    """Initialise l'ArtProvider avec certaines options spécifiques à la plateforme,
    notamment sous Windows pour désactiver certains remappages d'icônes avec corrections GTK.
    """
    # import wx  # Import local pour éviter effets de bord

    app = wx.GetApp()  # Récupère l'application wx
    if not app:  # Si aucune application wx n'existe
        app = wx.App(
            False
        )  # Création sécurisée d'une application wx sans interface graphique

    # wx.ArtProvider.PushProvider() était une méthode utilisée pour temporairement
    # remplacer le fournisseur d'images par défaut par un autre,
    # ce qui permettait de personnaliser l'apparence des éléments de l'interface.
    # Remplacé par Push.
    if operating_system.isWindows() and wx.DisplayDepth() >= 32:
        wx.SystemOptions.SetOption("msw.remap", "0")  # pragma: no cover
    if operating_system.isGTK():
        wx.SystemOptions.SetOption("gtk.desktop", "1")
    # Pousser le nouveau fournisseur d'images sur la pile:
    # try:
    #     # Ancienne méthode
    #     wx.ArtProvider.PushProvider(ArtProvider())  # pylint: disable=E1101
    #     # PushProvider n'existe pas voir Push ou PushBack
    #     # wx.ArtProvider.Push(ArtProvider())
    #     # wx.ArtProvider.PushBack(ArtProvider())
    # except AttributeError:
    #     # Nouvelle méthode Python3:
    # Push du provider seulement après wx prêt à l'utiliser, sinon wx.ArtProvider n'existe pas encore.
    wx.ArtProvider.Push(ArtProvider())
    # wx.ArtProvider.PushBack(ArtProvider())


# Dictionnaire des images sélectionnables
chooseableItemImages = dict(
    arrow_down_icon=_("Arrow down"),
    arrow_down_with_status_icon=_("Arrow down with status"),
    arrows_looped_blue_icon=_("Blue arrows looped"),
    arrows_looped_green_icon=_("Green arrows looped"),
    arrow_up_icon=_("Arrow up"),
    arrow_up_with_status_icon=_("Arrow up with status"),
    bomb_icon=_("Bomb"),
    book_icon=_("Book"),
    books_icon=_("Books"),
    box_icon=_("Box"),
    bug_icon=_("Ladybug"),
    cake_icon=_("Cake"),
    calculator_icon=_("Calculator"),
    calendar_icon=_("Calendar"),
    cat_icon=_("Cat"),
    cd_icon=_("Compact disc (CD)"),
    charts_icon=_("Charts"),
    chat_icon=_("Chatting"),
    checkmark_green_icon=_("Check mark"),
    checkmark_green_icon_multiple=_("Check marks"),
    clock_icon=_("Clock"),
    clock_alarm_icon=_("Alarm clock"),
    clock_stopwatch_icon=_("Stopwatch"),
    cogwheel_icon=_("Cogwheel"),
    cogwheels_icon=_("Cogwheels"),
    computer_desktop_icon=_("Desktop computer"),
    computer_laptop_icon=_("Laptop computer"),
    computer_handheld_icon=_("Handheld computer"),
    cross_red_icon=_("Red cross"),
    die_icon=_("Die"),
    document_icon=_("Document"),
    earth_blue_icon=_("Blue earth"),
    earth_green_icon=_("Green earth"),
    envelope_icon=_("Envelope"),
    envelopes_icon=_("Envelopes"),
    folder_blue_icon=_("Blue folder"),
    folder_blue_light_icon=_("Light blue folder"),
    folder_green_icon=_("Green folder"),
    folder_grey_icon=_("Grey folder"),
    folder_orange_icon=_("Orange folder"),
    folder_purple_icon=_("Purple folder"),
    folder_red_icon=_("Red folder"),
    folder_yellow_icon=_("Yellow folder"),
    folder_blue_arrow_icon=_("Blue folder with arrow"),
    heart_icon=_("Heart"),
    hearts_icon=_("Hearts"),
    house_green_icon=_("Green house"),
    house_red_icon=_("Red house"),
    key_icon=_("Key"),
    keys_icon=_("Keys"),
    lamp_icon=_("Lamp"),
    led_blue_questionmark_icon=_("Question mark"),
    led_blue_information_icon=_("Information"),
    led_blue_icon=_("Blue led"),
    led_blue_light_icon=_("Light blue led"),
    led_grey_icon=_("Grey led"),
    led_green_icon=_("Green led"),
    led_green_light_icon=_("Light green led"),
    led_orange_icon=_("Orange led"),
    led_purple_icon=_("Purple led"),
    led_red_icon=_("Red led"),
    led_yellow_icon=_("Yellow led"),
    life_ring_icon=_("Life ring"),
    lock_locked_icon=_("Locked lock"),
    lock_unlocked_icon=_("Unlocked lock"),
    magnifier_glass_icon=_("Magnifier glass"),
    music_piano_icon=_("Piano"),
    music_note_icon=_("Music note"),
    note_icon=_("Note"),
    palette_icon=_("Palette"),
    paperclip_icon=_("Paperclip"),
    pencil_icon=_("Pencil"),
    person_icon=_("Person"),
    persons_icon=_("People"),
    person_id_icon=_("Identification"),
    person_talking_icon=_("Person talking"),
    sign_warning_icon=_("Warning sign"),
    symbol_minus_icon=_("Minus"),
    symbol_plus_icon=_("Plus"),
    star_red_icon=_("Red star"),
    star_yellow_icon=_("Yellow star"),
    trafficlight_icon=_("Traffic light"),
    trashcan_icon=_("Trashcan"),
    weather_lightning_icon=_("Lightning"),
    weather_umbrella_icon=_("Umbrella"),
    weather_sunny_icon=_("Partly sunny"),
    wrench_icon=_("Wrench"),
)

itemImages = list(chooseableItemImages.keys()) + [
    "folder_blue_open_icon",
    "folder_green_open_icon",
    "folder_grey_open_icon",
    "folder_orange_open_icon",
    "folder_red_open_icon",
    "folder_purple_open_icon",
    "folder_yellow_open_icon",
    "folder_blue_light_open_icon",
]

chooseableItemImages[""] = _("No icon")
