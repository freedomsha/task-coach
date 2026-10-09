"""Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Task Coach is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# Points clés de la conversion :
#
# Importation de Tkinter : import tkinter as tk
# Remplacement des éléments wxPython :
# wx.EVT_CLOSE est supprimé car la gestion des événements de fermeture sera différente avec Tkinter.
# wx.ArtProvider.GetBitmap est remplacé par un TODO, car Tkinter utilise des chemins de fichiers pour les images.
# wx.messagebox est remplacé par tk.messagebox pour afficher les boîtes de dialogue.
#
# Adaptation des méthodes d'affichage :
# __showReminderDialog utilise tk.messagebox.askyesno pour afficher une boîte de dialogue de rappel.
# requestUserAttention utilise lift() et focus_force() pour mettre la fenêtre principale au premier plan.
#
# Gestion des événements : Les événements wxPython sont remplacés par des mécanismes Tkinter, si nécessaire.
# Compatibilité des notifications : La méthode __showReminderViaNotifier nécessitera une adaptation plus poussée
# selon le système de notification que tu souhaites utiliser (notifications natives de l'OS, par exemple).
# Héritage et convention de nommage : La classe est renommée en ReminderControllerTk pour indiquer qu'il s'agit de la version Tkinter.
# Suppression des références à wx si wx = None: pour éviter les NameError.
#
# Explications détaillées :
#
# Initialisation et configuration : La classe ReminderControllerTk est initialisée de la même manière que l'original,
# en conservant les références à la fenêtre principale, à la liste des tâches, à la liste des efforts et aux paramètres.
# Gestion des rappels : Les méthodes onAddTask, onRemoveTask et onSetReminder restent similaires,
# car elles interagissent principalement avec des objets de la taskcoachlib qui ne dépendent pas directement de l'interface graphique.
# Affichage des messages de rappel :
#
# showReminderMessages itère sur les tâches avec des rappels et appelle showReminderMessage pour chaque tâche.
# showReminderMessage détermine si une boîte de dialogue Task Coach doit être affichée ou si une notification système doit être utilisée.
# __showReminderDialog utilise tk.messagebox.askyesno pour afficher une boîte de dialogue modale.
# Si l'utilisateur clique sur "Oui", la méthode openTaskEditor est appelée 6.
# __showReminderViaNotifier tente d'utiliser le système de notification de l'OS via notify.AbstractNotifier.
#
#
# Mise en attente (snooze) : La méthode __snooze reste inchangée, car elle interagit avec la taskcoachlib pour reporter le rappel.
# Demande d'attention de l'utilisateur : La méthode requestUserAttention est adaptée pour Tkinter.
# Elle utilise lift() pour mettre la fenêtre au premier plan et focus_force() pour s'assurer qu'elle reçoit le focus.
# Enregistrement et suppression des rappels : Les méthodes __registerRemindersForTasks, __removeRemindersForTasks,
# __registerReminder et __removeReminder restent similaires,
# car elles gèrent la logique de planification des rappels à l'aide de date.Scheduler.
#
# Prochaines étapes :
#
# Implémenter les notifications système : Adapter la méthode __showReminderViaNotifier pour utiliser les notifications natives de Tkinter ou un module tiers comme plyer.
# Tester et déboguer : Tester chaque fonctionnalité pour s'assurer qu'elle fonctionne correctement avec Tkinter.
# Adapter les dialogues : Si tu souhaites utiliser des dialogues personnalisés au lieu de simples boîtes de message,
# tu devras les convertir de wxPython à Tkinter.

# from builtins import object
import logging
from taskcoachlib import patterns, meta, notify
from taskcoachlib.domain import date, task
from taskcoachlib.guitk.dialog import editor
from taskcoachlib.guitk.dialog.editor import TaskEditor
from taskcoachlib.i18n import _
from . import artprovidertk
# try:
# from ..thirdparty.pubsub import pub
# except ImportError:
# from wx.lib.pubsub import pub
from pubsub import pub
import tkinter as tk
from tkinter import messagebox

log = logging.getLogger(__name__)


class ReminderControllerTk(object):
    lastId = 0

    @classmethod
    def nextId(cls):
        cls.lastId += 1
        return cls.lastId

    def __init__(self, mainWindow, taskList, effortList, settings):
        super().__init__()
        pub.subscribe(self.onSetReminder, task.Task.reminderChangedEventType())
        patterns.Publisher().registerObserver(self.onAddTask, eventType=taskList.addItemEventType(), eventSource=taskList)
        patterns.Publisher().registerObserver(self.onRemoveTask, eventType=taskList.removeItemEventType(), eventSource=taskList)
        self.__tasksWithReminders = {}  # {task: reminderDateTime}
        self.__mainWindow = mainWindow
        self.__mainWindowWasHidden = False
        self.__registerRemindersForTasks(taskList)
        self.settings = settings
        self.taskList = taskList
        self.effortList = effortList

    def onAddTask(self, event):
        self.__registerRemindersForTasks(list(event.values()))

    def onRemoveTask(self, event):
        self.__removeRemindersForTasks(list(event.values()))

    def onSetReminder(self, newValue, sender):  # pylint: disable=W0613
        self.__removeRemindersForTasks([sender])
        self.__registerRemindersForTasks([sender])

    def onReminder(self):
        self.showReminderMessages(date.DateTime.now())

    def showReminderMessages(self, now):
        now += date.TimeDelta(seconds=5)  # Be sure not to miss reminders
        requestUserAttention = False
        for taskWithReminder in list(self.__tasksWithReminders.keys()):  # self.__tasksWithReminders.copy():
            if taskWithReminder.reminder() <= now:
                requestUserAttention = True
                self.showReminderMessage(taskWithReminder)
        if requestUserAttention:
            self.requestUserAttention()

    def showReminderMessage(self, taskWithReminder):
        if self.__useOwnReminderDialog():
            self.__showReminderDialog(taskWithReminder)
        else:
            self.__showReminderViaNotifier(taskWithReminder)
        self.__removeReminder(taskWithReminder)
        self.__snooze(taskWithReminder)

    def __useOwnReminderDialog(self):
        notifier = self.settings.get("feature", "notifier")
        return (
                notifier == "Task Coach" or notify.AbstractNotifier.get(notifier) is None
        )

    def __showReminderDialog(self, taskWithReminder):
        # Créer une fenêtre contextuelle Tkinter pour afficher le rappel
        message = _("Reminder for: %s") % taskWithReminder.subject()
        if tk.messagebox.askyesno(_("Task Coach Reminder"), message):
            self.openTaskEditor(taskWithReminder)
            #     editTask = TaskEditor(self.__mainWindow, [taskWithReminder], self.effortList, self.taskList, self.__mainWindow.taskFile, bitmap="edit")
        #     editTask.Show(True)
        # else:
        #     editTask = None
        # return editTask

    def __showReminderViaNotifier(self, taskWithReminder):
        # Utiliser le système de notification de l'OS (à adapter selon l'OS)
        notifier = notify.AbstractNotifier.get(self.settings.get("feature", "notifier"))
        notifier.Notify(
            _("%s Reminder") % meta.name,
            taskWithReminder.subject(),
            # TODO:  Remplacer par une icône Tkinter si nécessaire
            # wx.ArtProvider.GetBitmap("taskcoach", size=wx.Size(32, 32)),
            # artprovidertk.ArtProvider.GetBitmap("taskcoach", size=(32, 32)),
            artprovidertk.getIcon("taskcoach", desired_size=(32, 32)),
            windowId=self.__mainWindow.GetHandle(),
            )

    def __snooze(self, taskWithReminder):
        minutesToSnooze = self.settings.getint("view", "defaultsnoozetime")
        taskWithReminder.snoozeReminder(date.TimeDelta(minutes=minutesToSnooze))

    def onCloseReminderDialog(self, event, show=True):
        # À adapter si nécessaire (gestion de la fermeture de la fenêtre)
        pass

    def requestUserAttention(self):
        # Adapter pour Tkinter (ex: focus sur la fenêtre principale)
        # notifier = self.settings.get("feature", "notifier")
        # if (
        #     notifier != "Task Coach"
        #     and notify.AbstractNotifier.get(notifier) is not None
        # ):
        #     # When using Growl/Snarl, this is not necessary. Even when not using Growl, it's
        #     # annoying as hell.  Anyway.
        #     return
        # self.__mainWindowWasHidden = not self.__mainWindow.IsShown()
        # if self.__mainWindowWasHidden:
        #     self.__mainWindow.Show()
        # if not self.__mainWindow.IsActive():
        #     self.__mainWindow.RequestUserAttention()
        if self.__mainWindow:
            self.__mainWindow.lift()  # Mettre la fenêtre au premier plan
            self.__mainWindow.focus_force()  # Forcer le focus

    def __registerRemindersForTasks(self, tasks):
        for eachTask in tasks:
            if eachTask.reminder() and eachTask.reminder() < date.DateTime():
                self.__registerReminder(eachTask)

    def __removeRemindersForTasks(self, tasks):
        for eachTask in tasks:
            if eachTask in self.__tasksWithReminders:
                self.__removeReminder(eachTask)

    def __registerReminder(self, taskWithReminder):
        reminderDateTime = taskWithReminder.reminder()
        now = date.DateTime.now()
        if reminderDateTime < now:
            reminderDateTime = now + date.TimeDelta(seconds=10)
        job = self.__tasksWithReminders[taskWithReminder] = date.Scheduler().schedule(self.onReminder, reminderDateTime)
        job.setId(self.nextId())

    def __removeReminder(self, taskWithReminder):
        job = self.__tasksWithReminders[taskWithReminder]
        date.Scheduler().unschedule(job)
        del self.__tasksWithReminders[taskWithReminder]

    def openTaskEditor(self, taskWithReminder):
        editTask = TaskEditor(self.__mainWindow, [taskWithReminder], self.effortList, self.taskList, self.__mainWindow.taskFile, bitmap="edit")
        # editTask.Show(True)
        # else:
        #     editTask = None
        # return editTask
