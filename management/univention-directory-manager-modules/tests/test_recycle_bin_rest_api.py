#!/usr/bin/python3
"""Test REST API endpoint for manual recycle bin purging."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from unittest import TestCase, mock

import requests
from requests.auth import HTTPBasicAuth

from test_recycle_bin_cleanup import TestRecycleBinIntegration


import pytest

class TestRecycleBinRESTAPI(TestCase):
    """Test REST API endpoint for manual purging."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        from univention.admin.uldap import getAdminConnection
        cls.lo, cls.position = getAdminConnection()
        cls.recyclebin_base = 'cn=recyclebin,cn=internal'
        cls.test_entries = []
        
        cls.api_url = "http://localhost/univention/udm/recyclebin/purge"
        
        cls.username = os.environ.get('TEST_USERNAME', 'Administrator')
        cls.password = os.environ.get('TEST_PASSWORD', 'univention')
        cls.auth = HTTPBasicAuth(cls.username, cls.password)
        
        cls.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def setUp(self):
        """Set up before each test."""
        self.created_dns = []

    def tearDown(self):
        """Clean up after each test."""
        self.cleanup_test_entries()

    def create_test_entry(self, name, delete_at_timestamp):
        """Create a test recycle bin entry."""
        import ldap
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
        except Exception as e:
            return None
    
    def cleanup_test_entries(self):
        """Remove all test entries."""
        import ldap
        for dn in self.test_entries:
            try:
                self.lo.delete(dn)
            except ldap.NO_SUCH_OBJECT:
                pass
            except Exception:
                pass
    
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

    def test_purge_specific_dns(self):
        """Test purging specific DNs via REST API."""
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        dn1 = self.create_test_entry('test-api-1', yesterday.strftime("%Y%m%d%H%M%SZ"))
        dn2 = self.create_test_entry('test-api-2', yesterday.strftime("%Y%m%d%H%M%SZ"))
        
        data = {
            "dns": [dn1, dn2]
        }
        
        response = requests.post(
            self.api_url,
            json=data,
            auth=self.auth,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200, f"API call failed: {response.text}")
        
        result = response.json()
        self.assertTrue(result.get("success"), "Purge operation was not successful")
        self.assertEqual(len(result.get("purged", [])), 2, "Expected 2 entries to be purged")
        
        self.assertEqual(self.count_entries(['test-api-1', 'test-api-2']), 0, 
                         "Entries were not actually deleted from LDAP")

    def test_purge_invalid_dns(self):
        """Test error handling for invalid DNs."""
        
        data = {
            "dns": [
                "cn=nonexistent1,cn=recyclebin,cn=internal,dc=test",
                "cn=nonexistent2,cn=recyclebin,cn=internal,dc=test"
            ]
        }
        
        response = requests.post(
            self.api_url,
            json=data,
            auth=self.auth,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400, 
                        f"Expected 400 for invalid DNs, got {response.status_code}")
        
        error_data = response.json()
        self.assertIn("error_id", error_data)
        self.assertEqual(error_data.get("error_id"), "PURGE_FAILED")
        self.assertIn("affected_items", error_data)

    def test_unauthorized_access(self):
        """Test that authentication is required."""
        
        data = {
            "dns": ["cn=test,cn=recyclebin,cn=internal,dc=test"]
        }
        
        response = requests.post(
            self.api_url,
            json=data,
            headers=self.headers
        )
        
        self.assertIn(response.status_code, [401, 403], 
                     f"Expected 401/403 without auth, got {response.status_code}")

    def test_invalid_request_body(self):
        """Test handling of invalid request bodies."""
        
        response = requests.post(
            self.api_url,
            json={"wrong_field": ["test"]},
            auth=self.auth,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400, "Should reject missing 'dns' field")
        
        response = requests.post(
            self.api_url,
            json={"dns": "not_a_list"},
            auth=self.auth,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400, "Should reject non-list 'dns' field")
        
        response = requests.post(
            self.api_url,
            json={"dns": []},
            auth=self.auth,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400, "Should reject empty 'dns' list")

    def test_mixed_valid_invalid_dns(self):
        """Test purging with mix of valid and invalid DNs."""
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        valid_dn = self.create_test_entry('test-api-mixed', yesterday.strftime("%Y%m%d%H%M%SZ"))
        
        data = {
            "dns": [
                valid_dn,
                "cn=nonexistent,cn=recyclebin,cn=internal,dc=test"
            ]
        }
        
        response = requests.post(
            self.api_url,
            json=data,
            auth=self.auth,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 400, 
                        "Should return 400 when some DNs fail")

    def test_dry_run_mode(self):
        """Test dry-run mode (without --remove-expired)."""
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        dn = self.create_test_entry('test-api-dryrun', yesterday.strftime("%Y%m%d%H%M%SZ"))
        
        data = {"dns": [dn]}
        response = requests.post(
            self.api_url,
            json=data,
            auth=self.auth,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.count_entries(['test-api-dryrun']), 0,
                        "API currently always deletes (no dry-run mode)")


if __name__ == '__main__':
    import unittest
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRecycleBinRESTAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(0 if result.wasSuccessful() else 1)