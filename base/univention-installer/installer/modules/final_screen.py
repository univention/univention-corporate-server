#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: installation status screen
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
import linecache
from objects import *
from local import _
import os

error_log = "/tmp/installation_error.log"

class object(content):
	def checkname(self):
		return ['final']

	def layout(self):

		if os.path.isfile(error_log):
			self.elements.append(textline(_("Installation failed, please restart and try again."),self.minY+1,self.minX+2))
			for i in xrange(1, 10):
				line = linecache.getline(error_log, i)
				line = line[:50]
				line = line.replace("\n", " ")
				self.elements.append(textline(line, self.minY+3+i,self.minX+2))
		else:
			self.elements.append(textline(_("Installation succeded, please restart the computer."),self.minY+1,self.minX+2))
		self.elements.append(textline(_('Please press F12 to reboot the computer.'),self.minY+2,self.minX+2))

	def input(self,key):
		pass

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Installation status screen')

	def result(self):
		result = {}
		result['installation'] = 'the end'

		return result
