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

# Ce qu'il faut surveiller dans les Tests
#
# La plupart de tes échecs de tests (AssertionError: False is not true)
# proviendront de ces trois cas :
#
#     Le Reset des modifications :
#     Beaucoup de tests appellent self.taskFile.monitor().resetAllChanges().
#     Avec ton nouveau système,
#     assure-toi que cette méthode vide bien ton self.__changes local
#     et que tu remets les compteurs à zéro dans le bon moniteur.
#
#     L'instanciation des objets :
#     Dans les tests, si tu crées un Effort ou une Note manuellement,
#     assure-toi qu'ils sont bien rattachés au domaine surveillé
#     par le TaskFile du test, sinon le message PubSub sera envoyé
#     mais le TaskFile ne saura pas à quel objet l'appliquer.
#
#     Le nettoyage (tearDown) :
#     C'est ici que tu avais tes KeyError.
#     Maintenant que close() nettoie le dictionnaire local,
#     vérifie que tes tests ne réutilisent pas un objet taskFile déjà fermé.

# from builtins import str
# from builtins import object
import os
import io
import wx
from ... import tctest
from taskcoachlib import persistence, config
from taskcoachlib.domain import (
    base,
    task,
    effort,
    date,
    category,
    note,
    attachment,
)


class FakeAttachment(base.Object):
    """Classe d'attachement factice pour les tests de changement d'attachement."""

    def __init__(self, type_, location, notes=None, data=None):
        """Initialise un attachement factice."""
        super().__init__()
        self.type_ = type_
        self.__location = location
        self.__data = data
        self.__notes = notes or []

    def data(self):
        """Retourne les données de l'attachement."""
        return self.__data

    def location(self):
        """Retourne la localisation de l'attachement."""
        return self.__location

    def notes(self):
        """Retourne les notes associées à l'attachement."""
        return self.__notes


class TaskFileTestCase(tctest.TestCase):
    """TestCase de base pour les tests de TaskFile."""

    def setUp(self):
        """Initialise les objets de test."""
        # Objet de test pour les changements d'attachement
        self.settings = task.Task.settings = config.Settings(load=False)
        # Crée les TaskFiles pour les tests
        self.createTaskFiles()
        self.task = task.Task(subject="task")
        self.taskFile.tasks().append(self.task)
        self.category = category.Category("category")
        self.taskFile.categories().append(self.category)
        self.note = note.Note(subject="note")
        self.taskFile.notes().append(self.note)
        self.effort = effort.Effort(
            self.task, date.DateTime(2004, 1, 1), date.DateTime(2004, 1, 2)
        )
        self.task.addEffort(self.effort)
        self.filename = "test.tsk"
        self.filename2 = "test2.tsk"
        super().setUp()

    def createTaskFiles(self):
        """Crée les TaskFiles pour les tests."""
        # pylint: disable=W0201
        self.taskFile = persistence.TaskFile()
        self.emptyTaskFile = persistence.TaskFile()

    def tearDown(self):
        """Nettoie les objets de test."""
        super().tearDown()
        self.taskFile.close()
        self.taskFile.stop()
        self.emptyTaskFile.close()
        self.emptyTaskFile.stop()
        self.remove(
            self.filename,
            self.filename2,
            self.filename + ".delta",
            self.filename2 + ".delta",
        )

    def remove(self, *filenames):
        """Supprime les fichiers de test."""
        for filename in filenames:
            tries = 0
            while os.path.exists(filename) and tries < 3:
                try:  # Don't fail on random 'Access denied' errors.
                    os.remove(filename)
                    break
                except WindowsError:  # pragma: no cover pylint: disable=E0602
                    tries += 1


