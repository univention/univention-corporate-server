#!/bin/sh

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

check_and_install ()
{
	dpkg -l $1 | grep ^ii >>"$UPDATER_LOG" 2>&1
	if [ $? = 0 ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install $1 >>"$UPDATER_LOG" 2>&1
	fi
}

echo "Running postup.sh script"

# remove old cache file
rm -f /var/cache/univention-config/cache

eval $(univention-baseconfig shell) >>"$UPDATER_LOG" 2>&1

for p in univention-kolab2-webclient; do
	check_and_install $p
done

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-basesystem >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_master" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-master  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_backup" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-backup  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_slave" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-slave  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "memberserver" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-server-member  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "mobileclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-mobile-client  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-managed-client  >>"$UPDATER_LOG" 2>&1
fi

DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes dist-upgrade >>"$UPDATER_LOG" 2>&1

if [ -x /usr/sbin/update-initramfs ]; then
	update-initramfs -u -k all >>"$UPDATER_LOG" 2>&1
fi

# remove statoverride for UMC; required to ensure that UCM is not restarted during update
if [ -e /usr/sbin/univention-management-console-server ]; then
	dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
	chmod +x /usr/sbin/univention-management-console-server
fi
if [ -e /usr/sbin/apache2 ]; then
	dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
	chmod +x /usr/sbin/apache2
fi

univention-config-registry unset repository/local/old >>"$UPDATER_LOG" 2>&1

if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi

if [ ! -z "$update_custom_postup" ]; then
	echo -n "Running custom postupdate script"
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo "..."$update_custom_postup""
			if "$update_custom_postup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" | awk '{print "... "$0}' 2>&1; then
				echo "done."
			else
				echo "failed."
			fi
		else
			echo "..."$update_custom_postup"...not executable"
		fi
	else
		echo "..."$update_custom_postup"...not found"
	fi
fi

exit 0

