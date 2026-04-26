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

# from builtins import object
# try:
#    from .. import base
# except ImportError:
from taskcoachlib.domain import base

#  Importe la métaclasse DomainObjectOwnerMetaclass depuis le module taskcoachlib.domain.base


class NoteOwner(object, metaclass=base.DomainObjectOwnerMetaclass):
    # class NoteOwner(object, metaclass=base.DomainObjectOwnerMetaclass, __ownedType__="Note") :
    # Cela signifie que la classe bénéficiera des fonctionnalités de gestion des objets possédés
    # (notes dans ce cas) fournies par la métaclasse.
    """Classe Mixin pour les (autres) objets de domaine pouvant contenir des notes."""

    # __metaclass__ = base.DomainObjectOwnerMetaclass
    # TODO: lequel NoteOwner utiliser ? domain/note/noteowner ou domain/base/owner ?
    # domain/base/owner sert de base metaclass pour les classes utilisant DomainObjectOwnerMetaclass
    __ownedType__ = "Note"
    # Cet attribut est explicitement défini à 'Note'.
    # Il indique à la métaclasse que la classe peut posséder des objets de type Note.

    def __init__(self, *args, **kwargs):
        self.__notes = kwargs.pop("notes", [])
        # safe_super_init(NoteOwner, self, *args, **kwargs)
        # Transmet les arguments uniquement si le parent **n'est pas `object`**
        # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
        if type(self).__mro__[1] is not object:
            try:
                super().__init__(*args, **kwargs)
            except TypeError:
                super().__init__()
        else:
            super().__init__()  # Sécurisé pour `object`

    # Il faudra juste compléter les méthodes noteAddedEventType et noteRemovedEventType
    # pour qu'elles retournent les types d'événements appropriés.
    @classmethod
    def noteAddedEventType(class_):
        # like taskcoachlib/patterns/observer/addItemEventType
        # and taskcoachlib/domain/attachment/attachmentowner/attachmentAddedEventType
        # return f"{class_}.add"  # TODO : à essayer
        # return f"{class_}.noteAdded"  # TODO: a essayer
        return f"{class_}.add"
        # return f"{class_}.noteAdd"  # TODO: a essayer
        pass

    # @classmethod
    # def categoryAddedEventType(class_):
    #     return "categorizable.category.add"
    #
    # def addCategory(self, *categories, **kwargs):
    #     return self.__categories.add(set(categories), event=kwargs.pop("event", None))
    #
    # @classmethod
    # def categoryRemovedEventType(class_):
    #     return 'categorizable.category.remove'

    @classmethod
    def noteRemovedEventType(class_):
        # like taskcoachlib/patterns/observer/removeItemEventType
        # and taskcoachlib/domain/attachment/attachmentowner/attachmentRemovedEventType
        # return f"{class_}.remove"
        return f"{class_}.remove"
        # return f"{cls}.attachmentRemoved"  # TODO: a essayer
        pass

    def notes(self):
        # pass
        return self.__notes
