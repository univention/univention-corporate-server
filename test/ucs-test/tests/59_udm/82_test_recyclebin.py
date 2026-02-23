#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test LDAP recyclebin functionality
## tags: [ldap, udm, recyclebin]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager-tools

import copy
import datetime
import io
import logging
import subprocess
import time
import uuid
from types import SimpleNamespace

import ldap.dn
import pytest
from ldap.extop.dds import RefreshRequest
from ldap.filter import filter_format
from samba.dcerpc import security
from samba.ndr import ndr_unpack

import univention.admin.modules as udm_modules
from univention.admin.blocklist import hash_blocklist_value
from univention.admin.log import log
from univention.admin.recyclebin import Reference
from univention.admin.uexceptions import authFail, noObject, uidAlreadyUsed, valueError
from univention.admin.uldap import access, getAdminConnection, position
from univention.logging import basicConfig
from univention.testing.fixtures_recyclebin import RECYCLEBIN_DN, _deleted_object_dn
from univention.testing.strings import random_groupname, random_username
from univention.testing.udm import UCSTestUDM_CreateUDMObjectFailed
from univention.testing.utils import (
    get_ldap_connection, package_installed, restart_listener, restart_slapd, start_listener, stop_listener,
    verify_ldap_object, wait_for_drs_replication, wait_for_listener_replication,
)


pytest_plugins = 'univention.testing.fixtures_recyclebin'
udm_modules.update()
basicConfig(level=4, use_structured_logging=True)

SECONDS_PER_DAY = 60 * 60 * 24
TTL_TOLERANCE_SECONDS = 100
LDAP_TIMESTAMP_FORMAT = '%Y%m%d%H%M%S%z'

OT_USERS = 'users/user'
OT_GROUPS = 'groups/group'
OT_RECYCLEBIN = 'recyclebin/removedobject'


@pytest.fixture(autouse=True, scope='session')
def enabled_recyclebin(ucr_session):
    ucr_session.handler_set(['listener/module/recyclebin/deactivate=false'])
    restart_listener()
    yield
    restart_listener()


def _find_deleted_objects(original_dn):
    """Search for deleted objects in the recyclebin by their original DN."""
    lo = get_ldap_connection(primary=True)
    results = lo.search(
        base=RECYCLEBIN_DN,
        scope='one',
        filter=filter_format('(&(objectClass=univentionRecycleBinObject)(univentionRecycleBinOriginalDN=%s))', [original_dn]),
        attr=['univentionRecycleBinOriginalDN', 'univentionRecycleBinOriginalType', 'cn'],
    )
    deleted_objects = []
    for dn, attrs in results:
        original = attrs.get('univentionRecycleBinOriginalDN', [b''])[0].decode('utf-8')
        deleted_objects.append({
            'dn': dn,
            'originalDn': original,
            'univentionObjectType': attrs.get('univentionRecycleBinOriginalType', [b''])[0].decode('utf-8'),
        })
    return deleted_objects


def _cleanup_deleted_object(deleted_dn):
    lo = get_ldap_connection(primary=True)
    """Safely delete a recyclebin object, ignoring errors if it doesn't exist."""
    try:
        lo.delete(deleted_dn)
    except noObject as e:
        print(f'Warning: Could not clean up deleted object {deleted_dn}: {e}')


def _get_object_identifier(udm, object_type, dn):
    """Get the univentionObjectIdentifier for an object."""
    return udm.get_object(object_type, dn)['univentionObjectIdentifier'][0]


def verify_entryttl_deleteat(retention_time, dn):
    """Verify that entryTTL and deleteAt timestamps are correctly set based on retention policy."""
    lo = get_ldap_connection(primary=True)
    attrs = lo.get(dn, attr=['entryTtl', 'univentionRecycleBinDeleteAt', 'univentionRecycleBinDeletionDate'])
    entry_ttl = attrs['entryTtl'][0].decode('UTF-8')
    delete_at = attrs['univentionRecycleBinDeleteAt'][0].decode('UTF-8')
    deleted_at = attrs['univentionRecycleBinDeletionDate'][0].decode('UTF-8')

    deleted_at_date = datetime.datetime.strptime(deleted_at, LDAP_TIMESTAMP_FORMAT)
    delete_at_date = datetime.datetime.strptime(delete_at, LDAP_TIMESTAMP_FORMAT)

    # Verify deleteAt is correctly calculated
    expected_delete_at = deleted_at_date + datetime.timedelta(days=retention_time)
    assert delete_at_date == expected_delete_at, f'deleteAt date {delete_at_date} does not match expected {expected_delete_at}'

    # Verify entryTTL is approximately correct (it's a countdown timer)
    expected_ttl = retention_time * SECONDS_PER_DAY
    ttl_diff = expected_ttl - int(entry_ttl)
    assert ttl_diff < TTL_TOLERANCE_SECONDS, f'TTL difference ({ttl_diff}s) exceeds tolerance. Expected ~{expected_ttl}s, got {entry_ttl}s'


