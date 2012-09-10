#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  classes for the installer interface
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

import textwrap
import curses
import thread
import traceback
import sys
import os
import time
import copy
import re
from local import _

class InstallerCursesException(Exception): pass
class CardboxInvalidCardIndex(InstallerCursesException): pass

class dummy:
	def __init__(self):
		pass

	def result(self):
		return ''

	def usable(self):
		return 0

	def draw(self):
		pass

	def get_status(self):
		return 0

class baseObject:
	def __init__(self, text, pos_y, pos_x, width, status=0, align='left', position_parent=None):
		self.width = width
		self.set_indent(text)
		if align == 'middle':
			self.pos_x=pos_x-(self.width/2)
		elif align == 'right':
			self.pos_x=pos_x-self.width
		else:
			self.pos_x=pos_x
		self.pos_y=pos_y
		if position_parent:
			self.pos_y += position_parent.child_pos_y
			self.pos_x += position_parent.child_pos_x

		self.text=text
		self.pad = curses.newpad(1, width)
		self.disabled=0
		if status:
			self.set_on()
		else:
			self.set_off()
		self.pad.addstr(0,self.indent,self.text[:self.width-1-self.indent])

	def set_text(self, text):
		self.pad.erase()
		self.set_indent(text)
		self.pad.addstr(0,self.indent,text)

	def get_text(self):
		return self.text

	def set_on(self):
		self.active=1
		self.pad.bkgd(" ",curses.color_pair(3))

	def set_off(self):
		self.active=0
		self.pad.bkgd(" ",curses.color_pair(2))

	def set_pos(self, pos_y, pos_x):
		self.pos_x=pos_x
		self.pos_y=pos_y

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)

	def set_indent(self, text):
		self.indent = 1

	def get_status(self):
		return self.active

	def key_event(self, input):
		pass

	def color(self, color_number):
		self.pad.bkgd(" ",curses.color_pair(color_number))

	def enable(self):
		self.disabled=0
		self.pad.bkgd(" ",curses.color_pair(2))
		self.draw()
	def disable(self):
		self.disabled=1
		self.pad.bkgd(" ",curses.color_pair(4))
		self.draw()
	def usable(self):
		if self.disabled == 1:
			return 0
		return 1

	def result(self):
		return ''


class baseObject_2(baseObject):
	def draw(self):
		self.pad.addch(0,0,"[")
		self.pad.addch(0,self.width-2,"]")
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)


class button(baseObject_2):
	def __init__(self, text, pos_y, pos_x, width=-1, status=0, align='left', position_parent=None):
		if width == -1:
			width=len(text)+2+3
		baseObject_2. __init__(self, text, pos_y, pos_x, width, status, align, position_parent=position_parent)

	def set_text(self, text):
		self.pad.erase()
		#self.set_indent(text[:self.width-1])
		self.pad.addstr(0,self.indent,text)

	def set_indent(self, text):
		if self.width % 2 == 1:
			self.indent = (self.width/2)-(len(text)/2)
		else:
			self.indent = (self.width/2)-(len(text)/2)-1
		if self.indent < 0:
			self.indent=0


class boolitem(baseObject):
	def set_indent(self,text):
		self.indent = 0

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)


class input(baseObject_2):
	def __init__(self, text, pos_y, pos_x, width, status=0, align='left', position_parent=None):
		self.cursor=len(text)
		self.invert=curses.newpad(2,2)
		self.invert.bkgd(" ",curses.color_pair(3))
		self.start=0
		self.first=1
		baseObject_2.__init__(self, text, pos_y, pos_x, width, position_parent=position_parent)

	def key_event(self, input):
		if input == curses.KEY_BACKSPACE:
			if self.cursor > 0:
				self.text = self.text[:self.cursor-1]+self.text[self.cursor:]
				self.set_cursor(-1)
		elif input == 330:
			self.text = self.text[:self.cursor]+self.text[self.cursor+1:]
		elif input == curses.KEY_LEFT:
			self.set_cursor(-1)
		elif input == curses.KEY_RIGHT:
			self.set_cursor(1)
		elif input == curses.KEY_END:
			self.cursor=len(self.text)
			self.set_cursor(0)
		elif input == curses.KEY_HOME:
			self.cursor=0
			self.set_cursor(0)
		elif input > 256:
			pass
		elif input == 27: #ESC
			pass
		elif input == 10:
			return 'tab'
		else:
			self.text = self.text[:self.cursor]+chr(input)+self.text[self.cursor:]
			self.set_cursor(1)
		self.paste_text()
		self.draw()

	def set_on(self):
		if self.first:
			self.first=0
			self.cursor=len(self.text)
		self.active=1
		self.pad.bkgd(" ",curses.color_pair(3))
		self.paste_text()

	def set_off(self):
		self.active=0
		self.pad.bkgd(" ",curses.color_pair(2))
		self.paste_text()

	def set_cursor(self,diff):
		if not len(self.text) < self.cursor+diff:
			self.cursor += diff

		if self.cursor <= 0:
			self.start = 0
			self.cursor = 0
		elif self.start > self.cursor-3:
			self.start = self.cursor-3
		if self.start+self.width-4 < self.cursor:
			self.start = self.cursor-self.width+4
		if self.start <= 0:
			self.start = 0

	def draw(self):
		self.set_cursor(0)
		if self.active:
			if len(self.text) > self.cursor:
				self.invert.addch(0,0,self.text[self.cursor], curses.color_pair(2))
			else:
				self.invert.addch(0,0," ", curses.color_pair(2))
			position=self.cursor-self.start+1
		else:
			if self.disabled:
				color = curses.color_pair(4)
			else:
				color = curses.color_pair(2)
			self.invert.addch(0,0,"[",color) # not active park position for this pad
			position=0
		self.pad.addch(0,0,"[")
		self.pad.addch(0,self.width-2,"]")
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)
		self.invert.refresh(0,0,self.pos_y,self.pos_x+position,self.pos_y,self.pos_x+position)

	def paste_text(self):
		if len(self.text) > self.width-3:
			self.set_text( self.text[self.start:self.start+self.width-3] )
		else:
			self.set_text( self.text[self.start:] )

	def result(self):
		return self.text

class password(input):
	def __init__(self, text, pos_y, pos_x, width):
		self.hide=''
		input.__init__(self, text, pos_y, pos_x, width)
		self.paste_text()

	def paste_text(self):
		self.hide = '*' * len(self.text)
		if len(self.hide) > self.width-3:
			self.set_text( self.hide[self.start:self.start+self.width-3] )
		else:
			self.set_text( self.hide[self.start:] )
	def draw(self):
		self.set_cursor(0)
		if self.active:
			if len(self.text) > self.cursor:
				self.invert.addch(0,0,self.hide[self.cursor], curses.color_pair(2))
			else:
				self.invert.addch(0,0," ", curses.color_pair(2))
			position=self.cursor-self.start+1
		else:
			if self.disabled:
				color = curses.color_pair(4)
			else:
				color = curses.color_pair(2)
			self.invert.addch(0,0,"[",color) # not active park position for this pad
			position=0
		self.pad.addch(0,0,"[")
		self.pad.addch(0,self.width-2,"]")
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)
		self.invert.refresh(0,0,self.pos_y,self.pos_x+position,self.pos_y,self.pos_x+position)

