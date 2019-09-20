#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2019 Univention GmbH
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


import subprocess
from univention.management.console.modules.diagnostic import Warning, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for modified UCR templates')
description = _('No problems found with modified UCR templates')
run_descr = ['This can be checked by running: univention-check-templates']


def run(_umc_instance):
	cmd = ['univention-check-templates']
	try:
		subprocess.check_output(cmd)
	except subprocess.CalledProcessError as error:
		error_description = [
			_('Errors found by `univention-check-templates`.'),
			_('The following UCR files are modified locally.'),
			_('Updated versions will be named FILENAME.dpkg-*.'),
			_('The files should be checked for differences.'),
		]
		if error.output:
			MODULE.error('\n'.join(error_description))
			error_description.extend(('\n\n', error.output))
		raise Warning(' '.join(error_description))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
