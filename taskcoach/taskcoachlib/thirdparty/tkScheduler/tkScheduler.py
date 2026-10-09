#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module tkScheduler
==================

Ce module fournit la classe principale `tkScheduler`, le widget de planification
visuel et interactif pour Tkinter. Il a été converti depuis la version wxPython.

Il combine la logique de `tkSchedulerCore` et le dessin de `tkSchedulerPaint`
dans un widget complet avec des barres de défilement.

Fonctionnalités principales :
- Affiche un planning journalier, hebdomadaire ou mensuel.
- Permet l'interaction utilisateur (clic, glisser-déposer).
- Gère le défilement lorsque le contenu dépasse la zone visible.
- Met à jour automatiquement l'indicateur de l'heure actuelle.
"""
# C'est la dernière pièce du puzzle qui rassemble toute la logique (tkSchedulerCore) et le dessin (tkSchedulerPaint) dans un widget interactif et visible pour l'utilisateur.
#
# La conversion de wxScheduler.py est particulièrement intéressante car elle ne se contente pas de remplacer des fonctions, elle change la structure même du composant.
#
# La logique de la conversion
#
#     Le défi principal : scrolled.ScrolledPanel : wxPython offre un panneau à défilement très pratique. En Tkinter, il n'y a pas d'équivalent direct. Nous devons le construire nous-mêmes en combinant trois widgets :
#
#         Un tkinter.Frame qui servira de conteneur principal.
#
#         Un tkinter.Canvas sur lequel tout sera dessiné. C'est le cœur de notre composant.
#
#         Des tkinter.Scrollbar (barres de défilement) que nous lions au canevas.
#
#     Héritage : La nouvelle classe tkScheduler héritera de tk.Frame (pour être un widget) et de tkSchedulerCore (pour avoir toute la logique de gestion).
#
#     Timers et Événements :
#
#         wx.Timer est remplacé par la méthode widget.after() de Tkinter, qui permet de programmer l'exécution d'une fonction après un certain délai. C'est parfait pour les rafraîchissements périodiques et les redimensionnements différés.
#
#         Les événements wx.EVT_* sont remplacés par des liaisons d'événements Tkinter avec la méthode .bind(), comme <Configure> pour le redimensionnement (OnSize) ou <Button-1> pour un clic.
#
#     La méthode Refresh : Son rôle devient encore plus crucial. En plus de redessiner, elle doit calculer la taille totale nécessaire pour afficher tout le contenu (la "taille virtuelle") et mettre à jour la scrollregion du canevas. C'est cette étape qui indique aux barres de défilement jusqu'où elles peuvent aller.

import logging
import time
import tkinter as tk
from tkinter import ttk

from taskcoachlib.thirdparty.tkScheduler.tkSchedulerCore import tkSchedulerCore
from taskcoachlib.thirdparty.tkScheduler import tkSchedule

log = logging.getLogger(__name__)


class tkScheduler(tkSchedulerCore, tk.Frame):
    """
    Le widget principal du planificateur pour Tkinter.

    Combine un canevas pour le dessin et des barres de défilement dans un cadre.
    Hérite de tkSchedulerCore pour toute la logique de gestion des données et
    des interactions.
    """
    def __init__(self, master, *args, **kwds):
        """
        Initialise le widget de planification.

        Args:
            master: Le widget parent Tkinter.
        """
        # 1. Initialiser le Frame Tkinter
        tk.Frame.__init__(self, master, *args, **kwds)

        # 2. Créer la structure du widget (Canevas + Barres de défilement)
        self._create_widgets()

        # 3. Initialiser la logique du planificateur (tkSchedulerCore)
        #    On lui passe le canevas sur lequel il doit dessiner.
        tkSchedulerCore.__init__(self, self.canvas)

        # 4. Lier les événements Tkinter aux gestionnaires
        self._bind_events()

        # --- Variables de contrôle ---
        self._size_timer_id = None
        self._refresh_timer_id = None
        self._showNow = True
        self.Refresh() # Premier dessin
        self._start_refresh_timer()

        log.info("tkScheduler initialisé !")

    def _create_widgets(self):
        """Crée et positionne le canevas et les barres de défilement."""
        # Grille de configuration pour que le canevas s'étende
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Création du canevas
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Barres de défilement
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Lier les barres de défilement au canevas
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    def _bind_events(self):
        """Lie les événements du widget aux méthodes de gestion."""
        # Le redimensionnement du widget est géré par l'événement <Configure>
        self.bind("<Configure>", self.OnSize)

        # Le timer de rafraîchissement est géré par la méthode 'after'
        # Les événements de souris sont déjà liés dans tkSchedulerPaint sur le canevas

    # --- Gestionnaires d'événements ---

    def OnSize(self, event=None):
        """
        Gère le redimensionnement du widget.
        Utilise un timer pour ne pas redessiner trop souvent (debouncing).
        """
        # Annule le précédent appel au timer s'il existe
        if self._size_timer_id:
            self.after_cancel(self._size_timer_id)

        # Programme un rafraîchissement après 250ms d'inactivité
        self._size_timer_id = self.after(250, self.Refresh)

    def _start_refresh_timer(self):
        """Démarre le timer qui rafraîchit l'indicateur 'maintenant'."""
        if not self._showNow:
            return

        # Calcule le nombre de millisecondes avant la prochaine minute
        seconds_to_next_minute = 60 - (time.time() % 60)

        self._refresh_timer_id = self.after(int(seconds_to_next_minute * 1000), self._on_refresh_timer)

    def _on_refresh_timer(self):
        """
        Appelé toutes les minutes pour rafraîchir l'affichage et
        reprogrammer le prochain appel.
        """
        self.Refresh()
        # Reprogramme le timer pour dans 60 secondes
        if self._showNow:
            self._refresh_timer_id = self.after(60000, self._on_refresh_timer)

    # --- Méthodes publiques surchargées ---

    def Refresh(self):
        """
        Rafraîchit l'affichage du planning.
        Calcule la taille virtuelle, met à jour la zone de défilement et redessine.
        """
        log.info("tkScheduler.Refresh : Rafraîchissement de l'affichage.")

        # Calcule la taille minimale requise pour afficher tout le contenu
        # Note : Cette logique de calcul doit être dans DoPaint ou une méthode dédiée.
        # Pour l'instant, utilisons une taille fixe ou calculée dans DoPaint.
        # Ici, nous supposons que DrawBuffer met à jour une taille virtuelle.

        # Appel de la méthode de dessin de la classe parente
        super().Refresh()

        # Met à jour la zone de défilement du canevas.
        # 'bbox("all")' retourne le rectangle englobant tous les items dessinés.
        scroll_region = self.canvas.bbox("all")
        if scroll_region:
            self.canvas.config(scrollregion=scroll_region)

        log.info("tkScheduler.Refresh : Affichage rafraîchi.")

    def SetViewType(self, view=None):
        """Change le type de vue et rafraîchit l'affichage."""
        super().SetViewType(view)
        self.Refresh()

    def SetShowNow(self, show=True):
        """Affiche ou masque l'indicateur de l'heure courante."""
        self._showNow = show
        if self._refresh_timer_id:
            self.after_cancel(self._refresh_timer_id)
            self._refresh_timer_id = None

        if show:
            self._start_refresh_timer()

        self.Refresh()

    def GetShowNow(self):
        """Indique si l'heure courante est affichée."""
        return self._showNow

