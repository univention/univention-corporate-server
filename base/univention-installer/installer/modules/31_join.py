#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: configuration for the join process
#
# Copyright (C) 2004-2009 Univention GmbH
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
	def checkname(self):
		return ['domain_controller_account','domain_controller_password']

	def modvars(self):
		return ['domain_controller','domain_controller_account','domain_controller_password']

	def profile_complete(self):
		message=_('The following value is missing: ')
		if self.check('auto_join') | self.check('domain_controller_account') | self.check('domain_controller_password'):
			return False

		if self.all_results.has_key('auto_join') and self.all_results['auto_join'] in ['false', 'False']:
			return True

		if self.all_results['domain_controller_account'].strip() == '':
			if not self.ignore('domain_controller_account'):
				self.message=message+_('Join account')
				return False

		if self.all_results['domain_controller_password'].strip() == '':
			if not self.ignore('domain_controller_password'):
				self.message=message+_('Password')
				return False

		return True


	def mod_depends(self):
		return {'system_role': ['domaincontroller_backup','domaincontroller_slave','memberserver','managed_client','mobile_client'] }

	def layout(self):
		self.elements.append(textline(_('Start join at the end of installation.'),self.minY,self.minX+2)) #2
		self.elements.append(checkbox({" ": [" ", 0]},self.minY+1,self.minX+2,4, 1, [0])) #3

		self.elements.append(checkbox({" ": [" ", 0]},self.minY+4,self.minX+2,4, 1, [0])) #4
		self.elements.append(textline(_('Search Domain controller Master in DNS'),self.minY+3,self.minX+2)) #5

		self.elements.append(textline(_('Hostname of Domain controller Master'),self.minY+6,self.minX+2)) #6
		self.elements.append(input('',self.minY+7,self.minX+2,30)) #7

		self.elements.append(textline(_('Join account'),self.minY+9,self.minX+2)) #8
		self.elements.append(input('Administrator',self.minY+10,self.minX+2,30)) #9

		self.elements.append(textline(_('Password'),self.minY+12,self.minX+2)) #10
		self.elements.append(password('',self.minY+13,self.minX+2,30)) #11

		self.elements.append(textline(_('Password (retype)'),self.minY+15,self.minX+2)) #12
		self.elements.append(password('',self.minY+16,self.minX+2,30)) #13
		self.join_host_search_disabled=1
		self.elements[7].disable()
		self.join_disabled=0

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key in [ 10, 32 ] and self.elements[3].active:
			self.elements[self.current].key_event(key)
			if " " in self.elements[3].result():
				self.join_disabled=0
				if self.join_host_search_disabled:
					self.elements[7].enable()
				else:
					self.elements[7].disable()
				self.elements[9].enable()
				self.elements[11].enable()
				self.elements[13].enable()
			else:
				self.join_disabled=1
				self.elements[7].disable()
				self.elements[9].disable()
				self.elements[11].disable()
				self.elements[13].disable()
			self.draw()
		elif key in [ 10, 32 ] and self.elements[4].active:
			self.elements[self.current].key_event(key)
			if " " in self.elements[4].result():
				self.join_host_search_disabled=0
				if not self.join_disabled == 1:
					self.elements[7].disable()
			else:
				self.join_host_search_disabled=1
				if not self.join_disabled == 1:
					self.elements[7].enable()
			self.draw()
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):

		if self.elements[7].disabled and self.elements[9].disabled and self.elements[11].disabled and self.elements[13].disabled:
			return 0

		message=_('The following value is missing: ')
		if self.elements[7].result().strip() == '' and not " " in self.elements[4].result():
			return message+_('Hostname of Domain controller Master')
		if self.elements[9].result().strip() == '':
			return message+_('Join account')
		elif self.elements[11].result().strip() == '':
			return message+_('Password for Root')
		elif self.elements[13].result().strip() == '':
			return message+_('Password for Root (retype)')
		elif self.elements[11].result().strip() != self.elements[13].result().strip():
			return _('Passwords did not match.')
		return 0

	def helptext(self):
		return _('Join settings \n \n All settings to join this system into given domain.')

	def modheader(self):
		return _('Join settings')

	def result(self):
		result={}
		if self.elements[7].disabled and self.elements[9].disabled and self.elements[11].disabled and self.elements[13].disabled:
			result['auto_join']='false'
		else:
			if self.elements[7].result():
				result['domain_controller']='%s'%self.elements[7].result()
			result['domain_controller_account']='%s'%self.elements[9].result()
			result['domain_controller_password']='%s'%self.elements[11].result()
		return result
