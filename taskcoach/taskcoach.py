#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

taskcoach.py est le point d'entrée principal. Il :

    Configure le logging (déjà fait ✅),

    Prépare l’environnement (OS, sys.path, etc.),

    Tente d’importer taskcoachlib,

    Gère les arguments de la ligne de commande,

    Lance l’application (Application.start()).
"""

# Programme principal
# importer la bibliothèque pour enregistrer les événements
# voir https://docs.python.org/fr/3.12/library/logging.html pour son implantation
import logging
import logging.handlers

# et pour la gestion de la date et de l'heure dans les noms de fichiers de log
from datetime import datetime

from taskcoachlib.config.arguments import CURRENT_GUI

# Créer un enregistreur de niveau module
log = logging.getLogger(__name__)


def namer(name):
    # return "/log/" + name + ".txt"
    return name + ".log"
    # Avec la date et l'heure :
    # return name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    # return name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M") + ".txt"


def rotator(source, dest):
    with open(source, "rb") as f_in:
        with open(dest, "wb") as f_out:
            f_out.write(f_in.read())
    os.remove(source)


# --- Ajout pour supprimer les logs DEBUG de Pillow (PIL) ---
logging.getLogger("PIL").setLevel(logging.WARNING)
# --------------------------------------------------------
# Il reste à utiliser cet enregistreur pour effectuer toute journalisation nécessaire.
# Les messages enregistrés vers l’enregistreur d’images au niveau du module
# seront transmis aux gestionnaires d’enregistreurs dans les modules de niveau supérieur,
# jusqu’à l’enregistreur d’événements de niveau supérieur
# connu sous le nom d’enregistreur racine (ici);
# Cette approche est connue sous le nom de journalisation hiérarchique.

# La bibliothèque de journalisation adopte une approche modulaire et
# offre différentes catégories de composants : loggers, handlers, filters et formatters.
#
#     Les enregistreurs (loggers en anglais)
#       exposent l'interface que le code de l'application utilise directement.
#
#     Les gestionnaires (handlers)
#       envoient les entrées de journal (créés par les loggers)
#       vers les destinations voulues.
#
#     Les filtres (filters)
#       fournissent un moyen de choisir finement quelles entrées de journal
#       doivent être sorties.
#
#     Les formateurs (formatters)
#       spécifient la structure de l'entrée de journal dans la sortie finale.

# TODO : Faire un tri selon les dossiers name importants (application, changes, command,
#  config, domain, filesystem, gui, help, i18n, iphone, mailer, meta, notify, patterns,
#  persistence, powermgt, speak, syncml, thirdparty, tools, widgets, workaround)
# logging.getLogger("__main__").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.application").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.filesystem").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.config.settings").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.application.application").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.persistence.taskfile").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.gui.mainwindow").setLevel(logging.INFO)
logging.getLogger("taskcoachlib.gui.menu").setLevel(logging.WARNING)
logging.getLogger("taskcoachlib.gui.uicommand.settings_uicommand").setLevel(
    logging.INFO
)
logging.getLogger("taskcoachlib.gui.toolbar").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.widgets.treectrl").setLevel(logging.INFO)
# logging.getLogger("taskcoachlib.widgets.itemctrl").setLevel(logging.INFO)
logging.getLogger("taskcoachlib.widgets.autowidth").setLevel(logging.INFO)
logging.getLogger("taskcoachlib.widgets.tooltip").setLevel(logging.INFO)

filename_dated = "taskcoach_" + datetime.now().strftime("%Y%m%d%H%M") + ".log"
rh = logging.handlers.RotatingFileHandler(
    # "taskcoach.log", maxBytes=1024000, backupCount=50
    filename_dated,
    maxBytes=1024000,
    backupCount=50,
)
rh.rotator = rotator
rh.namer = namer

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, Tu peux passer à INFO ou WARNING en production
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        # logging.FileHandler("taskcoach.log", mode='w', encoding='utf-8'),
        # logging.handlers.RotatingFileHandler(
        #     "taskcoach.log", mode="w", encoding="utf-8"
        # ),
        rh,
        logging.StreamHandler(),  # Affiche aussi dans la console
    ],
)


# importer les bibliothèques permettant l'interface pour le système d'exploitation
import os

# et les paramètres et les variables propres au système
import sys

# autour d'un bug dans Ubuntu 10.10
# Fixe une variable d'environnement
os.environ["XLIB_SKIP_ARGB_VISUALS"] = "1"

# Cela prévient un message de la console quand wx.lib.masked
# est importé de taskcoachlib.widget sur Ubuntu 12.04 64bits

# try:
#     from mx import DateTime  # Essayer d'importer la Class DateTime,
# except ImportError:
#     pass  # si erreur ne rien faire
log.info("****************************************************************")
log.info(
    "*               D\u00e9marrage de Task Coach                          *"
)
log.info("****************************************************************")

if not hasattr(sys, "frozen"):
    # ces vérifications sont seulement nécessaires dans un environnement non-frozen,
    # i.e. nous passons ces vérifications quand il tourne depuis une application py2exe.fied
    # wxpython: wxversion non intégré sur python3 donc à ignorer :
    # remplacé par wx.__version__ donc ne plus importer wxversion.
    # https://docs.python.org/fr/3/howto/pyporting.html
    log.info("Environnement non frozen détecté (mode développement)")
    # try:
    #     import wxversion  # in python 3 try with wx.__version__
    #     # from wx.core import __version__ as wxversion  # ?
    #
    #     wxversion.select(["2.8-unicode", "3.0"], optionsRequired=True)
    #     # __version__.select(["2.8-unicode", "3.0"], optionsRequired=True)
    # except ImportError:
    #     # There is no wxversion for py3
    #     # Il n'y a aucun wxversion pour py3
    #     pass
    # except AttributeError:
    #    print(
    #        'wxversion.select(["2.8-unicode", "3.0"], optionsRequired=True) AttributeError: '
    #        "str object has no attribute select"
    #    )
    #    pass

    try:
        import taskcoachlib  # pylint: disable=W0611

        # d'apres https://diveintopython3.net/porting-code-to-python-3-with-2to3.html
    except ImportError:
        # On Ubuntu 12.04, taskcoachlib is installed in /usr/share/pyshared,
        # but that folder is not on the python path. Don't understand why.
        # We'll add it manually so the application can find it.
        # https://docs.python.org/fr/3.11/library/sys.html
        sys.path.insert(
            0, "/usr/share/pyshared"
        )  # ajoute à la variable d'environnement PYTHONPATH
        log.warning(
            "taskcoachlib introuvable, ajout manuel de /usr/share/pyshared au PYTHONPATH"
        )
        try:
            import taskcoachlib  # pylint: disable=W0611  # noqa: F401
        except ImportError:
            # si erreur écrire une erreur dans le log et sortir
            log.error(
                "Impossible d'importer 'taskcoachlib' m\u00eame apr\u00e8s avoir modifi\u00e9 sys.path"
            )
            sys.stderr.write(
                """ERROR: cannot import the library 'taskcoachlib'.
                Please see https://answers.launchpad.net/taskcoach/+faq/1063
                for more information and possible resolutions.
                ERREUR: Impossible d'importer la librairie 'taskcoachlib'.
                Voir l'adresse pour plus d'information et de possibles résolution.
                """
            )
            sys.exit(
                1
            )  # quitte le programme suite à une erreur autre que syntaxe
else:
    log.debug("Environnement frozen détecté (exécutable)")


def start():
    """Traîte les options (arguments) de ligne de commande et démarre l'application.

    Cette fonction traite les options de ligne de commande, initialise l'application
    et démarre/lance la boucle principale. Il gère également le profilage si l'option --profile
    est spécifiée.
    """
    # Correctif pour wxPython 4+ (Phoenix)
    # L'erreur "assert traits failed" survient car la configuration tente d'accéder
    # aux chemins système (wx.StandardPaths) avant que l'application wx ne soit créée.
    try:
        import wx

        if wx.GetApp() is None:
            _dummy_app = wx.App(False)
    except ImportError:
        pass

    # pylint: disable=W0404
    from taskcoachlib import application
    from taskcoachlib import config

    # from taskcoachlib.config import arguments
    # import des bibliothèques configurations-options et de l'application

    # options, args = config.ApplicationOptionParser().parse_args()
    # méthode de vérification des définitions des variables options et args de config avec optparse :
    # options = config.ApplicationArgumentParser().parser.parse_args()
    # avec argparse :
    # La méthode exécute l'analyseur syntaxique et places les données extraites dans un objet argparse.Namespace
    # args = config.ApplicationArgumentParser().parse_args()
    # pour diviser en 2 parties
    # Parfois, un script n'analyse que quelques-uns des arguments de la ligne de commande
    # avant de passer les arguments non-traités à un autre script ou programme.
    # La méthode parse_known_args() est utile dans ces cas. Elle fonctionne similairement à parse_args(),
    # mais elle ne lève pas d'erreur quand des arguments non-reconnus sont présents.
    # Au lieu, elle renvoie une paire de valeurs : l'objet Namespace rempli et la liste des arguments non-traités.
    # options, args = config.ApplicationArgumentParser().parse_known_args()
    # voir aussi:
    # De nombreuses commandes Unix permettent à l'utilisateur
    # d'entremêler les arguments optionnels et les arguments positionnels.
    # Les méthodes parse_intermixed_args() et parse_known_intermixed_args() permettent ce style d'analyse.
    # Ces analyseurs ne prennent pas en charge toutes les fonctionnalités d'argparse et
    # généreront des exceptions si des fonctionnalités non prises en charge sont utilisées.
    # En particulier, les sous-analyseurs et les groupes mutuellement exclusifs
    # qui incluent à la fois des options et des positions ne sont pas pris en charge.
    # nouvelle méthode à essayer
    # options: argparse.Namespace
    # args: list[str]
    # options, args = config.ApplicationArgumentParser().parser.parse_known_intermixed_args()
    parser = config.ApplicationArgumentParser()
    options, args = parser.parse_args()
    # options, args = (
    #     config.ApplicationArgumentParser().parser.parse_known_args()
    # )
    # en utilisant l'astuce de The Namespace object dans https://docs.python.org/3.11/library/argparse.html
    # options = vars(tcoptions)
    # options = vars(options)
    # print(vars(options), args)
    # print(f"taskcoach.py: options:{vars(options)} args:{args}")
    log.info(
        "Arguments analys\u00e9s : options=%s, args=%s", vars(options), args
    )

    # Définir le GUI global (pour tous les modules)
    from taskcoachlib.config.arguments import set_gui

    set_gui(options.gui_name)

    app = None
    if options.gui_name == "wx":
        # Lancement de l'initialisation de l'application version wxPython:
        log.debug("start : Lancement de la version wxPython.")
        app = application.application.Application(
            options, args
        )  # définition de la variable app comme application avec options et args
        # app = application.Application(tcargs)
    elif options.gui_name == "tk":
        # Lancement de l'initialisation de l'application version tkinter:
        log.debug("start : Lancement de la version tkinter.")
        app = application.tkapplication.TkinterApplication(options, args)
        # print("taskcoach.py: options.profile:", options.profile)  # is False !
    log.debug("Option --profile active : %s", options.profile)
    # Lancement de l'application :
    # Il est impératif d'appeler explicitement app.init() avant de démarrer l'application,
    # car c'est cette méthode qui charge les préférences utilisateur et prépare l'interface.
    app.init()  # logique, 2nd appel d'init (le 1er est dans tkapplication.TkinterApplication.__init)

    if options.profile:
        # if options["profile"]:
        import cProfile

        log.info("Mode profilage activ\u00e9, d\u00e9marrage avec cProfile.")
        # Lance app.start() et imprime les résultats de profil
        # (les statistiques qui décrivent combien de fois et pendant combien de temps
        # les diverses parties du programme sont exécutées.)
        # runctx fournit les cartographies globales et locales pour app.start().
        # Le résultat semble être enregistré dans la fichier taskcoach.profile !
        cProfile.runctx(
            "app.start()", globals(), locals(), filename=".profile"
        )
    else:
        log.info("Lancement de l'application avec Application.start()")
        # Point de lancement pour la boucle principale de Tkinter.
        app.start()


if __name__ == "__main__":
    log.info(
        "Lancement du programme Task Coach via taskcoach.py et les arguments d'ArgumentParser."
    )
    start()
