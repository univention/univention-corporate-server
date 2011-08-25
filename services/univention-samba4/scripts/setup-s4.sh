#!/bin/bash
#
# Copyright 2004-2011 Univention GmbH
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
			help) usage;;
			*) echo "$0: illegal option -- --${OPTARG}"; exit 1;;
		esac;;
		w) if [ -r "$OPTARG" ]; then adminpw="$(< $OPTARG)"; adminpw2="$adminpw"; fi ;;
		W) adminpw2='!unset';;
	esac
done

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

pwfile="/etc/samba4.secret"
if [ -e "$pwfile" ]; then
	pwhistoryfile="$pwfile.SAVE"
	if [ ! -f "$pwhistoryfile" ]; then
		cp -a "$pwfile" "$pwhistoryfile"	# always keep ownership
	else
		cat "$pwfile" >> "$pwhistoryfile"
	fi
	timestamp=$(stat --printf='%y' "$pwfile")
	printf "\t# modification timestamp: $timestamp\n" >> "$pwhistoryfile"
fi
touch "$pwfile"
chmod 600 "$pwfile"
echo -n "$adminpw" > "$pwfile"

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
	univention-config-registry set slapd/port="$(remove_port "$slapd_port" 389)" >>$LOGFILE 2>&1
fi
if [ -n "$slapd_port_ldaps" ]; then
	univention-config-registry set slapd/port/ldaps="$(remove_port "$slapd_port_ldaps" 636)" >>$LOGFILE 2>&1
fi
if [ "$ldap_server_name" = "$hostname.$domainname" ]; then
	univention-config-registry set ldap/server/port="7389" >>$LOGFILE 2>&1
fi
if [ "$ldap_master" = "$hostname.$domainname" ]; then
	univention-config-registry set ldap/master/port="7389" >>$LOGFILE 2>&1
fi

## restart processes with adjusted ports
stop_udm_cli_server
/etc/init.d/slapd restart >>$LOGFILE 2>&1
/etc/init.d/univention-directory-listener restart >>$LOGFILE 2>&1
/etc/init.d/univention-management-console-server restart >>$LOGFILE 2>&1

## Provision Samba4
eval "$(univention-config-registry shell)"

if [ -x /etc/init.d/samba ]; then
	/etc/init.d/samba stop >>$LOGFILE 2>&1
fi
if [ -x /etc/init.d/winbind ]; then
	/etc/init.d/winbind stop >>$LOGFILE 2>&1
fi
univention-config-registry set samba/autostart=no winbind/autostart=no >>$LOGFILE 2>&1

/etc/init.d/heimdal-kdc stop >>$LOGFILE 2>&1
univention-config-registry set kerberos/autostart=no >>$LOGFILE 2>&1

if [ ! -e /usr/modules ]; then
	ln -s /usr/lib /usr/modules		# somehow MODULESDIR is set to /usr/modules in samba4 source despite --enable-fhs
fi

S3_DOMAIN_SID="$(univention-ldapsearch -x objectclass=sambadomain sambaSID | sed -n 's/sambaSID: \(.*\)/\1/p')"

export LDB_MODULES_PATH=/usr/lib/samba/ldb/

# /usr/share/samba/setup/upgradeprovision --full --realm="$kerberos_realm" -s /etc/samba/smb.conf.samba3
/usr/share/samba/setup/provision --realm="$kerberos_realm" --domain="$windows_domain" --domain-sid="$S3_DOMAIN_SID" \
					--function-level=2008_R2 \
					--adminpass="$adminpw" --server-role='domain controller'	\
					--machinepass="$(</etc/machine.secret)" >>$LOGFILE 2>&1
# the code in /usr/share/pyshared/samba/provision.py derives the 'domaindn' from the realm, save it for later use
univention-config-registry set samba4/ldap/base="DC=${kerberos_realm/./,DC=}" >>$LOGFILE 2>&1

if [ ! -d /etc/phpldapadmin ]; then
	mkdir /etc/phpldapadmin
fi
if [ ! -e /etc/phpldapadmin/config.php ]; then
	cp /var/lib/samba/private/phpldapadmin-config.php /etc/phpldapadmin/config.php
fi

## TODO: Join-Script candidate: DNS-Setup
"${SCRIPTDIR}/setup-dns-in-ucsldap.sh" >>$LOGFILE 2>&1

/etc/init.d/samba4 restart >>$LOGFILE 2>&1	# somehow this currently is necessary to avoid 'Failed to listen on 0.0.0.0:445 - NT_STATUS_ADDRESS_ALREADY_ASSOCIATED'

exit 0
