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

Contient la classe mixin NoteOwner pour les (autres) objets de domaine pouvant contenir des notes.

La métaclasse DomainObjectOwnerMetaclass (dans owner.py) ajoute automatiquement les éléments suivants à NoteOwner si __ownedType__ = "Note" est défini :
Méthodes générées automatiquement :

      addNote(note) Méthode/Propriété
Rôle      Ajoute une note à la liste interne.
Exemple d'utilisation      note_owner.addNote(my_note)


      removeNote(note) Méthode/Propriété
Rôle      Supprime une note de la liste.
Exemple d'utilisation      note_owner.removeNote(my_note)


      notes() Méthode/Propriété
Rôle      Retourne la liste des notes.
Exemple d'utilisation      note_owner.notes()


      setNotes(notes) Méthode/Propriété
Rôle      Remplace la liste des notes.
Exemple d'utilisation      note_owner.setNotes([note1, note2])


      noteAddedEventType() Méthode/Propriété
Rôle      Type d'événement quand une note est ajoutée.
Exemple d'utilisation      NoteOwner.noteAddedEventType()


      noteRemovedEventType() Méthode/Propriété
Rôle      Type d'événement quand une note est supprimée.
Exemple d'utilisation      NoteOwner.noteRemovedEventType()


      notesChangedEventType() Méthode/Propriété
Rôle      Type d'événement quand la liste change.
Exemple d'utilisation      NoteOwner.notesChangedEventType()


      _notes Propriété
Rôle      Liste interne pour stocker les notes.
Exemple d'utilisation      note_owner._notes

