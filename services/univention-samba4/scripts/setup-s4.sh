#!/bin/bash
#
# Copyright 2004-2012 Univention GmbH
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

LDB_MODULES_PATH=/usr/lib/ldb; export LDB_MODULES_PATH;		## currently necessary for ldbtools

eval "$(univention-config-registry shell)"

usage(){ echo "$0 [-h|--help] [-w <samba4-admin password file>] [-W]"; exit 1; }

SCRIPTDIR=/usr/share/univention-samba4/scripts
LOGFILE="/var/log/univention/samba4-provision.log"

touch $LOGFILE
chmod 600 $LOGFILE

adminpw="$(pwgen -1 -s -c -n 16)"
adminpw2="$adminpw"

while getopts  "h-:W:" option; do
	case "${option}" in
		h) usage;;
		-)
		case "${OPTARG}" in
			binddn)
				binddn="${!OPTIND}"
				OPTIND=$((OPTIND+1))
				;;
			bindpwd)
				bindpwd="${!OPTIND}"
				OPTIND=$((OPTIND+1))
				;;
			help)
				usage
				;;
			*)
				echo "Unknown option --${OPTARG}" >&2
				;;
		esac;;
		w) if [ -r "$OPTARG" ]; then adminpw="$(< $OPTARG)"; adminpw2="$adminpw"; fi ;;
		W) adminpw2='!unset';;
	esac
done

