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

# from future import standard_library
# standard_library.install_aliases()
# from builtins import object
from taskcoachlib.patterns import singleton as patterns


class Command(object):
    """
    Classe de base pour toutes les commandes.

    Méthodes :
        do() : Exécute la commande et l'ajoute à l'historique des commandes.
        undo() : Annule la commande.
        redo() : Refaites la commande.
        __str__() : renvoie une représentation sous forme de chaîne de la commande.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialisez la commande.

        Args :
            *args : Liste d'arguments de longueur variable.
            **kwargs : Arguments de mots clés arbitraires.
        """
        super().__init__()  # object.__init__ takes no arguments

    def do(self) -> None:
        """
        Exécutez la commande et ajoutez-la à l’historique des commandes.
        """
        CommandHistory().append(self)

    def undo(self) -> None:
        """
        Annulez la commande.
        """
        pass

    def redo(self) -> None:
        """
        Refaites la commande.
        """
        pass

    # def __str__(self):
    def __str__(self) -> str:
        """
        Renvoie une représentation sous forme de chaîne de la commande.

        Renvoie :
            str : La représentation sous forme de chaîne de la commande.
        """
        return "command"


class CommandHistory(object, metaclass=patterns.Singleton):
    """
    Classe Singleton qui garde une trace de l'historique des commandes.

    Attributs :
        __history (list) : La liste des commandes exécutées.
        __future (list) : La liste des commandes qui ont été annulées et peuvent être redone.

    Méthodes :
        append(command) : Ajouter une commande à l'historique.
        undo() : Annuler la dernière commande.
        redo() : Refaire la dernière commande annulée.
        clear() : Effacer l'historique des commandes.
        hasHistory() : Vérifiez s'il y a des commandes exécutées dans l'historique.
        getHistory() : Obtenez la liste des commandes exécutées.
        hasFuture() : Vérifiez si des commandes peuvent être rétablies.
        getFuture() : Obtenez la liste des commandes qui peuvent être rétablies.
        undostr(label) : Obtenez une étiquette de chaîne pour l'opération d'annulation.
        redostr(label) ) : Obtenez une étiquette de chaîne pour l’opération de rétablissement.
    """

    def __init__(self) -> None:
        """
        Initialisez l'historique des commandes avec des listes vides pour l'historique et les commandes futures.
        """
        self.__history = []
        self.__future = []

    def append(self, command) -> None:
        """
        Ajoutez une commande à l'historique et effacez les futures commandes.

        Args :
            command (Command) : La commande à ajouter à l'historique.
        """
        self.__history.append(command)
        del self.__future[:]

    def undo(self) -> None:
        """
        Annulez la dernière commande et ajoutez-la à la liste des commandes futures.
        """
        if self.__history:
            command = self.__history.pop()
            command.undo()
            self.__future.append(command)

    def redo(self) -> None:
        """
        Refaites la dernière commande annulée et ajoutez-la à l'historique.
        """
        if self.__future:
            command = self.__future.pop()
            command.redo()
            self.__history.append(command)

    def clear(self) -> None:
        """
        Effacez l’historique des commandes et les commandes futures.
        """
        del self.__history[:]
        del self.__future[:]

    def hasHistory(self) -> bool:
        """
        Vérifiez s'il y a des commandes exécutées dans l'historique.

        Renvoie :
            list : La liste des commandes exécutées.
        """
        # renvoie une liste, un bool ne serait pas mieux ?
        return self.__history != []

    def getHistory(self):
        """
        Obtenez la liste des commandes exécutées.

        Renvoie :
            list : La liste des commandes exécutées.
        """
        return self.__history

    def hasFuture(self):
        """
        Vérifiez s'il existe des commandes qui peuvent être rétablies.

        Renvoie :
            list : La liste des commandes qui peuvent être rétablies.
        """
        return self.__future != []

    def getFuture(self):
        # def getFuture(self) -> list:
        """
        Obtenez la liste des commandes qui peuvent être rétablies.

        Renvoie :
            list : La liste des commandes qui peuvent être rétablies.
        """
        return self.__future

    def _extendLabel(self, label, commandList):
        # def _extendLabel(self, label: str, commandList: list) -> str:
        """
        Prolongez l'étiquette avec le nom de la dernière commande de la liste des commandes.

        Args :
            label (str) : L'étiquette à étendre.
            commandList (list) : La liste des commandes.

        Renvoie :
            str : L'étiquette étendue.
        """
        if commandList:
            commandName = " %s" % commandList[-1]
            label += commandName.lower()
        return label

    def undostr(self, label: str = "Undo"):
        # def undostr(self, label="Undo") -> str:
        """
        Obtenez une étiquette de chaîne pour l'opération d'annulation.

        Args :
            label (str) : L'étiquette de base pour l'opération d'annulation.

        Renvoie :
            str : L'étiquette étendue pour l'opération d'annulation.
        """
        return self._extendLabel(label, self.__history)

    def redostr(self, label: str = "Redo"):
        # def redostr(self, label: str = "Redo") -> str:
        """
        Obtenez une étiquette de chaîne pour l'opération de rétablissement.

        Args :
            label (str) : L'étiquette de base pour l'opération de rétablissement.

        Renvoie :
            str : L'étiquette étendue pour l'opération de rétablissement.
        """
        return self._extendLabel(label, self.__future)
