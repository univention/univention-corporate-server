#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Test blocklist entries
## tags: [udm,udm-settings,apptest]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import subprocess
from datetime import datetime, timedelta
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
    value_hashed = hash_blocklist_value(value.encode('UTF-8'))
    stdout = subprocess.check_output(['udm', 'blocklists/entry', 'list', '--filter', f'value={value}'])
    assert value_hashed.encode('UTF-8') in stdout
    lo, _po = getMachineConnection(ldap_master=True)
    assert lo.get(f'cn={value_hashed},{blocklist_dn}', required=True, exceptions=True)


def delete_blocklistentry(value, blocklist_dn):
    dn = f'cn={hash_blocklist_value(value.encode("UTF-8"))},{blocklist_dn}'
    lo, _po = getMachineConnection(ldap_master=True)
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


def test_clean_expired_entries(ucr, udm, mail_domain_name, enable_blocklists):
    current_time = datetime.utcnow()

    bl_name = uts.random_name()
    data = {
        'name': bl_name,
        'blockingProperties': [
            'users/user mailPrimaryAddress',
            'groups/group mailAddress',
        ]
    }
    bl_dn = udm.create_object('blocklists/list', **data)
    udm.stop_cli_server()

    expired_ble_name = uts.random_name()
    expired_entry_data = {
        'value': expired_ble_name,
        'originUniventionObjectIdentifier': '9521d08e-6cf6-103b-9a74-edbd30d12cd6',
        'blockedUntil': datetime.strftime(current_time + timedelta(days=-2), '%Y%m%d%H%M%SZ')

    }
    expired_ble_dn = udm.create_object('blocklists/entry', superordinate=bl_dn, **expired_entry_data)
    udm.stop_cli_server()

    ble_name = uts.random_name()
    entry_data = {
        'value': ble_name,
        'originUniventionObjectIdentifier': '9521d08e-6cf6-103b-9a74-edbd30d12cd6',
        'blockedUntil': datetime.strftime(current_time + timedelta(days=20), '%Y%m%d%H%M%SZ')

    }
    ble_dn = udm.create_object('blocklists/entry', superordinate=bl_dn, **entry_data)
    udm.stop_cli_server()

    # DNs of the blocklist entries
    entries_names = [expired_ble_name, ble_name]
    entries_dn = [expired_ble_dn, ble_dn]
    print(entries_dn)

    # Verify the entries exists
    for value in entries_names:
        check_blocklistentry_exists(value, bl_dn)

    subprocess.check_output(['/usr/share/univention-directory-manager-tools/univention-blocklist-clean-expired-entries',
                             '--remove-expired'])

    check_blocklistentry_exists(ble_name, bl_dn)

    with pytest.raises(AssertionError):
        check_blocklistentry_exists(expired_ble_name, bl_dn)
