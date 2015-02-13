#!/usr/bin/python2.7
#
# Univention Management Console
#  Module lib containing low-lewel commands to control the UMC server
#
# Copyright 2012-2014 Univention GmbH
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

from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.protocol.definitions import MODULE_ERR

from univention.lib.i18n import Translation

import subprocess
import locale
import json
import hashlib
import urllib2
import socket
import cookielib
import traceback
import univention.lib.urllib2_ssl
import univention.config_registry

_ = Translation( 'univention-management-console-module-lib' ).translate

CMD_ENABLE_EXEC = ['/usr/share/univention-updater/enable-apache2-umc', '--no-restart']
CMD_ENABLE_EXEC_WITH_RESTART = '/usr/share/univention-updater/enable-apache2-umc'
CMD_DISABLE_EXEC = '/usr/share/univention-updater/disable-apache2-umc'

def convertExceptionToString(ex):
	"""
	Exceptions like urllib2.URLError may contain a string or another exception as arguments.
	Try to create a user readable string of it.
	"""
	if hasattr(ex, 'args') and ex.args and isinstance(ex.args[0], socket.error):
		return str(ex.args[0][1])
	return str(ex)

class MessageSanitizer(StringSanitizer):
	def _sanitize(self, value, name, further_args):
		value = super(MessageSanitizer, self)._sanitize(value, name, further_args)
		if isinstance(value, unicode):
			# unicodestr -> bytestr (for use in command strings)
			for encoding in (locale.getpreferredencoding, 'UTF-8', 'ISO8859-1'):
				try:
					value = value.encode(encoding)
					break
				except UnicodeEncodeError:
					pass
		return value

class Server(object):

	def restart_isNeeded(self, request):
		"""TODO: It would be helpful to monitor the init.d scripts in order to
		         determine which service exactly should be reloaded/restartet.
		"""
		self.finished(request.id, True)

	def restart(self, request):
		"""Restart apache, UMC Web server, and UMC server.
		"""
		# send a response immediately as it won't be sent after the server restarts
		self.finished(request.id, True)

		# enable server restart and trigger restart
		# (disable first to make sure the services are restarted)
		subprocess.call(CMD_DISABLE_EXEC)
		p = subprocess.Popen(CMD_ENABLE_EXEC_WITH_RESTART, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out, err = p.communicate()
		MODULE.info('enabling server restart:\n%s' % out)

	@simple_response
	def ping(self):
		return dict(success=True)

	@sanitize(message=MessageSanitizer(default=''))
	def reboot(self, request):
		message = _('The system will now be restarted')
		if request.options['message']:
			message = '%s (%s)' % (message, request.options['message'])

		if self._shutdown(message, reboot=True) != 0:
			message = _('System could not reboot')
			request.status = MODULE_ERR

		self.finished(request.id, None, message)

	@sanitize(message=MessageSanitizer(default=''))
	def shutdown(self, request):
		message = _('The system will now be shut down')
		if request.options['message']:
			message = '%s (%s)' % (message, request.options['message'])

		if self._shutdown(message, reboot=False) != 0:
			message = _('System could not shutdown')
			request.status = MODULE_ERR

		self.finished(request.id, None, message)

	def _shutdown(self, message, reboot=False):
		action = '-r' if reboot else '-h'

		try:
			subprocess.call(('/usr/bin/logger', '-f', '/var/log/syslog', '-t', 'UMC', message))
		except (OSError, Exception):
			pass
		return subprocess.call(('/sbin/shutdown', action, 'now', message))

	def sso_getsession( self, request ):
		""" Create new UMC session on remote host and return session information
		    umc-command -s master.example.com -U Administrator -P univention lib/singlesignon/getsession -o host=slave.example.com
		"""
		result = False

		MODULE.process('Creating new session on remote host %s for user %s' % (request.options.get('host'), self._username))

		host = request.options.get('host','')
		if not host.lower().strip():
			MODULE.error('sso_getsession: no hostname given')
			self.finished( request.id, result, success=False, message=_('option "host" has not been specified'), status=400)
			return

		# this is a very simple and stupid check:
		# remove all valid characters and check if string is empty ==> valid hostname/FQDN
		if host.lower().strip('abcdefghijklmnopqrstuvwxyz0123456789-._'):
			MODULE.error('sso_getsession: given hostname seem to contain invalid characters')
			self.finished( request.id, result, success=False, message=_('given hostname seems to contain invalid characters'), status=400)
			return

		if not self._username or not self._password:
			MODULE.error('sso_getsession: cannot read credentials')
			self.finished( request.id, result, success=False, message=_('no credentials available'), status=400)
			return

		url = 'https://%s/umcp/auth' % host
		body = json.dumps({'options': {'username': self._username, 'password': self._password}})

		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

		MODULE.process('Preparing request...')

		# create urllib2 opener object
		opener = urllib2.build_opener(
			univention.lib.urllib2_ssl.VerifiedHTTPSHandler(
				key_file='/etc/univention/ssl/%s/private.key' % ucr.get('hostname'),
				cert_file='/etc/univention/ssl/%s/cert.pem' % ucr.get('hostname'),
				ca_certs_file='/etc/univention/ssl/ucsCA/CAcert.pem',
				check_hostname=(host != 'localhost'),
				))

		cookie_jar = cookielib.CookieJar()
		opener.add_handler(urllib2.HTTPCookieProcessor(cookie_jar))
		MODULE.process('Sending request...')
		try:
			response = opener.open(urllib2.Request(url, body, {'Content-Type': 'application/json', 'User-Agent': 'UMC 2'}))
			MODULE.process('Got response ...')
		except (urllib2.HTTPError, urllib2.URLError), ex:
			MODULE.error('sso_getsession: unable to connect to %r: %r' % (host, ex))
			self.finished( request.id, result, success=False, message=_('unable to connect to %r: %s') % (host, convertExceptionToString(ex),), status=500)
			return
		except univention.lib.urllib2_ssl.CertificateError, ex:
			MODULE.error('sso_getsession: certificate error when connecting to %r: %s' % (host, ex))
			self.finished( request.id, result, success=False, message=_('certificate error when connecting to %r: %s') % (host, ex), status=500)
			return
		except Exception, ex:
			MODULE.error('sso_getsession: unknown exception while connecting to %r: %s\n%s' % (host, ex, traceback.format_exc()))
			self.finished( request.id, result, success=False, message=_('unable to connect to %r: %s') % (host, ex), status=500)
			return

		login_token = None
		for cookie in cookie_jar:
			MODULE.info('sso_getsession: found cookie in response: name=%r  value=%r' % (cookie.name, cookie.value))
			if cookie.name == 'UMCSessionId':
				login_token = hashlib.sha256(cookie.value).hexdigest()

		if not login_token:
			self.finished( request.id, result, success=False, message=_('failed to get login token for host %r') % (host,), status=500)
			return

		self.finished( request.id, { 'loginToken': login_token })

