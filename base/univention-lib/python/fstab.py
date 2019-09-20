#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Read and write :file:`/etc/fstab`.
"""
from __future__ import print_function
# Copyright 2006-2019 Univention GmbH
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

import os
import re


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
		fd = open(self.__file, 'r')
		for line in fd.readlines():
			if File._is_comment(line):
				self.append(line[:-1])
			elif line.strip():
				self.append(self.__parse(line))
		fd.close()

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
		# type: (List[str], bool) -> List[Entry]
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

	def save(self):
		# type: () -> None
		"""
		Save entries to file.
		"""
		fd = open(self.__file, 'w')
		for line in self:
			fd.write('%s\n' % str(line))
		fd.close()

	def __parse(self, line):
		# type: (str) -> Entry
		"""
		Parse file system table line.

		1.	`fs_spec`
		2.	`fs_file`
		3.	`fs_vfstype`
		4.	`fs_mntops`
		5.	`fs_freq`
		6.	`fs_passno`

		:param str line: A line.
		:returns: The parsed entry.
		:rtype: Entry
		:raises InvalidEntry: if the line cannot be parsed.
		"""
		fields = line.split(None, 7)
		if len(fields) < 4:
			raise InvalidEntry('The following is not a valid fstab entry: %s' % line)  # TODO
		entry = Entry(*fields[: 4])
		if len(fields) > 4:
			dump = fields[4]
			if not File._is_comment(dump):
				entry.dump = int(dump)
			else:
				entry.comment = dump
		if len(fields) > 5:
			passno = fields[5]
			if not File._is_comment(passno):
				entry.passno = int(passno)
			else:
				entry.comment = passno
		if len(fields) > 6:
			entry.comment = ' '.join(fields[6:])
		return entry


class Entry(object):
	"""
	Entry of :manpage:`fstab(5)`.

	:param str spec: This field describes the block special device or remote filesystem to be mounted..
	:param str mount_point: This field describes the mount point (target) for the filesystem.
	:param str type: The type of the filesystem.
	:param options: The list of mount options associated with the filesystem.
	:type options: List[str]
	:param int dump: Option for :manpage:`dump(8)`.
	:param int passno: Order information for `fsck(8)`.
	:param str comment: Optional comment from end of line.

	:ivar str uuid: The file system |UUID| if the file system is mounted by it. Otherwise `None`.
	"""

	def __init__(self, spec, mount_point, type, options, dump=0, passno=0, comment=''):
		# type: (str, str, str, str, int, int, str) -> None
		self.spec = spec.strip()
		if self.spec.startswith('UUID='):
			self.uuid = self.spec[5:]  # type: Optional[str]
			uuid_dev = os.path.join('/dev/disk/by-uuid', self.uuid)
			if os.path.exists(uuid_dev):
				self.spec = os.path.realpath(uuid_dev)
		else:
			self.uuid = None
		self.mount_point = mount_point.strip()
		self.type = type.strip()
		self.options = options.split(',')
		self.dump = int(dump)
		self.passno = int(passno)
		self.comment = comment

	def __str__(self):
		if self.uuid:
			return 'UUID=%s\t%s\t%s\t%s\t%d\t%d\t%s' % (self.uuid, self.mount_point, self.type, ','.join(self.options), self.dump, self.passno, self.comment)
		else:
			return '%s\t%s\t%s\t%s\t%d\t%d\t%s' % (self.spec, self.mount_point, self.type, ','.join(self.options), self.dump, self.passno, self.comment)


class InvalidEntry(Exception):
	"""
	Invalid entry in file system table
	"""
	pass


if __name__ == '__main__':
	fstab = File('fstab')
	print(fstab.get(['xfs', 'ext3']))
