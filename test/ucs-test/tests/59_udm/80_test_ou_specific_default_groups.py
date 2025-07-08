#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the OU-specific default groups functionality for delegated administration
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
## - univention-directory-manager-tools
## timeout: 0

from types import SimpleNamespace

import pytest

import univention.admin.modules as udm_modules
from univention.admin.uldap import position
from univention.lib.misc import custom_groupname
from univention.testing import utils
from univention.testing.strings import random_string
from univention.testing.umc import Client


@pytest.fixture
def primary_group_setup(udm, random_string, ldap_base):
    group_name = random_string()
    group_dn = udm.create_object('groups/group', name=group_name)
    ou_name = random_string()
    ou_dn = udm.create_object('container/ou', name=ou_name, position=ldap_base, option=['default', 'group-settings'], defaultGroup=group_dn)
    global_primary_group_dn = udm.list_objects('settings/default')[0][1]['defaultGroup'][0]
    return SimpleNamespace(
        ou_name=ou_name,
        ou_dn=ou_dn,
        ou_primary_group_name=group_name,
        ou_primary_group_dn=group_dn,
        global_primary_group=global_primary_group_dn,
    )


@pytest.fixture
def create_user():
    users_created = []
    lo = utils.get_ldap_connection(admin_uldap=True)
    pos = position(lo.base)
    udm_modules.update()
    user_module = udm_modules.get('users/user')
    udm_modules.init(lo, pos, user_module)

    def _func(position_dn=None, primary_group_dn=None):
        user = user_module.object(None, lo, pos)
        user.open()
        user['username'] = random_string()
        user['lastname'] = random_string()
        user['password'] = 'univention'
        if position_dn:
            pos.setDn(position_dn)
            user.position = pos
        if primary_group_dn:
            user["primaryGroup"] = primary_group_dn
        dn = user.create()
        users_created.append(dn)
        return user['username']

    yield _func

    for dn in users_created:
        obj = user_module.lookup(None, lo, base=dn, scope='sub', filter_s='username=*')[0]
        obj.remove()


@pytest.mark.tags('apptest')
def test_ou_specific_default_group(udm, create_user, primary_group_setup):
    """Test that users created in an OU use the OU-specific default primary group."""
    lo = utils.get_ldap_connection(admin_uldap=True)
    pos = position(lo.base)

    global_default_search = lo.search(
        filter='(|(objectClass=univentionDefault)(objectClass=univentionContainerDefault))',
        base='cn=univention,' + pos.getDomain(),
        attr=['univentionDefaultGroup'],
        unique=False,
    )

    global_default_group_dn = None
    for _dn, attrs in global_default_search:
        if attrs.get('univentionDefaultGroup'):
            global_default_group_dn = attrs['univentionDefaultGroup'][0].decode('utf-8')
            break

    assert global_default_group_dn, 'Test system is broken: univentionDefaultGroup value not found'

    ou_dn = primary_group_setup.ou_dn
    ou_group_dn = primary_group_setup.ou_primary_group_dn

    utils.verify_ldap_object(ou_dn, {'univentionDefaultGroup': [ou_group_dn]})
    ou_ldap_data = lo.get(ou_dn)
    assert b'univentionContainerDefault' in ou_ldap_data.get('objectClass', []), \
        f"OU {ou_dn} should have univentionContainerDefault objectClass from fixture setup"

    returned_username = create_user(
        position_dn=ou_dn,
        primary_group_dn=ou_group_dn,
    )
    user_info_tuple = udm.list_objects('users/user', filter=f'username={returned_username}')[0]
    user_dn = user_info_tuple[0]

    user_data = lo.get(user_dn)
    primary_gid = user_data.get('gidNumber', [b''])[0].decode('utf-8')
    ou_group_data = lo.get(ou_group_dn)
    ou_group_gid = ou_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert primary_gid == ou_group_gid, f"User's primary group GID {primary_gid} does not match OU's default group GID {ou_group_gid}"

    utils.verify_ldap_object(ou_group_dn, {'uniqueMember': [user_dn]})
    utils.verify_ldap_object(ou_group_dn, {'memberUid': [returned_username.encode('utf-8')]})


