#!/bin/bash
#
# Copyright 2012-2013 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

. /usr/share/univention-lib/all.sh

scriptname=$(basename "$BASH_SOURCE")

create_spn_account() {

	command_name=$(basename $0)
	if [ "$command_name" != "$scriptname" ]; then
		command_name="${FUNCNAME[0]}"
	fi

	display_help() {
		cat <<-%EOR
		Syntax:
		$command_name [options]

		Options:
		--samaccountname <account>:		Account name
		--serviceprincipalname <spn>:	servicePrincipalName
		--privatekeytab <filename>:		privateKeytab
		-type <type>:            type of computer, e.g. "client"
		-ldapbase <ldap base>:   LDAP Base DN, e.g. dc=test,dc=local
		-realm <kerberos realm>: Kerberos realm, e.g. TEST.LOCAL
		-disableVersionCheck     Disable version check against _dcname_

		-h | --help | -?:        print this usage message and exit program
		--version:               print version information and exit program

		Description:
		$command_name creates a Samba account with a given servicePrincipalName
		e.g. $command_name --samaccountname "foo-\$hostname" \\
		                   --serviceprincipalname "FOO/\$hostname.\$domainname" \\
		                   --privatekeytab foo.keytab

		%EOR
	}

	while [ $# -gt 0 ]
	do
		case "$1" in
			"--samaccountname"|"--sAMAccountName")
				spn_account_name="${2:?missing argument for samaccountname}"
				shift 2 || exit 2
				;;
			"--serviceprincipalname"|"--servicePrincipalName")
				servicePrincipalName="${2:?missing argument for servicePrincipalName}"
				shift 2 || exit 2
				;;
			"--privatekeytab"|"--privateKeytab")
				privateKeytab="${2:?missing argument for privateKeytab}"
				shift 2 || exit 2
				;;
			"--help"|"-h"|"-?")
				display_help
				exit 0
				;;
			*)
				display_help
				exit 1
				;;
		esac
	done

	if [ -z "$spn_account_name" ]; then
		echo "Error: Option --samaccountname required"
		display_help
		exit 1
	fi
	if [ -z "$servicePrincipalName" ]; then
		echo "Error: Option --serviceprincipalname required"
		display_help
		exit 1
	fi
	if [ -z "$privateKeytab" ]; then
		echo "Error: Option --privatekeytab required"
		display_help
		exit 1
	fi

	spn_account_name_password=$(create_machine_password)

	spn_secrets_ldif=$(ldbsearch -H /var/lib/samba/private/secrets.ldb "(servicePrincipalName=$servicePrincipalName)" \
			| ldapsearch-wrapper | ldapsearch-decode64)
	previous_spn_secrets_password=$(sed -n 's/^secret: //p' <<<"$spn_secrets_ldif")

	spn_account_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb "(servicePrincipalName=$servicePrincipalName)" dn \
			| ldapsearch-wrapper | sed -n 's/^dn: //p')

	if [ -n "$spn_account_dn" ] && [ -n "$previous_spn_secrets_password" ]; then
		test_output=$(ldbsearch -k no -H ldap://$(hostname -f) -U"$spn_account_name" \
			--password="$previous_spn_secrets_password" -b "$spn_account_dn" -s base dn 2>/dev/null \
			| sed -n 's/^dn: //p')
		if [ -n "$test_output" ]; then
			## SPN account password ok, don't touch a running system.
			return
		fi
	fi

	if [ -z "$spn_account_dn" ]; then

		samba-tool user add "$spn_account_name" "$spn_account_name_password" || return $?

		samba-tool user setexpiry --noexpiry "$spn_account_name"

		ldbmodify -H /var/lib/samba/private/sam.ldb <<-%EOF
		dn: CN=$spn_account_name,CN=Users,$samba4_ldap_base
		changetype: modify
		replace: servicePrincipalName
		servicePrincipalName: $servicePrincipalName
		%EOF
	else
		echo -n "Setting new password for $spn_account_name account: "
		local password_set
		for i in 0 1 2 3 4 5 6 7 8 9; do
			if samba-tool user setpassword "$spn_account_name" --newpassword="$spn_account_name_password"; then
				password_set=1
				break
			elif [ "$i" -lt 9 ]; then
				## sometimes the random password does not meet the passwort complexity requirements..
				echo -n "Trying again with new password: "
				spn_account_name_password=$(create_machine_password)
			fi
		done
		if [ -z "$password_set" ]; then
			echo "Error: Failed to set password for $spn_account_name_password"
			exit 1
		fi

		samba-tool user setexpiry --noexpiry "$spn_account_name"
	fi

	# get msDS-KeyVersionNumber
	msdsKeyVersion=$(ldbsearch -H /var/lib/samba/private/sam.ldb  samAccountName="$spn_account_name" msDS-KeyVersionNumber \
					| sed -n 's/^msDS-KeyVersionNumber: \(.*\)/\1/p')
	if [ -z "$msdsKeyVersion" ]; then
		echo "ERROR: Could not determine msDS-KeyVersionNumber of $spn_account_name account!"
		exit 1
	fi
	
	spn_secrets_dn=$(sed -n 's/^dn: //p' <<<"$spn_secrets_ldif")
	if [ -z "$spn_secrets_dn" ]; then
		ldbadd -H /var/lib/samba/private/secrets.ldb <<-%EOF
		dn: samAccountName=$spn_account_name,CN=Principals
		objectClass: kerberosSecret
		privateKeytab: $privateKeytab
		realm: $kerberos_realm
		sAMAccountName: $spn_account_name
		secret: $spn_account_name_password
		servicePrincipalName: $servicePrincipalName
		name: $spn_account_name
		msDS-KeyVersionNumber: $msdsKeyVersion
		saltPrincipal: $spn_account_name@$kerberos_realm
		%EOF
	else
		echo -n "Saving password for $spn_account_name account: "
		ldbmodify -H /var/lib/samba/private/secrets.ldb <<-%EOF
		dn: $spn_secrets_dn
		changetype: modify
		replace: secret
		secret: $spn_account_name_password
		-
		replace: msDS-KeyVersionNumber
		msDS-KeyVersionNumber: $msdsKeyVersion
		%EOF
	fi
}

if [ "$(basename $0)" = "$scriptname" ]; then
	eval "$(ucr shell hostname domainname kerberos/realm samba4/ldap/base)"
	create_spn_account "$@"
fi
