#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#  Package management (info/install/progress...)
#
# Copyright 2012-2014 Univention GmbH
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
import re
from errno import ENOSPC, ENOENT
import subprocess
from contextlib import contextmanager
import threading
from logging import getLogger, DEBUG, Handler
from time import sleep

import apt_pkg
import apt
import apt.progress
from apt.cache import FetchFailedException, LockFailedException, ProblemResolver

apt_pkg.init()

from univention.lib.locking import get_lock, release_lock
from univention.lib.i18n import Translation
_ = Translation('univention-lib').translate

# FIXME: Requires univention-updater (but this requires univention-lib...)
# FIXME: The path to the script is hardcoded everywhere it is used.
# TODO: Solution: Put all the logic in univention-lib
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'
CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']

class LockError(Exception):
	'''Lock error for the package manager.
	Not to be confused with LockFailedException (apt)
	'''
	pass

class ProgressState(object):
	def __init__(self, parent_logger):
		self._logger = parent_logger.getChild('dpkg')
		self.hard_reset()

	def reset(self):
		self._info = None
		self._percentage = None

	def hard_reset(self):
		self.reset()
		self._start_steps = 0
		self._errors = []
		self._max_steps = 0
		self._finished = False

	def set_finished(self):
		self._finished = True

	def get_logger(self, logger_name=None):
		if logger_name is None:
			return self._logger
		return self._logger.getChild(logger_name)

	def info(self, info, logger_name=None):
		self._info = info
		self.get_logger(logger_name).info(info)

	def percentage(self, percentage, logger_name='percentage'):
		self._percentage = percentage
		if percentage is not None:
			self.get_logger(logger_name).info(percentage)

	def error(self, error, logger_name=None):
		self._errors.append(error)
		self.get_logger(logger_name).error(error)

	def add_start_steps(self, steps):
		self._start_steps += steps

	@property
	def _steps(self):
		if self._percentage is not None:
			return self._start_steps + self._percentage

	def poll(self):
		result = {
			'info' : self._info,
			'steps' : self._steps,
			'errors' : self._errors,
			'finished' : self._finished,
		}
		if self._max_steps and result['steps']:
			result['steps'] = int((result['steps'] * 100 / self._max_steps))
		self.reset()
		return result

class MessageWriter(object):
	'''Mimics a file object
	supports flush and write. Writes no '\\r',
	writes no empty strings, writes not just spaces.
	If it writes it is handled by progress_state '''

	def __init__(self, progress_state):
		self.progress_state = progress_state

	def flush(self):
		pass

	def write(self, msg):
		msg = msg.replace('\r', '').strip()
		if msg:
			self.progress_state.info(msg, logger_name='fetch')

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

	def fork(self):
		# start a new pipe
		fd_pipe_read, fd_pipe_write = os.pipe()

		# we better have a real file when using low-level routines
		# basically taken from: https://bugs.launchpad.net/jockey/+bug/280291
		p = os.fork()
		if p == 0:
			# child -> redirect stdout/stderr of dpkg to pipe
			os.dup2(fd_pipe_write, sys.stdout.fileno())
			os.dup2(fd_pipe_write, sys.stderr.fileno())

			# close unneeded pipe handles
			os.close(fd_pipe_read)
			os.close(fd_pipe_write)
		else:
			# parent -> close write handle
			os.close(fd_pipe_write)

			# wrap handle for reading end of the pipe... for convenience
			pipe_read = os.fdopen(fd_pipe_read)

			# start thread that monitors the pipes output
			self._check_pipe_thread = threading.Thread(target=self.check_pipe, args=(pipe_read,))
			self._check_pipe_thread.daemon = True
			self._check_pipe_thread.start()

		return p

	def check_pipe(self, pipe_read):
		while True:
			try:
				# read the next line
				output = pipe_read.readline()
				if not output:
					# pipe has been closed -> we are done
					break

				# we got a new line -> send to info handler
				self.progress_state.info(output.strip(), logger_name='process')
			except (OSError, IOError):
				# something unexpected happened -> break loop
				break

		# close the pipe's read end
		pipe_read.close()

	# status == pmstatus
	def status_change(self, pkg, percent, status):
		self.progress_state.info(status, logger_name='status')
		self.progress_state.percentage(percent)

	# status == pmerror
	# they are probably not for frontend-users
	def error(self, pkg, errormsg):
		self.progress_state.error('%s: %s' % (pkg, errormsg), logger_name='process')

