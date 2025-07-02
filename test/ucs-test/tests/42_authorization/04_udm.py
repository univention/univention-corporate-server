#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check UDM library delegated administration (authorization)
## bugs: []
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

from dataclasses import dataclass

import pytest

import univention.admin.authorization as udm_auth
from univention.admin import modules
from univention.admin.objects import get_object
from univention.admin.uexceptions import noObject, permissionDenied
from univention.admin.uldap import access, getAdminConnection, position
from univention.config_registry import ucr as _ucr


check_delegation = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='directory/manager/web/delegative-administration/enabled not activated')
LDAP_BASE = _ucr.get('ldap/base')
DEFAULT_USERS_CN_DN = f"cn=users,{LDAP_BASE}"
TEST_PASSWORD = "univention"


@dataclass
class OUConfig:
    name: str
    dn: str
    users_dn: str
    groups_dn: str
    admin_username: str
    admin_dn: str
    admin_password: str = TEST_PASSWORD


OU1 = OUConfig(
    name="ou1",
    dn=f"ou=ou1,{LDAP_BASE}",
    users_dn=f"cn=users,ou=ou1,{LDAP_BASE}",
    groups_dn=f"cn=groups,ou=ou1,{LDAP_BASE}",
    admin_username="ou1-admin",
    admin_dn=f"uid=ou1-admin,{DEFAULT_USERS_CN_DN}",
)

OU2 = OUConfig(
    name="ou2",
    dn=f"ou=ou2,{LDAP_BASE}",
    users_dn=f"cn=users,ou=ou2,{LDAP_BASE}",
    groups_dn=f"cn=groups,ou=ou2,{LDAP_BASE}",
    admin_username="ou2-admin",
    admin_dn=f"uid=ou2-admin,{DEFAULT_USERS_CN_DN}",
)


@pytest.fixture
def authorization_enabled():
    """Enable authorization for the test function."""
    lo_admin = getAdminConnection()[0]
    udm_auth.Authorization.enable(lambda: lo_admin)
    modules.update()


@pytest.fixture
def ou_admin_connection(authorization_enabled):
    """Create an OU admin connection."""
    def _create_connection(admin_dn: str, admin_password: str):
        lo = access(
            host=_ucr.get('ldap/master'),
            port=int(_ucr.get('ldap/master/port', '7389')),
            base=LDAP_BASE,
            binddn=admin_dn,
            bindpw=admin_password,
            start_tls=2,
        )
        if not lo:
            pytest.fail(f"Failed to create connection for {admin_dn}")

        authorized_connection = udm_auth.Authorization.inject_ldap_connection(lo)
        return authorized_connection

    connections = []

    def _factory(admin_dn: str, admin_password: str):
        conn = _create_connection(admin_dn, admin_password)
        connections.append(conn)
        return conn

    yield _factory

    for conn in connections:
        try:
            conn.unbind()
        except Exception:
            pass


