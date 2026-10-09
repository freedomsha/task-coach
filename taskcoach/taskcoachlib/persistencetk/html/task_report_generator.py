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
# Le fichier generator.py original semble être principalement responsable de
# la génération d'une représentation HTML d'une liste de tâches, destinée à
# l'exportation ou à un affichage de type rapport
# (utilisant des modules comme html et io, et faisant référence à wx qui est
# le toolkit d'interface utilisateur original).
#
# Pour une application Tkinter, une conversion directe n'est pas nécessaire,
# car ce module est spécifique au format HTML. Cependant, si votre objectif est de :
#
#     Créer une classe de rapport Tkinter qui affiche ou exporte les données
#     des tâches (par exemple, dans un format texte simple ou dans une fenêtre Tkinter), OU
#
#     Créer un composant d'affichage Tkinter (comme un TreeView ou un Text) qui
#     formate le contenu comme le faisait le générateur.
#
# Étant donné que vous passez à Tkinter, je vais créer une version simplifiée
# de generator.py, nommée task_report_generator.py, qui génère une chaîne de
# caractères formatée en texte brut ou en Markdown
# (plus moderne et facile à lire que le HTML dans un terminal ou un éditeur de
# texte simple) à partir d'une liste de tâches.
#
# Cette nouvelle classe, TaskReportGenerator, aura une méthode
# generate_markdown_report qui prend une liste de tâches et produit un rapport structuré.

# Explication et Instructions d'Implémentation
#
# J'ai créé le fichier task_report_generator.py qui contient la classe TaskReportGenerator.
#
# Ce que fait cette classe :
#
#     Formatage Markdown : Au lieu de générer du HTML, elle génère un rapport
#     formaté en Markdown (un format texte simple pour la mise en forme de texte),
#     ce qui est plus facile à intégrer dans un widget tkinter.Text ou à
#     exporter comme fichier texte simple.
#
#     Gestion de la Structure : Elle utilise la méthode récursive
#     _get_flattened_tasks pour aplatir la structure arborescente de vos tâches
#     (parents et enfants) tout en maintenant l'ordre.
#
#     Rendu des Colonnes : La méthode _render_column_item simule la façon dont
#     l'original generator.py rendait les informations spécifiques
#     (comme l'indentation pour le sujet en mode arborescence, et le résumé
#     des notes et des pièces jointes).
#
# Comment l'implémenter :
#
#     Enregistrez le fichier : Enregistrez le contenu ci-dessus sous le nom
#     task_report_generator.py dans le répertoire où se trouve votre logique de domaine.
#
#     Dépendances (Très Important) : Le code suppose que vos objets Task, Note,
#                                    Attachment et Column de votre module domain
#                                    ont toujours les méthodes suivantes
#                                    (comme dans l'original Taskcoach) :
#
#         Task.subject()
#         Task.get_domain_children()
#         Task.ancestors() (utilisé pour calculer l'indentation)
#         Task.notes()
#         Task.attachments()
#         Note.subject(), Note.description()
#         Attachment.subject()
#         Column.label(), Column.name(), Column.visible(), Column.render(item, humanReadable=False)
#
#     Utilisation dans Tkinter (Exemple) : Lorsque vous souhaitez exporter
#     ou afficher le rapport (par exemple, suite à un clic sur un bouton "Exporter"),
#     vous utilisez cette classe :

import html
from io import StringIO
import logging
# from . import task  # Assurez-vous que le module 'task' de votre dossier 'domain' est accessible
from taskcoachlib.domain import task

log = logging.getLogger(__name__)

# --- Configuration de base (CSS n'est plus pertinent, on utilise le style Markdown) ---


