# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import
import os
import sys
if not hasattr(sys, 'argv'):
	# prevent AttributeError: 'module' object has no attribute 'argv'
	# in maybe_patch_concurrency(argv=sys.argv,..) from importing celery.shared_task
	sys.argv = [s for s in open('/proc/self/cmdline', 'rb').read().split('\0') if s]
import json
import time
from collections import namedtuple
from celery.utils.log import get_task_logger
try:
	from typing import Any, Callable, Dict, List, Optional, Union
	import logging
	import pylibmc
except ImportError:
	pass


MEMCACHED_SOCKET = '/var/lib/univention-directory-listener/memcached.socket'
MEMCACHED_DATA_FILE = '/var/lib/univention-directory-listener/memcached_data.json'
__MEMCACHED_KEYS = {
	'user_lock': '__user_lock_{name}_{key}',
	'shared_var': 'shared_var_{name}_{key}',
}
TASK_TYPE_CLEAN = 'CLEAN'
TASK_TYPE_HANDLER = 'HANDLER'
TASK_TYPE_INITILIZE = 'INITIALIZE'
TASK_TYPE_PRE_RUN = 'PRE_RUN'
TASK_TYPE_POST_RUN = 'POST_RUN'
TASK_TYPE_QUIT = 'QUIT'


def get_mc_key(lock_type, lm_name, key):
	return __MEMCACHED_KEYS[lock_type].format(
		name=lm_name,
		key=key
	)


class MemcachedLock(object):
	"""
	Context manager that implements a lock using memcached.

	with MemcachedLock(memcached_client, 'lm_name', 'key'):
		# critical section
	"""
	logger = get_task_logger('univention.listener.async.listener_task')

	def __init__(self, client, lm_name, key, timeout=60, sleep_duration=0.05):
		self._client = client
		self.key = get_mc_key('user_lock', lm_name, key=key)
		self.timeout = timeout
		self.sleep_duration = sleep_duration

	def __enter__(self):
		while True:
			added = self._client.add(self.key, os.getpid(), self.timeout)
			if added:
				break
			time.sleep(self.sleep_duration)

	def __exit__(self, exc_type, exc_value, traceback):
		value = self._client.get(self.key)
		if value == os.getpid():
			self._client.delete(self.key)
		else:
			self.logger.error(
				'Lost lock %r! Operation took longer than %r seconds. Increase timeout.',
				self.key, self.timeout
			)


class MemcachedPersistence(object):
	filename = MEMCACHED_DATA_FILE


class MemcachedVariable(object):
	_var_type = 'var'
	_serialize_func = str
	_deserialize_func = str

	def __init__(self, client, lm_name, var_name, serialize_func=None, deserialize_func=None):
		self._client = client
		self.lm_name = lm_name
		self.var_name = var_name
		self._serialize_func = serialize_func or self._serialize_func
		self._deserialize_func = deserialize_func or self._deserialize_func

	def __repr__(self):
		return '{}({}/{}): {!r})'.format(self.__class__.__name__, self.lm_name, self.var_name, self.get())

	@property
	def key(self):
		return '__{0._var_type}_{0.lm_name}_{0.var_name}'.format(self)

	def get(self):
		res = self._client.get(self.key)
		return self._deserialize_func(res) if res is not None else None

	def append(self, value):
		"""Atomic memcached operation, no need for a lock."""
		value = self.serialize(value)
		appended = self._client.append(self.key, value)
		if not appended:
			self._client.set(self.key, value)

	def prepend(self, value):
		"""Atomic memcached operation, no need for a lock."""
		value = self.serialize(value)
		prepended = self._client.prepend(self.key, value)
		if not prepended:
			self._client.set(self.key, value)

	def set(self, value):
		"""Atomic memcached operation, no need for a lock."""
		self._client.set(self.key, self.serialize(value))
	
	def drop(self):
		"""Atomic memcached operation, no need for a lock."""
		self._client.delete(self.key)

	def remove(self, value):
		"""Not an atomic operation - lock needed!"""
		old_value = self.serialize()
		new_value = old_value.replace(self.serialize(value), '')
		self.set(new_value)

	def serialize(self, value=None):
		if value is None:
			value = self.get()
		return self._serialize_func(value) if self._serialize_func else value

	def lock(self):
		return MemcachedLock(self._client, self.lm_name, self.key)


