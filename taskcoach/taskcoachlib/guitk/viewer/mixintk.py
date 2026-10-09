# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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

Vous devez spécifier les classes de mixin avant les autres classes.

Ce code est une bibliothèque Python qui permet d'organiser
et de visualiser des données. Voici un ressumé rapide des fonctions principales :

1. **Sorter les éléments** : La bibliothèque utilise plusieurs classes
 pour organiser les éléments, tels que task.Task, attachment.Attachment, etc.,
 en fonction de leurs propriétés.

2. **Gestion des pièces jointes** : Les classes AttachmentDropTargetMixin
 permettent aux utilisateurs de glisser-déposer des fichiers et des URL
 dans un widget pour ajouter des pièces jointes à l'élément sélectionné.

3. **Clônes et copie** : La bibliothèque fournit des fonctions pour cloner
 les objets d'un domaine (task.Task et attachment.Attachment) en les passant
 par référence. Elle peut aussi créer de nouveaux objets d'un domaine
 à partir d'informations fournies.

4. **Interaction avec le domaine** : Les classes note.NoteColumnMixin et
 attachment.AttachmentColumnMixin permettent aux utilisateurs de visualiser
 les icônes associées aux notes et aux pièces jointes dans les Treeview de Tkinter.

5. **Configuration du modèle de données** : La bibliothèque utilise une
 configuration modulaire pour définir comment les données sont organisées
 dans le domaine, y compris la relation entre les objets (task.Task est lié
 à note.Note, et vice versa).

6. **Gestion des paramètres par défauts** : Les classes fournissent des
 méthodes pour lire les valeurs par défauts du modèle de données
 (self.settings.get("view", "defaultplannedstartdatetime")) et les utiliser
 dans la création d'objets.

7. **Suppression des objets d'un domaine** : La bibliothèque fournit une
 méthode pour supprimer tous les objets d'un domaine (task.Task.clear()).

8. **Récupération des données par valeur par défaut** : La bibliothèque
 fournit une méthode pour récupérer la valeur par défaut de l'objet actuel
 dans le domaine (self.settings.get("view", "defaultplannedstartdatetime")).

9. **Sauvegarde et chargement des configurations du modèle de données** :
 La bibliothèque permet de sauvegarder et charger les configurations du modèle
 de données pour l'utilisateur.

10. **Gestion des événements de glisser-déposer** : Les classes
 AttachmentDropTargetMixin utilisent des bindings Tkinter pour gérer les
 événements de glisser-déposer pour ajouter des pièces jointes.

Cette bibliothèque est conceptionnelle et peut être adaptée à d'autres
 applications ou domaines en fonction des spécificités du projet.
Chaque mixin est conçu pour fonctionner avec un Treeview spécifique,
 gérer l'affichage des données et les interactions utilisateur.
 Le code fournit des exemples de comment ces mixins peuvent être utilisés
