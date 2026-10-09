#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module tkReportScheduler
========================

Ce module, converti de la version wxPython, gère la génération de rapports
imprimables pour le planificateur Tkinter.

Contrairement à wxPython, Tkinter n'a pas de framework d'impression intégré.
Cette classe facilite donc la création d'un fichier PostScript à partir du
contenu du planificateur, qui peut ensuite être imprimé.

Elle fonctionne en créant un canevas temporaire "hors écran", en y dessinant
le planning via tkSchedulerPrint, puis en exportant le résultat.
"""
# La conversion de ce module est un peu différente des autres car elle touche à une fonctionnalité qui n'a pas d'équivalent direct dans Tkinter : le framework d'impression intégré de wxPython (wx.Printout).
#
# La logique de la conversion
#
#     Le concept d'impression :
#
#         Dans wxPython, wx.Printout est une classe spéciale qui s'intègre au dialogue d'impression du système. Le framework appelle des méthodes comme OnPrintPage pour dessiner chaque page sur un "contexte de périphérique" (DC) fourni par l'imprimante.
#
#         Dans Tkinter, il n'y a pas de framework d'impression de ce type. La méthode standard pour imprimer est de dessiner le contenu sur un tk.Canvas, puis d'exporter ce canevas vers un fichier PostScript (.ps). Ce fichier peut ensuite être envoyé à une imprimante ou converti en PDF.
#
#     Nouvelle approche pour tkReportScheduler :
#
#         La classe n'héritera plus d'une classe de base d'impression. Ce sera une classe "utilitaire" ou "générateur de rapport".
#
#         Son rôle principal sera d'orchestrer la création d'un fichier PostScript.
#
#         Pour ce faire, elle créera en interne une fenêtre et un canevas temporaires, invisibles pour l'utilisateur, qui serviront de surface de dessin.
#
#         Elle utilisera la classe tkSchedulerPrint que nous avons déjà convertie pour dessiner le planning sur ce canevas temporaire.
#
#         Enfin, elle générera le fichier PostScript à partir du canevas et détruira les widgets temporaires.

import tkinter as tk
from taskcoachlib.thirdparty.tkScheduler.tkSchedulerPrint import tkSchedulerPrint


class tkReportScheduler:
    """
    Classe utilitaire pour générer un rapport imprimable du planificateur.

    Elle prend en charge la configuration, le dessin sur un canevas temporaire
    et la génération d'un fichier PostScript.
    """
    def __init__(self, format, style, drawerClass, day, weekstart, periodCount, schedules):
        """
        Initialise le générateur de rapport avec la configuration du planning.

        Args:
            format (int): Le type de vue (JOUR, SEMAINE, MOIS).
            style (int): Le style d'affichage (VERTICAL, HORIZONTAL).
            drawerClass: La classe de dessin à utiliser.
            day (datetime): La date de début du rapport.
            weekstart (int): Le premier jour de la semaine.
            periodCount (int): Le nombre de périodes à afficher.
            schedules (list): La liste des objets tkSchedule à inclure.
        """
        self._format = format
        self._style = style
        self._drawerClass = drawerClass
        self._day = day
        self._schedules = schedules
        self._weekstart = weekstart
        self._periodCount = periodCount
        self.page_count = 1 # La pagination doit être gérée à l'extérieur

    def generate_report(self, output_filename="planning_report.ps"):
        """
        Génère le rapport du planning et le sauvegarde dans un fichier PostScript.

        Args:
            output_filename (str): Le chemin du fichier de sortie.

        Returns:
            str: Le chemin complet du fichier généré.
        """
        # 1. Créer une fenêtre et un canevas temporaires et invisibles
        temp_root = tk.Toplevel()
        temp_root.withdraw()  # Cacher la fenêtre

        # Dimensions approximatives d'une page A4 en points (unité de PostScript)
        A4_WIDTH_POINTS = 595
        A4_HEIGHT_POINTS = 842

        page_canvas = tk.Canvas(
            temp_root,
            width=A4_WIDTH_POINTS,
            height=A4_HEIGHT_POINTS,
            bg="white"
        )
        page_canvas.pack()

        # 2. Utiliser tkSchedulerPrint pour dessiner sur ce canevas
        scheduler_printer = self._get_scheduler(page_canvas)

        # Il faut que Tkinter traite les événements pour que le canevas obtienne sa taille réelle
        temp_root.update_idletasks()

        # Dessiner le contenu
        scheduler_printer.Draw()

        # 3. Générer le fichier PostScript
        page_canvas.postscript(file=output_filename, colormode='color')

        # 4. Nettoyer en détruisant la fenêtre temporaire
        temp_root.destroy()

        print(f"Rapport généré avec succès : {output_filename}")
        return output_filename

    def _get_scheduler(self, canvas):
        """
        Crée et configure une instance de tkSchedulerPrint.
        """
        scheduler = tkSchedulerPrint(canvas)

        # Appliquer toute la configuration
        scheduler.SetViewType(self._format)
        # Note : SetStyle, SetDrawer ne sont pas dans tkSchedulerCore,
        # ils doivent être ajoutés si nécessaire ou la logique doit être adaptée.
        # Pour l'instant, ces attributs sont dans tkSchedulerPaint.
        scheduler._style = self._style
        scheduler._drawerClass = self._drawerClass

        scheduler.SetDate(self._day)
        scheduler.SetWeekStart(self._weekstart)
        scheduler.SetPeriodCount(self._periodCount)

        scheduler.Add(self._schedules)

        return scheduler

# Comment l'utiliser ?
#
# Puisque la logique a changé, la manière d'utiliser cette classe est aussi différente. Voici un exemple complet qui montre comment générer un rapport et même comment lancer son impression depuis Python.
# import tkinter as tk
# from datetime import datetime
# import subprocess
# import sys
#
# # --- Supposons que vos bibliothèques sont dans un dossier "taskcoachlib.thirdparty.tkScheduler" ---
# from taskcoachlib.thirdparty.tkScheduler.tkSchedulerConstants import SCHEDULER_WEEKLY, SCHEDULER_VERTICAL
# from taskcoachlib.thirdparty.tkScheduler.tkSchedule import tkSchedule
# from taskcoachlib.thirdparty.tkScheduler.tkDrawer import tkBaseDrawer # Import nécessaire
# from taskcoachlib.thirdparty.tkScheduler.tkReportScheduler import tkReportScheduler
#
#
# # --- Fonction pour lancer l'impression du fichier PostScript ---
# def print_file(filepath):
#     """Lance l'impression d'un fichier en utilisant les commandes système."""
#     try:
#         if sys.platform == "win32":
#             # Sur Windows, on peut utiliser l'association de fichier par défaut
#             import os
#             os.startfile(filepath, "print")
#         elif sys.platform == "darwin": # macOS
#             subprocess.run(["lpr", filepath], check=True)
#         else: # Linux
#             subprocess.run(["lp", filepath], check=True)
#         print(f"Le fichier {filepath} a été envoyé à l'imprimante.")
#     except (FileNotFoundError, subprocess.CalledProcessError) as e:
#         print(f"Erreur lors de l'impression : {e}")
#         print("Veuillez vérifier que vous avez une imprimante configurée et que les commandes (lp/lpr) sont disponibles.")
#
#
# # --- Application principale de démonstration ---
# if __name__ == '__main__':
#     root = tk.Tk()
#     root.title("Démonstration d'impression")
#     root.geometry("300x200")
#
#     # 1. Préparer les données pour le rapport
#     today = datetime.now()
#     schedules_to_print = []
#     event = tkSchedule()
#     event.start = today.replace(hour=9, minute=0)
#     event.end = today.replace(hour=10, minute=30)
#     event.description = "Préparation du rapport mensuel"
#     schedules_to_print.append(event)
#
#     def generate_and_print():
#         print("Génération du rapport en cours...")
#         # 2. Créer une instance du générateur de rapport
#         report_generator = tkReportScheduler(
#             format=SCHEDULER_WEEKLY,
#             style=SCHEDULER_VERTICAL,
#             drawerClass=tkBaseDrawer,
#             day=today,
#             weekstart=0, # Lundi
#             periodCount=1,
#             schedules=schedules_to_print
#         )
#
#         # 3. Générer le fichier PostScript
#         output_file = report_generator.generate_report("weekly_report.ps")
#
#         # 4. (Optionnel) Lancer l'impression
#         print_file(output_file)
#
#     # Bouton pour lancer la génération
#     print_button = tk.Button(
#         root,
#         text="Générer et Imprimer le Rapport",
#         command=generate_and_print
#     )
#     print_button.pack(expand=True, padx=20, pady=20)
#
#     root.mainloop()
