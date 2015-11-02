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

from lib import Ressource, json_response


class PasswordReset(Ressource):

	@property
	def name(self):
		return "Password Reset"

	@cherrypy.expose
	@json_response
	def get_reset_methods(self, *args, **kwargs):
		"""
		Get list of reset methods available for a user. The respective plugin
		must be loaded and activated via UCR and the users respective data
		fields must be non-empty.
		"""
		try:
			username = self.get_arguments('username')
		except KeyError:
			raise cherrypy.HTTPError(422, 'missing parameter username')

		data = {"username": username}
		return self.umc_request('passwordreset/get_reset_methods', data)

	@cherrypy.expose
	@json_response
	def set_contact(self, *args, **kwargs):
		"""
		Change password reset contact data for user.
		An emtpy string to clear contact data is allowed.
		"""
		username, password, email, mobile = self.get_arguments('username', 'password', 'email', 'mobile')

		data = {
			"username": username,
			"password": password,
			"email": email,
			"mobile": mobile
		}
		result = self.umc_request('passwordreset/set_contact', data)
		cherrypy.response.status = result.pop('status', 500)

		if cherrypy.response.status == 200:
			self.log("Successfully set contact for user '{}' email: '{}' mobile: '{}'.".format(username, email, mobile))
		else:
			self.log("Error setting contact for user '{}' email: '{}' mobile: '{}'.".format(username, email, mobile))
		return result

	@cherrypy.expose
	@json_response
	def send_token(self, *args, **kwargs):
		"""
		Send a token to the user using supplied contact method.
		"""
		username, method = self.get_arguments('username', 'method')

		data = {"username": username, "method": method}
		result = self.umc_request('passwordreset/send_token', data)
		cherrypy.response.status = result.pop('status', 500)

		if cherrypy.response.status == 200:
			self.log("Successfully sent token for user '{}' with method '{}'.".format(username, method))
		else:
			self.log("Error sending token for user '{}' with method '{}'.".format(username, method))
		return result

	@cherrypy.expose
	@json_response
	def set_password(self, *args, **kwargs):
		"""Change users password."""
		token, username, password = self.get_arguments('token', 'username', 'password')
		data = {"token": token, "username": username, "password": password}
		result = self.umc_request('passwordreset/set_password', data)
		cherrypy.response.status = result.pop('status', 500)

		if cherrypy.response.status == 200:
			self.log("Successfully changed password of user '{}'.".format(username))
		else:
			self.log("Error changing password of user '{}'.".format(username))
		return result

application = cherrypy.Application(PasswordReset(), "/univention-self-service/passwordreset")
