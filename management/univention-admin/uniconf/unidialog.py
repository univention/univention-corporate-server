# -*- coding: utf-8 -*-
#
# Univention Admin
#  the basic dialogs
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

import sys, os, re, string, copy, types
ldir = '/usr/share/univention-webui/modules'
sys.path.append(ldir)
os.chdir(ldir)
import univention.debug

uniconf_mods={}
for m in ['modabout', 'modspacer','modbrowse', 'modedit', 'modlogout', 'modrelogin', 'modwizard', 'modself']:
	uniconf_mods[m] = __import__(m)

import unimodule
from local import _
from uniparts import *
import univention.admin.uldap

class unidialog(unimodule.unimodule):

	def __init__(self,a,b,c):
		b['site_title']='Univention Admin' 
		b['header_img']='style/header_admin.gif'
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
		
		position=self.save.get('ldap_position')
		if not position:
			position=univention.admin.uldap.position(self.uaccess.base)
	
		# display info text
		infotext=self.save.get("infobox_information_text")
		if infotext and type(infotext) in [types.StringType, types.UnicodeType]:
			self.subobjs.append(infobox("",{},{"obs":[htmltext("",{},{"htmltext":[infotext]})]}))

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
		
		# create instance of current module
		if self.save.get("uc_module")!=None and self.save.get("uc_module")!="none" :
			try:
				module = __import__("mod%s"%self.save.get("uc_module"))
				self.mod=module.create("",{},{"messagedir":ldir+"messages/","uaccess":self.uaccess,"submodule":self.save.get("uc_submodule")})#,"ldapdata":self.LDAPDATA
			except ImportError:
				pass
		if self.mod != None:
			self.subobjs.append(self.mod)
	
		# if there's no current module, display welcome dialog
		if ( self.save.get("uc_module")==None or self.save.get("uc_module")=="none" ) and self.save.get("auth_ok"):
			if not self.inithandlemessages():
				
				header_text = _("Welcome to Univention Admin")

				introduction_text = _("Univention Admin enables you to manage all components of your Univention Corporate Server (UCS) Domain.")

				component_texts = []
				component_texts.append([_("Wizards"),
						       _("Common tasks like administration of users, groups, servers, desktops and printers can easily be handled using the wizards.")])
				component_texts.append([_("Navigation"),
						       _("Besides everything you can do with the wizards, the navigation provides you also an interface for many other settings, including structural extensions like containers, organizational units and connected policies, advanced DNS and DHCP configuration or settings for Univention Admin itself.")])
				component_texts.append([_("Console"),_("The <a target=parent href=/console/>Univention Console</a> provides the possibilty to configure local settings on every UCS managed machine, e.g. network configuration or local software-installation. A link to the Univention Console for a machine can be found at the UCS object in the computer wizard.")])
				if self.save.get( 'personal_use' ) == '1':
					component_texts.append([_("License"),_("You are using the \"Free for personal use\" edition. Find more information on the about page.")])
				component_texts.append([_("Further Information"),_("For more information about UCS, Univention Admin and other Univention Tools take a look at the documentation or the online-forum on <a target=parent href=http://www.univention.de>www.univention.de</a>.")])
					

				
				self.subobjs.append(table("",
							  {'type':'content_header'},
							  {"obs":[(tablerow({},{},{'obs':[tablecol("",{'type':'browse_layout'},{"obs":[]})]}))]})
						    )

				self.nbook=notebook('', {}, {'buttons': [(header_text, header_text)], 'selected': 0})
				self.subobjs.append(self.nbook)

				subtables = []

				rows = []
				rows.append(tablerow({},{'border':'0'},{'obs':[tablecol({},{'colspan':'2','type':'welcome_layout'},{"obs":[htmltext('',{'border':'0'},{'htmltext':['<br><b>',introduction_text,'</b>']})]})]}))
				rows.append(tablerow({},{},{'obs':[tablecol({},{'colspan':'2','type':'welcome_layout'},{"obs":[]})]}))
				subtables.append(table('',{},{'obs':rows}))

				emptycol = tablecol({},{'type':'welcome_layout'},{"obs":[]})
				emptycol_span = tablecol({},{'colspan':'2','type':'welcome_layout'},{"obs":[]})

				rows = []
				for shorttext, longtext in component_texts:
					objects = [[tablecol('',{'type':'welcome_layout'},{"obs":[htmltext('', {'border':'0'}, {'htmltext':['<b>',shorttext,'</b>']})]}),
						    emptycol],
						   [emptycol,
						    tablecol('',{'type':'welcome_layout'},{"obs":[htmltext('', {'border':'0'}, {'htmltext':[longtext]})]})],
						   ]
					for obj in objects:
						rows.append(tablerow({},{'border':'0'},{'obs':obj}))
				
				subtables.append(table('',{},{'obs':rows}))
				self.subobjs.append(table('',
							  {'type':'content_main'},
							  {"obs":[tablerow("",{},{"obs":[tablecol("",{'type':'welcome_layout'},{"obs":subtables})]})]})
						    )

		# display info box with username
		if good_login:
			infoboxrows=[]
			position=self.save.get('ldap_position')
			logindomain=position.getLoginDomain()
			loginpos=univention.admin.uldap.position(position.getBase())
			loginpos.setDn(logindomain)
			logindomain=loginpos.getPrintable()
			if logindomain:
				logindomain='@'+logindomain
			else:
				logindomain=''
			utext=text("",{},{"text":[_("You are logged in as: %s%s") % (self.save.get("user"), logindomain)]})
			infoboxrows.append(tablerow("",{'border':'1'},{"obs":[tablecol("",{'type':'welcome_layout'},{"obs":[utext]})]}))
			self.subobjs.insert(0,headertext(_("// logged in as: %s%s")%(self.save.get("user"),logindomain),{},{}))
			self.subobjs.insert(0,title(_("// logged in as: %s%s")%(self.save.get("user"),logindomain),{},{}))
		else:
			self.subobjs.insert(0,title("Univention Admin",{},{}))
					
		# display menu
		menuheader=text("",{},{"text":[_("Univention Admin")]})
		menuheaderitem=menuitem("",{},{"item":menuheader})
		menulist=[]
		self.mbutlist=[]
		self.smbutlistlist=[]
		modlist=[]

		
		for tmpnam, tmpmod in uniconf_mods.items():
			if hasattr(tmpmod,'mymenunum'):
				menunum=tmpmod.mymenunum()
				if type(menunum) is types.ListType:
					for num in menunum:
						modlist.append((num, tmpnam, tmpmod))
				else:
					modlist.append((menunum, tmpnam, tmpmod))

		modlist.sort()
		activemoduleinmenu=self.save.get("uc_module")
		if self.save.get("uc_module") in ["usermessage","askuser"]:
			activemoduleinmenu=self.save.get("backtomodule")
		
		try:
			realmod=uniconf_mods['mod'+activemoduleinmenu]
		except KeyError:
			pass
			
		for num, tmpnam, tmpmod in modlist:
			modname=tmpnam[3:]
				
			modok=self.save.get("modok")
			if not modok:
				modok={}
			if not modname=="relogin":
				if not modok.get(modname):
					modok[modname]=1
				if not self.save.get("auth_ok"):
					continue
			self.save.put("modok",modok)

			subs=[]
			if modname==activemoduleinmenu: 
				try:
					subs=realmod.mysubmodules()
				except:
					pass
			if modname == self.save.get('edit_return_to'):
				try:
					curmod=__import__("mod"+modname)
					subs=curmod.mysubmodules()
				except:
					pass

			moduleinfo=tmpmod.myinfo(self.save.get("settings"))


			if moduleinfo.virtualmodules:
				for virtmod in moduleinfo.virtualmodules:
					if virtmod=="spacer":
						mit=space('',{'size':'2'},{})
					else:
						smbutlist=[]
						submenulist=[]
						icon_path='/icon/'+virtmod.id+'.png'
						if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
							icon_path='/icon/'+virtmod.id+'.gif'
						if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
							icon_path='/icon/generic.gif'

						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "virtmodule %s with icon %s" % (virtmod.id, icon_path))

						if self.save.get("uc_virtualmodule",'')==virtmod.id:
							mbut=button(virtmod.name,{'icon':icon_path,'active':'1'},{"helptext":virtmod.description,'active':'1'})
						else: 
							mbut=button(virtmod.name,{'icon':icon_path},{"helptext":virtmod.description})

						self.mbutlist.append([mbut, moduleinfo.id, virtmod.id])

						if virtmod.id == self.save.get('uc_virtualmodule'):
							for submod in virtmod.submodules:
								icon_path='/icon/submods/'+submod.id+'.png'
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/'+submod.id+'.gif'	
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/submods/'+submod.id+'.png'
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/submods/'+submod.id+'.gif'	
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/generic.gif'
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "submodule %s with icon %s" % (submod.id, icon_path))
								if self.save.get("uc_submodule",'') == submod.id or (not self.save.get("uc_submodule",'') and submod.id in ['find','users/self']):
									# this button is active, find is default in modwizard (the default should be moved into the submodule itself)
									smbut=button(submod.name,{'icon':icon_path,'active':'1'},{"helptext":submod.description,'active':'1'})
								else:
									smbut=button(submod.name,{'icon':icon_path},{"helptext":submod.description})
								smbutlist.append([smbut, moduleinfo.id, virtmod.id, submod.id])
								submenulist.append(menuitem("",{},{"item":smbut},n=submod.id))

							self.smbutlistlist.append(smbutlist)
						mit=menuitem("",{},{"item":mbut,"menu":menu("",{},{"items":submenulist})})

					menulist.append(mit)
			else:
				smbutlist=[]
				submenulist=[]
				if moduleinfo.name:
					icon_path = '/icon/generic.gif'
					if hasattr(tmpmod,'mymenuicon'):
						icon_path=tmpmod.mymenuicon()

					
					if moduleinfo.id==self.save.get('uc_module','') and self.save.get("uc_submodule",'')==None: # this button is active
						mbut=button(moduleinfo.name,{'icon':icon_path,'active':'1'},{"helptext":moduleinfo.description,'active':'1'})
					else: 
						mbut=button(moduleinfo.name,{'icon':icon_path},{"helptext":moduleinfo.description})
					self.mbutlist.append([mbut, moduleinfo.id])
	
					for submod in moduleinfo.submodules:
						smbut=button(submod.name,{},{"helptext":submod.description})
						smbutlist.append([smbut, moduleinfo.id, submod.id])
						submenulist.append(menuitem("",{},{"item":smbut},n=submod.id))

					self.smbutlistlist.append(smbutlist)
					mit=menuitem("",{},{"item":mbut,"menu":menu("",{},{"items":submenulist})})
					menulist.append(mit)

				else: # it's a spacer
					pass


		m=menu("",{},{"items":menulist})
		self.subobjs.append(m)
	
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
		for mbut in self.mbutlist:
			if hasattr(mbut[0],'pressed'):
				if mbut[0].pressed():
					reload_settings=self.save.get('reload_settings')
					self.save.clear()
					self.save.put('reload_settings', reload_settings)
					self.save.put("uc_module",mbut[1])
					if len(mbut) > 2:
						self.save.put("uc_virtualmodule",mbut[2])
					else:
						self.save.put("uc_virtualmodule", None)
					self.save.put("uc_submodule",None)
			
		for smbutlist in self.smbutlistlist:
			for but in smbutlist:
				if hasattr(but[0],'pressed'):
					if but[0].pressed():
						reload_settings=self.save.get('reload_settings')
						self.save.clear()
						self.save.put('reload_settings', reload_settings)
						if len(but) > 3:
							self.save.put("uc_module", but[1])
							self.save.put("uc_virtualmodule", but[2])
							self.save.put("uc_submodule",but[3])
						else:
							self.save.put("uc_module", but[1])
							self.save.put("uc_submodule",but[2])

	def handlemessage(self,msg):
		if msg=="msg:reinit":
			self.dirty=1


