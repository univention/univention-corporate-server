#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: timezone selection
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

class object(content):
	def checkname(self):
		return ['timezone']


	def profile_complete(self):
		if self.check('timezone'):
			return False
		if self.all_results.has_key('timezone'):
			return True
		else:
			if self.ignore('timezone'):
				return True
			return False

	def layout(self):

		self.elements.append(textline(_('Select a time zone:'),self.minY-1,self.minX+2))#2

		if self.all_results.has_key('timezone'):
			timezone_default=self.all_results['timezone']
		else:
			timezone_default="Europe/Berlin"
			lang = ""
			if os.environ.has_key('LANGUAGE'):
				lang=os.environ['LANGUAGE']
			if lang == "en":
				timezone_default="US/Eastern"
			elif lang == "de":
				timezone_default="Europe/Berlin"

		try:
			file=open('modules/timezone')
		except:
			file=open('/lib/univention-installer/modules/timezone')
		dict={}
		timezone=file.readlines()
		count=0
		default_position=0
		for line in range(len(timezone)):
			entry = timezone[line].split(' ')[1][:-1]
			dict[entry]=[entry,line]
			if entry == timezone_default:
				default_position=count
			count=count+1
		self.elements.append(select(dict,self.minY,self.minX+2,38,18, default_position))#3

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
		return _('Time zone \n \n Select the time zone your system is located in. ')

	def modheader(self):
		return _('Time zone')

	def result(self):
		result={}
		result['timezone']='%s' % self.elements[3].result()[0]
		return result
