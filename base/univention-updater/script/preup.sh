#!/bin/sh
# NOTE: please add a note and a bug number to each code snippet!

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

echo "Running preup.sh script" >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

eval $(univention-config-registry shell) >>"$UPDATER_LOG" 2>&1

# Bug #16454: Workaround to remove source.list on failed upgrades
function cleanup() {
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

## # Bug #19081:
## # check if scope is active and available for 2.4-0
## # this test can be removed after 2.4-0
## updateCheck=$(mktemp)
## echo '
## #!/usr/bin/python2.4
## 
## from univention.updater import UniventionUpdater, UCS_Version
## from univention.updater.tools import LocalUpdater
## import univention.config_registry
## import sys
## 
## configRegistry = univention.config_registry.ConfigRegistry()
## configRegistry.load()
## yes = ["enabled", "true", "1", "yes", "enable"]
## scopes = ["ucd"]
## 
## for scope in scopes:
## 
## 	if configRegistry.get("repository/online/component/%s" % scope, "").lower() in yes and configRegistry.get("update/check/component/%s" % scope, "yes").lower() in yes:
## 
## 		available = []
## 		updater = UniventionUpdater()
## 		available += updater.get_component_repositories(scope, ["2.4"])
## 		updater = LocalUpdater()
## 		available += updater.get_component_repositories(scope, ["2.4"])
## 		if not available:
## 			print scope
## 			sys.exit(1)
## sys.exit(0)
## ' >> $updateCheck
## 
## doUpdateCheck=$(ucr get update/check/component)
## if [ -n "$doUpdateCheck" -a "$doUpdateCheck" = "no" ]; then
## 	continue
## else
## 	scope=$(python2.4 $updateCheck)
## 	if [ ! $? -eq 0 ]; then
## 		scope=$(echo $scope | sed 's|# The site.*was not found ||')
## 		echo "An update to UCS 2.4 without the component \"$scope\" is
## not possible because the component \"$scope\" is required."
## 		rm -f $updateCheck
## 		exit 1
## 	fi
## fi
## rm -f $updateCheck

## # check for running openoffice.org instances
## check_ooo() {
## 	PID=`pgrep soffice.bin | head -n 1`
## 	if [ -n "$PID" ]; then
## 		echo "OpenOffice.org running!"
## 		echo ""
## 		echo -n "OpenOffice.org is running right now with pid "
## 		echo -n "$PID."
## 		echo " This can cause problems"
## 		echo "with (de-)registration of components and extensions"
## 		echo "Thus the openoffice.org packages will fail to install"
## 		echo "You should close all running instances of OpenOffice.org (including"
## 		echo "any currently running Quickstarter) before starting with the update."
## 		exit 1
## 	fi
## }
## 
## if [ "$update24_ignoreooo" != "yes" ]; then
## 	check_ooo
## fi

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

check_space(){
	partition=$1
	size=$2
	usersize=$3
	if [ `df -P $partition|tail -n1 | awk '{print $4}'` -gt "$size" ]
		then
		echo -e "Space on $partition:\t OK"
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
if [ ! -d $initrd_backup ]; then
	mkdir $initrd_backup
fi
mv /boot/*.bak /var/backups/univention-initrd.bak/ &>/dev/null

# check space on filesystems
if [ ! "$update24_checkfilesystems" = "no" ]
then

	check_space "/var/cache/apt/archives" "1250000" "1,5 GB"
	check_space "/boot" "40000" "40 MB"
	check_space "/" "2500000" "1,5 GB"

else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo "Checking for the package status"
dpkg -l 2>&1 | grep "^[a-zA-Z][A-Z] " >>"$UPDATER_LOG" 2>&1
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
if dpkg -l lilo 2>> "$UPDATER_LOG" >> "$UPDATER_LOG" ; then
	dpkg-divert --rename --divert /usr/share/initramfs-tools/bootsplash.debian --add /usr/share/initramfs-tools/hooks/bootsplash 2>> "$UPDATER_LOG" >> "$UPDATER_LOG"
fi

# remove old packages that causes conflicts
olddebs="python2.4-dns alsa-headers"
for deb in $olddebs; do
	if dpkg -l $deb >>"$UPDATER_LOG" 2>&1; then
		dpkg -P $deb >>"$UPDATER_LOG" 2>&1
	fi
done

# Update package lists
apt-get update >>"$UPDATER_LOG" 2>&1
#
for pkg in univention-ssl univention-thin-client-basesystem univention-thin-client-x-base usplash ; do
	# pre-update $pkg to avoid pre-dependency-problems
	if dpkg -l $pkg 2>> "$UPDATER_LOG" | grep ^ii  >>"$UPDATER_LOG" ; then
	    echo -n "Starting preupdate of $pkg..."
	    $update_commands_install $pkg >>"$UPDATER_LOG" 2>> "$UPDATER_LOG"
	    if [ ! $? = 0 ]; then
			echo "failed."
	        echo "ERROR: pre-update of $pkg failed!"
	        echo "       Please run 'dpkg --configure -a' manually."
	        exit 1
	    fi
	    dpkg -l 2>&1  | grep "  " | grep -v "^|" | grep "^[a-z]*[A-Z]" >>"$UPDATER_LOG" 2>&1
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
date >> "$UPDATER_LOG"
trap - EXIT

exit 0
