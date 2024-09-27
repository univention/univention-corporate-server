#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test portal SSO login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import json
import os
import time
from datetime import datetime, timedelta

import pytest
from utils import (
    keycloak_delete_session, keycloak_get_request, keycloak_login, keycloak_password_change, keycloak_sessions_by_user,
    portal_logout, run_command,
)

from univention.config_registry import handler_set
from univention.lib.umc import Unauthorized
from univention.testing import ucr as testing_ucr
from univention.testing.umc import Client
from univention.testing.utils import (
    get_ldap_connection, package_installed, wait_for_listener_replication, wait_for_replication_and_postrun,
)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_login(portal_login_via_keycloak, udm, protocol):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univention', protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_login_wrong_password_fails(portal_login_via_keycloak, keycloak_config, udm, protocol):
    username = udm.create_user()[1]
    assert portal_login_via_keycloak(username, 'univentionWrong', fails_with=keycloak_config.wrong_password_msg, protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_login_disabled_fails(portal_login_via_keycloak, keycloak_config, udm, protocol):
    username = udm.create_user(disabled=1)[1]
    assert portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.wrong_password_msg, protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_pwdChangeNextLogin(portal_login_via_keycloak, keycloak_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99', protocol=protocol)
    assert Client(username=username, password='Univention.99')
    with pytest.raises(Unauthorized):
        Client(username=username, password='univention')


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_wrong_old_password_fails(portal_login_via_keycloak, keycloak_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    assert portal_login_via_keycloak(username, 'univentionBAD', fails_with=keycloak_config.wrong_password_msg, protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
@pytest.mark.skipif(package_installed('univention-samba4'), reason='Missing software: univention-samba4')
def test_password_change_same_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(username, 'univention', new_password='univention', fails_with='Changing password failed. The password was already used.', protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_new_password_too_short_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='a',
        fails_with='Changing password failed. The password is too short.',
        protocol=protocol,
    )


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
@pytest.mark.skipif(package_installed('univention-samba4'), reason='Missing software: univention-samba4')
def test_password_change_confirm_new_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    portal_login_via_keycloak(
        username,
        'univention',
        new_password='univention',
        new_password_confirm='univention1',
        fails_with="Passwords don't match.",
        protocol=protocol,
    )


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_empty_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    username = udm.create_user(pwdChangeNextLogin=1)[1]
    page = portal_login_via_keycloak(username, 'univention', verify_login=False, protocol=protocol)
    # just click the button without old or new passwords
    page.click(f"[id='{keycloak_config.password_change_button_id}']")
    error = page.locator(keycloak_config.password_update_error_css_selector.replace("[class='", ".").replace("']", "").replace(" ", "."))
    assert error.inner_text() == 'Please specify password.', error.inner_text()


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_after_second_try(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    username = udm.create_user(password="univention", pwdChangeNextLogin=1)[1]
    page = portal_login_via_keycloak(
        username,
        password='univention',
        new_password='u',
        fails_with='Changing password failed. The password is too short.',
        protocol=protocol,
    )
    keycloak_password_change(page, keycloak_config, username, 'univention', 'Univention.99', 'Univention.99')
    assert Client(username=username, password='Univention.99')


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_password_change_expired_shadowLastChange(portal_login_via_keycloak, keycloak_config, udm, protocol):
    ldap = get_ldap_connection(primary=True)
    dn, username = udm.create_user()
    changes = [
        ('shadowMax', [''], [b'2']),
        ('shadowLastChange', [''], [b'1000']),
    ]
    ldap.modify(dn, changes)
    wait_for_replication_and_postrun()
    assert portal_login_via_keycloak(username, 'univention', new_password='Univention.99', protocol=protocol)
    assert Client(username=username, password='Univention.99')
    with pytest.raises(Unauthorized):
        Client(username=username, password='univention')


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_logout(portal_login_via_keycloak, portal_config, keycloak_config, udm, protocol):
    username = udm.create_user()[1]
    page = portal_login_via_keycloak(username, 'univention', protocol=protocol)
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert sessions

    portal_logout(page, portal_config)
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert not sessions


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_login_not_possible_with_deleted_user(keycloak_config, portal_login_via_keycloak, portal_config, udm, protocol):
    _dn, username = udm.create_user()
    # login
    page = portal_login_via_keycloak(username, 'univention', protocol=protocol)
    users = keycloak_get_request(keycloak_config, 'realms/ucs/users', params={'search': username})
    assert len(users) == 1
    assert users[0]['username'] == username
    # logout
    portal_logout(page, portal_config)
    sessions = keycloak_sessions_by_user(keycloak_config, username)
    assert not sessions

    udm.remove_user(username)

    # user has been deleted, login should be denied
    assert portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.wrong_password_msg)

    # check that user is no longer available in keycloak
    users = keycloak_get_request(keycloak_config, 'realms/ucs/users', params={'search': username})
    assert len(users) == 0


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_account_expired(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    yesterday = datetime.now() - timedelta(days=1)
    username = udm.create_user(userexpiry=yesterday.isoformat()[:10])[1]
    portal_login_via_keycloak(username, 'univentionA', fails_with=keycloak_config.wrong_password_msg, protocol=protocol)
    portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.account_expired_msg, protocol=protocol)


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_account_disabled(portal_login_via_keycloak, keycloak_config, portal_config, udm, protocol):
    dn, username = udm.create_user()
    ldap = get_ldap_connection(primary=True)
    changes = [('shadowExpire', [''], [b'1'])]
    ldap.modify(dn, changes)
    wait_for_listener_replication()
    portal_login_via_keycloak(username, 'univentionA', fails_with=keycloak_config.wrong_password_msg, protocol=protocol)
    portal_login_via_keycloak(username, 'univention', fails_with=keycloak_config.account_disabled_msg, protocol=protocol)


@pytest.mark.is_keycloak()
@pytest.mark.parametrize('protocol', ['login', 'saml', 'oidc'])
def test_portal_login_button(portal_config, protocol, ucr, page, keycloak_config, udm):
    try:
        _, username = udm.create_user()
        with testing_ucr.UCSTestConfigRegistry():
            handler_set([f'portal/auth-mode={protocol}'])
            run_command(['service', 'univention-portal-server', 'restart'])
            run_command(['service', 'univention-management-console-server', 'restart'])
            time.sleep(10)
            page.goto(portal_config.url)
            page.get_by_role('button', name='Menu').click()
            page.get_by_role('button', name='Login').click()
            page.get_by_label('Username or email')
            assert protocol in page.url
            if protocol == 'login':
                page.get_by_label('Username').fill(username)
                page.get_by_label('Password', exact=True).fill('univention')
                page.get_by_role('button', name='Login').click()
            else:
                keycloak_login(page=page, username=username, password='univention', keycloak_config=keycloak_config)
            page.get_by_role('button', name='Menu').click()
            page.get_by_text(username, exact=True).click()
    finally:
        run_command(['service', 'univention-portal-server', 'restart'])
        run_command(['service', 'univention-management-console-server', 'restart'])
        time.sleep(10)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='needs to change client config, only with keycloak.secret present')
def test_oidc_session_logout_after_access_token_invalid_issue_ucs_2401(portal_config, portal_login_via_keycloak, keycloak_config, portal_login_via_keycloak_custom_page, admin_account):
    client_id = f'https://{portal_config.fqdn}/univention/oidc/'
    client_config = json.loads(run_command(['univention-keycloak', 'oidc/rp', 'get', '--client-id', client_id, '--json', '--all']))[0]
    username = admin_account.username
    password = admin_account.bindpw
    access_token_lifespan = 10
    try:
        # enable frontchannel and set access token lifespan
        changes = {
            'frontchannelLogout': True,
            'attributes': {
                'access.token.lifespan': access_token_lifespan,
            }
        }
        run_command(['univention-keycloak', 'oidc/rp', 'update', client_id, json.dumps(changes)])
        page = portal_login_via_keycloak(username, password, protocol='oidc')
        tile = 'App Center'
        page.get_by_role('link', name=f'{tile} iFrame').click()
        # close the tab
        page.locator('[data-test="close-tab-1"]').click()
        # now delete the session in keycloak and wait for access.token.lifespan,
        # opening the module again should bring us to the login screen
        for session in keycloak_sessions_by_user(keycloak_config, username):
            keycloak_delete_session(keycloak_config, session['id'])
        assert keycloak_sessions_by_user(keycloak_config, username) == []
        time.sleep(access_token_lifespan + 1)
        page.get_by_role('link', name=f'{tile} iFrame').click()
        # we expect a login page
        portal_login_via_keycloak_custom_page(page, username, password, protocol='oidc')
    finally:
        # revert to original configuration
        changes = {
            'frontchannelLogout': client_config['frontchannelLogout'],
            'attributes': {
                'access.token.lifespan': client_config['attributes']['access.token.lifespan']
            }
        }
        run_command(['univention-keycloak', 'oidc/rp', 'update', client_id, json.dumps(changes)])
