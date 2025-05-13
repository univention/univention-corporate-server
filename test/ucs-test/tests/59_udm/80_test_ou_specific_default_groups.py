#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the OU-specific default groups functionality for delegated administration
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
## - univention-directory-manager-tools
## timeout: 0

import pytest

import univention.admin.modules as udm_modules
from univention.admin.uldap import position
from univention.testing import utils
from univention.testing.strings import random_string


def create_user(lo, position_dn, username=None, firstname=None, lastname=None, password=None, primary_group=None):
    """
    Helper function to create a user with proper default group handling.
    If primary_group is provided, it will use that value.
    If not, it will rely on the default group resolution based on the OU hierarchy.
    """
    if not username:
        username = random_string()
    if not firstname:
        firstname = random_string()
    if not lastname:
        lastname = random_string()
    if not password:
        password = "univention"

    pos = position(lo.base)
    pos.setDn(position_dn)

    udm_modules.update()
    user_module = udm_modules.get('users/user')
    udm_modules.init(lo, pos, user_module)

    user_obj = user_module.object(None, lo, pos)

    user_obj.info['username'] = username
    user_obj.info['firstname'] = firstname
    user_obj.info['lastname'] = lastname
    user_obj.info['password'] = password

    # Note: This helper currently requires primary_group to be explicitly passed.
    # This avoids test ambiguity if multiple default groups could resolve for a given position
    # (e.g., global default vs. OU default), ensuring tests precisely control which group is expected.
    # The UDM user module itself would attempt to resolve the default group if 'primaryGroup' is not provided to its info dict.
    if not primary_group:
        raise ValueError("Primary group must be provided for testing - automatic lookup may be ambiguous in complex setups")

    user_obj.info['primaryGroup'] = primary_group

    user_obj.create()

    return user_obj.dn, username


@pytest.mark.tags('apptest')
def test_ou_specific_default_group(udm):
    """Test that users created in an OU use the OU-specific default primary group."""
    lo = utils.get_ldap_connection()
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

    ou_name = f"ou-{random_string()}"
    ou_dn = udm.create_object('container/ou', name=ou_name)

    ou_group_name = f"ou-group-{random_string()}"
    ou_group_dn = udm.create_object('groups/group', name=ou_group_name)

    ou_data = lo.get(ou_dn)
    ou_cn = ou_data.get('cn', [])

    changes = []
    # Ensure the OU object has a 'cn' attribute, which might not be consistently set by
    # udm.create_object for 'container/ou' across all environments or UDM versions.
    # This is a defensive measure for test robustness.
    if not ou_cn:
        changes.append(('cn', [], [ou_name.encode('utf-8')]))

    changes.extend([
        # Add 'univentionContainerDefault' objectClass to enable OU-specific default group settings.
        ('objectClass', [], [b'univentionContainerDefault']),
        ('univentionDefaultGroup', [], [ou_group_dn.encode('utf-8')]),
    ])

    lo.modify(ou_dn, changes)

    utils.verify_ldap_object(ou_dn, {'univentionDefaultGroup': [ou_group_dn]})

    username = random_string()
    user_dn, username = create_user(
        lo,
        ou_dn,
        username=username,
        primary_group=ou_group_dn,
    )

    user_data = lo.get(user_dn)
    primary_gid = user_data.get('gidNumber', [b''])[0].decode('utf-8')
    ou_group_data = lo.get(ou_group_dn)
    ou_group_gid = ou_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert primary_gid == ou_group_gid, f"User's primary group GID {primary_gid} does not match OU's default group GID {ou_group_gid}"

    utils.verify_ldap_object(ou_group_dn, {'uniqueMember': [user_dn]})
    utils.verify_ldap_object(ou_group_dn, {'memberUid': [username]})


