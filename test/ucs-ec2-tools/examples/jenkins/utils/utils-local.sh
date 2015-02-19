#!/bin/bash
#
# Copyright 2014-2015 Univention GmbH
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

ucsschool-fetch-results () {
	# ucsschool-fetch-results <IP-ADDRESS>
	local ADDR="$1"
	local TARGETDIR="$2"
	if [ -n "$TARGETDIR" ] ; then
		[ ! -d "$TARGETDIR" ] && mkdir -p "$TARGETDIR"
	else
		TARGETDIR="."
	fi
	scp -i ~/ec2/keys/tech.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:ucs-test.log "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:test-reports "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/univention/management* "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:"/var/log/univention/{join,setup,listener}.log" "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/univention/connector* "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/samba/* "$TARGETDIR"
}


# === MAIN ===

ACTION="$1"
shift || exit 1

case "$ACTION" in
	ucsschool-fetch-results)
		ucsschool-fetch-results "$@"
		;;
	*)
		echo "Unknown action: $ACTION"
		;;
esac

# vim:set filetype=sh ts=4:
