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

Module `autowidthtk.py`

Ce module fournit le mixin `AutoColumnWidthMixin`, qui permet de redimensionner
automatiquement une colonne dans un contrôle à colonnes (par exemple, `wx.ListCtrl`,
`wx.TreeListCtrl`, ou `wx.lib.agw.hypertreelist.HyperTreeList`).

Fonctionnalités principales :
- Ajuste dynamiquement la largeur d'une colonne pour utiliser tout l'espace
  disponible sans créer d'espace inutile ou de barres de défilement horizontales.
- Gère les événements comme le redimensionnement ou le glissement des colonnes.

Dépendances :
- wxPython : Ce mixin suppose que les classes qui l'utilisent héritent de
  `wx.Window` ou de contrôles similaires (`wx.ListCtrl`, `wx.TreeListCtrl`).

Classes :
- `AutoColumnWidthMixin` : Fournit le comportement de redimensionnement
  automatique des colonnes.

Avertissements :
- Lorsque vous utilisez ce mixin, assurez-vous que votre contrôle est configuré
  pour un mode "rapport" (report mode) si nécessaire.
- Si vous surchargez `EVT_SIZE`, appelez `event.Skip()` pour garantir que la
  méthode `OnResize` du mixin est appelée.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.

#     Requête réussie
#
# La conversion directe de autowidth.py de wxPython vers Tkinter n'est pas possible.
# La logique et l'architecture des deux frameworks sont fondamentalement différentes.
#  Le module autowidth.py est un mixin wxPython, une classe conçue pour être héritée par d'autres classes wxPython comme wx.ListCtrl ou wx.TreeListCtrl afin de leur ajouter une fonctionnalité de redimensionnement automatique des colonnes.
#
# Différences fondamentales entre wxPython et Tkinter
#
#     Architecture des widgets :
#
#         wxPython : Il utilise une approche orientée objet avec des classes de widgets spécifiques qui ont des méthodes et des attributs bien définis pour gérer leur comportement et leur apparence (ex: GetColumnWidth, SetColumnWidth, Bind, Unbind). Le mixin dans le fichier autowidth.py s'appuie directement sur ces méthodes pour fonctionner.
#
#         Tkinter : Bien que basé sur Tcl/Tk, il encapsule les commandes Tcl dans des classes Python. L'équivalent de wx.ListCtrl est le ttk.Treeview. Le redimensionnement automatique des colonnes n'est pas géré de la même manière dans ttk.Treeview et ne dispose pas des mêmes mécanismes de liaison d'événements (Bind, Unbind) pour le glissement des colonnes ou le redimensionnement de la fenêtre.
#
#     Gestion des événements :
#
#         wxPython : Il utilise un système de liaison d'événements basé sur des types d'événements spécifiques (wx.EVT_SIZE, wx.EVT_LIST_COL_BEGIN_DRAG, etc.) pour réagir aux actions de l'utilisateur ou du système.
#
#         Tkinter : Il utilise une méthode bind() pour associer des fonctions à des événements génériques de l'interface utilisateur, tels que <Configure> pour les changements de taille ou <B1-Motion> pour le glissement de la souris. Ces événements ne correspondent pas directement à ceux de wxPython.
#
#     Contexte du mixin :
#
#         Le mixin AutoColumnWidthMixin est fortement lié aux spécificités de wxPython, notamment aux méthodes de la classe wx.ListCtrl (ou similaires). Il utilise des fonctionnalités comme super().__init__(*args, **kwargs) pour s'intégrer dans l'arbre d'héritage de wxPython.
#
# Approche recommandée pour Tkinter
#
# Au lieu de tenter une conversion directe, il faut réimplémenter la fonctionnalité pour un widget ttk.Treeview de Tkinter. Le ttk.Treeview possède une option stretch qui peut être configurée pour redimensionner automatiquement une colonne pour remplir l'espace restant, ce qui est l'objectif principal du mixin wxPython.
#
# Pour réaliser une fonctionnalité similaire à celle d' autowidth.py, voici une approche :
#
#     Identifier la colonne à redimensionner : Déterminez l'identifiant de la colonne dans votre ttk.Treeview que vous souhaitez redimensionner automatiquement.
#
#     Gérer l'événement de redimensionnement : Liez l'événement <Configure> de la fenêtre parent au widget ttk.Treeview. Cet événement se déclenche lorsque la fenêtre est redimensionnée.
#
#     Ajuster la largeur des colonnes : Dans la fonction liée à l'événement <Configure>, calculez l'espace disponible. Parcourez toutes les colonnes du ttk.Treeview  et déduisez leur largeur fixe de la largeur totale de la fenêtre. L'espace restant est alloué à la colonne "auto-ajustable" à l'aide de treeview.column("colonne_id", width=nouvelle_largeur).
#
#     Gérer le glissement des colonnes : Tkinter ne propose pas de gestion native pour le glissement d'une colonne de ttk.Treeview. Cependant, des solutions existent pour gérer manuellement les événements de la souris (<B1-Motion>, <ButtonRelease-1>) pour simuler le redimensionnement des colonnes.
#
#     Rechercher des modules existants : Il est possible qu'un module tiers similaire existe déjà pour Tkinter.
#
# En résumé, la migration nécessite une réécriture complète de la logique en utilisant les outils et les méthodes propres à Tkinter, plutôt qu'une conversion ligne par ligne.

