#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2024 Univention GmbH
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

import asyncio
import base64
import binascii
import datetime
import functools
import hashlib
import json
import secrets
import traceback
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, timedelta
from typing import Any
from urllib.parse import parse_qsl, urljoin, urlparse

from sqlalchemy.ext.asyncio import create_async_engine
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.web import RequestHandler

from univention.portal import Plugin, config
from univention.portal.extensions.oidc.auth import OIDCAuth, OIDCAuthError, TokenResponse
from univention.portal.extensions.oidc.db import DatabaseError, OIDCSession, SessionRepository, StateRepository, cleanup
from univention.portal.extensions.oidc.schema import metadata_obj
from univention.portal.log import get_logger
from univention.portal.user import User


class Session:
    def __init__(self, nonce):
        self.nonce = nonce
        self.user = None

    def is_valid(self):
        return True


class Authenticator(metaclass=Plugin):
    """
    Our base class for authentication
    May hold all the sessions, set cookies, etc.

    The idea is that this class handles the following
    methods from the Portal:
    `login_request`: A user GETs to the login action
    `login_user`: Credentials are POSTed to this action
    `get_user`: While gathering the portal data, the caller wants

    This base class does nothing...
    """

    def get_auth_mode(self, request):  # pragma: no cover
        return "ucs"

    async def login_request(self, request):  # pragma: no cover
        pass

    async def login_user(self, request):  # pragma: no cover
        pass

    async def logout_user(self, request):  # pragma: no cover
        pass

    async def get_user(self, request):  # pragma: no cover
        return User(username=None, display_name=None, groups=[], headers={})

    def refresh(self, reason=None):  # pragma: no cover
        pass


class UMCAuthenticator(Authenticator):
    """
    Specialized Authenticator that relies on a UMC that actually holds any session.
    Asks UMC for every request if this session is known.

    auth_mode:
            The preferred mode for auth. The portal hands it over to the frontend.
    umc_session_url:
            The URL where to go to with the cookie. Expects a json answer with the username.
    group_cache:
            As UMC does not return groups, we need a cache object that gets us the groups for the username.
    """

    def __init__(self, auth_mode, umc_session_url, group_cache):
        self.auth_mode = auth_mode
        umc_base_url = config.fetch("umc_base_url")
        self.umc_session_url = urljoin(umc_base_url, 'get/session-info')
        self.group_cache = group_cache

    def get_auth_mode(self, request):
        return self.auth_mode

    def refresh(self, reason=None):
        return self.group_cache.refresh(reason=reason)

    async def get_user(self, request):
        cookies = {key: morsel.value for key, morsel in request.cookies.items()}
        username, display_name = await self._get_username(cookies)
        groups = self.group_cache.get().get(username, [])
        return User(username, display_name=display_name, groups=groups, headers=dict(request.request.headers))

    async def _get_username(self, cookies):
        headers = {}
        for cookie in cookies:
            if cookie.startswith("UMCSessionId"):
                # UMCSessionId-1234 -> Host: localhost:1234
                host_port = cookie[13:]
                if host_port:
                    headers = {"Host": f"localhost:{host_port}"}
                break
        else:
            get_logger("user").debug("no user given")
            return None, None
        get_logger("user").debug("searching user for cookies=%r" % cookies)

        username = await self._ask_umc(cookies, headers)
        if username is None:
            get_logger("user").debug("no user found")
            return None, None
        else:
            get_logger("user").debug("found %s" % (username,))
            return username.lower(), username

    async def _ask_umc(self, cookies, headers):
        try:
            headers['Cookie'] = '; '.join('='.join(c) for c in cookies.items())
            req = HTTPRequest(self.umc_session_url, method="GET", headers=headers)
            http_client = AsyncHTTPClient()
            response = await http_client.fetch(req)
            data = json.loads(response.body.decode('UTF-8'))
            username = data["result"]["username"]
        except HTTPError as exc:
            get_logger("user").error("request failed: %s" % exc)
        except OSError as exc:
            get_logger("user").error("connection failed: %s" % exc)
        except ValueError:
            get_logger("user").error("malformed answer!")
        except KeyError:
            get_logger("user").warning("session unknown!")
        else:
            return username


