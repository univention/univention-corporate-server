#!/bin/sh

# remove old cache file

rm -f /var/cache/univention-config/cache

univention-baseconfig unset repository/patchlevel \
							repository/version


if [ -z "$system_role" ] || [ "$system_role" = "basesystem" ] || [ "$system_role" = "basissystem" ]; then
	DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes install univention-basesystem  2>&1 >>/var/log/univention/updater.log
fi

exit 0

