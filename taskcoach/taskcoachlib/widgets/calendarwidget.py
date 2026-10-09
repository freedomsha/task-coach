"""
Module calendarwidget.py - Implémente le widget de calendrier pour Task Coach.

Ce module contient les classes nécessaires pour afficher un calendrier interactif
dans l'application Task Coach, utilisant la bibliothèque wxScheduler. Il gère
la récupération et l'affichage des tâches, les interactions utilisateur telles
que la sélection, le double-clic, le clic droit, le glisser-déposer de tâches,
ainsi que la mise à jour dynamique du calendrier.

Classes principales :
    _CalendarContent: Composant interne représentant le contenu principal du calendrier.
    Calendar: Widget d'affichage des tâches sous forme de calendrier.
    TaskSchedule:

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach est un logiciel libre : vous pouvez le redistribuer et/ou le modifier
selon les termes de la Licence Publique Générale GNU telle que publiée par
la Free Software Foundation, soit la version 3 de la Licence, ou
(à votre discrétion) toute version ultérieure.

Task Coach est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
COMMERCIALISATION OU D'ADAPTATION À UN USAGE PARTICULIER. Voir le
Licence Publique Générale GNU pour plus de détails.

Vous auriez dû recevoir une copie de la Licence Publique Générale GNU
avec ce programme. Sinon, voir <http://www.gnu.org/licenses/>.

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

# from __future__ import division # Importation future pour la division (déjà gérée en Python 3).
# from past.utils import old_div # Compatibilité pour la division entière avec Python 2.
import logging  # Module de journalisation.
import wx  # La bibliothèque principale wxPython.
from taskcoachlib.thirdparty.wxScheduler import (
    wxScheduler,
    wxSchedule,
    wxReportScheduler,
    wxTimeFormat,
)  # Composants de wxScheduler.
from taskcoachlib.thirdparty.wxScheduler.wxSchedulerPaint import (
    EVT_SCHEDULE_ACTIVATED,  # Événement : un élément de calendrier est activé.
    EVT_SCHEDULE_RIGHT_CLICK,  # Événement : clic droit sur un élément.
    EVT_SCHEDULE_DCLICK,  # Événement : double-clic sur un élément.
    EVT_PERIODWIDTH_CHANGED,  # Événement : la largeur de la période d'affichage a changé.
)
from taskcoachlib.thirdparty.wxScheduler.wxSchedulerConstants import (
    wxSCHEDULER_WEEKSTART_MONDAY,  # Constante : la semaine commence le lundi.
    wxSCHEDULER_WEEKSTART_SUNDAY,  # Constante : la semaine commence le dimanche.
)
from taskcoachlib.domain import (
    date,
)  # Module pour la gestion des dates et heures spécifiques à Task Coach.
from taskcoachlib.widgets import (
    draganddrop,
)  # Module pour la gestion du glisser-déposer.
from taskcoachlib import (
    command,
    render,
)  # Modules pour les commandes et le rendu.
from . import tooltip  # Module pour les info-bulles.

log = logging.getLogger(__name__)  # Initialise le logger pour ce module.


class _CalendarContent(tooltip.ToolTipMixin, wxScheduler):
    """
    Composant interne représentant le contenu principal du calendrier dans TaskCoach.

    Cette classe est responsable :
    - de l’affichage visuel des tâches dans un calendrier personnalisé,
    - de la gestion des événements utilisateur (clics, double-clics, popup),
    - de la gestion du glisser-déposer de fichiers, URL ou e-mails,
    - du rafraîchissement des tâches selon leur état et leurs dates.

    Elle repose sur `wxScheduler`, un widget étendu pour afficher des périodes temporelles,
    et intègre la gestion des info-bulles contextuelles via `ToolTipMixin`.
    """

    def __init__(
        self,
        parent,
        taskList,
        iconProvider,
        onSelect,
        onEdit,
        onCreate,
        onChangeConfig,
        popupMenu,
        *args,
        **kwargs,
    ):
        """
        Initialise le panneau de contenu du calendrier avec les tâches à afficher.

        :param parent: widget parent (le calendrier principal)
        :param taskList: liste des tâches à afficher
        :param iconProvider: fournisseur d’icônes pour les tâches
        :param onSelect: callback appelé lors de la sélection
        :param onEdit: callback pour l’édition de tâche
        :param onCreate: callback pour la création d’une nouvelle tâche
        :param onChangeConfig: callback lors du changement de configuration
        :param popupMenu: menu contextuel à afficher sur clic droit
        :param args: arguments supplémentaires pour wxScheduler
        :param kwargs: mots-clés supplémentaires (incluant onDropURL, onDropFiles, onDropMail)
        """
        log.debug(f"_CalendarContent.__init__ : args={args}, kwargs={kwargs}")
        log.debug(
            f"_CalendarContent.__init__ : mro={_CalendarContent.__mro__}"
        )
        # self.getItemTooltipData = parent.getItemTooltipData

        self.__onDropURLCallback = kwargs.pop("onDropURL", None)
        self.__onDropFilesCallback = kwargs.pop("onDropFiles", None)
        self.__onDropMailCallback = kwargs.pop("onDropMail", None)

        log.debug(
            f"_CalendarContent.__init__ : avant super args={args}, kwargs={kwargs}"
        )
        # super().__init__(id=wx.ID_ANY, *args, **kwargs)
        # super().__init__(parent, *args, **kwargs)  # Faire attention à faire suivre les arguments dans tous les Parents-Enfants de la classe en suivant le MRO
        super().__init__(parent, wx.ID_ANY, *args, **kwargs)
        log.debug(
            f"_CalendarContent.__init__ : après super args={args}, kwargs={kwargs}"
        )
        self.getItemTooltipData = parent.getItemTooltipData

        self.dropTarget = draganddrop.DropTarget(
            self.OnDropURL, self.OnDropFiles, self.OnDropMail
        )

        self.SetDropTarget(self.dropTarget)

        self.selectCommand = onSelect
        self.iconProvider = iconProvider
        self.editCommand = onEdit
        self.createCommand = onCreate
        self.changeConfigCb = onChangeConfig
        self.popupMenu = popupMenu

        self.__tip = tooltip.SimpleToolTip(self)
        self.__selection = []

        self.__showNoPlannedStartDate = False
        self.__showNoDueDate = False
        self.__showUnplanned = False

        self.SetShowWorkHour(False)
        self.SetResizable(True)

        self.taskList = taskList
        self.RefreshAllItems(0)

        # EVT_SCHEDULE_ACTIVATED(self, self.OnActivation)
        self.Bind(EVT_SCHEDULE_ACTIVATED, self.OnActivation)
        # EVT_SCHEDULE_RIGHT_CLICK(self, self.OnPopup)
        self.Bind(EVT_SCHEDULE_RIGHT_CLICK, self.OnPopup)
        # EVT_SCHEDULE_DCLICK(self, self.OnEdit)
        self.Bind(EVT_SCHEDULE_DCLICK, self.OnEdit)
        # EVT_PERIODWIDTH_CHANGED(self, self.OnChangeConfig)
        self.Bind(EVT_PERIODWIDTH_CHANGED, self.OnChangeConfig)

        wxTimeFormat.SetFormatFunction(self.__formatTime)
        # wxTimeFormat.SetFormatFunction(self, self.__formatTime)
        # wxTimeFormat.SetFormatFunction(wxTimeFormat, self.__formatTime)  # ? TODO : A essayer.
        log.info("_CalendarContent initialisé !")

    @staticmethod
    def __formatTime(dateTime, includeMinutes=False):
        """
        Formate une date pour l’affichage dans le calendrier (barres horaires, événements).

        :param dateTime: objet date.DateTime à formater
        :param includeMinutes: booléen, indique s’il faut inclure les minutes
        :return: Chaîne de caractères formatée.
        """
        return render.time(
            TaskSchedule.tcDateTime(dateTime), minutes=includeMinutes
        )

    # Gestion du glisser-déposer
    def _handleDrop(self, x, y, droppedObject, cb):
        """
        Gère la logique de drop d’objet (URL, fichier, e-mail) dans le calendrier.

        :param x: position X du drop
        :param y: position Y du drop
        :param droppedObject: objet déposé (str, list, etc.)
        :param cb: fonction de callback associée au type de drop
        """
        if cb is not None:
            _, _, item = self._findSchedule(wx.Point(x, y))

            if item is not None:
                if isinstance(item, TaskSchedule):
                    cb(item.task, droppedObject)
                else:
                    datetime = date.DateTime(
                        item.GetYear(), item.GetMonth() + 1, item.GetDay()
                    )
                    cb(
                        None,
                        droppedObject,
                        plannedStartDateTime=datetime,
                        dueDateTime=datetime.endOfDay(),
                    )

    def GetPrintout(self, settings):
        return wxReportScheduler(
            self.GetViewType(),
            self.GetStyle(),
            self.GetDrawer(),
            self.GetDate(),
            self.GetWeekStart(),
            self.GetPeriodCount(),
            self.GetSchedules(),
        )

    def OnDropURL(self, x, y, url):
        """Gère le drop d’une URL."""
        self._handleDrop(x, y, url, self.__onDropURLCallback)

    def OnDropFiles(self, x, y, filenames):
        """Gère le drop de fichiers."""
        self._handleDrop(x, y, filenames, self.__onDropFilesCallback)

    def OnDropMail(self, x, y, mail):
        """Gère le drop de mails (via Drag & Drop)."""
        self._handleDrop(x, y, mail, self.__onDropMailCallback)

    # Affichage conditionnel des tâches
    def SetShowNoStartDate(self, doShow):
        """
        Active/désactive l’affichage des tâches sans date de début.

        :param doShow: Booléen.
        """
        log.info(
            f"_CalendarContent.SetShowNoStartDate : L’affichage des tâches sans date de début est {doShow}. Rafraîchissement."
        )
        self.__showNoPlannedStartDate = doShow
        self.RefreshAllItems(0)

    def SetShowNoDueDate(self, doShow):
        """
        Active/désactive l’affichage des tâches sans date d’échéance.

        :param doShow: Booléen.
        """
        log.info(
            f"_CalendarContent.SetShowNoDueDate : L’affichage des tâches sans date d’échéance est {doShow}. Rafraîchissement."
        )
        self.__showNoDueDate = doShow
        self.RefreshAllItems(0)

    def SetShowUnplanned(self, doShow):
        """
        Active/désactive l’affichage des tâches non planifiées.

        :param doShow: Booléen.
        """
        log.info(
            f"_CalendarContent.SetShowUnplanned : L’affichage des tâches non planifiées est {doShow}. Rafraîchissement."
        )
        self.__showUnplanned = doShow
        self.RefreshAllItems(0)

    # Actions utilisateur
    def OnChangeConfig(self, event):  # pylint: disable=W0613
        """Appelle le callback de changement de configuration."""
        self.changeConfigCb()

    def OnActivation(self, event):
        """Active un élément (sélection via clic)."""
        self.SetFocus()
        self.Select(event.schedule)

    def OnPopup(self, event):
        """Affiche le menu contextuel à la position du clic droit."""
        self.OnActivation(event)
        wx.CallAfter(self.PopupMenu, self.popupMenu)

    def OnEdit(self, event):
        """
        Gère un double-clic : ouvre l'édition d'une tâche existante ou en crée une nouvelle à la date cliquée.
        """
        if event.schedule is None:
            if event.date is not None:
                self.createCommand(
                    date.DateTime(
                        event.date.GetYear(),
                        event.date.GetMonth() + 1,
                        event.date.GetDay(),
                        event.date.GetHour(),
                        event.date.GetMinute(),
                        event.date.GetSecond(),
                    )
                )
        else:
            self.editCommand(event.schedule.task)

    # Sélection de tâches
    def Select(self, schedule=None):
        """
        Sélectionne une tâche planifiée (Schedule), ou efface la sélection si `None`.

        :param schedule: objet Schedule (ex. TaskSchedule)
        """
        if self.__selection:
            self.taskMap[self.__selection[0].id()].SetSelected(False)

        if schedule is None:
            self.__selection = []
        else:
            self.__selection = [schedule.task]
            schedule.SetSelected(True)

        # wx.CallAfter(self.selectCommand)
        wx.CallAfter(self.__safeSelectCommand)

    def __safeSelectCommand(self):
        """Safely call selectCommand, guarding against deleted C++ objects."""
        try:
            if self:
                self.selectCommand()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def SelectTask(self, task):
        """
        Sélectionne une tâche en la recherchant via son ID.

        :param task: tâche à sélectionner
        """
        if task.id() in self.taskMap:
            self.Select(self.taskMap[task.id()])

    # Rafraîchissement
    def RefreshAllItems(self, count):  # pylint: disable=W0613
        """
        Recharge et redessine toutes les tâches dans le calendrier selon les filtres actifs.

        :param count: Nombre d’éléments (non utilisé directement).
        """
        log.info(
            f"_CalendarContent.RefreshAllItems : Recharge et redessine toutes les tâches dans le calendrier selon les filtres actifs."
        )
        x, y = self.GetViewStart()
        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        self.DeleteAll()

        schedules = []
        self.taskMap = {}  # pylint: disable=W0201
        maxDateTime = date.DateTime()

        for task in self.taskList:
            if not task.isDeleted():
                if (
                    task.plannedStartDateTime() == maxDateTime
                    or not task.completed()
                ):
                    if (
                        task.plannedStartDateTime() == maxDateTime
                        and not self.__showNoPlannedStartDate
                    ):
                        continue

                    if (
                        task.dueDateTime() == maxDateTime
                        and not self.__showNoDueDate
                    ):
                        continue

                    if not self.__showUnplanned:
                        if (
                            task.plannedStartDateTime() == maxDateTime
                            and task.dueDateTime() == maxDateTime
                        ):
                            continue

                schedule = TaskSchedule(task, self.iconProvider)
                schedules.append(schedule)
                self.taskMap[task.id()] = schedule

                if task.id() == selectionId:
                    self.__selection = [task]
                    schedule.SetSelected(True)

        self.Add(schedules)
        # wx.CallAfter(self.selectCommand)
        wx.CallAfter(self.__safeSelectCommand)
        self.Scroll(x, y)
        log.info(
            f"_CalendarContent.RefreshAllItems : Terminé ! Toutes les tâches sont redessinées!"
        )

    def RefreshItems(self, *args):
        """
        Met à jour dynamiquement certaines tâches (ajout, suppression ou mise à jour visuelle).

        :param args: Arguments contenant la liste de tâches à rafraîchir.
        """
        log.info(
            f"_CalendarContent.RefreshItems : Met à jour dynamiquement certaines tâches de {args}."
        )
        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        for task in args:
            doShow = True

            if (
                task.plannedStartDateTime() == date.DateTime()
                and task.dueDateTime() == date.DateTime()
                and not self.__showUnplanned
            ):
                doShow = False

            if (
                task.plannedStartDateTime() == date.DateTime()
                and not self.__showNoPlannedStartDate
            ):
                doShow = False

            if (
                task.dueDateTime() == date.DateTime()
                and not self.__showNoDueDate
            ):
                doShow = False

            # Special case
            if task.isDeleted():
                doShow = False
            elif (
                task.plannedStartDateTime() != date.DateTime()
                and task.completed()
            ):
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
                    if (
                        self.__selection
                        and self.__selection[0].id() == task.id()
                    ):
                        self.__selection = []
                        # wx.CallAfter(self.selectCommand)
                        wx.CallAfter(self.__safeSelectCommand)
        log.info("_CalendarContent.RefreshItems : Mise à jour terminée !")

    # Utilitaires
    def GetItemCount(self):
        """
        Retourne le nombre d’éléments (Schedule) actuellement affichés dans le calendrier.
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
        Retourne l’info-bulle à afficher à la position (x, y) si un élément est présent.

        :param x: position x locale
        :param y: position y locale
        :return: une instance de `SimpleToolTip` ou None
        """
        originX, originY = self.GetViewStart()
        unitX, unitY = self.GetScrollPixelsPerUnit()

        try:
            _, _, schedule = self._findSchedule(
                wx.Point(x + originX * unitX, y + originY * unitY)
            )
        except TypeError:
            return

        if schedule and isinstance(schedule, TaskSchedule):
            item = schedule.task

            tooltipData = self.getItemTooltipData(item)
            doShow = any(data[1] for data in tooltipData)
            if doShow:
                self.__tip.SetData(tooltipData)
                return self.__tip
            else:
                return None

    # Intégration wxPython
    def GetMainWindow(self):
        """Retourne le widget principal (soi-même)."""
        return self

    MainWindow = property(GetMainWindow)


class Calendar(wx.Panel):
    """
    Widget d'affichage des tâches sous forme de calendrier dans TaskCoach.

    Ce widget est une composition de deux sous-panneaux :
    - `_headers` : panneau supérieur affichant l'en-tête du calendrier (jours, périodes, etc.)
    - `_content` : panneau principal contenant les éléments graphiques (cases, tâches, etc.)

    Il fournit une interface simplifiée pour contrôler l'affichage du calendrier :
    - Affichage des tâches sans dates,
    - Semaine commençant le lundi ou le dimanche,
    - Rafraîchissement des éléments affichés,
    - Sélection de tâches, etc.

    Il délègue la logique d'affichage et d'interaction à la classe `_CalendarContent`.
    """

    def __init__(
        self,
        parent,
        taskList,
        iconProvider,
        onSelect,
        onEdit,
        onCreate,
        onChangeConfig=None,
        popupMenu=None,
        *args,
        **kwargs,
    ):
        """
        Initialise le widget calendrier.

        :param parent: Le parent wxPython (souvent un Viewer ou Frame).
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
        self.getItemTooltipData = parent.getItemTooltipData

        super().__init__(parent)

        # Initialisation du panneau d'en-tête du calendrier
        self._headers = wx.Panel(self)
        # Initialisation du panneau des tâches
        self._content = _CalendarContent(
            self,
            taskList,
            iconProvider,
            onSelect,
            onEdit,
            onCreate,
            onChangeConfig=onChangeConfig,
            popupMenu=popupMenu,
            *args,
            **kwargs,
        )
        # self.widget._drawHeaders = True
        # Composition des 2 sous-panneaux :
        sizer = wx.BoxSizer(wx.VERTICAL)
        #     - `_headers` : panneau supérieur affichant l'en-tête du calendrier (jours, périodes, etc.)
        sizer.Add(self._headers, 0, wx.EXPAND)
        #     - `_content` : panneau principal contenant les éléments graphiques (cases, tâches, etc.)
        sizer.Add(self._content, 1, wx.EXPAND)
        # Définit la fenêtre pour avoir le Sizer de mise en page donné.
        self.SetSizer(sizer)

        # Définit le panneau wx.Panel self._header comme zone d'en-tête indépendante.
        # Les en-têtes seront alors dessinés sur ce panneau, indépendamment du scroll vertical.
        # Must wx.CallAfter because SetDrawerClass is called this way.
        # wx.callafter est obligatoire car SetDrawerclass est appelé de cette façon.
        wx.CallAfter(self._content.SetHeaderPanel, self._headers)
        log.info("Calendar.__init__ : initialisation terminée !")

    def Draw(self, dc):
        """
        Redessine le contenu du calendrier en appelant la méthode `Draw` du panneau `_content`.

        :param dc: Contexte de dessin wx.DC utilisé pour peindre le calendrier.
        """
        log.debug(
            f"Calendar.Draw : Utilise _content.Draw() sur {self.__class__.__name__} avec le contexte de dessin {dc}."
        )
        self._content.Draw(dc)

    def SetShowNoStartDate(self, doShow):
        """
        Active ou désactive l'affichage des tâches sans date de début.
        :param doShow: Booléen.
        """
        self._content.SetShowNoStartDate(doShow)

    def SetShowNoDueDate(self, doShow):
        """
        Active ou désactive l'affichage des tâches sans date d'échéance.
        :param doShow: booléen
        """
        self._content.SetShowNoDueDate(doShow)

    def SetShowUnplanned(self, doShow):
        """
        Active ou désactive l'affichage des tâches non planifiées (ni début ni fin).
        :param doShow: booléen
        """
        self._content.SetShowUnplanned(doShow)

    def SetWeekStartMonday(self):
        """
        Définit le lundi comme premier jour de la semaine dans le calendrier.
        """
        self._content.SetWeekStart(wxSCHEDULER_WEEKSTART_MONDAY)

    def SetWeekStartSunday(self):
        """
        Définit le dimanche comme premier jour de la semaine dans le calendrier.
        """
        self._content.SetWeekStart(wxSCHEDULER_WEEKSTART_SUNDAY)

    # Rafraîchissements
    def RefreshAllItems(self, count):
        """
        Rafraîchit entièrement le contenu du calendrier avec un nombre d'éléments donnés.
        :param count: Nombre total d'éléments à afficher.
        """
        log.info(
            f"Calendar.RefreshAllItems : Rafraîchit entièrement le contenu du calendrier avec {count} éléments."
        )
        self._content.RefreshAllItems(count)
        log.info(
            f"Calendar.RefreshAllItems : Les {count} éléments du calendrier ont été rafraîchit !"
        )

    def RefreshItems(self, *args):
        """
        Rafraîchit une sélection d'éléments uniquement (optimisé).
        :param args: Identifiants ou objets à mettre à jour
        """
        log.info(
            f"Calendar.RefreshItems : Rafraîchit uniquement les éléments {args}."
        )
        self._content.RefreshItems(*args)
        log.info(
            f"Calendar.RefreshItems : Les éléments {args} sont rafraîchit ! Terminé !"
        )

    # Gestion de sélection
    def GetItemCount(self):
        """
        Retourne le nombre total d'éléments affichés dans le calendrier.
        :return: int
        """
        return self._content.GetItemCount()

    def curselection(self):
        """
        Retourne la sélection courante dans le calendrier.
        :return: liste ou élément sélectionné
        """
        return self._content.curselection()

    def select(self, tasks):
        """
        Sélectionne les tâches données dans l'interface graphique du calendrier.
        :param tasks: liste de tâches (1 seule ou plusieurs)
        """
        if len(tasks) == 1:
            self._content.SelectTask(tasks[0])
        else:
            self._content.Select(None)

    def isAnyItemCollapsable(self):
        """
        Indique que les éléments ne sont pas repliables dans ce type de vue.
        :return: False
        """
        return False

    def __getattr__(self, name):
        """
        Permet de déléguer dynamiquement l'accès aux attributs de `_CalendarContent`.

        Si un attribut est introuvable dans `Calendar`, il est recherché dans `_CalendarContent`.

        Ce mécanisme est utilisé pour exposer des méthodes/attributs internes du contenu
        tout en encapsulant la logique interne.

        :param name: Nom de l'attribut.
        :return: Valeur de l'attribut dans _content.
        :raises AttributeError: Si l'attribut n'existe pas.
        """
        # Ancien code :
        # return getattr(self._content, name)
        # Version adaptée pour Phoenix :
        content = self._content
        if hasattr(content, "_getAttrDict"):
            d = content._getAttrDict()
            if name in d:
                return d[name]
        #
        # if hasattr(self._content, "_getAttrDict") and (name in self._content._getAttrDict()):
        #         return self._content._getAttrDict()[name]
        return getattr(content, name)


