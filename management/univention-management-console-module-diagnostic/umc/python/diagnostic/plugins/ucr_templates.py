#!/usr/bin/python2.7

from subprocess import Popen, PIPE, STDOUT
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Custom modified UCR templates')
description = _('Some Univention Config Registry templates are not in their original state.\n')


def run():
	process = Popen(['/usr/sbin/univention-check-templates'], stdout=PIPE, stderr=STDOUT)
	stdout, stderr = process.communicate()
	if process.returncode:
		raise Warning('%s%s' % (description, stdout))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
