#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test univention-keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os

import pytest
from utils import run_command


LEGACY_APP_AUTHORIZATION_NAME = "browser flow with legacy app authorization"
EXPECTED_EXECUTIONS = [
    {"requirement": "REQUIRED", "displayName": "Normal Login (browser legacy app authorization)", "configurable": False, "authenticationFlow": True, "level": 0, "index": 0},
    {"requirement": "ALTERNATIVE", "displayName": "Cookie", "configurable": False, "providerId": "auth-cookie", "level": 1, "index": 0},
    {"requirement": "ALTERNATIVE", "displayName": "Kerberos", "configurable": False, "providerId": "auth-spnego", "level": 1, "index": 1},
    {"requirement": "ALTERNATIVE", "displayName": "Identity Provider Redirector", "configurable": True, "providerId": "identity-provider-redirector", "level": 1, "index": 2},
    {"requirement": "ALTERNATIVE", "displayName": "forms (browser flow with legacy app authorization)", "configurable": False, "authenticationFlow": True, "level": 1, "index": 3},
    {"requirement": "REQUIRED", "displayName": "Username Password Form", "configurable": False, "providerId": "auth-username-password-form", "level": 2, "index": 0},
    {"requirement": "CONDITIONAL", "displayName": "Browser - Conditional OTP (browser flow with legacy app authorization)", "configurable": False, "authenticationFlow": True, "level": 2, "index": 1},
    {"requirement": "REQUIRED", "displayName": "Condition - user configured", "configurable": False, "providerId": "conditional-user-configured", "level": 3, "index": 0},
    {"requirement": "REQUIRED", "displayName": "OTP Form", "configurable": False, "providerId": "auth-otp-form", "level": 3, "index": 1},
    {"requirement": "REQUIRED", "displayName": "Univention App Authenticator", "configurable": True, "providerId": "univention-app-authenticator", "level": 0, "index": 1},
]


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_univention_keycloak_legacy_flow_config(keycloak_administrator_connection):
    flows = keycloak_administrator_connection.get_authentication_flows()
    remove = False
    if not any(x["alias"] == LEGACY_APP_AUTHORIZATION_NAME for x in flows):
        remove = True
        run_command(["univention-keycloak", "legacy-authentication-flow", "create"])

    try:
        executions = keycloak_administrator_connection.get_authentication_flow_executions(LEGACY_APP_AUTHORIZATION_NAME)
        for e in executions:
            del e["id"]
            del e["requirementChoices"]
            if "flowId" in e:
                del e["flowId"]
        assert executions == EXPECTED_EXECUTIONS
    finally:
        if remove:
            run_command(["univention-keycloak", "legacy-authentication-flow", "delete"])
            flows = keycloak_administrator_connection.get_authentication_flows()
            assert not any(x["alias"] == LEGACY_APP_AUTHORIZATION_NAME for x in flows)
