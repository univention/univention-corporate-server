#!/usr/share/ucs-test/runner python3
## desc: SSO Login at UMC as Service Provider with kerberos
## tags: [saml]
## join: true
## exposure: dangerous
## roles: [domaincontroller_master]
## packages:
##   - univention-samba4
## tags:
##  - skip_admember

import json
import subprocess
import xml.etree.ElementTree

import defusedxml.ElementTree as ET
import pytest
import requests
from requests_kerberos import OPTIONAL, HTTPKerberosAuth


@pytest.fixture()
def kerberos_ticket(ucr):
    ucr.get('hostname')

    # subprocess.call(['kdestroy'])
    # subprocess.check_call(['kinit', '--password-file=/etc/machine.secret', hostname + '$'])  # get kerberos ticket

    yield

    subprocess.check_call(['klist'])
    # subprocess.check_call(['kdestroy'])


def saml_request(session, target_sp_hostname, position, url, status_code, data=None):
    """
    does POST requests and raises SamlError which encodes the login step
    through position parameter.
    """
    headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
    umc_session_id = session.cookies.get('AUTH_SESSION_ID')
    if umc_session_id:
        headers["X-Xsrf-Protection"] = umc_session_id
    try:
        print(headers)
        # breakpoint()
        page = session.post(url)
    except requests.exceptions.SSLError:
        # Bug: https://github.com/shazow/urllib3/issues/556
        # raise SamlError("Problem while %s\nSSL error: %s" % (position, exc))
        raise Exception("Problem while %s\nSSL error: %s" % (position, 'Some ssl error'))
    except requests.ConnectionError as exc:
        raise Exception("Problem while %s\nNo connection to server: %s" % (position, exc))
    print(f'> GET {url} -> {page.status_code}')
    for resp in page.history:
        print(f'>> {resp.request.method} {resp.url} -> {resp.status_code}')

    return page


def parse_page(page, expected_format: str = "html"):
    if expected_format == 'json':
        return json.loads(bytes(page.content))
    try:
        return ET.fromstring(bytes(page.content))
    except xml.etree.ElementTree.ParseError as exc:
        print('WARN: could not parse XML/HTML: %s' % (exc,))
        return xml.etree.ElementTree.Element('html')


def test_keycloak_kerberos_login(kerberos_ticket, ucr):
    """
    Use Identity Provider to log in to a Service Provider.
    The IdP doesn't know the session and has to validate the kerberos ticket
    """
    ucr.handler_set(['kerberos/defaults/rdns=false'])

    # target_sp_hostname = '%(hostname)s.%(domainname)s' % ucr
    target_sp_hostname = 'ucs-sso-ng.ucs.test'
    session = requests.Session()
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
    page = None
    parsed_page = None
    position = 'Init...'

    # SamlSession = samltest.SamlTest('', '', use_kerberos=True)

    # def login_with_new_session_at_IdP(:
    # Open login prompt. Redirects to IdP. IdP answers with login prompt
    url = "https://%s/univention/saml/" % target_sp_hostname
    print(f"GET SAML login form at: {url}")
    # Login at IdP. IdP answers with SAML message and url to SP in body
    page = saml_request(session, target_sp_hostname, position, url, 200)

    assert page.status_code == 200, f"Server response while reaching login dialog was: {page.content.decode('UTF-8', 'replace')}"

    # SamlSession.login_with_new_session_at_IdP()
    # SamlSession.test_logged_in_status()
    # def test_logged_in_status(self):
    """Test login on umc"""
    # url = "https://%s/univention/get/session-info" % target_sp_hostname
    url = "https://master.ucs.test/univention/get/session-info"
    print("Test login @ %s" % url)
    position = "testing login"

    page = saml_request(session, target_sp_hostname, position, url, 200)
    assert page.status_code == 200, "Login type check failed"
    parsed_page = parse_page(page, expected_format='json')

    auth_type = parsed_page['result']['auth_type']

    assert auth_type == 'SAML', "SAML wasn't used for login?"

    print("Login success")
