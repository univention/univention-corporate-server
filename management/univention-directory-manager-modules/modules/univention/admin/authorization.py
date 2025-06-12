#!/usr/bin/python3
#
# Univention Directory Manager
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2025 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
"""Authorization for UDM access."""

import copy
import json
import os
import re
from logging import getLogger

import univention.admin.modules
from univention.admin._ucr import configRegistry as ucr
from univention.admin.uexceptions import permissionDenied
from univention.uldap import parentDn


log = getLogger('ADMIN')

# load roles
# TODO: move to some other place
ROLES = {}
DEFAULT_ROLES = '/usr/share/univention-directory-manager-modules/umc-udm-roles.json'
CUSTOM_ROLES = '/etc/umc-udm-roles.json'
if ucr.is_true('umc/udm/delegation'):
    try:
        for file in [DEFAULT_ROLES, CUSTOM_ROLES]:
            if os.path.isfile(file):
                with open(file) as roles:
                    ROLES.update(json.load(roles))
    except Exception as exc:
        log.error('Loading role failed with %s', exc)
    log.info('Loaded roles: {ROLES}')

ldap_base = ucr.get("ldap/base")


def _obj2dn(obj: object | dict | str) -> str:
    """Extracts the distinguished name (DN) from an object."""
    try:
        if hasattr(obj, "dn"):
            return obj.dn
        if isinstance(obj, dict):
            return obj["id"]
        if isinstance(obj, str):
            return obj
        if isinstance(obj, tuple) and len(obj) == 2:
            return obj[0]
    except (AttributeError, KeyError):
        pass
    raise ValueError("Invalid object format for extracting DN: ", obj)


def _obj2position(obj: object | dict | str) -> str:
    """Extracts the position from an object's distinguished name (DN)."""
    try:
        if isinstance(obj, tuple):
            return _obj2position(_obj2dn(obj[0]))
        if hasattr(obj, "position") and (not hasattr(obj, "dn") or not obj.dn):
            return obj.position.getDn().lower()
        if isinstance(obj, dict) and 'position' in obj:
            return obj['position'].lower()
        if parentDn(_obj2dn(obj), ucr['ldap/base']) is None:
            return _obj2dn(obj).lower()
        return parentDn(_obj2dn(obj), ucr['ldap/base']).lower()
    except (AttributeError, KeyError, IndexError):
        pass
    raise ValueError("Invalid object format for extracting position")


def _obj2module(obj: object | dict | str) -> str:
    if hasattr(obj, "module"):
        return obj.module
    if isinstance(obj, dict) and "univentionObjectType" in obj:
        return obj["univentionObjectType"][0].decode('UTF-8')
    if isinstance(obj, dict | str):
        dn = _obj2dn(obj)
        if dn.startswith('dc='):
            return 'container/dc'
        # FIXME: extract module name using dn
        if dn.lower().startswith('cn=groups,') or dn.lower().startswith('cn=users,'):
            return 'container/cn'
        if "cn=users" in dn or 'cn=self registered users' in dn or dn.startswith('uid='):
            return "users/user"
        if "cn=groups" in dn:
            return "groups/group"
        if dn.lower().startswith('ou='):
            return "container/ou"
        else:
            raise NotImplementedError(f"Module extraction from DN not implemented {dn}: {obj} ")
    if isinstance(obj, tuple):
        return _obj2module(obj[1])
    raise NotImplementedError(obj)


def _get_cap_priority(target_position: str):
    def __get_cap_priority(cap: dict) -> int:
        """Returns the priority of a capability."""
        if cap['condition']['position'] == '*':
            return 3  # lowest priority
        if cap['condition']['position'] == '$CONTEXT':
            return 2  # second-lowest priority
        else:
            if target_position.endswith(cap['condition']['position']):
                return - len(cap['condition']['position'])  # highest priority, best match has the highest priority
            return 1  # third-lowest priority - this means the capability no match with the target position
    return __get_cap_priority


def _check_permission_action(module: str, action: str, permissions: dict) -> bool:
    """Checks if a given action is allowed for a module in permissions."""
    if permissions.get(module, {}).get(action, None) is not None:
        return permissions[module][action]
    if permissions.get('*', {}).get(action, None) is not None:
        return permissions['*'][action]
    return False


