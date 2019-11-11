# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry backend for data storage."""
#  main configuration registry classes
#
# Copyright 2004-2019 Univention GmbH
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
from __future__ import print_function
import sys
import os
import fcntl
import re
import errno
import time
from collections import MutableMapping
import six
try:
	from typing import overload, Any, Dict, IO, Iterator, List, NoReturn, Optional, Set, Tuple, Type, TypeVar, Union  # noqa F401
	from types import TracebackType  # noqa
	_VT = TypeVar('_VT')
except ImportError:
	def overload(f):
		pass

__all__ = ['StrictModeException', 'exception_occured', 'SCOPE', 'ConfigRegistry']
MYPY = False
INVALID_VALUE_CHARS = '\r\n'


class StrictModeException(Exception):
	"""Attempt to store non-UTF-8 characters in strict UTF-8 mode."""


def exception_occured(out=sys.stderr):
	# type: (IO) -> NoReturn
	"""
	Print exception message and exit.

	:param out: Output stream for message.
	"""
	print('E: your request could not be fulfilled', file=out)
	print('try `univention-config-registry --help` for more information', file=out)
	sys.exit(1)


SCOPE = ['normal', 'ldap', 'schedule', 'forced', 'custom']


if MYPY:
	MM = MutableMapping[str, str]
else:
	MM = MutableMapping


