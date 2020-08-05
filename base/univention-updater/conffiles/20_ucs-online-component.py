# Copyright (C) 2011-2020 Univention GmbH
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

import os
import shutil

CUR = '/etc/apt/sources.list.d/20_ucs-online-component.list'
BAK = CUR + '.old'


def preinst(ucr, changes):
    if os.path.exists(BAK):
        os.remove(BAK)

    if os.path.exists(CUR):
        shutil.copy2(CUR, BAK)


def postinst(ucr, changes):
    if not os.path.exists(CUR):
        return

    for key in ucr.keys():
        if key.startswith('repository/online/component/'):
            component_part = '/'.join(key.split('/')[:4])
            if ucr.is_true(key):
                break
    else:
        return

    res = open(CUR, 'r').readlines()
    if len(res) <= 1:
        if os.path.exists(BAK):
            os.rename(BAK, CUR)

    if os.path.exists(BAK):
        os.remove(BAK)
