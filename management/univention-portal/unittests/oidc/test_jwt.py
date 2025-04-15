import datetime
import json
import secrets
from typing import Any

import jwt
import pytest

from univention.portal.extensions.oidc.auth import OIDCAuth, OIDCAuthError


EXAMPLE_ISSUER = "https://idp.example.com/"

DEFAULT_KEY = ('rsa.priv.json', 'RS256')


@pytest.fixture(scope='module')
def oidc_auth():
    oidc_well_known = {
        "issuer": EXAMPLE_ISSUER,
        "token_endpoint": EXAMPLE_ISSUER + 'token',
        "authorization_endpoint": EXAMPLE_ISSUER + 'auth',
        "end_session_endpoint": EXAMPLE_ISSUER + 'logout',
        "id_token_signing_alg_values_supported": ['RS256', 'ES256'],
    }
    with open('jwks.json') as f:
        jwks = json.loads(f.read())
    return OIDCAuth(oidc_well_known, jwks, "example.com", "abc123")


@pytest.fixture()
def default_payload():
    return {
        "iss": EXAMPLE_ISSUER,
        "aud": "test",
        "sub": "test",
        "uid": "test",
        "exp": int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.datetime.now(datetime.UTC).timestamp()),
    }


@pytest.fixture()
def default_logout_payload(default_payload):
    logut_payload = {
        "jti": secrets.token_hex(64),
        "events": {
            "http://schemas.openid.net/event/backchannel-logout": {},
        },
        "sid": secrets.token_hex(32),
    }

    return default_payload | logut_payload


@pytest.fixture()
def sign_jwt(default_payload):
    def __sign(key_file: str, alg: str, payload: dict[str, Any] | None = None):
        payload = payload or default_payload

        with open(key_file) as f:
            key = jwt.PyJWK.from_json(f.read())
        headers = {
            "kid": key.key_id,
        }

        return jwt.encode(payload, key.key, alg, headers)
    return __sign


@pytest.mark.parametrize('key_alg', [
    pytest.param(('rsa.priv.json', 'RS256'), id='rsa'),
    pytest.param(('es.priv.json', 'ES256'), id='es'),
])
def test_verify_jwt(oidc_auth, sign_jwt, key_alg: tuple[str, str]):
    key, alg = key_alg
    jwt = sign_jwt(key, alg)
    res = oidc_auth.verify_id_token(jwt)
    assert res['iss'] == EXAMPLE_ISSUER


def test_verify_jwt_invalid_signature(oidc_auth, sign_jwt):
    key = 'missing.priv.json'
    alg = 'ES256'
    jwt = sign_jwt(key, alg)
    with pytest.raises(OIDCAuthError):
        oidc_auth.verify_id_token(jwt)


def _assert_verify_id_token_raises_oidc_error(oidc_auth, sign_jwt, payload: dict[str, Any]):
    _assert_verify_raises_oidc_error(sign_jwt, payload, oidc_auth.verify_id_token)


def _assert_verify_logout_token_raises_oidc_error(oidc_auth, sign_jwt, payload: dict[str, Any]):
    _assert_verify_raises_oidc_error(sign_jwt, payload, oidc_auth.verify_logout_token)


def _assert_verify_raises_oidc_error(sign_jwt, payload: dict[str, Any], verify_func):
    key, alg = DEFAULT_KEY
    jwt = sign_jwt(key, alg, payload)
    with pytest.raises(OIDCAuthError):
        verify_func(jwt)


def test_verify_invalid_issuer(oidc_auth, sign_jwt, default_payload: dict[str, Any]):
    default_payload['iss'] = 'INVALID'
    _assert_verify_id_token_raises_oidc_error(oidc_auth, sign_jwt, default_payload)


def test_verify_jwt_expired(oidc_auth, sign_jwt, default_payload: dict[str, Any]):
    default_payload['exp'] = int((datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=5)).timestamp())
    _assert_verify_id_token_raises_oidc_error(oidc_auth, sign_jwt, default_payload)


def test_verify_missing_uid(oidc_auth, sign_jwt, default_payload: dict[str, Any]):
    del default_payload['uid']
    _assert_verify_id_token_raises_oidc_error(oidc_auth, sign_jwt, default_payload)


@pytest.mark.parametrize('key_alg', [
    pytest.param(('rsa.priv.json', 'RS256'), id='rsa'),
    pytest.param(('es.priv.json', 'ES256'), id='es'),
])
def test_verify_logout_token(oidc_auth, sign_jwt, key_alg, default_logout_payload):
    key, alg = key_alg
    jwt = sign_jwt(key, alg, default_logout_payload)
    res = oidc_auth.verify_logout_token(jwt)
    assert res['sid'] == default_logout_payload['sid']


def test_verify_logout_token_missing_events(oidc_auth, sign_jwt, default_logout_payload):
    del default_logout_payload['events']
    _assert_verify_logout_token_raises_oidc_error(oidc_auth, sign_jwt, default_logout_payload)


def test_verify_logout_token_nonce(oidc_auth, sign_jwt, default_logout_payload):
    default_logout_payload['nonce'] = 'test'
    _assert_verify_logout_token_raises_oidc_error(oidc_auth, sign_jwt, default_logout_payload)


def test_verify_logout_missing_sub_sid(oidc_auth, sign_jwt, default_logout_payload):
    del default_logout_payload['sid']
    del default_logout_payload['sub']
    _assert_verify_logout_token_raises_oidc_error(oidc_auth, sign_jwt, default_logout_payload)
