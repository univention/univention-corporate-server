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

eval $(/usr/sbin/univention-config-registry shell hostname samba4/sysvol/sync/interval)

if [ -z "$samba4_sysvol_sync_interval" ]; then
	samba4_sysvol_sync_interval=60;	# seconds between checking sysvol changes on all s4DCs
fi

jitter_delay=2	# seconds between triggering another s4dc to pull changes	# TODO: concept doesn't scale

SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'
exportdir="$SYSVOL_SYNCDIR/export"

export_local_sysvol() {
	if ! [ -d "$exportdir" ]; then
		mkdir -p "$exportdir"
	fi

	## check if something changed in the sysvol with respect to the last export
	sysvol_updated=0
	if diff -qr "$exportdir" "$SYSVOL_PATH"; then
		### export sysvol for $s4dc
		## snapshot modified local sysvol for export to other hosts into the export directory
		tmpdir=$(mktemp -d $SYSVOL_SYNCDIR/tmp.XXXXXXXXXX)
		chmod g+rx,o+rx "$tmpdir"
		rsync -aAX --delete "$SYSVOL_PATH"/ "$tmpdir"
		## check again if something changed meanwhile
		while diff -qr "$SYSVOL_PATH" "$tmpdir"; do
			rsync -aAX --delete "$SYSVOL_PATH"/ "$tmpdir"
		done
		mv "$exportdir" "$exportdir".tmp && mv "$tmpdir" "$exportdir" && rm -rf "$exportdir".tmp

		sysvol_updated=1
	fi
	return "$sysvol_updated"
}


sync_sysvol_from_host() {
	s4dc="$1"

	### TODO: this code is basically the same as in gpo-sync-master.sh
	### import sysvol from $host

	## temporary target directory for sysvol of $host
	importdir="$SYSVOL_SYNCDIR/import/$s4dc"
	# temporary backup directory for sysvol of $s4dc
	oldimportdir="$SYSVOL_SYNCDIR/import/$s4dc.bak"

	if ! [ -d "$oldimportdir" ]; then
		mkdir -p "$oldimportdir"
	fi

	if ! [ -d "$importdir" ]; then
		mkdir -p "$importdir"
	else
		rsync -aAX --delete "$importdir/" "$oldimportdir"
	fi

	## read $s4dc:$exportdir into temporary import directory to minimise temporary files in local sysvol
	univention-ssh-rsync /etc/machine.secret -aAX --delete --copy-dest="$oldimportdir" \
		"${hostname}\$"@"${s4dc}":"${exportdir}"/ "$importdir"
	
	## check again if something changed meanwhile
	tmpdir=$(mktemp -d "$importdir".XXXXXXXXXX)
	univention-ssh-rsync /etc/machine.secret -aAX --delete --copy-dest="$importdir" \
		"${hostname}\$"@"${s4dc}":"${exportdir}"/ "$tmpdir"
	while diff -qr "$importdir" "$tmpdir"; do
		rsync -aAX --delete "$tmpdir" "$importdir"
		## check again if something changed meanwhile
		univention-ssh-rsync /etc/machine.secret -aAX --delete --copy-dest="$importdir" \
		"${hostname}\$"@"${s4dc}":"${exportdir}"/ "$tmpdir"
	done
	rm -rf "$tmpdir"

	## check if something changed in the sysvol of $s4dc
	if diff -qr "$oldimportdir" "$importdir"; then
		## check if the current sysvol of $s4dc differs from the local active sysvol
		if diff -qr "$SYSVOL_PATH" "$importdir"; then
			## hot-merge the files into the local active sysvol
			## this potentially destroys changes in the local active sysvol, so avoid deleting (newer) files
			rsync -auAX "$importdir/" "$SYSVOL_PATH"
		fi
	fi
}

## snapshot current state of local sysvol into the export directory
export_local_sysvol

## determine list of Samba 4 DCs
samba4servicedcs=$(ldapsearch -ZZ -LLL -D "$ldap_hostdn" -y /etc/machine.secret "(&(univentionService=Samba 4)(objectClass=univentionDomainController))" cn | sed -n 's/^cn: \(.*\)/\1/p')      ## currently there is no u-d-m module computers/dc
samba4servicedcs=$(echo "$samba4servicedcs"| awk -v hostname="${hostname}" '{ for (i=1; i<=NF; i++) { if ($i != hostname){ print $i } } }')	## filter out this hostname

sync_sysvol_with_all_s4dcs() {
	## check all s4DCs and import their sysvol if something changed
	for s4dc in $samba4servicedcs; do
		sync_sysvol_from_host "$s4dc"
	done

	## export to all s4DCs if something changed
	if export_local_sysvol; then
		## notify other hosts if central sysvol changed
		for s4dc in $samba4servicedcs; do
			sleep $jitter_delay
			univention-ssh /etc/machine.secret "${hostname}\$"@"${s4dc}" \
				touch "$SYSVOL_SYNCDIR/trigger/$hostname"
		done
	fi
}

while true; do
	sync_sysvol_with_all_s4dcs
	sleep "$samba4_sysvol_sync_interval"
done
