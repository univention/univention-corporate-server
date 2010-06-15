# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the basic dialogs
#
# Copyright (C) 2004-2010 Univention GmbH
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

import sys, os, re, string, copy, types, locale
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
import univention.config_registry as ucr

class unidialog(unimodule.unimodule):

	def __init__(self,a,b,c):
		b['site_title']='Univention Directory Manager'
		b['header_img']= unimodule.selectIconByName( 'header_directory_manager', filesystemSubpath = '/style/' )
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
		self.have_logout = False
		self.have_browse = False
		self.have_about = False
		self.have_users = False
		self.have_computers = False

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
				self.mod=module.create("",{},{'req':self.req, "messagedir":ldir+"messages/","uaccess":self.uaccess,"submodule":self.save.get("uc_submodule")})#,"ldapdata":self.LDAPDATA
			except ImportError:
				pass
		if self.mod != None:
			self.subobjs.append(self.mod)

		self.mbutlist=[]


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
			# utext=text("",{},{"text":[_("You are logged in as: %s%s") % (self.save.get("user"), logindomain)]})
			# infoboxrows.append(tablerow("",{},{"obs":[tablecol("",{'type':'welcome_layout'},{"obs":[utext]})]}))
			# self.subobjs.insert(0,headertext(_("// logged in as: %s%s")%(self.save.get("user"),logindomain),{},{}))
			self.subobjs.insert(0,title(_("// logged in as: %s%s")%(self.save.get("user"),logindomain),{},{}))
		else:
			self.subobjs.insert(0,title("Univention Directory Manager",{},{}))

		# display menu
		menuheader=text("",{},{"text":[_("Univention Directory Manager")]})
		menuheaderitem=menuitem("",{},{"item":menuheader})
		menulist=[]
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
						icon_path = unimodule.selectIconByName( virtmod.id )

						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "virtmodule %s with icon %s" % (virtmod.id, icon_path))

						if self.save.get("uc_virtualmodule",'')==virtmod.id:
							mbut=button(virtmod.name,{'icon':icon_path,'active':'1'},{"helptext":virtmod.description,'active':'1'})
						else:
							mbut=button(virtmod.name,{'icon':icon_path},{"helptext":virtmod.description})

						self.mbutlist.append([mbut, moduleinfo.id, virtmod.id])
						if virtmod.id == 'users/user':
							self.have_users = True
						if virtmod.id == 'computers/compuer':
							self.have_computers = True

						if virtmod.id == self.save.get('uc_virtualmodule'):
							for submod in virtmod.submodules:
								icon_path = unimodule.selectIconByName( submod.id, filesystemSubpath = '/icon/', iconNameGeneric = '' )
								if not icon_path or not type(icon_path) in types.StringTypes:
									univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "submodule %s failed selectIcon with %s" % (submod.id, icon_path))
									icon_path = unimodule.selectIconByName( submod.id, filesystemSubpath = '/icon/submods/', iconNameGeneric = 'generic' )
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "submodule %s with icon %s" % (submod.id, icon_path))
								if self.save.get("uc_submodule",'') == submod.id or (not self.save.get("uc_submodule",'') and submod.id in ['find','users/self']):
									# this button is active, find is default in modwizard (the default should be moved into the submodule itself)
									smbut=button(submod.name,{'icon':icon_path,'active':'1'},{"helptext":submod.description,'active':'1'})
								else:
									smbut=button(submod.name,{'icon':icon_path},{"helptext":submod.description})
								smbutlist.append([smbut, moduleinfo.id, virtmod.id, submod.id])
								submenulist.append(menuitem("",{},{"item":smbut},n=submod.id))

							self.smbutlistlist.append(smbutlist)
						# don't add modself to the menu, since UCS 2.3 it is displayed in the header
						# if virtmod.id != 'self' or True:
						mit=menuitem("",{},{"item":mbut,"menu":menu("",{},{"items":submenulist})})

					#if virtmod.id != 'self' or True:
					menulist.append(mit)
			else:
				smbutlist=[]
				submenulist=[]
				if moduleinfo.name:
					icon_path = unimodule.selectIconByName( 'generic' )
					if hasattr(tmpmod,'mymenuicon'):
						icon_path=tmpmod.mymenuicon()


					if moduleinfo.id==self.save.get('uc_module','') and self.save.get("uc_submodule",'')==None: # this button is active
						mbut=button(moduleinfo.name,{'icon':icon_path,'active':'1'},{"helptext":moduleinfo.description,'active':'1'})
					else:
						mbut=button(moduleinfo.name,{'icon':icon_path},{"helptext":moduleinfo.description})
					self.mbutlist.append([mbut, moduleinfo.id])
					if moduleinfo.id == 'browse':
						self.have_browse = True
					elif moduleinfo.id == 'about':
						self.have_about = True
					elif moduleinfo.id == 'logout':
						self.have_logout = True

					for submod in moduleinfo.submodules:
						smbut=button(submod.name,{},{"helptext":submod.description})
						smbutlist.append([smbut, moduleinfo.id, submod.id])
						submenulist.append(menuitem("",{},{"item":smbut},n=submod.id))

					if not moduleinfo.id in [ 'about', 'logout', 'browse' ]:
						self.smbutlistlist.append(smbutlist)
						mit=menuitem("",{},{"item":mbut,"menu":menu("",{},{"items":submenulist})})
						menulist.append(mit)

				else: # it's a spacer
					pass

		if self.save.get("auth_ok"):
			lang = locale.getlocale( locale.LC_MESSAGES )
			if lang and lang[0]:
				lang = lang[0].split('_',1)[0]
			else:
				lang = 'en'
			header_item = []
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
            <div id="header">
                <!-- @start header-title -->
                <h1 class="header-title">
                    <span class="hide">univention</span> <a href="#" title="Start">directory manager</a>
                </h1>
                <!-- @end header-title -->
            <!-- @end header -->
					"""]})
			header_item.append(usermenu)
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
					<div id="user-menu">
					<!-- @start info -->
					<div id="info">
						<ul>
							<li class="help">
								<a title="%(help)s" href="/help.php?lang=%(lang)s&app=udm" target="_blank" onclick="helpwindow=window.open('/help.php?lang=%(lang)s&app=udm','pophelp','toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=no,width=530,height=450,top=150,left=100');helpwindow.focus();return false;">%(help)s</a>
							</li>
							<li class="spacer"> </li>
							<li class="about">
					""" % {'help': _('Help'), 'lang': lang} ]})
			header_item.append(usermenu)
			about_button=button(_('About UDM'),{'link':'1'},{"helptext":_('About UDM')})
			header_item.append(about_button)
			self.mbutlist.append([about_button, 'about', None])
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
							</li>
						</ul>
						
						<br class="clear"/>
					"""]})
			header_item.append(usermenu)
						
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
						<span class="session">
							%(loginmessage)s <span class="name">%(username)s</span>
						</span>
					</div>
					<!-- @end info -->
					""" % { 'loginmessage': _('You are logged in as'), 'username': self.save.get("user")}
					]})
			header_item.append(usermenu)
					
			# the my profile link must be disabled because we have a submenu and these submenu couldn't be displayed
			# in the header
			#usermenu = htmltext ('', {}, \
			#	{'htmltext': [_("""
			#		<!-- @start account options -->
			#		<ul class="options">
			#			<li class="profile">
			#		""")]})
			#header_item.append(usermenu)
			#self_button=button(_('My Profile'),{'icon':'/icon/users/self.png'},{"helptext":_('My Profile')})
			#header_item.append(self_button)
			#self.mbutlist.append([self_button, 'self', None])
			#usermenu = htmltext ('', {}, \
			#	{'htmltext': [_("""
			#			</li>
			#			<li class="logout">
			#		""")]})
			#header_item.append(usermenu)

			#usermenu = htmltext ('', {}, \
			#	{'htmltext': [_("""
			#		<!-- @start account options -->
			#		<ul class="options">
			#			<li class="logout">
			#		""")]})
			# header_item.append(usermenu)
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
					<!-- @start account options -->
					<ul class="options">
						<li class="profile">
					"""]})
			header_item.append(usermenu)
			if self.have_browse:
				self_button=button(_('Navigation'),{'icon':'/icon/browse.png'},{"helptext":_('Navigation')})
				header_item.append(self_button)
				self.mbutlist.append([self_button, 'browse', None])
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
						</li>
						<li class="logout">
					"""]})
			header_item.append(usermenu)
			logout_button=button(_('Logout'),{'icon':'/icon/exit.png'},{"helptext":_('Logout')})
			header_item.append(logout_button)
			self.mbutlist.append([logout_button, 'logout', None])
			usermenu = htmltext ('', {}, \
				{'htmltext': ["""
						</li>
					</ul>
					<br class="clear"/>
					<!-- @end account-options -->
				</div>
            </div>
					"""]})
			header_item.append(usermenu)

			header_item.reverse()

			for hi in header_item:
				self.subobjs.insert(0,hi)

		# if there's no current module, display welcome dialog
		if ( self.save.get("uc_module")==None or self.save.get("uc_module")=="none" ) and self.save.get("auth_ok"):
			if not self.inithandlemessages():
				# add top header
				topheader = htmltext('', {}, {'htmltext': ['<div id="content-wrapper-top">&nbsp;</div>']} )
				self.subobjs.append(topheader)
				# load UCR
				configRegistry = ucr.ConfigRegistry()
				configRegistry.load()
				if configRegistry.get('update/available','no') in ('yes'):
					# update is available
					lo = self.uaccess
					position=self.save.get('ldap_position')
					if not position:
						position=univention.admin.uldap.position(self.uaccess.base)
					# get user groups from UCR that should get a hint msg
					updateAvailableGroups = configRegistry.get('directory/manager/web/update/available/groups', None)
					if updateAvailableGroups:
						displayMsg = False
						# get userdn
						username = self.save.get("user")
						if username:
							try:
								userdn = lo.searchDn(filter='(uid=%s)' % username, base=position.getBase(), scope='sub')[0]
							except:
								userdn = None
						# check all specified groups if user is member
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "unidialog: updatemsg: user=%s" % userdn)
						for grp in updateAvailableGroups.split(','):
							grp = grp.strip()
							try:
								groups = lo.searchDn(filter='(&(cn=%s)(objectClass=univentionGroup)(uniqueMember=%s))' % (grp,userdn), base=position.getBase(), scope='sub')[0]
							except:
								groups = None
							if groups:
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "unidialog: updatemsg: groups=%s" % groups)
								displayMsg = True
								break
						if displayMsg:
							updatemsg = htmltext ('', {}, \
													{'htmltext': ["""
													<div id="content-wrapper-error">
													<h3>%(headline)s</h3>
													<p>%(msg)s</p>
													</div>
													""" % { 'headline': _('UCS Update Available'),
															'msg': _('An update for UCS is available. Please visit <a target="_blank" href="/univention-management-console/index.php?init_umccmd=update/overview">online update module</a> of Univention Management Console to install.')}
																]})
							self.subobjs.append(updatemsg)

				welcomemessage = htmltext ('', {}, \
					{'htmltext': ["""
					<div id="content-wrapper-relative">
					<!-- @start content-head -->
					<div id="content-head">
						<!-- @start tab-navigation -->
						<ul class="tabs">
							<li class="active">
								<a title="%(welcome)s" href="#">%(welcome)s</a>
							</li>
						</ul>
						<!-- @end tab-navigation -->
					</div>				
					<!-- @end content-head -->
					""" % {'welcome': _("Welcome to Univention Directory Manager")}
					]})
				self.subobjs.append(welcomemessage)
					
				welcomemessage = htmltext ('', {}, \
					{'htmltext': ["""
					<!-- @start content -->
					<div id="content">
						<ul>
							<li>
								<p>
									%(introduction_text)s
								</p>
							</li>
					""" %
					{'introduction_text': _("Univention Directory Manager enables you to manage all components of your Univention Corporate Server (UCS) Domain.")}
					]})
				self.subobjs.append(welcomemessage)
					
				if self.have_users:
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							<li class="assistance">
							<h2 class="h-link">
						"""
						]})
					self.subobjs.append(welcomemessage)
					mbut=button(_('Wizards'),{'link':'1', 'type': 'h-link'},{"helptext":_('Wizards')})
					self.mbutlist.append([mbut, 'wizard', 'users/user'])
					self.subobjs.append(mbut)
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							</h2>
							<p>
								%(wizard_text)s
							</p>
						</li>
					""" % {'wizard_text': _("Common tasks like administration of users, groups, servers, desktops and printers can easily be handled by using the wizards.") }
					]})
					self.subobjs.append(welcomemessage)
				if self.have_browse:
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							<li class="navigation">
							<h2 class="h-link">
						"""
						]})
					self.subobjs.append(welcomemessage)
					mbut=button(_('Navigation'),{'link':'1', 'type': 'h-link'},{"helptext":_('Navigation')})
					self.mbutlist.append([mbut, 'browse', None])
					self.subobjs.append(mbut)
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							</h2>
							<p>
								%(wizard_text)s
							</p>
						</li>
					""" % {'wizard_text': _("Besides everything you can do with the wizards, the navigation provides you also with an interface for many other settings, including structural extensions like containers, organizational units and connected policies, advanced DNS and DHCP configuration or settings for Univention Directory Manager itself.") }
					]})
					self.subobjs.append(welcomemessage)
				#component_texts.append([_("Univention Management Console"), _("The <a target=parent href=/univention-management-console/>Univention Management Console</a> provides the possibilty to configure local settings on every UCS managed machine, e.g. network configuration or local software-installation. A link to the Univention Management Console for a machine can be found at the computer object wizard."),
				#					'/univention-management-console/', None])
				welcomemessage = htmltext ('', {}, \
					{'htmltext': ["""
						<li class="umc">
						<h2 class="h-link"> <a title="Univention Management Console" target=parent href=/univention-management-console/ class="h-link">Univention Management Console</a></h2>
							<p>
								%(wizard_text)s
							</p>
						</li>
				""" % {'wizard_text': _("The <a target=parent href=/univention-management-console/>Univention Management Console</a> provides the possibilty to configure local settings on every UCS managed machine, e.g. network configuration or local software-installation. A link to the Univention Management Console for a machine can be found at the computer object wizard.")}
				]})
				self.subobjs.append(welcomemessage)
				if self.save.get( 'personal_use' ) == '1' and self.have_about:
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							<li class="license">
							<h2 class="h-link">
						"""
						]})
					self.subobjs.append(welcomemessage)
					mbut=button(_('License'),{'link':'1', 'type': 'h-link'},{"helptext":_('License')})
					self.mbutlist.append([mbut, 'about', None])
					self.subobjs.append(mbut)
					welcomemessage = htmltext ('', {}, \
						{'htmltext': ["""
							</h2>
							<p>
								%(wizard_text)s
							</p>
						</li>
					""" % {'wizard_text': _("You are using the \"Free for personal use\" edition. Find more information on the about page.") }
					]})
					self.subobjs.append(welcomemessage)

				welcomemessage = htmltext ('', {}, \
					{'htmltext': ["""
						<li class="furtherinformation">
						<h2 class="h-link"> <a title="Univention website" target=parent href=http://www.univention.de class="h-link">%(link)s</a></h2>
							<p>
								%(wizard_text)s
							</p>
						</li>
				""" % {'link': _("Further Information"), 
						'wizard_text': _("For more information about UCS, Univention Directory Manager and other Univention Tools take a look at the documentation or the online-forum on <a target=parent href=http://www.univention.de>www.univention.de</a>.") }
				]})
				self.subobjs.append(welcomemessage)

				content_end = htmltext ('', {}, \
					{'htmltext': ["""
						</ul>
					</div>
					<!-- @end content -->
					</div>
					"""]})
				self.subobjs.append(content_end)




		m=menu("",{},{"items":menulist})
		self.subobjs.append(m)

	def handlesmsg(self,msg):
		return 1

	def apply(self):

		if self.mod!=None:
			try:
				self.mod.apply()
			except univention.admin.uexceptions.base, ex:
				self.usermessage(_("error while modifying: %s %s")%(ex.message,unicode(ex)))
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
						if len(mbut) > 3:
							self.save.put("uc_submodule",mbut[3])
						else:
							self.save.put("uc_submodule",None)
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
