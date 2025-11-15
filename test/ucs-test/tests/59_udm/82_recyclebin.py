#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test LDAP trash bin functionality
## tags: [ldap, udm, trash_bin]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager-tools


import copy
import datetime
import io
import logging
import time
import uuid
from types import SimpleNamespace

import pytest
from ldap.extop.dds import RefreshRequest

import univention.admin.modules as udm_modules
from univention.admin.blocklist import hash_blocklist_value
from univention.admin.log import log
from univention.admin.recyclebin import Reference
from univention.admin.uexceptions import authFail, noObject, uidAlreadyUsed, valueError
from univention.admin.uldap import access, getAdminConnection, position
from univention.logging import basicConfig
from univention.testing.fixtures_recyclebin import RECYCLEBIN_DN, _deleted_object_dn
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM_CreateUDMObjectFailed
from univention.testing.utils import (
    restart_slapd, start_listener, stop_listener, verify_ldap_object, wait_for_listener_replication,
)


pytest_plugins = 'univention.testing.fixtures_recyclebin'
udm_modules.update()
basicConfig(level=4, use_structured_logging=True)


def _find_deleted_objects(lo, original_dn):
    results = lo.search(
        base=RECYCLEBIN_DN,
        scope='one',
        filter='(objectClass=univentionRecycleBinObject)',
        attr=['univentionRecycleBinOriginalDN', 'univentionRecycleBinOriginalType', 'cn'],
    )
    deleted_objects = []
    for dn, attrs in results:
        original = attrs.get('univentionRecycleBinOriginalDN', [b''])[0].decode('utf-8')
        if original == original_dn:
            deleted_objects.append({
                'dn': dn,
                'originalDn': original,
                'univentionObjectType': attrs.get('univentionRecycleBinOriginalType', [b''])[0].decode('utf-8'),
            })
    return deleted_objects


def _cleanup_deleted_object(lo, deleted_dn):
    try:
        lo.delete(deleted_dn)
    except noObject as e:
        print(f'Warning: Could not clean up deleted object {deleted_dn}: {e}')


def verify_entryttl_deleteat(retention_time, dn, lo):
    # check ttl and purgeAt
    attrs = lo.get(dn, attr=['entryTtl', 'univentionRecycleBinDeleteAt', 'univentionRecycleBinDeletionDate'])
    entry_ttl = attrs['entryTtl'][0].decode('UTF-8')
    delete_at = attrs['univentionRecycleBinDeleteAt'][0].decode('UTF-8')
    deleted_at = attrs['univentionRecycleBinDeletionDate'][0].decode('UTF-8')
    deleted_at_date = datetime.datetime.strptime(deleted_at, '%Y%m%d%H%M%S%z')

    # delete_at
    delete_at_date = datetime.datetime.strptime(delete_at, '%Y%m%d%H%M%S%z')
    assert delete_at_date == deleted_at_date + datetime.timedelta(days=retention_time)

    # entryTtl, fuzzy check, entryTtl is a counter
    expected_ttl = retention_time * 60 * 60 * 24
    ttl_diff = expected_ttl - int(entry_ttl)
    assert ttl_diff < 100, f'diff of expected_ttl ({expected_ttl}) and real ttl ({entry_ttl}) is too big'


def test_create_container_udm_cli_internal(udm, lo):
    name = random_username()
    udm.create_object('container/cn', position='cn=internal', name=name)
    assert lo.get(f'cn={name},cn=internal')


def test_create_not_allowed(udm, deleted_object_user_properties):
    del deleted_object_user_properties.__dict__['ldap_attrs']
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_object('recyclebin/removedobject', **deleted_object_user_properties.__dict__)


