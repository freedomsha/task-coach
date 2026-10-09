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

Les tests doivent couvrir la validation d'état,
la protection des clés du parent, et la sérialisation sûre:

Points clés validés par les tests :

    Gestion des objets possédés :
        Les tests vérifient que la méthode setFoos ne déclenche pas d'événement inutilement lorsque les objets restent inchangés.
        Un événement est correctement déclenché lorsque des objets sont ajoutés via setFoos.

    Suppression des objets :
        La suppression sans arguments (removeFoos) est gérée sans erreur.

Étapes suivantes :

    Couverture des tests : Si tu souhaites encore améliorer la robustesse, voici des cas supplémentaires à tester :
        Vérifier que addFoos et removeFoos déclenchent correctement les événements.
        Tester la sérialisation (__getstate__ et __setstate__).
        Tester le clonage via __getcopystate__.

    Optimisation des dépendances : Assure-toi que les modules importés comme patterns et base ne contiennent pas de fonctionnalités inutilisées pour éviter un code encombré.

    Validation fonctionnelle : Si ce composant est intégré dans un système plus large, exécute des tests d'intégration pour vérifier son comportement dans différents scénarios.

Cas couverts par les tests

Voici les scénarios validés:

    Ajout d’objets (addFoos) : Les tests confirment que l’ajout d’objets génère des notifications appropriées.

    Suppression d’objets (removeFoos) : La suppression d’objets (avec ou sans arguments) déclenche les événements attendus.

    Tests supplémentaires :
        Vérification des notifications lorsque les objets gérés changent.
        Sérialisation et restauration de l’état.
        Clonage des objets et validation de leur indépendance.
