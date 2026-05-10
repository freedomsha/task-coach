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

# from __future__ import absolute_import
#
# from builtins import object
from taskcoachlib import command
from taskcoachlib.domain import attachment, task, note, category
from .CommandTestCase import CommandTestCase


class AddAttachmentTestsMixin(object):
    # def __init__(self):
    #     self.attachment = None

    def addAttachment(self, selectedItems=None):
        self.attachment = attachment.FileAttachment(
            "attachment"
        )  # pylint: disable=W0201
        # print(f"AttachmentCommandsTest.AddAttachmentTestsMixin.addAttachment : 🛠️ DEBUG - Création d'une tâche self={self} avec attachements: {self.attachments}, attachment={self.attachment}")
        print(
            f"AttachmentCommandsTest.AddAttachmentTestsMixin.addAttachment : 🛠️ DEBUG - Création d'une tâche self={self} avec attachment={self.attachment}"
        )

        addAttachmentCommand = command.AddAttachmentCommand(
            self.container, selectedItems or [], attachments=[self.attachment]
        )
        addAttachmentCommand.do()

    def testAddOneAttachmentToOneItem(self):
        self.addAttachment([self.item1])
        self.assertDoUndoRedo(
            lambda: self.assertEqual(
                [self.attachment], self.item1.attachments()
            ),
            lambda: self.assertEqual([], self.item1.attachments()),
        )

    def testAddOneAttachmentToTwoItems(self):
        self.addAttachment([self.item1, self.item2])
        self.assertDoUndoRedo(
            lambda: self.assertTrue(
                [self.attachment]
                == self.item1.attachments()
                == self.item2.attachments()
            ),
            lambda: self.assertTrue(
                [] == self.item1.attachments() == self.item2.attachments()
            ),
        )


class AddAttachmentTestCase(CommandTestCase):
    # ItemClass = ContainerClass = lambda subject: "Subclass responsibility"
    # @staticmethod
    def ItemClass(subject):
        return "Subclass responsibility"

    # @staticmethod
    def ContainerClass(subject):
        return "Subclass responsibility"

    def setUp(self):
        super().setUp()
        self.item1 = self.ItemClass(subject="item1")
        self.item2 = self.ItemClass(subject="item2")
        self.container = self.ContainerClass([self.item1, self.item2])


class AddAttachmentCommandWithTasksTest(
    AddAttachmentTestCase, AddAttachmentTestsMixin
):
    ItemClass = task.Task
    ContainerClass = task.TaskList


class AddAttachmentCommandWithNotesTest(
    AddAttachmentTestCase, AddAttachmentTestsMixin
):
    ItemClass = note.Note
    ContainerClass = note.NoteContainer


class AddAttachmentCommandWithCategoriesTest(
    AddAttachmentTestCase, AddAttachmentTestsMixin
):
    ItemClass = category.Category
    ContainerClass = category.CategoryList
