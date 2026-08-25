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

# Le piège de la division : C'est le point le plus critique.
# En Python 2, 1/1000 vaut 0.
# En Python 3, cela vaut 0.001.
# Le code a été corrigé pour s'assurer que
# les conversions de microsecondes en millisecondes ne soient pas réduites à zéro.

# from __future__ import division

# from past.utils import old_div
from typing import Tuple
import datetime
import math

# def legacy_round(x):
#     # The builtin round() behavior changed in Python 3. Not sure we
#     # actually need this behavior, but since there are some unit tests
#     # that expect it...
#     # Le comportement intégré de round() a changé dans Python 3. Je ne suis pas sûr
#     # que nous ayons réellement besoin de ce comportement, mais comme certains tests unitaires l'attendent...
#     if x > 0:
#         return math.floor(x + 0.5)  # retourne le plus grand entier non supérieur à (x+0,5).
#     return math.ceil(x - 0.5)   # retourne le plus petit entier supérieur ou égal à (x-0,5).


class TimeDelta(datetime.timedelta):
    """
    Hérite de la classe datetime.timedelta de Python.

    Elle fournit des fonctionnalités supplémentaires pour
    manipuler des intervalles de temps en tenant compte des heures, minutes, secondes et millisecondes.

    Voici une analyse plus détaillée des éléments clés du code :

    Constantes :

        millisecondsPerSecond : Nombre de millisecondes dans une seconde.
        millisecondsPerDay : Nombre de millisecondes dans un jour.
        millisecondsPerMicroSecond : Nombre de millisecondes dans une microseconde.

    Méthodes de la classe TimeDelta :

        hoursMinutesSeconds (self) : Renvoie un tuple contenant le nombre d'heures, de minutes et de secondes de l'intervalle.
        sign (self) : Renvoie un entier indiquant le signe de l'intervalle (1 pour positif, -1 pour négatif).
        hours (self) : Renvoie l'intervalle exprimé en nombre d'heures en tenant compte du signe.
        minutes (self) : Renvoie l'intervalle exprimé en nombre de minutes en tenant compte du signe.
        totalSeconds (self) : Renvoie l'intervalle exprimé en nombre de secondes en tenant compte du signe.
        milliseconds (self) : Renvoie l'intervalle exprimé en nombre de millisecondes.
        round (self, hours=0, minutes=0, seconds=0, alwaysUp=False) : Arrondi l'intervalle aux unités spécifiées (heures, minutes, secondes). alwaysUp permet de toujours arrondir vers le haut.
        __add__ (self, other) : Permet l'addition de deux objets TimeDelta en renvoyant une nouvelle instance de TimeDelta.
        __sub__ (self, other) : Permet la soustraction de deux objets TimeDelta en renvoyant une nouvelle instance de TimeDelta.

    Commentaires supplémentaires :

        La méthode legacy_round (commentée) est conservée pour des raisons de tests unitaires.
        La conversion en flottant (float(self.totalSeconds())) dans la méthode round pourrait être évitée en Python 3 car la division d'entiers par des nombres flottants renvoie automatiquement un flottant.
        La méthode parseTimeDelta permet de parser une chaîne de caractères au format "heures:minutes:secondes" en un objet TimeDelta.

    En résumé, ce code fournit une classe TimeDelta améliorée par rapport à la classe intégrée de Python pour une manipulation plus flexible et informative des intervalles de temps.
    """

    millisecondsPerSecond = 1000
    millisecondsPerDay = 24 * 60 * 60 * millisecondsPerSecond
    millisecondsPerMicroSecond = 1 / 1000
    # millisecondsPerMicroSecond = 1 // 1000
    # millisecondsPerMicroSecond = old_div(1, 1000)

    def hoursMinutesSeconds(self):
        """Renvoie un tuple (heures, minutes, secondes). Notez que l'appelant
        est chargé de vérifier si l'instance TimeDelta est
        positive ou négative."""
        if self < TimeDelta():
            seconds = 3600 * 24 - self.seconds
            days = abs(self.days) - 1
        else:
            seconds = self.seconds
            days = self.days
        # hours, seconds = seconds // 3600, seconds % 3600
        hours, seconds = divmod(seconds, 3600)
        # minutes, seconds = seconds // 60, seconds % 60
        minutes, seconds = divmod(seconds, 60)
        hours += days * 24
        return hours, minutes, seconds

    def sign(self):
        return -1 if self < TimeDelta() else 1

    def hours(self):
        """Timedelta expressed in number of hours."""
        hours, minutes, seconds = self.hoursMinutesSeconds()
        return self.sign() * (hours + (minutes / 60) + (seconds / 3600))
        # return self.sign() * (hours + (old_div(minutes, 60)) + (old_div(seconds, 3600)))
        # return self.sign() * (hours + (minutes // 60) + (seconds // 3600))

    def minutes(self):
        """Timedelta expressed in number of minutes."""
        hours, minutes, seconds = self.hoursMinutesSeconds()
        return self.sign() * (hours * 60 + minutes + (seconds / 60))
        # return self.sign() * (hours * 60 + minutes + (old_div(seconds, 60)))
        # return self.sign() * (hours * 60 + minutes + (seconds // 60))

    def totalSeconds(self):
        """Timedelta expressed in number of seconds."""
        hours, minutes, seconds = self.hoursMinutesSeconds()
        return self.sign() * (hours * 3600 + minutes * 60 + seconds)

    def milliseconds(self):
        """Timedelta expressed in number of milliseconds."""
        # No need to use self.sign() since self.days is negative for negative values
        # return int(legacy_round((self.days * self.millisecondsPerDay) +
        #                         (self.seconds * self.millisecondsPerSecond) +
        #                         (self.microseconds * self.millisecondsPerMicroSecond)))
        return (
            (self.days * self.millisecondsPerDay)
            + (self.seconds * self.millisecondsPerSecond)
            + round(self.microseconds * self.millisecondsPerMicroSecond)
        )

    def round(self, hours=0, minutes=0, seconds=0, alwaysUp=False):
        # """ Arrondissez le timedelta aux x unités les plus proches. """
        # assert [hours, minutes, seconds].count(0) >= 2
        # roundingUnit = hours * 3600 + minutes * 60 + seconds
        # if roundingUnit:
        #     # round_ = math.ceil if alwaysUp else legacy_round
        #     round_ = math.ceil if alwaysUp else round
        #     roundedSeconds = round_(self.totalSeconds() / roundingUnit) * roundingUnit
        #     # roundedSeconds = round_(self.totalSeconds() / float(roundingUnit)) * roundingUnit
        #     return self.__class__(0, roundedSeconds)
        # else:
        #     return self
        # """Arrondit le timedelta aux x unités les plus proches."""
        # rounding_unit = hours * 3600 + minutes * 60 + seconds
        # if rounding_unit:
        #     rounding_function = math.ceil if alwaysUp else round
        #     quotient, remainder = divmod(self.total_seconds(), rounding_unit)
        #     # Si le reste est supérieur à la moitié de l'unité d'arrondi, on arrondit au-dessus
        #     if remainder >= rounding_unit / 2:
        #         quotient += 1
        #     rounded_seconds = quotient * rounding_unit
        #     return self.__class__(0, rounded_seconds)
        # else:
        #     return self
        """Arrondit le timedelta aux x unités les plus proches.

        :param int hours: Nombre d'heures de l'unité d'arrondi.
        :param int minutes: Nombre de minutes de l'unité d'arrondi.
        :param int seconds: Nombre de secondes de l'unité d'arrondi.
        :param bool alwaysUp: Si True, arrondit toujours vers le haut.

        :returns : Un nouvel objet TimeDelta arrondi.
        """
        # Calcule de l'unité d'arrondi :
        # Les paramètres hours, minutes, seconds sont combinés
        # pour obtenir une valeur roundingUnit exprimant le nombre de secondes
        # correspondant à l'unité d'arrondi souhaitée :
        assert [hours, minutes, seconds].count(0) >= 2
        # Arrondi des secondes totales (valeur de l'unité d'arrondi) :
        roundingUnit = hours * 3600 + minutes * 60 + seconds
        #
        # Le nombre total de secondes de l'intervalle est divisé par roundingUnit
        # et le résultat est arrondi à l'entier le plus proche
        # (ou à l'entier supérieur si alwaysUp est True).
        if roundingUnit:
            # round_ = math.ceil if alwaysUp else legacy_round
            # rounding_function = math.ceil if alwaysUp else round
            # Le résultat de l'arrondi est multiplié par roundingUnit
            # pour obtenir le nombre de secondes arrondies.
            # roundedSeconds = rounding_function(self.totalSeconds() / roundingUnit) * roundingUnit
            # roundedSeconds = (
            # (self.totalSeconds() // roundingUnit) * roundingUnit
            # )
            # quotient: quantité (valeur à l'unité) d'arrondi.
            # remainder: reste de la division.
            quotient, remainder = divmod(self.total_seconds(), roundingUnit)
            # Si arrondir vers le haut est choisi (vrai) :
            if alwaysUp:
                # Si le reste est supérieur à 0, on arrondit au-dessus.
                if remainder > 0:
                    quotient += 1
            else:
                # Si le reste est supérieur à la moitié de l'unité d'arrondi, on arrondit au-dessus
                if remainder >= roundingUnit / 2:
                    quotient += 1
                # quotient += round(remainder)
            roundedSeconds = quotient * roundingUnit
            # Création d'un nouveau timedelta :
            #
            # Un nouveau timedelta est créé avec le nombre de secondes arrondies.
            return self.__class__(0, roundedSeconds)
        else:
            return self
        # if rounding_unit:
        #     quotient, remainder = divmod(self.total_seconds(), rounding_unit)
        #     quotient += int(alwaysUp or remainder >= rounding_unit / 2)
        #     rounded_seconds = quotient * rounding_unit
        #     return self.__class__(0, rounded_seconds)
        # else:
        #     return self
        # """ Round the timedelta to the nearest x units.
        #
        #        Args:
        #            hours: Number of hours to round to.
        #            minutes: Number of minutes to round to.
        #            seconds: Number of seconds to round to.
        #            alwaysUp: If True, always round up, otherwise round to the nearest unit.
        #            alwaysUp: Si c'est vrai, arrondissez toujours à l'unité supérieure, sinon arrondissez à l'unité la plus proche.
        #        Returns:
        #            A rounded timedelta object.
        # """
        # total_seconds = self.total_seconds()
        # if hours > 0:
        #     rounded_seconds = round(total_seconds / (hours * 3600)) * (hours * 3600)
        # elif minutes > 0:
        #     rounded_seconds = round(total_seconds / (minutes * 60)) * (minutes * 60)
        # elif seconds > 0:
        #     rounded_seconds = round(total_seconds / seconds) * seconds
        # else:
        #     rounded_seconds = total_seconds
        #
        # if alwaysUp and rounded_seconds != total_seconds:
        #     rounded_seconds += 1
        #
        # # return timedelta(seconds=rounded_seconds)
        # return self.__class__(0, rounded_seconds)
        #
        # # Example usage
        # # time_delta = timedelta(hours=2, minutes=30, seconds=45)
        # # rounder = TimedeltaRounder()
        # # rounded_time = rounder.round(minutes=15, alwaysUp=True)
        # # print(rounded_time)  # Output: 2:45:00 (rounded up to the nearest 15 minutes)
        # #
        # # Explications:
        # #
        # # * **`timedelta.total_seconds()`** : Cette méthode renvoie la durée en secondes.
        # # * **`round(..., alwaysUp=True)`**: Ce paramètre assure que la durée est toujours arrondie à la valeur supérieure.
        # # * **Calcul de l'arrondissement**: Les conditions `if` permettent de choisir l'unité à laquelle arrondir.
        # # * **Gestion de `alwaysUp`**: Cette condition arrondira toujours au chiffre supérieur si le paramètre `alwaysUp` est True.

    def __add__(self, other):
        """Assurez-vous que nous renvoyons une instance TimeDelta et non une instance
        datetime.timedelta."""
        timeDelta = super().__add__(other)
        return self.__class__(
            timeDelta.days, timeDelta.seconds, timeDelta.microseconds
        )

    def __sub__(self, other):
        timeDelta = super().__sub__(other)
        return self.__class__(
            timeDelta.days, timeDelta.seconds, timeDelta.microseconds
        )


