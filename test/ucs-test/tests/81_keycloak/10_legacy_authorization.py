#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
import requests
from debian.debian_support import Version
from playwright.sync_api import expect
from utils import _, get_language_code, run_command

from univention.udm import UDM


LEGACY_APP_AUTHORIZATION_NAME = 'browser flow with legacy app authorization'
OLD_EXPECTED_EXECUTIONS = [
    {
        'requirement': 'REQUIRED',
        'displayName': 'Normal Login (browser legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 0,
        'index': 0,
        'priority': 1,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Cookie',
        'configurable': False,
        'providerId': 'auth-cookie',
        'level': 1,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Kerberos',
        'configurable': False,
        'providerId': 'auth-spnego',
        'level': 1,
        'index': 1,
        'priority': 20,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Identity Provider Redirector',
        'configurable': True,
        'providerId': 'identity-provider-redirector',
        'level': 1,
        'index': 2,
        'priority': 25,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'forms (browser flow with legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 1,
        'index': 4,
        'priority': 30,
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Username Password Form',
        'configurable': False,
        'providerId': 'auth-username-password-form',
        'level': 2,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'CONDITIONAL',
        'displayName': 'Browser - Conditional OTP (browser flow with legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 2,
        'index': 1,
        'priority': 20,
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Condition - user configured',
        'configurable': False,
        'providerId': 'conditional-user-configured',
        'level': 3,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'OTP Form',
        'configurable': False,
        'providerId': 'auth-otp-form',
        'level': 3,
        'index': 2,
        'priority': 30,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Organization Identity-First Login',
        'index': 1,
        'level': 3,
        'priority': 20,
        'providerId': 'organization',
        'configurable': True,
    },
    {
        'configurable': False,
        'displayName': 'Condition - user configured',
        'index': 0,
        'level': 3,
        'priority': 10,
        'providerId': 'conditional-user-configured',
        'requirement': 'REQUIRED',
    },
    {
        'authenticationFlow': True,
        'configurable': False,
        'displayName': 'Organization (browser flow with legacy app authorization)',
        'index': 3,
        'level': 1,
        'priority': 26,
        'requirement': 'ALTERNATIVE',
    },
    {
        'authenticationFlow': True,
        'configurable': False,
        'displayName': 'Browser - Conditional Organization (browser flow with legacy app authorization)',
        'index': 0,
        'level': 2,
        'priority': 10,
        'requirement': 'CONDITIONAL',
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Univention App Authenticator',
        'configurable': True,
        'providerId': 'univention-app-authenticator',
        'level': 0,
        'index': 1,
        'priority': 2,
    },
]
EXPECTED_EXECUTIONS = [
    {
        'requirement': 'REQUIRED',
        'displayName': 'Normal Login (browser legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 0,
        'index': 0,
        'priority': 1,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Cookie',
        'configurable': False,
        'providerId': 'auth-cookie',
        'level': 1,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Kerberos',
        'configurable': False,
        'providerId': 'auth-spnego',
        'level': 1,
        'index': 1,
        'priority': 20,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Identity Provider Redirector',
        'configurable': True,
        'providerId': 'identity-provider-redirector',
        'level': 1,
        'index': 2,
        'priority': 25,
    },
    {
        'configurable': True,
        'displayName': 'Condition - credential',
        'index': 1,
        'level': 3,
        'priority': 20,
        'providerId': 'conditional-credential',
        'requirement': 'REQUIRED',
    },
    {
        'configurable': False,
        'displayName': 'WebAuthn Authenticator',
        'index': 3,
        'level': 3,
        'priority': 40,
        'providerId': 'webauthn-authenticator',
        'requirement': 'DISABLED',
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'forms (browser flow with legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 1,
        'index': 4,
        'priority': 30,
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Username Password Form',
        'configurable': False,
        'providerId': 'auth-username-password-form',
        'level': 2,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'CONDITIONAL',
        'displayName': 'Browser - Conditional 2FA (browser flow with legacy app authorization)',
        'configurable': False,
        'authenticationFlow': True,
        'level': 2,
        'index': 1,
        'priority': 20,
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Condition - user configured',
        'configurable': False,
        'providerId': 'conditional-user-configured',
        'level': 3,
        'index': 0,
        'priority': 10,
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'OTP Form',
        'configurable': False,
        'providerId': 'auth-otp-form',
        'level': 3,
        'index': 2,
        'priority': 30,
    },
    {
        'configurable': False,
        'displayName': 'Recovery Authentication Code Form',
        'index': 4,
        'level': 3,
        'priority': 50,
        'providerId': 'auth-recovery-authn-code-form',
        'requirement': 'DISABLED',
    },
    {
        'requirement': 'ALTERNATIVE',
        'displayName': 'Organization Identity-First Login',
        'index': 1,
        'level': 3,
        'priority': 20,
        'providerId': 'organization',
        'configurable': True,
    },
    {
        'configurable': False,
        'displayName': 'Condition - user configured',
        'index': 0,
        'level': 3,
        'priority': 10,
        'providerId': 'conditional-user-configured',
        'requirement': 'REQUIRED',
    },
    {
        'authenticationFlow': True,
        'configurable': False,
        'displayName': 'Organization (browser flow with legacy app authorization)',
        'index': 3,
        'level': 1,
        'priority': 26,
        'requirement': 'ALTERNATIVE',
    },
    {
        'authenticationFlow': True,
        'configurable': False,
        'displayName': 'Browser - Conditional Organization (browser flow with legacy app authorization)',
        'index': 0,
        'level': 2,
        'priority': 10,
        'requirement': 'CONDITIONAL',
    },
    {
        'requirement': 'REQUIRED',
        'displayName': 'Univention App Authenticator',
        'configurable': True,
        'providerId': 'univention-app-authenticator',
        'level': 0,
        'index': 1,
        'priority': 2,
    },
]


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_univention_keycloak_legacy_flow_config(keycloak_administrator_connection, ucr):
    kc_app_version = ucr.get('appcenter/apps/keycloak/version')
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
        sorted_executions = sorted(executions, key=lambda ele: sorted(ele.items()))
        sorted_expected_executions = sorted(EXPECTED_EXECUTIONS if Version(kc_app_version) >= Version("26.3.1") else OLD_EXPECTED_EXECUTIONS, key=lambda ele: sorted(ele.items()))
        assert sorted_executions == sorted_expected_executions
    finally:
        if remove:
            run_command(['univention-keycloak', 'legacy-authentication-flow', 'delete'])
            flows = keycloak_administrator_connection.get_authentication_flows()
            assert not any(x['alias'] == LEGACY_APP_AUTHORIZATION_NAME for x in flows)


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_legacy_authorization_saml(legacy_authorization_setup_saml, keycloak_config, keycloak_administrator_connection, portal_login_via_keycloak):
    # verify logon not possible
    page = portal_login_via_keycloak(legacy_authorization_setup_saml.user, 'univention', verify_login=False)
    expect(page.locator('#kc-content-wrapper'), 'kc-content-wrapper not visible').to_be_visible()
    assert _('Access forbidden.') in page.content()

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
        headers={'Accept-Language': get_language_code()},
        data={
            'client_id': legacy_authorization_setup_oidc.client,
            'client_secret': legacy_authorization_setup_oidc.client_secret,
            'username': legacy_authorization_setup_oidc.user,
            'password': legacy_authorization_setup_oidc.password,
            'grant_type': 'password',
        },
    )
    assert _('Access forbidden.') in resp.text

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
