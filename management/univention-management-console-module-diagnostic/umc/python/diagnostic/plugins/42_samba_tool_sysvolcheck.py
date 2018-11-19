#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2018 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

from univention.management.console.modules.diagnostic import Warning, ProblemFixed, MODULE
from univention.management.console.modules.diagnostic import util

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check Samba sysvol ACLs for errors')
description = _('No errors found.'),
run_descr = ['This can be checked by running samba-tool ntacl sysvolcheck']

def run_samba_tool_ntacl_sysvolreset(umc_instance):
	if not util.is_service_active('Samba 4'):
		return

	cmd = ['samba-tool', 'ntacl', 'sysvolreset']
	(success, output) = util.run_with_output(cmd)

	cmd_string = ' '.join(cmd)
	if success:
		fix_log = [_('`{cmd}` succeeded.').format(cmd=cmd_string)]
		MODULE.process('Output of %s:\n%s' % (cmd_string, output))
	else:
		fix_log = [_('`{cmd}` failed.').format(cmd=cmd_string)]
		MODULE.error('Error running %s:\n%s' % (cmd_string, output))

	fix_log.append(output.decode('utf-8', 'replace'))
	run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
	'run_samba_tool_ntacl_sysvolreset': run_samba_tool_ntacl_sysvolreset,
}


def run(_umc_instance, rerun=False, fix_log=''):
	if not util.is_service_active('Samba 4'):
		return

	error_descriptions = list()
	if rerun and fix_log:
		error_descriptions.append(fix_log)

	buttons = [{
		'action': 'run_samba_tool_ntacl_sysvolreset',
		'label': _('Run `samba-tool ntacl sysvolreset`'),
	}]

	cmd = ['samba-tool', 'ntacl', 'sysvolcheck']
	(success, output) = util.run_with_output(cmd)
	if not success or output:
		error = _('`samba-tool ntacl sysvolcheck` returned a problem with the sysvol ACLs.')
		error_descriptions.append(error)
		#Filters an unhelpful error message from samba
		if output.find("NT_STATUS_OBJECT_NAME_NOT_FOUND") != -1:
			output_list = output.splitlines()
			for x in output_list:
				if x.find("NT_STATUS_OBJECT_NAME_NOT_FOUND") == -1:
					error_descriptions.append(x)
		else:
			error_descriptions.append(output)
		if not rerun:
			fix = _('You can run `samba-tool ntacl sysvolreset` to fix the issue.')
			error_descriptions.append(fix)
		raise Warning(description='\n'.join(error_descriptions), buttons=buttons)

	if rerun:
		fixed = _('`samba-tool ntacl sysvolcheck` found no problems.')
		error_descriptions.append(fixed)
		error_descriptions.append(output)
		raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