def test_create_and_restore(deleted_object_user_properties, lo):
    mod = udm_modules.get('recyclebin/removedobject')
    users = udm_modules.get('users/user')
    obj = mod.object(None, lo, position(RECYCLEBIN_DN))
    obj.open()
    obj['originalDN'] = deleted_object_user_properties.originalDN
    obj['purgeAt'] = deleted_object_user_properties.purgeAt
    obj['removalDate'] = deleted_object_user_properties.removalDate
    obj['originalObjectType'] = deleted_object_user_properties.originalObjectType
    obj['originalUniventionObjectIdentifier'] = deleted_object_user_properties.originalUniventionObjectIdentifier
    obj['originalEntryUUID'] = deleted_object_user_properties.originalEntryUUID
    obj['originalObjectClasses'] = deleted_object_user_properties.originalObjectClasses
    obj.oldattr = copy.deepcopy(deleted_object_user_properties.ldap_attrs)
    obj.oldattr.update(deleted_object_user_properties.ignore_ldap_attrs)
    user = None
    try:
        # create deleted objct
        obj.create(ignore_license=True)
        # check deleted object
        original_name = deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert mod.lookup(None, lo, f'originalName=*{original_name}*')
        obj = mod.lookup(None, lo, f'univentionRecycleBinOriginalUniventionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}')[0]
        obj.open()
        assert obj['originalDN'] == deleted_object_user_properties.originalDN
        assert obj['purgeAt'] == deleted_object_user_properties.purgeAt
        assert obj['removalDate'] == deleted_object_user_properties.removalDate
        assert obj['originalObjectType'] == deleted_object_user_properties.originalObjectType
        assert obj['originalUniventionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier
        assert obj['originalEntryUUID'] == deleted_object_user_properties.originalEntryUUID
        assert set(obj['originalObjectClasses']) == set(deleted_object_user_properties.originalObjectClasses)
        assert obj['displayName'] == deleted_object_user_properties.ldap_attrs['displayName'][0].decode('UTF-8')
        assert obj['username'] == deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert obj['password'] == deleted_object_user_properties.ldap_attrs['userPassword'][0].decode('UTF-8')
        assert obj['univentionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier
        assert set(obj['groups']) == {x.decode('UTF-8') for x in deleted_object_user_properties.ldap_attrs['memberOf'] if not x.decode('UTF-8').startswith('cn=doesnotexist')}
        assert set(obj.oldattr['objectClass']) == {b'top', b'univentionRecycleBinObject', b'univentionObject', b'extensibleObject', b'dynamicObject'}
        for key, values in deleted_object_user_properties.ldap_attrs.items():
            if key == 'memberOf':
                assert set(obj.oldattr[key]) == {x for x in values if not x.decode('UTF-8').startswith('cn=doesnotexist')}
            else:
                assert set(obj.oldattr[key]) == set(values), key
        # restore
        dn = obj.restore()
        assert dn == deleted_object_user_properties.originalDN
        # check deleted object has been removed
        assert [] == mod.lookup(None, lo, f'originalUniventionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}')
        # check restored object
        user = users.lookup(None, lo, None, base=deleted_object_user_properties.originalDN, unique=True, required=True)[0]
        user.open()
        assert user['username'] == deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert user['displayName'] == deleted_object_user_properties.ldap_attrs['displayName'][0].decode('UTF-8')
        assert set(user['groups']) == {
            x.decode('UTF-8') for x in deleted_object_user_properties.ldap_attrs['memberOf']
            if not x.decode('UTF-8').startswith('cn=doesnotexist')
        }
        assert user['univentionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier
        assert user.dn == deleted_object_user_properties.originalDN
        for key, values in deleted_object_user_properties.ldap_attrs.items():
            if key == 'memberOf':
                assert set(user.oldattr[key]) == {x for x in values if not x.decode('UTF-8').startswith('cn=doesnotexist')}
            else:
                assert set(user.oldattr[key]) == set(values)
        assert {x.decode('UTF-8') for x in user.oldattr['objectClass']} == set(deleted_object_user_properties.originalObjectClasses)
        user.remove()
    finally:
        try:
            obj.remove()
        except noObject:
            pass
        user = users.lookup(None, lo, f'univentionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}')
        if user:
            user[0].open()
            user[0].remove()


def test_user_restore_umc(udm, recyclebin_policy_session, lo, Client):
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    group_dn, _ = udm.create_group(position=container_recyclebin_policy)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    # goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    con = Client.get_test_connection(language='en-US')
    # search
    search_options = {
        'hidden': False,
        'objectType': 'recyclebin/removedobject',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'path'],
    }
    res = con.umc_command('udm/query', search_options, 'recyclebin/removedobject').result
    dn = [v['$dn$'] for v in res if v['name'] == username]
    assert dn and len(dn) == 1
    # simulate detail page, we had a problem that search no longer works after detail page
    options = [deleted_dn]
    res = con.umc_command('udm/get', options, 'recyclebin/removedobject').result[0]
    assert res['username'] == username
    assert res['groups']
    assert res['originalDN'] == user_dn
    options = [{'objectType': 'recyclebin/removedobject', 'objectDN': deleted_dn}]
    res = con.umc_command('udm/properties', options, 'recyclebin/removedobject').result[0]
    assert 'username' in [v['id'] for v in res]
    res = con.umc_command('udm/layout', options, 'recyclebin/removedobject').result[0]
    labels = [v['label'] for v in res]
    assert 'Account' in labels or 'Konto' in labels
    # search again
    res = con.umc_command('udm/query', search_options, 'recyclebin/removedobject').result
    assert res
    dn = [v['$dn$'] for v in res if v['name'] == username]
    assert dn and len(dn) == 1
    # restore
    options = [{'object': deleted_dn}]
    con.umc_command('udm/restore', options, 'recyclebin/removedobject')
    assert lo.get(user_dn)


def test_user_search_filter_umc(udm, recyclebin_policy_session, lo, Client):
    def _check_search(con, username, options):
        res = con.umc_command('udm/query', options, 'recyclebin/removedobject').result
        dn = [v['$dn$'] for v in res if v['name'] == username]
        assert dn and len(dn) == 1

    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    con = Client.get_test_connection()
    options = {
        'hidden': False,
        'objectType': 'recyclebin/removedobject',
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'path'],
    }
    search_attrs = [
        ('originalName', username),
        ('originalObjectType', 'users/user'),
    ]
    for prop, value in search_attrs:
        options['objectProperty'] = prop
        options['objectPropertyValue'] = value
        _check_search(con, username, options)


@pytest.mark.parametrize('listener_running', [True, False], ids=['listener running', 'listener stopped'])
def test_user_restore(udm, recyclebin_policy_session, ldap_base, lo, listener_running):
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    group1_dn, _ = udm.create_group(wait_for_replication=False)
    group2_dn, _ = udm.create_group(wait_for_replication=False)
    group3_dn, _ = udm.create_group(wait_for_replication=False)
    password = '&%$§§"%saidaa'
    user_dn, username = udm.create_user(groups=[group1_dn, group2_dn, group3_dn], password=password, position=container_recyclebin_policy)
    original_props = udm.get_object('users/user', user_dn)
    uoi = original_props['univentionObjectIdentifier'][0]
    if not listener_running:
        stop_listener()
    udm.remove_object('users/user', dn=user_dn, wait_for_replication=False)
    # auth does not work
    with pytest.raises(authFail):
        access(binddn=user_dn, bindpw=password, base=ldap_base)
    if not listener_running:
        # also remove one of the groups in this case
        udm.remove_object('groups/group', dn=group2_dn, wait_for_replication=False)
        original_props['groups'].remove(group2_dn)
        start_listener()
    wait_for_listener_replication()
    # some search test, also with wildcard
    assert udm.list_objects('recyclebin/removedobject', filter=f'originalUniventionObjectIdentifier={uoi}')
    assert udm.list_objects('recyclebin/removedobject', filter=f'univentionRecycleBinOriginalUniventionObjectIdentifier={uoi}')
    assert udm.list_objects('recyclebin/removedobject', filter=f'originalName={username}')
    assert udm.list_objects('recyclebin/removedobject', filter=f'originalName={username[:-1]}*')
    assert udm.list_objects('recyclebin/removedobject', filter=f'originalName=*{username[1:]}')
    assert udm.list_objects('recyclebin/removedobject', filter=f'originalUniventionObjectIdentifier={uoi[:-1]}*')
    # check ttl and purgeAt
    del_obj_dn, _ = udm.list_objects('recyclebin/removedobject', filter=f'originalDN={user_dn}')[0]
    verify_entryttl_deleteat(retention_time, del_obj_dn, lo)
    # restore
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=del_obj_dn)
    restored_props = udm.get_object('users/user', restored_dn)
    assert restored_dn == user_dn
    access(binddn=restored_dn, bindpw=password, base=ldap_base)
    for key in original_props.keys():
        assert set(original_props[key]) == set(restored_props[key]), key


