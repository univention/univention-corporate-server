#!/bin/bash
#
# Copyright (C) 2010-2011 Univention GmbH
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

UPDATER_LOG="/var/log/univention/updater.log"
exec 3>>"$UPDATER_LOG"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

echo "Running preup.sh script" >&3
date >&3

eval "$(univention-config-registry shell)" >&3 2>&3

cleanup () {
	# remove statoverride for UMC and apache in case of error during preup script
	if [ -e /usr/sbin/univention-management-console-server ]; then
		dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
		chmod +x /usr/sbin/univention-management-console-server 2>&3
	fi
	if [ -e /usr/sbin/apache2 ]; then
		dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
		chmod +x /usr/sbin/apache2 2>&3
	fi
}
trap cleanup EXIT

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
#echo "Please check the following documents carefully BEFORE updating to UCS ${UPDATE_NEXT_VERSION}:"
#echo "Release Notes: http://download.univention.de/doc/release-notes-2.4.pdf"
#echo "Changelog: http://download.univention.de/doc/changelog-2.4-2.pdf"
echo "Please note that Univention Corporate Server (UCS) 3.0 is under development."
echo "At the moment UCS 3.0 is not ready for production use!"
echo
#echo "Please also consider documents of following release updates and"
#echo "3rd party components."
#echo
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

