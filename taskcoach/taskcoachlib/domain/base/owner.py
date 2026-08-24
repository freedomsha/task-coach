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

Ce fichier définit une métaclasse qui génère dynamiquement des méthodes
pour gérer des objets de domaine spécifiques.

Rôle de DomainObjectOwnerMetaclass
Pourquoi une métaclasse ?

Objectif : Cette métaclasse permet de créer dynamiquement des méthodes et propriétés pour une classe qui gère un type spécifique d'objets du domaine (ex : Note, Attachment).
Exemple concret :
Si tu as une classe NoteOwner avec __ownedType__ = "Note", la métaclasse va automatiquement ajouter des méthodes comme :

addNote
removeNote
notes
notesChangedEventType
etc.

Comment ça marche ?

Étape 1 : Définition du type géré

La classe qui utilise cette métaclasse doit définir un attribut __ownedType__ (ex : __ownedType__ = "Note").
La métaclasse récupère cette valeur pour générer les noms des méthodes et propriétés.

Étape 2 : Création dynamique des méthodes

Pour chaque type (ex : Note), la métaclasse ajoute :

Méthodes de gestion :
    addNote(obj) → Ajoute un objet Note à la liste interne.
    removeNote(obj) → Supprime un objet Note.
    notes() → Retourne la liste des Note.

Propriétés :
    _notes → Liste interne qui stocke les objets.

Événements :
    notesChangedEventType → Type d'événement déclenché quand la liste change.
    noteAddedEventType → Type d'événement quand un Note est ajouté.
    noteRemovedEventType → Type d'événement quand un Note est supprimé.


Étape 3 : Gestion des observateurs

La métaclasse ajoute aussi une méthode __notifyObservers
pour notifier les observateurs (pattern Observer)
quand un objet est ajouté/supprimé.

Exemple avec NoteOwner
Supposons que tu as :

class NoteOwner(metaclass=DomainObjectOwnerMetaclass):
    __ownedType__ = "Note"

La métaclasse va transformer cette classe en :

class NoteOwner:
    __ownedType__ = "Note"
    _notes = []  # Liste interne

    def addNote(self, note):
        self._notes.append(note)
        self.__notifyObservers(self.noteAddedEventType())

    def removeNote(self, note):
        self._notes.remove(note)
        self.__notifyObservers(self.noteRemovedEventType())

    def notes(self):
        return self._notes

    @property
    def notesChangedEventType(self):
        return f"{self.__ownedType__}sChanged"

    # ... etc.

Qui fait quoi ?

      Couche Métaclasse (DomainObjectOwnerMetaclass)
      Rôle de la métaclasse :
      Crée dynamiquement les méthodes et propriétés pour gérer un type d'objet.
      Exemple : Ajoute addNote, removeNote, etc.

      Couche Classe (NoteOwner, AttachmentOwner)
      Rôle de la classe :
      Utilise les méthodes générées pour manipuler les objets.
      Exemple : note_owner.addNote(my_note)


      Couche Objet du domaine (Note, Attachment)
      Rôle de l'objet :
      Représente une entité métier (ex : une note, une pièce jointe).
      Exemple : my_note = Note(title="Réunion")

Problèmes courants et solutions
Problème 1 : "Je ne vois pas où est définie la méthode addNote !"
Solution :
            Elle est générée dynamiquement par la métaclasse.
            Cherche dans owner.py la partie où la métaclasse ajoute les méthodes
            (ex : setattr(klass, f"add{owned_type_capitalized}", add_method)).

Problème 2 : "Comment déboguer si une méthode ne marche pas ?"
Solution :
            Vérifie que la classe a bien __ownedType__ défini.
            Affiche les attributs de la classe avec dir(NoteOwner) pour voir les méthodes générées.
            Utilise print(NoteOwner.__dict__) pour voir ce qui a été ajouté.

Problème 3 : "C'est trop magique, je veux comprendre le flux !"
Solution :
            Ajoute des print dans la métaclasse pour voir quand les méthodes sont créées.
Exemple :
    print(f"Création de la méthode add{owned_type_capitalized} pour {name}")