def test_group_restore(udm, recyclebin_policy_session, ldap_base, lo):
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    memberOf_group_dn, _ = udm.create_group(wait_for_replication=False)
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy, memberOf=[memberOf_group_dn])
    member_group_dn, _ = udm.create_group(wait_for_replication=False, memberOf=[group_dn])  # noqa: RUF059
    member_user1_dn = udm.create_user(wait_for_replication=False, groups=[group_dn])  # noqa: F841
    member_user2_dn = udm.create_user(wait_for_replication=False, groups=[group_dn])  # noqa: F841
    member_computers_linux_dn = udm.create_object('computers/linux', name=random_username(), groups=[group_dn])  # noqa: F841
    original_props = udm.get_object('groups/group', group_dn)
    uoi = original_props['univentionObjectIdentifier'][0]  # noqa: F841
    # delete
    udm.remove_object('groups/group', dn=group_dn)
    # check ttl and purgeAt
    del_obj_dn, _ = udm.list_objects('recyclebin/removedobject', filter=f'originalDN={group_dn}')[0]
    verify_entryttl_deleteat(retention_time, del_obj_dn, lo)
    # restore
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=del_obj_dn)
    restored_props = udm.get_object('groups/group', restored_dn)
    assert restored_dn == group_dn
    for key in original_props.keys():
        assert set(original_props[key]) == set(restored_props[key]), key


def test_recyclebin_container_exists(lo):
    """Test that the recyclebin container exists in cn=internal"""
    attrs = lo.get(RECYCLEBIN_DN)
    assert attrs is not None
    assert b'organizationalRole' in attrs['objectClass']
    assert attrs['cn'][0].decode('utf-8') == 'recyclebin'


def test_user_delete_moves_to_trash_bin(udm, lo, recyclebin_policy_session):
    """Test that deleted user objects are moved to trash bin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    verify_ldap_object(user_dn, should_exist=True)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0
    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_group_delete_moves_to_trash_bin(udm, lo, recyclebin_policy_session):
    """Test that deleted group objects are moved to trash bin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    verify_ldap_object(group_dn, should_exist=True)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)
    deleted_objects = _find_deleted_objects(lo, group_dn)
    assert len(deleted_objects) > 0, 'Group should be found in recycle bin'
    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_referenced_by_tracking(udm, lo, recyclebin_policy_session):
    """Test that referencedBy field tracks objects that reference the deleted object"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy, users=[user_dn])
    group_attrs = lo.get(group_dn)
    assert group_attrs.get('uniqueMember', [])
    assert group_attrs.get('memberUid', [])
    udm.remove_object('users/user', dn=user_dn)
    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0, 'User should be found in recycle bin'
    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_multiple_object_types_deletion(udm, lo, recyclebin_policy_session):
    """Test that different types of LDAP objects can be moved to trash bin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    test_objects = []
    test_objects.append(('users/user', user_dn))
    test_objects.append(('groups/group', group_dn))
    deleted_dns = []
    for obj_type, obj_dn in test_objects:
        udm.remove_object(obj_type, dn=obj_dn)
        verify_ldap_object(obj_dn, should_exist=False)
        deleted_objects = _find_deleted_objects(lo, obj_dn)
        assert len(deleted_objects) > 0
        deleted_dns.extend([obj['dn'] for obj in deleted_objects])
    for deleted_dn in deleted_dns:
        _cleanup_deleted_object(lo, deleted_dn)


