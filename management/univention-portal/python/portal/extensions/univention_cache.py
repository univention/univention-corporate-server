#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2020 Univention GmbH
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
#

import json
from copy import deepcopy

from univention.portal.log import get_logger
from univention.portal import Plugin

from six import with_metaclass

class Cache(with_metaclass(Plugin)):
	def __init__(self, cache_file, reloader=None):
		self._cache_file = cache_file
		self._reloader = reloader
		self._cache = {}
		self.refresh()
		self._load()

	def _load(self):
		get_logger('cache').info('loading cache file {}'.format(self._cache_file))
		try:
			with open(self._cache_file) as fd:
				self._cache = json.load(fd)
		except EnvironmentError as exc:
			get_logger('cache').warn('Error loading {}: {}'.format(self._cache, exc))

	def get(self):
		if self.refresh():
			self._load()
		return self._cache

	def refresh(self, force=False):
		if self._reloader:
			return self._reloader.refresh(force=force)


class PortalFileCache(Cache):
	def get_user_links(self):
		return deepcopy(self.get()['user_links'])

	def get_entries(self):
		return deepcopy(self.get()['entries'])

	def get_folders(self):
		return deepcopy(self.get()['folders'])

	def get_portal(self):
		return deepcopy(self.get()['portal'])

	def get_categories(self):
		return deepcopy(self.get()['categories'])

	def get_menu_links(self):
		return deepcopy(self.get()['menu_links'])


class GroupFileCache(Cache):
	pass
