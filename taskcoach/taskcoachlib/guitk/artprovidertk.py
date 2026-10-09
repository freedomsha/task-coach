# -*- coding: utf-8 -*-

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

Module ArtProvider pour Task Coach version Tkinter (artprovider.py).

Ce module gère la fourniture et la manipulation des icônes et images pour l'interface utilisateur de Task Coach.
Ce module fournit des icônes et des images en utilisant le module
`icons.py` et les fonctions d'aide de `tkhelper.py`.
Il implémente une logique de création et de mise en cache pour
optimiser la gestion des ressources graphiques.
La version utilise la classe wx.ArtProvider pour fournir des bitmaps et icônes avec la possibilité de superposer des images
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
# Pour convertir le fichier artprovider.py de wxPython à tkinter,
# il est nécessaire de remplacer toutes les fonctionnalités spécifiques à wxPython
# par leurs équivalents tkinter. Cela inclut la gestion des images, des icônes et des options système.
#
# Voici les principales modifications :
#
#     Gestion des images et icônes : tkinter utilise PIL (Pillow)
#     pour gérer divers formats d'images et ne dispose pas d'un système ArtProvider intégré
#     comme wxPython. Il faut donc charger les images en tant que PhotoImage
#     ou BitmapImage de tkinter.PhotoImage et tkinter.BitmapImage ou PIL.ImageTk.PhotoImage
#     pour les images plus complexes.
#
#     Superposition d'images : La logique de superposition d'images
#     (avec le + dans l'ID de l'art) devra être recréée manuellement
#     en utilisant des opérations sur les images PIL.
#
#     Canaux Alpha et masques : La conversion des canaux alpha en masques est
#     une spécificité de wxPython. Avec Pillow, la transparence est gérée nativement,
#     et la logique de convertAlphaToMask peut être simplifiée ou adaptée
#     pour manipuler directement les canaux alpha des images PIL.
#
#     Options système : Les wx.SystemOptions n'ont pas d'équivalent direct
#     dans tkinter. Ces lignes peuvent être supprimées ou remplacées par
#     des configurations spécifiques à tkinter si nécessaire.
#
#     IconProvider : Le concept de cache d'icônes peut être conservé,
#     mais l'implémentation de getIconFromArtProvider devra être réécrite
#     pour utiliser les objets image de tkinter.
#
# Étant donné que le fichier artprovider.py dépend de taskcoachlib.gui.icons
# et taskcoachlib.tools.wxhelper, ces dépendances devront également être adaptées
# ou simulées pour tkinter.
#
# Résumé des changements :
#
#     PIL (Pillow) est maintenant une dépendance essentielle pour la manipulation d'images.
#     Vous devrez l'installer (pip install Pillow) si ce n'est pas déjà fait.
#
#     Les classes ArtProvider et IconProvider ont été réécrites pour utiliser les objets Image de PIL et les convertir en ImageTk.PhotoImage pour tkinter.
#
#     La logique de superposition d'images dans ArtProvider.CreateBitmap est maintenant gérée par les méthodes de PIL.Image.paste().
#
#     Les fonctions getAlphaDataFromImage, clearAlphaDataOfImage, et setAlphaDataToImage de wxhelper ont été simulées dans une classe MockWxHelper pour montrer comment elles pourraient être implémentées avec PIL.
#
#     Le catalogue d'icônes (icons.catalog) a été simulé avec MockIconsCatalog pour permettre au code de s'exécuter sans les fichiers d'icônes réels. Vous devrez remplacer cette simulation par votre propre logique de chargement d'images réelles.
#
#     Les appels à wx.ArtProvider.Push et wx.SystemOptions.SetOption ont été supprimés ou adaptés, car ils n'ont pas d'équivalent direct dans tkinter.
#
# Ce fichier fournit une base pour l'intégration de votre système d'icônes avec tkinter. Vous devrez adapter les parties simulées (MockIconsCatalog, MockWxHelper) pour charger vos images et gérer les données alpha de manière appropriée si vos icônes utilisent des transparences complexes.

