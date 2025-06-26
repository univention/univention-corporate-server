#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test minimal required properties for functional UMC UI with Guardian restrictions
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous


import subprocess

import pytest
from conftest import ClientHelper

from univention.config_registry import ucr as _ucr
from univention.lib.umc import BadRequest, UnprocessableEntity
from univention.testing.strings import random_username


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')

# Property sets for users and groups
USER_PROPERTY_SETS = {
    'asterisk': ['*'],
    'minimal_working': ['title', 'firstname', 'lastname', 'username', 'password', 'pwdChangeNextLogin', 'overridePWLength', 'disabled', 'description'],
    'missing_username': ['title', 'firstname', 'lastname', 'password', 'disabled', 'description'],
    'missing_lastname': ['username', 'password', 'disabled', 'description'],
    'empty': [],
}

GROUP_PROPERTY_SETS = {
    'asterisk': ['*'],
    'minimal_working': ['name'],
    'missing_username': ['description', 'sambaGroupType'],
    'missing_lastname': ['name', 'description'],
    'empty': [],
}


# Session-scoped cache to store created roles, groups, and users
_session_cache = {}


@pytest.fixture(scope='session')
def session_roles(ldap_base, guardian_role, build_acl):
    """Session-scoped fixture that creates all needed roles once and caches them."""
    if 'roles' not in _session_cache:
        _session_cache['roles'] = {}
        testroleprefix = random_username()
        acls = []

        for (property_set_key, user_property_set) in USER_PROPERTY_SETS.items():
            user_property_set = USER_PROPERTY_SETS[property_set_key]
            group_property_set = GROUP_PROPERTY_SETS[property_set_key]
            role = f'umc:udm:{testroleprefix}_{property_set_key}'
            acls.append(build_acl(role, user_property_set, group_property_set))
            _session_cache['roles'][property_set_key] = role

        # push ACLs to guardian
        guardian_role('\n'.join(acls))

    return _session_cache['roles']


@pytest.fixture(scope='session')
def session_users(ldap_base, udm_session, ou, session_roles):
    """Session-scoped fixture that creates all needed users once and caches them."""
    if 'users' not in _session_cache:
        _session_cache['users'] = {}

        for property_set_key in USER_PROPERTY_SETS.keys():
            user_name = random_username()
            user_guardian_roles = []
            user_guardian_roles.append(session_roles[property_set_key])
            udm_session.create_object(
                'users/user', username=user_name, lastname=user_name, password='univention', position=ou.dn,
                guardianRoles=user_guardian_roles,
                policy_reference=[f'cn=organizational-unit-admins,cn=UMC,cn=policies,{ldap_base}'],
            )
            cache_key = f'{property_set_key}'
            _session_cache['users'][cache_key] = user_name

    return _session_cache['users']


@pytest.fixture
def guardian_setup(session_users, property_set_key):
    """Fixture that returns an authenticated client using cached session resources."""
    cache_key = f'{property_set_key}'
    user_name = session_users[cache_key]

    client = ClientHelper()
    client.authenticate(user_name, 'univention')

    return client


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', False),
    ('missing_username', False),
    ('missing_lastname', False),
    ('empty', False),
])
def test_user_creation(guardian_setup, property_set_key, expected_success, ou, admin_umc_client):
    """Tests user creation, which requires a new user to be added."""
    client = guardian_setup
    result = {}
    try:
        result = client.create_user(ou.user_default_container)
        assert result.get('success') is expected_success
    except (AssertionError, BadRequest):
        if expected_success:
            raise
    finally:
        if result.get('success'):
            admin_umc_client.delete_object('users/user', result['$dn$'])


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', True),
])
def test_user_query(guardian_setup, property_set_key, expected_success, ou, udm_session):
    """Tests querying for users."""
    client = guardian_setup
    try:

        result = client.umc_command(
            'udm/query',
            {
                'container': ou.dn,
                'objectType': 'users/user',
                'objectProperty': 'None',
                'objectPropertyValue': '',
                'fields': ['name'],
            },
            'users/user',
        )
        if expected_success:
            assert result.status == 200
            list = udm_session.list_objects('users/user', position=ou.user_default_container)
            count = len(list)
            assert count == len(result.result)
        else:
            assert result.status == 403
    except (AssertionError, BadRequest, UnprocessableEntity):
        if expected_success:
            raise


