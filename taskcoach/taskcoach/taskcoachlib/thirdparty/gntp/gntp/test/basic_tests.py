#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Simple test to send each priority level
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
logging.basicConfig(level=logging.WARNING)

import os
import unittest
from gntp.test import GNTPTestCase
import gntp
import gntp.config
import gntp.notifier

ICON_URL = "https://www.google.com/intl/en_com/images/srpr/logo3w.png"
ICON_FILE = os.path.join(os.path.dirname(__file__), "growl-icon.png")
CALLBACK_URL = "http://github.com"


class BasicTests(GNTPTestCase):
	def test_mini(self):
		gntp.notifier.mini('Testing gntp.notifier.mini',
			applicationName=self.application
			)

	def test_config(self):
		gntp.config.mini('Testing gntp.config.mini',
			applicationName=self.application
			)

	def test_priority(self):
		for priority in [2, 1, 0, -1, -2]:
			self.assertIsTrue(self._notify(
				description='Priority %s' % priority,
				priority=priority
				))

	def test_english(self):
		self.assertIsTrue(self._notify(description='Hello World'))

	def test_extra(self):
		self.assertIsTrue(self._notify(description='allô'))

	def test_japanese(self):
		self.assertIsTrue(self._notify(description='おはおう'))

	def test_sticky(self):
		self.assertIsTrue(self._notify(sticky=True, description='Sticky Test'))

	def test_unknown_note(self):
		self.assertRaises(AssertionError, self._notify, noteType='Unknown')

	def test_parse_error(self):
		self.assertRaises(gntp.ParseError, gntp.parse_gntp, 'Invalid GNTP Packet')

	def test_url_icon(self):
		self.assertIsTrue(self._notify(
			icon=ICON_URL,
			description='test_url_icon',
			))

	def test_file_icon(self):
		self.assertIsTrue(self._notify(
			icon=open(ICON_FILE, 'rb').read(),
			description='test_file_icon',
			))

	def test_callback(self):
		self.assertIsTrue(self._notify(
			callback=CALLBACK_URL,
			description='Testing Callback',
			))

	#def test_subscribe(self):
	#	self.assertTrue(self.growl.subscribe(
	#		id='unittest-id',
	#		name='example.com',
	#		port=5000,
	#		))

if __name__ == '__main__':
	unittest.main()