# J'ai mis à jour le code de artprovidertk.py pour qu'il inclue les importations nécessaires de guitk.icons et tools.tkhelper. J'ai également réécrit la classe ArtProviderTk pour qu'elle utilise correctement les objets PyEmbeddedImageTk de votre fichier icons.py et gère le redimensionnement des images via Pillow.
#
# Pour le moment, j'ai inclus un exemple de démonstration dans le bloc if __name__ == '__main__': afin que vous puissiez tester le fonctionnement du fournisseur d'art. Cela vous permet de vérifier que les icônes se chargent correctement et que le redimensionnement fonctionne.

#
# Les classes ArtProvider et IconProvider du code original artprovider.py ont été adaptées pour les spécificités de Tkinter et de la bibliothèque Pillow.
#
# Voici la logique que j'ai suivie :
#
#     ArtProvider: La classe ArtProviderTk dans le nouveau code joue le rôle de la classe ArtProvider originale.
#                  Elle gère la récupération et la mise en cache des images.
#                  La méthode GetBitmap remplace la méthode CreateBitmap de la version wxPython, car Tkinter n'utilise pas le même modèle d'objets.
#
#     IconProvider: La classe IconProvider du code wxPython gérait un cache d'icônes et des tailles spécifiques.
#                   Dans le nouveau code, cette fonctionnalité est intégrée directement dans ArtProviderTk.
#                   Le dictionnaire self._icon_cache remplit exactement la même fonction,
#                   en stockant les objets PhotoImage pour éviter de les recréer à chaque fois.
#                   Cela rend la gestion des icônes plus simple et plus efficace dans le contexte de Tkinter.
#
# En bref, les fonctionnalités de ces deux classes ont été fusionnées en une seule, ArtProviderTk, pour s'aligner sur la manière dont Tkinter gère les images.

# Améliorations pour artprovidertk.py
#
# Gestion des erreurs :
# Dans la méthode GetBitmap,
#    ajoute une gestion des erreurs plus robuste pour les cas où l'icône n'est pas trouvée ou ne peut pas être chargée.
#    Cela peut inclure l'enregistrement d'un message d'erreur plus détaillé et le retour d'une icône par défaut au lieu de None.
# Dans convertAlphaToMask,
#    la conversion directe d'un PhotoImage en PIL Image n'est pas supportée et une simulation est utilisée.
#    Dans un environnement de production, assurez-vous d'utiliser les images sources originales avec PIL pour cette manipulation.
#    C'est fait !
#
#
# Documentation :
# Ajoute des docstrings plus complètes pour chaque méthode, expliquant ses arguments, son comportement et sa valeur de retour. Cela facilitera la compréhension et la maintenance du code.
#
#
# Découplage :
# Séparer complètement le chargement des images de la manipulation des images. Le catalogue devrait contenir les données brutes, et une fonction séparée devrait prendre ces données et les transformer en PhotoImage. Cela améliore la modularité.

# Améliorations supplémentaires (basées sur les suggestions précédentes)
#
# Gestion des exceptions : Enveloppe le chargement et la conversion des images dans des blocs try...except pour gérer les erreurs potentielles (par exemple, fichier introuvable, format d'image non valide).
# Logging : Utilise le module logging pour enregistrer les erreurs et les avertissements de manière structurée. Cela facilitera le débogage et la maintenance.
# Cache : Implémente un mécanisme de cache pour stocker les images déjà chargées et éviter de les recharger à chaque fois.

# Points importants :
#
# Gestion des erreurs : J'ai ajouté des blocs try...except pour intercepter les erreurs potentielles lors du chargement des icônes et j'utilise logging pour enregistrer les erreurs.  Tu peux configurer le niveau de verbosité du logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) en fonction de tes besoins.
# Cache : J'ai ajouté un cache simple pour éviter de recharger les icônes à chaque fois qu'elles sont demandées.  La clé du cache est une combinaison de l'ID de l'icône et de la taille souhaitée.
# Chemins d'accès : Assure-toi que les chemins d'accès aux fichiers d'icônes sont corrects.

# IMPORTANT:
# IconProvider retourne des PhotoImage Tkinter.
# Toute manipulation graphique DOIT être faite sur des PIL.Image.
# La PhotoImage finale ne doit être créée qu'à la toute fin.

import logging
import os
from typing import Union, Dict, Optional, Tuple
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # Importation de Pillow pour la manipulation d'images

from taskcoachlib import patterns, operating_system
from taskcoachlib.i18n import _
# Importation des modules Tkinter convertis
from taskcoachlib.guitk import icons as icons_tk
from taskcoachlib.tools import tkhelper as tkhelper

