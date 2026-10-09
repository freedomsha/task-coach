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
# Le fichier writer.py original est étroitement lié à la génération HTML et
# au concept de fichiers CSS séparés.
# Notre nouveau TaskReportGenerator produit du Markdown/texte brut.
#
# Pour conserver la logique de l'original
# tout en étant compatible avec la sortie Markdown et un environnement
# sans fichiers CSS externes (comme un éditeur de texte simple de Tkinter),
# je vais créer un nouveau fichier markdown_writer.py.
#
# Ce nouveau fichier implémentera la classe MarkdownWriter avec
# une méthode write() qui appellera la méthode appropriée
# (generate pour la liste, ou viewer2html pour le détail)
# de notre TaskReportGenerator et écrira le résultat en Markdown dans le flux de sortie fourni.

# Ce nouveau fichier, markdown_writer.py, remplit la fonction du
# writer.py original pour notre nouvelle architecture Markdown.
#
# Prochaines étapes
#
#     Enregistrez ce fichier sous le nom markdown_writer.py dans le répertoire
#     approprié de votre projet.
#
#     TODO : Dans votre code d'application (Tkinter),
#     remplacez l'importation de HTMLWriter par MarkdownWriter.
#
#     Lorsque vous générez un rapport, assurez-vous de passer l'instance du
#     TaskReportGenerator à la méthode write du MarkdownWriter,
#     ainsi que la tâche détaillée si vous voulez la vue viewer2html.
import os
import io

# Note: Ce fichier suppose que votre TaskReportGenerator (dans task_report_generator.py)
# est importable, soit en le plaçant dans le même répertoire, soit en ajustant l'import.
# Pour cet exemple, nous allons simuler l'import.
from taskcoachlib.persistencetk.html import task_report_generator as generator


class MarkdownWriter(object):
    """
    Écrit le rapport généré par TaskReportGenerator au format Markdown.

    Cette classe remplace HTMLWriter et supprime toute logique
    spécifique au HTML ou au CSS (comme la génération de fichiers .css séparés),
    car notre générateur produit du texte simple formaté en Markdown.
    """
    def __init__(self, fd, filename=None):
        """
        Initialise l'écrivain.

        Args:
            fd (file-like object) : Le descripteur de fichier où écrire la sortie.
            filename (str, optional) : Le nom de fichier, utilisé pour le contexte
                                       mais non essentiel ici.
        """
        self.__fd = fd
        self.__filename = filename

    def write(self, generator_instance, item=None, treeMode=True, indent=True, selectionOnly=False, columns=None):
        """
        Génère le rapport et l'écrit dans le flux de sortie (__fd).

        La signature est adaptée de l'original Taskcoach pour être compatible
        avec une instance de TaskReportGenerator.

        Args:
            generator_instance (TaskReportGenerator): L'instance du générateur de rapport.
            item (Task, optional): Si fourni, utilise viewer2html() pour un rapport détaillé
                                   pour cet élément unique.
            treeMode (bool): Passé à generator.generate().
            indent (bool): Passé à generator.generate().
            selectionOnly (bool): Non utilisé dans cette version Markdown simplifiée,
                                  car 'item' gère le rapport détaillé.
            columns (list): Si fourni et 'item' est None, cela peut indiquer
                            que nous générons la vue de liste complète.

        Returns:
            int: Le nombre d'éléments rapportés (1 si 'item' est fourni, ou
                 une valeur simulée pour le rapport de liste).
        """
        # Déterminer quelle méthode d'écriture appeler
        if item is not None:
            # Génère la vue détaillée (équivalent à l'ancienne viewer2html)
            report_content = generator_instance.viewer2html(item)
            count = 1  # Un seul élément est détaillé
        else:
            # Génère la vue de liste complète (équivalent à l'ancienne generate)
            report_content = generator_instance.generate(treeMode=treeMode, indent=indent)
            # Puisque nous n'avons pas la liste complète ici, on retourne 1 par défaut
            # ou vous pouvez ajuster TaskReportGenerator pour retourner le compte.
            count = 10  # Valeur par défaut simulée pour la compatibilité

        # Écrire le contenu Markdown/texte simple dans le descripteur de fichier
        self.__fd.write(report_content)

        return count

    # La méthode _writeCSS et la variable css ont été supprimées car non pertinentes.


# --- Exemple d'utilisation (décommenter pour tester) ---

if __name__ == '__main__':
    from datetime import datetime
    # from task_report_generator import TaskReportGenerator, MockTask, MockColumn, MockNote, MockAttachment
    from task_report_generator import TaskReportGenerator, MockColumn

    # 1. Simuler les classes de domaine (Task, Note, Attachment)
    class MockNote:
        def __init__(self, subject, description, children=None):
            self._subject = subject
            self._description = description
            self._children = children if children is not None else []

        def subject(self): return self._subject
        def description(self): return self._description
        def children(self): return self._children


    class MockAttachment:
        def __init__(self, subject):
            self._subject = subject
        def subject(self): return self._subject


    class MockTask:
        def __init__(self, subject, parent=None, due_date=None, completed=False, priority=0, status="Active"):
            self._subject = subject
            self._parent = parent
            self._children = []
            self._notes = []
            self._attachments = []
            self._due_date = due_date
            self._completed = completed
            self._priority = priority
            self._status = status
            self._planned_start_date = due_date
            self._actual_start_date = None
            self._completion_date = None
            if completed:
                self._completion_date = datetime.now()

            if parent:
                parent.children().append(self)

        def subject(self): return self._subject
        def children(self): return self._children
        def notes(self): return self._notes
        def attachments(self): return self._attachments
        def dueDateTime(self): return self._due_date
        def plannedStartDateTime(self): return self._planned_start_date
        def actualStartDateTime(self): return self._actual_start_date
        def completionDateTime(self): return self._completion_date
        def completed(self): return self._completed
        def priority(self): return self._priority
        def status(self): return self._status
        def ancestors(self):
            ancestors_list = []
            current = self._parent
            while current:
                ancestors_list.append(current)
                current = current._parent
            return ancestors_list

    # 1. Préparation des données (mêmes mocks que dans task_report_generator.py)
    task_root = MockTask("Liste de courses", due_date=datetime(2025, 10, 10), priority=5)
    task_enfant1 = MockTask("Acheter du lait", task_root, datetime(2025, 10, 5), priority=5)
    task_enfant2 = MockTask("Payer les factures", task_root, datetime(2025, 9, 30), completed=True, status="Completed")

    task_root.notes().append(MockNote("Note 1", "Détails importants à retenir..."))
    task_root.attachments().append(MockAttachment("Ticket de caisse.pdf"))
    mock_task_list = [task_root]
    mock_columns = [
        MockColumn("subject", "Tâche"),
        MockColumn("priority", "Priorité"),
        MockColumn("dueDateTime", "Échéance"),
    ]

    # 2. Initialisation du Générateur
    report_generator = TaskReportGenerator(mock_task_list, mock_columns)

    # 3. Écriture du rapport de liste dans un flux StringIO
    output_list = io.StringIO()
    writer_list = MarkdownWriter(output_list)
    writer_list.write(report_generator, treeMode=True)
    # print("\n--- Résultat du Rapport de Liste (generate) ---\n")
    # print(output_list.getvalue())

    # 4. Écriture du rapport détaillé dans un autre flux StringIO
    output_detail = io.StringIO()
    writer_detail = MarkdownWriter(output_detail)
    writer_detail.write(report_generator, item=task_root) # item=task_root appelle viewer2html
    # print("\n--- Résultat du Rapport Détaillé (viewer2html) ---\n")
    # print(output_detail.getvalue())
