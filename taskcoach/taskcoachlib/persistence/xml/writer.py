# -*- coding: utf-8 -*-

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

Module `writer.py`

Ce module gère l'écriture de fichiers XML pour Task Coach.
Il inclut des classes pour l'écriture de fichiers de tâches,
de modifications et de modèles.

Ce module contient des classes et fonctions pour la sérialisation des données de Task Coach
en XML. Il génère des fichiers XML à partir des tâches, catégories, notes, et autres
données du domaine. Les classes et méthodes gèrent la structure des fichiers XML, y
compris les attributs et les relations entre les objets.

Classes principales:
    - `XMLWriter` : Écrit des fichiers XML pour les données principales (tâches, catégories, notes).
    - `ChangesXMLWriter` : Sérialise les changements entre différents appareils pour la synchronisation.
    - `TemplateXMLWriter` : Étend `XMLWriter` pour écrire des fichiers modèles.

Fonctions principales:
    - `flatten` : Formate les nœuds XML pour un rendu lisible.
    - `sortedById` : Trie les objets en fonction de leurs identifiants.

**Fonctions**

* `flatten(elem)`:
    * Ajoute des sauts de ligne pour améliorer la lisibilité du XML.
    * Gère les éléments avec ou sans texte.

**Classes**

* `PIElementTree(ET.ElementTree)`:
    * Hérite de `xml.etree.ElementTree.ElementTree` pour gérer les instructions de traitement (PI).
    * `__init__(self, pi, *args, **kwargs)`:
        * Initialise l'arbre avec une instruction de traitement.
    * `_write(self, file, node, encoding, namespaces)`:
        * Écrit l'instruction de traitement et la déclaration XML.
    * `write(self, file, encoding, *args, **kwargs)`:
        * Écrit l'arbre XML avec l'instruction de traitement.

* `sortedById(objects)`:
    * Trie une liste d'objets par leur identifiant.

* `XMLWriter(object)`:
    * Classe principale pour l'écriture de fichiers de tâches XML.
    * `__init__(self, fd, versionnr=meta.data.tskversion)`:
        * Initialise l'écrivain avec un descripteur de fichier et un numéro de version.
    * `write(self, taskList, categoryContainer, noteContainer, syncMLConfig, guid)`:
        * Écrit les tâches, les catégories, les notes, la configuration SyncML et le GUID dans un fichier XML.
    * `notesOwnedByNoteOwners(self, *collectionOfNoteOwners)`:
        * Récupère toutes les notes appartenant à des objets qui possèdent des notes.
    * `taskNode(self, parentNode, task)`:
        * Crée un nœud XML pour une tâche.
    * `recurrenceNode(self, parentNode, recurrence)`:
        * Crée un nœud XML pour une récurrence.
    * `effortNode(self, parentNode, effort)`:
        * Crée un nœud XML pour un effort.
    * `categoryNode(self, parentNode, category, *categorizableContainers)`:
        * Crée un nœud XML pour une catégorie.
    * `noteNode(self, parentNode, note)`:
        * Crée un nœud XML pour une note.
    * `__baseNode(self, parentNode, item, nodeName)`:
        * Crée un nœud XML et ajoute les attributs de base.
    * `baseNode(self, parentNode, item, nodeName)`:
        * Crée un nœud XML et ajoute les attributs communs à tous les objets de domaine.
    * `baseCompositeNode(self, parentNode, item, nodeName, childNodeFactory, childNodeFactoryArgs=())`:
        * Crée un nœud XML composite et ajoute les nœuds enfants.
    * `attachmentNode(self, parentNode, attachment)`:
        * Crée un nœud XML pour une pièce jointe.
    * `syncMLNode(self, parentNode, syncMLConfig)`:
        * Crée un nœud XML pour la configuration SyncML.
    * `__syncMLNode(self, cfg, node)`:
        * Crée des nœuds XML pour les propriétés et les enfants de la configuration SyncML.
    * `budgetAsAttribute(self, budget)`:
        * Formate un budget en tant qu'attribut de chaîne.
    * `formatDateTime(self, dateTime)`:
        * Formate une date et une heure en tant que chaîne.

* `ChangesXMLWriter(object)`:
    * Classe pour l'écriture de fichiers XML de modifications.
    * `__init__(self, fd)`:
        * Initialise l'écrivain avec un descripteur de fichier.
    * `write(self, allChanges)`:
        * Écrit les modifications dans un fichier XML.

* `TemplateXMLWriter(XMLWriter)`:
    * Classe pour l'écriture de fichiers XML de modèles.
    * `write(self, tsk)`:
        * Écrit une tâche en tant que modèle.
    * `taskNode(self, parentNode, task)`:
        * Crée un nœud XML pour une tâche de modèle.
