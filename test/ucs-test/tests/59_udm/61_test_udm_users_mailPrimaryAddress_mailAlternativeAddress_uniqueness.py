#!/usr/share/ucs-test/runner pytest-3
## desc: test mailPrimaryAddress and mailAlternativeAddress uniqueness
## bugs: [57171]
## tags: [udm]
## roles: [domaincontroller_master]
## packages:
##   - python3-univention-directory-manager

from collections.abc import Callable

import pytest

from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed, UCSTestUDM_ModifyUDMObjectFailed


@pytest.fixture()
def mail_domain(udm: UCSTestUDM, ucr: UCSTestConfigRegistry, random_string: Callable) -> str:
    ucr.handler_set(['directory/manager/mail-address/uniqueness=true'])
    udm.stop_cli_server()
    mail_domain = random_string()
    udm.create_object('mail/domain', name=mail_domain)
    return mail_domain


def test_same_user(udm: UCSTestUDM, mail_domain: str, random_string: Callable) -> None:
    mailAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_user(mailPrimaryAddress=mailAddress, mailAlternativeAddress=mailAddress)
    dn, _ = udm.create_user(mailPrimaryAddress=mailAddress)
    udm.modify_object('users/user', dn=dn, mailAlternativeAddress=mailAddress, set={'mailPrimaryAddress': ''})
    udm.modify_object('users/user', dn=dn, mailPrimaryAddress=mailAddress, set={'mailAlternativeAddress': ''})
    mailAlternativeAddress1 = f'{random_string()}@{mail_domain}'
    mailAlternativeAddress2 = f'{random_string()}@{mail_domain}'
    mailAlternativeAddress3 = f'{random_string()}@{mail_domain}'
    udm.modify_object('users/user', dn=dn, mailAlternativeAddress=[mailAlternativeAddress1, mailAlternativeAddress2, mailAlternativeAddress3])
    udm.modify_object('users/user', dn=dn, mailPrimaryAddress=mailAlternativeAddress1, set={'mailAlternativeAddress': [mailAlternativeAddress2, mailAlternativeAddress3]})
    udm.modify_object('users/user', dn=dn, mailPrimaryAddress=mailAlternativeAddress2, set={'mailAlternativeAddress': [mailAlternativeAddress1, mailAlternativeAddress3]})
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=mailAlternativeAddress3, set={'mailAlternativeAddress': [mailAlternativeAddress2, mailAlternativeAddress3]})


def test_other_user(udm: UCSTestUDM, mail_domain: str, random_string: Callable) -> None:
    mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    udm.create_user(mailPrimaryAddress=mailPrimaryAddress, mailAlternativeAddress=mailAlternativeAddress)
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_user(mailPrimaryAddress=mailPrimaryAddress)
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_user(mailAlternativeAddress=mailAlternativeAddress)
    dn, _ = udm.create_user()
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailAlternativeAddress=mailAlternativeAddress)
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=mailPrimaryAddress)
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailAlternativeAddress=mailAlternativeAddress, mailPrimaryAddress=mailPrimaryAddress)


def test_reuse_mailPrimaryAddress_as_mailAlternativeAddress(udm: UCSTestUDM, mail_domain: str, random_string: Callable) -> None:
    old_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    dn, _ = udm.create_user(mailPrimaryAddress=old_mailPrimaryAddress)

    # reuse the mailPrimaryAddress as mailAlternativeAddress
    new_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailAlternativeAddress=old_mailPrimaryAddress)
    udm.modify_object('users/user', dn=dn, mailPrimaryAddress=new_mailPrimaryAddress, mailAlternativeAddress=old_mailPrimaryAddress)

    # not if the same value
    new_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=new_mailPrimaryAddress, mailAlternativeAddress=new_mailPrimaryAddress)

    # not if already exists as mailAlternativeAddress
    existing_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    udm.create_user(mailAlternativeAddress=existing_mailAlternativeAddress)
    old_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    dn, _ = udm.create_user(mailPrimaryAddress=old_mailPrimaryAddress)
    new_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=new_mailPrimaryAddress, mailAlternativeAddress=existing_mailAlternativeAddress)


def test_reuse_mailAlternativeAddress_as_mailPrimaryAddress(udm: UCSTestUDM, mail_domain: str, random_string: Callable) -> None:
    old_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    dn, _ = udm.create_user(mailAlternativeAddress=old_mailAlternativeAddress)

    # reuse the mailAlternativeAddress as mailPrimaryAddress
    new_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=old_mailAlternativeAddress)
    udm.modify_object('users/user', dn=dn, mailAlternativeAddress=new_mailAlternativeAddress, mailPrimaryAddress=old_mailAlternativeAddress)

    # not if the same value
    new_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailPrimaryAddress=new_mailAlternativeAddress, mailAlternativeAddress=new_mailAlternativeAddress)

    # not if already exists as mailPrimaryAddress
    existing_mailPrimaryAddress = f'{random_string()}@{mail_domain}'
    udm.create_user(mailPrimaryAddress=existing_mailPrimaryAddress)
    old_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    dn, _ = udm.create_user(mailAlternativeAddress=old_mailAlternativeAddress)
    new_mailAlternativeAddress = f'{random_string()}@{mail_domain}'
    with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=dn, mailAlternativeAddress=new_mailAlternativeAddress, mailPrimaryAddress=existing_mailPrimaryAddress)