class TaskFileTest(TaskFileTestCase):
    """Tests de base pour TaskFile."""

    def testIsEmptyInitially(self):
        """Vérifie que le TaskFile est vide initialement."""
        self.assertTrue(self.emptyTaskFile.isEmpty())

    def testHasNoTasksInitially(self):
        """Vérifie que le TaskFile n'a pas de tâches initialement."""
        self.assertFalse(self.emptyTaskFile.tasks())

    def testHasNoCategoriesInitially(self):
        """Vérifie que le TaskFile n'a pas de catégories initialement."""
        self.assertFalse(self.emptyTaskFile.categories())

    def testHasNoNotesInitially(self):
        """Vérifie que le TaskFile n'a pas de notes initialement."""
        self.assertFalse(self.emptyTaskFile.notes())

    def testHasNoEffortsInitially(self):
        """Vérifie que le TaskFile n'a pas d'efforts initialement."""
        self.assertFalse(self.emptyTaskFile.efforts())

    def testFileNameAfterCreate(self):
        """Vérifie que le nom de fichier est vide après la création du TaskFile."""
        self.assertEqual("", self.taskFile.filename())

    def testFileName(self):
        """Vérifie que le nom de fichier est correct après l'avoir défini."""
        self.taskFile.setFilename(self.filename)
        self.assertEqual(self.filename, self.taskFile.filename())

    def testLoadWithoutFilename(self):
        """Vérifie que le chargement sans nom de fichier ne fait rien."""
        self.taskFile.load()
        self.assertTrue(self.taskFile.isEmpty())

    def testLoadFromNotExistingFile(self):
        """Vérifie que le chargement à partir d'un fichier non existant ne fait rien."""
        self.taskFile.setFilename(self.filename)
        self.assertFalse(os.path.isfile(self.taskFile.filename()))
        self.taskFile.load()
        self.assertTrue(self.taskFile.isEmpty())

    def testClose_EmptyTaskFileWithoutFilename(self):
        """Vérifie que la fermeture d'un TaskFile vide sans nom de fichier réinitialise correctement le TaskFile."""
        self.taskFile.close()
        self.assertEqual("", self.taskFile.filename())
        self.assertTrue(self.taskFile.isEmpty())

    def testClose_EmptyTaskFileWithFilename(self):
        """
        Vérifie que la fermeture d'un TaskFile vide avec un nom de fichier
        réinitialise correctement le TaskFile.
        """
        self.taskFile.setFilename(self.filename)
        self.taskFile.close()
        self.assertEqual("", self.taskFile.filename())
        self.assertTrue(self.taskFile.isEmpty())

    def testClose_TaskFileWithTasksDeletesTasks(self):
        """
        Vérifie que la fermeture d'un TaskFile avec des tâches
        supprime les tâches et réinitialise le TaskFile.
        """
        self.taskFile.close()
        self.assertTrue(self.taskFile.isEmpty())

    def testClose_TaskFileWithCategoriesDeletesCategories(self):
        """
        Vérifie que la fermeture d'un TaskFile avec des catégories
        supprime les catégories et réinitialise le TaskFile.
        """
        self.taskFile.categories().append(self.category)
        self.taskFile.close()
        self.assertTrue(self.taskFile.isEmpty())

    def testClose_TaskFileWithNotesDeletesNotes(self):
        """
        Vérifie que la fermeture d'un TaskFile avec des notes
        supprime les notes et réinitialise le TaskFile.
        """
        self.taskFile.notes().append(note.Note())
        self.taskFile.close()
        self.assertTrue(self.taskFile.isEmpty())

    def testDoesNotNeedSave_Initial(self):
        """Vérifie que le TaskFile n'a pas besoin d'être sauvegardé initialement."""
        self.assertFalse(self.emptyTaskFile.needSave())

    def testDoesNotNeedSave_AfterSetFileName(self):
        """
        Vérifie que le TaskFile n'a pas besoin d'être sauvegardé
        après avoir défini un nom de fichier.
        """
        self.emptyTaskFile.setFilename(self.filename)
        self.assertFalse(self.emptyTaskFile.needSave())

    def testLastFilename_IsEmptyInitially(self):
        """Vérifie que le dernier nom de fichier est vide initialement."""
        self.assertEqual("", self.taskFile.lastFilename())

    def testLastFilename_EqualsCurrentFilenameAfterSetFilename(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier actuel après l'avoir défini."""
        self.taskFile.setFilename(self.filename)
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_EqualsPreviousFilenameAfterClose(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier précédent après la fermeture du TaskFile."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.close()
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_IsEmptyAfterClosingTwice(self):
        """Vérifie que le dernier nom de fichier est vide après avoir fermé le TaskFile deux fois."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.close()
        self.taskFile.close()
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_EqualsCurrentFilenameAfterSaveAs(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier actuel après avoir enregistré sous un nouveau nom."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.saveas(self.filename2)
        self.assertEqual(self.filename2, self.taskFile.lastFilename())

    def testTaskFileContainsTask(self):
        """Vérifie que le TaskFile contient une tâche après l'avoir ajoutée."""
        self.assertTrue(self.task in self.taskFile)

    def testTaskFileDoesNotContainTask(self):
        """Vérifie que le TaskFile ne contient pas une tâche qui n'a pas été ajoutée."""
        self.assertFalse(task.Task() in self.taskFile)

    def testTaskFileContainsNote(self):
        """Vérifie que le TaskFile contient une note après l'avoir ajoutée."""
        newNote = note.Note()
        self.taskFile.notes().append(newNote)
        self.assertTrue(newNote in self.taskFile)

    def testTaskFileDoesNotContainNote(self):
        """Vérifie que le TaskFile ne contient pas une note qui n'a pas été ajoutée."""
        self.assertFalse(note.Note() in self.taskFile)

    def testTaskFileContainsCategory(self):
        """Vérifie que le TaskFile contient une catégorie après l'avoir ajoutée."""
        newCategory = category.Category("Category")
        self.taskFile.categories().append(newCategory)
        self.assertTrue(newCategory in self.taskFile)

    def testTaskFileDoesNotContainCategory(self):
        """Vérifie que le TaskFile ne contient pas une catégorie qui n'a pas été ajoutée."""
        self.assertFalse(category.Category("Category") in self.taskFile)

    def testTaskFileContainsEffort(self):
        """Vérifie que le TaskFile contient un effort après l'avoir ajouté."""
        newEffort = effort.Effort(self.task)
        self.task.addEffort(newEffort)
        self.assertTrue(newEffort in self.taskFile)

    def testTaskFileDoesNotContainEffort(self):
        """Vérifie que le TaskFile ne contient pas un effort qui n'a pas été ajouté."""
        self.assertFalse(effort.Effort(self.task) in self.taskFile)


class DirtyTaskFileTest(TaskFileTestCase):
    """Tests de TaskFile liés à la détection des modifications."""

    def setUp(self):
        """Initialise les objets de test et prépare le TaskFile pour les tests de détection des modifications."""
        super().setUp()
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()

    def testSetupFileDoesNotNeedSave(self):
        """Vérifie que le TaskFile n'a pas besoin d'être sauvegardé après la configuration initiale."""
        self.assertFalse(self.taskFile.needSave())

    def testNeedSave_AfterNewTaskAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une nouvelle tâche."""
        newTask = task.Task(subject="Task")
        self.emptyTaskFile.tasks().append(newTask)
        self.assertTrue(self.emptyTaskFile.needSave())

    def testNeedSave_AfterTaskMarkedDeleted(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après qu'une tâche ait été marquée comme supprimée."""
        self.task.markDeleted()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNewNoteAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une nouvelle note."""
        newNote = note.Note(subject="Note")
        self.emptyTaskFile.notes().append(newNote)
        self.assertTrue(self.emptyTaskFile.needSave())

    def testNeedSave_AfterNoteRemoved(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une note."""
        self.taskFile.notes().remove(self.note)
        self.assertTrue(self.taskFile.needSave())

    def testDoesNotNeedSave_AfterSave(self):
        """Vérifie que le TaskFile n'a pas besoin d'être sauvegardé après l'avoir sauvegardé."""
        self.emptyTaskFile.tasks().append(task.Task())
        self.emptyTaskFile.setFilename(self.filename)
        self.emptyTaskFile.save()
        self.assertFalse(self.emptyTaskFile.needSave())

    def testDoesNotNeedSave_AfterClose(self):
        """Vérifie que le TaskFile n'a pas besoin d'être sauvegardé après l'avoir fermé."""
        self.taskFile.close()
        self.assertFalse(self.taskFile.needSave())

    def testNeedSave_AfterMerge(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après une fusion avec un autre fichier."""
        self.emptyTaskFile.merge(self.filename)
        self.assertTrue(self.emptyTaskFile.needSave())

    def testDoesNotNeedSave_AfterLoad(self):
        """Vérifie que le TaskFile n'a pas besoin d'être sauvegardé après l'avoir chargé."""
        self.taskFile.tasks().append(task.Task())
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.close()
        self.taskFile.load()
        self.assertFalse(self.taskFile.needSave())

    def testNeedSave_AfterEffortAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'un effort."""
        self.task.addEffort(effort.Effort(self.task, None, None))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEffortRemoved(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'un effort."""
        newEffort = effort.Effort(self.task, None, None)
        self.task.addEffort(newEffort)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.task.removeEffort(newEffort)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskSubject(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une tâche."""
        self.task.setSubject("new subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskDescription(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une tâche."""
        self.task.setDescription("new description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskForegroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une tâche."""
        self.task.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskBackgroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une tâche."""
        self.task.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskPlannedStartDateTime(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la date et heure de début prévue d'une tâche."""
        self.task.setPlannedStartDateTime(date.Now() + date.ONE_HOUR)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskDueDate(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la date d'échéance d'une tâche."""
        self.task.setDueDateTime(date.Tomorrow())
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditTaskCompletionDate(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la date de complétion d'une tâche."""
        self.task.setCompletionDateTime(date.Now())
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditPercentageComplete(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du pourcentage de complétion d'une tâche."""
        self.task.setPercentageComplete(50)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortDescription(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'un effort."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setDescription("new description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortStart(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la date et heure de début d'un effort."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setStart(date.DateTime(2005, 1, 1, 10, 0, 0))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortStop(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la date et heure de fin d'un effort."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setStop(date.DateTime(2005, 1, 1, 10, 0, 0))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortTask(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la tâche associée à un effort."""
        task2 = task.Task()
        self.taskFile.tasks().append(task2)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setTask(task2)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortForegroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'un effort."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterEditEffortBackgroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'un effort."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.effort.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterTaskAddedToCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une tâche à une catégorie."""
        self.task.addCategory(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterTaskRemovedFromCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une tâche d'une catégorie."""
        self.task.addCategory(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.task.removeCategory(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteAddedToCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note à une catégorie."""
        self.note.addCategory(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteRemovedFromCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une note d'une catégorie."""
        self.note.addCategory(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.assertFalse(self.taskFile.needSave())
        self.note.removeCategory(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAddingNoteToTask(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note à une tâche."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.task.addNote(note.Note(subject="Note"))  # pylint: disable=E1101
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterTaskNoteChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification d'une note d'une tâche."""
        self.taskFile.setFilename(self.filename)
        newNote = note.Note(subject="Note")
        self.task.addNote(newNote)  # pylint: disable=E1101
        self.taskFile.save()
        newNote.setSubject("New subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangePriority(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la priorité d'une tâche."""
        self.task.setPriority(10)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangeBudget(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du budget d'une tâche."""
        self.task.setBudget(date.TimeDelta(10))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangeHourlyFee(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du tarif horaire d'une tâche."""
        self.task.setHourlyFee(100)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangeFixedFee(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du tarif fixe d'une tâche."""
        self.task.setFixedFee(500)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAddChild(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une tâche enfant à une tâche."""
        self.taskFile.setFilename(self.filename)
        child = task.Task()
        self.taskFile.tasks().append(child)
        self.taskFile.save()
        print(
            "testNeedSave_AfterAddChild : allChanges = %s"
            % self.taskFile.monitor().allChanges()
        )  # N' affiche rien !
        self.task.addChild(child)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterRemoveChild(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une tâche enfant d'une tâche."""
        self.taskFile.setFilename(self.filename)
        child = task.Task()
        self.taskFile.tasks().append(child)
        self.task.addChild(child)
        self.taskFile.save()
        self.task.removeChild(child)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterSetReminder(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du rappel d'une tâche."""
        self.task.setReminder(date.DateTime(2005, 1, 1, 10, 0, 0))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangeRecurrence(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la récurrence d'une tâche."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.task.setRecurrence(date.Recurrence("daily"))
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangeSetting(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification d'un paramètre de tâche."""
        self.task.setShouldMarkCompletedWhenAllChildrenCompleted(True)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAddingCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterRemovingCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.categories().remove(self.category)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFilteringCategory(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après le filtrage d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.setFiltered()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterCategorySubjectChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.setSubject("new subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterCategoryDescriptionChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.setDescription("new description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangingCategoryForegroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangingCategoryBackgroundColor(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMakingSubclassesExclusive(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après avoir rendu les sous-catégories exclusives d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.makeSubcategoriesExclusive()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteSubjectChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une note."""
        list(self.taskFile.notes())[0].setSubject("new subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteDescriptionChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une note."""
        list(self.taskFile.notes())[0].setDescription("new description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteForegroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une note."""
        list(self.taskFile.notes())[0].setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterNoteBackgroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une note."""
        list(self.taskFile.notes())[0].setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAddNoteChild(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note enfant à une note."""
        list(self.taskFile.notes())[0].addChild(note.Note())
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterRemoveNoteChild(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une note enfant d'une note."""
        child = note.Note()
        list(self.taskFile.notes())[0].addChild(child)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        list(self.taskFile.notes())[0].removeChild(child)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangingTaskExpansionState(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de l'état d'expansion d'une tâche."""
        self.task.expand()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangingCategoryExpansionState(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de l'état d'expansion d'une catégorie."""
        self.taskFile.categories().append(self.category)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.category.expand()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterChangingNoteExpansionState(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de l'état d'expansion d'une note."""
        self.taskFile.notes().append(self.note)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.note.expand()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMarkDeleted(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après qu'un élément ait été marqué comme supprimé."""
        self.taskFile.notes().append(self.note)
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.note.markDeleted()
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMarkNotDeleted(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après qu'un élément ait été marqué comme non supprimé."""
        self.taskFile.notes().append(self.note)
        self.note.markDeleted()
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.note.cleanDirty()
        self.assertTrue(self.taskFile.needSave())

    def testLastFilename_EqualsCurrentFilenameAfterSetFilename(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier actuel après l'avoir défini."""
        self.taskFile.setFilename(self.filename)
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_EqualsPreviousFilenameAfterClose(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier précédent après la fermeture du TaskFile."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.close()
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_EqualsPreviousFilenameAfterClosingTwice(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier précédent après avoir fermé le TaskFile deux fois."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.close()
        self.taskFile.close()
        self.assertEqual(self.filename, self.taskFile.lastFilename())

    def testLastFilename_EqualsCurrentFilenameAfterSaveAs(self):
        """Vérifie que le dernier nom de fichier est égal au nom de fichier actuel après avoir enregistré sous un nouveau nom."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.saveas(self.filename2)
        self.assertEqual(self.filename2, self.taskFile.lastFilename())


class ChangingAttachmentsTestsMixin(object):
    """
    Classe Mixin.

    Fournit des tests pour vérifier que les modifications des attachements sont correctement détectées par le TaskFile.
    """

    def testNeedSave_AfterAttachmentAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une attachements à une tâche."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.item.addAttachments(self.attachment)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAttachmentRemoved(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la suppression d'une attachements d'une tâche."""
        self.taskFile.setFilename(self.filename)
        self.item.addAttachments(self.attachment)
        self.taskFile.save()
        self.item.removeAttachments(self.attachment)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterAttachmentsReplaced(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après le remplacement des attachements d'une tâche."""
        self.taskFile.setFilename(self.filename)
        self.item.addAttachments(self.attachment)
        self.taskFile.save()
        self.item.setAttachments([FakeAttachment("file", "attachment2")])
        self.assertTrue(self.taskFile.needSave())

    def addAttachment(self, anAttachment):
        """Ajoute une attachements à l'élément de test et prépare le TaskFile pour les tests de détection des modifications liées aux attachements."""
        print(
            f"TaskFileTest.ChangingAttachmentsTestsMixin.addAttachment : 🛠️ DEBUG - Création d'une tâche self={self} avec attachements: {self.attachments}, anAttachment={anAttachment}"
        )

        self.taskFile.setFilename(self.filename)
        self.item.addAttachments(anAttachment)
        self.taskFile.save()

    def addFileAttachment(self):
        """Ajoute une attachements de type fichier à l'élément de test et prépare le TaskFile pour les tests de détection des modifications liées aux attachements de type fichier."""
        self.fileAttachment = attachment.FileAttachment(
            "Old location"
        )  # pylint: disable=W0201
        self.addAttachment(self.fileAttachment)

    def testNeedSave_AfterFileAttachmentLocationChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la localisation d'une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.setLocation("New location")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFileAttachmentSubjectChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.setSubject("New subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFileAttachmentDescriptionChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.setDescription("New description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFileAttachmentForegroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFileAttachmentBackgroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterFileAttachmentNoteAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note à une attachements de type fichier."""
        self.addFileAttachment()
        self.fileAttachment.addNote(
            note.Note(subject="Note")
        )  # pylint: disable=E1101
        self.assertTrue(self.taskFile.needSave())

    def addURIAttachment(self):
        """Ajoute une attachements de type URI à l'élément de test et prépare le TaskFile pour les tests de détection des modifications liées aux attachements de type URI."""
        self.uriAttachment = attachment.URIAttachment(
            "Old location"
        )  # pylint: disable=W0201
        self.addAttachment(self.uriAttachment)

    def testNeedSave_AfterURIAttachmentLocationChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la localisation d'une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.setLocation("New location")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterURIAttachmentSubjectChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.setSubject("New subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterURIAttachmentDescriptionChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.setDescription("New description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterURIAttachmentForegroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterURIAttachmentBackgroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterURIAttachmentNoteAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note à une attachements de type URI."""
        self.addURIAttachment()
        self.uriAttachment.addNote(
            note.Note(subject="Note")
        )  # pylint: disable=E1101
        self.assertTrue(self.taskFile.needSave())

    def addMailAttachment(self):
        """Ajoute une attachements de type mail à l'élément de test et prépare le TaskFile pour les tests de détection des modifications liées aux attachements de type mail."""
        self.mailAttachment = attachment.MailAttachment(
            self.filename,
            readMail=lambda location: ("", ""),  # pylint: disable=W0201
        )
        self.addAttachment(self.mailAttachment)

    def testNeedSave_AfterMailAttachmentLocationChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la localisation d'une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.setLocation("New location")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMailAttachmentSubjectChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification du sujet d'une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.setSubject("New subject")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMailAttachmentDescriptionChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la description d'une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.setDescription("New description")
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMailAttachmentForegroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de premier plan d'une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.setForegroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMailAttachmentBackgroundColorChanged(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après la modification de la couleur de fond d'une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.setBackgroundColor(wx.RED)
        self.assertTrue(self.taskFile.needSave())

    def testNeedSave_AfterMailAttachmentNoteAdded(self):
        """Vérifie que le TaskFile a besoin d'être sauvegardé après l'ajout d'une note à une attachements de type mail."""
        self.addMailAttachment()
        self.mailAttachment.addNote(
            note.Note(subject="Note")
        )  # pylint: disable=E1101
        self.assertTrue(self.taskFile.needSave())


class TaskFileDirtyWhenChangingAttachmentsTestCase(TaskFileTestCase):
    """Classe de test pour vérifier que le TaskFile est marqué comme "dirty" (modifié) lorsqu'on modifie les attachements d'une tâche, d'une note ou d'une catégorie."""

    def setUp(self):
        """Prépare les éléments de test et un attachement factice pour les tests de détection des modifications liées aux attachements."""
        super().setUp()
        self.attachment = FakeAttachment("file", "attachment")


class TaskFileDirtyWhenChangingTaskAttachmentsTestCase(
    TaskFileDirtyWhenChangingAttachmentsTestCase, ChangingAttachmentsTestsMixin
):
    """Classe de test pour vérifier que le TaskFile est marqué comme "dirty" (modifié) lorsqu'on modifie les attachements d'une tâche."""

    def setUp(self):
        """Prépare les éléments de test et un attachement factice pour les tests de détection des modifications liées aux attachements d'une tâche."""
        super().setUp()
        self.item = self.task


class TaskFileDirtyWhenChangingNoteAttachmentsTestCase(
    TaskFileDirtyWhenChangingAttachmentsTestCase, ChangingAttachmentsTestsMixin
):
    """Classe de test pour vérifier que le TaskFile est marqué comme "dirty" (modifié) lorsqu'on modifie les attachements d'une note."""

    def setUp(self):
        """Prépare les éléments de test et un attachement factice pour les tests de détection des modifications liées aux attachements d'une note."""
        super().setUp()
        self.item = self.note


class TaskFileDirtyWhenChangingCategoryAttachmentsTestCase(
    TaskFileDirtyWhenChangingAttachmentsTestCase, ChangingAttachmentsTestsMixin
):
    """Classe de test pour vérifier que le TaskFile est marqué comme "dirty" (modifié) lorsqu'on modifie les attachements d'une catégorie."""

    def setUp(self):
        """Prépare les éléments de test et un attachement factice pour les tests de détection des modifications liées aux attachements d'une catégorie."""
        super().setUp()
        self.item = self.category


class TaskFileSaveAndLoadTest(TaskFileTestCase):
    """Classe de test pour vérifier que les tâches, catégories et notes sont correctement sauvegardées et chargées par le TaskFile."""

    def setUp(self):
        """Prépare un TaskFile vide pour les tests de sauvegarde et de chargement."""
        super().setUp()
        self.emptyTaskFile.setFilename(self.filename)

    def saveAndLoad(self, tasks, categories=None, notes=None):
        """Sauvegarde les tâches, catégories et notes fournies dans le TaskFile vide, puis le recharge et vérifie que les éléments chargés correspondent à ceux qui ont été sauvegardés."""
        categories = categories or []
        notes = notes or []
        self.emptyTaskFile.tasks().extend(tasks)
        self.emptyTaskFile.categories().extend(categories)
        self.emptyTaskFile.notes().extend(notes)
        self.emptyTaskFile.save()
        self.emptyTaskFile.load()
        self.assertEqual(
            sorted([eachTask.subject() for eachTask in tasks]),
            sorted(
                [eachTask.subject() for eachTask in self.emptyTaskFile.tasks()]
            ),
        )
        self.assertEqual(
            sorted([eachCategory.subject() for eachCategory in categories]),
            sorted(
                [
                    eachCategory.subject()
                    for eachCategory in self.emptyTaskFile.categories()
                ]
            ),
        )
        self.assertEqual(
            sorted([eachNote.subject() for eachNote in notes]),
            sorted(
                [eachNote.subject() for eachNote in self.emptyTaskFile.notes()]
            ),
        )

    def testSaveAndLoad(self):
        """Vérifie que les tâches, catégories et notes sont correctement sauvegardées et chargées par le TaskFile."""
        self.saveAndLoad(
            [task.Task(subject="ABC"), task.Task(dueDateTime=date.Tomorrow())]
        )

    def testSaveAndLoadTaskWithChild(self):
        """Vérifie que les tâches avec des tâches enfants sont correctement sauvegardées et chargées par le TaskFile."""
        parentTask = task.Task()
        childTask = task.Task(parent=parentTask)
        parentTask.addChild(childTask)
        self.saveAndLoad([parentTask, childTask])

    def testSaveAndLoadCategory(self):
        """Vérifie que les catégories sont correctement sauvegardées et chargées par le TaskFile."""
        self.saveAndLoad([], [self.category])

    def testSaveAndLoadNotes(self):
        """Vérifie que les notes sont correctement sauvegardées et chargées par le TaskFile."""
        self.saveAndLoad([], [], [self.note])

    def testSaveAs(self):
        """
        Vérifie que la méthode saveas du TaskFile fonctionne correctement
        en sauvegardant les tâches, catégories et notes dans un nouveau fichier,
        puis en rechargeant ce fichier
        et en vérifiant que les éléments chargés correspondent à ceux qui ont été sauvegardés.
        """
        self.taskFile.saveas("new.tsk")
        self.taskFile.load()
        self.assertEqual(1, len(self.taskFile.tasks()))
        self.taskFile.close()
        self.remove("new.tsk", "new.tsk.delta")

    def testSaveAsOverwrites(self):
        """
        Vérifie que la méthode saveas du TaskFile écrase correctement
        les données existantes dans le fichier de destination
        en sauvegardant les tâches, catégories et notes dans un nouveau fichier,
        puis en rechargeant ce fichier
        et en vérifiant que les éléments chargés correspondent à ceux qui ont été sauvegardés,
        même si le fichier de destination existait déjà avec des données différentes.
        """
        self.taskFile.saveas("new.tsk")
        self.taskFile.close()
        self.taskFile.tasks().extend([task.Task(subject="foo")])
        self.taskFile.saveas("new.tsk")
        self.assertEqual(1, len(self.taskFile.tasks()))
        self.taskFile.close()
        self.remove("new.tsk", "new.tsk.delta")


class TaskFileMergeTest(TaskFileTestCase):
    """Classe de test pour vérifier que la méthode merge du TaskFile fonctionne correctement en fusionnant les tâches, catégories et notes d'un autre fichier de tâches dans le TaskFile actuel."""

    def setUp(self):
        """Prépare un TaskFile de fusion pour les tests de fusion en créant un nouveau TaskFile, en lui attribuant un nom de fichier et en le laissant prêt à être fusionné avec le TaskFile de test principal."""
        super().setUp()
        self.mergeFile = persistence.TaskFile()
        self.mergeFile.setFilename("merge.tsk")

    def tearDown(self):
        """Nettoie les ressources utilisées par les tests de fusion en fermant et en arrêtant le TaskFile de fusion, puis en supprimant les fichiers de fusion créés pendant les tests, avant d'appeler la méthode tearDown de la classe parente pour effectuer tout nettoyage supplémentaire nécessaire."""
        self.mergeFile.close()
        self.mergeFile.stop()
        self.remove("merge.tsk", "merge.tsk.delta")
        super().tearDown()

    def merge(self):
        """Effectue la fusion des données du TaskFile de fusion dans le TaskFile de test principal en sauvegardant d'abord les données du TaskFile de fusion, puis en appelant la méthode merge du TaskFile de test principal avec le nom de fichier du TaskFile de fusion pour effectuer la fusion des tâches, catégories et notes."""
        self.mergeFile.save()
        self.taskFile.merge("merge.tsk")

    def testMerge_Tasks(self):
        """Vérifie que les tâches du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une nouvelle tâche au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal a augmenté d'une unité pour refléter la tâche fusionnée."""
        self.mergeFile.tasks().append(task.Task())
        self.merge()
        self.assertEqual(2, len(self.taskFile.tasks()))

    def testMerge_TasksWithSubtask(self):
        """Vérifie que les tâches avec des tâches enfants du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en créant une tâche parent et une tâche enfant dans le TaskFile de fusion, en établissant la relation parent-enfant entre elles, en effectuant la fusion, puis en vérifiant que le nombre total de tâches dans le TaskFile de test principal a augmenté de deux unités pour refléter les tâches fusionnées et que le nombre de tâches racines a augmenté d'une unité pour refléter la tâche parent fusionnée."""
        parent = task.Task(subject="parent")
        child = task.Task(subject="child")
        parent.addChild(child)
        child.setParent(parent)
        self.mergeFile.tasks().extend([parent, child])
        self.merge()
        self.assertEqual(3, len(self.taskFile.tasks()))
        self.assertEqual(2, len(self.taskFile.tasks().rootItems()))

    def testMerge_OneCategoryInMergeFile(self):
        """Vérifie que les catégories du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le sujet de la catégorie dans le TaskFile de test principal correspond au sujet de la catégorie fusionnée."""
        self.taskFile.categories().remove(self.category)
        self.mergeFile.categories().append(self.category)
        self.merge()
        self.assertEqual(
            [self.category.subject()],
            [cat.subject() for cat in self.taskFile.categories()],
        )

    def testMerge_DifferentCategories(self):
        """Vérifie que les catégories différentes du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie avec un sujet différent au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la catégorie fusionnée."""
        self.mergeFile.categories().append(
            category.Category("another category")
        )
        self.merge()
        self.assertEqual(2, len(self.taskFile.categories()))

    def testMerge_SameSubject(self):
        """Vérifie que les catégories avec le même sujet du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie avec le même sujet que la catégorie existante au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la catégorie fusionnée et que les sujets des catégories dans le TaskFile de test principal correspondent au sujet de la catégorie fusionnée."""
        self.mergeFile.categories().append(
            category.Category(self.category.subject())
        )
        self.merge()
        self.assertEqual(
            [self.category.subject()] * 2,
            [cat.subject() for cat in self.taskFile.categories()],
        )

    def testMerge_CategoryWithTask(self):
        """Vérifie que les catégories avec des tâches du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie au TaskFile de fusion, en associant une tâche à cette catégorie, en effectuant la fusion, puis en vérifiant que la tâche associée à la catégorie dans le TaskFile de test principal correspond à la tâche associée à la catégorie fusionnée."""
        self.taskFile.categories().remove(self.category)
        self.mergeFile.categories().append(self.category)
        aTask = task.Task(subject="merged task")
        self.mergeFile.tasks().append(aTask)
        self.category.addCategorizable(aTask)
        self.merge()
        self.assertEqual(
            aTask.id(),
            list(list(self.taskFile.categories())[0].categorizables())[0].id(),
        )

    def testMerge_Notes(self):
        """Vérifie que les notes du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une nouvelle note au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de notes dans le TaskFile de test principal a augmenté d'une unité pour refléter la note fusionnée."""
        newNote = note.Note(subject="new note")
        self.mergeFile.notes().append(newNote)
        self.merge()
        self.assertEqual(2, len(self.taskFile.notes()))

    def testMerge_SameTask(self):
        """Vérifie que les tâches avec le même ID du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une tâche avec le même ID que la tâche existante au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal n'a pas augmenté et que le sujet de la tâche dans le TaskFile de test principal correspond au sujet de la tâche fusionnée."""
        mergedTask = task.Task(subject="merged task", id=self.task.id())
        self.mergeFile.tasks().append(mergedTask)
        self.merge()
        self.assertEqual(1, len(self.taskFile.tasks()))
        self.assertEqual(
            "merged task", list(self.taskFile.tasks())[0].subject()
        )

    def testMerge_SameNote(self):
        """Vérifie que les notes avec le même ID du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une note avec le même ID que la note existante au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de notes dans le TaskFile de test principal n'a pas augmenté et que le sujet de la note dans le TaskFile de test principal correspond au sujet de la note fusionnée."""
        mergedNote = note.Note(subject="merged note", id=self.note.id())
        self.mergeFile.notes().append(mergedNote)
        self.merge()
        self.assertEqual(1, len(self.taskFile.notes()))
        self.assertEqual(
            "merged note", list(self.taskFile.notes())[0].subject()
        )

    def testMerge_SameCategory(self):
        """Vérifie que les catégories avec le même ID du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie avec le même ID que la catégorie existante au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal n'a pas augmenté et que le sujet de la catégorie dans le TaskFile de test principal correspond au sujet de la catégorie fusionnée."""
        mergedCategory = category.Category(
            subject="merged category", id=self.category.id()
        )
        self.mergeFile.categories().append(mergedCategory)
        self.merge()
        self.assertEqual(1, len(self.taskFile.categories()))
        self.assertEqual(
            "merged category", list(self.taskFile.categories())[0].subject()
        )

    def testMerge_CategoryLinkedToTask(self):
        """Vérifie que les catégories liées à des tâches du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie au TaskFile de fusion, en associant une tâche à cette catégorie, en effectuant la fusion, puis en vérifiant que la tâche associée à la catégorie dans le TaskFile de test principal correspond à la tâche associée à la catégorie fusionnée."""
        self.task.addCategory(self.category)
        self.category.addCategorizable(self.task)
        mergedCategory = category.Category(
            "merged category", id=self.category.id()
        )
        self.mergeFile.categories().append(mergedCategory)
        self.merge()
        self.assertEqual(
            self.category.id(), list(self.task.categories())[0].id()
        )

    def testMerge_CategoryLinkedToNote(self):
        """Vérifie que les catégories liées à des notes du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie au TaskFile de fusion, en associant une note à cette catégorie, en effectuant la fusion, puis en vérifiant que la note associée à la catégorie dans le TaskFile de test principal correspond à la note associée à la catégorie fusionnée."""
        self.note.addCategory(self.category)
        self.category.addCategorizable(self.note)
        mergedCategory = category.Category(
            "merged category", id=self.category.id()
        )
        self.mergeFile.categories().append(mergedCategory)
        self.merge()
        self.assertEqual(
            self.category.id(), list(self.note.categories())[0].id()
        )

    def testMerge_ExistingCategoryWithoutExistingSubCategoryRemovesTheSubCategory(
        self,
    ):
        """Vérifie que les catégories existantes sans sous-catégorie existante du TaskFile de fusion sont correctement fusionnées dans le TaskFile de test principal en ajoutant une catégorie avec une sous-catégorie au TaskFile de test principal, en ajoutant une catégorie sans sous-catégorie au TaskFile de fusion, en effectuant la fusion, puis en vérifiant que la sous-catégorie a été supprimée du TaskFile de test principal pour refléter la structure de la catégorie fusionnée."""
        subCategory = category.Category("subcategory")
        self.category.addChild(subCategory)
        self.taskFile.categories().append(subCategory)
        self.task.addCategory(subCategory)
        subCategory.addCategorizable(self.task)
        self.assertEqual(2, len(self.taskFile.categories()))
        mergedCategory = category.Category(
            "merged category", id=self.category.id()
        )
        self.mergeFile.categories().append(mergedCategory)
        self.merge()
        self.assertEqual(1, len(self.taskFile.categories()))


class LockedTaskFileLockTest(TaskFileTestCase):
    """Classe de test pour vérifier que les fichiers de tâches verrouillés (LockedTaskFile) ne restent pas verrouillés après les opérations de chargement, de sauvegarde et de fermeture."""

    def createTaskFiles(self):
        """Crée les instances de LockedTaskFile pour les tests de verrouillage en initialisant deux instances de LockedTaskFile, une pour le fichier de tâches principal et une pour un fichier de tâches vide, qui seront utilisées dans les tests pour vérifier que les fichiers ne restent pas verrouillés après les opérations de chargement, de sauvegarde et de fermeture."""
        # pylint: disable=W0201
        self.taskFile = persistence.LockedTaskFile()
        self.emptyTaskFile = persistence.LockedTaskFile()

    def tearDown(self):
        """Nettoie les ressources utilisées par les tests de verrouillage en fermant et en arrêtant les instances de LockedTaskFile, puis en appelant la méthode tearDown de la classe parente pour effectuer tout nettoyage supplémentaire nécessaire."""
        self.taskFile.close()
        self.taskFile.stop()
        self.emptyTaskFile.close()
        super().tearDown()

    def testFileIsNotLockedInitially(self):
        """Vérifie que les fichiers de tâches ne sont pas verrouillés initialement en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False avant toute opération de chargement, de sauvegarde ou de fermeture."""
        self.failIf(self.taskFile.is_locked())
        self.failIf(self.emptyTaskFile.is_locked())

    def testFileIsNotLockedAfterLoading(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après le chargement en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir chargé un fichier de tâches avec la méthode load."""
        self.taskFile.load(self.filename)
        self.failIf(self.taskFile.is_locked())

    def testFileIsNotLockedAfterClosing(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après la fermeture en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir fermé le fichier de tâches avec la méthode close."""
        self.taskFile.close()
        self.failIf(self.taskFile.is_locked())

    def testFileIsnotLockedAfterLoadingAndClosing(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après le chargement et la fermeture en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir chargé un fichier de tâches avec la méthode load, puis l'avoir fermé avec la méthode close."""
        self.taskFile.load(self.filename)
        self.taskFile.close()
        self.failIf(self.taskFile.is_locked())

    def testFileIsNotLockedAfterSaving(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après la sauvegarde en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir défini un nom de fichier avec la méthode setFilename, puis sauvegardé le fichier de tâches avec la méthode save."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.failIf(self.taskFile.is_locked())

    def testFileIsNotLockedAfterSavingAndClosing(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après la sauvegarde et la fermeture en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir défini un nom de fichier avec la méthode setFilename, sauvegardé le fichier de tâches avec la méthode save, puis l'avoir fermé avec la méthode close."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.close()
        self.failIf(self.taskFile.is_locked())

    def testFileIsNotLockedAfterSaveAs(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après la sauvegarde avec un nouveau nom de fichier en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir défini un nom de fichier avec la méthode setFilename, puis sauvegardé le fichier de tâches avec la méthode saveas en utilisant un nouveau nom de fichier."""
        self.taskFile.saveas(self.filename)
        self.failIf(self.taskFile.is_locked())

    def testFileIsNotLockedAfterSaveAndSaveAs(self):
        """Vérifie que les fichiers de tâches ne restent pas verrouillés après la sauvegarde et la sauvegarde avec un nouveau nom de fichier en vérifiant que les méthodes is_locked des instances de LockedTaskFile retournent False après avoir défini un nom de fichier avec la méthode setFilename, sauvegardé le fichier de tâches avec la méthode save, puis sauvegardé à nouveau le fichier de tâches avec la méthode saveas en utilisant un nouveau nom de fichier."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.saveas(self.filename2)
        self.failIf(self.taskFile.is_locked())

    def testFileCanBeLoadedAfterClose(self):
        """Vérifie que les fichiers de tâches peuvent être chargés après la fermeture en vérifiant que les tâches, catégories et notes d'un fichier de tâches peuvent être chargées avec la méthode load après avoir fermé le fichier de tâches avec la méthode close, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant la fermeture."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.close()
        self.emptyTaskFile.load(self.filename)
        self.assertEqual(1, len(self.emptyTaskFile.tasks()))

    def testOriginalFileCanBeLoadedAfterSaveAs(self):
        """Vérifie que les fichiers de tâches peuvent être chargés après la sauvegarde avec un nouveau nom de fichier en vérifiant que les tâches, catégories et notes d'un fichier de tâches peuvent être chargées avec la méthode load après avoir sauvegardé le fichier de tâches avec la méthode saveas en utilisant un nouveau nom de fichier, puis fermé le fichier de tâches, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant la sauvegarde avec le nouveau nom de fichier."""
        self.taskFile.setFilename(self.filename)
        self.taskFile.save()
        self.taskFile.saveas(self.filename2)
        self.taskFile.close()
        self.emptyTaskFile.load(self.filename)
        self.assertEqual(1, len(self.emptyTaskFile.tasks()))


class TaskFileMonitorTestBase(TaskFileTestCase):
    """Classe de test pour vérifier que le TaskFileMonitor suit correctement les modifications apportées aux tâches, catégories et notes d'un TaskFile, en vérifiant que les changements sont correctement enregistrés et réinitialisés après les opérations de sauvegarde et de fermeture, et que les GUID des moniteurs sont correctement gérés dans les fichiers de changements."""

    def setUp(self):
        """Prépare les éléments de test et un autre TaskFile pour les tests de suivi des modifications en sauvegardant d'abord le TaskFile de test principal avec les éléments de test, puis en créant une nouvelle instance de TaskFile pour le suivi des modifications, en lui attribuant le même nom de fichier que le TaskFile de test principal, et en chargeant les données du fichier pour que les deux TaskFiles soient synchronisés avant les tests de suivi des modifications."""
        super().setUp()

        self.taskFile.saveas(self.filename)
        self.taskFile.load()

        self.otherFile = persistence.TaskFile()
        self.otherFile.setFilename(self.filename)
        self.otherFile.load()

    def tearDown(self):
        """Nettoie les ressources utilisées par les tests de suivi des modifications en fermant et en arrêtant l'autre TaskFile utilisé pour le suivi des modifications, puis en supprimant les fichiers de tâches et de changements créés pendant les tests, avant d'appeler la méthode tearDown de la classe parente pour effectuer tout nettoyage supplémentaire nécessaire."""
        self.otherFile.close()
        self.otherFile.stop()
        self.remove("other.tsk")
        super().tearDown()

    def testTaskExistsAfterLoad(self):
        """Vérifie que les tâches existent après le chargement en vérifiant que les tâches du TaskFile de test principal sont présentes et accessibles après avoir chargé les données du fichier de tâches, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant le chargement."""
        # self.assertEqual(self.taskFile.monitor().getChanges(self.task), set())
        self.assertEqual(self.taskFile.monitor().getChanges(self.task), {})

    def testCategoryExistsAfterLoad(self):
        """Vérifie que les catégories existent après le chargement en vérifiant que les catégories du TaskFile de test principal sont présentes et accessibles après avoir chargé les données du fichier de tâches, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant le chargement."""
        # self.assertEqual(self.taskFile.monitor().getChanges(self.category), set())
        self.assertEqual(self.taskFile.monitor().getChanges(self.category), {})

    def testNoteExistsAfterLoad(self):
        """Vérifie que les notes existent après le chargement en vérifiant que les notes du TaskFile de test principal sont présentes et accessibles après avoir chargé les données du fichier de tâches, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant le chargement."""
        # self.assertEqual(self.taskFile.monitor().getChanges(self.note), set())
        self.assertEqual(self.taskFile.monitor().getChanges(self.note), {})

    def testChangeTask(self):
        """Vérifie que les modifications apportées à une tâche sont correctement suivies par le TaskFileMonitor en modifiant le sujet d'une tâche du TaskFile de test principal, puis en vérifiant que le TaskFileMonitor a enregistré la modification du sujet pour cette tâche."""
        self.task.setSubject("New subject")
        # self.assertEqual(self.taskFile.monitor().getChanges(self.task), set(['subject']))
        self.assertEqual(
            self.taskFile.monitor().getChanges(self.task), {"subject"}
        )

    def testChangeCategory(self):
        """Vérifie que les modifications apportées à une catégorie sont correctement suivies par le TaskFileMonitor en modifiant le sujet d'une catégorie du TaskFile de test principal, puis en vérifiant que le TaskFileMonitor a enregistré la modification du sujet pour cette catégorie."""
        self.category.setSubject("New subject")
        # self.assertEqual(self.taskFile.monitor().getChanges(self.category), set(['subject']))
        self.assertEqual(
            self.taskFile.monitor().getChanges(self.category), {"subject"}
        )

    def testChangeNone(self):
        """Vérifie que les modifications apportées à une note sont correctement suivies par le TaskFileMonitor en modifiant le sujet d'une note du TaskFile de test principal, puis en vérifiant que le TaskFileMonitor a enregistré la modification du sujet pour cette note."""
        self.note.setSubject("New subject")
        # self.assertEqual(self.taskFile.monitor().getChanges(self.note), set(['subject']))
        self.assertEqual(
            self.taskFile.monitor().getChanges(self.note), {"subject"}
        )

    def testChangesResetAfterSave(self):
        """Vérifie que les modifications suivies par le TaskFileMonitor sont réinitialisées après la sauvegarde en modifiant le sujet d'une tâche du TaskFile de test principal, en sauvegardant le fichier de tâches, puis en vérifiant que le TaskFileMonitor a réinitialisé les modifications enregistrées pour cette tâche après la sauvegarde."""
        self.task.setSubject("New subject")
        self.taskFile.save()
        # self.assertEqual(self.taskFile.monitor().getChanges(self.task), set([]))
        self.assertEqual(self.taskFile.monitor().getChanges(self.task), {})

    def testResetAfterClose(self):
        """Vérifie que les modifications suivies par le TaskFileMonitor sont réinitialisées après la fermeture en modifiant le sujet d'une tâche du TaskFile de test principal, en fermant le fichier de tâches, puis en vérifiant que le TaskFileMonitor a réinitialisé les modifications enregistrées pour cette tâche après la fermeture."""
        self.taskFile.close()
        self.assertEqual(self.taskFile.monitor().getChanges(self.task), None)

    def _loadChangesFromFile(self, filename):
        """Charge les modifications enregistrées dans le fichier de changements associé au fichier de tâches spécifié en utilisant le ChangesXMLReader pour lire les données du fichier de changements et retourner les modifications enregistrées pour les tâches, catégories et notes du TaskFile de test principal."""
        # return persistence.ChangesXMLReader(file(filename + '.delta', 'rU')).read()
        return persistence.ChangesXMLReader(
            io.open(filename + ".delta", "rU")
        ).read()

    def testGUIDPresentAfterLoad(self):
        """Vérifie que le GUID du TaskFileMonitor est présent dans le fichier de changements après le chargement en vérifiant que le GUID du TaskFileMonitor du TaskFile de test principal est présent dans les modifications chargées à partir du fichier de changements associé au fichier de tâches après avoir chargé les données du fichier de tâches."""
        self.failUnless(
            self.taskFile.monitor().guid()
            in self._loadChangesFromFile(self.filename)
        )

    def testGUIDNotPresentAfterClose(self):
        """Vérifie que le GUID du TaskFileMonitor n'est pas présent dans le fichier de changements après la fermeture en vérifiant que le GUID du TaskFileMonitor du TaskFile de test principal n'est pas présent dans les modifications chargées à partir du fichier de changements associé au fichier de tâches après avoir fermé le fichier de tâches."""
        self.taskFile.close()
        self.failIf(
            self.taskFile.monitor().guid()
            in self._loadChangesFromFile(self.filename)
        )

    def testChangeOtherSetsChanges(self):
        """Vérifie que les modifications apportées à une tâche dans un autre TaskFile sont correctement suivies par le TaskFileMonitor en modifiant le sujet d'une tâche du TaskFile utilisé pour le suivi des modifications, en sauvegardant ce fichier de tâches, puis en vérifiant que le TaskFileMonitor du TaskFile de test principal a enregistré la modification du sujet pour cette tâche, tandis que le TaskFileMonitor de l'autre fichier de tâches n'a pas enregistré de modifications pour cette tâche."""
        # self.otherFile.monitor().setChanges(self.task.id(), set(['subject']))
        self.otherFile.monitor().setChanges(self.task.id(), {"subject"})
        self.otherFile.save()
        allChanges = self._loadChangesFromFile(self.filename)
        # self.assertEqual(allChanges[self.taskFile.monitor().guid()].getChanges(self.task), set(['subject']))
        self.assertEqual(
            allChanges[self.taskFile.monitor().guid()].getChanges(self.task),
            {"subject"},
        )
        # self.assertEqual(allChanges[self.otherFile.monitor().guid()].getChanges(self.task), set())
        self.assertEqual(
            allChanges[self.otherFile.monitor().guid()].getChanges(self.task),
            {},
        )

    def testDeleteObject(self):
        """Vérifie que la suppression d'une tâche dans un autre TaskFile est correctement suivie par le TaskFileMonitor en supprimant une tâche du TaskFile utilisé pour le suivi des modifications, en sauvegardant ce fichier de tâches, puis en vérifiant que le TaskFileMonitor du TaskFile de test principal a enregistré la suppression pour cette tâche, tandis que le TaskFileMonitor de l'autre fichier de tâches n'a pas enregistré de modifications pour cette tâche."""
        self.otherFile.tasks().remove(self.otherFile.tasks().rootItems()[0])
        self.otherFile.save()
        allChanges = self._loadChangesFromFile(self.filename)
        # self.assertEqual(allChanges[self.taskFile.monitor().guid()].getChanges(self.task), set(['__del__']))
        self.assertEqual(
            allChanges[self.taskFile.monitor().guid()].getChanges(self.task),
            {"__del__"},
        )
        self.assertEqual(
            allChanges[self.otherFile.monitor().guid()].getChanges(self.task),
            None,
        )

    def testDiskChangesAfterLoad(self):
        """Vérifie que les modifications enregistrées dans le fichier de changements sont correctement chargées après le chargement en vérifiant que les modifications enregistrées pour une tâche dans le fichier de changements associé au fichier de tâches sont réinitialisées après avoir chargé les données du fichier de tâches, et que les éléments chargés correspondent à ceux qui ont été sauvegardés avant le chargement."""
        changes = self._loadChangesFromFile(self.filename)[
            self.taskFile.monitor().guid()
        ]
        # self.assertEqual(changes.getChanges(self.task), set())
        self.assertEqual(changes.getChanges(self.task), {})

    def testNewObject(self):
        """Vérifie que les nouvelles tâches créées dans un autre TaskFile sont correctement suivies par le TaskFileMonitor en créant une nouvelle tâche dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant ce fichier de tâches, puis en vérifiant que le TaskFileMonitor du TaskFile de test principal n'a pas enregistré de modifications pour cette tâche, tandis que le TaskFileMonitor de l'autre fichier de tâches n'a pas enregistré de modifications pour cette tâche."""
        item = task.Task(subject="New task")
        self.otherFile.tasks().append(item)
        self.otherFile.save()
        self.taskFile.save()
        allChanges = self._loadChangesFromFile(self.filename)
        # self.assertEqual(allChanges[self.otherFile.monitor().guid()].getChanges(item), set())
        self.assertEqual(
            allChanges[self.otherFile.monitor().guid()].getChanges(item), {}
        )
        # self.assertEqual(allChanges[self.taskFile.monitor().guid()].getChanges(item), set())
        self.assertEqual(
            allChanges[self.taskFile.monitor().guid()].getChanges(item), {}
        )


class TaskFileMultiUserTestBase(object):
    """Classe de test pour vérifier que les modifications apportées à un TaskFile dans un autre processus sont correctement suivies et reflétées dans le TaskFile actuel, en vérifiant que les tâches, catégories et notes créées, modifiées ou supprimées dans un autre processus sont correctement chargées et affichées dans le TaskFile actuel après les opérations de sauvegarde et de chargement."""

    def setUp(self):
        """Prépare les éléments de test et un autre TaskFile pour les tests multi-utilisateurs en créant d'abord les éléments de test dans le TaskFile de test principal, en sauvegardant ce fichier de tâches, puis en créant une nouvelle instance de TaskFile pour le deuxième utilisateur, en lui attribuant le même nom de fichier que le TaskFile de test principal, et en chargeant les données du fichier pour que les deux TaskFiles soient synchronisés avant les tests multi-utilisateurs."""
        self.createTaskFiles()

        self.task = task.Task(subject="Task")
        self.taskFile1.tasks().append(self.task)

        self.category = category.Category(subject="Category")
        self.taskFile1.categories().append(self.category)

        self.note = note.Note(subject="Note")
        self.taskFile1.notes().append(self.note)

        self.taskNote = note.Note(subject="Task note")
        self.task.addNote(self.taskNote)

        self.attachment = attachment.FileAttachment("foobarfile")
        self.task.addAttachment(self.attachment)

        self.filename = "test.tsk"

        self.taskFile1.setFilename(self.filename)
        self.taskFile2.setFilename(self.filename)

        self.taskFile1.save()
        self.taskFile2.load()

    def createTaskFiles(self):
        """Crée les instances de TaskFile pour les tests multi-utilisateurs en initialisant deux instances de TaskFile, une pour le fichier de tâches principal et une pour un autre fichier de tâches, qui seront utilisées dans les tests pour vérifier que les modifications apportées dans un autre processus sont correctement suivies et reflétées dans le TaskFile actuel."""
        # pylint: disable-msg=W0201
        self.taskFile1 = persistence.TaskFile()
        self.taskFile2 = persistence.TaskFile()

    def tearDown(self):
        """Nettoie les ressources utilisées par les tests multi-utilisateurs en fermant et en arrêtant les instances de TaskFile, puis en supprimant les fichiers de tâches créés pendant les tests, avant d'appeler la méthode tearDown de la classe parente pour effectuer tout nettoyage supplémentaire nécessaire."""
        self.taskFile1.close()
        self.taskFile1.stop()
        self.taskFile2.close()
        self.taskFile2.stop()
        self.remove(self.filename)

    def remove(self, *filenames):
        """Supprime les fichiers spécifiés en vérifiant d'abord s'ils existent, puis en essayant de les supprimer jusqu'à trois fois en cas d'erreurs d'accès aléatoires, pour nettoyer les fichiers de tâches et de changements créés pendant les tests multi-utilisateurs."""
        for filename in filenames:
            tries = 0
            while os.path.exists(filename) and tries < 3:
                try:  # Don't fail on random 'Access denied' errors.
                    os.remove(filename)
                    break
                except WindowsError:
                    tries += 1

    def _assertIdInList(self, objects, id_):
        """Vérifie que l'ID spécifié est présent dans la liste d'objets en parcourant la liste d'objets et en comparant l'ID de chaque objet avec l'ID spécifié, et en échouant le test si aucun objet avec l'ID spécifié n'est trouvé, sinon en retournant l'objet correspondant à l'ID spécifié."""
        for obj in objects:
            if obj.id() == id_:
                break
        else:
            # self.fail("ID %s not found" % id_)
            self.fail(f"ID {id_} not found")
        return obj

    def _testCreateObjectInOther(self, class_, listName):
        """Vérifie que les nouvelles tâches, catégories ou notes créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle instance de la classe spécifiée (tâche, catégorie ou note) dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste correspondante du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre d'objets dans la liste correspondante du TaskFile de test principal a augmenté d'une unité pour refléter l'objet créé, et que l'ID de l'objet créé est présent dans la liste d'objets du TaskFile de test principal après le chargement des modifications."""
        # newObject = class_(subject="New %s" % class_.__name__)
        newObject = class_(subject=f"New {class_.__name__}")
        getattr(self.taskFile1, listName)().append(newObject)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 2)
        self._assertIdInList(
            getattr(self.taskFile2, listName)().rootItems(), newObject.id()
        )

    def testOtherCreatesCategory(self):
        """Vérifie que les nouvelles catégories créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la catégorie créée, et que l'ID de la catégorie créée est présent dans la liste des catégories du TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectInOther(category.Category, "categories")

    def testOtherCreatesTask(self):
        """Vérifie que les nouvelles tâches créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle tâche dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des tâches du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal a augmenté d'une unité pour refléter la tâche créée, et que l'ID de la tâche créée est présent dans la liste des tâches du TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectInOther(task.Task, "tasks")

    def testOtherCreatesNote(self):
        """Vérifie que les nouvelles notes créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de notes dans le TaskFile de test principal a augmenté d'une unité pour refléter la note créée, et que l'ID de la note créée est présent dans la liste des notes du TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectInOther(note.Note, "notes")

    def _testCreateChildInOther(self, listName):
        """Vérifie que les sous-tâches, sous-catégories ou sous-notes créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle instance de la classe correspondante (sous-tâche, sous-catégorie ou sous-note) en tant qu'enfant d'un élément existant dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste correspondante du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre d'objets dans la liste correspondante du TaskFile de test principal a augmenté d'une unité pour refléter l'objet créé, et que l'ID de l'objet créé est présent dans la liste d'objets du TaskFile de test principal après le chargement des modifications."""
        item = getattr(self.taskFile1, listName)().rootItems()[0]
        # subItem = item.newChild(subject="New sub%s" % item.__class__.__name__)
        subItem = item.newChild(subject=f"New sub{item.__class__.__name__}")
        getattr(self.taskFile1, listName)().append(subItem)
        item.addChild(subItem)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 2)
        otherItem = getattr(self.taskFile2, listName)().rootItems()[0]
        self.assertEqual(len(otherItem.children()), 1)
        self.assertEqual(otherItem.children()[0].id(), subItem.id())

    def testOtherCreatesSubcategory(self):
        """Vérifie que les sous-catégories créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle sous-catégorie en tant qu'enfant d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la sous-catégorie créée, et que l'ID de la sous-catégorie créée est présent dans la liste des catégories du TaskFile de test principal après le chargement des modifications."""
        self._testCreateChildInOther("categories")

    def testOtherCreatesSubtask(self):
        """Vérifie que les sous-tâches créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle sous-tâche en tant qu'enfant d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des tâches du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal a augmenté d'une unité pour refléter la sous-tâche créée, et que l'ID de la sous-tâche créée est présent dans la liste des tâches du TaskFile de test principal après le chargement des modifications."""
        self._testCreateChildInOther("tasks")

    def testOtherCreatesSubnote(self):
        """Vérifie que les sous-notes créées dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle sous-note en tant qu'enfant d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de notes dans le TaskFile de test principal a augmenté d'une unité pour refléter la sous-note créée, et que l'ID de la sous-note créée est présent dans la liste des notes du TaskFile de test principal après le chargement des modifications."""
        self._testCreateChildInOther("notes")

    def _testCreateObjectWithChildInOther(self, class_, listName):
        """Vérifie que les nouvelles tâches, catégories ou notes créées avec des sous-tâches, sous-catégories ou sous-notes dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle instance de la classe spécifiée (tâche, catégorie ou note) avec une sous-instance correspondante (sous-tâche, sous-catégorie ou sous-note) dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste correspondante du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre d'objets dans la liste correspondante du TaskFile de test principal a augmenté d'une unité pour refléter l'objet créé, que l'ID de l'objet créé est présent dans la liste d'objets du TaskFile de test principal après le chargement des modifications, et que l'ID de la sous-instance créée est présent dans la liste des enfants de l'objet créé dans le TaskFile de test principal après le chargement des modifications."""
        # item = class_(subject="New %s" % class_.__name__)
        item = class_(subject=f"New {class_.__name__}")
        # subItem = item.newChild(subject="New sub%s" % class_.__name__)
        subItem = item.newChild(subject=f"New sub{class_.__name__}")
        item.addChild(subItem)
        getattr(self.taskFile1, listName)().append(item)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 3)
        otherItem = self._assertIdInList(
            getattr(self.taskFile2, listName)().rootItems(), item.id()
        )
        self.assertEqual(len(otherItem.children()), 1)
        self.assertEqual(otherItem.children()[0].id(), subItem.id())

    def testOtherCreatesCategoryWithChild(self):
        """Vérifie que les nouvelles catégories créées avec des sous-catégories dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie avec une sous-catégorie correspondante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la catégorie créée, que l'ID de la catégorie créée est présent dans la liste des catégories du TaskFile de test principal après le chargement des modifications, et que l'ID de la sous-catégorie créée est présent dans la liste des enfants de la catégorie créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectWithChildInOther(category.Category, "categories")

    def testOtherCreatesTaskWithChild(self):
        """Vérifie que les nouvelles tâches créées avec des sous-tâches dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle tâche avec une sous-tâche correspondante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des tâches du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal a augmenté d'une unité pour refléter la tâche créée, que l'ID de la tâche créée est présent dans la liste des tâches du TaskFile de test principal après le chargement des modifications, et que l'ID de la sous-tâche créée est présent dans la liste des enfants de la tâche créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectWithChildInOther(task.Task, "tasks")

    def testOtherCreatesNoteWithChild(self):
        """Vérifie que les nouvelles notes créées avec des sous-notes dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note avec une sous-note correspondante dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de notes dans le TaskFile de test principal a augmenté d'une unité pour refléter la note créée, que l'ID de la note créée est présent dans la liste des notes du TaskFile de test principal après le chargement des modifications, et que l'ID de la sous-note créée est présent dans la liste des enfants de la note créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectWithChildInOther(note.Note, "notes")

    def _testCreateObjectAndReparentExisting(self, listName):
        """Vérifie que les nouvelles tâches, catégories ou notes créées dans un autre TaskFile peuvent être réorganisées en tant que parents d'éléments existants dans le TaskFile actuel en créant une nouvelle instance de la classe correspondante (tâche, catégorie ou note) dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste correspondante du TaskFile de test principal, en réorganisant un élément existant de cette liste pour qu'il devienne un enfant de l'élément créé, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre d'objets dans la liste correspondante du TaskFile de test principal a augmenté d'une unité pour refléter l'objet créé, que l'ID de l'objet créé est présent dans la liste d'objets du TaskFile de test principal après le chargement des modifications, et que l'ID de l'élément existant réorganisé est présent dans la liste des enfants de l'objet créé dans le TaskFile de test principal après le chargement des modifications."""
        item = getattr(self.taskFile1, listName)().rootItems()[0]
        # newItem = item.__class__(subject="New %s" % item.__class__.__name__)
        newItem = item.__class__(subject=f"New {item.__class__.__name__}")
        getattr(self.taskFile1, listName)().append(newItem)
        newItem.addChild(item)
        item.setParent(newItem)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 2)
        for otherItem in getattr(self.taskFile2, listName)().rootItems():
            if otherItem.id() == newItem.id():
                break
        else:
            self.fail()
        self.assertEqual(len(otherItem.children()), 1)
        self.assertEqual(otherItem.children()[0].id(), item.id())

    def testOtherCreatesCategoryAndReparentsExisting(self):
        """Vérifie que les nouvelles catégories créées dans un autre TaskFile peuvent être réorganisées en tant que parents d'éléments existants dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en réorganisant une catégorie existante pour qu'elle devienne un enfant de la catégorie créée, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de catégories dans le TaskFile de test principal a augmenté d'une unité pour refléter la catégorie créée, que l'ID de la catégorie créée est présent dans la liste des catégories du TaskFile de test principal après le chargement des modifications, et que l'ID de la catégorie existante réorganisée est présent dans la liste des enfants de la catégorie créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectAndReparentExisting("categories")

    def testOtherCreatesTaskAndReparentsExisting(self):
        """Vérifie que les nouvelles tâches créées dans un autre TaskFile peuvent être réorganisées en tant que parents d'éléments existants dans le TaskFile actuel en créant une nouvelle tâche dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des tâches du TaskFile de test principal, en réorganisant une tâche existante pour qu'elle devienne un enfant de la tâche créée, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de tâches dans le TaskFile de test principal a augmenté d'une unité pour refléter la tâche créée, que l'ID de la tâche créée est présent dans la liste des tâches du TaskFile de test principal après le chargement des modifications, et que l'ID de la tâche existante réorganisée est présent dans la liste des enfants de la tâche créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectAndReparentExisting("tasks")

    def testOtherCreatesNoteAndReparentsExisting(self):
        """Vérifie que les nouvelles notes créées dans un autre TaskFile peuvent être réorganisées en tant que parents d'éléments existants dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en réorganisant une note existante pour qu'elle devienne un enfant de la note créée, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nombre de notes dans le TaskFile de test principal a augmenté d'une unité pour refléter la note créée, que l'ID de la note créée est présent dans la liste des notes du TaskFile de test principal après le chargement des modifications, et que l'ID de la note existante réorganisée est présent dans la liste des enfants de la note créée dans le TaskFile de test principal après le chargement des modifications."""
        self._testCreateObjectAndReparentExisting("notes")

    def _testChangeAttribute(self, name, value, listName):
        """Vérifie que les modifications apportées à un attribut d'une tâche, catégorie ou note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'attribut spécifié d'un élément existant dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la valeur de l'attribut modifié pour cet élément dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        obj = getattr(self.taskFile1, listName)().rootItems()[0]
        getattr(obj, "set" + name[0].upper() + name[1:])(value)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            getattr(
                getattr(self.taskFile2, listName)().rootItems()[0], name
            )(),
            value,
        )

    def _testExpand(self, listName):
        """Vérifie que les modifications d'expansion d'une tâche, catégorie ou note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'état d'expansion d'un élément existant dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'état d'expansion de cet élément dans le TaskFile de test principal correspond à l'état modifié après le chargement des modifications."""
        obj = getattr(self.taskFile1, listName)().rootItems()[0]
        obj.expand()
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.failUnless(
            getattr(self.taskFile2, listName)().rootItems()[0].isExpanded()
        )

    def testChangeCategoryName(self):
        """Vérifie que les modifications apportées au nom d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le nom d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le nom de cette catégorie dans le TaskFile de test principal correspond au nouveau nom après le chargement des modifications."""
        self._testChangeAttribute("subject", "New category name", "categories")

    def testChangeCategoryDescription(self):
        """Vérifie que les modifications apportées à la description d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la description d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la description de cette catégorie dans le TaskFile de test principal correspond à la nouvelle description après le chargement des modifications."""
        self._testChangeAttribute(
            "description", "New category description", "categories"
        )

    def testExpandCategory(self):
        """Vérifie que les modifications d'expansion d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'état d'expansion d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'état d'expansion de cette catégorie dans le TaskFile de test principal correspond à l'état modifié après le chargement des modifications."""
        self._testExpand("categories")

    def testChangeTaskSubject(self):
        """Vérifie que les modifications apportées au sujet d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le sujet d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le sujet de cette tâche dans le TaskFile de test principal correspond au nouveau sujet après le chargement des modifications."""
        self._testChangeAttribute("subject", "New task subject", "tasks")

    def testChangeTaskDescription(self):
        """Vérifie que les modifications apportées à la description d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la description d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la description de cette tâche dans le TaskFile de test principal correspond à la nouvelle description après le chargement des modifications."""
        self._testChangeAttribute(
            "description", "New task description", "tasks"
        )

    def testExpandTask(self):
        """Vérifie que les modifications d'expansion d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'état d'expansion d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'état d'expansion de cette tâche dans le TaskFile de test principal correspond à l'état modifié après le chargement des modifications."""
        self._testExpand("tasks")

    def testChangeNoteSubject(self):
        """Vérifie que les modifications apportées au sujet d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le sujet d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le sujet de cette note dans le TaskFile de test principal correspond au nouveau sujet après le chargement des modifications."""
        self._testChangeAttribute("subject", "New note subject", "notes")

    def testChangeNoteDescription(self):
        """Vérifie que les modifications apportées à la description d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la description d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la description de cette note dans le TaskFile de test principal correspond à la nouvelle description après le chargement des modifications."""
        self._testChangeAttribute(
            "description", "New note description", "notes"
        )

    def testChangeTaskStartDateTime(self):
        """Vérifie que les modifications apportées à la date et l'heure de début prévues d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la date et l'heure de début prévues d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la date et l'heure de début prévues de cette tâche dans le TaskFile de test principal correspondent à la nouvelle date et heure après le chargement des modifications."""
        self._testChangeAttribute(
            "plannedStartDateTime", date.DateTime(2011, 6, 15), "tasks"
        )

    def testChangeTaskDueDateTime(self):
        """Vérifie que les modifications apportées à la date et l'heure d'échéance d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la date et l'heure d'échéance d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la date et l'heure d'échéance de cette tâche dans le TaskFile de test principal correspondent à la nouvelle date et heure après le chargement des modifications."""
        self._testChangeAttribute(
            "dueDateTime", date.DateTime(2011, 7, 16), "tasks"
        )

    def testChangeTaskCompletionDateTime(self):
        """Vérifie que les modifications apportées à la date et l'heure d'achèvement d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la date et l'heure d'achèvement d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la date et l'heure d'achèvement de cette tâche dans le TaskFile de test principal correspondent à la nouvelle date et heure après le chargement des modifications."""
        self._testChangeAttribute(
            "completionDateTime", date.DateTime(2011, 2, 1), "tasks"
        )

    def testChangeTaskPrecentageComplete(self):
        """Vérifie que les modifications apportées au pourcentage d'achèvement d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le pourcentage d'achèvement d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le pourcentage d'achèvement de cette tâche dans le TaskFile de test principal correspond au nouveau pourcentage après le chargement des modifications."""
        self._testChangeAttribute("percentageComplete", 42, "tasks")

    def testChangeTaskRecurrence(self):
        """Vérifie que les modifications apportées à la récurrence d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la récurrence d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la récurrence de cette tâche dans le TaskFile de test principal correspond à la nouvelle récurrence après le chargement des modifications."""
        self._testChangeAttribute(
            "recurrence", date.Recurrence("daily", 3), "tasks"
        )

    def testChangeTaskReminder(self):
        """Vérifie que les modifications apportées au rappel d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le rappel d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le rappel de cette tâche dans le TaskFile de test principal correspond au nouveau rappel après le chargement des modifications."""
        self._testChangeAttribute(
            "reminder", date.DateTime(2999, 2, 1), "tasks"
        )

    def testChangeTaskBudget(self):
        """Vérifie que les modifications apportées au budget d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le budget d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le budget de cette tâche dans le TaskFile de test principal correspond au nouveau budget après le chargement des modifications."""
        self._testChangeAttribute(
            "budget", date.TimeDelta(seconds=60), "tasks"
        )

    def testChangeTaskPriority(self):
        """Vérifie que les modifications apportées à la priorité d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la priorité d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la priorité de cette tâche dans le TaskFile de test principal correspond à la nouvelle priorité après le chargement des modifications."""
        self._testChangeAttribute("priority", 42, "tasks")

    def testChangeTaskHourlyFee(self):
        """Vérifie que les modifications apportées au tarif horaire d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le tarif horaire d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le tarif horaire de cette tâche dans le TaskFile de test principal correspond au nouveau tarif horaire après le chargement des modifications."""
        self._testChangeAttribute("hourlyFee", 42, "tasks")

    def testChangeTaskFixedFee(self):
        """Vérifie que les modifications apportées au tarif fixe d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant le tarif fixe d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que le tarif fixe de cette tâche dans le TaskFile de test principal correspond au nouveau tarif fixe après le chargement des modifications."""
        self._testChangeAttribute("fixedFee", 42, "tasks")

    def testChangeTaskShouldMarkCompletedWhenAllChildrenCompleted(self):
        """Vérifie que les modifications apportées à l'attribut "shouldMarkCompletedWhenAllChildrenCompleted" d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant cet attribut pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la valeur de cet attribut pour cette tâche dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        self._testChangeAttribute(
            "shouldMarkCompletedWhenAllChildrenCompleted", False, "tasks"
        )

    def testExpandNote(self):
        """Vérifie que les modifications d'expansion d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'état d'expansion d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'état d'expansion de cette note dans le TaskFile de test principal correspond à l'état modifié après le chargement des modifications."""
        self._testExpand("notes")

    def _testChangeAppearance(
        self, listName, attrName, initialValue, newValue
    ):
        """Vérifie que les modifications apportées à l'apparence d'une tâche, catégorie ou note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'attribut d'apparence spécifié (couleur de premier plan, couleur de fond, icône ou icône sélectionnée) d'un élément existant dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la valeur de cet attribut d'apparence pour cet élément dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        setName = "set" + attrName[0].upper() + attrName[1:]
        obj = getattr(self.taskFile1, listName)().rootItems()[0]
        newObj = getattr(self.taskFile2, listName)().rootItems()[0]
        getattr(obj, setName)(initialValue)
        getattr(newObj, setName)(initialValue)
        self.taskFile1.monitor().resetAllChanges()
        self.taskFile2.monitor().resetAllChanges()
        getattr(obj, setName)(newValue)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(getattr(newObj, attrName)(), newValue)

    def testChangeCategoryForeground(self):
        """Vérifie que les modifications apportées à la couleur de premier plan d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la couleur de premier plan d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la couleur de premier plan de cette catégorie dans le TaskFile de test principal correspond à la nouvelle couleur après le chargement des modifications."""
        self._testChangeAppearance(
            "categories", "foregroundColor", (128, 128, 128), (255, 255, 0)
        )

    def testChangeCategoryBackground(self):
        """Vérifie que les modifications apportées à la couleur de fond d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la couleur de fond d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la couleur de fond de cette catégorie dans le TaskFile de test principal correspond à la nouvelle couleur après le chargement des modifications."""
        self._testChangeAppearance(
            "categories", "backgroundColor", (128, 128, 128), (255, 255, 0)
        )

    def testChangeCategoryIcon(self):
        """Vérifie que les modifications apportées à l'icône d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône de cette catégorie dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance(
            "categories", "icon", "initialIcon", "finalIcon"
        )

    def testChangeCategorySelectedIcon(self):
        """Vérifie que les modifications apportées à l'icône sélectionnée d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône sélectionnée d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône sélectionnée de cette catégorie dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance(
            "categories", "selectedIcon", "initialIcon", "finalIcon"
        )

    def testChangeNoteForeground(self):
        """Vérifie que les modifications apportées à la couleur de premier plan d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la couleur de premier plan d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la couleur de premier plan de cette note dans le TaskFile de test principal correspond à la nouvelle couleur après le chargement des modifications."""
        self._testChangeAppearance(
            "notes", "foregroundColor", (128, 128, 128), (255, 255, 0)
        )

    def testChangeNoteBackground(self):
        """Vérifie que les modifications apportées à la couleur de fond d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la couleur de fond d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la couleur de fond de cette note dans le TaskFile de test principal correspond à la nouvelle couleur après le chargement des modifications."""
        self._testChangeAppearance(
            "notes", "backgroundColor", (128, 128, 128), (255, 255, 0)
        )

    def testChangeNoteIcon(self):
        """Vérifie que les modifications apportées à l'icône d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône de cette note dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance("notes", "icon", "initialIcon", "finalIcon")

    def testChangeNoteSelectedIcon(self):
        """Vérifie que les modifications apportées à l'icône sélectionnée d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône sélectionnée d'une note existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône sélectionnée de cette note dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance(
            "notes", "selectedIcon", "initialIcon", "finalIcon"
        )

    def testChangeTaskBackground(self):
        """Vérifie que les modifications apportées à la couleur de fond d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant la couleur de fond d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la couleur de fond de cette tâche dans le TaskFile de test principal correspond à la nouvelle couleur après le chargement des modifications."""
        self._testChangeAppearance(
            "tasks", "backgroundColor", (128, 128, 128), (255, 255, 0)
        )

    def testChangeTaskIcon(self):
        """Vérifie que les modifications apportées à l'icône d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône de cette tâche dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance("tasks", "icon", "initialIcon", "finalIcon")

    def testChangeTaskSelectedIcon(self):
        """Vérifie que les modifications apportées à l'icône sélectionnée d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'icône sélectionnée d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'icône sélectionnée de cette tâche dans le TaskFile de test principal correspond à la nouvelle icône après le chargement des modifications."""
        self._testChangeAppearance(
            "tasks", "selectedIcon", "initialIcon", "finalIcon"
        )

    def testChangeExclusiveSubcategories(self):
        """Vérifie que les modifications apportées à l'exclusivité des sous-catégories d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant l'exclusivité des sous-catégories d'une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que l'exclusivité des sous-catégories de cette catégorie dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        self.category.makeSubcategoriesExclusive(True)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assert_(
            self.taskFile2.categories()
            .rootItems()[0]
            .hasExclusiveSubcategories()
        )

    def _testAddObjectCategory(self, listName):
        """Vérifie que les modifications apportées à l'ajout d'une catégorie à une tâche ou une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant cette catégorie à une tâche ou une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche ou la note correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la catégorie créée."""
        obj = getattr(self.taskFile1, listName)().rootItems()[0]
        obj.addCategory(self.category)
        self.category.addCategorizable(obj)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        newObj = getattr(self.taskFile2, listName)().rootItems()[0]
        self.assertEqual(len(newObj.categories()), 1)
        self.assertEqual(newObj.categories().pop().id(), self.category.id())

    def testAddNoteCategory(self):
        """Vérifie que les modifications apportées à l'ajout d'une catégorie à une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant cette catégorie à une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la note correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la catégorie créée."""
        self._testAddObjectCategory("notes")

    def testAddTaskCategory(self):
        """Vérifie que les modifications apportées à l'ajout d'une catégorie à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant cette catégorie à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la catégorie créée."""
        self._testAddObjectCategory("tasks")

    def _testChangeObjectCategory(self, listName):
        """Vérifie que les modifications apportées au changement de catégorie d'une tâche ou d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant une catégorie existante à une tâche ou une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant la catégorie ajoutée précédemment de cette tâche ou note, en ajoutant la nouvelle catégorie créée à cette tâche ou note, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche ou la note correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la nouvelle catégorie créée."""
        self.category2 = category.Category(subject="Other category")
        self.taskFile1.categories().append(self.category2)
        obj = getattr(self.taskFile1, listName)().rootItems()[0]
        obj.addCategory(self.category)
        self.category.addCategorizable(obj)
        self.taskFile1.save()
        self.taskFile2.save()
        # Load => CategoryList => addCategory()...
        self.taskFile1.monitor().resetAllChanges()

        self.category.removeCategorizable(obj)
        obj.removeCategory(self.category)
        self.category2.addCategorizable(obj)
        obj.addCategory(self.category2)

        self.taskFile1.save()
        self.taskFile2.monitor().resetAllChanges()
        self.doSave(self.taskFile2)

        newObj = getattr(self.taskFile2, listName)().rootItems()[0]
        self.assertEqual(len(newObj.categories()), 1)
        self.assertEqual(newObj.categories().pop().id(), self.category2.id())

    def testChangeNoteCategory(self):
        """Vérifie que les modifications apportées au changement de catégorie d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant une catégorie existante à une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant la catégorie ajoutée précédemment de cette note, en ajoutant la nouvelle catégorie créée à cette note, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la note correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la nouvelle catégorie créée."""
        self._testChangeObjectCategory("notes")

    def testChangeTaskCategory(self):
        """Vérifie que les modifications apportées au changement de catégorie d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle catégorie dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des catégories du TaskFile de test principal, en ajoutant une catégorie existante à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant la catégorie ajoutée précédemment de cette tâche, en ajoutant la nouvelle catégorie créée à cette tâche, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la nouvelle catégorie créée."""
        self._testChangeObjectCategory("tasks")

    def _testDeleteObject(self, listName):
        """Vérifie que les modifications apportées à la suppression d'une tâche, catégorie ou note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant un élément existant dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cet élément n'existe plus dans le TaskFile de test principal après le chargement des modifications."""
        item = getattr(self.taskFile1, listName)().rootItems()[0]
        getattr(self.taskFile1, listName)().remove(item)
        self.taskFile1.save()
        self.taskFile2.monitor().setChanges(item.id(), set())
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile1, listName)()), 0)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 0)

    def _testDeleteModifiedLocalObject(self, listName):
        """Vérifie que les modifications apportées à la suppression d'une tâche, catégorie ou note modifiée localement dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant un élément existant dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cet élément, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cet élément n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cet élément avant sa suppression ne sont pas présentes dans le TaskFile de test principal."""
        item = getattr(self.taskFile1, listName)().rootItems()[0]
        getattr(self.taskFile1, listName)().remove(item)
        self.taskFile1.save()
        getattr(self.taskFile2, listName)().rootItems()[0].setSubject(
            "New subject."
        )
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 1)

    def _testDeleteModifiedRemoteObject(self, listName):
        """Vérifie que les modifications apportées à la suppression d'une tâche, catégorie ou note modifiée dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant un élément existant dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cet élément, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cet élément n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cet élément avant sa suppression sont présentes dans le TaskFile de test principal."""
        getattr(self.taskFile1, listName)().rootItems()[0].setSubject(
            "New subject."
        )
        self.taskFile1.save()
        item = getattr(self.taskFile2, listName)().rootItems()[0]
        getattr(self.taskFile2, listName)().remove(item)
        self.doSave(self.taskFile2)
        self.assertEqual(len(getattr(self.taskFile2, listName)()), 1)
        self.assertEqual(
            getattr(self.taskFile2, listName)().rootItems()[0].subject(),
            "New subject.",
        )

    def testDeleteCategory(self):
        """Vérifie que les modifications apportées à la suppression d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant une catégorie existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cette catégorie n'existe plus dans le TaskFile de test principal après le chargement des modifications."""
        self._testDeleteObject("categories")

    def testDeleteNote(self):
        self._testDeleteObject("notes")

    def testDeleteTask(self):
        self._testDeleteObject("tasks")

    def testDeleteModifiedLocalCategory(self):
        """Vérifie que les modifications apportées à la suppression d'une catégorie modifiée localement dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant une catégorie existante dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cette catégorie, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cette catégorie n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cette catégorie avant sa suppression ne sont pas présentes dans le TaskFile de test principal."""
        self._testDeleteModifiedLocalObject("categories")

    def testDeleteModifiedLocalNote(self):
        """Vérifie que les modifications apportées à la suppression d'une note modifiée localement dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant une note existante dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cette note, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cette note n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cette note avant sa suppression ne sont pas présentes dans le TaskFile de test principal."""
        self._testDeleteModifiedLocalObject("notes")

    def testDeleteModifiedLocalTask(self):
        self._testDeleteModifiedLocalObject("tasks")

    def testDeleteModifiedRemoteCategory(self):
        """Vérifie que les modifications apportées à la suppression d'une catégorie modifiée dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant une catégorie existante dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cette catégorie, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cette catégorie n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cette catégorie avant sa suppression sont présentes dans le TaskFile de test principal."""
        self._testDeleteModifiedRemoteObject("categories")

    def testDeleteModifiedRemoteNote(self):
        """Vérifie que les modifications apportées à la suppression d'une note modifiée dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en supprimant une note existante dans le TaskFile utilisé pour le suivi des modifications après avoir modifié cette note, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que cette note n'existe plus dans le TaskFile de test principal après le chargement des modifications, et que les modifications apportées à cette note avant sa suppression sont présentes dans le TaskFile de test principal."""
        self._testDeleteModifiedRemoteObject("notes")

    def testDeleteModifiedRemoteTask(self):
        self._testDeleteModifiedRemoteObject("tasks")

    def _testAddNoteToObject(self, listName):
        """Vérifie que les modifications apportées à l'ajout d'une note à une tâche ou une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une tâche ou une catégorie existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche ou la catégorie correspondante dans le TaskFile de test principal a exactement une note après le chargement des modifications, et que l'ID de cette note correspond à l'ID de la note créée."""
        newNote = note.Note(subject="Other note")
        getattr(self.taskFile1, listName)().rootItems()[0].addNote(newNote)
        noteCount = len(
            getattr(self.taskFile1, listName)().rootItems()[0].notes()
        )
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(getattr(self.taskFile2, listName)().rootItems()[0].notes()),
            noteCount,
        )

    def testAddNoteToTask(self):
        """Vérifie que les modifications apportées à l'ajout d'une note à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement une note après le chargement des modifications, et que l'ID de cette note correspond à l'ID de la note créée."""
        self._testAddNoteToObject("tasks")

    def testAddNoteToCategory(self):
        self._testAddNoteToObject("categories")

    def testAddNoteToAttachment(self):
        """Vérifie que les modifications apportées à l'ajout d'une note à une pièce jointe dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une pièce jointe existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la pièce jointe correspondante dans le TaskFile de test principal a exactement une note après le chargement des modifications, et que l'ID de cette note correspond à l'ID de la note créée."""
        newNote = note.Note(subject="Attachment note")
        self.attachment.addNote(newNote)
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(
                self.taskFile2.tasks().rootItems()[0].attachments()[0].notes()
            ),
            1,
        )

    def _testAddAttachmentToObject(self, listName):
        """Vérifie que les modifications apportées à l'ajout d'une pièce jointe à une tâche, une catégorie ou une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle pièce jointe dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des pièces jointes du TaskFile de test principal, en ajoutant cette pièce jointe à une tâche, une catégorie ou une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche, la catégorie ou la note correspondante dans le TaskFile de test principal a exactement une pièce jointe après le chargement des modifications, et que l'ID de cette pièce jointe correspond à l'ID de la pièce jointe créée."""
        newAttachment = attachment.FileAttachment("Other attachment")
        getattr(self.taskFile1, listName)().rootItems()[0].addAttachment(
            newAttachment
        )
        attachmentCount = len(
            getattr(self.taskFile1, listName)().rootItems()[0].attachments()
        )
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(
                getattr(self.taskFile2, listName)()
                .rootItems()[0]
                .attachments()
            ),
            attachmentCount,
        )

    def testAddAttachmentToTask(self):
        """Vérifie que les modifications apportées à l'ajout d'une pièce jointe à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle pièce jointe dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des pièces jointes du TaskFile de test principal, en ajoutant cette pièce jointe à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement une pièce jointe après le chargement des modifications, et que l'ID de cette pièce jointe correspond à l'ID de la pièce jointe créée."""
        self._testAddAttachmentToObject("tasks")

    def testAddAttachmentToCategory(self):
        """Vérifie que les modifications apportées à l'ajout d'une pièce jointe à une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle pièce jointe dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des pièces jointes du TaskFile de test principal, en ajoutant cette pièce jointe à une catégorie existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la catégorie correspondante dans le TaskFile de test principal a exactement une pièce jointe après le chargement des modifications, et que l'ID de cette pièce jointe correspond à l'ID de la pièce jointe créée."""
        self._testAddAttachmentToObject("categories")

    def testAddAttachmentToNote(self):
        self._testAddAttachmentToObject("notes")

    def _testRemoveNoteFromObject(self, listName):
        """Vérifie que les modifications apportées à la suppression d'une note d'une tâche ou d'une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une tâche ou une catégorie existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette note de cette tâche ou catégorie, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche ou la catégorie correspondante dans le TaskFile de test principal n'a plus de note après le chargement des modifications."""
        newNote = note.Note(subject="Other note")
        noteCount = len(
            getattr(self.taskFile1, listName)().rootItems()[0].notes()
        )
        getattr(self.taskFile1, listName)().rootItems()[0].addNote(newNote)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.taskFile2.save()

        getattr(self.taskFile1, listName)().rootItems()[0].removeNote(newNote)
        self.taskFile2.monitor().setChanges(newNote.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(getattr(self.taskFile2, listName)().rootItems()[0].notes()),
            noteCount,
        )

    def testRemoveNoteFromTask(self):
        """Vérifie que les modifications apportées à la suppression d'une note d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette note de cette tâche, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal n'a plus de note après le chargement des modifications."""
        self._testRemoveNoteFromObject("tasks")

    def testRemoveNoteFromCategory(self):
        self._testRemoveNoteFromObject("categories")

    def testRemoveNoteFromAttachment(self):
        """Vérifie que les modifications apportées à la suppression d'une note d'une pièce jointe dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des notes du TaskFile de test principal, en ajoutant cette note à une pièce jointe existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette note de cette pièce jointe, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la pièce jointe correspondante dans le TaskFile de test principal n'a plus de note après le chargement des modifications."""
        newNote = note.Note(subject="Attachment note")
        self.attachment.addNote(newNote)
        self.taskFile1.save()
        self.taskFile2.save()

        self.taskFile1.tasks().rootItems()[0].attachments()[0].removeNote(
            newNote
        )
        self.taskFile2.monitor().setChanges(newNote.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(
                self.taskFile2.tasks().rootItems()[0].attachments()[0].notes()
            ),
            0,
        )

    def _testRemoveAttachmentFromObject(self, listName):
        """Vérifie que les modifications apportées à la suppression d'une pièce jointe d'une tâche, d'une catégorie ou d'une note dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle pièce jointe dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des pièces jointes du TaskFile de test principal, en ajoutant cette pièce jointe à une tâche, une catégorie ou une note existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette pièce jointe de cette tâche, catégorie ou note, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche, la catégorie ou la note correspondante dans le TaskFile de test principal n'a plus de pièce jointe après le chargement des modifications."""
        newAttachment = attachment.FileAttachment("Other attachment")
        attachmentCount = len(
            getattr(self.taskFile1, listName)().rootItems()[0].attachments()
        )
        getattr(self.taskFile1, listName)().rootItems()[0].addAttachment(
            newAttachment
        )
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.taskFile2.save()

        getattr(self.taskFile1, listName)().rootItems()[0].removeAttachment(
            newAttachment
        )
        self.taskFile2.monitor().setChanges(newAttachment.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(
                getattr(self.taskFile2, listName)()
                .rootItems()[0]
                .attachments()
            ),
            attachmentCount,
        )

    def testRemoveAttachmentFromTask(self):
        """Vérifie que les modifications apportées à la suppression d'une pièce jointe d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle pièce jointe dans le TaskFile utilisé pour le suivi des modifications, en l'ajoutant à la liste des pièces jointes du TaskFile de test principal, en ajoutant cette pièce jointe à une tâche existante dans le TaskFile de test principal, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette pièce jointe de cette tâche, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal n'a plus de pièce jointe après le chargement des modifications."""
        self._testRemoveAttachmentFromObject("tasks")

    def testRemoveAttachmentFromCategory(self):
        self._testRemoveAttachmentFromObject("categories")

    def testRemoveAttachmentFromNote(self):
        self._testRemoveAttachmentFromObject("notes")

    def testChangeNoteBelongingToTask(self):
        """Vérifie que les modifications apportées à une note appartenant à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant une propriété d'une note existante appartenant à une tâche dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la même propriété de cette note dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        self.taskNote.setSubject("New subject")
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            self.taskFile2.tasks().rootItems()[0].notes()[0].subject(),
            "New subject",
        )

    def testChangeAttachmentBelongingToTask(self):
        """Vérifie que les modifications apportées à une pièce jointe appartenant à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en modifiant une propriété d'une pièce jointe existante appartenant à une tâche dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la même propriété de cette pièce jointe dans le TaskFile de test principal correspond à la nouvelle valeur après le chargement des modifications."""
        self.attachment.setLocation("new location")
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            self.taskFile2.tasks().rootItems()[0].attachments()[0].location(),
            "new location",
        )

    def testAddChildToNoteBelongingToTask(self):
        """Vérifie que les modifications apportées à l'ajout d'une note enfant à une note appartenant à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note enfant, en l'ajoutant à une note existante appartenant à une tâche dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la note parent correspondante dans le TaskFile de test principal a exactement une note enfant après le chargement des modifications, et que l'ID de cette note enfant correspond à l'ID de la note enfant créée."""
        subNote = self.taskNote.newChild(subject="Child note")
        self.taskNote.addChild(subNote)
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(self.taskFile2.tasks().rootItems()[0].notes()[0].children()), 1
        )

    def testRemoveChildToNoteBelongingToTask(self):
        """Vérifie que les modifications apportées à la suppression d'une note enfant d'une note appartenant à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle note enfant, en l'ajoutant à une note existante appartenant à une tâche dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette note enfant de cette note parent, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la note parent correspondante dans le TaskFile de test principal n'a plus de note enfant après le chargement des modifications."""
        subNote = self.taskNote.newChild(subject="Child note")
        self.taskNote.addChild(subNote)
        self.taskFile1.save()
        self.taskFile2.save()

        self.taskNote.removeChild(subNote)
        self.taskFile2.monitor().setChanges(subNote.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(self.taskFile2.tasks().rootItems()[0].notes()[0].children()), 0
        )

    def testAddCategorizedNoteBelongingToOtherCategory(self):
        """Vérifie que les modifications apportées à l'ajout d'une note catégorisée appartenant à une catégorie dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant deux catégories, en ajoutant une note à la première catégorie, en ajoutant cette première catégorie à une note existante dans le TaskFile utilisé pour le suivi des modifications, en ajoutant la note à la deuxième catégorie, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la note correspondante dans le TaskFile de test principal a exactement une catégorie après le chargement des modifications, et que l'ID de cette catégorie correspond à l'ID de la deuxième catégorie créée."""
        # Categories should be handled in priority...
        cat1 = category.Category(subject="Cat #1")
        cat2 = category.Category(subject="Cat #2")
        newNote = note.Note(subject="Note")
        cat1.addNote(newNote)
        newNote.addCategory(cat2)
        cat2.addCategorizable(newNote)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        try:
            self.doSave(self.taskFile2)
        except Exception as e:
            self.fail(str(e))

    def testAddEffortToTask(self):
        """Vérifie que les modifications apportées à l'ajout d'un effort à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant un nouvel effort pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement un effort après le chargement des modifications, et que l'ID de cet effort correspond à l'ID de l'effort créé."""
        newEffort = effort.Effort(
            self.task, date.DateTime(2011, 5, 1), date.DateTime(2011, 6, 1)
        )
        self.task.addEffort(newEffort)
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            newEffort.id(),
            self.taskFile2.tasks().rootItems()[0].efforts()[0].id(),
        )

    def testRemoveEffortFromTask(self):
        """Vérifie que les modifications apportées à la suppression d'un effort d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant un nouvel effort pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cet effort de cette tâche, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal n'a plus d'effort après le chargement des modifications."""
        newEffort = effort.Effort(
            self.task, date.DateTime(2011, 5, 1), date.DateTime(2011, 6, 1)
        )
        self.task.addEffort(newEffort)
        self.taskFile1.save()
        self.taskFile2.save()
        self.task.removeEffort(newEffort)
        self.taskFile2.monitor().setChanges(newEffort.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            len(self.taskFile2.tasks().rootItems()[0].efforts()), 0
        )

    def testChangeEffortTask(self):
        """Vérifie que les modifications apportées au changement de tâche d'un effort dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle tâche, en l'ajoutant à la liste des tâches du TaskFile de test principal, en créant un nouvel effort pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en changeant la tâche de cet effort pour la nouvelle tâche créée, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche associée à cet effort dans le TaskFile de test principal correspond à la nouvelle tâche après le chargement des modifications, et que l'ID de cette tâche correspond à l'ID de la nouvelle tâche créée."""
        newTask = task.Task(subject="Other task")
        self.taskFile1.tasks().append(newTask)
        newEffort = effort.Effort(
            self.task, date.DateTime(2011, 5, 1), date.DateTime(2011, 6, 1)
        )
        self.task.addEffort(newEffort)
        self.taskFile1.save()
        self.taskFile2.save()
        newEffort.setTask(newTask)
        self.taskFile2.monitor().setChanges(newEffort.id(), set())
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        for theTask in self.taskFile2.tasks():
            if theTask.id() == newTask.id():
                self.assertEqual(len(theTask.efforts()), 1)
                break
        else:
            self.fail()

    def testChangeEffortStart(self):
        """Vérifie que les modifications apportées au changement de date de début d'un effort dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant un nouvel effort pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en changeant la date de début de cet effort pour une nouvelle date, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la date de début de cet effort dans le TaskFile de test principal correspond à la nouvelle date après le chargement des modifications."""
        newEffort = effort.Effort(
            self.task, date.DateTime(2011, 5, 1), date.DateTime(2011, 6, 1)
        )
        self.task.addEffort(newEffort)
        self.taskFile1.save()
        self.taskFile2.save()
        # This is needed because the setTask in sync() generates a DEL event
        self.taskFile1.monitor().setChanges(newEffort.id(), set())
        newDate = date.DateTime(2010, 6, 1)
        newEffort.setStart(newDate)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            self.taskFile2.tasks().rootItems()[0].efforts()[0].getStart(),
            newDate,
        )

    def testChangeEffortStop(self):
        """Vérifie que les modifications apportées au changement de date de fin d'un effort dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant un nouvel effort pour une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en changeant la date de fin de cet effort pour une nouvelle date, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la date de fin de cet effort dans le TaskFile de test principal correspond à la nouvelle date après le chargement des modifications."""
        newEffort = effort.Effort(
            self.task, date.DateTime(2011, 5, 1), date.DateTime(2011, 6, 1)
        )
        self.task.addEffort(newEffort)
        self.taskFile1.save()
        self.taskFile2.save()
        # This is needed because the setTask in sync() generates a DEL event
        self.taskFile1.monitor().setChanges(newEffort.id(), set())
        newDate = date.DateTime(2012, 6, 1)
        newEffort.setStop(newDate)
        self.taskFile2.monitor().resetAllChanges()
        self.taskFile1.save()
        self.doSave(self.taskFile2)
        self.assertEqual(
            self.taskFile2.tasks().rootItems()[0].efforts()[0].getStop(),
            newDate,
        )

    def testAddPrerequisite(self):
        """Vérifie que les modifications apportées à l'ajout d'une tâche préalable à une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle tâche préalable, en l'ajoutant à la liste des tâches du TaskFile de test principal, en ajoutant cette tâche préalable à la liste des tâches préalables d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal a exactement une tâche préalable après le chargement des modifications, et que l'ID de cette tâche préalable correspond à l'ID de la tâche préalable créée."""
        newTask = task.Task(subject="Prereq")
        self.taskFile1.tasks().append(newTask)
        self.taskFile2.save()
        self.task.addPrerequisites([newTask])
        self.taskFile2.load()
        self.taskFile1.save()
        self.taskFile2.monitor().resetAllChanges()
        self.doSave(self.taskFile2)

        for tsk in self.taskFile2.tasks():
            if tsk.id() == self.task.id():
                self.assertEqual(len(tsk.prerequisites()), 1)
                self.assertEqual(
                    list(tsk.prerequisites())[0].id(), newTask.id()
                )
                break
        else:
            self.fail()

    def testRemovePrerequisite(self):
        """Vérifie que les modifications apportées à la suppression d'une tâche préalable d'une tâche dans un autre TaskFile sont correctement suivies et reflétées dans le TaskFile actuel en créant une nouvelle tâche préalable, en l'ajoutant à la liste des tâches du TaskFile de test principal, en ajoutant cette tâche préalable à la liste des tâches préalables d'une tâche existante dans le TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, en supprimant cette tâche préalable de cette tâche, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que la tâche correspondante dans le TaskFile de test principal n'a plus de tâche préalable après le chargement des modifications."""
        newTask = task.Task(subject="Prereq")
        self.taskFile1.tasks().append(newTask)
        self.task.addPrerequisites([newTask])
        self.taskFile1.save()
        self.taskFile2.load()
        self.task.removePrerequisites([newTask])
        self.taskFile1.save()
        self.taskFile2.monitor().resetAllChanges()
        self.doSave(self.taskFile2)

        for tsk in self.taskFile2.tasks():
            if tsk.id() == self.task.id():
                self.assertEqual(len(tsk.prerequisites()), 0)
                break
        else:
            self.fail()


class TaskFileMultiUserTestSave(TaskFileMultiUserTestBase, TaskFileTestCase):
    """Teste la fonctionnalité de sauvegarde d'un TaskFile dans un environnement multi-utilisateur en vérifiant que les modifications apportées à un TaskFile sont correctement sauvegardées et reflétées dans un autre TaskFile utilisé pour le suivi des modifications, en sauvegardant les modifications dans les deux fichiers de tâches, puis en vérifiant que les propriétés modifiées dans le TaskFile de test principal correspondent aux nouvelles valeurs après le chargement des modifications."""

    def doSave(self, taskFile):
        """Vérifie que les modifications apportées à un TaskFile dans un environnement multi-utilisateur sont correctement sauvegardées et reflétées dans un autre TaskFile utilisé pour le suivi des modifications en sauvegardant les modifications dans le TaskFile spécifié, puis en vérifiant que les propriétés modifiées dans le TaskFile de test principal correspondent aux nouvelles valeurs après le chargement des modifications."""
        taskFile.save()


class TaskFileMultiUserTestMerge(TaskFileMultiUserTestBase, TaskFileTestCase):
    """
    Teste la fonctionnalité de fusion d'un TaskFile
    dans un environnement multi-utilisateur
    en vérifiant que les modifications apportées à un TaskFile sont correctement fusionnées
    et reflétées dans un autre TaskFile utilisé pour le suivi des modifications,
    en sauvegardant les modifications dans les deux fichiers de tâches,
    puis en vérifiant que les propriétés modifiées dans le TaskFile de test principal
    correspondent aux nouvelles valeurs après le chargement des modifications.
    """

    def doSave(self, taskFile):
        """
        Vérifie que les modifications apportées à un TaskFile
        dans un environnement multi-utilisateur sont correctement fusionnées
        et reflétées dans un autre TaskFile utilisé
        pour le suivi des modifications en fusionnant les modifications dans le TaskFile spécifié,
        puis en vérifiant que les propriétés modifiées dans le TaskFile de test principal
        correspondent aux nouvelles valeurs après le chargement des modifications.
        """
        taskFile.mergeDiskChanges()
