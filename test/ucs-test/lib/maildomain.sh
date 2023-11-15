#!/bin/bash
# shellcheck shell=bash

# shellcheck disable=SC2034
CONTROLMODE=true

# shellcheck source=base.sh
. "$TESTLIBPATH/base.sh" || exit 137
# shellcheck source=random.sh
. "$TESTLIBPATH/random.sh" || exit 137

maildomain_name_randomname () { #Generates a random string as maildomain an echoes it. Usage: MAILDOMAINNAME=$(maildomain_name_randomname)
	random_string
}


create_mail_domain () { #Creates a mail/domain name like the first argument, supplied to the function.
	# creating a mail/domain name could be like:
	# MAILDOMAINNAME=$(maildomain_name_randomname)
	# create_mail_domain "$MAILDOMAINNAME"
	local domain="${1:?mail domain, e.g. \$(maildomain_name_randomname)}" rc=0
	shift
	if udm_out="$(udm-test mail/domain create \
		--position="cn=domain,cn=mail,$ldap_base" \
		--set name="$domain" \
		"$@" 2>&1)"
	then
		UDM1 <<<"$udm_out"
	else
		rc=$?
		echo "$udm_out" >&2
	fi
	return "$rc"
}

delete_mail_domain () { # Deletes a mail/domain name like the first argument, supplied to the function.
	# creating a mail/domain name could be like:
	# MAILDOMAINNAME=$(maildomain_name_randomname)
	# create_mail_domain "$MAILDOMAINNAME"
	local domain="${1:?mail domain, e.g. \$(maildomain_name_randomname)}"
	udm-test mail/domain remove --dn "cn=$domain,cn=domain,cn=mail,$ldap_base"
}

# vim:set filetype=sh ts=4:
