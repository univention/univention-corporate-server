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

import os.path

import cherrypy

from univention.selfservice.frontend import UniventionSelfServiceFrontend


class SetPassword(UniventionSelfServiceFrontend):

	def get_wsgi_app(self):
		config = {
			"/": {
				"tools.sessions.on": True,
				"tools.staticdir.root": os.path.join(self.file_root, "setpassword")},
			"/static": {
				"tools.staticdir.on": True,
				"tools.staticdir.dir": './static'}}
		self.log("get_wsgi_app() config: {}".format(config))

		return cherrypy.Application(self, self.url, config=config)

	@property
	def url(self):
		return self.url_root + "/setpassword"

	@property
	def name(self):
		return "Password Self Service"

	@cherrypy.expose
	def index(self):
		return """<html>
	<head></head>
	<body>
		<form action="set_password" method="post">
			<p>Username: <input type="text" name="username" value="please enter username"></p>
			<p>Old password: <input type="text" name="oldpassword" value="please enter old password"></p>
			<p>New password: <input type="text" name="newpassword1" value="please enter new password"></p>
			<p>New password again: <input type="text" name="newpassword2" value="please enter new password again"></p>
			<p><input type="submit" value="Submit"></p>
		</form>
	</body>
</html>"""

	@cherrypy.expose
	def set_password(self, username, oldpassword, newpassword1, newpassword2):
		self.log("oldpassword: {} newpassword1: {} newpassword2: {}".format(oldpassword, newpassword1, newpassword2))
		if newpassword1 != newpassword2:
			return "new passwords differ"
		connection = self.get_umc_connection(username, oldpassword)
		if connection:
			result = connection.request('passwordchange', {
				"password": oldpassword,
				"new_password": newpassword1
			})
			return "UMC returned: {}".format(result)
		else:
			return "Error connecting to UMC."
