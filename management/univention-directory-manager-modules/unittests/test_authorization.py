# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
import sys
# import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


sys.path.insert(0, os.path.abspath("../modules"))
sys.modules["univention.admin.uexceptions"] = MagicMock()
sys.modules["unidecode"] = MagicMock()
sys.modules["univention.admin.localization"] = MagicMock()
sys.modules["univention.admin.uexceptions"] = MagicMock()
sys.modules["univention.config_registry"] = MagicMock()
sys.modules["univention.logging"] = MagicMock()
sys.modules["univention.admin._ucr"] = MagicMock()
sys.modules["ldap"] = MagicMock()
sys.modules["ldap.filter"] = MagicMock()
# hook, mapping, modules, objects, syntax
sys.modules["univention.admin.hook"] = MagicMock()
sys.modules["univention.admin.mapping"] = MagicMock()
sys.modules["univention.admin.modules"] = MagicMock()
sys.modules["univention.admin.objects"] = MagicMock()
sys.modules["univention.admin.syntax"] = MagicMock()
sys.modules["univention.admin.handlers"] = MagicMock()


def parentDn(dn):
    idx = dn.find(',')
    return dn[idx + 1:]


sys.modules["univention.uldap"] = MagicMock()
sys.modules["univention.uldap"].parentDn = parentDn
try:
    import univention.admin.authorization as auth
    from univention.admin.authorization import (
        Authorization, _check_condition, _check_permission_action, _check_permissions, _check_permissions_create,
        _check_permissions_delete, _check_permissions_modify, _check_permissions_read, _check_scope_base,
        _check_scope_subtree, _get_attrs_from_permissions, _get_cap_priority, _get_capabilities,
        _get_readable_attrs_from_permissions, _get_writable_attrs_from_permissions, _obj2dn, _obj2module, _obj2position,
    )
except ImportError:
    raise

Authorization.enable(MagicMock())


def mock_fun(return_value):
    def wrapper(*args, **kwargs):
        return return_value
    return wrapper


def get_default_roles():
    roles_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), "umc-udm-roles.json")
    with open(roles_json) as roles:
        return json.load(roles)


def mock_obj(obj_dict: dict):
    obj = SimpleNamespace(**obj_dict)
    if "id" in obj_dict:
        obj.dn = obj_dict["id"]
    if "module_name" in obj_dict:
        obj.module = obj_dict["module_name"]
    if "position" in obj_dict:
        obj.position = MagicMock()
        obj.position.getDn.return_value = obj_dict["position"]
    obj.diff = lambda: obj_dict.get("diff", [])
    return obj


