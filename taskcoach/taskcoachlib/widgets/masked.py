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

Module `masked.py`

Ce module fournit des classes de contrôle étendues pour gérer des entrées
masquées et formatées dans Task Coach. Il inclut des contrôles pour la gestion
de texte, de montants, et de durées temporelles.

(Les classes fournies dans masked.py étendent les contrôles wx.lib.masked
pour ajouter des fonctionnalités adaptées à Task Coach,
comme la gestion des montants et des durées.)

Classes principales :
    - `FixOverwriteSelectionMixin` : Mixin permettant de gérer les sélections de texte
      avec des comportements spécifiques à certains systèmes d'exploitation.
    - `TextCtrl` : Contrôle de texte étendu basé sur `masked.TextCtrl`.
    - `AmountCtrl` : Contrôle pour les montants numériques avec support des séparateurs
      décimaux et des milliers.
    - `TimeDeltaCtrl` : Contrôle masqué pour la saisie ou l'affichage de durées au
      format heures:minutes:secondes.

Compatibilité :
    - Ce module utilise les widgets `wx.lib.masked` pour gérer les masques de saisie.
    - Gère des comportements spécifiques pour les systèmes GTK.



Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Licence : GNU General Public License, version 3 ou ultérieure.
"""

# from builtins import object
from taskcoachlib import operating_system
from wx.lib import masked
import wx
import locale


class FixOverwriteSelectionMixin(object):
    """
    Mixin pour corriger les comportements de sélection et de saisie dans
    les contrôles masqués (`masked.TextCtrl` et `masked.ComboBox`).

    Ce mixin gère des cas spécifiques, comme la navigation au clavier
    dans les onglets et les comportements de sélection sur GTK.

    Elle est ajouté à TextCtrl et AmountCtrl(Variante de masked.NumCtrl).

    Mixin pour corriger les comportements de sélection et de saisie dans
    les contrôles masqués (`masked.TextCtrl` et `masked.ComboBox`).

    Ce mixin suppose que la classe finale fournit les méthodes suivantes :
    - `_SetSelection(start, end)` : Définit la sélection de texte.
    - `GetParent()` : Retourne le parent du contrôle.
                      Ce parent doit avoir NavigateBook comme attribut.
                      Soit gui.dialog.editor, soit gui.dialog.entry.
    - `_OnKeyDown(event)` : Gère les événements clavier.

    Si ces méthodes ne sont pas disponibles, elles doivent être implémentées
    dans la classe qui utilise ce mixin.

    Méthodes :
        - `_SetSelection` : Définit la sélection de texte avec un comportement
          adapté à GTK.
        - `_OnKeyDown` : Gère les événements clavier pour la navigation.
    """

    def _SetSelection(self, start, end):
        """
        Définit la sélection de texte dans le contrôle.

        Sur GTK, ajuste les positions de début et de fin pour s'assurer que le
        curseur reste au début du champ, ce qui permet de remplacer le contenu
        au lieu de passer au champ suivant.

        De la même manière que _GetSelection, chaque classe dérivée de
        MaskedEditMixin doit définir la fonction permettant de définir
        le début et la fin de la sélection de texte actuelle.
        (par exemple .SetSelection() pour masked.TextCtrl et .SetMark() pour
        masked.ComboBox.

        Défini dans wx.lib.masked.combobox ou wx.lib.masked.textctrl.

        Dans combobox et textctrl, Autorise mixin à définir la sélection de texte de ce contrôle.
        REQUIS par toute classe dérivée de MaskedEditMixin.

        Args :
            start (int) : Début de la sélection.
            end (int) : Fin de la sélection.

        Returns :
            None

        Raises :
            NotImplementedError : Si `_SetSelection` n'est pas disponible dans la
                                  classe finale.
        """
        # if operating_system.isGTK():  # pragma: no cover
        #     # By exchanging the start and end parameters we make sure that the
        #     # cursor is at the start of the field so that typing overwrites the
        #     # current field instead of moving to the next field:
        #     start, end = end, start
        # super()._SetSelection(start, end)

        if hasattr(super(), "_SetSelection"):
            if operating_system.isGTK():  # pragma: no cover
                start, end = end, start
            super()._SetSelection(start, end)
            return
        else:
            # Solution par défaut : Ne rien faire ou lever une exception.
            raise NotImplementedError(
                "_SetSelection doit être implémenté ou accessible dans la classe finale."
            )

    def GetParent(self):
        """
        Retourne le parent de ce contrôle.

        Returns :
            wx.Window : Parent de ce contrôle.

        Raises :
            NotImplementedError : Si `GetParent` n'est pas disponible.
        """
        if hasattr(super(), "GetParent"):
            return super().GetParent()
        raise NotImplementedError(
            "GetParent doit être disponible dans la classe utilisant FixOverwriteSelectionMixin."
        )

    def _OnKeyDown(self, event):
        """
        Gère les événements clavier pour permettre la navigation dans les onglets.

        Si la touche `Tab` est utilisée avec des modificateurs (comme `Ctrl` ou `Shift`),
        transmet l'événement au parent pour gérer la navigation.

        Args :
            event (wx.KeyEvent) : Événement clavier.
        """
        # Allow keyboard navigation in notebook. Just skipping the event does not work;
        # propagate it all the way up...
        if (
            event.GetKeyCode() == wx.WXK_TAB
            and event.GetModifiers()
            and hasattr(self.GetParent(), "NavigateBook")
        ):
            if self.GetParent().NavigateBook(event):
                return
        super()._OnKeyDown(event)


class TextCtrl(FixOverwriteSelectionMixin, masked.TextCtrl):
    """
    Contrôle de texte étendu basé sur `masked.TextCtrl`.

    Ce contrôle hérite des fonctionnalités du mixin `FixOverwriteSelectionMixin`
    pour améliorer les comportements de sélection de texte.

    Utilisé dans TimeDeltaCtrl.
    """

    pass


class AmountCtrl(FixOverwriteSelectionMixin, masked.NumCtrl):
    """
    Contrôle pour saisir des montants numériques avec support des séparateurs
    décimaux et des milliers.

    Ce contrôle ajuste automatiquement les séparateurs en fonction des
    conventions locales.

    Utilisé dans gui.dialog.entry.AmountEntry, et gui.viewer.inplace_editor.AmountCtrl.

    Méthodes :
        - `__init__` : Initialise le contrôle avec des paramètres locaux.

    Attributs spécifiques :
        - `decimalChar` : Caractère utilisé pour les décimales (ex. `.` ou `,`).
        - `groupChar` : Caractère utilisé pour séparer les milliers.
        - `groupDigits` : Indique si les séparateurs de milliers sont activés.
    """

    def __init__(self, parent, value=0, locale_conventions=None):
        """
        Initialise un contrôle de montant avec les paramètres régionaux.

        Args :
            parent (wx.Window) : Fenêtre parente.
            value (float) : Valeur initiale.
            locale_conventions (dict, optional) : Conventions locales pour les
                séparateurs décimaux et de milliers. Par défaut, utilise les
                conventions du système.
        """
        locale_conventions = locale_conventions or locale.localeconv()
        decimalChar = locale_conventions["decimal_point"] or "."
        groupChar = locale_conventions["thousands_sep"] or ","
        groupDigits = len(locale_conventions["grouping"]) > 1
        # The thousands separator may come up as ISO-8859-1 character
        # 0xa0, which looks like a space but isn't ASCII, which
        # confuses NumCtrl... Play it safe and avoid any non-ASCII
        # character here, or groupChars that consist of multiple characters.
        if len(groupChar) > 1 or ord(groupChar) >= 128:
            groupChar = ","
        # Prevent decimalChar and groupChar from being the same:
        if groupChar == decimalChar:
            groupChar = "." if decimalChar == "," else ","
        super(AmountCtrl, self).__init__(
            parent,
            value=value,
            allowNegative=False,
            fractionWidth=2,
            selectOnEntry=True,
            decimalChar=decimalChar,
            groupChar=groupChar,
            groupDigits=groupDigits,
        )


class TimeDeltaCtrl(TextCtrl):
    """
    Contrôle masqué pour la saisie ou l'affichage de durées au format
    `<heure>:<minute>:<seconde>`.

    Champ d'édition masqué permettant de saisir ou d'afficher des deltas temporels de la forme
    <heure>:<minute>:<seconde>. La saisie de deltas de temps négatifs n'est pas là,
    l'affichage de deltas de temps négatifs est autorisé si le contrôle
    est en lecture seule.

    Fonctionnalités :
        - Permet d'afficher des durées négatives si le contrôle est en mode
          lecture seule.
        - Fournit une méthode pour définir dynamiquement la valeur de la durée.

    Méthodes :
        - `__init__` : Initialise le contrôle avec des heures, minutes et secondes.
        - `set_value` : Met à jour la valeur affichée dans le contrôle.
        - `__hour_string` : Génère une chaîne de caractères pour l'affichage
          des heures, incluant un signe négatif si nécessaire.
    """

    def __init__(
        self,
        parent,
        hours,
        minutes,
        seconds,
        readonly=False,
        negative_value=False,
        *args,
        **kwargs,
    ):
        """
        Initialise un contrôle pour afficher ou saisir une durée.

        Args :
            parent (wx.Window) : Fenêtre parente.
            hours (int) : Nombre d'heures.
            minutes (int) : Nombre de minutes.
            seconds (int) : Nombre de secondes.
            readonly (bool) : Si `True`, empêche la modification de la valeur.
            negative_value (bool) : Si `True`, permet l'affichage d'une durée négative.
        """
        # If the control is read only (meaning it could potentially have to
        # show negative values) or if the value is actually negative, allow
        # the minus sign in the mask. Otherwise only allow for numbers.
        mask = "X{9}:##:##" if negative_value or readonly else "#{9}:##:##"
        hours = self.__hour_string(hours, negative_value)
        super().__init__(
            parent,
            mask=mask,
            formatcodes="FS",
            fields=[
                masked.Field(formatcodes="Rr", defaultValue=hours),
                masked.Field(defaultValue="%02d" % minutes),
                masked.Field(defaultValue="%02d" % seconds),
            ],
            *args,
            **kwargs,
        )

    def set_value(self, hours, minutes, seconds, negative_value=False):
        """
        Met à jour la valeur affichée dans le contrôle.

        Args :
            hours (int) : Nombre d'heures.
            minutes (int) : Nombre de minutes.
            seconds (int) : Nombre de secondes.
            negative_value (bool) : Si `True`, affiche une durée négative.
        """
        hours = self.__hour_string(hours, negative_value)
        self.SetCtrlParameters(
            formatcodes="FS",
            fields=[
                masked.Field(formatcodes="Rr", defaultValue=hours),
                masked.Field(defaultValue="%02d" % minutes),
                masked.Field(defaultValue="%02d" % seconds),
            ],
        )
        self.Refresh()

    @staticmethod
    def __hour_string(hours, negative_value):
        """
        Génère une chaîne pour représenter les heures.

        Si la valeur est négative, ajoute un signe moins devant le nombre d'heures.

        Si la valeur est négative (par exemple, dépassement du budget), placez un signe moins
        avant le nombre d'heures et assurez-vous que le champ a la largeur appropriée.

        Args :
            hours (int) : Nombre d'heures.
            negative_value (bool) : Si `True`, ajoute un signe moins.

        Returns :
            str : Chaîne formatée représentant les heures.
        """
        # return (
        #     "%9s" % ("-" + "%d" % hours) if negative_value else "%9d" % hours
        # )
        # return f"-{f'{hours:d}':>9}" if negative_value else f"{hours:9d}"  # MAUVAIS !
        return f"{'-' + str(hours):>9}" if negative_value else f"{hours:9d}"
