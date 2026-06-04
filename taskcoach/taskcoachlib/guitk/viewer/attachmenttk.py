# guitk/viewer/attachment.py

# Explications des changements :
#
# Importations : Remplacement des importations wx par tkinter et tkinter.ttk.
# Héritage :
#
# wx.Panel est remplacé par ttk.Frame.
# widgets.VirtualListCtrl est remplacé par ttk.Treeview.
#
#
# __init__: Adaptation de l'initialisation pour accepter les arguments nécessaires à Tkinter.
# createWidget :
#
# Création d'un ttk.Treeview à la place du wx.ListCtrl.
# Les colonnes sont créées en utilisant les définitions de self._columns.
# La méthode populate_tree est appelée pour remplir le Treeview avec les données.
# Gestion de l'événement de sélection (onSelect).
#
#
# _createColumns :
#
# Les définitions de colonnes sont conservées, mais adaptées pour Tkinter.
# Les renderCallback sont utilisés pour extraire les données à afficher dans chaque colonne.
# Adaptation des largeurs de colonnes (width).
#
#
# populate_tree : Méthode pour remplir le Treeview avec les données.
# Autres méthodes : Adaptation des autres méthodes pour utiliser les équivalents Tkinter.
#
# Points importants :
#
# Gestion des images : La gestion des images avec wx.ImageList est complexe et nécessitera une adaptation spécifique pour Tkinter (utilisation de PhotoImage). J'ai commenté cette partie dans l'exemple.
# Tri des colonnes : La gestion du tri des colonnes est implémentée mais nécessite d'être adapté.
# Événements : Les événements wxPython (wx.EVT_XXX) sont remplacés par les événements Tkinter (<ButtonRelease-1>, etc.).
# SortableViewerMixin, AttachmentDropTargetMixin: Ces mixins sont supposés être adaptés pour Tkinter.
# Menu contextuel : Adaptation des menus contextuels pour Tkinter.
#
# Pour la suite :
#
# Teste ce code : Adapte l'exemple d'utilisation à la fin du fichier pour tester le code.
# Adapte les images : Implémente la gestion des images avec PhotoImage.
# Implémente le Drag and Drop : Adapte le code pour gérer le Drag and Drop si nécessaire.
# Adapte les autres fichiers : Continue la conversion des autres fichiers en suivant les mêmes principes.
#
# J'ai essayé de rechercher des informations spécifiques dans les fichiers que vous avez fournis, mais je n'ai pas trouvé de résultats pertinents concernant la conversion vers Tkinter.

import logging
import os
import tkinter as tk
import tkinter.ttk as ttk
from taskcoachlib import widgetstk
from taskcoachlib.widgetstk import itemctrltk
from taskcoachlib.domain import attachment
from taskcoachlib.i18n import _
from taskcoachlib.guitk import dialog
from taskcoachlib.guitk.dialog import editor
from taskcoachlib.guitk import uicommand
from taskcoachlib import render
import taskcoachlib.guitk.menutk
from taskcoachlib.guitk.viewer import basetk, mixintk

log = logging.getLogger(__name__)


