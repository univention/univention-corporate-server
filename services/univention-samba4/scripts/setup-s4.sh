#!/bin/bash
#
# Copyright 2004-2017 Univention GmbH
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
. /usr/share/univention-samba4/lib/all.sh

eval "$(univention-config-registry shell)"

samba_private_dir="/var/lib/samba/private"
samba_sam="$samba_private_dir/sam.ldb"
samba_secrets="$samba_private_dir/secrets.ldb"
SCRIPTDIR=/usr/share/univention-samba4/scripts
LOGFILE="/var/log/univention/samba4-provision.log"

touch $LOGFILE
chmod 600 $LOGFILE

usage(){ echo "$0 [-h|--help] [-w <samba4-admin password file>] [-W]"; exit 1; }

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
		w) if [ -r "$OPTARG" ]; then adminpw="$(< $OPTARG)"; adminpw2="$adminpw"; fi ;;
		W) adminpw2='!unset';;
	esac
done

DOMAIN_SID="$(univention-ldapsearch -x "(&(objectclass=sambadomain)(sambaDomainName=$windows_domain))" sambaSID | ldapsearch-wrapper | sed -n 's/sambaSID: \(.*\)/\1/p')"

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
	echo "INFO: Storing /etc/machine.secret in secrets.ldb"
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
S3_DCS="$(univention-ldapsearch -x "(&(objectclass=univentionDomainController)(univentionService=Samba 3))" cn | ldapsearch-wrapper | sed -n 's/cn: \(.*\)/\1/p')"
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
stop_conflicting_services

if [ ! -e /usr/modules ]; then
	ln -s /usr/lib /usr/modules		# somehow MODULESDIR is set to /usr/modules in samba4 source despite --enable-fhs
fi

if [ -z "$samba4_function_level" ]; then
	samba4_function_level=2008_R2
	univention-config-registry set samba4/function/level="$samba4_function_level"
fi

kinit_with_samba_secret_works() {
	local t
	local rc

	for t in $(seq 5); do
		sleep 1
		kinit --password-file=<(ldbsearch -H "$samba_secrets" "(&(objectClass=primaryDomain)(sAMAccountName=${hostname^^}$))" secret  | sed -n 's/^secret: //p') ${hostname^^}$
		rc=$?
		if [ "$rc" -eq 0 ]; then
			kdestroy
			return 0
		fi
	done
	return "$rc"
}

kinit_with_keytab_works() {
	local t
	local rc

	for t in $(seq 3); do
		sleep 1
		kinit -t /etc/krb5.keytab ${hostname^^}$
		rc=$?
		if [ "$rc" -eq 0 ]; then
			kdestroy
			return 0
		fi
	done
	return "$rc"
}

check_samba_secret_against_samdb() {
	local secret
	local count
	local rc

	echo "INFO: Checking Samba machine password"
	eval "$(ucr shell hostname)"
	secret=$(ldbsearch -H "$samba_secrets" "(&(objectClass=primaryDomain)(sAMAccountName=${hostname^^}$))" secret  | sed -n 's/^secret: //p')
	if [ -z "$secret" ]; then
		echo "INFO: No machine password stored in Samba"
		return 1
	fi

	count=$(pgrep -cx samba)
	if [ "$count" -eq 0 ]; then
		echo "INFO: Temporarily starting Samba for this check"
		/etc/init.d/samba start
		sleep 3
	fi

	if kinit_with_samba_secret_works; then
		echo "INFO: The machine password stored in Samba works with kinit"
		check_krb5_keytab_against_samdb
		rc=$?
	else
		echo "INFO: The machine password stored in Samba doesn't work with kinit"
		rc=1
	fi
	if [ "$count" -eq 0 ]; then
		echo "INFO: Stopping Samba again"
		/etc/init.d/samba stop
	fi
	return ${rc:-0}
}

