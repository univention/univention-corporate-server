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
[ -n "$hostname" ] && univention-config-registry set hostname="$hostname"
[ -n "$hostname" ] && hostname -F /etc/hostname

# set domainame
domainname=$(get_profile_var "domainname")
[ -n "$domainname" ] && univention-config-registry set domainname="$domainname"
# set ldap/basee
ldap_base=$(get_profile_var "ldap/base")
[ -n "$ldap_base" ] && univention-config-registry set ldap/base="$ldap_base"
# set windows domain
windows_domain=$(get_profile_var "windows/domain")
[ -n "$windows_domain" ] && univention-config-registry set windows/domain="$windows_domain"

eval "$(univention-config-registry shell)"

# The ldap server join script must create the Administrator account
if [ "$server_role" = "domaincontroller_master" ]; then
	p=$(get_profile_var "root_password")
	if [ -n "$p" ]; then
		if [ ! -e /var/lib/univention-ldap ]; then
			mkdir -p /var/lib/univention-ldap
		fi
		echo -n "$p" >/var/lib/univention-ldap/root.secret
		chmod 600 /var/lib/univention-ldap/root.secret
	fi
	unset p
fi
# set root password
/usr/lib/univention-system-setup/scripts/basis/18root_password

if [ "$server_role" = "domaincontroller_master" ]; then
      univention-config-registry set ldap/server/name="$hostname.$domainname" \
      						ldap/master="$hostname.$domainname" \
      						kerberos/adminserver="$hostname.$domainname"
fi

# do not allow the UMC or webserver to be restarted
/usr/share/univention-updater/disable-apache2-umc

# cleanup secrets
echo -n "$(makepasswd)" > /etc/ldap.secret
echo -n "$(makepasswd)" > /etc/ldap-backup.secret
rm -f /etc/machine.secret

echo "Starting re-configuration of SSL"
# Re-create SSL certificates even if the admin did'nt change all variables
/usr/lib/univention-system-setup/scripts/ssl/10ssl --force-recreate

univention-certificate new -name "$hostname.$domainname"
ln -sf "/etc/univention/ssl/$hostname.$domainname" "/etc/univention/ssl/$hostname"

# Call scripts which won't be handled by join scripts
# keyboard, language and timezone
echo "Starting re-configuration of locales"
run-parts /usr/lib/univention-system-setup/scripts/keyboard/
run-parts /usr/lib/univention-system-setup/scripts/language/
run-parts /usr/lib/univention-system-setup/scripts/defaultlocale/
run-parts /usr/lib/univention-system-setup/scripts/timezone/
run-parts /usr/lib/univention-system-setup/scripts/modules/

# Do network stuff
echo "Starting re-configuration of network"
run-parts -a --network-only -- /usr/lib/univention-system-setup/scripts/net/

# Install selected software
echo "Starting re-configuration of software packages"
run-parts /usr/lib/univention-system-setup/scripts/software/

eval "$(univention-config-registry shell)"

info_header "$(basename $0)" "$(gettext "Domain join")"

# see how many join scripts we need to execute
joinScripts=(/usr/lib/univention-install/*.inst)
nJoinSteps=$((${#joinScripts[@]}+1))
progress_steps $nJoinSteps
progress_msg "$(gettext "Preparing domain join")"
progress_next_step

# Call join
if [ -d /var/lib/univention-ldap/ldap ]; then
	rm -f /var/lib/univention-ldap/ldap/*
	univention-config-registry commit /var/lib/univention-ldap/ldap/DB_CONFIG
fi
(
	if [ "$server_role" = "domaincontroller_master" ]; then
		mkdir -p /var/univention-join/ /usr/share/univention-join/
		rm -f /var/univention-join/joined /var/univention-join/status
		touch /var/univention-join/joined /var/univention-join/status
		ln -sf /var/univention-join/joined /usr/share/univention-join/.joined
		ln -sf /var/univention-join/status /usr/lib/univention-install/.index.txt

		for i in /usr/lib/univention-install/*.inst; do
			echo "Configure $i"
			$i
		done
	else
		if [ -n "$dcaccount" -a -n "$password_file" ]; then
			# Copy to a temporary password file, because univention-join
			# will copy the file to the same directory on the master
			# with the given user credentials. This won't work.
			pwd_file="$(mktemp)"
			cp "$password_file" "$pwd_file"
			/usr/share/univention-join/univention-join -dcaccount "$dcaccount" -dcpwd "$pwd_file"
			rm -f "$pwd_file"
		fi
	fi
) | (
	# parse the output for lines "^Configure .*" which indicate that a join
	# script is being executed
	while read line; do
		if [ "${line#Configure }" != "$line" ]; then
			# found line starting with "Configure " ... parse the join script name
			joinScript=${line#Configure }
			joinScript=${joinScript%%.inst*}
			progress_msg "$(gettext "Configure") $(basename $joinScript)"
			progress_next_step
		fi
		echo "$line"
	done
)
progress_next_step $nJoinSteps

rm -f /var/lib/univention-ldap/root.secret

# allow execution of servers again and perform a restart
/usr/share/univention-updater/enable-apache2-umc

exit 0

