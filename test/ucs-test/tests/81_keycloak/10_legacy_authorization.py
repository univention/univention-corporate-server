#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
import requests
from utils import run_command

from univention.udm import UDM


LEGACY_APP_AUTHORIZATION_NAME = 'browser flow with legacy app authorization'
EXPECTED_EXECUTIONS = [
    {'requirement': 'REQUIRED', 'displayName': 'Normal Login (browser legacy app authorization)', 'configurable': False, 'authenticationFlow': True, 'level': 0, 'index': 0},
    {'requirement': 'ALTERNATIVE', 'displayName': 'Cookie', 'configurable': False, 'providerId': 'auth-cookie', 'level': 1, 'index': 0},
    {'requirement': 'ALTERNATIVE', 'displayName': 'Kerberos', 'configurable': False, 'providerId': 'auth-spnego', 'level': 1, 'index': 1},
    {'requirement': 'ALTERNATIVE', 'displayName': 'Identity Provider Redirector', 'configurable': True, 'providerId': 'identity-provider-redirector', 'level': 1, 'index': 2},
    {'requirement': 'ALTERNATIVE', 'displayName': 'forms (browser flow with legacy app authorization)', 'configurable': False, 'authenticationFlow': True, 'level': 1, 'index': 3},
    {'requirement': 'REQUIRED', 'displayName': 'Username Password Form', 'configurable': False, 'providerId': 'auth-username-password-form', 'level': 2, 'index': 0},
    {
        'requirement': 'CONDITIONAL',
        'displayName': 'Browser - Conditional OTP (browser flow with legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 2,
        'index': 1,
    },
    {'requirement': 'REQUIRED', 'displayName': 'Condition - user configured', 'configurable': False, 'providerId': 'conditional-user-configured', 'level': 3, 'index': 0},
    {'requirement': 'REQUIRED', 'displayName': 'OTP Form', 'configurable': False, 'providerId': 'auth-otp-form', 'level': 3, 'index': 1},
    {'requirement': 'REQUIRED', 'displayName': 'Univention App Authenticator', 'configurable': True, 'providerId': 'univention-app-authenticator', 'level': 0, 'index': 1},
]


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_univention_keycloak_legacy_flow_config(keycloak_administrator_connection):
    flows = keycloak_administrator_connection.get_authentication_flows()
    remove = False
    if not any(x['alias'] == LEGACY_APP_AUTHORIZATION_NAME for x in flows):
        remove = True
        run_command(['univention-keycloak', 'legacy-authentication-flow', 'create'])

    try:
        executions = keycloak_administrator_connection.get_authentication_flow_executions(LEGACY_APP_AUTHORIZATION_NAME)
        for e in executions:
            del e['id']
            del e['requirementChoices']
            if 'description' in e:
                del e['description']
            if 'flowId' in e:
                del e['flowId']
        assert executions == EXPECTED_EXECUTIONS
    finally:
        if remove:
            run_command(['univention-keycloak', 'legacy-authentication-flow', 'delete'])
            flows = keycloak_administrator_connection.get_authentication_flows()
            assert not any(x['alias'] == LEGACY_APP_AUTHORIZATION_NAME for x in flows)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_legacy_authorization_saml(legacy_authorization_setup_saml, keycloak_config, keycloak_administrator_connection, portal_login_via_keycloak):
    # verify logon not possible
    driver = portal_login_via_keycloak(legacy_authorization_setup_saml.user, 'univention', verify_login=False)
    assert any(txt in driver.page_source for txt in ['You do not have the needed privileges to access', 'Zugriff verboten'])

    # add user to group
    udm = UDM.admin().version(2)
    udm_groups = udm.get('groups/group')
    group_obj = udm_groups.get(legacy_authorization_setup_saml.group_dn)
    group_obj.props.users.append(legacy_authorization_setup_saml.user_dn)
    group_obj.save()

    # delete user in keycloak to "update" membership cache
    user_id = keycloak_administrator_connection.get_user_id(legacy_authorization_setup_saml.user)
    keycloak_administrator_connection.delete_user(user_id)

    # verify logon
    assert portal_login_via_keycloak(legacy_authorization_setup_saml.user, 'univention')


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_legacy_authorization_oidc(legacy_authorization_setup_oidc, keycloak_config, keycloak_administrator_connection):
    # verify logon not possible
    resp = requests.post(
        keycloak_config.token_url,
        data={
            'client_id': legacy_authorization_setup_oidc.client,
            'client_secret': legacy_authorization_setup_oidc.client_secret,
            'username': legacy_authorization_setup_oidc.user,
            'password': legacy_authorization_setup_oidc.password,
            'grant_type': 'password',
        },
    )
    assert resp.json().get('error') == 'unknown_error'  # https://github.com/keycloak/keycloak/issues/13368

    # add user to group
    udm = UDM.admin().version(2)
    udm_groups = udm.get('groups/group')
    group_obj = udm_groups.get(legacy_authorization_setup_oidc.group_dn)
    group_obj.props.users.append(legacy_authorization_setup_oidc.user_dn)
    group_obj.save()

    # delete user in keycloak to "update" membership cache
    user_id = keycloak_administrator_connection.get_user_id(legacy_authorization_setup_oidc.user)
    keycloak_administrator_connection.delete_user(user_id)

    # verify logon
    resp = requests.post(
        keycloak_config.token_url,
        data={
            'client_id': legacy_authorization_setup_oidc.client,
            'client_secret': legacy_authorization_setup_oidc.client_secret,
            'username': legacy_authorization_setup_oidc.user,
            'password': legacy_authorization_setup_oidc.password,
            'grant_type': 'password',
        },
    )
    assert resp.json().get('access_token')
