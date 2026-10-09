# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
# Structure et héritage :
# SettingsCommand hérite de base_uicommandtk.UICommand 1.
# BooleanSettingsCommand hérite de SettingsCommand 2.
# UICheckCommand hérite de BooleanSettingsCommand 3.
# UIRadioCommand hérite de BooleanSettingsCommand 4.
#
# Fonctionnalités principales :
# La classe SettingsCommand sert de base pour les commandes liées aux paramètres de l'application. Elle initialise les attributs settings, section et setting pour indiquer où le paramètre est stocké 1.
# La classe BooleanSettingsCommand sert de base pour les commandes qui modifient un paramètre booléen et met à jour l'interface utilisateur en conséquence 2. Elle contient une méthode onUpdateUI, qui est une relique de wxPython et nécessite une adaptation pour Tkinter (utilisation de StringVar, BooleanVar, etc.) 2 5.
# La classe UICheckCommand représente une commande de type case à cocher. Elle utilise tk.BooleanVar pour gérer l'état de la case à cocher et met à jour les paramètres de l'application en conséquence 6 4.
# La classe UIRadioCommand représente une commande de type bouton radio. Elle utilise tk.StringVar pour gérer l'état du bouton radio et met à jour les paramètres de l'application en conséquence 4 7.
#
# Points d'attention et éléments à compléter (TODO) :
# La méthode onUpdateUI de BooleanSettingsCommand nécessite une adaptation pour Tkinter. Il faut utiliser les variables de contrôle Tkinter (StringVar, BooleanVar, etc.) pour mettre à jour l'interface utilisateur 2 5.
# Dans UICheckCommand et UIRadioCommand, les lignes commentées # self.settings.bind(...) suggèrent qu'il y avait une tentative de lier les modifications des paramètres à la mise à jour de la variable Tkinter. Cela doit être implémenté pour que l'interface utilisateur soit automatiquement mise à jour lorsque les paramètres sont modifiés par d'autres moyens 6 7.
# La méthode getBitmap de UICheckCommand retourne une chaîne vide car Tkinter gère l'affichage de l'état "coché" par défaut 4.
# La gestion des menuId dans addToMenu est simplifiée car Tkinter n'utilise pas d'ID d'entier comme wxPython 3.
#
# Améliorations potentielles :
# Il serait utile d'ajouter des commentaires expliquant comment les variables de contrôle Tkinter (StringVar, BooleanVar) sont utilisées pour lier l'état des éléments de l'interface utilisateur aux paramètres de l'application.
# La gestion des erreurs pourrait être améliorée en ajoutant des blocs try...except pour intercepter les exceptions potentielles lors de la manipulation des paramètres.

# Autres points à considérer :
# Gestion des icônes : Le commentaire TODO mentionne la gestion des icônes via tkartprovider.py 7.  Il faut s'assurer que ce module est correctement implémenté et que les icônes sont chargées et affichées correctement dans l'interface utilisateur.
# Mise à jour des labels de menu : Tkinter ne gère pas automatiquement la mise à jour des labels de menu 8, 9.  Si cette fonctionnalité est importante, il faudra implémenter une solution manuelle pour mettre à jour les labels lorsque cela est nécessaire.