class select:
	def __init__(self, dict, pos_y, pos_x, width, visible, status=0, line=1, longline=0):
		self.width = width
		self.visible=[0,visible]
		self.pos_x=pos_x+1
		self.pos_y=pos_y
		self.line=line
		self.dict={}
		self.list=[]
		self.disabled = 0
		self.longline = longline
		list=[]

		if type(dict) is type(self.dict):
			self.dict=dict

			# try to sort...
			list=self.dict.keys()
			dict_size=len(list)
			if len(list) > 0 and len(self.dict[list[0]]) > 1:
				for key in self.dict.keys():
					if self.dict[key][1] < dict_size and self.dict[key][1] > -1:
						list[self.dict[key][1]]=key

		elif type(dict) is type(self.list):
			list=dict


		self.active=status
		if len(list) > visible:
			self.scrollbar = scrollbar(self.pos_y,pos_x+width,visible,len(list))
			if self.line:
				self.leftline = vLine(pos_y,pos_x,visible)
		else:
			if self.line:
				if self.longline:
					self.rightline = vLine(self.pos_y,pos_x+width, visible)
					self.leftline = vLine(pos_y,pos_x, visible)
				else:
					self.rightline = vLine(self.pos_y,pos_x+width,len(list))
					self.leftline = vLine(pos_y,pos_x,len(list))

		for i in range(len(list)):
			self.list.append(baseObject(list[i],pos_y,self.pos_x,width))
			pos_y += 1
		self.current=self.active
		if self.current > len(list)-1:
			self.current = len(list)-1
		self.set(0)


	def get_status(self):
		return self.active

	def set_on(self):
		if len(self.list) > 0:
			self.active=1
			self.list[self.current].set_on()

	def set_off(self):
		if len(self.list) > 0:
			self.active=0
			self.list[self.current].color(1)

	def set(self,diff):
		if len(self.list) > 0:
			self.list[self.current].set_off()
			if self.current+diff >= 0 and self.current+diff < len(self.list):
				self.current = self.current+diff
			elif self.current+diff > len(self.list):
				self.current = len(self.list)-1
			elif self.current+diff < 0:
				self.current = 0
			self.list[self.current].set_on()

	def draw(self):
		if len(self.list) > self.visible[1]:
			if self.current < self.visible[0]:
				self.visible[0]=self.current
			elif self.current > self.visible[0]+self.visible[1]-1:
				self.visible[0]=self.current-self.visible[1]+1
			for i in range(self.visible[1]):
				self.list[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x)
				self.list[self.visible[0]+i].draw()
			self.scrollbar.draw(self.current)
			if self.line:
				self.leftline.draw()
		elif len(self.list) > 0:
			for i in range(len(self.list)):
				self.list[i].draw()
			if self.line:
				self.leftline.draw()
				self.rightline.draw()


	def key_event(self, input):
		if not self.active:
			self.active = 1
		if input == curses.KEY_DOWN:
			self.set(1)
		elif input == curses.KEY_UP:
			self.set(-1)
		elif input == 10:
			return 'tab'
		elif input == 338: # PGDN
			self.set(self.visible[1]-1)
		elif input == 339: # PGUP
			self.set(-(self.visible[1]-1))
		self.draw()

	def enable(self):
		self.disabled=0
		for i in range(len(self.list)):
			self.list[i].color(4)
		self.list[self.current].set_on()
		self.draw()

	def disable(self):
		self.disabled=1
		for i in range(len(self.list)):
			self.list[i].color(1)
		self.draw()

	def usable(self):
		if self.disabled == 1:
			return 0
		if len(self.list) > 0:
			return 1
		return 0

	def result(self):
		result=[]
		for i in range(len(self.list)):
			if self.list[i].get_status():
				if len(self.dict) > 0:
					result.append(self.dict[self.list[i].get_text()][0])
				else:
					result.append(i)
		return result

class mselect(select):
	def __init__(self, dict, pos_y, pos_x, width, visible, status=0):
		self.width = width
		self.visible=[0,visible]
		self.pos_x=pos_x+1
		self.pos_y=pos_y
		#self.dict=dict
		#
		## try to sort...
		#list=self.dict.keys()
		#dict_size=len(list)
		#if len(self.dict[list[0]]) > 1:
		#	for key in self.dict.keys():
		#		if self.dict[key][1] < dict_size and self.dict[key][1] > -1:
		#			list[self.dict[key][1]]=key
		#
		#self.list=[]

		self.dict={}
		self.list=[]

		if type(dict) is type(self.dict):
			self.dict=dict

			# try to sort...
			list=self.dict.keys()
			dict_size=len(list)
			if len(list) > 0 and len(self.dict[list[0]]) > 1:
				for key in self.dict.keys():
					if self.dict[key][1] < dict_size and self.dict[key][1] > -1:
						list[self.dict[key][1]]=key

		elif type(dict) is type(self.list):
			list=dict

		self.active=status
		if len(list) > visible:
			self.scrollbar = scrollbar(self.pos_y,pos_x+width,visible,len(list))
			self.leftline = vLine(pos_y,pos_x,visible)
		else:
			self.rightline = vLine(self.pos_y,pos_x+width,len(list))
			self.leftline = vLine(pos_y,pos_x,len(list))
		for i in range(len(list)):
			self.list.append(baseObject(list[i],pos_y,pos_x,width))
			pos_y += 1
		self.current=0
		self.choice=[]

	def draw(self):
		if len(self.list) > self.visible[1]:
			if self.current < self.visible[0]:
				self.visible[0]=self.current
			elif self.current > self.visible[0]+self.visible[1]-1:
				self.visible[0]=self.current-self.visible[1]+1
			for i in range(self.visible[1]):
				self.list[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x)
				self.list[self.visible[0]+i].draw()
			self.scrollbar.draw(self.current)
			self.leftline.draw()
		elif len(self.list) > 0:
			for i in range(len(self.list)):
				self.list[i].draw()
			self.leftline.draw()
			self.rightline.draw()

	def key_event(self,input):
		if input == curses.KEY_DOWN:
			self.set(1)
		elif input == curses.KEY_UP:
			self.set(-1)
		elif input == 32:
			self.select()
		elif input == 10:
			self.select()
			return 'tab'
		elif input == 338: # PGDN
			self.set(self.visible[1]-1)
		elif input == 339: # PGUP
			self.set(-(self.visible[1]-1))
		self.draw()

	def select(self):
		if self.current in self.choice:
			self.choice.remove(self.current)
			self.list[self.current].set_on()

		else:
			self.choice.append(self.current)
			self.choice.sort()
			self.list[self.current].color(1)

	def set(self,diff):
		if self.current in self.choice:
			self.list[self.current].color(1)
		else:
			self.list[self.current].set_off()
		if self.current+diff >= 0 and self.current+diff < len(self.list):
			self.current = self.current+diff
		elif self.current+diff > len(self.list):
			self.current = len(self.list)-1
		elif self.current+diff < 0:
			self.current = 0
		self.list[self.current].set_on()

	def set_on(self):
		self.active=1
		self.list[self.current].set_on()

	def set_off(self):
		self.active=0
		if self.current in self.choice:
			self.list[self.current].color(1)
		else:
			self.list[self.current].set_off()

class textline:
	def __init__(self, text, pos_y, pos_x, align='left', width=0, position_parent=None):
		self.width=len(text)
		if width:
			self.width=width

		if align == 'middle':
			self.pos_x=pos_x-(self.width/2)
		elif align == 'right':
			self.pos_x=pos_x-self.width
		else:
			self.pos_x=pos_x
		self.pos_y=pos_y
		if position_parent:
			self.pos_y += position_parent.child_pos_y
			self.pos_x += position_parent.child_pos_x
		self.text=text
		self.height=1
		self.pad=curses.newpad(self.height, self.width+2)
		self.bgcolor()
		if len(text) >0 and self.width  >= 0:
			self.pad.addstr(0,0,text[:self.width])

	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(4))

	def set_text(self,text):
		self.width=len(text)
		self.pad=curses.newpad(self.height, self.width)
		self.bgcolor()
		self.pad.addstr(0,0,text)
		self.text=text

	def get_text(self):
		return self.text

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)

	def usable(self):
		return 0

	def set_pos(self,pos_y,pos_x):
		self.pos_y=pos_y
		self.pos_x=pos_x