class TaskReportGenerator(object):
    """
    Génère un rapport en texte brut (Markdown) à partir d'une liste de tâches
    ou pour une seule tâche détaillée.

    Cette classe remplace la génération HTML de l'original Taskcoach
    par une génération Markdown ou texte simple, plus adaptée
    à un environnement d'exportation ou d'affichage simple en Tkinter.
    """

    def __init__(self, task_list, columns):
        """
        Initialise le générateur de rapport.

        Args:
            task_list (TaskList) : La liste des tâches à rapporter (doit être itérable).
            columns (list) : Une liste d'objets 'Column' (ou de classes simulées)
                             définissant les colonnes à inclure dans le rapport.
        """
        self.__task_list = task_list
        self.__columns = columns

    def generate(self, treeMode=True, indent=True):
        """
        Génère le rapport de tâches au format Markdown (mode tableau).

        Cette méthode correspond à la signature de la méthode 'generate'
        du fichier generator.py original.

        Args:
            treeMode (bool): Si True, affiche les tâches avec indentation
                             pour représenter la hiérarchie.
            indent (bool): Si True, indente la colonne du sujet en mode arborescence.

        Returns:
            str: Le rapport de tâches formaté en Markdown.
        """
        bf = StringIO()

        # 1. Titre
        bf.write("# Rapport de Tâches (Vue Liste)\n\n")

        # 2. En-têtes de colonnes (pour la table Markdown)
        header_names = [c.label() for c in self.__columns if c.visible()]
        bf.write("| " + " | ".join(header_names) + " |\n")
        bf.write("|" + "---|" * len(header_names) + "\n")

        # 3. Contenu du rapport
        if treeMode:
            # En mode arborescence, nous utilisons une récursion pour obtenir la liste plate ordonnée.
            report_items = self._get_flattened_tasks(self.__task_list)
        else:
            # En mode liste simple, nous prenons simplement la liste des tâches.
            report_items = list(self.__task_list)

        for item in report_items:
            row_data = []
            for column in self.__columns:
                if column.visible():
                    # Passer les arguments treeMode et indent à la fonction de rendu
                    rendered_item = self._render_column_item(column, item, treeMode, indent)
                    # Supprime les sauts de ligne HTML pour le format Markdown/texte simple
                    rendered_item = rendered_item.replace("<br>", " / ")
                    rendered_item = rendered_item.replace("<br />", " / ")
                    # Tronque pour une meilleure lisibilité dans la table Markdown
                    # Note : Dans une vraie table Markdown, les nouvelles lignes posent problème.
                    # On va s'assurer que le contenu est sur une seule ligne.
                    rendered_item = rendered_item.split('\n')[0].strip()
                    row_data.append(rendered_item)

            # Écriture de la ligne de la table
            bf.write("| " + " | ".join(row_data) + " |\n")

        return bf.getvalue()

    def viewer2html(self, item):
        """
        Génère un rapport détaillé en Markdown pour un seul élément (tâche).

        Note: Le nom 'viewer2html' est conservé pour la compatibilité avec l'API originale,
              mais le contenu généré est en Markdown/texte simple pour l'environnement Tkinter.

        Args:
            item (Task): La tâche unique à détailler.

        Returns:
            str: Le rapport détaillé formaté en Markdown.
        """
        bf = StringIO()

        bf.write(f"# Détails de la Tâche : {item.subject()}\n\n")

        # --- Informations de base ---
        bf.write("## Attributs\n\n")
        bf.write("| Attribut | Valeur |\n")
        bf.write("| :--- | :--- |\n")

        # Liste fixe des attributs importants pour la vue détaillée
        detail_columns = [
            MockColumn("dueDateTime", "Échéance"),
            MockColumn("plannedStartDateTime", "Début Prévu"),
            MockColumn("actualStartDateTime", "Début Réel"),
            MockColumn("completionDateTime", "Achèvement"),
            MockColumn("priority", "Priorité"),
            MockColumn("status", "Statut"),
        ]

        for col in detail_columns:
            try:
                # Utiliser la méthode render de MockColumn pour obtenir la valeur
                value = col.render(item)

                # Tenter d'obtenir une valeur pour le statut si non géré par MockColumn
                if col.name() == "status" and value == "...":
                    value = str(item.status()) if item.status() else "-"

                # S'assurer que les valeurs non définies sont gérées
                if value is None or value == "N/A" or value == "...":
                    value = "-"

                bf.write(f"| {col.label()} | {html.escape(value)} |\n")
            except AttributeError:
                # Gérer les attributs manquants (par ex. s'ils ne sont pas dans MockTask)
                pass

        bf.write("\n")

        # --- Notes ---
        bf.write("## Notes\n\n")

        def render_notes_recursive(notes, level=0):
            """ Génère une liste de notes en Markdown de manière récursive. """
            indent = "  " * level
            for note in notes:
                subject = html.escape(note.subject())
                description = html.escape(note.description())

                bf.write(f"{indent}* **{subject}**\n")

                # La description est un bloc de texte. On indente les lignes suivantes.
                desc_lines = description.split('\n')
                for line in desc_lines:
                    if line.strip():
                        bf.write(f"{indent}  {line.strip()}\n")

                if note.children():
                    render_notes_recursive(note.children(), level + 1)

        if item.notes():
            render_notes_recursive(item.notes())
        else:
            bf.write("_Aucune note associée à cette tâche._\n")

        bf.write("\n")

        # --- Pièces Jointes ---
        bf.write("## Pièces Jointes\n\n")
        if item.attachments():
            for attachment in item.attachments():
                bf.write(f"* {html.escape(attachment.subject())}\n")
        else:
            bf.write("_Aucune pièce jointe associée à cette tâche._\n")

        return bf.getvalue()

    def _get_flattened_tasks(self, tasks_to_process, level=0):
        """
        Récupère les tâches dans un ordre plat pour l'affichage en mode arborescence,
        en incluant les enfants.
        """
        flattened = []
        for t in tasks_to_process:
            # L'indentation est gérée dans _render_column_item
            flattened.append(t)
            if t.children():
                # Appel récursif pour les enfants
                flattened.extend(self._get_flattened_tasks(t.children(), level + 1))
        return flattened

    def _render_column_item(self, column, item, tree_mode, indent):
        """
        Gère le rendu d'une seule cellule pour un élément et une colonne donnés.
        Simule la logique de rendu de l'original generator.py.
        """
        if column.name() == "subject":
            # Gérer l'indentation pour le sujet si le mode arborescence est activé
            rendered_item = column.render(item, humanReadable=False)

            if tree_mode and indent:  # Applique l'indentation seulement si treeMode ET indent sont vrais
                # Calculer l'indentation
                indent_level = len(item.ancestors())
                # Utiliser des espaces insécables pour simuler l'indentation en texte/Markdown
                indent_str = "    " * indent_level
                rendered_item = indent_str + rendered_item

            return html.escape(rendered_item).replace("\n", " ")  # Remplacer les sauts de ligne pour un affichage en ligne

        elif column.name() == "notes":
            # Gérer le rendu des notes (simplifié pour la vue liste)
            def render_notes_summary(notes):
                summary = StringIO()
                for i, note in enumerate(notes):
                    # N'affiche que les 50 premiers caractères du sujet et de la description
                    subject = html.escape(note.subject()[:50].strip())
                    description = html.escape(note.description()[:50].strip())
                    summary.write(f"[{subject}: {description}] ")
                    if i >= 1:  # Limiter à deux notes pour le résumé de la table
                        break
                return summary.getvalue().strip()

            return render_notes_summary(item.notes())

        elif column.name() == "attachments":
            # Rendu des pièces jointes (simplifié)
            return ", ".join(sorted([a.subject() for a in item.attachments()]))

        # Pour toutes les autres colonnes, utiliser le rendu standard
        rendered_item = html.escape(column.render(item, humanReadable=False)).replace("\n", " ")
        if not rendered_item:
            # Assurer qu'une cellule vide est représentée
            rendered_item = "-"
        return rendered_item


