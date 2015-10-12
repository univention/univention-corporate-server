#!/bin/bash
#
# Univention Samba4
#  helper script: synchronize sysvol
#
# Copyright 2004-2015 Univention GmbH
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

. /usr/share/univention-lib/ucr.sh

log() {
	local msg="${2//$'\r'/}"
	builtin echo $(date +"%F %T") "$1" "${msg//$'\n'/}"
}

log_error() {
	log ERROR "$1"
}

log_debug() {
	if $DEBUG; then
		log DEBUG "$1"
	fi
}

eval "$(/usr/sbin/univention-config-registry shell hostname samba4/sysvol/sync/host)"

DEBUG=false
SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'
SYSVOL_SYNC_TRIGGERDIR="$SYSVOL_SYNCDIR/.trigger"
LOCKFILE="/var/lock/sysvol-sync"

LC_ALL=C

# hash over the list of files/directories with ACLs set
all_files_and_dirs_have_acls () {
	local dir="$1"
	local host="$2"
	log_debug "[$host] checking ACL's"
	a_md5=$(getfacl -span -R "$1" | sed -ne 's/^# file: //p' | sort | md5sum)
	f_md5=$(find "$1" -type f -o -type d | sort | md5sum)
	if [ "$a_md5" != "$f_md5" ]; then
		log_error "[$host] some files from $host don't have ACLs set. Will not sync to hot target!"
		return 1
	fi
	return 0
}

########
# MAIN #
########

(

# get a lock, prevent script from running twice
flock -n 9 || exit 0
 

if ! [ -d "$SYSVOL_SYNC_TRIGGERDIR" ]; then
	mkdir -p "$SYSVOL_SYNC_TRIGGERDIR"
fi
chgrp 'DC Slave Hosts' "$SYSVOL_SYNC_TRIGGERDIR"
chmod g+w "$SYSVOL_SYNC_TRIGGERDIR"

if is_ucr_true samba4/sysvol/sync/debug; then
	DEBUG=true
fi

is_ucr_true samba4/sysvol/sync/setfacl/AU
if [ ! $? -eq 1 ]; then
	log_debug "[local] setfacl on /var/lib/samba/sysvol"
	setfacl -R -P -m 'g:Authenticated Users:r-x,d:g:Authenticated Users:r-x' /var/lib/samba/sysvol
fi


if [ "$1" = '--overwrite-local' ]; then
	rsync_options=("-aAX")
else
	rsync_options=("-auAX" "--dirs-update")
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

	## pull over network from downstream s4dc
	log_debug "[${s4dc}] rsync pull from downstream DC"
	out="$(univention-ssh-rsync /etc/machine.secret -aAX --delete --delete-excluded \
		--exclude='scripts/user/.*.vbs.[[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]]' \
		"${hostname}\$"@"${s4dc}":"${SYSVOL_PATH}"/ "$importdir" 2>&1)"
	rsync_exitcode=$?
	if [ $rsync_exitcode -ne 0 ]; then
		log_error "[${s4dc}] rsync exitcode was $rsync_exitcode.  Will not sync to hot target! ($out)"
		continue
	fi

	## hash over the list of files/directories with ACLs set
	if ! all_files_and_dirs_have_acls "$importdir" "$s4dc"; then
		continue
	fi

	## sync into hot target dir with local filesystem speed
	log_debug "[${s4dc}] local sync to hot target dir"
	rsync "${rsync_options[@]}" "$importdir"/ "$SYSVOL_PATH"
done

for s4dc in $samba4_sysvol_sync_host; do	## usually there should only be one..
	if [ "$s4dc" = "$hostname" ]; then
		continue
	fi

	importdir="${SYSVOL_SYNCDIR}/.${s4dc}"

	## pull from parent s4dc
	log_debug "[${s4dc}] rsync pull from upstream DC: ${s4dc}"
	out="$(univention-ssh-rsync /etc/machine.secret "${rsync_options[@]}" --delete \
		"${hostname}\$"@"${s4dc}":"${SYSVOL_PATH}"/ "$importdir" 2>&1)"
	rsync_exitcode=$?
	if [ $rsync_exitcode -ne 0 ]; then
		log_error "[${s4dc}] rsync exitcode was $rsync_exitcode.  Will not sync to cold target! ($out)"
		continue
	fi

	## hash over the list of files/directories with ACLs set
	if ! all_files_and_dirs_have_acls "$importdir" "$s4dc"; then
		continue
	fi

	## sync into hot target dir with local filesystem speed
	log_debug "[${s4dc}] local sync to hot target dir"
	out="$(rsync "${rsync_options[@]}" "$importdir"/ "$SYSVOL_PATH" 2>&1)"
	rsync_exitcode=$?
	if [ $rsync_exitcode -ne 0 ]; then
		log_error "[${s4dc}] rsync to hot target exited with $rsync_exitcode.  Will not place a trigger file! ($out)"
		continue
	fi

	## trigger the next pull by the parent s4dc
	log_debug "[${s4dc}] placing triggerfile on ${s4dc}"
	out="$(univention-ssh /etc/machine.secret "${hostname}\$"@"${s4dc}" \
		"mkdir -p '${SYSVOL_SYNC_TRIGGERDIR}'; touch '${SYSVOL_SYNC_TRIGGERDIR}/${hostname}'" 2>&1)"
	rsync_exitcode=$?
	if [ $rsync_exitcode -ne 0 ]; then
		log_error "[${s4dc}] placing triggerfile with ssh failed with $rsync_exitcode. ($out)"
		continue
	fi
	
done

) 9>"$LOCKFILE"