def test_extensible_object_direct_attribute_storage(udm, lo, recyclebin_policy_session):
    """Test that deleted objects use extensibleObject to store original attributes directly"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn)
    original_uid = original_attrs['uid'][0].decode('utf-8')
    original_givenName = original_attrs['givenName'][0].decode('utf-8')
    original_sn = original_attrs['sn'][0].decode('utf-8')
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(deleted_dn)
    assert 'extensibleObject' in [oc.decode('utf-8') for oc in deleted_attrs['objectClass']]
    assert 'univentionRecycleBinObject' in [oc.decode('utf-8') for oc in deleted_attrs['objectClass']]
    assert 'univentionRecycleBinOriginalDN' in deleted_attrs
    assert 'univentionRecycleBinOriginalType' in deleted_attrs
    assert 'univentionRecycleBinDeleteAt' in deleted_attrs
    assert 'uid' in deleted_attrs
    assert 'givenName' in deleted_attrs
    assert 'sn' in deleted_attrs
    assert deleted_attrs['uid'][0].decode('utf-8') == original_uid
    assert deleted_attrs['givenName'][0].decode('utf-8') == original_givenName
    assert deleted_attrs['sn'][0].decode('utf-8') == original_sn
    stored_original_dn = deleted_attrs['univentionRecycleBinOriginalDN'][0].decode('utf-8')
    assert stored_original_dn == user_dn
    stored_original_type = deleted_attrs['univentionRecycleBinOriginalType'][0].decode('utf-8')
    assert stored_original_type == 'users/user'
    if 'univentionObjectIdentifier' in original_attrs:
        original_uuid = original_attrs['univentionObjectIdentifier'][0]
        if 'univentionObjectIdentifier' in deleted_attrs:
            deleted_uuid = deleted_attrs['univentionObjectIdentifier'][0]
            assert deleted_uuid != original_uuid
    _cleanup_deleted_object(lo, deleted_dn)


def test_restore_deleted_object(udm, lo, recyclebin_policy_session):
    """Test that deleted objects can be restored from the trash bin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert user_dn == restored_dn
    verify_ldap_object(user_dn, should_exist=True)
    source_attrs = lo.get(user_dn)
    assert source_attrs['uid'][0].decode('utf-8') == original_attrs['uid'][0].decode('utf-8')
    assert source_attrs['givenName'][0].decode('utf-8') == original_attrs['givenName'][0].decode('utf-8')
    assert source_attrs['sn'][0].decode('utf-8') == original_attrs['sn'][0].decode('utf-8')


def test_restore_with_name_conflict(udm, lo, recyclebin_policy_session):
    """Test restore behavior when there's a naming conflict at the original location"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    username = random_username()
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, username=username, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    conflicting_user_dn, _ = udm.create_user(position=container_recyclebin_policy, username=username, wait_for_replication=False)
    # restore
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    recyclebin_module = udm_modules.modules['recyclebin/removedobject']
    pos = position(RECYCLEBIN_DN)
    deleted_udm_obj = recyclebin_module.object(None, lo, pos, dn=deleted_dn)
    deleted_udm_obj.open()
    with pytest.raises(uidAlreadyUsed):
        deleted_udm_obj.restore()
    verify_ldap_object(deleted_dn, should_exist=True)
    verify_ldap_object(conflicting_user_dn, should_exist=True)
    _cleanup_deleted_object(lo, deleted_dn)


def test_entryuuid_univention_object_identifier_preservation_across_delete_restore(udm, lo, recyclebin_policy_session):
    """Test that entryUUID is preserved across delete/restore cycle"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    original_attrs = lo.get(user_dn, ['*', '+'])
    original_uuid = original_attrs.get('entryUUID', [None])[0]
    original_id = original_attrs.get('univentionObjectIdentifier', [b''])[0]
    assert original_uuid, 'Original user should have entryUUID'
    assert original_id, 'Original user should have univentionObjectIdentifier'
    udm.remove_object('users/user', dn=user_dn)
    deleted_obj_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(deleted_obj_dn, attr=['*'])
    stored_uuid = deleted_attrs.get('univentionRecycleBinOriginalEntryUUID')
    stored_id = deleted_attrs.get('univentionRecycleBinOriginalUniventionObjectIdentifier')
    assert stored_uuid[0] == original_uuid
    assert stored_id[0] == original_id
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_obj_dn)
    assert restored_dn == user_dn
    source_attrs = lo.get(user_dn, attr=['*', '+'])
    restored_uuid = source_attrs.get('entryUUID', [None])[0]
    restored_id = source_attrs.get('univentionObjectIdentifier', [None])[0]
    assert restored_uuid == original_uuid
    assert restored_id == original_id
    # Cleanup
    lo.delete(user_dn)


def test_delete_at_timestamp_based_on_retention_policy(udm, lo, recyclebin_policy_session):
    """Test that purgeAt timestamp is calculated based on retention policy."""
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_entryttl_deleteat(retention_time, deleted_dn, lo)
    # Cleanup
    lo.delete(deleted_dn)


def test_user_group_restoration_comprehensive(udm, lo, recyclebin_policy_session):
    """Test restoration of users and groups with preserved relationships"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, groups=[group_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    group_attrs = lo.get(group_dn)
    assert user_dn.encode('utf-8') in group_attrs.get('uniqueMember', [])
    # remove
    udm.remove_object('users/user', dn=user_dn, wait_for_replication=False)
    verify_ldap_object(user_dn, should_exist=False)
    user_deleted_dn = _deleted_object_dn(user_dn, uoid)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)
    group_deleted_dn = _deleted_object_dn(group_dn, goid)
    # restore
    udm.restore_object('recyclebin/removedobject', dn=group_deleted_dn)
    verify_ldap_object(group_dn, should_exist=True)
    udm.restore_object('recyclebin/removedobject', dn=user_deleted_dn)
    verify_ldap_object(user_dn, should_exist=True)
    # check
    group_attrs = lo.get(group_dn)
    assert user_dn.encode('utf-8') in group_attrs.get('uniqueMember', [])
    # cleanup
    lo.delete(user_dn)
    lo.delete(group_dn)


def test_user_multiple_groups_deletion_restoration(udm, lo, recyclebin_policy_session):
    """Test deletion and restoration of user belonging to multiple groups"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    group1_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    group2_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    group3_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, groups=[group1_dn, group2_dn, group3_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    verify_ldap_object(group1_dn, should_exist=True)
    verify_ldap_object(group2_dn, should_exist=True)
    verify_ldap_object(group3_dn, should_exist=True)
    for dn in [group1_dn, group2_dn, group3_dn]:
        attrs = lo.get(dn)
        assert user_dn.encode('utf-8') in attrs.get('uniqueMember', [])
    # remove
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    for dn in [group1_dn, group2_dn, group3_dn]:
        attrs = lo.get(dn)
        assert user_dn.encode('utf-8') not in attrs.get('uniqueMember', [])
    # restore user
    user_deleted_dn = _deleted_object_dn(user_dn, uoid)
    udm.restore_object('recyclebin/removedobject', dn=user_deleted_dn)
    verify_ldap_object(user_dn, should_exist=True)
    # check
    for dn in [group1_dn, group2_dn, group3_dn]:
        attrs = lo.get(dn)
        assert user_dn.encode('utf-8') in attrs.get('uniqueMember', [])


def test_policy_references_restoration(udm, lo, recyclebin_policy_session, ldap_base):
    """Test that policy references are properly restored after object restoration"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    policy_dn = udm.create_object('policies/pwhistory', name=random_username(), position=f'cn=policies,{ldap_base}', length=5, pwLength=10)
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, policy_reference=[policy_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    verify_ldap_object(policy_dn, should_exist=True)
    user_attrs = lo.get(user_dn)
    assert policy_dn.encode('utf-8') in user_attrs.get('univentionPolicyReference', [])
    # remove
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    user_deleted_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(user_deleted_dn)
    assert policy_dn.encode('utf-8') in deleted_attrs.get('univentionPolicyReference', [])
    # restore
    udm.restore_object('recyclebin/removedobject', dn=user_deleted_dn)
    verify_ldap_object(user_dn, should_exist=True)
    restored_user_attrs = lo.get(user_dn)
    assert policy_dn.encode('utf-8') in restored_user_attrs.get('univentionPolicyReference', [])


def test_policy_disabled_check(udm, lo, ldap_base):
    """Test that recyclebin respects the enabled/disabled policy setting"""
    container_dn = udm.create_object('container/cn', position=ldap_base, name=f'test-disabled-{random_username()}', wait_for_replication=False)
    policy_dn = udm.create_object(
        'policies/recyclebin',
        name=f'test-disabled-policy-{random_username()}',
        enabled='FALSE',
        udm_modules=['users/user'],
        retention_time='30',
        wait_for_replication=False,
    )
    udm.modify_object('container/cn', dn=container_dn, policy_reference=[policy_dn], wait_for_replication=False)
    user_dn, _ = udm.create_user(position=container_dn, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=False)


def test_listener_cache_behavior(udm, lo, recyclebin_policy_session):
    """Test listener cache tracks deleted objects correctly"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn1, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid1 = udm.get_object('users/user', user_dn1)['univentionObjectIdentifier'][0]
    user_dn2, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid2 = udm.get_object('users/user', user_dn2)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn1, should_exist=True)
    verify_ldap_object(user_dn2, should_exist=True)
    udm.remove_object('users/user', dn=user_dn1, wait_for_replication=False)
    udm.remove_object('users/user', dn=user_dn2)
    verify_ldap_object(user_dn1, should_exist=False)
    verify_ldap_object(user_dn2, should_exist=False)
    deleted_dn1 = _deleted_object_dn(user_dn1, uoid1)
    deleted_dn2 = _deleted_object_dn(user_dn2, uoid2)
    assert user_dn1.encode('UTF-8') in lo.get(deleted_dn1).get('univentionRecycleBinOriginalDN', [])
    assert user_dn2.encode('UTF-8') in lo.get(deleted_dn2).get('univentionRecycleBinOriginalDN', [])
    _cleanup_deleted_object(lo, deleted_dn1)
    _cleanup_deleted_object(lo, deleted_dn2)


