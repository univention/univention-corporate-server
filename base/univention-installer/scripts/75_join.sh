#!/bin/sh
#
# Univention Installer
#  Join a system in the UCS domain
#
# Copyright 2004-2010 Univention GmbH
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
	if [ -n "$eth0_type" ] && [ "$eth0_type" = "dynamic" -o "$eth0_type" = "dhcp" ]; then
		dhclient eth0
	else
		# be sure eth0 is up and running for join. Bug #19547
		if [ -n "$eth0_ip" ] ; then
			ifup eth0
		fi
		if [ -n "$eth1_ip" ] ; then
			ifup eth1
		fi
		if [ -n "$eth2_ip" ] ; then
			ifup eth2
		fi
		if [ -n "$eth3_ip" ] ; then
			ifup eth3
		fi
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
	mkdir -p /var/univention-join/
	mkdir -p /usr/share/univention-join/
	touch /var/univention-join/joined
	touch /var/univention-join/status
	rm -rf /usr/lib/univention-install/.index.txt
	ln -s /var/univention-join/joined /usr/share/univention-join/.joined
        ln -s /var/univention-join/status /usr/lib/univention-install/.index.txt

	for i in /usr/lib/univention-install/*.inst; do
		echo "Configure \`basename \$i\`";
		echo "Configure \`basename \$i\`" >>/var/log/univention/join.log
		\$i >>/var/log/univention/join.log;
	done
fi

__EOT__

chmod +x /instmnt/join.sh
chroot /instmnt ./join.sh
