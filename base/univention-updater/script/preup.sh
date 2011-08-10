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

# Bug #16454: Workaround to remove source.list on failed upgrades
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

# Bug #21993: Check for suspend KVM instances
if [ yes != "$update24_ignorekvm" ] && which kvm >/dev/null && which virsh >/dev/null
then
	running= suspended= virtio=
	for vm in $(LC_ALL=C virsh -c qemu:///system list --all | sed -e '1,2d' -nre 's/^ *[-0-9]+ +(.+) (no state|running|idle|paused|in shutdown|shut off|crashed)$/\1/p')
	do
		if [ -S "/var/lib/libvirt/qemu/$vm.monitor" ]
		then
			running="${running:+$running }'$vm'"
		elif [ -s "/var/lib/libvirt/qemu/save/$vm.save" ]
		then
			suspended="${suspended:+$suspended }'$vm'"
		fi
		if grep -q "<target.* bus='virtio'.*/>\|<model.* type='virtio'.*/>" "/etc/libvirt/qemu/$vm.xml"
		then
			virtio="${virtio:+$virtio }'$vm'"
		fi
	done
	if [ -n "$running" ] || [ -n "$suspended" ] || [ -n "$virtio" ]
	then
		echo "\
WARNING: Qemu-kvm will be updated to version 0.14, which is incompatible with
previous versions. Virtual machines running Windows and using VirtIO must be
updated to use at least version 1.1.16 of the VirtIO driver for Windows.

All virtual machines should be turned off before updating. Please use UVMM or
virsh to turn off all running and suspended virtual machines.

This check can be disabled by setting the Univention Configuration Registry
variable \"update24/ignorekvm\" to \"yes\"."
		if [ -n "$virtio" ]
		then
			echo "VMs using virtio: $virtio" | fmt
		fi
		if [ -n "$running" ]
		then
			echo "Running VMs: $running" | fmt
		fi
		if [ -n "$suspended" ]
		then
			echo "Suspended VMs: $suspended" | fmt
		fi
	fi
	if [ -n "$running" ] || [ -n "$suspended" ]
	then
		exit 1
	fi
fi

###########################################################################
# RELEASE NOTES SECTION (Bug #19584)
# Please update URL to release notes and changelog on every release update
###########################################################################
echo
echo "HINT:"
echo "Please check the following documents carefully BEFORE updating to UCS ${UPDATE_NEXT_VERSION}:"
#echo "Release Notes: http://download.univention.de/doc/release-notes-2.4.pdf"
echo "Changelog: http://download.univention.de/doc/changelog-2.4-2.pdf"
echo
echo "Please also consider documents of following release updates and"
echo "3rd party components."
echo
if [ ! "$update_warning_releasenotes" = "no" -a ! "$update_warning_releasenotes" = "false" -a ! "$update_warning_releasenotes_internal" = "no" ] ; then
	echo "Update will wait here for 60 seconds..."
	echo "Press CTRL-c to abort or press ENTER to continue"
	# BUG: 'read -t' is the only bash'ism in this file, therefore she-bang has to be /bin/bash not /bin/sh!
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
	if [ "$lilo_is_installed" = "true" ]; then
		echo "WARNING: Bootloader lilo (packages lilo and/or univention-lilo) is installed!"
		echo "Update to UCS 3.0-0 with bootloader lilo is not supported. Please upgrade your bootloader"
		echo "to grub (package: univention-grub) before the update."
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
	continue
else
	if [ "$(dpkg-query -W -f='${Status}\n' univention-thin-client-basesystem 2>/dev/null)" = "install ok installed" ]; then
		tcsInstalled=true
	fi
fi
if [ "$tcsInstalled" = "true" ]; then
	# activate component
	univention-config-registry set \
		repository/online/component/tcs=yes \
		repository/online/component/tcs/version=current

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
yes = ["enabled", "true", "1", "yes", "enable"]
scope = "tcs"
version = "3.0"

if configRegistry.get("repository/online/component/%s" % scope, "").lower() in yes:
	available = []
	updater = UniventionUpdater()
	available += updater.get_component_repositories(scope, [version])
	updater = LocalUpdater()
	available += updater.get_component_repositories(scope, [version])
	if not available:
		sys.exit(1)
sys.exit(0)
' 2>"$updateError")
	
	# component tcs in 3.0 not found, -> abort the update
	if [ ! $? -eq 0 ]; then
		if [ -s $updateError ]; then
			echo "WARNING: Traceback in UniventionUpdater() python module:"
			cat "$updateError"
		fi
		echo "WARNING: An update to UCS 3.0 without the component 'tcs' is"
		echo "         not possible because the component 'tcs' is required."
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
		echo "         baseconfig variable update24/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
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
if [ ! "$update24_checkfilesystems" = "no" ]
then

	check_space "/var/cache/apt/archives" "700000" "0,7 GB"
	check_space "/boot" "55000" "55 MB"
	check_space "/" "1500000" "1,5 GB"

else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo "Checking for the package status"
dpkg -l 2>&1 | grep "^[a-zA-Z][A-Z] " >&3 2>&3
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
olddebs="python2.4-dns alsa-headers nagios2 nagios2-common nagios2-doc"
for deb in $olddebs; do
	if dpkg -l "$deb" >&3 2>&3; then
		dpkg -P "$deb" >&3 2>&3
	fi
done

# Update package lists
apt-get update >&3 2>&3

# BEGIN -- update to 3.0-0 Bug #23054
# 1. Install Python2.6-minimal before Python-minimal gets installed to workaround broken /usr/bin/python being used by python-support
$update_commands_install libssl0.9.8 python2.6-minimal python-central >&3 2>&3
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
	    dpkg -l 2>&1 | grep "  " | grep -v "^|" | grep "^[a-z]*[A-Z]" >&3 2>&3
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
