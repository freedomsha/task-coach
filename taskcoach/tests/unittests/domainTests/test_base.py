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

L'extrait de code Python fourni semble être lié au test d'une classe nommée
base.Object et de ses sous-classes dans une application de gestion de tâches.
Le test qui échoue est testGetState dans la classe ObjectTest.

Voici une ventilation du problème potentiel et des suggestions de débogage :

Problème potentiel :

Le message d'erreur "self. assertRaises(IndexError, self.collection.getObjectById, "id")" suggère que le test pourrait s'attendre à une IndexError à déclencher lors de l'appel de getObjectById sur une collection vide. Cependant, le test défaillant semble être dans ObjectTest qui traite d'un seul objet, pas d'une collection. Il peut y avoir une inadéquation entre la configuration du test et ce que le test tente d'accomplir.

Suggestions de débogage :

    Vérifiez la configuration du test : vérifiez la méthode de configuration (setUp) dans ObjectTest. Assurez-vous qu'il crée une instance de base.Object et l'attribue à une variable (par exemple, self.object).

    Vérifiez testGetState : examinez la méthode testGetState dans ObjectTest. Il essaie d'appeler self.object.getState() et risque d'échouer. Voici quelques possibilités :
        Implémentation manquante : si base.Object n'a pas de méthode getState définie, une AttributeError sera générée. Assurez-vous que base.Object implémente cette méthode comme prévu.
        Accès incorrect : peut-être que la méthode devrait être appelée directement sur l'instance (self.object), pas via __getstate__.

    Déclarations d'impression : ajoutez des instructions d'impression dans testGetState pour inspecter les valeurs de self.object et le résultat de self.object.__getstate__(). Cela peut aider à identifier si l'objet est créé correctement et si le dictionnaire d'état est généré comme prévu.

    Vérifiez le résultat attendu : vérifiez à nouveau le résultat attendu pour testGetState. Le test peut s'attendre à un format spécifique pour le dictionnaire d'état renvoyé par __getstate__.

Conseils supplémentaires :

    Exécutez les tests individuellement pour identifier celui qui échoue.
    Utilisez un débogueur pour parcourir les tests. le code ligne par ligne et inspectez les variables.
    Pensez à rechercher en ligne des problèmes similaires ou des exemples liés au test des méthodes __getstate__.