class NoTestUDMPermission:

    def test_check_all_authorization_methods_have_a_test(self):
        """Check if all methods in the authorization module have a test method."""
        function_type = type(mock_fun)
        not_tested = []
        skip_methods = ["parentDn"]
        for method in dir(auth):
            if method in skip_methods:
                continue
            if type(getattr(auth, method)) is function_type:
                method = method.removeprefix("_")
                if not hasattr(self, f"test_{method}"):
                    not_tested.append(method)
        assert not not_tested, f"Following methods are not tested: {not_tested}"

    def test_obj2dn(self):
        obj = SimpleNamespace(dn="cn=test,dc=example,dc=com")
        assert _obj2dn(obj) == "cn=test,dc=example,dc=com"
        assert _obj2dn({"id": "cn=test,dc=example,dc=com"}) == "cn=test,dc=example,dc=com"
        assert _obj2dn("cn=test,dc=example,dc=com") == "cn=test,dc=example,dc=com"
        with pytest.raises(ValueError):
            _obj2dn({})

    def test_obj2position(self):
        position = MagicMock()
        position.getDn.return_value = "cn=users,dc=example,dc=com"
        obj = SimpleNamespace(position=position)
        assert _obj2position(obj) == "cn=users,dc=example,dc=com"

        assert _obj2position("cn=test,dc=example,dc=com") == "dc=example,dc=com"

    def test_obj2module(self):
        obj = SimpleNamespace(module="users/user")
        assert _obj2module(obj) == "users/user"
        assert _obj2module({"module_name": "groups/group"}) == "groups/group"

    @pytest.mark.parametrize("actor_roles,expected", [
        ({"test_role": []}, [{'condition': {'position': '*', 'contexts': []}}]),
        ({"test_role2": []}, [{'condition': {'position': '$CONTEXT', 'contexts': []}}]),
        ({"test_role3": []}, [{'condition': {'position': 'cn=group,dc=example,dc=com', 'contexts': []}}]),
        ({"test_role": [], "test_role2": []}, [{'condition': {'position': '*', 'contexts': []}}, {'condition': {'position': '$CONTEXT', 'contexts': []}}]),
        ({"test_role": [], "test_role3": []}, [{'condition': {'position': '*', 'contexts': []}}, {'condition': {'position': 'cn=group,dc=example,dc=com', 'contexts': []}}]),
        ({"test_role4": []}, []),
    ])
    @patch("univention.admin.authorization.ldap_base", "dc=example,dc=com")
    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}}], "test_role2": [{"condition": {"position": "$CONTEXT"}}], "test_role3": [{"condition": {"position": "cn=group"}}]})
    def test_get_capabilities(self, actor_roles, expected):
        assert _get_capabilities(actor_roles) == expected

    @pytest.mark.parametrize("target_position, condition, expected", [
        ("cn=users,dc=example,dc=com", {"condition": {"position": "*"}}, 3),
        ("cn=users,dc=example,dc=com", {"condition": {"position": "$CONTEXT"}}, 2),
        ("cn=users,dc=example,dc=com", {"condition": {"position": "cn=users"}}, 1),
        ("cn=users,dc=example,dc=com", {"condition": {"position": "cn=users,dc=example,dc=com"}}, None),
        ("cn=users,dc=example,dc=com", {"condition": {"position": "dc=example,dc=com"}}, None),
        ("cn=users,ou=ou1,dc=example,dc=com", {"condition": {"position": "dc=example,dc=com"}}, None),
    ])
    def test_get_cap_priority(self, target_position, condition, expected):
        if expected is None:
            expected = - len(condition["condition"]["position"])
        assert _get_cap_priority(target_position)(condition) == expected

    @patch("univention.admin.authorization.ldap_base", "dc=example,dc=com")
    def test_sort_cap(self):
        target_position = "cn=users,cn=outest,dc=example,dc=com"
        test = {
            "test_role": [
                {
                    "condition": {
                        "position": "cn=outest",
                        "scope": "subtree",
                    },
                    "permissions": {
                        "*": {
                            "attributes": {
                                "*": {"access": "read"},
                            },
                        },
                    },
                },
                {
                    "condition": {
                        "position": "cn=users,cn=outest",
                        "scope": "subtree",
                    },
                    "permissions": {
                        "*": {
                            "attributes": {
                                "username": {"access": "write"},
                                "last_name": {"access": "read"},
                            },
                        },
                    },
                },
            ],
        }
        with patch("univention.admin.authorization.ROLES", test):
            caps = _get_capabilities({"test_role": []})
            caps.sort(key=_get_cap_priority(target_position))
            assert [cap["condition"]["position"] for cap in caps] == ["cn=users,cn=outest,dc=example,dc=com", "cn=outest,dc=example,dc=com"]

    @pytest.mark.parametrize("position, condition, expected", [
        ("cn=users,dc=example,dc=com", {"position": "cn=users,dc=example,dc=com"}, True),
        ("cn=users,dc=example,dc=com", {"position": "cn=other,dc=example,dc=com"}, False),
        ("cn=users,dc=example,dc=com", {"position": "*"}, True),
        ("cn=users,dc=example,dc=com", {"position": "$CONTEXT", "contexts": ["cn=users,dc=example,dc=com"]}, True),
        ("cn=users,dc=example,dc=com", {"position": "$CONTEXT", "contexts": ["cn=other,dc=example,dc=com"]}, False),
        ("cn=users,dc=example,dc=com", {"position": "$CONTEXT", "contexts": ["cn=other,dc=example,dc=com", "cn=users,dc=example,dc=com"]}, True),
    ])
    def test_check_condition(self, position, condition, expected):
        assert _check_condition(position, condition) == expected

    @pytest.mark.parametrize("module_name, permissions, expected", [
        ("users/user", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (['email'], ['username'], [])),
        ("groups/group", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, ([], [], [])),
        ("users/user", {"*": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (['email'], ['username'], [])),
        ("users/user", {"users/user": {"attributes": {"*": {"access": "read"}}}}, ([], ["*"], [])),
        ("groups/group", {"users/user": {"attributes": {"*": {"access": "read"}}}}, ([], [], [])),
    ])
    def test_get_attrs_from_permissions(self, module_name, permissions, expected):
        assert _get_attrs_from_permissions(module_name, permissions) == expected

    @pytest.mark.parametrize("module_name, permissions, expected", [
        ("users/user", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (["username", "email"], [])),
        ("groups/group", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, ([], [])),
        ("users/user", {"*": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (["username", "email"], [])),
        ("users/user", {"users/user": {"attributes": {"*": {"access": "read"}}}}, (["*"], [])),
        ("groups/group", {"users/user": {"attributes": {"*": {"access": "read"}}}}, ([], [])),
        ("users/user", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}, "description": {"access": "none"}}}}, (["username", "email"], ["description"])),
    ])
    def test_get_readable_attrs_from_permissions(self, module_name, permissions, expected):
        readable, non_readable = _get_readable_attrs_from_permissions(module_name, permissions)
        readable_expected, non_readable_expected = expected
        assert set(readable) == set(readable_expected)
        assert set(non_readable) == set(non_readable_expected)

    @pytest.mark.parametrize("module_name, permissions, expected", [
        ("users/user", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (["email"], ["username"])),
        ("groups/group", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, ([], [])),
        ("users/user", {"*": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}}}}, (["email"], ["username"])),
        ("users/user", {"users/user": {"attributes": {"*": {"access": "write"}}}}, (["*"], [])),
        ("groups/group", {"users/user": {"attributes": {"*": {"access": "write"}}}}, ([], [])),
        ("users/user", {"users/user": {"attributes": {"username": {"access": "read"}, "email": {"access": "write"}, "description": {"access": "none"}}}}, (["email"], ["description", "username"])),
    ])
    def test_get_writable_attrs_from_permissions(self, module_name, permissions, expected):
        writable, non_writable = _get_writable_attrs_from_permissions(module_name, permissions)
        writable_expected, non_writable_expected = expected
        assert set(writable) == set(writable_expected)
        assert set(non_writable) == set(non_writable_expected)

    @pytest.mark.parametrize("obj, cap, action, expected", [
        ({"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": True}}}], "create", True),
        ({"id": "cn=test,dc=example,dc=com", "module_name": "groups/group"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": True}}}], "create", False),
        ({"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": False}}}], "create", False),
        ({"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": True}}}], "delete", False),
        ({"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"delete": True}}}], "delete", True),
        ({"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, [{"condition": {"position": "*"}, "permissions": {"users/user": {"delete": False}}}], "delete", False),
    ])
    def test_check_permissions(self, obj, cap, action, expected):
        assert _check_permissions(obj, cap, action) == expected

    @pytest.mark.parametrize("objs, caps, expected", [
        ([{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}], [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"*": {"access": "read"}}}}}], [{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}]),
        ([{"id": "cn=test,dc=example,dc=com", "module_name": "groups/group"}], [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"*": {"access": "read"}}}}}], []),
        ([{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, {"id": "cn=test2,dc=example,dc=com", "module_name": "groups/group"}], [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"*": {"access": "read"}}}}}], [{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}]),
        ([{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, {"id": "cn=test2,dc=example,dc=com", "module_name": "groups/group"}], [{"condition": {"position": "*"}, "permissions": {"*": {"attributes": {"*": {"access": "read"}}}}}], [{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, {"id": "cn=test2,dc=example,dc=com", "module_name": "groups/group"}]),
    ])
    def test_check_permissions_read(self, objs, caps, expected):
        assert _check_permissions_read(objs, caps) == expected

    @pytest.mark.parametrize("dn, condition_positions, expected", [
        ("ou=ou1,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], True),
        ("ou=ou2,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], True),
        ("cn=users,ou=ou1,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], False),
        ("cn=groups,ou=ou2,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], False),
    ])
    def test_check_scope_base(self, dn, condition_positions, expected):
        assert _check_scope_base(dn, condition_positions) == expected

    @pytest.mark.parametrize("dn, condition_positions, expected", [
        ("cn=users,ou=ou1,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], True),
        ("cn=users,ou=ou2,dc=example,dc=com", ["ou=ou1,dc=example,dc=com", "ou=ou2,dc=example,dc=com"], True),
        ("cn=groups,ou=ou1,dc=example,dc=com", ["ou=ou2,dc=example,dc=com"], False),
        ("cn=groups,ou=ou2,dc=example,dc=com", ["ou=ou1,dc=example,dc=com"], False),
    ])
    def test_check_scope_subtree(self, dn, condition_positions, expected):
        assert _check_scope_subtree(dn, condition_positions) == expected

    @pytest.mark.parametrize("module_name, action, permissions, expected", [
        ("users/user", "create", {"users/user": {"create": True}}, True),
        ("users/user", "delete", {"*": {"delete": False}}, False),
        ("users/user", "create", {"*": {"create": True}, "users/user": {"create": False}}, False),
        ("users/user", "create", {"*": {"create": True}, "users/user": {"create": True}}, True),
        ("users/user", "create", {"*": {"create": False}, "users/user": {"create": True}}, True),
    ])
    def test_check_permission_action(self, module_name, action, permissions, expected):
        assert _check_permission_action(module_name, action, permissions) == expected

    @pytest.mark.parametrize("module_name, expected", [
        ("users/user", True),
        ("groups/group", False),
    ])
    def test_check_permissions_create(self, module_name, expected):
        caps = [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": True}}}]
        obj = {"id": "cn=test,dc=example,dc=com", "module_name": module_name}
        assert _check_permissions_create(obj, caps) == expected

    @pytest.mark.parametrize("module_name, expected", [
        ("users/user", True),
        ("groups/group", False),
    ])
    def test_check_permissions_delete(self, module_name, expected):
        caps = [{"condition": {"position": "*"}, "permissions": {"users/user": {"delete": True}}}]
        obj = {"id": "cn=test,dc=example,dc=com", "module_name": module_name}
        assert _check_permissions_delete(obj, caps) == expected

    @pytest.mark.parametrize("module_name, expected", [
        ("users/user", True),
        ("groups/group", False),
    ])
    def test_check_permissions_modify(self, module_name, expected):
        caps = [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"*": {"access": "write"}}}}}]
        obj = mock_obj({"id": "cn=test,dc=example,dc=com", "module_name": module_name, "diff": [("description", None, "new_description")]})
        assert _check_permissions_modify(obj, caps) == expected

    def test_check_permissions_modify_not_allowed(self):
        caps = [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"*": {"access": "write"}, "guardianRoles": {"access": "read"}}}}}]
        obj = mock_obj({"id": "cn=test,dc=example,dc=com", "module_name": "users/user", "diff": [("guardianRoles", None, "new_role")]})
        assert not _check_permissions_modify(obj, caps)

    @pytest.mark.parametrize("module_name, expected", [
        ("users/user", True),
        ("groups/group", False),
    ])
    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"users/user": {"create": True}}}]})
    def test_may_create(self, module_name, expected):
        get_user_roles = mock_fun({"test_role": []})
        obj = {"id": "cn=test,dc=example,dc=com", "module_name": module_name}
        with patch("univention.admin.authorization.ACLs.enabled", return_value=False):
            assert auth.may_create(obj, get_user_roles) is None
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            if expected:
                assert auth.may_create(obj, get_user_roles) is None
            else:
                with pytest.raises(TypeError):
                    assert auth.may_create(obj, get_user_roles) is None

    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"username": {"access": "write"}, "lastname": {"access": "read"}}}}}]})
    def test_may_read(self):
        get_user_roles = mock_fun({"test_role": []})
        objs = [{"id": "cn=test,dc=example,dc=com", "module_name": "users/user"}, {"id": "cn=test2,dc=example,dc=com", "module_name": "groups/group"}]
        with patch("univention.admin.authorization.ACLs.enabled", return_value=False):
            assert auth.may_read(objs, get_user_roles) == objs
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            assert auth.may_read(objs, get_user_roles) == [objs[0]]

    @pytest.mark.parametrize("info, attribute, value, objs_name, expected", [
        ({"username": "test", "description": "test"}, "description", "*test*", ["user1", "user2", "user3"], []),
        ({"username": "test", "description": "test"}, "username", "*test*", ["user1"], ["user1"]),
        ({"username": "test", "description": "test"}, None, "*test*", ["user1", "user2", "user3"], ["user1"]),
    ])
    def test_may_read_with_filter(self, info, attribute, value, objs_name, expected):
        default_search_attrs = ["username", "description", "lastname"]
        get_user_roles = mock_fun({"test_role": []})
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            with patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"*": {"attributes": {"*": {"access": "write"}, "description": {"access": "none"}}}}}]}):
                user1 = mock_obj({"id": "cn=user1,dc=example,dc=com", "module_name": "users/user", "info": info})
                user2 = mock_obj({"id": "cn=user2,dc=example,dc=com", "module_name": "users/user", "info": {"username": "user2-ou2", "description": "test"}})
                user3 = mock_obj({"id": "cn=user3,dc=example,dc=com", "module_name": "users/user", "info": {"username": "user3-ou2", "description": "test"}})
                objs = []
                if "user1" in objs_name:
                    objs.append(user1)
                if "user2" in objs_name:
                    objs.append(user2)
                if "user3" in objs_name:
                    objs.append(user3)
                result = auth.may_read(objs, get_user_roles, filter_options={'attribute': attribute, 'value': value, 'default_attributes': default_search_attrs})
                result_dn = [u.dn for u in result]
                assert set(result_dn) == {f"cn={u_e},dc=example,dc=com" for u_e in expected}
                # for u_e in expected:
                #     if f"cn={u_e},dc=example,dc=com" not in [u.dn for u in result]:
                #         assert False

    @pytest.mark.parametrize("module_name, diff, expected", [
        ("users/user", [("username", None, "new_username")], True),
        ("users/user", [("description", None, "new_description")], False),
        ("groups/group", [("description", None, "new_description")], False),
    ])
    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"users/user": {"attributes": {"username": {"access": "write"}, "lastname": {"access": "read"}}}}}]})
    def test_may_modify(self, module_name, diff, expected):
        get_user_roles = mock_fun({"test_role": []})
        obj = mock_obj({"id": "cn=test,dc=example,dc=com", "module_name": module_name, "diff": diff})
        with patch("univention.admin.authorization.ACLs.enabled", return_value=False):
            assert auth.may_modify(obj, get_user_roles) is None
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            if expected:
                assert auth.may_modify(obj, get_user_roles) is None
            else:
                with pytest.raises(TypeError):
                    assert auth.may_modify(obj, get_user_roles) is None

    @pytest.mark.parametrize("module_name, expected", [
        ("users/user", True),
        ("groups/group", False),
    ])
    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"users/user": {"delete": True}}}]})
    def test_may_delete(self, module_name, expected):
        get_user_roles = mock_fun({"test_role": []})
        obj = {"id": "cn=test,dc=example,dc=com", "module_name": module_name}
        with patch("univention.admin.authorization.ACLs.enabled", return_value=False):
            assert auth.may_delete(obj, get_user_roles) is None
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            if expected:
                assert auth.may_delete(obj, get_user_roles) is None
            else:
                with pytest.raises(TypeError):
                    assert auth.may_delete(obj, get_user_roles) is None

    @pytest.mark.parametrize("obj, dest, role, expected", [
        ({'dn': 'uid=user,ou=ou1,dc=example,dc=com', 'module': 'users/user'}, 'uid=user,cn=users,ou=ou1,dc=example,dc=com', "test_role", True),
        ({'dn': 'uid=user,ou=ou1,dc=example,dc=com', 'module': 'users/user'}, 'uid=user,cn=users,ou=ou1,dc=example,dc=com', "test_role2", False),
    ])
    @patch("univention.admin.authorization.ROLES", {"test_role": [{"condition": {"position": "*"}, "permissions": {"*": {"create": True, "delete": True}}}],
                                                    "test_role2": [{"condition": {"position": "ou=ou1,dc=example,dc=com"}, "permissions": {"*": {"create": True, "delete": True}}}]})
    def test_may_move(self, obj, dest, role, expected):
        obj = mock_obj(obj)
        get_user_roles = mock_fun({role: []})
        with patch("univention.admin.authorization.ACLs.enabled", return_value=False):
            assert auth.may_move(obj, dest, get_user_roles) is None
        with patch("univention.admin.authorization.ACLs.enabled", return_value=True):
            if expected:
                assert auth.may_move(obj, dest, get_user_roles) is None
            else:
                with pytest.raises(TypeError):
                    assert auth.may_move(obj, dest, get_user_roles) is None

    @patch("univention.admin.authorization.ldap_base", "dc=test")
    @patch("univention.admin.authorization.ROLES", get_default_roles())
    def test_check_permissions_modify_default_roles(self):
        caps = _get_capabilities({'domainadmin': []})
        assert caps
        assert _check_permissions_modify(mock_obj({'position': 'ou=hans', 'module_name': 'users/user', 'diff': []}), caps)
        assert _check_permissions_modify(mock_obj({'position': 'ou=hans', 'module_name': 'users/user', 'diff': []}), caps)
        assert _check_permissions_modify(mock_obj({'position': 'xyz', 'module_name': 'users/user', 'diff': []}), caps)
        assert _check_permissions_modify(mock_obj({'position': 'dc=bla', 'module_name': 'whatever', 'diff': []}), caps)
        caps = _get_capabilities({'ouadmin': ['ou=ou1', 'ou=ou2']})
        assert _check_permissions_modify(mock_obj({'position': 'ou=ou1,dc=test', 'module_name': 'users/user', 'diff': []}), caps)
        assert not _check_permissions_modify(mock_obj({'position': 'xyz', 'module_name': 'users/user', 'diff': []}), caps)
        assert _check_permissions_modify(mock_obj({'position': 'ou=ou2,dc=test', 'module_name': 'users/user', 'diff': []}), caps)
        assert not _check_permissions_modify(mock_obj({'position': 'ou=ou3,dc=test', 'module_name': 'users/user', 'diff': []}), caps)
        assert _check_permissions_modify(mock_obj({'position': 'ou=ou2,dc=test', 'module_name': 'whatever', 'diff': []}), caps)
        assert not _check_permissions_modify(mock_obj({'position': 'ou=aada', 'module_name': 'whatever', 'diff': []}), caps)

    @patch("univention.admin.authorization.ldap_base", "dc=test")
    @patch("univention.admin.authorization.ROLES", get_default_roles())
    def test_check_permissions_create_default_roles(self):
        caps = _get_capabilities({'domainadmin': []})
        assert caps
        assert _check_permissions_create({'position': 'ou=hans', 'module_name': 'users/user'}, caps)
        assert _check_permissions_create({'position': 'xyz', 'module_name': 'users/user'}, caps)
        assert _check_permissions_create({'position': 'dc=bla', 'module_name': 'whatever'}, caps)
        caps = _get_capabilities({'ouadmin': ['ou=ou1', 'ou=ou2']})
        assert caps
        assert not _check_permissions_create({'position': 'cn=users,dc=test', 'module_name': 'users/user'}, caps)
        assert _check_permissions_create({'position': 'ou=ou1,dc=test', 'module_name': 'users/user'}, caps)
        assert _check_permissions_create({'position': 'ou=ou1,dc=test', 'module_name': 'whatever'}, caps)
        assert _check_permissions_create({'position': 'ou=ou2,dc=test', 'module_name': 'users/user'}, caps)
        assert not _check_permissions_create({'position': 'ou=ou3,dc=test', 'module_name': 'users/user'}, caps)
        assert not _check_permissions_create({'position': 'cn=domain,cn=mail,dc=test', 'module_name': 'mail/domain'}, caps)
        assert not _check_permissions_create({'position': 'dc=bla', 'module_name': 'whatever'}, caps)
        assert _check_permissions_create({'position': 'cn=users,ou=ou2,dc=test', 'module_name': 'users/user'}, caps)

    @patch("univention.admin.authorization.ldap_base", "dc=test")
    @patch("univention.admin.authorization.ROLES", get_default_roles())
    def test_check_permissions_read_default_roles(self):
        ldap_base = "dc=test"
        objs = [
            f"uid=Administrator,cn=users,{ldap_base}",
            f"uid=join-backup,cn=users,{ldap_base}",
            f"uid=join-slave,cn=users,{ldap_base}",
            f"uid=krbkeycloak,cn=users,{ldap_base}",
            f"uid=Guest,cn=users,{ldap_base}",
            f"uid=krbtgt,cn=users,{ldap_base}",
            f"uid=dns-ucs-5833,cn=users,{ldap_base}",
            f"uid=ou1admin,cn=users,{ldap_base}",
            f"uid=user1-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user2-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user3-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user4-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user5-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user6-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user7-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user8-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user9-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=user10-ou1,cn=users,ou=ou1,{ldap_base}",
            f"uid=ou2admin,cn=users,{ldap_base}",
            f"uid=user1-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user2-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user3-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user4-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user5-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user6-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user7-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user8-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user9-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=user10-ou2,cn=users,ou=ou2,{ldap_base}",
            f"uid=ou3admin,cn=users,{ldap_base}",
            f"uid=user1-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user2-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user3-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user4-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user5-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user6-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user7-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user8-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user9-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=user10-ou3,cn=users,ou=ou3,{ldap_base}",
            f"uid=ou4admin,cn=users,{ldap_base}",
            f"uid=user1-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user2-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user3-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user4-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user5-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user6-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user7-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user8-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user9-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=user10-ou4,cn=users,ou=ou4,{ldap_base}",
            f"uid=ou5admin,cn=users,{ldap_base}",
            f"uid=user1-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user2-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user3-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user4-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user5-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user6-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user7-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user8-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user9-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=user10-ou5,cn=users,ou=ou5,{ldap_base}",
            f"uid=ou6admin,cn=users,{ldap_base}",
            f"uid=user1-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user2-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user3-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user4-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user5-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user6-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user7-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user8-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user9-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=user10-ou6,cn=users,ou=ou6,{ldap_base}",
            f"uid=ou7admin,cn=users,{ldap_base}",
            f"uid=user1-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user2-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user3-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user4-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user5-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user6-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user7-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user8-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user9-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=user10-ou7,cn=users,ou=ou7,{ldap_base}",
            f"uid=ou8admin,cn=users,{ldap_base}",
            f"uid=user1-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user2-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user3-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user4-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user5-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user6-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user7-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user8-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user9-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=user10-ou8,cn=users,ou=ou8,{ldap_base}",
            f"uid=ou9admin,cn=users,{ldap_base}",
            f"uid=user1-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user2-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user3-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user4-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user5-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user6-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user7-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user8-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user9-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=user10-ou9,cn=users,ou=ou9,{ldap_base}",
            f"uid=ou10admin,cn=users,{ldap_base}",
            f"uid=user1-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user2-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user3-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user4-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user5-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user6-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user7-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user8-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user9-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=user10-ou10,cn=users,ou=ou10,{ldap_base}",
            f"uid=test1,cn=users,{ldap_base}",
        ]
        caps = _get_capabilities({'domainadmin': []})
        assert caps
        assert set(_check_permissions_read(objs, caps)) == set(objs)

        caps = _get_capabilities({'ouadmin': ['ou=ou1']})
        assert caps
        assert set(_check_permissions_read(objs, caps)) == {obj for obj in objs if "cn=users,ou=ou1," in obj}
        print(_check_permissions_read(objs, caps))


if __name__ == "__main__":
    # unittest.main()
    pass
