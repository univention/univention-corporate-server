#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal SSO login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

from datetime import datetime, timedelta

import pytest
from utils import _, keycloak_get_request, keycloak_password_change, keycloak_sessions_by_user, run_command

from univention.lib.umc import Unauthorized
from univention.testing.umc import Client
from univention.testing.utils import (
    get_ldap_connection, package_installed, wait_for_listener_replication, wait_for_s4connector_replication,
)


def test_login(portal_login_via_keycloak, udm):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univention')


def test_login_wrong_password_fails(portal_login_via_keycloak, udm):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univentionWrong', fails_with=_('Invalid username or password.'))


def test_login_disabled_fails(portal_login_via_keycloak, udm):
    username = udm.create_user(disabled=1)[1]
    assert portal_login_via_keycloak(username, 'univention', fails_with=_('Invalid username or password.'))


def test_password_change_pwdChangeNextLogin(portal_login_via_keycloak, udm):
    username = udm.create_user(password='Univention.12', pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'Univention.12', new_password='Univention.99')
    wait_for_listener_replication()
    if package_installed('univention-samba4'):
        wait_for_s4connector_replication()
    assert Client(username=username, password='Univention.99')
    with pytest.raises(Unauthorized):
        Client(username=username, password='univention')


def test_password_change_wrong_old_password_fails(portal_login_via_keycloak, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'univentionBAD', fails_with=_('Invalid username or password.'))


@pytest.mark.skipif(package_installed('univention-samba4'), reason='Univention Samba 4 is and passwordhistory is not active')
def test_password_change_same_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(username, 'univention', new_password='univention', fails_with=_('Changing password failed. The password was already used.'))


def test_password_change_new_password_too_short_fails(portal_login_via_keycloak, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    if package_installed('univention-samba4'):
        error_msg = _('Changing password failed. The password is too short. The password must consist of at least 8 characters.')
    else:
        error_msg = _('Changing password failed. The password is too short.')
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='a',
        fails_with=error_msg,
    )


def test_password_change_confirm_new_passwords_fails(portal_login_via_keycloak, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='univention',
        new_password_confirm='univention1',
        fails_with=_("Passwords don't match."),
    )


def test_password_change_empty_passwords_fails(portal_login_via_keycloak, keycloak_config, udm):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    page = portal_login_via_keycloak(username, 'univention', verify_login=False)
    # just click the button without old or new passwords
    page.click(f"[id='{keycloak_config.password_change_button_id}']")
    error = page.locator(keycloak_config.password_update_error_css_selector.replace("[class='", ".").replace("']", "").replace(" ", "."))
    assert error.inner_text() == _('Please specify password.'), error.inner_text()


def test_password_change_after_second_try(portal_login_via_keycloak, keycloak_config, udm):
    error_msg = _('Changing password failed. The password was already used.')
    orig_history_setting = None
    if package_installed('univention-samba4'):
        error_msg = _('Changing password failed. The password was already used. Choose a password which does not match any of your last 3 passwords.')
        for line in run_command(['samba-tool', 'domain', 'passwordsettings', 'show']).split('\n'):
            if 'Password history length:' in line:
                orig_history_setting = line.split(':')[1].strip()
        run_command(['samba-tool', 'domain', 'passwordsettings', 'set', '--history-length=3'])
    try:
        username = udm.create_user(pwdChangeNextLogin=1, password='sdh78§$%kjJKJK')[1]
        page = portal_login_via_keycloak(
            username,
            'sdh78§$%kjJKJK',
            new_password='sdh78§$%kjJKJK',
            fails_with=error_msg,
        )
        keycloak_password_change(page, keycloak_config, 'sdh78§$%kjJKJK', 'Univention.99', 'Univention.99')
        wait_for_listener_replication()
        if package_installed('univention-samba4'):
            wait_for_s4connector_replication()
        assert Client(username=username, password='Univention.99')
    finally:
        if package_installed('univention-samba4') and orig_history_setting:
            run_command(['samba-tool', 'domain', 'passwordsettings', 'set', f'--history-length={orig_history_setting}'])


@pytest.mark.skipif(package_installed('univention-samba4'), reason='Univention Samba 4 is installed and wont react to shadowLastChange.')
def test_password_change_expired_shadowLastChange(portal_login_via_keycloak, udm):
    ldap = get_ldap_connection(primary=True)
    dn, username = udm.create_user()
    changes = [
        ('shadowMax', [''], [b'2']),
        ('shadowLastChange', [''], [b'1000']),
    ]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    # Since UCS 5.2 PAM auth/account is solely done by krb5, no more
    # shadow stuff. Just shadowMax + shadowLastChange will not trigger a
    # password change in PAM/UMC.
    # Keycloak still checks this case and presents a pw change dialog,
    # but the password is not changed. Check here if keycloak
    # presents a pw dialog.
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99')


def test_password_change_expired_krb5PasswordEnd_and_shadowLastChange(portal_login_via_keycloak, udm):
    ldap = get_ldap_connection(primary=True)
    dn, username = udm.create_user()
    changes = [
        ('krb5PasswordEnd', [''], [b'20240410000000Z']),
        ('shadowMax', [''], [b'2']),
        ('shadowLastChange', [''], [b'1000']),
        ('sambaPwdLastSet', [''], [b'0']),
    ]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99')
    wait_for_listener_replication()
    if package_installed('univention-samba4'):
        wait_for_s4connector_replication()
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
    assert logout.inner_text() == _('LOGOUT')
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
    #
    # see https://forge.univention.org/bugzilla/show_bug.cgi?id=55903
    # we can't logon with that deleted user, just check for that
    # generic error message
    # if this bug is fixed, just
    #   assert portal_login_via_keycloak(username, "univention", fails_with=_('Invalid username or password.'))
    # should do it
    page = portal_login_via_keycloak(username, 'univention', verify_login=False)
    error = page.locator("#kc-error-message")
    assert error.inner_text() == _('Unexpected error when handling authentication request to identity provider.')

    # check that user is no longer available in keycloak
    users = keycloak_get_request(keycloak_config, 'realms/ucs/users', params={'search': username})
    assert len(users) == 0


def test_account_expired(portal_login_via_keycloak, udm):
    yesterday = datetime.now() - timedelta(days=1)
    username = udm.create_user(userexpiry=yesterday.isoformat()[:10])[1]
    portal_login_via_keycloak(username, 'univentionA', fails_with=_('Invalid username or password.'))
    portal_login_via_keycloak(username, 'univention', fails_with=_('The account has expired.'))


def test_account_disabled(portal_login_via_keycloak, udm):
    dn, username = udm.create_user()
    ldap = get_ldap_connection(primary=True)
    changes = [('shadowExpire', [''], [b'1'])]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    portal_login_via_keycloak(username, 'univentionA', fails_with=_('Invalid username or password.'))
    portal_login_via_keycloak(username, 'univention', fails_with=_('The account is disabled.'))
