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
import hashlib
import json
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, timedelta
from typing import Any
from urllib.parse import parse_qsl, quote_plus, urlencode, urljoin, urlparse

import jwt
import redis.asyncio as redis
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.web import RequestHandler

from univention.portal import Plugin, config
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


@dataclass
class OIDCSession:
    id_token: str
    access_token: str
    refresh_token: str
    refresh_expires_in: int
    access_expires_in: int
    created_at: float
    uid: str
    umc_access_token: str
    sub: str
    sid: str
    iss: str

    @property
    def refresh_expires_at(self):
        return datetime.datetime.fromtimestamp(self.refresh_expires_in + self.created_at, UTC)

    @property
    def access_expires_at(self):
        return datetime.datetime.fromtimestamp(self.access_expires_in + self.created_at, UTC)

    @classmethod
    def from_token_response(cls, resp, verify_func):
        id_token = resp['id_token']
        verified_id_token = verify_func(id_token)

        return OIDCSession(
            id_token=id_token,
            access_token=resp['access_token'],
            refresh_token=resp['refresh_token'],
            refresh_expires_in=resp['refresh_expires_in'],
            access_expires_in=resp['expires_in'],
            uid=verified_id_token['uid'],
            umc_access_token="",
            created_at=datetime.datetime.now(UTC).timestamp(),
            sub=verified_id_token['sub'],
            sid=verified_id_token['sid'],
            iss=verified_id_token['iss'],
        )

    async def persist(self, session_id, conn: AsyncConnection):
        async with conn.transaction(), conn.cursor() as cur:
            await cur.execute(INSERT_SESSION, {
                'session_id': session_id,
                'id_token': self.id_token,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'refresh_expires_in': self.refresh_expires_in,
                'access_expires_in': self.access_expires_in,
                'uid': self.uid,
                'umc_access_token': self.umc_access_token,
                'sub': self.sub,
                'sid': self.sid,
                'iss': self.iss,
            })

    @classmethod
    async def delete(cls, sessiond_id: str, conn: AsyncConnection):
        async with conn.transaction(), conn.cursor() as cur:
            await cur.execute(DELETE_SESSION_BY_SESSION_ID, (sessiond_id,))

    @classmethod
    async def get_session_by_session_id(cls, session_id: str, conn: AsyncConnection):
        async with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
            res = await cur.execute(SELECT_SESSION_BY_SESSION_ID, (session_id,))
            row = await res.fetchone()

        if row is None:
            return None

        return cls(**row)


CREATE_TABLE = """CREATE TABLE IF NOT EXISTS sessions (
    session_id varchar PRIMARY KEY,
    id_token varchar NOT NULL,
    access_token varchar NOT NULL,
    refresh_token varchar NOT NULL,
    refresh_expires_in integer NOT NULL,
    access_expires_in integer NOT NULL,
    uid varchar NOT NULL,
    umc_access_token varchar NOT NULL,
    sub varchar NOT NULL,
    sid varchar NOT NULL,
    iss varchar NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sessions_iss ON sessions USING hash (iss);
CREATE INDEX IF NOT EXISTS sessions_sub ON sessions USING hash (sub);
CREATE INDEX IF NOT EXISTS sessions_sid ON sessions USING hash (sid);
CREATE INDEX IF NOT EXISTS sessions_session_id ON sessions USING hash (session_id);"""

INSERT_SESSION = """INSERT INTO sessions
    (session_id, id_token, access_token, refresh_token, refresh_expires_in, access_expires_in, uid, umc_access_token, sub, sid, iss)
VALUES
    (%(session_id)s, %(id_token)s, %(access_token)s, %(refresh_token)s, %(refresh_expires_in)s, %(access_expires_in)s, %(uid)s, %(umc_access_token)s, %(sub)s, %(sid)s, %(iss)s)
ON CONFLICT (session_id)
DO UPDATE SET
id_token = %(id_token)s,
access_token = %(access_token)s,
refresh_token = %(refresh_token)s,
refresh_expires_in = %(refresh_expires_in)s,
access_expires_in = %(access_expires_in)s,
uid = %(uid)s,
umc_access_token = %(umc_access_token)s,
sub = %(sub)s,
sid = %(sid)s,
iss = %(iss)s;
"""

SELECT_SESSION_BY_SESSION_ID = """SELECT
    id_token, access_token, refresh_token, refresh_expires_in, access_expires_in,
    uid, umc_access_token, extract(epoch from created_at)::float as created_at, sub, sid, iss
FROM sessions WHERE session_id = %s"""
DELETE_SESSION_BY_SESSION_ID = "DELETE FROM sessions WHERE session_id = %s"
DELETE_SESSIONS_BY_ISS_AND_SUB = "DELETE FROM sessions WHERE sub = %(sub)s AND iss = %(iss)s"
DELETE_SESSIONS_BY_SID = "DELETE FROM sessions WHERE sid = %s"