USER_CREATION_CASES = [
    pytest.param(OU1.admin_dn, OU1.admin_password, OU1.users_dn, True, id="ou1admin_in_ou1_should_succeed"),
    pytest.param(OU1.admin_dn, OU1.admin_password, OU2.users_dn, False, id="ou1admin_in_ou2_should_fail"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU2.users_dn, True, id="ou2admin_in_ou2_should_succeed"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU1.users_dn, False, id="ou2admin_in_ou1_should_fail"),
]


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,target_container,expect_success", USER_CREATION_CASES)
def test_ou_admin_user_creation_permissions(
    ou_admin_connection,
    random_username,
    admin_dn: str,
    admin_password: str,
    target_container: str,
    expect_success: bool,
):
    """Tests if an OU admin can or cannot create a new user in a specific container."""
    username = f"testuser_{random_username()[:8]}"

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    users_module = modules.get('users/user')
    modules.init(ou_admin_conn, position_obj, users_module)

    user_obj = users_module.object(None, ou_admin_conn, position_obj)
    user_obj.open()

    position_obj.setDn(target_container)
    user_obj.position = position_obj
    user_obj["username"] = username
    user_obj["lastname"] = f"TestUser_{random_username()[:6]}"
    user_obj["password"] = TEST_PASSWORD

    if expect_success:
        created_user_dn = user_obj.create()
        assert created_user_dn is not None

        expected_dn = f"uid={username},{target_container}"
        assert created_user_dn.lower() == expected_dn.lower()
    else:
        with pytest.raises(permissionDenied):
            user_obj.create()


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,user_container,expect_success", USER_CREATION_CASES)
def test_ou_admin_user_read_permissions(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    user_container: str,
    expect_success: bool,
):
    """Tests if an OU admin can or cannot read a user in a specific container."""
    username = f"readtest_{random_username()[:8]}"

    udm.create_object(
        'users/user',
        position=user_container,
        username=username,
        lastname=f"TestUser_{username}",
        password=TEST_PASSWORD,
    )

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    users_module = modules.get('users/user')
    modules.init(ou_admin_conn, position_obj, users_module)

    if expect_success:
        users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=user_container)
        assert users[0]['username'] == username
    else:
        with pytest.raises(noObject):
            users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=user_container)


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,user_container,expect_success", USER_CREATION_CASES)
def test_ou_admin_user_modification_permissions(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    user_container: str,
    expect_success: bool,
):
    """Tests if an OU admin can or cannot modify a user in a specific container."""
    username = f"modtest_{random_username()[:8]}"
    initial_description = "Initial description"
    modified_description = "Modified description"

    test_user_dn = udm.create_object(
        'users/user',
        position=user_container,
        username=username,
        lastname=f"TestUser_{username}",
        password=TEST_PASSWORD,
        description=initial_description,
    )

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    users_module = modules.get('users/user')
    modules.init(ou_admin_conn, position_obj, users_module)

    if expect_success:
        users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=user_container)
        assert len(users) == 1
        user_obj = users[0]

        user_obj.open()
        user_obj['description'] = modified_description
        user_obj.modify()

        user_obj.open()
        assert user_obj['description'] == modified_description
    else:
        user_obj = get_object(ou_admin_conn, test_user_dn)

        user_obj.open()
        user_obj['description'] = modified_description

        with pytest.raises(noObject):
            user_obj.modify()


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,user_container,expect_success", USER_CREATION_CASES)
def test_ou_admin_user_deletion_permissions(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    user_container: str,
    expect_success: bool,
):
    """Tests if an OU admin can or cannot delete a user in a specific container."""
    username = f"deltest_{random_username()[:8]}"
    test_user_dn = udm.create_object(
        'users/user',
        position=user_container,
        username=username,
        lastname=f"TestUser_{username}",
        password=TEST_PASSWORD,
    )

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    users_module = modules.get('users/user')
    modules.init(ou_admin_conn, position_obj, users_module)

    if expect_success:
        users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=user_container)
        assert len(users) == 1
        user_obj = users[0]

        user_obj.open()
        user_obj.remove()

        users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=user_container)
        assert len(users) == 0
    else:
        user_obj = get_object(ou_admin_conn, test_user_dn)
        user_obj.open()

        with pytest.raises(noObject):
            user_obj.remove()


USER_MOVE_CASES = [
    pytest.param(
        OU1.admin_dn, OU1.admin_password, OU1.users_dn,
        f"cn=movedusers_{{random_suffix}},{OU1.dn}", True, OU1.dn,
        id="ou1admin_move_within_ou1_succeeds",
    ),
    pytest.param(
        OU1.admin_dn, OU1.admin_password, OU1.users_dn,
        OU2.users_dn, False, None,
        id="ou1admin_move_to_ou2_fails",
    ),
    pytest.param(
        OU2.admin_dn, OU2.admin_password, OU2.users_dn,
        f"cn=movedusers_{{random_suffix}},{OU2.dn}", True, OU2.dn,
        id="ou2admin_move_within_ou2_succeeds",
    ),
    pytest.param(
        OU2.admin_dn, OU2.admin_password, OU2.users_dn,
        OU1.users_dn, False, None,
        id="ou2admin_move_to_ou1_fails",
    ),
]


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,initial_container,target_container_template,expect_success,ou_dn", USER_MOVE_CASES)
def test_ou_admin_user_move_permissions(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    initial_container: str,
    target_container_template: str,
    expect_success: bool,
    ou_dn: str,
):
    """Tests if an OU admin can or cannot move a user between containers."""
    username = f"movetest_{random_username()[:8]}"
    random_suffix = random_username()[:4]
    target_container = target_container_template.format(random_suffix=random_suffix)
    created_sub_container = None

    test_user_dn = udm.create_object(
        'users/user',
        position=initial_container,
        username=username,
        lastname=f"TestUser_{username}",
        password=TEST_PASSWORD,
    )

    if expect_success and ou_dn:
        sub_container_name = f"movedusers_{random_suffix}"
        created_sub_container = udm.create_object(
            'container/cn',
            position=ou_dn,
            name=sub_container_name,
        )

    try:
        ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

        position_obj = position(ou_admin_conn.base)
        users_module = modules.get('users/user')
        modules.init(ou_admin_conn, position_obj, users_module)

        if expect_success:
            users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=initial_container)
            assert len(users) == 1
            user_obj = users[0]

            user_obj.open()
            new_dn = user_obj.move(f"uid={username},{target_container}")

            assert new_dn.lower() == f"uid={username},{target_container}".lower()

            original_users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=initial_container)
            assert len(original_users) == 0

            moved_users = users_module.lookup(None, ou_admin_conn, f"(uid={username})", base=target_container)
            assert len(moved_users) == 1
        else:
            user_obj = get_object(ou_admin_conn, test_user_dn)
            user_obj.open()

            with pytest.raises(permissionDenied):
                user_obj.move(f"uid={username},{target_container}")

    finally:
        if created_sub_container:
            try:
                udm.remove_object('container/cn', dn=created_sub_container, options={'recursive': True})
            except Exception:
                pass


