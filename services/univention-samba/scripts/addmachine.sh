#!/bin/bash
#
# Univention Samba
#  Script for adding a machine via UMC
#
# Copyright 2012-2019 Univention GmbH
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


name="$1"

if [ -z "$name" ] || [ "$name" = "-h" -o "$name" = "-?" -o "$name" = "-help" -o "$name" = "--help" ]; then
	echo "Usage: $0 <windows computer name>"
	exit 1
fi

eval "$(ucr shell ldap/master hostname)"

# Create the windows computer via UMC
/usr/sbin/umc-command -s "$ldap_master" -y /etc/machine.secret -U "$hostname$" selectiveudm/create_windows_computer -o name="$name" -o samba3_mode=True; rc=$?
if [ $rc != 0 ]; then
	echo "Failed to create $name. $rc"
	exit $?
fi

# Wait for the replication (maximal 60 seconds)
c=0
while [ $c -lt  60 ]; do
	dn=$(univention-ldapsearch "uid=${name/%$/}$" dn | sed -ne 's|dn: ||p')
	test -n "$dn" && break
done

# Invalidate the nscd passwd cache
nscd -i passwd

exit 0

