# -*- coding: utf-8 -*-
#
# Univention Password Reset Self Service
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

import cherrypy

from univention.management.console.config import ucr
from lib import Ressource, json_response


class PasswordReset(Ressource):

	@property
	def name(self):
		return "Password Reset"

	def __init__(self):
		super(PasswordReset, self).__init__()
		self.umc_server = ucr.get("self-service/backend-server", ucr.get("ldap/master"))

	def get_connection(self):
		connection = super(PasswordReset, self).get_connection()
		username = "{}$".format(ucr.get("hostname"))
		try:
			with open('/etc/self-service-ldap.secret') as fd:
				password = fd.read().strip()
		except (OSError, IOError) as exc:
			self.log('Could not read UMC server credentials: %s' % (exc,))
			raise cherrypy.HTTPError('Could not authenticate at Univention Management Console service.', 503)
		status, response = connection.auth({'username': username, 'password': password})
		if status != 200:
			raise cherrypy.HTTPError(response, status)
		return connection

	def umc_request(self, url, data):
		connection = self.get_connection()
		cherrypy.response.status, response = connection.command(url, data)
		if isinstance(response, dict):
			response.pop('status', None)
		return response

	@cherrypy.expose
	@json_response
	def get_reset_methods(self, *args, **kwargs):
		"""
		Get list of reset methods available for a user. The respective plugin
		must be loaded and activated via UCR and the users respective data
		fields must be non-empty.
		"""
		username = self.get_arguments('username')

		return self.umc_request('passwordreset/get_reset_methods', {"username": username})

	@cherrypy.expose
	@json_response
	def get_contact(self, *args, **kwargs):
		"""
		Get contact data available for a user. The users respective data
		fields must be non-empty.
		"""
		username, password = self.get_arguments('username', 'password')

		return self.umc_request('passwordreset/get_contact', {
			"username": username,
			"password": password
		})

	@cherrypy.expose
	@json_response
	def set_contact(self, *args, **kwargs):
		"""
		Change password reset contact data for user.
		An emtpy string to clear contact data is allowed.
		"""
		username, password, email, mobile = self.get_arguments('username', 'password', 'email', 'mobile')

		return self.umc_request('passwordreset/set_contact', {
			"username": username,
			"password": password,
			"email": email,
			"mobile": mobile
		})

	@cherrypy.expose
	@json_response
	def send_token(self, *args, **kwargs):
		"""
		Send a token to the user using supplied contact method.
		"""
		username, method = self.get_arguments('username', 'method')

		return self.umc_request('passwordreset/send_token', {
			"username": username,
			"method": method
		})

	@cherrypy.expose
	@json_response
	def set_password(self, *args, **kwargs):
		"""Change users password."""
		token, username, password = self.get_arguments('token', 'username', 'password')

		return self.umc_request('passwordreset/set_password', {
			"token": token,
			"username": username,
			"password": password
		})

application = cherrypy.Application(PasswordReset(), "/univention-self-service/passwordreset")
