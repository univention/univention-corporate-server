#!/bin/bash
CONTROLMODE=true
. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

maildomain_name_randomname () { #Generates a random string as maildomain an echoes it. Usage: MAILDOMAINNAME=$(maildomain_name_randomname)
	random_string
}


create_mail_domain () { #Creates a mail/domain name like the first argument, supplied to the function.
	# creating a mail/domain name could be like:
	# MAILDOMAINNAME=$(maildomain_name_randomname)
	# create_mail_domain "$MAILDOMAINNAME"
	local domain="${1:?mail domain, e.g. \$(maildomain_name_randomname)}"
	shift
	udm-test mail/domain create \
		--position="cn=domain,cn=mail,$ldap_base" \
		--set name="$domain" \
		"$@"
	return $?
}

delete_mail_domain () { # Deletes a mail/domain name like the first argument, supplied to the function.
	# creating a mail/domain name could be like:
	# MAILDOMAINNAME=$(maildomain_name_randomname)
	# create_mail_domain "$MAILDOMAINNAME"
	local domain="${1:?mail domain, e.g. \$(maildomain_name_randomname)}"
	udm-test mail/domain remove --dn "cn=$domain,cn=domain,cn=mail,$ldap_base"
	return $?
}

# vim:set filetype=sh ts=4:
