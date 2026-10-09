#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx


class wxTimeFormat(object):
    """Singleton used to format times."""

    def __init__(self):
        def defaultFormat(dt, includeMinutes=False):
            """
            Définit le format de l'heure par défaut de l'affichage.

            Args :
                dt : Heure à afficher.
                includeMinutes (bool) : Affiche les minutes oui ou non.

            Returns :
                L'heure au format choisi, avec ou sans les minutes (par défaut).
            """
            if includeMinutes:
                return dt.Format("%H:%M")
            return dt.Format("%H")

        self.__fmt = defaultFormat

    def FormatTime(self, dateTime, includeMinutes=False):
        """
        Retourne l'heure au format défini par défaut (avec ou sans les minutes).

        Args :
            dateTime : L'heure à afficher.
            includeMinutes : Avec ou sans les minutes.

        Returns :
            self.__fmt() :
        """
        return self.__fmt(dateTime, includeMinutes=includeMinutes)

    def SetFormatFunction(self, func):
        """
        Règle la fonction de gestion du format de l'heure.

        Args :
            func : Fonction de gestion du format de l'heure à utiliser.
        """
        self.__fmt = func


wxTimeFormat = wxTimeFormat()
