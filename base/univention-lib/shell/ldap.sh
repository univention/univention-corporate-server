# Univention Common Shell Library
#
# Copyright 2011-2013 Univention GmbH
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


#
# ucs_getAttrOfDN returns the attribute value of an LDAP object
# ucs_getAttrOfDN <attributename> <DN> [<ldapsearch-credentials>]
# e.g. ucs_getAttrOfDN "krb5PasswordEnd" "uid=testuser,cn=users,dc=test,dc=system"
# ==> 20110622112559Z
#
ucs_getAttrOfDN() { # <attr> <dn> [<ldapsearch-credentials>]
	local attr="$1"
	local base="$2"
	if ! shift 2
	then
		echo "ucs_getAttrOfDN: wrong number of arguments" >&2
		return 2
	fi
	if [ -n "$attr" ]; then
		univention-ldapsearch -x "$@" -s base -b "$base" -LLL "$attr" \
			| ldapsearch-wrapper | ldapsearch-decode64 | sed -ne "s/^$attr: //p"
	fi
}

#
# ucs_convertUID2DN returns DN of user object for specified UID
# ucs_convertUID2DN <uid> [<ldapsearch-credentials>]
# e.g. ucs_convertUID2DN "testuser"
#
ucs_convertUID2DN() { # <uid> [<ldapsearch-credentials>]
	local uid="$1"
	if ! shift 1
	then
		echo "ucs_convertUID2DN: wrong number of arguments" >&2
		return 2
	fi
	if [ -n "$uid" ]; then
		univention-ldapsearch -x "$@" -LLL "(&(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=univentionMail)(objectClass=sambaSamAccount)(objectClass=simpleSecurityObject)(&(objectClass=person)(objectClass=organizationalPerson)(objectClass=inetOrgPerson)))(!(uidNumber=0))(!(uid=*\$))(uid=$uid))" dn | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne 's/dn: //p'
	fi
}

#
# ucs_convertDN2UID returns UID of user object for specified DN
# ucs_convertDN2UID <user dn> [<ldapsearch-credentials>]
# e.g. ucs_convertDN2UID "uid=testuser,cn=users,dc=test,dc=system"
#
ucs_convertDN2UID() { # <userdn> [<ldapsearch-credentials>]
	local userdn="$1"
	if ! shift 1
	then
		echo "ucs_convertDN2UID: wrong number of arguments" >&2
		return 2
	fi
	ucs_getAttrOfDN "uid" "$userdn" "$@"
}

#
# ucs_getGroupMembersDirect returns all members of specified group
# ucs_getGroupMembersDirect <group dn> [<ldapsearch-credentials>]
# e.g. ucs_getGroupMembersDirect "cn=Domain Admins,cn=groups,dc=test,dc=system"
#
ucs_getGroupMembersDirect() { # <groupDN> [<ldapsearch-credentials>]
	local groupdn="$1"
	if ! shift 1
	then
		echo "ucs_getGroupMembersDirect: wrong number of arguments" >&2
		return 2
	fi
	ucs_getAttrOfDN "uniqueMember" "$groupdn" "$@"
}

#
# ucs_getGroupMembersDirect returns all members of specified group and of all nested groups
# ucs_getGroupMembersDirect <group dn> [<ldapsearch-credentials>]
# e.g. ucs_getGroupMembersDirect "cn=Domain Admins,cn=groups,dc=test,dc=system"
#
# optional environment: ldap_binddn and ldap_bindpw
#
ucs_getGroupMembersRecursive(){ # <groupDN> [<ldapsearch-credentials>]
	local reply
	local ldif
	local groupdn="$1"
	if ! shift 1
	then
		echo "ucs_getGroupMembersRecursive: wrong number of arguments" >&2
		return 2
	fi
	ucs_getGroupMembersDirect "$groupdn" "$@" | while read reply
	do
		ldif=$(univention-ldapsearch -x "$@" -LLL -b "$reply" '(!(objectClass=univentionGroup))' dn | sed -ne "s/^dn: //p")
		if [ "$?" != 0 ]; then	## don't recurse in case of error
			break
		fi
		if [ -z "$ldif" ]
		then
			ucs_getGroupMembersRecursive "$reply" "$@"
		else
			echo "$reply"
		fi
	done | sort -u
}

