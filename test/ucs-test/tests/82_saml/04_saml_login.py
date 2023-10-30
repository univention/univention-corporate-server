#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: SSO Login at UMC as Service Provider
## tags: [saml]
## join: true
## packages:
##   - univention-saml
## exposure: safe
## tags:
##  - skip_admember

from univention.testing import utils

import samltest


def __get_samlSession():
    account = utils.UCSTestDomainAdminCredentials()
    return samltest.SamlTest(account.username, account.bindpw)


def __test_umc_sp(samlSession, test_function):
    samlSession.login_with_new_session_at_IdP()
    test_function()
    samlSession.logout_at_IdP()
    samlSession.test_logout_at_IdP()
    samlSession.test_logout()


def test_umc_web_server():
    samlSession = __get_samlSession()
    __test_umc_sp(samlSession, samlSession.test_logged_in_status)
