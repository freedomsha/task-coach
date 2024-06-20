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

from taskcoachlib import patterns


class Collection(patterns.CompositeSet):
    """
    A collection class that extends CompositeSet from taskcoachlib.patterns.

    This class represents a collection of domain objects and provides a method
    to retrieve an object by its ID.
    """

    def getObjectById(self, domainObjectId):
        """
        Get an object from the collection by its ID.

        Args:
            domainObjectId (str): The ID of the domain object to retrieve.

        Returns:
            The domain object with the specified ID.

        Raises:
            IndexError: If no object with the specified ID is found in the collection.
        """
        for domainObject in self:
            if domainObjectId == domainObject.id():
                return domainObject
        raise IndexError