check_krb5_keytab_against_samdb() {
	local count
	local rc

	echo "INFO: Checking if krb5.keytab works with kinit"
	count=$(pgrep -cx samba)
	if [ "$count" -eq 0 ]; then
		echo "INFO: Temporarily starting Samba for this check"
		/etc/init.d/samba start
		sleep 3
	fi
	if ! kinit_with_keytab_works; then
		echo "INFO: The krb5.keytab doesn't work with kinit"
		echo "INFO: Re-creating keytab from secrets.ldb"
		/usr/share/univention-samba4/scripts/create-keytab.sh
		if ! kinit_with_keytab_works; then
			echo "INFO: The krb5.keytab still doesn't work with kinit"
			rc=1
		else
			echo "INFO: Ok, now the krb5.keytab works with kinit"
		fi
	else
		echo "INFO: The krb5.keytab works with kinit"
	fi
	if [ "$count" -eq 0 ]; then
		echo "INFO: Stopping Samba again"
		/etc/init.d/samba stop
	fi
	return ${rc:-0}
}

assert_that_machine_secret_works_against_samdb() {
	local secret

	eval "$(ucr shell hostname)"
	secret=$(ldbsearch -H "$samba_secrets" "(&(objectClass=primaryDomain)(sAMAccountName=${hostname^^}$))" secret  | sed -n 's/^secret: //p')
	if [ -z "$secret" ]; then
		return 1
	fi
	if [ "$(</etc/machine.secret)" != "$secret" ]; then
		echo "INFO: /etc/machine.secret not in secrets.ldb"
		set_machine_secret
	fi
}

machine_account_in_samdb() {
	local server_kvno

	if ! [ -r "$samba_secrets" ]; then
		return 1
	fi

	if ! [ -r "$samba_sam" ]; then
		return 1
	fi

	echo "INFO: Looking for Samba machine account in sam.ldb"

	eval "$(ucr shell hostname)"
	server_kvno=$(ldbsearch -H "$samba_sam" "(sAMAccountName=$hostname$)" msDS-KeyVersionNumber 2>&1 /dev/null | sed -n 's/^msDS-KeyVersionNumber: //p')
	if [ -z "$server_kvno" ]; then
		return 1
	fi
}

secrets_are_ok() {
	if ! check_samba_secret_against_samdb; then
		return 1
	fi

	assert_that_machine_secret_works_against_samdb
}

skip_reprovision() {
	if [ "$server_role" == "domaincontroller_slave" ]; then
		return 1	## allow reprovision
	fi

	s4connector_dc=$(get_available_s4connector_dc)
	if [ -n "$s4connector_dc" ] && [ "$s4connector_dc" != "$hostname" ]; then
		return 1	## allow reprovision
	fi

	echo "INFO: Checking if a re-provision is really necessary or if it's dangerous"
	if machine_account_in_samdb; then
		if secrets_are_ok; then
			echo "INFO: This system runs the S4-Connector and the sam.ldb looks functional, skipping re-provision."
			return 0
		fi
		if is_ucr_true connector/s4/mapping/sid_to_ucs; then
			echo "ERROR: Aborting re-provision, there seem to be objectSIDs in sam.ldb which we should preserve."
			## Hard exit.
			exit 1
		fi
	fi

	echo "INFO: Checks ok, re-provision can continue"
	return 1	## allow reprovision
}

