#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Handle parsing and writing :file:`/etc/fstab`.

See <http://linux.die.net/include/mntent.h>.
"""
# Copyright 2006-2021 Univention GmbH
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

import os
import re
from typing import Container, List, Optional, Union  # noqa F401


class InvalidEntry(Exception):
	"""
	Invalid entry in file system table
	"""
	pass


class File(list):
	"""
	Handle lines of :file:`/etc/fstab`.

	:param str file: The name of the file.
	"""
	_is_comment = re.compile('[ \t]*#').search
	_filesystems = ('ext2', 'xfs', 'nfs', 'proc', 'auto', 'swap')

	def __init__(self, file='/etc/fstab'):
		# type: (str) -> None
		list.__init__(self)
		self.__file = file
		self.load()

	def load(self):
		# type: () -> None
		"""
		Load entries from file.
		"""
		with open(self.__file, 'r') as fd:
			for _line in fd:
				line = self.__parse(_line)
				if not isinstance(line, Entry) and _line.strip() and not _line.strip().startswith('#'):
					raise InvalidEntry('The following is not a valid fstab entry: %r' % (_line,))  # TODO
				self.append(line)

	def find(self, **kargs):
		# type: (**str) -> Optional[Entry]
		"""
		Search and return the entry matching the criteria.

		:param kwargs: A mapping of :py:class:`Entry` attributes to values.
		:returns: The first entry matching all criteria or `None`.
		:rtype: Entry or None
		"""
		for entry in self:
			found = True
			for arg, value in kargs.items():
				if not hasattr(entry, arg) or getattr(entry, arg) != value:
					found = False
					break
			if found:
				return entry
		return None

	def get(self, filesystem=[], ignore_root=True):
		# type: (Container[str], bool) -> List[Entry]
		"""
		Return list of entries matching a list of file system types.

		:param filesystem: A list of file system names.
		:type filesystem: List[str]
		:param bool ignore_root: Skip the root file system if `True`.
		:returns: A list of matching entries.
		:rtype: List[Entry]
		"""
		result = []
		for entry in self:
			if isinstance(entry, str):
				continue
			if ignore_root and entry.mount_point == '/':
				continue
			if not filesystem or entry.type in filesystem:
				result.append(entry)
		return result

	def save(self, filename=None):
		# type: (Optional[str]) -> None
		"""
		Save entries to file.
		"""
		with open(filename or self.__file, 'w') as fd:
			for line in self:
				fd.write('%s\n' % (line,))

	def __parse(self, line):
		# type: (str) -> Union[Entry, str]
		"""
		Parse file system table line.

		1. `fs_spec`
		2. `fs_file`
		3. `fs_vfstype`
		4. `fs_mntops`
		5. `fs_freq`
		6. `fs_passno`

		:param str line: A line.
		:returns: The parsed entry.
		:rtype: Entry
		:raises InvalidEntry: if the line cannot be parsed.
		"""
		line = line.lstrip().rstrip('\n')
		if line.startswith('#'):
			return line

		line, has_comment, comment = line.partition('#')
		fields = line.split(None, 5)
		if len(fields) < 4:
			return line

		rem = has_comment + comment if has_comment or fields[-1].endswith('\t') else None
		return Entry(*fields, comment=rem)  # type: ignore


class Entry(object):
	"""
	Mount table entry of :manpage:`fstab(5)`.

	:param str spec: This field describes the block special device or remote filesystem to be mounted.
	:param str mount_point: This field describes the mount point (target) for the filesystem.
	:param str type: The type of the filesystem.
	:param options: The list of mount options associated with the filesystem.
	:type options: List[str]
	:param int dump: Option for :manpage:`dump(8)`.
	:param int passno: Order information for `fsck(8)`.
	:param str comment: Optional comment from end of line.

	:ivar str uuid: The file system |UUID| if the file system is mounted by it. Otherwise `None`.
	"""

	_quote_dict = dict([(c, r'\%s' % oct(ord(c))) for c in ' \t\n\r\\'])
	_quote_re = re.compile(r'\\0([0-7]+)')

	def __init__(self, spec, mount_point, type, options, dump=None, passno=None, comment=None):
		# type: (str, str, str, str, str, str, str) -> None
		self.spec = self.unquote(spec.strip())
		if self.spec.startswith('UUID='):
			self.uuid = self.spec[5:]  # type: Optional[str]
			uuid_dev = os.path.join('/dev/disk/by-uuid', self.uuid)
			if os.path.exists(uuid_dev):
				self.spec = os.path.realpath(uuid_dev)
		else:
			self.uuid = None
		self.mount_point = self.unquote(mount_point.strip())
		self.type = self.unquote(type.strip())
		self.options = self.unquote(options).split(',') if not isinstance(options, list) else options
		self.dump = int(dump) if dump else None
		self.passno = int(passno) if passno else None
		self.comment = comment

	def __str__(self, delim='\t'):
		# type: (str) -> str
		"""
		Return the canonical string representation of the object.
		>>> str(Entry('proc', '/proc', 'proc', 'defaults', 0, 0))
		'proc\\t/proc\\tproc\\tdefaults\\t0\\t0'
		>>> str(Entry('/dev/sda', '/', 'ext2,ext3', 'defaults,rw', 0, 0, '# comment'))
		'/dev/sda\\t/\\text2,ext3\\tdefaults,rw\\t0\\t0\\t# comment'
		"""
		h = [
			self.quote('UUID=%s' % self.uuid if self.uuid else self.spec),
			self.quote(self.mount_point),
			self.quote(self.type),
			self.quote(','.join(self.options)),
		]
		if self.dump is not None:
			h.append(str(self.dump))
		if self.passno is not None:
			h.append(str(self.passno))

		if self.comment is not None:
			h.append(self.comment)
		return delim.join(h)

	def __repr__(self):
		# type: () -> str
		"""
		>>> Entry('proc', '/proc', 'proc', 'defaults', 0, 0)
		univention.lib.fstab.Entry('proc', '/proc', 'proc', options='defaults', freq=0, passno=0)
		"""
		h = [
			"%r" % self.spec,
			"%r" % self.mount_point,
			"%r" % self.type,
			"options=%r" % ','.join(self.options),
			"freq=%r" % self.dump,
			"passno=%r" % self.passno,
		]
		if self.comment is not None:
			h.append("comment=%r" % self.comment)
		return "univention.lib.fstab.Entry(%s)" % ', '.join(h)

	@classmethod
	def quote(cls, s):
		# type: (str) -> str
		"""
		Quote string to octal.

		>>> Entry.quote('a b')
		'a\\\\040b'
		"""
		return ''.join([cls._quote_dict.get(c, c) for c in s])

	@classmethod
	def unquote(cls, s):
		# type: (str) -> str
		"""
		Unquote octal to string.

		>>> Entry.unquote('a\\040b')
		'a b'
		"""
		return cls._quote_re.sub(lambda m: chr(int(m.group(1), 8)), s)

	def hasopt(self, opt):
		# type: (str) -> List[str]
		"""
		Search for an option matching OPT.

		>>> Entry('/dev/sda', '/', 'ext3', 'default,ro,user_xattr,acl', 0, 0).hasopt('user')
		['user_xattr']
		"""
		return [o for o in self.options if o.startswith(opt)]


if __name__ == '__main__':
	import doctest
	doctest.testmod()
