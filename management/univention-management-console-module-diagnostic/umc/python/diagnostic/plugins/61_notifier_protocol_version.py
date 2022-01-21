#!/usr/bin/python3
# -*- coding: utf-8 -*-

try:
	from distutils.version import LooseVersion as parse
except ImportError:  # python 3
	from packaging.version import parse
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical, MODULE, Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check security considerations of Notifier protocol version')
description = _('Starting with UCS 4.3-3 Errata 428, the minimum protocol version should be set to 3.')
run_descr = ['This can be checked by running: ucr get notifier/protocol/version']

version_err_msg = _('There is no version/version configured.')
patchlevel_err_msg = _('There is no version/patchlevel configured.')
erratalevel_err_msg = _('There is no version/erratalevel configured.')
npversion_err_msg = _('There is no notifier/protocol/version configured.')
int_cast_err_msg = _('The value notifier/protocol/version has an invalid value.')


def run(_umc_instance):
	ucr.load()
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
