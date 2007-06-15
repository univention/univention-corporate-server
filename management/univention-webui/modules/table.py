# -*- coding: utf-8 -*-
#
# Univention Webui
#  table.py
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

from uniconf import *

class table(uniconf):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("table")

	def init(self,input,xmlob,node):
		if self.atts.get("borderless") and not self.atts.get("borderless")=="0":
			self.atts["class"]="plain"
		else:
			self.atts["class"]="border"
		for ob in self.args["obs"]:
			self.subobjs.append(ob)
		uniconf.init(self,input,xmlob,node)

class longtable(uniconf):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("long_table")

	def init(self,input,xmlob,node):
		self.input=input

		for ob in self.args["obs"]:
			self.subobjs.append(ob)

		uniconf.init(self,input,xmlob,node)

		if self.input and node!=None:
			contenttags=getSubnodesByName(node,"content")
			if contenttags:
				content=self.gettagtext(contenttags[0].childNodes)
				self.ivars["content"]=unicode(content)

	def myxmlrepr(self, xmlob, node):
		contenttag=xmlob.createElement("content")
		node.appendChild(contenttag)
		return xmlob

	def getcontent(self):
		content = self.ivars.get("content",0)
		if content:
			return int(content)
		else:
			return 0

class tablerow(table):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("row")

class tablecol(table):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("col")

class infobox(tablecol):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("info")
