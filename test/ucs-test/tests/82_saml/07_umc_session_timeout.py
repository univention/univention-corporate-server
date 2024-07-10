#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Session timeout at UMC
## tags: [saml]
## bugs: [52443, 52888]
## join: true
## exposure: safe
## roles: [domaincontroller_master]

import subprocess
import time

from univention.config_registry import handler_set
from univention.testing import utils

import samltest


def test_umc_session_timeout(ucr, saml_session):
    session_timeout = 10
    try:
        handler_set([f'umc/saml/assertion-lifetime={session_timeout}', 'umc/saml/grace_time=1'])
        subprocess.check_call(['systemctl', 'restart', 'slapd.service'])
        subprocess.check_call(['/usr/share/univention-management-console/saml/update_metadata'])
        utils.wait_for_listener_replication()
        try:
            saml_session.login_with_new_session_at_IdP()
            saml_session.test_logged_in_status()
            saml_session.test_slapd()
            print('Waiting for session timeout')
            subprocess.check_call(['systemctl', 'restart', 'slapd.service'])  # close ldap connections
            time.sleep(session_timeout + 10)
            for test_method in (saml_session.test_logged_in_status, saml_session.test_slapd):
                try:
                    print(f'testing {test_method}')
                    test_method()
                except samltest.SamlError:
                    if saml_session.page.status_code == 401:
                        print(f'OK: session timeout error for {test_method}')
                    else:
                        raise
                else:
                    utils.fail(f'No session timeout error for {test_method}')
            saml_session.login_with_existing_session_at_IdP()
            saml_session.test_logged_in_status()
            saml_session.test_slapd()
            saml_session.logout_at_IdP()
            saml_session.test_logout_at_IdP()
            saml_session.test_logout()
        except samltest.SamlError as exc:
            utils.fail(str(exc))
    finally:
        subprocess.check_call(['systemctl', 'restart', 'slapd.service'])
        subprocess.check_call(['/usr/share/univention-management-console/saml/update_metadata'])
        utils.wait_for_listener_replication()
