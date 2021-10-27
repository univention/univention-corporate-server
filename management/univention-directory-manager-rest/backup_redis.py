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

#import multiprocessing

#manager = multiprocessing.Manager()

#shared_memory_dict = manager.dict()  # does only work with asyncio

import pickle

try:
	from collections.abc import MutableMapping
except ImportError:
	from collections import MutableMapping

import redis

shared_memory_dict = dict
__all_instances = []


class shared_memory_dict2(MutableMapping):
	"""redis dictionary - all keys are bytes, all string values are bytes"""

	def __init__(self, *args, **kwargs):
		self.metadata = {}
		self.conn = redis.Redis('localhost')
		super(shared_memory_dict2, self).update(*args, **kwargs)

	def _fetch(self):
		return self.conn.hgetall(id(self))

	def _fetch_decoded(self):
		d = self._fetch()
		return dict(
			(self._decode(key), self._decode_value(key, value))
			for key, value in d.items()
		)

	def _decode_value(self, key, value):
		key = self._decode(key)
		value = self._decode(value)
		t = self.metadata.get(key, str)
		return t(value)

	def _decode(self, value):
		if isinstance(value, bytes):
			return value.decode("UTF-8")
		return value

	def _push(self, d):
		if not d:
			self.conn.delete(id(self))
			return
		self.conn.hmset(id(self), d)

	def __getitem__(self, key):
		d = self._fetch()
		return self._decode_value(key, d[key.encode("UTF-8")])

	def __setitem__(self, key, value):
		d = self._fetch()
		d[key.encode("UTF-8")] = value
		self._push(d)
		self.metadata[key] = type(value)

	def __delitem__(self, key):
		d = self._fetch()
		d.__delitem__(key.encode("UTF-8"))
		self.conn.hdel(id(self), key)
		self.metadata.pop(key, None)

	def __iter__(self):
		return self._fetch_decoded().__iter__()

	def __len__(self):
		return self.conn.hlen(id(self))

	def __del__(self):
		self.clear()


class shared_memory_dict3(MutableMapping):

	def __init__(self, *args, **kwargs):
		self.conn = redis.StrictRedis('localhost')
		super(shared_memory_dict, self).update(*args, **kwargs)

	def _fetch(self):
		x = self.conn.get(id(self))
		if x is None:
			return {}
		return pickle.loads(x)

	def _push(self, d):
		self.conn.set(id(self), pickle.dumps(d))

	def __getitem__(self, key):
		d = self._fetch()
		return d[key]

	def __setitem__(self, key, value):
		d = self._fetch()  # lock?
		d[key] = value
		self._push(d)

	def __delitem__(self, key):
		d = self._fetch()
		d.__delitem__(key)
		self._push(d)

	def __iter__(self):
		return self._fetch().__iter__()

	def __len__(self):
		return len(self._fetch())

	def __del__(self):
		self.clear()
