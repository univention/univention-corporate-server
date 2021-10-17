#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
#
# Copyright 2006-2022 Univention GmbH
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

"""This module provides a class for an UMC module server. it is based on
the UMC server class
:class:`~univention.management.console.protocol.server.Server`.
"""

import os
import re
import sys
import json
import signal
import base64
import traceback
import logging
import threading

import notifier
import notifier.threads
import six
import tornado.log
from tornado.web import RequestHandler, Application, HTTPError
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket
import tornado.httputil

from .message import Request, Response
from .definitions import MODULE_ERR_INIT_FAILED, SUCCESS

from univention.management.console.log import MODULE
from univention.management.console.config import ucr, get_int
from univention.management.console.error import BadRequest
from univention.management.console.protocol.session import TEMPUPLOADDIR
from univention.management.console.protocol.server import _upload_manager

from univention.lib.i18n import Translation

try:
	from typing import Any, NoReturn, Optional  # noqa F401
except ImportError:
	pass

_ = Translation('univention.management.console').translate

if 422 not in tornado.httputil.responses:
	tornado.httputil.responses[422] = 'Unprocessable Entity'  # Python 2 is missing this status code


class ModuleServer(object):

	"""Implements an UMC module server

	:param str socket: UNIX socket filename
	:param str module: name of the UMC module to serve
	:param int timeout: If there are no incoming requests for *timeout* seconds the module server shuts down
	:param bool check_acls: if False the module server does not check the permissions (**dangerous!**)
	"""

	def __init__(self, socket, module, logfile, timeout=300):
		# type: (str, str, int, bool) -> None
		self.server = None
		self.__socket = socket
		self.__module = module
		self.__logfile = logfile
		self.__timeout = timeout
		# self.__time_remaining = timeout
		self.__active_requests = {}
		# self._timer()
		self.__init_etype = None
		self.__init_exc = None
		self.__init_etraceback = None
		self.__initialized = False
		self.__handler = None
		self._load_module()

	def _load_module(self):
		# type: () -> None
		MODULE.process('Loading python module.')
		modname = self.__module
		from ..error import UMC_Error
		try:
			try:
				file_ = 'univention.management.console.modules.%s' % (modname,)
				self.__module = __import__(file_, {}, {}, modname)
				MODULE.process('Imported python module.')
				self.__handler = self.__module.Instance()
				MODULE.process('Module instance created.')
			except Exception as exc:
				error = _('Failed to load module %(module)s: %(error)s\n%(traceback)s') % {'module': modname, 'error': exc, 'traceback': traceback.format_exc()}
				# TODO: systemctl reload univention-management-console-server
				MODULE.error(error)
				if isinstance(exc, ImportError) and str(exc).startswith('No module named %s' % (modname,)):
					error = '\n'.join((
						_('The requested module %r does not exist.') % (modname,),
						_('The module may have been removed recently.'),
						_('Please relogin to the Univention Management Console to see if the error persists.'),
						_('Further information can be found in the logfile %s.') % ('/var/log/univention/management-console-module-%s.log' % (modname,),),
					))
				raise UMC_Error(error, status=MODULE_ERR_INIT_FAILED)
		except UMC_Error:
			try:
				exc_info = sys.exc_info()
				self.__init_etype, self.__init_exc, self.__init_etraceback = exc_info  # FIXME: do not keep a reference to traceback
			finally:
				exc_info = None
		else:
			self.__handler.signal_connect('success', self._reply)

	def _reply(self, response):
		# any exception here will crash the process!
		try:
			return self.__reply(response)

