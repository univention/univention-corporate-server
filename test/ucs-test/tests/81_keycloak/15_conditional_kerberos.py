#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test conditional kerberos authentication
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
from utils import kerberos_auth, run_command


CONDITION_KERBEROS_FLOW_NAME = 'foo'
EXPECTED_EXECUTIONS = [{'requirement': 'REQUIRED', 'displayName': 'Univention Condition - IP subnet', 'alias': 'ipaddressconfig', 'configurable': True, 'providerId': 'univention-condition-ipaddress', 'level': 2, 'index': 0, 'priority': 0}, {'requirement': 'CONDITIONAL', 'displayName': 'Browser - Conditional OTP (foo)', 'configurable': False, 'authenticationFlow': True, 'level': 1, 'index': 1, 'priority': 20}, {'requirement': 'ALTERNATIVE', 'displayName': 'Kerberos alternative foo', 'configurable': False, 'authenticationFlow': True, 'level': 0, 'index': 1, 'priority': 20}, {'requirement': 'CONDITIONAL', 'displayName': 'Kerberos condition foo', 'configurable': False, 'authenticationFlow': True, 'level': 1, 'index': 0, 'priority': 0}, {'requirement': 'ALTERNATIVE', 'displayName': 'forms (foo)', 'configurable': False, 'authenticationFlow': True, 'level': 0, 'index': 3, 'priority': 30}, {'requirement': 'REQUIRED', 'displayName': 'Condition - user configured', 'configurable': False, 'providerId': 'conditional-user-configured', 'level': 2, 'index': 0, 'priority': 10}, {'requirement': 'ALTERNATIVE', 'displayName': 'Cookie', 'configurable': False, 'providerId': 'auth-cookie', 'level': 0, 'index': 0, 'priority': 10}, {'requirement': 'ALTERNATIVE', 'displayName': 'Kerberos', 'configurable': False, 'providerId': 'auth-spnego', 'level': 2, 'index': 1, 'priority': 1}, {'requirement': 'REQUIRED', 'displayName': 'OTP Form', 'configurable': False, 'providerId': 'auth-otp-form', 'level': 2, 'index': 1, 'priority': 20}, {'requirement': 'REQUIRED', 'displayName': 'Username Password Form', 'configurable': False, 'providerId': 'auth-username-password-form', 'level': 1, 'index': 0, 'priority': 10}, {'requirement': 'ALTERNATIVE', 'displayName': 'Identity Provider Redirector', 'configurable': True, 'providerId': 'identity-provider-redirector', 'level': 0, 'index': 2, 'priority': 25}]


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_univention_keycloak_legacy_flow_config(keycloak_administrator_connection, ucr):
    flows = keycloak_administrator_connection.get_authentication_flows()
    if not any(x['alias'] == CONDITION_KERBEROS_FLOW_NAME for x in flows):
        run_command(['univention-keycloak', 'conditional-krb-authentication-flow', 'create', '--allowed-ip=10.205.0.0/16', '--name=foo'])
        executions = keycloak_administrator_connection.get_authentication_flow_executions(CONDITION_KERBEROS_FLOW_NAME)
        for e in executions:
            del e['id']
            del e['requirementChoices']
            if 'description' in e:
                del e['description']
            if 'flowId' in e:
                del e['flowId']
            if 'authenticationConfig' in e:
                del e['authenticationConfig']
        sorted_executions = sorted(executions, key=lambda ele: sorted(ele.items()))
        sorted_expected_executions = sorted(EXPECTED_EXECUTIONS, key=lambda ele: sorted(ele.items()))
        print(sorted_executions)
        assert sorted_executions == sorted_expected_executions


KERBEROS_FLOWS = {"allowed": ['univention-keycloak', 'conditional-krb-authentication-flow', 'create', '--name=allowed', '--allowed-ip=0.0.0.0/0'], "notallowed": ['univention-keycloak', 'conditional-krb-authentication-flow', 'create', '--name=notallowed', '--allowed-ip=300.0.0.0/24']}


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
@pytest.mark.parametrize('allowed', ["allowed", "notallowed"])
def test_kerberos_authentication(keycloak_administrator_connection, portal_login_via_keycloak, ucr, protocol, portal_config, allowed):
    flow = KERBEROS_FLOWS["allowed"] if allowed == "allowed" else KERBEROS_FLOWS["notallowed"]
    flows = keycloak_administrator_connection.get_authentication_flows()
    if not any(x['alias'] == allowed for x in flows):
        run_command(flow)

    oidc_client = f'https://{portal_config.fqdn}/univention/oidc/'
    saml_client = f'https://{portal_config.fqdn}/univention/saml/metadata'
    try:
        run_command(['univention-keycloak', 'client-auth-flow', '--clientid', saml_client, '--auth-flow', allowed])
        run_command(['univention-keycloak', 'client-auth-flow', '--clientid', oidc_client, '--auth-flow', allowed])
        if allowed == "allowed":
            kerberos_auth(portal_login_via_keycloak, ucr, protocol, portal_config)
        else:
            with pytest.raises((AttributeError, KeyError)):
                kerberos_auth(portal_login_via_keycloak, ucr, protocol, portal_config)
    finally:
        run_command(['univention-keycloak', 'client-auth-flow', '--clientid', saml_client, '--auth-flow', "browser"])
        run_command(['univention-keycloak', 'client-auth-flow', '--clientid', oidc_client, '--auth-flow', "browser"])