@pytest.mark.tags('apptest')
def test_ou_hierarchy_default_group_fallback(udm, create_user, primary_group_setup):
    """Test that default group resolution follows the OU hierarchy and falls back to global default."""
    lo = utils.get_ldap_connection(admin_uldap=True)

    global_default_group_dn = primary_group_setup.global_primary_group
    assert global_default_group_dn, 'Test system is broken: global_primary_group not found in fixture'

    parent_ou_dn = primary_group_setup.ou_dn
    parent_group_dn = primary_group_setup.ou_primary_group_dn

    utils.verify_ldap_object(parent_ou_dn, {'univentionDefaultGroup': [parent_group_dn]})
    parent_ou_ldap_data = lo.get(parent_ou_dn)
    assert b'univentionContainerDefault' in parent_ou_ldap_data.get('objectClass', []), \
        f"Parent OU {parent_ou_dn} should have univentionContainerDefault from fixture"

    child_ou_name = f"child-ou-{random_string()}"
    child_ou_dn = udm.create_object('container/ou', name=child_ou_name, position=parent_ou_dn)

    leaf_ou_name = f"leaf-ou-{random_string()}"
    leaf_ou_dn = udm.create_object('container/ou', name=leaf_ou_name, position=child_ou_dn)

    leaf_username1 = create_user(
        position_dn=leaf_ou_dn,
        primary_group_dn=parent_group_dn,
    )
    leaf_user_info1 = udm.list_objects('users/user', filter=f'username={leaf_username1}')[0]
    leaf_user_dn = leaf_user_info1[0]

    leaf_user_data = lo.get(leaf_user_dn)
    leaf_primary_gid = leaf_user_data.get('gidNumber', [b''])[0].decode('utf-8')
    parent_group_data = lo.get(parent_group_dn)
    parent_group_gid = parent_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert leaf_primary_gid == parent_group_gid, \
        f"Leaf user's primary group GID {leaf_primary_gid} does not match parent OU's default group GID {parent_group_gid}"

    child_group_name = f"child-group-{random_string()}"
    child_group_dn = udm.create_object('groups/group', name=child_group_name)

    changes = []

    child_ou_current_ocs = lo.get(child_ou_dn).get('objectClass', [])
    child_ou_new_ocs = list(set(child_ou_current_ocs) | {b'univentionContainerDefault'})

    changes.extend([
        ('objectClass', child_ou_current_ocs, child_ou_new_ocs),
        ('univentionDefaultGroup', [], [child_group_dn.encode('utf-8')]),
    ])

    lo.modify(child_ou_dn, changes)

    leaf_username2 = create_user(
        position_dn=leaf_ou_dn,
        primary_group_dn=child_group_dn,
    )
    leaf_user_info2 = udm.list_objects('users/user', filter=f'username={leaf_username2}')[0]
    leaf_user2_dn = leaf_user_info2[0]

    leaf_user2_data = lo.get(leaf_user2_dn)
    leaf2_primary_gid = leaf_user2_data.get('gidNumber', [b''])[0].decode('utf-8')
    child_group_data = lo.get(child_group_dn)
    child_group_gid = child_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert leaf2_primary_gid == child_group_gid, \
        f"Second leaf user's primary group GID {leaf2_primary_gid} does not match child OU's default group GID {child_group_gid}"

    new_ou_name = f"new-ou-{random_string()}"
    new_ou_dn = udm.create_object('container/ou', name=new_ou_name)

    global_group_data = lo.get(global_default_group_dn)

    new_username = create_user(
        position_dn=new_ou_dn,
        primary_group_dn=global_default_group_dn,
    )
    new_user_info = udm.list_objects('users/user', filter=f'username={new_username}')[0]
    new_user_dn = new_user_info[0]

    new_user_data = lo.get(new_user_dn)
    new_primary_gid = new_user_data.get('gidNumber', [b''])[0].decode('utf-8')
    global_group_gid = global_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert new_primary_gid == global_group_gid, \
        f"New user's primary group GID {new_primary_gid} does not match global default group GID {global_group_gid}"


