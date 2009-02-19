# -*- coding: utf-8 -*-
#
# Univention Webui
#  question.py
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
import univention.debug as ud
	
class question(uniconf):
	def mytype(self):
		return "question"
	
	

	def myinit(self):
		if self.args.has_key("helptext"):
			self.helptext=self.args["helptext"]
		else:
			self.helptext=""



	def myxmlrepr(self,xmlob,node):
		tag=xmlob.createElement("description")
		node.appendChild(tag)
		
		tagtext=xmlob.createTextNode(self.desc)
		tag.appendChild(tagtext)
		
		tag=xmlob.createElement("helptext")
		node.appendChild(tag)
		
		tagtext=xmlob.createTextNode(self.helptext)
		tag.appendChild(tagtext)
		return xmlob

	
class question_text(question):
	
	def mytype(self):
		return "question_text"

	def myxvars(self):
		v = {}
		if self.xvars.has_key("usertext"):
			v["usertext"] = self.xvars["usertext"]
		elif self.args.has_key("usertext"):
			v ["usertext"] = self.args["usertext"]
		else:
			v["usertext"] = None

		return v


class question_ltext(question_text):
	
	def mytype(self):
		return "question_ltext"

class question_date(question_text):

	def mytype(self):
		return "question_date"


class question_dojo_date_widget(question_text):

	def mytype(self):
		return "question_dojo_date_widget"


class question_ip_adress(question_date):
	def mytype(self):
		return "question_ip_address"

class question_bool(question_text):

	def mytype(self):
		return "question_bool"

	def myinit(self):
		question.myinit(self)
		if self.args.has_key('button'):
			self.subobjs.append(self.args['button'])

	def deselect(self):
		self.xvars["usertext"]=None

	def select(self):
		self.xvars["usertext"]="selected"
	def selected(self):
		if self.xvars.has_key("usertext"):
			if self.xvars["usertext"]!=None and self.xvars["usertext"]!="":
				return "selected"
		return ""

class question_secure(question_text):

	def mytype(self):
		return "question_secure"

class question_choice(question):
	def mytype(self):
		return "question_choice"
	def myinit(self):
		question.myinit(self)
		self.choicelist=self.args["choicelist"]
		x=0
		for entry in self.choicelist:
			if entry["name"]=='0':
				self.choicelist[x]["name"]="ascii-null-escape"
			if entry.get("selected")=='0':
				self.choicelist[x]["selected"]="ascii-null-escape"
		if self.args.has_key("button"):
			self.subobjs.append(self.args["button"])
	def myxvars(self):
		v={}
		for c in self.args.get("choicelist",[]):
			if c.get("name")=='0':
				c["name"]="ascii-null-escape"
			if c.get("selected")=='0':
				c["selected"]="ascii-null-escape"
			if c.get("name",None):
				v[c["name"]]=c.get("selected",None)
		return v

	def reprchoice(self,xmlob,choice,node):
		choicetag=xmlob.createElement("choice")
		node.appendChild(choicetag)
		nametag=xmlob.createElement("name")
		choicetag.appendChild(nametag)
		nametexttag=xmlob.createTextNode(choice["name"])
		nametag.appendChild(nametexttag)
		descriptiontag=xmlob.createElement("description")
		choicetag.appendChild(descriptiontag)
		descriptiontexttag=xmlob.createTextNode(choice["description"])
		descriptiontag.appendChild(descriptiontexttag)

		if choice.has_key("level"): # is an attr of choice
			choicetag.setAttribute("level",choice["level"])

		return xmlob

	def getselected(self):
		for selection in self.xvars.keys():
			if self.xvars.get(selection,None):
				return selection
	def get_input(self):
		return self.getselected()
	def myxmlrepr(self,xmlob,node):
		xmlob=question.myxmlrepr(self,xmlob,node)
		for choice in self.choicelist:
			xmlob=self.reprchoice(xmlob,choice,node)
		return xmlob

class question_select(question_choice):
	def mytype(self):
		return "question_select"

class question_dojo_select(question_choice):
	def mytype(self):
		return "question_dojo_select"

class language_dojo_select(question_choice):
	def mytype(self):
		return "language_dojo_select"

class question_dojo_comboselect(question_choice):
	def mytype(self):
		return "question_dojo_comboselect"

class question_mselect(question_select):
	def mytype(self):
		return "question_mselect"

	def getselected(self):
		selected=[]
		for selection in self.choicelist:
			if self.xvars.get(unicode(selection["name"])):
					if selection["name"]=="ascii-null-escape":
						selected.append("0")
					else:
						selected.append(selection["name"])
		return selected


class question_file(question_text):

	def mytype(self):
		return "question_file"

	def __split_fields(self):
		text=self.xvars.get("usertext")
		if text and '@|@' in text:
			ud.debug(ud.ADMIN, ud.INFO, 'question.py: question_file: usertext=%s' % text)
			tmpfile, fname, fsize, ftype, ferror = text.split('@|@')
			self.xvars['usertext'] = tmpfile.replace('||', '|')
			self.xvars['filename'] = fname.replace('||', '|')
			self.xvars['filesize'] = fsize.replace('||', '|')
			self.xvars['filetype'] = ftype.replace('||', '|')
			self.xvars['fileerror'] = ferror.replace('||', '|')

	def get_filename(self):
		self.__split_fields()
		return self.xvars.get("filename")

	# warning: optional value: sometimes value is not set!
	def get_filesize(self):
		self.__split_fields()
		return self.xvars.get("filesize")

	def get_filetype(self):
		self.__split_fields()
		return self.xvars.get("filetype")

	def get_fileerror(self):
		self.__split_fields()
		return self.xvars.get("fileerror")

	def get_input(self):
		self.__split_fields()
		text=self.xvars.get("usertext")
		if text:
			return text.strip()
		return None
