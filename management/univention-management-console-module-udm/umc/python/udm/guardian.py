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


def user_may_read(objs):
    from univention.management.console.udm.udm_ldap import get_bind_user
    # if not ucr.is_true("umc/udm/delegation"):
    #    return objs
    user = get_bind_user()
    if user != "uid=karl,ou=Berlin,ou=People,ou=univention-demo-data,dc=intranet,dc=wiesenthal110,dc=de":
        return objs
    readable = []
    for obj in objs:
        if hasattr(obj, "dn") and "ou=Berlin" in obj.dn:
            readable.append(obj)
        if isinstance(obj, dict) and "ou=Berlin" in obj["id"]:
            readable.append(obj)
        if isinstance(obj, str) and "ou=Berlin" in obj:
            readable.append(obj)
    return readable
