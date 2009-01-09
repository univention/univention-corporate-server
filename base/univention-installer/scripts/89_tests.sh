#!/bin/sh
#
# Univention Installer
#  test the installation
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

. /tmp/installation_profile

instmnt="/instmnt"
log="/instmnt/var/log/univention/installation.log"

test_retval () {

	retval=$1
	msg=$2

	if [ "$retval" -eq 0 ]; then
		return 0
	fi

	echo "installation error: $msg" >> $log
	echo "system reboot" >> $log

	clear


	echo ""
	echo "******************************************************************"
	echo "***   ERROR ERROR ERROR  ERROR ERROR ERROR ERROR ERROR ERROR   ***"
	echo "***                   INSTALLATION ERROR                       ***"
	echo "***                                                            ***"
	echo "******************************************************************"
	echo ""
	echo "Error:"
	echo $msg
	echo ""
	echo "The installation was not successsfully. Please try again."
	echo ""

	if [ -n "$auto_reboot" ] && [ "$auto_reboot" = "Yes" -o "$auto_reboot" = "yes" -o "$auto_reboot" = "True" -o "$auto_reboot" = "true" ]; then
		reboot
	else
	        echo "Please press enter to reboot the system"
        	read foobar
		reboot
	fi
}

# is instmnt mounted
mount | grep $instmnt >/dev/null 
test_retval $? "Something wrong with the installation root, it is not mounted."

# chroot
chroot $instmnt << __EOF__
exit
__EOF__
test_retval $? "could not chroot to $instmnt"

# packages
chroot $instmnt << __EOF__
. /etc/univention/installation_profile
for i in $packages; do
	dpkg -l \$i | grep "^ii[[:space:]]*\$i" >/dev/null || exit 1
done
__EOF__
test_retval $? "not all software packages were correctly installed"

# Administrator
chroot $instmnt << __EOF__
id Administrator >/dev/null || exit 1
__EOF__
test_retval $? "user Administrator was not created"

# Administrator in admin group
chroot $instmnt << __EOF__
getent group | grep "Domain Admins" | grep Administrator >/dev/null || exit 1
__EOF__
test_retval $? "user Administrator is not member of \"Domain Admins\" group"