# Il faut donc trouver une autre façon de lier les modifications des paramètres à la mise à jour de l'interface utilisateur. Voici plusieurs approches possibles, en tenant compte du code que vous avez fourni :
# 1. Utilisation des variables de contrôle Tkinter et d'une fonction de rappel :
# Dans les classes UICheckCommand et UIRadioCommand, vous utilisez déjà tk.BooleanVar et tk.StringVar pour gérer l'état des éléments de l'interface utilisateur 2 1.
#
#
# L'idée est de définir une fonction de rappel (callback) qui sera appelée chaque fois que le paramètre correspondant est modifié. Cette fonction mettra à jour la variable de contrôle Tkinter, ce qui entraînera la mise à jour de l'interface utilisateur.
# Dans cet exemple, self._variable.trace("w", self._on_variable_changed) ajoute un "trace" à la variable Tkinter.  Cela signifie que la fonction _on_variable_changed sera appelée chaque fois que la variable est modifiée (en écriture, "w").  Dans _on_variable_changed, vous mettez à jour le paramètre correspondant dans self.settings.
#
# 2. Utilisation d'un système d'événements personnalisé :
# Vous pouvez créer un système d'événements personnalisé dans votre application.  L'objet Settings émettrait un événement chaque fois qu'un paramètre est modifié. Les classes UICheckCommand et UIRadioCommand s'abonneraient à ces événements et mettraient à jour leurs variables de contrôle Tkinter en conséquence.
#
# 3. Modification directe des paramètres dans doCommand :
# Dans la méthode doCommand de UICheckCommand et UIRadioCommand, vous pouvez directement modifier la valeur du paramètre dans self.settings et ensuite mettre à jour la variable Tkinter.  Cependant, cette approche ne garantit pas que l'interface utilisateur sera mise à jour si le paramètre est modifié par d'autres parties du code.
#
# Choix de la meilleure approche :
# L'approche avec la fonction de rappel (trace) est la plus simple à mettre en œuvre et devrait fonctionner dans la plupart des cas.  Elle assure une synchronisation bidirectionnelle entre l'interface utilisateur et les paramètres.
# Le système d'événements personnalisé est plus complexe, mais il offre plus de flexibilité et de contrôle sur la façon dont les modifications des paramètres sont propagées dans l'application.
#
# Avant de choisir une approche, il est important de comprendre comment les paramètres sont utilisés et modifiés dans le reste de l'application.  Si les paramètres sont uniquement modifiés via l'interface utilisateur, l'approche avec la fonction de rappel peut être suffisante.  Si les paramètres sont modifiés par d'autres parties du code, un système d'événements personnalisé peut être nécessaire pour garantir que l'interface utilisateur est toujours à jour.
# En résumé, l'erreur AttributeError est due à l'absence de la méthode bind dans l'objet Settings sous Tkinter. Il faut donc utiliser une autre approche pour lier les modifications des paramètres à l'interface utilisateur, comme les fonctions de rappel ou un système d'événements personnalisé. La première approche (fonction de rappel) est la plus simple.

# 20/01/2026:
# Voici une analyse et des suggestions d'améliorations, basées sur les extraits de code fournis et les objectifs que tu as mentionnés :
# 1. Analyse Générale
#
# Structure et Héritage : La structure d'héritage semble correcte et suit le modèle de settings_uicommand.py 1 2. Les classes héritent de base_uicommandtk.UICommand et se spécialisent progressivement pour gérer les paramètres de l'application, les paramètres booléens, les cases à cocher et les boutons radio.
# Fonctionnalités Principales : Les classes de base (SettingsCommand, BooleanSettingsCommand) initialisent correctement les attributs nécessaires pour stocker et manipuler les paramètres 3 2 4 5. Les classes dérivées (UICheckCommand, UIRadioCommand) utilisent des variables de contrôle Tkinter (BooleanVar, StringVar) pour lier l'état des éléments de l'interface utilisateur aux paramètres de l'application 6 7 8 9.
# Adaptation à Tkinter : L'adaptation de onUpdateUI pour Tkinter est essentielle, et l'utilisation de trace sur les variables Tkinter semble être une approche appropriée pour réagir aux changements de paramètres 10 11 8 12.
# Gestion des Erreurs : L'ajout de blocs try...except pour intercepter les exceptions lors de la manipulation des paramètres est une excellente pratique 13 14 15.
#
# 2. Points d'Amélioration et Compléments
#
# Gestion Bidirectionnelle des Paramètres : Le point crucial est de s'assurer que les modifications des paramètres (par l'utilisateur via l'interface ou par le code) sont correctement reflétées dans l'interface, et vice versa 7. L'utilisation de trace est une bonne base, mais il faut s'assurer que cela couvre tous les cas de figure.
#
# Fonctions de Rappel : Les fonctions de rappel (_on_variable_changed) sont bien utilisées pour mettre à jour les paramètres lorsque les variables Tkinter changent 7 16 9.
# Initialisation Correcte : Assure-toi que l'état initial des variables Tkinter (BooleanVar, StringVar) est toujours synchronisé avec la valeur actuelle des paramètres lors de la création des commandes 8.
#
#
# Méthode onUpdateUI : Bien que la méthode onUpdateUI soit présente pour la compatibilité, elle n'est pas directement utilisée dans l'implémentation Tkinter actuelle 10 11. Tu peux la supprimer si tu es sûr qu'elle n'est plus nécessaire.
# Gestion des Menus : La méthode addToMenu est simplifiée pour Tkinter, ce qui est approprié 17 18. Cependant, il faut s'assurer que l'ajout des commandes aux menus (checkbutton, radiobutton, etc.) fonctionne correctement avec Tkinter.
# Complétude des Classes :
#
# SettingsCommand : Vérifie si d'autres types de paramètres (entiers, chaînes de caractères) nécessitent des classes dérivées de SettingsCommand.
#
#
# Documentation et Commentaires : Ajoute des commentaires pour expliquer le fonctionnement des différentes parties du code, en particulier la liaison entre les variables Tkinter et les paramètres de l'application.
#
# 4. Prochaines Étapes
#
# Tests Unitaires : Écris des tests unitaires pour vérifier que les paramètres sont correctement liés à l'interface utilisateur et que les modifications sont bien persistées.
# Intégration : Utilise ces classes dans uicommandtk.py et menutk.py et teste l'ensemble du système pour t'assurer que tout fonctionne comme prévu.