def test_create_container_udm_cli_internal(udm, lo):
    name = random_username()
    udm.create_object('container/cn', position='cn=internal', name=name)
    assert lo.get(f'cn={name},cn=internal')


def test_create_not_allowed(udm, deleted_object_user_properties):
    """Test that manual creation of recyclebin objects is not allowed via UDM CLI."""
    del deleted_object_user_properties.__dict__['ldap_attrs']
    with pytest.raises(UCSTestUDM_CreateUDMObjectFailed):
        udm.create_object(OT_RECYCLEBIN, **deleted_object_user_properties.__dict__)


def test_create_and_restore(deleted_object_user_properties):
    """Test creating a recyclebin object programmatically and restoring it."""
    lo = get_ldap_connection(admin_uldap=True, primary=True)
    recyclebin_module = udm_modules.get(OT_RECYCLEBIN)
    users_module = udm_modules.get(OT_USERS)

    # Create recyclebin object
    deleted_obj = recyclebin_module.object(None, lo, position(RECYCLEBIN_DN))
    deleted_obj.open()
    deleted_obj['originalDN'] = deleted_object_user_properties.originalDN
    deleted_obj['purgeAt'] = deleted_object_user_properties.purgeAt
    deleted_obj['removalDate'] = deleted_object_user_properties.removalDate
    deleted_obj['originalObjectType'] = deleted_object_user_properties.originalObjectType
    deleted_obj['originalUniventionObjectIdentifier'] = deleted_object_user_properties.originalUniventionObjectIdentifier
    deleted_obj['originalEntryUUID'] = deleted_object_user_properties.originalEntryUUID
    deleted_obj['originalObjectClasses'] = deleted_object_user_properties.originalObjectClasses
    deleted_obj.oldattr = copy.deepcopy(deleted_object_user_properties.ldap_attrs)
    deleted_obj.oldattr.update(deleted_object_user_properties.ignore_ldap_attrs)

    restored_user = None
    try:
        # Create deleted object
        deleted_obj.create(ignore_license=True)

        # Verify deleted object exists and has correct properties
        original_name = deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert recyclebin_module.lookup(None, lo, f'originalName=*{original_name}*'), f'Could not find deleted object with originalName matching {original_name}'

        deleted_obj = recyclebin_module.lookup(
            None, lo,
            f'univentionRecycleBinOriginalUniventionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}',
        )[0]
        deleted_obj.open()

        # Verify all metadata fields
        assert deleted_obj['originalDN'] == deleted_object_user_properties.originalDN
        assert deleted_obj['purgeAt'] == deleted_object_user_properties.purgeAt
        assert deleted_obj['removalDate'] == deleted_object_user_properties.removalDate
        assert deleted_obj['originalObjectType'] == deleted_object_user_properties.originalObjectType
        assert deleted_obj['originalUniventionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier
        assert deleted_obj['originalEntryUUID'] == deleted_object_user_properties.originalEntryUUID
        assert set(deleted_obj['originalObjectClasses']) == set(deleted_object_user_properties.originalObjectClasses)

        # Verify preserved user attributes
        assert deleted_obj['displayName'] == deleted_object_user_properties.ldap_attrs['displayName'][0].decode('UTF-8')
        assert deleted_obj['username'] == deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert deleted_obj['password'] == deleted_object_user_properties.ldap_attrs['userPassword'][0].decode('UTF-8')
        assert deleted_obj['univentionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier

        # Verify group memberships (excluding non-existent groups)
        expected_groups = {
            x.decode('UTF-8') for x in deleted_object_user_properties.ldap_attrs['memberOf']
            if not x.decode('UTF-8').startswith('cn=doesnotexist')
        }
        assert set(deleted_obj['groups']) == expected_groups

        # Verify LDAP object classes
        expected_object_classes = {b'top', b'univentionRecycleBinObject', b'univentionObject', b'extensibleObject', b'dynamicObject'}
        assert set(deleted_obj.oldattr['objectClass']) == expected_object_classes

        # Verify all LDAP attributes are preserved
        for key, values in deleted_object_user_properties.ldap_attrs.items():
            if key == 'memberOf':
                expected_member_of = {x for x in values if not x.decode('UTF-8').startswith('cn=doesnotexist')}
                assert set(deleted_obj.oldattr[key]) == expected_member_of
            else:
                assert set(deleted_obj.oldattr[key]) == set(values), f'Mismatch in attribute: {key}'

        # Restore the object
        restored_dn = deleted_obj.restore()
        assert restored_dn == deleted_object_user_properties.originalDN, f'Restored DN {restored_dn} does not match original {deleted_object_user_properties.originalDN}'

        # Verify deleted object has been removed from recyclebin
        remaining_objects = recyclebin_module.lookup(
            None, lo,
            f'originalUniventionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}',
        )
        assert remaining_objects == [], 'Deleted object should be removed from recyclebin after restoration'

        # Verify restored user object
        restored_user = users_module.lookup(
            None, lo, None,
            base=deleted_object_user_properties.originalDN,
            unique=True, required=True,
        )[0]
        restored_user.open()

        # Verify user attributes after restoration
        assert restored_user['username'] == deleted_object_user_properties.ldap_attrs['uid'][0].decode('UTF-8')
        assert restored_user['displayName'] == deleted_object_user_properties.ldap_attrs['displayName'][0].decode('UTF-8')
        assert set(restored_user['groups']) == expected_groups
        assert restored_user['univentionObjectIdentifier'] == deleted_object_user_properties.originalUniventionObjectIdentifier
        assert restored_user.dn == deleted_object_user_properties.originalDN

        # Verify all LDAP attributes after restoration
        for key, values in deleted_object_user_properties.ldap_attrs.items():
            if key == 'memberOf':
                expected_member_of = {x for x in values if not x.decode('UTF-8').startswith('cn=doesnotexist')}
                assert set(restored_user.oldattr[key]) == expected_member_of
            else:
                assert set(restored_user.oldattr[key]) == set(values), f'Mismatch in restored attribute: {key}'

        restored_object_classes = {x.decode('UTF-8') for x in restored_user.oldattr['objectClass']}
        assert restored_object_classes == set(deleted_object_user_properties.originalObjectClasses)

        restored_user.remove()
    finally:
        # Clean up
        try:
            deleted_obj.remove()
        except noObject:
            pass

        remaining_users = users_module.lookup(
            None, lo,
            f'univentionObjectIdentifier={deleted_object_user_properties.originalUniventionObjectIdentifier}',
        )
        if remaining_users:
            remaining_users[0].open()
            remaining_users[0].remove()


@pytest.mark.parametrize(
    'name_suffix',
    [
        '',
        # pytest.param('ä+ü', marks=[
        #     pytest.mark.xfail(match='uniqueMember: value #0 already exists.'),  # broken DN chars (and utf-8 umlauts)
        #     pytest.mark.skipif(package_installed('univention-s4-connector'), reason="s4 connector setup, creating a user with '+' fails with: samldb: sAMAccountName contains invalid '+' character"),
        # ]),
        '§(id)',  # broken filter chars
        # pytest.param(random_username_special_characters(), marks=pytest.mark.xfail(match='uniqueMember: value #0 already exists.')),
    ],
)
def test_user_restore_umc(udm, ucr, name_suffix, recyclebin_policy_session, lo, Client):
    """Test user deletion and restoration via UMC interface."""
    container_recyclebin_policy, _ = recyclebin_policy_session

    ucr.handler_set([
        'directory/manager/web/modules/users/user/properties/username/syntax=string',
        'directory/manager/web/modules/groups/group/properties/name/syntax=string',
    ])

    user_dn, username = udm.create_user(username=random_username() + name_suffix, position=container_recyclebin_policy, wait_for_replication=False)
    group_dn, _ = udm.create_group(name=random_groupname() + name_suffix, position=container_recyclebin_policy)
    user_object_id = _get_object_identifier(udm, OT_USERS, user_dn)

    udm.remove_object(OT_USERS, dn=user_dn)
    udm.remove_object(OT_GROUPS, dn=group_dn)

    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_object_id)
    verify_ldap_object(deleted_dn, should_exist=True)
    # Test UMC search functionality
    con = Client.get_test_connection(language='en-US')
    search_options = {
        'hidden': False,
        'objectType': OT_RECYCLEBIN,
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'path'],
    }

    # Search for deleted object
    result = con.umc_command('udm/query', search_options, OT_RECYCLEBIN).result
    found_dns = [entry['$dn$'] for entry in result if entry['name'] == username]
    assert found_dns and len(found_dns) == 1, f'Expected to find exactly one deleted object for user {username}'

    # Test detail page access (verify search still works after viewing details)
    detail_result = con.umc_command('udm/get', [deleted_dn], OT_RECYCLEBIN).result[0]
    assert detail_result['username'] == username, 'Username should match in detail view'
    assert detail_result['groups'], 'Groups should be present in detail view'
    assert ldap.dn.str2dn(detail_result['originalDN']) == ldap.dn.str2dn(user_dn), 'Original DN should be preserved'

    # Test properties endpoint
    properties_options = [{'objectType': OT_RECYCLEBIN, 'objectDN': deleted_dn}]
    properties_result = con.umc_command('udm/properties', properties_options, OT_RECYCLEBIN).result[0]
    property_ids = [prop['id'] for prop in properties_result]
    assert 'username' in property_ids, 'username property should be available'

    # Test layout endpoint
    layout_result = con.umc_command('udm/layout', properties_options, OT_RECYCLEBIN).result[0]
    labels = [section['label'] for section in layout_result]
    assert 'Account' in labels, 'Account section should be in layout'

    # Verify search still works after viewing detail page
    result_after_details = con.umc_command('udm/query', search_options, OT_RECYCLEBIN).result
    assert result_after_details, 'Search should return results after viewing details'
    found_dns_again = [entry['$dn$'] for entry in result_after_details if entry['name'] == username]
    assert found_dns_again and len(found_dns_again) == 1, 'Should still find exactly one deleted object'

    # Restore the object via UMC
    restore_options = [{'object': deleted_dn}]
    restore_result = con.umc_command('udm/restore', restore_options, OT_RECYCLEBIN).result
    assert restore_result[0]['success'], restore_result[0]
    wait_for_listener_replication()
    assert lo.get(user_dn), f'User should be restored at original DN {user_dn}'