class TaskSchedule(wxSchedule):
    """
    Représente une tâche de Task Coach comme un événement de calendrier pour wxScheduler.

    Cette classe hérite de wxSchedule et fournit une implémentation pour
    afficher et interagir avec les tâches dans une vue de calendrier.
    Elle gère l'affichage des propriétés de la tâche (sujet, dates, couleur,
    icônes, progression), la sélection visuelle, et les modifications de dates
    via glisser-déposer ou redimensionnement.
    """

    def __init__(self, task, iconProvider):
        """
        Initialise une instance de TaskSchedule.

        Args :
            task : L'objet tâche Task Coach à encapsuler.
            iconProvider : Un objet capable de fournir l'icône appropriée pour la tâche.
        """
        log.info(
            f"TaskSchedule.__init__ : Représente la tâche {task} comme un événement de calendrier pour wxScheduler."
        )
        super().__init__()  # Appelle le constructeur de la classe parente (wxSchedule).

        self.__selected = False  # Attribut privé pour suivre l'état de sélection de l'événement.

        self.clientdata = (
            task  # Stocke la tâche Task Coach réelle comme données client.
        )
        self.iconProvider = iconProvider  # Stocke le fournisseur d'icônes.
        self.update()  # Appelle la méthode update pour initialiser les propriétés d'affichage.
        log.info(f"TaskSchedule.__init__ : tâche {task} initialisée !")

    def SetSelected(self, selected):
        """
        Définit l'état de sélection de l'événement du calendrier et met à jour son apparence.

        Lorsqu'un événement est sélectionné, sa couleur de fond et de premier plan
        est ajustée pour donner un retour visuel à l'utilisateur.

        Args :
            selected (bool) : True si l'événement doit être sélectionné, False sinon.
        """
        self.Freeze()  # Gèle les mises à jour visuelles pour des performances accrues.
        try:
            self.__selected = (
                selected  # Met à jour l'état de sélection interne.
            )
            if selected:
                # Si sélectionné, utilise la couleur de surbrillance du système pour le fond.
                self.color = wx.SystemSettings.GetColour(
                    wx.SYS_COLOUR_HIGHLIGHT
                )
                # Sur Windows, la couleur de surbrillance est parfois très foncée.
                # Si la couleur de premier plan de la tâche est également foncée,
                # on l'inverse pour assurer la lisibilité du texte.
                color = self.task.foregroundColor(True) or (
                    0,
                    0,
                    0,
                )  # Récupère la couleur de texte de la tâche.
                if len(color) == 3:  # Gère les tuples (R,G,B) ou (R,G,B,A).
                    r, g, b = color
                else:
                    r, g, b, a = color
                if (
                    r + g + b < 128 * 3
                ):  # Si la somme des composantes est trop faible (couleur foncée).
                    self.foreground = wx.Colour(
                        255 - r, 255 - g, 255 - b
                    )  # Inverse la couleur.
                else:
                    # Si la couleur est claire, utilise la couleur d'origine.
                    self.foreground = wx.Colour(
                        *(self.task.foregroundColor(True) or (0, 0, 0))
                    )
            else:
                # Si non sélectionné, utilise les couleurs de fond et de premier plan de la tâche.
                self.color = wx.Colour(
                    *(self.task.backgroundColor(True) or (255, 255, 255))
                )
                self.foreground = wx.Colour(
                    *(self.task.foregroundColor(True) or (0, 0, 0))
                )
        finally:
            self.Thaw()  # Dégèle les mises à jour visuelles.

    def SetStart(self, start):
        """
        Définit la date/heure de début planifiée de la tâche associée.

        Utilise une commande d'édition pour modifier la date de début planifiée de la tâche,
        ce qui permet d'annuler/rétablir cette opération.

        Args:
            start (wx.DateTime): La nouvelle date/heure de début planifiée.
        """
        # Exécute une commande pour modifier la date de début planifiée de la tâche.
        # La date wx.DateTime est convertie en date.DateTime de Task Coach.
        command.EditPlannedStartDateTimeCommand(
            items=[self.task], newValue=self.tcDateTime(start)
        ).do()

    def SetEnd(self, end):
        """
        Définit la date/heure de fin de la tâche associée.

        Si la tâche est complétée, cela met à jour sa date de complétion.
        Sinon, cela met à jour sa date d'échéance.
        Utilise des commandes d'édition pour permettre l'annulation/rétablissement.

        Args:
            end (wx.DateTime): La nouvelle date/heure de fin.
        """
        if self.task.completed():
            # Si la tâche est complétée, modifie la date de complétion.
            command.EditCompletionDateTimeCommand(
                items=[self.task], newValue=self.tcDateTime(end)
            ).do()
        else:
            # Sinon, modifie la date d'échéance.
            command.EditDueDateTimeCommand(
                items=[self.task], newValue=self.tcDateTime(end)
            ).do()

    def Offset(self, ts):
        # kwargs = dict()
        """
        Déplace la tâche dans le temps d'une durée spécifiée.

        Cette méthode est utilisée pour le glisser-déposer d'événements
        sur le calendrier. Elle met à jour le date de début planifiée,
        de complétion ou d'échéance de la tâche en fonction du décalage temporel.

        Args :
            ts (wx.TimeSpan) : Le décalage temporel à appliquer.
        """
        kwargs = dict()  # Cette ligne n'est pas utilisée.

        # Si la tâche a une date de début planifiée.
        if self.task.plannedStartDateTime() != date.DateTime():
            start = (
                self.GetStart()
            )  # Récupère la date de début actuelle de l'événement wxSchedule.
            # start.AddTS(ts) # Ancienne syntaxe wx.DateTime pour ajouter un TimeSpan.
            # start.Add(ts)   # Ancienne syntaxe wx.DateTime.
            start += ts  # Ajoute le TimeSpan à la date de début.
            # Exécute une commande pour modifier la date de début planifiée de la tâche.
            command.EditPlannedStartDateTimeCommand(
                items=[self.task], newValue=self.tcDateTime(start)
            ).do()
        # Si la tâche est complétée.
        if self.task.completed():
            end = (
                self.GetEnd()
            )  # Récupère la date de fin actuelle de l'événement wxSchedule.
            # end.AddTS(ts) # Ancienne syntaxe.
            # end.Add(ts)   # Ancienne syntaxe.
            end += ts  # Ajoute le TimeSpan à la date de fin.
            # Exécute une commande pour modifier la date de complétion de la tâche.
            command.EditCompletionDateTimeCommand(
                items=[self.task], newValue=self.tcDateTime(end)
            ).do()
        # Sinon, si la tâche a une date d'échéance.
        elif self.task.dueDateTime() != date.DateTime():
            end = (
                self.GetEnd()
            )  # Récupère la date de fin actuelle de l'événement wxSchedule.
            # end.AddTS(ts) # Ancienne syntaxe.
            # end.Add(ts)   # Ancienne syntaxe.
            end += ts  # Ajoute le TimeSpan à la date de fin.
            # Exécute une commande pour modifier la date d'échéance de la tâche.
            command.EditDueDateTimeCommand(
                items=[self.task], newValue=self.tcDateTime(end)
            ).do()

    @property
    def task(self):
        """
        Propriété qui retourne l'objet tâche Task Coach sous-jacent.

        Récupère l'objet tâche associé à un objet wxSchedule donné.
        Permet d'accéder à la tâche directement via `self.task`.

        Returns :
            Task : L'objet tâche correspondant.
        """
        # Args:
        #     wxSchedule (wxSchedule): L'objet wxSchedule dont on veut la tâche.
        return (
            self.clientdata
        )  # La tâche est stockée dans l'attribut clientdata.
        # return wxSchedule.GetClientData()  # La tâche est stockée comme ClientData dans wxSchedule.

    def wxScheduleById(self, id):
        """
        Récupère l'objet wxSchedule par son ID wxSchedule.

        Args :
            id (int) : L'ID de l'objet wxSchedule.

        Returns :
            (wxSchedule) : L'objet wxSchedule correspondant.
        """
        return self._wxSchedulesById[
            id
        ]  # Retourne le wxSchedule à partir de son ID wxSchedule.

    def update(self):
        """
        Met à jour toutes les propriétés visuelles de l'événement wxSchedule
        en fonction de l'état actuel de la tâche associée.

        Cette méthode est appelée chaque fois que la tâche sous-jacente est modifiée
        afin que le calendrier puisse se rafraîchir et afficher les informations les plus récentes.
        """
        log.info(
            "TaskSchedule.update : Met à jour toutes les propriétés visuelles de l'événement wxSchedule en fonction de l'état actuel de la tâche associée."
        )
        self.Freeze()  # Gèle les mises à jour visuelles.
        try:
            self.description = (
                self.task.subject()
            )  # Le sujet de la tâche devient la description de l'événement.

            # Définit la date de début de l'événement.
            # Utilise la date de début planifiée de la tâche, ou le début du jour actuel comme défaut.
            self.start = self.wxDateTime(
                self.task.plannedStartDateTime(),
                self.tupleFromDateTime(date.Now().startOfDay()),
            )
            # Définit la date de fin de l'événement.
            # Utilise la date de complétion si la tâche est complétée, sinon la date d'échéance.
            # Si aucune n'est présente, utilise la fin du jour actuel comme défaut.
            end = (
                self.task.completionDateTime()
                if self.task.completed()
                else self.task.dueDateTime()
            )
            self.end = self.wxDateTime(
                end, self.tupleFromDateTime(date.Now().endOfDay())
            )

            if self.task.completed():
                self.done = True  # Indique que la tâche est terminée (peut influencer le rendu).

            # Définit les couleurs de fond et de premier plan de l'événement basées sur les couleurs de la tâche.
            self.color = wx.Colour(
                *(self.task.backgroundColor(True) or (255, 255, 255))
            )
            self.foreground = wx.Colour(
                *(self.task.foregroundColor(True) or (0, 0, 0))
            )
            # Définit la police de caractères basée sur la police de la tâche.
            self.font = self.task.font(True)

            self.icons = [
                self.iconProvider(self.task, False)
            ]  # Ajoute l'icône principale de la tâche.
            if self.task.attachments():
                self.icons.append(
                    "paperclip_icon"
                )  # Ajoute l'icône de pièce jointe si nécessaire.
            if self.task.notes():
                self.icons.append(
                    "note_icon"
                )  # Ajoute l'icône de note si nécessaire.

            # Calcule le pourcentage d'achèvement récursif de la tâche pour la barre de progression.
            if self.task.percentageComplete(recursive=True):
                # Si le pourcentage est 0, on laisse 'complete' à None pour ne pas dessiner la barre.
                # old_div est pour la compatibilité Python 2, en Python 3 la division est flottante par défaut.
                # self.complete = old_div(1.0 * self.task.percentageComplete(recursive=True), 100)
                self.complete = (
                    1.0
                    * self.task.percentageComplete(recursive=True)
                    / 100  # Convertit le pourcentage en une valeur entre 0.0 et 1.0.
                )
            else:
                self.complete = (
                    None  # Pas de barre de progression si aucun pourcentage.
                )
        finally:
            self.Thaw()  # Dégèle les mises à jour visuelles.
        log.info("TaskSchedule.update : Mise à jour terminée !")

    @staticmethod
    def tupleFromDateTime(dateTime):
        """
        Convertit un objet date.DateTime de Task Coach en un tuple de date/heure.

        Le format du tuple est (jour, mois-1, année, heure, minute, seconde)
        pour être compatible avec wx.DateTimeFromDMY.

        Args :
            dateTime (date.DateTime) : L'objet date.DateTime à convertir.

        Returns :
            (tuple) : Un tuple représentant la date et l'heure.
        """
        return (
            dateTime.day,  # Jour du mois.
            dateTime.month - 1,  # Mois (0-11 pour wxPython).
            dateTime.year,  # Année.
            dateTime.hour,  # Heure.
            dateTime.minute,  # Minute.
            dateTime.second,
        )  # Seconde.

    @staticmethod
    def wxDateTime(dateTime, default):
        """
        Convertit un objet date.DateTime de Task Coach en un objet wx.DateTime.

        Si l'objet date.DateTime est un objet date.DateTime() par défaut (vide),
        alors les valeurs par défaut fournies sont utilisées.

        Args :
            dateTime (date.DateTime) : L'objet date.DateTime à convertir.
            default (tuple) : Un tuple de valeurs par défaut si dateTime est vide.

        Returns :
            (wx.DateTime) : L'objet wx.DateTime converti.
        """
        # Utilise les valeurs par défaut si dateTime est l'objet DateTime() par défaut (vide).
        args = (
            default
            if dateTime == date.DateTime()
            else (
                dateTime.day,
                dateTime.month - 1,
                dateTime.year,
                dateTime.hour,
                dateTime.minute,
                dateTime.second,
            )
        )
        # Crée un objet wx.DateTime à partir du tuple d'arguments.
        return wx.DateTimeFromDMY(
            *args
        )  # pylint: disable=W0142  # L'unpacking d'args est standard.

    @staticmethod
    def tcDateTime(dateTime):
        """
        Convertit un objet wx.DateTime en un objet date.DateTime de Task Coach.

        Args :
            dateTime (wx.DateTime) : L'objet wx.DateTime à convertir.

        Returns :
            (date.DateTime) : L'objet date.DateTime converti.
        """
        # Crée un objet date.DateTime à partir des composants de wx.DateTime.
        # Note : Le mois de wx.DateTime est 0-indexé, donc on ajoute 1 pour Task Coach.
        return date.DateTime(
            dateTime.GetYear(),
            dateTime.GetMonth() + 1,  # Ajustement du mois.
            dateTime.GetDay(),
            dateTime.GetHour(),
            dateTime.GetMinute(),
            dateTime.GetSecond(),
        )
