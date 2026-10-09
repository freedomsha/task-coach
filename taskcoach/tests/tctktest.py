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

**tctktest.py**

Ce fichier Python fournit des classes de base et des utilitaires pour les tests unitaires
utilisés dans le projet `taskcoachlib`.

**Classes principales**

* `TestCase` : Classe de base pour les tests unitaires.
  Elle hérite de `unittest.TestCase` et
  fournit des fonctionnalités supplémentaires utiles
  pour les tests liés à l'interface graphique (GUI)
  utilisant la bibliothèque `tkinter`.
    * Fournit une instance unique de l'application tkinter (`tk.Tk`) accessible via la variable `root`.
    * Implémente la méthode `tearDown` pour effectuer des actions de nettoyage après chaque test,
      notamment la destruction des widgets tkinter.
    * Fournit des méthodes utilitaires pour les tests :
        * `assertEqualLists` : Compare deux listes et vérifie si elles contiennent les mêmes éléments.
        * `registerObserver` : Enregistre l'objet de test en tant qu'observateur d'un type d'événement spécifique.
        * `onEvent` : Méthode appelée lorsque l'objet de test reçoit un événement.
* `TestCaseFrame` : Classe de base pour les tests unitaires nécessitant une fenêtre tkinter simulée.
    * Fournit une fenêtre tkinter simulée accessible via la variable `root`.
    * Implémente des méthodes liées à la fenêtre simulée :
        * `getToolBarPerspective` : Méthode simulée pour récupérer la perspective de la barre d'outils.
        * `AddBalloonTip` : Méthode simulée pour ajouter une infobulle (tooltip).
* `tkTestCase` : Classe de base pour les tests unitaires spécifiques à l'interface tkinter.
    * Hérite de `TestCase` et initialise l'interface graphique tkinter en utilisant `taskcoachlib.config.arguments.set_gui("tk")`.
    * Implémente la méthode `tearDown` pour nettoyer les widgets tkinter après chaque test.

**Fonctions utilitaires**

* `skipOnPlatform` : Décorateur pour les tests unitaires qui doivent être ignorés sur des plateformes spécifiques.
    * Permet de sauter des tests en fonction du système d'exploitation.

**Utilisation**

