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

# from __future__ import division

# from past.utils import old_div
import datetime
import re
import time
from . import timedelta
from .date import Date
from .fix import StrftimeFix


class DateTime(StrftimeFix, datetime.datetime):
    secondsPerMinute = 60
    minutesPerHour = 60
    hoursPerDay = 24
    secondsPerHour = minutesPerHour * secondsPerMinute
    secondsPerDay = hoursPerDay * secondsPerHour

    def __new__(class_, *args, **kwargs):
        if not args and not kwargs:
            max = datetime.datetime.max  # pylint: disable=W0622
            args = (
                max.year,
                max.month,
                max.day,
                max.hour,
                max.minute,
                max.second,
                max.microsecond,
            )
        return datetime.datetime.__new__(class_, *args, **kwargs)

    @staticmethod
    def fromDateTime(dateTime):
        return DateTime(
            year=dateTime.year,
            month=dateTime.month,
            day=dateTime.day,
            hour=dateTime.hour,
            minute=dateTime.minute,
            second=dateTime.second,
            microsecond=dateTime.microsecond,
        )

    def date(self):
        return Date(self.year, self.month, self.day)

    def weeknumber(self):
        return self.isocalendar()[1]

    def weekday(self):
        return self.isoweekday()  # Sunday = 7, Monday = 1, etc.

    def toordinal(self):
        """Return the ordinal number of the day, plus a fraction between 0 and
        1 for parts of the day."""
        ordinal = super().toordinal()
        seconds = (
            self.hour * self.secondsPerHour
            + self.minute * self.secondsPerMinute
            + self.second
        )
        # return ordinal + (old_div(seconds, self.secondsPerDay))
        return ordinal + (seconds / float(self.secondsPerDay))

    def startOfDay(self):
        return self.replace(hour=0, minute=0, second=0, microsecond=0)

    def endOfDay(self):
        return self.replace(hour=23, minute=59, second=59, microsecond=999999)

    def startOfWeek(self):
        days = self.weekday()
        monday = self - timedelta.TimeDelta(days=days - 1)
        return DateTime(monday.year, monday.month, monday.day)

    def endOfWeek(self):
        days = self.weekday()
        sunday = self + timedelta.TimeDelta(days=7 - days)
        return DateTime(sunday.year, sunday.month, sunday.day).endOfDay()

    def startOfWorkWeek(self):
        days = self.weekday()
        monday = self - timedelta.TimeDelta(days=days - 1)
        return DateTime(monday.year, monday.month, monday.day)

    def endOfWorkWeek(self):
        days = 5 - self.weekday()
        if days < 0:
            days += 7
        friday = self + timedelta.TimeDelta(days=days)
        return DateTime(friday.year, friday.month, friday.day).endOfDay()

    def startOfMonth(self):
        return DateTime(self.year, self.month, 1)

    def endOfMonth(self):
        for lastday in [31, 30, 29, 28]:
            try:
                return DateTime(self.year, self.month, lastday).endOfDay()
            except ValueError:
                pass

    def startOfYear(self):
        return DateTime(self.year, 1, 1).startOfDay()

    def endOfYear(self):
        return DateTime(self.year, 12, 31).endOfDay()

    def __sub__(self, other):
        """Make sure substraction returns instances of the right classes."""
        if self == DateTime() and isinstance(other, datetime.datetime):
            max = timedelta.TimeDelta.max  # pylint: disable=W0622
            return timedelta.TimeDelta(max.days, max.seconds, max.microseconds)
        result = super().__sub__(other)
        if isinstance(result, datetime.timedelta):
            result = timedelta.TimeDelta(
                result.days,
                result.seconds,
                result.microseconds,
            )
        elif isinstance(result, datetime.datetime):
            result = self.__class__(
                result.year,
                result.month,
                result.day,
                result.hour,
                result.minute,
                result.second,
                result.microsecond,
            )
        return result

    def __add__(self, other):
        result = super().__add__(other)
        return self.__class__(
            result.year,
            result.month,
            result.day,
            result.hour,
            result.minute,
            result.second,
            result.microsecond,
        )


DateTime.max = DateTime(datetime.datetime.max.year, 12, 31).endOfDay()
DateTime.min = DateTime(datetime.datetime.min.year, 1, 1).startOfDay()


def parseDateTime(string, *timeDefaults):
    """
    Méthode d'analyse de la date et de l'heure.

    Args :
        string : Date (et heure) à analyser.
        *timeDefaults : Heure par défaut.

    Returns : None si string est vide ou égal à None, sinon renvoie une date
              au format (year, month, day, hour:minute:second:microsecond)
              avec l'heure actuelle s'il n'y a que year, month et day.

    """
    # Si string est vide ou égal à None alors retourne None
    if string in ("", "None"):
        # print("dateandtime.parseDateTime : La date string est vide")
        return None
    # sinon renvoie une date au format (year, month, day, hour:minute:second:microsecond)
    else:
        # Sépare string en une liste args d'arg au format int.
        # print(f"dateandtime.parseDateTime : La date string = {string}.")
        args = [int(arg) for arg in re.split("[-:. ]", string)]
        # print(f"La liste d'arguments de date args = {args}")
        # Si la liste contient 3 éléments, il s'agit d'une date sans heures. On ajoute l'heure par défaut.
        if len(args) == 3:  # We parsed a date, no time
            args.extend(timeDefaults)
        # print(f"La liste d'arguments ajustée args = {args}")
        # print(f"dateandtime.parseDateTime : Le retour de parseDateTime = {DateTime(*args)}")
        return DateTime(*args)  # pylint: disable=W0142


def Now():
    return DateTime.now()


def Today():
    # For backwards compatibility: "Today()" may be used in templates
    return Now().replace(hour=0, minute=0, second=0, microsecond=0)


def Tomorrow():
    return Now() + timedelta.ONE_DAY


def Yesterday():
    return Now() - timedelta.ONE_DAY


def LastDayOfCurrentMonth(localtime=time.localtime):
    now = localtime()
    year, nextMonth = now[0], now[1] + 1
    if nextMonth > 12:
        nextMonth = 1
        year += 1
    return DateTime(year, nextMonth, 1) - timedelta.ONE_DAY
