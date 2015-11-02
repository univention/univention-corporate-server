# -*- coding: utf-8 -*-
#
# Univention Password Self Service frontend base class
#
# Copyright 2015 Univention GmbH
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

import json
import sys
from functools import wraps
from httplib import HTTPSConnection, HTTPException
from Cookie import SimpleCookie
from socket import error as SocketError

sys.stdout = sys.stderr
import cherrypy


def default_error_page(status, message, traceback, version):
	cherrypy.response.headers['Content-type'] = 'application/json'
	data = {'message': message}
	if traceback:
		data['traceback'] = traceback
	return json.dumps(data)


cherrypy.config.update({
	"environment": "embedded",
	"log.access_file": "/var/log/univention/self-service-access.log",
	"log.error_file": "/var/log/univention/self-service-error.log",
	'error_page.default': default_error_page
})


class Session(object):

	def __init__(self, hostname, locale=None):
		self.hostname = hostname
		self.locale = locale
		self._cookie = SimpleCookie()

	def get_connection(self):
		return HTTPSConnection(self.hostname)

	def command(self, url, data):
		status, content, headers = self._request('/univention-management-console/command/%s' % (url,), {'options': data})
		return status, content

	def set(self, data):
		status, content, headers = self._request('/univention-management-console/set', {'options': data})
		return status, content

	def auth(self, data):
		status, content, headers = self._request('/univention-management-console/auth', data)
		if status == 200:
			if self.locale:
				self.set({'locale': self.locale})
		else:
			self.log('Authentication on UMC at %s failed: %r' % (self.hostname, content))
		return status, content

	def _request(self, url, data=None):
		connection = self.get_connection()
		data = json.dumps(data or {})
		try:
			connection.request('POST', url, data, headers=self._headers)
			response = connection.getresponse()
		except:
			return self._handle_exception(*sys.exc_info())

		# if we receive cookies, store them
		cookie = response.getheader('set-cookie')
		if cookie:
			self._cookie.load(cookie)
			self._headers['Cookie'] = '; '.join('%s=%s' % (k, v.value)  for k, v in self._cookie.items())

		if response.getheader('Content-Type', '').startswith('application/json'):
			content = response.read()
			content = json.dumps(content)
		return response.status, content, response.getheaders()

	def _handle_exception(self, etype, exc, etraceback):
		try:
			raise etype, exc, etraceback
		except SocketError:
			self.log('Socket error while accessing UMC at %s: %s' % (self.hostname, exc))
			return 503, 'The Univention Management Console service could not be reached.', {}
		except HTTPException:
			self.log('HTTPException during request to %s: %s' % (self.hostname, exc))
			return 503, 'The communication with the Univention Management Console service failed.', {}


def json_response(func):

	@wraps(func)
	def _decorated(*args, **kwargs):
		data = json.dumps(func(*args, **kwargs))
		cherrypy.response.headers['Content-Type'] = 'application/json'
		return data
	return _decorated


class Ressource(object):

	@property
	def name(self):
		return self.__class__.__name__

	def __init__(self):
		self.umc_server = 'localhost'

	def get_arguments(self, *names):
		if cherrypy.request.headers.get('Content-Type', '').startswith('application/json'):
			try:
				data = json.loads(cherrypy.request.body.read())
			except ValueError:
				raise cherrypy.HTTPError(400, 'Invalid application/json document.')
		else:
			raise cherrypy.HTTPError(415, 'Unknown Content-Type; supported is application/json.')

		if not isinstance(data, dict):
			raise cherrypy.HTTPError(422, 'Payload is not an object.')

		if not names:
			return data
		try:
			args = [data[key] for key in names]
		except KeyError:
			raise cherrypy.HTTPError(422, 'Missing parameters; Required are %s.' % ', '.join(map(repr, names)))
		if len(names) == 1:
			return args[0]
		return args

	def log(self, msg, traceback=False):
		cherrypy.log("{}: {}".format(self.name, msg), traceback=traceback)

	def get_connection(self):
		locale = cherrypy.request.headers.values('Accept-Language') or ['en-US']
		return Session(self.umc_server, locale[0])