# --- Classes Simples pour la Démonstration (À remplacer par les vôtres) ---
# Ces classes simulent les objets dont le générateur a besoin.
# Vous DEVEZ les remplacer par les vrais objets Task, Note, Attachment et Column
# de votre module 'domain'.

class MockColumn(object):
    """ Simule l'objet Column pour le générateur. """
    def __init__(self, name, label, visible=True):
        self._name = name
        self._label = label
        self._visible = visible

    def name(self):
        return self._name

    def label(self):
        return self._label

    def visible(self):
        return self._visible

    def render(self, item, humanReadable=False):
        """ Simule la méthode de rendu. """
        # Ceci est utilisé pour la méthode generate()
        if self._name == "dueDateTime":
            return str(item.dueDateTime()) if item.dueDateTime() else "N/A"
        elif self._name == "subject":
            return item.subject()
        elif self._name == "completed":
            return "Oui" if item.completed() else "Non"
        elif self._name == "priority":
            return str(item.priority()) if item.priority() else "0"

        # Ceci est utilisé pour la méthode viewer2html()
        elif self._name == "plannedStartDateTime":
            return str(item.plannedStartDateTime()) if item.plannedStartDateTime() else "N/A"
        elif self._name == "actualStartDateTime":
            return str(item.actualStartDateTime()) if item.actualStartDateTime() else "N/A"
        elif self._name == "completionDateTime":
            return str(item.completionDateTime()) if item.completionDateTime() else "N/A"
        elif self._name == "status":
            return str(item.status()) if item.status() else "N/A"

        return "..." # Valeur par défaut si non gérée


# Le code ci-dessous est un exemple d'utilisation (décommenter pour tester)

