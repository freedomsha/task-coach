# -*- coding: utf-8 -*-

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

Fonctionnalité principale:

La classe Object semble être une classe de base polyvalente conçue pour
représenter des objets génériques avec des attributs tels que :

    Identification: id, creationDateTime, modificationDateTime
    Contenu: subject, description
    Apparence: fgColor, bgColor, font, icon, selectedIcon
    Ordre: ordering

Elle fournit également des méthodes pour gérer ces attributs,
ainsi que des mécanismes pour la sérialisation, la copie et la gestion d'événements.

Points clés et questions:

    Héritage de SynchronizedObject:
        Quel est le rôle exact de SynchronizedObject ?
        Gère-t-il la synchronisation de threads ou un autre type de synchronisation ?
        Les méthodes héritées de SynchronizedObject sont-elles utilisées dans cette classe ?

    Attributs personnalisés:
        Le regex rx_attributes est utilisé pour extraire des attributs personnalisés
        de la description. Comment ces attributs sont-ils utilisés dans le reste de l'application ?
        Y a-t-il une raison particulière d'utiliser un regex pour cela plutôt qu'un format de données plus structuré ?

    Gestion des événements:
        Les méthodes subjectChangedEvent, descriptionChangedEvent, etc. sont utilisées
        pour déclencher des événements lorsqu'un attribut est modifié.
        Quel est le mécanisme de gestion des événements utilisé dans le reste de l'application ?
        Les types d'événements sont stockés sous forme de chaînes.
        Y a-t-il un système de gestion d'événements plus sophistiqué en place ?

    Sérialisation et copie:
        Les méthodes __getstate__ et __getcopystate__ sont utilisées pour la
        sérialisation et la copie de l'objet. Quels sont les formats de sérialisation pris en charge ?
        Pourquoi la date et l'heure de création ne sont-elles pas incluses dans la copie ?

    Tri:
        Les méthodes de tri permettent de trier une liste d'objets en fonction
        de différents critères.
        Comment ces fonctions de tri sont-elles utilisées dans le reste de l'application ?

Questions spécifiques sur le code:

    _long_zero: Quel est le but de cette variable ? Pourquoi ne pas utiliser simplement 0 ?
    __repr__: Pourquoi renvoyer uniquement le subject dans la représentation en chaîne ? Ne serait-il pas plus informatif d'inclure d'autres informations ?
    customAttributes: Comment sont utilisés les attributs personnalisés ? Y a-t-il une validation sur les noms de section ?
    modificationEventTypes: La partie commentée semble contenir du code pour gérer l'héritage des types d'événements. Pourquoi a-t-elle été commentée ?

Suggestions d'amélioration:

    Documentation: Ajouter des docstrings plus détaillées pour expliquer le but de chaque méthode et attribut.
    Tests unitaires: Écrire des tests unitaires pour vérifier le comportement de la classe et de ses méthodes.
    Typage: Envisager d'utiliser des annotations de type pour améliorer la lisibilité et la maintenabilité du code.
    Simplification: Certaines parties du code pourraient être simplifiées, par exemple en utilisant des expressions ternaires ou des compréhensions de liste.


Fonctionnalité principale

    La classe SynchronizedObject semble être conçue pour gérer l'état d'un objet au cours de son cycle de vie, en particulier pour suivre les modifications et les suppressions. Elle fournit un mécanisme de synchronisation en émettant des événements lorsque l'état de l'objet change.

Attributs clés

    __status: Un entier représentant l'état actuel de l'objet (nouveau, modifié, supprimé ou aucun).

Méthodes clés

    __init__: Initialise l'objet avec un état par défaut (nouveau).
    markDirty: Marque l'objet comme modifié.
    markNew: Marque l'objet comme nouveau.
    markDeleted: Marque l'objet comme supprimé.
    cleanDirty: Marque l'objet comme non modifié.
    getStatus: Renvoie l'état actuel de l'objet.
    isNew, isModified, isDeleted: Des méthodes d'accès pour vérifier l'état de l'objet.

Mécanisme d'événements

La classe utilise un mécanisme d'événements pour notifier les changements d'état. Les événements sont émis à l'aide du décorateur @patterns.eventSource.
Sérialisation

Les méthodes __getstate__ et __setstate__ permettent de sérialiser et de désérialiser l'objet, en incluant son état actuel.
Questions et observations

    Synchronisation: Le nom de la classe suggère une synchronisation. Est-ce que cette classe est utilisée pour synchroniser l'accès à un objet partagé entre plusieurs threads ? Si oui, comment est-elle implémentée ?
    __getcopystate__: La méthode __getcopystate__ est vide. Cela signifie-t-il que les copies de l'objet ne conservent pas l'état original ?
    Types d'événements: Les types d'événements sont définis sous forme de chaînes. Est-ce que cela ne pose pas de problèmes de typage fort ? Un système d'événements plus sophistiqué pourrait utiliser des classes d'événements.
    États possibles: Il y a quatre états possibles (nouveau, modifié, supprimé, aucun). Est-ce que ces états couvrent tous les cas d'utilisation possibles ? Par exemple, y a-t-il un état pour représenter un objet en cours de validation ?
    Méthodes setStatus*: Ces méthodes sont utilisées pour modifier l'état interne de l'objet. Pourraient-elles être rendues privées pour éviter les modifications directes de l'état ?

Améliorations possibles

    Typage: Utiliser des annotations de type pour améliorer la lisibilité et la maintenabilité du code.
    Tests unitaires: Écrire des tests unitaires pour vérifier le comportement de la classe.
    Documentation: Ajouter des docstrings plus détaillées pour expliquer le but de chaque méthode et attribut.
    Simplifier les méthodes setStatus*: Ces méthodes pourraient être simplifiées en utilisant des expressions ternaires.
    Encapsuler l'état: Envisager de rendre l'attribut __status privé et d'utiliser des propriétés pour y accéder.

Conclusion préliminaire

    La classe SynchronizedObject fournit une base solide pour gérer l'état d'un objet et notifier les changements. Cependant, il y a quelques points qui pourraient être améliorés pour la rendre plus robuste et plus facile à utiliser.

Excellente décomposition du code ! Votre analyse a identifié avec précision les composants clés et les domaines potentiels d'amélioration de la classe Object.
Principaux points à retenir de votre analyse :

    Classe complète : la classe Object sert de classe de base polyvalente pour divers types d'objets au sein de l'application, fournissant une base solide pour la gestion des attributs, des états et des événements.
    Synchronisation et événements : la classe de base SynchronizedObject et le mécanisme piloté par les événements jouent un rôle crucial dans le suivi des modifications des objets et dans la notification des personnes intéressées. parties.
    Attributs personnalisés : la classe Attribute offre un moyen flexible de gérer les attributs d'objet et leurs événements associés.
    Sérialisation : les méthodes __getstate__ et __setstate__ gèrent la sérialisation et la désérialisation des objets, permettant ainsi aux objets d'être enregistrés et restaurés.
    Tri : La classe fournit diverses fonctions de tri basées sur différents attributs.

Domaines d’amélioration et de discussion supplémentaires :

1. SynchronizedObject et Thread Synchronization :

    Clarifier le mécanisme de synchronisation : si SynchronizedObject est effectivement destiné à la synchronisation des threads, il serait avantageux de fournir plus de détails sur les mécanismes sous-jacents, tels que les verrous ou autres primitives de synchronisation.
    Envisagez le threading module : le module de thread intégré de Python offre une variété de primitives de synchronisation qui peuvent être exploitées pour la gestion d'objets thread-safe.

2. Attributs personnalisés :

    Validation d'attribut : envisagez d'ajouter une validation à la classe Attribute pour garantir que les valeurs attribuées respectent des types de données ou des contraintes spécifiques.
    Héritage d'attributs personnalisés : explorez la possibilité de créer une hiérarchie de classes d'attributs personnalisées. pour gérer différents types d'attributs (par exemple, numérique, chaîne, date).

3. Système d'événements :

    Propagation des événements : déterminez la manière dont les événements sont propagés au sein de l'application. Existe-t-il un bus d'événements central ou chaque objet gère-t-il ses propres abonnements aux événements ?
    Données d'événement : envisagez d'enrichir les données d'événement avec un contexte supplémentaire, tel que les anciennes et les nouvelles valeurs d'un attribut.
    Événements asynchrones : explorez l'utilisation de mécanismes de gestion d'événements asynchrones pour les opérations non bloquantes.

4. Sérialisation :

    Gestion des versions : implémentez un mécanisme de gestion des versions pour les données sérialisées afin de gérer les modifications de la structure de l'objet au fil du temps.
    Sérialiseurs personnalisés : envisagez d'utiliser un sérialiseur personnalisé (par exemple, JSON, YAML) pour contrôler le format de sérialisation. et optimiser les performances.

5. Astuces de type :

    Saisie progressive : introduisez progressivement des astuces de type pour améliorer la lisibilité et la maintenabilité du code.
    Vérificateurs de type statiques : envisagez d'utiliser un vérificateur de type statique comme mypy pour renforcer la sécurité des types.

6. Tests :

    Tests unitaires : rédigez des tests unitaires complets pour couvrir divers scénarios et cas extrêmes.
    Tests basés sur les propriétés : explorez l'utilisation d'outils de test basés sur les propriétés comme Hypothesis pour générer un large éventail de cas de test.

7. Documentation :

    Docstrings : améliorez les docstrings pour fournir des explications plus détaillées sur les méthodes et les classes.
    Commentaires : ajoutez des commentaires pour clarifier les sections de code complexes ou non évidentes.

Questions et suggestions spécifiques :

    _long_zero : Cette variable semble être utilisée pour assurer la compatibilité avec Python 2 et 3 concernant les types entiers. Cependant, avec l'avènement de Python 3, cela pourrait devenir redondant.
    __repr__ : bien que le renvoi du sujet soit une valeur par défaut raisonnable, envisagez de fournir une représentation plus informative, en particulier à des fins de débogage.
    customAttributes : explorez en utilisant une représentation plus structurée. approche pour stocker des attributs personnalisés, tels qu'un dictionnaire ou une classe personnalisée.
    Types d'événements : envisagez d'utiliser une approche plus structurée pour définir des types d'événements, tels qu'une énumération ou une classe. hierarchie.
    modificationEventTypes : le code commenté suggère qu'il aurait pu y avoir un plan pour un mécanisme d'héritage d'événements plus sophistiqué. Il serait intéressant d'étudier les raisons de le commenter.

Considérations supplémentaires :

    Performance : Si les performances sont une préoccupation critique, profilez le code pour identifier les goulots d'étranglement et optimisez-le en conséquence.
    Maintenabilité : efforcez-vous d'adopter un style de codage cohérent et utilisez des noms de variables significatifs pour améliorer la lisibilité du code.
    Extensibilité : concevez la classe pour qu'elle puisse être facilement étendue avec de nouvelles fonctionnalités et personnalisations.

