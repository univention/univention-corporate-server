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
import requests

token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJTSXA0T3VTUlNyeS1wMkFzV0lpd1IzUnBnMEg2dlRUaW5fLXFrQWJNcXFFIn0.eyJleHAiOjE3NDAxMDg3NTQsImlhdCI6MTc0MDA3Mjc1NCwianRpIjoiYzk5YmUxOTctMDk3Yi00ZGEwLWE1ZDEtMzJkZjkwOWRiMDE1IiwiaXNzIjoiaHR0cHM6Ly91Y3Mtc3NvLW5nLnVjcy50ZXN0L3JlYWxtcy91Y3MiLCJhdWQiOlsiZ3VhcmRpYW4iLCJndWFyZGlhbi1zY3JpcHRzIiwiYWNjb3VudCJdLCJzdWIiOiJmOmVkZjJjYmI0LWExMTQtNGM1OC04ODU2LWM5ZDI4MWY1ZDFjNDpBZG1pbmlzdHJhdG9yIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZ3VhcmRpYW4tc2NyaXB0cyIsInNpZCI6IjUyMzdiOTQ4LTQzZTAtNDY0Ni05N2YzLWUyM2Y4OGY5MTExZiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cHM6Ly9tYXN0ZXIudWNzLnRlc3QiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImRlZmF1bHQtcm9sZXMtdWNzIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInVpZCI6IkFkbWluaXN0cmF0b3IiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJBZG1pbmlzdHJhdG9yIiwiZG4iOiJ1aWQ9QWRtaW5pc3RyYXRvcixjbj11c2VycyxkYz11Y3MsZGM9dGVzdCIsInByZWZlcnJlZF91c2VybmFtZSI6ImFkbWluaXN0cmF0b3IiLCJmYW1pbHlfbmFtZSI6IkFkbWluaXN0cmF0b3IifQ.mLaBYPK7ZrMpWVZWynwJGW-jdRifM0ocIYipavTZV7e-kvwHOHkaqMYZvbAr7rrwge-XGCxXMnZ8nzKqT9rBTXqji93qUGl3t-EcOXYMmORTWYT_c9xa32QxQ7y9tHJ5-4kIUfgSka4SiSoyKbQW-wRm7WPmZMudLz7iRYWmas1MK6W7O40tP_xVIkSo8_-L4VTVqflMCixgJYlo57FbDGHHEJZ1aznjAZzIINl8ZSALH0G0HADYNDtzWAMQe0WdzTAn_WlKAZWER1yjk9eCopf9l0hQTtMBx1vg54ljeX341Qx3UU6M4Coqb_MQ-pypIcPnjkE7hVTF-seAde_ZUw'
authz_server = 'https://master.ucs.test/guardian/authorization'

def get_guardian_permissions(actor_dn, target_id, target_context):
    body = {
        'namespaces': [],
        'actor': {
            'id': actor_dn,
            'roles': [
                {
                    'app_name': 'umc',
                    'namespace_name': 'umc',
                    # here the name of the actual user role would go, just hardcode admin for now
                    'name': 'admin',
                    'context': {
                        'app_name': 'umc',
                        'namespace_name': 'umc',
                        # this is the context, this could be for example an ou or an department within an org
                        'name': 'berlin'
                    }
                }
            ],
            'attributes': {},
        },
        'targets': [
            {
                'old_target': {
                    # could put the DN of the object being requested here?
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
    import json
    headers={'accept': 'application/json', 'content-type': 'application/json', 'authorization': 'Bearer ' + token}
    res = requests.post(authz_server + '/permissions', headers=headers, data=json.dumps(body))

    res_body = res.json()
    result = {}
    print(res_body)
    for item in res_body['target_permissions']:
        target_id = item['target_id']
        permissions = item['permissions']
        
        permission_names = []
        for perm in permissions:
            permission_names.append(perm['name'])  # Extract just the 'name' (e.g., 'read', 'write')

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
        return False
    user = get_bind_user()
    if user != "uid=karl,ou=Berlin,ou=People,ou=univention-demo-data,dc=ucs,dc=test":
        return False
    return True

def user_may_create(obj):
    if not _check_user_role():
        return
    if "ou=Berlin" not in obj._ldap_dn():
        raise permissionDenied()

def user_may_read(objs):
    if not _check_user_role():
        return objs
    print('""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""')
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
