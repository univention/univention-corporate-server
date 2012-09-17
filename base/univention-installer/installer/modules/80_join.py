#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: configuration for the join process
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

import subprocess

JOINTEST_RETVAL = 0

class object(content):

	def checkname(self):
		return ['domain_controller_account','domain_controller_password']

	def modvars(self):
		return ['domain_controller','domain_controller_account','domain_controller_password']

	def profile_complete(self):

		message=_('The following value is missing: ')
		if self.check('auto_join') | self.check('domain_controller_account') | self.check('domain_controller_password'):
			return False

		if self.all_results.has_key('auto_join') and self.all_results['auto_join'] in ['false', 'False']:
			return True

		if self.all_results['domain_controller_account'].strip() == '':
			if not self.ignore('domain_controller_account'):
				self.message=message+_('Join account')
				return False

		if self.all_results['domain_controller_password'].strip() == '':
			if not self.ignore('domain_controller_password'):
				self.message=message+_('Password')
				return False

		return True

	def mod_depends(self):
		return {'system_role': ['domaincontroller_backup','domaincontroller_slave','memberserver','managed_client','mobile_client'] }

	def layout(self):
		self.elements.append(textline(_('Start join at the end of installation.'),self.minY-11, self.minX+5)) #2
		self.elements.append(checkbox({" ": [" ", 0]},self.minY-10,self.minX+5,4, 1, [0])) #3

		self.elements.append(checkbox({" ": [" ", 0]},self.minY-7,self.minX+5,4, 1, [0])) #4
		self.elements.append(textline(_('Search Domain controller Master in DNS'),self.minY-8,self.minX+5)) #5

		self.elements.append(textline(_('Hostname of Domain controller Master'),self.minY-5,self.minX+5)) #6
		self.elements.append(input('',self.minY-4,self.minX+5,30)) #7

		self.elements.append(textline(_('Join account'),self.minY-2,self.minX+5)) #8
		self.elements.append(input('Administrator',self.minY-1,self.minX+5,30)) #9

		self.elements.append(textline(_('Password'),self.minY+1,self.minX+5)) #10
		self.elements.append(password('',self.minY+2,self.minX+5,30)) #11

		self.elements.append(textline(_('Password (retype)'),self.minY+4,self.minX+5)) #12
		self.elements.append(password('',self.minY+5,self.minX+5,30)) #13
		self.join_host_search_disabled=1
		self.elements[7].disable()
		self.join_disabled=0

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		elif key in [ 10, 32 ] and self.elements[3].active:
			self.elements[self.current].key_event(key)
			if " " in self.elements[3].result():
				self.join_disabled=0
				if self.join_host_search_disabled:
					self.elements[7].enable()
				else:
					self.elements[7].disable()
				self.elements[9].enable()
				self.elements[11].enable()
				self.elements[13].enable()
			else:
				self.join_disabled=1
				self.elements[7].disable()
				self.elements[9].disable()
				self.elements[11].disable()
				self.elements[13].disable()
			self.draw()
		elif key in [ 10, 32 ] and self.elements[4].active:
			self.elements[self.current].key_event(key)
			if " " in self.elements[4].result():
				self.join_host_search_disabled=0
				if not self.join_disabled == 1:
					self.elements[7].disable()
			else:
				self.join_host_search_disabled=1
				if not self.join_disabled == 1:
					self.elements[7].enable()
			self.draw()
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):

		global JOINTEST_RETVAL

		if self.elements[7].disabled and self.elements[9].disabled and self.elements[11].disabled and self.elements[13].disabled:
			return 0

		message=_('The following value is missing: ')
		if self.elements[7].result().strip() == '' and not " " in self.elements[4].result():
			return message+_('Hostname of Domain controller Master')
		if self.elements[9].result().strip() == '':
			return message+_('Join account')
		elif self.elements[11].result().strip() == '':
			return message+_('Password for Root')
		elif self.elements[13].result().strip() == '':
			return message+_('Password for Root (retype)')
		elif self.elements[11].result().strip() != self.elements[13].result().strip():
			return _('Passwords did not match.')

		# test join credentials
		data = {}
		JOINTEST_RETVAL = 0
		data["host"] = self.elements[7].result().strip()
		data["user"] = self.elements[9].result().strip()
		data["password"] = self.elements[11].result().strip()
		data["domain"] = self.all_results.get("domainname")
		self.joinact = TestJoin(self, _('Testing join settings'), _('Please wait ...'), name='joinact', data=data)
		self.joinact.draw()

		if JOINTEST_RETVAL != 0:
			if JOINTEST_RETVAL == 1:
				msg = _("The name/ip of the UCS DC master can not be resolved! Please check dns settings.")
			elif JOINTEST_RETVAL == 2: 
				msg = _("The UCS DC master is not reachable! Please check network settings.")
			elif JOINTEST_RETVAL == 3:
				msg = _("The login with the specified join account and password on the UCS DC master failed! Please check join settings.")
			else:
				msg = _("Connection to the UCS DC master failed! Please check network and join settings.") 

			return msg

		return 0

	def helptext(self):
		return _('Join settings \n \n All settings to join this system into given domain.')

	def modheader(self):
		return _('Join settings')

	def profileheader(self):
		return 'Join settings'

	def result(self):
		result={}
		if self.elements[7].disabled and self.elements[9].disabled and self.elements[11].disabled and self.elements[13].disabled:
			result['auto_join']='false'
		else:
			if self.elements[7].result():
				result['domain_controller']='%s'%self.elements[7].result()
			result['domain_controller_account']='%s'%self.elements[9].result()
			result['domain_controller_password']='%s'%self.elements[11].result()
		return result

class TestJoin(act_win):

	def __init__(self, parent, header, text, name, data):
		self.pos_x = parent.minX + 10
		self.pos_y = parent.minY + 2
		act_win.__init__(self, parent, header, text, name)
		self.data = data

	def function(self):

		global JOINTEST_RETVAL

		if os.path.exists("/sbin/univention-installer-check-join"):
			cmd = [
				"/sbin/univention-installer-check-join",
				self.data.get("host", ""),
				self.data.get("user", ""),
				self.data.get("password", ""),
				self.data.get("domain", ""),
			]
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
			(stdoutdata, stderrdata) = process.communicate()
			self.parent.debug("==> TestJoin stdout): %s" % stdoutdata)
			self.parent.debug("==> TestJoin stderr): %s" % stderrdata)
			JOINTEST_RETVAL = process.returncode

