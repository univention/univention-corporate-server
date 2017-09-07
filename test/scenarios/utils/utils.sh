#!/bin/bash
#
# Copyright 2013-2016 Univention GmbH
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

basic_setup ()
{
	if grep "QEMU Virtual CPU" /proc/cpuinfo ; then
		echo "KVM detected"
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
		# wait until Univention System Setup is running and profile file has been moved
	else
		echo "Assuming Amazon Cloud"
		cat >/etc/network/if-up.d/z_route <<__SH__
#!/bin/sh
ip route replace default via 10.210.216.13  # VPN gateway
ip route replace 169.254.169.254 dev eth0  # EC2 meta-data service
__SH__
		chmod +x /etc/network/if-up.d/z_route
		/etc/network/if-up.d/z_route
		sleep 10 # just wait a few seconds to give the amazone cloud some time
		# set dns/forwarder*, this should prevent a later bind restart (Bug #39807)
		i=1; cat /etc/resolv.conf | sed -ne 's|^nameserver ||p' | while read ns; do ucr set dns/forwarder$i=$ns; i="$((i+1))"; done
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
		if grep -F /dev/vda /boot/grub/device.map && [ -b /dev/xvda ] # Bug 36256
		then
			/usr/sbin/grub-mkdevicemap
			echo set grub-pc/install_devices /dev/xvda | debconf-communicate
		fi
	fi
	while pgrep -f "/etc/init.d/rc 2" && ! pgrep -f /opt/firefox/firefox ; do
		sleep 1s
	done
	sleep 5s
	if [ -f /var/cache/univention-system-setup/profile.bak ] ; then
		mv /var/cache/univention-system-setup/profile.bak /var/cache/univention-system-setup/profile
	fi
}

rotate_logfiles () {
	test -x /usr/sbin/logrotate && logrotate -f /etc/logrotate.conf
}

jenkins_updates () {
	local version_version version_patchlevel version_erratalevel target
	target="$(echo "${JOB_NAME:-}"|sed -rne 's,.*/UCS-([0-9]+\.[0-9]+-[0-9]+)/.*,\1,p')"
	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Starting from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."

	case "${release_update:-}" in
	public) upgrade_to_latest --updateto "$target" ;;
	testing) upgrade_to_testing --updateto "$target" ;;
	none|"") ;;
	*) echo "Unknown release_update='$release_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Continuing from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."

	case "${errata_update:-}" in
	testing) upgrade_to_latest_test_errata ;;
	public) upgrade_to_latest_errata ;;
	none|"") ;;
	*) echo "Unknown errata_update='$errata_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Finished at ${version_version}-${version_patchlevel}+${version_erratalevel}"
}

upgrade_to_latest_patchlevel ()
{
	local updateto="$(ucr get version/version)-99"
	upgrade_to_latest --updateto "$updateto"
}

upgrade_to_latest_errata () {
	local current="$(ucr get version/version)-$(ucr get version/patchlevel)"
	upgrade_to_latest --updateto "$current"
}

upgrade_to_latest_test_errata () {
	local current prev=DUMMY rc=0
	while current="$(ucr get version/version)-$(ucr get version/patchlevel)" && [ "$current" != "$prev" ]
	do
		if [ -x /root/activate-errata-test-scope.sh ]
		then
			/root/activate-errata-test-scope.sh
		fi
		upgrade_to_latest --updateto "$current"
		rc=$?
		prev="$current"
	done
	return $rc
}

upgrade_to_testing () {
	ucr set repository/online/server=updates-test.software-univention.de
	upgrade_to_latest "$@"
}

upgrade_to_latest () {
	declare -i remain=300 rv delay=30
	while true
	do
		univention-upgrade --noninteractive --ignoreterm --ignoressh "$@"
		rv="$?"
		case "$rv" in
		0) return 0 ;;  # success
		5) delay=30 ;;  # /var/lock/univention-updater exists
		*) delay=$remain ;;  # all other errors
		esac
		echo "ERROR: univention-upgrade failed exitcode $rv"
		ps faxwww
		ucr search --brief --non-empty update/check
		[ $remain -gt 0 ] || return "$rv"
		remain+=-$delay
		sleep "$delay"  # Workaround for Bug #31561
	done
}

