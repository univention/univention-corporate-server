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

from subprocess import PIPE, STDOUT, Popen

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Gateway is not reachable')
description = '\n'.join([
    _('The gateway %r could not be reached. Please make sure the gateway and related network settings are correctly configured by using the {setup:network}.'),
    _('If these settings are correct the problem relies in the gateway itself:'),
    _('Make sure the hardware of the gateway device is working properly.'),
])

umc_modules = [{
    'module': 'setup',
    'flavor': 'network',
}]

run_descr = ['This can be checked by running: ping "$(ucr get gateway)"']


def run(_umc_instance: Instance) -> None:
    gateway = ucr.get('gateway')
    if not gateway:
        MODULE.error('There is no gateway configured.')
        raise Critical(_('There is no gateway configured.'))
    process = Popen(['/bin/ping', '-c3', '-w4', '-W4', gateway], stdout=PIPE, stderr=STDOUT)
    stdout_, stderr = process.communicate()
    stdout = stdout_.decode('UTF-8', 'replace')
    if process.returncode:
        MODULE.error('\n'.join(description))
        raise Critical('\n'.join([description % (gateway,), '', stdout]))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
