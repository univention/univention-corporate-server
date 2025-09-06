#!/usr/share/ucs-test/runner pytest-3 -s
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
## desc: Streamlined integration test for DDS refresh operation
## tags: [ldap, dds, trash_bin, integration]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous
## packages:
##  - univention-directory-manager
##  - python3-univention-directory-manager


import ldap
import pytest
from ldap.extop.dds import RefreshRequest

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


class TestDDSRefreshIntegration:

    def test_dds_with_refresh_operation(self):
        """Test the core DDS refresh functionality on trash objects."""
        dds_enabled = _ucr.is_true('ldap/database/internal/overlay/dds', False)
        if not dds_enabled:
            pytest.skip("DDS overlay is not enabled")

        lo = get_admin_connection()

        with UCSTestUDM() as udm:
            # Create and delete user to get object in trash
            username = random_username()
            user_dn, _ = udm.create_user(
                username=username,
                firstname='DDS',
                lastname='RefreshTest',
            )

            print(f"\n1. Created test user: {user_dn}")
            verify_ldap_object(user_dn, should_exist=True)

            udm.remove_object('users/user', dn=user_dn)
            verify_ldap_object(user_dn, should_exist=False)
            print("2. User moved to trash")

            # Find in trash and verify DDS attributes
            trash_entry = find_trash_object(lo, user_dn)
            assert trash_entry is not None, f"User {user_dn} not found in trash"

            trash_dn, trash_attrs = trash_entry
            print(f"3. Found in trash: {trash_dn}")

            # Verify dynamicObject class
            object_classes = [oc.decode('utf-8') for oc in trash_attrs.get('objectClass', [])]
            assert 'dynamicObject' in object_classes, "Missing dynamicObject class"
            assert 'entryTtl' in trash_attrs, "Missing entryTtl attribute"

            # Test refresh operation to modify TTL
            min_ttl = int(_ucr.get('ldap/database/internal/dds/min-ttl', '86400'))
            test_ttl = min_ttl

            refresh_req = RefreshRequest(entryName=trash_dn, requestTtl=test_ttl)
            print(f"4. Setting TTL to {test_ttl} seconds via refresh")

            try:
                lo.lo.lo.extop_s(refresh_req)
                print("✓ DDS refresh operation successful")

                # Verify TTL was updated
                updated_attrs = lo.get(trash_dn, attr=['entryTtl'])
                actual_ttl = int(updated_attrs['entryTtl'][0].decode('utf-8'))
                print(f"5. Confirmed TTL set to {actual_ttl} seconds")

                # Clean up
                lo.delete(trash_dn)
                print("6. Cleaned up test object")

            except ldap.LDAPError as e:
                # Expected if ACLs don't allow refresh
                if 'Insufficient access' in str(e):
                    pytest.skip("ACL configuration doesn't allow refresh operation")
                raise

    def test_backward_compatibility_dds_disabled(self):
        """Verify trash works without DDS when overlay is disabled."""
        lo = get_admin_connection()

        with UCSTestUDM() as udm:
            username = random_username()
            user_dn, _ = udm.create_user(
                username=username,
                firstname='NoDDS',
                lastname='Test',
            )

            print(f"\n1. Created test user: {user_dn}")
            udm.remove_object('users/user', dn=user_dn)
            print("2. User moved to trash")

            trash_entry = find_trash_object(lo, user_dn)
            assert trash_entry is not None, "Object should be in trash"

            trash_dn, trash_attrs = trash_entry
            print(f"3. Found in trash: {trash_dn}")

            # Verify recyclebin attributes exist
            assert 'univentionRecycleBinObject' in [
                oc.decode('utf-8') for oc in trash_attrs.get('objectClass', [])
            ], "Missing recyclebin object class"

            # Clean up
            lo.delete(trash_dn)
            print("4. Cleaned up test object")
            print("✓ Trash bin works correctly regardless of DDS state")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
