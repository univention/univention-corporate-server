#!/bin/sh

UPDATER_LOG="/var/log/univention/updater.log"
UPDATE_LAST_VERSION="$1"
UPDATE_NEXT_VERSION="$2"

check_and_install ()
{
	dpkg -l $1 2>>"$UPDATER_LOG" | grep ^ii >>"$UPDATER_LOG" 2>&1
	if [ $? = 0 ]; then
		DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install $1 >>"$UPDATER_LOG" 2>&1
	fi
}

echo -n "Running postup.sh script:"
echo >> "$UPDATER_LOG"
date >>"$UPDATER_LOG" 2>&1

# remove old cache file
rm -f /var/cache/univention-config/cache

eval $(univention-config-registry shell) >>"$UPDATER_LOG" 2>&1

for p in univention-client-kernel-image; do
	check_and_install $p
done

if [ -z "$server_role" ] || [ "$server_role" = "basesystem" ] || [ "$server_role" = "basissystem" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-basesystem >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_master" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-server-master  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_backup" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-server-backup  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "domaincontroller_slave" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-server-slave  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "memberserver" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-server-member  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "mobileclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-mobile-client  >>"$UPDATER_LOG" 2>&1
elif [ "$server_role" = "fatclient" ] || [ "$server_role" = "managedclient" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes install univention-managed-client  >>"$UPDATER_LOG" 2>&1
fi

DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -o DPkg::Options::=--force-overwrite -o DPkg::Options::=--force-overwrite-dir -y --force-yes dist-upgrade >>"$UPDATER_LOG" 2>&1

if [ -x /usr/sbin/update-initramfs ]; then
	update-initramfs -u -k all >>"$UPDATER_LOG" 2>&1
fi

# update the thin client chroot
if [ -x /usr/bin/univention-thin-client-apt ]; then
	DEBIAN_FRONTEND=noninteractive univention-thin-client-apt dist-upgrade  >>"$UPDATER_LOG" 2>&1
fi

# install locate if findutils has been installed in UCR 2.2-2 (Bug: #15992)
if dpkg -l findutils 2>> "$UPDATER_LOG" | grep ^ii >> "$UPDATER_LOG" ; then
	echo "findutils has been installed in UCS 2.2-2 ... installing locate" >> "$UPDATER_LOG"
	$update_commands_install locate >>"$UPDATER_LOG" 2>&1
	if [ ! $? = 0 ]; then
		echo "findutils has been installed in UCS 2.2-2 ... installing locate"
	    echo "WARNING: post-installation of 'locate' failed!"
	    echo "         Please run 'dpkg --configure -a' manually."
	fi
fi

# remove statoverride for UMC; required to ensure that UCM is not restarted during update
if [ -e /usr/sbin/univention-management-console-server ]; then
	dpkg-statoverride --remove /usr/sbin/univention-management-console-server >/dev/null 2>&1
	chmod +x /usr/sbin/univention-management-console-server 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
fi
if [ -e /usr/sbin/apache2 ]; then
	dpkg-statoverride --remove /usr/sbin/apache2 >/dev/null 2>&1
	chmod +x /usr/sbin/apache2 2>> "$UPDATER_LOG"  >> "$UPDATER_LOG"
fi

univention-config-registry unset repository/local/old >>"$UPDATER_LOG" 2>&1

if [ -e "/etc/apt/sources.list.d/00_ucs_temporary_installation.list" ]; then
	rm -f /etc/apt/sources.list.d/00_ucs_temporary_installation.list
fi
if [ -e "/etc/apt/sources.list.d/01_ucs_temporary_installation_unmaintained_repo.list" ]; then
	rm -f /etc/apt/sources.list.d/01_ucs_temporary_installation_unmaintained_repo.list
fi

# Enable usplash after update (Bug #16363)
if dpkg -l lilo 2>> "$UPDATER_LOG" >> "$UPDATER_LOG" ; then
	dpkg-divert --rename --divert /usr/share/initramfs-tools/bootsplash.debian --remove /usr/share/initramfs-tools/hooks/bootsplash 2>> "$UPDATER_LOG" >> "$UPDATER_LOG"
fi

# fix ldap-backup.secret permissions
if [ -e "/etc/ldap-backup.secret" ]; then
	chgrp "DC Backup Hosts" /etc/ldap-backup.secret 2>&1
fi

if [ ! -z "$update_custom_postup" ]; then
	if [ -f "$update_custom_postup" ]; then
		if [ -x "$update_custom_postup" ]; then
			echo -n "Running custom postupdate script $update_custom_postup"
			"$update_custom_postup" "$UPDATE_LAST_VERSION" "$UPDATE_NEXT_VERSION" >>"$UPDATER_LOG" 2>&1
			echo "Custom postupdate script $update_custom_postup exited with exitcode: $?" >>"$UPDATER_LOG" 2>&1
		else
			echo "Custom postupdate script $update_custom_postup is not executable" >>"$UPDATER_LOG" 2>&1
		fi
	else
		echo "Custom postupdate script $update_custom_postup not found" >>"$UPDATER_LOG" 2>&1
	fi
fi

# Bug 16371: remove temporary apt.conf template to activate force-overwrite
# only recommended for update to UCS 2.3-0
if [ -e "/etc/apt/apt.conf.d/02univentionupdate" ]; then
	rm -f /etc/apt/apt.conf.d/02univentionupdate
fi

echo "done."
date >>"$UPDATER_LOG" 2>&1

exit 0

