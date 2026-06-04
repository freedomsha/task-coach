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
    Une classe de collection qui étend CompositeSet de taskcoachlib.patterns
    qui représente un ensemble d'objets composites observables.

    Hérite de CompositeCollection et de ObservableSet
    pour gérer les composites et leurs relations parent/enfant
    et avertir les observateurs quand un élément est ajouté ou supprimé.

    Cette classe représente une collection d'objets de domaine et
    fournit la méthode getObjectById pour récupérer un objet par son ID.
    """

    def getObjectById(self, domainObjectId):
        """
        Récupère un objet de la collection par son ID.

        Args :
            domainObjectId (str) : L'ID de l'objet de domaine à récupérer.

        Returns :
            L'objet de domaine avec l'ID spécifié.

        Raises :
            IndexError : Relève unr erreur si aucun objet avec l'ID spécifié n'est trouvé dans la collection.
        """
        for domainObject in self:
            if domainObjectId == domainObject.id():
                return domainObject
        raise IndexError
