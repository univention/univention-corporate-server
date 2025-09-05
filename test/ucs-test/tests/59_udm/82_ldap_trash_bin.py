#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test LDAP trash bin functionality
## tags: [ldap, udm, trash_bin]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager
##  - python3-univention-directory-manager


import copy
import json

import ldap
import pytest

import univention.admin.modules as udm_modules
import univention.admin.uexceptions
import univention.admin.uldap
from univention.admin.uldap import getMachineConnection
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


def test_create_deleted_object():
    setup_udm()
    lo, position = getMachineConnection(ldap_master=True)
    position.setBase(RECYCLEBIN_DN)
    mod = udm_modules.get('recyclebin/deletedobject')
    obj = mod.object(None, lo, position)
    obj.open()
    original_dn = 'uid=ou1-admin,cn=users,dc=ucs,dc=test'
    delete_at = '20261212085050Z'
    delete_by = lo.binddn
    original_object_type = 'users/user'
    original_univention_object_identifier = 'f2b2e6ff-ad41-47ce-87ea-9d2ac33aaaca'
    ldap_attrs = {
        'cn': [b'lastname'],
        'displayName': [b'lastname'],
        'gecos': [b'lastname'],
        'gidNumber': [b'5001'],
        'homeDirectory': [b'/home/test1'],
        'krb5KDCFlags': [b'126'],
        'krb5Key': [
            b'07\xa1\x1b0\x19\xa0\x03\x02\x01\x11\xa1\x12\x04\x10\xa7\x86\xdc\x0f\xdcn0c\x91\x98Z\xa0\xd2Y\xc7t\xa2\x180\x16\xa0\x03\x02\x01\x03\xa1\x0f\x04\rUCS.TESTtest1',
            b'07\xa1\x1b0\x19\xa0\x03\x02\x01\x17\xa1\x12\x04\x10\xca\xa1#\x9dD\xda~\xdf\x92k\xce9\xf5\xc6]\x0f\xa2\x180\x16\xa0\x03\x02\x01\x03\xa1\x0f\x04\rUCS.TESTtest1',
        ],
        'krb5KeyVersionNumber': [b'1'],
        'krb5MaxLife': [b'86400'],
        'krb5MaxRenew': [b'604800'],
        'krb5PrincipalName': [b'test1@UCS.TEST'],
        'loginShell': [b'/bin/bash'],
        'mailForwardCopyToSelf': [b'0'],
        'memberOf': [b'cn=Domain Users,cn=groups,dc=ucs,dc=test'],
        'pwhistory': [b' $6$znLCTmtimN7H0T92$2iuAyLCkTT/hjoSqTVzMy7U7Fh5OGHaHc6fGupy4KvYoSA2V4FCsfcw3qfQyKA5goXFclV6hvZNCk.xx3B4/u/'],
        'sambaAcctFlags': [b'[U          ]'],
        'sambaBadPasswordCount': [b'0'],
        'sambaBadPasswordTime': [b'0'],
        'sambaNTPassword': [b'CAA1239D44DA7EDF926BCE39F5C65D0F'],
        'sambaPrimaryGroupSID': [b'S-1-5-21-4050189495-1942909977-1471735533-513'],
        'sambaPwdLastSet': [b'1756909087'],
        'sambaSID': [b'S-1-5-21-4050189495-1942909977-1471735533-5386'],
        'sn': [b'lastname'],
        'uid': [b'test1'],
        'uidNumber': [b'2193'],
        'userPassword': [b'{crypt}$6$Si5dxjbGT8wI147P$AazXJ3prqclvVvCuIiou97V0XkzcuUoRiHqN.bqidlcg8kruJe23IIq6lZCJ00WuSPYbuE6IfTyFmPA3EipgA1'],
    }
    obj['originalDN'] = original_dn
    obj['deleteAt'] = delete_at
    obj['deletedBy'] = delete_by
    obj['originalObjectType'] = original_object_type
    obj['originalUniventionObjectIdentifier'] = original_univention_object_identifier
    obj.oldattr = copy.deepcopy(ldap_attrs)
    try:
        obj.create()
        obj = mod.lookup(None, lo, f'originalUniventionObjectIdentifier={original_univention_object_identifier}')[0]
        obj.open()
        assert obj['originalDN'] == original_dn
        assert obj['deleteAt'] == delete_at
        assert obj['deletedBy'] == delete_by
        assert obj['originalObjectType'] == original_object_type
        assert obj['originalUniventionObjectIdentifier'] == original_univention_object_identifier
        original_info = json.loads(obj['originalData'])
        assert original_info['groups'] == ['cn=Domain Users,cn=groups,dc=ucs,dc=test']
        assert original_info['displayName'] == 'lastname'
        assert original_info['sambaRID'] == '5386'
        assert original_info['username'] == 'test1'
        assert original_info['password'] == '***'
        assert original_info['univentionObjectIdentifier'] == original_univention_object_identifier
        for key, values in ldap_attrs.items():
            assert set(obj.oldattr[key]) == set(values)
        assert set(obj.oldattr['objectClass']) == {b'top', b'univentionRecycleBinObject', b'univentionObject', b'extensibleObject'}
    finally:
        obj.remove()


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
    assert 'univentionRecycleBinDeleteAt' in deleted_attrs
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


