#!/bin/sh

check_and_install ()
{
	dpkg -l $1 | grep ^ii >>/var/log/univention/updater.log 2>&1
	if [ $? = 0 ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install $1 >>/var/log/univention/updater.log 2>&1 
	fi
}

echo "Running postup.sh script"

# remove old cache file
rm -f /var/cache/univention-config/cache

eval $(univention-baseconfig shell) >>/var/log/univention/updater.log 2>&1

if [ -n "$repository_patchlevel" ]; then
	univention-baseconfig unset repository/patchlevel >>/var/log/univention/updater.log 2>&1
fi

if [ -n "$repository_version" ]; then
	univention-baseconfig unset repository/version >>/var/log/univention/updater.log 2>&1
fi

echo "univention-server-master install" | dpkg --set-selections
echo "univention-server-backup install" | dpkg --set-selections
echo "univention-server-slave install" | dpkg --set-selections
echo "univention-server-member install" | dpkg --set-selections
echo "univention-managed-client install" | dpkg --set-selections
echo "univention-fat-client install" | dpkg --set-selections
echo "univention-mobile-client install" | dpkg --set-selections

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-basesystem >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "domaincontroller_master" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-master  >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "domaincontroller_backup" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-backup  >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "domaincontroller_slave" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-slave  >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "memberserver" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-member  >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "mobileclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-mobile-client  >>/var/log/univention/updater.log 2>&1 
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-managed-client  >>/var/log/univention/updater.log 2>&1 
fi

echo "univention-pkgdb install" | dpkg --set-selections
echo "univention-application-server install" | dpkg --set-selections

check_and_install univention-groupware-webclient
check_and_install univention-application-server
check_and_install univention-pkgdb
check_and_install univention-pkgdb-tools
check_and_install univention-admin
check_and_install univention-java
check_and_install univention-client-kernel-image
check_and_install univention-mozilla-firefox
check_and_install kdebase
check_and_install kdenetwork


dpkg -l univention-console | grep ^ii >>/var/log/univention/updater.log 2>&1
if [ $? = 0 ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-management-console >>/var/log/univention/updater.log 2>&1 
fi

DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes dist-upgrade >>/var/log/univention/updater.log 2>&1 


reinstall=$(univention-baseconfig get update/2_0/freenx/reinstall)
if [ "$reinstall" = "1" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install freenx >>/var/log/univention/updater.log 2>&1 
	univention-baseconfig unset update/2_0/freenx/reinstall >>/var/log/univention/updater.log 2>&1
fi

univention-baseconfig commit >>/var/log/univention/updater.log 2>&1

exit 0

