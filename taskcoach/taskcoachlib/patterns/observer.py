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

# from . import singleton
import logging
from collections.abc import Iterable
from taskcoachlib.patterns import singleton
import functools

# from taskcoachlib.thirdparty.pubsub import pub
from pubsub import pub

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
    """

    # def __eq__(self, other: list) -> bool:
    def __eq__(self, other):
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
    """

    def __new__(class_, iterable=None, *args, **kwargs):
        # # return set.__new__(class_, iterable)
        #
        # if iterable is None:
        #     return set.__new__(class_)
        # else:
        #     return set.__new__(class_, iterable)
        #
        if iterable is not None and not isinstance(iterable, Iterable):
            raise TypeError("iterable must be an iterable")
        return set.__new__(class_, iterable)

    def __cmp__(self, other):
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


class Event(object):
    """
    L'événement représente des événements de notification.

    Les événements peuvent notifier un seul type d'événement pour une seule source ou plusieurs types d'événements
    et plusieurs sources en même temps. Les méthodes Event tentent de rendre les deux utilisations
    faciles.

    L'événement représente les événements de notification. Les événements peuvent notifier un seul type d'événement
    pour une seule source ou pour plusieurs types d'événements et plusieurs sources
    en même temps. Les méthodes Event tentent de faciliter les deux utilisations.

    Cela crée un événement pour un type, une source et une valeur
    >> event = Event('event type', 'event source', 'new value')

    Pour ajouter plus de sources d'événements avec leur propre valeur :
    >> event.addSource('une autre source', 'une autre valeur')

    Pour ajouter une source avec un type d'événement différent :
    >> event.addSource('encore une autre source', 'sa valeur', type='un autre type')
    """

    def __init__(self, type=None, source=None, *values):
        """
        Initialisez l'événement.

        Args :
            type (str) : (facultatif) Le type d'événement.
            source (object) : (facultatif) La source de l'événement.
            *values : Valeurs supplémentaires associées à l'événement.
        """
        # self.__sourcesAndValuesByType = {} if type is None else \
        #     {type: {} if source is None else {source: values}}

        # TODO : problème d'utilisation de __sourcesAndValuesByType !
        self.__sourcesAndValuesByType = (
            # dict()
            {}
            if type is None
            else {type: {} if source is None else {source: values}}
            # else {type: dict() if source is None else {source: values}}
        )  # dict or set ?

    # def __repr__(self) -> str:  # pragma: no cover
    def __repr__(self):  # pragma: no cover
        # return "Event(%s)" % (self.__sourcesAndValuesByType,)
        return f"Event({self.__sourcesAndValuesByType})"

    def __eq__(self, other):
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
        # eventType = kwargs.pop('type', self.type())
        # currentValues = set(self.__sourcesAndValuesByType.setdefault(eventType, {}).setdefault(source, tuple()))
        # currentValues |= set(values)
        # self.__sourcesAndValuesByType.setdefault(eventType, {})[source] = tuple(currentValues)

        # TODO : à vérifier problèmes dans les tests
        eventType = kwargs.pop(
            "type", self.type()
        )  # Définit le type d'événement
        # log.debug(f"Event: Ajout de source : {source}, type : {eventType}, valeurs : {values}")
        # currentValues = set(
        #     self.__sourcesAndValuesByType.setdefault(eventType, {}).setdefault(
        #         source, tuple()
        #     )
        # )
        sources = self.__sourcesAndValuesByType.setdefault(
            eventType, {}
        )  # Récupère ou crée le dictionnaire des sources pour le type d'événement
        currentValues = sources.get(
            source, tuple()
        )  # Récupère les valeurs actuelles pour la source, ou une tuple vide si la source n'existe pas
        # self.__sourcesAndValuesByType.setdefault(eventType, {})[source] = (
        #     tuple(currentValues)
        # )
        sources[source] = currentValues + values
        # self.__sourcesAndValuesByType[eventType][source] = tuple(currentValues)

    # def type(self) -> str:
    def type(self):
        """
        Renvoie le type d'événement.

        S'il existe plusieurs types d'événements, cette méthode
        renvoie un type d'événement arbitraire. Cette méthode est utile si
        l'appelant est sûr que cette instance d'événement a exactement un type d'événement.

        Returns :
            (str | none) : Le type d'événement.
        """
        return list(self.types())[0] if self.types() else None

    # def types(self) -> set:
    def types(self):
        """
        Renvoie l'ensemble des types d'événements que cet événement notifie.

        Returns :
            set : L'ensemble des types d'événements.
        """
        return set(self.__sourcesAndValuesByType.keys())

    # def sources(self, *types) -> set:
    def sources(self, *types):
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
            sources |= set(
                self.__sourcesAndValuesByType.get(type, dict()).keys()
            )
            # sources |= set(
            #     self.__sourcesAndValuesByType.get(type, {}).keys()
            # )
        return sources

    # def sourcesAndValuesByType(self) -> dict:
    def sourcesAndValuesByType(self):
        """
        Renvoie toutes les données {type : {source : valeurs}}.

        Returns :
            dict : Les données de l'événement.
        """
        return self.__sourcesAndValuesByType

    # def value(self, source=None, type=None) -> object:
    def value(self, source=None, type=None):
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
        """
        Renvoie les valeurs qui appartiennent à une source.

        Si la source est Aucune, renvoie
        les valeurs d'une source arbitraire. Cette dernière option est utile si
        l'appelant est sûr qu'il n'y a qu'une seule source.

        Args :
            source (object, facultatif) : La source de l'événement.
            type (str, facultatif) : Le type d'événement.

        Returns :
            list : Les valeurs associées à la source.
        """
        type = type or self.type()
        source = source or list(self.__sourcesAndValuesByType[type].keys())[0]
        return self.__sourcesAndValuesByType.get(type, {}).get(source, [])

    def subEvent(self, *typesAndSources):
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

    def send(self):
        """
        Envoyez cet événement aux observateurs du(des) type(s) de cet événement.
        """
        # Publisher().notifyObservers(self)
        if getattr(self, "_sending", False):
            print("Event send : Cycle détecté dans les événements.")
            return
        self._sending = True
        try:
            Publisher().notifyObservers(self)
        finally:
            self._sending = False


