#!/bin/bash
#
# Copyright 2013-2015 Univention GmbH
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

if [ "${0##*/}" = 'utils.sh' ] && [ -n "$1" ]
then
	trap '"$@"' EXIT
fi

basic_setup () {
	if grep "QEMU Virtual CPU" /proc/cpuinfo ; then
		echo "KVM detected"
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
		# wait until Univention System Setup is running and profile file has been moved
		while ! pgrep -f /opt/firefox/firefox ; do
			sleep 1s
			echo -n .
		done
		sleep 5s
		if [ -f /var/cache/univention-system-setup/profile.bak ] ; then
			mv /var/cache/univention-system-setup/profile.bak /var/cache/univention-system-setup/profile
		fi
	else
		echo "Assuming Amazon Cloud"
		echo 'supersede routers 10.210.216.13;' >/etc/dhcp/dhclient.conf.local
		echo -e '#!/bin/sh\nip route replace default via 10.210.216.13' >/etc/network/if-up.d/z_route
		chmod +x /etc/network/if-up.d/z_route
		/etc/network/if-up.d/z_route
		sleep 10 # just wait a few seconds to give the amazone cloud some time
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
	fi
}

jenkins_updates () {
	local version_version version_patchlevel version_erratalevel target
	target="$(echo "${JOB_NAME:-}"|sed -rne 's,.*/UCS-([0-9]+\.[0-9]+-[0-9]+)/.*,\1,p')"
	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Starting from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."

	case "${release_update:-}" in
	public) upgrade_to_latest --updateto "$target" "$@" ;;
	testing) upgrade_to_testing --updateto "$target" "$@" ;;
	none|"") ;;
	*) echo "Unknown release_update='$release_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Continuing from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."

	case "${errata_update:-}" in
	testing) upgrade_to_latest_test_errata "$@" ;;
	public) upgrade_to_latest_errata "$@" ;;
	none|"") ;;
	*) echo "Unknown errata_update='$errata_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Finished at ${version_version}-${version_patchlevel}+${version_erratalevel}"
}

upgrade_to_latest_errata () {
	# Bug #34336: needs further discussion if release or only errata updates are expected
	local current="$(ucr get version/version)-$(ucr get version/patchlevel)"
	upgrade_to_latest --updateto "$current" "$@"
}

upgrade_to_latest_test_errata () {
	local current prev=DUMMY
	while current="$(ucr get version/version)-$(ucr get version/patchlevel)" && [ "$current" != "$prev" ]
	do
		/root/activate-3.2-errata-test-scope.sh
		upgrade_to_latest_errata "$@"
		prev="$current"
	done
}

