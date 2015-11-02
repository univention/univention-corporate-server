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

		# FIXME: makes connection to the DC master instead of localhost
		# FIXME: fails if userpassword is expired
		data = {
			"password": {
				"password": password,
				"new_password": new_password
			}
		}
		result = self.umc_request('', data, command='set', username=username, password=password)
		cherrypy.response.status = result.pop('status', 500)

		if cherrypy.response.status == 200:
			self.log("Successfully changed password of user '{}'.".format(username))
		else:
			self.log("Error changing password of user '{}'.".format(username))
		return result

application = cherrypy.Application(SetPassword(), "/univention-self-service/passwordchange")