class OIDCAuthenticator(Authenticator):
    """Authenticate via OpenID Connect"""

    def __init__(self, group_cache):
        oidc_config: dict[str, Any] = config.fetch('oidc')
        self.group_cache = group_cache
        self.pkce_pool = redis.Redis(host='master.ucs.test', port=6379, db=0)
        self.session_pool = AsyncConnectionPool('postgresql://postgres:postgres@master.ucs.test:5433/postgres', open=False)
        self.__pool_opened = False
        self.__init_lock = asyncio.Lock()

        self.http_client = AsyncHTTPClient(force_instance=True)
        with open(oidc_config['openid_configuration']) as f:
            self.openid_configuration = json.loads(f.read())
        self.issuer = self.openid_configuration['issuer']
        self.token_endpoint = self.openid_configuration['token_endpoint']
        self.authorization_endpoint = self.openid_configuration['authorization_endpoint']
        self.session_cookie_name = oidc_config.get('session_cookie_name', 'portal_session_id')
        with open(oidc_config['openid_certs']) as f:
            self.jwks = json.loads(f.read())
        self.client_id = oidc_config['client_id']
        with open(oidc_config['client_secret_file']) as f:
            self.client_secret = f.read()

    def reverse_abs_url(self, request: RequestHandler, name, args=None):
        if args is None:
            args = request.path_args
        return request.request.protocol + "://" + request.request.host + request.reverse_url(name, *args)

    @asynccontextmanager
    async def get_db_connection(self):
        if not self.__pool_opened:
            async with self.__init_lock:
                if not self.__pool_opened:
                    await self.session_pool.open()
                    async with self.session_pool.connection() as conn:
                        await conn.execute(CREATE_TABLE)
                    self.__pool_opened = True

        async with self.session_pool.connection() as conn:
            await conn.set_autocommit(True)
            yield conn

    @property
    def client_basic_auth(self):
        client_id_encoded = quote_plus(self.client_id)
        client_secret_encoded = quote_plus(self.client_secret)

        client_auth = base64.b64encode(f'{client_id_encoded}:{client_secret_encoded}'.encode()).decode('ascii')

        return client_auth

    def get_key_for_token(self, token: str):
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']

        return jwt.PyJWK(next((jwk for jwk in self.jwks['keys'] if jwk['kid'] == kid), None))

    def verify_id_token(self, token: str):
        key = self.get_key_for_token(token)

        return jwt.decode(token, key.key, ['RS256'], {
            'require': ['exp', 'sub', 'iss', 'aud', 'uid'],
            'verify_aud': False,
            'verify_issuer': True,
            'verify_exp': True,
        }, issuer=self.issuer, leeway=20)

    def urlsafe_unpadded_b64encode(self, s):
        return base64.urlsafe_b64encode(s).decode('ascii').rstrip('=')

    def urlsafe_unpadded_b64decode(self, s: str):
        return base64.urlsafe_b64decode(s + '=' * (4 - len(s) % 4))

    def get_auth_mode(self, request):
        return "oidc"
        # return self.auth_mode

    def refresh(self, reason=None):
        return self.group_cache.refresh(reason=reason)

    async def redirect(self, request: RequestHandler):
        scope = "openid email"
        state = secrets.token_urlsafe(32)

        # https://datatracker.ietf.org/doc/html/rfc7636#section-4.1
        code_verifier_bytes = secrets.token_bytes(32)
        code_verifier = self.urlsafe_unpadded_b64encode(code_verifier_bytes)
        code_challenge_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = self.urlsafe_unpadded_b64encode(code_challenge_hash)
        redirect_uri = self.reverse_abs_url(request, 'login')

        query = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }

        redirect_url = urlparse(self.authorization_endpoint)

        auth_request_state = {
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
        }

        await self.pkce_pool.setex(state, timedelta(minutes=5), json.dumps(auth_request_state))
        return redirect_url._replace(query=urlencode(query)).geturl()

    async def oauth2_token_exchange(self, subject_token: str, aud: str):
        # not quite sure how useful this is at this point, since the AZP in the exchanged
        # token is still the Portal OIDC client (https://github.com/keycloak/keycloak/issues/31553, https://github.com/keycloak/keycloak/issues/31546)
        token_exchange_request_body = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": subject_token,
            "requested_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
            "audience": aud,
        }
        token_exchange_request = HTTPRequest(
            self.token_endpoint,
            'POST',
            {'content-type': 'application/x-www-form-urlencoded'},
            urlencode(token_exchange_request_body),
        )

        resp = await self.http_client.fetch(token_exchange_request)
        return json.loads(resp.body)

    async def persist_session(self, session_id: str, session: OIDCSession):
        async with self.get_db_connection() as conn:
            await session.persist(session_id, conn)

    async def login_request(self, request):
        code = request.get_query_argument('code', None)
        state = request.get_query_argument('state', None)
        if code is None or state is None:
            return request.redirect(await self.redirect(request), status=302)

        state_entry = json.loads(await self.pkce_pool.getdel(state))
        token_request_body = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': state_entry['redirect_uri'],
            'code_verifier': state_entry['code_verifier'],
        }

        token_request = HTTPRequest(
            self.token_endpoint,
            'POST',
            {'content-type': 'application/x-www-form-urlencoded', 'authorization': f'Basic {self.client_basic_auth}'},
            urlencode(token_request_body),
        )

        resp = await self.http_client.fetch(token_request)
        resp_body = json.loads(resp.body)

        session = OIDCSession.from_token_response(resp_body, self.verify_id_token)
        # get an UMC token through OIDC token exchange

        token_exchange_body = await self.oauth2_token_exchange(session.access_token, "https://master.ucs.test/univention/oidc/")
        session.umc_access_token = token_exchange_body['access_token']
        session_id = secrets.token_hex(32)

        await self.persist_session(session_id, session)
        request.set_cookie(self.session_cookie_name, session_id, expires=session.refresh_expires_at)

        # TODO: don't hardcode
        return request.redirect(self.reverse_abs_url(request, 'index'), status=302)

    async def login_user(self, request):
        pass

    async def logout_user(self, request):
        if request.request.method == 'GET':
            session_id = request.get_cookie(self.session_cookie_name, None)
            if session_id is None:
                return

            async with self.get_db_connection() as conn:
                await OIDCSession.delete(session_id, conn)

            request.clear_cookie(self.session_cookie_name)
        elif request.request.method == 'POST':
            content_type = request.request.headers['content-type']
            if content_type != "application/x-www-form-urlencoded":
                return
            args = parse_qsl(request.request.body.decode('utf-8'))
            logout_token = next((value for (key, value) in args if key == 'logout_token'), None)
            if logout_token is None:
                return
            key = self.get_key_for_token(logout_token)
            # https://openid.net/specs/openid-connect-backchannel-1_0.html#Validation
            # TODO: validate aud
            get_logger('user').debug('got logout token')
            try:
                token = jwt.decode(logout_token, key.key, ['RS256'], {
                    'require': ['exp', 'iss', 'aud'],
                    'verify_aud': False,
                    'verify_issuer': True,
                    'verify_exp': True,
                }, issuer=self.issuer, leeway=20)
            except jwt.InvalidTokenError as e:
                get_logger('user').warning('logout token failed verification: %s', e)

            if not token.get('sub') and not token.get('sid'):
                get_logger('user').warning('logout token does not container either sub or sid claim')
                return
            if not token['events'] or 'http://schemas.openid.net/event/backchannel-logout' not in token['events']:
                get_logger('user').warning('logout token does not contain an events claim with correct event')
                return
            if token.get('nonce'):
                get_logger('user').warning('logou token does contain a nonce claim')
                return

            iss = token.get('iss')
            sub = token.get('sub')
            sid = token.get('sid')

            async with self.get_db_connection() as conn, conn.transaction(), conn.cursor() as cur:
                if iss and sub:
                    get_logger('user').debug('deleting sessions by iss and sub')
                    await cur.execute(DELETE_SESSIONS_BY_ISS_AND_SUB, {'sub': sub, 'iss': iss})
                if sid:
                    get_logger('user').debug('deleting session by sid')
                    await cur.execute(DELETE_SESSIONS_BY_SID, (sid,))

    async def refresh_session(self, session_id: str, session: OIDCSession):
        refresh_token_request_body = {
            'refresh_token': session.refresh_token,
            'grant_type': "refresh_token",
        }

        refresh_token_request = HTTPRequest(
            self.token_endpoint,
            'POST',
            {'content-type': 'application/x-www-form-urlencoded', 'authorization': f'Basic {self.client_basic_auth}'},
            urlencode(refresh_token_request_body),
        )

        resp = await self.http_client.fetch(refresh_token_request)
        refresh_body = json.loads(resp.body)

        session = OIDCSession.from_token_response(refresh_body, self.verify_id_token)

        token_exchange_body = await self.oauth2_token_exchange(session.access_token, "https://master.ucs.test/univention/oidc/")
        session.umc_access_token = token_exchange_body['access_token']
        await self.persist_session(session_id, session)
        return session

    def must_refresh_session(self, session: OIDCSession):
        now = datetime.datetime.now(UTC)

        return (now + timedelta(seconds=30)) > session.access_expires_at

    async def get_session(self, session_id: str | None):
        if session_id is None:
            return None
        async with self.get_db_connection() as conn:
            session = await OIDCSession.get_session_by_session_id(session_id, conn)

            if session is None:
                return None
            if session.refresh_expires_at < datetime.datetime.now(UTC):
                await OIDCSession.delete(session_id, conn)
                return None

        return session

    async def get_user(self, request):
        session_id = request.get_cookie(self.session_cookie_name, None)
        headers = {}

        session = await self.get_session(session_id)

        display_name = None
        username = None

        if session is not None and self.must_refresh_session(session):
            print("refreshing session")
            session = await self.refresh_session(session_id, session)

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