#			async def reply():
#				self.__reply(response)
#			io_loop = tornado.ioloop.IOLoop.current()
#			io_loop.run_sync(reply)
##			io_loop.add_callback(self.__reply, response)
#			self.__reply(response)
		except Exception:
			MODULE.error(traceback.format_exc())
			raise

	def __reply(self, response):
		umcp_request = self.__active_requests.pop(response.id)
		request = umcp_request.request_handler
		if response.headers:
			for key, val in response.headers.items():
				request.set_header(key, val)
		for key, item in response.cookies.items():
			if six.PY2 and not isinstance(key, bytes):
				key = key.encode('utf-8')  # bug in python Cookie!
			if not isinstance(item, dict):
				item = {'value': item}
			request.set_cookie(key, **item)
		if isinstance(response.body, dict):
			response.body.pop('headers', None)
			response.body.pop('cookies', None)
		status = response.status or 200  # status is not set if not json
		request.set_status(status, response.reason)
		# set reason
		request.set_header('Content-Type', response.mimetype)
		if 300 <= status < 400:
			request.set_header('Location', response.headers.get('Location', ''))
		body = response.body
		if response.mimetype == 'application/json':
			if response.message:
				request.set_header('X-UMC-Message', json.dumps(response.message))
			if isinstance(response.body, dict):
				response.body.pop('options', None)
				response.body.pop('message', None)
			body = json.dumps(response.body).encode('ASCII')
		request.finish(body)

	# def _timer(self):
	# 	# type: () -> None
	# 	"""In order to avoid problems when the system time is changed (e.g.,
	# 	via rdate), we register a timer event that counts down the session
	# 	timeout second-wise."""
	# 	# count down the remaining time
	# 	if not self.__active_requests:
	# 		self.__time_remaining -= 1

	# 	if self.__time_remaining <= 0:
	# 		# module has timed out
	# 		self._timed_out()
	# 	else:
	# 		# count down the timer second-wise (in order to avoid problems when
	# 		# changing the system time, e.g. via rdate)
	# 		notifier.timer_add(1000, self._timer)

	def signal_handler_alarm(self, signo, frame):
		if self.__active_requests:
			MODULE.info('There are still open requests - do not shutdown')
			signal.alarm(1)
			return
		MODULE.info('Committing suicide')
		io_loop = tornado.ioloop.IOLoop.current()

		def shutdown():
			if self.__handler:
				self.__handler.destroy()
			self.server.stop()
			io_loop.stop()
		io_loop.add_callback_from_signal(shutdown)
		self._timed_out()

	def _timed_out(self):
		# type: () -> NoReturn
		MODULE.info('Committing suicide')
		if self.__handler:
			self.__handler.destroy()
		sys.exit(0)

	def error_handling(self, request, method, etype, exc, etraceback):
		if self.__handler:
			self.__handler._Base__requests[request.id] = (request, method)
			self.__handler._Base__error_handling(request, method, etype, exc, etraceback)
			return

		trace = ''.join(traceback.format_exception(etype, exc, etraceback))
		MODULE.error('The init function of the module failed\n%s: %s' % (exc, trace,))
		from ..error import UMC_Error
		if not isinstance(exc, UMC_Error):
			error = _('The initialization of the module failed: %s') % (trace,)
			exc = UMC_Error(error, status=MODULE_ERR_INIT_FAILED)
			etype = UMC_Error

		resp = Response(request)
		resp.status = exc.status
		resp.message = str(exc)
		resp.result = exc.result
		resp.headers = exc.headers
		self._reply(resp)

	def handle(self, msg, method, username, password, user_dn, auth_type, locale):
		from ..error import NotAcceptable
		# self.__time_remaining = self.__timeout
		signal.alarm(self.__timeout)
		MODULE.process('Received request %r: %r' % (' '.join(msg.arguments or [msg.command, method]), (username, msg.flavor, auth_type, locale)))
		self.__active_requests[msg.id] = msg

		if msg.command == 'EXIT':
			shutdown_timeout = 1
			MODULE.info("EXIT: module shutdown in %ds" % shutdown_timeout)
			# shutdown module after one second
			resp = Response(msg)
			resp.status = SUCCESS
			resp.message = 'module %s will shutdown in %ds' % (msg.arguments[0], shutdown_timeout)
			self._reply(resp)
			# notifier.timer_add(shutdown_timeout, self._timed_out)
			signal.alarm(1)
			return

		if self.__init_etype:
			# notifier.timer_add(10000, self._timed_out)
			signal.alarm(1)
			six.reraise(self.__init_etype, self.__init_exc, self.__init_etraceback)

		if not self.__initialized:
			self.__handler.username = username
			self.__handler.user_dn = user_dn
			self.__handler.password = password
			self.__handler.auth_type = auth_type
			try:
				self.__handler.update_language([locale])
			except NotAcceptable:
				pass  # ignore if the locale doesn't exists, it continues with locale C

			MODULE.process('Initializing module.')
			try:
				self.__handler.init()
				self.__initialized = True
			except Exception:
				try:
					exc_info = sys.exc_info()
					self.__init_etype, self.__init_exc, self.__init_etraceback = exc_info  # FIXME: do not keep a reference to traceback
					self.error_handling(msg, 'init', *exc_info)
				finally:
					exc_info = None
				return

		self.__handler.execute(method, msg)
		MODULE.info('Executed handler')

	def __enter__(self):
		application = Application([
			(r'/exit', Exit, {'server': self}),
			(r'(.*)', Handler, {'server': self}),
		], serve_traceback=ucr.is_true('umc/http/show_tracebacks', True))

		server = HTTPServer(application)
		server.add_socket(bind_unix_socket(self.__socket))
		self.server = server
		server.start()

		signal.signal(signal.SIGALRM, self.signal_handler_alarm)
		channel = logging.StreamHandler()
		channel = logging.FileHandler('/var/log/univention/%s.log' % (self.__logfile,))
		channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
		logger = logging.getLogger('tornado.access')
		logger.setLevel(logging.DEBUG)
		logger.addHandler(channel)

		self.running = True

		#import asyncio
		#from tornado.platform.asyncio import AnyThreadEventLoopPolicy
		#asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

		class Simple(notifier.threads.Simple):
			def run(self):
				io_loop = tornado.ioloop.IOLoop.current()
				future = io_loop.run_in_executor(None, self._run)
				io_loop.add_future(future, lambda f: self.announce())
		notifier.threads.Simple = Simple

		# we don't need to start a second loop if we use the tornado main loop
		self.nf_thread = None
		if notifier.loop is not getattr(getattr(notifier, 'nf_tornado', None), 'loop', None):
			def loop():
				while self.running:
					notifier.step()
			self.nf_thread = threading.Thread(target=loop, name='notifier')
			self.nf_thread.start()

		return self

	def __exit__(self, etype, exc, etraceback):
		self.running = False
		self.ioloop.stop()
		if self.nf_thread:
			self.nf_thread.join()

	def loop(self):
		self.ioloop = tornado.ioloop.IOLoop.current()
		self.ioloop.start()