log = logging.getLogger(__name__)

# Constantes basées sur wxPython pour la compatibilité
ART_TOOLBAR = "ART_TOOLBAR"
ART_MENU = "ART_MENU"
ART_BUTTON = "ART_BUTTON"
# Cache global pour les icônes déjà chargées
_icon_cache = {}
# Taille par défaut pour les icônes (si non spécifiée)
_DEFAULT_SIZE = (16, 16)


class ArtProviderTk(object):
    """
    Fournisseur d'art pour tkinter, gérant la création et la superposition d'images.

    Fournit des bitmaps et des icônes à partir du module icons.py.
    """
    # _icon_cache = {}  # Dictionnaire pour stocker les icônes mises en cache

    def __init__(self):
        # Le cache pour les icônes déjà créées afin d'éviter la recréation
        self._icon_cache = {}

    @staticmethod
    def GetBitmap(art_id: str, art_client: str = ART_TOOLBAR,
                  desired_size: Optional[tuple] = None) -> Union[tk.PhotoImage, None]:
        """
        Retourne un objet PhotoImage pour un ID d'icône donné.
        S'il n'existe pas dans le cache, il le crée et l'ajoute.

        Args:
            art_id: L'identifiant de l'icône (ex: 'copy16x16').
            art_client: Le contexte d'utilisation de l'icône (toolbar, menu, etc.).
            desired_size: La taille souhaitée de l'icône, si une mise à l'échelle est nécessaire.

        Returns:
            Un objet PhotoImage de Tkinter ou None si l'icône n'est pas trouvée.
        """
        if desired_size:
            icon_id = f"{art_id}{desired_size[0]}x{desired_size[1]}"
        else:
            icon_id = f"{art_id}16x16"  # Taille par défaut

        # Clé de cache unique pour chaque combinaison d'ID et de taille
        cache_key = (art_id, desired_size)
        # if cache_key in self._icon_cache:
        #     return self._icon_cache[cache_key]
        # if cache_key in ArtProviderTk._icon_cache:
        if cache_key in _icon_cache:
            # return ArtProviderTk._icon_cache[cache_key]
            return _icon_cache[cache_key]

        try:
            # Cherche l'icône directement dans le catalogue
            # if art_id in icons_tk.catalog:
            if icon_id in icons_tk.catalog:
                # icon_embedded = icons_tk.catalog[art_id]
                icon_embedded = icons_tk.catalog[icon_id]

                # Récupère l'image PIL à partir de l'objet PyEmbeddedImageTk
                image_pil = icon_embedded.GetImage()   # On appelle la méthode GetImage de l'instance

                if desired_size and image_pil.size != desired_size:
                    # Redimensionne l'image PIL si une taille est spécifiée
                    image_pil = image_pil.resize(desired_size, Image.LANCZOS)

                # Crée l'objet PhotoImage de Tkinter à partir de l'image PIL
                photo_image = ImageTk.PhotoImage(image_pil)
                # self._icon_cache[cache_key] = photo_image
                # ArtProviderTk._icon_cache[cache_key] = photo_image
                _icon_cache[cache_key] = photo_image
                return photo_image
            else:
                # log.error(f"Icône non trouvé dans le catalogue : {art_id}", stack_info=True)
                log.error(f"Icône non trouvé dans le catalogue : {icon_id}", stack_info=True)
                return None
                # return ""
        except Exception as e:
            # log.exception(f"Erreur lors du chargement de l'icône {art_id}: {e}")
            log.exception(f"Erreur lors du chargement de l'icône {icon_id}: {e}")
            return None  # Retourne None en cas d'erreur
            # return ""  # Retourne "" en cas d'erreur

    # def GetIcon(self, art_id: str, art_client: str = ART_TOOLBAR, desired_size: Optional[tuple] = None) -> Union[tk.PhotoImage, None]:
    #     """
    #     Alias pour GetBitmap, car Tkinter n'a pas de distinction native entre icônes et bitmaps.
    #     """
    #     return self.GetBitmap(art_id, art_client, desired_size)

    @staticmethod
    # def GetIcon(art_id, desired_size=_DEFAULT_SIZE, **kwargs):
    def GetIcon(art_id: str, art_client: str = ART_TOOLBAR,
                desired_size: Optional[tuple] = None) -> Union[tk.PhotoImage, None]:
        """
        Récupère une icône basée sur son identifiant (art_id).

        Retourne un objet PhotoImage pour un ID d'icône donné.

        Args :
            art_id : Identifiant de l'icône (par exemple, 'wrench_icon').
            art_client :
            desired_size : Taille souhaitée de l'icône (tuple de largeur et hauteur).
        Returns :
            Une instance de ImageTk.PhotoImage ou None si non trouvée.
        """
        # # Logique de mise en cache
        # cache_key = (art_id, desired_size)
        # if cache_key in _icon_cache:
        #     return _icon_cache[cache_key]
        #
        # # 1. Obtenir les données brutes de l'icône (simulé)
        # # icon_data = _get_icon_data(art_id, desired_size)
        # icon_data = icons_tk.PyEmbeddedImageTk.GetImage(art_id)
        #
        # if not icon_data:
        #     return None

        # try:
        #     width, height = desired_size
        #     color = icon_data['color']
        #
        #     # 2. Créer une image PIL de base (simulation de l'icône)
        #     # L'icône réelle serait chargée à partir de données binaires (icons.py)
        #     img = Image.new('RGBA', (width, height), color)
        #
        #     # 3. Convertir l'image PIL en ImageTk.PhotoImage
        #     # ATTENTION: PhotoImage doit être lié à un objet Tk ou Toplevel existant.
        #     # Pour éviter un crash si appelé avant l'initialisation de Tkinter,
        #     # nous devons nous assurer que le root est créé (ce qui est le cas dans
        #     # le scénario d'exécution de Task Coach ou le bloc __main__ de preferencestk.py).
        #
        #     # Le Tkinter PhotoImage doit être créé APRES tk.Tk().
        #     # Nous assumons ici que l'appel est fait dans un contexte où cela est possible.
        #     photo_image = ImageTk.PhotoImage(img)
        #
        #     # Mettre en cache et retourner
        #     _icon_cache[cache_key] = photo_image
        #     return photo_image

        try:
            bitmap = ArtProviderTk.GetBitmap(art_id, art_client, desired_size)
            return bitmap
        except Exception as e:
            # Gérer les erreurs de chargement ou de conversion
            log.error(f"ArtProvider.GetIcon : Erreur lors de la récupération de l'icône {art_id}: {e}")
            return None


