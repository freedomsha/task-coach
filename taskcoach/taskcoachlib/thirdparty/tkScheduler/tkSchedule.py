#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# J'ai converti le fichier wxSchedule.py pour Tkinter.
# Voici les principaux changements :
# Remplacements wxPython → Tkinter/Python standard :
#
# wx.DateTime → datetime.datetime
# wx.Colour → codes hexadécimaux (ex: #F7D439)
# wx.BLACK, wx.GREEN → codes hex
# wx.NORMAL_FONT → "TkDefaultFont"
# Événements wxPython → système de callbacks personnalisé
#
# Nouvelles méthodes pour Tkinter :
#
# bind(callback) : Enregistre un callback pour les notifications
# unbind(callback) : Désenregistre un callback
#
# Autres changements :
#
# Import de datetime et timedelta au lieu de wx
# Le système d'événements wxPython remplacé par des callbacks simples
# La méthode Offset() utilise maintenant timedelta au lieu de wx.DateSpan
# Les propriétés de couleur utilisent des strings hexadécimales
# Amélioration des messages d'erreur avec f-strings
#
# Le code conserve la même structure et logique que l'original,
# ce qui facilite la portabilité.
import logging
import warnings
import time
from datetime import datetime, timedelta
from tkinter import Event

from .tkScheduleUtils import copyDateTime

log = logging.getLogger(__name__)

# Constants for event handling
EVT_SCHEDULE_CHANGE = "<<ScheduleChange>>"

# Event type identifiers
SCHEDULE_CHANGED = "schedule_changed"


