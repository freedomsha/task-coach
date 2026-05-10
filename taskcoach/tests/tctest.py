#!/usr/bin/env python

"""
Task Coach - Your friendly task manager
Copyright (C) 2021 Task Coach developers <developers@taskcoach.org>

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

**tctest.py**

Ce fichier Python fournit des classes de base et des utilitaires pour les tests unitaires
utilisés dans le projet `taskcoachlib`.

**Classes principales**

* `TestCase` : Classe de base pour les tests unitaires.
  Elle hérite de `unittest.TestCase` et
  fournit des fonctionnalités supplémentaires utiles
  pour les tests liés à l'interface graphique (GUI)
  utilisant la bibliothèque `wx`.
    * Fournit une instance unique de l'application wx (`wx.App`) accessible via la variable `app`.
    * Implémente la méthode `tearDown` pour effectuer des actions de nettoyage après chaque test,
      notamment la déconnexion des événements wx, la suppression des enregistrements d'observateurs
      de publication-abonnement (`pubsub`), et la réinitialisation des compteurs d'instances numérotées.
    * Fournit des méthodes utilitaires pour les tests :
        * `assertEqualLists` : Compare deux listes et vérifie si elles contiennent les mêmes éléments.
        * `registerObserver` : Enregistre l'objet de test en tant qu'observateur d'un type d'événement spécifique.
        * `onEvent` : Méthode appelée lorsque l'objet de test reçoit un événement.
* `TestCaseFrame` : Classe de base pour les tests unitaires nécessitant une fenêtre wxFrame simulée.
    * Fournit une fenêtre wxFrame simulée accessible via la variable `frame`.
    * Implémente des méthodes liées à la fenêtre simulée :
        * `getToolBarPerspective` : Méthode simulée pour récupérer la perspective de la barre d'outils.
        * `AddBalloonTip` : Méthode simulée pour ajouter une infobulle (tooltip).
* `wxTestCase` : Classe de base pour les tests unitaires spécifiques à l'interface wx.
    * Hérite de `TestCase` et initialise l'interface graphique wx à l'aide de `taskcoachlib.gui.init()`.
    * Implémente la méthode `tearDown` pour nettoyer les objets GDI Windows après chaque test.

**Fonctions utilitaires**

* `skipOnPlatform` : Décorateur pour les tests unitaires qui doivent être ignorés sur des plateformes spécifiques.
    * Permet de sauter des tests en fonction du système d'exploitation.

**Utilisation**

Les classes et fonctions de ce fichier sont utilisées pour créer des tests unitaires pour le projet `taskcoachlib`.
Les développeurs de tests héritent généralement de `TestCase` ou `wxTestCase` pour bénéficier des fonctionnalités
fournies et implémentent des méthodes de test individuelles pour vérifier le comportement attendu du code.
"""

print("IMPORT tctest START")
import os

os.environ["DISPLAY"] = ":0"

os.environ["WX_USE_NATIVE_BACKEND"] = "0"

import wx

# ⚠️ CRITIQUE : créer wx.App AVANT tout le reste
if not wx.GetApp():
    app = wx.App(False)
# import os
import sys
import unittest
import logging
import gettext
import platform

from pubsub import pub

# import wx

from taskcoachlib import patterns

gettext.NullTranslations().install()

# Empêcher wx de planter sans DISPLAY
if "DISPLAY" not in os.environ:
    # Si l'environnement est sans GUI (ou PyCHarm mal configuré) :
    os.environ["DISPLAY"] = ":0"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# TMP: compat to map wx platform strings
_PLATFORM_MAP = {
    "__WXGTK__": "Linux",
    # "__WXMAC__": "Darwin",
    # "__WXMSW__": "Windows",
}


