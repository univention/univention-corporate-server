#!/bin/bash
#
# Copyright 2013-2017 Univention GmbH
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

set -x

is_ec2 () {
	test "$(ucr get updater/identify)" = "UCS (EC2 Test)" && return 0
	return 1
}

basic_setup () {
	# force dpkg not to call "sync" during package installations/updates
	echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/force-unsafe-io
	if grep "QEMU Virtual CPU" /proc/cpuinfo ; then
		echo "KVM detected"
		ucr set --force updater/identify="UCS (EC2 Test)"
	elif ip -4 addr show | grep -Fq 'inet 10.210.'
	then
		echo "Assuming Amazon Cloud"
		# Bug #46993: Remove OpenDNS resolver - use AmazonProvidedDNS
		sed -i -e '/^nameserver 208.67.22[02].22[02]/d' /etc/resolv.conf
		grep nameserver /etc/resolv.conf|cat -n|sed -re 's,^\s*([0-9]+)\s*(nameserver)\s*(.*),\2\1=\3 dns/forwarder\1=\3,'|xargs ucr set nameserver1= nameserver2= nameserver3= dns/forwarder1= dns/forwarder2= dns/forwarder3=
		ucr set --force updater/identify="UCS (EC2 Test)"
		if grep -F /dev/vda /boot/grub/device.map && [ -b /dev/xvda ] # Bug 36256
		then
			/usr/sbin/grub-mkdevicemap
			echo set grub-pc/install_devices /dev/xvda | debconf-communicate
		fi
	fi
	ucr set update/check/cron/enabled=false update/check/boot/enabled=false
	service cron reload || true
	# wait until Univention System Setup is running and profile file has been moved
	while pgrep -f "/etc/init.d/rc 2" && ! pgrep -f "startxwithfirefox" ; do
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
	ucr set update43/checkfilesystems=no
	local version_version version_patchlevel version_erratalevel target rc=0
	target="$(echo "${JOB_NAME:-}"|sed -rne 's,.*/UCS-([0-9]+\.[0-9]+-[0-9]+)/.*,\1,p')"
	# Update UCS@school instances always to latest patchlevel version
	[ -z "$target" ] && target="$(echo "${JOB_NAME:-}"|sed -rne 's,^UCSschool-([0-9]+\.[0-9]+)/.*,\1-99,p')"

	test -n "$TARGET_VERSION" && target="$TARGET_VERSION"
	test -n "$RELEASE_UPDATE" && release_update="$RELEASE_UPDATE"
	test -n "$ERRATA_UPDATE" && errata_update="$ERRATA_UPDATE"

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Starting from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."
	echo "release_update=$release_update"

	case "${release_update:-}" in
	public) upgrade_to_latest --updateto "$target" || rc=$? ;;
	testing) upgrade_to_testing --updateto "$target" || rc=$? ;;
	none|"") ;;
	*) echo "Unknown release_update='$release_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Continuing from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."
	echo "errata_update=$errata_update"

	test -n "$ERRATA_TESTS" && errata_update=testing

	case "${errata_update:-}" in
	testing) upgrade_to_latest_test_errata || rc=$? ;;
	public) upgrade_to_latest_errata || rc=$? ;;
	none|"") ;;
	*) echo "Unknown errata_update='$errata_update'" >&1 ; exit 1 ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Finished at ${version_version}-${version_patchlevel}+${version_erratalevel}"
	return $rc
}

upgrade_to_latest_patchlevel () {
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
	ucr set update42/skip/updater/check=yes
	set_repository_to_testing
	upgrade_to_latest "$@"
}

set_repository_to_testing () {
	if is_ec2; then
		ucr set repository/online/server=updates-test.software-univention.de
	else
		ucr set repository/online/server=updates-test.knut.univention.de
	fi
}

check_repository_to_testing () {
	local testing=${1:?missing testing switch}
	if [ "$testing" = "testing" ]; then
		set_repository_to_testing
	fi
	return 0
}

upgrade_to_latest () {
	local rv=0
	ucr set repository/online=true
	_upgrade_to_latest "$@" || rv=$?
	return $rv
}
_upgrade_to_latest () {
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

# temp. patch to retry source.list commit and apt-get update after error
patch_setup_join () {
	local script='{ set -x; nscd -i hosts; grep -H . /etc/resolv.conf /etc/apt/sources.list.d/15_ucs-online-version.list; ifconfig; ping -c 4 "$(ucr get repository/online/server)"; nslookup "$(ucr get repository/online/server)"; sleep 60; ucr commit /etc/apt/sources.list.d/*.list; apt-get update; } ; grep -H . /etc/apt/sources.list.d/15_ucs-online-version.list'
	sed -i "s~^apt-get update\$~& || $script~" /usr/lib/univention-system-setup/scripts/setup-join.sh
}
_fix_ssh47233 () { # Bug #47233: ssh connection stuck on reboot
	local g t
	g='/etc/pam.d/common-session' t='/etc/univention/templates/files/etc/pam.d/common-session.d/10univention-pam_common'
	grep -Fqs 'pam_systemd.so' "$g" && return 0
	grep -Fqs 'pam_systemd.so' "$t" ||
		echo "session optional        pam_systemd.so" >>"$t"
	ucr commit "$g"
}

run_setup_join () {
	local srv rv=0
	patch_setup_join # temp. remove me
	/usr/lib/univention-system-setup/scripts/setup-join.sh ${1:+"$@"} || rv=$?
	ucr set apache2/startsite='univention/' # Bug #31682
	for srv in univention-management-console-server univention-management-console-web-server apache2
	do
		invoke-rc.d "$srv" restart
	done
	ucr unset --forced update/available

	# No this breaks univention-check-templates -> 00_checks.81_diagnostic_checks.test _fix_ssh47233  # temp. remove me
	return $rv
}

run_setup_join_on_non_master () {
	local admin_password="${1:-univention}" rv=0 nameserver1
	nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	if [ -n  "$nameserver1" ]; then
		ucr set nameserver1="$nameserver1"
	fi
	printf '%s' "$admin_password" >/tmp/univention
	run_setup_join --dcaccount Administrator --password_file /tmp/univention || rv=$?
	return $rv
}

wait_until_update_server_is_resolvable () {
	local i=0
	local servers=""
	is_ec2 && servers="updates.software-univention.de updates-test.software-univention.de" || server="updates.knut.univention.de updates-test.knut.univention.de"
	for server in $servers; do
		while [ $i -lt 900 ]
		do
			host $server >/dev/null && break
			sleep 1
			i=$((i + 1))
		done
		if [ $i = 900 ]; then
			echo "WARNING: host $server did not succeed after 900 seconds"
			return 1
		else
			echo "host $server succeeded after $i seconds"
			continue
		fi
	done
}

wait_for_reboot () {
	local i=0 rv=0
	while [ $i -lt 900 ]
	do
		pidof apache2 && break
		sleep 1
		i=$((i + 1))
	done
	if [ $i = 900 ]; then
		echo "WARNING: wait_for_reboot: Did not find running apache after 900 seconds"
		rv=1
	fi
	# Wait a little bit more otherwise other services are not available
	sleep 30
	# stop kdm
	/etc/init.d/kdm stop || true
	service kdm stop || true
	return $rv
}

wait_for_replication () {
	local timeout=${1:-3600}
	local steps=${2:-10}
	local timestamp=$(date +"%s")
	echo "Waiting for replication..."
	while ! /usr/lib/nagios/plugins/check_univention_replication; do
		if [ $((timestamp+timeout)) -lt $(date +"%s") ]; then
			echo "ERROR: replication incomplete."
			return 1
		fi
		sleep $steps
	done
	return 0
}

wait_for_setup_process () {
	local i
	local setup_file="/var/www/ucs_setup_process_status.json"
	sleep 10
	for i in $(seq 1 1200); do
		if [ ! -e "$setup_file" ]; then
			return 0
		fi
		sleep 3
	done
	echo "setup did not finish after 3600s, timeout"
	return 1
}

switch_to_test_app_center () {
	local app rv=0
	ucr set repository/app_center/server=appcenter-test.software-univention.de update/secure_apt=no appcenter/index/verify=no
	[ -x "$(which univention-app)" ] || return 1
	univention-install --yes univention-appcenter-dev
	univention-app dev-use-test-appcenter
	if [ -e /var/cache/appcenter-installed.txt ]; then
		for app in $(< /var/cache/appcenter-installed.txt); do
			if univention-app get "$app" DockerImage | grep -q ucs-appbox; then
				# update appbox at this point
				univention-app shell "$app" univention-upgrade --noninteractive --disable-app-updates
				univention-app shell "$app" univention-install -y univention-appcenter-dev || rv=$?
				univention-app shell "$app" univention-app dev-use-test-appcenter || rv=$?
			fi
			#if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			#	univention-app shell "$app" univention-install -y univention-appcenter-dev || rv=$?
			#	univention-app shell "$app" univention-app dev-use-test-appcenter || rv=$?
			#fi
		done
	fi
	return $rv
}

switch_components_to_test_app_center () {
	ucr search --brief --value appcenter.software-univention.de |
		grep 'repository/online/component/.*/server' |
		awk -F ':' '{print $1}' |
		xargs -I % ucr set %=appcenter-test.software-univention.de
}

install_apps () {
	local app rv=0
	for app in "$@"; do echo "$app" >>/var/cache/appcenter-installed.txt; done
	for app in "$@"
	do
		username="$(ucr get tests/domainadmin/account | sed -e 's/uid=//' -e 's/,.*//')"
		if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			if [ -z "$(ucr get "appcenter/apps/$app/status")" ]; then
				univention-app install "$app" --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
			else
				univention-app upgrade "$app" --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
			fi
		else
			univention-app install --noninteractive "$app" || rv=$?
			univention-run-join-scripts -dcaccount "$username" -dcpwd "$(ucr get tests/domainadmin/pwdfile)"
		fi
	done
	return $rv
}

uninstall_apps () {
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

install_apps_master_packages () {
	local app rv=0
	for app in "$@"
	do
		[ -n "$(univention-app get "$app" DockerImage)" ] && continue
		univention-app install --noninteractive --only-master-packages "$app" || rv=$?
	done
	username="$(ucr get tests/domainadmin/account | sed -e 's/uid=//' -e 's/,.*//')"
	univention-app register --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)"
	return $rv
}

install_with_unmaintained () {
	local rv=0
	wait_for_repo_server || rv=$?
	ucr set repository/online=true repository/online/unmaintained=yes
	cat /etc/apt/sources.list.d/15_ucs-online-version.list
	univention-install --yes "$@" || rv=$?
	ucr set repository/online/unmaintained=no
	return $rv
}

wait_for_repo_server () {
	eval "$(ucr shell 'repository/online/server')"
	repository_online_server=${repository_online_server#https://}
	repository_online_server=${repository_online_server#http://}
	repository_online_server=${repository_online_server%%/*}
	for i in $(seq 1 300); do
		ping -c 2 "$repository_online_server" && return 0
		sleep 1
	done
	return 1
}

install_ucs_test () {
	wait_for_repo_server || return 1
	install_with_unmaintained ucs-test
	install_selenium || install_selenium
	# The AD Member Jenkins tests sometimes have network problems, so executing it twice.
}

install_ucs_test_from_errata_test () {
	wait_for_repo_server || return 1
	bash /root/activate-errata-test-scope.sh || return 1
	install_ucs_test || return 1
}

install_ucs_test_checks_from_errata_test () {
	local rv=0
	bash /root/activate-errata-test-scope.sh || rv=$?
	install_with_unmaintained ucs-test-checks "$@" || rv=$?
	return $rv
}

install_from_errata_test () {
	local rv=0
	bash /root/activate-errata-test-scope.sh || rv=$?
	install_with_unmaintained "$@" || rv=$?
	return $rv
}

install_additional_packages () {
	[ $# -ge 1 ] || return 0
	install_with_unmaintained "$@"
}

install_apps_test_packages () {
	local app rv=0
	ucr set repository/online/unmaintained=yes
	for app in "$@"
	do
		if [ -n "$(univention-app get $app DockerImage)" ]; then
			univention-app shell "$app" apt-get download "ucs-test-$app" &&
			dpkg -i /var/lib/docker/overlay/$(ucr get appcenter/apps/$app/container)/merged/ucs-test-${app}_*.deb &&
			univention-install -f --yes || rv=$?
		else
			univention-install --yes "ucs-test-$app" || rv=$?
		fi
	done
	ucr set repository/online/unmaintained=no
	return $rv
}

install_ucs_test_appcenter_uninstall () {
	install_with_unmaintained ucs-test-appcenter-uninstall
}

create_DONT_START_UCS_TEST () {
	echo "-----------------------------------------------------------------------------------"
	echo "$@"
	echo "Creating /DONT_START_UCS_TEST"
	echo "-----------------------------------------------------------------------------------"
	touch /DONT_START_UCS_TEST
}

prevent_ucstest_on_fail () {
	local rv=0
	"$@" || rv=$?
	if [ ! "$rv" = "0" ] ; then
		create_DONT_START_UCS_TEST "FAILED: prevent_ucstest_on_fail $@"
	fi
	return $rv
}

activate_ucsschool_devel_scope () {
	local component="repository/online/component/ucsschool_DEVEL"
	ucr set "$component"/description="Development version of UCS@school packages" \
		"$component"/version="$(ucr get version/version)" \
		"$component"/server=https://updates-test.software-univention.de \
		"$component"=enabled
}

ucsschool_scope_enabled () {
	[ "${UCSSCHOOL_RELEASE:-scope}" = "scope" ]
}

install_ucsschool () {
	local rv=0

	# Bug #50690: ucs-school-webproxy would set this to yes. Which breaks out test environment
	ucr set --force dhcpd/authoritative=no

	case "${UCSSCHOOL_RELEASE:-scope}" in
		appcenter.test)
			switch_to_test_app_center || rv=$?
			install_apps ucsschool || rv=$?
			;;
		public)
			install_apps ucsschool || rv=$?
			;;
		scope|*)
			activate_ucsschool_devel_scope || rv=$?
			echo "install_ucsschool - DEBUG1"
			# Ensure ucsschool is a registered app
			echo "ucsschool" >>/var/cache/appcenter-installed.txt
			cat /etc/apt/sources.list.d/20_ucs-online-component.list
			univention-app install --noninteractive ucsschool || rv=$?
			echo "install_ucsschool - DEBUG2"
			cat /etc/apt/sources.list.d/20_ucs-online-component.list
			;;
	esac
	return $rv
}

install_coverage () {
	install_with_unmaintained python-pip python-all-dev python-all-dbg python-setuptools python-docutils python-pkg-resources
	pip install coverage
}

remove_s4connector_tests_and_mark_tests_manual_installed () {
	univention-remove --yes ucs-test-s4connector
	apt-mark manual $(apt-mark showauto | grep ^ucs-test-)
}

install_ucs_windows_tools () {
	install_with_unmaintained ucs-windows-tools
}

install_selenium () {
	#install_with_unmaintained chromium-browser chromedriver chromium python-pip xvfb
	# install old version until Bug 48856 is fixed
	local chromium_version="71.0.3578.80-1~deb9u1"
	install_with_unmaintained python-pip xvfb chromium="$chromium_version" chromium-driver="$chromium_version" python-xvfbwrapper
	pip install selenium==3.6.0
}

run_apptests () {
	local app
	# some tests create domaincontroller_master objects, the listener ldap_server.py
	# sets these objects as ldap/server/name ldap/master in the docker container
	# until this is fixed, force the variables in the docker container
	for app in $(< /var/cache/appcenter-installed.txt); do
		if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			univention-app shell "$app" bash -c 'eval "$(ucr shell)"; test -n "$ldap_server_name" && ucr set --force ldap/server/name="$ldap_server_name"'
			univention-app shell "$app" bash -c 'eval "$(ucr shell)"; test -n "$ldap_master" && ucr set --force ldap/master="$ldap_master"'
			univention-app shell "$app" bash -c 'eval "$(ucr shell)"; test -n "$kerberos_adminserver" && ucr set --force kerberos/adminserver="$kerberos_adminserver"'
		fi
	done

	run_tests -r apptest "$@"
}

run_minimal_tests () {
	run_tests -s checks "$@"
}

run_minimal_apptests () {
	run_apptests -s checks -s appcenter "$@"
}

run_appcenter_uninstall_tests () {
	run_tests -s appcenter-uninstall "$@"
}

run_admember_tests () {
	ad_member_fix_udm_rest_api
	run_tests -p skip_admember -p docker "$@"
}

ad_member_fix_udm_rest_api () {  # workaround for Bug #50527
	ucr unset directory/manager/rest/authorized-groups/domain-admins
	univention-run-join-scripts --force --run-scripts 22univention-directory-manager-rest.inst
	service univention-directory-manager-rest restart
}

run_adconnector_tests () {
	# Test if the failed Jenkins test are timing issues
	sed -i 's|AD_ESTIMATED_MAX_COMPUTATION_TIME=3|AD_ESTIMATED_MAX_COMPUTATION_TIME=16|' /usr/share/ucs-test/55_adconnector/adconnector.sh
	run_tests -s checks -s adconnector "$@"
}

run_win_member_gpo_tests () {
	run_tests -r windows_gpo_test "$@"
}

run_windows_native_client_tests () {
	# tests that require a native windows client in the domain
	run_tests -r native_win_client "$@"
}

run_samba_dc_tests () {
	assert_join || return 1
	# just a test to make 81_diagnostic_checks.test happy
	samba-tool ntacl sysvolreset || true
	# Bug 48426
	/etc/init.d/samba restart
	local password="${1:-univention}"
	set_administrator_dn_for_ucs_test || return 1
	set_administrator_password_for_ucs_test "$password" || return 1
	install_ucs_test_checks_from_errata_test ucs-test-samba4 || return 1
	run_minimal_tests -s samba4
	return 0
}

run_ucsschool_tests () {
	local test_group="$1"
	declare -a test_args=()
	# following list have to be in sync with EC2Tools.groovy ==> addUASSinglEnvAxes/addUASMultiEnvAxes
	for i in base1 import1 import2 import3 import4 ; do
		[ "$test_group" != "$i" ] && test_args+=("--prohibit=ucsschool_${i}")
		[ "$(echo "$test_group" | sed -re 's/[0-9]+$//')" == "import" ] && test_args+=("--section=ucsschool")
	done
	run_apptests --prohibit=SKIP-UCSSCHOOL "${test_args[@]}"
}

run_tests () {
	if [ -e /DONT_START_UCS_TEST ] ; then
		echo "-----------------------------------------------------------------------------------"
		echo "File /DONT_START_UCS_TEST exists - skipping ucs-test!"
		echo "-----------------------------------------------------------------------------------"
		return 1
	fi
	if [ "$COVERAGE_REPORT" = "true" ]; then
		GENERATE_COVERAGE_REPORT="--with-coverage --coverage-show-missing --coverage-output-directory=/var/log/univention/coverage"
		install_with_unmaintained python-pip
		pip install coverage
	fi
	dpkg-query -W -f '${Status}\t${binary:Package}\t${Version}\n' > "packages-under-test.log"

	# check is ucs-test run is allowed
	if [ -n "$UCS_TEST_RUN" -a "$UCS_TEST_RUN" = "false" ]; then
		echo "ucs-test disabled by env UCS_TEST_RUN=$UCS_TEST_RUN"
		return 0
	fi

	LANG=de_DE.UTF-8 ucs-test -E dangerous -F junit -l "ucs-test.log" -p producttest $GENERATE_COVERAGE_REPORT "$@"
}

run_tests_with_parameters () {
	local s="${test_section:-}"
	case "$s" in
	all_sections|all*) s= ;;
	esac
	run_tests ${s:+-s "$s"} "$@"
}

run_join_scripts () {
	local admin_password="${1:-univention}"

	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		univention-run-join-scripts
	else
		echo -n "$admin_password" >/tmp/univention
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

run_rejoin () {
	local admin_password="${1:-univention}"

	echo -n "$admin_password" >/tmp/univention
	univention-join -dcaccount Administrator -dcpwd /tmp/univention
}

do_reboot () {
	nohup shutdown -r now &
	sleep 1
	exit
}

assert_version () {
	local requested_version="$1"
	local version version_version version_patchlevel

	eval "$(ucr shell '^version/(version|patchlevel)$')"
	version="$version_version-$version_patchlevel"
	echo "Requested version $requested_version"
	echo "Current version $version"
	if [ "$requested_version" != "$version" ]; then
		create_DONT_START_UCS_TEST "FAILED: assert_version $requested_version == $version"
		exit 1
	fi
	return 0
}

assert_minor_version () {
	local requested_version="$1" version_version
	eval "$(ucr shell '^version/version$')"
	echo "Requested minor version $requested_version"
	echo "Current minor version $version_version"
	if [ "$requested_version" != "$version_version" ]; then
		create_DONT_START_UCS_TEST "FAILED: assert_minor_version $requested_version == $version_version"
		exit 1
	fi
	return 0
}

assert_join () {
	# sometimes univention-check-join-status fails because the ldap server is restarted
	# and not available at this moment, so try it three times
	for i in $(seq 1 3); do
		univention-check-join-status
		test $? -eq 0 && return 0
		sleep 10
	done
	create_DONT_START_UCS_TEST "FAILED: univention-check-join-status"
	return 1
}

assert_adconnector_configuration () {
	if [ -z "$(ucr get connector/ad/ldap/host)" ]; then
		create_DONT_START_UCS_TEST "FAILED: assert_adconnector_configuration"
		exit 1
	fi
	return 0
}

assert_packages () {
	local package
	for package in "$@"
	do
		local installed=$(dpkg-query -W -f '${status}' "$package")
		if [ "$installed" != "install ok installed" ]; then
			create_DONT_START_UCS_TEST "Failed: package status of $package is $installed"
			exit 1
		fi
	done
	return 0
}

install_gpmc_windows () {
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local DOMAIN_ADMIN_ACCOUNT="${3:-administrator}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.add_gpo_management_console()
"
}

join_windows_memberserver () {
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local DNS_SERVER="${3:?Missing DNS server address}"
	local DOMAIN_ADMIN_ACCOUNT="${4:-administrator}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.domain_join('$DNS_SERVER')
"
}

reboot_windows_host () {
	local HOST="${1:?Missing host address}"
	local DOMAIN_ADMIN_ACCOUNT="${2:-administrator}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.reboot_remote_win_host()
"
}

shutdown_windows_host () {
	local HOST="${1:?Missing host address}"
	local DOMAIN_MODE="${2:-False}"
	local DOMAIN_ADMIN_ACCOUNT="${3:-administrator}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.shutdown_remote_win_host($DOMAIN_MODE)
"
}

set_windows_gateway () {
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local GATEWAY="${3:?Missing gateway address}"
	local DOMAIN_ADMIN_ACCOUNT="${4:-administrator}"
	local DOMAIN_MODE="${5:-False}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.set_gateway('$GATEWAY', $DOMAIN_MODE)
"
}

create_ad_user_and_add_the_user_to_the_group () {
	local HOST="${1:?Missing host address}"
	local DOMAIN="${2:?Missing domain name}"
	local NEW_USERNAME="${3:?Missing user name}"
	local NEW_PASSWORD="${4:?Missing user password}"
	local NEW_GROUP="${5:?Missing group name}"
	local DOMAIN_ADMIN_ACCOUNT="${6:-administrator}"
	local DOMAIN_ADMIN_PWD=$(ucr get tests/domainadmin/pwd)
	local LOCAL_ADMIN_ACCOUNT="testadmin"
	local LOCAL_ADMIN_PWD="Univention@99"

	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', '$DOMAIN_ADMIN_ACCOUNT', '$DOMAIN_ADMIN_PWD', '$LOCAL_ADMIN_ACCOUNT', '$LOCAL_ADMIN_PWD', 445, '$HOST')
win.create_user_and_add_to_group('$NEW_USERNAME', '$NEW_PASSWORD', '$NEW_GROUP')
"
}

set_administrator_dn_for_ucs_test () {
	local dn="$(univention-ldapsearch sambaSid=*-500 -LLL dn | sed -ne 's|dn: ||p')"
	ucr set tests/domainadmin/account="$dn"
}

set_administrator_password_for_ucs_test () {
	local password="$1"

	ucr set tests/domainadmin/pwd="$password" tests/domainadmin/pwdfile?"/var/lib/ucs-test/pwdfile"
	mkdir -p /var/lib/ucs-test/
	echo -n "$password" >/var/lib/ucs-test/pwdfile
}

set_windows_localadmin_password_for_ucs_test () {
	local username="$1"
	local password="$2"

	ucr set \
		tests/windows/localadmin/name="$username" \
		tests/windows/localadmin/pwd="$password"
}

set_userpassword_for_administrator ()
{
	local password="$1"
	local user="${2:-Administrator}"

	eval "$(ucr shell ldap/base)"

	local passwordhash="$(mkpasswd -m sha-512 $password)"
	echo "dn: uid=$user,cn=users,$ldap_base
changetype: modify
replace: userPassword
userPassword: {crypt}$passwordhash
" | ldapmodify -x -D "cn=admin,$ldap_base" -y /etc/ldap.secret
}


monkeypatch () {
	# this function can be used to monkeypatch all UCS@school systems before running the tests

	# Bug #42658: temporary raise the connection timeout which the UMC Server waits the module process to start
	[ -e /usr/share/pyshared/univention/management/console/protocol/session.py ] && sed -i 's/if mod._connect_retries > 200:/if mod._connect_retries > 1200:/' /usr/share/pyshared/univention/management/console/protocol/session.py
	[ -e /usr/lib/python2.7/dist-packages/univention/management/console/protocol/session.py ] && sed -i 's/if mod._connect_retries > 200:/if mod._connect_retries > 1200:/' /usr/lib/python2.7/dist-packages/univention/management/console/protocol/session.py
	univention-management-console-server restart

	# Bug #40419: UCS@school Slave reject: LDAP sambaSID != S4 objectSID == SID(Master)
	[ "$(hostname)" = "slave300-s1" ] && /usr/share/univention-s4-connector/remove_ucs_rejected.py "cn=master300,cn=dc,cn=computers,dc=autotest300,dc=local" || true
}

import_license () {
	# wait for server
	local server="license.univention.de"
	for i in $(seq 1 100); do
		nc -w 3 -z license.univention.de 443 && break
		sleep 1
	done
	python -m shared-utils/license_client "$(ucr get ldap/base)" "$(date -d '+6 month' '+%d.%m.%Y')"
	# It looks like we have in some AD member setups problems with the DNS resolution. Try to use
	# the static variante (Bug #46448)
	if [ ! -e ./ValidTest.license ]; then
		ucr set hosts/static/85.184.250.151=license.univention.de
		nscd -i hosts
		python -m shared-utils/license_client "$(ucr get ldap/base)" "$(date -d '+6 month' '+%d.%m.%Y')"
		ucr unset hosts/static/85.184.250.151
		nscd -i hosts
	fi
	univention-license-import ./ValidTest.license && univention-license-check
	echo "license/base=$(ucr get license/base) uuid/license=$(ucr get uuid/license)"
}

install_apps_via_umc () {
	local username=${1:?missing username} password=${2:?missing password} rv=0 app
	shift 2 || return $?
	test -e /var/cache/appcenter-installed.txt && rm /var/cache/appcenter-installed.txt
	for app in "$@"; do
		python -m shared-utils/apps -U "$username" -p "$password" -a $app || rv=$?
		echo "$app" >>/var/cache/appcenter-installed.txt
	done
	return $rv
}

update_apps_via_umc () {
	local username=${1:?missing username} password=${2:?missing password} rv=0 app
	shift 2 || return $?
	for app in "$@"; do
		python -m shared-utils/apps -U "$username" -p "$password" -a $app -u || rv=$?
	done
	return $rv
}

remove_apps_via_umc () {
	local username=${1:?missing username} password=${2:?missing password} rv=0 app
	local reverse=""
	shift 2 || return $?
	rm -f /var/cache/appcenter-uninstalled.txt
	# un-install in reverse order (requiredApps)
	for app in "$@"; do
		reverse="$app $reverse"
		echo "$app" >>/var/cache/appcenter-uninstalled.txt
	done
	for app in $reverse; do
		python -m shared-utils/apps -U "$username" -p "$password" -a $app -r || rv=$?
	done
	return $rv
}

assert_app_is_installed_and_latest () {
	univention-app info
	local rv=0 app
	for app in "$@"; do
		local latest="$(python -m shared-utils/app-info -a $app -v)"
		univention-app info | grep -q "Installed: .*\b$latest\b.*" || rv=$?
	done
	return $rv
}

assert_app_is_installed () {
	univention-app register --app  # Workaround for Bug #46463. As this call may hide errors in the registration functions of the App installation, it should definitely be removed.
	univention-app info
	local rv=0 app
	for app in "$@"; do
		 univention-app info | grep -q "Installed: .*\b$app\b.*" || rv=$?
	done
	return $rv
}

assert_app_master_packages () {
	local rv=0 app
	# TODO
	# for app in "$@"; do
	return $rv
}

run_app_appliance_tests () {
	local app rv=0
	for app in "$@"; do
		assert_app_is_installed $app || return 1
		echo $app >>/var/cache/appcenter-installed.txt
		# check additinal apps too
		for add in $(univention-app get $app ApplianceAdditionalApps | sed -ne 's|ApplianceAdditionalApps: ||p' | sed 's|,| |g'); do
			assert_app_is_installed $add || return 1
			echo $add >>/var/cache/appcenter-installed.txt
		done
	done
	# install ucs-test from errata test
	/root/activate-errata-test-scope.sh
	install_with_unmaintained ucs-test-appcenter ucs-test-checks || rv=$?
	run_minimal_apptests || rv=$?
	return $rv
}

run_app_specific_test () {
	local app=${1:?missing app} password=${2:?missing password} rv=0
	set_administrator_dn_for_ucs_test
	set_administrator_password_for_ucs_test "$password"
	univention-app dev-test \
		--appcenter-server http://appcenter-test.software-univention.de \
		"$app" \
		--binddn "$(ucr get tests/domainadmin/account)" \
		--bindpwdfile "$(ucr get tests/domainadmin/pwdfile)" || rv=$?
	return $rv
}

add_tech_key_authorized_keys() {
	install -m0755 -o0 -g0 -d /root/.ssh
	echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKxi4dwmF9K7gV4JbQUmQ4ufRHcxYOYUHWoIRuj8jLmP1hMOqEmZ43rSRoe2E3xTNg+RAjwkX1GQmWQzzjRIYRpUfwLo+yEXtER1DCDTupLPAT5ulL6uPd5mK965vbE46g50LHRyTGZTbsh1A/NPD7+LNBvgm5dTo/KtMlvJHWDN0u4Fwix2uQfvCSOpF1n0tDh0b+rr01orITJcjuezIbZsArTszA+VVJpoMyvu/I3VQVDSoHB+7bKTPwPQz6OehBrFNZIp4zl18eAXafDoutTXSOUyiXcrViuKukRmvPAaO8u3+r+OAO82xUSQZgIWQgtsja8vsiQHtN+EtR8mIn tech' >>/root/.ssh/authorized_keys
}

install_winrm() {
	# TODO: move python-winrm to ucs
	dpkg -i shared-utils/addons/python-winrm_*deb shared-utils/addons/python-isodate_*.deb  shared-utils/addons/python-xmltodict_*.deb
}

assert_admember_mode () {
	. /usr/share/univention-lib/admember.sh
	is_localhost_in_admember_mode
}

# start a local firefox and open umc portal page
start_portal_in_local_firefox () {
	service  univention-welcome-screen stop
	install_with_unmaintained --no-install-recommends univention-x-core univention-mozilla-firefox openbox
	X &
	DISPLAY=:0 openbox --config-file /etc/xdg/openbox/rc_no_shortcuts.xml &
	sleep 1
	DISPLAY=:0 firefox http://$(hostname -f)/univention/portal &
	sleep 10
	chvt 2
	sleep 1
}

postgres91_update () {
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod -x /usr/sbin/univention-pkgdb-scan
	service postgresql stop
	rm -rf /etc/postgresql/9.4
	apt-get install --reinstall postgresql-9.4
	pg_dropcluster 9.4 main --stop
	service postgresql start
	test -e /var/lib/postgresql/9.4/main && mv /var/lib/postgresql/9.4/main /var/lib/postgresql/9.4/main.old
	pg_upgradecluster 9.1 main
	ucr commit /etc/postgresql/9.4/main/*
	chown -R postgres:postgres /var/lib/postgresql/9.4
	service postgresql restart
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod +x /usr/sbin/univention-pkgdb-scan
	DEBIAN_FRONTEND='noninteractive'  univention-install --yes univention-postgresql-9.4
	pg_dropcluster 9.1 main --stop
	DEBIAN_FRONTEND='noninteractive' apt-get purge --yes postgresql-9.1
}

dump_systemd_journal () {
	journalctl > /var/log/journalctl.log || echo "Could not dump systemd journal."
}

add_hostname_to_juint_results ()
{
	local hostname="$(hostname)"
	for f in test-reports/*/*.xml; do
		sed -i "s| name=\"| name=\"${hostname}.|g;s|testcase classname=\"|testcase classname=\"${hostname}.|g" $f
	done
}

prepare_results () {
	add_tech_key_authorized_keys
	dump_systemd_journal
}

add_branch_repository () {
	local extra_list="/root/apt-get-branch-repo.list"
	if [ -s "$extra_list" ]; then
		cp "$extra_list" /etc/apt/sources.list.d/
		chmod a+r "/etc/apt/sources.list.d/$(basename "$extra_list")"
		apt-get update
		return $?
	fi
}

restart_services_bug_47762 ()
{
	# https://forge.univention.org/bugzilla/show_bug.cgi?id=47762
	# The services needs to be restart otherwise they wouldn't bind
	# to the new IP address
	if [ -x /etc/init.d/samba ]; then
		/etc/init.d/samba restart
	fi
	sleep 15
}

# https://forge.univention.org/bugzilla/show_bug.cgi?id=48157
restart_umc_bug_48157 ()
{
	sleep 30
	service univention-management-console-server restart || true
}

run_workarounds_before_starting_the_tests ()
{
	restart_services_bug_47762
	#restart_umc_bug_48157 # Bug is verified for now. Code can be removed if bug is closed.
}

sa_bug47030 () {
	sa-update -v --install /root/1854818.tar.gz || true
	sa-compile || true
	service spamassassin restart || true
	service amavis restart || true
}

online_fsresize () {
	# cloud-initramfs-growroot doesn't always work (bug #49337)
	# Try on-line resizing
	echo "Grow root partition"
	root_device="$(readlink -f "$(df --output=source / | tail -n 1)")"
	disk="${root_device%[0-9]}"
	part_number="${root_device#${disk}}"
	growpart "$disk" "$part_number"
	resize2fs "$root_device"
}

winrm_config () {
	local domain=${1:?missing domain} password=${2:?missing password} user=${3:?missing user} client=${4:?missing client} rv=0
	echo -e "[default]\ndomain = ${domain}\npassword = ${password}\nuser = ${user}\nclient = ${client}" > /root/.ucs-winrm.ini || rv=1
	return $rv
}

test_windows () {
	local rv=0
	if ! python shared-utils/ucs-winrm.py run-ps --cmd ipconfig; then
		sleep 60
		python shared-utils/ucs-winrm.py run-ps --cmd ipconfig || rv=1
	fi
	python shared-utils/ucs-winrm.py run-ps --cmd "(gwmi win32_operatingsystem).caption" || rv=1
	return $rv
}

promote_ad_server () {
	local forest=${1:=missing forest mode} domain=${1:=missing domain mode} rv=0
	python shared-utils/ucs-winrm.py promote-ad --forestmode ${forest} --domainmode ${domain} || rv=1
	sleep 400
	return $rv
}

# vim:set filetype=sh ts=4:
