#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import json
import signal
import argparse

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.httputil
import tornado.process

import pycurl

from univention.management.console.config import ucr
import univention.debug as ud


class Server(tornado.web.RequestHandler):
	"""A server which acts as proxy to multiple processes in different languages

	TODO: Implement authentication via PAM
	TODO: Implement ACL handling (restriction on certain paths for certain users/groups)
	TODO: Implement a SAML service provider
	TODO: Implement management of modules
	"""

	LANGUAGE_SERVICE_MAPPING = {
		'de': '/var/run/univention-directory-manager-rest-de-de.socket',
		'de_DE': '/var/run/univention-directory-manager-rest-de-de.socket',
		'en': '/var/run/univention-directory-manager-rest-en-us.socket',
		'en_US': '/var/run/univention-directory-manager-rest-en-us.socket',
	}
	PROCESSES = {}

	def set_default_headers(self):
		self.set_header('Server', 'Univention/1.0')  # TODO:

	@tornado.gen.coroutine
	def get(self):
		accepted_language = self.get_browser_locale().code
		socket = self.LANGUAGE_SERVICE_MAPPING.get(accepted_language, self.LANGUAGE_SERVICE_MAPPING['en'])  # TODO: de_AT
		request = tornado.httpclient.HTTPRequest(
			self.request.full_url(),
			method=self.request.method,
			body=self.request.body or None,
			headers=self.request.headers,
			allow_nonstandard_methods=True,
			follow_redirects=False,
			connect_timeout=20.0,  # TODO: raise value?
			request_timeout=int(ucr.get('directory/manager/rest/response-timeout', '310')) + 1,
			prepare_curl_callback=lambda curl: curl.setopt(pycurl.UNIX_SOCKET_PATH, socket),
		)
		client = tornado.httpclient.AsyncHTTPClient()
		try:
			response = yield client.fetch(request, raise_error=True)
		except tornado.curl_httpclient.CurlError as exc:
			ud.debug(ud.MAIN, ud.WARN, 'Reaching service failed: %s' % (exc,))
			# happens during starting the service and subprocesses when the UNIX sockets aren't available yet
			self.set_status(503)
			self.add_header('Retry-After', '3')  # Tell clients, we are ready in 3 seconds
			self.add_header('Content-Type', 'application/json')
			self.write(json.dumps('The service could not be reached. Please retry in a few seconds or contact an Administrator to restart the service.'))
			self.finish()
			return
		except tornado.httpclient.HTTPError as exc:
			response = exc.response

		self.set_status(response.code, response.reason)
		self._headers = tornado.httputil.HTTPHeaders()

		self.add_header('Content-Language', accepted_language.replace('_', '-'))
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
		parser = argparse.ArgumentParser(prog='python -m univention.admin.rest.server')
		parser.add_argument('-d', '--debug', type=int, default=2)
		args = parser.parse_args()
		ud.init('stdout', ud.FLUSH, ud.NO_FUNCTION)
		ud.set_level(ud.MAIN, args.debug)
		tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
		tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console-module-udm')
		cls.start_processes()
		cls.register_signal_handlers()
		app = tornado.web.Application([
			(r'.*', cls),
		], serve_traceback=ucr.is_true('directory/manager/rest/show-tracebacks', True),
		)
		app.listen(int(ucr.get('directory/manager/rest/server/port', 9979)), ucr.get('directory/manager/rest/server/address', '127.0.0.1'))
		ioloop = tornado.ioloop.IOLoop.instance()
		ioloop.start()

	@classmethod
	def start_processes(cls):
		for language in ('de_DE', 'en_US'):
			socket = cls.LANGUAGE_SERVICE_MAPPING[language]
			cls.PROCESSES[language] = tornado.process.Subprocess(['/usr/bin/python2.7', '-m', 'univention.admin.rest', '-s', socket, '-l', language, 'run'], stdout=sys.stdout, stderr=sys.stderr)

	@classmethod
	def register_signal_handlers(cls):
		signal.signal(signal.SIGTERM, cls.signal_handler_stop)
		signal.signal(signal.SIGINT, cls.signal_handler_stop)
		signal.signal(signal.SIGHUP, cls.signal_handler_reload)

	@classmethod
	def signal_handler_reload(cls, sig, frame):
		for process in cls.PROCESSES.values():
			os.kill(process.pid, sig)

	@classmethod
	def signal_handler_stop(cls, sig, frame):
		for process in cls.PROCESSES.values():
			os.kill(process.pid, sig)

		io_loop = tornado.ioloop.IOLoop.instance()

		def shutdown():
			io_loop.stop()

		io_loop.add_callback_from_signal(shutdown)
