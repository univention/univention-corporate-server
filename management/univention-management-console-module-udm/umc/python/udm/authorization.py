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


roles = {
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

### code from components/authorization-engine/guardian/authorization-api/guardian_authorization_api/models/policies.py
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass(frozen=True)
class NamespacedValue:
    app_name: str
    namespace_name: str
    name: str

    def __str__(self):
        return f"{self.app_name}:{self.namespace_name}:{self.name}"


@dataclass(frozen=True)
class Permission(NamespacedValue): ...


@dataclass(frozen=True)
class Context(NamespacedValue): ...


@dataclass(frozen=True)
class Role(NamespacedValue):
    context: Optional[Context] = None

    def __str__(self):
        if self.context:
            return f"{super().__str__()}&{self.context}"
        else:
            return f"{super().__str__()}"

### end code from components/authorization-engine/guardian/authorization-api/guardian_authorization_api/models/policies.py

### code from components/authorization-engine/guardian/authorization-api/guardian_authorization_api/adapters/persistence.py
import re

re_split_roles_and_contexts = re.compile(
    r"^((?P<role_app>[a-z0-9-_]+):(?P<role_namespace>[a-z0-9-_]+):(?P<role_name>[a-z0-9-_]+))(&(?P<context_app>[a-z0-9-_]+):(?P<context_namespace>[a-z0-9-_]+):(?P<context_name>[a-z0-9-_]+))?$"
)

def _to_policy_role(role: str):
    if res := re.search(re_split_roles_and_contexts, role):
        groups = res.groupdict()
        role_app = groups["role_app"]
        role_namespace = groups["role_namespace"]
        role_name = groups["role_name"]
        context = None
        if groups["context_name"] is not None:
            context = Context(
                name=groups["context_name"],
                app_name=groups["context_app"],
                namespace_name=groups["context_namespace"],
            )

        return Role(
            app_name=role_app,
            namespace_name=role_namespace,
            name=role_name,
            context=context,
        )
        raise Exception(f"Role {role} is malformed.")

#def parse_role(role):
#    if res := re.search(re_split_roles_and_contexts, role):
#        groups = res.groupdict()
#        role_app = groups["role_app"]
#        role_namespace = groups["role_namespace"]
#        role_name = groups["role_name"]
#        context = None
#        if groups["context_name"] is not None:
#            name=groups["context_name"]
#            app_name=groups["context_app"]
#            namespace_name=groups["context_namespace"]
#    return (



### end code from components/authorization-engine/guardian/authorization-api/guardian_authorization_api/adapters/persistence.py

ldap_base = ucr.get("ldap/base")

def _check_user_role():
    # return whether guardian handling is needed,
    # i.e., whether the actual user has meaningful roles
    if not ucr.is_true("umc/udm/delegation"):
        return False
    from univention.management.console.modules.udm.udm_ldap import get_user_roles  ## FIXME: circular import
    user_roles = get_user_roles()
    policies_roles = []
    for role in user_roles:
        policies_roles.append(_to_policy_role(role))
    if not [ parsed_role for parsed_role in policies_roles if parsed_role.name in ("domainadmins", "ouadmins") ]:
        return False
    ## Maybe retun here the context extracted from the role, sth like:
    # ctx = [ parsed_role.context for parsed_role in policies_roles if parsed_role.name in ("ouadmins") ]
    # if not ctx:  ## FIXME: pretty silly
    #      ctx = [ '*' for parsed_role in policies_roles if parsed_role.name in ("domainadmins") ]
    # return ctx
    return True


def user_may_create(obj):
    if not _check_user_role():
        return
    if "ou=Berlin" not in obj._ldap_dn():
        raise permissionDenied()


def user_may_read(objs):
    if not _check_user_role():
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
    if not _check_user_role():
        return
    if "ou=Berlin" not in obj.dn:
        raise permissionDenied()


def user_may_delete(obj):
    if not _check_user_role():
        return
    if "ou=Berlin" not in obj.dn:
        raise permissionDenied()
