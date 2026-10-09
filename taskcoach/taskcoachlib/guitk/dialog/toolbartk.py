# -*- coding: utf-8 -*-

"""
Task Coach - Votre gestionnaire de tâches amical
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre option) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION ou D'ADÉQUATION À UN USAGE PARTICULIER. Voir la
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Si ce n'est pas le cas, consultez <http://www.gnu.org/licenses/>.
"""
# Pour convertir toolbar.py en Python avec Tkinter, nous devons réimplémenter la logique de l'éditeur de barre d'outils. Étant donné que Tkinter ne possède pas de widget direct comme HyperTreeList de wxPython, une approche alternative est de simuler cette fonctionnalité en utilisant ttk.Treeview.
#
# Voici une tentative de conversion de toolbar.py et de son intérieur _ToolBarEditorInterior en utilisant tkinter et ttk. La classe _AutoWidthTree est remplacée par une logique Tkinter qui utilise les méthodes de ttk.Treeview.
#
# J'ai inclus une version simplifiée du fichier autowidth.py que vous avez fourni pour que le code soit autonome. J'ai également simulé les classes BalloonTipManager, widgets.Dialog, uicommand, et _ pour que l'exemple soit exécutable.

# Le code ci-dessus recrée la logique de l'éditeur de barre d'outils en utilisant les widgets standard de Tkinter.
#
# Changements clés :
#
#     GUI Framework : Remplacement de wx par tkinter et ttk.
#
#     Tree Widget : wx.lib.agw.hypertreelist.HyperTreeList est remplacé par ttk.Treeview.
#
#     Classes Simulées : Comme Tkinter est un framework de GUI différent, les classes et modules d'origine comme BalloonTipManager, widgets.Dialog, et uicommand ont été simulés pour permettre l'exécution du code.
#
#     Logique de l'éditeur : L'interface a été conçue pour avoir deux Treeview côte à côte, avec des boutons pour déplacer les commandes de l'un à l'autre, simulant le comportement de glisser-déposer de la version wxPython.
#
#     Gestion des événements : Les liaisons d'événements wx.EVT_BUTTON sont remplacées par des commandes directes sur les boutons Tkinter.

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import logging

from taskcoachlib.widgetstk import autowidthtk as autowidth
from taskcoachlib.widgetstk import dialogtk
from taskcoachlib.help.balloontipstk import BalloonTipManager
from taskcoachlib.guitk import uicommand
from taskcoachlib.guitk.toolbarttk import ToolBar
from taskcoachlib.i18n import _

# Simuler les classes et modules externes pour l'exemple
log = logging.getLogger(__name__)


# class BalloonTipManager:
#     def __init__(self):
#         pass
#
#
# class MockDialog(tk.Toplevel):
#     def __init__(self, parent, *args, **kwargs):
#         super().__init__(parent, *args, **kwargs)
#         self.transient(parent)
#         self.grab_set()
#
#     def ok(self, event=None):
#         self.destroy()
#
#
# class widgets:
#     Dialog = MockDialog
#
#
# class uicommand:
#     class UICommand:
#         def __init__(self, name):
#             self._name = name
#
#         def uniqueName(self):
#             return self._name
#
#     class UIGroup:
#         def __init__(self, name, commands):
#             self._name = name
#             self._commands = commands
#
#         def uiCommands(self, cache=False):
#             return self._commands
#
#
# class _:
#     def __init__(self, text):
#         self.text = text
#     def __str__(self):
#         return self.text
#
# _ = lambda s: s


# class AutoColumnWidthMixin:
#     """A mixin for ttk.Treeview to automatically adjust column widths."""
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.bind("<Configure>", self.on_resize)
#         self.fixed_columns = []
#         self.resize_column = None
#
#     def on_resize(self, event):
#         if self.winfo_width() > 1:
#             total_width = self.winfo_width()
#             fixed_width = sum(self.column(col, 'width') for col in self.fixed_columns)
#
#             if self.resize_column:
#                 resize_width = total_width - fixed_width
#                 if resize_width > 50:
#                     self.column(self.resize_column, width=resize_width)


