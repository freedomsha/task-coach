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
# from io import open as file  # j'ai ajouté
from io import open  # j'ai ajouté
import logging
import os
import pickle
import tempfile
import shutil

# try:
from pubsub import pub

# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
from taskcoachlib.persistence.xml import TemplateXMLWriter, TemplateXMLReader

log = logging.getLogger(__name__)


class TemplateList(object):
    """
    Classe
    """

    # def __init__(self, path, TemplateReader=TemplateXMLReader, openFile=file):
    def __init__(self, path, TemplateReader=TemplateXMLReader, openFile=open):
        self._path = path
        self._templates = self._readTemplates(TemplateReader, openFile)
        self._toDelete = []

    def _readTemplates(self, TemplateReader, openFile):
        log.debug(
            f"TemplateList._readTemplates : reading templates from {self._path}"
        )
        templates = []
        for filename in self._templateFilenames():
            # log.debug(f"TemplateList._readTemplates : reading template {filename}")
            template = self._readTemplate(filename, TemplateReader, openFile)
            # log.debug(f"TemplateList._readTemplates : read template {filename} : {template}")
            if template:
                log.debug(
                    f"TemplateList._readTemplates : adding template {filename} to list [{template}]"
                )
                templates.append((template, filename))
                # log.debug(f"TemplateList._readTemplates : added template {filename} to list")
        log.debug(
            f"TemplateList._readTemplates : finished reading templates from {self._path} : self._templates={templates}"
        )
        return templates

    def _readTemplate(self, filename, TemplateReader, openFile):
        # Je vais changer "r", encoding="utf-8" en "rb" dans _readTemplate.
        # Je vais aussi vérifier addTemplate qui ouvre en écriture.
        # Si on lit en binaire, il vaut mieux écrire en binaire ou s'assurer que TemplateXMLWriter gère le mode texte.
        # TemplateXMLWriter utilise probablement XMLWriter qui utilise ET.ElementTree.write.
        # ET.write attend généralement un fichier ouvert en binaire ou gère l'encodage.
        log.debug(
            f"TemplateList._readTemplate : reading template {filename} from {self._path}."
        )
        try:
            log.debug(
                f"TemplateList._readTemplate : opening file {filename} for reading."
            )
            # fd = openFile(
            #     os.path.join(self._path, filename), "r", encoding="utf-8"
            # )
            fd = openFile(os.path.join(self._path, filename), "rb")
            # log.debug(f"TemplateList._readTemplate : opened file {filename} for reading.")
        except IOError as e:
            log.error(
                f"TemplateList._readTemplate : ERROR! Opening file {filename} for reading: {e}"
            )
            return
        try:
            log.debug(
                f"TemplateList._readTemplate : reading template {filename} using TemplateReader."
            )
            return TemplateReader(fd).read()
        except Exception as e:  # else ?
            log.error(
                f"TemplateList._readTemplate : ERROR! Reading template {filename}: {e}"
            )
        finally:
            fd.close()

    def _templateFilenames(self):
        """

        Returns:

        """
        log.debug(
            f"TemplateList._templateFilenames : listing template filenames in {self._path}."
        )
        if not os.path.exists(self._path):
            log.debug(
                f"TemplateList._templateFilenames : path {self._path} does not exist. Returning empty list."
            )
            return []
        filenames = [
            name
            for name in os.listdir(self._path)
            if name.endswith(".tsktmpl")
            and os.path.exists(os.path.join(self._path, name))
        ]
        log.debug(
            f"TemplateList._templateFilenames : found template filenames in {self._path} : {filenames}"
        )

        listName = os.path.join(self._path, "list.pickle")
        log.debug(
            f"TemplateList._templateFilenames : looking for list file {listName}."
        )
        if os.path.exists(listName):
            try:
                log.debug(
                    f"TemplateList._templateFilenames : loading template list from {listName}."
                )
                # filenames = pickle.load(file(listName, "rb"))
                filenames = pickle.load(open(listName, "rb"))
                log.debug(
                    f"TemplateList._templateFilenames : loaded template list from {listName} : {filenames}"
                )
            except (OSError, pickle.UnpicklingError, EOFError):
                pass
        return filenames

    def save(self):
        # # pickle.dump([name for task, name in self._templates], file(os.path.join(self._path, "list.pickle"), "wb"))
        # pickle.dump(
        #     [name for task, name in self._templates],
        #     open(os.path.join(self._path, "list.pickle"), "wb"),
        # )
        with open(os.path.join(self._path, "list.pickle"), "wb") as pickleFile:
            pickle.dump([name for task, name in self._templates], pickleFile)

        for task, name in self._templates:
            # # templateFile = file(os.path.join(self._path, name), "w")
            # templateFile = open(
            #     os.path.join(self._path, name), "w", encoding="utf-8"
            # )
            templateFile = open(os.path.join(self._path, name), "wb")
            writer = TemplateXMLWriter(templateFile)
            writer.write(task)
            templateFile.close()

        for task, name in self._toDelete:
            os.remove(os.path.join(self._path, name))
        self._toDelete = []
        pub.sendMessage("templates.saved")

    def addTemplate(self, task):
        log.debug(
            f"TemplateList.addTemplate : adding template for task {task}."
        )
        handle, filename = tempfile.mkstemp(".tsktmpl", dir=self._path)
        os.close(handle)
        log.debug(
            f"TemplateList.addTemplate : created temporary file {filename} for new template."
        )
        # # templateFile = file(filename, "w")
        # templateFile = open(filename, "w", encoding="utf-8")
        templateFile = open(filename, "wb")
        writer = TemplateXMLWriter(templateFile)
        writer.write(task.copy())
        log.debug(
            f"TemplateList.addTemplate : wrote task {task} to temporary file {filename}."
        )
        templateFile.close()
        # theTask = TemplateXMLReader(file(filename, "rU")).read()
        # theTask = TemplateXMLReader(
        #     open(filename, "r", encoding="utf-8")
        # ).read()
        theTask = TemplateXMLReader(open(filename, "rb")).read()
        log.debug(
            f"TemplateList.addTemplate : read task {theTask} back from temporary file {filename}."
        )
        self._templates.append((theTask, os.path.split(filename)[-1]))
        log.debug(
            f"TemplateList.addTemplate : added template for task {theTask} with filename {filename} to template list {self._templates}."
        )
        return theTask

    def deleteTemplate(self, idx):
        self._toDelete.append(self._templates[idx])
        del self._templates[idx]

    def copyTemplate(self, filename):
        shutil.copyfile(
            filename, os.path.join(self._path, os.path.split(filename)[-1])
        )
        pub.sendMessage("templates.saved")

    def swapTemplates(self, i, j):
        self._templates[i], self._templates[j] = (
            self._templates[j],
            self._templates[i],
        )

    def __len__(self):
        return len(self._templates)

    def tasks(self):
        return [task for task, _ in self._templates]

    def names(self):
        return [name for _, name in self._templates]