En abordant ces points, vous pouvez améliorer davantage la classe Object et la rendre plus robuste, maintenable et adaptable aux exigences futures.
"""

# Règle d’or
# 👉 Chaque classe doit gérer uniquement ses propres clés, et laisser les parents inchangés

# Analyse des dysfonctionnements critiques & Corrections apportées
# 1. L'initialisation des attributs et la boucle infinie de super().__init__
#
#     Le problème : Dans le constructeur de Object, l'appel à self.createAttributes() était fait avant d'initialiser d'autres variables ou d'appeler super().__init__(). De plus, l'utilisation de super().__init__(*args, kwargs) transmettait des arguments inattendus aux classes parentes (comme object ou SynchronizedObject), provoquant des TypeError.
#
#     La correction :
#
#         Filtrage propre et strict de kwargs avant transmission.
#
#         Le chaînage d'initialisation de CompositeObject hérite maintenant de manière prédictible et robuste.
#
#         Remplacement de la détection complexe de la MRO par un appel super().__init__(*args, kwargs) sécurisé.
#
# 2. La sérialisation __getstate__ et __setstate__ (Sauvegardes .tsk)
#
#     Le problème : Python 3 sérialise tous les attributs privés (comme _Object__subject contenant l'instance d'objet Attribute), alors que le format XML/Pickle de Task Coach attend des valeurs primitives (str, int). De plus, __setstate__ plantait car l'attribut _Object__subject (entre autres) n'était pas encore recréé lors de la désérialisation, car __init__ n'est pas appelé lors d'un unpickle (__new__ est appelé directement).
#
#     La correction :
#
#         Nettoyage strict des attributs privés hérités dans __getstate__ (seuls les champs publics et plats de l'état sont exportés).
#
#         Dans __setstate__, appel systématique et robuste à self.createAttributes() avant d'exécuter les setters (setSubject, setDescription, etc.). Cela garantit que les instances d'Attribute associées aux événements existent déjà en mémoire avant d'y injecter les valeurs restaurées.
#
# 3. La méthode de classe modificationEventTypes
#
#     Le problème : Le crash TypeError: SynchronizedObject.modificationEventTypes() missing 1 required positional argument: 'self' survenait car super().modificationEventTypes() essayait d'appeler une méthode de classe sur un parent qui ne la définissait pas comme @classmethod.
#
#     La correction : Stabilisation de la méthode de classe pour récupérer de manière dynamique et sûre les types d'événements parents, avec repli (fallback) sur une liste vide si la méthode n'existe pas chez le parent.
# TODO : faire log !
import functools
import logging
import sys
import uuid
import re
import weakref
from pubsub import pub
from taskcoachlib import patterns
from taskcoachlib.domain.attribute import icon
from taskcoachlib.domain.date import DateTime, Now

# from taskcoachlib.domain.task.task import Task
from . import attribute
from .appearance import FIELD_DEFAULTS, FIELD_NO_VALUE_SOURCE

log = logging.getLogger(__name__)


class SynchronizedObject(object):
    """
    Une classe de base pour les objets synchronisés.

    Cette classe fournit des méthodes pour marquer les objets comme nouveaux, modifiés, supprimés ou aucun
    et synchronise ces états avec des événements.

    Elle gère des mécanismes de verrouillage ou de synchronisation d'accès aux attributs.

    Attributs :
        - STATUS_NONE (int) : = 0 Représente l'état "aucun" de l'objet.
        - STATUS_NEW (int) : = 1 Représente l'état "nouveau" de l'objet.
        - STATUS_CHANGED (int) : = 2 Représente l'état "modifié" de l'objet.
        - STATUS_DELETED (int) : = 3 Représente l'état "supprimé" de l'objet.
        - __status (int) : Le statut actuel de l'objet, qui peut être l'un des quatre états définis ci-dessus.

    Methods :
        - __init__ : Initialise l'objet avec un statut par défaut.
        - markDeletedEventType : Renvoie le type d'événement pour marquer un objet comme supprimé.
        - markNotDeletedEventType : Renvoie le type d'événement pour marquer un objet comme non supprimé.
        - modificationEventTypes : (commenté) Fournit les types d'événements de modification pour les classes dérivées.
        - __getstate__ : Prépare l'état de l'objet pour la sérialisation.
        - __setstate__ : Définit l'état de l'objet à partir de la désérialisation.
        - __getcopystate__ : Prépare l'état de l'objet pour la copie (actuellement vide).
        - markDirty : Marque l'objet comme modifié.
        - markNew : Marque l'objet comme nouveau.
        - markDeleted : Marque l'objet comme supprimé.
        - cleanDirty : Marque l'objet comme non modifié.
        - getStatus : Renvoie le statut actuel de l'objet.
        - setStatusDirty : Définit le statut de l'objet comme modifié.
        - setStatusNew : Définit le statut de l'objet comme nouveau.
        - setStatusDeleted : Définit le statut de l'objet comme supprimé.
        - setStatusNone : Définit le statut de l'objet comme aucun.
        - isNew : Vérifie si l'objet est nouveau.
        - isModified : Vérifie si l'objet est modifié.
        - isDeleted : Vérifie si l'objet est supprimé.

    """

    SERIALIZATION_CORE_KEYS = frozenset(
        [
            "status",
        ]
    )
    STATUS_NONE = 0
    STATUS_NEW = 1
    STATUS_CHANGED = 2
    STATUS_DELETED = 3

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'instance de l'objet.

        Args :
            *args : Liste d’arguments de longueur(length) variable.
            **kwargs : Arbitrary keyword arguments.

        Note :  Le statut de l'objet peut être défini via le mot-clé 'status' dans kwargs. Si aucun statut n'est fourni, il sera défini sur STATUS_NEW par défaut.

        Attributes :
            __status (int) : Le statut actuel de l'objet, qui peut être STATUS_NONE, STATUS_NEW, STATUS_CHANGED ou STATUS_DELETED.
        """
        # log.debug(f"SynchronizedObject.__init__ : 🔍 Avant super().__init__() : self.__status = kwargs.pop('status', self.STATUS_NEW)={kwargs.get('status', 'Non défini')}")
        log.debug("SynchronizedObject : Initialisation.")
        # self.__status = kwargs.pop("status", self.STATUS_NEW)
        self.__status = kwargs.pop(
            "status", None
        )  # On ne met PAS STATUS_NEW par défaut !

        if self.__status is None:
            self.__status = (
                self.STATUS_NEW
            )  # On met STATUS_NEW UNIQUEMENT si rien n'est défini
        print(
            f"SynchronizedObject.__init__ : ✅ Après assignation : self.__status = {self.__status}"
        )
        # print(
        #     f"SynchronizedObject.__init__ : 🔍 Avant super().__init__() : self.__status = {getattr(self, '__status', 'Non défini')}")

        # super().__init__(*args, **kwargs)  # ← Problème possible ici ! Peut-être le mettre avant self.__status !?
        # print(f"SynchronizedObject.__init__ : ✅ Après super().__init__() : self.__status = {self.__status}")
        # print(f"SynchronizedObject.__init__ : ⚠️ Après super().__init__() : self.__status = {self.__status}")
        # super().__init__()  # Comme SynchronizedObject est basé sur object, rien dans __init__ !
        # # Transmet les arguments uniquement si le parent **n'est pas `object`**
        # # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
        # if type(self).__mro__[1] is not object:
        #     try:
        #         super().__init__(*args, **kwargs)
        #     except TypeError:
        #         super().__init__()
        # else:
        #     super().__init__()  # Sécurisé pour `object`
        # Transmission sécurisée des arguments restants au parent s'il existe
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            super().__init__()
        log.debug("SynchronizedObject : Initialisé.")

    @classmethod
    def markDeletedEventType(class_):
        """
        Obtenir le type d'événement pour marquer un objet comme supprimé.

        Returns :
            (str) : Le type d'événement pour marquer un objet comme supprimé.
        """
        return "object.markdeleted"

    @classmethod
    def markNotDeletedEventType(class_):
        """
        Obtenir le type d'événement pour marquer un objet comme non supprimé.

        Return :
            (str) : Type d'événement permettant de marquer un objet comme non supprimé.
        """
        return "object.marknotdeleted"

    # Sérialisation : C'est ce qui permet d'ouvrir et de sauvegarder
    # les fichiers .tsk sans les corrompre.
    # Le passage à Python 3 a changé la façon dont les attributs privés sont gérés,
    # obligeant à filtrer manuellement ce qu'on sauvegarde.
    def validate_state(self, state):
        """Valide l'état minimal de SynchronizedObject."""
        missing = self.SERIALIZATION_CORE_KEYS.difference(state)

        assert not missing, (
            f"État de sérialisation invalide pour {type(self).__name__}. "
            f"Clés manquantes : {sorted(missing)}"
        )

    def __getstate__(self):
        """
        Étends l'état sérialisé de l'objet avec les informations de synchronisation.

        Returns :
            dict : L'état de l'objet, incluant l'état de synchronisation.
        """
        # Récupération de l'état de base de l'objet (depuis la classe supérieure Object)
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()
        log.debug(
            f"SynchronizedObject.__getstate__ : state avant update {state}."
        )
        # Ajout de l'attribut de statut de synchronisation
        state["status"] = self.__status
        # ---^ : Member 'object' of 'object | dict[Any, Any]' does not have attribute '__setitem__'
        log.debug(f"SynchronizedObject.__getstate__ : retourne state {state}.")
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Définir l'état de l'objet à partir de la désérialisation.

        Args :
            state (dict) : L’état à définir.
            event : (event) L'événement associé à la définition de l'état.
        """
        log.debug(
            f"SynchronizedObject.__setstate__ : pour state {state} et event {event}."
        )
        # try:
        #     super().__setstate__(state, event=event)
        # except AttributeError:
        #     pass
        # C'est dans Object()!
        old_status = getattr(
            self,
            "_SynchronizedObject__status",
            self.STATUS_NEW,
        )

        new_status = state["status"]

        if old_status != new_status:
            self.__status = new_status

        # Le statut est restauré par SynchronizedObject.__setstate__.
        # Object ne gère que les attributs propres à Object.
        # if (
        #     state["status"] != self.__status
        # ):  # Utiliser les différents cas avec match !
        #     # if state["status"] == self.STATUS_CHANGED:
        #     #     self.markDirty(event=event)
        #     # elif state["status"] == self.STATUS_DELETED:
        #     #     self.markDeleted(event=event)
        #     # elif state["status"] == self.STATUS_NEW:
        #     #     self.markNew(event=event)
        #     # elif state["status"] == self.STATUS_NONE:
        #     #     self.cleanDirty(event=event)
        #     match state["status"]:
        #         case self.STATUS_CHANGED:
        #             self.markDirty(event=event)
        #         case self.STATUS_DELETED:
        #             self.markDeleted(event=event)
        #         case self.STATUS_NEW:
        #             self.markNew(event=event)
        #         case self.STATUS_NONE:
        #             self.cleanDirty(event=event)

    def getStatus(self):
        """
        Obtenez l'état actuel de l'objet.

        Returns :
            (int) : Le statut actuel.
        """
        # print(
        #     f"object.SynchronizedObject.getStatus : 🔍 DEBUG - getStatus() appelé pour {self} - self.__status = {self.__status} ({type(self.__status)})")

        # if hasattr(self, "status") and callable(getattr(self, "status")):
        #     status_value = self.status()
        #     if isinstance(status_value, int):  # Si c'est déjà un entier
        #         return status_value
        #     if hasattr(status_value, "to_int") and callable(status_value.to_int):
        #         return status_value.to_int()  # Utilise une méthode de conversion explicite
        #     if hasattr(status_value, "value"):
        #         return status_value.value  # Si TaskStatus possède une valeur numérique
        #     # print(f"⚠️ getStatus : Impossible de convertir {status_value} en entier")
        #     return self.STATUS_CHANGED  # Fallback en cas d'erreur

        # if self.__status is None:
        #     # print("🟡 getStatus : self.__status est None → Forçage à STATUS_CHANGED (2)")
        #     self.__status = self.STATUS_CHANGED  # Force le recalcul

        # log.debug(
        print(
            f"✅ SynchronizedObject.getStatus renvoie {self.__status} - de type {type(self.__status)} pour l'objet {self}."
        )
        return self.__status

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Marquez l'objet comme sale (modifié).

        Args :
            force (bool) : (optional) Forcer le marquage de l'objet comme sale. La valeur par défaut est False.
            event : (event) L'événement associé au marquage de l'objet comme sale.
        """
        if not self.setStatusDirty(force):
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusDirty(self, force=False):
        """
        Définissez le statut de l'objet comme sale (modifié).

        Args :
            force (bool) : (optional) Forcer la définition du statut comme sale. La valeur par défaut est False.

        Returns :
            (bool) : True si le statut a été modifié et non supprimé, False dans le cas contraire.
        """

        # print(f"🔄 setStatusDirty appelé : {self.__status} → {self.STATUS_CHANGED}")
        oldStatus = self.__status
        if self.__status == self.STATUS_NONE or force:
            self.__status = self.STATUS_CHANGED
            # print(f"SynchronizedObject.setStatusDirty : 🛑 DEBUG - Modification de self.__status pour {self} : {self.__status}")
            log.debug(
                f"SynchronizedObject.setStatusDirty : 🛑 Modification de self.__status pour {self} : {self.__status}"
            )

            return oldStatus == self.STATUS_DELETED
        else:
            return False

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Marquez l'objet comme neuf-nouveau(new).

        Args :
            event : L'événement associé au marquage de l'objet comme nouveau.
        """
        if not self.setStatusNew():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNew(self):
        """
        Définissez le statut de l'objet comme nouveau.

        Returns :
            (bool) : Vrai si le statut a été modifié et non supprimé, faux dans le cas contraire.
        """
        # print(f"🔄 setStatusNew appelé : {self.__status} → {self.STATUS_NEW}")
        oldStatus = self.__status
        self.__status = self.STATUS_NEW
        return oldStatus == self.STATUS_DELETED

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Marquez l'objet comme supprimé.

        Args :
            event : L'événement associé au marquage de l'objet comme supprimé.
        """
        self.setStatusDeleted()
        event.addSource(self, self.__status, type=self.markDeletedEventType())

    def setStatusDeleted(self):
        """
        Définissez le statut de l'objet comme supprimé.
        """
        # print(f"🔄 setStatusDeleted appelé : {self.__status} → {self.STATUS_DELETED}")
        self.__status = self.STATUS_DELETED

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Marquez l'objet comme non sale (aucun).

        Args :
            event : L'événement associé au marquage de l'objet comme non sale.
        """
        # print(f"🔄 cleanDirty appelé : self {self} __status {self.__status}")
        if not self.setStatusNone():
            return
        event.addSource(
            self, self.__status, type=self.markNotDeletedEventType()
        )

    def setStatusNone(self):
        """
        Définissez le statut de l'objet sur aucun.

        Returns :
            bool : Vrai si le statut a été modifié et non supprimé, Faux dans le cas contraire.
        """
        # print(f"🔄 setStatusNone appelé : {self.__status} → {self.STATUS_NONE}")
        oldStatus = self.__status
        self.__status = self.STATUS_NONE
        return oldStatus == self.STATUS_DELETED

    def isNew(self):
        """
        Vérifiez si l'objet est nouveau.

        Returns :
            (bool) : Vrai si l'objet est nouveau, faux sinon.
        """
        # print(f"🔄 isNew appelé : {self.__status} = {self.STATUS_NEW}")
        return self.__status == self.STATUS_NEW

    def isModified(self):
        """
        Vérifiez si l'objet est modifié (sale).

        Returns :
            (bool) : Vrai si l'objet est modifié, faux sinon.
        """
        # print(f"🔄 isModified appelé : {self.__status} = {self.STATUS_CHANGED}")
        return self.__status == self.STATUS_CHANGED

    def isDeleted(self):
        """
        Vérifiez si l'objet est supprimé.

        Returns :
            (bool) : Vrai si l'objet est supprimé, faux sinon.
        """
        # print(f"🔄 isDeleted appelé : {self.__status} = {self.STATUS_DELETED}")
        return self.__status == self.STATUS_DELETED

    def __getcopystate__(self):
        # Voir https://docs.python.org/3.12/library/pickle.html#object.__getstate__
        # faut-il le réimplémenter ?
        # return NotImplemented  # Non
        # pass
        try:
            return super().__getcopystate__()
        except AttributeError:
            return {}

    # méthode à ajouter ? oui ou non ?
    @classmethod
    def modificationEventTypes(class_):
        """Obtenez les types d'événements de modification pour l'objet."""
        # pass
        return []


# @functools.total_ordering
class Object(SynchronizedObject):
    """
    Une classe de base pour les objets avec des attributs et des fonctionnalités communs.

    Classe de base représentant un objet avec des attributs communs et des notifications d'événements.

    Cette classe étend SynchronizedObject pour fournir des attributs supplémentaires
    et des méthodes permettant de gérer l'état et le comportement d'un objet.
    Hérite de SynchronizedObject et fournit des attributs comme le sujet, la description,
    les couleurs, la police, les icônes, etc. Tous ces attributs sont encapsulés
    dans des objets `Attribute` capables de déclencher des événements.

    SynchronizedObject fournit des mécanismes pour marquer l'objet
    comme nouveau, modifié ou supprimé, et pour émettre
    des événements correspondants via l'attribut __status.

    Méthodes de gestion de l'état héritées de SynchronizedObject :
        getStatus,
        markDirty,
        markNew,
        markDeleted,
        cleanDirty,
        setStatusDirty,
        setStatusNew,
        setStatusDeleted,
        setStatusNone,
        isNew,
        isModified,
        isDeleted.

    Attributs principaux :
        __subject,
        __description,
        __id,
        __creationDateTime,
        __modificationDateTime,
        __fgColor,
        __bgColor,
        __font,
        __icon,
        __selectedIcon,
        __ordering.

    Encapsulation des attributs: Beaucoup d'attributs sont encapsulés par des classes Attribute (ex: self.__subject = attribute.Attribute(...)).
    C'est un pattern qui permet d'ajouter de la logique (validation, événements de changement) lors de la lecture/écriture des attributs.

    Methods :
        __init__
        __repr__,
        __eq__,
        __lt__,
        __hash__,
        __getstate__,
        __setstate__,
        __getcopystate__,
        copy,
        monitoredAttributes,
        id,
        customAttributes,
        creationDateTime,
        modificationDateTime,
        setModificationDateTime,
        modificationDateTimeSortFunction,
        creationDteTimeSortFunction,
        subject,
        setSubject,
        subjectChangedEvent,
        subjectChangedEventType,
        ordering,
        setOrdering,
        orderingChangedEvent,
        orderingChangedEventType,
        orderingSortFunction,
        orderingSortEventType,
        description
        setDescription,
        descriptionChangedEvent,
        descriptionChangedEventType : Obtenir le type d'événement pour les événements de changement de description.,
        descriptionSortFunction,
        descriptionSortEventType,
        setForegroundColor : Définir la couleur de premier plan de l'objet composite.,
        foregroundColor,
        setBackgroundColor : Définir la couleur d'arrière-plan de l'objet composite.,
        backgroundColor,
        font,
        setFont,
        icon,
        setIcon,
        selectedIcon,
        setSelectedIcon,
        appearanceChangedEventType,
        appearanceChangedEvent,
        derivedFgColor,
        derivedFgColorSource,
        derivedBgColor,
        derivedBgColorSource,
        derivedIcon,
        derivedIconSource,
        derivedFont,
        derivedFontSource,
        setDerivedFgColor,
        setDerivedBgColor,
        setDerivedIcon,
        setDerivedFont,
        _onDerivedFgColorChanged,
        _onDerivedBgColorChanged,
        _onDerivedIconChanged,
        _onDerivedFontChanged,
        - derivedFgColorChangedEventType : Obtenir le type d'événement pour les événements de couleur de premier plan dérivée modifiée.
        - derivedBgColorChangedEventType : Obtenir le type d'événement pour les événements de couleur de fond dérivée modifiée.
        - derivedIconChangedEventType : Obtenir le type d'événement pour les événements d’icône dérivés modifiés.
        - derivedFontChangedEventType : Obtenir le type d'événement pour les événements de police dérivés modifiés.
        - effectiveFgColor : Obtenir la couleur de premier plan effective de l'objet composite.
        - effectiveFgColorSource : Obtenir la source de la couleur de premier plan effective de l'objet composite.
        - effectiveFgColorDefault : Obtenir la valeur par défaut de la couleur de premier plan effective de l'objet composite.
        - effectiveBgColor : Obtenir la couleur d'arrière-plan effective de l'objet composite.
        - effectiveBgColorSource : Obtenir la source de la couleur d'arrière-plan effective de l'objet composite.
        - effectiveBgColorDefault : Obtenir la valeur par défaut de la couleur d'arrière-plan effective de l'objet composite.
        - effectiveIcon : Obtenir le nom de l'icône effectif de l'objet composite.
        - effectiveIconSource : Obtenir la source de l'icône effectif de l'objet composite.
        - effectiveFont : Obtenir la police effective de l'objet composite.
        - effectiveFontSource : Obtenir la source de la police effective de l'objet composite.
        - effectiveFontDefault : Obtenir la police par défaut de l'objet composite.
        - setEffectiveFgColor : Définir la couleur de premier plan effective, sa valeur par défaut et sa source.
        - setEffectiveBgColor : Définir la couleur d'arrière-plan effective, sa valeur par défaut et sa source.
        - setEffectiveIcon : Définir l'icône effectif.
        - setEffectiveFont : Définir la valeur de la police à appliquer.
        - _onEffectiveFgColorChanged : Fonction de rappel pour les changements de couleur de premier plan effective.
        - _onEffectiveBgColorChanged : Fonction de rappel pour les changements de couleur d'arrière-plan effective.
        - _onEffectiveIconChanged : Fonction de rappel pour les changements d'icône effective.
        - _onEffectiveFontChanged : Fonction de rappel pour les changements de police effective.
        - effectiveFgColorChangedEventType : Obtenir le type d’événement pour les événements de couleur de premier plan dérivée modifiée.
        - effectiveBgColorChangedEventType : Obtenir le type d’événement pour les événements de couleur de fond dérivée modifiée.
        - effectiveIconChangedEventType : Obtenir le type d’événement pour les événements d’icône dérivée modifiée.
        - effectiveFontChangedEventType : Obtenir le type d’événement pour les événements de police dérivée modifiée.
        - modificationEventTypes : Fournit les types d'événements de modification pour les classes dérivées.
    """

    # Attributs que Object.__getstate__() et Object.__setstate__() gèrent :
    # ce qui doit être stocké dans le fichier.
    # Jamais dans __init__, sinon chaque instance sérialise cette constante, ce qui pollue les états.
    # SERIALIZATION_CORE_KEYS = {
    SERIALIZATION_CORE_KEYS = (
        SynchronizedObject.SERIALIZATION_CORE_KEYS
        | frozenset(
            [
                # "status",
                "id",
                "creationDateTime",
                "modificationDateTime",
                "subject",
                "description",
                "fgColor",
                "bgColor",
                "font",
                "icon",
                "ordering",
                "selectedIcon",
            ]
        )
        # }
    )
    # Owner, Task, Category et les futures classes du domaine héritent de Object.

    rx_attributes = re.compile(
        r"\[(\w+):(.+)\]"
    )  # Expression régulière pour parser les attributs

    # Gestion de la compatibilité Python 2/3 pour un entier long zéro
    if sys.version_info.major == 2:
        _long_zero = int(0)
    else:
        _long_zero = 0

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'instance d'objet.

        Initialise une nouvelle instance d'Object avec ses attributs et
        leurs gestionnaires d'événements.
        Initialise l'objet de base avec ses attributs standards, tout en filtrant
        les arguments non reconnus avant d'appeler le constructeur final.

        Initialise tous les attributs avec une instance de attribute.Attribute.

        Args :
            args : Liste d'argument positionnel de longueur variable (souvent vides ici).
            *kwargs : Arguments de mots clés arbitraires. Arguments nommés pour
                      personnaliser les attributs de l'objet. Attributs sérialisés
                      pour restaurer l'état de l'objet.

        Attributes :
            id (str) : Identifiant unique de l'objet.
            subject (str) : Sujet ou titre de l'objet.
            description (str) : Description détaillée de l'objet.
            creationDateTime (DateTime) : Date et heure de création de l'objet.
            modificationDateTime (DateTime) : Date et heure de la dernière modification de l'objet.
            fgColor (str) : Couleur de premier plan de l'objet (ex: "#RRGGBB").
            bgColor (str) : Couleur de fond de l'objet (ex: "#RRGGBB").
            font (str) : Police de caractères utilisée pour l'affichage de l'objet (ex: "Arial 12").
            icon (str) : Chemin vers l'icône associée à l'objet.
            selectedIcon (str) : Chemin vers l'icône utilisée lorsque l'objet est sélectionné.
            ordering (int) : Un entier représentant l'ordre de tri de l'objet parmi ses pairs.
        """
        print(f"Object.__init__ : reçoit args={args} et kwargs={kwargs}")
        # print(f"Object.__init__ : self avant init={self}")  # AttributeError: 'CompositeObject' object has no attribute '_Object__subject'
        # Récupère et définit
        Attribute = attribute.Attribute  # Raccourci pour la classe Attribute
        # print(f"Object.__init__ : Attribute={Attribute}")
        # print(f"Object.__init__ : kwargs={kwargs}")

        # On récupère la liste des clés à traiter localement
        # accepted_keys = [
        accepted_keys = [
            # "status",
            "id",
            "subject",
            "description",
            "creationDateTime",
            "modificationDateTime",
            "fgColor",
            "bgColor",
            "font",
            "icon",
            "selectedIcon",
            "ordering",
        ]

        # On extrait les attributs pour soi
        local_kwargs = {
            key: kwargs.pop(key) for key in accepted_keys if key in kwargs
        }

        # Faut-il les garder ou les effacer de kwargs ?
        # log.debug(
        print(
            f"Object.__init__ : kwargs={kwargs} et local_kwargs={local_kwargs} avant appel à super."
        )
        # Appel sécurisé au constructeur parent (sans kwargs dangereux)
        super().__init__(*args, **kwargs)

        # Création d'une référence faible à self, utilisée pour éviter les cycles de références
        selfRef = weakref.ref(self)

        # Définition des callbacks d'événements encapsulés
        # Fonction de rappel personnalisée pour les changements de sujet
        def setSubjectEvent(event):
            """Fonction de rappel personnalisée pour les changements de sujet."""
            obj = selfRef()
            if obj is not None:
                obj.subjectChangedEvent(event)

        # Fonction de rappel personnalisée pour les changements de description
        def setDescriptionEvent(event):
            """Fonction de rappel personnalisée pour les changements de description."""
            obj = selfRef()  # Récupère l'objet si encore en mémoire
            if obj is not None:
                obj.descriptionChangedEvent(event)  # Déclenche l'événement

        # Fonction de rappel personnalisée pour les changements d'apparence
        def setAppearanceEvent(event):
            """Fonction de rappel personnalisée pour les changements d'apparence."""
            obj = selfRef()
            if obj is not None:
                obj.appearanceChangedEvent(event)

        def setOrderingEvent(event):
            """Fonction de rappel personnalisée pour les changements d'ordre de tri."""
            obj = selfRef()
            if obj is not None:
                obj.orderingChangedEvent(event)

        # On extrait d'abord les données utiles pour Object
        # Attributs principaux, initialisés avec leurs gestionnaires d'événements
        ATTRIBUTE_SPECS = {
            "subject": ("", "subjectChangedEventType"),
            "description": ("", "descriptionChangedEventType"),
            "fgColor": (None, "appearanceChangedEvent"),
            "bgColor": (None, "appearanceChangedEvent"),
            "font": (None, "appearanceChangedEvent"),
            "icon": ("", "appearanceChangedEvent"),
            "ordering": (0, "orderingChangedEvent"),
            "selectedIcon": ("", "appearanceChangedEvent"),
        }
        DERIVED_ATTRIBUTE_SPECS = (
            ("_Object__derivedFgColorValue", None, "_onDerivedFgColorChanged"),
            (
                "_Object__derivedFgColorSource",
                None,
                "_onDerivedFgColorChanged",
            ),
            ("_Object__derivedBgColorValue", None, "_onDerivedBgColorChanged"),
            (
                "_Object__derivedBgColorSource",
                None,
                "_onDerivedBgColorChanged",
            ),
            ("_Object__derivedIconValue", "", "_onDerivedIconChanged"),
            ("_Object__derivedIconSource", None, "_onDerivedIconChanged"),
            ("_Object__derivedFontValue", None, "_onDerivedFontChanged"),
            ("_Object__derivedFontSource", None, "_onDerivedFontChanged"),
        )
        EFFECTIVE_ATTRIBUTE_SPECS = (
            (
                "_Object__effectiveFgColorValue",
                None,
                "_onEffectiveFgColorChanged",
            ),
            (
                "_Object__effectiveFgColorSource",
                None,
                "_onEffectiveFgColorChanged",
            ),
            (
                "_Object__effectiveFgColorDefault",
                None,
                "_onEffectiveFgColorChanged",
            ),
            (
                "_Object__effectiveBgColorValue",
                None,
                "_onEffectiveBgColorChanged",
            ),
            (
                "_Object__effectiveBgColorSource",
                None,
                "_onEffectiveBgColorChanged",
            ),
            (
                "_Object__effectiveBgColorDefault",
                None,
                "_onEffectiveBgColorChanged",
            ),
            ("_Object__effectiveIconValue", "", "_onEffectiveIconChanged"),
            ("_Object__effectiveIconSource", None, "_onEffectiveIconChanged"),
            ("_Object__effectiveFontValue", None, "_onEffectiveFontChanged"),
            ("_Object__effectiveFontSource", None, "_onEffectiveFontChanged"),
            ("_Object__effectiveFontDefault", None, "_onEffectiveFontChanged"),
        )
        # Initialisation des Attributes fondamentaux
        self.createAttributes()

        # # Raccordement dynamique des callbacks définis localement dans __init__
        # self.__subject.setEvent = setSubjectEvent
        # self.__description.setEvent = setDescriptionEvent
        # self.__fgColor.setEvent = setAppearanceEvent
        # self.__bgColor.setEvent = setAppearanceEvent
        # self.__font.setEvent = setAppearanceEvent
        # self.__icon.setEvent = setAppearanceEvent
        # self.__selectedIcon.setEvent = setAppearanceEvent
        # self.__ordering.setEvent = setOrderingEvent
        # Raccordement dynamique des callbacks définis localement dans __init__
        # On installe les vrais handlers après avoir créé les Attributes
        # et injecté les valeurs initiales afin d'éviter d'émettre des
        # notifications pendant l'initialisation.
        try:
            # Utilise la méthode setEvent exposée par attribute.Attribute
            self._Object__subject.setEvent(setSubjectEvent)
            self._Object__description.setEvent(setDescriptionEvent)
            self._Object__fgColor.setEvent(setAppearanceEvent)
            self._Object__bgColor.setEvent(setAppearanceEvent)
            self._Object__font.setEvent(setAppearanceEvent)
            self._Object__icon.setEvent(setAppearanceEvent)
            self._Object__selectedIcon.setEvent(setAppearanceEvent)
            self._Object__ordering.setEvent(setOrderingEvent)
        except Exception:
            # En cas d'erreur (par ex. ancienne implémentation d'Attribute), ne pas échouer
            pass

        # Restauration ou génération des attributs scalaires
        self.__id = local_kwargs.get("id") or str(uuid.uuid1())
        self.__creationDateTime = local_kwargs.get("creationDateTime") or Now()
        self.__modificationDateTime = (
            local_kwargs.get("modificationDateTime") or DateTime.min
        )

        # Injection des valeurs initiales
        if "subject" in local_kwargs:
            self.__subject.set(local_kwargs["subject"])
        if "description" in local_kwargs:
            self.__description.set(local_kwargs["description"])
        if "fgColor" in local_kwargs:
            self.__fgColor.set(local_kwargs["fgColor"])
        if "bgColor" in local_kwargs:
            self.__bgColor.set(local_kwargs["bgColor"])
        if "font" in local_kwargs:
            # self.__font.set(local_kwargs["font"])
            self.__font = local_kwargs["font"]
        if "icon" in local_kwargs:
            # self.__icon.set(local_kwargs["icon"])
            self.__icon = local_kwargs["icon"]
        if "selectedIcon" in local_kwargs:
            self.__selectedIcon.set(local_kwargs["selectedIcon"])
        if "ordering" in local_kwargs:
            self.__ordering.set(local_kwargs["ordering"])

        # # self.__creationDateTime = kwargs.pop("creationDateTime", None) or Now()
        # self.__creationDateTime = (
        #     local_kwargs.pop("creationDateTime", None) or Now()
        # )
        # # self.__modificationDateTime = kwargs.pop("modificationDateTime", DateTime.min)
        # self.__modificationDateTime = local_kwargs.pop(
        #     "modificationDateTime", DateTime.min
        # )
        # # self.__subject = Attribute(
        # #     kwargs.pop("subject", ""), self, self.subjectChangedEvent
        # # )
        # # self.__subject = Attribute(
        # #     kwargs.pop("subject", ""), self, setSubjectEvent
        # # )
        # # subject_value = kwargs.pop("subject", "")
        # subject_value = local_kwargs.pop("subject", "")
        # print(f"Object.__init__ : subject_value={subject_value}")
        # assert callable(
        #     setSubjectEvent
        # ), f"setSubjectEvent invalide : {setSubjectEvent!r}"
        #
        # if isinstance(subject_value, attribute.Attribute):
        #     self.__subject = subject_value
        # else:
        #     self.__subject = attribute.Attribute(
        #         subject_value, self, setSubjectEvent
        #     )
        # # log.debug(f"[DEBUG] Object.__init__() → subject reçu: {self.__subject!r}")
        # log.debug(
        #     f"[DEBUG] Object.__init__() → subject reçu: {self.__subject.get()}"
        # )
        # # self.__description = Attribute(
        # #     kwargs.pop("description", ""), self, self.descriptionChangedEvent
        # # )
        # # self.__description = Attribute(
        # #     kwargs.pop("description", ""), self, setDescriptionEvent
        # # )
        # # description_value = kwargs.pop("description", "")
        # description_value = local_kwargs.pop("description", "")
        # if isinstance(description_value, attribute.Attribute):
        #     self.__description = description_value
        # else:
        #     self.__description = Attribute(
        #         description_value, self, setDescriptionEvent
        #     )
        # log.debug(
        #     f"Object.__init__() : description reçu: {self.__description}"
        # )
        # # self.__fgColor = Attribute(
        # #     kwargs.pop("fgColor", None), self, self.appearanceChangedEvent
        # # )
        # # self.__fgColor = Attribute(
        # #     kwargs.pop("fgColor", None), self, setAppearanceEvent
        # # )
        # # fgColor_value = kwargs.pop("fgColor", None)
        # fgColor_value = local_kwargs.pop("fgColor", None)
        # if isinstance(fgColor_value, attribute.Attribute):
        #     self.__fgColor = fgColor_value
        # else:
        #     self.__fgColor = Attribute(fgColor_value, self, setAppearanceEvent)
        # # self.__bgColor = Attribute(
        # #     kwargs.pop("bgColor", None), self, self.appearanceChangedEvent
        # # )
        # # self.__bgColor = Attribute(
        # #     kwargs.pop("bgColor", None), self, setAppearanceEvent
        # # )
        # # bgColor_value = kwargs.pop("bgColor", None)
        # bgColor_value = local_kwargs.pop("bgColor", None)
        # if isinstance(bgColor_value, attribute.Attribute):
        #     self.__bgColor = bgColor_value
        # else:
        #     self.__bgColor = Attribute(bgColor_value, self, setAppearanceEvent)
        # # self.__font = Attribute(
        # #     kwargs.pop("font", None), self, self.appearanceChangedEvent
        # # )
        # # self.__font = Attribute(
        # #     kwargs.pop("font", None), self, setAppearanceEvent
        # # )
        # # font_value = kwargs.pop("font", None)
        # font_value = local_kwargs.pop("font", None)
        # if isinstance(font_value, attribute.Attribute):
        #     self.__font = font_value
        # else:
        #     self.__font = Attribute(font_value, self, setAppearanceEvent)
        # # self.__icon = Attribute(
        # #     kwargs.pop("icon", ""), self, self.appearanceChangedEvent
        # # )
        # # self.__icon = Attribute(
        # #     kwargs.pop("icon", ""), self, setAppearanceEvent
        # # )
        # # icon_value = kwargs.pop("icon", "")
        # icon_value = local_kwargs.pop("icon", "")
        # if isinstance(icon_value, attribute.Attribute):
        #     self.__icon = icon_value
        # else:
        #     self.__icon = Attribute(icon_value, self, setAppearanceEvent)
        # # self.__selectedIcon = Attribute(
        # #     kwargs.pop("selectedIcon", ""), self, self.appearanceChangedEvent
        # # )
        # # self.__selectedIcon = Attribute(
        # #     kwargs.pop("selectedIcon", ""), self, setAppearanceEvent
        # # )
        # # selectedIcon_value = kwargs.pop("selectedIcon", "")
        # selectedIcon_value = local_kwargs.pop("selectedIcon", "")
        # if isinstance(selectedIcon_value, attribute.Attribute):
        #     self.__selectedIcon = selectedIcon_value
        # else:
        #     self.__selectedIcon = Attribute(
        #         selectedIcon_value, self, setAppearanceEvent
        #     )
        # # # self.__ordering = Attribute(
        # # #     kwargs.pop("ordering", Object._long_zero),
        # # #     self,
        # # #     self.orderingChangedEvent,
        # # # )
        # # # self.__ordering = Attribute(
        # # #     kwargs.pop("ordering", Object._long_zero),
        # # #     self,
        # # #     setOrderingEvent,
        # # # )
        # # self.__ordering = Attribute(
        # #     local_kwargs.pop("ordering", Object._long_zero),
        # #     self,
        # #     setOrderingEvent,
        # # )
        # # # self.__id = kwargs.pop("id", None or str(uuid.uuid1()))  # ID unique
        # # self.__id = local_kwargs.pop("id", None or str(uuid.uuid1())
        # # )  # ID unique, mais ne permet d'avoir None comme id !
        # self.__id = local_kwargs.pop("id", None) or str(uuid.uuid1())
        # # log.debug(f"Object.__init__() : id reçu: {self.__id}.")
        # print(f"Object.__init__() : id reçu: {self.__id}.")

        # # Derived SSOT fields (value + source for each appearance type)
        # self.__derivedFgColorValue = Attribute(
        #     None, self, self._onDerivedFgColorChanged
        # )
        # self.__derivedFgColorSource = Attribute(
        #     None, self, self._onDerivedFgColorChanged
        # )
        # self.__derivedBgColorValue = Attribute(
        #     None, self, self._onDerivedBgColorChanged
        # )
        # self.__derivedBgColorSource = Attribute(
        #     None, self, self._onDerivedBgColorChanged
        # )
        # self.__derivedIconValue = Attribute(
        #     None, self, self._onDerivedIconChanged
        # )
        # self.__derivedIconSource = Attribute(
        #     None, self, self._onDerivedIconChanged
        # )
        # self.__derivedFontValue = Attribute(
        #     None, self, self._onDerivedFontChanged
        # )
        # self.__derivedFontSource = Attribute(
        #     None, self, self._onDerivedFontChanged
        # )

        # # Effective SSOT fields (value + source + default for colors/font, value + source for icon)
        # self.__effectiveFgColorValue = Attribute(
        #     None, self, self._onEffectiveFgColorChanged
        # )
        # self.__effectiveFgColorSource = Attribute(
        #     None, self, self._onEffectiveFgColorChanged
        # )
        # self.__effectiveFgColorDefault = Attribute(
        #     None, self, self._onEffectiveFgColorChanged
        # )
        # self.__effectiveBgColorValue = Attribute(
        #     None, self, self._onEffectiveBgColorChanged
        # )
        # self.__effectiveBgColorSource = Attribute(
        #     None, self, self._onEffectiveBgColorChanged
        # )
        # self.__effectiveBgColorDefault = Attribute(
        #     None, self, self._onEffectiveBgColorChanged
        # )
        # self.__effectiveIconValue = Attribute(
        #     None, self, self._onEffectiveIconChanged
        # )
        # self.__effectiveIconSource = Attribute(
        #     None, self, self._onEffectiveIconChanged
        # )
        # self.__effectiveFontValue = Attribute(
        #     None, self, self._onEffectiveFontChanged
        # )
        # self.__effectiveFontSource = Attribute(
        #     None, self, self._onEffectiveFontChanged
        # )
        # self.__effectiveFontDefault = Attribute(
        #     None, self, self._onEffectiveFontChanged
        # )

        # # Initialisation du parent
        # # super().__init__(*args, **kwargs)  # Appelle le constructeur de la classe parente
        # # super().__init__()  # à vérifier sinon revenir à la définition précédente
        # # Transmet les arguments uniquement si le parent **n'est pas `object'**
        # # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
        # if type(self).__mro__[1] is not object:
        #     # Class 'property' does not define '__getitem__', so the '[]' operator cannot be used on its instances
        #     try:
        #         super().__init__(*args, **kwargs)
        #     except TypeError:
        #         super().__init__()
        # else:
        #     super().__init__()  # Sécurisé pour `object`

    def _createAttribute(self, key, value, callback):
        """
        Crée un nouvel attribut.

        Args:
            key: Clef d'attribut
            value: Valeur de l'attribut
            callback: Méthode d'événement à utiliser

        Returns:
            None
        """
        setattr(
            self,
            key,
            attribute.Attribute(
                value,
                self,
                getattr(self, callback),
            ),
        )

    def createAttributes(self):
        """
        Crée tous les objets Attribute utilisés par Object.

        Cette méthode est utilisée :
        - lors de l'initialisation normale (__init__)
        - lors de la désérialisation (__setstate__)
        """
        # ce qui doit exister en mémoire pour que l'objet fonctionne.

        # # les clés sérialisées restent définies à un seul endroit
        # for key in SERIALIZATION_CORE_KEYS:
        #     if key not in ATTRIBUTE_SPECS:
        #         continue
        #
        #     default_value, callback_name = ATTRIBUTE_SPECS[key]
        #
        #     # les objets Attribute correspondants sont créés automatiquement
        #     setattr(
        #         self,
        #         f"_Object__{key}",
        #         attribute.Attribute(
        #             default_value,
        #             self,
        #             getattr(self, callback_name),
        #         ),
        #     )
        #
        # for key, default_value, callback_name in (
        #     DERIVED_ATTRIBUTE_SPECS + EFFECTIVE_ATTRIBUTE_SPECS
        # ):
        #     setattr(
        #         self,
        #         key,
        #         attribute.Attribute(
        #             default_value,
        #             self,
        #             getattr(self, callback_name),
        #         ),
        #     )
        # Attributs fondamentaux
        self._Object__subject = attribute.Attribute(
            "", self, lambda event: None
        )
        self._Object__description = attribute.Attribute(
            "", self, lambda event: None
        )
        self._Object__fgColor = attribute.Attribute(
            None, self, lambda event: None
        )
        self._Object__bgColor = attribute.Attribute(
            None, self, lambda event: None
        )
        self._Object__font = attribute.Attribute(
            None, self, lambda event: None
        )
        self._Object__icon = attribute.Attribute("", self, lambda event: None)
        self._Object__selectedIcon = attribute.Attribute(
            "", self, lambda event: None
        )
        self._Object__ordering = attribute.Attribute(
            self._long_zero, self, lambda event: None
        )

        # Attributs d'apparence dérivés
        self.__derivedFgColorValue = attribute.Attribute(
            None, self, self._onDerivedFgColorChanged
        )
        self.__derivedFgColorSource = attribute.Attribute(
            None, self, self._onDerivedFgColorChanged
        )
        self.__derivedBgColorValue = attribute.Attribute(
            None, self, self._onDerivedBgColorChanged
        )
        self.__derivedBgColorSource = attribute.Attribute(
            None, self, self._onDerivedBgColorChanged
        )
        self.__derivedIconValue = attribute.Attribute(
            "", self, self._onDerivedIconChanged
        )
        self.__derivedIconSource = attribute.Attribute(
            None, self, self._onDerivedIconChanged
        )
        self.__derivedFontValue = attribute.Attribute(
            None, self, self._onDerivedFontChanged
        )
        self.__derivedFontSource = attribute.Attribute(
            None, self, self._onDerivedFontChanged
        )

        # Attributs d'apparence effectifs
        self.__effectiveFgColorValue = attribute.Attribute(
            None, self, self._onEffectiveFgColorChanged
        )
        self.__effectiveFgColorSource = attribute.Attribute(
            None, self, self._onEffectiveFgColorChanged
        )
        self.__effectiveFgColorDefault = attribute.Attribute(
            None, self, self._onEffectiveFgColorChanged
        )
        self.__effectiveBgColorValue = attribute.Attribute(
            None, self, self._onEffectiveBgColorChanged
        )
        self.__effectiveBgColorSource = attribute.Attribute(
            None, self, self._onEffectiveBgColorChanged
        )
        self.__effectiveBgColorDefault = attribute.Attribute(
            None, self, self._onEffectiveBgColorChanged
        )
        self.__effectiveIconValue = attribute.Attribute(
            "", self, self._onEffectiveIconChanged
        )
        self.__effectiveIconSource = attribute.Attribute(
            None, self, self._onEffectiveIconChanged
        )
        self.__effectiveFontValue = attribute.Attribute(
            None, self, self._onEffectiveFontChanged
        )
        self.__effectiveFontSource = attribute.Attribute(
            None, self, self._onEffectiveFontChanged
        )
        self.__effectiveFontDefault = attribute.Attribute(
            None, self, self._onEffectiveFontChanged
        )

    def __repr__(self):
        """
        Renvoie une représentation sous forme de chaîne de l'instance d'objet.

        Returns :
            (str) : La représentation sous forme de chaîne.
        """
        # return self.subject()
        # Protect against the case where an instance attribute named 'subject'
        # (e.g. set during __setstate__) shadows the callable accessor
        # self.subject. In that case getattr(self, 'subject') may return a
        # string and calling it would raise TypeError. We therefore check
        # whether the attribute is callable and fall back gracefully.
        subj_attr = getattr(self, "subject", None)
        if callable(subj_attr):
            try:
                return subj_attr()
            except Exception:
                # If calling fails for any reason, fall through to fallback
                pass

        # If subject is not callable, try to read a plain value from __dict__
        subj_val = (
            self.__dict__.get("subject") if hasattr(self, "__dict__") else None
        )
        if subj_val is not None:
            return str(subj_val)

        # Last resort: return a simple class/id representation
        return f"<{self.__class__.__name__} id={id(self)}>"

    def __eq__(self, other):
        if not isinstance(other, Object):
            return NotImplemented
        return self.id() == other.id()

    def __lt__(self, other):
        if not isinstance(other, Object):
            return NotImplemented
        return self.id() < other.id()

    def __hash__(self):
        return hash(self.id())

    # Audit commun
    @staticmethod
    def safe_super_state(instance, klass):
        """Retourne l'état fourni par la classe parente.

        Récupère l'état du parent de manière sécurisée.
        Garantit toujours un dict exploitable.
        """
        # parent_getstate = getattr(super(klass, instance), "__getstate__", None)
        #
        # if parent_getstate:
        #     state = parent_getstate()
        # else:
        #     state = {}
        #
        # return dict(state)  # protection anti-effets de bord
        # Les méthodes générées dans owner.py peuvent l'utiliser !
        try:
            return dict(super(klass, instance).__getstate__())
        except AttributeError:
            return {}

    # @staticmethod
    def validate_state(self, state):
        """Valide l'état sérialisé.

        Vérifie qu'aucune clé de sérialisation fondamentale n'a disparu.
        """
        super().validate_state(state)
        # # missing = [key for key in SERIALIZATION_CORE_KEYS if key not in state]
        # # missing = [key for key in accepted_keys if key not in state]
        # missing = Object.SERIALIZATION_CORE_KEYS.difference(state)
        missing = self.SERIALIZATION_CORE_KEYS.difference(state)

        # # assert not missing, f"Clés manquantes dans le state : {missing}"
        # assert not missing, "Clés de sérialisation perdues : %s" % sorted(
        #     missing
        # )
        assert not missing, (
            f"État incomplet pour {type(self).__name__}. "
            f"Clés manquantes : {sorted(missing)}"
        )

        # return state

    # def protect_parent_keys(old_state, new_state):
    #     protected = set(old_state.keys()) & {"status", "id", "creationDateTime"}
    #
    #     for key in protected:
    #         new_state[key] = old_state[key]
    #
    #     return new_state

    @staticmethod
    def protect_parent_keys(parent_state, child_state):
        """
        Vérifie que les clés héritées n'ont pas disparu.
        """

        for key in parent_state:
            assert key in child_state, f"Clé héritée perdue : {key}"

        return child_state

    def __getstate__(self):
        """
        Retourne l'état sérialisé de l'objet.

        Cet état est un dictionnaire contenant uniquement les attributs utiles
        pour la sauvegarde, en filtrant les attributs internes ou non pertinents.
        Conserve les données héritées depuis les classes parentes,
        tout en filtrant les attributs internes non désirés.
        Collecte l'état de l'objet, en récupérant les valeurs .get() des objets
        Attribute et les ajoutant au dictionnaire state retourné par super().__getstate__().

        Returns :
            (dict) : Un dictionnaire nettoyé représentant l'état de l'objet.
        """
        # Définition des invariants de sérialisation
        # assert state["status"] == new_state["status"]
        # assert state["id"] == new_state["id"]
        # assert state["subject"] == new_state["subject"]
        # assert state["description"] == new_state["description"]
        # assert state["creationDateTime"] == new_state["creationDateTime"]
        # assert (
        #     state["modificationDateTime"] == new_state["modificationDateTime"]
        # )
        # assert state["fgColor"] == new_state["fgColor"]
        # assert state["bgColor"] == new_state["bgColor"]
        # assert state["font"] == new_state["font"]
        # assert state["icon"] == new_state["icon"]
        # assert state["ordering"] == new_state["ordering"]
        # assert state["selectedIcon"] == new_state["selectedIcon"]

        # Construction explicite du dictionnaire d'état.
        print("Object.__getstate__() : Appelé par ", self.__class__.__name__)
        try:
            # On récupère l'état hérité (ex : depuis SynchronizedObject)
            state = super().__getstate__()
        except AttributeError:
            state = dict()
        print(f"Object.__getstate__() après super et avant update: {state}")
        # log.debug(f"Object.__getstate__() : state avant update: {state}")
        # log.debug(f"DEBUG - Object.__getstate__() avant update subject.get() : {self.__subject.get()}")
        # if hasattr(self, 'subject'):
        #     log.debug(f"Object.__setstate__() - subject avant update: {self.subject}")
        # else:
        if not hasattr(self, "subject"):
            # log.debug(
            print("Object.__setstate__() - subject non défini avant update.")

        # On ajoute uniquement les champs publics attendus,
        # extraits via les attributs "Attribute".
        # Extraction propre des valeurs scalaires
        print(f"Object.__getstate__() : update")
        state.update(
            dict(
                id=self.__id,  # Identifiant unique de l'objet
                creationDateTime=self.__creationDateTime,  # Date de création
                modificationDateTime=self.__modificationDateTime,  # Date de modification
                subject=self.__subject.get(),  # Sujet de l'objet
                description=self.__description.get(),  # Description
                fgColor=self.__fgColor.get(),  # Couleur de premier plan
                bgColor=self.__bgColor.get(),  # Couleur d'arrière-plan
                font=self.__font.get(),  # Police utilisée
                icon=self.__icon.get(),  # Icône associée
                ordering=self.__ordering.get(),  # Icône sélectionnée
                selectedIcon=self.__selectedIcon.get(),  # Ordre d'affichage ou de tri
            )
        )
        print(
            f"Object.__getstate__() : state après update: {state} avant nettoyage"
        )
        # Object.__getstate__ ne doit JAMAIS filtrer les attributs des sous-classes
        # # # On supprime les clés privées (souvent nommées _NomClasse__attribut)
        # # # Ici, on retire tous les attributs privés de 'Object' (ex: _Object__subject)
        # # private_prefixes = [
        # #     f"_{self.__class__.__name__}__",
        # #     "_SynchronizedObject__",
        # # ]
        # # On supprime uniquement les attributs STRICTEMENT internes de Object/SynchronizedObject
        # private_prefixes = [
        #     "_Object__",
        #     "_SynchronizedObject__",
        # ]
        # keys_to_remove = [
        #     key
        #     for key in state
        #     if any(key.startswith(prefix) for prefix in private_prefixes)
        # ]
        # for key in keys_to_remove:
        #     del state[key]

        # ⚠️ Nettoyage uniquement des classes du framework, pas des subclasses métier
        # Suppression uniquement des attributs internes des classes parentes.
        # Les classes filles comme NoteOwner doivent conserver leurs attributs privés
        # pour permettre à Owner.__getstate__ de reconstruire leur état métier.
        for key in list(state.keys()):
            if key.startswith("_Object__") or key.startswith(
                "_SynchronizedObject__"
            ):
                # if key.startswith("_"):
                del state[key]

        print(
            f"Object.__getstate__() : state après nettoyage: {state} avant validation"
        )
        print("Object.__getstate : GETSTATE KEYS =", sorted(state.keys()))
        self.validate_state(state)

        # DEBUG : Affichage de l'état sérialisé pour vérification
        # log.debug(f"DEBUG - Object.__getstate__() renvoie : {state}")
        print(f"Object.__getstate__() renvoie : {state} après validation !")
        #
        return state

        # Problème __getstate__ contient maintenant plus d'objet :
        # {'_Object__bgColor': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b81888b500>,
        #  '_Object__creationDateTime': DateTime(2025, 3, 12, 20, 59, 14, 750288),
        #  '_Object__description': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b822a88d40>,
        #  '_Object__fgColor': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b818436f40>,
        #  '_Object__font': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b818889e40>,
        #  '_Object__icon': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b818889c80>,
        #  '_Object__id': '794711e8-ff7c-11ef-a937-a4f933b218b7',
        #  '_Object__modificationDateTime': DateTime(1, 1, 1, 0, 0),
        #  '_Object__ordering': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b80a7c1100>,
        #  '_Object__selectedIcon': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b80a7c2a40>,
        #  '_Object__subject': <taskcoachlib.domain.base.attribute.Attribute object at 0x74b822c04b80>,
        #  '_SynchronizedObject__status': 1,
        #  'bgColor': None,
        #  'creationDateTime': DateTime(2025, 3, 12, 20, 59, 14, 750288),
        #  'description': '',
        #  'fgColor': None,
        #  'font': None,
        #  'icon': '',
        #  'id': '794711e8-ff7c-11ef-a937-a4f933b218b7',
        #  'modificationDateTime': DateTime(1, 1, 1, 0, 0),
        #  'ordering': 0,
        #  'selectedIcon': '',
        #  'status': 1,
        #  'subject': ''} != {'bgColor': None,
        #  'creationDateTime': DateTime(2025, 3, 12, 20, 59, 14, 750288),
        #  'description': '',
        #  'fgColor': None,
        #  'font': None,
        #  'icon': '',
        #  'id': '794711e8-ff7c-11ef-a937-a4f933b218b7',
        #  'modificationDateTime': DateTime(1, 1, 1, 0, 0),
        #  'ordering': 0,
        #  'selectedIcon': '',
        #  'status': 1,
        #  'subject': ''}

        # Origine probable
        #
        # La méthode __getstate__ (comme __setstate__) est utilisée en Python
        # pour définir comment un objet doit être sérialisé/désérialisé
        # (par exemple, avec pickle, ou pour enregistrer son état).
        # Si tu ne la redéfinis pas dans ta classe, le comportement par défaut
        # consiste à retourner le dictionnaire __dict__,
        # donc tous les attributs de l’objet, y compris ceux privés et internes.

        # Python 3 ne masque pas autant les attributs privés (préfixés par __)
        # lors de la sérialisation si on utilise object.__getstate__
        # ou si la classe n'en définit pas un.
        # Ce genre d’attribut devient dans __dict__ : '_NomDeLaClasse__bgColor',
        # et est donc sérialisé si on ne filtre pas.

        # Solution :
        # Il faut redéfinir __getstate__() dans la classe concernée
        # pour ne retourner que ce que tu veux (et non tous les attributs de l’objet).

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """
        Définissez l'état de l'objet à partir de la désérialisation.

        Restaure l'état interne de l'objet après désérialisation.

        Les attributs privés créés dans __init__ ne sont pas présents car
        Python utilise __new__ puis appelle directement __setstate__.

        Args :
            state (dict) : L’état à définir.
            event : (event) L'événement associé à la définition de l'état.
        """
        log.debug(
            f"Object.__setstate__ : avant super, state={state} et event={event}."
        )
        print("DEBUG Object.__setstate__ AVANT")
        print(self.__dict__)

        # Toujours recréer les conteneurs d'attributs d'abord
        self.createAttributes()

        # Appeler le parent
        # C'est l'appel crucial qui va charger les attributs du parent SynchronizedObject
        try:
            super().__setstate__(state, event=event)
        # except AttributeError:  # Cache certains problèmes
        #     pass
        except AttributeError as error:
            print("ERREUR super().__setstate__ :", error)
            raise
        # log.debug(f"Object.__setstate__() - Entrée, state dict: {state}")

        # Reconstruction minimale des attributs Attribute internes.
        # missing = {}
        # for object_attr in self.SERIALIZATION_CORE_KEYS:
        #     if not hasattr(self, f"_Object__{object_attr}"):
        #         self.createAttributes()
        #
        # missing = {
        #     not hasattr(self, f"_Object__{object_attr}")
        #     for object_attr in self.SERIALIZATION_CORE_KEYS
        # }

        # if not hasattr(self, "_Object__subject"):
        #     self.__subject = attribute.Attribute(
        #         "", self, setEvent=self.subjectChangedEventType
        #     )
        #
        # if not hasattr(self, "_Object__description"):
        #     self.__description = attribute.Attribute(
        #         "", self, setEvent=self.descriptionChangedEventType
        #     )
        #
        # if not hasattr(self, "_Object__fgColor"):
        #     self.__fgColor = attribute.Attribute(
        #         None, self, self.appearanceChangedEvent
        #     )
        #
        # if not hasattr(self, "_Object__bgColor"):
        #     self.__bgColor = attribute.Attribute(
        #         None, self, self.appearanceChangedEvent
        #     )
        #
        # if not hasattr(self, "_Object__font"):
        #     self.__font = attribute.Attribute(
        #         None, self, self.appearanceChangedEvent
        #     )
        #
        # if not hasattr(self, "_Object__icon"):
        #     self.__icon = attribute.Attribute(
        #         "", self, self.appearanceChangedEvent
        #     )
        #
        # if not hasattr(self, "_Object__selectedIcon"):
        #     self.__selectedIcon = attribute.Attribute(
        #         "", self, self.appearanceChangedEvent
        #     )
        #
        # if not hasattr(self, "_Object__ordering"):
        #     self.__ordering = attribute.Attribute(
        #         0, self, self.orderingChangedEvent
        #     )
        #
        # # Reconstruction des attributs dérivés de couleur.
        # if not hasattr(self, "_Object__derivedFgColorValue"):
        #     self.__derivedFgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__derivedFgColorSource"):
        #     self.__derivedFgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__derivedBgColorValue"):
        #     self.__derivedBgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedBgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__derivedBgColorSource"):
        #     self.__derivedBgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedBgColorChanged,
        #     )
        #
        # # Reconstruction des attributs dérivés d'icône.
        # if not hasattr(self, "_Object__derivedIconValue"):
        #     self.__derivedIconValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedIconChanged,
        #     )
        #
        # if not hasattr(self, "_Object__derivedIconSource"):
        #     self.__derivedIconSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedIconChanged,
        #     )
        #
        # # Reconstruction des attributs dérivés de police.
        # if not hasattr(self, "_Object__derivedFontValue"):
        #     self.__derivedFontValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedFontChanged,
        #     )
        #
        # if not hasattr(self, "_Object__derivedFontSource"):
        #     self.__derivedFontSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onDerivedFontChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFgColorValue"):
        #     self.__effectiveFgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFgColorSource"):
        #     self.__effectiveFgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFgColorDefault"):
        #     self.__effectiveFgColorDefault = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveBgColorValue"):
        #     self.__effectiveFgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveBgColorSource"):
        #     self.__effectiveFgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveBgColorDefault"):
        #     self.__effectiveFgColorDefault = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFontValue"):
        #     self.__effectiveFgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFontSource"):
        #     self.__effectiveFgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveFontDefault"):
        #     self.__effectiveFgColorDefault = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveIconValue"):
        #     self.__effectiveFgColorValue = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveIconSource"):
        #     self.__effectiveFgColorSource = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # if not hasattr(self, "_Object__effectiveIconDefault"):
        #     self.__effectiveFgColorDefault = attribute.Attribute(
        #         None,
        #         self,
        #         self._onEffectiveFgColorChanged,
        #     )
        #
        # # TEST
        # if not hasattr(self, "_Object__subject"):
        #     print("RECONSTRUCTION DES ATTRIBUTS OBJECT")
        #
        #     self.__init__(
        #         subject=state.get("subject", ""),
        #         description=state.get("description", ""),
        #         fgColor=state.get("fgColor"),
        #         bgColor=state.get("bgColor"),
        #         font=state.get("font"),
        #         icon=state.get("icon", ""),
        #         selectedIcon=state.get("selectedIcon", ""),
        #         ordering=state.get("ordering", 0),
        #     )
        # # A RETIRER

        # Restauration des données scalaires d'état
        # Restaure l'identifiant de l'objet
        # self.__id = state["id"]
        if "id" in state:
            self.__id = state["id"]
        # self.__creationDateTime = state["creationDateTime"]
        # Restaure la date de création
        if "creationDateTime" in state:
            self.__creationDateTime = state["creationDateTime"]

        # Alimentation de nos Attributes
        # Récupérer la valeur du sujet du dictionnaire d'état
        # print("_Object__subject présent ?", hasattr(self, "_Object__subject"))
        # log.debug(f"Object.__setstate__ : setSubject :")
        # self.setSubject(state["subject"], event=event)
        # log.debug(
        #     f"Object.__setstate__() - subject après set: {self.__subject.get()}"
        # )
        # self.setDescription(state["description"], event=event)
        # self.setForegroundColor(state["fgColor"], event=event)
        # self.setBackgroundColor(state["bgColor"], event=event)
        # self.setFont(state["font"], event=event)
        # self.setIcon(state["icon"], event=event)
        # self.setSelectedIcon(state["selectedIcon"], event=event)
        # self.setOrdering(state["ordering"], event=event)
        self.setSubject(state.get("subject", ""), event=event)
        self.setDescription(state.get("description", ""), event=event)
        self.setForegroundColor(state.get("fgColor", None), event=event)
        self.setBackgroundColor(state.get("bgColor", None), event=event)
        self.setFont(state.get("font", None), event=event)
        self.setIcon(state.get("icon", ""), event=event)
        self.setSelectedIcon(state.get("selectedIcon", ""), event=event)
        self.setOrdering(state.get("ordering", 0), event=event)

        # Set modification date/time last to overwrite changes made by the
        # setters above
        # Définit la date/heure de la date de modification pour écraser
        #  les modifications apportées par le setters ci-dessus.
        # Écrase les modifications de date faites par les Setters ci-dessus
        # self.__modificationDateTime = state["modificationDateTime"]
        self.__modificationDateTime = state.get(
            "modificationDateTime", DateTime.min
        )

    def __getcopystate__(self):
        """
        Renvoie un dictionnaire qui peut être transmis à __init__ lors de la création
        d'une copie de l'objet.

        E.g. copy = obj.__class__(**original.__getcopystate__())

        Returns :
            state (dict) : Le dictionnaire d'état pour créer une copie.
        """
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        # log.debug(f"Object.__getcopystate__ : avant update state={state}.")
        if state is None:
            state = dict()
        # Notez que nous ne mettons pas l'identifiant et la date/heure de création dans le dict state,
        # car une copie devrait obtenir un nouvel identifiant et une nouvelle date/heure de création.
        state.update(
            dict(
                subject=self.__subject.get(),
                description=self.__description.get(),
                fgColor=self.__fgColor.get(),
                bgColor=self.__bgColor.get(),
                font=self.__font.get(),
                icon=self.__icon.get(),
                selectedIcon=self.__selectedIcon.get(),
                ordering=self.__ordering.get(),
            )
        )
        # log.debug(f"Object.__getcopystate__ : retourne state={state}.")
        return state

    def copy(self):
        """
        Créez une copie de l'objet.

        Returns :
            (Object) Une nouvelle instance de l'objet avec le même état.
        """
        state = self.__getcopystate__()
        print("COPY STATE =", state)
        # print(f"object.Object.__getcopystate__ : DEBUG - __getcopystate__() : {state}")  # Ajoute ce print
        return self.__class__(**state)  # Accessor kind: Getter
        # return self.__class__(**self.__getcopystate__())

    @classmethod
    def monitoredAttributes(class_):
        """
        Obtenez la liste des attributs surveillés.

        Returns :
            (list) : La liste des attributs surveillés.
                     ["ordering", "subject", "description", "appearance"]
        """
        return ["ordering", "subject", "description", "appearance"]

    # Id:

    def id(self):
        """
        Obtenez l'ID de l'objet.

        Returns :
            (str) : L'ID de l'objet.
        """
        return self.__id

    # Custom attributes
    def customAttributes(self, sectionName):
        """
        Obtenez les attributs personnalisés pour un nom de section donné.

        Args :
            sectionName (str) : Le nom de la section.

        Returns :
            attributes (set[str]) : L'ensemble des attributs personnalisés.
        """
        attributes = set()
        # Pour toutes les lignes de description créées par des retours à la ligne:
        for line in self.description().split("\n"):
            # match sont celles qui correspondent à ?
            match = self.rx_attributes.match(line.strip())
            # Si match existe et le deuxième élément de match est sectionName alors :
            if match and match.group(1) == sectionName:
                # Ajouter le 3e élément de match à attributes.
                attributes.add(match.group(2))
        return attributes

    # Editing date/time:

    def creationDateTime(self):
        """
        Obtenez la date et l'heure de création de l'objet.

        Returns :
            (DateTime) : La date et l'heure de création.
        """
        return self.__creationDateTime

    def modificationDateTime(self):
        """
        Obtenez la date et l'heure de modification de l'objet.

        Returns :
            (DateTime) : La date et l'heure de modification.
        """
        return self.__modificationDateTime

    def setModificationDateTime(self, dateTime):
        """
        Définissez la date et l'heure de modification de l'objet.

        Args :
            dateTime (DateTime) : La date et l'heure de modification.
        """
        self.__modificationDateTime = dateTime

    @staticmethod
    # def modificationDateTimeSortFunction(**kwargs):
    def modificationDateTimeSortFunction():
        """
        Obtenez une fonction de tri pour trier par date et heure de modification.

        Returns :
            (function) La fonction de tri.
        """
        return lambda item: item.modificationDateTime()

    @staticmethod
    # def creationDateTimeSortFunction(**kwargs):
    def creationDateTimeSortFunction():
        """
        Obtenez une fonction de tri pour trier par date et heure de création.

        Returns :
            (function) La fonction de tri.
        """
        return lambda item: item.creationDateTime()

    # Subject:

    def subject(self):
        """
        Obtenir le sujet de l'objet.

        Returns :
            (str) : Le sujet de l'objet.
        """
        return (
            self.__subject.get()
        )  # AttributeError: 'CompositeObject' object has no attribute '_Object__subject'
        # return self.__subject

    def setSubject(self, subject, event=None):
        """
        Définissez le sujet de l'objet.

        Args :
            subject (str) : Le sujet à définir.
            event : Événement associé à la définition du sujet.
        """
        self.__subject.set(subject, event=event)

    def subjectChangedEvent(self, event):
        """
        Gérer l'événement de changement de sujet.

        Args :
            event : L'événement.
        """
        event.addSource(
            self, self.subject(), type=self.subjectChangedEventType()
        )

    @classmethod
    def subjectChangedEventType(class_):
        """
        Obtenir le type d’événement pour les événements à sujet modifié.

        Returns :
            (str) : Type d'événement pour les événements de changement de sujet.
        """
        # return "%s.subject" % class_
        return f"{class_}.subject"

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par sujet.

        Fonction à passer à list.sort lors du tri par sujet.

        Returns :
            (function) La fonction de tri.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject()
        else:
            return lambda item: item.subject().lower()

    @classmethod
    def subjectSortEventTypes(class_):
        """
        Obtenez les types d'événements qui influencent l'ordre de tri des sujets.

        Returns :
            (tuple) Les types d'événements.
        """
        # Est-ce que ce doit être vraiment un tuple ou une liste ?
        return (class_.subjectChangedEventType(),)

    # Ordering:

    def ordering(self):
        """
        Obtenez l'ordre de l'objet.

        Returns :
            (int) L'ordre.
        """
        return self.__ordering.get()

    def setOrdering(self, ordering, event=None):
        """
        Définissez l'ordre de l'objet.

        Args :
            ordering (int) : L'ordre à définir.
            event : Événement associé à la définition de l'ordre.
        """
        self.__ordering.set(ordering, event=event)

    def orderingChangedEvent(self, event):
        """
        Gérez l’événement de modification de l'ordre.

        Args :
            event : L'événement.
        """
        event.addSource(
            self, self.ordering(), type=self.orderingChangedEventType()
        )

    @classmethod
    def orderingChangedEventType(class_):
        """
        Obtenez le type d'événement pour ordonner les événements modifiés.

        Returns :
            (str) : Type d'événement pour classer les événements modifiés.
        """
        # return "%s.ordering" % class_
        return f"{class_}.ordering"

    @staticmethod
    def orderingSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par ordre.

        Returns :
            (function) La fonction de tri.
        """
        return lambda item: item.ordering()

    @classmethod
    def orderingSortEventTypes(class_):
        """
        Obtenez les types d’événements qui influencent l’ordre de tri.

        Returns :
            (tuple) Les types d'événements.
        """
        return (class_.orderingChangedEventType(),)

    # Description:

    def description(self):
        """
        Obtenir la description de l'objet.

        Returns :
            (str) La description de l'objet.
        """
        # log.debug(f"Object.description : Retourne {self.__description.get()}.")
        return self.__description.get()

    def setDescription(self, description, event=None):
        """
        Définir la description de l'objet.

        Args :
            description (str) : La description à définir.
            event : Événement associé à la définition de la description.
        """
        # self.__description.set(description, event=event)
        # Si l’appelant passe un event, il s’en occupe.
        #
        # Si None est passé, on crée un event et on le publie explicitement
        # une fois que set() a eu un effet.
        if event is None:
            event = patterns.Event()  # 👈 Création automatique si besoin
            shouldPublish = True  # 👈 Flag pour savoir si on doit publier
        else:
            shouldPublish = False

        if self.__description.set(description, event=event):
            if shouldPublish:
                # Publier manuellement l'événement uniquement s'il a été créé ici
                patterns.Publisher().notifyObservers(event)

    def descriptionChangedEvent(self, event):
        """
        Gérer l’événement de modification de description.

        Cet événement est déclenché lorsqu'une nouvelle description est définie.
        On enregistre la nouvelle description à la fois comme source et comme valeur.

        Args :
            event : (Event) L'événement à enrichir avec la source modifiée.
        """
        # event.addSource(
        #     self, self.description, type=self.descriptionChangedEventType()
        # )
        # essayer
        # self.addSource(
        #     event, self.description(), type=self.descriptionChangedEventType()
        # )  # Unresolved attribute reference 'addSource' for class 'Object'
        # event.addSource(
        #     self, self.description(), type=self.descriptionChangedEventType()
        # )
        # current_description = self.description()
        # print(f"DEBUG — descriptionChangedEvent : self.description() = {current_description!r}")
        # event.addSource(
        #     self, current_description, type=self.descriptionChangedEventType()
        # )
        # event.addSource(self.description(), self.description(), type=self.descriptionChangedEventType())
        # On récupère la description actuelle
        # new_description = self.description()  # str is not callable
        new_description = self.description()

        # DEBUG facultatif :
        log.debug(
            f"descriptionChangedEvent — new_description = {new_description!r}"
        )

        # Ajoute la description comme source et comme valeur pour ce type d'événement
        event.addSource(
            self,
            # new_description,               # source de l'événement
            new_description,  # valeur associée à cette source
            type=self.descriptionChangedEventType(),  # type d'événement
        )

    @classmethod
    def descriptionChangedEventType(class_) -> str:
        """
        Obtenez le type d’événement pour les événements modifiés dans la description.

        Returns :
            (str) : Le type d'événement pour la description des événements a changé.
        """
        # return "%s.description" % class_
        return f"{class_}.description"  # Alternative plus moderne mais moins compatible avec les anciennes versions de Python.

    @staticmethod
    def descriptionSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par description.

        Fonction à transmettre à list.sort lors du tri par description.

        Returns :
            (function) La fonction de tri.
        """
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.description()
        else:
            return lambda item: item.description().lower()

    @classmethod
    def descriptionSortEventTypes(class_):
        """
        Obtenez les types d’événements qui influencent l’ordre de tri des descriptions.

        Returns :
            (tuple) Les types d'événements.
        """
        return (class_.descriptionChangedEventType(),)

    # Color:

    def setForegroundColor(self, color, event=None):
        """
        Définissez la couleur de premier plan de l'objet.

        Args :
            color : La couleur à définir.
            event : L'événement associé à la définition de la couleur.
        """
        self.__fgColor.set(color, event=event)
        # self.appearanceChangedEvent(event)
        # Trigger computeEffective after SSOT update
        from . import appearance

        appearance.computeEffective(self, "fgColor")

    def foregroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la couleur de premier plan de l'objet.

        Args :
            recursive bool : (optional) S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns :
            La couleur de premier plan.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__fgColor.get()

    def setBackgroundColor(self, color, event=None):
        """
        Définissez la couleur d'arrière-plan de l'objet.

        Args :
            color : La couleur à définir.
            event : L'événement associé à la définition de la couleur.
        """
        self.__bgColor.set(color, event=event)
        # self.appearanceChangedEvent(event)
        # Trigger computeEffective after SSOT update
        from . import appearance

        appearance.computeEffective(self, "bgColor")

    def backgroundColor(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la couleur d'arrière-plan de l'objet.

        Args :
            recursive bool : (optionnal) S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Return : La couleur d’arrière-plan.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__bgColor.get()

    # Font:

    def font(self, recursive=False):  # pylint: disable=W0613
        """
        Obtenez la police de l'objet.

        Args :
            recursive bool : (optional) S'il faut obtenir la police de manière récursive. La valeur par défaut est False.

        Returns :
            La police.
        """
        # L'argument 'récursif' n'est pas réellement utilisé ici, mais certains codes
        # supposent des objets composites là où il n'y en a pas. Il s'agit de
        # la solution de contournement la plus simple.
        return self.__font.get()

    def setFont(self, font, event=None):
        """
        Définissez la police de l'objet.

        Args :
            font : La police à définir.
            event : L'événement associé à la définition de la police.
        """
        self.__font.set(font, event=event)
        # Trigger computeEffective after SSOT update
        from . import appearance

        appearance.computeEffective(self, "font")

    # Icons:

    def icon(self):
        """
        Obtenez l'icône de l'objet.

        Returns :
            L'icône.
        """
        return self.__icon.get()

    def setIcon(self, icon, event=None):
        """
        Définissez l'icône de l'objet.

        Args :
            icon : L'icône à définir.
            event : L'événement associé à la définition de l'icône.
        """
        self.__icon.set(icon, event=event)
        # Trigger computeEffective after SSOT update
        from . import appearance

        appearance.computeEffective(self, "icon")

    def selectedIcon(self):
        """
        Obtenez l'icône sélectionnée de l'objet.

        Returns :
            L'icône sélectionnée.
        """
        return self.__selectedIcon.get()

    def setSelectedIcon(self, selectedIcon, event=None):
        """
        Définir l'icône sélectionnée à l'objet.

        Args :
            selectedIcon : L'icône sélectionnée à définir.
            event : L'événement associé à la définition de l'icône sélectionnée.
        """
        self.__selectedIcon.set(selectedIcon, event=event)

    # Event types:

    @classmethod
    def appearanceChangedEventType(class_):
        """
        Obtenez le type d’événement pour les événements d’apparence modifiée.

        Returns :
            (str) : Le type d'événement pour les événements d'apparence a changé.
        """
        # return "%s.appearance" % class_
        return f"{class_}.appearance"

    def appearanceChangedEvent(self, event):
        """
        Gérer l’événement de modification d’apparence.

        Args :
            event : L'événement.
        """
        event.addSource(self, type=self.appearanceChangedEventType())

    # --- Derived SSOT Getters ---

    def derivedFgColor(self):
        return self.__derivedFgColorValue.get() or FIELD_DEFAULTS["fgColor"]

    def derivedFgColorSource(self):
        return (
            self.__derivedFgColorSource.get()
            or FIELD_NO_VALUE_SOURCE["fgColor"]
        )

    def derivedBgColor(self):
        return self.__derivedBgColorValue.get() or FIELD_DEFAULTS["bgColor"]

    def derivedBgColorSource(self):
        return (
            self.__derivedBgColorSource.get()
            or FIELD_NO_VALUE_SOURCE["bgColor"]
        )

    def derivedIcon(self):
        return self.__derivedIconValue.get() or FIELD_DEFAULTS["icon"]

    def derivedIconSource(self):
        return self.__derivedIconSource.get() or FIELD_NO_VALUE_SOURCE["icon"]

    def derivedFont(self):
        return self.__derivedFontValue.get() or FIELD_DEFAULTS["font"]

    def derivedFontSource(self):
        return self.__derivedFontSource.get() or FIELD_NO_VALUE_SOURCE["font"]

    # --- Derived SSOT Setters (for use by computeDerived) ---

    def setDerivedFgColor(self, value, source, event=None):
        self.__derivedFgColorValue.set(value, event=event)
        self.__derivedFgColorSource.set(source, event=event)

    def setDerivedBgColor(self, value, source, event=None):
        self.__derivedBgColorValue.set(value, event=event)
        self.__derivedBgColorSource.set(source, event=event)

    def setDerivedIcon(self, value, source, event=None):
        self.__derivedIconValue.set(value, event=event)
        self.__derivedIconSource.set(source, event=event)

    def setDerivedFont(self, value, source, event=None):
        self.__derivedFontValue.set(value, event=event)
        self.__derivedFontSource.set(source, event=event)

    # --- Derived Event Handlers ---

    def _onDerivedFgColorChanged(self, event):
        event.addSource(self, type=self.derivedFgColorChangedEventType())

    def _onDerivedBgColorChanged(self, event):
        event.addSource(self, type=self.derivedBgColorChangedEventType())

    def _onDerivedIconChanged(self, event):
        event.addSource(self, type=self.derivedIconChangedEventType())

    def _onDerivedFontChanged(self, event):
        event.addSource(self, type=self.derivedFontChangedEventType())

    # --- Derived Event Types ---

    @classmethod
    def derivedFgColorChangedEventType(class_):
        """Obtenez le type d’événement pour les événements de couleur de premier plan dérivée modifiée."""
        return "pubsub.derived.fgColor"

    @classmethod
    def derivedBgColorChangedEventType(class_):
        """Obtenez le type d’événement pour les événements de couleur de fond dérivée modifiée."""
        return "pubsub.derived.bgColor"

    @classmethod
    def derivedIconChangedEventType(class_):
        """Obtenez le type d’événement pour les événements d’icône dérivés modifiés."""
        return "pubsub.derived.icon"

    @classmethod
    def derivedFontChangedEventType(class_):
        """Obtenez le type d’événement pour les événements de police dérivés modifiés."""
        return "pubsub.derived.font"

    # --- Effective SSOT Getters ---

    def effectiveFgColor(self):
        """Obtenez la couleur de premier plan effective de l'objet."""
        return self.__effectiveFgColorValue.get() or FIELD_DEFAULTS["fgColor"]

    def effectiveFgColorSource(self):
        """Obtenez la source de la couleur de premier plan effective de l'objet."""
        return (
            self.__effectiveFgColorSource.get()
            or FIELD_NO_VALUE_SOURCE["fgColor"]
        )

    def effectiveFgColorDefault(self):
        """Obtenez la valeur par défaut de la couleur de premier plan effective de l'objet."""
        return (
            self.__effectiveFgColorDefault.get() or FIELD_DEFAULTS["fgColor"]
        )

    def effectiveBgColor(self):
        """Obtenez la couleur d'arrière-plan effective de l'objet."""
        return self.__effectiveBgColorValue.get() or FIELD_DEFAULTS["bgColor"]

    def effectiveBgColorSource(self):
        """Obtenez la source de la couleur d'arrière-plan effective de l'objet."""
        return (
            self.__effectiveBgColorSource.get()
            or FIELD_NO_VALUE_SOURCE["bgColor"]
        )

    def effectiveBgColorDefault(self):
        """Obtenir la valeur par défaut de la couleur d'arrière-plan effective de l'objet."""
        return (
            self.__effectiveBgColorDefault.get() or FIELD_DEFAULTS["bgColor"]
        )

    def effectiveIcon(self):
        """Obtenir le nom de l'icône effectif de l'objet."""
        return self.__effectiveIconValue.get() or FIELD_DEFAULTS["icon"]

    def effectiveIconSource(self):
        """Obtenir la source de l'icône effectif de l'objet."""
        return (
            self.__effectiveIconSource.get() or FIELD_NO_VALUE_SOURCE["icon"]
        )

    def effectiveFont(self):
        """Obtenir la police effective de l'objet."""
        return self.__effectiveFontValue.get() or FIELD_DEFAULTS["font"]

    def effectiveFontSource(self):
        """Obtenir la source de la police effective de l'objet."""
        return (
            self.__effectiveFontSource.get() or FIELD_NO_VALUE_SOURCE["font"]
        )

    def effectiveFontDefault(self):
        """Obtenir la police par défaut de l'objet."""
        return self.__effectiveFontDefault.get() or FIELD_DEFAULTS["font"]

    # --- Effective SSOT Setters (for use by computeEffective) ---

    def setEffectiveFgColor(self, value, default, source, event=None):
        """Set the effective foreground color, its default, and its source."""
        self.__effectiveFgColorValue.set(value, event=event)
        self.__effectiveFgColorDefault.set(default, event=event)
        self.__effectiveFgColorSource.set(source, event=event)

    def setEffectiveBgColor(self, value, default, source, event=None):
        """Set the effective background color, its default, and its source."""
        self.__effectiveBgColorValue.set(value, event=event)
        self.__effectiveBgColorDefault.set(default, event=event)
        self.__effectiveBgColorSource.set(source, event=event)

    def setEffectiveIcon(self, value, source, event=None):
        """Définir l'icône effectif."""
        # Icon has no default
        self.__effectiveIconValue.set(value, event=event)
        self.__effectiveIconSource.set(source, event=event)

    def setEffectiveFont(self, value, default, source, event=None):
        """Définir la valeur de la police à appliquer."""
        self.__effectiveFontValue.set(value, event=event)
        self.__effectiveFontDefault.set(default, event=event)
        self.__effectiveFontSource.set(source, event=event)

    # --- Effective Event Handlers ---

    def _onEffectiveFgColorChanged(self, event):
        event.addSource(self, type=self.effectiveFgColorChangedEventType())

    def _onEffectiveBgColorChanged(self, event):
        event.addSource(self, type=self.effectiveBgColorChangedEventType())

    def _onEffectiveIconChanged(self, event):
        event.addSource(self, type=self.effectiveIconChangedEventType())

    def _onEffectiveFontChanged(self, event):
        event.addSource(self, type=self.effectiveFontChangedEventType())

    # --- Effective Event Types ---

    @classmethod
    def effectiveFgColorChangedEventType(class_):
        """Obtenir le nom de l'événement pour changer la couleur de premier plan à appliquer."""
        return "pubsub.effective.fgColor"

    @classmethod
    def effectiveBgColorChangedEventType(class_):
        return "pubsub.effective.bgColor"

    @classmethod
    def effectiveIconChangedEventType(class_):
        return "pubsub.effective.icon"

    @classmethod
    def effectiveFontChangedEventType(class_):
        return "pubsub.effective.font"

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez les types d'événements pour les événements de modification.

        Returns :
            (list) : La liste des types d'événements.
        """
        # Récupération sécurisée et robuste des événements de la classe parente
        try:
            # eventTypes = super(Object, class_).modificationEventTypes()
            eventTypes = super().modificationEventTypes()
            # TypeError: SynchronizedObject.modificationEventTypes() missing 1 required positional argument: 'self'
            # @classmethod def cmeth(cls, arg):
            #  super().cmeth(arg)
        # except TypeError:  # Pas sûr de ses 2 lignes, utilisées lors du debuggage !
        #     eventTypes = super().modificationEventTypes(class_)  # Unexpected argument !
        except AttributeError:
            # except AttributeError or TypeError:
            # eventTypes = []
            eventTypes = list()
        if eventTypes is None:
            eventTypes = list()
            # eventTypes = []
        # return eventTypes + [
        return list(eventTypes) + [
            class_.subjectChangedEventType(),
            class_.descriptionChangedEventType(),
            class_.appearanceChangedEventType(),
            class_.orderingChangedEventType(),
        ]
        # # Révision :
        #
        # # La fonction hasattr vérifie si la classe parent a une méthode modificationEventTypes.
        # # If the parent class has a modificationEventTypes method, call it
        # if hasattr(super(), "modificationEventTypes"):
        #     # parent_events = super().modificationEventTypes(
        #     #     class_()
        #     # )  # changement avec initialisation de l'instance
        #     parent_events = super().modificationEventTypes()  # changement de la méthode de classe
        #
        # else:
        #     # Si la classe parent ne possède pas la méthode, une liste vide est utilisée par défaut.
        #     parent_events = []
        # # if parent_events is None:
        # #     parent_events = []
        # parent_events = list(parent_events or [])
        # # Les types d'événements du parent sont combinés avec les types d'événements spécifiques de la classe Object.
        # return parent_events + [
        #     class_.subjectChangedEventType(),
        #     class_.descriptionChangedEventType(),
        #     class_.appearanceChangedEventType(),
        #     class_.orderingChangedEventType(),]


# Les mixins doivent être avant les types parents ! Sauf ici !
# class CompositeObject(patterns.ObservableComposite, Object):  # Ajoute des problèmes
# La classe qui "possède" les attributs fondamentaux de l'objet
# (comme Object possède __subject) devrait généralement être le premier parent
# dans l'héritage multiple (ou être le parent le plus "à gauche"
# qui définit ces attributs), de sorte que son __init__ et __setstate__
# soient appelés tôt dans la chaîne super().
class CompositeObject(
    Object, patterns.composite.ObservableComposite
):  # Est le seul bon ordre !
    """
    Un objet composite peut contenir d'autres objets en tant qu'enfants.

    Cette classe étend Object et ObservableComposite pour fournir des méthodes
    supplémentaires pour gérer les objets enfants et leur état.

    Methods :
        - __getcopystate__ : Obtenir un dictionnaire qui peut être transmis à __init__ lors de la création d'une copie de l'objet composite.
        - __setstate__ : Définir l'état de l'objet à partir de la désérialisation.
        - monitoredAttributes : Obtenir la liste des attributs surveillés.
        - subject : Obtenir le sujet de l'objet composite.
        - subjectChangedEvent : Gérer l'événement de changement de sujet.
        - subjectSortFunction : Obtenir une fonction de tri pour trier par sujet.
        - description : Obtenir la description de l'objet composite.
        - getDescription : Obtenir la description de l'objet composite.
        - isExpanded : Vérifier si le contexte de l'objet composite est développé.
        - expandedContexts : Obtenir les contextes développés de l'objet composite.
        - expand : Développer un contexte spécifique de l'objet composite.
        - expansionChangedEventType : Obtenir le type d'événement pour les événements de changement d'expansion.
        - expansionChangedEvent : Gérer l'événement de changement d'expansion.
        - expandedContextsChangedEventType : Obtenir le type d'événement pour les événements de changement de contextes développés.
        - appearanceChangedEvent : Gérer l'événement de modification d’apparence.
        - foregroundColor : Obtenir la couleur de premier plan de l'objet composite.
        - backgroundColor : Obtenir la couleur d'arrière-plan de l'objet composite.
        - font : Obtenir la police de l'objet composite.
        - icon : Obtenir l'icône de l'objet composite.
        - selectedIcon : Obtenir l'icône sélectionnée de l'objet composite.
        - pluralOrSingularIcon : Obtenir l'icône plurielle ou singulière de l'objet composite en fonction du nombre d'enfants.
        - modificationEventTypes : Obtenir les types d'événements pour les événements de modification.
        - markDeleted : Marquer l'objet composite comme supprimé.
        - markNew : Marquer l'objet composite comme nouveau.
        - markDirty : Marquer l'objet composite comme modifié.
        - cleanDirty : Marquer l'objet composite comme propre.

    Attributes :
        - __expandedContexts : Un ensemble privé pour stocker les contextes développés de l'objet composite.

    Examples :


    """

    def __init__(self, *args, **kwargs):
        """
        Initialise l'instance CompositeObject.

        Args :
            *args : Variable length argument list.
            **kwargs : Arbitrary keyword arguments.
        """
        self.__expandedContexts = set(kwargs.pop("expandedContexts", []))
        # super().__init__(*args, **kwargs)
        # Transmet les arguments uniquement si le parent **n'est pas `object`**
        # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
        # if type(self).__mro__[1] is not object:
        #     try:
        #         super().__init__(*args, **kwargs)
        #     except TypeError:
        #         super().__init__()
        # else:
        #     super().__init__()  # Sécurisé pour `object`
        # # Plus de super() perdu dans une hiérarchie complexe ! :

        # # On extrait manuellement les kwargs destinés à Composite
        # composite_keys = ("children", "parent")
        # composite_kwargs = {k: kwargs.pop(k) for k in composite_keys if k in kwargs}
        #
        # # Initialisation manuelle des deux parents
        # Object.__init__(self, *args, **kwargs)
        # patterns.ObservableComposite.__init__(self, **composite_kwargs)

        # Tu dois appeler toi-même Object.__init__() et Composite.__init__(),
        # puisque super() ne peut pas les gérer correctement en raison de
        # l’héritage en diamant.
        # On extrait les kwargs pour Composite uniquement
        children = kwargs.pop("children", None)
        parent = kwargs.pop("parent", None)

        log.debug(
            f"CompositeObject.__init__() → kwargs avant Object.__init__ : {kwargs}"
        )
        log.debug(
            f"CompositeObject.__init__() : children : {children}, parent : {parent}"
        )

        # Initialisation de la logique Object (subject, description, etc.)
        Object.__init__(self, *args, **kwargs)
        log.debug(
            f"CompositeObject.__init__() → kwargs après Object avant Composite: {kwargs}"
        )

        # Initialisation manuelle de Composite
        patterns.composite.Composite.__init__(
            self, children=children, parent=parent
        )
        log.debug(
            f"CompositeObject.__init__() → kwargs après Composite: {kwargs}"
        )

    def __getcopystate__(self) -> dict:
        """
        Renvoie un dictionnaire qui peut être transmis à __init__ lors de la création
        d'une copie de l'objet composite.

        Returns :
            state (dict) : Le dictionnaire d'état pour créer une copie.
        """
        print("CompositeObject.__getcopystate__ : enfants =", self.children())
        try:
            state = super().__getcopystate__()
        except AttributeError:
            state = dict()
        # log.debug(f"CompositeObject.__getcopystate__ : __getstate__() avant subject.get() : {self.__subject.get()}, state avant update {state}.")
        # AttributeError: 'Task' object has no attribute '_CompositeObject__subject'
        log.debug(
            f"CompositeObject.__getcopystate__ : state après super et avant update {state}."
        )
        state.update(dict(expandedContexts=self.expandedContexts()))
        log.debug(
            f"CompositeObject.__getcopystate__ : retourne state {state}."
        )
        return state

    def __setstate__(self, state, event=None):
        # C'est crucial : appeler d'abord le parent. Cela permettra à Object.__setstate__
        # de s'exécuter et de gérer correctement l'attribut 'subject'.
        # super().__setstate__(state, event)  # Erreur, il faut qu'un seul argument !
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        # NE PAS TENTER DE POPPER OU DE DÉFINIR 'subject' ICI.
        # L'attribut 'subject' est déjà géré par Object.__setstate__.

        # ... (ajouter ici le code pour gérer les attributs spécifiques à CompositeObject,
        #       comme les enfants si tu en as une gestion personnalisée dans __setstate__)

    @classmethod
    def monitoredAttributes(class_) -> list[str]:
        # def monitoredAttributes(cls):
        """
        Obtenir la liste des attributs surveillés.

        Returns :
            (list) : The list of monitored attributes.
        """
        # return Object.monitoredAttributes() + ["expandedContexts"]
        try:
            attrs = super().monitoredAttributes()
        except AttributeError:
            attrs = []
        attrs.append("expandedContexts")
        return attrs

    # Subject:

    def subject(self, recursive=False):  # pylint: disable=W0221
        """
        Obtenir le sujet de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir le sujet de manière récursive. La valeur par défaut est False.

        Returns :
            (str) : Le sujet de l'objet composite.
        """
        # log.debug(f"CompositeObject.subject : Obtenir le sujet de {self.id()}.")
        subject = super().subject()
        # if recursive and self.parent():
        #     # subject = "%s -> %s" % (
        #     #     self.parent().subject(recursive=True),
        #     #     subject,
        #     # )
        #     subject = f"{self.parent().subject(recursive=True)} -> {subject}"
        if recursive and (
            (hasattr(self, "parent") and callable(self.parent))
            or self.parent()
        ):
            parent = self.parent()
            if parent:
                subject = f"{parent.subject(recursive=True)} -> {subject}"
        # log.debug(
        #     f"CompositeObject.subject : retourne le sujet de {self.__class__.__name__} id={self.id()} : {subject}."
        # )
        # RecursionError: maximum recursion depth exceeded
        return subject

    def subjectChangedEvent(self, event):
        """
        Gérer l'événement de changement de sujet.

        Args :
            event : L'événement.
        """
        super().subjectChangedEvent(event)
        for child in self.children():
            child.subjectChangedEvent(event)

    @staticmethod
    def subjectSortFunction(**kwargs):
        """
        Obtenez une fonction de tri pour trier par sujet.

        Fonction à passer à list.sort lors du tri par sujet.

        Args :
            **kwargs :

        Returns :
            (function) : La fonction de tri.
        """
        recursive = kwargs.get("treeMode", False)
        if kwargs.get("sortCaseSensitive", False):
            return lambda item: item.subject(recursive=recursive)
        else:
            return lambda item: item.subject(recursive=recursive).lower()

    # Description:
    def description(self, recursive=False):  # pylint: disable=W0221,W0613
        # Allow for the recursive flag, but ignore it
        return super().description()

    def getDescription(self, recursive=False):  # pylint: disable=W0221,W0613
        """
        Obtenez la description de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir la description de manière récursive. La valeur par défaut est False.

        Returns :
            (str) : La description de l'objet composite.
        """
        # Autoriser l'indicateur récursif, mais l'ignorer !
        # return super().description()
        return super().description()

    # État d'expansion :

    # Remarque : l'état d'expansion est stocké par contexte. Un contexte est une simple chaîne
    # identifiant (sans virgules) pour distinguer les différents contextes,
    # c'est-à-dire les téléspectateurs. Un objet composite peut être développé dans un contexte et
    # réduit dans un autre.

    def isExpanded(self, context="None"):
        """
        Vérifiez si l'objet composite est développé dans le contexte spécifié.

        Renvoie un booléen indiquant si l'objet composite est
        développé dans le contexte spécifié.

        Args :
            context (str) : (optional) Le contexte. La valeur par défaut est "Aucun".

        Returns :
            (bool) : True si l'objet composite est développé, False sinon.
        """
        return context in self.__expandedContexts

    def expandedContexts(self):
        """
        Obtenez la liste des contextes dans lesquels l'objet composite est développé.

        Returns :
            (list) : La liste des contextes.
        """
        return list(self.__expandedContexts)

    def expand(self, expand=True, context="None", notify=True):
        """
        Développez ou réduisez l'objet composite dans le contexte spécifié.

        Args :
            expand (bool, optional) : Que ce soit pour s'étendre ou s'effondrer. La valeur par défaut est True.
            context (str, optional) : Le contexte. La valeur par défaut est "Aucun".
            notify (bool, optional) : S'il faut envoyer une notification. La valeur par défaut est True.
        """
        if expand == self.isExpanded(context):
            return
        if expand:
            self.__expandedContexts.add(context)
        else:
            self.__expandedContexts.discard(context)
        if notify:
            pub.sendMessage(
                self.expansionChangedEventType(), newValue=expand, sender=self
            )

    @classmethod
    def expansionChangedEventType(cls):
        """
        Obtenez le type d'événement pour les changements d'état d'expansion.

        Le type d'événement utilisé pour notifier les changements dans l'état d'expansion
        d'un objet composite.

        Returns :
            (str) : Le type d’événement pour les changements d’état d’expansion.
        """
        # return "pubsub.%s.expandedContexts" % cls.__name__.lower()
        return f"pubsub.{cls.__name__.lower()}.expandedContexts"

    def expansionChangedEvent(self, event):
        """
        Gérer l’événement de modification d’extension.

        Args :
            event : L'événement.
        """
        event.addSource(self, type=self.expansionChangedEventType())

    # Le ChangeMonitor s'attend à cela...
    @classmethod
    def expandedContextsChangedEventType(class_):
        """
        Obtenir le type d’événement pour les modifications de contextes étendus.

        Returns :
            (str) : Le type d'événement pour les contextes étendus change.
        """
        return class_.expansionChangedEventType()

    # Appearance:

    def appearanceChangedEvent(self, event):
        """
        Gérer l’événement de modification d’apparence.

        Args :
            event : L'événement.
        """
        super().appearanceChangedEvent(event)
        # Supposons que la plupart du temps, nos enfants changent également d'apparence.
        for child in self.children():
            child.appearanceChangedEvent(event)

    def foregroundColor(self, recursive=False):
        """
        Obtenez la couleur de premier plan de l'objet composite.

        Args :
            recursive (bool, optional) : S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Returns :
            La couleur de premier plan.
        """
        myFgColor = super().foregroundColor()
        if not myFgColor and recursive and self.parent():
            return self.parent().foregroundColor(recursive=True)
        else:
            return myFgColor

    def backgroundColor(self, recursive=False):
        """
        Obtenez la couleur d'arrière-plan de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir la couleur de manière récursive. La valeur par défaut est False.

        Return : La couleur d’arrière-plan.
        """
        myBgColor = super().backgroundColor()
        if not myBgColor and recursive and self.parent():
            return self.parent().backgroundColor(recursive=True)
        else:
            return myBgColor

    def font(self, recursive=False):
        """
        Obtenez la police de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir la police de manière récursive. La valeur par défaut est False.

        Returns :
            La police.
        """
        myFont = super().font()
        if not myFont and recursive and self.parent():
            return self.parent().font(recursive=True)
        else:
            return myFont

    def icon(self, recursive=False):
        """
        Obtenez l'icône de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir l'icône de manière récursive. La valeur par défaut est False.

        Returns :
            L'icône.
        """
        myIcon = super().icon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().icon(recursive=True)
        return self.pluralOrSingularIcon(myIcon, native=super().icon() == "")

    def selectedIcon(self, recursive=False):
        """
        Obtenez l'icône sélectionnée de l'objet composite.

        Args :
            recursive (bool) : (optional) S'il faut obtenir l'icône sélectionnée de manière récursive. La valeur par défaut est False.

        Returns :
            L'icône sélectionnée.
        """
        myIcon = super().selectedIcon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().selectedIcon(recursive=True)
        return self.pluralOrSingularIcon(
            myIcon, native=super().selectedIcon() == ""
        )

    def pluralOrSingularIcon(self, myIcon, native=True):
        """
        Obtenez l'icône au pluriel ou au singulier selon que l'objet a ou non des enfants.

        Args :
            myIcon : L'icône de base.
            native (bool) : (optional) Si l'icône provient des paramètres utilisateur. La valeur par défaut est True.

        Returns :
            L'icône plurielle ou singulière.
        """
        hasChildren = any(
            child for child in self.children() if not child.isDeleted()
        )
        mapping = (
            icon.itemImagePlural if hasChildren else icon.itemImageSingular
        )
        # Si l'icône provient des paramètres utilisateur, mettez-la uniquement au pluriel ; c'est probablement
        # la voie du moindre étonnement
        if native or hasChildren:
            return mapping.get(myIcon, myIcon)
        return myIcon

    # Types d'événements :

    @classmethod
    def modificationEventTypes(class_):
        """
        Obtenez les types d'événements pour les événements de modification.

        Returns :
            (list) : La liste des types d'événements.
        """
        # return super().modificationEventTypes() + [class_.expansionChangedEventType()]
        # parent_events = super().modificationEventTypes()

        # La fonction hasattr vérifie si la classe parent a une méthode modificationEventTypes.
        # If the parent class has a modificationEventTypes method, call it
        if hasattr(super(), "modificationEventTypes"):
            parent_events = (
                super().modificationEventTypes()
            )  # changement avec initialisation de l'instance
            # parent_events = super().modificationEventTypes()  # changement de la méthode de classe

        else:
            # Si la classe parent ne possède pas la méthode, une liste vide est utilisée par défaut.
            parent_events = []
        if parent_events is None:
            parent_events = []
        # Appel explicite à la méthode de ObservableComposite
        # observable_events = patterns.ObservableComposite.modificationEventTypes()
        return (
            [
                class_.addChildEventType(),
                class_.removeChildEventType(),
            ]
            + parent_events
            + [class_.expansionChangedEventType()]
        )
        # Changement possible :
        #     parent_events = set(super().modificationEventTypes())
        #     # Ajout des événements spécifiques à CompositeObject en évitant les doublons
        #     parent_events.update({
        #         class_.addChildEventType(),
        #         class_.removeChildEventType(),
        #         class_.expansionChangedEventType(),
        #     })
        #     return list(parent_events)

    # Remplacez les méthodes SynchronizedObject pour marquer également les objets enfants

    @patterns.eventSource
    def markDeleted(self, event=None):
        """
        Marquez l'objet composite et ses enfants comme supprimés.

        Args :
            event : L'événement associé au marquage de l'objet comme supprimé.
        """
        super().markDeleted(event=event)
        for child in self.children():
            child.markDeleted(event=event)

    @patterns.eventSource
    def markNew(self, event=None):
        """
        Marquez l'objet composite et ses enfants comme nouveaux.

        Args :
            event : L'événement associé au marquage de l'objet comme nouveau.
        """
        super().markNew(event=event)
        for child in self.children():
            child.markNew(event=event)

    @patterns.eventSource
    def markDirty(self, force=False, event=None):
        """
        Marquez l'objet composite et ses enfants comme sales (modifiés).

        Args :
            force (bool) : (optional) Forcer le marquage de l'objet comme sale. La valeur par défaut est False.
            event : L'événement associé au marquage de l'objet comme sale.
        """
        super().markDirty(force, event=event)
        for child in self.children():
            child.markDirty(force, event=event)

    @patterns.eventSource
    def cleanDirty(self, event=None):
        """
        Marque l'objet composite et ses enfants comme non sales (None).

        Args :
            event : L'événement associé au marquage de l'objet comme non sale.
        """
        super().cleanDirty(event=event)
        for child in self.children():
            child.cleanDirty(event=event)