# Instancie le fournisseur d'art. Il est recommandé d'utiliser un singleton.
art_provider_tk = ArtProviderTk()


class ArtProvider:  # Plus de wx.ArtProvider, c'est une classe utilitaire maintenant
    """Fournisseur d'art pour tkinter, gérant la création et la superposition d'images.

    Cette classe permet de charger des icônes simples ou composées
    (icône principale + icône overlay) en utilisant PIL pour les
    manipulations d'image, puis en retournant une PhotoImage utilisable
    par tkinter."""
    # def CreateBitmap(self, artId, artClient, size):
    def CreateBitmap(self, artId, size=(16, 16)):
        """
        Crée une icône tkinter.PhotoImage à partir d'un identifiant d'art.

        Si l'identifiant contient '+', une image overlay est superposée
        dans le coin inférieur droit de l'image principale.

        Args:
            artId (str): Identifiant de l'icône (ex: "icon" ou "icon+overlay")
            size (tuple): Taille finale de l'icône (largeur, hauteur)

        Returns:
            ImageTk.PhotoImage ou None
        """
        # Extraction de la largeur et de la hauteur demandées
        w, h = size

        # Cas d'une icône composée (ex: "main+overlay")
        if "+" in artId:
            # Séparation des deux identifiants
            main_id, overlay_id = artId.split("+")
            log.debug(
                "ArtProvider.CreateBitmap : essaie de créer "
                f"{main_id}+{overlay_id} de taille ({w}, {h})."
            )

            # Chargement de l'icône principale (PhotoImage tkinter)
            # main_image_pil = self._CreateBitmap(main_id, artClient, size)
            main_photoicon = IconProvider().getIcon(main_id, size)

            # Vérification que l'image principale existe
            if not main_photoicon:
                log.error("L'image principale est vide.")
                return None  # Retourne None si l'image principale n'est pas trouvée

            # Conversion immédiate en PIL.Image
            main_image_pil = ImageTk.getimage(main_photoicon).convert("RGBA")

            # Charger l'image de superposition overlay (PhotoImage tkinter)
            overlay_photoicon = IconProvider().getIcon(overlay_id, size)

            # Si l'overlay n'existe pas, on retourne l'image principale seule
            if not overlay_photoicon:
                log.error("L'image overlay non trouvée, retour de l'image principale.")
                return ImageTk.PhotoImage(main_image_pil)  # Retourne l'image principale seule si l'overlay n'est pas trouvé

            # # # 3. Convertir l'overlay (PhotoImage) en image PIL
            overlay_image_pil = ImageTk.getimage(overlay_photoicon).convert("RGBA")

            # Redimensionner l'image de superposition (moitié de la taille)
            overlay_image_pil = overlay_image_pil.resize(
                (w // 2, h // 2),  # Nouvelle taille
                Image.LANCZOS      # Filtre de haute qualité
            )

            # Calculer la position pour le coin inférieur droit
            x_offset = w - overlay_image_pil.width
            y_offset = h - overlay_image_pil.height

            # Superposer l'image de superposition sur l'image principale
            # avec gestion de la transparence
            main_image_pil.paste(
                overlay_image_pil,                # Image à coller
                (x_offset, y_offset),        # Position
                overlay_image_pil                 # Masque alpha
            )

            # Convertir finale de l'image PIL en PhotoImage de tkinter
            return ImageTk.PhotoImage(main_image_pil)
        # Cas d'une icône simple
        elif artId:
            # Charger une image simple directement depuis l'IconProvider
            photo = IconProvider().getIcon(artId, size)

            # # Si l'icône existe, on la retourne telle quel
            if not photo:
                return None  # Icône absente

            # Conversion propre en PIL puis retour en PhotoImage
            pil_image = ImageTk.getimage(photo).convert("RGBA")
            return ImageTk.PhotoImage(pil_image)

        # Aucun artId valide
        return None  # Retourne None si l'image n'est pas trouvée

    @staticmethod
    def convertAlphaToMask(image_tk):
        """Convertit un PhotoImage de tkinter en Image PIL, puis applique un masque alpha."""
        # Pour tkinter, PhotoImage gère déjà la transparence.
        # Cette fonction est principalement pour la compatibilité conceptuelle.
        # Si image_tk est un PhotoImage, on peut tenter de le convertir en PIL Image
        if isinstance(image_tk, ImageTk.PhotoImage):
            # C'est une simplification, car convertir PhotoImage en PIL Image n'est pas direct
            # sans la source originale. Pour cet exemple, nous allons simuler.
            # Dans une vraie application, vous chargeriez l'image originale avec PIL.
            log.warning("convertAlphaToMask est appelée sur un PhotoImage. La conversion directe n'est pas supportée.")
            # On retourne l'image telle quelle ou une version modifiée si on a la source PIL.
            # Pour l'instant, on simule en créant une image PIL simple.
            img_pil = Image.new('RGBA', (image_tk.width(), image_tk.height()), (255, 255, 255, 255))
            # Si l'image a un canal alpha, on peut le manipuler ici.
            # Par exemple, pour rendre le blanc transparent:
            # img_pil = img_pil.convert("RGBA")
            # datas = img_pil.getdata()
            # newData = []
            # for item in datas:
            #     if item[0] == 255 and item[1] == 255 and item[2] == 255:
            #         newData.append((255, 255, 255, 0))
            #     else:
            #         newData.append(item)
            # img_pil.putdata(newData)
            return ImageTk.PhotoImage(img_pil)
        return image_tk  # Retourne l'objet tel quel si ce n'est pas un PhotoImage


class IconProvider(object, metaclass=patterns.Singleton):
    """Singleton gérant un cache d'icônes pour éviter les fuites de mémoire.
    Fournit des icônes dans différentes tailles pour divers usages (boutons, menus, etc.).
    """

    def __init__(self):
        """Initialise l'ArtProvider avec certaines options spécifiques à la plateforme."""
        self.__iconCache = {}
        if operating_system.isMac():
            self.__iconSizeOnCurrentPlatform = 128
        elif operating_system.isGTK():
            self.__iconSizeOnCurrentPlatform = 48
        else:
            self.__iconSizeOnCurrentPlatform = 16
        self.art_provider = ArtProvider()  # Instancier notre ArtProvider pour tkinter

        # Cache pour les icônes de taille non standard (à ajouter si ce n'est pas fait)
        self._icon_cache_by_size = {}

    # def getIcon(self, iconTitle):
    #     """Renvoie l'icône. Utilise un cache pour optimiser la gestion mémoire."""
    #     try:
    #         return self.__iconCache[iconTitle]
    #     # except KeyError:
    #     except KeyError:
    #         icon = self.getIconFromArtProvider(iconTitle)
    #         self.__iconCache[iconTitle] = icon
    #         return icon

    # def getIcon(self, iconTitle: str, size: Tuple[int, int] = (16, 16)) -> Optional[ImageTk.PhotoImage]:
    #     """
    #     Récupère un objet PhotoImage à partir du catalogue d'icônes intégré,
    #     en s'assurant qu'il est mis à la bonne taille et mis en cache.
    #
    #     Cherche l'icône par son titre et sa taille souhaitée, en adaptant
    #     le titre du style wxPython (ex: 'arrow_down_icon') à la clé du catalogue
    #     icons.py (ex: 'arrow_down16x16').
    #     """
    #
    #     # 1. Utiliser le cache
    #     icon_key = (iconTitle, size)
    #     if icon_key in self.__iconCache:
    #         return self.__iconCache[icon_key]
    #
    #     # La demande est faite avec un suffixe _icon (ex: 'arrow_down_icon'),
    #     # mais le catalogue utilise peut-être un nom sans ce suffixe.
    #
    #     # 1. Tenter avec le titre original
    #     title_in_catalog = iconTitle
    #
    #     # 2. Si non trouvé, essayer de retirer le suffixe commun '_icon'
    #     if title_in_catalog not in icons_tk.catalog and iconTitle.endswith('_icon'): #
    #         # Dériver le nom sans le suffixe pour le catalogue (ex: 'arrow_down')
    #         title_in_catalog = iconTitle.removesuffix('_icon')
    #
    #         # Si le suffixe 'icon' est présent (ex: 'note_icon'), essayer sans.
    #         if title_in_catalog.endswith('icon'):
    #             title_in_catalog = title_in_catalog.removesuffix('icon')
    #
    #         # Nettoyage supplémentaire pour les titres qui pourraient encore avoir un suffixe indésirable (rare)
    #         if title_in_catalog.endswith('_'):
    #             title_in_catalog = title_in_catalog.removesuffix('_')
    #
    #     # 3. Vérifier dans le catalogue avec le titre ajusté
    #     if title_in_catalog in icons_tk.catalog: #
    #         # On utilise le titre ajusté pour trouver l'image de base
    #         return self._getIconForSize(title_in_catalog, size)
    #
    #     # 2. Tenter de charger l'image depuis le catalogue (icons.py)
    #     if iconTitle in icons_tk.catalog:
    #         # mock_image_obj est une instance de PyEmbeddedImageTk
    #         mock_image_obj = icons_tk.catalog[iconTitle]
    #
    #         # Utilise la méthode GetImage() pour récupérer l'objet PIL
    #         image_pil = mock_image_obj.GetImage()
    #
    #         # Mise à l'échelle si nécessaire (car Tkinter nécessite une taille exacte)
    #         if image_pil.size != size:
    #             # Utilise Image.Resampling.LANCZOS pour la qualité, si PIL est récent
    #             resample_method = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
    #             image_pil = image_pil.resize(size, resample=resample_method)
    #
    #         # Créer l'objet PhotoImage (celui qui peut être utilisé par Tkinter)
    #         photo_image = ImageTk.PhotoImage(image_pil)
    #
    #         # Mettre en cache la nouvelle icône
    #         self.__iconCache[icon_key] = photo_image
    #
    #         return photo_image
    #
    #     log.warning(f"Image non trouvée dans le catalogue pour l'ID: {iconTitle} et la taille: {size}")
    #     return None

    def getIcon(self, iconTitle, desired_size=(16, 16)):
        """
        Cherche l'icône par son titre et sa taille souhaitée, en adaptant
        le titre du style wxPython (ex: 'arrow_down_icon') à la clé du catalogue
        icons.py (ex: 'arrow_down16x16').
        """
        if "+" in iconTitle:
            return ArtProvider().CreateBitmap(iconTitle, desired_size)

        # Formater la taille en suffixe pour le catalogue (ex: '16x16')
        size_suffix = f"{desired_size[0]}x{desired_size[1]}"

        # Le nom demandé a souvent le suffixe '_icon'.
        # base_title = iconTitle.removesuffix('_icon')
        base_title = iconTitle

        # # Si le nom de base se termine par 'icon' (ex: 'clock_icon' -> 'clock_icon'), le retirer aussi
        # if base_title.endswith('icon'):
        #     base_title = base_title.removesuffix('icon')

        # Si le nom de base se termine par '_' (ex: 'led_blue_light_' après nettoyage)
        if base_title.endswith('_'):
            base_title = base_title.removesuffix('_')

        # Construire la clé finale du catalogue (ex: 'arrow_down' + '16x16' = 'arrow_down16x16')
        catalog_key = f"{base_title}{size_suffix}"

        # 1. Tenter de récupérer l'icône mise en cache par la taille
        # (Cette partie suppose que vous avez une logique de mise en cache
        # pour les icônes redimensionnées, si vous l'avez implémentée).
        # Pour le test initial, on se concentre sur la recherche dans icons.catalog.

        # 2. Vérifier dans le catalogue
        if catalog_key in icons_tk.catalog:
            # L'image de base (PyEmbeddedImageTk) est trouvée.
            embedded_image = icons_tk.catalog[catalog_key]

            # Utiliser la méthode qui gère le redimensionnement/conversion en PhotoImage
            return self._getIconForSize(embedded_image, desired_size)

        # Pour assurer la compatibilité au cas où l'ID est la clé directe (moins probable)
        if iconTitle in icons_tk.catalog:
            embedded_image = icons_tk.catalog[iconTitle]
            return self._getIconForSize(embedded_image, desired_size)

        # 3. Échec : journaliser l'avertissement et retourner None.
        logging.warning("Image non trouvée dans le catalogue pour l'ID: %s et la taille: %s (Clé de recherche: %s)",
                        iconTitle, desired_size, catalog_key)
        return None

    def iconBundle(self, iconTitle):
        """Crée un groupe d'icônes avec des icônes de différentes tailles."""
        # Tkinter n'a pas de concept direct de "IconBundle" comme wxPython.
        # On peut retourner un dictionnaire ou une liste de PhotoImage.
        bundle = {}
        for size in (16, 22, 32, 48, 64, 128):
            icon_img = self.getIconFromArtProvider(iconTitle, size)
            if icon_img:
                bundle[size] = icon_img
        return bundle

    def getIconFromArtProvider(self, iconTitle, iconSize=None):
        size = iconSize or self.__iconSizeOnCurrentPlatform
        # ArtProvider.CreateBitmap retourne déjà un ImageTk.PhotoImage
        # ou une Image PIL qui doit être convertie.
        img_or_photoimage = self.art_provider.CreateBitmap(iconTitle, "ART_FRAME_ICON", (size, size))

        if isinstance(img_or_photoimage, ImageTk.PhotoImage):
            return img_or_photoimage
        elif isinstance(img_or_photoimage, Image.Image):
            return ImageTk.PhotoImage(img_or_photoimage)
        return None

    # N'oubliez pas que vous devez également définir ou vous assurer que la méthode
    # _getIconForSize est correctement définie dans ArtProvider (elle prend
    # le PyEmbeddedImageTk et la taille, et retourne un ImageTk.PhotoImage) :

    def _getIconForSize(self, embedded_image, desired_size):
        """
        Prend une instance de PyEmbeddedImageTk et retourne un ImageTk.PhotoImage
        de la taille désirée, en gérant le redimensionnement si nécessaire.
        """
        # Obtenez l'objet PIL Image.
        pil_image = embedded_image.GetImage()

        # Définir la taille de l'image de base
        original_size = pil_image.size

        # Vérifiez si le redimensionnement est nécessaire
        if original_size != desired_size:
            # Redimensionner l'image PIL en utilisant un filtre de bonne qualité
            pil_image = pil_image.resize(desired_size, Image.Resampling.LANCZOS)

        # Convertir l'image PIL en PhotoImage de Tkinter
        photo_image = ImageTk.PhotoImage(pil_image)

        # Important : Stocker la référence dans un cache pour éviter que le garbage collector
        # de Python ne supprime l'image si elle n'est pas attachée immédiatement à un widget.
        # Vous devrez avoir une structure de cache dans votre classe IconProvider
        # (par exemple, self._icon_cache = {}). Pour la simplicité ici,
        # je suppose que l'appelant gère la référence.

        return photo_image


def iconBundle(iconTitle):
    """Crée un groupe d'icônes à partir d'un titre d'icône, avec plusieurs tailles pour différentes résolutions."""
    return IconProvider().iconBundle(iconTitle)


# def getIcon(iconTitle):
#     return IconProvider().getIcon(iconTitle)
# Remplacer la ligne : return IconProvider().getIcon(iconTitle)
# par un appel complet qui inclut la taille si nécessaire dans le wrapper principal
def getIcon(iconTitle: str, desired_size: Optional[Tuple[int, int]] = None) -> Optional[ImageTk.PhotoImage]:
    """Renvoie l'icône correspondant au titre donné, en utilisant un cache pour optimiser la gestion mémoire."""
    return IconProvider().getIcon(iconTitle, desired_size or (16, 16))


def init():
    """Initialise l'ArtProvider avec certaines options spécifiques à la plateforme."""
    # Les options système wx.SystemOptions n'ont pas d'équivalent direct dans tkinter.
    # Ces lignes sont donc commentées ou supprimées.
    # if operating_system.isWindows() and wx.DisplayDepth() >= 32:
    #     wx.SystemOptions.SetOption("msw.remap", "0")
    # if operating_system.isGTK():
    #     wx.SystemOptions.SetOption("gtk.desktop", "1")

    # Il n'y a pas de pile d'ArtProvider dans tkinter. L'instance de ArtProvider
    # est gérée directement par IconProvider.
    # Cette fonction init peut être utilisée pour s'assurer que l'IconProvider est instancié.
    _ = IconProvider()  # Juste pour s'assurer que l'instance singleton est créée


# Dictionnaire des images sélectionnables (inchangé, car ce sont des chaînes de caractères)
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


# Démonstration et tests
if __name__ == '__main__':
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageTk

    # Fonction pour créer une fenêtre de démonstration
    def run_demo():
        root = tk.Tk()
        root.title("Démonstration ArtProviderTk")
        root.geometry("400x300")

        frame = ttk.Frame(root, padding="10")
        frame.pack(fill="both", expand=True)

        label_title = ttk.Label(frame, text="Icônes chargées via ArtProviderTk", font=("Helvetica", 16))
        label_title.pack(pady=10)

        # Tester le chargement d'une icône de taille standard (16x16)
        # icon_copy_16 = art_provider_tk.GetIcon('copy16x16')
        # icon_copy_16 = art_provider_tk.GetIcon('copy')
        icon_copy_16 = getIcon('copy')
        if icon_copy_16:
            label_copy_16 = ttk.Label(frame, text="copy16x16", image=icon_copy_16, compound="left")
            label_copy_16.image = icon_copy_16  # Garde une référence pour éviter la suppression par le garbage collector
            label_copy_16.pack(pady=5)

        # Tester le chargement d'une icône de taille différente (mise à l'échelle)
        # icon_copy_32 = art_provider_tk.GetIcon('copy16x16', desired_size=(32, 32))
        # icon_copy_32 = art_provider_tk.GetIcon('copy', desired_size=(32, 32))
        icon_copy_32 = getIcon('copy', desired_size=(32, 32))
        if icon_copy_32:
            label_copy_32 = ttk.Label(frame, text="copy16x16 redimensionnée à 32x32", image=icon_copy_32, compound="left")
            label_copy_32.image = icon_copy_32
            label_copy_32.pack(pady=5)

        # Tester une icône inexistante
        # icon_non_existent = art_provider_tk.GetIcon('non_existent_icon')
        icon_non_existent = getIcon('non_existent_icon')
        if not icon_non_existent:
            label_non_existent = ttk.Label(frame, text="Icone 'non_existent_icon' non trouvée (c'est normal)")
            label_non_existent.pack(pady=5)

        # Utilisation d'une fonction de tkhelper pour la démonstration
        # Notez que la logique de tkhelper est différente et doit être utilisée comme tel.
        # Par exemple, nous n'avons pas besoin de get_button_from_frame_by_id ici
        # car c'est une fonction utilitaire pour la gestion de l'interface utilisateur.

        root.mainloop()

    run_demo()
