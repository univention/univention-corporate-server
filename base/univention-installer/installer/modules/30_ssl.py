#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: SSL CA configuration
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

class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.guessed = {}
		content.__init__(self, max_y, max_x, last, file, cmdline)

	def draw(self):
		pos=13
		if self.all_results.has_key('domainname') and self.all_results['domainname']:
			if len(self.elements) > 13:
				if not len(self.elements[pos].text) or not self.guessed.has_key('ssl_email') or self.guessed[ 'ssl_email' ] == self.elements[ pos ].text:
					text='ssl@%s' % self.all_results['domainname']
					self.guessed['ssl_email']=text
					self.elements[pos].text = text
					self.elements[pos].cursor=len(text)
					self.elements[pos].set_off()
					self.elements[pos].draw()
		content.draw(self)

	def checkname(self):
		return ['ssl']

	def profile_complete(self):
		message=_('The following value is missing: ')
		tolongmsg128=_('The following value is too long, only 128 characters allowed: ')
		tolongmsg64=_('The following value is too long, only 64 characters allowed: ')
		if self.check('ssl_country') | self.check('ssl_state') | self.check('ssl_locality') | self.check('ssl_organization') | self.check('ssl_organizationalunit') | self.check('ssl_email'):
			return False
		if self.all_results['ssl_country'].strip() == '':
			if not self.ignore('ssl_country'):
				self.message=message+_('Country')
				return False
		if len(self.all_results['ssl_country'].strip()) != 2:
			if not self.ignore('ssl_country'):
				self.message=_('Please enter a two letter country code.')
				return False

		if self.all_results['ssl_state'].strip() == '':
			if not self.ignore('ssl_state'):
				self.message=message+_('State')
				return False
		if len(self.all_results['ssl_state'].strip()) > 128:
			if not self.ignore('ssl_state'):
				self.message=tolongmsg128+_('State')
				return False

		if self.all_results['ssl_locality'].strip() == '':
			if not self.ignore('ssl_locality'):
				self.message=message+_('Location')
				return False
		if len(self.all_results['ssl_locality'].strip()) > 128:
			if not self.ignore('ssl_locality'):
				self.message=tolongmsg128+_('Location')
				return False

		if self.all_results['ssl_organization'].strip() == '':
			if not self.ignore('ssl_organization'):
				self.message=message+_('Organisation')
				return False
		if len(self.all_results['ssl_organization'].strip()) > 64:
			if not self.ignore('ssl_organization'):
				self.message=tolongmsg64+_('Organisation')
				return False

		if self.all_results['ssl_organizationalunit'].strip() == '':
			if not self.ignore('ssl_organizationalunit'):
				self.message=message+_('Unit')
				return False
		if len(self.all_results['ssl_organizationalunit'].strip()) > 64:
			if not self.ignore('ssl_organizationalunit'):
				self.message=tolongmsg64+_('Unit')
				return False

		if self.all_results['ssl_email'].strip() == '':
			if not self.ignore('ssl_email'):
				self.message=message+_('Mailaddress')
				return False
		if len(self.all_results['ssl_email'].strip()) > 64:
			if not self.ignore('ssl_email'):
				self.message=tolongmsg64+_('Mailaddress')
				return False
		if self.all_results['ssl_email'].find('@') == -1:
			if not self.ignore('ssl_email'):
				self.message = _("Please insert a valid mailaddress")
				return False
		return True


	def modvars(self):
		return ['ssl_country','ssl_state','ssl_locality','ssl_organization','ssl_organizationalunit','ssl_email']

	def mod_depends(self):
		return {'system_role':['domaincontroller_master']}

	def layout(self):
		self.elements.append(textline(_('Country Code'),self.minY,self.minX+2)) #2
		self.elements.append(input('',self.minY,self.minX+20,30)) #3

		self.elements.append(textline(_('State'),self.minY+2,self.minX+2)) #4
		self.elements.append(input('',self.minY+2,self.minX+20,30)) #5

		self.elements.append(textline(_('Location'),self.minY+4,self.minX+2)) #6
		self.elements.append(input('',self.minY+4,self.minX+20,30)) #7

		self.elements.append(textline(_('Organisation'),self.minY+6,self.minX+2)) #8
		self.elements.append(input('',self.minY+6,self.minX+20,30)) #9

		self.elements.append(textline(_('Unit'),self.minY+8,self.minX+2)) #10
		self.elements.append(input('',self.minY+8,self.minX+20,30)) #11

		self.elements.append(textline(_('Mailaddress'),self.minY+10,self.minX+2)) #12
		if self.all_results.has_key('domainname'):
			self.elements.append(input('ssl@%s'%self.all_results['domainname'],self.minY+10,self.minX+20,30)) #13
		else:
			self.elements.append(input('',self.minY+10,self.minX+20,30)) #13

	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		message=_('The following value is missing: ')
		tolongmsg128=_('The following value is too long, only 128 characters allowed: ')
		tolongmsg64=_('The following value is too long, only 64 characters allowed: ')
		if self.elements[3].result().strip() == '':
			self.move_focus( 3 )
			return message+_('Country')
		elif len(self.elements[3].result().strip()) != 2:
			self.move_focus( 3 )
			return _('Please enter a two letter country code.')

		elif self.elements[5].result().strip() == '':
			self.move_focus( 5 )
			return message+_('State')
		elif len(self.elements[5].result().strip()) > 128:
			self.move_focus( 5 )
			return tolongmsg128+_('State')

		elif self.elements[7].result().strip() == '':
			self.move_focus( 7 )
			return message+_('Location')
		elif len(self.elements[7].result().strip()) > 128:
			self.move_focus( 7 )
			return tolongmsg128+_('Location')

		elif self.elements[9].result().strip() == '':
			self.move_focus( 9 )
			return message+_('Organisation')
		elif len(self.elements[9].result().strip()) > 64:
			self.move_focus( 9 )
			return tolongmsg64+_('Organisation')

		elif self.elements[11].result().strip() == '':
			self.move_focus( 11 )
			return message+_('Unit')
		elif len(self.elements[11].result().strip()) > 64:
			self.move_focus( 11 )
			return tolongmsg64+_('Unit')

		if self.elements[13].result().strip() == '':
			self.move_focus( 13 )
			return message+_('Mailaddress')
		elif len(self.elements[13].result().strip()) > 64:
			self.move_focus( 13 )
			return tolongmsg64+_('Mailaddress')
		else:
			test=self.elements[13].result().split('@')
			message = _("Please insert a valid mailaddress")
		return 0

	def helptext(self):
		return _('SSL-Certificate \n \n The installation of a Domain Controller Master requires the creation of a SSL certificate. \n Enter all mandatory details')

	def modheader(self):
		return _('Certificate')

	def result(self):
		result={}
		result['ssl_country']='%s'%self.elements[3].result()
		result['ssl_state']='%s'%self.elements[5].result()
		result['ssl_locality']='%s'%self.elements[7].result()
		result['ssl_organization']='%s'%self.elements[9].result()
		result['ssl_organizationalunit']='%s'%self.elements[11].result()
		result['ssl_email']='%s'%self.elements[13].result()
		return result
