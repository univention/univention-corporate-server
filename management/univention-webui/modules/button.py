# -*- coding: utf-8 -*-
#
# Univention Webui
#  button.py
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

			
		