from builtins import str
import logging
import tkinter as tk
from tkinter import messagebox
from taskcoachlib.guitk.uicommand import base_uicommandtk

log = logging.getLogger(__name__)


class SettingsCommand(base_uicommandtk.UICommand):  # pylint: disable=W0223
    """
    SettingsCommands are saved in the settings (a ConfigParser).

    C'est une classe de base pour les commandes qui sont liées aux paramètres
    de l'application (stockés dans une sorte de fichier de configuration).

    Elle initialise les attributs settings, section, et setting
    pour savoir où le paramètre est stocké.
    """

    def __init__(self, settings=None, setting=None, section="view",
                 *args, **kwargs):
        self.settings = settings
        self.section = section
        self.setting = setting
        super().__init__(*args, **kwargs)


class BooleanSettingsCommand(SettingsCommand):  # pylint: disable=W0223
    """ Classe de Base pour les commandes qui modifient un paramètre booléen.

    Elle hérite de SettingsCommand et est la base pour les commandes
    qui modifient des paramètres booléens (ou qui peuvent être représentés
    par un état "coché" ou non).

    Chaque fois que le paramètre est modifié,
    la représentation de l'interface utilisateur est également modifiée.
    Par exemple, un menu est coché.
    """

    def __init__(self, value=None, *args, **kwargs):
        self.value = value
        super().__init__(*args, **kwargs)

    # Note: OnUpdateUI est une fonctionnalité spécifique à wxPython qui n'a pas
    # d'équivalent direct dans l'architecture Tkinter.
    # Pour Tkinter, la mise à jour de l'UI se fait généralement directement
    # via la modification de variables de contrôle Tkinter (StringVar, BooleanVar, etc.)
    # J'ai laissé la méthode onUpdateUI pour la compatibilité, mais son
    # implémentation doit être adaptée à la logique Tkinter.
    # Dans une application Tkinter, l'état d'un MenuItem peut être géré via
    # une variable associée.
    def onUpdateUI(self, event=None):
        # La logique de mise à jour de l'UI est généralement gérée
        # par l'objet de commande lui-même, pas par un événement global.
        # Cette méthode est laissée en tant que marqueur pour indiquer
        # où la logique wxPython a été.
        # Elle pourrait être utilisée (ou une fonction similaire)
        # pour mettre à jour la variable de contrôle Tkinter
        # lorsque le paramètre correspondant change.
        pass

    def addToMenu(self, menu, window, position=None):
        """ Ajouter un sous_menu au menu (Toolbar).

        Args :
            menu (tk.Menu) : Menu à ajouter
            window (tk.Tk ou tk.Toplevel) : Fenêtre
            position (int, optionnel) : Position.

        Returns :
            menuId (int) : ID du Menu ajouté.
        """
        # La logique addToMenu est simplifiée pour Tkinter.
        # Tkinter n'utilise pas d'ID d'entier comme wxPython,
        # mais on peut retourner l'index de l'élément ajouté.
        # Le concept de "menuId" est donc abstrait ici.
        super().addToMenu(menu, window, position)
        return len(menu.winfo_children()) - 1

    def isSettingChecked(self):
        raise NotImplementedError  # pragma: no cover


