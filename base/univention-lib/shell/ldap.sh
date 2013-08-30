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
# ucs_registerLDAPSchema copies the LDAP schema to a persistent place /var/lib/univention-ldap/local-schema/
# and it will not be removed if the package is uninstalled.
# ucs_registerLDAPSchema <schema file>
# e.g. ucs_registerLDAPSchema /usr/share/univention-fetchmail-schema/univention-fetchmail.schema
#
ucs_registerLDAPSchema () {
	local schemaFile="$1"

	if [ ! -e "$schemaFile" ]; then
		echo "ucs_registerLDAPSchema: missing schema file" >&2
		return 2
	fi

	local package_name package_version
	if [ -n "$DPKG_MAINTSCRIPT_PACKAGE" ]; then
		package_name="$DPKG_MAINTSCRIPT_PACKAGE"
	elif [ -n "$JS_SCRIPT_FULLNAME" ]; then
		package_name=$(dpkg -S "$JS_SCRIPT_FULLNAME" | cut -d: -f1)
	fi

	if [ -n "$package_name" ]; then
		echo "ERROR: Unable to determine Debian package name"
		echo "ERROR: This function only works in joinscript or postinst context"
		exit 1
	fi

	package_version=$(dpkg-query -f '${Version}' -W "$package_name")

	local filename=$(basename "$schemaFile")
	local objectname=$(basename "$filename" ".schema")
	local target_container_name="ldapschema"
	local target_container_dn="cn=$target_container_name,cn=univention,$ldap_base"
	local ldap_base="$(ucr get ldap/base)"

	univention-directory-manager containers/cn create "$@" --ignore_exists \
		--set name="$target_container_name" \
		--position "cn=univention,$ldap_base"

	local ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionSchema)(cn=$objectname))" \
											univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion)
	if [ -z "$ldif" ]; then

		output=$(univention-directory-manager settings/ldapschema create "$@" \
			--set name="$objectname" \
			--set filename="$filename" \
			--set schema=$(<"$schemaFile") \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--position "$target_container_dn")

		if [ $? -eq 0 ]; then

			object_dn=$(echo "$output" | sed -n 's/^Object created: //p')

			if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
				univention-directory-manager settings/ldapschema modify "$@" \
					--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
					--dn "$object_dn"
			fi

		else	## check again, might be a race

			ldif=$(univention-ldapsearch -xLLL "(&(objectClass=univentionLDAPExtensionSchema)(cn=$objectname))" \
												univentionLDAPExtensionPackage univentionLDAPExtensionPackageVersion)

		fi
	fi

	if [ -n "$ldif" ]; then	## object exists already, modify it

		local object_dn=$(echo "$ldif" | sed -n 's/^dn: //p')
		local registered_package=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackage: //p')
		local registered_package_version=$(echo "$ldif" | sed -n 's/^univentionLDAPExtensionPackageVersion: //p')

		if [ "$registered_package" = "$package_name" ]; then
			if ! dpkg --compare-versions "$package_version" gt "$registered_package_version"; then
				echo "ucs_registerLDAPSchema: ERROR: registered package version $registered_package_version is newer, skipping registration." >&2
				exit 2
			fi
		else
			echo "ucs_registerLDAPSchema: WARNING: schema $objectname was registered by package $registered_package version $registered_package_version, changing ownership." >&2
		fi

		univention-directory-manager settings/ldapschema modify "$@" \
			--set schema=$(gzip -c "$schemaFile" | base64) \
			--set active=FALSE \
			--set package="$package_name" \
			--set packageversion="$package_version" \
			--dn "$object_dn"

		if [ -n "$UNIVENTION_APP_IDENTIFIER" ]; then
			univention-directory-manager settings/ldapschema modify "$@" \
				--append appidentifier="$UNIVENTION_APP_IDENTIFIER" \
				--dn "$object_dn"
		fi

	fi

	local t t0=$(date +%s)
	while ! univention-directory-manager settings/ldapschema list "$@" \
			--filter "(&(name=$objectname)(active=TRUE))" | grep -q '^DN: '
	do
			t=$(date +%s)
			if [ $(($t - $t0)) -gt 300 ]; then
				echo "ERROR: Master did not mark the LDAP schema extension active within 5 minutes."
				exit 1
			fi
			sleep 3
	done
}

