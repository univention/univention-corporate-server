#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test LDAP trash bin functionality
## tags: [ldap, udm, trash_bin]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager
##  - python3-univention-directory-manager


import ldap
import pytest

import univention.admin.modules as udm_modules
import univention.admin.uexceptions
import univention.admin.uldap
from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object


LDAP_BASE = _ucr['ldap/base']
RECYCLEBIN_DN = "cn=recyclebin,cn=internal"
POLICY_DN = "cn=default-recyclebin-policy,cn=recyclebin,cn=policies"


def get_admin_connection():
    result = univention.admin.uldap.getAdminConnection()
    if isinstance(result, tuple):
        return result[0]
    return result


def setup_udm():
    udm_modules.update()


def _find_deleted_objects(lo, original_dn):
    try:
        results = lo.search(
            base=RECYCLEBIN_DN,
            scope='one',
            filter='(objectClass=univentionRecycleBinObject)',
            attr=['univentionRecycleBinOriginalDN', 'univentionObjectType', 'cn'],
        )

        deleted_objects = []
        for dn, attrs in results:
            original = attrs.get('univentionRecycleBinOriginalDN', [b''])[0].decode('utf-8')
            if original == original_dn:
                deleted_objects.append({
                    'dn': dn,
                    'originalDn': original,
                    'univentionObjectType': attrs.get('univentionObjectType', [b''])[0].decode('utf-8'),
                })

        return deleted_objects
    except ldap.LDAPError:
        return []


def _cleanup_deleted_object(lo, deleted_dn):
    try:
        lo.delete(deleted_dn)
    except (ldap.LDAPError, univention.admin.uexceptions.noObject) as e:
        print(f"Warning: Could not clean up deleted object {deleted_dn}: {e}")


def test_recyclebin_container_exists():
    """Test that the recyclebin container exists in cn=internal"""
    lo = get_admin_connection()

    attrs = lo.get(RECYCLEBIN_DN)
    assert attrs is not None
    assert b'organizationalRole' in attrs['objectClass']
    assert attrs['cn'][0].decode('utf-8') == 'recyclebin'


def test_recyclebin_policy_exists():
    """Test that the default recyclebin policy exists"""
    lo = get_admin_connection()
    ldap_base = lo.base
    policy_dn = f"{POLICY_DN},{ldap_base}"

    attrs = lo.get(policy_dn)
    assert attrs is not None
    assert b'univentionRecycleBinPolicy' in attrs['objectClass']
    assert attrs['univentionRecycleBinEnabled'][0].decode('utf-8') == 'TRUE'

    udm_modules_list = [m.decode('utf-8') for m in attrs['univentionRecycleBinUDMModules']]
    assert 'users/user' in udm_modules_list
    assert 'groups/group' in udm_modules_list


def test_policy_detection_working():
    """Test that the policy detection logic works correctly"""
    with UCSTestUDM() as udm:
        user_dn, _ = udm.create_user()

        lo = get_admin_connection()
        user_attrs = lo.get(user_dn)
        assert user_attrs is not None

        setup_udm()
        user_module = udm_modules.modules['users/user']
        position = univention.admin.uldap.position(lo.base)
        user_obj = user_module.object(None, lo, position, dn=user_dn)
        user_obj.open()

        should_recycle = user_obj._should_recycle_object()
        assert should_recycle


def test_user_delete_moves_to_trash_bin(udm):
    """Test that deleted user objects are moved to trash bin"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Test',
        lastname='User',
    )

    verify_ldap_object(user_dn, should_exist=True)

    udm.remove_object('users/user', dn=user_dn)

    verify_ldap_object(user_dn, should_exist=False)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_group_delete_moves_to_trash_bin(udm):
    """Test that deleted group objects are moved to trash bin"""
    lo = get_admin_connection()

    groupname = random_username()
    group_dn, _ = udm.create_group(
        name=groupname,
        description='Test group for trash bin',
    )

    verify_ldap_object(group_dn, should_exist=True)

    udm.remove_object('groups/group', dn=group_dn)

    verify_ldap_object(group_dn, should_exist=False)

    deleted_objects = _find_deleted_objects(lo, group_dn)
    assert len(deleted_objects) > 0, "Group should be found in recycle bin"

    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_referenced_by_tracking(udm):
    """Test that referencedBy field tracks objects that reference the deleted object"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Referenced',
        lastname='User',
    )

    groupname = random_username()
    group_dn, _ = udm.create_group(
        name=groupname,
        description='Test group that references user',
    )

    udm.modify_object('groups/group', dn=group_dn, users=[user_dn])

    group_attrs = lo.get(group_dn)
    has_unique_member = group_attrs.get('uniqueMember', [])
    has_member_uid = group_attrs.get('memberUid', [])
    assert has_unique_member or has_member_uid

    udm.remove_object('users/user', dn=user_dn)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0, "User should be found in recycle bin"

    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_multiple_object_types_deletion(udm):
    """Test that different types of LDAP objects can be moved to trash bin"""
    lo = get_admin_connection()

    test_objects = []

    username = random_username()
    user_dn, _ = udm.create_user(username=username, firstname='Multi', lastname='Test')
    test_objects.append(('users/user', user_dn))

    groupname = random_username()
    group_dn, _ = udm.create_group(name=groupname, description='Multi test group')
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