def _check_scope_subtree(position: str, condition_positions: list[str]) -> bool:
    """Checks if the position is in the subtree of the condition."""
    return any(position.endswith(condition_position) for condition_position in condition_positions)


def _check_scope_base(position: str, condition_positions: list[str]) -> bool:
    """Checks if the position is in the base of the condition."""
    return position in condition_positions


def _check_condition(position: str, condition: dict) -> bool:
    """Checks if the position matches the condition."""
    if condition['position'] == '*':
        return True
    scope = condition.get('scope', 'base')
    condition_positions = condition.get('contexts', []) if condition['position'] == '$CONTEXT' else [condition['position']]
    if scope in ('one', "subtree"):
        return _check_scope_subtree(position, condition_positions)
    if scope == "base":
        return _check_scope_base(position, condition_positions)
    raise NotImplementedError(f"Scope {scope} not implemented")


def _check_permissions(obj: object | str, caps: list[dict], action: str) -> bool:
    position = _obj2position(obj)
    module_name = _obj2module(obj)
    caps.sort(key=_get_cap_priority(position))
    for cap in caps:
        if _check_condition(position, cap['condition']):
            if _check_permission_action(module_name, action, cap['permissions']):
                return True
    return False


def _get_attrs_from_permissions(module_name: str, permissions: dict) -> (list[str], list[str], list[str]):
    """Retrieves writable and explicitly readable attributes for a given module from permissions."""
    attributes = permissions.get(module_name, {}).get('attributes', {}) or permissions.get('*', {}).get('attributes', {})
    readable_attributes = [attr for attr in attributes if attributes[attr].get('access', '') == 'read']
    writable_attributes = [attr for attr in attributes if attributes[attr].get('access', '') == 'write']
    none_attributes = [attr for attr in attributes if attributes[attr].get('access', '') == 'none']
    return writable_attributes, readable_attributes, none_attributes


def _get_readable_attrs_from_permissions(module_name: str, permissions: dict) -> (list[str], list[str]):
    """Retrieves readable attributes for a given module from permissions."""
    writable_attrs, readable_attrs, none_attrs = _get_attrs_from_permissions(module_name, permissions)
    return writable_attrs + readable_attrs, none_attrs


def _get_writable_attrs_from_permissions(module_name: str, permissions: dict) -> (list[str], list[str]):
    """Retrieves readable attributes for a given module from permissions."""
    writable_attrs, readable_attrs, none_attrs = _get_attrs_from_permissions(module_name, permissions)
    return writable_attrs, readable_attrs + none_attrs


def _check_permissions_delete(obj: object, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "delete")


def _check_permissions_modify(obj: object, caps: list[dict]) -> bool:
    """
    currently only checks if one attribute is writable
    in the future we need to get the list of modified attributes
    and check if they are all writable
    """
    position = _obj2position(obj)
    module_name = _obj2module(obj)
    caps.sort(key=_get_cap_priority(position))
    for cap in caps:
        if _check_condition(position, cap['condition']):
            writable_attrs, not_writable_attrs = _get_writable_attrs_from_permissions(module_name, cap['permissions'])
            if writable_attrs:
                modified_attrs = obj.diff()
                if "*" in writable_attrs:
                    if not_writable_attrs:
                        if any(attr in not_writable_attrs for attr, _, _ in modified_attrs):
                            return False
                    return True
                else:
                    return not any(attr not in writable_attrs for attr, _, _ in modified_attrs)
    return False


