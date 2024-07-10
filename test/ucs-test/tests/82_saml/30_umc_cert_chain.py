#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test handling of multiple certs in cert.pem
## tags: [saml]
## bugs: [47700]
## join: true
## roles: [domaincontroller_master]
## exposure: dangerous
## tags:
##  - skip_admember

import os

from univention.testing import utils

import samltest


def test_umc_cert_chain(saml_session):
    cert_folder = samltest.SPCertificate.get_server_cert_folder()
    with open(os.path.join(cert_folder, 'cert.pem'), 'rb') as cert_file:
        cert = cert_file.read()
    with open('/etc/univention/ssl/ucsCA/CAcert.pem', 'rb') as ca_file:
        cert += b'\n' + ca_file.read()
    with samltest.SPCertificate(cert):
        saml_check(saml_session)


def saml_check(saml_session):
    try:
        saml_session.login_with_new_session_at_IdP()
        saml_session.test_logged_in_status()
        saml_session.logout_at_IdP()
        saml_session.test_logout_at_IdP()
        saml_session.test_logout()
    except samltest.SamlError as exc:
        utils.fail(str(exc))
