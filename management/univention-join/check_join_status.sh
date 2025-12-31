#!/bin/bash
#
# Univention Join
#  helper script: checks the join status of the local system
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

LOG_FILE=/var/log/univention/check_join_status.log

log_error () { # Log error message and exit
	local message="Error: $@"
	echo $message
	echo $message >>"$LOG_FILE"
	exit 1
}
log_warn () { # Log warning message
	local message="Warning: $@"
	echo $message
	echo $message >>"$LOG_FILE"
}

echo "Start $0 at $(date)" >>"$LOG_FILE"
eval "$(univention-config-registry shell)"

if [ ! -e /etc/machine.secret ]; then
	log_error "/etc/machine.secret not found"
fi

if ! ldapsearch -x -H "ldap://$ldap_master:$ldap_master_port" -D "$ldap_hostdn" -y /etc/machine.secret -b "$ldap_base" -s base >>"$LOG_FILE" 2>&1
then
	log_error "ldapsearch -x failed"
fi


if ! ldapsearch -x -ZZ -H "ldap://$ldap_master:$ldap_master_port" -D "$ldap_hostdn" -y /etc/machine.secret -b "$ldap_base" -s base >>"$LOG_FILE" 2>&1
then
	log_error "ldapsearch -x -ZZ failed"
fi

if [ ! -e /var/univention-join/joined ]
then
	log_error "The system isn't joined yet"
fi

if ! ldapsearch -x -ZZ -D "$ldap_hostdn" -y /etc/machine.secret -b "$ldap_base" -s base >>"$LOG_FILE" 2>&1
then
	log_error "localhost ldapsearch failed"
fi

LC_COLLATE="C"
declare -i MISSING=0
for i in /usr/lib/univention-install/*.{inst,uinst}
do
	test -e "$i" || continue
	unset VERSION
	eval "$(grep -h ^VERSION= "$i")"
	n="${i#/usr/lib/univention-install/}"
	n="${n#[0-9][0-9]}"
	n="${n%.uinst}"
	n="${n%.inst}"
	if ! grep -Fxq "$n v${VERSION} successful" /var/univention-join/status
	then
		log_warn "'$n' is not configured."
		MISSING+=1
	fi
done

if [ 0 -ne "$MISSING" ]
then
	log_error "Not all install files configured: $MISSING missing"
fi

echo "Joined successfully"
echo "Joined successfully" >>"$LOG_FILE"

exit 0