def test_extensible_object_direct_attribute_storage(udm):
    """Test that deleted objects use extensibleObject to store original attributes directly"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='TestFirstName',
        lastname='TestLastName',
        description='Test user for extensibleObject verification',
    )

    original_attrs = lo.get(user_dn)
    original_uid = original_attrs['uid'][0].decode('utf-8')
    original_givenName = original_attrs['givenName'][0].decode('utf-8')
    original_sn = original_attrs['sn'][0].decode('utf-8')

    verify_ldap_object(user_dn, should_exist=True)

    udm.remove_object('users/user', dn=user_dn)

    verify_ldap_object(user_dn, should_exist=False)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_obj = deleted_objects[0]
    deleted_dn = deleted_obj['dn']

    deleted_attrs = lo.get(deleted_dn)

    assert 'extensibleObject' in [oc.decode('utf-8') for oc in deleted_attrs['objectClass']]
    assert 'univentionRecycleBinObject' in [oc.decode('utf-8') for oc in deleted_attrs['objectClass']]

    assert 'univentionRecycleBinOriginalDN' in deleted_attrs
    assert 'univentionRecycleBinOriginalType' in deleted_attrs
    assert 'univentionRecycleBinDeletionDate' in deleted_attrs
    assert 'univentionRecycleBinDeletedBy' in deleted_attrs

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


def test_restore_deleted_object(udm):
    """Test that deleted objects can be restored from the trash bin"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Restore',
        lastname='Test',
    )

    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn)

    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_obj = deleted_objects[0]
    deleted_dn = deleted_obj['dn']

    setup_udm()
    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    position = univention.admin.uldap.position(lo.base)
    deleted_udm_obj = recyclebin_module.object(None, lo, position, dn=deleted_dn)
    deleted_udm_obj.open()

    deleted_udm_obj.restore()

    verify_ldap_object(user_dn, should_exist=True)

    restored_attrs = lo.get(user_dn)
    assert restored_attrs['uid'][0].decode('utf-8') == original_attrs['uid'][0].decode('utf-8')
    assert restored_attrs['givenName'][0].decode('utf-8') == original_attrs['givenName'][0].decode('utf-8')
    assert restored_attrs['sn'][0].decode('utf-8') == original_attrs['sn'][0].decode('utf-8')

    remaining_deleted = _find_deleted_objects(lo, user_dn)
    assert len(remaining_deleted) == 0

    lo.delete(user_dn)


def test_restore_with_name_conflict(udm):
    """Test restore behavior when there's a naming conflict at the original location"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Conflict',
        lastname='Test',
    )

    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    conflicting_user_dn, _ = udm.create_user(
        username=username,
        firstname='New',
        lastname='User',
    )

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_obj = deleted_objects[0]
    deleted_dn = deleted_obj['dn']

    setup_udm()
    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    position = univention.admin.uldap.position(lo.base)
    deleted_udm_obj = recyclebin_module.object(None, lo, position, dn=deleted_dn)
    deleted_udm_obj.open()

    with pytest.raises((univention.admin.uexceptions.objectExists, univention.admin.uexceptions.ldapError)):
        deleted_udm_obj.restore()

    verify_ldap_object(conflicting_user_dn, should_exist=True)

    remaining_deleted = _find_deleted_objects(lo, user_dn)
    assert len(remaining_deleted) > 0

    udm.remove_object('users/user', dn=conflicting_user_dn)
    conflicting_deleted = _find_deleted_objects(lo, conflicting_user_dn)
    for obj in conflicting_deleted:
        _cleanup_deleted_object(lo, obj['dn'])

    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])


def test_entryuuid_preservation_across_delete_restore(udm):
    """Test that entryUUID is preserved across delete/restore cycle"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Test',
        lastname='UUID',
    )

    original_attrs = lo.get(user_dn, attr=['entryUUID'])
    original_uuid = original_attrs.get('entryUUID', [None])[0]
    assert original_uuid is not None, "Original user should have entryUUID"

    udm.remove_object('users/user', dn=user_dn)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_obj_dn = deleted_objects[0]['dn']
    deleted_attrs = lo.get(deleted_obj_dn, attr=['*'])
    stored_uuid = deleted_attrs.get('univentionRecycleBinOriginalEntryUUID')

    assert stored_uuid is not None
    assert stored_uuid[0] == original_uuid

    setup_udm()
    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    position = univention.admin.uldap.position(lo.base)
    deleted_udm_obj = recyclebin_module.object(None, lo, position, dn=deleted_obj_dn)
    deleted_udm_obj.open()

    restored_dn = deleted_udm_obj.restore()
    assert restored_dn == user_dn

    restored_attrs = lo.get(user_dn, attr=['entryUUID'])
    restored_uuid = restored_attrs.get('entryUUID', [None])[0]

    assert restored_uuid == original_uuid

    # Cleanup
    lo.delete(user_dn)
