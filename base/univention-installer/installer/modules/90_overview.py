#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
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

		just=16
		self.elements.append(textline(_('This is the last step of the interactive installation.'), self.minY+0, self.minX+2))
		self.elements.append(textline(_('Please check all settings carefully. During the next'), self.minY+1, self.minX+2))
		self.elements.append(textline(_('phase software packages will be installed and'), self.minY+2, self.minX+2))
		self.elements.append(textline(_('(pre-)configured.'), self.minY+3, self.minX+2))

		head = _("System role") + ":"
		self.elements.append(textline('%s %s' % (head.ljust(just), role) , self.minY+5, self.minX+2))
		head = _('Hostname') + ":"
		self.elements.append(textline('%s %s' % (head.ljust(just), self.all_results['hostname']) , self.minY+6, self.minX+2))
		head = _('Domain name') + ":"
		self.elements.append(textline('%s %s' % (head.ljust(just), self.all_results['domainname']) , self.minY+7, self.minX+2))
		count=2
		if self.all_results.has_key('eth0_type') and self.all_results['eth0_type'] == 'dynamic':
			head = _("eth0 Network") + ":"
			self.elements.append(textline('%s %s' % (head.ljust(just), _('dynamic')), self.minY+9, self.minX+2))
		else:
			head = _("eth0 IP") + ":"
			self.elements.append(textline('%s %s' % (head.ljust(just), self.all_results['eth0_ip']) , self.minY+9, self.minX+2))
			head = _("eth0 netmask") + ":"
			self.elements.append(textline('%s %s' % (head.ljust(just), self.all_results['eth0_netmask']) , self.minY+10, self.minX+2))
			count=count+1

		gateway=''
		if self.all_results.has_key('gateway'):
			gateway=self.all_results['gateway']
		head = _("Gateway") + ":"
		self.elements.append(textline('%s %s' % (head.ljust(just), gateway) , self.minY+8+count, self.minX+2))
		nameserver=''
		if self.all_results.has_key('nameserver_1'):
			nameserver=self.all_results['nameserver_1']
		head = _('Nameserver1') + ":"
		self.elements.append(textline('%s %s' % (head.ljust(just), nameserver) , self.minY+9+count, self.minX+2))

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
				self.elements.append(textline(_('%s will download files.') % p , self.minY+11+count, self.minX+2))
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

	def profileheader(self):
		return 'Overview'

	def result(self):
		result={}
		return result
