#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module:
#   MODULEDESC
#
# Copyright YEAR Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import uuid

from univention.lib.i18n import Translation
from univention.management.console.base import Base
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.log import MODULE

_ = Translation('PACKAGENAME').translate


class Instance(Base):
	# list of dummy entries
	entries = map(lambda x: {'id': str(uuid.uuid4()), 'name': x[0], 'color': x[1]}, [
		['Zackary Cavaco', 'Blue'],
		['Shon Hodermarsky', 'Green'],
		['Jude Nachtrieb', 'Green'],
		['Najarian', 'Blue'],
		['Oswaldo Lefeld', 'Blue'],
		['Vannessa Kopatz', 'Orange'],
		['Marcellus Hoga', 'Orange'],
		['Violette Connerty', 'Orange'],
		['Lucina Jeanquart', 'Blue'],
		['Mose Maslonka', 'Green'],
		['Emmie Dezayas', 'Green'],
		['Douglass Glaubke', 'Green'],
		['Deeann Delilli', 'Blue'],
		['Janett Cooch', 'Orange'],
		['Ike Collozo', 'Orange'],
		['Tamala Pecatoste', 'Orange'],
		['Shakira Cottillion', 'Blue'],
		['Colopy', 'Blue'],
		['Vivan Noggles', 'Green'],
		['Shawnda Hamalak', 'Blue'],
	])

	def init(self):
		# this initialization method is called when the module process is created
		pass

	def colors(self, request):
		"""Returns a list of all existing colors."""
		MODULE.info('MODULEID.colors: options: %s' % str(request.options))
		allColors = set(map(lambda x: x['color'], Instance.entries))
		allColors = map(lambda x: {'id': x, 'label': x}, allColors)
		allColors.append({'id': 'None', 'label': _('All colors')})
		MODULE.info('MODULEID.colors: result: %s' % str(allColors))
		self.finished(request.id, allColors)

	def query(self, request):
		"""Searches for entries in a dummy list

		requests.options = {}
		'name' -- search pattern for name (default: '')
		'color' -- color to match, 'None' for all colors (default: 'None')

		return: [ { 'id' : <unique identifier>, 'name' : <display name>, 'color' : <name of favorite color> }, ... ]
		"""
		MODULE.info('MODULEID.query: options: %s' % str(request.options))
		color = request.options.get('color', 'None')
		pattern = request.options.get('name', '')
		result = filter(lambda x: (color == 'None' or color == x['color']) and x['name'].find(pattern) >= 0, Instance.entries)
		MODULE.info('MODULEID.query: results: %s' % str(result))
		self.finished(request.id, result)

	@sanitize(StringSanitizer())
	def get(self, request):
		"""Returns the objects for the given IDs

		requests.options = [ <ID>, ... ]

		return: [ { 'id' : <unique identifier>, 'name' : <display name>, 'color' : <name of favorite color> }, ... ]
		"""
		MODULE.info('MODULEID.get: options: %s' % str(request.options))
		ids = set(request.options)
		result = filter(lambda x: x['id'] in ids, Instance.entries)
		MODULE.info('MODULEID.get: results: %s' % str(result))
		self.finished(request.id, result)
