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

eval $(/usr/sbin/univention-config-registry shell hostname)

#if [ -z "$samba4_sysvol_sync_interval" ]; then
#	samba4_sysvol_sync_interval=5;
#fi

SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'

## snapshot current state of local sysvol into an export directory
exportdir="$SYSVOL_SYNCDIR/export"
if ! [ -d "$exportdir" ]; then
	mkdir -p "$exportdir"
	rsync -a "$SYSVOL_PATH"/ "$exportdir"
	# check again if something changed meanwhile
	while diff -qr "$SYSVOL_PATH" "$exportdir"; do
		rsync -a --delete "$SYSVOL_PATH"/ "$exportdir"
	done
fi

## determine list of Samba 4 DCs
samba4servicedcs=$(ldapsearch -ZZ -LLL -D "$ldap_hostdn" -y /etc/machine.secret "(&(univentionService=Samba 4)(objectClass=univentionDomainController))" cn | sed -n 's/^cn: \(.*\)/\1/p')      ## currently there is no u-d-m module computers/dc
samba4servicedcs=$(echo "$samba4servicedcs"| awk -v hostname="${hostname}" '{ for (i=1; i<=NF; i++) { if ($i != hostname){ print $i } } }')	## filter out this hostname

for s4dc in $samba4servicedcs; do
	### import sysvol from $s4dc

	## temporary target directory for sysvol of $s4dc
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

	## check if something changed in the sysvol of $s4dc with repect to the local active sysvol
	if diff -qr "$oldimportdir" "$importdir"; then
		## check if the current sysvol of $s4dc differs from the local active sysvol
		if diff -qr "$SYSVOL_PATH" "$importdir"; then
			## hot-merge the files into the local active sysvol
			## this potentially destroys changes in the local active sysvol, so avoid deleting (newer) files
			rsync -auAX "$importdir/" "$SYSVOL_PATH"

			### export sysvol for $s4dc
			## snapshot modified local sysvol for export to other hosts into the export directory
			tmpdir=$(mktemp -d $SYSVOL_SYNCDIR/tmp.XXXXXXXXXX)
			chmod g+rx,o+rx "$tmpdir"
			rsync -aAX --delete "$SYSVOL_PATH"/ "$tmpdir"
			mv "$exportdir" "$exportdir".tmp && mv "$tmpdir" "$exportdir" && rm -rf "$exportdir".tmp
			sysvol_updated=1
		fi
	fi
done

if [ "$sysvol_updated" = 1 ]; then
	## notify other hosts if central sysvol changed
	for s4dc in $samba4servicedcs; do
		univention-ssh /etc/machine.secret "${hostname}\$"@"${s4dc}" \
			touch "$SYSVOL_SYNCDIR/trigger/$hostname"
	done
fi