def eventSource(f):
    """
    Décorez les méthodes qui envoient des événements avec du code pour éventuellement créer l'événement
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
        event = kwargs.pop("event", None)
        notify = event is None  # We only Notify if we're the event creator
        kwargs["event"] = event = event if event else Event()
        result = f(*args, **kwargs)
        if notify:
            event.send()
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
        """
        Initialisez la méthode MethodProxy.

        Args :
            method (fonction) : La méthode à envelopper.
        """
        self.method = method

    # def __repr__(self) -> str:
    def __repr__(self):
        # return "MethodProxy(%s)" % self.method  # pragma: no cover
        return f"MethodProxy({self.method})"  # pragma: no cover

    def __call__(self, *args, **kwargs):
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
        """
        Récupère l'instance associée à la méthode.

        Renvoie :
            object : L'instance associée à la méthode.
        """
        return self.method.__self__

    im_self = property(get_im_self)
    __self__ = im_self


def wrapObserver(decoratedMethod):
    """
    Enveloppez l'argument de l'observateur (supposé être le premier après self) dans
    une classe MethodProxy.

    Args :
        decoratedMethod (fonction) : La méthode à décorer.

    Returns :
        fonction : La méthode décorée.
    """

    def decorator(self, observer, *args, **kwargs):
        assert hasattr(observer, "__self__")
        observer = MethodProxy(observer)
        return decoratedMethod(self, observer, *args, **kwargs)

    return decorator


def unwrapObservers(decoratedMethod):
    """
    Déballez les observateurs renvoyés de leur classe MethodProxy.

    Args :
        decoratedMethod (fonction) : La méthode à décorer.

    Returns :
        fonction : La méthode décorée.
    """

    def decorator(*args, **kwargs):
        observers = decoratedMethod(*args, **kwargs)
        return [proxy.method for proxy in observers]

    return decorator


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
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'éditeur.
        """
        super().__init__(*args, **kwargs)
        self.clear()
        self.__observers = {}

    def clear(self):
        """
        Effacer le registre des observateurs. Principalement à des fins de tests.
        """
        # observers = {(eventType, eventSource): set(callbacks)}
        try:
            self.__observers.clear()
        except Exception:
            self.__observers = {}  # pylint: disable=W0201

    @wrapObserver
    def registerObserver(self, observer, eventType, eventSource=None):
        """
        Enregistrez un observateur pour un type d'événement. L'observateur est une méthode de rappel
        qui doit attendre un argument, une instance de Event.
        Le eventType peut être n'importe quoi hachable, généralement une chaîne. Lorsque
        passe une source d'événement spécifique, l'observer n'est appelé que lorsque l'événement
        provient de la source d'événement spécifiée.

        Args :
            observer (fonction) : la méthode de rappel de l'observateur.
            eventType (str) : le type d'événement à observer.
            eventSource (object, facultatif) : la source d'événement à observer.
        """
        observers = self.__observers.setdefault(
            (eventType, eventSource), set()
        )
        observers.add(observer)

    @wrapObserver
    def removeObserver(self, observer, eventType=None, eventSource=None):
        """
        Supprimez un observateur. Si aucun type d'événement n'est spécifié, l'observateur
        est supprimé pour tous les types d'événements. Si un type d'événement est spécifié
        , l'observateur est supprimé pour ce type d'événement uniquement. Si aucune source d'événement
        n'est spécifiée, l'observateur est supprimé pour toutes les sources d'événements.
        Si une source d'événement est spécifiée, l'observateur est supprimé pour cette source d'événement
        uniquement. Si un type d'événement et une source d'événement sont
        spécifiés, l'observateur est supprimé pour la combinaison de ce type d'événement spécifique
        et de cette source d'événement uniquement.

        Args :
            observer (fonction) : La méthode de rappel de l'observateur.
            eventType (str, facultatif) : Le type d'événement à arrêter d'observer.
            eventSource (object, facultatif) : La source d'événement à arrêter d'observer.
        """
        # pylint: disable=W0613

        # First, create a match function that will select the combination of
        # event source and event type we're looking for:

        if eventType and eventSource:

            def match(type, source):
                return type == eventType and source == eventSource

        elif eventType:

            def match(type, source):
                return type == eventType

        elif eventSource:

            def match(type, source):
                return source == eventSource

        else:

            def match(type, source):
                return True

        # Next, remove observers that are registered for the event source and
        # event type we're looking for, i.e. that match:
        matchingKeys = [key for key in self.__observers if match(*key)]
        for key in matchingKeys:
            self.__observers[key].discard(observer)
            if not self.__observers[key]:
                del self.__observers[key]

    def notifyObservers(self, event):
        """
        Informer les observateurs de l'événement. Le type et les sources de l'événement sont
        extraits de l'événement.

        Args :
            event (event) : L'événement dont il faut informer les observateurs.
        """
        if not event.sources():
            return
        # log.debug(
        #     f"Publisher.notifyObservers : lancé par {self.__class__.__name__} pour informer les observateurs de l'événement {event} avec sources {event.sources()}."
        # )
        # Recueillir les observateurs *et* les types et sources pour lesquels ils sont enregistrés
        observers = (
            dict()
        )  # {observer: set([(type, source), ...])}  liste set ou dict ? TODO !
        # observers = set()
        types = event.types()
        # Inclure les observateurs non inscrits pour une source d'événement spécifique :
        sources = event.sources() | {None}
        # sources = event.sources() | set([None])
        eventTypesAndSources = [
            (type, source) for source in sources for type in types
        ]
        # log.debug(
        #     f"Publisher.notifyObservers : pour chaque sources {sources} de chaque types {types} récupère {eventTypesAndSources}."
        # )
        for eventTypeAndSource in eventTypesAndSources:
            for observer in self.__observers.get(eventTypeAndSource, set()):
                # for observer in self.__observers.get(eventTypeAndSource, dict()):
                observers.setdefault(observer, set()).add(
                    eventTypeAndSource
                )  # dict() a setdefault ! pas set().
                # observers.setdefault(observer, []).append(eventTypeAndSource)
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
        """
        Obtenez les observateurs actuellement enregistrés. Spécifiez éventuellement
        un type d'événement spécifique pour obtenir des observateurs pour ce type d'événement uniquement.

        Args :
            eventType (str | None) : (facultatif) Le type d'événement par lequel filtrer les observateurs.

        Returns :
            result (set) : L'ensemble des observateurs.
        """
        if eventType:
            return self.__observers.get((eventType, None), set())
        else:
            result = set()
            for observers in list(self.__observers.values()):
                result |= observers
            return result