#
# ucs_addServiceToLocalhost adds a new service entry to local UDM host object. This can be easily used
# in join scripts to add a new service (like "nagios-server") after installation of corresponding service 
# package (luke "univention-nagios-server"). Additional arguments like UDM credentials will be passed 
# through.
# ucs_addServiceToLocalhost <servicename> [<udm-credentials>]
# e.g. ucs_addServiceToLocalhost "nagios-server" "$@"
#
ucs_addServiceToLocalhost () { # <servicename> [<udm-credentials>]
	local server_role ldap_base ldap_hostdn
	local servicename="$1"
	eval "$(ucr shell server/role ldap/base ldap/hostdn)"
	shift
	ucs_addServiceToHost "$servicename" "$server_role" "$ldap_hostdn" "$@"
}

#
# ucs_addServiceToLocalhost adds a new service entry to specified UDM host object. This can be easily used
# in e.g. join scripts to add a new service. Additional arguments like UDM credentials will be passed 
# through.
# ucs_addServiceToHost <servicename> <udm-module-name> <dn> [<udm-credentials>]
# e.g. ucs_addServiceToHost "nagios-server" "domaincontroller_slave" "cn=myslave,cn=dc,cn=computers,dc=test,dc=system" "$@"
#
ucs_addServiceToHost () { # <servicename> <udm-module-name> <dn> [options]
	local servicename="$1"
	local modulename="$2"
	local hostdn="$3"
	local ldap_base="$(ucr get ldap/base)"
	if ! shift 3
	then
		echo "ucs_addServiceToHost: wrong argument number" >&2
		return 2
	fi
	univention-directory-manager container/cn create "$@" --ignore_exists --set name="services" --position "cn=univention,$ldap_base"
	univention-directory-manager settings/service create "$@" --ignore_exists --set name="$servicename" --position "cn=services,cn=univention,$ldap_base"
	univention-directory-manager "computers/$modulename" modify "$@" --dn "$hostdn" --append service="$servicename"
}

#
# ucs_removeServiceFromLocalhost removes a service entry from local UDM host object. This can be easily used
# in join scripts to remove a service (like "nagios-server") after removing of corresponding service 
# package (luke "univention-nagios-server"). Additional arguments like UDM credentials will be passed 
# through.
# ucs_removeServiceFromLocalhost <servicename> [<udm-credentials>]
# e.g. ucs_removeServiceFromLocalhost "nagios-server" "$@"
#
ucs_removeServiceFromLocalhost () { # <servicename> [<udm-credentials>]
	local server_role ldap_base ldap_hostdn
	local servicename="$1"
	eval "$(ucr shell server/role ldap/base ldap/hostdn)"
	shift
	ucs_removeServiceFromHost "$servicename" "$server_role" "$ldap_hostdn" "$@"
}

#
# ucs_removeServiceFromHosz removes a service entry from specified UDM host object. This can be easily used
# in e.g. join scripts to remove a service. Additional arguments like UDM credentials will be passed 
# through.
# ucs_removeServiceFromHost <servicename> <udm-module-name> <dn> [<udm-credentials>]
# e.g. ucs_removeServiceFromHost "nagios-server" "domaincontroller_slave" "cn=myslave,cn=dc,cn=computers,dc=test,dc=system" "$@"
#
ucs_removeServiceFromHost () { # <servicename> <udm-module-name> <dn> [options]
	local servicename="$1"
	local modulename="$2"
	local hostdn="$3"
	local ldap_base="$(ucr get ldap/base)"
	if ! shift 3
	then
		echo "ucs_removeServiceFromHost: wrong argument number" >&2
		return 2
	fi
	univention-directory-manager "computers/$modulename" modify "$@" --dn "$hostdn" --remove service="$servicename"
	if ucs_isServiceUnused "$servicename" "$@" ; then
		univention-directory-manager settings/service remove "$@" --ignore_exists --dn "cn=$servicename,cn=services,cn=univention,$ldap_base"
	fi
}

