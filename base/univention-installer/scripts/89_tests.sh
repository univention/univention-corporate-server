#!/bin/bash
#
# Univention Installer
#  test the installation
#
# Copyright 2004-2013 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

# update progress message
. /tmp/progress.lib
echo "__MSG__:$(LC_ALL=$INSTALLERLOCALE gettext "Performing system test")" >&9

. /tmp/installation_profile

if [ -e /tmp/installation_profile_scanned ]; then
	. /tmp/installation_profile_scanned
fi

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
mount | grep $instmnt
test_retval $? "error" "Something wrong with the installation root,\nit is not mounted."

# chroot
chroot $instmnt << __EOF__
exit
__EOF__
test_retval $? "error" "Could not chroot to $instmnt."

# packages
chroot $instmnt << __EOF__
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

should_be_joined="$(echo "$call_master_joinscripts" | tr '[:upper:]' '[:lower:]')"

#only check on a DC Master
if [ "$server_role" = "domaincontroller_master" -a ! "$should_be_joined" = "false" -a ! "$should_be_joined" = "no" ]; then
	# Administrator
	chroot $instmnt << __EOF__
id Administrator 1>/tmp/installer.log || exit 1
__EOF__
	test_retval $? "error" "User Administrator was not created."

	# Administrator in admin group
	chroot $instmnt << __EOF__
getent group | grep "Domain Admins" | grep Administrator >/tmp/installer.log || exit 1
__EOF__
	test_retval $? "error" "User Administrator is not member of \"Domain Admins\" group."
fi

# test join status
if [ ! "$auto_join" = "false" -a ! "${system_role}" = "basesystem"  -a ! "$should_be_joined" = "false" -a ! "$should_be_joined" = "no" ] ; then
chroot $instmnt << __EOF__
i=0
# The listener may restarts the OpenLDAP server, re-try the join check for 60 seconds
while [ \$i -lt 60 ]; do
	echo "Test join status (\$i/60)"
	/usr/share/univention-join/check_join_status && break
	i=\$((i+1))
	sleep 1
done
test "\$i" = 60 && exit 1
exit 0
__EOF__
test_retval $? "warning" "This system has not been joined yet! If no other problem occurred,\nreboot and run script /usr/share/univention-join/check_join_status\nfor further investigation."
fi