La métaclasse ajoute aussi la logique pour notifier les observateurs
(via __notifyObservers) quand une note est ajoutée/supprimée.
"""

# from builtins import object
import logging

# try:
#    from .. import base
# except ImportError:
from taskcoachlib.domain import base
from taskcoachlib.domain.base import owner
from pubsub import pub

#  Importe la métaclasse DomainObjectOwnerMetaclass depuis le module taskcoachlib.domain.base

log = logging.getLogger(__name__)


class NoteOwner(object, metaclass=owner.DomainObjectOwnerMetaclass):
    # class NoteOwner(object, metaclass=base.DomainObjectOwnerMetaclass, __ownedType__="Note") :
    # Cela signifie que la classe bénéficiera des fonctionnalités de gestion des objets possédés
    # (notes dans ce cas) fournies par la métaclasse.
    """Classe Mixin pour les (autres) objets de domaine pouvant contenir des notes.

    NoteOwner est une classe mixin qui peut être utilisée pour les objets de domaine qui peuvent posséder des notes.
    En utilisant la métaclasse DomainObjectOwnerMetaclass, NoteOwner bénéficie de fonctionnalités de gestion des objets possédés, ce qui facilite l'ajout et la suppression de notes associées à ces objets de domaine.

    Les classes qui héritent de NoteOwner sont surtout Task et Category, mais d'autres classes de domaine pourraient également en bénéficier si elles ont besoin de gérer des notes associées.
    """

    # __metaclass__ = base.DomainObjectOwnerMetaclass
    # Lequel NoteOwner utiliser ? domain/note/noteowner ou domain/base/owner ?
    # domain/base/owner sert de base metaclass pour les classes utilisant DomainObjectOwnerMetaclass
    # La métaclasse a besoin de __ownedType__ = "Note" pour générer les méthodes.
    __ownedType__ = "Note"
    # Cet attribut est explicitement défini à 'Note'.
    # Il indique à la métaclasse que la classe peut posséder des objets de type Note.

    # Pas besoin de redéfinir noteAddedEventType, noteRemovedEventType, etc.
    # Pas besoin de redéfinir addNote, removeNote, etc.

    # Laisser la métaclasse DomainObjectOwnerMetaclass fournir
    # automatiquement le constructeur (owner.constructor). Ne
    # redéfinissons pas __init__ ici car cela empêche la
    # métaclasse d'initialiser correctement la liste des pièces
    # jointes (et casse la logique de copie).
    # def __init__(self, *args, **kwargs):
    #     """
    #     Initialise
    #
    #     Args:
    #         *args:
    #         **kwargs:
    #     """
    #     print(
    #         f"DEBUG: NoteOwner.__init__ called with args: {args}, kwargs: {kwargs}"
    #     )
    #     # self.__notes = kwargs.pop("notes", [])  # Géré dans owner.DomainObjectOwnerMetaclass
    #     # safe_super_init(NoteOwner, self, *args, **kwargs)
    #     print(
    #         f"DEBUG: NoteOwner.__init__ after popping notes, remaining kwargs: {kwargs}, self.__notes={self.__notes}"
    #     )
    #     # Transmet les arguments uniquement si le parent **n'est pas `object`**
    #     # Test de sécurité : on ne transmet que si `super()` n'est pas `object`
    #     if type(self).__mro__[1] is not object:
    #         try:
    #             super().__init__(*args, **kwargs)
    #         except TypeError:
    #             super().__init__()
    #     else:
    #         super().__init__()  # Sécurisé pour `object`
    #     print(
    #         f"DEBUG: NoteOwner.__init__ completed for {self} (id: {self.id() if hasattr(self,'id') else 'N/A'}) with notes: {self.__notes}"
    #     )

    # # Il faudra juste compléter les méthodes noteAddedEventType et noteRemovedEventType
    # # pour qu'elles retournent les types d'événements appropriés.
    # NON, il faut utiliser les méthodes générées par DomainObjectOwnerMetaclass !
    # @classmethod
    # def noteAddedEventType(class_):
    #     # # like taskcoachlib/patterns/observer/addItemEventType
    #     # # and taskcoachlib/domain/attachment/attachmentowner/attachmentAddedEventType
    #     # # return f"{class_}.add"  # TODO : à essayer
    #     # # return f"{class_}.noteAdded"  # TODO: a essayer
    #     # return f"{class_}.add"
    #     # # return f"{class_}.noteAdd"  # TODO: a essayer
    #     # pass
    #     return f"{class_.__module__.split('.')[-1]}.{class_.__ownedType__.lower()}.add"

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

    # Utiliser la méthode générée par DomainObjectOwnerMetaclass !
    # @classmethod
    # def noteRemovedEventType(class_):
    #     # # like taskcoachlib/patterns/observer/removeItemEventType
    #     # # and taskcoachlib/domain/attachment/attachmentowner/attachmentRemovedEventType
    #     # # return f"{class_}.remove"
    #     # return f"{class_}.remove"
    #     # # return f"{cls}.attachmentRemoved"  # TODO: a essayer
    #     # pass
    #     return f"{class_.__module__.split('.')[-1]}.{class_.__ownedType__.lower()}.remove"

    # def notes(self):
    #     # pass
    #     print(
    #         f"DEBUG: NoteOwner.notes() called for {self} (id: {self.id() if hasattr(self, 'id') else 'N/A'}, returning {len(self.__notes)} notes: {self.__notes}"
    #     )
    #     return self.__notes

    # Nouvelles lignes :
    # Décommenter si nécessaire mais ne fonctionne pas encore:
    # def __lt__(self, other):
    #     """Compare deux tâches par leur ID."""
    #     return self.id < other.id

    # def addNote(self, aNote):
    #     # pass
    #     if aNote not in self._notes:
    #         self._notes.append(aNote)
    #         # On notifie pour que TaskFile puisse passer needSave à True
    #         pub.sendMessage('task.notes.added', task=self, note=aNote)

    # def addNote(self, aNote, **kwargs):
    #     """Méthode singulière (utilisée par ton test)"""
    #     self.addNotes(aNote, **kwargs)
    #
    # def notes(self, recursive=False):
    #     """
    #     Retourne la liste des notes de la tâche.
    #     Si recursive est True, inclut aussi les notes des sous-tâches.
    #     """
    #     print(
    #         # f"DEBUG: Task.notes() called for task {self.id()} (subject: {self.subject()}) with recursive={recursive}"
    #         f"DEBUG: NoteOwner.notes() called for task {self.id()} (subject: {self.subject()}) with recursive={recursive}"
    #     )
    #     # Utiliser super().notes() pour accéder à la méthode de NoteOwner
    #     ownNotes = (
    #         super().notes()
    #     )  # This gets the notes directly attached to this task via NoteOwner
    #     # # Accès direct à l'attribut manglé de Noteowner pour éviter toute redéfinition de notes() qui pourrait causer une récursion infinie
    #     # ownNotes = self._NoteOwner__notes
    #     # print(f"DEBUG: Task.notes() - ownNotes for {self.id()}: {ownNotes}")
    #     print(
    #         f"DEBUG: NoteOwner.notes() - ownNotes for {self.id()}: {ownNotes}"
    #     )
    #
    #     childNotes = []
    #     if recursive:
    #         for child in self.children():
    #             print(
    #                 # f"DEBUG: Task.notes() - Getting notes for child task {child.id()} (subject: {child.subject()})"
    #                 f"DEBUG: NoteOwner.notes() - Getting notes for child task {child.id()} (subject: {child.subject()})"
    #             )
    #             childNotes.extend(child.notes(recursive=True))
    #
    #     allNotes = ownNotes + childNotes
    #     print(
    #         # f"DEBUG: Task.notes() - Returning allNotes for {self.id()}: {allNotes}"
    #         f"DEBUG: NoteOwner.notes() - Returning allNotes for {self.id()}: {allNotes}"
    #     )
    #     return allNotes
    #
    # def addNotes(self, *notes, **kwargs):
    #     """Méthode plurielle (utilisée par les Commandes)"""
    #     # print(f"DEBUG: Task.addNotes called for task {getattr(self,'id', lambda:None)()} with notes={notes}")
    #     for aNote in notes:
    #         # Vérifie l'existence de la note dans les notes de la tâche avant de l'ajouter pour éviter les doublons.
    #         # Utiliser super().notes() pour accéder à la liste gérée par NoteOwner.
    #         # Ensure we operate on the actual NoteOwner storage attribute
    #         notes_attr = getattr(self, "_NoteOwner__notes", None)
    #         if notes_attr is None:
    #             # Initialize the storage if missing
    #             setattr(self, "_NoteOwner__notes", [])
    #             notes_attr = getattr(self, "_NoteOwner__notes")
    #         if aNote not in notes_attr:
    #             # print(f"DEBUG: Adding note {aNote} to task {getattr(self,'id', lambda:None)()}")
    #             # Définit le parent de la note
    #             aNote.setParent(self)
    #             # Ajoute à la liste gérée par NoteOwner
    #             notes_attr.append(aNote)
    #             # Notifier pour que TaskFile.needSave passe à True
    #             try:
    #                 pub.sendMessage("task.notes.added", task=self, note=aNote)
    #             except Exception:
    #                 pub.sendMessage("task.notes.added")
    #
    # @classmethod
    # def notesChangedEventType(cls):
    #     """Retourne le type d'événement à publier lorsque les notes changent."""
    #     # pass
    #     return "pubsub.task.notes"
