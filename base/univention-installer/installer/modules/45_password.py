#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: password configuration
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
import os

class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		content.__init__(self, max_y, max_x, last, file, cmdline)
		self.interactive=False

	def checkname(self):
		return []

	def profile_complete(self):
		return True

	def modvars(self):
		return ['root_password']

	def depends(self):
		return {}

	def layout(self):
		index = -11

		if os.path.isfile('/usr/bin/xinit'):
			msg = _('''The graphical configuration frontend could not be started! To continue the reconfiguration of this system, a web browser is required.

You can access the configuration frontend by opening the following URL:

http://<ip address of this system>/umc/

After logging in as user "root",  select the module "System Setup".

The network settings (IP address) can be configured on next screen (press F12). To log in, the root password is required. If the password is unknown or should be changed, enter a new one below.

Hint: The network settings have to be confirmed before the system boot process will continue/the configuration frontend will be available.''')
		else:
			msg = _('''Currently no graphical frontend has been installed! To continue the reconfiguration of this system, a web browser is required.

You can access the configuration frontend by opening the following URL:

http://<ip address of this system>/umc/

After logging in as user "root",  select the module "System Setup".

The network settings (IP address) can be configured on next screen (press F12). To log in, the root password is required. If the password is unknown or should be changed, enter a new one below.

Hint: The network settings have to be confirmed before the system boot process will continue/the configuration frontend will be available.''')

		msglen = 22

		# description text
		self.add_elem('TEXTAREA1', textarea( msg, self.minY+index, self.minX+5, msglen, 65))

		index += msglen

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
		content.tab(self)

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.get_elem_by_id(self.current).key_event(key)

	def check_values (self, root_password1, root_password2, focus=True):
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

		if self.all_results.has_key('root_password_crypted'):
			root_password1='XXXXXXXXXX'
			root_password2='XXXXXXXXXX'
		else:
			root_password1=self.get_elem('IN_ROOTPW1').result()
			root_password2=self.get_elem('IN_ROOTPW2').result()
		return self.check_values(root_password1, root_password2)

	def helptext(self):
		return _('Password  \n \n Changing default root password into a custom one.')

	def modheader(self):
		return _('Password')

	def profileheader(self):
		return 'Password'

	def result(self):
		result={}

		if self.all_results.has_key('root_password_crypted'):
			result['root_password_crypted']=self.all_results['root_password_crypted']
		else:
			elempw1 = self.get_elem('IN_ROOTPW1')
			elempw2 = self.get_elem('IN_ROOTPW2')
			if elempw1.result().strip() == elempw2.result().strip() and len(elempw1.result().strip()) > 7:
				result['root_password']='%s' % elempw1.result().strip()

		return result
