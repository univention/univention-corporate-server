#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE, STDOUT
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Gateway is not reachable')
description = '\n'.join([
	_('The gateway %r could not be reached. Please make sure the gateway and related network settings are correctly configured by using the {setup:network}.'),
	_('If these settings are correct the problem relies in the gateway itself:'),
	_('Make sure the hardware of the gateway device is working properly.')
])

umc_modules = [{
	'module': 'setup',
	'flavor': 'network'
}]


def run():
	ucr.load()
	gateway = ucr.get('gateway')
	process = Popen(['/bin/ping', '-c3', '-w4', '-W4', gateway], stdout=PIPE, stderr=STDOUT)
	stdout, stderr = process.communicate()
	if process.returncode:
		raise Critical('\n'.join([description % (gateway,), '', stdout]))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
