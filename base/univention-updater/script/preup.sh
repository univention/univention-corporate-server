#!/bin/sh
# NOTE: please add a note and a bug number to each code snippet!

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

echo "Running preup.sh script" >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval "$(univention-config-registry shell)" >>"$UPDATER_LOG" 2>&1

cleanup () {
	# remove statoverride for UMC and apache in case of error during preup script
	if [ -e /usr/sbin/univention-management-console-server ]; then
		dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
		chmod +x /usr/sbin/univention-management-console-server 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
	fi
	if [ -e /usr/sbin/apache2 ]; then
		dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
		chmod +x /usr/sbin/apache2 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
	fi
}
trap cleanup EXIT

###########################################################################
# RELEASE NOTES SECTION (Bug #19584)
# Please update URL to release notes and changelog on every release update
###########################################################################
echo
echo "HINT:"
echo "Please check the following documents carefully BEFORE updating to UCS ${UPDATE_NEXT_VERSION}:"
#echo "Release Notes: http://download.univention.de/doc/release-notes-2.4.pdf"
echo "Changelog: http://download.univention.de/doc/changelog-2.4-4.pdf"
echo
echo "Please also consider documents of following release updates and"
echo "3rd party components."
echo
if [ ! "$update_warning_releasenotes" = "no" -a ! "$update_warning_releasenotes" = "false" -a ! "$update_warning_releasenotes_internal" = "no" ] ; then
	echo "Update will wait here for 60 seconds..."
	echo "Press CTRL-c to abort or press ENTER to continue"
	# BUG: 'read -t' is a bash'ism, but she-bang is /bin/sh, not /bin/bash!
	read -t 60 somevar
fi

# check if user is logged in using ssh
if [ -n "$SSH_CLIENT" ]; then
	if [ "$update24_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or run univention-updater with \"--ignoressh\" to ignore it."
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update24_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or run univention-updater with \"--ignoreterm\" to ignore it."
		exit 1
	fi
fi

# call custom preup script if configured
if [ ! -z "$update_custom_preup" ]; then
	if [ -f "$update_custom_preup" ]; then
		if [ -x "$update_custom_preup" ]; then
			echo "Running custom preupdate script $update_custom_preup"
			"$update_custom_preup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" >>"$UPDATER_LOG" 2>&1
			echo "Custom preupdate script $update_custom_preup exited with exitcode: $?" >>"$UPDATER_LOG" 2>&1
		else
			echo "Custom preupdate script $update_custom_preup is not executable" >>"$UPDATER_LOG" 2>&1
		fi
	else
		echo "Custom preupdate script $update_custom_preup not found" >>"$UPDATER_LOG" 2>&1
	fi
fi

#################### Bug #22093

get_latest_kernel_pkg () {
	# returns latest kernel package for given kernel version
	# currently running kernel is NOT included!
	local kernel_version="$1"
	local latest_dpkg latest_kver kver dpkgver
	for kver in $(dpkg-query -f '${Package}\n' -W linux-image-${kernel_version}-ucs\* 2>/dev/null | grep -Fv "linux-image-$(uname -r)" | sort -n)
	do
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
	local kernel_version="$1"
	local ignore_kver

	ignore_kver="$(get_latest_kernel_pkg "$kernel_version")"
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes remove --purge $(dpkg-query -f '${Package}\n' -W linux-image-${kernel_version}-ucs\* 2>/dev/null | egrep -v "linux-image-$(uname -r)|$ignore_kver") >>/var/log/univention/updater.log 2>&1
}

if [ "$update24_pruneoldkernel" = "yes" -o "$univention_ox_directory_integration_oxae" = "true" ]; then
	echo "Purging old kernel..." | tee -a /var/log/univention/updater.log
	pruneOldKernel "2.6.18"
	pruneOldKernel "2.6.26"
	pruneOldKernel "2.6.32"
	echo "done" | tee -a /var/log/univention/updater.log
fi

#####################

check_space(){
	local partition=$1
	local size=$2
	local usersize=$3
	if [ "$(df -P "$partition" | tail -n1 | awk '{print $4}')" -gt "$size" ]
	then
		echo -e "Space on $partition:\t OK"
	else
		echo "ERROR:   Not enough space in $partition, need at least $usersize."
        echo "         This may interrupt the update and result in an inconsistent system!"
    	echo "         If neccessary you can skip this check by setting the value of the"
		echo "         config registry variable update24/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		if [ "$partition" = "/boot" -a ! "$update24_pruneoldkernel" = "yes" -a ! "$univention_ox_directory_integration_oxae" = "true" ] ; then
			echo "         Old kernel versions on /boot can be pruned automatically during"
			echo "         next update attempt by setting config registry variable"
			echo "         update24/pruneoldkernel to \"yes\"."
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
mv /boot/*.bak /var/backups/univention-initrd.bak/ &>/dev/null

# check space on filesystems
if [ ! "$update24_checkfilesystems" = "no" ]
then
	check_space "/var/cache/apt/archives" "150000" "150 MB"
	check_space "/boot" "50000" "50 MB"
	check_space "/" "350000" "350 MB"
else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo "Checking for the package status"
if LC_ALL=C COLUMNS=200 dpkg -l 2>&1 | LC_ALL=C grep "^[a-z][A-Z] " >>"$UPDATER_LOG" 2>&1
then
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
if LC_ALL=C dpkg -l lilo >>"$UPDATER_LOG" 2>&1
then
	dpkg-divert --rename --divert /usr/share/initramfs-tools/bootsplash.debian --add /usr/share/initramfs-tools/hooks/bootsplash >>"$UPDATER_LOG" 2>&1
fi

# remove old packages that causes conflicts
olddebs="python2.4-dns alsa-headers"
for deb in $olddebs
do
	if LC_ALL=C dpkg -l "$deb" >>"$UPDATER_LOG" 2>&1; then
		dpkg -P "$deb" >>"$UPDATER_LOG" 2>&1
	fi
done

# Update package lists
apt-get update >>"$UPDATER_LOG" 2>&1
#
for pkg in univention-ssl univention-thin-client-basesystem univention-thin-client-x-base usplash
do
	# pre-update $pkg to avoid pre-dependency-problems
	if LC_ALL=C dpkg -l "$pkg" 2>>"$UPDATER_LOG" | grep ^ii >>"$UPDATER_LOG"
	then
	    echo -n "Starting preupdate of $pkg..."
	    if ! $update_commands_install "$pkg" >>"$UPDATER_LOG" 2>&1
	    then
			echo "failed."
	        echo "ERROR: pre-update of $pkg failed!"
	        echo "       Please run 'dpkg --configure -a' manually."
	        exit 1
	    fi
	    if LC_ALL=C COLUMNS=200 dpkg -l 2>&1 | LC_ALL=C grep "^[a-z][A-Z]" >>"$UPDATER_LOG" 2>&1
	    then
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
date >> "$UPDATER_LOG"
trap - EXIT

exit 0
