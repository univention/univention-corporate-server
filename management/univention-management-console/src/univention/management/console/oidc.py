#!/usr/bin/python3
#
# Univention Management Console
#  OpenID Connect implementation for the UMC
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
import binascii
import hashlib
import json
import os
import time
import uuid
from time import monotonic
from urllib.parse import urlencode, urlparse, urlunsplit

import jwt
from jwt.algorithms import RSAAlgorithm
from tornado import escape
from tornado.auth import OAuth2Mixin
from tornado.httpclient import HTTPClientError, HTTPRequest

import univention.debug as ud
from univention.management.console.config import ucr
from univention.management.console.error import BadRequest, NotFound, OpenIDProvideUnavailable, UMC_Error, Unauthorized
from univention.management.console.log import CORE
from univention.management.console.resource import Resource
from univention.management.console.session import Session
from univention.management.console.shared_memory import shared_memory


class OIDCUser(object):
    """OIDC tokens of the authenticated user."""

    __slots__ = ('id_token', 'access_token', 'refresh_token', 'claims', 'username', 'session_refresh_future')

    def __init__(self, id_token, access_token, refresh_token, claims):
        self.id_token = id_token
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.claims = claims
        self.username = claims['uid']
        self.session_refresh_future = None

    @property
    def session_end_time(self):
        exp = jwt.decode(self.refresh_token, verify=False)['exp'] if self.refresh_token else claims['exp']
        return int(monotonic() + (exp - time.time()))

    @property
    def token_end_time(self):
        return int(monotonic() + (self.claims['exp'] - time.time()))


