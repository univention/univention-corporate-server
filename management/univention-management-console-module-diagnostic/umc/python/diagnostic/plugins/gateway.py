#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Conflict

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Gateway is not reachable')
description = _('Please make sure the gateway is correctly configured in the {network} UMC module. If the settings are correct the problem relies in the gateway: Make sure the gateway is running.')

umc_modules = [
	('setup', 'network', {}),
	('udm', 'networks/network', {}),
#	('ucr', '', {})
]

def run():
	ucr.load()
	gateway = ucr.get('gateway')
	process = Popen(['/bin/ping', '-c1', '-w100', gateway], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()
	if process.returncode or 1:
		raise Conflict('%s%s' % (stderr, stderr))
