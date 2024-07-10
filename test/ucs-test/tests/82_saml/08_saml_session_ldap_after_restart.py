#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check if SSO session is still active after LDAP server restart
## tags: [saml]
## roles: [domaincontroller_master]
## exposure: dangerous
## tags:
##  - skip_admember

import subprocess


def test_session_ldap_after_restart(saml_session):
    saml_session.login_with_new_session_at_IdP()
    subprocess.call(['/etc/init.d/slapd', 'restart'])
    saml_session.test_logged_in_status()
    print("Success: SSO session is still working after slapd restart")