class textarea:
	def __init__(self, text, pos_y, pos_x, height, width, align='left', position_parent=None, drop_whitespace=True, warning=False):
		self.width = width
		self.height = height
		self.drop_whitespace = drop_whitespace
		self.warning = warning

		if align == 'middle':
			self.pos_x = pos_x-(self.width/2)
		elif align == 'right':
			self.pos_x = pos_x-self.width
		else:
			self.pos_x = pos_x
		self.pos_y=pos_y
		if position_parent:
			self.pos_y += position_parent.child_pos_y
			self.pos_x += position_parent.child_pos_x
		self.text=text
		self.pad=curses.newpad(self.height, self.width+1)
		self.bgcolor()

		self.update_lines()

	def update_lines(self):
		self.lines = []
		for parts in self.text.split('\n'):
			wrappedlines = textwrap.wrap(parts, self.width, drop_whitespace=self.drop_whitespace)
			if wrappedlines:
				self.lines.extend( wrappedlines )
			else:
				self.lines.extend( [''] )
		self.bgcolor()
		i=0
		for line in self.lines:
			self.pad.addstr(i, 0, line)
			i += 1
			if i >= self.height:
				break

	def erase(self):
		self.pad = curses.newpad(self.height, self.width+1)
		self.bgcolor()

	def bgcolor(self):
		if self.warning:
			self.pad.bkgd(" ",curses.color_pair(5))
		else:
			self.pad.bkgd(" ",curses.color_pair(4))

	def set_text(self, text):
		self.text=text
		self.update_lines()

	def get_text(self):
		return self.text

	def get_number_of_lines(self):
		if len(self.lines) > self.height:
			return self.height
		return len(self.lines)

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)

	def usable(self):
		return 0

	def set_pos(self,pos_y,pos_x):
		self.pos_y=pos_y
		self.pos_x=pos_x



class description(textline):
	def __init__(self, text, pos_y, pos_x, visible):
		self.visible=visible
		textline.__init__(self, text, pos_y, pos_x, width=visible)

	def set_text(self,text):
		self.width=self.visible+1
		self.pad=curses.newpad(self.height, self.width)
		self.bgcolor()
		self.pad.addstr(0,0,text[:self.visible])
		self.text=text

	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(4))

class headline(textline):
	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(5))

class footline(textline):
	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(5))

class modline(textline):
	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(4))
	def active(self):
		self.pad.bkgd(" ",curses.color_pair(5))

class card:
	def __init__(self, parent, name, pos_y, pos_x, child_pos_y, child_pos_x):
		self.parent = parent
		self.name = name
		self.elements = []
		self.element_index = {}
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.width = len(name)+2
		self.height = 2
		self.child_pos_x=child_pos_x
		self.child_pos_y=child_pos_y
		self.pad = curses.newpad(3, len(name)+2)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)
		self.pad.addstr(1,1,name)

	# removes all widgets from window
	def reset_layout(self):
		self.elements = []
		self.element_index = {}

	# adds widget to window and assigns name to it
	def add_elem(self, name, element):
		"""
		Add element to card with given name.
		Please note that <element> has to provide argument position_parent=OBJ which
		is required to define <element>'s position relative to upper left corner of <position_parent>.
		"""
		self.element_index[name] = len(self.elements)
		self.elements.append( element )

	# returns widget addressed by name
	def get_elem(self, name):
		return self.elements[ self.element_index[ name ] ]

	# tests if widget addressed by name exists
	def elem_exists(self, name):
		return self.element_index.has_key(name)

	# returns widget id (old behaviour) of widget addressed by name
	def get_elem_id(self, name):
		if self.element_index.has_key(name):
			return self.element_index[ name ]
		return None

	# returns widget addressed by widget id
	def get_elem_by_id(self, id):
		return self.elements[ id ]

	def draw_tab(self):
		"""
		draw header/tab for this card
		"""
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)

	def draw(self):
		"""
		draw content of card
		"""
		for elem in self.elements:
			elem.draw()

	def usable(self):
		return 0

class cardbox:
	def __init__(self, parent, pos_y, pos_x, height, width):
		self.parent = parent
		self.cards = []
		self.cardwidth = 0
		self.active = None
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.width = width
		self.height = height
		self.pad = curses.newpad(self.height-2, self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)

	def draw(self, onlyChilds=False):
		pos = 1
		for i in xrange(len(self.cards)):
			width = self.cards[i].width
			if pos >= self.width or pos+width >= self.width:
				continue
			# draw header/tab of all cards
			self.cards[i].draw_tab()
			# make tabs realistic
			if i == self.active:
				self.pad.addch(0,pos,curses.EDGE_BR)
				for cpos in xrange(pos+1,pos+width-1):
					self.pad.addch(0,cpos," ")
				self.pad.addch(0,pos+width-1,curses.EDGE_BL)
			else:
				self.pad.addch(0,pos,curses.ACS_BTEE)
				for cpos in xrange(pos+1,pos+width-1):
					self.pad.addch(0,cpos,curses.MY_HLINE)
				self.pad.addch(0,pos+width-1,curses.ACS_BTEE)
			pos += width

		if onlyChilds:
			# draw only top line of border
			self.pad.refresh(0,0,self.pos_y+2,self.pos_x,self.pos_y+2,self.pos_x+self.width)
		else:
			# draw complete pad
			self.pad.refresh(0,0,self.pos_y+2,self.pos_x,self.pos_y+self.height-1,self.pos_x+self.width)
		# draw content of active card
		self.cards[self.active].draw()

	def append_card(self, name):
		newcard = card(self.parent, name, self.pos_y, self.pos_x + 1 + self.cardwidth, self.pos_y+3, self.pos_x+1)
		self.cards.append(newcard)
		if self.active == None:
			self.active = 0
			self.add_current_elements_to_parent()
		self.cardwidth += len(name)+2
		return self.cards[-1]

	def remove_current_elements_from_parent(self):
		# save elem2name to be able to recover name2index later on
		obj2name = {}
		for name, index in self.parent.element_index.items():
			obj2name[ self.parent.elements[index] ] = name

		# remove cards elements from parent's element list
		for obj in self.cards[self.active].elements:
			if obj in self.parent.elements:
				self.parent.elements.remove(obj)

		# rebuild name2index of parent
		self.parent.element_index = {}
		index = 0
		for obj in self.parent.elements:
			if obj in obj2name:
				self.parent.element_index[obj2name[obj]] = index
			index += 1

	def add_current_elements_to_parent(self):
		# save elem2name to be able to recover name2index later on
		obj2name = {}
		for name, index in self.parent.element_index.items():
			obj2name[ self.parent.elements[index] ] = name

		# find self (cardbox) in parent's elements; if not found then return
		if not self in self.parent.elements:
			return
		i = self.parent.elements.index(self)
		# add card's elements to parent's elements just behind cardbox element
		self.parent.elements[i+1:i+1] = self.cards[self.active].elements

		# rebuild name2index of parent
		self.parent.element_index = {}
		index = 0
		for obj in self.parent.elements:
			if obj in obj2name:
				self.parent.element_index[obj2name[obj]] = index
			index += 1

		# add names from card to name2index of parent
		for name, index in self.cards[self.active].element_index.items():
			obj = self.cards[self.active].elements[index]
			i = self.parent.elements.index(obj)
			self.parent.element_index[name] = i

	def fix_active_element(self, old_active_element):
		self.parent.current = None
		for i in xrange(len(self.parent.elements)):
			elem = self.parent.elements[i]
			# if old_active_element is still set then the "current" element is not on any card ==> set all other elements to off
			if old_active_element and elem.usable() and elem != old_active_element:
				elem.set_off()
			# activate old_active_element and update "current"
			elif old_active_element and elem.usable() and elem == old_active_element:
				elem.set_on()
				self.parent.current = i
			# if old_active_element is not set then the "current" element has been on removed card ==> update "current"
			elif not old_active_element and elem.usable() and elem.active:
				self.parent.current = i
		if self.parent.current == None:
			for i in xrange(2, len(self.parent.elements)):
				if self.parent.elements[i].usable():
					self.parent.current = i
					self.parent.elements[i].set_on()
					break

	def next_card(self):
		# remember old active element
		old_active_element = self.parent.elements[self.parent.current]
		# remove current tab from elements
		self.remove_current_elements_from_parent()
		# if active element has been removed, then unset old_active_element
		if not old_active_element in self.parent.elements:
			old_active_element = None
		# set new card
		self.active = (self.active+1) % len(self.cards)
		# add new current tab to elements
		self.add_current_elements_to_parent()
		# set new active
		self.fix_active_element(old_active_element)

	def prev_card(self):
		# remember old active element
		old_active_element = self.parent.elements[self.parent.current]
		# remove current tab from elements
		self.remove_current_elements_from_parent()
		# if active element has been removed, then unset old_active_element
		if not old_active_element in self.parent.elements:
			old_active_element = None
		# set new card
		self.active = (self.active-1) % len(self.cards)
		# add new current tab to elements
		self.add_current_elements_to_parent()
		# set new active
		self.fix_active_element(old_active_element)

	def set_card(self, index):
		if (0 <= index) and (index < len(self.cards)):
			# remember old active element
			old_active_element = self.parent.elements[self.parent.current]
			# remove current tab from elements
			self.remove_current_elements_from_parent()
			# if active element has been removed, then unset old_active_element
			if not old_active_element in self.parent.elements:
				old_active_element = None
			# set new card
			self.active = index
			# add new current tab to elements
			self.add_current_elements_to_parent()
			# set new active
			self.fix_active_element(old_active_element)
		else:
			raise CardboxInvalidCardIndex()

	def get_card(self, index=None):
		"""
		returns current card or specified card if index!=None
		"""
		if index == None:
			return self.cards[self.active]
		return self.cards[index]

	def usable(self):
		return 0


class border:
	def __init__(self, pos_y, pos_x, width, height):
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.width = width
		self.height = height
		self.pad = curses.newpad(self.height, self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)

	def usable(self):
		return 0


class help_win:
	def __init__(self, text, max_y, max_x):
		self.width = 60
		self.height = 20
		self.text_height = 15
		self.text=text.replace('\n',' ### ').split()



		str=' '
		line=self.width-5
		self.clearline=''
		for i in range(line):
			self.clearline+=' '
		self.rows=[]
		for word in self.text:
			while len(word) > line:
				self.rows.append(' '+word[:line-1]+'-')
				word = word[line-1:]
			if word == '###':
				self.rows.append(str)
				str=''
			elif len(str)+len(word) > line:
				self.rows.append(str)
				str=' '+word
			else:
				str += word
			str +=' '
		self.rows.append(str)

		if len(self.rows) < 15:
			self.height = len(self.rows)+5


		self.pos_x=(max_x/2+1)-(self.width/2)
		self.pos_y=(max_y/2)-(self.height/2)
		self.pad = curses.newpad(self.height, self.width)
		self.shadow = curses.newpad(self.height, self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)
		self.shadow.bkgd(" ",curses.color_pair(1))
		self.headline=textline(self.headline(),self.pos_y,self.pos_x+(self.width/2)-len(self.headline())/2)
		self.footline=textline(self.footline(),self.pos_y+self.height-1,self.pos_x+(self.width/2)-len(self.footline())/2)

		self.current=0
		if len(self.rows) > self.text_height:
			self.scrollbar = scrollbar(self.pos_y+2,self.pos_x+self.width-2,self.text_height,len(self.rows)-self.text_height)
			self.scrollbar.color(4)
		self.scroll_draw(1)
		self.shadow.refresh(0,0,self.pos_y+1,self.pos_x+1,self.pos_y+self.height+1,self.pos_x+self.width+1)

	def headline(self):
		return _(' Help')

	def footline(self):
		return _(' Esc-Quit Dialog')

	def scroll_draw(self,do=0):
		if len(self.rows) > self.text_height or do > 0:
			for i in range(self.current,self.current+self.text_height):
				self.pad.addstr(i+2-self.current,1,self.clearline)
				self.pad.addstr(i+2-self.current,1,self.rows[i])
				if len(self.rows)-1 is i:
					break


	def draw(self):
		self.scroll_draw()
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)
		self.headline.draw()
		self.footline.draw()
		if len(self.rows) > self.text_height:
			self.scrollbar.draw(self.current)

	def set(self,diff):
		temp = self.current

		if self.current+diff < 0:
			temp = 0
		elif self.current+diff >= len(self.rows)-self.text_height:
			temp=len(self.rows)-self.text_height
		elif self.current+diff >= 0 and self.current+diff <= len(self.rows)-self.text_height:
			temp = self.current+diff
		elif temp == len(self.rows)-self.text_height:
			temp = self.current+diff

		if temp != self.current:
			self.current=temp
			self.draw()


	def key_event(self, input):
		if input == curses.KEY_DOWN:
			self.set(1)
		elif input == curses.KEY_UP:
			self.set(-1)
		elif input == 338: # PGDN
			self.set(self.text_height-1)
		elif input == 339: # PGUP
			self.set(-(self.text_height-1))
		elif input == 27: # ESC -> exit help
			return 0
		else:
			return 1
		#self.draw()
		return 1

	def usable(self):
		return 0

class warning(help_win):
	def headline(self):
		return _(' Warning')

class exit(help_win):
	def headline(self):
		return _(' End')

class scrollbar:
	def __init__(self,pos_y,pos_x,height,total):
		self.height=height
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.total=total
		self.pad=curses.newpad(self.height+2,1)
		self.pad.bkgd(curses.MY_VLINE,curses.color_pair(2))
		self.curs=0

	def color(self,num):
		self.pad.bkgd(curses.MY_VLINE,curses.color_pair(num))

	def draw(self,current):
		#self.pad.erase()
		self.pad.delch(self.curs,0)
		self.curs=int(float(self.height)/self.total*current)
		if self.curs > self.height-1:
			self.curs=self.height-1
		self.pad.addch(self.curs,0,curses.MY_BOARD)
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height-1,self.pos_x)

	def usable(self):
		return 0




class vLine:
	def __init__(self,pos_y,pos_x,height):
		self.height=height
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.pad=curses.newpad(self.height+2,1)
		self.pad.bkgd(curses.MY_VLINE,curses.color_pair(2))

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height-1,self.pos_x)

	def usable(self):
		return 0
class hLine:
	def __init__(self,pos_y,pos_x,height):
		self.height=height
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.pad=curses.newpad(1,self.height+2)
		self.pad.bkgd(curses.MY_HLINE,curses.color_pair(2))

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y,self.pos_x+self.height-1)

	def usable(self):
		return 0

class radiobutton:
	def __init__(self,dict,pos_y,pos_x,width,visible,selected=[0],fixed=[], position_parent=None):
		# UNSORTED:
		#    dict[ DESCRIPTION ] = [ RETURNVALUE ]
		# SORTED:
		#    dict[ DESCRIPTION ] = [ RETURNVALUE, POSITION-AS-INT ]
		self.pos_x=pos_x
		self.pos_y=pos_y
		if position_parent:
			self.pos_y += position_parent.child_pos_y
			self.pos_x += position_parent.child_pos_x
		self.visible=[0,visible]
		if len(selected) > 0 and str(selected[0]).isalpha():
			self.selected=[dict.values().index(selected)]
		else:
			self.selected=selected
		self.button=[]
		self.desc=[]
		self.dict=dict
		self.active=0
		self.fixed=fixed
		self.disabled=0

		# try to sort...
		list=self.dict.keys()
		dict_size=len(list)
		if len(list) > 0 and len(self.dict[list[0]]) > 1:
			for key in self.dict.keys():
				if self.dict[key][1] < dict_size and self.dict[key][1] > -1:
					list[self.dict[key][1]]=key
		self.clearline=description((' '*width), self.pos_y, self.pos_x+4,width)

		if len(list) > visible:
			self.scrollbar = scrollbar(self.pos_y,pos_x+width+5,visible,len(list))

		for i in range(len(list)):
			self.button.append(boolitem('[ ]', self.pos_y+i, self.pos_x,4))
			if i in self.selected:
				self.button[i].set_text('[X]')
			self.desc.append(description(list[i], self.pos_y+i, self.pos_x+4,width))

		self.current=0
		self.draw()

	def set_on(self):
		if len(self.button):
			self.button[self.current-1].set_off()
			self.active=1
			self.button[self.current].set_on()

	def set_off(self):
		if len(self.button):
			self.active=0
			self.button[self.current].set_off()

	def set(self,diff):
		if len(self.button) > 0:
			self.button[self.current].set_off()
			if self.current+diff >= 0 and self.current+diff < len(self.button):
				self.current = self.current+diff
			elif self.current+diff > len(self.button):
				self.current = len(self.button)-1
			elif self.current+diff < 0:
				self.current = 0
			self.button[self.current].set_on()

	def select(self):
		if not self.current in self.fixed:
			self.button[self.selected[0]].set_text('[ ]')
			self.selected[0]=self.current
			self.button[self.selected[0]].set_text('[X]')

	def draw(self):
		if len(self.button) > self.visible[1]:
			if self.current < self.visible[0]:
				self.visible[0]=self.current
			elif self.current > self.visible[0]+self.visible[1]-1:
				self.visible[0]=self.current-self.visible[1]+1
			for i in range(self.visible[1]):
				self.button[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x)
				self.clearline.set_pos(self.pos_y+i,self.pos_x+4)
				self.desc[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x+4)
				self.button[self.visible[0]+i].draw()
				self.clearline.draw()
				self.desc[self.visible[0]+i].draw()
			self.scrollbar.draw(self.current)
		else:
			for i in range(len(self.button)):
				self.button[i].draw()
				self.desc[i].draw()

	def key_event(self, input):
		if input == curses.KEY_DOWN:
			self.set(1)
		elif input == curses.KEY_UP:
			self.set(-1)
		elif input == 32 or input == 10:
			self.select()
		elif input == 338: # PGDN
			self.set(self.visible[1]-1)
		elif input == 339: # PGUP
			self.set(-(self.visible[1]-1))
		self.draw()


	def enable(self):
		self.disabled=0
		for i in range(len(self.button)):
			self.button[i].set_off()
		self.draw()

	def disable(self):
		self.disabled=1
		for i in range(len(self.button)):
			self.button[i].color(4)
		self.draw()

	def usable(self):
		if self.disabled == 1:
			return 0
		if len(self.button):
			return 1
		else:
			return 0

	def result(self):
		return self.dict[self.desc[self.selected[0]].get_text()][0]

	def get_focus(self):
		"""
		Returns index of radiobutton that has currently focus. Additionally the result value of that radiobutton will be returned.
		>>> obj.get_focus(self)
		[ 3, 'resulttext' ]
		"""
		return [ self.current, self.dict[self.desc[self.current].get_text()][0] ]


class checkbox(radiobutton):
	def select(self):
		if not self.current in  self.fixed:
			if self.current in self.selected:
				self.button[self.current].set_text('[ ]')
				self.selected.remove(self.current)
			else:
				self.button[self.current].set_text('[X]')
				self.selected.append(self.current)

	def result(self):
		result=[]
		for i in self.selected:
			result.append(self.dict[self.desc[i].get_text()][0])
		return result


class checkbox3(radiobutton):
	def __init__(self,dict,pos_y,pos_x,width,visible,selected_half=[], selected_full=[0]):
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.visible=[0,visible]
		self.selected_full=selected_full
		self.selected_half=selected_half
		#if len(selected) > 0 and str(selected[0]).isalpha():
		#	self.selected=[dict.values().index(selected)]
		#else:
		#	self.selected=selected
		self.button=[]
		self.desc=[]
		self.dict=dict
		self.active=0


		# try to sort...
		list=self.dict.keys()
		dict_size=len(list)
		if len(self.dict[list[0]]) > 1:
			for key in self.dict.keys():
				if self.dict[key][1] < dict_size and self.dict[key][1] > -1:
					list[self.dict[key][1]]=key
		self.clearline=description((' '*width), self.pos_y, self.pos_x+4,width)

		if len(list) > visible:
			self.scrollbar = scrollbar(self.pos_y,pos_x+width+5,visible,len(list))

		for i in range(len(list)):
			self.button.append(boolitem('[ ]', self.pos_y+i, self.pos_x,4))
			if i in self.selected_half:
				self.button[i].set_text('[/]')
			elif i in self.selected_full:
				self.button[i].set_text('[X]')
			self.desc.append(description(list[i], self.pos_y+i, self.pos_x+4,width))
		self.select_all()

		self.current=0
		self.draw()

	def set_on(self):
		self.button[self.current-1].set_off()
		self.active=1
		self.button[self.current].set_on()

	def set_off(self):
		self.active=0
		self.button[self.current].set_off()

	def set(self,diff):
		if len(self.button) > 0:
			self.button[self.current].set_off()
			if self.current+diff >= 0 and self.current+diff < len(self.button):
				self.current = self.current+diff
			elif self.current+diff > len(self.button):
				self.current = len(self.button)-1
			elif self.current+diff < 0:
				self.current = 0
			self.button[self.current].set_on()

	def draw(self):
		if len(self.button) > self.visible[1]:
			if self.current < self.visible[0]:
				self.visible[0]=self.current
			elif self.current > self.visible[0]+self.visible[1]-1:
				self.visible[0]=self.current-self.visible[1]+1
			for i in range(self.visible[1]):
				self.button[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x)
				self.clearline.set_pos(self.pos_y+i,self.pos_x+4)
				self.desc[self.visible[0]+i].set_pos(self.pos_y+i,self.pos_x+4)
				self.button[self.visible[0]+i].draw()
				self.clearline.draw()
				self.desc[self.visible[0]+i].draw()
			self.scrollbar.draw(self.current)
		else:
			for i in range(len(self.button)):
				self.button[i].draw()
				self.desc[i].draw()

	def key_event(self, input):
		if input == curses.KEY_DOWN:
			self.set(1)
		elif input == curses.KEY_UP:
			self.set(-1)
		elif input == 32:
			self.select()
		elif input == 338: # PGDN
			self.set(self.visible[1]-1)
		elif input == 339: # PGUP
			self.set(-(self.visible[1]-1))
		elif input == 10:
			self.select()
			return 'tab'
		self.draw()

	def usable(self):
		return 1

	def select_all(self):
		for i in self.dict.keys():
			pos=self.dict[i][1]
			if pos in self.selected_half:
				self.button[pos].set_text('[/]')
			elif pos in self.selected_full:
				self.button[pos].set_text('[X]')
			else:
				self.button[pos].set_text('[ ]')

	def select(self):
		if self.current in self.selected_full:
			self.button[self.current].set_text('[ ]')
			self.selected_full.remove(self.current)
			self.selected_half.append(self.current)
		elif self.current in self.selected_half:
			self.button[self.current].set_text('[X]')
			self.selected_half.remove(self.current)
			self.selected_full.append(self.current)
		else:
			self.button[self.current].set_text('[ ]')
			self.selected_full.append(self.current)

	def set_selected_full(self, index):
		if index in self.selected_half:
			self.selected_half.remove(index)
		self.selected_full.append(index)

	def set_selected_half(self, index):
		if index in self.selected_full:
			self.selected_full.remove(index)
		self.selected_half.append(index)

	def result(self):
		result_full=[]
		result_half=[]
		for i in self.selected_full:
			result_full.append(self.dict[self.desc[i].get_text()][0])
		for j in self.selected_half:
			result_half.append(self.dict[self.desc[j].get_text()][0])
		return result_half,result_full

class content:
	def __init__(self,max_y,max_x,last=(1,1), file='/tmp/installer.log', cmdline={}):
		self.all_results={}
		self.file=file
		self.last=last
		self.width=80
		self.height=35
		self.pos_x=(max_x/2)-30
		self.pos_y=(max_y/2)-17
		if not self.pos_y:
			self.pos_y=1
		self.max_x=max_x
		self.max_y=max_y
		self.minX=self.max_x/2-28
		self.minY=self.max_y/2-4
		self.maxWidth=56
		self.maxHeight=28
		self.maxX=self.minX+66
		self.maxY=self.minY+27
		self.cmdline=cmdline
		self.pad=curses.newpad(self.height,self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,' ',' ',' ',' ',' ',' ',' ')
		self.elements=[]
		self.reset_layout()
		self.current=0
		self.std_button()
		self.header=textline(self.modheader(), self.pos_y, self.pos_x+self.width-len(self.modheader())-2)
		self.container={}
		#self.debug('(content)init')
		if self.cmdline.has_key('profile'):
			self.startIt=0
		else:
			self.startIt=1
		self.already_checked=[]

	def debug(self, str):
		if not self.file:
			self.file='/tmp/installer.log'
		f=open(self.file, 'a+')
		f.write(str+'\n')
		f.close()

	def refresh_modheader(self):
		self.header=textline(self.modheader(), self.pos_y, self.pos_x+self.width-len(self.modheader())-2)

	# removes all widgets from window
	def reset_layout(self):
		self.elements = []
		self.element_index = {}

	# adds widget to window and assigns name to it
	def add_elem(self, name, element):
		self.element_index[name] = len(self.elements)
		self.elements.append( element )

	# returns widget addressed by name
	def get_elem(self, name):
		return self.elements[ self.element_index[ name ] ]

	# tests if widget addressed by name exists
	def elem_exists(self, name):
		return self.element_index.has_key(name)

	# returns widget id (old behaviour) of widget addressed by name
	def get_elem_id(self, name):
		if self.element_index.has_key(name):
			return self.element_index[ name ]
		return None

	# returns widget addressed by widget id
	def get_elem_by_id(self, id):
		return self.elements[ id ]

	def std_button(self):
		#self.debug('(content)std_button')
		if self.last[1] == 1:
			text=_('F12-Next')
			next_element = button(text, self.pos_y+self.height-2, self.pos_x+self.width-2,align='right')
		else:
			if self.cmdline.has_key('mode') and self.cmdline['mode'] == 'setup':
				text=_('F12-Accept changes')
			elif self.cmdline.has_key('recover') and self.cmdline['recover']:
				text=_('F12-Start Recover Shell')
			else:
				text=_('F12-Start installation')
			next_element = button(text, self.pos_y+self.height-2, self.pos_x+self.width-2,align='right')

		if self.last[0] == 1 :
			text=_('F11-Back')
			back_element = button(text, self.pos_y+self.height-2, self.pos_x+4)
		else:
			back_element = textline('', self.pos_y+self.height-2, self.pos_x+5)

		# add new __NEXT_BUTTON__ element or overwrite existing
		if self.elem_exists("__NEXT_BUTTON__"):
			old_element = self.get_elem('__NEXT_BUTTON__')
			if hasattr(next_element, 'set_on') and hasattr(old_element,'active') and old_element.active:
				next_element.set_on()
			self.elements[self.get_elem_id("__NEXT_BUTTON__")] = next_element
		else:
			next_element.set_on();
			self.add_elem("__NEXT_BUTTON__", next_element)
			self.current=0

		# add new __BACK_BUTTON__ element or overwrite existing
		if self.elem_exists("__BACK_BUTTON__"):
			old_element = self.get_elem('__BACK_BUTTON__')
			if hasattr(back_element, 'set_on') and hasattr(old_element,'active') and old_element.active:
				back_element.set_on()
			self.elements[self.get_elem_id("__BACK_BUTTON__")] = back_element
		else:
			self.add_elem("__BACK_BUTTON__", back_element)


	def layout_reset(self):
		#self.debug('(content)layout_reset')
		self.elements=[]
		self.element_index={}
		self.std_button()
		self.layout()
		self.draw()

	def modvars(self):
		#self.debug('(content)modvars')
		return ''

	def btn_next(self):
		# Should not be used in conjunction with the new menu classes
		#self.debug('(content)btn_next')
		return self.elements[0].get_status()

	def activate_next(self):
		#self.debug('(content)activate_next')
		try:
			self.elements[self.current].set_off()
		except:
			pass

		# This code is really fishy. It assumes that the first menu element
		# is always an input element, which isn't true for several modules
		# Fixing this at a lower level would require quite some restructuring,
		# so catch the exception for now

		self.current=0

		try:
			self.elements[self.current].set_on()
		except:
			pass

	def btn_back(self):
		# Should not be used in conjunction with the new menu classes
		#self.debug('(content)btn_back')
		if self.elements[1].usable():
			return self.elements[1].get_status()
		return 0

	def draw(self):
		if self.startIt:
			self.startIt=0
			try:
				self.start()
			except KeyboardInterrupt:
				self.sub.stop()
			self.layout()
			#if not hasattr(self,"sub"):
			#	self.tab() # activate next (usable) input-element
			if not hasattr(self, 'skip_tab') or not self.skip_tab:
				if self.current==0 and not hasattr(self,"sub"):  # if next input-element is 'back' activate 'next'
					self.tab()
					self.tab()

		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)
		self.header.draw()
		for element in self.elements:
			element.draw()
		if hasattr(self,"sub"):
			self.sub.draw()
		#if self.startIt:
		#	self.startIt=0
		#	try:
		#		self.start()
		#	except KeyboardInterrupt:
		#		self.sub.stop()


	def helptext(self):
		return _('Sorry, no help for this module.')

	def help(self):
		if hasattr(self,"sub"):
			self.sub.help()
		else:
			self.helppad=help_win(self.helptext(),self.max_y,self.max_x)
			self.helppad.draw()

	def modheader(self):
		return ''

	def help_input(self,key):
		#self.debug('(content)help_input')
		if hasattr(self,"sub") and hasattr(self.sub,"helppad"):
			return self.sub.helppad.key_event(key)
		elif hasattr(self,"helppad"):
			return self.helppad.key_event(key)

	def kill_subwin(self):
		'''
		Is called from Main if ESC is pressed
		'''
#		if hasattr(self.sub, 'sub'):
#			self.sub.sub.exit()
		self.sub.exit()

	def input(self, key):
		#self.debug('(content)input')
		return 0

	def move_focus( self, to ):
		"""moves the focus from the current element to the one specified with 'to'"""
		if self.current != to:
			self.elements[ self.current ].set_off()
			self.elements[ to ].set_on()
			self.current = to

	def incomplete(self):
		#self.debug('(content)incomplete')
		return 0

	def tab(self):
		#self.debug('(content)tab')
		# sometime default is not usable
		while not self.elements[self.current].usable():
			self.current = (self.current+1)%len(self.elements)
		if hasattr(self,"sub"):
			if hasattr(self.sub,"tab"):
				self.sub.tab()
		else:
			self.elements[self.current].set_off()
			self.elements[self.current].draw()
			self.current = (self.current+1)%len(self.elements)
			while not self.elements[self.current].usable():
				self.current = (self.current+1)%len(self.elements)
			self.elements[self.current].set_on()
			self.elements[self.current].draw()

	def tab_reverse(self):
		#self.debug('(content)tab_reverse')
		# sometime default is not usable
		while not self.elements[self.current].usable():
			self.current = (self.current+1)%len(self.elements)
		if hasattr(self,"sub"):
			self.sub.tab_reverse()
		else:
			self.elements[self.current].set_off()
			self.elements[self.current].draw()
			self.current = (self.current-1)%len(self.elements)
			while not self.elements[self.current].usable():
				self.current = (self.current-1)%len(self.elements)
			self.elements[self.current].set_on()
			self.elements[self.current].draw()

	def put_result(self, results):
		#self.debug('(content)put_result')
		self.activate_next()
		reset=0
		for key in self.modvars():
			if not results.has_key(key):
				results[key]=''
		if len(self.depends()) > 0:
			for key in self.depends().keys():
				if self.all_results.has_key(key) and results.has_key(key):
					if self.all_results[key] != results[key]:
						for entry in self.depends()[key]:
							results[entry]=''
							reset=1
		self.all_results=copy.deepcopy(results)
		if reset:
			self.layout_reset()

	def get_result(self):
		#self.debug('(content)get_result')
		return self.result()

	def result(self):
		#self.debug('(content)result')
		result=[]
		for i in range(len(self.elements)):
			if self.elements[i].usable():
				result.append(self.elements[i].result())
		if hasattr(self,"subresult"):
			result.append(self.subresult)
		return result

	def start(self):
		pass

	def depends(self):
		return []

	def mod_depends(self):
		return {}

	def ignore(self,key):
		if self.all_results.has_key('to_ignore'):
			if 'all' in self.all_results['to_ignore'].split(' '):
				return True
			for i in self.all_results['to_ignore'].split(' '):
				if i == key:
					return True
		elif self.all_results.has_key('ignore'):
			if 'all' in self.all_results['ignore'].split(' '):
				return True
			for i in self.all_results['ignore'].split(' '):
				if i == key:
					return True
		elif self.all_results.has_key('to_scan'):
			if 'all' in self.all_results['to_scan'].split(' '):
				return True
			for i in self.all_results['to_scan'].split(' '):
				if i == key:
					return True
		elif self.all_results.has_key('scan'):
			if 'all' in self.all_results['scan'].split(' '):
				return True
			for i in self.all_results['scan'].split(' '):
				if i == key:
					return True
		return False

	def check(self,key):
		if self.all_results.has_key('to_check'):
			if key in self.already_checked:
				return False
			if 'all' in self.all_results['to_check'].split():
				self.already_checked.append(key)
				return True
			for i in self.all_results['to_check'].split():
				if i == key:
					self.already_checked.append(key)
					return True
		elif self.all_results.has_key('check'):
			if key in self.already_checked:
				return False
			if 'all' in self.all_results['check'].split():
				self.already_checked.append(key)
				return True
			for i in self.all_results['check'].split():
				if i == key:
					self.already_checked.append(key)
					return True
		return False


	def checkname(self):
		return []

	def profile_complete(self):
		self.debug('check profile for: %s'%self.modheader())
		return True

	def run_profiled(self):
		return {} # do nothing only press the 'next'-button when running profiled

	def profile_prerun(self):
		pass

	def profile_postrun(self):
		pass

	def syntax_is_hostname(self, hostname):
		#_re=re.compile("^[a-z]{1}[a-z,0-9,_,-]*$")
		_re=re.compile("^[a-z]([a-z0-9-]*[a-z0-9])*$")
		if _re.match(hostname):
			return True
		return False
	def syntax_is_domainname(self, domainname):
		#_re=re.compile("^[a-z,0-9]{1}[-,a-z,.,0-9]*$")
		_re=re.compile("^([a-z0-9]([a-z0-9-]*[a-z0-9])*[.])*[a-z0-9]([a-z0-9-]*[a-z0-9])*$")
		if _re.match(domainname):
			return True
		return False

	def syntax_is_windowsdomainname(self, domainname):
		#_re=re.compile("^[a-z,0-9]{1}[-,a-z,.,0-9]*$")
		_re=re.compile("^([a-z]([a-z0-9-]*[a-z0-9])*[.])*[a-z]([a-z0-9-]*[a-z0-9])*$")
		if _re.match(domainname):
			return True
		return False
	def syntax_is_domaincontroller(self, domaincontroller):
		_re=re.compile("^[a-zA-Z].*\..*$")
		if _re.match(domaincontroller):
			return True
		return False

	def profile_f12_run(self):
		pass

class subwin:
	def __init__(self,parent,pos_y,pos_x,width,height,show_border=True,show_shadow=True):
		if parent != None:
			self.parent=parent
			self.max_x=self.parent.max_x
			self.max_y=self.parent.max_y
		else:
			self.max_x=100
			self.max_y=35
		self.show_border = show_border
		self.show_shadow = show_shadow
		self.all_results={}
		self.width=width
		self.height=height
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.pad=curses.newpad(self.height,self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		if self.show_shadow:
			self.shadow = curses.newpad(self.height, self.width)
			self.shadow.bkgd(" ",curses.color_pair(1))
		if self.show_border:
			self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)
		self.reset_layout()
		self.current=0
		self.update_header()
		self.startIt=1
		self.layout()
		temp=self.current
		if len(self.elements) > 0 and not self.elements[self.current].usable():
			while not self.elements[self.current].usable():
				self.current=(self.current+1)%len(self.elements)
				if self.current==temp:
					break

	def update_header(self):
		if len(self.strip_header()):
			y_xtra=0
		else:
			y_xtra=1
		self.header = textline(self.strip_header(), self.pos_y+y_xtra, self.pos_x+self.width-len(self.strip_header())-2)

	# removes all widgets from window
	def reset_layout(self):
		self.elements = []
		self.element_index = {}

	# adds widget to window and assigns name to it
	def add_elem(self, name, element):
		self.element_index[name] = len(self.elements)
		self.elements.append( element )

	# returns widget addressed by name
	def get_elem(self, name):
		return self.elements[ self.element_index[ name ] ]

	# tests if widget addressed by name exists
	def elem_exists(self, name):
		return self.element_index.has_key(name)

	# returns widget id (old behaviour) of widget addressed by name
	def get_elem_id(self, name):
		if self.element_index.has_key(name):
			return self.element_index[ name ]
		return None

	# returns widget addressed by widget id
	def get_elem_by_id(self, id):
		return self.elements[ id ]

	def draw(self):
		if hasattr(self,"sub"):
			self.sub.draw()
		else:
			if self.show_shadow:
				self.shadow.refresh(0,0,self.pos_y+1,self.pos_x+1,self.pos_y+self.height+1,self.pos_x+self.width+1)
			self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)
			self.header.draw()
			for element in self.elements:
				element.draw()
			if self.startIt:
				self.startIt=0
				self.start()

	def helptext(self):
		return _('Sorry, no help for this module.')

	def help(self):
		if hasattr(self,"sub"):
			self.sub.help()
		else:
			self.helppad=help_win(self.helptext(),self.max_y,self.max_x)
			self.helppad.draw()

	def modheader(self):
		return ''

	def strip_header(self):
		if len(self.modheader().strip()):
			return ' %s' % self.modheader().strip()
		return ''


	def input(self, key):
		return 0

	def incomplete(self):
		return 0

	def tab(self):
		# sometime default is not usable
		if hasattr(self,"sub"):
			if hasattr(self.sub,'tab'):
				self.sub.tab()
		elif len(self.elements)>0:
			while not self.elements[self.current].usable():
				self.current = (self.current+1)%len(self.elements)
			if hasattr(self,"sub"):
				self.sub.tab()
			elif len(self.elements)>0:
				self.elements[self.current].set_off()
				self.elements[self.current].draw()
				self.current = (self.current+1)%len(self.elements)
				while not self.elements[self.current].usable():
					self.current = (self.current+1)%len(self.elements)
				self.elements[self.current].set_on()
				self.elements[self.current].draw()

	def tab_reverse(self):
		# sometime default is not usable
		if hasattr(self,"sub"):
			self.sub.tab_reverse()
		elif len(self.elements)>0:
			while not self.elements[self.current].usable():
				self.current = (self.current-1)%len(self.elements)
			if hasattr(self,"sub"):
				self.sub.tab_reverse()
			elif len(self.elements)>0:
				self.elements[self.current].set_off()
				self.elements[self.current].draw()
				self.current = (self.current-1)%len(self.elements)
				while not self.elements[self.current].usable():
					self.current = (self.current-1)%len(self.elements)
				self.elements[self.current].set_on()
				self.elements[self.current].draw()

	def put_result(self, results):
		self.all_results=results

	def get_result(self):
		pass
		#return self.result()

	def exit(self):
		if (self.parent != None):
			delattr(self.parent,"sub")
			self.parent.draw()

	def result(self):
		pass
		#result=[]
		#for i in range(len(self.elements)):
		#	if self.elements[i].usable():
		#		result.append(self.elements[i].result())
		#if hasattr(self,"subresult"):
		#	result.append(self.subresult)
		#return result
	def start(self):
		pass


class yes_no_win(subwin):
	def __init__(self,parent,pos_y,pos_x,width,height, msglist=[], align='middle', callback_yes=None, callback_no=None, default='yes', btn_name_yes=None, btn_name_no=None, *args, **kwargs):
		# adjust size if width and height is too small
		for line in msglist:
			if width < len(line)+4:
				width = len(line)+4
		if height < len(msglist)+6:
			height = len(msglist)+6

		self.msglist = msglist
		self.align = align
		self.callback_yes = callback_yes
		self.callback_no = callback_no
		self.args = args
		self.kwargs = kwargs
		self.win_incomplete = True

		self.btn_name_yes = _('Yes')
		if btn_name_yes:
			self.btn_name_yes = btn_name_yes

		self.btn_name_no = _('No')
		if btn_name_no:
			self.btn_name_no = btn_name_no

		if default.lower() == 'yes':
			self.default = 'BT_YES'
		else:
			self.default = 'BT_NO'

		subwin.__init__(self,parent,pos_y,pos_x,width,height)

	def incomplete(self):
		return self.win_incomplete

	def input(self, key):
		if key in [ 10, 32 ]:
			if self.get_elem('BT_YES').get_status(): #Yes
				sub = self.parent.sub
				self._ok()
				if self.parent.sub is sub:
					self.win_incomplete = False
					return 0
				else:
					return 1
			elif self.get_elem('BT_NO').get_status(): #No
				sub = self.parent.sub
				self._false()
				if self.parent.sub is sub:
					self.win_incomplete = False
					return 0
				else:
					return 1
		elif key == 260 and self.get_elem('BT_NO').active:
			#move left
			self.get_elem('BT_NO').set_off()
			self.get_elem('BT_YES').set_on()
			self.current=self.get_elem_id('BT_YES')
			self.draw()
		elif key == 261 and self.get_elem('BT_YES').active:
			#move right
			self.get_elem('BT_YES').set_off()
			self.get_elem('BT_NO').set_on()
			self.current=self.get_elem_id('BT_NO')
			self.draw()
		return 1

	def layout(self):
		y = 2
		if self.align == 'middle':
			x = self.pos_x+(self.width/2)
		else:
			x = self.pos_x+2
		for msg in self.msglist:
			self.elements.append(textline(msg, self.pos_y+y, x, align=self.align))
			y+=1
		y+=1

		self.add_elem('BT_YES', button(self.btn_name_yes, self.pos_y+y, self.pos_x+4, len(self.btn_name_yes)+5, align='left'))
		self.add_elem('BT_NO', button(self.btn_name_no, self.pos_y+y, self.pos_x+self.width-3, len(self.btn_name_no)+5, align='right'))

		self.current = self.get_elem_id( self.default )
		self.elements[ self.current ].set_on()

	def _ok(self):
		if self.callback_yes != None:
			self.callback_yes('BT_YES', *self.args, **self.kwargs)

	def _false(self):
		if self.callback_no != None:
			self.callback_no('BT_NO', *self.args, **self.kwargs)


class msg_win(subwin):
	def __init__(self,parent,pos_y,pos_x,width,height, msglist=[], align='middle', callback=None, *args, **kwargs):
		# adjust size if width and height is too small
		for line in msglist:
			if width < len(line)+6:
				width = len(line)+6
		if height < len(msglist)+6:
			height = len(msglist)+6

		self.msglist = msglist
		self.align = align
		self.callback = callback
		self.args = args
		self.kwargs = kwargs

		subwin.__init__(self,parent,pos_y,pos_x,width,height)

	def input(self, key):
		if key in [ 10, 32 ]:
			sub = self.parent.sub
			self._ok()
			if self.parent.sub is sub:
				return 0
			else:
				return 1
		return 1

	def layout(self):
		y = 2
		for msg in self.msglist:
			self.elements.append(textline(msg,self.pos_y+y,self.pos_x+1+(self.width/2),self.align))
			y+=1
		y+=1

		self.elements.append(button(_("Ok"),self.pos_y+y,self.pos_x+1+(self.width/2),15,align="middle"))
		self.current=len(self.elements)-1
		self.elements[self.current].set_on()

	def _ok(self):
		if self.callback != None:
			self.callback(*self.args, **self.kwargs)


class activity:
	def __init__(self,pos_y,pos_x,width):
		self.width=width
		self.pos_y=pos_y
		self.pos_x=pos_x
		self.pad=curses.newpad(1,self.width)
		self.pad.bkgd(' ',curses.color_pair(3))
		self.current=0
		self.direction=1

	def draw(self):
		if (self.current==(self.width-2) and (self.direction > 0)) or ((self.current==0) and (self.direction < 0 )):
			self.direction *= (-1)
		self.current += self.direction
		self.pad.erase()
		self.pad.addch(0,self.current,curses.MY_BOARD)
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y,self.pos_x+self.width-1)


	def usable(self):
		return 0

class act_win:
	def __init__(self,parent,header,text,name='sub'):
		self.name=name
		if not hasattr(self, "pos_x"):
			self.pos_y=parent.minY+5
			self.pos_x=parent.minX
		self.parent=parent
		self.width=55
		self.height=6
		self.pad=curses.newpad(self.height,self.width)
		self.shadow = curses.newpad(self.height, self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.shadow.bkgd(" ",curses.color_pair(1))
		self.description=textline(text[:self.width-8],self.pos_y+(self.height/2)-1, self.pos_x+4)
		self.act_bar=activity(self.pos_y+(self.height/2),self.pos_x+4,self.width-8)
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)
		if len(header.strip()):
			header=" %s" % header.strip()
		else:
			header=''
		self.header=textline(header, self.pos_y, self.pos_x+self.width/2-len(header)/2-1)
		self.act=1

	def draw(self):
		self.shadow.refresh(0,0,self.pos_y+1,self.pos_x+1,self.pos_y+self.height+1,self.pos_x+self.width+1)
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+self.height,self.pos_x+self.width)
		self.header.draw()
		self.description.draw()
		thread.start_new_thread(self.loop,())
		self.function()
		self.stop()
		delattr(self,"act_bar")
		delattr(self.parent,self.name)
		time.sleep(0.03)
		self.parent.draw()

	def loop(self):
		while self.act:
			self.act_bar.draw()
			time.sleep(0.03)
		thread.exit()

	def function(self):
		pass

	def stop(self):
		self.act=0

	def tab(self):
		pass

	def tab_reverse(self):
		pass
