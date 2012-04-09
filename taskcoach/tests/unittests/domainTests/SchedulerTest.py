'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2012 Task Coach developers <developers@taskcoach.org>

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

import test
from taskcoachlib.domain import date


class SchedulerTest(test.TestCase):    
    def setUp(self):
        super(SchedulerTest, self).setUp()
        self.scheduler = date.Scheduler()
        
    def callback(self):
        pass
        
    def testScheduleAtDateTime(self):
        futureDate = date.Now() + date.oneDay
        self.scheduler.schedule(self.callback, futureDate)
        self.failUnless(self.scheduler.get_jobs())
        self.scheduler._process_jobs(futureDate)
        self.failIf(self.scheduler.get_jobs())

    def testScheduleAtPastDateTime(self):
        pastDate = date.Now() + date.oneDay
        self.scheduler.schedule(self.callback, pastDate)
        self.failUnless(self.scheduler.get_jobs())
        self.scheduler._process_jobs(pastDate)
        self.failIf(self.scheduler.get_jobs())