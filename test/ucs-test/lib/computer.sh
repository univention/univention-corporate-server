#!/bin/bash
. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

computer_randomname () { # Generate a name for a Computer. E.g. COMPUTERNAME=$(computer_randomname)
	random_hostname
}

computer_create () { # Creates a computer. E.g. computer_create "$COMPUTERNAME"
	local COMPUTERNAME=${1?:missing parameter: computer name}
	local role=${2:-windows}
	shift
	shift
	log_and_execute udm-test "computers/$role" create \
		--position "cn=computers,$ldap_base" \
		--set name="$COMPUTERNAME" \
		"$@"
}

computer_dn () { #echos the DN of a Computer. E.g. computer_dn $GROUPNAME
	local name="$1"
	local role=${2:-windows}
	udm-test "computers/$role" list --filter cn="$name" | sed -ne 's/^DN: //p'
}

computer_remove () { # Removes a computer. E.g. computer_remove "$COMPUTERNAME"
	local COMPUTERNAME=${1?:missing parameter: name}
	local role=${2:-windows}
	log_and_execute udm-test "computers/$role" remove --dn "cn=$COMPUTERNAME,cn=computers,$ldap_base"
}

# vim:set filetype=sh ts=4:
