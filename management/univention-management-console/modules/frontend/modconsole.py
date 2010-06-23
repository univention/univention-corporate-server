# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: control part
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

import locale, os, sys, time, string

import unimodule

#import univention.admin.uldap
#import univention.admin.modules

import univention.management.console.protocol as umcp
import univention.management.console.tools as umc_tools
import univention.management.console as umc

from uniparts import *

# UMCP client comm
import client
# main widget for UMC (based on notebook)
import widget
import pages

import pages

import v

import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry ()
configRegistry.load()

LANG_DE = 'de_DE.utf8'
#LANG_EN = 'en_EN.utf8'
LANG_EN = 'C'
#LANG_DEFAULT = configRegistry.get ('directory/manager/web/language', locale.getdefaultlocale ())
LANG_DEFAULT = configRegistry.get ('umc/web/language', LANG_EN)

_ = umc.Translation( 'univention.management.console.frontend' ).translate

notebook_widget = None
init_umccmd = None

def create(a,b,c):
	return modconsole( a, b, c )

## def myinfo(settings):
##	if settings.listAdminModule('modconsole'):
##		return unimodule.realmodule("console", _("Console2"), _("Univention Console2"))
##	else:
##		return unimodule.realmodule("console", "", "")

def myrgroup():
	return ""

def mywgroup():
	return ""

def mymenunum():
	return 600

def mymenuicon():
	return '/icon/console.gif'

