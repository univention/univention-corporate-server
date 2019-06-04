#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019 Univention GmbH
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

from __future__ import absolute_import
from __future__ import division
#from __future__ import print_function
from __future__ import unicode_literals

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.httputil

from univention.management.console.config import ucr


class Server(tornado.web.RequestHandler):
	"""A server which acts as proxy to multiple processes in different languages

	TODO: Implement authentication via PAM
	TODO: Implement ACL handling (restriction on certain pathes for certain users/groups)
	TODO: Implement a SAML service provider
	TODO: Implement management of modules
	TODO: use UNIX sockets instead of TCP services
	"""

	LANGUAGE_SERVICE_MAPPING = {
		'de': 8887,
		'de-DE': 8887,
		'en': 8888,
		'en-US': 8888,
	}

	@tornado.gen.coroutine
	def get(self):
		accepted_language = self.get_browser_locale().code
		port = self.LANGUAGE_SERVICE_MAPPING.get(accepted_language, self.LANGUAGE_SERVICE_MAPPING['en'])
		uri = 'http://localhost:%d%s' % (port, self.request.uri,)
		request = tornado.httpclient.HTTPRequest(
			uri,
			method=self.request.method,
			body=self.request.body or None,
			headers=self.request.headers,
			allow_nonstandard_methods=True,
			follow_redirects=False,
			connect_timeout=20.0,
			request_timeout=20.0,
		)
		client = tornado.httpclient.AsyncHTTPClient()
		response = yield client.fetch(request, raise_error=False)
		self.set_status(response.code, response.reason)
		self._headers = tornado.httputil.HTTPHeaders()

		for header, v in response.headers.get_all():
			if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection', 'X-Http-Reason'):
				self.add_header(header, v)

		if response.body:
			self.set_header('Content-Length', len(response.body))
			self.write(response.body)
		self.finish()

	@tornado.web.asynchronous
	def post(self):
		return self.get()

	@tornado.web.asynchronous
	def put(self):
		return self.get()

	@tornado.web.asynchronous
	def delete(self):
		return self.get()

	@tornado.web.asynchronous
	def patch(self):
		return self.get()

	@tornado.web.asynchronous
	def options(self):
		return self.get()

	@classmethod
	def main(cls):
		tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
		tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console-module-udm')
		app = tornado.web.Application([
			(r'.*', cls),
		], debug=True
		)
		app.listen(int(ucr.get('umc/server/port', 8889)))
		ioloop = tornado.ioloop.IOLoop.instance()
		ioloop.start()
