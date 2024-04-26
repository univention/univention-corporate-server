#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keycloak admin console login
## tags: [keycloak]
## roles: [domaincontroller_master]
## exposure: dangerous

import pytest
import requests

from univention.config_registry import ucr


FQDN_HOST = '%(hostname)s.%(domainname)s' % ucr
FQDN_SSO = 'ucs-sso-ng.%(domainname)s' % ucr


pytestmark = pytest.mark.skipif(
    ucr.get('keycloak/server/sso/fqdn', FQDN_SSO) != FQDN_SSO,
    reason='Custom keycloak FQDN/path',
)


@pytest.mark.parametrize('path', ['/', '/myauth'])
@pytest.mark.parametrize('fqdn', [FQDN_HOST, FQDN_SSO])
def test_kc_fqdn_path(change_app_setting, fqdn, path):
    settings = {
        'keycloak/server/sso/fqdn': fqdn,
        'keycloak/server/sso/path': path,
    }
    if fqdn == FQDN_HOST:
        # if keycloak uses the UCS hostname, we need to use a global config
        settings['keycloak/server/sso/virtualhost'] = False
        if path == '/':
            pytest.skip('this is not supported')
    change_app_setting('keycloak', settings)
    url = f'https://{fqdn}{path}/realms/ucs'
    resp = requests.get(url)
    assert resp.status_code == 200