class _AutoWidthTree(autowidth.AutoColumnWidthMixin, ttk.Treeview):
    """Simule _AutoWidthTree en utilisant ttk.Treeview."""
    # def __init__(self, *args, **kwargs):
    def __init__(self, parent, *args, **kwargs):
        # super().__init__(*args, **kwargs)
        # Treeview de base pour simuler HyperTreeList
        super().__init__(parent, *args, columns=("Command",), show="tree", **kwargs)
        self.column("#0", width=0, stretch=tk.NO)  # Masquer la première colonne de l'arbre
        self.column("Command", anchor="w", width=250)  # ne pas mettre stretch=tk.NO, sinon l’auto-width sera bloqué
        self.heading("Command", text="Command")

        # Activer l’auto-ajustement des colonnes
        self.SetResizeColumn("Command")
        self.bind("<Configure>", self._on_autowidth_resize)

    def GetRootItem(self):
        # Simuler la racine pour Treeview (qui est la chaîne vide)
        return ''

    def GetChildren(self, item):
        # Obtenir les enfants d'un item
        return self.get_children(item)

    def GetItemData(self, item):
        # Récupérer les données associées à l'item (PyData dans wx)
        return self.set(item, 'data')

    def SetItemData(self, item, data):
        # Stocker les données associées à l'item
        self.set(item, 'data', data)

    def GetItemPyData(self, item):  # Pour la compatibilité avec l'ancien code (commenté)
        # return self.GetItemData(item)
        return self._item_to_object[item]

    def SetItemPyData(self, item, data): # Pour la compatibilité avec l'ancien code (commenté)
        self.SetItemData(item, data)

    def EnableItem(self, item, enable):
        # Simuler l'activation/désactivation d'un item (en changeant la couleur)
        if enable:
            self.tag_remove('disabled', item)
        else:
            self.tag_add('disabled', item)

        self.tag_configure('disabled', foreground='gray')

    def SelectItem(self, item):
        self.selection_set(item)
        self.focus(item)

    # Note: wx.lib.agw.hypertreelist n'utilise pas de méthode 'Append' directe
    # mais plutôt 'AppendItem', mais le Treeview utilise 'insert'. Nous allons
    # nous adapter à l'insertion standard de Tkinter.
    def AppendItem(self, parent, text, data=None):
        item = self.insert(parent, 'end', text=text, values=(text,))
        if data is not None:
            self.SetItemData(item, data)
        return item

    def InsertItem(self, parent, index, text, data=None):
        item = self.insert(parent, index, text=text, values=(text,))
        if data is not None:
            self.SetItemData(item, data)
        return item

    def GetItem(self, item):
        # Simuler un objet 'TreeItem' pour Tkinter
        class TreeItemMock:
            def __init__(self, tree, item_id):
                self.tree = tree
                self.id = item_id

            def GetText(self):
                return self.tree.item(self.id, 'text')

            def GetData(self):
                return self.tree.GetItemData(self.id)

        return TreeItemMock(self, item)

    def ToggleAutoResizing(self, enable):
        # Méthode simulée
        pass

    def DeleteAllItems(self):
        self.delete(*self.get_children())

    def GetRootItem(self):
        return ''

    def AddRoot(self, text):
        # Dans Treeview, la racine est implicite ('')
        return ''

    def Freeze(self):
        # Simuler Freeze/Thaw
        pass
    def Thaw(self):
        pass


class _ToolBarEditorInterior(ttk.Frame):
    # def __init__(self, parent, toolbar, settings, *args, **kwargs):
    def __init__(self, parent, toolbar, settings):
        self.__toolbar = toolbar
        # Initialiser __visible avec la perspective actuelle de la barre d'outils
        self.__visible = [cmd for cmd in self.__toolbar.uiCommands() if cmd is not None]  # Simplification pour l'initialisation Tk

        # super().__init__(parent, *args, **kwargs)
        # self.__toolbar = toolbar
        self.__settings = settings
        super().__init__(parent)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        # Simuler wx.ImageList - Tkinter n'a pas d'ImageList direct pour Treeview, on utilise des tags/texte.
        self.__imgListIndex = {}

        vsizer = ttk.Frame(self)
        vsizer.grid(row=0, column=0, columnspan=4, sticky="ew")

        # Aperçu de la barre d'outils (Preview)
        # Tkinter n'a pas de StaticBox direct, on utilise un LabelFrame
        sb_preview = ttk.LabelFrame(vsizer, text=_("Preview"))
        sb_preview.pack(fill="x", padx=5, pady=5)

        # Utiliser ToolBar
        self.__preview = ToolBar(sb_preview, settings, self.__toolbar.GetToolBitmapSize())
        self.__preview.pack(fill="x", padx=5, pady=5)
        self.__HackPreview()

        # self.__visibleCommands = _AutoWidthTree(self, columns=("command_name"), show="tree", selectmode="extended")
        # self.__remainingCommands = _AutoWidthTree(self, columns=("command_name"), show="tree", selectmode="extended")
        #
        # self.__visibleCommands.column("#0", width=0, stretch=tk.NO)
        # self.__visibleCommands.heading("#0", text="Visible")
        # self.__visibleCommands.column("command_name", width=250, stretch=tk.NO)
        # self.__visibleCommands.heading("command_name", text=_("Visible Commands"))
        #
        # self.__remainingCommands.column("#0", width=0, stretch=tk.NO)
        # self.__remainingCommands.heading("#0", text="Remaining")
        # self.__remainingCommands.column("command_name", width=250, stretch=tk.NO)
        # self.__remainingCommands.heading("command_name", text=_("Remaining Commands"))
        #
        # self.__visibleCommands.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        # self.__remainingCommands.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        # Cadre principal pour les listes et boutons
        hsizer = ttk.Frame(self)
        hsizer.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        hsizer.columnconfigure(0, weight=1)
        hsizer.columnconfigure(2, weight=1)
        hsizer.rowconfigure(0, weight=1)

        # Liste des commandes restantes (Available tools)
        sb_remaining = ttk.LabelFrame(hsizer, text=_("Available tools"))
        sb_remaining.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        sb_remaining.columnconfigure(0, weight=1)
        sb_remaining.rowconfigure(0, weight=1)

        self.__remainingCommands = _AutoWidthTree(sb_remaining, selectmode="browse")
        self.__remainingCommands.grid(row=0, column=0, sticky="nsew")
        self.__remainingCommands.bind("<<TreeviewSelect>>", self.__OnRemainingSelectionChanged)

        # # Buttons
        # button_frame = ttk.Frame(self)
        # button_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)
        #
        # move_right_btn = ttk.Button(button_frame, text=">", command=self.__move_command_to_remaining)
        # move_right_btn.pack(pady=5)
        #
        # move_left_btn = ttk.Button(button_frame, text="<", command=self.__move_command_to_visible)
        # move_left_btn.pack(pady=5)

        # Boutons Afficher/Masquer (Show/hide buttons)
        btnSizer_show_hide = ttk.Frame(hsizer)
        btnSizer_show_hide.grid(row=0, column=1, sticky="ns", padx=3, pady=3)

        self.__showButton = ttk.Button(btnSizer_show_hide, text=">", command=self.__onShow, state=tk.DISABLED)
        self.__showButton.pack(pady=5)
        self.__hideButton = ttk.Button(btnSizer_show_hide, text="<", command=self.__onHide, state=tk.DISABLED)
        self.__hideButton.pack(pady=5)

        # Liste des commandes visibles (Tools)
        sb_visible = ttk.LabelFrame(hsizer, text=_("Tools"))
        sb_visible.grid(row=0, column=2, sticky="nsew", padx=3, pady=3)
        sb_visible.columnconfigure(0, weight=1)
        sb_visible.rowconfigure(0, weight=1)

        self.__visibleCommands = _AutoWidthTree(sb_visible, selectmode="browse")
        self.__visibleCommands.grid(row=0, column=0, sticky="nsew")
        self.__visibleCommands.bind("<<TreeviewSelect>>", self.__OnVisibleSelectionChanged)

        # Boutons Déplacer (Move buttons)
        btnSizer_move = ttk.Frame(hsizer)
        btnSizer_move.grid(row=0, column=3, sticky="ns", padx=3, pady=3)

        self.__moveUpButton = ttk.Button(btnSizer_move, text="▲", command=self.__onMoveUp, state=tk.DISABLED)
        self.__moveUpButton.pack(pady=5)
        self.__moveDownButton = ttk.Button(btnSizer_move, text="▼", command=self.__onMoveDown, state=tk.DISABLED)
        self.__moveDownButton.pack(pady=5)

        self.__PopulateRemainingCommands()
        self.__PopulateVisibleCommands()

        self.__remainingSelection = None
        self.__visibleSelection = None

        # Simuler CallAfter et BalloonTip
        # Tkinter ne gère pas CallAfter de la même manière pour les dialogues
        # On exécute le BalloonTip directement après l'initialisation
        BalloonTipManager().AddBalloonTip(
            settings,
            "customizabletoolbars_dnd",
            self.__visibleCommands,
            title=_("Drag and drop (Simulated)"),
            message=_(
                """Reorder toolbar buttons by drag and dropping them in this list."""
            ),
        )

        # self.__populate()

    def __OnRemainingSelectionChanged(self, event):
        selected_item = self.__remainingCommands.selection()
        self.__remainingSelection = selected_item[0] if selected_item else None
        self.__showButton.config(state=tk.NORMAL if self.__remainingSelection is not None else tk.DISABLED)

    def __move_command_to_remaining(self):
        selected_items = self.__visibleCommands.selection()
        if not selected_items:
            return

        for item in selected_items:
            item_text = self.__visibleCommands.item(item, 'values')[0]
            self.__remainingCommands.insert("", "end", values=(item_text,))
            self.__visibleCommands.delete(item)

    def __OnVisibleSelectionChanged(self, event):
        selected_item = self.__visibleCommands.selection()
        self.__visibleSelection = selected_item[0] if selected_item else None

        is_selected = self.__visibleSelection is not None
        self.__hideButton.config(state=tk.NORMAL if is_selected else tk.DISABLED)

        if is_selected:
            children = self.__visibleCommands.GetChildren(self.__visibleCommands.GetRootItem())
            idx = children.index(self.__visibleSelection)
            self.__moveUpButton.config(state=tk.NORMAL if idx != 0 else tk.DISABLED)
            self.__moveDownButton.config(state=tk.NORMAL if idx != len(children) - 1 else tk.DISABLED)
        else:
            self.__moveUpButton.config(state=tk.DISABLED)
            self.__moveDownButton.config(state=tk.DISABLED)

    def __move_command_to_visible(self):
        selected_items = self.__remainingCommands.selection()
        if not selected_items:
            return

        for item in selected_items:
            item_text = self.__remainingCommands.item(item, 'values')[0]
            self.__visibleCommands.insert("", "end", values=(item_text,))
            self.__remainingCommands.delete(item)

    def __onHide(self):
        if not self.__visibleSelection:
            return

        children = self.__visibleCommands.GetChildren(self.__visibleCommands.GetRootItem())
        idx = children.index(self.__visibleSelection)

        # Récupérer l'objet uiCommand
        uiCommand = self.__visibleCommands.GetItemData(self.__visibleSelection)

        # Supprimer de la liste visible
        self.__visibleCommands.delete(self.__visibleSelection)
        self.__visibleSelection = None
        self.__hideButton.config(state=tk.DISABLED)
        del self.__visible[idx]

        # Si c'est une commande, la réactiver dans la liste restante
        if isinstance(uiCommand, uicommand.UICommand):
            for child in self.__remainingCommands.GetChildren(self.__remainingCommands.GetRootItem()):
                if self.__remainingCommands.GetItemData(child) == uiCommand:
                    self.__remainingCommands.EnableItem(child, True)
                    break

        self.__HackPreview()
        self.__OnVisibleSelectionChanged(None) # Mettre à jour les boutons de mouvement

    def __onShow(self):
        if not self.__remainingSelection:
            return

        # Récupérer l'objet uiCommand
        uiCommand = self.__remainingCommands.GetItemData(self.__remainingSelection)

        if uiCommand is None:
            text = _('Separator')
        elif isinstance(uiCommand, int):
            text = _('Spacer')
        else:
            text = uiCommand.getHelpText()

        # Ajouter à la liste visible
        item = self.__visibleCommands.AppendItem(self.__visibleCommands.GetRootItem(), text, data=uiCommand)
        self.__visible.append(uiCommand)

        # Si c'est une commande, la désactiver dans la liste restante
        if isinstance(uiCommand, uicommand.UICommand):
            self.__remainingCommands.EnableItem(self.__remainingSelection, False)
            self.__remainingSelection = None
            self.__showButton.config(state=tk.DISABLED)

        self.__visibleCommands.SelectItem(item) # Sélectionner l'élément nouvellement ajouté
        self.__HackPreview()

    def __Swap(self, delta):
        if not self.__visibleSelection:
            return

        children = self.__visibleCommands.GetChildren(self.__visibleCommands.GetRootItem())
        index = children.index(self.__visibleSelection)
        new_index = index + delta

        if new_index < 0 or new_index >= len(children):
            return

        # Récupérer l'item sélectionné et ses données
        selected_item_id = self.__visibleSelection
        text = self.__visibleCommands.item(selected_item_id, 'text')
        data = self.__visibleCommands.GetItemData(selected_item_id)

        # Supprimer et réinsérer
        self.__visibleCommands.delete(selected_item_id)

        # Treeview insert prend l'index *avant* lequel insérer
        item = self.__visibleCommands.InsertItem(self.__visibleCommands.GetRootItem(), new_index, text, data=data)

        # Mettre à jour la liste interne __visible
        self.__visible[index], self.__visible[new_index] = self.__visible[new_index], self.__visible[index]

        self.__visibleCommands.SelectItem(item)
        self.__HackPreview()
        self.__OnVisibleSelectionChanged(None) # Mettre à jour les boutons de mouvement

    def __onMoveUp(self):
        self.__Swap(-1)

    def __onMoveDown(self):
        self.__Swap(1)

    # Note: La gestion du glisser-déposer (Drag & Drop) est complexe et dépendante du framework.
    # Dans Tkinter, cela nécessite des bindings <B1-Motion>, <ButtonRelease-1> et une
    # logique de positionnement Treeview complexe. Dans cette version, nous nous
    # concentrons sur les boutons haut/bas pour la réorganisation, qui est
    # l'alternative la plus simple au D&D.

    def __HackPreview(self):
        # Récupérer la perspective de la barre d'outils
        self.__preview.loadPerspective(self.getToolBarPerspective(), customizable=False)
        for uiCommand in self.__preview.visibleUICommands():
            if uiCommand is not None and not isinstance(uiCommand, int):
                # Dans wxPython, on 'unbind' la commande de la barre d'outils
                # Ici, on s'assure que le bouton de prévisualisation est actif (enabled)
                uiCommand.unbind(self.__preview, uiCommand.id)
                self.__preview.EnableTool(uiCommand.id, True)

    def __populate(self):
        # Simuler les commandes
        all_commands = [
            uicommand.UICommand("New Task"),
            uicommand.UICommand("Delete Task"),
            uicommand.UICommand("Mark Completed"),
            uicommand.UICommand("Add Note"),
            uicommand.UICommand("Add Attachment")
        ]

        self.__visible = [uicommand.UICommand("New Task"), uicommand.UICommand("Delete Task")]
        self.__PopulateVisibleCommands(self.__visible)

        remaining = [cmd for cmd in all_commands if cmd.uniqueName() not in [vc.uniqueName() for vc in self.__visible]]
        self.__Populate(self.__remainingCommands, remaining)

    # def __Populate(self, tree_widget, commands):
    #     tree_widget.delete(*tree_widget.get_children())
    #     for command in commands:
    #         tree_widget.insert("", "end", values=(command.uniqueName(),))

    def __Populate(self, tree, uiCommands, enableCallback):
        tree.Freeze()
        try:
            tree.DeleteAllItems()
            root = tree.AddRoot("Root") # '' dans Treeview

            for uiCommand in uiCommands:
                if uiCommand is None:
                    text = _("Separator")
                elif isinstance(uiCommand, int):
                    text = _("Spacer")
                else:
                    text = uiCommand.getHelpText()

                item = tree.AppendItem(root, text)

                if uiCommand is not None and not isinstance(uiCommand, int):
                    # Pas de SetItemImage direct dans ttk.Treeview sans extensions
                    # On utilise l'activation/désactivation
                    tree.EnableItem(item, enableCallback(uiCommand))

                # Stocker l'objet uiCommand dans les données de l'item
                tree.SetItemData(item, uiCommand)
        finally:
            tree.Thaw()

    def __PopulateRemainingCommands(self):
        all_uiCommands = self.__toolbar.uiCommands(cache=False)

        def enableCallback(uiCommand):
            if isinstance(uiCommand, uicommand.UICommand):
                # La commande est disponible si elle n'est PAS dans la liste visible
                return uiCommand not in self.__visible
            return True # Séparateur et Espaceur toujours disponibles

        # Commandes restantes : Séparateur (None), Espaceur (1), et les UICommand non visibles
        commands_to_show = [None, 1] + [
            uiCommand for uiCommand in all_uiCommands
            if isinstance(uiCommand, uicommand.UICommand)
        ]

        self.__Populate(
            self.__remainingCommands,
            commands_to_show,
            enableCallback,
        )

    # def __PopulateVisibleCommands(self, commands):
    #     self.__visibleCommands.delete(*self.__visibleCommands.get_children())
    #     for command in commands:
    #         self.__visibleCommands.insert("", "end", values=(command.uniqueName(),))

    def __PopulateVisibleCommands(self):
        # Pour les commandes visibles, on suppose qu'elles sont toutes activées (True)
        self.__Populate(self.__visibleCommands, self.__visible, lambda x: True)

    def getToolBarPerspective(self):
        names = []
        # for item in self.__visibleCommands.get_children():
        #     names.append(self.__visibleCommands.item(item, 'values')[0])
        # Parcourir la liste interne __visible, qui est l'ordre réel
        for uiCommand in self.__visible:
            if uiCommand is None:
                names.append("Separator")
            elif isinstance(uiCommand, int):
                names.append("Spacer")
            else:
                names.append(uiCommand.uniqueName())
        return ",".join(names)

    def createToolBarUICommands(self):
        return self.__toolbar.uiCommands(cache=False)


