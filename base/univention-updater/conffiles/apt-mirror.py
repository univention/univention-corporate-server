# Copyright (C) 2011-2019 Univention GmbH
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

FILE_NAME = '/etc/apt/mirror.list'


def preinst(baseConfig, changes):
    if os.path.exists('%s.old' % FILE_NAME):
        os.remove('%s.old' % FILE_NAME)
    if os.path.exists(FILE_NAME):
        shutil.copyfile('%s' % FILE_NAME, '%s.old' % FILE_NAME)
    if 'local/repository' in set(changes):
        """ Immediately resolve pending policy changes if local/repository is changed (Bug #16646) """
        os.system('/usr/lib/univention-directory-policy/univention-policy-set-repository-server >>/var/log/univention/repository.log')


def postinst(baseConfig, changes):
    if os.path.exists(FILE_NAME):
        res = open(FILE_NAME, 'r').readlines()
        if len(res) <= 1:
            os.remove(FILE_NAME)
            if os.path.exists('%s.old' % FILE_NAME):
                shutil.copyfile('%s.old' % FILE_NAME, '%s' % FILE_NAME)
        if os.path.exists('%s.old' % FILE_NAME):
            os.remove('%s.old' % FILE_NAME)
