#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keycloak admin console login
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import pytest
from utils import _


def test_login_administrator(keycloak_adm_login, admin_account):
    keycloak_adm_login(admin_account.username, admin_account.bindpw)


def test_login_administrator_with_wrong_password_fails(keycloak_adm_login, admin_account):
    assert keycloak_adm_login(
        admin_account.username,
        f'{admin_account.bindpw}1234',
        fails_with=_('The authentication has failed, please login again.'),
    )
    with pytest.raises(AssertionError):
        keycloak_adm_login(
            admin_account.username,
            f'{admin_account.bindpw}1234',
            fails_with="wrong message",
        )


def test_login_local_admin(keycloak_adm_login, keycloak_secret, keycloak_admin):
    if keycloak_secret:
        assert keycloak_adm_login(keycloak_admin, keycloak_secret)


def test_login_non_admin_fails(keycloak_adm_login, udm):
    username = udm.create_user(password='univention')[1]
    assert keycloak_adm_login(username, 'univention', fails_with=_('The authentication has failed, please login again.'))


def test_login_domain_admins(keycloak_adm_login, domain_admins_dn, udm):
    username = udm.create_user(password='univention', primaryGroup=domain_admins_dn)[1]
    assert keycloak_adm_login(username, 'univention')


def test_login_domain_admins_wrong_password_fails(keycloak_adm_login, domain_admins_dn, udm):
    username = udm.create_user(password='univention', primaryGroup=domain_admins_dn)[1]
    assert keycloak_adm_login(username, 'password', fails_with=_('The authentication has failed, please login again.'))


def test_login_domain_admins_pwdChangeNextLogin(keycloak_adm_login, domain_admins_dn, udm):
    # password change via admin console is not enabled
    username = udm.create_user(password='univention', primaryGroup=domain_admins_dn, pwdChangeNextLogin=1)[1]
    assert keycloak_adm_login(username, 'univention', fails_with=_('The authentication has failed, please login again.'))
