#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2006-2023 Univention GmbH
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

"""This module provides a class for an UMC module server"""

import base64
import json
import os
import re
import signal
import sys
import tempfile
import traceback

import six
import tornado.httputil
import tornado.locale
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket
from tornado.web import Application, HTTPError, RequestHandler

from univention.lib.i18n import I18N_Error, Locale, Translation
from univention.management.console.config import get_int, ucr
from univention.management.console.error import BadRequest, Unauthorized
from univention.management.console.log import MODULE, log_reopen
from univention.management.console.message import Request, Response
from univention.management.console.modules.decorators import SimpleThread


try:
    from typing import Any, NoReturn, Optional  # noqa: F401
except ImportError:
    pass

_ = Translation('univention.management.console').translate

_MODULE_SHUTDOWN_TIMEOUT = 1
_MODULE_ERR_INIT_FAILED = 592  # FIXME: HTTP violation. Use 500/502 intead.
TEMPUPLOADDIR = '/var/tmp/univention-management-console-frontend'


class UploadManager(dict):
    """Store file uploads in temporary files so that module processes can access them"""

    def add(self, request_id, store):
        with tempfile.NamedTemporaryFile(prefix=request_id, dir=TEMPUPLOADDIR, delete=False) as tmpfile:
            tmpfile.write(store['body'])
        self.setdefault(request_id, []).append(tmpfile.name)

        return tmpfile.name

    def cleanup(self, request_id):
        if request_id in self:
            filenames = self[request_id]
            for filename in filenames:
                if os.path.isfile(filename):
                    os.unlink(filename)
            del self[request_id]
            return True

        return False


_upload_manager = UploadManager()


class _Skip(Exception):
    pass