ONE_SECOND = TimeDelta(seconds=1)
ONE_MINUTE = TimeDelta(minutes=1)
ONE_HOUR = TimeDelta(hours=1)
TWO_HOURS = TimeDelta(hours=2)
ONE_DAY = TimeDelta(days=1)
ONE_WEEK = TimeDelta(days=7)
ONE_YEAR = TimeDelta(days=365)


def parseTimeDelta(string):
    """
    Fonctionnalité :

    La méthode parseTimeDelta est conçue pour analyser une chaîne de caractères représentant un intervalle de temps au format heures:minutes:secondes et la convertir en un objet TimeDelta.

    Fonctionnement étape par étape :

    Analyse de la chaîne de caractères :
        La méthode tente de diviser la chaîne de caractères en trois parties (heures, minutes, secondes) en utilisant le caractère :.
        Chaque partie est convertie en un entier.

    Gestion des erreurs :
        Si une erreur se produit lors de l'analyse de la chaîne (par exemple, si le format n'est pas correct), la méthode capture l'exception ValueError et initialise les heures, minutes et secondes à zéro.

    Création de l'objet TimeDelta :
        Un nouvel objet TimeDelta est créé en utilisant les valeurs extraites de la chaîne de caractères (ou les valeurs par défaut si une erreur s'est produite).

    Exemple d'utilisation :
    Python

    interval_string = "2:30:15"
    delta = parseTimeDelta(interval_string)
    print(delta)  # Output : 2:30:15

    Utilisez ce code avec précaution.

    Cas d'utilisation :

    Cette méthode peut être utile dans diverses situations, notamment :

    Parsing d'intervalles de temps à partir de chaînes de caractères : Par exemple, pour analyser des durées spécifiées par l'utilisateur.
    Conversion de chaînes de temps en objets TimeDelta : Pour faciliter les calculs et manipulations d'intervalles de temps.

    En résumé, la méthode parseTimeDelta offre une manière simple et flexible
    de convertir des chaînes de caractères représentant des intervalles de temps
    en objets TimeDelta utilisables dans votre application.
    :param string:
    :return:
    """
    try:
        hours, minutes, seconds = [int(x) for x in string.split(":")]
    except ValueError:
        hours, minutes, seconds = 0, 0, 0
    return TimeDelta(hours=hours, minutes=minutes, seconds=seconds)
