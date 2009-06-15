#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: base configuration
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
import string

class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.guessed = {}
		content.__init__(self, max_y, max_x, last, file, cmdline)
		self.interactive=False

	def checkname(self):
		return ['hostname','domainname','ldap_base']

	def profile_complete(self):

		if self.interactive:
			self.message=self.incomplete()
			if self.message:
				return False
			else:
				return True

		#self.interactive=False

		if self.check('hostname') | self.check('domainname') | self.check('ldap_base') | self.check( 'windows_domain'):
			return False
		if self.check('root_password') and self.check('root_password_crypted'):
			return False
		if self.all_results.has_key('root_password_crypted'):
			self.message=self.check_values(self.all_results['hostname'], self.all_results['domainname'], self.all_results['windows_domain'], self.all_results['ldap_base'], "XXXXXXXXXX", "XXXXXXXXXX", focus=False)
		else:
			self.message=self.check_values(self.all_results['hostname'], self.all_results['domainname'], self.all_results['windows_domain'], self.all_results['ldap_base'], self.all_results['root_password'], self.all_results['root_password'], focus=False)
		if self.message:
			return False

		if self.all_results.has_key('ldap_base') and self.all_results['ldap_base']:
			self.guessed[ 'ldap_base' ] = self.all_results['ldap_base']+'already_initialize'

		return True

	def modvars(self):
		return ['hostname','domainname','ldap_base','root_password', 'windows_domain']

	def depends(self):
		return {'system_role':['ldap_base', 'hostname']}

	def layout(self):
		self.elements.append(textline(_('Hostname:'), self.minY, self.minX+2))#2
		self.elements.append(input(self.all_results['hostname'], self.minY+1, self.minX+2,30))#3

		self.elements.append(textline(_('Domain name:'), self.minY+3, self.minX+2))#4
		self.elements.append(input(self.all_results['domainname'], self.minY+4, self.minX+2,30))#5

		if self.all_results.has_key('system_role') and self.all_results['system_role'] == 'domaincontroller_master':
			self.append_spaces=3
			self.elements.append(textline(_('LDAP base:'), self.minY+6, self.minX+2))#6
			self.elements.append(input(self.all_results['ldap_base'], self.minY+7, self.minX+2,30))#7
			if self.all_results.has_key('ldap_base') and self.all_results['ldap_base']:
				self.guessed[ 'ldap_base' ] = self.all_results['ldap_base']+'already_initialize'
		else:
			self.append_spaces=0

		self.elements.append(textline(_('Windows domain:'), self.minY+6+int(self.append_spaces), self.minX+2))#8
		self.elements.append(input(self.all_results['windows_domain'], self.minY+7+int(self.append_spaces), self.minX+2,30))#9
		if self.all_results.has_key('windows_domain') and self.all_results['windows_domain']:
			self.guessed[ 'windows_domain' ] = self.all_results['windows_domain']+'already_initialize'

		self.elements.append(textline(_('Root password:'),self.minY+9+int(self.append_spaces),self.minX+2)) #10
		self.elements.append(password(self.all_results['root_password'],self.minY+10+int(self.append_spaces),self.minX+2,30)) #11

		self.elements.append(textline(_('Root password (retype):'),self.minY+12+int(self.append_spaces),self.minX+2)) #12
		self.elements.append(password(self.all_results['root_password'],self.minY+13+int(self.append_spaces),self.minX+2,30)) #13

	def tab(self):
		if self.current == 3:
			if len(self.elements[3].text) and not self.elements[3].text.islower():
				text = self.elements[3].text.lower()
				self.guessed[ 'hostname' ] = text
				self.elements[3].text = text
				self.elements[3].cursor=len(text)
				self.elements[3].set_off()
				self.elements[3].draw()
				self.draw()
		if self.current == 5:
			if len(self.elements[5].text):
				pos=7
				if  self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
					pos=9
				if not len(self.elements[pos].text) or not self.guessed.has_key( 'windows_domain' ) or self.guessed[ 'windows_domain' ] == self.elements[ pos ].text:
					text = self.elements[5].text.split('.')[0].upper()
					self.guessed[ 'windows_domain' ] = text
					self.elements[pos].text = text
					self.elements[pos].cursor=len(text)
					self.elements[pos].set_off()
					self.elements[pos].draw()
					self.draw()
				if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
					if not len(self.elements[7].text) or not self.guessed.has_key( 'ldap_base' ) or self.guessed[ 'ldap_base' ] == self.elements[ 7 ].text:
						text = "dc=" + string.join( self.elements[ 5 ].text.split( '.' ), ',dc=' ).lower()
						self.guessed[ 'ldap_base' ] = text
						self.elements[7].text = text
						self.elements[7].cursor=len(text)
						self.elements[7].set_off()
						self.elements[7].draw()
						self.draw()
				if not self.elements[5].text.islower():
					text = self.elements[5].text.lower()
					self.guessed[ 'domainname' ] = text
					self.elements[5].text = text
					self.elements[5].cursor=len(text)
					self.elements[5].set_off()
					self.elements[5].draw()
					self.draw()
		if  self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			pos_windows_domain=9
		else:
			pos_windows_domain=7
		if self.current == pos_windows_domain:
			if len(self.elements[pos_windows_domain].text) and not self.elements[pos_windows_domain].text.isupper():
				text = self.elements[pos_windows_domain].text.upper()
				self.guessed[ 'windows_domain' ] = text
				self.elements[pos_windows_domain].text = text
				self.elements[pos_windows_domain].cursor=len(text)
				self.elements[pos_windows_domain].set_off()
				self.elements[pos_windows_domain].draw()
				self.draw()
		content.tab(self)


	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def check_values (self, hostname, domainname, windows_domain, ldap_base, root_password1, root_password2, focus=True):
		if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			password1_position=11
			password2_position=13
			windows_domain_position=9
		else:
			windows_domain_position=7
			password1_position=9
			password2_position=11

		if not windows_domain.strip() == '':
			if not self.syntax_is_domainname(windows_domain.lower()) or not windows_domain == windows_domain.upper():
				if not self.ignore('windows_domain'):
					if focus:
						self.move_focus(windows_domain_position)
					return _("Please enter a valid windows domain name.")
			
		if hostname.strip() == '' or hostname.strip() in ['localhost', 'local'] or hostname.strip().find(' ') != -1 or not self.syntax_is_hostname(hostname):
			if not self.ignore('hostname'):
				if focus:
					self.move_focus( 3 )
				return _("Please enter a valid hostname in lowercase.")
		if domainname.strip() == '' or domainname.strip().find(' ') != -1 or not self.syntax_is_domainname(domainname):
			if not self.ignore('domainname'):
				if focus:
					self.move_focus( 5 )
				return _("Please enter a valid domain name in lowercase.")
		if len(hostname.strip()+domainname.strip()) >= 64:
			if not self.ignore('hostname') and not self.ignore('domainname'):
				if focus:
					self.move_focus( 3 )
				return _('The length of host and domain name is greater then 64.')
		if hostname.strip() == domainname.strip().split('.')[0]:
			if not self.ignore('hostname') and not self.ignore('domainname'):
				if focus:
					self.move_focus( 5 )
				return _("Hostname is equal to domain name.")
		if (ldap_base.strip() == '') and (self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master'):
			if not self.ignore('ldap_base'):
				if focus:
					self.move_focus( 7 )
				return _("Please enter the LDAP base.")
		if (ldap_base.strip() != '') and ((self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master')) or ldap_base.strip().find(' ') != -1:

			if not self.ignore('ldap_base'):
				message=_("Syntax-Error. Please enter a LDAP base according to this format: dc=test,dc=net ")
				for dc in ldap_base.strip().split(','):
					if len(dc.split('='))>2:
						if focus:
							self.move_focus( 7 )
						return message
					elif not dc.split('=')[0] in ['dc', 'cn', 'c', 'o', 'l']:
						if focus:
							self.move_focus( 7 )
						return message
				if ldap_base.strip().find(' ') != -1:
					if focus:
						self.move_focus( 7 )
					return message
		if not self.all_results.has_key('root_password_crypted'):
			if root_password1.strip() == '':
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Please enter a Password.")
			if root_password2.strip() == '':
				if not self.ignore('password'):
					if focus:
						self.move_focus( password2_position )
					return _("Please retype the Password.")
			if root_password1.strip() != root_password2.strip():
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Passwords do not match.")
			if len(root_password1.strip()) < 8:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Your password is too short. For security reasons, your password must contain at least 8 characters.")
			if root_password1.strip().find(" ") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Illegal password: A password may not contain blanks.")
			if root_password2.strip().find(" ") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password2_position )
					return _("Illegal password: A password may not contain blanks.")
			if root_password1.strip().find('\\') != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Illegal password: A password may not contain back slashes.")
			if root_password2.strip().find('\\') != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password2_position )
					return _("Illegal password: A password may not contain back slashes.")
			if root_password1.strip().find('"') != -1 or root_password1.strip().find("'") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password1_position )
					return _("Illegal password: A password may not contain quotation marks.")
			if root_password2.strip().find('"') != -1 or root_password2.strip().find("'") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( password2_position )
					return _("Illegal password: A password may not contain quotation marks.")
		return 0


	def incomplete(self):
		if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			ldap_base=self.elements[7].result()
			windows_domain_position=9
		else:
			ldap_base=''
			windows_domain_position=7
		if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			password1_position=11
			password2_position=13
		else:
			password1_position=9
			password2_position=11
		if self.all_results.has_key('root_password_crypted'):
			root_password1='XXXXXXXXXX'
			root_password2='XXXXXXXXXX'
		else:
			root_password1=self.elements[password1_position].result()
			root_password2=self.elements[password2_position].result()
		return self.check_values(self.elements[3].result(), self.elements[5].result(), self.elements[windows_domain_position].result(), ldap_base, root_password1, root_password2)

	def helptext(self):
		return _('Settings  \n \n Configuration of basic system settings like hostname, domain name and LDAP base and root password')

	def modheader(self):
		return _('Settings')

	def result(self):
		result={}
		result['hostname']='%s' % self.elements[3].result().strip().lower()
		result['domainname']='%s' % self.elements[5].result().strip().lower()
		if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			result['ldap_base']='%s' % self.elements[7].result().strip()
			result['windows_domain']='%s' % self.elements[9].result().strip().upper()
			if self.all_results.has_key('root_password_crypted'):
				result['root_password_crypted']=self.all_results['root_password_crypted']
			else:
				if self.elements[11].result().strip() == self.elements[13].result().strip() and len(self.elements[11].result().strip()) >7:
					result['root_password']='%s' % self.elements[11].result().strip()
		else:
			result['windows_domain']='%s' % self.elements[7].result().strip().upper()
			if self.all_results.has_key('root_password_crypted'):
				result['root_password_crypted']=self.all_results['root_password_crypted']
			else:
				if self.elements[9].result().strip() == self.elements[11].result().strip() and len(self.elements[9].result().strip()) > 7:
					result['root_password']='%s' % self.elements[9].result().strip()
		return result
