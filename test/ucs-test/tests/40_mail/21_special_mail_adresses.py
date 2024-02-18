#!/usr/share/ucs-test/runner python3
## desc: Test special mail addresses
## tags: [apptest]
## exposure: dangerous
## packages: [univention-mail-server]
import time

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.config_registry import handler_set
from univention.testing import utils

from essential.mail import mail_delivered, send_mail


def check_sending_mail(username, password, recipient_email):
    token = str(time.time())
    send_mail(recipients=recipient_email, msg=token, tls=True, username=username, password=password)
    delivered = mail_delivered(token, check_root=True)
    if not delivered:
        utils.fail('Mail sent with token = %r to %s was not redirected to root' % (token, recipient_email))


def main():
    with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm:
        fqdn = '%(hostname)s.%(domainname)s' % ucr
        handler_set(['mail/alias/root=systemmail@%s' % fqdn])
        mailAddress = '%s@%s' % (uts.random_name(), ucr.get('domainname'))
        _userdn, _username = udm.create_user(
            set={
                'password': 'univention',
                'mailHomeServer': fqdn,
                'mailPrimaryAddress': mailAddress,
            },
        )
        for mail_name in ('postmaster', 'webmaster'):
            recipient_email = '%s@%s' % (mail_name, fqdn)
            check_sending_mail(mailAddress, 'univention', recipient_email)


if __name__ == '__main__':
    main()