class ToolBarEditor(BalloonTipManager, dialogtk.Dialog):
    def __init__(self, toolbar, settings, parent,  *args, **kwargs):
        self.__toolbar = toolbar
        self.__settings = settings
        # self.title(_("Toolbar Customizer"))
        # Le titre de la boîte de dialogue doit être défini au début
        dialog_title = _("Customize Toolbar")
        # super().__init__(parent, *args, **kwargs)
        # 1. Appel Correct du chaînage d'héritage (MRO)
        # On passe le 'parent' au premier super() qui doit le relayer jusqu'à tk.Toplevel
        # J'ajoute l'argument 'title' pour corriger la première erreur ET je passe le 'parent'
        # Note : Si widgets.Dialog attend aussi 'parent' en premier, c'est crucial.
        super().__init__(parent, title=dialog_title, *args, **kwargs)
        self.geometry("900x700")
        self.center_window()

        # self._interior = _ToolBarEditorInterior(self, self.__toolbar, self.__settings)
        # Retire ces lignes ! Elles sont maintenant gérées par dialogtk.Dialog.__init__
        # self._interior = self.createInterior()
        # self._interior.pack(fill="both", expand=True)

        # # Buttons OK/Cancel
        # button_frame = ttk.Frame(self)
        # button_frame.pack(fill="x", pady=5)
        #
        # ok_btn = ttk.Button(button_frame, text=_("OK"), command=self.ok_and_save)
        # ok_btn.pack(side="right", padx=5)
        #
        # cancel_btn = ttk.Button(button_frame, text=_("Cancel"), command=self.destroy)
        # cancel_btn.pack(side="right", padx=5)
        self.create_buttons()

    def center_window(self):
        # Centrer la fenêtre sur l'écran
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def createInterior(self, parent):
        """
            Crée le contenu principal de l'éditeur (ToolBarEditorInterior)
            dans le conteneur fourni par la classe Dialog.
            """
        # L'intérieur doit être créé dans le 'parent' qui est le cadre interne de la boîte de dialogue (self._panel dans le code précédent).
        # return _ToolBarEditorInterior(self.__toolbar, self.__settings, self._panel)
        return _ToolBarEditorInterior(parent, self.__toolbar, self.__settings)

    def create_buttons(self):
        # Boutons OK/Cancel en bas
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)

        ok_btn = ttk.Button(button_frame, text=_("OK"), command=self.ok_and_save)
        ok_btn.pack(side="right", padx=5)

        cancel_btn = ttk.Button(button_frame, text=_("Cancel"), command=self.destroy)
        cancel_btn.pack(side="right", padx=5)

    # def ok_and_save(self):
    #     self.ok()
    #     self.__toolbar.savePerspective(self._interior.getToolBarPerspective())

    def ok_and_save(self, event=None):
        self.__toolbar.savePerspective(self._interior.getToolBarPerspective())
        super().ok(event=event)


# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    # Assurez-vous d'avoir un Tk() racine même si vous le cachez.
    root = tk.Tk()
    # root.withdraw()

    class FinalMockToolBar:
        """Mock ToolBar pour l'exemple final, plus complet."""
        def __init__(self):
            self._perspective = "New Task,Separator,Delete Task"

        def savePerspective(self, perspective):
            print(f"Saving perspective: {perspective}")
            self._perspective = perspective

        def uiCommands(self, cache=False):
            # Commandes disponibles (incluant séparateur et espaceur pour la liste restante)
            return [
                uicommand.UICommand("New Task", "new"),
                uicommand.UICommand("Delete Task", "delete"),
                uicommand.UICommand("Mark Completed", "completed"),
                uicommand.UICommand("Add Note"),
                uicommand.UICommand("Add Attachment"),
                None,  # Séparateur
                1,  # Espaceur
            ]

        def visibleUICommands(self):
            # La barre d'outils réelle doit savoir quelles commandes sont visibles
            # (pour l'initialisation de l'éditeur)
            all_cmds = {cmd.uniqueName(): cmd for cmd in self.uiCommands() if isinstance(cmd, uicommand.UICommand)}
            visible = []
            for name in self._perspective.split(','):
                if name == "Separator":
                    visible.append(None)
                elif name == "Spacer":
                    visible.append(1)
                elif name in all_cmds:
                    visible.append(all_cmds[name])
            return visible

        def GetToolBitmapSize(self):
            return (16, 16) # Taille par défaut pour la simulation

    class MockSettings:
        pass

    toolbar = FinalMockToolBar()
    settings = MockSettings()

    dialog = ToolBarEditor(toolbar=toolbar, settings=settings, parent=root)
    root.mainloop()

