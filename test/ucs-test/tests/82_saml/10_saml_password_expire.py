#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether SSO is not possible with expired password flag on user account
## tags: [saml,skip_admember]
## join: true
## exposure: dangerous

import pytest

import univention.testing.udm as udm_test
from univention.testing.utils import get_ldap_connection

import samltest


def test_normal_user():
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin='1')[1]
        # wrong password
        saml_session = samltest.SamlTest(username, 'aaaunivention')
        with pytest.raises(samltest.SamlAuthenticationFailed):
            saml_session.login_with_new_session_at_IdP()
        # correct password
        saml_session = samltest.SamlTest(username, 'univention')
        with pytest.raises(samltest.SamlPasswordExpired):
            saml_session.login_with_new_session_at_IdP()


def test_kinit_user():
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user(pwdChangeNextLogin='1')
        lo = get_ldap_connection()
        lo.modify(dn, [('userPassword', lo.get(dn, ['userPassword'])['userPassword'], [b'{KINIT}'])])
        udm.verify_ldap_object(dn, {'userPassword': ['{KINIT}']})
        # wrong password
        saml_session = samltest.SamlTest(username, 'aaaunivention')
        with pytest.raises(samltest.SamlAuthenticationFailed):
            saml_session.login_with_new_session_at_IdP()
        # correct password
        saml_session = samltest.SamlTest(username, 'univention')
        with pytest.raises(samltest.SamlPasswordExpired):
            saml_session.login_with_new_session_at_IdP()


def test_k5key_user():
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user(pwdChangeNextLogin='1')
        lo = get_ldap_connection()
        lo.modify(dn, [('userPassword', lo.get(dn, ['userPassword'])['userPassword'], [b'{K5KEY}'])])
        udm.verify_ldap_object(dn, {'userPassword': ['{K5KEY}']})
        # wrong password
        saml_session = samltest.SamlTest(username, 'aaaunivention')
        with pytest.raises(samltest.SamlAuthenticationFailed):
            saml_session.login_with_new_session_at_IdP()
        # correct password
        saml_session = samltest.SamlTest(username, 'univention')
        with pytest.raises(samltest.SamlPasswordExpired):
            saml_session.login_with_new_session_at_IdP()
