#!/bin/bash
# univention Join
# helper script: checks the join status of the local system

log_error () { # Log error message and exit
	local message="Error: $@"
	echo $message
}

check_join_status () {

    echo "Start $0 at $(date)"
    eval "$(univention-config-registry shell)"

    if [ ! -e /etc/machine.secret ]; then
		log_error "/etc/machine.secret not found"
		return 1
    fi

	if ! ldapsearch -x -h "$ldap_master" -p "$ldap_master_port" -D "$ldap_hostdn" -w "$(</etc/machine.secret)" -b "$ldap_base" -s base
	then
		log_error "ldapsearch -x failed"
		return 1
	fi


	if ! ldapsearch -x -ZZ -h "$ldap_master" -p "$ldap_master_port" -D "$ldap_hostdn" -w "$(</etc/machine.secret)" -b "$ldap_base" -s base
	then
		log_error "ldapsearch -x -ZZ failed"
		return 1
	fi

	if [ ! -e /var/univention-join/joined ]
	then
		log_error "The system isn't joined yet"
		return 1
	fi

	if ! ldapsearch -x -ZZ -D "$ldap_hostdn" -w "$(</etc/machine.secret)" -b "$ldap_base" -s base
	then
		log_error "localhost ldapsearch failed"
		return 1
	fi
	return 0
}


