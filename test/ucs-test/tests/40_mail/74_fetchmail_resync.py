#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Fetchmail, Test for regressions on bug 56521. A listener resync shouldn't duplicate entries in the /etc/fetchmailrc file.
## tags: [apptest, fetchmail]
## exposure: dangerous
## packages:
##  - univention-fetchmail

from __future__ import annotations

import subprocess
import time

import pytest

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test

from essential.mail import random_email


@pytest.fixture()
def udm():
    with udm_test.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def ucr():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        yield ucr


@pytest.fixture()
def fqdn():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        return '%(hostname)s.%(domainname)s' % ucr


def test_populate_file_and_resync(udm, ucr, fqdn):
    for i in range(5):
        remote_username = uts.random_string()
        password = uts.random_string()
        user_addr = random_email()
        udm.create_user(
            set={
                'mailHomeServer': fqdn,
                'mailPrimaryAddress': user_addr,
            }, append={
                'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                    f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                    f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
            })

    time.sleep(5)
    original_file = []
    with open('/etc/fetchmailrc') as f:
        original_file = f.readlines()
        original_file.sort()

    subprocess.call(['univention-directory-listener-ctrl', 'resync', 'fetchmailrc'])
    time.sleep(5)

    resynced_file = []
    with open('/etc/fetchmailrc') as f:
        resynced_file = f.readlines()
        resynced_file.sort()

    assert original_file == resynced_file
