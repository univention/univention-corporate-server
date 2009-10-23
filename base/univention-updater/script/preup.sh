#!/bin/sh

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

echo "Running preup.sh script"
date

eval $(univention-config-registry shell) >>"$UPDATER_LOG" 2>&1

# check if user is logged in using ssh
if [ -n "$SSH_CLIENT" ]; then
	if [ "$update23_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or set the Univention Configuration Registry variable \"update23/ignoressh\" to \"yes\" to ignore it."
		killall univention-updater
		exit 1
	fi
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update23_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or set the Univention Configuration Registry variable \"update23/ignoreterm\" to \"yes\" to ignore it."
		killall univention-updater
		exit 1
	fi
fi

if [ ! -z "$update_custom_preup" ]; then
	echo -n "Running custom preupdate script"
	if [ -f "$update_custom_preup" ]; then
		if [ -x "$update_custom_preup" ]; then
			echo " $update_custom_preup"
			"$update_custom_preup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" 2>&1
			echo "$update_custom_preup exited with exitcode: $?"
		else
			echo " $update_custom_preup is not executable"
		fi
	else
		echo " $update_custom_preup not found"
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
		echo "         baseconfig variable update23/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		echo ""
		# kill the running univention-updater process
		killall univention-updater
		exit 1
	fi
}

# check space on filesystems
if [ ! "$update23_checkfilesystems" = "no" ]
then

	check_space "/var/cache/apt/archives" "400000" "400 MB"
	check_space "/boot" "20000" "20 MB"
	check_space "/" "600000" "600 MB"

else
    echo "WARNING: skipped disk-usage-test as requested"
fi


echo "Checking for the package status" | tee -a "$UPDATER_LOG"
dpkg -l 2>&1  | grep "  " | grep -v "^|" | grep "^[a-z]*[A-Z]" >>"$UPDATER_LOG" 2>&1
if [ $? = 0 ]; then
	echo "ERROR: The package state on this system is inconsistent." | tee -a "$UPDATER_LOG"
	echo "       Please run 'dpkg --configure -a' manually" | tee -a "$UPDATER_LOG"
	killall univention-updater
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


# Update package lists
apt-get update >>"$UPDATER_LOG" 2>&1
#
for pkg in univention-ssl univention-thin-client-basesystem ; do
	# pre-update $pkg to avoid pre-dependency-problems
	if dpkg -l $pkg | grep ^ii  >>"$UPDATER_LOG" 2>&1 ; then
	    echo "Starting preupdate of $pkg... (may take some time)"
	    $update_commands_install $pkg >>"$UPDATER_LOG" 2>&1
	    if [ ! $? = 0 ]; then
	        echo "ERROR: pre-update of $pkg failed!" | tee -a "$UPDATER_LOG"
	        echo "       Please run 'dpkg --configure -a' manually." | tee -a "$UPDATER_LOG"
	        killall univention-updater
	        exit 1
	    fi
	    dpkg -l 2>&1  | grep "  " | grep -v "^|" | grep "^[a-z]*[A-Z]" >>"$UPDATER_LOG" 2>&1
	    if [ $? = 0 ]; then
	        echo "ERROR: pre-update of $pkg failed!" | tee -a "$UPDATER_LOG"
	        echo "       Inconsistent package state detected. Please run 'dpkg --configure -a' manually." | tee -a "$UPDATER_LOG"
	        killall univention-updater
	        exit 1
	    fi
	    echo "Preupdate of $pkg done."
	fi
done

echo "Finished running preup.sh script"
date

exit 0