def test_user_search_filter_umc(udm, recyclebin_policy_session, lo, Client):
    """Test UMC search filters for recyclebin objects."""
    def _check_search(con, username, search_options):
        """Helper to verify search returns exactly one result for the given username."""
        result = con.umc_command('udm/query', search_options, OT_RECYCLEBIN).result
        found_dns = [entry['$dn$'] for entry in result if entry['name'] == username]
        assert found_dns and len(found_dns) == 1, f'Expected to find exactly one result for {username}, found {len(found_dns)}'

    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create and delete a test user
    user_dn, username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    user_object_id = _get_object_identifier(udm, OT_USERS, user_dn)
    udm.remove_object(OT_USERS, dn=user_dn)

    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_object_id)
    verify_ldap_object(deleted_dn, should_exist=True)

    # Test search with different filter properties
    con = Client.get_test_connection()
    base_options = {
        'hidden': False,
        'objectType': OT_RECYCLEBIN,
        'objectProperty': 'None',
        'objectPropertyValue': '',
        'fields': ['name', 'path'],
    }

    # Test various search properties
    search_filters = [
        ('originalName', username),
        ('originalObjectType', OT_USERS),
    ]

    for property_name, property_value in search_filters:
        search_options = base_options.copy()
        search_options['objectProperty'] = property_name
        search_options['objectPropertyValue'] = property_value
        _check_search(con, username, search_options)


