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
import grp
import pwd
import sys
import inspect
import logging
import pylibmc
from celery import Task
from celery.utils.log import get_task_logger
from univention.listener.exceptions import ListenerModuleRuntimeError
from univention.listener.handler_logging import calculate_loglevel
from univention.listener.async.utils import get_configuration_object
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.async.memcached import (
	get_mc_key, load_ldap_credentials, MemcachedLock, MEMCACHED_SOCKET, TASK_TYPE_HANDLER
)
try:
	from typing import Any, Dict, List, Union, Type
	from celery import Task
	from univention.listener.async.async_handler import AsyncListenerModuleHandler
	from univention.listener.async.memcached import ListenerJob
except ImportError:
	pass


listener_uid = pwd.getpwnam('listener').pw_uid
adm_gid = grp.getgrnam('adm').gr_gid


class ListenerTask(Task):
	"""
	The Task class gets initialized in the workers main process. When it
	forks processes for concurrency they inherit its attributes. They are
	accessible in bound tasks as "self.<attr>".

	When concurrency > 1 is configured, a memcached server is used to provide
	access to data from different processes. get_shared_var() and
	set_shared_var() can be used in handler methods to read and write data.
	"""
	abstract = True
	__listener_configs = dict()  # type: Dict[str, ListenerModuleConfiguration]
	__listener_handlers = dict()  # type: Dict[str, AsyncListenerModuleHandler]
	_memcache = pylibmc.Client([MEMCACHED_SOCKET], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})  # type: pylibmc.client.Client
	_is_initialized = False
	_loglevel = None
	logger = get_task_logger(__name__)  # type: logging.Logger
	logger.setLevel(logging.INFO)

	@classmethod
	def get_lm_config_instance(cls, filename, name):  # type: (str, str) -> ListenerModuleConfiguration
		cls._set_loglevel(name)
		if name not in cls.__listener_configs:
			conf_obj = get_configuration_object(filename)
			conf_obj.logger = cls.logger
			cls.__listener_configs[name] = conf_obj
		return cls.__listener_configs[name]

	@classmethod
	def get_lm_instance(cls, filename, name):  # type: (str, str) -> AsyncListenerModuleHandler
		cls._set_loglevel(name)
		if name not in cls.__listener_handlers:
			lm_config = cls.get_lm_config_instance(filename, name)
			lm_instance = lm_config.get_listener_module_instance()
			lm_instance.logger = cls.logger
			# injecting methods into object, so it doesn't get access to the memcache client
			lm_instance.lock = lambda key, timeout=60, sleep_duration=0.05: MemcachedLock(cls._memcache, name, key, timeout, sleep_duration)
			lm_instance.get_shared_var = lambda var_name: cls._get_shared_var(name, var_name)
			lm_instance.set_shared_var = lambda var_name, var_value: cls._set_shared_var(name, var_name, var_value)
			lm_instance._get_ldap_credentials = lambda: cls._get_ldap_credentials(lm_config, name)
			cls.__listener_handlers[name] = lm_instance
			if os.geteuid() != listener_uid:
				os.seteuid(listener_uid)
		return cls.__listener_handlers[name]

	@classmethod
	def _get_shared_var(cls, name, var_name):  # type: (str, str) -> Dict[str, Any]
		return cls._memcache.get(get_mc_key('shared_var', name, key=var_name))

	@classmethod
	def _set_shared_var(cls, name, var_name, var_value):  # type: (str, str, Any) -> None
		return cls._memcache.set(get_mc_key('shared_var', name, key=var_name), var_value)

	@classmethod
	def _get_ldap_credentials(cls, lm_config, name):
		# type: (ListenerModuleConfiguration, str) -> univention.admin.uldap.access

		# When HandlerMetaClass initializes AsyncListenerModuleHandler
		# through AsyncListenerModuleAdapter it doesn't load the LDAP
		# credentials from memcache, but installs
		# AsyncListenerModuleAdapter_setdata() as setdata() in the module
		# instead, which is correct in the main listener process.
		# In the Celery process(es) the LDAP credentials must be loaded
		# from memcache through.
		ldap_creds = load_ldap_credentials(cls._memcache, name)
		if ldap_creds:
			return ldap_creds
		else:
			raise ListenerModuleRuntimeError(
				'LDAP connection of listener module {!r} has not yet been initialized in Celery task (PID: %r).'.format(
					lm_config.get_name(), os.getpid())
			)

	@classmethod
	def _set_loglevel(cls, name):
		if not cls._loglevel:
			cls._loglevel = calculate_loglevel(name)
			cls.logger.setLevel(getattr(logging, cls._loglevel))

	def run_listener_job(self, lj, lm_instance):  # type: (ListenerJob, AsyncListenerModuleHandler) -> None
		self._set_loglevel(lm_instance.config.get_name())
		func = getattr(lm_instance, lj.lm_func)
		lm_method_args = inspect.getargspec(func).args
		func_args = tuple(getattr(lj, arg) for arg in lm_method_args if arg != 'self')
		self.logger.debug(
			'Starting %s.%s()...',
			lm_instance.config.get_listener_module_class().__name__, func.__func__.__name__
		)
		try:
			res = func(*func_args)
			self.logger.debug(
				'%s.%s() returned %r.',
				lm_instance.config.get_listener_module_class().__name__, func.__func__.__name__, res
			)
		except Exception:
			# All exceptions must be caught, or the worker will exit.
			exc_type, exc_value, exc_traceback = sys.exc_info()
			self.logger.debug(
				'Exception caught for %s.%s(). %s: %s',
				lm_instance.config.get_listener_module_class().__name__, func.__func__.__name__, exc_type, exc_value
			)
			if lj.lm_func_type == TASK_TYPE_HANDLER:
				# If the user didn't write a custom error handler, the default
				# one (ListenerModuleHandler.error_handler) will log the
				# exception and reraise it.
				try:
					lm_instance.error_handler(
						lj.dn,
						getattr(lj, 'old', {}),
						getattr(lj, 'new', {}),
						lj.lm_func,
						exc_type,
						exc_value,
						exc_traceback
					)
				except Exception:
					self.logger.exception('Error handler in asynchronious handler raised an excpetion!')
					self.logger.error('Please fix the error handler.')
			else:
				self.logger.exception(
					'Exception caught for %s.%s() with arguments %r',
					lm_instance.config.get_listener_module_class().__name__, func.__func__.__name__, func_args
				)
