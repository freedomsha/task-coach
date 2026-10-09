# panel.py pour Tkinter, converti de wxPython
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
# Le fichier panel.py de wxPython gère l'ajout de contrôles à des sizers.
# Tkinter n'a pas de concept de "sizer" de la même manière,
# mais utilise des gestionnaires de géométrie comme pack, grid et place.
# La conversion se fera en utilisant ces gestionnaires. J'ai aussi fait en sorte
# que les classes soient des Frame plutôt que des Panel, ce qui est l'équivalent
# le plus proche dans Tkinter.

# J'ai converti le fichier panel.py en utilisant Tkinter.
# La principale différence est que Tkinter utilise des gestionnaires de
# géométrie (pack, grid) au lieu de sizers.
#
#     PanelWithBoxSizer : Utilise tk.Frame et le gestionnaire de géométrie pack.
#     C'est l'équivalent le plus proche de la disposition par défaut d'un BoxSizer.
#
#     BoxWithFlexGridSizer : J'ai utilisé tk.LabelFrame pour l'équivalent de
#     wx.StaticBox et le gestionnaire de géométrie grid pour imiter le comportement du FlexGridSizer.
#
#     BoxWithBoxSizer : Comme le précédent, j'ai utilisé tk.LabelFrame pour la
#     boîte statique et le gestionnaire pack pour la disposition des widgets internes.
#
# Le code inclut des exemples pour chaque classe, ce qui vous permettra de voir
# comment elles s'utilisent.
import tkinter as tk
from tkinter import ttk


class FrameWithBoxSizer(tk.Frame):
    """
    Une adaptation de PanelWithBoxSizer de wxPython.
    Utilise le gestionnaire de géométrie pack de Tkinter.
    """
    def __init__(self, parent, orientation=tk.VERTICAL, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.orientation = orientation
        self.pack(fill=tk.BOTH, expand=True)

    def fit(self):
        """
        Cette méthode n'a pas besoin de faire grand-chose avec pack,
        car les widgets s'ajustent automatiquement.
        """
        pass

    def add(self, control, *args, **kwargs):
        """
        Ajoute un contrôle à la boîte de sizer (pack).
        """
        if self.orientation == tk.VERTICAL:
            kwargs.setdefault('fill', tk.X)
            kwargs.setdefault('padx', 10)
            kwargs.setdefault('pady', 5)
        else:
            kwargs.setdefault('fill', tk.Y)
            kwargs.setdefault('padx', 5)
            kwargs.setdefault('pady', 10)

        control.pack(*args, **kwargs)


class BoxWithFlexGridSizer(tk.LabelFrame):
    """
    Une adaptation de BoxWithFlexGridSizer de wxPython.
    Utilise le gestionnaire de géométrie grid de Tkinter.
    """
    def __init__(self, parent, label, num_columns, growableCol=None, *args, **kwargs):
        super().__init__(parent, text=label, *args, **kwargs)
        self.num_columns = num_columns
        self.growableCol = growableCol
        self.row_counter = 0

        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configurer les colonnes redimensionnables si nécessaire
        if self.growableCol is not None:
            self.columnconfigure(self.growableCol, weight=1)

    def fit(self):
        """
        Cette méthode n'a pas besoin de faire grand-chose avec grid,
        car les widgets s'ajustent automatiquement.
        """
        pass

    def add(self, control, *args, **kwargs):
        """
        Ajoute un contrôle au FlexGridSizer (grid).
        """
        row = self.row_counter // self.num_columns
        column = self.row_counter % self.num_columns

        if isinstance(control, str):
            control = ttk.Label(self, text=control, anchor='e')

        kwargs.setdefault('padx', 5)
        kwargs.setdefault('pady', 5)
        kwargs.setdefault('sticky', 'w')

        control.grid(row=row, column=column, *args, **kwargs)
        self.row_counter += 1


class BoxWithBoxSizer(tk.LabelFrame):
    """
    Une adaptation de BoxWithBoxSizer de wxPython.
    Utilise le gestionnaire de géométrie pack de Tkinter.
    """
    def __init__(self, parent, label, orientation=tk.VERTICAL, *args, **kwargs):
        super().__init__(parent, text=label, *args, **kwargs)
        self.orientation = orientation
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

    def fit(self):
        """
        Cette méthode n'a pas besoin de faire grand-chose avec pack,
        car les widgets s'ajustent automatiquement.
        """
        pass

    def add(self, control, *args, **kwargs):
        """
        Ajoute un contrôle au sizer intérieur.
        """
        if self.orientation == tk.VERTICAL:
            kwargs.setdefault('fill', tk.X)
            kwargs.setdefault('padx', 5)
            kwargs.setdefault('pady', 5)
        else:
            kwargs.setdefault('fill', tk.Y)
            kwargs.setdefault('padx', 5)
            kwargs.setdefault('pady', 5)

        control.pack(*args, **kwargs)


# --- Exemple d'utilisation ---
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Exemple de Panneaux (Tkinter)")

    # Exemple de PanelWithBoxSizer
    panel_box = FrameWithBoxSizer(root, orientation=tk.VERTICAL)
    panel_box.add(ttk.Label(panel_box, text="Label 1"))
    panel_box.add(ttk.Entry(panel_box))
    panel_box.add(ttk.Button(panel_box, text="Bouton"))

    # Exemple de BoxWithFlexGridSizer
    flex_box = BoxWithFlexGridSizer(root, label="FlexGrid Panel", num_columns=2)
    flex_box.add("Nom:")
    flex_box.add(ttk.Entry(flex_box))
    flex_box.add("Prénom:")
    flex_box.add(ttk.Entry(flex_box))

    # Exemple de BoxWithBoxSizer
    static_box = BoxWithBoxSizer(root, label="Static Box Panel", orientation=tk.HORIZONTAL)
    static_box.add(ttk.Button(static_box.frame, text="OK"))
    static_box.add(ttk.Button(static_box.frame, text="Annuler"))

    root.mainloop()

