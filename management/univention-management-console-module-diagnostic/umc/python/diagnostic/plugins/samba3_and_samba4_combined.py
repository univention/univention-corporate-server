#!/usr/bin/python2.7

from subprocess import call

from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Conflicting packages Samba3 and Samba4 are installed at the same time.')
description = _('Currently Samba3 and Samba4 are installed at the same time. Please remove one of them ({apps:samba4} / {apps:samba3}) using the {appcenter:appcenter}.')
umc_modules = [{
	'module': 'appcenter',
	'flavor': 'appcenter'
}, {
	'module': 'apps',
	'flavor': 'samba3'
}, {
	'module': 'apps',
	'flavor': 'samba4'
}]


def run():
	samba3_installed = call(['/usr/bin/dpkg', '-s', 'univention-samba']) == 0
	samba4_installed = call(['/usr/bin/dpkg', '-s', 'univention-samba4']) == 0
	if samba4_installed and samba3_installed:
		raise Critical()


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
