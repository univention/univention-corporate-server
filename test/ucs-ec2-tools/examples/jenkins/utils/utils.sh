#!/bin/bash
#
# Copyright 2013-2014 Univention GmbH
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
		echo -e "#!/bin/sh\nroute del default ; route add default gw 10.210.216.13" >>/etc/network/if-up.d/z_route
		chmod +x /etc/network/if-up.d/z_route
		/etc/network/if-up.d/z_route
		sleep 10 # just wait a few seconds to give the amazone cloud some time
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
	fi
	while pgrep -f "/etc/init.d/rc 2" && ! pgrep -f /opt/firefox/firefox ; do
		sleep 1s
	done
	sleep 5s
	if [ -f /var/cache/univention-system-setup/profile.bak ] ; then
		mv /var/cache/univention-system-setup/profile.bak /var/cache/univention-system-setup/profile
	fi
	bug37459_postfix_pfs
}
bug37459_postfix_pfs () {
	local FILE='/usr/share/univention-mail-postfix/create-dh-parameter-files.sh'
	dpkg-divert --local --rename --divert "${FILE}.ucs-test" --add "$FILE"
	ln -s /bin/true "$FILE"

	if [ ! /dev/urandom -ef /dev/random ]
	then
		mv /dev/random /dev/random.orig
		ln -f /dev/urandom /dev/random
	fi
}

upgrade_to_latest_errata ()
{
	local current="$(ucr get version/version)-$(ucr get version/patchlevel)"
	upgrade_to_latest --updateto "$current"
}

upgrade_to_latest_test_errata ()
{
	local current prev=DUMMY rc=0
	while current="$(ucr get version/version)-$(ucr get version/patchlevel)" && [ "$current" != "$prev" ]
	do
		if [ -x /root/activate-errata-test-scope.sh ]
		then
			/root/activate-errata-test-scope.sh
		fi
		upgrade_to_latest
		rc=$?
		prev="$current"
	done
	return $rc
}

upgrade_to_testing ()
{
	ucr set repository/online/server=testing.univention.de
	upgrade_to_latest
}

upgrade_to_latest () {
	declare -i max=300 rv delay=30
	while true
	do
		univention-upgrade --noninteractive --ignoreterm --ignoressh "$@"
		rv="$?"
		case "$rv" in
		0) return 0 ;;
		5) delay=30 ;;
		*) delay=300 ;;
		esac
		echo "ERROR: univention-upgrade failed exitcode $rv"
		ps faxwww
		ucr search --brief --non-empty update/check
		max+=-$delay
		[ $max -ge 0 ] || return "$rv"
		sleep "$delay"  # Workaround for Bug #31561
	done
}

run_setup_join ()
{
	local srv
	/usr/lib/univention-system-setup/scripts/setup-join.sh
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do invoke-rc.d "$srv" restart; done
	ucr unset --forced update/available
}

run_setup_join_on_non_master ()
{
	local admin_password="${1:-univention}"
	local srv
	ucr set nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	echo -n "$admin_password" >/tmp/univention
	/usr/lib/univention-system-setup/scripts/setup-join.sh --dcaccount Administrator --password_file /tmp/univention
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do invoke-rc.d "$srv" restart; done
	ucr unset --forced update/available
}

wait_for_reboot ()
{
	local i
	for ((i=0;i<100;i++)); do pidof apache2 && break; sleep 1; done
}

switch_to_test_app_center ()
{
	ucr set repository/app_center/server=appcenter.test.software-univention.de
}

install_apps ()
{
	local app
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-installed.txt; done
	for app in "$@"; do univention-add-app -a --latest "$app"; done
}

uninstall_apps ()
{
	local app
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-uninstalled.txt; done
	for app in "$@"; do /root/uninstall-app.py -a "$app"; done
}

install_apps_master_packages ()
{
	local app
	for app in "$@"; do univention-add-app -m --latest "$app"; done
}

install_ucs_test ()
{
	ucr set repository/online/unmaintained=yes
	univention-install --yes ucs-test
	ucr set repository/online/unmaintained=no
}

install_apps_test_packages ()
{
	local app
	ucr set repository/online/unmaintained=yes
	for app in "$@"; do univention-install --yes "ucs-test-$app" || true; done
	ucr set repository/online/unmaintained=no
}

install_ucs_test_appcenter_uninstall ()
{
	ucr set repository/online/unmaintained=yes
	univention-install --yes ucs-test-appcenter-uninstall
	ucr set repository/online/unmaintained=no
}

install_ucs_windows_tools ()
{
	ucr set repository/online/unmaintained=yes
	univention-install --yes ucs-windows-tools
	ucr set repository/online/unmaintained=no
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
	run_tests -p skip_admember "$@"
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
	local HOST="$1"
	local DOMAIN="$2"
	local ADMIN_ACCOUNT="${3:-administrator}"
	
        if [[ ! -z "$HOST" ]] && [[ ! -z "$DOMAIN" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'Administrator', 'Univention@99', 445, '$HOST')
win.add_gpo_management_console()
"
	else
		echo "You must specify a host address, domain name, dns server address."
	fi
}

join_windows_memberserver ()
{
	local HOST="$1"
	local DOMAIN="$2"
	local DNS_SERVER="$3"
	local ADMIN_ACCOUNT="${4:-administrator}"
	
        if [[ ! -z "$HOST" ]] && [[ ! -z "$DOMAIN" ]] && [[ ! -z "$DNS_SERVER" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.domain_join('$DNS_SERVER')
"
	else
		echo "You must specify a host address, domain name, dns server address."
	fi
}

_promote_ad ()
{
	local HOST="$1"
	local DOMAIN="$2"
	local MODE="$3"
	local ADMIN_ACCOUNT="${4:-administrator}"
	if [[ ! -z "$HOST" ]] && [[ ! -z "$DOMAIN" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.promote_ad('$MODE', '$MODE')
"
	else
		echo "You must specify an host address domain name."
	fi
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
	local HOST="$1"
	local ADMIN_ACCOUNT="${2:-administrator}"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$ADMIN_ACCOUNT', 'Univention@99', 'Administrator', 'Univention@99', 445, '$HOST')
win.reboot_remote_win_host()
"
}

shutdown_windows_host ()
{
	local HOST="$1"
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
	local HOST="$1"
	local DOMAIN="$2"
	local GATEWAY="$3"
	local ADMIN_ACCOUNT="${4:-administrator}"
	if [[ ! -z "$HOST" ]] && [[ ! -z "$GATEWAY" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.set_gateway('$GATEWAY')
"
	else
		echo "You must specify an host address domain name and a gateway."
	fi
}

create_ad_user_and_add_the_user_to_the_group ()
{
	local HOST="$1"
	local DOMAIN="$2"
	local NEW_ADMIN_USERNAME="$3"
	local NEW_ADMIN_PASSWORD="$4"
	local NEW_ADMIN_GROUP="$5"
	local ADMIN_ACCOUNT="${6:-administrator}"
	if [ -n "$HOST" -a -n "$NEW_ADMIN_USERNAME" -a -n "$NEW_ADMIN_PASSWORD" -a -n "$NEW_ADMIN_GROUP" ]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$ADMIN_ACCOUNT', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.create_user_and_add_to_group('$NEW_ADMIN_USERNAME', '$NEW_ADMIN_PASSWORD', '$NEW_ADMIN_GROUP')
"
	else
		echo "Please specify an host address, a domain name, an admin username, an admin password and a group name."
	fi
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
