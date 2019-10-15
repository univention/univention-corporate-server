#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: reads /etc/mtab
#
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

from __future__ import print_function

import os


class File(list):

	def __init__(self, file='/etc/mtab'):
		list.__init__(self)
		self.__file = file
		self.load()

	def load(self):
		fd = open(self.__file, 'r')
		for line in fd.readlines():
			self.append(self.__parse(line))
		fd.close()

	def get(self, partition):
		for entry in self:
			if os.path.realpath(entry.spec) == os.path.realpath(partition):
				return entry
		return None

	def __parse(self, line):
		fields = line.split(None, 5)
		entry = Entry(*fields)
		return entry


class Entry(object):

	def __init__(self, spec, mount_point, type, options, dump=0, passno=0, comment=''):
		self.spec = spec.strip()
		self.mount_point = mount_point.strip()
		self.type = type.strip()
		self.options = options.split(',')
		self.dump = int(dump)
		self.passno = int(passno)


class InvalidEntry(Exception):
	pass


if __name__ == '__main__':
	mtab = File('mtab')
	print(mtab.get('/dev/sda4'))
