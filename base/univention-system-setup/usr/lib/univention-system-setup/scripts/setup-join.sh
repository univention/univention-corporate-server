#!/bin/bash
#
# Univention System Setup
#  Appliance mode
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


password_file=""
dcaccount=""
dcname=""
runcleanup=true

while [ "$#" -gt 0 ]; do
	case $1 in
		--dcname)
			dcname="$2"
			shift 2
			;;
		--dcaccount)
			dcaccount="$2"
			shift 2
			;;
		--password_file)
			password_file="$2"
			shift 2
			;;
		--do_not_run_cleanup)
			runcleanup=false
			shift 1
			;;
		--run_cleanup_as_atjob)
			runcleanup=atjob
			shift 1
			;;
		--help)
			echo "Usage: $0 [--dcname <dcname>] [--dcaccount <dcaccount> --password_file <passwordfile>] [--do_not_run_cleanup]"
			exit 1
			;;
		*)
			echo "WARNING: Unknown parameter $1"
			echo "Usage: $0 [--dcname <dcname>] [--dcaccount <dcaccount> --password_file <passwordfile>] [--do_not_run_cleanup]"
			exit 1
	esac
done

SETUP_LOG="/var/log/univention/setup.log"
JOIN_LOG="/var/log/univention/join.log"

. /usr/lib/univention-system-setup/scripts/setup_utils.sh

echo "Reset UCR variables"
run-parts -v /usr/lib/univention-system-setup/scripts/00_system_setup

echo "no-ldap" > /var/run/univention-system-setup.ldap

# Call scripts which won't be handled by join scripts
# keyboard, language and timezone
echo "Starting re-configuration of locales"
run-parts -v /usr/lib/univention-system-setup/scripts/15_keyboard
run-parts -v /usr/lib/univention-system-setup/scripts/20_language
run-parts -v /usr/lib/univention-system-setup/scripts/25_defaultlocale

# Do not allow the UMC to be restarted, webserver is OK, but
# make sure the webserver uses the same certificates during setup.
# The variables are removed in during cleanup
/usr/share/univention-updater/disable-apache2-umc --exclude-apache
# Do not change apache certificate when installing via debian installer
eval "$(univention-config-registry shell)"
if [ "$system_setup_boot_installer" != "true" ]; then
	certificate="$(mktemp -p /var/cache/univention-system-setup)"
	key="$(mktemp -p /var/cache/univention-system-setup)"
	ca="$(mktemp -p /var/cache/univention-system-setup)"
	cp "/etc/univention/ssl/$(ucr get hostname).$(ucr get domainname)/cert.pem" "$certificate"
	cp "/etc/univention/ssl/$(ucr get hostname).$(ucr get domainname)/private.key" "$key"
	cp "/etc/univention/ssl/ucsCA/CAcert.pem" "$ca"
	ucr set \
		apache2/ssl/certificate="$certificate" \
		apache2/ssl/key="$key" \
		apache2/ssl/ca="$ca"
fi

# Re-create the system uuid
/usr/lib/univention-system-setup/scripts/10_basis/50uuid --force-recreate

