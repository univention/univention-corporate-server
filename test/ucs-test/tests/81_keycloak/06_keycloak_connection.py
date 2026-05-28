#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keyloak connections
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import json
import os

import pytest
from keycloak import KeycloakAdmin
from keycloak.connection import ConnectionManager
from keycloak.exceptions import KeycloakPostError


def assert_invalid_grant(exc):
    body = json.loads(exc.response_body)
    assert exc.response_code == 400
    assert body.get("error") == "invalid_grant"
    assert body.get("error_description") == "Invalid user credentials"


def test_admin_connection_administrator(keycloak_administrator_connection, admin_account):
    assert keycloak_administrator_connection.realm_name == 'ucs'
    assert isinstance(keycloak_administrator_connection.connection, ConnectionManager)
    assert keycloak_administrator_connection.client_id == 'admin-cli'
    assert keycloak_administrator_connection.client_secret_key is None
    assert keycloak_administrator_connection.username == admin_account.username


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_admin_connection_admin(keycloak_admin_connection, keycloak_admin):
    assert keycloak_admin_connection.username == keycloak_admin
    assert keycloak_admin_connection.client_id == 'admin-cli'


def test_admin_connection_admin_fails_non_existing_user(keycloak_config):
    with pytest.raises(KeycloakPostError) as exc_info:
        KeycloakAdmin(
            server_url=keycloak_config.url,
            username='sfsdfdfd',
            password='ljljdlkajdlkjdlk',
            realm_name='ucs',
            user_realm_name='master',
            verify=True,
        )
    assert_invalid_grant(exc_info.value)


def test_admin_connection_non_admin_fails(keycloak_config, udm):
    password = 'univention'
    username = udm.create_user(password=password)[1]
    with pytest.raises(KeycloakPostError) as exc_info:
        KeycloakAdmin(
            server_url=keycloak_config.url,
            username=username,
            password=password,
            realm_name='ucs',
            user_realm_name='master',
            verify=True,
        )
    assert_invalid_grant(exc_info.value)


def test_admin_connection_domain_admins_group(keycloak_config, domain_admins_dn, udm):
    password = '#äö=)(///$(!)&êîâû'
    username = udm.create_user(password=password, primaryGroup=domain_admins_dn)[1]
    connection = KeycloakAdmin(
        server_url=keycloak_config.url,
        username=username,
        password=password,
        realm_name='ucs',
        user_realm_name='master',
        verify=True,
    )
    assert connection.username == username
    assert connection.client_id == 'admin-cli'


def test_openid_connection_administrator(keycloak_openid_connection, admin_account):
    # Administrator
    token = keycloak_openid_connection.token(admin_account.username, admin_account.bindpw, scope='openid')
    keycloak_openid_connection.logout(token['refresh_token'])


def test_openid_connection_fails_non_existing_user(keycloak_openid_connection):
    with pytest.raises(KeycloakPostError) as exc_info:
        keycloak_openid_connection.token('lsjdlsajdlksa', 'dskjasdlk')
    assert_invalid_grant(exc_info.value)


def test_openid_connection_user(keycloak_openid_connection, udm):
    password = 'univentionöäü!$ê'
    username = udm.create_user(password=password)[1]
    token = keycloak_openid_connection.token(username, password, scope='openid')
    keycloak_openid_connection.logout(token['refresh_token'])


def test_openid_connection_machine_account(keycloak_openid_connection, ucr):
    username = f"{ucr.get('hostname')}$"
    password = open('/etc/machine.secret').read().strip()
    keycloak_openid_connection.token(username, password, scope='openid')
