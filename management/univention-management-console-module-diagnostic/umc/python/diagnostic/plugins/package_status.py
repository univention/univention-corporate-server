#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE

from univention.management.console.modules.diagnostic import Critical, Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Package status corrupt')
description = '\n'.join([
	_('The package status of %s packages is corrupt.'),
	_('Login to the system as root via ssh and run the command "dpkg --configure -a" in order to correct the packages status.'),
	_('More information about the cause can be gained by executing "dpkg --audit".')
])


def run():
	proccess = Popen(['dpkg', '--audit'], stdout=PIPE, env={'LANG': 'C'})
	stdout, stderr = proccess.communicate()

	if 'The following packages' in stdout:
		num = len([line for line in stdout.splitlines() if line.startswith(' ')])
		raise Warning(description % num)

	if proccess.returncode:
		raise Critical(description % _('some'))
