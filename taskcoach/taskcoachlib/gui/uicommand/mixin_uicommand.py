"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

Vous devez spécifier les classes de mixin avant les autres classes.
"""

# from builtins import object
from taskcoachlib.domain import task, note, category, effort, attachment
import wx


# Quels sont ces types de classes ? Mixin
# class NeedsSelectionMixin:
class NeedsSelectionMixin(object):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and self.viewer.curselection()


class NeedsSelectedCategorizableMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un catégorisable sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(note.Note)
        )


class NeedsOneSelectedItemMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur qui nécessitent exactement un élément sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and len(self.viewer.curselection()) == 1


class NeedsSelectedCompositeMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément composite
    sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(note.Note)
            or self.viewer.curselectionIsInstanceOf(category.Category)
        )


class NeedsOneSelectedCompositeItemMixin(
    NeedsOneSelectedItemMixin, NeedsSelectedCompositeMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent exactement un élément composite sélectionné."""

    pass


class NeedsAttachmentViewerMixin(object):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant une visionneuse affichant les pièces jointes."""

    def enabled(self, event):
        return super().enabled(event) and self.viewer.isShowingAttachments()


class NeedsSelectedTasksMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant une ou plusieurs tâches sélectionnées."""

    def enabled(self, event):
        return super().enabled(event) and self.viewer.curselectionIsInstanceOf(
            task.Task
        )


class NeedsSelectedNoteOwnersMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de note sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(category.Category)
            or self.viewer.curselectionIsInstanceOf(attachment.Attachment)
        )


class NeedsSelectedNoteOwnersMixinWithNotes(NeedsSelectedNoteOwnersMixin):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins un propriétaire de note sélectionné
    avec des notes."""

    def enabled(self, event):
        # pylint: disable=E1101
        return super().enabled(event) and any(
            [item.notes() for item in self.viewer.curselection()]
        )


class NeedsSelectedAttachmentOwnersMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un propriétaire de pièce jointe sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and (
            self.viewer.curselectionIsInstanceOf(task.Task)
            or self.viewer.curselectionIsInstanceOf(category.Category)
            or self.viewer.curselectionIsInstanceOf(note.Note)
        )


class NeedsOneSelectedTaskMixin(
    NeedsSelectedTasksMixin, NeedsOneSelectedItemMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant au moins une tâche sélectionnée."""

    pass


class NeedsSelectionWithAttachmentsMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément sélectionné avec
    une ou plusieurs pièces jointes."""

    def enabled(self, event):
        return super().enabled(event) and any(
            item.attachments()
            for item in self.viewer.curselection()
            if not isinstance(item, effort.Effort)
        )


class NeedsSelectedEffortMixin(NeedsSelectionMixin):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un effort sélectionné."""

    def enabled(self, event):
        return super().enabled(event) and self.viewer.curselectionIsInstanceOf(
            effort.Effort
        )


class NeedsSelectedAttachmentsMixin(
    NeedsAttachmentViewerMixin, NeedsSelectionMixin
):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins une pièce jointe sélectionnée
    ."""

    pass


class NeedsAtLeastOneTaskMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une tâche."""

    def enabled(self, event):  # pylint: disable=W0613
        return len(self.taskList) > 0


class NeedsAtLeastOneCategoryMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur nécessitant la création d’au moins une catégorie."""

    def enabled(self, event):  # pylint: disable=W0613
        return len(self.categories) > 0


class NeedsItemsMixin(object):
    """Classe Mixin pour les commandes d'interface utilisateur qui nécessitent au moins un élément dans leur visionneuse."""

    def enabled(self, event):  # pylint: disable=W0613
        return self.viewer.size()


class NeedsTreeViewerMixin(object):
    """Classe Mixin pour les commandes d'interface utilisateur nécessitant une visionneuse d'arborescence."""

    def enabled(self, event):
        return super().enabled(event) and self.viewer.isTreeViewer()


class NeedsDeletedItemsMixin(object):
    """Classe Mixin pour les commandes d’interface utilisateur qui nécessitent la présence d’éléments supprimés."""

    def enabled(self, event):
        return super().enabled(event) and self.iocontroller.hasDeletedItems()


class PopupButtonMixin(object):
    """Mélange cela avec un UICommand pour un menu contextuel de barre d'outils."""

    def doCommand(self, event):  # pylint: disable=W0613
        try:
            args = [self.__menu]
        except AttributeError:
            self.__menu = self.createPopupMenu()  # pylint: disable=W0201
            args = [self.__menu]

        # Check if menu has any items
        if self.__menu.GetMenuItemCount() == 0:
            wx.MessageBox(
                _(
                    "No templates available. Create a template first by saving a task as a template."
                ),
                _("No Templates"),
                wx.OK | wx.ICON_INFORMATION,
                self.mainWindow(),
            )
            return

        if self.toolbar:
            args.append(self.menuXY())
        self.mainWindow().PopupMenu(*args)  # pylint: disable=W0142

    def menuXY(self):
        """Emplacement pour afficher le menu."""
        return self.mainWindow().ScreenToClient((self.menuX(), self.menuY()))

    def menuX(self):
        # Get the tool's position in the toolbar
        toolRect = self.toolbar.GetToolRect(self.id)
        if toolRect is not None:
            # Convert toolbar-local position to screen coordinates
            toolbarScreenPos = self.toolbar.GetScreenPosition()
            # Align to the left edge of the button
            return toolbarScreenPos[0] + toolRect[0]
        else:
            # Fallback to mouse position if tool rect not available
            buttonWidth = self.toolbar.GetToolSize()[0]
            mouseX = wx.GetMousePosition()[0]
            return mouseX - 0.5 * buttonWidth

    def menuY(self):
        toolbarY = self.toolbar.GetScreenPosition()[1]
        toolbarHeight = self.toolbar.GetSize()[1]
        return toolbarY + toolbarHeight

    def createPopupMenu(self):
        raise NotImplementedError  # pragma: no cover
