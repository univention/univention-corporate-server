#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2017 Univention GmbH
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

import ldap
import socket
import subprocess

import univention.uldap
from univention.management.console.modules.diagnostic import Critical, ProblemFixed

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check local AD database for errors')
description = _('No errors found.'),


def run_samba_tool_dbcheck_fix(umc_instance):
	if not is_service_active('Samba 4'):
		return

	cmd = ['samba-tool', 'dbcheck', '--fix', '--yes']
	(success, output) = run_with_output(cmd)
	if success:
		fix_log = [_('`samba-tool dbcheck --fix --yes` failed.')]
	else:
		fix_log = [_('`samba-tool dbcheck --fix --yes` succeeded.')]
	fix_log.append(output)
	run(umc_instance, rerun=True, fix_log='\n'.join(fix_log))


actions = {
	'run_samba_tool_dbcheck_fix': run_samba_tool_dbcheck_fix
}


def is_service_active(service):
	lo = univention.uldap.getMachineConnection()
	raw_filter = '(&(univentionService=%s)(cn=%s))'
	filter_expr = ldap.filter.filter_format(raw_filter, (service, socket.gethostname()))
	for (dn, _attr) in lo.search(filter_expr, attr=['cn']):
		if dn is not None:
			return True
	return False


def run_with_output(cmd):
	output = list()
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	(stdout, stderr) = process.communicate()
	if stdout:
		output.append('\nSTDOUT:\n{}'.format(stdout))
	if stderr:
		output.append('\nSTDERR:\n{}'.format(stderr))
	return (process.returncode == 0, '\n'.join(output))


def run(_umc_instance, rerun=False, fix_log=''):
	if not is_service_active('Samba 4'):
		return

	error_descriptions = list()
	if rerun and fix_log:
		error_descriptions.append(fix_log)

	buttons = [{
		'action': 'run_samba_tool_dbcheck_fix',
		'label': _('Run `samba-tool dbcheck --fix --yes`'),
	}]

	cmd = ['samba-tool', 'dbcheck']
	(success, output) = run_with_output(cmd)
	if not success:
		error = _('`samba-tool dbcheck` returned a problem with the local AD database.')
		error_descriptions.append(error)
		error_descriptions.append(output)
		if not rerun:
			fix = _('You can run `samba-tool dbcheck --fix` to fix the issue.')
			error_descriptions.append(fix)
		raise Critical(description='\n'.join(error_descriptions), buttons=buttons)

	if rerun:
		fixed = _('`samba-tool dbcheck` found no problems with the local AD database.')
		error_descriptions.append(fixed)
		error_descriptions.append(output)
		raise ProblemFixed(description='\n'.join(error_descriptions))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
