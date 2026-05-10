# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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

# Dans TaskCoach original :
#
# Le widget ne doit jamais appeler directement les objets domaine
# Il doit uniquement passer par :
# self.__adapter.children(parent)
# Et le viewer doit uniquement passer par :
# self.presentation()
# voir : self.presentation().observable(recursive=True).children(parent)

# Il serait préférable de remplacer wx.ListCtrl par wx.DataViewCtrl
# (qui est plus moderne et puissant pour les données structurées).
# from __future__ import division
# from builtins import map
# from builtins import zip
# from builtins import str
# from builtins import object
# from future import standard_library

# standard_library.install_aliases()
# from past.utils import old_div
import ast
import logging
import math
import wx
import struct
import tempfile

from future.backports.datetime import timedelta
from wx.lib.scrolledpanel import ScrolledPanel
import wx.lib.agw.piectrl
from taskcoachlib import operating_system
from taskcoachlib import command, domain, render
from taskcoachlib import widgets
from taskcoachlib.domain import task, date

# from taskcoachlib.gui import uicommand, dialog
from taskcoachlib.gui import dialog
from taskcoachlib.gui.uicommand import uicommand
import taskcoachlib.gui.menu

# from taskcoachlib.gui.menu import *
from taskcoachlib.i18n import _

# try:
from pubsub import pub

# except ImportError:
#    try:
#        from ...thirdparty.pubsub import pub
#    except ImportError:
#        from wx.lib.pubsub import pub
from taskcoachlib.thirdparty.wxScheduler import (
    wxSCHEDULER_TODAY,
    wxFancyDrawer,
)
from taskcoachlib.thirdparty import smartdatetimectrl as sdtc
from taskcoachlib.widgets import (
    CalendarConfigDialog,
    HierarchicalCalendarConfigDialog,
)

# from twisted.internet.threads import deferToThread
# from twisted.internet.defer import inlineCallbacks
# NOTE (Twisted Removal - 2024): Replaced deferToThread/inlineCallbacks with
# concurrent.futures ThreadPoolExecutor. This provides the same async thread
# execution without Twisted reactor dependency.
from concurrent.futures import ThreadPoolExecutor
from taskcoachlib.gui.viewer import base
from taskcoachlib.gui.viewer import inplace_editor
from taskcoachlib.gui.viewer import mixin
from taskcoachlib.gui.viewer import refresher

log = logging.getLogger(__name__)


class DueDateTimeCtrl(inplace_editor.DateTimeCtrl):
    """
    Contrôle de sélection de date et heure pour les dates d'échéance.

    Ce contrôle est utilisé pour définir ou modifier la date d'échéance d'une tâche
    en utilisant une sélection relative (par exemple, en fonction d'une autre date).

    Méthodes :
        __init__ (self, parent, wxId, item, column, owner, value, **kwargs) :
            Initialise le contrôle avec les paramètres fournis, notamment l'élément à éditer.
        OnChoicesChange (self, event) :
            Gère les événements de changement de sélection dans le contrôle de choix.
    """

    def __init__(self, parent, wxId, item, column, owner, value, **kwargs):
        # Pass relative info for future implementation
        kwargs["relative"] = True
        kwargs["startDateTime"] = item.GetData().plannedStartDateTime()
        super().__init__(parent, wxId, item, column, owner, value, **kwargs)
        sdtc.EVT_TIME_CHOICES_CHANGE(self._dateTimeCtrl, self.OnChoicesChange)
        self._dateTimeCtrl.LoadChoices(
            item.GetData().settings.get("feature", "sdtcspans")
        )

    def OnChoicesChange(self, event):
        self.item().GetData().settings.settext(
            "feature", "sdtcspans", event.GetValue()
        )


class TaskViewerStatusMessages(object):
    """
    Génère les messages de statut affichés dans le visualiseur de tâches.

    Ces messages incluent le nombre de tâches sélectionnées, visibles, totales
    ainsi que le nombre de tâches en retard, inactives, ou terminées.

    Méthodes :
        __init__(self, viewer) :
            Initialise la classe avec un visualiseur de tâches.
        __call__(self) :
            Retourne les messages de statut basés sur le nombre de tâches dans
            différents états.
    """

    template1 = _("Tasks: %d selected, %d visible, %d total")
    template2 = _("Status: %d overdue, %d late, %d inactive, %d completed")

    def __init__(self, viewer):
        super().__init__()
        log.debug(
            "TaskViewerStatusMessages.__init__ : récupération du viewer et de la présentation."
        )
        self.__viewer = viewer
        self.__presentation = viewer.presentation()

    def __call__(self):
        count = self.__presentation.observable(
            recursive=True
        ).nrOfTasksPerStatus()
        return self.template1 % (
            len(self.__viewer.curselection()),
            self.__viewer.nrOfVisibleTasks(),
            self.__presentation.originalLength(),
        ), self.template2 % (
            count[task.status.overdue],
            count[task.status.late],
            count[task.status.inactive],
            count[task.status.completed],
        )


class BaseTaskViewer(
    mixin.SearchableViewerMixin,  # pylint: disable=W0223
    mixin.FilterableViewerForTasksMixin,
    base.CategorizableViewerMixin,
    base.WithAttachmentsViewerMixin,
    base.TreeViewer,
):
    """
    Visualiseur de base pour les tâches.

    Cette classe gère la visualisation des tâches sous forme d'arborescence,
    et permet d'ajouter des filtres, des pièces jointes, et de rechercher
    des tâches spécifiques.

    Méthodes :
        __init__ (self, *args, **kwargs) :
            Initialise le visualiseur et enregistre les observateurs nécessaires pour suivre les changements d'apparence.
        detach (self) :
            Détache le visualiseur et les observateurs associés.
        _renderTimeSpent (self, *args, **kwargs) :
            Rend le temps passé sous forme décimale ou standard.
        onAppearanceSettingChange (self, value) :
            Met à jour l'apparence des tâches en fonction des paramètres d'affichage.
        domainObjectsToView (self) :
            Retourne les objets de domaine (tâches) à visualiser.
        createFilter (self, taskList) :
            Crée un filtre pour les tâches à visualiser.
        nrOfVisibleTasks (self) :
            Retourne le nombre de tâches visibles.
    """

    coreObjectType = "tasks"

    def __init__(self, *args, **kwargs):
        """
        Initialise le visualiseur et enregistre les observateurs nécessaires pour suivre les changements d'apparence.

        Crée une instance TaskViewerStatusMessages pour gérer les messages de la barre d'état.
        Appelle Self.__RegisterForAppearanceChanges() pour configurer les auditeurs pour les modifications des paramètres liés à l'apparence.
        Appelle wx.CallAfter(self.__DisplayBallon) pour afficher une bulle d'aide (ce n'est probablement pas lié à l'accident).

        Args :
            *args :
            **kwargs :
        """

        log.debug(
            f"BaseTaskViewer : Création du Visualiseur de base pour les tâches."
        )
        super().__init__(*args, **kwargs)
        self.statusMessages = TaskViewerStatusMessages(self)
        self.__registerForAppearanceChanges()
        self.registerObserver(
            self.onDomainObjectAdded,
            # eventType=task.Task.addEventType(),
            eventType=task.Task.addChildEventType(),
        )

        self.registerObserver(
            self.onDomainObjectRemoved,
            # eventType=task.Task.removeEventType(),
            eventType=task.Task.removeChildEventType(),
        )
        log.debug("BaseTaskViewer : Appel de CallAfter.")
        wx.CallAfter(self.__DisplayBalloon)
        log.debug(
            "BaseTaskViewer : CallAfter passé avec succès. Visualiseur de base créé."
        )

    def __DisplayBalloon(self):
        # Guard against deleted C++ object - can happen when wx.CallAfter
        # callback executes after window destruction (e.g., closing nested dialogs)
        try:
            if not self or self.IsBeingDeleted():
                return
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            return
        if (
            self.toolbar.getToolIdByCommand("ViewerHideTasks_completed")
            != wx.ID_ANY
            and self.toolbar.IsShownOnScreen()
            and hasattr(wx.GetTopLevelParent(self), "AddBalloonTip")
        ):
            wx.GetTopLevelParent(
                self
            ).AddBalloonTip(  # Unresolved attribute reference 'AddBalloonTip' for class 'Window'
                self.settings,
                "filtershiftclick",
                self.toolbar,
                getRect=lambda: self.toolbar.GetToolRect(
                    self.toolbar.getToolIdByCommand(
                        "ViewerHideTasks_completed"
                    )
                ),
                message=_(
                    """Shift-click on a filter tool to see only tasks belonging to the corresponding status"""
                ),
            )

    def to_wx_color(rgb):
        """
        Convertit (r, g, b) en wx.Colour.
        """
        import wx

        return wx.Colour(*rgb)

    def to_wx_font(font_tuple):
        import wx

        if not font_tuple:
            return wx.NullFont

        family, size, style = font_tuple

        weight = wx.FONTWEIGHT_NORMAL
        if style == "bold":
            weight = wx.FONTWEIGHT_BOLD

        return wx.Font(size, wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL, weight,
                       faceName=family)

    def __registerForAppearanceChanges(self):
        """
        C’est important pour les mises à jour de l’interface utilisateur !
        Il abonne le spectateur aux modifications de la police,
        de la couleur de premier plan, de la couleur d’arrière-plan et
        des paramètres d’icône pour divers états de tâche (actif, inactif, terminé, etc.).
        Il enregistre également des observateurs pour les modifications d’attributs
         de tâche (par exemple, les conditions préalables).

        Returns :

        """
        log.debug(
            "BaseTaskViewer.__registerForAppearanceChanges : Enregistrement des observateurs pour les changements d'apparence."
        )
        # Zones de préoccupation potentielles dans BaseTaskViewer :
        #
        # La méthode __registerForAppearanceChanges peut valoir la peine
        # d’être examinée si le plantage semble lié à la façon dont
        # l’apparence de la tâche est mise à jour.
        # Cependant, il utilise pub.subscribe et self.registerObserver,
        # qui sont généralement sûrs.
        for appearance in (
            "font",
            "fgcolor",
            "bgcolor",
            "icon",
            "font_dark",
            "fgcolor_dark",
            "bgcolor_dark",
            "icon_dark",
        ):
            appearanceSettings = [
                # "settings.%s.%s" % (appearance, setting)
                f"settings.{appearance}.{setting}"
                for setting in (
                    "activetasks",
                    "inactivetasks",
                    "completedtasks",
                    "duesoontasks",
                    "overduetasks",
                    "latetasks",
                )
            ]
            for appearanceSetting in appearanceSettings:
                pub.subscribe(
                    self.onAppearanceSettingChange, appearanceSetting
                )
        pub.subscribe(self.onAppearanceSettingChange, "settings.window.theme")
        self.registerObserver(
            self.onAttributeChanged_Deprecated,
            eventType=task.Task.appearanceChangedEventType(),
        )
        pub.subscribe(
            self.onAttributeChanged, task.Task.prerequisitesChangedEventType()
        )
        log.debug(
            "BaseTaskViewer : Enregistrement des observateurs pour les changements d'apparence. Appel de refresh."
        )
        pub.subscribe(self.refresh, "powermgt.on")
        wx.CallAfter(self.refresh)  # Ne change rien !

    def detach(self):
        """
        Détache le visualiseur et les observateurs associés.
        """
        super().detach()
        self.statusMessages = None  # Break cycle

    def _renderTimeSpent(self, *args, **kwargs):
        """
        Rend le temps passé sous forme décimale ou standard.

        Args :
            *args :
            **kwargs :

        Returns :

        """
        if self.settings.getboolean("feature", "decimaltime"):
            return render.timeSpentDecimal(*args, **kwargs)
        return render.timeSpent(*args, **kwargs)

    def onAppearanceSettingChange(self, value):  # pylint: disable=W0613
        """
        Met à jour l'apparence des tâches en fonction des paramètres d'affichage.

        Args :
            value :

        Returns :

        """
        log.debug(
            "BaseTaskViewer.onAppearanceSettingChange : Changement de paramètre d'apparence détecté, rafraîchissement du visualiseur."
        )
        # Rafraîchir les éléments affichés dans la visionneuse :
        if self:
            log.debug(
                "BaseTaskViewer.onAppearanceSettingChange : Appel de wx.CallAfter pour rafraîchir le visualiseur."
            )
            wx.CallAfter(
                self.refresh
            )  # Let domain objects update appearance first
        # Show/hide status in toolbar may change too
        log.debug(
            "BaseTaskViewer.onAppearanceSettingChange : Mise à jour de la perspective de la barre d'outil."
        )
        self.toolbar.loadPerspective(self.toolbar.perspective(), cache=False)

    def domainObjectsToView(self):
        """
        Retourne les objets de domaine (tâches) à visualiser.

        Returns :
            BaseTaskViewer.taskFile.tasks() :
        """
        # return self.taskFile.tasks()
        to_return = self.taskFile.tasks()
        log.debug(
            f"BaseTaskViewer.domainObjectsToView : Nombre total d'objets dans la TaskList : {len(to_return)}"
        )

        # Task Coach utilise souvent des filtres ou des hiérarchies.
        # Vérifions les tâches à la racine ou toutes les tâches.
        for i, t in enumerate(to_return):
            log.info(f"Tâche {i}: {t.subject()} (ID: {t.id()})")

        if len(to_return) == 0:
            log.warning(
                "BaseTaskViewer.domainObjectsToView : ALERTE : Aucune tâche n'est présente dans le modèle après le chargement."
            )
        log.debug(
            f"BaseTaskViewer.domainObjectsToView : Retourne les tâches à visualiser : self.taskFile.tasks()={to_return}."
        )

        return to_return

    def onDomainObjectAdded(self, event):
        self.refresh()

    def onDomainObjectRemoved(self, event):
        self.refresh()

    def isShowingTasks(self):
        return True

    def createFilter(self, taskList):
        """
        Crée un filtre pour les tâches à visualiser.

        Crée un filtre pour exclure les tâches supprimées.

        Il s’agit d’une opération au niveau des données,
        et non de l’interface utilisateur.

        Args :
            taskList : Liste des tâches supprimées à filtrer.

        Returns :
            Une méthode super de la création de filtre sur les tâches supprimées.
        """
        log.debug(
            "BaseTaskViewer.createFilter : Création d'un filtre pour les tâches supprimées."
        )
        # Il est peu probable que la méthode createFilter
        # provoquent des blocages de l’interface utilisateur,
        # car elle gère le filtrage des données.
        #
        tasks = domain.base.DeletedFilter(taskList)  # Commenté pour test
        return super().createFilter(tasks)
        # return taskList  # Si cela fait réapparaître les tâches, le problème vient des filtres.

    def nrOfVisibleTasks(self):
        """
        Retourne le nombre de tâches visibles.


        Calcule le nombre de tâches actuellement visibles dans le visualiseur.

        Returns :
            (int) : Le nombre d'objets de domaine que cette visionneuse affiche actuellement.
        """
        # Il est peu probable que la méthodes nrOfVisibleTasks provoque
        # des blocages de l’interface utilisateur,
        # car elle gère le comptage des données.
        #
        # Make this overridable for viewers where the widget does not show all
        # items in the presentation, i.e. the widget does filtering on its own.
        log.debug(
            f"BaseTaskViewer.nrOfVisibleTasks : Calcul du nombre de tâches visibles."
        )
        return len(self.presentation())


