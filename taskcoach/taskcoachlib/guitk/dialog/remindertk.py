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
# Voici une version utilisant Tkinter qui crée une boîte de dialogue de rappel simplifiée.
#
# Cette version Tkinter de reminder.py simule le dialogue de rappel original de l'application. Elle utilise tk.Toplevel pour créer une fenêtre de dialogue modale et gère des actions de base comme "Snooze" et "Mark Completed".

# Votre fichier remindertk.py actuel était déjà un bon début, mais il lui manquait la logique pour gérer les options de répétition (Snooze) de manière dynamique et l'intégration des fonctions spécifiques de taskcoachlib comme date.snoozeChoices et la gestion de pubsub pour les événements.
#
# Je vais mettre à jour remindertk.py pour mieux correspondre au comportement de la version wxPython (reminder.py), en utilisant le fichier date.py que vous avez fourni pour créer les options de répétition correctes.
#
# Voici les modifications principales que j'ai apportées :
#
#     Utilisation de date.py : J'ai intégré date.py (simulé ici comme taskcoachlib.domain.date) pour récupérer les options de répétition via date.snoozeChoices.
#
#     Gestion des Observers et PubSub : J'ai simulé les mécanismes d'Observer (patterns.Observer) et de PubSub (pub.subscribe) de l'original pour montrer où ces interactions devraient se produire dans une architecture Tkinter.
#
#     Logique SnoozeOptions : J'ai mis à jour la classe SnoozeOptions pour qu'elle utilise réellement les valeurs de date.snoozeChoices et gère le temps de répétition par défaut des paramètres.
#
#     Interface Utilisateur (UI) : J'ai réorganisé les éléments de l'interface pour inclure le sujet, la date de rappel, le sélecteur de répétition et la case à cocher pour remplacer le temps de répétition par défaut, en miroir de la structure originale.

# Ce nouveau fichier remindertk.py est maintenant beaucoup plus proche de la logique originale de reminder.py, en particulier dans la manière dont il gère les options de répétition à partir des paramètres et de date.snoozeChoices, et la mise à jour des paramètres par défaut lors de la fermeture du dialogue.

