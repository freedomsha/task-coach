#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module calendarwidgettk.py - Implémente le widget de calendrier pour Task Coach (Tkinter).

Ce module contient les classes nécessaires pour afficher un calendrier interactif
dans l'application Task Coach, utilisant tkScheduler. Il gère
la récupération et l'affichage des tâches, les interactions utilisateur telles
que la sélection, le double-clic, le clic droit, le glisser-déposer de tâches,
ainsi que la mise à jour dynamique du calendrier.

Classes principales :
    _CalendarContent: Composant interne représentant le contenu principal du calendrier.
    Calendar: Widget d'affichage des tâches sous forme de calendrier.
    TaskSchedule: Représentation d'une tâche comme événement de calendrier.

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre discrétion) toute version ultérieure.
"""

import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

from taskcoachlib.thirdparty.tkScheduler.tkScheduler import tkScheduler
from taskcoachlib.thirdparty.tkScheduler.tkSchedule import tkSchedule
from taskcoachlib.thirdparty.tkScheduler.tkReportScheduler import tkReportScheduler
from taskcoachlib.thirdparty.tkScheduler.tkTimeFormat import tkTimeFormat
from taskcoachlib.thirdparty.tkScheduler.tkSchedulerConstants import (
    SCHEDULER_WEEKSTART_MONDAY,
    SCHEDULER_WEEKSTART_SUNDAY,
)
from taskcoachlib.domain import date
from taskcoachlib.widgetstk import draganddroptk as draganddrop
from taskcoachlib import command, render
from taskcoachlib.widgetstk import tooltiptk as tooltip

log = logging.getLogger(__name__)


class _CalendarContent(tooltip.ToolTip, tkScheduler):
    """
    Composant interne représentant le contenu principal du calendrier dans TaskCoach.

    Cette classe est responsable :
    - de l'affichage visuel des tâches dans un calendrier personnalisé,
    - de la gestion des événements utilisateur (clics, double-clics, popup),
    - de la gestion du glisser-déposer de fichiers, URL ou e-mails,
    - du rafraîchissement des tâches selon leur état et leurs dates.
    """

    def __init__(self, parent, taskList, iconProvider, onSelect, onEdit,
                 onCreate, onChangeConfig, popupMenu, *args, **kwargs):
        """
        Initialise le panneau de contenu du calendrier avec les tâches à afficher.

        :param parent: widget parent (le calendrier principal)
        :param taskList: liste des tâches à afficher
        :param iconProvider: fournisseur d'icônes pour les tâches
        :param onSelect: callback appelé lors de la sélection
        :param onEdit: callback pour l'édition de tâche
        :param onCreate: callback pour la création d'une nouvelle tâche
        :param onChangeConfig: callback lors du changement de configuration
        :param popupMenu: menu contextuel à afficher sur clic droit
        :param args: arguments supplémentaires pour tkScheduler
        :param kwargs: mots-clés supplémentaires (incluant onDropURL, onDropFiles, onDropMail)
        """
        log.debug(f"_CalendarContent.__init__ : args={args}, kwargs={kwargs}")

        # Extraire les callbacks de drop avant d'initialiser les parents
        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)

        # Créer un frame comme conteneur
        tk.Frame.__init__(self, parent)

        # Initialiser tkScheduler avec ce frame comme master
        tkScheduler.__init__(self, self, *args, **kwargs)

        log.debug(f"_CalendarContent.__init__ : après super args={args}, kwargs={kwargs}")

        self.getItemTooltipData = parent.getItemTooltipData

        # Configuration du drag and drop
        self.dropTarget = draganddrop.FileUrlDropTarget(
            self.canvas,
            on_drop_url_callback=self.OnDropURL,
            on_drop_file_callback=self.OnDropFiles
        )

        self.selectCommand = onSelect
        self.iconProvider = iconProvider
        self.editCommand = onEdit
        self.createCommand = onCreate
        self.changeConfigCb = onChangeConfig
        self.popupMenu = popupMenu

        self.__selection = []

        self.__showNoPlannedStartDate = False
        self.__showNoDueDate = False
        self.__showUnplanned = False

        self.SetShowWorkHour(False)
        self.SetResizable(True)

        self.taskList = taskList
        self.taskMap: dict = {}
        self.RefreshAllItems(0)

        # Binding des événements personnalisés
        self.canvas.bind("<<ScheduleActivated>>", self.OnActivation)
        self.canvas.bind("<<ScheduleRightClick>>", self.OnPopup)
        self.canvas.bind("<<ScheduleDClick>>", self.OnEdit)
        self.canvas.bind("<<PeriodWidthChanged>>", self.OnChangeConfig)

        tkTimeFormat.SetFormatFunction(self.__formatTime)
        log.info("_CalendarContent initialisé !")

    @staticmethod
    def __formatTime(dateTime, includeMinutes=False):
        """
        Formate une date pour l'affichage dans le calendrier (barres horaires, événements).

        :param dateTime: objet datetime à formater
        :param includeMinutes: booléen, indique s'il faut inclure les minutes
        :return: Chaîne de caractères formatée.
        """
        return render.time(TaskSchedule.tcDateTime(dateTime),
                           minutes=includeMinutes)

    # Gestion du glisser-déposer
    def _handleDrop(self, x, y, droppedObject, cb):
        """
        Gère la logique de drop d'objet (URL, fichier, e-mail) dans le calendrier.

        :param x: position X du drop
        :param y: position Y du drop
        :param droppedObject: objet déposé (str, list, etc.)
        :param cb: fonction de callback associée au type de drop
        """
        if cb is not None:
            found = self._findSchedule((x, y))

            if found is not None:
                _, _, item = found

                if isinstance(item, TaskSchedule):
                    cb(item.task, droppedObject)
                else:
                    # item est un datetime
                    datetime_obj = date.DateTime(item.year,
                                                 item.month,
                                                 item.day)
                    cb(None, droppedObject, plannedStartDateTime=datetime_obj,
                       dueDateTime=datetime_obj.endOfDay())

    def OnDropURL(self, x, y, url):
        """Gère le drop d'une URL."""
        self._handleDrop(x, y, url, self.__onDropURLCallback)

    def OnDropFiles(self, x, y, filenames):
        """Gère le drop de fichiers."""
        self._handleDrop(x, y, filenames, self.__onDropFilesCallback)

    def OnDropMail(self, x, y, mail):
        """Gère le drop de mails (via Drag & Drop)."""
        self._handleDrop(x, y, mail, self.__onDropMailCallback)

    def GetPrintout(self, settings):
        """Génère un rapport imprimable du calendrier."""
        return tkReportScheduler(
            self.GetViewType(),
            self.GetStyle(),
            self.GetDrawer(),
            self.GetDate(),
            self.GetWeekStart(),
            self.GetPeriodCount(),
            self.GetSchedules()
        )

    # Affichage conditionnel des tâches
    def SetShowNoStartDate(self, doShow):
        """
        Active/désactive l'affichage des tâches sans date de début.

        :param doShow: Booléen.
        """
        log.info(f"_CalendarContent.SetShowNoStartDate : L'affichage des tâches sans date de début est {doShow}. Rafraîchissement.")
        self.__showNoPlannedStartDate = doShow
        self.RefreshAllItems(0)

    def SetShowNoDueDate(self, doShow):
        """
        Active/désactive l'affichage des tâches sans date d'échéance.

        :param doShow: Booléen.
        """
        log.info(f"_CalendarContent.SetShowNoDueDate : L'affichage des tâches sans date d'échéance est {doShow}. Rafraîchissement.")
        self.__showNoDueDate = doShow
        self.RefreshAllItems(0)

    def SetShowUnplanned(self, doShow):
        """
        Active/désactive l'affichage des tâches non planifiées.

        :param doShow: Booléen.
        """
        log.info(f"_CalendarContent.SetShowUnplanned : L'affichage des tâches non planifiées est {doShow}. Rafraîchissement.")
        self.__showUnplanned = doShow
        self.RefreshAllItems(0)

    # Actions utilisateur
    def OnChangeConfig(self, event):
        """Appelle le callback de changement de configuration."""
        self.changeConfigCb()

    def OnActivation(self, event):
        """Active un élément (sélection via clic)."""
        self.focus_set()
        schedule = getattr(self.canvas, 'schedule_object', None)
        if schedule:
            self.Select(schedule)

    def OnPopup(self, event):
        """Affiche le menu contextuel à la position du clic droit."""
        self.OnActivation(event)
        self.after(10, lambda: self.popupMenu.tk_popup(
            event.x_root if hasattr(event, 'x_root') else self.winfo_pointerx(),
            event.y_root if hasattr(event, 'y_root') else self.winfo_pointery(),
        ))

    def OnEdit(self, event):
        """
        Gère un double-clic : ouvre l'édition d'une tâche existante ou en crée une nouvelle à la date cliquée.
        """
        schedule = getattr(self.canvas, 'schedule_object', None)
        date_obj = getattr(self.canvas, 'date_object', None)

        if schedule is None:
            if date_obj is not None:
                self.createCommand(date.DateTime(
                    date_obj.year,
                    date_obj.month,
                    date_obj.day,
                    date_obj.hour,
                    date_obj.minute,
                    date_obj.second
                ))
        else:
            self.editCommand(schedule.task)

    # Sélection de tâches
    def Select(self, schedule=None):
        """
        Sélectionne une tâche planifiée (Schedule), ou efface la sélection si `None`.

        Args :
            schedule : objet Schedule (ex. TaskSchedule)
        """
        if self.__selection:
            task_id = self.__selection[0].id()
            if task_id in self.taskMap:
                self.taskMap[task_id].SetSelected(False)

        if schedule is None:
            self.__selection = []
        else:
            self.__selection = [schedule.task]
            schedule.SetSelected(True)

        self.after(10, self.selectCommand)

    def SelectTask(self, task):
        """
        Sélectionne une tâche en la recherchant via son ID.

        Args :
            task : Tâche à sélectionner
        """
        if task.id() in self.taskMap:
            self.Select(self.taskMap[task.id()])

    # Rafraîchissement
    def RefreshAllItems(self, count):
        """
        Recharge et redessine toutes les tâches dans le calendrier selon les filtres actifs.

        :param count: Nombre d'éléments (non utilisé directement).
        """
        log.info(f"_CalendarContent.RefreshAllItems : Recharge et redessine toutes les tâches dans le calendrier selon les filtres actifs.")

        # Sauvegarder la position de scroll
        x_scroll = self.canvas.xview()[0]
        y_scroll = self.canvas.yview()[0]

        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        self.DeleteAll()

        schedules = []
        self.taskMap = {}
        maxDateTime = date.DateTime()

        for task in self.taskList:
            if not task.isDeleted():
                if task.plannedStartDateTime() == maxDateTime or not task.completed():
                    if task.plannedStartDateTime() == maxDateTime and not self.__showNoPlannedStartDate:
                        continue

                    if task.dueDateTime() == maxDateTime and not self.__showNoDueDate:
                        continue

                    if not self.__showUnplanned:
                        if task.plannedStartDateTime() == maxDateTime and task.dueDateTime() == maxDateTime:
                            continue

                schedule = TaskSchedule(task, self.iconProvider)
                schedules.append(schedule)
                self.taskMap[task.id()] = schedule

                if task.id() == selectionId:
                    self.__selection = [task]
                    schedule.SetSelected(True)

        self.Add(schedules)
        self.after(10, self.selectCommand)

        # Restaurer la position de scroll
        self.canvas.xview_moveto(x_scroll)
        self.canvas.yview_moveto(y_scroll)

        log.info(f"_CalendarContent.RefreshAllItems : Terminé ! Toutes les tâches sont redessinées!")

    def RefreshItems(self, *args):
        """
        Met à jour dynamiquement certaines tâches (ajout, suppression ou mise à jour visuelle).

        :param args: Arguments contenant la liste de tâches à rafraîchir.
        """
        log.info(f"_CalendarContent.RefreshItems : Met à jour dynamiquement certaines tâches de {args}.")
        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        for task in args:
            doShow = True

            if task.plannedStartDateTime() == date.DateTime() and task.dueDateTime() == date.DateTime() and not self.__showUnplanned:
                doShow = False

            if task.plannedStartDateTime() == date.DateTime() and not self.__showNoPlannedStartDate:
                doShow = False

            if task.dueDateTime() == date.DateTime() and not self.__showNoDueDate:
                doShow = False

            # Special case
            if task.isDeleted():
                doShow = False
            elif task.plannedStartDateTime() != date.DateTime() and task.completed():
                doShow = True

            if doShow:
                if task.id() in self.taskMap:
                    schedule = self.taskMap[task.id()]
                    schedule.update()
                else:
                    schedule = TaskSchedule(task, self.iconProvider)
                    self.taskMap[task.id()] = schedule
                    self.Add([schedule])

                if task.id() == selectionId:
                    self.__selection = [task]
                    schedule.SetSelected(True)
            else:
                if task.id() in self.taskMap:
                    self.Delete(self.taskMap[task.id()])
                    del self.taskMap[task.id()]
                    if self.__selection and self.__selection[0].id() == task.id():
                        self.__selection = []
                        self.after(10, self.selectCommand)
        log.info("_CalendarContent.RefreshItems : Mise à jour terminée !")

    # Utilitaires
    def GetItemCount(self):
        """
        Retourne le nombre d'éléments (Schedule) actuellement affichés dans le calendrier.
        """
        return len(self.GetSchedules())

    def curselection(self):
        """
        Retourne la liste des tâches actuellement sélectionnées.
        """
        return self.__selection

    # Info-bulles
    def OnBeforeShowToolTip(self, x, y):
        """
        Retourne l'info-bulle à afficher à la position (x, y) si un élément est présent.

        :param x: position x locale
        :param y: position y locale
        :return: une instance de tooltip ou None
        """
        # Obtenir les positions de scroll
        x_offset = int(self.canvas.canvasx(0))
        y_offset = int(self.canvas.canvasy(0))

        try:
            found = self._findSchedule((x + x_offset, y + y_offset))
        except (TypeError, AttributeError):
            return None

        if found:
            _, _, schedule = found
            if isinstance(schedule, TaskSchedule):
                item = schedule.task

                tooltipData = self.getItemTooltipData(item)
                doShow = any(data[1] for data in tooltipData)
                if doShow:
                    tooltip_text = "\n".join([f"{label}: {value}" for label, value in tooltipData if value])
                    return tooltip_text
        return None

    # Intégration Tkinter
    def GetMainWindow(self):
        """Retourne le widget principal (soi-même)."""
        return self

    MainWindow = property(GetMainWindow)


