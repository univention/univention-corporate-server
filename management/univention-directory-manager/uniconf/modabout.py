# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  show the about dialog
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

import os
import sys
import ldap
import string
import re
import datetime

import unimodule
from uniparts import *
from local import _

import univention.admin.uldap
import univention.admin.modules
import univention_baseconfig
import univention.debug

import ldif

class ldifParser(ldif.LDIFParser):
        dn = None
        mod_list = []
        dncount = 0
        base = None
        err = ""

        def __init__(self, input_file, ignored_attr_types=None, max_entries=0, process_url_schemes=None, line_sep='\n' ):
                ldif.LDIFParser.__init__(self,input_file, ignored_attr_types, max_entries, process_url_schemes,line_sep)

        def check(self,base):
                ldif.LDIFParser.parse(self)

                #count dn
                if self.dncount == 0:
                        self.err = _("No Base DN has been found.")
                elif self.dncount > 1:
                        self.err = _("More than one Base DN has been defined.")

                #check base
                if self.base != base or base == None:
                        self.err = _("Wrong Base DN. Expected was %s but %s has been found.") % (base,self.base)

                return self.err

        def handle(self,dn,entry):
                if dn == None or dn == "":
                        self.err = _("No Base DN has been found.")
                        return

                self.dn = dn
                self.dncount += 1

                if 'univentionLicenseBaseDN' in entry:
                        self.base = "%s" % entry['univentionLicenseBaseDN'][0]
                else:
                        self.err = _("No Base DN has been defined.")
                        return

                #create modification list
                for atr in entry:
                        val = ()
                        for v in entry[atr]:
                                val += (v,)
                        self.mod_list.insert(0,(ldap.MOD_REPLACE, atr, val))

def create(a,b,c):
	return modabout(a,b,c)

def myinfo(settings):
	if settings.listAdminModule('modabout'):
		return unimodule.realmodule("about", _("About"), _("About Univention Directory Manager"))
	else:
		return unimodule.realmodule("about", "", "")

def myrgroup():
	return ""

def mywgroup():
	return ""

def mymenunum():
	return 600

def mymenuicon():
	return unimodule.selectIconByName( 'about' )

