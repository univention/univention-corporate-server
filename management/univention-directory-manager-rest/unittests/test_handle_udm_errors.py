#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Unit tests for handle_udm_errors in the UDM REST API module.

Tests that LDAP errors caused by concurrent modifications
(TYPE_OR_VALUE_EXISTS, NO_SUCH_ATTRIBUTE) are returned as
HTTP 500 (ServerError) instead of HTTP 400 (Bad Request).
"""

from unittest.mock import MagicMock, patch

import ldap
import pytest

import univention.admin.uexceptions as udm_errors
from univention.management.console.error import ServerError
from univention.management.console.modules.udm.udm_ldap import UDM_Error


@pytest.fixture
def resource():
    """Create a minimal Resource instance with mocked dependencies."""
    with (
        patch('univention.admin.rest.module.ucr', MagicMock()),
        patch('univention.admin.rest.module.shared_memory', MagicMock()),
    ):
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
        return instance


class TestHandleUdmErrorsConcurrentModification:
    """Tests for concurrent modification LDAP errors (Bug 58804 / Issue #3243)."""

    def test_type_or_value_exists_raises_500(self, resource):
        """ldap.TYPE_OR_VALUE_EXISTS should result in HTTP 500, not 400."""
        ldap_exc = ldap.TYPE_OR_VALUE_EXISTS(
            {
                'desc': 'Type or value exists',
                'info': 'modify/add: uniqueMember: value #0 already exists',
            },
        )
        udm_exc = udm_errors.ldapError(
            'Type or value exists',
            original_exception=ldap_exc,
        )

        def action():
            raise udm_exc

        with pytest.raises(ServerError):
            resource.handle_udm_errors(action)

    def test_no_such_attribute_raises_500(self, resource):
        """ldap.NO_SUCH_ATTRIBUTE should result in HTTP 500, not 400."""
        ldap_exc = ldap.NO_SUCH_ATTRIBUTE(
            {
                'desc': 'No such attribute',
                'info': 'modify/delete: uniqueMember: no such value',
            },
        )
        udm_exc = udm_errors.ldapError(
            'No such attribute',
            original_exception=ldap_exc,
        )

        def action():
            raise udm_exc

        with pytest.raises(ServerError):
            resource.handle_udm_errors(action)

    def test_other_ldap_error_raises_udm_error(self, resource):
        """Other ldap errors (e.g. CONSTRAINT_VIOLATION) should still raise UDM_Error (HTTP 400)."""
        ldap_exc = ldap.CONSTRAINT_VIOLATION(
            {
                'desc': 'Constraint violation',
            },
        )
        udm_exc = udm_errors.ldapError(
            'Constraint violation',
            original_exception=ldap_exc,
        )

        def action():
            raise udm_exc

        with pytest.raises(UDM_Error):
            resource.handle_udm_errors(action)

    def test_ldap_error_without_original_exception_raises_udm_error(self, resource):
        """ldapError without original_exception should still raise UDM_Error (HTTP 400)."""
        udm_exc = udm_errors.ldapError('some error')

        def action():
            raise udm_exc

        with pytest.raises(UDM_Error):
            resource.handle_udm_errors(action)

    def test_500_message_mentions_concurrent_modification(self, resource):
        """The 500 error message should mention concurrent modification."""
        ldap_exc = ldap.TYPE_OR_VALUE_EXISTS(
            {
                'desc': 'Type or value exists',
            },
        )
        udm_exc = udm_errors.ldapError(
            'Type or value exists',
            original_exception=ldap_exc,
        )

        def action():
            raise udm_exc

        with pytest.raises(ServerError, match='modified by another request'):
            resource.handle_udm_errors(action)

    def test_successful_action_returns_result(self, resource):
        """A successful action should return its result unchanged."""

        def action():
            return 'success'

        result = resource.handle_udm_errors(action)
        assert result == 'success'

    def test_permission_denied_still_raises_403(self, resource):
        """permissionDenied should still raise HTTPError 403."""
        from tornado.web import HTTPError

        udm_exc = udm_errors.permissionDenied()

        def action():
            raise udm_exc

        with pytest.raises(HTTPError) as exc_info:
            resource.handle_udm_errors(action)
        assert exc_info.value.status_code == 403
