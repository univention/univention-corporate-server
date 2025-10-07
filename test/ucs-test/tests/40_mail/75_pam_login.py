#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Test authentication after sending mail. This should not create additional mail directories
## exposure: dangerous
## tags: [apptest]
## packages: [univention-mail-server]
## bugs: [57976]


import os
import time

import univention.testing.strings as uts

from essential.mail import random_email, send_mail
from essential.mailclient import MailClient_SSL


def test_populate_file_and_resync(udm, ucr, fqdn):

    username = uts.random_string()
    password = 'univention'
    user_addr = random_email()
    msgid = uts.random_name()
    udm.create_user(
        set={
            'username': username,
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        })
    send_mail(recipients=user_addr, messageid=msgid, server=fqdn)
    # wait a bit
    time.sleep(5)
    imap = MailClient_SSL(f'{fqdn}')
    assert imap.login_ok(user_addr, password) == 0
    mailfront, mailback = user_addr.split('@')
    assert os.path.isdir(f'/var/spool/dovecot/private/{mailback}/{mailfront}')
    assert not os.path.isdir(f'/var/spool/dovecot/private/{mailfront}')
    assert not os.path.isdir(f'/var/spool/dovecot/private/{username}')
    assert not os.path.isdir(f'/var/spool/dovecot/private/{mailfront}')
