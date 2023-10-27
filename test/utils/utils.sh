#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2023 Univention GmbH
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

# shellcheck disable=SC2015

set -x

die () {
	echo "${0##*/}: $*" >&2
	exit 1
}

have () {
	command -v "${1:?command}" >/dev/null 2>&1
}

FTP_DOM='software-univention.de' FTP_SCHEME='https' FTP_TEST_REPO="updates-test"
case "${VIRTTECH:=$(systemd-detect-virt)}" in
amazon|xen) ;;
qemu|kvm) FTP_DOM='knut.univention.de' FTP_SCHEME='http' FTP_TEST_REPO="updates-test" ;;
esac

basic_setup_allow_uss () {
	# force dpkg not to call "sync" during package installations/updates
	echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/force-unsafe-io
	case "$VIRTTECH" in
	qemu|kvm)
		echo "KVM detected"
		ucr set --force dhclient/linklocal/fallback=false dhclient/options/timeout=30
		;;
	amazon|xen)
		echo "Assuming Amazon Cloud"
		;;
	esac

	_fix_grub56574
	_fix_dns46993

	ucr set --force updater/identify="UCS (EC2 Test)"
	ucr set update/check/cron/enabled=false update/check/boot/enabled=false mail/antispam/rules/autoupdate?yes server/password/cron='#0 1 * * *'
	systemctl reload cron.service || true
	sa_bug53751
}

_fix_grub56574 () {  # Bug #38911,56574: Fix GRUB root device
	local bdev
	bdev="$(/usr/sbin/grub-probe -t disk /boot/grub)" &&
		[ -n "$bdev" ] &&
		echo set grub-pc/install_devices "$bdev" | debconf-communicate
}

_fix_dns46993 () {  # Bug #46993: Use AmazonProvidedDNS/dnsmasq4kvm and remove OpenDNS resolver
	[ -f /var/univention-join/joined ] &&
		return 0
	sed -rne 's/^nameserver\s*([.0-9]+|[.0-9:A-Fa-f]+)\s*$/\1/;T;/^208\.67\.22[02]\.22[02]|^2620:0+:0?cc[cd]::0*2$/d;p' /etc/resolv.conf |
		head -n 3 |
		cat -n |
		sed -re 's,^\s*([0-9]+)\s+(.+),nameserver\1=\2 dns/forwarder\1=\2,' |
		xargs ucr set nameserver/external=false nameserver1= nameserver2= nameserver3= dns/forwarder1= dns/forwarder2= dns/forwarder3=
}

basic_setup () {
	basic_setup_allow_uss
	stop_uss_and_restore_profile
}

stop_uss_and_restore_profile () {
	local SRV='univention-system-setup-boot.service' job
	if [ 'LoadState=loaded' = "$(systemctl --property LoadState show "$SRV")" ]
	then
		# prevent future
		systemctl mask "$SRV"
		# cancel pending
		job="$(systemctl --property Job show "$SRV")" &&
			[ -n "${job#Job=}" ] &&
			systemctl cancel "${job#Job=}" ||
			:
		# kill current
		systemctl kill "$SRV"
		systemctl reset-failed "$SRV"
	fi

	local USS_PROFILE='/var/cache/univention-system-setup/profile'
	[ -f "${USS_PROFILE}.bak" ] &&
		[ ! -e "${USS_PROFILE}" ] &&
		mv "${USS_PROFILE}.bak" "${USS_PROFILE}"
	:
}

rotate_logfiles () {
	have logrotate &&
		logrotate -f /etc/logrotate.conf
}

prepare_domain_for_ucs52_preup_checks() {
	/usr/share/univention-directory-manager-tools/udm-remap-country-from-st-to-c || return $?

	univention-ldapsearch -LLL '(&(objectClass=univentionNagiosServiceClass)(!(univentionNagiosUseNRPE=1)))' 1.1 | sed -rne 's#^dn: ##p' | while read -r dn; do udm nagios/service remove --dn "$dn"; done
	univention-ldapsearch -LLL 'objectClass=univentionNagiosTimeperiodClass' 1.1 | sed -rne 's#^dn: ##p' | while read -r dn; do udm nagios/timeperiod remove --dn "$dn" || ldapdelete -D "cn=admin,$(ucr get ldap/base)" -y /etc/ldap.secret "$dn"; done

	univention-ldapsearch -LLL '(objectClass=univentionSAMLIdpConfig)' 1.1 | ldapsearch-decode64 | sed -rne 's#^dn: ##p' | while read -r dn; do udm saml/idpconfig remove --dn "$dn"; done
	univention-ldapsearch -LLL '(objectClass=univentionSAMLServiceProvider)' 1.1 | ldapsearch-decode64 | sed -rne 's#^dn: ##p' | while read -r dn; do udm saml/serviceprovider remove --dn "$dn"; done
}

jenkins_updates () {
	ucr set update43/checkfilesystems=no update44/checkfilesystems=no update50/checkfilesystems=no update50/ignore_legacy_objects=yes update50/ignore_old_packages=yes
	local version_version version_patchlevel version_erratalevel target rc=0
	target="$(echo "${JOB_NAME:-}"|sed -rne 's,.*/UCS-([0-9]+\.[0-9]+-[0-9]+)/.*,\1,p')"
	# Update UCS@school instances always to latest patchlevel version
	[ -z "$target" ] && target="$(echo "${JOB_NAME:-}"|sed -rne 's,^UCSschool-([0-9]+\.[0-9]+)/.*,\1-99,p')"

	[ -n "${TARGET_VERSION:-}" ] && target="$TARGET_VERSION"
	[ -n "${RELEASE_UPDATE:-}" ] && release_update="$RELEASE_UPDATE"
	[ -n "${ERRATA_UPDATE:-}" ] && errata_update="$ERRATA_UPDATE"

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Starting from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."
	echo "release_update=$release_update"

	case "${release_update:-}" in
	public) upgrade_to_latest --updateto "$target" || rc=$? ;;
	testing) upgrade_to_testing --updateto "$target" || rc=$? ;;
	none|"") ;;
	*) die "Unknown release_update='$release_update'" ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Continuing from ${version_version}-${version_patchlevel}+${version_erratalevel} to ${target}..."
	echo "errata_update=$errata_update"

	case "${errata_update:-}" in
	testing) upgrade_to_latest_test_errata || rc=$? ;;
	public) upgrade_to_latest_errata || rc=$? ;;
	none|"") ;;
	*) die "Unknown errata_update='$errata_update'" ;;
	esac

	eval "$(ucr shell '^version/(version|patchlevel|erratalevel)$')"
	echo "Finished at ${version_version}-${version_patchlevel}+${version_erratalevel}"
	return $rc
}

upgrade_to_latest_patchlevel () {
	local updateto
	updateto="$(ucr get version/version)-99"
	upgrade_to_latest --updateto "$updateto"
}

upgrade_to_latest_errata () {
	local current
	current="$(ucr get version/version)-$(ucr get version/patchlevel)"
	upgrade_to_latest --updateto "$current"
}

upgrade_to_latest_test_errata_if () {
	local errata_update="${1:-$ERRATA_UPDATE}"
	[ "$errata_update" != "testing" ] ||
		upgrade_to_latest_test_errata
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
	ucr set repository/online/server="${FTP_SCHEME}://${FTP_TEST_REPO}.${FTP_DOM}/"
	apt-get -qq update
}
fix_repository_schema () {  # Bug #55044 - to be removed when upgrading from 5.0-2+e528
	local key='repository/online/server' repo
	repo="$(ucr get "$key")"
	case "$repo" in
	*://*) return 0 ;;
	esac
	ucr set "${key}=${FTP_SCHEME}://${repo}/"
}

set_repository_if_testing () {  # "[ENV:RELEASE_UPDATE]"
	case "${1:?missing testing argument}" in
	testing) set_repository_to_testing ;;
	esac
}

upgrade_to_latest () {
	ucr set repository/online=true
	_upgrade_to_latest "$@"
}
_upgrade_to_latest () {
	declare -i remain=300 rv delay=30
	declare -a upgrade_opts=("--noninteractive" "--ignoreterm" "--ignoressh")
	while true
	do
		[ "true" = "$DISABLE_APP_UPDATES" ] && upgrade_opts+=("--disable-app-updates")
		univention-upgrade "${upgrade_opts[@]}" "$@"
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
	# shellcheck disable=SC2016
	local script='{ set -x; nscd -i hosts; grep -H . /etc/resolv.conf /etc/apt/sources.list.d/15_ucs-online-version.list; ifconfig; ping -c 4 "$(ucr get repository/online/server)"; nslookup "$(ucr get repository/online/server)"; sleep 60; ucr commit /etc/apt/sources.list.d/*.list; apt-get update; } ; grep -H . /etc/apt/sources.list.d/15_ucs-online-version.list'
	sed -i "s~^apt-get update\$~& || $script~" /usr/lib/univention-system-setup/scripts/setup-join.sh
}
_fix_ssh47233 () { # Bug #47233: ssh connection stuck on reboot
	local G='/etc/pam.d/common-session' T='/etc/univention/templates/files/etc/pam.d/common-session.d/10univention-pam_common'
	grep -Fqs 'pam_systemd.so' "$G" && return 0
	grep -Fqs 'pam_systemd.so' "$T" ||
		echo "session optional        pam_systemd.so" >>"$T"
	ucr commit "$G"
}

run_setup_join () {
	local rv=0
	patch_setup_join # temp. remove me
	set -o pipefail
	/usr/lib/univention-system-setup/scripts/setup-join.sh ${1:+"$@"} | tee -a /var/log/univention/setup.log || rv=$?
	set +o pipefail
	ucr set apache2/startsite='univention/' # Bug #31682
	deb-systemd-invoke try-reload-or-restart univention-management-console-server apache2
	ucr unset --forced update/available

	# No this breaks univention-check-templates -> 00_checks.81_diagnostic_checks.test _fix_ssh47233  # temp. remove me

	# TODO find a better place for this
	# currently neither the app nor UCS creates the SAML login portal entry, we need it for our tests
	udm portals/entry modify --dn "cn=login-saml,cn=entry,cn=portals,cn=univention,$(ucr get ldap/base)" --set activated=TRUE

	return $rv
}

run_setup_join_on_non_master () {
	local admin_password="${1:-univention}" nameserver1
	nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	if [ -n  "$nameserver1" ]; then
		ucr set nameserver1="$nameserver1"
	fi
	printf '%s' "$admin_password" >/tmp/univention
	run_setup_join --dcaccount Administrator --password_file /tmp/univention
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
	return $rv
}

wait_for_replication () {
	local timeout=${1:-3600}
	local steps=${2:-10}
	local timestamp
	timestamp=$(date +"%s")
	echo "Waiting for replication..."
	while ! /usr/lib/nagios/plugins/check_univention_replication; do
		if [ "$((timestamp+timeout))" -lt "$(date +"%s")" ]; then
			echo "ERROR: replication incomplete."
			return 1
		fi
		sleep "$steps"
	done
	return 0
}

wait_for_process () {
	local timeout=${1:-3600}
	local steps=${2:-10}
	local process_name=${3:?Missing process name}
	local timestamp
	timestamp=$(date +"%s")
	echo "Waiting for process '$process_name'..."
	while ! pgrep -f "$process_name" >/dev/null; do
		if [ "$((timestamp+timeout))" -lt "$(date +"%s")" ]; then
			echo "ERROR: process '$process_name' does not run."
			return 1
		fi
		sleep "$steps"
	done
	return 0
}

wait_for_slapd () {
	wait_for_process 600 1 /usr/sbin/slapd -f /etc/ldap/slapd.conf
}

wait_for_setup_process () {
	local i
	local SETUP_FILE="/var/www/ucs_setup_process_status.json"
	sleep 10
	for i in $(seq 1 1200); do
		[ -e "$SETUP_FILE" ] ||
			return 0
		sleep 3
	done
	echo "setup did not finish after 3600s, timeout"
	return 1
}

switch_app_center() {
	if [ "$UCS_TEST_APPCENTER" = "true" ]; then
		switch_to_test_app_center
	elif [ "$(ucr get repository/app_center/server)" != "appcenter.software-univention.de" ]; then
		univention-install --yes univention-appcenter-dev
		univention-app dev-use-test-appcenter --revert
	fi
}

switch_to_test_app_center () {
	local app rv=0
	have univention-app || return 1
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
		xargs -I % ucr set %="appcenter-test.software-univention.de/"
}

install_apps () {
	local app rv=0 username
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
	local app rv=0 username
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
	local app rv=0 username
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
	# rebuild sources list on network error
	if grep -q "An error occurred during the repository check" /etc/apt/sources.list.d/15_ucs-online-version.list; then
		sleep 60
		ucr set repository/online=true repository/online/unmaintained=yes
	fi
	cat /etc/apt/sources.list.d/15_ucs-online-version.list
	univention-install --yes "$@" || rv=$?
	ucr set repository/online/unmaintained=no
	return $rv
}

