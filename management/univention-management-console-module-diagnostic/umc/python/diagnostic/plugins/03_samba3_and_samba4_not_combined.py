#!/usr/bin/python2.7

from subprocess import Popen, PIPE

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Samba3 and Samba4 conflict')
description = _('Ensure that Samba3 and Samba4 are not installed at the same time')

def run():
	process = Popen(['/bin/bash', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate('''
#!/bin/bash

dpkg -s univention-samba 2>/dev/null
samba3_installed=$?

dpkg -s univention-samba4 2>/dev/null
samba4_installed=$?

if [ $samba3_installed == 0 ] && [ $samba4_installed == 0 ]; then
	echo 'Samba3 and Samba4 are installed at the same time'
	echo 'Only one of them should be used'
	echo 'summary: Samba3/Samba4 conflict found'
	exit 1
fi

if [ $samba3_installed == 0 ]; then
	echo -e 'Samba3 is installed\n'
else
	echo -e 'Samba3 is not installed\n'
fi

if [ $samba4_installed == 0 ]; then
	echo 'Samba4 is installed'
else
	echo 'Samba4 is not installed'
fi''')
	return not process.returncode, stdout, stderr
