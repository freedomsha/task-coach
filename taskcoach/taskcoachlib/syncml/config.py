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

"""

Classes for storing Funambol client configuration

"""

# from builtins import object


class SyncMLConfigNode(object):
    """A SyncMLConfigNode is a node in the SyncML configuration tree. It has a name,
    a list of children and a dictionary of properties.

    Un SyncMLConfigNode est un nœud dans l'arbre de configuration SyncML.
    Il a un nom, une liste d'enfants et un dictionnaire de propriétés.

    Methods :
    - children() : returns the list of children
    - properties() : returns the list of properties as (name, value) pairs
    - addChild(child) : adds a child to the list of children
    - get(name) : returns the value of the property with the given name, or "" if the property does not exist
    - set(name, value) : sets the value of the property with the given name to the given value
    - __getitem__(name) : returns the child with the given name, or raises KeyError if no such child exists
    """

    def __init__(self, name):
        """Initializes a SyncMLConfigNode with the given name, an empty list of children and an empty dictionary of properties.
        Initializes a SyncMLConfigNode avec le nom donné, une liste vide d'enfants et un dictionnaire vide de propriétés.

        Arguments:
        - name : the name of the node / le nom du nœud

        Attributes :
        - name : the name of the node / le nom du nœud
        - __children : the list of children / la liste des enfants
        - __properties : the dictionary of properties / le dictionnaire des propriétés
        """
        super().__init__()

        self.name = name

        self.__children = []
        self.__properties = {}

    def children(self):
        """
        Returns the list of children.
        Returns la liste des enfants.
        """
        return self.__children

    def properties(self):
        """
        Returns the list of properties as (name, value) pairs.
        Returns la liste des propriétés sous forme de paires (nom, valeur).
        """
        return list(self.__properties.items())

    def addChild(self, child):
        """
        Adds a child to the list of children.
        Ajoute un enfant à la liste des enfants.
        """
        self.__children.append(child)

    def get(self, name):
        """
        Returns the value of the property with the given name, or "" if the property does not exist.
        Returns la valeur de la propriété avec le nom donné, ou "" si la propriété n'existe pas.
        """
        return self.__properties.get(name, "")

    def set(self, name, value):
        """
        Sets the value of the property with the given name to the given value.
        Définit la valeur de la propriété avec le nom donné à la valeur donnée.
        """
        self.__properties[name] = value

    def __getitem__(self, name):
        """
        Returns the child with the given name, or raises KeyError if no such child exists.
        Returns l'enfant avec le nom donné, ou lève une erreur KeyError si aucun enfant de ce nom n'existe.
        """
        for child in self.__children:
            if child.name == name:
                return child
        raise KeyError(name)


def createDefaultSyncConfig(uid):
    """
    Creates a default SyncML configuration for the given uid.
    Crée une configuration SyncML par défaut pour le uid donné.

    Args :
        uid : the uid of the TaskCoach instance / le uid de l'instance TaskCoach

    Returns :
        a SyncMLConfigNode representing the default SyncML configuration for the given uid /
        un SyncMLConfigNode représentant la configuration SyncML par défaut pour le uid donné

        The default SyncML configuration for a TaskCoach instance with the given uid is as follows :
        La configuration SyncML par défaut pour une instance TaskCoach avec le uid donné est la suivante :
        <root>
            <TaskCoach-uid>
                <spds>
                    <sources>
                        <TaskCoach-uid.Tasks />
                        <TaskCoach-uid.Notes />
                    </sources>
                    <syncml>
                        <Auth />
                        <Conn />
                    </syncml>
                </spds>
            </TaskCoach-uid>
        </root>
    """
    cfg = SyncMLConfigNode("root")
    root = SyncMLConfigNode("TaskCoach-%s" % uid)
    cfg.addChild(root)
    spds = SyncMLConfigNode("spds")
    root.addChild(spds)
    sources = SyncMLConfigNode("sources")
    spds.addChild(sources)
    syncml = SyncMLConfigNode("syncml")
    spds.addChild(syncml)
    tasks = SyncMLConfigNode("TaskCoach-%s.Tasks" % uid)
    sources.addChild(tasks)
    notes = SyncMLConfigNode("TaskCoach-%s.Notes" % uid)
    sources.addChild(notes)
    auth = SyncMLConfigNode("Auth")
    syncml.addChild(auth)
    conn = SyncMLConfigNode("Conn")
    syncml.addChild(conn)

    return cfg
