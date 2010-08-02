# -*- coding: utf-8 -*-
#
# Univention Directory Manager
#  the admin redirect logic
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

from uniparts import *
import os
import sys
import time
import ldap
import string
import re
import unimodule
import unisignon
import univention.debug
import univention.config_registry
from local import _

def create(a,b,c):
	return modredirect(a,b,c)
def myinfo(settings):
	return unimodule.realmodule("redirect", _("Redirect"), _("Redirect"))
def myrgroup():
	return ""
def mywgroup():
	return ""
def mymenunum():
	return 800
def mymenuicon():
	return unimodule.selectIconByName( 'exit' )

class modredirect(unimodule.unimodule):
	def mytype(self):
		return "dialog"

	def myinit(self):
		#from uniparts import *
		pass

	def myinit(self):
		self.authfail=None
		self.save=self.parent.save

		self.div_start('content-wrapper')
		#self.subobjs.append(table("",
		#		{'type':'content_header'},
		#		{"obs":[tablerow("",{},{"obs":[tablecol("",{},{"obs":[]})]})]})
		#	)
		self.nbook=notebook('', {}, {'buttons': [(_('Redirect'), _('Redirect'))], 'selected': 0})
		self.subobjs.append(self.nbook)
		self.div_start('content')

		# get current user, password and language
		username = self.save.get('user')
		password = self.save.get('pass')
		language = self.save.get('language')
		if not language:
			language = os.environ["LC_MESSAGES"][0:2]
			if not language or len(language) < 2:
				language = 'en'

		# get redirect target
		host = self.save.get('redirect_host')
		args = self.save.get('redirect_args')
		if not host:
			# use fallback
			host = self.save.get('uc_virtualmodule')
			args = self.save.get('uc_submodule')

		# determine protocol of current connection
		proto = 'http'
		if int(os.environ["HTTPS"]) == 1:
			proto = 'https'
		# use specified protocol or the same as in current connection
		proto = self.save.get('redirect_proto', proto)

		ud.debug(ud.ADMIN, ud.INFO, 'modredirect: creating SSO request object')
		sso = unisignon.SignOnRedirect( host, username, password, language=language, application='UMC', protocol=proto, arguments=args )
		ud.debug(ud.ADMIN, ud.INFO, 'modredirect: got SSO request object')
		targetURL = sso.getTargetURL()

		session_hostname = host
		if host == os.environ["HTTP_HOST"]:
			# if specified host is localhost then use FQDN as hostname - otherwise urllib will complain about certificate's wrong common name
			ucr = univention.config_registry.ConfigRegistry()
			ucr.load()
			session_hostname = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))

		try:
			ud.debug(ud.ADMIN, ud.ERROR, 'modredirect: sending SSO request')
			# always use HTTPS for creating a new session - use temporarily session_hostname as host
			sso.createSession(host=session_hostname, protocol='https')
			ud.debug(ud.ADMIN, ud.ERROR, 'modredirect: SSO request done - no error')
			msg = _('A new window with Univention Management Console will be opened in a few seconds. If this is not the case, please click %(starttag)shere%(endtag)s.')
		except Exception, e:
			msg = _('Creating a new session for Univention Management Console on host %(host)s failed. Please click %(starttag)shere%(endtag)s to log in manually.')

		msg = msg % {
				'host': host,
				'starttag': '<a href="%s" target="_blank">' % targetURL,
				'endtag': '</a>',
				}

		# session is valid ==> add javascript code for submitting "redirect" form and javascript code to get back to UDM startup page
		if sso.getSessionID():
			# set current module to "none"
			self.save.put('uc_module', 'none')
			# get javascript from signon object and merge it with own javascript, so user is pushed back to UDM startup page after creating UMC popup
			msg += sso.getOnLoadJavascriptTag()
			msg += '<script type="text/javascript">dojo.addOnLoad(function(){ setTimeout(function(){ document.forms["content"].submit(); }, 3000); });</script>'

		# build layout
		redirecttxt = htmltext('', {}, {'htmltext': ["""<p>%s</p>""" %  msg ] } )

		row1 = tablerow("",{},
						{"obs":[tablecol("",{"colspan":"2",'type':'note_layout_text'},
										 {"obs":[ redirecttxt ]})]
						 }
						)

		tab = table("",{},{"obs":[row1]})

		self.subobjs.append(table("",{'type':'logout'},
								  {"obs":[tablerow("",{},
												   {"obs":[tablecol("",{"colspan":"2"},
																	{"obs":[tab]})]
													})]
								   })
							)


		self.div_stop('content')
		self.div_stop('content-wrapper')

	def apply(self):
		pass

	def waitmessage(self):
		return _('Creating new session for Univention Management Console...')
