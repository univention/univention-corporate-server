#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether SSO is not possible with expired user account
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

from datetime import datetime, timedelta

import pytest

import univention.testing.udm as udm_test

import samltest


def test_expired_account():
    yesterday = datetime.now() - timedelta(days=1)
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(userexpiry=yesterday.isoformat()[:10])[1]
        saml_session = samltest.SamlTest(testcase_user_name, 'aaaunivention')
        with pytest.raises(samltest.SamlAuthenticationFailed):
            saml_session.login_with_new_session_at_IdP()
        saml_session = samltest.SamlTest(testcase_user_name, 'univention')
        with pytest.raises(samltest.SamlAccountExpired):
            saml_session.login_with_new_session_at_IdP()


def test_unexpired_account():
    tomorrow = datetime.now() + timedelta(days=1)
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(userexpiry=tomorrow.isoformat()[:10])[1]
        saml_session = samltest.SamlTest(testcase_user_name, 'univention')
        saml_session.login_with_new_session_at_IdP()
        saml_session.test_logged_in_status()