#	def start_update(self):
#		self.log('SUPDATE')
#
#	def finish_update(self):
#		self.log('FUPDATE')
#
#	def conffile(self, current, new):
#		self.log('CONFF', current, new)
#
#	def dpkg_status_change(self, pkg, status):
#		self.log('DPKG', pkg, status)
#
#	def processing(self, pkg, stage):
#		self.log('PROCESS', pkg, stage)
#

class _PackageManagerLoggerHandler(Handler):

	def __init__(self, info_handler, step_handler, error_handler):
		super(_PackageManagerLoggerHandler, self).__init__()
		self.info_handler = info_handler
		self.step_handler = step_handler
		self.error_handler = error_handler

	def emit(self, record):
		if record.name == 'packagemanager.dpkg.percentage':
			if self.step_handler:
				self.step_handler(record.msg)
		elif record.levelname == 'ERROR':
			if self.error_handler:
				self.error_handler(record.msg)
		elif record.levelname == 'INFO':
			if self.info_handler:
				self.info_handler(record.msg)


class PackageManager(object):

	def __init__(self, lock=True, info_handler=None, step_handler=None, error_handler=None, always_noninteractive=True):
		# parent logger, public. should be extended by adding a handler
		self.logger = getLogger('packagemanager')
		self.logger.setLevel(DEBUG)
		if info_handler or step_handler or error_handler:
			handler = _PackageManagerLoggerHandler(info_handler, step_handler, error_handler)
			self.logger.addHandler(handler)

		self.cache = None
		self._open_cache()
		self.progress_state = ProgressState(self.logger)
		self.fetch_progress = FetchProgress(self.progress_state)
		self.dpkg_progress = DpkgProgress(self.progress_state)
		self._always_install = []
		self.always_noninteractive = always_noninteractive
		self.lock_fd = None
		if lock:
			self.lock()

	def always_install(self, pkgs=None, just_mark=False):
		'''Set packages that should be installed and never
		uninstalled. If you overwrite old always_install-pkgs,
		make sure to reopen_cache()
		'''
		if not just_mark:
			if pkgs is None:
				pkgs = []
			self._always_install = pkgs
		for pkg in self._always_install:
			if self.is_installed(pkg):
				pkg.mark_keep()
			else:
				pkg.mark_install()

	def lock(self, raise_on_fail=True):
		self.lock_fd = get_lock('univention-lib-package-manager', nonblocking=True)
		return_value = self.lock_fd is not None
		if return_value is False:
			if raise_on_fail:
				raise LockError(_('Failed to lock'))
		return return_value

	def unlock(self):
		if self.lock_fd is not None:
			release_lock(self.lock_fd)
			self.lock_fd = None
			return True
		return False

	def is_locked(self):
		return self.lock_fd is not None

	@contextmanager
	def locked(self, reset_status=False, set_finished=False):
		self.lock()
		if reset_status:
			self.reset_status()
		try:
			yield
		except:
			self.set_finished()
			raise
		finally:
			if set_finished:
				self.set_finished()
			self.unlock()

	def _shell_command(self, command, handle_streams=True):
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		if handle_streams:
			if out:
				self.progress_state.info(out)
			if err:
				self.progress_state.error(err)
		return out, err

	@contextmanager
	def no_umc_restart(self, exclude_apache=False):
		if exclude_apache:
			cmd_disable_exec = [CMD_DISABLE_EXEC, '--exclude-apache']
		else:
			cmd_disable_exec = CMD_DISABLE_EXEC
		self._shell_command(cmd_disable_exec)
		try:
			yield
		finally:
			self._shell_command(CMD_ENABLE_EXEC)

	def __del__(self):
		# should be done automatically. i am a bit paranoid
		if self.lock_fd is not None:
			self.unlock()

	def _set_apt_pkg_config(self, options):
		revert_options = []
		for option_name, option_value in options:
			old_value = apt_pkg.config.get(option_name)
			apt_pkg.config[option_name] = option_value
			revert_options.append((option_name, old_value))
		return revert_options

	def add_hundred_percent(self):
		self.progress_state.add_start_steps(100)
		self.progress_state.percentage(0)

	def set_max_steps(self, steps):
		self.progress_state._max_steps = steps

	def set_finished(self):
		self.progress_state.set_finished()

	def poll(self, timeout):
		return self.progress_state.poll()

	def reset_status(self):
		self.progress_state.hard_reset()

	@contextmanager
	def brutal_noninteractive(self):
		with self.noninteractive():
			options = [
				('DPkg::Options::', '--force-overwrite'),
				('DPkg::Options::', '--force-overwrite-dir'),
				('APT::Get::AllowUnauthenticated', '1'),
				('APT::Get::Trivial-Only', 'no'),
				('quiet', '1'),
			]
			revert_options = self._set_apt_pkg_config(options)
			try:
				yield
			finally:
				self._set_apt_pkg_config(revert_options)

	@contextmanager
	def noninteractive(self):
		''' dont ever ask for user input '''
		old_debian_frontend = os.environ.get('DEBIAN_FRONTEND')
		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
		options = [
			('APT::Get::Assume-Yes', 'true'),
			('APT::Get::force-yes', 'true'),
			('DPkg::Options::', '--force-confold'),
		]
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
		self.reopen_cache()
		try:
			if self.always_noninteractive:
				with self.noninteractive():
					self.cache.update(self.fetch_progress)
			else:
				self.cache.update(self.fetch_progress)
		except FetchFailedException as e:
			self.progress_state.error(_('Fetch failed (%s)') % e)
			return False
		except LockFailedException:
			self.progress_state.error(_('Failed to lock'))
			return False
		else:
			self.reopen_cache()
			return True

	def get_packages(self, pkg_names):
		'''Get many Package-objects at once
		(only those that exist, write error
		for others)
		'''
		return filter(None, map(self.get_package, pkg_names))

	def get_package(self, pkg_name, raise_key_error=False):
		'''Get Package-object for package_name
		Otherwise write an error
		'''
		if isinstance(pkg_name, apt.package.Package):
			# we already have a Package instance :)
			return pkg_name
		try:
			return self.cache[pkg_name]
		except KeyError:
			if raise_key_error:
				raise
			else:
				self.progress_state.error('%s: %s' % (pkg_name, _('No such package')))

	def is_installed(self, pkg_name, reopen=False):
		'''Returns whether a package is installed.
		Returns None if package is not found.
		'''
		if reopen:
			self.reopen_cache()
		try:
			package = self.get_package(pkg_name, raise_key_error=True)
		except KeyError:
			return None
		else:
			# Bug #31261 - apt.Package thinks unpacked but unconfigured packages are installed
			# return package.is_installed
			return package._pkg.current_state == apt_pkg.CURSTATE_INSTALLED

	def packages(self, reopen=False):
		'''Yields all packages in cache'''
		if reopen:
			self.reopen_cache()
		for pkg in self.cache:
			yield pkg

	def mark_auto(self, auto, *pkgs):
		'''Immediately sets packages to automatically
		installed (or not). Calls commit()!'''
		for pkg in self.get_packages(pkgs):
			pkg.mark_auto(auto)
		self.commit()
		self.reopen_cache()

	def mark(self, install, remove, dry_run=False):
		'''Marks packages, returns all
		installed, removed or broken packages.
		'''
		to_be_installed = set()
		to_be_removed = set()
		broken = set()
		if install is None:
			install = []
		if remove is None:
			remove = []
		# fix problems and fix them only once
		# this is necessary because we used auto_fix=False
		# auto_fix causes problems when used multiple times
		# as every auto_fix thinks this is the most important operation
		#   and does not take care of other deletes and installs
		# see below for a real-life situation
		fixer = ProblemResolver(self.cache)
		for pkg in remove:
			try:
				pkg.mark_delete(auto_fix=False)
			except SystemError:
				broken.add(pkg.name)
			else:
				fixer.clear(pkg)
				fixer.protect(pkg)
				fixer.remove(pkg)
		for pkg in install:
			try:
				pkg.mark_install(auto_fix=False)
				pkg.mark_auto(False)
			except SystemError:
				broken.add(pkg.name)
			else:
				fixer.clear(pkg)
				fixer.protect(pkg)
		fixer.install_protect()
		try:
			fixer.resolve()
		except SystemError as exc:
			self.progress_state.error(str(exc))
			for pkg in install + remove:
				broken.add(pkg.name)
		# if more than one package is to be installed and this package
		#   has an OR-dependency, the package will automatically choose
		#   the first one. but if the second OR-dependency is to be
		#   installed explicitely along with that package in the
		#   beginning, the first OR-dependency is obsolete (and all of
		#   its own dependencies). Sadly we have to remove them manually.
		# btw: this is the reason why we have to use the ProblemResolver.
		#   If OR-dependency1 conflicts with OR-dependency2 this causes
		#   problems when the original package used auto_fix=True but
		#   the second OR-dependency is to be installed explicitely.
		# see https://forge.univention.org/bugzilla/show_bug.cgi?id=30279
		package_was_garbage = True
		while package_was_garbage:
			package_was_garbage = False
			for pkg in self.cache.get_changes():
				if pkg.marked_install and pkg.is_auto_installed and pkg.is_auto_removable:
					try:
						pkg.mark_delete()
					except SystemError as exc:
						# Bug #34291
						broken.add(pkg.name)
					package_was_garbage = True
		for pkg in self.cache.get_changes():
			if pkg.marked_install or pkg.marked_upgrade:
				to_be_installed.add(pkg.name)
				if pkg in remove:
					broken.add(pkg.name)
				if apt_pkg.config.get('APT::Get::AllowUnauthenticated') != '1':
					authenticated = False
					for origin in pkg.candidate.origins:
						authenticated |= origin.trusted
					if not authenticated:
						self.progress_state.error('%s: %s' % (pkg.name, _('Untrusted origin')))
						broken.add(pkg.name)
			if pkg.marked_delete:
				to_be_removed.add(pkg.name)
				if pkg in install:
					broken.add(pkg.name)
			if pkg.is_inst_broken:
				broken.add(pkg.name)
		# some actions can change flags in other pkgs,
		# e.g. install firefox-de and firefox-en: one will
		# silently not be installed
		for pkg in remove:
			if not pkg.marked_delete:
				# maybe its already removed...
				if pkg.marked_install or self.is_installed(pkg):
					broken.add(pkg.name)
		for pkg in install:
			if not pkg.marked_install:
				# maybe its already installed...
				if pkg.marked_delete or not self.is_installed(pkg):
					broken.add(pkg.name)
		if dry_run:
			self.reopen_cache()
		return sorted(to_be_installed), sorted(to_be_removed), sorted(broken)

	def commit(self, install=None, remove=None, upgrade=False, dist_upgrade=False, msg_if_failed=''):
		'''Really commit changes (mark_install or mark_delete)
		or pass Package-objects that shall be commited.
		Never forgets to pass progress objects, may print error
		messages, always reopens cache.
		'''
		# translate package names to apt.package.Package instances
		install = self.get_packages(install or [])
		remove = self.get_packages(remove or [])

		# perform an upgrade/dist_upgrade
		if dist_upgrade:
			self.cache.upgrade(dist_upgrade=True)
		elif upgrade:
			self.cache.upgrade(dist_upgrade=False)

		# only if commit does something. if it is just called
		# to really commit changes made manually, dont dry_run
		# as it reopens the cache
		broken = []
		if install or remove:
			to_be_installed, to_be_removed, broken = self.mark(install, remove, dry_run=True)

		result = False
		try:
			if broken:
				raise SystemError()

			# perform an upgrade/dist_upgrade -> marks packages to upgrade/install
			if dist_upgrade:
				self.cache.upgrade(dist_upgrade=True)
			elif upgrade:
				self.cache.upgrade(dist_upgrade=False)

			# mark packages to install/remove
			self.mark(install, remove, dry_run=False)

			# commit marked packages
			kwargs = {'fetch_progress' : self.fetch_progress, 'install_progress' : self.dpkg_progress}
			if self.always_noninteractive:
				with self.noninteractive():
					result = self.cache.commit(**kwargs)
			else:
				result = self.cache.commit(**kwargs)
			if not result:
				raise SystemError()
		except FetchFailedException as e:
			self.progress_state.error(_('Fetch failed (%s)') % e)
			return False
		except SystemError:
			if msg_if_failed:
				self.progress_state.error(msg_if_failed)

		# better do a:
		self.reopen_cache()

		# check whether all packages have been installed
		for pkg in install:
			if not self.is_installed(pkg.name): # fresh from cache
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to install')))

		# check whether all packages have been removed
		for pkg in remove:
			if self.is_installed(pkg.name): # fresh from cache
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to uninstall')))

		return result

	def reopen_cache(self):
		'''Reopens the cache
		Has to be done when the apt database changed.
		'''
		self._open_cache()
		self.always_install(just_mark=True)

	def _open_cache(self):
		def _open():
			if self.cache is None:
				self.cache = apt.Cache()
			else:
				self.cache.open()
		for i in xrange(10):
			try:
				_open()
			except SystemError:
				sleep(0.5)
			else:
				return
		try:
			_open()
		except SystemError as exc:
			# still failing, let it raise
			self._handle_system_error(exc, *sys.exc_info())

	def _handle_system_error(self, exc, etype, evalue, etraceback):
		# All strings which must pass this function are in: https://forge.univention.org/bugzilla/attachment.cgi?id=6898
		messages = re.sub('\s([WE]:)', r'\n\1', str(exc)).splitlines()
		further = set()

		apt_update = False
		hold_package = False
		no_space_left = False
		missing_files = False
		renaming_failed = False

		message = [_('Could not initialize package manager.')]
		for msg in messages:
			if msg.startswith('W:'):
				if 'apt-get update' in msg:
					apt_update = True
					continue
			elif msg.startswith('E:'):
				if 'pkgProblemResolver::Resolve' in msg:
					hold_package = True
					continue
				match = re.search(' - (write|open|rename) \((\d+): .*\)', msg)
				if match:
					type_, errno = match.groups()
					errno = int(errno)
					if errno == ENOSPC:
						no_space_left = True
						continue
					elif errno == ENOENT and type_ == 'open':
						missing_files = True
						continue
					elif errno == ENOENT and type_ == 'rename':
						renaming_failed = True
						continue
			msg = re.sub('^W:', _('Warning: '), msg)
			msg = re.sub('^E:', _('Error: '), msg)
			msg = re.sub(',$', '.', msg)
			further.add(msg)

		if no_space_left:
			message.append(_('There is no free hard disk space left on the device.'))
		if hold_package:
			message.append(_('Some package conflicts could not be resolved. This was probably caused by packages with "hold" state.'))
		if renaming_failed or missing_files:
			message.append(_('Probably another process is currently using it or the package sources are corrupt. Please try again later.'))
			apt_update = True
		elif apt_update:
			message.append(_('The package sources are probably corrupt.'))
		if apt_update:
			message.extend([
				_('The sources.list entries could be repaired by executing the following commands as root on this server:'),
				'\n', 'ucr commit /etc/apt/sources.list.d/*; apt-get update'])
		if further:
			message.extend(['\n\n'+_('Further information regarding the error:'), '\n'+'\n'.join(further)])
		raise etype, etype(' '.join(message)), etraceback

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
				# dont auto_fix. maybe some errors magically
				# disappear if we just remove
				# enough packages...
				pkg.mark_delete(auto_fix=False)

		failed_msg = _('Autoremove failed')
		# but in the end we should test
		if self.cache.broken_count:
			self.progress_state.error(failed_msg)
		else:
			if self.cache.get_changes():
				self.commit(msg_if_failed=failed_msg)

	def upgrade(self):
		'''Instantly performs an 'apt-get upgrade'.'''
		return self.commit(upgrade=True)

	def dist_upgrade(self):
		'''Instantly performs an 'apt-get dist-upgrade'.'''
		return self.commit(dist_upgrade=True)

	def install(self, *pkg_names):
		'''Instantly installs packages when found.
		works like apt-get install and apt-get upgrade'''
		return self.commit(install=pkg_names)

	def uninstall(self, *pkg_names):
		'''Instantly deletes packages when found'''
		return self.commit(install=self._always_install, remove=pkg_names)
