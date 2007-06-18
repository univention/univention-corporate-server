#!/bin/sh

# remove old cache file

rm -f /var/cache/univention-config/cache

#Die folgenden Zeilen können nach dem Update auf 2.0 wieder entfernt werden {------------------------------------------------------

univention-baseconfig unset repository/patchlevel \
							repository/version

#} --------------------------------------------------------------------------------------------------------------------------------

exit 0