class ModuleServer(object):
    """
    Implements an UMC module server

    :param str socket: UNIX socket filename
    :param str module: name of the UMC module to serve
    :param str logfile: name of the logfile
    :param int timeout: If there are no incoming requests for *timeout* seconds the module server shuts down
    """

    def __init__(self, socket, module, logfile, timeout=300):
        # type: (str, str, str, int) -> None
        self.server = None
        self.__socket = socket
        self.__module = module
        self.__logfile = logfile
        self.__timeout = timeout
        self.__init_etype = None
        self.__init_exc = None
        self.__init_etraceback = None
        self.__initialized = False
        self.__handler = None
        self._load_module()

    def __enter__(self):
        tornado.locale.load_gettext_translations('/usr/share/locale', 'univention-management-console')
        routes = self.__handler.tornado_routes if self.__handler else []
        application = Application(routes + [
            (r'^/exit', Exit),
            (r'^/univention/(?:command|upload)/(.*)', Handler, {'server': self, 'handler': self.__handler}),
            (r'^/cancel', Cancel, {'handler': self.__handler}),
        ], serve_traceback=ucr.is_true('umc/http/show_tracebacks', True))

        signal.signal(signal.SIGALRM, self.signal_handler_alarm)
        signal.signal(signal.SIGTERM, self.signal_handler_stop)
        signal.signal(signal.SIGHUP, self.signal_handler_reload)
        signal.signal(signal.SIGUSR1, self.signal_handler_reload)

        if not six.PY2:
            # TODO: remove in UCS 5.1:
            # allow other threads which are not created by asyncio to start the asyncio loop
            # this is important for UMC modules which call finish() in the thread instead of the main thread!
            import asyncio

            from tornado.platform.asyncio import AnyThreadEventLoopPolicy
            asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        server = HTTPServer(
            application,
            max_body_size=ucr.get_int('umc/http/max_request_body_size', 104857600),
        )
        server.add_socket(bind_unix_socket(self.__socket))
        self.server = server
        server.start()

        return self

    def __exit__(self, etype, exc, etraceback):
        self.running = False
        self.ioloop.stop()

    def loop(self):
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()

    def _load_module(self):
        # type: () -> None
        MODULE.debug('Loading Python module.')
        modname = self.__module
        from .error import UMC_Error
        try:
            try:
                file_ = f'univention.management.console.modules.{modname}'
                self.__module = __import__(file_, {}, {}, modname)
                MODULE.debug('Imported Python module.')
                self.__handler = self.__module.Instance()
                MODULE.debug('Module instance created.')
            except Exception as exc:
                error = _('Failed to load module %(module)s: %(error)s\n%(traceback)s') % {'module': modname, 'error': exc, 'traceback': traceback.format_exc()}
                # TODO: systemctl reload univention-management-console-server
                MODULE.error(error)
                if isinstance(exc, ImportError) and str(exc).startswith(f'No module named {modname}'):
                    error = '\n'.join((
                        _('The requested module %r does not exist.') % (modname,),
                        _('The module may have been removed recently.'),
                        _('Please relogin to the Univention Management Console to see if the error persists.'),
                        _('Further information can be found in the logfile %s.') % ('/var/log/univention/management-console-module-%s.log' % (modname,),),
                    ))
                raise UMC_Error(error, status=_MODULE_ERR_INIT_FAILED)
        except UMC_Error:
            try:
                exc_info = sys.exc_info()
                self.__init_etype, self.__init_exc, self.__init_etraceback = exc_info  # FIXME: do not keep a reference to traceback
            finally:
                exc_info = None

    def signal_handler_stop(self, signo, frame):
        MODULE.process('Received SIGTERM')
        raise SystemExit(0)

    def signal_handler_reload(self, signo, frame):
        MODULE.process(f'Received reload signal ({signo})')
        log_reopen()

    def signal_handler_alarm(self, signo, frame):
        MODULE.info('Received SIGALARM')
        if self.__handler is not None and self.__handler._Base__requests:
            MODULE.warn('There are still open requests - do not shutdown')
            signal.alarm(1)
            return

        if SimpleThread.running_threads > 0:
            MODULE.warn('There are still running threads - do not shutdown')
            signal.alarm(15)
            return

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
        MODULE.process('Committing suicide')
        if self.__handler:
            self.__handler.destroy()
        sys.exit(0)

    def error_handling(self, request, method, etype, exc, etraceback):
        if self.__handler:
            self.__handler._Base__requests[request.id] = (request, method)
            self.__handler._Base__error_handling(request, method, etype, exc, etraceback)
            return

        trace = ''.join(traceback.format_exception(etype, exc, etraceback))
        MODULE.error(f'The init function of the module failed\n{exc}: {trace}')
        from .error import UMC_Error
        if not isinstance(exc, UMC_Error):
            error = _('The initialization of the module failed: %s') % (trace,)
            exc = UMC_Error(error, status=_MODULE_ERR_INIT_FAILED)
            etype = UMC_Error

        resp = Response(request)
        resp.status = exc.status
        resp.message = str(exc)
        resp.result = exc.result
        resp.headers = exc.headers
        request._request_handler.reply(resp)

    def handle_init(self, msg):
        from .error import NotAcceptable
        signal.alarm(self.__timeout)

        if self.__init_etype:
            MODULE.error('module loading failed; respond then shutdown')
            signal.alarm(3)
            exc_info = (self.__init_etype, self.__init_exc, self.__init_etraceback)
            self.error_handling(msg, 'init', *exc_info)
            raise _Skip()

        if not self.__initialized:
            try:
                self.__handler.update_language([msg.locale])
            except NotAcceptable:
                pass  # ignore if the locale doesn't exists, it continues with locale C

            MODULE.debug('Initializing module.')
            try:
                self.__handler.prepare(msg)
            except BaseException:
                MODULE.error('module init() failed; respond then shutdown')
                signal.alarm(3)
                raise
            self.__initialized = True