class UMCAndSecretAuthenticator(UMCAuthenticator):
    """Authenticate with a private secret and become any user (god mode)"""

    async def get_user(self, request):
        user = await super().get_user(request)
        if user and user.username:
            return user

        authorization = request.request.headers.get('Authorization')
        if not authorization:
            return user

        try:
            if not authorization.lower().startswith('basic '):
                raise ValueError()
            display_name, password = base64.b64decode(authorization.split(' ', 1)[1].encode('ISO8859-1')).decode('UTF-8').split(':', 1)
        except (ValueError, IndexError, binascii.Error):
            raise HTTPError(400)

        username = display_name.lower()
        get_logger("user").debug("received basic auth request with username=%r", username)
        try:
            with open(config.fetch("portal-secret-file")) as fd:  # noqa: ASYNC101
                config_secret = fd.read().strip()
        except (KeyError, AttributeError):
            return user

        # compare hashed password to prevent time based side channel attack
        if hashlib.sha512(password.encode('utf-8')).hexdigest() != hashlib.sha512(config_secret.encode('utf-8')).hexdigest():
            get_logger("user").warning("password mismatch: %s != %s", config_secret, password)
            return user

        groups = self.group_cache.get().get(username, [])
        return User(username, display_name, groups, headers=dict(request.request.headers))


