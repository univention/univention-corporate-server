#!/bin/sh

echo "Running preup.sh script"



eval $(univention-baseconfig shell) >>/var/log/univention/updater.log 2>&1

# check if user is logged in using ssh
if [ -n "$SSH_CLIENT" ]; then
	if [ "$update20_ignoressh" != "yes" ]; then
		echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or set the baseconfig variable update21/ignoressh to yes to ignore it."
		killall univention-updater
		exit 1
	fi
    
fi

if [ "$TERM" = "xterm" ]; then
	if [ "$update21_ignoreterm" != "yes" ]; then
		echo "WARNING: You are logged in under X11 -- this may interrupt the update and result in an inconsistent system!"
		echo "Please log in under the console or set the baseconfig variable update21/ignoreterm to yes to ignore it."
		killall univention-updater
		exit 1
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
		echo "         baseconfig variable update21/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		echo ""
		# kill the running univention-updater process
		killall univention-updater
		exit 1
	fi
}

# check space on filesystems
if [ "$update21_checkfilesystems" != "no" ]
then

	check_space "/var/cache/apt/archives" "600000" "600 MB"
	check_space "/boot" "6000" "6 MB"
    check_space "/" "900000" "900 MB"

else
    echo "WARNING: skipped disk-usage-test as you requested"
fi


echo "Checking for unconfigured packages"
DEBIAN_FRONTEND=noninteractive dpkg --configure -a >>/var/log/univention/updater.log 2>&1

if [ $? != 0 ]; then
	echo "Failed to configure the unconfigured packages. Please run 'dpkg --configure -a' manually"
	# kill the running univention-updater process
	killall univention-updater
	exit 1
fi

