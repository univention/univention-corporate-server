#!/bin/bash
#
# Copyright 2004-2019 Univention GmbH
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
. /usr/share/univention-samba4/lib/all.sh

eval "$(univention-config-registry shell)"

samba_private_dir="/var/lib/samba/private"
samba_sam="$samba_private_dir/sam.ldb"
samba_secrets="$samba_private_dir/secrets.ldb"
SCRIPTDIR=/usr/share/univention-samba4/scripts
LOGFILE="/var/log/univention/samba4-provision.log"

touch $LOGFILE
chmod 600 $LOGFILE

usage(){ echo "$0 [-h|--help]"; exit 1; }

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
			bindpwdfile)
				bindpwdfile="${!OPTIND}"
				OPTIND=$((OPTIND+1))
				;;
			site|site=*)
				## allow "--site=foo" and "--site foo"
				val=${OPTARG#*=}
				if [ "$val" != "$OPTARG" ]; then
					opt=${OPTARG%=$val}
				else
					val="${!OPTIND}"
					opt="${OPTARG}"
					OPTIND=$((OPTIND+1))
				fi
				## store the sitename
				sitename="$val"
				;;
			help)
				usage
				;;
			*)
				echo "Unknown option --${OPTARG}" >&2
				;;
		esac;;
	esac
done