wait_for_repo_server () {
	local i repository_online_server
	eval "$(ucr shell 'repository/online/server')"
	repository_online_server=${repository_online_server#https://}
	repository_online_server=${repository_online_server#http://}
	repository_online_server=${repository_online_server%%/*}
	for ((i=0; i<300; i++))
	do
		ping -c 2 "$repository_online_server" && return 0
		sleep 1
	done
	return 1
}

install_ucs_test () {
	wait_for_repo_server || return 1
	install_with_unmaintained ucs-test "$@"
}

install_ucs_test_from_errata_test () {
	wait_for_repo_server || return 1
	/root/activate-errata-test-scope.sh || return 1
	install_ucs_test "$@"
}

install_ucs_test_checks_from_errata_test () {
	local rv=0
	/root/activate-errata-test-scope.sh || rv=$?
	install_with_unmaintained ucs-test-checks "$@" || rv=$?
	return $rv
}

install_from_errata_test () {
	local rv=0
	/root/activate-errata-test-scope.sh || rv=$?
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
			dpkg -i "/var/lib/docker/overlay/$(ucr get appcenter/apps/$app/container)/merged/ucs-test-${app}_"*.deb &&
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
	"$@" || {
		rv=$?
		create_DONT_START_UCS_TEST "FAILED: prevent_ucstest_on_fail $*"
	}
	return $rv
}

activate_ucsschool_devel_scope () {
	local COMPONENT="repository/online/component/ucsschool_DEVEL"
	ucr set "$COMPONENT/description=Development version of UCS@school packages" \
		"$COMPONENT/version=$(ucr get version/version)" \
		"$COMPONENT/server=${FTP_SCHEME}://${FTP_TEST_REPO}.${FTP_DOM}/" \
		"$COMPONENT=enabled"
}

activate_idbroker_devel_scope () {
	local COMPONENT="repository/online/component/idbroker_DEVEL"
	ucr set "$COMPONENT/description=Development version of UCS idbroker" \
		"$COMPONENT/version=current" \
		"$COMPONENT/server=${FTP_SCHEME}://${FTP_TEST_REPO}.${FTP_DOM}/" \
		"$COMPONENT=enabled"
}

activate_idbroker_repositories () {
	local rv=0
	case "${IDBROKER_RELEASE:-$UCSSCHOOL_RELEASE}" in
		appcenter.test)
			switch_to_test_app_center || rv=$?
			;;
		public)
			;;
		scope|*)
			activate_idbroker_devel_scope || rv=$?
			;;
	esac
	univention-app info
	return $rv
}


ucsschool_scope_enabled () {
	[ "${UCSSCHOOL_RELEASE:-scope}" = "scope" ]
}

activate_ucsschool_repositories () {
	local rv=0

	case "${UCSSCHOOL_RELEASE:-scope}" in
		appcenter.test)
			switch_to_test_app_center || rv=$?
			;;
		public)
			;;
		scope|*)
			activate_ucsschool_devel_scope || rv=$?
			;;
	esac
	univention-app info
	return $rv
}

upgrade_ucsschool () {
	local rv=0 username
	username="$(ucr get tests/domainadmin/account | sed -e 's/uid=//' -e 's/,.*//')"
	univention-app upgrade ucsschool --noninteractive --username="$username" --pwdfile="$(ucr get tests/domainadmin/pwdfile)" || rv=$?
	univention-app info
	wait_for_reboot # TODO is this necessary?
	return $rv
}

install_ucsschool () {
	local rv=0

	# Bug #50690: ucs-school-webproxy would set this to yes. Which breaks our test environment
	ucr set --force dhcpd/authoritative=no
	# Bug #54228: run tests without stopping the notifier during imports, to detect problems
	ucr set --force ucsschool/stop_notifier=no

	echo 'deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_5.1-0-ucs-school-5.1/all/' >>/etc/apt/sources.list
	echo 'deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_5.1-0-ucs-school-5.1/$(ARCH)/' >>/etc/apt/sources.list

	univention-install -y ucs-school-umc-installer
	return $?

	activate_ucsschool_repositories || rv=$?

	case "${UCSSCHOOL_RELEASE:-scope}" in
		appcenter.test)
			install_apps ucsschool || rv=$?
			;;
		public)
			install_apps ucsschool || rv=$?
			;;
		scope|*)
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

remove_s4connector_tests_and_mark_tests_manual_installed () {
	univention-remove --yes ucs-test-s4connector
	apt-mark manual 'ucs-test-*'
}

remove_adconnector_tests_and_mark_tests_manual_installed () {
	univention-remove --yes ucs-test-adconnector ucs-test-admember
	apt-mark manual 'ucs-test-*'
}

install_ucs_windows_tools () {
	install_with_unmaintained ucs-windows-tools
}

run_apptests () {
	local app
	# some tests create domaincontroller_master objects, the listener ldap_server.py
	# sets these objects as ldap/server/name ldap/master in the docker container
	# until this is fixed, force the variables in the docker container
	for app in $(< /var/cache/appcenter-installed.txt); do
		if [ -n "$(univention-app get "$app" DockerImage)" ]; then
			# shellcheck disable=SC2016
			univention-app shell "$app" bash -c '
			eval "$(ucr shell)"
			[ -n "${ldap_server_name:-}" && ucr set --force ldap/server/name="$ldap_server_name"
			[ -n "${ldap_master:-}" ] && ucr set --force ldap/master="$ldap_master"
			[ -n "${kerberos_adminserver:-}" ] && ucr set --force kerberos/adminserver="$kerberos_adminserver"
			'
		fi
	done

	run_tests -r apptest "$@"
}

run_minimal_tests () {
	run_tests -s checks "$@"
}

# shellcheck disable=SC2120
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

run_keycloak_tests () {
	# workaround Bug #55976
	ucr set diagnostic/check/disable/04_saml_certificate_check=true
	run_tests -s checks -s keycloak -s end "$@"
}

ad_member_fix_udm_rest_api () {  # workaround for Bug #50527
	ucr unset directory/manager/rest/authorized-groups/domain-admins
	univention-run-join-scripts --force --run-scripts 22univention-directory-manager-rest.inst
	deb-systemd-invoke restart univention-directory-manager-rest
}

run_adconnector_tests () {
	# Test if the failed Jenkins test are timing issues
	sed -i 's|AD_ESTIMATED_MAX_COMPUTATION_TIME=3|AD_ESTIMATED_MAX_COMPUTATION_TIME=16|' /usr/share/ucs-test/55_adconnector/adconnector.sh
	run_tests -s checks -s adconnector -s end "$@"
}

run_adconnector_and_s4connector_tests () {
	# Test if the failed Jenkins test are timing issues
	sed -i 's|AD_ESTIMATED_MAX_COMPUTATION_TIME=3|AD_ESTIMATED_MAX_COMPUTATION_TIME=16|' /usr/share/ucs-test/55_adconnector/adconnector.sh
	run_tests -s checks -s adconnector -s samba4 -s s4connector -s end "$@"
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
	local test_group="${1:?}" i
	declare -a test_args=()
	# following list have to be in sync with EC2Tools.groovy ==> addUASSinglEnvAxes/addUASMultiEnvAxes
	for i in base1 import1 import2 import3 import4 ; do
		[ "$test_group" != "$i" ] && test_args+=("--prohibit=ucsschool_${i}")
		if [ "$(echo "$test_group" | sed -re 's/[0-9]+$//')" == "import" ]; then
			# test_args+=("--section=checks")  # enable?
			test_args+=("--section=ucsschool")
			test_args+=("--section=end")
		fi
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
	if [ "${COVERAGE_REPORT:-}" = "true" ]; then
		GENERATE_COVERAGE_REPORT="--with-coverage --coverage-show-missing --coverage-output-directory=/var/log/univention/coverage"
	fi
	dpkg-query -W -f '${Status}\t${binary:Package}\t${Version}\n' > "packages-under-test.log"

	# check is ucs-test run is allowed
	if [ "${UCS_TEST_RUN:-}" = "false" ]; then
		echo "ucs-test disabled by env UCS_TEST_RUN=$UCS_TEST_RUN"
		return 0
	fi

	# TODO: remove this is just to make testing easier in the development phase
	echo "deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_$(ucr get version/version)-0/all/" >/etc/apt/sources.list.d/99ucs-test.list
	echo "deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_$(ucr get version/version)-0/\$(ARCH)/" >>/etc/apt/sources.list.d/99ucs-test.list
	univention-upgrade --disable-app-updates --noninteractive --ignoreterm --ignoressh
	rm -f /etc/apt/sources.list.d/99ucs-test.list

	# shellcheck disable=SC2086
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
		printf '%s' "$admin_password" >/tmp/univention
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

run_rejoin () {
	local admin_password="${1:-univention}"

	printf '%s' "$admin_password" >/tmp/univention
	if ! univention-join -dcaccount Administrator -dcpwd /tmp/univention; then
		# Later join scripts can fail in large environments if the replication can not keep up
		wait_for_replication "$(( 6 * 3600 ))" 60
		univention-install -y ucs-test-framework && python3 -c "import univention.testing.ucs_samba; univention.testing.ucs_samba.wait_for_s4connector(timeout=3600 * 24, delta_t=60)"
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

do_reboot () {
	nohup shutdown -r now &
	sleep 1
	exit
}

assert_version () {
	local requested_version="${1:?UCS release}"
	local version version_version version_patchlevel

	eval "$(ucr shell '^version/(version|patchlevel)$')"
	version="$version_version-$version_patchlevel"
	echo "Requested version $requested_version"
	echo "Current version $version"
	[ "$requested_version" = "$version" ] &&
		return 0
	create_DONT_START_UCS_TEST "FAILED: assert_version $requested_version == $version"
	return 1
}

assert_minor_version () {
	local requested_version="${1:?UCS major.minor release}" version_version
	eval "$(ucr shell '^version/version$')"
	echo "Requested minor version $requested_version"
	echo "Current minor version $version_version"
	[ "$requested_version" = "$version_version" ] &&
		return 0
	create_DONT_START_UCS_TEST "FAILED: assert_minor_version $requested_version == $version_version"
	return 1
}

assert_join () {
	# sometimes univention-check-join-status fails because the ldap server is restarted
	# and not available at this moment, so try it three times
	local i
	for i in 1 2 3
	do
		univention-check-join-status &&
			return 0
		sleep 10
	done
	create_DONT_START_UCS_TEST "FAILED: univention-check-join-status"
	return 1
}

assert_adconnector_configuration () {
	[ -n "$(ucr get connector/ad/ldap/host)" ] &&
		return 0
	create_DONT_START_UCS_TEST "FAILED: assert_adconnector_configuration"
	return 1
}

assert_packages () {
	local package installed
	for package in "$@"
	do
		installed=$(dpkg-query -W -f '${status}' "$package")
		[ "$installed" = "install ok installed" ] &&
			continue
		create_DONT_START_UCS_TEST "Failed: package status of $package is $installed"
		return 1
	done
	return 0
}

set_administrator_dn_for_ucs_test () {
	local dn
	dn="$(univention-ldapsearch -LLL '(sambaSid=*-500)' 1.1 | sed -ne 's|dn: ||p')"
	ucr set tests/domainadmin/account="$dn"
}

set_administrator_password_for_ucs_test () {
	local password="${1?password}" FN='/var/lib/ucs-test/pwdfile'
	install -m 0755 -o root -g root -d "${FN%/*}"
	printf '%s' "$password" >"$FN"
	ucr set tests/domainadmin/pwd="$password" tests/domainadmin/pwdfile?"$FN"
}

set_root_password_for_ucs_test () {
	local password="${1?password}" FN='/var/lib/ucs-test/root-pwdfile'
	install -m 0755 -o root -g root -d "${FN%/*}"
	printf '%s' "$password" >"$FN"
	ucr set tests/root/pwd="$password" tests/root/pwdfile?"$FN"
}

set_windows_localadmin_password_for_ucs_test () {
	ucr set \
		tests/windows/localadmin/name="${1?username}" \
		tests/windows/localadmin/pwd="${2?password}"
}

set_userpassword_for_administrator () {
	local password="${1?password}"
	local user="${2:-Administrator}"
	local lb
	lb="$(ucr get ldap/base)"

	local passwordhash
	passwordhash="$(mkpasswd -m sha-512 "$password")"
	echo "dn: uid=$user,cn=users,$lb
changetype: modify
replace: userPassword
userPassword: {crypt}$passwordhash
" | ldapmodify -x -D "cn=admin,$lb" -y /etc/ldap.secret
}


monkeypatch () {
	# this function can be used to monkeypatch all UCS@school systems before running the tests

	# Bug #42658: temporary raise the connection timeout which the UMC Server waits the module process to start
	[ -e /usr/lib/python3/dist-packages/univention/management/console/protocol/session.py ] && sed -i 's/if mod._connect_retries > 200:/if mod._connect_retries > 1200:/' /usr/lib/python3/dist-packages/univention/management/console/protocol/session.py
	deb-systemd-invoke restart univention-management-console-server

	# Bug #40419: UCS@school Slave reject: LDAP sambaSID != S4 objectSID == SID(Master)
	[ "$(hostname)" = "slave300-s1" ] && /usr/share/univention-s4-connector/remove_ucs_rejected.py "cn=master300,cn=dc,cn=computers,dc=autotest300,dc=test" || true
}

import_license () {
	local users="${1:-50}"
	local lb
	lb="$(ucr get ldap/base)"
	# wait for server
	local server="license.univention.de" i
	for i in $(seq 1 100); do
		nc -w 3 -z "$server" 443 && break
		sleep 1
	done
	/root/shared-utils/license_client.py "${lb}" -u "$users" "$(date -d '+6 month' '+%d.%m.%Y')"
	# It looks like we have in some AD member setups problems with the DNS resolution. Try to use
	# the static variante (Bug #46448)
	if [ ! -e ./ValidTest.license ]; then
		ucr set "hosts/static/85.184.250.151=$server"
		nscd -i hosts
		/root/shared-utils/license_client.py "${lb}" -u "$users" "$(date -d '+6 month' '+%d.%m.%Y')"
		ucr unset hosts/static/85.184.250.151
		nscd -i hosts
	fi
	univention-license-import ./ValidTest.license && univention-license-check
	echo "license/base=$(ucr get license/base) uuid/license=$(ucr get uuid/license)"
}

umc_apps () {
	local version
	version=$(ucr get version/version)
	if [ "${version%%.*}" -ge 5 ]; then
		# umc appcenter with UCS 5.0
		python3 umc-appcenter.py "$@"
	else
		# legacy umc appcenter, needed for app release tests
		/root/shared-utils/apps.py "$@"
	fi
}

install_apps_via_umc () {
	local username=${1:?missing username} password=${2:?missing password} rv=0 app
	shift 2 || return $?
	univention-app update || return $?
	rm -f /var/cache/appcenter-installed.txt
	for app in "$@"; do
		# shellcheck disable=SC2153
		if [ -n "$MAIN_APP" ] && [ -n "$MAIN_APP_VERSION" ] && [ "$MAIN_APP" = "$app" ]; then
			umc_apps -U "$username" -p "$password" -a "$app" -v "$MAIN_APP_VERSION" || rv=$?
		else
			umc_apps -U "$username" -p "$password" -a "$app" || rv=$?
		fi
		echo "$app" >>/var/cache/appcenter-installed.txt
	done
	return $rv
}

install_apps_via_cmdline () {
	univention-app update || return $?
	local username=${1:?missing username} password=${2:?missing password} rv=0 app password_file
	shift 2 || return $?
	password_file="$(mktemp)"
	echo "$password" > "$password_file"
	for app in "$@"; do
		univention-app install --noninteractive --username "$username" --pwdfile "$password_file" "$app" || rv=$?
	done
	rm -f "$password_file"
	return $rv
}

update_apps_via_cmdline () {
	univention-app update || return $?
	local username=${1:?missing username} password=${2:?missing password} rv=0 app password_file
	shift 2 || return $?
	password_file="$(mktemp)"
	echo "$password" > "$password_file"
	for app in "$@"; do
		univention-app upgrade --noninteractive --username "$username" --pwdfile "$password_file" "$app" || rv=$?
	done
	rm -f "$password_file"
	return $rv
}

update_apps_via_umc () {
	local username=${1:?missing username} password=${2:?missing password} main_app=${3:?missing main_app} rv=0 app
	shift 3 || return $?

	# update the main app
	if [ -n "$MAIN_APP" ] && [ -n "$MAIN_APP_VERSION" ] && [ "$MAIN_APP" = "$main_app" ]; then
		umc_apps -U "$username" -p "$password" -a "$main_app" -v "$MAIN_APP_VERSION" -u || rv=$?
	else
		umc_apps -U "$username" -p "$password" -a "$main_app" -u || rv=$?
	fi

	# In app tests we want to check the new version of the main app.
	# And for the main app an update is required.
	# Additional apps can have updates, but if no update is
	# available, we just ignore this (-i)
	for app in "$@"; do
		[ "$app" = "$main_app" ] && continue
		if ! assert_app_is_installed_and_latest_or_specific_version "${app}"; then
			# try update, but do not except that an update is available
			if [ -n "$MAIN_APP" ] && [ -n "$MAIN_APP_VERSION" ] && [ "$MAIN_APP" = "$app" ]; then
				umc_apps -U "$username" -p "$password" -a "$app" -v "$MAIN_APP_VERSION" -u -i || rv=$?
			else
				umc_apps -U "$username" -p "$password" -a "$app" -u -i || rv=$?
			fi
		fi
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
		umc_apps -U "$username" -p "$password" -a "$app" -r || rv=$?
	done
	return $rv
}

assert_app_is_installed_and_latest_or_specific_version () {
	univention-app info
	local rv=0 app latest
	for app in "$@"; do
		if [ -n "$MAIN_APP" ] && [ -n "$MAIN_APP_VERSION" ] && [ "$MAIN_APP" = "$app" ]; then
			latest="$MAIN_APP"="$MAIN_APP_VERSION"
		else
			latest="$(/root/shared-utils/app-info.py -a "$app" -v)"
		fi
		univention-app info | grep -q "Installed: .*\b$latest\b.*" || rv=$?
	done
	return $rv
}

assert_app_is_installed_and_latest () {
	univention-app info
	local rv=0 app latest
	for app in "$@"; do
		latest="$(/root/shared-utils/app-info.py -a "$app" -v)"
		univention-app info | grep -q "Installed: .*\b$latest\b.*" || rv=$?
	done
	return $rv
}

assert_app_is_installed () {
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
	local app rv=0 add
	for app in "$@"; do
		assert_app_is_installed "$app" || return 1
		echo "$app" >>/var/cache/appcenter-installed.txt
		# check additinal apps too
		for add in $(univention-app get "$app" ApplianceAdditionalApps | sed -ne 's|ApplianceAdditionalApps: ||p' | sed 's|,| |g'); do
			assert_app_is_installed "$add" || return 1
			echo "$add" >>/var/cache/appcenter-installed.txt
		done
	done
	## install ucs-test from errata test
	#/root/activate-errata-test-scope.sh
	install_with_unmaintained ucs-test-appcenter ucs-test-checks || rv=$?
	# shellcheck disable=SC2119
	run_minimal_apptests || rv=$?
	return $rv
}

run_app_specific_test () {
	local app=${1:?missing app} password=${2:?missing password} rv=0
	set_administrator_dn_for_ucs_test
	set_administrator_password_for_ucs_test "$password"
	univention-app dev-test-setup || rv=$?
	univention-app dev-test \
		--appcenter-server "http://appcenter-test.software-univention.de/" \
		"$app" \
		--binddn "$(ucr get tests/domainadmin/account)" \
		--bindpwdfile "$(ucr get tests/domainadmin/pwdfile)" || rv=$?
	return $rv
}

add_tech_key_authorized_keys() {
	install -m0755 -o0 -g0 -d /root/.ssh
	echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKxi4dwmF9K7gV4JbQUmQ4ufRHcxYOYUHWoIRuj8jLmP1hMOqEmZ43rSRoe2E3xTNg+RAjwkX1GQmWQzzjRIYRpUfwLo+yEXtER1DCDTupLPAT5ulL6uPd5mK965vbE46g50LHRyTGZTbsh1A/NPD7+LNBvgm5dTo/KtMlvJHWDN0u4Fwix2uQfvCSOpF1n0tDh0b+rr01orITJcjuezIbZsArTszA+VVJpoMyvu/I3VQVDSoHB+7bKTPwPQz6OehBrFNZIp4zl18eAXafDoutTXSOUyiXcrViuKukRmvPAaO8u3+r+OAO82xUSQZgIWQgtsja8vsiQHtN+EtR8mIn tech' >>/root/.ssh/authorized_keys
}

assert_admember_mode () {
	# shellcheck source=/dev/null
	. /usr/share/univention-lib/admember.sh
	is_localhost_in_admember_mode
}

# start a local firefox and open umc portal page
start_portal_in_local_firefox () {
	systemctl stop  univention-welcome-screen.service
	install_with_unmaintained --no-install-recommends univention-x-core univention-mozilla-firefox openbox
	X &
	DISPLAY=:0 openbox --config-file /etc/xdg/openbox/rc_no_shortcuts.xml &
	sleep 1
	DISPLAY=:0 firefox "http://$(hostname -f)/univention/portal" &
	sleep 10
	chvt 2
	sleep 1
}

postgres94_update () {
	postgres_update '9.4' '9.6'
}

prepare_domain_for_ucs50_postup () {
	postgres_update '9.6' '11'
}

prepare_domain_for_ucs52_postup () {
	postgres_update '11' '15'
}

postgres_update () {
	local old="${1:?}" new="${2:?}"
	if ! dpkg -l | grep -q '^ii.*postgresql-'"$old"' '; then
		echo "postgresql-$old not installed"
		return 0
	fi
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod -x /usr/sbin/univention-pkgdb-scan
	systemctl stop postgresql.service
	rm -rf "/etc/postgresql/$new"
	apt-get install -y --reinstall "postgresql-$new"
	ucr set postgres11/autostart='yes'
	systemctl unmask postgresql@11-main.service
	pg_dropcluster "$new" main --stop
	systemctl start postgresql.service
	[ -e "/var/lib/postgresql/$new/main" ] && mv "/var/lib/postgresql/$new/main" "/var/lib/postgresql/$new/main.old"
	pg_upgradecluster "$old" main
	DEBIAN_FRONTEND='noninteractive' univention-install --yes "univention-postgresql-$new"
	ucr commit "/etc/postgresql/$new/main/"*
	chown -R postgres:postgres "/var/lib/postgresql/$new"
	[ ! -e /etc/postgresql/11/main/conf.d/ ] && mkdir /etc/postgresql/11/main/conf.d/ && chown postgres:postgres /etc/postgresql/11/main/conf.d/
	systemctl unmask postgresql.service
	systemctl restart postgresql.service
	[ -f /usr/sbin/univention-pkgdb-scan ] && chmod +x "/usr/sbin/univention-pkgdb-scan"
	pg_dropcluster "$old" main --stop
	DEBIAN_FRONTEND='noninteractive' apt-get purge --yes "postgresql-$old"
	systemctl restart postgresql.service
}

dump_systemd_journal () {
	journalctl > /var/log/journalctl.log || echo "Could not dump systemd journal." >&2
}

add_hostname_to_juint_results () {
	local HOSTNAME
	: "${HOSTNAME:=$(hostname)}"
	sed -i "s|<testsuite\>[^<>]*\<name=\"|&${HOSTNAME}.|g;s|<testcase\>[^<>]*\<classname=\"|&${HOSTNAME}.|g" test-reports/*/*.xml
}

prepare_results () {
	add_tech_key_authorized_keys
	dump_systemd_journal
}

add_ucsschool_dev_repo () {
	local majorminor
	majorminor="$(ucr get version/version)"
	cat << EOF > /etc/apt/sources.list.d/ucsschool-dev-repo.list
deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_${majorminor}-0-ucs-school-${majorminor}/all/
deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_${majorminor}-0-ucs-school-${majorminor}/\$(ARCH)/
EOF
}

add_guardian_dev_repo () {
	local majorminor
	majorminor="$(ucr get version/version)"
	cat << EOF > /etc/apt/sources.list.d/guardian-dev-repo.list
deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_${majorminor}-0-guardian/all/
deb [trusted=yes] http://omar.knut.univention.de/build2/ ucs_${majorminor}-0-guardian/\$(ARCH)/
EOF
}

# deprecated (use add_extra_branch_repo)
add_branch_repository () {
	local extra_list="/root/apt-get-branch-repo.list"
	[ -s "$extra_list" ] ||
		return 0
	install -m644 "$extra_list" /etc/apt/sources.list.d/
	apt-get -qq update
}

slugify () {
	iconv -t ascii//TRANSLIT |
		sed "s/'//g;s/[^a-zA-Z0-9]\\+/-/g;s/^-//;s/-\$//;s/.*/\\L&/"
}

# configure branch repository and apt prefs
add_extra_branch_repository () {
	local REPO_SERVER="http://omar.knut.univention.de/build2/git" repo_name
	if [ -n "$UCS_ENV_UCS_BRANCH" ]; then
		repo_name="$(echo "$UCS_ENV_UCS_BRANCH" | slugify)"
		echo "deb [trusted=yes] $REPO_SERVER/$repo_name git main" >"/etc/apt/sources.list.d/$repo_name.list"
		cat >"/etc/apt/preferences.d/99$repo_name.pref" <<__PREF__
Package: *
Pin: release o=Univention,a=git,n=git
Pin-Priority: 1001
__PREF__
		apt-get -qq update
	fi
}

restart_services_bug_47762 () {
	# https://forge.univention.org/bugzilla/show_bug.cgi?id=47762
	# The services needs to be restart otherwise they wouldn't bind
	# to the new IP address
	[ -x /etc/init.d/samba ] ||
		return 0
	/etc/init.d/samba restart
	sleep 15
}

# https://forge.univention.org/bugzilla/show_bug.cgi?id=48157
restart_umc_bug_48157 () {
	sleep 30
	deb-systemd-invoke restart univention-management-console-server || true
}

run_workarounds_before_starting_the_tests () {
	restart_services_bug_47762
	#restart_umc_bug_48157 # Bug is verified for now. Code can be removed if bug is closed.
}

sa_bug53751 () {
	# https://forge.univention.org/bugzilla/show_bug.cgi?id=47030
	# https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=922499
	# https://forge.univention.org/bugzilla/show_bug.cgi?id=49575
	# https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=920348
	local CFG='/etc/ca-certificates.conf'
	[ -f "$CFG" ] &&
		sed -i -e 's=^mozilla/DST_Root_CA_X3.crt=!&=' "$CFG" &&
		update-ca-certificates --certbundle ca-certificates.tmp &&
		mv /etc/ssl/certs/ca-certificates.tmp /etc/ssl/certs/ca-certificates.crt ||
		true

	local BASE='/var/lib/spamassassin/compiled' user='debian-spamd'
	have sa-update &&
		curl https://spamassassin.apache.org/updates/GPG.KEY | sa-update --import -
	have sa-update &&
		sa-update -vv &&
		su -c 'sa-compile' - "$user" &&
		systemctl try-restart spamassassin.service amavis.service
	[ -d "$BASE" ] &&
		find "$BASE" -not -user "$user" -exec chown -v "$user:" {} +
	:
}

fix_certificates53013 () { # <ip>
	# https://forge.univention.org/bugzilla/show_bug.cgi?id=53013
	local ip="${1:?}"
	ucr set ssl/default/hashfunction=sha256 ssl/default/bits=2048

	local hostname domainname ldap_base saml_idp_certificate_certificate saml_idp_certificate_privatekey ucs_server_sso_fqdn server_role ldap_hostdn
	eval "$(ucr shell hostname domainname ldap/base saml/idp/certificate/certificate saml/idp/certificate/privatekey ucs/server/sso/fqdn server/role ldap/hostdn)"
	local fqhn="${hostname:?}.${domainname:?}"

	# Renew host certificate
	univention-certificate update-expired || :
	univention-certificate revoke -name "${fqhn}" || :
	univention-certificate new -name "${fqhn}"

	systemctl try-restart slapd.service apache2.service univention-management-console-server.service || :

	[ -f /var/univention-join/joined ] || return 0

	# Overwrite IP address from KVM template with current IP
	univention-register-network-address --verbose
	udm "computers/${server_role}" modify --dn "${ldap_hostdn}" --set ip="${ip}"
	udm dns/host_record modify --dn relativeDomainName="${ucs_server_sso_fqdn%%.*},zoneName=${ucs_server_sso_fqdn#*.},cn=dns,${ldap_base:?}" --set a="${ip}"
	nscd -i hosts || :

	# Renew SSO certificate
	[ -n "${ucs_server_sso_fqdn:-}" ] || return 0

	univention-certificate revoke -name "${ucs_server_sso_fqdn:?}" || :
	rm -f "${saml_idp_certificate_certificate:?}" "${saml_idp_certificate_privatekey:?}"
	univention-run-join-scripts --force --run-scripts 91univention-saml.inst 92univention-management-console-web-server

	return 0

	# Incomplete alternative: renew SSO certificate manually
	univention-certificate new -name "${ucs_server_sso_fqdn}"
	install -o root -g samlcgi -m 0644 "/etc/univention/ssl/${ucs_server_sso_fqdn}/cert.pem" "${saml_idp_certificate_certificate:?}"
	install -o root -g samlcgi -m 0640 "/etc/univention/ssl/${ucs_server_sso_fqdn}/private.key" "${saml_idp_certificate_privatekey:?}"
	/usr/sbin/univention-directory-listener-ctrl resync univention-saml-simplesamlphp-configuration
	/usr/share/univention-management-console/saml/update_metadata
	# TODO: /usr/share/univention-management-console/saml/idp/*.xml -> https:/${ucs/server/sso/fqdn}/simplesamlphp/saml2/idp/certificate
	# TODO: What else?
}

fake_initial_schema () {
	[ "$(ucr get ldap/server/type)" = master ] && return
	[ -s /var/lib/univention-ldap/schema.conf ] && return
	local tmp
	tmp=$(mktemp)
	printf '# univention_dummy.conf\n\nldap/server/type: master' >"$tmp"
	UNIVENTION_BASECONF="$tmp" univention-config-registry filter \
		</etc/univention/templates/files/etc/ldap/slapd.conf.d/10univention-ldap-server_schema \
		>/var/lib/univention-ldap/schema.conf
	rm -f "$tmp"
}

online_fsresize () {
	# cloud-initramfs-growroot doesn't always work (bug #49337)
	# Try on-line resizing
	echo "Grow root partition"
	local root_device disk part_number
	root_device="$(readlink -f "$(df --output=source / | tail -n 1)")"
	disk="${root_device%[0-9]}"
	part_number="${root_device#"${disk}"}"
	growpart "$disk" "$part_number"
	resize2fs "$root_device"
}

winrm_config () {
	local domain=${1:?missing domain} password=${2:?missing password} user=${3:?missing user} client=${4:?missing client}
	echo -e "[default]\ndomain = ${domain}\npassword = ${password}\nuser = ${user}\nclient = ${client}" > /root/.ucs-winrm.ini
}

# setup for the ucs-$role kvm template (provisioned but not joined)
basic_setup_ucs_role () {
	local masterip="${1:?missing master ip}"
	local admin_password="${2:-univention}"
	# TODO
	#   ... recreate ssh keys ...
	# join non-master systems
	[ "$(ucr get server/role)" = "domaincontroller_master" ] &&
		return 0

	printf '%s' "$admin_password" > /tmp/univention.txt
	ucr set nameserver1="$masterip"
	univention-join -dcaccount Administrator -dcpwd /tmp/univention.txt
}

ucs-winrm () {
	local IMAGE="docker.software-univention.de/ucs-winrm"
	docker run --rm -v /etc/localtime:/etc/localtime:ro -v "$HOME/.ucs-winrm.ini:/root/.ucs-winrm.ini:ro" "$IMAGE" "$@"
}

add_extra_apt_scope () {
	[ -n "$SCOPE" ] ||
		return 0

	if [ "$(echo "$SCOPE" | cut -c1-5)" = "http:" ] || [ "$(echo "$SCOPE" | cut -c1-6)" = "https:" ]; then
		# support: deb [trusted=yes] http://192.168.0.10/build2/git/fbest-12345-foo/ git main
		echo "deb [trusted=yes] $SCOPE" > /etc/apt/sources.list.d/99_extra_scope.list
	else
		echo "deb [trusted=yes] http://192.168.0.10/build2/ ucs_$(ucr get version/version)-0-$SCOPE/all/" > /etc/apt/sources.list.d/99_extra_scope.list
		echo "deb [trusted=yes] http://192.168.0.10/build2/ ucs_$(ucr get version/version)-0-$SCOPE/\$(ARCH)/" >> /etc/apt/sources.list.d/99_extra_scope.list
	fi
	apt-get update -qq || true  # ignore failure, univention-upgrade will do this as well
}

create_version_file_tmp_ucsver () {
	local testing="${1:-false}"
	if [ "$testing" = "true" ]; then
		echo "ucsver=@%@version/version@%@-@%@version/patchlevel@%@+$(date +%Y-%m-%d)" | ucr filter>/tmp/ucs.ver
	elif [ "$testing" = "false" ]; then
		echo 'ucsver=@%@version/version@%@-@%@version/patchlevel@%@+e@%@version/erratalevel@%@' | ucr filter>/tmp/ucs.ver
	else
		return 1
	fi
}

# individualize KVM template
#  create computer account with same position/services/ucsschoolRoles as in template
#  configure new name
#  basic setup
#  restart some services/run some join scripts
change_template_hostname () {
	local hostname="${1:?missing hostname}"
	local primary_ip="${2:?missing primary ip}"
	local admin_password="${3:?missing admin password}"
	local new_fqdn rv=0 server_role old_hostdn old_hostname hostdn admin_user admin_userdn
	new_fqdn="$hostname.$(ucr get domainname)"
	server_role="$(ucr get server/role)"
	old_hostdn="$(ucr get ldap/hostdn)"
	old_hostname="$(ucr get hostname)"
	hostdn="$(ucr get ldap/hostdn | sed "s/^cn=[^,]*/cn=$hostname/")"
	admin_user="Administrator"
	admin_userdn="uid=$admin_user,cn=users,$(ucr get ldap/base)"

	# new name
	ucr set \
		"hostname=$hostname" \
		"ldap/hostdn=$hostdn" \
		"ldap/server/name=$new_fqdn" \
		"hosts/static/${primary_ip}=$(ucr get ldap/master)"

	# create new computer account, with the same position
	# password, services and ucsschool_roles
	udm "computers/$server_role" create \
		--binddn "$admin_userdn" \
		--bindpwd "$admin_password" \
		--position="${old_hostdn#*,}" \
		--set name="$hostname" \
		--set password="$(cat /etc/machine.secret)" \
		--set domain="$(ucr get domainname)" || rv=1
	while read -r service; do
		udm "computers/$server_role" modify --binddn "$admin_userdn" --bindpwd "$admin_password" --dn "$hostdn" --append service="$service"
	done < <(udm computers/domaincontroller_backup list --filter name="$old_hostname" | sed -n 's/^  service: //p')
	while read -r school_role; do
		udm "computers/$server_role" modify --binddn "$admin_userdn" --bindpwd "$admin_password" --dn "$hostdn" --append ucsschoolRole="$school_role"
	done < <(udm computers/domaincontroller_backup list --filter name="$old_hostname" | sed -n 's/^  ucsschoolRole: //p')

	# get new cert
	univention-fetch-certificate "$hostname" "$primary_ip" || rv=1

	# fix some templates
	[ -e /etc/bind/named.conf.samba4 ] && ucr commit /etc/bind/named.conf.samba4

	# systemctl try-restart univention-directory-listener.service univention-management-console-server.service apache2.service postgresql.service || [ $? -eq 5]
	for service in slapd univention-directory-listener univention-management-console-server apache2 postgresql; do
		if service "$service.service" status 2>/dev/null 1>/dev/null; then
			service "$service.service" restart || rv=1
		fi
	done

	# register ip and basic setup
	basic_setup_ucs_joined "$primary_ip" "$admin_password" || rv=1
	wait_for_replication 100 5

	printf '%s' "$admin_password" > /tmp/join_pwd
	univention-run-join-scripts -dcaccount "$admin_user" -dcpwd /tmp/join_pwd --force --run-scripts 05univention-bind || rv=1

	# update ucs-sso
	if [ "$server_role" = "domaincontroller_backup" ]; then
		systemctl stop nscd.service
		univention-run-join-scripts -dcaccount "$admin_user" -dcpwd /tmp/join_pwd --force --run-scripts 91univention-saml || rv=1
		univention-run-join-scripts -dcaccount "$admin_user" -dcpwd /tmp/join_pwd --force --run-scripts 92univention-management-console-web-server || rv=1
		systemctl start nscd.service
	fi

	if [ -e "/usr/lib/univention-install/40ucs-school-import-http-api.inst" ]; then
		univention-run-join-scripts -dcaccount "$admin_user" -dcpwd /tmp/join_pwd --force --run-scripts  40ucs-school-import-http-api
	fi

	rm -f /tmp/join_pwd

	univention-directory-listener-ctrl resync univention-saml-servers univention-saml-simplesamlphp-configuration umc-service-providers || rv=1

	return $rv
}

basic_setup_ucs_joined () {
	local masterip="${1:?missing master ip}"
	local admin_password="${2:-univention}"
	local rv=0 server_role ldap_base domain old_ip urna_rv=0 current_ip i

	server_role="$(ucr get server/role)"
	ldap_base="$(ucr get ldap/base)"
	domain="$(ucr get domainname)"

	if [ "$server_role" = "domaincontroller_master" ]; then
		# sometimes univention-network-common.service fails on the
		# primary for yet unknown reasons, make sure to update the ip address
		local current_ip
		current_ip="$(udm dns/host_record list --filter name=master | sed -n 's/^\W*a: //p')"
		if [ -n "$current_ip" ] && [ "$current_ip" != "$masterip" ]; then
			/usr/sbin/univention-register-network-address --verbose
		fi
	fi

	# TODO
	#  ... recreate ssh keys ...
	# fix ip on non-master systems
	if [ "$server_role" != "domaincontroller_master" ]; then
		ucr set "hosts/static/${masterip}=$(ucr get ldap/master)"
		if [ "$(ucr get server/role)" = "memberserver" ]; then
			ucr set nameserver1="$masterip"
		else
			ucr set ldap/server/ip="$(ucr get "interfaces/$(ucr get interfaces/primary)/address")"
		fi
		ucr unset nameserver2
		deb-systemd-invoke restart univention-directory-listener || rv=1
		for i in $(seq 1 5); do
			univention-register-network-address --verbose && urna_rv=0 && break
			urna_rv=1
			sleep 20
		done
		[ $urna_rv -eq 1 ] && rv=1
		echo $urna_rv

		systemctl restart nscd.service || rv=1
	fi

	# get old ip TODO how to do it correctly?
	old_ip="$(grep "set interfaces/eth0/address=" /var/log/univention/config-registry.replog | tail -1 | awk -F 'old:' '{print $2}')"
	if [ -z "$old_ip" ]; then
		old_ip="$(zgrep "set interfaces/eth0/address=" /var/log/univention/config-registry.replog.1.gz | tail -1 | awk -F 'old:' '{print $2}')"
	fi

	# fix ucs-sso
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		local sso_fqdn sso_hostname
		sso_fqdn="$(ucr get ucs/server/sso/fqdn)"
		sso_hostname="${sso_fqdn%%.*}"
		[ -n "$old_ip" ] && udm dns/host_record modify \
			--dn "relativeDomainName=$sso_hostname,zoneName=$domain,cn=dns,$ldap_base" \
			--remove a="$old_ip"
	fi

	# fix samba/dns settings on samba DC's
	# hacky approach, save the old ip addresses during template creation
	# and fix dns settings until https://forge.univention.org/bugzilla/show_bug.cgi?id=54189
	# is fixed
	if [ -e /var/lib/samba/private/sam.ldb ]; then
		local old_ip ip binddn
		ldap_base="$(ucr get ldap/base)"
		old_ip="$(ucr get internal/kvm/template/old/ip)"
		ip="$(ucr get interfaces/eth0/address)"
		binddn="uid=Administrator,cn=users,$ldap_base"

		if [ -n "$old_ip" ]; then
			udm dns/host_record modify --binddn "$binddn" --bindpwd "$admin_password" \
				--dn "relativeDomainName=ForestDnsZones,zoneName=$domain,cn=dns,$ldap_base" \
				--append a="$ip" --remove a="$old_ip"
			udm dns/host_record modify --binddn "$binddn" --bindpwd "$admin_password" \
				--dn "relativeDomainName=DomainDnsZones,zoneName=$domain,cn=dns,$ldap_base" \
				--append a="$ip" --remove a="$old_ip"
			udm dns/host_record modify --binddn "$binddn" --bindpwd "$admin_password" \
				--dn "relativeDomainName=gc._msdcs,zoneName=$domain,cn=dns,$ldap_base" \
				--append a="$ip" --remove a="$old_ip"
			udm dns/host_record modify --binddn "$binddn" --bindpwd "$admin_password" \
				--dn "relativeDomainName=ucs-sso,zoneName=$domain,cn=dns,$ldap_base" \
				--append a="$ip" --remove a="$old_ip"
			udm dns/forward_zone modify --binddn "$binddn" --bindpwd "$admin_password" \
				--dn "zoneName=$domain,cn=dns,$ldap_base" \
				--remove a="$old_ip" --append a="$ip"
		fi

		# update primary ip
		if [ "$(ucr get server/role)" != "domaincontroller_master" ]; then
			local master old_ip_master
			master="$(ucr get ldap/master)"
			old_ip_master="$(dig +short "$master")"
			if [ -n "$old_ip_master" ]; then
				samba-tool dns update -U"Administrator%$admin_password" localhost "$domain" "${master%%.*}" A "$old_ip_master" "$masterip"
				/etc/init.d/samba restart || rv=1
			fi
		fi
	fi
	if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
		# Flush old ip's from bind
		/usr/sbin/rndc retransfer "$(hostname -d)."
	fi

	return $rv
}

# add entry to ssh environment to pass variables via env
add_to_ssh_environment () {
	local entry="${1:?missing entry}"
	# add newline if missing
	[ -n "$(tail -c1 /root/.ssh/environment)" ] && printf '\n' >>/root/.ssh/environment
	echo "$entry" >> /root/.ssh/environment
}

# make env file available in ssh session
set_env_variables_from_env_file () {
	local env_file="${1:?missing env file}" entry
	while read -r entry; do
		add_to_ssh_environment "$entry"
	done < "$env_file"
	return 0
}

copy_test_data_cache() {
	univention-install -y sshpass
	local root_password="${1:?missing root password}" ip
	shift
	for ip in "$@"; do
		sshpass -p "$root_password" scp -r  -o StrictHostKeyChecking=no -o UpdateHostKeys=no /var/lib/test-data root@"$ip":/var/lib/ || return 1
	done
}

# create python diskcache for users and groups
# (used in performance template job)
create_and_copy_test_data_cache () {
	univention-install -y python3-pip
	pip3 install diskcache
	python3 - <<"EOF" || return 1
from diskcache import Index
from univention.udm import UDM

udm = UDM.admin().version(2)
udm_users = udm.get("users/user")
udm_groups = udm.get("groups/group")
users_db = Index("/var/lib/test-data/users")
groups_db = Index("/var/lib/test-data/groups")

for user in udm_users.search():
    if "hidden" not in user.props.objectFlag:
        users_db.update(
            {
                user.props.username: {
                    "dn": user.dn,
                    "username": user.props.username,
                    "password": "univention",
                }
            }
        )

for group in udm_groups.search():
    groups_db.update(
        {
            group.props.name: {
                "name": group.props.name,
                "dn": group.dn,
            }
        }
    )

users_db.cache.close()
groups_db.cache.close()
EOF
	copy_test_data_cache "$@"

}

cleanup_translog () {
	deb-systemd-invoke stop univention-directory-listener univention-directory-notifier || return 1
	/usr/share/univention-directory-notifier/univention-translog stat || return 1
	/usr/share/univention-directory-notifier/univention-translog prune -1000 || return 1
}

performance_template_settings () {
	local mdb_maxsize="${1:-12884901888}"
	ucr set \
		directory/manager/user/primarygroup/update=false \
		nss/group/cachefile/invalidate_interval=disabled \
		ldap/database/mdb/maxsize="$mdb_maxsize" \
		listener/cache/mdb/maxsize="$mdb_maxsize" \
		slapd/backup=disabled
}

################################################################################
# performance measurement to syslog
#
# this code is meant to use log program from the environment variable `LOGGER`
# and defaults to the `logger` utility without any parameters. Since the system
# log can already be distributed across several hosts, it is relatively simple
# and stable compared to a database logging mechanism. Because the risk to
# avoid is, that remote logging could eventually break our tests.
#
# In its default configuration all messages can be extracted from the log with:
#     journalctl -t root
# where `root` is called 'the identifier', the enitity to place the message
# in syslog. This can be renamed, e.g. to foo as in
#     export LOGGER='logger -t foo'
# before running utils.sh.
#
################################################################################

START="$(date +%s%N)"

log_reset_timer () {
	START=$(date +%s%N)
}

log_call_stack () {
	local i caller
	for ((i=0; i<10; i++))
	do
		caller="$(caller "$i")" || break
		echo "$i: $caller"
	done
}

log_execution_time () {
	${LOGGER:-logger} "$BASH_EXECUTION_STRING needed $(( ($(date +%s%N) - START) / 1000000)) ms"
}


# trap log_execution_time EXIT

# vim:set filetype=sh ts=4:
