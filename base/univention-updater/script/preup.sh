#!/bin/bash
#
# Copyright (C) 2010-2014 Univention GmbH
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
echo " English version: http://docs.univention.de/release-notes-4.0-0-en.html"
echo " German version:  http://docs.univention.de/release-notes-4.0-0-de.html"
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
	if [ "$update40_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoressh\" to ignore it."
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update40_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoreterm\" to ignore it."
		exit 1
	fi
fi

# shell-univention-lib is proberly not installed, so use a local function
is_ucr_true () {
    local value
    value="$(/usr/sbin/univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
        1|yes|on|true|enable|enabled) return 0 ;;
        0|no|off|false|disable|disabled) return 1 ;;
        *) return 2 ;;
    esac
}

check_scalix_schema_present() {
	attributes=( scalixScalixObject scalixMailnode scalixAdministrator scalixMailboxAdministrator scalixServerLanguage scalixEmailAddress scalixLimitMailboxSize scalixLimitOutboundMail scalixLimitInboundMail scalixLimitNotifyUser scalixHideUserEntry scalixMailboxClass )

	objectclasses=( scalixUserClass scalixGroupClass )

	for oc in "${objectclasses[@]}"; do
		output=$(univention-ldapsearch -xLLL objectClass="$oc" dn "${attributes[@]}")
		if [ -n "$output" ]; then
			echo "ERROR: There are Scalix objectclasses present:"
			echo "$output"
			echo "ERROR: The remaining scalix attributes need to be removed before update"
			exit 1
		fi
	done

	for at in "${attributes[@]}"; do ## better safe than sorry..
		output=$(univention-ldapsearch -xLLL "$at=*" dn "${attributes[@]}")
		if [ -n "$output" ]; then
			echo "ERROR: There are Scalix attributes present:"
			echo "$output"
			echo "ERROR: The remaining scalix attributes need to be removed before update"
			exit 1
		fi
	done
}
check_scalix_schema_present

## Check for univention-horde4 (UCS version), univention-horde4 has been
## moved to the appcenter, block update here if UCS version of univention-horde4 
## is installed (should be updated to appcenter version)
if ! is_ucr_true update40/ignore_horde4; then
	horde4="$(dpkg-query -W -f '${Version}' univention-horde4 2>/dev/null)"
	if [ -n "$horde4" ] && dpkg --compare-versions "$horde4" lt "3.0.0" ; then
		echo "ERROR: An old version of univention-horde4 is installed."
		echo "       Please upgrade to the latest version of the horde app"
		echo "       in order to continue the update to UCS 4.0."
		echo "       The horde app can be installed/updated via the UMC AppCenter module."
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
	echo "Please check the following packages and unmark them or set the UCR variable update40/ignore_hold to yes"
	for hp in $hold_packages; do
		echo " - $hp"
	done
	if is_ucr_true update40/ignore_hold; then
		echo "WARNING: update40/ignore_hold is set to true. Skipped as requested."
	else
		exit 1
	fi
fi

## Check for UCS Xen-4.1 (Bug #35656)
check_for_xen () {
	local IFS='
'
	declare -a hosts=($(univention-ldapsearch -LLLo ldif-wrap=no univentionService='XEN Host' cn | sed -ne 's/^cn: //p')) # IFS
	if [ -z "$hosts" ]
	then
		case "$(dpkg-query -W -f '${Status}/${Version}' xen-4.1 2>/dev/null)" in
		install\ *\ */4.1.*-*.*.????????????) ;;
		*) return 0 ;;
		esac
	fi
	echo "WARNING: The Xen hypervisor is no longer supported by UCS."
	if [ -n "$hosts" ]
	then
		IFS=' '
		echo "         It seems to be used on the following host of this domain:"
		echo "           ${hosts[*]}"
		echo "         Updating UVMM to UCS-4 will remove the capability to manage "
		echo "         virtual machines on those hosts."
		echo ""
	fi
	echo "         The package 'xen-4.1' must be removed before the update can continue."
	if is_ucr_true update40/ignore_xen
	then
		echo "WARNING: update40/ignore_xen is set to true. Skipped as requested."
		return 0
	fi
	exit 1
}
check_for_xen

## Check for PostgreSQL-8.3 (Bug #36371)
check_for_postgresql83 () {
	case "$(dpkg-query -W -f '${Status}' postgresql-8.3 2>/dev/null)" in
	install*) ;;
	*) return 0 ;;
	esac
	echo "WARNING: PostgreSQL-8.3 is no longer supported by UCS-4 and must be migrated to"
	echo "         a newer version of PostgreSQL. See <http://sdb.univention.de/1249> for"
	echo "         more details."
	if is_ucr_true update40/ignore_postgresql83; then
		echo "WARNING: update40/ignore_postgresql83 is set to true. Skipped as requested."
	else
		exit 1
	fi
}
check_for_postgresql83

## Check for Cyrus-2.2 (Bug #36372)
check_for_cyrus22 () {
	case "$(dpkg-query -W -f '${Status}' cyrus-common-2.2 2>/dev/null)" in
	install*) ;;
	*) return 0 ;;
	esac
	echo "WARNING: Cyrus-2.2 is no longer supported by UCS-4 and must be migrated to a"
	echo "         newer version of Cyrus-IMAPd. See <http://sdb.univention.de/1213> for"
	echo "         more details."
	if is_ucr_true update40/ignore_cyrus22; then
		echo "WARNING: update40/ignore_cyrus22 is set to true. Skipped as requested."
	else
		exit 1
	fi
}
check_for_cyrus22

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

if [ "$update40_pruneoldkernel" = "yes" ]; then
	echo "Purging old kernel..." | tee -a /var/log/univention/updater.log
	pruneOldKernel "2.6.*"
	pruneOldKernel "3.2.0"
	pruneOldKernel "3.10.0"
	echo "done" | tee -a /var/log/univention/updater.log
fi

#####################

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
		echo "         If neccessary you can skip this check by setting the value of the"
		echo "         config registry variable update40/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		if [ "$partition" = "/boot" -a ! "$update40_pruneoldkernel" = "yes" ] ; then
			echo "         Old kernel versions on /boot can be pruned automatically during"
			echo "         next update attempt by setting config registry variable"
			echo "         update40/pruneoldkernel to \"yes\"."
		fi
		echo ""
		# kill the running univention-updater process
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
if [ "$update40_checkfilesystems" != "no" ]
then
	check_space "/var/cache/apt/archives" "200000" "200 MB"
	check_space "/boot" "50000" "50 MB"
	check_space "/" "500000" "500 MB"
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
	echo "       Please contact the support team"
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

# Update to UCS 4.0-0 remove pnm2ppa as this breaks univention-printserver Bug #36365
dpkg --purge pnm2ppa >>"$UPDATER_LOG" 2>&1
# End Update to UCS 4.0-0 remove pnm2ppa, can be removed after 4.0.0

# autoremove before the update
if ! is_ucr_true update40/skip/autoremove; then
    DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes autoremove >>"$UPDATER_LOG" 2>&1
fi

# Added python2.7 to the supported versions
egrep -q '^supported-versions.*python2.7' /usr/share/python/debian_defaults ||\
	sed -i 's|\(^supported-versions.*\)|\1, python2.7|' /usr/share/python/debian_defaults
# Pre-upgrade
preups="gcc-4.4 univention-ldap-config python-support python-univention univention-config univention-samba"
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

echo ""
echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
