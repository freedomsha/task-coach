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
# J'ai converti le widget Notebook de wxPython vers tkinter et ttk.
# Ce widget est utilisé pour gérer plusieurs pages ou onglets dans une interface graphique.
# La version originale utilisait wx.lib.agw.aui.AuiNotebook,
# un widget de carnet de notes plus avancé, mais
# ttk.Notebook est l'équivalent le plus proche et
# le plus courant dans la bibliothèque standard de tkinter.
#
# Pour que le code soit fonctionnel et autonome,
# j'ai également inclus des classes factices pour GridCursor, widgets, et artprovider.

# Points clés de la conversion :
#
#     Remplacement des classes : La classe Notebook hérite désormais de
#                                ttk.Notebook, l'équivalent standard de Tkinter.
#
#     Adaptation des méthodes :
#
#         La méthode AddPage a été modifiée pour utiliser la syntaxe de
#         ttk.Notebook.add().
#         L'option bitmap n'est pas nativement supportée par ttk.Notebook,
#         donc elle est simulée et ignorée dans l'implémentation.
#
#         La méthode ok parcourt les onglets du ttk.Notebook et
#         appelle la méthode ok sur chaque page (si elle existe),
#         comme dans l'original.
#
#     Simplification des styles : Les styles complexes de wx.lib.agw.aui ont
#                                 été remplacés par une utilisation standard
#                                 et plus simple de ttk.Notebook.

# Principales modifications et explications :
#
# Importation des modules : Utilisation de tkinter et tkinter.ttk.
# Héritage : La classe BookPage hérite de ttk.Frame .
# GridCursor : J'ai inclus la classe GridCursor car elle est utilisée pour positionner les éléments dans la page.  Elle est légèrement simplifiée pour Tkinter.
# Initialisation : Le constructeur __init__ initialise les attributs, y compris le nombre de colonnes, la colonne étirable, et la bordure. Les valeurs par défaut sont gérées directement dans la définition des arguments.
# Suppression de SetSizerAndFit : La méthode fit est vide car Tkinter gère la taille des widgets différemment de wxPython.  La taille est gérée par le gestionnaire de géométrie (grid dans ce cas).
# Gestion de la disposition avec grid : Au lieu d'utiliser un wx.GridBagSizer, j'utilise directement la méthode grid des widgets Tkinter pour les positionner.  J'utilise grid_columnconfigure pour configurer la colonne étirable .
# Gestion des flags : J'ai adapté les flags de wxPython à leurs équivalents Tkinter. Par exemple, wx.EXPAND est remplacé par tk.E+tk.W (Est + Ouest) pour étirer le widget horizontalement.
# Remplacement de wx.StaticLine : wx.StaticLine est remplacé par ttk.Separator pour créer une ligne de séparation horizontale.
# Remplacement de wx.StaticText : wx.StaticText est remplacé par ttk.Label.
# Adaptation des méthodes addEntry, addLine, __addControl et __createStaticTextControlIfNeeded : Ces méthodes ont été adaptées pour utiliser les widgets et les méthodes de positionnement de Tkinter.
#

import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from taskcoachlib.guitk import artprovidertk

# Logger pour ce fichier
log = logging.getLogger(__name__)

# # Simulation des classes externes
# class widgets:
#     class Dialog(tk.Toplevel):
#         def __init__(self, parent, *args, **kwargs):
#             super().__init__(parent, *args, **kwargs)
#             self.transient(parent)
#             self.grab_set()
#
#         def ok(self, event=None):
#             self.destroy()
#
# class artprovider:
#     @staticmethod
#     def GetBitmap(icon_name, size, scale):
#         # Simuler un objet bitmap
#         return f"SimulatedBitmap({icon_name})"


class GridCursor:
    """
    Classe utilitaire pour aider lors de l’ajout de contrôles à un GridBagSizer.
    Implémentation simplifiée pour Tkinter.
    """
    def __init__(self, columns):
        self.__columns = columns
        self.__nextPosition = (0, 0)

    def __updatePosition(self, colspan):
        x, y = self.__nextPosition
        x += colspan
        if x >= self.__columns:
            x = 0
            y += 1
        self.__nextPosition = (x, y)

    def next(self, colspan=1):
        position = self.__nextPosition
        self.__updatePosition(colspan)
        return position

    def maxRow(self):
        row, column = self.__nextPosition
        return max(0, row - 1) if column == 0 else row

    def getPosition(self, colspan=1):
        position = self.__nextPosition
        self.__updatePosition(colspan)
        return position


