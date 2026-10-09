#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tkinter_schedule_utils
=============================

Ce module contient des fonctions utilitaires pour la gestion de temps et de dates,
initialement basées sur wxPython (wx.DateTime / wx.DateSpan), mais réécrites
pour utiliser le module standard `datetime` de Python, compatible avec Tkinter.

Contient :
- timeFunction : décorateur mesurant le temps d'exécution cumulé d'une fonction.
- copyDate : copie un objet date.
- copyDateTime : copie un objet datetime.
- setToWeekDayInSameWeek : calcule un jour précis de la même semaine qu’une date donnée.
"""
# Le fichier wxScheduleUtils.py que tu m’as fourni contient surtout des fonctions utilitaires indépendantes de l’interface graphique, sauf qu’elles utilisent wx.DateTime et wx.DateSpan, spécifiques à wxPython.
# Nous allons les convertir en fonctions équivalentes basées sur datetime de la bibliothèque standard Python, de manière compatible avec Tkinter.

# Modifications principales :
#
# wx.DateTime remplacé par datetime.datetime.
#
# wx.DateSpan(days=1) remplacé par timedelta(days=1).
#
# Conversion plus sûre pour copyDateTime() (gère les None).
#
# startDay suit la convention Python (0 = lundi).
#
# Ajout de docstrings et de commentaires explicatifs sur chaque ligne critique.

import atexit   # Pour exécuter une fonction automatiquement à la sortie du programme
import time     # Pour mesurer la durée d'exécution des fonctions
import traceback  # Pour obtenir la pile d'appels pour chaque fonction mesurée
from datetime import datetime, timedelta  # Pour remplacer wx.DateTime et wx.DateSpan


def timeFunction(func):
    """
    Décorateur : mesure et affiche la durée totale d’exécution d’une fonction.

    À la fin du programme, affiche le temps total cumulé pour chaque fonction
    décorée, ainsi que le nombre d’appels et la pile d’exécution associée.

    Args:
        func (callable): La fonction à mesurer.

    Returns:
        callable: Une fonction enveloppée qui mesure le temps d'exécution.
    """
    func.elapsed = dict()  # Dictionnaire pour stocker temps total et nombre d'appels par pile d'exécution

    def wrapper(*args, **kwargs):
        """Enveloppe la fonction pour mesurer le temps d'exécution."""
        t0 = time.time()  # On capture le temps de départ
        try:
            return func(*args, **kwargs)  # On exécute la fonction
        finally:
            # On capture la pile d'appels (limite courte pour ne pas polluer les logs)
            exc = "\n".join(traceback.format_stack(limit=2)[:-1])
            # On récupère les valeurs précédentes pour cette pile (temps total, nombre d'appels)
            elapsed, count = func.elapsed.get(exc, (0.0, 0))
            # On met à jour avec le temps écoulé sur cet appel
            func.elapsed[exc] = (elapsed + (time.time() - t0), count + 1)

    def printit():
        """Affiche un résumé à la fin de l'exécution du programme."""
        elapsed = [(tm, count, exc) for exc, (tm, count) in func.elapsed.items()]
        elapsed.sort()  # Trie par durée
        totalElapsed = 0.0
        totalCount = 0
        for tm, count, exc in elapsed:
            print("========== %d ms / %d appels" % (int(tm * 1000), count))
            print(exc)
            totalElapsed += tm
            totalCount += count
        print("===========")
        print("Temps total : %d ms" % int(totalElapsed * 1000))
        print("Nombre total d’appels : %d" % totalCount)

    # Enregistre la fonction printit à exécuter à la sortie du programme
    atexit.register(printit)

    return wrapper


def copyDate(value):
    """
    Crée une copie d'un objet `datetime.date` ou `datetime.datetime` en ne conservant que la date.

    Args:
        value (datetime | date): La valeur à copier.

    Returns:
        datetime.date: Une nouvelle date avec les mêmes valeurs de jour, mois et année.
    """
    # On reconstruit un objet date avec les mêmes valeurs
    return datetime(value.year, value.month, value.day).date()


def copyDateTime(value):
    """
    Retourne une copie d’un objet `datetime.datetime`.

    Si `value` est None ou invalide, retourne None.

    Args:
        value (datetime | None): L’objet datetime à copier.

    Returns:
        datetime | None: Une nouvelle instance identique, ou None.
    """
    # Si la valeur est absente, on renvoie None
    if value is None:
        return None
    # On retourne une nouvelle instance avec les mêmes champs
    return datetime(
        value.year,
        value.month,
        value.day,
        value.hour,
        value.minute,
        value.second,
        value.microsecond
    )


def setToWeekDayInSameWeek(day, offset, startDay=0):
    """
    Calcule la date correspondant à un jour précis de la même semaine qu’une date donnée.

    Remplace la fonction wx.DateTime.SetToWeekDayInSameWeek.

    Args:
        day (datetime): La date de départ.
        offset (int): Nombre de jours à ajouter après avoir trouvé le premier jour de la semaine.
        startDay (int): Jour de début de semaine (0=lundi, 6=dimanche). Par défaut : lundi.

    Returns:
        datetime: La date calculée correspondant au décalage dans la même semaine.
    """
    # On s'assure que day est bien un datetime (pas une date simple)
    if isinstance(day, datetime):
        current = day
    else:
        current = datetime(year=day.year, month=day.month, day=day.day)

    # Tant qu'on n'a pas trouvé le jour de début de semaine souhaité
    while current.weekday() != startDay:
        # On recule d'un jour
        current -= timedelta(days=1)

    # On ajoute ensuite l'offset demandé
    current += timedelta(days=offset)

    return current
