#!/usr/bin/python2.7

from subprocess import Popen, PIPE
from univention.management.console.modules.diagnostic import Conflict

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Custom modified UCR templates')
description = _('Some Univention Config Registry templates are not in their original state.')

def run():
	import time
	time.sleep(2)
	process = Popen(['/usr/sbin/univention-check-templates'], stdout=PIPE, stderr=PIPE)
	if process.returncode:
		raise Conflict('%s%s' (stdout, stderr))
