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

# Les échecs des tests unitaires liés à la gestion des pièces jointes dans TaskCoach après la migration Python 2.7 → Python 3.X sont principalement dus à des problèmes de gestion des événements, de synchronisation et d’incompatibilités entre les versions de Python. Les appels répétés à Event.addSource et les messages de débogage indiquant des ajouts non désirés de pièces jointes sont des indicateurs clés de ces problèmes. De plus, les différences dans la gestion des objets et des collections entre Python 2.7 et Python 3.X, ainsi que les incompatibilités des bibliothèques tierces, contribuent à ces échecs.
# Pour résoudre ces problèmes, il est recommandé de revoir la gestion des événements et des pièces jointes dans TaskCoach, d’adapter le code aux spécificités de Python 3.X, de vérifier la compatibilité des bibliothèques tierces, et de tester rigoureusement les méthodes de sauvegarde et de chargement des fichiers. Ces mesures permettront de restaurer la fiabilité des tests unitaires et d’assurer une gestion cohérente des pièces jointes dans TaskCoach sous Python 3.X.
#
# Cette analyse approfondie fournit une base solide pour comprendre et corriger les problèmes rencontrés lors de la migration de TaskCoach vers Python 3.X, en s’appuyant sur les logs, le code source et les spécificités des versions de Python.

from taskcoachlib.domain import base


class AttachmentOwner(object, metaclass=base.DomainObjectOwnerMetaclass):
    """Classe Mixin pour d'autres objets de domaine pouvant avoir des pièces jointes.

    Attributes :
        __ownedType__ (str) : Type d'objet propriétaire des pièces jointes. (Attachment)
        __attachments (list) : liste des pièces jointes.
    """

    # __metaclass__ = base.DomainObjectOwnerMetaclass
    __ownedType__ = "Attachment"

    def __init__(self, *args, **kwargs):
        self.__attachments = kwargs.pop("attachments", [])
        # safe_super_init(AttachmentOwner, self, *args, **kwargs)
        print(
            f"AttachmentOwner.__init__ : récupère attachments = {self.__attachments}."
        )
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
        """Retourner la commande d'ajout d'une pièce jointe sous forme de chaîne de caractères."""
        # like taskcoachlib/patterns/observer/addItemEventType
        # and taskcoachlib/domain/base/owner/noteAddedEventType
        # return '%s.add' % cls
        return f"{class_}.add"
        pass

    @classmethod
    def attachmentRemovedEventType(class_):
        """Retourner la commande de suppression d'une pièce jointe sous forme de chaîne de caractères."""
        # like taskcoachlib/patterns/observer/removeItemEventType
        # and taskcoachlib/domain/base/owner/noteRemovedEventType
        # return '%s.remove' % cls
        return f"{class_}.remove"
        pass

    def attachments(self):
        """Retourne la liste des pièces jointes."""
        print("AttachmentOwner.attachments est appelé !")
        return self.__attachments
        pass
