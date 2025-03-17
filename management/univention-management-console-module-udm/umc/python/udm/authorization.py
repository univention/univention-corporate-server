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
        # ouadmin can read and write all attributes of all udm modules in the ou
        {
            "target": {
                "position": "$CONTEXT",
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

}


ldap_base = ucr.get("ldap/base")


def _check_authorization():
    if not ucr.is_true("umc/udm/delegation"):
        return False
    return True


def _get_capablities(actor_roles):
    cap = []
    for role in actor_roles:
        cap += ROLES.get(role, [])
    return cap


def _check_permission_action(module: str, action: str, permissions: dict) -> bool:
    allowed = False
    if '*' in permissions:
        allowed = permissions['*'].get(action, False)
    if module in permissions:
        allowed = permissions[module].get(action, False)
    return allowed


def _check_permissions_create(obj, caps):

    dn = obj._ldap_dn()
    module = obj.module
    allowed = False

    for cap in caps:
        # FIXME, how to get the best matching position
        if dn.endswith(cap['target']['position']):
            allowed = _check_permission_action(module, 'create', cap['permissions'])
        if cap['target']['position'] == '*':
            allowed = _check_permission_action(module, 'create', cap['permissions'])

    return allowed


def user_may_create(obj, actor_dn, actor_roles):
    if not _check_authorization():
        return
    cap = _get_capablities(actor_roles)
    allowed = _check_permissions_create(obj, cap)
    if not allowed:
        raise Forbidden()


def user_may_read(objs):
    if not _check_authorization():
        return objs
    readable = []
    for obj in objs:
        if hasattr(obj, "dn") and "ou=Berlin" in obj.dn:
            # "real" udm obj
            readable.append(obj)
        if isinstance(obj, dict) and "ou=Berlin" in obj["id"]:
            # from syntax choices ({"id": dn, "label": name})
            readable.append(obj)
        if isinstance(obj, str) and "ou=Berlin" in obj:
            # straight dn strings
            readable.append(obj)
    return readable


def user_may_update(obj):
    if not _check_authorization():
        return
    if "ou=Berlin" not in obj.dn:
        raise permissionDenied()


def user_may_delete(obj):
    if not _check_authorization():
        return
    if "ou=Berlin" not in obj.dn:
        raise permissionDenied()
