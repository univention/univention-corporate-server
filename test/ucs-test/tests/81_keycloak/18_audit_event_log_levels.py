#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test audit event log level settings
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import os
import re

import pytest
import requests
from utils import run_command

from univention.testing.utils import wait_for_listener_replication


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_audit_event_log_levels(change_app_setting, keycloak_session, keycloak_admin, keycloak_secret, keycloak_config, udm):
    """
    Test that audit events are logged at the configured levels.

    Uses direct token endpoint calls instead of browser-based login to avoid
    fragility from container recreation during app setting changes.
    """
    change_app_setting('keycloak', {
        'keycloak/log/level': 'INFO',
        'keycloak/audit/events/success/level': 'INFO',
        'keycloak/audit/events/error/level': 'ERROR',
    })
    admin_conn = keycloak_session(keycloak_admin, keycloak_secret)

    # Enable user events on the ucs realm
    realm = admin_conn.get_realm('ucs')
    original_events_enabled = realm.get('eventsEnabled', False)
    original_events_listeners = realm.get('eventsListeners', [])

    admin_conn.update_realm('ucs', payload={
        'eventsEnabled': True,
        'eventsListeners': list({*original_events_listeners, 'jboss-logging'}),
    })

    try:
        token_url = keycloak_config.token_url
        username = udm.create_user()[1]
        wait_for_listener_replication()

        # Test successful login
        response = requests.post(token_url, data={
            'client_id': 'admin-cli',
            'grant_type': 'password',
            'username': username,
            'password': 'univention',
        }, verify=True)
        assert response.status_code == 200, f'Login should succeed, got {response.status_code}: {response.text}'

        logs = run_command(['docker', 'logs', 'keycloak'])
        login_pattern = r'INFO.*\[org\.keycloak\.events\].*type="LOGIN"'
        assert re.search(login_pattern, logs), 'Expected INFO level LOGIN event in logs'

        # Test failed login
        response = requests.post(token_url, data={
            'client_id': 'admin-cli',
            'grant_type': 'password',
            'username': username,
            'password': 'wrong_password',
        }, verify=True)
        assert response.status_code == 401, f'Login should fail, got {response.status_code}: {response.text}'

        logs = run_command(['docker', 'logs', 'keycloak'])
        login_error_pattern = r'ERROR.*\[org\.keycloak\.events\].*type="LOGIN_ERROR"'
        assert re.search(login_error_pattern, logs), 'Expected ERROR level LOGIN_ERROR event in logs'

    finally:
        # Restore original realm settings
        admin_conn.update_realm('ucs', payload={
            'eventsEnabled': original_events_enabled,
            'eventsListeners': original_events_listeners,
        })
