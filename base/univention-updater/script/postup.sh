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

for p in	univention-pkgdb \
			univention-printquota \
			univention-application-server \
			univention-bind \
			univention-bind-proxy \
			univention-kolab2 \
			univention-samba; do
	echo "$p install" | dpkg --set-selections
done

for p in	univention-application-server \
			univention-pkgdb \
			univention-pkgdb-tools \
			univention-samba \
			univention-bind \
			univention-bind-proxy \
			univention-kolab2; do
	check_and_install $p
done

dpkg -l univention-groupware-webclient | grep ^ii >>/var/log/univention/updater.log 2>&1
if [ $? = 0 ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-kolab2-webclient >>/var/log/univention/updater.log 2>&1 
fi


dpkg -l univention-admin | grep ^ii >>/var/log/univention/updater.log 2>&1
if [ $? = 0 ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-directory-manager >>/var/log/univention/updater.log 2>&1 
fi

for p in	univention-java \
			univention-client-kernel-image \
			univention-mozilla-firefox \
			kdebase \
			kdenetwork \
			jade; do
	check_and_install $p
done


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

update-initramfs -u >>/var/log/univention/updater.log 2>&1

#overwrite bootsplash init script with the new version
if [ -e "/etc/init.d/bootsplash.dpkg-dist" ]; then
	mv /etc/init.d/bootsplash.dpkg-dist /etc/init.d/bootsplash
fi

exit 0

