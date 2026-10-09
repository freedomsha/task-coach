# -*- coding: utf-8 -*-
"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

Task Coach is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Task Coach is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see
<http://www.gnu.org/licenses/>.

Ce fichier contient deux classes principales : BaseCategoryViewer et CategoryViewer, qui définissent les vues arborescentes des catégories dans Task Coach.

**Pour créer les commandes pour la barre d'outils** :
Les commandes sont instanciées dynamiquement via des appels dans les méthodes create*ToolBarUICommands, en injectant le viewer courant.
Elles sont ensuite collectées et utilisées dans la création de la barre d’outils dans MainWindow, toolbar.py ou des conteneurs de type UICommandContainer.

**Méthodes impliquées** : (Chacune retourne un ou plusieurs objets issus du module uicommand.)
createCreationToolBarUICommands()
createColumnUICommands()
createModeToolBarUICommands() (dans CategoryViewer)

**Fonctionnement général**
1-Création via uicommand
Les commandes sont instanciées comme objets de classes uicommand.XYZCommand, par exemple :
uicommand.CategoryNew(...)
uicommand.NewSubItem(...)
uicommand.ViewColumn(...)
2-Association avec viewer=self
Chaque commande reçoit un paramètre viewer=self, ce qui lui donne un accès direct à la vue courante (BaseCategoryViewer ou CategoryViewer).
Cela permet d'exécuter des actions ciblées sur les données affichées.
3-Résultat
Ces méthodes renvoient :
- des tuples (comme (cmd1, cmd2))
- ou des listes (dans createColumnUICommands)
4-Intégration dans l’interface
Ces commandes sont ensuite intégrées dans des menus ou barres d’outils via les composants de l’interface (probablement dans mainwindow, toolbar ou des panel spécifiques).

