#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: system configuration
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
		return 'Software'

	def result(self):
		result=[]
		for element in self.elements[2:len(self.elements)]:
			if element.usable():
				result.append(element.result())
		return result
