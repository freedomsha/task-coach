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

Fonctionnalité de base

La classe Attachment est une classe de base pour
différents types de pièces jointes, telles que les pièces jointes de fichiers
ou les pièces jointes d'images. Il fournit une interface commune
pour gérer l'emplacement d'une pièce jointe
et pour notifier les modifications apportées à cet emplacement.

Attributs clés

    location : l'emplacement de la pièce jointe.

Méthodes clés

    __init__ : initialise la pièce jointe avec un emplacement donné.
    location : obtient l'emplacement de la pièce jointe.
    setLocation : définit l'emplacement de la pièce jointe et informe les auditeurs.
    open : ouvre la pièce jointe (méthode abstraite, implémentée par les sous-classes).
    __getstate__ et __setstate__ : méthodes de sérialisation et de désérialisation.
    __getcopystate__ : méthode de création de copies de la pièce jointe.

Observations et améliorations potentielles

    Gestion de l'emplacement :
        L'attribut d'emplacement est utilisé pour stocker l'emplacement de la pièce jointe.
        La méthode setLocation est utilisée pour mettre à jour l'emplacement et avertir les auditeurs.
        Envisagez d'utiliser un mécanisme plus robuste pour gérer les chemins de fichiers, comme l'utilisation de pathlib pour gérer les opérations de chemin spécifiques à la plate-forme.

    Notifications d'événements :
        La méthode locationChangedEventType définit un type d'événement pour les changements d'emplacement.
        La méthode markDirty, héritée de la classe de base, est probablement utilisée pour déclencher la notification.
        Assurez-vous que le mécanisme de notification d'événement est cohérent avec le reste de l'application.

    Sérialisation et copie :
        Les méthodes __getstate__ et __setstate__ sont utilisées pour la sérialisation et la désérialisation.
        Le La méthode __getcopystate__ est utilisée pour créer des copies de la pièce jointe.
        Assurez-vous que le processus de sérialisation gère tous les attributs pertinents et que le processus de copie crée une copie complète si nécessaire.

    Implémentation manquante :
        La méthode open est abstraite et doit être implémentée par des sous-classes pour fournir un comportement d'ouverture spécifique pour différents types de pièces jointes.

Questions potentielles pour une analyse plus approfondie

    Types de pièces jointes :
        Comment les différents types de pièces jointes (par exemple, fichier, image, URL) sont-ils représentés ? Existe-t-il des sous-classes spécifiques pour chaque type ?
    Considérations sur la sécurité :
        Comment les pièces jointes sont-elles gérées en toute sécurité, en particulier lorsqu'il s'agit de fichiers potentiellement malveillants ?
    Gestion des erreurs :
        Quels mécanismes de gestion des erreurs sont en place pour des opérations telles que ouvrir ou enregistrer des pièces jointes ?
    Performance :
        Existe-t-il des optimisations de performances qui peuvent être apportées, en particulier pour les pièces jointes volumineuses ou les opérations fréquentes ?


Fonctionnalité de base

La classe FileAttachment est une sous-classe concrète de Attachment qui représente les pièces jointes. Il étend la classe de base en fournissant des implémentations spécifiques pour l'ouverture et la normalisation des chemins de fichiers.

Méthodes clés

    open : ouvre la pièce jointe à l'aide de la fonction openAttachment spécifiée.
    normalizedLocation : normalise le chemin du fichier en fonction de le répertoire de travail.
    isLocalFile : Vérifie si la pièce jointe est un fichier local.

