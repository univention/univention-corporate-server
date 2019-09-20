# Univention Samba4 Shell Library (bash)
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

. /usr/share/univention-lib/ldap.sh

# Bug #27001
univention_samba4_is_ucr_false () { # test if UCS variable is "false"
    local value
    value="$(univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr '[:upper:]' '[:lower:]')" in
        1|yes|on|true|enable|enabled) return 1 ;;
        0|no|off|false|disable|disabled) return 0 ;;
        *) return 2 ;;
    esac
}

extract_binddn_bindpwd_bindpwdfile_dcaccount_from_args() {
	## parse bind credentials from command line arguments into shell variables
	while [ $# -gt 0 ]; do
		case "$1" in
			"--binddn")
				binddn="${2:?missing binddn}"
				shift 2 || exit 2
				;;
			"--bindpwdfile")
				bindpwdfile="${2:?missing bindpwdfile}"
				shift 2 || exit 2
				;;
			*)
				shift
				;;
		esac
	done
	# dc account is empty on master and backup, unless --ask-pass is used
	test -n "$binddn" && dcaccount=$(ucs_convertDN2UID "$binddn" "$@")
	test -z "$binddn" && binddn="cn=admin,$ldap_base"
	test -z "$bindpwdfile" && bindpwdfile="/etc/ldap.secret"
	test -z "$bindpwd" && bindpwd="$(< "$bindpwdfile")"
}

assert_dcaccount_and_bindpwd() {
	if [ -z "$dcaccount" ] ||  [ -z "$bindpwd" ]; then
		echo "Administrative credentials are needed to join to existing Samba4 domain. Please run:"
		printf "\tunivention-run-join-scripts --ask-pass\n"
		echo "to complete the domain join."
		exit 1
	fi
}

extract_binddn_and_bindpwd_from_args() {
	## parse binddn and bindpwd from command line arguments into shell variables
	while [ $# -gt 0 ]; do
		case "$1" in
			"--binddn")
							binddn="${2:?missing binddn}"
							shift 2 || exit 2
							;;
			"--bindpwd")
							bindpwd="${2:?missing bindpwd}"
							shift 2 || exit 2
							;;
			*)
				shift
				;;
		esac
	done
}

univention_samba4_append_to_ucr() {
	key="${1?append_to_ucr needs two parameters, called without any}"
	value="${2?append_to_ucr needs two parameters, called only with \""$@"\"}"
	separator=','

	python <<-%EOF
	from univention.config_registry import ConfigRegistry
	ucr = ConfigRegistry()
	ucr.load()
	valuelist = ucr.get('$key', '').split('$separator')
	if not '$value' in valuelist:
	    valuelist.append('$value')
	    ucr['$key'] = '$separator'.join(valuelist)
	    ucr.save()
	%EOF
}

remove_non_samba4_dc_srv_records() {

	ldif=$(univention-ldapsearch -LLL "(&(objectClass=univentionDomainController)(univentionService=Samba 4))" cn associatedDomain | ldapsearch-wrapper)

	samba4_dcs_fqdn_list=("${hostname}.${domainname}")	## initialize with own fqdn for the initial join of the first Samba4 DC
	while read -d '' record; do
		if [ -n "$record" ]; then
			cn=$(sed -n 's/^cn: //p' <<<"$record")
			associatedDomain=$(sed -n 's/^associatedDomain: //p' <<<"$record")
			samba4_dcs_fqdn_list+=("${cn}.${associatedDomain}")
		fi
	done < <(echo -e "$ldif\n" | sed 's/^$/\x0/')

	relativeDomainName_list=('_kerberos._tcp' '_kerberos._udp' '_kpasswd._tcp' '_kpasswd._udp' '_ldap._tcp')

	for record in "${relativeDomainName_list[@]}"; do
		ldap_record=$(univention-ldapsearch -LLL \
			"(&(objectClass=dNSZone)(zoneName=$domainname)(relativeDomainName=$record))" sRVRecord dn \
			| ldapsearch-wrapper)
		sRVRecord_DN=$(sed -n 's/^dn: //p' <<<"$ldap_record")
		sRVRecord_attrs=$(sed -n 's/^sRVRecord: //p' <<<"$ldap_record")

		zoneDN=$(univention-ldapsearch -LLL "(&(objectClass=dNSZone)(zoneName=$domainname)(relativeDomainName=@))" dn \
			| ldapsearch-wrapper | sed -n 's/^dn: //p')

		while read line; do
			fields=($line)
			if [ "${#fields[@]}" = 4 ]; then
				unset offers_samba4_service
				for fqdn in "${samba4_dcs_fqdn_list[@]}"; do
					if [ "${fields[3]}" = "$fqdn." ]; then
						offers_samba4_service=1
						break
					fi
				done
				if [ -z "$offers_samba4_service" ] || [ "$record" = '_ldap._tcp' -a "${fields[2]}" -eq 7389 ] ; then
					echo "${fields[3]%%.} port ${fields[2]} is not offering the Service 'Samba 4'"
					univention-directory-manager dns/srv_record modify "$@" \
								--superordinate "$zoneDN" \
								--dn "$sRVRecord_DN" \
								--remove location="$line"
				fi
			fi
		done <<<"$sRVRecord_attrs"
	done
}