run_samba_domain_provision() {
	samba-tool domain provision \
	    --realm="$kerberos_realm" \
	    --domain="$windows_domain" \
	    --domain-sid="$DOMAIN_SID" \
	    --function-level="$samba4_function_level" \
	    --adminpass="$adminpw" \
	    --server-role='domain controller' \
	    ${sitename:+--site="$sitename"} \
	    --machinepass="$(</etc/machine.secret)" 2>&1 | tee -a "$LOGFILE"

	if ! machine_account_in_samdb; then
		echo "Samba4 provision failed, exiting $0"
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
	## Before starting the upgrade check for Samba accounts that are not POSIX accounts:
	non_posix_sambaSamAccount_dns=$(univention-ldapsearch -xLLL "(&(objectClass=sambaSamAccount)(!(objectClass=posixAccount)))" dn | ldapsearch-wrapper | sed -n 's/^dn: \(.*\)/\1/p')
	if [ -n "$non_posix_sambaSamAccount_dns" ]; then
		echo "ERROR: Found Samba accounts in LDAP that are not POSIX accounts, please remove these before updating to Samba 4" >&2
		echo "$non_posix_sambaSamAccount_dns" | while read dn; do
			echo "DN: $dn" >&2
		done
		exit 1
	fi

	## Before starting the upgrade check for group names colliding with user names
	uid_ldap_check_function() {
		local filter="$1"
		collision=$(univention-ldapsearch -xLLL "(&(objectClass=posixAccount)(|$filter))" uid | ldapsearch-wrapper | sed -n 's/^uid: \(.*\)/\1/p')
		if [ -n "$collision" ]; then
			echo "ERROR: Group names and user names must be unique, please rename these before updating to Samba 4" >&2
			echo "The following user names are also present as group names:" >&2
			echo "$collision" >&2
			exit 1
		fi
	}

	filter_maxsize=10000	## approximate limit for the LDAP filter string size
	while read name; do
		if [ "$((${#filter} + ${#name}))" -lt "$filter_maxsize" ]; then
			filter="$filter(uid=$name)"
		else
			uid_ldap_check_function "$filter"
			filter="(uid=$name)"
		fi
	done < <(univention-ldapsearch -xLLL "(objectClass=posixGroup)" cn | ldapsearch-wrapper | sed -n 's/^cn: \(.*\)/\1/p')
	if [ -n "$filter" ]; then
		uid_ldap_check_function "$filter"
	fi

	## Preparations for the samba3update:
	extract_binddn_and_bindpwd_from_args "$@"
	groups=("Windows Hosts" "DC Backup Hosts" "DC Slave Hosts" "Computers" "Power Users")
	for group in "${groups[@]}"; do
		record=$(univention-ldapsearch -xLLL "(&(cn=$group)(objectClass=univentionGroup))" dn description | ldapsearch-wrapper)
		description=$(echo "$record" | sed -n 's/^description: \(.*\)/\1/p')
		if [ -z "$description" ]; then
			dn=$(echo "$record" | sed -n 's/^dn: \(.*\)/\1/p')
			univention-directory-manager groups/group modify "$@" --dn "$dn" --set description="$group"
		fi
	done

	## commit samba3 smb.conf
	mkdir -p /var/lib/samba3/etc/samba
	cat /usr/share/univention-samba4/samba3upgrade/smb.conf.d/* | ucr filter > /var/lib/samba3/etc/samba/smb.conf
	## fix up /var/lib/samba3/smb.conf for samba-tool
	touch /etc/samba/base.conf /etc/samba/installs.conf /etc/samba/printers.conf /etc/samba/shares.conf

	# The upgrade tool uses /var/lib/samba3/ for these files
	#  https://forge.univention.org/bugzilla/show_bug.cgi?id=33251
	for tdbfile in schannel_store.tdb idmap2.tdb passdb.tdb secrets.tdb; do
		if [ -e /var/lib/samba3/private/$tdbfile -a ! -e /var/lib/samba3/$tdbfile ]; then
			cp /var/lib/samba3/private/$tdbfile /var/lib/samba3/$tdbfile
		fi
	done

	## move  univention-samba4 default smb.conf out of the way
	mv /etc/samba/smb.conf /var/tmp/univention-samba4_smb.conf
	### run samba-tool domain samba3upgrade
	samba-tool domain classicupgrade /var/lib/samba3/etc/samba/smb.conf --dbdir /var/lib/samba3 | tee -a "$LOGFILE"
	## move univention-samba4 config back again, overwriting minimal smb.conf created by samba3upgrade
	mv /var/tmp/univention-samba4_smb.conf /etc/samba/smb.conf

	## set the samba4 machine account secret in secrets.ldb to /etc/machine.secret
	set_machine_secret

	## finally set the Administrator password, which samba3upgrade did not migrate
	samba-tool user setpassword Administrator --newpassword="$adminpw"
fi

if [ ! -d /etc/phpldapadmin ]; then
	mkdir /etc/phpldapadmin
fi
if [ ! -e /etc/phpldapadmin/config.php ]; then
	cp "$samba_private_dir/phpldapadmin-config.php" /etc/phpldapadmin/config.php
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
