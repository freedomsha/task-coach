# -*- coding: utf-8 -*-
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

Ce module définit la classe `TaskStatus` et plusieurs instances représentant différents statuts de tâche.

La classe `TaskStatus` encapsule des informations sur un statut de tâche spécifique, notamment :

* `statusString` : un court identifiant de chaîne pour le statut.
* `pluralLabel` : une étiquette lisible par l'homme pour la forme plurielle du statut.
* `countLabel` : Un format de chaîne pour afficher le nombre de tâches avec ce statut.
* `hideMenuText` : Le texte à afficher dans le menu pour masquer les tâches avec ce statut.
* `hideHelpText` : Un texte d'aide expliquant la signification du statut.

Il fournit également des méthodes pour :

* Récupérer l'icône appropriée en fonction du statut et paramètres.
* Obtenir le texte pour masquer l'état.
* Comparaison des objets d'état.
* Hachage des objets d'état à utiliser dans les collections.

Le module définit plusieurs instances de `TaskStatus` classe pour les statuts de tâches courants :
* `inactif`
* `tard`
* `actif`
* `duesoon`
* `overdue`
* `completed`

Chaque instance possède ses propres attributs spécifiques et fournit un moyen pratique de représenter et de travailler avec différents statuts de tâches au sein de l'application.
"""

# from builtins import object
from taskcoachlib.i18n import _
from taskcoachlib.config import defaults


class TaskStatus(object):
    """
    Représente un statut spécifique pour une tâche.

    Attributs :
        statusString (str) : Un identifiant de chaîne courte pour le statut.
        pluralLabel (str) : Une étiquette lisible par l'homme pour la forme plurielle du statut.
        countLabel (str) : Un format de chaîne pour afficher le nombre de tâches avec ce statut.
        hideMenuText (str) : Le texte à afficher dans le menu pour masquer les tâches avec ce statut status.
        hideHelpText (str) : Un texte d'aide expliquant la signification du statut.
    """

    def __init__(
        self, statusString, pluralLabel, countLabel, hideMenuText, hideHelpText
    ):
        self.statusString = statusString
        self.pluralLabel = pluralLabel
        self.countLabel = countLabel
        self.hideMenuText = hideMenuText
        self.hideHelpText = hideHelpText

    # Ceci n'est utilisé que par les commandes ui, donc utilisez la valeur par défaut si l'utilisateur a configuré 'pas de bitmap', car nous
    # en avons besoin pour la barre d'outils...

    def getBitmap(self, settings):
        """
        Récupère l'icône associée au statut.

        Args :
            settings (object ?) : L'objet des paramètres de l'application.

        Returns :
            (str) : Le chemin d'accès au fichier d'icône.
        """
        if settings.get("icon", "%stasks" % self.statusString):
            return settings.get("icon", "%stasks" % self.statusString)
        return defaults.defaults["icon"]["%stasks" % self.statusString]

    def getHideBitmap(self, settings):
        """
        Récupère l'icône pour masquer les tâches avec ce statut.

        Args :
            settings : (object) L'objet des paramètres de l'application.

        Returns :
            (str) : Le chemin d'accès de l'icône à déposer.
        """
        if settings.get("icon", "%stasks" % self.statusString):
            return "%s+cross_red_icon" % settings.get(
                "icon", "%stasks" % self.statusString
            )
        return (
            "%s+cross_red_icon"
            % defaults.defaults["icon"]["%stasks" % self.statusString]
        )

    def __repr__(self):
        """
        Renvoie une représentation sous forme de chaîne de l'objet TaskStatus.

        Returns :
            (str) : Une représentation sous forme de chaîne de l'objet.
        """
        # return "%s(%s)" % (self.__class__.__name__, self.statusString)
        return f"{self.__class__.__name__}({self.statusString})"

    def __str__(self):
        """
        Renvoie la chaîne d'état.

        Returns :
            (str) : La chaîne d'état.
        """
        return self.statusString

    def __eq__(self, other):
        """
        Vérifie si deux objets TaskStatus sont égaux.

        Args :
            other (TaskStatus) : l'autre objet TaskStatus à comparer.

        Returns :
            (bool) : True si les chaînes d'état sont égales, Faux sinon.
        """
        # return self.statusString == other.statusString
        if isinstance(other, TaskStatus):
            return self.statusString == other.statusString
        return False

    # j'ai ajouté cette fonction :
    def __hash__(self) -> int:
        """
        Renvoie le hachage de l'objet TaskStatus.

        Returns :
            (int) : La valeur de hachage.
        """
        # Because of __eq__
        # return hash(id(self))
        return hash(
            self.statusString
        )  # TODO : id(self) ou self.statusString ? AI!

    def __neq__(self, other):
        """
        Vérifie si deux objets TaskStatus ne sont pas égaux.

        Args :
            other (TaskStatus) : L'autre objet TaskStatus à comparer.

        Returns :
            (bool) : True si les chaînes d'état ne sont pas égaux, Faux sinon.
        """
        return self.statusString != other.statusString

    def __bool__(self):
        """
        Renvoie True pour tous les objets TaskStatus.

        Returns :
            (bool) : toujours vrai.
        """
        return True


# Définition des statuts
inactive = TaskStatus(
    "inactive",
    _("Inactive tasks"),
    _("Inactive tasks: %d (%d%%)"),
    _("Hide &inactive tasks"),
    _("Show/hide inactive tasks (incomplete tasks without actual start date)"),
)

late = TaskStatus(
    "late",
    _("Late tasks"),
    _("Late tasks: %d (%d%%)"),
    _("Hide &late tasks"),
    _(
        "Show/hide late tasks (inactive tasks with a planned start in the past)"
    ),
)

active = TaskStatus(
    "active",
    _("Active tasks"),
    _("Active tasks: %d (%d%%)"),
    _("Hide &active tasks"),
    _(
        "Show/hide active tasks (incomplete tasks with an actual start date in the past)"
    ),
)

duesoon = TaskStatus(
    "duesoon",
    _("Due soon tasks"),
    _("Due soon tasks: %d (%d%%)"),
    _("Hide &due soon tasks"),
    _(
        "Show/hide due soon tasks (incomplete tasks with a due date in the near future)"
    ),
)

overdue = TaskStatus(
    "overdue",
    _("Overdue tasks"),
    _("Overdue tasks: %d (%d%%)"),
    _("Hide &over due tasks"),
    _(
        "Show/hide over due tasks (incomplete tasks with a due date in the past)"
    ),
)

completed = TaskStatus(
    "completed",
    _("Completed tasks"),
    _("Completed tasks: %d (%d%%)"),
    _("Hide &completed tasks"),
    _("Show/hide completed tasks"),
)

# Mapping des valeurs numériques vers les instances de TaskStatus
_status_map = {
    4: completed,
    5: overdue,
    6: duesoon,
    7: active,
    8: inactive,
    9: late,
}


def from_int(value):
    """Convertit un entier en instance de TaskStatus."""
    # print(f"TaskStatus.from_int() appelé avec {value}, _status_map = {_status_map}")
    # print(f"DEBUG - TaskStatus.from_int() appelé avec {value}, retourne {_status_map.get(int(value))}")
    if isinstance(value, int):
        return _status_map.get(
            value
        )  # Par défaut, retourne "inactive" si inconnu
    else:
        return _status_map.get(
            int(value)
        )  # Par défaut, retourne "inactive" si inconnu
    # return _status_map.get(value, inactive)  # Par défaut, retourne "inactive" si inconnu


# print(f"DEBUG - Vérification des statuts : completed = {completed} ({type(completed)})")