GUARDIAN_ROLES_SECURITY_CASES = [
    pytest.param(OU1.admin_dn, OU1.admin_password, OU1.users_dn, "create", id="ou1admin_create_user_guardian_roles"),
    pytest.param(OU1.admin_dn, OU1.admin_password, OU1.users_dn, "modify", id="ou1admin_modify_user_guardian_roles"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU2.users_dn, "create", id="ou2admin_create_user_guardian_roles"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU2.users_dn, "modify", id="ou2admin_modify_user_guardian_roles"),
]


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,container_dn,operation", GUARDIAN_ROLES_SECURITY_CASES)
def test_ou_admin_cannot_set_guardian_roles_on_users(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    container_dn: str,
    operation: str,
):
    """Tests that OU admins cannot set guardianRoles on users."""
    username = f"grdtest_{operation}_{random_username()[:6]}"
    privileged_role = ["umc:udm:domainadmin"]

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    users_module = modules.get('users/user')
    modules.init(ou_admin_conn, position_obj, users_module)

    if operation == "create":
        # Test: OU admin attempts to create user with guardian roles
        user_obj = users_module.object(None, ou_admin_conn, position_obj)
        user_obj.open()
        position_obj.setDn(container_dn)
        user_obj.position = position_obj
        user_obj["username"] = username
        user_obj["lastname"] = f"GuardianTest{operation.capitalize()}"
        user_obj["password"] = TEST_PASSWORD
        user_obj["guardianRoles"] = privileged_role
        with pytest.raises(permissionDenied):
            user_obj.create()
    elif operation == "modify":
        # Test: OU admin attempts to modify existing user to add guardian roles
        created_user_dn = udm.create_object(
            'users/user',
            position=container_dn,
            username=username,
            lastname=f"TestUser_{username}",
            password=TEST_PASSWORD,
        )
        user_obj = get_object(ou_admin_conn, created_user_dn)
        user_obj.open()
        user_obj["guardianRoles"] = privileged_role
        with pytest.raises(permissionDenied):
            user_obj.modify()


GUARDIAN_MEMBER_ROLES_SECURITY_CASES = [
    pytest.param(OU1.admin_dn, OU1.admin_password, OU1.groups_dn, "create", id="ou1admin_create_group_guardian_member_roles"),
    pytest.param(OU1.admin_dn, OU1.admin_password, OU1.groups_dn, "modify", id="ou1admin_modify_group_guardian_member_roles"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU2.groups_dn, "create", id="ou2admin_create_group_guardian_member_roles"),
    pytest.param(OU2.admin_dn, OU2.admin_password, OU2.groups_dn, "modify", id="ou2admin_modify_group_guardian_member_roles"),
]


@check_delegation
@pytest.mark.parametrize("admin_dn,admin_password,container_dn,operation", GUARDIAN_MEMBER_ROLES_SECURITY_CASES)
def test_ou_admin_cannot_set_guardian_member_roles_on_groups(
    ou_admin_connection,
    udm,
    random_username,
    admin_dn: str,
    admin_password: str,
    container_dn: str,
    operation: str,
):
    """Tests that OU admins cannot set guardianMemberRoles on groups."""
    group_name = f"grdgrp_{operation}_{random_username()[:6]}"
    privileged_role = ["umc:udm:domainadmin"]

    ou_admin_conn = ou_admin_connection(admin_dn, admin_password)

    position_obj = position(ou_admin_conn.base)
    groups_module = modules.get('groups/group')
    modules.init(ou_admin_conn, position_obj, groups_module)

    if operation == "create":
        # Test: OU admin attempts to create group with guardian member roles
        group_obj = groups_module.object(None, ou_admin_conn, position_obj)
        group_obj.open()
        position_obj.setDn(container_dn)
        group_obj.position = position_obj
        group_obj["name"] = group_name
        group_obj["guardianMemberRoles"] = privileged_role
        with pytest.raises(permissionDenied):
            group_obj.create()

    elif operation == "modify":
        # Test: OU admin attempts to modify existing group to add guardian member roles
        created_group_dn = udm.create_object(
            'groups/group',
            position=container_dn,
            name=group_name,
        )

        group_obj = get_object(ou_admin_conn, created_group_dn)
        group_obj.open()
        group_obj["guardianMemberRoles"] = privileged_role

        with pytest.raises(permissionDenied):
            group_obj.modify()

        udm.remove_object('groups/group', dn=created_group_dn)
