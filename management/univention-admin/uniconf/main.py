#
# Univention Admin
#  provides the main dialog class
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
sys.path.append('/usr/share/univention-webui/modules/')
ldir = '/usr/share/univention-admin/uniconf/'
sys.path.append(ldir)
os.chdir(ldir)
import univention.debug, gettext

uniconf_mods={}
for m in ['modabout', 'modspacer','modbrowse', 'modedit', 'modlogout', 'modrelogin', 'modwizard']:
	uniconf_mods[m] = __import__(m)

import unimodule
from local import _
from uniparts import *
import univention.admin.uldap

class new_saver:
	def __init__(self):
		self.dict={}
	def put(self, var, content):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver put %s=%s' % (var, content))
		self.dict[var]=content
	def get(self, var, default=''):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver get %s=%s' % (var, self.dict.get(var, '')))
		if var in ["uc_submodule","uc_module","noorder"] and not self.dict.has_key(var):
			return None
		return self.dict.get(var, default)
	def clear(self):
		dontclear=["uc_module","uc_virtualmodule","uc_submodule","user","pass","ldap_position","modok","thinclients_off","thinclients_checked","auth_ok"]
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ALL, 'saver clear')
		for key in self.dict.keys():
			if not key in dontclear:
				del self.dict[key]

class dialog(unimodule.unimodule):

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
				component_texts.append([_("Further Information"),_("For more information about UCS, Univention Admin and other Univention Tools take a look at the documentation or the online-forum on <a target=parent href=http://www.univention.de>www.univention.de</a>.")])


				rows=[(tablerow({},{},{'obs':[tablecol({},{'colspan':'2'},{"obs":[header(header_text,{"type":"4"},{})]})]}))]
				rows.append(tablerow({},{},{'obs':[tablecol({},{'colspan':'2'},{"obs":[htmltext('',{},{'htmltext':['<br><b>',introduction_text,'</b>']})]})]}))
				rows.append(tablerow({},{},{'obs':[tablecol({},{'colspan':'2'},{"obs":[]})]}))
				self.subobjs.append(table('',{},{'obs':rows}))

				emptycol = tablecol({},{'border':'0'},{"obs":[]})
				emptycol_span = tablecol({},{'colspan':'2','border':'0'},{"obs":[]})

				rows = []
				for shorttext, longtext in component_texts:
					objects = [[tablecol('',{},{"obs":[htmltext('', {'border':'0'}, {'htmltext':['<b>',shorttext,'</b>']})]}),
						    emptycol],
						   [emptycol,
						    tablecol('',{},{"obs":[htmltext('', {'border':'0'}, {'htmltext':[longtext]})]})],
						   ]
					for obj in objects:
						rows.append(tablerow({},{'border':'0'},{'obs':obj}))

				self.subobjs.append(table('',{'border':'1'},{'obs':rows}))

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
			infoboxrows.append(tablerow("",{'border':'1'},{"obs":[tablecol("",{'border':'1'},{"obs":[utext]})]}))
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

			moduleinfo=tmpmod.myinfo()

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

						if moduleinfo.id==self.save.get('uc_module','') and self.save.get("uc_virtualmodule",'')==virtmod.id: # this button is active
							mbut=button(virtmod.name,{'icon':icon_path,'active':'1'},{"helptext":virtmod.description,'active':'1'})
						else:
							mbut=button(virtmod.name,{'icon':icon_path},{"helptext":virtmod.description})

						self.mbutlist.append([mbut, moduleinfo.id, virtmod.id])

						if virtmod.id == self.save.get('uc_virtualmodule'):
							for submod in virtmod.submodules:
								icon_path='/icon/submods/'+submod.id+'.png'
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/submods/'+submod.id+'.gif'
								if not os.path.exists('/usr/share/univention-admin/www'+icon_path):
									icon_path='/icon/generic.gif'
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "submodule %s with icon %s" % (submod.id, icon_path))
								if self.save.get("uc_submodule",'') == submod.id or (not self.save.get("uc_submodule",'') and submod.id=='find'):
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

				else: # it's a spacer
					mbut=space('',{'size':'2'},{})
				self.mbutlist.append([mbut, moduleinfo.id])

				for submod in moduleinfo.submodules:
					smbut=button(submod.name,{},{"helptext":submod.description})
					smbutlist.append([smbut, moduleinfo.id, submod.id])
					submenulist.append(menuitem("",{},{"item":smbut},n=submod.id))

				self.smbutlistlist.append(smbutlist)
				mit=menuitem("",{},{"item":mbut,"menu":menu("",{},{"items":submenulist})})
				menulist.append(mit)

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
					self.save.put("uc_module",mbut[1])
					self.save.put('reload_settings', reload_settings)
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
						#self.dirty=1#not needed anymore
						#break

	def handlemessage(self,msg):
		if msg=="msg:reinit":
			self.dirty=1