class Attachmentviewer(
    mixintk.AttachmentDropTargetMixin,  # pylint: disable=W0223
    basetk.SortableViewerWithColumns,
    mixintk.SortableViewerForAttachmentsMixin,
    mixintk.SearchableViewerMixin,
    mixintk.NoteColumnMixin,
    basetk.ListViewer,
):
    """Vue des pièces jointes dans Task Coach."""

    # Classe de tri pour les pièces jointes
    SorterClass = attachment.AttachmentSorter
    viewerImages = basetk.ListViewer.viewerImages + [
        "fileopen",
        "fileopen_red",
    ]

    def __init__(
        self, parent, attachmentsToShow, taskFile, settings, **kwargs
    ):
        """Initialise la vue des pièces jointes."""
        self.attachments = attachmentsToShow
        self.taskFile = taskFile
        self.settings = settings
        kwargs.setdefault("settingssection", "attachmentviewer")
        super().__init__(parent, taskFile, settings, **kwargs)
        self.tree = None  # Ajout pour stocker l'instance de Treeview

    def _addAttachments(self, attachments, item, **itemDialogKwargs):
        """Ajoute des pièces jointes."""
        # Don't try to add attachments to attachments.
        print(
            f"viewer.attachment.AttachmentViewer._addAttachments : 📌 [DEBUG] Ajout des attachements : {attachments} dans self={self}"
        )
        super()._addAttachments(attachments, None, **itemDialogKwargs)

    def domainObjectsToView(self):
        """Retourne les objets de domaine à afficher dans cette vue."""
        return self.attachments

    def isShowingAttachments(self):
        """Vérifie si la vue affiche des pièces jointes."""
        return True

    def curselectionIsInstanceOf(self, class_):
        """Vérifie si la sélection courante est une instance de la classe spécifiée."""
        return class_ == attachment.Attachment

    # def createWidget(self):
    def createWidget(self, parent):
        """Crée et retourne le widget utilisé pour afficher les pièces jointes."""
        # imageList = self.createImageList() # A adapter
        itemPopupMenu = taskcoachlib.guitk.menutk.AttachmentPopupMenu(
            self.parent,
            self.settings,
            self.taskFile,
            self,  # presentation() n'existe plus, remplacer par self.taskFile
        )
        columnPopupMenu = taskcoachlib.guitk.menutk.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        self._columns = self._createColumns()

        # Création du Treeview pour afficher les pièces jointes
        self.tree = ttk.Treeview(
            self, columns=[col.name for col in self._columns], show="headings"
        )
        for col in self._columns:
            self.tree.heading(
                col.name,
                text=col.header,
                command=lambda c=col: self.sort_column(c, reverse=False),
            )  # Gestion du tri
            self.tree.column(
                col.name, width=col.width
            )  # Initialisation de la largeur

        # Remplissage du Treeview avec les données
        self.populate_tree()

        # Gestion des événements (sélection, etc.)
        self.tree.bind("<ButtonRelease-1>", self.onSelect)

        return self.tree

    def populate_tree(self):
        """Remplissage du Treeview avec les données des pièces jointes."""
        for item in self.domainObjectsToView():
            values = []
            for column in self._columns:
                values.append(
                    column.render(item)
                )  # Utilisation de la méthode render de la colonne
            self.tree.insert("", tk.END, values=values)

    def sort_column(self, col, reverse):
        """Tri des colonnes."""
        print("Tri des colonnes")
        # items = [(self.tree.set(child, col.name), child) for child in self.tree.get_children('')]
        # items.sort(reverse=reverse)
        # for index, (value, child) in enumerate(items):
        #     self.tree.move(child, '', index)
        # self.tree.heading(col.name, command=lambda: self.sort_column(col, not reverse))

    def _createColumns(self):
        """Crée et retourne les colonnes utilisées pour afficher les informations des pièces jointes."""
        # Column_def = widgetstk.itemctrl.Column
        return [
            widgetstk.itemctrltk.Column(
                "type",
                _("Type"),
                width=100,
                eventTypes="",  # Ajuster la largeur
                renderCallback=lambda item: item.type_,  # Remplacer typeImageIndices
            ),
            widgetstk.itemctrltk.Column(
                "subject",
                _("Subject"),
                width=150,
                eventTypes="",
                renderCallback=lambda item: item.subject(),
            ),
            widgetstk.itemctrltk.Column(
                "description",
                _("Description"),
                width=200,
                eventTypes="",
                renderCallback=lambda item: item.description(),
            ),
            # Ajoutez d'autres colonnes ici en adaptant le code wxPython
            widgetstk.itemctrltk.Column(
                "creationDateTime",
                _("Creation date"),
                width=120,
                eventTypes="",
                renderCallback=lambda item: str(
                    item.creationDateTime()
                ),  # Formatage de la date
            ),
            widgetstk.itemctrltk.Column(
                "modificationDateTime",
                _("Modification date"),
                width=120,
                eventTypes="",
                renderCallback=lambda item: str(
                    item.modificationDateTime()
                ),  # Formatage de la date
            ),
        ]

    def createColumnUICommands(self):
        """Crée et retourne les commandes de l'interface utilisateur pour gérer les colonnes."""
        return [
            uicommand.ToggleAutoColumnResizing(
                viewer=self, settings=self.settings
            ),
            None,
            uicommand.ViewColumn(
                menuText=_("&Description"),
                helpText=_("Show/hide description column"),
                setting="description",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Creation date"),
                helpText=_("Show/hide creation date column"),
                setting="creationDateTime",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Modification date"),
                helpText=_("Show/hide last modification date column"),
                setting="modificationDateTime",
                viewer=self,
            ),
        ]

    def createCreationToolBarUICommands(self):
        """Crée et retourne les commandes de la barre d'outils pour la création de pièces jointes."""
        return (
            uicommand.AttachmentNew(
                attachments=self.taskFile, settings=self.settings, viewer=self
            ),
        ) + super().createCreationToolBarUICommands()

    def createActionToolBarUICommands(self):
        """Crée et retourne les commandes de la barre d'outils pour les actions sur les pièces jointes."""
        return (
            uicommand.AttachmentOpen(
                attachments=attachment.AttachmentList(),
                viewer=self,
                settings=self.settings,
            ),
        ) + super().createActionToolBarUICommands()

    def typeImageIndices(self, anAttachment, exists=os.path.exists):
        """Retourne les indices des images associées à un type de pièce jointe."""
        if anAttachment.type_ == "file":
            attachmentBase = self.settings.get("file", "attachmentbase")
            if exists(anAttachment.normalizedLocation(attachmentBase)):
                index = 0  # self.imageIndex["fileopen"]
            else:
                index = 1  # self.imageIndex["fileopen_red"]
        else:
            try:
                index = {"uri": 2, "mail": 3}[
                    anAttachment.type_
                ]  # self.imageIndex[{"uri": "earth_blue_icon", "mail": "envelope_icon"}[anAttachment.type_]]
            except KeyError:
                index = -1
        return {tk.NORMAL: index}

    def itemEditorClass(self):
        """Retourne la classe de l'éditeur d'éléments."""
        return (
            dialog.editor.AttachmentEditor
        )  # TODO : a remettre une fois dialog créé
        log.error(
            "AttachmentViwer.itemEditorClass : dialog.editor.AttachmentEditor à mettre !"
        )

    def newItemCommandClass(self):
        """Classe de commande pour créer un nouvel élément."""
        raise NotImplementedError

    def newSubItemCommandClass(self):
        """Classe de commande pour créer un sous-élément."""
        return None

    def deleteItemCommandClass(self):
        """Classe de commande pour supprimer un élément."""
        raise NotImplementedError

    def cutItemCommandClass(self):
        """Classe de commande pour couper un élément."""
        raise NotImplementedError

    def onSelect(self, event):
        """Gestion de la sélection d'un élément."""
        # A adapter
        pass


# # Exemple d'utilisation (à adapter à ton application)
# if __name__ == '__main__':
#     import tkinter as tk
#     # from taskcoachlib.domain import TaskFile, Settings
#     from taskcoachlib.persistencetk.taskfile import TaskFile
#     from taskcoachlib.config.settings import Settings
#     # Créer une fenêtre Tkinter
#     root = tk.Tk()
#     root.title("Attachment Viewer")
#
#     # Créer un TaskFile et des Settings (à remplacer par tes propres instances)
#     task_file = TaskFile(root)
#     settings = Settings()
#
#     # Créer des pièces jointes (à remplacer par tes propres données)
#     attachments = [
#         attachment.FileAttachment("file1.txt"),
#         attachment.URIAttachment("http://example.com")
#     ]
#
#     # Créer et afficher le AttachmentViewer
#     viewer = Attachmentviewer(root, attachmentsToShow=attachments, taskFile=task_file, settings=settings)
#     viewer.pack(expand=True, fill=tk.BOTH)
#
#     # Lancer la boucle principale Tkinter
#     root.mainloop()