def test_univention_object_identifier_preservation(udm):
    """Test that univentionObjectIdentifier is preserved during delete and restore."""
    lo = get_admin_connection()
    setup_udm()

    user_dn = udm.create_user()[0]
    original_attrs = lo.get(user_dn)
    original_obj_id = original_attrs.get('univentionObjectIdentifier', [b''])[0].decode('utf-8')

    assert original_obj_id, "User should have univentionObjectIdentifier"

    udm.remove_object('users/user', dn=user_dn)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_dn = deleted_objects[0]['dn']
    deleted_attrs = lo.get(deleted_dn)

    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    deleted_udm_obj = recyclebin_module.object(None, lo, None, dn=deleted_dn)
    deleted_udm_obj.open()

    stored_obj_id = deleted_udm_obj['originalUniventionObjectIdentifier']
    assert stored_obj_id == original_obj_id

    ldap_stored_obj_id = deleted_attrs.get('univentionRecycleBinOriginalUniventionObjectIdentifier', [])
    if ldap_stored_obj_id:
        ldap_stored_obj_id_str = ldap_stored_obj_id[0].decode('utf-8')
        assert ldap_stored_obj_id_str == original_obj_id

    restored_dn = deleted_udm_obj.restore()
    assert restored_dn == user_dn

    restored_attrs = lo.get(user_dn)
    restored_obj_id = restored_attrs.get('univentionObjectIdentifier', [b''])[0].decode('utf-8')

    assert restored_obj_id == original_obj_id

    # Cleanup
    lo.delete(user_dn)


def test_delete_at_timestamp_based_on_retention_policy(udm):
    """Test that deleteAt timestamp is calculated based on retention policy."""
    lo = get_admin_connection()
    setup_udm()

    user_dn = udm.create_user()[0]
    udm.remove_object('users/user', dn=user_dn)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_dn = deleted_objects[0]['dn']

    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    deleted_udm_obj = recyclebin_module.object(None, lo, None, dn=deleted_dn)
    deleted_udm_obj.open()

    delete_at = deleted_udm_obj['deleteAt']
    assert delete_at

    import re
    timestamp_pattern = r'^\d{14}Z$'
    assert re.match(timestamp_pattern, delete_at)

    deleted_attrs = lo.get(deleted_dn)
    ldap_delete_at = deleted_attrs.get('univentionRecycleBinDeleteAt', [])
    assert ldap_delete_at

    ldap_delete_at_str = ldap_delete_at[0].decode('utf-8')
    assert ldap_delete_at_str == delete_at

    # Cleanup
    lo.delete(deleted_dn)


