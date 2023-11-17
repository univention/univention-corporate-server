import subprocess

import pytest

import samltest


@pytest.fixture()
def kerberos_ticket(ucr, account) -> None:
    ucr.handler_set(['kerberos/defaults/rdns=false', 'saml/idp/authsource=univention-negotiate'])
    subprocess.call(['kdestroy'])
    subprocess.check_call(['kinit', '--password-file=%s' % (account.pwdfile,), account.username])  # get kerberos ticket

    yield

    subprocess.check_call(['kdestroy'])


@pytest.fixture()
def saml_session(account):
    return samltest.SamlTest(account.username, account.bindpw)


@pytest.fixture()
def saml_session_kerberos():
    return samltest.SamlTest('', '', use_kerberos=True)
