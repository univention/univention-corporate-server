#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#  Package management (info/install/progress...)
#
# Copyright 2012 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

import sys
import os
import time
import locale
from contextlib import contextmanager
import apt_pkg
import apt
import apt.progress
from apt.cache import FetchFailedException, LockFailedException

apt_pkg.init()

from univention.lib.locking import get_lock, release_lock
from univention.lib.i18n import Translation
_ = Translation('univention-lib').translate

class LockError(Exception):
	'''Lock error for the package manager.
	Not to be confused with LockFailedException (apt)
	'''
	pass

class ProgressState(object):
	def __init__(self, info_handler, step_handler, error_handler, handle_only_frontend_errors):
		self.info_handler = info_handler
		self.step_handler = step_handler
		self.error_handler = error_handler
		self.handle_only_frontend_errors = handle_only_frontend_errors
		self.hard_reset()

	def reset(self):
		self._info = None
		self._percentage = None

	def hard_reset(self):
		self.reset()
		self._start_steps = 0
		self._errors = []

	def info(self, info):
		self._info = info
		if self.info_handler:
			self.info_handler(info)

	def percentage(self, percentage):
		self._percentage = percentage
		if percentage is not None:
			if self.step_handler:
				self.step_handler(self._steps)

	def error(self, error, frontend=True):
		if frontend:
			self.info(error)
			self._errors.append(error)
		else:
			if self.handle_only_frontend_errors:
				return
		if self.error_handler:
			self.error_handler(error)

	def add_start_steps(self, steps):
		self._start_steps += steps

	@property
	def _steps(self):
		if self._percentage is not None:
			return self._start_steps + self._percentage

	def poll(self):
		result = {
			'info': self._info,
			'steps': self._steps,
			'errors': self._errors,
		}
		self.reset()
		return result

class MessageWriter(object):
	'''Mimics a file object (default: stdout)
	supports flush and write. Writes no '\\r',
	writes no empty strings, writes not just spaces.
	If it writes its tweaking output: '__MSG__:%s\\n' '''

	def __init__(self, progress_state):
		self.progress_state = progress_state

	def flush(self):
		pass

	def write(self, msg):
		msg = msg.replace('\r', '').strip()
		if msg:
			self.progress_state.info(msg)

class FetchProgress(apt.progress.text.AcquireProgress):
	'''Used to handle information about fetching packages.
	Writes a lot of __MSG__es, as it uses MessageWriter
	'''
	def __init__(self, outfile=None):
		super(FetchProgress, self).__init__()
		self._file = MessageWriter(outfile)

	# dont use _winch
	def start(self):
		super(apt.progress.text.AcquireProgress, self).start()
		import signal
		self._signal = signal.SIG_IGN

	# force defaults
	def _write(self, msg, newline=True, maximize=True):
		super(FetchProgress, self)._write(msg, newline=False, maximize=False)

class DpkgProgress(apt.progress.base.InstallProgress):
	'''Progress when installing or removing software.
	Writes messages (and percentage) from apts status file descriptor
	'''
	def __init__(self, progress_state):
		super(DpkgProgress, self).__init__()
		self.progress_state = progress_state

	# status == pmstatus
	def status_change(self, pkg, percent, status):
		self.progress_state.info(status)
		self.progress_state.percentage(percent)

	# status == pmerror
	# they are probably not for frontend-users
	def error(self, pkg, errormsg):
		self.progress_state.error('%s: %s' % (pkg, errormsg), frontend=False)

#	def start_update(self):
#		self.script.log('SUPDATE')
#
#	def finish_update(self):
#		self.script.log('FUPDATE')
#
#	def conffile(self, current, new):
#		self.script.log('CONFF', current, new)
#
#	def dpkg_status_change(self, pkg, status):
#		self.script.log('DPKG', pkg, status)
#
#	def processing(self, pkg, stage):
#		self.script.log('PROCESS', pkg, status)
#