def skipOnPlatform(*platforms):
    """
    Décorateur pour ignorer l'exécution d'une méthode de test sur les plates-formes spécifiées.

    Ce décorateur vérifie la plate-forme sur laquelle le test est exécuté et ignore l'exécution
    de la méthode de test si la plate-forme actuelle correspond à l'une des
    plates-formes spécifiées.

    Args:
        *platforms: Un ou plusieurs identifiants de plateforme (sous forme de chaînes) pour lesquels le test
            doit être ignoré. Chaque identifiant doit correspondre à une clé du dictionnaire
            _PLATFORM_MAP.

    Returns:
        Callable: Fonction qui ignore le test ou exécute la méthode de test d'origine
        , en fonction de la plateforme actuelle.
    """

    def wrapper(func):
        # import wx

        if platform.system() in [_PLATFORM_MAP[name] for name in platforms]:
            # return lambda self, *args, **kwargs: self.skipTest("platform is %s" % wx.Platform)
            return lambda self, *args, **kwargs: self.skipTest(
                f"platform is {wx.Platform}"
            )
        return func

    return wrapper


def is_gui_available():
    """
    Vérifie si une interface utilisateur graphique (GUI) est disponible.

    Cette fonction détermine si une interface utilisateur graphique est disponible pour
    une utilisation en vérifiant les variables d'environnement "DISPLAY" et "CI". Il renvoie
    True si « DISPLAY » est défini (indiquant la disponibilité d'un environnement GUI)
    et « CI » n'est pas défini (indiquant que le code ne s'exécute pas dans un environnement d'intégration continue).

    Returns:
        bool: True if a GUI is available, False otherwise.
    """
    return os.environ.get("DISPLAY") is not None and not os.environ.get("CI")


def skipIfNotGui(reason="Requires GUI environment"):
    """
    Décorateur pour ignorer un test si un environnement GUI n'est pas disponible.

    Cette fonction encapsule un scénario de test avec une condition, garantissant que le test est
    exécuté uniquement lorsqu'un environnement d'interface utilisateur graphique (GUI) est accessible.

    Args:
        reason (str): Raison pour laquelle le test est ignoré si un environnement GUI
            n'est pas disponible. La valeur par défaut est « Nécessite un environnement GUI ».

    Returns:
        function: La fonction de scénario de test modifiée qui sera ignorée si l'environnement GUI
        n'est pas disponible.
    """
    return unittest.skipUnless(is_gui_available(), reason)


class TestCase(unittest.TestCase):
    """
    Encapsule la configuration et le démontage des scénarios de test, fournit des méthodes utilitaires pour les assertions
    et gère les enregistrements d'événements à des fins de test.

    Cette classe hérite de `unittest.TestCase` et est conçue pour faciliter les tests unitaires
    pour les applications nécessitant la configuration du framework wxPython.
    et logique événementielle. Il inclut des méthodes d'assertion personnalisées et
    gère les observateurs d'événements à l'aide des modèles Éditeur-Abonné.

    Attributes:
        app (wx.App): An instance of `wx.App`, which is required for initializing
            wxPython objects that depend on an application context.
    """

    # Some non-UI stuff also needs the app to be constructed (like
    # wx.BLACK et al)
    # app = wx.App(0)  # Cette ligne pose un problème pour passer les tests !
    # # PyCharm lance tctest.py
    # # Python importe le fichier
    # # 👉 wx.App(0) est exécuté immédiatement
    # # wx n’est pas prêt (DISPLAY, thread, contexte…)
    # # 💥 crash C++ → traits failed + SIGSEGV
    # # Solution :
    app = None  # initialisation différée

    @classmethod
    def setUpClass(cls):
        """Initialise wx.App une seule fois pour tous les tests."""
        import wx  # Import local

        cls.app = wx.GetApp()  # Récupère l'app existante
        if not cls.app:  # Si aucune app wx n'existe
            cls.app = wx.App(False)  # Création propre sans redirection
        if not wx.App.IsMainLoopRunning():
            cls.app = wx.App(False)  # Assure que l'app est prête

    def tearDown(self):
        """Nettoyage après chaque test."""
        import wx  # Import wx local pour éviter les problèmes d'importation

        # self.app.Disconnect(wx.ID_ANY)
        if self.app:  # Vérifie que l'app existe
            try:
                self.app.Disconnect(wx.ID_ANY)  # Déconnecte événements wx
            except Exception:
                pass  # Ignore erreurs wx

        patterns.Publisher().clear()  # Reset pubsub
        patterns.NumberedInstances.count = dict()  # Reset IDs
        if hasattr(self, "events"):
            del self.events  # Nettoyage attribut
        pub.unsubAll()  # Désinscription pubsub
        super().tearDown()  # Appel parent

    # Pourrais être remplacé par assertListEqual :
    def assertEqualLists(self, expectedList, actualList):
        self.assertEqual(len(expectedList), len(actualList))
        for item in expectedList:
            self.assertTrue(item in actualList)

    # def assertEqualLists(self, expectedList, actualList):
    #     self.assertListEqual(expectedList, actualList)

    def registerObserver(self, eventType, eventSource=None):
        if not hasattr(self, "events"):
            self.events = []  # pylint: disable=W0201
        patterns.Publisher().registerObserver(
            self.onEvent, eventType=eventType, eventSource=eventSource
        )

    def onEvent(self, event):
        self.events.append(event)