class BaseTaskTreeViewer(BaseTaskViewer):  # pylint: disable=W0223
    # class BaseTaskTreeViewer(BaseTaskViewer):
    """
    Visualiseur de tâches sous forme d'arborescence avec rafraîchissement automatique.

    Ce visualiseur est conçu pour afficher les tâches sous forme d'arbre
    avec des rafraîchissements en temps réel toutes les secondes ou minutes.

    Méthodes :
        __init__(self, *args, **kwargs) :
            Initialise le visualiseur avec des options supplémentaires pour rafraîchir les tâches.
        detach (self) :
            Détache les observateurs et arrête les rafraîchissements automatiques.
        newItemDialog (self, *args, **kwargs) :
            Ouvre une boîte de dialogue pour créer un nouvel élément (tâche ou sous-tâche).
        editItemDialog (self, items, bitmap, columnName="", items_are_new=False) :
            Ouvre une boîte de dialogue pour éditer les tâches sélectionnées.
        createTaskPopupMenu (self) :
            Crée le menu contextuel pour les tâches.
    """
    defaultTitle = _("Tasks")
    defaultBitmap = "led_blue_icon"

    def __init__(self, *args, **kwargs):
        """
        Initialise le visualiseur avec des options supplémentaires pour rafraîchir les tâches.

        Appelle le constructeur BaseTaskViewer.
        Crée en option des instances refresher(SecondRefresher, MinuteRefresher)
        pour des mises à jour automatiques.
        """
        # Args :
        #     *args :
        #     **kwargs :

        log.debug(
            f"BaseTaskTreeViewer : Création du Visualiseur de tâches sous forme d'arborescence avec rafraîchissement automatique."
        )
        super().__init__(*args, **kwargs)
        if kwargs.get("doRefresh", True):
            self.secondRefresher = refresher.SecondRefresher(
                self, task.Task.trackingChangedEventType()
            )
            self.minuteRefresher = refresher.MinuteRefresher(self)
        else:
            self.secondRefresher = self.minuteRefresher = None
        log.debug(
            "BaseTaskTreeViewer initialisé avec rafraîchissement automatique."
        )

    def detach(self):
        """
        Détache les observateurs et arrête les rafraîchissements automatiques.

        Returns :

        """
        super().detach()
        if hasattr(self, "secondRefresher") and self.secondRefresher:
            self.secondRefresher.stopClock()
            self.secondRefresher.removeInstance()
            del self.secondRefresher
        if hasattr(self, "minuteRefresher") and self.minuteRefresher:
            self.minuteRefresher.stopClock()
            del self.minuteRefresher

    def newItemDialog(self, *args, **kwargs):
        """
        Ouvre une boîte de dialogue pour créer un nouvel élément (tâche ou sous-tâche).

        Args :
            *args :
            **kwargs :

        Returns :

        """
        kwargs["categories"] = self.taskFile.categories().filteredCategories()
        return super().newItemDialog(*args, **kwargs)

    def editItemDialog(
        self, items, bitmap, columnName="", items_are_new=False
    ):
        """
        Ouvre une boîte de dialogue pour éditer les tâches sélectionnées.

        Args :
            items :
            bitmap :
            columnName :
            items_are_new :

        Returns :

        """
        if isinstance(items[0], task.Task):
            return super().editItemDialog(
                items,
                bitmap,
                columnName=columnName,
                items_are_new=items_are_new,
            )
        else:
            return dialog.editor.EffortEditor(
                wx.GetTopLevelParent(self),
                items,
                self.settings,
                self.taskFile.efforts(),
                self.taskFile,
                bitmap=bitmap,
                items_are_new=items_are_new,
            )

    def itemEditorClass(self):
        return dialog.editor.TaskEditor

    def newItemCommandClass(self):
        return command.NewTaskCommand

    def newSubItemCommandClass(self):
        return command.NewSubTaskCommand

    def newSubItemCommand(self):
        kwargs = dict()
        if self.__shouldPresetPlannedStartDateTime():
            kwargs["plannedStartDateTime"] = (
                task.Task.suggestedPlannedStartDateTime()
            )
        if self.__shouldPresetDueDateTime():
            kwargs["dueDateTime"] = task.Task.suggestedDueDateTime()
        if self.__shouldPresetActualStartDateTime():
            kwargs["actualStartDateTime"] = (
                task.Task.suggestedActualStartDateTime()
            )
        if self.__shouldPresetCompletionDateTime():
            kwargs["completionDateTime"] = (
                task.Task.suggestedCompletionDateTime()
            )
        if self.__shouldPresetReminderDateTime():
            kwargs["reminder"] = task.Task.suggestedReminderDateTime()
        # pylint: disable=W0142
        log.debug(
            f"BaseTaskTreeViewer.newSubItemCommand : Création d'une nouvelle commande de sous-tâche avec les paramètres suivants : {kwargs}"
        )
        return self.newSubItemCommandClass()(
            self.presentation(), self.curselection(), **kwargs
        )

    def __shouldPresetPlannedStartDateTime(self):
        return self.settings.get(
            "view", "defaultplannedstartdatetime"
        ).startswith("preset")

    def __shouldPresetDueDateTime(self):
        return self.settings.get("view", "defaultduedatetime").startswith(
            "preset"
        )

    def __shouldPresetActualStartDateTime(self):
        return self.settings.get(
            "view", "defaultactualstartdatetime"
        ).startswith("preset")

    def __shouldPresetCompletionDateTime(self):
        return self.settings.get(
            "view", "defaultcompletiondatetime"
        ).startswith("preset")

    def __shouldPresetReminderDateTime(self):
        return self.settings.get("view", "defaultreminderdatetime").startswith(
            "preset"
        )

    def deleteItemCommand(self):
        log.debug(
            "BaseTaskTreeViewer.deleteItemCommand : Création d'une commande de suppression de tâche."
        )
        return command.DeleteTaskCommand(
            self.presentation(),
            self.curselection(),
            shadow=self.settings.getboolean("feature", "syncml"),
        )

    def getSupportedPasteTypes(self):
        return (task.Task,)

    def createTaskPopupMenu(self):
        """
        Crée et retourne le TaskPopupMenu/menu contextuel pour les tâches.

        Directement lié à la création de menu. Crée un menu Popup de tâche qui
        est un menu wx.Menu.

        Returns :
            Le menu contextuel TaskPopupMenu.
        """
        # from taskcoachlib.gui.menu import TaskPopupMenu
        log.debug(
            f"BaseTaskTreeViewer.createTaskPopupMenu : Création du menu contextuel."
        )
        # log.debug(f"mainwindow={self.parent}, settings={self.settings},"
        #           f"tasks={self.presentation()}, efforts={self.taskFile.efforts()},"
        #           f"categories={self.taskFile.categories()}, taskViewer={self}")
        # return taskcoachlib.gui.menu.TaskPopupMenu(
        #     self.parent,
        #     self.settings,
        #     self.presentation(),
        #     self.taskFile.efforts(),
        #     self.taskFile.categories(),
        #     self)
        task_popup_menu = taskcoachlib.gui.menu.TaskPopupMenu(
            self.parent,
            self.settings,
            self.presentation(),
            self.taskFile.efforts(),
            self.taskFile.categories(),
            self,
        )
        return task_popup_menu

    def createCreationToolBarUICommands(self):
        """
        Cette méthode crée des commandes UI (en utilisant le module uicommand)
        pour la barre d'outil. Les commandes UI manipulent souvent l'UI (par
        exemple, créer des boîtes de dialogue, changer les propriétés de widget.)

        Returns :

        """
        log.debug(
            "BaseTaskTreeViewer.createCreationToolBarUICommands : Création des commandes de la barre d'outil de création."
        )
        return (
            uicommand.TaskNew(
                taskList=self.presentation(), settings=self.settings
            ),
            uicommand.NewSubItem(viewer=self),
            uicommand.TaskNewFromTemplateButton(
                taskList=self.presentation(),
                settings=self.settings,
                bitmap="newtmpl",
            ),
        ) + super().createCreationToolBarUICommands()

    def createActionToolBarUICommands(self):
        """
        Cette méthode crée des commandes UI (en utilisant le module uicommand)
        pour la barre d'outil. Les commandes UI manipulent souvent l'UI (par
        exemple, créer des boîtes de dialogue, changer les propriétés de widget.)

        Returns :

        """
        uiCommands = (
            uicommand.AddNote(settings=self.settings, viewer=self),
            uicommand.TaskMarkInactive(settings=self.settings, viewer=self),
            uicommand.TaskMarkActive(settings=self.settings, viewer=self),
            uicommand.TaskMarkCompleted(settings=self.settings, viewer=self),
        )
        uiCommands += (
            # EffortStart needs a reference to the original (task) list to
            # be able to stop tracking effort for tasks that are already
            # being tracked, but that might be filtered in the viewer's
            # presentation.
            None,
            uicommand.EffortStart(viewer=self, taskList=self.taskFile.tasks()),
            uicommand.EffortStop(
                viewer=self,
                effortList=self.taskFile.efforts(),
                taskList=self.taskFile.tasks(),
            ),
        )
        return uiCommands + super().createActionToolBarUICommands()

    def createModeToolBarUICommands(self):
        hideUICommands = tuple(
            [
                uicommand.ViewerHideTasks(
                    taskStatus=status, settings=self.settings, viewer=self
                )
                for status in task.Task.possibleStatuses()
            ]
        )
        otherModeUICommands = super().createModeToolBarUICommands()
        separator = (None,) if otherModeUICommands else ()
        return hideUICommands + separator + otherModeUICommands

    # @staticmethod
    def iconName(self, item, isSelected):
        return (
            item.selectedIcon(recursive=True)
            if isSelected
            else item.icon(recursive=True)
        )

    def getItemTooltipData(self, task):  # pylint: disable=W0621
        log.debug(
            f"BaseTaskTreeViewer.getItemTooltipData : task={self.getItemText(task)}"
        )
        result = [
            (
                self.iconName(task, task in self.curselection()),
                [self.getItemText(task)],
            )
        ]
        if task.notes():
            result.append(
                (
                    "note_icon",
                    sorted([note.subject() for note in task.notes()]),
                )
            )
        # # Note: attachments are handled by WithAttachmentsViewerMixin
        # if task.attachments():
        #     result.append(
        #         (
        #             "paperclip_icon",
        #             sorted(
        #                 [str(attachment) for attachment in task.attachments()]
        #             ),
        #         )
        #     )
        return result + super().getItemTooltipData(task)

    def label(self, task):  # pylint: disable=W0621
        return self.getItemText(task)


class RootNode(object):
    """
    Classe de base pour représenter la racine d'une arborescence de tâches.

    Elle permet d'obtenir les tâches à la racine et de gérer leur affichage,
    ainsi que les attributs tels que les couleurs et les polices des éléments de tâche.

    Attributs :
        tasks : Liste des tâches à la racine de l'arborescence.

    Méthodes :
        __init__(self, tasks) : Initialise la racine avec les tâches données.
        subject(self) : Retourne une chaîne vide (aucun sujet pour la racine).
        children(self, recursive=False) : Retourne les tâches enfants.
        foregroundColor(self, *args, **kwargs) : Retourne la couleur de premier plan.
        backgroundColor(self, *args, **kwargs) : Retourne la couleur d'arrière-plan.
        font(self, *args, **kwargs) : Retourne la police à utiliser pour afficher la tâche.
        completed(self, *args, **kwargs) : Indique si une tâche est terminée.
    """

    def __init__(self, tasks):
        """
        Initialise la racine avec les tâches données.

        Args :
            tasks : Liste des tâches à la racine de l'arborescence.
        """
        log.debug(f"RootNode : Initialise la racine avec les tâches {tasks}.")
        # Liste des tâches à la racine de l'arborescence :
        self.tasks = tasks

    # @staticmethod
    def subject(self):
        """
        Retourne une chaîne vide (aucun sujet pour la racine).

        Returns :
            Le sujet de la tâche.
        """
        return ""

    def children(self, recursive=False):
        # Attention : la méthode children est appelée fréquemment pour obtenir les tâches à afficher.
        # mais children est aussi une méthode python standard pour les arbres, et elle est utilisée par les visualiseurs d'arbres pour obtenir les enfants d'un nœud.
        """
        Retourne les tâches enfants.

        Args :
            recursive (bool) :

        Returns :
            Les tâches enfants.
        """
        if recursive:
            return self.tasks[:]
        else:
            return self.tasks.rootItems()

    # pylint: disable=W0613

    # @staticmethod
    def foregroundColor(self, *args, **kwargs):
        """
        Retourne la couleur de premier plan.

        Args :
            *args :
            **kwargs :

        Returns :

        """
        return None

    # @staticmethod
    def backgroundColor(self, *args, **kwargs):
        """
        Retourne la couleur d'arrière-plan.

        Args :
            *args :
            **kwargs :

        Returns:

        """
        return None

    # @staticmethod
    def font(self, *args, **kwargs):
        """
        Retourne la police à utiliser pour afficher la tâche.

        Args :
            *args :
            **kwargs :

        Returns :

        """
        return None

    # @staticmethod
    def completed(self, *args, **kwargs):
        """
        Indique si une tâche est terminée.

        Args :
            *args :
            **kwargs :

        Returns :
            (bool) : False par défaut, aucune tâche terminée.
        """
        return False

    late = dueSoon = inactive = overdue = isBeingTracked = completed


