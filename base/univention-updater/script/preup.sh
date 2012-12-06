#!/bin/bash
#
# Copyright (C) 2010-2012 Univention GmbH
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
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

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
echo " English version: http://download.univention.de/doc/release-notes-3.1_en.pdf"
echo " German version:  http://download.univention.de/doc/release-notes-3.1.pdf"
# echo "Changelog: http://download.univention.de/doc/changelog-2.4-2.pdf"
# echo "Please note that Univention Corporate Server (UCS) 3.0 is under development."
# echo "At the moment UCS 3.0 is not ready for production use!"
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
	if [ "$update31_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoressh\" to ignore it."
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update31_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoreterm\" to ignore it."
		exit 1
	fi
fi

if [ `uname -m` != "x86_64" ]; then
	if [ "$(dpkg-query -W -f='${Status}\n' univention-kernel-image-2.6.32 2>/dev/null)" = "install ok installed" ]; then
		paeavail=`grep "^flags" /proc/cpuinfo | grep pae`
		if [ -n "$paeavail" ]; then
			echo "You have the univention-kernel-image-2.6.32 installed, which is the meta package for systems"
			echo "without the Physical Adress Extension needed to support more than 4 GB of memory."
			echo "Starting with UCS 3.1 the standard kernel for 32 bit CPUs will always use PAE. To upgrade"
			echo "to this kernel you need to perform the following steps before starting the update:"
			echo
			echo "1. univention-install univention-kernel-image-2.6.32-64gb"
			echo "2. Reboot the system"
			echo "3. apt-get remove univention-kernel-image-2.6.32"
			exit 1
		fi
	fi
fi

# call custom preup script if configured
if [ ! -z "$update_custom_preup" ]; then
	if [ -f "$update_custom_preup" ]; then
		if [ -x "$update_custom_preup" ]; then
			echo "Running custom preupdate script $update_custom_preup"
			"$update_custom_preup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" >&3 2>&3
			echo "Custom preupdate script $update_custom_preup exited with exitcode: $?" >&3
		else
			echo "Custom preupdate script $update_custom_preup is not executable" >&3
		fi
	else
		echo "Custom preupdate script $update_custom_preup not found" >&3
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

## check for hold packages 
hold_packages=$(LC_ALL=C dpkg -l | grep ^h | awk '{print $2}')
if [ -n "$hold_packages" ]; then
	echo "WARNING: Some packages are marked as hold -- this may interrupt the update and result in an inconsistent"
	echo "system!"
	echo "Please check the following packages and unmark them or set the UCR variable update31/ignore_hold to yes"
	for hp in $hold_packages; do
		echo " - $hp"
	done
	if is_ucr_true update31/ignore_hold; then
		echo "WARNING: update31/ignore_hold is set to true. Skipped as requested."
	else
		exit 1
	fi
fi

##

#################### Bug #22093

get_latest_kernel_pkg () {
	# returns latest kernel package for given kernel version
	# currently running kernel is NOT included!

	kernel_version="$1"

	latest_dpkg=""
	latest_kver=""
	for kver in $(COLUMNS=200 dpkg -l linux-image-${kernel_version}-ucs\* 2>/dev/null | grep linux-image- | awk '{ print $2 }' | sort -n | grep -v "linux-image-$(uname -r)") ; do
		dpkgver="$(apt-cache show $kver | sed -nre 's/Version: //p')"
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

	ignore_kver="$(get_latest_kernel_pkg "$kernel_version")"
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes remove --purge $(COLUMNS=200 dpkg -l linux-image-${kernel_version}-ucs\* 2>/dev/null | grep linux-image- | awk '{ print $2 }' | sort -n | egrep -v "linux-image-$(uname -r)|$ignore_kver" | tr "\n" " ") >>/var/log/univention/updater.log 2>&1
}

if [ "$update31_pruneoldkernel" = "yes" ]; then
	echo "Purging old kernel..." | tee -a /var/log/univention/updater.log
	pruneOldKernel "2.6.18"
	pruneOldKernel "2.6.26"
	pruneOldKernel "2.6.32"
	echo "done" | tee -a /var/log/univention/updater.log
fi

#####################

check_space(){
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
		echo "         config registry variable update30/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		if [ "$partition" = "/boot" -a ! "$update31_pruneoldkernel" = "yes" ] ; then
			echo "         Old kernel versions on /boot can be pruned automatically during"
			echo "         next update attempt by setting config registry variable"
			echo "         update31/pruneoldkernel to \"yes\"."
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
if [ ! "$update31_checkfilesystems" = "no" ]
then

	check_space "/var/cache/apt/archives" "800000" "0,8 GB"
	check_space "/boot" "50000" "50 MB"
	check_space "/" "1300000" "1,3 GB"

else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo -n "Checking for package status: "
dpkg -l 2>&1 | LC_ALL=C grep "^[a-zA-Z][A-Z] " >&3 2>&3
if [ $? = 0 ]; then
	echo "failed"
	echo "ERROR: The package state on this system is inconsistent."
	echo "       Please run 'dpkg --configure -a' manually"
	exit 1
fi
echo "OK"

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
		echo "ERROR: The LDAP connection to $ldap_server_name with the machine account has"
		echo "       failed (invalid credentials)!"
		echo "       This MUST be fixed before the update can continue."
		echo
		echo "       This problem can be corrected by setting the content of the file"
		echo "       /etc/machine.secret as the password of the computer object using"
		echo "       Univention Management Console."
		exit 1
	fi
fi

# check for deprecated MySQL option skip-bdb in modified configuration files
MYSQL_CONF="/etc/mysql/my.cnf"
if test -f "$MYSQL_CONF" && ! conffile_is_unmodified "$MYSQL_CONF" && grep -q '\<skip-bdb\>' "$MYSQL_CONF"
then
	echo "ERROR: The MySQL configuration file /etc/mysql/my.cnf has been modified and"
	echo "       contains the deprecated option 'skip-bdb'. The option MUST be removed"
	echo "       before the update can continue."
	exit 1
fi

# BEGIN 3.1 update mark univention-legacy-kolab-schema as manually installed Bug #28900
if [ "$(dpkg-query -W -f='${Status}\n' univention-legacy-kolab-schema 2>/dev/null)" = "install ok installed" ]; then
	apt-get unmarkauto univention-legacy-kolab-schema
fi
# END 3.1 update mark univention-legacy-kolab-schema as manually installed Bug #28900

# Pre-update univention-config to ensure ucr is available during the upgrade:
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=29208
$update_commands_update >&3 2>&3
for pkg in univention-config; do
	if dpkg -l "$pkg" 2>&3 | grep ^ii  >&3 ; then
		echo -n "Starting pre-upgrade of $pkg: "
		$update_commands_install "$pkg" >&3 2>&3
		if [ ! $? = 0 ]; then
			echo "failed."
			echo "ERROR: Failed to upgrade $pkg."
			exit 1
		fi
		echo "done."
	fi
done

# Pre-download python-univention-directory-manager-legacy-ucd-tcs
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=29212
if dpkg -l "python-univention-directory-manager" 2>&3 | grep ^ii  >&3 ; then
	if ! apt-get install -d --yes python-univention-directory-manager-legacy-ucd-tcs >&3 2>&3; then	
		echo "ERROR: Failed to download the package "
		echo "       python-univention-directory-manager-legacy-ucd-tcs."
		echo "       Please check your network and repository settings."
		exit 1
	fi
fi

echo ""
echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
