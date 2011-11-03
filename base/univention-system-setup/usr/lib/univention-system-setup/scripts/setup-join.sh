#!/bin/bash
#
# Univention System Setup
#  Appliance mode
#
# Copyright 2011 Univention GmbH
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


password_file=""
dcaccount=""

while [ "$#" -gt 0 ]; do
    case $1 in
        --dcaccount)
			dcaccount="$2"
            shift 2
            ;;
        --password_file)
			password_file="$2"
            shift 2
            ;;
		--help)
            echo "Usage: $0 [--dcaccount <dcaccount> --password_file <passwordfile>]"
			exit 1
            ;;
        *)
            echo "WARNING: Unknown parameter $1"
            echo "Usage: $0 [--dcaccount <dcaccount> --password_file <passwordfile>]"
			exit 1
    esac
done

SETUP_LOG="/var/log/univention/setup.log"

. /usr/lib/univention-system-setup/scripts/setup_utils.sh

echo "no-ldap" > /var/run/univention-system-setup.ldap


echo "Starting re-configuration of basic settings"
# set hostname
hostname=$(get_profile_var "hostname")
[ -n "$hostname" ] && univention-config-registry set hostname="$hostname" >>$SETUP_LOG 2>&1
# set domainame
domainname=$(get_profile_var "domainname")
[ -n "$domainname" ] && univention-config-registry set domainname="$domainname" >>$SETUP_LOG 2>&1
# set ldap/basee
ldap_base=$(get_profile_var "ldap/base")
[ -n "$ldap_base" ] && univention-config-registry set ldap/base="$ldap_base" >>$SETUP_LOG 2>&1
# set windows domain
windows_domain=$(get_profile_var "windows/domain")
[ -n "$windows_domain" ] && univention-config-registry set windows/domain="$windows_domain" >>$SETUP_LOG 2>&1
# set root password
/usr/lib/univention-system-setup/scripts/basis/18root_password >>$SETUP_LOG 2>&1

eval "$(univention-config-registry shell)"

if [ "$server_role" = "domaincontroller_master" ]; then
      univention-config-registry set ldap/server/name="$hostname.$domainname" \
      						ldap/master="$hostname.$domainname" \
      						kerberos/adminserver="$hostname.$domainname"
fi

# cleanup secrets
echo -n "$(makepasswd)" > /etc/ldap.secret
echo -n "$(makepasswd)" > /etc/ldap-backup.secret
rm -f /etc/machine.secret

echo "Starting re-configuration of SSL"
# Re-create SSL certificates even if the admin did'nt change all variables
/usr/lib/univention-system-setup/scripts/ssl/10ssl --force-recreate >>$SETUP_LOG 2>&1

univention-certificate new -name "$hostname.$domainname" >>$SETUP_LOG 2>&1
ln -sf "/etc/univention/ssl/$hostname.$domainname" "/etc/univention/ssl/$hostname" >>$SETUP_LOG 2>&1

# Call scripts which won't be handled by join scripts
# keyboard, language and timezone
echo "Starting re-configuration of locales"
run-parts /usr/lib/univention-system-setup/scripts/keyboard/ >>$SETUP_LOG 2>&1
run-parts /usr/lib/univention-system-setup/scripts/language/ >>$SETUP_LOG 2>&1
run-parts /usr/lib/univention-system-setup/scripts/timezone/ >>$SETUP_LOG 2>&1
run-parts /usr/lib/univention-system-setup/scripts/modules/ >>$SETUP_LOG 2>&1

# Do network stuff
echo "Starting re-configuration of network"
run-parts -a --network-only -- /usr/lib/univention-system-setup/scripts/net/ >>$SETUP_LOG 2>&1

# Install selected software
echo "Starting re-configuration of software packages"
run-parts /usr/lib/univention-system-setup/scripts/software/ >>$SETUP_LOG 2>&1

eval "$(univention-config-registry shell)"

echo -e "\nStarting domain join\n"
# Call join
if [ -d /var/lib/univention-ldap/ldap ]; then
	rm -f /var/lib/univention-ldap/ldap/*
	univention-config-registry commit /var/lib/univention-ldap/ldap/DB_CONFIG >>$SETUP_LOG 2>&1
fi

if [ "$server_role" = "domaincontroller_master" ]; then
	mkdir -p /var/univention-join/ /usr/share/univention-join/
	rm -f /var/univention-join/joined /var/univention-join/status
	touch /var/univention-join/joined /var/univention-join/status
	ln -sf /var/univention-join/joined /usr/share/univention-join/.joined
	ln -sf /var/univention-join/status /usr/lib/univention-install/.index.txt

	for i in /usr/lib/univention-install/*.inst; do
		echo "Configure $(basename $i)"
		echo "Configure $(basename $i)" >>$SETUP_LOG 2>&1
		$i >>$SETUP_LOG 2>&1
	done
else
	if [ -n "$dcaccount" -a -n "$password_file" ]; then
		/usr/share/univention-join/univention-join -dcaccount $domain_controller_account -dcpwd "$password_file" >>$SETUP_LOG 2>&1
	fi
fi

exit 0
