#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test keycloak kerberos login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import subprocess

import pytest
import requests
from bs4 import BeautifulSoup
from requests_kerberos import OPTIONAL, HTTPKerberosAuth


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_kerberos_authentication(ucr, protocol):

    ucr.handler_set(['kerberos/defaults/rdns=false'])
    subprocess.call(['kdestroy'])
    hostname = ucr.get('hostname')
    domainname = ucr.get('domainname')
    subprocess.check_call(['kinit', '--password-file=/var/lib/ucs-test/pwdfile', 'Administrator'])
    session = requests.Session()
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

    headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
    url = f'https://{hostname}.{domainname}/univention/saml/' if protocol == 'saml' else f'https://{hostname}.{domainname}/univention/oidc/'
    page = session.get(url, data=None, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
    assert page.status_code == 200

    if protocol == 'saml':
        soup = BeautifulSoup(page.content, features='lxml')
        saml_resp = soup.find('input', {'name': 'SAMLResponse'}).attrs['value']
        relay_state = soup.find('input', {'name': 'RelayState'}).attrs['value']
        uri = soup.find('form', {'name': 'saml-post-binding'}).attrs['action']
        print(f'Got URI: {uri}')
        print(f'Got SAMLResponse: {saml_resp}')
        print(f'Got RelayState: {relay_state}')
        assert saml_resp
        data = {'SAMLResponse': saml_resp, 'RelayState': relay_state}
        page = session.post(uri, data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
        assert page.status_code == 200

    cookies = session.cookies.get_dict()
    assert cookies['UMCUsername'] == 'Administrator'
    assert 'UMCSessionId' in cookies
    assert 'AUTH_SESSION_ID' in cookies
    assert 'KEYCLOAK_IDENTITY' in cookies
