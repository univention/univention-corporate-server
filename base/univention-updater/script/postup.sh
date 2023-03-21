#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2010-2024 Univention GmbH
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

have () {
	command -v "$1" >/dev/null 2>&1
}
die () {
	echo "$*" >&2
	exit 1
}
apt_install () {
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --allow-unauthenticated --allow-downgrades --allow-remove-essential --allow-change-held-packages install "$@" >&3 2>&3
}
apt_reinstall () {
	apt_install --reinstall "$@"
}
check_and_install () {
	is_installed "$1" &&
		apt_install "$1"
}
check_and_reinstall () {
	is_installed "$1" &&
		reinstall "$1"
}
is_installed () {
	[ 'install' = "$(dpkg-query -f '${db:Status-Want}' -W "$1")" ]
}
is_deinstalled () {
	[ 'deinstall' = "$(dpkg-query -f '${db:Status-Want}' -W "$1")" ]
}
is_joined () {
	[ -f /var/univention-join/joined ]
}

echo -n "Running postup.sh script:"
echo >&3
date >&3 2>&3

eval "$(univention-config-registry shell)" >&3 2>&3
# shellcheck source=/dev/null
. /usr/share/univention-lib/ucr.sh || exit $?

case "${server_role:-}" in
domaincontroller_master) apt_install univention-server-master ;;
domaincontroller_backup) apt_install univention-server-backup ;;
domaincontroller_slave) apt_install univention-server-slave ;;
memberserver) apt_install univention-server-member ;;
'') ;;  # unconfigured
*) die "The server role '$server_role' is not supported!" ;;
esac

is_ucr_true update52/skip/autoremove ||
	DEBIAN_FRONTEND=noninteractive apt-get -y --allow-unauthenticated --allow-downgrades --allow-remove-essential --allow-change-held-packages autoremove >&3 2>&3

# removes temporary sources list (always required)
rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list

# removing the atd service conf file that is setting the KillMode attribute
if [ -e "/etc/systemd/system/atd.service.d/update510.conf" ]; then
	rm -f /etc/systemd/system/atd.service.d/update510.conf
	rmdir --ignore-fail-on-non-empty /etc/systemd/system/atd.service.d/
	systemctl daemon-reload
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

have univention-check-templates &&
	! univention-check-templates >&3 2>&3 &&
	echo "Warning: UCR templates were not updated. Please check $UPDATER_LOG or execute univention-check-templates as root."

is_joined &&
	udm "computers/$server_role" modify \
		--binddn "${ldap_hostdn:?}" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "${ldap_hostdn:?}" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="$UPDATE_NEXT_VERSION" >&3 2>&3

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >&3 2>&3

# run remaining joinscripts
case "${server_role:-}" in
domaincontroller_master) univention-run-join-scripts >&3 2>&3 ;;
esac

# Bug #52971: fix __pycache__ directory permissions
find /usr/lib/python3/dist-packages/ -type d -not -perm 755 -name __pycache__ -exec chmod 755 {} +


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
exec >>"$UPDATER_LOG" 2>&1

# Bug #47436: Only re-enable Apache2 and UMC if USS is not running. USS will re-enable Apache2 and UMC.
/usr/share/univention-updater/enable-apache2-umc \$(pgrep -f /usr/lib/univention-system-setup/scripts/setup-join.sh >/dev/null && echo '--no-restart')

# Bug #48808
univention-app update || true
univention-app register --app || true

# Bug #53212 (4.4-x to 5.0-0)
if dpkg -l univention-samba4 | grep -q ^ii; then
	if samba-tool drs showrepl 2>&1 | egrep -q "DsReplicaGetInfo (.*) failed"; then
		/etc/init.d/samba restart
	fi
	sleep 5
	if [ "\$(pgrep -c '(samba|rpc[([]|s3fs|cldap|ldap|drepl|kdc|kcc|ntp_signd|dnsupdate|winbindd|wrepl)')" -lt 10 ]; then  # should be about 25
		echo 'WARNING '
		echo 'WARNING: There are too few samba processes running. Please check functionality before updating other UCS systems!'
		echo 'WARNING '
	fi
	if ! univention-s4search -s base -b '' defaultNamingContext >/dev/null 2>&1; then
		echo 'ERROR '
		echo 'ERROR: Samba/AD LDAP is not available. Please check functionality before updating other UCS systems!'
		echo 'ERROR '
	fi
fi

# kill UMCP based univention-management-console-server
pgrep -f /usr/sbin/univention-management-console-server | while read pid; do
	lsof -iTCP:"6670" -sTCP:LISTEN -nP | awk '{ print $2}' | grep -q "^${pid}$" && kill "$pid"
done
pkill -f '/usr/bin/python3.*/usr/sbin/univention-management-console-web-server'
EOF

exit 0
