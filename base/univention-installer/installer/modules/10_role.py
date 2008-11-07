#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system role selection
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
	def checkname(self):
		return ['system_role']

	def profile_complete(self):
		if self.check('system_role'):
			return False
		if self.all_results.has_key('system_role'):
			return True
		if self.ignore('system_role'):
			return True
		return False

	def run_profiled(self):
		return {'system_role': self.mapping(self.all_results['system_role'])}

	def mapping(self,value):
		if value in ['domaincontroller_master','DomainController_Master']:
			return 'domaincontroller_master'
		elif value in ['domaincontroller_backup','DomainController_Backup']:
			return 'domaincontroller_backup'
		elif value in ['domaincontroller_slave','DomainController_Slave']:
			return 'domaincontroller_slave'
		elif value in ['memberserver','MemberServer']:
			return 'memberserver'
		elif value in ['managed_client','FatClient']:
			return 'managed_client'
		elif value in ['mobile_client','MobileClient']:
			return 'mobile_client'
		elif value in ['basesystem','Base']:
			return 'basesystem'


	def layout(self):
		oxae = False
		if self.cmdline.has_key('edition') and self.cmdline['edition'][0] == 'oxae':
			oxae = True
		self.elements.append(textline(_('System role:'), self.minY, self.minX+2))#2
		dict={}
		dict['Domain Controller Master']=['domaincontroller_master',0]
		if not oxae:
			dict['Domain Controller Backup']=['domaincontroller_backup',1]
			dict['Domain Controller Slave']=['domaincontroller_slave',2]
			dict['Memberserver']=['memberserver',3]
			dict['Managed Client']=['managed_client',4]
			dict['Mobile Client']=['mobile_client',5]
			dict['Basissystem']=['basesystem',6]

			list=['domaincontroller_master','domaincontroller_backup','domaincontroller_slave','memberserver','managed_client','mobile_client','basesystem']
			select=0
			if self.all_results.has_key('system_role'):
				select=list.index(self.mapping(self.all_results['system_role']))
		else:
			select=0

		self.elements.append(radiobutton(dict,self.minY+1,self.minX+2,40,10,[select]))#3
		self.elements[3].current=select

		if oxae:
			self.elements.append(textline('[ ] %s' % _('Domain Controller Backup'),self.minY+2,self.minX+2,40,40))#4
			self.elements.append(textline('[ ] %s' % _('Domain Controller Slave'),self.minY+3,self.minX+2,40,40))#5
			self.elements.append(textline('[ ] %s' % _('Memberserver'),self.minY+4,self.minX+2,40,40))#6
			self.elements.append(textline('[ ] %s' % _('Managed Client'),self.minY+5,self.minX+2,40,40))#7
			self.elements.append(textline('[ ] %s' % _('Mobile Client'),self.minY+6,self.minX+2,40,40))#8
			self.elements.append(textline('[ ] %s' % _('Basissystem'),self.minY+7,self.minX+2,40,40))#9


	def input(self,key):
		self.debug('key_event=%d' % key)
		if key in [10, 32] and self.btn_next():
			return 'next'
		elif key in [10,32] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('System role \n \n Choose a system role. Different components will be installed. \n \n Domain Controller Master: \n This system keeps the whole LDAP tree and is the core of your UCS domain. \n \n Domain Controller Backup: \n This system keeps a copy of the complete LDAP structure, which cannot be changed manually. \n \n Domain Controller Slave: \n This system includes required LDAP data for a special purpose (i.e. location based). \n \n Memberserver: \n Member of a domain offering specified domainwide services like printing or backup. No LDAP data is stored on such a system. \n \n Managed Client: \n A Linux desktop system. \n \n Mobile Client: \n A managed client with notebook optimizations. \n \n Basesystem: \n A stand-alone server solution for web-server or firewall for example. This system is not a member of any domain.')

	def modheader(self):
		return _('System role')

	def result(self):
		return {'system_role':self.elements[3].result()}