Observations et potentiel Améliorations

    Fonction openAttachment :
        La fonction openAttachment est transmise en tant qu'argument à la méthode open, permettant de personnaliser le comportement d'ouverture des fichiers.
        Envisagez d'utiliser un mécanisme d'ouverture de fichiers plus robuste qui gère les exceptions potentielles. et les interactions de l'utilisateur.

    Normalisation du chemin de fichier :
        La méthode normalizedLocation garantit que le chemin du fichier est correctement normalisé, en particulier lorsqu'il s'agit de chemins relatifs et de travail. répertoires.
        Envisagez d'utiliser pathlib pour une manipulation de chemin plus avancée et des opérations indépendantes de la plate-forme.

    Détection de fichier local :
        La méthode isLocalFile vérifie si la pièce jointe est un fichier local en analysant l'URL.
        Cette méthode pourrait être simplifiée en vérifiant directement si le chemin commence par une racine du système de fichiers.

Améliorations potentielles

    Erreur Gestion :
        Implémentez la gestion des erreurs dans les cas où le fichier ne peut pas être ouvert ou où le chemin n'est pas valide.
    Considérations de sécurité :
        Tenez compte des implications en matière de sécurité, telles que la désinfection des chemins de fichiers pour empêcher les attaques potentielles.
    Performance :
        Pour les fichiers volumineux, envisagez d'utiliser des opérations de fichiers asynchrones ou des fichiers mappés en mémoire pour améliorer les performances.
    Compatibilité multiplateforme :
        Assurez-vous que les mécanismes d'ouverture de fichier et de normalisation du chemin fonctionner correctement sur différents systèmes d'exploitation.

Considérations supplémentaires

    Validation du type de fichier :
        Selon le cas d'utilisation, vous souhaiterez peut-être valider le type de fichier pour garantir la compatibilité avec l'application.
    Limites de taille de fichier :
        Envisagez d'implémenter des limites de taille de fichier pour éviter des problèmes potentiels avec les fichiers volumineux.
    Interface utilisateur :
        Si l'application dispose d'une interface utilisateur, fournissez des commentaires à l'utilisateur pendant le traitement du fichier. opérations d'ouverture et de fermeture.
