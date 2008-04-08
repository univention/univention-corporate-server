#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
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
import string

class object(content):
	def checkname(self):
		return ['']

	def modvars(self):
		return ['']

	def depends(self):
		return {}

	def layout(self):
		if self.all_results['system_role'] == 'domaincontroller_master':
			role="Domaincontroller Master "
		elif self.all_results['system_role'] == 'domaincontroller_backup':
			role="Domaincontroller Backup "
		elif self.all_results['system_role'] == 'domaincontroller_slave':
			role="Domaincontroller Slave  "
		elif self.all_results['system_role'] == 'memberserver':
			role="Memberserver            "
		elif self.all_results['system_role'] == 'managed_client':
			role="Managed Client          "
		elif self.all_results['system_role'] == 'mobile_client':
			role="Mobile Client           "
		else:
			role="Basesystem              "

		self.elements.append(textline(_('Press "Start installation" to begin process'), self.minY+1, self.minX+2))
		self.elements.append(textline(_('Systemrole:    %s') % role , self.minY+3, self.minX+2))
		self.elements.append(textline('Hostname:      %s' % self.all_results['hostname'] , self.minY+4, self.minX+2))
		self.elements.append(textline(_('Domainname:    %s') % self.all_results['domainname'] , self.minY+5, self.minX+2))
		count=0
		if self.all_results.has_key('eth0_type') and self.all_results['eth0_type'] == 'dynamic':
			self.elements.append(textline('eth0 Network:  dynamic', self.minY+7, self.minX+2))
		else:
			self.elements.append(textline('eth0 IP:       %s' % self.all_results['eth0_ip'] , self.minY+7, self.minX+2))
			self.elements.append(textline('eth0 Netmask:  %s' % self.all_results['eth0_netmask'] , self.minY+8, self.minX+2))
			count=count+1

		gateway=''
		if self.all_results.has_key('gateway'):
			gateway=self.all_results['gateway']
		self.elements.append(textline('Gateway:       %s' % gateway , self.minY+8+count, self.minX+2))
		nameserver=''
		if self.all_results.has_key('nameserver_1'):
			nameserver=self.all_results['nameserver_1']
		self.elements.append(textline('Nameserver1:   %s' % nameserver , self.minY+9+count, self.minX+2))

		internet_files=[]
		if 'msttcorefonts' in self.all_results['packages']:
			internet_files.append('Microsoft Fonts')
		if 'univention-windows-installer' in self.all_results['packages']:
			internet_files.append('Windows Installer')
		if 'univention-flashplugin' in self.all_results['packages']:
			internet_files.append('Flashplugin')

		if not internet_files:
			self.elements.append(textline(_('No package will download files from the internet.'), self.minY+11+count, self.minX+2))
		else:
			for p in internet_files:
				self.elements.append(textline(_('%s will download internet files.') % p , self.minY+11+count, self.minX+2))
				count=count+1


	def draw(self):
		self.layout()
		content.draw(self)

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
		return _('Overview \n \n Installation settings')

	def modheader(self):
		return _('Overview')

	def result(self):
		result={}
		return result
