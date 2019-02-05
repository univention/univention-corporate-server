#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages system services
#
# Copyright 2011-2019 Univention GmbH
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

from univention.management.console.base import Base
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer

from univention.admindiary.backend import query, get, translate


class Instance(Base):
	def _format_entry(self, entry):
		message = entry['message']
		if entry['event_name'] != 'COMMENT':
			message = translate(entry['event_name'], self.locale.locale)
		try:
			message = message.format(*entry['args'])
		except (AttributeError, IndexError, KeyError):
			if entry['args']:
				message = '%s (%s)' % (message, ', '.join(entry['args']))
		res_entry = {
			'id': entry['id'],
			'date': entry['timestamp'],
			'event': entry['event_name'],
			'source': entry['hostname'],
			'author': entry['username'],
			'context_id': entry['context_id'],
			'message': message,
			'tags': entry['tags'],
		}
		if 'amendments' in entry:
			res_entry['amendments'] = entry['amendments']
		return res_entry

	@simple_response
	def get(self, context_id):
		result = []
		entries = get(context_id)
		for entry in entries:
			res_entry = self._format_entry(entry)
			result.append(res_entry)
		return sorted(result, key=lambda x: x['id'])

	@sanitize(pattern=PatternSanitizer(default='.*'))
	@simple_response
	def query(self, pattern):
		result = []
		entries = query()
		for entry in entries:
			res_entry = self._format_entry(entry)
			result.append(res_entry)
		return sorted(result, key=lambda x: x['date'])
