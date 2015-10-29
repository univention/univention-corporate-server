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

import json

import cherrypy

from lib import UniventionSelfServiceFrontend, UMCConnectionError


class SetPassword(UniventionSelfServiceFrontend):

	@property
	def name(self):
		return "Password Self Service"

	@cherrypy.expose
	def index(self):
		options = self.get_arguments()
		username = options.get('username')
		password = options.get('password')
		new_password = options.get('new_password')
		if not all((username, password, new_password)):
			raise cherrypy.HTTPError(422)

		try:
			connection = self.get_umc_connection(username=username, password=password)
		except UMCConnectionError as ue:
			cherrypy.response.status = ue.status
			return json.dumps({"status": ue.status, "message": ue.msg})

		url = ""
		data = {
			"password": {
				"password": password,
				"new_password": new_password}
		}
		result = self.umc_request(connection, url, data, command='set')

		if result["status"] == 200:
			self.log("Successfully changed password of user '{}'.".format(username))
		else:
			self.log("Error changing password of user '{}'.".format(username))
		return json.dumps(result)

application = cherrypy.Application(SetPassword(), "/univention-self-service/passwordchange")