remove_port()
{
	# Test:
	# r 389
	# r 7389,389
	# r 389,7389
	# r 389,7389,8389
	# r 7389,389,8389
	# r 7389,8389,389

	if [ -n "$1" -a -n "$2" ]; then
		echo "$1" | sed -e "s|^${2},||;s|,${2},|,|;s|,${2}$||;s|^${2}$||"
	fi

}

disable_slapd_on_standard_port() {
	if [ -n "$slapd_port" ]; then
		univention-config-registry set slapd/port="$(remove_port "$slapd_port" 389)"
	fi
	if [ -n "$slapd_port_ldaps" ]; then
		univention-config-registry set slapd/port/ldaps="$(remove_port "$slapd_port_ldaps" 636)"
	fi

	/etc/init.d/slapd crestart
	sleep 1
}

is_ucs_school_domain() {
	local ldif

	ldif=$(univention-ldapsearch -LLL \
		"(univentionService=UCS@school)" \
		dn)

	grep -q "^dn: " <<<"$ldif"
}

is_localhost_administration() {
	local ldif
	local hostname="$(hostname)\$"
	local master=$(ucr get ldap/master)
	local master_port=$(ucr get ldap/master/port)
	ldif=$(univention-ldapsearch -h "$master" -p "$master_port" -LLL \
		"(&(uid=$hostname)(univentionService=UCS@school Administration))")
	grep -q "^dn: " <<<"$ldif"
}

is_localhost_education() {
	local ldif
	local hostname="$(hostname)\$"
	local master=$(ucr get ldap/master)
	local master_port=$(ucr get ldap/master/port)
	ldif=$(univention-ldapsearch -h "$master" -p "$master_port" -LLL \
		"(&(uid=$hostname)(univentionService=UCS@school Education))")
	grep -q "^dn: " <<<"$ldif"
}

# copied from ucs-school-lib/shell/base.sh
school_ou() {
	# syntax: school_ou [hostdn]
	#
	# Tries to determine the LDAP name of the host's OU.
	# The OU name is derived from the given host DN. If no DN has been passed to
	# the function, the hostdn of the system is used as fallback.
	# PLEASE NOTE: This function works only on domaincontroller_slave systems!
	#              Other systems will return an empty value!
	#
	# example:
	# $ ucr get ldap/hostdn
	# cn=myslave,cn=dc,cn=server,cn=computers,ou=gymmitte,dc=example,dc=com
	# $ school_ou
	# gymmitte
	# $ school_ou cn=myslave,cn=dc,cn=server,cn=computers,ou=foobar,dc=example,dc=com
	# foobar
	# $ school_ou cn=myslave,cn=dc,cn=server,cn=computers,ou=foo,ou=bar,dc=example,dc=com
	# foo

	local ldap_hostdn

	if [ -n "$1" ] ; then
		ldap_hostdn=",$1" # add leading comma, in case only the DN of the OU is given
	else
		ldap_hostdn="$(/usr/sbin/univention-config-registry get ldap/hostdn)"
	fi

	echo "$ldap_hostdn" | grep -oiE ',ou=.*$' | sed -nre 's/^,[oO][uU]=([^,]+),.*/\1/p'
}

# copied from ucs-school-lib/shell/base.sh
school_dn() {
	# syntax: school_dn [hostdn]
	#
	# Tries to determine the LDAP DN of the host's OU.
	# The OU DN is derived from the given host DN. If no DN has been passed to
	# the function, the hostdn of the system is used as fallback.
	# PLEASE NOTE: This function works only on domaincontroller_slave systems!
	#              Other systems will return an empty value!
	#
	# example:
	# $ ucr get ldap/hostdn
	# cn=myslave,cn=dc,cn=server,cn=computers,ou=gymmitte,dc=example,dc=com
	# $ school_dn
	# ou=gymmitte,dc=example,dc=com
	# $ school_dn cn=myslave,cn=dc,cn=server,cn=computers,ou=foobar,dc=example,dc=com
	# ou=foobar,dc=example,dc=com
	# $ school_dn cn=myslave,cn=dc,cn=server,cn=computers,ou=foo,ou=bar,dc=example,dc=com
	# ou=foo,ou=bar,dc=example,dc=com

	local ldap_hostdn

	if [ -n "$1" ] ; then
		ldap_hostdn=",$1" # add leading comma, in case only the DN of the OU is given
	else
		ldap_hostdn="$(/usr/sbin/univention-config-registry get ldap/hostdn)"
	fi

	echo "$ldap_hostdn" | grep -oiE ',ou=.*$' | cut -b2-
}

