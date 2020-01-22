#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import pwd
import subprocess
from univention.management.console.modules.diagnostic import Warning, Critical, ProblemFixed, MODULE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Spamassassin Rules Check')
description = _('All spamassassin rules ok')
run_descr = ['Checks spamassassin rule set and configuration files']

def run(_umc_instance, retest=False):

	uid = -1
	gid = -1
	try:
		pw = pwd.getpwnam('debian-spamd')
		uid = pw[2]
		gid = pw[3]
	except KeyError:
		raise Warning('No user debian-spamd')
		return

	process = subprocess.Popen(['/usr/bin/spamassassin', '--lint'], preexec_fn=demote(uid, gid))
	result = process.wait()

	if result != 0:
		buttons = [{
			'action': 'update_signatures',
			'label': _('Update Signatures'),}]
		raise Warning('Errors in configuration files', buttons=buttons)

	if retest:
		raise ProblemFixed(buttons=[])

def update_signatures(_umc_instance):
	MODULE.process('Updating signatures')
	cron_result = subprocess.Popen(['sh', '/etc/cron.daily/spamassassin'], shell=True).wait()

	if cron_result:
		raise Warning('Could not fetch signatures')
	return run(_umc_instance, retest=True)

def demote(user_uid, user_gid):
	def result():
		os.setgid(user_gid)
		os.setuid(user_uid)
	return result

actions = {
	'update_signatures' : update_signatures
}

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