class OIDCAuthenticator(Authenticator):
    """Authenticate via OpenID Connect"""

    def __init__(self, group_cache):
        oidc_config: dict[str, Any] = config.fetch('oidc')
        self.group_cache = group_cache

        with open(oidc_config['postgres_connection_url']) as fd:
            self.engine = create_async_engine(fd.read())
        self.__pool_opened = False
        self.__init_lock = asyncio.Lock()

        self.session_repository = SessionRepository(self.get_db_connection)
        self.state_repository = StateRepository(self.get_db_connection)
        self.cleanup_task = None

        with open(oidc_config['openid_configuration']) as fd:
            self.openid_configuration = json.loads(fd.read())
        with open(oidc_config['openid_certs']) as fd:
            self.jwks = json.loads(fd.read())
        self.client_id = oidc_config['client_id']
        with open(oidc_config['client_secret_file']) as fd:
            self.client_secret = fd.read()
        self.oidc_flow = OIDCAuth(self.openid_configuration, self.jwks, self.client_id, self.client_secret)

        self.session_cookie_name = oidc_config.get('session_cookie_name', 'portal_session_id')

    def reverse_abs_url(self, request: RequestHandler, name, args=None):
        if args is None:
            args = request.path_args
        return request.request.protocol + "://" + request.request.host + request.reverse_url(name, *args)

    def get_abs_url(self, request: RequestHandler):
        return request.request.protocol + "://" + request.request.host

    async def __create_schema(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata_obj.create_all)

    async def __ensure_db_init(self):
        async with self.__init_lock:
            if not self.__pool_opened:
                await self.__create_schema()
                self.cleanup_task = asyncio.create_task(cleanup(self.get_db_connection))
                self.__pool_opened = True

    @asynccontextmanager
    async def get_db_connection(self):
        if not self.__pool_opened:
            await self.__ensure_db_init()
        async with self.engine.connect() as conn:
            yield conn

    def get_auth_mode(self, request):
        return "oidc"
        # return self.auth_mode

    def refresh(self, reason=None):
        return self.group_cache.refresh(reason=reason)

    async def new_session(self, get_token_response: Callable[[], Awaitable[TokenResponse]], persist_function: Callable[[str, OIDCSession], Awaitable[None]], session_id: str | None = None) -> tuple[str, OIDCSession] | None:
        try:
            token_response = await get_token_response()
        except OIDCAuthError:
            get_logger("user").warning("failed exchange token: %s", traceback.format_exc())
            return None
        session = OIDCSession.from_token_response(token_response, self.oidc_flow.verify_id_token)

        try:
            token_exchange_response = await self.oidc_flow.token_exchange(session.access_token, "https://master.ucs.test/univention/oidc/")
        except OIDCAuthError:
            get_logger("user").warning("token exchange failed: %s", traceback.format_exc())
            return None
        session.umc_access_token = token_exchange_response.access_token

        session_id = session_id or secrets.token_hex(32)

        try:
            await persist_function(session_id, session)
        except DatabaseError:
            get_logger("error").error("failed to persist session: %s", traceback.format_exc())

        return (session_id, session)

    async def login_request(self, request):
        code = request.get_query_argument('code', None)
        state = request.get_query_argument('state', None)
        if code is None or state is None:
            redirect_uri = self.reverse_abs_url(request, 'login')
            get_logger('user').debug('oidc login redirect to OP')
            authorization_request = self.oidc_flow.generate_authorization_request(redirect_uri)
            try:
                await self.state_repository.create(authorization_request.state, authorization_request.code_verifier, redirect_uri)
            except DatabaseError:
                get_logger("error").error("failed to persist state: %s", traceback.format_exc())
                return request.redirect('/', status=302)
            return request.redirect(authorization_request.authorization_url, status=302)

        get_logger('user').debug('oidc login request with state')

        try:
            state_entry = await self.state_repository.get_delete_by_state(state)
        except DatabaseError:
            get_logger("user").error("failed to retrieve state: %s", traceback.format_exc())
            return request.redirect("/", status=302)

        if state_entry is None:
            get_logger('user').warning('state %s not found', state)
            return

        token_response_fn = functools.partial(self.oidc_flow.exchange_code_for_tokens, code, state_entry['redirect_uri'], state_entry['code_verifier'])
        new_session = await self.new_session(token_response_fn, self.session_repository.insert_session)
        if new_session is None:
            # TODO: somehow display an error to the user?
            return request.redirect('/')

        session_id, session = new_session
        request.set_cookie(self.session_cookie_name, session_id, expires=session.refresh_expires_at)

        # TODO: don't hardcode
        return request.redirect(self.reverse_abs_url(request, 'index'), status=302)

    async def login_user(self, request):
        pass

    async def refresh_session(self, session_id: str, session: OIDCSession):
        token_response_fn = functools.partial(self.oidc_flow.refresh_tokens, session.refresh_token)

        new_session = await self.new_session(token_response_fn, self.session_repository.update_session, session_id)
        if new_session is None:
            return None
        _, session = new_session
        return session

    def must_refresh_session(self, session: OIDCSession):
        now = datetime.datetime.now(UTC)

        return (now + timedelta(seconds=30)) > session.access_expires_at

    async def get_session(self, session_id: str | None):
        try:
            if session_id is None:
                return None
            session = await self.session_repository.find_by_session_id(session_id)

            if session is None:
                return None
            if session.refresh_expires_at < datetime.datetime.now(UTC):
                await self.session_repository.delete(session_id)
                return None
        except DatabaseError:
            get_logger("user").error("failed to get session: %s", traceback.format_exc())
            return None

        return session

    async def get_user(self, request):
        session_id = request.get_cookie(self.session_cookie_name, None)
        headers = {}

        display_name = None
        username = None

        session = await self.get_session(session_id)

        if session is not None and self.must_refresh_session(session):
            session = await self.refresh_session(session_id, session)
            if session is None:
                request.clear_cookie(self.session_cookie_name)
                request.redirect('/', status=302)

            request.set_cookie(self.session_cookie_name, session_id, expires=session.refresh_expires_at)

        if session is not None:
            display_name = session.uid
            username = display_name.lower()
            headers['Authorization'] = 'Bearer ' + session.umc_access_token
            request.set_cookie('PortalAccessToken', session.umc_access_token)

        if not session and session_id:
            request.clear_cookie(self.session_cookie_name)

        groups = self.group_cache.get().get(username, [])

        return User(username=username, display_name=display_name, groups=groups, headers=headers)

    async def logout_user(self, request):
        if request.request.method == 'GET':
            session_id = request.get_cookie(self.session_cookie_name, None)
            if session_id is None:
                return request.redirect('/', status=302)

            session = await self.get_session(session_id)

            if session is None:
                request.clear_cookie(self.session_cookie_name)
                return request.redirect('/', status=302)

            post_logout_redirect_location = request.get_query_argument('location', '/univention/portal/')
            post_logout_redirect_uri = urlparse(self.get_abs_url(request))._replace(path=post_logout_redirect_location).geturl()

            url = self.oidc_flow.generate_logout_url(post_logout_redirect_uri, session.id_token)

            return request.redirect(url, status=302)

        elif request.request.method == 'POST':
            content_type = request.request.headers['content-type']
            if content_type != "application/x-www-form-urlencoded":
                return
            args = parse_qsl(request.request.body.decode('utf-8'))
            logout_token = next((value for (key, value) in args if key == 'logout_token'), None)
            if logout_token is None:
                return

            token = self.oidc_flow.verify_logout_token(logout_token)
            if token is None:
                return

            iss = token.get('iss')
            sub = token.get('sub')
            sid = token.get('sid')

            if iss and sub:
                get_logger('user').debug('deleting sessions by iss and sub')
                await self.session_repository.delte_by_iss_and_sub(iss, sub)
            if sid:
                get_logger('user').debug('deleting session by sid')
                await self.session_repository.delete_by_sid(sid)
