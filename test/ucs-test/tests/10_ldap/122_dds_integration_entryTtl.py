#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Integration test for DDS overlay with entryTtl automatic purging
## tags: [ldap, dds, recyclebin_bin, integration]
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
from univention.testing.utils import restart_listener, verify_ldap_object


LDAP_BASE = _ucr['ldap/base']
RECYCLEBIN_DN = "cn=recyclebin,cn=internal"


@pytest.fixture(autouse=True, scope='session')
def enabled_recyclebin(ucr_session):
    ucr_session.handler_set(['listener/module/recyclebin/deactivate=false'])
    restart_listener()
    yield
    restart_listener()


def get_admin_connection():
    result = univention.admin.uldap.getAdminConnection()
    if isinstance(result, tuple):
        return result[0]
    return result


def setup_udm():
    udm_modules.update()


def find_recyclebin_object(lo, original_dn):
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


def test_recyclebin_object_with_short_ttl_for_testing():
    dds_enabled = _ucr.is_true('ldap/database/internal/overlay/dds', False)
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

        verify_ldap_object(user_dn, should_exist=True)

        udm.remove_object('users/user', dn=user_dn)
        verify_ldap_object(user_dn, should_exist=False)

        recyclebin_entry = find_recyclebin_object(lo, user_dn)
        assert recyclebin_entry is not None

        recyclebin_dn, recyclebin_attrs = recyclebin_entry

        object_classes = [oc.decode('utf-8') for oc in recyclebin_attrs.get('objectClass', [])]
        assert 'univentionRecycleBinObject' in object_classes
        assert 'extensibleObject' in object_classes
        assert 'dynamicObject' in object_classes

        assert 'entryTtl' in recyclebin_attrs
        ttl_value = int(recyclebin_attrs['entryTtl'][0].decode('utf-8'))

        expected_ttl = 30 * 86400
        # Allow small tolerance for timing differences
        assert abs(ttl_value - expected_ttl) <= 10

        assert 'univentionRecycleBinOriginalDN' in recyclebin_attrs
        assert 'univentionRecycleBinDeleteAt' in recyclebin_attrs
        assert 'univentionRecycleBinOriginalType' in recyclebin_attrs

        original_dn = recyclebin_attrs['univentionRecycleBinOriginalDN'][0].decode('utf-8')
        assert original_dn == user_dn

        original_type = recyclebin_attrs['univentionRecycleBinOriginalType'][0].decode('utf-8')
        assert original_type == 'users/user'

        try:
            lo.delete(recyclebin_dn)
        except ldap.LDAPError:
            pass  # Cleanup failed, but test passed


def test_manual_dds_object_with_short_ttl():
    dds_enabled = _ucr.is_true('ldap/database/internal/overlay/dds', False)
    if not dds_enabled:
        pytest.skip("DDS overlay is not enabled")

    lo = get_admin_connection()

    test_cn = f"dds-test-{int(time.time())}"
    test_dn = f"cn={test_cn},cn=internal"

    test_ttl = 60
    min_ttl = int(_ucr.get('ldap/database/internal/overlay/dds/min-ttl', '86400'))

    if test_ttl < min_ttl:
        test_ttl = min_ttl

    attrs = {
        'objectClass': [b'dynamicObject', b'organizationalRole'],
        'cn': [test_cn.encode('utf-8')],
        'description': [b'Test object for DDS automatic purging'],
    }

    controls = [RelaxRulesControl()]
    lo.add(test_dn, list(attrs.items()), serverctrls=controls)

    refresh_req = RefreshRequest(entryName=test_dn, requestTtl=test_ttl)
    lo.lo.lo.extop_s(refresh_req, serverctrls=[])

    created_attrs = lo.get(test_dn, attr=['*', '+'])
    assert created_attrs is not None

    object_classes = [oc.decode('utf-8') for oc in created_attrs.get('objectClass', [])]
    assert 'dynamicObject' in object_classes
    assert 'entryTtl' in created_attrs

    actual_ttl = int(created_attrs['entryTtl'][0].decode('utf-8'))

    assert actual_ttl > 0

    lo.delete(test_dn)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
