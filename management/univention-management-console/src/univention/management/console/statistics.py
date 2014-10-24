# -*- coding: utf-8 -*-
#
# Univention Management Console
#  runtime statistics of the UMC server
#
# Copyright 2011-2014 Univention GmbH
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


class Counter(object):

	"""Implements a counter that counts available elements of
	any type that can be inactive."""

	def __init__(self):
		self._all = 0l
		self._active = 0l

	def new(self):
		"""Increase counter by one active element"""
		self._all += 1
		self._active += 1

	def inactive(self):
		"""Decrease counter of active elements by one"""
		self._active -= 1

	def json(self):
		"""Returns counter information in JSON compatible form"""
		return {'all': self._all, 'active': self._active}


class Statistics(object):

	"""Collects information about the connections, modules, requests and
	users processed and seen by the running UMC server instance"""
	connections = Counter()
	modules = Counter()
	requests = Counter()
	users = set()

	@staticmethod
	def json():
		"""Returns the statistics ina JSON compatible form"""
		return {
			'connections': Statistics.connections.json(),
			'modules': Statistics.modules.json(),
			'requests': Statistics.requests.json(),
			'users': list(Statistics.users)
		}

#: global :class:`Statistics` object
statistics = Statistics()