# Le fichier autowidth.py que vous avez fourni est un mixin wxPython,
# une classe qui fournit des fonctionnalités de redimensionnement automatique
# des colonnes pour des widgets wxPython comme ListCtrl et HyperTreeList.
#
# Inutilité de la conversion directe
#
# La conversion de ce fichier n'est pas pertinente pour Tkinter. Voici pourquoi :
#
#     Différences d'architecture : Les mixins et les systèmes d'événements de
#     wxPython sont fondamentalement différents de ceux de Tkinter.
#     Vous ne pouvez pas simplement traduire les appels de méthodes et
#     les gestionnaires d'événements de l'un à l'autre.
#
#     Absence de fonctionnalités équivalentes : Tkinter et son module ttk ne
#     possèdent pas de concept natif de mixin AutoColumnWidthMixin ou d'une
#     gestion aussi complexe du redimensionnement de colonnes.
#     Les widgets ttk.Treeview et ttk.Listbox gèrent la largeur des colonnes différemment.
#
#     Conflit de dépendances : Le code wxPython dépend de sa propre bibliothèque
#     pour la gestion des fenêtres et des événements. Tenter de le "convertir"
#     directement impliquerait de réécrire entièrement sa logique pour utiliser
#     les concepts de Tkinter, ce qui équivaut à un nouveau développement plutôt qu'à une conversion.
#
# Solution pour Tkinter
#
# Pour obtenir une fonctionnalité similaire de redimensionnement automatique
# des colonnes dans Tkinter,
# vous devez développer une nouvelle approche spécifiquement pour le widget
# ttk.Treeview. Ce widget est l'équivalent le plus proche de wx.ListCtrl en
# mode "rapport" (report mode) et prend en charge l'affichage en colonnes.
#
# Mise en œuvre de l'ajustement automatique
#
#     Gérer l'événement de redimensionnement de la fenêtre : Dans Tkinter,
#     vous pouvez lier un événement <Configure> à la fenêtre ou au widget Treeview lui-même.
#     Cet événement est déclenché lorsque la taille de la fenêtre change.
#
#     Calculer l'espace disponible : À l'intérieur du gestionnaire d'événements,
#     récupérez la largeur totale du Treeview en utilisant widget.winfo_width().
#
#     Ajuster les largeurs de colonne : Vous pouvez itérer sur les colonnes du
#     Treeview (tree.column('#0', width=...), tree.column('col1', width=...), etc.)
#     et ajuster la largeur de la colonne que vous souhaitez redimensionner
#     pour qu'elle occupe l'espace restant.
#
# Vous pouvez utiliser une logique similaire à celle du mixin wxPython :
# calculer la largeur totale de toutes les colonnes à largeur fixe,
# puis soustraire ce total de la largeur disponible pour trouver la largeur
# de la colonne qui doit être redimensionnée automatiquement.
"""
# Ce qui a été ajouté :
#
#     Logs de niveau DEBUG : Pour les calculs mathématiques et les passages fréquents (comme on_resize).
#
#     Logs de niveau INFO : Pour les actions importantes comme le changement de colonne cible ou le lancement d'un redimensionnement complet.
#
#     Gestion d'erreur sur self._font : Si _font n'est pas encore initialisé dans la classe qui utilise le mixin, le code ne plantera pas et logguera un avertissement.
#
#     Utilisation de self.ResizeColumnMinWidth : J'ai remplacé la valeur en dur 50 par l'attribut de l'instance dans on_resize.

# 1. État réel de autowidthtk.py
# Réponse courte
#
# 👉 Non, autowidthtk.py n’est pas encore totalement sûr ni totalement fonctionnel
# 👉 Mais : la logique de base est bonne et exploitable
#
# Tu es clairement au bon niveau d’abstraction (un mixin dédié à l’auto-redimensionnement), et tu as déjà fait l’essentiel du travail intellectuel de portage wx → Tkinter.
#
# Ce qui est déjà BIEN fait ✅
#
# ✔️ Séparation claire du rôle :
# AutoColumnWidthMixin ne fait que gérer la largeur des colonnes
#
# ✔️ Utilisation correcte de :
# <Configure> pour détecter les redimensionnements
# winfo_width() pour connaître la largeur réelle
# self.column(col)['width'] pour les colonnes fixes
# ✔️ Gestion d’une largeur minimale (ResizeColumnMinWidth)
# ✔️ Logs utiles (DEBUG / INFO / WARNING)
# ✔️ Méthode _getRequiredColumnWidth() pertinente (header + contenu)
#
# 👉 Sur le plan algorithmique, tu es très proche de ce que faisait wxPython.
#
# 2. Problèmes concrets identifiés
# Je vais être précis, parce que certains points peuvent te faire perdre beaucoup de temps plus tard.
# Problème 1 – AutoColumnWidthMixin appelle super().__init__
# Pourquoi c’est dangereux
#
# Dans TaskCoach Tkinter, tu as adopté (à juste titre) cette règle :
#
# 👉 Les mixins abstraits ne doivent PAS initialiser le widget Tkinter
# Or ici :
#
# AutoColumnWidthMixin n’hérite pas de ttk.Treeview
# mais il appelle quand même super().__init__
# ce qui dépend dangereusement du MRO
#
# 👉 C’est exactement le type de bug silencieux qui crée :
# des AttributeError: object has no attribute tk
# ou des widgets partiellement initialisés
#
# Conclusion
# ⚠️ Ce mixin n’est PAS “non-coopératif”, contrairement aux autres mixins de itemctrltk.py.
#
# 🔴 Problème 2 – Hypothèse implicite : self est un Treeview
#
# Dans tout le fichier, tu utilises :
# Cela suppose implicitement que :
#
# AutoColumnWidthMixin est toujours mixé sur un ttk.Treeview déjà initialisé
# Mais ce n’est ni documenté clairement, ni garanti par le code.
#
# ➡️ Ce n’est pas faux conceptuellement, mais :
# il faut l’assumer explicitement
# et surtout ne jamais appeler __init__ du widget ici
#
# 🟠 Problème 3 – resize_column ambigu (index vs id)
# Problème
# Dans Tkinter :
#
# les colonnes sont identifiées par ID string ("task_name")
# PAS par index entier (sauf #0)
# 👉 Ici, resize_column peut être :
#
# un int
# ou une string
# ou un index hors liste
# ⚠️ C’est une source de bugs très probable
#
# 🟠 Problème 4 – _font n’est pas contractuellement défini
# Tu fais bien de protéger :
# Mais :
# le mixin dépend de _font
# sans le documenter clairement
# ni fournir d’alternative officielle (tk.font.Font(...))
# 👉 Aujourd’hui ça marche “par chance”, pas par contrat.

# 🟡 Problème 5 – <Configure> déclenché trop tôt
# Dans TaskCoach :
# beaucoup de widgets sont construits avant d’avoir leurs colonnes finales
# winfo_width() vaut souvent 1 au début
# Tu le gères partiellement, mais :
# le mixin ne sait pas quand il est “prêt”

# Intégration et Explications
#
# Voici comment ce fichier s'intègre dans votre architecture :
#     La Logique de Redimensionnement (_on_autowidth_resize) :
#         Contrairement à wxPython où l'on dit "AutoWidth", en Tkinter,
#         Treeview a besoin de savoir exactement quelle largeur donner à une colonne.
#
#         La méthode calcule : Largeur Totale - (Largeur des autres colonnes) = Largeur de la colonne cible.
#
#         Elle gère le cas particulier de la colonne #0 (l'arborescence)
#         qui est gérée séparément des colonnes de données dans Tkinter.
#
#     Liaison d'événement (<Configure>) :
#         C'est l'équivalent de EVT_SIZE ou EVT_WINDOW_RESIZE.
#         Chaque fois que l'utilisateur redimensionne la fenêtre principale,
#         cet événement est déclenché sur le Treeview, recalculant la largeur des colonnes.
#
#     Utilisation dans itemctrltk.py :
#         Dans votre fichier itemctrltk.py, vous avez :
#         Python
#
#     class _CtrlWithAutoResizedColumnsMixin(autowidthtk.AutoColumnWidthMixin):
#         # ...
#         def on_resize(self, event):
#              # ...
#
#     Action requise : Vous pouvez maintenant nettoyer itemctrltk.py.
#     La classe _CtrlWithAutoResizedColumnsMixin dans itemctrltk.py
#     peut soit être supprimée (si vous utilisez directement autowidthtk.AutoColumnWidthMixin),
#     soit simplifiée pour juste appeler setResizeColumn lors de l'initialisation.
#
#     Si vous gardez la méthode on_resize dans itemctrltk.py
#     (comme montré dans votre upload précédent),
#     assurez-vous qu'elle n'entre pas en conflit avec _on_autowidth_resize.
#     Le mieux est de supprimer la méthode on_resize locale de itemctrltk.py
#     et de laisser ce fichier autowidthtk.py gérer la logique.
#
# Définir la colonne à étirer :
#
#     Dans TaskTree (ou TaskList dans itemctrltk.py), après avoir créé les colonnes, vous devrez appeler :
#     Python
#
# self.setResizeColumn('task_name') # ou 'subject', l'ID de la colonne principale
#
# Cela garantira que la colonne "Sujet" prend tout l'espace disponible, comportement typique de TaskCoach.
import logging
import tkinter as tk
from tkinter import ttk

log = logging.getLogger(__name__)


# class AutoColumnWidthMixin(ttk.Treeview):
class AutoColumnWidthMixin:  # mixin !
    """
    Mixin pour redimensionner automatiquement une colonne dans un
    ttk.Treeview afin qu'elle utilise tout l'espace disponible.
    Ce mixin ajuste dynamiquement la largeur d'une colonne spécifiée
    pour éviter les barres de défilement horizontales tout en utilisant
    efficacement l'espace disponible.

    Ce mixin suppose :
        - un widget ttk.Treeview
        - déjà initialisé
        - avec self['columns'] défini
    Il ne crée aucun widget.
    Il ne doit pas appeler super().__init__.

    resize_column (string) : ID de colonne Tkinter à redimensionner automatiquement
                             (par défaut : la dernière colonne).
    ResizeColumnMinWidth (int) : Largeur minimale de la colonne redimensionnable
                                 (par défaut : 50).
    """
    # def __init__(self, master, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        """Initialise le mixin avec des paramètres spécifiques.

        Args :
            master : Le widget parent (généralement un ttk.Treeview).
            *args, **kwargs : Arguments supplémentaires pour le constructeur
                              du widget parent.
        Kwargs spécifiques :
        resizeableColumn (int) : Index de la colonne à redimensionner
                                 automatiquement (par défaut : -1).
        resizeableColumnMinWidth (int) : Largeur minimale de la colonne
                                         redimensionnable (par défaut : 50).

        """
        log.debug("Initialisation de AutoColumnWidthMixin.")
        # On ne propage pas args/kwargs ici car c'est un mixin utilitaire
        # et on suppose que la classe parent gère l'init Tkinter.
        # Cependant, pour être sûr dans un MRO complexe :
        # super().__init__(master, *args, **kwargs)
        # Extraction des paramètres spécifiques avant de passer le reste au parent
        # resize_column = ID de colonne Tkinter (string)
        # self.resize_column = kwargs.pop("resizeableColumn", len(kwargs.get('columns', [])))  # Par défaut, la dernière colonne
        self._resize_column_id = kwargs.pop("resizeableColumn", str(len(kwargs.get('columns', []))-1))  # Par défaut, la dernière colonne !!! Attention à ne pas oublier le -1.
        #
        self.ResizeColumnMinWidth = kwargs.pop("resizeableColumnMinWidth", 50)
        # self._min_column_width = kwargs.pop("resizeableColumnMinWidth", 50)
        # log.debug(f"Attributs initialisés : resize_column={self.resize_column}, "
        #           f"ResizeColumnMinWidth={self.ResizeColumnMinWidth}")
        log.debug(f"AutoColumnWidthMixin : Attributs initialisés : La dernière colonne à redimensionner est _resize_column_id={self._resize_column_id}, "
                  f"ResizeColumnMinWidth={self.ResizeColumnMinWidth}")
        # self.set_columns()
        # On appelle le constructeur suivant dans le MRO (Method Resolution Order)
        # super().__init__(master, *args, **kwargs)  # Pourquoi c’est dangereux
        # Dans TaskCoach Tkinter, tu as adopté (à juste titre) cette règle :
        # 👉 Les mixins abstraits ne doivent PAS initialiser le widget Tkinter
        # Recommandation 1 – Rendre le mixin non-coopératif
        # C’est la plus importante.
        # 👉 AutoColumnWidthMixin ne doit PAS appeler super().__init__
        # Il doit :
        # uniquement initialiser ses attributs
        # et être activé explicitement par la classe concrète (TaskList, TreeListCtrl, etc.)
        # 📌 Conceptuellement :
        # Ce mixin configure un Treeview existant, il ne le crée pas.

        # self.resize_column = 'task_name'
        self.__is_auto_resizing = False
        # Liaison de l'événement de redimensionnement de la fenêtre/widget
        # self.bind('<Configure>', self.on_resize)  # pour détecter les redimensionnements
        self.bind('<Configure>', self._on_autowidth_resize)  # pour détecter les redimensionnements
        # TODO : peut-être trop tôt puisque c'est appelé dans itemctrltk._CtrlWithAutoResizedColumnsMixin
        # Au lieu de cela, envisager d'appeler resizeColumns() explicitement après la configuration des colonnes
        #

    def SetResizeColumn(self, column_id):
        """
        Définit la colonne à redimensionner automatiquement.

        Args :
            column (int) : Index de la colonne.
        """
        # log.info(f"Changement de la colonne à redimensionner : {self.resize_column} -> {column}")
        log.info(f"AutoColumnWidthMixin.SetResizeColumn : Changement de la colonne à redimensionner : {self._resize_column_id} -> {column_id}")
        # self.resize_column = column
        self._resize_column_id = column_id
        # Forcer une mise à jour immédiate
        self.update_idletasks()
        self._on_autowidth_resize(None)
        # # Forcer un premier calcul
        # self.after(100, lambda: self.on_resize(None))

    def getResizeColumn(self):
        """Retourne l'ID de la colonne à redimensionner."""
        # return self.resize_column
        return self._resize_column_id

    # def set_columns(self):
    #     # Configurez vos colonnes ici
    #     self['columns'] = ('task_name', 'due_date', 'priority')
    #     self.column('#0', width=0, stretch=tk.NO)  # Colonne fantôme
    #     self.heading('task_name', text='Tâche')
    #     self.heading('due_date', text='Date d’échéance')
    #     self.heading('priority', text='Priorité')
    #
    #     # Définir des largeurs initiales ou minimales
    #     self.column('due_date', minwidth=100, width=150)
    #     self.column('priority', minwidth=50, width=75)
    #
    #     # Insérer des données de test
    #     self.insert('', 'end', values=('Convertir le fichier', '2025-09-01', 'Haute'))
    #     self.insert('', 'end', values=('Écrire la documentation', '2025-09-15', 'Moyenne'))

    def _getRequiredColumnWidth(self, col):
        log.debug(f"AutoColumnWidthMixin._getRequiredColumnWidth : Calcul de la largeur requise pour la colonne : {col}")
        # Mesurer la largeur du texte de l'en-tête (Header)
        header_text = self.heading(col, 'text')
        # Note : self._font doit être défini dans la classe parente ou l'instance
        # Si _font n’est pas défini, une estimation approximative est utilisée.
        try:
            header_width = self._font.measure(header_text) + 20  # + marge pour la flèche de tri
        except AttributeError:
            log.warning("AutoColumnWidthMixin._getRequiredColumnWidth : Attribut '_font' non trouvé, utilisation d'une mesure par défaut.")
            header_width = len(header_text) * 10 + 20

        # Mesurer le contenu (si présent)
        content_width = 0
        for item in self.get_children():
            cell_text = str(self.set(item, col))
            # Problème 4 – _font n’est pas contractuellement défini
            try:
                # Si _font n’est pas défini, une estimation approximative est utilisée.
                width = self._font.measure(cell_text)
            except AttributeError:
                width = len(cell_text) * 8
            # content_width = max(content_width, self._font.measure(cell_text))
            content_width = max(content_width, width)

        # return max(header_width, content_width + 10)
        required = max(header_width, content_width + 10)
        log.debug(f"AutoColumnWidthMixin._getRequiredColumnWidth : Largeur calculée pour la colonne '{col}': Header={header_width}, Contenu={content_width} -> Requis={required}")
        return required

    def resizeColumns(self):
        """

        Returns:

        """
        log.info("AutoColumnWidthMixin : Lancement de resizeColumns (calcul global)")
        self.update_idletasks()  # Force Tkinter à calculer les dimensions réelles
        # On récupère les colonnes de données uniquement
        columns = self['columns']
        if not columns:
            log.warning("Aucune colonne à redimensionner.")
            return

        total_width = self.winfo_width()
        log.debug(f"Largeur actuelle du widget : {total_width}px")
        # # Si le widget n'est pas encore affiché, winfo_width() renvoie 1
        # if total_width <= 1:
        #     self.update_idletasks()
        #     total_width = self.winfo_width()

        for col_id in columns:
            # Forcer une largeur minimale si le contenu est vide
            required_width = self._getRequiredColumnWidth(col_id)
            final_width = max(required_width, 50)  # Sécurité : 50px min
            log.debug(f"AutoColumnWidthMixin.resizeColumns : Application largeur : {col_id} -> {final_width}px")
            self.column(col_id, width=final_width)

    # # # Ancienne méthode on_resize (commentée) remplacée par _on_autowidth_resize
    # def on_resize(self, event=None):
    #     """Ajuste la largeur de la colonne spécifiée en fonction de l'espace disponible."""
    #     if not self._resize_column_id:
    #         return
    #     # On récupère la largeur actuelle du widget
    #     current_width = self.winfo_width()  # pour connaître la largeur réelle
    #     # Sécurité : si le widget n'est pas encore rendu (largeur <= 1)
    #     if current_width <= 1:
    #         return
    #     # if self.winfo_width() > 1:  # Assurez-vous que le widget est visible
    #     if current_width > 1:
    #         # total_width = self.winfo_width()
    #         # Calcul des colonnes fixes
    #         fixed_width = 0
    #         columns = self['columns']
    #
    #         # On récupère toutes les colonnes affichées (y compris #0 si visible)
    #         display_columns = self["displaycolumns"]
    #         if display_columns == "#all":
    #             display_columns = self.cget("columns")
    #
    #         # Calculer la largeur totale des colonnes à largeur fixe
    #         # Calcul de la somme des largeurs des colonnes non-extensibles
    #         # for col in self['columns']:
    #         for col in columns:
    #             # for col in display_columns:
    #             # if col != self.resize_column:
    #             if col != self._resize_column_id:
    #                 fixed_width += self.column(col)['width']  # pour les colonnes fixes
    #                 # fixed_width += self.column(col, 'width')
    #
    #         # Gestion de la colonne #0 (l'arbre) si ce n'est pas elle qu'on redimensionne
    #         if self._resize_column_id != "#0":
    #             fixed_width += self.column("#0", 'width')
    #
    #         # Définir la largeur de la colonne redimensionnable
    #         # resize_width = total_width - fixed_width
    #         resize_width = current_width - fixed_width
    #
    #         log.debug(f"AutoColumnWidthMixin.on_resize : Événement Resize : Total={current_width}px, Fixe={fixed_width}px, Restant={resize_width}px")
    #
    #         # Calcul de la nouvelle largeur (marge de 4px pour éviter le scroll horizontal)
    #         # On utilise getattr par sécurité pour éviter l'AttributeError que vous avez eu
    #         min_width = getattr(self, 'ResizeColumnMinWidth', 50)
    #         new_width = max(min_width, current_width - fixed_width - 4)
    #
    #         # Assurez-vous que la largeur est positive et supérieure à un minimum
    #         # if resize_width > 50:
    #         if resize_width > self.ResizeColumnMinWidth:
    #             log.debug(f"Ajustement de la colonne '{self._resize_column_id}' à {resize_width}px")
    #             self.column(self._resize_column_id, width=resize_width)
    #         else:
    #             log.warning(f"AutoColumnWidthMixin.on_resize : Espace insuffisant pour '{self._resize_column_id}' ({resize_width}px < {self.ResizeColumnMinWidth}px)")
    #
    #         # try:
    #         #     self.column(self._resize_column_id, width=int(new_width))
    #         # except Exception as e:
    #         #     # Éviter de crasher si la colonne n'existe plus pendant le redimensionnement
    #         #     pass

    def _on_autowidth_resize(self, event=None):
        """
        Appelé lorsque la taille du widget change.
        Calcule l'espace restant et l'attribue à la colonne redimensionnable.
        """
        # Si aucun événement n'est passé, on utilise self (appel manuel)
        if event is None:
            widget_width = self.winfo_width()
        else:
            # Vérifier que l'événement vient bien du Treeview lui-même
            if event.widget != self:
                return
            widget_width = event.width

        # Sécurité : si le widget n'est pas encore visible ou trop petit
        if widget_width <= 1:
            return

        # Si aucune colonne spécifique n'est définie, on ne fait rien
        # (Ou on pourrait par défaut prendre la dernière, mais c'est risqué)
        if not self._resize_column_id:
            return

        # Liste de toutes les colonnes visibles
        # Note: '#0' est la colonne de l'arbre. 'displaycolumns' contient les autres.
        # Si displaycolumns est '#all', il faut récupérer 'columns'.

        display_cols = self["displaycolumns"]
        log.debug(f"AutoColumnWidthMixin._on_autowidth_resize : Les colonnes visibles à redimensionner sont {display_cols}.")
        if display_cols == "#all":
            display_cols = self["columns"]

        # Calculer la largeur occupée par toutes les AUTRES colonnes
        used_width = 0

        # Vérifier si la colonne #0 (l'arbre) est visible
        # show peut être 'tree', 'headings', 'tree headings' ou ''
        show_option = self["show"]
        tree_col_visible = "tree" in str(show_option)

        # Si la colonne à redimensionner est l'arbre lui-même (#0)
        if self._resize_column_id == "#0":
            if not tree_col_visible:
                return  # On ne peut pas redimensionner une colonne invisible

        # Inutile puisqu'intégré dans display_cols ?
        # # Itérer sur la colonne #0 si visible
        # if tree_col_visible and self._resize_column_id != "#0":
        #     try:
        #         # used_width += self.column("#0", "width")  # TypeError: TreeListCtrl.column() takes 2 positional arguments but 3 were given
        #         used_width += self.column("#0", option="width")
        #         # used_width += self.column("#0")["width"]  # fonctionne aussi
        #     except tk.TclError:
        #         pass

        # Itérer sur les autres colonnes
        log.debug(f"AutoColumnWidthMixin._on_autowidth_resize : Calcul de la largeur utilisée par les autres colonnes de {display_cols}.")
        for col_id in display_cols:
            log.debug(f"AutoColumnWidthMixin._on_autowidth_resize : Traitement de la colonne {col_id}.")
            if col_id != self._resize_column_id:
                try:
                    used_width += self.column(col_id, option="width")
                    # used_width += self.column(col_id)["width"]  # fonctionne aussi
                    log.debug(f"AutoColumnWidthMixin._on_autowidth_resize : Largeur de la colonne {col_id} = {self.column(col_id, option='width')}px.")
                except tk.TclError:
                    log.error(f"AutoColumnWidthMixin._on_autowidth_resize : Impossible de récupérer la largeur de la colonne {col_id}.", stack_info=True)
                    pass

        # Calculer l'espace restant
        # Note : On retire quelques pixels pour la bordure/scroller (ajustement heuristique)
        # 4 pixels est souvent une marge de sécurité pour éviter la barre de scroll horizontale
        available_width = widget_width - used_width - 4

        # Appliquer la nouvelle largeur avec un minimum de sécurité
        if available_width < self.ResizeColumnMinWidth:
            available_width = self.ResizeColumnMinWidth

        try:
            # On met à jour la largeur de la colonne cible
            self.column(self._resize_column_id, width=int(available_width))
        except tk.TclError as e:
            log.warning(f"AutoColumnWidthMixin._on_autowidth_resize : Impossible de redimensionner la colonne {self._resize_column_id}", stack_info=True)


