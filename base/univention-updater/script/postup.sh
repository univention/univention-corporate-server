#!/bin/sh

# remove old cache file

rm -f /var/cache/univention-config/cache

univention-baseconfig unset repository/patchlevel \
							repository/version


if [ -z "$system_role" ] || [ "$system_role" = "basesystem" ] || [ "$system_role" = "basissystem" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-basesystem  2>&1 >>/var/log/univention/updater.log
fi

reinstall=$(univention-baseconfig get update/2.0/freenx/reinstall)
if [ "$reinstall" = "1" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install freenx  2>&1 >>/var/log/univention/updater.log
	univention-baseconfig unset update/2.0/freenx/reinstall
fi

exit 0

