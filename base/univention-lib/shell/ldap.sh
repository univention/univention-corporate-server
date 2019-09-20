# Univention Common Shell Library
#
# Copyright 2011-2019 Univention GmbH
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


#
# ucs_getAttrOfDN returns the attribute value of an LDAP object
# ucs_getAttrOfDN <attributename> <DN> [<ldapsearch-credentials>]
# e.g. ucs_getAttrOfDN "krb5PasswordEnd" "uid=testuser,cn=users,dc=test,dc=system"
# ==> 20110622112559Z
#
ucs_getAttrOfDN () { # <attr> <dn> [<ldapsearch-credentials>]
	local attr="$1"
	local base="$2"
	if ! shift 2
	then
		echo "ucs_getAttrOfDN: wrong number of arguments" >&2
		return 2
	fi
	if [ -n "$attr" ]; then
		univention-ldapsearch "$@" -s base -b "$base" -LLL "$attr" \
			| ldapsearch-wrapper | ldapsearch-decode64 | sed -ne "s/^$attr: //p"
	fi
}

die() {
	rc=$?
	echo "$@"
	exit $rc
}

#
# ucs_convertUID2DN returns DN of user object for specified UID
# ucs_convertUID2DN <uid> [<ldapsearch-credentials>]
# e.g. ucs_convertUID2DN "testuser"
#
ucs_convertUID2DN () { # <uid> [<ldapsearch-credentials>]
	local uid="$1"
	if ! shift 1
	then
		echo "ucs_convertUID2DN: wrong number of arguments" >&2
		return 2
	fi
	if [ -n "$uid" ]; then
		univention-ldapsearch "$@" -LLL "(&(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=univentionMail)(objectClass=sambaSamAccount)(objectClass=simpleSecurityObject)(&(objectClass=person)(objectClass=organizationalPerson)(objectClass=inetOrgPerson)))(!(uidNumber=0))(!(uid=*\$))(uid=$uid))" dn | ldapsearch-wrapper | ldapsearch-decode64 | sed -ne 's/dn: //p'
	fi
}

