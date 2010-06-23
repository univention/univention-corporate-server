#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: keyboard layout selection
#
# Copyright 2004-2010 Univention GmbH
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
import string
from objects import *
from local import _

class object(content):
	def checkname(self):
		return ['keymap']

	def profile_complete(self):
		if self.check('keymap') | self.check('country'):
			return False
		if self.all_results.has_key('keymap') or self.all_results.has_key('country'):
			return True
		else:
			if self.ignore('country') or self.ignore('keymap'):
				return True
			return False

	def run_profiled(self):
		if self.all_results.has_key('country'):
			self.profile_kmap=self.all_results['country']
		else:
			self.profile_kmap=self.all_results['keymap']
		self.sub = self.active(self,_('Loading Keyset'),_('Please wait...'))
		self.sub.draw()

		if self.all_results.has_key('country'):
			return { 'keymap': self.all_results['country']}
		elif self.all_results.has_key('keymap'):
			return { 'keymap': self.all_results['keymap']}

	def layout(self):
		#Headline
		self.elements.append(textline(_('Select your keyboard layout:'),self.minY-1,self.minX+2)) #2

		try:
			file=open('modules/keymap')
		except:
			file=open('/lib/univention-installer/modules/keymap')

		dict={}
		keymap=[]
		for line in file.readlines():
			keymap.append(line[line.find(' '):])
		keymap.sort()

		if self.all_results.has_key('keymap'):
			default_value=self.all_results['keymap']
		else:
			default_value='de-latin1'
			lang = ""
			if os.environ.has_key('LANGUAGE'):
				lang=os.environ['LANGUAGE']
			if lang == "en":
				default_value='us' #"us" is listed after "uk"
			elif lang == "de":
				default_value='de-latin1'

		default_line=''
		for line in range(len(keymap)):
			entry = keymap[line].strip()
			dict[entry]=[entry,line]
			if entry.split(':')[1] == default_value:
				default_line=line

		#Marking qwertz:de-latin1 as active (Element 5)
		self.elements.append(select(dict,self.minY,self.minX+2,38,18, default_line)) #3


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
		return _('Keyboard layout \n \n Select your keyboard layout.')

	def modheader(self):
		return _('Keyboard')

	def result(self):
		result={}
		result['keymap']='%s' % string.split(self.elements[3].result()[0], ':')[1]
		self.sub = self.active(self,_('Loading Keyset'),_('Please wait...'))
		self.sub.draw()

		return result

	class active(act_win):

		def loadkeys(self):
			#Trying to load the choosen keyset
			if hasattr(self.parent, 'profile_kmap'):
				if self.parent.profile_kmap.find(':') > -1:
					binkeyset='/usr/keymaps/%s.kmap'%string.split(self.parent.profile_kmap, ':')[1]
				else:
					binkeyset='/usr/keymaps/%s.kmap'%self.parent.profile_kmap
			else:
				binkeyset='/usr/keymaps/%s.kmap'%string.split(self.parent.elements[3].result()[0], ':')[1]
			self.parent.debug('binary-keyset: %s'%binkeyset)

			if os.path.exists(binkeyset):
				#loadkeys will return 0 if it was successful
				try:
					res=os.system('/bin/loadkeys < %s > /dev/null 2>&1'% binkeyset)
				except:
					res=1

				if os.path.exists('/lib/univention-installer-startup.d/S88keyboard'):
					os.system('/lib/univention-installer-startup.d/S88keyboard > /dev/null 2>&1')

				return res
			else:
				# on PPC we have no keymaps
				return 0

		def function(self):
			self.loadkeys()