"""

# from builtins import str
# from builtins import object
import base64
import io
import logging
import os
import sys
from taskcoachlib import meta
from taskcoachlib.domain import date, task, note, category
from xml.etree import ElementTree as eTree

log = logging.getLogger(__name__)


def flatten(elem):
    """
    Formate un élément XML pour une sortie lisible avec des sauts de ligne.

    Args :
        elem : Élément XML à formater.
    """
    if len(elem) and not elem.text:
        elem.text = "\n"
    elif elem.text:
        elem.text = "\n%s\n" % elem.text
    elem.tail = "\n"
    for child in elem:
        flatten(child)

    # to_remove = []
    # to_extend = {}
    # for child in elem:
    #     flatten(child)
    #     if not child.tag:  # C'est un commentaire ou PI
    #         continue
    #     if child.getchildren():
    #         continue
    #     if child.text is not None and '\n' in child.text:
    #         lines = [line.strip() for line in child.text.split('\n') if line.strip()]
    #         if lines:
    #             child.text = lines[0]
    #             for line in lines[1:]:
    #                 new_child = eTree.Element(child.tag)
    #                 new_child.text = line
    #                 to_extend.setdefault(elem, []).append(new_child)
    #             to_remove.append(child)
    # for el, children in to_extend.items():
    #     index = el.index(to_remove[0]) if to_remove else len(el)
    #     for i, child in enumerate(children):
    #         el.insert(index + i, child)
    # for el in to_remove:
    #     elem.remove(el)


class PIElementTree(eTree.ElementTree):
    """
    Extension de `ElementTree` pour ajouter une instruction de traitement XML personnalisée.

    Cette classe permet d'inclure une déclaration XML spécifique en tête des fichiers
    générés, notamment pour inclure des informations de version.

    Attributs :
        - `__pi` : Contenu de l'instruction de traitement XML.

    Méthodes :
        - `write` : Écrit les nœuds XML avec l'instruction de traitement personnalisée.
    """

    def __init__(self, pi, *args, **kwargs):
        """
        Initialise une instance de `PIElementTree` avec une instruction de traitement.

        Args :
            pi (str) : Instruction de traitement XML à inclure dans le fichier.
            *args :
            **kwargs :
        """
        self._root = (
            self.getroot()
        )  # Attribut utilisé dans les write des classes suivantes
        self.__pi = pi
        eTree.ElementTree.__init__(self, *args, **kwargs)

    def _write(self, file, node, encoding, namespaces):
        """
        Écrit les nœuds XML avec la déclaration de traitement en tête.

        Args :
            file : Fichier ou flux dans lequel écrire.
            node : Nœud racine à écrire.
            encoding (str) : Encodage du fichier XML.
            namespaces : Espaces de noms XML utilisés.
        """
        # Si le noeud est la racine :
        if node == self._root:
            # WTF? ElementTree does not write the encoding if it's ASCII or UTF-8...
            if encoding in ["us-ascii", "utf-8"]:
                # for encoding in ["us-ascii", "utf-8"]:
                # file.write('<?xml version="1.0" encoding="%s"?>\n' % encoding).encode(encoding)
                # file.write(f'<?xml version="1.0" encoding="{encoding}"?>\n', )
                # Check if file is in binary mode or text mode
                # Default to binary if mode cannot be determined (for wrapped file objects)
                is_binary = not (
                    hasattr(file, "mode") and "b" not in file.mode
                )
                log.debug(
                    "PIElementTree._write : Essaie d'écrire l'en-tête du fichier."
                )
                if is_binary:
                    # Binary mode: write bytes
                    try:
                        file.write(
                            f'<?xml version="1.0" encoding="{encoding}"?>\n'.encode(
                                encoding
                            )
                        )
                    except UnicodeEncodeError as e:
                        log.exception(
                            f"PIElementTree._write : Erreur en écrivant l'en-tête : {e}"
                        )
                        pass
                else:
                    # Text mode: write strings
                    file.write(
                        f'<?xml version="1.0" encoding="{encoding}"?>\n'
                    )
            # file.write(f"{self.__pi}\n".encode(encoding), )
            # Write processing instruction
            is_binary = not (hasattr(file, "mode") and "b" not in file.mode)
            if is_binary:
                try:
                    log.debug(
                        "PIElementTree._write : Essaie d'écrire la suite de l'en-tête du fichier."
                    )
                    file.write(f"{self.__pi}\n".encode(encoding))
                except UnicodeEncodeError as e:
                    log.exception(
                        f"PIElementTree._write : Erreur en écrivant la suite de l'en-tête : {e}"
                    )
                    log.info(
                        f"PIElementTree._write : L'erreur est écrite dans la suite de l'en-tête."
                    )
                    file.write(
                        f"{self.__pi}\n".encode("utf-8", errors="replace")
                    )
            else:
                file.write(self.__pi + "\n")
        # eTree.ElementTree._write(self, file, node, encoding, namespaces)  # pylint: disable=E1101
        eTree.ElementTree.write(
            self, file, node, encoding, namespaces
        )  # pylint: disable=E1101

    # def write(self, file, encoding, *args, **kwargs):  # Signature of method 'PIElementTree.write()' does not match signature of the base method in class 'ElementTree'
    # def write(self, file, encoding, *args, **kwargs):  # Signature of Nonemethod 'PIElementTree.write()' does not match signature of the base method in class 'ElementTree'
    def write(
        self,
        file,
        encoding: str | None = None,
        xml_declaration: bool | None = None,
        default_namespace: str | None = None,
        method: str | None = None,
        *args,
        short_empty_elements: bool = True,
        **kwargs,
    ) -> None:
        """
        Écrit l'arbre XML avec l'instruction de traitement.

        Args :
            file :
            encoding :
            xml_declaration :
            default_namespace :
            method :
            *args :
            **kwargs :
            short_empty_elements

        Returns :

        """
        # Mais il est inutile d'ajouter **kwargs deux fois !
        if encoding is None:
            encoding = "utf-8"
        # Check if file is in binary mode or text mode
        # Default to binary if mode cannot be determined (for wrapped file objects)
        is_binary = not (hasattr(file, "mode") and "b" not in file.mode)
        if sys.version_info >= (2, 7):
            # file.write(f"<?xml version='1.0' encoding='{encoding}'?>\n".encode(encoding), )
            # # file.write(f"<?xml version='1.0' encoding='{encoding}'?>\n")
            # # content = f"<?xml version='1.0' encoding='{encoding}'?>\n".encode(encoding)
            # # file.write(content.decode(encoding))
            # # file.write((self.__pi + "\n").encode(encoding), )
            # # file.write(f"{self.__pi}\n")
            # file.write(f"{self.__pi}\n".encode(encoding), )
            # # content = (self.__pi + "\n").encode(encoding)
            # # file.write(content.decode(encoding))
            # Write XML declaration and processing instruction
            if is_binary:
                # Binary mode: write bytes
                try:
                    log.debug(
                        "PIElementTree.write : Essaie d'écrire l'instruction de traitement du fichier."
                    )
                    file.write(
                        f"<?xml version='1.0' encoding='{encoding}'?>\n".encode(
                            encoding
                        )
                    )
                    file.write(f"{self.__pi}\n".encode(encoding))
                    kwargs["xml_declaration"] = False
                    eTree.ElementTree.write(
                        self, file, encoding, *args, **kwargs
                    )
                except UnicodeEncodeError as e:
                    log.exception(
                        f"PIElementTree.write : Erreur en écrivant l'instruction de traitement : {e}"
                    )
                    file.write(
                        f"<?xml version='1.0' encoding='utf-8'?>\n".encode(
                            "utf-8", errors="replace"
                        )
                    )
                    file.write(
                        f"{self.__pi}\n".encode("utf-8", errors="replace")
                    )
            else:
                # Text mode: write strings
                file.write('<?xml version="1.0" encoding="%s"?>\n' % encoding)
                file.write(self.__pi + "\n")
                kwargs["xml_declaration"] = False
                # Use 'unicode' encoding to write strings instead of bytes
                # ET.ElementTree.write(self, file, "unicode", *args, **kwargs)
                eTree.ElementTree.write(self, file, "unicode", *args, **kwargs)

        #     kwargs["xml_declaration"] = False
        # eTree.ElementTree.write(self, file, encoding=encoding, *args, **kwargs)
        # # eTree.ElementTree.write(self, file, encoding="unicode", *args, **kwargs)
        # if isinstance(file, io.BytesIO):
        #     eTree.ElementTree.write(self, file, encoding="utf-8", *args, **kwargs)
        # else:
        #     eTree.ElementTree.write(self, file, encoding="unicode", *args, **kwargs)


def sortedById(objects):
    """
    Trie une liste d'objets en fonction de leurs identifiants.

    Args :
        objects (list) : Liste d'objets à trier.

    Returns :
        (list) : Liste triée d'objets.
    """
    log.debug(
        f"Trie d'une liste d'objets {objects} en fonction de leurs identifiants."
    )
    # # s = [(obj.id(), obj) for obj in objects]
    # # s.sort()
    # # return [obj for dummy_id, obj in s]
    # return sorted(objects, key=lambda item: item.id())
    # On convertit l'ID en string (ou une chaîne vide si None) pour permettre la comparaison
    return sorted(objects, key=lambda item: str(item.id() or ""))


class XMLWriter(object):
    """
    Génère des fichiers XML pour les données principales de Task Coach.

    Cette classe sérialise les tâches, catégories, notes et autres objets dans un
    fichier XML en respectant les relations hiérarchiques et les attributs.

    Attributs :
        - `maxDateTime` : Constante représentant la date maximale pour les comparaisons.
        - `__fd` : Flux dans lequel le contenu XML sera écrit.
        - `__versionnr` : Numéro de version des données.

    Méthodes principales :
        - `write` : Génère un fichier XML à partir des objets de domaine.
        - `taskNode` : Génère un nœud XML pour une tâche.
        - `categoryNode` : Génère un nœud XML pour une catégorie.
        - `noteNode` : Génère un nœud XML pour une note.
        - `effortNode` : Génère un nœud XML pour un effort.
    """

    maxDateTime = date.DateTime()
    # maxDateTime = eTree.Element("maxDateTime") # Peut-être initialiser un élément vide ?

    def __init__(self, fd, versionnr=meta.data.tskversion):
        """
        Initialise une instance de `XMLWriter`.

        Args :
            fd : Flux ou fichier de destination dans lequel le contenu XML sera écrit.
            versionnr (int) : Numéro de version des données.
        """
        # self.__fd doit être initialisé comme un buffer d'écriture (par exemple, io.StringIO ou io.BytesIO).
        self.__fd = fd
        self.__versionnr = versionnr

    def write(
        self, taskList, categoryContainer, noteContainer, syncMLConfig, guid
    ):
        """
        Écrit les données de domaine dans un fichier XML.

        Args :
            taskList : Liste des tâches.
            categoryContainer : Conteneur de catégories.
            noteContainer : Conteneur de notes.
            syncMLConfig : Configuration SyncML pour la synchronisation.
            guid (str) : Identifiant global unique pour le fichier.
        """
        # Création de root l'élément de base XML avec le nom <tasks>.
        root = eTree.Element("tasks")

        # Sécurité au cas où rootItems() renvoie None
        rootTasks = taskList.rootItems() or []

        # Pour chaque rootTask dans la liste des rootItems de la liste de tâche triée par id.
        # for rootTask in sortedById(taskList.rootItems()):
        for rootTask in sortedById(rootTasks):
            # Créer des attributs, les dictionnaires rootTask contenant les attributs de l'élément nœud "task" dans l'élément parent root.
            self.taskNode(root, rootTask)

        ownedNotes = self.notesOwnedByNoteOwners(taskList, categoryContainer)

        # Sécurité au cas où rootItems() renvoie None
        rootCategories = categoryContainer.rootItems() or []
        # for rootCategory in sortedById(categoryContainer.rootItems()):
        for rootCategory in sortedById(rootCategories):
            self.categoryNode(
                root, rootCategory, taskList, noteContainer, ownedNotes
            )

        # Sécurité au cas où rootItems() renvoie None
        rootNotes = noteContainer.rootItems() or []
        # for rootNote in sortedById(noteContainer.rootItems()):
        for rootNote in sortedById(rootNotes):
            if rootNote not in ownedNotes:
                self.noteNode(root, rootNote)

        if syncMLConfig:
            self.syncMLNode(root, syncMLConfig)
        if guid:
            eTree.SubElement(root, "guid").text = guid

        # Formatter le nœud principal de façon lisible :
        flatten(root)
        # Convertir cette ligne PIElementTree :
        # PIElementTree(
        #     '<?taskcoach release="%s" tskversion="%d"?>\n'
        #     % (meta.data.version, self.__versionnr),
        #     root,
        # ).write(self.__fd, "utf-8")
        # PIElementTree(
        #     f'<?taskcoach release="{meta.data.version}" tskversion="{self.__versionnr:d}"?>\n',
        #     root,
        # ).write(self.__fd, encoding="utf-8")
        pi_content = f'<?taskcoach release="{meta.data.version}" tskversion="{self.__versionnr}"?>\n'
        log.debug(f"XMLWriter.write : Après flatten, root = {root}")
        tree = eTree.ElementTree(root)
        log.debug(f"XMLWriter.write : tree = {tree}")
        tree_str = eTree.tostring(
            tree.getroot(), encoding="utf-8", xml_declaration=False
        ).decode("utf-8")
        # xml_bytes = ET.tostring(tree.getroot(), encoding='utf-8', xml_declaration=False)
        log.debug(f"XMLWriter.write : tree_str = {tree_str}")
        log.debug(f"XMLWriter.write : Écriture du fichier {self.__fd.name}.")
        self.__fd.write(pi_content + tree_str)
        # try:
        #     self.__fd.write(pi_content.encode('utf-8'))
        #     self.__fd.write(xml_bytes)
        # except AttributeError:
        #     log.error("XMLWriter.write : Le descripteur de fichier ne supporte pas l'écriture de bytes.")
        #     raise

    # @staticmethod
    def notesOwnedByNoteOwners(self, *collectionOfNoteOwners):
        """
        Récupère toutes les notes appartenant à des objets qui possèdent des notes.

        Args :
            *collectionOfNoteOwners :

        Returns :

        """
        notes = []
        for noteOwners in collectionOfNoteOwners:
            for noteOwner in noteOwners:
                notes.extend(noteOwner.notes(recursive=True))
        return notes

    def taskNode(self, parentNode, task):  # pylint: disable=W0621
        """
        Création des attributs, les dictionnaires contenant les attributs de l'élément node "task" dans l'élément parent parentNode.

        Args :
            parentNode : Element parent.
            task : Element noeud "task" auquel rajouter les dictionnaires d'attributs.

        Returns :
            node (Element) :

        """
        # vous avez déjà un nettoyage à la fin, mais il est préférable de s'assurer
        # que les valeurs insérées sont toujours des chaînes de caractères
        maxDateTime = self.maxDateTime
        node = self.baseCompositeNode(parentNode, task, "task", self.taskNode)
        node.attrib["status"] = str(task.getStatus())
        if task.plannedStartDateTime() != maxDateTime:
            node.attrib["plannedstartdate"] = str(task.plannedStartDateTime())
        if task.dueDateTime() != maxDateTime:
            node.attrib["duedate"] = str(task.dueDateTime())
        if task.actualStartDateTime() != maxDateTime:
            node.attrib["actualstartdate"] = str(task.actualStartDateTime())
        if task.completionDateTime() != maxDateTime:
            node.attrib["completiondate"] = str(task.completionDateTime())
        if task.percentageComplete():
            node.attrib["percentageComplete"] = str(task.percentageComplete())
        if task.recurrence():
            self.recurrenceNode(node, task.recurrence())
        if task.budget() != date.TimeDelta():
            # node.attrib["budget"] = self.budgetAsAttribute(task.budget())
            node.attrib["budget"] = str(self.budgetAsAttribute(task.budget()))
        if task.plannedDuration() != date.TimeDelta():
            # node.attrib["plannedDuration"] = self.budgetAsAttribute(
            node.attrib["plannedDuration"] = str(
                self.budgetAsAttribute(task.plannedDuration())
            )

        if task.plannedDurationMode() != "implicit":
            # node.attrib["plannedDurationMode"] = task.plannedDurationMode()
            node.attrib["plannedDurationMode"] = str(
                task.plannedDurationMode()
            )
        if task.priority():
            node.attrib["priority"] = str(task.priority())
        if task.hourlyFee():
            node.attrib["hourlyFee"] = str(task.hourlyFee())
        if task.fixedFee():
            node.attrib["fixedFee"] = str(task.fixedFee())
        reminder = task.reminder()
        if reminder != maxDateTime and reminder is not None:  # is not None !
            node.attrib["reminder"] = str(reminder)
            reminderBeforeSnooze = task.reminder(includeSnooze=False)
            if (
                reminderBeforeSnooze is not None  # is not None
                and reminderBeforeSnooze < task.reminder()
            ):
                node.attrib["reminderBeforeSnooze"] = str(reminderBeforeSnooze)
        # Assurez-vous que les IDs des prérequis ne sont pas None
        prerequisiteIds = " ".join(
            [
                # prerequisite.id()
                str(prerequisite.id())
                for prerequisite in sortedById(task.prerequisites())
            ]
        )
        if prerequisiteIds:
            # node.attrib["prerequisites"] = prerequisiteIds
            node.attrib["prerequisites"] = prerequisiteIds
        if (
            task.shouldMarkCompletedWhenAllChildrenCompleted() is not None
        ):  # is not None !
            node.attrib["shouldMarkCompletedWhenAllChildrenCompleted"] = str(
                task.shouldMarkCompletedWhenAllChildrenCompleted()
            )
        for effort in sortedById(task.efforts()):
            self.effortNode(node, effort)
        for eachNote in sortedById(task.notes()):
            self.noteNode(node, eachNote)
        for attachment in sortedById(task.attachments()):
            self.attachmentNode(node, attachment)
        # Très important :
        # Mesure de sécurité globale pour ce nœud :
        # On retire après coup toute valeur qui serait restée à None
        for key, val in list(node.attrib.items()):
            if val is None:
                del node.attrib[key]
            else:
                node.attrib[key] = str(
                    val
                )  # Forcer la conversion en string ici pour ElementTree
        return node

    def recurrenceNode(self, parentNode, recurrence):
        """
        Crée un nœud XML pour une récurrence.

        Args :
            parentNode :
            recurrence :

        Returns :

        """
        attrs = dict(unit=recurrence.unit)
        if recurrence.amount > 1:
            attrs["amount"] = str(recurrence.amount)
        if recurrence.count > 0:
            attrs["count"] = str(recurrence.count)
        if recurrence.max > 0:
            attrs["max"] = str(recurrence.max)
        if recurrence.stop_datetime != self.maxDateTime:
            attrs["stop_datetime"] = str(recurrence.stop_datetime)
        if recurrence.sameWeekday:
            attrs["sameWeekday"] = "True"
        if recurrence.recurBasedOnCompletion:
            attrs["recurBasedOnCompletion"] = "True"
        if recurrence.weekdays:
            attrs["weekdays"] = ",".join(str(d) for d in recurrence.weekdays)
        return eTree.SubElement(parentNode, "recurrence", attrs)

    def effortNode(self, parentNode, effort):
        """
        Crée un nœud XML pour un effort.

        Args :
            parentNode :
            effort :

        Returns :

        """
        formattedStart = self.formatDateTime(effort.getStart())
        attrs = dict(
            id=effort.id(),
            status=str(effort.getStatus()),
            start=formattedStart,
        )
        stop = effort.getStop()
        if stop is not None:
            formattedStop = self.formatDateTime(stop)
            if formattedStop == formattedStart:
                # Make sure the effort duration is at least one second
                formattedStop = self.formatDateTime(stop + date.ONE_SECOND)
            attrs["stop"] = formattedStop
        entryMode = effort.entryMode()
        if entryMode and entryMode != "standard":
            attrs["entryMode"] = entryMode
        node = eTree.SubElement(parentNode, "effort", attrs)
        if effort.description():
            eTree.SubElement(node, "description").text = effort.description()
        return node

    def categoryNode(
        self, parentNode, category, *categorizableContainers
    ):  # pylint: disable=W0621
        """
        Crée un nœud XML pour une catégorie.

        Args :
            parentNode : Nœud parent.
            category : Catégorie.
            *categorizableContainers : Conteneur des catégorisables.

        Returns :

        """

        def inCategorizableContainer(categorizable):
            """
            Renvoie Vrai si categorizable est dans le conteneur des catégorisables.

            Args :
                categorizable : Objet catégorisable à vérifier.

            Returns :
                (bool) : categorizable est dans le conteneur des catégorisables ?
            """
            for container in categorizableContainers:
                if categorizable in container:
                    return True
            return False

        node = self.baseCompositeNode(
            parentNode,
            category,
            "category",
            self.categoryNode,
            categorizableContainers,
        )
        if category.isFiltered():
            node.attrib["filtered"] = str(category.isFiltered())
        if category.hasExclusiveSubcategories():
            node.attrib["exclusiveSubcategories"] = str(
                category.hasExclusiveSubcategories()
            )
        for eachNote in sortedById(category.notes()):
            self.noteNode(node, eachNote)
        for attachment in sortedById(category.attachments()):
            self.attachmentNode(node, attachment)
        # Make sure the categorizables referenced are actually in the
        # categorizableContainer, i.e. they are not deleted
        categorizableIds = " ".join(
            [
                categorizable.id()
                for categorizable in sortedById(category.categorizables())
                if inCategorizableContainer(categorizable)
            ]
        )
        if categorizableIds:
            node.attrib["categorizables"] = categorizableIds
        return node

    def noteNode(self, parentNode, note):  # pylint: disable=W0621
        """
        Crée un nœud XML pour une note.

        Args :
            parentNode :
            note :

        Returns :

        """
        node = self.baseCompositeNode(parentNode, note, "note", self.noteNode)
        for attachment in sortedById(note.attachments()):
            self.attachmentNode(node, attachment)
        return node

    # @staticmethod
    def __baseNode(self, parentNode, item, nodeName):
        """
        Utilise xml.etree.ElementTree.SubElement pour créer un sous-Element de base.

        Args :
            parentNode : Element parent.
            item : Dictionnaire contenant l'id et le status et autres à ajouter à l'élément.
            nodeName : Nom de l'élément à créer.

        Returns :
            node (Element) : Sous-Element créé contenant l'Element parent,
                             le Nom de l'Element, le dictionnaire avec des morceaux d'item{id=;status=}
                             et les dates de création, de modification, le sujet et la description.

        """
        node = eTree.SubElement(
            parentNode,
            nodeName,
            dict(id=item.id(), status=str(item.getStatus())),
        )
        if item.creationDateTime() > date.DateTime.min:
            node.attrib["creationDateTime"] = str(item.creationDateTime())
        if item.modificationDateTime() > date.DateTime.min:
            node.attrib["modificationDateTime"] = str(
                item.modificationDateTime()
            )
        if item.subject():
            node.attrib["subject"] = item.subject()
        if item.description():
            eTree.SubElement(node, "description").text = item.description()
        # Mesure de sécurité globale pour ce nœud :
        # On retire après coup toute valeur qui serait restée à None
        for key, val in list(node.attrib.items()):
            if val is None:
                del node.attrib[key]
        return node

    def baseNode(self, parentNode, item, nodeName):
        """Créer un nœud et ajouter les attributs partagés par tous les objets de domaine,
        tels que l'identifiant, le sujet et la description.

        Args :
            parentNode : Nœud Element parent.
            item : Dictionnaire contenant les éléments à ajouter à l'Element.
            nodeName : Nom de l'élément.

        Returns :
            node (Element) : Sous-Element à utiliser contenant l'Element parent,
                             le Nom de l'Element, le dictionnaire avec des morceaux d'item{id=;status=}
                             et les dates de création, de modification, le sujet et la description, plus
                             les éléments ajoutés (fgcolor, bgcolor, font, icon, selectIcon et ordering).
        """
        node = self.__baseNode(parentNode, item, nodeName)
        if item.foregroundColor():
            node.attrib["fgColor"] = str(item.foregroundColor())
        if item.backgroundColor():
            node.attrib["bgColor"] = str(item.backgroundColor())
        if item.font():
            node.attrib["font"] = str(item.font().GetNativeFontInfoDesc())
        if item.icon():
            node.attrib["icon"] = str(item.icon())
        if item.selectedIcon():
            node.attrib["selectedIcon"] = str(item.selectedIcon())
        if item.ordering():
            node.attrib["ordering"] = str(item.ordering())
        return node

    def baseCompositeNode(
        self,
        parentNode,
        item,
        nodeName,
        childNodeFactory,
        childNodeFactoryArgs=(),
    ):
        """Identique à baseNode, mais crée également des nœuds enfants au moyen de
        childNodeFactory."""
        node = self.__baseNode(parentNode, item, nodeName)
        if item.foregroundColor():
            node.attrib["fgColor"] = str(item.foregroundColor())
        if item.backgroundColor():
            node.attrib["bgColor"] = str(item.backgroundColor())
        if item.font():
            node.attrib["font"] = str(item.font().GetNativeFontInfoDesc())
        if item.icon():
            node.attrib["icon"] = str(item.icon())
        if item.selectedIcon():
            node.attrib["selectedIcon"] = str(item.selectedIcon())
        if item.ordering():
            node.attrib["ordering"] = str(item.ordering())
        # Attribut ajouté en plus :
        if item.expandedContexts():
            node.attrib["expandedContexts"] = str(
                tuple(sorted(item.expandedContexts()))
            )
        for child in sortedById(item.children()):
            childNodeFactory(
                node, child, *childNodeFactoryArgs
            )  # pylint: disable=W0142
        return node

    def attachmentNode(self, parentNode, attachment):
        """
        Utilise baseNode pour créer un noeud.
        Configure l'attribut "type" avec l'attribut type_ de piece jointe.

        Args :
            parentNode : Element parent.
            attachment : Piece jointe à ajouter.

        Returns :
            node (Element) : Sous-Element pièce jointe à utiliser.
        """
        node = self.baseNode(parentNode, attachment, "attachment")
        node.attrib["type"] = attachment.type_
        data = attachment.data()
        if data is None:
            node.attrib["location"] = attachment.location()
        else:
            try:
                eTree.SubElement(
                    node,
                    "data",
                    dict(
                        extension=os.path.splitext(attachment.location())[-1]
                    ),
                    # ).text = data.encode("base64")
                ).text = base64.b64encode(data)
            except Exception:
                log.error(f"eTree ne support pas base64 !")
                eTree.SubElement(
                    node,
                    "data",
                    dict(
                        extension=os.path.splitext(attachment.location())[-1]
                    ),
                ).text = data.encode("base64")
        for eachNote in sortedById(attachment.notes()):
            self.noteNode(node, eachNote)
        return node

    def syncMLNode(self, parentNode, syncMLConfig):
        """
        Crée un nœud XML pour la configuration SyncML.

        Args :
            parentNode :
            syncMLConfig :

        Returns :

        """
        node = eTree.SubElement(parentNode, "syncmlconfig")
        self.__syncMLNode(syncMLConfig, node)
        return node

    def __syncMLNode(self, cfg, node):
        """
        Crée des nœuds XML pour les propriétés et les enfants de la configuration SyncML.

        Args :
            cfg :
            node :

        Returns :

        """
        for name, value in cfg.properties():
            eTree.SubElement(node, "property", dict(name=name)).text = value

        for childCfg in cfg.children():
            child = eTree.SubElement(node, childCfg.name)
            self.__syncMLNode(childCfg, child)

    # @staticmethod
    def budgetAsAttribute(self, budget):
        """
        Formate un budget en tant qu'attribut de chaîne.

        Args :
            budget :

        Returns :

        """
        return "%d:%02d:%02d" % budget.hoursMinutesSeconds()

    # @staticmethod
    def formatDateTime(self, dateTime):
        """
        Formate une date et une heure en tant que chaîne.

        Args :
            dateTime :

        Returns :

        """
        return dateTime.strftime("%Y-%m-%d %H:%M:%S")


class ChangesXMLWriter(object):
    """
    Sérialise les changements d'état pour la synchronisation entre appareils.

    Attributs :
        - `__fd` : Flux ou fichier dans lequel écrire les changements.

    Méthodes :
        - `write` : Écrit les changements dans un fichier XML.
    """

    # Il faut s'assurer que si un objet n'a pas de changements,
    # on ne définit pas son texte à None.
    # On peut soit sauter le nœud, soit mettre une chaîne vide.

    def __init__(self, fd):
        self.__fd = fd

    def write(self, allChanges):
        """
        Écrit les modifications dans un fichier XML.

        Args :
            allChanges (dict) : Dictionnaire contenant les changements par appareil.
        """
        root = eTree.Element("changes")
        if allChanges:
            for devName, monitor in allChanges.items():
                # for devName, monitor in list(allChanges.items()):
                devNode = eTree.SubElement(root, "device")
                # devNode.attrib["guid"] = monitor.guid()
                devNode.attrib["guid"] = str(
                    monitor.guid() or ""
                )  # Sécurité : forcer str et gérer le None

                # Dans la boucle qui crée les nœuds <obj>,
                # si changes est vide ou contient une valeur non-string,
                # join ou tostring échouent.
                for id_, changes in list(monitor.allChanges().items()):
                    objNode = eTree.SubElement(devNode, "obj")
                    # objNode.attrib["id"] = id_
                    objNode.attrib["id"] = str(id_ or "")  # Sécurité str()
                    # if changes:
                    #     objNode.text = ",".join(list(changes))
                    # On ne crée le nœud que s'il y a vraiment des changements
                    if changes:
                        # objNode = eTree.SubElement(devNode, "obj")
                        # objNode.attrib["id"] = str(id_)
                        # On s'assure que le résultat de join est une chaîne
                        objNode.text = ",".join([str(c) for c in changes])
                    else:
                        # Optionnel : si vous voulez le nœud vide sans erreur
                        # objNode = eTree.SubElement(devNode, "obj")
                        # objNode.attrib["id"] = str(id_)
                        # objNode.text = ""
                        objNode.text = (
                            ""  # Jamais None pour éviter le crash au tostring
                        )
                        # pass

        tree = eTree.ElementTree(root)
        # # tree.write(self.__fd)
        # # tree.write(self.__fd, encoding="unicode")  # Sauf que ce n'est pas de l'unicode mais de l'utf-8 !
        # # tree.write(self.__fd, encoding="utf-8")
        log.info(
            f"ChangesXMLWriter.write : Écriture du fichier {self.__fd.name}."
        )
        # tree.write(self.__fd)  # Essayer avec tostring !
        # log.debug(f"ChangesXMLWriter.write : DEBUG - Contenu du fichier écrit:\n{self.__fd.getvalue()}")
        # tree_as_bytes = eTree.tostring(root, encoding="utf-8")
        # xml_bytes = eTree.tostring(tree.getroot(), encoding='utf-8', xml_declaration=False)
        # tree_str = eTree.tostring(tree.getroot(), encoding='utf-8', xml_declaration=False).decode('utf-8')
        tree_str = eTree.tostring(
            tree.getroot(), encoding="utf-8", xml_declaration=False
        )
        # self.__fd.write(tree_as_bytes)
        # self.__fd.write(xml_bytes)
        # self.__fd.write(tree_str)
        # # Il est nécessaire d'encoder la chaîne tree_str en bytes avant de l'écrire dans le fichier
        # self.__fd.write(tree_str.encode('utf-8'))
        # # L'erreur AttributeError: 'bytes' object has no attribute 'encode'. Did you mean: 'decode'? indique que vous essayez d'encoder un objet qui est déjà de type bytes. Cela se produit à la ligne 813 du fichier persistence/xml/writer.py 1 2.
        # # Cela suggère que tree_str est de type bytes au lieu de str à ce moment-là.
        # Cependant, cette modification pourrait ne pas être suffisante, car elle ne prend pas en compte le mode d'ouverture du fichier (self.__fd).
        # if isinstance(self.__fd, io.TextIOWrapper):
        #     # tree_str = tree_str.decode('utf-8')
        #     # self.__fd.write(tree_str)
        #     # Cette modification décode tree_str en utilisant l'encodage UTF-8 seulement si self.__fd est un fichier texte.
        #     self.__fd.write(tree_str.decode("utf-8"))
        # else:
        #     self.__fd.write(tree_str)
        # Cette modification vérifie si le fichier a été ouvert en mode texte ou binaire. Si c'est un fichier texte, alors on décode tree_str avant d'écrire. Sinon, on écrit directement les bytes.
        # De plus, il est important de vérifier le mode d'ouverture du fichier dans taskfile.py. Il faut s'assurer que les fichiers .delta sont ouverts en mode texte ("w") avec l'encodage UTF-8 lors de l'écriture des changements.
        try:
            # Essayer d'écrire des bytes directement (cas binaire)
            self.__fd.write(tree_str)  # Plante ici !
        # except TypeError:
        #     # Si ça échoue (attendu str, reçu bytes), alors décoder et écrire
        #     self.__fd.write(tree_str.decode("utf-8"))
        except Exception as e:
            # On logue l'erreur réelle 'e' pour comprendre pourquoi l'écriture a échoué
            log.error(
                f"ChangesXMLWriter.write : Erreur lors de la sérialisation/écriture : {e}"
            )

        log.info(
            f"ChangesXMLWriter.write : Tentative de lecture du fichier {self.__fd.name} :"
        )
        if hasattr(self.__fd, "getvalue"):  # StringIO ou BytesIO
            log.info(
                f"ChangesXMLWriter.write : Contenu du fichier écrit:\n{self.__fd.getvalue()}"
            )
        # else:  # Fichier ouvert en mode écriture
        # elif "r" in self.__fd.mode or "+" in self.__fd.mode:  # Si le fichier supporte la lecture
        elif hasattr(self.__fd, "mode") and (
            "r" in self.__fd.mode or "+" in self.__fd.mode
        ):  # Si le fichier supporte la lecture
            # AttributeError: 'SafeWriteFile' object has no attribute 'mode'
            self.__fd.seek(0)  # Repositionne le curseur au début
            log.info(
                f"ChangesXMLWriter.write : Contenu du fichier écrit:\n{self.__fd.read()}"
            )
            self.__fd.seek(0)  # Remet le curseur au début du fichier
        # Au lieu de tester si le fichier est lisible (ce qui échoue en mode 'w'),
        # on vérifie juste s'il est ouvert.
        elif not hasattr(self.__fd, "write"):
            log.error(
                f"ChangesXMLWriter.write : Le descripteur n'est pas prêt pour l'écriture."
            )
            return
        # Supprimez ou commentez la vérification qui déclenche le Warning :
        # if not self.__fd.readable(): <--- C'est ça qui pose problème
        else:
            # log.warning(
            #     f"ChangesXMLWriter.write : ⚠️ Impossible de lire {self.__fd.name}, mode : {self.__fd.mode}"
            # )
            fd_name = getattr(self.__fd, "name", "Unknown")
            fd_mode = getattr(self.__fd, "mode", "Unknown")
            log.warning(
                f"ChangesXMLWriter.write : ⚠️ Impossible de lire {fd_name}, mode : {fd_mode}"
            )


class TemplateXMLWriter(XMLWriter):
    """
    Étend `XMLWriter` pour écrire des modèles de tâches en XML.

    Méthodes principales :
        - `write` : Écrit un modèle de tâche en XML.
        - `taskNode` : Génère un nœud XML pour une tâche avec des attributs spécifiques aux modèles.
    """

    # def write(self, tsk):  # pylint: disable=W0221 # Méthode de XMLWrite avec signature différente -> à changer !?
    def write(self, tsk, categoryContainer, noteContainer, syncMLConfig, guid):
        # def write(self, tsk, categoryContainer=None,
        #           noteContainer=None, syncMLConfig=None, guid=None):
        """
        Sérialise une tâche en tant que modèle XML.

        Args :
            tsk : Tâche à sérialiser.
            categoryContainer :
            noteContainer :
            syncMLConfig :
            guid :
        """
        super().write(
            task.TaskList([tsk]),
            category.CategoryList(),
            note.NoteContainer(),
            None,
            None,
        )

    def taskNode(self, parentNode, tsk):  # pylint: disable=W0621
        """
        Génère un nœud XML pour une tâche, avec des attributs spécifiques aux modèles.

        Args :
            parentNode : Nœud parent pour la tâche.
            tsk : Tâche à sérialiser en XML.

        Returns :
            node (Element) : Nœud XML créé.
        """
        log.debug(
            f"TemplateXMLWriter.taskNode : Génération d'un noeud avec parentNode={parentNode} et task={tsk}."
        )
        node = super().taskNode(parentNode, tsk)

        for name, getter in [
            ("plannedstartdate", "plannedStartDateTime"),
            ("duedate", "dueDateTime"),
            ("completiondate", "completionDateTime"),
            ("reminder", "reminder"),
        ]:
            # if hasattr(tsk, name + "tmpl"):
            #     value = getattr(tsk, name + "tmpl") or None
            # else:
            log.debug(
                f"TemplateXMLWrite.taskNode : Pour name={name} et getter={getter}"
            )
            dateTime = getattr(tsk, getter)()
            log.debug(f"TemplateXMLWrite.taskNode : dateTime = {dateTime}")
            # Si on récupère un objet Attribute, on prend sa valeur
            if hasattr(dateTime, "value"):
                dateTime = dateTime.value()
                log.debug(
                    f"TemplateXMLWriter.taskNode : Récupération de l'attribut dateTime.value : dateTime = {dateTime}."
                )
            if dateTime not in (None, date.DateTime()):
                log.debug(
                    f"dateTime {dateTime} n'est ni None, ni {date.DateTime()}."
                )
                delta = dateTime - date.Now()
                minutes = delta.days * 24 * 60 + round(delta.seconds / 60)
                # minutes = delta.days * 24 * 60 + (delta.seconds // 60)
                if minutes < 0:
                    # value = "%d minutes ago" % -minutes
                    value = f"{-minutes:d} minutes ago"
                else:
                    # value = "%d minutes from now" % minutes
                    value = f"{minutes:d} minutes from now"
            else:
                value = None

        if value is None:
            log.debug("value est None.")
            if name in node.attrib:

                del node.attrib[name]
        # else:
        #     # node.attrib[name + "tmpl"] = value
        #     node.attrib[name] = value
        log.debug(f"TemplateXMLWriter.taskNode: Renvoie node={node} !")
        return node
