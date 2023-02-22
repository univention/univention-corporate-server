#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak admin console login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import univention.testing.udm as udm_test
from univention.testing.utils import UCSTestDomainAdminCredentials


def test_login_admin(keycloak_adm_login):
    account = UCSTestDomainAdminCredentials()
    assert keycloak_adm_login(account.username, account.bindpw)


def test_login_admin_with_wrong_password_fails(keycloak_adm_login, keycloak_config):
    account = UCSTestDomainAdminCredentials()
    assert keycloak_adm_login(account.username, f"{account.bindpw}1234", fails_with=keycloak_config.wrong_password_msg)


def test_login_non_admin_fails(keycloak_adm_login, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(password="univention")[1]
        assert keycloak_adm_login(username, "univention", fails_with=keycloak_config.wrong_password_msg)


def test_login_domain_admins(keycloak_adm_login, domain_admins_dn):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(password="univention", primaryGroup=domain_admins_dn)[1]
        assert keycloak_adm_login(username, "univention")


def test_login_domain_admins_wrong_password_fails(keycloak_adm_login, keycloak_config, domain_admins_dn):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(password="univention", primaryGroup=domain_admins_dn)[1]
        assert keycloak_adm_login(username, "password", fails_with=keycloak_config.wrong_password_msg)