"""

from io import open as file
from filecmp import cmp

# unresolved reference 'cmp'
from functools import total_ordering
import os
from urllib.parse import urlparse
from taskcoachlib import patterns, mailer
from taskcoachlib.domain import base
from taskcoachlib.i18n import _
from taskcoachlib.tools import openfile

# try:
from pubsub import pub

# except ImportError:
#    # try:
#    from taskcoachlib.thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
# from taskcoachlib.domain.base import NoteOwner
from taskcoachlib.domain.note.noteowner import NoteOwner  # plutôt ?
from taskcoachlib.domain.attachment.attachmentowner import AttachmentOwner


def getRelativePath(path, basePath=os.getcwd()):
    """Essaie de deviner la version relative de « chemin » à partir de « basePath ». Si
    ce n'est pas possible, renvoie le « chemin » absolu. 'path' et 'basePath' doivent tous deux
    être absolus."""

    path = os.path.realpath(os.path.normpath(path))
    basePath = os.path.realpath(os.path.normpath(basePath))

    drive1, path1 = os.path.splitdrive(path)
    drive2, path2 = os.path.splitdrive(basePath)

    # No relative path is possible if the two are on different drives.
    if drive1 != drive2:
        return path

    if path1.startswith(path2):
        if path1 == path2:
            return ""

        if path2 == os.path.sep:
            return path1[1:].replace("\\", "/")

        return path1[len(path2) + 1 :].replace("\\", "/")
        # return path1[len(path2) + 1 :].replace("\\", "/")

    path1 = path1.split(os.path.sep)
    path2 = path2.split(os.path.sep)

    while path1 and path2 and path1[0] == path2[0]:
        path1.pop(0)
        path2.pop(0)

    while path2:
        path1.insert(0, "..")
        path2.pop(0)

    return os.path.join(*path1).replace("\\", "/")  # pylint: disable=W0142


# class Attachment(base.Object, NoteOwner):
@total_ordering
class Attachment(base.Object, NoteOwner):
    """
    Classe de base abstraite pour les pièces jointes.

    Fonctionnalité de base

    La classe Attachment est une classe de base pour
    différents types de pièces jointes,
    telles que les pièces jointes de fichiers
    ou les pièces jointes d'images.
    Il fournit une interface commune
    pour gérer l'emplacement d'une pièce jointe
    et pour notifier les modifications apportées à cet emplacement.

    Attributs clés

        location : l'emplacement de la pièce jointe.

    Méthodes clés

        __init__ : initialise la pièce jointe avec un emplacement donné.
        location : obtient l'emplacement de la pièce jointe.
        setLocation : définit l'emplacement de la pièce jointe et informe les auditeurs.
        open : ouvre la pièce jointe (méthode abstraite, implémentée par les sous-classes).
        __getstate__ et __setstate__ : méthodes de sérialisation et de désérialisation.
        __getcopystate__ : méthode de création de copies de la pièce jointe.

    Observations et améliorations potentielles

        Gestion de l'emplacement :
            L'attribut d'emplacement est utilisé pour stocker l'emplacement de la pièce jointe.
            La méthode setLocation est utilisée pour mettre à jour l'emplacement et avertir les auditeurs.
            Envisagez d'utiliser un mécanisme plus robuste pour gérer les chemins de fichiers, comme l'utilisation de pathlib pour gérer les opérations de chemin spécifiques à la plate-forme.

        Notifications d'événements :
            La méthode locationChangedEventType définit un type d'événement pour les changements d'emplacement.
            La méthode markDirty, héritée de la classe de base, est probablement utilisée pour déclencher la notification.
            Assurez-vous que le mécanisme de notification d'événement est cohérent avec le reste de l'application.

        Sérialisation et copie :
            Les méthodes __getstate__ et __setstate__ sont utilisées pour la sérialisation et la désérialisation.
            Le La méthode __getcopystate__ est utilisée pour créer des copies de la pièce jointe.
            Assurez-vous que le processus de sérialisation gère tous les attributs pertinents et que le processus de copie crée une copie complète si nécessaire.

        Implémentation manquante :
            La méthode open est abstraite et doit être implémentée par des sous-classes pour fournir un comportement d'ouverture spécifique pour différents types de pièces jointes.

    Questions potentielles pour une analyse plus approfondie

        Types de pièces jointes :
            Comment les différents types de pièces jointes (par exemple, fichier, image, URL) sont-ils représentés ? Existe-t-il des sous-classes spécifiques pour chaque type ?
        Considérations sur la sécurité :
            Comment les pièces jointes sont-elles gérées en toute sécurité, en particulier lorsqu'il s'agit de fichiers potentiellement malveillants ?
        Gestion des erreurs :
            Quels mécanismes de gestion des erreurs sont en place pour des opérations telles que ouvrir ou enregistrer des pièces jointes ?
        Performance :
            Existe-t-il des optimisations de performances qui peuvent être apportées, en particulier pour les pièces jointes volumineuses ou les opérations fréquentes ?

    """

    type_ = "unknown"  # Utilisé dans XML.xriter.py

    def __init__(self, location="", *args, **kwargs):
        """
        Initialise une pièce jointe avec sa localisation et l'état hérité.

        Args :
            location (str) : Le chemin de la pièce jointe.
            *args : Arguments positionnels.
            **kwargs : Attributs hérités de la copie/sérialisation.
        """
        print(
            f"DEBUG - Attachment.__init__() appelé avec location={location}, args={args}, kwargs={kwargs}"
        )
        if "subject" not in kwargs:
            # Historically the subject for file attachments was set to the
            # full location. Tests expect the subject attribute in the XML to
            # equal the attachment location, so default to location here.
            kwargs["subject"] = location

        # On extrait l’attribut propre à Attachment
        self.__location = kwargs.pop("location", location)

        # self.__location = location
        # print(f"Attachment.__init__ : Type of self.__location: {type(self.__location)}")  # Added for debugging
        # print(f"self.__location: {self.__location}")  # Added for debugging

        # # Appelle l'initialisation de la classe de base sans arguments supplémentaires
        # super().__init__()
        # Appel du constructeur parent avec les kwargs restants
        super().__init__(*args, **kwargs)

        # # Récupère le dictionnaire d'état à partir de kwargs
        # state = kwargs.pop("state", None)
        #
        # # Initialise les attributs spécifiques à Attachment à partir du dictionnaire d'état
        # if state:
        #     self.__location = state.get("location", None)  # Ou toute autre logique pour gérer l'absence de 'location'
        #
        # # autres :
        # if "subject" not in kwargs:
        #     kwargs["subject"] = location
        # # SynchronizedObject a initialisé :
        # # # self.__status = kwargs.pop("status", self.STATUS_NEW)
        # # Object a initialisé :
        # # Attribute = attribute.Attribute
        # # self.__creationDateTime = kwargs.pop("creationDateTime", None) or Now()
        # # self.__modificationDateTime = kwargs.pop("modificationDateTime", DateTime.min)
        # # self.__subject = Attribute(
        # #      kwargs.pop("subject", ""), self, self.subjectChangedEvent
        # #         )
        # # self.__description = Attribute(
        # #             kwargs.pop("description", ""), self, self.descriptionChangedEvent
        # #         )
        # # self.__fgColor = Attribute(
        # #             kwargs.pop("fgColor", None), self, self.appearanceChangedEvent
        # #         )
        # # self.__bgColor = Attribute(
        # #             kwargs.pop("bgColor", None), self, self.appearanceChangedEvent
        # #         )
        # # self.__font = Attribute(
        # #             kwargs.pop("font", None), self, self.appearanceChangedEvent
        # #         )
        # # self.__icon = Attribute(
        # #             kwargs.pop("icon", ""), self, self.appearanceChangedEvent
        # #         )
        # # self.__selectedIcon = Attribute(
        # #             kwargs.pop("selectedIcon", ""), self, self.appearanceChangedEvent)
        # # self.__ordering = Attribute(
        # #             kwargs.pop("ordering", Object._long_zero), self, self.orderingChangedEvent)
        # # self.__id = kwargs.pop("id", None) or str(uuid.uuid1())
        # super().__init__()
        # self.__location = location

        print(
            f"DEBUG - Attachment.__init__() terminé avec location={self.__location}"
        )

    def copy(self):
        """
        Crée une copie indépendante de la pièce jointe avec les mêmes attributs,
        sans perturber les méthodes comme `description()`.

        Returns :
            Attachment : Une nouvelle instance de l'attachement.
        """
        # return self.__class__(**self.__getcopystate__())
        # Obtenir l'état de l'objet sous forme de dictionnaire
        state = self.__getcopystate__()
        print(f"DEBUG - Attachment.__getcopystate__() renvoie : {state}")
        # Filtrer les clés indésirables :
        # # Clés valides à conserver — mais attention à ne pas réécraser les attributs sensibles
        # valid_keys = {
        #     'id', 'creationDateTime', 'modificationDateTime',
        #     'fgColor', 'bgColor', 'font', 'icon', 'ordering', 'selectedIcon', 'location'
        # }
        # # Filtrage pour ne pas écraser les méthodes comme description()
        # Retirer les clés qui risquent de masquer des méthodes, mais **sans les perdre**
        # On va les réinjecter via les setters juste après instanciation
        overrides = {
            key: state.pop(key)
            for key in ("subject", "description")
            if key in state
        }
        # overrides = {}
        # for key in ['subject', 'description']:
        #     if key in state:
        #         overrides[key] = state.pop(key)

        # # Filtrer les clés à garder dans le constructeur
        # # state = {k: v for k, v in state.items() if k in valid_keys}
        # constructor_state = {k: v for k, v in state.items() if k in valid_keys}

        # # Créer une nouvelle instance sans écraser les méthodes
        # new_attachment = self.__class__(**constructor_state)
        # On crée une nouvelle instance sans les attributs ambigus
        new_attachment = self.__class__(**state)

        # # # Appliquer description et subject via les méthodes prévues à cet effet
        # # new_attachment.setDescription(self.description())
        # # new_attachment.setSubject(self.subject())
        #
        # # Restaurer les attributs avec les setters pour ne pas écraser les méthodes
        # if hasattr(self, 'description') and callable(getattr(self, 'description')):
        #     new_attachment.setDescription(self.description())
        # if hasattr(self, 'subject') and callable(getattr(self, 'subject')):
        #     new_attachment.setSubject(self.subject())
        # On applique proprement les valeurs via les méthodes existantes
        if "subject" in overrides:
            new_attachment.setSubject(overrides["subject"])
        if "description" in overrides:
            new_attachment.setDescription(overrides["description"])

        # return self.__class__(**state)
        return new_attachment

    def data(self):
        """Retourne"""
        return None

    def setParent(self, parent):
        # FIXME: We shouldn't assume that pasted items are composite
        # in PasteCommand.
        pass

    def location(self):
        """Retourne l'emplacement de la pièce jointe."""
        return self.__location

    def setLocation(self, location):
        if location != self.__location:
            self.__location = location
            self.markDirty()
            pub.sendMessage(
                self.locationChangedEventType(),
                newValue=location,
                sender=self,
            )

    @classmethod
    def locationChangedEventType(class_):  # better use cls not class_
        # def locationChangedEventType(cls):  # better use cls not class_
        # class_ is a specific cls
        return "pubsub.attachment.location"

    @classmethod
    def monitoredAttributes(class_):
        # def monitoredAttributes(cls):
        return base.Object.monitoredAttributes() + ["location"]

    def open(self, workingDir=None):
        raise NotImplementedError

    # En Python 3, __cmp__ n'existe plus. Pour que les objets soient triables
    # (par exemple dans les listes de tâches), il faut définir __eq__ et __lt__
    # et utiliser @functools.total_ordering
    # qui génère automatiquement les autres opérateurs de comparaison (>, <=, etc.).
    def __cmp__(self, other):
        """Compare l'attachement avec un autre objet en fonction de leur emplacement."""
        try:
            return cmp(self.location(), other.location())
        except AttributeError:
            # return False
            return 1

    # # j'ai ajouté cette fonction
    # # à commenter ?
    # def __hash__(self):
    #     return hash(self.__location)

    # Note: We intentionally do NOT override __hash__ or __eq__ here.
    # The parent class (base.Object) provides stable ID-based hashing
    # which is required for observer registration to work correctly.
    # Using location-based hashing caused KeyError crashes when the
    # location changed after observer registration (issue #84).

    def __lt__(self, other):
        """Compare l'attachement avec un autre objet pour le tri en fonction de leur emplacement."""
        try:
            return self.location() < other.location()
        except AttributeError:
            return False

    def __getstate__(self):
        """Retourne l'état de l'attachement sous forme de dictionnaire pour la sérialisation."""
        try:
            state = super().__getstate__()
        except AttributeError:
            state = dict()
        state.update(dict(location=self.location()))
        # state.update(location=self.location())
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        """Met à jour l'état de l'attachement à partir d'un dictionnaire, en informant les auditeurs des changements."""
        try:
            super().__setstate__(state, event=event)
        except AttributeError:
            pass
        self.setLocation(state["location"])

    def __getcopystate__(self):
        """Retourne un dictionnaire avec l'emplacement mis à jour qui peut être utilisé
        lors de la création d'une copie de l'objet."""
        # return self.__getstate__()
        # Don't include id and creationDateTime - copies should get new ones
        state = super().__getcopystate__()
        state.update(dict(location=self.location()))
        return state

    def __unicode__(self):
        return self.subject()

    @classmethod
    def modificationEventTypes(class_):
        """Retourne"""
        # def modificationEventTypes(cls):
        eventTypes = super().modificationEventTypes()
        return eventTypes + [class_.locationChangedEventType()]


