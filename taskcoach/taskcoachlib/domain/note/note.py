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

# from . import noteowner
from taskcoachlib.domain.categorizable import CategorizableCompositeObject

# from taskcoachlib.domain import base
from taskcoachlib.domain.attachment.attachmentowner import AttachmentOwner
from taskcoachlib.domain.note.noteowner import NoteOwner


# class Note(base.AttachmentOwner,
class Note(AttachmentOwner, CategorizableCompositeObject):
    """Cette classe représente des notes. Les notes comprennent un sujet, une description
    et des pièces jointes. De plus, une note peut être attribuée aux catégories.
    """

    # pass

    def __init__(self, *args, **kwargs):
        print(f"Note.__init__ kwargs = {kwargs}")
        print(">>> Note.__init__ AVANT super")
        super().__init__(*args, **kwargs)
        print(">>> Note.__init__ APRES super")
        print("Note.__init__ : terminé !")
        # Note: Effective appearance is computed by ComputeStyles polling

    def addAttachments(self, param, **kwargs):
        """Ajouter une ou plusieurs pièces jointes à la note."""
        print(
            f"Task.addAttachments : Ajout de pièces jointes à la note {self.id}."
        )
        # self.addAttachments(param)

        # [Previous line repeated 981 more times]
        # RecursionError: maximum recursion depth exceeded
        # pub.sendMessage("task.attachments.added")
        super().addAttachments(param, **kwargs)
        pass