class Calendar(tk.Frame):
    """
    Widget d'affichage des tâches sous forme de calendrier dans TaskCoach.

    Ce widget est une composition de deux sous-panneaux :
    - `_headers` : panneau supérieur affichant l'en-tête du calendrier (jours, périodes, etc.)
    - `_content` : panneau principal contenant les éléments graphiques (cases, tâches, etc.)
    """

    def __init__(self, parent, taskList, iconProvider, onSelect, onEdit,
                 onCreate, onChangeConfig=None, popupMenu=None, *args, **kwargs):
        """
        Initialise le widget calendrier.

        :param parent: Le parent Tkinter (souvent un Viewer ou Frame).
        :param taskList: Liste des tâches à afficher dans le calendrier.
        :param iconProvider: Fournisseur d'icônes pour les tâches.
        :param onSelect: Fonction appelée lors de la sélection d'une tâche.
        :param onEdit: Fonction appelée lors de l'édition d'une tâche.
        :param onCreate: Fonction appelée lors de la création d'une tâche.
        :param onChangeConfig: Callback pour l'ouverture de la configuration (optionnel).
        :param popupMenu: Menu contextuel associé aux éléments du calendrier.
        :param args: Arguments supplémentaires.
        :param kwargs: Paramètres supplémentaires pour `_CalendarContent`.
        """
        log.info("Calendar.__init__ : initialisation de Calendar.")

        super().__init__(parent)

        self.getItemTooltipData = parent.getItemTooltipData

        # Initialisation du panneau d'en-tête du calendrier
        self._headers = tk.Frame(self, height=50)
        # self._headers.pack(side=tk.TOP, fill=tk.X)
        self._headers.pack(side="top", fill="x")

        # Initialisation du panneau des tâches
        self._content = _CalendarContent(
            self, taskList, iconProvider,
            onSelect, onEdit, onCreate,
            onChangeConfig=onChangeConfig,
            popupMenu=popupMenu,
            *args, **kwargs
        )
        # self._content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._content.pack(side="top", fill="both", expand=True)

        # Définit le panneau _headers comme zone d'en-tête indépendante
        self.after(100, lambda: self._content.SetHeaderPanel(self._headers))
        log.info("Calendar.__init__ : initialisation terminée !")

    def Draw(self, dc=None):
        """
        Redessine le contenu du calendrier.

        :param dc: Contexte de dessin (non utilisé dans Tkinter, conservé pour compatibilité)
        """
        log.debug(f"Calendar.Draw : Utilise _content.Refresh() sur {self.__class__.__name__}")
        self._content.Refresh()

    def SetShowNoStartDate(self, doShow):
        """Active ou désactive l'affichage des tâches sans date de début."""
        self._content.SetShowNoStartDate(doShow)

    def SetShowNoDueDate(self, doShow):
        """Active ou désactive l'affichage des tâches sans date d'échéance."""
        self._content.SetShowNoDueDate(doShow)

    def SetShowUnplanned(self, doShow):
        """Active ou désactive l'affichage des tâches non planifiées."""
        self._content.SetShowUnplanned(doShow)

    def SetWeekStartMonday(self):
        """Définit le lundi comme premier jour de la semaine."""
        self._content.SetWeekStart(SCHEDULER_WEEKSTART_MONDAY)

    def SetWeekStartSunday(self):
        """Définit le dimanche comme premier jour de la semaine."""
        self._content.SetWeekStart(SCHEDULER_WEEKSTART_SUNDAY)

    # Rafraîchissements
    def RefreshAllItems(self, count):
        """Rafraîchit entièrement le contenu du calendrier."""
        log.info(f"Calendar.RefreshAllItems : Rafraîchit entièrement le contenu du calendrier avec {count} éléments.")
        self._content.RefreshAllItems(count)
        log.info(f"Calendar.RefreshAllItems : Les {count} éléments du calendrier ont été rafraîchis !")

    def RefreshItems(self, *args):
        """Rafraîchit une sélection d'éléments uniquement."""
        log.info(f"Calendar.RefreshItems : Rafraîchit uniquement les éléments {args}.")
        self._content.RefreshItems(*args)
        log.info(f"Calendar.RefreshItems : Les éléments {args} sont rafraîchis ! Terminé !")

    # Gestion de sélection
    def GetItemCount(self):
        """Retourne le nombre total d'éléments affichés."""
        return self._content.GetItemCount()

    def curselection(self):
        """Retourne la sélection courante."""
        return self._content.curselection()

    def select(self, tasks):
        """Sélectionne les tâches données."""
        if len(tasks) == 1:
            self._content.SelectTask(tasks[0])
        else:
            self._content.Select(None)

    def isAnyItemCollapsable(self):
        """Indique que les éléments ne sont pas repliables."""
        return False

    def __getattr__(self, name):
        """Délègue dynamiquement l'accès aux attributs de `_CalendarContent`."""
        content = self._content
        if hasattr(content, "_getAttrDict"):
            d = content._getAttrDict()
            if name in d:
                return d[name]
        return getattr(content, name)