dans un application Python.
"""
# J'ai remplacé wx par tkinter et tkinter.ttk.
# Les mixins NoteColumnMixin et AttachmentColumnMixin ont été simplifiés
# car la gestion des images dans les widgets Treeview de Tkinter est différente de wx.TreeCtrl.
# TODO : Il faudra adapter la logique d'affichage des icônes dans les classes de viewer concrètes qui utilisent ces mixins.
#
# Je n'ai pas pu convertir la partie widgetCreationKeywordArguments de AttachmentDropTargetMixin
# car le glisser-déposer en Tkinter nécessite une implémentation spécifique via des bindings.
# Les méthodes onDropURL, onDropFiles, et onDropMail sont conservées,
# mais elles devront être liées aux événements de glisser-déposer de Tkinter dans le code du viewer.


import logging
import tkinter as tk
from tkinter import ttk
from pubsub import pub

from taskcoachlib import command
from taskcoachlib.domain import base, task, category, attachment
from taskcoachlib.guitk.uicommand import uicommandtk as uicommand
from taskcoachlib.i18n import _

log = logging.getLogger(__name__)


class SearchableViewerMixin(object):
    """ Classe Mixin pour obtenir une visionneuse consultable.

    Fournit des méthodes pour gérer les options de recherche, le filtre et
    les commandes de la barre d'outils pour la recherche.

    Methods :
        isSearchable() : bool définissant si la visionneuse est consultable.
        createFilter() : Créer un filtre de recherche.
        searchOptions() : Créer un dictionnaire d'options de recherche.
        setSearchFilter() : Configure le filtre de recherche et l'applique à la visionneuse.
        getSearchFilter() : Récupère et retourne le filtre de recherche.
        createToolBarUICommands() : Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.
    """

    def isSearchable(self):
        """ Retourne True si la visionneuse est consultable. """
        return True

    def createFilter(self, presentation):
        """
        Crée et retourne un filtre de recherche.

        Args:
            presentation: La présentation de la visionneuse.

        Returns:
            Un filtre de recherche.
        """
        representation = super().createFilter(presentation)
        return base.SearchFilter(representation, **self.searchOptions())

    def searchOptions(self):
        """
        Crée et retourne un dictionnaire d'options de recherche.

        Returns :
            dict : Un dictionnaire d'options de recherche.
        """
        (
            searchString,
            matchCase,
            includeSubItems,
            searchDescription,
            regularExpression,
        ) = self.getSearchFilter()
        return dict(
            searchString=searchString,
            matchCase=matchCase,
            includeSubItems=includeSubItems,
            searchDescription=searchDescription,
            regularExpression=regularExpression,
            treeMode=self.isTreeViewer(),
        )

    def setSearchFilter(
        self,
        searchString,
        matchCase=False,
        includeSubItems=False,
        searchDescription=False,
        regularExpression=False,
    ):
        """
        Configure le filtre de recherche et l'applique à la visionneuse.

        Args:
            searchString: La chaîne de caractères à rechercher.
            matchCase: Si True, la recherche est sensible à la casse.
            includeSubItems: Si True, la recherche inclut les sous-éléments.
            searchDescription: Si True, la recherche inclut la description.
            regularExpression: Si True, la recherche utilise une expression régulière.
        """
        section = self.settingsSection()
        self.settings.set(section, "searchfilterstring", searchString)
        self.settings.set(section, "searchfiltermatchcase", str(matchCase))
        self.settings.set(section, "searchfilterincludesubitems", str(includeSubItems))
        self.settings.set(section, "searchdescription", str(searchDescription))
        self.settings.set(section, "regularexpression", str(regularExpression))
        self.presentation().setSearchFilter(
            searchString,
            matchCase=matchCase,
            includeSubItems=includeSubItems,
            searchDescription=searchDescription,
            regularExpression=regularExpression,
        )

    def getSearchFilter(self):
        """
        Récupère et retourne le filtre de recherche.

        Returns :
            tuple : Un tuple contenant les paramètres du filtre de recherche.
        """
        section = self.settingsSection()
        searchString = self.settings.get(section, "searchfilterstring")
        matchCase = self.settings.getboolean(section, "searchfiltermatchcase")
        includeSubItems = self.settings.getboolean(section, "searchfilterincludesubitems")
        searchDescription = self.settings.getboolean(section, "searchdescription")
        regularExpression = self.settings.getboolean(section, "regularexpression")
        return (
            searchString,
            matchCase,
            includeSubItems,
            searchDescription,
            regularExpression)

    def createToolBarUICommands(self):
        """ UI commands to put on the toolbar of this viewer.

        Returns :
            tuple : Un tuple contenant les commandes de la barre d'outils.
        """
        searchUICommand = uicommand.Search(viewer=self, settings=self.settings)
        return super().createToolBarUICommands() + (1, searchUICommand)


class FilterableViewerMixin(object):
    """
    A viewer that is filterable. This is a mixin class.
    Ajoute à la visionneuse l'interface utilisateur des commandes de filtrage.

    Methods :
        isFilterable() : bool
        getFilterUICommands() : Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.
        createFilterUICommands() : Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse. Crée les commandes (Remettre à zéro le filtre, Choix des catégories à filtrer).
    """
    def __init__(self, *args, **kwargs):
        log.debug("FilterableViewerMixin.__init__ : Initialisation d'une visionneuse filtrable.")
        self.__filterUICommands = None
        super().__init__(*args, **kwargs)
        log.debug("FilterableViewerMixin initialisé !")

    def isFilterable(self):
        """ Retourne True si la visionneuse est filtrable. """
        return True

    def getFilterUICommands(self):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Returns :
            tuple : Un tuple contenant les commandes de filtrage.
        """
        if not self.__filterUICommands:
            self.__filterUICommands = self.createFilterUICommands()
        return self.__filterUICommands[:2] + self.createCategoryFilterCommands() + self.__filterUICommands[2:]

    def createFilterUICommands(self):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils
        de la visionneuse.

        Crée les commandes Remise à zéro du filtre et Choix des catégories à filtrer.
        """
        return [uicommand.ResetFilter(viewer=self),
                uicommand.CategoryViewerFilterChoice(settings=self.settings),
                None]

    def createToolBarUICommands(self):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Crée la commande Remise à zéro du filtre dans la barre d'outils de la visionneuse.
        """
        clearUICommand = uicommand.ResetFilter(viewer=self)
        return super().createToolBarUICommands() + (clearUICommand,)

    def resetFilter(self):
        """
        Remise à zéro du filtre des catégories.
        """
        self.taskFile.categories().resetAllFilteredCategories()

    def hasFilter(self):
        """
        Retourne True si le filtre des catégories est actif, False sinon.
        """
        return bool(self.taskFile.categories().filteredCategories())

    def createCategoryFilterCommands(self):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Crée les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).
        """
        categories = self.taskFile.categories()
        commands = [_("&Categories"),
                    uicommand.ResetCategoryFilter(categories=categories)]
        if categories:
            commands.append(None)
            commands.extend(self.createToggleCategoryFilterCommands(categories.rootItems()))
        return [tuple(commands)]

    def createToggleCategoryFilterCommands(self, categories):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Crée les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).
        """
        categories = list(categories)
        categories.sort(key=lambda category: category.subject())
        commands = [uicommand.ToggleCategoryFilter(
            category=eachCategory) for eachCategory in categories]
        categoriesWithChildren = [eachCategory for eachCategory
                                  in categories if eachCategory.children()]
        if categoriesWithChildren:
            commands.append(None)
            for eachCategory in categoriesWithChildren:
                subCommands = [_("%s (subcategories)") % eachCategory.subject()]
                subCommands.extend(self.createToggleCategoryFilterCommands(eachCategory.children()))
                commands.append(tuple(subCommands))
        return commands


