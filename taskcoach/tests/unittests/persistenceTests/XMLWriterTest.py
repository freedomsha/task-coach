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

Tests unitaires pour le module XMLWriter.

Ce fichier contient des tests pour valider que le module `XMLWriter` génère correctement
les fichiers XML en fonction des données de tâches, catégories, notes et efforts.

Les tests utilisent un objet `XMLWriter` et vérifient si les fragments XML générés
correspondent aux attentes.
"""

# from future import standard_library

# standard_library.install_aliases()
# from builtins import str
# from builtins import object
import wx
import io  # We cannot use CStringIO since unicode strings are used below.
from ... import tctest
from taskcoachlib import persistence, config, meta
from taskcoachlib.domain import (
    base,
    task,
    effort,
    date,
    category,
    note,
    attachment,
)
from taskcoachlib.syncml.config import SyncMLConfigNode
from taskcoachlib.gui.uicommand.uicommand import AddAttachment


class XMLWriterTest(tctest.TestCase):
    """
    Classe de tests pour valider le comportement de `persistence.XMLWriter`.

    Cette classe regroupe des tests pour vérifier que les objets du modèle,
    comme les tâches, catégories, notes et efforts, sont correctement sérialisés
    en XML par l'écrivain XML.

    Attributs :
        - `fd` : Flux mémoire pour capturer la sortie XML.
        - `writer` : Instance de `XMLWriter` utilisée pour les tests.
        - `task` : Exemple de tâche utilisée dans les tests.
        - `taskList` : Liste contenant les tâches pour les tests.
        - `category` : Exemple de catégorie utilisée dans les tests.
        - `categoryContainer` : Conteneur de catégories utilisé dans les tests.
        - `note` : Exemple de note utilisée dans les tests.
        - `noteContainer` : Conteneur de notes utilisé dans les tests.
        - `changes` : Dictionnaire pour suivre les modifications dans les objets.
    """

    # Méthodes principales
    def setUp(self):
        """
        Configure les objets nécessaires pour les tests.

        Initialise les objets XMLWriter, tâche, catégories et notes avant chaque
        test. Utilise `io.StringIO ou io.BytesIO` pour capturer la sortie XML dans un flux mémoire.
        """
        task.Task.settings = config.Settings(load=False)
        # Flux mémoire pour capturer la sortie XML :
        self.fd = (
            io.StringIO()
        )  # Cela crée un objet StringIO (Un flux de texte utilisant un tampon de texte en mémoire).
        # Use BytesIO for binary data
        # self.fd = io.BytesIO()
        self.fd.name = "testfile.tsk"  # Name attribute assignment might not be necessary for StringIO
        # Pour StringIO, encoding n'est plus réglable. utf-8 est automatique.
        # self.fd.encoding = "UTF-8"  # Remove or comment this out if it's present in your code
        # Instance de `XMLWriter` utilisée pour les tests :
        self.writer = persistence.XMLWriter(self.fd)
        # Exemple de tâche utilisée dans les tests :
        self.task = task.Task()
        # Liste contenant les tâches pour les tests :
        self.taskList = task.TaskList([self.task])
        # Exemple de catégorie utilisée dans les tests :
        self.category = category.Category("Category")
        # Conteneur de catégories utilisé dans les tests :
        self.categoryContainer = category.CategoryList([self.category])
        # Exemple de note utilisée dans les tests :
        self.note = note.Note()
        # Conteneur de notes utilisé dans les tests :
        # self.noteContainer = note.NoteContainer([self.note])
        # NoteContainer([self.note]) ne fonctionnait pas correctement
        # à cause de l'héritage de CategorizableContainer,
        # tandis que append() est la méthode standard et fiable.
        self.noteContainer = note.NoteContainer()
        self.noteContainer.append(
            self.note
        )  # ✅ Ajout explicite avec append()
        # self.task.addNote(self.note)  # ✅ Ajoutez la note à la tâche ici
        # Dictionnaire pour suivre les modifications dans les objets :
        self.changes = dict()

    def __writeAndRead(self) -> str:
        """
        Écrit les données dans un flux XML et retourne le contenu sérialisé.

        Returns :
            str : Contenu XML généré.
        """
        self.writer.write(
            self.taskList,
            self.categoryContainer,
            self.noteContainer,
            SyncMLConfigNode("root"),
            guid={self.task.id(): "GUID"},  # Ajout d'un GUID pour la tâche
            # guid=self.task.id() or "GUID",  # Ajout d'un GUID pour la tâche
        )  # TypeError: a bytes-like object is required, not 'str'
        # if isinstance(self.fd.getvalue(), bytes):
        #     return self.fd.getvalue().decode(self. fd.encoding)
        # Vérifie si self.fd a un attribut encoding avant de l'utiliser
        if isinstance(self.fd.getvalue(), bytes):
            encoding = getattr(self.fd, "encoding", "utf-8")
            return self.fd.getvalue().decode(encoding)
        elif isinstance(self.fd.getvalue(), str):
            return self.fd.getvalue()
        return None

    def expectInXML(self, xmlFragment):
        """
        Vérifie qu'un fragment de XML est présent dans la sortie générée.

        Args :
            xmlFragment (str) : Fragment de XML attendu.

        Assertions :
            AssertionError : Si le fragment attendu n'est pas trouvé dans la sortie XML.
        """
        xml = self.__writeAndRead()
        print(
            f"XMLWriterTest.expectInXML : vérifie si xmlFragment={xmlFragment} est dans XML output:\n{xml}\n"
        )
        self.assertTrue(
            xmlFragment in xml or xmlFragment in xml.replace("&apos;", "'"),
            "%s not in %s" % (str(xmlFragment), str(xml)),
        )

    def expectNotInXML(self, xmlFragment):
        """
        Vérifie qu'un fragment de XML est absent dans la sortie générée.

        Args :
            xmlFragment (str) : Fragment de XML qui ne doit pas être présent.

        Lève :
            AssertionError : Si le fragment est trouvé dans la sortie XML.
        """
        xml = self.__writeAndRead()
        self.assertFalse(xmlFragment in xml, "%s in %s" % (xmlFragment, xml))

    # tests

    # Exemples de tests unitaires
    def testVersion(self):
        """
        Vérifie que la version du logiciel est incluse dans le fichier XML.
        """
        # self.expectInXML('<?taskcoach release="%s"' % meta.data.version)
        self.expectInXML(f'<?taskcoach release="{meta.data.version}"')

    def testGUID(self):
        """
        Vérifie que l'identifiant global unique (GUID) est correctement sérialisé.
        """
        self.expectInXML("<guid>\nGUID\n</guid>")

    def testTaskSubject(self):
        """
        Vérifie que le sujet d'une tâche est correctement écrit dans le fichier XML.
        """
        self.task.setSubject("Subject")
        self.expectInXML('subject="Subject"')

    def testTaskMarkedDeleted(self):
        """
        Vérifie que la tâche est correctement marquée effacée dans le fichier XML..

        Returns :
            None
        """
        self.task.markDeleted()
        self.expectInXML('status="3"')

    def testTaskSubjectWithUnicode(self):
        self.task.setSubject("ï¬Ÿï­Žï­–")
        self.expectInXML('subject="ï¬Ÿï­Žï­–"')

    def testTaskDescription(self):
        """
        Vérifie que la description d'une tâche est incluse dans le fichier XML.
        """
        self.task.setDescription("Description")
        self.expectInXML("<description>\nDescription\n</description>\n")

    def testEmptyTaskDescriptionIsNotWritten(self):
        self.expectNotInXML("<description>")

    def testTaskPlannedStartDateTime(self):
        self.task.setPlannedStartDateTime(date.DateTime(2004, 1, 1, 11, 0, 0))
        # self.expectInXML(
        #     'plannedstartdate="%s"' % str(self.task.plannedStartDateTime())
        # )
        self.expectInXML(
            f'plannedstartdate="{self.task.plannedStartDateTime()}"'
        )

    def testNoPlannedStartDateTime(self):
        self.task.setPlannedStartDateTime(date.DateTime())
        self.expectNotInXML("plannedstartdate=")

    def testTaskActualStartDateTime(self):
        self.task.setActualStartDateTime(date.DateTime(2007, 12, 31, 9, 0, 0))
        self.expectInXML(
            'actualstartdate="%s"' % str(self.task.actualStartDateTime())
        )
        # self.expectInXML('actualstartdate="%s"' % self.task.actualStartDateTime())

    def testNoActualStartDateTime(self):
        self.task.setActualStartDateTime(date.DateTime())
        self.expectNotInXML("actualstartdate=")

    def testTaskDueDateTime(self):
        self.task.setDueDateTime(date.DateTime(2004, 1, 1, 10, 5, 5))
        self.expectInXML('duedate="%s"' % str(self.task.dueDateTime()))
        # self.expectInXML('duedate="%s"' % self.task.dueDateTime())

    def testNoDueDateTime(self):
        self.expectNotInXML("duedate=")

    def testTaskCompletionDateTime(self):
        self.task.setCompletionDateTime(date.DateTime(2004, 1, 1, 10, 8, 4))
        # self.expectInXML('completiondate="%s"' % str(self.task.completionDateTime()))
        self.expectInXML(f'completiondate="{self.task.completionDateTime()}"')

    def testNoCompletionDateTime(self):
        self.expectNotInXML("completiondate=")

    def testChildTask(self):
        self.task.addChild(task.Task(subject="child"))
        self.expectInXML('subject="child" />\n</task>\n<category')

    # Tests d'effort
    def testEffort(self):
        """
        Vérifie que les efforts associés à une tâche sont correctement sérialisés
        dans le fichier XML, y compris les heures de début et de fin.
        """
        taskEffort = effort.Effort(
            self.task,
            date.DateTime(2004, 1, 1),
            date.DateTime(2004, 1, 2),
            description="description\nline 2",
        )
        self.task.addEffort(taskEffort)
        self.expectInXML(
            # '<effort id="%s" start="%s" status="%d" stop="%s">\n'
            '<effort id="%s" status="%d" start="%s" stop="%s">\n'
            "<description>\ndescription\nline 2\n</description>\n"
            "</effort>"
            % (
                taskEffort.id(),
                base.SynchronizedObject.STATUS_NEW,
                taskEffort.getStart(),
                taskEffort.getStop(),
            )
        )

    def testThatEffortTimesDoNotContainMilliseconds(self):
        """
        Vérifie que les heures de début et de fin des efforts ne contiennent pas
        de millisecondes dans le fichier XML.
        """
        self.task.addEffort(
            effort.Effort(
                self.task,
                date.DateTime(2004, 1, 1, 10, 0, 0, 123456),
                date.DateTime(2004, 1, 1, 10, 0, 10, 654310),
            )
        )
        self.expectInXML('start="2004-01-01 10:00:00"')
        self.expectInXML('stop="2004-01-01 10:00:10"')

    def testThatEffortStartAndStopAreNotEqual(self):
        self.task.addEffort(
            effort.Effort(
                self.task,
                date.DateTime(2004, 1, 1, 10, 0, 0, 123456),
                date.DateTime(2004, 1, 1, 10, 0, 0, 654310),
            )
        )
        self.expectInXML('start="2004-01-01 10:00:00"')
        self.expectInXML('stop="2004-01-01 10:00:01"')

    def testEmptyEffortDescriptionIsNotWritten(self):
        self.task.addEffort(
            effort.Effort(
                self.task, date.DateTime(2004, 1, 1), date.DateTime(2004, 1, 2)
            )
        )
        self.expectNotInXML("<description>")

    def testActiveEffort(self):
        self.task.addEffort(
            effort.Effort(self.task, date.DateTime(2004, 1, 1))
        )
        self.expectInXML(
            '<effort id="%s" status="%d" start="%s" />'
            % (
                str(self.task.efforts()[0].id()),
                base.SynchronizedObject.STATUS_NEW,
                str(self.task.efforts()[0].getStart()),
            )
        )

    def testNoEffortByDefault(self):
        self.expectNotInXML("<efforts>")

    def testBudget(self):
        self.task.setBudget(date.ONE_HOUR)
        # self.expectInXML('budget="%s"' % str(self.task.budget()))
        self.expectInXML(f'budget="{self.task.budget()}"')

    def testNoBudget(self):
        self.expectNotInXML("budget")

    def testBudget_MoreThan24Hour(self):
        self.task.setBudget(date.TimeDelta(hours=25))
        self.expectInXML('budget="25:00:00"')

    def testOneCategoryWithoutTask(self):
        aCategory = category.Category("test", id="id")
        self.categoryContainer.append(aCategory)
        self.expectInXML(
            '<category id="id" status="1" creationDateTime="%s" '
            'subject="test" />' % aCategory.creationDateTime()
        )

    def testOneCategoryWithOneTask(self):
        self.categoryContainer.append(category.Category("test", [self.task]))
        self.expectInXML('categorizables="%s"' % self.task.id())

    def testTwoCategoriesWithOneTask(self):
        subjects = ["test", "another"]
        expectedResults = []
        for subject in subjects:
            cat = category.Category(subject, [self.task])
            self.categoryContainer.append(cat)
            expectedResults.append(
                "<category "
                'id="%s" status="1" creationDateTime="%s" '
                'subject="%s" categorizables="%s" />'
                % (cat.id(), cat.creationDateTime(), subject, self.task.id())
            )
        for expectedResult in expectedResults:
            self.expectInXML(expectedResult)

    def testOneCategoryWithSubTask(self):
        child = task.Task()
        self.taskList.append(child)
        self.task.addChild(child)
        self.categoryContainer.append(category.Category("test", [child]))
        self.expectInXML('categorizables="%s"' % child.id())

    def testSubCategoryWithoutTasks(self):
        parent = category.Category(subject="parent")
        child = category.Category(subject="child")
        parent.addChild(child)
        self.categoryContainer.extend([parent, child])
        self.expectInXML(
            '<category id="%s" status="1" '
            'creationDateTime="%s" subject="parent">\n'
            '<category id="%s" status="1" creationDateTime="%s" '
            'subject="child" />\n</category>'
            % (
                parent.id(),
                parent.creationDateTime(),
                child.id(),
                child.creationDateTime(),
            )
        )

    def testSubCategoryWithOneTask(self):
        parent = category.Category(subject="parent")
        child = category.Category(subject="child", categorizables=[self.task])
        parent.addChild(child)
        self.categoryContainer.extend([parent, child])
        self.expectInXML(
            '<category id="%s" status="1" '
            'creationDateTime="%s" subject="parent">\n'
            '<category id="%s" status="1" '
            'creationDateTime="%s" subject="child" categorizables="%s" />\n'
            "</category>"
            % (
                parent.id(),
                parent.creationDateTime(),
                child.id(),
                child.creationDateTime(),
                self.task.id(),
            )
        )

    def testFilteredCategory(self):
        self.categoryContainer.extend(
            [category.Category(subject="test", filtered=True)]
        )
        self.expectInXML('filtered="True"')

    def testCategoryWithDescription(self):
        aCategory = category.Category(
            subject="subject", description="Description", id="id"
        )
        self.categoryContainer.append(aCategory)
        # self.expectInXML(
        #     '<category creationDateTime="%s" id="id" status="1" subject="subject">\n'
        #     "<description>\nDescription\n</description>\n"
        #     "</category>" % str(aCategory.creationDateTime())
        # )
        self.expectInXML(
            '<category id="id" status="1" creationDateTime="%s" subject="subject">\n'
            "<description>\nDescription\n</description>\n"
            "</category>" % aCategory.creationDateTime()
        )

    def testCategoryWithUnicodeSubject(self):
        unicodeCategory = category.Category(subject="ï¬Ÿï­Žï­–", id="id")
        self.categoryContainer.extend([unicodeCategory])
        self.expectInXML('subject="ï¬Ÿï­Žï­–"')

    def testCategoryWithDeletedTask(self):
        aCategory = category.Category(
            subject="category", categorizables=[self.task], id="id"
        )
        self.categoryContainer.append(aCategory)
        self.taskList.remove(self.task)
        # self.expectInXML(
        #     '<category creationDateTime="%s" id="id" status="1" '
        #     'subject="category" />' % str(aCategory.creationDateTime())
        # )
        self.expectInXML(
            '<category id="id" status="1" creationDateTime="%s" '
            'subject="category" />' % aCategory.creationDateTime()
        )

    def testDefaultPriority(self):
        self.expectNotInXML("priority")

    def testPriority(self):
        self.task.setPriority(5)
        self.expectInXML('priority="5"')

    def testTaskId(self):
        # self.expectInXML('id="%s"' % self.task.id())
        self.expectInXML(f'id="{self.task.id()}"')

    def testCategoryId(self):
        aCategory = category.Category(subject="category")
        self.categoryContainer.append(aCategory)
        self.expectInXML('id="%s"' % aCategory.id())

    def testNoteId(self):
        self.expectInXML('id="%s"' % self.note.id())

    def testTwoTasks(self):
        self.task.setSubject("task 1")
        task2 = task.Task(subject="task 2")
        self.taskList.append(task2)
        self.expectInXML('subject="task 2"')

    def testDefaultHourlyFee(self):
        self.expectNotInXML("hourlyFee")

    def testHourlyFee(self):
        self.task.setHourlyFee(100)
        self.expectInXML('hourlyFee="100"')

    def testDefaultFixedFee(self):
        self.expectNotInXML("fixedFee")

    def testFixedFee(self):
        self.task.setFixedFee(1000)
        self.expectInXML('fixedFee="1000"')

    def testNoReminder(self):
        self.expectNotInXML("reminder")

    # Gestion des rappels
    def testReminder(self):
        """
        Vérifie que la date et l'heure de rappel d'une tâche sont correctement
        écrites dans le fichier XML.
        """
        self.task.setReminder(date.DateTime(2005, 5, 7, 13, 15, 10))
        # self.expectInXML('reminder="%s"' % str(self.task.reminder()))
        self.expectInXML('reminder="%s"' % self.task.reminder())
        self.expectNotInXML("reminderBeforeSnooze")

    def testSnoozedReminder(self):
        """
        Vérifie que les rappels différés (snooze) sont correctement sérialisés.
        """
        now = date.Now()
        self.task.setReminder(now + date.TimeDelta(seconds=30))
        self.task.snoozeReminder(date.TimeDelta(seconds=120), now=lambda: now)
        # self.expectInXML('reminder="%s"' % str(self.task.reminder()))
        self.expectInXML('reminder="%s"' % self.task.reminder())
        # self.expectInXML(
        #     'reminderBeforeSnooze="%s"' % str(self.task.reminder(includeSnooze=False))
        # )
        self.expectInXML(
            'reminderBeforeSnooze="%s"'
            % self.task.reminder(includeSnooze=False)
        )

    def testReminderIsNoneButSnoozedReminderNot(self):
        now = date.Now()
        self.task.setReminder(now + date.TimeDelta(seconds=30))
        self.task.snoozeReminder(date.TimeDelta())
        self.expectNotInXML("reminder")

    def testMarkCompletedWhenAllChildrenAreCompletedSetting_None(self):
        self.expectNotInXML("shouldMarkCompletedWhenAllChildrenCompleted")

    def testMarkCompletedWhenAllChildrenAreCompletedSetting_True(self):
        self.task.setShouldMarkCompletedWhenAllChildrenCompleted(True)
        self.expectInXML('shouldMarkCompletedWhenAllChildrenCompleted="True"')

    def testMarkCompletedWhenAllChildrenAreCompletedSetting_False(self):
        self.task.setShouldMarkCompletedWhenAllChildrenCompleted(False)
        self.expectInXML('shouldMarkCompletedWhenAllChildrenCompleted="False"')

    def testNote(self):
        aNote = note.Note(id="id")
        self.noteContainer.append(aNote)
        self.expectInXML(
            '<note id="id" status="%d" creationDateTime="%s" '
            "/>"
            % (base.SynchronizedObject.STATUS_NEW, aNote.creationDateTime())
        )

    def testNoteWithSubject(self):
        self.noteContainer.append(note.Note(subject="Note"))
        self.expectInXML('subject="Note"')

    def testNoteWithDescription(self):
        self.noteContainer.append(note.Note(description="Description"))
        self.expectInXML("<description>\nDescription\n</description>\n")

    def testNoteWithChild(self):
        child = note.Note(id="child")
        self.note.addChild(child)
        self.noteContainer.append(child)
        self.expectInXML(
            '<note id="%s" status="%d" creationDateTime="%s">\n'
            '<note id="child" status="%d" creationDateTime="%s" />\n'
            "</note>"
            % (
                self.note.id(),
                base.SynchronizedObject.STATUS_NEW,
                self.note.creationDateTime(),
                base.SynchronizedObject.STATUS_NEW,
                child.creationDateTime(),
            )
        )

    def testNoteWithCategory(self):
        cat = category.Category(subject="cat")
        self.categoryContainer.append(cat)
        self.note.addCategory(cat)
        cat.addCategorizable(self.note)
        self.expectInXML('categorizables="%s"' % self.note.id())

    # Tests de gestion des couleurs
    def testCategoryForegroundColor(self):
        """
        Vérifie que la couleur de premier plan (foreground color) d'une catégorie est
        correctement incluse dans le fichier XML.
        """
        self.categoryContainer.append(
            category.Category(subject="test", fgColor=wx.RED)
        )
        self.expectInXML('fgColor="(255, 0, 0, 255)"')

    def testCategoryBackgroundColor(self):
        """
        Vérifie que la couleur d'arrière-plan (background color) d'une catégorie est
        correctement incluse dans le fichier XML.
        """
        self.categoryContainer.append(
            category.Category(subject="test", bgColor=wx.RED)
        )
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedCategoryForegroundColor(self):
        parent = category.Category(subject="test", fgColor=wx.RED)
        child = category.Category(subject="child", id="id")
        parent.addChild(child)
        self.categoryContainer.append(parent)
        self.expectInXML(
            '<category id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testDontWriteInheritedCategoryBackgroundColor(self):
        parent = category.Category(subject="test", bgColor=wx.RED)
        child = category.Category(subject="child", id="id")
        parent.addChild(child)
        self.categoryContainer.append(parent)
        self.expectInXML(
            '<category id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testTaskForegroundColor(self):
        self.task.setForegroundColor(wx.RED)
        self.expectInXML('fgColor="(255, 0, 0, 255)"')

    def testTaskBackgroundColor(self):
        self.task.setBackgroundColor(wx.RED)
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedTaskForegroundColor(self):
        self.task.setForegroundColor(wx.RED)
        child = task.Task(
            subject="child", id="id", plannedStartDateTime=date.DateTime()
        )
        self.task.addChild(child)
        self.taskList.append(child)
        self.expectInXML(
            '<task id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testDontWriteInheritedTaskBackgroundColor(self):
        self.task.setBackgroundColor(wx.RED)
        child = task.Task(
            subject="child", id="id", plannedStartDateTime=date.DateTime()
        )
        self.task.addChild(child)
        self.taskList.append(child)
        self.expectInXML(
            '<task id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testNoteForegroundColor(self):
        self.note.setForegroundColor(wx.RED)
        self.expectInXML('fgColor="(255, 0, 0, 255)"')

    def testNoteBackgroundColor(self):
        self.note.setBackgroundColor(wx.RED)
        # self.task.addNote(self.note)  # ✅ Ajoutez la note à la tâche ici
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedNoteForegroundColor(self):
        parent = note.Note(fgColor=wx.RED)
        child = note.Note(subject="child", id="id")
        parent.addChild(child)
        self.noteContainer.append(parent)
        self.expectInXML(
            '<note id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testDontWriteInheritedNoteBackgroundColor(self):
        parent = note.Note(bgColor=wx.RED)
        child = note.Note(subject="child", id="id")
        parent.addChild(child)
        self.noteContainer.append(parent)
        self.expectInXML(
            '<note id="id" status="1" creationDateTime="%s" '
            'subject="child" />' % child.creationDateTime()
        )

    def testNoRecurencce(self):
        self.expectNotInXML("recurrence")

    def testDailyRecurrence(self):
        self.task.setRecurrence(date.Recurrence("daily"))
        self.expectInXML('<recurrence unit="daily" />')

    def testWeeklyRecurrence(self):
        self.task.setRecurrence(date.Recurrence("weekly"))
        self.expectInXML('<recurrence unit="weekly" />')

    def testMonthlyRecurrence(self):
        self.task.setRecurrence(date.Recurrence("monthly"))
        self.expectInXML('<recurrence unit="monthly" />')

    def testMonthlyRecurrenceOnSameWeekday(self):
        self.task.setRecurrence(date.Recurrence("monthly", sameWeekday=True))
        self.expectInXML('<recurrence unit="monthly" sameWeekday="True" />')

    def testYearlyRecurrence(self):
        self.task.setRecurrence(date.Recurrence("yearly"))
        self.expectInXML('<recurrence unit="yearly" />')

    def testRecurrenceCount(self):
        self.task.setRecurrence(date.Recurrence("daily", count=5))
        self.expectInXML('count="5"')

    def testMaxRecurrenceCount(self):
        self.task.setRecurrence(date.Recurrence("daily", maximum=5))
        self.expectInXML('max="5"')

    def testRecurrenceStopDateTime(self):
        stop_datetime = date.DateTime(2000, 1, 1, 10, 9, 8)
        self.task.setRecurrence(
            date.Recurrence("daily", stop_datetime=stop_datetime)
        )
        # self.expectInXML('stop_datetime="%s"' % str(stop_datetime))
        self.expectInXML('stop_datetime="%s"' % stop_datetime)

    def testRecurrenceFrequency(self):
        self.task.setRecurrence(date.Recurrence("daily", amount=2))
        self.expectInXML('amount="2"')

    def testRecurrenceBasedOnCompletion(self):
        self.task.setRecurrence(
            date.Recurrence("daily", recurBasedOnCompletion=True)
        )
        self.expectInXML('recurBasedOnCompletion="True"')

    def testNoAttachments(self):
        self.expectNotInXML("attachment")

    # addAttachment, addNote, etc., are dynamically generated so pylint can't
    # find them. Disable the error message.
    # pylint: disable=E1101

    def testTaskWithOneAttachment(self):
        task_attachment = attachment.FileAttachment("whatever.txt", id="foo")
        self.task.addAttachments(task_attachment)
        self.expectInXML(
            '<attachment id="foo" status="1" '
            'creationDateTime="%s" subject="whatever.txt" '
            'type="file" location="whatever.txt" '
            "/>" % task_attachment.creationDateTime()
        )

    def testObjectWithAttachmentWithNote(self):
        att = attachment.FileAttachment("whatever.txt", id="foo")
        self.task.addAttachments(att)
        attachment_note = note.Note(subject="attnote", id="spam")
        att.addNote(attachment_note)
        self.expectInXML(
            '<attachment id="foo" status="1" '
            'creationDateTime="%s" subject="whatever.txt" '
            'type="file" location="whatever.txt">\n'
            "<note" % att.creationDateTime()
        )

    def testNoteWithOneAttachment(self):
        note_attachment = attachment.FileAttachment("whatever.txt", id="foo")
        self.note.addAttachments(note_attachment)
        self.expectInXML(
            '<attachment id="foo" status="1" '
            'creationDateTime="%s" subject="whatever.txt" '
            'type="file" location="whatever.txt" '
            "/>" % note_attachment.creationDateTime()
        )

    def testCategoryWithOneAttachment(self):
        cat = category.Category("cat")
        self.categoryContainer.append(cat)
        category_attachment = attachment.FileAttachment(
            "whatever.txt", id="foo"
        )
        cat.addAttachments(category_attachment)
        self.expectInXML(
            '<attachment id="foo" status="1" '
            'creationDateTime="%s" subject="whatever.txt" '
            'type="file" location="whatever.txt" '
            "/>" % category_attachment.creationDateTime()
        )

    def testTaskWithTwoAttachments(self):
        attachments = [
            attachment.FileAttachment("whatever.txt"),
            attachment.FileAttachment("/home/frank/attachment.doc"),
        ]
        for a in attachments:
            self.task.addAttachments(a)
        for att in attachments:
            self.expectInXML(
                '<attachment id="%s" status="1" creationDateTime="%s" '
                'subject="%s" type="file" location="%s" '
                "/>"
                % (
                    att.id(),
                    att.creationDateTime(),
                    att.location(),
                    att.location(),
                )
            )

    def testTaskWithNote(self):
        self.task.addNote(self.note)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s" '
            "/>\n</task>" % (self.note.id(), self.note.creationDateTime())
        )

    def testTaskWithNotes(self):
        """Tester l'ajout de plusieurs notes à une tâche."""
        anotherNote = note.Note(subject="Another note", id="id")
        self.task.addNote(self.note)
        self.task.addNote(anotherNote)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s" />\n'
            '<note id="id" status="1" creationDateTime="%s" subject="Another note" '
            "/>\n</task>"
            % (
                self.note.id(),
                self.note.creationDateTime(),
                anotherNote.creationDateTime(),
            )
        )

    def testTaskWithNestedNotes(self):
        """Tester"""
        subNote = note.Note(subject="Subnote", id="id")
        self.note.addChild(subNote)
        self.task.addNote(self.note)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s">\n'
            '<note id="id" status="1" creationDateTime="%s" subject="Subnote" '
            "/>\n</note>\n</task>"
            % (
                self.note.id(),
                self.note.creationDateTime(),
                subNote.creationDateTime(),
            )
        )

    def testTaskWithNoteWithCategory(self):
        newNote = note.Note()
        self.task.addNote(newNote)
        newNote.addCategory(self.category)
        self.category.addCategorizable(newNote)
        self.expectInXML('categorizables="%s"' % newNote.id())

    def testTaskWithNoteWithSubNoteWithCategory(self):
        newNote = note.Note()
        newSubNote = note.Note()
        newNote.addChild(newSubNote)
        self.task.addNote(newNote)
        newSubNote.addCategory(self.category)
        self.category.addCategorizable(newSubNote)
        self.expectInXML('categorizables="%s"' % newSubNote.id())

    def testCategoryWithNote(self):
        self.category.addNote(self.note)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s" '
            "/>\n</category>" % (self.note.id(), self.note.creationDateTime())
        )

    def testCategoryWithNotes(self):
        anotherNote = note.Note(subject="Another note", id="id")
        self.category.addNote(self.note)
        self.category.addNote(anotherNote)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s" />\n'
            '<note id="id" status="1" creationDateTime="%s" subject="Another '
            'note" />\n</category>'
            % (
                self.note.id(),
                self.note.creationDateTime(),
                anotherNote.creationDateTime(),
            )
        )

    def testCategoryWithNestedNotes(self):
        subNote = note.Note(subject="Subnote", id="id")
        self.note.addChild(subNote)
        self.category.addNote(self.note)
        self.expectInXML(
            '>\n<note id="%s" status="1" creationDateTime="%s">\n'
            '<note id="id" status="1" creationDateTime="%s" subject="Subnote" '
            "/>\n</note>\n</category>"
            % (
                self.note.id(),
                self.note.creationDateTime(),
                subNote.creationDateTime(),
            )
        )

    def testTaskDefaultExpansionState(self):
        # Don't write anything if the task is not expanded:
        self.expectNotInXML("expandedContexts")

    def testTaskExpansionState(self):
        self.task.expand()
        self.expectInXML('''expandedContexts="('None',)"''')

    def testTaskExpansionState_SpecificContext(self):
        self.task.expand(context="Test")
        self.expectInXML('''expandedContexts="('Test',)"''')

    def testTaskExpansionState_MultipleContexts(self):
        self.task.expand(context="Test")
        self.task.expand(context="Another context")
        self.expectInXML('''expandedContexts="('Another context', 'Test')"''')

    def testCategoryExpansionState(self):
        cat = category.Category("cat")
        self.categoryContainer.append(cat)
        cat.expand()
        self.expectInXML('''expandedContexts="('None',)"''')

    def testNoteExpansionState(self):
        self.note.expand()
        self.expectInXML('''expandedContexts="('None',)"''')

    def testPercentageComplete(self):
        self.task.setPercentageComplete(50)
        self.expectInXML('''percentageComplete="50"''')

    def testPercentageComplete_Float(self):
        self.task.setPercentageComplete(50.0)
        self.expectInXML('''percentageComplete="50.0"''')

    def testExclusiveSubcategories(self):
        self.category.makeSubcategoriesExclusive()
        self.expectInXML('''exclusiveSubcategories="True"''')

    def testNonExclusiveSubcategoriesByDefault(self):
        self.expectNotInXML("""exclusiveSubcategories""")

    def testTaskFont(self):
        self.task.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"' % wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testNoTaskFontByDefault(self):
        self.expectNotInXML("font")

    def testNoteFont(self):
        self.note.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"' % wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testCategoryFont(self):
        self.category.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"' % wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testAttachmentFont(self):
        att = attachment.FileAttachment(
            "whatever.txt", id="foo", font=wx.SWISS_FONT
        )
        self.task.addAttachments(att)
        self.expectInXML('font="%s"' % wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testNonAsciiFontName(self):
        class FakeFont(object):
            def GetNativeFontInfoDesc(self):
                return "微软雅黑"

        font = FakeFont()
        self.task.setFont(font)
        self.expectInXML('font="微软雅黑"')

    def testTaskIcon(self):
        self.task.setIcon("icon")
        self.expectInXML('icon="icon"')

    def testNoTaskIcon(self):
        self.expectNotInXML("icon")

    def testSelectedTaskIcon(self):
        self.task.setSelectedIcon("icon")
        self.expectInXML('selectedIcon="icon"')

    def testNoSelectedTaskIcon(self):
        self.expectNotInXML("selectedIcon")

    def testNoteIcon(self):
        self.note.setIcon("icon")
        self.expectInXML('icon="icon"')

    def testSelectedNoteIcon(self):
        self.note.setSelectedIcon("icon")
        self.expectInXML('selectedIcon="icon"')

    def testCategoryIcon(self):
        self.category.setIcon("icon")
        self.expectInXML('icon="icon"')

    def testSelectedCategoryIcon(self):
        self.category.setSelectedIcon("icon")
        self.expectInXML('selectedIcon="icon"')

    def testAttachmentIcon(self):
        att = attachment.FileAttachment("whatever.txt", id="foo", icon="icon")
        self.task.addAttachments(att)
        self.expectInXML('icon="icon"')

    def testSelectedAttachmentIcon(self):
        att = attachment.FileAttachment("whatever.txt", selectedIcon="icon")
        self.task.addAttachments(att)
        self.expectInXML('selectedIcon="icon"')

    def testPrerequisite(self):
        prerequisite = task.Task(subject="prereq")
        self.taskList.append(prerequisite)
        self.task.addPrerequisites([prerequisite])
        self.expectInXML('prerequisites="%s"' % prerequisite.id())

    def testMultiplePrerequisites(self):
        """Vérifie que plusieurs tâches préalables (prerequisites) sont correctement sérialisées
        dans le fichier XML, même si elles ont le même identifiant."""
        # Use the same id's for both prerequisites because we don't know in
        # what order they will end up in the XML.
        # prerequisites = [
        #     task.Task(subject="prereq1", id="id"),
        #     task.Task(subject="prereq2", id="id"),
        # ]
        # self.taskList.extend(prerequisites)
        # self.task.addPrerequisites(prerequisites)
        # self.expectInXML('prerequisites="id id"')
        # Problème : lxml ne supporte pas les ids identiques !
        prerequisites = [
            task.Task(subject="prereq1", id="id1"),
            task.Task(subject="prereq2", id="id2"),
        ]
        self.taskList.extend(prerequisites)
        self.task.addPrerequisites(prerequisites)
        self.expectInXML('prerequisites="id1 id2"')

    def testEncodingAttribute(self):
        # self.expectInXML("encoding='utf-8'")
        self.expectInXML('encoding="utf-8"')

    def testCreationDateTime(self):
        # self.expectInXML('creationDateTime="%s"' % str(self.task.creationDateTime()))
        self.expectInXML(
            'creationDateTime="%s"' % self.task.creationDateTime()
        )

    def testDoNotWriteUnknownCreationDateTime(self):
        task_with_unknown_creation_datetime = task.Task(
            creationDateTime=date.DateTime.min
        )
        self.taskList.append(task_with_unknown_creation_datetime)
        self.expectNotInXML('creationDateTime="0001-01-01 00:00:00"')

    def testModificationDateTime(self):
        self.task.setModificationDateTime(date.DateTime(2013, 1, 1, 0, 0, 0))
        self.expectInXML('modificationDateTime="2013-01-01 00:00:00"')

    def testDoNotWriteUnknownModificationDateTime(self):
        task_with_unknown_modification_datetime = task.Task(
            modificationDateTime=date.DateTime.min
        )
        self.expectNotInXML('modificationDateTime="0001-01-01 00:00:00"')
