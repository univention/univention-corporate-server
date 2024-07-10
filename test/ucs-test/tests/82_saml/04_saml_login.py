#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: SSO Login at UMC as Service Provider
## tags: [saml]
## join: true
## exposure: safe
## packages:
##   - univention-samba4
## tags:
##  - skip_admember

def test_umc_web_server(saml_session):
    saml_session.login_with_new_session_at_IdP()
    saml_session.test_logged_in_status()
    saml_session.logout_at_IdP()
    saml_session.test_logout_at_IdP()
    saml_session.test_logout()