class OIDCResource(OAuth2Mixin, Resource):
    """Base class for all OIDC resources."""

    requires_authentication = False

    async def prepare(self):
        await super(OIDCResource, self).prepare()
        state = shared_memory.pkce.get(self.get_query_argument('state', ''), {})
        self.set_settings(state.get('iss', self.get_query_argument('iss', self.application.settings['default_authorization_server'])))

    def get_openid_provider(self, issuer):
        for openid_provider in self.application.settings['oidc'].values():
            if openid_provider['issuer'] == issuer:
                return openid_provider
        raise KeyError(issuer)

    def set_settings(self, issuer):
        try:
            settings = self.get_openid_provider(issuer)
        except KeyError:
            raise NotFound(self._('The OpenID Provider is not available. This might be a misconfiguration.'))

        self.client_id = settings['client_id']
        self.issuer = settings['issuer']
        with open(settings['openid_configuration']) as fd:  # noqa: ASYNC101
            settings["op"] = json.loads(fd.read())
        with open(settings['openid_certs']) as fd:  # noqa: ASYNC101
            settings["jwks"] = json.loads(fd.read())
            self.JWKS = settings["jwks"]
        with open(settings['client_secret_file']) as fd:  # noqa: ASYNC101
            self.client_secret = fd.read().strip()
        self._OAUTH_AUTHORIZE_URL = settings["op"]["authorization_endpoint"]
        self._OAUTH_ACCESS_TOKEN_URL = settings["op"]["token_endpoint"]
        self._OAUTH_END_SESSION_URL = settings["op"]["end_session_endpoint"]
        self._OAUTH_USERINFO_URL = settings["op"]["userinfo_endpoint"]
        self._OAUTH_CERT_URL = settings["op"]["jwks_uri"]
        self.id_token_signing_alg_values_supported = settings["op"]["id_token_signing_alg_values_supported"]
        self.extra_parameters = [x.strip() for x in settings.get('extra_parameters', '').split(',') if x.strip()]

    async def bearer_authorization(self, bearer_token):
        if self.current_user and self.current_user.user.authenticated and self.current_user.oidc.access_token == bearer_token:
            return

        try:
            claims = self.verify_access_token(bearer_token)
        except Unauthorized as exc:
            self.add_header('WWW-Authenticate', 'Bearer realm="Univention Management Console" scope="openid" error="invalid_token" error_description="%s"' % (exc,))
            raise

        # FIXME: Access Denied from Keycloak: https://github.com/keycloak/keycloak/issues/16844 because we don't have a "openid" scope
        # await self.get_user_information(bearer_token)

        oidc = OIDCUser(None, bearer_token, None, claims)
        await self.pam_oidc_authentication(oidc)

    async def authenticate(self, code, code_verifier, nonce):
        CORE.debug('OIDC authenticate')
        try:
            response = await self.get_access_token(
                redirect_uri=self.reverse_abs_url('oidc-login'),
                code=code,
                code_verifier=code_verifier,
            )
        except HTTPClientError as exc:
            CORE.error('Could not get access token: %s' % (exc.response.body,))
            raise OpenIDProvideUnavailable(self._('Could not receive token from authorization server.'))

        try:
            id_token = response['id_token']
            access_token = response['access_token']
            refresh_token = response['refresh_token']
        except KeyError:
            raise OpenIDProvideUnavailable(self._("Authorization server response did not contain token."))

        ud.debug(ud.MAIN, 99, 'Access token: %s' % (access_token,))
        ud.debug(ud.MAIN, 99, 'ID token: %s' % (id_token,))
        ud.debug(ud.MAIN, 99, 'Refresh token: %s' % (refresh_token,))
        claims = self.verify_id_token(id_token, nonce)
        oidc = OIDCUser(id_token, access_token, refresh_token, claims)
        await self.pam_oidc_authentication(oidc)

    async def pam_oidc_authentication(self, oidc):
        # important: must be called before the auth, to preserve session id in case of re-auth and that a user cannot choose his own session ID by providing a cookie
        sessionid = self.create_sessionid()

        # TODO: drop in the future to gain performance
        result = await self.current_user.authenticate({
            'locale': self.locale.code,
            'username': oidc.username,
            'password': oidc.access_token,
            'auth_type': 'OIDC',
        })
        if not self.current_user.user.authenticated:
            CORE.error('SECURITY WARNING: PAM OIDC Authentication failed while JWT verification succeeded!')
            raise UMC_Error(result.message, result.status, result.result)

        # as an alternative to PAM we could just set the user as authenticated because jwt.decode() already ensured this.
        # but we keep the behavior for now because this is what happened prior to the UMC-Web-Server and UMC-Sever unification
        # PAM also makes acct_mgmt. This is of course also done by the OP but nevertheless we don't know if this is still required.
        # self.current_user.set_credentials(oidc.username, oidc.access_token, 'OIDC')
        self.current_user.oidc = oidc
        self.set_session(sessionid)

    def verify_id_token(self, token, nonce):
        claims = self._verify_jwt(id_token=token)
        if nonce and claims.get('nonce') != nonce:
            raise Unauthorized('The nonce is not matching.')
        return claims

    def verify_access_token(self, token):
        return self._verify_jwt(access_token=token)

    def verify_logout_token(self, token):
        claims = self._verify_jwt(logout_token=token)

        # TODO: verify contents of sub or/and sid, events
        if not (claims.get('sub') or claims['sid']):
            raise Unauthorized(self._('The logout token is missing a sub or sid claim'))
        if not claims.get('events'):
            raise Unauthorized(self._('The logout token is missing a events claim'))
        if claims.get('nounce'):
            raise Unauthorized(self._('The logout token must not have a nounce claim'))

        return claims

    def _verify_jwt(self, id_token=None, access_token=None, logout_token=None):
        if len(list(filter(None, [id_token, access_token, logout_token]))) != 1:
            raise TypeError()
        if id_token:
            token = id_token
            audience = self.client_id
            options = {
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
            }
        elif access_token:
            token = access_token
            audience = None
            options = {
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': False,
                'verify_iss': True,
            }
            # TODO: verify azp
        elif logout_token:
            token = logout_token
            audience = self.client_id
            options = {
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': False,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
            }
        try:
            claims = jwt.decode(
                token, self._get_public_key(token),
                algorithms=self.id_token_signing_alg_values_supported,
                options=options,
                issuer=self.issuer,
                audience=audience,
                leeway=ucr.get_int('umc/oidc/grace-time', 3),  # seconds
            )
        except jwt.ExpiredSignatureError:
            CORE.warn("Signature expired")
            raise Unauthorized(self._("The Token signature is expired."))
        except jwt.InvalidSignatureError as exc:
            CORE.error("Invalid signature: %s" % (exc,))
            raise Unauthorized(self._('The Token contains an invalid signature: %s') % (exc,))
        except jwt.InvalidIssuerError as exc:
            CORE.warn("Invalid issuer: %s" % (exc,))
            raise Unauthorized(self._('The Token contains an invalid issuer: %s') % (exc,))
        except jwt.InvalidAudienceError as exc:
            CORE.warn("Invalid signature: %s" % (exc,))
            raise Unauthorized(self._('The Token contains an invalid audience: %s') % (exc,))
        except jwt.MissingRequiredClaimError as exc:
            CORE.warn("Missing claim: %s" % (exc,))
            raise Unauthorized(self._('The Token is missing a required claim: %s') % (exc,))
        except jwt.ImmatureSignatureError as exc:
            CORE.warn("Immature signature: %s" % (exc,))
            raise Unauthorized(self._('The Token contains an immature signature: %s') % (exc,))

        CORE.debug('OIDC JWK-Payload: %r' % (claims,))
        return claims

    def _get_public_key(self, token):
        kid = jwt.get_unverified_header(token)['kid']
        for key in self.JWKS['keys']:
            if key['kid'] == kid:
                return RSAAlgorithm.from_jwk(json.dumps(key))

    async def get_user_information(self, bearer_token):
        user_info_req = HTTPRequest(
            self._OAUTH_USERINFO_URL,
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer %s" % (bearer_token,),
            },
        )
        http_client = self.get_auth_http_client()
        try:
            user_info_res = await http_client.fetch(user_info_req)
        except HTTPClientError as exc:
            CORE.warn("Fetching user info failed: %s %s" % (user_info_req.url, exc))
            raise OpenIDProvideUnavailable(self._("Could not receive user information from OP."))

        user_info = json.loads(user_info_res.body.decode('utf-8'))
        CORE.debug('OIDC User-Info: %r' % (user_info,))
        return user_info

    async def download_jwks(self):
        request = HTTPRequest(self._OAUTH_CERT_URL, method='GET')
        http_client = self.get_auth_http_client()

        try:
            response = await http_client.fetch(request, raise_error=False)
        except HTTPClientError as exc:
            CORE.warn("Fetching certificate failed: %s %s" % (request.url, exc))
            raise OpenIDProvideUnavailable(self._("Could not receive certificate from OP."))

        if response.code != 200:
            CORE.warn("Fetching certificate failed")
            raise OpenIDProvideUnavailable(self._("Could not receive certificate from OP."))
        return json.loads(response.body.decode('utf-8'))

    async def get_access_token(self, redirect_uri, code, code_verifier):
        return await self._get_access_token(redirect_uri, {"code": code, "grant_type": "authorization_code", "code_verifier": code_verifier})

    async def get_new_access_token(self, redirect_uri, refresh_token):
        return await self._get_access_token(redirect_uri, {"refresh_token": refresh_token, "grant_type": "refresh_token"})

    async def _get_access_token(self, redirect_uri, data):
        http_client = self.get_auth_http_client()
        body = urlencode(dict(
            data,
            redirect_uri=redirect_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
        ))  # TODO: request specific AUD for ldap server
        try:
            response = await http_client.fetch(
                self._OAUTH_ACCESS_TOKEN_URL,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=body,
            )
        except HTTPClientError:
            raise  # handled in get()
        return escape.json_decode(response.body)

    async def refresh_session_tokens(self, user):
        """Refresh the tokens using the refresh token."""
        CORE.debug('Refreshing OIDC session')
        try:
            response = await self.get_new_access_token(
                redirect_uri=self.reverse_abs_url('oidc-login', ()),
                refresh_token=user.oidc.refresh_token,
            )
        except HTTPClientError as exc:
            CORE.error('Could not get new access token: %s' % (exc.response.body,))
            raise OpenIDProvideUnavailable(self._('Could not receive token from authorization server.'))

        try:
            id_token = response['id_token']
            access_token = response['access_token']
            refresh_token = response['refresh_token']
        except KeyError:
            raise OpenIDProvideUnavailable(self._("Authorization server response did not contain token."))

        user.oidc.id_token = id_token
        user.oidc.access_token = access_token
        user.oidc.refresh_token = refresh_token

        # TODO: do we need to re-authenticate?
        claims = self.verify_id_token(id_token, None)
        oidc = OIDCUser(id_token, access_token, refresh_token, claims)
        await self.pam_oidc_authentication(oidc)

    def _logout_success(self):
        user = self.current_user
        if user:
            user.oidc = None
        self.redirect('/univention/logout', status=303)


