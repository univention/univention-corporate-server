#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
import string

class object(content):
	def checkname(self):
		return ['local_repository','create_home_share']


	def modvars(self):
		return ['local_repository','create_home_share']

	def mod_depends(self):
		return {'system_role': ['domaincontroller_master', 'domaincontroller_backup','domaincontroller_slave','memberserver','basesystem'] }

	def depends(self):
		return {}

	def profile_complete(self):
		if self.check('local_repository') | self.check('create_home_share'):
			return False
		return True

	def layout(self):
		oxae = False
		if self.cmdline.has_key('edition') and self.cmdline['edition'][0] == 'oxae':
			oxae = True

		self.reset_layout()

		if oxae:
			self.add_elem('create_local_repo', textline('[ ] %s' % _('Create local repository'), self.minY+1, self.minX+2,40,40,))
		elif self.all_results.has_key('system_role') and self.all_results['system_role'] in ['domaincontroller_master', 'domaincontroller_backup' ]:
			self.add_elem('create_local_repo', checkbox({_('Create local repository'): 'local_repository'}, self.minY+1, self.minX+2,30,1,[]))
		else:
			self.add_elem('create_local_repo', checkbox({_('Create local repository'): 'local_repository'}, self.minY+1, self.minX+2,30,1,[]))

		if self.all_results.has_key('system_role') and self.all_results['system_role'] in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver' ]:
			self.add_elem('create_home_share', checkbox({_('Create home share'): 'create_home_share'}, self.minY+3, self.minX+2,30,1,[0]))
		elif not (self.all_results.has_key('system_role') and self.all_results['system_role'] in ['basesystem']):
			self.add_elem('create_home_share', checkbox({_('Create home share'): 'create_home_share'}, self.minY+3, self.minX+2,30,1,[ ]))

		self.add_elem('BT_back', button(_('F11-Back'),self.minY+18,self.minX+2))
		self.add_elem('BT_next', button(_('F12-Next'),self.minY+18,self.minX+20+(self.width)-37))

		self.current = self.get_elem_id('BT_next')
		self.get_elem_by_id(self.current).set_on()

	def input(self,key):

		try:
			if key in [ 10, 32 ] and self.get_elem('BT_back').get_status():
				return 'prev'

			elif key in [ 10, 32 ] and self.get_elem('BT_next').get_status():
				return 'next'

			else:
				return self.get_elem_by_id(self.current).key_event(key)
		except AttributeError:
			# it might be possible, that the focus is on the textline (OXAE). Bug #12205
			return

	def incomplete(self):
		return 0

	def helptext(self):
		return _('System-Settings  \n \n Various system settings')

	def modheader(self):
		return _('System-Settings')

	def result(self):
		result={}

		oxae = False
		if self.cmdline.has_key('edition') and self.cmdline['edition'][0] == 'oxae':
			oxae = True

		if oxae:
			result['local_repository']='false'
		else:
			if len(self.get_elem('create_local_repo').selected) > 0:
				result['local_repository']='true'
			else:
				result['local_repository']='false'

		# by default no local repository is created
		result[ 'local_repository' ] = 'false'

		if not (self.all_results.has_key('system_role') and self.all_results['system_role'] in ['basesystem']):
			if len(self.get_elem('create_home_share').selected) > 0:
				result['create_home_share']='true'
			else:
				result['create_home_share']='false'
		else:
			result['create_home_share']='false'

		return result