get_available_s4connector_dc() {
	local s4cldapbase
	local s4cldapfilter
	local OU
	local ldif
	local s4connector_dc
	local s4connector_dc_array

	eval "$(ucr shell ldap/base ldap/hostdn)"

	s4cldapbase="$ldap_base"
	s4cldapfilter="(&(univentionService=S4 Connector)(objectClass=univentionDomainController))"
	if is_ucs_school_domain; then
		OU=$(school_ou "$ldap_hostdn")
		if [ -z "$OU" ]; then
			## We are in a central school department, ignore all S4 SlavePDC:
			s4cldapfilter="(&(!(univentionService=S4 SlavePDC))(univentionService=S4 Connector)(objectClass=univentionDomainController))"
			## or alternatively, defacto this should give the same result:
			## s4cldapfilter="(&(univentionService=S4 Connector)(univentionServerRole=master)(univentionServerRole=backup))"
		else
			## We are in a school department
			## this can either be the administration or the education section,
			## both have separate samba domains, so ignore the other section
			if is_localhost_education; then
				s4cldapfilter="(&(univentionService=S4 SlavePDC)(univentionService=S4 Connector)(objectClass=univentionDomainController)(univentionService=UCS@school Education))"
			elif is_localhost_administration; then
				s4cldapfilter="(&(univentionService=S4 SlavePDC)(univentionService=S4 Connector)(objectClass=univentionDomainController)(univentionService=UCS@school Administration))"
			else
				## unsupported, a school slave with UCS@school Administration or UCS@school Education service
				echo "ERROR: This seems to be a UCS@school school department server," 1>&2
				echo "ERROR: but is neither a administrative nor a educative server." 1>&2
				echo "ERROR: This is not supported, make sure that UCS@school metapackages are installed properly" 1>&2
				return 1
			fi
			s4cldapbase=$(school_dn "$ldap_hostdn")
		fi
	fi

	ldif=$(univention-ldapsearch -b "$s4cldapbase" \
		-LLLo ldif-wrap=no \
		"$s4cldapfilter" cn)
	s4connector_dc=$(sed -n 's/^cn: \(.*\)/\1/p' <<<"$ldif")

	if is_ucs_school_domain; then
		s4connector_dc_array=( $s4connector_dc )
		if [ "${#s4connector_dc_array[@]}" -gt 1 ]; then
			echo "ERROR: More than one S4 Connector hosts available: ${s4connector_dc_array[*]}" 1>&2
			# check for slaves without "S4 SlavePDC"
			broken_school_slaves="$(univention-ldapsearch -LLL "(&$s4cldapfilter(univentionServerRole=slave))" cn | sed -n -e 's|^cn: ||p' | tr '\n' ' ')"
			if [ -n "$broken_school_slaves" -a -z "$OU" ]; then
				echo "ERROR:"
				echo "ERROR: If this is a central (non-school) slave, make sure every school slave" 1>&2
				echo "ERROR: has the 'univentionService=S4 SlavePDC' service set!" 1>&2
				echo "ERROR: Possible broken school slaves: $broken_school_slaves" 1>&2
			fi
			return 1	## this is fatal
		fi
	fi

	echo "$s4connector_dc"
}

extract_rIDNextRID() {
	local test_output
	local ridset_dn
	## Workaround for Bug #34754
	if [ -r /var/lib/samba/private/sam.ldb ]; then
		ridset_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb sAMAccountName="$hostname$" rIDSetReferences  | ldapsearch-wrapper | sed -n 's/^rIDSetReferences: //p')
		if [ -n "$ridset_dn" ]; then
			echo "extract_rIDNextRID: Saving rid pool"
			test_output=$(ldbsearch -H /var/lib/samba/private/sam.ldb -s base -b "$ridset_dn" | ldapsearch-wrapper)
			old_rIDAllocationPool=$(sed -n 's/^rIDAllocationPool: //p' <<<"$test_output")
			old_rIDPreviousAllocationPool=$(sed -n 's/^rIDPreviousAllocationPool: //p' <<<"$test_output")
			old_rIDNextRID=$(sed -n 's/^rIDNextRID: //p' <<<"$test_output")
		else
			echo "extract_rIDNextRID: Attribute rIDSetReferences not found"
		fi
	fi
}

