
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

import pytest
import requests

from requests_kerberos import OPTIONAL, HTTPKerberosAuth


@pytest.fixture()
def kerberos_ticket(ucr):
    hostname = ucr.get('hostname')

    subprocess.call(['kdestroy'])
    subprocess.check_call(['kinit', '--password-file=/etc/machine.secret', hostname + '$'])  # get kerberos ticket

    yield

    subprocess.check_call(['klist'])
    # subprocess.check_call(['kdestroy'])


def test_keycloak_kerberos_login(kerberos_ticket, ucr):
    """
    Use Identity Provider to log in to a Service Provider.
    The IdP doesn't know the session and has to validate the kerberos ticket
    """
    ucr.handler_set(['kerberos/defaults/rdns=false'])

    session = requests.Session()
    # session.auth = ('Administrator', 'univention')
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

    login_response = session.post(
        "https://ucs-sso-ng.ucs.test/univention/saml/",
    )

    assert login_response.status_code == 200, f"Server response while reaching login dialog was: {login_response.content.decode('UTF-8', 'replace')}"

    # Test login at umc
    info_response = session.get(
        "https://master.ucs.test/univention/get/session-info",
    )

    assert info_response.status_code == 200, "Login type check failed"
    parsed_page = json.loads(bytes(info_response.content))

    auth_type = parsed_page['result']['auth_type']

    assert auth_type == 'SAML', "SAML wasn't used for login?"

    print("Login success")
