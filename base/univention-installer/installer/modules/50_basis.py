#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: base configuration
#
# Copyright (C) 2004-2012 Univention GmbH
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
import string
import re


class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.hostname_last_warning = ''
		self.domainname_last_warning = ''
		self.windomain_last_warning = ''
		self.guessed = {}
		content.__init__(self, max_y, max_x, last, file, cmdline)
		self.interactive=False
		self.oxae = (self.cmdline.get('edition') and self.cmdline['edition'][0] == 'oxae')

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
			self.message=self.check_values(
				self.all_results['hostname'],
				self.all_results['domainname'],
				self.all_results['ox_primary_maildomain'],
				self.all_results['windows_domain'],
				self.all_results['ldap_base'],
				"XXXXXXXXXX",
				"XXXXXXXXXX",
				focus=False)
		else:
			self.message=self.check_values(
				self.all_results['hostname'],
				self.all_results['domainname'],
				self.all_results['ox_primary_maildomain'],
				self.all_results['windows_domain'],
				self.all_results['ldap_base'],
				self.all_results['root_password'],
				self.all_results['root_password'],
				focus=False)
		if self.message:
			return False

		if self.all_results.has_key('ldap_base') and self.all_results['ldap_base']:
			self.guessed[ 'ldap_base' ] = self.all_results['ldap_base']+'already_initialize'

		return True

	def modvars(self):
		return ['hostname','domainname','ldap_base','root_password', 'windows_domain', 'ox_primary_maildomain']

	def depends(self):
		return {'system_role':['ldap_base', 'hostname']}

	def layout(self):
		self.oxae = (self.cmdline.get('edition') and self.cmdline['edition'][0] == 'oxae')

		index = -11

		fqdn = ''
		if self.all_results['hostname'] or self.all_results['domainname']:
			fqdn = '%s.%s' % (self.all_results['hostname'], self.all_results['domainname'])

		# fqdn
		self.add_elem('TXT_FQDN',
			textline(_('Fully qualified domain name (e.g. host.example.com):'), self.minY+index, self.minX+5))#2
		index += 1
		self.add_elem('IN_FQDN', input(fqdn, self.minY+index, self.minX+5,30))#3
		index += 2

		# oxae maildomain
		if self.oxae:
			self.add_elem('TXT_MAILDOMAIN',
				textline(_('Mail domain (e.g. example.com):'), self.minY+index, self.minX+5))#4
			index += 1
			self.add_elem('IN_MAILDOMAIN',
				input(self.all_results.get('ox_primary_maildomain',''), self.minY+index, self.minX+5,30))#5
			index += 2

		# ucs ldap base
		if self.all_results.has_key('system_role') and self.all_results['system_role'] == 'domaincontroller_master':
			if not self.oxae:
				self.add_elem('TXT_LDAPBASE',
					textline(_('LDAP base:'), self.minY+index, self.minX+5))#6
				index += 1
				self.add_elem('IN_LDAPBASE',
					input(self.all_results['ldap_base'], self.minY+index, self.minX+5,30))#7
				index += 2
				if self.all_results.has_key('ldap_base') and self.all_results['ldap_base']:
					self.guessed[ 'ldap_base' ] = self.all_results['ldap_base']+'already_initialize'

		# windom
		self.add_elem('TXT_WINDOMAIN', textline(_('Windows domain name:'), self.minY+index, self.minX+5))#8
		index += 1
		self.add_elem('IN_WINDOMAIN', input(self.all_results['windows_domain'], self.minY+index, self.minX+5,30))#9
		index += 2
		if self.all_results.has_key('windows_domain') and self.all_results['windows_domain']:
			self.guessed[ 'windows_domain' ] = self.all_results['windows_domain']+'already_initialize'

		# password
		self.add_elem('TXT_ROOTPW1', textline(_('Root password:'),self.minY+index,self.minX+5)) #10
		index += 1
		self.add_elem('IN_ROOTPW1', password(self.all_results['root_password'],self.minY+index,self.minX+5,30)) #11
		index += 2

		self.add_elem('TXT_ROOTPW2', textline(_('Root password (retype):'),self.minY+index,self.minX+5)) #12
		index += 1
		self.add_elem('IN_ROOTPW2', password(self.all_results['root_password'],self.minY+index,self.minX+5,30)) #13
		index += 1

	def tab(self):
		# fqdn
		if self.current == self.get_elem_id('IN_FQDN'):
			elem_fqdn = self.get_elem('IN_FQDN')
			if len(elem_fqdn.text) and not elem_fqdn.text.islower():
				text = elem_fqdn.text.lower()
				self.guessed['fqdn'] = text
				elem_fqdn.text = text
				elem_fqdn.cursor=len(text)
				elem_fqdn.set_off()
				elem_fqdn.draw()
				self.draw()
			if elem_fqdn.text:

				# IF oxmaildomain is not set OR oxmaildomain has not been guessed yet
				# OR oxmaildomain is currently equal to guessed oxmaildomain THEN
				if self.oxae:
					fqdn = elem_fqdn.text

					elem_oxmaildomain = self.get_elem('IN_MAILDOMAIN')
					if not len(elem_oxmaildomain.text) or not self.guessed.has_key('ox_primary_maildomain') \
					or self.guessed['ox_primary_maildomain'] == elem_oxmaildomain.text:
						if '.' in fqdn:
							oxmaildomain = fqdn[fqdn.find('.')+1:]
							self.guessed[ 'ox_primary_maildomain' ] = oxmaildomain
							elem_oxmaildomain.text = oxmaildomain
							elem_oxmaildomain.cursor=len(oxmaildomain)
							elem_oxmaildomain.set_off()
							elem_oxmaildomain.draw()
							self.draw()
				# ucs
				else:

					fqdn = elem_fqdn.text
					# master -> ldapbase
					if self.all_results.has_key( 'system_role' ) and \
					self.all_results['system_role'] == 'domaincontroller_master':
						element = self.get_elem('IN_LDAPBASE')
						if not len(element.text) or not self.guessed.has_key('ldap_base') \
						or self.guessed['ldap_base'] == element.text:
							if '.' in fqdn:
								dom = fqdn[fqdn.find('.')+1:]
								if dom:
									base = "dc=" + string.join(dom.split( '.' ), ',dc=').lower()
									self.guessed['ldap_base'] = base
									element.text = base
									element.cursor=len(base)
									element.set_off()
									element.draw()
									self.draw()
					# rest -> win dom
					else:
						element = self.get_elem('IN_WINDOMAIN')
						if not len(element.text) or not self.guessed.has_key('windows_domain') \
						or self.guessed['windows_domain'] == element.text:
							if '.' in fqdn:
								tmp = fqdn.split('.')
								if len(tmp) > 0:
									text = tmp[1].upper()
									text = re.sub("^\d*", "", text)
									self.guessed['windows_domain'] = text
									element.text = text
									element.cursor=len(text)
									element.set_off()
									element.draw()
									self.draw()

		# win dom for ucs master and oxae
		elem_id = "IN_LDAPBASE"
		if self.oxae:
			elem_id = "IN_MAILDOMAIN"
		if self.all_results.has_key( 'system_role' ) and \
		self.all_results['system_role'] == 'domaincontroller_master':
			if self.current == self.get_elem_id(elem_id):
				elem_fqdn = self.get_elem('IN_FQDN')
				element = self.get_elem("IN_WINDOMAIN")
				if not len(element.text) or not self.guessed.has_key('windows_domain') \
				or self.guessed['windows_domain'] == element.text:
					fqdn = elem_fqdn.text
					if fqdn and "." in fqdn:
						tmp = fqdn.split('.')
						if len(tmp) > 0:
							text = tmp[1].upper()
							text = re.sub("^\d*", "", text)
							self.guessed['windows_domain'] = text
							element.text = text
							element.cursor=len(text)
							element.set_off()
							element.draw()
							self.draw()

		# upper case win dom
		if self.current == self.get_elem_id('IN_WINDOMAIN'):
			elem = self.get_elem('IN_WINDOMAIN')
			if len(elem.text) and not elem.text.isupper():
				text = elem.text.upper()
				self.guessed[ 'windows_domain' ] = text
				elem.text = text
				elem.cursor=len(text)
				elem.set_off()
				elem.draw()
				self.draw()
		content.tab(self)

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.get_elem_by_id(self.current).key_event(key)

	def check_values (self, hostname, domainname, oxmaildomain, windows_domain, ldap_base, root_password1, root_password2, focus=True):
		if not windows_domain.strip() == '':
			if not self.syntax_is_windowsdomainname(windows_domain.lower()) or not windows_domain == windows_domain.upper():
				if not self.ignore('windows_domain'):
					if focus:
						self.move_focus( self.get_elem_id('IN_WINDOMAIN') )
					return _("Please enter a valid windows domain name.")

		if len(windows_domain.strip()) > 14:
			if not self.ignore('windows_domain'):
				if focus:
					self.move_focus( self.get_elem_id('IN_WINDOMAIN') )
				return _("The length of the windows domain name is greater than 14 characters.")

		# no . in windom
		if not windows_domain.find(".") == -1:
			if not self.ignore('windows_domain'):
				if focus:
					self.move_focus( self.get_elem_id('IN_WINDOMAIN') )
				return _("Periods are not allowed in windows domain names.")

		# windom != dns
		if windows_domain.strip().lower() == domainname.strip().lower():
			if not self.ignore('windows_domain'):
				if focus:
					self.move_focus( self.get_elem_id('IN_WINDOMAIN') )
				return _("The windows domain and the domain name may not be the same.")

		if windows_domain.strip().lower() == hostname.strip().lower():
			if not self.ignore('windows_domain'):
				# The warning will be displayed only once
				if windows_domain != self.windomain_last_warning:
					self.windomain_last_warning = windows_domain
					if focus:
						self.move_focus( self.get_elem_id('IN_WINDOMAIN') )
					return _("For Active Directory domains the hostname and the windows domain name may not be the same. This warning is shown only once, the installation can be continued with the name currently given.")

		if hostname.strip() == '' or hostname.strip() in ['localhost', 'local'] or hostname.strip().find(' ') != -1 or not self.syntax_is_hostname(hostname):
			if not self.ignore('hostname'):
				if focus:
					self.move_focus( self.get_elem_id('IN_FQDN') )
				return _("Please enter a valid fully qualified domain name in lowercase (e.g. host.example.com).")

		if len(hostname) > 13:
			# The warning will be displayed only once
			if hostname != self.hostname_last_warning:
				self.hostname_last_warning = hostname
				return _("A valid netbios name can not be longer than 13 characters. If samba is installed, the hostname should be shortened.")

		if self.oxae:
			if oxmaildomain.strip() == '' or oxmaildomain.strip().find(' ') != -1 or not self.syntax_is_domainname(oxmaildomain):
				if not self.ignore('ox_primary_maildomain'):
					if focus:
						self.move_focus( self.get_elem_id('IN_MAILDOMAIN') )
					return _("Please enter a valid mail domain in lowercase (e.g. example.com).")

		if domainname.strip() == '' or domainname.strip().find(' ') != -1 or not self.syntax_is_domainname(domainname):
			if not self.ignore('domainname'):
				if focus:
					self.move_focus( self.get_elem_id('IN_FQDN') )
				return _("Please enter a valid fully qualified domain name in lowercase (e.g. host.example.com).")

		if domainname.find('.') == -1:
			if not self.ignore('domainname'):
				# The warning will be displayed only once
				if domainname != self.domainname_last_warning:
					self.domainname_last_warning = domainname
					if focus:
						self.move_focus( self.get_elem_id('IN_FQDN') )
					return _("For Active Directory domains the fully qualified domain name must have at least two dots (e.g. host.example.com). This warning is shown only once, the installation can be continued with the name currently given.")

		if len(hostname.strip()+domainname.strip()) >= 63:
			if not self.ignore('hostname') and not self.ignore('domainname'):
				if focus:
					self.move_focus( self.get_elem_id('IN_FQDN') )
				return _('The length of fully qualified domain name is greater than 63 characters.')

		if hostname.strip() == domainname.strip().split('.')[0]:
			if not self.ignore('hostname') and not self.ignore('domainname'):
				if focus:
					self.move_focus( self.get_elem_id('IN_FQDN') )
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
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Please enter a Password.")
			if root_password2.strip() == '':
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW2') )
					return _("Please retype the Password.")
			if root_password1.strip() != root_password2.strip():
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Passwords do not match.")
			if len(root_password1.strip()) < 8:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Your password is too short. For security reasons, your password must contain at least 8 characters.")
			try:
				root_password1.strip().decode("ascii")
			except:
				return _("Illegal password: A password may only contain ascii characters.")

			if root_password1.strip().find(" ") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Illegal password: A password may not contain blanks.")
			if root_password2.strip().find(" ") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW2') )
					return _("Illegal password: A password may not contain blanks.")
			if root_password1.strip().find('\\') != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Illegal password: A password may not contain back slashes.")
			if root_password2.strip().find('\\') != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW2') )
					return _("Illegal password: A password may not contain back slashes.")
			if root_password1.strip().find('"') != -1 or root_password1.strip().find("'") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW1') )
					return _("Illegal password: A password may not contain quotation marks.")
			if root_password2.strip().find('"') != -1 or root_password2.strip().find("'") != -1:
				if not self.ignore('password'):
					if focus:
						self.move_focus( self.get_elem_id('IN_ROOTPW2') )
					return _("Illegal password: A password may not contain quotation marks.")
		return 0

	def incomplete(self):
		ldap_base=''

		if '.' in self.get_elem('IN_FQDN').text:
			hostname, domainname = self.get_elem('IN_FQDN').result().strip().lower().split('.', 1)
		else:
			hostname = self.get_elem('IN_FQDN').result().strip().lower()
			domainname = ''

		if self.oxae:
			oxmaildomain = self.get_elem('IN_MAILDOMAIN').result()
			if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
				ldap_base = "dc=" + ',dc='.join( self.get_elem('IN_MAILDOMAIN').text.strip().lower().split( '.' ) )
		else:
			oxmaildomain = ''
			if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
				ldap_base=self.get_elem('IN_LDAPBASE').result()

		windomain = self.get_elem('IN_WINDOMAIN').result()

		if self.all_results.has_key('root_password_crypted'):
			root_password1='XXXXXXXXXX'
			root_password2='XXXXXXXXXX'
		else:
			root_password1=self.get_elem('IN_ROOTPW1').result()
			root_password2=self.get_elem('IN_ROOTPW2').result()
		return self.check_values(hostname, domainname, oxmaildomain, windomain, ldap_base, root_password1, root_password2)

	def helptext(self):
		if self.oxae:
			return _('Settings  \n \n Configuration of basic system settings like fully qualified domain name, mail domain, windows domain and root password.')
		else:
			return _('Settings  \n \n Configuration of basic system settings like hostname, domain name and LDAP base and root password.')

	def modheader(self):
		return _('Settings')

	def profileheader(self):
		return 'Settings'

	def result(self):
		result={}
		if self.oxae:
			result['ox_primary_maildomain'] = self.get_elem('IN_MAILDOMAIN').result().strip().lower()

		hostname, domainname = self.get_elem('IN_FQDN').result().strip().lower().split('.', 1)
		result['fqdn'] = self.get_elem('IN_FQDN').result().strip().lower()
		result['hostname'] = hostname
		result['domainname'] = domainname

		if self.all_results.has_key( 'system_role' ) and self.all_results['system_role'] == 'domaincontroller_master':
			if self.oxae:
				result['ldap_base'] ="dc=" + ',dc='.join( self.get_elem('IN_MAILDOMAIN').text.strip().lower().split( '.' ) )
			else:
				result['ldap_base']='%s' % self.get_elem('IN_LDAPBASE').result().strip()

		result['windows_domain']='%s' % self.get_elem('IN_WINDOMAIN').result().strip().upper()

		if self.all_results.has_key('root_password_crypted'):
			result['root_password_crypted']=self.all_results['root_password_crypted']
		else:
			elempw1 = self.get_elem('IN_ROOTPW1')
			elempw2 = self.get_elem('IN_ROOTPW2')
			if elempw1.result().strip() == elempw2.result().strip() and len(elempw1.result().strip()) > 7:
				result['root_password']='%s' % elempw1.result().strip()

		return result
