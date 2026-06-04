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

from taskcoachlib.domain import base


class AttachmentOwner(object, metaclass=base.DomainObjectOwnerMetaclass):
    """Classe Mixin pour d'autres objets de domaine pouvant avoir des pièces jointes."""

    # __metaclass__ = base.DomainObjectOwnerMetaclass
    __ownedType__ = "Attachment"

    def __init__(self, *args, **kwargs):
        self.__attachments = kwargs.pop("attachments", [])
        # safe_super_init(AttachmentOwner, self, *args, **kwargs)
        # Transmet les arguments uniquement si le parent **n'est pas `object`**
        # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
        if type(self).__mro__[1] is not object:
            try:
                super().__init__(*args, **kwargs)
            except TypeError:
                super().__init__()
        else:
            super().__init__()  # Sécurisé pour `object`

    @classmethod
    def attachmentAddedEventType(class_):
        # like taskcoachlib/patterns/observer/addItemEventType
        # and taskcoachlib/domain/base/owner/noteAddedEventType
        # return '%s.add' % cls
        return f"{class_}.add"
        pass

    @classmethod
    def attachmentRemovedEventType(class_):
        # like taskcoachlib/patterns/observer/removeItemEventType
        # and taskcoachlib/domain/base/owner/noteRemovedEventType
        # return '%s.remove' % cls
        return f"{class_}.remove"
        pass

    def attachments(self):
        print("AttachmentOwner.attachments est appelé !")
        return self.__attachments
        pass
