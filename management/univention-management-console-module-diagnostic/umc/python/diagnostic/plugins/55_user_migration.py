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
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, ProblemFixed


_ = Translation('univention-management-console-module-diagnostic').translate

SCRIPT = '/usr/share/univention-directory-manager-tools/univention-migrate-users-to-ucs4.3'
title = _('User objects which are not migrated')
description = '\n'.join([
    _('With UCS 4.3 the LDAP format of user objects changed. After upgrading the Primary Directory Node all user objects are migrated into the new format.'),
    _('When a user object is created by a system which is not yet on UCS 4.3 it will have the old format. These user objects need to migrated again.'),
])
run_descr = ['Checks user objects exist which are not migrated by using %s --check' % (SCRIPT,)]


def run(_umc_instance: Instance) -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return

    process = Popen([SCRIPT, '--check'], stderr=STDOUT, stdout=PIPE)
    stdout_, _stderr = process.communicate()
    stdout = stdout_.decode('UTF-8', 'replace')
    if process.returncode:
        MODULE.error(description + stdout)
        raise Critical(description + stdout, buttons=[{
            'action': 'migrate_users',
            'label': _('Migrate user objects'),
        }])


def migrate_users(_umc_instance: Instance) -> None:
    process = Popen([SCRIPT], stderr=STDOUT, stdout=PIPE)
    stdout_, _stderr = process.communicate()
    stdout = stdout_.decode('UTF-8', 'replace')
    if process.returncode:
        MODULE.error('Error running univention-migrate-users-to-ucs4.3:\n%s' % (stdout,))
        raise Critical(_('The migration failed: %s') % (stdout,))
    else:
        MODULE.process('Output of univention-migrate-users-to-ucs4.3:\n%s' % (stdout,))
    raise ProblemFixed(buttons=[])


actions = {
    'migrate_users': migrate_users,
}


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