@pytest.fixture(autouse=True)
def kill_udm_modules_process():
    yield
    subprocess.call(['pkill', '-f', '.*univention-management-console-module -m udm.*'])


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', True),
])
def test_user_get(guardian_setup, property_set_key, expected_success, udm_session, ou):
    """Tests retrieving a single user."""
    client = guardian_setup
    dummy_username = random_username()
    dummy_dn = udm_session.create_object(
        'users/user', username=dummy_username, lastname=dummy_username,
        password='univention', position=ou.user_default_container,
    )
    try:
        result = client.get_object('users/user', dummy_dn)
        if expected_success:
            assert result is not None
        else:
            assert result is None
    except (AssertionError, BadRequest):
        if expected_success:
            raise


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', False),
    ('missing_username', False),
    ('missing_lastname', False),
    ('empty', False),
])
def test_group_creation(guardian_setup, property_set_key, expected_success, ou, admin_umc_client):
    """Tests group creation, which requires a new group to be added."""
    client = guardian_setup
    result = {}
    try:
        result = client.create_group(ou.group_default_container)
        assert result.get('success') is expected_success
    except (AssertionError, BadRequest):
        if expected_success:
            raise
    finally:
        if result.get('success'):
            admin_umc_client.delete_object('groups/group', result['$dn$'])


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', True),
])
def test_group_query(guardian_setup, property_set_key, expected_success, ou, udm_session):
    """Tests querying for groups."""
    client = guardian_setup
    try:
        result = client.umc_command(
            'udm/query',
            {
                'container': ou.dn,
                'objectType': 'groups/group',
                'objectProperty': 'None',
                'objectPropertyValue': '',
                'fields': ['name'],
            },
            'groups/group',
        )
        if expected_success:
            assert result.status == 200
            count = len(udm_session.list_objects('groups/group', position=ou.group_default_container))
            assert count == len(result.result)
        else:
            assert result.status == 403
    except (AssertionError, BadRequest, UnprocessableEntity):
        if expected_success:
            raise


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', True),
])
def test_group_get(guardian_setup, property_set_key, expected_success, udm_session, ou):
    """Tests retrieving a single group."""
    client = guardian_setup
    dummy_groupname = random_username()
    dummy_dn = udm_session.create_object(
        'groups/group', name=dummy_groupname, position=ou.group_default_container,
    )
    try:
        result = client.get_object('groups/group', dummy_dn)
        if expected_success:
            assert result is not None
        else:
            assert result is None
    except (AssertionError, BadRequest):
        if expected_success:
            raise


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', False),
    ('missing_lastname', True),
    ('empty', False),
])
def test_group_edit(guardian_setup, property_set_key, expected_success, udm_session, ou, admin_umc_client):
    """Tests modifying a group's details."""
    client = guardian_setup
    dummy_dn = udm_session.create_object(
        'groups/group', name=random_username(), position=ou.group_default_container,
    )
    result = {}
    new_name = random_username()
    try:
        result = client.modify_object('groups/group', dummy_dn, {'name': new_name})
        assert result.get('success') is expected_success
    except (AssertionError, BadRequest):
        if expected_success:
            raise
    finally:
        if result.get('success'):
            admin_umc_client.delete_object('groups/group', f'cn={new_name},{ou.group_default_container}')


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', False),
])
def test_group_remove(guardian_setup, property_set_key, expected_success, udm_session, ou):
    """Tests deleting a group."""
    client = guardian_setup
    dummy_dn = udm_session.create_object(
        'groups/group', name=random_username(), position=ou.group_default_container,
    )
    try:
        result = client.delete_object('groups/group', dummy_dn)
        assert result.get('success') is expected_success
    except (AssertionError, BadRequest):
        if expected_success:
            raise


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', False),
])
def test_user_edit(guardian_setup, property_set_key, expected_success, udm_session, ou):
    """Tests modifying a user's details."""
    client = guardian_setup
    dummy_dn = udm_session.create_object(
        'users/user', username=random_username(), lastname=random_username(),
        password='univention', position=ou.user_default_container,
    )
    try:
        result = client.modify_object('users/user', dummy_dn, {'description': 'edited-by-test'})
        assert result.get('success') is expected_success
    except (AssertionError, BadRequest):
        if expected_success:
            raise


@pytest.mark.parametrize('property_set_key, expected_success', [
    ('asterisk', True),
    ('minimal_working', True),
    ('missing_username', True),
    ('missing_lastname', True),
    ('empty', False),
])
def test_user_remove(guardian_setup, property_set_key, expected_success, udm_session, ou):
    """Tests deleting a user."""
    client = guardian_setup
    dummy_dn = udm_session.create_object(
        'users/user', username=random_username(), lastname=random_username(),
        password='univention', position=ou.user_default_container,
    )
    try:
        result = client.delete_object('users/user', dummy_dn)
        assert result.get('success') is expected_success
        # If deletion succeeds, the object is gone. To prevent other tests using this cache
        # from failing, we should remove this entry.

    except (AssertionError, BadRequest):
        if expected_success:
            raise
