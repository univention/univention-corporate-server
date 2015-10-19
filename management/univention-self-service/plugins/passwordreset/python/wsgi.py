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

from univention.selfservice.frontend import UniventionSelfServiceFrontend


class PasswordReset(UniventionSelfServiceFrontend):
	@property
	def name(self):
		return "Password Reset"

	@cherrypy.expose
	def get_reset_methods(self, username):
		"""
		Get list of reset methods available for a user. The respective plugin
		must be loaded and activated via UCR and the users respective data
		fields must be non-empty.

		:param username: username
		:return: json encoded list of strings in 'result'
		"""
		connection = self.get_umc_connection()
		url = "passwordreset/get_reset_methods"
		data = {"username": username}
		return self.umc_request(connection, url, data)

	@cherrypy.expose
	def set_contact(self, username, password, email, mobile):
		"""
		Change password reset contact data for user.
		An emtpy string to clear contact data is allowed.

		:param username: username
		:param password: password
		:param email: email
		:param mobile: phone number
		:return: json(True) in 'result' if success or HTTPException in case
		of an authentication error.
		"""
		connection = self.get_umc_connection()
		url = "passwordreset/set_contact"
		data = {"username": username,
			"password": password,
			"email": email,
			"mobile": mobile}
		return self.umc_request(connection, url, data)

	@cherrypy.expose
	def send_token(self, username, method):
		"""
		Send a token to the user using supplied contact method.

		:param username: username
		:param method: method ('sms' / 'email')
		:return: json(True) in 'result' if success
		"""
		connection = self.get_umc_connection()
		url = "passwordreset/send_token"
		data = {"username": username, "method": method}
		return self.umc_request(connection, url, data)

	@cherrypy.expose
	def set_password(self, token, password):
		"""
		Change users password.

		:param token: token
		:param password: new password
		:return: json(True) in 'result' if success or error message if error
		"""
		connection = self.get_umc_connection()
		url = "passwordreset/set_password"
		data = {"token": token, "password": password}
		return self.umc_request(connection, url, data)

application = cherrypy.Application(PasswordReset(), "/self-service/passwordreset")