@pytest.mark.parametrize('listener_running', [True, False], ids=['listener running', 'listener stopped'])
def test_user_restore(udm, recyclebin_policy_session, ldap_base, lo, listener_running):
    """
    Test user deletion and restoration with group memberships.

    Tests both scenarios:
    - Listener running during deletion
    - Listener stopped (with one group also deleted)
    """
    container_recyclebin_policy, retention_time = recyclebin_policy_session

    # Create test groups and user
    group1_dn, _ = udm.create_group(wait_for_replication=False)
    group2_dn, _ = udm.create_group(wait_for_replication=False)
    group3_dn, _ = udm.create_group(wait_for_replication=False)

    password = '&%$§§"%saidaa'
    user_dn, username = udm.create_user(
        groups=[group1_dn, group2_dn, group3_dn],
        password=password,
        position=container_recyclebin_policy,
    )

    if package_installed('univention-samba4'):  # to avoid flakyness on non-primary nodes, wait for object to receive the final sambaSID
        verify_ldap_object(user_dn, should_exist=True)  # first wait for initial object replication, to give the S4-Connector on the primary enough time
        wait_for_listener_replication()
        res = wait_for_drs_replication(
            ldap_filter=f'(&(sAMAccountName={username})(&(objectClass=user)(!(objectClass=computer))(userAccountControl:1.2.840.113556.1.4.803:=512)))',  # filter copied from UCSTestUDM.ad_object_identifying_filter
            attrs=['objectSid'],
        )
        sid = str(ndr_unpack(security.dom_sid, res[0]["objectSid"][0]))
        verify_ldap_object(user_dn, expected_attr={'sambaSID': [sid]}, should_exist=True)

    original_props = udm.get_object(OT_USERS, user_dn)
    user_object_id = original_props['univentionObjectIdentifier'][0]

    # Stop listener if testing that scenario
    if not listener_running:
        stop_listener()

    try:
        udm.remove_object(OT_USERS, dn=user_dn, wait_for_replication=False)

        # In listener-stopped scenario, also delete one group
        if not listener_running:
            udm.remove_object(OT_GROUPS, dn=group2_dn, wait_for_replication=False)
            original_props['groups'].remove(group2_dn)
    finally:
        if not listener_running:
            start_listener()

    wait_for_listener_replication()

    deleted_dn = _deleted_object_dn(user_object_id)
    verify_ldap_object(deleted_dn, should_exist=True)
    del_obj = lo.search(filter_format('uid=%s', [username]), base=RECYCLEBIN_DN)

    # Verify authentication fails for deleted user
    with pytest.raises(authFail):
        access(binddn=user_dn, bindpw=password, base=ldap_base)

    # Test various search filters (including wildcards)
    search_tests = [
        (f'originalUniventionObjectIdentifier={user_object_id}', 'by originalUniventionObjectIdentifier'),
        (f'univentionRecycleBinOriginalUniventionObjectIdentifier={user_object_id}', 'by long attr name'),
        (f'originalName={username}', 'by exact originalName'),
        (f'originalName={username[:-1]}*', 'by originalName prefix wildcard'),
        (f'originalName=*{username[1:]}', 'by originalName suffix wildcard'),
        (f'originalUniventionObjectIdentifier={user_object_id[:-1]}*', 'by OID prefix wildcard'),
    ]

    for filter_expr, description in search_tests:
        results = udm.list_objects(OT_RECYCLEBIN, filter=filter_expr)
        assert results, f'Search {description} should return results'

    # Verify TTL and purgeAt timestamps
    deleted_obj_dn, _ = udm.list_objects(OT_RECYCLEBIN, filter=filter_format('originalDN=%s', [user_dn]))[0]
    verify_entryttl_deleteat(retention_time, deleted_obj_dn)

    # Restore user
    restored_dn = udm.restore_object(OT_RECYCLEBIN, dn=deleted_obj_dn)
    wait_for_listener_replication()
    restored_props = udm.get_object(OT_USERS, restored_dn)

    # Verify restoration
    assert restored_dn == user_dn, f'Restored DN should match original: {restored_dn} != {user_dn}'

    # Verify authentication works after restoration
    access(binddn=restored_dn, bindpw=password, base=ldap_base)

    # Verify all properties are restored correctly
    for key in original_props.keys():
        assert set(original_props[key]) == set(restored_props[key]), f'Property {key} mismatch: original={original_props[key]}, restored={restored_props[key]}, del_obj={del_obj}'


