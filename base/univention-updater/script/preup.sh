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

echo ""

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

# Save current KDE package status. These packages might be removed
# during the UCS 3.0 update
if [ -z "$update30_kde_check" ]; then
	if [ "$(dpkg-query -W -f='${Status}\n' univention-kde 2>/dev/null)" = "install ok installed" ]; then
		univention-config-registry set update30/kde/univentionkde=true >&3
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' kdepim 2>/dev/null)" = "install ok installed" ]; then
		univention-config-registry set update30/kde/kdepim=true >&3
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' kdemultimedia 2>/dev/null)" = "install ok installed" ]; then
		univention-config-registry set update30/kde/kdemultimedia=true >&3
	fi
	univention-config-registry set update30/kde/check=true >&3
fi

# In some cases grub/boot might point to a device no longer present (e.g. if the system was installed
# in a virtual machine and migrated). To prevent grub-install from failing and rendering the system
# unbootable, bail out the update

grubbasedevice="$(univention-config-registry get grub/boot | sed 's/\/dev\///')"
if [ -n "$grubbasedevice" -a -e "/proc/partitions" ]; then
	awk '{print $4}' /proc/partitions | grep "${grubbasedevice}" 1> /dev/null

	if [ $? = 1 ]; then
		echo "The partition specified in the Univention Configuration Registry variable"
		echo "grub/boot could not be found in /proc/partitions, aborting update"
		exit 1
	fi
fi


# update to 3.0-0 Bug #22436
# check if kolab is installed ==> exit
if [ ! "$update_kolab_check" = "no" -a ! "$update_kolab_check" = "false" -a ! "$update_kolab_check" = "1" ] ; then
	ucs_kolab_is_installed=false
	if [ "$(dpkg-query -W -f='${Status}\n' univention-kolab2 2>/dev/null)" = "install ok installed" ]; then
		if dpkg --compare-versions "$(dpkg-query -W -f='${Version}\n' univention-kolab2)" lt "4" ; then
			ucs_kolab_is_installed=true
		fi
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' univention-mail-postfix-kolab2 2>/dev/null)" = "install ok installed" ]; then
		if dpkg --compare-versions "$(dpkg-query -W -f='${Version}\n' univention-mail-postfix-kolab2)" lt "5" ; then
			ucs_kolab_is_installed=true
		fi
	fi
	if [ "$(dpkg-query -W -f='${Status}\n' univention-mail-cyrus-kolab2 2>/dev/null)" = "install ok installed" ]; then
		if dpkg --compare-versions "$(dpkg-query -W -f='${Version}\n' univention-mail-cyrus-kolab2)" lt "4" ; then
			ucs_kolab_is_installed=true
		fi
	fi
	if [ "$ucs_kolab_is_installed" = "true" ] ; then
		echo "WARNING: kolab2 mail stack is installed!"
		echo
		echo "As of UCS 3.0 the Kolab groupware will be maintained by Kolab Systems."
		echo "Please visit http://kolabsys.com/ucs for update/migration instructions."
		echo "The update process will stop here."
		echo
		echo "This check can be disabled by setting the Univention Configuration Registry"
		echo "variable \"update/kolab/check\" to \"no\"."
		exit 1
	fi
fi

# update to 3.0-0 Bug #23191
if [ ! "$update_customatts_check" = "no" -a ! "$update_customatts_check" = "false" -a ! "$update_customatts_check" = "1" ]; then
	customatts=false
	ca=$(ldapsearch -x objectClass=univentionAdminProperty -LLL | grep ^cn: | awk -F "cn: " '{print $2}')
	if [ -n "$ca" ]; then
		customatts=true
	fi

	if "$customatts" = "true" ] ; then
		echo "WARNING: univention-directory-manager custom attributes found!"
		echo
		echo "$ca"
		echo
		echo "With UCS 3.0 the univention-directory-manager no longer supports"
		echo "custom attributes (settings/customattribute)."
		echo "The update process will stop here."
		echo
		echo "Please convert the custom attributes to their new counterparts"
		echo "extended attributes (extended_attribute). Additional information"
		echo "with migration instructions can be found in the UCS Wiki:"
		echo "  http://wiki.univention.de/index.php?title=Update_Customon_Attributes_to_Extended_Attributes/en"
		echo
		echo "This check can be disabled by setting the Univention Configuration Registry"
		echo "variable \"update/customatts/check\" to \"no\"."
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
		echo "http://sdb.univention.de/1210"
		echo ""
		echo "If the bootloader has been migrated and the packages \"lilo\" and"
		echo "\"univention-lilo\" are removed from the system, the upgrade can be restarted."
		echo ""
		echo "This check can be disabled by setting the Univention Configuration Registry"
		echo "variable \"update/lilo/check\" to \"no\"."
		exit 1
	fi
