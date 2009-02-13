#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: expert partition
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

import objects
from objects import *
from local import _

class object(content):

	def profile_complete(self):
		return True

	def checkname(self):
		return ['expert partitioner']

	def layout(self):

		msg = [
			_('Univention Installer has been started with the'),
			_('Software RAID boot option, which mandates expert mode.'),
			_('The hard disk has to be partitioned and formatted manually.'),
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
			self.elements.append(textline(i,self.minY+j,self.minX+2))
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
		return _('Partitioner (expert mode):\n\nCTRL+ALT+F2 interactive shell\nCTRL+ALT+F1 installation screen')

	def modheader(self):
		return _('Part. expert mode')

	def result(self):
		result={}
		return result
