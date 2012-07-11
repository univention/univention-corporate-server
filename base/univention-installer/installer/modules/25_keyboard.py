#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: keyboard layout selection
#
# Copyright 2004-2012 Univention GmbH
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
		return ['keymap']

	def profile_complete(self):
		if self.check('keymap') | self.check('country'):
			return False
		if self.all_results.has_key('keymap') or self.all_results.has_key('country'):
			return True
		else:
			if self.ignore('country') or self.ignore('keymap'):
				return True
			return False

	def run_profiled(self):
		if self.all_results.has_key('country'):
			map = self.all_results['country']
		else:
			map = self.all_results['keymap']

		self.loadkeys(map)

		if self.all_results.has_key('country'):
			return { 'keymap': self.all_results['country']}
		elif self.all_results.has_key('keymap'):
			return { 'keymap': self.all_results['keymap']}

	def get_keymaps(self, all=False):
		maps = {}

		if all:
			kfile = "all-kmaps"
		else:
			kfile = "default-kmaps"

		# get kmaps for language countries
		try:
			file = open("locale/" + kfile)
		except:
			file = open("/lib/univention-installer/locale/" + kfile)
		for line in file:
			if line.startswith("#"): continue
			line = line.strip("\n")
			parts = line.split(":")
			if len(parts) > 1:
				parts[0] = parts[0].replace("Standard ", "")
				parts[0] = parts[0].replace(" Standard ", "")
				parts[0] = parts[0].replace("Standard", "")
				maps[parts[0]] = parts[1]

		return maps

	def create_kmap_list(self, language, showAll=False):
		if showAll:
			maps = self.get_keymaps(all=True)
		else:
			maps = self.get_keymaps()

		dict = {}
		mapCounter = 0
		default_position = 0
		for map in sorted(maps):
			mapFile = maps[map]
			dict[map] = [mapFile, mapCounter]
			if map[0:4] == language[0:4]:
				default_position = mapCounter
			if language == mapFile:
				default_position = mapCounter
			if self.cmdline.get("COUNTRY_FROM_TIMEZONE", "").lower() == mapFile:
				default_position = mapCounter
			mapCounter = mapCounter + 1

		return dict, default_position, showAll

	def layout(self):
		if self.all_results.has_key('keymap'):
			default_value = self.all_results['keymap']
		else:
			default_value = self.cmdline.get("DEFAULT_LANGUAGE_EN", "German")

		dict, default_position, showAll = self.create_kmap_list(default_value)

		self.elements.append(textline(_('Select your keyboard layout:'), self.minY-11, self.minX+5))
		self.add_elem('MAPS',select(dict,self.minY-9, self.minX+5, WIDTH, HEIGHT, default_position))
		self.add_elem('CBX', checkbox({_('Show all available keyboard layouts'):' '}, self.minY-8+HEIGHT, self.minX+5, 60, 1, []))

		self.move_focus(self.get_elem_id('MAPS'))

# 	def draw(self):
# 		content.draw(self)

	def update_elem_maps(self):
		idx = self.get_elem_id('MAPS')
		cbx = self.get_elem('CBX')
		all_kmaps = bool(cbx.result())
		if self.all_results.get('keymap'):
			default_value = self.all_results.get('keymap')
		else:
			default_value = self.cmdline.get("DEFAULT_LANGUAGE_EN", "German")

		dict, default_position, showAll = self.create_kmap_list(default_value, all_kmaps)
		elem = select(dict, self.minY-9, self.minX+5, WIDTH, HEIGHT, default_position, longline=1)
		self.elements[idx] = elem

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key in [ 10, 32 ] and self.get_elem('CBX').active:
			self.elements[self.current].key_event(key)
			self.update_elem_maps()
			self.draw()
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Keyboard layout \n \n Select your keyboard layout.')

	def modheader(self):
		return _('Keyboard')

	def profileheader(self):
		return 'Keyboard'

	def loadkeys(self, map):
		if ":" in map:
			map = map.split(":")[1]

		mapFile = "/usr/keymaps/%s.kmap" % map

		if os.path.exists(mapFile):
			self.debug('binary-keyset: %s' % mapFile)
			os.system('/bin/loadkeys < %s > /dev/null 2>&1'% mapFile)
		else:
			self.debug('binary-keyset: %s not found' % mapFile)

		# ???
		if os.path.exists('/lib/univention-installer-startup.d/S88keyboard'):
			os.system('/lib/univention-installer-startup.d/S88keyboard > /dev/null 2>&1')

	def result(self):
		result = {}
		map = self.get_elem('MAPS').result()[0]
		self.loadkeys(map)
		result['keymap'] = map
		return result