fi

# check if this is ucs 3.0 and set propper python version
version=$(dpkg-query -W -f '${Version}' univention-updater)
if dpkg --compare-versions "$version" lt "7.0"; then
	python_version="python2.4"
else
	python_version="python2.6"
fi


# Remove firmware packages, which require an interactive debconf EULA confirmation. Early kernel
# meta packages had a dependency, which has been removed in 2.4-4. Double-check anyway, since
# some installations might carry the package locally or from uninstalled UCS 2.3 packages
dpkg --purge firmware-ipw2x00 firmware-ivtv 2>/dev/null
if [ "$(dpkg-query -W -f='${Status}\n' firmware-ipw2x00 2>/dev/null)" = "hold ok installed" ]; then
	echo "firmware-ipw2x00 needs to be removed before the update"
	exit 1
fi

if [ "$(dpkg-query -W -f='${Status}\n' firmware-ivtv 2>/dev/null)" = "hold ok installed" ]; then
	echo "firmware-ivtv needs to be removed before the update"
	exit 1
fi


# BEGIN -- update to 3.0-0 Bug #22878
# first, test if univention-thin-client-basesystem is installed (UCS TCS or UCS with thin-client packages)
# second, activate tcs component (thin client services are now only available via component tcs)
# test if component is available (with univention.updater)
echo -n "Checking for thin client packages: "
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

		echo "found"
		if [ -s $updateError ]; then
			echo "WARNING: Traceback in UniventionUpdater() python module:"
			cat "$updateError"
		fi
		cat <<__HERE__
WARNING: The package univention-thin-client-basesystem is installed on
      this system. An update to UCS 3.0 without the component 'tcs' is
      not possible because the component 'tcs' is required to upgrade
      the installed thin client packages.
      If the thin client packages are not essential on this system, it
      is possible to remove these packages by running the following
      command:
           apt-get remove --purge univention-thin-client-basesystem
      Afterwards a new update test to UCS 3.0 can be started.

__HERE__
		exit 1
	else
		echo "done"
	fi
	rm "$updateError"
else
	echo "done"

fi
# END -- update to 3.0-0 Bug #22878

