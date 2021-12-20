#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import sys
if sys.version_info.major == 2:
	from distutils.version import LooseVersion as parse
else:
	from packaging.version import parse
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical, MODULE, Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Notifier protocol version is less than 3')
description = _('Starting with UCS 4.3-3 Errata 428, the minimum protocol version should be set to 3.')
run_descr = ['This can be checked by running: ucr get notifier/protocol/version']

version_err_msg = _('There is no version/version configured.')
patchlevel_err_msg = _('There is no version/patchlevel configured.')
erratalevel_err_msg = _('There is no version/erratalevel configured.')
npversion_err_msg = _('There is no notifier/protocol/version configured.')


def run(_umc_instance):
	ucr.load()
	np_version = ucr.get('notifier/protocol/version')
	ucs_version = ucr.get('version/version')
	ucs_patchlevel = ucr.get('version/patchlevel')
	ucs_erratalevel = ucr.get('version/erratalevel')

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
		if int(np_version) < 3:
			MODULE.error(description)
			raise Warning(description)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