def test_group_restore(udm, recyclebin_policy_session, ldap_base):
    """Test group deletion and restoration with nested groups and members."""
    container_recyclebin_policy, retention_time = recyclebin_policy_session

    # Create group hierarchy: parent group -> test group -> child group
    parent_group_dn, _ = udm.create_group(wait_for_replication=False)
    group_dn, _ = udm.create_group(
        wait_for_replication=False,
        position=container_recyclebin_policy,
        memberOf=[parent_group_dn],
    )
    udm.create_group(wait_for_replication=False, memberOf=[group_dn])

    # Add various members to the test group
    udm.create_user(wait_for_replication=False, groups=[group_dn])
    udm.create_user(wait_for_replication=False, groups=[group_dn])
    udm.create_object('computers/linux', name=random_username(), groups=[group_dn])

    # Store original properties for comparison
    original_props = udm.get_object(OT_GROUPS, group_dn)

    # Delete the group
    udm.remove_object(OT_GROUPS, dn=group_dn)

    # Verify TTL and purgeAt timestamps
    deleted_obj_dn, _ = udm.list_objects(OT_RECYCLEBIN, filter=f'originalDN={group_dn}')[0]
    verify_entryttl_deleteat(retention_time, deleted_obj_dn)

    # Restore the group
    restored_dn = udm.restore_object(OT_RECYCLEBIN, dn=deleted_obj_dn)
    restored_props = udm.get_object(OT_GROUPS, restored_dn)

    # Verify restoration
    assert restored_dn == group_dn, f'Restored DN should match original: {restored_dn} != {group_dn}'

    # Verify all properties are restored correctly
    for key in original_props.keys():
        assert set(original_props[key]) == set(restored_props[key]), f'Property {key} mismatch: original={original_props[key]}, restored={restored_props[key]}'