# BEGIN -- update to 3.0-0 Bug #23157
# Update Managed and Mobile client update without UCD 3.2 is not possible
role="$(univention-config-registry get server/role)"
if [ "$role" = "managed_client" ] || [ "$role" = "mobile_client" ] || [ "$role" = "fatclient" ]; then
	echo -n "Checking for Univention Corporate Desktop (UCD): "

	# save old values
	old_repository_online_component_ucd="$repository_online_component_ucd"
	old_repository_online_component_ucd_version="$repository_online_component_ucd_version"
	
	# activate component
	univention-config-registry set \
		repository/online/component/ucd=yes \
		repository/online/component/ucd/version=current >&3


	# check if component is available in ucs 3.0-0
	updateError=$(mktemp)
	scope=$($python_version -c '
from univention.updater import UniventionUpdater, UCS_Version
from univention.updater.tools import LocalUpdater
import univention.config_registry
import sys

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
scope = "ucd"
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

	# component ucd in 3.0 not found, -> abort the update
	if [ ! $res -eq 0 ]; then

		# reset old values
		if [ -n "$old_repository_online_component_ucd" ]; then
			univention-config-registry set repository/online/component/ucd="$old_repository_online_component_ucd" >&3
		else
			univention-config-registry unset repository/online/component/ucd >&3
		fi
		if [ -n "$old_repository_online_component_ucd_version" ]; then
			univention-config-registry set repository/online/component/ucd/version="$old_repository_online_component_ucd_version" >&3
		else
			univention-config-registry unset repository/online/component/ucd/version >&3
		fi

		if [ -s $updateError ]; then
			echo "WARNING: Traceback in UniventionUpdater() python module:"
			cat "$updateError"
		fi
		echo "failed"
		cat <<__HERE__
WARNING: An update to UCS 3.0 on a Managed or Mobile Client is only
      possible with the component 'ucd'. The 'ucd' component is
      currently not available for UCS 3.0.
__HERE__
		exit 1
	else
		echo "done"
	fi
fi


# END -- update to 3.0-0 Bug #23157

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

	check_space "/var/cache/apt/archives" "1800000" "1,8 GB"
	check_space "/boot" "50000" "50 MB"
	check_space "/" "2800000" "2,8 GB"

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

# only for update to UCS 3.0-0:
# ensure that /etc/univention/templates/files/etc/ldap/slapd.conf.d/10univention-ldap-server_schema
# is untouched by the user otherwise the update will fail (Bug #23483)
if [ "$server_role" = "domaincontroller_master" -o "$server_role" = "domaincontroller_backup" -o "$server_role" = "domaincontroller_slave" ] ; then
	for fn in "/etc/univention/templates/files/etc/ldap/slapd.conf.d/10univention-ldap-server_schema" ; do
	 	if ! conffile_is_unmodified "$fn" ; then
	 		echo "ERROR: the configuration file $fn"
	 		echo "       has been modified by user! Please reconstruct original file otherwise"
	 		echo "       the update will fail."
	 		exit 1
	 	fi
	done
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

echo -n "Starting pre-upgrade of python2.6: "
# BEGIN -- update to 3.0-0 Bug #23054
# 1. Install Python2.6-minimal before Python-minimal gets installed to workaround broken /usr/bin/python being used by python-support
$update_commands_install libssl0.9.8 python2.6-minimal python-central univention-config-wrapper >&3 2>&3
res=$?
if [ $res != 0 ]; then
	echo "failed."
	echo "ERROR: Failed to upgrade python2.6."
	exit $res
fi
echo "done."

# 2. Upgrade slapd before new libdb4.7 4.7.25-9.3.201105022022 gets installed, which used a different signature than old 4.7.25-6.7.201101311721
case "$(dpkg-query -W -f '${Status}' slapd)" in
install*)
	if dpkg --compare-versions "$(dpkg-query -W -f '${Version}' libdb4.7)" lt 4.7.25-9.3.201105022022
	then
		echo -n "Starting pre-upgrade of slapd: "
		$update_commands_install slapd db4.8-util libdb4.7=4.7.25-6\* >&3 2>&3
		res=$?
		if [ $res != 0 ]; then
			echo "failed."
			echo "ERROR: Failed to upgrade slapd."
			exit $res
		fi
		echo "done."
	fi
	;;
esac
# END -- update to 3.0-0 Bug #23054

for pkg in univention-ssl; do
	# pre-update $pkg to avoid pre-dependency-problems
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

## BEGIN Bug #24413
echo "Stopping gdm (will get restarted after update)"
[ -x /etc/init.d/gdm ] && /etc/init.d/gdm stop >&3 2>&3
ucr set gdm/autostart/update30backup="$(ucr get gdm/autostart)" >&3 2>&3
ucr set gdm/autostart=false >&3 2>&3
## END Bug #24413

## BEGIN Bug #23483
# add legacy objectclasses in preparation for update
if [ "$server_role" = "domaincontroller_master" ] ; then
	echo "Adding additional objectclasses to user template objects..."
	/usr/share/univention-legacy-kolab-schema/add-legacy-objectclasses --update >&3 2>&3
fi
## END Bug #23483

## BEGIN -- Python 2.4 environment Bug #24195
if [ ! -e /usr/lib/python2.4/site-packages/univention/__init__.py ]; then
	touch /usr/lib/python2.4/site-packages/univention/__init__.py
fi

for pymodule in config_registry.py config_registry_info.py baseconfig.py debhelper.py; do
	if [ ! -e /usr/lib/python2.4/site-packages/univention/${pymodule} ]; then
		ln -sf /usr/share/pyshared/univention/${pymodule} /usr/lib/python2.4/site-packages/univention/
	fi
done
## END -- Bug #24195

echo ""
echo "Starting update process, this may take a while."
echo "Check /var/log/univention/updater.log for more information."
date >&3
trap - EXIT

exit 0
