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

from __future__ import absolute_import
from univention.listener.handler import ListenerModuleHandler
try:
	from typing import Any, Optional, Dict, List, Type
	# from univention.listener.async.listener_task import ListenerTask
	import types.TracebackType
except ImportError:
	pass


class AsyncListenerModuleHandler(ListenerModuleHandler):
	"""
	Asynchronous listener module base class.

	When a listener module is configured with parallelism > 1 the handler code
	will run in multiple processes in parallel. To share variables between the
	processes methods are provided to easily save data to and retrieve it from
	a memcached server.
	set_shared_var() and get_shared_var() can be used to store and retrieve
	data, lock() can be used to prevent race conditions.

	All operations on the same LDAP object will be serialized: `create()`,
	`modify()` and `remove()` will never run in parallel for objects with the
	same `entryUUID` and the execution order of those functions will be
	preserved.Operations on LDAP object with different `entryUUIDs` will run in
	parallel.

	A word of *caution* about `pre_run()` and `post_run()` in asynchronous
	listener modules: If possible their use should be completely avoided. They
	will run in the expected order, but as they might be queued in between
	`create()`, `modify()`, `remove()`, it is possible for those calls to
	follow a `post_run()`. So even if a `pre_run()` will follow a `post_run()`
	before the next c/m/r call, it may not be efficient to tear down network/DB
	connections etc.

	* pre_run() is guaranteed to only run before the first create/modify/
	remove() and after a post_run().
	* post_run() is guaranteed to run as the last function.

	The error_handler() in asynchronous listener must not raise an exception
	itself!
	"""
	_support_async = True

	def lock(self, key, timeout=60, sleep_duration=0.05):
		# type: (str, Optional[int], Optional[int]) -> ListenerTask.MemcachedLock
		"""
		Context manager to lock a critical section (aka "monitor").

		with self.lock('my_var'):
			my_var = self.get_shared_var('my_var')
			# ...
			self.set_shared_var('my_var', my_var)

		:param key: str: identifier for lock
		:param timeout: int: lock will be released automatically after so many seconds
		:param sleep_duration: float: seconds to between checking the lock
		:return: None
		"""
		pass  # implemented in listener_task.ListenerTask

	def get_shared_var(self, var_name):  # type: (str) -> Any
		"""
		Retrieve a variable previously stored by set_shared_var().

		:param var_name: str: identifier for stored data
		:return: stored data or None if no data was stored before
		"""
		pass  # implemented in listener_task.ListenerTask

	def set_shared_var(self, var_name, var_value):  # type: (str, Any) -> None
		"""
		Store a variable, so other processes of the same listener module can
		retrieve it.

		:param var_name: str: identifier for stored data
		:param var_value: data to be stored
		:return: None
		"""
		pass  # implemented in listener_task.ListenerTask

	def error_handler(self, dn, old, new, command, exc_type, exc_value, exc_traceback):
		# type: (str, Dict[str, List], Dict[str, List], str, Type[BaseException], BaseException, types.TracebackType) -> None
		"""
		Will be called for unhandled exceptions in create/modify/remove.

		:param dn: str
		:param old: dict
		:param new: dict
		:param command: str
		:param exc_type: exception class
		:param exc_value: exception object
		:param exc_traceback: traceback object
		:return: None
		"""
		self.logger.exception('dn=%r command=%r', dn, command)
		raise exc_type, exc_value, exc_traceback
