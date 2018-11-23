#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import re
from univention.management.console.modules.diagnostic import Critical, ProblemFixed, MODULE
from univention.management.console.config import ucr
from univention.config_registry import handler_set

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

suggested_max_open_files = 32808

title = _('Security limits exceeded')
#(Samba often uses too many opened file descriptors')
description = '\n'.join([
	_('The security limits (e.g. for max_open_files) are currently not configured properly.'),
	_('This can cause several different serious problems (e.g. the login at samba servers may be impossible, file operations (copy, move) on shares can fail, etc.)'),
	_('It is suggested to increase the security limits either manually by using {ucr} or to automatically adjust them to the suggested limits:'),
	'<pre>samba/max_open_files=%s</pre>' % (suggested_max_open_files,),
	# _('More related information can be found at the "{sdb}".'),
])
# SDB article not published yet, Bug #35868
# links = [{
#	'name': 'sdb',
#	'href': _('http://forum.univention.de/viewtopic.php?f=48&t=2100'),
#	'label': _('Samba4 max open files - Univention Forum')
#}]
buttons = [{
	'name': 'adjust',
	'label': _('Adjust to suggested limits'),
	'action': 'adjust'
}]
actions = {}  # filled at bottom
run_descr = ['checks samba logfile /var/log/samba/log.smbd for "too many open files" messages', 'and checks if ucr get samba/max_open_files is set to the suggested value of 32808']


def run(_umc_instance):
	MODULE.info('Checking samba logfiles for "Too many open files" messages')
	counter = 0
	try:
		with open('/var/log/samba/log.smbd', 'rb') as fd:
			for line in fd:
				counter += len(re.findall('Too many open files', line))
	except (OSError, IOError):
		return  # logfile does not exists

	ucr.load()
	try:
		max_open_files = int(ucr.get('samba/max_open_files', 32808))
	except ValueError:
		max_open_files = 0
	MODULE.process("open files: %s , max open files: %s" % (counter, max_open_files))
	if counter and max_open_files < suggested_max_open_files:
		raise Critical(umc_modules=[{'module': 'ucr'}])


def adjust(_umc_instance):
	MODULE.process('Setting samba/max_open_files')
	handler_set([
		'samba/max_open_files=%d' % (suggested_max_open_files,)
	])
	raise ProblemFixed(_('The limits have been adjusted to the suggested value.'), buttons=[])


actions['adjust'] = adjust


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
