#!/bin/sh

# remove old cache file

rm -f /var/cache/univention-config/cache

eval $( /usr/sbin/univention-baseconfig shell version/version version/patchlevel)

univention-baseconfig set version/version="$version_version" version/patchlevel="$version_patchlevel"

exit 0

