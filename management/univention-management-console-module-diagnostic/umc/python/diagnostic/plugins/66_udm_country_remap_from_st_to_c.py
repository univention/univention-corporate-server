#!/usr/bin/python3
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2024 Univention GmbH
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

import html
import shlex
import subprocess

from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Critical, ProblemFixed, Warning, util


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check if UDM country can be remapped from st to c.')
description = _('The user property "country" is currently erroneously mapped to the LDAP attribute "st". "st" represents a state (province) while the correct LDAP attribute "c" represents a country. The migration will check and move all LDAP data from "st" to "c" for all users and user templates and install a domain wide UCR policy to change the fields in UDM. If this behavior is not wanted this check can be disabled by setting the UCR variable "diagnostic/check/disable/66_udm_country_remap_from_st_to_c" to true.')
run_descr = ['This can be checked by running: /usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c --check']


def run_remap_country_script(umc_instance):
    cmd = ['/usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c']
    (success, output) = util.run_with_output(cmd)

    cmd_string = ' '.join(shlex.quote(x) for x in cmd)
    MODULE.process('Output of %s:\n%r' % (cmd_string, output))
    fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

    fix_log.append(output)
    if not success:
        fix_log.insert(0, _('The migration failed:'))
        raise Critical(description='\n'.join(fix_log))
    run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
    'run_remap_country_script': run_remap_country_script,
}


def run(_umc_instance, rerun: bool = False, fix_log: str = '') -> None:
    if ucr.get('server/role') != 'domaincontroller_master':
        return
    error_descriptions = []
    if rerun and fix_log:
        error_descriptions.append(fix_log)

    buttons = [{
        'action': 'run_remap_country_script',
        'label': _('migrate LDAP data'),
    }]

    cmd = ['/usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c', '--check']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _stderr = process.communicate()
    exit_code = process.returncode
    if exit_code == 0:
        if rerun:
            fixed = _('`/usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c` successfully migrated your UCS instance to the new UDM country mapping.')
            error_descriptions.append(fixed)
            MODULE.error('\n'.join(error_descriptions))
            raise ProblemFixed(description='\n'.join(error_descriptions))
        return
    elif exit_code == 3:
        error_descriptions.append(description)
        if not rerun:
            fix = _('You can run `/usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c` to migrate.')
            error_descriptions.append(fix)
        if stdout:
            error_descriptions.append(_('The script would apply the following changes:'))
            error_descriptions.append(html.escape(stdout.decode('UTF-8')))
        raise Warning(description='\n'.join(error_descriptions), buttons=buttons)
    else:
        error_descriptions.append(description)
        error_descriptions.append(_('The automation script dry-run failed:'))
        raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
