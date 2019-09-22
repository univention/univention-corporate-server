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
import time
import locale
import signal
from functools import partial
import argparse
import traceback
import logging

import tornado.log
import tornado.ioloop
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket

# IMPORTANT NOTICE: we must import as few modules as possible, so that univention.admin is not yet imported
# because importing the UDM handlers would cause that the gettext translation gets applied before we set a locale
from univention.management.console.config import ucr
from univention.management.console.log import log_init, log_reopen, CORE
from univention.lib.i18n import Locale


class Server(object):

	def start(self, args):
		if os.fork() > 0:
			os._exit(0)
		self.run()

	def run(self, args):
		# locale must be set before importing UDM!
		log_init('/dev/stdout', args.debug)
		language = str(Locale(args.language))
		locale.setlocale(locale.LC_MESSAGES, language)
		os.umask(0o077)  # FIXME: should probably be changed, this is what UMC sets

		# The UMC-Server and module processes are clearing environment variables
		os.environ.clear()
		os.environ['PATH'] = '/bin:/sbin:/usr/bin:/usr/sbin'
		os.environ['LANG'] = language

		import univention.admin.modules as udm_modules
		udm_modules.update()

		from univention.admin.rest.module import Application
		application = Application(serve_traceback=ucr.is_true('directory/manager/rest/show-tracebacks', True))

		server = HTTPServer(application)
		if args.port:
			server.bind(args.port)
		server.start(args.cpus)

		if args.unix_socket:
			socket = bind_unix_socket(args.unix_socket)
			server.add_socket(socket)
		signal.signal(signal.SIGTERM, partial(self.signal_handler_stop, server))
		signal.signal(signal.SIGINT, partial(self.signal_handler_stop, server))
		signal.signal(signal.SIGHUP, self.signal_handler_reload)

		channel = logging.StreamHandler()
		channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)
		logger.addHandler(channel)

		try:
			tornado.ioloop.IOLoop.current().start()
		except (SystemExit, KeyboardInterrupt):
			raise
		except:
			CORE.error(traceback.format_exc())
			raise

	def signal_handler_stop(self, server, sig, frame):
		io_loop = tornado.ioloop.IOLoop.instance()

		def stop_loop(deadline):
			now = time.time()
			if now < deadline and (io_loop._callbacks or io_loop._timeouts):
				io_loop.add_timeout(now + 1, stop_loop, deadline)
			else:
				io_loop.stop()

		def shutdown():
			# wait one second to shutdown
			server.stop()
			stop_loop(time.time() + 1)

		io_loop.add_callback_from_signal(shutdown)

	def signal_handler_reload(self, signal, frame):
		ucr.load()
		log_reopen()

	@classmethod
	def main(cls):
		server = cls()

		parser = argparse.ArgumentParser()
		parser.add_argument('-d', '--debug', type=int, default=int(ucr.get('directory/manager/rest/debug/level', 2)), help='debug level')
		parser.add_argument('-l', '--language', default='C', help='The process locale')
		parser.add_argument('-s', '--unix-socket', help='Bind to a UNIX socket')
		parser.add_argument('-p', '--port', help='Bind to a TCP port')
		parser.add_argument('-c', '--cpus', type=int, default=int(ucr.get('directory/manager/rest/cpus', 1)), help='How many processes should be forked')

		subparsers = parser.add_subparsers(title='actions', description='All available actions')

		start_parser = subparsers.add_parser('start', description='Start the service')
		start_parser.set_defaults(func=server.start)

		run_parser = subparsers.add_parser('run', description='Start the service in foreground')
		run_parser.set_defaults(func=server.run)

		args = parser.parse_args()

		args.func(args)


if __name__ == "__main__":
	Server.main()
