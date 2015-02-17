#!/bin/bash
#
# UCS Virtual Machine Manager Daemon
#  uvmm check script
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

logfile="/var/log/univention/virtual-machine-manager-daemon-errors.log"

if sv status /etc/runit/univention-virtual-machine-manager-daemon | grep ^run: > /dev/null 2>&1; then
	tempfile="$(mktemp)"
	trap "rm -f '$tempfile'" EXIT

	uvmm groups >"$tempfile" 2>&1 &
	pid=$!

	eval "$(univention-config-registry shell uvmm/check/timeout)"
	sleep ${uvmm_check_timeout:-5}s

	if ! grep -q "^DATA:" "$tempfile"
	then
		# Kill the uvmm process
		kill $pid >/dev/null 2>&1
		wait $pid >/dev/null 2>&1

		echo "uvmm-check.sh: uvmm does not response like expected. Restarting uvmmd now." >>"$logfile"
		cat "$tempfile" >> "$logfile"
		invoke-rc.d univention-virtual-machine-manager-daemon restart >/dev/null 2>&1
	fi
fi

exit 0
