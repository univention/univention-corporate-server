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
from univention.management.console.modules.diagnostic import Critical, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check primary LDAP server')

run_descr = ['This can be checked by running: ucr get ldap/server/name']


links = [{
    'name': 'sdb',
    'href': 'https://help.univention.com/t/changing-the-primary-ldap-server-to-redistribute-the-server-load/14138',
    'label': _('Univention Support Database - Change the primary LDAP Server to redistribute the server load'),
}]


def deactivate_test(umc_instance: Instance) -> None:
    ucr_set([f'diagnostic/check/disable/{Path(__file__).stem}=yes'])


actions = {
    'deactivate_test': deactivate_test,
}


def run(_umc_instance: Instance) -> None:
    if ucr['server/role'] != 'memberserver':
        return

    lo = univention.uldap.getMachineConnection()
    master = lo.search(base=ucr['ldap/base'], filter='(univentionServerRole=master)', attr=['cn'])
    try:
        master_cn = master[0][1].get('cn')[0].decode('UTF-8')
    except IndexError:
        raise Critical('Could not find a Primary Directory Node %s' % (master,))

    master_fqdn = f"{master_cn}.{ucr['domainname']}"
    if master_fqdn == ucr['ldap/server/name']:
        res = lo.searchDn(base=ucr['ldap/base'], filter='(univentionServerRole=backup)')

        # Case: ldap/server/name is the Primary Directory Node and there are Backup Directory Nodes available.
        if res:
            button = [{
                'action': 'deactivate_test',
                'label': _('Deactivate test'),
            }]
            warn = (_('The primary LDAP Server of this System (UCR ldap/server/name) is set to the Primary Directory Node of this UCS domain (%s).\nSince this environment provides further LDAP Servers, we recommend a different configuration to reduce the load on the Primary Directory Node.\nPlease see {sdb} for further information.') % (master_fqdn,))
            raise Warning(warn, buttons=button)


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
