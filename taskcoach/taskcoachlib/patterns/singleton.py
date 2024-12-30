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


class Singleton(type):
    """Singleton metaclass. Use by defining the metaclass of a class Singleton,
    e.g.: class ThereCanBeOnlyOne:
              __metaclass__ = Singleton

    Called when the instance is "called" in function;
    if this method is defined,
    x(arg1, arg2, ...) roughly translates to type(x).__call__(x, arg1, . ..).
    The object class itself does not provide this method.

        :param *args: Variable length argument list.
        :param **kwargs: Arbitrary keyword arguments.
        :return:
    """

    # instance = None  # Singleton attribute containing the instance
    # hasInstance = None  # Singleton attribute containing the instance

    # is it a @classmethod ?
    # @classmethod
    def __call__(class_, *args, **kwargs):
        if not class_.hasInstance():
            # pylint: disable=W0201
            class_.instance = super(Singleton, class_).__call__(
                *args, **kwargs
            )
            # class_.instance = super().__call__(*args, **kwargs)
        return class_.instance

    # @classmethod
    def deleteInstance(class_) -> None:
        """Delete the (only) instance. This method is mainly for unittests so
        they can start with a clean slate."""
        if class_.hasInstance():
            del class_.instance

    # @classmethod
    def hasInstance(class_) -> bool:
        """Has the (only) instance been created already?"""
        return "instance" in class_.__dict__
