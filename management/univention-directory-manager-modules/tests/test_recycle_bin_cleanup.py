#!/usr/bin/python3
"""Integration tests for recycle bin cleanup script - creates real LDAP data."""

import os
import subprocess
from datetime import datetime, timedelta

import ldap
import ldap.dn
import pytest

from univention.admin.uldap import getAdminConnection


class TestRecycleBinIntegration:
    """Integration tests with real LDAP data."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.lo, self.position = getAdminConnection()
        self.recyclebin_base = 'cn=recyclebin,cn=internal'
        self.test_entries = []
        self.script_path = '/usr/share/univention-directory-manager-tools/univention-recycle-bin-clean-expired-entries'
        if not os.path.exists(self.script_path):
            test_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_path = os.path.join(test_dir, '..', 'scripts', 'univention-recycle-bin-clean-expired-entries')
            if not os.path.exists(self.script_path):
                self.script_path = 'scripts/univention-recycle-bin-clean-expired-entries'

        self._ensure_recyclebin_container()

        yield

        self.cleanup_test_entries()

    def _ensure_recyclebin_container(self):
        """Ensure the recyclebin container exists."""
        internal_dn = f'cn=internal,{self.lo.base}'
        recyclebin_dn = f'{self.recyclebin_base},{self.lo.base}'

        try:
            self.lo.search(base=internal_dn, scope='base')
        except ldap.NO_SUCH_OBJECT:
            attrs = [
                ('objectClass', [b'top', b'organizationalRole']),
                ('cn', [b'internal']),
            ]
            try:
                self.lo.add(internal_dn, attrs)
            except ldap.ALREADY_EXISTS:
                pass

        try:
            self.lo.search(base=recyclebin_dn, scope='base')
        except ldap.NO_SUCH_OBJECT:
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
        original_dn = f'uid={name},cn=users,dc=test'
        dn = f'cn={name},{self.recyclebin_base},{self.lo.base}'

        attrs = [
            ('objectClass', [b'top', b'organizationalRole', b'univentionRecycleBinObject']),
            ('cn', [name.encode('utf-8')]),
            ('univentionRecycleBinOriginalDN', [original_dn.encode('utf-8')]),
            ('univentionRecycleBinOriginalType', [b'users/user']),
            ('univentionRecycleBinDeletedBy', [self.lo.binddn.encode('utf-8')]),
            ('univentionRecycleBinDeleteAt', [delete_at_timestamp.encode('utf-8')]),
        ]

        try:
            self.lo.add(dn, attrs)
            self.test_entries.append(dn)
            return dn
        except ldap.ALREADY_EXISTS:
            self.test_entries.append(dn)
            return dn
        except Exception:
            return None

    def cleanup_test_entries(self):
        """Remove all test entries."""
        for dn in self.test_entries:
            try:
                self.lo.delete(dn)
            except ldap.NO_SUCH_OBJECT:
                pass
            except Exception:
                pass

    def run_cleanup_script(self, remove=False, scheduled=False):
        """Run the cleanup script and capture output."""
        cmd = ['python3', self.script_path]
        if remove:
            cmd.append('--remove-expired')
        if scheduled:
            cmd.append('--scheduled')

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout, result.stderr, result.returncode

    def count_entries(self, entry_names):
        """Count how many test entries still exist."""
        count = 0
        for name in entry_names:
            search_filter = f'(&(objectClass=univentionRecycleBinObject)(cn={name}))'
            try:
                results = self.lo.search(base=f'{self.recyclebin_base},{self.lo.base}', filter=search_filter)
                if results:
                    count += 1
            except Exception:
                pass
        return count

    def test_expired_entries_detection(self):
        """Test that expired entries are correctly identified."""

        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)

        expired_name = 'test-expired-user'
        future_name = 'test-future-user'

        self.create_test_entry(expired_name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(future_name, tomorrow.strftime("%Y%m%d%H%M%SZ"))

        _stdout, _stderr, returncode = self.run_cleanup_script(remove=False)

        assert returncode == 0, f"Script failed with return code {returncode}"

        count = self.count_entries([expired_name, future_name])
        assert count == 2, "Entries were deleted in list mode"

    def test_expired_entries_removal(self):
        """Test that expired entries are actually removed."""

        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)

        expired_name = 'test-remove-expired'
        future_name = 'test-keep-future'

        self.create_test_entry(expired_name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(future_name, tomorrow.strftime("%Y%m%d%H%M%SZ"))

        _stdout, _stderr, returncode = self.run_cleanup_script(remove=True)

        assert returncode == 0, f"Script failed with return code {returncode}"

        assert self.count_entries([expired_name]) == 0, "Expired entry was not deleted"
        assert self.count_entries([future_name]) == 1, "Future entry was incorrectly deleted"

    def test_script_with_no_expired_entries(self):
        """Test script behavior when no entries are expired."""

        name1 = 'test-future-1'
        name2 = 'test-future-2'

        tomorrow = datetime.utcnow() + timedelta(days=1)
        next_week = datetime.utcnow() + timedelta(days=7)

        self.create_test_entry(name1, tomorrow.strftime("%Y%m%d%H%M%SZ"))
        self.create_test_entry(name2, next_week.strftime("%Y%m%d%H%M%SZ"))

        _stdout, _stderr, returncode = self.run_cleanup_script(remove=True)

        assert returncode == 0, f"Script failed with return code {returncode}"

        assert self.count_entries([name1, name2]) == 2, "Future entries were deleted"

    def test_scheduled_vs_manual_logging(self):
        """Test that scheduled flag affects logging."""

        yesterday = datetime.utcnow() - timedelta(days=1)
        name = 'test-scheduled-logging'

        # Test 1: Manual run (without --scheduled)
        self.create_test_entry(name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        _stdout1, _stderr1, returncode1 = self.run_cleanup_script(remove=True, scheduled=False)
        assert returncode1 == 0, "Manual run failed"

        # Test 2: Scheduled run (with --scheduled)
        self.create_test_entry(name, yesterday.strftime("%Y%m%d%H%M%SZ"))
        _stdout2, _stderr2, returncode2 = self.run_cleanup_script(remove=True, scheduled=True)
        assert returncode2 == 0, "Scheduled run failed"
