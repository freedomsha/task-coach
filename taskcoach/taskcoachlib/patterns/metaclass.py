"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2021 Task Coach developers <developers@taskcoach.org>

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
# Selon ChatGPT:
# Ce module semble fonctionner correctement en Python 3. Cependant, il y a quelques points à noter :
#
#     Dépendance implicite de l'ordre d'instanciation :
#     Ce module suppose que les instances sont créées dans un ordre séquentiel.
#     Cela signifie que si les instances sont créées de manière non séquentielle,
#     le comportement de lowestUnusedNumber peut être imprévisible.
#
#     Compatibilité avec les classes existantes :
#     L'utilisation de cette métaclass affectera toutes les sous-classes de la classe où elle est utilisée.
#     Assurez-vous que cela correspond à l'intention de votre conception.
#
#     Utilisation de weakref.WeakKeyDictionary :
#     Cela garantit que les instances sont nettoyées de la mémoire lorsqu'elles ne sont plus utilisées,
#     ce qui est une bonne pratique pour éviter les fuites de mémoire.
#
#     Compatibilité avec d'autres métaclasses :
#     Comme toute métaclass, cela ne fonctionnera pas avec d'autres métaclasses incompatibles.
#
#     Conception du code :
#     Le code est bien documenté et semble être une implémentation valide d'une métaclass.
#     Cependant, assurez-vous de tester minutieusement son comportement dans votre application
#     pour vous assurer qu'il fonctionne comme prévu dans votre cas d'utilisation spécifique.
#
# Dans l'ensemble, si ce module répond à vos besoins et fonctionne comme prévu dans votre application,
# vous pouvez l'utiliser en toute confiance en Python 3.

# Pour améliorer le module de métaclasses NumberedInstances :
#
#     Utilisation d'un dictionnaire par classe :
#     Actuellement, NumberedInstances.count utilise un dictionnaire partagé pour toutes les classes.
#     Cela peut entraîner des problèmes si plusieurs classes utilisent cette métaclass.
#     Il serait préférable d'utiliser un dictionnaire distinct pour chaque classe en utilisant les attributs de classe.
#
#     Utilisation d'un compteur global :
#     Plutôt que de rechercher le plus bas numéro non utilisé à chaque instantiation,
#     vous pouvez simplement utiliser un compteur global qui incrémente à chaque création d'instance.
#     Cela simplifierait la logique de lowestUnusedNumber.
#
#     Tests unitaires :
#     Ajoutez des tests unitaires pour vérifier le comportement de la métaclass dans différentes situations,
#     en particulier pour vérifier que les numéros d'instance sont uniques et qu'ils sont attribués correctement.

# Module pour les métaclasses qui ne sont pas des modèles largement reconnus.
import weakref


