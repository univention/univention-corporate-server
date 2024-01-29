#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Test blocklist entries
## tags: [udm,udm-settings,apptest]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import subprocess
from types import SimpleNamespace

import pytest

import univention.testing.strings as uts
import univention.testing.udm
from univention.admin.blocklist import hash_blocklist_value
from univention.admin.uldap import getMachineConnection


@pytest.fixture()
def enable_blocklists(ucr, udm):
    ucr.handler_set(['directory/manager/blocklist/enabled=true'])
    udm.stop_cli_server()


@pytest.fixture()
def blocklist_list(random_string, udm, enable_blocklists):
    name = random_string()
    data = {
        'name': name,
        'blockingProperties': [
            'users/user mailPrimaryAddress',
            'groups/group mailAddress',
        ]
    }
    dn = udm.create_object('blocklists/list', **data)
    return SimpleNamespace(cn=name, dn=dn)


def check_blocklistentry_exists(value, blocklist_dn):
    value_hashed = hash_blocklist_value(value)
    stdout = subprocess.check_output(['udm', 'blocklists/entry', 'list', '--filter', f'value={value}'])
    assert value_hashed.encode('UTF-8') in stdout
    lo, po = getMachineConnection(ldap_master=True)
    assert lo.get(f'cn={value_hashed},{blocklist_dn}', required=True, exceptions=True)


def delete_blocklistentry(value, blocklist_dn):
    dn = f'cn={hash_blocklist_value(value)},{blocklist_dn}'
    lo, po = getMachineConnection(ldap_master=True)
    lo.get(dn, required=True, exceptions=True)
    lo.delete(dn)


@pytest.fixture()
def mail_domain_name(udm):
    mail_domain_name = f'{uts.random_name()}.{uts.random_name()}'
    udm.create_object('mail/domain', name=mail_domain_name)
    return mail_domain_name


def test_blocks_across_modules(blocklist_list, udm, mail_domain_name):
    emailaddr = f'{uts.random_name()}@{mail_domain_name}'
    user = udm.create_user(mailPrimaryAddress=emailaddr)[0]
    udm.remove_object('users/user', dn=user)

    with pytest.raises(univention.testing.udm.UCSTestUDM_CreateUDMObjectFailed):
        udm.create_group(mailAddress=emailaddr)[0]

    delete_blocklistentry(emailaddr, blocklist_list.dn)
    udm.create_group(mailAddress=emailaddr)[0]


def test_modify_same_user(blocklist_list, udm, mail_domain_name):
    emailaddr = f'{uts.random_name()}@{mail_domain_name}'
    user = udm.create_user(mailPrimaryAddress=emailaddr)[0]

    emailaddr2 = f'{uts.random_name()}@{mail_domain_name}'
    udm.modify_object('users/user', dn=user, mailPrimaryAddress=emailaddr2)
    check_blocklistentry_exists(emailaddr, blocklist_list.dn)

    udm.modify_object('users/user', dn=user, mailPrimaryAddress=emailaddr)


def test_modify(blocklist_list, udm, mail_domain_name):
    emailaddr = f'{uts.random_name()}@{mail_domain_name}'
    user = udm.create_user(mailPrimaryAddress=emailaddr)[0]
    udm.remove_object('users/user', dn=user)

    check_blocklistentry_exists(emailaddr, blocklist_list.dn)

    emailaddr2 = f'{uts.random_name()}@{mail_domain_name}'
    user2 = udm.create_user(mailPrimaryAddress=emailaddr2)[0]
    with pytest.raises(univention.testing.udm.UCSTestUDM_ModifyUDMObjectFailed):
        udm.modify_object('users/user', dn=user2, mailPrimaryAddress=emailaddr)
    delete_blocklistentry(emailaddr, blocklist_list.dn)

    udm.modify_object('users/user', dn=user2, mailPrimaryAddress=emailaddr)


