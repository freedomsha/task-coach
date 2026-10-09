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
# Selon chatGPT :
# Ce module est une implémentation classique d'un Singleton en utilisant une métaclass en Python.
# Il semble fonctionner correctement en Python 3, mais il y a quelques points à noter :
#
#     Gestion de l'instanciation :
#     La méthode __call__ de la métaclass est utilisée pour contrôler le processus d'instanciation.
#     Si aucune instance n'a été créée, une nouvelle instance est créée à l'aide de super().__call__().
#     Sinon, l'instance existante est renvoyée.
#
#     Suppression de l'instance :
#     La méthode deleteInstance est fournie pour supprimer explicitement l'instance unique.
#     Cela peut être utile dans certains cas, par exemple pour les tests unitaires.
#
#     Vérification de l'instance : La méthode hasInstance est fournie pour vérifier si une instance a déjà été créée.
#
#     Gestion des exceptions :
#     Le code utilise pylint: disable=W0201 pour désactiver l'avertissement concernant l'assignation
#     directe à class_.instance. Cela est fait car instance est normalement considéré comme une variable d'instance,
#     mais dans ce cas, il est utilisé comme un attribut de classe.
#
# Dans l'ensemble, cette implémentation semble propre et fonctionnelle.
# Cependant, comme pour toute utilisation de Singleton,
# assurez-vous qu'elle correspond à la conception de votre application et évitez les abus de cette conception,
# car les Singletons peuvent entraîner des problèmes de test et de maintenabilité à grande échelle.

# Pour améliorer la métaclass Singleton :
#
#     Compatibilité avec les sous-classes :
#     Actuellement, la métaclass Singleton ne gère qu'une seule instance pour chaque classe.
#     Si une classe a des sous-classes et que vous voulez que chaque sous-classe ait sa propre instance unique,
#     vous devrez ajuster la logique de la métaclass en conséquence.
#
#     Gestion des exceptions :
#     Évitez de désactiver les avertissements avec pylint: disable=W0201.
#     Au lieu de cela, vous pouvez utiliser une approche différente pour éviter cet avertissement
#     ou désactiver l'avertissement localement autour du code concerné.
#
#     Méthodes de classe :
#     Ajoutez des méthodes de classe pour créer et supprimer l'instance unique,
#     plutôt que d'accéder directement à __dict__ de la classe.
#     Cela rendra l'API plus explicite et plus facile à utiliser.
#
#     Gestion des arguments :
#     Ajoutez une gestion d'arguments plus robuste pour la méthode __call__,
#     en passant les arguments reçus à la méthode __call__ de la classe de base.
#     Cela permettrait de prendre en charge l'instanciation avec des arguments.


class Singleton(type):
    """ A metaclass that ensures that only one instance of a class is ever created.

    Singleton metaclass. Use by defining the metaclass of a class Singleton,
        e.g.: class ThereCanBeOnlyOne(metaclass=Singleton):
                  # ...
    """
    # Métaclasse Singleton. A utiliser en définissant la métaclasse d'une classe Singleton,
    #         par exemple: class IlNePeutYEnAvoirQuUn(metaclass=Singleton):

    # def __call__(class_, *args, **kwargs):
    # la classe Signgleton est appelée comme une fonction
    # fau-il la remplacer par __new__ ?

    _instance = None

    def __call__(cls, *args, **kwargs):
        """Create a new instance of the class if none exists, otherwise return the existing instance."""
        # if not cls.hasInstance():
        #    # pylint: disable=W0201
        #    # cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        #     cls.instance = super().__call__(*args, **kwargs)
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

    # def deleteInstance(class_):
    # @classmethod
    def deleteInstance(cls):
        """ Delete the (only) instance of the class.

        Delete the (only) instance. This method is mainly for unittests so
            they can start with a clean slate.

        """
        # Supprimez l' (unique) instance. Cette méthode est principalement destinée aux tests unitaires
        # afin qu'ils puissent commencer avec une table rase.
        # if cls.hasInstance():
        if cls._instance is not None:
            del cls._instance

    # def hasInstance(class_):
    # @classmethod
    def hasInstance(cls):
        """ Check if an instance of the class has been created.

        Has the (only) instance been created already? """
        # La (seule) instance a-t-elle déjà été créée ?
        return 'instance' in cls.__dict__
        # return cls._instance is not None

