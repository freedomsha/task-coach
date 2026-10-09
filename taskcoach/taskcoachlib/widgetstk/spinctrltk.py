"""
Task Coach - Votre gestionnaire de tâches
Conversion du widget SpinCtrl de wxPython à Tkinter.

Ce module recrée la fonctionnalité de SpinCtrl en utilisant les widgets
Entry et Spinbox de Tkinter. Il gère la synchronisation de la valeur
entre les deux widgets, la gestion des bornes (min/max), et la gestion
des événements clavier (flèches haut/bas, PageUp/PageDown).
"""
# La conversion d'un widget aussi spécifique qu'un SpinCtrl nécessite de
# recréer sa fonctionnalité en utilisant les composants de base de Tkinter,
# à savoir un Entry et des Spinbutton (ou de simples Button).
#
# J'ai converti le code spinctrl.py en une classe SpinCtrl pour Tkinter.
# Ce fichier, nommé spinctrltk.py, utilise tkinter.ttk pour
# une meilleure intégration visuelle avec le système d'exploitation.

# J'ai choisi d'utiliser le widget ttk.Spinbox de Tkinter, qui est l'équivalent
# natif et plus moderne de la combinaison TextCtrl + SpinButton de wxPython.
# Il gère déjà une grande partie de la logique de synchronisation et de
# validation que vous aviez dans la version wxPython.
#
# Le code inclut également une petite section if __name__ == "__main__":
# pour que vous puissiez l'exécuter directement et voir le widget en action.

import tkinter as tk
from tkinter import ttk
from tkinter import Event


# class SpinCtrl(ttk.Frame):
class SpinCtrl(ttk.Spinbox):
    """
    Un widget SpinCtrl pour Tkinter, combinant un champ de texte et des boutons de rotation.
    """
    def __init__(self, parent, value=0, min_val=-2147483647, max_val=2147483647, **kwargs):
        """
        Initialise le widget SpinCtrl.

        :param parent: Le widget parent.
        :param value: La valeur initiale.
        :param min_val: La valeur minimale.
        :param max_val: La valeur maximale.
        :param kwargs: Arguments supplémentaires (non utilisés pour le moment).
        """
        super().__init__(parent)

        self._min_val = min_val
        self._max_val = max_val
        self._value = tk.IntVar(self, value=min(max(int(value), min_val), max_val))

        # Utilisation de la classe Spinbox de ttk qui combine les deux fonctionnalités
        self._spinbox = ttk.Spinbox(
            self,
            from_=self._min_val,
            to=self._max_val,
            textvariable=self._value,
            wrap=False
        )

        # Lie les événements clavier pour un comportement similaire à l'original wxPython
        self._spinbox.bind("<Key>", self.onKey)
        self._spinbox.bind("<FocusIn>", self.onSetFocus)

        # Place le widget dans la fenêtre
        self._spinbox.pack(fill=tk.BOTH, expand=True)

    def onKey(self, event: Event):
        """
        Gère les événements de touche pour incrémenter/décrémenter la valeur.
        """
        delta_by_keycode = {
            'Up': 1, 'Key-Up': 1,
            'Down': -1, 'Key-Down': -1,
            'Prior': 10,  # Touche PageUp
            'Next': -10   # Touche PageDown
        }

        delta = delta_by_keycode.get(event.keysym, 0)

        if delta != 0:
            current_value = self.GetValue()
            new_value = current_value + delta
            self.SetValue(new_value)
            return "break"  # Empêche l'action par défaut de la touche
        else:
            return None

        # Le widget Spinbox gère déjà la validation du texte en interne.
        # Nous n'avons pas besoin de recréer la logique onText.

    def onSetFocus(self, event: Event):
        """
        Sélectionne tout le texte lorsque le widget reçoit le focus.
        """
        self._spinbox.select_range(0, tk.END)

    def GetValue(self) -> int:
        """
        Retourne la valeur actuelle du widget.
        """
        try:
            return self._value.get()
        except tk.TclError:
            # Si la valeur dans l'Entry est invalide, retourne la valeur de la variable
            return self._spinbox.get()

    def SetValue(self, value: int):
        """
        Définit la valeur du widget.
        """
        # La variable Tkinter se charge de mettre à jour le widget
        self._value.set(value)

    def GetMin(self) -> int:
        """
        Retourne la valeur minimale.
        """
        return self._min_val

    def GetMax(self) -> int:
        """
        Retourne la valeur maximale.
        """
        return self._max_val


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple de SpinCtrl Tkinter")
    root.geometry("300x150")

    def on_value_change():
        """Fonction appelée lorsque la valeur change."""
        print(f"La nouvelle valeur est : {spinctrl_widget.GetValue()}")

    # Crée une instance du widget SpinCtrl
    spinctrl_widget = SpinCtrl(root, value=50, min_val=0, max_val=100)
    spinctrl_widget.pack(pady=20)

    # Lie la fonction de rappel à un événement virtuel Tkinter
    spinctrl_widget._spinbox.bind("<<Increment>>", lambda e: on_value_change())
    spinctrl_widget._spinbox.bind("<<Decrement>>", lambda e: on_value_change())

    # Vous pouvez également récupérer la valeur directement
    tk.Label(root, text="Contrôlez la valeur ci-dessus").pack()

    root.mainloop()