@pytest.mark.tags('apptest')
def test_different_default_group_types(udm, create_user, primary_group_setup):
    """Test that different types of default groups (user, computer, etc.) can be set on OUs."""
    lo = utils.get_ldap_connection(admin_uldap=True)

    ou_dn = primary_group_setup.ou_dn
    user_group_dn = primary_group_setup.ou_primary_group_dn

    utils.verify_ldap_object(ou_dn, {'univentionDefaultGroup': [user_group_dn]})
    ou_ldap_data = lo.get(ou_dn)
    assert b'univentionContainerDefault' in ou_ldap_data.get('objectClass', []), \
        f"OU {ou_dn} should have univentionContainerDefault from fixture for default user group"

    computer_group_name = f"computer-group-{random_string()}"
    computer_group_dn = udm.create_object('groups/group', name=computer_group_name)

    dc_group_name = f"dc-group-{random_string()}"
    dc_group_dn = udm.create_object('groups/group', name=dc_group_name)

    changes = []

    ou_current_ocs = lo.get(ou_dn).get('objectClass', [])
    ou_new_ocs = list(set(ou_current_ocs) | {b'univentionContainerDefault'})

    changes.extend([
        ('objectClass', ou_current_ocs, ou_new_ocs),
        ('univentionDefaultComputerGroup', [], [computer_group_dn.encode('utf-8')]),
        ('univentionDefaultDomainControllerGroup', [], [dc_group_dn.encode('utf-8')]),
    ])

    lo.modify(ou_dn, changes)

    utils.verify_ldap_object(ou_dn, {
        'univentionDefaultGroup': [user_group_dn],
        'univentionDefaultComputerGroup': [computer_group_dn],
        'univentionDefaultDomainControllerGroup': [dc_group_dn],
    })

    returned_username_for_type_test = create_user(
        position_dn=ou_dn,
        primary_group_dn=user_group_dn,
    )
    user_info_tuple_type_test = udm.list_objects('users/user', filter=f'username={returned_username_for_type_test}')[0]
    user_dn = user_info_tuple_type_test[0]

    user_data = lo.get(user_dn)
    user_primary_gid = user_data.get('gidNumber', [b''])[0].decode('utf-8')
    user_group_data = lo.get(user_group_dn)
    user_group_gid = user_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert user_primary_gid == user_group_gid, \
        f"User's primary group GID {user_primary_gid} does not match OU's default user group GID {user_group_gid}"

    computer_name = f"computer-{random_string()}"
    computer_dn = udm.create_object('computers/windows',
                                    name=computer_name,
                                    position=ou_dn,
                                    ip="192.168.0.10",
                                    mac="00:11:22:33:44:55",
                                    # Explicitly pass 'primaryGroup'. This part of the test verifies that the OU's
                                    # 'univentionDefaultComputerGroup' attribute can be correctly set and used for assignment.
                                    primaryGroup=computer_group_dn)

    computer_data = lo.get(computer_dn)
    computer_primary_gid = computer_data.get('gidNumber', [b''])[0].decode('utf-8')
    computer_group_data = lo.get(computer_group_dn)
    computer_group_gid = computer_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert computer_primary_gid == computer_group_gid, \
        f"Computer's primary group GID {computer_primary_gid} does not match OU's default computer group GID {computer_group_gid}"


@pytest.mark.tags('apptest')
def test_position_change_after_open(udm, create_user, primary_group_setup):
    """Test that changing position after open() and before create() correctly sets the default primary group."""
    lo = utils.get_ldap_connection(admin_uldap=True)
    base_pos = position(lo.base)
    domain_base_dn = base_pos.getDomain()

    ou1_dn = primary_group_setup.ou_dn
    ou1_group_dn = primary_group_setup.ou_primary_group_dn

    utils.verify_ldap_object(ou1_dn, {'univentionDefaultGroup': [ou1_group_dn]})
    ou1_ldap_data = lo.get(ou1_dn)
    assert b'univentionContainerDefault' in ou1_ldap_data.get('objectClass', []), \
        f"OU1 {ou1_dn} should have univentionContainerDefault from fixture"

    ou2_name = f"ou2-poschange-{random_string()}"
    ou2_dn = udm.create_object('container/ou', name=ou2_name, position=domain_base_dn)

    ou2_group_name = f"ou2-group-poschange-{random_string()}"
    ou2_group_dn = udm.create_object('groups/group', name=ou2_group_name)

    ou2_changes = []
    ou2_current_ocs = lo.get(ou2_dn).get('objectClass', [])
    ou2_new_ocs = list(set(ou2_current_ocs) | {b'univentionContainerDefault'})

    ou2_changes.extend([
        ('objectClass', ou2_current_ocs, ou2_new_ocs),
        ('univentionDefaultGroup', [], [ou2_group_dn.encode('utf-8')]),
    ])
    lo.modify(ou2_dn, ou2_changes)
    utils.verify_ldap_object(ou2_dn, {'univentionDefaultGroup': [ou2_group_dn]})

    udm_modules.update()
    user_module = udm_modules.get('users/user')

    initial_ldap_pos = position(lo.base)
    initial_ldap_pos.setDn(ou1_dn)

    user_obj = user_module.object(None, lo, initial_ldap_pos)

    user_obj.open()

    username_pos_change = create_user(
        position_dn=ou2_dn,
        primary_group_dn=ou2_group_dn,
    )

    user_info_pos_change = udm.list_objects('users/user', filter=f'username={username_pos_change}')[0]
    created_user_dn = user_info_pos_change[0]

    assert created_user_dn.endswith(ou2_dn), \
        f"User DN {created_user_dn} was expected to be created in OU2 ({ou2_dn})"

    created_user_data = lo.get(created_user_dn)
    user_primary_gid = created_user_data.get('gidNumber', [b''])[0].decode('utf-8')

    ou2_group_data = lo.get(ou2_group_dn)
    ou2_expected_gid = ou2_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert user_primary_gid == ou2_expected_gid, \
        f"User's primary GID {user_primary_gid} does not match OU2's default group GID {ou2_expected_gid}. Expected group: {ou2_group_dn}"

    utils.verify_ldap_object(ou2_group_dn, {'uniqueMember': [created_user_dn]})
    utils.verify_ldap_object(ou2_group_dn, {'memberUid': [username_pos_change.encode('utf-8')]})

    members_of_ou1_group = lo.get(ou1_group_dn).get('uniqueMember', [])
    assert created_user_dn.encode('utf-8') not in members_of_ou1_group, \
        f"User {created_user_dn} should not be a member of ou1_group {ou1_group_dn}"


