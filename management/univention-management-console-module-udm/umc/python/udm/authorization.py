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

from univention.management.console.config import ucr
from univention.management.console.error import Forbidden
from univention.management.console.log import MODULE
from univention.uldap import parentDn


# https://docs.software-univention.de/guardian-manual/3.0/what-is-the-guardian.html#terminology-guardian-permission
# example of how to define capabilities and permissions of a role
# [
# #  Capability
#   {
#     "condition": {
#       "position": "$CONTEXT",  # ldap_position without $ldap_base, $CONTEXT on the role, "*", self
# #      "scope": "subtree"  # subtree, base, one, children
#     },
#     "permissions": {
#       "users/users": {   # udm module, "*"
#         "attributes": {
#           "username": "write",
#           "*": "read"
#         },
#         "create": true,
#         "delete": false
# #      "filter": "(objectClass=inetOrgPerson)"
#       },
#       "groups/groups": {
#         "attributes": {
#           "*": "read"
#         },
#         "create": true
#       }
#     }
#   },
#   {
#     "condition": {
#       "position": "*"
#     },
#     "permissions": {
#       "mail/domain": {
#         "attributes": {
#           "*": "read"
#         }
#       }
#     }
#   }
# ]

# load roles, TODO move to some other place
ROLES = {}
DEFAULT_ROLES = '/usr/share/univention-management-console-module-udm/umc-udm-roles.json'
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


def _check_authorization():
    return ucr.is_true("umc/udm/delegation")


def _get_capabilities(actor_roles):
    cap = []
    for role, contexts in actor_roles.items():
        roles_caps = copy.deepcopy(ROLES.get(role, []))
        for role_cap in roles_caps:
            position = role_cap['condition']['position']
            role_cap['condition']['position'] = position if position in ['*', '$CONTEXT'] else f"{position},{ldap_base}".lower()
            role_cap['condition']['contexts'] = [f'{context},{ldap_base}'.lower() for context in contexts]
        cap += roles_caps
    return cap


def obj2dn(obj: object | dict | str) -> str:
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


def obj2position(obj: object | dict | str) -> str:
    """Extracts the position from an object's distinguished name (DN)."""
    try:
        if hasattr(obj, "position") and (not hasattr(obj, "dn") or not obj.dn):
            return obj.position.getDn().lower()
        if isinstance(obj, dict) and 'position' in obj:
            return obj['position'].lower()
        return parentDn(obj2dn(obj)).lower()
    except (AttributeError, KeyError, IndexError):
        pass
    raise ValueError("Invalid object format for extracting position")


def obj2module(obj: object | dict | str) -> str:
    if hasattr(obj, "module"):
        return obj.module
    if isinstance(obj, dict) and "module_name" in obj:
        return obj["module_name"]
    if isinstance(obj, dict | str):
        dn = obj2dn(obj)
        # FIXME extract module name using dn
        if "cn=users" in dn:
            return "users/user"
        if "cn=groups" in dn:
            return "groups/group"
        else:
            raise NotImplementedError(f"Module extraction from DN not implemented {dn}: {obj} ")


def get_cap_priority(cap: dict) -> int:
    """Returns the priority of a capability."""
    if cap['condition']['position'] == '*':
        return 2
    if cap['condition']['position'] == '$CONTEXT':
        return 1
    return 0


def _check_permission_action(module: str, action: str, permissions: dict) -> bool:
    """Checks if a given action is allowed for a module in permissions."""
    return permissions.get(module, {}).get(action, False) or permissions.get('*', {}).get(action, False)


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


def _check_permissions(obj: object, caps: list[dict], action: str) -> bool:
    position = obj2position(obj)
    module_name = obj2module(obj)
    caps.sort(key=get_cap_priority)
    for cap in caps:
        if _check_condition(position, cap['condition']):
            if _check_permission_action(module_name, action, cap['permissions']):
                return True
    return False


def _check_permissions_create(obj: object, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "create")


def _check_permissions_delete(obj: object, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "delete")


def _check_permissions_read(objs: list[object | dict | str], caps: list[dict]) -> list[object | dict | str]:
    """Filters readable objects based on permissions."""
    readables = []
    attrs_readble = {}
    objs_processed = {}
    # TODO filter objs here

    for obj in objs:
        try:
            position = obj2position(obj)
            module_name = obj2module(obj)
            objs_processed.setdefault((position, module_name), []).append(obj)
        except ValueError:
            continue

    caps.sort(key=get_cap_priority)
    for (position, module_name), _objs in objs_processed.items():
        for cap in caps:
            if _check_condition(position, cap['condition']):
                readble_attrs = _get_readable_attrs_from_permissions(module_name, cap['permissions'])

                if readble_attrs:
                    attrs_readble[(position, module_name)] = readble_attrs
                    break

    for (position, module_name), _objs in objs_processed.items():
        if (position, module_name) in attrs_readble:
            # TODO remove unreadable attributes from objects
            readables.extend(_objs)

    return readables


def _get_attrs_from_permissions(module_name: str, permissions: dict) -> (list[str], list[str]):
    """Retrieves writable and explicitly readable attributes for a given module from permissions."""
    attributes = permissions.get(module_name, {}).get('attributes', []) or permissions.get('*', {}).get('attributes', [])
    readable_attributes = [attr for attr in attributes if attributes[attr] == 'read']
    writable_attributes = [attr for attr in attributes if attributes[attr] == 'write']
    return writable_attributes, readable_attributes


def _get_readable_attrs_from_permissions(module_name: str, permissions: dict) -> (list[str], list[str]):
    """Retrieves readable attributes for a given module from permissions."""
    writable_attrs, readable_attrs = _get_attrs_from_permissions(module_name, permissions)
    return writable_attrs + readable_attrs


def _check_permissions_modify(obj: object | dict | str, caps: list[dict]) -> bool:
    """
    currently only checks if one attribuet is writable
    in the future we need to get the list of modified attributes
    and check if they are all writable
    """
    position = obj2position(obj)
    module_name = obj2module(obj)
    caps.sort(key=get_cap_priority)
    for cap in caps:
        if _check_condition(position, cap['condition']):
            writable_attrs, readable_attrs = _get_attrs_from_permissions(module_name, cap['permissions'])
            if writable_attrs:
                if "*" in writable_attrs and readable_attrs:
                    # TODO check that modified attributes are not in the list of readable attributes
                    return True
                return True
    return False


def user_may_create(obj, actor_roles_func):
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    # allowed = _check_permissions_create(obj._ldap_dn, obj.module, cap)
    # FIXME is obj.position.getDn reliable?
    allowed = _check_permissions_create(obj, cap)
    if not allowed:
        raise Forbidden()


def user_may_read(objs: list[object | dict | str], actor_roles_func) -> list[object | dict | str]:
    if not _check_authorization():
        return objs
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)

    return _check_permissions_read(objs, cap)


def user_may_modify(obj: list[object | dict | str], actor_roles_func) -> None:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if _check_permissions_modify(obj, cap):
        return
    else:
        raise Forbidden()


def user_may_delete(obj: list[object | dict | str], actor_roles_func) -> None:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capabilities(actor_roles)
    if _check_permissions_delete(obj, cap):
        return
    else:
        raise Forbidden()
