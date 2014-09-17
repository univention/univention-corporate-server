#!/bin/bash
## title: Samba3 and Samba4 conflict
## description: Ensure that Samba3 and Samba4 are not installed at the same time


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
fi