#
# ucs_convertDN2UID returns UID of user object for specified DN
# ucs_convertDN2UID <user dn> [<ldapsearch-credentials>]
# e.g. ucs_convertDN2UID "uid=testuser,cn=users,dc=test,dc=system"
#
ucs_convertDN2UID () { # <userdn> [<ldapsearch-credentials>]
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
ucs_getGroupMembersDirect () { # <groupDN> [<ldapsearch-credentials>]
	local groupdn="$1"
	if ! shift 1
	then
		echo "ucs_getGroupMembersDirect: wrong number of arguments" >&2
		return 2
	fi
	ucs_getAttrOfDN "uniqueMember" "$groupdn" "$@"
}

#
# ucs_getGroupMembersRecursive returns all members of specified group and of all nested groups
# ucs_getGroupMembersRecursive <group dn> [<ldapsearch-credentials>]
# e.g. ucs_getGroupMembersRecursive "cn=Domain Admins,cn=groups,dc=test,dc=system"
#
# optional environment: ldap_binddn and ldap_bindpw
#
ucs_getGroupMembersRecursive () { # <groupDN> [<ldapsearch-credentials>]
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
		ldif=$(univention-ldapsearch "$@" -LLL -b "$reply" '(!(objectClass=univentionGroup))' dn | sed -ne "s/^dn: //p")
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
	local server_role ldap_hostdn
	local servicename="$1"
	if ! shift 1
	then
		echo "ucs_addServiceToLocalhost: wrong argument number" >&2
		return 2
	fi
	eval "$(/usr/sbin/univention-config-registry shell server/role ldap/hostdn)"
	ucs_addServiceToHost "$servicename" "$server_role" "$ldap_hostdn" "$@"
}

#
# ucs_addServiceToHost adds a new service entry to specified UDM host object. This can be easily used
# in e.g. join scripts to add a new service. Additional arguments like UDM credentials will be passed 
# through.
# ucs_addServiceToHost <servicename> <udm-module-name> <dn> [<udm-credentials>]
# e.g. ucs_addServiceToHost "nagios-server" "domaincontroller_slave" "cn=myslave,cn=dc,cn=computers,dc=test,dc=system" "$@"
#
ucs_addServiceToHost () { # <servicename> <udm-module-name> <dn> [options]
	local servicename="$1"
	local modulename="$2"
	local hostdn="$3"
	local ldap_base="$(/usr/sbin/univention-config-registry get ldap/base)"
	if ! shift 3
	then
		echo "ucs_addServiceToHost: wrong argument number" >&2
		return 2
	fi
	univention-directory-manager container/cn create "$@" --ignore_exists \
		--set name="services" --position "cn=univention,$ldap_base"
	univention-directory-manager settings/service create "$@" --ignore_exists \
		--set name="$servicename" --position "cn=services,cn=univention,$ldap_base"
	univention-directory-manager "computers/$modulename" modify "$@" \
		--dn "$hostdn" --append service="$servicename"
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
	local server_role ldap_hostdn
	local servicename="$1"
	if ! shift 1
	then
		echo "ucs_removeServiceFromLocalhost: wrong argument number" >&2
		return 2
	fi
	eval "$(/usr/sbin/univention-config-registry shell server/role ldap/hostdn)"
	ucs_removeServiceFromHost "$servicename" "$server_role" "$ldap_hostdn" "$@"
}

#
# ucs_removeServiceFromHost removes a service entry from specified UDM host object. This can be easily used
# in e.g. join scripts to remove a service. Additional arguments like UDM credentials will be passed 
# through.
# ucs_removeServiceFromHost <servicename> <udm-module-name> <dn> [<udm-credentials>]
# e.g. ucs_removeServiceFromHost "nagios-server" "domaincontroller_slave" "cn=myslave,cn=dc,cn=computers,dc=test,dc=system" "$@"
#
ucs_removeServiceFromHost () { # <servicename> <udm-module-name> <dn> [options]
	local servicename="$1"
	local modulename="$2"
	local hostdn="$3"
	local ldap_base="$(/usr/sbin/univention-config-registry get ldap/base)"
	if ! shift 3
	then
		echo "ucs_removeServiceFromHost: wrong argument number" >&2
		return 2
	fi
	univention-directory-manager "computers/$modulename" modify "$@" \
		--dn "$hostdn" --remove service="$servicename"
	if ucs_isServiceUnused "$servicename" "$@" &&
		univention-directory-manager settings/service list "$@" \
			--position "cn=$servicename,cn=services,cn=univention,$ldap_base" >/dev/null
	then
		univention-directory-manager settings/service remove "$@" \
			--dn "cn=$servicename,cn=services,cn=univention,$ldap_base"
	fi
}

#
# parse join credentials and save them in
# binddn bindpwd (bindpwdfile)
# ucs_parseCredentials "$@"
#  $binddn
#
ucs_parseCredentials () {
	while [ $# -ge 1 ]
	do
		case "$1" in
		--binddn)
			binddn="$2"
			shift 2 || die "Missing argument to --binddn"
			;;
		--bindpwd)
			bindpwd="$2"
			shift 2 || die "Missing argument to --bindpwd"
			;;
		--bindpwdfile)
			bindpwdfile="$2"
			shift 2 || die "Missing argument to --bindpwdfile"
			[ -f "$bindpwdfile" ] || die "Missing bindpwdfile $bindpwdfile"
			;;
		*)
			shift
			;;
		esac
	done
}

