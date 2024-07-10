#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test umc upgrade
## tags: [saml]
## bugs: [50670]
## join: true
## roles: [domaincontroller_master]
## exposure: dangerous
## tags:
##  - skip_admember

import subprocess
import time

from univention.testing import utils

import samltest


def test_saml_check(saml_session):
    # cert_folder = samltest.SPCertificate.get_server_cert_folder()
    # with open(os.path.join(cert_folder, 'cert.pem'), 'rb') as cert_file:
    #     cert = cert_file.read()
    # with open('/etc/univention/ssl/ucsCA/CAcert.pem', 'rb') as ca_file:
    #     cert += b'\n' + ca_file.read()
    # with samltest.SPCertificate(cert):
    #     saml_check()
    saml_check(saml_session)


def saml_check(saml_session):
    try:
        print('Getting SAML login')
        saml_session.login_with_new_session_at_IdP()
        saml_session.test_logged_in_status()
        print('First try: require_password has to fail')
        call_umc_action_that_does_not_require_password(saml_session)
        call_umc_action_that_requires_password(saml_session, 401)
        upgrade_umc_saml_session(saml_session)
        saml_session.test_logged_in_status(None)
        print('Second try: require_password has to succeed')
        call_umc_action_that_does_not_require_password(saml_session)
        call_umc_action_that_requires_password(saml_session, 200)
        print('Ending module process; sleeping for 30 seconds... Password still known?')
        kill_umc_module()
        time.sleep(30)
        print('Third try: require_password has to succeed')
        call_umc_action_that_does_not_require_password(saml_session)
        call_umc_action_that_requires_password(saml_session, 200)
        saml_session.logout_at_IdP()
        saml_session.test_logout_at_IdP()
        saml_session.test_logout()
    except samltest.SamlError as exc:
        utils.fail(str(exc))


def call_umc_action_that_does_not_require_password(session):
    print('Testing appcenter/ping')
    url = "https://%s/univention/command/appcenter/ping" % session.target_sp_hostname
    session._request('POST', url, 200)


def call_umc_action_that_requires_password(session, expected):
    print('Testing appcenter/sync_ldap')
    url = "https://%s/univention/command/appcenter/sync_ldap" % session.target_sp_hostname
    session._request('POST', url, expected)


def upgrade_umc_saml_session(session):
    account = utils.UCSTestDomainAdminCredentials()
    umc_login = "https://%s/univention/auth" % session.target_sp_hostname
    session._request('POST', umc_login, 200, data={"username": account.username, "password": account.bindpw})


def kill_umc_module():
    return
    # extended regular expression, otherwise i find myself...
    ret = subprocess.call('pgrep -f "/usr/sbin/univention-management-console-module -m [a]ppcenter"', shell=True)
    assert ret == 0, "No App Center processes"
    ret = subprocess.call('pkill -f "/usr/sbin/univention-management-console-module -m [a]ppcenter"', shell=True)
    ret = subprocess.call('pgrep -f "/usr/sbin/univention-management-console-module -m [a]ppcenter"', shell=True)
    assert ret == 1, "pgrep returned %s" % ret