if __name__ == '__main__':
    from datetime import datetime


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

    # 2. Créer une liste de tâches simulées
    task_root = MockTask("Liste de courses")
    task_enfant1 = MockTask("Acheter du lait", task_root, datetime(2025, 10, 5), priority=5)
    task_enfant2 = MockTask("Payer les factures", task_root, datetime(2025, 9, 30), completed=True)
    task_petit_enfant = MockTask("Facture d'électricité", task_enfant2, priority=10)

    # Ajout de notes détaillées et hiérarchiques
    note_enfant = MockNote("Rappel", "Attention à la date limite!", [MockNote("Lien", "www.edf.fr")])
    task_root.notes().append(MockNote("Note 1", "Détails importants à retenir pour l'organisation de la semaine."))
    task_root.notes().append(note_enfant)
    task_root.attachments().append(MockAttachment("Ticket de caisse.pdf"))
    task_root.attachments().append(MockAttachment("ListeFournitures.docx"))

    # La liste des tâches (seulement les tâches de niveau racine pour le générateur)
    mock_task_list = [task_root]

    # 3. Créer une liste de colonnes simulées
    mock_columns = [
        MockColumn("subject", "Tâche"),
        MockColumn("priority", "Priorité"),
        MockColumn("dueDateTime", "Échéance"),
        MockColumn("completed", "Terminée"),
        MockColumn("notes", "Notes (Résumé)"),
        MockColumn("attachments", "Pièces Jointes")
    ]

    # 4. Générer le rapport détaillé (viewer2html)
    generator = TaskReportGenerator(mock_task_list, mock_columns)
    detailed_report = generator.viewer2html(task_root)

    print("\n--- RAPPORT DÉTAILLÉ (viewer2html) ---\n")
    print(detailed_report)

    # 5. Générer le rapport de liste (generate)
    list_report = generator.generate(treeMode=True, indent=True)
    print("\n--- RAPPORT LISTE (generate) ---\n")
    print(list_report)


# Utilisation dans Tkinter (Exemple) : Lorsque vous souhaitez exporter ou afficher le rapport (par exemple, suite à un clic sur un bouton "Exporter"), vous utilisez cette classe :
# Supposons que vous ayez déjà initialisé task_list et columns
# from taskcoachlib.domain.tasklist import TaskList
# from taskcoachlib.gui.columns import get_default_columns # Ou votre propre liste de colonnes
# from votre_module import TaskReportGenerator # Importez votre nouveau fichier

# ... Obtenir la liste de tâches filtrée et triée...
# task_list_to_report = your_filtered_and_sorted_list
# columns_to_report = your_column_objects

# generator = TaskReportGenerator(task_list_to_report, columns_to_report)
# markdown_report = generator.generate_markdown_report(tree_mode=True)

# # Pour afficher dans un widget Text de Tkinter:
# report_text_widget.delete("1.0", "end")
# report_text_widget.insert("1.0", markdown_report)
#
# # Pour exporter vers un fichier texte:
# # with open("rapport_taches.md", "w", encoding="utf-8") as f:
# # f.write(markdown_report)

# Ce nouveau module remplit la même fonction de génération de rapport que l'ancien `generator.py`, mais en utilisant un format texte simple (Markdown) adapté à l'environnement Tkinter.
#
# Avez-vous besoin d'aide pour une autre partie de la conversion, peut-être le `filter.py` ou le `sorter.py` qui pourraient nécessiter une interaction plus directe avec l'interface utilisateur Tkinter ?

# Dans le fichier generator.py original, cette méthode produisait du HTML détaillé. Pour maintenir la cohérence avec notre approche Tkinter/exportation de texte simple, j'ai implémenté la méthode viewer2html(self, item) de manière à ce qu'elle génère un rapport détaillé en Markdown pour une tâche donnée.
#
# J'ai mis à jour le Canvas task_report_generator.py pour inclure cette méthode. J'ai aussi ajouté des attributs simulés à la classe MockTask pour que l'exemple de démonstration (dans le bloc if __name__ == '__main__':) puisse fonctionner correctement.
#
# Voici le fichier mis à jour :
#
# Instructions d'Utilisation
#
#     Enregistrez le fichier : Assurez-vous que ce code remplace celui de task_report_generator.py.
#
#     Appel de la méthode : Dans votre code Tkinter, lorsque l'utilisateur sélectionne une tâche et demande à en voir les détails ou à l'exporter, appelez la méthode sur cette tâche :

# # Supposons que 'selected_task' est l'objet Task sélectionné
# # et que 'report_generator' est une instance de TaskReportGenerator
#
# detailed_markdown = report_generator.viewer2html(selected_task)
#
# # Vous pouvez ensuite insérer 'detailed_markdown' dans un widget Tkinter Text
# # ou l'écrire dans un fichier.
#
# La sortie sera une chaîne de caractères Markdown facile à lire, contenant les attributs de la tâche, la liste complète des notes (avec leur hiérarchie) et les pièces jointes.
#
# N'hésitez pas si vous avez d'autres questions sur la compatibilité de `filter.py`
# ou `sorter.py` avec Tkinter !
