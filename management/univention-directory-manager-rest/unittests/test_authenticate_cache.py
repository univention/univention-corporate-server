#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Unit tests for ResourceBase.authenticate's Authorization-header cache handling.

Covers Bug #59702: a malformed shared_memory.authenticated cache entry must
not crash authentication - it should be discarded and a fresh entry built -
while a well-formed cache entry must still short-circuit re-parsing and
re-authentication, unaffected by the fix.
"""

import base64
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_shared_memory():
    """Patch the shared_memory singleton with a real dict-backed cache."""
    with patch('univention.admin.rest.module.shared_memory') as mock_sm:
        mock_sm.authenticated = {}
        mock_sm.authorized = {}
        yield mock_sm


@pytest.fixture
def resource(mock_shared_memory):
    """Create a minimal Resource instance with mocked dependencies."""
    with patch('univention.admin.rest.module.ucr', MagicMock()):
        from univention.admin.rest.module import Resource

        mock_app = MagicMock()
        mock_app.settings = {}
        mock_request = MagicMock()
        mock_request.method = 'GET'
        mock_request.headers = {}
        mock_request.body = b''
        mock_request.connection = MagicMock()

        instance = Resource.__new__(Resource)
        instance.application = mock_app
        instance.request = mock_request
        # Bypass the real delegative-administration lookup (needs a real
        # UCR); it is irrelevant to the cache-handling logic under test.
        instance._authz_ldap_connection = MagicMock(side_effect=lambda userdn, conn: conn)
        yield instance


@pytest.fixture
def mock_ldap_connection():
    conn = MagicMock()
    conn.whoami.return_value = 'uid=testuser,dc=example,dc=com'
    return conn


def _basic_auth_header(username, password):
    credentials = base64.b64encode(f'{username}:{password}'.encode('ISO8859-1')).decode('ISO8859-1')
    return f'Basic {credentials}'


class TestAuthenticateCacheHandling:
    """Tests for Bug #59702: malformed shared_memory.authenticated entries."""

    @pytest.mark.parametrize(
        'malformed_value',
        [
            'not-a-tuple',  # wrong length -> ValueError (too many values to unpack)
            ('only', 'two'),  # wrong length -> ValueError (not enough values to unpack)
            None,  # not iterable -> TypeError
            False,  # not iterable -> TypeError
            12345,  # not iterable -> TypeError
        ],
    )
    def test_malformed_cache_entry_is_discarded_and_reauthenticates(
        self,
        resource,
        mock_shared_memory,
        mock_ldap_connection,
        malformed_value,
    ):
        """A malformed cache entry must be discarded and replaced, not crash authentication."""
        authorization = _basic_auth_header('testuser', 'secret')
        mock_shared_memory.authenticated[authorization] = malformed_value
        resource._auth_get_userdn = MagicMock(return_value='uid=testuser,dc=example,dc=com')

        with (
            patch('univention.admin.rest.module.get_user_ldap_read_connection', return_value=(mock_ldap_connection, MagicMock())),
            patch('univention.admin.rest.module.log') as mock_log,
        ):
            result = resource.authenticate(authorization)

        assert result is True
        resource._auth_get_userdn.assert_called_once_with('testuser')
        mock_log.warning.assert_called_once()
        assert mock_shared_memory.authenticated[authorization] == (None, 'testuser', 'uid=testuser,dc=example,dc=com', 'secret')

    def test_no_cache_entry_performs_full_authentication(self, resource, mock_shared_memory, mock_ldap_connection):
        """Baseline: an Authorization header that is not cached yet authenticates normally."""
        authorization = _basic_auth_header('testuser', 'secret')
        resource._auth_get_userdn = MagicMock(return_value='uid=testuser,dc=example,dc=com')

        with patch('univention.admin.rest.module.get_user_ldap_read_connection', return_value=(mock_ldap_connection, MagicMock())):
            result = resource.authenticate(authorization)

        assert result is True
        resource._auth_get_userdn.assert_called_once_with('testuser')
        assert mock_shared_memory.authenticated[authorization] == (None, 'testuser', 'uid=testuser,dc=example,dc=com', 'secret')

    def test_well_formed_cache_entry_short_circuits_reauthentication(self, resource, mock_shared_memory, mock_ldap_connection):
        """Happy path: a regular, well-formed cache entry is used as-is, without reparsing credentials."""
        authorization = _basic_auth_header('testuser', 'secret')
        cached = (None, 'testuser', 'uid=testuser,dc=example,dc=com', 'secret')
        mock_shared_memory.authenticated[authorization] = cached
        resource._auth_get_userdn = MagicMock(side_effect=AssertionError('should not re-parse a cached, well-formed entry'))

        with (
            patch('univention.admin.rest.module.get_user_ldap_read_connection', return_value=(mock_ldap_connection, MagicMock())),
            patch('univention.admin.rest.module.log') as mock_log,
        ):
            result = resource.authenticate(authorization)

        assert result is True
        resource._auth_get_userdn.assert_not_called()
        mock_log.warning.assert_not_called()
        assert mock_shared_memory.authenticated[authorization] == cached

    def test_concurrent_eviction_between_check_and_lookup_is_handled(self, resource, mock_ldap_connection):
        """
        Regression guard: a concurrent pop by another worker process between the
        membership check and the lookup raises KeyError, which must not crash authentication.
        """

        class _ConcurrentlyEvictedDict(dict):
            """Raises KeyError on the first lookup only, then behaves like a normal dict."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._raised = False

            def __getitem__(self, key):
                if not self._raised:
                    self._raised = True
                    super().pop(key, None)
                    raise KeyError(key)
                return super().__getitem__(key)

        authorization = _basic_auth_header('testuser', 'secret')
        evicted_cache = _ConcurrentlyEvictedDict({authorization: 'placeholder'})
        resource._auth_get_userdn = MagicMock(return_value='uid=testuser,dc=example,dc=com')

        with (
            patch('univention.admin.rest.module.shared_memory') as mock_sm,
            patch('univention.admin.rest.module.get_user_ldap_read_connection', return_value=(mock_ldap_connection, MagicMock())),
            patch('univention.admin.rest.module.log') as mock_log,
        ):
            mock_sm.authenticated = evicted_cache
            mock_sm.authorized = {}
            result = resource.authenticate(authorization)

        assert result is True
        resource._auth_get_userdn.assert_called_once_with('testuser')
        mock_log.warning.assert_not_called()
        assert evicted_cache[authorization] == (None, 'testuser', 'uid=testuser,dc=example,dc=com', 'secret')
