# -*- coding: utf-8 -*-
#
# Univention Password Self Service
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


class SetPassword(Ressource):

	@property
	def name(self):
		return "Password Self Service"

	@cherrypy.expose
	@json_response
	def index(self):
		username, password, new_password = self.get_arguments('username', 'password', 'new_password')

		session = self.get_connection()

		# (try to) authenticate with the user credentials
		status, response = session.auth({"username": username, "password": password})
		if status == 401:
			# if the password is expired we need to change it directly
			status, response = session.auth({
				"username": username,
				"password": password,
				"new_password": new_password
			})
			if status == 200:
				# password changing succeeded
				cherrypy.response.status = status
				return response

		if status != 200:
			cherrypy.response.status = status
			return response

		cherrypy.response.status, response = session.set({
			"password": {
				"password": password,
				"new_password": new_password
			}
		})
		return response

application = cherrypy.Application(SetPassword(), "/univention-self-service/passwordchange")