class SquareMapRootNode(RootNode):
    """
    Classe représentant la racine d'une carte carrée des tâches.

    Elle permet de calculer et d'obtenir des attributs spécifiques aux tâches
    dans une vue sous forme de carte carrée, notamment pour des attributs comme
    le budget ou le temps passé.

    Méthodes :
        __getattr__(self, attr) : Retourne un attribut calculé récursivement.
    """

    def __getattr__(self, attr):
        """
        Retourne un attribut calculé récursivement.

        Args :
            attr :

        Returns :
            getTaskAttribute :
        """

        def getTaskAttribute(recursive=True):
            if recursive:
                # return max(
                #     sum(
                #         (
                #             getattr(task, attr)(recursive=True)
                #             for task in self.children()
                #         ),
                #         self.__zero,
                #     ),
                #     self.__zero,
                # )
                s = 0
                # s = timedelta(0)
                for task in self.children():
                    # Patch Phoenix compatibility:
                    if hasattr(task, "_getAttrDict"):
                        d = task._getAttrDict()
                        if attr in d:
                            value = d[attr]
                        else:
                            value = getattr(task, attr)
                    else:
                        value = getattr(task, attr)
                    s += value(
                        recursive=True
                    )  # value = task._getAttrDict[attr]
                return max(s, self.__zero)
            else:
                return self.__zero

        self.__zero = (
            date.TimeDelta()
            if attr in ("budget", "budgetLeft", "timeSpent")
            else 0
        )  # pylint: disable=W0201
        return getTaskAttribute


class TimelineRootNode(RootNode):
    """
    Classe représentant la racine de l'arborescence dans une vue chronologique des tâches.

    Cette classe trie les tâches en fonction de leur date de début planifiée et
    permet de gérer l'affichage des tâches dans une chronologie.

    Méthodes :
        children(self, recursive=False) : Trie les enfants en fonction de leur date de début planifiée.
        parallel_children(self, recursive=False) : Retourne les enfants parallèles (enfants directs).
        sequential_children(self) : Retourne une liste vide (pas de tâches séquentielles ici).
        plannedStartDateTime(self, recursive=False) : Retourne la date de début planifiée la plus tôt.
        dueDateTime(self, recursive=False) : Retourne la date d'échéance la plus tardive.
    """

    # log.debug(f"TimelineRootNode : lancé avec RootNode={RootNode}")
    # log crée des erreurs !
    def children(self, recursive=False):
        children = super().children(recursive)
        children.sort(key=lambda task: task.plannedStartDateTime())
        return children

    def parallel_children(self, recursive=False):
        return self.children(recursive)

    # @staticmethod
    def sequential_children(self):
        return []

    def plannedStartDateTime(self, recursive=False):  # pylint: disable=W0613
        plannedStartDateTimes = [
            item.plannedStartDateTime(recursive=True)
            for item in self.parallel_children()
        ]
        plannedStartDateTimes = [
            dt for dt in plannedStartDateTimes if dt != date.DateTime()
        ]
        if not plannedStartDateTimes:
            plannedStartDateTimes.append(date.Now())
        return min(plannedStartDateTimes)

    def dueDateTime(self, recursive=False):  # pylint: disable=W0613
        dueDateTimes = [
            item.dueDateTime(recursive=True)
            for item in self.parallel_children()
        ]
        dueDateTimes = [dt for dt in dueDateTimes if dt != date.DateTime()]
        if not dueDateTimes:
            dueDateTimes.append(date.Tomorrow())
        return max(dueDateTimes)


class TimelineViewer(BaseTaskTreeViewer):
    """
    Visualiseur de la chronologie des tâches.

    Affiche les tâches dans une vue chronologique avec des options pour les éditer,
    les sélectionner, et voir leurs dates de début et d'échéance.

    Méthodes :
        __init__(self, *args, **kwargs) :
            Initialise le visualiseur chronologique avec des paramètres spécifiques.
        createWidget(self) :
            Crée le widget chronologique pour afficher les tâches.
        onEdit(self, item) :
            Permet l'édition d'une tâche directement depuis la vue chronologique.
        curselection(self) :
            Retourne la sélection actuelle dans la chronologie.
        bounds(self, item) :
            Calcule les limites de temps d'un élémentdans la chronologie..
    """

    defaultTitle = _("Timeline")
    defaultBitmap = "timelineviewer"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "timelineviewer")
        super().__init__(*args, **kwargs)
        for eventType in (
            task.Task.subjectChangedEventType(),
            task.Task.plannedStartDateTimeChangedEventType(),
            task.Task.dueDateTimeChangedEventType(),
            task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )

    def createWidget(self):
        self.rootNode = TimelineRootNode(
            self.presentation()
        )  # pylint: disable=W0201
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        return widgets.Timeline(
            self, self.rootNode, self.onSelect, self.onEdit, itemPopupMenu
        )

    def onEdit(self, item):
        edit = uicommand.Edit(viewer=self)
        edit(item)

    # def curselection(self):
    def curselection(self, forceUpdate=False):
        # Override curselection, because there is no need to translate indices
        # back to domain objects. Our widget already returns the selected domain
        # object itself. forceUpdate is ignored since widget always returns fresh data.
        # TODO: AttributeError: 'TimelineViewer' object has no attribute 'widget'
        return self.widget.curselection()

    def bounds(self, item):
        times = [self.start(item), self.stop(item)]
        for child in self.parallel_children(item) + self.sequential_children(
            item
        ):
            times.extend(self.bounds(child))
        times = [time for time in times if time is not None]
        return (min(times), max(times)) if times else []

    # @staticmethod
    def start(self, item, recursive=False):
        try:
            start = item.plannedStartDateTime(recursive=recursive)
            if start == date.DateTime():
                return None
        except AttributeError:
            start = item.getStart()
        return start.toordinal()

    # @staticmethod
    def stop(self, item, recursive=False):
        try:
            if item.completed():
                stop = item.completionDateTime(recursive=recursive)
            else:
                stop = item.dueDateTime(recursive=recursive)
            if stop == date.DateTime():
                return None
            else:
                stop += date.ONE_DAY
        except AttributeError:
            stop = item.getStop()
            if not stop:
                return None
        return stop.toordinal()

    # @staticmethod
    def sequential_children(self, item):
        try:
            return item.efforts()
        except AttributeError:
            return []

    def parallel_children(self, item, recursive=False):
        try:
            children = [
                child
                for child in item.children(recursive=recursive)
                if child in self.presentation()
            ]
            children.sort(key=lambda task: task.plannedStartDateTime())
            return children
        except AttributeError:
            return []

    # @staticmethod
    def foreground_color(self, item, depth=0):  # pylint: disable=W0613
        return item.foregroundColor(recursive=True)

    # @staticmethod
    def background_color(self, item, depth=0):  # pylint: disable=W0613
        return item.backgroundColor(recursive=True)

    # @staticmethod
    def font(self, item, depth=0):  # pylint: disable=W0613
        return item.font(recursive=True)

    def icon(self, item, isSelected=False):
        bitmap = self.iconName(item, isSelected)
        return wx.ArtProvider.GetIcon(bitmap, wx.ART_MENU, (16, 16))

    # @staticmethod
    def now(self):
        return date.Now().toordinal()

    # @staticmethod
    def nowlabel(self):
        return _("Now")

    def getItemTooltipData(self, item):
        if isinstance(item, task.Task):
            result = super().getItemTooltipData(item)
        else:
            result = [
                (
                    None,
                    [
                        render.dateTimePeriod(
                            item.getStart(), item.getStop(), humanReadable=True
                        )
                    ],
                )
            ]
            if item.description():
                result.append(
                    (
                        None,
                        [
                            line.rstrip("\n")
                            for line in item.description().split("\n")
                        ],
                    )
                )
        return result


class SquareTaskViewer(BaseTaskTreeViewer):
    """
    Visualiseur des tâches sous forme de carte carrée.

    Affiche les tâches sous forme de blocs carrés en fonction de critères
    tels que le budget, le temps passé, ou la priorité.

    Méthodes :
        __init__(self, *args, **kwargs) :
            Initialise le visualiseur avec les critères de tri et de rendu des tâches.
        createWidget(self) :
            Crée le widget de la carte carrée pour afficher les tâches.
        orderBy(self, choice) :
            Trie les tâches selon le critère choisi (budget, temps, etc.).
        render(self, value) :
            Rend la valeur associée à une tâche (par exemple, budget ou temps).
    """

    defaultTitle = _("Task square map")
    defaultBitmap = "squaremapviewer"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "squaretaskviewer")
        self.__orderBy = "revenue"
        self.__transformTaskAttribute = lambda x: x
        self.__zero = 0
        self.renderer = dict(
            budget=render.budget,
            timeSpent=self._renderTimeSpent,
            fixedFee=render.monetaryAmount,
            revenue=render.monetaryAmount,
            priority=render.priority,
        )
        super().__init__(*args, **kwargs)
        # sortKeys = eval(self.settings.get(self.settingsSection(), "sortby"))
        sortKeys = ast.literal_eval(
            self.settings.get(self.settingsSection(), "sortby")
        )
        orderBy = sortKeys[0] if sortKeys else "budget"
        self.orderBy(sortKeys[0] if sortKeys else "budget")
        pub.subscribe(
            self.on_order_by_changed,
            "settings.%s.sortby" % self.settingsSection(),
        )
        self.orderUICommand.setChoice(self.__orderBy)
        for eventType in (
            task.Task.subjectChangedEventType(),
            task.Task.dueDateTimeChangedEventType(),
            task.Task.plannedStartDateTimeChangedEventType(),
            task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )

    def curselectionIsInstanceOf(self, class_):
        return class_ == task.Task

    def createWidget(self):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        log.debug(
            f"SquareTaskViewer.createWidget : Création du widget SquareMap avec rootNode={SquareMapRootNode(self.presentation())}."
        )
        return widgets.SquareMap(
            self,
            SquareMapRootNode(self.presentation()),
            self.onSelect,
            uicommand.Edit(viewer=self),
            itemPopupMenu,
        )

    def createModeToolBarUICommands(self):
        self.orderUICommand = uicommand.SquareTaskViewerOrderChoice(
            viewer=self, settings=self.settings
        )  # pylint: disable=W0201
        return super().createModeToolBarUICommands() + (self.orderUICommand,)

    def hasModes(self):
        return True

    def getModeUICommands(self):
        return [_("Lay out tasks by"), None] + [
            uicommand.SquareTaskViewerOrderByOption(
                menuText=menuText,
                value=value,
                viewer=self,
                settings=self.settings,
            )
            for (menuText, value) in zip(
                uicommand.SquareTaskViewerOrderChoice.choiceLabels,
                uicommand.SquareTaskViewerOrderChoice.choiceData,
            )
        ]

    def on_order_by_changed(self, value):
        self.orderBy(value)

    def orderBy(self, choice):
        """Trie les tâches selon le critère choisi (budget, temps, etc.)."""
        if choice == self.__orderBy:
            return
        oldChoice = self.__orderBy
        self.__orderBy = choice
        try:
            oldEventType = getattr(
                task.Task, "%sChangedEventType" % oldChoice
            )()
        except AttributeError:
            oldEventType = "task.%s" % oldChoice
        if oldEventType.startswith("pubsub"):
            try:
                pub.unsubscribe(self.onAttributeChanged, oldEventType)
            except pub.TopicNameError:
                pass  # Can happen on first call to orderBy
        else:
            self.removeObserver(
                self.onAttributeChanged_Deprecated, oldEventType
            )
        try:
            newEventType = getattr(task.Task, "%sChangedEventType" % choice)()
            # newEventType = getattr(task.Task, f"{choice}ChangedEventType")()
        except AttributeError:
            newEventType = "task.%s" % choice
        if newEventType.startswith("pubsub"):
            pub.subscribe(self.onAttributeChanged, newEventType)
        else:
            self.registerObserver(
                self.onAttributeChanged_Deprecated, newEventType
            )
        if choice in ("budget", "timeSpent"):
            # self.__transformTaskAttribute = lambda timeSpent: timeSpent.milliseconds() / 1000
            # self.__transformTaskAttribute = lambda timeSpent: old_div(timeSpent.milliseconds(), 1000)
            self.__transformTaskAttribute = (
                lambda timeSpent: timeSpent.milliseconds() // 1000
            )
            self.__zero = date.TimeDelta()
        else:
            self.__transformTaskAttribute = lambda x: x
            self.__zero = 0
        log.debug(
            f"SquareTaskViewer.orderBy : Changement du critère de tri de {oldChoice} à {choice}. Appel de refresh:"
        )
        self.refresh()

    # def curselection(self):
    def curselection(self, forceUpdate=False):
        # Override curselection, because there is no need to translate indices
        # back to domain objects. Our widget already returns the selected domain
        # object itself. forceUpdate is ignored since widget always returns fresh data.
        return self.widget.curselection()

    def nrOfVisibleTasks(self):
        log.debug(
            f"SquareTaskViewer.nrOfVisibleTasks : Calcul du nombre de tâches visibles avec orderBy={self.__orderBy}."
        )
        return len(
            [
                eachTask
                for eachTask in self.presentation()
                if getattr(eachTask, self.__orderBy)(recursive=True)
                > self.__zero
            ]
        )

    # SquareMap adapter methods:
    # pylint: disable=W0621

    def overall(self, task):
        return self.__transformTaskAttribute(
            max(getattr(task, self.__orderBy)(recursive=True), self.__zero)
        )

    def children_sum(self, children, parent):  # pylint: disable=W0613
        children_sum = sum(
            (
                max(
                    getattr(child, self.__orderBy)(recursive=True), self.__zero
                )
                for child in children
                if child in self.presentation()
            ),
            self.__zero,
        )
        return self.__transformTaskAttribute(max(children_sum, self.__zero))

    def empty(self, task):
        overall = self.overall(task)
        if overall:
            children_sum = self.children_sum(self.children(task), task)
            return max(
                self.__transformTaskAttribute(self.__zero),
                (overall - children_sum),
            ) / float(overall)
        return 0

    def getItemText(self, task):
        # log.debug()
        text = super().getItemText(task)
        value = self.render(getattr(task, self.__orderBy)(recursive=False))
        # return "%s (%s)" % (text, value) if value else text
        return f"{text} ({value})" if value else text

    def value(self, task, parent=None):  # pylint: disable=W0613
        return self.overall(task)

    # @staticmethod
    def foreground_color(self, task, depth):  # pylint: disable=W0613
        return task.foregroundColor(recursive=True)

    # @staticmethod
    def background_color(self, task, depth):  # pylint: disable=W0613
        red = blue = 255 - (depth * 3) % 100
        green = 255 - (depth * 2) % 100
        color = wx.Colour(red, green, blue)
        return task.backgroundColor(recursive=True) or color

    # @staticmethod
    def font(self, task, depth):  # pylint: disable=W0613
        return task.font(recursive=True)

    def icon(self, task, isSelected):
        bitmap = self.iconName(task, isSelected) or "led_blue_icon"
        return wx.ArtProvider.GetIcon(bitmap, wx.ART_MENU, (16, 16))

    # Helper methods

    def render(self, value):
        return self.renderer[self.__orderBy](value)


