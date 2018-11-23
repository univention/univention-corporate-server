#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE

from univention.management.console.modules.diagnostic import Critical, Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Package status corrupt')
description = '\n'.join([
	_('The package status of %s packages is corrupt.'),
	_('You may log in to the system as root via ssh and run the command "dpkg --configure -a" as an attempt to correct the packages status.'),
	_('More information about the cause can be gained by executing "dpkg --audit".')
])

run_descr = ['This can be checked by running: dpkg --audit']


def run(_umc_instance):
	proccess = Popen(['dpkg', '--audit'], stdout=PIPE, env={'LANG': 'C'})
	stdout, stderr = proccess.communicate()

	if 'The following packages' in stdout:
		num = len([line for line in stdout.splitlines() if line.startswith(' ')])
		raise Warning(description % num)

	if proccess.returncode:
		raise Critical(description % _('some'))