# # Comment l'utiliser ?
# import tkinter as tk
# from datetime import datetime, timedelta
#
# # Supposons que tous vos fichiers (tkScheduler.py, tkSchedule.py, etc.)
# # se trouvent dans un dossier nommé "scheduler_lib"
# # from taskcoachlib.thirdparty.tkScheduler.tkScheduler import tkScheduler
# from taskcoachlib.thirdparty.tkScheduler.tkSchedule import tkSchedule
# from taskcoachlib.thirdparty.tkScheduler.tkSchedulerConstants import SCHEDULER_WEEKLY, SCHEDULER_MONTHLY
#
# # --- Fenêtre principale de l'application ---
# root = tk.Tk()
# root.title("Mon Planificateur Tkinter")
# root.geometry("1024x768")
#
# # --- Création du widget Scheduler ---
# scheduler_widget = tkScheduler(root, bg="lightgrey")
# scheduler_widget.pack(fill="both", expand=True, padx=10, pady=10)
#
# # --- Ajout de quelques événements pour la démonstration ---
# now = datetime.now()
# event1 = tkSchedule()
# event1.start = now.replace(hour=10, minute=0)
# event1.end = now.replace(hour=11, minute=30)
# event1.description = "Réunion de projet"
# event1.color = "#FFDDC1" # Couleur pastel
#
# event2 = tkSchedule()
# event2.start = now.replace(hour=14, minute=0) + timedelta(days=1)
# event2.end = now.replace(hour=15, minute=0) + timedelta(days=1)
# event2.description = "Rendez-vous dentiste"
# event2.color = "#C1FFD7"
#
# scheduler_widget.Add([event1, event2])
#
#
# # --- Ajout de boutons pour changer de vue ---
# def set_weekly_view():
#     scheduler_widget.SetViewType(SCHEDULER_WEEKLY)
#
# def set_monthly_view():
#     scheduler_widget.SetViewType(SCHEDULER_MONTHLY)
#
# button_frame = tk.Frame(root)
# button_frame.pack(pady=5)
#
# btn_week = tk.Button(button_frame, text="Vue Semaine", command=set_weekly_view)
# btn_week.pack(side="left", padx=5)
#
# btn_month = tk.Button(button_frame, text="Vue Mois", command=set_monthly_view)
# btn_month.pack(side="left", padx=5)
#
#
# # --- Démarrer l'application ---
# root.mainloop()
