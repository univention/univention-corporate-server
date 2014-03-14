#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system role selection
#
# Copyright 2004-2013 Univention GmbH
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

import curses
from objects import *
from local import _

MAXLENGTH=65

class object(content):
	def __init__(self, *args, **kwargs):
		content.__init__(self, *args, **kwargs)
		self.call_master_joinscripts = None
		self.basesystem_warning_shown = False

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

		self.elements.append(textline(_('Select the system role:'), self.minY-11, self.minX+5))#2
		dict={}
		dict[_('Master domain controller')]=['domaincontroller_master',0]
		dict[_('Backup domain controller')]=['domaincontroller_backup',1]
		dict[_('Slave domain controller')]=['domaincontroller_slave',2]
		dict[_('Member server')]=['memberserver',3]
		dict[_('Base system')]=['basesystem',4]

		list=['domaincontroller_master','domaincontroller_backup','domaincontroller_slave','memberserver','basesystem']
		select=0
		if self.all_results.has_key('system_role'):
			select=list.index(self.mapping(self.all_results['system_role']))

		self.add_elem('RADIO', radiobutton(dict,self.minY-9,self.minX+7,40,10,[select]))#3
		self.elements[3].current=select
		self.add_elem('TXT_DESCRIPTION', textline( _('Further information for selected system role:'), self.minY-3, self.minX+5))
		self.add_elem('TEXTAREA', dummy())
		self.add_elem('CALL_MASTER_JOINSCRIPTS', dummy())

		self.update_description()
		self.update_call_master_joinscripts()

	def update_call_master_joinscripts(self):
		selected_role = self.get_elem('RADIO').result()

		msg = ''
		if selected_role == 'domaincontroller_master':
			if self.call_master_joinscripts is None:
				msg = ''
			elif self.call_master_joinscripts:
				msg = _('Join scripts will be called during installation.')
			else:
				msg = _('Join scripts will not be called during installation.')

		idx = self.get_elem_id('CALL_MASTER_JOINSCRIPTS')
		self.elements[idx] = textline( msg, self.minY+17, self.minX+5 )

	def update_description(self):
		descriptions = {
			'domaincontroller_master': _('The domain controller master (DC master for short) contains the original dataset for the entire LDAP directory. Changes to the LDAP directory are only performed on this server. For this reason, this must be the first system to be commissioned and there can only be one of them within a domain. In addition, the Root Certification Authority (root CA) is also on the DC master. All SSL certificates created are archived on the DC master.'),
			'domaincontroller_backup': _('Servers with the role of domain controller backup (DC backup for short) contain a replicated copy of the entire LDAP directory, which cannot be changed as all write accesses occur exclusively on the DC master. A copy of all SSL certificates including the private key of the root CA is kept on the DC backup. The DC backup is as such a backup copy of the DC master.  If the DC master should collapse completely, running a special command allows the DC backup to take over the role of the DC master permanently in a very short time.'),
			'domaincontroller_slave': _('Each domain controller slave (DC slave for short) contains a replicated copy of the entire LDAP directory, which cannot be changed as all write accesses occur on the DC master. The copy can either contain the entire directory or be limited to the files required by a location through selective replication. The DC slave only stores a copy of its own and the public SSL certificate of the root CA. A DC slave system cannot be promoted to a DC master.'),
			'memberserver': _('Member servers are members of a LDAP domain and offer services such as file storage for the domain. Member servers do not contain a copy of the LDAP directory. It only stores a copy of its own and the public SSL certificate of the root CA.'),
			'basesystem': _('A base system is an independent system. It is not a member of a domain and does not offer any web based management functions. A base system is thus suitable for services which are operated outside of the trust context of the domain, such as a web server or a firewall. It is possible to configure DNS and DHCP settings for base systems via the Univention management system as long as the base system is entered as an IP managed client in the directory service.'),
			}

		# get current role
		selected_role = self.get_elem('RADIO').get_focus()[1]
		self.debug('ROLE: selected_role=%r' % selected_role)

		# overwrite existing textarea
		idx = self.get_elem_id('TEXTAREA')
		self.elements[idx] = textarea( descriptions.get(selected_role,'UNKNOWN'), self.minY-1, self.minX+6, 15, MAXLENGTH)

	def input(self,key):
		self.debug('key_event=%d' % key)
		if key in [10, 32] and self.btn_next():
			return 'next'
		elif key in [10,32] and self.btn_back():
			return 'prev'
		elif key == curses.KEY_F3:
			if self.call_master_joinscripts is None:
				self.call_master_joinscripts = False
			else:
				self.call_master_joinscripts = not(self.call_master_joinscripts)
			self.update_call_master_joinscripts()
			self.draw()
			return 1
		elif key in [10,32] and self.get_elem('RADIO').active:
			val = self.elements[self.current].key_event(key)
			self.update_call_master_joinscripts()
			self.update_description()
			self.draw()
			return val
		elif key in [curses.KEY_UP, curses.KEY_DOWN] and self.get_elem('RADIO').active:
			val = self.elements[self.current].key_event(key)
			self.update_description()
			self.draw()
			return val
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		selected_role = self.get_elem('RADIO').get_focus()[1]
		if selected_role == 'basesystem' and not self.basesystem_warning_shown:
			self.basesystem_warning_shown = True
			return _('A base system does not offer any web-based domain management functions and will not be able to be a domain member. A base system should only be used in some rare use cases, for example as firewall system. This warning is shown only once, the installation can be continued as base system.')
		return 0

	def helptext(self):
		return _('System role \n \n Select a system role. Depending on the system role different components will be installed. \n \n Master domain controller: \n This system keeps the whole LDAP tree and is the core of your UCS domain. \n \n Backup domain controller: \n This system keeps a copy of the complete LDAP structure, which cannot be changed manually. \n \n Slave domain controller: \n This system includes required LDAP data for a special purpose (i.e. location based). \n \n Member server: \n Member of a domain offering specified domainwide services like printing or backup. No LDAP data is stored on such a system. \n \n Base system: \n A stand-alone server solution for web-server or firewall for example. This system is not a member of any domain.')

	def modheader(self):
		return _('System role')

	def profileheader(self):
		return 'System role'

	def result(self):
		if self.call_master_joinscripts is None:
			# default is to call join scripts
			self.call_master_joinscripts = True

		return {'system_role': self.elements[3].result(),
				'call_master_joinscripts': str(bool(self.call_master_joinscripts)).lower(),
				}
