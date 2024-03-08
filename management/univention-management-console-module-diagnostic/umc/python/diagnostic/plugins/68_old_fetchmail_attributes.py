#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2024 Univention GmbH
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

import importlib.util
import sys
from collections import namedtuple
from os import path
from shutil import which

from univention.admin import uldap
from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, ProblemFixed, Warning


_ = Translation('univention-management-console-module-diagnostic').translate


title = _('Fetchmail attributes were not migrated')
description = '\n'.join([
    _('Not all old LDAP fetchmail configurations have been migrated or incomplete configurations remain in some objects.'),
])

description_non_master = '\n'.join([
    _("It is not possible to automatically fix the problem when 'univention-fetchmail' is running on a non-master server."),
    _("Run the script '/usr/share/univention-fetchmail/migrate-fetchmail.py --binddn $DN --bindpwdfile $PWDFILE' to migrate the complete configurations."),
])

run_descr = ['Checks if deprecated LDAP fetchmail attributes still exist. Full configurations can be migrated to the new attributes.']

_ = Translation('univention-management-console-module-diagnostic').translate


def load_migrate_fetchmail():
    spec = importlib.util.spec_from_file_location('migrate_fetchmail', '/usr/share/univention-fetchmail/migrate-fetchmail.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['migrate_fetchmail'] = module
    spec.loader.exec_module(module)
    return module


def load_args(dry_run=True):
    Args = namedtuple("args", 'binddn bindpwdfile dry_run dn')
    args = Args(binddn=None, bindpwdfile=None, dry_run=dry_run, dn=None)
    return args


def output(ret, role):
    complete = []
    incomplete = []
    for x in ret:
        if x[1].issuperset(['fetchmailUsername', 'fetchmailProtocol', 'fetchmailServer', 'fetchmailPassword']):
            complete.append(_("User: %r\n") % (x[0],))
        else:
            incomplete.append(_("User: %r - remaining fetchmail attributes: %s.\n") % (x[0], ', '.join(x[1])))

    buttons = []
    result = description + '\n\n'
    if role != 'domaincontroller_master':
        result += description_non_master + '\n'

    if complete:
        result += _('The following complete configurations were found: ') + "\n"
        result += "".join(complete)
        result += "\n"
        buttons = [{
            'action': 'migrate_configurations',
            'label': _('Migrate configurations'),
        }]

    if incomplete:
        result += _('The following incomplete configurations have been found. Manual action is required to fix it. Attributes still present from past configurations can be deleted.') + "\n"
        result += "".join(incomplete)

    return result, buttons


def migrate_configurations(umc_instance: Instance):
    migrate_fetchmail = load_migrate_fetchmail()
    converter = migrate_fetchmail.Converter()
    converter.args = load_args(dry_run=False)
    converter.access, converter.position = uldap.getAdminConnection()
    converter.main(cmdline=False)
    return run(umc_instance, retest=True)


actions = {
    'migrate_configurations': migrate_configurations,
}


def run(_umc_instance: Instance, retest: bool = False) -> None:
    if not which("fetchmail") or not path.exists("/usr/share/univention-fetchmail/migrate-fetchmail.py"):
        return

    migrate_fetchmail = load_migrate_fetchmail()
    converter = migrate_fetchmail.Converter()
    converter.args = load_args()
    role = ucr.get('server/role')
    if role == 'domaincontroller_master':
        converter.access, converter.position = uldap.getAdminConnection()
    else:
        converter.access, converter.position = uldap.getMachineConnection()

    ret = converter.main(cmdline=False)
    if ret:
        message, buttons = output(ret, role)
        raise Warning(description=message, buttons=buttons)

    if retest:
        raise ProblemFixed()


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
