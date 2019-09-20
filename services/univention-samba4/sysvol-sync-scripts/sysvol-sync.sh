#!/bin/bash
#
# Univention Samba4
#  helper script: synchronize sysvol
#
# Copyright 2004-2019 Univention GmbH
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

. /usr/share/univention-lib/ucr.sh

log() {
	local msg="${2//$'\r'/}"
	builtin echo $(date +"%F %T") "$1" "${msg//$'\n'/}" 1>&2
}

stderr_log_error() {
	log ERROR "$1"
}

stderr_log_debug() {
	if $DEBUG; then
		log DEBUG "$1"
	fi
}

eval "$(/usr/sbin/univention-config-registry shell hostname samba4/sysvol/sync/host domainname)"

DEBUG=false
SYSVOL_PATH='/var/lib/samba/sysvol'
SYSVOL_SYNCDIR='/var/cache/univention-samba4/sysvol-sync'
SYSVOL_SYNC_TRIGGERDIR="$SYSVOL_SYNCDIR/.trigger"
PROCESS_LOCKFILE="/var/lock/sysvol-sync-process"
SYSVOL_LOCKFILE="/var/lock/sysvol-sync-dir"

LC_ALL=C

# hash over the list of files/directories with ACLs set
all_files_and_dirs_have_acls () {
	local dir="$1/$domainname/Policies"
	shift
	local host="$1"

	if [ -d "$dir" ]; then
		stderr_log_debug "[$host] checking ACL's"
		a_md5=$(getfacl -span -R "$dir" | sed -ne 's/^# file: //p' | sort | md5sum)
		f_md5=$(find "$dir" -type f -o -type d | sort | md5sum)
		if [ "$a_md5" != "$f_md5" ]; then
			stderr_log_error "[$host] some files from $host don't have ACLs set. Will not sync to hot target!"
			return 1
		fi
	fi

	return 0
}

check_if_need_sync() {
	local remote_login="$1"
	shift

	local dst="$1"
	shift

	local rsync_options=("$@")
	local need_sync

	local src="$remote_login:$SYSVOL_PATH"
	need_sync="$(univention-ssh-rsync /etc/machine.secret \
		--dry-run -v "${rsync_options[@]}" \
		"$src"/ "$dst" 2>/dev/null \
		| tail --lines=+2 | head --lines=-3)"

	if [ -z "$need_sync" ]; then
		return 1
	fi
	return 0
}

close_remote_locking_pipe() {
	local pipe_dir="$1"

	echo DONE > "$pipe_dir/pipe0"
	rm -rf "$pipe_dir"
}

create_remote_locking_pipe() {
	### Note: This function creates an EXIT trap.
	### The EXIT trap is triggered whenever a calling subshell exits.
	###
	### So don't do things like: out=$(create_remote_locking_pipe)
	### which would immediately trigger that trap!
	###
	local pipe_dir="$1"

	## setup pipes for communication with remote locker process
	trap "close_remote_locking_pipe '$pipe_dir'" EXIT
	for pipename in "pipe0" "pipe1"; do
		if ! mkfifo "$pipe_dir/$pipename"; then
			stderr_log_error "[$log_prefix] Could not create fifo: $pipe_dir/$pipename."
			close_remote_locking_pipe "$pipe_dir"
			trap - EXIT
			return 1
		fi
	done
	return 0
}

get_remote_lock() {
	local remote_login="$1"
	local pipe_dir

	pipe_dir=$(mktemp -d)
	create_remote_locking_pipe "$pipe_dir" || return $?

	## try to create remote shared (read) lock
	stderr_log_debug "[$log_prefix] trying to get remote read lock"
	timeout=30
	univention-ssh --no-split /etc/machine.secret "$remote_login" \
		-o ServerAliveInterval=20 \
		"(flock --timeout=$timeout -s 8 || exit 1; echo LOCKED; read WAIT;) 8>\"$SYSVOL_LOCKFILE\"" \
		< <(cat "$pipe_dir/pipe0") 2>&1 > "$pipe_dir/pipe1" | grep -v 'Could not chdir to home directory' 1>&2 &

	read REPLY < "$pipe_dir/pipe1"
	if [ "$REPLY" != "LOCKED" ]; then
		stderr_log_error "[$log_prefix] Could not acquire remote read lock after $timeout seconds."
		close_remote_locking_pipe "$pipe_dir"
		trap - EXIT
		return 1
	fi

	## if the file does not exists on upstream, the default permissions for $SYSVOL_LOCKFILE are wrong,
	## we need to fix them to ensure other hosts can get a lock too
	univention-ssh --no-split /etc/machine.secret "$remote_login" -o ServerAliveInterval=20 \
		"test -G '$SYSVOL_LOCKFILE' && chgrp 'DC Slave Hosts' '$SYSVOL_LOCKFILE' && chmod 664 '$SYSVOL_LOCKFILE'" \
		2>/dev/null

	return 0
}

