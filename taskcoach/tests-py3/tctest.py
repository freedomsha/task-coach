#!/usr/bin/env python

'''
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
'''

import os
import sys
import unittest
import logging
import gettext

from pubsub import pub
import wx

gettext.NullTranslations().install()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from taskcoachlib import patterns


class TestCase(unittest.TestCase):
    def setUp(self):
        # Some non-UI stuff also needs the app to be constructed (like
        # wx.BLACK et al)
        self.app = wx.App(0)

    def tearDown(self):
        self.app.Disconnect(wx.ID_ANY)

        patterns.Publisher().clear()
        patterns.NumberedInstances.count = dict()
        if hasattr(self, 'events'):
            del self.events
        pub.unsubAll()
        super().tearDown()

    def assertEqualLists(self, expectedList, actualList):
        self.assertEqual(len(expectedList), len(actualList))
        for item in expectedList:
            self.assertTrue(item in actualList)

    def registerObserver(self, eventType, eventSource=None):
        if not hasattr(self, 'events'):
            self.events = []  # pylint: disable=W0201
        patterns.Publisher().registerObserver(self.onEvent, eventType=eventType,
                                              eventSource=eventSource)

    def onEvent(self, event):
        self.events.append(event)


def main():
    unittest.main()