def test_create(blocklist_list, udm, mail_domain_name):
    emailaddr = f'{uts.random_name()}@{mail_domain_name}'
    user = udm.create_user(mailPrimaryAddress=emailaddr)[0]
    udm.remove_object('users/user', dn=user)

    check_blocklistentry_exists(emailaddr, blocklist_list.dn)

    with pytest.raises(univention.testing.udm.UCSTestUDM_CreateUDMObjectFailed):
        user = udm.create_user(mailPrimaryAddress=emailaddr)[0]
    delete_blocklistentry(emailaddr, blocklist_list.dn)
    user = udm.create_user(mailPrimaryAddress=emailaddr)[0]


def test_multivalue_property_create(ucr, udm, enable_blocklists):
    bl_name = uts.random_name()
    data = {
        'name': bl_name,
        'blockingProperties': [
            'users/user description',
            'users/user postOfficeBox',
        ]
    }
    bl_dn = udm.create_object('blocklists/list', **data)
    udm.stop_cli_server()
    value = uts.random_name()
    values = [f'{value}1', f'{value}2', f'{value}3', f'{value}4']
    user = udm.create_user(description=values[-1], postOfficeBox=values[:3])[0]
    udm.remove_object('users/user', dn=user)
    for value in values:
        check_blocklistentry_exists(value, bl_dn)
        with pytest.raises(univention.testing.udm.UCSTestUDM_CreateUDMObjectFailed):
            udm.create_user(description=value)
        with pytest.raises(univention.testing.udm.UCSTestUDM_CreateUDMObjectFailed):
            udm.create_user(postOfficeBox=value)
        delete_blocklistentry(value, bl_dn)
    for value in values:
        udm.create_user(description=value)
        udm.create_user(postOfficeBox=value)


def test_multivalue_property_modify(ucr, udm, mail_domain_name, enable_blocklists):
    bl_name = uts.random_name()
    data = {
        'name': bl_name,
        'blockingProperties': [
            'users/user e-mail',
            'users/user mailPrimaryAddress',
            'groups/group mailAddress',
        ]
    }
    bl_dn = udm.create_object('blocklists/list', **data)
    udm.stop_cli_server()
    value = uts.random_name()
    values = [
        f'{value}1@{mail_domain_name}',
        f'{value}2@{mail_domain_name}',
        f'{value}3@{mail_domain_name}',
        f'{value}4@{mail_domain_name}',
    ]
    attrs = {'mailPrimaryAddress': values[-1], 'e-mail': values[:3]}
    user = udm.create_user(**attrs)[0]
    user2 = udm.create_user()[0]
    group = udm.create_group()[0]
    udm.remove_object('users/user', dn=user)
    # all values blocked
    for value in values:
        check_blocklistentry_exists(value, bl_dn)
        with pytest.raises(univention.testing.udm.UCSTestUDM_ModifyUDMObjectFailed):
            udm.modify_object('users/user', dn=user2, mailPrimaryAddress=value)
        with pytest.raises(univention.testing.udm.UCSTestUDM_ModifyUDMObjectFailed):
            email = {'e-mail': value}
            udm.modify_object('users/user', dn=user2, **email)
        with pytest.raises(univention.testing.udm.UCSTestUDM_ModifyUDMObjectFailed):
            udm.modify_object('groups/group', dn=group, mailAddress=value)
    # free values
    for value in values:
        delete_blocklistentry(value, bl_dn)
    # block values
    for value in values:
        udm.modify_object('users/user', dn=user2, mailPrimaryAddress=value)
    udm.remove_object('users/user', dn=user2)
    # check is blocked and free
    for value in values:
        with pytest.raises(univention.testing.udm.UCSTestUDM_ModifyUDMObjectFailed):
            udm.modify_object('groups/group', dn=group, mailAddress=value)
        delete_blocklistentry(value, bl_dn)
    # block values again
    for value in values:
        udm.modify_object('groups/group', dn=group, mailAddress=value)
    udm.remove_object('groups/group', dn=group)
    # check is blocked
    for value in values:
        check_blocklistentry_exists(value, bl_dn)
        delete_blocklistentry(value, bl_dn)