Les classes et fonctions de ce fichier sont utilisées pour créer des tests unitaires pour le projet `taskcoachlib`.
Les développeurs de tests héritent généralement de `TestCase` ou `tkTestCase` pour bénéficier des fonctionnalités
fournies et implémenter des méthodes de test individuelles pour vérifier le comportement attendu du code.
"""
# Explications des changements :
#
# wx.App → tkinter.Tk : L'application principale est maintenant une instance de tkinter.Tk.
# wx.Frame → tkinter.Toplevel : La fenêtre de test est une instance de tkinter.Toplevel.
# Gestion des événements : Utilisation de pubsub pour la gestion des événements (comme dans le code original), mais vous pouvez aussi utiliser les callbacks Tkinter classiques si nécessaire.
# Nettoyage : Dans tearDown, on détruit les widgets enfants pour éviter les fuites de mémoire.
# Suppression des dépendances wxPython : Les fonctions et décorateurs spécifiques à wxPython ont été supprimés ou adaptés.
#
# Prochaines étapes :
#
# Testez ce code avec vos tests unitaires existants pour vérifier que tout fonctionne comme attendu.
# Adaptez les méthodes spécifiques (comme AddBalloonTip) si nécessaire pour votre cas d'usage.
# Si vous utilisez des fonctionnalités avancées de wxPython (comme les barres d'outils), il faudra les adapter manuellement pour Tkinter.

import os
import sys
import unittest
import logging
import gettext
import platform

from pubsub import pub
import tkinter as tk
from tkinter import ttk

from taskcoachlib.config import arguments
from taskcoachlib.patterns import (
    Publisher,
    NumberedInstances,
)  # Ajout de l'importation du module patterns

gettext.NullTranslations().install()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# TMP: compat to map wx platform strings
_PLATFORM_MAP = {
    "__WXGTK__": "Linux",
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
        if platform.system() in [_PLATFORM_MAP[name] for name in platforms]:
            return lambda self, *args, **kwargs: self.skipTest(
                f"platform is {platform.system()}"
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
    pour les applications nécessitant la configuration du framework tkinter.
    et logique événementielle. Il inclut des méthodes d'assertion personnalisées et
    gère les observateurs d'événements à l'aide des modèles Éditeur-Abonné.

    Attributes:
        root (tk.Tk): An instance of `tk.Tk`, which is required for initializing
            tkinter objects that depend on an application context.
    """

    # Some non-UI stuff also needs the app to be constructed (like
    # tk.BLACK et al)
    # root = tk.Tk()
    app = tk.Tk()
    app.withdraw()  # Cache la fenêtre principale pour éviter qu'elle n'apparaisse pendant les tests

    def tearDown(self):
        # Détruit les widgets enfants pour éviter les fuites de mémoire
        # self.root.destroy()
        for widget in self.app.winfo_children():
            widget.destroy()
        # Publisher.clear()  # Utilisation de la classe Publisher depuis l'importation
        Publisher.clear(
            self
        )  # Utilisation de la classe Publisher depuis l'importation
        NumberedInstances.count = (
            dict()
        )  # Utilisation de la classe NumberedInstances depuis l'importation
        if hasattr(self, "events"):
            del self.events
        pub.unsubAll()
        super().tearDown()

    # Pourrais être remplacé par assertListEqual :
    def assertEqualLists(self, expectedList, actualList):
        self.assertEqual(len(expectedList), len(actualList))
        for item in expectedList:
            self.assertTrue(item in actualList)

    def registerObserver(self, eventType, eventSource=None):
        if not hasattr(self, "events"):
            self.events = []  # pylint: disable=W0201
        # Publisher.registerObserver(
        #     self.onEvent, eventType=eventType, eventSource=eventSource
        # )
        pub.subscribe(self.onEvent, eventType)

    def onEvent(self, event):
        self.events.append(event)


# class TestCaseFrame(tk.Tk):
class TestCaseFrame(tk.Toplevel):
    """
    Représente un cadre personnalisé pour un scénario de test.

    Cette classe étend la classe tk.Tk pour fournir un cadre spécialisé
    à des fins de scénario de test. Il comprend des fonctionnalités
    permettant de gérer les perspectives de la barre d'outils
    et d'ajouter des info-bulles. Le cadre peut être personnalisé davantage
    et étendu selon les besoins.

    Cette classe étend la classe `tk.Toplevel`
    pour fournir une fenêtre spécialisée à des fins de test.

    Attributes:
        toolbarPerspective (str) : Stores the perspective of the toolbar.
    """

    def __init__(self):
        super().__init__()
        self.toolbarPerspective = ""

    def getToolBarPerspective(self):
        return self.toolbarPerspective

    def AddBalloonTip(self, *args, **kwargs):
        pass


class tkTestCase(TestCase):
    """
    Représente un scénario de test pour tkinter, héritant de TestCase. Cette classe est spécialisée dans
    la création d'un cadre de test pour les applications GUI construites avec tkinter, garantissant une configuration et un démontage corrects
    des composants de l'interface graphique.

    Le but de cette classe est de fournir un environnement contrôlé pour les tests GUI, où
    les objets GDI et autres ressources graphiques sont correctement gérés. pendant le cycle de vie du test.
    Ceci est particulièrement important pour éviter les fuites de ressources sur les systèmes Windows, où les objets GDI
    ont une limite d'allocation stricte.

    Attributes:
        frame (TestCaseFrame): A frame used for testing GUI components.
    """

    # pylint: disable=W0404
    frame = TestCaseFrame()
    arguments.set_gui("tk")

    def tearDown(self):
        super().tearDown()
        # Détruit les widgets enfants de la fenêtre de test
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.frame.destroy()


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


if __name__ == "__main__":
    main()
