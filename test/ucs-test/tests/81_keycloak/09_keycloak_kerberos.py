#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak kerberos login
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import subprocess

import requests
from bs4 import BeautifulSoup
from requests_kerberos import OPTIONAL, HTTPKerberosAuth


def test_kerberos_authentication(ucr):
    ucr.handler_set(['kerberos/defaults/rdns=false'])
    subprocess.call(['kdestroy'])
    hostname = ucr.get("hostname")
    domainname = ucr.get("domainname")
    subprocess.check_call(['kinit', '--password-file=/var/lib/ucs-test/pwdfile', 'Administrator'])
    session = requests.Session()
    session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)

    headers = {'Accept-Language': 'en-US;q=0.6,en;q=0.4', 'Referer': ''}
    url = f"https://{hostname}.{domainname}/univention/saml/"
    page = session.get(url, data=None, verify='/etc/univention/ssl/ucsCA/CAcert.pem', headers=headers)
    assert page.status_code == 200

    soup = BeautifulSoup(page.content, features="lxml")
    saml_resp = soup.find("input", {"name": "SAMLResponse"})
    print("%s\nGot SAML respose" % (saml_resp,))
    assert saml_resp
