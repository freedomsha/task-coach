# hcalendar.py pour Tkinter, converti de wxPython
"""
Task Coach - Your friendly task manager
Copyright (C) 2014 Task Coach developers <developers@taskcoach.org>

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
# Ce fichier s'appuie fortement sur les classes de wxevents.py,
# donc la conversion de hcalendar.py doit prendre en compte les changements apportés à wxevents.py.
#
# Le code wxPython utilise des événements personnalisés, un mixin pour les info-bulles
# et un mécanisme de glisser-déposer qui n'a pas d'équivalent direct dans Tkinter.
# J'ai donc adapté la classe pour qu'elle utilise les événements et les méthodes de gestion de Tkinter.
#
# Voici la version convertie, en supposant que le wxevents.py que vous avez fourni
# soit maintenant tkevents.py.

# J'ai converti le code de hcalendar.py pour qu'il soit compatible avec Tkinter.
# Les principales adaptations sont :
#
#     Héritage : La classe HierarchicalCalendar hérite de CalendarCanvas de votre version Tkinter,
#     que j'ai renommée tkevents.py pour éviter toute confusion.
#
#     Gestion des événements : Les événements wx.EVT_... ont été remplacés par
#     des liaisons Tkinter (<Double-Button-1>, <Button-3>).
#
#     Fonctionnalités non-Tkinter : Les fonctionnalités de ToolTipMixin et de
#     glisser-déposer (draganddrop.DropTarget) ont été commentées ou remplacées
#     par des implémentations de base, car Tkinter n'offre pas ces fonctionnalités
#     de manière native et elles nécessitent une logique plus complexe pour être reproduites.
#
#     Logique de date : La logique de SetCalendarFormat a été adaptée pour
#     utiliser les objets datetime de Python directement,
#     car les classes date et command de l'implémentation originale ne sont pas disponibles ici.
#
# Le code inclut également une petite section if __name__ == "__main__":
# pour vous permettre de tester le widget directement.

# L'aspect me plaît mais il manque des fonctions

# TODO : A refaire en prenant en compte draganddrop et tooltip quand ils seront prêt !

# D'accord, je vais vous aider à compléter la conversion de hcalendartk.py en
# tenant compte des dépendances que vous avez fournies (draganddroptk.py, tooltiptk.py, et tkevents.py).
# Voici une liste des points à adresser pour rendre hcalendartk.py fonctionnel :
#
# Intégration du Drag and Drop :
#
#
# La classe HierarchicalCalendar utilisait draganddrop.DropTarget dans hcalendar.py.
# Il faut adapter cela en utilisant draganddroptk.FileUrlDropTarget ou une approche similaire.
# Assurez-vous que les callbacks OnDropURL, OnDropFiles et OnDropMail sont
# correctement gérés et que les données sont traitées en conséquence.
#
#
# Gestion des Tooltips :
#
#
# hcalendar.py utilisait un ToolTipMixin.  Il faut s'assurer que la classe tooltip.ToolTip
# est correctement initialisée et utilisée dans HierarchicalCalendar.
# Implémentez la logique pour afficher les tooltips en utilisant les événements
# <Enter> et <Leave> et en affichant une fenêtre Toplevel avec le texte approprié.
#
#
# Adaptation des méthodes de calendrier :
#
#
# Les méthodes comme SetCalendarFormat, Next, Prev et Today doivent être adaptées
# pour fonctionner avec les objets datetime de Python.
# Assurez-vous que les dates de début et de fin du calendrier sont correctement
# mises à jour et que l'affichage est rafraîchi en conséquence.
#
#
# Implémentation de HitTest :
#
#
# La méthode HitTest est essentielle pour déterminer si un clic de souris
# se trouve sur un événement. Implémentez cette méthode dans HierarchicalCalendar
# ou assurez-vous qu'elle est accessible depuis la classe de base CalendarCanvas.
#
#
# Gestion de la sélection :
#
#
# Adaptez les méthodes curselection, clear_selection, select et select_all pour
# gérer correctement la sélection des événements dans le calendrier.
#
#
# Redéfinition des méthodes abstraites :
#
#
# Assurez-vous que les méthodes abstraites héritées de CalendarCanvas
# (devenu tkevents.py) sont correctement implémentées dans HierarchicalCalendar.
# Cela inclut GetRootEvents, GetChildren, GetStart, GetEnd, GetText, GetBackgroundColor,
# GetForegroundColor, GetProgress et GetIcons.
#
#
# Événements :
#
#
# Remplacez les événements wx.EVT_... par les liaisons Tkinter équivalentes.
#
# Voici une version modifiée de hcalendartk.py avec les adaptations nécessaires.
# Notez que certaines parties nécessiteront une implémentation plus détaillée
# en fonction de la structure de données de votre application TaskCoach.

# Points importants à retenir:
#
# Structure de données: L’implémentation des méthodes telles que
# GetRootEvents(), GetChildren(), GetStart(), GetEnd(), GetText(),
# GetBackgroundColor(), GetForegroundColor(), GetProgress() et GetIcons()
# dépend fortement de la façon dont les données des tâches sont stockées et
# gérées dans votre application TaskCoach.
# Vous devrez adapter ces méthodes pour qu’elles correspondent à votre structure de données.
#
# HitTest: La méthode HitTest() est essentielle pour
# déterminer si un événement a été cliqué.
# Vous devrez implémenter une logique précise pour calculer les coordonnées
# des événements dans le calendrier et vérifier si les coordonnées de la souris
# se trouvent dans ces limites.
#
# Tooltips: J’ai inclus une implémentation de base des tooltips à titre d’exemple.
# Vous pouvez personnaliser l’apparence et le comportement des tooltips en
# modifiant le code correspondant.
#
# Drag and Drop: Le drag and drop est initialisé mais les méthodes OnDropURL()
# et OnDropFiles() sont des stubs.

# J'ai bien compris que tkevents.py contient maintenant la classe CalendarCanvas et que tooltiptk.py et draganddroptk.py sont prêts à être intégrés.
# Voici les étapes à suivre pour compléter la conversion :
#
# Intégration de draganddroptk.py :
#
# Remplacer l'ancien système de DropTarget commenté par la nouvelle classe FileUrlDropTarget de draganddroptk.py .
# S'assurer que les callbacks OnDropURL, OnDropFiles et OnDropMail sont correctement connectés et que les données sont traitées correctement.
#
#
# Intégration de tooltiptk.py :
#
# Utiliser la classe ToolTip de tooltiptk.py  pour afficher des info-bulles lorsque la souris survole un événement.
# Implémenter la logique pour afficher les tooltips en utilisant les événements <Enter> et <Leave> et en affichant une fenêtre Toplevel avec le texte approprié.
#
#
# Implémentation de HitTest dans tkevents.py:
#
# Implémenter correctement la méthode HitTest dans CalendarCanvas (dans tkevents.py ) pour déterminer si un clic de souris se trouve sur un événement. Cette méthode est cruciale pour la sélection et l'édition des événements.
#
#
# Adaptation des méthodes de calendrier :
#
# Les méthodes comme SetCalendarFormat, Next, Prev et Today doivent fonctionner avec les objets datetime de Python et les classes Date et DateTime définies dans dateandtime.py .
#
#
# Redéfinition des méthodes abstraites :
#
# S'assurer que les méthodes abstraites héritées de CalendarCanvas sont correctement implémentées dans HierarchicalCalendar. Cela inclut GetRootEvents, GetChildren, GetStart, GetEnd, GetText, GetBackgroundColor, GetForegroundColor, GetProgress et GetIcons. Ces méthodes doivent utiliser les classes et fonctions définies dans date.py , dateandtime.py , render.py  et timedelta.py .

# Les modifications apportées sont les suivantes :
#
# Drag and Drop :
#
# La classe FileUrlDropTarget est maintenant appliquée au main_canvas et les callbacks OnDropURL et OnDropFiles sont utilisés. Les event wxPython sont à None.
#
#
# Tooltips :
#
# J'ai conservé la base pour les tooltips.  Il faut que tu définisses self.tooltip_text quand tu le souhaites.
#
#
# dateandtime.py et render.py :
#
# J'ai modifié _OnLeftDClick et SetCalendarFormat pour utiliser les objets DateTime et les méthodes de calcul de date de dateandtime.py .
# J'ai aussi ajouté FormatDateTime pour utiliser render.dateFunc .
#
#
# Commentaires :
#
# J'ai laissé des commentaires TODO pour les parties qui nécessitent une implémentation spécifique à votre application.
#
#
#
# N'hésitez pas à me poser d'autres questions.
# J'ai tenté de rechercher des informations sur les fonctions  OnDropMail, _OnBeforeShowToolTip, getItemTooltipData dans les fichiers que vous avez fournis, mais cela n'a retourné aucun résultat pertinent.

# Pour déterminer si le fichier hcalendartk.py s'intègre bien avec le reste du projet, il faut vérifier plusieurs aspects :
#
# Compatibilité des imports:
#
#
# Assurez-vous que les modules importés dans hcalendartk.py existent et sont compatibles avec Tkinter. Vérifiez que les chemins d'importation sont corrects.
# Dans le hcalendartk.py fourni , on remarque l'import de taskcoachlib.domain.date as dateandtime au lieu de from taskcoachlib.domain import dateandtime. Il faut uniformiser.
# Il y a un import de taskCommands dans le hcalendartk.py fourni . Il faut vérifier que le chemin est correct (from taskcoachlib.command import taskCommands).
#
#
# Héritage et surcharge des méthodes:
#
#
# HierarchicalCalendar hérite de CalendarCanvas et tooltip.ToolTip .  Assurez-vous que les méthodes abstraites de CalendarCanvas sont correctement implémentées dans HierarchicalCalendar et que les méthodes de tooltip.ToolTip sont utilisées correctement.
# Vérifiez que les méthodes surchargées ont la même signature que les méthodes de la classe de base.
#
#
# Gestion des dates et heures:
#
#
# Le code utilise les classes date et datetime du module taskcoachlib.domain . Assurez-vous que ces classes sont utilisées de manière cohérente dans tout le code.
# Vérifiez que les conversions entre les objets datetime de Python et les objets date de TaskCoach sont effectuées correctement.
#
#
# Gestion des événements:
#
#
# Le code utilise les événements Tkinter (<Button-1>, <Double-Button-1>, <Button-3>) . Assurez-vous que ces événements sont correctement liés et que les gestionnaires d'événements sont implémentés correctement.
# Le code utilise des événements virtuels (<<SelectionChanged>>, <<DatesChanges>>) . Assurez-vous que ces événements sont correctement générés et liés.
#
#
# Drag and Drop:
#
#
# Le code utilise la classe FileUrlDropTarget pour gérer le drag and drop . Assurez-vous que cette classe est utilisée correctement et que les callbacks OnDropURL et OnDropFiles sont implémentés correctement.
#
#
# Tooltips:
#
#
# Le code utilise la classe tooltiptk.ToolTip pour afficher les tooltips . Assurez-vous que cette classe est utilisée correctement et que les tooltips sont affichés correctement.
#
#
# Structure de données:
#
#
# Le code dépend d'une structure de données pour les tâches et les événements. Assurez-vous que cette structure de données est cohérente avec le reste du code et que les méthodes GetRootEvents, GetChildren, GetStart, GetEnd, GetText, GetBackgroundColor, GetForegroundColor, GetProgress et GetIcons sont implémentées correctement en fonction de cette structure de données.
#
#
# Compatibilité avec les commandes:
#
#
# Le code utilise les commandes définies dans le module taskcoachlib.command . Assurez-vous que ces commandes sont utilisées correctement et que les événements appropriés sont déclenchés.
#
#
# Vérification de la logique:
#
#
# Vérifiez que la logique du code est correcte et que le calendrier affiche correctement les tâches et les événements.
# Vérifiez que les sélections, les modifications et les créations d'événements fonctionnent correctement.
# Vérifiez que le drag and drop et les tooltips fonctionnent correctement.
#
# En résumé, pour intégrer correctement le fichier hcalendartk.py au reste du projet, vous devrez :
#
# Vérifier et corriger les imports.
# Implémenter les méthodes abstraites de CalendarCanvas.
# Implémenter les callbacks pour le drag and drop et les tooltips.
# Adapter la logique de gestion des dates et heures.
# Adapter la structure de données.
# Vérifier que les commandes sont utilisées correctement.
#
# J'ai tenté de vérifier la présence des fonctions getRootItems, getItemText, plannedStartDateTime, dueDateTime, backgroundColor, foregroundColor, percentageComplete, get_domain_children, add_command, et add_command dans les fichiers que vous avez fournis, mais cela n'a retourné aucun résultat pertinent.

# Voici une analyse de la façon dont hcalendartk.py s'intègre au reste du projet, ainsi que des corrections et améliorations potentielles :
# Points positifs de l'intégration :
#
# Gestion des dates et heures : Le code a été modifié pour utiliser les objets DateTime et les méthodes de calcul de date de dateandtime.py , , ce qui est essentiel pour l'intégration.
# Drag and Drop : La classe FileUrlDropTarget est maintenant appliquée au main_canvas ,  et les callbacks OnDropURL et OnDropFiles sont utilisés.
# Tooltips : La structure de base des tooltips est en place, avec les événements <Enter> et <Leave> .
# Événements Tkinter : Les événements Tkinter sont utilisés au lieu des événements wxPython .
#
# Problèmes et améliorations potentielles:
#
# Incohérence des imports : Dans hcalendartk.py, on remarque l'import de taskcoachlib.domain.date as dateandtime au lieu de from taskcoachlib.domain import dateandtime. Il faut uniformiser avec from taskcoachlib.domain import dateandtime.
# Méthode HitTest : La méthode HitTest est essentielle pour déterminer si un événement a été cliqué , . Elle doit être implémentée dans CalendarCanvas  (dans tkevents.py) et renvoyer un objet avec les informations appropriées.
# La gestion de la sélection: Adapter les méthodes curselection, clear_selection, select et select_all pour gérer correctement la sélection des événements dans le calendrier.
# Implémentation de OnDropMail : La fonction OnDropMail est un stub .
# getItemTooltipData : La fonction getItemTooltipData est définie par self.getItemTooltipData = parent.getItemTooltipData dans le __init__ de hcalendartk.py. Par contre, cette fonction n'existe pas dans les fichiers fournis.
# __tip : La variable self.__tip est instancié mais n'est pas utilisé dans la fonction OnBeforeShowToolTip .
# Fonction on_selection_changed : La fonction on_selection_changed est défini comme une fonction local dans if __name__ == "__main__": . Il faut revoir l'implémentation.
#
# Recommandations :
#
# Implémentation de HitTest dans tkevents.py : La méthode HitTest est essentielle pour déterminer si un événement a été cliqué. Elle doit être implémentée avec une logique précise pour calculer les coordonnées des événements dans le calendrier et vérifier si les coordonnées de la souris se trouvent dans ces limites .
# Vérification de la structure de données: L’implémentation des méthodes telles que GetRootEvents(), GetChildren(), GetStart(), GetEnd(), GetText(), GetBackgroundColor(), GetForegroundColor(), GetProgress() et GetIcons() dépend fortement de la façon dont les données des tâches sont stockées et gérées dans votre application TaskCoach. Vous devrez adapter ces méthodes pour qu’elles correspondent à votre structure de données .
# Vérification de l'implémentation du Drag and Drop : S'assurer que les callbacks OnDropURL, OnDropFiles et OnDropMail sont correctement connectés et que les données sont traitées correctement.
# Vérification de l'implémentation des Tooltips: J’ai inclus une implémentation de base des tooltips à titre d’exemple. Vous pouvez personnaliser l’apparence et le comportement des tooltips en modifiant le code correspondant.
import tkinter as tk
from tkinter import ttk
import datetime
import math
from taskcoachlib.widgetstk import tkevents
from taskcoachlib.widgetstk.tkevents import CalendarCanvas
from taskcoachlib.widgetstk import draganddroptk
from taskcoachlib.widgetstk import tooltiptk
from taskcoachlib.domain.date import dateandtime
from taskcoachlib.command import taskCommands


class HierarchicalCalendar(CalendarCanvas, tooltiptk.ToolTip):
    """
    Un calendrier hiérarchique pour afficher les tâches et les événements,
    adapté pour Tkinter.
    """
    # Formats d'en-tête (bitmask)
    HDR_WEEKNUMBER = 1
    HDR_DATE = 2

    # Formats de calendrier
    CAL_WEEKLY = 0
    CAL_WORKWEEKLY = 1
    CAL_MONTHLY = 2

    def __init__(
            self, parent, tasks, onSelect, onEdit, onCreate, popupMenu, **kwargs
    ):
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)
        self.__taskList = tasks
        self.__onSelect = onSelect
        self.__onEdit = onEdit
        self.__onCreate = onCreate
        self.__popupMenu = popupMenu
        self.__calFormat = self.CAL_WEEKLY
        self.__hdrFormat = self.HDR_DATE
        self.__drawNow = True
        self.__adapter = parent

        self.getItemTooltipData = parent.getItemTooltipData
        super().__init__(parent, **kwargs)
        self.SetCalendarFormat(self.__calFormat)

        self.__tip = tooltiptk.ToolTip(self)
        # self.__dropTarget = draganddrop.DropTarget(self.OnDropURL, self.OnDropFiles, self.OnDropMail)
        # self.SetDropTarget(self.__dropTarget)
        # Le glisser-déposer doit être géré manuellement.
        # Tkinter ne prend pas en charge les DropTargets de la même manière que wxPython.
        # Il faudrait implémenter des événements de glisser-déposer personnalisés si nécessaire.
        # Drag and Drop
        # self.__drop_target = draganddroptk.FileUrlDropTarget(
        #     self,
        #     on_drop_url_callback=self.OnDropURL,
        #     on_drop_file_callback=self.OnDropFiles,
        # )
        self.__drop_target = draganddroptk.FileUrlDropTarget(
            self.main_canvas,  # On applique le drop target au canvas principal
            on_drop_url_callback=self.OnDropURL,
            on_drop_file_callback=self.OnDropFiles,
        )

        # Le système d'événements de Tkinter est différent.
        # On utilise les liaisons directes du canevas.
        # self.bind("<Button-1>", self._OnLeftDown)  # Géré dans CalendarCanvas, mais peut être override
        # self.bind("<Double-Button-1>", self._OnLeftDClick)
        # self.bind("<Button-3>", self._OnRightUp)  # Clic droit pour le menu contextuel
        self.main_canvas.bind("<Button-1>", self._OnLeftDown)  # Géré dans CalendarCanvas
        self.main_canvas.bind("<Double-Button-1>", self._OnLeftDClick)
        self.main_canvas.bind("<Button-3>", self._OnRightUp)  # Clic droit pour le menu contextuel

        # Tooltip
        self.tooltip_text = ""  # Initialiser tooltip_text
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

        # Liaison de l'événement virtuel
        # self.my_widget.bind("<<SelectionChanged>>", self.on_selection_changed)
        self.bind("<<SelectionChanged>>", self._OnSelectionChanged)

        # Essai pour un autre événement
        self.bind("<<DatesChanges>>", self._OnDatesChanged)

    def _OnSelectionChanged(self, event):
        self.__onSelect()

    def _OnDatesChanged(self, event):
        if event.start is None or event.end is None:
            return
        task = event.event
        start = dateandtime.DateTime.fromDateTime(event.start)
        end = dateandtime.DateTime.fromDateTime(event.end)

        if task.plannedStartDateTime() != start:
            taskCommands.EditPlannedStartDateTimeCommand(items=[task],
                                                         newValue=start).do()
        if task.dueDateTime() != end:
            taskCommands.EditDueDateTimeCommand(items=[task],
                                                newValue=end).do()

    def _OnLeftDClick(self, event):
        """
        Gère le double-clic gauche pour modifier ou créer un événement.
        """
        hit = self.HitTest(event.x, event.y)
        # La logique de HitTest doit être implémentée dans la classe parente
        # ou passée via un paramètre.
        # Simplification pour l'exemple :
        # hit = type('obj', (object,), {'event': None, 'dateTime': datetime.datetime.now()})()

        # if hit.event is None:
        if hit and hit.event is None:
            if self.__onCreate:
                # self.__onCreate(hit.dateTime)
                self.__onCreate(dateandtime.DateTime.fromDateTime(hit.dateTime))  # Utiliser la classe DateTime de TaskCoach
        # else:
        elif hit and hit.event:
            if self.__onEdit:
                self.__onEdit(hit.event)

    def _OnRightUp(self, event):
        """
        Affiche le menu contextuel lors d'un clic droit.
        """
        if self.__popupMenu:
            self.__popupMenu.post(event.x_root, event.y_root)

    # Tooltip methods
    def on_enter(self, event):
        """Gère l'entrée de la souris dans le widget."""
        x, y = event.x, event.y
        hit = self.HitTest(x, y)
        if hit and hit.event:
            self.tooltip_text = self.GetText(hit.event)
            if self.tooltip_text:
                self.show_tooltip()

    def on_leave(self, event):
        """Gère la sortie de la souris du widget."""
        self.hide_tooltip()
        self.tooltip_text = ""

    def show_tooltip(self):
        """Affiche l'infobulle."""
        if self.tooltip_text:
            self.update_idletasks()
            # x = self.winfo_rootx() + self.mouse_x + 10
            x = self.winfo_rootx() + self.winfo_pointerx() + 10
            # y = self.winfo_rooty() + self.mouse_y + 10
            y = self.winfo_rooty() + self.winfo_pointery() + 10
            self.geometry(f"+{x}+{y}")
            self.deiconify()

    def hide_tooltip(self):
        """Masque l'infobulle."""
        self.withdraw()

    def OnBeforeShowToolTip(self, x, y):
        """
        Gère l'affichage des info-bulles.
        """
        # L'implémentation des info-bulles est différente dans Tkinter.
        # Cela nécessiterait une classe ToolTip personnalisée.
        # Pour l'instant, c'est une fonctionnalité désactivée.
        # return None  # À implémenter si nécessaire
        hit = self.HitTest(x, y)
        if hit is None or hit.event is None:
            return None

        tooltipData = self.getItemTooltipData(hit.event)  # Méthode venant de guitk.viewer.task.BaseTaskTreeViewer.
        doShow = any(data[1] for data in tooltipData)
        if doShow:
            self.__tip.SetData(tooltipData)
            return self.__tip
        else:
            return None

    def GetMainWindow(self):
        return self

    def GetItemCount(self):
        # Cette méthode dépend de votre implémentation de la gestion des événements/tâches.
        # return 0
        # return len(self._coords)  # La version wx
        return len(self.__taskList)  # À adapter

    def RefreshAllItems(self, count):
        self.redraw()

    def RefreshItems(self, *items):
        self.redraw()

    def curselection(self):
        # Cette méthode est un vestige de la version wx.
        # Elle doit être adaptée à la gestion de la sélection de votre application.
        # return []  # À adapter
        return list(self.Selection())

    def clear_selection(self):
        # À adapter
        # pass
        self.Select([])

    def select(self, items):
        # À adapter
        # pass
        self.Select(items)

    def select_all(self):
        # À adapter
        # pass
        items = list()
        for task in self.__taskList:
            items.append(task)
            items.extend(task.children(recursive=True))
        self.select(items)

    # Configuration

    def SetCalendarFormat(self, fmt):
        """
        Définit le format du calendrier (semaine, mois, etc.).
        """
        self.__calFormat = fmt
        now = datetime.datetime.now()

        # Ces méthodes doivent être implémentées dans une classe "date"
        # ou directement ici si elles sont simples.
        if self.__calFormat == self.CAL_WORKWEEKLY:
            # self._start = now.startOfWorkWeek()
            self._start = now - datetime.timedelta(days=now.weekday())
            # self._end = now.endOfWorkWeek()
            self._end = self._start + datetime.timedelta(days=4)
        elif self.__calFormat == self.CAL_WEEKLY:
            # self._start = now.startOfWeek()
            self._start = now - datetime.timedelta(days=now.weekday())
            # self._end = now.endOfWeek()
            self._end = self._start + datetime.timedelta(days=6)
        elif self.__calFormat == self.CAL_MONTHLY:
            # self._start = now.startOfMonth()
            self._start = now.replace(day=1)
            # self._end = now.endOfMonth()
            next_month = now.replace(day=28) + datetime.timedelta(days=4)
            self._end = next_month.replace(day=1) - datetime.timedelta(days=1)

        self.redraw()

    def CalendarFormat(self):
        return self.__calFormat

    def SetHeaderFormat(self, fmt):
        self.__hdrFormat = fmt
        self.redraw()

    def HeaderFormat(self):
        return self.__hdrFormat

    def SetDrawNow(self, drawNow):
        self.__drawNow = drawNow
        self.redraw()

    def DrawNow(self):
        return self.__drawNow

    # Drag and Drop Handlers
    def OnDropURL(self, event, url):
        """Gère le drop d'une URL."""
        if self.__onDropURLCallback:
            self.__onDropURLCallback(event, url)

    def OnDropFiles(self, event, filenames):
        """Gère le drop de fichiers."""
        if self.__onDropFilesCallback:
            self.__onDropFilesCallback(event, filenames)

    def OnDropMail(self, event, mail):
        """Gère le drop d'un mail."""
        if self.__onDropMailCallback:
            self.__onDropMailCallback(event, mail)

    # def HitTest(self, x, y):
    #     """
    #     Effectue un test de position pour déterminer si un événement se trouve aux coordonnées données.
    #     """
    #     # TODO: Implémentez la logique pour déterminer si un événement se trouve à la position (x, y)
    #     # et renvoyez un objet avec les informations appropriées.
    #
    #     # Pour l'instant, renvoie None
    #     return None

    # Méthodes à implémenter en fonction de la structure de données de TaskCoach
    def GetRootEvents(self):
        """Retourne les événements racine."""
        return self.__adapter.getRootItems()

    def GetChildren(self, task):
        """Retourne les enfants d'une tâche."""
        return self.__adapter.children(task)

    def GetStart(self, task):
        """Retourne la date de début d'une tâche."""
        dt = task.plannedStartDateTime()
        # return None if dt == date.DateTime() else dt
        return dt if dt else None

    def GetEnd(self, task):
        """Retourne la date de fin d'une tâche."""
        dt = task.dueDateTime()
        # return None if dt == date.DateTime() else dt
        return dt if dt else None

    def GetText(self, task):
        """Retourne le texte d'une tâche."""
        return self.__adapter.getItemText(task)

    def GetBackgroundColor(self, task):
        """Retourne la couleur de fond d'une tâche."""
        color = task.backgroundColor(True)
        return color if color else "white"

    def GetForegroundColor(self, task):
        """Retourne la couleur de texte d'une tâche."""
        color = task.foregroundColor(True)
        return color if color else "black"

    def GetProgress(self, task):
        """Retourne la progression d'une tâche."""
        p = task.percentageComplete(recursive=True)
        return p / 100.0 if p else None

    def GetIcons(self, task):
        """Retourne les icônes d'une tâche."""
        icons = []  # À adapter
        return icons


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test HierarchicalCalendar Tkinter")
    root.geometry("800x600")

    # Création d'un menu contextuel simple pour le test
    popup = tk.Menu(root, tearoff=0)
    popup.add_command(label="Option 1")
    popup.add_command(label="Option 2")

    # Fonctions de rappel factices pour le test
    def on_select():
        print("Événement de sélection déclenché.")

    def on_edit(event):
        print(f"Modifier l'événement : {event}")

    def on_create(datetime_obj):
        print(f"Créer un événement à : {datetime_obj}")

    def on_selection_changed(self, event):
        print("La sélection a changé !")
        # Vous pouvez accéder à la sélection via self.my_widget._selection
        # Ou en ajoutant les données de sélection à l'événement si nécessaire
        # event.selection = self.my_widget._selection

    def on_drop_url(event, url):
        print(f"URL dropped: {url}")

    def on_drop_files(event, files):
        print(f"Files dropped: {files}")

        # Données de tâches factices
    tasks = []

    # Création du widget HierarchicalCalendar
    h_cal = HierarchicalCalendar(
        root,
        tasks,
        onSelect=on_select,
        onEdit=on_edit,
        onCreate=on_create,
        popupMenu=popup,
        onDropURL=on_drop_url,
        onDropFiles=on_drop_files
    )
    h_cal.pack(fill=tk.BOTH, expand=True)

    # Liaison de l'événement virtuel
    # self.my_widget.bind("<<SelectionChanged>>", self.on_selection_changed)
    h_cal.bind("<<SelectionChanged>>", on_selection_changed)

    root.mainloop()

