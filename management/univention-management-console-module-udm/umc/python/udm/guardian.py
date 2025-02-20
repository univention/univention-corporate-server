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


def _check_user_role():
    # return whether guardian handling is needed,
    # i.e., whether the actual user has meaningful roles
    from univention.management.console.modules.udm.udm_ldap import get_bind_user
    if not ucr.is_true("umc/udm/delegation"):
        return False
    user = get_bind_user()
    if user != "uid=karl,ou=Berlin,ou=People,ou=univention-demo-data,dc=intranet,dc=wiesenthal110,dc=de":
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
