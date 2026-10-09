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

# from builtins import range
# from builtins import object
import logging
from taskcoachlib import operating_system

from taskcoachlib.gui.viewer import effort
from taskcoachlib.gui.viewer import task
from taskcoachlib.gui.viewer import category
from taskcoachlib.gui.viewer import note

log = logging.getLogger(__name__)  # Initialise le logger pour ce module.


def viewerTypes():
    """Return the available viewer types, using the names as used in the
    settings.

    Renvoie les types de visionneuses disponibles, en utilisant les noms utilisés dans les paramètres.
    """
    types = [
        "timelineviewer",
        "squaretaskviewer",
        "taskviewer",
        "taskstatsviewer",
        "noteviewer",
        "categoryviewer",
        "effortviewer",
        "calendarviewer",
        "hierarchicalcalendarviewer",
        "effortviewerforselectedtasks",
    ]
    try:
        import igraph
    except ImportError:
        pass
    else:
        types.append("taskinterdepsviewer")
    return tuple(types)


class addViewers(object):  # pylint: disable=C0103, R0903
    """addViewers est une classe se faisant passer pour une méthode.

    C'est une classe car cela facilite la répartition du travail
    entre différentes méthodes utilisant les mêmes variables d'instance.
    """

    floating = False  # Start viewers floating? Not when restoring layout

    def __init__(self, viewer_container, task_file, settings):
        self.__viewer_container = viewer_container
        self.__settings = settings
        self.__viewer_init_args = (
            viewer_container.containerWidget,
            task_file,
            settings,
        )
        self.__add_all_viewers()

    def __add_all_viewers(self):
        """Open viewers as saved previously in the settings.

        Ouvrez les visionneuses telles qu'elles ont été enregistrées précédemment dans les paramètres.
        """
        self.__add_viewers(task.TaskViewer)
        self.__add_viewers(task.TaskStatsViewer)
        self.__add_viewers(task.SquareTaskViewer)
        self.__add_viewers(task.TimelineViewer)
        self.__add_viewers(task.CalendarViewer)
        self.__add_viewers(task.HierarchicalCalendarViewer)
        try:
            import igraph
        except ImportError:
            pass
        else:
            self.__add_viewers(task.TaskInterdepsViewer)
        self.__add_viewers(effort.EffortViewer)
        self.__add_viewers(effort.EffortViewerForSelectedTasks)
        self.__add_viewers(category.CategoryViewer)
        self.__add_viewers(note.NoteViewer)

    def __add_viewers(self, viewer_class):
        """Ouvrez les visionneuses de la classe de visionneuse spécifiée
        telle que enregistrée précédemment dans les paramètres.
        """
        number_of_viewers_to_add = self._number_of_viewers_to_add(viewer_class)
        for _ in range(number_of_viewers_to_add):
            log.debug(
                "addViewers.__add_viewers : Adding viewer of class %s",
                viewer_class,
            )
            log.warning(
                f"addViewers.__add_viewers : viewer_instance = {viewer_class.__name__}({self.__viewer_init_args}, {self._viewer_kwargs(viewer_class)})"
            )
            viewer_instance = viewer_class(
                *self.__viewer_init_args, **self._viewer_kwargs(viewer_class)
            )
            self.__viewer_container.addViewer(
                viewer_instance, floating=self.floating
            )

    def _number_of_viewers_to_add(self, viewer_class):
        """
        Renvoie le nombre de visionneuses de la classe de visionneuse spécifiée
        que l'utilisateur a ouverte précédemment.
        """
        return self.__settings.getint(
            "view", viewer_class.__name__.lower() + "count"
        )

    def _viewer_kwargs(self, viewer_class):  # pylint: disable=R0201
        """
        Return the keyword arguments to be passed to the viewer
        initializer.

        Renvoie les arguments de mot-clé à transmettre à l'initialiseur du visualiseur.
        """
        return (
            dict(viewerContainer=self.__viewer_container)
            if issubclass(viewer_class, effort.EffortViewerForSelectedTasks)
            else dict()
        )


class addOneViewer(addViewers):  # pylint: disable=C0103, R0903
    """addOneViewer is a class masquerading as a method to add one viewer
    of a specified viewer class.

    addOneViewer est une classe se faisant passer pour une méthode
    permettant d'ajouter une visionneuse d'une classe de visionneuse spécifiée.
    """

    floating = True  # Start viewer floating? Yes when opening a new viewer

    def __init__(
        self, viewer_container, task_file, settings, viewer_class, **kwargs
    ):
        self.__viewer_class = viewer_class
        self.__kwargs = kwargs
        super().__init__(viewer_container, task_file, settings)

    def _number_of_viewers_to_add(self, viewer_class):
        return 1 if viewer_class == self.__viewer_class else 0

    def _viewer_kwargs(self, viewer_class):
        kwargs = super()._viewer_kwargs(viewer_class)
        kwargs.update(self.__kwargs)
        return kwargs
