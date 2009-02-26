#!/bin/sh
#
# Univention Installer
#  test the installation
#
# Copyright (C) 2004-2009 Univention GmbH
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
	level=$2
	msg=$3

	if [ "$retval" -eq 0 ]; then
		return 0
	fi

	echo "Installation ${level}: " >> $log
	echo -e "$msg" >> $log
}

# is instmnt mounted
mount | grep $instmnt 2>/tmp/installer.log >/tmp/installer.log 
test_retval $? "error" "Something wrong with the installation root,\nit is not mounted."

# chroot
chroot $instmnt 2>/tmp/installer.log 1>/tmp/installer.log<< __EOF__
exit
__EOF__
test_retval $? "error" "Could not chroot to $instmnt."

# packages
chroot $instmnt 2>/tmp/installer.log 1>/tmp/installer.log<< __EOF__
dpkg -l | egrep "^i[^i]" > /tmp/failed-packages.txt
if [ 0 -eq \$? ]; then
	exit 1
else
	exit 0
fi
__EOF__
test_retval $? "error" "Not all software packages were correctly installed."
if [ -s "$instmnt/tmp/failed-packages.txt" ]; then
	echo "missing packages:" >> $log
	cat $instmnt/tmp/failed-packages.txt >> $log
fi

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

#only check on a DC Master
if [ "$server_role" = "domaincontroller_master" ]; then

	# Administrator
	chroot $instmnt 2>/tmp/installer.log 1>/tmp/installer.log<< __EOF__
id Administrator 1>/tmp/installer.log || exit 1
__EOF__
	test_retval $? "error" "User Administrator was not created."

	# Administrator in admin group
	chroot $instmnt 2>/tmp/installer.log 1>/tmp/installer.log<< __EOF__
getent group | grep "Domain Admins" | grep Administrator >/tmp/installer.log || exit 1
__EOF__
	test_retval $? "error" "User Administrator is not member of \"Domain Admins\" group."

fi

# test join status
if [ ! "$auto_join" = "false" -a ! "${system_role}" = "basesystem" ] ; then
chroot $instmnt 2>/tmp/installer.log 1>/tmp/installer.log<< __EOF__
/usr/share/univention-join/check_join_status | grep -c "Joined successful" || exit 1
__EOF__
test_retval $? "warning" "This system has not been joined yet! If no other problem occurred,\nreboot and run script /usr/share/univention-join/check_join_status\nfor further investigation."
fi
