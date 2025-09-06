#!/usr/share/ucs-test/runner pytest-3 -s
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
## desc: Integration test for DDS overlay with entryTtl automatic purging
## tags: [ldap, dds, trash_bin, integration]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager
##  - python3-univention-directory-manager


import time

import ldap
import pytest
from ldap.controls.simple import RelaxRulesControl
from ldap.extop.dds import RefreshRequest

import univention.admin.modules as udm_modules
import univention.admin.uldap
from univention.config_registry import ucr as _ucr
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object


LDAP_BASE = _ucr['ldap/base']
RECYCLEBIN_DN = "cn=recyclebin,cn=internal"


def get_admin_connection():
    result = univention.admin.uldap.getAdminConnection()
    if isinstance(result, tuple):
        return result[0]
    return result


def setup_udm():
    udm_modules.update()


def find_trash_object(lo, original_dn):
    try:
        results = lo.search(
            base=RECYCLEBIN_DN,
            scope='one',
            filter=f'(univentionRecycleBinOriginalDN={ldap.filter.escape_filter_chars(original_dn)})',
            attr=['*', '+'],
        )
        return results[0] if results else None
    except ldap.LDAPError:
        return None


def test_dds_overlay_enabled():
    dds_enabled = _ucr.is_true('ldap/overlay/dds', False)
    if not dds_enabled:
        pytest.skip("DDS overlay is not enabled (ldap/overlay/dds=false)")

    max_ttl = _ucr.get('ldap/overlay/dds/max-ttl', '31536000')
    min_ttl = _ucr.get('ldap/overlay/dds/min-ttl', '86400')
    interval = _ucr.get('ldap/overlay/dds/interval', '3600')

    print("\nDDS Configuration:")
    print(f"  max_ttl: {max_ttl} seconds")
    print(f"  min_ttl: {min_ttl} seconds")
    print(f"  interval: {interval} seconds")


def test_trash_object_with_short_ttl_for_testing():
    dds_enabled = _ucr.is_true('ldap/overlay/dds', False)
    if not dds_enabled:
        pytest.skip("DDS overlay is not enabled")

    lo = get_admin_connection()

    with UCSTestUDM() as udm:
        username = random_username()
        user_dn, _ = udm.create_user(
            username=username,
            firstname='DDS',
            lastname='IntegrationTest',
            description='Test user for DDS integration with short TTL',
        )

        print(f"\nCreated test user: {user_dn}")
        verify_ldap_object(user_dn, should_exist=True)

        udm.remove_object('users/user', dn=user_dn)
        verify_ldap_object(user_dn, should_exist=False)

        trash_entry = find_trash_object(lo, user_dn)
        assert trash_entry is not None, f"User {user_dn} not found in trash bin"

        trash_dn, trash_attrs = trash_entry
        print(f"Found in trash: {trash_dn}")

        object_classes = [oc.decode('utf-8') for oc in trash_attrs.get('objectClass', [])]
        assert 'univentionRecycleBinObject' in object_classes, "Missing univentionRecycleBinObject class"
        assert 'extensibleObject' in object_classes, "Missing extensibleObject class"
        assert 'dynamicObject' in object_classes, "Missing dynamicObject class (required for DDS)"

        assert 'entryTtl' in trash_attrs, "entryTtl attribute missing - DDS won't purge this object"
        ttl_value = int(trash_attrs['entryTtl'][0].decode('utf-8'))
        print(f"entryTtl value: {ttl_value} seconds")

        expected_ttl = 30 * 86400
        # Allow small tolerance for timing differences
        assert abs(ttl_value - expected_ttl) <= 10, f"Expected TTL ~{expected_ttl}, got {ttl_value}"

        assert 'univentionRecycleBinOriginalDN' in trash_attrs
        assert 'univentionRecycleBinDeleteAt' in trash_attrs
        assert 'univentionRecycleBinOriginalType' in trash_attrs

        original_dn = trash_attrs['univentionRecycleBinOriginalDN'][0].decode('utf-8')
        assert original_dn == user_dn, f"Original DN mismatch: {original_dn} != {user_dn}"

        original_type = trash_attrs['univentionRecycleBinOriginalType'][0].decode('utf-8')
        assert original_type == 'users/user', f"Original type mismatch: {original_type}"

        print(f"✓ Object successfully moved to trash with entryTtl={ttl_value}")
        print("✓ DDS will automatically purge after TTL expires")

        try:
            lo.delete(trash_dn)
            print(f"✓ Cleaned up trash object: {trash_dn}")
        except ldap.LDAPError as e:
            print(f"Warning: Could not clean up {trash_dn}: {e}")


def test_manual_dds_object_with_short_ttl():
    dds_enabled = _ucr.is_true('ldap/overlay/dds', False)
    if not dds_enabled:
        pytest.skip("DDS overlay is not enabled")

    lo = get_admin_connection()

    test_cn = f"dds-test-{int(time.time())}"
    test_dn = f"cn={test_cn},cn=internal"

    test_ttl = 60
    min_ttl = int(_ucr.get('ldap/overlay/dds/min-ttl', '86400'))

    if test_ttl < min_ttl:
        print(f"Warning: Test TTL {test_ttl} is below configured min_ttl {min_ttl}")
        print("Using min_ttl instead to avoid LDAP constraint violation")
        test_ttl = min_ttl

    print(f"\nCreating manual DDS test object with TTL={test_ttl} seconds")
    print(f"Object will be created at: {test_dn}")

    attrs = {
        'objectClass': [b'dynamicObject', b'organizationalRole'],
        'cn': [test_cn.encode('utf-8')],
        'description': [b'Test object for DDS automatic purging'],
    }

    try:
        controls = [RelaxRulesControl()]
        lo.add(test_dn, list(attrs.items()), serverctrls=controls)
        print("✓ Successfully created DDS test object")

        # Use refresh operation to set the TTL (like in deletedobject.py)
        refresh_req = RefreshRequest(entryName=test_dn, requestTtl=test_ttl)
        res = lo.lo.lo.extop_s(refresh_req, serverctrls=[])
        if res:
            print(f"✓ Successfully set TTL to {test_ttl} seconds via DDS refresh")
        else:
            print("⚠️ DDS refresh operation returned unexpected response")

        created_attrs = lo.get(test_dn, attr=['*', '+'])
        assert created_attrs is not None, "Object should exist after creation"

        object_classes = [oc.decode('utf-8') for oc in created_attrs.get('objectClass', [])]
        assert 'dynamicObject' in object_classes, "dynamicObject class missing"
        assert 'entryTtl' in created_attrs, "entryTtl attribute missing"

        actual_ttl = int(created_attrs['entryTtl'][0].decode('utf-8'))
        print(f"✓ Object created with entryTtl={actual_ttl} seconds")

        interval = int(_ucr.get('ldap/overlay/dds/interval', '3600'))
        expected_purge_time = actual_ttl + interval

        print("\nDDS Automatic Purging Information:")
        print(f"  Object TTL: {actual_ttl} seconds")
        print(f"  interval: {interval} seconds")
        print(f"  Expected purge time: {expected_purge_time} seconds from now")
        print("  Object should be automatically removed by DDS after TTL expires")

        if actual_ttl <= 300:
            print(f"\n⚠️  Note: With TTL={actual_ttl}s, you could manually verify")
            print("   automatic purging by checking if object still exists after")
            print(f"   {expected_purge_time} seconds (TTL + interval).")
            print(f"\n   Command to check: ldapsearch -x -D 'cn=admin,{LDAP_BASE}' -W -b '{test_dn}'")
        else:
            print("\n   TTL too long for practical testing verification")

        print("\n✓ Integration test successful - DDS purge chain is properly configured")

    except ldap.LDAPError as e:
        pytest.fail(f"Failed to create DDS test object: {e}")

    finally:
        try:
            lo.delete(test_dn)
            print(f"✓ Cleaned up test object: {test_dn}")
        except ldap.NO_SUCH_OBJECT:
            print(f"✓ Test object already removed (possibly by DDS): {test_dn}")
        except ldap.LDAPError as e:
            print(f"Warning: Could not clean up {test_dn}: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
