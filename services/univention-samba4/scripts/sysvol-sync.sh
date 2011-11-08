#!/bin/bash
#
# Univention Samba4
#  helper script: synchronize sysvol
#
# Copyright 2004-2011 Univention GmbH
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

eval "$(/usr/sbin/univention-config-registry shell hostname samba4/sysvol/sync/host)"

SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'
SYSVOL_HOSTDIR="${SYSVOL_SYNCDIR}/${hostname}"

if ! [ -d "$SYSVOL_SYNCDIR" ]; then
	mkdir -p "$SYSVOL_SYNCDIR"
fi
chgrp 'DC Slave Hosts' "$SYSVOL_SYNCDIR"
chmod g+w "$SYSVOL_SYNCDIR"

## merge updates pushed to us by other s4DCs
for importdir in $(find "$SYSVOL_SYNCDIR" -mindepth 1 -maxdepth 1 -type d); do
	s4dc=$(basename "$importdir")
	if [ "$s4dc" = "$hostname" ]; then
		continue
	fi

	## these directories were written by a non-privileged account, so the xattrs are missing
	cd "$importdir/sysvol"	## necessary for relative paths in .xattr
	setfattr --restore="${importdir}/.xattr"

	## now rsync into hot target zone
	rsync -auAX "${importdir}/sysvol/" "$SYSVOL_PATH"
done

for s4dc in $samba4_sysvol_sync_host; do	## usually there should only be one..
	if [ "$s4dc" = "$hostname" ]; then
		continue
	fi

	## pull sysvol from parent s4dc
	univention-ssh-rsync /etc/machine.secret -auAX \
		"${hostname}\$"@"${s4dc}":"${SYSVOL_PATH}"/ "$SYSVOL_PATH" 2>/dev/null

	## snapshot hot sysvol into transfer directory
	SYSVOL_SNAPSHOTDIR="$SYSVOL_HOSTDIR/sysvol"
	mkdir -p "$SYSVOL_SNAPSHOTDIR"
	rsync -auAX "$SYSVOL_PATH"/ "$SYSVOL_SNAPSHOTDIR"

	## dump xattrs from that path, must be identical to import upstream path
	SYSVOL_XATTRFILE="$SYSVOL_HOSTDIR/.xattr"
	cd "$SYSVOL_SNAPSHOTDIR"	## necessary for relative paths in .xattr
	getfattr -R -d -m '' -P . > "$SYSVOL_XATTRFILE"

	## push to parent s4dc
	univention-ssh /etc/machine.secret "${hostname}\$"@"${s4dc}" \
		mkdir -p "${SYSVOL_HOSTDIR}" 2>/dev/null

	univention-ssh-rsync /etc/machine.secret -aAX --delete \
		"${SYSVOL_HOSTDIR}"/ "${hostname}\$"@"${s4dc}":"${SYSVOL_HOSTDIR}" 2>/dev/null
done
