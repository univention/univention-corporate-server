#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test accessing UMC UDM LDAP module with new access token
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import time
from html.parser import HTMLParser
from typing import Any, Dict

import pytest
import requests
from utils import run_command

from univention.config_registry.frontend import ucr_update


ACCESS_TOKEN_LIFESPAN = 15


class ExtractFormAction(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.form_action = ''

    def handle_starttag(self, tag, attrs):
        if tag != 'form':
            return
        attrs = dict(attrs)
        if attrs.get('method', '').lower() == 'post' and attrs.get('action'):
            self.form_action = attrs.get('action', '')


@pytest.fixture()
def disable_saml_oauthbearer_grace(ucr_proper):
    ucrv = 'ldap/server/sasl/oauthbearer/grace-time'
    original = ucr_proper.get(ucrv, None)

    ucr_update(ucr_proper, {ucrv: '0'})
    run_command(['systemctl', 'restart', 'slapd'])
    run_command(['systemctl', 'restart', 'univention-management-console-server'])
    time.sleep(10)

    yield

    ucr_update(ucr_proper, {ucrv: original})
    run_command(['systemctl', 'restart', 'slapd'])
    run_command(['systemctl', 'restart', 'univention-management-console-server'])


@pytest.fixture()
def umc_base_url(ucr_proper):
    return f"https://{ucr_proper.get('hostname')}.{ucr_proper.get('domainname')}/univention"


@pytest.fixture()
def client():
    return requests.Session()


def set_access_token_expiry_time(client: Dict[Any, Any]):
    client['attributes']['access.token.lifespan'] = str(ACCESS_TOKEN_LIFESPAN)


@pytest.mark.usefixtures('modify_keycloak_clients', 'disable_saml_oauthbearer_grace')
@pytest.mark.parametrize('modify_keycloak_clients', [set_access_token_expiry_time], indirect=True)
def test_udm_module_with_new_access_token(umc_base_url: str, client: requests.Session):
    resp = client.get(f'{umc_base_url}/oidc/')
    parser = ExtractFormAction()
    parser.feed(resp.text)
    next_url = parser.form_action
    if 'Kerberos Unsupported' in resp.text:
        resp = client.post(next_url)
        print('resp:')
        parser.feed(resp.text)
        next_url = parser.form_action

    body = {'username': 'Administrator', 'password': 'univention', 'credentialId': ''}

    resp = client.post(next_url, body)
    assert resp.status_code == 200, f"Keycloak login failed: {resp.text}"
    assert client.cookies.get('UMCSessionId') is not None, "No UMCSessionId cookie after login"
    umc_request_body = {
        "options": {
            "objectType": "users/user"
        },
        "flavor": "users/user"
    }

    xsrf_header = {'X-Xsrf-Protection': client.cookies.get('UMCSessionId')}
    resp = client.post(f'{umc_base_url}/command/udm/containers', json=umc_request_body, headers=xsrf_header)
    assert resp.status_code == 200, f"First UMC request failed: {resp.text}"

    time.sleep(ACCESS_TOKEN_LIFESPAN + 5)
    run_command(['systemctl', 'restart', 'slapd'])
    time.sleep(5)
    resp = client.post(f'{umc_base_url}/command/udm/containers', json=umc_request_body, headers=xsrf_header)
    assert resp.status_code == 200, f"Second UMC request, after token refresh failed: {resp.text}"
