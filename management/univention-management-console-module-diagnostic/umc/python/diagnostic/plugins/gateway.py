#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Gateway is not reachable')
description = _('Please make sure the gateway is correctly configured in the {setup:network} UMC module.\nIf the settings are correct the problem relies in the gateway: Make sure the gateway is running.\n')

umc_modules = [{
	'module': 'setup',
	'flavor': 'network'
}]


def run():
	ucr.load()
	gateway = ucr.get('gateway')
	process = Popen(['/bin/ping', '-c1', '-w500', gateway], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode:
		raise Critical('%s%s%s' % (description, stderr, stderr))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
