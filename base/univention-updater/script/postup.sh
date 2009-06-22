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

for p in univention-kolab2-webclient; do
	check_and_install $p
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

DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes dist-upgrade >>/var/log/univention/updater.log 2>&1

if [ -x /usr/sbin/update-initramfs ]; then
	update-initramfs -u -k all >>/var/log/univention/updater.log 2>&1
fi

# remove statoverride for UMC; required to ensure that UCM is not restarted during update
if [-e /usr/sbin/univention-management-console-server ]; then
	dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
	chmod +x /usr/sbin/univention-management-console-server
fi
if [ -e /usr/sbin/apache2 ]; then
	dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
	chmod +x /usr/sbin/apache2
fi

univention-config-registry unset repository/local/old >>/var/log/univention/updater.log 2>&1

if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

exit 0

