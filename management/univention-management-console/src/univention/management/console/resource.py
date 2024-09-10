#!/usr/bin/python3
#
# Copyright 2022-2024 Univention GmbH
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

import base64
import datetime
import hashlib
import ipaddress
import json
import re
import traceback
import uuid
import weakref
from html import escape, unescape
from http.client import LENGTH_REQUIRED, UNAUTHORIZED
from http.server import BaseHTTPRequestHandler

import tornado
from tornado.gen import convert_yielded
from tornado.web import HTTPError, RequestHandler

import univention.debug as ud
from univention.management.console.config import ucr
from univention.management.console.error import BadRequest, Forbidden, UMC_Error, Unauthorized
from univention.management.console.ldap import get_machine_connection
from univention.management.console.log import CORE
from univention.management.console.session import Session


LENGTH_REQUIRED, UNAUTHORIZED = int(LENGTH_REQUIRED), int(UNAUTHORIZED)

traceback_pattern = re.compile(r'(Traceback.*most recent call|File.*line.*in.*\d)')

_http_response_codes = BaseHTTPRequestHandler.responses.copy()
_http_response_codes[500] = ('Internal Server Error', 'The server encountered an unexpected condition which prevented it from fulfilling the request.')
_http_response_codes[503] = ('Service Unavailable', 'The server is currently unable to handle the request due to a temporary overloading or maintenance of the server.')


