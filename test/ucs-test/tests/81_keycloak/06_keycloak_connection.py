#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keyloak connections
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
from keycloak import KeycloakAdmin
from keycloak.connection import ConnectionManager
from keycloak.exceptions import KeycloakAuthenticationError


def test_admin_connection_administrator(keycloak_administrator_connection, admin_account,):
    assert keycloak_administrator_connection.realm_name == "ucs"
    assert isinstance(keycloak_administrator_connection.connection, ConnectionManager,)
    assert keycloak_administrator_connection.client_id == "admin-cli"
    assert keycloak_administrator_connection.client_secret_key is None
    assert keycloak_administrator_connection.username == admin_account.username


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret",)
def test_admin_connection_admin(keycloak_admin_connection, keycloak_admin,):
    assert keycloak_admin_connection.username == keycloak_admin
    assert keycloak_admin_connection.client_id == "admin-cli"


def test_admin_connection_admin_fails_non_existing_user(keycloak_config,):
    with pytest.raises(KeycloakAuthenticationError):
        KeycloakAdmin(
            server_url=keycloak_config.url,
            username="sfsdfdfd",
            password="ljljdlkajdlkjdlk",
            realm_name='ucs',
            user_realm_name='master',
            verify=True,)


def test_admin_connection_non_admin_fails(keycloak_config, udm,):
    password = "univention"
    username = udm.create_user(password=password)[1]
    with pytest.raises(KeycloakAuthenticationError):
        KeycloakAdmin(
            server_url=keycloak_config.url,
            username=username,
            password=password,
            realm_name='ucs',
            user_realm_name='master',
            verify=True,)


def test_admin_connection_domain_admins_group(keycloak_config, domain_admins_dn, udm,):
    password = "#äö=)(///$(!)&êîâû"
    username = udm.create_user(password=password, primaryGroup=domain_admins_dn,)[1]
    connection = KeycloakAdmin(
        server_url=keycloak_config.url,
        username=username,
        password=password,
        realm_name='ucs',
        user_realm_name='master',
        verify=True,)
    assert connection.username == username
    assert connection.client_id == "admin-cli"


def test_openid_connection_administrator(keycloak_openid_connection, admin_account,):
    # Administrator
    token = keycloak_openid_connection.token(admin_account.username, admin_account.bindpw, scope="openid",)
    userinfo = keycloak_openid_connection.userinfo(token['access_token'])
    assert userinfo["preferred_username"] == admin_account.username.lower(), "Wrong user login"
    keycloak_openid_connection.logout(token['refresh_token'])


def test_openid_connection_fails_non_existing_user(keycloak_openid_connection,):
    with pytest.raises(KeycloakAuthenticationError):
        keycloak_openid_connection.token("lsjdlsajdlksa", "dskjasdlk",)


def test_openid_connection_user(keycloak_openid_connection, udm,):
    password = "univentionöäü!$ê"
    username = udm.create_user(password=password)[1]
    token = keycloak_openid_connection.token(username, password, scope="openid",)
    userinfo = keycloak_openid_connection.userinfo(token['access_token'])
    assert userinfo["preferred_username"] == username.lower(), "Wrong user login"
    keycloak_openid_connection.logout(token['refresh_token'])
