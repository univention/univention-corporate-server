# -*- coding: utf-8 -*-
#
# Univention Webui
#  notebook.py
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

from uniconf import *

import univention.debug

def getSubnodesByName(node,name):
	list=node.getElementsByTagName(name)
	list2=[]
	for l in list:
		if l.parentNode==node:
			list2.append(l)
	return list2

class notebook(uniconf):
	def mytype(self):
		return("notebook")
	def myivars(self):
		selected = "0";
		closed = "-1";
		if self.ivars.get( "selected" ):
			selected = self.ivars[ "selected" ]
		if self.ivars.get( "closed" ):
			closed = self.ivars[ "closed" ]
		return { "selected": selected, "closed" : closed }

	def myinit(self):
		if self.args.get("selected"):
			self.ivars["selected"]=unicode(self.args["selected"])
		else:
			self.ivars["selected"]="0"
	def butrepr(self,xmlob,node,desc,helptext,active):
		tag=xmlob.createElement("text")
		node.appendChild(tag)
		tagtext=xmlob.createTextNode(desc)
		tag.appendChild(tagtext)
		tag=xmlob.createElement("helptext")
		node.appendChild(tag)
		tagtext=xmlob.createTextNode(helptext)
		tag.appendChild(tagtext)
		var=xmlob.createElement("var")
		node.appendChild(var)
		name=xmlob.createElement("name")
		var.appendChild(name)
		nametext=xmlob.createTextNode("pressed")
		name.appendChild(nametext)
		value=xmlob.createElement("content")
		var.appendChild(value)
		if active:
			tag=xmlob.createElement("active")
			node.appendChild(tag)
			tagtext=xmlob.createTextNode("1")
			tag.appendChild(tagtext)
		return xmlob

	def myxmlrepr(self,xmlob,node):
		number=0
		var=xmlob.createElement("var")
		var.setAttribute("internal","1")
		node.appendChild(var)
		name=xmlob.createElement("name")
		var.appendChild(name)
		nametext=xmlob.createTextNode("selected")
		name.appendChild(nametext)
		value=xmlob.createElement("content")
		var.appendChild(value)
		valuetext=xmlob.createTextNode(unicode(self.args.get("selected","0")))
		value.appendChild(valuetext)
		for button in self.args.get("buttons",[]):
			closeable = False
			icon, statusicon = "", ""
			if len(button) == 5: # specific for UMC
				text, help, icon, statusicon, closeable = button
			elif len(button) == 4: # specific for UMC
				text, help, icon, statusicon = button
			else: # Univention Admin
				text, help = button

			if closeable:
				closeable = "1"
			else:
				closeable = "0"

			tag=xmlob.createElement("button")
			if closeable:
				tag.setAttribute( 'closeable', closeable )
			if icon:
				tag.setAttribute( 'icon', icon )
			if statusicon:
				tag.setAttribute( 'statusicon', statusicon )
			node.appendChild(tag)

			active = 0
			if self.args.get("selected") and int(self.args["selected"]) == number:
				active = 1
			elif not self.args.get("selected") and number == 0:
				active = 1

			xmlob=self.butrepr(xmlob,tag,text,help,active)

			if closeable == "1": # add a "close"-button
				#number +=1
				tag=xmlob.createElement("button")

				tag.setAttribute( 'closebutton', "1" )

				node.appendChild(tag)
				xmlob=self.butrepr(xmlob, tag, text, help, active)

			number+=1
		return xmlob

	def init(self,input,xmlob,node):
		self.bpressed=0
		self.input=input
		self.type=self.mytype()
		self.ivars=self.myivars()
		if self.input and node!=None:
			num=0
			for n in getSubnodesByName(node,"button"):
				closebutton = False
				if n.attributes.has_key("closebutton"):
					closebutton = True
				vars=getSubnodesByName(n,"var")
				for v in vars:
					nametag=getSubnodesByName(v,"name")[0]
					valuetag=getSubnodesByName(v,"content")[0]
					name=self.gettagtext(nametag.childNodes)
					value=self.gettagtext(valuetag.childNodes)
					if value:
						if closebutton:
							self.closed = 1
							self.ivars["closed"]=unicode(num-1)
						else:
							self.ivars["selected"]=unicode(num)
							self.bpressed = 1
				if not closebutton:
					num+=1
			if not self.bpressed:
				self.ivars["selected"]=unicode(self.args.get("selected"))

	def getselected(self):
		if not self.input:
			return None
		return int(self.ivars.get("selected",0))

	def getclosed(self):
		if not self.input:
			return None
		return int(self.ivars.get("closed",-1))