class MemcachedQueue(MemcachedVariable):
	_var_type = 'queue'
	delimiter = '|'

	def get(self):
		return [s for s in (self._client.get(self.key) or '').split(self.delimiter) if s]

	def append(self, value):
		"""Atomic memcached operation, no need for a lock."""
		value = self.serialize(value)
		appended = self._client.append(self.key, '{!s}{!s}'.format(self.delimiter, value))
		if not appended:
			self._client.set(self.key, value)

	def prepend(self, value):
		"""Atomic memcached operation, no need for a lock."""
		value = self.serialize(value)
		prepended = self._client.prepend(self.key, '{!s}{!s}'.format(value, self.delimiter))
		if not prepended:
			self._client.set(self.key, value)

	def remove(self, value):
		"""Not an atomic operation - lock needed!"""
		cur_values = self.get()
		while value in cur_values:
			cur_values.remove(value)
		self.set(self.delimiter.join(self.serialize(v) for v in cur_values))

	def serialize(self, value=None):
		if value is None:
			return self.delimiter.join(self.serialize(v) for v in self.get())
		else:
			return super(MemcachedQueue, self).serialize(value)


QueuedTask = namedtuple('QueuedTask', ['type', 'id', 'entry_uuid'])
QueuedTask.delimiter = '.'
QueuedTask.__str__ = lambda self: '{0.type}{0.delimiter}{0.id}{0.delimiter}{0.entry_uuid}'.format(self)
QueuedTask.__eq__ = lambda self, o: self.id == o.id


class TasksQueue(MemcachedQueue):
	_var_type = 'tasks_queue'

	def get(self):
		q = super(TasksQueue, self).get()
		return [QueuedTask(*s.split('.')) for s in q]


class ListenerJob(object):
	_var_type = 'listener_job'

	def __init__(self, client, lm_name, lm_func_type, lm_func, job_id, **kwargs):
		assert lm_func_type in (
			TASK_TYPE_CLEAN, TASK_TYPE_HANDLER, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN,
			TASK_TYPE_QUIT
		)
		if lm_func_type == TASK_TYPE_HANDLER:
			assert 'dn' in kwargs
			assert 'old' in kwargs or 'new' in kwargs

		self._client = client
		self.lm_name = lm_name
		self.lm_func_type = lm_func_type
		self.lm_func = lm_func
		self.job_id = job_id
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __repr__(self):
		return '{}({})'.format(
			self.__class__.__name__,
			', '.join('{!r}={!r}'.format(k, v) for k, v in self.__dict__.items() if not k.startswith('_'))
		)

	def as_json(self):
		return json.dumps(dict((k, v) for k, v in self.__dict__.items() if not k.startswith('_')))

	@property
	def key(self):
		return self._get_key(self.lm_name, self.job_id)

	@classmethod
	def _get_key(cls, lm_name, job_id):
		return '__{}_{}_{}'.format(cls._var_type, lm_name, job_id)

	def store(self):
		"""Atomic memcached operation, no need for a lock."""
		self._client.set(self.key, self.as_json())

	def drop(self):
		"""Atomic memcached operation, no need for a lock."""
		self._client.delete(self._get_key(self.lm_name, self.job_id))

	@classmethod
	def drop_static(cls, client, lm_name, job_id):
		"""Atomic memcached operation, no need for a lock."""
		client.delete(cls._get_key(lm_name, job_id))

	@classmethod
	def from_memcache(cls, client, lm_name, job_id):
		lj_json = client.get(cls._get_key(lm_name, job_id))
		lj = json.loads(lj_json)
		assert lj['lm_name'] == lm_name and lj['job_id'] == job_id, 'Loaded ListenerJob has bad data: {!r}'.format(lj)
		return cls(client, lj.pop('lm_name'), lj.pop('lm_func_type'), lj.pop('lm_func'), lj.pop('job_id'), **lj)


def load_ldap_credentials(client, lm_name):
	try:
		return MemcachedVariable(
			client,
			lm_name,
			'ldap_credentials',
			serialize_func=json.dumps,
			deserialize_func=json.loads
		).get()
	except TypeError:
		return None


def store_ldap_credentials(client, lm_name, ldap_credentials):
	MemcachedVariable(
		client,
		lm_name,
		'ldap_credentials',
		serialize_func=json.dumps,
		deserialize_func=json.loads
	).set(ldap_credentials)