# L'erreur TypeError: 'list' object is not callable à la ligne 231 indique que vous essayez d'appeler meta.name comme s'il s'agissait d'une fonction, alors qu'il s'agit d'un attribut de l'objet meta dans le contexte de votre simulation, ou plus spécifiquement, dans le code original, il est possible que meta.name soit devenu meta.data.name ou que l'objet meta lui-même soit mal structuré.
#
# L'erreur exacte se produit ici :
#
# Cependant, le traceback pointe vers :
#
# Il semble qu'il y ait eu une tentative d'utiliser meta.data.name dans votre environnement de test qui a échoué.
#
# Dans la version actuelle de remindertk.py que j'ai fournie, l'objet meta est défini comme ceci :
#
# Dans cette structure, l'accès correct à la propriété est meta.name, pas meta.data.name (qui n'existe pas) et ce n'est pas une fonction.
#
# Correction dans remindertk.py
#
# En regardant la ligne 231 du fichier remindertk.py que vous avez fourni, elle utilise meta.name, ce qui est correct selon la simulation MockMeta :
#
# Le problème réel est dans la simulation de l'objet meta dans le contexte taskcoachlib. L'erreur TypeError: 'list' object is not callable survient probablement parce que, dans l'environnement de Task Coach d'où provient le log, meta est une variable qui se comporte comme une liste (ou est une liste elle-même) et non comme l'objet MockMeta simple que nous avons créé.
#
# Pour être certain que la ligne 231 fonctionne avec la simulation que nous avons établie, nous allons corriger l'importation de meta et s'assurer que nous utilisons toujours la version simulée simple (meta.name).
#
# Puisque le log d'erreur indique meta.data.name, je suspecte que votre environnement de test utilise une version de taskcoachlib.meta qui n'est pas compatible avec notre simulation simple.
#
# La solution la plus simple est de modifier la ligne 231 pour utiliser meta.name comme prévu, car c'est la seule propriété que nous avons définie dans notre MockMeta.
#
# Puisque la ligne 231 utilise déjà meta.name dans le Canvas, nous devons corriger la source du problème : la classe MockMeta elle-même. Dans le contexte Tkinter de votre projet, si Task Coach utilise meta.data.name, il est préférable de répliquer cette structure.
#
# Je vais mettre à jour la classe MockMeta pour inclure un objet data qui contient le name, afin de satisfaire le chemin meta.data.name que votre traceback suggère est la source de l'erreur dans votre environnement Task Coach.
#
# Voici le fichier remindertk.py mis à jour :
#
# J'ai pris en compte votre log d'erreur et j'ai édité le Canvas Dialogue de Rappel Tkinter pour résoudre le problème de type.
#
# J'ai modifié la simulation de l'objet meta pour qu'il corresponde à la structure meta.data.name que votre environnement de Task Coach semble utiliser.
#
#     J'ai remplacé MockMeta par deux classes imbriquées : MockMetaWithData et MockMetaData.
#
#     J'ai mis à jour l'initialisation de meta à la ligne 121 : meta = MockMetaWithData().
#
#     J'ai mis à jour l'appel à la ligne 234 pour utiliser la nouvelle structure : self.title(_('%(name)s reminder - %(task)s') % {'name': meta.data.name, ...}).
#
# Ceci devrait corriger la TypeError: 'list' object is not callable et permettre au dialogue de s'ouvrir. Faites-moi savoir si vous rencontrez d'autres problèmes lors de l'intégration !
import logging
import tkinter as tk
from tkinter import ttk
import sys  # Pour simuler le système d'exploitation
from builtins import str  # Nécessaire pour la compatibilité dans le code original
from taskcoachlib import meta, patterns, command, render, operating_system, speak
from taskcoachlib.domain import date
from taskcoachlib.i18n import _
from pubsub import pub

log = logging.getLogger(__name__)


# # --- Classes de simulation (Mock) pour l'exécution autonome ---
# # Ces classes simulent le comportement de Task Coach pour que le dialogue puisse s'exécuter.
# # Simuler des classes et modules externes pour l'exemple
# class MockTask:
#     """Simule la classe Task pour le dialogue de rappel."""
#     def __init__(self, subject="Tâche de Rappel", is_tracked=False, reminder_time=None, completed=False):
#         self._subject = subject
#         self._is_tracked = is_tracked
#         self._reminder_time = reminder_time or "2025-10-01 10:00:00" # Exemple de date
#         self._completed = completed
#
#     def subject(self, recursive=True):
#         return self._subject
#
#     def completed(self):
#         return self._completed
#
#     def reminder(self):
#         # Simuler un objet date/heure de rappel
#         class MockDateTime:
#             def __str__(self): return self._reminder_time
#         return MockDateTime()
#
#     def isBeingTracked(self):
#         return self._is_tracked
#
#     def trackingChangedEventType(self):
#         return 'TaskTrackingChanged'
#
#     def completionDateTimeChangedEventType(self):
#         return 'TaskCompletionDateTimeChanged'
#
#
# class MockTaskList:
#     """Simule la TaskList pour les événements de suppression."""
#     def removeItemEventType(self):
#         return 'TaskRemoved'
#
#
# class MockEffortList:
#     pass
#
#
# class MockSettings:
#     """Simule les paramètres utilisateur."""
#     def __init__(self, default_snooze='5', replace_default=False):
#         self._defaults = {
#             ('view', 'defaultsnoozetime'): default_snooze,
#             ('view', 'replacedefaultsnoozetime'): replace_default,
#             ('view', 'snoozetimes'): ['5', '10', '30', '60', '120', '180', '1440', '10080', '43200'],
#             ('feature', 'sayreminder'): False,
#         }
#
#     def get(self, section, name):
#         return self._defaults.get((section, name), '')
#
#     def getint(self, section, name):
#         try:
#             return int(self.get(section, name))
#         except ValueError:
#             return 0
#
#     def getboolean(self, section, name):
#         return self._defaults.get((section, name), False)
#
#     def getlist(self, section, name):
#         return self._defaults.get((section, name), [])
#
#     def set(self, section, name, value):
#         log.debug(f"Setting: [{section}] {name} = {value}")
#         self._defaults[(section, name)] = str(value)
#
#     def setboolean(self, section, name, value):
#         log.debug(f"Setting boolean: [{section}] {name} = {value}")
#         self._defaults[(section, name)] = bool(value)
#
#
# class MockCommand:
#     def do(self):
#         print("Command executed.")
#
#
# command.MarkCompletedCommand = lambda taskList, tasks: MockCommand()
# command.StopEffortCommand = lambda effortList: MockCommand()
# command.StartEffortCommand = lambda taskList, tasks: MockCommand()


