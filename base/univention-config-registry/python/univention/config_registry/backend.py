# -*- coding: utf-8 -*-
#
"""Univention Configuration Registry backend for data storage."""
#  main configuration registry classes
#
# Copyright 2004-2015 Univention GmbH
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
import fcntl
import re
import errno
import time

__all__ = ['StrictModeException', 'exception_occured',
		'SCOPE', 'ConfigRegistry']

INVALID_VALUE_CHARS = '\r\n'


class StrictModeException(Exception):
	"""Attempt to store non-UTF-8 characters in strict UTF-8 mode."""
	pass


def exception_occured(out=sys.stderr):
	"""Print exception message and exit."""
	print >> out, 'E: your request could not be fulfilled'
	print >> out, \
			'try `univention-config-registry --help` for more information'
	sys.exit(1)


SCOPE = ['normal', 'ldap', 'schedule', 'forced', 'custom']


class ConfigRegistry(dict):
	"""
	Merged persistent value store.
	This is a merged view of several sub-registries.
	"""
	NORMAL, LDAP, SCHEDULE, FORCED, CUSTOM, MAX = range(6)
	PREFIX = '/etc/univention'
	BASES = {
			NORMAL: 'base.conf',
			LDAP: 'base-ldap.conf',
			SCHEDULE: 'base-schedule.conf',
			FORCED: 'base-forced.conf',
			}

	def __init__(self, filename=None, write_registry=NORMAL):
		dict.__init__(self)
		self.file = os.getenv('UNIVENTION_BASECONF') or filename or None
		if self.file:
			self.scope = ConfigRegistry.CUSTOM
		else:
			self.scope = write_registry
		self._registry = {}
		for reg in range(ConfigRegistry.MAX):
			if self.file and reg != ConfigRegistry.CUSTOM:
				self._registry[reg] = {}
			elif not self.file and reg == ConfigRegistry.CUSTOM:
				self._registry[reg] = {}
			else:
				self._registry[reg] = self._create_registry(reg)

	def _create_registry(self, reg):
		"""Create internal sub registry."""
		if reg == ConfigRegistry.CUSTOM:
			filename = self.file
		else:
			filename = os.path.join(ConfigRegistry.PREFIX,
					ConfigRegistry.BASES[reg])
		return _ConfigRegistry(filename=filename)

	def load(self):
		"""Load registry from file."""
		for reg in self._registry.values():
			if isinstance(reg, _ConfigRegistry):
				reg.load()
		strict = self.is_true('ucr/encoding/strict')
		for reg in self._registry.values():
			if isinstance(reg, _ConfigRegistry):
				reg.strict_encoding = strict

	def save(self):
		"""Save registry to file."""
		registry = self._registry[self.scope]
		registry.save()

	def lock(self):
		"""Lock registry file."""
		registry = self._registry[self.scope]
		registry.lock()

	def unlock(self):
		"""Un-lock registry file."""
		registry = self._registry[self.scope]
		registry.unlock()

	def __enter__(self):
		"""
		Lock Config Registry for read-modify-write cycle.
		> with ConfigRegistry() as ucr:
		>   ucr['key'] = 'value'
		"""
		self.lock()
		self.load()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is None:
			self.save()
		self.unlock()

	def __delitem__(self, key):
		"""Delete registry key."""
		registry = self._registry[self.scope]
		del registry[key]

	def __getitem__(self, key):
		"""Return registry value."""
		return self.get(key)

	def __setitem__(self, key, value):
		"""Set registry value."""
		registry = self._registry[self.scope]
		registry[key] = value

	def __contains__(self, key):
		"""Check if registry key is set."""
		for reg in (ConfigRegistry.FORCED,
				ConfigRegistry.SCHEDULE,
				ConfigRegistry.LDAP,
				ConfigRegistry.NORMAL,
				ConfigRegistry.CUSTOM):
			registry = self._registry[reg]
			if key in registry:
				return True
		return False

	def iterkeys(self):
		"""Iterate over all registry keys."""
		merge = self._merge()
		for key in merge:
			yield key

	__iter__ = iterkeys

	def get(self, key, default=None, getscope=False):
		"""Return registry value (including optional scope)."""
		for reg in (ConfigRegistry.FORCED,
				ConfigRegistry.SCHEDULE,
				ConfigRegistry.LDAP,
				ConfigRegistry.NORMAL,
				ConfigRegistry.CUSTOM):
			try:
				registry = self._registry[reg]
				# BUG: _ConfigRegistry[key] does not raise a KeyError for unset
				# keys, but returns ''
				if key not in registry:
					continue
				value = registry[key]
				if getscope:
					return (reg, value)
				else:
					return value
			except KeyError:
				continue
		return default

	def has_key(self, key, write_registry_only=False):
		"""Check if registry key is set (DEPRECATED)."""
		if write_registry_only:
			registry = self._registry[self.scope]
			return key in registry
		else:
			return key in self

	def _merge(self, getscope=False):
		"""Merge sub registry."""
		merge = {}
		for reg in (
				ConfigRegistry.FORCED,
				ConfigRegistry.SCHEDULE,
				ConfigRegistry.LDAP,
				ConfigRegistry.NORMAL,
				ConfigRegistry.CUSTOM,
				):
			registry = self._registry[reg]
			if not isinstance(registry, _ConfigRegistry):
				continue
			for key, value in registry.items():
				if key not in merge:
					if getscope:
						merge[key] = (reg, value)
					else:
						merge[key] = registry[key]
		return merge

	def items(self, getscope=False):
		"""Return all registry entries a 2-tuple (key, value)."""
		merge = self._merge(getscope=getscope)
		return merge.items()

	def keys(self):
		"""Return all registry keys."""
		merge = self._merge()
		return merge.keys()

	def values(self):
		"""Return all registry values."""
		merge = self._merge()
		return merge.values()

	def __str__(self):
		"""Return registry content as string."""
		merge = self._merge()
		return '\n'.join(['%s: %s' % (key, val) for key, val in merge.items()])

	def is_true(self, key=None, default=False, value=None):
		"""Return if the strings value of key is considered as true."""
		if key:
			if key in self:
				value = self.get(key).lower()  # pylint: disable-msg=E1103
			else:
				return default
		return value in ('yes', 'true', '1', 'enable', 'enabled', 'on')

	def is_false(self, key=None, default=False, value=None):
		"""Return if the strings value of key is considered as false."""
		if key:
			if key in self:
				value = self.get(key).lower()  # pylint: disable-msg=E1103
			else:
				return default
		return value in ('no', 'false', '0', 'disable', 'disabled', 'off')

	def update(self, changes):
		"""
		Set or unset the given config registry variables.
		:changes: dictionary of ucr-variable-name: value-or-None.
		"""
		registry = self._registry[self.scope]
		changed = {}
		for key, value in changes.iteritems():
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

