#!/bin/sh
#
# Univention Installer
#  join computer
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

. /tmp/installation_profile

if [ -n "$system_role" ]; then
	export server_role="$system_role"
fi

# copy installation profile
cat /tmp/installation_profile | sed -e "s|root_password=.*|#root_password=''|" | sed -e "s|domain_controller_password=.*|#domain_controller_password=''|" > /instmnt/etc/univention/installation_profile

sync

cat >>/instmnt/join.sh <<__EOT__

if [ -d /var/lib/univention-ldap/ldap ]; then
	rm -f /var/lib/univention-ldap/ldap/*
fi

if [ "$server_role" != "domaincontroller_master" ] && [ -n "$domain_controller_account" -a -n "$domain_controller_password" ]; then
	if [ -n "$interfaces_eth0_type" ] && [ "$interfaces_eth0_type" = "dynamic" -o "$interfaces_eth0_type" = "dhcp" ]; then
		dhclient eth0
	fi
	if [ -z "$auto_join" ] || [ "$auto_join" != "FALSE" -a "$auto_join" != "false" -a "$auto_join" != "False" ]; then
		pwd_file=\`mktemp\`
		chmod 600 \$pwd_file
		echo "$domain_controller_password" >>\$pwd_file
		if [ -n "$domain_controller" ]; then
			/usr/share/univention-join/univention-join -dcname $domain_controller -dcaccount $domain_controller_account -dcpwd \$pwd_file
		else
			/usr/share/univention-join/univention-join -dcaccount $domain_controller_account -dcpwd \$pwd_file
		fi
	fi
fi


if [ "$server_role" = "domaincontroller_master" ]; then
	mkdir -p /usr/share/univention-join/
	touch /usr/share/univention-join/.joined
	for i in /usr/lib/univention-install/*.inst; do
		echo "Configure \`basename \$i\`";
		\$i >>/var/log/univention/join.log;
	done
fi

__EOT__

chmod +x /instmnt/join.sh
chroot /instmnt ./join.sh
