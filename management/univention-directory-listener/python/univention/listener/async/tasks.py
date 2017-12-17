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
if not hasattr(sys, 'argv'):
	# prevent AttributeError: 'module' object has no attribute 'argv'
	# in maybe_patch_concurrency(argv=sys.argv,..) from importing celery.shared_task
	sys.argv = [s for s in open('/proc/self/cmdline', 'rb').read().split('\0') if s]
import time
from celery import shared_task
from celery.signals import after_setup_task_logger
from univention.listener.async.listener_task import ListenerTask
from univention.listener.async.memcached import (
	ListenerJob, MemcachedVariable, MemcachedQueue, TasksQueue,
	TASK_TYPE_CLEAN, TASK_TYPE_HANDLER, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN, TASK_TYPE_QUIT
)
from univention.listener.async.utils import entry_uuid_var_name


listener_uid = pwd.getpwnam('listener').pw_uid
adm_gid = grp.getgrnam('adm').gr_gid


@after_setup_task_logger.connect
def after_setup_task_logger_handler(sender=None, headers=None, body=None, **kwargs):
	logfile = kwargs.get('logfile')
	if logfile:
		os.chown(logfile, listener_uid, adm_gid)
		os.chmod(logfile, 0o640)


@shared_task(base=ListenerTask, bind=True)
def async_listener_job(self, filename, name):
	self.logger.info('*** Starting to observe task queue (task.id: %r, PID: %r, PPID: %r)...', self.request.id, os.getpid(), os.getppid())
	while True:
		found_job = True
		handler_wait_for = None
		euuid_var = None
		tasks_queue = TasksQueue(self._memcache, name, 'TasksQueue')
		tasks_taken = MemcachedQueue(self._memcache, name, 'TasksTaken')
		with tasks_queue.lock():
			for task in tasks_queue.get():
				if task.type == TASK_TYPE_QUIT:
					# make sure to release lock on TasksQueue before exiting
					break
				elif task.type in (TASK_TYPE_CLEAN, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN):
					# if a handler task is chosen, and one of these task types is before it, wait for the last one encountered
					handler_wait_for = task

				if task.id in tasks_taken.get():
					# task is taken by another worker
					continue

				if task.type in (TASK_TYPE_CLEAN, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN):
					# run job
					break
				elif task.type == TASK_TYPE_HANDLER:
					euuid_var = MemcachedVariable(self._memcache, name, entry_uuid_var_name(task.entry_uuid))
					if euuid_var.get():
						# another worker is already working on a job with the same entryUUID, skip job to preserve
						# per-LDAP-object order
						continue
					else:
						# lock entryUUID to prevent another worker to work on the same LDAP object
						euuid_var.set(task.id)
						# run job
						break
				else:
					raise RuntimeError('Unknown task type. task={!r}'.format(task))
			else:
				# no 'break' happened: either the queue is empty or there is no task this worker can work on atm
				# leave TasksQueue lock, so other workers or the listener can acquire it while we sleep
				found_job = False
			if found_job:
				# we have a job, lock it
				if task.type != TASK_TYPE_QUIT:
					tasks_taken.append(task.id)

		if not found_job:
			# sleep outside TasksQueue lock
			time.sleep(1)
			continue
		if task.type == TASK_TYPE_QUIT:
			self.logger.info('Found QUIT job, exiting (PID=%r).', os.getpid())
			return
		if task.type in (TASK_TYPE_CLEAN, TASK_TYPE_INITILIZE, TASK_TYPE_PRE_RUN, TASK_TYPE_POST_RUN):
			# wait until it's our turn
			while tasks_queue.get()[0] != task:
				time.sleep(0.1)
		elif task.type == TASK_TYPE_HANDLER and handler_wait_for:
			# wait for other task types to finish before running
			while handler_wait_for in tasks_queue.get():
				time.sleep(0.1)
		listener_job = ListenerJob.from_memcache(self._memcache, name, task.id)
		# run the users LM code
		try:
			self.run_listener_job(listener_job, self.get_lm_instance(filename, name))
		except Exception:
			# User wrote no custom error handler.
			# run_listener_job() has already logged the traceback.
			pass
		finally:
			# remove task from queues
			with tasks_queue.lock():
				tasks_queue.remove(task)
				tasks_taken.remove(task.id)
				listener_job.drop()
				if task.type == TASK_TYPE_HANDLER:
					euuid_var.drop()
