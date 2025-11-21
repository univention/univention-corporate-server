#!/usr/share/ucs-test/runner pytest-3
## desc: test reuse of mailPrimaryAddress
## bugs: [58828]
## tags: [udm]
## roles: [domaincontroller_master]
## packages:
##   - python3-univention-directory-manager

from collections.abc import Callable

import pytest

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed


@pytest.fixture
def mail_domain(udm: UCSTestUDM, ucr: UCSTestConfigRegistry, random_string: Callable) -> str:
    mail_domain = random_string()
    udm.create_object('mail/domain', name=mail_domain)
    return mail_domain


def test_release_mailPrimaryAddress(udm: UCSTestUDM, mail_domain: str, random_string: Callable) -> None:
    mailAddress = f'{random_string()}@{mail_domain}'
    dn, _ = udm.create_user(mailPrimaryAddress=mailAddress)
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_user(mailPrimaryAddress=mailAddress)
    udm.modify_object('users/user', dn=dn, mailPrimaryAddress="old_" + mailAddress)
    udm.create_user(mailPrimaryAddress=mailAddress)
