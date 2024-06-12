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
    A class to parse and manage command-line arguments for the Task Coach application.

    This class uses `argparse.ArgumentParser`
    to define and handle the command-line options available to the user.

    Attributes:
        parser (argparse.ArgumentParser): The argument parser instance
        used to handle command-line options.

    Methods:
        __init__(self, *args, **kwargs): Initializes the argument parser
        with custom usage information.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the argument parser with custom usage information.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Sets:
            kwargs["usage"] (str): Custom usage message describing
            the program's usage.
        """
        kwargs["usage"] = "usage='%(prog)s [options] [.tsk file]'"
        # super().__init__(*args, **kwargs)

    # Initialize the ArgumentParser with a description
    parser = argparse.ArgumentParser(description="Your friendly task manager")

    # Define the command-line arguments
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


#    parser.add_argument("args", help="Name of .tsk File to open.")