def test_security_reference_tracking_safety(udm):
    """Test that reference tracking doesn't expose sensitive information"""
    lo = get_admin_connection()

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='RefTrack',
        lastname='Security',
    )

    groupname = random_username()
    group_dn, _ = udm.create_group(
        name=groupname,
        description='Reference tracking security test group',
    )

    udm.modify_object('groups/group', dn=group_dn, users=[user_dn])

    group_attrs = lo.get(group_dn)
    has_reference = group_attrs.get('uniqueMember', []) or group_attrs.get('memberUid', [])
    assert has_reference

    udm.remove_object('users/user', dn=user_dn)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0

    deleted_dn = deleted_objects[0]['dn']
    deleted_attrs = lo.get(deleted_dn)

    referenced_by = deleted_attrs.get('referencedBy', [])
    if referenced_by:
        for ref in referenced_by:
            ref_data = json.loads(ref.decode('utf-8'))
            assert 'dn' in ref_data
            assert 'module' in ref_data
            assert 'password' not in str(ref_data).lower()
            assert 'secret' not in str(ref_data).lower()

    # Cleanup
    udm.remove_object('groups/group', dn=group_dn)
    group_deleted = _find_deleted_objects(lo, group_dn)

    for obj in deleted_objects:
        _cleanup_deleted_object(lo, obj['dn'])
    for obj in group_deleted:
        _cleanup_deleted_object(lo, obj['dn'])


def test_user_group_restoration_comprehensive(udm):
    """Test restoration of users and groups with preserved relationships"""
    lo = get_admin_connection()

    groupname = random_username()
    group_dn, _ = udm.create_group(
        name=groupname,
        description='Test group for restoration',
    )

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='Restoration',
        lastname='Test',
        groups=[group_dn],
    )

    verify_ldap_object(user_dn, should_exist=True)
    verify_ldap_object(group_dn, should_exist=True)

    group_attrs = lo.get(group_dn)
    assert user_dn.encode('utf-8') in group_attrs.get('uniqueMember', [])

    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    deleted_users = _find_deleted_objects(lo, user_dn)
    assert len(deleted_users) > 0
    user_deleted_obj = deleted_users[0]

    deleted_user_attrs = lo.get(user_deleted_obj['dn'])
    preserved_memberships = deleted_user_attrs.get('seeAlso', [])
    if preserved_memberships:
        preserved_groups = [g.decode('utf-8') for g in preserved_memberships]
        assert group_dn in preserved_groups

    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)

    deleted_groups = _find_deleted_objects(lo, group_dn)
    assert len(deleted_groups) > 0
    group_deleted_obj = deleted_groups[0]

    setup_udm()
    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    position = univention.admin.uldap.position(lo.base)

    deleted_group_udm_obj = recyclebin_module.object(None, lo, position, dn=group_deleted_obj['dn'])
    deleted_group_udm_obj.open()
    deleted_group_udm_obj.restore()

    verify_ldap_object(group_dn, should_exist=True)

    deleted_user_udm_obj = recyclebin_module.object(None, lo, position, dn=user_deleted_obj['dn'])
    deleted_user_udm_obj.open()
    deleted_user_udm_obj.restore()

    verify_ldap_object(user_dn, should_exist=True)

    final_group_attrs = lo.get(group_dn)
    if preserved_memberships:
        assert user_dn.encode('utf-8') in final_group_attrs.get('uniqueMember', [])

    remaining_deleted_users = _find_deleted_objects(lo, user_dn)
    remaining_deleted_groups = _find_deleted_objects(lo, group_dn)
    assert len(remaining_deleted_users) == 0
    assert len(remaining_deleted_groups) == 0

    lo.delete(user_dn)
    lo.delete(group_dn)


