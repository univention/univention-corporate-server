# -*- coding: utf-8 -*-
#
# Univention Webui
#  uniconf.py
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

from xml.dom.minidom import *
from localwebui import _

import types

import univention.debug
import sys

def getSubnodesByName(node,name):
	list=node.getElementsByTagName(name)
	list2=[]
	for l in list:
		if l.parentNode==node:
			list2.append(l)
	return list2

class uniconf:
	def get_input(self):
		text=self.xvars.get("usertext")
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'search text = %s' % text)
		if text:
			return text.strip()
		else:
			return None
	def __init__(self,de,at,ar,n=None):
		#no instances of this one planed
		self.inited=0
		self.desc=de
		self.atts=at
		self.args=ar
		self.parent=self
		self.messagebuff=[]
		self.subobjs=[]
		self.xvars={}
		self.ivars={}
		self.type=""
		self.id="main"
		self.invalid=0
		self.dirty=0
		self.firstrun=0
		self.input=0
		self.name=n
		# request
		self.req = None
		if self.args and self.args.has_key ('req'):
			self.req = self.args['req']
			del self.args['req']
		for i in self.atts.keys():
			if not type(self.atts[i]) in [types.StringType, types.UnicodeType]:
				if not self.atts[i]==None:
					raise Exception,"attributes must be strings: %s" % str(i)

	def findlongestfit(self,st,stlist,oldfitlen):
		stlist.sort()
		l=0
		found=None
		for i in stlist:
			if i==st:
				return (st,0)
			if len(i)>len(st):
				continue
			if i[0:len(st)-1]!=st:
				continue
			dummy=len(i)
			if dummy>l:
				l=dummy
				found=i
			if dummy<l:
				break
		return (found,len(st)-l)



	def hide(self):
		self.atts["internal"]=None

	def show(self):
		if self.atts.get("internal","not set")!="not set":
			del self.atts["internal"]


	def find_id(self,node,id,lnfit=None):
		if node == None:
			return None
		if lnfit==None:
			lnfit=len(id)
		iddict={}
		for n in node.childNodes:
			try:
				iddict[n.getAttribute("id")]=n
			except:
				pass
		nextid,lnf=self.findlongestfit(id,iddict.keys(),lnfit)
		if nextid==None:
			return None
		if lnf==0:
			return iddict[nextid]
		return self.find_id(iddict.get(nextid,None),id,lnfit=lnf)


	def init(self,input,xmlob,node):
		self.input=input
		self.type=self.mytype()
		if self.type=="saver":
			self.xvars=self.myxvars()
			self.ivars=self.myivars()
			self.myinit()
			return
		if node!=None:
			if input:
				try:
					inv=node.getAttribute("invalid")
				except:
					inv="0"
				if inv!="1":
					vars=getSubnodesByName(node,"var")
					self.xvars,self.ivars=self.parsevars(vars)
					self.parseatts(node)
				else:
					self.xvars=self.myxvars()
					self.ivars=self.myivars()
			else:
				self.xvars=self.myxvars()
				self.ivars=self.myivars()
		else:
			self.xvars=self.myxvars()
			self.ivars=self.myivars()
		if self.xvars==None:
			self.xvars={}
		if self.ivars==None:
			self.ivars={}
		self.myinit()
		id={}
		for obj in self.subobjs:
			try:
				obj.parent=self
			except Exception,ex:
				pass
			if 1:#obj.name==None:
				try:
					obj.name=obj.mytype()
				except Exception,ex:
					sys.stderr.write("Problem with: "+unicode(obj)+" "+unicode(ex)+"\n")


			if not id.has_key(obj.name):
				id[obj.name]=0
			else:
				id[obj.name]=id[obj.name]+1
			if id[obj.name]!=0:
				obj.name=obj.name+unicode(id[obj.name])
			obj.id= self.id +"_%s"%(obj.name)
			obj.init(input,xmlob,self.find_id(node,obj.id))


	def check(self):
		for obj in self.subobjs:
			obj.check()


	def apply(self):
		for i in self.subobjs:
			i.apply()

	def xmlrepr(self,xmlob,node):
		existing=self.find_id(xmlob,self.id)
		self.myel=xmlob.createElement(self.type)
		if existing ==None:
			node.appendChild(self.myel)
		else :
			existing.parentNode.replaceChild(self.myel,existing)
		xmlob=self.reprattrs(xmlob,self.myel)
		xmlob=self.reprvars(xmlob,self.myel)
		xmlob=self.myxmlrepr(xmlob,self.myel)

		for obj in self.subobjs :
			xmlob=obj.xmlrepr(xmlob,self.myel)
		return xmlob



	def reprvars(self,xmlob,node):
		if self.atts.has_key("passive"):
			passivetag=xmlob.createElement("passive")
			node.appendChild(passivetag)
		if self.atts.has_key("focus"):
			focustag=xmlob.createElement("focus")
			node.appendChild(focustag)
		if self.atts.has_key("defaultbutton"):
			defaultbuttontag=xmlob.createElement("defaultbutton")
			node.appendChild(defaultbuttontag)

		vars=self.xvars.keys()
		for var in vars:
			vartag=xmlob.createElement("var")
			node.appendChild(vartag)
			nametag=xmlob.createElement("name")
			vartag.appendChild(nametag)
			nametexttag=xmlob.createTextNode(var)
			nametag.appendChild(nametexttag)
			contenttag=xmlob.createElement("content")
			vartag.appendChild(contenttag)
			if self.xvars[var]!=None:
				contenttexttag=xmlob.createTextNode(self.xvars[var])
				contenttag.appendChild(contenttexttag)
		vars=self.ivars.keys()
		for var in vars:
			vartag=xmlob.createElement("var")
			vartag.setAttribute("internal","1")
			node.appendChild(vartag)
			nametag=xmlob.createElement("name")
			vartag.appendChild(nametag)
			nametexttag=xmlob.createTextNode(var)
			nametag.appendChild(nametexttag)
			contenttag=xmlob.createElement("content")
			vartag.appendChild(contenttag)
			if self.ivars[var]!=None:
				contenttexttag=xmlob.createTextNode(self.ivars[var])
				contenttag.appendChild(contenttexttag)

		return xmlob


	def reprattrs(self,xmlob,node):
		if self.invalid:
			self.atts["invalid"]="1"
		att=self.atts.keys()
		for a in att:
			if not self.atts[a]==None :
				node.setAttribute(a,self.atts[a])
			else :
				node.setAttribute(a,"")
		node.setAttribute("id",self.id)
		return xmlob

	def myxmlrepr(self,xmlob,xmlrepr):
		return xmlob

	def myxvars(self):
		return {}
	def myivars(self):
		return {}

	def myinit(self):
		pass

	def gettagtext(self,nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data
		return rc

	def parsevars(self,vars):
		xvardic={}
		ivardic={}
		for v in vars:
			nametag=getSubnodesByName(v,"name")[0]
			valuetag=getSubnodesByName(v,"content")[0]

			name=self.gettagtext(nametag.childNodes)
			value=self.gettagtext(valuetag.childNodes)
			atts=[]
			if v.hasAttributes():
				for i in xrange(0,v.attributes.length):
					att=v.attributes.item(i).name
					atts.append(att)
				if "internal" in atts:
					ivardic[name]=value
				else:
					xvardic[name]=value
			else:
				xvardic[name]=value
		return xvardic,ivardic



	def parseatts(self,node):
		atts=[]

		if node.attributes!=None:
			for i in xrange(0,node.attributes.length):
				att=node.attributes.item(i).name
			atts.append(att)

			for att in atts:
				self.atts[att]=node.getAttribute(att)


	def xmlpar(self,xmlob,node):
		if node == None:
			return
		try:
			inv=node.getAttribute("invalid")
		except:
			inv="0"
		if inv!="1":
			vars=getSubnodesByName(node,"var")
			self.xvars,self.ivars=self.parsevars(vars)
			self.parseatts(node)
			for ob in self.subobjs:
				n=self.find_id(xmlob,ob.id)
				if n==None:
					continue
				ob.xmlpar(xmlob,n)



	def message(self,msg):
		if not self.handlesmsg(msg):
			self.messagebuff.append(msg)
			if self.parent == self:
				raise "unhandled message" + unicode(msg) + " in " + self.id
			self.parent.message(msg)
		else :
			self.messagebuff.append(msg[:])


	def mytype(self):
		#to be implemented by each object
		pass

	def handlesmsg(self,msg):
		#to be implemented by each object
		return 0
