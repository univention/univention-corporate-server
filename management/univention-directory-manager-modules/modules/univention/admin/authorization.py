#!/usr/bin/python3
#
# Univention Management Console
#  module: manages UDM modules
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
import copy
import json
import os
import re

from univention.management.console.config import ucr
from univention.management.console.error import Forbidden
from univention.management.console.log import MODULE
from univention.uldap import parentDn


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
        MODULE.error(f'Loading role failed with {exc}')
    MODULE.info(f'Loaded roles: {ROLES}')

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
    except (AttributeError, KeyError):
        pass
    raise ValueError("Invalid object format for extracting DN")


def _obj2position(obj: object | dict | str) -> str:
    """Extracts the position from an object's distinguished name (DN)."""
    try:
        if hasattr(obj, "position") and (not hasattr(obj, "dn") or not obj.dn):
            return obj.position.getDn().lower()
        if isinstance(obj, dict) and 'position' in obj:
            return obj['position'].lower()
        return parentDn(_obj2dn(obj)).lower()
    except (AttributeError, KeyError, IndexError):
        pass
    raise ValueError("Invalid object format for extracting position")


def _obj2module(obj: object | dict | str) -> str:
    if hasattr(obj, "module"):
        return obj.module
    if isinstance(obj, dict) and "module_name" in obj:
        return obj["module_name"]
    if isinstance(obj, dict | str):
        dn = _obj2dn(obj)
        # FIXME: extract module name using dn
        if "cn=users" in dn:
            return "users/user"
        if "cn=groups" in dn:
            return "groups/group"
        else:
            raise NotImplementedError(f"Module extraction from DN not implemented {dn}: {obj} ")


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
    if scope == "subtree":
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
                    attrs_readable[(position, module_name)] = readable_attrs, not_readable_attrs
                    break

    for (position, module_name), _objs in objs_processed.items():
        if (position, module_name) in attrs_readable:
            if not isinstance(_objs[0], dict | str):
                readable_attrs, not_readable_attrs = attrs_readable[(position, module_name)]
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


def _check_authorization() -> bool:
    return ucr.is_true("umc/udm/delegation")


def may_create(obj: object | dict | str, actor_roles_func: callable) -> None:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if not _check_permissions_create(obj, cap):
        raise Forbidden()


def may_read(objs: list[object | dict | str] | object, actor_roles_func: callable, filter_options: dict | None = None) -> list[object | dict | str] | object:
    if not _check_authorization():
        return objs
    result = objs
    if not isinstance(objs, list):
        result = [objs]
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    result = _check_permissions_read(result, cap)
    if not isinstance(objs, list):
        if not result:
            raise Forbidden()
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
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if not _check_permissions_modify(obj, cap):
        raise Forbidden()


def may_delete(obj: object, actor_roles_func: callable) -> None:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if not _check_permissions_delete(obj, cap):
        raise Forbidden()


# TODO: check if we need something special for move/rename
def may_move(obj: object, dest: str, actor_roles_func: callable) -> None:
    if not _check_authorization():
        return
    # may_modify(obj, actor_roles_func)  # optional
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if not _check_permissions_delete(obj, cap):
        raise Forbidden()
    if not _check_permissions_create(dest, cap):
        raise Forbidden()
    return
