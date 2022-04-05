#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
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

"""
Implements several helper classes to handle the state of a session
and the communication with the module processes
"""

#import asyncio.exceptions
import base64
import errno
import gzip
import json
import os
import re
import signal
import stat
import subprocess
import time
import uuid
from ipaddress import ip_address

import concurrent.futures
import ldap
import pycurl
import six
import tornado
import tornado.curl_httpclient
import tornado.gen
import tornado.httpclient
import tornado.web
from six.moves.http_client import LENGTH_REQUIRED, REQUEST_ENTITY_TOO_LARGE
from six.moves.urllib_parse import urlparse, urlsplit, urlunsplit
from tornado.web import HTTPError

import univention.admin.uexceptions as udm_errors
from univention.lib.i18n import I18N_Error, Locale

from .config import MODULE_COMMAND, MODULE_INACTIVITY_TIMER, ucr
from .error import BadGateway, BadRequest, Forbidden, NotFound, UMC_Error, Unauthorized
from .ldap import reset_cache as reset_ldap_connection_cache
from .locales import I18N, I18N_Manager
from .log import CORE
from .message import Message
from .modules.decorators import copy_function_meta_data, sanitize_args
from .modules.sanitizers import DictSanitizer, ListSanitizer, StringSanitizer
from .pam import PasswordChangeFailed
from .resource import Resource
from .session import categoryManager, moduleManager


try:
    from time import monotonic
except ImportError:
    from monotonic import monotonic

try:
    from shlex import quote
except ImportError:
    from pipes import quote


def sanitize(*sargs, **skwargs):
    defaults = {'default': {}, 'required': True, 'may_change_value': True}
    if sargs:
        defaults.update(skwargs)
        sanitizer = ListSanitizer(sargs[0], **defaults)
    else:
        sanitizer = DictSanitizer(skwargs, **defaults)

    def _decorator(function):
        def _response(self, *args, **kwargs):
            self.request.body_arguments = sanitize_args(sanitizer, 'request.options', {'request.options': self.request.body_arguments})
            return function(self, *args, **kwargs)
        copy_function_meta_data(function, _response)
        return _response
    return _decorator


class CouldNotConnect(Exception):
    pass


class _ModuleConnection(object):

    def __init__(self):
        self._client = tornado.httpclient.AsyncHTTPClient(force_instance=True)

    async def connect(self, connect_retries=0):
        pass

    def request(self, method, uri, headers=None, body=None):
        pass

    def do_request(self, method, uri, headers=None, body=None, unix_socket=None):
        request = tornado.httpclient.HTTPRequest(
            self.get_uri(uri),
            method=method,
            body=body,
            headers=headers,
            allow_nonstandard_methods=True,
            follow_redirects=False,
            connect_timeout=11.0,
            request_timeout=60 * 60 * 24,  # ucr.get_int('umc/http/response-timeout', 310) + 2,  # never!
            prepare_curl_callback=(lambda curl: curl.setopt(pycurl.UNIX_SOCKET_PATH, unix_socket)) if unix_socket else None,
        )

        return self._wrap_future(self._client.fetch(request, raise_error=True))

    def _wrap_future(self, request_future):
        result_future = tornado.concurrent.Future()

        def propagate_result(future):
            if future.cancelled():
                if not result_future.cancelled():
                    result_future.cancel()
            elif future.exception():
                def reraise():
                    raise future.exception()
                try:
                    response = self._handle_errors(reraise)
                except Exception as exc:
                    result_future.set_exception(exc)
                else:
                    result_future.set_result(response)
            else:
                result_future.set_result(future.result())

        def cancel_downstream(future):
            if future.cancelled() and not request_future.cancelled():
                request_future.cancel()

        request_future.add_done_callback(propagate_result)
        result_future.add_done_callback(cancel_downstream)
        return result_future

    def _handle_errors(self, function):
        try:
            response = function()
        except tornado.curl_httpclient.CurlError as exc:
            CORE.warn('Reaching module failed: %s' % (exc,))
            raise CouldNotConnect(exc)
        except tornado.httpclient.HTTPError as exc:
            response = exc.response
            if response is None:  # (599, 'Timeout while connecting', None)
                raise CouldNotConnect(exc)
        except ValueError as exc:  # HTTP GET request with body
            CORE.warn('Reaching module failed: %s' % (exc,))
            raise BadRequest(str(exc))
        except concurrent.futures.CancelledError as exc:
            CORE.warn('Aborted module process request: %s' % (exc,))
            raise CouldNotConnect(exc)
        #except asyncio.exceptions.CancelledError as exc:
        #    CORE.warn('Aborted module process request: %s' % (exc,))
        #    raise CouldNotConnect(exc)

        return response

    def get_uri(self, uri):
        return uri


