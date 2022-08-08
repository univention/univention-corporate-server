#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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
import os
from copy import deepcopy

from six import with_metaclass
from univention.portal import Plugin
from univention.portal.log import get_logger


class Cache(with_metaclass(Plugin)):
	"""
	Base class for Caching in general

	`get`: Gets the complete cache content.
	`refresh`: Refreshes the cache. Gets a "reason" to decide if this is
	really needed. The value "force" should be handled as if it is really
	needed.

	cache_file:
		Filename where the content is stored
	reloader:
		Class that handles the actual refresh
	"""

	def __init__(self, cache_file, reloader=None):
		self._cache_file = cache_file
		self._reloader = reloader
		self._cache = {}
		self._loaded = False

	def get_id(self):
		try:
			stat = os.stat(self._cache_file)
			return str(stat.st_mtime)
		except (EnvironmentError):
			return ""

	def _load(self):
		get_logger("cache").info("loading cache file {}".format(self._cache_file))
		try:
			with open(self._cache_file) as fd:
				self._cache = json.load(fd)
		except (EnvironmentError, ValueError):
			get_logger("cache").exception("Error loading {}".format(self._cache_file))
		else:
			self._loaded = True

	def get(self):
		if not self._loaded or self.refresh():
			self._load()
		return self._cache

	def refresh(self, reason=None):
		if self._reloader:
			return self._reloader.refresh(reason=reason, content=self._cache)


class PortalFileCache(Cache):
	"""
	Specialized cache for portal data. The implementation does not differ
	from that of a base cache, but it provides more specialized cache
	access methods that it needs in order to work with the Portal class.

	`get_user_links`
	`get_entries`
	`get_folders`
	`get_portal`
	`get_categories`
	`get_menu_links`
	"""

	def get_user_links(self):
		return deepcopy(self.get()["user_links"])

	def get_entries(self):
		return deepcopy(self.get()["entries"])

	def get_folders(self):
		return deepcopy(self.get()["folders"])

	def get_portal(self):
		return deepcopy(self.get()["portal"])

	def get_categories(self):
		return deepcopy(self.get()["categories"])

	def get_menu_links(self):
		return deepcopy(self.get()["menu_links"])


class GroupFileCache(Cache):
	"""
	Caching class for groups.
	In fact it is just the same as the normal Cache and just here in case
	we want to get smarter at some point.
	"""