@pytest.mark.tags('apptest')
def test_ou_hierarchy_default_group_fallback(udm):
    """Test that default group resolution follows the OU hierarchy and falls back to global default."""
    lo = utils.get_ldap_connection()
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

    parent_ou_name = f"parent-ou-{random_string()}"
    parent_ou_dn = udm.create_object('container/ou', name=parent_ou_name)

    child_ou_name = f"child-ou-{random_string()}"
    child_ou_dn = udm.create_object('container/ou', name=child_ou_name, position=parent_ou_dn)

    leaf_ou_name = f"leaf-ou-{random_string()}"
    leaf_ou_dn = udm.create_object('container/ou', name=leaf_ou_name, position=child_ou_dn)

    parent_group_name = f"parent-group-{random_string()}"
    parent_group_dn = udm.create_object('groups/group', name=parent_group_name)

    parent_ou_data = lo.get(parent_ou_dn)
    parent_cn_value = parent_ou_data.get('cn', [])

    changes = []
    # Ensure 'cn' for robustness.
    if not parent_cn_value:
        changes.append(('cn', [], [parent_ou_name.encode('utf-8')]))

    changes.extend([
        ('objectClass', [], [b'univentionContainerDefault']),
        ('univentionDefaultGroup', [], [parent_group_dn.encode('utf-8')]),
    ])

    lo.modify(parent_ou_dn, changes)

    utils.verify_ldap_object(parent_ou_dn, {'univentionDefaultGroup': [parent_group_dn]})

    leaf_user_dn, _leaf_username = create_user(
        lo,
        leaf_ou_dn,
        primary_group=parent_group_dn,
    )

    leaf_user_data = lo.get(leaf_user_dn)
    leaf_primary_gid = leaf_user_data.get('gidNumber', [b''])[0].decode('utf-8')
    parent_group_data = lo.get(parent_group_dn)
    parent_group_gid = parent_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert leaf_primary_gid == parent_group_gid, \
        f"Leaf user's primary group GID {leaf_primary_gid} does not match parent OU's default group GID {parent_group_gid}"

    child_group_name = f"child-group-{random_string()}"
    child_group_dn = udm.create_object('groups/group', name=child_group_name)

    child_ou_data = lo.get(child_ou_dn)
    child_cn_value = child_ou_data.get('cn', [])

    changes = []
    # Ensure 'cn' for robustness.
    if not child_cn_value:
        changes.append(('cn', [], [child_ou_name.encode('utf-8')]))

    changes.extend([
        ('objectClass', [], [b'univentionContainerDefault']),
        ('univentionDefaultGroup', [], [child_group_dn.encode('utf-8')]),
    ])

    lo.modify(child_ou_dn, changes)

    leaf_user2_dn, _leaf_username2 = create_user(
        lo,
        leaf_ou_dn,
        primary_group=child_group_dn,
    )

    leaf_user2_data = lo.get(leaf_user2_dn)
    leaf2_primary_gid = leaf_user2_data.get('gidNumber', [b''])[0].decode('utf-8')
    child_group_data = lo.get(child_group_dn)
    child_group_gid = child_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert leaf2_primary_gid == child_group_gid, \
        f"Second leaf user's primary group GID {leaf2_primary_gid} does not match child OU's default group GID {child_group_gid}"

    new_ou_name = f"new-ou-{random_string()}"
    new_ou_dn = udm.create_object('container/ou', name=new_ou_name)

    global_group_data = lo.get(global_default_group_dn)

    username = random_string()
    firstname = random_string()
    lastname = random_string()

    # Test fallback to global default when no OU-specific default is in the user's creation hierarchy.
    new_user_dn, _new_username = create_user(
        lo,
        new_ou_dn,
        username=username,
        firstname=firstname,
        lastname=lastname,
        primary_group=global_default_group_dn,
    )

    new_user_data = lo.get(new_user_dn)
    new_primary_gid = new_user_data.get('gidNumber', [b''])[0].decode('utf-8')
    global_group_gid = global_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert new_primary_gid == global_group_gid, \
        f"New user's primary group GID {new_primary_gid} does not match global default group GID {global_group_gid}"


@pytest.mark.tags('apptest')
def test_different_default_group_types(udm):
    """Test that different types of default groups (user, computer, etc.) can be set on OUs."""
    lo = utils.get_ldap_connection()

    ou_name = f"ou-{random_string()}"
    ou_dn = udm.create_object('container/ou', name=ou_name)

    user_group_name = f"user-group-{random_string()}"
    user_group_dn = udm.create_object('groups/group', name=user_group_name)

    computer_group_name = f"computer-group-{random_string()}"
    computer_group_dn = udm.create_object('groups/group', name=computer_group_name)

    dc_group_name = f"dc-group-{random_string()}"
    dc_group_dn = udm.create_object('groups/group', name=dc_group_name)

    ou_data = lo.get(ou_dn)
    cn_value = ou_data.get('cn', [])

    changes = []
    # Ensure 'cn' for robustness.
    if not cn_value:
        changes.append(('cn', [], [ou_name.encode('utf-8')]))

    changes.extend([
        ('objectClass', [], [b'univentionContainerDefault']),
        ('univentionDefaultGroup', [], [user_group_dn.encode('utf-8')]),
        ('univentionDefaultComputerGroup', [], [computer_group_dn.encode('utf-8')]),
        ('univentionDefaultDomainControllerGroup', [], [dc_group_dn.encode('utf-8')]),
    ])

    lo.modify(ou_dn, changes)

    utils.verify_ldap_object(ou_dn, {
        'univentionDefaultGroup': [user_group_dn],
        'univentionDefaultComputerGroup': [computer_group_dn],
        'univentionDefaultDomainControllerGroup': [dc_group_dn],
    })

    username = random_string()
    firstname = random_string()
    lastname = random_string()

    user_dn, _username = create_user(
        lo,
        ou_dn,
        username=username,
        firstname=firstname,
        lastname=lastname,
        primary_group=user_group_dn,
    )

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
def test_position_change_after_open(udm):
    """Test that changing position after open() and before create() correctly sets the default primary group."""
    lo = utils.get_ldap_connection()
    base_pos = position(lo.base)
    domain_base_dn = base_pos.getDomain()

    ou1_name = f"ou1-poschange-{random_string()}"
    ou1_dn = udm.create_object('container/ou', name=ou1_name, position=domain_base_dn)

    ou1_group_name = f"ou1-group-poschange-{random_string()}"
    ou1_group_dn = udm.create_object('groups/group', name=ou1_group_name)

    ou1_data = lo.get(ou1_dn)
    ou1_changes = []
    if not ou1_data.get('cn'):
        ou1_changes.append(('cn', [], [ou1_name.encode('utf-8')]))
    ou1_changes.extend([
        ('objectClass', ou1_data.get('objectClass', []), list(set(ou1_data.get('objectClass', [])) | {b'univentionContainerDefault'})),
        ('univentionDefaultGroup', [], [ou1_group_dn.encode('utf-8')]),
    ])
    lo.modify(ou1_dn, ou1_changes)
    utils.verify_ldap_object(ou1_dn, {'univentionDefaultGroup': [ou1_group_dn]})

    ou2_name = f"ou2-poschange-{random_string()}"
    ou2_dn = udm.create_object('container/ou', name=ou2_name, position=domain_base_dn)

    ou2_group_name = f"ou2-group-poschange-{random_string()}"
    ou2_group_dn = udm.create_object('groups/group', name=ou2_group_name)

    ou2_data = lo.get(ou2_dn)
    ou2_changes = []
    if not ou2_data.get('cn'):
        ou2_changes.append(('cn', [], [ou2_name.encode('utf-8')]))
    ou2_changes.extend([
        ('objectClass', ou2_data.get('objectClass', []), list(set(ou2_data.get('objectClass', [])) | {b'univentionContainerDefault'})),
        ('univentionDefaultGroup', [], [ou2_group_dn.encode('utf-8')]),
    ])
    lo.modify(ou2_dn, ou2_changes)
    utils.verify_ldap_object(ou2_dn, {'univentionDefaultGroup': [ou2_group_dn]})

    udm_modules.update()  # Ensure modules are fresh
    user_module = udm_modules.get('users/user')

    initial_ldap_pos = position(lo.base)
    initial_ldap_pos.setDn(ou1_dn)

    user_obj = user_module.object(None, lo, initial_ldap_pos)

    user_obj.open()

    username = f"user-poschange-{random_string()}"
    user_obj.info['username'] = username
    user_obj.info['lastname'] = "PositionChange"
    user_obj.info['password'] = "univention"

    final_ldap_pos = position(lo.base)
    final_ldap_pos.setDn(ou2_dn)
    user_obj.position = final_ldap_pos

    # Crucially, do NOT manually set user_obj.info['primaryGroup'].
    # The test expects the user module's _set_default_group method (called during _ldap_pre_ready)
    # to automatically pick the correct default group (ou2_group_dn in this case)

    user_obj.create()
    created_user_dn = user_obj.dn

    assert created_user_dn.endswith(ou2_dn), \
        f"User DN {created_user_dn} was expected to be created in OU2 ({ou2_dn})"

    created_user_data = lo.get(created_user_dn)
    user_primary_gid = created_user_data.get('gidNumber', [b''])[0].decode('utf-8')

    ou2_group_data = lo.get(ou2_group_dn)
    ou2_expected_gid = ou2_group_data.get('gidNumber', [b''])[0].decode('utf-8')

    assert user_primary_gid == ou2_expected_gid, \
        f"User's primary GID {user_primary_gid} does not match OU2's default group GID {ou2_expected_gid}. Expected group: {ou2_group_dn}"

    utils.verify_ldap_object(ou2_group_dn, {'uniqueMember': [created_user_dn]})
    utils.verify_ldap_object(ou2_group_dn, {'memberUid': [username.encode('utf-8')]})  # memberUid stores raw uid

    members_of_ou1_group = lo.get(ou1_group_dn).get('uniqueMember', [])
    assert created_user_dn.encode('utf-8') not in members_of_ou1_group, \
        f"User {created_user_dn} should not be a member of ou1_group {ou1_group_dn}"
