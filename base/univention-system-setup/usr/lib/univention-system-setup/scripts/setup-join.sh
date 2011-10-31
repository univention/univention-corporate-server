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
        *)
            echo "WARNING: Unknown parameter $1"
			shift
    esac
done

. /usr/lib/univention-system-setup/scripts/setup_utils.sh

# Re-create SSL certificates even if the admin did'nt change all variables
/usr/lib/univention-system-setup/scripts/ssl/10ssl --force-recreate

# Call scripts which won't be handled by join scripts
# keyboard, language and timezone
run-parts /usr/lib/univention-system-setup/scripts/keyboard/
run-parts /usr/lib/univention-system-setup/scripts/language/
run-parts /usr/lib/univention-system-setup/scripts/timezone/
run-parts /usr/lib/univention-system-setup/scripts/modules/

# Do network stuff
run-parts -a --network-only -- /usr/lib/univention-system-setup/scripts/net/

# Install selected software
run-parts /usr/lib/univention-system-setup/scripts/software/

# Call join
if [ -d /var/lib/univention-ldap/ldap ]; then
	rm -f /var/lib/univention-ldap/ldap/*
fi

if [ "$server_role" = "domaincontroller_master" ]; then
	mkdir -p /var/univention-join/ /usr/share/univention-join/
	touch /var/univention-join/joined /var/univention-join/status
	if [ -e /usr/lib/univention-install/.index.txt ]; then
		rm -f /usr/lib/univention-install/.index.txt
	fi
	ln -s /var/univention-join/joined /usr/share/univention-join/.joined
	ln -s /var/univention-join/status /usr/lib/univention-install/.index.txt

	for i in /usr/lib/univention-install/*.inst; do
		echo "Configure $(basename $i)" >>/var/log/univention/join.log
		$i >>/var/log/univention/join.log 2>&1
	done
else
	if [ -n "$dcaccount" -a -n "$password_file" ]; then
	/usr/share/univention-join/univention-join -dcaccount $domain_controller_account -dcpwd "$password_file"
fi

exit 0
