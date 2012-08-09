#!/bin/bash

## this script may be removed after update to ucs3.1 (Bug #21262)

### This script checks if the old default for min password length is
### still active in the Samba domain policy.
### If this is the case, it checks if there is a single UCS password
### policy referenced at the ldap/base and if it differs from the
### value in the Samba domain policy.
### If these strict criteria are met, the Samba min password length
### is set to the value of the UCS password policy.

eval "$(univention-config-registry shell)"

sambaMinPwdLength=$(univention-ldapsearch -xLLL \
	"(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" \
	sambaMinPwdLength | sed -n 's/^sambaMinPwdLength: \(.*\)$/\1/p')

if [ "$sambaMinPwdLength" = "5" ]; then
	## the samba domain policy still has the pre ucs3.1 default

	## check UDM password policies for the domain
	univentionPolicyPWHistory=$(univention-ldapsearch -xLLL \
					univentionPWLength=* dn \
					| sed -n 's/^dn: \(.*\)/\1/p')
	## count referenced UDM password policies
	referenced_policies=0
	unset univentionPWLength
	while read policy_dn; do
		referencing_objects=$(univention-ldapsearch -xLLL \
						univentionPolicyReference="$policy_dn" dn \
						| sed -n 's/^dn: \(.*\)/\1/p')
		referenced_policies=$(($referenced_policies+1))
		if [ "$referenced_policies" -gt 1 ]; then
			## more than one referenced policy, stop
			break
		fi

		while read referencing_dn; do
			if [ "$referencing_dn" = "$ldap_base" ]; then
				univentionPWLength=$(univention-ldapsearch -xLLL \
						-b "$policy_dn" -s base univentionPWLength \
						| sed -n 's/^univentionPWLength: \(.*\)/\1/p')
			fi
		done <<<"$referencing_objects"
		
	done <<<"$univentionPolicyPWHistory"

	if [ "$referenced_policies" = 1 ] && [ -n "$univentionPWLength" ]; then
		## OK, there is a single active UDM policy, it's connected to the ldap/base
		if [ "$univentionPWLength" != "$sambaMinPwdLength" ]; then
			## and the old samba default policy does not match, adjust it:
			pdbedit -P "min password length" -C "$univentionPWLength"
		fi
	fi
fi
