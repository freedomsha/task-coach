"""
Task Coach - Votre gestionnaire de tâches
Conversion des widgets masqués de wxPython à Tkinter.

Ce module recrée la fonctionnalité des contrôles masqués (masked.TextCtrl,
masked.NumCtrl) de wxPython pour Tkinter en utilisant une approche
basée sur les événements et la validation de l'entrée.

Classes principales :
    - `AmountCtrl` : Contrôle pour les montants numériques.
    - `TimeDeltaCtrl` : Contrôle pour les durées au format heures:minutes:secondes.
"""
# Le module masked.py gère des fonctionnalités plus complexes,
# notamment les champs de texte masqués et la manipulation de valeurs numériques
# basées sur les conventions locales.
#
# Pour Tkinter, il n'y a pas d'équivalent direct à wx.lib.masked.
# Je vais donc recréer cette fonctionnalité en utilisant une approche plus
# idiomatique de Tkinter, en m'appuyant sur les événements de frappe et
# la validation pour appliquer le formatage et les masques.

# J'ai recréé les classes AmountCtrl et TimeDeltaCtrl en m'appuyant sur
# des widgets ttk.Entry et en utilisant des mécanismes de validation et
# de formatage basés sur les événements.
#
#     AmountCtrl : J'ai mis en place une logique pour formater le nombre
#     en fonction des conventions locales et pour valider l'entrée à chaque frappe.
#     Cela permet de gérer les séparateurs décimaux et de milliers comme dans la version wxPython.
#
#     TimeDeltaCtrl : J'ai simplifié la logique pour afficher les heures, minutes et secondes.
#     Le formatage est géré par la méthode set_value,
#     et une validation simple est effectuée à la frappe pour s'assurer que
#     seuls les chiffres et les : sont présents.
#
# Le code inclut également un exemple d'utilisation (if __name__ == "__main__":)
# pour chaque widget, ce qui devrait vous aider à les intégrer facilement dans
# votre application Task Coach.

import tkinter as tk
from tkinter import ttk
import locale
import re


class AmountCtrl(ttk.Entry):
    """
    Contrôle pour saisir des montants numériques avec support des séparateurs
    décimaux et des milliers.
    """
    def __init__(self, parent, value=0, locale_conventions=None, **kwargs):
        """
        Initialise un contrôle de montant avec les paramètres régionaux.

        :param parent: Le widget parent.
        :param value: La valeur initiale.
        :param locale_conventions: Conventions locales pour les séparateurs.
        """
        self.locale_conventions = locale_conventions or locale.localeconv()
        self.decimal_char = self.locale_conventions["decimal_point"] or "."
        self.group_char = self.locale_conventions["thousands_sep"] or ""

        # Empêcher le séparateur décimal d'être le même que le séparateur de groupe
        if self.group_char == self.decimal_char:
            self.group_char = "," if self.decimal_char == "." else "."

        self._value_var = tk.StringVar(parent, value=f"{value:,.2f}")
        super().__init__(parent, textvariable=self._value_var, **kwargs)

        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_key_release(self, event):
        """
        Valide et formate l'entrée de l'utilisateur après chaque frappe.
        """
        # Supprime tout sauf les chiffres, le point décimal et le signe moins
        text = self.get().replace(self.group_char, "")
        text = text.replace(self.decimal_char, ".")

        if not re.match(r"^-?\d*\.?\d*$", text):
            # L'entrée est invalide, restaure la dernière valeur valide
            current_value = self.GetValue()
            self._value_var.set(f"{current_value:,.2f}")
            return

        try:
            val = float(text)
            self._format_value(val)
        except (ValueError, IndexError):
            pass

    def _on_focus_in(self, event):
        """
        Sélectionne tout le texte à l'entrée du focus.
        """
        self.select_range(0, tk.END)

    def _on_focus_out(self, event):
        """
        Formate la valeur à la perte du focus.
        """
        text = self.get().replace(self.group_char, "")
        text = text.replace(self.decimal_char, ".")
        try:
            val = float(text)
        except (ValueError, IndexError):
            val = 0.0
        self._format_value(val)

    def _format_value(self, value):
        """
        Formate la valeur numérique en chaîne de caractères avec les séparateurs locaux.
        """
        formatted_value = f"{value:,.2f}".replace(",", "TEMP").replace(".", self.decimal_char).replace("TEMP", self.group_char)
        self._value_var.set(formatted_value)

    def GetValue(self):
        """
        Retourne la valeur float du contrôle.
        """
        try:
            text = self.get().replace(self.group_char, "")
            text = text.replace(self.decimal_char, ".")
            return float(text)
        except (ValueError, IndexError):
            return 0.0

    def SetValue(self, value):
        """
        Définit la valeur du contrôle.
        """
        self._format_value(value)


class TimeDeltaCtrl(ttk.Entry):
    """
    Contrôle masqué pour la saisie ou l'affichage de durées au format
    <heure>:<minute>:<seconde>.
    """
    def __init__(self, parent, hours, minutes, seconds, readonly=False, negative_value=False, **kwargs):
        """
        Initialise un contrôle pour une durée.

        :param parent: Le widget parent.
        :param hours: Nombre d'heures.
        :param minutes: Nombre de minutes.
        :param seconds: Nombre de secondes.
        :param negative_value: Affiche une durée négative si True.
        """
        self._value_var = tk.StringVar(parent)
        super().__init__(parent, textvariable=self._value_var, **kwargs)

        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.set_value(hours, minutes, seconds, negative_value)

    def set_value(self, hours: int, minutes: int, seconds: int, negative_value=False):
        """
        Met à jour la valeur affichée dans le contrôle.
        """
        sign = "-" if negative_value else ""
        formatted_value = f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
        self._value_var.set(formatted_value)

    def _on_key_release(self, event):
        """
        Valide l'entrée au format hh:mm:ss.
        """
        text = self.get()
        # Supprime tout caractère qui n'est pas un chiffre ou un ":"
        sanitized_text = re.sub(r"[^0-9:]", "", text)
        if sanitized_text != text:
            self._value_var.set(sanitized_text)

    def _on_focus_in(self, event):
        """
        Sélectionne tout le texte lorsque le widget reçoit le focus.
        """
        self.select_range(0, tk.END)


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Exemple de widgets masqués Tkinter")
    root.geometry("400x200")

    # Exemples pour AmountCtrl
    tk.Label(root, text="AmountCtrl (valeur 1234.56)").pack()
    amount_ctrl = AmountCtrl(root, value=1234.56)
    amount_ctrl.pack(pady=5)

    # Exemples pour TimeDeltaCtrl
    tk.Label(root, text="TimeDeltaCtrl (durée négative)").pack()
    time_delta_ctrl = TimeDeltaCtrl(root, hours=10, minutes=5, seconds=45, negative_value=True)
    time_delta_ctrl.pack(pady=5)

    root.mainloop()

