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

from univention.management.console import Translation
from univention.management.console.base import Base
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer

from univention.admindiary.backend import query

_ = Translation('univention-management-console-module-admindiary').translate


class Instance(Base):
	@sanitize(pattern=PatternSanitizer(default='.*'))
	@simple_response
	def query(self, pattern):
		result = {}
		entries = query()
		for entry in entries:
			if entry['context_id'] in result:
				result[entry['context_id']]['amendments'] = True
			else:
				try:
					message = entry['message'] % tuple(entry['args'])
				except TypeError:
					if entry['args']:
						message = '%s (%s)' % (entry['message'], ', '.join(entry['args']))
					else:
						message = entry['message']
				res_entry = {
						'date': entry['timestamp'],
						'message': message,
						'amendments': False,
				}
				result[entry['context_id']] = res_entry
		return sorted(result.values(), key=lambda x: x['date'])
