#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check whether it is possible to change expired password
## tags: [saml, skip_admember]
## join: true
## exposure: dangerous

import time

import pytest

import univention.testing.udm as udm_test
from univention.testing import ucs_samba

import samltest


def test_change_expired_password(ucr):
    with udm_test.UCSTestUDM() as udm:
        testcase_user_name = udm.create_user(pwdChangeNextLogin='1')[1]
        if ucr.get('server/role') == 'memberserver' and ucs_samba.get_available_s4connector_dc():
            #  Make sure the user has been replicated or the password change can fail
            print('Wait for s4 replication')
            time.sleep(17)
        saml_session = samltest.SamlTest(testcase_user_name, 'univention')

        with pytest.raises(samltest.SamlPasswordExpired):
            saml_session.login_with_new_session_at_IdP()

        # changing to the current password should fail
        with pytest.raises(samltest.SamlPasswordChangeFailed):
            saml_session.change_expired_password('univention')

        saml_session.change_expired_password('Univention.99')
        saml_session.test_logged_in_status()
