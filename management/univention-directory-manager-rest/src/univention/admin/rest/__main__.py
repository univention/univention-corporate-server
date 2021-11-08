#!/usr/bin/python3
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

import atexit
import os
import time
import locale
import signal
from functools import partial
import argparse
import random
import traceback
import logging
from multiprocessing import current_process
from multiprocessing.managers import BaseManager, DictProxy, SyncManager
from multiprocessing.util import _exit_function

import tornado.log
import tornado.ioloop
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket

# IMPORTANT NOTICE: we must import as few modules as possible, so that univention.admin is not yet imported
# because importing the UDM handlers would cause that the gettext translation gets applied before we set a locale
from univention.management.console.config import ucr
from univention.management.console.log import log_init, log_reopen, CORE
from univention.lib.i18n import Locale


MAX_SOCKET_PATH_LENGTH = 1024  # socket path string must not be longer than that!


def sorted_dict_s(d):
	return "{%s}" % (", ".join(["{!r}: {!r}".format(k, d[k]) for k in sorted(d.keys() or [])]),)


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

		main_pid = os.getpid()
		CORE.error("**** [{!r}] Server.run() main process ****".format(main_pid))
		CORE.error("**** [{!r}] I am starting the manager...".format(main_pid))
		manager_data = SyncManager()
		manager_data.start()
		CORE.error("**** [{!r}] Started the data manager at address {!r}.".format(main_pid, manager_data.address))
		the_dict_proxy_main_proc = manager_data.dict()
		the_dict_proxy_main_proc["creator"] = main_pid
		CORE.error("**** [{!r}] the_dict_proxy_main_proc: {}".format(main_pid, sorted_dict_s(the_dict_proxy_main_proc)))

		class DictAccessManager(SyncManager): pass
		DictAccessManager.register(str("get_the_dict"), callable=lambda: the_dict_proxy_main_proc, proxytype=DictProxy)
		manager_access = DictAccessManager()
		manager_access.start()
		access_manager_address = manager_access.address
		CORE.error("**** [{!r}] Started the access manager at address {!r}.".format(main_pid, access_manager_address))

		server = HTTPServer(application)
		if args.port:
			server.bind(args.port)
		server.start(args.cpus)

		# from here on only the forked process run
		my_pid = os.getpid()

		# remove the SyncManagers exit functions from atexit in the forked processes. must be called only in the creators process
		# in Python3 we can use atexit.unregister(), in Python2 we have to access a private variable
		for func, targs, kargs in atexit._exithandlers[:]:
			if func == _exit_function:# or func == SyncManager.join:
				CORE.error("**** [{!r}] Removing MP.utils._exit_function() from atexit handlers.".format(my_pid))
				atexit._exithandlers.remove((func, targs, kargs))

		class DictManager2(SyncManager): pass
		DictManager2.register(str("get_the_dict"), proxytype=DictProxy)
		# the authkey is the same for all processes, as they were forked()
		manager2 = DictManager2(address=access_manager_address, authkey=current_process().authkey)
		manager2.connect()
		CORE.error("**** [{!r}] Connected to manager.".format(my_pid))
		the_dict_proxy = manager2.get_the_dict()
		the_dict_proxy[my_pid] = "not creator"
		CORE.error("**** [{!r}] dict: {}".format(my_pid, sorted_dict_s(the_dict_proxy)))

		for _ in range(5):
			other_key = random.choice(list(the_dict_proxy.keys()))
			val = random.randint(0, 9)
			sleep = random.uniform(0.0, 0.3)
			CORE.error("**** [{!r}] found {}, writing {!r} to keys {!r} and {!r} and sleeping {:0.2f}s...".format(
				my_pid, sorted_dict_s(the_dict_proxy), val, my_pid, other_key, sleep
			))
			the_dict_proxy[my_pid] = val
			the_dict_proxy[other_key] = val
			time.sleep(sleep)
		CORE.error("**** [{!r}] done. Result: di={}".format(my_pid, sorted_dict_s(the_dict_proxy)))

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
		except Exception:
			CORE.error(traceback.format_exc())
			raise

	def signal_handler_stop(self, server, sig, frame):
		io_loop = tornado.ioloop.IOLoop.instance()
		loop = getattr(io_loop, 'asyncio_loop', io_loop)  # Support Python2+3 Tornado version

		def stop_loop(deadline):
			now = time.time()
			if now < deadline:  # and (io_loop.callbacks or io_loop.timeouts):  # FIXME: neither _UnixSelectorEventLoop nor AsyncIOMainLoop have callbacks
				io_loop.add_timeout(now + 1, stop_loop, deadline)
			else:
				loop.stop()

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