# Classe des pages
class BookPage(ttk.Frame):
    """Une page dans un cahier (notebook)."""
    def __init__(self, parent, *args, columns=None, growableColumn=None, **kwargs):
        """Initialise l'instance BookPage."""
        super().__init__(parent, *args, **kwargs)

        self._columns = columns if columns is not None else 2  # Valeur par défaut si columns n'est pas fourni
        self._position = GridCursor(self._columns)
        self._growableColumn = growableColumn if growableColumn is not None else self._columns - 1
        self._borderWidth = 5

        self._grid_columnconfigure = {}
        self._grid_rowconfigure = {}

        # Utilisation de grid au lieu de sizer
        self.grid_columnconfigure(self._growableColumn, weight=1)  # Colonne étirable

    def fit(self):
        """Adapte la taille de la page à son contenu."""
        # Pas besoin de SetSizerAndFit dans Tkinter, la gestion de la taille est différente
        pass

    def __defaultFlags(self, controls):
        """Renvoie les indicateurs par défaut pour placer une liste de contrôles."""
        labelInFirstColumn = isinstance(controls[0], str)
        flags = []
        for columnIndex in range(len(controls)):
            # flag = tk.ALL | tk.CENTER
            flag = tk.NSEW  # Remplacer par tk.NSEW pour étirer dans toutes les directions
            if columnIndex == 0 and labelInFirstColumn:
                # flag |= tk.LEFT
                flag += tk.W  # Aligner à gauche si c'est le label en première colonne
            else:
                # flag |= tk.E + tk.W  # Remplace wx.EXPAND par tk.E + tk.W
                flag += tk.E + tk.W  # Étirer horizontalement
            flags.append(flag)
        return flags

    def __determineFlags(self, controls, flagsPassed):
        """Fusionne les drapeaux par défaut avec ceux passés."""
        flagsPassed = flagsPassed or [None] * len(controls)
        defaultFlags = self.__defaultFlags(controls)
        return [
            defaultFlag if flagPassed is None else flagPassed
            for flagPassed, defaultFlag in zip(flagsPassed, defaultFlags)
        ]

    def addEntry(self, *controls, **kwargs):
        """Ajoute une ligne de contrôles."""
        flags = self.__determineFlags(controls, kwargs.get("flags", None))
        controls = [
            self.__createStaticTextControlIfNeeded(control)
            for control in controls
            if control is not None
        ]
        lastColumnIndex = len(controls) - 1

        for columnIndex, control in enumerate(controls):
            self.__addControl(
                columnIndex,
                control,
                flags[columnIndex],
                lastColumn=columnIndex == lastColumnIndex
            )

        if kwargs.get("growable", False):
            self.grid_rowconfigure(self._position.maxRow(), weight=1)

    def addLine(self):
        """Ajoute une ligne horizontale."""
        line = ttk.Separator(self, orient=tk.HORIZONTAL)  # Remplace wx.StaticLine par ttk.Separator
        self.__addControl(
            0, line, flag=tk.E+tk.W, lastColumn=True
        )  # Remplace wx.GROW par tk.E+tk.W

    def __addControl(self, columnIndex, control, flag, lastColumn):
        """Ajoute un contrôle à la grille."""
        colspan = max(self._columns - columnIndex, 1) if not lastColumn else 1
        position = self._position.next(colspan)
        control.grid(
            row=position[0],
            column=position[1],
            columnspan=colspan,
            sticky=flag,
            padx=self._borderWidth,
            pady=self._borderWidth
        )

    def __createStaticTextControlIfNeeded(self, control):
        """Crée un StaticText si nécessaire."""
        if isinstance(control, str):
            control = ttk.Label(self, text=control)  # Remplace wx.StaticText par ttk.Label
        return control