# check if user is logged in using ssh
if [ -n "$SSH_CLIENT" ]; then
	if [ "$update30_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoressh\" to ignore it."
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update30_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or re-run with \"--ignoreterm\" to ignore it."
		exit 1
	fi
fi

# update to 3.0-0 Bug #23063
# check if lilo or univention-lilo is installed and exit
if [ ! "$update_lilo_check" = "no" -a ! "$update_lilo_check" = "false" -a ! "$update_lilo_check" = "1" ]; then
	lilo_is_installed=false
	if [ "$(dpkg-query -W -f='${Status}\n' lilo 2>/dev/null)" = "install ok installed" ]; then
		lilo_is_installed=true
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' univention-lilo 2>/dev/null)" = "install ok installed" ]; then
		lilo_is_installed=true
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' lilo 2>/dev/null)" = "hold ok installed" ]; then
		lilo_is_installed=true
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' univention-lilo 2>/dev/null)" = "hold ok installed" ]; then
		lilo_is_installed=true
	fi
	if [ "$lilo_is_installed" = "true" ]; then
		echo "WARNING: Bootloader lilo is installed!"
		echo ""
		echo "With UCS 3.0-0 the default bootloader is grub and all UCS installations with"
		echo "lilo as bootloader must be migrated to grub. Additional information about the"
		echo "installation and configuration of grub can be found in the Univention SDB:"
		echo "http://sdb.univention.de/1072"
		echo ""
		echo "If the bootloader has been migrated and the packages \"lilo\" and"
		echo "\"univention-lilo\" are removed from the system, the upgrade can be restarted."
		echo ""
		echo "This check can be disabled by setting the Univention Configuration Registry"
		echo "variable \"update/lilo/check\" to \"no\"."
		exit 1
	fi
fi

# BEGIN -- update to 3.0-0 Bug #22878
# first, test if univention-thin-client-basesystem is installed (UCS TCS or UCS with thin-client packages)
# second, activate tcs component (thin client services are now only available via component tcs)
# test if component is available (with univention.updater)
checkTcsComponent=$(univention-config-registry get update/check/component/tcs)
tcsInstalled=false
if [ -n "$checkTcsComponent" -a "$checkTcsComponent" = "no" ]; then
	tcsInstalled="ignore"
else
	if [ "$(dpkg-query -W -f='${Status}\n' univention-thin-client-basesystem 2>/dev/null)" = "install ok installed" ]; then
		tcsInstalled=true
	fi
fi
if [ "$tcsInstalled" = "true" ]; then

	# save old values
	old_repository_online_component_tcs="$repository_online_component_tcs"
	old_repository_online_component_tcs_version="$repository_online_component_tcs_version"
	
	# activate component
	univention-config-registry set \
		repository/online/component/tcs=yes \
		repository/online/component/tcs/version=current >&3

	# check if this is ucs 3.0 and set propper python version
	version=$(dpkg-query -W -f '${Version}' univention-updater)
	if dpkg --compare-versions "$version" lt "7.0"; then
		python_version="python2.4"
	else
		python_version="python2.6"
	fi

	# check if component is available in ucs 3.0-0
	updateError=$(mktemp)
	scope=$($python_version -c '
from univention.updater import UniventionUpdater, UCS_Version
from univention.updater.tools import LocalUpdater
import univention.config_registry
import sys

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
scope = "tcs"
version = "3.0"

if configRegistry.is_true("repository/online/component/%s" % scope, False):
	available = []
	updater = UniventionUpdater()
	available += updater.get_component_repositories(scope, [version])
	updater = LocalUpdater()
	available += updater.get_component_repositories(scope, [version])
	if not available:
		sys.exit(1)
sys.exit(0)
' 2>"$updateError")
	res=$?

	# component tcs in 3.0 not found, -> abort the update
	if [ ! $res -eq 0 ]; then

		# reset old values
		if [ -n "$old_repository_online_component_tcs" ]; then
			univention-config-registry set repository/online/component/tcs="$old_repository_online_component_tcs" >&3
		else
			univention-config-registry unset repository/online/component/tcs >&3
		fi
		if [ -n "$old_repository_online_component_tcs_version" ]; then
			univention-config-registry set repository/online/component/tcs/version="$old_repository_online_component_tcs_version" >&3
		else
			univention-config-registry unset repository/online/component/tcs/version >&3
		fi

		if [ -s $updateError ]; then
			echo "WARNING: Traceback in UniventionUpdater() python module:"
			cat "$updateError"
		fi
		echo "WARNING: An update to UCS 3.0 without the component 'tcs' is not possible"
		echo "     because the component 'tcs' is required. If the thin client packages"
        echo "     are not essential on this system, it is possible to remove these"
		echo "     packages by running the following command:"
		echo "        apt-get remove --purge univention-thin-client-basesystem"
		echo "     Afterwards a new update test to UCS 3.0 can be started."
		echo ""
		exit 1
	fi
	rm "$updateError"

fi
# END -- update to 3.0-0 Bug #22878


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

if [ "$update30_pruneoldkernel" = "yes" -o "$univention_ox_directory_integration_oxae" = "true" ]; then
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
	if [ `df -P "$partition" | tail -n1 | awk '{print $4}'` -gt "$size" ]
		then
		printf "Space on $partition:\t OK\n"
	else
		echo "ERROR:   Not enough space in $partition, need at least $usersize."
        echo "         This may interrupt the update and result in an inconsistent system!"
    	echo "         If neccessary you can skip this check by setting the value of the"
		echo "         config registry variable update30/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		if [ "$partition" = "/boot" -a ! "$update30_pruneoldkernel" = "yes" -a ! "$univention_ox_directory_integration_oxae" = "true" ] ; then
			echo "         Old kernel versions on /boot can be pruned automatically during"
			echo "         next update attempt by setting config registry variable"
			echo "         update30/pruneoldkernel to \"yes\"."
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
if [ ! "$update30_checkfilesystems" = "no" ]
then

	check_space "/var/cache/apt/archives" "700000" "0,7 GB"
	check_space "/boot" "50000" "50 MB"
	check_space "/" "1500000" "1,5 GB"

else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo "Checking for the package status"
dpkg -l 2>&1 | LC_ALL=C grep "^[a-zA-Z][A-Z] " >&3 2>&3
if [ $? = 0 ]; then
	echo "ERROR: The package state on this system is inconsistent."
	echo "       Please run 'dpkg --configure -a' manually"
	exit 1
fi

# ensure that UMC is not restarted during the update process
if [ -e /usr/sbin/univention-management-console-server ]; then
	dpkg-statoverride --add root root 0644 /usr/sbin/univention-management-console-server >/dev/null 2>&1
	chmod -x /usr/sbin/univention-management-console-server
fi

if [ -e /usr/sbin/apache2 ]; then
	dpkg-statoverride --add root root 0644 /usr/sbin/apache2 >/dev/null 2>&1
	chmod -x /usr/sbin/apache2
fi

# Disable usplash during update (Bug #16363)
if dpkg -l lilo >&3 2>&3 ; then
	dpkg-divert --rename --divert /usr/share/initramfs-tools/bootsplash.debian --add /usr/share/initramfs-tools/hooks/bootsplash >&3 2>&3
fi

# remove old packages that causes conflicts
olddebs="python2.4-dns alsa-headers"
for deb in $olddebs; do
	if dpkg -l "$deb" >&3 2>&3; then
		dpkg -P "$deb" >&3 2>&3
	fi
done

# Update package lists
apt-get update >&3 2>&3

# BEGIN -- update to 3.0-0 Bug #23054
# 1. Install Python2.6-minimal before Python-minimal gets installed to workaround broken /usr/bin/python being used by python-support
$update_commands_install libssl0.9.8 python2.6-minimal python-central univention-config-wrapper >&3 2>&3
# 2. Upgrade slapd before new libdb4.7 4.7.25-9.3.201105022022 gets installed, which used a different signature than old 4.7.25-6.7.201101311721
case "$(dpkg-query -W -f '${Status}' slapd)" in
install*)
	if dpkg --compare-versions "$(dpkg-query -W -f '${Version}' libdb4.7)" lt 4.7.25-9.3.201105022022
	then
		$update_commands_install slapd db4.8-util libdb4.7=4.7.25-6\* >&3 2>&3
	fi
	;;
esac
# END -- update to 3.0-0 Bug #23054

for pkg in univention-ssl univention-thin-client-basesystem univention-thin-client-x-base usplash ; do
	# pre-update $pkg to avoid pre-dependency-problems
	if dpkg -l "$pkg" 2>&3 | grep ^ii  >&3 ; then
	    echo -n "Starting preupdate of $pkg..."
	    $update_commands_install "$pkg" >&3 2>&3
	    if [ ! $? = 0 ]; then
			echo "failed."
	        echo "ERROR: pre-update of $pkg failed!"
	        echo "       Please run 'dpkg --configure -a' manually."
	        exit 1
	    fi
	    dpkg -l 2>&1 | grep "  " | grep -v "^|" | LC_ALL=C grep "^[a-z]*[A-Z]" >&3 2>&3
	    if [ $? = 0 ]; then
			echo "failed."
	        echo "ERROR: pre-update of $pkg failed!"
	        echo "       Inconsistent package state detected. Please run 'dpkg --configure -a' manually."
	        exit 1
	    fi
		echo "done."
	fi
done

echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
