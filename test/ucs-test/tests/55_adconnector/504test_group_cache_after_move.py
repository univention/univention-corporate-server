#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test groupcache/membership after moving a user object"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember
## bugs:
##  - 51929

from types import SimpleNamespace

import pytest

from univention.testing.strings import random_username
from univention.testing.utils import adconnector_stopped

from adconnector import connector_setup2


def get_ucs_groups(lo, dn):
    attrs = lo.get(dn, attr=['memberOf', 'gidNumber'])
    groups = {x.decode('utf-8').casefold() for x in attrs.get('memberOf', [])}
    # remove primary group, AD memberOf does not include primary Group
    gid = attrs.get('gidNumber', [b''])[0].decode('UTF-8')
    if gid:
        p_group = lo.search(f'(&(gidNumber={gid})(univentionObjectType=groups/group))')
        if p_group and len(p_group) == 1:
            groups.remove(p_group[0][0].casefold())
    return groups


def verify_groups(ad, lo, ucs_dn, ad_dn, expected_ucs_group, expected_ad_groups):
    ucs_groups = get_ucs_groups(lo, ucs_dn)
    ad_groups = ad.get_groups(ad_dn)
    assert expected_ucs_group == ucs_groups
    assert {x.casefold() for x in expected_ad_groups} == ad_groups


