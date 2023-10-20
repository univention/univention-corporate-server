#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
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

import re

from univention.config_registry import handler_set, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, ProblemFixed


_ = Translation('univention-management-console-module-diagnostic').translate

suggested_max_open_files = 32808

title = _('Security limits exceeded')
# (Samba often uses too many opened file descriptors')
description = '\n'.join([
    _('The security limits (e.g. for max_open_files) are currently not configured properly.'),
    _('This can cause several different serious problems (e.g. the login at samba servers may be impossible, file operations (copy, move) on shares can fail, etc.)'),
    _('It is suggested to increase the security limits either manually by using {ucr} or to automatically adjust them to the suggested limits:'),
    f'<pre>samba/max_open_files={suggested_max_open_files}</pre>',
    # _('More related information can be found at the "{sdb}".'),
])
links = [{
    'name': 'sdb',
    'href': _('https://help.univention.com/t/samba4-max-open-files/1758'),
    'label': _('Samba4 max open files - Univention Help'),
}]
buttons = [{
    'label': _('Adjust to suggested limits'),
    'action': 'adjust',
}]
actions = {}  # filled at bottom
run_descr = ['checks samba logfile /var/log/samba/log.smbd for "too many open files" messages', 'and checks if ucr get samba/max_open_files is set to the suggested value of 32808']


def run(_umc_instance: Instance) -> None:
    MODULE.info('Checking samba logfiles for "Too many open files" messages')
    counter = 0
    try:
        with open('/var/log/samba/log.smbd', 'rb') as fd:
            for line in fd:
                counter += len(re.findall(b'Too many open files', line))
    except OSError:
        return  # logfile does not exists

    max_open_files = ucr.get_int('samba/max_open_files', 32808)
    MODULE.process(f"open files: {counter} , max open files: {max_open_files}")
    if counter and max_open_files < suggested_max_open_files:
        raise Critical(umc_modules=[{'module': 'ucr'}])


def adjust(_umc_instance: Instance) -> None:
    MODULE.process('Setting samba/max_open_files')
    handler_set([
        'samba/max_open_files=%d' % (suggested_max_open_files,),
    ])
    raise ProblemFixed(_('The limits have been adjusted to the suggested value.'), buttons=[])


actions['adjust'] = adjust


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
