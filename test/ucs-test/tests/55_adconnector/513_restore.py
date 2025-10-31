#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the UCS<->AD delete synchronization"
## exposure: dangerous
## packages:
## - univention-ad-connector

import random

import pytest
from ldap.dn import escape_dn_chars

from univention.admin.recyclebin import RECYCLEBIN_BASE
from univention.admin.uldap import access
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object

from adconnector import _Connector, connector_running_on_this_host, wait_for_sync


def _deleted_object_dn(dn: str) -> str:
    return f'univentionRecycleBinOriginalDN={escape_dn_chars(dn)},{RECYCLEBIN_BASE}'


@pytest.fixture(scope='module')
def recyclebin_policy(udm_session: UCSTestUDM, ldap_base: str) -> dict:
    name = random_username()
    retention_time = random.randint(100, 300)  # days

    pol_dn = udm_session.create_object(
        'policies/recyclebin',
        position=f'cn=policies,{ldap_base}',
        name=name,
        udm_modules=['users/user', 'groups/group'],
        retention_time=retention_time,
        wait_for_replication=False,
    )
    con_dn = udm_session.create_object(
        'container/cn',
        position=f'{ldap_base}',
        name=f'recyclebin_{name}',
        policy_reference=pol_dn,
        wait_for_replication=False,
    )
    return {'container_dn': con_dn, 'retention_time': retention_time}


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention AD Connector not configured.')
def test_restore_ucs(udm: UCSTestUDM, recyclebin_policy: dict, lo: access, ad_connector: _Connector):
    # create
    user_dn, username = udm.create_user(position=recyclebin_policy.get('container_dn'))
    wait_for_sync()
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn, attr=['+', '*'])

    ad_dn = ad_connector.get_dn(username)
    original_samba_attrs = ad_connector._ad.get(ad_dn, attr=['+', '*'])

    # remove
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    wait_for_sync()

    # restore
    deleted_dn = _deleted_object_dn(user_dn)
    restored_dn = udm.restore_object('recyclebin/deletedobject', dn=deleted_dn)
    wait_for_sync()
    assert user_dn == restored_dn
    verify_ldap_object(user_dn, should_exist=True)
    restored_attrs = lo.get(user_dn, attr=['+', '*'])

    # Check UCS attributes
    diverse_attributes = [
        'createTimestamp',
        'entryCSN',
        'modifyTimestamp',
        'sambaPwdLastSet',
    ]
    for da in diverse_attributes:
        original_attrs.pop(da)
        restored_attrs.pop(da)
    assert {k: set(v) for k, v in original_attrs.items()} == {k: set(v) for k, v in restored_attrs.items()}

    # Check Samba attributes
    restored_samba_attrs = ad_connector._ad.get(ad_dn, attr=['+', '*'])
    diverse_attributes = [
        'whenChanged',
        'lastKnownParent',
        'uSNChanged',
        'dSCorePropagationData',
        'msDS-LastKnownRDN',
    ]
    for da in diverse_attributes:
        if original_samba_attrs.get(da):
            original_samba_attrs.pop(da)
        if restored_samba_attrs.get(da):
            restored_samba_attrs.pop(da)
    assert {k: set(v) for k, v in original_samba_attrs.items()} == {k: set(v) for k, v in restored_samba_attrs.items()}


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention AD Connector not configured.')
def test_restore_ad(udm: UCSTestUDM, recyclebin_policy, lo: access, ad_connector: _Connector):
    # Create user in UCS
    user_dn, username = udm.create_user(position=recyclebin_policy.get('container_dn'))
    wait_for_sync()
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn, attr=['+', '*'])

    ad_dn = ad_connector.get_dn(username)
    original_samba_attrs = ad_connector._ad.get(ad_dn, attr=['+', '*'])

    # Remove user in UCS
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    wait_for_sync()

    # Restore in AD
    ad_connector.restore_object(dn=ad_dn)
    wait_for_sync()

    # Check UCS attributes
    restored_attrs = lo.get(user_dn, attr=['+', '*'])
    diverse_attributes = [
        'createTimestamp',
        'entryCSN',
        'modifyTimestamp',
        'sambaPwdLastSet',
    ]
    for da in diverse_attributes:
        if original_attrs.get(da):
            original_attrs.pop(da)
        if restored_attrs.get(da):
            restored_attrs.pop(da)
    assert {k: set(v) for k, v in original_attrs.items()} == {k: set(v) for k, v in restored_attrs.items()}

    # Check Samba attributes
    restored_samba_attrs = ad_connector._ad.get(ad_dn, attr=['+', '*'])
    diverse_attributes = [
        'whenChanged',
        'lastKnownParent',
        'uSNChanged',
        'dSCorePropagationData',
        'msDS-LastKnownRDN',
    ]
    for da in diverse_attributes:
        if original_samba_attrs.get(da):
            original_samba_attrs.pop(da)
        if restored_samba_attrs.get(da):
            restored_samba_attrs.pop(da)
    assert {k: set(v) for k, v in original_samba_attrs.items()} == {k: set(v) for k, v in restored_samba_attrs.items()}


def test_link_after_restore_ucs(udm: UCSTestUDM, recyclebin_policy: dict, ad_connector: _Connector):
    # Create, delete and restore user in UCS
    user_dn, username = udm.create_user(position=recyclebin_policy.get('container_dn'))
    wait_for_sync()
    udm.remove_object('users/user', dn=user_dn)
    wait_for_sync()
    deleted_dn = _deleted_object_dn(user_dn)
    restored_dn = udm.restore_object('recyclebin/deletedobject', dn=deleted_dn)
    # Bug in restore_object()
    udm._cleanup.setdefault('users/user', []).append(restored_dn)
    wait_for_sync()
    assert user_dn == restored_dn

    # Modify the display name
    new_firstname = 'test_link_after_restore_ucs'
    udm.modify_object(modulename='users/user', dn=restored_dn, firstname=new_firstname)
    wait_for_sync()

    # Test if the new display name is synced to Samba
    s4_dn = ad_connector.get_dn(username)
    samba_attrs = ad_connector._ad.get(s4_dn, attr=['givenName'])
    assert samba_attrs.get('givenName')[0].decode('UTF-8') == new_firstname