def _check_permissions_read(objs: list[object | dict | str], caps: list[dict]) -> list[object | dict | str]:
    """Filters readable objects based on permissions."""
    readables = []
    attrs_readable = {}
    objs_processed = {}

    for obj in objs:
        try:
            position = _obj2position(obj)
            module_name = _obj2module(obj)
            objs_processed.setdefault((position, module_name), []).append(obj)
        except ValueError:
            continue

    for (position, module_name), _objs in objs_processed.items():
        caps.sort(key=_get_cap_priority(position))
        for cap in caps:
            if _check_condition(position, cap['condition']):
                readable_attrs, not_readable_attrs = _get_readable_attrs_from_permissions(module_name, cap['permissions'])

                if readable_attrs:
                    attrs_readable[position, module_name] = readable_attrs, not_readable_attrs
                    break

    for (position, module_name), _objs in objs_processed.items():
        if (position, module_name) in attrs_readable:
            if not isinstance(_objs[0], dict | str | tuple):
                readable_attrs, not_readable_attrs = attrs_readable[position, module_name]
                for obj in _objs:
                    if "*" not in readable_attrs:
                        obj.info = {attr_name: obj.info[attr_name] for attr_name in readable_attrs if attr_name in obj.info}
                    else:
                        for attr_name in not_readable_attrs:
                            if attr_name in obj.info:
                                del obj.info[attr_name]
                        obj.info = {attr_name: obj.info[attr_name] for attr_name in obj.info}
            readables.extend(_objs)

    return readables


def _check_permissions_create(obj: object | str, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "create")


def _get_capabilities(actor_roles: dict) -> list[dict]:
    cap = []
    for role, contexts in actor_roles.items():
        roles_caps = copy.deepcopy(ROLES.get(role, []))
        for role_cap in roles_caps:
            position = role_cap['condition']['position']
            role_cap['condition']['position'] = position if position in ['*', '$CONTEXT'] else f"{position},{ldap_base}".lower() if position else ldap_base.lower()
            role_cap['condition']['contexts'] = [f'{context},{ldap_base}'.lower() for context in contexts]
        cap += roles_caps
    return cap


def may_create(obj: object | dict | str, actor_roles_func: callable) -> None:
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    return _check_permissions_create(obj, cap)


def may_read(objs: list[object | dict | str] | object, actor_roles_func: callable, filter_options: dict | None = None) -> list[object | dict | str] | object:
    result = objs
    if not isinstance(objs, list):
        result = [objs]
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    result = _check_permissions_read(result, cap)
    if not isinstance(objs, list):
        if not result:
            raise permissionDenied()
        return result[0]
    if filter_options:
        attribute = filter_options.get('attribute')
        value = filter_options.get('value')
        default_attributes = filter_options.get('default_attributes', [])
        if result and not isinstance(result[0], str) and attribute not in [None, 'None']:
            result = [obj for obj in result if attribute in obj.info]
        elif result and not isinstance(result[0], str) and value and value != '*':
            re_value = re.compile(value.replace('*', '.*'))
            result = [obj for obj in result if any(attr in obj.info and re_value.match(obj.info[attr]) for attr in default_attributes)]
    return result


def may_modify(obj: object, actor_roles_func: callable) -> None:
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    return _check_permissions_modify(obj, cap)


def may_delete(obj: object, actor_roles_func: callable) -> None:
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    return _check_permissions_delete(obj, cap)


# TODO: check if we need something special for move/rename
def may_move(obj: object, dest: str, actor_roles_func: callable) -> None:
    # may_modify(obj, actor_roles_func)  # optional
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    return _check_permissions_delete(obj, cap) and _check_permissions_create(dest, cap)