class NumberedInstances(type):
    """ Une métaclasse qui numérote les instances de classe.

    À utiliser en définissant la métaclasse d'une classe NumberedInstances, par exemple :
        class Numbered (metaclass=NumberedInstances) :
            # ...
        Chaque instance de la classe Numbered aura un attribut instanceNumber unique.
        """

    # Attribut de classe count est un dictionnaire
    count = dict()
    # count: dict[<type>, <type>] = ...

    # ChatGPT ajoute __init__
    # def __init__(cls, name, bases, dct):
    #     """Initialise la classe avec un nombre d'instances unique."""
    #     super().__init__(name, bases, dct)
    #     cls._instance_count = 0
    #     print(f"tclib.patterns.metaclass.py NumberedInstances.__init__: initialise class = {cls} à _instance_count: {cls._instance_count}")  # Ajout de journalisation

    # Vieux code
    def __call__(cls, *args, **kwargs):
        """Créez une nouvelle instance de la classe avec un numéro d'instance unique.

        Crée les attributs NumberedInstances.count[cls] et NumberedInstances.count[cls][instance],
         instanceNumber et kwargs['instanceNumber']
        Renvois la fonction super instance.

        """
        # Si (l'objet)la classe n'est pas dans le dictionnaire de classe
        if cls not in NumberedInstances.count:
            # le créer en temps que référence faible
            # https://docs.python.org/fr/3/library/weakref.html
            NumberedInstances.count[cls] = weakref.WeakKeyDictionary()
        # l'attribut nombre d'instance est (méthode) le dernier nombre inutilisé pour (l'objet)la classe
        instanceNumber = NumberedInstances.lowestUnusedNumber(cls)
        # L'argument-Attribut dictionnaire kwargs devient le nombre d'instance
        kwargs["instanceNumber"] = instanceNumber
        # L'attribut instance devient un appel à super
        # https://www.stashofcode.fr/comment-marche-fonction-super-de-python/
        # Comprendre comment super () fonctionne, permet donc de s'assurer quelle implémentation d'une méthode
        # doit être utilisée à chaque étage d'une hiérarchie où elle est surchargée.
        instance = super(NumberedInstances, cls).__call__(*args, **kwargs)
        # remplacé par:
        # instance = super().__call__(*args, **kwargs)
        # L'attribut de classe compteur d'instance de l'objet(la classe) devient le nombre d'instance
        NumberedInstances.count[cls][instance] = instanceNumber
        # Renvoie la fonction super instance
        return instance
        # Nouveau code
        # # def __new__(cls, *args, **kwargs):
        # # à remplacer par __new__() ?
        # # if cls not in NumberedInstances.count:
        # #    NumberedInstances.count[cls] = weakref.WeakKeyDictionary()
        # # instanceNumber = NumberedInstances.lowestUnusedNumber(cls)
        # # kwargs['instanceNumber'] = instanceNumber
        # # instance = super().__call__(*args, **kwargs)
        # # NumberedInstances.count[cls][instance] = instanceNumber
        # instance = super().__call__(*args, **kwargs)
        # instance.instanceNumber = cls._instance_count
        # kwargs['instanceNumber'] = instance.instanceNumber
        # cls._instance_count += 1
        # return instance

    # Vieux code
    def lowestUnusedNumber(cls):
        # def lowestUnusedNumber(cls) -> int:
        """Méthode qui renvoie le plus bas numéro d'instance inutilisé pour la classe.
        """
        # vieux code
        # L'attribut Numéros utilisés est la liste des valeurs du dictionnaire de classe de l'objet(classe).
        usedNumbers = sorted(NumberedInstances.count[cls].values())
        # pour chaque index et numéro utilisé dans les numéros utilisés
        for index, usedNumber in enumerate(usedNumbers):
            # si le numéro utilisé est différent de l'index
            if usedNumber != index:
                # renvoyer l'index
                return index
        # sinon renvoyer le nombre de numéros utilisés
        return len(usedNumbers)

        # nouveau code
        # nombres utilisés = liste des valeurs du dictionnaire des classes de NumberedInstances
        # usedNumbers = sorted(NumberedInstances.count[cls].values())
        # #
        # for index, usedNumber in enumerate(usedNumbers):
        #     if usedNumber != index:
        #         return index
        # return len(usedNumbers)


metadic = {}
# metadic: dict[<type>, <type>] = ...


def _generatemetaclass(bases, metas, priority):
    trivial = lambda m: sum([issubclass(M, m) for M in metas], m is type)
    # hackish!! m is trivial if it is 'type' or, in the case explicit
    # metaclasses are given, if it is a superclass of at least one of them
    metabs = tuple([mb for mb in map(type, bases) if not trivial(mb)])
    metabases = (metabs + metas, metas + metabs)[priority]
    if metabases in metadic:  # already generated metaclass
        return metadic[metabases]
    elif not metabases:  # trivial metabase
        meta = type
    elif len(metabases) == 1:  # single metabase
        meta = metabases[0]
    else:  # multiple metabases
        metaname = "_" + "".join([m.__name__ for m in metabases])
        meta = makecls()(metaname, metabases, {})
    return metadic.setdefault(metabases, meta)


def makecls(*metas, **options):
    """Class factory avoiding metatype conflicts. The invocation syntax is
    makecls(M1,M2,..,priority=1)(name,bases,dic). If the base classes have
    metaclasses conflicting within themselves or with the given metaclasses,
    it automatically generates a compatible metaclass and instantiate it.
    If priority is True, the given metaclasses have priority over the
    bases' metaclasses"""

    priority = options.get("priority", False)  # default, no priority
    return lambda n, b, d: _generatemetaclass(b, metas, priority)(n, b, d)
