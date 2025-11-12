#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: "Test groupcache/membership after moving a user object"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember
## bugs:
##  - 51929

import subprocess

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
    assert {x.casefold() for x in expected_ucs_group} == ucs_groups
    assert {x.casefold() for x in expected_ad_groups} == ad_groups


def add_user_to_new_group_ad(ad, user_dn_ad):
    group3_name = f'grp3-{random_username(mixed_case=True)}'
    group3_dn_ad = ad.create_group(group3_name, wait_for_replication=False)
    ad.add_to_group(group3_dn_ad, user_dn_ad)
    ad.wait_for_sync()
    group3_dn = ad.ucs_dn(group3_dn_ad)
    return group3_dn, group3_dn_ad


def add_user_to_new_group_ucs(udm, ad, user_dn):
    group3_name = f'grp3-{random_username(mixed_case=True)}'
    group3_dn, _ = udm.create_group(groupname=group3_name, wait_for_replication=False)
    udm.modify_object('users/user', dn=user_dn, append={'groups': [group3_dn]}, wait_for_replication=False)
    ad.wait_for_sync()
    group3_dn_ad = ad.ad_dn(group3_dn)
    return group3_dn, group3_dn_ad


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_user_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move user in ad, change group membership, all while the connector is not running
        with adconnector_stopped():
            user_dn_ad = ad.rename(setup.user_dn_ad, position=ad.ldap_base, wait_for_replication=False)
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
        setup = ad.create_ou_structure_and_user(udm)
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
def test_rename_parent_rename_child_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        # create user and groups in AD
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        # rename parent
        ou1_name = f'new-{setup.ou1_name}'
        ou1_dn_ad = ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}')
        ou1_dn = f'ou={ou1_name},{ldap_base}'
        ou11_dn_ad = f'ou={setup.ou11_name},{ou1_dn_ad}'
        ou11_dn = f'ou={setup.ou11_name},{ou1_dn}'
        user_dn_ad = f'cn={setup.username},{ou11_dn_ad}'
        user_dn = f'uid={setup.username},{ou11_dn}'
        # check rename
        assert ad.get(ou1_dn_ad)
        assert ad.get(ou11_dn_ad)
        assert ad.get(user_dn_ad)
        assert lo.get(user_dn)
        assert not ad.get(setup.user_dn_ad.casefold())
        assert not lo.get(setup.user_dn.casefold())
        # rename child (users), change sam account name, in one step (connector not running)
        with adconnector_stopped():
            username = f'new-{setup.username}'
            sam_account_name = username
            final_user_dn_ad = ad.rename(user_dn_ad, rdn=f'cn={username}', wait_for_replication=False)
            ad.set_attributes(final_user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        final_user_dn = ad.ucs_dn(final_user_dn_ad)
        # check rename
        assert ou1_name.casefold() in final_user_dn and username.casefold() in final_user_dn
        assert ou1_name in final_user_dn_ad and username in final_user_dn_ad
        assert not ad.get(user_dn_ad)
        assert not lo.get(user_dn)
        assert lo.get(final_user_dn)
        assert ad.get(final_user_dn_ad)
        # change group membership and test
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, final_user_dn_ad)
        verify_groups(ad, lo, final_user_dn, final_user_dn_ad, {setup.group1_dn, group3_dn}, {setup.group1_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_rename_parent_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # rename parent ou1 in AD, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou1_name = f'new-{setup.ou1_name}'
            ou1_dn_ad = ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}', wait_for_replication=False)
            user_dn_ad = f'cn={setup.username},ou={setup.ou11_name},{ou1_dn_ad}'
            assert ad.get(user_dn_ad)
            ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
            ad.add_to_group(setup.group2_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        # verify user and group membership
        assert not lo.get(setup.user_dn)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert ou1_name.casefold() in user_dn
        assert lo.get(user_dn.casefold())
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_rename_parent_in_ucs(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        # create user and groups in AD
        setup = ad.create_ou_structure_and_user(udm)
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
        assert ou1_name.casefold() in user_dn_ad
        assert ad.get(user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ucs(udm, ad, user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_parent_in_ad(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        verify_groups(ad, lo, setup.user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # move ou11 to new parent ou2 in AD, change group membership, all while the connector is not running
        with adconnector_stopped():
            ou11_dn_ad = ad.rename(setup.ou11_dn_ad, position=setup.ou2_dn_ad, wait_for_replication=False)
            user_dn_ad = f'cn={setup.username},{ou11_dn_ad}'
            assert ad.get(user_dn_ad)
            ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
            ad.add_to_group(setup.group2_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        # verify user and group membership
        assert not lo.get(setup.user_dn)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert setup.ou2_name.casefold() in user_dn
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn}, {setup.group2_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group2_dn, group3_dn}, {setup.group2_dn_ad, group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_move_parent_in_ucs(udm, lo, ldap_base, mode):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm)
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
        assert setup.ou2_name.casefold() in user_dn_ad
        assert ad.get(user_dn_ad.casefold())
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
        group_name = random_username(mixed_case=True)
        user_name_prefix = random_username(mixed_case=True)
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
            user_dn_ad = ad.rename(user_dn_ad, rdn=f'cn={user_name}X', wait_for_replication=False)
            sam_account_name = f'{user_name_prefix}rÖto.1'
            ad.set_attributes(user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]}, wait_for_replication=False)
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
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        ou1_guid = ad.guid(setup.ou1_dn_ad)
        ou11_guid = ad.guid(setup.ou11_dn_ad)
        # check guid cache
        assert setup.ou1_dn_ad.casefold() == ad.cache_guid2dn(ou1_guid).casefold()
        assert setup.ou11_dn_ad.casefold() == ad.cache_guid2dn(ou11_guid).casefold()
        # rename ou1
        ou1_name = f'new-{setup.ou1_name}'
        ou1_dn_ad = ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}')
        ou11_dn_ad = f'ou={setup.ou11_name},{ou1_dn_ad}'
        ad.wait_for_sync()
        ou1_dn = ad.ucs_dn(ou1_dn_ad)
        ou11_dn = ad.ucs_dn(ou11_dn_ad)
        assert ad.get(ou1_dn_ad)
        assert ad.get(ou11_dn_ad)
        assert lo.get(ou1_dn)
        assert lo.get(ou11_dn)
        assert ou1_name.casefold() in ou1_dn
        assert ou1_name.casefold() in ou11_dn
        # modify ou11
        ou11_dn_ad = f'ou={setup.ou11_name},{ou1_dn_ad}'
        description = random_username(mixed_case=True)
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
def test_rename_and_move_and_change_sam_account_name_in_ad(udm, lo, mode):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        # rename, move change sam account name, in one step (connector not running)
        with adconnector_stopped():
            username = f'new-{setup.username}'
            sam_account_name = username
            user_dn_ad = ad.rename(setup.user_dn_ad, rdn=f'cn={username}', position=setup.ou2_dn_ad, wait_for_replication=False)
            ad.set_attributes(user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        assert setup.ou2_dn in user_dn
        assert setup.ou2_dn_ad in user_dn_ad
        assert not lo.get(setup.user_dn)
        assert not ad.get(setup.user_dn_ad)
        # add to some group and check group membership after sync
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        verify_groups(ad, lo, user_dn, user_dn_ad, {group3_dn}, {group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_change_sam_account_name_in_ad(udm, mode, lo):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        sam_account_name = f'new-{setup.username}'
        ad.set_attributes(setup.user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]})
        user_dn = ad.ucs_dn(setup.user_dn_ad)
        assert sam_account_name not in setup.user_dn_ad
        assert ad.get(setup.user_dn_ad)
        assert setup.user_dn_ad.casefold() == ad.ad_dn(user_dn)
        assert not lo.get(setup.user_dn)
        assert lo.get(user_dn)
        assert sam_account_name.casefold() in user_dn
        assert user_dn.casefold() != setup.user_dn
        # we have to add this new user DN to udm-test, otherwise we get UCSTestUDM_CannotModifyExistingObject
        udm._cleanup['users/user'] = [user_dn]
        verify_groups(ad, lo, user_dn, setup.user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, setup.user_dn_ad)
        ad.remove_from_group(setup.group1_dn_ad, setup.user_dn_ad)
        ad.wait_for_sync()
        verify_groups(ad, lo, user_dn, setup.user_dn_ad, {group3_dn}, {group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_and_change_sam_account_name_in_ad(udm, mode, lo):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        # move and change sam account name, in one step (connector not running)
        with adconnector_stopped():
            sam_account_name = f'new-{setup.username}'
            user_dn_ad = ad.rename(setup.user_dn_ad, position=setup.ou2_dn_ad, wait_for_replication=False)
            ad.set_attributes(user_dn_ad, {'sAMAccountName': [sam_account_name.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        assert not ad.get(setup.user_dn_ad)
        assert ad.get(user_dn_ad)
        user_dn = ad.ucs_dn(user_dn_ad)
        assert ad.ad_dn(user_dn) == user_dn_ad.casefold()
        assert user_dn != setup.user_dn
        assert sam_account_name.casefold() in user_dn
        assert setup.ou2_dn.casefold() in user_dn
        assert not lo.get(setup.user_dn)
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # add to some group and check group membership after sync
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        verify_groups(ad, lo, user_dn, user_dn_ad, {group3_dn}, {group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_change_cn_in_ad(udm, mode, lo):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        cn = f'new-{setup.username}'
        user_dn_ad = ad.rename(setup.user_dn_ad, rdn=f'cn={cn}')
        assert user_dn_ad.casefold() == ad.ad_dn(setup.user_dn)
        assert lo.get(setup.user_dn)
        assert user_dn_ad != setup.user_dn_ad
        assert cn in user_dn_ad
        assert ad.get(user_dn_ad)
        assert ad.ucs_dn(user_dn_ad).casefold() == setup.user_dn
        verify_groups(ad, lo, setup.user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        verify_groups(ad, lo, setup.user_dn, user_dn_ad, {group3_dn}, {group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_change_cn_weird_in_ad(udm, mode, lo):
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        cn = f'neä-{setup.username}'
        user_dn_ad = ad.rename(setup.user_dn_ad, rdn=f'cn={cn}')
        assert user_dn_ad.casefold() == ad.ad_dn(setup.user_dn)
        assert lo.get(setup.user_dn)
        assert user_dn_ad.casefold() != setup.user_dn_ad
        assert cn in user_dn_ad
        assert ad.get(user_dn_ad)
        assert ad.ucs_dn(user_dn_ad).casefold() == setup.user_dn
        verify_groups(ad, lo, setup.user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        ad.remove_from_group(setup.group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        verify_groups(ad, lo, setup.user_dn, user_dn_ad, {group3_dn}, {group3_dn_ad})


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_move_plus_one_ou_in_ad(udm, mode, lo, ldap_base):
    with connector_setup2(mode) as ad:
        username = f'A Ä!{random_username()}'
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        ou_plus1_dn_ad = ad.create_ou('+1', position=setup.ou1_dn_ad, wait_for_replication=False)
        user_dn_ad = ad.create_user(username, position=ou_plus1_dn_ad, wait_for_replication=False)
        user_sid_ad = ad.get(user_dn_ad)['objectSid'][0]
        ad.add_to_group(setup.group1_dn_ad, user_dn_ad)
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        # move/rename ou
        ou1_name = f'new-{setup.ou1_name}'
        ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}', position=setup.ou2_dn_ad)
        assert not ad.get(user_dn_ad)
        assert not lo.get(user_dn)
        user_dn_ad = f'cn={username},ou=\+1,ou={ou1_name},{setup.ou2_dn_ad}'  # noqa: W605
        user_dn = ad.ucs_dn(user_dn_ad)
        assert ad.get(user_dn_ad)
        assert lo.get(user_dn)
        assert user_dn == f'uid={username},ou=\+1,ou={ou1_name},{setup.ou2_dn}'.casefold()  # noqa: W605
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        assert user_sid_ad == ad.get(user_dn_ad)['objectSid'][0], 'SID for user changed, new object in AD after move in UCS!'
        # and another change, just to be sure
        group3_dn, group3_dn_ad = add_user_to_new_group_ad(ad, user_dn_ad)
        verify_groups(ad, lo, user_dn, user_dn_ad, {group3_dn, setup.group1_dn}, {group3_dn_ad, setup.group1_dn_ad})
        assert len(ad.initial_tracebacks) == len(ad.tracebacks())
        # TODO: somehow remove this mapping in sync mode?
        intermediate_user_dn = f'uid={username},ou=\\2b1,ou={ou1_name},{ldap_base}'.casefold()
        intermediate_user_dn_ad = f'cn={username},ou=\+1,ou={ou1_name},{ad.ldap_base}'.casefold()  # noqa: W605
        assert not ad.ad_dn(intermediate_user_dn)
        assert not ad.ucs_dn(intermediate_user_dn_ad)


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_move_plus_one_ou_in_ucs(udm, mode, lo, ldap_base):
    with connector_setup2(mode) as ad:
        username = f'A Ä!{random_username()}'
        setup = ad.create_ou_structure_and_user(udm)
        ou_plus1_dn = udm.create_object('container/ou', name='+1', position=setup.ou1_dn, wait_for_replication=False)
        user_dn, _ = udm.create_user(username=username, position=ou_plus1_dn, wait_for_replication=False)
        udm.modify_object('users/user', dn=user_dn, append={'groups': [setup.group1_dn]}, wait_for_replication=False)
        ad.wait_for_sync()
        user_dn_ad = ad.ad_dn(user_dn.replace('\\+1', '\\2b1'))  # TODO: why?
        user_sid_ad = ad.get(user_dn_ad)['objectSid'][0]
        assert ad.get(user_dn_ad)
        # move/rename ou
        ou1_name = f'new-{setup.ou1_name}'
        with adconnector_stopped():
            ou1_dn = udm.modify_object('container/ou', dn=setup.ou1_dn, name=ou1_name, wait_for_replication=False)
            ou1_dn = udm.move_object('container/ou', dn=ou1_dn, position=setup.ou2_dn, wait_for_replication=False)
        ad.wait_for_sync()
        assert not ad.get(user_dn_ad)
        assert not lo.get(user_dn)
        user_dn_ad = f'cn={username},ou=\+1,ou={ou1_name},{setup.ou2_dn_ad}'  # noqa: W605
        user_dn = f'uid={username},ou=\+1,ou={ou1_name},{setup.ou2_dn}'  # noqa: W605
        assert user_dn_ad.casefold() == ad.ad_dn(user_dn.replace('\\+1', '\\2b1'))  # TODO: why?
        assert user_dn.casefold().replace('\\+1', '\\2b1') == ad.ucs_dn(user_dn_ad)  # TODO: why?
        assert ad.get(user_dn_ad)
        assert lo.get(user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {setup.group1_dn}, {setup.group1_dn_ad})
        assert user_sid_ad == ad.get(user_dn_ad)['objectSid'][0], 'SID for user changed, new object in AD after move in UCS!'
        # we have to add this new user DN to udm-test, otherwise we get UCSTestUDM_CannotModifyExistingObject
        udm._cleanup['users/user'].append(user_dn)
        udm._cleanup['users/user'].append(user_dn.replace('\\+1', '\\2b1'))  # TODO: why?
        # and another change, just to be sure
        udm.modify_object('users/user', dn=user_dn, remove={'groups': [setup.group1_dn]}, wait_for_replication=False)
        udm._cleanup['users/user'].append(user_dn)  # TODO: why again?
        group3_dn, group3_dn_ad = add_user_to_new_group_ucs(udm, ad, user_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {group3_dn}, {group3_dn_ad})
        assert user_sid_ad == ad.get(user_dn_ad)['objectSid'][0], 'SID for user changed, new object in AD after move in UCS!'
        assert len(ad.initial_tracebacks) == len(ad.tracebacks())
        # check intermediate objects in dn mapping tables
        intermediate_user_dn = f'uid={username},ou=\\2b1,ou={ou1_name},{ldap_base}'.casefold()
        intermediate_user_dn_ad = f'cn={username},ou=\+1,ou={ou1_name},{ad.ldap_base}'.casefold()  # noqa: W605
        assert not ad.ad_dn(intermediate_user_dn)
        assert not ad.ucs_dn(intermediate_user_dn_ad)


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_rename_ou_rename_group(mode, udm, lo):
    """
    https://git.knut.univention.de/univention/dev/internal/dev-issues/dev-incidents/-/issues/172
    ucr set connector/ad/mapping/syncmode=read
    systemctl restart univention-ad-connector.service
    # Create the following tree in AD ou1->ou1.1->ou1.1.1
    # Create a group in AD ou1->ou1.1->ou1.1.1->group1
    # Add some members to the group in AD
    # Rename ou1 to ou2 in AD
    # Rename ou1.1.1 to ou1.1.2 in AD
    # Rename group1 to group2 in AD -> Traceback
    """
    # TODO: multiple problems in sync mode
    # 1. traceback during move -> add ldap.ALREADY_EXISTS to excpetion handling in connector/ad/__init__.py 2217?
    with connector_setup2(mode) as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        group_name = f'grp-{random_username(mixed_case=True)}'
        group_dn_ad = ad.create_group(group_name, position=setup.ou111_dn_ad, wait_for_replication=False)
        ad.add_to_group(group_dn_ad, setup.user_dn_ad)
        ad.wait_for_sync()
        group_dn = ad.ucs_dn(group_dn_ad)
        # rename while connector is stopped
        with adconnector_stopped():
            # rename ou1
            ou1_name = f'new-{setup.ou1_name}'
            ou1_dn_ad = ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}', wait_for_replication=False)
            ou111_dn_ad = f'ou={setup.ou111_name},ou={setup.ou11_name},{ou1_dn_ad}'
            assert ad.get(ou111_dn_ad)
            # rename ou111
            ou111_name = f'new-{setup.ou111_name}'
            ou111_dn_ad = ad.rename(ou111_dn_ad, rdn=f'ou={ou111_name}', wait_for_replication=False)
            group_dn_ad = f'cn={group_name},{ou111_dn_ad}'
            assert ad.get(group_dn_ad)
            # rename group
            new_group_name = f'new-{group_name}'
            new_group_dn_ad = ad.rename(group_dn_ad, rdn=f'cn={new_group_name}', wait_for_replication=False)
            ad.set_attributes(new_group_dn_ad, {'sAMAccountName': [new_group_name.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        tb = ad.last_traceback()
        assert not (
            tb
            and 'in sync_from_ucs' in tb
            and "self.lo_ad.rename(old_dn, object['dn'])" in tb
            and "ldap.ALREADY_EXISTS: {'desc': 'Already exists', 'info': '00002071: UpdErr: " in tb
            and "DSID-031B0CF6, problem 6005 (ENTRY_EXISTS)" in tb
        ), f'Suspicious traceback found: {tb}'
        ou1_dn = ad.ucs_dn(ou1_dn_ad)
        assert ou1_name.casefold() in ou1_dn
        ou111_dn = ad.ucs_dn(ou111_dn_ad)
        assert ou1_name.casefold() in ou111_dn
        assert ou111_name.casefold() in ou111_dn
        user_dn_ad = f'cn={setup.username},ou={setup.ou11_name},{ou1_dn_ad}'
        user_dn = f'uid={setup.username},ou={setup.ou11_name},{ou1_dn}'
        assert not ad.get(setup.user_dn_ad)
        assert not lo.get(setup.user_dn)
        assert ad.get(user_dn_ad)
        assert lo.get(user_dn)
        new_group_dn = ad.ucs_dn(new_group_dn_ad)
        assert not ad.get(group_dn_ad)
        assert ad.get(new_group_dn_ad)
        assert lo.get(new_group_dn)
        assert not lo.get(group_dn)
        verify_groups(ad, lo, user_dn, user_dn_ad, {new_group_dn, setup.group1_dn}, {new_group_dn_ad, setup.group1_dn_ad})


def test_move_ad_ou_to_allowsubtree(udm, ldap_base, ucr, lo):
    """
    This test tries to emulate the folloing allowsubtree workflow
    ou=ou1 - not allowed
    ou=ou2 - allowed
    in UCS ou=new-ou11,ou=2 already exists (empty)
    in AD move/rename ou=ou11,ou=1 to ou=new-ou11,ou2
    """
    ldap_base_ad = ucr['connector/ad/ldap/base']
    ou_allowed_name = f'allowed-ou-{random_username(mixed_case=True)}'
    ou_allowed_dn_ad = f'ou={ou_allowed_name},{ldap_base_ad}'
    ou_allowed_dn = f'ou={ou_allowed_name},{ldap_base}'
    settings = [
        f'connector/ad/mapping/allowsubtree/myou/ucs={ou_allowed_dn}',
        f'connector/ad/mapping/allowsubtree/myou/ad={ou_allowed_dn_ad}',
    ]
    with connector_setup2('read') as ad:
        setup = ad.create_ou_structure_and_user(udm, in_ad=True)
        # remove the again in UCS, we will resync this ou to the allowed OU in AD
        udm._cleanup.setdefault('container/ou', []).append(setup.ou1_dn)
        udm.remove_object('container/ou', dn=setup.ou1_dn, wait_for_replication=False)
        with adconnector_stopped():
            ucr.handler_set(settings)
        # create allowed ou
        ad.create_ou(ou_allowed_name, wait_for_replication=True)
        ou1_name = f'new-{setup.ou1_name}'
        # create the ou, that we want to move to allowed in AD, also in UCS, that is what we told the customer to do
        udm.create_object('container/ou', name=ou1_name, position=ou_allowed_dn, wait_for_replication=False)
        # in AD move ou to allowed OU
        ou1_dn_ad = ad.rename(setup.ou1_dn_ad, rdn=f'ou={ou1_name}', position=ou_allowed_dn_ad)
        tb = ad.last_traceback()
        assert not (
            tb
            and f'univention.admin.uexceptions.objectExists: Object exists: ou={ou1_name},' in tb
        ), f'Suspicious traceback found: {tb}'
        # resync content, the connector currently does not sync childs in this case
        cmd = [
            '/usr/share/univention-ad-connector/resync_object_from_ad.py',
            '-c', 'connector',
            '--base', ou1_dn_ad,
            '--filter', '(objectClass=*)',
        ]
        with adconnector_stopped():
            subprocess.check_call(cmd)
        ad.wait_for_sync()
        # check resync
        ou1_dn = f'ou={ou1_name},ou={ou_allowed_name},{ldap_base}'
        ou11_dn = f'ou={setup.ou11_name},{ou1_dn}'
        ou111_dn = f'ou={setup.ou111_name},{ou11_dn}'
        user_dn = f'uid={setup.username},{ou11_dn}'
        assert lo.get(ou1_dn)
        assert lo.get(ou11_dn)
        assert lo.get(ou111_dn)
        assert lo.get(user_dn)
        # no new traceback
        assert tb == ad.last_traceback()
