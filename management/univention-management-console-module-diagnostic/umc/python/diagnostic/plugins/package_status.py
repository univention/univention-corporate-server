#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from subprocess import call

from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Package status corrupt')
description = '\n'.join([
	_('The package status is corrupt.'),
	_('Login to the system as root via ssh and run the command "dpkg --configure -a" in order to correct the packages status.'),
	_('More information about the cause can be gained by executing "dpkg --audit".')
])


def run():
	if call(['dpkg', '--audit']) != 0:
		raise Critical()