#
# ucs_isServiceUnused cechks whether a service entry is used.
# ucs_isServiceUnused <servicename> [<udm-credentials>]
# e.g.  if ucs_isServiceUnused "DNS" "$@"; then uninstall DNS; fi
#
ucs_isServiceUnused () {
	local servicename="$1"

	if ! shift 1
	then
		echo "ucs_lastHostWithService: wrong argument number" >&2
		return 2
	fi
	
	# create a tempfile to get the real return code of the ldapsearch command,
	# otherwise we get only the code of the sed command
	local tempfile=$(mktemp)
	univention-ldapsearch univentionService="${servicename}" cn >"$tempfile"
	if [ $? != 0 ]; then
		rm -f "$tempfile"
		echo "ucs_isServiceUnused: search failed" >&2
		return 2
	fi

	count=$(grep -c "^cn: " "$tempfile")
	if [ $? = 0 ] && [ $count -gt 0 ]; then
		ret=1
	else
		ret=0
	fi
	
	rm -f "$tempfile"

	return $ret
}

#
# ucs_registerLDAPSchema writes an LDAP schema extension to UDM.
# A listener module then writes it to a persistent place /var/lib/univention-ldap/local-schema/.
#
# ucs_registerLDAPSchema <schema file> [options]
# e.g. ucs_registerLDAPSchema /usr/share/univention-fetchmail-schema/univention-fetchmail.schema
#
ucs_registerLDAPSchema () {
	local SH_FUNCNAME
	SH_FUNCNAME=ucs_registerLDAPSchema

	display_help() {
		printf "usage: $SH_FUNCNAME [<options>] <schema file>\n"
		printf "internal options:\n"
		printf "\t--binddn <binddn>\n"
		printf "\t--bindpwd <bindpwd>\n"
		printf "\t--bindpwdfile <bindpwdfile>\n"
	}

	## Parse arguments
	local schemaFile
	schemaFile="$1"

	if ! shift 1
	then
		echo "ERROR: $SH_FUNCNAME: wrong number of arguments" >&2
		display_help
		return 2
	fi

	## Validate arguments
	if [ ! -e "$schemaFile" ]; then
		echo "ERROR: $SH_FUNCNAME: given schema file does not exist" >&2
		return 2
	fi

	local package_name package_version calling_script_name calling_script_basename
	calling_script_name=$(basename -- "$0")
	calling_script_basename=$(basename -- "$calling_script_name" .postinst)
	if [ "$calling_script_basename" != "$calling_script_name" ]; then
		package_name="$calling_script_basename"
	elif [ -n "$JS_SCRIPT_FULLNAME" ]; then
		package_name=$(dpkg -S "$JS_SCRIPT_FULLNAME" | cut -d: -f1)
	fi

	if [ -n "$package_name" ]; then
		package_version=$(dpkg-query -f '${Version}' -W "$package_name")
	else
		eval "$(ucr shell '^tests/ucs_registerLDAP/.*')"
		if [ -n "$tests_ucs_registerLDAP_packagename" ] && [ -n "$tests_ucs_registerLDAP_packageversion" ]; then
			package_name="$tests_ucs_registerLDAP_packagename"
			package_version="$tests_ucs_registerLDAP_packageversion"
		else
			echo "ERROR: $SH_FUNCNAME: Unable to determine Debian package name"
			echo "ERROR: This function only works in joinscript or postinst context"
			return 1
		fi
	fi

	local filename objectname target_container_name ldap_base target_container_dn
	filename=$(basename -- "$schemaFile")
	objectname=$(basename -- "$filename" ".schema")
	ldap_base="$(ucr get ldap/base)"
	target_container_name="ldapschema"
	target_container_dn="cn=$target_container_name,cn=univention,$ldap_base"

	univention-directory-manager container/cn create "$@" --ignore_exists \
		--set name="$target_container_name" \
		--position "cn=univention,$ldap_base"

	local ldif
	ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionSchema)(cn=$objectname))" \
			univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion | ldapsearch-wrapper)
	if [ -z "$ldif" ]; then

		output=$(univention-directory-manager settings/ldapschema create "$@" \
			--set name="$objectname" \
			--set filename="$filename" \
			--set schema="$(gzip -c "$schemaFile" | base64 -w0)" \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--position "$target_container_dn" 2>&1)
		echo "$output"

		if [ $? -eq 0 ]; then
			object_dn=$(echo "$output" | sed -n 's/^Object created: //p')

			if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
				univention-directory-manager settings/ldapschema modify "$@" \
					--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
					--dn "$object_dn"
			fi

		else	## check again, might be a race

			ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionSchema)(cn=$objectname))" \
					univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion | ldapsearch-wrapper)

			if [ -z "$ldif" ]; then
				echo "ERROR: $SH_FUNCNAME: Failed to create settings/ldapschema object." >&2
				return 2
			fi
		fi
	fi

	if [ -n "$ldif" ]; then	## object exists already, modify it

		local registered_package registered_package_version
		registered_package=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackage: //p')
		registered_package_version=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackageVersion: //p')

		if [ "$registered_package" = "$package_name" ]; then
			if ! dpkg --compare-versions "$package_version" gt "$registered_package_version"; then
				echo "ERROR: $SH_FUNCNAME: registered package version $registered_package_version is newer, skipping registration." >&2
				return 2
			fi
		else
			echo "WARNING: $SH_FUNCNAME: schema $objectname was registered by package $registered_package version $registered_package_version, changing ownership." >&2
		fi

		local object_dn
		object_dn=$(echo "$ldif" | sed -n 's/^dn: //p')

		output=$(univention-directory-manager settings/ldapschema modify "$@" \
			--set schema="$(gzip -c "$schemaFile" | base64 -w0)" \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--dn "$object_dn" 2>&1)
		echo "$output"

		if [ $? -ne 0 ]; then
			echo "ERROR: $SH_FUNCNAME: Modification of settings/ldapschema object failed." >&2
			return 2
		else
			if echo "$output" | grep -q "^No modification: $object_dn$"; then
				return 0
			fi
		fi
			

		if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
			univention-directory-manager settings/ldapschema modify "$@" \
				--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
				--dn "$object_dn"
		fi

	fi

	timeout=180	#seconds
	echo -n "Waiting up to $timeout seconds for activation of the LDAP schema extension: "
	local t t0
	t0=$(date +%s)
	while ! univention-directory-manager settings/ldapschema list "$@" \
			--filter "(&(name=$objectname)(active=TRUE))" | grep -q '^DN: '
	do
			t=$(date +%s)
			if [ $(($t - $t0)) -gt "$timeout" ]; then
				echo
				echo "ERROR: $SH_FUNCNAME: Master did not mark the LDAP schema extension active within 3 minutes."
				return 1
			fi
			echo -n "."
			sleep 3
	done
	echo "OK"
}

# ucs_unregisterLDAPSchema removes an LDAP schema extension from UDM.
# A listener module then tries to remove it.
#
# ucs_unregisterLDAPSchema <schema file> [options]
# e.g. ucs_unregisterLDAPSchema /usr/share/univention-fetchmail-schema/univention-fetchmail.schema
#
ucs_unregisterLDAPSchema () {
	local SH_FUNCNAME
	SH_FUNCNAME=ucs_unregisterLDAPSchema

	display_help() {
		printf "usage: $SH_FUNCNAME [<options>] <schema file>\n"
		printf "internal options:\n"
		printf "\t--binddn <binddn>\n"
		printf "\t--bindpwd <bindpwd>\n"
		printf "\t--bindpwdfile <bindpwdfile>\n"
	}

	## Parse arguments
	local schemaFile
	schemaFile="$1"

	if ! shift 1
	then
		echo "ERROR: $SH_FUNCNAME: wrong number of arguments" >&2
		display_help
		return 2
	fi

	## Validate arguments
	if [ ! -e "$schemaFile" ]; then
		echo "ERROR: $SH_FUNCNAME: given schema file does not exist" >&2
		return 2
	fi

	local objectname
	objectname=$(basename "$schemaFile" ".schema")

	local schema_ldif
	schema_ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionSchema)(cn=$objectname))" \
			univentionAppIdentifier | ldapsearch-wrapper)

	if [ -z "$schema_ldif" ]; then
		echo "ERROR: $SH_FUNCNAME: Schema object not found in LDAP."
		return 1
	fi

	app_filter=""
	local appidentifier
	for appidentifier in $(echo "$schema_ldif" | sed -n 's/^univentionAppIdentifier: //p'); do
		app_filter="$app_filter(cn=$appidentifier)"
	done

	if [ -n "$app_filter"]; then
		local app_ldif
		app_ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionApp)$app_filter)" cn | ldapsearch-wrapper)
		if [ -n "$app_ldif" ]; then
			echo -n "INFO: $SH_FUNCNAME: The schema $objectname is still registered by the following apps:"
			for appidentifier in $(echo "$app_ldif" | sed -n 's/^cn: //p'); do
				echo -n " $appidentifier"
			done
			echo .
			return 2
		fi
	fi

	object_dn=$(echo "$schema_ldif" | sed -n 's/^dn: //p')

	univention-directory-manager settings/ldapschema delete "$@" \
		--dn="$object_dn"
}

#
# ucs_registerLDAPACL writes an LDAP ACL extension to UDM.
# A listener module then writes it to a persistent place.
#
# ucs_registerLDAPACL <ACL file> [options]
# e.g. ucs_registerLDAPACL /var/tmp/univention-testapp.acl
#
ucs_registerLDAPACL () {
	local SH_FUNCNAME
	SH_FUNCNAME=ucs_registerLDAPACL
	## Parse options
	local ucsversionstart ucsversionend

	display_help() {
		printf "usage: $SH_FUNCNAME [<options>] <ACL file>\n"
		printf "options:\n"
		printf "\t--ucsversionstart <ucsversionstart>\n"
		printf "\t--ucsversionend <ucsversionend>\n"
		printf "internal options:\n"
		printf "\t--binddn <binddn>\n"
		printf "\t--bindpwd <bindpwd>\n"
		printf "\t--bindpwdfile <bindpwdfile>\n"
	}

	local passthroughoptions
	while [ $# -gt 0 ]
	do
		case "$1" in
			"--binddn"|"--bindpwd"|"--bindpwdfile")
				eval "local ${1#--}=\"\$2\""
				passthroughoptions="$passthroughoptions ${1#--}"
				shift 2 || { echo missing argument to $1; return 2; }
				;;
			"--ucsversionstart"|"--ucsversionend")
				eval "${1#--}=\"\$2\""
				shift 2 || { echo missing argument to $1; return 2; }
				;;
			--)
				shift
				break
				;;
			"--help"|"-h"|"-?")
				display_help
				return 0
				;;
			-*)
				display_help
				return 1
				;;
			*)
				break
				;;
		esac
	done

	## Validate options
	if [ -n "$(echo "$ucsversionstart" | sed 's/[-.0-9]*//')" ]; then
		echo "ERROR: $SH_FUNCNAME: Option --ucsversionstart invalid: may only contain digit, dot and dash characters"
		return 1
	fi
	if [ -n "$(echo "$ucsversionend" | sed 's/[-.0-9]*//')" ]; then
		echo "ERROR: $SH_FUNCNAME: Option --ucsversionend invalid: may only contain digit, dot and dash characters"
		return 1
	fi

	## Parse arguments
	local ACLFile
	ACLFile="$1"
	if ! shift 1
	then
		echo "ERROR: $SH_FUNCNAME: wrong number of arguments" >&2
		display_help
		return 2
	fi

	## Validate arguments
	if [ ! -e "$ACLFile" ]; then
		echo "ERROR: $SH_FUNCNAME: given ACL file does not exist" >&2
		return 2
	fi

	## Restore passthrough options
	local key
	for key in $passthroughoptions; do
		val=$(eval echo \$$key)
		set -- "$@" "--$key" "$val"
	done

	local package_name package_version calling_script_name calling_script_basename
	calling_script_name=$(basename -- "$0")
	calling_script_basename=$(basename -- "$calling_script_name" .postinst)
	if [ "$calling_script_basename" != "$calling_script_name" ]; then
		package_name="$calling_script_basename"
	elif [ -n "$JS_SCRIPT_FULLNAME" ]; then
		package_name=$(dpkg -S "$JS_SCRIPT_FULLNAME" | cut -d: -f1)
	fi

	if [ -n "$package_name" ]; then
		package_version=$(dpkg-query -f '${Version}' -W "$package_name")
	else
		eval "$(ucr shell '^tests/ucs_registerLDAP/.*')"
		if [ -n "$tests_ucs_registerLDAP_packagename" ] && [ -n "$tests_ucs_registerLDAP_packageversion" ]; then
			package_name="$tests_ucs_registerLDAP_packagename"
			package_version="$tests_ucs_registerLDAP_packageversion"
		else
			echo "ERROR: $SH_FUNCNAME: Unable to determine Debian package name"
			echo "ERROR: This function only works in joinscript or postinst context"
			return 1
		fi
	fi

	local filename objectname target_container_name ldap_base target_container_dn
	filename=$(basename -- "$ACLFile")
	objectname=$(basename -- "$filename" ".acl")
	ldap_base="$(ucr get ldap/base)"
	target_container_name="ldapacl"
	target_container_dn="cn=$target_container_name,cn=univention,$ldap_base"

	univention-directory-manager container/cn create "$@" --ignore_exists \
		--set name="$target_container_name" \
		--position "cn=univention,$ldap_base"

	local ldif
	ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionACL)(cn=$objectname))" \
			univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion | ldapsearch-wrapper)
	if [ -z "$ldif" ]; then

		output=$(univention-directory-manager settings/ldapacl create "$@" \
			${ucsversionstart:+--set ucsversionstart="$ucsversionstart"} \
			${ucsversionend:+--set ucsversionend="$ucsversionend"} \
			--set name="$objectname" \
			--set filename="$filename" \
			--set acl="$(gzip -c "$ACLFile" | base64 -w0)" \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--position "$target_container_dn" 2>&1)
		echo "$output"

		if [ $? -eq 0 ]; then

			object_dn=$(echo "$output" | sed -n 's/^Object created: //p')

			if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
				univention-directory-manager settings/ldapacl modify "$@" \
					--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
					--dn "$object_dn"
			fi

		else	## check again, might be a race

			ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionACL)(cn=$objectname))" \
					univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion | ldapsearch-wrapper)

			if [ -z "$ldif" ]; then
				echo "ERROR: $SH_FUNCNAME: Failed to create settings/ldapacl object." >&2
				return 2
			fi
		fi
	fi

	if [ -n "$ldif" ]; then	## object exists already, modify it

		local registered_package registered_package_version
		registered_package=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackage: //p')
		registered_package_version=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackageVersion: //p')

		if [ "$registered_package" = "$package_name" ]; then
			if ! dpkg --compare-versions "$package_version" gt "$registered_package_version"; then
				echo "ERROR: $SH_FUNCNAME: registered package version $registered_package_version is newer, skipping registration." >&2
				return 2
			fi
		else
			echo "WARNING: $SH_FUNCNAME: ACL $objectname was registered by package $registered_package version $registered_package_version, changing ownership." >&2
		fi

		local object_dn
		object_dn=$(echo "$ldif" | sed -n 's/^dn: //p')

		output=$(univention-directory-manager settings/ldapacl modify "$@" \
			${ucsversionstart:+--set ucsversionstart=$ucsversionstart} \
			${ucsversionend:+--set ucsversionend=$ucsversionend} \
			--set acl="$(gzip -c "$ACLFile" | base64 -w0)" \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--dn "$object_dn" 2>&1)
		echo "$output"

		if [ $? -ne 0 ]; then
			echo "ERROR: $SH_FUNCNAME: Modification of settings/ldapacl object failed." >&2
			return 2
		else
			if echo "$output" | grep -q "^No modification: $object_dn$"; then
				return 0
			fi
		fi
			

		if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
			univention-directory-manager settings/ldapacl modify "$@" \
				--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
				--dn "$object_dn"
		fi

	fi

	timeout=180	#seconds
	echo -n "Waiting up to $timeout seconds for activation of the LDAP ACL extension: "
	local t t0
	t0=$(date +%s)
	while ! univention-directory-manager settings/ldapacl list "$@" \
			--filter "(&(name=$objectname)(active=TRUE))" | grep -q '^DN: '
	do
			t=$(date +%s)
			if [ $(($t - $t0)) -gt "$timeout" ]; then
				echo
				echo "ERROR: $SH_FUNCNAME: Master did not mark the LDAP ACL extension active within 3 minutes."
				return 1
			fi
			echo -n "."
			sleep 3
	done
	echo "OK"
}

