#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Updater
#  read the repository settings
#
# Copyright 2004-2021 Univention GmbH
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
from sys import exit
from typing import Dict, List

from univention.config_registry import ConfigRegistry
from univention.lib.policy_result import PolicyResultFailed, policy_result

# Name of the cron.d file
CRON_D = '/etc/cron.d/univention-repository-sync'


def write_cron_job(cron: str) -> None:
    with open(CRON_D, 'w') as cron_file:
        cron_file.write('# cron job for syncing repository\n')
        cron_file.write("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n")
        if cron == '* * * * * ':
            return

        cron_file.write('%s root /usr/sbin/univention-repository-update net >>/var/log/univention/repository.log\n' % cron)


def one(results: Dict[str, List[str]], key: str) -> str:
    try:
        return results[key][0]
    except LookupError:
        return ""


def main() -> None:
    if os.path.exists(CRON_D):
        os.unlink(CRON_D)

    configRegistry = ConfigRegistry()
    configRegistry.load()
    ldap_hostdn = configRegistry.get('ldap/hostdn')
    if not ldap_hostdn:
        return

    try:
        results, _policies = policy_result(ldap_hostdn)
    except PolicyResultFailed as ex:
        exit('failed to execute univention_policy_result: %s' % ex)

    cron = one(results, "univentionRepositoryCron")
    if cron:
        write_cron_job(cron)


if __name__ == '__main__':
    main()