class HierarchicalCalendarViewer(
    mixin.AttachmentDropTargetMixin,
    mixin.SortableViewerForTasksMixin,
    BaseTaskTreeViewer,
):
    """
    Visualiseur de calendrier hiérarchique.

    Affiche les tâches dans un calendrier hiérarchisé en fonction de leurs dates de début
    et d'échéance.

    Méthodes :
        createWidget (self) :
            Crée le widget du calendrier hiérarchique.
        onEdit (self, item) :
            Permet l'édition des tâches directement depuis la vue du calendrier.
        onCreate (self, dateTime, show=True) :
            Crée une nouvelle tâche à une date spécifique.
        atMidnight (self) :
            Rafraîchit le calendrier à minuit pour mettre à jour les dates.
    """

    defaultTitle = _("Hierarchical calendar")
    defaultBitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "hierarchicalcalendarviewer")
        super().__init__(*args, **kwargs)

        # pylint: disable=E1101
        for eventType in (
            task.Task.subjectChangedEventType(),
            task.Task.attachmentsChangedEventType(),
            task.Task.notesChangedEventType(),
            task.Task.trackingChangedEventType(),
            task.Task.percentageCompleteChangedEventType(),
        ):
            # if eventType is not None and eventType.startswith("pubsub"):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )

        # Dates are treated separately because the layout may change (_Invalidate)
        # pylint: disable=E1101
        for eventType in (
            task.Task.plannedStartDateTimeChangedEventType(),
            task.Task.dueDateTimeChangedEventType(),
            task.Task.completionDateTimeChangedEventType(),
        ):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onLayoutAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onLayoutAttributeChanged_Deprecated, eventType
                )

        self.reconfig()

        # Subscribe to global timer for midnight processing
        pub.subscribe(self._onDateChanged, "timer.date")

    def _onDateChanged(self, timestamp):
        """Handle date change from global timer."""
        self.atMidnight()

    def reconfig(self):
        self.widget.SetCalendarFormat(
            self.settings.getint(self.settingsSection(), "calendarformat")
        )
        self.widget.SetHeaderFormat(
            self.settings.getint(self.settingsSection(), "headerformat")
        )
        self.widget.SetDrawNow(
            self.settings.getboolean(self.settingsSection(), "drawnow")
        )
        self.widget.SetTodayColor(
            list(
                map(
                    int,
                    self.settings.get(
                        self.settingsSection(), "todaycolor"
                    ).split(","),
                )
            )
        )

    def configure(self):
        dialog = HierarchicalCalendarConfigDialog(
            self.settings,
            self.settingsSection(),
            self,
            title=_("Hierarchical calendar viewer configuration"),
        )
        dialog.CentreOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            self.reconfig()

    def createModeToolBarUICommands(self):
        return super().createModeToolBarUICommands() + (
            None,
            uicommand.HierarchicalCalendarViewerConfigure(viewer=self),
            uicommand.HierarchicalCalendarViewerPreviousPeriod(viewer=self),
            uicommand.HierarchicalCalendarViewerToday(viewer=self),
            uicommand.HierarchicalCalendarViewerNextPeriod(viewer=self),
        )

    def detach(self):
        super().detach()
        pub.unsubscribe(self._onDateChanged, "timer.date")

    def atMidnight(self):
        self.widget.SetCalendarFormat(self.widget.CalendarFormat())

    def onLayoutAttributeChanged(self, newValue, sender):
        self.refresh()

    def onLayoutAttributeChanged_Deprecated(self, event):
        self.refresh()

    def isTreeViewer(self):
        return True

    def onEverySecond(self, event):  # pylint: disable=W0221,W0613
        pass

    def createWidget(self):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        widget = widgets.HierarchicalCalendar(
            self,
            self.presentation(),
            self.onSelect,
            self.onEdit,
            self.onCreate,
            itemPopupMenu,
            **self.widgetCreationKeywordArguments(),
        )
        return widget

    def onEdit(self, item):
        edit = uicommand.Edit(viewer=self)
        edit(item)

    def onCreate(self, dateTime, show=True):
        plannedStartDateTime = dateTime
        dueDateTime = (
            dateTime.endOfDay()
            if dateTime == dateTime.startOfDay()
            else dateTime
        )
        create = uicommand.TaskNew(
            taskList=self.presentation(),
            settings=self.settings,
            taskKeywords=dict(
                plannedStartDateTime=plannedStartDateTime,
                dueDateTime=dueDateTime,
            ),
        )
        return create(event=None, show=show)

    def isAnyItemExpandable(self):
        return False

    def isAnyItemCollapsable(self):
        return False

    def GetPrintout(self, settings):
        return self.widget.GetPrintout(settings)


class CalendarViewer(
    mixin.AttachmentDropTargetMixin,
    mixin.SortableViewerForTasksMixin,
    BaseTaskTreeViewer,
):
    """
    Classe d'affichage des tâches sous forme de calendrier.

    Hérite de :
    - AttachmentDropTargetMixin : permet le glisser-déposer de pièces jointes,
    - SortableViewerForTasksMixin : tri des tâches par colonnes,
    - BaseTaskTreeViewer : base des vues arborescentes de tâches (même si ici ce n'est pas un arbre).

    Cette vue permet de visualiser les tâches sur une période, avec personnalisation
    du nombre de périodes, du style, de l'orientation, etc. L'utilisateur peut aussi
    configurer les couleurs, l'affichage du "maintenant", et d'autres filtres.
    """

    defaultTitle = _("Calendar")
    defaultBitmap = "calendar_icon"

    def __init__(self, *args, **kwargs):
        """
        Initialise la vue calendrier avec les paramètres et préférences utilisateurs :
        - Restaure la date de vue si enregistrée,
        - Applique le jour de début de semaine,
        - Configure les heures de travail et les préférences d'affichage,
        - S'abonne aux modifications des tâches et des paramètres.
        """
        kwargs.setdefault("settingsSection", "calendarviewer")
        kwargs["doRefresh"] = False
        super().__init__(*args, **kwargs)

        start = self.settings.get(self.settingsSection(), "viewdate")
        if start:
            dt = wx.DateTime.Now()
            dt.ParseDateTime(start)
            self.widget.SetDate(dt)

        self.onWeekStartChanged(self.settings.gettext("view", "weekstart"))
        self.onWorkingHourChanged()

        self.reconfig()
        self.widget.SetPeriodWidth(
            self.settings.getint(self.settingsSection(), "periodwidth")
        )

        for eventType in ("start", "end"):
            pub.subscribe(
                self.onWorkingHourChanged,
                "settings.view.efforthour%s" % eventType,
            )
        pub.subscribe(self.onWeekStartChanged, "settings.view.weekstartmonday")

        # pylint: disable=E1101
        for eventType in (
            task.Task.subjectChangedEventType(),
            task.Task.plannedStartDateTimeChangedEventType(),
            task.Task.dueDateTimeChangedEventType(),
            task.Task.completionDateTimeChangedEventType(),
            task.Task.attachmentsChangedEventType(),
            task.Task.notesChangedEventType(),
            task.Task.trackingChangedEventType(),
            task.Task.percentageCompleteChangedEventType(),
        ):
            # # Si tu veux savoir D’OÙ vient ce eventType None pour corriger à la source,
            # # donne le code où eventType est défini ou passé à ce constructeur,
            # # il est possible de sécuriser toute la chaîne.
            # if isinstance(eventType, str) and eventType.startswith("pubsub"):
            if eventType.startswith("pubsub"):
                pub.subscribe(self.onAttributeChanged, eventType)
            else:
                self.registerObserver(
                    self.onAttributeChanged_Deprecated, eventType
                )
        # Subscribe to global timer for midnight processing
        pub.subscribe(self._onDateChanged, "timer.date")
        pub.subscribe(
            self._onCalendarColoursChanged, "calendar.colours.changed"
        )

    def _onDateChanged(self, timestamp):
        """Handle date change from global timer."""
        self.atMidnight()

    def _onCalendarColoursChanged(self):
        self.reconfig()

    def detach(self):
        """
        Méthode appelée lors du détachement de la vue.
        """
        super().detach()
        pub.unsubscribe(self._onDateChanged, "timer.date")
        pub.unsubscribe(
            self._onCalendarColoursChanged, "calendar.colours.changed"
        )

    def isTreeViewer(self):
        """
        Indique que cette vue n'est pas une arborescence (contrairement aux autres vues héritées).
        :return: False
        """
        return False

    def onEverySecond(self, event):  # pylint: disable=W0221,W0613
        """
        Surcharge inactive : inutile ici car coûteuse en performances.
        """
        pass  # Too expensive

    def atMidnight(self):
        """
        Appelée automatiquement chaque jour à minuit.
        Met à jour la vue si elle est configurée pour afficher la date actuelle.
        """
        if not self.settings.get(self.settingsSection(), "viewdate"):
            # User has selected the "current" date/time; it may have
            # changed now
            self.SetViewType(wxSCHEDULER_TODAY)

    def onWorkingHourChanged(self, value=None):  # pylint: disable=W0613
        """
        Applique les heures de travail (début et fin) à la vue calendrier.
        Utilisé lorsque l'utilisateur modifie les paramètres.
        """
        self.widget.SetWorkHours(
            self.settings.getint("view", "efforthourstart"),
            self.settings.getint("view", "efforthourend"),
        )

    def onWeekStartChanged(self, value):
        """
        Change le jour de début de semaine dans le calendrier (lundi ou dimanche).
        :param value: 'monday' ou 'sunday'
        """
        assert value in ("monday", "sunday")
        if value == "monday":
            self.widget.SetWeekStartMonday()
        else:
            self.widget.SetWeekStartSunday()

    def createWidget(self):
        """
        Crée le widget principal (vue calendrier) avec son menu contextuel.
        Applique aussi un style de dessin personnalisé (gradient) si activé.
        :return: instance de Calendar (widgets.Calendar)
        """
        log.info(
            "CalendarViewer.createWidget : Crée le widget principal avec son menu contextuel."
        )
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        widget = widgets.Calendar(  # Est-il bien configuré ?
            self,
            self.presentation(),
            self.iconName,
            self.onSelect,
            self.onEdit,
            self.onCreate,
            self.onChangeConfig,
            itemPopupMenu,
            **self.widgetCreationKeywordArguments(),
        )

        # widget.SetDrawHeaders(
        #     True
        # )  # <- Active l'affichage des numéros de jour
        if self.settings.getboolean("calendarviewer", "gradient"):
            # If called directly, we crash with a Cairo assert failing...
            log.debug(
                "CalendarViewer.createWidget : Lance un CallAfter avec widgets.Calendar.SetDrawer et wxFancyDrawer."
            )
            # wx.CallAfter(widget.SetDrawer, wxFancyDrawer)
            wx.CallAfter(self.__safeSetDrawer, widget, wxFancyDrawer)
            log.debug(
                "CalendarViewer.createWidget : CallAfter avec widgets.Calendar.SetDrawer et wxFancyDrawer est passé ! Terminé et pass !"
            )
            # pass

        # log.info(f"CalendarViewer.createWidget : Renvoie widget à {self}.")
        return widget

    def __safeSetDrawer(self, widget, drawer):
        """Safely set the drawer on a widget, guarding against deleted C++ objects."""
        try:
            if widget:
                widget.SetDrawer(drawer)
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

        return widget

    def onChangeConfig(self):
        """
        Enregistre la largeur de période actuelle dans les paramètres après modification de la configuration.
        """
        self.settings.set(
            self.settingsSection(),
            "periodwidth",
            str(self.widget.GetPeriodWidth()),
        )

    def onEdit(self, item):
        """
        Ouvre la fenêtre d'édition d'une tâche.
        :param item: tâche à éditer
        """
        edit = uicommand.Edit(viewer=self)
        edit(item)

    def onCreate(self, dateTime, show=True):
        """
        Crée une nouvelle tâche à une date donnée.

        :param dateTime: Date/heure de début planifiée.
        :param show: Affiche la tâche après création si True.
        :return: objet uicommand.TaskNew exécuté.
        """
        plannedStartDateTime = dateTime
        dueDateTime = (
            dateTime.endOfDay()
            if dateTime == dateTime.startOfDay()
            else dateTime
        )
        create = uicommand.TaskNew(
            taskList=self.presentation(),
            settings=self.settings,
            taskKeywords=dict(
                plannedStartDateTime=plannedStartDateTime,
                dueDateTime=dueDateTime,
            ),
        )
        return create(event=None, show=show)

    def createModeToolBarUICommands(self):
        """
        Ajoute les commandes spécifiques à la vue calendrier dans la barre d’outils :
        configuration, période précédente, aujourd’hui, période suivante.
        :return: tuple de commandes UI.
        """
        return super().createModeToolBarUICommands() + (
            None,
            uicommand.CalendarViewerConfigure(viewer=self),
            uicommand.CalendarViewerPreviousPeriod(viewer=self),
            uicommand.CalendarViewerToday(viewer=self),
            uicommand.CalendarViewerNextPeriod(viewer=self),
        )

    def SetViewType(self, type_):
        """
        Définit le type de vue du calendrier (jour, semaine, mois, etc.)
        et enregistre la date affichée dans les paramètres.
        """
        self.widget.SetViewType(type_)
        dt = self.widget.GetDate()
        now = wx.DateTime.Today()
        if (dt.GetYear(), dt.GetMonth(), dt.GetDay()) == (
            now.GetYear(),
            now.GetMonth(),
            now.GetDay(),
        ):
            toSave = ""
        else:
            toSave = dt.Format()
        self.settings.set(self.settingsSection(), "viewdate", toSave)

    # We need to override these because BaseTaskTreeViewer is a tree viewer, but
    # CalendarViewer is not. There is probably a better solution...

    def isAnyItemExpandable(self):
        """
        Aucun élément n'est extensible dans une vue calendrier.
        """
        return False

    def isAnyItemCollapsable(self):
        """
        Aucun élément n'est repliable dans une vue calendrier.
        """
        return False

    def reconfig(self):
        """
        Applique la configuration de l'utilisateur à la vue :
        - Nombre de périodes affichées
        - Type et orientation de la vue
        - Affichage des tâches sans dates
        - Affichage du moment présent
        - Couleur de surbrillance
        """
        log.debug(
            "CalendarViewer.reconfig : Application de la configuration utilisateur à la vue."
        )
        self.widget.Freeze()
        try:
            self.widget.SetPeriodCount(
                self.settings.getint(self.settingsSection(), "periodcount")
            )
            self.widget.SetViewType(
                self.settings.getint(self.settingsSection(), "viewtype")
            )
            self.widget.SetStyle(
                self.settings.getint(self.settingsSection(), "vieworientation")
            )
            self.widget.SetShowNoStartDate(
                self.settings.getboolean(self.settingsSection(), "shownostart")
            )
            self.widget.SetShowNoDueDate(
                self.settings.getboolean(self.settingsSection(), "shownodue")
            )
            self.widget.SetShowUnplanned(
                self.settings.getboolean(
                    self.settingsSection(), "showunplanned"
                )
            )
            self.widget.SetShowNow(
                self.settings.getboolean(self.settingsSection(), "shownow")
            )

            hcolor = self.settings.get(
                self.settingsSection(), "highlightcolor"
            )
            if hcolor:
                highlightColor = wx.Colour(
                    *tuple([int(c) for c in hcolor.split(",")])
                )
                self.widget.SetHighlightColor(highlightColor)

            # Other month days background color
            theme = self.settings.get("window", "theme")
            if theme == "automatic":
                from taskcoachlib.application.application import (
                    detect_dark_theme,
                )

                is_dark = detect_dark_theme()
            else:
                is_dark = theme == "dark"
            section = "calendar_dark" if is_dark else "calendar_light"
            use_system = self.settings.getboolean(
                section, "other_month_bg_system"
            )
            if use_system:
                self.widget.SetOtherMonthColor(None)
            else:
                color_tuple = self.settings.getvalue(section, "other_month_bg")
                self.widget.SetOtherMonthColor(wx.Colour(*color_tuple))

            # self.widget.RefreshAllItems(0)
            self.widget.scheduleRefresh(0)
        finally:
            self.widget.Thaw()

    def configure(self):
        """
        Affiche la boîte de dialogue de configuration de la vue calendrier.
        Applique les changements si l'utilisateur clique sur OK.
        """
        dialog = CalendarConfigDialog(
            self.settings,
            self.settingsSection(),
            self,
            title=_("Calendar viewer configuration"),
        )
        dialog.CentreOnParent()
        if dialog.ShowModal() == wx.ID_OK:
            self.reconfig()

    def GetPrintout(self, settings):
        """
        Retourne un objet imprimable basé sur le contenu affiché du calendrier.

        :param settings: paramètres d'impression
        :return: objet wx.Printout
        """
        return self.widget.GetPrintout(settings)