def get_user_roles(lo, user_dn: str) -> None:
    # code from components/authorization-engine/guardian/authorization-api/guardian_authorization_api/adapters/persistence.py
    re_split_roles_and_contexts = re.compile(r"^((?P<role_app>[a-z0-9-_]+):(?P<role_namespace>[a-z0-9-_]+):(?P<role_name>[a-z0-9-_]+))(&(?P<context_app>[a-z0-9-_]+):(?P<context_namespace>[a-z0-9-_]+):(?P<context_name>[a-z0-9-_=,]+))?$")
    # FIXME: Why doesn't this allow at least "=" and "," at least in "context_name"?
    # Basically it should allow everything valid in an LDAP DN!? I.e.  case insensitive UTF-8 see https://ldapwiki.com/wiki/Wiki.jsp?page=Distinguished%20Name%20Case%20Sensitivity and https://ldapwiki.com/wiki/Wiki.jsp?page=Ou

    data = lo.authz_connection.get(user_dn, attr=['univentionObjectType'])
    mod = univention.admin.modules.get(data['univentionObjectType'][0].decode('UTF-8'))
    obj = mod.object(None, lo, None, user_dn)
    obj.open()
    if hasattr(obj, 'open_guardian'):
        obj.open_guardian()
    role_set = set(obj.get("guardianInheritedRoles", []) + obj.get("guardianRoles", []))

    __user_roles = {}
    # simulating guardian_authorization_api.adapters.persistence.UDMPersistenceAdapter._to_policy_role()
    for role in role_set:
        if role.startswith("umc:udm:"):
            res = re.search(re_split_roles_and_contexts, role)
            if res:
                res.groupdict()
                __user_roles.setdefault(res["role_name"], [])
                if res["context_name"]:
                    __user_roles[res["role_name"]].append(res["context_name"])
    log.info('Setting user roles to %s', __user_roles)
    return __user_roles


class Authorization:
    """Check authorization via access control lists"""

    enabled = False
    get_privileged_connection = lambda: None  # noqa: E731
    _cache_user_roles = {}
    _cache_univention_object_identifier = {}

    @classmethod
    def enable(cls, get_privileged_connection):
        """Enables ACL checking globally if the running service supports it"""
        cls.enabled = True
        cls.get_privileged_connection = get_privileged_connection

    @classmethod
    def inject_ldap_connection(cls, user_connection, metadata=None):
        if cls.enabled:
            user_connection.metadata = metadata
        return user_connection

    @classmethod
    def get_authz_connection(cls, lo):
        if cls.enabled:
            lo_admin = cls.get_privileged_connection()
            if cls._cache_univention_object_identifier.get(lo.binddn) is None:
                cls._cache_univention_object_identifier[lo.binddn] = lo_admin.lo.get_univention_object_identifier(lo.binddn)
            lo_admin.lo.set_univention_object_identifier(cls._cache_univention_object_identifier[lo.binddn])
            return lo_admin
        return lo

    @property
    def lo(self):
        return self.__class__.get_privileged_connection()

    def _user_roles(self, lo):
        actor_dn = lo.binddn
        if self._cache_user_roles.get(actor_dn) is None:
            self._cache_user_roles[actor_dn] = get_user_roles(self.lo, actor_dn)
        return lambda: self._cache_user_roles[actor_dn]

    def is_receive_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True
        try:
            may_read(obj, self._user_roles(obj.lo))
        except permissionDenied:
            if not raise_exception:
                return False
            raise
        return True

    def filter_search_results(self, lo, results, options=None):
        if not self.enabled:
            return results

        # FIXME: remove this performance intensive search!!!
        options = options or {}
        result_is_dn = options.pop('result-is-ldap-dn', None)
        if result_is_dn:
            options['result-is-udm'] = True
            results = [univention.admin.objects.get_object(lo, dn) for dn in results]

        data = may_read(results, self._user_roles(lo), filter_options=options)

        if result_is_dn:
            data = [obj.dn for obj in data]

        return data

    def is_create_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True
        if not may_create(obj, self._user_roles(obj.lo)) and raise_exception:
            raise permissionDenied()
        return True

    def is_modify_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True
        if not may_modify(obj, self._user_roles(obj.lo)) and raise_exception:
            raise permissionDenied()
        return True

    def is_rename_allowed(self, *args, **kwargs):
        if not self.enabled:
            return True
        return True  # TODO: implement ?

    def is_move_allowed(self, obj, dest, raise_exception=True):
        if not self.enabled:
            return True
        moved_obj = copy.deepcopy(obj)
        moved_obj.dn = dest
        if not may_move(obj, moved_obj, self._user_roles(obj.lo)) and raise_exception:
            raise permissionDenied()
        return True

    def is_remove_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True
        if not may_delete(obj, self._user_roles(obj.lo)) and raise_exception:
            raise permissionDenied()
        return True

    def object_exists(self, obj):
        if not self.is_receive_allowed(obj, raise_exception=False):
            raise univention.admin.uexceptions.noObject(obj.dn)