#
# ucs_isServiceUnused cechks whether a service entry is used.
# ucs_isServiceUnused <servicename> [<udm-credentials>]
# e.g.  if ucs_isServiceUnused "DNS" "$@"; then uninstall DNS; fi
#
ucs_isServiceUnused () { # <servicename>
	local servicename="$1"
	local master="$(/usr/sbin/univention-config-registry get ldap/master)"
	local port="$(/usr/sbin/univention-config-registry get ldap/master/port)"

	if ! shift 1
	then
		echo "ucs_lastHostWithService: wrong argument number" >&2
		return 2
	fi

	if [ -z "$port" ]
	then
		port=7389
	fi

	ucs_parseCredentials "$@"

	# search always on the master
	set -- -H "ldap://$master:$port"

	# set credentials
	if [ -n "$binddn" ] && [ -n "$bindpwd" ]
	then
		set -- "$@" -D "$binddn" -w "$bindpwd"
	elif [ -n "$binddn" ] && [ -n "$bindpwdfile" ]
	then
		set -- "$@" -D "$binddn" -y "$bindpwdfile"
	fi

	# create a tempfile to get the real return code of the ldapsearch command,
	# otherwise we get only the code of the sed command
	local tempfile="$(mktemp)"
	univention-ldapsearch univentionService="${servicename}" "$@" cn >"$tempfile"
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

# ucs_registerLDAPExtension writes an LDAP schema or ACL extension to UDM.
# A listener module then writes it to a persistent place and restarts slapd.
#
# e.g. ucs_registerLDAPExtension --schema /usr/share/univention-fetchmail-schema/univention-fetchmail.schema \
#                                --acl /var/tmp/foo.acl
#
ucs_registerLDAPExtension () {
	local SH_FUNCNAME
	SH_FUNCNAME=ucs_registerLDAPExtension

	package_options_are_passed() {
		local opttemp
		opttemp=$(getopt -q -o '' --longoptions 'packagename:,packageversion:' --name "ucs_registerLDAPExtension" -- "$@")
		eval set -- "$opttemp"

	usage() {
		echo >&2 "usage: ucs_registerLDAPExtension [--packagename <name> --packageversion <version>]"
		exit 1
	}

		local package_name
		local package_version
		while [ $# -gt 0 ]; do
			case "$1" in
				--packagename)
					package_name="$2"
					shift 2
					;;
				--packageversion)
					package_version="$2"
					shift 2
					;;
				--)
					shift
					break
					;;
				*)
					shift
					;;
			esac
		done

		if   [ -n "$package_name" ]; then
			if [ -n "$package_version" ]; then
				return 0
			else
				echo >&2 "Option --packagename requires --packageversion too"
				exit 1
			fi
		else
			if [ -n "$package_version" ]; then
				echo >&2 "Option --packageversion requires --packagename too"
				exit 1
			else
				return 1
			fi
		fi
	}

	if ! package_options_are_passed "$@"; then
		local calling_script_name
		local calling_script_basename
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
			eval "$(/usr/sbin/univention-config-registry shell '^tests/ucs_registerLDAP/.*')"
			if [ -n "$tests_ucs_registerLDAP_packagename" ] && [ -n "$tests_ucs_registerLDAP_packageversion" ]; then
				package_name="$tests_ucs_registerLDAP_packagename"
				package_version="$tests_ucs_registerLDAP_packageversion"
			else
				echo "ERROR: $SH_FUNCNAME: Unable to determine Debian package name"
				echo "ERROR: This function only works in joinscript or postinst context"
				return 1
			fi
		fi
	fi

	local rc
	python -m univention.lib.ldap_extension ucs_registerLDAPExtension --packagename "$package_name" --packageversion "$package_version" "$@"

	rc=$?
	case $rc in
		4) return 0	## mask non-fatal return code
		   ;;
		*) return $rc
		   ;;
	esac
}

# ucs_unregisterLDAPExtension removes an LDAP schema or ACL extension from UDM.
# A listener module then tries to remove it.
#
# ucs_unregisterLDAPACL <ac file> [options]
# e.g. ucs_unregisterLDAPExtension --acl <acl object name> --schema <schema object name>
#
ucs_unregisterLDAPExtension () {
	python -m univention.lib.ldap_extension ucs_unregisterLDAPExtension "$@"
}


# ucs_registerLDAPSchema copies the LDAP schema to a persistent place /var/lib/univention-ldap/local-schema/
# and it will not be removed if the package is uninstalled.
# ucs_registerLDAPSchema <schema file>
# e.g. ucs_registerLDAPSchema /usr/share/univention-fetchmail-schema/univention-fetchmail.schema
#
ucs_registerLDAPSchema () {
	local schemaFile="$1"

	if [ ! -d /var/lib/univention-ldap/local-schema ]; then
		mkdir -p /var/lib/univention-ldap/local-schema
		chmod 755 /var/lib/univention-ldap/local-schema
	fi

	if [ ! -e "$schemaFile" ]; then
		echo "ucs_registerLDAPSchema: missing schema file" >&2
		return 2
	fi

	cp "$schemaFile" /var/lib/univention-ldap/local-schema/

	/usr/sbin/univention-config-registry commit /etc/ldap/slapd.conf

	test -x /etc/init.d/slapd && /etc/init.d/slapd crestart
}