def test_recyclebin_container_exists(lo):
    """Test that the recyclebin container exists in cn=internal"""
    attrs = lo.get(RECYCLEBIN_DN)
    assert attrs is not None
    assert b'organizationalRole' in attrs['objectClass']
    assert attrs['cn'][0].decode('utf-8') == 'recyclebin'


def test_user_delete_moves_to_recycle_bin(udm, lo, recyclebin_policy_session):
    """Test that deleted user objects are moved to recyclebin."""
    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create user
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    verify_ldap_object(user_dn, should_exist=True)

    # Delete user
    udm.remove_object(OT_USERS, dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    # Verify user is in recyclebin
    deleted_objects = _find_deleted_objects(user_dn)
    assert len(deleted_objects) > 0, f'User {user_dn} should be found in recyclebin after deletion'

    for obj in deleted_objects:
        _cleanup_deleted_object(obj['dn'])


def test_ignore_user_delete_moves_to_recycle_bin(udm, lo, recyclebin_policy_session):
    """Test that users with PKI option are NOT moved to recyclebin (ignored)."""
    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create user with PKI option (which should be ignored by recyclebin)
    user_dn, _ = udm.create_user(
        position=container_recyclebin_policy,
        append_option=['pki'],
        wait_for_replication=False,
    )
    verify_ldap_object(user_dn, should_exist=True)

    # Delete user
    udm.remove_object(OT_USERS, dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    # Verify user is NOT in recyclebin (PKI users are excluded)
    deleted_objects = _find_deleted_objects(user_dn)
    assert not deleted_objects, f'User with PKI option should not be in recyclebin, but found {len(deleted_objects)} objects'


def test_group_delete_moves_to_recycle_bin(udm, lo, recyclebin_policy_session):
    """Test that deleted group objects are moved to recyclebin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    group_dn, _ = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(group_dn, should_exist=True)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(goid)
    verify_ldap_object(deleted_dn, should_exist=True)
    deleted_objects = _find_deleted_objects(group_dn)
    assert len(deleted_objects) > 0, 'Group should be found in Recycle Bin'
    for obj in deleted_objects:
        _cleanup_deleted_object(obj['dn'])


def test_multiple_object_types_deletion(udm, lo, recyclebin_policy_session):
    """Test that different types of LDAP objects can be moved to recyclebin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    group_dn, _ = udm.create_group(wait_for_replication=True, position=container_recyclebin_policy)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    test_objects = []
    test_objects.append(('users/user', user_dn, uoid))
    test_objects.append(('groups/group', group_dn, goid))
    deleted_dns = []
    for obj_type, obj_dn, oid in test_objects:
        udm.remove_object(obj_type, dn=obj_dn)
        deleted_dn = _deleted_object_dn(oid)
        verify_ldap_object(deleted_dn, should_exist=True)
        verify_ldap_object(obj_dn, should_exist=False)
        deleted_objects = _find_deleted_objects(obj_dn)
        assert len(deleted_objects) > 0
        deleted_dns.extend([obj['dn'] for obj in deleted_objects])
    for deleted_dn in deleted_dns:
        _cleanup_deleted_object(deleted_dn)


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
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
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
    _cleanup_deleted_object(deleted_dn)


def test_restore_deleted_object(udm, lo, recyclebin_policy_session):
    """Test that deleted objects can be restored from the recyclebin"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    original_attrs = lo.get(user_dn)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert user_dn == restored_dn
    verify_ldap_object(user_dn, should_exist=True)
    source_attrs = lo.get(user_dn)
    assert source_attrs['uid'][0].decode('utf-8') == original_attrs['uid'][0].decode('utf-8')
    assert source_attrs['givenName'][0].decode('utf-8') == original_attrs['givenName'][0].decode('utf-8')
    assert source_attrs['sn'][0].decode('utf-8') == original_attrs['sn'][0].decode('utf-8')


def test_restore_with_name_conflict(udm, lo, recyclebin_policy_session):
    """Test restore behavior when there's a naming conflict at the original location."""
    container_recyclebin_policy, _ = recyclebin_policy_session

    # Create and delete a user
    username = random_username()
    user_dn, _ = udm.create_user(
        position=container_recyclebin_policy,
        username=username,
        wait_for_replication=False,
    )
    user_object_id = _get_object_identifier(udm, OT_USERS, user_dn)

    udm.remove_object(OT_USERS, dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)

    # Create a new user with the same username (creates conflict)
    conflicting_user_dn, _ = udm.create_user(
        position=container_recyclebin_policy,
        username=username,
        wait_for_replication=False,
    )

    # Attempt to restore original user (should fail due to username conflict)
    deleted_dn = _deleted_object_dn(user_object_id)
    verify_ldap_object(deleted_dn, should_exist=True)
    recyclebin_module = udm_modules.modules[OT_RECYCLEBIN]
    deleted_udm_obj = recyclebin_module.object(None, lo, position(RECYCLEBIN_DN), dn=deleted_dn)
    deleted_udm_obj.open()

    with pytest.raises(uidAlreadyUsed):
        deleted_udm_obj.restore()

    # Verify both objects still exist (restore failed, conflict remains)
    verify_ldap_object(deleted_dn, should_exist=True)
    verify_ldap_object(conflicting_user_dn, should_exist=True)

    _cleanup_deleted_object(deleted_dn)


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
    deleted_obj_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_obj_dn, should_exist=True)
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


def test_delete_at_timestamp_based_on_retention_policy(udm, lo, recyclebin_policy_session):
    """Test that purgeAt timestamp is calculated based on retention policy."""
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    verify_entryttl_deleteat(retention_time, deleted_dn)
    _cleanup_deleted_object(deleted_dn)


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
    user_deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(user_deleted_dn, should_exist=True)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)
    group_deleted_dn = _deleted_object_dn(goid)
    verify_ldap_object(group_deleted_dn, should_exist=True)

    # restore
    udm.restore_object('recyclebin/removedobject', dn=group_deleted_dn)
    verify_ldap_object(group_dn, should_exist=True)
    udm.restore_object('recyclebin/removedobject', dn=user_deleted_dn)
    verify_ldap_object(user_dn, should_exist=True)

    # check
    group_attrs = lo.get(group_dn)
    assert user_dn.encode('utf-8') in group_attrs.get('uniqueMember', [])


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
    user_deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(user_deleted_dn, should_exist=True)
    time.sleep(3)  # TODO: give the listener some time to update the group references, find another way to avoid sleep
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
    user_deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(user_deleted_dn, should_exist=True, retry_count=3, delay=3)
    deleted_attrs = lo.get(user_deleted_dn)
    assert policy_dn.encode('utf-8') in deleted_attrs.get('univentionPolicyReference', [])

    # restore
    udm.restore_object('recyclebin/removedobject', dn=user_deleted_dn)
    verify_ldap_object(user_dn, should_exist=True)
    restored_user_attrs = lo.get(user_dn)
    assert policy_dn.encode('utf-8') in restored_user_attrs.get('univentionPolicyReference', [])