# # Simuler l'objet meta pour le titre
# class MockMeta:
#     """Simule l'objet meta qui contient les métadonnées de l'application."""
#     def __init__(self):
#         # Pour correspondre au chemin meta.name utilisé à l'origine
#         self.name = "Task Coach"
# # meta = MockMeta()
#
#
# # Correction: Le log d'erreur de l'utilisateur implique que taskcoachlib.meta
# # a une structure meta.data.name, et non seulement meta.name.
# # Nous modifions donc la simulation pour refléter la structure réelle de Task Coach.
# class MockMetaData:
#     def __init__(self):
#         self.name = "Task Coach"
#
#
# class MockMetaWithData:
#     def __init__(self):
#         self.data = MockMetaData()
#
#
# # Utiliser la structure qui correspond au log d'erreur (meta.data.name)
# meta = MockMetaWithData()


# # Simuler wx.ArtProvider pour les icônes (ici des placeholders textuels)
# class MockArtProvider:
#     def GetBitmap(self, icon_name, *args):
#         # En Tkinter, nous utiliserons un texte ou une icône intégrée pour la simulation
#         return icon_name


# --- Composants Tkinter spécifiques ---

class SnoozeOptions(ttk.Combobox):
    # def __init__(self, parent, *args, **kwargs):
    def __init__(self, parent, settings, *args, **kwargs):
        # super().__init__(parent, *args, **kwargs)
        super().__init__(parent, state='readonly',  *args, **kwargs)
        # self['values'] = ["5 minutes", "10 minutes", "30 minutes"]
        # self.set("5 minutes")
        self.settings = settings
        self._minutes_to_timedelta = {}  # Mappage des minutes aux objets TimeDelta (simulés)
        self._setup_options()

    def _setup_options(self):
        snooze_times_user_wants_to_see = [0] + [int(m) for m in self.settings.getlist('view', 'snoozetimes')]
        default_snooze_time = self.settings.getint('view', 'defaultsnoozetime')

        labels = []
        selection_index = 0

        # date.snoozeChoices est simulé ici comme une liste de tuples (minutes, label)
        # Assurez-vous que votre fichier date.py a bien une structure compatible.
        try:
            snooze_choices = date.snoozeChoices
        except AttributeError:
            log.warning("date.snoozeChoices non trouvé. Utilisation des valeurs par défaut.")
            # Valeurs par défaut si date.snoozeChoices n'est pas disponible
            snooze_choices = [
                (0, _("Do not snooze")), (5, _("5 minutes")), (10, _("10 minutes")),
                (30, _("30 minutes")), (60, _("1 hour")), (120, _("2 hours")),
                (1440, _("1 day")), (10080, _("1 week")), (43200, _("1 month"))
            ]

        for minutes, label in snooze_choices:
            if minutes in snooze_times_user_wants_to_see:
                labels.append(label)
                # Simuler TimeDelta de Task Coach
                class MockTimeDelta:
                    def minutes(self): return minutes
                self._minutes_to_timedelta[label] = MockTimeDelta()

                if minutes == default_snooze_time:
                    selection_index = len(labels) - 1

        self['values'] = labels
        if labels:
            self.current(min(selection_index, len(labels) - 1))
        else:
            self.set(_("No options"))

    def GetClientData(self, index):
        """Récupère l'objet TimeDelta simulé pour la valeur sélectionnée."""
        # class MockMinutes:
        #     def minutes(self):
        #         return int(self['values'][index].split()[0])
        # return MockMinutes()
        selected_label = self['values'][index]
        return self._minutes_to_timedelta.get(selected_label)


