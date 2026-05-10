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

from pubsub import pub
from ... import tctest


class PubSubTest(tctest.TestCase):
    def setUp(self):
        """Initialize the test case."""
        self.calledTestTopic = False

    def onTestTopic(self):
        """Handler for the 'TestTopic' topic.

        En français : 'Gestionnaire pour le sujet 'TestTopic'.'
        """
        self.calledTestTopic = True

    def testSubscribe(self):
        """Test that subscribing to a topic and sending a message works.

        En français : 'Tester que s'abonner à un sujet et envoyer un message fonctionne.'
        """
        pub.subscribe(self.onTestTopic, "TestTopic")
        pub.sendMessage("TestTopic")
        self.assertTrue(self.calledTestTopic)
