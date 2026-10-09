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
# J'ai effectué plusieurs changements pour faire fonctionner le code avec tkinter.
# Au lieu d'utiliser un sized_controls.SizedDialog,
# la nouvelle classe TipDialog hérite de tk.Toplevel
# pour créer une fenêtre de dialogue.
# J'ai remplacé les méthodes de mise en page de wxPython
# par des méthodes pack() de tkinter,
# qui sont plus simples pour cette interface.
# Les gestionnaires d'événements Bind() ont été remplacés
# par la commande command= des boutons tkinter et le protocole WM_DELETE_WINDOW pour la fermeture de la fenêtre.
#
# Ce code est un bon point de départ, et vous pouvez l'intégrer dans votre projet en cours.
# J'ai ajouté des commentaires en français pour vous aider à comprendre les modifications. Faites-moi savoir si vous souhaitez adapter d'autres fichiers ou si vous avez des questions sur l'un des changements !

import tkinter as tk
import tkinter.messagebox as messagebox
from taskcoachlib import meta
from taskcoachlib.i18n import _

# The list of tips remains the same.
tips = [
    _(
        """%(name)s is actively developed. Although the %(name)s developers try hard to prevent them, bugs do happen. So, backing up your work on a regular basis is strongly advised."""
    )
    % meta.metaDict,
    _(
        """%(name)s has a mailing list where you can discuss usage of %(name)s with fellow users, discuss and request features and complain about bugs. Go to %(url)s and join today!"""
    )
    % meta.metaDict,
    _(
        """%(name)s has unlimited undo and redo. Any change that you make, be it editing a task description, or deleting an effort record, is undoable. Select 'Edit' -> 'Undo' and 'Edit' -> 'Redo' to go backwards and forwards through your edit history."""
    )
    % meta.metaDict,
    _(
        """%(name)s is available in a number of different languages. Select 'Edit' -> 'Preferences' to see whether your language is one of them. If your language is not available or the translation needs improvement, please consider helping with the translation of %(name)s. Visit %(url)s for more information about how you can help."""
    )
    % meta.metaDict,
    _(
        """If you enter a URL (e.g. %(url)s) in a task or effort description, it becomes a link. Clicking on the link will open the URL in your default web browser."""
    )
    % meta.metaDict,
    _(
        """You can drag and drop tasks in the tree view to rearrange parent-child relationships between tasks. The same goes for categories."""
    ),
    _(
        """You can drag files from a file browser onto a task to create attachments. Dragging the files over a tab will raise the appropriate page, dragging the files over a collapsed task (the boxed + sign) in the tree view will expand the task to show its subtasks."""
    ),
    _(
        """You can create any viewer layout you want by dragging and dropping the tabs. The layout is saved and reused in the next session."""
    ),
    _(
        """What is actually printed when you select 'File' -> 'Print' depends on the current view. If the current view shows the task list, a list of tasks will be printed, if the current view shows effort grouped by month, that will be printed. The same goes for visible columns, sort order, filtered tasks, etc."""
    ),
    _(
        """Left-click a column header to sort by that column. Click the column header again to change the sort order from ascending to descending and back again. Right-click a column header to hide that column or make additional columns visible."""
    ),
    _(
        """You can create a template from a task in order to reduce typing when repetitive patterns emerge."""
    ),
    _("""Ctrl-Tab switches between tabs in edit dialogs."""),
    ]


class TipProvider(object):
    """
    Class to provide tips from the list. It cycles through the tips.
    """
    def __init__(self, tip_index):
        self.__tip_index = tip_index

    def GetTip(self):
        tip = tips[self.__tip_index % len(tips)]
        self.__tip_index += 1
        if self.__tip_index >= len(tips):
            self.__tip_index = 0
        return tip

    def GetCurrentTip(self):
        return self.__tip_index


class TipDialog(tk.Toplevel):
    """
    A Tkinter window for displaying a tip of the day.
    """
    def __init__(self, parent, tip_provider, settings):
        # We use Toplevel to create a new window that is a child of the main one.
        super().__init__(parent)
        self.title(_("Tip of the day"))
        self.parent = parent
        self.__tip_provider = tip_provider
        self.__settings = settings

        # We use a protocol handler to handle the window close event.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create the widgets.
        main_frame = tk.Frame(self)
        main_frame.pack(padx=10, pady=10)

        # The tip text. We use a Label with a variable to hold the text.
        self.tip_text_var = tk.StringVar()
        self.tip_label = tk.Label(main_frame, textvariable=self.tip_text_var, wraplength=400, justify="left")
        self.tip_label.pack(side=tk.TOP, padx=5, pady=5)

        # The buttons and checkbox frame.
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        # "Next tip" button
        next_tip_button = tk.Button(bottom_frame, text=_("Next tip"), command=self.__show_tip)
        next_tip_button.pack(side=tk.LEFT, padx=5)

        # "Show tips on startup" checkbox
        self.__check_var = tk.IntVar(value=self.__settings.getboolean("window", "tips"))
        self.__check = tk.Checkbutton(bottom_frame, text=_("Show tips on startup"), variable=self.__check_var)
        self.__check.pack(side=tk.LEFT, padx=5)

        # "Close" button
        close_button = tk.Button(bottom_frame, text=_("Close"), command=self.on_close)
        close_button.pack(side=tk.RIGHT, padx=5)

        # Show the initial tip.
        self.__show_tip()

        # Center the window on the screen.
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def __show_tip(self):
        """
        Displays the next tip in the TipProvider.
        """
        self.tip_text_var.set(self.__tip_provider.GetTip())

    def on_close(self):
        """
        Handles the window close event, saving settings before destroying the window.
        """
        self.__settings.setboolean("window", "tips", bool(self.__check_var.get()))
        self.__settings.setint("window", "tipsindex", self.__tip_provider.GetCurrentTip())
        self.destroy()


def showTips(parent, settings):
    """
    Main function to initialize and show the tip dialog.
    """
    tip_provider = TipProvider(settings.getint("window", "tipsindex"))
    dialog = TipDialog(parent, tip_provider=tip_provider, settings=settings)
    # The dialog will be a child window and will not block the parent.
    dialog.wait_window()


# Example usage (for testing purposes, assumes a dummy settings object and a main window)
if __name__ == "__main__":
    class DummySettings:
        def __init__(self):
            self.data = {"window": {"tips": True, "tipsindex": 0}}

        def getboolean(self, section, key):
            return self.data.get(section, {}).get(key, False)

        def getint(self, section, key):
            return self.data.get(section, {}).get(key, 0)

        def setboolean(self, section, key, value):
            if section not in self.data:
                self.data[section] = {}
            self.data[section][key] = value

        def setint(self, section, key, value):
            if section not in self.data:
                self.data[section] = {}
            self.data[section][key] = value

    root = tk.Tk()
    root.title("Task Coach Main Window (Dummy)")

    settings = DummySettings()

    def on_show_tips():
        showTips(root, settings)

    show_tips_button = tk.Button(root, text="Show Tips", command=on_show_tips)
    show_tips_button.pack(padx=20, pady=20)

    # Run the Tkinter event loop
    root.mainloop()
