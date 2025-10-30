#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the UCS<->AD delete synchronization"
## exposure: dangerous
## packages:
## - univention-ad-connector


import random

import pytest
from ldap.dn import escape_dn_chars, str2dn

from univention.admin.recyclebin import RECYCLEBIN_BASE
from univention.testing.strings import random_username
from univention.testing.utils import verify_ldap_object

from adconnector import connector_running_on_this_host, wait_for_sync


def _deleted_object_dn(dn):
    return f'univentionRecycleBinOriginalDN={escape_dn_chars(dn)},{RECYCLEBIN_BASE}'


@pytest.fixture(scope='module')
def recyclebin_policy(udm_session, ldap_base):
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
    return con_dn, retention_time


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_restore_ucs(udm, recyclebin_policy, lo):
    # create
    container_recyclebin_policy, _ = recyclebin_policy
    user_dn, _ = udm.create_user(position=container_recyclebin_policy)
    wait_for_sync()
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn, attr=['+', '*'])

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

    # check
    diverse_attributes = [
        'createTimestamp',
        'entryCSN',
        'modifyTimestamp',
    ]
    for da in diverse_attributes:
        original_attrs.pop(da)
        restored_attrs.pop(da)
    assert {k: set(v) for k, v in original_attrs.items()} == {k: set(v) for k, v in restored_attrs.items()}


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_restore_ad(udm, recyclebin_policy, lo, ad_connector):
    container_recyclebin_policy, _ = recyclebin_policy

    # Create user in UCS
    user_dn, _ = udm.create_user(position=container_recyclebin_policy)
    cn, *_ = str2dn(user_dn)
    wait_for_sync()
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn, attr=['+', '*'])
    ad_dn = ad_connector.get_dn(cn)

    # Remove user in UCS
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    wait_for_sync()

    # Restore in ad
    ad_connector.restore_object(dn=ad_dn)
    wait_for_sync()

    # check
    restored_attrs = lo.get(user_dn, attr=['+', '*'])
    diverse_attributes = [
        'createTimestamp',
        'entryCSN',
        'modifyTimestamp',
        'shadowLastChange',
    ]
    for da in diverse_attributes:
        if original_attrs.get(da):
            original_attrs.pop(da)
        if restored_attrs.get(da):
            restored_attrs.pop(da)
    assert {k: set(v) for k, v in original_attrs.items()} == {k: set(v) for k, v in restored_attrs.items()}
