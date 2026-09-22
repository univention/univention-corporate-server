#!/usr/share/ucs-test/runner pytest-3 -s -l -vv --tb=native
## desc: Test security of OIDC implementation
## roles:
##  - domaincontroller_master
## tags:
##  - SKIP
## exposure: dangerous

import base64
import json
import sys
import time
import uuid
from urllib.parse import urlparse

import jwt
import ldap
import psycopg2
import pytest
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_der_private_key

import univention.uldap
from univention.config_registry import ucr


fqdn = f'{ucr["hostname"]}.{ucr["domainname"]}'
now = int(time.time())


def get_keycloak_private_key() -> str | None:
    QUERY = """
    SELECT
        r.name AS realm,
        c.id AS component_id,
        c.name AS component_name,
        c.provider_id,
        private_key.value AS private_key,
        kid.value AS kid
    FROM component AS c
    JOIN realm AS r
      ON r.id = c.realm_id
    JOIN component_config AS private_key
      ON private_key.component_id = c.id
     AND private_key.name = 'privateKey'
    LEFT JOIN component_config AS kid
      ON kid.component_id = c.id
     AND kid.name = 'kid'
    ORDER BY
        r.name,
        c.provider_id,
        c.name,
        c.id
    """

    def parse_jdbc_postgresql_url(url: str) -> dict[str, object]:
        """Convert e.g.jdbc:postgresql://db.example.test:5432/keycloak into connection parameters."""
        prefix = 'jdbc:'
        url = url.removeprefix(prefix)

        parsed = urlparse(url)

        if parsed.scheme != 'postgresql':
            raise ValueError(
                f'Unsupported database URL {url!r}; expected PostgreSQL',
            )

        database = parsed.path.lstrip('/')
        if not database:
            raise ValueError(f'No database name found in {url!r}')

        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'dbname': database,
        }

    def get_connection_parameters() -> dict[str, object]:
        db_url = ucr.get('kc/db/url')

        if not db_url:
            fqdn = '.'.join(
                part
                for part in (
                    ucr.get('hostname'),
                    ucr.get('domainname'),
                )
                if part
            )
            db_url = f'jdbc:postgresql://{fqdn}:5432/keycloak'

        params = parse_jdbc_postgresql_url(db_url)
        params['user'] = ucr.get('kc/db/username', 'keycloak')
        params['password'] = open('/etc/postgresql-keycloak.secret').read()
        return params

    with psycopg2.connect(**get_connection_parameters()) as connection:  # type: ignore
        with connection.cursor() as cursor:
            cursor.execute(QUERY)

            found = False

            for (
                realm,
                component_id,
                component_name,
                provider_id,
                private_key,
                kid,
            ) in cursor:
                print(f'realm:      {realm}')
                print(f'component:  {component_name}')
                print(f'component-id: {component_id}')
                print(f'provider:   {provider_id}')
                print(f'kid:        {kid or "<not stored>"}')
                print('private-key:')
                print(private_key)
                print()
                if realm == 'ucs' and provider_id == 'rsa-generated':
                    return private_key

            if not found:
                print('No private keys found.', file=sys.stderr)


class InvalidToken(Exception):
    pass


def create_token(
    claims,
    algorithm='RS256',
    signing_key=None,
    kid=None,
):
    headers = {'typ': 'JWT'}
    if kid is not None:
        headers['kid'] = kid

    if algorithm.lower() == 'none':
        return jwt.encode(claims, '', algorithm='none', headers=headers | {'alg': 'none'})

    if signing_key is None:
        raise ValueError(f'{algorithm} requires a signing_key')

    return jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)


@pytest.fixture
def valid_claims():
    now = int(time.time())

    return {
        'exp': now + 300,
        'iat': now - 300,
        'auth_time': now - 300,
        'jti': f'test:{uuid.uuid4()}',
        'iss': f'https://ucs-sso-ng.{ucr["domainname"]}/realms/ucs',
        'aud': [
            f'ldaps://{ucr["domainname"]}/',
            'account',
        ],
        'sub': 'test-user',
        'typ': 'Bearer',
        'azp': f'https://{fqdn}/univention/oidc/',
        'acr': '1',
        'scope': 'openid email profile',
        'uid': 'Administrator',
        'email_verified': False,
        'name': 'Administrator',
        'preferred_username': 'administrator',
        'family_name': 'Administrator',
    }


