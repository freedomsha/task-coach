"""
Task Coach - Your friendly task manager
Copyright (C) 2012 Task Coach developers <developers@taskcoach.org>

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


# No way to monkey-patch this unfortunately...

def ExceptionAsUnicode(e):
    """
    Convertit une exception en une chaîne de caractères Unicode.

    Cette fonction essaie de convertir les arguments de l'exception en Unicode.
    Si un argument ne peut pas être converti en Unicode, il est alors converti
    en chaîne de caractères standard et ajouté à la sortie.

    Args :
        e (Exception) : L'exception à convertir en chaîne de caractères Unicode.

    Returns :
        str : Une représentation Unicode de l'exception.
    """
    try:
        #     return unicode(e)
        # except NameError:
        return str(e)
    except UnicodeDecodeError:
        components = list()
        for arg in e.args:
            if isinstance(arg, str):
                try:
                    # components.append(arg.decode("utf-8"))
                    # Unresolved attribute reference 'decode' for class 'str'
                    components.append(arg.encode("utf-8"))
                except UnicodeDecodeError:
                    try:
                        # components.append(arg.decode("iso-8859-15"))
                        # Unresolved attribute reference 'decode' for class 'str'
                        components.append(arg.encode("iso-8859-15"))
                    except UnicodeDecodeError:
                        components.append(repr(arg))
            else:
                components.append(str(arg))
        # return "%s: %s" % (e.__class__.__name__, " - ".join(components))
        return f"{e.__class__.__name__}: {' - '.join(components)}"
