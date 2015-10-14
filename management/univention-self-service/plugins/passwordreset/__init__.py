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

import os.path

import cherrypy

from univention.selfservice.frontend import UniventionSelfServiceFrontend


class PasswordReset(UniventionSelfServiceFrontend):

	def get_wsgi_app(self):
		config = {
			"/": {
				"tools.sessions.on": True,
				"tools.staticdir.root": os.path.join(self.file_root, "passwordreset")},
			"/static": {
				"tools.staticdir.on": True,
				"tools.staticdir.dir": './static'}}
		self.log("get_wsgi_app() config: {}".format(config))

		return cherrypy.Application(self, self.url, config=config)

	@property
	def url(self):
		return self.url_root + "/passwordreset"

	@property
	def name(self):
		return "Password Reset"

	@cherrypy.expose
	def index(self):
		return """<html>
	<head></head>
	<body>
		<p>PasswordReset static stuff here: <img src="static/debian-logo-reset.png"/></p>
		<p><a href="edit_contact">Edit contact</a></p>
		<p><a href="token">Enter token</a></p>
	</body>
</html>"""

	@cherrypy.expose
	def edit_contact(self):
		connection = self.get_umc_connection()
		if connection:
			result = connection.request('passwordreset/set_contact', {
				"username": "test1",
				"password": "test1",
				"email": "test1m@uni.dtr"
			})
			return "UMC returned: {}".format(result)
		else:
			return "Error connecting to UMC."

	@cherrypy.expose
	def token(self, tokenarg=None):
		if tokenarg:
			html = '''<p>Thank you for token <code>{thetoken}</code></p>
			<input type="hidden" name="token" value="{thetoken}">'''.format(thetoken=tokenarg)
		else:
			html = '<p>Token: <input type="text" name="token" value="please enter token"></p>'
		return """<html>
	<head></head>
	<body>
		<form action="submit_token" method="post">
			{token_input}
			<p>New password: <input type="text" name="password1" value="please enter new password"></p>
			<p>New password again: <input type="text" name="password2" value="please enter new password again"></p>
			<p><input type="submit" value="Submit"></p>
		</form>
	</body>
</html>""".format(token_input=html)

	@cherrypy.expose
	def submit_token(self, token=None, password1=None, password2=None):
		if not all([token, password1, password2]):
			return "missing parameter"
		elif password1 != password2:
			return "passwords do not match"
		else:
			connection = self.get_umc_connection()
			if connection:
				result = connection.request('passwordreset/set_password', {
					"token": token,
					"password": password1,
				})
				return "UMC returned: {}".format(result)
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
