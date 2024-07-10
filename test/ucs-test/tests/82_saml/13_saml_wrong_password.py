#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether SSO is not possible with wrong password
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

import pytest

import univention.testing.udm as udm_test

import samltest


def test_saml_wrong_password():
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user()[1]
        saml_session = samltest.SamlTest(testcase_user_name, 'Wrong password')

        with pytest.raises(samltest.SamlAuthenticationFailed):
            saml_session.login_with_new_session_at_IdP()
