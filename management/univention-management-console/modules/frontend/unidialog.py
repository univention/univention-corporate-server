# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: basic dialog class
#
# Copyright 2006-2010 Univention GmbH
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

import sys, os, re, string, copy, types
ldir = '/usr/share/univention-webui/modules'
sys.path.append(ldir)
# os.chdir(ldir)
import univention.debug
import univention_baseconfig

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

uniconf_mods={}
for m in ['modconsole']:#['modabout', 'modspacer','modbrowse', 'modedit', 'modlogout', 'modrelogin', 'modwizard', 'modself']:
	uniconf_mods[m] = __import__(m)

import unimodule
#from local import _
_ = univention.management.console.Translation('univention-management-console-frontend').translate
from uniparts import *
import univention.admin.uldap

class unidialog(unimodule.unimodule):

	def __init__(self,a,b,c):
		if baseConfig.has_key('umc/title') and baseConfig['umc/title']:
			b['site_title']=baseConfig['umc/title']
		else:
			b['site_title']='Univention Management Console'
		if baseConfig.has_key('umc/title/image') and \
			   baseConfig['umc/title/image']:
			b['header_img']=baseConfig['umc/title/image']
		else:
			b['header_img']='themes/images/default/management-console.gif'
		unimodule.unimodule.__init__(self,a,b,c)

	def mytype(self):
		return "dialog"

	def myxvars(self):
		return {}

	def init(self,a,b,c):
		self.xnode=c
		self.xmlob=b
		self.mod=None
		uniconf.init(self,a,b,c)

	def myinit(self):
		global uniconf_mods

		# change to modrelogin if not logged in
		good_login=0
		if not self.save.get("auth_ok"):
			if not self.save.get("uc_module")=="usermessage":
				self.save.put("uc_module","relogin")
				self.save.put("uc_submodule","none")
			else:
				pass
		else:
			good_login=1

		# FIXME: just start modconsole
		self.save.put("uc_module","console")
		good_login=1

		# create instance of current module
		if self.save.get("uc_module")!=None and self.save.get("uc_module")!="none" :
			try:
				module = __import__("mod%s"%self.save.get("uc_module"))
				self.mod=module.create("",{},{'req':self.req,"messagedir":ldir+"messages/","uaccess":self.uaccess,"submodule":self.save.get("uc_submodule")})#,"ldapdata":self.LDAPDATA
			except ImportError:
				pass
		# display info text
		infotext=self.save.get("infobox_information_text")
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'new infotext: %s' % infotext)
		if self.mod != None:
			self.subobjs.append(self.mod)
		if infotext and type(infotext) in [types.StringType, types.UnicodeType]:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'new infotext: %s' % infotext)
			self.subobjs.append(infobox("",{},{"obs":[htmltext("",{},{"htmltext":[infotext]})]}))

	def handlesmsg(self,msg):
		return 1

	def apply(self):
		if self.mod!=None:
			try:
				self.mod.apply()
			except univention.admin.uexceptions.base, ex:
				self.usermessage(_("error while modifying: %s %s")%(ex.message,str(ex)))
		elif self.applyhandlemessages():
			return
		for msg in self.messagebuff:
			if self.handlesmsg(msg):
				self.handlemessage(msg)

	def handlemessage(self,msg):
		if msg=="msg:reinit":
			self.dirty=1
