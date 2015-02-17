#!/bin/bash
#
# Univention System Setup
#  Appliance mode
#
# Copyright 2011-2015 Univention GmbH
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

# do not allow the UMC or webserver to be restarted
/usr/share/univention-updater/disable-apache2-umc

# Re-create sources.list files before installing the role packages
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=28089
ucr commit /etc/apt/sources.list.d/*
apt-get update

# Install the server package
/usr/lib/univention-system-setup/scripts/05_role/10role

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
else
	univention-config-registry unset ldap/translogfile
fi
# set root password
/usr/lib/univention-system-setup/scripts/10_basis/18root_password

# set init-script configuration
/usr/lib/univention-system-setup/scripts/10_basis/20initscripts

if [ "$server_role" = "domaincontroller_master" ]; then
	realm="$(echo $domainname | tr "[:lower:]" "[:upper:]")"
	univention-config-registry set ldap/server/name="$hostname.$domainname" \
						ldap/master="$hostname.$domainname" \
						kerberos/adminserver="$hostname.$domainname" \
						kerberos/realm="$realm" \
						mail/alias/root="systemmail@$hostname.$domainname"

fi

# cleanup secrets
if [ "$server_role" = "domaincontroller_master" ]; then
	. /usr/share/univention-lib/base.sh
	echo -n "$(create_machine_password)" > /etc/ldap.secret
	echo -n "$(create_machine_password)" > /etc/ldap-backup.secret
else
	rm -f /etc/ldap.secret /etc/ldap-backup.secret
fi
rm -f /etc/machine.secret

if [ "$system_setup_boot_installer" != "true" ]; then
	# Re-create ssh keys
	ssh_installation_status="$(dpkg --get-selections openssh-server 2>/dev/null | awk '{print $2}')"
	if [ "$ssh_installation_status" = "install" ]; then
		rm -f /etc/ssh/ssh_host_*
		DEBIAN_FRONTEND=noninteractive dpkg-reconfigure openssh-server
	fi

	test -x /usr/share/univention-mail-postfix/create-dh-parameter-files.sh && \
		/usr/share/univention-mail-postfix/create-dh-parameter-files.sh
fi


# Call scripts which won't be handled by join scripts
# keyboard, language and timezone
echo "Starting re-configuration of locales"
run-parts /usr/lib/univention-system-setup/scripts/15_keyboard/
run-parts /usr/lib/univention-system-setup/scripts/20_language/
run-parts /usr/lib/univention-system-setup/scripts/25_defaultlocale/

# Do network stuff
echo "Starting re-configuration of network"
run-parts -a --network-only -a --appliance-mode -- /usr/lib/univention-system-setup/scripts/30_net/

run-parts /usr/lib/univention-system-setup/scripts/35_timezone/

# Re-create SSL certificates on DC Master even if the admin didn't change all variables
# otherwise a lot of appliances will have the same SSL certificate secret
if [ "$server_role" = "domaincontroller_master" ]; then
	echo "Starting re-configuration of SSL"
	/usr/lib/univention-system-setup/scripts/40_ssl/10ssl --force-recreate
fi

univention-certificate new -name "$hostname.$domainname"
ln -sf "/etc/univention/ssl/$hostname.$domainname" "/etc/univention/ssl/$hostname"

run-parts /usr/lib/univention-system-setup/scripts/45_modules/

# Re-create sources.list files
ucr commit /etc/apt/sources.list.d/*

# Install selected software
echo "Starting re-configuration of software packages"
run-parts /usr/lib/univention-system-setup/scripts/50_software/

eval "$(univention-config-registry shell)"

is_profile_var_true "start/join"
if [ $? -ne 1 ]; then
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
				# with the given user credentials. This will not work.
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
			if [ "${line#* Message:  }" != "$line" ]; then
				# found line indicating join failed. output
				progress_join_error "${line#* Message:  }"
			fi
			echo "$line"
		done
	)
	progress_next_step $nJoinSteps
fi

# Run certain scripts that should be executed after univention-join
# (e.g. univention-upgrade which would require testing new installations
# each time we release an update)
echo "Running postjoin scripts"
run-parts /usr/lib/univention-system-setup/scripts/90_postjoin/

# Cleanup
rm -f /var/lib/univention-ldap/root.secret

# Rewrite apache2 default sites, workaround for
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=27597
ucr commit \
	/var/www/ucs-overview/entries.json \
	/var/www/ucs-overview/languages.json

# Restart NSCD
test -x /etc/init.d/nscd && invoke-rc.d nscd restart

# Start atd as the appliance cleanup script is started as at job
test -x /etc/init.d/atd && invoke-rc.d atd start

# Commit PAM files, workaround for
#   https://forge.univention.org/bugzilla/show_bug.cgi?id=26846
#   https://forge.univention.org/bugzilla/show_bug.cgi?id=27536
ucr commit /etc/pam.d/*

# Removed system setup login message
ucr set system/setup/showloginmessage=false

# allow a restart of server components without actually restarting them
/usr/share/univention-updater/enable-apache2-umc --no-restart

# call appliance hooks
if [ -d /usr/lib/univention-system-setup/appliance-hooks.d ]; then
	run-parts /usr/lib/univention-system-setup/appliance-hooks.d
fi

exit 0

