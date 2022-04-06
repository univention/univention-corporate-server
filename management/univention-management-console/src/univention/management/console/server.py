#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC server
#
# Copyright 2006-2021 Univention GmbH
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

from __future__ import absolute_import, division

import os
import sys
import pipes
import signal
import logging
import resource
import traceback
import threading
from argparse import ArgumentParser

import setproctitle
from tornado.web import Application as TApplication
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets
import tornado
from concurrent.futures import ThreadPoolExecutor

from univention.management.console.resources import Auth, Upload, Command, UCR, Meta, Info, Modules, Categories, UserPreferences, Hosts, Set, SetPassword, SetLocale, SetUserPreferences, SessionInfo, GetIPAddress, Index, Logout, Nothing, NewSession
from univention.management.console.log import CORE, log_init, log_reopen
from univention.management.console.config import ucr, get_int
from univention.management.console.saml import SamlACS, SamlMetadata, SamlSingleLogout, SamlLogout, SamlIframeACS
from univention.management.console.shared_memory import shared_memory

from univention.lib.i18n import NullTranslation

_ = NullTranslation('univention-management-console-frontend').translate

pool = ThreadPoolExecutor(max_workers=get_int('umc/http/maxthreads', 35))


class Application(TApplication):
	"""The tornado application with all UMC resources"""

	def __init__(self, **kwargs):
		tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console')
		super(Application, self).__init__([
			(r'/', Index),
			(r'/auth/?', Auth),
			(r'/upload/?', Upload),
			(r'/(upload)/(.+)', Command),
			(r'/(command)/(.+)', Command),
			(r'/get/session-info', SessionInfo),
			(r'/get/ipaddress', GetIPAddress),
			(r'/get/ucr', UCR),
			(r'/get/meta', Meta),
			(r'/get/info', Info),
			(r'/get/new-session', NewSession),
			(r'/get/modules', Modules),
			(r'/get/categories', Categories),
			(r'/get/user/preferences', UserPreferences),
			(r'/get/hosts', Hosts),
			(r'/set/?', Set),
			(r'/set/password', SetPassword),
			(r'/set/locale', SetLocale),
			(r'/set/user/preferences', SetUserPreferences),
			(r'/saml/', SamlACS),
			(r'/saml/metadata', SamlMetadata),
			(r'/saml/slo/?', SamlSingleLogout),
			(r'/saml/logout', SamlLogout),
			(r'/saml/iframe/?', SamlIframeACS),
			(r'/logout', Logout),
		], default_handler_class=Nothing, **kwargs)

		SamlACS.reload()


class Server(object):
	"""univention-management-console-server"""

	def __init__(self):
		self.parser = ArgumentParser()
		self.parser.add_argument(
			'-d', '--debug', type=int, default=get_int('umc/server/debug/level', 1),
			help='if given than debugging is activated and set to the specified level [default: %(default)s]'
		)
		self.parser.add_argument(
			'-L', '--log-file', default='stdout',
			help='specifies an alternative log file [default: %(default)s]'
		)
		self.parser.add_argument(
			'-c', '--processes', default=get_int('umc/http/processes', 1), type=int,
			help='How many processes to start'
		)
		self.options = self.parser.parse_args()
		self._child_number = None

		# TODO? not really
		# os.environ['LANG'] = locale.normalize(self.options.language)

		# init logging
		log_init(self.options.log_file, self.options.debug, self.options.processes > 1)

	def signal_handler_hup(self, signo, frame):
		"""Handler for the reload action"""
		ucr.load()
		log_reopen()
		self._inform_childs(signal)
		print(''.join(['%s:\n%s' % (th, ''.join(traceback.format_stack(sys._current_frames()[th.ident]))) for th in threading.enumerate()]))

	def signal_handler_reload(self, signo, frame):
		log_reopen()
		SamlACS.reload()
		self._inform_childs(signal)

	def _inform_childs(self, signal):
		if self._child_number is not None:
			return  # we are the child process
		try:
			children = list(shared_memory.children.items())
		except EnvironmentError:
			children = []
		for child, pid in children:
			try:
				os.kill(pid, signal)
			except EnvironmentError as exc:
				CORE.process('Failed sending signal %d to process %d: %s' % (signal, pid, exc))

	def run(self):
		setproctitle.setproctitle('/usr/bin/python3 /usr/sbin/univention-management-console-server' + ' '.join(pipes.quote(x) for x in sys.argv[1:]))
		signal.signal(signal.SIGHUP, self.signal_handler_hup)
		signal.signal(signal.SIGUSR1, self.signal_handler_reload)

		tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
		try:
			fd_limit = get_int('umc/http/max-open-file-descriptors', 65535)
			resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
		except (ValueError, resource.error) as exc:
			CORE.error('Could not raise NOFILE resource limits: %s' % (exc,))

		sockets = bind_sockets(get_int('umc/http/port', 8090), ucr.get('umc/http/interface', '127.0.0.1'), backlog=get_int('umc/http/requestqueuesize', 100), reuse_port=True)
		if self.options.processes != 1:
			shared_memory.start()

			CORE.process('Starting with %r processes' % (self.options.processes,))
			try:
				self._child_number = tornado.process.fork_processes(self.options.processes, 0)
			except RuntimeError as exc:
				CORE.warn('Child process died: %s' % (exc,))
				os.kill(os.getpid(), signal.SIGTERM)
				raise SystemExit(str(exc))
			if self._child_number is not None:
				shared_memory.children[self._child_number] = os.getpid()

		application = Application(serve_traceback=ucr.is_true('umc/http/show_tracebacks', True))
		server = HTTPServer(
			application,
			idle_connection_timeout=get_int('umc/http/response-timeout', 310),  # is this correct? should be internal response timeout
			max_body_size=get_int('umc/http/max_request_body_size', 104857600),
		)
		self.server = server
		server.add_sockets(sockets)

		channel = logging.StreamHandler()
		channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)
		logger.addHandler(channel)

		ioloop = tornado.ioloop.IOLoop.current()

		try:
			ioloop.start()
		except Exception:
			CORE.error(traceback.format_exc())
			ioloop.stop()
			pool.shutdown(False)
			raise
		except (KeyboardInterrupt, SystemExit):
			ioloop.stop()
			pool.shutdown(False)


if __name__ == '__main__':
	Server().run()
