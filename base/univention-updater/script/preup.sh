#!/bin/sh

echo "Running preup.sh script"

# check if user is logged in using ssh

if [ -n "$SSH_CLIENT" ]
    then
    echo "WARNING: You are logged in using SSH -- this may interrupt the update and result in an inconsistent system!"
    echo "         I will wait 10 seconds until starting the update. If you are not sure press Strg+C to quit."
    echo -n "         " 
    
    for i in `seq 1 10`
      do
      echo -n "."
      sleep 1
    done
    echo ""

fi
	

eval $(univention-baseconfig shell) >>/var/log/univention/updater.log 2>&1


check_space(){
	partition=$1
	size=$2
	usersize=$3
	if [ `df $partition|tail -n1 | awk '{print $4}'` -gt "$size" ]
		then 
		echo -e "Space on $partition:\t OK"
	else
		echo "ERROR:   Not enough space in $partition, need at least $usersize."
        echo "         This may interrupt the update and result in an inconsistent system!"
    	echo "         If neccessary you can skip this check by setting the value of the"
		echo "         baseconfig variable update20/checkfilesystems to \"no\"."
		echo "         But be aware that this is not recommended!"
		echo ""
		exit 1
	fi
}

# check space on filesystems
if [ "$update20_checkfilesystems" != "no" ]
then

	check_space "/var/cache/apt/archives" "1400000" "1.4 GB"
	check_space "/boot" "6000" "6 MB"
    check_space "/" "1400000" "1.4 GB"

else
    echo "WARNING: skipped disk-usage-test as you requested"
fi


if [ ! -e "/etc/univention/ssl/ucsCA" -a -d "/etc/univention/ssl/udsCA" ] ; then
	mv /etc/univention/ssl/udsCA /etc/univention/ssl/ucsCA
	ln -s ucsCA /etc/univention/ssl/udsCA
fi

dpkg -l freenx | grep ^ii >>/var/log/univention/updater.log 2>&1
if [ $? = 0 ]; then
	univention-baseconfig set update/2_0/freenx/reinstall?1 >>/var/log/univention/updater.log 2>&1
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes remove freenx  >>/var/log/univention/updater.log 2>&1 
fi

echo "univention-server-master hold" | dpkg --set-selections
echo "univention-server-backup hold" | dpkg --set-selections
echo "univention-server-slave hold" | dpkg --set-selections
echo "univention-server-member hold" | dpkg --set-selections
echo "univention-managed-client hold" | dpkg --set-selections
echo "univention-fat-client hold" | dpkg --set-selections
echo "univention-mobile-client hold" | dpkg --set-selections
echo "univention-pkgdb hold" | dpkg --set-selections
echo "univention-printquota hold" | dpkg --set-selections
echo "univention-application-server hold" | dpkg --set-selections

