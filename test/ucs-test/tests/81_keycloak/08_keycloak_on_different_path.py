#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak admin console login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

from urllib.parse import urljoin

import pytest
import requests

from univention.config_registry import ucr


@pytest.mark.parametrize(
    'kc_fqdn',
    ['%(hostname)s.%(domainname)s' % ucr, 'ucs-sso-ng.%(domainname)s' % ucr],
    ids=['same_fqdn', 'different_fqdn'],
)
@pytest.mark.parametrize(
    'kc_path', ['/', '/myauth'],
    ids=['default_sso_path', 'custom_sso_path'],
)
def test_kc_fqdn_path(change_app_setting, kc_fqdn, kc_path):
    settings = {
        'keycloak/server/sso/fqdn': kc_fqdn,
        'keycloak/server/sso/path': kc_path,
    }
    change_app_setting('keycloak', settings)

    url = urljoin(f"https://{kc_fqdn}", f"{kc_path}/realms/ucs")
    resp = requests.get(url)
    assert resp.status_code == 200