class FileAttachment(Attachment):
    """Représente une pièce jointe de type fichier local."""

    type_ = "file"

    def open(
        self, workingDir=None, openAttachment=openfile.openFile
    ):  # pylint: disable=W0221
        """Ouvre la pièce jointe en utilisant la fonction openAttachment spécifiée."""
        return openAttachment(self.normalizedLocation(workingDir))

    def normalizedLocation(self, workingDir=None):
        """Retourne une version normalisée de l'emplacement de la pièce jointe, en tenant compte du répertoire de travail."""
        location = self.location()
        if self.isLocalFile():
            if workingDir and not os.path.isabs(location):
                location = os.path.join(workingDir, location)
            location = os.path.normpath(location)
        return location

    def isLocalFile(self) -> bool:
        """Vérifie si la pièce jointe est un fichier local en analysant l'URL."""
        # return urlparse(self.location())[0] == ""
        return urlparse(self.location())[0] == ""


class URIAttachment(Attachment):
    type_ = "uri"

    def __init__(self, location, *args, **kwargs):
        if location.startswith("message:") and "subject" not in kwargs:
            # unresolved attribute reference settings
            if self.settings.getboolean("os_darwin", "getmailsubject"):
                subject = mailer.getSubjectOfMail(location[8:])
                if subject:
                    kwargs["subject"] = subject
            else:
                kwargs["subject"] = _("Mail.app message")
        super().__init__(location, *args, **kwargs)

    def open(self, workingDir=None):
        return openfile.openFile(self.location())


