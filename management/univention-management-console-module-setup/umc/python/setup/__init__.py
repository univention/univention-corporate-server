#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import subprocess
import re
import csv
import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
import util

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-setup').translate

PATH_SYS_CLASS_NET = '/sys/class/net'

class Instance(umcm.Base):
	def load(self, request):
		'''Return a dict with all necessary values for system-setup read from the current
		status of the system.'''
		values = util.load_values()
		self.finished(request.id, values)

	def save(self, request):
		'''Reconfigures the system according to the values specified in the dict given as
		option names "values".'''

		values = request.options.get('values')
		if not values:
			MODULE.error( 'No property "values" given for save().' )
			self.finished(request.id, False)
			return

		# write the profile file and run setup scripts
		util.write_profile(values)
		util.run_scripts()

		# finish request
		self.finished(request.id, True)

	def lang_locales(self, request):
		'''Return a list of all available locales.'''
		try:
			file = open('/lib/univention-installer/locale/languagelist')
		except:
			MODULE.error( 'Cannot find locale data for languages in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		r = csv.reader(file, delimiter=';')
		locales = [ { 'label': i[1], 'id': '%s:UTF-8' % i[5] } for i in r if not i[0].startswith('#') ]

		self.finished(request.id, locales)

	def lang_timezones(self, request):
		'''Return a list of all available time zones.'''
		try:
			file = open('/lib/univention-installer/locale/timezone')
		except:
			MODULE.error( 'Cannot find locale data for timezones in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		timezones = [ i.strip('\n') for i in file if not i.startswith('#') ]

		self.finished(request.id, timezones)

	def lang_keymaps(self, request):
		'''Return a list of all available keyboard layouts.'''
		try:
			file = open('/lib/univention-installer/locale/all-kmaps')
		except:
			MODULE.error( 'Cannot find locale data for keymaps in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		r = csv.reader(file, delimiter=':')
		keymaps = [ { 'label': i[0], 'id': i[1] } for i in r if not i[0].startswith('#') ]

		self.finished(request.id, keymaps)

	def net_read(self, request):
		'''Return a dict of all current network settings.'''

	def net_interfaces(self, request):
		'''Return a list of all available network interfaces.'''
		interfaces = [ idev['name'] for idev in util.detect_interfaces() ]
		self.finished(request.id, interfaces)

	def net_dhclient(self, request):
		'''Request a DHCP address. Expects as options a dict containing the key
		"interface" and optionally the key "timeout" (in seconds).'''
		interface = request.options.get('interface')
		timeout = request.options.get('timeout', 45)
		if not interface:
			MODULE.error( 'No property "interface" given for dhclient().' )
			self.finished(request.id, None)
			return

		res = util.dhclient(interface, timeout)
		self.finished(request.id, res)



