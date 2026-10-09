#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tkTimeFormat
===================

Ce module définit une classe singleton pour formater les heures dans
l'application Tkinter. Il remplace la dépendance à wx.DateTime.Format()
par l'utilisation du module standard datetime de Python.

Ce module est conçu pour être compatible avec TaskCoach converti en Tkinter.
"""
# Différences principales avec la version wxPython :
# Élément	Ancienne version (wx)	Nouvelle version (tkinter/pure Python)
# Dépendance	import wx	from datetime import datetime
# Formatage	dt.Format("%H:%M")	dt.strftime("%H:%M")
# Classe	wxTimeFormat	TkTimeFormat
# Instance globale	wxTimeFormat = wxTimeFormat()	tkTimeFormat = TkTimeFormat()

from datetime import datetime


class TkTimeFormat:
    """
    Singleton utilisé pour formater les heures dans l'application.

    Il fournit une fonction par défaut qui retourne une chaîne représentant
    une heure donnée, avec ou sans les minutes. Cette fonction peut être
    redéfinie par l'utilisateur via `SetFormatFunction()`.
    """

    def __init__(self):
        """
        Initialise la fonction de formatage par défaut.
        """

        def defaultFormat(dt: datetime, includeMinutes: bool = False) -> str:
            """
            Définit le format de l'heure par défaut pour l'affichage.

            Args:
                dt (datetime): Heure à afficher.
                includeMinutes (bool): Si True, inclut les minutes dans l'affichage.

            Returns:
                str: Heure formatée selon le choix de l'utilisateur.
            """
            # Si l'utilisateur souhaite inclure les minutes
            if includeMinutes:
                return dt.strftime("%H:%M")  # Format HH:MM (ex: 14:35)
            # Sinon, afficher uniquement l'heure entière
            return dt.strftime("%H")  # Format HH (ex: 14)

        # Enregistre la fonction de formatage par défaut
        self.__fmt = defaultFormat

    def FormatTime(self, dateTime: datetime, includeMinutes: bool = False) -> str:
        """
        Retourne l'heure au format défini (par défaut ou personnalisé).

        Args:
            dateTime (datetime): Heure à afficher.
            includeMinutes (bool): Si True, inclut les minutes dans le format.

        Returns:
            str: Heure formatée.
        """
        # Appelle la fonction de formatage actuelle (__fmt)
        return self.__fmt(dateTime, includeMinutes=includeMinutes)

    def SetFormatFunction(self, func):
        """
        Définit une nouvelle fonction personnalisée de formatage de l'heure.

        Args:
            func (Callable[[datetime, bool], str]): Fonction de formatage à utiliser.
        """
        # Met à jour la fonction de formatage utilisée par le singleton
        self.__fmt = func


# Instancie le singleton global comme dans la version wx
tkTimeFormat = TkTimeFormat()
