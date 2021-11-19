# -*- coding: utf-8 -*-
#
#  main configuration registry classes
#
# Copyright 2004-2021 Univention GmbH
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

"""Univention Configuration Registry backend for data storage."""

from __future__ import print_function

import sys
import os
import fcntl
import re
import errno
import time
from enum import IntEnum
from stat import S_ISREG
try:
	from collections.abc import Mapping, MutableMapping  # Python 3.3+
except ImportError:
	from collections import Mapping, MutableMapping

import six

from univention.config_registry.handler import run_filter

if six.PY2:
	from io import open
try:
	from typing import overload, Any, Dict, IO, Iterator, List, ItemsView, NoReturn, Optional, Set, Tuple, Type, TypeVar, Union  # noqa F401
	from types import TracebackType  # noqa F401
	from typing_extension import Literal  # noqa F401
	_T = TypeVar('_T', bound='ReadOnlyConfigRegistry')
	_VT = TypeVar('_VT')
except ImportError:  # pragma: no cover
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
	print(u'E: your request could not be fulfilled', file=out)
	print(u'try `univention-config-registry --help` for more information', file=out)
	sys.exit(1)


SCOPE = ['normal', 'ldap', 'schedule', 'forced', 'custom', 'default']


class Load(IntEnum):
	MANUAL = 0
	ONCE = 1
	ALWAYS = 2


if MYPY:  # pragma: no cover
	_M = Mapping[str, str]
	_MM = MutableMapping[str, str]
else:
	_M = Mapping
	_MM = MutableMapping


class BooleanConfigRegistry(object):
	"""
	Mixin class for boolean operations.
	"""

	TRUE = frozenset({'yes', 'true', '1', 'enable', 'enabled', 'on'})
	FALSE = frozenset({'no', 'false', '0', 'disable', 'disabled', 'off'})

	def is_true(self, key=None, default=False, value=None):
		# type: (Optional[str], bool, Optional[str]) -> bool
		"""
		Return if the strings value of key is considered as true.

		:param key: UCR variable name.
		:param default: Default value to return, if UCR variable is not set.
		:param value: text string to directly evaluate instead of looking up the key.
		:returns: `True` when the value is one of `yes`, `true`, `1`, `enable`, `enabled`, `on`.

		>>> ucr = ConfigRegistry('/dev/null')
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
		return value.lower() in self.TRUE

	def is_false(self, key=None, default=False, value=None):
		# type: (Optional[str], bool, Optional[str]) -> bool
		"""
		Return if the strings value of key is considered as false.

		:param key: UCR variable name.
		:param default: Default value to return, if UCR variable is not set.
		:param value: text string to directly evaulate instead of looking up the key.
		:returns: `True` when the value is one of `no`, `false`, `0`, `disable`, `disabled`, `off`.

		>>> ucr = ConfigRegistry('/dev/null')
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
		return value.lower() in self.FALSE


class ViewConfigRegistry(_M, BooleanConfigRegistry):
	"""
	Immutable view of UCR.
	"""

	def __init__(self, ucr):
		# type: (Mapping[str, str]) -> None
		self.ucr = ucr

	def __getitem__(self, key):
		# type: (str) -> str
		return self.ucr.__getitem__(key)

	def __iter__(self):
		# type: () -> Iterator[str]
		return self.ucr.__iter__()

	def __len__(self):
		# type: () -> int
		return self.ucr.__len__()


