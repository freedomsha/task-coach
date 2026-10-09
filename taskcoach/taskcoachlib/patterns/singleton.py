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
import logging

log = logging.getLogger(__name__)


class Singleton(type):
    """Métaclasse Singleton. À utiliser en définissant la métaclasse d'une classe Singleton,
    par exemple : class ThereCanBeOnlyOne(metaclass=Singleton).
    """

    def __call__(class_, *args, **kwargs):
        """
        Appelée lorsque l'instance est "appelée" en fonction;
        si cette méthode est définie,
        x(arg1, arg2, ...) se traduit grossièrement par type(x).__call__(x, arg1, ...).
        La classe object elle-même ne fournit pas cette méthode.

        Args :
            *args: Liste d'arguments de longueur variable.
            **kwargs: Arguments de mots clés arbitraires.

        Returns :

        """
        if not class_.hasInstance():
            # pylint: disable=W0201
            class_.instance = super().__call__(*args, **kwargs)
        # log.debug(f"Singleton.__call__ : retourne la classe instanciée {class_.instance.__class__.__name__}")  # !!! Crée une boucle !!!
        return class_.instance

    def deleteInstance(class_):
        """Supprimez la (unique) instance. Cette méthode est principalement destinée aux tests unitaires afin
        qu'ils puissent commencer avec une table rase."""
        if class_.hasInstance():
            del class_.instance

    # def hasInstance(class_) -> bool:
    def hasInstance(class_):
        """La (seule) instance a-t-elle déjà été créée ?"""
        return "instance" in class_.__dict__
