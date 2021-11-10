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

from contextlib import contextmanager
import os
from pwd import getpwnam

import lmdb
from ldap import explode_dn

from univention.uldap import getMachineConnection

DB_DIRECTORY = '/usr/share/univention-group-membership-cache'


class LmdbCaches(object):
	def __init__(self, db_directory=DB_DIRECTORY):
		self.env = lmdb.open(db_directory, 2 ** 32 - 1, max_dbs=128)
		self._fix_permissions(db_directory)
		self._caches = {}

	def _fix_permissions(self, db_directory):
		listener_uid = getpwnam('listener').pw_uid
		os.chown(os.path.join(db_directory, 'data.mdb'), listener_uid, -1)
		os.chown(os.path.join(db_directory, 'lock.mdb'), listener_uid, -1)

	def add_cache_class(self, cache_class):
		return self.add_cache(cache_class, cache_class.__name__, cache_class.single_value)

	def add_cache(self, cache_class, name, single_value):
		sub_db = self.env.open_db(name, dupsort=not single_value)
		cache = cache_class(self.env, sub_db)
		self._caches[name] = cache
		return cache

	def add_full_shard(self, shard_class):
		try:
			single_value = shard_class.single_value
		except AttributeError:
			single_value = False
		cache = self.add_cache(LdapCache, shard_class.__name__, single_value)
		cache.single_value = single_value
		cache.add_shard(shard_class)
		return cache

	def recreate(self, class_names=None):
		if class_names is None:
			class_names = sorted(self._caches)
		queries = {}
		for name, cache in self._caches.items():
			if name not in class_names:
				continue
			cache.clear()
			for shard in cache.shards:
				queries.setdefault(shard.ldap_filter, ([], set()))
				caches, attrs = queries[shard.ldap_filter]
				caches.append(shard)
				attrs.add(shard.key)
				attrs.add(shard.value)
				attrs.update(shard.attributes)
		for query, (caches, attrs) in queries.items():
			attrs.discard('dn')
			for obj in self.query_objects(query, attrs):
				for shard in caches:
					shard.add_object(obj)

	def query_objects(self, query, attrs):
		print('Querying', query, 'getting', attrs)
		lo = getMachineConnection()
		return lo.search(query, attr=attrs)

	def get_cache(self, name):
		return self._caches[name]

	def get_caches_for_query(self, query):
		return [cache for cache in self._caches if cache.ldap_filter == query]


class LdapCache(object):
	single_value = False

	def __init__(self, env, sub_db):
		self.env = env
		self.sub_db = sub_db
		self.shards = []

	@contextmanager
	def writing_transaction(self, txn=None):
		if txn is not None:
			yield txn
		else:
			with self.env.begin(self.sub_db, write=True) as txn:
				yield txn

	def save(self, key, values):
		with self.writing_transaction() as txn:
			self.delete(key, txn)
			for value in values:
				txn.put(key, value)

	def clear(self):
		with self.env.begin(write=True) as txn:
			txn.drop(self.sub_db, delete=False)

	def delete(self, key, txn=None):
		with self.writing_transaction(txn) as txn:
			txn.delete(key)

	@contextmanager
	def reading_cursor(self):
		with self.env.begin(self.sub_db) as txn:
			with txn.cursor() as cursor:
				yield cursor


	def __iter__(self):
		with self.reading_cursor() as cursor:
			for key, value in cursor:
				yield key, value

	def get(self, key):
		with self.reading_cursor() as cursor:
			if self.single_value:
				return cursor.get(key)
			else:
				cursor.set_key(key)
				return list(cursor.iternext_dup())

	def load(self):
		ret = {}
		with self.load_key_translations() as translations:
			with self.reading_cursor() as cursor:
				for key in cursor.iternext_nodup():
					translated = translations.get(key)
					if translated is None:
						continue
					ret[translated] = self.get(key)
		return ret

	@contextmanager
	def load_key_translations(self):
		with self.env.begin(caches.get_cache('EntryUUID').sub_db) as txn:
			yield txn

	def add_shard(self, shard_class):
		self.shards.append(shard_class(self))


class Shard(object):
	key = 'entryUUID'
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


class LowerValuesShard(Shard):
	def get_values(self, obj):
		values = super(LowerValuesShard, self).get_values(obj)
		return [value.lower() for value in values]


class EntryUUIDShard(LowerValuesShard):
	value = 'dn'


class UserEntryUUIDShard(EntryUUIDShard):
	ldap_filter = '(univentionObjectType=users/user)'


class GroupEntryUUIDShard(EntryUUIDShard):
	ldap_filter = '(univentionObjectType=groups/group)'


class EntryUUID(LdapCache):
	single_value = True

	def load_key_translation(self):
		pass

	def translate_key(self, key):
		return key

class UsersInGroup(LowerValuesShard):
	ldap_filter = '(univentionObjectType=groups/group)'
	value = 'uniqueMember'
	attributes = ['memberUid']

	def get_values(self, obj):
		values = super(UsersInGroup, self).get_values(obj)
		uids = set([uid.lower() for uid in obj[1].get('memberUid', [])])
		return [value for value in values if explode_dn(value, 1)[0] in uids]


class GroupsInGroup(UsersInGroup):
	def get_values(self, obj):
		ret = []
		values = super(UsersInGroup, self).get_values(obj)
		uids = set([uid.lower() for uid in obj[1].get('memberUid', [])])
		for value in values:
			rdn = explode_dn(value, 1)[0]
			if rdn in uids:
				continue
			if '%s$' % rdn in uids:
				continue
			ret.append(value)
		return ret


#class UserAzureConnections(Shard):
#	single_value = True
#	ldap_filter = '(univentionObjectType=users/user)'
#	value = 'univentionOffice365ADConnectionAlias'
#	attributes = ['univentionOffice365Enabled']
#
#	def get_values(self, obj):
#		if obj[1].get('univentionOffice365Enabled', [b'0'])[0] == b'0':
#			return []
#		return super(UserAzureConnections, self).get_values(obj)


caches = LmdbCaches()
cache0 = caches.add_cache_class(EntryUUID)
cache0.add_shard(UserEntryUUIDShard)
cache0.add_shard(GroupEntryUUIDShard)
cache1 = caches.add_full_shard(UsersInGroup)
cache2 = caches.add_full_shard(GroupsInGroup)
#cache3 = caches.add_full_shard(UserAzureConnections)


def dn_to_entry_uuid(dn):
	cache = caches.get_cache('EntryUUID')
	dn = dn.lower()
	for key, value in self:
		if value == dn:
			return key


def entry_uuid_to_dn(entry_uuid):
	cache = caches.get_cache('EntryUUID')
	return cache.get(entry_uuid)
