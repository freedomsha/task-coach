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

from . import singleton as patterns


class Command(object):
    """
    Base class for all commands.

    Methods:
        do(): Execute the command and append it to the command history.
        undo(): Undo the command.
        redo(): Redo the command.
        __str__(): Return a string representation of the command.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the command.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__()  # object.__init__ takes no arguments

    def do(self):
        """
        Execute the command and append it to the command history.
        """
        CommandHistory().append(self)

    def undo(self):
        """
        Undo the command.
        """
        pass

    def redo(self):
        """
        Redo the command.
        """
        pass

    def __str__(self):
        """
        Return a string representation of the command.

        Returns:
            str: The string representation of the command.
        """
        return "command"


class CommandHistory(object, metaclass=patterns.Singleton):
    """
    Singleton class that keeps track of command history.

    Attributes:
        __history (list): The list of executed commands.
        __future (list): The list of commands that have been undone and can be redone.

    Methods:
        append(command): Add a command to the history.
        undo(): Undo the last command.
        redo(): Redo the last undone command.
        clear(): Clear the command history.
        hasHistory(): Check if there are executed commands in the history.
        getHistory(): Get the list of executed commands.
        hasFuture(): Check if there are commands that can be redone.
        getFuture(): Get the list of commands that can be redone.
        undostr(label): Get a string label for the undo operation.
        redostr(label): Get a string label for the redo operation.
    """

    def __init__(self):
        """
        Initialize the command history with empty lists for history and future commands.
        """
        self.__history = []
        self.__future = []

    def append(self, command):
        """
        Add a command to the history and clear the future commands.

        Args:
            command (Command): The command to add to the history.
        """
        self.__history.append(command)
        del self.__future[:]

    def undo(self):
        """
        Undo the last command and add it to the future commands list.
        """
        if self.__history:
            command = self.__history.pop()
            command.undo()
            self.__future.append(command)

    def redo(self):
        """
        Redo the last undone command and add it back to the history.
        """
        if self.__future:
            command = self.__future.pop()
            command.redo()
            self.__history.append(command)

    def clear(self):
        """
        Clear the command history and future commands.
        """
        del self.__history[:]
        del self.__future[:]

    def hasHistory(self):
        """
        Check if there are executed commands in the history.

        Returns:
            list: The list of executed commands.
        """
        return self.__history

    def getHistory(self):
        """
        Get the list of executed commands.

        Returns:
            list: The list of executed commands.
        """
        return self.__history

    def hasFuture(self):
        """
        Check if there are commands that can be redone.

        Returns:
            list: The list of commands that can be redone.
        """
        return self.__future

    def getFuture(self):
        """
        Get the list of commands that can be redone.

        Returns:
            list: The list of commands that can be redone.
        """
        return self.__future

    def _extendLabel(self, label, commandList):
        """
        Extend the label with the name of the last command in the command list.

        Args:
            label (str): The label to extend.
            commandList (list): The list of commands.

        Returns:
            str: The extended label.
        """
        if commandList:
            commandName = " %s" % commandList[-1]
            label += commandName.lower()
        return label

    def undostr(self, label="Undo"):
        """
        Get a string label for the undo operation.

        Args:
            label (str): The base label for the undo operation.

        Returns:
            str: The extended label for the undo operation.
        """
        return self._extendLabel(label, self.__history)

    def redostr(self, label="Redo"):
        """
        Get a string label for the redo operation.

        Args:
            label (str): The base label for the redo operation.

        Returns:
            str: The extended label for the redo operation.
        """
        return self._extendLabel(label, self.__future)