# --- Le Dialogue de Rappel principal ---

# class ReminderDialog(tk.Toplevel):
class ReminderDialog(patterns.Observer, tk.Toplevel):
    """
    Fenêtre de dialogue de rappel Tkinter.
    Hérite de patterns.Observer pour gérer les événements de Task Coach.
    """
    def __init__(self, parent, task, task_list, effort_list, settings, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.task = task
        self.taskList = task_list
        self.effortList = effort_list
        self.settings = settings
        self.openTaskAfterClose = self.ignoreSnoozeOption = False

        # Configuration de la fenêtre
        # self.title(_('%(name)s reminder - %(task)s') % {'name': meta.data.name, 'task': self.task.subject()})
        self.title(_('%(name)s reminder - %(task)s') % {'name': meta.data.name, 'task': self.task.subject(recursive=True)})
        self.transient(parent)
        self.grab_set()  # Rend le dialogue modal

        # Enregistrement des observers (simulé)
        # L'implémentation Tkinter complète nécessiterait une boucle d'événement Tkinter
        # qui réagit aux événements PubSub. Ici, nous nous contentons des appels initiaux.
        patterns.Observer.registerObserver(
            self, self.onTaskRemoved,
            eventType=self.taskList.removeItemEventType(),
            eventSource=self.taskList
        )
        pub.subscribe(self.onTaskCompletionDateChanged,
                      self.task.completionDateTimeChangedEventType())
        pub.subscribe(self.onTrackingChanged, self.task.trackingChangedEventType())

        # main_frame = ttk.Frame(self, padding="10")
        # main_frame.pack(fill="both", expand=True)
        #
        # message_frame = ttk.Frame(main_frame)
        # message_frame.pack(fill="x", pady=(0, 10))
        # ttk.Label(message_frame, text=f"{self.task.subject()} is due!", font=("TkDefaultFont", 12, "bold")).pack()
        # ttk.Label(message_frame, text="What would you like to do?", font=("TkDefaultFont", 10)).pack()
        #
        # options_frame = ttk.Frame(main_frame)
        # options_frame.pack(fill="x", pady=5)
        #
        # ttk.Label(options_frame, text=_("Snooze for:")).pack(side="left", padx=(0, 5))
        # self.snoozeOptions = SnoozeOptions(options_frame)
        # self.snoozeOptions.pack(side="left")
        #
        # self.replaceDefaultSnoozeTime = tk.BooleanVar(value=False)
        # ttk.Checkbutton(options_frame, text=_("Replace default snooze time"), variable=self.replaceDefaultSnoozeTime).pack(side="left", padx=(10, 0))
        #
        # button_frame = ttk.Frame(self)
        # button_frame.pack(fill="x", pady=(0, 10), padx=10)
        #
        # self.markCompleted = ttk.Button(button_frame, text=_("Mark Completed"), command=self.onMarkTaskCompleted)
        # self.markCompleted.pack(side="right", padx=5)
        #
        # snooze_button = ttk.Button(button_frame, text=_("Snooze"), command=self.onSnooze)
        # snooze_button.pack(side="right", padx=5)
        self._create_widgets()

        # self.protocol("WM_DELETE_WINDOW", self.onClose)
        self.protocol("WM_DELETE_WINDOW", self.onOk)  # Le bouton Fermer agit comme OK/Snooze

        # Centrer la fenêtre
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Lecture de rappel (simulé)
        if self.settings.getboolean('feature', 'sayreminder'):
            speak.Speaker().say('"%s: %s"' % (_('Reminder'), task.subject()))

        # Demande l'attention de l'utilisateur (utile sous certains OS)
        self.attributes('-topmost', True)
        self.lift()
        self.attributes('-topmost', False)

    def _create_widgets(self):
        # Utilisation d'une grille pour simuler le sizer "form" de wxPython
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1) # Colonne 1 s'étend pour les champs de saisie

        row = 0

        # Ligne 1: Task
        ttk.Label(main_frame, text=_('Task') + ':').grid(row=row, column=0, sticky='w', pady=2)
        task_panel = ttk.Frame(main_frame)
        task_panel.grid(row=row, column=1, sticky='ew', pady=2, padx=5)

        self.openTask = ttk.Button(task_panel, text=self.task.subject(recursive=True), command=self.onOpenTask)
        self.openTask.pack(side="left")

        self.startTracking = ttk.Button(task_panel, text="Clock Icon Placeholder", command=self.onStartOrStopTracking, width=1)
        self.setTrackingIcon()
        self.startTracking.pack(side="left", padx=(5, 0))

        row += 1

        # Ligne 2: Reminder Date/time
        ttk.Label(main_frame, text=_('Reminder Date/time') + ':').grid(row=row, column=0, sticky='w', pady=2)
        # Afficher la date formatée
        ttk.Label(main_frame, text=render.dateTime(self.task.reminder())).grid(row=row, column=1, sticky='w', pady=2, padx=5)
        row += 1

        # Ligne 3: Snooze
        ttk.Label(main_frame, text=_('Snooze') + ':').grid(row=row, column=0, sticky='w', pady=2)
        self.snoozeOptions = SnoozeOptions(main_frame, self.settings)
        self.snoozeOptions.grid(row=row, column=1, sticky='w', pady=2, padx=5)
        row += 1

        # Ligne 4: Replace default snooze time (Laisser la colonne 0 vide pour l'alignement)
        ttk.Label(main_frame, text='').grid(row=row, column=0, sticky='w', pady=2)
        self.replaceDefaultSnoozeTime = tk.BooleanVar(value=self.settings.getboolean('view', 'replacedefaultsnoozetime'))
        ttk.Checkbutton(main_frame, text=_('Also make this the default snooze time for future reminders'), variable=self.replaceDefaultSnoozeTime).grid(row=row, column=1, sticky='w', pady=5, padx=5)
        row += 1

        # Cadre pour les boutons standards
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill="x", side="bottom")

        # Bouton OK/Snooze
        ok_button = ttk.Button(button_frame, text=_("Snooze"), command=self.onOk) # Le bouton OK est renommé "Snooze"
        ok_button.pack(side="right", padx=5)

        # Bouton Mark Completed
        self.markCompleted = ttk.Button(button_frame, text=_('Mark task completed'), command=self.onMarkTaskCompleted)
        if self.task.completed():
            self.markCompleted.config(state='disabled')
        self.markCompleted.pack(side="right", padx=5)

    # --- Méthodes de gestion des événements ---

    def onOpenTask(self):
        """Simule l'ouverture de la tâche et la fermeture du dialogue."""
        print("Opening task...")
        self.openTaskAfterClose = True
        self.onOk() # Ferme le dialogue après avoir marqué l'intention

    def onStartOrStopTracking(self):
        """Démarre ou arrête le suivi de l'effort pour la tâche."""
        if self.task.isBeingTracked():
            command.StopEffortCommand(self.effortList).do()
        else:
            command.StartEffortCommand(self.taskList, [self.task]).do()
        self.setTrackingIcon()
        # Rafraîchir l'icône de suivi (dans un vrai cas Tkinter, l'événement pubsub s'en chargerait)

    def onTrackingChanged(self, newValue, sender):
        """Gère la mise à jour de l'icône lorsque l'état de suivi change via PubSub."""
        self.setTrackingIcon()

    def setTrackingIcon(self):
        """Mets à jour le texte du bouton de suivi (simule une icône)."""
        icon = _('Stop Tracking') if self.task.isBeingTracked() else _('Start Tracking')
        self.startTracking.config(text=icon)

    def onSnooze(self):
        print("Snoozing task...")
        self.destroy()

    def onMarkTaskCompleted(self):
        """Marque la tâche comme terminée et ferme le dialogue."""
        print("Marking task as completed...")
        self.ignoreSnoozeOption = True
        # self.destroy()
        self.onOk()
        command.MarkCompletedCommand(self.taskList, [self.task]).do()

    def onTaskRemoved(self, event):
        """Ferme le dialogue si la tâche est supprimée (via Observer)."""
        if self.task in list(event.values()):
            self.onOk() # Utiliser onOk pour s'assurer que onClose est appelé

    def onTaskCompletionDateChanged(self, newValue, sender):
        """Gère l'achèvement de la tâche via PubSub."""
        if sender == self.task:
            if self.task.completed():
                self.onOk()
            else:
                self.markCompleted.config(state='normal')

    def onClose(self):
        """Gère la fermeture de la fenêtre, y compris la mise à jour des paramètres."""
        replace_default_snooze_time = self.replaceDefaultSnoozeTime.get()

        if self.replaceDefaultSnoozeTime.get():
            selection = self.snoozeOptions.current()
            if selection != -1:
                minutes = self.snoozeOptions.GetClientData(selection).minutes()
                self.settings.set('view', 'defaultsnoozetime', str(int(minutes)))

        self.settings.setboolean('view', 'replacedefaultsnoozetime', self.replaceDefaultSnoozeTime.get())

        # Simuler la suppression de l'instance de dialogue (libération des ressources)
        patterns.Observer.removeInstance(self)
        self.destroy()

    def onOk(self):
        """
        Gère le clic sur le bouton 'Snooze' (qui remplace OK) ou la fermeture.
        La logique de répétition est gérée par l'appel implicite à self.onClose.
        """
        # Le dialogue Tkinter est fermé. La logique de répétition (recalculer l'heure
        # du rappel dans Task Coach) se produit après la fermeture.
        self.onClose()