def genErrorMessage(head, messagelines, mailto = None):
	#FIXME: use existing xml objects instead of directly printing XML?
	utfxml = '<?xml version="1.0" encoding="utf-8"?><dialog id="main" main="">'
	utfxml += '<htmltext>generror: header: %s<br></htmltext>'%header
	small=0
	import cgi
	for n, i in enumerate(messagelines):
		if n>0:
			small=1
			utfxml+='<header id="exception%d" type="%d"><text>bla: %s</text></header>' % (n, 3+small, cgi.escape(i))
		else:
			utfxml+='<header id="exception%d" type="%d"><text>bla2: %s</text></header>' % (n, 3+small, cgi.escape(i))
	if mailto:
		text = _('Report this error to Univention Feedback &lt;feedback@univention.de&gt;')
		link = '<a href="%s">%s</a>' % (mailto, text)
		utfxml += '<htmltext>%s</htmltext>' % cgi.escape(link)
	utfxml+='</dialog>'
	return utfxml

def genErrorMailto(messagelines):
	from urllib import quote, urlencode
	from urlparse import urlunparse
	scheme = 'mailto'
	address = quote('Univention Feedback <feedback@univention.de>')
	subject = 'Bugreport: Univention Admin Traceback'
	body = '''%s:
1) %s
2) %s
3) %s

----------

''' % (_('Please take a second to provide the following information'),
       _('steps to reproduce'),
       _('expected result'),
       _('actual result'))
	for line in messagelines:
		body += line
	query = { 'subject': subject,
		  'body':    body }
	url = urlunparse((scheme, '', address, '', urlencode(query), ''))
	return url.replace('+', '%20')

def processRequest(xmltext, save, uaccess):
	if not uaccess:
		return genErrorMessage(_("No LDAP-Connection"),[_("Is the LDAP-Server started and reachable ?")])
	try:
		object_changed=0

		# parse XML
		got_input=0
		if xmltext:
			try:
				xmlin=parseString(xmltext)
				got_input=1
			except Exception,e:
				sys.stderr.write("\nparser says: "+str(e)+"\n"+xmltext[0:4])

		# create dialog instance
		t = dialog("",{"main":""},{"messagedir":ldir+"messages/"})
		t.save = save
		t.uaccess = uaccess

		if got_input == 1:
			xmlob=xmlin
			t.init(1,xmlob,xmlob.documentElement)
			got_input=0
		else:
			xmlob=Document()
			t.init(0,xmlob,xmlob.documentElement)

		t.check()
		t.apply()

		# we have to reinitialize because of changes in the structure
		xmlob=Document()
		t = dialog("",{"main":None},{"messagedir":ldir+"messages/"})
		t.save = save # write back the status of the main module
		t.uaccess = uaccess
		t.init(0,xmlob,xmlob.documentElement)

		t.save.put("noorder","")
		xmlob=t.xmlrepr(xmlob,xmlob)
		xmltext=xmlob.toxml()

		templist=xmltext.split("\n")
		templist[0]="<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
		utfxml=string.join(templist,"\n")

		save.put("infobox_information_text",'')
		return utfxml

	except univention.admin.uexceptions.ldapError, msg:
		return genErrorMessage(_("Can not process LDAP-Request:"),["%s: %s"%(_('LDAP error'),msg),_("You need to login again.")])

	except:
		# print traceback

		import traceback
		info = sys.exc_info()
		lines = traceback.format_exception(*info)
		return genErrorMessage(_("A Python Exception has occured:"), lines, genErrorMailto(lines))


# this is more a temporary solution
def new_uaccess():

	host = ''
	base = ''
	port = ''
	ridbase = ''

	errors=0
	try:
		import univention_baseconfig
		ubc=univention_baseconfig.baseConfig()
		# FIXME: ubc.load "eats" IOError exceptions...
		ubc.load()
		host=ubc["ldap/master"]
		base=ubc["ldap/base"]
		port=ubc["ldap/port"]
	except ImportError:
		errors=1
	except IOError:
		errors=1

	if not port:
		# should be safe to fall back to default LDAP port
		port = "389"

	return univention.admin.uldap.access(host=host, port=int(port), base=base)
