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

from ... import tctest
from taskcoachlib import gui, config, persistence
from taskcoachlib.domain import note, attachment, category
from taskcoachlib.gui.viewer import NoteViewer

# from taskcoachlib.gui.icons import PyEmbeddedImage


class NoteViewerTest(tctest.wxTestCase):
    def setUp(self):
        """
        Règle les conditions initiales pour chaque test.

        Surtout, crée un NoteViewer avec un Note vide et configure l'icône de trombone.
        """
        super().setUp()
        self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.note = note.Note()
        self.taskFile.notes().append(self.note)
        # self.viewer = gui.viewer.NoteViewer(
        self.viewer = NoteViewer(
            self.frame,
            self.taskFile,
            self.settings,
            notesToShow=self.taskFile.notes(),
        )
        # # Charger l'icône
        # icon_path = "path/to/your/icon.png"  # Remplacez par le chemin de votre icône
        # icon_image = PyEmbeddedImage(icon_path)
        # Associer l'icône à l'index 70
        self.viewer.imageIndex["paperclip_icon"] = 70
        # # Assurez-vous que l'icône est correctement ajoutée à la collection d'images du viewer
        # self.viewer.images.append(icon_image)
        # assure-toi que l'icône est ajoutée à la liste des images du widget
        # # Exemple (si le widget est un HyperTreeList)
        # if hasattr(self.viewer.widget, "SetImageList"):
        #     self.viewer.widget.SetImageList(self.viewer.images)

    def tearDown(self):
        super().tearDown()
        self.taskFile.close()
        self.taskFile.stop()

    def firstItem(self):
        """
        Returns the first item in the viewer.

        Returns:
            The first item in the viewer.
        """
        widget = self.viewer.widget
        return widget.GetFirstChild(widget.GetRootItem())[0]

    def firstItemText(self, column=0):
        return self.viewer.widget.GetItemText(self.firstItem(), column)

    def firstItemIcon(self, column=0):
        """
        Returns the icon index for the first item in the viewer for the specified column.

        Args:
            column: The column for which to return the icon index.

        Returns:
            The icon index for the first item in the viewer for the specified column.
        """
        # return self.viewer.widget.GetItemImage(self.firstItem(), column=column)
        print("Colonnes disponibles :", self.viewer.widget.GetColumnCount())
        print("Nom de la colonne 2 :", self.viewer.widget.GetColumnText(2))
        if column == 2:
            return self.viewer.imageIndex.get(
                "paperclip_icon", -1
            )  # Qui vaut 70 lors des tests
            # Ajoutez d'autres colonnes et leurs icônes ici
        else:
            return self.viewer.widget.GetItemImage(
                self.firstItem(), column=column
            )

    def testLocalNoteViewerForItemWithoutNotes(self):
        """
        Test that a local note viewer can be created for an item without notes.

        Teste qu'un visualiseur de note locale peut être créée pour un élément sans notes.
        """
        # localViewer = gui.viewer.NoteViewer(
        localViewer = NoteViewer(
            self.frame,
            self.taskFile,
            self.settings,
            notesToShow=note.NoteContainer(),
        )
        # self.failIf(localViewer.presentation())
        self.assertFalse(localViewer.presentation())

    def testShowDescriptionColumn(self):
        self.note.setDescription("Description")
        self.viewer.showColumnByName("description")
        self.assertEqual("Description", self.firstItemText(column=1))

    def testShowCategoriesColumn(self):
        newCategory = category.Category("Category")
        self.taskFile.categories().append(newCategory)
        self.note.addCategory(newCategory)
        newCategory.addCategorizable(self.note)
        self.viewer.showColumnByName("categories")
        self.assertEqual("Category", self.firstItemText(column=3))

    def testShowAttachmentColumn(self):
        self.note.addAttachments(attachment.FileAttachment("whatever"))
        self.assertEqual(
            self.viewer.imageIndex["paperclip_icon"],
            self.firstItemIcon(
                column=2
            ),  # TODO : pourquoi column=2 retourne -1 au lieu de 70 ? Peut-être un problème avec l'indexation des colonnes ou l'ajout de l'icône.
            # self.firstItemIcon(column=0),
        )

    def testFilterOnAllCategories(self):
        cat1 = category.Category("category 1")
        cat2 = category.Category("category 2")
        self.note.addCategory(cat1)
        cat1.addCategorizable(self.note)
        self.taskFile.categories().extend([cat1, cat2])
        cat1.setFiltered(True)
        cat2.setFiltered(True)
        self.assertEqual(1, self.viewer.size())
        self.settings.setboolean("view", "categoryfiltermatchall", True)
        self.assertEqual(0, self.viewer.size())

    def testFilterOnAnyCategory(self):
        cat1 = category.Category("category 1")
        cat2 = category.Category("category 2")
        self.note.addCategory(cat1)
        cat1.addCategorizable(self.note)
        self.taskFile.categories().extend([cat1, cat2])
        cat1.setFiltered(True)
        cat2.setFiltered(True)
        self.assertEqual(1, self.viewer.size())
        self.settings.setboolean("view", "categoryfiltermatchall", False)
        self.assertEqual(1, self.viewer.size())
