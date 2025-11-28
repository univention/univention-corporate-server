#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test recyclebin restore functionality in the UDM REST API
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-rest

import random
import subprocess
import time

import pytest

from univention.admin.rest.client import UDM as UDMClient, _NoRelation
from univention.admin.uexceptions import noObject
from univention.admin.uldap import getAdminConnection
from univention.config_registry import ucr
from univention.testing.fixtures_recyclebin import _deleted_object_dn
from univention.testing.strings import random_username
from univention.testing.utils import UCSTestDomainAdminCredentials, restart_listener, restart_slapd, verify_ldap_object


RECYCLEBIN_DN = 'cn=recyclebin,cn=internal'
LDAP_BASE = ucr['ldap/base']


@pytest.fixture(autouse=True, scope='session')
def enabled_recyclebin(ucr_session):
    ucr_session.handler_set(['listener/module/recyclebin/deactivate=false'])
    restart_listener()
    yield
    restart_listener()


def setup_recyclebin_infrastructure():
    """Ensure recyclebin container and DDS overlay are configured."""
    lo, _ = getAdminConnection()

    # Check if recyclebin container exists
    try:
        lo.get(RECYCLEBIN_DN)
        print(f"Recyclebin container {RECYCLEBIN_DN} already exists")
    except noObject:
        print(f"Creating {RECYCLEBIN_DN} container...")
        ldif_content = f"""dn: {RECYCLEBIN_DN}
cn: recyclebin
objectClass: organizationalRole
objectClass: univentionObject
univentionObjectType: container/cn
description: Container for deleted LDAP objects (recycle bin)
"""
        process = subprocess.Popen(
            ['ldapadd', '-x', '-D', f'cn=admin,{LDAP_BASE}', '-y', '/etc/ldap.secret'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, stderr = process.communicate(ldif_content.encode())
        if process.returncode != 0 and b'Already exists' not in stderr:
            raise RuntimeError(f"Failed to create recyclebin container: {stderr.decode()}")
        print(f"Successfully created {RECYCLEBIN_DN}")

    # Ensure DDS overlay is enabled
    from univention.config_registry import handler_set
    dds_enabled = ucr.get('ldap/database/internal/overlay/dds')
    if dds_enabled != 'true':
        print("Enabling DDS overlay for internal database...")
        handler_set([
            'ldap/database/internal/overlay/dds=true',
            'ldap/database/internal/overlay/dds/max-ttl=31536000',
            'ldap/database/internal/overlay/dds/min-ttl=60',
            'ldap/database/internal/overlay/dds/default-ttl=86400',
        ])
        print("DDS overlay configured, restarting slapd...")
        restart_slapd()
        time.sleep(2)
        print("slapd restarted successfully")
    else:
        print("DDS overlay already enabled")

    try:
        lo.get(RECYCLEBIN_DN)
        print("✓ Recyclebin infrastructure setup complete")
    except noObject:
        raise RuntimeError(f"Recyclebin container {RECYCLEBIN_DN} not accessible after setup")


def escape_dn_chars(dn):
    """Escape special characters in a DN for use in another DN"""
    return dn.replace(',', '\\2C').replace('=', '\\3D')


class UDMRestClient(UDMClient):
    @classmethod
    def test_connection(cls):
        account = UCSTestDomainAdminCredentials(ucr)
        return cls.http(f'https://{ucr["hostname"]}.{ucr["domainname"]}/univention/udm/', account.username, account.bindpw)


@pytest.fixture
def udm_rest():
    """Fixture for UDM REST client"""
    return UDMRestClient.test_connection()


@pytest.fixture(scope='module', autouse=True)
def setup_recyclebin():
    """Setup recyclebin infrastructure once for all tests"""
    setup_recyclebin_infrastructure()


@pytest.fixture
def recyclebin_policy(udm, setup_recyclebin):
    """Create a recyclebin policy and container for testing"""
    name = random_username()
    retention_time = random.randint(100, 300)  # days
    pol_dn = udm.create_object(
        'policies/recyclebin',
        position=f'cn=policies,{ucr["ldap/base"]}',
        name=name,
        udm_modules=['users/user', 'groups/group'],
        retention_time=retention_time,
        wait_for_replication=False,
    )
    con_dn = udm.create_object(
        'container/cn',
        position=ucr["ldap/base"],
        name=f'recyclebin_{name}',
        policy_reference=pol_dn,
        wait_for_replication=False,
    )
    return con_dn, retention_time


def test_user_restore_rest_api(udm, udm_rest, recyclebin_policy):
    """Test restoring a deleted user via REST API"""
    container_recyclebin_policy, _ = recyclebin_policy
    user_dn, _username = udm.create_user(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    original_props = udm.get_object('users/user', user_dn)
    udm.remove_object('users/user', dn=user_dn)
    verify_ldap_object(user_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    module = udm_rest.get('recyclebin/removedobject')
    deleted_obj = module.get(deleted_dn)
    response = deleted_obj.restore()
    assert response.response.status_code == 200
    assert deleted_obj.dn == user_dn
    verify_ldap_object(user_dn, should_exist=True)
    verify_ldap_object(deleted_dn, should_exist=False)
    restored_props = udm.get_object('users/user', user_dn)
    assert restored_props['username'][0] == original_props['username'][0]
    assert restored_props['lastname'][0] == original_props['lastname'][0]
    assert restored_props['firstname'][0] == original_props['firstname'][0]


def test_group_restore_rest_api(udm, udm_rest, recyclebin_policy):
    """Test restoring a deleted group via REST API"""
    container_recyclebin_policy, _ = recyclebin_policy
    group_dn, _groupname = udm.create_group(position=container_recyclebin_policy, wait_for_replication=False)
    uoid = udm.get_object('groups/group', group_dn)['univentionObjectIdentifier'][0]
    original_props = udm.get_object('groups/group', group_dn)
    udm.remove_object('groups/group', dn=group_dn)
    verify_ldap_object(group_dn, should_exist=False)
    deleted_dn = _deleted_object_dn(group_dn, uoid)
    verify_ldap_object(deleted_dn, should_exist=True)
    module = udm_rest.get('recyclebin/removedobject')
    deleted_obj = module.get(deleted_dn)
    response = deleted_obj.restore()
    assert response.response.status_code == 200
    verify_ldap_object(group_dn, should_exist=True)
    verify_ldap_object(deleted_dn, should_exist=False)
    restored_props = udm.get_object('groups/group', group_dn)
    assert restored_props['name'][0] == original_props['name'][0]


def test_restore_non_recyclebin_object_fails(udm, udm_rest):
    """Test that restore fails for non-recyclebin objects"""
    user_dn, _ = udm.create_user()
    module = udm_rest.get('users/user')
    user_obj = module.get(user_dn)
    with pytest.raises(_NoRelation) as exc_info:
        user_obj.restore()
    assert str(exc_info.value) == 'udm:restore'


def test_restore_fails_when_parent_container_missing(udm, udm_rest, recyclebin_policy):
    """Test that restore fails gracefully when parent container doesn't exist"""
    from univention.admin.rest.client import UnprocessableEntity
    container_recyclebin_policy, _ = recyclebin_policy
    container_dn = udm.create_object('container/cn', name='temp_container', position=container_recyclebin_policy, wait_for_replication=False)
    user_dn, _ = udm.create_user(position=container_dn, wait_for_replication=False)
    uoid = udm.get_object('users/user', user_dn)['univentionObjectIdentifier'][0]
    udm.remove_object('users/user', dn=user_dn)
    udm.remove_object('container/cn', dn=container_dn)
    deleted_dn = _deleted_object_dn(user_dn, uoid)
    module = udm_rest.get('recyclebin/removedobject')
    deleted_obj = module.get(deleted_dn)
    with pytest.raises(UnprocessableEntity) as exc_info:
        deleted_obj.restore()
    assert 'Parent container' in str(exc_info.value) or 'does not exist' in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