run_setup_join ()
{
	local srv rv=0
	/usr/lib/univention-system-setup/scripts/setup-join.sh || rv=$?
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do
		invoke-rc.d "$srv" restart
	done
	ucr unset --forced update/available
	return $rv
}

run_setup_join_on_non_master ()
{
	local admin_password="${1:-univention}"
	local srv rv=0
	ucr set nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	echo -n "$admin_password" >/tmp/univention
	/usr/lib/univention-system-setup/scripts/setup-join.sh --dcaccount Administrator --password_file /tmp/univention || rv=$?
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do
		invoke-rc.d "$srv" restart
	done
	ucr unset --forced update/available
	return $rv
}

wait_for_reboot ()
{
	local i=0
	while [ $i -lt 900 ]
	do
		pidof apache2 && break
		sleep 1
		i=$((i + 1))
	done
	if [ $i = 900 ]; then
		echo "WARNING: wait_for_reboot: Did not find running apache after 900 seconds"
	fi
}

switch_to_test_app_center ()
{
	ucr set repository/app_center/server=appcenter-test.software-univention.de
	univention-app update
}

switch_components_to_test_app_center ()
{
	ucr search --brief --value appcenter.software-univention.de | \
		grep 'repository/online/component/.*/server' | \
		awk -F ':' '{print $1}' | \
		xargs -I % ucr set %=appcenter-test.software-univention.de
}

install_apps ()
{
	local app rv=0
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-installed.txt; done
	for app in "$@"
	do
		latestversion="$(univention-app list "$app" | egrep '    \w+' | sed 's/^\s*//g' | tail -n1)"
		if [ -n "$(univention-app get "$app=$latestversion" DockerImage)" ]; then
			username="$(ucr get tests/domainadmin/account | sed -e 's/uid=//' -e 's/,.*//')"
			if [ -z "$(ucr get "appcenter/apps/$app/status")" ]; then
				univention-app install "$app" --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
			else
				univention-app upgrade "$app" --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
			fi
		else
			univention-add-app -a --latest "$app" || rv=$?
		fi
	done
	return $rv
}

uninstall_apps ()
{
	local app rv=0
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-uninstalled.txt; done
	for app in "$@"
	do
		if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			username="$(ucr get tests/domainadmin/account | sed -e 's/uid=//' -e 's/,.*//')"
			univention-app remove "$app" --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
		else
			/root/uninstall-app.py -a "$app" || rv=$?
		fi
	done
	return $rv
}

install_apps_master_packages ()
{
	local app rv=0
	for app in "$@"
	do
		if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			continue
		fi
		univention-add-app -m --latest "$app" || rv=$?
	done
	return $rv
}

install_with_unmaintained () {
	local rv=0
	ucr set repository/online/unmaintained=yes
	univention-install --yes "$@" || rv=$?
	ucr set repository/online/unmaintained=no
	return $rv
}

install_ucs_test ()
{
	install_with_unmaintained ucs-test
}

install_apps_test_packages ()
{
	local app rv=0
	ucr set repository/online/unmaintained=yes
	for app in "$@"
	do
		univention-install --yes "ucs-test-$app" || rv=$?
	done
	ucr set repository/online/unmaintained=no
	return $rv
}

install_ucs_test_appcenter_uninstall ()
{
	install_with_unmaintained ucs-test-appcenter-uninstall
}

install_ucsschool ()
{
	case "${ucsschool_release:-scope}" in
		appcenter.test)
			switch_to_test_app_center
			install_apps ucsschool
			;;
		public)
			install_apps ucsschool
			;;
		scope|*)
			local component="repository/online/component/ucsschool_DEVEL"
			ucr set "$component"/description="Development version of UCS@school packages" \
				"$component"/version="$(ucr get version/version)" \
				"$component"/server=updates-test.software-univention.de \
				"$component"=enabled
			echo "install_ucsschool - DEBUG1"
			cat /etc/apt/sources.list.d/20_ucs-online-component.list
			univention-install --yes ucs-school-umc-installer
			echo "install_ucsschool - DEBUG2"
			cat /etc/apt/sources.list.d/20_ucs-online-component.list
			;;
	esac

}

remove_s4connector_tests_and_mark_tests_manual_installed ()
{
	univention-remove --yes ucs-test-s4connector
	apt-mark manual $(apt-mark showauto | grep ^ucs-test-)
}

install_ucs_windows_tools ()
{
	install_with_unmaintained ucs-windows-tools
}