class Handler(RequestHandler):

	def set_default_headers(self):
		self.set_header('Server', 'UMC-Module/1.0')  # TODO:

	def initialize(self, server):
		self.server = server

	def prepare(self):
		pass

	@tornado.web.asynchronous
	def get(self, path):
		method = self.request.headers['X-UMC-Method']
		flavor = self.request.headers.get('X-UMC-Flavor')
		username, password = self.parse_authorization()
		user_dn = json.loads(self.request.headers.get('X-User-Dn', 'null'))
		auth_type = self.request.headers.get('X-UMC-AuthType')
		mimetype = re.split('[ ;]', self.request.headers.get('Content-Type', ''))[0]
		umcp_command = self.request.headers.get('X-UMC-Command', 'COMMAND')
		if mimetype.startswith('application/json'):
			mimetype = 'application/json'
		locale = self.locale.code
		msg = Request(umcp_command, [path], mime_type=mimetype)
		if mimetype.startswith('application/json'):
			msg.options = json.loads(self.request.body)
			msg.flavor = flavor
		elif umcp_command == 'UPLOAD' and self.request.headers.get('Content-Type', '').startswith('multipart/form-data'):
			msg.body = self._get_upload_arguments(msg)
		else:
			msg.body = self.request.body
		msg.headers = dict(self.request.headers)
		msg.http_method = self.request.method
		if six.PY2:
			msg.cookies = dict((x.key.decode('ISO8859-1'), x.value.decode('ISO8859-1')) for x in self.request.cookies.values())
		else:
			msg.cookies = dict((x.key, x.value) for x in self.request.cookies.values())
		for name, value in list(msg.cookies.items()):
			if name == self.suffixed_cookie_name('UMCSessionId'):
				msg.cookies['UMCSessionId'] = value
		msg.request_handler = self
		self.server.handle(msg, method, username, password, user_dn, auth_type, locale)

	def suffixed_cookie_name(self, cookie_name):
		return cookie_name  # FIXME/TODO

	def parse_authorization(self):
		credentials = self.request.headers.get('Authorization')
		if not credentials:
			return
		try:
			scheme, credentials = credentials.split(u' ', 1)
		except ValueError:
			raise HTTPError(400)
		if scheme.lower() != u'basic':
			return
		try:
			username, password = base64.b64decode(credentials.encode('utf-8')).decode('latin-1').split(u':', 1)
		except ValueError:
			raise HTTPError(400)
		return username, password

	@tornado.web.asynchronous
	def post(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def put(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def delete(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def patch(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def options(self, *args):
		return self.get(*args)

	def _get_upload_arguments(self, req):
		# FIXME / TODO: move into UMC-Server core?
		options = []
		body = {}

		# check if enough free space is available
		min_size = get_int('umc/server/upload/min_free_space', 51200)  # kilobyte
		s = os.statvfs(TEMPUPLOADDIR)
		free_disk_space = s.f_bavail * s.f_frsize // 1024  # kilobyte
		if free_disk_space < min_size:
			MODULE.error('there is not enough free space to upload files')
			raise BadRequest('There is not enough free space on disk')

		for name, field in self.request.files.items():
			for part in field:
				tmpfile = _upload_manager.add(req.id, part)
				options.append(self._sanitize_file(tmpfile, name, part))

		for name in self.request.body_arguments:
			value = self.get_body_arguments(name)
			if len(value) == 1:
				value = value[0]
			body[name] = value

		body['options'] = options
		return body

	def _sanitize_file(self, tmpfile, name, store):
		# check if filesize is allowed
		st = os.stat(tmpfile)
		max_size = get_int('umc/server/upload/max', 64) * 1024
		if st.st_size > max_size:
			MODULE.warn('file of size %d could not be uploaded' % (st.st_size))
			raise BadRequest('The size of the uploaded file is too large')

		filename = store['filename']
		# some security
		for c in '<>/':
			filename = filename.replace(c, '_')

		return {
			'filename': filename,
			'name': name,
			'tmpfile': tmpfile,
			'content_type': store['content_type'],
		}


def Exit(RequestHandler):
	pass