@pytest.fixture(scope='session')
def kid():
    url = f'https://ucs-sso-ng.{ucr["domainname"]}/realms/ucs/protocol/openid-connect/certs'
    return requests.get(url, timeout=10).json()['keys'][0]['kid']


@pytest.fixture(scope='session')
def encode_token(kid):
    key_string = get_keycloak_private_key() or ''
    key = load_der_private_key(
        base64.b64decode(key_string),
        password=None,
    )

    def _create_token(claims, algorithm='RS256', signing_key=key, kid=kid):
        return create_token(claims, algorithm, signing_key, kid)

    return _create_token


def verify_token(token):
    lo = univention.uldap.access(uri=f'ldap://{fqdn}:7389', base=ucr['ldap/base'])
    try:
        lo.bind_oauthbearer(None, token)
    except ldap.INVALID_CREDENTIALS as exc:  # type: ignore
        raise InvalidToken(exc.args[0]['info'].split(': ', 1)[1].replace('authentication failure: ', ''))


def test_rejects_token_without_exp(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('exp')

    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token has no expiration claim'):
        verify_token(token)


def test_rejects_token_without_kid(valid_claims, encode_token):
    token = encode_token(valid_claims, kid=None)

    with pytest.raises(InvalidToken, match='JWT signing key is unknown: ""'):
        verify_token(token)


def test_rejects_token_unknown_kid(valid_claims, encode_token):
    token = encode_token(valid_claims, kid='asdf')

    with pytest.raises(InvalidToken, match='JWT signing key is unknown: "asdf"'):
        verify_token(token)


def test_rejects_expired_token(valid_claims, encode_token):
    claims = valid_claims | {
        'exp': int(time.time()) - 8 * 60,
    }

    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token is expired or not yet valid'):
        verify_token(token)


def test_rejects_token_without_preferred_username(valid_claims, encode_token):
    claims = valid_claims.copy()
    # claims.pop('preferred_username')
    claims.pop('uid')

    token = encode_token(claims)

    with pytest.raises(
        InvalidToken,
        match='token contains no non-empty uid claim',
    ):
        verify_token(token)


def test_rejects_token_with_wrong_issuer(valid_claims, encode_token):
    claims = valid_claims | {
        'iss': 'https://wrong.example.test/',
    }

    token = encode_token(claims)

    with pytest.raises(
        InvalidToken,
        match=r'invalid or missing issuer: "https://wrong.example.test/"',
    ):
        verify_token(token)


def test_rejects_token_with_wrong_audience(valid_claims, encode_token):
    claims = valid_claims | {
        'aud': 'wrong-client',
    }

    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid or missing audience'):
        verify_token(token)


def test_rejects_token_with_wrong_authorized_party(valid_claims, encode_token):
    claims = valid_claims | {
        'azp': 'wrong-client',
    }

    token = encode_token(claims)

    with pytest.raises(
        InvalidToken,
        match='invalid authorized party: "wrong-client"',
    ):
        verify_token(token)


@pytest.mark.xfail(reason='not implemented')
def test_rejects_token_without_required_scope(valid_claims, encode_token):
    claims = valid_claims | {'scope': 'profile email'}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='required scope "openid" is missing'):
        verify_token(token)


@pytest.mark.xfail(reason='not implemented')
@pytest.mark.parametrize('scope', [None, 123, [], {}])
def test_rejects_token_with_non_string_scope(valid_claims, encode_token, scope):
    claims = valid_claims | {'scope': scope}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='required scope "openid" is missing'):
        verify_token(token)


def test_rejects_token_with_invalid_signature(valid_claims, encode_token):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    token = encode_token(
        valid_claims,
        signing_key=key,
    )

    with pytest.raises(InvalidToken, match='JWT signature is invalid'):
        verify_token(token)


def test_rejects_token_with_disallowed_signature_algorithm(valid_claims, encode_token):
    import secrets

    token = encode_token(
        valid_claims,
        algorithm='HS256',
        signing_key=secrets.token_bytes(32),
    )

    with pytest.raises(InvalidToken, match='JWT signature is invalid'):
        verify_token(token)


def test_rejects_token_invalid_jwt(valid_claims, encode_token):
    with pytest.raises(InvalidToken, match='there was an error parsing the JWT'):
        verify_token('not.a.valid-jwt')


def test_rejects_token_with_none_signature_algorithm(valid_claims, encode_token):
    token = encode_token(
        valid_claims,
        algorithm='none',
    )

    with pytest.raises(InvalidToken, match='there was an error parsing the JWT'):
        verify_token(token)


