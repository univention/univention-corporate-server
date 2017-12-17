# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  PEP 484 type hints stub file
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
import types
import logging
from collections import namedtuple
from typing import Any, Callable, Dict, List, Optional, Type, Union
import pylibmc


MEMCACHED_SOCKET = '/var/lib/univention-directory-listener/memcached.socket'
MEMCACHED_DATA_FILE = '/var/lib/univention-directory-listener/memcached_data.json'
__MEMCACHED_KEYS = {
	'user_lock': '__user_lock_{name}_{key}',
	'shared_var': 'shared_var_{name}_{key}',
}  # type: Dict[str, str]
TASK_TYPE_CLEAN = 'CLEAN'
TASK_TYPE_HANDLER = 'HANDLER'
TASK_TYPE_INITILIZE = 'INITIALIZE'
TASK_TYPE_PRE_RUN = 'PRE_RUN'
TASK_TYPE_POST_RUN = 'POST_RUN'
TASK_TYPE_QUIT = 'QUIT'

def get_mc_key(lock_type: str, lm_name: str, key: str) -> str:
	...

class MemcachedLock(object):
	logger = None  # type: logging.Logger

	def __init__(
			self,
			client: pylibmc.client.Client,
			lm_name: str,
			key: str,
			timeout: int = 60,
			sleep_duration: float = 0.05
	) -> None:
		self._client = client
		self.key = get_mc_key('user_lock', lm_name, key=key)
		self.timeout = timeout
		self.sleep_duration = sleep_duration
		...
	def __enter__(self) -> None:
		...
	def __exit__(self, exc_type: Type[BaseException], exc_value: BaseException, traceback: types.TracebackType) -> None:
		...

class MemcachedPersistence(object):
	filename = MEMCACHED_DATA_FILE

class MemcachedVariable(object):
	_var_type = 'var'
	_serialize_func = str  # type: Union[Callable, Type[str]]
	_deserialize_func = str  # type: Union[Callable, Type[str]]

	def __init__(
			self,
			client: pylibmc.client.Client,
			lm_name: str,
			var_name: str,
			serialize_func: Optional[Callable] = None,
			deserialize_func: Optional[Callable] = None
	) -> None:
		self._client = client
		self.lm_name = lm_name
		self.var_name = var_name
		self._serialize_func = serialize_func or self._serialize_func
		self._deserialize_func = deserialize_func or self._deserialize_func
		...
	def __repr__(self) -> str:
		...
	@property
	def key(self) -> str:
		...
	def get(self) -> Any:
		...
	def append(self, value: str) -> None:
		...
	def prepend(self, value: str) -> None:
		...
	def set(self, value: Any) -> None:
		...
	def drop(self) -> None:
		...
	def remove(self, value: str) -> None:
		...
	def serialize(self, value: Optional[str] = None) -> str:
		...
	def lock(self) -> MemcachedLock:
		...

class MemcachedQueue(MemcachedVariable):
	_var_type = 'queue'
	delimiter = '|'
	def get(self) -> List[str]:
		...
	def append(self, value: Union[str, QueuedTask]) -> None:
		...
	def prepend(self, value: Union[str, QueuedTask]) -> None:
		...
	def remove(self, value: str) -> None:
		...
	def serialize(self, value: Optional[Union[str, QueuedTask]] = None) -> str:
		...

QueuedTask = namedtuple('QueuedTask', ['type', 'id', 'entry_uuid'])

class TasksQueue(MemcachedQueue):
	_var_type = 'tasks_queue'
	def get(self) -> List[QueuedTask]:
		...

class ListenerJob(object):
	_var_type = 'listener_job'
	def __init__(
			self,
			client: pylibmc.client.Client,
			lm_name: str,
			lm_func_type: str,
			lm_func: str,
			job_id: str,
			**kwargs: str
	) -> None:
		self._client = client
		self.lm_name = lm_name
		self.lm_func_type = lm_func_type
		self.lm_func = lm_func
		self.job_id = job_id
		...
	def __repr__(self) -> str:
		...
	def as_json(self) -> str:
		...
	@property
	def key(self) -> str:
		...
	@classmethod
	def _get_key(cls, lm_name: str, job_id: str) -> str:
		...
	def store(self) -> None:
		...
	def drop(self) -> None:
		...
	@classmethod
	def drop_static(cls, client: pylibmc.client.Client, lm_name: str, job_id: str) -> None:
		...
	@classmethod
	def from_memcache(cls, client:pylibmc.client.Client, lm_name: str, job_id: str) -> ListenerJob:
		...

def load_ldap_credentials(client: pylibmc.client.Client, lm_name: str) -> Union[Dict[str, str], None]:
	...
def store_ldap_credentials(client: pylibmc.client.Client, lm_name: str, ldap_credentials: Dict[str, str]) -> None:
	...
