# -*- coding: utf-8 -*-
#
# Univention Webui
#  unisignon.py
#
# Copyright 2010 Univention GmbH
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

import traceback
import univention.debug as ud
import urllib
import urllib2
import re

class SignOnRedirect(object):
	VALID_APPLICATIONS = ('UMC', 'UDM')
	VALID_PROTOCOLS = ('http', 'https')

	def __init__(self, host, username, password, language='en', application='UMC', protocol='https', arguments=None):
		"""
		create sign on and redirect object
		Arguments:
  			host: hostname or ip address (host has to be identical to SSL certificate name! Otherwise an exception is raised)
			username: username to log on
			passwort: corresponding password for specified username
			language: language (de,en)
			application: 'UMC' or 'UDM'
			protocol: 'http' or 'https'
			arguments: array of additional arguments, e.g. arguments=['foo=bar', 'init_umccmd=update/overview']
 		"""
		self.host = host
		self.protocol = protocol
		self.username = username
		self.password = password
		self.language = language
		self.arguments = arguments
		self.application = application
		self.sessionid = None
		self.targetURL = None
		self.validateProtocol()
		self.validateApplication()
		self.validateLanguage()
		self.buildTargetURL()


	def getTargetURL(self):
		"""
			return targetURL
			e.g. https://qamaster.univention.qa/univention-management-console/index.php
		"""
		return self.targetURL


	def getSessionID(self):
		"""
		return retrieved session id (may be None on failure!)
		"""
		return self.sessionid


	def validateProtocol(self):
		if not self.protocol in self.VALID_PROTOCOLS:
			raise Exception('Invalid protocol: %s  (valid: %s' % (self.protocol, self.VALID_PROTOCOLS))


	def validateApplication(self):
		if not self.application in self.VALID_APPLICATIONS:
			raise Exception('Invalid application: %s  (valid: %s' % (self.application, self.VALID_APPLICATIONS))


	def validateLanguage(self):
		lang = self.language
		if not lang:
			raise Exception('Invalid language: %s' % self.language )

		if len(lang) > 2:
			lang = lang[0:2].lower()

		if not lang.isalpha() or len(lang) < 2:
			raise Exception('Invalid language: %s' % self.language )

		self.language = lang


	def changeProtocol(self, proto):
		"""
			change protocol (e.g. after getting session id via HTTPS switch to HTTP)
		"""
		self.protocol = proto
		self.validateProtocol()
		self.buildTargetURL()


	def buildTargetURL(self, host=None, protocol=None, arguments=None, application=None, save=True):
		"""
			create URL to specified application and pass additional arguments to application (like 'init_umccmd')
		"""
		if host == None:
			host = self.host
		if protocol == None:
			protocol = self.protocol
		if arguments == None:
			arguments = self.arguments
		if application == None:
			application = self.application

		args = ''
		if arguments:
			args = '?%s' % '&'.join( arguments )
		if application == 'UDM':
			targetURL = '%s://%s/univention-directory-manager/index.php%s' % (protocol, host, args)
		elif application == 'UMC':
			targetURL = '%s://%s/univention-management-console/index.php%s' % (protocol, host, args)
		else:
			raise Exception('Invalid application: %s  (valid: %s' % (application, self.VALID_APPLICATIONS))

		if save:
			self.targetURL = targetURL

		return targetURL


	def createSession(self, host=None, protocol=None, arguments=None):
		"""
			create new session and get sessionid from application (UDM/UMC)
		"""
		data = [ ('pre_session_username', self.username),
				 ('pre_session_password', self.password),
				 ('pre_session_language', self.language) ]

		# use temporary targetURL - if host or protocol is None then corresponding class attribute is used by buildTargetURL
		targetURL = self.buildTargetURL(host=host, protocol=protocol, save=False)

		try:
			ud.debug(ud.ADMIN, ud.INFO, 'unisignon: trying to get new session for %s on host %s' % (self.application, self.host))
			# send request and fetch data
			http_session = urllib2.urlopen( targetURL, urllib.urlencode(data) )
			page_content = http_session.read()

			# parse session id
			tmp_id = re.search('<input[^>]*?name="session_id"[^>]*?>', page_content).group(0)
			self.sessionid = re.search("""value=["'](._[a-f0-9]+)["']""", tmp_id).group(1)                # "

			# missing session id ==> raise Exception
			if not self.sessionid:
				raise Exception('Cannot get session id for application %s' % self.application)

			# session id is present but missing text 'You are logged in as' (text is shown on every page) ==> raise Exception
			if not 'You are logged in as' in page_content and not 'Sie sind angemeldet als' in page_content:
				self.sessionid = None
				raise Exception('Got invalid session id for application %s' % self.application)

			ud.debug(ud.ADMIN, ud.INFO, 'unisignon: got new session for %s on host %s: sessionid=%s' % (self.application, self.host, self.sessionid))
		except Exception, e:
			ud.debug(ud.ADMIN, ud.ERROR, 'unisignon: creating new session for %s on host %s failed: %s' % (self.application, self.host, str(e)))
			ud.debug(ud.ADMIN, ud.INFO,  'unisignon: traceback for failed session:\n%s' % (traceback.format_exc()))
			raise


	def getJavascript(self):
		"""
			get javascript for changing redirect form and submitting form
		"""
		actions = [ 'document.forms["redirectsignon"].session_id.value="%s";' % self.sessionid,
					'document.forms["redirectsignon"].action="%s";' % self.targetURL,
					'document.forms["redirectsignon"].submit();',
					]
		return ''.join(actions)


	def getOnLoadJavascript(self):
		"""
			get Dojo OnLoad javascript which causes a redirect directly after page has been loaded completely
		"""
		return 'dojo.addOnLoad(function(){%s});' % self.getJavascript()


	def getOnLoadJavascriptTag(self):
		"""
			get Dojo OnLoad javascript which causes a redirect directly after page has been loaded completely
			==> '<script type="text/javascript">' + getOnLoadJavascript() + '</script>'
		"""
		return '<script type="text/javascript">%s</script>' % self.getOnLoadJavascript()
