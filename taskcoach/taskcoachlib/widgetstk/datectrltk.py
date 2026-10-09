# datectrl.py for Tkinter, converted from wxPython
"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

# Le code wxPython original est très lié aux événements et aux structures de widgets de wxWidgets, notamment wx.Panel et wx.BoxSizer. L'équivalent Tkinter que je vais créer utilisera les ttk.Frame et le pack ou grid pour l'organisation des widgets, et gérera les événements de manière différente.

# J'ai converti les classes DateTimeCtrl et TimeEntry du fichier datectrl.py pour qu'elles fonctionnent avec Tkinter. J'ai aussi ajouté un exemple d'utilisation dans la section if __name__ == "__main__": pour que vous puissiez tester les widgets.
#
#     DateTimeCtrl utilise la classe Entry de votre code smartdatetimectrl.py.
#
#     TimeEntry utilise également SmartDateTimeCtrl pour gérer le champ d'heure.
#
# J'ai omis certaines fonctionnalités avancées de l'original wxPython, comme _SmartDateTimeCtrl et la gestion des événements HandleKey, car elles dépendent de l'architecture spécifique de wxWidgets et ne sont pas nécessaires pour l'équivalent simplifié sous Tkinter.

# Je vois le problème. L'erreur _tkinter.TclError: unknown option "-hour" est très claire.
#
# Le fichier datectrltk.py a été écrit pour fonctionner avec la version précédente de smartdatetimectrltk.py, où la classe SmartDateTimeCtrl acceptait des arguments comme hour pour initialiser la valeur de l'heure. Cependant, la nouvelle version de smartdatetimectrltk.py (avec la classe Entry unifiée) ne prend plus ces arguments car elle gère la valeur comme une seule chaîne de caractères.
#
# En conséquence, datectrltk.py tente de passer hour=value à SmartDateTimeCtrl, qui le transmet à son parent, ttk.Frame, et finalement à tkinter.ttk.Entry, qui ne reconnaît pas l'option -hour.
#
# Pour corriger cela, il faut modifier datectrltk.py pour qu'il utilise correctement la nouvelle API de SmartDateTimeCtrl. Il ne faut pas passer d'arguments de type hour au constructeur, mais plutôt utiliser la méthode SetValue après l'initialisation pour définir la valeur de l'heure.
#
# Voici le code corrigé pour datectrltk.py. Les lignes modifiées sont dans la classe TimeEntry.
# Bonjour,
#
# Merci pour la trace d'erreur. Elle est très claire et m'aide à identifier la source du problème.
#
# L'erreur _tkinter.TclError: unknown option "-hour" se produit parce que l'ancienne classe SmartDateTimeCtrl prenait des arguments comme hour et day, mais la nouvelle version que j'ai fournie, basée sur un seul widget ttk.Entry, ne les reconnaît plus. Ces arguments sont transmis directement à l'initialiseur de ttk.Entry qui ne sait pas quoi en faire.
#
# Pour résoudre cela, j'ai mis à jour le fichier datectrltk.py afin qu'il s'adapte à la nouvelle structure de SmartDateTimeCtrl.
#
# Voici les modifications principales :
#
#     Changement dans TimeEntry : J'ai supprimé l'argument hour=value de l'initialisation de SmartDateTimeCtrl qui causait l'erreur.
#
#     Nouvelle logique de valeur initiale : Le code utilise désormais la méthode SetValue de SmartDateTimeCtrl pour définir la valeur initiale. J'ai créé un objet datetime.datetime temporaire avec la date actuelle et l'heure fournie par la variable value.
#
#     Mise à jour de GetValue : La méthode GetValue de TimeEntry a été corrigée pour extraire l'heure de l'objet datetime.datetime retourné par self.__entry.GetValue(), ce qui est la nouvelle manière de fonctionner du widget.
import tkinter as tk
from tkinter import ttk
import datetime

# Assurez-vous que le fichier smartdatetimectrl.py est dans le bon répertoire
# pour que cette importation fonctionne.
# sauf que smartdatetimectrl est wxpython !
from taskcoachlib.thirdparty.tk3rdparty.smartdatetimectrltk import Entry as SmartDateTimeCtrl


