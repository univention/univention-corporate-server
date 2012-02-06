#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: reads and writes /etc/fstab
#
# Copyright 2006-2012 Univention GmbH
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

import os
import re

class File(list):
	_is_comment = re.compile('[ \t]*#').search
	_filesystems = ('ext2', 'xfs', 'nfs', 'proc', 'auto', 'swap')

	def __init__(self, file = '/etc/fstab'):
		list.__init__(self)
		self.__file = file
		self.load()

	def load(self):
		fd = open(self.__file, 'r')
		for line in fd.readlines():
			if File._is_comment(line):
				self.append(line[:-1])
			elif line.strip():
				self.append(self.__parse(line))
		fd.close()

	def find(self, **kargs):
		for entry in self:
			found = True
			for arg, value in kargs.items():
				if not hasattr(entry, arg) or getattr(entry, arg) != value:
					found = False
					break
			if found:
				return entry
		return None

	def get(self, filesystem = [], ignore_root = True):
		result = []
		for entry in self:
			if type(entry) == str:
				continue
			if ignore_root and entry.mount_point == '/':
				continue
			if not filesystem or entry.type in filesystem:
				result.append(entry)
		return result

	def save(self):
		fd = open(self.__file, 'w')
		for line in self:
			fd.write('%s\n' % str(line))
		fd.close()

	def __parse(self, line):
		fields = line.split(None, 7)
		if len(fields) < 4:
			raise InvalidEntry('The following is not a valid fstab entry: %s' % line) #TODO
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
	def __init__(self, spec, mount_point, type, options,
		         dump = 0, passno = 0, comment = ''):
		self.spec = spec.strip()
		if self.spec.startswith('UUID='):
			self.uuid = self.spec[5:]
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

	def __str__( self ):
		if self.uuid:
			return 'UUID=%s\t%s\t%s\t%s\t%d\t%d\t%s' % \
			       ( self.uuid, self.mount_point, self.type,  ','.join( self.options ),
			         self.dump, self.passno, self.comment )
		else:
			return '%s\t%s\t%s\t%s\t%d\t%d\t%s' % \
			       ( self.spec, self.mount_point, self.type,  ','.join( self.options ),
			         self.dump, self.passno, self.comment )

class InvalidEntry(Exception):
	pass

if __name__ == '__main__':
	fstab= File('fstab')
	print fstab.get(['xfs', 'ext3'])