DOMAIN_SID="$(univention-ldapsearch -x "(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" sambaSID | sed -n 's/sambaSID: \(.*\)/\1/p')"

# Search for Samba 3 DCs
S3_DCS="$(univention-ldapsearch -x "(&(objectclass=univentionDomainController)(univentionService=Samba 3))" cn | sed -n 's/cn: \(.*\)/\1/p')"
if [ -n "$S3_DCS" ]; then
	## safty belt
	if is_ucr_true samba4/ignore/mixsetup; then
		echo "WARNING: The following Samba 3 domaincontroller have been found:"
		echo "         $S3_DCS"
		echo "         It is not possible to install a samba 4 domaincontroller "
		echo "         into a samba 3 environment.samba4/ignore/mixsetup is true."
		echo "         Continue as requested"
	else
		echo "ERROR: The following Samba 3 domaincontroller have been found:"
		echo "       $S3_DCS"
		echo "       It is not possible to install a samba 4 domaincontroller "
		echo "       into a samba 3 environment."
		exit 1
	fi
fi

if [ -z "$binddn" ]; then
	if [ -r "/etc/ldap.secret" ]; then
		binddn="cn=admin,$ldap_base"
		bindpwd=$(< /etc/ldap.secret)
	else
		echo "ERROR: Options --binddn and --bindpwd not given for samba3upgrade"
		exit 1
	fi
fi
## store the binddn and bindpwd options in UDM_ARGV
UDM_ARGV=("--binddn" "$binddn" --bindpwd "$bindpwd")
set -- "${UDM_ARGV[@]}"


while [ "$adminpw" != "$adminpw2" ]; do
	read -p "Choose Samba4 admin password: " adminpw
	if [ "${#adminpw}" -lt 8 ]; then
		echo "Password too short, Samba4 minimal requirements: 8 characters, one digit, one uppercase"
		continue
	fi
	read -p "Confirm password: " adminpw2
	if [ "$adminpw" != "$adminpw2" ]; then
		echo "Passwords don't match, please try again"
	fi
done

## Provision Samba4
eval "$(univention-config-registry shell)"	## eval again

if [ -x /etc/init.d/samba ]; then
	/etc/init.d/samba stop 2>&1 | tee -a "$LOGFILE"
fi
if [ -x /etc/init.d/winbind ]; then
	/etc/init.d/winbind stop 2>&1 | tee -a "$LOGFILE"
fi
univention-config-registry set samba/autostart=no winbind/autostart=no 2>&1 | tee -a "$LOGFILE"

/etc/init.d/heimdal-kdc stop 2>&1 | tee -a "$LOGFILE"
univention-config-registry set kerberos/autostart=no 2>&1 | tee -a "$LOGFILE"

if [ ! -e /usr/modules ]; then
	ln -s /usr/lib /usr/modules		# somehow MODULESDIR is set to /usr/modules in samba4 source despite --enable-fhs
fi

if [ -z "$samba4_function_level" ]; then
	samba4_function_level=2003
	univention-config-registry set samba4/function/level="$samba4_function_level"
fi


S3_DOMAIN_SID_FOR_MY_DOMAIN="$(univention-ldapsearch -x "(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" sambaSID | sed -n 's/sambaSID: \(.*\)/\1/p')"
if [ -z "$S3_DCS" ] || [ -z "$S3_DOMAIN_SID_FOR_MY_DOMAIN" ]; then

	if [ -z "$DOMAIN_SID" ]; then
		# No SID for this windows/domain has been generated
		DOMAIN_SID="$(univention-newsid)"
	fi

	/usr/share/samba/setup/provision --realm="$kerberos_realm" --domain="$windows_domain" --domain-sid="$DOMAIN_SID" \
						--function-level="$samba4_function_level" \
						--adminpass="$adminpw" --server-role='domain controller'	\
						--machinepass="$(</etc/machine.secret)" 2>&1 | tee -a "$LOGFILE"

else

	eval $(echo "$@" | sed -n 's/.*--binddn \(.*\) --bindpwd \(.*\).*/binddn="\1"\nbindpwd="\2"/p')
	groups=("Windows Hosts" "DC Backup Hosts" "DC Slave Hosts" "Computers" "Power Users")
	for group in "${groups[@]}"; do
		record=$(univention-ldapsearch -xLLL "(&(cn=$group)(objectClass=univentionGroup))" dn description | ldapsearch-wrapper)
		description=$(echo "$record" | sed -n 's/^description: \(.*\)/\1/p')
		if [ -z "$description" ]; then
			dn=$(echo "$record" | sed -n 's/^dn: \(.*\)/\1/p')
			univention-directory-manager groups/group modify "$@" --dn "$dn" --set description="$group"
		fi
	done

	### create ldifs to temporarily fix sambaGroupType 5 and 2 for samba3upgrade
	### unfortunately udm currently does not allow setting sambaGroupType=4
	create_modify_ldif() {
		record="$1"
		dn=$(echo "$record" | sed -n "s/dn: \(.*\)/\1/p")
		if [ -n "$dn" ]; then
			cat <<-%EOF
			dn: $dn
			changetype: modify
			replace: sambaGroupType
			sambaGroupType: 4
			-

			%EOF
		fi
	}

	ldif_records() {
		func="$1"; shift
		if ! declare -F "$func" >/dev/null; then
			echo "ldif_records: First argument must be a valid function name"
			echo "ldif_records: "$func" is not a valid function name"
			return 1
		fi
		while read -d '' record; do
			"$func" "$record" "$@"
		done < <(sed 's/^$/\x0/')	## beware: skips last record, but that's ok with usual univention-ldapsearch output
	}

	ldif_sambaGroupType_5_to_4=$(univention-ldapsearch sambaGroupType=5 dn sambaGroupType | ldif_records create_modify_ldif)
	reverse_ldif_sambaGroupType_5_to_4="${ldif_sambaGroupType_5_to_4//sambaGroupType: 4/sambaGroupType: 5}"

	ldif_sambaGroupType_2_to_4=$(univention-ldapsearch sambaGroupType=2 dn sambaGroupType | ldif_records create_modify_ldif)
	reverse_ldif_sambaGroupType_2_to_4="${ldif_sambaGroupType_2_to_4//sambaGroupType: 4/sambaGroupType: 2}"

	reverse_sambaGroupType_change() {
		echo "$reverse_ldif_sambaGroupType_5_to_4" | ldapmodify -D "$binddn" -w "$bindpwd" | tee -a "$LOGFILE"
		echo "$reverse_ldif_sambaGroupType_2_to_4" | ldapmodify -D "$binddn" -w "$bindpwd" | tee -a "$LOGFILE"
	}
	trap reverse_sambaGroupType_change EXIT

	## now adjust sambaGroupType 2 and 5
	echo "$ldif_sambaGroupType_5_to_4" | ldapmodify -D "$binddn" -w "$bindpwd" | tee -a "$LOGFILE"
	echo "$ldif_sambaGroupType_2_to_4" | ldapmodify -D "$binddn" -w "$bindpwd" | tee -a "$LOGFILE"

	## commit samba3 smb.conf
	mkdir -p /var/lib/samba3/etc/samba
	cat /usr/share/univention-samba4/samba3upgrade/smb.conf.d/* | ucr filter > /var/lib/samba3/etc/samba/smb.conf
	## fix up /var/lib/samba3/smb.conf for samba-tool
	touch /etc/samba/base.conf /etc/samba/installs.conf /etc/samba/printers.conf /etc/samba/shares.conf
	echo -e "[global]\n\trealm = $kerberos_realm" >> /var/lib/samba3/etc/samba/smb.conf

	## move  univention-samba4 default smb.conf out of the way
	mv /etc/samba/smb.conf /var/tmp/univention-samba4_smb.conf
	### run samba-tool domain samba3upgrade
	samba-tool domain samba3upgrade /var/lib/samba3/etc/samba/smb.conf  --libdir /var/lib/samba3 | tee -a "$LOGFILE"
	## move univention-samba4 config back again, overwriting minimal smb.conf created by samba3upgrade
	mv /var/tmp/univention-samba4_smb.conf /etc/samba/smb.conf

	### revert changes for sambaGroupType 5 and 2
	reverse_sambaGroupType_change
	trap - EXIT

	## finally set the Administrator password, which samba3upgrade did not migrate
	samba-tool user setpassword Administrator --newpassword="$adminpw"
fi

if [ ! -d /etc/phpldapadmin ]; then
	mkdir /etc/phpldapadmin
fi
if [ ! -e /etc/phpldapadmin/config.php ]; then
	cp /var/lib/samba/private/phpldapadmin-config.php /etc/phpldapadmin/config.php
fi

### Next adjust OpenLDAP ports before starting Samba4

# Test:
# r 389
# r 7389,389
# r 389,7389
# r 389,7389,8389
# r 7389,389,8389
# r 7389,8389,389
remove_port ()
{
	if [ -n "$1" -a -n "$2" ]; then
		echo "$1" | sed -e "s|^${2},||;s|,${2},|,|;s|,${2}$||;s|^${2}$||"
	fi

}

if [ -n "$slapd_port" ]; then
	univention-config-registry set slapd/port="$(remove_port "$slapd_port" 389)" 2>&1 | tee -a "$LOGFILE"
fi
if [ -n "$slapd_port_ldaps" ]; then
	univention-config-registry set slapd/port/ldaps="$(remove_port "$slapd_port_ldaps" 636)" 2>&1 | tee -a "$LOGFILE"
fi
if [ "$ldap_server_name" = "$hostname.$domainname" ]; then
	univention-config-registry set ldap/server/port="7389" 2>&1 | tee -a "$LOGFILE"
fi
if [ "$ldap_master" = "$hostname.$domainname" ]; then
	univention-config-registry set ldap/master/port="7389" 2>&1 | tee -a "$LOGFILE"
fi

## restart processes with adjusted ports
stop_udm_cli_server
/etc/init.d/slapd restart 2>&1 | tee -a "$LOGFILE"
/etc/init.d/univention-directory-listener restart 2>&1 | tee -a "$LOGFILE"
/etc/init.d/univention-management-console-server restart 2>&1 | tee -a "$LOGFILE"

exit 0
