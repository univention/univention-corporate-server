#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal keycloak self service features
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages: [univention-self-service]
## apps: [keycloak]

from utils import _


def test_login_denied_if_not_verified(keycloak_settings, portal_login_via_keycloak, unverified_user, portal_config, keycloak_config, change_app_setting, is_keycloak):
    change_app_setting('keycloak', {'ucs/self/registration/check_email_verification': True})
    page = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = page.locator(".ucs-p")
    error_msg = error.inner_html()
    assert _('Your account is not verified.') in error_msg
    # verify
    unverified_user.verify()
    # try again
    page.click("input[class='pf-c-button pf-m-primary pf-m-block btn-lg']")
    # verify that we are in the portal now
    page.locator(f"[id='{portal_config.header_menu_id}']")


def test_verified_msg(change_app_setting, unverified_user, portal_login_via_keycloak, is_keycloak):
    settings = {
        'keycloak/login/messages/en/accountNotVerifiedMsg': 'en yada yada yada',
        'keycloak/login/messages/de/accountNotVerifiedMsg': 'de yada yada yada',
        'ucs/self/registration/check_email_verification': True,
    }
    change_app_setting('keycloak', settings)
    page = portal_login_via_keycloak(unverified_user.username, unverified_user.password, verify_login=False)
    error = page.locator(".ucs-p")
    error_msg = error.inner_text()
    assert error_msg == _('en yada yada yada')
    page.locator("input[class='pf-c-button pf-m-primary pf-m-block btn-lg']")
