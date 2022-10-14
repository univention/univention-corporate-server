#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2022 Univention GmbH
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

from packaging.version import parse

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, Warning

_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check of the protocol version of the Univention Directory Notifier')
description = _('Starting with UCS 4.3-3 Errata 428, the minimum protocol version should be set to 3.')
run_descr = ['This can be checked by running: ucr get notifier/protocol/version']

version_err_msg = _('There is no version/version configured.')
patchlevel_err_msg = _('There is no version/patchlevel configured.')
erratalevel_err_msg = _('There is no version/erratalevel configured.')
npversion_err_msg = _('There is no notifier/protocol/version configured.')
int_cast_err_msg = _('The value notifier/protocol/version has an invalid value.')


def run(_umc_instance: Instance) -> None:
	np_version = ucr.get('notifier/protocol/version')
	ucs_version = ucr.get('version/version')
	ucs_patchlevel = ucr.get('version/patchlevel')
	ucs_erratalevel = ucr.get('version/erratalevel')
	server_role = ucr.get('server/role')

	if server_role not in ('domaincontroller_master', 'domaincontroller_backup'):
		return

	if not ucs_version:
		MODULE.error(version_err_msg)
		raise Critical(version_err_msg)
	if not ucs_patchlevel:
		MODULE.error(patchlevel_err_msg)
		raise Critical(patchlevel_err_msg)
	if not ucs_erratalevel:
		MODULE.error(erratalevel_err_msg)
		raise Critical(erratalevel_err_msg)

	if parse("4.3-3e428") <= parse("%s-%se%s" % (ucs_version, ucs_patchlevel, ucs_erratalevel)):
		if not np_version:
			MODULE.error(npversion_err_msg)
			raise Critical(_(npversion_err_msg))
		try:
			np_version = int(np_version)
		except ValueError:
			MODULE.error(int_cast_err_msg)
			raise Critical(int_cast_err_msg)

		if np_version < 3:
			MODULE.error(description)
			raise Warning(description)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
