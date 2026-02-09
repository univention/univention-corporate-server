#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import ssl
from argparse import Namespace
from unittest.mock import patch

import pytest


def test_HTTError(umc):
    _resp = Namespace(**{'getheader': lambda a, b: b})  # noqa: PIE804
    req = umc.Request('GET', '/')
    for code, Error in umc.HTTPError.codes.items():
        resp = umc.Response(code, 'reason', 'no body', {}, _resp)
        with pytest.raises(Error):
            raise umc.HTTPError(req, resp, 'theHostname')


class TestClientSkipHostnameCheck:
    """Tests for the skip_hostname_check parameter in Client."""

    @pytest.fixture
    def mock_authenticate(self, umc):
        """Mock authentication to avoid actual network calls."""
        with patch.object(umc.Client, 'authenticate') as mock:
            yield mock

    def test_skip_hostname_check_default_localhost(self, umc, mock_authenticate):
        """When hostname is None (localhost), skip_hostname_check defaults to True."""
        client = umc.Client(hostname=None, username='test', password='test')
        assert client._is_localhost is True
        assert client._skip_hostname_check is True

    def test_skip_hostname_check_default_remote(self, umc, mock_authenticate):
        """When hostname is provided, skip_hostname_check defaults to False."""
        client = umc.Client(hostname='remote.example.com', username='test', password='test')
        assert client._is_localhost is False
        assert client._skip_hostname_check is False

    def test_skip_hostname_check_explicit_true(self, umc, mock_authenticate):
        """skip_hostname_check=True overrides the default."""
        client = umc.Client(hostname='remote.example.com', username='test', password='test', skip_hostname_check=True)
        assert client._skip_hostname_check is True

    def test_skip_hostname_check_explicit_false(self, umc, mock_authenticate):
        """skip_hostname_check=False overrides the default for localhost."""
        client = umc.Client(hostname=None, username='test', password='test', skip_hostname_check=False)
        assert client._is_localhost is True
        assert client._skip_hostname_check is False

    def test_get_connection_with_skip_hostname_check(self, umc, mock_authenticate):
        """When skip_hostname_check is True, SSL context should have check_hostname=False."""
        client = umc.Client(hostname=None, username='test', password='test')
        assert client._skip_hostname_check is True

        with patch.object(umc.Client, 'ConnectionType') as mock_connection_type:
            client._get_connection()
            mock_connection_type.assert_called_once()
            call_kwargs = mock_connection_type.call_args[1]
            assert 'context' in call_kwargs
            ssl_context = call_kwargs['context']
            assert isinstance(ssl_context, ssl.SSLContext)
            assert ssl_context.check_hostname is False

    def test_get_connection_without_skip_hostname_check(self, umc, mock_authenticate):
        """When skip_hostname_check is False, no custom SSL context should be passed."""
        client = umc.Client(hostname='remote.example.com', username='test', password='test')
        assert client._skip_hostname_check is False

        with patch.object(umc.Client, 'ConnectionType') as mock_connection_type:
            client._get_connection()
            mock_connection_type.assert_called_once()
            call_kwargs = mock_connection_type.call_args[1]
            assert 'context' not in call_kwargs
