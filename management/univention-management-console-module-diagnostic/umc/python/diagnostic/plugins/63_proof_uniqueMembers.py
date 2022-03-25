#!/usr/bin/python3
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2022 Univention GmbH
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

import pipes

from univention.management.console.modules.diagnostic import Warning, ProblemFixed
from univention.management.console.modules.diagnostic import util
from univention.management.console.log import MODULE
from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check LDAP database for group membership attribute errors')
description = _('Check the LDAP database for inconsistencies in group membership attributes.')
run_descr = ['This can be checked by running: /usr/share/univention-directory-manager-tools/proof_uniqueMembers -c']


def run_proof_uniqueMembers_fix(umc_instance):
	cmd = ['/usr/share/univention-directory-manager-tools/proof_uniqueMembers']
	(success, output) = util.run_with_output(cmd)

	cmd_string = ' '.join(pipes.quote(x) for x in cmd)
	MODULE.process('Output of %s:\n%r' % (cmd_string, output))
	fix_log = [_('Output of `{cmd}`:').format(cmd=cmd_string)]

	fix_log.append(output.decode('utf-8', 'replace'))
	run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
	'run_proof_uniqueMembers_fix': run_proof_uniqueMembers_fix,
}


def run(_umc_instance, rerun=False, fix_log=''):
	error_descriptions = []
	if rerun and fix_log:
		error_descriptions.append(fix_log)

	buttons = [{
		'action': 'run_proof_uniqueMembers_fix',
		'label': _('Run `/usr/share/univention-directory-manager-tools/proof_uniqueMembers`'),
	}]

	cmd = ['/usr/share/univention-directory-manager-tools/proof_uniqueMembers', '-c']
	(success, output) = util.run_with_output(cmd)
	if not success:
		error = _('`/usr/share/univention-directory-manager-tools/proof_uniqueMembers -c` found an error with the LDAP database group membership attributes.')
		error_descriptions.append(error)
		error_descriptions.append(output)
		if not rerun:
			fix = _('You can run `/usr/share/univention-directory-manager-tools/proof_uniqueMembers` to fix the issue.')
			error_descriptions.append(fix)
		raise Warning(description='\n'.join(error_descriptions), buttons=buttons)

	if rerun:
		fixed = _('`/usr/share/univention-directory-manager-tools/proof_uniqueMembers -c` found no errors with the LDAP database group membership attributes.')
		error_descriptions.append(fixed)
		MODULE.error('\n'.join(error_descriptions))
		raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