class modabout(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def myinit(self):
		self.save=self.parent.save
		self.lo=self.args["uaccess"]

		if self.inithandlemessages():
			return

		self.subobjs.append(table("",
					  {'type':'content_header'},
					  {"obs":[tablerow("",{},{"obs":[tablecol("",{'type':'about_layout'},{"obs":[]})]})]})
				    )

		self.nbook = notebook('', {}, {'buttons': [("%s %s" % (_('About'),_("Univention Directory Manager")),"%s %s" % (_('About'),_("Univention Directory Manager")))], 'selected': 0})
		self.subobjs.append(self.nbook)


		rows=[]

		baseConfig=univention_baseconfig.baseConfig()
		baseConfig.load()

		## Admin
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
			header(_("Univention Directory Manager"),{"type":"4"},{})
			]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Version')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[self.getversion()]})]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Build')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[self.getbuild()]})]})
			]}))

		## UCS
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Hostname')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[baseConfig['hostname']]})]})
			]}))

		version_string = ""
		codename = ""
		
		for key in ['version/version','version/patchlevel','version/security-patchlevel']:
			if baseConfig.has_key(key) and baseConfig[key]:
				if version_string:
					version_string = "%s-%s" % (version_string,baseConfig[key])
				else:
					version_string = baseConfig[key]

		if baseConfig.has_key("version/releasename"):
			codename = baseConfig["version/releasename"]

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('local Installation')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':["%s %s (%s)" % (_('Univention Corporate Server'), version_string, codename)]})]})
			]}))

		days = baseConfig.get( 'ssl/validity/days', '' )
		if days:
			days = datetime.datetime.fromtimestamp( int( days ) * 24 * 60 * 60 ).strftime( "%x" )

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Validity date of the SSL certificate')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ days ]})]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
			]}))

		## OX
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"3",'type':'about_layout'},{"obs":[
			header(_("Open-Xchange"),{'width':'400', "type":"4"},{})
			]})
			]}))

		### get ox context and integration versions
		ldap_base = baseConfig['ldap_base']
		domain_name = "%s.%s" % (baseConfig['hostname'], baseConfig['domainname'])
		result_set = self.lo.search("(&(objectClass=oxContext)(oxHomeServer=%s))" % domain_name)

		for ox_context in result_set:
			name = ox_context[0].split(",")[0][3:]
			ox_context_info = ox_context[1]
			rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
				header(_("Context: %s" % name),{"type":"4"},{})
				]})
				]}))			
			if ox_context_info.has_key("oxAdminDaemonVersion"):
				rows.append(tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Admin Daemon Version:')]})]}),
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ ox_context_info['oxAdminDaemonVersion'][0] ]})]})
					]}))
			if ox_context_info.has_key("oxGroupwareVersion"):
				rows.append(tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Groupware Version:')]})]}),
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ ox_context_info['oxGroupwareVersion'] [0]]})]})
					]}))
			if ox_context_info.has_key("oxGuiVersion"):
				rows.append(tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('GUI Version:')]})]}),
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ ox_context_info['oxGuiVersion'][0] ]})]})
					]}))
			if ox_context_info.has_key("oxIntegrationVersion"):
				rows.append(tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Integration Version:')]})]}),
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ ox_context_info['oxIntegrationVersion'][0] ]})]})
					]}))

			rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		## Licence
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
			header(_("Licence"),{"type":"4"},{})
			]})
			]}))
		module=univention.admin.modules.get('settings/license')
		objects=module.lookup(None, self.lo, '')

		if objects:
			object=objects[0]
			object.open()
 			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['base'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['base']]})]})
 				]}))

			if object['base'] == 'Free for personal use edition':
				self.save.put("personal_use","1")

 			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['accounts'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['accounts']]})]})
 				]}))

			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['groupwareaccounts'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['groupwareaccounts']]})]})
 				]}))

			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['clients'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['clients']]})]})
 				]}))

			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['desktops'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['desktops']]})]})
 				]}))

			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['expires'].short_description]})]}),
 				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object['expires']]})]})
 				]}))

			productTypes = ""
			for t in object['productTypes']:
				productTypes += ", " + t

 			rows.append(tablerow("",{},{"obs":[
  				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[object.descriptions['productTypes'].short_description]})]}),
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[productTypes[2:]]})]})
  				]}))

			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, "check for personal use: %s" % self.save.get( 'personal_use' ))
			if self.save.get( 'personal_use' ) == '1':
				rows.append(tablerow("",{},{"obs":[
					tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[_('License')]})]}),
					tablecol("",{'type':'about_layout'},{"obs":[htmltext('',{},{'htmltext':[u'Die "Free For Personal Use" Ausgabe von Univention Corporate Server ist eine spezielle Softwarelizenz mit der Verbraucher im Sinne des § 13 BGB die kostenlose Nutzung von Univention Corporate Server und darauf basierenden Softwareprodukten für private Zwecke ermöglicht wird. <br><br>\
							Im Rahmen dieser Lizenz darf UCS von unseren Servern heruntergeladen, installiert und genutzt werden. Es ist jedoch nicht erlaubt, die Software Dritten zum Download oder zur Nutzung zur Verfügung zu stellen oder sie im Rahmen einer überwiegend beruflichen oder gewerbsmäßigen Nutzung zu verwenden.  <br><br>\
							Die Überlassung der "Free For Personal Use"-Ausgabe von UCS erfolgt im Rahmen eines Schenkungsvertrages. Wir schließen deswegen alle Gewährleistungs- und Haftungsansprüche aus, es sei denn, es liegt ein Fall des Vorsatzes oder der groben Fahrlässigkeit vor. Wir weisen darauf hin, dass bei der "Free For Personal Use"-Ausgabe die Haftungs-, Gewährleistungs-, Support- und Pflegeansprüche, die sich aus unseren kommerziellen Softwareverträgen ergeben, nicht gelten.  <br><br>\
							Wir wünschen Ihnen viel Freude bei der Nutzung der "Free For Personal Use" Ausgabe von Univention Corporate Server und freuen uns über Ihr Feedback. Bei Fragen wenden Sie sich bitte an unser Forum, dass Sie im Internet unter <a target=parent href=http://forum.univention.de/>http://forum.univention.de/</a> erreichen.']})]})
					]}))
 		else:
 			rows.append(tablerow("",{},{"obs":[
 				tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[text('',{},{'text':[_('no licence found')]})]})
 				]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
			]}))

                ##Upload License from Keyfile
                self.certBrowse = question_file('', {} , {"helptext":_("Select a file")})
                self.certLoadBtn = button(_("Update License"),{'icon':'/style/ok.gif'},{"helptext":_("Upload selected file")})
                rows.append(tablerow("",{},{"obs":[
                                        tablecol("",{'type':'about_layout'},{"obs":[
                                                header(_("Update License via File"),{"type":"4"},{})
                                        ]}),
                                        tablecol("",{'colspan':'2','type':'about_layout'},{"obs":[
                                                self.certBrowse,
                                                htmltext('',{},{'htmltext':['<br>']}),
                                                self.certLoadBtn
                                        ]})
                        ]}))
		
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
			]}))

		#Upload License as Text-Copy from License-Mail
                self.certText =  question_ltext('', {}, {'helptext': _("Copy the License Code into this field")}) 
                self.certLoadTextBtn = button(_("Update License"),{'icon':'/style/ok.gif'},{"helptext":_("Upload the License")})
                rows.append(tablerow("",{},{"obs":[
                                        tablecol("",{'type':'about_layout'},{"obs":[
                                                header(_("Update License via Mail"),{"type":"4"},{})
                                        ]}),
                                        tablecol("",{'colspan':'2','type':'about_layout'},{"obs":[
                                                self.certText,
                                                htmltext('',{},{'htmltext':['<br>']}),
                                                self.certLoadTextBtn
                                        ]})
                        ]}))

		## Contact
		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[
			header(_("Contact"),{"type":"4"},{})
			]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':['Univention GmbH']})]}),
			tablecol("",{'type':'about_layout'},{"obs":[htmltext('',{},{'htmltext':[
			'<a href=http://www.univention.de target=parent>www.univention.de</a>'
			]})]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[_('ALL RIGHTS RESERVED')]})]}),
			tablecol("",{'type':'about_layout'},{"obs":[htmltext('',{},{'htmltext':[
			'<a href="mailto:info@univention.de">info@univention.de</a>'
			]})]})
			]}))

		rows.append(tablerow("",{},{"obs":[
			tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
			]}))

		self.subobjs.append(table("",{'type':'content_main'},{"obs":rows}))

	def apply(self):
		bla = "dd"
                # license import
                if (hasattr(self,'certLoadBtn') and self.certLoadBtn.pressed()) or (hasattr(self,'certLoadTextBtn') and self.certLoadTextBtn.pressed()):
                        if self.certBrowse.get_input() or (self.certText.get_input() and self.certText.get_input() != ""):
                                import subprocess, tempfile

				if self.certBrowse.get_input():
	                                #read content from license file
					certFile = open(self.certBrowse.get_input())
				else:
					#remove everythingt which is not part of the lizense
					mail_text = self.certText.get_input()

					license_text = []
					#extrakt license from mail
					add = False
					found = False
					for line in mail_text.split("\n"):
						line = line.lstrip(" ")
						if line.startswith("dn: cn=admin,cn=license"):
							add = True

						if add:
							license_text.append(line)

						if line.startswith("univentionLicenseSignature:"):
							found = True
							break
					mail_text = ""
					if found:
						for line in license_text:
							mail_text = "%s%s\n" % (mail_text, line)

					#create license file from mail
					if mail_text != "":
						certFileTemp = tempfile.mkstemp()
						certFile = file("%s" % certFileTemp[1], "w")
						certFile.write("%s" % mail_text)
						certFile.close()
						
						certFile = file("%s" % certFileTemp[1], "r")
					else:
						certFile = None

				if certFile != None:
	                                #read license from file
        	                        ldif_parser = ldifParser(certFile)

                	                #check license
                        	        position = self.save.get('ldap_position')
	                                base = position.getDomain()
        	                        res = ldif_parser.check(base)

	                                #close
        	                        certFile.close()
					os.remove(certFile.name)
				else:
					res = _("The License you have entered is invalid.")
	
                                #return result
                                if res != "":
                                        self.usermessage(_("An Error has occured:<br> %s" % res))
                                else:
                                        #install license
                                        settings = self.save.get("settings")
                                        pwd = self.save.get("pass")

                                        ldap_con = ldap.open("localhost")
                                        ldap_con.simple_bind_s(settings.userdn, pwd)
                                        ldap_con.modify_s(ldif_parser.dn,ldif_parser.mod_list)
                                        ldap_con.unbind_s()

                                        self.usermessage(_("The License has been sucessfully installed. You have to relogin."))
                                        self.save.put("LOGOUT",1)
                                        self.save.put("logout",1)
                                        self.save.put("uc_module","relogin")
                                        self.save.put("uc_submodule","none")
                                return

		self.applyhandlemessages()

