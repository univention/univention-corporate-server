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
from utils import portal_logout


@pytest.mark.parametrize('protocol', ['saml', 'oidc'])
def test_kerberos_authentication(portal_login_via_keycloak, ucr, protocol, portal_config):

    if protocol == 'oidc':
        # login with playwright to get rid of the oidc grant
        # privileges dialog, i don't get it to work with requests
        #   soup = BeautifulSoup(page.content, features='lxml')
        #   uri = soup.find('form', {'class': 'form-actions'}).attrs['action']
        #   code = soup.find('input', {'name': 'code'}).attrs['value']
        #   data = {'code': code, 'accept': 'Yes'}
        #   page = session.post(f'https://ucs-sso-ng.ucs.test/{uri}', data=data, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
        page = portal_login_via_keycloak('Administrator', 'univention', protocol='oidc')
        portal_logout(page, portal_config)
        page.close()

    ucr.handler_set(['kerberos/defaults/rdns=false'])
    subprocess.call(['kdestroy'])
    subprocess.check_call(['kinit', '--password-file=/var/lib/ucs-test/pwdfile', 'Administrator'])
    session = requests.Session()
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

    headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
    url = f'https://{portal_config.fqdn}/univention/saml/' if protocol == 'saml' else f'https://{portal_config.fqdn}/univention/oidc/'
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
