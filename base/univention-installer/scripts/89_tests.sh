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
log="/tmp/installation_error.log"


test_retval () {

	retval=$1
	msg=$2

	if [ "$retval" -eq 0 ]; then
		return 0
	fi

	echo "Installation error: " >> $log
	echo -e "$msg" >> $log
}

# is instmnt mounted
mount | grep $instmnt 2>/dev/null >/dev/null 
test_retval $? "Something wrong with the installation root,\nit is not mounted."

# chroot
chroot $instmnt 2>/dev/null 1>/dev/null<< __EOF__
exit
__EOF__
test_retval $? "Could not chroot to $instmnt."

# packages
chroot $instmnt 2>/dev/null 1>/dev/null<< __EOF__
dpkg -l | egrep "^i[^i]" >/tmp/failed-packages.txt
if [ 0 -eq $? ]; then
	exit 1
else
	exit 0
fi
__EOF__
test_retval $? "Not all software packages were correctly installed."
if [ -e "$instmnt/tmp/failed-packages.txt" ]; then
	cat $instmnt/tmp/failed-packages.txt >> $log
fi

# Administrator
chroot $instmnt 2>/dev/null 1>/dev/null<< __EOF__
id Administrator 1>/dev/null || exit 1
__EOF__
test_retval $? "User Administrator was not created."

# Administrator in admin group
chroot $instmnt 2>/dev/null 1>/dev/null<< __EOF__
getent group | grep "Domain Admins" | grep Administrator >/dev/null || exit 1
__EOF__
test_retval $? "User Administrator is not member of \"Domain Admins\" group."