restore_rIDNextRID() {
	local test_output
	local ridset_dn
	## Workaround for Bug #34754
	if [ -r /var/lib/samba/private/sam.ldb ]; then
		ridset_dn=$(ldbsearch -H /var/lib/samba/private/sam.ldb sAMAccountName="$hostname$" rIDSetReferences  | ldapsearch-wrapper | sed -n 's/^rIDSetReferences: //p')
		if [ -n "$ridset_dn" ]; then
			test_output=$(ldbsearch -H /var/lib/samba/private/sam.ldb -s base -b "$ridset_dn" | ldapsearch-wrapper)
			new_rIDAllocationPool=$(sed -n 's/^rIDAllocationPool: //p' <<<"$test_output")
			new_rIDPreviousAllocationPool=$(sed -n 's/^rIDPreviousAllocationPool: //p' <<<"$test_output")
			new_rIDNextRID=$(sed -n 's/^rIDNextRID: //p' <<<"$test_output")
		else
			echo "restore_rIDNextRID: Attribute rIDSetReferences not found"
		fi
	fi
	if [ -n "$new_rIDAllocationPool" ] && [ -z "$new_rIDNextRID" ]; then
		if [ "$new_rIDAllocationPool" = "$old_rIDAllocationPool" ] && [ -n "$old_rIDNextRID" ]; then
			echo "restore_rIDNextRID: Restoring rid pool"
			{
			cat <<-%EOF
			dn: $ridset_dn
			changetype: modify
			add: rIDNextRID
			rIDNextRID: $old_rIDNextRID
			%EOF

			if [ -z "$new_rIDPreviousAllocationPool" ]; then
				if [ -n "$old_rIDPreviousAllocationPool" ]; then
					cat <<-%EOF
					-
					add: rIDPreviousAllocationPool
					rIDPreviousAllocationPool: $old_rIDPreviousAllocationPool
					%EOF
				else
					cat <<-%EOF
					-
					add: rIDPreviousAllocationPool
					rIDPreviousAllocationPool: $new_rIDAllocationPool
					%EOF
				fi
			fi
			} | ldbmodify -H /var/lib/samba/private/sam.ldb
		else
			if [ -n "$old_rIDNextRID" ]; then
				echo "restore_rIDNextRID: Not Restoring"
				echo "restore_rIDNextRID: new_rIDAllocationPool: $new_rIDAllocationPool, old_rIDAllocationPool: $old_rIDAllocationPool"
			fi
		fi
	fi
}

cleanup_var_lib_samba()
{
	local backup_folder
	backup_folder="/var/lib/samba_backup_$(date +%Y%m%d%H%M%S)"
	if var_lib_samba_is_s4; then
		extract_rIDNextRID
		mv /var/lib/samba "$backup_folder"
		## and copy everything back except private/*
		rsync -a --exclude /private/* "$backup_folder/" /var/lib/samba
	fi
}

samba4_ldb_sam_module_prepend()
{
	local variables
	local domaindn
	local LDB_URI
	local module
	local register_opts
	local sam_ldb
	local tempfile
	## check if any of the relevant options are set
	variables="$(univention-config-registry search --brief "^samba4/ldb/sam/module/")"
	if [ -n "$variables" ]; then
		sam_ldb="/var/lib/samba/private/sam.ldb"
		LDB_URI="tdb://$sam_ldb"

		domaindn="DC=${kerberos_realm//./,DC=}" # that's what /usr/share/pyshared/samba/provision.py uses
		if ! ldbsearch -H "$LDB_URI" -b $domaindn -s base dn 2>/dev/null| grep -qi ^"dn: $domaindn"; then
			echo "Samba4 does not seem to be provisioned, skipping samba4_ldb_sam_module_prepend"
			exit 1
		fi

		## check the samba4/ldb/sam/module/prepend list
		if [ -n "$samba4_ldb_sam_module_prepend" ]; then
			for module in $samba4_ldb_sam_module_prepend; do
				register_opts="$register_opts --prepend $module"
			done
		fi

		if [ -n "$register_opts" ]; then
			## backup LDB file
			tempfile="$(mktemp)"
			cp "$sam_ldb" "$tempfile"

			## Restart the S4 Connector to check samba4/ldb/sam/module/prepend and use the bypass_samaccountname_ldap_check control
			if [ -x /etc/init.d/univention-s4-connector ]; then
				invoke-rc.d univention-s4-connector crestart
			fi

			## Register the Module
			/usr/share/univention-samba4/scripts/register_ldb_module.py -H "$sam_ldb" --ignore-exists $register_opts
			## check if ldb file is ok
			if ldbsearch -H "$sam_ldb" -b '@MODULES' -s base  > /dev/null; then
				rm "$tempfile"
			else
				echo "Restoring original sam.ldb"
				mv "$tempfile" "$sam_ldb"
			fi
		fi
	fi
}
