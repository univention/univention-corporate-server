#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import re
from univention.management.console.modules.diagnostic import Warning, ProblemFixed, MODULE
from univention.config_registry import handler_set

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Samba often uses too many opened file descriptors')
description = _('The limits for max_open_files are currently not configured properly.\nThis can cause errors in Samba4 when copying many files between different shared.\nSuggestion is to increase the value by using the UCR module:\n\nucr set security/limits/user/*/soft/nofile=32828 security/limits/user/*/hard/nofile=32828')
links = [(_('http://forum.univention.de/viewtopic.php?f=48&t=2100'), _('Samba4 max open files - Univention Forum'))]
buttons = [{
	'label': _('Adjust to suggested limits'),
	'action': 'adjust'
}]
actions = {}


def run():
	MODULE.info(_('Checking samba logfiles for "Too many open files" messages'))
	try:
		with open('/var/log/samba/log.smbd', 'rb') as fd:
			counter = re.findall('Too many open files', fd.read())
	except OSError:
		pass  # logfile does not exists

	if True or counter:
		raise Warning(umc_modules=[('ucr', '', {})])


def adjust():
	handler_set([
		'security/limits/user/*/soft/nofile=32828',
		'security/limits/user/*/hard/nofile=32828'
	])
	raise ProblemFixed(_('The limits have been adjusted to the suggested value.'), buttons=[])
actions['adjust'] = adjust


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
