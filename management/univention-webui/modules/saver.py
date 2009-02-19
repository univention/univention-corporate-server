# -*- coding: utf-8 -*-
#
# Univention Webui
#  saver.py
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

import sys
import os
import re
import string
import copy
import ldap
import binascii
from localwebui import _

import univention.debug
import univention.admin.uldap

from uniparts import *
import cPickle
import cStringIO

class saver (uniconf):
	def myxvars(self):    #if the saver allready has xvars, don't overwrite them
		try:
			return self.xvars
		except:
			return {}
	def mytype(self):
		return "saver"
	def put(self,var,content):
		if var in  ("uc_submodule","uc_module","noorder"):
			self.xvars[var]=repr(content)
		else:
			if not content==None:
				self.xvars[var]=self.serialize(content)
			else:
				if self.xvars.has_key(var):
					del self.xvars[var]
	def get(self,var):
		if var in ("uc_submodule","uc_module","noorder"):
			return eval(self.xvars.get(var,"None"))
		return  self.deserialize(self.xvars.get(var,None))

	def serialize(self,ob):
		f=cStringIO.StringIO()
		P=cPickle.Pickler(f)
		P.dump(ob)
		return binascii.b2a_base64(f.getvalue())

	def deserialize(self,st):
		if st==None or st=="":
			return None
		f=cStringIO.StringIO(binascii.a2b_base64(unicode(st)))
		P=cPickle.Unpickler(f)
		erg=P.load()
		return erg

	def clear(self):
		dontclear={"uc_module":1,"uc_virtualmodule":1,"uc_submodule":1,"user":1,"pass":1,"ldap_position":1,"modok":1,"thinclients_off":1,"thinclients_checked":1,"auth_ok":1}
		for var in self.xvars.keys():
			if not dontclear.get(var):
				self.put(var,None)