class Handler(RequestHandler):

    def set_default_headers(self):
        self.set_header('Server', 'UMC-Module/1.0')

    def initialize(self, server, handler):
        self.server = server
        self.handler = handler
        self.request_id = None
        self.ioloop = tornado.ioloop.IOLoop.current()

    def on_connection_close(self):
        super(Handler, self).on_connection_close()
        MODULE.warn('Connection was aborted by the client!')
        self._remove_active_request()

    def on_finish(self):
        super(Handler, self).on_finish()
        self._remove_active_request()

    def _remove_active_request(self):
        if self.handler:
            self.handler._Base__requests.pop(self.request_id, None)

    async def get(self, path):
        try:
            username, password = self.parse_authorization()
        except TypeError:  # can only happen when doing manual requests
            self._ = self.locale.translate
            raise Unauthorized(self._("No authentication provided to module process."))

        flavor = self.request.headers.get('X-UMC-Flavor')
        user_dn = json.loads(self.request.headers.get('X-User-Dn', 'null'))
        auth_type = self.request.headers.get('X-UMC-AuthType')
        mimetype = re.split('[ ;]', self.request.headers.get('Content-Type', ''))[0]
        umcp_command = self.request.headers.get('X-UMC-Command', 'COMMAND')
        if umcp_command == 'UPLOAD' and mimetype != 'multipart/form-data':
            # very important for security reasons in combination with the file_upload decorator
            # otherwise manipulated requests are able to specify the path of temporary uploaded files
            umcp_command = 'COMMAND'

        # tornado drops the territory because we only have /usr/share/locale/de/LC_MESSAGES/
        locale = self.locale.code
        try:
            locale = Locale(locale)
            if not locale.territory:  # TODO: replace by using the actual provided value
                locale.territory = {'de': 'DE', 'fr': 'FR', 'en': 'US'}.get(self.locale.code)
        except I18N_Error as exc:
            MODULE.warn(f'Invalid locale: {exc} {locale}')
        locale = str(locale)

        msg = Request(umcp_command, [path], mime_type=mimetype)
        msg._request_handler = self
        self.request_id = msg.id = self.request.headers.get('X-UMC-Request-ID', msg.id)
        msg.username = username
        msg.user_dn = user_dn
        msg.password = password
        msg.auth_type = auth_type
        msg.locale = locale
        self.request.umcp_message = msg
        if mimetype == 'application/json':
            msg.options = json.loads(self.request.body)
            msg.flavor = flavor
        elif umcp_command == 'UPLOAD' and mimetype == 'multipart/form-data':
            msg.mimetype = 'application/json'
            msg.body = self._get_upload_arguments(msg)
        elif self.request.method in ('GET', 'HEAD'):
            msg.mimetype = 'application/json'
            msg.body = {}
            args = {name: self.get_query_arguments(name) for name in self.request.query_arguments}
            args = {name: value[0] if len(value) == 1 else value for name, value in args.items()}
            msg.flavor = args.pop('flavor', None)
            msg.options = args
        else:
            msg.body = self.request.body

        msg.headers = dict(self.request.headers)
        msg.http_method = self.request.method
        if six.PY2:
            msg.cookies = {x.key.decode('ISO8859-1'): x.value.decode('ISO8859-1') for x in self.request.cookies.values()}
        else:
            msg.cookies = {x.key: x.value for x in self.request.cookies.values()}
        for name, value in list(msg.cookies.items()):
            if name == self.suffixed_cookie_name('UMCSessionId'):
                msg.cookies['UMCSessionId'] = value

        if self.handler:
            last_request = self.handler._current_request
            if not last_request or last_request.user_dn != user_dn:
                MODULE.process('Setting user LDAP DN: %r' % (user_dn,))
            if not last_request or last_request.auth_type != auth_type:
                MODULE.process('Setting auth type: %r' % (auth_type,))
            self.handler._current_request = msg

        method = self.request.headers['X-UMC-Method']  # TODO: error handling if unset
        MODULE.process('Received request %r: %r' % (' '.join(msg.arguments or [msg.command, method]), (msg.username, msg.flavor, msg.auth_type, msg.locale)))
        try:
            self.server.handle_init(msg)
        except _Skip:
            return

        self._auto_finish = False  # if methods start threads and don't await a future of it an empty response is generated because finish() will be called immediately and twice then
        self.handler.execute(method, msg)
        MODULE.debug('Executed handler')

    post = put = delete = patch = options = get

    def reply(self, response):
        if response.headers:
            for key, val in response.headers.items():
                self.set_header(key, val)
        for key, item in response.cookies.items():
            if six.PY2 and not isinstance(key, bytes):
                key = key.encode('utf-8')  # bug in python Cookie!
            if not isinstance(item, dict):
                item = {'value': item}
            self.set_cookie(key, **item)
        if isinstance(response.body, dict):
            response.body.pop('headers', None)
            response.body.pop('cookies', None)
        status = response.status or 200  # status is not set if not json
        self.set_status(status, response.reason)
        # set reason
        self.set_header('Content-Type', response.mimetype)
        if 300 <= status < 400:
            self.set_header('Location', response.headers.get('Location', ''))
        body = response.body
        if response.mimetype == 'application/json':
            if response.message:
                self.set_header('X-UMC-Message', json.dumps(response.message))
            if isinstance(response.body, dict):
                response.body.pop('options', None)
                response.body.pop('message', None)
            body = json.dumps(response.body).encode('ASCII')

        def _reply(body):
            try:
                self.finish(body)
            except Exception:
                MODULE.error(f'FATAL ERROR in reply(): {traceback.format_exc()}')

        ioloop = tornado.ioloop.IOLoop.current()
        if ioloop is self.ioloop:  # main thread
            _reply(body)
        else:
            # TODO: remove in UCS 5.1:
            MODULE.error('called finish() from thread. should be done in main thread! Traceback (most recent call last)\n%s' % (''.join(traceback.format_stack()),))
            self.ioloop.add_callback(_reply, body)

    def suffixed_cookie_name(self, cookie_name):
        # TODO: test if the Host header is correctly passed through the UNIX socket
        host, _, port = self.request.headers.get('Host', '').partition(':')
        if port:
            try:
                port = '-%d' % (int(port),)
            except ValueError:
                port = ''
        return f'{cookie_name}{port}'

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

    def write_error(self, status_code, exc_info=(None, None, None), **kwargs):
        MODULE.error('Fatal error: %s' % (''.join(traceback.format_exception(*exc_info)) if exc_info else status_code,))
        if not hasattr(self.request, 'umcp_message'):
            if status_code >= 500:
                kwargs['exc_info'] = exc_info
            return super(Handler, self).write_error(status_code, **kwargs)

        msg = self.request.umcp_message
        exc_info = exc_info or (None, None, None)
        self.server.error_handling(msg, 'GET', *exc_info)

    def _get_upload_arguments(self, req):
        # TODO: move into UMC-Server core?
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


class Cancel(RequestHandler):

    def initialize(self, handler):
        self.handler = handler

    def get(self):
        id_to_cancel = self.request.headers.get("X-UMC-Request-ID")
        try:
            request, method = self.handler._Base__requests.pop(id_to_cancel)
        except KeyError:
            body = json.dumps({'status': 400, 'result': None, 'message': _('failed to cancel request.')})
            self.set_status(400)
        else:
            MODULE.debug('Cancelled request with id %r' % (id_to_cancel,))
            request._request_handler.finish()
            body = None
            self.set_status(204)
        self.finish(body)


class Exit(RequestHandler):

    def post(self):
        MODULE.process("EXIT: module shutdown in %ds" % _MODULE_SHUTDOWN_TIMEOUT)
        self.set_header('Content-Type', 'application/json')
        body = json.dumps({'status': 200, 'result': None, 'message': 'module %s will shutdown in %ds' % ('TODO', _MODULE_SHUTDOWN_TIMEOUT)}).encode('ASCII')
        self.finish(body)
        signal.alarm(_MODULE_SHUTDOWN_TIMEOUT)

    get = post