DOMAIN_SID="$(univention-ldapsearch "(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" sambaSID | ldapsearch-wrapper | sed -n 's/sambaSID: \(.*\)/\1/p')"

## helper function
stop_conflicting_services() {
	## stop samba3 services and heimdal-kdc if present
	if [ -x /etc/init.d/samba ]; then
		if [ -n "$(pgrep -f '/usr/sbin/(smbd|nmbd)')" ]; then
			/etc/init.d/samba stop 2>&1 | tee -a "$LOGFILE"
		fi
	fi
	if [ -x /etc/init.d/winbind ]; then
		if [ -n "$(pgrep -xf /usr/sbin/winbindd)" ]; then
			/etc/init.d/winbind stop 2>&1 | tee -a "$LOGFILE"
		fi
	fi
	if [ -x /etc/init.d/heimdal-kdc ]; then
		if [ -n "$(pgrep -f '/usr/lib/heimdal-servers/(kdc|kpasswdd)')" ]; then
			/etc/init.d/heimdal-kdc stop 2>&1 | tee -a "$LOGFILE"
		fi
	fi

	tmp_ucr_key_value_list=()
	if [ "$samba_autostart" != "no" ]; then
		# Bug #43874: samba4 has that idea to divert the univention-service file to "not confuse the admin with a stopped heimdal-kdc", but now we're confusing systemd
		[ -d /run/systemd ] && systemctl disable heimdal-kdc.service || :
		[ -d /run/systemd ] && systemctl mask heimdal-kdc.service || :
			tmp_ucr_key_value_list[0]="samba/autostart=no"
	fi
	if [ "$winbind_autostart" != "no" ]; then
			tmp_ucr_key_value_list[${#tmp_ucr_key_value_list[@]}]="winbind/autostart=no"
	fi
	if [ "$kerberos_autostart" != "no" ]; then
			tmp_ucr_key_value_list[${#tmp_ucr_key_value_list[@]}]="kerberos/autostart=no"
	fi
	if [ -n "$tmp_ucr_key_value_list" ]; then
		univention-config-registry set "${tmp_ucr_key_value_list[@]}" 2>&1 | tee -a "$LOGFILE"
	fi
	unset tmp_ucr_key_value_list
}

set_machine_secret() {
	## 1. store password locally in secrets.ldb
	old_kvno=$(ldbsearch -H "$samba_sam" samAccountName="${hostname}\$" msDS-KeyVersionNumber | sed -n 's/msDS-KeyVersionNumber: \(.*\)/\1/p')
	new_kvno=$(($old_kvno + 1))

	ldbmodify -H "$samba_secrets" <<-%EOF
	dn: flatname=${windows_domain},cn=Primary Domains
	changetype: modify
	replace: secret
	secret:< file:///etc/machine.secret
	-
	replace: msDS-KeyVersionNumber
	msDS-KeyVersionNumber: $new_kvno
	-
	%EOF

	## 2. replace random machine secret in SAM with /etc/machine.secret
	samba-tool user setpassword "${hostname}\$" --newpassword="$(cat /etc/machine.secret)"
}

# Search for Samba 3 DCs
S3_DCS="$(univention-ldapsearch "(&(objectclass=univentionDomainController)(univentionService=Samba 3))" cn | ldapsearch-wrapper | sed -n 's/cn: \(.*\)/\1/p')"
if [ -n "$S3_DCS" ]; then
	## safety belt
	if is_ucr_true samba4/ignore/mixsetup; then
		echo "WARNING: The following Samba 3 domaincontroller have been found:"
		echo "         $S3_DCS"
		echo "         It is not possible to install a samba 4 domaincontroller "
		echo "         into a samba 3 environment. samba4/ignore/mixsetup is true."
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
		bindpwd="$(< /etc/ldap.secret)"
		bindpwdfile="/etc/ldap.secret"
	fi
fi
## store the binddn and bindpwd options in UDM_ARGV
if [ -n "$bindpwdfile" ]; then
	UDM_ARGV=("--binddn" "$binddn" --bindpwdfile "$bindpwdfile")
else
	UDM_ARGV=("--binddn" "$binddn" --bindpwd "$bindpwd")
fi
set -- "${UDM_ARGV[@]}"


## Provision Samba4
stop_conflicting_services

if [ ! -e /usr/modules ]; then
	ln -s /usr/lib /usr/modules		# somehow MODULESDIR is set to /usr/modules in samba4 source despite --enable-fhs
fi

if [ -z "$samba4_function_level" ]; then
	samba4_function_level=2008_R2
	univention-config-registry set samba4/function/level="$samba4_function_level"
fi

provision_is_ok() {
	local client_kvno
	local server_kvno

	if ! [ -r /var/lib/samba/private/secrets.ldb ]; then
		return 1
	fi

	if ! [ -r /var/lib/samba/private/sam.ldb ]; then
		return 1
	fi

	client_kvno=$(ldbsearch -H /var/lib/samba/private/secrets.ldb -b "flatname=$windows_domain,cn=Primary Domains" msDS-KeyVersionNumber 2>&1 /dev/null | sed -n 's/^msDS-KeyVersionNumber: //p')

	server_kvno=$(ldbsearch -H /var/lib/samba/private/sam.ldb "(sAMAccountName=$hostname$)" msDS-KeyVersionNumber 2>&1 /dev/null | sed -n 's/^msDS-KeyVersionNumber: //p')

	if [ "$client_kvno" != "$server_kvno" ]; then
		return 1
	fi
}

skip_reprovision() {
	if [ "$server_role" == "domaincontroller_slave" ]; then
		return 1	## allow reprovision
	fi

	s4connector_dc=$(get_available_s4connector_dc)
	if [ -n "$s4connector_dc" ] && [ "$s4connector_dc" != "$hostname" ]; then
		return 1	## allow reprovision
	fi

	if ! provision_is_ok; then
		return 1	## allow reprovision
	fi

	echo "INFO: This system runs the S4-Connector and the sam.ldb looks functional"
	echo "      skipping re-provision."
}

run_samba_domain_provision() {
	samba-tool domain provision \
	    --realm="$kerberos_realm" \
	    --domain="$windows_domain" \
	    --domain-sid="$DOMAIN_SID" \
	    --function-level="$samba4_function_level" \
	    --server-role='domain controller' \
	    ${sitename:+--site="$sitename"} \
	    --machinepass="$(</etc/machine.secret)" 2>&1 | tee -a "$LOGFILE"

	if ! provision_is_ok; then
		echo "ERROR: Samba4 provision failed, exiting $0"
		exit 1
	fi
}

if [ -z "$S3_DCS" ] \
    || [ -z "$DOMAIN_SID" ] \
    || is_ucr_true samba4/provision/secondary \
    || is_ucr_true samba4/provision/primary
then

	if [ -z "$DOMAIN_SID" ]; then
		# No SID for this windows/domain has been generated
		DOMAIN_SID="$(univention-newsid)"
		cleanup_var_lib_samba
		run_samba_domain_provision
	else
		if ! skip_reprovision; then
			cleanup_var_lib_samba
			run_samba_domain_provision
		fi
	fi

else
	echo "ERROR: Samba/NT (samba3) Domain Controller migration to Samba/AD is not supported any more."
	exit 1
fi

### Next adjust OpenLDAP ports before starting Samba4

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