def test_recyclebin_type_limitation(udm, lo, recyclebin_policy_session):
    """Test that recyclebin only processes users and groups, not computers"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    computer_dn = udm.create_object('computers/linux', position=container_recyclebin_policy, name=random_username())
    uoid = udm.get_object('computers/linux', computer_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(computer_dn, should_exist=True)
    udm.remove_object('computers/linux', dn=computer_dn)
    verify_ldap_object(computer_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(computer_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=False)


def test_original_name_extraction_and_storage(udm, lo, recyclebin_policy_session):
    """Test that originalName is properly extracted and stored for different object types"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    group_dn, groupname = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn, wait_for_replication=False)
    udm.remove_object('groups/group', dn=group_dn, wait_for_replication=False, remove_referring=False)
    # check originalName
    verify_ldap_object(user_dn, should_exist=False)
    verify_ldap_object(group_dn, should_exist=False)
    deleted_user_dn = _deleted_object_dn(user_dn, uoid)
    deleted_group_dn = _deleted_object_dn(group_dn, goid)
    recyclebin_module = udm_modules.modules['recyclebin/removedobject']
    pos = position(RECYCLEBIN_DN)
    deleted_user_obj = recyclebin_module.object(None, lo, pos, dn=deleted_user_dn)
    deleted_user_obj.open()
    deleted_group_obj = recyclebin_module.object(None, lo, pos, dn=deleted_group_dn)
    deleted_group_obj.open()
    assert deleted_user_obj.info['originalName'] == username
    assert deleted_group_obj.info['originalName'] == groupname
    # search originalName
    res = udm.list_objects('recyclebin/removedobject', filter=f'originalName={username}')
    assert len(res) == 1 and username in res[0][1]['originalName']
    res = udm.list_objects('recyclebin/removedobject', filter=f'originalName={groupname}')
    assert len(res) == 1 and groupname in res[0][1]['originalName']
    # cleanup
    _cleanup_deleted_object(lo, deleted_user_dn)
    _cleanup_deleted_object(lo, deleted_group_dn)


def test_dds_automatic_purging_enabled(udm, lo, recyclebin_policy_session, ucr):
    """Test that DDS automatic purging is enabled for recyclebin objects"""
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(deleted_dn)
    object_classes = [cls.decode('utf-8') for cls in deleted_attrs.get('objectClass', [])]
    assert 'dynamicObject' in object_classes
    verify_entryttl_deleteat(retention_time, deleted_dn, lo)
    # manually update ttls and check if slapd purges the entry
    # we need ldap/database/internal/dds/min-ttl='1' for that to work
    ucr.handler_set(['ldap/database/internal/dds/min-ttl=1'])
    restart_slapd()
    loa, _ = getAdminConnection()
    ttl_seconds = 3
    refresh_req = RefreshRequest(entryName=deleted_dn, requestTtl=ttl_seconds)
    loa.lo.lo.extop_s(refresh_req, serverctrls=[])
    time.sleep(ttl_seconds)
    restart_slapd()
    for i in range(60):
        time.sleep(ttl_seconds)
        if not lo.get(deleted_dn):
            break
    assert not lo.get(deleted_dn), '{deleted_dn} should be deleted, but still exists'
    # cleanup
    _cleanup_deleted_object(lo, deleted_dn)