class ReadOnlyConfigRegistry(_M, BooleanConfigRegistry):
	"""
	Merged persistent read-only value store.
	This is a merged view of several sub-registries.

	:param filename: File name for custom layer text database file.
	"""
	DEFAULTS, NORMAL, LDAP, SCHEDULE, FORCED, CUSTOM = range(6)
	LAYER_PRIORITIES = (CUSTOM, FORCED, SCHEDULE, LDAP, NORMAL, DEFAULTS)
	PREFIX = '/etc/univention'
	BASES = {
		NORMAL: 'base.conf',
		LDAP: 'base-ldap.conf',
		SCHEDULE: 'base-schedule.conf',
		FORCED: 'base-forced.conf',
		DEFAULTS: 'base-defaults.conf',
	}

	def __init__(self, filename=""):
		# type: (str) -> None
		super(ReadOnlyConfigRegistry, self).__init__()
		custom = os.getenv('UNIVENTION_BASECONF') or filename
		self.autoload = Load.MANUAL

		self._registry = {}  # type: Dict[int, _ConfigRegistry]
		for reg in self.LAYER_PRIORITIES:
			if reg == self.CUSTOM:
				self._registry[reg] = _ConfigRegistry(custom if custom else os.devnull)
			else:
				self._registry[reg] = _ConfigRegistry(os.devnull if custom else os.path.join(self.PREFIX, self.BASES[reg]))

	def _walk(self):
		# type: () -> Iterator[Tuple[int, _ConfigRegistry]]
		"""
		Iterator over layers.

		:returns: Iterator of 2-tuple (layers-mumber, layer)
		"""
		if self.autoload:
			self.load(Load.MANUAL if self.autoload == Load.ONCE else self.autoload)

		for reg in self.LAYER_PRIORITIES:
			registry = self._registry[reg]
			yield (reg, registry)

	def load(self, autoload=Load.MANUAL):
		# type: (_T, Load) -> _T
		"""
		Load registry from file.

		:param autoload: Automatically reload changed files.
		"""
		for reg in self._registry.values():
			reg.load()

		self.autoload = Load.MANUAL  # prevent recursion!
		strict = six.PY2 and self.is_true('ucr/encoding/strict')
		self.autoload = autoload

		for reg in self._registry.values():
			reg.strict_encoding = strict

		return self

	def __enter__(self):
		# type: () -> ViewConfigRegistry
		"""
		Return immutable view despite `autoload`.

		:returns: A frozen registry.

		> ucr_live = ConfigRegistry().load(autoload=Load.ALWAYS)
		> with ucr_live as ucr_frozen:
		>   for key, value in ucr_frozen.items():
		>     print(key, value)
		"""
		return ViewConfigRegistry(self._merge())

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		"""
		Release registry view.
		"""

	def __getitem__(self, key):  # type: ignore
		# type: (str) -> Optional[str]
		"""
		Return registry value.

		:param key: UCR variable name.
		:returns: the value or `None`.

		Bug #28276: ucr[key] returns None instead of raising KeyError - it would break many UCR templates!
		"""
		return self.get(key)

	def __contains__(self, key):  # type: ignore
		# type: (str) -> bool
		"""
		Check if registry key is set.

		:param key: UCR variable name.
		:returns: `True` is set, `False` otherwise.
		"""
		return any(key in registry for _reg, registry in self._walk())

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
	def get(self, key, default, getscope):  # noqa F811 # pragma: no cover
		# type: (str, _VT, Literal[True]) -> Union[Tuple[int, str], _VT]
		pass

	@overload
	def get(self, key, default=None):  # noqa F811 # pragma: no cover
		# type: (str, _VT) -> Union[str, _VT]
		pass

	def get(self, key, default=None, getscope=False):  # noqa F811
		# type: (str, Optional[_VT], bool) -> Union[str, Tuple[int, str], _VT, None]
		"""
		Return registry value (including optional scope).

		:param key: UCR variable name.
		:param default: Default value when the UCR variable is not set.
		:param getscope: `True` makes the method return the scope level in addition to the value itself.
		:returns: the value or a 2-tuple (level, value) or the default.
		"""
		for reg, registry in self._walk():
			try:
				value = registry[key]  # type: str
			except KeyError:
				continue
			if reg == self.DEFAULTS:
				value = self._eval_default(value)
			return (reg, value) if getscope else value
		return default

	@overload
	def _merge(self):  # pragma: no cover
		# type: () -> Dict[str, str]
		pass

	@overload
	def _merge(self, getscope):  # noqa F811 # pragma: no cover
		# type: (Literal[True]) -> Dict[str, Tuple[int, str]]
		pass

	def _merge(self, getscope=False):  # noqa F811
		# type: (bool) -> Union[Dict[str, str], Dict[str, Tuple[int, str]]]
		"""
		Merge sub registry.

		:param getscope: `True` makes the method return the scope level in addition to the value itself.
		:returns: A mapping from varibal ename to eiter the value (if `getscope` is False) or a 2-tuple (level, value).
		"""
		merge = {}  # type: Dict[str, Union[str, Tuple[int, str]]]
		for reg, registry in self._walk():
			for key, value in registry.items():
				if key not in merge:
					if reg == self.DEFAULTS:
						value = self._eval_default(value)
					merge[key] = (reg, value) if getscope else value

		return merge  # type: ignore

	def _eval_default(self, default):
		# type: (str) -> str
		"""
		Recursively evaluate default value.

		:param default: Default value.
		:returns: Substituted value.
		"""
		try:
			value = run_filter(default, self, opts={'disallow-execution': True})
		except RuntimeError:  # maximum recursion depth exceeded
			value = b''

		if six.PY2:
			return value
		return value.decode("UTF-8")

	@overload
	def items(self):  # pragma: no cover
		# type: () -> ItemsView[str, str]
		pass

	@overload
	def items(self, getscope):  # noqa F811 # pragma: no cover
		# type: (Literal[True]) -> ItemsView[str, Tuple[int, str]]
		pass

	def items(self, getscope=False):  # noqa F811
		# type: (bool) -> Union[ItemsView[str, str], ItemsView[str, Tuple[int, str]]]
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