class UICheckCommand(BooleanSettingsCommand):
    """
    Elle hérite de BooleanSettingsCommand et
    représente une commande qui se comporte comme une case à cocher dans un menu.

    Elle utilise le style "checkbutton" pour l'élément de menu Tkinter.

    Elle a des méthodes pour obtenir l'état du paramètre (isSettingChecked) et
    pour le modifier (doCommand).

    """
    # self.settings.bind(...) : Il manque une liaison (bind) entre
    # les modifications du paramètre (self.settings) et
    # la variable de contrôle Tkinter (self._variable) 1, 2.
    # Cette liaison est cruciale pour que l'interface utilisateur reflète toujours
    # l'état actuel des paramètres, même si ceux-ci sont modifiés par d'autres parties du code.
    # Il faut donc explorer comment implémenter cette liaison avec Tkinter.
    def __init__(self, *args, **kwargs):
        # super().__init__(kind="checkbutton", *args, **kwargs)
        # TypeError: taskcoachlib.guitk.uicommand.settings_uicommandtk.BooleanSettingsCommand.__init__() got multiple values for keyword argument 'kind'
        super().__init__(*args, **kwargs)
        # tk.BooleanVar stocke l'état de la case à cocher (True/False)
        self._variable = tk.BooleanVar(value=self.isSettingChecked())
        self._variable.trace_add("write", self._on_variable_changed)  # Ajout d'une trace
        # La valeur initiale est définie en fonction de la valeur actuelle du paramètre.
        # L'état de la variable est mis à jour lorsque le paramètre est changé.
        # TODO :
        # self.settings.bind(self.section, self.setting, lambda: self._variable.set(self.isSettingChecked()))
        # self.settings.bind(...) permettrait de lier directement la variable Tkinter
        # aux modifications du paramètre, assurant une synchronisation automatique.
        # Cependant, comme mentionné précédemment, l'objet Settings
        # n'a pas de méthode bind dans Tkinter.
        # Il faut donc trouver une autre façon de lier les modifications
        # des paramètres à la mise à jour de l'interface utilisateur.
        # Voici une approche possible :

        # Dans cet exemple, self._variable.trace("w", self._on_variable_changed)
        # ajoute un "trace" à la variable Tkinter.
        # Cela signifie que la fonction _on_variable_changed sera appelée
        # chaque fois que la variable est modifiée (en écriture, "w").
        # Dans _on_variable_changed, vous mettez à jour le paramètre
        # correspondant dans self.settings.

    def isSettingChecked(self):
        return self.settings.getboolean(self.section, self.setting)

    def _isMenuItemChecked(self, event=None):
        # Avec Tkinter, on utilise la variable de contrôle pour l'état.
        return self._variable.get()

    def _on_variable_changed(self, *args):
        # Cette fonction est appelée lorsque la variable Tkinter change
        new_value = self._variable.get()
        # self.settings.setboolean(self.section, self.setting, new_value)
        try:
            # Met à jour le paramètre de l'application
            self.settings.setboolean(self.section, self.setting, new_value)
        except Exception as e:
            log.error(f"Erreur lors de la modification du paramètre : {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la modification du paramètre : {e}")

    # Il est important d'ajouter des blocs try...except autour des opérations
    # qui pourraient potentiellement échouer, comme la lecture ou l'écriture des paramètres.
    def doCommand(self, event=None):
        # Inversion de l'état de la variable Tkinter
        new_state = not self._variable.get()
        # self._variable.set(new_state)
        # # Met à jour le paramètre de l'application
        # self.settings.setboolean(self.section, self.setting, new_state)
        try:
            # Met à jour la variable de contrôle et le paramètre
            self._variable.set(new_state)
            # Met à jour le paramètre de l'application
            self.settings.setboolean(self.section, self.setting, new_state)
        except Exception as e:
            log.error(f"Erreur lors de la modification du paramètre : {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la modification du paramètre : {e}")

    def getBitmap(self):
        # Tkinter gère l'affichage de l'état "coché" par défaut.
        return ""


class UIRadioCommand(BooleanSettingsCommand):
    """
    Elle hérite également de BooleanSettingsCommand mais
    représente une commande qui fait partie d'un groupe de boutons radio.

    Elle utilise le style "radiobutton" pour l'élément de menu Tkinter.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(kind="radiobutton", bitmap="",
                         *args, **kwargs)
        # On suppose qu'une seule variable de contrôle est partagée
        # par toutes les commandes radio du même groupe.
        self._variable = tk.StringVar(value=str(self.isSettingChecked()))
        # TODO :
        # self.settings.bind(self.section, self.setting, lambda: self._variable.set(str(self.isSettingChecked())))
        self._variable.trace("w", self._on_variable_changed)  # Ajout d'une trace

    def isSettingChecked(self):
        return self.settings.get(self.section, self.setting) == str(self.value)

    def _on_variable_changed(self, *args):
        # Cette fonction est appelée lorsque la variable Tkinter change
        new_value = self._variable.get()
        # self.settings.setvalue(self.section, self.setting, new_value)
        try:
            self.settings.set(self.section, self.setting, new_value)
        except Exception as e:
            log.error(f"Erreur lors de la modification du paramètre : {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la modification du paramètre : {e}")

    def doCommand(self, event=None):
        # Met à jour la variable de contrôle et le paramètre
        # self._variable.set(str(self.value))
        # self.settings.setvalue(self.section, self.setting, self.value)
        try:
            # Met à jour la variable de contrôle et le paramètre
            self._variable.set(str(self.value))
            self.settings.setvalue(self.section, self.setting, self.value)
        except Exception as e:
            log.error(f"Erreur lors de la modification du paramètre : {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la modification du paramètre : {e}")