class _ConfigRegistry(dict):
	"""
	Persistent value store.
	This is a single value store using a text file.
	"""
	def __init__(self, filename=None):
		dict.__init__(self)
		if file:
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
		self.lock_file = None

	def load(self):
		"""Load sub registry from file."""
		self.clear()
		import_failed = False
		try:
			reg_file = open(self.file, 'r')
		except EnvironmentError:
			import_failed = True
		else:
			if len(reg_file.readlines()) < 2:  # comment or nothing
				import_failed = True

		if import_failed:
			try:
				reg_file = open(self.backup_file, 'r')
			except EnvironmentError:
				return

		reg_file.seek(0)
		for line in reg_file.readlines():
			line = re.sub(r'^[^:]*#.*$', "", line)
			if line == '':
				continue
			if line.find(': ') == -1:
				continue

			key, value = line.split(': ', 1)
			value = value.strip()
			if len(value) == 0:  # if variable was set without an value
				value = ''

			self[key] = value
		reg_file.close()

		if import_failed:
			self.__save_file(self.file)

	def __create_base_conf(self):
		"""Create sub registry file."""
		if not os.path.exists(self.file):
			try:
				reg_file = os.open(self.file, os.O_CREAT | os.O_RDONLY, 0644)
				os.close(reg_file)
			except EnvironmentError:
				msg = "E: file '%s' does not exist and could not be created"
				print >> sys.stderr, msg % (self.file,)
				exception_occured()

	def __save_file(self, filename):
		"""Save sub registry to file."""
		temp_filename = '%s.temp' % filename
		try:
			try:
				file_stat = os.stat(filename)
				mode = file_stat.st_mode
				user = file_stat.st_uid
				group = file_stat.st_gid
			except:
				mode = 00644
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
			except OSError:
				# In this case the temp file created above in this
				# function was already moved by a concurrent UCR
				# operation. Dump the current state to a backup file
				temp_filename = '%s.concurrent_%s' % (filename, time.time())
				reg_file = open(temp_filename, 'w')
				reg_file.write('# univention_ base.conf\n\n')
				reg_file.write(self.__str__())
				reg_file.close()
		except EnvironmentError, ex:
			# suppress certain errors
			if ex.errno != errno.EACCES:
				raise

	def save(self):
		"""Save sub registry to file."""
		for filename in (self.backup_file, self.file):
			self.__save_file(filename)

	def lock(self):
		"""Lock sub registry file."""
		self.lock_file = open(self.lock_filename, "a+")
		fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)

	def unlock(self):
		"""Un-lock sub registry file."""
		self.lock_file.close()

	def __getitem__(self, key):
		"""Return value from sub registry."""
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			return ''

	def __setitem__(self, key, value):
		"""Set value in sub registry."""
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
		"""Remove non-UTF-8 characters from value."""
		for letter in INVALID_VALUE_CHARS:
			seq = seq.replace(letter, '')
		return seq

	def __str__(self):
		"""Return sub registry content as string."""
		return '\n'.join(['%s: %s' % (key, self.remove_invalid_chars(val)) for
			key, val in sorted(self.items())])

# vim:set sw=4 ts=4 noet:
