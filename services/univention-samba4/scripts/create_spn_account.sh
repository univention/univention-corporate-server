#!/bin/bash
#
# Copyright 2012-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

. /usr/share/univention-lib/all.sh

scriptname=$(basename "$BASH_SOURCE")

error () {
	echo "ERROR: $*" >&2
	exit 1
}

create_spn_account () {

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
		-h | --help | -?:        print this usage message and exit program

		Description:
		$command_name creates a Samba account with a given servicePrincipalName
		e.g. $command_name --samaccountname "foo-\$hostname" \\
		                   --serviceprincipalname "FOO/\$hostname.\$domainname" \\
		                   --privatekeytab foo.keytab
		%EOR
	}

	credentials=()
	while [ $# -gt 0 ]
	do
		case "$1" in
			"--samaccountname"|"--sAMAccountName")
				samAccountName="${2:?missing argument for "$1"}"
				shift 2 || exit 2
				;;
			"--serviceprincipalname"|"--servicePrincipalName")
				servicePrincipalName="${2:?missing argument for "$1"}"
				shift 2 || exit 2
				;;
			"--privatekeytab"|"--privateKeytab")
				privateKeytab="${2:?missing argument for "$1"}"
				shift 2 || exit 2
				;;
			"--help"|"-h"|"-?")
				display_help
				exit 0
				;;
			"--bindpwdfile")
				bindpwdfile="${2:?missing argument for "$1"}"
				credentials+=("--bindpwdfile" "$bindpwdfile")
				shift 2 || exit 2
				;;
			"--binddn")
				binddn="${2:?missing argument for "$1"}"
				credentials+=("--binddn" "$binddn")
				shift 2 || exit 2
				;;
			*)
				display_help
				exit 1
				;;
		esac
	done

	test -z "$samAccountName" && error "Option --samaccountname required"
	test -z "$servicePrincipalName" && error "Option --serviceprincipalname required"
	test -z "$privateKeytab" && error "Option --privatekeytab required"

	password=$(create_machine_password)
	samba_private_dir="/var/lib/samba/private"
	keytab_path="$samba_private_dir/$privateKeytab"

	## check if user exists
	SPN_DN="$(udm users/user list "${credentials[@]}" --filter username="$samAccountName" | sed -n 's/^DN: //p')"
	if [ -n "$SPN_DN" ]; then
		## modify service account
		univention-directory-manager users/user modify "${credentials[@]}" \
			--set password="$password" \
			--set overridePWHistory=1 \
			--set overridePWLength=1 \
			--dn "$SPN_DN" || error "could not modify user account $samAccountName"
	else
		## create service_accountname via udm, but servicePrincipalName is missing
		univention-directory-manager users/user create "${credentials[@]}"  \
			--position "cn=users,$ldap_base" \
			--ignore_exists \
			--set username="$samAccountName" \
			--set lastname="Service" \
			--set objectFlag="hidden" \
			--set password="$password" || error "could not create user account $samAccountName"
	fi

	## wait for S4 Connector and possibly DRS until the service_accountname is available
	timeout=${create_spn_account_timeout:-1200}
	for i in $(seq 1 10 $timeout); do
		echo "looking for spn account \"$samAccountName\" in local samba"
		service_account_dn=$(ldbsearch -H $samba_private_dir/sam.ldb samAccountName="$samAccountName" dn | sed -n 's/^dn: \(.*\)/\1/p')
		[ -n "$service_account_dn" ] && break
		sleep 10
	done


	test -z "$service_account_dn" && error "$samAccountName account not found in local samba"

	## add servicePrincipalName to account
	ldbmodify -H "$samba_private_dir/sam.ldb" <<-%EOF
	dn: $service_account_dn
	changetype: modify
	replace: servicePrincipalName
	servicePrincipalName: $servicePrincipalName
	-
	%EOF

	key_version="$(ldbsearch -H "$samba_private_dir/sam.ldb" samAccountName="$samAccountName" msDS-KeyVersionNumber | sed -n 's/^msDS-KeyVersionNumber: //p')"
	test -z "$key_version" && key_version=1

	## create spn in secrets.ldb
	spn_secrets="$(ldbsearch -H "$samba_private_dir/secrets.ldb" sAMAccountName="$samAccountName" | sed -n 's/^dn: //p')"
	if [ -n "$spn_secrets" ]; then
		## update spn in secrets.ldb
		ldbmodify -H "$samba_private_dir/secrets.ldb" <<-%EOF
		dn: samAccountName=$samAccountName,CN=Principals
		changetype: modify
		replace: secret
		secret: $password
		-
		replace: msDS-KeyVersionNumber
		msDS-KeyVersionNumber: $key_version
		%EOF
	else
		## trigger Samba4 to create service keytab
		ldbadd -H "$samba_private_dir/secrets.ldb" <<-%EOF
		dn: samAccountName=$samAccountName,CN=Principals
		objectClass: kerberosSecret
		sAMAccountName: $samAccountName
		servicePrincipalName: $servicePrincipalName
		realm: $kerberos_realm
		secret: $password
		msDS-KeyVersionNumber: $key_version
		privateKeytab: $privateKeytab
		saltPrincipal: $samAccountName@$kerberos_realm
		name: $samAccountName
		%EOF
	fi

	sleep 3

	if ! [ -f "$keytab_path" ]; then
		echo "WARNING: samba did not create a keytab for samAccountName=$samAccountName"
		echo "WARNING: creating keytab manually"
		/usr/lib/univention-heimdal/univention-create-keytab --keytab="$keytab_path" \
			--principal="host/$samAccountName.$domainname" \
			--alias="$servicePrincipalName" \
			--alias="$samAccountName" \
			--kvno="$key_version" \
			--password="$password"
	fi

	samba-tool user setexpiry --noexpiry "$samAccountName"
}

if [ "$(basename $0)" = "$scriptname" ]; then
	eval "$(ucr shell hostname domainname kerberos/realm ldap/base)"
	create_spn_account "$@"
fi