def test_reference_based_restoration(udm, lo, recyclebin_policy_session):
    """Test that relationships are restored using generic references with UUIDs"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    group_attrs = lo.get(group_dn, attr=['univentionObjectIdentifier'])
    group_uuid = group_attrs['univentionObjectIdentifier'][0].decode('utf-8')
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, groups=[group_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    user_attrs = lo.get(user_dn, attr=['memberOf'])
    member_of = [dn.decode('utf-8') for dn in user_attrs.get('memberOf', [])]
    assert group_dn in member_of
    # remove
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(deleted_dn)
    references = deleted_attrs.get('univentionRecycleBinReference', [])
    assert len(references) > 0
    stored_references = [ref.decode('utf-8') for ref in references]
    assert any(group_uuid in ref for ref in stored_references)
    # restore
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert restored_dn == user_dn
    verify_ldap_object(user_dn, should_exist=True)
    source_attrs = lo.get(user_dn, attr=['memberOf'])
    member_of = [dn.decode('utf-8') for dn in source_attrs.get('memberOf', [])]
    assert group_dn in member_of


def test_reference_restoration_with_colon_in_username(udm, lo, recyclebin_policy_session, ldap_base):
    """Test that references work correctly when DNs/values contain colons"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    test_uuid = '550e8400:e29b:41d4:a716:446655440000'
    test_dn = f'uid=test:user:123,cn=users,{ldap_base}'
    ref = str(Reference('dn', 'groups/group', 'users', 'uuid', test_uuid))
    parsed = Reference.parse(ref)
    assert parsed.lookup_value == test_uuid
    ref_dn = str(Reference('dn', 'groups/group', 'users', 'dn', test_dn))
    parsed_dn = Reference.parse(ref_dn)
    assert parsed_dn.lookup_value == test_dn
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    group_attrs = lo.get(group_dn, attr=['univentionObjectIdentifier'])
    group_uuid = group_attrs['univentionObjectIdentifier'][0].decode('utf-8')
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, groups=[group_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    user_attrs = lo.get(user_dn, attr=['memberOf'])
    member_of = [dn.decode('utf-8') for dn in user_attrs.get('memberOf', [])]
    assert group_dn in member_of
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    deleted_attrs = lo.get(deleted_dn)
    references = deleted_attrs.get('univentionRecycleBinReference', [])
    assert len(references) > 0
    stored_references = [ref.decode('utf-8') for ref in references]
    assert any(group_uuid in ref for ref in stored_references)
    for ref in stored_references:
        parsed = Reference.parse(ref)
        assert parsed is not None
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert restored_dn == user_dn
    verify_ldap_object(user_dn, should_exist=True)
    source_attrs = lo.get(user_dn, attr=['memberOf'])
    member_of = [dn.decode('utf-8') for dn in source_attrs.get('memberOf', [])]
    assert group_dn in member_of


def test_structured_logging_for_recyclebin_operations(udm, lo, recyclebin_policy_session):
    """Test that structured logging is working for recyclebin operations"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.INFO)
    log.addHandler(handler)
    try:
        user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
        uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
        udm.remove_object('users/user', dn=user_dn)
        deleted_dn = _deleted_object_dn(user_dn, uoid)
        recyclebin_module = udm_modules.modules['recyclebin/removedobject']
        deleted_user_obj = recyclebin_module.object(None, lo, position(RECYCLEBIN_DN), dn=deleted_dn)
        deleted_user_obj.open()
        restored_dn = deleted_user_obj.restore()
        log_output = log_capture.getvalue()
        assert 'Object restored from recyclebin' in log_output
        # FIXME: we don't have the additional info in log_output?
        # assert 'event_type=delete' in log_output or 'event_type":"delete"' in log_output
        # assert 'status=success' in log_output or 'status":"success"' in log_output
        # assert 'event_type=restore' in log_output or 'event_type":"restore"' in log_output
        lo.delete(restored_dn)
    finally:
        log.root.removeHandler(handler)


@pytest.fixture
def blocklist_username(ucr, udm):
    ucr.handler_set(['directory/manager/blocklist/enabled=true'])
    udm.stop_cli_server()
    name = random_username()
    dn = udm.create_object('blocklists/list', name=name, blockingProperties=['users/user username'], wait_for_replication=False)
    return SimpleNamespace(cn=name, dn=dn)


def blocklistentry_dn(value, blocklist_dn):
    value_hashed = hash_blocklist_value(value.encode('UTF-8'))
    return f'cn={value_hashed},{blocklist_dn}'


def get_blocklist_entry(lo, value, blocklist_dn):
    return lo.get(blocklistentry_dn(value, blocklist_dn))


def test_blocklist_same_id_not_blocked(udm, lo, recyclebin_policy_session, blocklist_username):
    container_recyclebin_policy, _ = recyclebin_policy_session
    username = random_username()
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, username=username, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    assert get_blocklist_entry(lo, username, blocklist_username.dn), 'blocklist entry for username is missing'
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert restored_dn == user_dn
    assert lo.get(user_dn)


def test_blocklist_different_id_blocked(udm, lo, recyclebin_policy_session, blocklist_username):
    container_recyclebin_policy, _ = recyclebin_policy_session
    username = random_username()
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, username=username, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    attrs = get_blocklist_entry(lo, username, blocklist_username.dn)
    # change id on blocklist entry
    changes = [('originUniventionObjectIdentifier', attrs['originUniventionObjectIdentifier'], str(uuid.uuid4()).encode('UTF-8'))]
    lo.modify(blocklistentry_dn(username, blocklist_username.dn), changes)
    # now restore, should fail, restore with UDM to get the proper exception
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    recyclebin_module = udm_modules.modules['recyclebin/removedobject']
    obj = recyclebin_module.object(None, lo, position(RECYCLEBIN_DN), dn=deleted_dn)
    obj.open()
    # mock blocklist_enabled as it does not see the temp UCR changes (directory/manager/blocklist/enabled=true)
    import univention.admin.blocklist

    univention.admin.blocklist.blocklist_enabled = lambda x: True
    with pytest.raises(valueError) as exc:
        obj.restore()
    assert f'The value "{username}" is blocked for the property "username".' == str(exc.value)


def test_uuid_lookup_from_recyclebin_when_group_deleted_first(udm, lo, recyclebin_policy_session):
    """Test that UUID is looked up from recyclebin when referenced group is already deleted"""
    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create group and get its UUID
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    group_attrs = lo.get(group_dn, attr=['univentionObjectIdentifier'])
    group_uuid = group_attrs['univentionObjectIdentifier'][0].decode('utf-8')

    # Create user with membership in that group
    user_dn, _ = udm.create_user(
        position=container_recyclebin_policy,
        groups=[group_dn],
        wait_for_replication=False,
    )
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    user_attrs = lo.get(user_dn, attr=['memberOf'])
    member_of = [dn.decode('utf-8') for dn in user_attrs.get('memberOf', [])]
    assert group_dn in member_of, 'User should be member of group'

    # Delete group first (moves to recyclebin)
    # Note: Don't use remove_referring to keep user's group membership intact
    import subprocess

    subprocess.run(
        [
            '/usr/sbin/udm-test',
            'groups/group',
            'remove',
            '--dn',
            group_dn,
        ],
        check=True,
    )
    verify_ldap_object(group_dn, should_exist=False)
    deleted_group_dn = _deleted_object_dn(group_dn, goid)
    verify_ldap_object(deleted_group_dn, should_exist=True)

    # Delete user second (should find group UUID in recyclebin)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_user_dn = _deleted_object_dn(user_dn, uoid)

    # Verify that user's references include our test group with UUID from recyclebin
    deleted_user_attrs = lo.get(deleted_user_dn)
    references = deleted_user_attrs.get('univentionRecycleBinReference', [])
    assert len(references) > 0, 'User should have at least one reference'

    stored_references = [ref.decode('utf-8') for ref in references]

    # Check that reference contains the group UUID (from recyclebin lookup)
    # Note: User may also have references to other groups like Domain Users
    test_group_found = False
    all_group_refs = []
    for ref in stored_references:
        parsed = Reference.parse(ref)
        if parsed and parsed.target_module == 'groups/group':
            all_group_refs.append(parsed)
            if parsed.lookup_value == group_uuid:
                # Found our test group - verify it uses UUID lookup
                assert parsed.lookup_attribute == 'uuid', f'Reference should use UUID lookup, got: {parsed.lookup_attribute}'
                test_group_found = True

    assert test_group_found, (
        f'Should have found a reference with test group UUID {group_uuid}. Group references found: {[(r.lookup_attribute, r.lookup_value) for r in all_group_refs]}'
    )

    # Cleanup
    _cleanup_deleted_object(lo, deleted_user_dn)
    _cleanup_deleted_object(lo, deleted_group_dn)


def test_uuid_lookup_from_recyclebin_feature(udm, lo, recyclebin_policy_session):
    """Test that references use UUID (not DN) when objects exist in active LDAP"""
    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create group and get UUID
    group_dn, _ = udm.create_group(position=container_recyclebin_policy, wait_for_replication=False)
    group_attrs = lo.get(group_dn, attr=['univentionObjectIdentifier'])
    group_uuid = group_attrs['univentionObjectIdentifier'][0].decode('utf-8')

    # Create user in group
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, groups=[group_dn], wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]

    # Delete user (group still active)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_user_dn = _deleted_object_dn(user_dn, uoid)

    # Verify references use UUID (from active LDAP)
    deleted_user_attrs = lo.get(deleted_user_dn)
    references = deleted_user_attrs.get('univentionRecycleBinReference', [])
    assert len(references) > 0, 'User should have at least one reference'

    stored_references = [ref.decode('utf-8') for ref in references]

    # Check that group reference uses UUID lookup (not DN)
    group_found = False
    for ref in stored_references:
        parsed = Reference.parse(ref)
        if parsed and parsed.target_module == 'groups/group':
            if parsed.lookup_value == group_uuid:
                assert parsed.lookup_attribute == 'uuid', f'Should use UUID lookup, got: {parsed.lookup_attribute}'
                group_found = True
                break

    assert group_found, f'Expected group UUID {group_uuid} in references, got: {stored_references}'

    # Cleanup
    _cleanup_deleted_object(lo, deleted_user_dn)


def test_deleted_user_with_complex_attributes_display(udm, lo, recyclebin_policy_session, share_for_testing_session):
    """Test reading deleted user with primaryGroup, homeShare and complex text attributes via UDM"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    share_dn = share_for_testing_session
    group_dn, _ = udm.create_group(position=container_recyclebin_policy, wait_for_replication=False)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]

    username = random_username()
    user_dn = udm.create_object(
        'users/user',
        position=container_recyclebin_policy,
        username=username,
        lastname=random_username(),
        password='univention',
        primaryGroup=group_dn,
        homeShare=share_dn,
        homeSharePath=username,
        description='Complex user\nwith multiline\ndescription',
        organisation='Test Organisation GmbH',
        title='Dr. Ing.',
        employeeNumber='EMP-12345',
        employeeType='Software Developer',
        wait_for_replication=False,
    )
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]

    original_attrs = lo.get(user_dn)
    original_share_host = original_attrs.get('univentionShareHost', [])
    original_share_path = original_attrs.get('univentionSharePath', [])

    udm.remove_object('users/user', dn=user_dn, wait_for_replication=False)
    verify_ldap_object(user_dn, should_exist=False)

    udm.remove_object('groups/group', dn=group_dn, wait_for_replication=False, remove_referring=False)
    verify_ldap_object(group_dn, should_exist=False)

    deleted_user_dn = _deleted_object_dn(user_dn, uoid)
    deleted_group_dn = _deleted_object_dn(group_dn, goid)

    recyclebin_module = udm_modules.modules['recyclebin/removedobject']
    pos = position(RECYCLEBIN_DN)
    deleted_user_obj = recyclebin_module.object(None, lo, pos, dn=deleted_user_dn)
    deleted_user_obj.open()

    assert deleted_user_obj.info['originalName'] == username
    assert deleted_user_obj.info['originalDN'] == user_dn
    assert deleted_user_obj.info['originalObjectType'] == 'users/user'

    deleted_ldap_attrs = lo.get(deleted_user_dn)
    assert b'Complex user' in deleted_ldap_attrs.get('description', [b''])[0]
    assert b'Test Organisation' in deleted_ldap_attrs.get('o', [b''])[0]
    assert b'Dr. Ing.' in deleted_ldap_attrs.get('title', [b''])[0]
    assert b'EMP-12345' in deleted_ldap_attrs.get('employeeNumber', [b''])[0]
    assert b'Software Developer' in deleted_ldap_attrs.get('employeeType', [b''])[0]

    if original_share_host:
        deleted_share_host = deleted_ldap_attrs.get('univentionShareHost', [])
        assert deleted_share_host == original_share_host, 'Share host should be preserved'
    if original_share_path:
        deleted_share_path = deleted_ldap_attrs.get('univentionSharePath', [])
        assert deleted_share_path == original_share_path, 'Share path should be preserved'

    res = udm.list_objects('recyclebin/removedobject', filter=f'originalName={username}')
    assert len(res) == 1 and username in res[0][1]['originalName']

    _cleanup_deleted_object(lo, deleted_user_dn)
    _cleanup_deleted_object(lo, deleted_group_dn)