copy_sysvol_from() {
	local remote_login="$1"
	shift
	local importdir="$1"
	shift
	local rsync_options=("$@")

	local src="$remote_login:$SYSVOL_PATH"
	(	get_remote_lock "$remote_login" || return 1

		## Read remote sysvol to local importdir
		out="$(univention-ssh-rsync /etc/machine.secret \
			"${rsync_options[@]}" \
			"$src"/ "$importdir" 2>&1)"

		rsync_exitcode=$?
		if [ $rsync_exitcode -ne 0 ]; then
			stderr_log_error "[$log_prefix] rsync exitcode was $rsync_exitcode ($out)"
			return 1
		fi
	)	## this subshell context is important to release the lock again

	# Note: returns here with subshell exitcode
}

sync_to_local_sysvol() {
	local importdir="$1"
	shift
	local rsync_options=("$@")

	stderr_log_debug "[$log_prefix] local sync from importdir to sysvol"
	(
		stderr_log_debug "[$log_prefix] trying to get exclusive (write) lock on local sysvol"
		timeout=60
		if ! flock --timeout=$timeout 8; then
			stderr_log_error "[$log_prefix] could not lock local sysvol dir for writing after $timeout seconds"
			return 1
		fi
		out="$(rsync "${rsync_options[@]}" "$importdir"/ "$SYSVOL_PATH" 2>&1)"
		rsync_exitcode=$?
		if [ $rsync_exitcode -ne 0 ]; then
			stderr_log_error "[$log_prefix] rsync to local sysvol exited with $rsync_exitcode ($out)"
			return $rsync_exitcode
		fi
		if is_ucr_true samba4/sysvol/sync/fix_gpt_ini; then
			stderr_log_debug "[$log_prefix] search for multiple gpt.ini files and delete all but the newest"
			fix_gpt_ini
		fi
	) 8>"$SYSVOL_LOCKFILE"

	# Note: returns here with subshell exitcode
}

trigger_upstream_sync() {
	local remote_login="$1"

	stderr_log_debug "[$log_prefix] placing triggerfile."
	out="$(univention-ssh --no-split /etc/machine.secret "$remote_login" \
		-o ServerAliveInterval=15 \
		"mkdir -p \"${SYSVOL_SYNC_TRIGGERDIR}\"; touch \"${SYSVOL_SYNC_TRIGGERDIR}/${hostname}\"" 2>&1)"

	rsync_exitcode=$?
	if [ $rsync_exitcode -ne 0 ]; then
		stderr_log_error "[$log_prefix] placing triggerfile with ssh failed with $rsync_exitcode. ($out)"
		return $rsync_exitcode
	fi
}

sync_from_active_downstream_DCs() {
	if is_ucr_false "samba4/sysvol/sync/from_downstream"; then
		return
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

		log_prefix="$s4dc"
		importdir="$SYSVOL_SYNCDIR/$s4dc"

		## check if downstream s4dc has changes:
		stderr_log_debug "[$log_prefix] rsync check for changes on downstream DC"

		rsync_options=(-aAX --delete --delete-excluded \
			--exclude='scripts/user/.*.vbs.[[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]][[:alnum:]]' \
			)

		remote_login="$hostname\$@$s4dc"
		check_if_need_sync "$remote_login" "$importdir" "${rsync_options[@]}"
		if [ $? -eq 0 ]; then
			## pull from parent s4dc
			stderr_log_debug "[$log_prefix] rsync pull from downstream DC"

			copy_sysvol_from "$remote_login" "$importdir" "${rsync_options[@]}"
			if [ $? -ne 0 ]; then
				stderr_log_error "[$log_prefix] Skipping sync to local sysvol!"
				continue
			fi
		else
			stderr_log_debug "[$log_prefix] No downstream changes."
		fi

		## hash over the list of files/directories with ACLs set
		if ! all_files_and_dirs_have_acls "$importdir" "$s4dc"; then
			continue
		fi

		## sync into hot target dir with local filesystem speed
		sync_to_local_sysvol "$importdir" "${default_rsync_options[@]}"
	done
}

