#!/bin/bash
#
# Copyright (C) 2010-2017 Univention GmbH
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

export DEBIAN_FRONTEND=noninteractive

UPDATER_LOG="/var/log/univention/updater.log"
exec 3>>"$UPDATER_LOG"
UPDATE_NEXT_VERSION="$1"

echo "Running preup.sh script" >&3
date >&3

eval "$(univention-config-registry shell)" >&3 2>&3

conffile_is_unmodified () {
	# conffile_is_unmodified <conffile>
	# returns exitcode 0 if given conffile is unmodified
	if [ ! -f "$1" ]; then
		return 1
	fi
	local chksum="$(md5sum "$1" | awk '{ print $1 }')"
	local fnregex="$(python -c 'import re,sys;print re.escape(sys.argv[1])' "$1")"
	for testchksum in $(dpkg-query -W -f '${Conffiles}\n' | sed -nre "s,^ $fnregex ([0-9a-f]+)( .*)?$,\1,p") ; do
		if [ "$testchksum" = "$chksum" ] ; then
			return 0
		fi
	done
	return 1
}

readcontinue ()
{
	while true ; do
		echo -n "Do you want to continue [Y/n]? "
		read var
		if [ -z "$var" -o "$var" = "y" -o "$var" = 'Y' ]; then
			return 0
		elif [ "$var" = "n" -o "$var" = 'N' ]; then
			return 1
		else
			echo ""
			continue
		fi
	done
}

###########################################################################
# RELEASE NOTES SECTION (Bug #19584)
# Please update URL to release notes and changelog on every release update
###########################################################################
echo
echo "HINT:"
echo "Please check the release notes carefully BEFORE updating to UCS ${UPDATE_NEXT_VERSION}:"
echo " English version: https://docs.software-univention.de/release-notes-4.2-0-en.html"
echo " German version:  https://docs.software-univention.de/release-notes-4.2-0-de.html"
echo
echo "Please also consider documents of following release updates and"
echo "3rd party components."
echo
if [ ! "$update_warning_releasenotes" = "no" -a ! "$update_warning_releasenotes" = "false" -a ! "$update_warning_releasenotes_internal" = "no" ] ; then
	if [ "$UCS_FRONTEND" = "noninteractive" ]; then
		echo "Update will wait here for 60 seconds..."
		echo "Press CTRL-c to abort or press ENTER to continue"
		# BUG: 'read -t' is the only bash'ism in this file, therefore she-bang has to be /bin/bash not /bin/sh!
		read -t 60 somevar
	else
		readcontinue || exit 1
	fi
fi

echo ""

# check if user is logged in using ssh
if [ -n "$SSH_CLIENT" ]; then
	if [ "$update42_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoressh\" to ignore it."
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update42_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoreterm\" to ignore it."
		exit 1
	fi
fi

# shell-univention-lib is proberly not installed, so use a local function
is_ucr_true () {
	local value
	value="$(/usr/sbin/univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
		1|yes|on|true|enable|enabled) return 0 ;;
		0|no|off|false|disable|disabled) return 1 ;;
		*) return 2 ;;
	esac
}

# Bug 44601
if [ "$(update-alternatives --query nc|sed -nre 's/^Value:\s+//p')" != '/bin/nc.openbsd' ]
then
	echo "WARNING: Please install netcat-openbsd and run"
	echo "            update-alternatives --auto nc"
	echo "         for the update to proceed."
	exit 1
fi

# Bug #44915:
echo "Trying to detect if migration to dependency based boot will fail:" >&3
insserv_problem=0
for service in $(LC_ALL=C insserv --dryrun 2>&1 | sed -nre 's/^insserv: script (.*?): service (.*?) already provided!$/\2/p')
do
	echo "WARNING: ${service} is provided by multiple scripts in /etc/init.d/"
	insserv_problem=1
done

