#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC server
#
# Copyright 2006-2024 Univention GmbH
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

import io
import json
import logging
import logging.handlers
import os
import resource
import signal
import sys
from argparse import ArgumentParser

import atexit
import tornado
from concurrent.futures import ThreadPoolExecutor
from sdnotify import SystemdNotifier
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets
from tornado.web import Application as TApplication, url

import univention.debug as ud
from univention.management.console import saml
from univention.management.console.config import ucr
from univention.management.console.log import CORE, log_init, log_reopen
from univention.management.console.oidc import (
    OIDCBackchannelLogout, OIDCFrontchannelLogout, OIDCLogin, OIDCLogout, OIDCLogoutFinished, OIDCMetadata,
)
from univention.management.console.resources import (
    UCR, Auth, Categories, Command, GetIPAddress, Hosts, Index, Info, Logout, Meta, Modules, NewSession, Nothing,
    SessionInfo, Set, SetLocale, SetPassword, SetUserPreferences, Upload, UserPreferences,
)
from univention.management.console.saml import SamlACS, SamlIframeACS, SamlLogout, SamlMetadata, SamlSingleLogout
from univention.management.console.session import categoryManager, moduleManager
from univention.management.console.shared_memory import shared_memory


try:
    from multiprocessing.util import _exit_function
except ImportError:
    _exit_function = None

pool = ThreadPoolExecutor(max_workers=ucr.get_int('umc/http/maxthreads', 35))


class Application(TApplication):
    """The tornado application with all UMC resources"""

    def __init__(self, **settings):
        tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console')
        super(Application, self).__init__([
            url(r'/', Index, name='index'),
            (r'/auth/?', Auth),
            (r'/upload/?', Upload),
            (r'/(upload)/(.+)', Command),
            (r'/(command)/(.+)', Command),
            (r'/get/session-info', SessionInfo),
            (r'/get/ipaddress', GetIPAddress),
            (r'/get/ucr', UCR),
            (r'/get/meta', Meta),
            (r'/get/info', Info),
            (r'/get/newsession', NewSession),
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
            (r'/saml/logout/?', SamlLogout),
            (r'/saml/iframe/?', SamlIframeACS),
            url(r'/oidc/', OIDCLogin, name='oidc-login'),
            url(r'/oidc/logout', OIDCLogout, name='oidc-logout'),
            url(r'/oidc/frontchannel-logout', OIDCFrontchannelLogout, name='frontchannel-logout'),
            url(r'/oidc/backchannel-logout', OIDCBackchannelLogout, name='backchannel-logout'),
            url(r'/oidc/logout-done', OIDCLogoutFinished, name='oidc-logout-done'),
            url(r'/oidc/.well-known/oauth-client', OIDCMetadata),
            (r'/logout/?', Logout),
            (r'()/(.+)', Command),
        ], default_handler_class=Nothing, **settings)

        SamlACS.reload()


def tornado_log_reopen():
    for logname in ('tornado.access', 'tornado.application', 'tornado.general'):
        logger = logging.getLogger(logname)
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()