Exemple d’utilisation concrète dans CategoryViewer:
self.filterUICommand = uicommand.CategoryViewerFilterChoice(settings=self.settings)
return super().createModeToolBarUICommands() + (self.filterUICommand,)
Ici :
CategoryViewerFilterChoice est une commande spécialisée pour filtrer les catégories.
Elle est ajoutée à l’ensemble des commandes de la barre d’outils « mode ».
"""
# Voici le plan général de la conversion, suivi du code converti:
# Plan de conversion :
#
# Mise à jour des imports : Remplacer les anciens imports wxPython par les nouveaux imports Tkinter que vous avez spécifiés.
# Adaptation des classes :
#
# BaseCategoryViewer: Adapter cette classe pour utiliser les composants Tkinter
#                     au lieu de wxPython. Cela inclut le remplacement de
#                     wx.CheckTreeCtrl par un équivalent Tkinter
#                     (possiblement un arbre créé avec tkinter.ttk.Treeview et des cases à cocher).
# CategoryViewer: Mettre à jour l'initialisation et toute méthode utilisant des éléments spécifiques à wxPython.
#
#
# Remplacement des composants UI : wxPython utilise des contrôles spécifiques (ex: wx.LIST_FORMAT_LEFT). Il faudra trouver les équivalents en Tkinter.
# Gestion des événements : Adapter la gestion des événements (self.onSelect, self.onCheck, etc.) pour qu'elle fonctionne avec le système d'événements de Tkinter.
# UICommands : S'assurer que les UICommands utilisés sont compatibles avec Tkinter. Cela peut nécessiter des adaptations dans la façon dont les commandes sont appelées et exécutées.
# Suppression des éléments obsolètes : Retirer ou commenter les éléments de code obsolètes ou spécifiques à wxPython qui ne sont plus nécessaires.

# Points importants :
#
# ttk.Treeview : J'ai remplacé wx.CheckTreeCtrl par ttk.Treeview.
# Vous devrez implémenter la logique des cases à cocher vous-même,
# car Treeview n'a pas cette fonctionnalité nativement.
# Vous pouvez le faire en ajoutant une colonne avec des images représentant
# l'état coché/décoché et en gérant les clics sur cette colonne.
# Adaptation des événements : Les événements comme onSelect et onCheck
# devront être adaptés pour fonctionner avec le système d'événements de Tkinter.
# Cela implique de lier des fonctions aux événements du Treeview (ex: <Button-1> pour les clics).
# wx.LIST_FORMAT_LEFT : J'ai remplacé wx.LIST_FORMAT_LEFT par tk.LEFT.
# RefreshItems : La méthode RefreshItems n'a pas d'équivalent direct dans Tkinter.
# Vous devrez trouver une autre façon de rafraîchir l'affichage des éléments dans l'arbre.
# Une solution pourrait être de reconfigurer les éléments modifiés.
# Images : La gestion des images devra être revue pour utiliser les objets PhotoImage de Tkinter.
# Méthodes à implémenter : Les méthodes commentées avec "À adapter pour Tkinter"
# nécessitent une implémentation spécifique à Tkinter.

# from future import standard_library
# standard_library.install_aliases()
import logging
import tkinter as tk
from tkinter import ttk  # Pour l'arbre (Treeview)
from taskcoachlib import command, widgetstk
from taskcoachlib.widgetstk import itemctrltk, treectrltk
from taskcoachlib.domain import category
from taskcoachlib.i18n import _

# from taskcoachlib.gui import uicommand, dialog, menu
from taskcoachlib.guitk.uicommand import uicommandtk as uicommand
from taskcoachlib.guitk import dialog
# from taskcoachlib.guitk.dialog import editor  # itemEditorClass l'importera en local

# from taskcoachlib.gui.dialog.editor import CategoryEditor  # circular import
import taskcoachlib.guitk.menutk

# from taskcoachlib.gui.menu import *
from taskcoachlib.guitk.viewer import basetk
from taskcoachlib.guitk.viewer import mixintk

# from taskcoachlib.guitk.viewer.mixintk import AttachmentDropTargetMixin
from taskcoachlib.guitk.viewer import inplace_editortk

log = logging.getLogger(__name__)


class BaseCategoryViewer(
    mixintk.AttachmentDropTargetMixin,  # pylint: disable=W0223
    mixintk.FilterableViewerMixin,
    mixintk.SortableViewerForCategoriesMixin,
    mixintk.SearchableViewerMixin,
    basetk.WithAttachmentsViewerMixin,
    mixintk.NoteColumnMixin,
    mixintk.AttachmentColumnMixin,
    basetk.SortableViewerWithColumns,
    basetk.TreeViewer
):
    """
    Classe de base pour la vue des catégories.
    Cette classe gère l'affichage et l'interaction avec les catégories dans une vue arborescente,
    y compris la gestion des pièces jointes, des filtres, et du tri.
    """

    SorterClass = category.CategorySorter
    defaultTitle = _("Categories")
    defaultBitmap = "folder_blue_arrow_icon"

    def __init__(self, *args, **kwargs):
        """
        Initialise la classe BaseCategoryViewer.
        Args:
            *args: Arguments positionnels.
            **kwargs: Arguments nommés.
        """
        # kwargs.setdefault('settingsSection', 'category_viewer')
        # il ne trouvait pas de category_viewer
        kwargs.setdefault("settingsSection", "categoryviewer")
        super().__init__(*args, **kwargs)
        for eventType in [
            category.Category.subjectChangedEventType(),
            category.Category.appearanceChangedEventType(),
            category.Category.exclusiveSubcategoriesChangedEventType(),
            category.Category.filterChangedEventType(),
        ]:
            self.registerObserver(self.onAttributeChanged_Deprecated, eventType)

    def domainObjectsToView(self):
        """
        Retourne les objets de domaine à afficher dans la vue.
        Returns :
            (list) : Liste des catégories à afficher.
        """
        return self.taskFile.categories()

    def curselectionIsInstanceOf(self, class_):
        """
        Vérifie si la sélection actuelle est une instance de la classe spécifiée.
        Args :
            class_ (type) : La classe à vérifier.
        Returns :
            (bool) : True si la sélection est une instance de la classe spécifiée.
        """
        return class_ == category.Category

    # Explications des modifications :
    #
    # Remplacement du widget : Au lieu de créer un ttk.Treeview directement, on instancie maintenant treectrltk.TreeListCtrl.
    # Passage des paramètres : Tous les paramètres nécessaires pour initialiser le TreeListCtrl sont passés lors de sa création :
    #
    # parent : Le viewer lui-même (self).
    # columns : La liste des colonnes créées par self.createColumns().
    # selectCommand, editCommand, dragAndDropCommand, itemPopupMenu, columnPopupMenu : Les callbacks et menus nécessaires pour la gestion des événements et des interactions.
    # validateDrag: la validation du drag and drop
    #
    #
    # Suppression de la configuration de l'ImageList : La ligne widget.AssignImageList(imageList) est commentée car la gestion des images est différente avec TreeListCtrl (elle est gérée au niveau des colonnes, si nécessaire).
    # Suppression de setmaincolumn : La ligne widget.SetMainColumn(1) est supprimée.
    #
    # Points importants :
    #
    # Cette version suppose que les méthodes onSelect et onEdit existent déjà dans votre classe BaseCategoryViewer ou une de ses classes parentes et qu'elles sont adaptées pour fonctionner avec les événements de TreeListCtrl (Tkinter).
    # J'ai inclus le dragAndDropCommand. Il faudra vérifier si elle est conforme.
    # Assurez-vous que la classe Column dans itemctrltk.py a bien une méthode name() et is_shown() [[29, 30]].
    # Il faut vérifier que l'ArtProvider est opérationnel.
    # Il faut vérifier la gestion des événements, des cases à cocher, et des enfants exclusifs.
    #
    # Prochaines étapes :
    #
    # Implémenter onSelect et onEdit : Assurez-vous que ces méthodes sont définies et qu'elles gèrent correctement les événements de sélection et d'édition du TreeListCtrl.
    # Tester la gestion des colonnes : Vérifiez que l'affichage et le masquage des colonnes fonctionnent correctement.
    # Adapter la gestion des événements : Liez les événements nécessaires du TreeListCtrl (clics, double-clics, etc.) aux fonctions correspondantes dans votre classe.

    # D'après le message d'erreur, il semble qu'il y ait un problème lors de la création du TreeListCtrl avec Tkinter. L'erreur spécifique est _tkinter.TclError: unknown option "-selectCommand". Cela indique que l'option selectCommand n'est pas une option valide pour le widget ttk.Treeview de Tkinter.
    # Dans le code wxPython, il était possible de passer des arguments comme selectCommand directement au constructeur du TreeCtrl. Cependant, Tkinter a une approche différente. Les gestionnaires d'événements (comme la sélection) doivent être liés au widget via la méthode bind.
    # Voici comment je pense qu'on peut résoudre ce problème :
    #
    # 1-Supprimer selectCommand et editCommand des arguments de TreeListCtrl :
    # Dans taskcoachlib/widgetstk/treectrltk.py,
    # supprimez selectCommand et editCommand de la liste des arguments
    # passés à la classe parente (CtrlWithItemsMixin).
    #
    # 2-Lier les événements de sélection et d'édition
    # après la création du TreeListCtrl :
    # Après avoir créé l'instance de TreeListCtrl
    # dans taskcoachlib/guitk/viewer/categorytk.py,
    # utilisez la méthode bind pour lier les événements de sélection et d'édition
    # aux fonctions onSelect et Edit.
    # def createWidget(self):
    def createWidget(self, parent):
        """
        Crée et retourne le widget utilisé pour afficher les catégories.
        Returns :
            widget (ttk.Treeview) : (treectrltk.CheckTreeCtrl) Le widget CheckTreeCtrl utilisé pour afficher les catégories.
        """
        log.debug(f"BaseCategoryViewer.createWidget : Création du widget BaseCategoryViewer dans self={self.__class__.__name__} avec parent={parent}.")
        # imageList = self.createImageList()  # À adapter pour Tkinter
        self._columns = self.createColumns()
        log.debug(f"BaseCategoryViewer.createWidget : colonnes créées ={self._columns}.")
        itemPopupMenu = self.createCategoryPopupMenu()
        columnPopupMenu = taskcoachlib.guitk.menutk.ColumnPopupMenu(self, parent)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])

        # # Création du Treeview avec des colonnes
        # widget = ttk.Treeview(self, columns=[col.name for col in self._columns], show="tree headings")

        # Création du TreeListCtrl
        # widget = widgetstk.treectrltk.CheckTreeCtrl(
        widget = widgetstk.treectrltk.TreeListCtrl(  # Sauf que ce n'est pas un TreeListCtrl qu'il faut !? Si !
            self,  # self ou parent ?
            # parent,
            # self,  # adapter ?
            parent,
            # self.adapter, # passer l'adapter ici'
            # parent=self,
            # adapter= ,
            columns=self._columns,  # Les colonnes
            selectCommand=self.onSelect,  # Enlever ça, les commandes utilisent bind !
            # checkCommand=self.onCheck,  # unknown option "-checkCommand"
            # editCommand=self.onEdit,
            editCommand=uicommand.Edit(viewer=self),
            dragAndDropCommand=uicommand.CategoryDragAndDrop(
                viewer=self, categories=self.presentation()
            ),
            itemPopupMenu=itemPopupMenu,
            columnPopupMenu=columnPopupMenu,
            # resizeableColumn=1 if self.hasOrderingColumn() else 0, #pas utilisé
            # validateDrag=self.validateDrag,
            **self.widgetCreationKeywordArguments()  # Problèmes ?  taskcoachlib.gui.viewer.mixin.AttachmentDropTargetMixin
        )

        # # Configuration des colonnes
        # for col in self._columns:
        #     widget.heading(col.name, text=col.name)  # Définir les en-têtes
        #     # TODO: Ajouter les commandes de tri et redimensionnement ici
        #
        # # if self.hasOrderingColumn():
        # #     widget.SetMainColumn(1) # À adapter pour Tkinter

        # Configuration de l'ImageList si nécessaire
        # widget.AssignImageList(imageList)  # À adapter pour Tkinter
        # pylint: disable=E1101
        # self.widget.pack(expand=True, fill="both")
        widget.pack(expand=True, fill="both")

        widget.bind("<ButtonRelease-1>", self.onSelect)  # Binding pour la selection (clic gauche)
        widget.bind("<Double-Button-1>", uicommand.Edit(viewer=self))  # Binding pour l'édition (double clic)

        # return self.widget
        log.debug(f"BaseCategoryViewer.createWidget : widget TreeListCtrl créé ={widget.__class__.__name__}{widget}.")
        return widget

    def createCategoryPopupMenu(self, localOnly=False):
        """
        Crée et retourne le menu contextuel pour les catégories.
        Args :
            localOnly (bool) : (optional) Indique si le menu est local seulement. Par défaut à False.
        Returns :
            (tk.Menu) : Le menu contextuel pour les catégories.
        """
        # # return taskcoachlib.guitk.menutk.CategoryPopupMenu(
        # #     self.parent, self.settings, self.taskFile, self, localOnly
        # # )  # il manque self, self.parent à la place de parent mais quoi mettre ?
        # return taskcoachlib.guitk.menutk.CategoryPopupMenu(
        #     self.parent, self, self.settings, self.taskFile,  localOnly
        # )  # En modifiant l'appel à CategoryPopupMenu,
        # # on s'assure que l'objet de type CategoryViewer est bien passé à CategoryPopupMenu.
        return taskcoachlib.guitk.menutk.CategoryPopupMenu(
            self, self.parent, self.settings, self.taskFile, self, localOnly
        )
        # return taskcoachlib.guitk.menutk.CategoryPopupMenu(
        #     parent=self.parent, parent_window=self, settings=self.settings, taskFile=self.taskFile, categoryViewer=self, localOnly=localOnly
        # )

    def createColumns(self):
        """
        Crée et retourne les colonnes pour l'affichage des catégories.
        Returns :
            (list) : Liste des colonnes créées.
        """
        # pylint: disable=W0142,E1101
        kwargs = dict(resizeCallback=self.onResizeColumn)
        columns = [
            widgetstk.itemctrltk.Column(
                # self.widget.column(
                "ordering",
                "",
                category.Category.orderingChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="ordering"
                ),
                imageIndicesCallback=self.orderingImageIndices,
                renderCallback=lambda category: "",
                width=self.getColumnWidth("ordering"),
            ),
            widgetstk.itemctrltk.Column(
                "subject",
                _("Subject"),
                category.Category.subjectChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="subject"
                ),
                imageIndicesCallback=self.subjectImageIndices,
                width=self.getColumnWidth("subject"),
                editCallback=self.onEditSubject,
                editControl=inplace_editortk.SubjectCtrl,
                **kwargs
            ),
            widgetstk.itemctrltk.Column(
                "description",
                _("Description"),
                category.Category.descriptionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="description"
                ),
                renderCallback=lambda category: category.description(),
                width=self.getColumnWidth("description"),
                editCallback=self.onEditDescription,
                editControl=inplace_editortk.DescriptionCtrl,
                **kwargs
            ),
            widgetstk.itemctrltk.Column(
                "attachments",
                "",
                category.Category.attachmentsChangedEventType(),
                # pylint: disable=E1101
                width=self.getColumnWidth("attachments"),
                alignment=tk.LEFT,  # Remplacer wx.LIST_FORMAT_LEFT
                imageIndicesCallback=self.attachmentImageIndices,
                # headerImageIndex=self.imageIndex["paperclip_icon"],  # imageIndex ne fonctionne pas pour l'instant, la liste semble vide !
                renderCallback=lambda category: "",
                **kwargs
            ),
            widgetstk.itemctrltk.Column(
                "notes",
                "",
                category.Category.notesChangedEventType(),
                # pylint: disable=E1101
                width=self.getColumnWidth("notes"),
                alignment=tk.LEFT,  # Remplacer wx.LIST_FORMAT_LEFT
                imageIndicesCallback=self.noteImageIndices,
                # headerImageIndex=self.imageIndex["note_icon"],
                renderCallback=lambda category: "",
                **kwargs
            ),
            widgetstk.itemctrltk.Column(
                "creationDateTime",
                _("Creation date"),
                width=self.getColumnWidth("creationDateTime"),
                renderCallback=self.renderCreationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="creationDateTime"
                ),
                **kwargs
            ),
            widgetstk.itemctrltk.Column(
                "modificationDateTime",
                _("Modification date"),
                width=self.getColumnWidth("modificationDateTime"),
                renderCallback=self.renderModificationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="modificationDateTime"
                ),
                *category.Category.modificationEventTypes(),
                **kwargs
            ),
        ]
        # columns.pack(expand=True, fill="both")
        return columns

    def createCreationToolBarUICommands(self):
        """
        Crée et retourne les commandes de la barre d'outils pour la création de catégories.
        Returns :
            (tuple) : Les commandes de création.
        """
        return (
            uicommand.CategoryNew(
                categories=self.presentation(), settings=self.settings
            ),
            uicommand.NewSubItem(viewer=self),
        )

    def createColumnUICommands(self):
        """
        Crée et retourne les commandes pour la gestion des colonnes.
        Returns :
            (list) : Liste des commandes pour les colonnes.
        """
        commands = [
            uicommand.ToggleAutoColumnResizing(viewer=self, settings=self.settings),
            None,
            uicommand.ViewColumn(
                menuText=_("&Manual ordering"),
                helpText=_("Show/hide the manual ordering column"),
                setting="ordering",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Description"),
                helpText=_("Show/hide description column"),
                setting="description",
                viewer=self,
            ),
            uicommand.ViewColumn(
                menuText=_("&Attachments"),
                helpText=_("Show/hide attachments column"),
                setting="attachments",
                viewer=self,
            ),
        ]
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self,
            )
        )
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Creation date"),
                helpText=_("Show/hide creation date column"),
                setting="creationDateTime",
                viewer=self,
            )
        )
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Modification date"),
                helpText=_("Show/hide last modification date column"),
                setting="modificationDateTime",
                viewer=self,
            )
        )
        return commands

    def onAttributeChanged(self, newValue, sender):
        """
        Gère les événements de changement d'attribut.
        Args :
            newValue : La nouvelle valeur de l'attribut.
            sender : L'objet qui a envoyé l'événement.
        """
        super().onAttributeChanged(newValue, sender)

    def onAttributeChanged_Deprecated(self, event):
        """
        Gère les événements de changement d'attributs obsolètes.
        Args :
            event : L'événement.
        """
        if category.Category.exclusiveSubcategoriesChangedEventType() in event.types():
            # We need to refresh the get_domain_children of the changed item as well
            # because they have to use radio buttons instead of checkboxes, or
            # vice versa:
            # Nous devons également actualiser les enfants de l'élément modifié
            # car ils doivent utiliser des boutons radio au lieu de cases à cocher, ou vice versa:
            items = event.sources()
            for item in items.copy():
                items |= set(item.children())
                # self.widget.RefreshItems(*items)  # À adapter pour Tkinter
            pass  # Remplacer par l'équivalent Tkinter
            # pylint: disable=W0142
        else:
            super().onAttributeChanged_Deprecated(event)

    def onCheck(self, event, final):
        """
        Gère les événements de sélection des cases à cocher.
        Args :
            event : L'événement de sélection.
            final : Indique si c'est la sélection finale.
        """
        # categoryToFilter = self.widget.GetItemPyData(event.GetItem()) # À adapter pour Tkinter
        categoryToFilter = self.widget._item_to_object[event.GetItem()]  # TODO Reste à convertir event.GetItem() en item Tkinter
        categoryToFilter.setFiltered(event.GetItem().IsChecked())  # À adapter pour Tkinter
        self.sendViewerStatusEvent()  # Notify status observers like the status bar

    def getIsItemChecked(self, item):
        """
        Vérifie si un élément est coché.
        Args :
            item : L'élément à vérifier.
        Returns :
            (bool) : True si l'élément est coché.
        """
        if isinstance(item, category.Category):
            return item.isFiltered()
        return False

        # @staticmethod

    def getItemParentHasExclusiveChildren(self, item):
        """
        Vérifie si le parent de l'élément a des sous-catégories exclusives.
        Args :
            item : L'élément à vérifier.
        Returns :
            (bool) : True si le parent a des sous-catégories exclusives.
        """
        parent = item.parent()
        return parent and parent.hasExclusiveSubcategories()

    def isShowingCategories(self):
        """
        Vérifie si la vue affiche des catégories.
        Returns :
            (bool) : True si la vue affiche des catégories.
        """
        return True

    def statusMessages(self):
        """
        Retourne les messages de statut à afficher.
        Returns :
            (tuple) : Messages de statut.
        """
        status1 = _("Categories: %d selected, %d total") % (
            len(self.curselection()),
            len(self.presentation()),
        )
        filteredCategories = self.presentation().filteredCategories()
        status2 = _("Status: %d filtered") % len(filteredCategories)
        return status1, status2

    def itemEditorClass(self):
        """
        Retourne la classe de l'éditeur d'éléments.
        Returns :
            (type) : Classe de l'éditeur d'éléments.
        """
        from taskcoachlib.guitk.dialog.editor import CategoryEditor
        return (
            dialog.editor.CategoryEditor
        )  # from taskcoachlib.guitk.dialog.editor import CategoryEditor
        # return CategoryEditor

    def newItemCommandClass(self):
        """
        Retourne la classe de commande pour créer un nouvel élément.
        Returns :
            (type) : Classe de commande pour créer un nouvel élément.
        """
        return command.NewCategoryCommand

    def newSubItemCommandClass(self):
        """
        Retourne la classe de commande pour créer un nouvel sous-élément.
        Returns :
            (type) : Classe de commande pour créer un nouvel sous-élément.
        """
        return command.NewSubCategoryCommand

    def deleteItemCommandClass(self):
        """
        Retourne la classe de commande pour supprimer un élément.
        Returns :
            (type) : Classe de commande pour supprimer un élément.
        """
        return command.DeleteCategoryCommand


class Categoryviewer(BaseCategoryViewer):  # pylint: disable=W0223
    """
    Vue des catégories, héritant de BaseCategoryViewer.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise la classe CategoryViewer.
        Args :
            *args: Arguments positionnels.
            **kwargs: Arguments nommés.
        """
        # nouvelle ligne pour compter les instances
        # print('taskcoachlib.gui.viewer.category.CategoryViewer')
        # CategoryViewer._instance_count = 0
        super().__init__(*args, **kwargs)
        self.filterUICommand.setChoice(
            self.settings.getboolean("view", "categoryfiltermatchall")
        )

    def createModeToolBarUICommands(self):
        """
        Crée et retourne les commandes pour la barre d'outils du mode.
        Returns :
            (tuple) : Les commandes de la barre d'outils du mode.
        """
        # pylint: disable=W0201
        self.filterUICommand = uicommand.CategoryViewerFilterChoice(
            settings=self.settings
        )
        # return super().createModeToolBarUICommands() + self.filterUICommand
        # TypeError: can only concatenate tuple (not "CategoryViewerFilterChoice") to tuple
        # Exception ignored in atexit callback: <built-in function _wxPyCleanup>
        return super().createModeToolBarUICommands() + (self.filterUICommand,)
