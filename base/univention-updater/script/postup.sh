#!/bin/bash
# SPDX-FileCopyrightText: 2010-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# shellcheck disable=SC2317

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
if [ -e "/etc/systemd/system/atd.service.d/update520.conf" ]; then
	rm -f /etc/systemd/system/atd.service.d/update520.conf
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

# Bug #58875 remove pxe linux
if ! is_installed univention-net-installer; then
	if [ "$server_role" = "domaincontroller_master" ]; then
		case "$(univention-directory-manager policies/dhcp_boot list --filter cn=default-settings | awk '/^boot_filename: / {print $2}')" in
		''|pxelinux.0)
			univention-directory-manager policies/dhcp_boot modify --ignore_exists \
				--dn "cn=default-settings,cn=boot,cn=dhcp,cn=policies,$ldap_base" \
				--set boot_filename=None || die
				# unset all pxe ucr vars
				ucr search --brief --key ^pxe | sed 's/\:.*//' | xargs ucr unset
		esac
	fi
	a2dissite univention-net-installer.conf 2>/dev/null
	ucr unset security/packetfilter/package/univention-net-installer-daemon/tcp/49173/all
	ucr unset security/packetfilter/package/univention-net-installer-daemon/tcp/49173/all/en
fi


# Bug #52971: fix __pycache__ directory permissions
find /usr/lib/python3/dist-packages/ -type d -not -perm 755 -name __pycache__ -exec chmod 755 {} +

# Bug #52923 #57296: switch back to old fetchmail/autostart status
if [ -n "$(ucr search "^fetchmail/autostart/update522$")" ] ; then
	eval "$(ucr shell fetchmail/autostart/update522)"
	if [ -z "$fetchmail_autostart_update522" ] ; then
		ucr unset fetchmail/autostart >&3 2>&3
	else
		ucr set fetchmail/autostart="$fetchmail_autostart_update522" >&3 2>&3
	fi
	ucr unset fetchmail/autostart/update522 >&3 2>&3
	echo "Please note:" >&3
	echo "The following fetchmail restart might fail if fetchmail is unconfigured." >&3
	echo "This is usually no error." >&3
	systemctl restart fetchmail >&3 2>&3
fi

# remove backup packages sources
rm -f /etc/apt/sources.list.d/15_ucs-online-version.list.upgrade522.bak
rm -f /etc/apt/sources.list.d/20_ucs-online-component.list.upgrade522.bak

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
