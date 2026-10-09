#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import warnings
import wx
import wx.lib.newevent
import time

from .wxScheduleUtils import copyDateTime

log = logging.getLogger(__name__)

# New event
wxEVT_COMMAND_SCHEDULE_CHANGE = wx.NewEventType()
EVT_SCHEDULE_CHANGE = wx.PyEventBinder(wxEVT_COMMAND_SCHEDULE_CHANGE)


# Constants


# class wxSchedule(wx.EvtHandler):
class wxSchedule(object):
    """
    Classe représentant un événement ou une planification, avec gestion de catégorie, couleur, période de début/fin, état d’achèvement, description et autres métadonnées.

    - Utilise les propriétés `start` et `end` pour définir le début et la fin de la planification.
    - Si les heures de début et de fin sont à 00:00, l’événement est considéré comme couvrant une ou plusieurs journées entières.
    - Supporte la notification d’événements lors des modifications (pattern observer via wx).
    - Permet de définir une catégorie, une couleur, une police, une description, un état "fait", des notes, des icônes et des données associées.
    - Fournit des méthodes pour sérialiser les données, cloner la planification, geler/dégeler les notifications, et comparer des instances.

    Propriétés principales :
        - category : Catégorie de l’événement (ex : Travail, Congé…)
        - color : Couleur associée
        - start, end : wx.DateTime de début et de fin
        - done : Booléen indiquant si la tâche est terminée
        - description, notes : Texte libre
        - icons, clientdata, complete, id : Métadonnées diverses

    Pour plus de détails, voir l’implémentation de chaque méthode.
    """

    SCHEDULE_DEFAULT_COLOR = wx.Colour(247, 212, 57)
    SCHEDULE_DEFAULT_FOREGROUND = wx.BLACK

    CATEGORIES = {
        "Work": wx.GREEN,
        "Holiday": wx.GREEN,
        "Phone": wx.GREEN,
        "Email": wx.GREEN,
        "Birthday": wx.GREEN,
        "Ill": wx.GREEN,
        "At home": wx.GREEN,
        "Fax": wx.GREEN,
    }

    # def __init__(self):
    def __init__(self, *args, **kwargs):
        # def __init__(self, parent=None, id=wx.ID_ANY, *args, **kwds):
        """
        Utilisez self.start et self.end pour définir le début et la fin du calendrier.
        Si les deux et la fin de DateTime ont du temps à 00:00
        Le calendrier est relatif sur toute la journée/jours.
        """
        # La chaîne d’héritage passe des arguments positionnels (parent, id, ...) tout du long.
        # Si une classe dans la chaîne ne les accepte pas, tu as "takes 1 positional argument but 3 were given".

        log.debug(
            f"wxSchedule.__init__ : self={self.__class__.__name__} avant super args={args}, kwargs={kwargs}"
        )
        # super(wxSchedule, self).__init__()
        # super().__init__()
        super().__init__(*args, **kwargs)
        # super().__init__(parent, id, *args, **kwds)

        log.debug("wxSchedule.__init__ : plante après cela !")
        self._color = self.SCHEDULE_DEFAULT_COLOR
        self._font = wx.NORMAL_FONT
        self._foreground = self.SCHEDULE_DEFAULT_FOREGROUND
        self._category = "Work"
        self._description = ""
        self._notes = ""
        self._end = wx.DateTime().Now()
        self._start = wx.DateTime().Now()
        self._done = False
        self._clientdata = None
        self._icons = []
        self._complete = None
        # self._id = "%.f-%s" % (time.time(), id(self))
        self._id = f"{time.time():f}-{id(self)}"

        # Need for freeze the event notification
        self._freeze = False
        self._layoutNeeded = False
        self.passed = 0
        log.info("wxSchedule initialisé !")

    def __getattr__(self, name):
        # Gestion des attributs Phoenix si présent
        self.passed += 1  # gestion de boucle infinie sur hasattr
        # if hasattr(self, "_getAttrDict"):
        if 0 < self.passed < 2 and hasattr(self, "_getAttrDict"):
            d = self._getAttrDict()
            if name in d:
                return d[name]

        # Gère la rétrocompatibilité des anciens getters/setters.
        if name[:3] in ["get", "set"]:
            warnings.warn(
                "getData() is deprecated, use GetData() instead",
                DeprecationWarning,
                stacklevel=2,
            )

            name = name[0].upper() + name[1:]
            return getattr(self, name)

        raise AttributeError(name)

    # Global methods
    def Freeze(self):
        # Freeze the event notification
        self._freeze = True
        self._layoutNeeded = False

    def Thaw(self):
        # Wake up the event
        self._freeze = False
        self._eventNotification(self._layoutNeeded)

    def GetData(self):
        """
        Retourne les données du wxSchedule sous forme de dictionnaire.
        """
        attributes = [
            "category",
            "color",
            "font",
            "foreground",
            "description",
            "done",
            "end",
            "notes",
            "start",
            "clientdata",
            "icons",
            "complete",
            "id",
        ]
        data = dict()

        for attribute in attributes:
            data[attribute] = self.__getattribute__(attribute)

        return data

    def Clone(self):
        # Clone l'objet wxSchedule.
        newSchedule = wxSchedule()
        for name, value in self.GetData().items():
            setattr(newSchedule, name, value)
        # Le début et la fin doivent également être copiés
        newSchedule._start = copyDateTime(newSchedule._start)
        newSchedule._end = copyDateTime(newSchedule._end)
        return newSchedule

    # Internal methods

    def _eventNotification(self, layoutNeeded=False):
        """Si non gelé (freeze), réveille et déclenche la notification d'événement."""
        if self._freeze:
            self._layoutNeeded = self._layoutNeeded or layoutNeeded
            return

        # Crée l'événement et le propage.
        evt = wx.PyCommandEvent(wxEVT_COMMAND_SCHEDULE_CHANGE)

        evt.category = self._category
        evt.color = self._color
        evt.font = self._font
        evt.foreground = self._foreground
        evt.description = self._description
        evt.done = self._done
        evt.end = self._end
        evt.notes = self._notes
        evt.start = self._start
        evt.icons = self._icons
        evt.complete = self._complete
        evt.schedule = self
        evt.layoutNeeded = layoutNeeded

        evt.SetEventObject(self)

        self.ProcessEvent(evt)

    def __eq__(self, schedule):
        """
        Contrôle si le wxSchedule passé est égal à l'instance courante.
        """
        # Is not a wxSchedule
        if not isinstance(schedule, wxSchedule):
            return False

        # Check wxSchedules attributes
        return self.GetData() == schedule.GetData()

    # Properties
    def SetCategory(self, category):
        """
        Définit la catégorie.
        """
        if category not in self.CATEGORIES.keys():
            raise ValueError("%s is not a valid category" % category)

        self._category = category
        self._eventNotification()

    def GetCategory(self):
        """
        Retourne la catégorie courante.
        """
        return self._category

    def SetColor(self, color):
        """
        Définit la couleur.
        """
        if not isinstance(color, wx.Colour):
            raise ValueError("Color can be only a wx.Colour value")

        self._color = color
        self._eventNotification()

    def GetColor(self):
        """
        Retourne la couleur.
        """
        return self._color

    def SetFont(self, font):
        """
        Définit la police de caractère.
        """

        if font is None:
            self._font = wx.NORMAL_FONT
        else:
            self._font = font

        self._eventNotification()

    def GetFont(self):
        """
        Retourne la police de caractère.
        """
        return self._font

    def SetForeground(self, color):
        """
        Définit la couleur du texte.
        """
        self._foreground = color

    def GetForeground(self):
        """
        Retourne la couleur du texte.
        """
        return self._foreground

    def SetDescription(self, description):
        """
        Définit la description de la planification.
        """
        if not isinstance(description, str):
            raise ValueError("Description can be only a str value")

        self._description = description
        self._eventNotification(True)

    def GetDescription(self):
        """
        Retourne la description de la planification.
        """
        return self._description

    def SetDone(self, done):
        """
        Règle si la planification est terminée.
        """
        if not isinstance(done, bool):
            raise ValueError("Done can be only a bool value")

        self._done = done
        self._eventNotification()

    def GetDone(self):
        """
        Retourne l'état d'achèvement (fait ou non).
        """
        return self._done

    def SetEnd(self, dtEnd):
        """
        Définit la date/heure de fin.
        """
        if not isinstance(dtEnd, wx.DateTime):
            raise ValueError("dateTime can be only a wx.DateTime value")

        self._end = dtEnd
        self._eventNotification(True)

    def GetEnd(self):
        """
        Retourne la date/heure de fin.
        """
        return self._end

    def SetNotes(self, notes):
        """
        Définit les notes associées.
        """
        if not isinstance(notes, str):
            raise ValueError("notes can be only a str value")

        self._notes = notes
        self._eventNotification()

    def GetNotes(self):
        """
        Retourne les notes associées.
        """
        return self._notes

    def SetStart(self, dtStart):
        """Définit la date/heure de début."""
        if not isinstance(dtStart, wx.DateTime):
            raise ValueError("dateTime can be only a wx.DateTime value")

        self._start = dtStart
        self._eventNotification(True)

    def GetStart(self):
        """
        Retourne la date/heure de début.
        """
        return self._start

    def Offset(self, ts):
        """
        Décale la planification du laps de temps indiqué.

        Args :
            ts :
        """
        # self._start.AddTS(ts)
        self._start += ts
        # self._end.AddTS(ts)
        self._end += ts
        self._eventNotification(True)

    def GetIcons(self):
        return self._icons

    def SetIcons(self, icons):
        layoutNeeded = (bool(icons) and not bool(self._icons)) or (
            bool(self._icons) and not bool(icons)
        )
        self._icons = icons

        self._eventNotification(layoutNeeded)

    def GetComplete(self):
        return self._complete

    def SetComplete(self, complete):
        layoutNeeded = (self._complete is None and complete is not None) or (
            self._complete is not None and complete is None
        )
        self._complete = complete
        self._eventNotification(layoutNeeded)

    def SetClientData(self, clientdata):
        self._clientdata = clientdata

    def GetClientData(self):
        return self._clientdata

    def SetId(self, id_):
        self._id = id_

    def GetId(self):
        return self._id

    category = property(GetCategory, SetCategory)
    color = property(GetColor, SetColor)
    font = property(GetFont, SetFont)
    foreground = property(GetForeground, SetForeground)
    description = property(GetDescription, SetDescription)
    done = property(GetDone, SetDone)
    start = property(GetStart, SetStart)
    end = property(GetEnd, SetEnd)
    notes = property(GetNotes, SetNotes)
    clientdata = property(GetClientData, SetClientData)
    icons = property(GetIcons, SetIcons)
    complete = property(GetComplete, SetComplete)
    id = property(GetId, SetId)
