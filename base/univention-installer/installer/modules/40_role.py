#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system role selection
#
# Copyright 2004-2011 Univention GmbH
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
		elif value in ['basesystem','Base']:
			return 'basesystem'


	def layout(self):
		oxae = False
		if self.cmdline.has_key('edition') and self.cmdline['edition'][0] == 'oxae':
			oxae = True
		self.elements.append(textline(_('Select the system role:'), self.minY, self.minX+2))#2
		dict={}
		dict[_('Master domain controller')]=['domaincontroller_master',0]
		if not oxae:
			dict[_('Backup domain controller')]=['domaincontroller_backup',1]
			dict[_('Slave domain controller')]=['domaincontroller_slave',2]
			dict[_('Member server')]=['memberserver',3]
			dict[_('Base system')]=['basesystem',4]

			list=['domaincontroller_master','domaincontroller_backup','domaincontroller_slave','memberserver','basesystem']
			select=0
			if self.all_results.has_key('system_role'):
				select=list.index(self.mapping(self.all_results['system_role']))
		else:
			select=0

		self.elements.append(radiobutton(dict,self.minY+1,self.minX+2,40,10,[select]))#3
		self.elements[3].current=select

		if oxae:
			self.elements.append(textline('[ ] %s' % _('Backup domain controller'),self.minY+2,self.minX+2,40,40))#4
			self.elements.append(textline('[ ] %s' % _('Slave domain controller'),self.minY+3,self.minX+2,40,40))#5
			self.elements.append(textline('[ ] %s' % _('Member server'),self.minY+4,self.minX+2,40,40))#6
			self.elements.append(textline('[ ] %s' % _('Base system'),self.minY+5,self.minX+2,40,40))#7


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
		return _('System role \n \n Select a system role. Depending on the system role different components will be installed. \n \n Master domain controller: \n This system keeps the whole LDAP tree and is the core of your UCS domain. \n \n Backup domain controller: \n This system keeps a copy of the complete LDAP structure, which cannot be changed manually. \n \n Slave domain controller: \n This system includes required LDAP data for a special purpose (i.e. location based). \n \n Member server: \n Member of a domain offering specified domainwide services like printing or backup. No LDAP data is stored on such a system. \n \n Base system: \n A stand-alone server solution for web-server or firewall for example. This system is not a member of any domain.')

	def modheader(self):
		return _('System role')

	def profileheader(self):
		return 'System role'

	def result(self):
		return {'system_role':self.elements[3].result()}
