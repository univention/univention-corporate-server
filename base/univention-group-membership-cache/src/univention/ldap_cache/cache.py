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

from ldap import explode_dn

from univention.ldap_cache.gdbm_cache import GdbmCaches as Caches, GdbmCache as Cache, GdbmShard as Shard
#from univention.ldap_cache.lmdb_cache import LmdbCaches as Caches, LmdbCache as Cache, LmdbShard as Shard

class LowerValuesShard(Shard):
	def get_values(self, obj):
		values = super(LowerValuesShard, self).get_values(obj)
		return [value.lower() for value in values]


class EntryUUID(Cache):
	single_value = True


class EntryUUIDShard(LowerValuesShard):
	value = 'dn'


class UserEntryUUIDShard(EntryUUIDShard):
	ldap_filter = '(univentionObjectType=users/user)'


class GroupEntryUUIDShard(EntryUUIDShard):
	ldap_filter = '(univentionObjectType=groups/group)'


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


caches = Caches()
cache0 = caches.add_cache_class(EntryUUID)
cache0.add_shard(UserEntryUUIDShard)
cache0.add_shard(GroupEntryUUIDShard)
cache1 = caches.add_full_shard(UsersInGroup)
cache2 = caches.add_full_shard(GroupsInGroup)
#cache3 = caches.add_full_shard(UserAzureConnections)
#caches.rebuild()


def dn_to_entry_uuid(dn):
	cache = caches.get_cache('EntryUUID')
	dn = dn.lower()
	for key, value in cache:
		if value == dn:
			return key


def entry_uuid_to_dn(entry_uuid):
	cache = caches.get_cache('EntryUUID')
	return cache.get(entry_uuid)