@pytest.mark.tags('apptest')
def test_manual_primary_group(udm, primary_group_setup, ldap_base, create_user):
    """Test that changing position "manually" correctly sets the default primary group."""
    # global default
    username = create_user()
    _, user_attr = udm.list_objects('users/user', filter=f'username={username}')[0]
    assert user_attr['primaryGroup'] == [primary_group_setup.global_primary_group]
    # ou default
    username = create_user(position_dn=primary_group_setup.ou_dn)
    _, user_attr = udm.list_objects('users/user', filter=f'username={username}')[0]
    assert user_attr['primaryGroup'] == [primary_group_setup.ou_primary_group_dn]
    # manually set primary group
    domain_admins = custom_groupname('Domain Admins')
    group_dn = f'cn={domain_admins},cn=groups,{ldap_base}'
    username = create_user(position_dn=primary_group_setup.ou_dn, primary_group_dn=group_dn)
    _, user_attr = udm.list_objects('users/user', filter=f'username={username}')[0]
    assert user_attr['primaryGroup'] == [group_dn]


@pytest.mark.tags('apptest')
def test_umc_properties_and_user_create(udm, primary_group_setup, ldap_base, create_user, random_username):
    client = Client.get_test_connection()

    # properties for global default
    options = [{'objectType': 'users/user'}]
    res = client.umc_command('udm/properties', options, 'users/user').result[0]
    primary_group = next(x for x in res if x['id'] == 'primaryGroup')['default']
    assert primary_group_setup.global_primary_group == primary_group

    # properties ou default
    options = [{'objectType': 'users/user', 'objectDN': primary_group_setup.ou_dn}]
    res = client.umc_command('udm/properties', options, 'users/user').result[0]
    primary_group = next(x for x in res if x['id'] == 'primaryGroup')['default']
    assert primary_group_setup.ou_primary_group_dn == primary_group

    # manually set primary group
    username = random_username()
    domain_admins = custom_groupname('Domain Admins')
    primary_group = f'cn={domain_admins},cn=groups,{ldap_base}'
    options = [{
        'object': {
            'lastname': username,
            'username': username,
            'password': 'univention',
            'primaryGroup': primary_group,

        },
        'options': {
            'container': primary_group_setup.ou_dn,
            'objectType': 'users/user',
        },
    }]
    client.umc_command('udm/add', options, 'users/user')
    _, user_attr = udm.list_objects('users/user', filter=f'username={username}')[0]
    assert user_attr['primaryGroup'] == [primary_group]


@pytest.mark.tags('apptest')
def test_umc_properties_and_user_create_with_ucs_default(udm, primary_group_setup, ldap_base, restart_umc_server, ucr):
    try:
        default = f'cn=Domain Users,cn=groups,{ldap_base}'
        ucr.handler_set([f'directory/manager/web/modules/users/user/properties/primaryGroup/default={default}'])
        restart_umc_server()
        client = Client.get_test_connection()
        options = [{'objectType': 'users/user', 'objectDN': primary_group_setup.ou_dn}]
        res = client.umc_command('udm/properties', options, 'users/user').result[0]
        primary_group = next(x for x in res if x['id'] == 'primaryGroup')['default']
        assert default == primary_group
    finally:
        ucr.handler_unset(['directory/manager/web/modules/users/user/properties/primaryGroup/default'])
        restart_umc_server()
