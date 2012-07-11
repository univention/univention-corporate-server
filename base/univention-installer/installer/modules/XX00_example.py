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

class object(content):
	#def __init__():
	#def std_button():
	#def draw():
	#def help():

	def layout(self):
		# baseObject(text, pos_y, pos_x, width,status=0) ## set status=1 for active element
		# button(text, pos_y, pos_x, width,status=0)
		# input(text, pos_y, pos_x, width,status=0)
		# password(text, pos_y, pos_x, width,status=0)
		# select(list, pos_y, pos_x, width, visible, status=0)
		# mselect(list, pos_y, pos_x, width, visible, status=0)
		# textline(text, pos_y, pos_x)
		# description(text, pos_y, pos_x)
		# radiobutton(list,pos_y,pos_x,selected)
		# checkbox(list,pos_y,pos_x,selected=[])

		self.elements.append(button('button',self.max_y/2-8,self.max_x/2-15,10))
		self.elements.append(input('inputabcdef',self.max_y/2-6,self.max_x/2-15,10))
		self.elements.append(password('topsecret',self.max_y/2-4,self.max_x/2-15,10))
		list=['one','two','three','four','five']
		self.elements.append(select(list,self.max_y/2-2,self.max_x/2-15,10,3))
		self.elements.append(mselect(list,self.max_y/2+2,self.max_x/2-15,10,3))
		self.elements.append(textline('textfield',self.max_y/2-8,self.max_x/2))
		self.elements.append(radiobutton(list,self.max_y/2-6,self.max_x/2,[0]))
		self.elements.append(checkbox(list,self.max_y/2,self.max_x/2,[0,2,4]))

	def input(self,key):
		if key == 10 and self.btn_next():
			return 'next'
		elif key == 10 and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)

	def incomplete(self):
		return 0

	def helptext(self):
		return 'A short description...'

	def modheader(self):
		return _('Software')

	def profileheader(self):
		return 'Software'

	def result(self):
		result=[]
		for element in self.elements[2:len(self.elements)]:
			if element.usable():
				result.append(element.result())
		return result