run_apptests ()
{
	run_tests -r apptest "$@"
}

run_minimal_apptests ()
{
	run_apptests -s checks -s appcenter "$@"
}

run_appcenter_uninstall_tests ()
{
	run_tests -s appcenter-uninstall "$@"
}

run_admember_tests ()
{
	run_tests -p skip_admember -p docker "$@"
}

run_adconnector_tests ()
{
	# Test if the failed Jenkins test are timing issues
	sed -i 's|AD_ESTIMATED_MAX_COMPUTATION_TIME=3|AD_ESTIMATED_MAX_COMPUTATION_TIME=16|' /usr/share/ucs-test/55_adconnector/adconnector.sh
	run_tests -s adconnector "$@"
}

run_win_member_gpo_tests ()
{
	run_tests -r windows_gpo_test "$@"
}

run_windows_native_client_tests ()
{
	# tests that require a native windows client in the domain
	run_tests -r native_win_client "$@"
}

run_tests ()
{
	LANG=de_DE.UTF-8 ucs-test -E dangerous -F junit -l "ucs-test.log" -p producttest "$@"
}

run_tests_with_parameters() {
	local s="${test_section:-}"
	case "$s" in
	all_sections|all*) s= ;;
	esac
	ucs-test ${s:+-s "$s"} -E dangerous -F junit -l "ucs-test.log" "$@"
}

run_join_scripts ()
{
	local admin_password="${1:-univention}"

	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		univention-run-join-scripts
	else
 		echo -n "$admin_password" >/tmp/univention
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

do_reboot () {
	reboot
}

install_gpmc_windows ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local ADMIN_ACCOUNT="${3:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'Administrator', 'Univention@99', 445, '$HOST')
win.add_gpo_management_console()
"
}

join_windows_memberserver ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local DNS_SERVER="${3:?Missing DNS server address}"
	local ADMIN_ACCOUNT="${4:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.domain_join('$DNS_SERVER')
"
}

_promote_ad ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local MODE="${3:?Missing mode}"
	local ADMIN_ACCOUNT="${4:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.promote_ad('$MODE', '$MODE')
"
}

promote_ad_w2k12r2 ()
{
	_promote_ad "$1" "$2" "Win2012R2" "$3"
}

promote_ad_w2k12 ()
{
	_promote_ad "$1" "$2" "Win2012" "$3"
}

promote_ad_w2k8r2 ()
{
	_promote_ad "$1" "$2" "Win2008R2" "$3"
}

promote_ad_w2k8 ()
{
	_promote_ad "$1" "$2" "Win2008" "$3"
}

promote_ad_w2k3r2 ()
{
	_promote_ad "$1" "$2" "Win2003R2" "$3"
}

reboot_windows_host ()
{
	local HOST="${1:?Missing host address}"
	local ADMIN_ACCOUNT="${2:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$ADMIN_ACCOUNT', 'Univention@99', 'Administrator', 'Univention@99', 445, '$HOST')
win.reboot_remote_win_host()
"
}

shutdown_windows_host ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN_MODE="${2:-False}"
	local ADMIN_ACCOUNT="${3:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.shutdown_remote_win_host($DOMAIN_MODE)
"
}

set_windows_gateway ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local GATEWAY="${3:?Missing gateway address}"
	local ADMIN_ACCOUNT="${4:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.set_gateway('$GATEWAY')
"
}

create_ad_user_and_add_the_user_to_the_group ()
{
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local NEW_ADMIN_USERNAME="${3:?Missing admin user name}"
	local NEW_ADMIN_PASSWORD="${4:?Missing admin password}"
	local NEW_ADMIN_GROUP="${5:?Missing group name}"
	local ADMIN_ACCOUNT="${6:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.create_user_and_add_to_group('$NEW_ADMIN_USERNAME', '$NEW_ADMIN_PASSWORD', '$NEW_ADMIN_GROUP')
"
}

set_administrator_dn_for_ucs_test ()
{
	local dn="$(univention-ldapsearch sambaSid=*-500 -LLL dn | sed -ne 's|dn: ||p')"
	ucr set tests/domainadmin/account="$dn"
}

set_administrator_password_for_ucs_test ()
{
	local password="$1"

	ucr set tests/domainadmin/pwd="$password"
	echo -n "$password" >/var/lib/ucs-test/pwdfile
}


# vim:set filetype=sh ts=4:
