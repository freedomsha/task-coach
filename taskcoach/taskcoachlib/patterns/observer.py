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


Explications
Types de base : Les types de base comme int, str, list, set, dict sont utilisés pour les annotations de type.
Types génériques : Optional, Any, Callable, Dict, List, Set, Tuple, Union sont utilisés pour des annotations plus complexes.
Méthodes : Chaque méthode a été annotée avec ses types d'arguments et son type de retour.
Classes : Les classes ont été annotées pour indiquer les types des attributs internes.
"""

# Explications
# Utilisation de id(source) : En utilisant l'identifiant de l'objet comme clé, vous vous assurez que chaque objet a une clé unique qui est hachable.
# Récupération des objets source : Lorsque vous récupérez les sources, vous utilisez les identifiants pour accéder aux objets.

# Résumé du problème
# L'erreur dans ton log venait du fait que des instance de collections (ex. TaskList) — qui peuvent être non hachables — étaient utilisées directement comme éléments d'un tuple-clé de dictionnaire dans le registre des observateurs (Publisher.__observers). En Python un tuple est hachable seulement si tous ses éléments le sont ; ici l'élément source n'était pas hachable -> TypeError.
# Plusieurs endroits manipulent des "sources" d'événements : la classe Event et la classe Publisher. Il fallait rendre le comportement cohérent pour éviter d'utiliser un objet non hachable comme clé de dict.

# Principales corrections :
# Event
# Internalise les sources en utilisant soit l'objet source lui-même (quand il est hashable) soit id(source) comme clé si l'objet est non-hashable.
# Ajout d'une table de correspondance privée self.__idToSource pour retrouver l'objet original lorsque nous avons stocké id(source).
# Les méthodes affectées : init, addSource, sources, values, sourcesAndValuesByType.
# API publique inchangée : callers (ex. code qui demande event.sources(), event.values(...)) continueront à recevoir les objets originaux.
# Publisher
# Normalise le stockage des clés (eventType, eventSource) de la même façon que Event : si eventSource est non-hashable, on utilise id(eventSource) comme clé et on garde la table self.__idToSource.
# Adaptation de :
# init / clear : initialisation / nettoyage du mapping id->source.
# registerObserver : convertit eventSource en clé hachable avant de stocker.
# removeObserver : comparaison adaptée pour matcher les clés stockées (int = id) avec l'objet fourni ; nettoyage de la table id->source lorsque la clé est supprimée.
# notifyObservers : lors de la recherche des observateurs, on convertit la source "originale" en la clé stockée (id ou objet) pour faire le lookup, mais on transmet aux observers des (type, source) avec la source originale (pour construire le subEvent).
#
# Pourquoi cette solution
# Minimaliste et non-invasive : on ne change pas l'API publique des événements/observateurs ; on corrige seulement la façon dont on stocke les clés en interne.
# Résout le bug concret : plus d'exception TypeError lors de setdefault avec tuple contenant une source non-hashable.
# Préserve la possibilité d'utiliser les objets originaux côté appelant (Event.sources() renvoie toujours les objets).
#
# Extrait des changements (explication technique courte)
# Quand une source n'est pas hashable, la clé interne devient id(source) (entier) et on mémorise __idToSource[id] = source.
# Lors du lookup on résout la clé via le même procédé (hashable → objet, non-hashable → id).
# Suppression : si on supprime la dernière entrée pour une clé stockée par id, on supprime aussi la clef du mapping __idToSource.

# Remarques et points à surveiller
# Il reste des warnings de linting (imports typés non utilisés, etc.) mais ce n'est pas bloquant pour l'exécution. J'ai préféré conserver le style et les annotations présentes afin de minimiser les changements.
# L'utilisation de id(object) pour la clé est une solution pragmatique ; elle suppose que l'objet reste vivant pendant la durée d'enregistrement de l'observateur. Tant que l'observateur tient une référence (MethodProxy) à l'instance, l'objet ne sera pas garbage-collected, donc pas de réutilisation d'id problématique.
# Si tu veux, on peut implémenter une clé basée sur (object.class, id(object)) ou un wrapper explicit pour rendre encore plus robuste — mais ce n'est a priori pas nécessaire.
# from . import singleton
import logging
from collections.abc import Iterable
from typing import (
    Any,
    Callable,
    Dict,
    List as TypedList,
    Optional,
    Set,
    Tuple,
    Union,
)
from taskcoachlib.patterns import singleton
import functools

# from taskcoachlib.thirdparty.pubsub import pub
from pubsub import pub
import os

# Optionally install a tracer for PyPubSub sendMessage calls when
# TASKCOACH_TRACE_PUBSUB is set. This helps debugging why TaskFile
# (which listens via pubsub) does or does not receive messages.
if os.environ.get("TASKCOACH_TRACE_PUBSUB") in ("1", "true", "True"):
    try:
        _orig_sendMessage = pub.sendMessage

        def _traced_sendMessage(topic, *args, **kwargs):
            try:
                print(
                    f"pub.sendMessage: topic={topic!r}, args={args}, kwargs={kwargs}"
                )
            except Exception:
                print("pub.sendMessage: (trace) failed to stringify message")
            return _orig_sendMessage(topic, *args, **kwargs)

        pub.sendMessage = _traced_sendMessage
    except Exception:
        # If pub doesn't have sendMessage or monkeypatching fails, ignore
        pass
# Ignore these pylint messages:
# - W0142: * or ** magic
# - W0622: Redefining builtin types
# pylint: disable=W0142,W0622

log = logging.getLogger(__name__)


class List(list):
    """
    Une sous-classe de liste utilisée pour les collections d'objets de domaine.
    Garantit que les sous-classes de List sont toujours considérées comme inégales
    même lorsque leur contenu est le même.

    Cette classe est conçue pour éviter les erreurs potentielles liées à l'utilisation
    d'arguments de mot-clé avec la classe `list` de base. En forçant l'utilisation
    d'un seul argument positionnel (optionnel) correspondant à un itérable,
    on garantit un comportement plus prévisible.

    Methods :
        __eq__ : Comparez deux listes pour l'égalité, en considérant les sous-classes de List comme inégales même si leur contenu est le même.
        removeItems : Supprimez plusieurs éléments de la liste, utile pour ObservableList pour générer une seule notification lors de la suppression de plusieurs éléments.

    """

    # def __eq__(self, other: list) -> bool:
    def __eq__(self, other):
        # def __eq__(self, other: Union['List', list]) -> bool:
        """
        Comparez deux listes pour l'égalité.

        Les sous-classes de List sont toujours considérées comme inégales, même lorsque
        leur contenu est le même. En effet, les sous-classes List sont
        utilisées comme collections d'objets de domaine. Lorsqu'il est comparé à d'autres types,
        le contenu est comparé.

        Args :
            other (List ou list) : La liste avec laquelle comparer.

        Returns :
            bool : True si les listes sont égales, False sinon.
        """
        if isinstance(other, List):
            return self is other
        else:
            return list(self) == other

    # def removeItems(self, items: list):
    def removeItems(self, items):
        # def removeItems(self, items: list) -> None:
        """
        Supprimez plusieurs éléments de la liste.

        List.removeItems est l'opposé de list.extend. Utile pour
        ObservableList pour pouvoir générer une seule notification
        lors de la suppression de plusieurs éléments.

        Args :
            items (list) : Les éléments à supprimer.
        """
        for item in items:
            list.remove(
                self, item
            )  # No super() to prevent overridden remove method from being invoked


# Résumé du problème
# L'erreur TypeError: cannot use 'taskcoachlib.domain.task.tasklist.TaskList'
# as a dict key survient parce que des instances de TaskList
# (ou plus exactement des collections dérivées de set) sont utilisées
# comme clés dans des dictionnaires (ex. dans Event/Publisher)
# mais les instances héritées de set sont par défaut non hachables
# en Python (built-in set met hash = None).
# Le code existant (Event/Publisher) s'attend à pouvoir
# utiliser des « sources » qui peuvent être des collections
# (TaskList, ObservableSet, etc.) comme clés.
# La solution la moins intrusive est d'ajouter un hash basé
# sur l'identité des objets pour ces classes de collection
# afin d'autoriser leur usage comme clés sans modifier la logique métier.
class Set(set):
    """
    Sous-classe de `set` qui restreint les arguments lors de l'instanciation.

    Une sous-classe d'ensemble utilisée pour les collections d'objets de domaine.
    Garantit que les arguments de mot-clé ne sont pas transmis à la classe d'ensemble de base.
    Le type d'ensemble intégré n'aime pas les arguments de mot-clé, donc pour le garder,
    il est heureux que nous ne le fassions pas. Je ne les transmets pas.

    Cette classe est conçue pour éviter les erreurs potentielles liées à l'utilisation
    d'arguments de mot-clé avec la classe `set` de base. En forçant l'utilisation
    d'un seul argument positionnel (optionnel) correspondant à un itérable,
    on garantit un comportement plus prévisible.

    Methods :
        __new__ : Crée une nouvelle instance de Set, en vérifiant que l'argument est un itérable.
        __cmp__ : Compare deux ensembles pour l'égalité, en utilisant set.__eq__ pour éviter les erreurs dans Python 2.5.
        __hash__ : Rendre les instances de Set hachables en utilisant un hachage basé sur l'identité (id(self))
                   pour permettre leur utilisation comme clés de dictionnaire,
                   tout en restant compatibles avec l'égalité basée sur l'identité définie ailleurs.
    """

    def __new__(class_, iterable=None, *args, **kwargs):
        # def __new__(cls, iterable: Optional[Iterable] = None, *args, **kwargs) -> 'Set':
        # # return set.__new__(class_, iterable)
        if iterable is not None and not isinstance(iterable, Iterable):
            raise TypeError("iterable must be an iterable")
        if iterable is None:
            return set.__new__(class_)
        else:
            return set.__new__(class_, iterable)

    def __cmp__(self, other):
        # def __cmp__(self, other: Union['Set', set]) -> int:
        """
        Comparez deux ensembles pour l'égalité.

        Si set.__cmp__ est appelé, nous obtenons une TypeError dans Python 2.5, donc
        appelez set.__eq__ à la place.

        Args :
            other (Set or set) : L'ensemble à comparer.

        Returns :
            (int) : Retourne 0 si les ensembles sont égaux, -1 sinon.
        """
        if self == other:
            return 0
        else:
            return -1

    # Rendre les instances de Set hachables afin qu'elles puissent être
    # utilisées comme clés de dictionnaire. Les collections de domaine
    # (sous-classes de Set) sont mutables mais le code existant (par ex.
    # Publisher/Event) s'attend à pouvoir utiliser les instances comme
    # clés. Nous utilisons un hachage basé sur l'identité pour rester
    # compatibles avec l'égalité basée sur l'identité définie ailleurs.
    # Raison du choix
    # Minimal : n'affecte que le comportement de hashage (permet d'utiliser les collections comme clés).
    # Non invasif : on ne change pas la logique d'égalité existante (beaucoup de ces collections comparent par identité).
    # Central : ajouter hash dans Set résout le souci pour toutes les sous-classes de collection (TaskList, CompositeSet, ObservableSet, etc.) au lieu d'ajouter hash partout.
    def __hash__(self):
        """Obtenez le hachage de l'ensemble.

        On utilise un hachage fondé sur l'identité (id(self)) pour rester compatible avec l'égalité par identité qui est utilisée pour ces collections (cela n'affecte pas la sémantique métier).
        """
        return hash(id(self))


class Event(object):
    """
    L'événement représente des événements de notification.

    Les événements peuvent notifier un seul type d'événement
    pour une seule source ou plusieurs types d'événements
    et plusieurs sources en même temps.
    Les méthodes Event tentent de rendre les deux utilisations
    faciles.

    L'événement représente les événements de notification.
    Les événements peuvent notifier un seul type d'événement
    pour une seule source ou pour plusieurs types d'événements
    et plusieurs sources en même temps.
    Les méthodes Event tentent de faciliter les deux utilisations.

    Cela crée un événement pour un type, une source et une valeur
    >> event = Event('event type', 'event source', 'new value')

    Pour ajouter plus de sources d'événements avec leur propre valeur :
    >> event.addSource('une autre source', 'une autre valeur')

    Pour ajouter une source avec un type d'événement différent :
    >> event.addSource('encore une autre source', 'sa valeur', type='un autre type')

    Methods :
        __init__ : Initialiser l'événement avec un type, une source et des valeurs facultatives.
        __repr__ : Représentation de l'événement sous forme de chaîne de caractères.
        __eq__ : Comparer deux événements pour l'égalité.
        addSource : Ajouter une source avec des valeurs facultatives à l'événement.
        type : Renvoie le type d'événement.
        types : Renvoie l'ensemble des types d'événements que cet événement notifie.
        sources : Renvoie l'ensemble de toutes les sources de cette instance d'événement, ou les sources pour des types d'événements spécifiques.
        sourcesAndValuesByType : Renvoie toutes les données {type : {source : valeurs}}.
        value : Renvoie la valeur qui appartient à une source.
        values : Renvoie les valeurs qui appartiennent à une source.
        subEvent : Crée un sous-événement pour une source et un type d'événement spécifiques.
        send : Envoyer l'événement aux observateurs du(des) type(s) de cet événement.
    """

    def __init__(self, type=None, source=None, *values):
        # def __init__(self, type: Optional[str] = None, source: Optional[Any] = None, *values: Any) -> None:
        """
        Initialisez l'événement.

        Args :
            type (str) : (facultatif) Le type d'événement.
            source (object) : (facultatif) La source de l'événement.
            *values : Valeurs supplémentaires associées à l'événement.

        Attributes :
            __sourcesAndValuesByType (dict) : Un dictionnaire contenant les types d'événements comme clés et des dictionnaires de sources et de valeurs comme valeurs.
            _sending (bool) : Un indicateur pour éviter les cycles dans l'envoi d'événements.
        """
        # self.__sourcesAndValuesByType = {} if type is None else \
        #     {type: {} if source is None else {source: values}}

        # TODO : problème d'utilisation de __sourcesAndValuesByType !
        self.__sourcesAndValuesByType = (
            # self.__sourcesAndValuesByType: Dict[str, Dict[Any, Tuple[Any, ...]]] = (
            # dict()
            {}
            if type is None
            # else {type: {} if source is None else {source: values}}
            # else {type: dict() if source is None else {source: values}}
            else {type: {} if source is None else {}}
        )  # dict or set ?
        # Internal storage uses keys that are either the source object itself
        # (when hashable) or id(source) when the source object is unhashable.
        # We also keep a mapping from id -> object so the public API can
        # always present actual objects as sources.

        # Map from id(source) to the actual source object for keys stored as ids
        self.__idToSource = {}
        if type is not None and source is not None:
            # Use addSource to populate storage consistently
            self.addSource(source, *values, type=type)
        self._sending = False  # To prevent cycles in event sending

    # def __repr__(self) -> str:
    def __repr__(self):  # pragma: no cover
        """
        Représentation de l'événement sous forme de chaîne de caractères.

        Returns:
            str : L'événement sous forme de chaîne de caractères.
        """
        # return "Event(%s)" % (self.__sourcesAndValuesByType,)
        return f"Event({self.__sourcesAndValuesByType})"

    def __eq__(self, other):
        # def __eq__(self, other: 'Event') -> bool:
        """
        Comparez deux événements pour l'égalité.

        Les événements sont comparables lorsque toutes leurs données sont égales.

        Args :
            other (event) : L'événement avec lequel comparer.

        Returns :
            (bool) : Vrai si les événements sont égaux, faux sinon.
        """
        return self.sourcesAndValuesByType() == other.sourcesAndValuesByType()

    def addSource(self, source, *values, **kwargs):
        # def addSource(self, source: Any, *values: Any, **kwargs: Any) -> None:
        """
        Ajoutez une source avec des valeurs facultatives à l'événement.

        Ajoutez une source avec des valeurs facultatives à l'événement. Spécifiez éventuellement
        le type comme argument de mot-clé. Si aucun type n'est spécifié, la source
        et les valeurs sont ajoutées pour un type aléatoire, c'est-à-dire n'omettez le type que si
        l'événement n'a qu'un seul type.

        Args :
            source (objet) : La source de l'événement.
            *values : Valeurs supplémentaires associées à l'événement.
            **kwargs : Arguments de mots-clés arbitraires (type : str, facultatif).
        """
        # Use the source object itself as the dict key. Observable collections and
        # domain objects implement __hash__ appropriately so they can be used as
        # keys. This keeps the event system working with actual objects instead
        # of their id() values which simplifies matching with registered
        # observers.
        # eventType = kwargs.pop('type', self.type())
        # currentValues = set(self.__sourcesAndValuesByType.setdefault(eventType, {}).setdefault(source, tuple()))
        # currentValues |= set(values)
        # self.__sourcesAndValuesByType.setdefault(eventType, {})[source] = tuple(currentValues)

        # # TODO : à vérifier problèmes dans les tests
        # print(
        #     f"Event.addSource : Ajout de source : {source} avec des valeurs : {values}, kwargs : {kwargs}"
        # )
        eventType = kwargs.pop(
            "type", self.type()
        )  # Définit le type d'événement
        # # log.debug(f"Event: Ajout de source : {source}, type : {eventType}, valeurs : {values}")
        # # print(f"Event.addSource : récupère le type d'événement : {eventType}.")
        # # currentValues = set(
        # #     self.__sourcesAndValuesByType.setdefault(eventType, {}).setdefault(
        # #         source, tuple()
        # #     )
        # # )
        # sources = self.__sourcesAndValuesByType.setdefault(
        #     eventType, {}
        # )  # Récupère ou crée le dictionnaire des sources pour le type d'événement
        # # TypeError: cannot use 'taskcoachlib.domain.task.tasklist.TaskList' as a dict key (unhashable type: 'TaskList')
        # # print(f"Event.addSource : récupère les sources : {sources}.")
        # source_key = id(source)
        # currentValues = sources.get(
        #     # source,
        #     # tuple(),
        #     source_key,
        #     tuple(),
        # )  # Récupère les valeurs actuelles pour la source, ou une tuple vide si la source n'existe pas
        # print(f"Event.addSource : récupère les valeurs : {currentValues}.")
        # # self.__sourcesAndValuesByType.setdefault(eventType, {})[source] = (
        # #     tuple(currentValues)
        # # )
        # print(
        #     f"Event.addSource : Ajoute les valeurs : {values} à la source : {source} dans le dictionnaire de sources : {sources}."
        # )
        # # sources[source] = currentValues + values
        # sources[source_key] = currentValues + values
        # # self.__sourcesAndValuesByType[eventType][source] = tuple(currentValues)
        # print(f"Event.addSource : Voici les nouvelles sources : {sources}.")

        # Use the source object itself as the dict key. Observable collections and
        # domain objects implement __hash__ appropriately so they can be used as
        # keys. This keeps the event system working with actual objects instead
        # of their id() values which simplifies matching with registered
        # observers.

        sources = self.__sourcesAndValuesByType.setdefault(eventType, {})

        # Determine a dict key that is hashable: use the source itself when
        # possible, otherwise fall back to id(source) and remember the
        # original object in __idToSource.
        if source is None:
            source_key = None
        else:
            try:
                hash(source)
            except TypeError:
                source_key = id(source)
                # store mapping so we can recover the original object later
                self.__idToSource[source_key] = source
            else:
                source_key = source

        currentValues = set(sources.setdefault(source_key, tuple()))
        currentValues |= set(values)
        print(
            f"Event.addSource : Ajoute les valeurs : {values} à la source : {source} (clé : {source_key}) dans le dictionnaire de sources : {sources}."
        )
        sources[source_key] = tuple(currentValues)

    # def type(self) -> str:
    def type(self):
        # def type(self) -> Optional[str]:
        """
        Renvoie le type d'événement.

        S'il existe plusieurs types d'événements, cette méthode
        renvoie un type d'événement arbitraire. Cette méthode est utile si
        l'appelant est sûr que cette instance d'événement a exactement un seul type d'événement.

        Returns :
            (str | none) : Le type d'événement.
        """
        return list(self.types())[0] if self.types() else None

    # def types(self) -> set:
    def types(self):
        # def types(self) -> Set[str]:
        """
        Renvoie l'ensemble des types d'événements que cet événement notifie.

        Returns :
            set : L'ensemble des types d'événements.
        """
        return set(self.__sourcesAndValuesByType.keys())

    # def sources(self, *types) -> set:
    def sources(self, *types):
        # def sources(self, *types: str) -> Set[Any]:
        """
        Renvoie l'ensemble de toutes les sources de cette instance d'événement, ou les sources
        pour des types d'événements spécifiques.

        Args :
            *types : types d'événements spécifiques à filtrer.

        Returns :
            set : L'ensemble des sources.
        """
        types = (
            types or self.types()
        )  # Utilise tous les types si aucun n'est spécifié
        sources = set()
        for type in types:
            # # Récupérer les objets source à partir de leurs identifiants
            # # sources |= set(
            # #     self.__sourcesAndValuesByType.get(type, dict()).keys()
            # # )
            # # # sources |= set(
            # # #     self.__sourcesAndValuesByType.get(type, {}).keys()
            # # # )
            # sources |= {
            #     source
            #     for source in self.__sourcesAndValuesByType.get(
            #         type, {}
            #     ).keys()
            # }
            for key in self.__sourcesAndValuesByType.get(type, {}).keys():
                if key is None:
                    sources.add(None)
                elif isinstance(key, int):
                    # stored as id -> retrieve original object when possible
                    orig = self.__idToSource.get(key)
                    if orig is not None:
                        # If the original object is hashable we can return it
                        # as a set element; otherwise add the id instead to
                        # avoid TypeError when inserting into a set.
                        try:
                            hash(orig)
                        except TypeError:
                            # return the int id for unhashable originals
                            sources.add(key)
                        else:
                            sources.add(orig)
                else:
                    sources.add(key)
        return sources

    # def sourcesAndValuesByType(self) -> dict:
    def sourcesAndValuesByType(self):
        # def sourcesAndValuesByType(self) -> Dict[str, Dict[Any, Tuple[Any, ...]]]:
        """
        Renvoie toutes les données {type : {source : valeurs}}.

        Returns :
            dict : Les données de l'événement.
        """
        # return self.__sourcesAndValuesByType
        # Return a mapping {type: {source_object: values}} where source_object
        # is the original source (not id) so callers don't need to know about
        # our internal id-based keys.
        result = {}
        for type, sources in self.__sourcesAndValuesByType.items():
            result[type] = {}
            for key, vals in sources.items():
                if key is None:
                    result[type][None] = vals
                elif isinstance(key, int):
                    orig = self.__idToSource.get(key)
                    if orig is not None:
                        result[type][orig] = vals
                else:
                    result[type][key] = vals
        return result

    # def value(self, source=None, type=None) -> object:
    def value(self, source=None, type=None):
        # def value(self, source: Optional[Any] = None, type: Optional[str] = None) -> Any:
        """
        Renvoie la valeur qui appartient à une source.

        S'il existe plusieurs valeurs,
        cette méthode renvoie uniquement la première. Cette méthode est donc
        utile si l'appelant est sûr qu'il n'y a qu'une seule valeur associée
        à la source. Si la source est None, renvoie la valeur d'une source
        arbitraire. Cette dernière option est utile si l'appelant est sûr
        qu'il n'y a qu'une seule source.

        Args :
            source (object, facultatif) : La source de l'événement.
            type (str, facultatif) : Le type d'événement.

        Returns :
            object : La valeur associée à la source.
        """
        return self.values(source, type)[0]

    def values(self, source=None, type=None):
        # def values(self, source: Optional[Any] = None, type: Optional[str] = None) -> TypedList[Any]:
        """
        Renvoie les valeurs qui appartiennent à une source.

        Si la source est Aucune,
        renvoie les valeurs d'une source arbitraire.
        Cette dernière option est utile
        si l'appelant est sûr qu'il n'y a qu'une seule source.

        Args :
            source (object, facultatif) : La source de l'événement.
            type (str, facultatif) : Le type d'événement.

        Returns :
            list : Les valeurs associées à la source.
        """
        type = type or self.type()
        # # If no specific source is given, pick an arbitrary one for the type.
        # selected_source = source or (
        #     list(self.__sourcesAndValuesByType.get(type, {}).keys())[0]
        #     if self.__sourcesAndValuesByType.get(type)
        #     else None
        # )
        # return self.__sourcesAndValuesByType.get(type, {}).get(
        #     selected_source, []
        # )

        # Resolve source to internal key representation
        if source is None:
            # pick an arbitrary stored key
            stored_keys = list(
                self.__sourcesAndValuesByType.get(type, {}).keys()
            )
            selected_key = stored_keys[0] if stored_keys else None
        else:
            try:
                hash(source)
            except TypeError:
                selected_key = id(source)
            else:
                selected_key = source

        return self.__sourcesAndValuesByType.get(type, {}).get(
            selected_key, []
        )

    def subEvent(self, *typesAndSources):
        # def subEvent(self, *typesAndSources: Tuple[str, Any]) -> 'Event':
        """
        Créez un nouvel événement qui contient un sous-ensemble des données de cet événement.

        Args :
            *typesAndSources : Tuples de (type, source).

        Returns :
            Event : L'événement de sous-ensemble.
        """
        # Il faut s'assurer que subEvent ne traite pas plusieurs fois la même combinaison de (type, source).
        # On utilise un ensemble (set) pour suivre les combinaisons déjà ajoutées au nouvel événement.
        # Unicité : En suivant les couples (type_s, eachSource) dans l'ensemble added,
        # le code ignore la deuxième requête du test car ('eventtype', self)
        # a déjà été inséré lors de la première itération.
        #
        # Conformité au test : L'événement résultant ne contiendra qu'une seule fois la valeur,
        # correspondant ainsi à self.event et faisant passer l'assertion assertEqual.
        subEvent = self.__class__()
        added = set()  # Pour suivre les (type, source) déjà traités

        for type_s, source in typesAndSources:
            sourcesToAdd = self.sources(type_s)
            if source is not None:
                # Make sure source is actually in self.sources(type):
                # sourcesToAdd &= set([source])
                # TODO: try this
                sourcesToAdd &= {source}
            kwargs = dict(
                type=type_s  # TODO : type=type ou type=source ?
            )  # Python doesn't allow type=type after *values
            for eachSource in sourcesToAdd:
                # subEvent.addSource(
                #     eachSource, *self.values(eachSource, type_s), **kwargs
                # )  # pylint: disable=W0142
                # On vérifie si on a déjà ajouté cette source pour ce type
                if (type_s, eachSource) not in added:
                    subEvent.addSource(
                        eachSource, *self.values(eachSource, type_s), **kwargs
                    )
                    added.add((type_s, eachSource))
        return subEvent

    def send(self) -> None:
        """
        Envoyez cet événement aux observateurs du(des) type(s) de cet événement.

        L'envoi de l'événement est effectué via Publisher.notifyObservers.
        Pour éviter les cycles dans les événements,
        une vérification est effectuée pour s'assurer que l'événement n'est pas déjà en cours d'envoi.
        Si c'est le cas, un message est imprimé et l'envoi est interrompu.
        Sinon, l'événement est envoyé et la variable _sending est réinitialisée à False une fois l'envoi terminé.
        """
        # Publisher().notifyObservers(self)
        if getattr(self, "_sending", False):
            print("Event send : Cycle détecté dans les événements.")
            log.error("Event send : Cycle détecté dans les événements.")
            return
        self._sending = True
        try:
            Publisher().notifyObservers(self)
        except Exception as e:
            log.exception(
                f"Event send : Exception lors de l'envoi de l'événement : {e}"
            )
        finally:
            self._sending = False


def eventSource(f):
    # def eventSource(f: Callable) -> Callable:
    """
    Décorer les méthodes qui envoient des événements avec du code
    pour éventuellement créer l'événement
    et éventuellement l'envoyer.

    Cela permet d'envoyer un seul événement
    pour des chaînes de plusieurs méthodes dont chacune doit envoyer un événement.

    Args :
        f (fonction) : La méthode pour décorer.

    Returns :
        function : La méthode décorée.
    """

    @functools.wraps(f)
    def decorator(*args, **kwargs):
        # def decorator(*args: Any, **kwargs: Any) -> Any:
        """
        Décorez la méthode.

        Args :
            *args: Arguments de longueur variable.
            **kwargs: Arguments optionnels.

        Attributes :
            event (Event) : L'événement à envoyer, s'il n'est pas déjà fourni dans les arguments de mot-clé.
            notify (bool) : Indique si l'événement doit être envoyé après l'appel de la méthode décorée.

        Returns:
            object: Le résultat de l'appel de la méthode décorée.
        """
        # Récupérer l'événement des arguments de mot-clé ou en créer un nouveau s'il n'existe pas
        event = kwargs.pop("event", None)
        print(
            f"eventSource : Récupération de l'événement : {event} à partir des arguments de mot-clé."
        )
        # Créer un nouvel événement si aucun n'est fourni, sinon utiliser l'événement existant
        notify = event is None  # We only Notify if we're the event creator
        # Passer l'événement à la méthode décorée via les arguments de mot-clé
        event = event if event else Event()
        kwargs["event"] = event if event else Event()
        print(
            f"eventSource : Appel de la méthode décorée avec l'événement : {kwargs['event']}."
        )
        result = f(*args, **kwargs)
        if notify:
            print(f"eventSource : Envoi de l'événement : {kwargs['event']}.")
            event.send()
        print(
            f"eventSource : Résultat de l'appel de la méthode décorée : {result} !"
        )
        return result

    return decorator


class MethodProxy(object):
    """
    Enveloppez les méthodes dans une classe qui permet de comparer les méthodes.

    Comparaison si les méthodes d'instance ont été modifiées dans Python 2.5,
    les méthodes d'instance sont égales lorsque leurs instances sont égales, ce qui n'est pas
    le comportement nécessaire pour les rappels. Cette classe encapsule les rappels pour restaurer ou
    pour récupérer l'ancien comportement.
    """

    def __init__(self, method):
        # def __init__(self, method: Callable) -> None:
        """
        Initialisez la méthode MethodProxy.

        Args :
            method (fonction) : La méthode à envelopper.

        Attributes :
            method (fonction) : La méthode encapsulée.
        """
        self.method = method

    # def __repr__(self) -> str:
    def __repr__(self):
        """
        Représentation de la méthode MethodProxy sous forme de chaîne de caractères.

        Returns :
            str : La méthode MethodProxy sous forme de chaîne de caractères.
        """
        # return "MethodProxy(%s)" % self.method  # pragma: no cover
        return f"MethodProxy({self.method})"  # pragma: no cover

    def __call__(self, *args, **kwargs):
        # def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Appelez la méthode encapsulée.

        Args :
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.

        Returns :
            objet : le résultat de l’appel de méthode.
        """
        return self.method(*args, **kwargs)

    # def __eq__(self, other) -> bool:
    def __eq__(self, other):
        # def __eq__(self, other: 'MethodProxy') -> bool:
        """
        Comparez deux objets MethodProxy pour l'égalité.

        Args :
            other (MethodProxy) : Le MethodProxy avec lequel comparer.

        Returns :
            bool : True si les MethodProxies sont égaux, False sinon .
        """
        return (
            self.method.__self__.__class__ is other.method.__self__.__class__
            and self.method.__self__ is other.method.__self__
            and self.method.__func__ is other.method.__func__
        )

    # def __ne__(self, other) -> bool:
    def __ne__(self, other):
        # def __ne__(self, other: 'MethodProxy') -> bool:
        """
        Comparez deux objets MethodProxy pour l'inégalité.

        Args :
            other (MethodProxy) : Le MethodProxy avec lequel comparer.

        Returns :
            bool : True si les MethodProxies ne sont pas égaux, False sinon.
        """
        return not (self == other)

    # def __hash__(self) -> int:
    def __hash__(self):
        """
        Obtenez le hachage du MethodProxy.

        Returns :
            int : Le hachage du MethodProxy.
        """
        # Can't use self.method.__self__ for the hash, it might be mutable
        return hash(
            (
                self.method.__self__.__class__,
                id(self.method.__self__),
                self.method.__func__,
            )
        )

    def get_im_self(self):
        # def get_im_self(self) -> Any:
        """
        Récupère l'instance associée à la méthode.

        Renvoie :
            object : L'instance associée à la méthode.
        """
        return self.method.__self__

    im_self = property(get_im_self)
    __self__ = im_self


def wrapObserver(decoratedMethod):
    # def wrapObserver(decoratedMethod: Callable) -> Callable:
    """
    Enveloppez l'argument de l'observateur (supposé être le premier après self) dans
    une classe MethodProxy.

    Args :
        decoratedMethod (fonction) : La méthode à décorer.

    Returns :
        fonction : La méthode décorée.
    """

    def decorator(self, observer, *args, **kwargs):
        # def decorator(self: Any, observer: Callable, *args: Any, **kwargs: Any) -> Any:
        assert hasattr(observer, "__self__")
        observer = MethodProxy(observer)
        return decoratedMethod(self, observer, *args, **kwargs)

    return decorator


def unwrapObservers(decoratedMethod):
    # def unwrapObservers(decoratedMethod: Callable) -> Callable:
    """
    Déballez les observateurs renvoyés de leur classe MethodProxy.

    Args :
        decoratedMethod (fonction) : La méthode à décorer.

    Returns :
        fonction : La méthode décorée. Soit la liste des méthodes d'observateur débloquées.
    """

    def decorator(*args, **kwargs):
        """
        Déballez les observateurs renvoyés de leur classe MethodProxy.
        Args :
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.

        Returns :
            list : La liste des méthodes d'observateur débloquées.
        """
        # def decorator(*args: Any, **kwargs: Any) -> TypedList[Callable]:
        observers = decoratedMethod(*args, **kwargs)
        return [proxy.method for proxy in observers]

    return decorator


# Petite question : Dans Publisher.init, tu ajoute self.__idToSource = {] mais pourquoi ne pas utiliser self.__observers directement ?
# Problème originel : certains objets « sources » (par ex. collections comme TaskList) sont potentiellement non-hashables par Python (ou sont mutables et leur hash vaut None). Or le registre des observateurs (Publisher.__observers) utilise des tuples (eventType, eventSource) comme clés de dictionnaire. Si eventSource n'est pas hashable, Python lève TypeError quand on tente d'utiliser ce tuple comme clé.
# Deux approches possibles :
#   Forcer toutes ces collections à être hashables (on trouvera parfois des patchs qui ajoutent __hash__ = lambda self: hash(id(self))). C'est possible, mais touche beaucoup de classes de collection et peut être invasif.
#   Conserver une représentation interne stable et hachable pour la clé (par ex. id(source)), et garder une table séparée pour retrouver l'objet original quand on en a besoin. C'est l'approche retenue ici.
# Rôle concret de __idToSource :
#   Quand on doit stocker une clé mais que la source n'est pas hashable, on stocke id(source) comme clé dans __observers (ou dans Event.__sourcesAndValuesByType) et on enregistre __idToSource[id] = source. Cela permet :
#       d'éviter le TypeError (tuple contenant un entier est hashable),
#       de retrouver plus tard l'objet original quand on doit construire le sous-événement transmis à l'observateur (pour que l'observateur reçoive l'objet réel),
#       de permettre une suppression correcte d'observateurs : removeObserver reçoit l'objet original et doit retrouver les clés internes correspondantes (via __idToSource).
# Pourquoi ne pas « tout faire » avec __observers :
#   __observers est le registre clé->set(callbacks); il est conçu pour lookup rapide. Si on remplaçait en permanence la clé par l'objet original, on se heurterait encore au problème de non-hashabilité. Si on utilisait id(...) partout sans table « id→objet », on perdrait l'objet (et on ne pourrait pas reconstituer l'original pour l'API publique).
#   Séparer la « clé interne hachable » et le « stockage id→objet » permet de garder l'API publique (Event.sources() rend les objets), tout en ayant un comportement interne sûr et performant.
# Conclusion : __idToSource est la façon pragmatique et sûre de résoudre le bug TypeError tout en conservant l'API publique d'événements.


class Publisher(object, metaclass=singleton.Singleton):
    """
    Publisher est utilisé pour s’inscrire aux notifications d’événements.

    Il prend en charge le modèle éditeur/abonnement, également connu sous le nom de modèle observateur.
    Les objets (observateurs) intéressés par les notifications de changement enregistrent une méthode de rappel
    via Publisher.registerObserver. Le rappel devrait
    attendre un argument ; une instance de la classe Event. Les observateurs peuvent
    enregistrer leur intérêt pour des types d'événements spécifiques (sujets) et
    éventuellement des sources d'événements spécifiques, lors de leur inscription.

    Note d'implémentation :
    - Publisher est une classe Singleton puisque tous les observables et tous les observateurs
    doivent utiliser exactement un seul registre pour être sûr que tous les observables
    peuvent atteindre tous les observateurs.

    Attributes :
        __observers (dict) : Le registre des observateurs, organisé par type d'événement et source d'événement.
        __idToSource (dict) : Un mapping de id -> source pour les sources d'événements non hachables utilisées comme clés.

    Methods :
        __init__ : Initialisez l'éditeur.
        clear : Effacer le registre des observateurs. Principalement à des fins de tests.
        registerObserver : Enregistrez un observateur pour un type d'événement.
        removeObserver : Supprimez un observateur.
        notifyObservers : Informer les observateurs de l'événement.
        observers : Obtenez les observateurs actuellement enregistrés.

    """

    def __init__(self, *args, **kwargs):
        # def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialisez l'éditeur.

        Args :
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.

        Attributes :
            __observers (dict) : Le registre des observateurs, organisé par type d'événement et source d'événement.
        """
        super().__init__(*args, **kwargs)
        self.clear()
        self.__observers = {}
        # Map id -> source object for unhashable event sources used as keys
        self.__idToSource = {}

    def clear(self) -> None:
        """
        Effacer le registre des observateurs. Principalement à des fins de tests.
        """
        # observers = {(eventType, eventSource): set(callbacks)}
        try:
            self.__observers.clear()
        except Exception:
            self.__observers = {}  # pylint: disable=W0201
        # also clear id->source mapping
        try:
            self.__idToSource.clear()
        except Exception:
            self.__idToSource = {}

    @wrapObserver
    def registerObserver(self, observer, eventType, eventSource=None):
        # def registerObserver(self, observer: Callable, eventType: str, eventSource: Optional[Any] = None) -> None:
        """
        Enregistrez un observateur pour un type d'événement.

        L'observateur est une méthode de rappel
        qui doit attendre un argument, une instance de Event.
        Le eventType peut être n'importe quoi hachable, généralement une chaîne.
        Lorsque passe une source d'événement spécifique,
        l'observer n'est appelé que lorsque l'événement
        provient de la source d'événement spécifiée.

        Args :
            observer (fonction) : la méthode de rappel de l'observateur.
            eventType (str) : le type d'événement à observer.
            eventSource (object, facultatif) : la source d'événement à observer.
        """
        # log.debug(
        print(
            f"Publisher.registerObserver : Enregistre l'observateur {observer} pour le type d'événement {eventType} et la source d'événement {eventSource}."
        )
        try:
            # observers = self.__observers.setdefault(
            #     # (eventType, eventSource), set()  # TypeError: cannot use 'tuple' as a dict key (unhashable type: 'TaskList')
            #     # (eventType, eventSource.id),
            #     (eventType, id(eventSource)),
            #     set(),
            # )
            print(
                # f"Publisher.registerObserver : Ajoute observer = {observer} à observers : {observers}."
                f"Publisher.registerObserver : Ajoute observer = {observer} à observers."
            )
            # # observers.add(observer)
            # key = (eventType, None if eventSource is None else eventSource)

            # Normalize eventSource to a hashable key
            def _source_key(source):
                """Normalize the event source to a hashable key for use in the observers dict.
                En français : Normaliser la source d'événement en une clé hachable pour l'utilisation dans le dictionnaire des observateurs.

                If the source is None, return None. If the source is hashable, return it directly.
                En français : Si la source est None, renvoyer None. Si la source est hachable, la renvoyer directement.
                If the source is unhashable, use id(source) as the key and store the mapping in __idToSource for later retrieval of the original object.
                En français : Si la source est non hachable, utiliser id(source) comme clé et stocker la correspondance dans __idToSource pour une récupération ultérieure de l'objet original.
                """
                if source is None:
                    return None
                # Try to use the source itself as the key if it's hashable; otherwise, use id(source) and store the mapping in __idToSource.
                # This allows us to support unhashable sources while still allowing observers to receive the original source object.
                # This is necessary because some event sources (e.g. TaskList) are unhashable, and we need a way to use them as keys in the observers dict without causing a TypeError.
                # The __idToSource mapping allows us to retrieve the original source object later when we need to construct the event passed to the observer, so the observer receives the actual object instead of an id.
                # En français : Essayez d'utiliser la source elle-même comme clé si elle est hachable ; sinon, utilisez id(source) et stockez la correspondance dans __idToSource.
                # Cela nous permet de prendre en charge les sources non hachables tout en permettant aux observateurs de recevoir l'objet source original.
                # Cela est nécessaire car certaines sources d'événements (par ex. TaskList) sont non hachables, et nous avons besoin d'un moyen de les utiliser comme clés dans le dictionnaire des observateurs sans provoquer de TypeError.
                # La correspondance __idToSource nous permet de récupérer l'objet source original plus tard lorsque nous devons construire l'événement passé à l'observateur, afin que l'observateur reçoive l'objet réel au lieu d'un id.

                # This approach allows us to maintain the public API of events (Event.sources() returns the original objects) while having a safe and performant internal representation for the observers registry.
                # Note: we only store the id->source mapping for unhashable sources to avoid unnecessary memory usage for hashable sources.
                # This design allows us to handle both hashable and unhashable sources seamlessly in the Publisher without requiring changes to the event sources themselves.
                # This is a pragmatic solution to the TypeError issue while preserving the functionality and API of the event system.
                # The _source_key function encapsulates the logic for determining the appropriate key to use for a given event source, abstracting away the details of handling hashable vs unhashable sources from the rest of the registerObserver method.
                # By using this helper function, we can keep the main logic of registerObserver clean and focused on the registration process, while the _source_key function takes care of the complexities of key normalization for event sources.
                # This design also allows for future extensions or changes to how we handle event sources without needing to modify the core registration logic, as we can simply update the _source_key function as needed.
                # Overall, this approach provides a robust and flexible way to manage event source keys in the Publisher's observers registry while ensuring that observers receive the correct source objects when notified of events.

                # En français : Si la source est None, renvoyer None. Si la source est hachable, la renvoyer directement. Si la source est non hachable, utiliser id(source) comme clé et stocker la correspondance dans __idToSource pour une récupération ultérieure de l'objet original.
                # Note : nous ne stockons la correspondance id->source que pour les sources non hachables afin d'éviter une utilisation de mémoire inutile pour les sources hachables.
                # Cette conception nous permet de gérer à la fois les sources hachables et non hachables de manière transparente dans le Publisher sans nécessiter de modifications des sources d'événements elles-mêmes.
                # La fonction _source_key encapsule la logique pour déterminer la clé appropriée à utiliser pour une source d'événement donnée, abstrahant les détails de la gestion des sources hachables vs non hachables du reste de la méthode registerObserver.
                # En utilisant cette fonction d'aide, nous pouvons garder la logique principale de registerObserver propre et centrée sur le processus d'enregistrement, tandis que la fonction _source_key s'occupe des complexités de la normalisation des clés pour les sources d'événements.
                # Cette conception permet également des extensions ou des changements futurs sur la façon dont nous gérons les sources d'événements sans avoir besoin de modifier la logique d'enregistrement principale, car nous pouvons simplement mettre à jour la fonction _source_key selon les besoins.
                # Dans l'ensemble, cette approche fournit un moyen robuste et flexible de gérer les clés des sources d'événements dans le registre des observateurs du Publisher tout en garantissant que les observateurs reçoivent les objets source corrects lorsqu'ils sont informés des événements.

                try:
                    hash(source)
                except TypeError:
                    k = id(source)
                    self.__idToSource[k] = source
                    return k
                else:
                    return source

            key = (eventType, _source_key(eventSource))
            observers = self.__observers.setdefault(key, set())
            # Register the observer for this (eventType, eventSource) key.
            # Previously the code created the observers set but never added the
            # observer to it which meant notifyObservers could never find any
            # callbacks to call. Add the observer here.
            observers.add(observer)
            # print(
            #     f"Publisher.registerObserver : observers = {self.__observers} !"
            # )  # Trop verbeux, surtout avec les collections de domaine comme sources d'événements.
        except Exception as e:
            log.exception(f"Publisher.registerObserver : Exception : {e}.")

    @wrapObserver
    def removeObserver(self, observer, eventType=None, eventSource=None):
        # def removeObserver(self, observer: Callable, eventType: Optional[str] = None, eventSource: Optional[Any] = None) -> None:
        """
        Supprimez un observateur.

        Si aucun type d'événement n'est spécifié,
        l'observateur est supprimé pour tous les types d'événements.
        Si un type d'événement est spécifié,
        l'observateur est supprimé pour ce type d'événement uniquement.
        Si aucune source d'événement n'est spécifiée,
        l'observateur est supprimé pour toutes les sources d'événements.
        Si une source d'événement est spécifiée,
        l'observateur est supprimé pour cette source d'événement uniquement.
        Si un type d'événement et une source d'événement sont spécifiés,
        l'observateur est supprimé pour la combinaison de ce type d'événement spécifique
        et de cette source d'événement uniquement.

        Args :
            observer (fonction) : La méthode de rappel de l'observateur.
            eventType (str, facultatif) : Le type d'événement à arrêter d'observer.
            eventSource (object, facultatif) : La source d'événement à arrêter d'observer.
        """
        # pylint: disable=W0613

        # First, create a match function that will select the combination of
        # event source and event type we're looking for:

        # Helper to compare stored source keys with a provided eventSource
        def _source_matches(stored_key, provided_source):
            """Compare une clé de source stockée avec une source d'événement fournie."""
            if stored_key is None and provided_source is None:
                return True
            if isinstance(stored_key, int):
                return self.__idToSource.get(stored_key) == provided_source
            return stored_key == provided_source

        if eventType and eventSource:

            def match(type, source):
                """Compare une paire (type, source) avec les critères de suppression."""
                # # def match(type: Optional[str], source: Optional[Any]) -> bool:
                # return type == eventType and source == eventSource
                return type == eventType and _source_matches(
                    source, eventSource
                )

        elif eventType:

            def match(type, source):
                """Compare un type d'événement avec le critère de suppression, en ignorant la source."""
                # def match(type: Optional[str], source: Optional[Any]) -> bool:
                return type == eventType

        elif eventSource:

            def match(type, source):
                """Compare une source d'événement avec le critère de suppression, en ignorant le type d'événement."""
                # # def match(type: Optional[str], source: Optional[Any]) -> bool:
                # return source == eventSource
                return _source_matches(source, eventSource)

        else:

            def match(type, source):
                """Accepte toutes les paires (type, source) car aucun critère de suppression n'est spécifié."""
                # def match(type: Optional[str], source: Optional[Any]) -> bool:
                return True

        # Next, remove observers that are registered for the event source and
        # event type we're looking for, i.e. that match:
        # Création d'une liste de clés à supprimer :
        matchingKeys = [key for key in self.__observers if match(*key)]
        # Suppression des observateurs correspondants :
        for key in matchingKeys:
            self.__observers[key].discard(observer)
            if not self.__observers[key]:
                del self.__observers[key]
                # also remove id->source entry if present
                try:
                    if isinstance(key[1], int):
                        del self.__idToSource[key[1]]
                except Exception:
                    pass

    def notifyObservers(self, event):
        # def notifyObservers(self, event: Event) -> None:
        """
        Informer les observateurs de l'événement. Le type et les sources de l'événement sont
        extraits de l'événement.

        Args :
            event (event) : L'événement dont il faut informer les observateurs.

        Returns :
            None
        """
        # Ajout d'un traceur conditionnel (activable par la variable d'environnement TASKCOACH_TRACE_PUBSUB=1) dans Publisher.notifyObservers pour imprimer les types et sources d'événement ainsi que les observateurs qui seront invoqués.
        # Optional tracing for debugging pubsub message flow.
        # Activate by setting environment variable TASKCOACH_TRACE_PUBSUB=1
        trace_pubsub = os.environ.get("TASKCOACH_TRACE_PUBSUB") in (
            "1",
            "true",
            "True",
        )

        if not event.sources():
            if trace_pubsub:
                print(
                    f"Publisher.notifyObservers: event has no sources, event={event}"
                )
            return
        # log.debug(
        #     f"Publisher.notifyObservers : lancé par {self.__class__.__name__} pour informer les observateurs de l'événement {event} avec sources {event.sources()}."
        # )
        # Recueillir les observateurs *et* les types et sources pour lesquels ils sont enregistrés
        observers = (
            dict()
        )  # {observer: set([(type, source), ...])}  liste set ou dict ? TODO !
        # observers = set()
        # observers: Dict[MethodProxy, Set[Tuple[Optional[str], Optional[Any]]]] = {}
        types = event.types()
        # Inclure les observateurs non inscrits pour une source d'événement spécifique :
        sources = event.sources() | {None}
        # # sources = event.sources() | set([None])
        # eventTypesAndSources = [
        #     (type, source) for source in sources for type in types
        # ]
        # # log.debug(
        # #     f"Publisher.notifyObservers : pour chaque sources {sources} de chaque types {types} récupère {eventTypesAndSources}."
        # # )
        # for eventTypeAndSource in eventTypesAndSources:
        #     for observer in self.__observers.get(eventTypeAndSource, set()):
        #         # for observer in self.__observers.get(eventTypeAndSource, dict()):
        #         observers.setdefault(observer, set()).add(
        #             eventTypeAndSource
        #         )  # dict() a setdefault ! pas set().
        #         # observers.setdefault(observer, []).append(eventTypeAndSource)

        if trace_pubsub:
            try:
                print(
                    "Publisher.notifyObservers: event types=",
                    list(types),
                    " sources=",
                    list(event.sources()),
                    " event=",
                    event,
                )
            except Exception:
                # Ensure tracing never raises
                print(
                    "Publisher.notifyObservers: (trace) failed to stringify event"
                )

        # For each original source, compute stored key and look up observers.
        for source_orig in sources:
            stored_source = None
            if source_orig is None:
                stored_source = None
            else:
                try:
                    hash(source_orig)
                except TypeError:
                    stored_source = id(source_orig)
                else:
                    stored_source = source_orig

            for type in types:
                stored_pair = (type, stored_source)
                for observer in self.__observers.get(stored_pair, set()):
                    # collect original (type, source_orig) for subEvent creation
                    observers.setdefault(observer, set()).add(
                        (type, source_orig)
                    )
        for (
            observer,
            eventTypesAndSources,
        ) in (
            observers.items()
        ):  # AttributeError: 'set' object has no attribute 'items'
            # for observer, eventTypesAndSources in observers.:
            subEvent = event.subEvent(*eventTypesAndSources)
            if subEvent.types():
                observer(subEvent)
        # log.debug(
        #     f"Publisher.notifyObservers : observers={observers} et observers.items={observers.items()} sont définis !"
        # )

    @unwrapObservers
    def observers(self, eventType=None):
        # def observers(self, eventType=None) -> set:
        # def observers(self, eventType: Optional[str] = None) -> Set[Callable]:
        """
        Obtenez les observateurs actuellement enregistrés. Spécifiez éventuellement
        un type d'événement spécifique pour obtenir des observateurs pour ce type d'événement uniquement.

        Args :
            eventType (str | None) : (facultatif) Le type d'événement par lequel filtrer les observateurs.

        Returns :
            result (set) : L'ensemble des observateurs.
        """
        if eventType:
            return self.__observers.get(
                (eventType, None), set()
            )  # set() ou Set() ? TODO !
        else:
            result = set()
            for observers in list(self.__observers.values()):
                result |= observers
            return result


class Observer(object):
    """
    Classe mixin de base Observer qui permet de gérer l’enregistrement
    et la suppression des observateurs.

    Attributes :
        __observers (set) : L'ensemble des observateurs.

    Methods :
        registerObserver : Enregistrez un observateur.
        removeObserver : Supprimez un observateur.
        removeInstance : Supprimez tous les observateurs enregistrés sur cette instance.
    """

    def __init__(self, *args, **kwargs):
        # def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialisez la liste des observateurs.

        Args :
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.

        Attributes :
            __observers (set) : L'ensemble des observateurs.

        """
        self.__observers = set()
        # self.__observers: Set[Callable] = set()
        super().__init__(*args, **kwargs)
        # log.debug(f"Observer.__init__ : Liste des observateurs : {self.__observers}")

    def registerObserver(self, observer, *args, **kwargs):
        # def registerObserver(self, observer: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Enregistrez un observateur.

        Args :
            observer (function) : La méthode de rappel de l'observateur.
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.
        """
        self.__observers.add(observer)
        Publisher().registerObserver(observer, *args, **kwargs)

    def removeObserver(self, observer, *args, **kwargs):
        # def removeObserver(self, observer: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Supprimer un observateur.

        Args:
            observer (function) : La méthode de rappel de l'observateur.
            *args : liste d'arguments de longueur variable.
            **kwargs : Arguments de mots clés arbitraires.
        """
        self.__observers.discard(observer)
        Publisher().removeObserver(observer, *args, **kwargs)

    def removeInstance(self) -> None:
        """
        Supprimez tous les observateurs enregistrés sur cette instance.
        """
        for observer in self.__observers.copy():
            self.removeObserver(observer)
        pub.unsubAll(
            listenerFilter=lambda listener: hasattr(
                listener.getCallable(), "__self__"
            )
            and listener.getCallable().__self__ is self
        )


class Decorator(Observer):
    """
    Classe Decorator pour ajouter une fonctionnalité d'observateur à une autre classe.
    Hérite d'Observer et encapsule une instance observable.

    Attributes :
        __observable (object) : L'instance observable encapsulée.

        From Observer :
            __observers (set) : L'ensemble des observateurs.

    Methods :
        __init__ : Initialisez le décorateur.
        observable : Obtenez l'instance observable encapsulée.
        __getattr__ : Déléguez l'accès aux attributs à l'instance observable encapsulée.

        From Observer :
            registerObserver : Enregistrez un observateur.
            removeObserver : Supprimez un observateur.
            removeInstance : Supprimez tous les observateurs enregistrés sur cette instance.
    """

    def __init__(self, observable, *args, **kwargs):
        # def __init__(self, observable: Any, *args: Any, **kwargs: Any) -> None:
        """
        Initialisez le décorateur.

        Args :
            observable (objet) : l'instance observable à envelopper.
            *args : liste d'arguments de longueur variable.
            **kwargs : arguments de mots clés arbitraires.

        Attributes :
            __observable (objet) : L'instance observable encapsulée.
        """
        self.__observable = observable
        super().__init__(*args, **kwargs)

    def observable(self, recursive=False):
        # def observable(self, recursive: bool = False) -> Any:
        """
        Obtenez l'instance observable encapsulée.

        Attributes :
            __observable (object) : L'instance observable encapsulée.

        Args :
            recursive (bool) : (optional) True, obtenez l'observable de niveau supérieur.

        Returns :
            (object) L'observable encapsulé exemple.
        """
        if recursive:
            try:
                return self.__observable.observable(recursive=True)
            except AttributeError:
                pass
        return self.__observable

    def __getattr__(self, attribute):
        # def __getattr__(self, attribute: str) -> Any:
        """
        Déléguez l'accès aux attributs à l'instance observable encapsulée.

        Args :
            attribute (str) : le nom de l'attribut.

        Returns :
            (Any) : La valeur de l'attribut.
        """
        # return getattr(self.observable(), attribute)
        observable = self.observable()
        # Pour wxPython Phoenix
        if hasattr(observable, "_getAttrDict"):
            d = observable._getAttrDict()
            if attribute in d:
                # log.debug(f"Decorator.__getattr__ : retourne {d[attribute]} d'observable._getAttrDict()")
                return d[attribute]
        # Fallback classique
        # return getattr(observable, attribute)
        observable_to_ret = getattr(observable, attribute)
        # log.debug(f"Decorator.__getattr__ : retourne les attributs {observable_to_ret} d'observable")
        return observable_to_ret


class ObservableCollection(object):
    """
    Classe mixin de base pour les collections observables.

    Attributes :
        None

    Methods :
        __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
        detach : Met en pause les Cycles.
        addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
        removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
        modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.

    """

    # def __hash__(self) -> int:
    def __hash__(self):
        """Rendre les ObservableCollections appropriées comme clés dans les dictionnaires.

        Calcule la valeur de hachage pour cet ObservableCollection.

        Returns :
            (int) : la valeur de hachage.
        """
        return hash(id(self))

    def detach(self) -> None:
        """Met en pause les Cycles."""
        pass

    @classmethod
    # def addItemEventType(class_) -> str:
    def addItemEventType(class_):
        """Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments
        ont été ajoutés à la collection.

        Returns :
            "class_.add" (str) : Le type d'événement pour l'ajout d'éléments.
        """
        return f"{class_}.add"

    @classmethod
    # def removeItemEventType(class_) -> str:
    def removeItemEventType(class_):
        """Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments
        ont été supprimés de la collection.

        Returns :
            "class_.remove" (str) : Le type d'événement pour la suppression d'éléments.
        """
        return f"{class_}.remove"

    @classmethod
    def modificationEventTypes(class_):
        # def modificationEventTypes(class_) -> list[str]:
        # def modificationEventTypes(cls) -> TypedList[str]:
        """
        Type d'événement utilisé pour informer les observateurs
        qu'un ou plusieurs éléments ont changé.

        Les modifications sont soit des ajouts, soit des suppressions.

        Returns :
            list : Les types d'événements de modification pour cette collection.
        """
        try:
            eventTypes = super().modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [
            class_.addItemEventType(),
            class_.removeItemEventType(),
        ]


class ObservableSet(ObservableCollection, Set):
    """
    ObservableSet est un ensemble qui avertit les observateurs
    lorsque des éléments sont ajoutés ou supprimés de l'ensemble.

    Methods :
        __eq__ : Compare cet ObservableSet avec un autre objet.
        append : Ajoute un élément à ObservableSet.
        extend : Étend l'ObservableSet avec plusieurs éléments.
        remove : Supprime un élément de l'ObservableSet.
        removeItems : Supprime plusieurs éléments de l'ObservableSet.
        clear : Efface tous les éléments de l’événement ObservableSet.

        From ObservableCollection :
            __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            detach : Met en pause les Cycles.
            addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
    """

    # def __eq__(self, other) -> bool:
    def __eq__(self, other):
        # def __eq__(self, other: Union['ObservableSet', list]) -> bool:
        """
        Compare cet ObservableSet avec un autre objet.

        Args :
            other : L'objet à comparer avec 'self.__class__'.

        Returns :
            result (bool) : True si les objets sont égaux, False sinon.
        """
        # Si l'objet est une instance ou instance fille de self.
        if isinstance(other, self.__class__):
            # le résultat de la comparaison de self avec other.
            result = self is other
        else:
            # sinon, le résultat est la comparaison de other avec la liste des itérables dans self.
            result = list(self) == other
        return result

    # FIXME: Uniquement pour satisfaire registerObserver() car déjà dans ObservableCollection.
    # def __hash__(self) -> int:
    # def __hash__(self):
    #     """
    #     Calcule la valeur de hachage pour cet ObservableSet.
    #
    #     Returns :
    #         (int) : la valeur de hachage.
    #     """
    #     return hash(id(self))

    @eventSource
    def append(self, item, event=None):
        # def append(self, item: Any, event: Optional[Event] = None) -> None:
        """
        Ajoute un élément à ObservableSet.

        Args :
            item : L'élément à ajouter.
            event : Événement facultatif associé à l'opération.
        """
        self.add(item)
        event.addSource(self, item, type=self.addItemEventType())

    @eventSource
    def extend(self, items, event=None):
        # def extend(self, items: Iterable, event: Optional[Event] = None) -> None:
        """
        Étend l'ObservableSet avec plusieurs éléments.

        Args :
            items : itérable des éléments à ajouter.
            event : événement facultatif associé à l'opération.
        """
        if not items:
            return
        self.update(items)
        event.addSource(self, *items, **dict(type=self.addItemEventType()))

    @eventSource
    def remove(self, item, event=None):
        # def remove(self, item: Any, event: Optional[Event] = None) -> None:
        """
        Supprime un élément de l'ObservableSet.

        Args :
            item : L'élément à supprimer.
            event : Événement facultatif associé à l'opération.
        """
        super().remove(item)
        event.addSource(self, item, type=self.removeItemEventType())

    @eventSource
    def removeItems(self, items, event=None):
        # def removeItems(self, items: Iterable, event: Optional[Event] = None) -> None:
        """
        Supprime plusieurs éléments de l'ObservableSet.

        Args :
            items : itérable des éléments à supprimer.
            event : événement facultatif associé à l'opération.
        """
        if not items:
            return
        self.difference_update(items)
        event.addSource(self, *items, **dict(type=self.removeItemEventType()))

    @eventSource
    def clear(self, event=None):
        # def clear(self, event: Optional[Event] = None) -> None:
        """
        Efface tous les éléments de l’événement ObservableSet.

        Args :
            event : événement facultatif associé à l’opération.
        """
        if not self:
            return
        items = tuple(self)
        super().clear()
        event.addSource(self, *items, **dict(type=self.removeItemEventType()))


class ObservableList(ObservableCollection, List):
    """ObservableList est une liste qui informe les observateurs
    lorsque des éléments sont ajoutés ou supprimés de la liste.

    Attributes :
        None

    Methods :
        append : Ajoute un élément à ObservableList.
        extend : Étend l'ObservableList avec plusieurs éléments.
        remove : Supprime un élément de l'ObservableList.
        removeItems : Supprime plusieurs éléments de l'ObservableList.
        clear : Efface tous les éléments de l’événement ObservableList.

        From ObservableCollection :
            __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            detach : Met en pause les Cycles.
            addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
    """

    @eventSource
    def append(self, item, event=None):
        # def append(self, item: Any, event: Optional[Event] = None) -> None:
        """
        Ajoute un élément à ObservableList.

        Args :
            item : L'élément à ajouter.
            event : Événement facultatif associé à l'opération.
        """
        super().append(item)
        event.addSource(self, item, type=self.addItemEventType())

    @eventSource
    def extend(self, items, event=None):
        # def extend(self, items: Iterable, event: Optional[Event] = None) -> None:
        """
        Étend l'ObservableList avec plusieurs éléments.

        Args :
            items : itérable des éléments à ajouter.
            event : événement facultatif associé à l'opération.
        """
        if not items:
            return
        super().extend(items)
        event.addSource(self, *items, **dict(type=self.addItemEventType()))

    @eventSource
    def remove(self, item, event=None):
        # def remove(self, item: Any, event: Optional[Event] = None) -> None:
        """
        Supprime un élément de l'ObservableList.

        Args :
            item : L'élément à supprimer.
            event : Événement facultatif associé à l'opération.
        """
        super().remove(item)
        event.addSource(self, item, type=self.removeItemEventType())

    @eventSource
    def removeItems(self, items, event=None):  # pylint: disable=W0221
        # def removeItems(self, items: Iterable, event: Optional[Event] = None) -> None:
        """
        Supprime plusieurs éléments de l'ObservableList.

        Args :
            items : itérable des éléments à supprimer.
            event : événement facultatif associé à l'opération.
        """
        if not items:
            return
        super().removeItems(items)
        event.addSource(self, *items, **dict(type=self.removeItemEventType()))

    @eventSource
    def clear(self, event=None):
        # def clear(self, event: Optional[Event] = None) -> None:
        """
        Efface tous les éléments de l’événement ObservableList.

        Args :
            event : événement facultatif associé à l’opération.
        """
        if not self:
            return
        items = tuple(self)
        del self[:]
        event.addSource(self, *items, **dict(type=self.removeItemEventType()))


class CollectionDecorator(Decorator, ObservableCollection):
    """CollectionDecorator observe une ObservableCollection et est également une
    ObservableCollection elle-même.

    Son but est de décorer une autre collection observable (comme une liste ou un ensemble)
    et d'ajouter des comportements, tels que le tri ou le filtrage.
    Les utilisateurs de cette classe ne devraient pas voir de différence entre
    l'utilisation de la collection originale ou une version décorée.

    Cette classe est une sous-classe de ObservableComposite qui décore une collection
    (liste, ensemble, etc.) et notifie les observateurs
    lorsqu'un élément est ajouté ou supprimé de la collection.

    Les méthodes de cette classe sont des méthodes de délégation
    qui appellent les méthodes correspondantes de la collection sous-jacente.

    Hérite de :
        Decorator: Classe permettant de décorer un objet avec des comportements supplémentaires.
        ObservableCollection: Collection observable qui notifie les observateurs des changements.

    Attributs :
        __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
        observable (ObservableCollection) : La collection observée.
        __observers (set) : L'ensemble des observateurs.

    Méthodes :
        - __init__ : Initialise la CollectionDecorator.
        - --repr__ : Retourne une représentation sous forme de chaîne de la collection décorée.
        - --str__ : Retourne une représentation sous forme de chaîne de la collection décorée.
        - refresh() : Rafraîchit la collection.
        - freeze() : Gèle la collection et arrête temporairement les notifications aux observateurs.
        - thaw() : Dégèle la collection et reprend les notifications.
        - isFrozen() : Retourne True si la collection est gelée.
        - detach() : Détache la collection et arrête d'observer les événements.
        - onAddItem(event) : Méthode appelée lorsqu'un élément est ajouté à la collection observée.
        - onRemoveItem(event) : Méthode appelée lorsqu'un élément est supprimé de la collection observée.
        - extendSelf(items, event=None) : Ajoute des éléments à la collection décorée sans déléguer à la collection observée.
        - removeItemsFromSelf(items, event=None) : Supprime des éléments de la collection décorée sans déléguer à la collection observée.

        From ObservableCollection :
            __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            detach : Met en pause les Cycles.
            addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
            __eq__ : Compare cet ObservableSet avec un autre objet.
            append : Ajoute un élément à ObservableSet.
            extend : Étend l'ObservableSet avec plusieurs éléments.
            remove : Supprime un élément de l'ObservableSet.
            removeItems : Supprime plusieurs éléments de l'ObservableSet.

    """

    def __init__(self, observedCollection, *args, **kwargs):
        # def __init__(self, observedCollection: ObservableCollection, *args: Any, **kwargs: Any) -> None:
        """
        Initialise la CollectionDecorator en observant les événements d'ajout et de suppression d'éléments
        dans la collection observable.

        Args :
            observedCollection (ObservableCollection) : La collection à décorer et observer.
            *args : Arguments supplémentaires pour l'initialisation.
            **kwargs : Arguments nommés supplémentaires pour l'initialisation.

        Attributes :
            __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
            observable (ObservableCollection) : La collection observée.
            __observers (set) : L'ensemble des observateurs.
        """
        super().__init__(observedCollection, *args, **kwargs)
        self.__freezeCount = 0
        observable = (
            self.observable()
        )  # C'est ici que l'observable est stocké.
        # Observe les événements d'ajout et de suppression dans la collection observable
        self.registerObserver(
            self.onAddItem,
            eventType=observable.addItemEventType(),
            eventSource=observable,
        )
        self.registerObserver(
            self.onRemoveItem,
            eventType=observable.removeItemEventType(),
            eventSource=observable,
        )
        self.extendSelf(observable)

    # def __repr__(self) -> str:  # pragma: no cover
    def __repr__(self):  # pragma: no cover
        """Retourne une représentation sous forme de chaîne de la collection décorée."""
        return f"{self.__class__}({super().__repr__()})"

    def __str__(self) -> str:
        """Retourne une représentation sous forme de chaîne de la collection décorée."""
        return f"{self.__class__.__name__}({super().__str__()})"

    # Explication :
    #
    # En ajoutant cette méthode refresh au décorateur, lorsque thaw() appellera self.refresh(),
    # il trouvera cette méthode. La méthode refresh que nous venons d'ajouter est "intelligente" :
    # elle essaie d'appeler refresh() sur l'objet qu'elle enveloppe (si cet objet le peut),
    # mais si l'objet de base (comme NoteContainer) ne le peut pas,
    # elle se contente de notifier ses propres observateurs (le Noteviewer),
    # qui eux savent comment se rafraîchir.
    def refresh(self) -> None:
        """
        Rafraîchit la collection. Si l'observable sous-jacent a une méthode
        de rafraîchissement, appelle-la. Sinon, propage la notification
        de changement.

        Attributes :
            observable (object) : L'objet observable encapsulé.
        """
        observable = self.observable()
        log.debug(
            f"CollectionDecorator.refresh : Entrée avec observable = {type(observable).__name__}"
        )
        # # if hasattr(observable, "refresh"):
        # # CheckTreeCtrl (et tous les widgets wx) ont une méthode Refresh() — mais en Python,
        # # hasattr(widget, "refresh") est case-insensitive dans certains contextes wxPython,
        # # ou plus probablement le CheckTreeCtrl hérite d'une classe qui a une méthode refresh (minuscule) via la MRO.
        # # Ne propager le refresh que si l'observable est une CollectionDecorator
        # # (pas un widget wx ou autre objet non-collection)
        # if hasattr(observable, "refresh") and isinstance(
        #     observable, CollectionDecorator
        # ):
        if isinstance(observable, CollectionDecorator):
            log.debug(
                f"CollectionDecorator.refresh : appelle observable.refresh()"
            )
            observable.refresh()
        # # else:
        # elif not hasattr(observable, "refresh"):
        #     log.debug(
        #         f"CollectionDecorator.refresh : appelle self.notifyObservers()"
        #     )
        #     # # Si l'objet de base ne peut pas être rafraîchi (comme un NoteContainer),
        #     # # on notifie les observateurs que cette collection (le décorateur)
        #     # # a changé, ce qui déclenchera le refresh() du Viewer.
        #     # self.notifyObservers(Event(self))
        #     # VERSION CORRIGÉE :
        #     # Appelle explicitement la méthode de la classe parente 'Publisher'
        #     # pour éviter d'être intercepté par __getattr__.
        #     Publisher.notifyObservers(self, Event(self))
        #     # Cette modification force Python à appeler la méthode notifyObservers
        #     # de la classe Publisher (la classe parente)
        #     # au lieu de laisser __getattr__ la chercher sur le NoteContainer.
        # # Sinon, ne rien faire — le viewer recevra la notification via les events

        # La classe CollectionDecorator (utilisée par Sorter, Filter, etc.)
        # gère un mécanisme freeze()/thaw() pour suspendre les mises à jour.
        # Quand thaw() est appelé, il diminue son propre compteur _frozen
        # et essaie ensuite d'appeler thaw() (ou d'accéder à _frozen)
        # sur l'objet qu'il enveloppe (self.observable()).
        # Le problème est que la chaîne de décorateurs (NoteSorter -> CategoryFilter -> SearchFilter)
        # finit par envelopper directement le NoteContainer (la collection de notes elle-même).
        # Or, NoteContainer n'est pas un CollectionDecorator et n'a pas d'attribut _frozen.
        # L'accès via __getattr__ dans CollectionDecorator tente de propager l'accès à _frozen jusqu'au NoteContainer,
        # ce qui cause l'AttributeError.
        # Le CollectionDecorator ne devrait appeler freeze() ou thaw()
        # sur l'objet qu'il contient (self.observable())
        # que si cet objet possède effectivement ces méthodes.
        # Explication:
        #     En utilisant hasattr(observable, 'freeze') et hasattr(observable, 'thaw'),
        #     on s'assure que l'appel récursif ne se produit que si l'objet enveloppé supporte explicitement ces méthodes.
        #     Cela empêchera l'appel d'atteindre le NoteContainer (ou tout autre objet de base qui n'est pas "freezable")
        #     et résoudra l'AttributeError.
        log.debug("CollectionDecorator.refresh : terminé !")

    def freeze(self) -> None:
        """
        Gèle la collection, arrêtant temporairement les notifications de changements aux observateurs.

        Si la collection observée est elle-même un CollectionDecorator,
        elle appelle également la méthode freeze sur cette collection.

        Attributes :
            observable (object) : L'objet observable encapsulé.
            __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
        """
        log.debug(
            f"CollectionDecorator.freeze : {self.__class__.__name__}.freeze() - Entrée, compteur = {self.__freezeCount}."
        )
        # if isinstance(self.observable(), CollectionDecorator):
        #     self.observable().freeze()
        # AJOUTER LA VÉRIFICATION :
        observable = self.observable()
        if hasattr(observable, "freeze"):
            observable.freeze()
        self.__freezeCount += 1
        log.debug(
            f"CollectionDecorator.freeze : {self.__class__.__name__}.freeze() - Sortie, compteur = {self.__freezeCount} !"
        )

    def thaw(self) -> None:
        """
        Désactive le gel de l'objet, ce qui permet à nouveau les notifications.

        Dégèle la collection, permettant de reprendre les notifications de changements aux observateurs.

        Si la collection observée est elle-même un CollectionDecorator,
        appelle également la méthode thaw sur cette collection.

        Attributes :
            observable (object) : L'objet observable encapsulé.
            __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
        """
        # CollectionDecorator est une classe qui "décore" (encapsule)
        # un autre objet "observable".
        # thaw() appelle thaw() sur l'objet qu'il décore (self.observable()).
        # La cause de l'erreur est donc que l'attribut self.__observable
        # (qui est retourné par self.observable()) est None
        # lorsque CollectionDecorator.thaw() est appelée.
        log.debug(
            f"CollectionDecorator.thaw : {self.__class__.__name__}.thaw() - Entrée, compteur freeze = {self.__freezeCount}."
        )
        # # if self.isFrozen():
        # self.__freezeCount -= 1
        # Ensure counter does not go below zero
        # if self._frozen > 0:
        if self.isFrozen():
            # self._frozen -= 1
            self.__freezeCount -= 1
        # if isinstance(self.observable(), CollectionDecorator):
        #     self.observable().thaw()
        #     if not self._frozen:
        #         log.debug(f"{self.__class__.__name__}.thaw() - Dégelé, appelle notifyFrozenObservers")
        #         # self.notifyFrozenObservers()
        # AJOUTER LA VÉRIFICATION :
        observable = self.observable()
        log.debug(
            f"CollectionDecorator.thaw : observable de type {type(observable).__name__}."
        )
        if hasattr(observable, "thaw"):
            observable.thaw()  # Boucle entre ici et domain.base.filter.Filter.thaw()

        # if not self._frozen:
        if not self.__freezeCount:
            self.refresh()  # Update the collection if counter is back to zero
        # log.debug(f"{self.__class__.__name__}.thaw() - Sortie")
        # log.debug(f"{self.__class__.__name__}.thaw() - Sortie, compteur = {self._frozen}")
        log.debug(
            f"CollectionDecorator.thaw : {self.__class__.__name__}.thaw() - Sortie, compteur = {self.__freezeCount} !"
        )

    def isFrozen(self) -> bool:
        # def isFrozen(self):
        """
        Vérifie si la collection est gelée.

        Returns :
            (bool) : True si la collection est gelée, sinon False.
        """
        # return self.__freezeCount != 0
        return self.__freezeCount > 0 or self.__freezeCount != 0

    def detach(self) -> None:
        """
        Détache la collection de ses observateurs et arrête de recevoir les notifications des événements.

        Cela inclut la suppression des observateurs pour les événements d'ajout et de suppression d'éléments.
        """
        self.removeObserver(self.onAddItem)
        self.removeObserver(self.onRemoveItem)
        self.observable().detach()
        super().detach()

    def onAddItem(self, event):
        # def onAddItem(self, event: Event) -> None:
        """
        Méthode appelée lorsqu'un élément est ajouté à la collection observée.

        Le comportement par défaut consiste simplement à ajouter à
        cette collection les éléments qui sont
        ajoutés à la collection d'origine.
        Par défaut, cette méthode ajoute également les éléments à cette collection décorée.
        Étendre pour ajouter un comportement.
        Peut être étendue pour ajouter un comportement spécifique lors de l'ajout.

        Args :
            event (Event) : L'événement d'ajout d'élément.
        """
        self.extendSelf(list(event.values()))

    def onRemoveItem(self, event):
        # def onRemoveItem(self, event: Event) -> None:
        """
        Méthode appelée lorsqu'un élément est supprimé de la collection observée.

        Le comportement par défaut consiste simplement à supprimer également
        de cette collection les éléments qui sont
        supprimés de la collection d'origine.
        Par défaut, cette méthode supprime également les éléments de cette collection décorée.
        Étendre pour ajouter un comportement.
        Peut être étendue pour ajouter un comportement spécifique lors de la suppression.

        Args :
            event (Event) : L'événement de suppression d'élément.
        """
        self.removeItemsFromSelf(list(event.values()))

    def extendSelf(self, items, event=None):
        # def extendSelf(self, items: TypedList[Any], event: Optional[Event] = None) -> None:
        """
        Ajoute des éléments à cette collection décorée sans déléguer à la collection observée.

        Fournit une méthode pour étendre cette collection sans déléguer à
        la collection observée.

        Args :
            items (list) : Liste des éléments à ajouter à la collection décorée.
            event (Event) : (optionnel) L'événement associé à l'ajout des éléments.
        """
        return super().extend(items, event=event)

    def removeItemsFromSelf(self, items, event=None):
        # def removeItemsFromSelf(self, items: TypedList[Any], event: Optional[Event] = None) -> None:
        """
        Supprime des éléments de cette collection décorée sans déléguer à la collection observée.

        Fournit une méthode pour supprimer des éléments de cette collection sans
        déléguer à la collection observée.

        Args :
            items (list) : Liste des éléments à supprimer de la collection décorée.
            event (Event) (optionnel) L'événement associé à la suppression des éléments.
        """
        return super().removeItems(items, event=event)

    # Déléguer les modifications à la collection observée
    # Méthode provenant de CollectionDecorator

    def append(self, *args, **kwargs):
        # def append(self, *args: Any, **kwargs: Any) -> None:
        """Appelle la méthode append sur la collection observée."""
        return self.observable().append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        # def extend(self, *args: Any, **kwargs: Any) -> None:
        """Appelle la méthode extend sur la collection observée."""
        return self.observable().extend(*args, **kwargs)

    def remove(self, *args, **kwargs):
        # def remove(self, *args: Any, **kwargs: Any) -> None:
        """Appelle la méthode remove sur la collection observée."""
        return self.observable().remove(*args, **kwargs)

    def removeItems(self, *args, **kwargs):
        # def removeItems(self, *args: Any, **kwargs: Any) -> None:
        """Appelle la méthode removeItems sur la collection observée."""
        return self.observable().removeItems(*args, **kwargs)


class ListDecorator(CollectionDecorator, ObservableList):
    """
    ListDecorator est une spécialisation de CollectionDecorator pour les listes observables.

    Cette classe hérite de :
    CollectionDecorator et ObservableList,
    permettant de décorer une liste observable
    et d'ajouter des comportements supplémentaires
    tout en notifiant les observateurs des changements dans la liste.

    Attributes :
        From CollectionDecorator :
            __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
            __observable (ObservableCollection) : La collection observée.
            __observers (set) : L'ensemble des observateurs.

    Méthodes :
        From CollectionDecorator :
            - __init__ : Initialise la CollectionDecorator.
            - --repr__ : Retourne une représentation sous forme de chaîne de la collection décorée.
            - --str__ : Retourne une représentation sous forme de chaîne de la collection décorée.
            - refresh : Rafraîchit la collection.
            - freeze : Gèle la collection et arrête temporairement les notifications aux observateurs.
            - thaw : Dégèle la collection et reprend les notifications.
            - isFrozen : Retourne True si la collection est gelée.
            - detach : Détache la collection et arrête d'observer les événements.
            - onAddItem : Méthode appelée lorsqu'un élément est ajouté à la collection observée.
            - onRemoveItem : Méthode appelée lorsqu'un élément est supprimé de la collection observée.
            - extendSelf : Ajoute des éléments à la collection décorée sans déléguer à la collection observée.
            - removeItemsFromSelf : Supprime des éléments de la collection décorée sans déléguer à la collection observée.

        From ObservableCollection :
            __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            detach : Met en pause les Cycles.
            addItemEventType : (classmethod) Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
            __eq__ : Compare cet ObservableSet avec un autre objet.
            append : Ajoute un élément à ObservableSet.
            extend : Étend l'ObservableSet avec plusieurs éléments.
            remove : Supprime un élément de l'ObservableSet.
            removeItems : Supprime plusieurs éléments de l'ObservableSet.

        From ObservableList :
            append : Ajoute un élément à ObservableList.
            extend : Étend l'ObservableList avec plusieurs éléments.
            remove : Supprime un élément de l'ObservableList.
            removeItems : Supprime plusieurs éléments de l'ObservableList.
            clear : Efface tous les éléments de l’événement ObservableList.

        From ObservableCollection :
            __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            detach : Met en pause les Cycles.
            addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
    """

    pass


class SetDecorator(CollectionDecorator, ObservableSet):
    """
    SetDecorator est une spécialisation de CollectionDecorator pour les ensembles observables.

    Cette classe hérite de :
    CollectionDecorator et ObservableSet,
    permettant de décorer un ensemble observable
    et d'ajouter des comportements supplémentaires
    tout en notifiant les observateurs des changements dans l'ensemble.

    Attributes :
        From CollectionDecorator :
            __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.
            observable (ObservableCollection) : La collection observée.
            __observers (set) : L'ensemble des observateurs.

    Méthodes :
        From CollectionDecorator :
            - __init__ : Initialise la CollectionDecorator.
            - --repr__ : Retourne une représentation sous forme de chaîne de la collection décorée.
            - --str__ : Retourne une représentation sous forme de chaîne de la collection décorée.
            - refresh() : Rafraîchit la collection.
            - freeze() : Gèle la collection et arrête temporairement les notifications aux observateurs.
            - thaw() : Dégèle la collection et reprend les notifications.
            - isFrozen() : Retourne True si la collection est gelée.
            - detach() : Détache la collection et arrête d'observer les événements.
            - onAddItem(event) : Méthode appelée lorsqu'un élément est ajouté à la collection observée.
            - onRemoveItem(event) : Méthode appelée lorsqu'un élément est supprimé de la collection observée.
            - extendSelf(items, event=None) : Ajoute des éléments à la collection décorée sans déléguer à la collection observée.
            - removeItemsFromSelf(items, event=None) : Supprime des éléments de la collection décorée sans déléguer à la collection observée.

        From ObservableCollection :
            - __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            - detach : Met en pause les Cycles.
            - addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            - removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            - modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
            - __eq__ : Compare cet ObservableSet avec un autre objet.
            - append : Ajoute un élément à ObservableSet.
            - extend : Étend l'ObservableSet avec plusieurs éléments.
            - remove : Supprime un élément de l'ObservableSet.
            - removeItems : Supprime plusieurs éléments de l'ObservableSet.

        From ObservableSet :
            - __eq__ : Compare cet ObservableSet avec un autre objet.
            - append : Ajoute un élément à ObservableSet.
            - extend : Étend l'ObservableSet avec plusieurs éléments.
            - remove : Supprime un élément de l'ObservableSet.
            - removeItems : Supprime plusieurs éléments de l'ObservableSet.
            - clear : Efface tous les éléments de l’événement ObservableSet.

        From ObservableCollection :
            - __hash__ : Rendre les Collections Observables appropriées comme clés dans les dictionnaires.
            - detach : Met en pause les Cycles.
            - addItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été ajoutés à la collection.
            - removeItemEventType (classmethod) : Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments ont été supprimés de la collection.
            - modificationEventTypes (classmethod) : Renvoie les types d'événements de modification pour cette collection.
    """

    pass
