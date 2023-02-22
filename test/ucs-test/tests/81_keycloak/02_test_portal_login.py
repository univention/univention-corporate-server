#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test portal SSO login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import pytest

import univention.testing.udm as udm_test
from univention.lib.umc import Unauthorized
from univention.testing.umc import Client
from univention.testing.utils import get_ldap_connection, wait_for_listener_replication


def test_login(portal_login_via_keycloak):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user()[1]
        assert portal_login_via_keycloak(username, "univention")


def test_login_wrong_password(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user()[1]
        assert portal_login_via_keycloak(username, "univentionWrong", fails_with=keycloak_config.wrong_password_msg)


def test_login_disabled(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(disabled=1)[1]
        assert portal_login_via_keycloak(username, "univention", fails_with=keycloak_config.wrong_password_msg)


def test_login_pwdChangeNextLogin(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        assert portal_login_via_keycloak(username, "univention", new_password="Univention.99")
        assert Client(username=username, password="Univention.99")
        with pytest.raises(Unauthorized):
            Client(username=username, password="univention")


def test_login_pwdChangeNextLogin_wrong_password(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        assert portal_login_via_keycloak(username, "univentionBAD", new_password="Univention.99", fails_with=keycloak_config.wrong_password_msg)


def test_password_expired_shadowLastChange(portal_login_via_keycloak, keycloak_config):
    ldap = get_ldap_connection(primary=True)
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user()
        changes = [
            ("shadowMax", [""], [b"2"]),
            ("shadowLastChange", [""], [b"1000"]),
        ]
        ldap.modify(dn, changes)
        wait_for_listener_replication()
        assert portal_login_via_keycloak(username, "univention", new_password="Univention.99")
        assert Client(username=username, password="Univention.99")
        with pytest.raises(Unauthorized):
            Client(username=username, password="univention")