class MailAttachment(Attachment):
    type_ = "mail"

    def __init__(self, location, *args, **kwargs):
        self._readMail = kwargs.pop("readMail", mailer.readMail)
        subject, content = self._readMail(location)

        kwargs.setdefault("subject", subject)
        kwargs.setdefault("description", content)

        super().__init__(location, *args, **kwargs)

    def open(self, workingDir=None):
        return mailer.openMail(self.location())

    def read(self):
        return self._readMail(self.location())

    def data(self):
        try:
            # return file(self.location(), "rb").read()  # fichier binaire !!!
            with open(
                self.location(), "rb"
            ) as f:  # Ouvre le fichier en mode binaire
                return f.read()  # Lit et retourne le contenu du fichier
        except IOError:
            return None  # En cas d'erreur, retourne None


def AttachmentFactory(location, type_=None, *args, **kwargs):
    """
    Vérifie si l'attachement a un emplacement défini et valide
    et retourne l'attachement.
    """
    if not location:
        print(
            f"⚠️ [DEBUG] L'attachement a un emplacement vide ! kwargs={kwargs}"
        )
    else:
        print(f"✅ [DEBUG] Attachement valide : {location}")
    return None if not location else Attachment(location, *args, **kwargs)

    if not location or not isinstance(location, str):
        print(
            f"attachment.AttachmentFactory : ⚠️ WARNING - Emplacement d'attachement invalide : {location}"
        )
        return None
    if type_ is None:
        if location.startswith("URI:"):
            return URIAttachment(
                location[4:], subject=location[4:], description=location[4:]
            )
        elif location.startswith("FILE:"):
            return FileAttachment(
                location[5:], subject=location[5:], description=location[5:]
            )
        elif location.startswith("MAIL:"):
            return MailAttachment(
                location[5:], subject=location[5:], description=location[5:]
            )

        return FileAttachment(location, subject=location, description=location)

    try:
        return {
            "file": FileAttachment,
            "uri": URIAttachment,
            "mail": MailAttachment,
        }[type_](location, *args, **kwargs)
    except KeyError:
        raise TypeError("Unknown attachment type: %s" % type_)
