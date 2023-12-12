#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: SSO Login at UMC as Service Provider with kerberos
## tags: [saml]
## join: true
## exposure: dangerous
## roles: [domaincontroller_master]
## packages:
##   - univention-samba4
## tags:
##  - skip_admember

#import subprocess


def test_umc_web_server(kerberos_ticket, saml_session_kerberos):
    saml_session_kerberos.login_with_new_session_at_IdP()
    saml_session_kerberos.test_logged_in_status()
    saml_session_kerberos.logout_at_IdP()

    # FIXME: if KRB ticket is not destroyed, session in Keycloak is recreated
    # subprocess.check_call(['kdestroy'])

    saml_session_kerberos.test_logout_at_IdP()
    saml_session_kerberos.test_logout()