class ConfigRegistry(ReadOnlyConfigRegistry, _MM):
	"""
	Merged persistent value store.
	This is a merged view of several sub-registries.

	:param filename: File name for custom layer text database file.
	:param write_registry: The UCR level used for writing.
	"""

	def __init__(self, filename="", write_registry=ReadOnlyConfigRegistry.NORMAL):
		# type: (str, int) -> None
		super(ConfigRegistry, self).__init__(filename)
		custom = os.getenv('UNIVENTION_BASECONF') or filename
		self.scope = self.CUSTOM if custom else write_registry
		for reg in self.LAYER_PRIORITIES:
			registry = self._registry[reg]
			registry._create_base_conf()

	@property
	def _layer(self):
		# type: () -> _ConfigRegistry
		"""
		Return selected layer.
		"""
		return self._registry[self.scope]

	def save(self):
		# type: () -> None
		"""Save registry to file."""
		self._layer.save()

	def lock(self):
		# type: () -> None
		"""Lock registry file."""
		self._layer.lock()

	def unlock(self):
		# type: () -> None
		"""Un-lock registry file."""
		self._layer.unlock()

	def __enter__(self):  # type: ignore
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

	def clear(self):
		# type: () -> None
		"""
		Clear all registry keys.
		"""
		self._layer.clear()

	def __delitem__(self, key):
		# type: (str) -> None
		"""
		Delete registry key.

		:param key: UCR variable name.
		"""
		del self._layer[key]

	def __setitem__(self, key, value):
		# type: (str, str) -> None
		"""
		Set registry value.

		:param key: UCR variable name.
		:param value: UCR variable value.
		"""
		self._layer[key] = value

	def update(self, changes):  # type: ignore
		# type: (Dict[str, Optional[str]]) -> Dict[str, Tuple[Optional[str], Optional[str]]]
		"""
		Set or unset the given config registry variables.

		:param changes: dictionary of ucr-variable-name: value-or-None.
		:returns: A mapping from UCR variable name to a 2-tuple (old-value, new-value)
		"""
		registry = self._layer
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

	RE_COMMENT = re.compile(r'^[^:]*#.*$')

	def __init__(self, filename):
		# type: (str) -> None
		dict.__init__(self)
		self.file = filename
		self.backup_file = self.file + '.bak'
		self.lock_filename = self.file + '.lock'
		# will be set by <ConfigRegistry> for each <_ConfigRegistry> - <True>
		# means the backend files are valid UTF-8 and should stay that way -->
		# only accept valid UTF-8
		self.strict_encoding = False
		self.lock_file = None  # type: Optional[IO]
		self.mtime = 0.0

	def load(self):
		# type: () -> None
		"""Load sub registry from file."""
		for fn in (self.file, self.backup_file):
			new = {}
			try:
				file_stat = os.stat(fn)
				if file_stat.st_mtime <= self.mtime and fn == self.file:
					return

				with open(fn, 'r', encoding='utf-8') as reg_file:
					if reg_file.readline() == '' or reg_file.readline() == '':
						continue

					reg_file.seek(0)
					for line in reg_file:
						line = self.RE_COMMENT.sub("", line)
						if line == '':
							continue
						if line.find(': ') == -1:
							continue

						key, value = line.split(': ', 1)
						new[key] = value.strip()

				break
			except EnvironmentError:
				pass
		else:
			return

		self.mtime = file_stat.st_mtime
		self.update(new)
		for key in set(self.keys()) - set(new.keys()):
			self.pop(key, None)

		if fn != self.file:
			self._save_file(self.file)

	def _create_base_conf(self):
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

	def _save_file(self, filename):
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
				if not S_ISREG(file_stat.st_mode):
					return
			except EnvironmentError:
				file_stat = os.stat_result((0o0644, -1, -1, -1, 0, 0, -1, -1, -1, -1))

			# open temporary file for writing
			self._save_to(temp_filename)
			try:
				os.chmod(temp_filename, file_stat.st_mode)
				os.chown(temp_filename, file_stat.st_uid, file_stat.st_gid)
				os.rename(temp_filename, filename)
			except EnvironmentError as ex:
				if ex.errno == errno.EBUSY:
					with open(filename, 'w+', encoding='utf-8') as fd:
						fd.write(open(temp_filename, 'r', encoding='utf-8').read())
					os.unlink(temp_filename)
				else:
					# In this case the temp file created above in this
					# function was already moved by a concurrent UCR
					# operation. Dump the current state to a backup file
					temp_filename = '%s.concurrent_%s' % (filename, time.time())
					self._save_to(temp_filename)
		except EnvironmentError as ex:
			# suppress certain errors
			if ex.errno != errno.EACCES:
				raise

	def _save_to(self, filename):
		# type: (str) -> None
		"""
		Serialize sub registry to file.

		:param filename: File name for saving.
		"""
		with open(filename, 'w', encoding='utf-8') as fd:
			# write data to file
			fd.write(u'# univention_ base.conf\n\n')
			fd.write(self.__unicode__())
			# flush (meta)data
			fd.flush()
			os.fsync(fd.fileno())

	def save(self):
		# type: () -> None
		"""Save sub registry to file."""
		for filename in (self.backup_file, self.file):
			self._save_file(filename)

	def lock(self):
		# type: () -> None
		"""Lock sub registry file."""
		self.lock_file = lock = open(self.lock_filename, "a+", encoding='utf-8')
		fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

	def unlock(self):
		# type: () -> None
		"""Un-lock sub registry file."""
		if self.lock_file is not None:
			self.lock_file.close()
			self.lock_file = None

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
		return '\n'.join(
			'%s: %s' % (key, self.remove_invalid_chars(val))
			for key, val in sorted(self.items())
		)

	def __unicode__(self):
		data = self.__str__()
		if isinstance(data, bytes):
			data = data.decode('UTF-8')
		return data


# vim:set sw=4 ts=4 noet:
