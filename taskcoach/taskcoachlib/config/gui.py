# taskcoachlib/config/gui.py

"""
Configuration du backend graphique utilisé par TaskCoach.

Ce module est le SEUL endroit qui connaît le GUI actif.
"""

from taskcoachlib.config.arguments import get_gui  # Récupère l'argument CLI

# Nom du GUI actif ("wx" ou "tk")
GUI_NAME = get_gui()
