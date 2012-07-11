#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: expert partition
#
# Copyright 2004-2012 Univention GmbH
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

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

from objects import *
from local import _

class object(content):

	def profile_complete(self):
		return True

	def checkname(self):
		return ['expert partitioning']

	def layout(self):
		msg = [
			_('Univention Installer has been started with the'),
			_('Software RAID option. The hard disk has to be'),
			_('partitioned and formatted manually.'),
			' ',
			_('By pressing'),
			' ',
			_('    [ALT]+[F2]'),
			' ',
			_('an interactive shell will be started, which allows you'),
			_('to partition your hard disks using the standard'),
			_('tools like cfdisk, mkfs.ext3, mdadm or lvcreate.'),
			' ',
			_('By pressing'),
			' ',
			_('    [ALT]+[F1]'),
			' ',
			_('the installation will be continued.'),
			]

		j = 0
		for i in msg:
			self.elements.append(textline(i,self.minY-11+j,self.minX+5))
			j = j + 1

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Partitioning (expert mode):\n\nCTRL+ALT+F2 interactive shell\nCTRL+ALT+F1 installation screen')

	def modheader(self):
		return _('Partitioning')

	def profileheader(self):
		return 'Partitioning'

	def result(self):
		result={}
		return result