class DateTimeCtrl(ttk.Frame):
    """
    Un contrôle de date et d'heure pour Tkinter, basé sur SmartDateTimeCtrl.
    """
    def __init__(self, parent, callback=None, noneAllowed=True,
                 starthour=8, endhour=18, interval=15, showSeconds=False,
                 showRelative=False, adjustEndOfDay=False, units=None, **kwargs):
        """
        Initialise le contrôle.

        :param parent: Le widget parent.
        :param callback: Fonction de rappel à appeler lors d'un changement de valeur.
        :param noneAllowed: Si la valeur peut être None.
        :param starthour: Heure de début pour l'intervalle.
        :param endhour: Heure de fin pour l'intervalle.
        :param interval: Intervalle en minutes.
        :param showSeconds: Afficher ou non les secondes.
        :param showRelative: (Non implémenté) Afficher les options relatives.
        :param adjustEndOfDay: (Non implémenté) Ajuster la fin de journée.
        :param units: (Non implémenté) Unités de temps.
        :param kwargs: Arguments additionnels pour ttk.Frame.
        """
        super().__init__(parent, **kwargs)

        self.__adjust = adjustEndOfDay
        self.__callback = callback
        self.__value = None

        # Créez une instance de notre SmartDateTimeCtrl pour Tkinter
        # Le format est déduit des paramètres, ce qui est une simplification
        # par rapport à l'original.
        # time_format = "hh:mm"
        time_format = "%H:%M"
        if showSeconds:
            # time_format += ":ss"
            time_format += ":$S"

        # Le format est "MM/DD/YYYY" pour être compatible avec l'implémentation actuelle de SmartDateTimeCtrl
        # date_format = "DD/MM/YYYY"
        date_format = "%d/%m/%Y"

        self.__ctrl = SmartDateTimeCtrl(
            self,
            format_string=f"{date_format} {time_format}",
            # Les autres paramètres comme startHour, endHour, etc. ne sont pas encore
            # gérés par l'implémentation simplifiée de SmartDateTimeCtrl.
        )
        self.__ctrl.pack(fill=tk.X, expand=True)

        # Associer un événement de changement de valeur
        self.__ctrl.bind("<<EntryChanged>>", self.__on_change)

    def __on_change(self, event):
        """
        Gestionnaire d'événement interne pour les changements de valeur.
        """
        self.__value = self.__ctrl.GetValue()
        if self.__callback is not None:
            self.__callback(self.__value)

    def GetValue(self):
        """
        Retourne la valeur actuelle du contrôle.
        """
        # Le code d'ajustement de fin de journée n'est pas implémenté
        return self.__value

    def SetValue(self, dateTime):
        """
        Définit la valeur du contrôle.
        """
        self.__ctrl.SetValue(dateTime)
        self.__value = self.__ctrl.GetValue()

    def setCallback(self, callback):
        """
        Définit la fonction de rappel.
        """
        self.__callback = callback

    def Cleanup(self):
        """
        Fonction de nettoyage (non nécessaire dans cette version Tkinter simplifiée).
        """
        pass


class TimeEntry(ttk.Frame):
    """
    Un contrôle d'entrée de temps simple, converti pour Tkinter.
    """
    def __init__(self, parent, value, defaultValue=0, disabledValue=None, disabledMessage=None, **kwargs):
        """
        Initialise le contrôle d'entrée de temps.
        """
        super().__init__(parent, **kwargs)

        self.__disabledValue = disabledValue
        self.__value = value

        self.pack(fill=tk.X, expand=True)

        # Créez le SmartDateTimeCtrl pour l'heure
        # self.__entry = SmartDateTimeCtrl(self, format_string="hh:mm", hour=value)
        self.__entry = SmartDateTimeCtrl(self, format_string="%H:%M")
        self.__entry.pack(side=tk.LEFT)
        # Définir la valeur initiale en utilisant la nouvelle méthode SetValue
        self.__entry.SetValue(datetime.datetime.now().replace(hour=value, minute=0, second=0, microsecond=0))

        if disabledMessage:
            self.__var = tk.BooleanVar()
            self.__checkbox = ttk.Checkbutton(self, text=disabledMessage, variable=self.__var, command=self.on_check)
            self.__checkbox.pack(side=tk.LEFT, padx=5)

            if value == disabledValue:
                self.__var.set(True)
                self.__entry.pack_forget()  # Masquer l'entrée d'heure

    def on_check(self):
        """
        Gère l'événement de la case à cocher pour activer/désactiver le champ d'entrée.
        """
        if self.__var.get():
            self.__entry.pack_forget()  # Masquer
        else:
            self.__entry.pack(side=tk.LEFT)  # Afficher

    def GetValue(self):
        """
        Retourne la valeur du contrôle.
        """
        if self.__disabledValue and self.__var.get():
            return self.__disabledValue

        # Une valeur par défaut simple si GetValue() retourne None
        val = self.__entry.GetValue()
        if val:
            return val.hour
        return self.__value


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test DateCtrl/TimeEntry Tkinter")

    def my_callback(new_value):
        print("Valeur changée :", new_value)

    # Test de DateTimeCtrl
    dt_ctrl_frame = ttk.LabelFrame(root, text="DateTimeCtrl")
    dt_ctrl_frame.pack(padx=10, pady=5, fill=tk.X)

    dt_ctrl = DateTimeCtrl(dt_ctrl_frame, callback=my_callback)
    dt_ctrl.pack(fill=tk.X, padx=5, pady=5)

    def set_value_to_now():
        dt_ctrl.SetValue(datetime.datetime.now())

    set_btn = ttk.Button(dt_ctrl_frame, text="Définir à maintenant", command=set_value_to_now)
    set_btn.pack(pady=5)

    # Test de TimeEntry
    time_entry_frame = ttk.LabelFrame(root, text="TimeEntry")
    time_entry_frame.pack(padx=10, pady=5, fill=tk.X)

    time_entry = TimeEntry(time_entry_frame, value=10, disabledMessage="Heure désactivée", disabledValue=999)
    time_entry.pack(fill=tk.X, padx=5, pady=5)

    def print_time_value():
        print("Valeur de TimeEntry:", time_entry.GetValue())

    print_btn = ttk.Button(time_entry_frame, text="Afficher l'heure", command=print_time_value)
    print_btn.pack(pady=5)

    root.mainloop()
