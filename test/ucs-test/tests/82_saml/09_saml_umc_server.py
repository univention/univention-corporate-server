#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: SSO Login at UMC, test umc connection and ldap connection
## tags: [saml]
## roles: [domaincontroller_master]
## join: true
## exposure: safe
## tags:
##  - skip_admember

import subprocess
import time

from univention.testing import utils

import samltest


def __get_saml_session():
    account = utils.UCSTestDomainAdminCredentials()
    return samltest.SamlTest(account.username, account.bindpw)


def __test_umc_sp(samlSession, test_function):
    samlSession.login_with_new_session_at_IdP()
    test_function()
    samlSession.logout_at_IdP()
    samlSession.test_logout_at_IdP()
    samlSession.test_logout()


def test_umc_server():
    def assert_module_testing():
        # Ensure an UMC module will be opened
        subprocess.check_call(['systemctl', 'stop', 'univention-management-console-server'])
        saml_session.test_umc_server()

    saml_session = __get_saml_session()
    try:
        __test_umc_sp(saml_session, assert_module_testing)
    except samltest.SamlError:
        if saml_session.page.status_code == 503:
            pass
        else:
            raise
    else:
        utils.fail('test_umc_server() should not work without umc server running')
    finally:
        subprocess.check_call(['systemctl', 'start', 'univention-management-console-server'])
        time.sleep(3)  # umc-server is not ready immediately

    saml_session = __get_saml_session()
    __test_umc_sp(saml_session, saml_session.test_umc_server)


def test_umc_ldap_con():
    def assert_slapd_testing():
        saml_session.test_slapd()
        # Ensure an ldap connection will be opened
        subprocess.check_call(['systemctl', 'stop', 'slapd'])
        saml_session.test_slapd()

    try:
        saml_session = __get_saml_session()
        __test_umc_sp(saml_session, assert_slapd_testing)
    except samltest.SamlError:
        if saml_session.page.status_code == 503:
            pass
        else:
            raise
    else:
        utils.fail('test_slapd() should not work without slapd running')
    finally:
        subprocess.check_call(['systemctl', 'start', 'slapd'])

    for _ in range(2):
        saml_session = __get_saml_session()
        __test_umc_sp(saml_session, saml_session.test_slapd)