class TaskSchedule(tkSchedule):
    """
    Représente une tâche de Task Coach comme un événement de calendrier pour tkScheduler.
    """

    def __init__(self, task, iconProvider):
        """
        Initialise une instance de TaskSchedule.

        Args :
            task : L'objet tâche Task Coach à encapsuler.
            iconProvider : Un objet capable de fournir l'icône appropriée pour la tâche.
        """
        log.info(f"TaskSchedule.__init__ : Représente la tâche {task} comme un événement de calendrier pour tkScheduler.")
        super().__init__()

        self.__selected = False

        self.clientdata = task
        self.iconProvider = iconProvider
        self.update()
        log.info(f"TaskSchedule.__init__ : tâche {task} initialisée !")

    def SetSelected(self, selected):
        """Définit l'état de sélection de l'événement."""
        self.Freeze()
        try:
            self.__selected = selected
            if selected:
                # Couleur de surbrillance pour la sélection
                self.color = "#0078D7"  # Bleu Windows
                color = self.task.foregroundColor(True) or (0, 0, 0)
                if len(color) == 3:
                    r, g, b = color
                else:
                    r, g, b, a = color
                if r + g + b < 128 * 3:
                    self.foreground = f"#{255-r:02x}{255-g:02x}{255-b:02x}"
                else:
                    fg_color = self.task.foregroundColor(True) or (0, 0, 0)
                    self.foreground = f"#{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}"
            else:
                bg_color = self.task.backgroundColor(True) or (255, 255, 255)
                self.color = f"#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}"
                fg_color = self.task.foregroundColor(True) or (0, 0, 0)
                self.foreground = f"#{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}"
        finally:
            self.Thaw()

    def SetStart(self, start):
        """Définit la date/heure de début planifiée."""
        command.EditPlannedStartDateTimeCommand(
            items=[self.task],
            newValue=self.tcDateTime(start)
        ).do()

    def SetEnd(self, end):
        """Définit la date/heure de fin."""
        if self.task.completed():
            command.EditCompletionDateTimeCommand(
                items=[self.task],
                newValue=self.tcDateTime(end)
            ).do()
        else:
            command.EditDueDateTimeCommand(
                items=[self.task],
                newValue=self.tcDateTime(end)
            ).do()

    def Offset(self, ts):
        """Déplace la tâche dans le temps."""
        if self.task.plannedStartDateTime() != date.DateTime():
            start = self.GetStart()
            start += ts
            command.EditPlannedStartDateTimeCommand(
                items=[self.task],
                newValue=self.tcDateTime(start)
            ).do()

        if self.task.completed():
            end = self.GetEnd()
            end += ts
            command.EditCompletionDateTimeCommand(
                items=[self.task],
                newValue=self.tcDateTime(end)
            ).do()
        elif self.task.dueDateTime() != date.DateTime():
            end = self.GetEnd()
            end += ts
            command.EditDueDateTimeCommand(
                items=[self.task],
                newValue=self.tcDateTime(end)
            ).do()

    @property
    def task(self):
        """Propriété qui retourne l'objet tâche Task Coach sous-jacent."""
        return self.clientdata

    def update(self):
        """Met à jour toutes les propriétés visuelles de l'événement."""
        log.info("TaskSchedule.update : Met à jour toutes les propriétés visuelles de l'événement.")
        self.Freeze()
        try:
            self.description = self.task.subject()

            # Définit la date de début
            self.start = self.datetimeFromTask(
                self.task.plannedStartDateTime(),
                date.Now().startOfDay()
            )

            # Définit la date de fin
            end = self.task.completionDateTime() if self.task.completed() else self.task.dueDateTime()
            self.end = self.datetimeFromTask(end, date.Now().endOfDay())

            if self.task.completed():
                self.done = True

            # Définit les couleurs
            bg_color = self.task.backgroundColor(True) or (255, 255, 255)
            self.color = f"#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}"
            fg_color = self.task.foregroundColor(True) or (0, 0, 0)
            self.foreground = f"#{fg_color[0]:02x}{fg_color[1]:02x}{fg_color[2]:02x}"

            # Définit la police
            self.font = self.task.font(True)

            self.icons = [self.iconProvider(self.task, False)]
            if self.task.attachments():
                self.icons.append("paperclip_icon")
            if self.task.notes():
                self.icons.append("note_icon")

            # Calcule le pourcentage d'achèvement
            if self.task.percentageComplete(recursive=True):
                self.complete = 1.0 * self.task.percentageComplete(recursive=True) / 100
            else:
                self.complete = None
        finally:
            self.Thaw()
        log.info("TaskSchedule.update : Mise à jour terminée !")

    @staticmethod
    def datetimeFromTask(taskDateTime, default):
        """Convertit un objet date.DateTime de Task Coach en datetime Python."""
        if taskDateTime == date.DateTime():
            # Utiliser la valeur par défaut
            return datetime(default.year, default.month, default.day,
                            default.hour, default.minute, default.second)
        return datetime(taskDateTime.year, taskDateTime.month, taskDateTime.day,
                        taskDateTime.hour, taskDateTime.minute, taskDateTime.second)

    @staticmethod
    def tcDateTime(dt):
        """Convertit un datetime Python en objet date.DateTime de Task Coach."""
        return date.DateTime(dt.year, dt.month, dt.day,
                             dt.hour, dt.minute, dt.second)
