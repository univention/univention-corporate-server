#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2010-2022 Univention GmbH
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

die () {
	echo "$*" >&2
	exit 1
}
install () {
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --allow-unauthenticated --allow-downgrades --allow-remove-essential --allow-change-held-packages install "$@" >&3 2>&3
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
# shellcheck source=/dev/null
. /usr/share/univention-lib/ucr.sh || exit $?

case "${server_role:-}" in
domaincontroller_master) install univention-server-master ;;
domaincontroller_backup) install univention-server-backup ;;
domaincontroller_slave) install univention-server-slave ;;
memberserver) install univention-server-member ;;
'') ;;  # unconfigured
basesystem) die "The server role '$server_role' is not supported anymore with UCS-5!" ;;
*) die "The server role '$server_role' is not supported!" ;;
esac

if ! is_ucr_true update50/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --allow-unauthenticated --allow-downgrades --allow-remove-essential --allow-change-held-packages autoremove >&3 2>&3
fi

# removes temporary sources list (always required)
if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

# removing the atd service conf file that is setting the KillMode attribute
if [ -e "/etc/systemd/system/atd.service.d/update500.conf" ]; then
	rm -f /etc/systemd/system/atd.service.d/update500.conf
	rmdir --ignore-fail-on-non-empty /etc/systemd/system/atd.service.d/
	systemctl daemon-reload
fi

# Bug #52993: recreate initramfs for all available kernels due to removed initramfs/init
echo "recreate initramfs for all available kernels due to changes in univention-initrd..." >&3 2>&3
/usr/sbin/update-initramfs -k all -c >&3 2>&3
echo "done" >&3 2>&3

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

if [ -f /var/univention-join/joined ]
then
	udm "computers/$server_role" modify \
		--binddn "${ldap_hostdn:?}" \
		--bindpwdfile "/etc/machine.secret" \
		--dn "${ldap_hostdn:?}" \
		--set operatingSystem="Univention Corporate Server" \
		--set operatingSystemVersion="$UPDATE_NEXT_VERSION" >&3 2>&3
fi

# Bug #44188: recreate and reload packetfilter rules to make sure the system is accessible
service univention-firewall restart >&3 2>&3

# run remaining joinscripts
if [ "$server_role" = "domaincontroller_master" ]; then
	univention-run-join-scripts >&3 2>&3
fi

rm -f /etc/apt/preferences.d/99ucs500.pref /etc/apt/apt.conf.d/99ucs500

rm -f /etc/apt/sources.list.d/15_ucs-online-version.list.upgrade500-backup
rm -f /etc/apt/sources.list.d/20_ucs-online-component.list.upgrade500-backup

# Bug #47192: Remove deprecated errata components
ucr search --brief --non-empty '^repository/online/component/[1-4][.][0-9]+-[0-9]+-errata' |
  tee -a "$UPDATER_LOG" |
  cut -d: -f1 |
  xargs -r ucr unset

# Bug #52971: fix __pycache__ directory permissions
find /usr/lib/python3/dist-packages/ -type d -not -perm 755 -name __pycache__ -exec chmod 755 {} \;


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
if dpkg -l univention-samba4 | grep -q ^ii; then
	if samba-tool drs showrepl  2>&1 | egrep -q "DsReplicaGetInfo (.*) failed"; then
		/etc/init.d/samba restart
	fi
	sleep 5
	if [ "$(pgrep -c '(samba|rpc[([]|s3fs|cldap|ldap|drepl|kdc|kcc|ntp_signd|dnsupdate|winbindd|wrepl)') -lt 10 ]; then  # should be about 25
		echo "WARNING "
		echo "WARNING: There are too few samba processes running. Please check functionality before updating other UCS systems!"
		echo "WARNING "
	fi
	if ! univention-s4search -s base -b '' defaultNamingContext >/dev/null 2>&1; then
		echo "ERROR "
		echo "ERROR: Samba/AD LDAP is not available. Please check functionality before updating other UCS systems!"
		echo "ERROR "
	elif
fi
EOF

exit 0
