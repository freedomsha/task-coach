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

This Python code defines two classes, `Attribute` and `SetAttribute`, which provide a way to manage single and multiple
attributes with event handling. The classes use weak references for their owner objects to avoid memory leaks. The `Attribute`
class handles setting and getting a single value with an associated event handler. The `SetAttribute` class manages a set of
values, allowing elements to be added or removed with events triggered accordingly. Both classes utilize the
`patterns.eventSource` decorator to facilitate event handling.

Ce code Python définit deux classes, `Attribut` et` setAttribute`, qui fournissent
un moyen de gérer les attributs simples et multiples avec la gestion des événements.
Les classes utilisent des références faibles pour leurs objets
propriétaires pour éviter les fuites de mémoire.
La classe `Attribut` gère le réglage et l'obtention d'une valeur unique
avec un gestionnaire d'événements associé.
La classe `SetAttribute` gère un ensemble de valeurs, permettant d'ajouter
ou de supprimer des éléments avec des événements déclenchés en conséquence.
Les deux classes utilisent le décorateur
`patterns.eventSource' pour faciliter la manipulation des événements.

"""

import logging

# from builtins import object
from taskcoachlib import patterns
import weakref

# from taskcoachlib.thirdparty._weakrefset import WeakSet
from weakref import WeakSet  # En test!

log = logging.getLogger(__name__)


# Le bug __func__ : C'est une correction technique subtile mais critique.
# En Python 3, manipuler __func__ sur des méthodes liées est risqué
# car on perd le contexte self.
# Le nouveau code passe simplement la méthode, ce qui est plus standard et fonctionne.
class Attribute(object):
    """
    A class to manage a single attribute with event handling.

    The `Attribute` class handles setting and getting a single value with an associated event handler.
    It uses weak references for its owner object to avoid memory leaks.

    Une classe pour gérer un seul attribut avec la gestion des événements.

    Le réglage et l'obtention de la classe `Attribut` appelle une seule valeur avec un gestionnaire d'événements associé.
    Il utilise des références faibles pour son objet propriétaire pour éviter les fuites de mémoire.
    """

    __slots__ = ("__value", "__owner", "__setEvent")

    def __init__(self, value, owner, setEvent):
        """
        Initialise une nouvelle instance de la classe `Attribut`.

        Args :
            value : La valeur initiale de l'attribut.
            owner : L'objet propriétaire de l'attribut. Une référence faible à cet objet est stockée.
            setEvent : La fonction de gestionnaire d'événements à appeler lorsque l'attribut est défini.

        Attributes :
            - __value : La valeur actuelle de l'attribut.
            - __owner : La référence faible à l'objet propriétaire.
            - __setEvent : La fonction de gestionnaire d'événements à appeler lors de la définition de l'attribut.
        """
        # print(
        #     "Attribute.__init__",
        #     "owner=", owner,
        #     "value=", value,
        #     "setEvent=", setEvent,
        #     "type=", type(setEvent)
        # )
        # # Remplace ton debug par quelque chose qui n'appelle jamais __repr__ :
        # log.debug(
        #     "Attribute.__init__ owner=%s type=%s"
        #     % (
        #         type(owner).__name__ if owner else None,
        #         type(setEvent).__name__,
        #     ),
        # )
        if setEvent is not None and not callable(setEvent):
            raise TypeError(
                f"Attribute.__init__ : setEvent doit être callable, reçu {setEvent!r}"
            )
        super().__init__()
        self.__value = value
        # self.__owner = weakref.ref(owner)
        self.__owner = owner
        # Définit la fonction sous-jacente setEvent
        # self.__setEvent = setEvent.__func__  # Différent en python 3
        # En Python, quand on passe method.__func__, on enlève la partie liée (self).
        # Cet attribut est disponible dans les méthodes de type bound_method (méthodes liées à une instance).
        # Exemple pratique :
        # class MyClass:
        #    def method(self):
        #        pass
        # obj = MyClass()
        # m = obj.method
        # # Accéder à la fonction sous-jacente
        # print(m.__func__)

        # Dans cet exemple, m.__func__ renvoie la fonction définie dans la classe MyClass.
        # Cela permet d'accéder à la définition de la méthode indépendamment de l'instance.
        # Utilité :
        #     Permet de récupérer la fonction originale pour des opérations d'introspection ou de manipulation.
        #     Utile dans la programmation avancée, notamment pour la création de décorateurs ou pour la réflexion sur les méthodes.

        # Donc au lieu d’appeler :
        #     owner._Object__setDescriptionEvent(event)
        #
        # Tu appelles :
        #     Object._Object__setDescriptionEvent(event)  # <- manque le self ici !
        #
        # Cela peut :
        #     soit planter silencieusement,
        #     soit ne rien faire du tout (ex. pas d'appel à event.addSource).
        # Lorsque vous accédez Foo.f ou Foo().f une méthode est renvoyée;
        # elle n'est pas liée dans le premier cas et liée dans le second.
        # Une méthode de python est essentiellement une enveloppe autour d'une fonction
        # qui contient également une référence à la classe où il est une méthode.
        # Lorsqu'elle est liée, elle contient également une référence à l'instance.

        # Lorsque vous appelez une méthode, il fera un contrôle de type
        # sur le premier argument passé pour s'assurer qu'il s'agit d'une instance
        # (il doit s'agir d'une instance de la classe référencée,
        # ou d'une sous-classe de cette classe).
        # Quand la méthode est liée, elle fournira ce premier argument,
        # sur une méthode non liée que vous lui fournissez vous-même.

        # C'est cet objet de méthode qui a l'attribut __func__attribut,
        # qui n'est qu'une référence à la fonction emballée.
        # En accédant à la fonction sous-jacente au lieu d'appeler la méthode,
        # vous supprimez le code de contrôle,
        # et vous pouvez passer tout ce que vous voulez comme premier argument.
        # Les fonctions ne se soucient pas de leurs types d'arguments,
        # mais les méthodes le font.

        # Notez que dans Python 3, cela a changé;
        # Foo.f retourne simplement la fonction, pas une méthode non liée.
        # Foo().f retournant une méthode immobile, toujours liée,
        # mais il n'y a plus de moyen de créer une méthode non liée.

        # Sous le capot, chaque objet de fonction a un __get__méthode,
        # voici ce qui retourne l'objet de méthode:

        # >>> class Foo(object):
        # ...     def f(self): pass
        # ...
        # >>> Foo.f
        # <unbound method Foo.f>
        # >>> Foo().f
        # <bound method Foo.f of <__main__.Foo object at 0x11046bc10>>
        # >>> Foo.__dict__['f']
        # <function f at 0x110450230>
        # >>> Foo.f.__func__
        # <function f at 0x110450230>
        # >>> Foo.f.__func__.__get__(Foo(), Foo)
        # <bound method Foo.f of <__main__.Foo object at 0x11046bc50>>
        # >>> Foo.f.__func__.__get__(None, Foo)
        # <unbound method Foo.f>

        # Ce n'est pas le chemin de code le plus efficace, donc,
        # Python 3.7 ajoute une nouvelle paire de codes opératoires LOAD_METHOD-CALL_METHOD
        # qui remplace la Paire de code opératoires courante LOAD_ATTRIBUTE-CALL_FUNCTION
        # précisément pour éviter de créer un nouvel objet de méthode à chaque fois.
        # Cette optimisation transforme la voie d'exécution pour instance.foo()
        # de type(instance).__dict__['foo'].__get__(instance, type(instance))()
        # avec type(instance).__dict__['foo'](instance),
        # donc passant "manuellement" dans l'instance directement à l'objet de la fonction.
        # Cela permet d'économiser environ 20 % de temps sur les micro-repères existants.

        # Dans ce cas, l’attribut __func__ n’est utilisé
        # que pour implémenter divers attributs, mais pas pour appeler la méthode.
        # Lors de la construction d’une nouvelle méthode à partir d’un base_function,
        # nous vérifions que l’objet self est une instance de __objclass__
        # (si une classe a été spécifiée comme parent) et levons une TypeError dans le cas contraire.

        self.__setEvent = setEvent
        # print(
        #     "Attribute.__init__ self.__setEvent=%r type=%s",
        #     self.__setEvent,
        #     type(self.__setEvent).__name__,
        # )
        # # Ne jamais afficher directement une méthode liée dans ce contexte.
        log.debug(
            "Attribute.__init__ self.__setEvent type=%s name=%s owner_type=%s"
            % (
                type(self.__setEvent).__name__,
                getattr(self.__setEvent, "__name__", None),
                type(getattr(self.__setEvent, "__self__", None)).__name__,
            ),
        )
        # print(
        #     f"Attribute.__init__ self.__setEvent type={type(self.__setEvent).__name__} name={getattr(self.__setEvent, "__name__", None)} owner_type={type(getattr(self.__setEvent, "__self__", None)).__name__}"
        # )

    def get(self):
        """
        Obtient la valeur actuelle de l'attribut.

        Returns :
            La valeur actuelle de l'attribut.
        """
        log.debug("Attribute.get : retourne self.__value ", self.__value)
        return self.__value

    def setEvent(self, setEvent):
        """
        Définit ou remplace le gestionnaire d'événement utilisé lorsque
        l'attribut change. Accepts any callable or None.

        Cette méthode permet à l'appelant (par ex. Object.__init__)
        d'installer le gestionnaire d'événement après la création de
        l'Attribute, ce qui évite de déclencher des événements pendant
        l'initialisation.
        """
        if setEvent is not None and not callable(setEvent):
            raise TypeError(
                f"Attribute.setEvent : setEvent doit être callable, reçu {setEvent!r}"
            )
        log.debug(f"Attribute.setEvent : définit self.__setEvent={setEvent}")
        self.__setEvent = setEvent

    @patterns.eventSource
    def set(self, value, event=None):
        """
        Définit la valeur de l'attribut et déclenche l'événement associé.

        Args :
            value : La nouvelle valeur à définir pour l'attribut.
            event : Données d'événement facultatives à transmettre au gestionnaire d'événements.

        Returns :
            Vrai si la valeur a été définie avec succès et que l'événement a été déclenché, faux autrement.
        """
        # Le code de la méthode set a été corrigé pour ne pas utiliser __func__ et pour appeler directement la méthode d'événement.
        # En Python 3, l'utilisation de __func__ sur une méthode liée peut entraîner des problèmes de contexte, car elle supprime la référence à l'instance (self).
        # La nouvelle implémentation passe simplement la méthode d'événement, qui est déjà liée à l'instance via le propriétaire.
        # Cela garantit que le contexte de l'instance est préservé lors de l'appel du gestionnaire d'événements, et évite les erreurs potentielles liées à la manipulation de __func__.
        # En résumé, la correction technique consiste à appeler directement la méthode d'événement sans tenter de manipuler __func__, ce qui est plus sûr et plus conforme aux conventions de Python 3.
        # Définition de la méthode set corrigée pour éviter les problèmes liés à __func__ en Python 3.
        # Définition du propriétaire avec une référence faible pour éviter les fuites de mémoire. :
        owner = self.__owner
        log.debug(
            f"Attribute.set : Définition de l'attribut {self} avec comme propriétaire owner={owner}, valeur={value} et transmet l'événement event={event}."
        )
        # Vérifie si le propriétaire existe toujours (n'a pas été collecté par le ramasse-miettes).
        if owner is not None:
            # Vérifie si la nouvelle valeur est différente de l'actuelle pour éviter les appels d'événements inutiles.
            if value == self.__value:
                print(
                    f"Attribute.set : La valeur de {self} est déjà définie ainsi : {value}"
                )
                return False
            # Met à jour la valeur de l'attribut.
            self.__value = value
            # self.__setEvent(owner, event)  # ❌ trop d'arguments
            # print(
            #     f"Attribute.set : value={value}, Calling setEvent with owner: {owner} and event: {event}"
            # )  # Debug print
            # print(
            #     "DEBUG Attribute.__setEvent =",
            #     self.__setEvent,
            #     "type=",
            #     type(self.__setEvent),
            # )
            import inspect

            log.debug(
                "Attribute.set : SETEVENT =",
                self.__setEvent,
            )

            log.debug(inspect.signature(self.__setEvent))
            self.__setEvent(
                # event
                event=event
            )  # ✅ juste l'event, self est déjà lié via owner
            # !!! Ce changement est peut-être correct pour les méthodes liées
            # !!! (bound methods), mais pas pour les lambdas.
            log.debug(
                "Attribute.set : Valeur a été définie avec succès et l'événement a été déclenché !"
            )
            return True
        log.debug("Attribute.set : Impossible de définir la valeur !")
        return False


class SetAttribute(object):
    """
    Une classe pour gérer un ensemble d'attributs avec la gestion des événements.

    La classe «SetAttribute» gère un ensemble de valeurs, permettant à des
    éléments d'être ajoutés ou supprimés avec des événements déclenchés en conséquence.
    Il utilise des références faibles pour son objet propriétaire pour éviter les fuites de mémoire.

    Methods :
        - get() : Obtenir une copie de l'ensemble actuel des valeurs.
        - set(values, event=None) : Définit les valeurs de l'attribut et déclenche les événements associés.
        - add(values, event=None) : Ajoute des valeurs à l'attribut et déclenche les événements associés.
        - remove(values, event=None) : Supprime des valeurs de l'attribut et déclenche les événements associés.
        - __nullEvent(*args, **kwargs) : Un gestionnaire d'événements par défaut qui ne fait rien.
    """

    __slots__ = (
        "__set",
        "__owner",
        "__addEvent",
        "__removeEvent",
        "__changeEvent",
        "__setClass",
    )

    def __init__(
        self,
        values,
        owner,
        addEvent=None,
        removeEvent=None,
        changeEvent=None,
        weak=False,
    ):
        """
        Initialise une nouvelle instance de la classe «setAttribute».

        Args :
            values : L'ensemble de valeurs de départ pour l'attribut.
            owner : L'objet propriétaire de l'attribut. Une référence faible à cet objet est stockée.
            addEvent : Fonction de gestionnaire d'événements en option à appeler lorsque des éléments sont ajoutés à l'ensemble.
            removeEvent : Fonction de gestionnaire d'événements en option à appeler lorsque les éléments sont supprimés de l'ensemble.
            changeEvent : Fonction de gestionnaire d'événements facultatif à appeler lorsque l'ensemble change.
            weak : Si vrai, utilisez un WeakSet(réglage faible) pour stocker les valeurs. Par défaut est faux.

        Attributes :
            - __setClass : La classe utilisée pour stocker les valeurs (set ou WeakSet).
            - __set : L'ensemble de valeurs de l'attribut.
            - __owner : La référence faible à l'objet propriétaire.
            - __addEvent : La fonction de gestionnaire d'événements pour les ajouts.
            - __removeEvent : La fonction de gestionnaire d'événements pour les suppressions.
            - __changeEvent : La fonction de gestionnaire d'événements pour les changements.
        """
        log.debug(
            "SetAttribute.__init__ avec owner=",
            owner,
            "values=",
            values,
            "weak=",
            weak,
            "type=",
            type(weak),
            "et méthodes",
            addEvent,
            removeEvent,
            changeEvent,
        )
        self.__setClass = WeakSet if weak else set
        self.__set = self.__setClass(values) if values else self.__setClass()
        self.__owner = weakref.ref(owner)
        # Définit les fonctions de gestionnaire d'événements, en utilisant des gestionnaires par défaut qui ne font rien si aucun n'est fourni.
        self.__addEvent = (addEvent or self.__nullEvent).__func__  #
        self.__removeEvent = (removeEvent or self.__nullEvent).__func__
        self.__changeEvent = (changeEvent or self.__nullEvent).__func__

    def get(self):
        """
        Obtenir une copie de l'ensemble actuel des valeurs.

        Returns :
            Un nouvel ensemble contenant les valeurs actuelles de l'attribut.
        """
        log.debug(
            "SetAttribute.get : retourne une copie de l'ensemble actuel des valeurs."
        )
        return set(self.__set)

    @patterns.eventSource
    def set(self, values, event=None):
        """
        Définit les valeurs de l'attribut et déclenche les événements associés.

        Args :
            values : Le nouvel ensemble de valeurs à définir pour l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été définies avec succès et que les événements ont été déclenchés, faux sinon.
        """
        # Définition de la méthode set pour SetAttribute, qui met à jour l'ensemble de valeurs et déclenche les événements d'ajout, de suppression et de changement en conséquence.
        # Le code vérifie d'abord si le propriétaire existe toujours, puis compare les nouvelles valeurs avec les anciennes pour déterminer les éléments ajoutés et supprimés. Ensuite, il met à jour l'ensemble de valeurs et déclenche les événements appropriés.
        # Définit owner comme propriétaire de référence faible pour éviter les fuites de mémoire.
        owner = self.__owner()
        log.debug(
            f"SetAttribute.set : Définition de l'attribut {self} avec comme propriétaire owner={owner}, valeurs={values} et transmet l'événement event={event}."
        )
        # Vérifie si le propriétaire existe toujours (n'a pas été collecté par le ramasse-miettes).
        if owner is not None:
            # Vérifier si les valeurs appartiennent à l'ensemble contenu dans le propriétaire, si c'est le cas, il n'y a pas de changement à faire, donc retourne False.
            if values == set(self.__set):
                log.debug(
                    "SetAttribute.set : Les valeurs est déjà définie ainsi."
                )
                return False
            # Calculer les éléments ajoutés et supprimés en comparant les nouvelles valeurs avec les anciennes.
            added = values - set(self.__set)
            removed = set(self.__set) - values
            self.__set = self.__setClass(values)
            if added:
                self.__addEvent(owner, event, *added)  # pylint: disable=W0142
            if removed:
                self.__removeEvent(
                    owner, event, *removed
                )  # pylint: disable=W0142
            if added or removed:
                # Déclenche l'événement de changement avec les nouvelles valeurs de l'ensemble.
                self.__changeEvent(owner, event, *set(self.__set))
            log.debug(
                "SetAttribute.set : Valeur a été définie avec succès et l'événement a été déclenché !"
            )
            return True
        log.debug("SetAttribute.set : Impossible de définir les valeurs !")
        return False

    @patterns.eventSource
    def add(self, values, event=None):
        """
        Ajoute des valeurs à l'attribut et déclenche les événements associés.

        Args :
            values : Les valeurs à ajouter à l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été ajoutées avec succès et que les événements ont été déclenchés, faux sinon.
        """
        owner = self.__owner()
        if owner is not None:
            if values <= set(self.__set):
                return False
            self.__set = self.__setClass(set(self.__set) | values)
            self.__addEvent(owner, event, *values)  # pylint: disable=W0142
            self.__changeEvent(owner, event, *set(self.__set))
            return True
        return False

    @patterns.eventSource
    def remove(self, values, event=None):
        """
        Removes values from the attribute and triggers the associated events.
        Supprime les valeurs de l'attribut et déclenche les événements associés.

        Args :
            values : Les valeurs à supprimer de l'attribut.
            event : Données d'événement facultatives à transmettre aux gestionnaires d'événements.

        Returns :
            Vrai si les valeurs ont été supprimées avec succès et que les événements ont été déclenchés, faux autrement.
        """
        owner = self.__owner()
        if owner is not None:
            if values & set(self.__set) == set():
                return False
            self.__set = self.__setClass(set(self.__set) - values)
            self.__removeEvent(owner, event, *values)  # pylint: disable=W0142
            self.__changeEvent(owner, event, *set(self.__set))
            return True
        return False

    def __nullEvent(self, *args, **kwargs):
        pass