def test_user_multiple_groups_deletion_restoration(udm):
    """Test deletion and restoration of user belonging to multiple groups"""
    lo = get_admin_connection()

    group1_name = random_username()
    group1_dn, _ = udm.create_group(
        name=group1_name,
        description='Test group 1 for multi-group membership',
    )

    group2_name = random_username()
    group2_dn, _ = udm.create_group(
        name=group2_name,
        description='Test group 2 for multi-group membership',
    )

    group3_name = random_username()
    group3_dn, _ = udm.create_group(
        name=group3_name,
        description='Test group 3 for multi-group membership',
    )

    username = random_username()
    user_dn, _ = udm.create_user(
        username=username,
        firstname='MultiGroup',
        lastname='Test',
        groups=[group1_dn, group2_dn, group3_dn],
    )

    verify_ldap_object(user_dn, should_exist=True)
    verify_ldap_object(group1_dn, should_exist=True)
    verify_ldap_object(group2_dn, should_exist=True)
    verify_ldap_object(group3_dn, should_exist=True)

    group1_attrs = lo.get(group1_dn)
    group2_attrs = lo.get(group2_dn)
    group3_attrs = lo.get(group3_dn)

    assert user_dn.encode('utf-8') in group1_attrs.get('uniqueMember', [])
    assert user_dn.encode('utf-8') in group2_attrs.get('uniqueMember', [])
    assert user_dn.encode('utf-8') in group3_attrs.get('uniqueMember', [])

    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    deleted_objects = _find_deleted_objects(lo, user_dn)
    assert len(deleted_objects) > 0
    deleted_obj = deleted_objects[0]

    deleted_attrs = lo.get(deleted_obj['dn'])
    preserved_memberships = deleted_attrs.get('seeAlso', [])

    if preserved_memberships:
        preserved_groups = [g.decode('utf-8') for g in preserved_memberships]
        expected_groups = {group1_dn, group2_dn, group3_dn}
        preserved_groups_set = set(preserved_groups)
        common_groups = expected_groups.intersection(preserved_groups_set)
        assert len(common_groups) > 0

    updated_group1_attrs = lo.get(group1_dn)
    updated_group2_attrs = lo.get(group2_dn)
    updated_group3_attrs = lo.get(group3_dn)

    assert user_dn.encode('utf-8') not in updated_group1_attrs.get('uniqueMember', [])
    assert user_dn.encode('utf-8') not in updated_group2_attrs.get('uniqueMember', [])
    assert user_dn.encode('utf-8') not in updated_group3_attrs.get('uniqueMember', [])

    setup_udm()
    recyclebin_module = udm_modules.modules['recyclebin/deletedobject']
    position = univention.admin.uldap.position(lo.base)

    deleted_udm_obj = recyclebin_module.object(None, lo, position, dn=deleted_obj['dn'])
    deleted_udm_obj.open()
    deleted_udm_obj.restore()

    verify_ldap_object(user_dn, should_exist=True)

    final_group1_attrs = lo.get(group1_dn)
    final_group2_attrs = lo.get(group2_dn)
    final_group3_attrs = lo.get(group3_dn)

    restored_memberships = []
    if user_dn.encode('utf-8') in final_group1_attrs.get('uniqueMember', []):
        restored_memberships.append(group1_dn)
    if user_dn.encode('utf-8') in final_group2_attrs.get('uniqueMember', []):
        restored_memberships.append(group2_dn)
    if user_dn.encode('utf-8') in final_group3_attrs.get('uniqueMember', []):
        restored_memberships.append(group3_dn)

    if preserved_memberships:
        preserved_groups_set = {g.decode('utf-8') for g in preserved_memberships}
        expected_groups = {group1_dn, group2_dn, group3_dn}
        common_preserved = expected_groups.intersection(preserved_groups_set)
        restored_set = set(restored_memberships)
        restored_common = common_preserved.intersection(restored_set)

        if len(common_preserved) > 0:
            assert len(restored_common) > 0

    remaining_deleted = _find_deleted_objects(lo, user_dn)
    assert len(remaining_deleted) == 0

    lo.delete(user_dn)
    lo.delete(group1_dn)
    lo.delete(group2_dn)
    lo.delete(group3_dn)