En suivant ces étapes, vous devriez être en mesure d'identifier la cause première de l'échec du test et de le corriger en conséquence.
"""

import gc
import weakref
import wx

from ... import tctest
from taskcoachlib import patterns
from taskcoachlib.domain import base, date


class SynchronizedObjectTest(tctest.TestCase):
    """Tests for base.SynchronizedObject."""  # pylint: disable=W0105

    def setUp(self):
        super().setUp()
        self.object = base.SynchronizedObject()
        self.events = []

    def onEvent(self, event):
        self.events.append(event)

    def registerObserver(
        self, eventType, eventSource=None
    ):  # pylint: disable=W0221
        patterns.Publisher().registerObserver(self.onEvent, eventType)

    def assertObjectStatus(self, expectedStatus):
        self.assertEqual(expectedStatus, self.object.getStatus())

    def assertOneEventReceived(self, eventSource, eventType, *values):
        self.assertEqual(
            [patterns.Event(eventType, eventSource, *values)], self.events
        )

    def testInitialStatus(self):
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NEW)

    def testMarkDeleted(self):
        self.object.markDeleted()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_DELETED)

    def testMarkDeletedNotification(self):
        self.registerObserver(self.object.markDeletedEventType())
        self.object.markDeleted()
        self.assertOneEventReceived(
            self.object,
            self.object.markDeletedEventType(),
            self.object.getStatus(),
        )

    def testMarkNewObjectAsNotDeleted(self):
        self.object.cleanDirty()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NONE)

    def testMarkDeletedObjectAsUndeleted(self):
        self.object.markDeleted()
        self.object.cleanDirty()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NONE)

    def testMarkNotDeletedNotification(self):
        self.object.markDeleted()
        self.registerObserver(self.object.markNotDeletedEventType())
        self.object.cleanDirty()
        self.assertOneEventReceived(
            self.object,
            self.object.markNotDeletedEventType(),
            self.object.getStatus(),
        )

    def testSetStateToDeletedCausesNotification(self):
        """

        Il ne vérifie pas seulement que :
        self.getStatus() == STATUS_DELETED
        Il vérifie aussi qu'un événement :
        object.markdeleted
        a été émis.

        """
        # Ce test est intéressant car il impose une contrainte souvent oubliée lors de la migration Python 2 → Python 3 : __setstate__() ne doit pas seulement restaurer l'état interne, il doit aussi rejouer les notifications nécessaires.
        # Changer le status:
        # self.object.getStatus() == self.object.STATUS_DELETED
        # et émettre un événement self.object.markDeletedEventType()
        # avec comme valeur self.object.STATUS_DELETED
        self.object.markDeleted()
        # Enregistrer l'état actuel de l'objet
        state = self.object.__getstate__()
        print(f"testSetStateToDeletedCausesNotification : state={state}")
        # Le dictionnaire doit contenir l'information que l'objet est supprimé.
        # Vider les événements déjà générés ou l'état "dirty"
        self.object.cleanDirty()
        # On écoute uniquement les événements de suppression.
        self.registerObserver(self.object.markDeletedEventType())
        #
        self.object.__setstate__(
            state
        )  # C'est ici que la migration python 2->3 casse souvent.
        self.assertOneEventReceived(
            self.object,
            self.object.markDeletedEventType(),
            self.object.STATUS_DELETED,
        )

    def testSetStateToNotDeletedCausesNotification(self):
        """"""
        # Sauvegarde l'état (status=1) de l'objet
        state = self.object.__getstate__()
        # Change l'état comme marqué effacé (3)
        self.object.markDeleted()
        #
        self.registerObserver(self.object.markNotDeletedEventType())
        # Enregistre l'état actuel de l'objet avec l'ancien état nouveau (1)
        self.object.__setstate__(state)
        # Vérification de l'état actuel de l'objet après restauration
        self.assertOneEventReceived(
            self.object,
            self.object.markNotDeletedEventType(),
            self.object.STATUS_NEW,
        )


class ObjectSubclass(base.Object):
    pass


class ObjectTest(tctest.TestCase):
    def setUp(self):
        super().setUp()
        self.tcobject = base.Object()
        print(
            f"ObjectTest.setUp : initialisation self.tcobject={self.tcobject}, id={self.tcobject.id()}, creationDateTime={self.tcobject.creationDateTime()}, modificationDateTime={self.tcobject.modificationDateTime()}, subject={self.tcobject.subject()}, description={self.tcobject.description()}, status={self.tcobject.getStatus()}, fgColor={self.tcobject.foregroundColor()}, bgColor={self.tcobject.backgroundColor()}, font={self.tcobject.font()}, icon={self.tcobject.icon()}, selectedIcon={self.tcobject.selectedIcon()}"
        )
        self.subclassObject = ObjectSubclass()
        self.eventsReceived = []
        for eventType in (
            self.tcobject.subjectChangedEventType(),
            self.tcobject.descriptionChangedEventType(),
            self.tcobject.appearanceChangedEventType(),
        ):
            patterns.Publisher().registerObserver(self.onEvent, eventType)
        print(
            f"ObjectTest.setUp : fin de setUp self.tcobject={self.tcobject}, id={self.tcobject.id()}, creationDateTime={self.tcobject.creationDateTime()}, modificationDateTime={self.tcobject.modificationDateTime()}, subject={self.tcobject.subject()}, description={self.tcobject.description()}, status={self.tcobject.getStatus()}, fgColor={self.tcobject.foregroundColor()}, bgColor={self.tcobject.backgroundColor()}, font={self.tcobject.font()}, icon={self.tcobject.icon()}, selectedIcon={self.tcobject.selectedIcon()}"
        )
        print(
            "ObjectTest.setUp : self.tcobject.modificationEventTypes()=",
            self.tcobject.modificationEventTypes(),
        )

    def onEvent(self, event):
        self.eventsReceived.append(event)

    # Basic tests:

    def testCyclicReference(self):
        """
        Le test testCyclicReference veut s'assurer que :

        Si on détruit l'objet principal,
        toutes ses dépendances (comme les attributs)
        ne maintiennent pas de référence forte,
        donc il est collecté par le ramasse-miettes (GC).

        Returns : None

        """
        domainObject = base.Object()  # création d'un objet
        weak = weakref.ref(domainObject)  # on garde une référence faible
        del domainObject  # Assuming CPython  # on supprime la référence principale
        print(f"weak={weak}")
        gc.collect()  # 🔄 Forcer la collecte des objets non référencés
        self.assertTrue(weak() is None)  # on vérifie que l'objet a été détruit

    # Custom attributes tests:

    def testCustomAttributes(self):
        self.tcobject.setDescription(
            "\n[mailto:cc=foo@bar.com]\n[mailto:cc=baz@spam.com]\n"
        )
        self.assertEqual(
            self.tcobject.customAttributes("mailto"),
            {"cc=foo@bar.com", "cc=baz@spam.com"},
        )

    # Id tests:

    def testSetIdOnCreation(self):
        domainObject = base.Object(id="123")
        self.assertEqual("123", domainObject.id())

    def testIdIsAString(self):
        self.assertEqual(type(""), type(self.tcobject.id()))

    def testDifferentObjectsHaveDifferentIds(self):
        self.assertNotEqual(base.Object().id(), self.tcobject.id())

    def testCopyHasDifferentId(self):
        objectId = self.tcobject.id()  # Force generation of id
        copy = self.tcobject.copy()
        self.assertNotEqual(copy.id(), objectId)

    # Creation Date/time tests:

    def testSetCreationDateTimeOnCreation(self):
        creation_datetime = date.DateTime(2012, 12, 12, 10, 0, 0)
        domain_object = base.Object(creationDateTime=creation_datetime)
        self.assertEqual(creation_datetime, domain_object.creationDateTime())

    def testCreationDateTimeIsSetWhenNotPassed(self):
        now = date.Now()
        creation_datetime = self.tcobject.creationDateTime()
        minute = date.TimeDelta(seconds=60)
        self.assertTrue(now - minute < creation_datetime < now + minute)

    # Modification Date/time tests:

    def testSetModificationDateTimeOnCreation(self):
        modification_datetime = date.DateTime(2012, 12, 12, 10, 0, 0)
        domain_object = base.Object(modificationDateTime=modification_datetime)
        self.assertEqual(
            modification_datetime, domain_object.modificationDateTime()
        )

    def testModificationDateTimeIsNotSetWhenNotPassed(self):
        self.assertEqual(
            date.DateTime.min, self.tcobject.modificationDateTime()
        )

    # Subject tests:

    def testSubjectIsEmptyByDefault(self):
        self.assertEqual("", self.tcobject.subject())

    def testSetSubjectOnCreation(self):
        domainObject = base.Object(subject="Hi")
        self.assertEqual("Hi", domainObject.subject())

    def testSetSubject(self):
        self.tcobject.setSubject("New subject")
        self.assertEqual("New subject", self.tcobject.subject())

    def testSetSubjectCausesNotification(self):
        self.tcobject.setSubject("New subject")
        self.assertEqual(
            patterns.Event(
                self.tcobject.subjectChangedEventType(),
                self.tcobject,
                "New subject",
            ),
            self.eventsReceived[0],
        )

    def testSetSubjectUnchangedDoesNotCauseNotification(self):
        self.tcobject.setSubject("")
        self.assertFalse(self.eventsReceived)

    def testSubjectChangedNotificationIsDifferentForSubclass(self):
        self.subclassObject.setSubject("New")
        self.assertFalse(self.eventsReceived)

    # Description tests:

    def testDescriptionIsEmptyByDefault(self):
        # self.assertFalse(self.object.description())
        self.assertFalse(self.tcobject.description())
        # self.assertFalse(self.tcobject.getDescription())

    def testSetDescriptionOnCreation(self):
        domainObject = base.Object(description="Hi")
        self.assertEqual("Hi", domainObject.description())
        # self.assertEqual("Hi", domainObject.getDescription())

    def testSetDescription(self):
        self.tcobject.setDescription("New description")
        # self.assertEqual("New description", self.object.description())
        self.assertEqual("New description", self.tcobject.description())

    def testSetDescriptionCausesNotification(self):
        self.tcobject.setDescription(
            "New description"
        )  # On modifie la description
        self.assertEqual(
            patterns.Event(
                self.tcobject.descriptionChangedEventType(),  # Type d’événement
                # self.tcobject.description(),  # Ancienne valeur (attendue)
                self.tcobject,
                "New description",  # Nouvelle valeur
            ),
            self.eventsReceived[0],  # Événement réellement reçu
        )
        # event = patterns.Event()  # 👈 Crée un événement vide à remplir
        # self.tcobject.setDescription("New description", event=event)  # 👈 Le passe à setDescription
        # self.assertEqual(
        #     patterns.Event(
        #         self.tcobject.descriptionChangedEventType(),  # type d'événement
        #         {"New description": ("New description",)},    # contenu attendu
        #     ),
        #     event  # 👈 compare avec l’événement généré
        # )

    def testSetDescriptionUnchangedDoesNotCauseNotification(self):
        self.tcobject.setDescription("")
        self.assertFalse(self.eventsReceived)

    def testDescriptionChangedNotificationIsDifferentForSubclass(self):
        self.subclassObject.setDescription("New")
        self.assertFalse(self.eventsReceived)

    # State tests:

    def testGetState(self):
        print(f"testGetState : tcobject={self.tcobject}")
        self.assertEqual(
            dict(
                subject="",
                description="",
                id=self.tcobject.id(),
                status=self.tcobject.getStatus(),
                fgColor=None,
                bgColor=None,
                font=None,
                icon="",
                selectedIcon="",
                creationDateTime=self.tcobject.creationDateTime(),
                modificationDateTime=self.tcobject.modificationDateTime(),
                ordering=self.tcobject.ordering(),
            ),
            self.tcobject.__getstate__(),
        )  # Problème __getstate__ contient maintenant plus d'objet :
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

    def testSetState(self):
        newState = dict(
            subject="New",
            description="New",
            id=None,
            status=self.tcobject.STATUS_DELETED,
            fgColor=wx.GREEN,
            bgColor=wx.RED,
            font=wx.SWISS_FONT,
            icon="icon",
            selectedIcon="selectedIcon",
            creationDateTime=date.DateTime(2012, 12, 12, 12, 0, 0),
            modificationDateTime=date.DateTime(2012, 12, 12, 12, 1, 0),
            ordering=42,
        )
        self.tcobject.__setstate__(newState)
        self.assertEqual(newState, self.tcobject.__getstate__())

    def testSetState_SendsOneNotification(self):
        """
        Vérifie que la restauration d'un objet supprimé
        génère exactement une notification de suppression.
        """
        newState = dict(
            subject="New",
            description="New",
            id=None,
            status=self.tcobject.STATUS_DELETED,
            fgColor=wx.GREEN,
            bgColor=wx.RED,
            font=wx.SWISS_FONT,
            icon="icon",
            selectedIcon="selectedIcon",
            creationDateTime=date.DateTime(2013, 1, 1, 0, 0, 0),
            modificationDateTime=date.DateTime(2013, 1, 1, 1, 0, 0),
            ordering=42,
        )
        patterns.Publisher().registerObserver(
            self.onEvent,
            self.tcobject.markDeletedEventType(),
        )
        self.tcobject.__setstate__(newState)
        self.assertEqual(1, len(self.eventsReceived))
        self.assertEqual(
            [
                patterns.Event(
                    self.tcobject.markDeletedEventType(),
                    self.tcobject,
                    self.tcobject.STATUS_DELETED,
                )
            ],
            self.eventsReceived,
        )

    # copy tests:

    def testCopy_IdIsNotCopied(self):
        copy = self.tcobject.copy()
        self.assertNotEqual(copy.id(), self.tcobject.id())

    def testCopy_CreationDateTimeIsNotCopied(self):
        copy = self.tcobject.copy()
        # Use >= to prevent failures on fast computers with low time granularity
        self.assertTrue(
            copy.creationDateTime() >= self.tcobject.creationDateTime()
        )

    def testCopy_ModificationDateTimeIsNotCopied(self):
        self.tcobject.setModificationDateTime(
            date.DateTime(2013, 1, 1, 1, 0, 0)
        )
        copy = self.tcobject.copy()
        self.assertEqual(date.DateTime.min, copy.modificationDateTime())

    def testCopy_SubjectIsCopied(self):
        self.tcobject.setSubject("New subject")
        copy = self.tcobject.copy()
        self.assertEqual(copy.subject(), self.tcobject.subject())

    def testCopy_DescriptionIsCopied(self):
        self.tcobject.setDescription("New description")
        copy = self.tcobject.copy()
        # self.assertEqual(copy.description(), self.object.description())
        # self.assertEqual(copy.getDescription(), self.tcobject.description())
        self.assertEqual(copy.description(), self.tcobject.description())

    def testCopy_ForegroundColorIsCopied(self):
        self.tcobject.setForegroundColor(wx.RED)
        copy = self.tcobject.copy()
        self.assertEqual(
            copy.foregroundColor(), self.tcobject.foregroundColor()
        )

    def testCopy_BackgroundColorIsCopied(self):
        self.tcobject.setBackgroundColor(wx.RED)
        copy = self.tcobject.copy()
        self.assertEqual(
            copy.backgroundColor(), self.tcobject.backgroundColor()
        )

    def testCopy_FontIsCopied(self):
        self.tcobject.setFont(wx.SWISS_FONT)
        copy = self.tcobject.copy()
        self.assertEqual(copy.font(), self.tcobject.font())

    def testCopy_IconIsCopied(self):
        self.tcobject.setIcon("icon")
        copy = self.tcobject.copy()
        self.assertEqual(copy.icon(), self.tcobject.icon())

    def testCopy_ShouldUseSubclassForCopy(self):
        copy = self.subclassObject.copy()
        self.assertEqual(copy.__class__, self.subclassObject.__class__)

    # Color tests

    def testDefaultForegroundColor(self):
        self.assertEqual(None, self.tcobject.foregroundColor())

    def testSetForegroundColor(self):
        self.tcobject.setForegroundColor(wx.GREEN)
        self.assertEqual(wx.GREEN, self.tcobject.foregroundColor())

    def testSetForegroundColorWithTupleColor(self):
        self.tcobject.setForegroundColor((255, 0, 0, 255))
        self.assertEqual(
            wx.Colour(255, 0, 0, 255), self.tcobject.foregroundColor()
        )

    def testSetForegroundColorOnCreation(self):
        domainObject = base.Object(fgColor=wx.GREEN)
        self.assertEqual(wx.GREEN, domainObject.foregroundColor())

    def testForegroundColorChangedNotification(self):
        self.tcobject.setForegroundColor(wx.BLACK)
        self.assertEqual(1, len(self.eventsReceived))

    def testDefaultBackgroundColor(self):
        self.assertEqual(None, self.tcobject.backgroundColor())

    def testSetBackgroundColor(self):
        self.tcobject.setBackgroundColor(wx.RED)
        self.assertEqual(wx.RED, self.tcobject.backgroundColor())

    def testSetBackgroundColorWithTupleColor(self):
        self.tcobject.setBackgroundColor((255, 0, 0, 255))
        self.assertEqual(
            wx.Colour(255, 0, 0, 255), self.tcobject.backgroundColor()
        )

    def testSetBackgroundColorOnCreation(self):
        domainObject = base.Object(bgColor=wx.GREEN)
        self.assertEqual(wx.GREEN, domainObject.backgroundColor())

    def testBackgroundColorChangedNotification(self):
        self.tcobject.setBackgroundColor(wx.BLACK)
        self.assertEqual(1, len(self.eventsReceived))

    # Font tests:

    def testDefaultFont(self):
        self.assertEqual(None, self.tcobject.font())

    def testSetFont(self):
        self.tcobject.setFont(wx.SWISS_FONT)
        self.assertEqual(wx.SWISS_FONT, self.tcobject.font())

    def testSetFontOnCreation(self):
        domainObject = base.Object(font=wx.SWISS_FONT)
        self.assertEqual(wx.SWISS_FONT, domainObject.font())

    def testFontChangedNotification(self):
        self.tcobject.setFont(wx.SWISS_FONT)
        self.assertEqual(1, len(self.eventsReceived))

    # Icon tests:

    def testDefaultIcon(self):
        self.assertEqual("", self.tcobject.icon())

    def testSetIcon(self):
        self.tcobject.setIcon("icon")
        self.assertEqual("icon", self.tcobject.icon())

    def testSetIconOnCreation(self):
        domainObject = base.Object(icon="icon")
        self.assertEqual("icon", domainObject.icon())

    def testIconChangedNotification(self):
        self.tcobject.setIcon("icon")
        self.assertEqual(1, len(self.eventsReceived))

    def testDefaultSelectedIcon(self):
        self.assertEqual("", self.tcobject.selectedIcon())

    def testSetSelectedIcon(self):
        self.tcobject.setSelectedIcon("selected")
        self.assertEqual("selected", self.tcobject.selectedIcon())

    def testSelectedIconAfterSettingRegularIconOnly(self):
        self.tcobject.setIcon("icon")
        self.assertEqual("", self.tcobject.selectedIcon())

    def testSetSelectedIconOnCreation(self):
        domainObject = base.Object(selectedIcon="icon")
        self.assertEqual("icon", domainObject.selectedIcon())

    def testSelectedIconChangedNotification(self):
        self.tcobject.setSelectedIcon("icon")
        self.assertEqual(1, len(self.eventsReceived))

    # Event types:

    def testModificationEventTypes(self):
        self.assertEqual(
            [
                self.tcobject.subjectChangedEventType(),
                self.tcobject.descriptionChangedEventType(),
                self.tcobject.appearanceChangedEventType(),
                self.tcobject.orderingChangedEventType(),
            ],
            self.tcobject.modificationEventTypes(),
        )

    def testGetstateDoesNotContainPrivateAttributes(self):
        """
        Vérifie que __getstate__ ne retourne aucun attribut privé de type _Classe__attribut.
        """
        state = self.tcobject.__getstate__()

        # Vérifie que toutes les clés sont 'publiques' (pas de noms mangle)
        for key in state:
            self.assertFalse(
                key.startswith("_Object__")
                or key.startswith("_SynchronizedObject__"),
                f"L'état contient une clé privée indésirable : {key}",
            )

    # Tests for serialization safety (validate_state and protect_parent_keys)

    def testValidateState_RaisesAssertionErrorWhenStatusIsMissing(self):
        """
        Vérifie que validate_state() lève une AssertionError quand une clé requise est absente.
        """
        incomplete_state = {
            "subject": "test",
            "description": "test",
            # 'status' est manquant
        }
        with self.assertRaises(AssertionError) as context:
            self.tcobject.validate_state(incomplete_state)
        self.assertIn("status", str(context.exception))

    def testValidateState_PassesWhenAllCoreKeysPresent(self):
        """
        Vérifie que validate_state() ne lève pas d'exception quand toutes les clés requises sont présentes.
        """
        complete_state = self.tcobject.__getstate__()
        # La validation ne doit pas lever d'exception
        try:
            self.tcobject.validate_state(complete_state)
        except AssertionError:
            self.fail(
                "validate_state() should not raise AssertionError with complete state"
            )

    def testProtectParentKeys_RaisesWhenParentKeyIsLost(self):
        """
        Vérifie que protect_parent_keys() détecte quand une clé héritée disparaît.
        """
        parent_state = {"id": "123", "status": 1, "subject": "test"}
        child_state = {"subject": "test"}  # 'id' et 'status' manquent

        with self.assertRaises(AssertionError) as context:
            base.Object.protect_parent_keys(parent_state, child_state)
        # Vérifier que le message d'erreur mentionne la clé perdue
        error_msg = str(context.exception)
        self.assertIn("Clé héritée perdue", error_msg)

    def testProtectParentKeys_PassesWhenAllKeysArePresent(self):
        """
        Vérifie que protect_parent_keys() ne lève pas d'exception quand toutes les clés du parent sont présentes.
        """
        parent_state = {"id": "123", "status": 1, "subject": "test"}
        child_state = {
            "id": "123",
            "status": 1,
            "subject": "test",
            "description": "new",
        }

        # La méthode ne doit pas lever d'exception
        try:
            result = base.Object.protect_parent_keys(parent_state, child_state)
            self.assertEqual(child_state, result)
        except AssertionError:
            self.fail(
                "protect_parent_keys() should not raise AssertionError when all keys are present"
            )

    def testSerializationPreservesCoreAttributes(self):
        """
        Vérifie que la sérialisation préserve tous les attributs essentiels.
        """
        # Modifier plusieurs attributs de l'objet
        self.tcobject.setSubject("Test Subject")
        self.tcobject.setDescription("Test Description")
        self.tcobject.setForegroundColor(wx.RED)
        self.tcobject.setBackgroundColor(wx.GREEN)

        # Sérialiser l'état
        state = self.tcobject.__getstate__()

        # Vérifier que tous les attributs essentiels sont présents
        essential_keys = {
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
        for key in essential_keys:
            self.assertIn(
                key, state, f"Key {key} missing from serialized state"
            )

        # Vérifier que les valeurs sont correctes
        self.assertEqual("Test Subject", state["subject"])
        self.assertEqual("Test Description", state["description"])
        self.assertEqual(wx.RED, state["fgColor"])
        self.assertEqual(wx.GREEN, state["bgColor"])

    def testStateRoundTrip_PreservesAllData(self):
        """
        Vérifie que les données ne sont pas perdues lors d'une sérialisation/désérialisation complète.
        """
        # Configurer un objet avec des valeurs
        self.tcobject.setSubject("Test Subject")
        self.tcobject.setDescription("Test Description")
        self.tcobject.setForegroundColor(wx.RED)
        self.tcobject.setBackgroundColor(wx.GREEN)
        self.tcobject.setFont(wx.SWISS_FONT)
        self.tcobject.setIcon("test_icon")
        self.tcobject.setSelectedIcon("selected_icon")
        self.tcobject.setOrdering(42)

        # Obtenir l'état
        original_state = self.tcobject.__getstate__()

        # Créer un nouvel objet et lui donner le même état
        new_object = base.Object()
        new_object.__setstate__(original_state)

        # Obtenir le nouvel état
        new_state = new_object.__getstate__()

        # Vérifier que les états sont identiques
        self.assertEqual(original_state, new_state)

    def testSynchronizedObjectSerializationPreservesStatus(self):
        """
        Vérifie que le status de SynchronizedObject est préservé lors de la sérialisation.
        """
        # Marquer l'objet comme supprimé
        self.tcobject.markDeleted()

        # Sérialiser
        state = self.tcobject.__getstate__()

        # Vérifier que le status est préservé
        self.assertIn("status", state)
        self.assertEqual(
            base.SynchronizedObject.STATUS_DELETED, state["status"]
        )

        # Créer un nouvel objet et restaurer l'état
        new_object = base.Object()
        new_object.__setstate__(state)

        # Vérifier que le status a été restauré
        self.assertEqual(
            base.SynchronizedObject.STATUS_DELETED, new_object.getStatus()
        )


class CompositeObjectTest(tctest.TestCase):
    def setUp(self):
        super().setUp()
        self.compositeObject = base.CompositeObject()
        self.child = None
        self.eventsReceived = []

    def onEvent(self, event):
        self.eventsReceived.append(event)

    def addChild(self, **kwargs):
        self.child = base.CompositeObject(**kwargs)
        self.compositeObject.addChild(self.child)
        self.child.setParent(self.compositeObject)

    def removeChild(self):
        self.compositeObject.removeChild(self.child)

    def testIsExpanded(self):
        self.assertFalse(self.compositeObject.isExpanded())

    def testExpand(self):
        self.compositeObject.expand()
        self.assertTrue(self.compositeObject.isExpanded())

    def testCollapse(self):
        self.compositeObject.expand()
        self.compositeObject.expand(False)
        self.assertFalse(self.compositeObject.isExpanded())

    def testSetExpansionStateViaConstructor(self):
        compositeObject = base.CompositeObject(expandedContexts=["None"])
        self.assertTrue(compositeObject.isExpanded())

    def testSetExpansionStatesViaConstructor(self):
        compositeObject = base.CompositeObject(
            expandedContexts=["context1", "context2"]
        )
        self.assertEqual(
            ["context1", "context2"],
            sorted(compositeObject.expandedContexts()),
        )

    def testExpandInContext_DoesNotChangeExpansionStateInDefaultContext(self):
        self.compositeObject.expand(context="some_viewer")
        self.assertFalse(self.compositeObject.isExpanded())

    def testExpandInContext_DoesChangeExpansionStateInGivenContext(self):
        self.compositeObject.expand(context="some_viewer")
        self.assertTrue(self.compositeObject.isExpanded(context="some_viewer"))

    def testIsExpandedInUnknownContext_ReturnsFalse(self):
        self.assertFalse(self.compositeObject.isExpanded(context="whatever"))

    def testGetContextsWhereExpanded(self):
        self.assertEqual([], self.compositeObject.expandedContexts())

    def testRecursiveSubject(self):
        self.compositeObject.setSubject("parent")  # Sujet du parent
        self.addChild(subject="child")  # Ajoute un enfant avec son sujet
        print(f"[TEST DEBUG] self.child.subject() = {self.child.subject()!r}")
        # self.child.setSubject("child")
        self.assertEqual(
            "parent -> child", self.child.subject(recursive=True)
        )  # Test la chaîne récursive

    def testSubjectNotification(self):
        self.addChild(subject="child")
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=self.compositeObject.subjectChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setSubject("parent")
        self.assertEqual(
            [
                patterns.Event(
                    self.compositeObject.subjectChangedEventType(),
                    self.child,
                    "child",
                )
            ],
            self.eventsReceived,
        )

    def testSubItemUsesParentForegroundColor(self):
        self.addChild()
        self.compositeObject.setForegroundColor(wx.RED)
        self.assertEqual(wx.RED, self.child.foregroundColor(recursive=True))

    def testSubItemDoesNotUseParentForegroundColorIfItHasItsOwnForegroundColor(
        self,
    ):
        self.addChild(fgColor=wx.RED)
        self.compositeObject.setForegroundColor(wx.BLUE)
        self.assertEqual(wx.RED, self.child.foregroundColor(recursive=True))

    def testApperanceChangedNotificationWhenForegroundColorChanges(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.appearanceChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setForegroundColor(wx.RED)
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentBackgroundColor(self):
        self.addChild()
        self.compositeObject.setBackgroundColor(wx.RED)
        self.assertEqual(wx.RED, self.child.backgroundColor(recursive=True))

    def testSubItemDoesNotUseParentBackgroundColorIfItHasItsOwnBackgroundColor(
        self,
    ):
        self.addChild(bgColor=wx.RED)
        self.compositeObject.setBackgroundColor(wx.BLUE)
        self.assertEqual(wx.RED, self.child.backgroundColor(recursive=True))

    def testBackgroundColorChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.appearanceChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setBackgroundColor(wx.RED)
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentFont(self):
        self.addChild()
        self.compositeObject.setFont(wx.ITALIC_FONT)
        self.assertEqual(wx.ITALIC_FONT, self.child.font(recursive=True))

    def testSubItemDoesNotUseParentFontIfItHasItsOwnFont(self):
        """
        Tester si un sous-item n'utilise pas la police du parent
        s'il a sa propre police.
        """
        self.addChild(font=wx.SWISS_FONT)
        self.compositeObject.setFont(wx.ITALIC_FONT)
        self.assertEqual(wx.SWISS_FONT, self.child.font(recursive=True))

    def testFontChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.appearanceChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setFont(wx.SWISS_FONT)
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentIcon(self):
        self.addChild()
        self.compositeObject.setIcon("icon")
        self.assertEqual("icon", self.child.icon(recursive=True))

    def testSubItemDoesNotUseParentIconIfItHasItsOwnIcon(self):
        self.addChild(icon="childIcon")
        self.compositeObject.setIcon("icon")
        self.assertEqual("childIcon", self.child.icon(recursive=True))

    def testIconChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.appearanceChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setIcon("icon")
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentSelectedIcon(self):
        self.addChild()
        self.compositeObject.setSelectedIcon("icon")
        self.assertEqual("icon", self.child.selectedIcon(recursive=True))

    def testSubItemDoesNotUseParentSelectedIconIfItHasItsOwnSelectedIcon(self):
        self.addChild(selectedIcon="childIcon")
        self.compositeObject.setSelectedIcon("icon")
        self.assertEqual("childIcon", self.child.selectedIcon(recursive=True))

    def testSubItemUsesParentSelectedIconEvenIfItHasItsOwnIcon(self):
        self.addChild(icon="childIcon")
        self.compositeObject.setSelectedIcon("icon")
        self.assertEqual("icon", self.child.selectedIcon(recursive=True))

    def testSelectedIconChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.appearanceChangedEventType(),
            eventSource=self.child,
        )
        self.compositeObject.setSelectedIcon("icon")
        self.assertEqual(1, len(self.eventsReceived))

    def testCompositeWithChildrenUsesPluralIconIfAvailable(self):
        self.compositeObject.setIcon("book_icon")
        self.assertEqual(
            "book_icon", self.compositeObject.icon(recursive=True)
        )
        self.addChild()
        self.assertEqual(
            "books_icon", self.compositeObject.icon(recursive=True)
        )
        self.assertEqual(
            "book_icon", self.compositeObject.icon(recursive=False)
        )

    def testCompositeWithChildrenUsesPluralSelectedIconIfAvailable(self):
        self.compositeObject.setSelectedIcon("book_icon")
        self.assertEqual(
            "book_icon", self.compositeObject.selectedIcon(recursive=True)
        )
        self.addChild()
        self.assertEqual(
            "books_icon", self.compositeObject.selectedIcon(recursive=True)
        )
        self.assertEqual(
            "book_icon", self.compositeObject.selectedIcon(recursive=False)
        )

    def testCompositeWithoutChildrenDoesNotUseSingularIconIfAvailable(self):
        self.compositeObject.setIcon("books_icon")
        self.assertEqual(
            "books_icon", self.compositeObject.icon(recursive=False)
        )
        self.assertEqual(
            "books_icon", self.compositeObject.icon(recursive=True)
        )

    def testCompositeWithoutChildrenDoesNotUseSingularSelectedIconIfAvailable(
        self,
    ):
        self.compositeObject.setSelectedIcon("books_icon")
        self.assertEqual(
            "books_icon", self.compositeObject.selectedIcon(recursive=False)
        )
        self.assertEqual(
            "books_icon", self.compositeObject.selectedIcon(recursive=True)
        )

    def testChildOfCompositeUsesSingularIconIfAvailable(self):
        """
        Test si l'enfant d'un composite utilise l'icône singulier
        si elle est disponible.
        """
        # Assigner un icône au composite
        self.compositeObject.setIcon("books_icon")
        # Ajouter un enfant au composite
        self.addChild()
        # Vérifier que l'icône du composite est correcte
        self.assertEqual("book_icon", self.child.icon(recursive=True))

    def testChildOfCompositeUsesSingularSelectedIconIfAvailable(self):
        self.compositeObject.setSelectedIcon("books_icon")
        self.addChild()
        self.assertEqual("book_icon", self.child.selectedIcon(recursive=True))

    def testParentUsesSingularIconAfterChildRemoved(self):
        self.compositeObject.setIcon("book_icon")
        self.addChild()
        self.assertEqual(
            "books_icon", self.compositeObject.icon(recursive=True)
        )
        self.removeChild()
        self.assertEqual(
            "book_icon", self.compositeObject.icon(recursive=True)
        )

    def testParentUsesSingularSelectedIconAfterChildRemoved(self):
        self.compositeObject.setSelectedIcon("book_icon")
        self.addChild()
        self.assertEqual(
            "books_icon", self.compositeObject.selectedIcon(recursive=True)
        )
        self.removeChild()
        self.assertEqual(
            "book_icon", self.compositeObject.selectedIcon(recursive=True)
        )

    def testCopy(self):
        self.compositeObject.expand(context="some_viewer")
        copy = self.compositeObject.copy()
        # pylint: disable=E1101
        self.assertEqual(
            copy.expandedContexts(), self.compositeObject.expandedContexts()
        )
        self.compositeObject.expand(context="another_viewer")
        self.assertFalse("another_viewer" in copy.expandedContexts())

    def testMarkDeleted(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent, eventType=base.CompositeObject.markDeletedEventType()
        )
        self.compositeObject.markDeleted()
        expectedEvent = patterns.Event(
            base.CompositeObject.markDeletedEventType(),
            self.compositeObject,
            base.CompositeObject.STATUS_DELETED,
        )
        expectedEvent.addSource(
            self.child, base.CompositeObject.STATUS_DELETED
        )
        self.assertEqual([expectedEvent], self.eventsReceived)

    def testMarkDirty(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType(),
        )
        self.compositeObject.markDeleted()
        self.compositeObject.markDirty(force=True)
        expectedEvent = patterns.Event(
            base.CompositeObject.markNotDeletedEventType(),
            self.compositeObject,
            base.CompositeObject.STATUS_CHANGED,
        )
        expectedEvent.addSource(
            self.child, base.CompositeObject.STATUS_CHANGED
        )
        self.assertEqual([expectedEvent], self.eventsReceived)

    def testMarkNew(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType(),
        )
        self.compositeObject.markDeleted()
        self.compositeObject.markNew()
        expectedEvent = patterns.Event(
            base.CompositeObject.markNotDeletedEventType(),
            self.compositeObject,
            base.CompositeObject.STATUS_NEW,
        )
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_NEW)
        self.assertEqual([expectedEvent], self.eventsReceived)

    def testCleanDirty(self):
        self.addChild()
        patterns.Publisher().registerObserver(
            self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType(),
        )
        self.compositeObject.markDeleted()
        self.compositeObject.cleanDirty()
        expectedEvent = patterns.Event(
            base.CompositeObject.markNotDeletedEventType(),
            self.compositeObject,
            base.CompositeObject.STATUS_NONE,
        )
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_NONE)
        self.assertEqual([expectedEvent], self.eventsReceived)

    def testModificationEventTypes(self):
        self.assertEqual(
            [
                self.compositeObject.addChildEventType(),
                self.compositeObject.removeChildEventType(),
                self.compositeObject.subjectChangedEventType(),
                self.compositeObject.descriptionChangedEventType(),
                self.compositeObject.appearanceChangedEventType(),
                self.compositeObject.orderingChangedEventType(),
                self.compositeObject.expansionChangedEventType(),
            ],
            self.compositeObject.modificationEventTypes(),
        )


class BaseCollectionTest(tctest.TestCase):
    def setUp(self):
        super().setUp()
        self.collection = base.Collection()

    def testLookupByIdWhenCollectionIsEmptyRaisesIndexError(self):
        self.assertRaises(IndexError, self.collection.getObjectById, "id")

    def testLookupIdWhenObjectIsInCollection(self):
        domainObject = base.CompositeObject()
        self.collection.append(domainObject)
        self.assertEqual(
            domainObject, self.collection.getObjectById(domainObject.id())
        )
