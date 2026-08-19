#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test metrics settings
## tags: [keycloak, skip_admember]
## roles: [domaincontroller_master]
## exposure: dangerous

import os
import re

import pytest
import requests


@pytest.mark.skipif(not os.path.isfile('/etc/keycloak.secret'), reason='fails on hosts without keycloak.secret')
def test_metrics_settings(ucr, admin_account, portal_login_via_keycloak, change_app_setting, is_keycloak):
    """Test keycloak metrics"""
    change_app_setting('keycloak', {
        'keycloak/management/port': '9000',
        'keycloak/event/metrics/user/enabled': 'True',
        'keycloak/http/metrics/histograms/enabled': 'True',
    })
    portal_login_via_keycloak(admin_account.username, admin_account.bindpw, protocol='oidc')
    resp = requests.get(f'http://{ucr["hostname"]}:9000/metrics')
    assert resp.status_code == 200
    assert re.search(r'keycloak_user_events_total\{.*event="login"', resp.text) is not None
    resp = requests.get(f'http://{ucr["hostname"]}:9000/health')
    assert resp.status_code == 200
    assert "Keycloak Initialized" in resp.text
