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


import json
import requests

from univention.admin.uexceptions import permissionDenied
from univention.management.console.config import ucr

guardian_user = "Administrator"
guardian_user_password = "univention"

keycloak_url = 'https://%s/realms/ucs/protocol/openid-connect/token' % ucr.get("keycloak/server/sso/fqdn")
authz_server = 'https://%s.%s/guardian/authorization' % (ucr.get("hostname"), ucr.get("domainname"))

_response = requests.post(keycloak_url, data={"password": guardian_user_password, "username": guardian_user, "client_id": "guardian-scripts", "grant_type": "password"})

token = _response.json()["access_token"]

guardian_app_name = "udm-umc"
guardian_namespace = "users_user"
guardian_context = "berlin"


def get_guardian_permissions(actor_dn, target_id, target_context):
    body = {
        'namespaces': [],
        'actor': {
            'id': actor_dn,
            'roles': [
                {
                    'app_name': guardian_app_name,
                    'namespace_name': guardian_namespace,
                    # here the role of user role would go, just hardcode admin for now
                    'name': 'admin',
                    'context': {
                        'app_name': guardian_app_name,
                        'namespace_name': guardian_namespace,
                        # this is the context, this could be for example an ou or an department within an org
                        'name': guardian_context
                    }
                }
            ],
            'attributes': {},
        },
        'targets': [
            {
                'old_target': {
                    'id': target_id,
                    'roles': [
                        {
                            'app_name': 'umc',
                            'namespace_name': 'umc',
                            'name': 'resource',
                            'context': {
                                'app_name': 'umc',
                                'namespace_name': 'umc',
                                # needs to match above for condition of capability to be true
                                'name': target_context
                            }
                        }
                    ],
                    'attributes': {}
                }
            }
        ],
        'contexts': [],
        'include_general_permissions': False,
        'extra_request_data': {}
    }
    headers = {'accept': 'application/json', 'content-type': 'application/json', 'authorization': 'Bearer ' + token}
    res = requests.post(authz_server + '/permissions', headers=headers, data=json.dumps(body))

    res_body = res.json()
    result = {}
    print(res_body)
    for item in res_body['target_permissions']:
        target_id = item['target_id']
        permissions = item['permissions']

        permission_names = []
        for perm in permissions:
            permission_names.append(perm['name'])

        result[target_id] = permission_names

    return result[target_id]

def check_guardian_permissions(actor_dn, target_id, target_context, action):
    perms = get_guardian_permissions(actor_dn, target_id, target_context)
    print(f'guardian_permissions are {perms} {actor_dn=}, {target_id=}, {target_context=}, {action=}')
    a = action in perms
    print(f'RESULT IS {a}')

    return a


def get_first_ou(dn_string):
    ou_start_index = dn_string.find("ou=")
    if ou_start_index == -1:
        return None

    comma_after_ou = dn_string.find(",", ou_start_index)

    if comma_after_ou == -1:
        # 'ou=' is at the end of the string
        ou_value = dn_string[ou_start_index + 3:]  # +3 to skip "ou="
    else:
        ou_value = dn_string[ou_start_index + 3:comma_after_ou]

    return ou_value


def _check_user_role():
    # return whether guardian handling is needed,
    # i.e., whether the actual user has meaningful roles
    from univention.management.console.modules.udm.udm_ldap import get_bind_user
    if not ucr.is_true("umc/udm/delegation"):
        print("FEATURE DISABLED")
        return False
    user = get_bind_user()
    if user != "uid=karl,ou=Berlin,ou=People,ou=univention-demo-data,%s" % ucr.get("ldap/base"):
        print("CARL!!!!!!")
        print(user)
        return False
    return True


def user_may_create(obj):
    if not _check_user_role():
        return
    dn = obj._ldap_dn()

    ou = get_first_ou(dn)

    if not isinstance(ou, str):
        raise permissionDenied()
    print(dn)
    authz_result = check_guardian_permissions('karl', dn, ou.lower(), 'write')
    print(f'create result {authz_result}')
    if not authz_result:
        raise permissionDenied()
    print('""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""')


def user_may_read(objs):
    if not _check_user_role():
        return objs
    readable = []
    for obj in objs:
        dn = ""
        ou = ""
        if hasattr(obj, "dn"):
            # "real" udm obj
            dn = obj.dn
        if isinstance(obj, dict):
            # from syntax choices ({"id": dn, "label": name})
            dn = obj['id']
        if isinstance(obj, str):
            # straight dn strings
            dn = obj
        ou = get_first_ou(dn)
        if not isinstance(ou, str):
            continue

        print('""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""')
        print(dn)
        authz_result = check_guardian_permissions('karl', dn, ou.lower(), 'read')
        if authz_result:
            readable.append(obj)
        print('""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""')
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
