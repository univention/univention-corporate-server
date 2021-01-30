#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Univention common Python Library for
package management (info/install/progress...)
"""
# Copyright 2012-2021 Univention GmbH
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

import logging  # noqa F401
import sys
import os
import re
import signal
from errno import ENOSPC, ENOENT
import subprocess
from contextlib import contextmanager
import threading
from logging import getLogger, DEBUG, Handler
from time import sleep
from types import TracebackType  # noqa F401
from typing import IO, Any, Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Type, Union  # noqa F401

import six

import apt_pkg
import apt
import apt.progress
from apt.cache import FetchFailedException, LockFailedException, ProblemResolver

from univention.lib.locking import get_lock, release_lock
from univention.lib.i18n import Translation

apt_pkg.init()

_ = Translation('univention-lib').translate

# FIXME: Requires univention-updater (but this requires univention-lib...)
# FIXME: The path to the script is hardcoded everywhere it is used.
# TODO: Solution: Put all the logic in univention-lib
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'
CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']


class LockError(Exception):
	"""
	Lock error for the package manager.
	Not to be confused with :py:class:`LockFailedException`
	"""


class ProgressState(object):
	"""
	Track |APT| progress and report.

	:param logging.Logger parent_logger: The Logger of the parent.
	"""
	def __init__(self, parent_logger):
		# type: (logging.Logger) -> None
		self._logger = parent_logger.getChild('dpkg')
		self.hard_reset()

	def reset(self):
		# type: () -> None
		"""
		Reset minimal progress state.
		"""
		self._info = None
		self._percentage = None  # type: Optional[float]

	def hard_reset(self):
		# type: () -> None
		"""
		Reset full progress state.
		"""
		self.reset()
		self._start_steps = 0
		self._errors = []  # type: List[str]
		self._max_steps = 0
		self._finished = False

	def set_finished(self):
		# type: () -> None
		"""
		Mark installation as finished.
		"""
		self._finished = True

	def get_logger(self, logger_name=None):
		# type: (Optional[str]) -> logging.Logger
		"""
		Return (sub-)logger.

		:param str logger_name: The optional name for the sub-logger. If not given, the shared logger of the manager is used.
		:returns: A Logger instance.
		:rtype: logging.Logger
		"""
		if logger_name is None:
			return self._logger
		return self._logger.getChild(logger_name)

	def info(self, info, logger_name=None):
		# type: (Any, Optional[str]) -> None
		"""
		Log info message.

		:param str info: The info message to log.
		:param str logger_name: The optional name for the sub-logger. If not given, the shared logger of the manager is used.
		"""
		self._info = info
		self.get_logger(logger_name).info(info)

	def percentage(self, percentage, logger_name='percentage'):
		# type: (float, str) -> None
		"""
		Update progress information.

		:param float percentage: The percentage of completeness.
		:param str logger_name: The optional name for the sub-logger. If not given, the shared logger of the manager is used.
		"""
		self._percentage = percentage
		if percentage is not None:
			self.get_logger(logger_name).info(percentage)

	def error(self, error, logger_name=None):
		# type: (Any, Optional[str]) -> None
		"""
		Log error message.

		:param str error: The error message to log.
		:param str logger_name: The optional name for the sub-logger. If not given, the shared logger of the manager is used.
		"""
		self._errors.append(error)
		self.get_logger(logger_name).error(error)

	def add_start_steps(self, steps):
		# type: (int) -> None
		"""
		Add additional planned steps.

		:param int steps: The number of additional steps to add.
		"""
		self._start_steps += steps

	@property
	def _steps(self):
		# type: () -> Optional[float]
		"""
		Return progress as step counter

		:returns: A percentage value, which might be >100%
		:rtype: float
		"""
		if self._percentage is not None:
			return self._start_steps + self._percentage

	def poll(self):
		# type: () -> Dict[str, Any]
		"""
		Return the aggregated state.
		The state is reset afterwards using :py:meth:`reset`.

		:returns: A dictionary containing the last info and error message, number of steps and finished state.
		:rtype: dict
		"""
		result = {
			'info': self._info,
			'steps': self._steps,
			'errors': self._errors,
			'finished': self._finished,
		}
		if self._max_steps and result['steps']:
			result['steps'] = int((result['steps'] * 100 / self._max_steps))
		self.reset()
		return result


class MessageWriter(object):
	"""
	Mimics a :py:func:`file` object
	supports :py:meth:`flush` and :py:meth:`write`. Writes no '\\r',
	writes no empty strings, writes not just spaces.
	If it writes it is handled by `progress_state`.

	:param ProgressState progress_state: Instance which is responsible for collecting the state.
	"""

	def __init__(self, progress_state):
		# type: (ProgressState) -> None
		self.progress_state = progress_state

	def flush(self):
		# type: () -> None
		"""
		Dummy function to flush all pending writes.
		"""
		pass

	def write(self, msg):
		# type: (Any) -> None
		"""
		Write sanitized message to the state collector.

		:param str msg: The message to write.
		"""
		msg = msg.replace('\r', '').strip()
		if msg:
			self.progress_state.info(msg, logger_name='fetch')


class FetchProgress(apt.progress.text.AcquireProgress):
	"""
	Used to handle information about fetching packages.
	Writes a lot of `__MSG__`es, as it uses :py:class:`MessageWriter`.

	:param ProgressState outfile: An instance to receive the progress information.
	"""

	def __init__(self, outfile=None):
		# type: (ProgressState) -> None
		super(FetchProgress, self).__init__()
		self._file = MessageWriter(outfile)

	# don't use _winch
	def start(self):
		# type: () -> None
		"""
		Start collection progress information.
		"""
		super(apt.progress.text.AcquireProgress, self).start()
		self._signal = signal.SIG_IGN

	# force defaults
	def _write(self, msg, newline=True, maximize=True):
		# type: (Any, bool, bool) -> None
		"""
		Write message.

		:param str msg: The message to write.
		:param bool newline: Append trailing newline.
		:param bool maximize: resize to terminal width.
		"""
		super(FetchProgress, self)._write(msg, newline=False, maximize=False)


class DpkgProgress(apt.progress.base.InstallProgress):
	"""
	Report progress when installing or removing software.
	Writes messages (and percentage) from |APT| status file descriptor
	"""

	def __init__(self, progress_state):
		# type: (ProgressState) -> None
		super(DpkgProgress, self).__init__()
		self.progress_state = progress_state

	def fork(self):
		# type: () -> int
		"""
		Fork a child process for calling |APT| and setup pipes for progress reporting.
		The parent process will also start a Thread for reading the pipe.

		:returns: The process identifier: `0` for the child, `!= 0` for the parent process.
		:rtype: int
		"""
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
		# type: (IO) -> None
		"""
		Internal function for reading the pipe and updating the progress status.

		:param file read: The pipe to read.
		"""
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
		"""
		Update installation status and progress.

		:param str pkg: The currently process package name.
		:param float percent: The progress.
		:param str status: The status message.
		"""
		self.progress_state.info(status, logger_name='status')
		self.progress_state.percentage(percent)

	# status == pmerror
	# they are probably not for frontend-users
	def error(self, pkg, errormsg):
		"""
		Report an error.

		:param str pkg: The name of the binary package currently being processed.
		:param str errormsg: An error message.
		"""
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
	"""
	Translate Python :py:mod:`logging` events to separate handlers.

	:parmm info_handler: A optional function which accepts info messages as the single argument.
	:parmm step_handler: A optional function which accepts step messages as the single argument.
	:parmm error_handler: A optional function which accepts error messages as the single argument.
	"""

	def __init__(self, info_handler, step_handler, error_handler):
		# type: (Optional[Callable[[Any], None]], Optional[Callable[[Any], None]], Optional[Callable[[Any], None]]) -> None
		super(_PackageManagerLoggerHandler, self).__init__()
		self.info_handler = info_handler
		self.step_handler = step_handler
		self.error_handler = error_handler

	def emit(self, record):
		# type: (logging.LogRecord) -> None
		"""
		Translate event to calls of |APT| handlers.
		:param logging.LogRecord event: An event.
		"""
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
	"""
	High-level package manager for |UCS|.

	:param bool lock: Get an exclusive lock to prevent other instances from running in parallel.
	:param info_handler: Some handler to handle info messages.
	:param step_handler: Some handler to handle progress messages.
	:param error_handler: Some handler to handle error messages.
	:param always_noninteractive: Run :command:`dpkg` in non-interactive mode to prevent any user input.
	"""

	def __init__(self, lock=True, info_handler=None, step_handler=None, error_handler=None, always_noninteractive=True):
		# type: (bool, Optional[Callable[[Any], None]], Optional[Callable[[Any], None]], Optional[Callable[[Any], None]], bool) -> None
		self.lock_fd = None  # type: Optional[IO]
		self.apt_lock_fd = -1  # type: int
		# parent logger, public. should be extended by adding a handler
		self.logger = getLogger('packagemanager')
		self.logger.setLevel(DEBUG)
		if info_handler or step_handler or error_handler:
			handler = _PackageManagerLoggerHandler(info_handler, step_handler, error_handler)
			self.logger.addHandler(handler)

		self.cache = None  # type: apt.cache.Cache
		self._open_cache()
		self.progress_state = ProgressState(self.logger)
		self.fetch_progress = FetchProgress(self.progress_state)
		self.dpkg_progress = DpkgProgress(self.progress_state)
		self._always_install = []  # type: List[apt.package.Package]
		self.always_noninteractive = always_noninteractive
		if lock:
			self.lock()

	def always_install(self, pkgs=None, just_mark=False):
		# type: (Optional[List[apt.package.Package]], bool) -> None
		"""
		Set packages that should be installed and never
		uninstalled. If you overwrite old `always_install`,
		make sure to call :py:meth:`reopen_cache`.

		:param list pkgs: The list of packages to .
		:param bool just_mark: if `True`, process the previously saved list of packages instead of the given new list.
		"""
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
		# type: (bool) -> bool
		"""
		Get locks to prevent concurrent calls.

		:param bool raise_on_fail: Raise :py:class:`LockError` instead of returning `False`.
		:returns: `True` if all locks were are acquired, `False` otherwise.
		:rtype: bool
		:raises LockError: if the lock cannot be acquired.
		"""
		if self.is_locked():
			return True
		self.lock_fd = get_lock('univention-lib-package-manager', nonblocking=True)
		return_value = self.lock_fd is not None

		if return_value is True:
			# get apt lock; taken from dist-packages/apt/cache.py
			lockfile = apt_pkg.config.find_dir("Dir::Cache::Archives") + "lock"
			self.apt_lock_fd = apt_pkg.get_lock(lockfile)
			if self.apt_lock_fd < 0:
				return_value = False

		if return_value is False:
			if raise_on_fail:
				raise LockError(_('Failed to lock'))

		return return_value

	def unlock(self):
		# type: () -> bool
		"""
		Release locks.

		:returns: `True` if the manager lock was taken, `False` otherwise.
		:rtype: bool
		"""
		if self.apt_lock_fd >= 0:
			os.close(self.apt_lock_fd)
			self.apt_lock_fd = -1
		if self.lock_fd is not None:
			release_lock(self.lock_fd)
			self.lock_fd = None
			return True
		return False

	def is_locked(self):
		# type: () -> bool
		"""
		Return the state of the lock.

		:returns: `True` if the lock is acquired, `False` otherwise.
		:rtype: bool
		"""
		return self.lock_fd is not None and self.apt_lock_fd >= 0

	@contextmanager
	def locked(self, reset_status=False, set_finished=False):
		"""
		Perform locking and cleanup actions before and after working with package state.

		:param bool reset_status: Cancel all pending actions.
		:param bool set_finished:  Call :py:meth:`set_finished` at the end.
		"""
		self.lock()
		if reset_status:
			self.reset_status()
		try:
			yield
		except BaseException:
			self.set_finished()
			raise
		finally:
			if set_finished:
				self.set_finished()
			self.unlock()

	def _shell_command(self, command, handle_streams=True):
		# type: (Union[str, Sequence[str]], bool) -> Tuple[str, str]
		"""
		Execute command processing and returning its output.

		:param list command: The command to execute.
		:param bool handle_streams: Pass stdout and stderr to registered progress handler.
		:returns: a 2-tuple (stdout, stderr)
		:rtype: tuple(str, str)
		"""
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
		"""
		Run package manager with restart of |UMC| (and Apache) disabled.

		:param bool exclude_apache: If `True` Apache may be restarted.
		"""
		if exclude_apache:
			cmd_disable_exec = [CMD_DISABLE_EXEC, '--exclude-apache']
		else:
			cmd_disable_exec = CMD_DISABLE_EXEC
		self._shell_command(cmd_disable_exec, False)
		try:
			yield
		finally:
			self._shell_command(CMD_ENABLE_EXEC, False)

	def __del__(self):
		# should be done automatically. i am a bit paranoid
		if self.lock_fd is not None:
			self.unlock()

	def _set_apt_pkg_config(self, options):
		# type: (Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]
		"""
		Set |APT| options.

		:param options: A list of 2-tuples (name, value)
		:type options: list[tuple[str, str]]
		:returns: A list of 2-tuples (name, old-value)
		:rtype: list[tuple[str, str]]
		"""
		revert_options = []
		for option_name, option_value in options:
			old_value = apt_pkg.config.get(option_name)
			apt_pkg.config[option_name] = option_value
			revert_options.append((option_name, old_value))
		return revert_options

	def add_hundred_percent(self):
		# type: () -> None
		"""
		Add another 100 steps.
		"""
		self.progress_state.add_start_steps(100)
		self.progress_state.percentage(0)

	def set_max_steps(self, steps):  # type (int) -> None
		"""
		Set maximum number of steps.

		:param int steps: Number of steps.
		"""
		self.progress_state._max_steps = steps

	def set_finished(self):  # type () -> None
		"""
		Signal all steps done.
		"""
		self.progress_state.set_finished()

	def poll(self, timeout):
		# type: (Any) -> Dict[str, Any]
		"""
		Poll for progress.

		:param timeout: Ignored
		:returns: A dictionary containing the last info and error message, number of steps and finished state.
		:rtype: dict
		"""
		return self.progress_state.poll()

	def reset_status(self):
		# type: () -> None
		"""
		Reset progress indicator back to start.
		"""
		self.progress_state.hard_reset()

	@contextmanager
	def brutal_noninteractive(self):
		# type: () -> Iterator
		"""
		Configure package manager to never ask for user input and to overwrite changed files
		"""
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
		# type: () -> Iterator[None]
		"""
		Configure package manager to never ask for user input.
		"""
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
		# type: () -> bool
		"""
		`apt-get update`

		:returns: `True on success, `False` otherwise.
		:rtype: bool
		"""
		self.reopen_cache()
		try:
			if self.always_noninteractive:
				with self.noninteractive():
					self.cache.update(self.fetch_progress)
			else:
				self.cache.update(self.fetch_progress)
		except FetchFailedException as exc:
			self.progress_state.error(_('Fetching failed'))
			for message in self._get_error_message(exc):
				self.progress_state.error(message)
			return False
		except LockFailedException:
			self.progress_state.error(_('Failed to lock'))
			return False
		else:
			self.reopen_cache()
			return True

	def get_packages(self, pkg_names):
		# type: (Sequence[str]) -> List[apt.package.Package]
		"""
		Get many Package-objects at once
		(only those that exist, write error for others)

		:param pkg_names: A list of binary package names.
		:returns: A list of |APT| cache entries.
		"""
		packages = [self.get_package(pkg_name) for pkg_name in pkg_names]
		return [pkg for pkg in packages if pkg]

	def get_package(self, pkg_name, raise_key_error=False):
		# type: (str, bool) -> Any
		"""
		Get Package-object for package name.

		:param str pkg_name: A binary package name.
		:param raise_key_error: Raise error when `True`, otherwise write an error message.
		:returns: The |APT| cache entry for the binary package.
		"""
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
		# type: (str, bool) -> Optional[bool]
		"""
		Returns whether a package is installed.

		:param str pkg_name: A binary package name.
		:param bool reopen: Re-open the |APT| cache before checking.
		:returns: `True` if installed, `False` if not, and `None` if package is not found.
		"""
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
		# type: (bool) -> Iterator[Any]
		"""
		Yields all packages in cache.

		:param bool reopen: Re-open the |APT| cache before returning.
		"""
		if reopen:
			self.reopen_cache()
		for pkg in self.cache:
			yield pkg

	def mark_auto(self, auto, *pkgs):
		# type: (bool, str) -> None
		"""
		Immediately sets packages to automatically installed (or not).

		:param bool auto: Mark the packages as automatically installed (`True`) or not.
		:param pkgs: A list of binary package names.

		Calls :py:meth:`commit`!
		"""
		for pkg in self.get_packages(pkgs):
			pkg.mark_auto(auto)
		self.commit()

	def mark(self, install, remove, dry_run=False):
		# type: (Optional[List[apt.package.Package]], Optional[List[apt.package.Package]], bool) -> Tuple[List[str], List[str], List[str]]
		"""
		Mark packages as automatically installed (or not).

		:param install: A list of packages to install.
		:param remove: A list of packages to remove.
		:param bool dry_run: Only simulate the action if `True`.
		:returns: A 3-tuple (to_be_installed, to_be_removed, broken), where each argument is a list of package names.
		"""
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
			for message in self._get_error_message(exc):
				self.progress_state.error(message)
			for pkg in install + remove:
				broken.add(pkg.name)
		# if more than one package is to be installed and this package
		#   has an OR-dependency, the package will automatically choose
		#   the first one. but if the second OR-dependency is to be
		#   installed explicitly along with that package in the
		#   beginning, the first OR-dependency is obsolete (and all of
		#   its own dependencies). Sadly we have to remove them manually.
		# btw: this is the reason why we have to use the ProblemResolver.
		#   If OR-dependency1 conflicts with OR-dependency2 this causes
		#   problems when the original package used auto_fix=True but
		#   the second OR-dependency is to be installed explicitly.
		# see https://forge.univention.org/bugzilla/show_bug.cgi?id=30279
		package_was_garbage = True
		while package_was_garbage:
			package_was_garbage = False
			for pkg in self.cache.get_changes():
				if pkg.marked_install and pkg.is_auto_installed and pkg.is_auto_removable:
					try:
						pkg.mark_delete()
					except SystemError:
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
		# type: (Optional[Sequence[str]], Optional[Sequence[str]], bool, bool, str) -> bool
		"""
		Really commit changes (mark_install or mark_delete)
		or pass Package-objects that shall be committed.
		Never forgets to pass progress objects, may print error
		messages, always reopens cache.

		:param install: List of package names to install.
		:param remove: List of package names to remove.
		:param upgrade: Perform upgrade were no new packages are installed.
		:param dist_upgrade: Perform upgrade were new packages may be installed and old packages may be removed.
		:param msg_if_failed: Test message to output if things go wrong.
		:returns: `True` on success, `False` otherwise.
		"""
		# translate package names to apt.package.Package instances
		install = self.get_packages(install or [])
		remove = self.get_packages(remove or [])

		# perform an upgrade/dist_upgrade
		if dist_upgrade:
			self.cache.upgrade(dist_upgrade=True)
		elif upgrade:
			self.cache.upgrade(dist_upgrade=False)

		# only if commit does something. if it is just called
		# to really commit changes made manually, don't dry_run
		# as it reopens the cache
		broken = []  # type: List[str]
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
			kwargs = {'fetch_progress': self.fetch_progress, 'install_progress': self.dpkg_progress}
			if self.always_noninteractive:
				with self.noninteractive():
					result = self.cache.commit(**kwargs)
			else:
				result = self.cache.commit(**kwargs)
			if not result:
				raise SystemError()
		except FetchFailedException as exc:
			self.progress_state.error(_('Fetching failed'))
			for message in self._get_error_message(exc):
				self.progress_state.error(message)
			return False
		except SystemError:
			if msg_if_failed:
				self.progress_state.error(msg_if_failed)

		# better do a:
		self.reopen_cache()

		# check whether all packages have been installed
		for pkg in install:
			if not self.is_installed(pkg.name):  # fresh from cache
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to install')))

		# check whether all packages have been removed
		for pkg in remove:
			if self.is_installed(pkg.name):  # fresh from cache
				self.progress_state.error('%s: %s' % (pkg.name, _('Failed to uninstall')))

		return result

	def reopen_cache(self):
		# type: () -> None
		"""
		Reopen the |APT| cache.

		Has to be done when the |APT| database changed.
		"""
		self._open_cache()
		self.always_install(just_mark=True)

	def _open_cache(self):
		# type: () -> None
		"""
		Internal function to (re-)open the |APT| cache.
		"""
		def _open():
			if self.cache is None:
				self.cache = apt.Cache()
			else:
				self.cache.open()
		for i in range(10):
			try:
				_open()
			except SystemError:
				sleep(0.5)
			else:
				return
		try:
			_open()
		except SystemError:
			# still failing, let it raise
			self._handle_system_error(*sys.exc_info())

	def _handle_system_error(self, etype, exc, etraceback):
		# type: (Type[BaseException], BaseException, TracebackType) -> None
		"""
		Log exception from opening |APT| cache.

		:param type etype: Exception type.
		:param BaseException exc: Exception instance.
		:param etraceback: Exception traceback.
		"""
		message = '%s %s' % (_('Could not initialize package manager.'), '\n'.join(self._get_error_message(exc)))
		six.reraise(etype, etype(message), etraceback)

	def _get_error_message(self, exc):
		# type: (BaseException) -> List[str]
		"""
		Parse exception message and return standardized messages for user consumption.

		:param BaseException exc: An exception instance.
		:returns: A list of translated messages.

		All strings which must pass this function are in: <https://forge.univention.org/bugzilla/attachment.cgi?id=6898>
		"""
		messages = re.sub(r'\s([WE]:)', r'\n\1', str(exc)).splitlines()
		further = set()  # type: Set[str]

		apt_update = False
		hold_package = False
		no_space_left = False
		missing_files = False
		renaming_failed = False

		message = []
		for msg in messages:
			if msg.startswith('W:'):
				if 'apt-get update' in msg:
					apt_update = True
					continue
			elif msg.startswith('E:'):
				if 'pkgProblemResolver::Resolve' in msg:
					hold_package = True
					continue
				match = re.search(r' - (write|open|rename) \((\d+): .*\)', msg)
				if match:
					type_, errno_ = match.groups()
					errno = int(errno_)
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
			if not msg.endswith('.'):
				msg = '%s.' % msg
			further.add(msg)
		further.discard('')
		further.discard('.')

		if no_space_left:
			message.append(_('There is no free hard disk space left on the device.'))
		if hold_package:
			message.append(_('Some package conflicts could not be resolved. This was probably caused by packages with "hold" state.'))
		if renaming_failed or missing_files:
			# i18n: "using it" refers to the "package manager"
			message.append(_('Probably another process is currently using it or the package sources are corrupt. Please try again later.'))
			apt_update = True
		elif apt_update:
			message.append(_('The package sources are probably corrupt.'))
		if apt_update:
			message.extend([
				_('The sources.list entries could be repaired by executing the following commands as root on this server:'),
				'ucr commit /etc/apt/sources.list.d/*; apt-get update'])
		if further:
			further_ = list(further)
			message.append('\n%s\n%s' % (_('Further information regarding this error:'), further_[0]))
			message.extend(further_[1:])
		return message

	def autoremove(self):
		# type: () -> Optional[bool]
		"""
		Remove all packages which are no longer required.

		It seems that there is nothing like `self.cache.autoremove`.
		"""
		for pkg in self.cache:
			if pkg.is_auto_removable:
				self.progress_state.info(_('Deleting unneeded %s') % pkg.name)
				# don't auto_fix. maybe some errors magically
				# disappear if we just remove
				# enough packages...
				pkg.mark_delete(auto_fix=False)

		failed_msg = _('Autoremove failed')
		# but in the end we should test
		if self.cache.broken_count:
			self.progress_state.error(failed_msg)
			return False
		else:
			if self.cache.get_changes():
				return self.commit(msg_if_failed=failed_msg)

	def upgrade(self):
		# type: () -> bool
		"""
		Instantly performs an `apt-get upgrade`.

		:returns: `True` on success, `False` otherwise.
		"""
		return self.commit(upgrade=True)

	def dist_upgrade(self):
		# type: () -> bool
		"""
		Instantly performs an `apt-get dist-upgrade`.

		:returns: `True` on success, `False` otherwise.
		"""
		return self.commit(dist_upgrade=True)

	def install(self, *pkg_names):
		# type: (str) -> bool
		"""
		Instantly installs packages when found.
		Works like `apt-get install` and `apt-get upgrade`.

		:param pkg_names: A list of binary package names to install.
		:returns: `True` on success, `False` otherwise.
		"""
		return self.commit(install=pkg_names)

	def uninstall(self, *pkg_names):
		# type: (str) -> bool
		"""
		Instantly deletes packages when found.

		:param pkg_names: A list of binary package names to remove.
		:returns: `True` on success, `False` otherwise.
		"""
		return self.commit(install=self._always_install, remove=pkg_names)
