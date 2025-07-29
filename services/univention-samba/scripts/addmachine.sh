#!/bin/bash
#
# Univention Samba
#  Script for adding a machine via UMC
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


name="$1"

if [ -z "$name" ] || [ "$name" = "-h" -o "$name" = "-?" -o "$name" = "-help" -o "$name" = "--help" ]; then
	echo "Usage: $0 <windows computer name>"
	exit 1
fi

eval "$(ucr shell ldap/master hostname)"

# Create the windows computer via UMC
/usr/sbin/umc-command -s "$ldap_master" -y /etc/machine.secret -U "$hostname$" selectiveudm/create_windows_computer -o name="$name" -o samba3_mode=True; rc=$?
if [ $rc != 0 ]; then
	echo "Failed to create $name. $rc"
	exit $?
fi

# Wait for the replication (maximal 60 seconds)
c=0
while [ $c -lt  60 ]; do
	dn=$(univention-ldapsearch "uid=${name/%$/}$" dn | sed -ne 's|dn: ||p')
	test -n "$dn" && break
done

# Invalidate the sssd passwd cache for that account
sss_cache --user="${name/%$/}$"

exit 0

