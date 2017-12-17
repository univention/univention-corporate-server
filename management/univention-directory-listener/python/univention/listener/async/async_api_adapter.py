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
import sys
import inspect
import pylibmc
from kombu.utils import uuid
from univention.listener import ListenerModuleAdapter
from univention.listener.async.utils import encode_dict
from univention.listener.async.memcached import (
	store_ldap_credentials, MEMCACHED_SOCKET, ListenerJob, MemcachedLock, QueuedTask, TasksQueue,
	TASK_TYPE_CLEAN, TASK_TYPE_HANDLER, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN
)


class AsyncListenerModuleAdapter(ListenerModuleAdapter):
	"""
	Adapter to convert the univention.listener.listener_module interface to
	the existing listener module interface.
	This is the version for for *asynchronous* listener modules.
	It is really a proxy which forwards requests to celery workers.

	Use in a classic listener module like this:
	globals().update(AsyncListenerModuleAdapter(MyListenerModuleConfiguration()).get_globals())
	"""
	_support_async = True

	def __init__(self, module_configuration, *args, **kwargs):
		"""
		:param module_configuration: ListenerModuleConfiguration object
		"""
		super(AsyncListenerModuleAdapter, self).__init__(module_configuration, *args, **kwargs)
		self.lm_name = self.config.get_name()
		self.logger = self.config.logger
		self.lm_path = inspect.getsourcefile(self.config.get_listener_module_class())
		self._listener_ldap_cred = dict()
		self._memcache = pylibmc.Client([MEMCACHED_SOCKET], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})
		self.task_queue = TasksQueue(self._memcache, self.lm_name, 'TasksQueue')

	def _setdata(self, key, value):
		self._listener_ldap_cred.setdefault(self.lm_name, {})[key] = value
		if all(a in self._listener_ldap_cred[self.lm_name] for a in ('basedn', 'binddn', 'bindpw', 'ldapserver')):
			self.logger.debug('Saving LDAP credentials for workers...')
			store_ldap_credentials(self._memcache, self.lm_name, dict(  # convert keywords to those expected by uldap
				base=self._listener_ldap_cred[self.lm_name]['basedn'],
				binddn=self._listener_ldap_cred[self.lm_name]['binddn'],
				bindpw=self._listener_ldap_cred[self.lm_name]['bindpw'],
				host=self._listener_ldap_cred[self.lm_name]['ldapserver']
			))

	def _handler(self, dn, new, old, command):
		if command == 'r':
			self._saved_old = old
			self._saved_old_dn = dn
			self._rename = True
			self._renamed = False
			return
		elif command == 'a' and self._rename:
			old = self._saved_old

		old_encoded = encode_dict(old)
		new_encoded = encode_dict(new)
		try:
			if old and not new:
				self.logger.debug('Queueing "remove" for dn=%r len(old)=%r', dn, len(old))
				job_id = self._create_listener_job(
					TASK_TYPE_HANDLER,
					'remove',
					old['entryUUID'][0],
					dn=dn,
					old=old_encoded
				)
				self.logger.debug('remove %d job_id: %r', dn, job_id)
			elif old and new:
				if self._renamed and not self._module_handler.diff(old, new):
					# ignore second modify call after a move if no non-metadata
					# attribute changed
					self._rename = self._renamed = False
					return
				self.logger.debug(
					'Queueing "modify" to for dn=%r len(old)=%r len(new)=%r old_dn=%r',
					dn, len(old), len(new), self._saved_old_dn if self._rename else None
				)
				job_id = self._create_listener_job(
					TASK_TYPE_HANDLER,
					'modify',
					new['entryUUID'][0],
					dn=dn,
					old=old_encoded,
					new=new_encoded,
					old_dn=self._saved_old_dn if self._rename else None
				)
				self.logger.debug('modify %d job_id: %r', dn, job_id)
				self._renamed = self._rename
				self._rename = False
				self._saved_old_dn = None
			elif not old and new:
				self.logger.debug('Queueing "create" for dn=%r len(new)=%r', dn, len(new))
				job_id = self._create_listener_job(
					TASK_TYPE_HANDLER,
					'create',
					new['entryUUID'][0],
					dn=dn,
					new=new_encoded
				)
				self.logger.debug('create %d job_id: %r', dn, job_id)
		except Exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			self._module_handler.error_handler(dn, old, new, command, exc_type, exc_value, exc_traceback)

	def _lazy_initialize(self):
		self.logger.debug('Queueing "initialize"...')
		job_id = self._create_listener_job(
			TASK_TYPE_INITILIZE,
			'initialize',
			None
		)
		self.logger.debug('initialize job_id: %r', job_id)

	def _lazy_clean(self):
		self.logger.debug('Queueing "clean"...')
		job_id = self._create_listener_job(
			TASK_TYPE_CLEAN,
			'clean',
			None
		)
		self.logger.debug('clean job_id: %r', job_id)

	def _lazy_pre_run(self):
		self.logger.debug('Queueing "pre_run"...')
		job_id = self._create_listener_job(
			TASK_TYPE_PRE_RUN,
			'pre_run',
			None
		)
		self.logger.debug('pre_run job_id: %r', job_id)

	def _lazy_post_run(self):
		self.logger.debug('Queueing "post_run"...')
		job_id = self._create_listener_job(
			TASK_TYPE_POST_RUN,
			'post_run',
			None
		)
		self.logger.debug('initialize post_run: %r', job_id)

	def _create_listener_job(self, task_type, lm_func, entry_uuid, prepend=False, **kwargs):
		job_id = uuid()
		ListenerJob(
			self._memcache,
			self.lm_name,
			task_type,
			lm_func,
			job_id,
			**kwargs
		).store()
		qt = QueuedTask(task_type, job_id, entry_uuid)
		with MemcachedLock(self._memcache, self.lm_name, 'TasksQueue'):
			if prepend:
				self.task_queue.prepend(qt)
			else:
				self.task_queue.append(qt)
		return job_id