class PackageManager(object):
	def __init__(self, lock=True, info_handler=None, step_handler=None, error_handler=None, handle_only_frontend_errors=False):
		self.cache = apt.Cache()
		self.progress_state = ProgressState(info_handler, step_handler, error_handler, handle_only_frontend_errors)
		self.fetch_progress = FetchProgress(self.progress_state)
		self.dpkg_progress = DpkgProgress(self.progress_state)
		self.always_install = None
		self.lock_fd = None
		if lock:
			self.lock()

	def lock(self, raise_on_fail=True):
		self.lock_fd = get_lock('univention-lib-package-manager', nonblocking=True)
		return_value = self.lock_fd is not None
		if return_value is False:
			if raise_on_fail:
				raise LockError(_('Failed to lock'))
		return return_value

	def unlock(self):
		release_lock(self.lock_fd)
		self.lock_fd = None

	def is_locked(self):
		return self.lock_fd is not None

	def __del__(self):
		# should be done automatically. i am a bit paranoid
		self.unlock()

	def _set_apt_pkg_config(self, options):
		revert_options = {}
		for option_name, option_value in options.iteritems():
			old_value = apt_pkg.config.get(option_name)
			apt_pkg.config[option_name] = option_value
			revert_options[option_name] = old_value
		return revert_options

	def add_hundred_percent(self):
		self.progress_state.add_start_steps(100)
		self.progress_state.percentage(0)

	def poll(self, timeout):
		SLEEP_TIME = 0.2
		n = timeout / SLEEP_TIME
		while n:
			status = self.progress_state.poll()
			for k, v in status.iteritems():
				if k != 'errors' and v is not None:
					break
			else:
				time.sleep(SLEEP_TIME)
				n -= 1
				continue
			return status
		return {'timeout': True}

	@contextmanager
	def brutal_noninteractive(self):
		with self.noninteractive():
			options = {
					'DPkg::Options::': '--force-overwrite',
					'DPkg::Options::': '--force-overwrite-dir',
					'APT::Get::Trivial-Only': 'no',
					'quiet': '1',
			}
			revert_options = self._set_apt_pkg_config(options)
			try:
				yield
			finally:
				self._set_apt_pkg_config(revert_options)

	@contextmanager
	def noninteractive(self):
		# dont ever ask for user input
		old_debian_frontend = os.environ.get('DEBIAN_FRONTEND')
		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
		options = {
				'APT::Get::Assume-Yes': 'true',
				'APT::Get::force-yes': 'true',
				'APT::Get::AllowUnauthenticated': '1',
				'DPkg::Options::': '--force-confold',
		}
		revert_options = self._set_apt_pkg_config(options)
		try:
			yield
		finally:
			self._set_apt_pkg_config(revert_options)
			if old_debian_frontend:
				os.environ['DEBIAN_FRONTEND'] = old_debian_frontend
			else:
				del os.environ['DEBIAN_FRONTEND']

	def update(self):
		'''apt-get update
		Returns success
		'''
		try:
			self.cache.update(self.fetch_progress)
		except FetchFailedException:
			self.progress_state.error(_('Fetch failed'))
			return False
		except LockFailedException:
			self.progress_state.error(_('Failed to lock'))
			return False
		else:
			return True

	def get_package(self, pkg_name):
		'''Get Package-object for package_name
		Otherwise write an error
		'''
		try:
			return self.cache[pkg_name]
		except KeyError:
			self.progress_state.error('%s: %s' % (pkg_name, _('No such package')))

	def commit(self, install=None, remove=None, msg_if_failed=''):
		'''Really commit changes (mark_install or mark_delete)
		or pass Package-objects that shall be commited.
		Never forgets to pass progress objects, may print error
		messages, always reopens cache.
		'''
		if install is None:
			install = []
		if remove is None:
			remove = []
		for pkg in install:
			pkg.mark_install()
		for pkg in remove:
			pkg.mark_delete()
		result = False
		try:
			result = self.cache.commit(fetch_progress=self.fetch_progress, install_progress=self.dpkg_progress)
			if not result:
				raise SystemError()
		except SystemError:
			if msg_if_failed:
				self.progress_state.error(msg_if_failed)
		# better do a:
		self.reopen_cache()

		return result

	def reopen_cache(self):
		'''Reopens the cache
		Has to be done when the apt database changed.
		'''
		self.cache.open()

	def autoremove(self):
		'''It seems that there is nothing like
		self.cache.autoremove
		So, we need to implement it by hand
		acts as apt-get autoremove
		'''
		for pkg_name in self.cache.keys():
			pkg = self.cache[pkg_name]
			if pkg.is_auto_removable:
				self.progress_state.info(_('Deleting unneeded %s') % pkg.name)
				pkg.mark_delete()
		if self.cache.get_changes():
			self.commit(msg_if_failed=_('Autoremove failed'))

	def install(self, *pkg_names):
		'''Instantly installs packages when found.
		works like apt-get install and apt-get upgrade'''
		pkgs = []
		for pkg_name in pkg_names:
			pkg = self.get_package(pkg_name)
			if pkg is not None:
				pkgs.append(pkg)
		self.commit(install=pkgs)
		for pkg in pkgs:
			pkg = self.cache[pkg.name] # fresh from cache
			if not pkg.is_installed:
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to install')))

	def uninstall(self, *pkg_names):
		'''Instantly deletes packages when found'''
		pkgs = []
		for pkg_name in pkg_names:
			pkg = self.get_package(pkg_name)
			if pkg is not None:
				pkgs.append(pkg)
		self.commit(install=self.always_install, remove=pkgs)
		for pkg in pkgs:
			pkg = self.cache[pkg.name] # fresh from cache
			if pkg.is_installed:
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to uninstall')))

