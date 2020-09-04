#!/bin/bash
#
# Copyright (C) 2010-2020 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

export DEBIAN_FRONTEND=noninteractive

UPDATER_LOG="/var/log/univention/updater.log"
exec 3>>"$UPDATER_LOG"
UPDATE_NEXT_VERSION="$1"

install () {
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install "$@" >&3 2>&3
}
reinstall () {
	install --reinstall "$@"
}
check_and_install () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		install "$1"
	fi
}
check_and_reinstall () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	if [ "$state" = "install" ]; then
		reinstall "$1"
	fi
}
is_installed () {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "install"
}
is_deinstalled() {
	local state
	state="$(dpkg --get-selections "$1" 2>/dev/null | awk '{print $2}')"
	test "$state" = "deinstall"
}

echo -n "Running postup.sh script:"
echo >&3
date >&3 2>&3

eval "$(univention-config-registry shell)" >&3 2>&3
. /usr/share/univention-lib/ucr.sh || exit $?

case "${server_role:-}" in
''|basesystem|basissystem) install univention-basesystem ;;
domaincontroller_master) install univention-server-master ;;
domaincontroller_backup) install univention-server-backup ;;
domaincontroller_slave) install univention-server-slave ;;
memberserver) install univention-server-member ;;
esac

if ! is_ucr_true update50/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >&3 2>&3
fi

# removes temporary sources list (always required)
if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

# executes custom postup script (always required)
if [ -n "${update_custom_postup:-}" ]; then
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo -n "Running custom postupdate script $update_custom_postup"
			"$update_custom_postup" "$UPDATE_NEXT_VERSION" >&3 2>&3
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >&3
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >&3
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >&3
	fi
fi

if [ -x /usr/sbin/univention-check-templates ]; then
	if ! /usr/sbin/univention-check-templates >&3 2>&3
	then
		echo "Warning: UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."
	fi
fi

if [ -f /var/univention-join/joined ] && [ "$server_role" != basesystem ]; then
	udm "computers/$server_role" modify \
		--binddn "$ldap_hostdn" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "$ldap_hostdn" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="$UPDATE_NEXT_VERSION" >&3 2>&3
fi

# run remaining joinscripts
if [ "$server_role" = "domaincontroller_master" ]; then
	univention-run-join-scripts >&3 2>&3
fi

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >&3 2>&3

# Bug #51531: re-evaluate extensions startucsversion and enducsversion (always required)
/usr/sbin/univention-directory-listener-ctrl resync udm_extension
/usr/sbin/univention-directory-listener-ctrl resync ldap_extension

rm -f /etc/apt/preferences.d/99ucs500.pref

echo "


****************************************************
*    THE UPDATE HAS BEEN FINISHED SUCCESSFULLY.    *
* Please make a page reload of UMC and login again *
****************************************************


" >&3 2>&3

echo "done."
date >&3

# make sure that UMC server is restarted (Bug #43520, Bug #33426)
at now >&3 2>&3 <<EOF
sleep 30
exec 3>>"$UPDATER_LOG"
# Bug #47436: Only re-enable apache2 and umc if system-setup 
# is not running. System-setup will re-enable apache2 and umc.
if ! pgrep -l -f /usr/lib/univention-system-setup/scripts/setup-join.sh; then
  /usr/share/univention-updater/enable-apache2-umc --no-restart >&3 2>&3
fi
service univention-management-console-server restart >&3 2>&3
service univention-management-console-web-server restart >&3 2>&3
# the file path moved. during update via UMC the apache is not restarted. The new init script therefore checks the wrong pidfile which fails restarting.
cp /var/run/apache2.pid /var/run/apache2/apache2.pid
service apache2 restart >&3 2>&3
# Bug #48808
univention-app update >&3 2>&3 || true
univention-app register --app >&3 2>&3 || true
EOF

exit 0
