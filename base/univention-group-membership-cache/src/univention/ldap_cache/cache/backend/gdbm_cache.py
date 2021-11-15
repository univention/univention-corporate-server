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
import os
from pwd import getpwnam
from contextlib import contextmanager
import json

import gdbm

from univention.ldap_cache.cache.backend import Caches, LdapCache, Shard
from univention.ldap_cache.log import log, debug


class GdbmCaches(Caches):
	def add_sub_cache(self, name, single_value):
		db_file = os.path.join(self._directory, '%s.db' % name)
		debug('Using GDBM %s', name)
		cache = GdbmCache(name, single_value)
		cache.db_file = db_file
		self._caches[name] = cache
		return cache


class GdbmCache(LdapCache):
	def _fix_permissions(self):
		listener_uid = getpwnam('listener').pw_uid
		os.chown(self.db_file, listener_uid, -1)

	@contextmanager
	def writing(self, writer=None):
		if writer is not None:
			yield writer
		else:
			writer = gdbm.open(self.db_file, 'csu')
			self._fix_permissions()
			try:
				yield writer
			finally:
				writer.close()

	reading = writing

	def save(self, key, values):
		with self.writing() as writer:
			self.delete(key, writer)
			if not values:
				return
			debug('%s - Saving %s %r', self.name, key, values)
			if self.single_value:
				writer[key] = values[0]
			else:
				writer[key] = json.dumps(values)

	def clear(self):
		log('%s - Clearing whole DB!', self.name)
		db = gdbm.open(self.db_file, 'n')
		self._fix_permissions()
		db.close()

	def delete(self, key, writer=None):
		debug('%s - Delete %s', self.name, key)
		with self.writing(writer) as writer:
			try:
				del writer[key]
			except KeyError:
				pass

	def __iter__(self):
		with self.reading() as reader:
			key = reader.firstkey()
			while key is not None:
				yield key, self.get(key, reader)
				key = reader.nextkey(key)

	def get(self, key, reader=None):
		with self.reading(reader) as reader:
			try:
				value = reader[key]
			except KeyError:
				return None
			if self.single_value:
				return value
			elif value:
				return json.loads(value)

	def load(self):
		debug('%s - Loading', self.name)
		return dict(self)


class GdbmShard(Shard):
	key = 'dn'
