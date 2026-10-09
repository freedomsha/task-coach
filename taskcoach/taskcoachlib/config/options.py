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

import optparse  # pour analyser les options de ligne de commande
# https://docs.python.org/fr/3/library/optparse.html
# Obsolète depuis la version 3.2 :
# The optparse module is deprecated and will not be developed further;
# development will continue with the argparse module.
# Déprécié depuis la version 3.2 :
# le module optparse est déprécié et ne sera plus développé ;
# le développement se poursuivra avec le module argparse.
# https://docs.pyth on.org/3/library/argparse.html#module-argparse
# https://docs.python.org/fr/3.11/library/optparse.html#module-optparse

# from ...taskcoachlib import meta
from taskcoachlib import meta


# copie de la classe OptionParser pour chaque objet-instance utilisant OptionParser héritée de optparse.OptionParser
class OptionParser(optparse.OptionParser, object):
    """ subclass to control command line options.

    Usage:
    ======
        only methods to control command line options
    """
    # sous-classe d'optparse.OptionParser pour contrôler les options de ligne de commande.
    def __init__(self, *args, **kwargs):
        """ constructor """
        # constructeur
        # Une méthode constructeur a ceci de particulier qu'elle est exécutée automatiquement
        # lorsque l'on instancie un nouvel objet à partir de la classe.
        # On peut donc y placer tout ce qui semble nécessaire pour initialiser automatiquement l'objet que l'on crée.
        # paramètres:
        # *args : les arguments passés en paramètre sont empaquetés dans args qui se comporte comme un tuple
        # **kwargs: les arguments passés en paramètre sont empaquetés dans kwargs qui se comporte comme un dictionnaire
        # retours:
        #
        # https://docs.python.org/fr/3.8/library/functions.html?highlight=classe%20super#super
        # Renvoie un objet mandataire déléguant les appels de méthode à une classe parente ou sœur de type OptionParser.
        # C'est utile pour accéder aux méthodes __init__ héritées qui ont été remplacées dans la classe.
        super().__init__(*args, **kwargs)
        # variables d'instance uniques pour chaque instance :
        # appel des méthodes addoptiongroups et addoptions pour l'instance courante:
        self.__addOptionGroups()
        self.__addOptions()

    def __addOptionGroups(self):
        # méthode pour
        self.__getAndAddOptions("OptionGroup", self.add_option_group)

    def __addOptions(self):
        # méthode pour
        self.__getAndAddOptions("Option", self.add_option)

    def __getAndAddOptions(self, suffix, addOption):
        # méthode pour obtenir et ajouter des options
        for getOption in self.__methodsEndingWith(suffix):
            addOption(getOption(self))

    def __methodsEndingWith(self, suffix):
        # méthode pour
        return [method for name, method in list(vars(self.__class__).items()) if
                name.endswith(suffix)]


class OptionGroup(optparse.OptionGroup, object):
    # classe option de groupe
    pass


class ApplicationOptionParser(OptionParser):
    """ subclass of OptionParser to control command line options.

    Usage:
    ======
        only methods to control command line options.
    """
    # sous-classe de OptionParser créé précédemment pour contrôler les options de ligne de commande.
    def __init__(self, *args, **kwargs):
        # constructeur
        kwargs["usage"] = "usage: %prog [options] [.tsk file]"
        kwargs["version"] = "%s %s" % (meta.data.name, meta.data.version)
        super(ApplicationOptionParser, self).__init__(*args, **kwargs)

    # utilisation de la méthode optparse.Option plutôt que optparse.OptionParser.add_option
    # @staticmethod
    # def profileOption(self):
    def profileOption(self):
        """ methode to add a profile option.

        method to add an option type flag to use a profile"""
        # méthode d'ajout de l'option profile
        #
        # Méthode de type drapeau pour activer l'utilisation d'un profile ou non
        # l'aide est cachée
        #
        # retour:
        #   optparse.Option
        #   --profile
        return optparse.Option("--profile", default=False,
                               action="store_true", help=optparse.SUPPRESS_HELP)

    # @staticmethod
    def profile_skipstartOption(self):
        # def profile_skipstartOption():
        """ method to add an option for skip to start.

        Méthode d'ajout de l'option -s ou skipstart

         Méthode de type drapeau pour activer ou non le démarrage

         Returns:
           optparse.Option
           -s ou --skipstart
        """
        return optparse.Option("-s", "--skipstart", default=False,
                               action="store_true", help=optparse.SUPPRESS_HELP)

    # @staticmethod
    def iniOption(self):
        # def iniOption():
        """ method to add an option for use an inifile. """
        # méthode d'ajout de l'option -i ou ini pour spécifier un INIFILE
        #
        # Cette méthode renvoie l'ajout de l'option -i(--ini)
        # pour préciser le fichier inifile à utiliser pour enregistrer les réglages.
        return optparse.Option("-i", "--ini", dest="inifile",
                               help="use the specified INIFILE for storing settings")

    # @staticmethod
    def languageOption(self):
        # def languageOption():
        """ method to add an option for use a specific language.

        This method return to add the option_class -l or --language to use for the GUI
        (e.g. "nl" or "fr")
        """
        # méthode d'ajout de l'option -l ou language pour spécifier la langue
        #
        # Cette méthode renvoie l'ajout de l'option -l(--language)
        # pour préciser le choix de la langue utilisée dans le GUI.(avec 2 lettres)
        #
        # retour:
        #   optparse.Option
        #   -l XX ou --language XX
        #   utilise le language spécifié pour le GUI (exemple "en", "nl" ou "fr")
        #   parmi celles contenues dans meta.data (choix parmi des strings)
        return optparse.Option("-l", "--language", dest="language",
                               type="choice", choices=sorted([lang for (lang, enabled) in
                                                              list(meta.data.languages.values()) if
                                                              lang is not None] + ["en"]),
                               help="use the specified LANGUAGE for the GUI (e.g. nl or fr")

    # @staticmethod
    def poOption(self):
        # def poOption():
        """ method to add an option for use a specific 'pofile'.

        This method return to add the option_class -p or --po to use a pofile.
        """
        # Méthode d'ajout de l'option -p pour préciser quel POFILE pour l'interface.
        #
        # Cette méthode renvoie l'ajout de l'option_class -p ou --po pour prendre en compte un fichier pofile
        #
        # Retour :
        # optparse.Option
        #   -p X.po ou --po X.po avec le nom du pofile
        #   utilise le POFILE spécifié pour traduire le GUI
        #   le nom attendu est de type string
        return optparse.Option("-p", "--po", dest="pofile",
                               help="use the specified POFILE for translation of the GUI")
