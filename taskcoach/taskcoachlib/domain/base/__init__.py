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

# Tu as actuellement un système qui fonctionne depuis longtemps,
# avec beaucoup de logique métier imbriquée dans Object, Owner, Task, Category,
# les métaclasses et les événements.
# Dans ce contexte, passer directement à un framework générique
# de sérialisation serait risqué.
# La phase "safe mais minimale" va te permettre
# de stabiliser le comportement avant toute refactorisation.

# Phase 1 : Stabilisation
# 1. Définir les invariants de sérialisation
# Avant même de modifier Task ou Category,
# documenter noir sur blanc les invariants.
# Pour tout objet dérivant de Object :
# state["status"]
# state["id"]
# state["subject"]
# state["description"]
# state["creationDateTime"]
# state["modificationDateTime"]
# state["fgColor"]
# state["bgColor"]
# state["font"]
# state["icon"]
# state["selectedIcon"]
# state["ordering"]

# doivent toujours survivre à :
# state = obj.__getstate__()
# new_obj = type(obj)()
# new_obj.__setstate__(state)
# new_state = new_obj.__getstate__()

# Autrement dit :
# assert state["status"] == new_state["status"]
# assert state["id"] == new_state["id"]
# assert state["subject"] == new_state["subject"]
# assert state["description"] == new_state["description"]
# ...

from .object import Object, CompositeObject, SynchronizedObject
from .attribute import Attribute, SetAttribute
from .collection import Collection
from .filter import Filter, SearchFilter, SelectedItemsFilter, DeletedFilter
from .sorter import Sorter, TreeSorter
from .owner import DomainObjectOwnerMetaclass
from .appearance import (
    computeDerived,
    computeEffective,
    FIELD_TYPES,
    SYSTEM_FG_COLOR,
    SYSTEM_BG_COLOR,
    SYSTEM_FONT,
    SYSTEM_THEME_SOURCE,
)

# from .owner import DomainObjectOwnerMetaclass, NoteOwner, AttachmentOwner
# Où sont ces deux dernières classes ?
# NoteOwner est dans domain.note.noteowner
# et AttachmentOwner est dans domain.attachment.attachmentowner

__all__ = [
    "Attribute",
    "Collection",
    "CompositeObject",
    "DeletedFilter",
    "DomainObjectOwnerMetaclass",
    "Filter",
    "Object",
    "SearchFilter",
    "SelectedItemsFilter",
    "SetAttribute",
    "Sorter",
    "SynchronizedObject",
    "TreeSorter",
]

# Ce fichier domain.base.__init__ est demandé par :
# tclib/domain/attachment/attachment
# tclib/domain/attachment/attachmentowner
# tclib/domain/attachment/sorter
# tclib/domain/base/filter
# tclib/domain/categorizable/categorizable
# tclib/domain/categorizable/categorizablecontainer
# tclib/domain/category/category
# tclib/domain/effort/effort
# tclib/gui/menu
# tclib/gui/uicommand/uicommand
# tclib/gui/viewer/mixin
# tclib/gui/persistence/taskfile
# tclib/persistence/xml/reader
# tests/unittests/domainTests/test_base
# tests/unittests/domainTests/test_filter
# tests/unittests/guiTests/EditorTest
# tests/unittests/guiTests/UpdatePerSecondViewerTest
# tests/unittests/persistenceTests/XMLWriterTest
