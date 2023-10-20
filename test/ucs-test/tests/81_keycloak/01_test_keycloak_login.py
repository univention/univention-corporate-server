#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak admin console login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous


def test_login_administrator(keycloak_adm_login, admin_account,):
    assert keycloak_adm_login(admin_account.username, admin_account.bindpw,)


def test_login_administrator_with_wrong_password_fails(keycloak_adm_login, keycloak_config, admin_account,):
    assert keycloak_adm_login(
        admin_account.username,
        f"{admin_account.bindpw}1234",
        fails_with=keycloak_config.wrong_password_msg,)


def test_login_local_admin(keycloak_adm_login, keycloak_secret, keycloak_admin,):
    if keycloak_secret:
        assert keycloak_adm_login(keycloak_admin, keycloak_secret,)


def test_login_non_admin_fails(keycloak_adm_login, keycloak_config, udm,):
    username = udm.create_user(password="univention")[1]
    assert keycloak_adm_login(username, "univention", fails_with=keycloak_config.wrong_password_msg,)


def test_login_domain_admins(keycloak_adm_login, domain_admins_dn, udm,):
    username = udm.create_user(password="univention", primaryGroup=domain_admins_dn,)[1]
    assert keycloak_adm_login(username, "univention",)


def test_login_domain_admins_wrong_password_fails(keycloak_adm_login, keycloak_config, domain_admins_dn, udm,):
    username = udm.create_user(password="univention", primaryGroup=domain_admins_dn,)[1]
    assert keycloak_adm_login(username, "password", fails_with=keycloak_config.wrong_password_msg,)


def test_login_domain_admins_pwdChangeNextLogin(keycloak_adm_login, keycloak_config, domain_admins_dn, udm,):
    # password change via admin console is not enabled
    username = udm.create_user(password="univention", primaryGroup=domain_admins_dn, pwdChangeNextLogin=1,)[1]
    assert keycloak_adm_login(username, "univention", fails_with=keycloak_config.wrong_password_msg,)