class Resource(RequestHandler):
    """Base class for every UMC resource"""

    requires_authentication = True
    ignore_session_timeout_reset = False

    @property
    def _(self):
        return self.locale.translate

    def set_default_headers(self):
        self.set_header('Server', 'UMC-Server/1.0')

    async def prepare(self):
        super().prepare()
        self._proxy_uri()
        self.request.content_negotiation_lang = 'json'
        self.decode_request_arguments()
        await self.parse_authorization()
        if not self.ignore_session_timeout_reset:
            self.current_user.reset_timeout()  # FIXME: order correct?
        await self.refresh_oidc_session()
        self.check_session_validity()
        self.bind_session_to_ip()
        if self.requires_authentication and not self.current_user.user.authenticated:
            raise Forbidden(self._("For using this request a login is required."))

    def check_session_validity(self):
        if not self.requires_authentication:  # TODO: or do we just want to disable this during auth?
            return
        session = self.current_user
        if (session.saml or session.oidc) and session.timed_out():
            raise Unauthorized(self._('The session has expired.'))

    def get_current_user(self):
        session = Session.get_or_create(self.get_session_id())  # FIXME: this creates a Session instance even if the session does not exists
        weakself = weakref.ref(self)
        session._ = lambda *args: weakself()._(*args)  # hack to prevent circular use, when "_" is not yet set but only in prepare()  # noqa: PLW0108
        if not session.user.ip:
            session.user.ip = self.get_ip_address()
        return session

    def get_user_locale(self):
        locale = self.current_user.user._locale
        if locale:
            return tornado.locale.get(locale)

    def get_session_id(self):
        """get the current session ID from cookie (or basic auth hash)."""
        # caution: use this function wisely: do not create a new session with this ID!
        # because it is an arbitrary value coming from the Client!
        return self.get_cookie('UMCSessionId') or self.sessionidhash()

    def create_sessionid(self, random=True):
        if self.current_user.user.authenticated:
            # if the user is already authenticated at the UMC-Server
            # we must not change the session ID cookie as this might cause
            # race conditions in the frontend during login, especially when logged in via SAML
            return self.get_session_id()
        if random:
            return str(uuid.uuid4())
        return self.sessionidhash()

    def sessionidhash(self):
        session = '%s%s%s%s' % (self.request.headers.get('Authorization', ''), self.request.headers.get('Accept-Language', ''), self.get_ip_address(), self.sessionidhash.salt)
        return hashlib.sha256(session.encode('UTF-8')).hexdigest()[:36]
        # TODO: the following is more secure (real random) but also much slower
        # return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', session, self.sessionidhash.salt, 100000))[:36]

    sessionidhash.salt = uuid.uuid4()

    def set_session(self, sessionid):
        Session.put(sessionid, self.current_user)
        self.set_cookies(('UMCSessionId', sessionid), ('UMCUsername', self.current_user.user.username))

    def expire_session(self):
        self.current_user.logout()
        self.set_cookies(('UMCSessionId', ''), expires=datetime.datetime.fromtimestamp(0))

    def set_cookies(self, *cookies, **kwargs):
        # TODO: use expiration from session timeout?
        # set the cookie once during successful authentication
        if kwargs.get('expires'):
            expires = kwargs.get('expires')
        elif ucr.is_true('umc/http/enforce-session-cookie'):
            # session cookie (will be deleted when browser closes)
            expires = None
        else:
            # force expiration of cookie in 5 years from now on...
            expires = (datetime.datetime.now() + datetime.timedelta(days=5 * 365))
        for name, value in cookies:
            name = self.suffixed_cookie_name(name)
            if value is None:  # session.user.username might be None for unauthorized users
                self.clear_cookie(name, path='/univention/')
                continue
            cookie_args = {
                'expires': expires,
                'path': '/univention/',
                'secure': self.request.protocol == 'https' and ucr.is_true('umc/http/enforce-secure-cookie'),
                'version': 1,
            }
            if ucr.get('umc/http/cookie/samesite') in ('Strict', 'Lax', 'None'):
                cookie_args['samesite'] = ucr['umc/http/cookie/samesite']
            self.set_cookie(name, value, **cookie_args)

    def get_cookie(self, name, default=None):
        cookie = self.request.cookies.get
        morsel = cookie(self.suffixed_cookie_name(name)) or cookie(name)
        if morsel:
            return morsel.value
        return default

    def suffixed_cookie_name(self, name):
        return name
        _host, _, port = self.request.headers.get('Host', '').partition(':')
        if port:
            try:
                port = '-%d' % (int(port),)
            except ValueError:
                port = ''
        return '%s%s' % (name, port)

    def bind_session_to_ip(self):
        ip = self.get_ip_address()

        allowed_networks = [ipaddress.ip_network(network) for network in ('127.0.0.1,::1,' + ucr.get('umc/http/allowed-session-overtake/ranges', '')).split(',') if network]

        current_ip = self.current_user.user.ip
        # make sure a lost connection to the UMC-Server does not bind the session to ::1
        if ip != current_ip and any(ipaddress.ip_address(current_ip) in network for network in allowed_networks):
            CORE.warn('Switching session IP from=%r to=%r' % (current_ip, ip))
            self.current_user.user.ip = current_ip = ip

        # bind session to IP (allow requests from localhost)
        if ip != current_ip and not any(ipaddress.ip_address(ip) in network for network in allowed_networks):
            CORE.warn('The sessionid (ip=%s) is not valid for this IP address (%s)' % (ip, current_ip))
            # very important! We must expire the session cookie, with the same path, otherwise one ends up in a infinite redirection loop after changing the IP address (e.g. because switching from VPN to regular network)
            for name in self.request.cookies:
                if name.startswith('UMCSessionId'):
                    self.clear_cookie(name, path='/univention/')
            raise Unauthorized(self._('The current session is not valid with your IP address for security reasons. This might happen after switching the network. Please login again.'))

    def get_ip_address(self):
        """get the IP address of client by last entry (from apache) in X-FORWARDED-FOR header"""
        return self.request.headers.get('X-Forwarded-For', self.request.remote_ip).rsplit(',', 1).pop().strip()

    def _proxy_uri(self):  # TODO: replace with tornado builtin
        if self.request.headers.get('X-UMC-HTTPS') == 'on':
            self.request.protocol = 'https'
        self.request.uri = '/univention%s' % (self.request.uri,)

    async def parse_authorization(self):
        credentials = self.request.headers.get('Authorization')
        if not credentials:
            return
        sessionid = self.create_sessionid(False)
        if sessionid in Session.sessions:
            return
        try:
            scheme, credentials = credentials.split(' ', 1)
        except ValueError:
            raise BadRequest('invalid Authorization')
        if scheme.lower() == 'basic':
            await self.basic_authorization(credentials)
        elif scheme.lower() == 'bearer':
            await self.bearer_authorization(credentials)

    async def basic_authorization(self, credentials):
        try:
            username, password = base64.b64decode(credentials.encode('utf-8')).decode('latin-1').split(':', 1)
        except ValueError:
            raise BadRequest('invalid Authorization')

        sessionid = self.sessionidhash()
        session = self.current_user
        result = await session.authenticate({'locale': self.locale.code, 'username': username, 'password': password})
        if not session.user.authenticated:
            raise UMC_Error(result.message, result.status, result.result)

        ud.debug(ud.MAIN, 99, 'auth: creating session with sessionid=%r' % (sessionid,))
        self.set_session(sessionid)

    async def bearer_authorization(self, bearer_token):
        from univention.management.console.oidc import OIDCResource
        oidc = OIDCResource(self.application, self.request)
        oidc.path_args = self.path_args
        oidc.set_settings(self.application.settings['default_authorization_server'])
        await oidc.bearer_authorization(bearer_token)

    async def refresh_oidc_session(self):
        session = self.current_user

        if not session.oidc or not session.oidc.refresh_token or not session.timed_out(session_end_time=session.oidc.token_end_time):
            return

        if session.oidc.session_refresh_future:
            await session.oidc.session_refresh_future
            return

        from univention.management.console.oidc import OIDCResource
        oidc = OIDCResource(self.application, self.request)
        oidc.path_args = self.path_args
        oidc.set_settings(session.oidc.claims['iss'])
        session.oidc.session_refresh_future = convert_yielded(oidc.refresh_session_tokens(session))
        try:
            await session.oidc.session_refresh_future
        finally:
            session.oidc.session_refresh_future = None

    @property
    def lo(self):
        return get_machine_connection(write=False)[0]

    def load_json(self, body):
        try:
            json_ = json.loads(body)
            if not isinstance(json_, dict):
                raise BadRequest(self._('JSON document have to be dict'))
        except ValueError:
            raise BadRequest(self._('Invalid JSON document'))
        return json_

    def decode_request_arguments(self):
        flavor = None
        if self.request.headers.get('Content-Type', '').startswith('application/json'):  # normal (json) request
            # get body and parse json
            body = '{}'
            if self.request.method in ('POST', 'PUT'):
                if not self.request.headers.get("Content-Length"):
                    raise HTTPError(LENGTH_REQUIRED, 'Missing Content-Length header')
                body = self.request.body.decode('UTF-8', 'replace')

            args = self.load_json(body)
            flavor = args.pop('flavor', None)
            self.request.body_arguments = args.get('options', {})
            self.request.body = json.dumps(self.request.body_arguments).encode('ASCII')
        elif self.request.headers.get('Content-Type', '').startswith('multipart/form-data'):  # file upload request
            flavor = self.get_argument('flavor', None)
        elif self.request.path.startswith(('/auth', '/command', '/get')):  # request is not json
            args = {name: self.get_query_arguments(name) for name in self.request.query_arguments}
            if self.request.method == 'POST':
                args.update({name: self.get_body_arguments(name) for name in self.request.body_arguments})
            args = {name: value[0] if len(value) == 1 else value for name, value in args.items()}
            flavor = args.pop('flavor', None)
            self.request.body_arguments = args
            if self.request.method not in ('HEAD', 'GET'):
                self.request.body = json.dumps(self.request.body_arguments).encode('ASCII')
                self.request.headers['Content-Type'] = 'application/json'
        if flavor and isinstance(flavor, str):
            self.request.headers['X-UMC-Flavor'] = flavor

    def content_negotiation(self, response, wrap=True):
        lang = self.request.content_negotiation_lang
        formatter = getattr(self, '%s_%s' % (self.request.method.lower(), lang), getattr(self, 'get_%s' % (lang,)))
        codec = getattr(self, 'content_negotiation_%s' % (lang,))
        self.finish(codec(formatter(response, wrap)))

    def get_json(self, result, wrap=True):
        message = json.loads(self._headers.get('X-UMC-Message', 'null'))
        response = {'status': self.get_status()}  # TODO: get rid of this
        if message:
            response['message'] = message
        if wrap:
            response['result'] = result
        else:
            response = result
        return response

    def content_negotiation_json(self, response):
        self.set_header('Content-Type', 'application/json')
        return json.dumps(response).encode('ASCII')

    def write_error(self, status_code, **kwargs):
        try:
            return self._write_error(status_code, exc_info=kwargs.pop('exc_info', None), **kwargs)
        except Exception:
            CORE.exception('Error during error handling')
            raise

    def _write_error(self, status_code, exc_info=None, **kwargs):
        if not exc_info:
            return super().write_error(status_code, **kwargs)

        exc = exc_info[1]
        if isinstance(exc, HTTPError | UMC_Error):
            status = exc.status_code
            reason = exc.reason
            body = exc.result if isinstance(exc, UMC_Error) else None
            message = exc.msg if isinstance(exc, UMC_Error) else exc.log_message
            error = kwargs.pop('error', None)
            stacktrace = None
            if isinstance(exc, UMC_Error) and isinstance(error, dict) and error.get('traceback'):
                stacktrace = '%s\nRequest: %s\n\n%s' % (exc.msg, error.get('command'), error.get('traceback'))
                stacktrace = stacktrace.strip()
        else:
            status = 500
            stacktrace = ''.join(traceback.format_exception(*exc_info))
            body = None
            message = str(exc)
            reason = None

        if not self.settings.get("serve_traceback"):
            stacktrace = None

        content = self.default_error_page(status, message, stacktrace, body)
        self.set_status(status, reason=reason)
        self.finish(content.encode('utf-8'))

    def default_error_page(self, status, message, stacktrace, result=None):
        if message and not stacktrace and traceback_pattern.search(message):
            index = message.find('Traceback') if 'Traceback' in message else message.find('File')
            message, stacktrace = message[:index].strip(), message[index:].strip()
        if stacktrace:
            CORE.error('%s', (stacktrace,))
        if ucr.is_false('umc/http/show_tracebacks', False):
            stacktrace = None

        accept_json, accept_html = 0, 0
        for mimetype, qvalue in self.check_acceptable('Accept', 'text/html'):
            if mimetype in ('text/*', 'text/html'):
                accept_html = max(accept_html, qvalue)
            if mimetype in ('application/*', 'application/json'):
                accept_json = max(accept_json, qvalue)
        if accept_json < accept_html:
            return self.default_error_page_html(status, message, stacktrace, result)
        page = self.default_error_page_json(status, message, stacktrace, result)
        if self.request.headers.get('X-Iframe-Response'):
            self.set_header('Content-Type', 'text/html')
            return '<html><body><textarea>%s</textarea></body></html>' % (escape(page, False),)
        return page

    def default_error_page_html(self, status, message, stacktrace, result=None):
        content = self.default_error_page_json(status, message, stacktrace, result)
        try:
            with open('/usr/share/univention-management-console-frontend/error.html') as fd:
                content = fd.read().replace('%ERROR%', json.dumps(escape(content, True)))
            self.set_header('Content-Type', 'text/html; charset=UTF-8')
        except OSError:
            pass
        return content

    def default_error_page_json(self, status, message, stacktrace, result=None):
        """The default error page for responses"""
        if status == 401 and message == _http_response_codes.get(status):
            message = ''
        location = self.request.full_url().rsplit('/', 1)[0]
        if status == 404:
            stacktrace = None
        response = {
            'status': status,
            'message': message,
            'traceback': unescape(stacktrace) if stacktrace else stacktrace,
            'location': location,
        }
        if result:
            response['result'] = result
        self.set_header('Content-Type', 'application/json')
        return json.dumps(response)

    def check_acceptable(self, header, default=''):
        accept = self.request.headers.get(header, default).split(',')
        langs = []
        for language in accept:
            if not language.strip():
                continue
            score = 1.0
            parts = language.strip().split(";")
            for part in (x for x in parts[1:] if x.strip().startswith("q=")):
                try:
                    score = float(part.strip()[2:])
                    break
                except (ValueError, TypeError):
                    raise
                    score = 0.0
            langs.append((parts[0].strip(), score))
        langs.sort(key=lambda pair: pair[1], reverse=True)
        return langs

    def reverse_abs_url(self, name, path=None):
        return '%s://%s/univention%s' % (self.request.protocol, self.request.host, self.reverse_url(name, *(self.path_args if path is None else path)))
