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
run_descr = ['Checks syntax of spamassassin rule set and configuration files']

def run(_umc_instance, url='http://www.univention.de/', connecttimeout=30, timeout=30):

	uid = -1
	gid = -1
	try:
		pw = pwd.getpwnam("debian-spamd")
		uid = pw[2]
		gid = pw[3]
	except KeyError:
		raise Warning("No user debian-spamd")
		return

	process = subprocess.Popen(["/usr/bin/spamassassin", "--lint"], preexec_fn=demote(uid, gid))
	result = process.wait()

	if result != 0:
		raise Warning("Errors in configuration files")

def demote(user_uid, user_gid):
	def result():
		os.setgid(user_gid)
		os.setuid(user_uid)
	return result

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