# ucs_unregisterLDAPACL removes an LDAP ACL extension from UDM.
# A listener module then tries to remove it.
#
# ucs_unregisterLDAPACL <ACL file> [options]
# e.g. ucs_unregisterLDAPACL /var/tmp/univention-example.acl
#
ucs_unregisterLDAPACL () {
	local SH_FUNCNAME
	SH_FUNCNAME=ucs_unregisterLDAPACL

	display_help() {
		printf "usage: $SH_FUNCNAME [<options>] <ACL file>\n"
		printf "internal options:\n"
		printf "\t--binddn <binddn>\n"
		printf "\t--bindpwd <bindpwd>\n"
		printf "\t--bindpwdfile <bindpwdfile>\n"
	}

	## Parse arguments
	local ACLFile
	ACLFile="$1"
	if ! shift 1
	then
		echo "ERROR: $SH_FUNCNAME: wrong number of arguments" >&2
		display_help
		return 2
	fi

	## Validate arguments
	if [ ! -e "$ACLFile" ]; then
		echo "ERROR: $SH_FUNCNAME: given ACL file does not exist" >&2
		return 2
	fi

	local objectname
	objectname=$(basename -- "$ACLFile" ".acl")

	local ACL_ldif
	ACL_ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionACL)(cn=$objectname))" \
			univentionAppIdentifier | ldapsearch-wrapper)

	if [ -z "$ACL_ldif" ]; then
		echo "ERROR: $SH_FUNCNAME: ACL object not found in LDAP."
		return 1
	fi

	app_filter=""
	local appidentifier
	for appidentifier in $(echo "$ACL_ldif" | sed -n 's/^univentionAppIdentifier: //p'); do
		app_filter="$app_filter(cn=$appidentifier)"
	done

	if [ -n "$app_filter"]; then
		local app_ldif
		app_ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionApp)$app_filter)" cn | ldapsearch-wrapper)
		if [ -n "$app_ldif" ]; then
			echo -n "INFO: $SH_FUNCNAME: The ACL $objectname is still registered by the following apps:"
			for appidentifier in $(echo "$app_ldif" | sed -n 's/^cn: //p'); do
				echo -n " $appidentifier"
			done
			echo .
			return 2
		fi
	fi

	object_dn=$(echo "$ACL_ldif" | sed -n 's/^dn: //p')

	univention-directory-manager settings/ldapacl delete "$@" \
		--dn="$object_dn"
}