class Observer(object):
    """
    Classe mixin de base Observer qui permet de gérer l’enregistrement et la suppression des observateurs.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez la liste des observateurs.
        """
        self.__observers = set()
        super().__init__(*args, **kwargs)
        # log.debug(f"Observer.__init__ : Liste des observateurs : {self.__observers}")

    def registerObserver(self, observer, *args, **kwargs):
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
        """
        Supprimer un observateur.

        Args:
            observer (function) : La méthode de rappel de l'observateur.
            *args : liste d'arguments de longueur variable.
            **kwargs : Arguments de mots clés arbitraires.
        """
        self.__observers.discard(observer)
        Publisher().removeObserver(observer, *args, **kwargs)

    def removeInstance(self):
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
    """

    def __init__(self, observable, *args, **kwargs):
        """
        Initialisez le décorateur.

        Args :
            observable (objet) : l'instance observable à envelopper.
        """
        self.__observable = observable
        super().__init__(*args, **kwargs)

    def observable(self, recursive=False):
        """
        Obtenez l'instance observable encapsulée.

        Args :
            recursive (bool) : (optional) True, obtenez l'observable de niveau supérieur.

        Renvoie :
            (object) L'observable encapsulé exemple.
        """
        if recursive:
            try:
                return self.__observable.observable(recursive=True)
            except AttributeError:
                pass
        return self.__observable

    def __getattr__(self, attribute):
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
    Classe mixin de base pour les collections observables."""

    # def __hash__(self) -> int:
    def __hash__(self):
        """Rendre les ObservableCollections appropriées comme clés dans les dictionnaires."""
        return hash(id(self))

    def detach(self):
        """Met en pause les Cycles."""
        pass

    @classmethod
    # def addItemEventType(class_) -> str:
    def addItemEventType(class_):
        """Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments
        ont été ajoutés à la collection."""
        return f"{class_}.add"

    @classmethod
    # def removeItemEventType(class_) -> str:
    def removeItemEventType(class_):
        """Type d'événement utilisé pour informer les observateurs qu'un ou plusieurs éléments
        ont été supprimés de la collection."""
        return f"{class_}.remove"

    @classmethod
    def modificationEventTypes(class_):
        # def modificationEventTypes(class_) -> list[str]:
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
    ObservableSet est un ensemble qui avertit les observateurs lorsque des éléments sont ajoutés ou supprimés de l'ensemble.
    """

    # def __eq__(self, other) -> bool:
    def __eq__(self, other):
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

    # FIXME: Uniquement pour satisfaire registerObserver()
    # def __hash__(self) -> int:
    def __hash__(self):
        """
        Calcule la valeur de hachage pour cet ObservableSet.

        Returns :
            (int) : la valeur de hachage.
        """
        return hash(id(self))

    @eventSource
    def append(self, item, event=None):
        """
        Ajoute un élément à ObservableList.

        Args :
            item : L'élément à ajouter.
            event : Événement facultatif associé à l'opération.
        """
        self.add(item)
        event.addSource(self, item, type=self.addItemEventType())

    @eventSource
    def extend(self, items, event=None):
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
    lorsque des éléments sont ajoutés ou supprimés de la liste."""

    @eventSource
    def append(self, item, event=None):
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
    ObservableCollection elle-même. Son but est de décorer une autre collection observable (comme une liste ou un ensemble)
    et d'ajouter des comportements, tels que le tri ou le filtrage.
    Les utilisateurs de cette classe ne devraient pas voir de différence entre
    l'utilisation de la collection originale ou une version décorée.

    Cette classe est une sous-classe de ObservableComposite qui décore une collection
    (liste, ensemble, etc.) et notifie les observateurs lorsqu'un élément est ajouté ou supprimé de la collection.

    Les méthodes de cette classe sont des méthodes de délégation qui appellent les méthodes correspondantes de la collection sous-jacente.

    Hérite de :
        Decorator: Classe permettant de décorer un objet avec des comportements supplémentaires.
        ObservableCollection: Collection observable qui notifie les observateurs des changements.

    Attributs :
        __freezeCount (int) : Compteur utilisé pour savoir si la collection est gelée (freeze) ou non.

    Méthodes :
        - freeze() : Gèle la collection et arrête temporairement les notifications aux observateurs.
        - thaw() : Dégèle la collection et reprend les notifications.
        - isFrozen() : Retourne True si la collection est gelée.
        - detach() : Détache la collection et arrête d'observer les événements.
        - onAddItem(event) : Méthode appelée lorsqu'un élément est ajouté à la collection observée.
        - onRemoveItem(event) : Méthode appelée lorsqu'un élément est supprimé de la collection observée.
        - extendSelf(items, event=None) : Ajoute des éléments à la collection décorée sans déléguer à la collection observée.
        - removeItemsFromSelf(items, event=None) : Supprime des éléments de la collection décorée sans déléguer à la collection observée.
    """

    def __init__(self, observedCollection, *args, **kwargs):
        """
        Initialise la CollectionDecorator en observant les événements d'ajout et de suppression d'éléments
        dans la collection observable.

        Args :
            observedCollection (ObservableCollection) : La collection à décorer et observer.
            *args : Arguments supplémentaires pour l'initialisation.
            **kwargs : Arguments nommés supplémentaires pour l'initialisation.
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
    def refresh(self):
        """
        Rafraîchit la collection. Si l'observable sous-jacent a une méthode
        de rafraîchissement, appelle-la. Sinon, propage la notification
        de changement.
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

    def freeze(self):
        """
        Gèle la collection, arrêtant temporairement les notifications de changements aux observateurs.

        Si la collection observée est elle-même un CollectionDecorator,
        elle appelle également la méthode freeze sur cette collection.
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

    def thaw(self):
        """
        Désactive le gel de l'objet, ce qui permet à nouveau les notifications.

        Dégèle la collection, permettant de reprendre les notifications de changements aux observateurs.

        Si la collection observée est elle-même un CollectionDecorator,
        appelle également la méthode thaw sur cette collection.
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

    # def isFrozen(self) -> bool:
    def isFrozen(self):
        """
        Vérifie si la collection est gelée.

        Returns :
            (bool) : True si la collection est gelée, sinon False.
        """
        # return self.__freezeCount != 0
        return self.__freezeCount > 0 or self.__freezeCount != 0

    def detach(self):
        """
        Détache la collection de ses observateurs et arrête de recevoir les notifications des événements.

        Cela inclut la suppression des observateurs pour les événements d'ajout et de suppression d'éléments.
        """
        self.removeObserver(self.onAddItem)
        self.removeObserver(self.onRemoveItem)
        self.observable().detach()
        super().detach()

    def onAddItem(self, event):
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

    def append(self, *args, **kwargs):
        """Appelle la méthode append sur la collection observée."""
        return self.observable().append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        """Appelle la méthode extend sur la collection observée."""
        return self.observable().extend(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """Appelle la méthode remove sur la collection observée."""
        return self.observable().remove(*args, **kwargs)

    def removeItems(self, *args, **kwargs):
        """Appelle la méthode removeItems sur la collection observée."""
        return self.observable().removeItems(*args, **kwargs)


class ListDecorator(CollectionDecorator, ObservableList):
    """
    ListDecorator est une spécialisation de CollectionDecorator pour les listes observables.

    Cette classe hérite de CollectionDecorator et ObservableList, permettant de décorer une liste observable
    et d'ajouter des comportements supplémentaires tout en notifiant les observateurs des changements dans la liste.
    """

    pass


class SetDecorator(CollectionDecorator, ObservableSet):
    """
    SetDecorator est une spécialisation de CollectionDecorator pour les ensembles observables.

    Cette classe hérite de CollectionDecorator et ObservableSet, permettant de décorer un ensemble observable
    et d'ajouter des comportements supplémentaires tout en notifiant les observateurs des changements dans l'ensemble.
    """

    pass
