#!/usr/share/ucs-test/runner python3
## desc: Session timeout at UMC
## tags: [saml]
## bugs: [52443, 52888]
## join: true
## exposure: safe
## roles: [domaincontroller_master]

import subprocess
import time

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils

import samltest


def main():
    session_timeout = 10
    with ucr_test.UCSTestConfigRegistry():
        handler_set([f'umc/saml/assertion-lifetime={session_timeout}', 'umc/saml/grace_time=1'])
        subprocess.check_call(['systemctl', 'restart', 'slapd.service'])
        subprocess.check_call(['/usr/share/univention-management-console/saml/update_metadata'])
        utils.wait_for_listener_replication()
        account = utils.UCSTestDomainAdminCredentials()
        SamlSession = samltest.SamlTest(account.username, account.bindpw,)
        try:
            SamlSession.login_with_new_session_at_IdP()
            SamlSession.test_logged_in_status()
            SamlSession.test_slapd()
            print('Waiting for session timeout')
            subprocess.check_call(['systemctl', 'restart', 'slapd.service'])  # close ldap connections
            time.sleep(session_timeout + 10)
            for test_method in (SamlSession.test_logged_in_status, SamlSession.test_slapd):
                try:
                    print(f'testing {test_method}')
                    test_method()
                except samltest.SamlError:
                    if SamlSession.page.status_code == 401:
                        print(f'OK: session timeout error for {test_method}')
                    else:
                        raise
                else:
                    utils.fail(f'No session timeout error for {test_method}')
            SamlSession.login_with_existing_session_at_IdP()
            SamlSession.test_logged_in_status()
            SamlSession.test_slapd()
            SamlSession.logout_at_IdP()
            SamlSession.test_logout_at_IdP()
            SamlSession.test_logout()
        except samltest.SamlError as exc:
            utils.fail(str(exc))


if __name__ == '__main__':
    try:
        main()
    finally:
        subprocess.check_call(['systemctl', 'restart', 'slapd.service'])
        subprocess.check_call(['/usr/share/univention-management-console/saml/update_metadata'])
        utils.wait_for_listener_replication()
    print("####Success: SSO login is working####")