class OIDCLogin(OIDCResource):
    """User initiated login at the OP using Authentication Code Flow."""

    async def get(self):
        code = self.get_argument('code', False)
        if not code:
            await self.do_single_sign_on(
                self.get_query_argument('target_link_uri', self.get_query_argument('location', '/univention/management/')),
                self.get_query_argument('login_hint', None),
            )
            return

        state = shared_memory.pkce.pop(self.get_query_argument('state', ''), {})
        await self.authenticate(code, state.get('code_verifier'), state.get('nonce'))

        # protect against javascript:alert('XSS'), mailto:foo and other non relative links!
        location = urlparse(state.get('location', ''))
        if location.path.startswith('//'):
            location = urlparse('')
        location = urlunsplit(('', '', location.path, location.query, location.fragment))
        self.redirect(location or self.reverse_abs_url('index'), status=303)

    async def post(self):
        return await self.get()

    async def do_single_sign_on(self, location, login_hint):
        CORE.debug('OIDC single sign on')
        # TODO: The Client MUST understand the login_hint and iss parameters and SHOULD support the target_link_uri parameter.
        extra_parameters = {'approval_prompt': 'auto'}
        for extra_parameter in self.extra_parameters:
            value = self.get_query_argument(extra_parameter, None)
            if value:
                extra_parameters[extra_parameter] = value
        state = str(uuid.uuid4())
        nonce = binascii.b2a_hex(uuid.uuid4().bytes).decode('ASCII')
        extra_parameters['state'] = state
        extra_parameters['nonce'] = nonce
        extra_parameters['display'] = 'page'
        # extra_parameters['prompt'] = 'login'  # 'content'
        # extra_parameters['max_age'] = ''
        extra_parameters['ui_locales'] = self.locale.code
        if login_hint:
            extra_parameters['login_hint'] = login_hint

        code_verifier = base64.urlsafe_b64encode(os.urandom(43)).decode('ASCII').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('ASCII').rstrip('=')

        shared_memory.pkce[state] = {'iss': self.issuer, 'location': location, 'code_verifier': code_verifier, 'nonce': nonce}
        extra_parameters['code_challenge'] = code_challenge
        extra_parameters['code_challenge_method'] = 'S256'

        self.authorize_redirect(
            redirect_uri=self.reverse_abs_url('oidc-login'),
            client_id=self.client_id,
            scope=['openid'],
            response_type='code',
            extra_params=extra_parameters,
        )