def test_policy_disabled_check(udm, ldap_base):
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
    user_dn, _ = udm.create_user(position=container_dn, wait_for_replication=True)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(user_dn, should_exist=True)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=False)


def test_listener_cache_behavior(udm, recyclebin_policy_session):
    """Test listener cache tracks deleted objects correctly"""
    lo = get_ldap_connection(admin_uldap=True, primary=True)
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
    deleted_dn1 = _deleted_object_dn(uoid1)
    deleted_dn2 = _deleted_object_dn(uoid2)
    verify_ldap_object(deleted_dn1, should_exist=True)
    verify_ldap_object(deleted_dn2, should_exist=True)
    assert user_dn1.encode('UTF-8') in lo.get(deleted_dn1).get('univentionRecycleBinOriginalDN', []), f'missing removed object {deleted_dn1}'
    assert user_dn2.encode('UTF-8') in lo.get(deleted_dn2).get('univentionRecycleBinOriginalDN', []), f'missing removed object {deleted_dn2}'
    _cleanup_deleted_object(deleted_dn1)
    _cleanup_deleted_object(deleted_dn2)


def test_recyclebin_type_limitation(udm, recyclebin_policy_session):
    """Test that recyclebin only processes users and groups, not computers"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    computer_dn = udm.create_object('computers/linux', position=container_recyclebin_policy, name=random_username())
    uoid = udm.get_object('computers/linux', computer_dn)['univentionObjectIdentifier'][0]
    verify_ldap_object(computer_dn, should_exist=True)
    udm.remove_object('computers/linux', dn=computer_dn)
    verify_ldap_object(computer_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=False)


def test_original_name_extraction_and_storage(udm, lo, recyclebin_policy_session):
    """Test that originalName is properly extracted and stored for different object types"""
    container_recyclebin_policy, _ = recyclebin_policy_session
    user_dn, username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    group_dn, groupname = udm.create_group(wait_for_replication=False, position=container_recyclebin_policy)
    goid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn, wait_for_replication=False)
    udm.remove_object('groups/group', dn=group_dn, wait_for_replication=True, remove_referring=False)

    # check originalName
    verify_ldap_object(user_dn, should_exist=False)
    verify_ldap_object(group_dn, should_exist=False)
    deleted_user_dn = _deleted_object_dn(uoid)
    deleted_group_dn = _deleted_object_dn(goid)
    verify_ldap_object(deleted_user_dn, should_exist=True)
    verify_ldap_object(deleted_group_dn, should_exist=True)
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

    _cleanup_deleted_object(deleted_user_dn)
    _cleanup_deleted_object(deleted_group_dn)


@pytest.mark.roles('domaincontroller_master')
def test_dds_automatic_purging_enabled(udm, lo, recyclebin_policy_session, ucr):
    """Test that DDS automatic purging is enabled for recyclebin objects"""
    container_recyclebin_policy, retention_time = recyclebin_policy_session
    user_dn, _ = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    deleted_attrs = lo.get(deleted_dn)
    object_classes = [cls.decode('utf-8') for cls in deleted_attrs.get('objectClass', [])]
    assert 'dynamicObject' in object_classes
    verify_entryttl_deleteat(retention_time, deleted_dn)

    # manually update ttls and check if slapd purges the entry
    # we need ldap/database/internal/overlay/dds/min-ttl='1' for that to work
    ucr.handler_set(['ldap/database/internal/overlay/dds/min-ttl=1'])
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
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    time.sleep(3)  # TODO: give the listener some time to update the group references, find another way to avoid sleep
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
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    time.sleep(3)  # TODO: give the listener some time to update the group references, find another way to avoid sleep
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


def test_structured_logging_for_recyclebin_operations(udm, recyclebin_policy_session):
    """Test that structured logging is working for recyclebin operations"""
    lo = get_ldap_connection(admin_uldap=True, primary=True)
    container_recyclebin_policy, _ = recyclebin_policy_session
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(logging.INFO)
    log.addHandler(handler)
    try:
        user_dn, _ = udm.create_user(position=container_recyclebin_policy)
        uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
        udm.remove_object('users/user', dn=user_dn)
        deleted_dn = _deleted_object_dn(uoid)
        verify_ldap_object(deleted_dn, should_exist=True)
        recyclebin_module = udm_modules.modules['recyclebin/removedobject']
        deleted_user_obj = recyclebin_module.object(None, lo, position(RECYCLEBIN_DN), dn=deleted_dn)
        deleted_user_obj.open()
        deleted_user_obj.restore()
        log_output = log_capture.getvalue()
        assert 'Object restored from recyclebin' in log_output
        # FIXME: we don't have the additional info in log_output?
        # assert 'event_type=delete' in log_output or 'event_type":"delete"' in log_output
        # assert 'status=success' in log_output or 'status":"success"' in log_output
        # assert 'event_type=restore' in log_output or 'event_type":"restore"' in log_output
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
    deleted_dn = _deleted_object_dn(uoid)
    restored_dn = udm.restore_object('recyclebin/removedobject', dn=deleted_dn)
    assert restored_dn == user_dn
    assert lo.get(user_dn)


def test_blocklist_different_id_blocked(udm, recyclebin_policy_session, blocklist_username):
    lo = get_ldap_connection(admin_uldap=True, primary=True)
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
    deleted_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
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
    deleted_group_dn = _deleted_object_dn(goid)
    verify_ldap_object(deleted_group_dn, should_exist=True)

    # Delete user second (should find group UUID in recyclebin)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_user_dn = _deleted_object_dn(uoid)

    # Verify that user's references include our test group with UUID from recyclebin
    verify_ldap_object(deleted_user_dn, should_exist=True)
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

    _cleanup_deleted_object(deleted_user_dn)
    _cleanup_deleted_object(deleted_group_dn)


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
    deleted_user_dn = _deleted_object_dn(uoid)
    verify_ldap_object(deleted_user_dn, should_exist=True)
    time.sleep(3)  # TODO: give the listener some time to update the group references, find another way to avoid sleep

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

    _cleanup_deleted_object(deleted_user_dn)


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

    udm.remove_object('groups/group', dn=group_dn, wait_for_replication=True, remove_referring=False)
    verify_ldap_object(group_dn, should_exist=False)

    deleted_user_dn = _deleted_object_dn(uoid)
    deleted_group_dn = _deleted_object_dn(goid)
    verify_ldap_object(deleted_user_dn, should_exist=True)
    verify_ldap_object(deleted_group_dn, should_exist=True)

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

    _cleanup_deleted_object(deleted_user_dn)
    _cleanup_deleted_object(deleted_group_dn)
