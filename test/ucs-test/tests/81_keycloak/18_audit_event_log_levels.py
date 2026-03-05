#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test audit event log level settings
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os
import re

import pytest
from utils import portal_logout, run_command


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_audit_event_log_levels(change_app_setting, portal_login_via_keycloak, udm, portal_config):
    """Test that audit events are logged at the configured levels"""
    change_app_setting('keycloak', {
        'keycloak/audit/events/success/level': 'INFO',
        'keycloak/audit/events/error/level': 'ERROR',
    })

    # Test successful login
    username = udm.create_user()[1]
    page = portal_login_via_keycloak(username, 'univention')
    logs = run_command(['docker', 'logs', '--since', '5s', 'keycloak'])
    login_pattern = r'INFO.*\[org\.keycloak\.events\].*type="LOGIN"'
    assert re.search(login_pattern, logs), f'Expected INFO level LOGIN event in logs, got:\n{logs}'

    # Logout before testing failed login
    portal_logout(page, portal_config)

    # Test failed login
    username2 = udm.create_user()[1]
    portal_login_via_keycloak(
        username2,
        'wrong_password',
        fails_with='The authentication has failed, please login again.',
    )
    logs = run_command(['docker', 'logs', '--since', '5s', 'keycloak'])
    login_error_pattern = r'ERROR.*\[org\.keycloak\.events\].*type="LOGIN_ERROR"'
    assert re.search(login_error_pattern, logs), f'Expected ERROR level LOGIN_ERROR event in logs, got:\n{logs}'