class tkSchedule(object):
    """
    Classe représentant un événement ou une planification, avec gestion de catégorie, couleur,
    période de début/fin, état d'achèvement, description et autres métadonnées.

    - Utilise les propriétés `start` et `end` pour définir le début et la fin de la planification.
    - Si les heures de début et de fin sont à 00:00, l'événement est considéré comme couvrant
      une ou plusieurs journées entières.
    - Supporte la notification d'événements lors des modifications (pattern observer via Tkinter).
    - Permet de définir une catégorie, une couleur, une police, une description, un état "fait",
      des notes, des icônes et des données associées.
    - Fournit des méthodes pour sérialiser les données, cloner la planification, geler/dégeler
      les notifications, et comparer des instances.

    Propriétés principales :
        - category : Catégorie de l'événement (ex : Travail, Congé…)
        - color : Couleur associée (code hexadécimal ou nom)
        - start, end : datetime de début et de fin
        - done : Booléen indiquant si la tâche est terminée
        - description, notes : Texte libre
        - icons, clientdata, complete, id : Métadonnées diverses

    Pour plus de détails, voir l'implémentation de chaque méthode.
    """
    SCHEDULE_DEFAULT_COLOR = "#F7D439"  # Jaune (remplace wx.Colour(247, 212, 57))
    SCHEDULE_DEFAULT_FOREGROUND = "#000000"  # Noir (remplace wx.BLACK)

    CATEGORIES = {
        "Work": "#00AA00",
        "Holiday": "#00AA00",
        "Phone": "#00AA00",
        "Email": "#00AA00",
        "Birthday": "#00AA00",
        "Ill": "#00AA00",
        "At home": "#00AA00",
        "Fax": "#00AA00",
    }

    def __init__(self, *args, **kwargs):
        """
        Initialisez la planification.

        Utilisez self.start et self.end pour définir le début et la fin du calendrier.
        Si les deux datetime de début et fin ont du temps à 00:00,
        le calendrier est relatif sur toute la journée/jours.
        """
        log.debug(f"tkSchedule.__init__ : self={self.__class__.__name__} avant init args={args}, kwargs={kwargs}")

        # Initialise les callbacks pour les événements
        self._event_callbacks = []

        log.debug("tkSchedule.__init__ : initialisation complétée")

        self._color = self.SCHEDULE_DEFAULT_COLOR
        self._font = "TkDefaultFont"  # Police par défaut Tkinter
        self._foreground = self.SCHEDULE_DEFAULT_FOREGROUND
        self._category = "Work"
        self._description = ""
        self._notes = ""
        self._end = datetime.now()
        self._start = datetime.now()
        self._done = False
        self._clientdata = None
        self._icons = []
        self._complete = None
        self._id = f"{time.time():f}-{id(self)}"

        # Gestion du gel des notifications d'événements
        self._freeze = False
        self._layoutNeeded = False
        self.passed = 0

        log.info("tkSchedule initialisé !")

    def __getattr__(self, name):
        """Gère les attributs manquants et la rétrocompatibilité des anciens getters/setters."""
        self.passed += 1  # Gestion de boucle infinie sur hasattr

        if 0 < self.passed < 2:
            # Tentative de récupération via _getAttrDict si disponible
            if hasattr(self, "_getAttrDict"):
                d = self._getAttrDict()
                if name in d:
                    return d[name]

        # Gère la rétrocompatibilité des anciens getters/setters (camelCase -> PascalCase)
        if name[:3] in ["get", "set"]:
            warnings.warn(
                f"{name}() is deprecated, use {name[0].upper() + name[1:]}() instead",
                DeprecationWarning,
                stacklevel=2,
            )
            name = name[0].upper() + name[1:]
            return getattr(self, name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # Global methods
    def Freeze(self):
        """Gèle les notifications d'événements."""
        self._freeze = True
        self._layoutNeeded = False

    def Thaw(self):
        """Déverrouille les notifications d'événements et envoie les notifications en attente."""
        self._freeze = False
        self._eventNotification(self._layoutNeeded)

    def GetData(self):
        """
        Retourne les données du tkSchedule sous forme de dictionnaire.
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
        """Clone l'objet tkSchedule."""
        newSchedule = tkSchedule()
        for name, value in self.GetData().items():
            setattr(newSchedule, name, value)
        # Le début et la fin doivent également être copiés
        newSchedule._start = copyDateTime(newSchedule._start)
        newSchedule._end = copyDateTime(newSchedule._end)
        return newSchedule

    # Internal methods

    def _eventNotification(self, layoutNeeded=False):
        """
        Si non gelée (freeze), déclenche la notification d'événement.

        Appelle tous les callbacks enregistrés avec les données mises à jour.
        """
        if self._freeze:
            self._layoutNeeded = self._layoutNeeded or layoutNeeded
            return

        # Crée un dictionnaire d'événement avec toutes les données
        event_data = {
            "category": self._category,
            "color": self._color,
            "font": self._font,
            "foreground": self._foreground,
            "description": self._description,
            "done": self._done,
            "end": self._end,
            "notes": self._notes,
            "start": self._start,
            "icons": self._icons,
            "complete": self._complete,
            "schedule": self,
            "layoutNeeded": layoutNeeded,
            "type": SCHEDULE_CHANGED,
        }

        # Appelle tous les callbacks enregistrés
        for callback in self._event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                log.error(f"Erreur lors de l'appel du callback : {e}", exc_info=True)

    def bind_callback(self, callback):
        """
        Enregistre un callback pour les notifications d'événements.

        Args:
            callback : Fonction appelée avec le dictionnaire d'événement en paramètre.
        """
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)

    def unbind_callback(self, callback):
        """
        Désenregistre un callback.

        Args:
            callback : La fonction à désenregistrer.
        """
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def __eq__(self, schedule):
        """
        Contrôle si le tkSchedule passé est égal à l'instance courante.
        """
        # N'est pas un tkSchedule
        if not isinstance(schedule, tkSchedule):
            return False

        # Compare les attributs
        return self.GetData() == schedule.GetData()

    # Properties
    def SetCategory(self, category):
        """Définit la catégorie."""
        if category not in self.CATEGORIES.keys():
            raise ValueError(f"{category} is not a valid category")

        self._category = category
        self._eventNotification()

    def GetCategory(self):
        """Retourne la catégorie courante."""
        return self._category

    def SetColor(self, color):
        """
        Définit la couleur.

        Args:
            color : Code hexadécimal (#RRGGBB) ou nom de couleur (str).
        """
        if not isinstance(color, str):
            raise ValueError("Color must be a string (hex code or color name)")

        self._color = color
        self._eventNotification()

    def GetColor(self):
        """Retourne la couleur."""
        return self._color

    def SetFont(self, font):
        """Définit la police de caractère."""
        if font is None:
            self._font = "TkDefaultFont"
        else:
            self._font = font

        self._eventNotification()

    def GetFont(self):
        """Retourne la police de caractère."""
        return self._font

    def SetForeground(self, color):
        """Définit la couleur du texte."""
        if not isinstance(color, str):
            raise ValueError("Foreground must be a string (hex code or color name)")

        self._foreground = color

    def GetForeground(self):
        """Retourne la couleur du texte."""
        return self._foreground

    def SetDescription(self, description):
        """Définit la description de la planification."""
        if not isinstance(description, str):
            raise ValueError("Description must be a string")

        self._description = description
        self._eventNotification(True)

    def GetDescription(self):
        """Retourne la description de la planification."""
        return self._description

    def SetDone(self, done):
        """Règle si la planification est terminée."""
        if not isinstance(done, bool):
            raise ValueError("Done must be a boolean value")

        self._done = done
        self._eventNotification()

    def GetDone(self):
        """Retourne l'état d'achèvement (fait ou non)."""
        return self._done

    def SetEnd(self, dtEnd):
        """Définit la date/heure de fin."""
        if not isinstance(dtEnd, datetime):
            raise ValueError("dtEnd must be a datetime.datetime value")

        self._end = dtEnd
        self._eventNotification(True)

    def GetEnd(self):
        """Retourne la date/heure de fin."""
        return self._end

    def SetNotes(self, notes):
        """Définit les notes associées."""
        if not isinstance(notes, str):
            raise ValueError("notes must be a string value")

        self._notes = notes
        self._eventNotification()

    def GetNotes(self):
        """Retourne les notes associées."""
        return self._notes

    def SetStart(self, dtStart):
        """Définit la date/heure de début."""
        if not isinstance(dtStart, datetime):
            raise ValueError("dtStart must be a datetime.datetime value")

        self._start = dtStart
        self._eventNotification(True)

    def GetStart(self):
        """Retourne la date/heure de début."""
        return self._start

    def Offset(self, ts):
        """
        Décale la planification du laps de temps indiqué.

        Args:
            ts (timedelta): L'intervalle de temps à ajouter.
        """
        if not isinstance(ts, timedelta):
            raise ValueError("ts must be a timedelta value")

        self._start += ts
        self._end += ts
        self._eventNotification(True)

    def GetIcons(self):
        """Retourne la liste des icônes."""
        return self._icons

    def SetIcons(self, icons):
        """Définit la liste des icônes."""
        layoutNeeded = (bool(icons) and not bool(self._icons)) or (
                bool(self._icons) and not bool(icons)
        )
        self._icons = icons

        self._eventNotification(layoutNeeded)

    def GetComplete(self):
        """Retourne l'état de complétude."""
        return self._complete

    def SetComplete(self, complete):
        """Définit l'état de complétude."""
        layoutNeeded = (self._complete is None and complete is not None) or (
                self._complete is not None and complete is None
        )
        self._complete = complete
        self._eventNotification(layoutNeeded)

    def SetClientData(self, clientdata):
        """Définit les données clients."""
        self._clientdata = clientdata

    def GetClientData(self):
        """Retourne les données clients."""
        return self._clientdata

    def SetId(self, id_):
        """Définit l'identifiant unique."""
        self._id = id_

    def GetId(self):
        """Retourne l'identifiant unique."""
        return self._id

    # Propriétés Python
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