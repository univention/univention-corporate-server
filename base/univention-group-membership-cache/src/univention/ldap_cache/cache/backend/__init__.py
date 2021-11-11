#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2021 Univention GmbH
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

from univention.uldap import getMachineConnection
DB_DIRECTORY = '/usr/share/univention-group-membership-cache/caches'


from univention.ldap_cache.cache.plugins import Plugin


class Caches(object):
	__metaclass__ = Plugin

	def __init__(self, db_directory=DB_DIRECTORY):
		self._directory = db_directory
		self._caches = {}

	def get_shards_for_query(self, query):
		ret = []
		for cache in self._caches.values():
			for shard in cache.shards:
				if shard.ldap_filter == query:
					ret.append(shard)
		return ret

	def get_queries(self, cache_names=None):
		queries = {}
		for name, cache in self._caches.items():
			if cache_names is not None and name not in cache_names:
				continue
			for shard in cache.shards:
				queries.setdefault(shard.ldap_filter, ([], set()))
				caches, attrs = queries[shard.ldap_filter]
				caches.append(shard)
				attrs.add(shard.key)
				attrs.add(shard.value)
				attrs.update(shard.attributes)
		return queries

	def rebuild(self, cache_names=None):
		for name, cache in self._caches.items():
			if cache_names is None or name in cache_names:
				cache.clear()
		for query, (caches, attrs) in self.get_queries(cache_names).items():
			attrs.discard('dn')
			for obj in self._query_objects(query, attrs):
				for shard in caches:
					shard.add_object(obj)

	def _query_objects(self, query, attrs):
		lo = getMachineConnection()
		return lo.search(query, attr=attrs)

	def get_sub_cache(self, name):
		return self._caches.get(name)

	def add(self, klass):
		if not klass.ldap_filter or not klass.value:
			return
		name = klass.db_name or klass.__name__
		cache = self.get_sub_cache(name)
		if cache is None:
			cache = self.add_sub_cache(name, klass.single_value)
		cache.add_shard(klass)


class Shard(object):
	__metaclass__ = Plugin

	ldap_filter = None
	db_name = None
	single_value = False
	key = 'entryUUID'
	value = None
	attributes = []

	def __init__(self, cache):
		self._cache = cache

	def add_object(self, obj):
		try:
			key = self.get_key(obj)
		except ValueError:
			return
		values = self.get_values(obj)
		if values:
			self._cache.save(key, values)
		else:
			self._cache.delete(key)

	def _get_from_object(self, obj, attr):
		if attr == 'dn':
			return [obj[0]]
		return obj[1].get(attr, [])

	def get_values(self, obj):
		return self._get_from_object(obj, self.value)

	def get_key(self, obj):
		values = self._get_from_object(obj, self.key)
		if values:
			return values[0].lower()
		raise ValueError(self.key)


class LdapCache(object):
	__metaclass__ = Plugin

	def __init__(self, name, single_value):
		self.name = name
		self.single_value = single_value
		self.shards = []

	def add_shard(self, shard_class):
		self.shards.append(shard_class(self))