class TestCaseFrame(wx.Frame):
    """
    Représente un cadre personnalisé pour un scénario de test.

    Cette classe étend la classe wx.Frame pour fournir un cadre spécialisé à des fins de scénario de test
    . Il comprend des fonctionnalités permettant de gérer les perspectives de la barre d'outils
    et d'ajouter des info-bulles. Le cadre peut être personnalisé davantage
    et étendu selon les besoins.

    Attributes:
        toolbarPerspective (str): Stores the perspective of the toolbar.
    """

    def __init__(self):
        super().__init__(None, wx.ID_ANY, "Frame")
        self.toolbarPerspective = ""

    def getToolBarPerspective(self):
        return self.toolbarPerspective

    def AddBalloonTip(self, *args, **kwargs):
        pass


class wxTestCase(TestCase):
    """
    Représente un scénario de test pour wxPython, héritant de TestCase. Cette classe est spécialisée dans
    la création d'un cadre de test pour les applications GUI construites avec wxPython, garantissant une configuration et un démontage corrects
    des composants de l'interface graphique.

    Le but de cette classe est de fournir un environnement contrôlé pour les tests GUI, où
    les objets GDI et autres ressources graphiques sont correctement gérés. pendant le cycle de vie du test.
    Ceci est particulièrement important pour éviter les fuites de ressources sur les systèmes Windows, où les objets GDI
    ont une limite d'allocation stricte.

    Attributes:
        frame (TestCaseFrame): A frame used for testing GUI components.
    """

    # # pylint: disable=W0404
    # frame = TestCaseFrame()
    # from taskcoachlib import gui
    #
    # gui.init()  # appelé trop tôt
    # # Remplacer par :
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import wx  # Import local

        # 🔒 S'assurer que wx est prêt AVANT gui
        app = wx.GetApp()
        if not app:
            app = wx.App(False)

        # ⚠️ Import différé CRUCIAL pour éviter les problèmes d'importation et de contexte wx
        from taskcoachlib import gui

        print("AVANT GUI INIT")
        # ⚠️ Initialisation GUI seulement après wx.App
        gui.init()

        cls.frame = TestCaseFrame()

    def tearDown(self):
        super().tearDown()
        self.frame.DestroyChildren()  # Clean up GDI objects on Windows


def main():
    """
    Exécute les tests unitaires définis dans le programme.

    Cette fonction exploite le framework unittest pour découvrir et exécuter tous les tests
    définis dans le module actuel ou les modules importés. Il sert de point d'entrée
    pour l'exécution des tests, garantissant que les résultats de la suite de tests sont
    formatés et affichés de manière cohérente. L'exécution de cette fonction
    est essentielle pour valider l'exactitude du code et gérer les problèmes potentiels
    identifiés par les tests unitaires.
    """
    unittest.main()
