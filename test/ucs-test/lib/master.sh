#!/bin/bash
# Run commands on ldap/master
eval "$(ucr shell ldap/master '^tests/domainadmin/.*')"
MASTER_SSH_TIMEOUT=20

on_master () { # Execute command on ldap/master through shell
	univention-ssh --no-split \
		-timeout "$MASTER_SSH_TIMEOUT" \
		"$tests_domainadmin_pwdfile" "root@${ldap_master}" \
		"$@"
}
on_master_escaped () { # Execute command on ldap/master
	local arg= args=()
	for arg in "$@"
	do
		args+=("$(printf "%q" "$arg")")
	done
	on_master "${args[@]}"
}

master_reachable_via_ssh () { # Checks if the Master could be reachable via port 22 (ssh)
	# usage: master_reachable_via_ssh
	# return values:
	#	1 = yes
	#	0 = no
	local key="${HOSTNAME}_${0}_${$}_${RANDOM}"
	on_master_escaped echo "$key" | grep -Fq "$key"
}

master_ucr_set () { # set a ucr variable on the master system
	# usage: master_ucr_set "ldap/acl/user/password" "yes"
	# return value:
	#	0 = ok
	#	>0 = error
	local variable="${1?:missing variable name}"
	local value="${2?:missing variable value}"
	on_master_escaped univention-config-registry set "${variable}=${value}" >/dev/null
}

master_ucr_get () { # returns the value of a ucr variable on the master system
	# usage: VALUE="$(master_ucr_get ldap/acl/user/password)"
	# return text:
	#	the value of the ucr variable
	local variable="${1?:missing variable name}"
	on_master_escaped univention-config-registry get "$variable"
}

master_ldap_secret () { # returns the LDAP Password for cn=admin,$ldap_base from the ldap/master Server
	# usage: ldap_pasword="$(master_ldap_secret)"
	# return text:
	#	the ldap cleartext password
	on_master_escaped cat /etc/ldap.secret
}

master_restart_service () { # restarts a service
	# usage: master_restart_service "slapd"
	# return value:
	#	0 = ok
	#	>0 = error
	local service="${1?:missing service name}"
	on_master_escaped invoke-rc.d "$service" restart >/dev/null 2>&1
}

master_udm_version () { # gets the version of the UDM on the master system
	# usage: version="$(master_udm_version)"
	# return text:
	#	Version string of the UDM package
	on_master_escaped dpkg-query -W -f '${Version}' univention-directory-manager-tools
}

master_udm_installed () { # checks if UDM is installed on the master
	# usage: ret=$(master_udm_installed) # return values are 0=no and 1=yes
	# return values:
	#	0 = no UDM is installed
	#	1 = UDM is installed
	[ -n "$(master_udm_version)" ] && :
}

# vim:set filetype=sh ts=4:
