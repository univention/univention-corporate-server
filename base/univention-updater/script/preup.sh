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

# shellcheck disable=SC2317

export DEBIAN_FRONTEND=noninteractive

UPDATE_NEXT_VERSION="$1"
UPDATER_LOG="/var/log/univention/updater.log"
exec 3>>"$UPDATER_LOG"

###CHECKS###

readcontinue () {
	local var
	while true
	do
		echo -n "Do you want to continue [Y/n]? "
		read -r var
		case "$var" in
		''|y|Y) return 0 ;;
		n|N) return 1 ;;
		*) echo "" ;;
		esac
	done
}

echo
echo "HINT:"
echo "Please check the release notes carefully BEFORE updating to UCS ${UPDATE_NEXT_VERSION}:"
echo ""
echo "UCS 5.1-0 is an intermediate release and must not be used in production."
echo "After the update to UCS 5.1-0 make sure to immediately update to UCS 5.2-0,"
echo "the updater will ask you to do so."
echo ""
echo "All the necessary information is therefore in the release notes for UCS 5.2-0."
echo ""
echo " English version: https://docs.software-univention.de/release-notes/5.2-0/en/"
echo " German version:  https://docs.software-univention.de/release-notes/5.2-0/de/"
echo
echo "Please also consider documents of following release updates and"
echo "3rd party components."
echo
if ! is_ucr_false update/warning/releasenotes && [ "${update_warning_releasenotes_internal:-}" != "no" ]
then
	if [ "$UCS_FRONTEND" = "noninteractive" ]; then
		echo "Update will wait here for 60 seconds..."
		echo "Press CTRL-c to abort or press ENTER to continue"
		# BUG: 'read -t' is the only bash'ism in this file, therefore she-bang has to be /bin/bash not /bin/sh!
		# shellcheck disable=SC2034
		read -r -t 60 somevar
	else
		readcontinue || exit 1
	fi
fi

echo ""

update_check_ssh () {
	[ -n "$SSH_CLIENT" ] || return 0
	[ "${update51_ignoressh:-}" = "yes" ] && return 0
	[ "${update52_ignoressh:-}" = "yes" ] && return 0
	echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
	echo "Please log in under the console or re-run with \"--ignoressh\" to ignore it."
	return 1
}

update_check_term () {
	[ "$TERM" = "xterm" ] || return 0
	[ "${update51_ignoreterm:-}" = "yes" ] && return 0
	[ "${update52_ignoreterm:-}" = "yes" ] && return 0
	echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
	echo "Please log in under the console or re-run with \"--ignoreterm\" to ignore it."
	return 1
}

# call custom preup script if configured
if [ -n "${update_custom_preup:-}" ]; then
	if [ -f "$update_custom_preup" ]; then
		if [ -x "$update_custom_preup" ]; then
			echo "Running custom preupdate script $update_custom_preup"
			"$update_custom_preup" "$UPDATE_NEXT_VERSION" >&3 2>&3
			echo "Custom preupdate script $update_custom_preup exited with exitcode: $?" >&3
		else
			echo "Custom preupdate script $update_custom_preup is not executable" >&3
		fi
	else
		echo "Custom preupdate script $update_custom_preup not found" >&3
	fi
fi

prune_kernel () {
	is_ucr_true "update${VERSION}/pruneoldkernel" || return 0
	univention-prune-kernels
}

prune_kernel  # do this before update_check_disk_space

checks

# Several LDAP objects are no longer supported with UCS 5 and are removed automatically.
delete_obsolete_objects

# save ucr settings
[ -d "${updateLogDir:?}" ] ||
	install -m0700 -o root -d "$updateLogDir"
cp /etc/univention/base*.conf "$updateLogDir/"
ucr dump > "$updateLogDir/ucr.dump"

# move old initrd files in /boot
initrd_backup='/var/backups/univention-initrd.bak'
[ -d "$initrd_backup" ] ||
	install -m 0755 -o root -g root -d "$initrd_backup"
mv /boot/*.bak "$initrd_backup" >/dev/null 2>&1


# Bug #52923 #57296: disable fetchmail during update to prevent aborting update
if dpkg -l univention-fetchmail 2>&3 | grep ^ii  >&3 ; then
	if [ -z "$(ucr search "^fetchmail/autostart/update510$")" ] ; then
		ucr set fetchmail/autostart/update510="$(ucr get fetchmail/autostart)" >&3
	fi
	ucr set fetchmail/autostart=no >&3 2>&3
	systemctl stop fetchmail >&3 2>&3 || :
fi

# Bug #58248: univention-ldap-usercert is a dependency of univention-usercert
# if univention-usercert was installed (cool-solution), it gets uninstalled
# during the update to 5.2-0. If the customer didn't follow the instructions
# exactly this autoremoves univention-ldap-usercert, causing schema problems.
# apt-mark manual always returns 0. even if not installed
if dpkg -l univention-ldap-usercert | grep ^ii; then
	apt-mark manual univention-ldap-usercert
fi

# set KillMode of atd service to process to save the children from getting killed
# up to this point the updater process is a child of atd as well
install -m 0755 -o root -g root -d /etc/systemd/system/atd.service.d
echo -en "[Service]\nKillMode=process" > /etc/systemd/system/atd.service.d/update510.conf
systemctl daemon-reload

# ensure that en_US is included in list of available locales (Bug #44150)
case "${locale:-}" in
	*en_US*) ;;
	*) /usr/sbin/univention-config-registry set locale="${locale:+$locale }en_US.UTF-8:UTF-8" ;;
esac

# autoremove before the update
is_ucr_true update52/skip/autoremove ||
	DEBIAN_FRONTEND=noninteractive apt-get -y --allow-unauthenticated --allow-downgrades --allow-remove-essential --allow-change-held-packages autoremove >&3 2>&3

deactivate_old_package_sources () {
	# disable UCS 5.0 package sources to avoid mixing package versions during update
	local sources_lists
	sources_lists=("/etc/apt/sources.list.d/15_ucs-online-version.list" "/etc/apt/sources.list.d/20_ucs-online-component.list")
	for sources_list in "${sources_lists[@]}"; do
		mv "$sources_list" "${sources_list}.upgrade510.bak"
	done
}
deactivate_old_package_sources

# Issue univention/ucs#2542: make sure we keep univention-appcenter-docker
if dpkg -l univention-appcenter-docker 2>&3 | grep ^ii  >&3 ; then
	ucr set update/510/univention-appcenter-docker=true
fi

# src postgres-15
pin_packages="libecpg-compat3 libecpg-compat3-dbgsym libecpg-dev libecpg-dev-dbgsym libecpg6 libecpg6-dbgsym libpgtypes3 libpgtypes3-dbgsym libpq-dev libpq5 libpq5-dbgsym postgresql-15 postgresql-15-dbgsym postgresql-client-15 postgresql-client-15-dbgsym postgresql-doc-15 postgresql-plperl-15 postgresql-plperl-15-dbgsym postgresql-plpython3-15 postgresql-plpython3-15-dbgsym postgresql-pltcl-15 postgresql-pltcl-15-dbgsym postgresql-server-dev-15"

# src libzstd
pin_packages+=" libzstd-dev libzstd1 libzstd1-dbgsym libzstd1-udeb zstd zstd-dbgsym"

[ -f /etc/apt/preferences.d/99ucs510.pref ] ||
cat >/etc/apt/preferences.d/99ucs510.pref <<__PREF__
Package: $pin_packages
Pin: release l=Univention Corporate Server, v=5.1.0
Pin-Priority: 1001
__PREF__
[ -f /etc/apt/apt.conf.d/99ucs510 ] || echo 'APT::Get::Allow-Downgrades "true";' >/etc/apt/apt.conf.d/99ucs510


# Issue univention/ucs#2548: make sure we keep univention-monitoring-client and univention-nagios-client
if dpkg -l univention-monitoring-client 2>&3 | grep ^ii  >&3 ; then
  ucr set update/510/univention-monitoring-client=true
fi
if dpkg -l univention-nagios-client 2>&3 | grep ^ii  >&3 ; then
  ucr set update/510/univention-nagios-client=true
fi

# univention/ucs#1945 - disable php7.0
# apache2: Syntax error on line 146 of /etc/apache2/apache2.conf: Syntax error on line 3 of /etc/apache2/mods-enabled/php7.0.load:
#          Cannot load /usr/lib/apache2/modules/libphp7.0.so into server: /usr/lib/apache2/modules/libphp7.0.so:
#          cannot open shared object file: No such file or directory Action '--configtest' failed.
a2dismod php7.0 || true

# univention/ucs#1951 - dirty hack to migrate the app scripts from py2 to py2 (admin-dashboard)
test -e /usr/sbin/univention-dashboard-management && sed -i s'|/usr/bin/python2.7|/usr/bin/python3|' /usr/sbin/univention-dashboard-management
test -e /usr/sbin/univention-metrics-domain && sed -i s'|/usr/bin/python2.7|/usr/bin/python3|' /usr/sbin/univention-metrics-domain

# Pre-upgrade
preups=""
${update_commands_update:-false} >&3 2>&3
for pkg in $preups; do
	if dpkg -l "$pkg" 2>&3 | grep ^ii  >&3 ; then
		echo -n "Starting pre-upgrade of $pkg: "
		if ! ${update_commands_install:-false} "$pkg" >&3 2>&3
		then
			echo "failed."
			echo "ERROR: Failed to upgrade $pkg."
			exit 1
		fi
		echo "done."
	fi
done

# Bug #56232: Enable the support for numeric user ID's if it is required
if [ "${server_role:-}" = "domaincontroller_master" ] && dpkg --compare-versions "$1" eq "5.1"
then
	echo "Checking for usernames and groups with legacy format. This can take a few minutes..."

	echo "Checking usernames..."
	if univention-ldapsearch -LLL "objectClass=person" uid | ldapsearch-decode64 | grep -qoP "(?<=uid: )[0-9]+$"; then
		echo "Legacy username format required. Creating policy..."

		udm policies/registry create \
			--position "cn=config-registry,cn=policies,${ldap_base:?}" \
			--set name=enable-legacy-username-format \
			--set registry="directory/manager/user/enable-legacy-username-format true"

		udm container/dc modify \
			--dn "$ldap_base" \
			--policy-reference "cn=enable-legacy-username-format,cn=config-registry,cn=policies,$ldap_base"
	fi

	echo "Checking groups..."
	if univention-ldapsearch -LLL "univentionObjectType=groups/group" cn | ldapsearch-decode64 | grep -qoP "(?<=cn: )[0-9]+$"; then
		echo "Legacy group cn format required. Creating policy..."

		udm policies/registry create \
			--position "cn=config-registry,cn=policies,$ldap_base" \
			--set name=enable-legacy-group-cn-format \
			--set registry="directory/manager/group/enable-legacy-cn-format true"

		udm container/dc modify \
			--dn "$ldap_base" \
			--policy-reference "cn=enable-legacy-group-cn-format,cn=config-registry,cn=policies,$ldap_base"
	fi
fi

echo "** Starting: apt-get -s -o Debug::pkgProblemResolver=yes dist-upgrade" >&3 2>&3
apt-get -s -o Debug::pkgProblemResolver=yes dist-upgrade >&3 2>&3

echo ""
echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
