#!/bin/bash
#
# Univention Samba4
#  helper script: synchronize sysvol
#
# Copyright 2004-2013 Univention GmbH
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

# Bug #27001
## code duplication from univention-samba4/lib/base.sh
univention_samba4_is_ucr_false () { # test if UCS variable is "false"
	local value
	value="$(univention-config-registry get "$1")"
	case "$(echo -n "$value" | tr [:upper:] [:lower:])" in
		1|yes|on|true|enable|enabled) return 1 ;;
		0|no|off|false|disable|disabled) return 0 ;;
		*) return 2 ;;
	esac
}

eval "$(/usr/sbin/univention-config-registry shell hostname samba4/sysvol/sync/host)"

SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'
SYSVOL_SYNC_TRIGGERDIR="$SYSVOL_SYNCDIR/.trigger"

if ! [ -d "$SYSVOL_SYNC_TRIGGERDIR" ]; then
	mkdir -p "$SYSVOL_SYNC_TRIGGERDIR"
fi
chgrp 'DC Slave Hosts' "$SYSVOL_SYNC_TRIGGERDIR"
chmod g+w "$SYSVOL_SYNC_TRIGGERDIR"

if ! univention_samba4_is_ucr_false samba4/sysvol/sync/setfacl/AU; then
	setfacl -R -P -m 'g:Authenticated Users:r-x,d:g:Authenticated Users:r-x' /var/lib/samba/sysvol
fi

if [ "$1" = '--overwrite-local' ]; then
	rsync_options=("-aAX")
else
	rsync_options=("-auAX")
fi

## merge updates pushed to us by other s4DCs
for triggerfile in $(find "${SYSVOL_SYNC_TRIGGERDIR}" -mindepth 1 -maxdepth 1 -type f); do
	## clear flag
	rm "$triggerfile"

	## pull from downstream s4dc
	s4dc=$(basename "$triggerfile")
	if [ "$s4dc" = "$hostname" ]; then
		continue
	fi

	importdir="${SYSVOL_SYNCDIR}/${s4dc}"

	## step one: pull over network from downstream s4dc
	univention-ssh-rsync /etc/machine.secret -aAX --delete \
		"${hostname}\$"@"${s4dc}":"${SYSVOL_PATH}"/ "$importdir" 2>/dev/null

	## step two: sync into hot target dir with local filesystem speed
	rsync "${rsync_options[@]}" "$importdir"/ "$SYSVOL_PATH"
done

for s4dc in $samba4_sysvol_sync_host; do	## usually there should only be one..
	if [ "$s4dc" = "$hostname" ]; then
		continue
	fi

	## pull from parent s4dc
	univention-ssh-rsync /etc/machine.secret "${rsync_options[@]}" \
		"${hostname}\$"@"${s4dc}":"${SYSVOL_PATH}"/ "$SYSVOL_PATH" 2>/dev/null

	## trigger the next pull by the parent s4dc
	univention-ssh /etc/machine.secret "${hostname}\$"@"${s4dc}" \
		"mkdir -p '${SYSVOL_SYNC_TRIGGERDIR}'; touch '${SYSVOL_SYNC_TRIGGERDIR}/${hostname}'" 2>/dev/null
done
