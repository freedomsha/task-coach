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

Ce fichier Python définit des dictionnaires pour gérer les noms d'icônes singuliers et pluriels dans Task Coach.

Fonctionnalités principales
    Dictionnaires d'icônes :
        itemImagePlural: Associe les noms d'icônes singuliers à leurs équivalents pluriels.
        itemImageOpen: Associe les noms d'icônes fermées à leurs équivalents ouverts.
        itemImageSingular: Inverse du dictionnaire itemImagePlural.
    Fonctions utilitaires :
        getImageOpen(name) : Renvoie le nom de l'icône ouverte correspondant à un nom d'icône fermée.
        getImagePlural(name) : Renvoie le nom de l'icône plurielle correspondant à un nom d'icône singulier.

Exemple d'utilisation
Python

# Pour obtenir le nom de l'icône plurielle pour "book_icon" :
plural_name = getImagePlural("book_icon")  # Renvoie "books_icon"

# Pour obtenir le nom de l'icône ouverte pour "folder_blue_icon" :
open_name = getImageOpen("folder_blue_icon")  # Renvoie "folder_blue_open_icon"

Utilisez ce code avec précaution.

Remarques
    Les dictionnaires d'icônes sont utilisés pour gérer la cohérence des noms d'icônes dans différentes situations (singulier, pluriel, ouvert, fermé).
    Les fonctions utilitaires permettent d'obtenir facilement le nom d'icône approprié en fonction du contexte.

Ce fichier joue un rôle important dans la gestion cohérente des icônes dans l'application Task Coach, en assurant que les icônes appropriées sont utilisées en fonction du nombre d'éléments affichés et de leur état (ouvert ou fermé).
"""

# Dictionnaires d'icônes :
# Associe les noms d'icônes singuliers à leurs équivalents pluriels:
itemImagePlural = dict(
    book_icon="books_icon",
    cogwheel_icon="cogwheels_icon",
    envelope_icon="envelopes_icon",
    heart_icon="hearts_icon",
    key_icon="keys_icon",
    led_blue_icon="folder_blue_icon",
    led_blue_light_icon="folder_blue_light_icon",
    led_grey_icon="folder_grey_icon",
    led_green_icon="folder_green_icon",
    led_orange_icon="folder_orange_icon",
    led_purple_icon="folder_purple_icon",
    led_red_icon="folder_red_icon",
    led_yellow_icon="folder_yellow_icon",
    checkmark_green_icon="checkmark_green_icon_multiple",
    person_icon="persons_icon",
)


# Associe les noms d'icônes fermées à leurs équivalents ouverts.
itemImageOpen = dict()
for _color in ["blue", "grey", "green", "orange", "purple", "red", "yellow"]:
    # itemImageOpen["folder_%s_icon" % _color] = "folder_%s_open_icon" % _color
    itemImageOpen[f"folder_{_color}_icon"] = f"folder_{_color}_open_icon"


def getImageOpen(name):
    """Renvoie le nom de l'icône ouverte correspondant à un nom d'icône fermée."""
    return itemImageOpen.get(name, name)


# Inverse du dictionnaire itemImagePlural.
itemImageSingular = dict()
for key, value in itemImagePlural.items():
    # for key, value in list(itemImagePlural.items()):
    itemImageSingular[value] = key


def getImagePlural(name):
    """Renvoie le nom de l'icône plurielle correspondant à un nom d'icône singulier."""
    return itemImagePlural.get(name, name)
