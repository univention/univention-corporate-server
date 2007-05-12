#!/usr/bin/python2.3
# -*- coding: utf-8 -*-
#
# Univention Installer
#  classes for the installer interface
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

import curses
import thread
import traceback
import sys
import os
import time
import copy
import re
from local import _

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
	def __init__(self, text, pos_y, pos_x, width, status=0, align='left'):
		self.width = width
		self.set_indent(text)
		if align == 'middle':
			self.pos_x=pos_x-(self.width/2)
		elif align == 'right':
			self.pos_x=pos_x-self.width
		else:
			self.pos_x=pos_x
		self.pos_y=pos_y

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
	def __init__(self, text, pos_y, pos_x, width=-1, status=0, align='left'):
		if width == -1:
			width=len(text)+2+3
		baseObject_2. __init__(self, text, pos_y, pos_x, width, status, align)

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


class bool(baseObject):
	def set_indent(self,text):
		self.indent = 0

	def draw(self):
		self.pad.refresh(0,0,self.pos_y,self.pos_x,self.pos_y+1,self.pos_x+self.width-2)


class input(baseObject_2):
	def __init__(self, text, pos_y, pos_x, width, status=0, align='left'):
		self.cursor=len(text)
		self.invert=curses.newpad(2,2)
		self.invert.bkgd(" ",curses.color_pair(3))
		self.start=0
		self.first=1
		baseObject_2.__init__(self, text, pos_y, pos_x, width)

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
	def __init__(self, dict, pos_y, pos_x, width, visible, status=0, line=1):
		self.width = width
		self.visible=[0,visible]
		self.pos_x=pos_x+1
		self.pos_y=pos_y
		self.line=line
		self.dict={}
		self.list=[]
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

	def usable(self):
		if len(self.list) > 0:
			return 1
		else:
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
	def __init__(self, text, pos_y, pos_x, align='left', width=0):
		self.width=len(text)+1
		if width:
			self.width=width

		if align == 'middle':
			self.pos_x=pos_x-(self.width/2)
		elif align == 'right':
			self.pos_x=pos_x-self.width
		else:
			self.pos_x=pos_x
		self.pos_y=pos_y
		self.text=text
		self.height=1
		self.pad=curses.newpad(self.height, self.width)
		self.bgcolor()
		if len(text) >0 and self.width-1  >= 0:
			self.pad.addstr(0,0,text[:self.width-1])

	def bgcolor(self):
		self.pad.bkgd(" ",curses.color_pair(4))

	def set_text(self,text):
		self.width=len(text)+1
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

class help_win:
	def __init__(self, text, max_y, max_x):
		self.width = 40
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
	def __init__(self,dict,pos_y,pos_x,width,visible,selected=[0],fixed=[]):
		self.pos_x=pos_x
		self.pos_y=pos_y
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
			self.button.append(bool('[ ]', self.pos_y+i, self.pos_x,4))
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
		elif input == 32:
			self.select()
		elif input == 338: # PGDN
			self.set(self.visible[1]-1)
		elif input == 339: # PGUP
			self.set(-(self.visible[1]-1))
		elif input == 10:
			return 'tab'
		self.draw()

	def usable(self):
		if len(self.button):
			return 1
		else:
			return 0

	def result(self):
		return self.dict[self.desc[self.selected[0]].get_text()][0]


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
			self.button.append(bool('[ ]', self.pos_y+i, self.pos_x,4))
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
		self.width=60
		self.height=22
		self.pos_x=(max_x/2)-20
		self.pos_y=(max_y/2)-11
		if not self.pos_y:
			self.pos_y=1
		self.max_x=max_x
		self.max_y=max_y
		self.minX=self.max_x/2-18
		self.minY=self.max_y/2-9
		self.maxWidth=56
		self.maxHeight=17
		self.maxX=self.minX+56
		self.maxY=self.minY+17
		self.cmdline=cmdline
		self.pad=curses.newpad(self.height,self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.pad.border(curses.MY_VLINE,' ',' ',' ',' ',' ',' ',' ')
		self.elements=[]
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

	def std_button(self):
		#self.debug('(content)std_button')
		if self.last[1] == 1:
			text=_('F12-Next')
			self.elements.append(button(text, self.pos_y+self.height-2, self.pos_x+self.width-2,align='right'))
		else:
			if self.cmdline.has_key('mode') and self.cmdline['mode'] == 'setup':
				text=_('F12-Accept changes')
			elif self.cmdline.has_key('recover') and self.cmdline['recover']:
				text=_('F12-Start Recover Shell')
			else:
				text=_('F12-Start installation')
			self.elements.append(button(text, self.pos_y+self.height-2, self.pos_x+self.width-2,align='right'))
		if self.last[0] == 1 :
			text=_('F11-Back')
			self.elements.append(button(text, self.pos_y+self.height-2, self.pos_x+4))
		else:
			self.elements.append(textline('', self.pos_y+self.height-2, self.pos_x+5))
		self.current=0
		self.elements[self.current].set_on();

	def layout_reset(self):
		#self.debug('(content)layout_reset')
		self.elements=[]
		self.std_button()
		self.layout()
		self.draw()

	def modvars(self):
		#self.debug('(content)modvars')
		return ''

	def btn_next(self):
		#self.debug('(content)btn_next')
		return self.elements[0].get_status()

	def activate_next(self):
		#self.debug('(content)activate_next')
		try:
			self.elements[self.current].set_off()
		except:
			pass
		self.current=0
		self.elements[self.current].set_on()

	def btn_back(self):
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
		_re=re.compile("^[a-z]{1}[a-z,0-9,_,-]*$")
		if _re.match(hostname):
			return True
		return False
	def syntax_is_domainname(self, domainname):
		_re=re.compile("^[a-z,0-9]{1}[-,a-z,.,0-9]*$")
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
	def __init__(self,parent,pos_y,pos_x,width,height):
		if parent != None:
			self.parent=parent
			self.max_x=self.parent.max_x
			self.max_y=self.parent.max_y
		else:
			self.max_x=80
			self.max_y=25

		self.all_results={}
		self.width=width
		self.height=height
		self.pos_x=pos_x
		self.pos_y=pos_y
		self.pad=curses.newpad(self.height,self.width)
		self.shadow = curses.newpad(self.height, self.width)
		self.pad.bkgd(" ",curses.color_pair(4))
		self.shadow.bkgd(" ",curses.color_pair(1))
		self.pad.border(curses.MY_VLINE,curses.MY_VLINE,curses.MY_HLINE,curses.MY_HLINE,curses.EDGE_TL,curses.EDGE_TR,curses.EDGE_BL,curses.EDGE_BR)
		self.elements=[]
		self.current=0
		if len(self.strip_header()):
			y_xtra=0
		else:
			y_xtra=1
		self.header=textline(self.strip_header(), self.pos_y+y_xtra, self.pos_x+self.width-len(self.strip_header())-2)
		self.startIt=1
		self.layout()
		temp=self.current
		if len(self.elements) > 0 and not self.elements[self.current].usable():
			while not self.elements[self.current].usable():
				self.current=(self.current+1)%len(self.elements)
				if self.current==temp:
					break

	def draw(self):
		if hasattr(self,"sub"):
			self.sub.draw()
		else:
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