class modconsole(unimodule.unimodule):
	def __init__( self, a, b, c ):
		unimodule.unimodule.__init__( self, a, b, c )

	def __commonHeader(self, close_header=False):
		obs = []
		if configRegistry.has_key('umc/title') and configRegistry['umc/title']:
			self.save.put( 'site_title' , '%s' % configRegistry['umc/title'] )
		else:
			self.save.put( 'site_title' , 'Univention Management Console' )

		close_header_tag = ''
		if close_header:
			close_header_tag='</div>'

		if configRegistry.has_key('umc/title/image') and configRegistry['umc/title/image']:
			header = htmltext ('', {}, \
				{'htmltext': ["""
							<div id="header" style="background:transparent url(%(image)s) no-repeat scroll left top">
							%(close_header)s
						""" % {'image': configRegistry['umc/title/image'], 'close_header':close_header_tag}]})
		else:
			header = htmltext ('', {}, \
				{'htmltext': ["""
							<div id="header">
								<!-- @start header-title -->
								<h1 class="header-title">
									<span class="hide">univention</span> <a href="/univention-management-console/" title="Start">management console</a>
								</h1>
								<!-- @end header-title -->
							%(close_header)s
						""" % {'close_header':close_header_tag}]})
		self.subobjs.append(header)

	def __quickmenu(self):
		lang = locale.getlocale( locale.LC_MESSAGES )
		if lang and lang[0]:
			lang = lang[0].split('_',1)[0]
		else:
			lang = 'en'
		usermenu = htmltext ('', {}, \
			{'htmltext': ["""
				<div id="user-menu">
				<!-- @start info -->
				<div id="info">
					<ul>
						<li class="help">
								<a title="%(help)s" href="/help.php?lang=%(lang)s&app=umc" target="_blank" onclick="helpwindow=window.open('/help.php?lang=%(lang)s&app=umc','pophelp','toolbar=no,location=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=no,width=530,height=450,top=150,left=100');helpwindow.focus();return false;">%(help)s</a>
						</li>
						<li class="spacer"> </li>
						<li class="about">
				""" % {'help': _('Help'), 'lang': lang} ]})
		self.subobjs.append(usermenu)
		self.aboutbutton=button(_('About UMC'),{'link':'1'},{"helptext":_('About UMC')})
		self.subobjs.append(self.aboutbutton)
		usermenu = htmltext ('', {}, \
			{'htmltext': ["""
						</li>
					</ul>
					
					<br class="clear"/>
				"""]})
		self.subobjs.append(usermenu)
					
		usermenu = htmltext ('', {}, \
			{'htmltext': ["""
					<span class="session">
						%(loginmessage)s <span class="name">%(username)s</span>
					</span>
				</div>
				<!-- @end info -->
				""" % { 'loginmessage': _('You are logged in as'), 'username': self.save.get("relogin_username")}
				]})
		self.subobjs.append(usermenu)
				
		usermenu = htmltext ('', {}, \
			{'htmltext': ["""
					<!-- @start account options -->
					<ul class="options">
						<li class="logout">
				"""]})
		self.subobjs.append(usermenu)
		self.logoutbutton=button(_('Logout'),{'icon':'/icon/exit.png'},{"helptext":_('Logout')})
		self.subobjs.append(self.logoutbutton)
		#self.mbutlist.append([logout_button, 'logout', None])
		usermenu = htmltext ('', {}, \
			{'htmltext': ["""
					</li>
				</ul>
				<br class="clear"/>
				<!-- @end account-options -->
			</div>
        </div>
				"""]})
		self.subobjs.append(usermenu)

	def __login(self): # build login-Screen
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: __login: log on to UMCP server')

		self.__commonHeader(True)

		login_message = htmltext ('', {}, \
				{'htmltext': ["""
					<div id=content-wrapper>
					<div id=content-head>
					<h2>%(login)s</h2>
					</div>
					""" % {'login': _('Univention Management Console Login')}]})
		self.subobjs.append(login_message)

		sessioninvalid = None
		if self.req and self.req.meta and self.req.meta.has_key ('Sessioninvalid') \
				and self.req.meta['Sessioninvalid'] == '1':
					description_caption = _('Session Timeout')
					description1 = _('To increase the session timeout log into Univention Management Console, select the Univention Configuration Registry module and change the value of <code>umc/web/timeout</code>.')
					#description2 = _('As an alternative you can set the UCR variable with the following command line statement <code>univention-config-registry directory/manager/timeout=TIMEOUT_IN_SECONDS</code>.')
					sessioninvalid = htmltext ('', {}, \
							{'htmltext': ["""
								<div class=error message>
								<h3>%s</h3>
								<p>%s</p>
								</div>
								""" % (description_caption, description1)]})

		unsupportedbrowser = None
		if self.req and self.req.meta and self.req.meta.has_key ('Unsupportedbrowser') \
				and self.req.meta['Unsupportedbrowser'] == '1':
					description_caption = _('Unsupported web browser')
					description1 = _('The Univention Management Console (UMC) has not been tested with your web browser. You should use Firefox since version 3.x or Microsoft Internet Explorer since version 6.0.')
					unsupportedbrowser = htmltext ('', {}, \
							{'htmltext': ["""
								<div class=error message>
								<h3>%s</h3>
								<p>%s</p>
								</div>
								""" % (description_caption, description1)]})

		unsecureconnection = None
		if int(os.environ["HTTPS"]) != 1:
			description_caption = _('Insecure Connection')
			description1 = _('This network connection is not encrypted. All personal or sensitive data will be transmitted in plain text. Please follow <a href=https://%s/univention-management-console/ >this link</a> to use a secure SSL connection.') % os.environ['HTTP_HOST']
			unsecureconnection = htmltext ('', {}, \
							{'htmltext': ["""
								<div class=error message>
								<h3>%s</h3>
								<p>%s</p>
								</div>
								""" % (description_caption, description1)]})
		# select language
		# the installed languages can be obtained via locale -a
		# but I shouldn't check on that but rely on the languages I set
		# up for this tool
		langs = [
				{"level": '0', "name": 'de', "description": "Deutsch"},
				{"level": '0', "name": 'en', "description": "English"}
				]
		default_lang = None
		if LANG_DEFAULT:
			if LANG_DEFAULT == 'C':
				default_lang = 'en'
			elif LANG_DEFAULT:
				default_lang = LANG_DEFAULT.split ('_')[0]

		if default_lang:
			for l in langs:
				if l['name'] == default_lang:
					l['selected'] = default_lang
					break

		self.chooselang=language_dojo_select(_("Language:"),{'width':'265'},{"helptext":_("Select language for this session"),"choicelist":langs})

		self.usernamein=question_text(_("User name"),{'width':'265','puretext': '1'},{"usertext":self.save.get("relogin_username"),"helptext":_("Please enter your uid.")})
		self.cabut=button(_("Cancel"),{'class':'cancel', 'link': '/'},{"helptext":_("Abort login")})
		self.passwdin=question_secure(_("Password"),{'width':'265','puretext': '1'},{"usertext":self.save.get("relogin_passwd"),"helptext":_("Please enter your password.")})
		self.okbut=button(_("Login"),{'class':'submit', 'defaultbutton':'1'},{"helptext":_("Login")})

		if unsecureconnection:
			self.subobjs.append(unsecureconnection)

		if sessioninvalid:
			self.subobjs.append(sessioninvalid);

		if unsupportedbrowser:
			self.subobjs.append(unsupportedbrowser);

		login_message = htmltext ('', {}, \
				{'htmltext': ["""
					<div id=content>
					<div class=form-wrapper>
					"""]})
		self.subobjs.append(login_message);

		self.div_start('form-item', divtype='class')
		self.subobjs.append(self.usernamein);
		self.div_stop('form-item')
		self.div_start('form-item', divtype='class')
		self.subobjs.append(self.passwdin);
		self.div_stop('form-item')
		self.div_start('form-item', divtype='class')
		self.subobjs.append(self.chooselang)
		self.div_stop('form-item')
		self.subobjs.append(htmltext ('', {}, {'htmltext': ['<div class="form-item">']}))
		self.subobjs.append(self.cabut)
		self.subobjs.append(self.okbut)
		self.subobjs.append(htmltext('', {}, {'htmltext': ['<br class="clear"/> </div>']}))

		# close content div
		login_message = htmltext ('', {}, \
				{'htmltext': ["""
					</div>
					</div>
					"""]})
		self.subobjs.append(login_message);

		# close content-wrapper div
		login_message = htmltext ('', {}, \
				{'htmltext': ["""
					</div>
					"""]})
		self.subobjs.append(login_message);


		#self.subobjs.append(table("",
		#	{'type':'content_main_menuless'},
		#	{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":rows})]})]})]}
		#	))


	def __logout(self): # ask for logout and jump to login or back to process
		self.__commonHeader( )
		self.__quickmenu( )

		self.div_start('content-wrapper', divtype='id')
		self.okbut=button(_("Logout"),{'class':'submit', 'link': '/univention-management-console/index.php?relogin=1', 'defaultbutton': '1'},{"helptext":_("Logout")})
		self.cabut=button(_("Cancel"),{'class':'cancel'},{"helptext":_("Abort logout")})

		rows = []

		logouttext = text('',{},{'text':[_("Do you really want to logout?")]})
		rows.append(tablerow("",{},{"obs":[tablecol("",{"colspan":"2",'type':'login_layout'},{"obs":[ logouttext ]})]}))

		okcol=tablecol("",{'type':'login_layout_button'},{"obs":[self.okbut]})
		cacol=tablecol("",{'type':'login_layout_button'},{"obs":[self.cabut]})
		rows.append(tablerow("",{},{"obs":[cacol,okcol]}))

		self.nbook=notebook('', {}, {'buttons': [(_('Logout'), _('Logout'))], 'selected': 0})
		self.subobjs.append(self.nbook)
		self.div_start('content', divtype='id')
		self.div_start('logout_message', divtype='id')

		self.subobjs.append(table("",
			{'type':'content_main_menuless'},
			{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":rows})]})]})]}
			))
		self.div_stop('logout_message')
		self.div_stop('content')
		self.div_stop('content-wrapper')

	def __about(self): # ask for logout and jump to login or back to process
		self.__commonHeader( )
		self.__quickmenu( )

		rows = []

		build_version = v.build

		self.div_start('content-wrapper', divtype='id')

		if configRegistry.has_key("version/releasename"):
			build_version = build_version + "(" + configRegistry["version/releasename"] + ")"

		self.div_start('content-head', divtype='id')
		self.subobjs.append(htmltext ('', {}, {'htmltext': ['<h2>%s</h2>' % _('About Univention Management Console')]}))
		self.div_stop('content-head')

		self.div_start('content', divtype='id')

		rows.append(tablerow("",{},{"obs":[
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Version')]})]}),
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[v.version]})]})
				]}))

		rows.append(tablerow("",{},{"obs":[
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Build')]})]}),
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[build_version]})]})
				]}))

		## UCS
		rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		rows.append(tablerow("",{},{"obs":[
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Hostname')]})]}),
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[configRegistry['hostname']]})]})
				]}))

		version_string = ""
		for key in ['version/version','version/patchlevel','version/security-patchlevel']:
			if configRegistry.has_key(key) and configRegistry[key]:
				if version_string:
					version_string = "%s-%s" % (version_string,configRegistry[key])
				else:
					version_string = configRegistry[key]

		rows.append(tablerow("",{},{"obs":[
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':[ _('Local installation')]})]}),
				tablecol("",{'type':'about_layout'},{"obs":[text('',{},{'text':["%s %s" % (_('UCS version'), version_string)]})]})
				]}))

		rows.append(tablerow("",{},{"obs":[
				tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
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

		self.subobjs.append(table("",
			{'type':'content_main_menuless'},
			{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[table("",{},{"obs":rows})]})]})]}
			))

		self.okbut=button(_("Ok"),{'class':'submit', 'defaultbutton': '1'},{"helptext":_("Logout")})

		self.subobjs.append(self.okbut)
		self.div_stop('content')
		self.div_stop('content-wrapper')

	def __process(self):
		global notebook_widget
		layout = notebook_widget.layout()
		report = notebook_widget.report()

		if report:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, '__process: report: %s' % report )
			self.userinfo( report )
		self.subobjs.extend( layout )

		if notebook_widget.refresh():
			self.atts['refresh']='1000'

			# This "link button" is needed in order for the refresh to
			# work properly.
			hack_button = button( '', { 'link' : '1' }, { 'helptext' : _( 'Update status' ) } )
			self.subobjs.append( hack_button )

	def __div_start(self, div):
		div_header = htmltext ('', {}, \
			{'htmltext': ["""
				<div id="%(div)s">
				""" % {'div': div }]})
		self.subobjs.append(div_header)

	def __div_stop(self, div=None):
		div_header = htmltext ('', {}, \
			{'htmltext': ["""
				</div>
				""" ]})
		self.subobjs.append(div_header)


	def mytype(self):
		return "dialog"

	def myinit(self):
		global init_umccmd
		self.save = self.parent.save

		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit')

		self.lo = self.args[ "uaccess" ] # will be None in console as we don't connect the ldap directly (so far...)

		if self.inithandlemessages():
			return

		if self.req and self.req.meta:
			if not init_umccmd:
				init_umccmd = self.req.meta.get('init_umccmd')
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modconsole.myinit(): set init_umccmd=%s' % repr(init_umccmd))

		if self.save.get('logout'): # quit connection and fall back to login...
			self.save.put('consolemode','logout')
			self.__logout()
			return

		if self.save.get('about'): # quit connection and fall back to login...
			self.save.put('consolemode','about')
			self.__about()
			return

		if not self.save.get( 'auth_ok' , False ) == True: # do authentication and login
			# connect to daemon
			univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: connection to UMCP server')
			if not self.save.get( 'umc_connected', False ):
				univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: trying ...')
				if not client.connect( timeout = 10 ):
					univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: myinit: FAILED')

			if client.error_get() != client.NOERROR:
				self.save.put( 'consolemode', None )
				self.save.put( 'auth_ok', False )
				self.usermessage( _('Authentication failed: A connection to the UMC daemon could not be established.' ), application='umc', need_header=True, relogin=True )
				univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'UMCP client error: no connection')
			else:
				self.save.put('consolemode','login')
				self.save.put( 'umc_connected', True )
				self.__login()
		else:								 # process the umcp-response
			if client.error_get() != client.NOERROR:
				self.save.put( 'consolemode', None )
				self.save.put( 'auth_ok', False )
				self.save.put( 'umc_connected', False )
				return
			self.__commonHeader()
			self.__quickmenu()
			self.save.put('consolemode','process')
			global notebook_widget
			if not notebook_widget:
				notebook_widget = widget.Notebook( self.save )

				req = umcp.Request( 'GET', args = [ 'modules/list' ] )
				id = client.request_send( req )
				response = client.response_wait( id, timeout = 10 )
				if response:
					all_modules = response.body[ 'modules' ]
					# all_modules = { 'MODULENAME' : {
					#								   'short_description': 'ding',
					#								   'commands': {
					#												 'ding/dong/confirm': {
					#																			 'short_description': 'my foo bar',
					#																			 'caching': False,
					#																			 'startup': False,
					#																			 'long_description': '',
					#																			 'priority': 0,
					#																		   },
					#												  ....
					#												},
					#								   'long_description': 'FOOOBAR',
					#								   'categories': ['system', 'all'],
					#								   'icon': 'ding/main',
					#								  },
					#				   'NEXTMODULE': { .... },
					#				  }
					if init_umccmd:
						modulename = None
						for modname in all_modules:
							if init_umccmd in all_modules[modname].get('commands',{}).keys():
								modulename = modname
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modconsole.myinit(): init_umccmd: module=%s' % modulename)
						if modulename:
							if notebook_widget.existsPage( modulename ):
								notebook_widget.selectPage( modulename )
							else:
								mod = pages.Module( modulename, all_modules[ modulename ], init_cmd = init_umccmd )
								notebook_widget.appendPage( mod )
								univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modconsole.myinit(): init_umccmd: created module %s' % modulename)

			self.__process()

	def apply(self):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'Function: apply')
		self.applyhandlemessages()

		if hasattr(self,'logoutbutton') and self.logoutbutton.pressed():
			self.save.put('logout','1')
			return

		if hasattr(self,'aboutbutton') and self.aboutbutton.pressed():
			self.save.put('about','1')
			return

		pre_session_login = bool(self.req) and bool(self.req.meta) and bool(self.req.meta.get('pre_session_username')) and bool(self.req.meta.get('pre_session_password'))
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'modconsole: apply: pre_session_login = %s' % pre_session_login )
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modconsole: apply: pre_session_username=%s" % self.req.meta.get('pre_session_username'))
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, "modconsole: apply: pre_session_language=%s" % self.req.meta.get('pre_session_language'))

		if self.save.get('consolemode') == 'login':
			if pre_session_login:
				self.save.put("relogin_username",self.req.meta.get('pre_session_username'))
				self.save.put("relogin_password",self.req.meta.get('pre_session_password'))
			else:
				self.save.put("relogin_username",self.usernamein.xvars.get("usertext",""))
				self.save.put("relogin_password",self.passwdin.xvars.get("usertext",""))

			if self.cabut.pressed():
				self.save.put( 'auth_ok', False ) # just to be sure

			if self.okbut.pressed() or pre_session_login:
				authUsername = self.save.get("relogin_username",'')
				authPassword = self.save.get("relogin_password",'')

				#if not authUsername or not authPassword:
				#	return
				req = umcp.Request( 'AUTH' )
				req.body[ 'username' ] = authUsername
				req.body[ 'password' ] = authPassword

				id = client.request_send( req )
				response = client.response_wait( id, timeout = 10 )
				if response:
					(authenticated, status, statusinformation) = \
						( response.status() == 200, response.status(),
						  umcp.status_information( response.status() ) )
				else:
					authenticated = False
					statusinformation = _( 'The UMC server did not responed to the authentication request' )
				if authenticated:
					self.save.put( 'auth_ok', True )

					# create authenticated ldap connection
					ldapc = umc.LdapConnection()
					if ldapc:
						res = ldapc.searchDn( filter = 'uid=%s' % authUsername )
						# use only first object found
						if res and res[0]:
							ldapc.connect( binddn = res[0], bindpw = authPassword )

					# set locale after authentication
					language = None
					if hasattr(self, 'chooselang'):
						language = self.chooselang.getselected()
					if self.req.meta.get('pre_session_language'):
						language = self.req.meta.get('pre_session_language')

					if language:
						if language == 'de':
							language = LANG_DE
						elif language == 'en':
							language = LANG_EN
						else:
							language = LANG_DEFAULT
						# WARNING this code could cause an exception maybe it needs to be surrounded by parenthesis
						os.environ["LC_MESSAGES"] = language
						locale.setlocale( locale.LC_MESSAGES, language )

						req = umcp.Request( 'SET', args = ('locale', language ) )
						id = client.request_send( req )
						response = client.response_wait( id, timeout = 10 )
						if response:
							(status, statusinformation) = \
									 ( response.status(), umcp.status_information( response.status() ) )
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
												   'modconsole.py: locale set (%s): status: %s (%s)' % (language, status, statusinformation))
						else:
							univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
												   'modconsole.py: setting locale timed out')

					# pass sessionid to UMC server after successful authentication
					req = umcp.Request( 'SET', args = ('sessionid', client._sessionId ) )
					id = client.request_send( req )
					response = client.response_wait( id, timeout = 10 )
					if response:
						(status, statusinformation) = ( response.status(), umcp.status_information( response.status() ) )
						univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO,
											   'modconsole.py: sessionid set (%s): status: %s (%s)' % (client._sessionId, status, statusinformation))
					else:
						univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'modconsole.py: setting sessionid timed out')
				else:
					self.save.put( 'consolemode', None )
					self.save.put( 'auth_ok', False )
					self.usermessage( _('Authentication failed: %s') % statusinformation, application='umc', need_header=True, relogin=True )

		elif self.save.get('consolemode') == 'logout':
			if self.cabut.pressed():
				self.save.put( 'consolemode', 'process' )
				self.save.put( 'logout', None )
			if self.okbut.pressed():
				client.disconnect()
				ldapc = umc.LdapConnection()
				if ldapc:
					ldapc.disconnect()
				self.save.put( 'consolemode', 'login' )
				self.save.put( 'logout', None )
				self.save.put( 'umc_connected', False )
				self.save.put( 'auth_ok', False )
				self.userinfo( _( 'Logout successful.' ) )
		elif self.save.get('consolemode') == 'about':
			if self.okbut.pressed():
				self.save.put( 'consolemode', 'process' )
				self.save.put( 'about', None )

		elif self.save.get('consolemode') == 'process':
			global notebook_widget
			notebook_widget.apply()
			report = notebook_widget.report()
			if report:
				self.userinfo( report )

		elif self.save.get('consolemode'):
			raise "unknown consolemode"
		else:
			pass # no consolemode set, maybe a failed login