def test_rejects_token_with_unknown_signature_algorithm(valid_claims, encode_token, kid):
    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    header = b64url(
        json.dumps(
            {
                'alg': 'UNKNOWN',
                'typ': 'JWT',
                'kid': kid,
            },
        ).encode(),
    )

    payload = b64url(json.dumps(valid_claims).encode())

    token = f'{header}.{payload}.invalid-signature'

    with pytest.raises(InvalidToken, match='there was an error parsing the JWT'):
        verify_token(token)


def test_rejects_token_with_preferred_username_as_list(valid_claims, encode_token):
    claims = valid_claims | {
        'uid': ['alice'],
    }

    token = encode_token(claims)

    with pytest.raises(
        InvalidToken,
        match='token contains no non-empty uid claim',
    ):
        verify_token(token)


def test_accepts_valid_token(valid_claims, encode_token):
    verify_token(encode_token(valid_claims))


@pytest.mark.parametrize('value', [None, 123, [], {}])
def test_rejects_token_with_invalid_issuer_type(valid_claims, encode_token, value):
    claims = valid_claims | {'iss': value}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid or missing issuer: ""'):
        verify_token(token)


def test_rejects_token_without_issuer(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('iss')
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid or missing issuer: ""'):
        verify_token(token)


@pytest.mark.parametrize('audience', [None, 123, {}, [], ['wrong-client'], [123, None]])
def test_rejects_token_with_invalid_audience(valid_claims, encode_token, audience):
    claims = valid_claims | {'aud': audience}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid or missing audience'):
        verify_token(token)


def test_rejects_token_without_audience(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('aud')
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid or missing audience'):
        verify_token(token)


def test_accepts_trusted_audience_in_array(valid_claims, encode_token):
    claims = valid_claims | {
        'aud': ['wrong-client', f'ldaps://{ucr["domainname"]}/'],
    }
    verify_token(encode_token(claims))


def test_accepts_trusted_audience_as_string(valid_claims, encode_token):
    claims = valid_claims | {'aud': f'ldaps://{ucr["domainname"]}/'}
    verify_token(encode_token(claims))


def test_rejects_token_without_authorized_party(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('azp')
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid authorized party: ""'):
        verify_token(token)


@pytest.mark.parametrize('authorized_party', [None, 123, [], {}])
def test_rejects_token_with_invalid_authorized_party_type(valid_claims, encode_token, authorized_party):
    claims = valid_claims | {'azp': authorized_party}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='invalid authorized party: ""'):
        verify_token(token)


@pytest.mark.parametrize('expiration', [None, 'tomorrow', [], {}])
def test_rejects_token_with_invalid_expiration_type(valid_claims, encode_token, expiration):
    claims = valid_claims | {'exp': expiration}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token has no expiration claim'):
        verify_token(token)


def test_rejects_token_with_nbf_in_future(valid_claims, encode_token):
    claims = valid_claims | {'nbf': int(time.time()) + 8 * 60}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token is expired or not yet valid'):
        verify_token(token)


def test_rejects_token_with_iat_in_future(valid_claims, encode_token):
    claims = valid_claims | {'iat': int(time.time()) + 8 * 60}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token is expired or not yet valid'):
        verify_token(token)


@pytest.mark.parametrize('claim', ['nbf', 'iat'])
@pytest.mark.parametrize('value', ['invalid', [], {}])
def test_rejects_token_with_invalid_numeric_date(valid_claims, encode_token, claim, value):
    claims = valid_claims | {claim: value}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token is expired or not yet valid'):
        verify_token(token)


def test_accepts_token_without_nbf(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('nbf', None)
    verify_token(encode_token(claims))


def test_accepts_token_without_iat(valid_claims, encode_token):
    claims = valid_claims.copy()
    claims.pop('iat', None)
    verify_token(encode_token(claims))


@pytest.mark.parametrize('uid', ['', None, 123, [], {}])
def test_rejects_token_with_invalid_uid(valid_claims, encode_token, uid):
    claims = valid_claims | {'uid': uid}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match='token contains no non-empty uid claim'):
        verify_token(token)


@pytest.mark.parametrize('uid', ['root', 'Root', 'ROOT', 'rOoT'])
def test_rejects_disallowed_username_case_insensitively(valid_claims, encode_token, uid):
    claims = valid_claims | {'uid': uid}
    token = encode_token(claims)

    with pytest.raises(InvalidToken, match=f'username "{uid}" is disallowed'):
        verify_token(token)
