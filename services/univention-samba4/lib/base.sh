# Univention Samba4 Shell Library (bash)
#
# Copyright 2012-2014 Univention GmbH
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


# Bug #27001
univention_samba4_is_ucr_false () { # test if UCS variable is "false"
    local value
    value="$(univention-config-registry get "$1")"
    case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
        1|yes|on|true|enable|enabled) return 1 ;;
        0|no|off|false|disable|disabled) return 0 ;;
        *) return 2 ;;
    esac
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

	ldif=$(univention-ldapsearch -LLLx "(&(objectClass=univentionDomainController)(univentionService=Samba 4))" cn associatedDomain | ldapsearch-wrapper)

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
		ldap_record=$(univention-ldapsearch -LLLx \
			"(&(objectClass=dNSZone)(zoneName=$domainname)(relativeDomainName=$record))" sRVRecord dn \
			| ldapsearch-wrapper)
		sRVRecord_DN=$(sed -n 's/^dn: //p' <<<"$ldap_record")
		sRVRecord_attrs=$(sed -n 's/^sRVRecord: //p' <<<"$ldap_record")

		zoneDN=$(univention-ldapsearch -LLLx "(&(objectClass=dNSZone)(zoneName=$domainname)(relativeDomainName=@))" dn \
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