class ConfigRegistry(MM):
	"""
	Merged persistent value store.
	This is a merged view of several sub-registries.

	:param filename: File name for text database file.
	:param write_registry: The UCR level used for writing.
	"""
	NORMAL, LDAP, SCHEDULE, FORCED, CUSTOM = range(5)
	LAYER_PRIORITIES = (FORCED, SCHEDULE, LDAP, NORMAL, CUSTOM)
	PREFIX = '/etc/univention'
	BASES = {
		NORMAL: 'base.conf',
		LDAP: 'base-ldap.conf',
		SCHEDULE: 'base-schedule.conf',
		FORCED: 'base-forced.conf',
	}

	def __init__(self, filename=None, write_registry=NORMAL):
		# type: (str, int) -> None
		super(ConfigRegistry, self).__init__()
		self.file = os.getenv('UNIVENTION_BASECONF') or filename or None
		if self.file:
			self.scope = ConfigRegistry.CUSTOM
		else:
			self.scope = write_registry

		self._registry = {}  # type: Dict[int, Union[_ConfigRegistry, Dict[str, str]]]
		for reg in self.LAYER_PRIORITIES:
			if self.file and reg != ConfigRegistry.CUSTOM:
				self._registry[reg] = {}
			elif not self.file and reg == ConfigRegistry.CUSTOM:
				self._registry[reg] = {}
			else:
				self._registry[reg] = self._create_registry(reg)

	def _create_registry(self, reg):
		# type: (int) -> _ConfigRegistry
		"""
		Create internal sub registry.

		:param reg: UCR level.
		:returns: UCR instance.
		"""
		if reg == ConfigRegistry.CUSTOM:
			filename = self.file
		else:
			filename = os.path.join(ConfigRegistry.PREFIX, ConfigRegistry.BASES[reg])
		return _ConfigRegistry(filename=filename)

	def load(self):
		# type: () -> None
		"""Load registry from file."""
		for reg in self._registry.values():
			if isinstance(reg, _ConfigRegistry):
				reg.load()

		if six.PY3:
			return  # Python 3 uses Unicode internally and uses UTF-8 for serialization; no need to check it.

		strict = self.is_true('ucr/encoding/strict')
		for reg in self._registry.values():
			if isinstance(reg, _ConfigRegistry):
				reg.strict_encoding = strict

	def save(self):
		# type: () -> None
		"""Save registry to file."""
		registry = self._registry[self.scope]
		if isinstance(registry, _ConfigRegistry):
			registry.save()

	def lock(self):
		# type: () -> None
		"""Lock registry file."""
		registry = self._registry[self.scope]
		if isinstance(registry, _ConfigRegistry):
			registry.lock()

	def unlock(self):
		# type: () -> None
		"""Un-lock registry file."""
		registry = self._registry[self.scope]
		if isinstance(registry, _ConfigRegistry):
			registry.unlock()

	def __enter__(self):
		# type: () -> ConfigRegistry
		"""
		Lock Config Registry for read-modify-write cycle.

		:returns: The locked registry.

		> with ConfigRegistry() as ucr:
		>   ucr['key'] = 'value'
		"""
		self.lock()
		self.load()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		"""
		Unlock registry.
		"""
		if exc_type is None:
			self.save()
		self.unlock()

	def __delitem__(self, key):
		# type: (str) -> None
		"""
		Delete registry key.

		:param key: UCR variable name.
		"""
		registry = self._registry[self.scope]
		del registry[key]

	def __getitem__(self, key):  # type: ignore
		# type: (str) -> Optional[str]
		"""
		Return registry value.

		:param key: UCR variable name.
		:returns: the value or `None`.

		Bug #28276: ucr[key] returns None instead of raising KeyError - it would break many UCR templates!
		"""
		return self.get(key)

	def __setitem__(self, key, value):
		# type: (str, str) -> None
		"""
		Set registry value.

		:param key: UCR variable name.
		:param value: UCR variable value.
		"""
		registry = self._registry[self.scope]
		registry[key] = value

	def __contains__(self, key):  # type: ignore
		# type: (str) -> bool
		"""
		Check if registry key is set.

		:param key: UCR variable name.
		:returns: `True` is set, `False` otherwise.
		"""
		for reg in self.LAYER_PRIORITIES:
			registry = self._registry[reg]
			if key in registry:
				return True
		return False

	def __iter__(self):
		# type: () -> Iterator[str]
		"""
		Iterate over all registry keys.

		:returns: Iterator over all UCR variable names.
		"""
		merge = self._merge()
		for key in merge:
			yield key

	def __len__(self):
		# type: () -> int
		"""
		Return length.

		:returns: Number of UCR variables set.
		"""
		merge = self._merge()
		return len(merge)

	@overload  # type: ignore
	def get(self, key):
		# type: (str) -> Optional[str]
		pass

	@overload  # noqa F811
	def get(self, key, default):
		# type: (str, _VT) -> Union[str, _VT]
		pass

	@overload  # noqa F811
	def get(self, key, default, getscope):
		# type: (str, _VT, bool) -> Tuple[int, Union[None, str, _VT]]
		pass

	def get(self, key, default=None, getscope=False):  # noqa F811
		# type: (str, _VT, bool) -> Union[None, str, _VT, Tuple[int, Union[None, str, _VT]]]
		"""
		Return registry value (including optional scope).

		:param key: UCR variable name.
		:param default: Default value when the UCR variable is not set.
		:param getscope: `True` makes the method return the scope level in addition to the value itself.
		:returns: the value or a 2-tuple (level, value) or the default.
		"""
		for reg in self.LAYER_PRIORITIES:
			try:
				registry = self._registry[reg]
				value = registry[key]  # type: str
			except KeyError:
				continue
			return (reg, value) if getscope else value
		return default

	def has_key(self, key, write_registry_only=False):
		# type: (str, bool) -> bool
		"""
		Check if registry key is set.

		.. deprecated:: 3.1
			Use `in`.
		"""
		if write_registry_only:
			registry = self._registry[self.scope]
			return key in registry
		else:
			return key in self

	@overload
	def _merge(self):
		# type: () -> Dict[str, str]
		pass

	@overload  # noqa F811
	def _merge(self, getscope):
		# type: (bool) -> Dict[str, Tuple[int, str]]
		pass

	def _merge(self, getscope=False):  # noqa F811
		# type: (bool) -> Union[Dict[str, str], Dict[str, Tuple[int, str]]]
		"""
		Merge sub registry.

		:param getscope: `True` makes the method return the scope level in addition to the value itself.
		:returns: A mapping from varibal ename to eiter the value (if `getscope` is False) or a 2-tuple (level, value).
		"""
		merge = {}  # type: Dict[str, Union[str, Tuple[int, str]]]
		for reg in self.LAYER_PRIORITIES:
			registry = self._registry[reg]
			if not isinstance(registry, _ConfigRegistry):
				continue
			for key, value in registry.items():
				if key not in merge:
					merge[key] = (reg, value) if getscope else value

		return merge  # type: ignore

	@overload  # type: ignore
	def items(self):
		# type: () -> Dict[str, str]
		pass

	@overload  # noqa F811
	def items(self, getscope):
		# type: (bool) -> Dict[str, Tuple[int, str]]
		pass

	def items(self, getscope=False):  # noqa F811
		# type: (bool) -> Union[Dict[str, str], Dict[str, Tuple[int, str]]]
		"""
		Return all registry entries a 2-tuple (key, value) or (key, (scope, value)) if getscope is True.

		:param getscope: `True` makes the method return the scope level in addition to the value itself.
		:returns: A mapping from varibal ename to eiter the value (if `getscope` is False) or a 2-tuple (level, value).
		"""
		merge = self._merge(getscope=getscope)
		return merge.items()  # type: ignore

	def __str__(self):
		# type: () -> str
		"""Return registry content as string."""
		merge = self._merge()
		return '\n'.join(['%s: %s' % (key, val) for key, val in merge.items()])

	@overload
	def is_true(self, key):
		# type: (str) -> bool
		pass

	@overload  # noqa F811
	def is_true(self, key, default):
		# type: (str, bool) -> bool
		pass

	@overload  # noqa F811
	def is_true(self, key, default, value):
		# type: (str, bool, Optional[str]) -> bool
		pass

	def is_true(self, key=None, default=False, value=None):  # noqa F811
		# type: (str, bool, Optional[str]) -> bool
		"""
		Return if the strings value of key is considered as true.

		:param key: UCR variable name.
		:param default: Default value to return, if UCR variable is not set.
		:param value: text string to directly evaulate instead of looking up the key.
		:returns: `True` when the value is one of `yes`, `true`, `1`, `enable`, `enabled`, `on`.

		>>> ucr = ConfigRegistry()
		>>> ucr['key'] = 'yes'
		>>> ucr.is_true('key')
		True
		>>> ucr.is_true('other')
		False
		>>> ucr.is_true('other', True)
		True
		>>> ucr.is_true(value='1')
		True
		"""
		if value is None:
			value = self.get(key)  # type: ignore
			if value is None:
				return default
		return value.lower() in ('yes', 'true', '1', 'enable', 'enabled', 'on')

	@overload
	def is_false(self, key):
		# type: (str) -> bool
		pass

	@overload  # noqa F811
	def is_false(self, key, default):
		# type: (str, bool) -> bool
		pass

	@overload  # noqa F811
	def is_false(self, key=None, default=False, value=None):
		# type: (str, bool, Optional[str]) -> bool
		pass

	def is_false(self, key=None, default=False, value=None):  # noqa F811
		# type: (str, bool, Optional[str]) -> bool
		"""
		Return if the strings value of key is considered as false.

		:param key: UCR variable name.
		:param default: Default value to return, if UCR variable is not set.
		:param value: text string to directly evaulate instead of looking up the key.
		:returns: `True` when the value is one of `no`, `false`, `0`, `disable`, `disabled`, `off`.

		>>> ucr = ConfigRegistry()
		>>> ucr['key'] = 'no'
		>>> ucr.is_false('key')
		True
		>>> ucr.is_false('other')
		False
		>>> ucr.is_false('other', True)
		True
		>>> ucr.is_false(value='0')
		True
		"""
		if value is None:
			value = self.get(key)  # type: ignore
			if value is None:
				return default
		return value.lower() in ('no', 'false', '0', 'disable', 'disabled', 'off')

	def update(self, changes):  # type: ignore
		# type: (Dict[str, Optional[str]]) -> Dict[str, Tuple[Optional[str], Optional[str]]]
		"""
		Set or unset the given config registry variables.

		:param changes: dictionary of ucr-variable-name: value-or-None.
		:returns: A mapping from UCR variable name to a 2-tuple (old-value, new-value)
		"""
		registry = self._registry[self.scope]
		changed = {}
		for key, value in changes.items():
			old_value = registry.get(key, None)
			if value is None:
				try:
					del registry[key]
				except KeyError:
					continue
			else:
				registry[key] = value
			new_value = registry.get(key, value)
			changed[key] = (old_value, new_value)
		return changed

	def setdefault(self, key, default):  # type: ignore
		# type: (str, str) -> str
		"""
		Set value for variable only when not yet set.

		:param key: UCR variable name.
		:param default: UCR variable value.
		:returns: The old value, if the variable was not yet set, otherwise the new value.
		"""
		# Bug #28276: setdefault() required KeyError
		value = self.get(key, default=self)
		if value is self:
			value = self[key] = default

		return value  # type: ignore


