#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit tests for :py:meth:`univention.admin.license.license.is_enterprise`."""

from unittest.mock import MagicMock, patch

import pytest

import univention.admin.license as udm_license


LICENSE_DN = 'cn=admin,cn=license,cn=univention,dc=example,dc=net'
LDAP_BASE = 'dc=example,dc=net'


def make_lo(*licenses):
    lo = MagicMock()
    lo.search.return_value = [
        (dn, {'univentionLicenseBaseDN': [base_dn.encode('UTF-8')]})
        for dn, base_dn in licenses
    ]
    return lo


@pytest.mark.parametrize('base_dn,validity,expected', [
    pytest.param(LDAP_BASE, 0, True, id='valid-subscription'),
    pytest.param('UCS Core Edition', 0, False, id='core-edition'),
    pytest.param('Free for personal use edition', 0, False, id='free-for-personal-use'),
    pytest.param(LDAP_BASE, 1, False, id='invalid-signature'),
    pytest.param(LDAP_BASE, 2, False, id='expired'),
    pytest.param('dc=other,dc=net', 4, False, id='wrong-base-dn'),
    pytest.param(LDAP_BASE, -1, False, id='not-a-license-object'),
])
def test_is_enterprise(base_dn, validity, expected):
    lo = make_lo((LICENSE_DN, base_dn))
    with patch.object(udm_license.univention.license, 'check', return_value=validity) as check:
        assert udm_license.license.is_enterprise(lo) is expected
    check.assert_called_once_with(LICENSE_DN)


def test_is_enterprise_without_license():
    lo = make_lo()
    with patch.object(udm_license.univention.license, 'check') as check:
        assert udm_license.license.is_enterprise(lo) is False
    check.assert_not_called()


def test_is_enterprise_does_not_trust_unvalidated_values():
    """An invalid license claiming the domain base DN must not count as subscription."""
    lo = make_lo(('cn=fake,cn=license,cn=univention,dc=example,dc=net', LDAP_BASE), (LICENSE_DN, 'UCS Core Edition'))
    with patch.object(udm_license.univention.license, 'check', side_effect=[1, 0]):
        assert udm_license.license.is_enterprise(lo) is False


def test_is_enterprise_does_not_change_selected_license():
    lo = make_lo((LICENSE_DN, LDAP_BASE))
    with (
        patch.object(udm_license.univention.license, 'check', return_value=0),
        patch.object(udm_license.univention.license, 'select') as select,
        patch.object(udm_license.univention.license, 'selectDN') as select_dn,
    ):
        assert udm_license.license.is_enterprise(lo) is True
    select.assert_not_called()
    select_dn.assert_not_called()
