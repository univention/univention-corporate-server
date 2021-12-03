#!/usr/bin/python3
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

from six.moves import dbm_gnu as gdbm

from univention.ldap_cache.cache.backend import Caches, LdapCache, Shard, _s
from univention.ldap_cache.log import log, debug


class GdbmCaches(Caches):
	def _add_sub_cache(self, name, single_value, reverse):
		db_file = os.path.join(self._directory, '%s.db' % name)
		debug('Using GDBM %s', name)
		cache = GdbmCache(name, single_value, reverse)
		cache.db_file = db_file
		self._caches[name] = cache
		return cache


class GdbmCache(LdapCache):
	def _fix_permissions(self):
		listener_uid = getpwnam('listener').pw_uid
		os.chown(self.db_file, listener_uid, -1)
		os.chmod(self.db_file, 0o640)

	@contextmanager
	def writing(self, writer=None):
		if writer is not None:
			yield writer
		else:
			if not os.path.exists(self.db_file):
				self.clear()
			writer = gdbm.open(self.db_file, 'csu')
			try:
				yield writer
			finally:
				writer.close()

	reading = writing

	def save(self, key, values):
		with self.writing() as writer:
			if self.reverse:
				for value in values:
					current = self.get(value, writer) or []
					if key in current:
						continue
					debug('%s - Adding %s %r', self.name, value, key)
					current.append(key)
					writer[value] = json.dumps(current)
			else:
				self.delete(key, values, writer)
				if not values:
					return
				debug('%s - Saving %s %r', self.name, key, values)
				if self.single_value:
					writer[key] = values[0]
				else:
					writer[key] = json.dumps(values)

	def clear(self):
		log('%s - Clearing whole DB!', self.name)
		gdbm.open(self.db_file, 'n').close()
		self._fix_permissions()

	def cleanup(self):
		log('%s - Cleaning up DB', self.name)
		with self.writing() as db:
			db.reorganize()
		self._fix_permissions()

	def delete(self, key, values, writer=None):
		debug('%s - Delete %s', self.name, key)
		with self.writing(writer) as writer:
			if self.reverse:
				for value in values:
					current = self.get(value, writer) or []
					try:
						current.remove(key)
					except ValueError:
						continue
					writer[value] = json.dumps(current)
			else:
				try:
					del writer[key]
				except KeyError:
					pass

	def __iter__(self):
		with self.reading() as reader:
			key = _s(reader.firstkey())
			while key is not None:
				yield key, self.get(key, reader)
				key = _s(reader.nextkey(key))

	def get(self, key, reader=None):
		with self.reading(reader) as reader:
			try:
				value = reader[key]
			except KeyError:
				return None
			if self.single_value:
				return _s(value)
			elif value:
				return _s(json.loads(value))

	def load(self):
		debug('%s - Loading', self.name)
		return dict(self)


class GdbmShard(Shard):
	key = 'dn'
