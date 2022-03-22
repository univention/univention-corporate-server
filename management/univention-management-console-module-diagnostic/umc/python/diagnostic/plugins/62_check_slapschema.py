#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from subprocess import Popen, PIPE

import os
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Warning

_ = Translation('univention-management-console-module-diagnostic').translate

title = _('LDAP schema files are missing')
description = '\n'.join([
	_('The following LDAP schema definitions are missing:\n'),
])
att_missing = _('The schema definition for attribute {0} is missing.\n')


def reduce_errors(list_errors):
	error_info = []
	for error in list_errors:
		error_split = error.split()
		error_code = [word for word in error_split if word.isupper()]
		error_info.append(error_code)
	# print([[word for word in error.split() if word.isupper()] for error in list_errors])
	return error_info


def run(_umc_instance):
	# Check if slapschema is installed
	if not os.path.exists('/usr/sbin/slapschema'):
		return
	process = Popen(['slapschema'], stdout=PIPE, stderr=PIPE, env={'LANG': 'C'}, shell=True)
	stdout, stderr = process.communicate()
	stderr = stderr.decode('UTF-8', 'replace')

	# Check if there was an error
	if not stderr:
		return
	# Filter UNKNOWN error message
	error_list = stderr.splitlines()
	error_id = reduce_errors(error_list)
	# Raise Warning with all attribute missing a schema
	error_msg = description + "".join([att_missing.format(error) for error in error_id])

	raise Warning(error_msg)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main

	main()