class _OIDCLogoutBase(OIDCResource):

    def _logout_success(self):
        user = self.current_user
        if user:
            user.oidc = None
        self.redirect('/univention/logout', status=303)


class OIDCLogout(_OIDCLogoutBase):
    """User initiated logout at the OP"""

    def get(self):
        """User initiated front channel logout at OP."""
        CORE.debug('frontchannel logout')
        user = self.current_user

        if user is None or user.oidc is None:
            return self._logout_success()

        access_token = user.oidc.access_token
        if not access_token:
            raise BadRequest(self._("Not logged in"))

        logout_url = '%s?%s' % (self._OAUTH_END_SESSION_URL, urlencode({
            'post_logout_redirect_uri': self.reverse_abs_url('oidc-logout-done'),
            'client_id': self.client_id,
            # 'logout_hint': None,
            # 'ui_locales': None,
        }))
        self.redirect(logout_url)

    async def post(self):
        """User initiated back channel logout at OP."""
        CORE.debug('backchannel logout')
        user = self.current_user

        if user is None or user.oidc is None:
            return self._logout_success()

        id_token = user.oidc.id_token
        if not id_token:
            raise BadRequest(self._("Not logged in"))

        http_client = self.get_auth_http_client()
        try:
            await http_client.fetch(
                self._OAUTH_END_SESSION_URL,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=urlencode({
                    'id_token_hint': id_token,
                    'client_id': self.client_id,
                    # 'logout_hint': None,
                    # 'ui_locales': None,
                }),
            )
            # escape.json_decode(response.body)
        except HTTPClientError:
            raise  # FIXME:

        return self._logout_success()


class OIDCLogoutFinished(_OIDCLogoutBase):

    def get(self):
        self._logout_success()


class OIDCFrontchannelLogout(_OIDCLogoutBase):
    """OP initiated frontchannel logout at this RP."""

    def get(self):
        CORE.debug('frontchannel OP logout')
        self.add_header('Cache-Control', 'no-store')
        # self.get_query_argument('iss')
        # sid = self.get_query_argument('sid')
        return self._logout_success()