def create_ou_structure_and_user(udm, ad, in_ad=False):
    # create user and groups in AD
    ou1_name = f'ou1-{random_username()}'
    ou11_name = f'ou11-{random_username()}'
    ou2_name = f'ou2-{random_username()}'
    group1_name = f'grp1-{random_username()}'
    group2_name = f'grp2-{random_username()}'
    username = random_username()
    if in_ad:
        ou1_dn_ad = ad.create_ou(ou1_name, wait_for_replication=False)
        ou2_dn_ad = ad.create_ou(ou2_name, wait_for_replication=False)
        ou11_dn_ad = ad.create_ou(ou11_name, position=ou1_dn_ad, wait_for_replication=False)
        user_dn_ad = ad.create_user(username, position=ou11_dn_ad, wait_for_replication=False)
        group1_dn_ad = ad.create_group(group1_name, wait_for_replication=False)
        group2_dn_ad = ad.create_group(group2_name, wait_for_replication=False)
        ad.add_to_group(group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        group1_dn = ad.ucs_dn(group1_dn_ad)
        group2_dn = ad.ucs_dn(group2_dn_ad)
        ou1_dn = ad.ucs_dn(ou1_dn_ad)
        ou2_dn = ad.ucs_dn(ou2_dn_ad)
        ou11_dn = ad.ucs_dn(ou11_dn_ad)
    else:
        ou1_dn = udm.create_object('container/ou', name=ou1_name, wait_for_replication=False)
        ou2_dn = udm.create_object('container/ou', name=ou2_name, wait_for_replication=False)
        ou11_dn = udm.create_object('container/ou', name=ou11_name, position=ou1_dn, wait_for_replication=False)
        group1_dn, _ = udm.create_group(wait_for_replication=False)
        group2_dn, _ = udm.create_group(wait_for_replication=False)
        user_dn, username = udm.create_user(groups=[group1_dn], position=ou11_dn, wait_for_replication=False)
        ad.wait_for_sync()
        user_dn_ad = ad.ad_dn(user_dn)
        group1_dn_ad = ad.ad_dn(group1_dn)
        group2_dn_ad = ad.ad_dn(group2_dn)
        ou1_dn_ad = ad.ad_dn(ou1_dn)
        ou2_dn_ad = ad.ad_dn(ou2_dn)
        ou11_dn_ad = ad.ad_dn(ou11_dn)

    return SimpleNamespace(
        ou1_name=ou1_name,
        ou1_dn=ou1_dn,
        ou1_dn_ad=ou1_dn_ad,
        ou11_name=ou11_name,
        ou11_dn=ou11_dn,
        ou11_dn_ad=ou11_dn_ad,
        ou2_name=ou2_name,
        ou2_dn=ou2_dn,
        ou2_dn_ad=ou2_dn_ad,
        group1_dn=group1_dn,
        group1_dn_ad=group1_dn_ad,
        group2_dn=group2_dn,
        group2_dn_ad=group2_dn_ad,
        user_dn=user_dn,
        user_dn_ad=user_dn_ad,
        username=username,
        user_position_ad=ou11_dn_ad,
        user_position=ou11_dn,
    )


def add_user_to_new_group_ad(ad, user_dn_ad):
    group3_name = f'grp3-{random_username()}'
    group3_dn_ad = ad.create_group(group3_name, wait_for_replication=False)
    ad.add_to_group(group3_dn_ad, user_dn_ad)
    ad.wait_for_sync()
    group3_dn = ad.ucs_dn(group3_dn_ad)
    return group3_dn, group3_dn_ad


def add_user_to_new_group_ucs(udm, ad, user_dn):
    group3_name = f'grp3-{random_username()}'
    group3_dn, _ = udm.create_group(groupname=group3_name, wait_for_replication=False)
    udm.modify_object('users/user', dn=user_dn, append={'groups': [group3_dn]}, wait_for_replication=False)
    ad.wait_for_sync()
    group3_dn_ad = ad.ad_dn(group3_dn)
    return group3_dn, group3_dn_ad


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_user_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move user in ad, change group membership, all while the connector is not running
        with adconnector_stopped():
            user_dn_ad = ad._ad.rename_or_move_user_or_group(setup.user_dn_ad, position=ad.ldap_base)
            ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
            ad.add_to_group(setup.group2_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        # verify user and group membership
        user_dn = ad.ucs_dn(user_dn_ad)
        assert not lo.get(setup.user_dn)
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_move_user_in_ucs(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move user in ucs, change group membership, all while the connector is not running
        with adconnector_stopped():
            user_dn = udm.move_object('users/user', dn=setup.user_dn, position=ldap_base, wait_for_replication=False)
            udm.modify_object('users/user', dn=user_dn, remove={'groups': [setup.group1_dn]}, wait_for_replication=False)
            udm.modify_object('users/user', dn=user_dn, append={'groups': [setup.group2_dn]}, wait_for_replication=False)
        ad.wait_for_sync()
        # verify user and group membership
        user_dn_ad = ad.ad_dn(user_dn)
        assert not ad.get(setup.user_dn_ad)
        assert ad.get(user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ucs(udm, ad, user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_rename_parent_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # rename parent ou1 in AD, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou1_name = f'new-{setup.ou1_name}'
            ou1_dn_ad = ad.rename(setup.ou1_dn_ad, ou1_name, wait_for_replication=False)
            user_dn_ad = f'cn={setup.username},ou={setup.ou11_name},{ou1_dn_ad}'
            assert ad.get(user_dn_ad)
            ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
            ad.add_to_group(setup.group2_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        # verify user and group membership
        assert not lo.get(setup.user_dn)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert ou1_name in user_dn
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_rename_parent_in_ucs(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        # create user and groups in AD
        setup = create_ou_structure_and_user(udm, ad)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # rename parent ou1  in UCS, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou1_name = f'new-{setup.ou1_name}'
            udm.modify_object('container/ou', dn=setup.ou1_dn, name=ou1_name, wait_for_replication=False)
            ou1_dn = f'ou={ou1_name},{ldap_base}'
            user_dn = f'uid={setup.username},ou={setup.ou11_name},{ou1_dn}'
            assert lo.get(user_dn)
            # we have to add this new user DN to udm-test, otherwise we get UCSTestUDM_CannotModifyExistingObject
            udm._cleanup['users/user'].append(user_dn)
            udm.modify_object('users/user', dn=user_dn, remove={'groups': [setup.group1_dn]}, wait_for_replication=False)
            udm.modify_object('users/user', dn=user_dn, append={'groups': [setup.group2_dn]}, wait_for_replication=False)
        ad.wait_for_sync()
        # verify user and group membership
        assert not ad.get(setup.user_dn_ad)
        user_dn_ad = ad.ad_dn(user_dn)
        assert ou1_name in user_dn_ad
        assert ad.get(user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ucs(udm, ad, user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_parent_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move ou11 to new parent ou2 in AD, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou11_dn_ad = f'ou={setup.ou11_name},{setup.ou2_dn_ad}'
            ou11_dn_ad = ad.move(setup.ou11_dn_ad, ou11_dn_ad, wait_for_replication=False)
            user_dn_ad = f'cn={setup.username},{ou11_dn_ad}'
            assert ad.get(user_dn_ad)
            ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
            ad.add_to_group(setup.group2_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        # verify user and group membership
        assert not lo.get(setup.user_dn)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert setup.ou2_name in user_dn
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_move_parent_in_ucs(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move ou11 to new parent ou2 in UCS, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou11_dn = udm.move_object('container/ou', dn=setup.ou11_dn, position=setup.ou2_dn, wait_for_replication=False)
            user_dn = f'uid={setup.username},{ou11_dn}'
            assert lo.get(user_dn)
            # we have to add this new user DN to udm-test, otherwise we get UCSTestUDM_CannotModifyExistingObject
            udm._cleanup['users/user'].append(user_dn)
            udm.modify_object('users/user', dn=user_dn, remove={'groups': [setup.group1_dn]}, wait_for_replication=False)
            udm.modify_object('users/user', dn=user_dn, append={'groups': [setup.group2_dn]}, wait_for_replication=False)
        ad.wait_for_sync()
        # verify user and group membership
        assert not ad.get(setup.user_dn_ad)
        user_dn_ad = ad.ad_dn(user_dn)
        assert setup.ou2_name in user_dn_ad
        assert ad.get(user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ucs(udm, ad, user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['read'], ids=['read mode'])
def test_rename_user_with_umlauts(udm, lo, ldap_base, mode):
    '''
    ucr set connector/ad/mapping/syncmode=read
    systemctl restart univention-ad-connector.service
    # Create group g1 in AD
    # Create User "rÖto 1" but with samAccountName "röto.1"! in AD
    # Add "rÖto 1" to g1 in AD
    # Rename "rÖto 1" -> "rÖto 1X" and change samAccountName to "rÖto.1"! in AD -> Traceback
    '''
    with connector_setup2(mode) as ad:
        group_name = random_username()
        user_name_prefix = random_username()
        user_name = f'{user_name_prefix}rÖto 1'
        sam_account_name = f'{user_name_prefix}röto.1'
        principal_name = f'{sam_account_name}@{ad.domain}'
        group_dn_ad = ad.create_group(group_name, wait_for_replication=False)
        user_dn_ad = ad.create_user(
            user_name,
            wait_for_replication=False,
            sAMAccountName=sam_account_name.encode('UTF-8'),
            userPrincipalName=principal_name.encode('UTF-8'),
        )
        ad.add_to_group(group_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        group_dn = ad.ucs_dn(group_dn_ad)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert {group_dn} == get_ucs_groups(lo, user_dn)
        # rename user and change samAccountName
        with adconnector_stopped():
            user_dn_ad = ad.rename(user_dn_ad, f'{user_name}X', wait_for_replication=False)
            sam_account_name = f'{user_name_prefix}rÖto.1'
            ad.set_attributes(user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]})
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        assert {group_dn} == get_ucs_groups(lo, user_dn)
        assert {group_dn_ad.casefold()} == ad.get_groups(user_dn_ad)
        # check for traceback
        tb = ad.last_traceback()
        assert not (
            tb
            and 'object_memberships_sync_to_ucs' in tb
            and 'one_group_member_sync_to_ucs' in tb
            and 'ldap.TYPE_OR_VALUE_EXISTS' in tb
            and 'modify/add: uniqueMember: value #0 already exists' in tb
        ), f'Suspicious traceback found: {tb}'


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_rename_parent_change_ou_in_ad(udm, lo, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad, in_ad=True)
        ad.wait_for_sync()
        ou1_guid = ad.guid(setup.ou1_dn_ad)
        ou11_guid = ad.guid(setup.ou11_dn_ad)
        # check guid cache
        assert setup.ou1_dn_ad.casefold() == ad.cache_guid2dn(ou1_guid).casefold()
        assert setup.ou11_dn_ad.casefold() == ad.cache_guid2dn(ou11_guid).casefold()
        # rename ou1
        ou1_name = f'new-{setup.ou1_name}'
        ou1_dn_ad = ad.rename(setup.ou1_dn_ad, ou1_name, wait_for_replication=True)
        ou11_dn_ad = f'ou={setup.ou11_name},{ou1_dn_ad}'
        ad.wait_for_sync()
        ou1_dn = ad.ucs_dn(ou1_dn_ad)
        ou11_dn = ad.ucs_dn(ou11_dn_ad)
        assert ad.get(ou1_dn_ad)
        assert ad.get(ou11_dn_ad)
        assert lo.get(ou1_dn)
        assert lo.get(ou11_dn)
        assert ou1_name in ou1_dn
        assert ou1_name in ou11_dn
        # modify ou11
        ou11_dn_ad = f'ou={setup.ou11_name},{ou1_dn_ad}'
        description = random_username()
        ad.set_attributes(ou11_dn_ad, {'description': [description.encode('UTF-8')]})
        # check modification
        ad.wait_for_sync()
        ou11_dn = ad.ucs_dn(ou11_dn_ad)
        assert [description.encode('UTF-8')] == ad.get(ou11_dn_ad)['description']
        assert [description.encode('UTF-8')] == lo.get(ou11_dn)['description']
        # check guid cache
        assert ou1_dn_ad.casefold() == ad.cache_guid2dn(ou1_guid).casefold()
        assert ou11_dn_ad.casefold() == ad.cache_guid2dn(ou11_guid).casefold()


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_rename_and_move_user_in_ad(udm, lo, mode):
    with connector_setup2(mode) as ad:
        setup = create_ou_structure_and_user(udm, ad)
        ad.wait_for_sync()
        # rename, move change sam account name, in one step (connector not running)
        with adconnector_stopped():
            username = f'new-{setup.username}'
            sam_account_name = username
            user_dn_ad = f'cn={username},{setup.ou2_dn_ad}'
            ad._ad.lo.rename_s(setup.user_dn_ad, f'cn={username}', newsuperior=setup.ou2_dn_ad)
            ad.set_attributes(user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]})
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        assert setup.ou2_dn in user_dn
        assert setup.ou2_dn_ad in user_dn_ad
        # TODO: add to some group and check group membership after sync
