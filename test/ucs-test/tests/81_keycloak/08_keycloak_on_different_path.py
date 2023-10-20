#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak admin console login
## tags: [keycloak]
## roles: [domaincontroller_master]
## exposure: dangerous

import pytest
import requests

from univention.config_registry import ucr


@pytest.mark.parametrize('path', ['/', '/myauth'])
@pytest.mark.parametrize('fqdn', ['%(hostname)s.%(domainname)s' % ucr, 'ucs-sso-ng.%(domainname)s' % ucr])
def test_kc_fqdn_path(change_app_setting, fqdn, path):
    settings = {
        'keycloak/server/sso/fqdn': fqdn,
        'keycloak/server/sso/path': path,
    }
    if fqdn == f"{ucr['hostname']}.{ucr['domainname']}":
        # if keycloak uses the UCS hostname, we need to use a global config
        settings['keycloak/server/sso/virtualhost'] = False
        if path == "/":
            pytest.skip("this is not supported")
    default_fqdn = 'ucs-sso-ng.%(domainname)s' % ucr
    if ucr.get('keycloak/server/sso/fqdn', default_fqdn) != default_fqdn:
        pytest.skip("this test makes only sense in scenarios without custom settings for keycloak FQDN/path")
    change_app_setting('keycloak', settings)
    url = f"https://{fqdn}{path}/realms/ucs"
    resp = requests.get(url)
    assert resp.status_code == 200