# Ensure the following import is in your module
from taskcoachlib.patterns.metaclass import makecls

# class TaskViewer(mixin.AttachmentDropTargetMixin,  # pylint: disable=W0223
#                 mixin.SortableViewerForTasksMixin,
#                 mixin.NoteColumnMixin, mixin.AttachmentColumnMixin,
#                 base.SortableViewerWithColumns, BaseTaskTreeViewer):
# Define the TaskViewer class using the makecls function
# DynamicTaskViewerBase = makecls(mixin.AttachmentDropTargetMixin,
#                                mixin.SortableViewerForTasksMixin,
#                                mixin.NoteColumnMixin,
#                                mixin.AttachmentColumnMixin,
#                                base.SortableViewerWithColumns,
#                                BaseTaskTreeViewer)

# Set the _instance_count attribute on the dynamically created class
# DynamicTaskViewerBase._instance_count = 0


# class TaskViewer(DynamicTaskViewerBase):
class TaskViewer(
    mixin.AttachmentDropTargetMixin,
    mixin.SortableViewerForTasksMixin,
    mixin.NoteColumnMixin,
    mixin.AttachmentColumnMixin,
    base.SortableViewerWithColumns,
    BaseTaskTreeViewer,
):
    """
    Visualiseur de tâches standard dans Task Coach.

    Ce visualiseur affiche les tâches sous forme d'arborescence avec des colonnes
    personnalisables, triables et filtrables. Il permet également de gérer des
    pièces jointes, des notes, et d'effectuer du glisser-déposer pour réorganiser
    les tâches.

    Méthodes :
        __init__ (self, *args, **kwargs) : Initialise le visualiseur de tâches avec les paramètres fournis.
        activate (self) : Active le visualiseur et affiche une info-bulle pour le tri manuel.
        isTreeViewer (self) : Détermine si le visualiseur est en mode arborescence.
        curselectionIsInstanceOf (self, class_) : Vérifie si la sélection actuelle est une instance de la classe spécifiée.
        createWidget (self) : Crée le widget de l'arborescence des tâches avec des menus contextuels.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise le visualiseur de tâches avec les paramètres fournis.

        Args :
            *args :
            **kwargs :
        """
        # self._instance_count = taskcoachlib.patterns.NumberedInstances.lowestUnusedNumber(self) + 1  # pas sur !
        log.debug(
            "TaskViewer.__init__ : Initialisation, Création du Visualiseur de tâches standard."
        )
        # logging.debug(
        #     "Avec le Nombre de tâches dans le modèle: %s",
        #     len(self.presentation()),
        # )  # fait planter si self.presentation() n'est pas encore défini, mais on veut voir ce qui se passe
        # Règle de priorité pour settingsSection : si elle est déjà définie dans kwargs, on la garde, sinon on la définit à "taskviewer".
        kwargs.setdefault("settingsSection", "taskviewer")
        # Appel du constructeur de la classe parente pour initialiser les fonctionnalités de base du visualiseur.
        super().__init__(*args, **kwargs)
        log.info("MODEL IN VIEWER: %s", id(self.taskFile))
        log.warning("TaskViewer.presentation id = %s", id(self.presentation()))
        log.warning("TaskViewer.taskFile id = %s", id(self.taskFile))
        log.warning("TaskFile.tasks id = %s", id(self.taskFile.tasks()))
        logging.debug(
            "Nombre de tâches dans le modèle: %s", len(self.presentation())
        )
        # log.info("TaskViewer collection reçue: %s", self.domainObjects())  # AttributeError: 'TaskViewer' object has no attribute 'domainObjects'
        if self.isVisibleColumnByName("timeLeft"):
            self.minuteRefresher.startClock()
        pub.subscribe(
            self.onTreeListModeChanged,
            "settings.%s.treemode" % self.settingsSection(),
        )
        log.debug("TaskViewer.__init__ initialisé !")
        log.info("Visible columns TaskViewer: %s.", self.visibleColumns())
        log.debug(
            "TaskViewer.__init__ : fin d'initialisation avec Presentation objects: %s",
            list(self.presentation()),
        )

    def activate(self):
        """
        Active le visualiseur et affiche une info-bulle pour le tri manuel.

        Returns :

        """
        log.debug("TaskViewer.activate : Activation du visualiseur de tâches.")
        if hasattr(wx.GetTopLevelParent(self), "AddBalloonTip"):
            try:
                wx.GetTopLevelParent(
                    self
                ).AddBalloonTip(  # Unresolved attribute reference 'AddBalloonTip' for class 'Window'
                    self.settings,
                    "manualordering",
                    self.widget,
                    title=_("Manual ordering"),
                    getRect=lambda: wx.Rect(0, 0, 28, 16),
                    message=_(
                        """Show the "Manual ordering" column, then drag and drop items 
                    from this column to sort them arbitrarily."""
                    ),
                )
            except Exception as e:
                log.error(
                    f"TaskViewer.activate: erreur durant l'activation du visualiseur {self.__class__.__name__} et de l'affichage de l'info_bulle : {e}."
                )
        log.debug(
            "TaskViewer.activate : Visualiseur de tâches activé et info-bulle affichée si possible."
        )

    def isTreeViewer(self):
        """
        Détermine si le visualiseur est en mode arborescence.

        Returns :
            (bool) : True si mode arborescence, sinon False pour le mode liste.
        """
        # We first ask our presentation what the mode is because
        # ConfigParser.getboolean is a relatively expensive method. However,
        # when initializing, the presentation might not be created yet. So in
        # that case we get an AttributeError and we use the settings.
        try:
            log.debug(
                f"TaskViewer.isTreeViewer : Demande à la présentation si le mode est arborescence. self.presentation()={self.presentation()}."
            )
            return self.presentation().treeMode()
        except AttributeError:
            log.debug(
                f"TaskViewer.isTreeViewer : La présentation n'est pas encore créée, utilisation des paramètres. self.settings={self.settings}."
            )
            return self.settings.getboolean(self.settingsSection(), "treemode")

    def showColumn(self, column, show=True, *args, **kwargs):
        log.debug(
            "TaskViewer.showColumn : showColumn appelé pour la colonne '%s' avec show=%s.",
            column.name(),
            show,
        )
        if column.name() == "timeLeft":
            if show:
                self.minuteRefresher.startClock()
            else:
                self.minuteRefresher.stopClock()
        super().showColumn(column, show, *args, **kwargs)
        log.debug(
            "TaskViewer.showColumn : showColumn terminé pour la colonne '%s'.",
            column.name(),
        )

    def curselectionIsInstanceOf(self, class_):
        """
        Vérifie si la sélection actuelle est une instance de la classe spécifiée.

        Args :
            class_ : Classe à comparer.

        Returns :
            (bool) :
        """
        return class_ == task.Task

    def createWidget(self):
        """
        Crée le widget de l'arborescence des tâches avec des menus contextuels.

        Returns :

        """
        log.debug(
            f"TaskViewer.createWidget : Crée le widget de l'arborescence des tâches avec des menus contextuels. self={self.__class__.__name__}. "
        )
        # Création de la liste d'images utilisée par le widget (icônes des tâches, etc.). A des effets de bord car elle enregistre les indices d'icônes dans self.imageIndex.
        imageList = self.createImageList()  # Has side-effects
        # log.debug(f"TaskViewer.createWidget : Arrêt après cela : ")
        # Création des colonnes du visualiseur, avec leurs callbacks de rendu, d'édition, etc.
        self._columns = self._createColumns()
        # Création des menus contextuels pour les éléments et les colonnes du widget.
        itemPopupMenu = self.createTaskPopupMenu()
        # Création du menu contextuel pour les colonnes, avec des options de tri, de masquage, etc.
        columnPopupMenu = self.createColumnPopupMenu()
        # Enregistrement des menus contextuels pour une gestion ultérieure (par exemple, pour les mettre à jour ou les détruire).
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        log.debug("TaskViewer.createWidget : definit le widget TreeListCtrl.")
        # Création du widget principal de l'arborescence des tâches, en lui passant les colonnes, les callbacks de sélection, d'édition, de glisser-déposer, et les menus contextuels.
        widget = widgets.TreeListCtrl(
            self,
            self.columns(),
            self.onSelect,
            uicommand.Edit(viewer=self),
            uicommand.TaskDragAndDrop(
                taskList=self.presentation(), viewer=self
            ),
            itemPopupMenu,
            columnPopupMenu,
            resizeableColumn=1 if self.hasOrderingColumn() else 0,
            validateDrag=self.validateDrag,
            **self.widgetCreationKeywordArguments(),
        )
        log.debug(
            "TaskViewer.createWidget: Widget TreeListCtrl créé, configuration de l'imageList et du MainColumn."
        )
        logging.debug("Widget créé: %s", type(widget))
        # SetMainColumn is a HypertreeList function!
        # Si le visualiseur a une colonne d'ordonnancement (pour le tri manuel),
        # on la définit comme colonne principale du widget,
        # ce qui permet d'afficher les icônes de tri et de gérer le redimensionnement.
        if self.hasOrderingColumn():
            widget.SetMainColumn(
                1
            )  # SetMainColumn est une fonction d'hypertreelist !
        widget.AssignImageList(imageList)  # pylint: disable=E1101
        widget.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        widget.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        log.debug(
            f"TaskViewer.createWidget retourne widget avec {len(self.presentation())} tâches."
        )
        # wx.CallAfter(self.refresh)
        return widget

    def onBeginEdit(self, event):
        """Make sure only the non-recursive part of the subject can be
        edited inline."""
        event.Skip()
        if not self.isTreeViewer():
            # Make sure the text control only shows the non-recursive subject
            # by temporarily changing the item text into the non-recursive
            # subject. When the editing ends, we change the item text back into
            # the recursive subject. See onEndEdit.
            treeItem = event.GetItem()
            editedTask = self.widget.GetItemPyData(treeItem)  # to GetItemData?
            self.widget.SetItemText(treeItem, editedTask.subject())

    def onEndEdit(self, event):
        """Make sure only the non-recursive part of the subject can be
        edited inline."""
        event.Skip()
        if not self.isTreeViewer():
            # Restore the recursive subject. Here we don't care whether users
            # actually changed the subject. If they did, the subject will
            # be updated via the regular notification mechanism.
            treeItem = event.GetItem()
            editedTask = self.widget.GetItemPyData(treeItem)  # to GetItemData?
            self.widget.SetItemText(
                treeItem, editedTask.subject(recursive=True)
            )

    def _createColumns(self):
        """
        Crée les colonnes du visualiseur. (createWidget de TaskViewer et CheckableTaskViewer).
        Returns:

        """
        # log.debug("taskViewer._createColumns : ")
        kwargs = dict(resizeCallback=self.onResizeColumn)
        # pylint: disable=E1101,W0142
        # log.error("taskViewer._createColumns : s'arrête après ça :")
        # columns = []
        # try:
        columns = (
            [
                widgets.Column(
                    "ordering",
                    "",
                    task.Task.orderingChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self,
                        value="ordering",
                    ),
                    renderCallback=lambda task: "",
                    imageIndicesCallback=self.orderingImageIndices,
                    width=self.getColumnWidth("ordering"),
                ),
                widgets.Column(
                    "subject",
                    _("Subject"),
                    task.Task.subjectChangedEventType(),
                    task.Task.completionDateTimeChangedEventType(),
                    task.Task.actualStartDateTimeChangedEventType(),
                    task.Task.dueDateTimeChangedEventType(),
                    task.Task.plannedStartDateTimeChangedEventType(),
                    task.Task.trackingChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="subject"
                    ),
                    width=self.getColumnWidth("subject"),
                    imageIndicesCallback=self.subjectImageIndices,
                    renderCallback=self.renderSubject,
                    editCallback=self.onEditSubject,
                    editControl=inplace_editor.SubjectCtrl,
                    **kwargs,
                ),
            ]
            + [
                widgets.Column(
                    "description",
                    _("Description"),
                    task.Task.descriptionChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="description"
                    ),
                    renderCallback=lambda task: task.description(),
                    width=self.getColumnWidth("description"),
                    editCallback=self.onEditDescription,
                    editControl=inplace_editor.DescriptionCtrl,
                    **kwargs,
                )
            ]
            + [
                widgets.Column(
                    "attachments",
                    _("Attachments"),
                    task.Task.attachmentsChangedEventType(),
                    width=self.getColumnWidth("attachments"),
                    alignment=wx.LIST_FORMAT_LEFT,
                    imageIndicesCallback=self.attachmentImageIndices,
                    headerImageIndex=self.imageIndex["paperclip_icon"],
                    renderCallback=lambda task: "",
                    **kwargs,
                )
            ]
        )
        # except Exception as e:
        #     log.exception(
        #         f"TaskViewer._createColumns : erreur : {e}", exc_info=True
        #     )
        # log.warning("taskViewer._createColumns : But : ARRIVER ICI !")
        columns.append(
            widgets.Column(
                "notes",
                _("Notes"),
                task.Task.notesChangedEventType(),
                width=self.getColumnWidth("notes"),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndicesCallback=self.noteImageIndices,
                headerImageIndex=self.imageIndex["note_icon"],
                renderCallback=lambda task: "",
                **kwargs,
            )
        )
        columns.extend(
            [
                widgets.Column(
                    "categories",
                    _("Categories"),
                    task.Task.categoryAddedEventType(),
                    task.Task.categoryRemovedEventType(),
                    task.Task.categorySubjectChangedEventType(),
                    task.Task.expansionChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="categories"
                    ),
                    width=self.getColumnWidth("categories"),
                    renderCallback=self.renderCategories,
                    **kwargs,
                ),
                widgets.Column(
                    "prerequisites",
                    _("Prerequisites"),
                    task.Task.prerequisitesChangedEventType(),
                    task.Task.expansionChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="prerequisites"
                    ),
                    renderCallback=self.renderPrerequisites,
                    width=self.getColumnWidth("prerequisites"),
                    **kwargs,
                ),
                widgets.Column(
                    "dependencies",
                    _("Dependents"),
                    task.Task.dependenciesChangedEventType(),
                    task.Task.expansionChangedEventType(),
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value="dependencies"
                    ),
                    renderCallback=self.renderDependencies,
                    width=self.getColumnWidth("dependencies"),
                    **kwargs,
                ),
            ]
        )

        for name, columnHeader, editCtrl, editCallback, eventTypes in [
            (
                "plannedStartDateTime",
                _("Planned start date"),  # TODO : Date ou date ?
                inplace_editor.DateTimeCtrl,
                self.onEditPlannedStartDateTime,
                [],
            ),
            (
                "dueDateTime",
                _("Due date"),
                DueDateTimeCtrl,
                self.onEditDueDateTime,
                [task.Task.expansionChangedEventType()],
            ),
            (
                "actualStartDateTime",
                _("Actual start date"),
                inplace_editor.DateTimeCtrl,
                self.onEditActualStartDateTime,
                [task.Task.expansionChangedEventType()],
            ),
            (
                "completionDateTime",
                _("Completion date"),
                inplace_editor.DateTimeCtrl,
                self.onEditCompletionDateTime,
                [task.Task.expansionChangedEventType()],
            ),
        ]:
            # renderCallback = getattr(
            #     self, "render%s" % (name[0].capitalize() + name[1:])
            # )
            renderCallback = getattr(
                self, f"render{name[0].capitalize() + name[1:]}"
            )
            # renderCallback = getattr(
            #     self, f"render{name[0].capitalize()}{name[1:]}"
            # )
            columns.append(
                widgets.Column(
                    name,
                    columnHeader,
                    sortCallback=uicommand.ViewerSortByCommand(
                        viewer=self, value=name
                    ),
                    renderCallback=renderCallback,
                    width=self.getColumnWidth(name),
                    alignment=wx.LIST_FORMAT_RIGHT,
                    editControl=editCtrl,
                    editCallback=editCallback,
                    settings=self.settings,
                    *eventTypes,
                    **kwargs,
                )
            )

        # Status columns (derived from dates, updated by scheduler)
        columns.append(
            widgets.Column(
                "status",
                _("Status"),
                task.Task.statusChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="status"
                ),
                renderCallback=lambda task: task.statusText(),
                width=self.getColumnWidth("status"),
                **kwargs,
            )
        )
        columns.append(
            widgets.Column(
                "statusIcon",
                _("Status icon"),
                task.Task.statusChangedEventType(),
                width=self.getColumnWidth("statusIcon"),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndicesCallback=self.statusImageIndices,
                renderCallback=lambda task: "",
                **kwargs,
            )
        )
        columns.append(
            widgets.Column(
                "statusIconText",
                _("Status combo"),
                task.Task.statusChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="status"
                ),
                renderCallback=lambda task: task.statusText(),
                width=self.getColumnWidth("statusIconText"),
                imageIndicesCallback=self.statusImageIndices,
                **kwargs,
            )
        )

        dependsOnEffortFeature = [
            "budget",
            "timeSpent",
            "budgetLeft",
            "hourlyFee",
            "fixedFee",
            "revenue",
        ]

        for name, columnHeader, editCtrl, editCallback, eventTypes in [
            (
                "percentageComplete",
                _("% complete"),
                inplace_editor.PercentageCtrl,
                self.onEditPercentageComplete,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.percentageCompleteChangedEventType(),
                ],
            ),
            (
                "timeLeft",
                _("Time left"),
                None,
                None,
                [task.Task.expansionChangedEventType(), "task.timeLeft"],
            ),
            (
                "recurrence",
                _("Recurrence"),
                None,
                None,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.recurrenceChangedEventType(),
                ],
            ),
            (
                "budget",
                _("Budget"),
                inplace_editor.BudgetCtrl,
                self.onEditBudget,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.budgetChangedEventType(),
                ],
            ),
            (
                "timeSpent",
                _("Time spent"),
                None,
                None,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.timeSpentChangedEventType(),
                ],
            ),
            (
                "budgetLeft",
                _("Budget left"),
                None,
                None,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.budgetLeftChangedEventType(),
                ],
            ),
            (
                "priority",
                _("Priority"),
                inplace_editor.PriorityCtrl,
                self.onEditPriority,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.priorityChangedEventType(),
                ],
            ),
            (
                "hourlyFee",
                _("Hourly fee"),
                inplace_editor.AmountCtrl,
                self.onEditHourlyFee,
                [task.Task.hourlyFeeChangedEventType()],
            ),
            (
                "fixedFee",
                _("Fixed fee"),
                inplace_editor.AmountCtrl,
                self.onEditFixedFee,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.fixedFeeChangedEventType(),
                ],
            ),
            (
                "revenue",
                _("Revenue"),
                None,
                None,
                [
                    task.Task.expansionChangedEventType(),
                    task.Task.revenueChangedEventType(),
                ],
            ),
        ]:
            if (
                name in dependsOnEffortFeature
            ) or name not in dependsOnEffortFeature:
                # renderCallback = getattr(
                #     self, "render%s" % (name[0].capitalize() + name[1:])
                # )
                renderCallback = getattr(
                    self, f"render{name[0].capitalize() + name[1:]}"
                )
                columns.append(
                    widgets.Column(
                        name,
                        columnHeader,
                        sortCallback=uicommand.ViewerSortByCommand(
                            viewer=self, value=name
                        ),
                        renderCallback=renderCallback,
                        width=self.getColumnWidth(name),
                        alignment=wx.LIST_FORMAT_RIGHT,
                        editControl=editCtrl,
                        editCallback=editCallback,
                        *eventTypes,
                        **kwargs,
                    )
                )

        columns.append(
            widgets.Column(
                "reminder",
                _("Reminder"),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="reminder"
                ),
                renderCallback=self.renderReminder,
                width=self.getColumnWidth("reminder"),
                alignment=wx.LIST_FORMAT_RIGHT,
                editControl=inplace_editor.DateTimeCtrl,
                editCallback=self.onEditReminderDateTime,
                settings=self.settings,
                *[
                    task.Task.expansionChangedEventType(),
                    task.Task.reminderChangedEventType(),
                ],
                **kwargs,
            )
        )
        columns.append(
            widgets.Column(
                "creationDateTime",
                _("Creation date"),
                width=self.getColumnWidth("creationDateTime"),
                renderCallback=self.renderCreationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="creationDateTime"
                ),
                **kwargs,
            )
        )
        columns.append(
            widgets.Column(
                "modificationDateTime",
                _("Modification date"),
                width=self.getColumnWidth("modificationDateTime"),
                renderCallback=self.renderModificationDateTime,
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="modificationDateTime"
                ),
                *task.Task.modificationEventTypes(),
                **kwargs,
            )
        )
        columns.append(
            widgets.Column(
                "id",
                _("ID"),
                width=self.getColumnWidth("id"),
                renderCallback=lambda task: task.id(),
                sortCallback=uicommand.ViewerSortByCommand(
                    viewer=self, value="id"
                ),
                **kwargs,
            )
        )
        log.debug(f"TaskViewer._createColumns retourne columns {columns}.")
        # log.debug(f"TaskViewer._createColumns retourne columns.")
        return columns

    def createColumnUICommands(self):
        """
        Crée les commandes de l'interface utilisateur pour gérer les colonnes.
        (overwrite de la méthode de gui.viewer.base.ViewerWithColumns.createColumnUICommands).
        Raises :
            NotImplementedError : Si non implémenté dans une sous-classe.
        """
        commands = [
            uicommand.ToggleAutoColumnResizing(
                viewer=self, settings=self.settings
            ),
            None,
            (
                _("&Dates"),
                uicommand.ViewColumns(
                    menuText=_("&All date columns"),
                    helpText=_("Show/hide all date-related columns"),
                    setting=[
                        "plannedStartDateTime",
                        "dueDateTime",
                        "timeLeft",
                        "actualStartDateTime",
                        "completionDateTime",
                        "recurrence",
                        "status",
                        "statusIcon",
                        "statusIconText",
                    ],
                    viewer=self,
                ),
                None,
                uicommand.ViewColumn(
                    menuText=_("&Planned start date"),
                    helpText=_("Show/hide planned start date column"),
                    setting="plannedStartDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Due date"),
                    helpText=_("Show/hide due date column"),
                    setting="dueDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Actual start date"),
                    helpText=_("Show/hide actual start date column"),
                    setting="actualStartDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Completion date"),
                    helpText=_("Show/hide completion date column"),
                    setting="completionDateTime",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Time left"),
                    helpText=_("Show/hide time left column"),
                    setting="timeLeft",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Recurrence"),
                    helpText=_("Show/hide recurrence column"),
                    setting="recurrence",
                    viewer=self,
                ),
                None,
                uicommand.ViewColumn(
                    menuText=_("&Status"),
                    helpText=_("Show/hide status text column"),
                    setting="status",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("Status &icon"),
                    helpText=_("Show/hide status icon column"),
                    setting="statusIcon",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("Status &combo"),
                    helpText=_(
                        "Show/hide status combo column (icon and text)"
                    ),
                    setting="statusIconText",
                    viewer=self,
                ),
            ),
        ]
        commands.extend(
            [
                (
                    _("&Budget"),
                    uicommand.ViewColumns(
                        menuText=_("&All budget columns"),
                        helpText=_("Show/hide all budget-related columns"),
                        setting=["budget", "timeSpent", "budgetLeft"],
                        viewer=self,
                    ),
                    None,
                    uicommand.ViewColumn(
                        menuText=_("&Budget"),
                        helpText=_("Show/hide budget column"),
                        setting="budget",
                        viewer=self,
                    ),
                    uicommand.ViewColumn(
                        menuText=_("&Time spent"),
                        helpText=_("Show/hide time spent column"),
                        setting="timeSpent",
                        viewer=self,
                    ),
                    uicommand.ViewColumn(
                        menuText=_("&Budget left"),
                        helpText=_("Show/hide budget left column"),
                        setting="budgetLeft",
                        viewer=self,
                    ),
                ),
                (
                    _("&Financial"),
                    uicommand.ViewColumns(
                        menuText=_("&All financial columns"),
                        helpText=_("Show/hide all finance-related columns"),
                        setting=["hourlyFee", "fixedFee", "revenue"],
                        viewer=self,
                    ),
                    None,
                    uicommand.ViewColumn(
                        menuText=_("&Hourly fee"),
                        helpText=_("Show/hide hourly fee column"),
                        setting="hourlyFee",
                        viewer=self,
                    ),
                    uicommand.ViewColumn(
                        menuText=_("&Fixed fee"),
                        helpText=_("Show/hide fixed fee column"),
                        setting="fixedFee",
                        viewer=self,
                    ),
                    uicommand.ViewColumn(
                        menuText=_("&Revenue"),
                        helpText=_("Show/hide revenue column"),
                        setting="revenue",
                        viewer=self,
                    ),
                ),
            ]
        )
        commands.extend(
            [
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
                    menuText=_("&Prerequisites"),
                    helpText=_("Show/hide prerequisites column"),
                    setting="prerequisites",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Dependents"),
                    helpText=_("Show/hide dependents column"),
                    setting="dependencies",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Percentage complete"),
                    helpText=_("Show/hide percentage complete column"),
                    setting="percentageComplete",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Attachments"),
                    helpText=_("Show/hide attachment column"),
                    setting="attachments",
                    viewer=self,
                ),
            ]
        )
        commands.append(
            uicommand.ViewColumn(
                menuText=_("&Notes"),
                helpText=_("Show/hide notes column"),
                setting="notes",
                viewer=self,
            )
        )
        commands.extend(
            [
                uicommand.ViewColumn(
                    menuText=_("&Categories"),
                    helpText=_("Show/hide categories column"),
                    setting="categories",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Priority"),
                    helpText=_("Show/hide priority column"),
                    setting="priority",
                    viewer=self,
                ),
                uicommand.ViewColumn(
                    menuText=_("&Reminder"),
                    helpText=_("Show/hide reminder column"),
                    setting="reminder",
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
                uicommand.ViewColumn(
                    menuText=_("&ID"),
                    helpText=_("Show/hide ID column"),
                    setting="id",
                    viewer=self,
                ),
            ]
        )
        return commands

    def createModeToolBarUICommands(self):
        """Crée des commandes UI pour la barre d'outils (modes)."""
        treeOrListUICommand = uicommand.TaskViewerTreeOrListChoice(
            viewer=self, settings=self.settings
        )  # pylint: disable=W0201
        return super().createModeToolBarUICommands() + (treeOrListUICommand,)

    def hasModes(self):
        return True

    def getModeUICommands(self):
        return [_("Show tasks as"), None] + [
            uicommand.TaskViewerTreeOrListOption(
                menuText=menuText,
                value=value,
                viewer=self,
                settings=self.settings,
            )
            for (menuText, value) in zip(
                uicommand.TaskViewerTreeOrListChoice.choiceLabels,
                uicommand.TaskViewerTreeOrListChoice.choiceData,
            )
        ]

    def createColumnPopupMenu(self):
        return taskcoachlib.gui.menu.ColumnPopupMenu(self)
        # from taskcoachlib.gui.menu import ColumnPopupMenu
        # return ColumnPopupMenu(self)

    def setSortByTaskStatusFirst(
        self, *args, **kwargs
    ):  # pylint: disable=W0221
        super().setSortByTaskStatusFirst(*args, **kwargs)
        self.showSortOrder()

    def getSortOrderImage(self):
        sortOrderImage = super().getSortOrderImage()
        if self.isSortByTaskStatusFirst():  # pylint: disable=E1101
            sortOrderImage = sortOrderImage.rstrip("icon") + "with_status_icon"
        return sortOrderImage

    def setSearchFilter(
        self, searchString, *args, **kwargs
    ):  # pylint: disable=W0221
        super().setSearchFilter(searchString, *args, **kwargs)
        if searchString:
            self.expandAll()  # pylint: disable=E1101

    def onTreeListModeChanged(self, value):
        self.presentation().setTreeMode(value)

    # pylint: disable=W0621

    def renderSubject(self, task):
        # return task.subject(recursive=not self.isTreeViewer())
        subject_to_return = task.subject(recursive=not self.isTreeViewer())
        log.debug(
            f"TaskViewer.renderSubject : Retourne {subject_to_return} pour task={task}"
        )
        return subject_to_return

    def renderPlannedStartDateTime(self, task, humanReadable=True):
        return self.renderedValue(
            task,
            task.plannedStartDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderDueDateTime(self, task, humanReadable=True):
        return self.renderedValue(
            task,
            task.dueDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderActualStartDateTime(self, task, humanReadable=True):
        return self.renderedValue(
            task,
            task.actualStartDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderCompletionDateTime(self, task, humanReadable=True):
        return self.renderedValue(
            task,
            task.completionDateTime,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderRecurrence(self, task):
        return self.renderedValue(task, task.recurrence, render.recurrence)

    def renderPrerequisites(self, task):
        return self.renderSubjectsOfRelatedItems(task, task.prerequisites)

    def renderDependencies(self, task):
        return self.renderSubjectsOfRelatedItems(task, task.dependencies)

    def renderTimeLeft(self, task):
        return self.renderedValue(
            task, task.timeLeft, render.timeLeft, task.completed()
        )

    def renderTimeSpent(self, task):
        return self.renderedValue(task, task.timeSpent, self._renderTimeSpent)

    def renderBudget(self, task):
        return self.renderedValue(task, task.budget, render.budget)

    def renderBudgetLeft(self, task):
        return self.renderedValue(task, task.budgetLeft, render.budget)

    def renderRevenue(self, task):
        return self.renderedValue(task, task.revenue, render.monetaryAmount)

    # @staticmethod
    def renderHourlyFee(self, task):
        # hourlyFee has no recursive value
        return render.monetaryAmount(task.hourlyFee())

    def renderFixedFee(self, task):
        return self.renderedValue(task, task.fixedFee, render.monetaryAmount)

    def renderPercentageComplete(self, task):
        return self.renderedValue(
            task, task.percentageComplete, render.percentage
        )

    def renderPriority(self, task):
        return self.renderedValue(task, task.priority, render.priority) + " "

    def renderReminder(self, task, humanReadable=True):
        return self.renderedValue(
            task,
            task.reminder,
            lambda x: render.dateTime(x, humanReadable=humanReadable),
        )

    def renderedValue(self, item, getValue, renderValue, *extraRenderArgs):
        value = getValue(recursive=False)
        template = "%s"
        if self.isItemCollapsed(item):
            recursiveValue = getValue(recursive=True)
            if value != recursiveValue:
                value = recursiveValue
                template = "(%s)"
        return template % renderValue(value, *extraRenderArgs)

    def statusImageIndices(self, task):
        """Return image index for the task's current status icon."""
        iconName = task.statusIconName()
        index = self.imageIndex.get(iconName, -1)
        return {wx.TreeItemIcon_Normal: index}

    def onEditPlannedStartDateTime(self, item, newValue):
        keep_delta = self.settings.get("view", "datestied") == "startdue"
        command.EditPlannedStartDateTimeCommand(
            items=[item], newValue=newValue, keep_delta=keep_delta
        ).do()

    def onEditDueDateTime(self, item, newValue):
        keep_delta = self.settings.get("view", "datestied") == "duestart"
        command.EditDueDateTimeCommand(
            items=[item], newValue=newValue, keep_delta=keep_delta
        ).do()

    # @staticmethod
    def onEditActualStartDateTime(self, item, newValue):
        command.EditActualStartDateTimeCommand(
            items=[item], newValue=newValue
        ).do()

    # @staticmethod
    def onEditCompletionDateTime(self, item, newValue):
        command.EditCompletionDateTimeCommand(
            items=[item], newValue=newValue
        ).do()

    # @staticmethod
    def onEditPercentageComplete(self, item, newValue):
        command.EditPercentageCompleteCommand(
            items=[item], newValue=newValue
        ).do()  # pylint: disable=E1101

    # @staticmethod
    def onEditBudget(self, item, newValue):
        command.EditBudgetCommand(items=[item], newValue=newValue).do()

    # @staticmethod
    def onEditPriority(self, item, newValue):
        command.EditPriorityCommand(items=[item], newValue=newValue).do()

    # @staticmethod
    def onEditReminderDateTime(self, item, newValue):
        command.EditReminderDateTimeCommand(
            items=[item], newValue=newValue
        ).do()

    # @staticmethod
    def onEditHourlyFee(self, item, newValue):
        command.EditHourlyFeeCommand(items=[item], newValue=newValue).do()

    # @staticmethod
    def onEditFixedFee(self, item, newValue):
        command.EditFixedFeeCommand(items=[item], newValue=newValue).do()

    def onEverySecond(self, event):
        # Only update when a column is visible that changes every second
        if any(
            [
                self.isVisibleColumnByName(column)
                for column in ("timeSpent", "budgetLeft", "revenue")
            ]
        ):
            super().onEverySecond(event)

    def getRootItems(self):
        """If the viewer is in tree mode, return the real root items. If the
        viewer is in list mode, return all items."""
        log.debug(
            f"TaskViewer.getRootItems : self.presentation() = {self.presentation()}"
        )
        # return (
        #     # Si tree mode, on retourne les items racines de la présentation, qui sont les vrais items racines
        #     super().getRootItems()
        #     if self.isTreeViewer()
        #     # Si list mode, on retourne les items racines de la présentation, qui sont tous les items (car en list mode, tous les items sont des racines)
        #     else self.presentation()
        #     # else self.presentation().rootItems()
        #     # else self.presentation().allItems(recursive=True)
        #     # else self.presentation().getRootItems()  # ?
        # )
        rootItems_to_return = (
            super().getRootItems()
            if self.isTreeViewer()
            else self.presentation()
        )
        log.debug(f"TaskViewer.getRootItems : Retourne {rootItems_to_return}.")
        return rootItems_to_return

    def getItemParent(self, item):
        return super().getItemParent(item) if self.isTreeViewer() else None

    def children(
        self, item=None
    ):  # TODO : le mot children est utilisé dans tkinter pour les fenêtre !
        """Retourne les enfants d'un élément selon le mode arbre/liste."""
        log.debug(
            f"TaskViewer.children : item={item}, self.isTreeViewer()={self.isTreeViewer()}"
        )
        # return (
        #     super().children(item)
        #     if (self.isTreeViewer() or item is None)
        #     else []
        # )
        result = (
            super().children(item)
            if (self.isTreeViewer() or item is None)
            else []
        )
        log.debug(f"TaskViewer.children(item={item}) retourne {result}")
        return result

    # def getItemText(self, task):
    #     return task.subject()


class CheckableTaskViewer(TaskViewer):  # pylint: disable=W0223
    """
    Visualiseur de tâches avec cases à cocher.

    Ce visualiseur permet de cocher ou décocher des tâches dans une arborescence.
    Il étend le `TaskViewer` en ajoutant des fonctionnalités liées à la gestion
    des cases à cocher pour chaque tâche.

    Méthodes :
        createWidget (self) : Crée le widget d'affichage avec des cases à cocher pour les tâches.
        onCheck (self, event, final) : Gère les événements liés au changement d'état des cases à cocher.
        getIsItemChecked (self, task) : Vérifie si une tâche est cochée.
        getItemParentHasExclusiveChildren (self, task) : Vérifie si une tâche parent a des enfants exclusifs.
    """

    def createWidget(self):
        imageList = self.createImageList()  # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = self.createTaskPopupMenu()
        columnPopupMenu = self.createColumnPopupMenu()
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        log.debug(
            f"CheckableTaskViewer.createWidget : self.columns() = {self.columns()}"
        )
        widget = widgets.CheckTreeCtrl(
            self,
            self.columns(),
            self.onSelect,
            self.onCheck,
            uicommand.Edit(viewer=self),
            uicommand.TaskDragAndDrop(
                taskList=self.presentation(), viewer=self
            ),
            itemPopupMenu,
            columnPopupMenu,
            **self.widgetCreationKeywordArguments(),
        )
        widget.AssignImageList(
            imageList
        )  # pylint: disable=E1101  Parameter 'which' unfilled
        # widget.AssignImageList(imageList, wx.IMAGE_LIST_NORMAL)  # pylint: disable=E1101
        return widget

    def onCheck(self, event, final):
        pass

    def getIsItemChecked(self, task):  # pylint: disable=W0613,W0621
        return False

    # @staticmethod
    def getItemParentHasExclusiveChildren(
        self, task
    ):  # pylint: disable=W0613,W0621
        # Ces deux méthodes (getItemParentHasExclusiveChildren et getIsItemChecked) sont des méthodes du viewer/adaptateur, pas du widget. Toutes les fois que CheckTreeCtrl doit interroger le viewer pour l'état d'un objet, il doit passer par self._TreeListCtrl__adapter.
        return False


class TaskStatsViewer(BaseTaskViewer):  # pylint: disable=W0223
    """
    Visualiseur de statistiques sur les tâches.

    Ce visualiseur affiche des statistiques sous forme de diagrammes circulaires
    et autres graphiques, basées sur le statut des tâches (en retard, complétées, etc.).

    Méthodes :
        __init__(self, *args, **kwargs) : Initialise le visualiseur de statistiques avec les paramètres par défaut.
        createWidget(self) : Crée le widget de diagramme circulaire pour afficher les statistiques.
        initLegend(self, widget) : Initialise la légende du diagramme.
        refresh(self) : Rafraîchit l'affichage du diagramme circulaire en fonction des paramètres actuels.
    """

    defaultTitle = _("Task statistics")
    defaultBitmap = "charts_icon"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("settingsSection", "taskstatsviewer")
        super().__init__(*args, **kwargs)
        pub.subscribe(
            self.onPieChartAngleChanged,
            "settings.%s.piechartangle" % self.settingsSection(),
        )

    def createWidget(self):
        widget = wx.lib.agw.piectrl.PieCtrl(self)
        widget.SetShowEdges(False)
        widget.SetHeight(20)
        self.initLegend(widget)
        for dummy in task.Task.possibleStatuses():
            widget._series.append(
                wx.lib.agw.piectrl.PiePart(1)
            )  # pylint: disable=W0212
        return widget

    def createClipboardToolBarUICommands(self):
        return ()

    def createEditToolBarUICommands(self):
        return ()

    def createCreationToolBarUICommands(self):
        log.debug(
            f"TaskStatsViewer.createCreationToolBarUICommands : self.presentation() = {self.presentation()}"
        )
        return (
            uicommand.TaskNew(
                taskList=self.presentation(), settings=self.settings
            ),
            uicommand.TaskNewFromTemplateButton(
                taskList=self.presentation(),
                settings=self.settings,
                bitmap="newtmpl",
            ),
        )

    def createActionToolBarUICommands(self):
        return tuple(
            [
                uicommand.ViewerHideTasks(
                    taskStatus=status, settings=self.settings, viewer=self
                )
                for status in task.Task.possibleStatuses()
            ]
        ) + (
            uicommand.ViewerPieChartAngle(viewer=self, settings=self.settings),
        )

    # @staticmethod
    def initLegend(self, widget):
        legend = widget.GetLegend()
        legend.SetTransparent(False)
        legend.SetBackColour(wx.WHITE)
        legend.SetLabelFont(wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT))
        legend.Show()

    def refresh(self):
        self.widget.SetAngle(
            self.settings.getint(self.settingsSection(), "piechartangle")
            / 180.0
            * math.pi
        )
        self.refreshParts()
        self.widget.Refresh()

    def refreshParts(self):
        log.debug(
            f"TaskStatsViewer.refreshParts : self.presentation() = {self.presentation()}"
        )
        series = self.widget._series  # pylint: disable=W0212
        tasks = self.presentation()
        total = len(tasks)
        counts = tasks.nrOfTasksPerStatus()
        for part, status in zip(series, task.Task.possibleStatuses()):
            nrTasks = counts[status]
            percentage = round(100.0 * nrTasks // total) if total else 0
            part.SetLabel(status.countLabel % (nrTasks, percentage))
            part.SetValue(nrTasks)
            part.SetColour(self.getFgColor(status))
        # PietCtrl can't handle empty pie charts:
        if total == 0:
            series[0].SetValue(1)

    def getFgColor(self, status):
        try:
            theme = self.settings.get("window", "theme")
            if theme == "automatic":
                from taskcoachlib.application.application import (
                    detect_dark_theme,
                )

                is_dark = detect_dark_theme()
            else:
                is_dark = theme == "dark"
            section = "fgcolor_dark" if is_dark else "fgcolor"
        except Exception:
            section = "fgcolor"
        # color = wx.Colour(
        #     *eval(self.settings.get("fgcolor", "%stasks" % status))
        # )
        color = wx.Colour(
            *ast.literal_eval(self.settings.get(section, "%stasks" % status))
        )
        if status == task.status.active and color == wx.BLACK:
            color = wx.BLUE
        return color

    def refreshItems(self, *args, **kwargs):  # pylint: disable=W0613
        self.refresh()

    def select(self, *args):
        pass

    def updateSelection(self, *args, **kwargs):
        pass

    def isTreeViewer(self):
        return False

    def onPieChartAngleChanged(self, value):  # pylint: disable=W0613
        self.refresh()


try:
    import igraph
except ImportError:
    pass
else:

    class TaskInterdepsViewer(BaseTaskViewer):
        # defaultTitle = _("Tasks Interdependencies")
        defaultTitle = "Tasks Interdependencies"
        # defaultBitmap = _("graph_icon")
        defaultBitmap = "graph_icon"

        graphFile = tempfile.NamedTemporaryFile(suffix=".png")

        def __init__(self, *args, **kwargs):
            kwargs.setdefault("settingsSection", "taskinterdepsviewer")
            self._needsUpdate = False  # refresh called from parent constructor
            self._updating = False
            super().__init__(*args, **kwargs)

            pub.subscribe(
                self.onAttributeChanged,
                task.Task.dependenciesChangedEventType(),
            )
            pub.subscribe(
                self.onAttributeChanged,
                task.Task.prerequisitesChangedEventType(),
            )

        def createWidget(self):
            # self.scrolled_panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
            self.scrolled_panel = ScrolledPanel(self, -1)

            self.vbox = wx.BoxSizer(wx.VERTICAL)
            self.hbox = wx.BoxSizer(wx.HORIZONTAL)
            self.vbox.Add(self.hbox, 0, wx.ALIGN_CENTRE)
            self.scrolled_panel.SetSizer(self.vbox)

            graph, visual_style = self.form_depend_graph()
            if graph.get_edgelist():
                igraph.plot(graph, self.graphFile.name, **visual_style)
                bitmap = wx.Image(
                    self.graphFile.name, wx.BITMAP_TYPE_ANY
                ).ConvertToBitmap()
            else:
                bitmap = wx.NullBitmap
            graph_png_bm = wx.StaticBitmap(
                self.scrolled_panel, wx.ID_ANY, bitmap
            )

            self.hbox.Add(graph_png_bm, 1, wx.ALL, 3)
            self.scrolled_panel.SetupScrolling()

            return self.scrolled_panel

        def createClipboardToolBarUICommands(self):
            return ()

        def createEditToolBarUICommands(self):
            return ()

        def createCreationToolBarUICommands(self):
            return ()

        def createActionToolBarUICommands(self):
            return tuple(
                [
                    uicommand.ViewerHideTasks(
                        taskStatus=status, settings=self.settings, viewer=self
                    )
                    for status in task.Task.possibleStatuses()
                ]
            )

        # @staticmethod
        def initLegend(self, widget):
            legend = widget.GetLegend()
            legend.Show()

        @staticmethod
        def determine_vertex_weight(budget, priority):
            budg_h = budget.total_seconds() // 3600
            return (budg_h + priority * (budg_h + 1) + 10) % 200

        @staticmethod
        def convert_rgba_to_rgb(rgba):
            # rgb = (rgba[0], rgba[1], rgba[2])
            # return "#" + struct.pack("BBB", *rgb).decode(  # encode ?
            #     "hex"
            # )  # unresolved attribute reference encode for class bytes
            # return "#%02x%02x%02x" % (rgba[0], rgba[1], rgba[2])
            return f"#{rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}"

        def form_depend_graph(self):
            vertices = dict()  # task => (weight, color)
            edges = set()  # of 2-tuples (task, task)

            def addVertex(tsk):
                if tsk not in vertices:
                    vertices[tsk] = (
                        self.determine_vertex_weight(
                            tsk.budget(), tsk.priority()
                        ),
                        self.convert_rgba_to_rgb(
                            task.foregroundColor(recursive=True)
                        ),
                    )

            log.debug(
                f"TaskInterdepsViewer.form_depend_graph : self.presentation() = {self.presentation()}"
            )
            for task in self.presentation():
                if task.prerequisites():
                    addVertex(task)
                    for prereq in task.prerequisites():
                        addVertex(prereq)
                        edges.add((prereq, task))

            vertices = list(sorted(vertices.items()))
            vertices_w = [weight for task, (weight, color) in vertices]
            vertices_col = [color for task, (weight, color) in vertices]
            vertices = [task for task, (weight, color) in vertices]
            edges = sorted(
                [
                    (vertices.index(task0), vertices.index(task1))
                    for (task0, task1) in edges
                ]
            )
            vertices = [task.subject() for task in vertices]

            graph = igraph.Graph(
                vertex_attrs={"label": vertices}, edges=edges, directed=True
            )
            graph.topological_sorting(mode=igraph.OUT)
            visual_style = {}
            visual_style["vertex_color"] = vertices_col
            visual_style["edge_width"] = [3 for x in graph.es]
            visual_style["margin"] = 70
            visual_style["edge_curved"] = True
            graph.vs["label_dist"] = 1

            # weighted vertex
            indegree = graph.degree(type="in")
            if indegree:
                max_i_degree = max(indegree)
            visual_style["vertex_size"] = [
                (i_deg / max_i_degree) * 20 + vert_w
                for i_deg, vert_w in zip(indegree, vertices_w)
            ]

            return graph, visual_style

        def getFgColor(self, status):
            try:
                theme = self.settings.get("window", "theme")
                if theme == "automatic":
                    from taskcoachlib.application.application import (
                        detect_dark_theme,
                    )

                    is_dark = detect_dark_theme()
                else:
                    is_dark = theme == "dark"
                section = "fgcolor_dark" if is_dark else "fgcolor"
            except Exception:
                section = "fgcolor"
            color = wx.Colour(
                # *eval(self.settings.get("fgcolor", "%stasks" % status))
                *ast.literal_eval(
                    self.settings.get(section, "%stasks" % status)
                )
            )
            if status == task.status.active and color == wx.BLACK:
                color = wx.BLUE
            return color

        def select(self, *args):
            pass

        def updateSelection(self, *args, **kwargs):
            pass

        def isTreeViewer(self):
            return False

        def refreshItems(self, *items):
            self.refresh()

        def refresh(self):
            if not self._needsUpdate:
                self._needsUpdate = True
                if not self._updating:
                    self._refresh()

        # @inlineCallbacks
        def _refresh(self):
            """
            Refresh the graph visualization asynchronously.

            DESIGN NOTE (Twisted Removal - 2024):
            Previously used @inlineCallbacks and deferToThread from Twisted.
            Now uses concurrent.futures.ThreadPoolExecutor with wx.CallAfter
            for thread-safe GUI updates. This maintains the same async behavior
            without requiring the Twisted reactor.
            """
            log.debug(
                f"TaskInterdepsViewer._refresh : Starting refresh. _needsUpdate={self._needsUpdate}, _updating={self._updating}"
            )
            bitmap = None
            while self._needsUpdate:
                # Compute this in main thread because of concurrent access issues
                graph, visual_style = self.form_depend_graph()
                self._needsUpdate = False  # Any new refresh starting here should trigger a new iteration

                # Only proceed with plotting if there are edges to display
                if graph.get_edgelist():
                    self._updating = True
                    # Use ThreadPoolExecutor for background thread execution
                    executor = ThreadPoolExecutor(max_workers=1)

                    # try:
                    #     # yield deferToThread(
                    #     #     igraph.plot,
                    #     #     graph,
                    #     #     self.graphFile.name,
                    #     #     **visual_style,
                    #     # )
                    # finally:
                    #     self._updating = False
                    def do_plot():
                        try:
                            igraph.plot(
                                graph, self.graphFile.name, **visual_style
                            )
                        except Exception as e:
                            logging.error(
                                f"Erreur lors du rendu des tâches: {e}"
                            )
                            raise
                        finally:
                            self._updating = False
                        return True

                    # bitmap = wx.Image(
                    #     self.graphFile.name, wx.BITMAP_TYPE_ANY
                    # ).ConvertToBitmap()
                    def on_plot_complete(future):
                        try:
                            future.result()  # Check for exceptions
                            bitmap = wx.Image(
                                self.graphFile.name, wx.BITMAP_TYPE_ANY
                            ).ConvertToBitmap()
                        except Exception:
                            bitmap = wx.NullBitmap

                        # Update GUI in main thread
                        def update_gui():
                            if self._needsUpdate:
                                # Another refresh was requested, recurse
                                self._refresh()
                            else:
                                self._finish_refresh(bitmap)

                        wx.CallAfter(update_gui)

                    future = executor.submit(do_plot)
                    future.add_done_callback(on_plot_complete)
                    log.debug(
                        f"TaskInterdepsViewer._refresh : Plotting in background thread, returning to main thread for GUI update."
                    )
                    return  # Exit and let callback handle completion
                # Sinon, pas de graph à afficher, on peut directement finir le rafraîchissement
                else:
                    bitmap = wx.NullBitmap
                    log.debug(
                        f"TaskInterdepsViewer._refresh : No edges to display, skipping plotting."
                    )
                    self._finish_refresh(bitmap)
                    return

        def _finish_refresh(self, bitmap):
            """Complete the refresh by updating the GUI with the new bitmap."""
            # Only update graphics once all refreshes have been "collapsed"
            log.debug(
                f"TaskInterdepsViewer._finish_refresh : Updating graph with bitmap={bitmap}"
            )
            graph_png_bm = wx.StaticBitmap(
                self.scrolled_panel, wx.ID_ANY, bitmap
            )
            self.hbox.Clear(True)
            self.hbox.Add(graph_png_bm, 1, wx.ALL, 3)
            # wx.CallAfter(self.scrolled_panel.SendSizeEvent)
            wx.CallAfter(self.__safeSendSizeEvent)

    def __safeSendSizeEvent(self):
        """Safely send size event to scrolled panel, guarding against deleted C++ objects."""
        try:
            if self.scrolled_panel:
                self.scrolled_panel.SendSizeEvent()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass
