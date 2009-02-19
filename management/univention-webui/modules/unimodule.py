# -*- coding: utf-8 -*-
#
# Univention Webui
#  unimodule.py
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

import v
import sys
import os
import re
import string
import copy
import ldap

from uniparts import *
from localwebui import _

def selectIconByName(iconName, iconNameGeneric = 'generic', filesystemSubpath = '/icon/' ):
	'''Select an icon by an given object name.
	iconPathGeneric is the fallback if no icon with the given Name exists'''
	
	defaultType = '.png'
	alternativeType = '.gif'
	
	filesystemLocations = [ '/usr/share/univention-directory-manager/www',
		'/usr/share/univention-webui-style' ]
	filesystemSubpathGeneric = '/icon/'
	
	availablePaths = [filesystemSubpath+iconName+defaultType,
			  filesystemSubpath+iconName+alternativeType ]
	
	if iconNameGeneric:
		availablePaths.append( filesystemSubpathGeneric+iconNameGeneric+defaultType )
		availablePaths.append( filesystemSubpathGeneric+iconNameGeneric+alternativeType )
		
	for iconPath in availablePaths:
	  	for prefix in filesystemLocations:
			if os.path.exists( prefix + iconPath ):
				return iconPath
	return False

class unimodule(uniconf):
	def myname(self):
		return myname()
	def getversion(self):
		return v.version
	def getbuild(self):
		return v.build
	def isallowedtoview(self,ldapob,rgroup,user=None):
		return 1
	
	def usermessage(self,message):
		messages=self.save.get("usermessages")
		if not messages:
			messages=[]
		messages.append(("message",message))
		self.save.put("usermessages",messages)

	def askuser(self,question,val,yes=_("OK"),no=_("Cancel"),yeshelp=_("OK"),nohelp=_("Cancel")):
		messages=self.save.get("usermessages")
		if messages==None:
			messages=[]
		messages.append(("simplequestion",question,val,yes,no,yeshelp,nohelp))
		self.save.put("usermessages",messages)
		

	def mysubmodules(self): #The submodules of this module
		return []

	def myinit(self):
		self.subobjs.append(header(self.mydescription(),{"type":"4"},{}))
	
	def inithandlemessages(self):
		self.grokset=0
		messages=self.save.get("usermessages")
		if messages:
			if messages[0][0] in ["message", "simplequestion"]:
				usertext=messages[0][1]
				self.subobjs.append(table("",
						  {'type':self.save.get( 'header_table_type' , 'content_header' )},
						  {"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[]})]})]}))
				
				self.nbook=notebook('', {}, {'buttons': [(_('Notification'), _('Notification'))], 'selected': 0})
				self.subobjs.append(self.nbook)

				self.usert=htmltext('',{},{'htmltext':["<b>%s</b>"%usertext]})

			if messages[0][0]=="message":
				
				self.usertcol=tablecol("",{'type':'note_layout'},{"obs":[self.usert]})
				self.okbut=button(_("OK"),{'icon':'/style/ok.gif'},{"helptext":_("ok")})
				self.okbutcol=tablecol("",{'type':'note_layout'},{"obs":[self.okbut]})
				self.row1=tablerow("",{},{"obs":[self.usertcol]})
				self.row2=tablerow("",{},{"obs":[self.okbutcol]})
				self.tab=table("",{},{"obs":[self.row1,self.row2]})
				self.subobjs.append(table("",{'type':self.save.get( 'main_table_type' , 'content_main' )},
						{"obs":[tablerow("",{},
							{"obs":[tablecol("",{"colspan":"2"},
								{"obs":[self.tab]})]
							})]
						})
					)
				return 1
			elif messages[0][0]=="simplequestion":
				if self.askedfor(messages[0][2],0):
					self.usertcol=tablecol("",{"colspan":"2",'type':'note_layout'},{"obs":[self.usert]})
					self.okbut=button(messages[0][3],{'icon':'/style/ok.gif'},{"helptext":messages[0][5]})
					self.okbutcol=tablecol("",{'type':'note_layout'},{"obs":[self.okbut]})
					self.cabut=button(messages[0][4],{'icon':'/style/cancel.gif'},{"helptext":messages[0][6]})
					self.cabutcol=tablecol("",{'type':'note_layout'},{"obs":[self.cabut]})
					self.row1=tablerow("",{},{"obs":[self.usertcol]})
					self.row2=tablerow("",{},{"obs":[self.okbutcol,self.cabutcol]})
					self.tab=table("",{},{"obs":[self.row1,self.row2]})
					self.subobjs.append(table("",{'type':self.save.get( 'main_table_type' , 'content_main' )},
							{"obs":[tablerow("",{},
								{"obs":[tablecol("",{"colspan":"2"},
									{"obs":[self.tab]})]
								})]
							})
						)
					return 1
				else:
					return 0
	def applyhandlemessages(self):
		ret=0
		button=0
		messages=self.save.get("usermessages")
		if messages:
			if messages[0][0] == "simplequestion":
				if self.askedfor(messages[0][2],0):
					ret=1
					if self.okbut.pressed():
						self.askedfor(messages[0][2],1)
						button=1
					if self.cabut.pressed():
						self.askedfor(messages[0][2],None)
						button=1
			else:
				messages=messages[1:]
				ret=1
			if button:
				messages=self.save.get("usermessages")
				messages=messages[1:]
			self.save.put("usermessages",messages)
			return ret
		
	def askedfor(self,a,b):
		return 0

	def userinfo(self,infotext):
		self.save.put("infobox_information_text",infotext)

	def userinfo_append(self,new):
		old=self.save.get('infobox_information_text')
		if old:
			self.save.put('infobox_information_text', old+'<br>'+new)
		else:
			self.save.put('infobox_information_text', new)

class realmodule:
	def __init__(self, id, name, description='', virtualmodules=[], submodules=[]):
		self.id=id
		self.name=name
		self.description=description
		self.virtualmodules=[]
		self.submodules=[]
		if not submodules:
			self.virtualmodules=virtualmodules
		if not virtualmodules:
			self.submodules=submodules

class virtualmodule:
	def __init__(self, id, name, description='', submodules=[]):
		self.id=id
		self.name=name
		self.description=description
		self.submodules=submodules

class submodule:
	def __init__(self, id, name, description=''):
		self.id=id
		self.name=name
		self.description=description
