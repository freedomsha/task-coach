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

import argparse
from taskcoachlib import meta


class ApplicationArgumentParser:
    """
    Une fonction pour analyser et gérer les arguments de ligne de commande pour l'application Task Coach.

    Cette fonction utilise `argparse.ArgumentParser`
    pour définir et gérer les options de ligne de commande disponibles pour l'utilisateur.

    Attributs :
        analyseur (argparse.ArgumentParser) : instance de l'analyseur d'arguments
        utilisée pour gérer les options de ligne de commande.

    Methods :
        __init__(self, *args, ** kwargs) : initialise l'analyseur d'arguments
        avec des informations d'utilisation personnalisées.
    """

    def __init__(self, *args, **kwargs):
        """
            Initialisez l'analyseur d'arguments avec des informations d'utilisation personnalisées.

            Args :
                *args : liste d'arguments de longueur variable.
                **kwargs : arguments de mots clés arbitraires.

            Sets :
                kwargs["usage"] (str) : message d'utilisation personnalisé décrivant
                l'utilisation du programme.
        """
        # kwargs["usage"] = "usage='%(prog)s [options] [.tsk file]'"
        # super().__init__(*args, **kwargs)
        pass

    # Initialisez l'ArgumentParser avec une description
    parser = argparse.ArgumentParser(usage="%(prog)s [options] [.tsk file]", description="Your friendly task manager")

    # Définir les arguments de la ligne de commande
    parser.add_argument(
        "--version",
        action="version",
        version=f"This version : {meta.data.name} {meta.data.version}",
        help="Show program's version number and exit.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        default=False,
        help="Enable profiling of the application.",
    )
    parser.add_argument(
        "-s",
        "--skipstart",
        default=False,
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-i",
        "--ini",
        dest="inifile",
        help="Use the specified INIFILE for storing settings.",
    )
    parser.add_argument(
        "-l",
        "--language",
        nargs=1,
        dest="language",
        type=str,
        choices=sorted(
            [
                lang
                for (lang, enabled) in meta.data.languages.values()
                if lang is not None
            ]
            + ["en"]
        ),
        help='Use the specified LANGUAGE for the GUI (e.g. "nl" or "fr").',
    )
    parser.add_argument(
        "-p",
        "--po",
        nargs=1,
        dest="pofile",
        help="Use the specified POFILE for translation of the GUI.",
    )