class ModuleProcess(_ModuleConnection):
    """
    handles the communication with a UMC module process

    :param str module: name of the module to start
    :param str debug: debug level as a string
    :param str locale: locale to use for the module process
    """

    def __init__(self, module, debug='0', locale=None, no_daemonize_module_processes=False):
        super(ModuleProcess, self).__init__()
        self.name = module
        self.socket = '%s.socket' % (('/run/univention-management-console/%u-%s-%lu-%s' % (os.getpid(), module.replace('/', ''), int(time.time() * 1000), uuid.uuid4()))[:85],)
        modxmllist = moduleManager[module]
        python = '/usr/bin/python3' if any(modxml.python_version == 3 for modxml in modxmllist) else '/usr/bin/python2.7'
        args = [python, MODULE_COMMAND, '-m', module, '-s', self.socket, '-d', str(debug)]
        for modxml in modxmllist:
            if modxml.notifier:
                args.extend(['-n', modxml.notifier])
                break
        if locale:
            args.extend(('-l', '%s' % locale))
        if no_daemonize_module_processes:
            args.extend(('-f', '-L', 'stdout'))

        CORE.process('running: %s' % ' '.join(quote(x) for x in args))
        self.__process = tornado.process.Subprocess(args, stderr=subprocess.PIPE)
        # self.__process.initialize()  # TODO: do we need SIGCHILD handler?
        self.set_exit_callback(self._died)  # default

        self._active_requests = set()
        self._inactivity_timer = None

    def set_exit_callback(self, callback):
        self.__process.set_exit_callback(callback)

    async def connect(self, connect_retries=0):
        if os.path.exists(self.socket) and stat.S_ISSOCK(os.stat(self.socket).st_mode):
            return True
        elif connect_retries > 200:
            raise CouldNotConnect('timeout exceeded')
        elif self.__process and self.__process.proc.poll() is not None:
            stderr_fd = self.__process.stderr
            stderr = stderr_fd.read().decode('utf-8', 'replace') if stderr_fd else ''
            if stderr:
                CORE.error(stderr)
            raise CouldNotConnect('process died' + stderr)
        else:
            if connect_retries and not connect_retries % 50:
                CORE.info('No connection to module process yet')
            connect_retries += 1
            await tornado.gen.sleep(0.05)
            await self.connect(connect_retries)

    def request(self, method, uri, headers=None, body=None):
        # watch the module's activity and kill it after X seconds inactivity
        self.reset_inactivity_timer()

        if headers is None:
            headers = {}

        request_id = headers.get("X-UMC-Request-ID") or Message.generate_id()
        self._active_requests.add(request_id)

        def _reset(fut):
            self.reset_inactivity_timer()
            if request_id in self._active_requests:
                self._active_requests.remove(request_id)

        response = self.do_request(method, uri, headers, body, self.socket)
        response.add_done_callback(_reset)

        return response

    def get_uri(self, uri):
        if uri.startswith('https://'):
            uri = 'http://' + uri[8:]

        return uri

    def stop(self):
        # type: () -> None
        CORE.process('ModuleProcess: stopping %r' % (self.pid(),))
        if self.__process:
            tornado.ioloop.IOLoop.current().add_callback(self.stop_process)

    async def stop_process(self):
        proc = self.__process.proc
        if proc.poll() is None:
            proc.terminate()
        await tornado.gen.sleep(3.0)
        if proc.poll() is None:
            proc.kill()
        CORE.info('ModuleProcess: child stopped')
        self.__process = None

    def _died(self, returncode):
        # type: (int) -> None
        pid = self.pid()
        CORE.process('ModuleProcess: child %d (%s) exited with %d%s' % (pid, self.name, returncode, self.str_returncode(returncode)))
        self.disconnect_inactivity_timer()

    def str_returncode(self, returncode):
        if returncode == 0:
            return ' (success)'
        elif returncode < 0:
            try:
                return ' (%s)' % (signal.Signals(abs(returncode)).name,)
            except ValueError:
                pass
        try:
            return ' (%s?)' % (errno.errorcode[abs(returncode)],)
        except KeyError:
            return ''

    def pid(self):
        # type: () -> int
        """Returns process ID of module process"""
        if self.__process is None:
            return 0
        return self.__process.pid

    def disconnect_inactivity_timer(self):
        if self._inactivity_timer is not None:
            ioloop = tornado.ioloop.IOLoop.current()
            ioloop.remove_timeout(self._inactivity_timer)
            self._inactivity_timer = None

    def reset_inactivity_timer(self):
        """
        Resets the inactivity timer. This timer watches the
        inactivity of the module process. If the module did not receive
        a request for MODULE_INACTIVITY_TIMER seconds the module process
        is shut down to save resources.
        """
        self.disconnect_inactivity_timer()
        ioloop = tornado.ioloop.IOLoop.current()
        self._inactivity_timer = ioloop.call_later(MODULE_INACTIVITY_TIMER // 1000, self._mod_inactive)

    def _mod_inactive(self):
        CORE.debug('The module %s is inactive for too long.' % (self.name,))
        if self._active_requests:
            CORE.debug('There are unfinished requests. Waiting for %s requests to finish.' % len(self._active_requests))
            ioloop = tornado.ioloop.IOLoop.current()
            self._inactivity_timer = ioloop.call_later(1, self._mod_inactive)
            return

        if self.__process:
            CORE.info('Sending shutdown request to %s module' % (self.name,))
            try:
                # or /exit HTTP request?
                self.__process.proc.send_signal(signal.SIGALRM)
            except ProcessLookupError as exc:
                CORE.warn('Could not shutdown module: %s' % (exc,))


class ModuleProxy(_ModuleConnection):

    def __init__(self, proxy_address, unix_socket=None):
        self.proxy_address = proxy_address
        self.unix_socket = None

    async def connect(self, connect_retries=0):
        return not self.unix_socket or os.path.exists(self.unix_socket)

    def request(self, method, uri, headers=None, body=None):
        return self.do_request(method, uri, headers, body, self.unix_socket)

    def get_uri(self, uri):
        request = urlsplit(uri)
        proxy = urlsplit(self.proxy_address)
        # TODO: join base path of proxy?
        return urlunsplit((proxy.scheme, proxy.netloc, request.path, request.query, ''))


class Index(Resource):
    """Redirect to correct path when bypassing gateway"""

    def get(self):
        self.redirect('/univention/', status=305)

    post = get


class Logout(Resource):
    """Logout a user"""

    requires_authentication = False
    ignore_session_timeout_reset = True

    def get(self, **kwargs):
        session = self.current_user
        if session.oidc is not None:
            return self.redirect('/univention/oidc/logout', status=303)
        if session.saml is not None:
            return self.redirect('/univention/saml/logout', status=303)

        self.expire_session()
        self.redirect(ucr.get('umc/logout/location') or '/univention/', status=303)

    post = get


class Nothing(Resource):

    requires_authentication = False

    async def prepare(self, *args, **kwargs):
        await super(Nothing, self).prepare(*args, **kwargs)
        raise NotFound()


class SessionInfo(Resource):
    """Get information about the current session"""

    requires_authentication = False
    ignore_session_timeout_reset = True

    def get(self):
        info = {}
        session = self.current_user
        if not session.user.authenticated:
            raise Unauthorized()
        info['username'] = session.user.username
        info['auth_type'] = session.get_umc_auth_type()
        info['remaining'] = int(session.session_end_time - monotonic())
        self.content_negotiation(info)

    post = get


class GetIPAddress(Resource):
    """Get the most likely IP address of the client"""

    requires_authentication = False

    def get(self):
        try:
            addresses = self.addresses
        except ValueError:
            # hacking attempt
            addresses = [self.request.remote_ip]
        self.content_negotiation(addresses, False)

    @property
    def addresses(self):
        addresses = self.request.headers.get('X-Forwarded-For', self.request.remote_ip).split(',') + [self.request.remote_ip]
        addresses = {ip_address(x.decode('ASCII', 'ignore').strip() if isinstance(x, bytes) else x.strip()) for x in addresses}
        addresses.discard(ip_address(u'::1'))
        addresses.discard(ip_address(u'127.0.0.1'))
        return tuple(address.exploded for address in addresses)

    post = get


class NewSession(Resource):
    """Drop all information from the current session - like a relogin"""

    def get(self):
        self.current_user.renew()
        self.content_negotiation(None)

    post = get


class Auth(Resource):
    """Authenticate the user via PAM - either via plain password or via SAML message"""

    requires_authentication = False

    async def parse_authorization(self):
        return  # do not call super method: prevent basic auth

    @sanitize(
        username=StringSanitizer(required=True, minimum=1),
        password=StringSanitizer(required=True, minimum=1),
        auth_type=StringSanitizer(allow_none=True),
        new_password=StringSanitizer(required=False, allow_none=True, minimum=1),
    )
    async def post(self):
        try:
            content_length = int(self.request.headers.get("Content-Length", 0))
        except ValueError:
            content_length = None
        if not content_length and content_length != 0:
            CORE.process('auth: missing Content-Length header')
            raise HTTPError(int(LENGTH_REQUIRED))

        if self.request.method in ('POST', 'PUT'):
            max_length = 2000 * 1024
            if content_length >= max_length:  # prevent some DoS
                raise HTTPError(int(REQUEST_ENTITY_TOO_LARGE), 'Request data is too large, allowed length is %d' % max_length)

        self.request.body_arguments['auth_type'] = None
        self.request.body_arguments['locale'] = self.locale.code
        session = self.current_user
        # create a sessionid if the user is not yet authenticated
        # important: must be called before the auth, to preserve session id in case of re-auth and that a user cannot choose his own session ID by providing a cookie
        sessionid = self.create_sessionid(True)

        result = await session.authenticate(self.request.body_arguments)

        self.set_session(sessionid)
        self.set_status(result.status)
        if result.message:
            self.set_header('X-UMC-Message', json.dumps(result.message))
        self.content_negotiation(result.result)

    get = post


class Modules(Resource):
    """Get a list of available modules"""

    requires_authentication = False

    async def prepare(self):
        await super(Modules, self).prepare()
        self.i18n = I18N_Manager()
        self.i18n['umc-core'] = I18N()
        self.i18n.set_locale(self.locale.code)

    def get(self):
        categoryManager.load()
        moduleManager.load()
        if self.get_argument('reload', False):
            CORE.info('Reloading ACLs for existing session')
            self.current_user.acls._reload_acls_and_permitted_commands()

        permitted_commands = list(self.current_user.acls.get_permitted_commands(moduleManager).values())

        favorites = self._get_user_favorites()
        modules = [
            self._module_definition(module, favorites)
            for module in permitted_commands
            if not module.flavors
        ]
        modules.extend([
            self._flavor_definition(module, flavor, favorites)
            for module in permitted_commands
            for flavor in module.flavors
        ])

        CORE.debug('Modules: %s' % (modules,))
        self.content_negotiation({'modules': modules}, wrap=False)

    def _flavor_definition(self, module, flavor, favorites):
        favcat = []
        if '%s:%s' % (module.id, flavor.id) in favorites:
            favcat.append('_favorites_')

        translationId = flavor.translationId or module.id
        return {
            'id': module.id,
            'flavor': flavor.id,
            'name': self.i18n._(flavor.name, translationId),
            'url': self.i18n._(module.url, translationId),
            'description': self.i18n._(flavor.description, translationId),
            'icon': flavor.icon,
            'categories': (flavor.categories or (module.categories if not flavor.hidden else [])) + favcat,
            'priority': flavor.priority,
            'keywords': list(set(flavor.keywords + [self.i18n._(keyword, translationId) for keyword in flavor.keywords])),
            'version': flavor.version,
        }

    def _module_definition(self, module, favorites):
        favcat = []
        if module.id in favorites:
            favcat.append('_favorites_')
        translationId = module.translationId or module.id
        return {
            'id': module.id,
            'name': self.i18n._(module.name, translationId),
            'url': self.i18n._(module.url, translationId),
            'description': self.i18n._(module.description, translationId),
            'icon': module.icon,
            'categories': module.categories + favcat,
            'priority': module.priority,
            'keywords': list(set(module.keywords + [self.i18n._(keyword, translationId) for keyword in module.keywords])),
            'version': module.version,
        }

    def _get_user_favorites(self):
        if not self.current_user.user.user_dn:  # user not authenticated or no LDAP user
            return set(ucr.get('umc/web/favorites/default', '').split(','))
        lo = self.current_user.get_user_ldap_connection(no_cache=True)
        favorites = self._get_user_preferences(lo).setdefault('favorites', ucr.get('umc/web/favorites/default', '')).strip()
        return set(favorites.split(','))

    def _get_user_preferences(self, lo):
        user_dn = self.current_user.user.user_dn
        if not user_dn or not lo:
            return {}
        try:
            preferences = lo.get(user_dn, ['univentionUMCProperty']).get('univentionUMCProperty', [])
        except (ldap.LDAPError, udm_errors.base) as exc:
            CORE.warn('Failed to retrieve user preferences: %s' % (exc,))
            return {}
        preferences = (val.decode('utf-8', 'replace') for val in preferences)
        return dict(val.split(u'=', 1) if u'=' in val else (val, u'') for val in preferences)

    post = get


class Categories(Resource):
    """Get a list of available categories"""

    requires_authentication = False

    async def prepare(self):
        await super(Categories, self).prepare()
        self.i18n = I18N_Manager()
        self.i18n['umc-core'] = I18N()
        self.i18n.set_locale(self.locale.code)

    def get(self):
        categoryManager.load()
        ucr.load()
        _ucr_dict = dict(ucr.items())
        categories = []
        for category in categoryManager.values():
            categories.append({
                'id': category.id,
                'icon': category.icon,
                'color': category.color,
                'name': self.i18n._(category.name, category.domain).format(**_ucr_dict),
                'priority': category.priority,
            })
        CORE.debug('Categories: %s' % (categories,))
        self.content_negotiation({'categories': categories}, wrap=False)

    post = get


class Upload(Resource):
    """Handle generic file upload which is not targeted for any module"""

    def post(self):
        """Handles a file UPLOAD request, respond with a base64 representation of the content."""
        result = []
        for name, file_objs in self.request.files.items():
            for file_obj in file_objs:
                # don't accept files bigger than umc/server/upload/max
                max_size = ucr.get_int('umc/server/upload/max', 64) * 1024
                if len(file_obj['body']) > max_size:
                    raise BadRequest(self._('filesize is too large, maximum allowed filesize is %d bytes') % (max_size,))

                b64buf = base64.b64encode(file_obj['body']).decode('ASCII')
                result.append({'filename': file_obj['filename'], 'name': name, 'content': b64buf})

        self.content_negotiation(result)


class Command(Resource):
    """Gateway for command/upload requests to UMC module processes"""

    requires_authentication = False

    async def prepare(self, *args, **kwargs):
        await super(Command, self).prepare(*args, **kwargs)
        self.future = None
        self.process = None
        self._request_id = Message.generate_id()
        self._request_url = None

    def forbidden_or_unauthenticated(self, message):
        # make sure that the UMC login dialog is shown if e.g. restarting the UMC-Server during active sessions
        if self.current_user.user.authenticated:
            return Forbidden(message)
        return Unauthorized(self._("For using this module a login is required."))

    def on_connection_close(self):
        super(Command, self).on_connection_close()
        CORE.warn('Connection was aborted by the client!')
        self._remove_active_request()
        if self.future is not None:
            self.future.cancel()
        if self.process is not None and self._request_url is not None:
            self.cancel_request()

    def cancel_request(self):
        fut = self.process.request("GET", "%s://%s/cancel" % (self._request_url.scheme, self._request_url.netloc), {'X-UMC-Request-ID': self._request_id})

        def cb(response):
            CORE.process('Cancel request for %s completed with %d' % (self._request_id, response.result().code))

        tornado.ioloop.IOLoop.current().add_future(fut, cb)

    def on_finish(self):
        super(Command, self).on_finish()
        self._remove_active_request()

    def _remove_active_request(self):
        session = self.current_user
        if session and session._active_requests:
            try:
                session._active_requests.remove(hash(self))
            except KeyError:
                pass

    async def get(self, umcp_command, command):
        """
        Handles a COMMAND request. The request must contain a valid
        and known command that can be accessed by the current user. If
        access to the command is prohibited the request is answered as a
        forbidden command.

        If there is no running module process for the given command a
        new one is started and the request is added to a queue of
        requests that will be passed on when the process is ready.

        If a module process is already running the request is passed on
        and the inactivity timer is reset.
        """
        session = self.current_user
        acls = session.acls
        session._active_requests.add(hash(self))

        self._request_url = urlparse(self.request.full_url())
        module_name = acls.get_module_providing(moduleManager, command)
        if not module_name:
            CORE.warn('No module provides %s' % (command))
            raise self.forbidden_or_unauthenticated(self._("No module found for this request."))

        CORE.info('Checking ACLs for %s (%s)' % (command, module_name))
        options = self.request.body_arguments
        flavor = self.request.headers.get('X-UMC-Flavor')
        if not acls.is_command_allowed(command, options, flavor):
            CORE.warn('Command %s is not allowed' % (command))
            raise self.forbidden_or_unauthenticated(self._("Not allowed to perform this request."))

        methodname = acls.get_method_name(moduleManager, module_name, command)
        if not methodname:
            CORE.warn('Command %s does not exists' % (command))
            raise self.forbidden_or_unauthenticated(self._("Unknown request."))

        headers = self.get_request_header(session, methodname, umcp_command)

        # tornado drops the territory because we only have /usr/share/locale/de/LC_MESSAGES/
        locale = Locale(self.locale.code)
        if not locale.territory:  # TODO: replace by using the actual provided value
            locale.territory = {'de': 'DE', 'fr': 'FR', 'en': 'US'}.get(self.locale.code)
        process = self.process = session.processes.get_process(module_name, str(locale), self.settings.get("no_daemonize_module_processes"))
        CORE.info('Passing request to module %s' % (module_name,))

        try:
            await process.connect()
            # send first command
            self.future = process.request(self.request.method, self.request.full_url(), body=self.request.body or None, headers=headers)
            response = await self.future
        except concurrent.futures.CancelledError:
            raise BadGateway('%s: %s: canceled' % (self._('Connection to module process failed'), module_name))
        #except asyncio.exceptions.CancelledError:
        #    raise BadGateway('%s: %s: canceled' % (self._('Connection to module process failed'), module_name))
        except CouldNotConnect as exc:
            # (happens during starting the service and subprocesses when the UNIX sockets aren't available yet)
            # also happens when module process gets killed during request
            # cleanup module
            session.processes.stop_process(module_name)
            # TODO: read stderr
            reason = 'UMC-Server module process connection failed'
            raise BadGateway('%s: %s: %s' % (self._('Connection to module process failed'), module_name, exc), reason=reason)
        else:
            CORE.debug('Received response %s' % (response.code,))
            self.set_status(response.code, response.reason)
            self._headers = tornado.httputil.HTTPHeaders()

            for header, v in response.headers.get_all():
                if header.title() not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection', 'X-Http-Reason', 'Range', 'Trailer', 'Server', 'Set-Cookie'):
                    self.add_header(header, v)

            message = json.loads(response.headers.get('X-UMC-Message', 'null'))
            if response.headers.get('Content-Type', '').startswith('application/json'):
                if response.code >= 400:
                    body = json.loads(response.body)
                    exc = UMC_Error(message, response.code, body.get('result'), reason=response.reason)
                    self.write_error(response.code, exc_info=(UMC_Error, exc, None), error=body.get('error'))
                    return
                elif message:
                    body = json.loads(response.body)
                    body['message'] = message
                    response._body = json.dumps(body).encode('ASCII')

            if response.body:
                self.set_header('Content-Length', str(len(response.body)))
                self.write(response.body)
            self.finish()

    def get_request_header(self, session, methodname, umcp_command):
        headers = dict(self.request.headers)
        for header in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection', 'X-Http-Reason', 'Range', 'Trailer', 'Server', 'Set-Cookie', 'X-UMC-AuthType'):
            headers.pop(header, None)
        headers['Cookie'] = '; '.join([m.OutputString(attrs=[]) for name, m in self.cookies.items() if not name.startswith('UMCUsername')])
        headers['X-User-Dn'] = json.dumps(session.user.user_dn)
        #headers['X-UMC-Flavor'] = None
        # X-UMC-IP=self.get_ip_address() ?
        headers['Authorization'] = 'basic ' + base64.b64encode(('%s:%s' % (session.user.username, session.get_umc_password())).encode('ISO8859-1')).decode('ASCII')
        headers['X-UMC-Method'] = methodname
        headers['X-UMC-Command'] = umcp_command.upper()
        headers['X-UMC-Request-ID'] = self._request_id
        auth_type = session.get_umc_auth_type()
        if auth_type:
            headers['X-UMC-AuthType'] = auth_type
        return headers

    post = put = delete = patch = options = get


class UCR(Resource):
    """Get UCR Variables matching a pattern"""

    @sanitize(StringSanitizer(required=True))
    def get(self):
        ucr.load()
        result = {}
        for value in self.request.body_arguments:
            if value.endswith('*'):
                value = value[:-1]
                result.update({x: ucr.get(x) for x in ucr.keys() if x.startswith(value)})
            else:
                result[value] = ucr.get(value)
        self.content_negotiation(result)

    post = get


class Meta(Resource):
    """Get Metainformation about the environment"""

    requires_authentication = False

    META_JSON_PATH = '/var/www/univention/meta.json'

    META_UCR_VARS = [
        'domainname',
        'hostname',
        'ldap/master',
        'license/base',
        'server/role',
        'ssl/validity/host',
        'ssl/validity/root',
        'ssl/validity/warning',
        'umc/web/favorites/default',
        'umc/web/piwik',
        'update/available',
        'update/reboot/required',
        'uuid/license',
        'uuid/system',
        'version/erratalevel',
        'version/patchlevel',
        'version/releasename',
        'version/version',
    ]

    def get(self):
        def _get_ucs_version():
            try:
                return '{version/version}-{version/patchlevel} errata{version/erratalevel}'.format(**ucr)
            except KeyError:
                pass

        def _has_system_uuid():
            fake_uuid = '00000000-0000-0000-0000-000000000000'
            return ucr.get('uuid/system', fake_uuid) != fake_uuid

        def _has_free_license():
            return ucr.get('license/base') in ('UCS Core Edition', 'Free for personal use edition')

        try:
            with open(self.META_JSON_PATH) as fd:
                meta_data = json.load(fd)
        except (EnvironmentError, ValueError) as exc:
            CORE.error('meta.json is not available: %s' % (exc,))
            meta_data = {}

        if not self.current_user.user.authenticated:
            self.content_negotiation(meta_data)
            return

        ucr.load()
        meta_data.update({
            "ucsVersion": _get_ucs_version(),
            "ucs_version": _get_ucs_version(),
            "has_system_uuid": _has_system_uuid(),
            "has_free_license": _has_free_license(),
            "hasFreeLicense": _has_free_license(),
            "has_license_base": bool(ucr.get('license/base')),
            "appliance_name": ucr.get('umc/web/appliance/name'),
        })
        meta_data.update([(i, ucr.get(i)) for i in self.META_UCR_VARS])
        self.content_negotiation(meta_data)

    post = get


class Info(Resource):
    """Get UCS and UMC version number and SSL validity"""

    CHANGELOG_VERSION = re.compile(r'^[^(]*\(([^)]*)\).*')

    def get_umc_version(self):
        try:
            with gzip.open('/usr/share/doc/univention-management-console-server/changelog.Debian.gz') as fd:
                line = fd.readline().decode('utf-8', 'replace')
        except IOError:
            return
        try:
            return self.CHANGELOG_VERSION.match(line).groups()[0]
        except AttributeError:
            return

    def get_ucs_version(self):
        return '{}-{} errata{} ({})'.format(ucr.get('version/version', ''), ucr.get('version/patchlevel', ''), ucr.get('version/erratalevel', '0'), ucr.get('version/releasename', ''))

    def get(self):
        ucr.load()

        result = {
            'umc_version': self.get_umc_version(),
            'ucs_version': self.get_ucs_version(),
            'server': '{}.{}'.format(ucr.get('hostname', ''), ucr.get('domainname', '')),
            'ssl_validity_host': ucr.get_int('ssl/validity/host', 0) * 24 * 60 * 60 * 1000,
            'ssl_validity_root': ucr.get_int('ssl/validity/root', 0) * 24 * 60 * 60 * 1000,
        }
        self.content_negotiation(result)

    post = get


class Hosts(Resource):
    """List all directory nodes in the domain"""

    def get(self):
        self.content_negotiation(self.get_hosts())

    post = get

    def get_hosts(self):
        lo = self.lo
        if not lo:  # unjoined / no LDAP connection
            return []
        try:
            domaincontrollers = lo.search(filter="(objectClass=univentionDomainController)", attr=['cn', 'associatedDomain'])
        except (ldap.LDAPError, udm_errors.base) as exc:
            reset_ldap_connection_cache(lo)
            CORE.warn('Could not search for domaincontrollers: %s' % (exc))
            return []

        return sorted(
            b'.'.join((computer['cn'][0], computer['associatedDomain'][0])).decode('utf-8', 'replace')
            for dn, computer in domaincontrollers
            if computer.get('associatedDomain')
        )


class Set(Resource):
    """
    Generic set of locale, user preferences (favorites) or password

    ..deprecated:: 5.0
        use specific pathes ("set/{password,locale,user/preferences}") instead
    """

    async def post(self):
        is_univention_lib = self.request.headers.get('User-Agent', '').startswith('UCS/')
        for key in self.request.body_arguments:
            cls = {'password': SetPassword, 'user': SetUserPreferences, 'locale': SetLocale}.get(key)
            self.set_header('X-UMC-Message', json.dumps('The /univention/set/ endpoint is deprecated and going to be removed.'))
            if is_univention_lib and cls:
                # for backwards compatibility with non redirecting clients we cannot redirect here :-(
                p = cls(self.application, self.request)
                p._ = self._
                p.finish = self.finish
                await p.post()
                return
            if key == 'password':
                self.redirect('/univention/set/password', status=307)
            elif key == 'user':
                self.redirect('/univention/set/user/preferences', status=307)
            elif key == 'locale':
                self.redirect('/univention/set/locale', status=307)
        raise NotFound()


class SetLocale(Resource):
    """
    Set the locale for the session.

    .. deprecated:: 5.0
            set language via `Accept-Language` HTTP header
    """

    requires_authentication = False

    @sanitize(locale=StringSanitizer(required=True))
    async def post(self):
        self.set_header('X-UMC-Message', json.dumps('Setting a session locale is deprecated and going to be removed. Use Accept-Language header instead!'))
        locale = self.request.body_arguments['locale'].replace('-', '_')
        try:
            lang = Locale(locale)
        except I18N_Error as exc:
            CORE.warn('Invalid locale specified: %r -> %s' % (locale, exc))
            raise BadRequest(self._('Specified locale is not available'))
        self.current_user.user._locale = locale
        self.set_header('Content-Language', '%s-%s' % (lang.language, lang.territory) if lang.territory else lang.language)
        self.content_negotiation(None)


class SetPassword(Resource):
    """Change the password of the currently authenticated user"""

    @sanitize(password=DictSanitizer({
        "password": StringSanitizer(required=True),
        "new_password": StringSanitizer(required=True),
    }))
    async def post(self):
        assert self.current_user.user.authenticated
        username = self.current_user.user.username
        password = self.request.body_arguments['password']['password']
        new_password = self.request.body_arguments['password']['new_password']

        args = {
            'locale': str(self.locale.code),
            'username': username,
            'password': password,
            'new_password': new_password,
        }

        CORE.info('Changing password of user %r' % (username,))
        try:
            await self.current_user.change_password(args)
        except PasswordChangeFailed as exc:
            raise UMC_Error(str(exc), 400, {'new_password': '%s' % (exc,)})  # 422
        else:
            CORE.info('Successfully changed password')
            self.set_header('X-UMC-Message', json.dumps(self._('Password successfully changed.')))
            self.content_negotiation(None)


class UserPreferences(Resource):
    """get user specific preferences like favorites"""

    def get(self):
        # fallback is an empty dict
        lo = self.current_user.get_user_ldap_connection()
        result = {'preferences': self._get_user_preferences(lo)}
        self.content_negotiation(result, False)

    def post(self):
        return self.get()

    def _get_user_preferences(self, lo):
        user_dn = self.current_user.user.user_dn
        if not user_dn or not lo:
            return {}
        try:
            preferences = lo.get(user_dn, ['univentionUMCProperty']).get('univentionUMCProperty', [])
        except (ldap.LDAPError, udm_errors.base) as exc:
            CORE.warn('Failed to retrieve user preferences: %s' % (exc,))
            return {}
        preferences = (val.decode('utf-8', 'replace') for val in preferences)
        return dict(val.split(u'=', 1) if u'=' in val else (val, u'') for val in preferences)


class SetUserPreferences(UserPreferences):
    """set user specific preferences like favorites"""

    def get(self):
        return self.post()

    @sanitize(user=DictSanitizer({
        "preferences": DictSanitizer({}, required=True),
    }))
    async def post(self):
        lo = self.current_user.get_user_ldap_connection()
        # eliminate double entries
        preferences = self._get_user_preferences(lo)
        preferences.update(dict(self.request.body_arguments['user']['preferences']))
        if preferences:
            self._set_user_preferences(lo, preferences)
        self.content_negotiation(None)

    def _set_user_preferences(self, lo, preferences):
        user_dn = self.current_user.user.user_dn
        if not user_dn or not lo:
            return

        user = lo.get(user_dn, ['univentionUMCProperty', 'objectClass'])
        old_preferences = user.get('univentionUMCProperty')
        object_classes = list(set(user.get('objectClass', [])) | {b'univentionPerson'})

        # validity / sanitizing
        new_preferences = []
        for key, value in preferences.items():
            if not isinstance(key, six.string_types):
                CORE.warn('user preferences keys needs to be strings: %r' % (key,))
                continue

            # we can put strings directly into the dict
            if isinstance(value, six.string_types):
                new_preferences.append((key, value))
            else:
                new_preferences.append((key, json.dumps(value)))
        new_preferences = [b'%s=%s' % (key.encode('utf-8'), value.encode('utf-8')) for key, value in new_preferences]

        lo.modify(user_dn, [['univentionUMCProperty', old_preferences, new_preferences], ['objectClass', user.get('objectClass', []), object_classes]])
