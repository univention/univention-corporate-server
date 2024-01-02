#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2024 Univention GmbH
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

from pathlib import Path

import univention.uldap
from univention.config_registry import handler_set as ucr_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Critical, Instance, ProblemFixed, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Primary LDAP server check')
description = ['Check the UCR variable `ldap/master` for correctness.']
run_descr = ["Checking Primary LDAP server"]
umc_modules = [{'module': 'ucr'}]


def deactivate_test(umc_instance: Instance) -> None:
    ucr_set([f'diagnostic/check/disable/{Path(__file__).stem}=yes'])


def fix_ldap_master(umc_instance: Instance) -> None:
    master_fqdn = lookup_master()
    ucr_set([f'ldap/master={master_fqdn}'])
    run(umc_instance, retest=True)


actions = {
    'fix_ldap_master': fix_ldap_master,
    'deactivate_test': deactivate_test,
}


def lookup_master() -> str:
    lo = univention.uldap.getMachineConnection()
    master = lo.search(base=ucr['ldap/base'], filter='(univentionServerRole=master)', attr=['cn'])
    try:
        master_cn = master[0][1].get('cn')[0].decode('UTF-8')
    except IndexError:
        raise Critical(f'Could not find the Primary Directory Node {master}')

    return f"{master_cn}.{ucr['domainname']}"


def run(_umc_instance: Instance, retest: bool = False) -> None:
    buttons = [
        {
            "action": "fix_ldap_master",
            "label": _("Fix Primary LDAP server configuration"),
        },
        {
            'action': 'deactivate_test',
            'label': _('Deactivate test'),
        },
    ]

    master_fqdn = lookup_master()
    if master_fqdn != ucr['ldap/master']:
        warn = (_('The primary LDAP Server of this System (UCR ldap/master) is not set to the Primary Directory Node of this UCS domain (%s).') % (master_fqdn,))
        raise Warning(warn, buttons=buttons)

    if retest:
        raise ProblemFixed(buttons=[])


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
