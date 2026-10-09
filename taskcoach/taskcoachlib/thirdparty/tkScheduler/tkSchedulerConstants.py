#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de constantes pour la version Tkinter du planificateur (Scheduler).
Ce module remplace wxSchedulerConstants.py (version wxPython).

Il définit les constantes de configuration, les dimensions par défaut et
les fonctions permettant d’obtenir les couleurs système pour l’interface Tkinter.
"""

# Le fichier wxSchedulerConstants.py contient uniquement
# des constantes et fonctions utilitaires graphiques basées sur wx.SystemSettings et wx.Colour.
# Pour le convertir à Tkinter, on va :
#
# Remplacer wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
# par la couleur du fond système via tkinter.ttk.Style() ou root.cget("bg").
#
# Remplacer les wx.Colour par des tuples RGB ou des chaînes hexadécimales ("#rrggbb").
#
# Supprimer les objets wx.Size, qui deviennent simplement des tuples (largeur, hauteur).
#
# Supprimer les références à wx.LIGHT_GREY_PEN, remplacées par une couleur RGB équivalente.
#
# Laisser la journalisation intacte.

# Différences principales :
# Élément	        wxPython	                                        Tkinter
# Couleur système	wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)	root.cget("bg")
# Type de couleur	wx.Colour(r,g,b)	                                "#rrggbb"
# Taille	        wx.Size(x,y)	                                    (x, y)
# Crayon gris clair	wx.LIGHT_GREY_PEN	                                "#d3d3d3"

import logging  # Import du module pour la journalisation
import tkinter as tk  # Import du module Tkinter pour la GUI

# Création du logger du module
log = logging.getLogger(__name__)

# --- Informations générales ---
SCHEDULER_VERSION = "1.3"  # Version du module Scheduler

# --- Types de planification ---
SCHEDULER_DAILY = 1       # Vue quotidienne
SCHEDULER_WEEKLY = 2      # Vue hebdomadaire
SCHEDULER_MONTHLY = 3     # Vue mensuelle
SCHEDULER_TODAY = 4       # Vue du jour courant
SCHEDULER_TO_DAY = 5      # Vue jusqu’à aujourd’hui
SCHEDULER_PREV = 6        # Vue précédente
SCHEDULER_NEXT = 7        # Vue suivante
SCHEDULER_PREVIEW = 8     # Vue d’aperçu

# --- Jours de début de semaine ---
SCHEDULER_WEEKSTART_MONDAY = 1  # La semaine commence le lundi
SCHEDULER_WEEKSTART_SUNDAY = 0  # La semaine commence le dimanche


def _get_system_background_color() -> str:
    """
    Retourne la couleur de fond système de Tkinter.

    Returns:
        str: Couleur hexadécimale représentant la couleur de fond du système.
    """
    # Création d'une fenêtre temporaire Tk pour récupérer la couleur système
    # root = tk.Tk()
    Top_bg = tk.Toplevel()
    Top_bg.withdraw()  # Cache la fenêtre
    color = Top_bg.cget("bg")  # Récupère la couleur de fond système
    Top_bg.destroy()  # Détruit la fenêtre temporaire
    return color


def _adjust_color_brightness(color: str, delta: int = -15) -> str:
    """
    Ajuste la luminosité d’une couleur hexadécimale.

    Args:
        color (str): Couleur hexadécimale (ex: "#rrggbb").
        delta (int): Valeur d’ajustement (- pour assombrir, + pour éclaircir).

    Returns:
        str: Nouvelle couleur hexadécimale ajustée.
    """
    # Conversion hex -> RGB
    color = color.lstrip("#")
    r = max(0, min(255, int(color[0:2], 16) + delta))
    g = max(0, min(255, int(color[2:4], 16) + delta))
    b = max(0, min(255, int(color[4:6], 16) + delta))
    # Conversion RGB -> hex
    return f"#{r:02x}{g:02x}{b:02x}"


def SCHEDULER_BACKGROUND_BRUSH() -> str:
    """
    Définit et retourne la couleur de fond assombrie pour le planificateur.

    Returns:
        str: Couleur hexadécimale du fond du planificateur.
    """
    bg = _get_system_background_color()  # Obtient la couleur de fond système
    darker_bg = _adjust_color_brightness(bg, delta=-15)  # Assombrit la couleur
    log.debug(f"SCHEDULER_BACKGROUND_BRUSH renvoie la couleur {darker_bg}")
    return darker_bg  # Retourne la couleur ajustée


def DAY_BACKGROUND_BRUSH() -> str:
    """
    Retourne la couleur de fond des jours (non modifiée).

    Returns:
        str: Couleur hexadécimale du fond du jour.
    """
    bg = _get_system_background_color()  # Récupère la couleur du fond système
    log.debug(f"DAY_BACKGROUND_BRUSH renvoie la couleur {bg}")
    return bg


# --- Couleurs et styles ---
FOREGROUND_PEN = "#d3d3d3"  # Gris clair (équivalent à wx.LIGHT_GREY_PEN)

# --- Dimensions et marges ---
LEFT_COLUMN_SIZE = 50               # Largeur de la colonne de gauche
HEADER_COLUMN_SIZE = 20             # Hauteur de l’en-tête
DAY_SIZE_MIN = (400, 400)           # Taille minimale d’une journée
WEEK_SIZE_MIN = (980, 400)          # Taille minimale d’une semaine
MONTH_CELL_SIZE_MIN = (100, 100)    # Taille minimale d’une cellule de mois
SCHEDULE_INSIDE_MARGIN = 5          # Marge intérieure autour des éléments
SCHEDULE_OUTSIDE_MARGIN = 2         # Marge extérieure entre éléments
SCHEDULE_MAX_HEIGHT = 80            # Hauteur maximale d’un élément planifié

# --- Orientation ---
SCHEDULER_HORIZONTAL = 1  # Orientation horizontale
SCHEDULER_VERTICAL = 2    # Orientation verticale
