#!/usr/bin/python3
#
# Univention Management Console
#  Univention Directory Manager Module
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import argparse
import locale
import logging
import os
import signal
import time
from functools import partial

import atexit
import tornado.ioloop
import tornado.locale
from setproctitle import getproctitle, setproctitle
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets, bind_unix_socket

from univention.admin.rest.shared_memory import shared_memory
from univention.admin.rest.utils import init_request_context_logging
from univention.config_registry import ucr
from univention.lib.i18n import Locale, Translation
from univention.logging import Structured
# IMPORTANT NOTICE: we must import as few modules as possible, so that univention.admin is not yet imported
# because importing the UDM handlers would cause that the gettext translation gets applied before we set a locale
from univention.management.console.log import log_init, log_reopen


log = Structured(logging.getLogger('ADMIN'))


try:
    from multiprocessing.util import _exit_function
except ImportError:
    _exit_function = None

proctitle = getproctitle()


class Server:

    child_id = None

    def run(self, args):
        self.child_id = None
        setproctitle(proctitle + '   # server')
        # locale must be set before importing UDM!
<<<<<<< HEAD
        log_init('/dev/stdout', args.debug, args.processes != 1, use_structured_logging=ucr.is_true('directory/manager/rest/debug/structured-logging', True))
=======
        log_init('/dev/stdout', args.debug, args.processes != 1)
>>>>>>> 5c6dbcdad4b (feat: remove unstructured debug messages)
        language = str(Locale(args.language))
        locale.setlocale(locale.LC_MESSAGES, language)
        os.umask(0o077)  # FIXME: should probably be changed, this is what UMC sets
        Translation.set_all_languages(language)
        tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-directory-manager-rest')

        # The UMC-Server and module processes are clearing environment variables
        os.environ.clear()
        os.environ['PATH'] = '/bin:/sbin:/usr/bin:/usr/sbin'
        os.environ['LANG'] = language

        # tornado logging
        import univention.logging
        univention.logging.extendLogger('tornado', univention_debug_category='NETWORK')
        logger = logging.getLogger('tornado')
        logger.set_ud_level(ucr.get_int('directory/manager/rest/tornado-debug/level', 3))

        # start sharing memory (before fork, before first usage, after import)
        shared_memory.start()

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

        # start mutliprocessing
        if args.processes != 1:
            if _exit_function is not None:
                atexit.unregister(_exit_function)
            self.socks = socks
            try:
                child_id = tornado.process.fork_processes(args.processes, 0)
            except RuntimeError as exc:  # tornados way to exit from multiprocessing on failures
                log.debug('Stopped process.', error=exc)
                self.signal_handler_stop(None, signal.SIGTERM, None)
            else:
                self.start_child(child_id)
                log.debug('process ended')
        else:
            self.run_server(socks)

    def start_child(self, child_id):
        setproctitle(proctitle + f'   # child {child_id}')
        self.child_id = child_id
        log.debug('Started child.', child=self.child_id)
        shared_memory.children[self.child_id] = os.getpid()
        self.run_server(self.socks)

    def run_server(self, socks):
        from univention.admin.rest.module import Application, request_context
        application = Application(
            serve_traceback=ucr.is_true('directory/manager/rest/show-tracebacks', True),
        )

        server = HTTPServer(application)
        server.add_sockets(socks)

        # signal handers (after forking)
        signal.signal(signal.SIGTERM, partial(self.signal_handler_stop, server))
        signal.signal(signal.SIGINT, partial(self.signal_handler_stop, server))
        signal.signal(signal.SIGHUP, partial(self.signal_handler_reload, application))

        init_request_context_logging(request_context)

        try:
            tornado.ioloop.IOLoop.current().start()
        except Exception:
            log.exception('Could not start main loop')
            self.signal_handler_stop(server, signal.SIGTERM, None)
            raise

    def signal_handler_stop(self, server, sig, frame):
        if self.child_id is None:
            try:
                children_pids = list(shared_memory.children.values())
            except Exception:  # multiprocessing failure
                children_pids = []
            log.debug('Stopping children.', children=children_pids)
            for pid in children_pids:
                self.safe_kill(pid, sig)

            shared_memory.shutdown()
        else:
            log.debug('shutting down in one second')

        io_loop = tornado.ioloop.IOLoop.current()
        loop = getattr(io_loop, 'asyncio_loop', io_loop)  # Support Python2+3 Tornado version

        def stop_loop(deadline):
            now = time.time()
            if now < deadline:
                io_loop.add_timeout(now + 1, stop_loop, deadline)
            else:
                loop.stop()

        def shutdown():
            # wait one second to shutdown
            if server:
                server.stop()
            stop_loop(time.time() + 1)

        io_loop.add_callback_from_signal(shutdown)

    def signal_handler_reload(self, application, signal, frame):
        log.debug('Reloading service.')
        application.reload()
        if self.child_id is None:
            for pid in shared_memory.children.values():
                self.safe_kill(pid, signal)
        ucr.load()
        log_reopen()
        tornado_logger = logging.getLogger("tornado")
        for handler in tornado_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                stream = handler.stream
                handler.close()
                handler.stream = stream

    def safe_kill(self, pid, signo):
        try:
            os.kill(pid, signo)
        except OSError as exc:
            log.error('Could not kill children', signo=signo, pid=pid, error=exc)
        else:
            os.waitpid(pid, os.WNOHANG)

    @classmethod
    def main(cls):
        server = cls()

        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--debug', type=int, default=ucr.get_int('directory/manager/rest/debug/level'), help='debug level')
        parser.add_argument('-l', '--language', default='C', help='The process locale')
        parser.add_argument('-s', '--unix-socket', help='Bind to a UNIX socket')
        parser.add_argument('-p', '--port', help='Bind to a TCP port')
        parser.add_argument('-c', '--processes', type=int, default=ucr.get_int('directory/manager/rest/processes'), help='How many processes should be forked')

        args = parser.parse_args()
        server.run(args)


if __name__ == "__main__":
    Server.main()
