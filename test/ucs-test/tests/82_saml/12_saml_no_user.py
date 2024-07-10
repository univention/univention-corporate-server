#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether SSO is not possible with non existing user account
## tags:
##  - saml
##  - univention
## join: true
## exposure: dangerous
## tags:
##  - skip_admember

import pytest

import samltest


def test_saml_no_user():
    saml_session = samltest.SamlTest('NonExistent3.14', 'univention')

    with pytest.raises(samltest.SamlAuthenticationFailed):
        saml_session.login_with_new_session_at_IdP()
