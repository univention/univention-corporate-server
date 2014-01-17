#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: timezone selection
#
# Copyright 2004-2013 Univention GmbH
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

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

from objects import *
from local import _

HEIGHT = 25
WIDTH = 40


class object(content):
	def checkname(self):
		return ['timezone']

	def profile_complete(self):
		if self.check('timezone') or self.check('locales') or self.check('locale_default'):
			return False
		if self.all_results.has_key('timezone') and self.all_results.has_key('locales') and self.all_results.has_key('locale_default'):
			return True
		else:
			if self.ignore('timezone') and self.ignore('locales') and self.ignore('locale_default'):
				return True
			return False

	def get_locale_from_language(self, language, countrycode):
		try:
			file = open('/usr/share/i18n/SUPPORTED')
		except:
			file = open('/usr/share/locale/SUPPORTED')

		lang = language.split("_")[0]
		lang_code = lang.lower() + "_" + countrycode.upper()

		for line in file:
			if line.startswith("#"): continue
			line = line.strip("\n")
			parts = line.split(" ")
			if len(parts) > 1:
				# we want only utf-8 locales
				if parts[1].lower() == "utf-8":
					# append .UTF-8 if necessary
					if not parts[0].upper().endswith(".UTF-8"):
						parts[0] = "%s.UTF-8" % parts[0]
					# check if language_countrycode locale exist
					if parts[0].replace(".UTF-8", "") == lang_code:
						return parts[0] + ":UTF-8"

		# non found, return fallback locale from locale/languagelist or en_US locale
		fallback = self.cmdline.get("DEFAULT_LOCALE", "en_US.UTF-8")
		if not fallback.endswith(".UTF-8"):
			fallback = fallback + ".UTF-8"
		if not fallback.endswith(":UTF-8"):
			fallback = fallback + ":UTF-8"
		return fallback

	def get_countrycode_from_timezone(self, timezone):
		try:
			file = open('locale/countrycode2timezone')
		except:
			file = open('/lib/univention-installer/locale/countrycode2timezone')

		for line in file:
			if line.startswith("#"): continue
			line = line.strip("\n")
			parts = line.split(" ")
			if len(parts) > 1:
				if timezone.lower() ==  parts[1].lower():
					return parts[0]

		return "DE"

	def get_default_timezone(self, countrycode):
		try:
			file = open('locale/countrycode2timezone')
		except:
			file = open('/lib/univention-installer/locale/countrycode2timezone')

		for line in file:
			if line.startswith("#"): continue
			line = line.strip("\n")
			parts = line.split(" ")
			if len(parts) > 1:
				if countrycode.upper() == parts[0].upper():
					return parts[1]

		return "Europe/Berlin"

	def get_timezone_shortlist(self, countrycode):
		timezones = {}
		shortFile = "locale/short-list/%s.short" % countrycode

		if os.path.isfile(shortFile) or os.path.isfile("/lib/univention-installer/" + shortFile):
			try:
				file = open(shortFile)
			except:
				file = open("/lib/univention-installer/" + shortFile)

			for line in file:
				if line.startswith("#"): continue
				line = line.strip("\n")
				parts = line.split("\t")
				if len(parts) > 2:
					timezones[self.get_default_timezone(parts[0])] = 1

		return timezones

	def get_all_timezones(self):
		timezones = {}
		try:
			file = open('locale/timezone')
		except:
			file = open('/lib/univention-installer/locale/timezone')

		for line in file:
			line = line.strip("\n")
			if line.startswith("#"): continue
			timezones[line] = 1

		return timezones

	def create_timezone_list(self, defaultTimeZone, showAll=False):
		zones = {}

		zones = self.get_timezone_shortlist(self.cmdline.get("DEFAULT_COUNTRYCODE", "DE").lower())
		zones.update(self.get_timezone_shortlist(self.cmdline.get("DEFAULT_LANGUAGE", "de")))

		# no short list was found, display default timezone
		if not zones:
			zones[defaultTimeZone] = 1

		# disply all zones
		if showAll:
			zones = self.get_all_timezones()

		dict = {}
		zoneCounter = 0
		default_position = 0

		for zone in sorted(zones):
			dict[zone] = [zone, zoneCounter]
			if zone == defaultTimeZone:
				default_position = zoneCounter
			zoneCounter = zoneCounter + 1

		return dict, default_position, showAll

	def layout(self):
		if self.all_results.has_key('timezone'):
			self.timezone_default = self.all_results['timezone']
		else:
			self.timezone_default = self.get_default_timezone(self.cmdline.get("DEFAULT_COUNTRYCODE", "DE"))

		dict, default_position, showAll = self.create_timezone_list(self.timezone_default)

		self.elements.append(textline(_('Select a time zone:'), self.minY-11, self.minX+5))
		self.add_elem('ZONES',select(dict, self.minY-9, self.minX+5, WIDTH, HEIGHT, default_position, longline=1))
		self.add_elem('CBX', checkbox({_('Show all available timezones'):['yes', 0]},self.minY-8+HEIGHT, self.minX+5, WIDTH, 1, []))

		self.move_focus(self.get_elem_id('ZONES'))

	def update_elem_zones(self):
		idx = self.get_elem_id('ZONES')
		cbx = self.get_elem('CBX')
		all_zones = bool(cbx.result())
		if self.all_results.has_key('timezone'):
			self.timezone_default = self.all_results['timezone']

		dict, default_position, showAll = self.create_timezone_list(self.timezone_default, all_zones)
		elem = select(dict, self.minY-9, self.minX+5, WIDTH, HEIGHT, default_position, longline=1)
		self.elements[idx] = elem

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key in [ 10, 32 ] and self.get_elem('CBX').active:
			self.elements[self.current].key_event(key)
			self.update_elem_zones()
			self.draw()
		else:
			return self.elements[self.current].key_event(key)

#	def draw(self):
#		content.draw(self)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Time zone \n \n Select the time zone your system is located in. ')

	def modheader(self):
		return _('Time zone')

	def profileheader(self):
		return 'Time zone'

	def result(self):
		result = {}
		zone = self.get_elem('ZONES').result()[0]
		countrycode = self.get_countrycode_from_timezone(zone)
		self.cmdline["COUNTRY_FROM_TIMEZONE"] = countrycode
		locale = self.get_locale_from_language(self.cmdline.get("DEFAULT_LANGUAGE", "de"), countrycode)
		result['timezone'] = zone
		result['locales'] = locale
		result['locale_default'] = locale
		return result
