# -*- coding: utf-8 -*-
#
# Univention Webui
#  button.py
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

class button(uniconf):
	def mytype(self):
		return "button"

	def myxvars(self):
		return {"pressed":None}

	def myinit(self):
		self.helptext=self.args["helptext"]

	def myxmlrepr(self,xmlob,node):
		if "active" in self.args.keys():
			tag=xmlob.createElement("active")
			node.appendChild(tag)
			tagtext=xmlob.createTextNode(self.args["active"])
			tag.appendChild(tagtext)
		tag=xmlob.createElement("text")
		node.appendChild(tag)
		tagtext=xmlob.createTextNode(self.desc)
		tag.appendChild(tagtext)
		tag=xmlob.createElement("helptext")
		node.appendChild(tag)
		tagtext=xmlob.createTextNode(self.helptext)
		tag.appendChild(tagtext)
		return xmlob

	def pressed(self):
		p= self.xvars.get("pressed","")
		if p!=None and p!="":
			self.xvars["pressed"]=""
			return 1
		return 0
	
	def setActive(self,active):
		self.args["active"]=active
		self=button(self.desc,self.atts,self.args,self.name)

			
		
		

