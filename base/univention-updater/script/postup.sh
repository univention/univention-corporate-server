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

for p in	univention-server-master \
			univention-server-backup \
			univention-server-slave \
			univention-server-member \
			univention-managed-client \
			univention-fat-client \
			univention-mobile-client; do
	echo "$p install" | dpkg --set-selections
done

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


# this entry is only valid for update to UCS 2.1-2
if [ "$nscd_group_size" = "211" ] ; then
	echo "autoincreasing nscd/group/size from 211 to 3001..." >> /var/log/univention/updater.log 2>&1
	univention-config-registry set nscd/group/size=3001 >> /var/log/univention/updater.log 2>&1
	echo "done" >> /var/log/univention/updater.log 2>&1
fi


DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes dist-upgrade >>/var/log/univention/updater.log 2>&1

update-initramfs -u -k all>>/var/log/univention/updater.log 2>&1

exit 0

