#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: provides size information about a hard drive partition
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

'''This module provides a similar functionality as the UNIX tool df'''

import os


class DeviceInfo(object):

	def __init__(self, path):
		self.path = path
		self._statvfs = os.statvfs(self.path)

	def free(self):
		return (self._statvfs.f_bfree * self._statvfs.f_bsize)

	def available(self):
		return (self._statvfs.f_bavail * self._statvfs.f_bsize)

	def size(self):
		return (self._statvfs.f_blocks * self._statvfs.f_bsize)

	def block_size(self):
		return self._statvfs.f_bsize
