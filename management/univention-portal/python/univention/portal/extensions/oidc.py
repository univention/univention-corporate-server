#!/usr/bin/python3
#
# Univention Management Console
#  OpenID Connect implementation for the Portal
#
# Copyright 2024 Univention GmbH
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

# import base64
import binascii
# import hashlib
import json
# import os
import uuid
from urllib.parse import urlencode, urlparse, urlunsplit

import jwt
from jwt.algorithms import RSAAlgorithm
from tornado import escape
from tornado.auth import OAuth2Mixin
from tornado.httpclient import HTTPClientError
from tornado.web import HTTPError

from univention.portal import config
from univention.portal.handlers.portal_resource import PortalResource
from univention.portal.log import get_logger


shared_memory = {}


class OIDCResource(OAuth2Mixin, PortalResource):
    """Base class for all OIDC resources."""

    @property
    def access_token(self):
        return self.get_secure_cookie(self.access_token_cookie_name)

    @property
    def id_token(self):
        return self.get_secure_cookie(self.id_token_cookie_name)

    def get_current_user(self):
        try:
            return self.verify_id_token(self.id_token, None)
        except Exception:
            pass

    async def prepare(self):
        super(OIDCResource, self).prepare()
        self._ = self.locale.translate
        settings = self.settings['oidc']
        self.client_id = settings['client_id']
        self.issuer = settings['issuer']
        self.JWKS = settings["jwks"]
        self.client_secret = settings['client_secret']
        self._OAUTH_AUTHORIZE_URL = settings["op"]["authorization_endpoint"]
        self._OAUTH_ACCESS_TOKEN_URL = settings["op"]["token_endpoint"]
        self._OAUTH_END_SESSION_URL = settings["op"]["end_session_endpoint"]
        self._OAUTH_USERINFO_URL = settings["op"]["userinfo_endpoint"]
        self._OAUTH_CERT_URL = settings["op"]["jwks_uri"]
        self.id_token_signing_alg_values_supported = settings["op"]["id_token_signing_alg_values_supported"]
        self.extra_parameters = [x.strip() for x in settings.get('extra_parameters', '').split(',') if x.strip()]
        self.access_token_cookie_name = settings.get('access-token-cookie-name', 'portal-access-token')
        self.id_token_cookie_name = settings.get('id-token-cookie-name', 'portal-id-token')
        self.state_cookie_name = settings.get('state-cookie-name', 'portal-state')

    async def authenticate(self, code, code_verifier, nonce):
        get_logger("oidc").debug('OIDC authenticate')
        try:
            response = await self.get_access_token(
                redirect_uri=self.reverse_abs_url('login'),
                code=code,
                code_verifier=code_verifier,
            )
        except HTTPClientError as exc:
            get_logger("oidc").error('Could not get access token: %s' % (exc.response.body,))
            raise HTTPError(502, self._('Could not receive token from authorization server.'))

        try:
            id_token = response['id_token']
            access_token = response['access_token']
            refresh_token = response['refresh_token']
        except KeyError:
            raise HTTPError(502, self._("Authorization server response did not contain token."))

        # TODO: configure in keycloak
        # access_token = self._get_exchanged_access_token(access_token)

        get_logger("oidc").log(9, 'Access token: %s' % (access_token,))
        get_logger("oidc").log(9, 'ID token: %s' % (id_token,))
        get_logger("oidc").log(9, 'Refresh token: %s' % (refresh_token,))
        self.verify_id_token(id_token, nonce)

        self.set_secure_cookie(self.access_token_cookie_name, access_token)
        self.set_secure_cookie(self.id_token_cookie_name, id_token)

    def verify_id_token(self, token, nonce):
        claims = self._verify_jwt(id_token=token)
        if nonce and claims.get('nonce') != nonce:
            raise HTTPError(401, 'The nonce is not matching.')
        return claims

    def verify_access_token(self, token):
        return self._verify_jwt(access_token=token)

    def verify_logout_token(self, token):
        claims = self._verify_jwt(logout_token=token)

        # TODO: verify contents of sub or/and sid, events
        if not (claims.get('sub') or claims['sid']):
            raise HTTPError(401, self._('The logout token is missing a sub or sid claim'))
        if not claims.get('events'):
            raise HTTPError(401, self._('The logout token is missing a events claim'))
        if claims.get('nounce'):
            raise HTTPError(401, self._('The logout token must not have a nounce claim'))

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
                leeway=config.fetch('oidc-grace-time', 3),  # seconds
            )
        except jwt.ExpiredSignatureError:
            get_logger("oidc").warn("Signature expired")
            raise HTTPError(401, self._("The Token signature is expired."))
        except jwt.InvalidSignatureError as exc:
            get_logger("oidc").error("Invalid signature: %s" % (exc,))
            raise HTTPError(401, self._('The Token contains an invalid signature: %s') % (exc,))
        except jwt.InvalidIssuerError as exc:
            get_logger("oidc").warn("Invalid issuer: %s" % (exc,))
            raise HTTPError(401, self._('The Token contains an invalid issuer: %s') % (exc,))
        except jwt.InvalidAudienceError as exc:
            get_logger("oidc").warn("Invalid signature: %s" % (exc,))
            raise HTTPError(401, self._('The Token contains an invalid audience: %s') % (exc,))
        except jwt.MissingRequiredClaimError as exc:
            get_logger("oidc").warn("Missing claim: %s" % (exc,))
            raise HTTPError(401, self._('The Token is missing a required claim: %s') % (exc,))
        except jwt.ImmatureSignatureError as exc:
            get_logger("oidc").warn("Immature signature: %s" % (exc,))
            raise HTTPError(401, self._('The Token contains an immature signature: %s') % (exc,))

        get_logger("oidc").debug('OIDC JWK-Payload: %r' % (claims,))
        return claims

    def _get_public_key(self, token):
        kid = jwt.get_unverified_header(token)['kid']
        for key in self.JWKS['keys']:
            if key['kid'] == kid:
                return RSAAlgorithm.from_jwk(json.dumps(key))  # FIXME: could also be != RSA

    async def get_access_token(self, redirect_uri, code, code_verifier):
        # return await self._get_access_token(redirect_uri, {"code": code, "grant_type": "authorization_code", "code_verifier": code_verifier})
        return await self._get_access_token(redirect_uri, {"code": code, "grant_type": "authorization_code"})

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

    async def _get_exchanged_access_token(self, access_token):
        http_client = self.get_auth_http_client()
        body = urlencode({
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'subject_token': access_token,
            'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token',
            'audience': config.fetch('oidc-umc-relying-party'),
            # 'requested_subject': '', no impersonation, same user!
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
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
        get_logger("oidc").debug('Refreshing OIDC session')
        try:
            response = await self.get_new_access_token(
                redirect_uri=self.reverse_abs_url('oidc-login', ()),
                refresh_token=user.oidc.refresh_token,
            )
        except HTTPClientError as exc:
            get_logger("oidc").error('Could not get new access token: %s' % (exc.response.body,))
            raise HTTPError(502, self._('Could not receive token from authorization server.'))

        try:
            id_token = response['id_token']
            access_token = response['access_token']
            # refresh_token = response['refresh_token']
        except KeyError:
            raise HTTPError(502, self._("Authorization server response did not contain token."))

        self.set_secure_cookie(self.access_token_cookie_name, access_token)
        self.set_secure_cookie(self.id_token_cookie_name, id_token)

        # TODO: do we need to re-authenticate?
        self.verify_id_token(id_token, None)

    def _logout_success(self):
        self.clear_cookie(self.access_token_cookie_name)
        self.clear_cookie(self.id_token_cookie_name)


class OIDCLogin(OIDCResource):
    """User initiated login at the OP using Authentication Code Flow."""

    async def get(self):
        code = self.get_argument('code', False)
        if not code:
            await self.do_single_sign_on(
                self.get_query_argument('target_link_uri', self.reverse_abs_url('login')),
                self.get_query_argument('login_hint', None),
            )
            return

        state = shared_memory.pop(self.get_query_argument('state', ''), {})
        await self.authenticate(code, state.get('code_verifier'), state.get('nonce'))

        # protect against javascript:alert('XSS'), mailto:foo and other non relative links!
        target_link_uri = urlparse(state.get('target_link_uri', ''))
        if target_link_uri.path.startswith('//'):
            target_link_uri = urlparse('')
        target_link_uri = urlunsplit(('', '', target_link_uri.path, target_link_uri.query, target_link_uri.fragment))
        self.redirect(target_link_uri or self.reverse_abs_url('index'), status=303)

    async def post(self):
        return await self.get()

    async def do_single_sign_on(self, target_link_uri, login_hint):
        get_logger("oidc").debug('OIDC single sign on')
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

        code_verifier = None
        # code_verifier = base64.urlsafe_b64encode(os.urandom(43)).decode('ASCII').rstrip('=')
        # code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('ASCII').rstrip('=')

        shared_memory[state] = {'iss': self.issuer, 'target_link_uri': target_link_uri, 'code_verifier': code_verifier, 'nonce': nonce}
        # extra_parameters['code_challenge'] = code_challenge
        # extra_parameters['code_challenge_method'] = 'S256'

        self.authorize_redirect(
            redirect_uri=self.reverse_abs_url('login'),
            client_id=self.client_id,
            scope=['openid'],
            response_type='code',
            extra_params=extra_parameters,
        )


class OIDCLogout(OIDCResource):
    """User initiated logout at the OP"""

    def get(self):
        """User initiated front channel logout at OP."""
        user = self.current_user

        if not user:
            return self._logout_success()

        logout_url = '%s?%s' % (self._OAUTH_END_SESSION_URL, urlencode({
            'post_logout_redirect_uri': self.reverse_abs_url('oidc-logout-done'),
            'client_id': self.client_id,
            # 'logout_hint': None,
            # 'ui_locales': None,
        }))
        self.redirect(logout_url)

    async def post(self):
        """User initiated back channel logout at OP."""
        get_logger("oidc").debug('backchannel logout')
        user = self.current_user
        id_token = self.id_token

        if not user or not id_token:
            return self._logout_success()

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


class OIDCFrontchannelLogout(OIDCResource):
    """OP initiated frontchannel logout at this RP."""

    def get(self):
        get_logger("oidc").debug('frontchannel OP logout')
        self.add_header('Cache-Control', 'no-store')
        # self.get_query_argument('iss')
        # sid = self.get_query_argument('sid')
        return self._logout_success()
