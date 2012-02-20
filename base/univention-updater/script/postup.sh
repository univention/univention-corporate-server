#!/bin/bash
#
# Copyright (C) 2010-2011 Univention GmbH
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

export DEBIAN_FRONTEND=noninteractive

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

install ()
{
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install $1 >>"$UPDATER_LOG" 2>&1
}
reinstall ()
{
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes --reinstall install $1 >>"$UPDATER_LOG" 2>&1
}
check_and_install ()
{
	state="$(dpkg --get-selections $1 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install $1
	fi
}
check_and_reinstall ()
{
	state="$(dpkg --get-selections $1 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall $1
	fi
}

echo -n "Running postup.sh script:"
echo >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval "$(univention-config-registry shell)" >>"$UPDATER_LOG" 2>&1

## for p in univention-xen; do
## 	check_and_install $p
## done
## 
## for p in libxenstore3.0; do
## 	check_and_reinstall $p
## done

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	install univention-basesystem
elif [ "$server_role" = "domaincontroller_master" ]; then
	install univention-server-master
elif [ "$server_role" = "domaincontroller_backup" ]; then
	install univention-server-backup  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_slave" ]; then
	install univention-server-slave
elif [ "$server_role" = "memberserver" ]; then
	install univention-server-member
elif [ "$server_role" = "mobileclient" ]; then
	install univention-mobile-client
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	install univention-managed-client
fi

# remove statoverride for UMC; required to ensure that UCM is not restarted during update (always required)
if [ -e /usr/sbin/univention-management-console-server ]; then
	dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
	chmod +x /usr/sbin/univention-management-console-server 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
fi
if [ -e /usr/sbin/apache2 ]; then
	dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
	chmod +x /usr/sbin/apache2 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
fi


# removes temporary sources list (always required)
if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

# executes custom postup script (always required)
if [ ! -z "$update_custom_postup" ]; then
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo -n "Running custom postupdate script $update_custom_postup"
			"$update_custom_postup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" >>"$UPDATER_LOG" 2>&1
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >>"$UPDATER_LOG" 2>&1
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >>"$UPDATER_LOG" 2>&1
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >>"$UPDATER_LOG" 2>&1
	fi
fi

if [ -x /usr/sbin/univention-check-templates ]; then
	/usr/sbin/univention-check-templates >>"$UPDATER_LOG" 2>&1
	rc=$?
	if [ "$rc" != 0 ]; then
		if [ "$rc" = 1 ]; then
			echo "Warning: $rc UCR template was not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
		else
			echo "Warning: $rc UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
		fi
	fi
fi

# For UCS 3.0-1 a reboot is required
univention-config-registry set update/reboot/required=true >>"$UPDATER_LOG" 2>&1

echo "done."
date >>"$UPDATER_LOG" 2>&1

exit 0