class OIDCBackchannelLogout(OIDCResource):
    """OP initiated backchannel logout at this RP."""

    def post(self):
        CORE.debug('backchannel OP logout')
        logout_token = self.get_argument('logout_token')
        self.add_header('Cache-Control', 'no-store')
        try:
            claims = self.verify_logout_token(logout_token)
        except Unauthorized as exc:
            self.add_header('Content-Type', 'application/json')
            self.set_status(400)
            self.finish({'error': 'invalid_request', 'error_description': str(exc)})
            return

        sessions = [user for user in Session.sessions.values() if user and user.oidc and user.oidc.id_token and claims['iss'] == user.oidc.claims['iss']]
        for user in sessions:
            if user.oidc.claims['sid'] == claims.get('sid'):
                user.logout()
                break
        else:
            for user in sessions:
                if user.oidc.claims['sub'] == claims.get('sub'):
                    user.logout()

        self.finish()


class OIDCMetadata(OIDCResource):
    """A client metadata document suitable for dynamic client registration."""

    def get(self):
        if ucr.get('umc/oidc/rp/server'):
            fqdn = ucr['umc/oidc/rp/server']
            addresses = [fqdn]
        else:
            from univention.config_registry.interfaces import Interfaces
            i = Interfaces()
            fqdn = '%(hostname)s.%(domainname)s' % ucr
            addresses = [fqdn]
            addresses.extend([y['address'] for x, y in i.all_interfaces if y and y.get('address')])

        bases = ['%s://%s/univention/oidc/' % (scheme, addr) for addr in addresses for scheme in ('https', 'http')]
        result = {
            'redirect_uris': bases,
            'response_types': ['code'],
            'grant_types': ['authorization_code', 'refresh_token'],
            'application_type': 'web',
            'contacts': [ucr.get('umc/oidc/contact-person/mail', '')],
            'client_name': 'Univention Management Console',
            'logo_uri': f'https://{fqdn}/favicon.ico',
            'client_uri': f'https://{fqdn}/univention/management/',
            'policy_uri': f'https://{fqdn}/univention/impress.html',
            'tos_uri': f'https://{fqdn}/univention/tos.html',
            # 'jwks_uri': f'https://{fqdn}/univention/oidc/jwks.json',
            # 'jwks': None,
            # 'sector_identifier_uri': None,
            'subject_type': 'pairwise',
            # 'id_token_signed_response_alg'
            # 'id_token_encrypted_response_alg'
            # 'id_token_encrypted_response_enc'
            # 'userinfo_signed_response_alg'
            # 'userinfo_encrypted_response_alg'
            # 'userinfo_encrypted_response_enc'
            # 'request_object_signing_alg'
            # 'request_object_encryption_alg'
            # 'request_object_encryption_enc'
            'token_endpoint_auth_method': 'client_secret_basic',
            # 'token_endpoint_auth_signing_alg':
            'default_max_age': 1800,
            'require_auth_time': False,
            # 'default_acr_values': None,
            'initiate_login_uri': self.reverse_abs_url('oidc-login'),
            'request_uris': [],
            'post_logout_redirect_uris': [base + '*' for base in bases],
            'backchannel_logout_session_required': True,
            'backchannel_logout_uri': self.reverse_abs_url('backchannel-logout'),
            'frontchannel_logout_session_required': True,
            'frontchannel_logout_uri': self.reverse_abs_url('frontchannel-logout'),
        }
        self.content_negotiation(result, wrap=False)


if __name__ == '__main__':
    import sys
    with open('/usr/share/univention-management-console/oidc/oidc.json') as fd:
        oidc = next(iter(json.load(fd)['oidc'].values()))
    with open(oidc['openid_configuration']) as fd:
        op = json.load(fd)
    with open(oidc['openid_certs']) as fd:
        jwks = json.load(fd)
    public_key = RSAAlgorithm.from_jwk(json.dumps(jwks['keys'][0]))
    token = sys.stdin.read().strip()
    claims_decoded = None
    print(jwt.get_unverified_header(token), file=sys.stderr)
    for verify, leeway in ((False, 60 * 60 * 24), (True, 0)):
        try:
            claims = jwt.decode(
                token, public_key,
                algorithms=op['id_token_signing_alg_values_supported'],
                options={
                    'verify_signature': False,
                    'verify_exp': False,
                    'verify_nbf': False,
                    'verify_iat': False,
                    'verify_aud': False,
                    'verify_iss': False,

                },
                issuer=op['issuer'],
                audience=oidc['client_id'],
                leeway=60 * 60 * 24,
            )
            claims_decoded = claims
        except jwt.exceptions.PyJWTError as exc:
            print(exc, file=sys.stderr)
    print(json.dumps(claims_decoded))