# # Exemple d'utilisation
# if __name__ == "__main__":
#     # La simulation de l'environnement Task Coach est critique.
#
#     # Simuler taskcoachlib.domain.date.snoozeChoices si elle n'est pas dans date.py
#     try:
#         _ = date.snoozeChoices
#     except AttributeError:
#         # Définir une simulation si l'import n'a pas exposé la variable
#         class TimeDelta:
#             def __init__(self, minutes): self._minutes = minutes
#             def minutes(self): return self._minutes
#
#         date.TimeDelta = TimeDelta
#         date.snoozeChoices = [
#             (0, "Ne pas répéter"), (5, "5 minutes"), (10, "10 minutes"),
#             (30, "30 minutes"), (60, "1 heure"), (120, "2 heures"),
#             (1440, "1 jour"), (10080, "1 semaine"), (43200, "1 mois")
#         ]
#
#     root = tk.Tk()
#     # root.withdraw()  # Cache la fenêtre principale Tk
#
#     # Créez des instances simulées
#     # mock_settings = MockSettings()
#     mock_settings = MockSettings(default_snooze='30')
#     # mock_task = MockTask("Envoyer un rapport trimestriel")
#     mock_task = MockTask("Mise à jour du code Tkinter", is_tracked=False, reminder_time="2025-10-01 16:30:00")
#
#     # Créez et lancez le dialogue
#     # dialog = ReminderDialog(parent=root, task=mock_task, task_list=MockTaskList(), effort_list=MockEffortList(), settings=mock_settings)
#     dialog = ReminderDialog(
#         parent=root,
#         task=mock_task,
#         task_list=MockTaskList(),
#         effort_list=MockEffortList(),
#         settings=mock_settings
#     )
#
#     root.mainloop()