fix_gpt_ini () {
	# find policy dirs with multiple gpt.ini's
	local poldir="$SYSVOL_PATH/$domainname/Policies/"
	while read dir; do
		# sort gpt.ini's by time of last status change
		mapfile -t gpts < <(stat -c "%Z %n" "$dir"/[Gg][Pp][Tt].[Ii][Nn][Ii] 2>/dev/null | sort -n -r)
		if [ "${#gpts[@]}" -gt 1 ]; then
			# multiple gpt.ini's found, delete first element of list (newest gpt.ini) and remove the rest
			gpts=("${gpts[@]:1}")
			for gpt in "${gpts[@]}"; do
				local file=${gpt#* }
				test -f $file && rm $file
			done
		fi
	done < <(find "$poldir" -maxdepth 1 -type d -name '{*}')
}

sync_from_upstream_DC() {
	for s4dc in $samba4_sysvol_sync_host; do	## usually there should only be one..
		if [ "$s4dc" = "$hostname" ]; then
			continue
		fi

		log_prefix="$s4dc"
		importdir="$SYSVOL_SYNCDIR/.$s4dc"
		remote_login="$hostname\$@$s4dc"

		## trigger the next pull by the parent s4dc
		trigger_upstream_sync "$remote_login"
		if [ $? -ne 0 ]; then
			stderr_log_error "[$log_prefix] Placing a trigger file failed."
			continue
		fi

		if is_ucr_false "samba4/sysvol/sync/from_upstream"; then
			continue
		fi
		
		## check if parent s4dc has changes:
		stderr_log_debug "[${s4dc}] rsync check for changes on upstream DC"

		rsync_options=("${default_rsync_options[@]}" --delete)

		check_if_need_sync "$remote_login" "$importdir" "${rsync_options[@]}"
		if [ $? -eq 0 ]; then
			## pull from parent s4dc
			stderr_log_debug "[$log_prefix] rsync pull from upstream DC"

			copy_sysvol_from "$remote_login" "$importdir" "${rsync_options[@]}"
			if [ $? -ne 0 ]; then
				stderr_log_error "[$log_prefix] Skipping sync to local sysvol!"
				continue
			fi
		else
			stderr_log_debug "[$log_prefix] No upstream changes."
		fi

		## hash over the list of files/directories with ACLs set
		if ! all_files_and_dirs_have_acls "$importdir" "$s4dc"; then
			continue
		fi

		## sync into hot target dir with local filesystem speed
		## check if we have to delete local changes during sync
		local hot_sync_rsync_options=("${default_rsync_options[@]}")
		if is_ucr_true "samba4/sysvol/sync/from_upstream/delete"; then
			hot_sync_rsync_options+=("--delete")
		fi
		sync_to_local_sysvol "$importdir" "${hot_sync_rsync_options[@]}"
	done
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
	stderr_log_debug "[local] setfacl on /var/lib/samba/sysvol"
	setfacl -R -P -m 'g:Authenticated Users:r-x,d:g:Authenticated Users:r-x' /var/lib/samba/sysvol
fi

if [ "$1" = '--overwrite-local' ]; then
	default_rsync_options=("-aAX")
else
	default_rsync_options=("-auAX" "--dirs-update")
fi

touch "$SYSVOL_LOCKFILE"
chgrp "DC Slave Hosts" "$SYSVOL_LOCKFILE"
chmod g+w "$SYSVOL_LOCKFILE"

sync_from_active_downstream_DCs
sync_from_upstream_DC

) 9>"$PROCESS_LOCKFILE"
