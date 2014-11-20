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
		echo -e "#!/bin/sh\nroute del default ; route add default gw 10.210.216.13" >>/etc/network/if-up.d/z_route
		chmod +x /etc/network/if-up.d/z_route
		/etc/network/if-up.d/z_route
		sleep 10 # just wait a few seconds to give the amazone cloud some time
		ucr set --force updater/identify="UCS (EC2 Test)"
		ucr set update/check/cron/enabled=false update/check/boot/enabled=false
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
		if [ -x /root/activate-$(ucr get version/version)-errata-test-scope.sh ]
		then
			/root/activate-$(ucr get version/version)-errata-test-scope.sh
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

upgrade_to_latest ()
{
	univention-upgrade --noninteractive --ignoreterm --ignoressh "$@" && return 0
	(echo "ERROR: univention-upgrade failed in attempt 1 with exitcode $?"; ps faxwww ; ucr search update/check)
	# Workaround for Bug #31561
	sleep 300
	univention-upgrade --noninteractive --ignoreterm --ignoressh "$@" && return 0
	(echo "ERROR: univention-upgrade failed in attempt 2 with exitcode $?"; ps faxwww ; ucr search update/check)
	return 1
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
	local srv
	ucr set nameserver1="$(sed -ne 's|^nameserver=||p' /var/cache/univention-system-setup/profile)"
	echo -n "univention" >/tmp/univention
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

run_tests ()
{
	LANG=de_DE.UTF-8 ucs-test -E dangerous -F junit -l "ucs-test.log" -p producttest "$@"
}

run_join_scripts ()
{
	if [ "$(ucr get server/role)" = "domaincontroller_master" ]; then
		univention-run-join-scripts
	else
 		echo -n "univention" >/tmp/univention
		univention-run-join-scripts -dcaccount Administrator -dcpwd /tmp/univention
	fi
}

do_reboot () {
	reboot
}

promote_ad_w2k12 ()
{
	local HOST="$1"
	local DOMAIN="$2"
	if [[ ! -z "$HOST" ]] && [[ ! -z "$DOMAIN" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.promote_ad('Win2008R2', 'Win2008R2')
"
	else
		echo "You must specify an host address domain name."
	fi
}

promote_ad_w2k8 ()
{
	local HOST="$1"
	local DOMAIN="$2"
	if [[ ! -z "$HOST" ]] && [[ ! -z "$DOMAIN" ]]; then
	python -c "
import univention.winexe
win=univention.winexe.WinExe('$DOMAIN', 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.promote_ad('Win2008', 'Win2008')
"
	else
		echo "You must specify an host address domain name."
	fi
}

shutdown_windows_host ()
{
	local HOST="$1"
	python -c "
import univention.winexe
win=univention.winexe.WinExe('dummydomain', 'administrator', 'Univention@99', 'testadmin', 'Univention@99', 445, '$HOST')
win.shutdown_remote_win_host()
"
}

# vim:set filetype=sh ts=4:
