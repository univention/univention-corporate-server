#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import re
from univention.management.console.modules.diagnostic import Conflict, MODULE
from univention.config_registry import handler_set

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Samba often uses too many opened file descriptors')
description = _('The limits for max_open_files are currently not configured properly. This can cause errors in Samba4 when copying many files between different shared. Suggestion is to increase the value by using the UCR module: ucr set security/limits/user/*/soft/nofile=32828 security/limits/user/*/hard/nofile=32828')
links = [(_('http://forum.univention.de/viewtopic.php?f=48&t=2100'), _('Samba4 max open files - Univention Forum'))]
umc_modules = [('ucr', '', {})]
buttons = [{
	'label': _('Adjust to suggested limits'),
	'action': 'adjust'
}]

def run(action=None):
	if action == 'adjust':
		return adjust()
	MODULE.info(_('Checking samba logfiles for "Too many open files" messages'))
	try:
		with open('/var/log/samba/log.smbd', 'rb') as fd:
			counter = re.findall('Too many open files', fd.read())
	except OSError:
		pass  # logfile does not exists

	if counter:
		raise Conflict()


def adjust():
	handler_set([
		'security/limits/user/*/soft/nofile=32828',
		'security/limits/user/*/hard/nofile=32828'
	])
