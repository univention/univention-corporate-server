#!/usr/bin/python3
#
# Univention Management Console
#  module: manages UDM modules
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2024 Univention GmbH
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


from univention.admin.uexceptions import permissionDenied
from univention.management.console.config import ucr
from univention.management.console.error import Forbidden


# https://docs.software-univention.de/guardian-manual/3.0/what-is-the-guardian.html#terminology-guardian-permission
# example of how to define capabilities and permissions of a role
# [
# #  Capability
#   {
#     "target": {
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
#     "target": {
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


ROLES = {
    "domainadmin": [
        # domainadmin can read and write all attributes of all udm modules
        {
            "target": {
                "position": "*",
            },
            "permissions": {
                "*": {
                    "attributes": {
                        "*": "write",
                    },
                    "create": True,
                    "delete": True,
                },
            },
        },
    ],
    "ouadmin": [
        # ouadmin can read and write all attributes of all udm modules in the ou except guardianRole attributes
        {
            "target": {
                "position": "$CONTEXT",
            },
            "permissions": {
                "*": {
                    "attributes": {
                        "*": "write",
                        "guardianRole": "read",
                        "guardianMemberRoles": "read",
                    },
                    "create": True,
                    "delete": True,
                },
            },
        },
        {
            "target": {
                "position": "cn=groups",
            },
            "permissions": {
                "groups/group": {
                    "attributes": {
                        "*": "read",
                    },
                },
            },
        },
        {
            "target": {
                "position": "cn=domain,cn=mail",
            },
            "permissions": {
                "mail/domain": {
                    # FIXME just for testing, should be False or unset
                    "create": True,
                },
            },
        },
    ],
}


ldap_base = ucr.get("ldap/base")


def _check_authorization():
    if not ucr.is_true("umc/udm/delegation"):
        return False
    return True


def _get_capablities(actor_roles):
    cap = []
    for role, contexts in actor_roles.items():
        roles_caps = ROLES.get(role, [])
        for role_cap in roles_caps:
            role_cap['target']['contexts'] = [f'{context},{ldap_base}'.lower() for context in contexts]
        cap += roles_caps
    return cap


def _check_permission_action(module: str, action: str, permissions: dict) -> bool:
    """Checks if a given action is allowed for a module in permissions."""
    return permissions.get(module, {}).get(action, False) or permissions.get('*', {}).get(action, False)


def _check_permissions(obj: object, caps: list[dict], action: str) -> bool:
    allowed = None
    position = obj2position(obj)
    module_name = obj2module(obj)
    caps.sort(key=get_cap_priority)
    for cap in caps:
        target_position = cap['target']['position']
        permissions = cap['permissions']

        if target_position == '$CONTEXT' and cap['target']['contexts'] and position in cap['target']['contexts']:
            # TODO replace context with context of role
            allowed = _check_permission_action(module_name, action, permissions)
        elif target_position == '*':
            allowed = _check_permission_action(module_name, action, permissions)
        elif f"{target_position},{ldap_base}" == position:
            # FIXME, how to get the best matching position
            allowed = _check_permission_action(module_name, action, permissions)

        if allowed is not None and allowed:
            return True
    return False


def _check_permissions_create(obj: object, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "create")


def _check_permissions_delete(obj: object, caps: list[dict]) -> bool:
    return _check_permissions(obj, caps, "delete")


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
        return obj2dn(obj).split(',', 1)[1].lower()
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
    if cap['target']['position'] == '*':
        return 2
    if cap['target']['position'] == '$CONTEXT':
        return 1
    return 0


def _check_permission_attr_read(module_name: str, permissions: dict) -> list[str]:
    """Retrieves allowed attributes for a given module from permissions."""
    return permissions.get(module_name, {}).get('attributes', []) or permissions.get('*', {}).get('attributes', [])


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
        allowed_attrs = None
        for cap in caps:
            target_position = cap['target']['position']
            permissions = cap['permissions']

            if target_position == '$CONTEXT' and cap['target']['contexts'] and position in cap['target']['contexts']:
                # TODO replace context with context of role
                allowed_attrs = _check_permission_attr_read(module_name, permissions)
            elif target_position == '*':
                allowed_attrs = _check_permission_attr_read(module_name, permissions)
            elif f"{target_position},{ldap_base}" == position:
                # FIXME, how to get the best matching position
                allowed_attrs = _check_permission_attr_read(module_name, permissions)

            if allowed_attrs:
                attrs_readble[(position, module_name)] = allowed_attrs
                break
    for k, _objs in objs_processed.items():  # k = (position, module_name)
        if k in attrs_readble:
            # TODO remove unreadable attributes from objects
            readables.extend(_objs)

    return readables


def _check_permissions_modify(obj: object | dict | str, caps: list[dict]) -> bool:
    return True


def user_may_create(obj, actor_roles_func):
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capablities(actor_roles)
    # allowed = _check_permissions_create(obj._ldap_dn, obj.module, cap)
    # FIXME is obj.position.getDn reliable?
    allowed = _check_permissions_create(obj, cap)
    if not allowed:
        raise Forbidden()


def user_may_read(objs: list[object | dict | str], actor_roles_func) -> list[object | dict | str]:
    if not _check_authorization():
        return objs
    actor_roles = actor_roles_func()
    cap = _get_capablities(actor_roles)

    return _check_permissions_read(objs, cap)


def user_may_update(obj: list[object | dict | str], actor_roles_func) -> list[object | dict | str]:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capablities(actor_roles)
    if _check_permissions_modify(obj, cap):
        return
    else:
        raise permissionDenied()


def user_may_delete(obj: list[object | dict | str], actor_roles_func) -> list[object | dict | str]:
    if not _check_authorization():
        return
    actor_roles = actor_roles_func()
    cap = _get_capablities(actor_roles)
    if _check_permissions_delete(obj, cap):
        return
    else:
        raise permissionDenied()
