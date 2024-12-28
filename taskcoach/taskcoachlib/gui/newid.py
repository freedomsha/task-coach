"""
Task Coach - Your friendly task manager
Copyright (C) 2019 Task Coach developers <developers@taskcoach.org>

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

import wx


class IdProvider(set):
    """
    Identifier provider for user interface elements in wxPython.

    This class manages the unique identifiers needed for user interface elements,
    avoiding conflicts and ensuring identifier availability.
    """

    def get(self):
        """
        Get a new unique identifier.

        This method generates a new unique identifier using wx.ID_ANY (not wx.NewIdRef()) and adds it
        to the set of identifiers managed by this class.

        Returns:
            int: A new unique identifier.
        """
        if self:
            return self.pop()

        return wx.ID_ANY

    def put(self, id_):
        """
        Release identifier.

        This method removes the specified identifier from the set of identifiers managed by
        this class, making it available for future reuse.

        Args:
            id_ (int): The identifier to release.
        """
        if id_ > 0:
            self.add(id_)


# Create a single instance of IdProvider for use in the application.
IdProvider = IdProvider()