# Classe de base pour un carnet de notes
class BookMixin:
    """
    Un mixin pour les classes de carnet de notes.
    """
    def __init__(self, *args, **kwargs):
        self._bitmapSize = kwargs.pop("bitmap_size", (16, 16))
        super().__init__(*args, **kwargs)

    def AddPage(self, page, name, bitmap=None):
        """
        Ajoute une page au carnet de notes.

        Args :
            page (tk.Frame) : L'objet de la page.
            name (str) : Le nom de la page.
            bitmap (str, optional) : Le nom du bitmap. La valeur par défaut est None.
        """
        # Tkinter ne prend pas de bitmap dans AddPage, donc nous le simulons dans les commentaires
        # bitmap_img = artprovider.GetBitmap(bitmap, self._bitmapSize[0], 1)
        bitmap_img = artprovidertk.ArtProviderTk.GetBitmap(bitmap, self._bitmapSize[0], 1)
        # self.add(page, text=name)  # Unresolved attribute reference 'add' for class 'BookMixin'
        self.add(page, text=name, image=bitmap_img)
        # add est valable pour ttk.Notebook !

    def ok(self, *args, **kwargs):
        """
        Effectue l'action « ok » pour toutes les pages.
        """
        for page_id in self.tabs():
            page_widget = self.nametowidget(page_id)
            if hasattr(page_widget, "ok"):
                page_widget.ok(*args, **kwargs)


class Notebook(BookMixin, ttk.Notebook):
    """
    Un Notebook doté de fonctionnalités.
    """
    def __init__(self, parent, *args, **kwargs):
        # La logique de style est simplifiée pour Tkinter :
        # defaultStyle = kwargs.get("agwStyle", aui.AUI_NB_DEFAULT_STYLE)
        # kwargs["agwStyle"] = (
        #     defaultStyle
        #     & ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        #     & ~aui.AUI_NB_MIDDLE_CLICK_CLOSE
        # )
        super().__init__(parent, *args, **kwargs)


# Comment utiliser cette classe :
#
# Intègre cette classe dans ton fichier notebooktk.py.
# Dans ta classe Notebook, tu peux maintenant créer et ajouter des BookPage comme suit :
# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tkinter Notebook Example")
    root.geometry("400x300")

    notebook = Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # # Création de pages
    # page1 = ttk.Frame(notebook)
    # page2 = ttk.Frame(notebook)
    # Exemple d'utilisation dans la classe Notebook (notebooktk.py)(utiliser self au lieu de notebook)
    # page1 = BookPage(self, columns=2, growableColumn=1)  # self fait référence au Notebook
    page1 = BookPage(notebook, columns=2, growableColumn=1)  # self fait référence au Notebook
    page2 = BookPage(notebook, columns=2, growableColumn=1)  # self fait référence au Notebook
    page3 = BookPage(notebook, columns=2, growableColumn=1)  # self fait référence au Notebook

    page1.addEntry("Label 1:", ttk.Entry(page1))
    page1.addEntry("Label 2:", ttk.Entry(page1))
    # self.add(page1, text="Page 1") # Utilise la méthode add du Notebook (héritée de ttk.Notebook)
    # notebook.add(page1, text="Page 1") # Utilise la méthode add du Notebook (héritée de ttk.Notebook)

    # # Ajout de contenu aux pages
    label1 = ttk.Label(page1, text="This is Page 1")
    # label1.pack(padx=20, pady=20)
    # page1.__createStaticTextControlIfNeeded("This is Page 1")
    page1.addEntry("Texte 1", label1)

    label2 = ttk.Label(page2, text="This is Page 2")
    # label2.pack(padx=20, pady=20)
    page2.addEntry("Texte 2", label2)  # "This is Page 2" non visible !
    #

    label3 = ttk.Label(page3, text="This is Page 3")
    label3.pack(padx=20, pady=20)
    # # Ajout des pages au notebook
    notebook.AddPage(page1, "Page 1", bitmap="icon1")
    notebook.AddPage(page2, "Page 2", bitmap="icon2")
    notebook.AddPage(page3, "Page 3", bitmap="icon3")

    root.mainloop()

# Points importants :
#
# grid_columnconfigure et grid_rowconfigure : Ces méthodes sont utilisées
# pour configurer le comportement des colonnes et des lignes dans la grille.
# weight=1 indique que la colonne ou la ligne doit s'étirer pour
# remplir l'espace disponible.
# sticky : L'option sticky dans la méthode grid est utilisée pour
# spécifier comment le widget doit être aligné et étiré dans sa cellule de grille.
# tk.E+tk.W signifie "étirer à l'Est et à l'Ouest" (horizontalement).
# tk.ALL (ou tk.NSEW) signifie "étirer dans toutes les directions".
# Adaptation à Taskcoach : Tu devras adapter le contenu de chaque BookPage
# en fonction des besoins spécifiques de Taskcoach.
# Cela impliquera de recréer les widgets et
# la logique de chaque page de l'interface wxPython d'origine.

