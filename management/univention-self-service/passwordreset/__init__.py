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
		return 'Edit contact'


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