# Pour la compatibilité avec le code existant qui pourrait importer TaskList d'ici
# (Bien que TaskList soit plutôt définie dans itemctrltk.py ou domain)
# Nous fournissons une classe factice ou de base si nécessaire.
# Elle est très utile pour les tests
# 👉 Mais elle ne doit jamais être utilisée en production
#
# TODO : Je te conseille :
# soit de la déplacer dans un fichier de test
# soit de la marquer explicitement comme helper / debug

# class AutoWidthTreeList(AutoColumnWidthMixin, ttk.Treeview):
#     """
#     Une classe combinée prête à l'emploi pour les tests.
#     """
#     def __init__(self, master, **kwargs):
#         # Initialiser Treeview d'abord pour avoir accès à self.bind
#         ttk.Treeview.__init__(self, master, **kwargs)
#         # Initialiser le mixin ensuite
#         AutoColumnWidthMixin.__init__(self)


# if __name__ == '__main__':
#     from taskcoachlib.domain.task.tasklist import TaskList
#     root = tk.Tk()
#     root.title("TaskCoach avec Tkinter")
#     root.geometry("600x400")
#
#     task_list = TaskList(root, show='headings')
#     task_list.pack(fill=tk.BOTH, expand=True)  # TaskList n'est pas encore un widget ! pour être packé !
#
#     root.mainloop()
