#!/bin/bash
#
# Copyright (C) 2010-2017 Univention GmbH
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
UPDATE_NEXT_VERSION="$1"

install ()
{
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install "$@" >>"$UPDATER_LOG" 2>&1
}
reinstall ()
{
	install --reinstall "$@"
}
check_and_install ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install "$1"
	fi
}
check_and_reinstall ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall "$1"
	fi
}
is_installed ()
{
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "install"
	return $?
}
is_deinstalled() {
	local state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "deinstall"
	return $?
}

echo -n "Running postup.sh script:"
echo >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval "$(univention-config-registry shell)" >>"$UPDATER_LOG" 2>&1

# shell-univention-lib is proberly not installed, so use a local function
is_ucr_true () {
    local value
    value="$(/usr/sbin/univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
        1|yes|on|true|enable|enabled) return 0 ;;
        0|no|off|false|disable|disabled) return 1 ;;
        *) return 2 ;;
    esac
}

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	install univention-basesystem
elif [ "$server_role" = "domaincontroller_master" ]; then
	install univention-server-master
elif [ "$server_role" = "domaincontroller_backup" ]; then
	install univention-server-backup
elif [ "$server_role" = "domaincontroller_slave" ]; then
	install univention-server-slave
elif [ "$server_role" = "memberserver" ]; then
	install univention-server-member
elif [ "$server_role" = "mobileclient" ]; then
	install univention-mobile-client
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	install univention-managed-client
fi

# Bug #43899: master package of self-service changed, install new master
# package now, or dependencies will be uninstalled
if [ "$server_role" = "domaincontroller_master" ] && is_installed univention-self-service-passwordreset-umc
then
	install univention-self-service-master
fi

# Update to UCS 4.3 autoremove
if ! is_ucr_true update43/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >>"$UPDATER_LOG" 2>&1
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
			"$update_custom_postup" "$UPDATE_NEXT_VERSION" >>"$UPDATER_LOG" 2>&1
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >>"$UPDATER_LOG"
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >>"$UPDATER_LOG"
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >>"$UPDATER_LOG"
	fi
fi

if [ -x /usr/sbin/univention-check-templates ]; then
	/usr/sbin/univention-check-templates >>"$UPDATER_LOG" 2>&1
	rc=$?
	if [ "$rc" != 0 ]; then
		echo "Warning: UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
	fi
fi

if [ -f /var/univention-join/joined -a "$server_role" != basesystem ]; then
	udm "computers/$server_role" modify \
		--binddn "$ldap_hostdn" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "$ldap_hostdn" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="4.3-0" >>"$UPDATER_LOG" 2>&1
fi

# Move to mirror mode for previous errata component
ucr set \
	repository/online/component/4.2-3-errata=false \
	repository/online/component/4.2-3-errata/localmirror=true \
	repository/online/component/4.3-0-errata=enabled \
	repository/online/component/4.3-0-errata/description="Errata updates for UCS 4.3-0" \
	repository/online/component/4.3-0-errata/version="4.3" >>"$UPDATER_LOG" 2>&1

# Bug 45328
# update/register appcenter at this point because 4.3-0 postup still is in 4.2 mode
univention-app update || true
univention-app register --app || true
# Bug 45328

# run remaining joinscripts
if [ "$server_role" = "domaincontroller_master" ]; then
	univention-run-join-scripts >>"$UPDATER_LOG" 2>&1
fi

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >>"$UPDATER_LOG" 2>&1

/usr/share/univention-directory-manager-tools/univention-migrate-users-to-ucs4.3 >>"$UPDATER_LOG" 2>&1

echo "


****************************************************
*    THE UPDATE HAS BEEN FINISHED SUCCESSFULLY.    *
* Please make a page reload of UMC and login again *
****************************************************


" >>"$UPDATER_LOG" 2>&1

echo "done."
date >>"$UPDATER_LOG"

# make sure that UMC server is restarted (Bug #43520, Bug #33426)
at now >>"$UPDATER_LOG" 2>&1 <<EOF
sleep 30
/usr/share/univention-updater/enable-apache2-umc --no-restart >>"$UPDATER_LOG" 2>&1
service univention-management-console-server restart >>"$UPDATER_LOG" 2>&1
service univention-management-console-web-server restart >>"$UPDATER_LOG" 2>&1
# the file path moved. during update via UMC the apache is not restarted. The new init script therefore checks the wrong pidfile which fails restarting.
cp /var/run/apache2.pid /var/run/apache2/apache2.pid
service apache2 restart >>"$UPDATER_LOG" 2>&1
EOF

exit 0
