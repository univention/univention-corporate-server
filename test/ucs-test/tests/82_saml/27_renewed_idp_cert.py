#!/usr/share/ucs-test/runner python3
## desc: Check that umc and slapd do not stop if the sso cert is renewed.
## tags: [saml]
## bugs: [45042]
## roles: [domaincontroller_master]
## join: true
## exposure: dangerous

import subprocess
import time

import univention.config_registry
from univention.testing import utils

import samltest


ucr = univention.config_registry.ConfigRegistry()
ucr.load()


def renew_sso_cert():
    sso_fqdn = ucr['ucs/server/sso/fqdn']
    subprocess.check_call(['univention-certificate', 'new', '-name', sso_fqdn, '-days', '100'])
    subprocess.check_call([
        "cp",
        f"/etc/univention/ssl/{sso_fqdn}/cert.pem",
        f"/etc/simplesamlphp/{sso_fqdn}-idp-certificate.crt",
    ])
    subprocess.check_call([
        "cp",
        f"/etc/univention/ssl/{sso_fqdn}/private.key",
        f"/etc/simplesamlphp/{sso_fqdn}-idp-certificate.key",
    ])
    subprocess.check_call(["deb-systemd-invoke", "restart", "univention-saml"])


def reload_idp_metadata():
    idp_metadata_umc = ucr.get('umc/saml/idp-server')
    subprocess.check_call([
        "ucr",
        "set",
        f"umc/saml/idp-server={idp_metadata_umc}",
    ])


def restart_slapd():
    subprocess.check_call(["deb-systemd-invoke", "restart", "slapd"])


def restart_umc_server():
    subprocess.check_call(["deb-systemd-invoke", "restart", "univention-management-console-server"])
    time.sleep(5)


def main():
    renew_sso_cert()
    reload_idp_metadata()
    account = utils.UCSTestDomainAdminCredentials()
    saml_session = samltest.SamlTest(account.username, account.bindpw)
    try:
        # Previously umc had a segfault here
        saml_session.login_with_new_session_at_IdP()
    except samltest.SamlError as exc:
        expected_error = '\\n'.join([
            "The SAML authentication failed. This might be a temporary problem. Please login again.",
            "Further information can be found in the following logfiles:",
            "* /var/log/univention/management-console-web-server.log",
            "* /var/log/univention/management-console-server.log",
        ])
        if expected_error not in str(exc):
            utils.fail(str(exc))
    reload_idp_metadata()
    try:
        # Previously slapd had a segfault here
        saml_session.test_slapd()
    except samltest.SamlError as exc:
        expected_error = "Wrong status code: 401, expected: 200"
        if expected_error not in str(exc):
            utils.fail(str(exc))
    restart_umc_server()
    restart_slapd()
    saml_session.login_with_existing_session_at_IdP()
    saml_session.test_slapd()
    saml_session.logout_at_IdP()
    saml_session.test_logout_at_IdP()
    saml_session.test_logout()


if __name__ == '__main__':
    try:
        main()
    finally:
        # Make sure everything is in a working state again
        reload_idp_metadata()
        restart_umc_server()
        restart_slapd()
    print("####Success: Neither umc nor slapd have a segfault because of a renewed certificate.####")