class Server(object):
    """univention-management-console-server"""

    def __init__(self):
        self.parser = ArgumentParser()
        self.parser.add_argument(
            '-d', '--debug', type=int, default=ucr.get_int('umc/server/debug/level', 1),
            help='if given then debugging is activated and set to the specified level [default: %(default)s]',
        )
        self.parser.add_argument(
            '-L', '--log-file', default='/var/log/univention/management-console-server.log',
            help='specifies an alternative log file [default: %(default)s]',
        )
        self.parser.add_argument(
            '-p', '--port', default=ucr.get_int('umc/http/port', 8090), type=int,
            help='defines an alternative port number [default %(default)s]',
        )
        self.parser.add_argument(
            '-c', '--processes', type=int, default=1,  # ucr.get_int('umc/http/processes', 1),
            help='How many processes to fork. 0 means auto detection [default: %(default)s].',
        )
        self.parser.add_argument(
            '--no-daemonize-module-processes', action='store_true', help='starts modules in foreground so that logs go to stdout',
        )
        self.options = self.parser.parse_args()
        saml.PORT = self.options.port
        self._child_number = None

        # TODO: not really?
        # os.environ['LANG'] = locale.normalize(self.options.language)

        # init logging
        log_init(self.options.log_file, self.options.debug, self.options.processes > 1)

    def signal_handler_hup(self, signo, frame):
        """Handler for the postrotate action"""
        CORE.process('Got SIGHUP')
        ucr.load()
        log_reopen()
        tornado_log_reopen()
        self._inform_childs(signal)

    def signal_handler_sigusr2(self, signo, frame):
        """Handler for SIGUSR2 for debugging e.g. memory analysis"""
        self.analyse_memory()

    def signal_handler_reload(self, signo, frame):
        """Handler for the reload action"""
        CORE.process('Got SIGUSR1')
        log_reopen()
        tornado_log_reopen()
        SamlACS.reload()
        self.reload()
        self._inform_childs(signal)

    def signal_handler_stop(self, signo, frame):
        CORE.warn('Shutting down all open connections')
        self._inform_childs(signal)
        raise SystemExit(0)

    @classmethod
    def reload(cls):
        CORE.info('Reloading resources: UCR, modules, categories')
        ucr.load()
        moduleManager.load()
        categoryManager.load()

    def _inform_childs(self, signal):
        if self._child_number is not None:
            return  # we are the child process
        try:
            children = list(shared_memory.children.items())
        except EnvironmentError:
            children = []
        for _child, pid in children:
            try:
                os.kill(pid, signal)
            except EnvironmentError as exc:
                CORE.process('Failed sending signal %d to process %d: %s' % (signal, pid, exc))

    def run(self):
        n = SystemdNotifier()
        signal.signal(signal.SIGHUP, self.signal_handler_hup)
        signal.signal(signal.SIGUSR1, self.signal_handler_reload)
        signal.signal(signal.SIGUSR2, self.signal_handler_sigusr2)
        signal.signal(signal.SIGTERM, self.signal_handler_stop)

        tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        try:
            fd_limit = ucr.get_int('umc/http/max-open-file-descriptors', 65535)
            resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
        except (ValueError, resource.error) as exc:
            CORE.error('Could not raise NOFILE resource limits: %s' % (exc,))

        # bind sockets
        sockets = bind_sockets(self.options.port, ucr.get('umc/http/interface', '127.0.0.1'), backlog=ucr.get_int('umc/http/requestqueuesize', 100), reuse_port=True)

        # start sub worker processes
        if self.options.processes != 1:
            # start sharing memory (before fork, before first usage, after import)
            shared_memory.start()

            # stop conflicting exit function of shared_memory in this main process
            if _exit_function is not None:
                atexit.unregister(_exit_function)

            CORE.process('Starting with %r processes' % (self.options.processes,))
            n.notify("READY=1")
            try:
                self._child_number = tornado.process.fork_processes(self.options.processes, 0)
            except RuntimeError as exc:
                CORE.warn('Child process died: %s' % (exc,))
                os.kill(os.getpid(), signal.SIGTERM)
                raise SystemExit(str(exc))
            except KeyboardInterrupt:
                raise SystemExit(0)
            if self._child_number is not None:
                shared_memory.children[self._child_number] = os.getpid()

        with open('/usr/share/univention-management-console/oidc/oidc.json') as fd:
            config = json.load(fd)
            oidc = config.get('oidc', {})
            for setting in oidc.values():
                with open(setting['openid_configuration']) as fd:
                    setting["op"] = json.loads(fd.read())
                with open(setting['openid_certs']) as fd:
                    setting["jwks"] = json.loads(fd.read())
                with open(setting['client_secret_file']) as fd:
                    setting['client_secret'] = fd.read().strip()

            settings = {
                'oidc': oidc,
                'default_authorization_server': config.get('default_authorization_server'),
            }
        application = Application(
            serve_traceback=ucr.is_true('umc/http/show_tracebacks', True),
            no_daemonize_module_processes=self.options.no_daemonize_module_processes,
            **settings,
        )
        server = HTTPServer(
            application,
            idle_connection_timeout=ucr.get_int('umc/http/response-timeout', 310),  # TODO: is this correct? should be internal response timeout
            max_body_size=ucr.get_int('umc/http/max_request_body_size', 104857600),
        )
        self.server = server
        server.add_sockets(sockets)

        if self.options.log_file in {'stdout', 'stderr', '/dev/stdout', '/dev/stderr'}:
            channel = logging.StreamHandler(sys.stdout if self.options.log_file in {'stdout', '/dev/stdout'} else sys.stderr)
        else:
            channel = logging.handlers.RotatingFileHandler(self.options.log_file, 'a+')

        channel.setFormatter(tornado.log.LogFormatter(fmt='%(color)s%(asctime)s  %(levelname)10s      (%(process)9d) :%(end_color)s %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
        for logname in ('tornado.access', 'tornado.application', 'tornado.general'):
            logger = logging.getLogger(logname)
            logger.setLevel({ud.INFO: logging.INFO, ud.WARN: logging.WARNING, ud.ERROR: logging.ERROR, ud.ALL: logging.DEBUG, ud.PROCESS: logging.INFO}.get(ucr.get_int('umc/server/tornado-debug/level', 0), logging.ERROR))
            logger.addHandler(channel)

        self.reload()

        n.notify("READY=1")
        ioloop = tornado.ioloop.IOLoop.current()

        try:
            ioloop.start()
        except Exception:
            CORE.exception('Error during server loop')
            ioloop.stop()
            pool.shutdown(False)
            raise
        except (KeyboardInterrupt, SystemExit):
            ioloop.stop()
            pool.shutdown(False)

    @staticmethod
    def analyse_memory():
        # type: () -> None
        """Print the number of living UMC objects. Helpful when analysing memory leaks."""
        components = (
            'session.Session', 'session.User', 'session.IACLs', 'session.Processes',
            'server.Server',
            'acl.ACLs', 'acl.LDAP_ACLs', 'acl.Rule', 'auth.AuthHandler',
            'base.Base',
            'category.Manager', 'category.XML_Definition',
            'ldap.LDAP',
            'locales.I18N', 'locales.I18N_Manager',
            'module.Manager', 'module.Module', 'module.Flavor',
            'resources.ModuleProcess', 'resources.SessionInfo', 'resources.Command',
            'saml.SAMLUser', 'saml.SamlACS', 'saml.SamlIframeACS', 'saml.SamlLogout', 'saml.SamlSingleLogout',
        )
        try:
            import objgraph
        except ImportError:
            return
        CORE.warn('### MEMORY')
        s = io.StringIO()
        objgraph.show_most_common_types(30, shortnames=False, file=s, filter=lambda o: type(o).__module__.startswith('univention.'))
        CORE.warn('%s', s.getvalue())
        CORE.warn('univention.admin.uldap.access: %d', objgraph.count('univention.admin.uldap.access'))
        CORE.warn('univention.uldap.access: %d', objgraph.count('univention.uldap.access'))
        for component in components:
            CORE.warn('%s: %d', component, objgraph.count('univention.management.console.%s' % (component,)))

        # objgraph.show_backrefs(objgraph.by_type('univention.uldap.access')[0])


def main():
    Server().run()


if __name__ == '__main__':
    main()
