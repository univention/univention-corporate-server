#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: security settings
#
# Copyright (C) 2007 Univention GmbH
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
		return ['security_profile']

	def modvars(self):
		return ['security_profile']

	def mod_depends(self):
		return {'system_role': ['domaincontroller_master', 'domaincontroller_backup','domaincontroller_slave','memberserver','basesystem','managed_client','mobile_client'] }

	def depends(self):
		return {}

 	def mapping(self,value):
		if value in ['normal','Normal']:
			return 'normal'
		elif value in ['strict','Strict']:
			return 'strict'
		elif value in ['open','Open']:
			return 'open'

	def profile_complete(self):
		if self.check('security_profile'):
			return False
		return True

	def layout(self):
		self.reset_layout()
		self.add_elem('security_profile_label0', textline(_('Activate filtering of system services:'), self.minY+1, self.minX+2))
		self.add_elem('security_profile_label1', textline(_('These options control how many system services are'), self.minY+2, self.minX+2))
		self.add_elem('security_profile_label2', textline(_('initially blocked by a packet filter (iptables):'), self.minY+3, self.minX+2))
		self.add_elem('security_profile_label3', textline(_('strict: Only SSH and HTTPS are allowed. This is only'), self.minY+4, self.minX+2))
		self.add_elem('security_profile_label4', textline(_('        intended for an initial, locked-down setup.'), self.minY+5, self.minX+2))
		self.add_elem('security_profile_label6', textline(_('normal: Typical selection of services, recommended'), self.minY+6, self.minX+2))
		self.add_elem('security_profile_label7', textline(_('open  : No service is filtered'), self.minY+7, self.minX+2))

		dict={}
		dict['Open']=['open',0]
		dict['Normal']=['normal',1]
		dict['Strict']=['strict',2]

		list=['normal','strict','open']
		select=1

		if self.all_results.has_key('security/profile'):
			if self.all_results['security/profile'] == "open":
				select = 0
			elif self.all_results['security/profile'] == "strict":
				select = 2
		
		self.add_elem('security_profile_radio', radiobutton(dict,self.minY+9,self.minX+2,40,10,[select]))
		self.get_elem('security_profile_radio').current = select

		self.add_elem('BT_back', button(_('F11-Back'),self.minY+18,self.minX))
		self.add_elem('BT_next', button(_('F12-Next'),self.minY+18,self.minX+(self.width)-37))

		self.current = self.get_elem_id('security_profile_radio')

	def input(self,key):

		if key in [ 10, 32 ] and self.get_elem('BT_back').get_status():
			return 'prev'

		elif key in [ 10, 32 ] and self.get_elem('BT_next').get_status():
			return 'next'

#		elif key in [ 10, 32 ] and self.get_elem('security_profile_radio').get_status() and self.get_elem('security_profile_radio').result() == 2:
#			msglist= [ _('This option is only intended for!'),
#				   _('an initial locked-down system setup.'),
#				   _('For a fully functional system you will'),
#				   _('need to enable further services.') ]
#			self.sub=msg_win(self.sub, self.sub.minY+(self.sub.maxHeight/8)+2,self.sub.minX+(self.sub.maxWidth/8),1,1, msglist)
#			self.sub.draw()
		else:
			return self.get_elem_by_id(self.current).key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return _('Security Settings  \n \n Pre-defined packet filter configuration options for various system roles')

	def modheader(self):
		return _('Security Settings')

	def result(self):
		result={}

		if self.get_elem('security_profile_radio').result() == 'open':
			result['security_profile'] = 'open'
		elif self.get_elem('security_profile_radio').result() == 'normal':
			result['security_profile'] = 'normal'
		elif self.get_elem('security_profile_radio').result() == 'strict':
			result['security_profile'] = 'strict'

		return result