"""

# Tu as un pattern hérité Python 2 :
# sérialisation multi-couches via metaclass
# 👉 donc règle stricte :
# 🚨 NE JAMAIS FAIRE :
# . state = {}
# . state = {...} reconstruction manuelle
# . pop() sur les clés du parent

# Étape 1 : Commencer par la version "Safe mais minimal"
#
# Appliquer les 4 règles à Owner, Task, et Category.
# Ajouter les verrous architecturaux (assert, protect_parent_keys) pour éviter les régressions.
# Tester en profondeur : Vérifie que status, id, et les autres clés parent sont toujours présentes.
# → Cela résoudra le bug actuel et te donnera une base solide.

# Étape 2 : Passe à la version "Framework de sérialisation"
#
# Créer un SerializationMixin qui implémente __getstate__ et __setstate__ de manière générique.
# Faire hériter Owner, Task, etc. de ce mixin.
# Supprimer les overrides manuels au fur et à mesure.
# → Cela permettra de scaler sans risque.

# Étape 3 (Optionnelle) : Auto-génération si besoin
#
# Si beaucoup de nouvelles classes >100 ou des règles de sérialisation complexes, passer à l'introspection.

# Python 3.6+ est requis pour les f-strings utilisées dans ce code.
# Python 3 utilise un typage dynamique, ce qui permet de créer des méthodes et des propriétés à la volée.
import logging
from taskcoachlib import patterns
from taskcoachlib.domain.base import Object

log = logging.getLogger(__name__)


# DomainObjectOwnerMetaclass est utilisé par :
# tc/tclib/domain/base/__init__
# tc/tclib/domain/attachment/attachmentowner
# tc/tclib/domain/note/noteowner
# tc/tests/unitests/domainTests/test_domainobjectownermetaclass
# tc/tests/unitests/domainTests/test_owner
def DomainObjectOwnerMetaclass(name, bases, ns):
    """
    Métaclasse pour gérer dynamiquement des objets d'un type particulier.

    Cette métaclasse fait d'une classe le propriétaire de certains objets de domaine.
    Cette métaclasse ajoute des méthodes et propriétés pour un type d'objet
    défini par l'attribut `__ownedType__` dans la classe cible. Exemple :
    si `__ownedType__ = "Note"`, des méthodes comme `addNote`, `removeNote`,
    ou `notesChangedEventType` sont créées automatiquement.

    L'attribut __ownedType__ de la classe doit être une chaîne.
    Pour chaque type, les méthodes suivantes seront ajoutées à la classe
    (en supposant ici un type 'Foo') :

      - __init__, __getstate__, __setstate__, __getcopystate__, __setcopystate__
      - addFoo, removeFoo, addFoos, removeFoos
      - setFoos, foos
      - foosChangedEventType
      - fooAddedEventType
      - fooRemovedEventType
      - modificationEventTypes
      - __notifyObservers

    Args :
        name (str) : Le nom de la classe créé.
        bases (tuple) : Un tuple des classes de base de la classe.
        ns (dict) : Un dictionnaire de l'espace de noms de la classe.

    Returns :
        type : La classe nouvellement créée avec des méthodes et des propriétés ajoutées.

    Raises :
        AttributeError : Si la classe cible n'a pas d'attribut `__ownedType__` ou si ce n'est pas une chaîne.

    Examples :
        class NoteOwner(metaclass=DomainObjectOwnerMetaclass):
            __ownedType__ = "Note"

        note_owner = NoteOwner()
        note_owner.addNote(Note())
        print(note_owner.notes())  # Affiche la liste des notes possédées
        def added_handler(event):
            print("Note ajoutée :", event.sources())

    Utilisé dans AttachmentOwner pour gérer les pièces jointes, et dans NoteOwner pour gérer les notes.

    Objectif : Cette métaclasse permet de créer dynamiquement des méthodes
    et propriétés pour une classe qui gère un type spécifique d'objets du
    domaine (ex : Note, Attachment).

    Exemple concret :
    Si tu as une classe NoteOwner avec __ownedType__ = "Note", la métaclasse va automatiquement ajouter des méthodes comme :

    addNote
    removeNote
    notes
    notesChangedEventType
    etc.

    """
    #
    # print(
    #     f"owner.DomainObjectOwnerMetaclass : pour la classe {name}, avec bases {bases} et ns {ns}."
    # )
    # Cette métaclasse est une fonction au lieu d'une sous-classe de type
    # car comme nous remplaçons __init__, nous ne voulons pas que la métaclasse
    # soit héritée par les enfants.
    # Mais est-ce que la méthode __New__ ne résoud pas ce problème ?
    klass = type(name, bases, ns)

    # Définition du type d'objet géré (donné dans la classe qui l'utilise ! voir NoteOwner ou AttachmentOwner !)
    owned_type = klass.__ownedType__.lower()

    # Si on veux utiliser une classe plutôt qu'une fonction :
    # Avantages :
    # Plus "standard" (utilisation de type).
    # Permet d'utiliser __init__ pour l'initialisation.
    #
    # Inconvénient :
    # La métaclasse sera héritée par les sous-classes (ce que tu veux éviter).
    # Sinon tu désactiver l'héritage dans __new__ ou utiliser un décorateur pour appliquer la métaclass uniquement aux classes que tu veux.
    #
    # class DomainObjectOwnerMetaclass(type):
    #     def __new__(cls, name, bases, ns):
    #         # Désactiver l'héritage en vérifiant bases dans __new__ :
    #         # Vérifier que la classe parente n'est pas déjà une sous-classe
    #         if any(isinstance(base, DomainObjectOwnerMetaclass) for base in bases):
    #             raise TypeError("Cette métaclasse ne peut pas être héritée")
    #         # Récupérer __ownedType__ depuis ns
    #         owned_type = ns.get('__ownedType__')
    #         if not owned_type:
    #             raise AttributeError(f"{name} doit définir __ownedType__")
    #
    #         # Créer la classe avec type.__new__
    #         klass = super().__new__(cls, name, bases, ns)
    #
    #         # Ajouter les méthodes dynamiques (comme dans ta fonction actuelle)
    #         # Exemple : ajouter addNote, removeNote, etc.
    #         def add_method(self, obj):
    #             # Logique pour ajouter un objet
    #             pass
    #         setattr(klass, f"add{owned_type}", add_method)
    #
    #         return klass

    # Définir des méthodes et des propriétés dynamiques pour la classe
    # owned_attr_name = lambda: f"_{name}__{klass.__ownedType__.lower()}s"
    # def owned_attr_name():
    #     return f"_{name}__{klass.__ownedType__.lower()}s"
    # Utilitaire pour générer un nom d'attribut privé
    def _attribute_name(suffix):
        """
        Génère un nom d'attribut privé pour le suffixe donné dans la classe de nom donné pour un type spécifique.

        Args :
            suffix (str) : Le suffixe à ajouter au nom d'attribut.

        Returns :
            str : Le nom d'attribut généré.

        Examples :
            Pour __ownedType__ = "Note", suffix = "foo" et le nom de la classe créé name = "cls",
            retourne le nom de l'attribut "_cls__foonotes"
        """
        log.debug(
            f"owner.DomainObjectOwnerMetaclass._attribute_name : retourne le nom d'attribut _{name}__{suffix}{owned_type}s pour la classe {name}."
        )
        return f"_{name}__{suffix}{owned_type}s"

    # Définir le constructeur
    def constructor(instance, *args, **kwargs):
        """Initialisez l'instance avec la liste des objets possédés.
        (conteneur par défaut : liste)

        Args :
            instance : L'instance initialisée.
            *args : Liste d'argument de longueur variable.
            **kwargs : Arguments de mots clés arbitraires.
        """
        # NB: we use a simple list here. Maybe we should use a container type.
        log.debug(
            f"Owner.constructor : Initialise l'instance avec la liste des objets possédés pour {name}."
        )
        # setattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()),
        #         kwargs.pop(klass.__ownedType__.lower() + "s", []))
        # setattr(instance, owned_attr_name(), kwargs.pop(klass.__ownedType__.lower() + "s", []))
        setattr(
            instance, _attribute_name(""), kwargs.pop(f"{owned_type}s", [])
        )
        log.debug("Owner.constructor : AVANT SUPER :", instance.__dict__)
        # super(klass, instance).__new__(klass)
        super(klass, instance).__init__(*args, **kwargs)
        log.debug("Owner.constructor : APRES SUPER :", instance.__dict__)

    klass.__init__ = constructor

    # # @classmethod
    # def changedEventType(class_):
    #      return "%s.%ss" % (class_, klass.__ownedType__.lower())
    #      return f"{class_}.{klass.__ownedType__.lower()}s"
    #
    # setattr(klass, "%ssChangedEventType" % klass.__ownedType__.lower(),
    #         classmethod(changedEventType))
    #
    # # @classmethod
    # def addedEventType(class_):
    #     return "%s.%s.added" % (class_, klass.__ownedType__.lower())
    #
    # setattr(klass, "%sAddedEventType" % klass.__ownedType__.lower(),
    #         classmethod(addedEventType))
    #
    # # @classmethod
    # def removedEventType(class_):
    #     return "%s.%s.removed" % (class_, klass.__ownedType__.lower())
    #
    # setattr(klass, "%sRemovedEventType" % klass.__ownedType__.lower(),
    #         classmethod(removedEventType))

    # Générer les noms des événements associés
    # Générateurs de types d'événements
    # def generate_event_type(suffix):
    #     return lambda class_: f"{class_}.{klass.__ownedType__.lower()}{suffix}"
    def generate_event_name(event_type):
        """
        Génère le nom d'un événement.

        Args :
            event_type (str) : Le type d'événement.

        Returns :
            str : Le nom de l'événement généré.
        """
        log.debug(
            f"owner.DomainObjectOwnerMetaclass.generate_event_name : génère et retourne le nom de l'événement {klass}.{owned_type}{event_type} pour {name}."
        )
        return f"{klass}.{owned_type}{event_type}"

    # setattr(klass, f"{klass.__ownedType__.lower()}sChangedEventType", classmethod(generate_event_type("s")))
    setattr(
        klass,
        f"{owned_type}sChangedEventType",
        classmethod(lambda cls: generate_event_name("")),
    )
    # setattr(klass, f"{klass.__ownedType__.lower()}AddedEventType", classmethod(generate_event_type(".added")))
    setattr(
        klass,
        f"{owned_type}AddedEventType",
        classmethod(lambda cls: generate_event_name(".added")),
    )
    # setattr(klass, f"{klass.__ownedType__.lower()}RemovedEventType", classmethod(generate_event_type(".removed")))
    setattr(
        klass,
        f"{owned_type}RemovedEventType",
        classmethod(lambda cls: generate_event_name(".removed")),
    )

    # Ajouter les types d'événements de modification
    # @classmethod
    def modificationEventTypes(class_):
        """Renvoie tous les types d’événements liés aux modifications.

        Args :
            class_ : La classe pour laquelle récupérer les types d'événements de modification.

        Returns :
            list : Une liste des types d'événements de modification.
        """
        try:
            eventTypes = super(klass, class_).modificationEventTypes()
        except AttributeError:
            eventTypes = list()
            # eventTypes = []
        # # if eventTypes is None:
        # #     eventTypes = []
        log.debug(
            f"owner.modificationEventTypes : liste des types d’événements liés aux modifications eventTypes = {eventTypes}."
        )
        # parent_events = getattr(super(klass, class_), "modificationEventTypes", lambda: [])()

        # return eventTypes + [changedEventType(class_)]
        # return parent_events + [class_.foosChangedEventType()]
        # return parent_events + [f"{class_}.{klass.__ownedType__.lower()}s"]
        # return parent_events + [generate_event_type("s")]
        # return parent_events + [generate_event_name("")]
        return eventTypes + [generate_event_name("")]

    klass.modificationEventTypes = classmethod(modificationEventTypes)

    # def objects(instance, recursive=False):
    #     ownedObjects = getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()))
    #     result = [ownedObject for ownedObject in ownedObjects
    #               if not ownedObject.isDeleted()]
    #     if recursive:
    #         for ownedObject in result[:]:
    #             result.extend(ownedObject.children(recursive=True))
    #     return result

    # Object management methods
    # Méthode pour récupérer les objets gérés
    def objects(instance, recursive=False):
        """Obtenez la liste des objets possédés, incluant éventuellement leurs enfants.

        Args :
            instance : L'instance pour laquelle récupérer les objets possédés.
            recursive (bool) : Sans inclure les enfants récursivement.

        Returns :
            list : Une liste d'objets possédés.
        """
        # ownedObjects = getattr(instance, "_%s__%ss" % (name, owned_type))
        # owned_objects = getattr(instance, owned_attr_name())
        owned_objects = getattr(instance, _attribute_name(""))

        if owned_objects is None:
            log.debug(
                "DEBUG DomainObjectOwnerMetaclass.objects : owned_objects est None : %s %s %s %s",
                instance,
                type(instance),
                instance.__dict__,
                _attribute_name(""),
            )
        else:
            log.debug(
                "DEBUG DomainObjectOwnerMetaclass.objects : owned_objects est : %s %s %s %s",
                instance,
                type(instance),
                instance.__dict__,
                _attribute_name(""),
            )

        # Filtrer les objets supprimés
        result = [
            obj
            for obj in owned_objects  # TypeError: 'NoneType' object is not iterable  -> corrigé dans tast.py
            if obj is not None and not obj.isDeleted()
        ] or []

        # Inclure les enfants récursivement si nécessaire
        if recursive:
            for obj in result[:]:
                result.extend(obj.children(recursive=True))

        log.debug(
            f"owner.objects : retourne la liste des objets possédés par {name}, incluant éventuellement leurs enfants : {result}"
        )
        return result

    # setattr(klass, "%ss" % klass.__ownedType__.lower(), objects)
    # setattr(klass, f"{klass.__ownedType__.lower()}s", objects)
    setattr(klass, f"{owned_type}s", objects)

    # Méthode pour définir les objets gérés
    @patterns.eventSource
    def setObjects(instance, newObjects, event=None):
        """Définissez la liste des objets possédés et déclenchez des événements en cas de modification.

        Args :
            instance : L'instance pour laquelle définir les objets possédés.
            newObjects (list) : La nouvelle liste des objets possédés.
            event : L'événement à déclencher.
        """
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : \n=== SETOBJECTS ==="
        )
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : ID(instance) = %s",
            id(instance),
        )
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : TYPE(instance) = %s",
            type(instance),
        )
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : DICT = %s",
            instance.__dict__,
        )
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : DEBUG setObjects newObjects = %s",
            newObjects,
        )
        # print("DEBUG setObjects objects(instance) =", objects(instance))
        log.debug(
            "DomainObjectOwnerMetaclass.setObjects : DEBUG attribute name = %s",
            _attribute_name(""),
        )
        log.debug(
            f"DomainObjectOwnerMetaclass.setObjects : DEBUG: setObjects called for {type(instance).__name__}. New objects: {newObjects}"
        )
        current_owned_attr_name = _attribute_name("")
        log.debug(
            f"DomainObjectOwnerMetaclass.setObjects : DEBUG - Value of {current_owned_attr_name} before setattr: {getattr(instance, current_owned_attr_name, 'N/A')}"
        )

        if newObjects == objects(instance):
            log.debug(
                f"DDomainObjectOwnerMetaclass.setObjects : DEBUG - newObjects are the same as current objects. Returning."
            )
            return
        # setattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower()),
        #         newObjects)
        # setattr(instance, owned_attr_name(), newObjects)
        # setattr(instance, _attribute_name(""), newObjects)
        setattr(instance, current_owned_attr_name, newObjects)
        log.debug(
            f"DomainObjectOwnerMetaclass.setObjects : - Value of {current_owned_attr_name} after setattr: {getattr(instance, current_owned_attr_name, 'N/A')}"
        )
        changedEvent(instance, event, *newObjects)  # pylint: disable=W0142

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "set%ss" % klass.__ownedType__, setObjects)
    # setattr(klass, f"set{klass.__ownedType__}s", setObjects)
    # attribute = _attribute_name("")
    attribute = f"set{klass.__ownedType__}s"
    log.debug(
        "DomainObjectOwnerMetaclass.setObjects :  : DEBUG écriture attribut : %s",
        attribute,
    )
    # setattr(instance, attribute, newObjects)
    setattr(klass, attribute, setObjects)
    # print("DEBUG après écriture :", instance.__dict__)
    log.debug(
        "DomainObjectOwnerMetaclass.setObjects : DEBUG après écriture : %s",
        klass.__dict__,
    )

    # Méthodes d'événement : ajout, suppression, changement
    def changedEvent(instance, event, *objects):
        """
        Ajoute un événement modifié à l'événement donné.

        Args :
            instance : L'instance qui possède les objets.
            event : L'événement pour ajouter l'événement modifié.
            *objects : Les objets qui ont changé.
        """
        log.debug(
            f"owner.changedEvent : Ajoute l'événement {objects} modifié à {event}."
        )
        # event.addSource(instance, *objects,
        #                 **dict(type=changedEventType(instance.__class__)))
        event.addSource(instance, *objects, type=generate_event_name(""))
        log.debug(
            f"owner.changedEvent : Événement créé par changedEvent: {event}"
        )

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)
        # NON, pas deux fois !

    # setattr(klass, "%ssChangedEvent" % klass.__ownedType__.lower(), changedEvent)

    def addedEvent(instance, event, *objects):
        """
        Ajoute un événement supplémentaire à l'événement donné.

        Args :
            instance : L'instance qui possède les objets.
            event : L'événement pour ajouter l'événement ajouté.
            *objects : Les objets qui ont été ajoutés.
        """
        # event.addSource(instance, *objects,
        #                 **dict(type=addedEventType(instance.__class__)))
        event.addSource(instance, *objects, type=generate_event_name(".added"))
        log.debug(f"Événement envoyé par addedEvent: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "%sAddedEvent" % klass.__ownedType__.lower(), addedEvent)

    def removedEvent(instance, event, *objects):
        """
        Ajoute un événement supprimé à l'événement donné.

        Args :
            instance : L'instance qui possède les objets.
            event : L'événement pour ajouter l'événement supprimé.
            *objects : Les objets qui ont été supprimés.
        """
        # event.addSource(instance, *objects,
        #                 **dict(type=removedEventType(instance.__class__)))
        event.addSource(
            instance, *objects, type=generate_event_name(".removed")
        )
        log.debug(f"Événement envoyé par removedEvent: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "%sRemovedEvent" % klass.__ownedType__.lower(), removedEvent)

    # Gestionnaires d'événements
    # def create_event_handler(event_type):
    #     return lambda instance, event, *objs: event.addSource(instance, *objs, type=event_type(instance.__class__))
    #
    # # changedEvent = create_event_handler(lambda class_: class_.foosChangedEventType())
    # # changedEvent = create_event_handler(lambda class_: f"{class_}.{klass.__ownedType__.lower()}s")
    # changedEvent = create_event_handler(lambda class_: generate_event_type("s"))
    # # addedEvent = create_event_handler(lambda cls: cls.foosAddedEventType())
    # addedEvent = create_event_handler(lambda class_: generate_event_type(".added"))
    # # removedEvent = create_event_handler(lambda cls: cls.foosRemovedEventType())
    # removedEvent = create_event_handler(lambda class_: generate_event_type(".removed"))

    # Ajouter les méthodes d'événements
    # setattr(klass, f"{klass.__ownedType__.lower()}sChangedEvent", changedEvent)
    setattr(klass, f"{owned_type}sChangedEvent", changedEvent)
    # setattr(klass, f"{klass.__ownedType__.lower()}sAddedEvent", addedEvent)
    setattr(klass, f"{owned_type}sAddedEvent", addedEvent)
    # setattr(klass, f"{klass.__ownedType__.lower()}sRemovedEvent", removedEvent)
    setattr(klass, f"{owned_type}sRemovedEvent", removedEvent)

    # Méthodes d'ajout et de suppression d'objets
    @patterns.eventSource
    def addObject(instance, ownedObject, event=None):
        """Ajouter un seul objet possédé.

        Args :
            instance : L'instance à laquelle l'objet est ajouté.
            ownedObject : L'objet à ajouter.
            event : L'événement à déclencher.
        """
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).append(ownedObject)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}").append(ownedObject)
        # getattr(instance, owned_attr_name()).append(ownedObject)
        getattr(instance, _attribute_name("")).append(ownedObject)
        changedEvent(instance, event, ownedObject)
        addedEvent(instance, event, ownedObject)
        log.debug(f"Événement envoyé par addObject: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "add%s" % klass.__ownedType__, addObject)
    setattr(klass, f"add{klass.__ownedType__}", addObject)

    @patterns.eventSource
    def addObjects(instance, *ownedObjects, **kwargs):
        """Ajoutez plusieurs objets détenus.

        Ajoutez plusieurs objets possédés à l'instance.

        Cette méthode étend la liste des objets propriétaires avec les objets fournis.
        Il déclenche également «Changeevent» et «AddingEvent» pour informer les observateurs du changement.

        Args:
            instance: L'instance à laquelle les objets sont ajoutés.
            *ownedObjects: Nombre variable d'objets propriétaires à ajouter.
            **kwargs:
                event: Objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        if not ownedObjects:
            return
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).extend(ownedObjects)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}s").extend(ownedObjects)
        # getattr(instance, owned_attr_name()).extend(ownedObjects)
        # getattr(instance, _attribute_name("")).append(ownedObjects)  # append(ownedObjects) ajoute un tuple des objets au lieu d'étendre la liste.
        getattr(instance, _attribute_name("")).extend(ownedObjects)
        event = kwargs.pop("event", None)
        changedEvent(instance, event, *ownedObjects)
        addedEvent(instance, event, *ownedObjects)
        log.debug(f"Événement envoyé par addObjects: {event}")

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)

    # setattr(klass, "add%ss" % klass.__ownedType__, addObjects)
    setattr(klass, f"add{klass.__ownedType__}s", addObjects)

    @patterns.eventSource
    def removeObject(instance, ownedObject, event=None):
        """
        Supprimer un seul objet possédé.

        Supprimer un seul objet détenu de l'instance.

        Cette méthode supprime l'objet propriétaire spécifié de la liste des objets possédés.
        Il déclenche également «Changeevent» et «RemovedEvent» pour informer les observateurs du changement.

        Args:
            instance: L'instance à partir de laquelle l'objet est supprimé.
            ownedObject: L'objet possédé à supprimer.
            event: Objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).remove(ownedObject)
        # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}").remove(ownedObject)
        # getattr(instance, owned_attr_name()).remove(ownedObject)
        getattr(instance, _attribute_name("")).remove(ownedObject)
        changedEvent(instance, event, ownedObject)
        removedEvent(instance, event, ownedObject)

        if event is not None:
            # Forcer l'ajout explicite de la source
            event.addSource(instance)
        log.debug(f"Événement envoyé par removeObject: {event}")

    # setattr(klass, "remove%s" % klass.__ownedType__, removeObject)
    setattr(klass, f"remove{klass.__ownedType__}", removeObject)

    @patterns.eventSource
    def removeObjects(instance, *ownedObjects, **kwargs):
        """
        Supprimer plusieurs objets possédés.

        Remove multiple owned objects from the instance.

        Cette méthode supprime les objets propriétaires spécifiés de la liste des objets possédés.
        Il déclenche également «Changeevent» et «RemovedEvent» pour informer les observateurs du changement.

        Args :
            instance : L'instance à partir de laquelle les objets sont supprimés.
            *ownedObjects : Nombre variable d'objets propriétaires à supprimer.
            **kwargs :
                event : Objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        # Vérifier si des objets sont fournis avant de tenter de les supprimer
        if not ownedObjects:
            return
        for ownedObject in ownedObjects:
            try:
                # Récupérer la liste des objets possédés et supprimer l'objet actuel
                # getattr(instance, "_%s__%ss" % (name, klass.__ownedType__.lower())).remove(ownedObject)
                # getattr(instance, f"_{name}__{klass.__ownedType__.lower()}s").remove(ownedObject)
                # getattr(instance, owned_attr_name()).remove(ownedObject)
                getattr(instance, _attribute_name("")).remove(ownedObject)
            except ValueError:
                pass
        # Récupérer l'événement à partir des kwargs pour le passer aux gestionnaires d'événements
        event = kwargs.pop("event", None)
        changedEvent(instance, event, *ownedObjects)
        removedEvent(instance, event, *ownedObjects)

        # Forcer l'ajout explicite de la source
        if event is not None:
            event.addSource(instance)
        log.debug(f"Événement envoyé par removeObjects: {event}")

    # setattr(klass, "remove%ss" % klass.__ownedType__, removeObjects)
    setattr(klass, f"remove{klass.__ownedType__}s", removeObjects)

    # Méthodes de gestion de l'État
    # État de sérialisation
    def getstate(instance):
        """Obtenez l'état de l'objet, y compris les objets possédés.

        Obtenez l'état de l'instance de sérialisation.

        Construit l'état sérialisable de l'objet Owner.

        - Récupère l'état du parent sans le modifier.
        - Ajoute uniquement les objets possédés.
        - Ne supprime aucune clé héritée (status, id, etc.).

        Sérialisation sûre de Owner.

        Règles :
        - ne touche jamais aux clés du parent
        - ajoute uniquement les objets possédés
        - toujours append-only

        Cette méthode renvoie un dictionnaire contenant l'état de l'instance,
        y compris la liste des objets propriétaires.

        Args :
            instance : L'instance pour obtenir l'état de l'objet.

        Returns :
            dict : Un dictionnaire représentant l'état de l'instance.
        """
        # nettoyer correctement, parce que là tu as surtout un mélange dangereux de :
        #
        # debug massif (utile mais qui brouille)
        # double appel super().__getstate__
        # state = {} qui écrase tout héritage
        # clés dynamiques non garanties (foos vs _OwnerUnderTest__foos)
        # et surtout : tu perds les clés du parent
        # 🎯 Objectif du nettoyage
        #
        # On veut :
        # ✔ conserver totalement l’état du parent
        # ✔ ajouter seulement l’attribut “owned”
        # ✔ éviter toute transformation destructive
        # ✔ garantir compatibilité Object.__setstate__ (donc status toujours présent)
        # ✔ supprimer les zones instables
        # # 1. état parent (CRITIQUE : status/id viennent de là)
        # state = safe_super_state(instance, klass)
        # 🔹 Récupère la méthode __getstate__ du parent si elle existe
        # parent_getstate = getattr(super(klass, instance), "__getstate__", None)
        # parent_getstate = instance.safe_super_state(instance, klass)  # TypeError: 'dict' object is not callable
        # parent_getstate = dict(super(klass, instance).__getstate__()) else {}
        parent_getstate = super(klass, instance).__getstate__()
        # parent_getstate = Object.validate_state(
        #     super(klass, instance).__getstate__()
        # )
        log.debug("OWNER parent_getstate = %s", parent_getstate)

        # # Les assertions servent à vérifier que le parent a bien fourni son état.
        # missing = SERIALIZATION_CORE_KEYS - set(parent_getstate.keys())
        #
        # assert not missing, (
        #     f"Sérialisation incomplète dans " f"{klass.__name__}: {missing}"
        # )
        # Vérifier l'état de l'instance avant de l'appeler
        instance.validate_state(parent_getstate)

        # 🔹 Appel du parent ou dictionnaire vide si absent
        # state = parent_getstate() if parent_getstate else {}
        # state = parent_getstate()
        state = dict(parent_getstate)
        # state = parent_getstate.copy()

        # 🔹 Sécurité : on copie pour éviter effets de bord
        state = dict(state)

        # 🔹 Nom de l'attribut privé (ex: _OwnerUnderTest__foos)
        attr_name = _attribute_name("")

        # 🔹 Récupération des objets possédés safe
        owned_objects = getattr(instance, attr_name, [])

        # 🔹 Ajout dans le state SANS supprimer le reste
        state[f"{owned_type}s"] = list(owned_objects)
        # state[f"{owned_type}s"] = list(
        #     getattr(instance, _attribute_name(""), [])
        # )

        Object.protect_parent_keys(parent_getstate, state)

        # 🔹 Debug minimal utile
        log.debug(
            f"[Owner.getstate] {klass.__name__} -> {len(owned_objects)} objets"
        )

        # 🔹 Retour du state complet (parent + owned)
        return state

    klass.__getstate__ = getstate

    @patterns.eventSource
    def setstate(instance, state, event=None):
        """Définissez l'état de l'objet, y compris les objets possédés.

        Définissez l'état de l'instance pendant la désérialisation.

        Reconstruit l'état de l'objet Owner depuis un dictionnaire sérialisé.
        Désérialisation sûre.

        Règles :
        - toujours en premier, appliquer d'abord l'état du parent (Object/SynchronizedObject)
        - puis restauration locale des objets possédés

        Cette méthode définit l'état de l'instance en fonction du dictionnaire
        fourni, y compris la liste des objets possédés.

        Args :
            instance : L'instance pour définir son état.
            state (dict) : Un dictionnaire représentant l'état de l'instance.
            event : Objet d'événement facultatif à passer aux gestionnaires d'événements.
        """
        log.debug("DomainObjectOwnerMetaclass.setstate : AVANT validate_state,")
        log.debug("ID INSTANCE = %s", id(instance))
        log.debug("TYPE = %s", type(instance))
        log.debug(
            f"DEBUG: {name}.__setstate__ - Before parent_setstate. Instance dict: {instance.__dict__}"
        )

        # 🔹 Récupère __setstate__ du parent si existant
        parent_setstate = getattr(super(klass, instance), "__setstate__", None)

        # Les assertions servent à vérifier que le parent a bien fourni son état.
        missing = Object.SERIALIZATION_CORE_KEYS - set(state.keys())

        assert not missing, (
            f"Etat corrompu pour " f"{klass.__name__}: {missing}"
        )

        log.debug("DEBUG setstate state keys: %s", state.keys())
        log.debug("DEBUG recherche: %s", f"{owned_type}s")
        log.debug("DEBUG valeur trouvée: %s", state.get(f"{owned_type}s"))
        log.debug("AVANT parent_setstate")
        log.debug("instance.__dict__.keys(): %s", instance.__dict__.keys())
        log.debug(
            "_Object__subject présent ?",
            "_Object__subject" in instance.__dict__,
        )
        log.debug("instance.__dict__ = %s", instance.__dict__)
        # 🔹 Applique l'état parent (IMPORTANT pour status, id, etc.)
        if parent_setstate:
            parent_setstate(state, event=event)
        log.debug(
            f"DEBUG: {name}.__setstate__ - After parent_setstate. Instance dict: {instance.__dict__}"
        )

        # 🔹 Récupère les objets sérialisés (ex: foos)
        owned_objects = state.get(f"{owned_type}s", [])
        log.debug(
            f"DEBUG: {name}.__setstate__ - Owned objects from state: {owned_objects}"
        )

        current_owned_attr_name = _attribute_name("")
        log.debug(
            f"DEBUG: {name}.__setstate__ - Current internal owned attribute name: {current_owned_attr_name}"
        )
        log.debug(
            f"DEBUG: {name}.__setstate__ - Value of {current_owned_attr_name} before setObjects: {getattr(instance, current_owned_attr_name, 'N/A')}"
        )

        # 🔹 Applique la liste restaurée, injection contrôlée
        # print(
        #     f"DomainObjectOwnerMetaclass.setstate : AVANT setObjects sur {name}, avec owned_objects={owned_objects} et event={event}, instance = {instance}."
        # )
        setObjects(instance, owned_objects, event=event)
        log.debug(
            f"DEBUG: {name}.__setstate__ - Value of {current_owned_attr_name} after setObjects: {getattr(instance, current_owned_attr_name, 'N/A')}"
        )
        log.debug("DomaineObjectOwnerMetaclass.setstate : terminé !")

    klass.__setstate__ = setstate

    def getcopystate(instance):
        """Obtenir une copie de l'état de l'objet.

        Obtenez une copie de l'état de l'instance de copie.

        Cette méthode renvoie un dictionnaire contenant une copie de l'état
        de l'instance, y compris une copie de la liste des objets propriétaires.

        Args :
            instance : L'instance pour obtenir la copie de l'État de l'instance.

        Returns :
            dict : Un dictionnaire représentant une copie de l'état de l'instance.
        """
        # try:
        #     state = super(klass, instance).__getcopystate__()
        # except AttributeError:
        #     state = dict()
        # state = getattr(super(klass, instance), "__getcopystate__", lambda: {})()
        state = (
            super(klass, instance).__getcopystate__()
            if hasattr(super(klass, instance), "__getcopystate__")
            else {}
        )
        # state["%ss" % klass.__ownedType__.lower()] = [
        #     ownedObject.copy() for ownedObject in objects(instance)
        # ]
        # state[klass.__ownedType__.lower() + "s"] = [obj.copy() for obj in objects(instance)]
        state[f"{owned_type}s"] = [obj.copy() for obj in objects(instance)]
        # state["children"] = [child.copy() for child in self.children()]  # Créer de nouveaux objets
        log.debug(f"owner.getcopystate : retourne state : {state}.")
        return state

    klass.__getcopystate__ = getcopystate

    return klass


# # Specific classes are defined here to avoid circular imports
#
#
# class NoteOwner(metaclass=DomainObjectOwnerMetaclass):
#     """ Classe Mixin pour les (autres) objets de domaine pouvant contenir des notes. """
#
#     __ownedType__ = "Note"
#
#     @classmethod
#     def noteAddedEventType(cls):
#         # like taskcoachlib/patterns/observer/addItemEventType
#         # and taskcoachlib/domain/attachment/attachmentowner/attachmentAddedEventType
#         # return '%s.add' % cls
#         pass
#
#     @classmethod
#     def noteRemovedEventType(cls):
#         # like taskcoachlib/patterns/observer/removeItemEventType
#         # and taskcoachlib/domain/attachment/attachmentowner/attachmentRemovedEventType
#         # return '%s.remove' % cls
#         pass
#
#
# class AttachmentOwner(metaclass=DomainObjectOwnerMetaclass):
#     """Classe Mixin pour d'autres objets de domaine pouvant avoir des pièces jointes."""
#
#     __ownedType__ = "Attachment"
