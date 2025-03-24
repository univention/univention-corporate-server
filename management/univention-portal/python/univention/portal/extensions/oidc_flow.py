import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from urllib.parse import quote_plus, urlencode, urlparse

import jwt
from python.univention.portal.log import get_logger
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


@dataclass(frozen=True)
class AuthorizationRequest:
    authorization_url: str
    code_verifier: str
    state: str


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    refresh_token: str
    id_token: str
    refresh_expires_in: int
    expires_in: int


class OIDCFlow:
    def __init__(self, oidc_configuration, oidc_certs, client_id, client_secret) -> None:
        self.oidc_configuration = oidc_configuration
        self.oidc_certs = oidc_certs
        self.client_id = client_id
        self.client_secret = client_secret

        self.issuer = self.openid_configuration['issuer']
        self.token_endpoint = self.openid_configuration['token_endpoint']
        self.authorization_endpoint = self.openid_configuration['authorization_endpoint']
        self.end_session_endpoint = self.openid_configuration['end_session_endpoint']

        self.jwks = json.loads(oidc_certs)

        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.http_client = AsyncHTTPClient(force_instance=True, defaults={'connect_timeout': 20, 'request_timeout': 60})

    @property
    def client_basic_auth(self):
        client_id_encoded = quote_plus(self.client_id)
        client_secret_encoded = quote_plus(self.client_secret)

        client_auth = base64.b64encode(f'{client_id_encoded}:{client_secret_encoded}'.encode()).decode('ascii')

        return client_auth

    def _urlsafe_unpadded_b64encode(self, data: bytes) -> str:
        import base64
        encoded = base64.urlsafe_b64encode(data)
        return encoded.decode('ascii').rstrip('=')

    def generate_authorization_request(self, redirect_uri: str) -> AuthorizationRequest:
        scope = "openid email"
        state = secrets.token_urlsafe(32)

        # https://datatracker.ietf.org/doc/html/rfc7636#section-4.1
        code_verifier_bytes = secrets.token_bytes(32)
        code_verifier = self.urlsafe_unpadded_b64encode(code_verifier_bytes)
        code_challenge_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = self.urlsafe_unpadded_b64encode(code_challenge_hash)

        query = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }

        redirect_url = urlparse(self.authorization_endpoint)._replace(query=urlencode(query)).geturl()

        return AuthorizationRequest(redirect_url, code_verifier, state)

    async def exchange_code_for_tokens(self, code, redirect_uri, code_verifier) -> TokenResponse:
        token_request_body = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
        }

        token_request = HTTPRequest(
            self.token_endpoint,
            'POST',
            {'content-type': 'application/x-www-form-urlencoded', 'authorization': f'Basic {self.client_basic_auth}'},
            urlencode(token_request_body),
        )

        resp = await self.http_client.fetch(token_request)
        return TokenResponse(**json.loads(resp.body))

    async def token_exchange(self, subject_token: str, aud: str) -> TokenResponse:
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
        return TokenResponse(**json.loads(resp.body))

    def generate_logout_url(self, post_logout_redirect_url: str, id_token: str):
        url = urlparse(self.end_session_endpoint)
        params = {
            'id_token_hint': id_token,
            'client_id': self.client_id,
            'post_logout_redirect_uri': post_logout_redirect_url,
        }

        return url._replace(query=urlencode(params)).geturl()

    async def refresh_tokens(self, refresh_token) -> TokenResponse:
        refresh_token_request_body = {
            'refresh_token': refresh_token,
            'grant_type': "refresh_token",
        }

        refresh_token_request = HTTPRequest(
            self.token_endpoint,
            'POST',
            {'content-type': 'application/x-www-form-urlencoded', 'authorization': f'Basic {self.client_basic_auth}'},
            urlencode(refresh_token_request_body),
        )

        resp = await self.http_client.fetch(refresh_token_request)
        return TokenResponse(**json.loads(resp.body))

    def verify_id_token(self, token: str):
        key = self.get_key_for_token(token)

        return jwt.decode(token, key.key, ['RS256'], {
            'require': ['exp', 'sub', 'iss', 'aud', 'uid'],
            'verify_aud': False,
            'verify_issuer': True,
            'verify_exp': True,
        }, issuer=self.issuer, leeway=20)

    def get_key_for_token(self, token: str):
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']

        return jwt.PyJWK(next((jwk for jwk in self.jwks['keys'] if jwk['kid'] == kid), None))

    def verify_logout_token(self, logout_token: str):
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

        return token
