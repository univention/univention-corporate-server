#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
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

MAXLENGTH = 65

def ljust_utf8(msg, just):
	return msg.decode('utf-8').ljust(just).encode('utf-8')


class object(content):
	def checkname(self):
		return ['']

	def modvars(self):
		return ['']

	def depends(self):
		return {}

	def layout(self):
		self.debug('OVERVIEW: layout()')
		self.debug('OVERVIEW: all_results=%r' % self.all_results)

		self.reset_layout()

		self.std_button()

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

		self.all_results['packages'] = ''

		msg = _('This is the last step of the interactive installation. Please check all settings carefully. During the next phase software packages will be installed and (pre-)configured.')
		self.add_elem('TextArea', textarea(msg, self.minY-11, self.minX+5, 5, MAXLENGTH))
		linecnt = self.minY - 11 + self.get_elem('TextArea').get_number_of_lines()

		just=21
		ifjust=19

		linecnt += 1
		head = _("System role") + ":"
		self.elements.append(textline('%s %s' % (ljust_utf8(head, just), role), linecnt, self.minX+5))

		linecnt += 1
		head = _('Hostname') + ":"
		self.elements.append(textline('%s %s' % (ljust_utf8(head, just), self.all_results['hostname']), linecnt, self.minX+5, width=MAXLENGTH))

		linecnt += 1
		head = _('Domain name') + ":"
		self.elements.append(textline('%s %s' % (ljust_utf8(head, just), self.all_results['domainname']), linecnt, self.minX+5, width=MAXLENGTH))

		linecnt += 2
		self.add_elem('TXT1', textline( _('Settings of interface eth0:'), linecnt, self.minX+5))

		head = _("IPv4 address") + ":"
		if self.all_results.has_key('eth0_type') and self.all_results['eth0_type'] == 'dynamic':
			linecnt += 1
			self.elements.append(textline('%s %s' % (ljust_utf8(head, ifjust), _('configuration via DHCP')), linecnt, self.minX+7, width=MAXLENGTH))
		else:
			if self.all_results.get('eth0_ip'):
				linecnt += 1
				self.elements.append(textline('%s %s' % (ljust_utf8(head, ifjust), self.all_results['eth0_ip']), linecnt, self.minX+7, width=MAXLENGTH))

				linecnt += 1
				head = _("IPv4 netmask") + ":"
				self.elements.append(textline('%s %s' % (ljust_utf8(head, ifjust), self.all_results['eth0_netmask']), linecnt, self.minX+7, width=MAXLENGTH))

		head = _("IPv6 address") + ":"
		if self.all_results.get('eth0_acceptra') in ['true']:
			linecnt += 1
			self.elements.append(textline('%s %s' % (ljust_utf8(head, ifjust), _('configuration via SLAAC')), linecnt, self.minX+7, width=MAXLENGTH))
		else:
			if self.all_results.get('eth0_ip6') and self.all_results.get('eth0_prefix6'):
				linecnt += 1
				self.elements.append(textline('%s %s/%s' % (ljust_utf8(head, ifjust), self.all_results['eth0_ip6'], self.all_results['eth0_prefix6']), linecnt, self.minX+7, width=MAXLENGTH))

		linecnt += 1

		gateway = self.all_results.get('gateway')
		if gateway:
			linecnt += 1
			head = _("IPv4 Gateway") + ":"
			self.elements.append(textline('%s %s' % (ljust_utf8(head, just), gateway) , linecnt, self.minX+5, width=MAXLENGTH))

		gateway6 = self.all_results.get('gateway6')
		if gateway6:
			linecnt += 1
			head = _("IPv6 Gateway") + ":"
			self.elements.append(textline('%s %s' % (ljust_utf8(head, just), gateway6) , linecnt, self.minX+5, width=MAXLENGTH))

		nameserver = self.all_results.get('nameserver_1')
		if nameserver:
			linecnt += 1
			head = _('Domain DNS Server') + ":"
			self.elements.append(textline('%s %s' % (ljust_utf8(head, just), nameserver) , linecnt, self.minX+5, width=MAXLENGTH))

		extnameserver = self.all_results.get('dns_forwarder_1')
		if extnameserver:
			linecnt += 1
			head = _('External DNS Server') + ":"
			self.elements.append(textline('%s %s' % (ljust_utf8(head, just), extnameserver) , linecnt, self.minX+5, width=MAXLENGTH))

		linecnt += 2
		cb_val = {_('Update system after installation'): ['update_system_after_installation', 0]}
		cb_selection = [0]
		self.add_elem('CB_UPDATE', checkbox(cb_val, linecnt, self.minX+5, 55, 2, cb_selection))

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
		# If checkbox is off, the result of CB_UPDATE is empty, otherwise CB_UPDATE returns 'update_system_after_installation'
		# The return value gets converted to 'true' or 'false'
		result['update_system_after_installation'] = str(bool(self.get_elem('CB_UPDATE').result())).lower()
		return result
