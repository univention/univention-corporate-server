#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal SSO login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

from datetime import datetime, timedelta

import pytest
from utils import keycloak_get_request, keycloak_password_change, keycloak_sessions_by_user

from univention.lib.umc import Unauthorized
from univention.testing.umc import Client
from univention.testing.utils import get_ldap_connection, wait_for_listener_replication


def test_login(portal_login_via_keycloak, udm):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univention')


def test_login_wrong_password_fails(portal_login_via_keycloak, keycloak_config, udm):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univentionWrong', fails_with=keycloak_config.wrong_password_msg)


def test_login_disabled_fails(portal_login_via_keycloak, keycloak_config, udm):
    username = udm.create_user(disabled=1)[1]
    assert portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.wrong_password_msg)


def test_password_change_pwdChangeNextLogin(portal_login_via_keycloak, keycloak_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99')
    assert Client(username=username, password='Univention.99')
    with pytest.raises(Unauthorized):
        Client(username=username, password='univention')


def test_password_change_wrong_old_password_fails(portal_login_via_keycloak, keycloak_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'univentionBAD', fails_with=keycloak_config.wrong_password_msg)


def test_password_change_same_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(username, 'univention', new_password='univention', fails_with='Changing password failed. The password was already used.')


def test_password_change_new_password_too_short_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='a',
        fails_with='Changing password failed. The password is too short.',
    )


def test_password_change_confirm_new_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='univention',
        new_password_confirm='univention1',
        fails_with="Passwords don't match.",
    )


def test_password_change_empty_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    page = portal_login_via_keycloak(username, 'univention', verify_login=False)
    # just click the button without old or new passwords
    page.click(f"[id='{keycloak_config.password_change_button_id}']")
    error = page.locator(keycloak_config.password_update_error_css_selector.replace("[class='", ".").replace("']", "").replace(" ", "."))
    assert error.inner_text() == 'Please specify password.', error.inner_text()


def test_password_change_after_second_try(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    page = portal_login_via_keycloak(
        username,
        'univention',
        new_password='univention',
        fails_with='Changing password failed. The password was already used.',
    )
    keycloak_password_change(page, keycloak_config, 'univention', 'Univention.99', 'Univention.99')
    assert Client(username=username, password='Univention.99')


def test_password_change_expired_shadowLastChange(portal_login_via_keycloak, keycloak_config, udm):
    ldap = get_ldap_connection(primary=True)
    dn, username = udm.create_user()
    changes = [
        ('shadowMax', [''], [b'2']),
        ('shadowLastChange', [''], [b'1000']),
    ]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99')
    assert Client(username=username, password='Univention.99')
    with pytest.raises(Unauthorized):
        Client(username=username, password='univention')


def test_logout(portal_login_via_keycloak, portal_config, keycloak_config, udm):
    username = udm.create_user()[1]
    page = portal_login_via_keycloak(username, 'univention')
    page.click(f"[id='{portal_config.header_menu_id}']")
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert sessions
    logout = page.locator(f"#{portal_config.logout_button_id}")
    lang = page.evaluate('() => window.navigator.userLanguage || window.navigator.language')
    logout_msg = portal_config.logout_msg if lang == 'en-US' else portal_config.logout_msg_de
    assert logout.inner_text() == logout_msg
    logout.click()
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert not sessions


def test_login_not_possible_with_deleted_user(keycloak_config, portal_login_via_keycloak, portal_config, udm):
    _dn, username = udm.create_user()
    # login
    page = portal_login_via_keycloak(username, 'univention')
    users = keycloak_get_request(keycloak_config, 'realms/ucs/users', params={'search': username})
    assert len(users) == 1
    assert users[0]['username'] == username
    # logout
    page.click(f"[id={portal_config.header_menu_id}]")
    page.click(f"[id={portal_config.logout_button_id}]")
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert not sessions

    udm.remove_user(username)

    # user has been deleted, login should be denied
    assert portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.wrong_password_msg)

    # check that user is no longer available in keycloak
    users = keycloak_get_request(keycloak_config, 'realms/ucs/users', params={'search': username})
    assert len(users) == 0


def test_account_expired(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    yesterday = datetime.now() - timedelta(days=1)
    username = udm.create_user(userexpiry=yesterday.isoformat()[:10])[1]
    portal_login_via_keycloak(username, 'univentionA', fails_with=keycloak_config.wrong_password_msg)
    portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.account_expired_msg)


def test_account_disabled(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    dn, username = udm.create_user()
    ldap = get_ldap_connection(primary=True)
    changes = [('shadowExpire', [''], [b'1'])]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    portal_login_via_keycloak(username, 'univentionA', fails_with=keycloak_config.wrong_password_msg)
    portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.account_disabled_msg)