class FilterableViewerForCategorizablesMixin(FilterableViewerMixin):
    """
    A viewer that is filterable by categories. This is a mixin class.
    Un visualiseur filtrable par catégories. C'est une classe mixin.

    Methods:
        createFilter(self, items) : Crée et retourne les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).
    """
    def createFilter(self, items):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Crée les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).

        Returns :
            tuple : Un tuple contenant les commandes de filtrage.
        """
        items = super().createFilter(items)
        filterOnlyWhenAllCategoriesMatch = self.settings.getboolean("view", "categoryfiltermatchall")
        return category.filter.CategoryFilter(items,
                                              categories=self.taskFile.categories(),
                                              treeMode=self.isTreeViewer(),
                                              filterOnlyWhenAllCategoriesMatch=filterOnlyWhenAllCategoriesMatch)


class FilterableViewerForTasksMixin(FilterableViewerForCategorizablesMixin):
    """
    A viewer that is filterable by categories. This is a mixin class.
    Un visualiseur filtrable par catégories. C'est une classe mixin.

    Methods:
        createFilter(self, taskList) : Crée et retourne les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).
    """
    # def createFilter(self, taskList):
    def createFilter(self, items):
        """
        Retourne la liste des UI commands à mettre dans la barre d'outils de la visionneuse.

        Crée les commandes (Remise à zéro du filtre, Choix des catégories à filtrer).

        Returns :
            tuple : Un tuple contenant les commandes de filtrage de visualisation.
        """
        # taskList = super().createFilter(taskList)
        taskList = super().createFilter(items)
        # return task.filter.ViewFilter(taskList, treeMode=self.isTreeViewer(),
        #                               **self.viewFilterOptions())
        return task.filter.ViewFilter(taskList, treeMode=self.isTreeViewer(),
                                      **self.viewFilterOptions())

    def viewFilterOptions(self):
        """
        Retourne un dictionnaire contenant les options du filtre de visualisation.

        Returns :
            dict : Un dictionnaire contenant les options du filtre de visualisation.
        """
        return dict(hideCompositeTasks=self.isHidingCompositeTasks(),
                    statusesToHide=self.hiddenTaskStatuses())

    def hideTaskStatus(self, status, hide=True):
        """
        Cacher le status de tâche.

        Args:
            status: Le statut de la tâche à cacher.
            hide: Un booléen indiquant si le statut doit être caché.

        Returns:
            None
        """
        self.__setBooleanSetting(f"hide{status}tasks", hide)
        self.presentation().hideTaskStatus(status, hide)

    def showOnlyTaskStatus(self, status):
        """
        Montrer seulement ce status de tâche.

        Args:
            status: Le statut de la tâche à montrer.

        Returns:
            None
        """
        for taskStatus in task.Task.possibleStatuses():
            self.hideTaskStatus(taskStatus, hide=status != taskStatus)

    def isHidingTaskStatus(self, status):
        """
        Retourne l'état caché du status de la tâche.

        Args:
            status: Le statut de la tâche.

        Returns:
            bool: Un booléen indiquant si le statut est caché.
        """
        return self.__getBooleanSetting(f"hide{status}tasks")

    def hiddenTaskStatuses(self):
        """
        Retourne la liste des status cachés.

        Returns:
            list: Une liste des status cachés.
        """
        return [status for status in task.Task.possibleStatuses()
                if self.isHidingTaskStatus(status)]

    def hideCompositeTasks(self, hide=True):
        """
        Cacher les tâches composite.

        Args:
            hide: Un booléen indiquant si les tâches composite doivent être cachées.
        Returns:
            None
        """
        self.__setBooleanSetting("hidecompositetasks", hide)
        self.presentation().hideCompositeTasks(hide)

    def isHidingCompositeTasks(self):
        """
        Retourne True si les tâches composite sont cachées.

        Returns:
            bool: Un booléen indiquant si les tâches composite sont cachées.
        """
        return self.__getBooleanSetting("hidecompositetasks")

    def resetFilter(self):
        super().resetFilter()
        for status in task.Task.possibleStatuses():
            self.hideTaskStatus(status, False)
        if not self.isTreeViewer():
            self.hideCompositeTasks(False)

    def hasFilter(self):
        return super().hasFilter() or self.presentation().hasFilter()

    def createFilterUICommands(self):
        return super().createFilterUICommands() + [uicommand.ViewerHideTasks(
            taskStatus, viewer=self, settings=self.settings) for taskStatus in
             task.Task.possibleStatuses()] + [uicommand.ViewerHideCompositeTasks(viewer=self)]

    def __getBooleanSetting(self, setting):
        return self.settings.getboolean(self.settingsSection(), setting)

    def __setBooleanSetting(self, setting, booleanValue):
        self.settings.setboolean(self.settingsSection(), setting, booleanValue)


class SortableViewerMixin(object):
    """ Une visionneuse triable. C'est une classe mixin.

    Gère l'affichage du tri par colonne dans un Treeview.
    """

    def __init__(self, *args, **kwargs):
        log.debug("SortableViewerMixin.__init__ : initialisation d'une visionneuse triable.")
        self._sortUICommands = []
        super().__init__(*args, **kwargs)
        log.debug("SortableViewerMixin initialisée !")

    def isSortable(self):
        """
        Retourne True si le visualiseur est triable.

        Returns:
            bool: Un booléen indiquant si le visualiseur est triable.
        """
        return True

    def registerPresentationObservers(self):
        """
        Enregistrer et renvoyer la présentation aux abonnés observateurs.
        """
        super().registerPresentationObservers()
        pub.subscribe(self.onSortOrderChanged,
                      self.presentation().sortEventType())

    def detach(self):
        """
        Détacher le visualiseur.

        Arrête les ressources de rafraîchissement secondaire et minutaire
        si elles existent. Si une erreur survient lors de l'arrêt,
        elle est journalisée.

        ### Explication de la Méthode detach

        - **Arrêt des Ressources**: La méthode detach arrête les ressources de
                                    rafraîchissement secondaire (secondRefresher)
                                    et minutaire (minuteRefresher) si elles existent.
                                    Ces ressources sont utilisées
                                    pour mettre à jour automatiquement la vue
                                    lorsque certaines actions ont lieu.
        - **Journalisation d'Erreurs**: Si une erreur survient lors de l'arrêt
                                        des ressources, elle est journalisée
                                        avec log.exception().
        - **Appel Parent**: La méthode appelle le méthode parent detach()
                            pour terminer les actions spécifiques de la classe mixin.
        - **Unabonnement aux Événements**: L'événement onSortOrderChanged du
                                           présentateur est abonné,
                                           ce qui signifie que
                                           lorsque l'ordre de tri change,
                                           la vue est rafraîchie et
                                           le sélectionnement est mis à jour.

        Cette méthode assure que les ressources de rafraîchissement sont
        correctement arrêtées avant de fermer la visionneuse,
        réduisant ainsi les coûts d'énergie et garantissant une performance stable.

        Returns:
            None
        """
        try:
            if self.secondRefresher is not None:
                self.secondRefresher.stop()
        except Exception:
            log.exception("Impossible d'arrêter secondRefresher")

        try:
            if self.minuteRefresher is not None:
                self.minuteRefresher.stop()
        except Exception:
            log.exception("Impossible d'arrêter minuteRefresher")
        super().detach()
        pub.unsubscribe(self.onSortOrderChanged,
                        self.presentation().sortEventType())

    def onSortOrderChanged(self, sender):
        """
        Gestionnaire d'événement qui se déclenche lorsque le tri du modèle de données est modifié.

        Args:
            sender (EventSender) : L'objet qui a déclenché l'événement.

        Returns:
            None
        """
        # Vérifier si l'événement provient du modèle de données
        if sender == self.presentation():
            # Rafraîchir la vue et mettre à jour le sélectionnement
            self.refresh()
            self.updateSelection(sendViewerStatusEvent=False)
            self.sendViewerStatusEvent()

    def createSorter(self, presentation):
        """
        Crée un tri de la présentation.

        Args:
            presentation: Présentation à trier.

        Returns:
            Sorter: Un objet de tri.
        """
        return self.SorterClass(presentation, **self.sorterOptions())

    def sorterOptions(self):
        """
        Retourne les options de tri.

        Returns:
            dict: Un dictionnaire contenant les options de tri.
        """
        return dict(sortBy=self.sortKey(),
                    sortCaseSensitive=self.isSortCaseSensitive())

    def sortBy(self, sortKey):
        """
        Trier par mot-clé.

        Args:
            sortKey : Mot-clé pour définir le tri.

        Returns:
            None
        """
        self.presentation().sortBy(sortKey)
        self.settings.set(self.settingsSection(), "sortby", str(self.presentation().sortKeys()))

    def isSortedBy(self, sortKey) -> bool:
        """
        Vérifie si le modèle de données est trié par un certain mot-clé.

        Args:
            sortKey (str) : Le mot-clé utilisé pour définir le tri.

        Returns:
            bool: True si le modèle est trié par sortKey, False sinon.
        """
        presentation_obj = self.presentation()
        # log.debug(f"SortableViewerMixin.isSortBy : Type de presentation_ob: {type(presentation_obj)}")  # Attendu: NoteSorter
        log.debug(f"SortableViewerMixin.isSortBy : self.presentation(): {presentation_obj} pour self={self.__class__.__name__}.")
        sortKeys = self.presentation().sortKeys()
        # return sortKeys and (sortKeys[0] == sortKey or sortKeys[0] == "-" + sortKey)
        result_isSortBy = sortKeys and (sortKeys[0] == sortKey or sortKeys[0] == "-" + sortKey)
        return result_isSortBy

    def sortKey(self):
        """
        Récupère et retourne les clés de tri actuelles depuis les paramètres de configuration.

        Cette méthode lit la valeur du paramètre 'sortby' dans la section de settings
        de la visionneuse et l'évalue pour convertir la chaîne de caractères en objet Python.

        Returns:
            list: Une liste de clés de tri (ex : ['subject'] ou ['-description', 'subject']).
                  Le préfixe '-' indique un tri décroissant.

        Example :
            >>> viewer.sortKey()
            ['subject']
            >>> viewer.sortKey()
            ['-description', 'subject']
        """
        return eval(self.settings.get(self.settingsSection(), "sortby"))

    def isSortOrderAscending(self):
        """
        Détermine si l'ordre de tri actuel est ascendant.

        Cette méthode vérifie la première clé de tri de la présentation.
        Si la clé commence par '-', le tri est décroissant, sinon il est ascendant.

        Returns:
            bool: True si le tri est ascendant, False s'il est décroissant
                  ou si aucune clé de tri n'est définie.

        Example :
            >>> viewer.isSortOrderAscending()
            True  # Tri ascendant (ex : ['subject'])
            >>> viewer.isSortOrderAscending()
            False  # Tri décroissant (ex : ['-subject'])
        """
        sortKeys = self.presentation().sortKeys()
        return sortKeys and not sortKeys[0].startswith("-")

    def setSortOrderAscending(self, ascending=True):
        """
        Définie l'ordre de tri actuel comme ascendant selon la valeur de ascending.

        Règle la présentation et les mots clés de réglage.

        Args:
            ascending: Un booléen pour indiquer si ascendant ou non.
        """
        self.presentation().sortAscending(ascending)
        self.settings.set(self.settingsSection(), "sortby", str(self.presentation().sortKeys()))

    def isSortCaseSensitive(self):
        """
        Détermine si le tri est sensible à la casse.

        Cette méthode lit le paramètre 'sortcasesensitive' depuis les paramètres
        de configuration de la visionneuse.

        Returns:
            bool: True si le tri est sensible à la casse, False sinon.

        Example :
            >>> viewer.isSortCaseSensitive()
            True
            >>> viewer.isSortCaseSensitive()
            False
        """
        return self.settings.getboolean(self.settingsSection(), "sortcasesensitive")

    def setSortCaseSensitive(self, sortCaseSensitive=True):
        """
        Définit si le tri doit être sensible à la casse.

        Cette méthode met à jour le paramètre de configuration et la présentation
        pour appliquer le nouveau paramètre de sensibilité à la casse.

        Args:
            sortCaseSensitive (bool) : True pour un tri sensible à la casse,
                                       False pour un tri insensible à la casse.
                                       Par défaut True.

        Returns:
            None

        Example :
            >>> viewer.setSortCaseSensitive(True)
            >>> viewer.setSortCaseSensitive(False)
        """
        self.settings.set(self.settingsSection(), "sortcasesensitive",
                          str(sortCaseSensitive))
        self.presentation().sortCaseSensitive(sortCaseSensitive)

    def getSortUICommands(self):
        """
        Retourne les commandes d'interface utilisateur pour le tri.

        Cette méthode récupère les commandes d'interface utilisateur liées au tri.
        Si les commandes n'ont pas encore été créées, elles sont générées via
        createSortUICommands().

        Returns:
            list: Une liste de commandes d'interface utilisateur pour le tri.
        """
        if not self._sortUICommands:
            self.createSortUICommands()
        return self._sortUICommands

    def createSortUICommands(self):
        """
        Crée les commandes d'interface utilisateur pour le tri.

        Cette méthode combine les commandes liées à l'ordre de tri et celles liées aux critères de tri.
        Elle appelle createSortOrderUICommands() pour obtenir les commandes de tri par ordre,
        puis createSortByUICommands() pour obtenir les commandes de tri par critère.

        Si des commandes de tri par critère sont présentes, une commande None est ajoutée avant ces dernières
        dans la liste finale.

        Returns:
            list: Une liste comprenant les commandes d'interface utilisateur pour le tri.
        """
        self._sortUICommands = self.createSortOrderUICommands()
        sortByCommands = self.createSortByUICommands()
        if sortByCommands:
            self._sortUICommands.append(None)
            self._sortUICommands.extend(sortByCommands)


    def createSortOrderUICommands(self):
        """
        Crée les commandes d'interface utilisateur pour l'ordre de tri.

        Cette méthode crée deux commandes :
        - ViewerSortOrderCommand pour définir l'ordre parmi les options d'affichage disponibles.
        - ViewerSortCaseSensitive pour définir si le tri doit être sensible à la casse ou non.

        Returns:
            list: Une liste comprenant les commandes d'interface utilisateur de l'ordre de tri.
        """
        return [uicommand.ViewerSortOrderCommand(viewer=self),
                uicommand.ViewerSortCaseSensitive(viewer=self)]

    def createSortByUICommands(self):
        """
        Crée les commandes d'interface utilisateur pour trier par critère.

        Cette méthode crée des commandes pour chaque critère de tri défini, y compris :
        - "subject" (sujet)
        - "description" (description)
        - "creationDateTime" (date de création)
        - "modificationDateTime" (date de modification)

        Chaque commande est liée à un paramètre 'value' qui identifie le critère de tri,
        et un 'menuText' qui définit l'affichage dans l'interface utilisateur.

        Returns:
            list: Une liste des commandes d'interface utilisateur pour trier par critère.
        """
        return [
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="subject",
                menuText=_("Sub&ject"),
                helpText=self.sortBySubjectHelpText,
            ),
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="description",
                menuText=_("&Description"),
                helpText=self.sortByDescriptionHelpText,
            ),
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="creationDateTime",
                menuText=_("&Creation date"),
                helpText=self.sortByCreationDateTimeHelpText,
            ),
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="modificationDateTime",
                menuText=_("&Modification date"),
                helpText=self.sortByModificationDateTimeHelpText,
            ),
        ]


class SortableViewerForEffortMixin(SortableViewerMixin):
    def createSortOrderUICommands(self):
        return [uicommand.ViewerSortOrderCommand(viewer=self)]

    def createSortByUICommands(self):
        return []

    def sortKey(self):
        return ["-period"]


class ManualOrderingMixin(object):
    def __init__(self, *args, **kwargs):
        log.debug("ManualOrderingMixin.__init__ : initialisation de l'ordre manuel.")
        super().__init__(*args, **kwargs)
        log.debug("ManualOrderingMixin initialisée.")

    def createSortByUICommands(self):
        """
        Crée les commandes d'interface utilisateur pour trier par critère.

        Cette méthode crée des commandes pour chaque critère de tri défini et
        ajoute en début de liste l'ordre manuel.

        Returns:
            list: Une liste des commandes d'interface utilisateur pour trier par critère.
        """
        return [
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="ordering",
                menuText=_("&Manual ordering"),
                helpText=self.sortByOrderingHelpText
            )] + super(ManualOrderingMixin, self).createSortByUICommands()

    def orderingImageIndices(self, item):
        # TODO : Tkinter ne gère pas les images d'icônes de la même manière que wx,
        # donc cette méthode doit être adaptée dans les implémentations concrètes
        # du viewer si nécessaire. Ici, on peut retourner une valeur par défaut.
        return {}


class SortableViewerForCategoriesMixin(ManualOrderingMixin, SortableViewerMixin):
    sortBySubjectHelpText = _("Sort categories by subject")
    sortByDescriptionHelpText = _("Sort categories by description")
    sortByCreationDateTimeHelpText = _("Sort categories by creation date")
    sortByModificationDateTimeHelpText = _("Sort categories by last modification date")
    sortByOrderingHelpText = _("Sort categories manually")


class SortableViewerForCategorizablesMixin(SortableViewerMixin):
    """ Mixin class to create uiCommands for sorting categorizables. """

    def createSortByUICommands(self):
        commands = super().createSortByUICommands()
        commands.append(
            uicommand.ViewerSortByCommand(
                viewer=self,
                value="categories",
                menuText=_("&Category"),
                helpText=self.sortByCategoryHelpText,
            )
        )
        return commands


class SortableViewerForAttachmentsMixin(SortableViewerForCategorizablesMixin):
    sortBySubjectHelpText = _("Sort attachments by subject")
    sortByDescriptionHelpText = _("Sort attachments by description")
    sortByCategoryHelpText = _("Sort attachments by category")
    sortByCreationDateTimeHelpText = _("Sort attachments by creation date")
    sortByModificationDateTimeHelpText = _(
        "Sort attachments by last modification date"
    )


class SortableViewerForNotesMixin(
    ManualOrderingMixin, SortableViewerForCategorizablesMixin
):
    """
     Gère l'affichage du tri par colonne dans un Treeview spécifique aux notes.

    """
    sortBySubjectHelpText = _("Sort notes by subject")
    sortByDescriptionHelpText = _("Sort notes by description")
    sortByCategoryHelpText = _("Sort notes by category")
    sortByCreationDateTimeHelpText = _("Sort notes by creation date")
    sortByModificationDateTimeHelpText = _(
        "Sort notes by last modification date"
    )
    sortByOrderingHelpText = _("Sort notes manually")


class SortableViewerForTasksMixin(
    ManualOrderingMixin, SortableViewerForCategorizablesMixin
):
    """
    Gère l'affichage du tri par colonne dans un Treeview spécifique aux tâches.
    """
    SorterClass = task.sorter.Sorter
    sortBySubjectHelpText = _("Sort tasks by subject")
    sortByDescriptionHelpText = _("Sort tasks by description")
    sortByCategoryHelpText = _("Sort tasks by category")
    sortByCreationDateTimeHelpText = _("Sort tasks by creation date")
    sortByModificationDateTimeHelpText = _("Sort tasks by last modification date")
    sortByOrderingHelpText = _("Sort tasks manually")

    def __init__(self, *args, **kwargs):
        self.__sortKeyUnchangedCount = 0
        super().__init__(*args, **kwargs)

    def sortBy(self, sortKey):
        if self.isSortedBy(sortKey):
            self.__sortKeyUnchangedCount += 1
        else:
            self.__sortKeyUnchangedCount = 0
        if self.__sortKeyUnchangedCount > 1:
            self.setSortByTaskStatusFirst(not self.isSortByTaskStatusFirst())
            self.__sortKeyUnchangedCount = 0
        super().sortBy(sortKey)

    def isSortByTaskStatusFirst(self):
        return self.settings.getboolean(
            self.settingsSection(), "sortbystatusfirst"
        )

    def setSortByTaskStatusFirst(self, sortByTaskStatusFirst):
        self.settings.set(
            self.settingsSection(),
            "sortbystatusfirst",
            str(sortByTaskStatusFirst),
        )
        self.presentation().sortByTaskStatusFirst(sortByTaskStatusFirst)

    def sorterOptions(self):
        options = super().sorterOptions()
        options.update(treeMode=self.isTreeViewer(),
                       sortByTaskStatusFirst=self.isSortByTaskStatusFirst())
        return options

    def createSortOrderUICommands(self):
        commands = super().createSortOrderUICommands()
        commands.append(uicommand.ViewerSortByTaskStatusFirst(viewer=self))
        return commands

    def createSortByUICommands(self):
        commands = super().createSortByUICommands()
        dependsOnEffortFeature = [
            "budget",
            "timeSpent",
            "budgetLeft",
            "hourlyFee",
            "fixedFee",
            "revenue",
        ]
        for menuText, helpText, value in [
            (
                _("&Planned start date"),
                _("Sort tasks by planned start date"),
                "plannedStartDateTime",
            ),
            (_("&Due date"), _("Sort tasks by due date"), "dueDateTime"),
            (
                _("&Completion date"),
                _("Sort tasks by completion date"),
                "completionDateTime",
            ),
            (
                _("&Prerequisites"),
                _("Sort tasks by prerequisite tasks"),
                "prerequisites",
            ),
            (
                _("&Dependents"),
                _("Sort tasks by dependent tasks"),
                "dependencies",
            ),
            (_("&Time left"), _("Sort tasks by time left"), "timeLeft"),
            (
                _("&Percentage complete"),
                _("Sort tasks by percentage complete"),
                "percentageComplete",
            ),
            (_("&Recurrence"), _("Sort tasks by recurrence"), "recurrence"),
            (_("&Budget"), _("Sort tasks by budget"), "budget"),
            (_("&Time spent"), _("Sort tasks by time spent"), "timeSpent"),
            (_("Budget &left"), _("Sort tasks by budget left"), "budgetLeft"),
            (_("&Priority"), _("Sort tasks by priority"), "priority"),
            (_("&Hourly fee"), _("Sort tasks by hourly fee"), "hourlyFee"),
            (_("&Fixed fee"), _("Sort tasks by fixed fee"), "fixedFee"),
            (_("&Revenue"), _("Sort tasks by revenue"), "revenue"),
            (
                _("&Reminder"),
                _("Sort tasks by reminder date and time"),
                "reminder",
            ),
        ]:
            if value not in dependsOnEffortFeature or (
                value in dependsOnEffortFeature
            ):
                commands.append(
                    uicommand.ViewerSortByCommand(
                        viewer=self,
                        value=value,
                        menuText=menuText,
                        helpText=helpText,
                    )
                )
        return commands


class AttachmentDropTargetMixin(object):
    """ Classe Mixin pour les téléspectateurs qui sont des cibles de dépôt
    pour les pièces jointes (attachments).

    Propose une interface pour ajouter des pièces jointes à un élément.
    """
    # Cette classe AttachmentDropTargetMixin est un mixin utilisé dans les
    # classes de visualisation de documents (par exemple, NoteTreeview ou TaskTreeview)
    # pour gérer les téléspectateurs qui sont des cibles de dépôt
    # pour les pièces jointes (attachments).
    # Voici une explication détaillée du contenu de cette classe et de son utilité :
    #
    # L'utilisation du mixin AttachmentDropTargetMixin permet de centraliser
    # le code relatif au dépôt de pièces jointes dans une classe unique,
    # ce qui facilite la maintenance et l'extension du code.

    def widgetCreationKeywordArguments(self):
        """ Retourne les arguments de création du widget.

        La méthode widgetCreationKeywordArguments est utilisée
        pour fournir les arguments de création
        pour les widgets qui sont utilisés dans la vue.
        Cela peut inclure des options spécifiques comme des icônes personnalisées.
        """
        kwargs = super().widgetCreationKeywordArguments()
        # Tkinter ne gère pas les événements de glisser-déposer de la même manière que wx,
        # donc les gestionnaires d'événements doivent être liés directement aux widgets.
        # On garde les noms de méthodes pour la compatibilité, mais elles seront appelées
        # par des bindings Tkinter.
        return kwargs

    def _addAttachments(self, attachments, item, **itemDialogKwargs):
        """
        Ajouter des pièces jointes. Si l'élément fait référence à un objet de domaine existant,
        ajoutez les pièces jointes à cet objet. Si l'élément est None, utilisez le
        newItemDialog pour créer un nouvel objet de domaine et ajouter les pièces jointes
        à ce nouvel objet.

        La méthode _addAttachments est appelée lorsqu'une pièce jointe
        est déposée sur un élément.
        Elle gère le processus de création ou d'ajout des pièces jointes
        en fonction du type d'élément (item) et des paramètres spécifiques.
        """
        print(f"mixin.AttachmentDropTargetMixin._addAttachments : 📌 [DEBUG] Ajout des attachements : {attachments}")
        if item is None:
            itemDialogKwargs["subject"] = attachments[0].subject()
            if self.settings.get(
                "view", "defaultplannedstartdatetime"
            ).startswith("preset"):
                itemDialogKwargs["plannedStartDateTime"] = (
                    task.Task.suggestedPlannedStartDateTime()
                )
            if self.settings.get("view", "defaultduedatetime").startswith(
                "preset"
            ):
                itemDialogKwargs["dueDateTime"] = (
                    task.Task.suggestedDueDateTime()
                )
            if self.settings.get(
                "view", "defaultactualstartdatetime"
            ).startswith("preset"):
                itemDialogKwargs["actualStartDateTime"] = (
                    task.Task.suggestedActualStartDateTime()
                )
            if self.settings.get(
                "view", "defaultcompletiondatetime"
            ).startswith("preset"):
                itemDialogKwargs["completionDateTime"] = (
                    task.Task.suggestedCompletionDateTime()
                )
            if self.settings.get("view", "defaultreminderdatetime").startswith(
                "preset"
            ):
                itemDialogKwargs["reminder"] = (
                    task.Task.suggestedReminderDateTime()
                )
            newItemDialog = self.newItemDialog(
                bitmap="new", attachments=attachments, **itemDialogKwargs
            )
            newItemDialog.Show()
        else:
            addAttachment = command.AddAttachmentCommand(self.presentation(),
                                                         [item], attachments=attachments)
            addAttachment.do()

    def onDropURL(self, item, url, **kwargs):
        """ Cette méthode est appelée par le widget lorsqu'une URL est déposée sur un élément.

        Le gestionnaire d'événement onDropURL est appelé lorsque une URL
        est déposée sur un élément. Cela appelle la méthode _addAttachments
        pour ajouter les pièces jointes à l'élément correspondant.
        """
        attachments = [attachment.URIAttachment(url)]
        self._addAttachments(attachments, item, **kwargs)

    def onDropFiles(self, item, filenames, **kwargs):
        """This method is called by the widget when one or more files
        are dropped on an item."""
        attachmentBase = self.settings.get("file", "attachmentbase")
        if attachmentBase:
            filenames = [attachment.getRelativePath(filename, attachmentBase)
                         for filename in filenames]
        attachments = [attachment.FileAttachment(filename) for filename in filenames]
        self._addAttachments(attachments, item, **kwargs)

    def onDropMail(self, item, mail, **kwargs):
        """
        This method is called by the widget when a mail message is dropped
        on an item.

        Le gestionnaire d'événement onDropMail est appelé lorsqu'un message de
        courrier électronique est déposé sur un élément.
        Cela appelle la méthode _addAttachments
        pour ajouter les pièces jointes à l'élément correspondant.
        """
        att = attachment.MailAttachment(mail)
        subject, content = att.read()
        self._addAttachments([att], item, subject=subject, description=content,
                             **kwargs)


class NoteColumnMixin(object):
    """
    Propose une interface pour afficher les notes sur le côté d'un élément de la liste.

    La classe NoteColumnMixin est utilisée dans les classes de visualisation
    de notes (par exemple, NoteTreeview) pour gérer les icônes personnalisées
    d'une colonne spécifique (note_image_indices).
    Cela peut inclure l'ajout d'une icône spéciale pour les notes.
    """
    def noteImageIndices(self, item):
        # La gestion des icônes dans les Treeview de Tkinter est différente.
        # Cette méthode devra être implémentée au cas par cas dans la
        # classe de viewer qui l'utilise.
        # Pour le moment, on retourne un index par défaut ou un nom d'image.
        return "note_icon" if item.notes() else ""


class AttachmentColumnMixin(object):
    """
    Propose une interface pour afficher les pièces jointes sur le côté d'un élément de la liste.

    La classe AttachmentColumnMixin est utilisée dans les classes de
    visualisation d'attachments (par exemple, TaskTreeview)
    pour gérer les icônes personnalisées d'une colonne spécifique
    (attachment_image_indices).
    Cela peut inclure l'ajout d'une icône spéciale pour les pièces jointes.
    """
    def attachmentImageIndices(self, item):
        # Comme pour NoteColumnMixin, cette méthode doit être adaptée.
        return "paperclip_icon" if item.attachments() else ""
