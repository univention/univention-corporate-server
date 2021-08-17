#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019-2021 Univention GmbH
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
import time
import locale
import signal
from functools import partial
import argparse
import traceback
import logging
from multiprocessing.util import _exit_function

from setproctitle import getproctitle, setproctitle

import tornado.log
import tornado.ioloop
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets, bind_unix_socket

# IMPORTANT NOTICE: we must import as few modules as possible, so that univention.admin is not yet imported
# because importing the UDM handlers would cause that the gettext translation gets applied before we set a locale
from univention.management.console.config import ucr
from univention.management.console.log import log_init, log_reopen, CORE
from univention.lib.i18n import Locale
from univention.admin.rest.shared_memory import shared_memory

try:
	from atexit import unregister
except ImportError:
	import atexit

	def unregister(function):
		for func, targs, kargs in atexit._exithandlers[:]:
			if func == function:
				atexit._exithandlers.remove((func, targs, kargs))


proctitle = getproctitle()


class Server(object):

	child_id = None
	children = shared_memory.dict()

	def start(self, args):
		if os.fork() > 0:
			os._exit(0)
		self.run(args)

	def run(self, args):
		self.child_id = None
		setproctitle(proctitle + '   # server')
		# locale must be set before importing UDM!
		log_init('/dev/stdout', args.debug, args.processes != 1)
		language = str(Locale(args.language))
		locale.setlocale(locale.LC_MESSAGES, language)
		os.umask(0o077)  # FIXME: should probably be changed, this is what UMC sets

		# The UMC-Server and module processes are clearing environment variables
		os.environ.clear()
		os.environ['PATH'] = '/bin:/sbin:/usr/bin:/usr/sbin'
		os.environ['LANG'] = language

		# tornado logging
		channel = logging.StreamHandler()
		channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)
		logger.addHandler(channel)

		import univention.admin.modules as udm_modules
		udm_modules.update()

		# bind sockets
		socks = []
		if args.port:
			socks.extend(bind_sockets(args.port, '127.0.0.1', reuse_port=True))

		if args.unix_socket:
			socks.append(bind_unix_socket(args.unix_socket))

		# signal handers
		signal.signal(signal.SIGTERM, partial(self.signal_handler_stop, None))
		signal.signal(signal.SIGINT, partial(self.signal_handler_stop, None))
		signal.signal(signal.SIGHUP, self.signal_handler_reload)

		# important!: make sure shared memory instances are created before fork() ing
		import univention.admin.rest.module  # noqa: F401

		# start mutliprocessing
		if args.processes != 1:
			unregister(_exit_function)
			self.socks = socks
			try:
				child_id = tornado.process.fork_processes(args.processes, 0)
			except RuntimeError as exc:  # tornados way to exit from multiprocessing on failures
				CORE.info('Stopped process: %s' % (exc,))
				self.signal_handler_stop(None, signal.SIGTERM, None)
			else:
				self.start_child(child_id)
				CORE.info('process ended')
		else:
			self.run_server(socks)

	def start_child(self, child_id):
		setproctitle(proctitle + '   # child %s' % (child_id,))
		self.child_id = child_id
		CORE.info('Started child %s' % (self.child_id,))
		self.children[self.child_id] = os.getpid()
		self.run_server(self.socks)

	def run_server(self, socks):
		from univention.admin.rest.module import Application
		application = Application(serve_traceback=ucr.is_true('directory/manager/rest/show-tracebacks', True))

		server = HTTPServer(application)
		server.add_sockets(socks)

		# signal handers (after forking)
		signal.signal(signal.SIGTERM, partial(self.signal_handler_stop, server))
		signal.signal(signal.SIGINT, partial(self.signal_handler_stop, server))
		signal.signal(signal.SIGHUP, self.signal_handler_reload)

		try:
			tornado.ioloop.IOLoop.current().start()
		except Exception:
			CORE.error(traceback.format_exc())
			self.signal_handler_stop(server, signal.SIGTERM, None)
			raise

	def signal_handler_stop(self, server, sig, frame):
		if self.child_id is None:
			try:
				children_pids = list(self.children.values())
			except Exception:  # multiprocessing failure
				children_pids = []
			CORE.info('stopping children: %r' % (children_pids,))
			for pid in children_pids:
				self.safe_kill(pid, sig)

			shared_memory.shutdown()
		else:
			CORE.info('shutting down in one second')

		io_loop = tornado.ioloop.IOLoop.current()
		loop = getattr(io_loop, 'asyncio_loop', io_loop)  # Support Python2+3 Tornado version

		def stop_loop(deadline):
			now = time.time()
			if now < deadline:  # and (io_loop.callbacks or io_loop.timeouts):  # FIXME: neither _UnixSelectorEventLoop nor AsyncIOMainLoop have callbacks
				io_loop.add_timeout(now + 1, stop_loop, deadline)
			else:
				loop.stop()

		def shutdown():
			# wait one second to shutdown
			if server:
				server.stop()
			stop_loop(time.time() + 1)

		io_loop.add_callback_from_signal(shutdown)

	def signal_handler_reload(self, signal, frame):
		if self.child_id is None:
			for pid in self.children.values():
				self.safe_kill(pid, signal)
		ucr.load()
		log_reopen()

	def safe_kill(self, pid, signo):
		try:
			os.kill(pid, signo)
		except EnvironmentError as exc:
			CORE.error('Could not kill(%s) %s: %s' % (signo, pid, exc))
		else:
			os.waitpid(pid, os.WNOHANG)

	@classmethod
	def main(cls):
		server = cls()

		parser = argparse.ArgumentParser()
		parser.add_argument('-d', '--debug', type=int, default=int(ucr.get('directory/manager/rest/debug/level', 2)), help='debug level')
		parser.add_argument('-l', '--language', default='C', help='The process locale')
		parser.add_argument('-s', '--unix-socket', help='Bind to a UNIX socket')
		parser.add_argument('-p', '--port', help='Bind to a TCP port')
		parser.add_argument('-c', '--processes', type=int, default=int(ucr.get('directory/manager/rest/processes', 1)), help='How many processes should be forked')

		subparsers = parser.add_subparsers(title='actions', description='All available actions')

		start_parser = subparsers.add_parser('start', description='Start the service')
		start_parser.set_defaults(func=server.start)

		run_parser = subparsers.add_parser('run', description='Start the service in foreground')
		run_parser.set_defaults(func=server.run)

		args = parser.parse_args()

		args.func(args)


if __name__ == "__main__":
	Server.main()
