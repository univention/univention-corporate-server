# -*- coding: utf-8 -*-
#
# Univention Webui
#  table.py
#
# Copyright 2004-2010 Univention GmbH
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

class dynamic_longtable(table):
	def myinit(self):
		self.save = self.parent.save
	def mytype(self):
		return("dynamic_longtable")

## 	def init(self,input,xmlob,node):
## 		self.input=input

## 		for ob in self.args["obs"]:
## 			self.subobjs.append(ob)

## 		uniconf.init(self,input,xmlob,node)

## 		#if self.input and node!=None:
## 		#	contenttags=getSubnodesByName(node,"content")
## 		#	if contenttags:
## 		#		content=self.gettagtext(contenttags[0].childNodes)
## 		#		self.ivars["content"]=unicode(content)

## 	def myxmlrepr(self, xmlob, node):
## 		#contenttag=xmlob.createElement("content")
## 		#node.appendChild(contenttag)

## 		if hasattr(self, "start"): # not needed
## 			tag=xmlob.createElement("start")
## 			node.appendChild(tag)
## 			tagtext=xmlob.createTextNode(self.start)
## 			tag.appendChild(tagtext)

## 		if hasattr(self, "visible"): # not needed
## 			tag=xmlob.createElement("visible")
## 			node.appendChild(tag)
## 			tagtext=xmlob.createTextNode(self.visible)
## 			tag.appendChild(tagtext)

## 		return xmlob

## 	def getcontent(self):
## 		content = self.ivars.get("content",0)
## 		if content:
## 			return int(content)
## 		else:
## 			return 0

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
