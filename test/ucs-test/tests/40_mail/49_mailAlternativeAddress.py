#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test mailAlternativeAddress of groups
## tags: [udm,apptest]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - univention-mail-server

import time

import pytest

import univention.testing.strings as uts
from univention.testing import utils

from essential.mail import file_search_mail, send_mail


def test_group_mail_alternative_address_delivery(ucr, udm):
    TIMEOUT = 60
    domain = ucr['domainname'].lower()

    user_mail = '%s@%s' % (uts.random_string(), domain)
    user_dn, _ = udm.create_user(
        set={
            'mailPrimaryAddress': user_mail,
            'mailHomeServer': '%s.%s' % (ucr['hostname'], domain),
        },
    )

    group_primary = '%s@%s' % (uts.random_string(), domain)
    group_alt = '%s@%s' % (uts.random_string(), domain)

    group_dn, _ = udm.create_group(
        set={
            'mailAddress': group_primary,
            'mailAlternativeAddress': [group_alt],
            'users': [user_dn],
        },
    )

    utils.verify_ldap_object(
        group_dn,
        {
            'mailPrimaryAddress': [group_primary],
            'mailAlternativeAddress': [group_alt],
        },
        strict=False,
    )

    token = f'token: {time.time()}'

    send_mail(
        recipients=group_alt,
        msg=token,
    )

    while TIMEOUT > 0:
        if file_search_mail(tokenlist=[token], mail_address=user_mail):
            return
        TIMEOUT -= 1
        time.sleep(1)
    pytest.fail('mail sent to group alternative address %r was not delivered to %r' % (group_alt, user_mail))