"""

# from builtins import object
from ... import tctest

# from taskcoachlib.domain import base
from taskcoachlib.domain.base import owner
from taskcoachlib.domain.base.object import Object
from taskcoachlib import patterns


class OwnerUnderTest(Object, metaclass=owner.DomainObjectOwnerMetaclass):
    __ownedType__ = "Foo"


class Foo(object):
    def __init__(self):
        self._is_deleted = False

    def isDeleted(self):
        return self._is_deleted

    def copy(self):
        return Foo()


class OwnerTest(tctest.TestCase):
    def setUp(self):
        super().setUp()
        self.owner = OwnerUnderTest()
        self.events = []  # Initialise une liste pour capturer les événements
        # self.events = {}

    def onEvent(self, event):
        # print(f"Événement capturé par onEvent: {event}")
        # print(f"Structure : {event.__dict__}")
        self.events.append(event)

    # pylint: disable=E1101

    def testSetObjects_NoNotificationWhenUnchanged(self):
        patterns.Publisher().registerObserver(
            # self.onEvent, self.owner.foosChangedEventType()
            self.onEvent,
            self.owner.foosChangedEventType(),
        )
        self.owner.setFoos([])
        self.assertFalse(self.events)

    def testSetObjects_NotificationWhenCanged(self):
        patterns.Publisher().registerObserver(
            # self.onEvent, self.owner.foosChangedEventType()
            self.onEvent,
            self.owner.foosChangedEventType(),
        )
        self.owner.setFoos([Foo()])
        self.assertEqual(1, len(self.events))

    def testRemoveNoObjects(self):
        self.owner.removeFoos()
        self.assertFalse(self.owner.foos())

    # Vérifier que addFoos et removeFoos déclenchent correctement les événements
    def testAddFoos_NotificationTriggered(self):
        """
        Ce test assure que les appels à addFoos notifient correctement les observateurs.
        :return:
        """
        patterns.observer.Publisher().registerObserver(
            self.onEvent, self.owner.foosChangedEventType()
        )
        foo1, foo2 = Foo(), Foo()
        self.owner.addFoos(foo1, foo2)

        self.assertEqual(
            len(self.events), 1
        )  # Vérifie qu'un événement est déclenché
        self.assertTrue(
            hasattr(self.events[0], "sources")
        )  # Vérifie que sources existe
        self.assertIn(
            self.owner, self.events[0].sources()
        )  # Vérifie que le propriétaire est source
        # Vérifie que l'événement contient les bonnes données (self.owner comme clé ou source attendue)
        # self.assertIn(self.owner.foosChangedEventType(), self.events[0].keys())
        # event_data = self.events[0].__dict__
        event_data = self.events[
            0
        ].sourcesAndValuesByType()  # Accède aux données de l'événement
        # print(f"Événement capturé par testAddFoos_NotificationTriggered (bonnes données ?): {event_data}")
        # Vérifie si la clé attendue existe
        self.assertIn(self.owner.foosChangedEventType(), event_data.keys())

        self.assertEqual(
            self.events[0].sources(), {self.owner}
        )  # sources n'est pas une liste mais un ensemble set()

    def testRemoveFoos_NotificationTriggered(self):
        """
        Ce test assure que les appels à removeFoos notifient correctement les observateurs.
        :return:
        """
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])
        patterns.Publisher().registerObserver(
            self.onEvent, self.owner.foosChangedEventType()
        )
        self.owner.removeFoos(foo1)
        self.assertEqual(
            len(self.events), 1
        )  # Vérifie qu'un événement est déclenché
        self.assertTrue(
            hasattr(self.events[0], "sources")
        )  # Vérifie que sources existe
        self.assertEqual(
            self.events[0].sources(), {self.owner}
        )  # sources n'est pas une liste mais un ensemble set()

    # Tester la sérialisation (__getstate__ et __setstate__)
    def testSerialization_GetAndSetState(self):
        """
        Ces tests vérifient que l'état d'un objet peut être sauvegardé et restauré sans perte de données.
        :return:
        """
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Obtenir l'état actuel
        state = (
            self.owner.__getstate__()
        )  # La méthode __getstate__ sauvegarde l’état actuel de OwnerUnderTest.
        self.assertIn("foos", state)
        self.assertEqual(state["foos"], [foo1, foo2])

        # Restaurer l'état
        new_owner = OwnerUnderTest()
        new_owner.__setstate__(state)
        self.assertEqual(
            new_owner.foos(), [foo1, foo2]
        )  # La méthode __setstate__ restaure correctement cet état.

    # Tester le clonage (__getcopystate__)
    def testCloning_CopyState(self):
        """
        Ces tests assurent que le clonage crée des copies indépendantes des objets gérés.
        :return:
        """
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Obtenir une copie de l'état
        state = self.owner.__getcopystate__()
        # self.assertIn("foos", state)

        # Vérifier que les objets sont des copies distinctes
        copied_foos = state["foos"]
        self.assertEqual(len(copied_foos), 2)
        self.assertNotEqual(copied_foos[0], foo1)  # Nouvelle instance
        self.assertNotEqual(copied_foos[1], foo2)
        # La méthode __getcopystate__ produit des copies indépendantes des objets gérés, validant ainsi le comportement attendu.

    # Tests for serialization safety (new tests for owner.py modifications)

    def testGetState_ValidatesParentState(self):
        """
        Vérifie que __getstate__ valide l'état du parent avant de l'utiliser.
        """
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Obtenir l'état - ne doit pas lever d'exception
        try:
            state = self.owner.__getstate__()
            self.assertIn("foos", state)
            self.assertIn("status", state)  # Clé requise du parent
            self.assertIn("id", state)  # Clé requise du parent
        except AssertionError:
            self.fail(
                "__getstate__ should not raise AssertionError with valid parent state"
            )

    def testGetState_ProtectsParentKeys(self):
        """
        Vérifie que __getstate__ préserve toutes les clés du parent.
        """
        foo1 = Foo()
        self.owner.setFoos([foo1])

        # Obtenir l'état
        state = self.owner.__getstate__()

        # Vérifier que les clés du parent sont présentes
        parent_keys = {
            "id",
            "status",
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
        }
        for key in parent_keys:
            self.assertIn(
                key, state, f"Parent key {key} missing from serialized state"
            )

        # Vérifier que les clés des objets gérés sont aussi présentes
        self.assertIn("foos", state)

    def testSetState_RaisesAssertionOnMissingCoreKeys(self):
        """
        Vérifie que __setstate__ détecte un état corrompu avec des clés manquantes.
        """
        # Créer un état incomplet (sans "status")
        incomplete_state = {
            "id": "test-id",
            "subject": "test",
            "description": "test",
            # "status" manquant intentionnellement
            "foos": [],
        }

        new_owner = OwnerUnderTest()

        # Vérifier qu'une AssertionError est levée
        with self.assertRaises(AssertionError) as context:
            new_owner.__setstate__(incomplete_state)

        error_msg = str(context.exception)
        self.assertIn("Etat corrompu", error_msg)

    def testSerializationRoundTrip_PreservesOwnedObjects(self):
        """
        Vérifie qu'un cycle complet de sérialisation/désérialisation préserve les objets gérés.
        """
        # Créer l'état initial
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Sérialiser
        original_state = self.owner.__getstate__()

        # Créer un nouvel objet et restaurer l'état
        new_owner = OwnerUnderTest()
        new_owner.__setstate__(original_state)

        # Vérifier que les objets gérés sont restaurés
        restored_foos = new_owner.foos()
        self.assertEqual(len(restored_foos), 2)
        self.assertEqual(restored_foos, [foo1, foo2])

        # Vérifier que l'état complètement restauré est identique
        restored_state = new_owner.__getstate__()
        self.assertEqual(original_state, restored_state)

    def testSerializationRoundTrip_PreservesParentAttributes(self):
        """
        Vérifie que la sérialisation préserve les attributs du parent (Object).
        """
        # Modifier des attributs du parent
        self.owner.setSubject("Test Subject")
        self.owner.setDescription("Test Description")
        foo1 = Foo()
        self.owner.setFoos([foo1])

        # Obtenir l'état
        original_state = self.owner.__getstate__()
        original_id = original_state["id"]
        original_status = original_state["status"]

        # Créer un nouvel objet et restaurer l'état
        new_owner = OwnerUnderTest()
        new_owner.__setstate__(original_state)

        # Vérifier que les attributs du parent sont préservés
        self.assertEqual(new_owner.subject(), "Test Subject")
        self.assertEqual(new_owner.description(), "Test Description")
        self.assertEqual(new_owner.id(), original_id)
        self.assertEqual(new_owner.getStatus(), original_status)

        # Vérifier que les objets gérés sont aussi préservés
        self.assertEqual(len(new_owner.foos()), 1)

    def testGetState_ContainsOnlyPublicKeys(self):
        """
        Vérifie que __getstate__ filtre les clés privées de Object et SynchronizedObject.
        """
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Obtenir l'état
        state = self.owner.__getstate__()

        # Vérifier que les clés privées de Object et SynchronizedObject sont filtrées
        # Note: Les clés comme _OwnerUnderTest__foos sont présentes car elles viennent
        # de la métaclasse qui génère dynamiquement les attributs
        for key in state.keys():
            self.assertFalse(
                key.startswith("_Object__")
                or key.startswith("_SynchronizedObject__"),
                f"State contains undesired private key from parent classes: {key}",
            )

    def testSetObjects_PreservesParentState(self):
        """
        Vérifie que setObjects ne corrompt pas l'état du parent.
        """
        # Modifier un attribut du parent
        self.owner.setSubject("Original Subject")
        original_id = self.owner.id()
        original_status = self.owner.getStatus()

        # Ajouter des objets gérés
        foo1, foo2 = Foo(), Foo()
        self.owner.setFoos([foo1, foo2])

        # Vérifier que l'état du parent est préservé
        self.assertEqual(self.owner.subject(), "Original Subject")
        self.assertEqual(self.owner.id(), original_id)
        self.assertEqual(self.owner.getStatus(), original_status)

    def testAddFoos_PreservesParentStateAndOwnedObjects(self):
        """
        Vérifie que addFoos ajoute des objets sans perdre l'état du parent ou les objets existants.
        """
        # Initialiser avec une liste d'objets
        foo1 = Foo()
        self.owner.setFoos([foo1])
        self.owner.setSubject("Test Subject")

        # Ajouter d'autres objets
        foo2, foo3 = Foo(), Foo()
        self.owner.addFoos(foo2, foo3)

        # Vérifier que tous les objets sont présents
        foos = self.owner.foos()
        self.assertEqual(len(foos), 3)
        self.assertIn(foo1, foos)
        self.assertIn(foo2, foos)
        self.assertIn(foo3, foos)

        # Vérifier que l'état du parent est préservé
        self.assertEqual(self.owner.subject(), "Test Subject")

    def testRemoveFoos_PreservesParentStateAndRemainingObjects(self):
        """
        Vérifie que removeFoos supprime des objets sans perdre l'état du parent ou les objets restants.
        """
        # Initialiser avec une liste d'objets
        foo1, foo2, foo3 = Foo(), Foo(), Foo()
        self.owner.setFoos([foo1, foo2, foo3])
        self.owner.setSubject("Test Subject")

        # Supprimer un objet
        self.owner.removeFoos(foo2)

        # Vérifier que les objets restants sont présents
        foos = self.owner.foos()
        self.assertEqual(len(foos), 2)
        self.assertIn(foo1, foos)
        self.assertIn(foo3, foos)
        self.assertNotIn(foo2, foos)

        # Vérifier que l'état du parent est préservé
        self.assertEqual(self.owner.subject(), "Test Subject")