upgrade_to_testing () {
	ucr set repository/online/server=updates-test.software-univention.de
	upgrade_to_latest --updateto '3.3-99' "$@"
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

run_setup_join () {
	local srv
	/usr/lib/univention-system-setup/scripts/setup-join.sh
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do invoke-rc.d "$srv" restart; done
	ucr unset --forced update/available
}

run_setup_join_on_non_master () {
	local srv
	ucr set nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	echo -n "univention" >/tmp/univention
	/usr/lib/univention-system-setup/scripts/setup-join.sh --dcaccount Administrator --password_file /tmp/univention
	ucr set apache2/startsite='ucs-overview/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do invoke-rc.d "$srv" restart; done
	ucr unset --forced update/available
}

wait_for_reboot () {
	local i=0
	while [ $i -lt 100 ]; do pidof apache2 && break; sleep 1; i=$((1+i));done
}

switch_to_test_app_center ()
{
	ucr set repository/app_center/server=appcenter-test.software-univention.de
}

switch_components_to_test_app_center ()
{
	ucr search --brief --value appcenter.software-univention.de | \
		grep 'repository/online/component/.*/server' | \
		awk -F ':' '{print $1}' | \
		xargs -I % ucr set %=appcenter-test.software-univention.de
}

install_apps () {
	local app
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-installed.txt; done
	for app in "$@"; do univention-add-app -a --latest "$app"; done
}

install_apps_master_packages () {
	local app
	for app in "$@"; do univention-add-app -m --latest "$app"; done
}

install_ucs_test () {
	ucr set repository/online/unmaintained=yes
	univention-install --yes ucs-test
	ucr set repository/online/unmaintained=no
}

install_apps_test_packages () {
	local app
	ucr set repository/online/unmaintained=yes
	for app in "$@"; do univention-install --yes "ucs-test-$app" || true; done
	ucr set repository/online/unmaintained=no
}

install_ucs_windows_tools () {
	ucr set repository/online/unmaintained=yes
	univention-install --yes ucs-windows-tools
	ucr set repository/online/unmaintained=no
}

run_apptests () {
	run_tests -r apptest "$@"
}

run_tests () {
	[ ! -e /DONT_START_UCS_TEST ] && LANG=de_DE.UTF-8 ucs-test -E dangerous -F junit -l "ucs-test.log" -p producttest "$@"
}

run_join_scripts () {
	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		univention-run-join-scripts
	else
 		echo -n "univention" >/tmp/univention
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

assert_version () {
	local requested_version="$1"
	local version

	eval "$(ucr shell '^version/(version|patchlevel)$')"
	version="$version_version-$version_patchlevel"
	echo "Requested version $requested_version"
	echo "Current version $version"
	if [ "$requested_version" != "$version" ]; then
		echo "Creating /DONT_START_UCS_TEST"
		touch /DONT_START_UCS_TEST
		exit 1
	fi
}

assert_join () {
	if ! univention-check-join-status; then
		echo "Creating /DONT_START_UCS_TEST"
		touch /DONT_START_UCS_TEST
		exit 1
	fi
}

assert_packages () {
	local packages="$@"
	for package in $packages; do
		local installed=$(dpkg-query -W -f '${status}' "$package")
    	if [ "$installed" != "install ok installed" ]; then
			echo "Failed: package status of $package is $installed"
			echo "Creating /DONT_START_UCS_TEST"
			touch /DONT_START_UCS_TEST
			exit 1
		fi
	done
}

promote_ad_w2k12 () {
	local HOST="${1:?host address}"
	local DOMAIN="${2:?domain name}"
	python -c "from sys import argv
import univention.winexe
win=univention.winexe.WinExe(argv[2], 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, argv[1])
win.promote_ad('Win2008R2', 'Win2008R2')
" "$@"
}

promote_ad_w2k8 () {
	local HOST="${1:?host address}"
	local DOMAIN="${2:?domain name}"
	python -c "from sys import argv
import univention.winexe
win=univention.winexe.WinExe(argv[2], 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, argv[1])
win.promote_ad('Win2008', 'Win2008')
" "$@"
}

shutdown_windows_host () {
	local HOST="${1:?host address}"
	python -c "from sys import argv
import univention.winexe
win=univention.winexe.WinExe('dummydomain', 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, argv[1])
win.shutdown_remote_win_host()
" "$@"
}

set_gateway () {
	local HOST="${1:?host address}"
	local DOMAIN="${2:?domain name}"
	local GATEWAY="${3:?gateway address}"
	python -c "from sys import argv
import univention.winexe
win=univention.winexe.WinExe(argv[2], 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, argv[1])
win.set_gateway(argv[3])
" "$@"
}

migrate_postgres84_to_91 ()
{
	# http://sdb.univention.de/1292
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod -x /usr/sbin/univention-pkgdb-scan
	service postgresql stop
	rm -rf /etc/postgresql/9.1
	apt-get install --reinstall postgresql-9.1
	pg_dropcluster 9.1 main --stop
	service postgresql start
	test -e /var/lib/postgresql/9.1/main && mv /var/lib/postgresql/9.1/main /var/lib/postgresql/9.1/main.old
	pg_upgradecluster 8.4 main
	ucr commit /etc/postgresql/9.1/main/*
	chown -R postgres:postgres /var/lib/postgresql/9.1
	service postgresql restart
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod +x /usr/sbin/univention-pkgdb-scan
	pg_dropcluster 8.4 main --stop
	dpkg -P postgresql-8.4
}

# vim:set filetype=sh ts=4:
