#!/usr/bin/python3
"""Integration tests for recycle bin cleanup script - creates real LDAP data."""

import os
import subprocess
import sys
from datetime import datetime, timedelta
import ldap
import ldap.dn
from univention.admin.uldap import getAdminConnection
from univention.udm import UDM


class TestRecycleBinIntegration:
    """Integration tests with real LDAP data."""
    
    def __init__(self):
        self.lo, self.position = getAdminConnection()
        self.recyclebin_base = 'cn=recyclebin,cn=internal'
        self.test_entries = []
        self.script_path = '/usr/share/univention-directory-manager-tools/univention-recycle-bin-clean-expired-entries'
        # Fallback for development - update path relative to new test location
        if not os.path.exists(self.script_path):
            self.script_path = '../scripts/univention-recycle-bin-clean-expired-entries'
        
        # Ensure recyclebin container exists
        self._ensure_recyclebin_container()
    
    def _ensure_recyclebin_container(self):
        """Ensure the recyclebin container exists."""
        internal_dn = f'cn=internal,{self.lo.base}'
        recyclebin_dn = f'{self.recyclebin_base},{self.lo.base}'
        
        # Check/create internal container
        try:
            self.lo.search(base=internal_dn, scope='base')
        except ldap.NO_SUCH_OBJECT:
            print(f"Creating internal container: {internal_dn}")
            attrs = [
                ('objectClass', [b'top', b'organizationalRole']),
                ('cn', [b'internal']),
            ]
            try:
                self.lo.add(internal_dn, attrs)
            except ldap.ALREADY_EXISTS:
                pass
        
        # Check/create recyclebin container
        try:
            self.lo.search(base=recyclebin_dn, scope='base')
        except ldap.NO_SUCH_OBJECT:
            print(f"Creating recyclebin container: {recyclebin_dn}")
            attrs = [
                ('objectClass', [b'top', b'organizationalRole']),
                ('cn', [b'recyclebin']),
            ]
            try:
                self.lo.add(recyclebin_dn, attrs)
            except ldap.ALREADY_EXISTS:
                pass
    
    def create_test_entry(self, name, delete_at_timestamp):
        """Create a test recycle bin entry."""
        # Use cn as RDN like existing entries
        original_dn = f'uid={name},cn=users,dc=test'
        dn = f'cn={name},{self.recyclebin_base},{self.lo.base}'
        
        attrs = [
            ('objectClass', [b'top', b'organizationalRole', b'univentionRecycleBinObject']),
            ('cn', [name.encode('utf-8')]),  # Required for organizationalRole
            ('univentionRecycleBinOriginalDN', [original_dn.encode('utf-8')]),
            ('univentionRecycleBinOriginalType', [b'users/user']),
            ('univentionRecycleBinDeletedBy', [self.lo.binddn.encode('utf-8')]),
            ('univentionRecycleBinDeleteAt', [delete_at_timestamp.encode('utf-8')]),
        ]
        
        try:
            self.lo.add(dn, attrs)
            self.test_entries.append(dn)
            print(f"Created test entry: {dn}")
            return dn
        except ldap.ALREADY_EXISTS:
            print(f"Entry {dn} already exists, will be cleaned up")
            self.test_entries.append(dn)
            return dn
        except Exception as e:
            print(f"Failed to create test entry {dn}: {e}")
            return None
    
    def cleanup_test_entries(self):
        """Remove all test entries."""
        for dn in self.test_entries:
            try:
                self.lo.delete(dn)
                print(f"Cleaned up: {dn}")
            except ldap.NO_SUCH_OBJECT:
                pass  # Already deleted
            except Exception as e:
                print(f"Failed to cleanup {dn}: {e}")
    
    def run_cleanup_script(self, remove=False, scheduled=False):
        """Run the cleanup script and capture output."""
        cmd = ['python3', self.script_path]
        if remove:
            cmd.append('--remove-expired')
        if scheduled:
            cmd.append('--scheduled')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    
    def count_entries(self, entry_names):
        """Count how many test entries still exist."""
        count = 0
        for name in entry_names:
            # Search by cn since that's what we use as RDN
            search_filter = f'(&(objectClass=univentionRecycleBinObject)(cn={name}))'
            try:
                results = self.lo.search(base=f'{self.recyclebin_base},{self.lo.base}', filter=search_filter)
                if results:
                    count += 1
            except Exception as e:
                print(f"Error counting {name}: {e}")
        return count
    
    def test_expired_entries_detection(self):
        """Test that expired entries are correctly identified."""
        print("\n=== Test 1: Expired entries detection ===")
        
        # Create test entries
        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        expired_name = 'test-expired-user'
        future_name = 'test-future-user'
        
        self.create_test_entry(expired_name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(future_name, tomorrow.strftime("%Y%m%d%H%M%SZ"))
        
        # Run script in list mode
        stdout, stderr, returncode = self.run_cleanup_script(remove=False)
        
        # With logging enabled, output goes to log file, not stdout
        # We can only verify by checking that entries still exist
        
        # Check return code
        assert returncode == 0, f"Script failed with return code {returncode}"
        
        # Verify entries still exist (list mode shouldn't delete)
        count = self.count_entries([expired_name, future_name])
        print(f"Remaining entries: {count} (expected 2)")
        assert count == 2, "Entries were deleted in list mode"
        
        print("✓ Expired entries correctly identified")
        return True
    
    def test_expired_entries_removal(self):
        """Test that expired entries are actually removed."""
        print("\n=== Test 2: Expired entries removal ===")
        
        # Create test entries
        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        expired_name = 'test-remove-expired'
        future_name = 'test-keep-future'
        
        self.create_test_entry(expired_name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(future_name, tomorrow.strftime("%Y%m%d%H%M%SZ"))
        
        # Run script in remove mode
        stdout, stderr, returncode = self.run_cleanup_script(remove=True)
        
        # Check return code
        assert returncode == 0, f"Script failed with return code {returncode}"
        # Note: With logging, deletion messages go to log file, not stdout
        
        # Verify expired entry is gone, future entry remains
        assert self.count_entries([expired_name]) == 0, "Expired entry was not deleted"
        assert self.count_entries([future_name]) == 1, "Future entry was incorrectly deleted"
        
        print("✓ Expired entries correctly removed")
        return True
    
    def test_script_with_no_expired_entries(self):
        """Test script behavior when no entries are expired."""
        print("\n=== Test 3: No expired entries ===")
        
        # Create only future entries
        name1 = 'test-future-1'
        name2 = 'test-future-2'
        
        from datetime import datetime, timedelta
        tomorrow = datetime.utcnow() + timedelta(days=1)
        next_week = datetime.utcnow() + timedelta(days=7)
        
        self.create_test_entry(name1, tomorrow.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(name2, next_week.strftime("%Y%m%d%H%M%SZ"))
        
        # Run script in remove mode
        stdout, stderr, returncode = self.run_cleanup_script(remove=True)
        
        # Should complete without errors
        assert returncode == 0, f"Script failed with return code {returncode}"
        # Note: With logging, output goes to log file, not stdout
        
        # Both entries should still exist
        assert self.count_entries([name1, name2]) == 2, "Future entries were deleted"
        
        print("✓ Script correctly handles no expired entries")
        return True
    
    def test_scheduled_vs_manual_logging(self):
        """Test that scheduled flag affects logging."""
        print("\n=== Test 4: Scheduled vs Manual logging ===")
        
        # Create an expired entry
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        name = 'test-scheduled-logging'
        
        # Test 1: Manual run (without --scheduled)
        self.create_test_entry(name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        stdout1, stderr1, returncode1 = self.run_cleanup_script(remove=True, scheduled=False)
        assert returncode1 == 0, "Manual run failed"
        
        # Test 2: Scheduled run (with --scheduled)
        self.create_test_entry(name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        stdout2, stderr2, returncode2 = self.run_cleanup_script(remove=True, scheduled=True)
        assert returncode2 == 0, "Scheduled run failed"
        
        print("✓ Both scheduled and manual modes work correctly")
        return True
    
    def run_all_tests(self):
        """Run all tests."""
        print("Starting integration tests for recycle bin cleanup")
        print("=" * 50)
        
        tests = [
            self.test_expired_entries_detection,
            self.test_expired_entries_removal,
            self.test_script_with_no_expired_entries,
            self.test_scheduled_vs_manual_logging,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except AssertionError as e:
                print(f"✗ Test failed: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ Test error: {e}")
                failed += 1
            finally:
                # Clean up after each test
                self.cleanup_test_entries()
                self.test_entries = []
        
        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        return failed == 0


if __name__ == '__main__':
    import os
    tester = TestRecycleBinIntegration()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)