# Re-create sources.list files before installing the role packages
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=28089
ucr commit /etc/apt/sources.list.d/*
apt-get update

# Bug #45896: Make the UCS 4.3 DVD trusted
sed -i 's|deb cdrom:\[UCS |deb \[trusted=yes\] cdrom:\[UCS |' /etc/apt/sources.list

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

info_header "create-ssh-keys" "$(gettext "Recreating SSH keys")"
progress_msg "$(gettext "This might take a moment...")"
progress_steps 10

# cleanup secrets
if [ "$server_role" = "domaincontroller_master" ]; then
	. /usr/share/univention-lib/base.sh
	echo -n "$(create_machine_password)" > /etc/ldap.secret
	echo -n "$(create_machine_password)" > /etc/ldap-backup.secret
else
	rm -f /etc/ldap.secret /etc/ldap-backup.secret
fi
rm -f /etc/machine.secret
progress_next_step 1

if [ "$system_setup_boot_installer" != "true" ]; then
	# Re-create ssh keys
	ssh_installation_status="$(dpkg --get-selections openssh-server 2>/dev/null | awk '{print $2}')"
	if [ "$ssh_installation_status" = "install" ]; then
		rm -f /etc/ssh/ssh_host_*
		DEBIAN_FRONTEND=noninteractive dpkg-reconfigure openssh-server
	fi
	progress_next_step 3

	if [ -x /usr/share/univention-mail-postfix/create-dh-parameter-files.sh ]; then
		DH_LOG_FILE="/var/log/univention/dh-parameter-files-creation.log"
		touch "$DH_LOG_FILE"
		chmod 640 "$DH_LOG_FILE"
		/usr/share/univention-mail-postfix/create-dh-parameter-files.sh >> "$DH_LOG_FILE" 2>&1 &
	fi

	progress_next_step 15
fi

# Do network stuff
echo "Starting re-configuration of network"
run-parts -v -a --network-only -a --appliance-mode -- /usr/lib/univention-system-setup/scripts/30_net

run-parts -v /usr/lib/univention-system-setup/scripts/35_timezone

# Re-create SSL certificates on DC Master even if the admin didn't change all variables
# otherwise a lot of appliances will have the same SSL certificate secret
if [ "$server_role" = "domaincontroller_master" ]; then
	echo "Starting re-configuration of SSL"
	# Recreate SSL CA
	/usr/lib/univention-system-setup/scripts/40_ssl/10ssl --force-recreate

	# Create initial certificate for master
	univention-certificate new -name "$hostname.$domainname"
	ln -snf "$hostname.$domainname" "/etc/univention/ssl/$hostname"
	
	invoke-rc.d apache2 restart
else
	# Other system roles require the certificate creation here only if they to not join
	# Create them in any case, as apache2 will not start otherwise
	# These should be treated as dummy certificates,
	# as a new certificate will be created and downloaded when joining a UCS domain
	. /usr/share/univention-ssl/make-certificates.sh
	cd "$SSLBASE"
	echo "Creating base ssl certificate"
	fqdn="$hostname.$domainname"
	gencert "$SSLBASE/$fqdn" "$fqdn" "$days"
	if getent group "DC Backup Hosts" 2>&1 >/dev/null
	then
		chgrp -R "DC Backup Hosts" "$SSLBASE/$name"
		chmod -R g+rX "$SSLBASE/$name"
	fi
	ln -snf "$fqdn" "/etc/univention/ssl/$hostname"
fi

run-parts -v /usr/lib/univention-system-setup/scripts/45_modules

# Re-create sources.list files
ucr commit /etc/apt/sources.list.d/*

# Install selected software
echo "Starting re-configuration of software packages"
run-parts -v /usr/lib/univention-system-setup/scripts/50_software

eval "$(univention-config-registry shell)"

is_profile_var_true "start/join"
if [ $? -ne 1 ]; then
	info_header "domain-join" "$(gettext "Domain setup (this might take a while)")"

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
				echo "Configure $(basename "$i") $(LC_ALL=C date)" | tee -a "$JOIN_LOG"
				# test
				$i 2>&1 | tee -a "$JOIN_LOG"
			done
		else
			if [ -n "$dcaccount" -a -n "$password_file" ]; then
				# Copy to a temporary password file, because univention-join
				# will copy the file to the same directory on the master
				# with the given user credentials. This will not work.
				pwd_file="$(mktemp)"
				cp "$password_file" "$pwd_file"
				if [ -n "$dcname" ]; then
					/usr/share/univention-join/univention-join -dcname "$dcname" -dcaccount "$dcaccount" -dcpwd "$pwd_file"
				else
					/usr/share/univention-join/univention-join -dcaccount "$dcaccount" -dcpwd "$pwd_file"
				fi
				rm -f "$pwd_file"
			fi
		fi
	) 2>&1 | (
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
			if [ "${line#__JOINERR__}" != "$line" ]; then
				# found line indicating join failed. output
				echo "$line"
				continue
			fi
			if [ "${line#* Message:  }" != "$line" ]; then
				# found line indicating join failed. output
				progress_join_error "${line#* Message:  }"
				continue
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
run-parts -v /usr/lib/univention-system-setup/scripts/90_postjoin

# Cleanup
rm -f /var/lib/univention-ldap/root.secret

# Rewrite apache2 default sites, workaround for
#  https://forge.univention.org/bugzilla/show_bug.cgi?id=27597
ucr commit \
	/var/www/univention/meta.json \
	/var/www/univention/languages.json

# Restart NSCD
service restart nscd

# Start atd as the appliance cleanup script is started as at job
service start atd

# Commit PAM files, workaround for
#   https://forge.univention.org/bugzilla/show_bug.cgi?id=26846
#   https://forge.univention.org/bugzilla/show_bug.cgi?id=27536
ucr commit /etc/pam.d/*

# Removed system setup login message
ucr set system/setup/showloginmessage=false

# call appliance hooks
info_header "appliance-hooks.d" "$(gettext "Running appliance scripts")"
/usr/lib/univention-system-setup/scripts/appliance_hooks.py

# allow a restart of server components without actually restarting them
/usr/share/univention-updater/enable-apache2-umc --no-restart

if [ "$runcleanup" = true ]; then
	echo "=== Running cleanup scripts $(date --rfc-3339=seconds)"
	/usr/lib/univention-system-setup/scripts/cleanup.py
elif [ "$runcleanup" = atjob ]; then
	# run cleanup scripts via at with a delay of 1sec
	echo "=== Cleanup scripts will be run as at job $(date --rfc-3339=seconds)"
	echo "sleep 1; /usr/lib/univention-system-setup/scripts/cleanup.py >> $SETUP_LOG 2>&1" | at now
else
	echo "== Cleanup scripts will not be run now, option --do_not_run_cleanup was given $(date --rfc-3339=seconds)"
fi

exit 0

