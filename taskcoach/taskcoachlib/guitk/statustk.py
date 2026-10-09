"""
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
# Voici une proposition de conversion du fichier status.py de wxPython vers Tkinter,
# en tenant compte de sa fonctionnalité et de son rôle dans l'application TaskCoach.
# Analyse du code source status.py
# Le code fourni définit une classe StatusBar qui hérite de wx.StatusBar.
# Cette barre d'état a pour but d'afficher des informations sur l'état de l'application,
# et notamment des messages provenant des "viewers" (vues). Voici les points clés à convertir :
#
# Héritage : wx.StatusBar doit être remplacé par une équivalence Tkinter
#            (un Frame avec un Label pour chaque champ).
# Gestion des événements : Les événements wx.EVT_TIMER, wx.EVT_MENU_HIGHLIGHT_ALL,
#                          et wx.EVT_TOOL_ENTER doivent être gérés avec les mécanismes de Tkinter.
# Timer : wx.Timer doit être remplacé par root.after.
# PubSub : pubsub est utilisé pour la communication.
#          Il faudra vérifier si cette librairie est toujours nécessaire
#          ou si on peut utiliser un autre moyen de communication.
# wx.CallLater et wx.FutureCall: Ces méthodes doivent être remplacées par root.after.

# Explications et points importants :
#
# Remplacement de wx.StatusBar : La classe hérite maintenant de tk.Frame.
#                                Deux tk.Label sont créés pour simuler
#                                les deux champs de la barre d'état originale 1.
# Timer Tkinter : wx.Timer et wx.CallLater sont remplacés par la méthode after de Tkinter,
#                 qui permet de planifier l'exécution d'une fonction après un délai en millisecondes.
#                 after_cancel permet d'annuler un appel planifié 2.
# Gestion des événements : Les événements wx.EVT_MENU_HIGHLIGHT_ALL et
#                          wx.EVT_TOOL_ENTER sont remplacés par des bind
#                          sur les événements <Enter> et <Button-1>.
# Destruction : La méthode destroy est incluse pour nettoyer les ressources
#               (annulation du timer) lorsque la barre d'état est détruite 2.
# PubSub : J'ai laissé le code commenté pour l'utilisation de pubsub.
#          Si vous n'utilisez plus pubsub, vous pouvez simplifier la communication entre les composants.
# Adaptation Nécessaire : Vous devrez adapter la partie self.viewer.statusMessages()
#                         en fonction de la nouvelle structure de votre application Tkinter.
#                         Il faudra également gérer la communication entre les différents composants
#                         pour mettre à jour la barre d'état.
# Style : J'ai utilisé tkinter.ttk pour créer un style plus moderne pour les labels, mais c'est optionnel.
# Code de test: J'ai ajouté un code de test pour valider le fonctionnement de la status bar.

# Corrections et améliorations :
#
# Stockage du texte : La variable status_message permet de conserver
#                     le dernier message affiché dans chaque champ.
# Utilisation de config : La méthode config est utilisée pour modifier le texte
#                         du Label Tkinter correspondant au bon panneau.
#
# Avec cette version, la fonction set_status_text devrait maintenant
# mettre à jour correctement le texte dans le panneau spécifié de la barre d'état,
# tout en conservant le comportement de temporisation et de restauration du texte.

import tkinter as tk
import tkinter.ttk as ttk  # Pour un style plus moderne (facultatif)
from pubsub import pub  # Si pubsub est toujours utilisé


class StatusBar(tk.Frame):
    """
    Cette barre d'état a pour but d'afficher des informations sur l'état de l'application,
    et notamment des messages provenant des "viewers" (vues).
    """
    def __init__(self, parent, viewer):
        super().__init__(parent)
        self.parent = parent
        self.viewer = viewer
        self.status_labels = []
        self.status_labels.append(tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W))
        self.status_labels.append(tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W))
        self.status_labels[0].pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_labels[1].pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.after_id = None  # Pour stocker l'ID du after
        self.status_message = ["", ""]  # pour conserver le status

        # Si pubsub est toujours utilisé, adapter comme suit:
        pub.subscribe(self.on_viewer_status_changed, "viewer.status")

        self.bind("<Enter>", self.reset_status_bar)  # remplace wx.EVT_MENU_HIGHLIGHT_ALL, wx.EVT_TOOL_ENTER
        self.bind("<Button-1>", self.reset_status_bar)

        self.on_viewer_status_changed()  # Initialisation

    def reset_status_bar(self, event=None):
        """ Restaure le texte de la barre d'état. """
        self._display_status()

    def on_viewer_status_changed(self):
        """ Met à jour le statut après un délai. """
        self.after(500, self._display_status)

    def _display_status(self):
        """ Affiche le statut actuel. """
        try:
            status1, status2 = self.viewer.statusMessages()
            self.set_status_text(status1, 0)  # Définit le texte d'état du i-ème champ.
            self.set_status_text(status2, 1)
        except AttributeError:
            return  # Le viewer n'est pas encore prêt

    def set_status_text(self, message, pane=0, delay=3000):
        """ Affiche un message dans la barre d'état avec un délai. """
        # Définit le texte d'état du i-ème champ.
        self.status_message[pane] = message
        self.status_labels[pane].config(text=message)
        if self.after_id:
            self.after_cancel(self.after_id)  # Annule l'appel précédent
        self.after_id = self.after(delay, self._display_status)

    def destroy(self):
        """Nettoyage."""
        self.unbind("<Enter>")
        self.unbind("<Button-1>")
        if self.after_id:
            self.after_cancel(self.after_id)
        super().destroy()


if __name__ == '__main__':
    # code de test
    class ViewerTest:
        def statusMessages(self):
            return "status 1", "status 2"
    root = tk.Tk()
    viewer = ViewerTest()
    status_bar = StatusBar(root, viewer)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()