class _ConfigRegistry(dict):
	"""
	Persistent value store.
	This is a single value store using a text file.

	:param filename: File name for text database file.
	"""

	def __init__(self, filename=None):
		# type: (str) -> None
		dict.__init__(self)
		if filename:
			self.file = filename
		else:
			self.file = '/etc/univention/base.conf'
		self.__create_base_conf()
		self.backup_file = self.file + '.bak'
		self.lock_filename = self.file + '.lock'
		# will be set by <ConfigRegistry> for each <_ConfigRegistry> - <True>
		# means the backend files are valid UTF-8 and should stay that way -->
		# only accept valid UTF-8
		self.strict_encoding = False
		self.lock_file = None  # type: Optional[IO]

	def load(self):
		# type: () -> None
		"""Load sub registry from file."""
		import_failed = False
		try:
			reg_file = open(self.file, 'r')
		except EnvironmentError:
			import_failed = True
		else:
			import_failed = reg_file.readline() == '' and reg_file.readline() == ''

		if import_failed:
			try:
				reg_file = open(self.backup_file, 'r')
			except EnvironmentError:
				return

		reg_file.seek(0)
		new = {}
		for line in reg_file:
			line = re.sub(r'^[^:]*#.*$', "", line)
			if line == '':
				continue
			if line.find(': ') == -1:
				continue

			key, value = line.split(': ', 1)
			new[key] = value.strip()
		reg_file.close()

		self.update(new)
		for key in set(self.keys()) - set(new.keys()):
			self.pop(key, None)

		if import_failed:
			self.__save_file(self.file)

	def __create_base_conf(self):
		# type: () -> None
		"""Create sub registry file."""
		try:
			reg_file = os.open(self.file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
			os.close(reg_file)
		except EnvironmentError as ex:
			if ex.errno != errno.EEXIST:
				msg = "E: file '%s' does not exist and could not be created"
				print(msg % (self.file,), file=sys.stderr)
				exception_occured()

	def __save_file(self, filename):
		# type: (str) -> None
		"""
		Save sub registry to file.

		:param filename: File name for saving.
		:raises EnvironmentError: on fatal errors.
		"""
		temp_filename = '%s.temp' % filename
		try:
			try:
				file_stat = os.stat(filename)
				mode = file_stat.st_mode
				user = file_stat.st_uid
				group = file_stat.st_gid
			except EnvironmentError:
				mode = 0o0644
				user = 0
				group = 0
			# open temporary file for writing
			reg_file = open(temp_filename, 'w')
			# write data to file
			reg_file.write('# univention_ base.conf\n\n')
			reg_file.write(self.__str__())
			# flush (meta)data
			reg_file.flush()
			os.fsync(reg_file.fileno())
			# close fd
			reg_file.close()
			try:
				os.chmod(temp_filename, mode)
				os.chown(temp_filename, user, group)
				os.rename(temp_filename, filename)
			except OSError as ex:
				if ex.errno == errno.EBUSY:
					with open(filename, 'w+') as fd:
						fd.write(open(temp_filename, 'r').read())
					os.unlink(temp_filename)
				else:
					# In this case the temp file created above in this
					# function was already moved by a concurrent UCR
					# operation. Dump the current state to a backup file
					temp_filename = '%s.concurrent_%s' % (filename, time.time())
					reg_file = open(temp_filename, 'w')
					reg_file.write('# univention_ base.conf\n\n')
					reg_file.write(self.__str__())
					reg_file.close()
		except EnvironmentError as ex:
			# suppress certain errors
			if ex.errno != errno.EACCES:
				raise

	def save(self):
		# type: () -> None
		"""Save sub registry to file."""
		for filename in (self.backup_file, self.file):
			self.__save_file(filename)

	def lock(self):
		# type: () -> None
		"""Lock sub registry file."""
		self.lock_file = open(self.lock_filename, "a+")
		fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

	def unlock(self):
		# type: () -> None
		"""Un-lock sub registry file."""
		assert self.lock_file
		self.lock_file.close()

	def __setitem__(self, key, value):
		"""
		Set value in sub registry.

		:param key: UCR variable name.
		:param value: UCR variable value.
		"""
		if self.strict_encoding:
			try:
				key.decode('UTF-8')  # only accept valid UTF-8 encoded bytes
			except UnicodeError:
				raise StrictModeException('variable name is not UTF-8 encoded')
			try:
				value.decode('UTF-8')  # only accept valid UTF-8 encoded bytes
			except UnicodeError:
				raise StrictModeException('value is not UTF-8 encoded')
		return dict.__setitem__(self, key, value)

	@staticmethod
	def remove_invalid_chars(seq):
		# type: (str) -> str
		"""
		Remove non-UTF-8 characters from value.

		:param seq: Text string.
		:returns: Text string with invalid characters removed.
		"""
		for letter in INVALID_VALUE_CHARS:
			seq = seq.replace(letter, '')
		return seq

	def __str__(self):
		# type: () -> str
		"""Return sub registry content as string."""
		return '\n'.join(['%s: %s' % (key, self.remove_invalid_chars(val)) for key, val in sorted(self.items())])

# vim:set sw=4 ts=4 noet:
