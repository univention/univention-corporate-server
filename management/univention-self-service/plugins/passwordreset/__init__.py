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

from univention.selfservice.frontend import UniventionSelfServiceFrontend

import cherrypy


class PasswordReset(UniventionSelfServiceFrontend):
	@property
	def cherrypy_conf(self):
		return {}

	@property
	def url(self):
		return "passwordreset/"

	@property
	def name(self):
		return "Univention Password Self Service"

	@cherrypy.expose
	def index(self):
		return """<html>
	<head></head>
	<body>
		<p><a href="edit_contact">Edit contact</a></p>
	</body>
</html>"""

	@cherrypy.expose
	def edit_contact(self):
		connection = self.get_umc_connection()
		if connection:
			result = connection.request('passwordreset/editcontact', {
				"username": "test1",
				"password": "test1",
				"email": "test1m@uni.dtr"
			})
			return str(result)
		else:
			return "Error connecting to UMC."

# class PasswordReset(UniventionSelfServiceFrontend):
# 	def get_cherrypy_conf(self):
# 		return {'/passwordreset': {
# 			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
# 			'tools.sessions.on': True,
# 			'tools.response_headers.on': True,
# 			'tools.response_headers.headers': [('Content-Type', 'text/plain')],
# 		}}
#
# 	@cherrypy.tools.accept(media='text/plain')
# 	@cherrypy.expose
# 	def GET(self):
# 		return cherrypy.session['mystring']
#
# 	@cherrypy.expose
# 	def POST(self, length=8):
# 		some_string = ''.join(random.sample(string.hexdigits, int(length)))
# 		cherrypy.session['mystring'] = some_string
# 		return some_string
#
# 	@cherrypy.expose
# 	def PUT(self, another_string):
# 		cherrypy.session['mystring'] = another_string
#
# 	@cherrypy.expose
# 	def DELETE(self):
# 		cherrypy.session.pop('mystring', None)



# 	@cherrypy.expose
# 	def index(self):
# 		cherrypy.response.headers['Content-Type'] = 'application/json'
# 		return json.dumps('Hello World!')
#
#
# def request_token(username, mailaddress):
# 	connection = UMCConnection.get_machine_connection()  # uses the machine.secret, must run as root then, ... (replace?)
# 	try:
# 		result = connection.request('passwordreset/reset', {
# 			'username': username,
# 			'mailaddress': mailaddress,
# 		})
# 	except (ValueError, NotImplementedError, HTTPException):
# 		raise  # the lib is completely broken ...
# 	return result
#
#
# def submit_token(token):
# 	connection = UMCConnection.get_machine_connection()
# 	try:
# 		result = connection.request('passwordreset/submit', {
# 			'token': token,
# 		})
# 	except (ValueError, NotImplementedError, HTTPException):
# 		raise  # the lib is completely broken ...
# 	return result
