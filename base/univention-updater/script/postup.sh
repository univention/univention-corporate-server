#!/bin/sh

# remove old cache file

rm -f /var/cache/univention-config/cache

eval $( /usr/sbin/univention-baseconfig shell version/version version/patchlevel)

univention-baseconfig set version/version="$version_version" version/patchlevel="$version_patchlevel"
#Die folgenden Zeilen können nach dem Update auf 2.0 wieder entfernt werden {------------------------------------------------------
univention-baseconfig unset repository/patchlevel
univention-baseconfig unset repository/version
#} --------------------------------------------------------------------------------------------------------------------------------
exit 0