for initscript in /etc/init.d/*
do
	package=$(dpkg -S "$initscript" 2>/dev/zero | sed -nre 's|^([^ ]+): '"$initscript"'|\1|p')
	if [ -n "$package" -a "$package" != "univention-system-setup-boot" ]
	then
		status=$(dpkg-query --showformat='${db:Status-Abbrev}\n' --show "$package")
		if [ "$status" = 'rc ' ]
		then
			echo "WARNING: Removed, but configured, package $package left $initscript behind"
			insserv_problem=1
		fi
	fi
done

if insserv --dryrun 1>&3 2>&3
then
	echo "insserv --dryrun: OK" >&3
else
	echo "insserv --dryrun: FAILED" >&3
	echo "WARNING: The /etc/init.d/*-scripts can not be migrated to dependency based boot order."
	echo "         Check /etc/init.d/ for old init scripts."
	insserv_problem=1
fi
if [ "$insserv_problem" -ne 0 ]
then
	if is_ucr_true update42/ignore_insserv
	then
		echo "WARNING: update42/ignore_insserv is set to true. Skipping as requested."
	else
		echo "         Aborting, because the update would likely fail."
		echo "         Please check and fix the aforementioned issues."
		echo "         (To ignore, set the UCRV variable update42/ignore_insserv to yes)"
		exit 1
	fi
fi


# save ucr settings
updateLogDir="/var/univention-backup/update-to-$UPDATE_NEXT_VERSION"
if [ ! -d "$updateLogDir" ]; then
	mkdir -p "$updateLogDir"
fi
cp /etc/univention/base*.conf "$updateLogDir/"
ucr dump > "$updateLogDir/ucr.dump"

# call custom preup script if configured
if [ ! -z "$update_custom_preup" ]; then
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

## check for hold packages
hold_packages=$(LC_ALL=C dpkg -l | grep ^h | awk '{print $2}')
if [ -n "$hold_packages" ]; then
	echo "WARNING: Some packages are marked as hold -- this may interrupt the update and result in an inconsistent"
	echo "system!"
	echo "Please check the following packages and unmark them or set the UCR variable update42/ignore_hold to yes"
	for hp in $hold_packages; do
		echo " - $hp"
	done
	if is_ucr_true update42/ignore_hold; then
		echo "WARNING: update42/ignore_hold is set to true. Skipped as requested."
	else
		exit 1
	fi
fi

## Bug #44650 begin - check slapd on member
if [ -e "$(which slapd)" -a "$server_role" = "memberserver" ]; then
	echo "WARNING: The ldap server is installed on your memberserver. This is not supported"
	echo "         and may lead to problems during the update. Please deinstall the package"
	echo "         *slapd* from this system with either the command line tool univention-remove "
	echo "           -> univention-remove slapd"
	echo "         or via the package management in the Univention Management Console."
	echo "         Make sure that only the package slapd gets removed!"
	echo "         This check can be disabled by setting the UCR variable"
	echo "         update42/ignore_slapd_on_member to yes."
	if is_ucr_true update42/ignore_slapd_on_member; then
		echo "WARNING: update42/ignore_slapd_on_member is set to true. Skipped as requested."
	else
		exit 1
	fi
fi
## Bug #44650 end

#################### Bug #22093

list_passive_kernels () {
	kernel_version="$1"
	dpkg-query -W -f '${Package}\n' "linux-image-${kernel_version}-ucs*" 2>/dev/null |
		fgrep -v "linux-image-$(uname -r)"
}

get_latest_kernel_pkg () {
	# returns latest kernel package for given kernel version
	# currently running kernel is NOT included!

	kernel_version="$1"

	latest_dpkg=""
	latest_kver=""
	for kver in $(list_passive_kernels "$kernel_version") ; do
		dpkgver="$(apt-cache show "$kver" 2>/dev/null | sed -nre 's/Version: //p')"
		if dpkg --compare-versions "$dpkgver" gt "$latest_dpkg" ; then
			latest_dpkg="$dpkgver"
			latest_kver="$kver"
		fi
	done
	echo "$latest_kver"
}

pruneOldKernel () {
	# removes all kernel packages of given kernel version
	# EXCEPT currently running kernel and latest kernel package
	# ==> at least one and at most two kernel should remain for given kernel version
	kernel_version="$1"

	list_passive_kernels "$kernel_version" |
		fgrep -v "$(get_latest_kernel_pkg "$kernel_version")" |
		DEBIAN_FRONTEND=noninteractive xargs -r apt-get -o DPkg::Options::=--force-confold -y --force-yes purge
}

if [ "$update42_pruneoldkernel" = "yes" ]; then
	echo -n "Purging old kernel... " | tee -a "$UPDATER_LOG"
	for kernel_version in 2.6.* 3.2.0 3.10.0 3.16 3.16.0 4.1.0; do
		pruneOldKernel "$kernel_version" >>"$UPDATER_LOG" 2>&1
	done
	echo "done" | tee -a "$UPDATER_LOG"
fi

#####################

if mountpoint -q /usr
then
	echo "failed"
	echo "ERROR:   /usr/ seems to be a separate file system, which is no longer supported."
	echo "         Mounting file systems nowadays requires many helpers, which use libraries"
	echo "         and other resources from /usr/ by default. With a separate /usr/ they"
	echo "         often break in subtle ways or lead to hard to debug boot problems."
	echo "         As such the content of /usr/ must be moved to the root file system before"
	echo "         the system can be upgraded to UCS-4.2. This procedure should be performed"
	echo "         manually and might require resizing the file systems. It is described at"
	echo "         <http://sdb.univention.de/1386>."
	echo ""
	exit 1
fi

check_space () {
	partition=$1
	size=$2
	usersize=$3
	echo -n "Checking for space on $partition: "
	if [ `df -P "$partition" | tail -n1 | awk '{print $4}'` -gt "$size" ]; then
		echo "OK"
	else
		echo "failed"
		echo "ERROR:   Not enough space in $partition, need at least $usersize."
		echo "         This may interrupt the update and result in an inconsistent system!"
		echo "         If necessary you can skip this check by setting the value of the"
		echo "         config registry variable update42/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		if [ "$partition" = "/boot" -a ! "$update42_pruneoldkernel" = "yes" ] ; then
			echo "         Old kernel versions on /boot can be pruned automatically during"
			echo "         next update attempt by setting config registry variable"
			echo "         update42/pruneoldkernel to \"yes\"."
		fi
		echo ""
		# kill the running univention-updater process
		exit 1
	fi
}

fail_if_role_package_will_be_removed ()
{
	local role_package

	case "$server_role" in
		domaincontroller_master) role_package="univention-server-master" ;;
		domaincontroller_backup) role_package="univention-server-backup" ;;
		domaincontroller_slave) role_package="univention-server-slave" ;;
		memberserver) role_package="univention-server-member" ;;
		basesystem) role_package="univention-basesystem" ;;
	esac

	test -z "$role_package" && return

	#echo "Executing: LC_ALL=C $update_commands_distupgrade_simulate | grep -q "^Remv $role_package""  >&3 2>&3
	LC_ALL=C $update_commands_distupgrade_simulate 2>&1 | grep -q "^Remv $role_package"
	if [ $? = 0 ]; then
		echo "ERROR: The pre-check of the update calculated that the"
		echo "       essential software package $role_package will be removed"
		echo "       during the upgrade. This could result into a broken system."
		echo
		# If you really know what you are doing, you can skip this check by
		# setting the UCR variable update/commands/distupgrade/simulate to /bin/true.
		# But you have been warned!
		# In this case, you have to set the UCR variable after the update back
		# to the old value which can be get from /var/log/univention/config-registry.replog
		echo "       Please contact the Univention Support in case you have an Enterprise"
		echo "       Subscription. Otherwise please try the Univention Forum"
		echo "       http://forum.univention.de/"
		exit 1
	fi
}


# move old initrd files in /boot
initrd_backup=/var/backups/univention-initrd.bak/
if [ ! -d "$initrd_backup" ]; then
	mkdir "$initrd_backup"
fi
mv /boot/*.bak /var/backups/univention-initrd.bak/ >/dev/null 2>&1

# check space on filesystems
if [ "$update42_checkfilesystems" != "no" ]
then
	check_space "/var/cache/apt/archives" "4000000" "4000 MB"
	check_space "/boot" "100000" "100 MB"
	check_space "/" "4000000" "4000 MB"
else
	echo "WARNING: skipped disk-usage-test as requested"
fi


echo -n "Checking for package status: "
if dpkg -l 2>&1 | LC_ALL=C grep "^[a-zA-Z][A-Z] " >&3 2>&3
then
	echo "failed"
	echo "ERROR: The package state on this system is inconsistent."
	echo "       Please run 'dpkg --configure -a' manually"
	exit 1
fi
echo "OK"

if [ -x /usr/sbin/slapschema ]; then
	echo -n "Checking LDAP schema: "
	if ! /usr/sbin/slapschema >&3 2>&3; then
		echo "failed"
		echo "ERROR: There is a problem with the LDAP schema on this system."
		echo "       Please check $UPDATER_LOG or run 'slapschema' manually."
		exit 1
	fi
	echo "OK"
fi

# check for valid machine account
if [ -f /var/univention-join/joined -a ! -f /etc/machine.secret ]
then
	echo "ERROR: The credentials for the machine account could not be found!"
	echo "       Please re-join this system."
	exit 1
fi

eval "$(ucr shell server/role ldap/base ldap/hostdn ldap/server/name)"
if [ -n "$server_role" -a "$server_role" != "basesystem" -a -n "$ldap_base" -a -n "$ldap_hostdn" ]
then
	ldapsearch -x -D "$ldap_hostdn" -w "$(< /etc/machine.secret)" -b "$ldap_base" -s base &>/dev/null
	if [ $? -eq 49 ]
	then
		echo "ERROR: A LDAP connection to the configured LDAP servers with the machine"
		echo "       account has failed (invalid credentials)!"
		echo "       This MUST be fixed before the update can continue."
		echo
		echo "       This problem can be corrected by setting the content of the file"
		echo "       /etc/machine.secret to the password of the computer object using"
		echo "       Univention Management Console."
		exit 1
	fi
fi

# check for DC Master UCS version
check_master_version ()
{
	if [ -f /var/univention-join/joined ]; then
		if [ "$server_role" != domaincontroller_master -a "$server_role" != basesystem ]; then
			master_version="$(univention-ssh /etc/machine.secret ${hostname}\$@$ldap_master /usr/sbin/ucr get version/version 2>/dev/null)" >&3 2>&3
			master_patchlevel="$(univention-ssh /etc/machine.secret ${hostname}\$@$ldap_master /usr/sbin/ucr get version/patchlevel 2>/dev/null)" >&3 2>&3
			python -c 'from univention.lib.ucs import UCS_Version
import sys
master=UCS_Version("'$master_version'-'$master_patchlevel'")
me=UCS_Version("'$version_version'-'$version_patchlevel'")
if master <= me:
	sys.exit(1)
'
			if [ $? != 0 ]; then
				echo "WARNING: Your domain controller master is still on version $master_version-$master_patchlevel."
				echo "         It is strongly recommended that the domain controller master is"
				echo "         always the first system to be updated during a release update."

				if is_ucr_true update42/ignore_version; then
					echo "WARNING: update42/ignore_version is set to true. Skipped as requested."
				else
					echo "This check can be skipped by setting the UCR"
					echo "variable update42/ignore_version to yes."
					exit 1
				fi
			fi
		fi
	fi
}
check_master_version

# check that no apache configuration files are manually adjusted; Bug #43520
check_overwritten_umc_templates () {
	univention-check-templates 2>/dev/null | grep /etc/univention/templates/files/etc/apache2/sites-available/ >>"$UPDATER_LOG" 2>&1
	if [ $? = 0 ]; then
		echo "WARNING: There are modified Apache configuration files in /etc/univention/templates/files/etc/apache2/sites-available/."
		echo "Please restore the original configuration files before upgrading and apply the manual changes again after the upgrade succeeded."
		if is_ucr_true update42/ignore_apache_template_checks; then
			echo "WARNING: update42/ignore_apache_template_checks is set to true. Skipped as requested."
		else
			echo "This check can be skipped by setting the UCR"
			echo "variable update42/ignore_apache_template_checks to yes."
			exit 1
		fi
	fi
}
check_overwritten_umc_templates

# Bug 44281, block update for univention App appliances until appliance
# package has been updated...
check_app_appliance () {
	if dpkg -l univention-app-appliance >/dev/null 2>&1
	then
		echo "ERROR: The UCS 4.2 update is not yet available for UCS app appliances."
		echo "       Please try to update your system to UCS 4.2 at a later point."
		exit 1
	fi
}
check_app_appliance

# Bug 41868, fix old computer objects, can be removed after 4.2-0
if ! is_ucr_true update42/skip/computerobjectcheck; then
	if [ "domaincontroller_master" = "$server_role" -a -e /etc/ldap.secret -a -e /var/univention-join/joined ]; then
		while read dn; do
			echo "fixing objectclass (adding shadowAccount) on: $dn" >>"$UPDATER_LOG"
			echo "dn: $dn
changetype: modify
add: objectClass
objectClass: shadowAccount" | ldapmodify -x -D "cn=admin,$ldap_base" -y /etc/ldap.secret >>"$UPDATER_LOG" 2>&1
		done < <( \
			univention-ldapsearch -LLL \
			'(&(objectClass=univentionHost)(objectClass=posixAccount)(!(objectClass=shadowAccount)))' dn 2>>"$UPDATER_LOG" \
			| ldapsearch-wrapper \
			| sed -n 's/^dn: \(.*\)/\1/p')
	fi
fi

# Bug 43639, removed old sysklogd configs, can be removed after 4.2-0
if [ "deinstall" = "$(dpkg --get-selections sysklogd 2>/dev/null | awk '{print $2}')" ]; then
	dpkg -P sysklogd >>"$UPDATER_LOG" 2>&1
	rm /etc/init.d/sysklogd* >>"$UPDATER_LOG" 2>&1
fi

# Bug 43639, remove old blas/lapack alternatives, can be removed after 4.2-0
if update-alternatives --quiet --list liblapack.so.3gf >/dev/null 2>&1; then
	update-alternatives --remove-all liblapack.so.3gf
fi
if update-alternatives --quiet --list libblas.so.3gf >/dev/null 2>&1; then
	update-alternatives --remove-all libblas.so.3gf
fi

check_qemu () {
	local f issues=false

	for f in /var/lib/libvirt/qemu/save/*.save
	do
		[ -f "$f" ] && break
	done
	if [ -f "$f" ]
	then
		echo "ERROR: Found QEMU virtual machines suspended to disk"
		echo "       There are known issues with restoring the runtime state of virtual machines."
		echo ""
		issues=true
	fi

	if pidof kvm qemu-system-i386 qemu-system-x86_64 >/dev/null
	then
		echo "ERROR: Found running QEMU virtual machines"
		echo "       Upgrading the host system while virtual machines are still running is not"
		echo "       recommended. They should be migrated to other hosts or shut down cleanly."
		echo ""
		issues=true
	fi

	if grep -q -s machine=\[\"\'\]pc-\[01\]\[.\] /etc/libvirt/qemu/*.xml
	then
		echo "ERROR: Found QEMU virtual machines using old machines"
		echo "       Virtual machines using old QEMU virtual machine configurations may experience"
		echo "       reboot problems and should be upgraded."
		echo ""
		issues=true
	fi

	if "$issues"
	then
		echo "      See <http://sdb.univention.de/solution_id_1384.html> for more information."
		echo "      This check can be disabled by setting the UCR variable 'update42/qemu' to 'yes'."
		if is_ucr_true update42/qemu
		then
			echo "WARNING: 'update42/qemu' is set, skipping as requested."
		else
			exit 1
		fi
	fi
	return 0
}
check_qemu

# ensure that en_US is included in list of available locales (Bug #44150)
available_locales="$(/usr/sbin/univention-config-registry get locale)"
case "$available_locales" in
	*en_US*) ;;
	*) /usr/sbin/univention-config-registry set locale="$available_locales en_US.UTF-8:UTF-8";;
esac


# autoremove before the update
if ! is_ucr_true update42/skip/autoremove; then
	DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >>"$UPDATER_LOG" 2>&1
fi

# Pre-upgrade
preups=""
$update_commands_update >&3 2>&3
for pkg in $preups; do
	if dpkg -l "$pkg" 2>&3 | grep ^ii  >&3 ; then
		echo -n "Starting pre-upgrade of $pkg: "
		if ! $update_commands_install "$pkg" >&3 2>&3
		then
			echo "failed."
			echo "ERROR: Failed to upgrade $pkg."
			exit 1
		fi
		echo "done."
	fi
done

python -c '
from univention.appcenter.app import AppManager
from univention.appcenter.ucr import ucr_save, ucr_get

for app in AppManager.get_all_locally_installed_apps():
	if app.docker:
		key = "appcenter/apps/%s/ucs" % app.id
		if not ucr_get(key):
			ucr_save({key: ucr_get("version/version")})
'
if [ $? != 0 ]; then
	echo "WARNING: Something went wrong while registering current Apps."
	echo "         This may lead to Apps not being recognized as installed"
	echo "         after the update."
fi

echo "** Starting: apt-get -s -o Debug::pkgProblemResolver=yes dist-upgrade" >&3 2>&3
apt-get -s -o Debug::pkgProblemResolver=yes dist-upgrade >&3 2>&3

fail_if_role_package_will_be_removed

# Bug #44346: Pin temporary sources list - can be removed after UCS-4-2-0
ln -n -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list /etc/apt/sources.list.d/00_ucs_update_in_progress.list 2>&3 || :

echo ""
echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
